;;; recursive_belief_hierarchy.lisp
;;; Theory of Mind – Recursive Belief Hierarchy.

(defpackage :revarie-tom
  (:use :common-lisp)
  (:export :create-belief-state
           :update-belief
           :get-belief
           :belief-state
           :belief-state-depth))

(in-package :revarie-tom)

(defstruct belief-state
  "Represents what an agent thinks (potentially about another agent)."
  (agent nil)
  (beliefs (make-hash-table :test 'equal))
  (depth 1))

(defun create-belief-state (agent depth)
  "Factory to create a belief state for a specific agent at a specific depth."
  (make-belief-state :agent agent :depth depth))

(defun update-belief (state proposition probability-or-nested-state)
  "Update a proposition with a probability or a nested belief state."
  (setf (gethash proposition (belief-state-beliefs state)) 
        probability-or-nested-state))

(defun get-belief (state proposition)
  "Retrieve a belief. Returns 0.5 (uncertainty) if not found."
  (gethash proposition (belief-state-beliefs state) 0.5))
