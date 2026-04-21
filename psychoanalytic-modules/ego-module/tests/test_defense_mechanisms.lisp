(require :fiveam)
(load "../defense_mechanisms.lisp")
(defpackage :revarie-ego-tests (:use :common-lisp :fiveam :revarie-ego))
(in-package :revarie-ego-tests)

(test repression-test
  (let ((ego (revarie-ego::make-ego-state)))
    (revarie-ego::repress ego "secret")
    (is (member "secret" (revarie-ego::ego-state-repressed ego) :test #'equal))))

(run! 'repression-test)
