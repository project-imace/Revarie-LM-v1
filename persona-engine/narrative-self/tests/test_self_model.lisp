(require :fiveam)
(load "../self_model.lisp")
(defpackage :revarie-narrative-self-tests
  (:use :common-lisp :fiveam :revarie-narrative-self))
(in-package :revarie-narrative-self-tests)

(test model-creation
  (let ((model (revarie-narrative-self::make-self-model :name "Test")))
    (is (string= "Test" (revarie-narrative-self::self-model-name model)))))

(test episode-recording
  (let ((model (revarie-narrative-self::make-self-model)))
    (revarie-narrative-self::remember-episode model :achievement "Test episode")
    (is (= 1 (length (revarie-narrative-self::self-model-significant-episodes model))))))

(run! 'model-creation)
(run! 'episode-recording)
