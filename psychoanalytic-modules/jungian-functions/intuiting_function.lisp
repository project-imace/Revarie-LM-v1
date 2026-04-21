(defpackage :revarie-jungian
  (:use :common-lisp)
  (:export :make-jung-intuition :intuit :add-association))

(in-package :revarie-jungian)

(defstruct jung-intuition
  (associations (make-hash-table :test 'equal))
  (insights nil))

(defun make-jung-intuition ()
  (make-jung-intuition))

(defun add-association (int source target)
  (push target (gethash source (jung-intuition-associations int)))
  target)

(defun intuit (int seed)
  (let ((possibilities (gethash seed (jung-intuition-associations int))))
    (if possibilities
        (format nil "Intuition suggests: ~A might lead to ~A" seed (first possibilities))
        "The unconscious is silent.")))
