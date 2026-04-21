(require :fiveam)
(load "../intuiting_function.lisp")
(defpackage :revarie-jungian-tests (:use :common-lisp :fiveam :revarie-jungian))
(in-package :revarie-jungian-tests)

(test intuition-test
  (let ((int (revarie-jungian::make-jung-intuition)))
    (revarie-jungian::add-association int "smoke" "fire")
    (is (search "fire" (revarie-jungian::intuit int "smoke")))))

(run! 'intuition-test)
