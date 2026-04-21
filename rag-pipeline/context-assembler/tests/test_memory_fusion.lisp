(require :fiveam)
(load "../memory_fusion.lisp")
(defpackage :revarie-memory-fusion-tests
  (:use :common-lisp :fiveam :revarie-memory-fusion))
(in-package :revarie-memory-fusion-tests)

(test fusion-basic
  (let ((fragments (list (revarie-memory-fusion::make-memory-fragment :id "1" :content "Hello" :score 0.9))))
    (let ((result (revarie-memory-fusion::fuse-memories fragments)))
      (is (stringp result)))))

(run! 'fusion-basic)
