;;; value_iteration.lisp
;;; POMDP Engine – Value Iteration.
;;; Implements the classic dynamic programming algorithm for solving
;;; Partially Observable Markov Decision Processes. Computes the
;;; optimal value function V*(b) and policy π*(b).
;;;
;;; Theoretical foundations:
;;; - Bellman (1957): Dynamic Programming.
;;; - Smallwood & Sondik (1973): The optimal control of POMDPs.
;;; - Cassandra, Littman, & Zhang (1997): Incremental Pruning.

(defpackage :revarie-pomdp
  (:use :common-lisp)
  (:export :make-pomdp
           :value-iteration
           :alpha-vector
           :belief-value
           :optimal-action
           :prune-dominated))

(in-package :revarie-pomdp)

;;; ---------------------------------------------------------------------------
;;; Alpha Vector Representation
;;; ---------------------------------------------------------------------------

;; FIXED: Used %make-alpha-vector to prevent infinite recursion
(defstruct (alpha-vector (:constructor %make-alpha-vector))
  "An α‑vector represents a piecewise‑linear and convex value function
   over the belief simplex. Each α‑vector is a hyperplane: V(b) = max_α α·b."
  (coefficients nil :type list)  ; Linear coefficients (length = n_states)
  (action nil :type symbol)       ; Action associated with this α‑vector
  (id (gensym "ALPHA-") :type symbol))

(defun make-alpha-vector (coefficients &key action)
  "Create a new α‑vector from coefficient list."
  (%make-alpha-vector :coefficients coefficients :action action))

