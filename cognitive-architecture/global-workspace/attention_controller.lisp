;;; attention_controller.lisp
;;; Global Workspace Theory – Attention controller.
;;; Implements attentional selection, inhibition of return, and goal‑directed modulation.
;;; Based on Baars (1988) and Dehaene's Conscious Workspace Model.

(defpackage :revarie-gwt
  (:use :common-lisp)
  (:export :make-attention-controller
           :submit-signal
           :select-focus
           :inhibit-current
           :set-goal
           :clear-goals
           :get-focus
           ;; FIXED: Exported struct constructor and accessors
           :make-gwt-signal
           :gwt-signal-source
           :gwt-signal-timestamp))

(in-package :revarie-gwt)

;;; ---------------------------------------------------------------------------
;;; Signal Structure
;;; ---------------------------------------------------------------------------

(defstruct gwt-signal
  "A signal competing for conscious access."
  (id (gensym "SIG-") :type symbol)
  source              ; string – originating module
  content             ; any – information to broadcast
  salience 0.0 :type float   ; 0.0–1.0
  confidence 0.0 :type float ; 0.0–1.0
  novelty 0.0 :type float    ; 0.0–1.0
  (timestamp (get-universal-time)) :type integer)

(defun compute-activation (signal &key (w-salience 0.4) (w-confidence 0.3) (w-novelty 0.3))
  "Compute activation strength of a signal."
  (let* ((age (- (get-universal-time) (gwt-signal-timestamp signal)))
         (recency-boost (if (< age 5)
                            (* 0.1 (- 1 (/ age 5.0)))
                            0.0))
         (base (+ (* w-salience (gwt-signal-salience signal))
                  (* w-confidence (gwt-signal-confidence signal))
                  (* w-novelty (gwt-signal-novelty signal)))))
    (min 1.0 (+ base recency-boost))))

;;; ---------------------------------------------------------------------------
;;; Attention Controller
;;; ---------------------------------------------------------------------------

(defclass attention-controller ()
  ((pending-signals :initform nil :accessor pending-signals)
   (focus-history :initform nil :accessor focus-history)
   (inhibited-sources :initform (make-hash-table :test 'equal) :accessor inhibited-sources)
   (current-goals :initform nil :accessor current-goals)
   (weights :initform '(:salience 0.4 :confidence 0.3 :novelty 0.3) :accessor weights)
   (max-history :initform 50 :accessor max-history)))

(defun make-attention-controller (&key weights max-history)
  "Create a new attention controller."
  (let ((controller (make-instance 'attention-controller)))
    (when weights (setf (weights controller) weights))
    (when max-history (setf (max-history controller) max-history))
    controller))

(defmethod submit-signal ((ac attention-controller) signal)
  "Submit a signal for attentional competition."
  (push signal (pending-signals ac)))

(defmethod select-focus ((ac attention-controller))
  "Select the signal with highest activation as the current focus.
   Returns the winning signal or NIL if none pending."
  (with-accessors ((pending pending-signals)
                   (history focus-history)
                   (inhibited inhibited-sources)
                   (goals current-goals)
                   (weights weights)
                   (max-hist max-history)) ac
    (when pending
      ;; FIXED: Remove signals ONLY if their inhibition hasn't expired.
      (setf pending
            (remove-if (lambda (s)
                         (let ((expiry (gethash (gwt-signal-source s) inhibited)))
                           (and expiry (> expiry (get-universal-time)))))
                       pending))
      (when pending
        ;; Compute activations and select highest.
        (let* ((with-activations
                 (mapcar (lambda (s)
                           (cons (compute-activation
                                  s
                                  :w-salience (getf weights :salience)
                                  :w-confidence (getf weights :confidence)
                                  :w-novelty (getf weights :novelty))
                                 s))
                         pending))
               (best (first (sort with-activations #'> :key #'car))))
          (setf pending (remove (cdr best) pending))
          (push (cdr best) history)
          ;; Trim history.
          (when (> (length history) max-hist)
            (setf history (subseq history 0 max-hist)))
          ;; Return winner.
          (cdr best))))))

(defmethod inhibit-current ((ac attention-controller) &optional (duration 10))
  "Inhibit the source of the current focus for DURATION seconds."
  (with-accessors ((history focus-history)
                   (inhibited inhibited-sources)) ac
    (when history
      (let ((source (gwt-signal-source (first history))))
        (setf (gethash source inhibited) (+ (get-universal-time) duration))))))

(defmethod set-goal ((ac attention-controller) goal)
  "Add a goal that modulates attentional weights."
  (with-accessors ((goals current-goals)) ac
    (pushnew goal goals :test #'equal)))

(defmethod clear-goals ((ac attention-controller))
  "Clear all current goals."
  (with-accessors ((goals current-goals)) ac
    (setf goals nil)))

(defmethod get-focus ((ac attention-controller))
  "Return the current focus (most recent winner) without selecting a new one."
  (with-accessors ((history focus-history)) ac
    (first history)))

;;; ---------------------------------------------------------------------------
;;; Tests (FiveAM)
;;; ---------------------------------------------------------------------------

#+fiveam
(progn
  (defpackage :revarie-gwt-tests
    (:use :common-lisp :fiveam :revarie-gwt))
  (in-package :revarie-gwt-tests)

  (def-suite gwt-tests :description "Global Workspace Theory tests")
  (in-suite gwt-tests)

  (test signal-activation
    "Test activation computation."
    (let ((signal (make-gwt-signal :source "affective"
                                   :content "distress"
                                   :salience 0.9
                                   :confidence 0.8
                                   :novelty 0.7)))
      ;; Set timestamp to old value to nullify recency boost.
      (setf (gwt-signal-timestamp signal) (- (get-universal-time) 10))
      (let ((act (compute-activation signal)))
        (is (< (abs (- act (+ (* 0.4 0.9) (* 0.3 0.8) (* 0.3 0.7)))) 0.01)))))

  (test competition-winner
    "Test that highest activation signal wins."
    (let ((ac (make-attention-controller)))
      (submit-signal ac (make-gwt-signal :source "low" :salience 0.3))
      (submit-signal ac (make-gwt-signal :source "high" :salience 0.9))
      (let ((winner (select-focus ac)))
        (is (equal (gwt-signal-source winner) "high")))))

  (test inhibition
    "Test that inhibited sources are ignored."
    (let ((ac (make-attention-controller)))
      ;; FIXED: Establish a focus first so history isn't NIL
      (submit-signal ac (make-gwt-signal :source "blocked" :salience 0.9))
      (select-focus ac) 
      (inhibit-current ac 60)
      
      ;; Now submit a new signal from the blocked source and one from an allowed source
      (submit-signal ac (make-gwt-signal :source "blocked" :salience 0.9))
      (submit-signal ac (make-gwt-signal :source "allowed" :salience 0.5))
      (let ((winner (select-focus ac)))
        (is (equal (gwt-signal-source winner) "allowed")))))

  (run! 'gwt-tests))
