;;; memory_fusion.lisp – RAG Pipeline: Memory Fusion
;;;
;;; Fuses multiple retrieved memory fragments into a coherent narrative.
;;; Resolves contradictions, prioritizes salient information, and maintains
;;; temporal consistency across the 14‑day study.
;;;
;;; Theoretical Foundations:
;;; - Conway & Pleydell-Pearce (2000): Self-Memory System
;;; - Bartlett (1932): Remembering – reconstructive memory

(defpackage :revarie-memory-fusion
  (:use :common-lisp)
  (:export :fuse-memories
           :resolve-contradictions
           :prioritize-by-salience
           :format-as-narrative))

(in-package :revarie-memory-fusion)

;;; ---------------------------------------------------------------------------
;;; Memory Fusion
;;; ---------------------------------------------------------------------------

(defstruct memory-fragment
  "A single retrieved memory fragment."
  (id "" :type string)
  (content "" :type string)
  (score 0.0 :type float)
  (day-number 0 :type fixnum)
  (memory-type :chat :type keyword)
  (emotional-tone :neutral :type keyword)
  (salience 0.0 :type float))

(defun fuse-memories (fragments &key (max-fragments 5) (persona :samara))
  "Fuse multiple memory fragments into a coherent context string."
  (let* ((prioritized (prioritize-by-salience fragments max-fragments))
         (resolved (resolve-contradictions prioritized))
         (narrative (format-as-narrative resolved persona)))
    narrative))

(defun prioritize-by-salience (fragments max-count)
  "Prioritize fragments by score, recency, and emotional salience."
  (let ((scored
          (mapcar (lambda (f)
                    (let* ((base-score (memory-fragment-score f))
                           (recency-boost (* 0.1 (memory-fragment-day-number f)))
                           (emotion-boost (if (eq (memory-fragment-emotional-tone f) :negative) 0.15 0.0))
                           (final-score (+ base-score recency-boost emotion-boost)))
                      (cons f final-score)))
                  fragments)))
    (mapcar #'car
            (subseq (sort scored #'> :key #'cdr)
                    0 (min max-count (length scored))))))

(defun resolve-contradictions (fragments)
  "Resolve contradictory memories (simplified: keep highest score version)."
  (let ((content-map (make-hash-table :test 'equal)))
    (dolist (f fragments)
      (let* ((key (subseq (memory-fragment-content f) 0 (min 50 (length (memory-fragment-content f)))))
             (existing (gethash key content-map)))
        (when (or (null existing)
                  (> (memory-fragment-score f) (memory-fragment-score existing)))
          (setf (gethash key content-map) f))))
    (loop for v being the hash-values of content-map collect v)))

(defun format-as-narrative (fragments persona)
  "Format fragments as a coherent narrative based on persona."
  (if (null fragments)
      ""
      (let ((lines
              (loop for f in fragments
                    collect (format nil "~A" (memory-fragment-content f)))))
        (if (eq persona :samara)
            (format nil "Here's what I remember:~%~{~A~%~}" lines)
            (format nil "Previous data:~%~{~A~%~}" lines)))))


;;; ---------------------------------------------------------------------------
;;; Tests
;;; ---------------------------------------------------------------------------
