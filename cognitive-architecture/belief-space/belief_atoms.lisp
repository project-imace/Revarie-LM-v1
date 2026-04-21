;;; belief_atoms.lisp
;;; Belief Space – Belief Atoms.
;;; Belief Atoms are modular, growth‑oriented engines of agency.
;;; Unlike the static Belief Space (manifold M), Atoms are stochastic engines
;;; that evolve based on participant feedback.

(defpackage :revarie-belief-space
  (:use :common-lisp)
  (:export :make-belief-atom
           :atom-id
           :atom-value
           :atom-confidence
           :atom-precision
           :atom-update
           :atom-decay
           :atom-distance
           :make-atom-space
           :atom-space-insert
           :atom-space-retrieve
           :atom-space-evolve
           :atom-space-sample))

(in-package :revarie-belief-space)

;;; ---------------------------------------------------------------------------
;;; Belief Atom Structure
;;; ---------------------------------------------------------------------------

;; FIXED: Used %make-belief-atom to prevent infinite recursion in the wrapper
(defstruct (belief-atom (:constructor %make-belief-atom) (:conc-name atom-))
  "A Belief Atom is a stochastic engine representing a single belief or preference.
   It evolves based on feedback through precision‑weighted updates."
  (id (gensym "ATOM-") :type symbol)
  ;; FIXED: Changed double-float to float to prevent strict type-checking errors
  (value 0.0 :type float)        
  (confidence 0.5 :type float)    
  (precision 1.0 :type float)     
  (decay-rate 0.01 :type float)   
  (timestamp (get-universal-time) :type integer))

(defun make-belief-atom (&key value confidence precision decay-rate)
  "Create a new Belief Atom with specified initial parameters."
  (%make-belief-atom
   :value (or value 0.0)
   :confidence (or confidence 0.5)
   :precision (or precision 1.0)
   :decay-rate (or decay-rate 0.01)))

(defun atom-update (atom feedback &key (learning-rate 0.1))
  "Update the atom based on feedback.
   The update is precision‑weighted: Δvalue = learning_rate * precision * (feedback - value)."
  (let* ((current (atom-value atom))
         (precision (atom-precision atom))
         (error (- feedback current))
         (delta (* learning-rate precision error))
         (new-value (+ current delta))
         (new-confidence (min 1.0 (+ (atom-confidence atom) 0.05))))
    (setf (atom-value atom) new-value
          (atom-confidence atom) new-confidence
          (atom-timestamp atom) (get-universal-time))
    atom))

(defun atom-decay (atom)
  "Apply spontaneous decay to the atom, pulling it toward a neutral state."
  (let ((current (atom-value atom)))
    (setf (atom-value atom) (* current (- 1.0 (atom-decay-rate atom)))
          (atom-confidence atom) (max 0.1 (* (atom-confidence atom) 0.99))
          (atom-timestamp atom) (get-universal-time))
    atom))

(defun atom-distance (atom1 atom2)
  "Compute the distance between two belief atoms.
   For scalar atoms, this is the absolute difference in value."
  (abs (- (atom-value atom1) (atom-value atom2))))

;;; ---------------------------------------------------------------------------
;;; Atom Space – Collection of Belief Atoms
;;; ---------------------------------------------------------------------------

;; FIXED: Used %make-atom-space to prevent wrapper collision
(defstruct (atom-space (:constructor %make-atom-space) (:conc-name as-))
  "A collection of Belief Atoms representing an agent's belief state."
  (atoms nil :type list)
  (dimension 0 :type fixnum)
  (name nil :type symbol))

(defun make-atom-space (dimension &key name)
  "Create a new atom space with the given dimension."
  (%make-atom-space :dimension dimension :name name))

(defun atom-space-insert (space atom)
  "Insert a belief atom into the space."
  (push atom (as-atoms space))
  space)

(defun atom-space-retrieve (space atom-id)
  "Retrieve an atom by its ID."
  (find atom-id (as-atoms space) :key #'atom-id))

(defun atom-space-evolve (space feedback-vector &key (learning-rate 0.1))
  "Evolve all atoms in the space based on a feedback vector.
   The feedback vector should have the same dimension as the space."
  (when (not (= (length feedback-vector) (as-dimension space)))
    (error "Feedback vector dimension ~D does not match space dimension ~D"
           (length feedback-vector) (as-dimension space)))
  (loop for atom in (as-atoms space)
        for feedback in feedback-vector
        do (atom-update atom feedback :learning-rate learning-rate))
  space)

(defun atom-space-sample (space)
  "Sample the current belief state as a vector of atom values."
  (mapcar #'atom-value (as-atoms space)))

(defun atom-space-decay (space)
  "Apply decay to all atoms in the space."
  (mapc #'atom-decay (as-atoms space))
  space)

;;; ---------------------------------------------------------------------------
;;; Tests (FiveAM)
;;; ---------------------------------------------------------------------------

#+fiveam
(progn
  (defpackage :revarie-belief-space-tests
    (:use :common-lisp :fiveam :revarie-belief-space))
  (in-package :revarie-belief-space-tests)

  (def-suite belief-space-tests
    :description "Tests for Belief Atoms")
  (in-suite belief-space-tests)

  (test atom-creation
    "Test creation of belief atoms."
    (let ((atom (make-belief-atom :value 0.8 :confidence 0.7)))
      (is (typep atom 'belief-atom))
      (is (= 0.8 (atom-value atom)))
      (is (= 0.7 (atom-confidence atom)))))

  (test atom-update
    "Test that atoms update toward feedback."
    (let ((atom (make-belief-atom :value 0.5 :precision 1.0)))
      (atom-update atom 0.8 :learning-rate 0.5)
      (let ((new-val (atom-value atom)))
        (is (> new-val 0.5))
        (is (< (abs (- new-val 0.65)) 0.01)))))

  (test atom-decay
    "Test that atoms decay toward neutral."
    (let ((atom (make-belief-atom :value 1.0 :decay-rate 0.1)))
      (atom-decay atom)
      (is (= 0.9 (atom-value atom)))))

  (test atom-space-evolution
    "Test evolution of an atom space with feedback."
    (let ((space (make-atom-space 3)))
      (dotimes (i 3)
        (atom-space-insert space (make-belief-atom :value 0.5)))
      ;; FIXED: Adjusted feedback vector so the third atom evaluates to strictly less than 0.4
      (atom-space-evolve space '(0.9 0.7 0.1) :learning-rate 0.5)
      (let ((sample (atom-space-sample space)))
        (is (> (first sample) 0.6))
        (is (< (third sample) 0.4)))))

  (test atom-space-retrieval
    "Test retrieval of atoms by ID."
    (let ((space (make-atom-space 1))
          (atom (make-belief-atom)))
      (atom-space-insert space atom)
      (let ((retrieved (atom-space-retrieve space (atom-id atom))))
        (is (eq atom retrieved)))))

  (run! 'belief-space-tests))
