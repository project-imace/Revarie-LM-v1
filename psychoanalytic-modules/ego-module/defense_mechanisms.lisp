;;; defense_mechanisms.lisp – Ego Module: Defense Mechanisms

(defpackage :revarie-ego
  (:use :common-lisp)
  (:export :make-ego-state
           :defend
           :repress
           :sublimate
           :project
           :ego-state-repressed
           :ego-state-projections))

(in-package :revarie-ego)

(defstruct ego-state
  (repressed nil)
  (projections (make-hash-table :test 'equal))
  (defense-history nil)
  (ego-strength 0.6)
  (energy 0.8))

(defun repress (ego thought)
  (push thought (ego-state-repressed ego))
  (format nil "[repressed] ~A" thought))

(defun sublimate (ego impulse)
  (format nil "[sublimated] ~A" (getf impulse :content)))

(defun project (ego feeling target)
  (setf (gethash feeling (ego-state-projections ego)) target)
  (format nil "~A feels ~A" target feeling))

(defun apply-defense (ego defense impulse)
  (case defense
    (:repression (repress ego (getf impulse :content)))
    (:sublimation (sublimate ego impulse))
    (:projection (project ego (getf impulse :content) "others"))
    (t "[fallback defense]")))

(defun defend (ego impulse &key (moral-cost 0.0) (reality-risk 0.0))
  (let* ((pressure (+ (getf impulse :intensity 0.5) moral-cost reality-risk))
         (defense (if (> pressure 1.5) :repression :sublimation)))
    (apply-defense ego defense impulse)
    (push (list :defense defense :timestamp (get-universal-time)) 
          (ego-state-defense-history ego))
    defense))
