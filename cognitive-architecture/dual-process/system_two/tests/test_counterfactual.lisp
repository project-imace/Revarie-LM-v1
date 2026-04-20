;;; test_counterfactual.lisp
;;; Unit tests for counterfactual simulator.

(require :fiveam)

(defpackage :revarie-system-two-tests
  (:use :common-lisp :fiveam)
  (:import-from :revarie-system-two
                :create-world
                :make-counterfactual
                :evaluate
                :compare-worlds
                :possible-world-p))

(in-package :revarie-system-two-tests)

(def-suite system-two-tests
  :description "Tests for System 2 counterfactual reasoning.")

(in-suite system-two-tests)

(test world-creation
  "Test creation of possible worlds."
  (let ((world (create-world :facts '(("sky" . "blue") ("grass" . "green")))))
    (is (possible-world-p world))
    (is (equal "blue" (evaluate world "sky")))
    (is (equal "green" (evaluate world "grass")))))

(test counterfactual-reasoning
  "Test creation and evaluation of counterfactual worlds."
  (let* ((actual (create-world :facts '(("sky" . "blue"))))
         (counterfactual (make-counterfactual actual :altered-facts '(("sky" . "red")))))
    (is (equal "blue" (evaluate actual "sky")))
    (is (equal "red" (evaluate counterfactual "sky")))
    (is (equal (list '("sky" "blue" "red")) (compare-worlds actual counterfactual)))))

(test empty-query
  "Test evaluation of non-existent facts."
  (let ((world (create-world)))
    (is (null (evaluate world "nonexistent")))))

(run! 'system-two-tests)
