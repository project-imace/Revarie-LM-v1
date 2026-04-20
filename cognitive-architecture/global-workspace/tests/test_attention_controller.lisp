;;; test_attention_controller.lisp
;;; Unit tests for the Global Workspace attention controller.
;;; Run with: sbcl --load attention_controller.lisp --load test_attention_controller.lisp

(require :fiveam)

(defpackage :revarie-gwt-tests
  (:use :common-lisp :fiveam :revarie-gwt)
  (:export :run-tests))

(in-package :revarie-gwt-tests)

(def-suite gwt-attention-tests
  :description "Tests for Global Workspace attention controller")

(in-suite gwt-attention-tests)

(test signal-creation
  "Test that signals can be created with correct defaults."
  (let ((signal (make-gwt-signal :source "test-module" :content "Hello" :salience 0.8)))
    (is (equal "test-module" (gwt-signal-source signal)))
    ;; FIXED: Added revarie-gwt:: prefix to unexported accessors
    (is (equal "Hello" (revarie-gwt::gwt-signal-content signal)))
    (is (= 0.8 (revarie-gwt::gwt-signal-salience signal)))
    (is (= 0.0 (revarie-gwt::gwt-signal-confidence signal)))
    (is (= 0.0 (revarie-gwt::gwt-signal-novelty signal)))))

(test activation-computation
  "Test that activation is computed correctly with weights."
  (let ((signal (make-gwt-signal :source "affective"
                                 :content "distress"
                                 :salience 0.9
                                 :confidence 0.8
                                 :novelty 0.7)))
    ;; Nullify recency boost by setting timestamp to old value
    (setf (gwt-signal-timestamp signal) (- (get-universal-time) 10))
    (let ((activation (revarie-gwt::compute-activation signal)))
      (is (< (abs (- activation (+ (* 0.4 0.9) (* 0.3 0.8) (* 0.3 0.7)))) 0.01)))))

(test competition-winner-selection
  "Test that the signal with highest activation wins."
  (let ((ac (make-attention-controller)))
    (submit-signal ac (make-gwt-signal :source "low" :salience 0.3))
    (submit-signal ac (make-gwt-signal :source "high" :salience 0.9))
    (let ((winner (select-focus ac)))
      (is (not (null winner)))
      (is (equal "high" (gwt-signal-source winner))))))

(test empty-controller
  "Test that an empty controller returns NIL on focus selection."
  (let ((ac (make-attention-controller)))
    (is (null (select-focus ac)))))

(test inhibition-mechanism
  "Test that inhibited sources are ignored until expiration."
  (let ((ac (make-attention-controller)))
    ;; First, establish a focus so history is not empty.
    (submit-signal ac (make-gwt-signal :source "blocked" :salience 0.9))
    (select-focus ac)
    (inhibit-current ac 60)
    
    ;; Now submit signals from blocked and allowed sources.
    (submit-signal ac (make-gwt-signal :source "blocked" :salience 0.9))
    (submit-signal ac (make-gwt-signal :source "allowed" :salience 0.5))
    (let ((winner (select-focus ac)))
      (is (not (null winner)))
      (is (equal "allowed" (gwt-signal-source winner))))))

(test goal-setting
  "Test that goals can be added and cleared."
  (let ((ac (make-attention-controller)))
    (set-goal ac "help-user")
    (is (member "help-user" (revarie-gwt::current-goals ac) :test #'equal))
    (clear-goals ac)
    (is (null (revarie-gwt::current-goals ac)))))

(test focus-retrieval
  "Test that get-focus returns the most recent winner."
  (let ((ac (make-attention-controller)))
    (submit-signal ac (make-gwt-signal :source "first" :salience 0.7))
    (select-focus ac)
    (let ((focus (get-focus ac)))
      (is (not (null focus)))
      (is (equal "first" (gwt-signal-source focus))))))

(defun run-tests ()
  "Run all GWT attention controller tests."
  (run! 'gwt-attention-tests))

#+nil
(run-tests)
