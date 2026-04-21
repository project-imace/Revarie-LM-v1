;;; test_value_iteration.lisp
;;; Unit tests for POMDP Value Iteration.
;;; Run with: sbcl --load value_iteration.lisp --load test_value_iteration.lisp

(require :fiveam)

(defpackage :revarie-pomdp-tests
  (:use :common-lisp :fiveam :revarie-pomdp)
  (:export :run-tests))

(in-package :revarie-pomdp-tests)

(def-suite pomdp-tests
  :description "Tests for POMDP Value Iteration")
(in-suite pomdp-tests)

;; Helper to create a simple 2-state, 2-action, 2-observation POMDP
(defun make-tiger-pomdp ()
  "Create the classic Tiger POMDP for testing."
  (let ((transitions (make-hash-table :test 'equal))
        (obs-matrix (make-hash-table :test 'equal))
        (rewards (make-hash-table :test 'equal)))
    
    ;; FIXED: Use nested hash tables for transitions
    (dolist (act '("listen" "open-left" "open-right"))
      (let ((act-h (make-hash-table :test 'equal)))
        (dolist (s '("tiger-left" "tiger-right"))
          (let ((s-h (make-hash-table :test 'equal)))
            (setf (gethash s s-h) 1.0)
            (setf (gethash s act-h) s-h)))
        (setf (gethash act transitions) act-h)))

    ;; FIXED: Use nested hash tables for observations
    (let ((tl-obs (make-hash-table :test 'equal))
          (tr-obs (make-hash-table :test 'equal)))
      (setf (gethash "hear-left" tl-obs) 0.85)
      (setf (gethash "hear-right" tl-obs) 0.15)
      (setf (gethash "tiger-left" obs-matrix) tl-obs)

      (setf (gethash "hear-left" tr-obs) 0.15)
      (setf (gethash "hear-right" tr-obs) 0.85)
      (setf (gethash "tiger-right" obs-matrix) tr-obs))
    
    ;; Rewards
    (setf (gethash (list "tiger-left" "listen") rewards) -1.0)
    (setf (gethash (list "tiger-right" "listen") rewards) -1.0)
    (setf (gethash (list "tiger-left" "open-left") rewards) -100.0)
    (setf (gethash (list "tiger-right" "open-left") rewards) 10.0)
    (setf (gethash (list "tiger-left" "open-right") rewards) 10.0)
    (setf (gethash (list "tiger-right" "open-right") rewards) -100.0)
    
    (make-pomdp :states '("tiger-left" "tiger-right")
                :actions '("listen" "open-left" "open-right")
                :observations '("hear-left" "hear-right")
                :transitions transitions
                :observations-matrix obs-matrix
                :rewards rewards
                :discount 0.95)))

(test alpha-vector-dot-product
  "Test dot product of α‑vector and belief."
  (let ((alpha (revarie-pomdp::make-alpha-vector '(0.5 0.8 0.2)))
        (belief '(0.3 0.6 0.1)))
    (is (< (abs (- (revarie-pomdp::alpha-dot alpha belief)
                   (+ (* 0.5 0.3) (* 0.8 0.6) (* 0.2 0.1)))) 1e-9))))

(test vector-dominance
  "Test dominance check between α‑vectors."
  (let ((a (revarie-pomdp::make-alpha-vector '(0.9 0.8)))
        (b (revarie-pomdp::make-alpha-vector '(0.7 0.6))))
    (is (revarie-pomdp::vector-dominates a b))
    (is (not (revarie-pomdp::vector-dominates b a)))))

(test value-iteration-convergence
  "Test that value iteration converges and returns α‑vectors."
  (let* ((pomdp (make-tiger-pomdp))
         (alphas (value-iteration pomdp :max-iterations 50 :epsilon 1e-4)))
    (is (not (null alphas)))
    (is (> (length alphas) 0))))

(test belief-value-calculation
  "Test V(b) = max_α α·b."
  (let ((alphas (list (revarie-pomdp::make-alpha-vector '(0.5 0.5))
                      (revarie-pomdp::make-alpha-vector '(0.8 0.2))))
        (belief '(0.5 0.5)))
    (is (< (abs (- (belief-value belief alphas) 0.5)) 1e-9))))

(test optimal-action-selection
  "Test that optimal action is selected correctly."
  (let* ((pomdp (make-tiger-pomdp))
         (alphas (value-iteration pomdp :max-iterations 30 :epsilon 0.01))
         (belief '(0.5 0.5)))
    (let ((action (optimal-action belief alphas)))
      (is (member action '("listen" "open-left" "open-right") :test #'equal)))))

(test prune-dominated-vectors
  "Test that dominated α‑vectors are pruned."
  (let* ((a (revarie-pomdp::make-alpha-vector '(0.9 0.8)))
         (b (revarie-pomdp::make-alpha-vector '(0.7 0.6)))
         (c (revarie-pomdp::make-alpha-vector '(0.5 0.9)))
         (vectors (list a b c))
         (pruned (prune-dominated vectors)))
    ;; a dominates b, so b should be removed
    (is (= (length pruned) 2))
    (is (member a pruned))
    (is (member c pruned))
    (is (not (member b pruned)))))

(defun run-tests ()
  "Run all POMDP value iteration tests."
  (run! 'pomdp-tests))

#+nil
(run-tests)
