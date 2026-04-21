(require :fiveam)
(load "../primary_process.lisp")
(defpackage :revarie-id-tests
  (:use :common-lisp :fiveam :revarie-id))
(in-package :revarie-id-tests)

(test condensation-test
  (let ((pp (revarie-id::make-primary-process)))
    (is (string= "a b c" (revarie-id::condense pp '("a" "b" "c"))))))

(test symbol-test
  (let ((pp (revarie-id::make-primary-process)))
    (revarie-id::symbolize pp "A" "B")
    (is (string= "B" (gethash "A" (revarie-id::primary-process-symbols pp))))))

(run! 'condensation-test)
(run! 'symbol-test)
