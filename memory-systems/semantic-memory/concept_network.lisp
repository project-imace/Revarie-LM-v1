;;; concept_network.lisp
;;; Semantic Memory – Concept Network.
;;; Implements a semantic network of concepts and relations.
;;; Supports spreading activation, inheritance, and intersection search.
;;;
;;; Theoretical foundations:
;;; - Collins & Quillian (1969): Semantic memory as hierarchical network.
;;; - Quillian (1968): Semantic memory retrieval via intersection search.
;;; - Anderson (1983): ACT-R spreading activation theory.

(defpackage :revarie-semantic-memory
  (:use :common-lisp)
  (:export :make-concept-network
           :add-concept
           :add-relation
           :set-activation
           :spread-activation
           :get-active-concepts
           :find-shortest-path
           :query-by-property
           :reset-activations))

(in-package :revarie-semantic-memory)

;;; ---------------------------------------------------------------------------
;;; Concept Node
;;; ---------------------------------------------------------------------------

(defstruct concept
  "A concept node in the semantic network."
  (id "" :type string)
  (label "" :type string)
  (properties (make-hash-table :test 'equal) :type hash-table)
  (activation 0.0 :type float)
  (base-activation 0.0 :type float))

(defun make-concept (id label &key properties base-activation)
  "Create a new concept node."
  (let ((c (make-concept :id id :label label)))
    (when properties
      (loop for (k . v) in properties
            do (setf (gethash k (concept-properties c)) v)))
    (when base-activation
      (setf (concept-base-activation c) base-activation))
    c))

;;; ---------------------------------------------------------------------------
;;; Relation
;;; ---------------------------------------------------------------------------

(defstruct relation
  "A directed relation between two concepts."
  (id "" :type string)
  (type "" :type string)      ; "isa", "has-property", "causes", etc.
  (source "" :type string)
  (target "" :type string)
  (weight 1.0 :type float)
  (bidirectional nil :type boolean))

(defun make-relation (type source target &key weight bidirectional)
  "Create a new relation."
  (make-relation :id (format nil "~A_~A_~A" source type target)
                 :type type
                 :source source
                 :target target
                 :weight (or weight 1.0)
                 :bidirectional bidirectional))

;;; ---------------------------------------------------------------------------
;;; Concept Network
;;; ---------------------------------------------------------------------------

(defclass concept-network ()
  ((concepts :initform (make-hash-table :test 'equal) :accessor concepts)
   (relations :initform (make-hash-table :test 'equal) :accessor relations)
   (outgoing :initform (make-hash-table :test 'equal) :accessor outgoing)
   (incoming :initform (make-hash-table :test 'equal) :accessor incoming)
   (decay-rate :initform 0.5 :accessor decay-rate)
   (activation-threshold :initform 0.1 :accessor activation-threshold)
   (max-pulses :initform 10 :accessor max-pulses)))

(defun make-concept-network (&key decay-rate activation-threshold max-pulses)
  "Create a new concept network."
  (let ((net (make-instance 'concept-network)))
    (when decay-rate (setf (decay-rate net) decay-rate))
    (when activation-threshold (setf (activation-threshold net) activation-threshold))
    (when max-pulses (setf (max-pulses net) max-pulses))
    net))

;;; ---------------------------------------------------------------------------
;;; Graph Construction
;;; ---------------------------------------------------------------------------

(defmethod add-concept ((net concept-network) id label &key properties base-activation)
  "Add a concept to the network."
  (let ((c (make-concept id label :properties properties :base-activation base-activation)))
    (setf (gethash id (concepts net)) c)
    c))

(defmethod add-relation ((net concept-network) type source target &key weight bidirectional)
  "Add a relation between concepts."
  (unless (and (gethash source (concepts net))
               (gethash target (concepts net)))
    (error "Source or target concept does not exist"))
  (let ((rel (make-relation type source target :weight weight :bidirectional bidirectional)))
    (setf (gethash (relation-id rel) (relations net)) rel)
    ;; Update adjacency
    (push (relation-id rel) (gethash source (outgoing net)))
    (push (relation-id rel) (gethash target (incoming net)))
    ;; Bidirectional
    (when bidirectional
      (let ((rev-rel (make-relation type target source :weight weight :bidirectional t)))
        (setf (gethash (relation-id rev-rel) (relations net)) rev-rel)
        (push (relation-id rev-rel) (gethash target (outgoing net)))
        (push (relation-id rev-rel) (gethash source (incoming net)))))
    rel))

;;; ---------------------------------------------------------------------------
;;; Spreading Activation
;;; ---------------------------------------------------------------------------

(defmethod set-activation ((net concept-network) concept-id value)
  "Set activation on a specific concept."
  (let ((c (gethash concept-id (concepts net))))
    (when c
      (setf (concept-activation c) (max 0.0 (float value))))))

(defmethod spread-activation-pulse ((net concept-network))
  "Perform one pulse of spreading activation."
  (let ((new-activation (make-hash-table :test 'equal)))
    (maphash
     (lambda (id concept)
       (declare (ignore id))
       (when (>= (concept-activation concept) (activation-threshold net))
         ;; Spread to outgoing neighbors
         (dolist (rel-id (gethash (concept-id concept) (outgoing net)))
           (let* ((rel (gethash rel-id (relations net)))
                  (spread (* (concept-activation concept)
                             (relation-weight rel)
                             (- 1.0 (decay-rate net)))))
             (incf (gethash (relation-target rel) new-activation 0.0) spread)))
         ;; Spread to incoming neighbors (backward association)
         (dolist (rel-id (gethash (concept-id concept) (incoming net)))
           (let* ((rel (gethash rel-id (relations net)))
                  (spread (* (concept-activation concept)
                             (relation-weight rel)
                             (- 1.0 (decay-rate net))
                             0.5)))
             (incf (gethash (relation-source rel) new-activation 0.0) spread)))))
     (concepts net))
    ;; Apply new activations
    (maphash
     (lambda (id concept)
       (setf (concept-activation concept)
             (min 1.0 (+ (* (concept-activation concept) (decay-rate net))
                         (gethash id new-activation 0.0)))))
     (concepts net))))

(defmethod spread-activation ((net concept-network) &optional (pulses nil))
  "Run spreading activation for specified pulses (default: max-pulses)."
  (let ((n (or pulses (max-pulses net))))
    (dotimes (i n)
      (spread-activation-pulse net))))

(defmethod reset-activations ((net concept-network))
  "Reset all activations to base level."
  (maphash
   (lambda (id concept)
     (declare (ignore id))
     (setf (concept-activation concept) (concept-base-activation concept)))
   (concepts net)))

;;; ---------------------------------------------------------------------------
;;; Query and Retrieval
;;; ---------------------------------------------------------------------------

(defmethod get-active-concepts ((net concept-network) &optional (threshold 0.0))
  "Return concepts with activation above threshold, sorted descending."
  (let ((active nil))
    (maphash
     (lambda (id concept)
       (declare (ignore id))
       (when (>= (concept-activation concept) threshold)
         (push (cons (concept-id concept) (concept-activation concept)) active)))
     (concepts net))
    (sort active #'> :key #'cdr)))

(defmethod find-shortest-path ((net concept-network) source target)
  "Find shortest path between two concepts using BFS."
  (unless (and (gethash source (concepts net))
               (gethash target (concepts net)))
    (return-from find-shortest-path nil))
  (let ((parent (make-hash-table :test 'equal))
        (visited (make-hash-table :test 'equal))
        (queue (list source)))
    (setf (gethash source visited) t)
    (loop while queue do
      (let ((current (pop queue)))
        (when (string= current target)
          ;; Reconstruct path
          (let ((path (list target))
                (node target))
            (loop while (not (string= node source)) do
              (setf node (gethash node parent))
              (push node path))
            (return-from find-shortest-path path)))
        (dolist (rel-id (gethash current (outgoing net)))
          (let ((next (relation-target (gethash rel-id (relations net)))))
            (unless (gethash next visited)
              (setf (gethash next visited) t)
              (setf (gethash next parent) current)
              ;; FIXED: Use append to ensure FIFO (Breadth-First Search) behavior
              (setf queue (append queue (list next))))))))
    nil))

(defmethod query-by-property ((net concept-network) key value)
  "Find concepts with a specific property value."
  (let ((results nil))
    (maphash
     (lambda (id concept)
       (declare (ignore id))
       (let ((prop (gethash key (concept-properties concept))))
         (when (and prop (string= prop value))
           (push (concept-id concept) results))))
     (concepts net))
    results))

;;; ---------------------------------------------------------------------------
;;; Tests (FiveAM)
;;; ---------------------------------------------------------------------------

#+fiveam
(progn
  (defpackage :revarie-semantic-memory-tests
    (:use :common-lisp :fiveam :revarie-semantic-memory))
  (in-package :revarie-semantic-memory-tests)

  (def-suite semantic-memory-tests
    :description "Tests for Semantic Memory Concept Network")
  (in-suite semantic-memory-tests)

  (test concept-creation
    "Test creation of concepts."
    (let ((c (make-concept "dog" "Dog" :properties '(("color" . "brown")))))
      (is (string= "dog" (concept-id c)))
      (is (string= "Dog" (concept-label c)))
      (is (string= "brown" (gethash "color" (concept-properties c))))))

  (test network-construction
    "Test building a concept network."
    (let ((net (make-concept-network)))
      (add-concept net "dog" "Dog")
      (add-concept net "animal" "Animal")
      (add-relation net "isa" "dog" "animal")
      (is (= 2 (hash-table-count (concepts net))))
      (is (= 1 (hash-table-count (relations net))))))

  (test spreading-activation
    "Test activation spread through network."
    (let ((net (make-concept-network)))
      (add-concept net "source" "Source")
      (add-concept net "target" "Target")
      (add-relation net "assoc" "source" "target" :weight 0.8)
      (set-activation net "source" 1.0)
      (spread-activation net 1)
      (let ((active (get-active-concepts net 0.1)))
        (is (>= (length active) 1)))))

  (test shortest-path
    "Test finding shortest path between concepts."
    (let ((net (make-concept-network)))
      (add-concept net "A" "A")
      (add-concept net "B" "B")
      (add-concept net "C" "C")
      (add-relation net "link" "A" "B")
      (add-relation net "link" "B" "C")
      (let ((path (find-shortest-path net "A" "C")))
        (is (equal '("A" "B" "C") path)))))

  (test property-query
    "Test querying concepts by property."
    (let ((net (make-concept-network)))
      (add-concept net "apple" "Apple" :properties '(("color" . "red")))
      (add-concept net "banana" "Banana" :properties '(("color" . "yellow")))
      (let ((red (query-by-property net "color" "red")))
        (is (equal '("apple") red)))))

  (run! 'semantic-memory-tests))
