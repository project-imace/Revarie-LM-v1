;;; ideal_self.lisp – Superego Module: Ego-Ideal
;;; Implements standards of perfection and aspirations.

(defpackage :revarie-superego
  (:use :common-lisp)
  (:export :make-ideal-self
           :set-ideal
           :get-ideal
           :evaluate-against-ideal
           :aspire
           :ideal-self-traits
           :ideal-self-perfectionism))

(in-package :revarie-superego)

(defstruct ideal-self
  "The Ego-Ideal: internalized standards of what one 'ought' to be."
  (traits (make-hash-table :test 'equal))
  (aspirations nil)
  (perfectionism 0.6))

;; NOTE: The default constructor make-ideal-self is created by defstruct.

(defun set-ideal (is trait value)
  "Set the target value for an ideal trait."
  (setf (gethash trait (ideal-self-traits is)) (max 0.0 (min 1.0 value))))

(defun get-ideal (is trait)
  "Retrieve ideal value."
  (gethash trait (ideal-self-traits is) 0.5))

(defun evaluate-against-ideal (is trait current-value)
  "Returns :meets, :close, or :fails-short."
  (let* ((ideal (get-ideal is trait))
         (diff (abs (- ideal current-value))))
    (cond ((< diff 0.1) :meets)
          ((< diff 0.3) :close)
          (t :fails-short))))

(defun aspire (is goal)
  "Record a new aspirational goal."
  (push (list :goal goal :timestamp (get-universal-time))
        (ideal-self-aspirations is)))
