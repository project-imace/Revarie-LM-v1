(require :fiveam)
(load "../ideal_self.lisp")
(defpackage :revarie-superego-tests
  (:use :common-lisp :fiveam :revarie-superego))
(in-package :revarie-superego-tests)

(test trait-evaluation
  (let ((is (revarie-superego::make-ideal-self)))
    (revarie-superego::set-ideal is "honesty" 0.9)
    (is (eq :meets (revarie-superego::evaluate-against-ideal is "honesty" 0.85)))
    (is (eq :fails-short (revarie-superego::evaluate-against-ideal is "honesty" 0.4)))))

(run! 'trait-evaluation)
