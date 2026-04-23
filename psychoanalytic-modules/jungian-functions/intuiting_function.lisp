;;; intuiting_function.lisp – Jungian Intuiting Function
;;;
;;; Implements Jung's Intuiting psychological function: pattern recognition,
;;; perception of possibilities, and unconscious synthesis. Intuition perceives
;;; through holistic impressions, seeing connections and future potentials.
;;;
;;; Theoretical Foundations:
;;; - Jung (1921): "Psychological Types" – Intuition as irrational function
;;;   oriented by unconscious patterns and possibilities.
;;; - von Franz (1971): "The Inferior Function" – Intuition's dialectic with Sensing.
;;; - Bowers et al. (1990): "Intuition in the context of discovery" – pattern
;;;   recognition below conscious threshold.
;;;
;;; Mathematical Model:
;;; - Pattern strength = coherence * novelty * associative_spread
;;; - Possibility generation via Markov chain on associative network
;;; - Archetypal resonance via symbolic matching

(defpackage :revarie-jungian
  (:use :common-lisp)
  (:export :make-intuiting-function
           :intuit
           :see-patterns
           :generate-possibilities
           :get-archetypes
           :add-association
           :get-insights
           :intuition-strength))

(in-package :revarie-jungian)

;;; ---------------------------------------------------------------------------
;;; Intuiting Function State
;;; ---------------------------------------------------------------------------

