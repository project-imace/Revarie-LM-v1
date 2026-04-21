(require :fiveam)
(load "../recursive_belief_hierarchy.lisp")
(defpackage :revarie-tom-tests (:use :common-lisp :fiveam :revarie-tom))
(in-package :revarie-tom-tests)

(test nested-belief-depth
  (let ((alice-beliefs (create-belief-state "Alice" 1))
        (bob-beliefs (create-belief-state "Bob" 2)))
    (update-belief bob-beliefs "Alice-thinks" alice-beliefs)
    (is (= 2 (belief-state-depth bob-beliefs)))
    (is (string= "Alice" (belief-state-agent (get-belief bob-beliefs "Alice-thinks"))))))

(run! 'nested-belief-depth)
