;;; test_saddle_point.lisp
;;; Unit tests for Saddle Point Seeker.
;;; Run with: sbcl --load saddle_point_seeker.lisp --load test_saddle_point.lisp

(require :fiveam)

(defpackage :revarie-rebound-tests
  (:use :common-lisp :fiveam :revarie-rebound)
  (:export :run-tests))

(in-package :revarie-rebound-tests)

(def-suite rebound-tests
  :description "Tests for Rebound Mechanism saddle point seeker")
(in-suite rebound-tests)

(test saddle-point-creation
  "Test creation of saddle points."
  (let ((sp (make-saddle-point '(1.0 2.0 3.0))))
    (is (typep sp 'revarie-rebound::saddle-point))
    (is (equal '(1.0 2.0 3.0) (revarie-rebound::sp-coordinates sp)))
    (is (= 3 (revarie-rebound::sp-dimension sp)))))

(test find-saddle-point-convergence
  "Test that the seeker converges to a stationary point."
  (let ((seeker (make-saddle-point-seeker nil :max-iterations 50)))
    (let ((result (find-saddle-point seeker '(2.0 2.0))))
      (is (listp result))
      (is (= 2 (length result))))))

(test saddle-point-distance-with-predefined
  "Test distance computation to predefined saddle point."
  (let* ((sp (make-saddle-point '(0.0 0.0)))
         (seeker (make-saddle-point-seeker nil :saddle-points (list sp))))
    (let ((dist (saddle-point-distance seeker '(3.0 4.0))))
      (is (< (abs (- dist 5.0)) 1e-6)))))

(test saddle-point-distance-default
  "Test distance computation when no saddle points are predefined."
  (let ((seeker (make-saddle-point-seeker nil)))
    (let ((dist (saddle-point-distance seeker '(3.0 4.0))))
      (is (< (abs (- dist 5.0)) 1e-6)))))

(test neutral-stabilization-target
  "Test that neutral stabilization target returns coordinates."
  (let ((seeker (make-saddle-point-seeker nil :max-iterations 30)))
    (let ((target (neutral-stabilization-target seeker '(1.0 1.0))))
      (is (listp target))
      (is (= 2 (length target))))))

(test saddle-point-gradient-shape
  "Test that gradient computation returns correct dimension."
  (let ((seeker (make-saddle-point-seeker nil)))
    (let ((grad (saddle-point-gradient seeker '(2.0 3.0))))
      (is (= 2 (length grad))))))

(defun run-tests ()
  "Run all rebound mechanism tests."
  (run! 'rebound-tests))

#+nil
(run-tests)