(defstruct (intuiting-function (:constructor %make-intuiting-function))
  "State of the Intuiting psychological function."
  (name "Intuition" :type string)
  (associations (make-hash-table :test 'equal) :type hash-table)
  (archetypes (make-hash-table :test 'equal) :type hash-table)
  (patterns nil :type list)
  (insights nil :type list)
  (openness 0.7 :type float)
  (pattern-sensitivity 0.6 :type float)
  (intuition-strength 0.5 :type float)
  (history nil :type list))

(defun make-intuiting-function (&key (name "Intuition") (openness 0.7) (sensitivity 0.6))
  "Create a new Intuiting function instance."
  (let ((int (%make-intuiting-function :name name :openness openness :pattern-sensitivity sensitivity)))
    (initialize-archetypes int)
    int))

(defun initialize-archetypes (int)
  "Initialize Jungian archetypes for pattern recognition."
  (let ((archetypes '(("hero" . "courage, overcoming, victory")
                      ("shadow" . "darkness, hidden, unconscious")
                      ("anima" . "soul, feminine, connection")
                      ("animus" . "spirit, masculine, assertion")
                      ("wise_old_man" . "wisdom, guidance, knowledge")
                      ("great_mother" . "nurture, creation, nature")
                      ("trickster" . "chaos, mischief, transformation")
                      ("self" . "wholeness, integration, center"))))
    (loop for (name . meaning) in archetypes
          do (setf (gethash name (intuiting-function-archetypes int)) meaning))))

;;; ---------------------------------------------------------------------------
;;; Associative Network
;;; ---------------------------------------------------------------------------

(defun add-association (int source target &key (weight 1.0) (bidirectional t))
  "Add an associative link between concepts."
  (let ((source-key (string-downcase source))
        (target-key (string-downcase target)))
    (push (cons target-key weight) (gethash source-key (intuiting-function-associations int)))
    (when bidirectional
      (push (cons source-key weight) (gethash target-key (intuiting-function-associations int)))))
  target)

(defun get-associations (int concept)
  "Get all associations for a concept with weights."
  (gethash (string-downcase concept) (intuiting-function-associations int)))

(defun spread-activation (int seed depth &key (decay 0.5))
  "Spread activation through associative network."
  (let ((activated (make-hash-table :test 'equal))
        (current (list (cons (string-downcase seed) 1.0))))
    (setf (gethash (string-downcase seed) activated) 1.0)
    (loop for d from 1 to depth
          for next-activations = nil
          do (loop for (concept . strength) in current
                   for associations = (get-associations int concept)
                   do (loop for (assoc . weight) in associations
                            for spread = (* strength weight (expt decay d))
                            do (incf (gethash assoc activated 0.0) spread)
                               (push (cons assoc spread) next-activations)))
             (setf current next-activations))
    activated))

;;; ---------------------------------------------------------------------------
;;; Pattern Recognition
;;; ---------------------------------------------------------------------------

(defun see-patterns (int items &key (min-coherence 0.3))
  "Detect patterns among a set of items.
   Returns a list of (pattern-name coherence evidence)."
  (let ((patterns nil)
        (co-occurrence (make-hash-table :test 'equal)))
    
    ;; Build co-occurrence matrix
    (loop for i in items
          do (loop for j in items
                   unless (string= i j)
                   do (let ((key (if (string< i j) (cons i j) (cons j i))))
                        (incf (gethash key co-occurrence 0)))))
    
    ;; Extract significant co-occurrences
    (maphash (lambda (pair count)
               (when (> count 1)
                 (let* ((coherence (/ count (length items) 2.0))
                        (pattern-name (format nil "~A_~A" (car pair) (cdr pair))))
                   (when (> coherence min-coherence)
                     (push (list pattern-name coherence pair) patterns)))))
             co-occurrence)
    
    ;; Sort by coherence
    (setf patterns (sort patterns #'> :key #'second))
    
    ;; Store discovered patterns
    (setf (intuiting-function-patterns int) 
          (append patterns (intuiting-function-patterns int)))
    
    patterns))

;;; ---------------------------------------------------------------------------
;;; Archetypal Resonance
;;; ---------------------------------------------------------------------------

(defun detect-archetype (int content)
  "Detect which archetype resonates with the given content."
  (let ((scores (make-hash-table :test 'equal))
        (content-lower (string-downcase content)))
    (maphash (lambda (archetype meaning)
               (let ((meaning-lower (string-downcase meaning)))
                 (loop for word in (cl-ppcre:split "\\s*,\\s*" meaning-lower)
                       when (search word content-lower)
                       do (incf (gethash archetype scores 0) 1))))
             (intuiting-function-archetypes int))
    
    (let ((best nil) (best-score 0))
      (maphash (lambda (archetype score)
                 (when (> score best-score)
                   (setf best archetype best-score score)))
               scores)
      (values best best-score))))

;;; ---------------------------------------------------------------------------
;;; Possibility Generation
;;; ---------------------------------------------------------------------------

(defun generate-possibilities (int seed &key (count 5) (creativity 0.7))
  "Generate future possibilities from a seed concept.
   Uses Markov chain on associative network with randomness factor."
  (let* ((seed-key (string-downcase seed))
         (activated (spread-activation int seed-key 3 :decay 0.4))
         (possibilities nil)
         (current seed-key))
    
    (dotimes (i count)
      (let* ((associations (get-associations int current))
             (total-weight (reduce #'+ associations :key #'cdr)))
        (if (or (null associations) (< total-weight 0.01))
            (push (format nil "possibility_~D" i) possibilities)
            (let* ((random-factor (* creativity (random 1.0)))
                   (adjusted-weights
                     (mapcar (lambda (a)
                               (cons (car a) (+ (cdr a) random-factor)))
                             associations))
                   (selected (weighted-random-choice adjusted-weights)))
              (push selected possibilities)
              (setf current selected)))))
    
    (nreverse possibilities)))

(defun weighted-random-choice (weighted-items)
  "Select an item randomly with given weights."
  (let ((total (reduce #'+ weighted-items :key #'cdr)))
    (if (zerop total)
        (caar weighted-items)
        (let ((r (random total)))
          (loop for (item . weight) in weighted-items
                do (decf r weight)
                   (when (<= r 0)
                     (return item)))))))

;;; ---------------------------------------------------------------------------
;;; Core Intuition Function
;;; ---------------------------------------------------------------------------

(defun intuit (int input &key (depth 2))
  "Primary intuition function: synthesize patterns and generate insight."
  (let* ((words (cl-ppcre:split "\\s+" input))
         (patterns (when (> (length words) 2) (see-patterns int words)))
         (activated (spread-activation int (first words) depth))
         (archetype (multiple-value-bind (arch score) (detect-archetype int input)
                      (when (> score 1) arch)))
         (possibilities (generate-possibilities int (first words) :count 3)))
    
    ;; Synthesize insight
    (let ((insight
            (cond
              (patterns
               (format nil "I sense a pattern: ~A appears connected to ~A"
                       (first words) (third patterns)))
              (archetype
               (format nil "This evokes the ~A archetype" archetype))
              (t
               (format nil "Possibilities emerge: ~{~A~^, ~}" possibilities)))))
      
      ;; Record insight
      (push (list :input input :insight insight :timestamp (get-universal-time))
            (intuiting-function-insights int))
      
      ;; Update intuition strength based on pattern detection success
      (when patterns
        (setf (intuiting-function-intuition-strength int)
              (min 1.0 (+ (intuiting-function-intuition-strength int) 0.05))))
      
      (values insight patterns archetype possibilities))))

;;; ---------------------------------------------------------------------------
;;; Accessors
;;; ---------------------------------------------------------------------------

(defun get-insights (int &optional (n 10))
  "Return recent insights."
  (subseq (intuiting-function-insights int) 0 (min n (length (intuiting-function-insights int)))))

(defun get-archetypes (int)
  "Return list of all archetypes."
  (let ((result nil))
    (maphash (lambda (k v) (push (cons k v) result)) (intuiting-function-archetypes int))
    result))

(defun intuition-strength (int)
  "Return current intuition strength."
  (intuiting-function-intuition-strength int))

;;; ---------------------------------------------------------------------------
;;; Tests
;;; ---------------------------------------------------------------------------

#+fiveam
(progn
  (defpackage :revarie-jungian-tests
    (:use :common-lisp :fiveam :revarie-jungian))
  (in-package :revarie-jungian-tests)

  (def-suite jungian-tests :description "Jungian Intuiting Tests")
  (in-suite jungian-tests)

  (test association-creation
    (let ((int (make-intuiting-function)))
      (revarie-jungian::add-association int "fire" "heat")
      (is (not (null (revarie-jungian::get-associations int "fire"))))))

  (test pattern-detection
    (let ((int (make-intuiting-function)))
      (let ((patterns (revarie-jungian::see-patterns int '("cat" "dog" "cat" "dog" "cat"))))
        (is (not (null patterns))))))

  (test possibility-generation
    (let ((int (make-intuiting-function)))
      (revarie-jungian::add-association int "seed" "flower")
      (revarie-jungian::add-association int "flower" "fruit")
      (let ((poss (revarie-jungian::generate-possibilities int "seed" :count 3)))
        (is (= 3 (length poss))))))

  (test intuition-function
    (let ((int (make-intuiting-function)))
      (revarie-jungian::add-association int "cloud" "rain")
      (revarie-jungian::add-association int "rain" "growth")
      (multiple-value-bind (insight patterns arch poss) (revarie-jungian::intuit int "cloud rain storm")
        (declare (ignore patterns arch poss))
        (is (stringp insight)))))

  (run! 'jungian-tests))
