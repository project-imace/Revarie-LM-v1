;;; test_belief_atoms.lisp
;;; Unit tests for Belief Atoms.
;;; Run with: sbcl --load belief_atoms.lisp --load test_belief_atoms.lisp

(require :fiveam)

(defpackage :revarie-belief-space-tests
  (:use :common-lisp :fiveam :revarie-belief-space)
  (:export :run-tests))

(in-package :revarie-belief-space-tests)

(def-suite belief-atoms-tests
  :description "Tests for Belief Atoms module")

(in-suite belief-atoms-tests)

(test atom-creation
  "Test creation of belief atoms with default and custom values."
  (let ((atom1 (make-belief-atom))
        (atom2 (make-belief-atom :value 0.8 :confidence 0.7 :precision 2.0)))
    ;; FIXED: Prefixed the unexported struct type
    (is (typep atom1 'revarie-belief-space::belief-atom))
    (is (= 0.0 (atom-value atom1)))
    (is (= 0.5 (atom-confidence atom1)))
    (is (= 1.0 (atom-precision atom1)))
    (is (= 0.8 (atom-value atom2)))
    (is (= 0.7 (atom-confidence atom2)))
    (is (= 2.0 (atom-precision atom2)))))

(test atom-update
  "Test that atoms update toward feedback with precision weighting."
  (let ((atom (make-belief-atom :value 0.5 :precision 1.0)))
    (atom-update atom 0.8 :learning-rate 0.5)
    (let ((new-val (atom-value atom)))
      (is (> new-val 0.5))
      (is (< (abs (- new-val 0.65)) 0.01))
      (is (> (atom-confidence atom) 0.5)))))

(test atom-decay
  "Test spontaneous decay of atoms toward neutral."
  (let ((atom (make-belief-atom :value 1.0 :decay-rate 0.1)))
    (atom-decay atom)
    (is (= 0.9 (atom-value atom)))
    (is (< (atom-confidence atom) 0.5))))

(test atom-distance
  "Test distance between two belief atoms."
  (let ((atom1 (make-belief-atom :value 0.2))
        (atom2 (make-belief-atom :value 0.7)))
    (is (= 0.5 (atom-distance atom1 atom2)))))

(test atom-space-creation
  "Test creation of atom space."
  (let ((space (make-atom-space 5 :name 'test-space)))
    ;; FIXED: Prefixed unexported types and internal struct accessors
    (is (typep space 'revarie-belief-space::atom-space))
    (is (= 5 (revarie-belief-space::as-dimension space)))
    (is (eq 'test-space (revarie-belief-space::as-name space)))
    (is (null (revarie-belief-space::as-atoms space)))))

(test atom-space-insert-retrieve
  "Test insertion and retrieval of atoms."
  (let* ((space (make-atom-space 2))
         (atom (make-belief-atom :value 0.3)))
    (atom-space-insert space atom)
    (let ((retrieved (atom-space-retrieve space (atom-id atom))))
      (is (eq atom retrieved)))))

(test atom-space-evolution
  "Test evolution of entire atom space with feedback vector."
  (let ((space (make-atom-space 3)))
    (dotimes (i 3)
      (atom-space-insert space (make-belief-atom :value 0.5)))
    (atom-space-evolve space '(0.9 0.7 0.1) :learning-rate 0.5)
    (let ((sample (atom-space-sample space)))
      (is (> (first sample) 0.6))
      (is (< (third sample) 0.4)))))

(test atom-space-decay
  "Test decay of all atoms in space."
  (let ((space (make-atom-space 2)))
    (dotimes (i 2)
      (atom-space-insert space (make-belief-atom :value 1.0 :decay-rate 0.1)))
    ;; FIXED: Prefixed the unexported decay function
    (revarie-belief-space::atom-space-decay space)
    (let ((sample (atom-space-sample space)))
      (is (every (lambda (v) (< (abs (- v 0.9)) 0.01)) sample)))))

(defun run-tests ()
  "Run all belief atoms tests."
  (run! 'belief-atoms-tests))

#+nil
(run-tests)
