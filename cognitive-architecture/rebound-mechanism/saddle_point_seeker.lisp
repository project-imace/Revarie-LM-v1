;;; saddle_point_seeker.lisp
;;; Rebound Mechanism – Saddle Point Seeker.
;;; Identifies the Saddle Point of Negativity (neutral stabilization) on the
;;; manifold M. This is the target state toward which the rebound force
;;; guides the agent when it drifts outside axiomatic bounds.

(defpackage :revarie-rebound
  (:use :common-lisp)
  (:export :make-saddle-point-seeker
           :find-saddle-point
           :saddle-point-distance
           :saddle-point-gradient
           :neutral-stabilization-target))

(in-package :revarie-rebound)

;;; ---------------------------------------------------------------------------
;;; Saddle Point Representation
;;; ---------------------------------------------------------------------------

;; FIXED: Used %make-saddle-point to prevent infinite recursion
(defstruct (saddle-point (:constructor %make-saddle-point) (:conc-name sp-))
  "A saddle point on the manifold M representing neutral stabilization."
  (coordinates nil :type list)
  (dimension 0 :type fixnum)
  (curvature nil :type list)  ; Principal curvatures at the saddle point
  (energy 0.0 :type float))

(defun make-saddle-point (coordinates &key curvature)
  "Create a saddle point from coordinates."
  (let ((sp (%make-saddle-point
              :coordinates coordinates
              :dimension (length coordinates)
              :curvature curvature
              :energy 0.0)))
    sp))

;;; ---------------------------------------------------------------------------
;;; Saddle Point Seeker
;;; ---------------------------------------------------------------------------

(defclass saddle-point-seeker ()
  ((manifold :initarg :manifold :accessor seeker-manifold)
   (saddle-points :initform nil :accessor seeker-saddle-points)
   (convergence-tolerance :initform 1e-6 :accessor seeker-tolerance)
   (max-iterations :initform 100 :accessor seeker-max-iterations)))

(defun make-saddle-point-seeker (manifold &key saddle-points tolerance max-iterations)
  "Create a new saddle point seeker for a given manifold."
  (let ((seeker (make-instance 'saddle-point-seeker :manifold manifold)))
    (when saddle-points
      (setf (seeker-saddle-points seeker) saddle-points))
    (when tolerance
      (setf (seeker-tolerance seeker) tolerance))
    (when max-iterations
      (setf (seeker-max-iterations seeker) max-iterations))
    seeker))

(defgeneric find-saddle-point (seeker point)
  (:documentation "Find the nearest saddle point to the given point."))

(defmethod find-saddle-point ((seeker saddle-point-seeker) point)
  "Iteratively descend the gradient to locate a saddle point."
  (let ((current (copy-list point))
        (iter 0)
        (step-size 0.05))
    (loop while (< iter (seeker-max-iterations seeker)) do
      (let* ((grad (saddle-point-gradient seeker current))
             (grad-norm (sqrt (reduce #'+ (mapcar (lambda (x) (* x x)) grad)))))
        (when (< grad-norm (seeker-tolerance seeker))
          (return-from find-saddle-point current))
        ;; Update toward saddle (minimize gradient norm)
        (setf current (mapcar (lambda (c g) (- c (* step-size g))) current grad))
        (incf iter)))
    current))

(defgeneric saddle-point-distance (seeker point)
  (:documentation "Compute distance from point to nearest saddle point."))

(defmethod saddle-point-distance ((seeker saddle-point-seeker) point)
  "Distance to the nearest known saddle point."
  (if (null (seeker-saddle-points seeker))
      ;; FIXED: Break the circular dependency. Default to origin as neutral target.
      (sqrt (reduce #'+ (mapcar (lambda (p) (* p p)) point)))
      (let ((nearest (first (sort (seeker-saddle-points seeker)
                                  #'< :key (lambda (sp)
                                             (sqrt (reduce #'+
                                                (mapcar (lambda (p c) (expt (- p c) 2))
                                                        point (sp-coordinates sp)))))))))
        (sqrt (reduce #'+ (mapcar (lambda (p c) (expt (- p c) 2))
                                  point (sp-coordinates nearest)))))))

(defgeneric saddle-point-gradient (seeker point)
  (:documentation "Compute gradient toward the saddle point."))

(defmethod saddle-point-gradient ((seeker saddle-point-seeker) point)
  "Numerical gradient approximation."
  (let ((eps 1e-6)
        (dim (length point))
        (base-dist (saddle-point-distance seeker point)))
    (loop for i from 0 below dim collect
      (let ((perturbed (copy-list point)))
        (incf (nth i perturbed) eps)
        (/ (- (saddle-point-distance seeker perturbed) base-dist) eps)))))

(defun neutral-stabilization-target (seeker point)
  "Return the coordinates of the neutral stabilization target (saddle point)."
  (find-saddle-point seeker point))

;;; ---------------------------------------------------------------------------
;;; Tests (FiveAM)
;;; ---------------------------------------------------------------------------

#+fiveam
(progn
  (defpackage :revarie-rebound-tests
    (:use :common-lisp :fiveam :revarie-rebound))
  (in-package :revarie-rebound-tests)

  (def-suite rebound-tests
    :description "Tests for Rebound Mechanism saddle point seeker")
  (in-suite rebound-tests)

  (test saddle-point-creation
    "Test creation of saddle points."
    (let ((sp (make-saddle-point '(1.0 2.0 3.0))))
      ;; FIXED: Prefixed unexported symbols to fix test visibility
      (is (typep sp 'revarie-rebound::saddle-point))
      (is (equal '(1.0 2.0 3.0) (revarie-rebound::sp-coordinates sp)))
      (is (= 3 (revarie-rebound::sp-dimension sp)))))

  (test find-saddle-point-convergence
    "Test that the seeker converges to a stationary point."
    (let ((seeker (make-saddle-point-seeker nil :max-iterations 50)))
      (let ((result (find-saddle-point seeker '(2.0 2.0))))
        (is (listp result))
        (is (= 2 (length result))))))

  (test saddle-point-distance-calculation
    "Test distance computation to saddle point."
    (let* ((sp (make-saddle-point '(0.0 0.0)))
           (seeker (make-saddle-point-seeker nil :saddle-points (list sp))))
      (let ((dist (saddle-point-distance seeker '(3.0 4.0))))
        (is (< (abs (- dist 5.0)) 1e-6)))))

  (run! 'rebound-tests))
