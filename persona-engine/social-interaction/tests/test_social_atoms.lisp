(require :fiveam)
(load "../social_atoms.lisp")
(defpackage :revarie-social-tests
  (:use :common-lisp :fiveam :revarie-social))
(in-package :revarie-social-tests)

(test trust-building
  (let ((sa (revarie-social::make-social-atoms)))
    (revarie-social::social-reward sa "Bob" 0.9)
    (is (> (revarie-social::trust-bond sa "Bob") 0.1))))

(test proximity-motivation
  (let ((sa (revarie-social::make-social-atoms :attachment-style :anxious)))
    (is (> (revarie-social::proximity-seeking sa "partner" 5.0) 0.5))))

(run! 'trust-building)
(run! 'proximity-motivation)
