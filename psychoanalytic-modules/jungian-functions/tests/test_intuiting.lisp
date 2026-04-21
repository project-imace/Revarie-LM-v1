(require :fiveam)
(load "../intuiting_function.lisp")
(defpackage :revarie-jungian-tests
  (:use :common-lisp :fiveam :revarie-jungian))
(in-package :revarie-jungian-tests)

(test association-test
  (let ((int (revarie-jungian::make-intuiting-function)))
    (revarie-jungian::add-association int "fire" "heat")
    (is (not (null (revarie-jungian::get-associations int "fire"))))))

(test intuition-test
  (let ((int (revarie-jungian::make-intuiting-function)))
    (revarie-jungian::add-association int "cloud" "rain")
    (let ((insight (revarie-jungian::intuit int "cloud rain")))
      (is (stringp insight)))))

(run! 'association-test)
(run! 'intuition-test)
