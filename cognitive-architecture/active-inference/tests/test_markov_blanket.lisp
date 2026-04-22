;;; test_markov_blanket.lisp
;;; Unit tests for the Markov Blanket implementation.
;;; Run with: sbcl --load markov_blanket.lisp --load test_markov_blanket.lisp

(require :fiveam)

(defpackage :revarie-active-inference-tests
  (:use :common-lisp :fiveam :revarie-active-inference)
  (:export :run-tests))

(in-package :revarie-active-inference-tests)

(def-suite active-inference-tests
  :description "Tests for Active Inference Markov blanket")

(in-suite active-inference-tests)

(test blanket-creation
  "Test creation of a Markov blanket."
  (let ((mb (make-markov-blanket 3 2 1)))
    (is (revarie-active-inference:markov-blanket-p mb))
    (is (= 3 (length (blanket-internal mb))))
    (is (= 2 (length (blanket-sensory mb))))
    (is (= 1 (length (blanket-active mb))))))

(test sensory-update
  "Test updating sensory states."
  (let ((mb (make-markov-blanket 2 2 1)))
    (update-sensory mb '(1.0 0.5))
    (is (equal '(1.0 0.5) (blanket-sensory mb)))))

(test active-update
  "Test updating active states."
  (let ((mb (make-markov-blanket 2 2 2)))
    (update-active mb '(0.8 -0.2))
    (is (equal '(0.8 -0.2) (blanket-active mb)))))

(test internal-update
  "Test updating internal states."
  (let ((mb (make-markov-blanket 3 2 1)))
    (update-internal mb '(0.1 0.2 0.3))
    (is (equal '(0.1 0.2 0.3) (blanket-internal mb)))))

(test free-energy-computation
  "Test that free energy is computed correctly and is positive."
  (let ((mb (make-markov-blanket 2 2 1)))
    (update-sensory mb '(1.0 0.0))
    (update-internal mb '(0.5 0.5))
    (let ((fe (free-energy mb)))
      (is (> fe 0.0)))))

(test free-energy-decreases-with-better-prediction
  "Test that free energy decreases when internal states better predict sensory states."
  (let ((mb (make-markov-blanket 2 2 1)))
    (update-sensory mb '(1.0 0.5))
    ;; Poor prediction
    (update-internal mb '(0.0 0.0))
    (let ((fe-bad (free-energy mb)))
      ;; Better prediction
      (update-internal mb '(0.9 0.4))
      (let ((fe-good (free-energy mb)))
        (is (< fe-good fe-bad))))))

(test dimension-mismatch-errors
  "Test that updating with wrong dimensions signals an error."
  (let ((mb (make-markov-blanket 3 2 1)))
    (signals error (update-sensory mb '(1.0)))
    (signals error (update-active mb '(1.0 2.0)))
    (signals error (update-internal mb '(1.0)))))

(defun run-tests ()
  "Run all Active Inference tests."
  (run! 'active-inference-tests))

#+nil
(run-tests)
