;;; primary_process.lisp – Id Module: Primary Process Thinking

(defpackage :revarie-id
  (:use :common-lisp)
  (:export :make-primary-process
           :condense
           :displace
           :symbolize
           :free-associate
           :dream-work
           :primary-process-thought
           :get-cathexes))

(in-package :revarie-id)

(require :cl-ppcre)

(defstruct primary-process
  (associations (make-hash-table :test 'equal))
  (symbols (make-hash-table :test 'equal))
  (cathexes (make-hash-table :test 'equal))
  (history nil)
  (max-history 500))

(defun hash-table-keys (ht)
  (loop for k being the hash-keys of ht collect k))

(defun condense (pp thoughts &key (separator " "))
  (let ((result (format nil "~{~A~^~A~}" thoughts separator)))
    (push (list :condense thoughts result) (primary-process-history pp))
    result))

(defun displace (pp source target &key (intensity 1.0))
  (let ((current (gethash source (primary-process-cathexes pp) 0.0)))
    (setf (gethash source (primary-process-cathexes pp)) (- current (* current intensity)))
    (incf (gethash target (primary-process-cathexes pp) 0.0) (* current intensity))
    (setf (gethash source (primary-process-associations pp)) target))
  target)

(defun symbolize (pp concept symbol &key (bidirectional t))
  (setf (gethash concept (primary-process-symbols pp)) symbol)
  (when bidirectional (setf (gethash symbol (primary-process-symbols pp)) concept))
  symbol)

(defun invest (pp concept amount)
  (incf (gethash concept (primary-process-cathexes pp) 0.0) amount))

(defun free-associate (pp seed depth)
  (labels ((associate (concept remaining)
             (if (zerop remaining)
                 (list concept)
                 (let ((next (or (gethash concept (primary-process-associations pp))
                                 (first (hash-table-keys (primary-process-associations pp)))
                                 concept)))
                   (cons concept (associate next (1- remaining)))))))
    (associate seed depth)))

(defun primary-process-thought (pp input &key (chaos 0.5))
  (let* ((words (cl-ppcre:split "\\s+" input))
         (condensed (condense pp words))
         (displaced (if (> chaos 0.4)
                        (displace pp condensed (or (first (hash-table-keys (primary-process-associations pp))) "id-echo"))
                        condensed)))
    displaced))

(defun get-cathexes (pp)
  (let ((result nil))
    (maphash (lambda (k v) (push (cons k v) result)) (primary-process-cathexes pp))
    result))