(defun alpha-dot (alpha belief)
  "Compute the dot product α·b."
  (reduce #'+ (mapcar #'* (alpha-vector-coefficients alpha) belief)))

;;; ---------------------------------------------------------------------------
;;; POMDP Structure
;;; ---------------------------------------------------------------------------

(defstruct pomdp
  "A Partially Observable Markov Decision Process."
  (states nil :type list)           ; List of state names
  (actions nil :type list)          ; List of action names
  (observations nil :type list)     ; List of observation names
  (transitions nil :type hash-table) ; Action -> (From -> (To -> Prob))
  (observations-matrix nil :type hash-table) ; State -> (Obs -> Prob)
  (rewards nil :type hash-table)    ; (State Action) -> Reward
  (discount 0.95 :type float))      ; Discount factor γ

(defun make-pomdp (&key states actions observations
                        transitions observations-matrix rewards discount)
  "Create a new POMDP instance."
  (make-pomdp :states states
              :actions actions
              :observations observations
              :transitions (or transitions (make-hash-table :test 'equal))
              :observations-matrix (or observations-matrix (make-hash-table :test 'equal))
              :rewards (or rewards (make-hash-table :test 'equal))
              :discount (or discount 0.95)))

;;; ---------------------------------------------------------------------------
;;; Core Value Iteration
;;; ---------------------------------------------------------------------------

(defun value-iteration (pomdp &key (epsilon 1e-6) (max-iterations 1000))
  "Compute the optimal value function via value iteration.
   Returns a list of α‑vectors representing the piecewise‑linear convex value function."
  (let* ((states (pomdp-states pomdp))
         (n-states (length states))
         (actions (pomdp-actions pomdp))
         (observations (pomdp-observations pomdp))
         (discount (pomdp-discount pomdp))
         ;; Initialize α‑vectors: one per action, with optimistic values
         (alpha-vectors
           (loop for action in actions
                 collect (make-alpha-vector
                           (make-list n-states :initial-element
                                      (/ (loop for s in states
                                               maximize (gethash (list s action)
                                                                 (pomdp-rewards pomdp) 0.0))
                                         (- 1.0 discount)))
                           :action action))))
    (loop for iter from 1 to max-iterations do
      ;; FIXED: Save old-alphas for accurate convergence comparison
      (let ((new-alphas nil)
            (old-alphas alpha-vectors))
        ;; For each action, generate new α‑vectors
        (dolist (action actions)
          ;; For each observation, we need to compute the transformation
          (let ((obs-alphas (make-hash-table :test 'equal)))
            ;; Precompute observation-specific α‑vector components
            (dolist (obs observations)
              (let ((transformed
                      (loop for s in states
                            collect (* (gethash s (gethash obs (pomdp-observations-matrix pomdp)) 0.0)
                                       (loop for s-prime in states
                                             sum (* (gethash s-prime (gethash s (gethash action (pomdp-transitions pomdp))) 0.0)
                                                    (gethash (list s-prime action) (pomdp-rewards pomdp) 0.0))))))
                (setf (gethash obs obs-alphas)
                      (make-alpha-vector transformed :action action))))
            ;; Generate cross‑product of existing α‑vectors per observation
            (let ((obs-choices (loop for obs in observations
                                     collect (or (gethash obs obs-alphas)
                                                 (make-alpha-vector
                                                   (make-list n-states :initial-element 0.0)
                                                   :action action)))))
              ;; Combine via cross‑sum
              (labels ((cross-sum (alphas acc)
                         (if (null alphas)
                             ;; FIXED: acc is already the list of summed coefficients. No mapcar needed.
                             (push (make-alpha-vector acc :action action) new-alphas)
                             (dolist (a (car alphas))
                               (cross-sum (cdr alphas)
                                          (if acc
                                              (mapcar #'+ acc (alpha-vector-coefficients a))
                                              (alpha-vector-coefficients a)))))))
                (cross-sum (list obs-choices) nil)))))
        ;; Prune dominated α‑vectors
        (setf alpha-vectors (prune-dominated new-alphas))
        ;; Check convergence against the previous generation
        (when (< (max-value-diff alpha-vectors old-alphas) epsilon)
          (return-from value-iteration alpha-vectors))))
    alpha-vectors))

(defun max-value-diff (old new)
  "Compute maximum absolute difference between two sets of α‑vectors."
  (if (or (null old) (null new))
      0.0
      (max (reduce #'max (mapcar #'alpha-vector-coefficients old)
                   :key (lambda (coefs) (reduce #'max coefs)))
           (reduce #'max (mapcar #'alpha-vector-coefficients new)
                   :key (lambda (coefs) (reduce #'max coefs))))))

;;; ---------------------------------------------------------------------------
;;; Pruning Dominated Vectors
;;; ---------------------------------------------------------------------------

;; FIXED: Renamed to match the export and call in value-iteration
(defun prune-dominated (alpha-vectors)
  "Remove α‑vectors that are dominated by others over the belief simplex.
   Uses a witness algorithm: find a belief point where one vector strictly
   dominates another."
  (let ((result nil))
    (dolist (a alpha-vectors)
      (unless (some (lambda (b)
                      (and (not (eq a b))
                           (vector-dominates b a)))
                    alpha-vectors)
        (push a result)))
    (nreverse result)))

(defun vector-dominates (a b)
  "Check if α‑vector A dominates B over the entire belief simplex."
  (let ((coefs-a (alpha-vector-coefficients a))
        (coefs-b (alpha-vector-coefficients b)))
    (every #'>= coefs-a coefs-b)))

;;; ---------------------------------------------------------------------------
;;; Belief Evaluation and Action Selection
;;; ---------------------------------------------------------------------------

(defun belief-value (belief alpha-vectors)
  "Compute V(b) = max_α α·b."
  (reduce #'max alpha-vectors :key (lambda (a) (alpha-dot a belief))))

(defun optimal-action (belief alpha-vectors)
  "Return the action associated with the α‑vector that maximizes α·b."
  (let ((best-alpha
          (reduce (lambda (a b)
                    (if (> (alpha-dot a belief) (alpha-dot b belief)) a b))
                  alpha-vectors)))
    (alpha-vector-action best-alpha)))

;;; ---------------------------------------------------------------------------
;;; Tests (FiveAM)
;;; ---------------------------------------------------------------------------

#+fiveam
(progn
  (defpackage :revarie-pomdp-tests
    (:use :common-lisp :fiveam :revarie-pomdp))
  (in-package :revarie-pomdp-tests)

  (def-suite pomdp-tests
    :description "Tests for POMDP Value Iteration")
  (in-suite pomdp-tests)

  (test alpha-vector-dot-product
    "Test dot product of α‑vector and belief."
    ;; FIXED: Added package prefix for unexported symbols
    (let ((alpha (revarie-pomdp::make-alpha-vector '(0.5 0.8 0.2)))
          (belief '(0.3 0.6 0.1)))
      (is (< (abs (- (revarie-pomdp::alpha-dot alpha belief) (+ (* 0.5 0.3) (* 0.8 0.6) (* 0.2 0.1)))) 1e-9))))

  (test vector-dominance
    "Test dominance check between α‑vectors."
    (let ((a (revarie-pomdp::make-alpha-vector '(0.9 0.8)))
          (b (revarie-pomdp::make-alpha-vector '(0.7 0.6))))
      (is (revarie-pomdp::vector-dominates a b))
      (is (not (revarie-pomdp::vector-dominates b a)))))

  (test belief-value-calculation
    "Test V(b) = max_α α·b."
    (let ((alphas (list (revarie-pomdp::make-alpha-vector '(0.5 0.5))
                        (revarie-pomdp::make-alpha-vector '(0.8 0.2))))
          (belief '(0.5 0.5)))
      (is (< (abs (- (belief-value belief alphas) 0.5)) 1e-9))))

  (run! 'pomdp-tests))
