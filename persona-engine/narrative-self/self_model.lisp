;;; self_model.lisp – Narrative Self: Self Model
;;;
;;; Implements a computational model of the narrative self – the ongoing
;;; autobiographical story that maintains identity coherence across time.
;;; Based on narrative psychology and self-memory systems theory.
;;;
;;; Theoretical Foundations:
;;; - Conway & Pleydell-Pearce (2000): Self-Memory System (SMS).
;;; - McAdams (2001): Narrative identity and life stories.
;;; - Dennett (1991): "Consciousness Explained" – self as center of narrative gravity.
;;; - Gallagher (2000): Philosophical conceptions of the self.
;;; - Damasio (1999): "The Feeling of What Happens" – core and autobiographical self.

(defpackage :revarie-narrative-self
  (:use :common-lisp)
  (:export :make-self-model
           :narrate-experience
           :update-self-narrative
           :get-self-narrative
           :get-core-values
           :set-core-value
           :self-consistency
           :identity-strength
           :life-story-summary
           :autobiographical-reasoning
           :remember-episode))

(in-package :revarie-narrative-self)

;;; ---------------------------------------------------------------------------
;;; Self Model Structure
;;; ---------------------------------------------------------------------------

(defstruct (self-model (:constructor %make-self-model))
  "The narrative self – center of autobiographical gravity."
  (name nil :type (or null string))
  (core-values (make-hash-table :test 'equal) :type hash-table)
  (life-themes nil :type list)
  (significant-episodes nil :type list)
  (self-narrative nil :type list)
  (identity-strength 0.5 :type float)
  (narrative-coherence 0.5 :type float)
  (temporal-continuity 0.5 :type float)
  (agency-attribution 0.6 :type float)
  (version-counter 0 :type fixnum)
  (max-narrative-length 1000 :type fixnum)
  (max-episodes 500 :type fixnum))

(defun make-self-model (&key (name nil))
  "Create a new self-model with optional name."
  (let ((model (%make-self-model :name name)))
    (initialize-core-values model)
    model))

(defun initialize-core-values (model)
  "Initialize default core values that define the self."
  (setf (gethash "autonomy" (self-model-core-values model)) 0.7)
  (setf (gethash "connection" (self-model-core-values model)) 0.8)
  (setf (gethash "growth" (self-model-core-values model)) 0.75)
  (setf (gethash "integrity" (self-model-core-values model)) 0.8)
  (setf (gethash "compassion" (self-model-core-values model)) 0.7)
  (setf (gethash "curiosity" (self-model-core-values model)) 0.65)
  (setf (gethash "competence" (self-model-core-values model)) 0.6))

(defun set-core-value (model value-name importance)
  "Set the importance of a core value (0.0 to 1.0)."
  (setf (gethash value-name (self-model-core-values model))
        (max 0.0 (min 1.0 importance))))

(defun get-core-values (model)
  "Return all core values as an alist."
  (let ((values nil))
    (maphash (lambda (k v) (push (cons k v) values))
             (self-model-core-values model))
    values))

;;; ---------------------------------------------------------------------------
;;; Episodic Memory Integration
;;; ---------------------------------------------------------------------------

(defstruct autobiographical-episode
  "A significant episode in the life narrative."
  (id nil :type symbol)
  (timestamp 0 :type integer)
  (event-type nil :type keyword)  ; :achievement, :relationship, :challenge, :insight, :turning-point
  (description "" :type string)
  (emotional-signature nil :type list)  ; (valence intensity)
  (self-relevance 0.5 :type float)
  (integration-level 0.0 :type float)   ; How integrated into narrative
  (tags nil :type list))

(defun remember-episode (model event-type description 
                         &key (self-relevance 0.5) (emotional-signature '(0.0 0.5)) (tags nil))
  "Record a new autobiographical episode."
  (let ((episode (make-autobiographical-episode
                   :id (gensym "EP-")
                   :timestamp (get-universal-time)
                   :event-type event-type
                   :description description
                   :emotional-signature emotional-signature
                   :self-relevance self-relevance
                   :tags tags)))
    (push episode (self-model-significant-episodes model))
    (when (> (length (self-model-significant-episodes model))
             (self-model-max-episodes model))
      (setf (self-model-significant-episodes model)
            (subseq (self-model-significant-episodes model) 
                    0 (self-model-max-episodes model))))
    (update-narrative-coherence model)
    (incf (self-model-version-counter model))
    episode))

(defun find-episodes-by-tag (model tag)
  "Retrieve episodes with a specific tag."
  (remove-if-not (lambda (ep) (member tag (autobiographical-episode-tags ep)))
                 (self-model-significant-episodes model)))

(defun find-episodes-by-type (model event-type)
  "Retrieve episodes of a specific type."
  (remove-if-not (lambda (ep) (eq event-type (autobiographical-episode-event-type ep)))
                 (self-model-significant-episodes model)))

;;; ---------------------------------------------------------------------------
;;; Narrative Construction and Update
;;; ---------------------------------------------------------------------------

(defun narrate-experience (model experience &key (self-relevance 0.5) (emotional-impact 0.5))
  "Transform raw experience into narrative form.
   Returns a narrative fragment that can be integrated into the life story."
  (let* ((event-type (classify-experience experience))
         (narrative-fragment
           (format nil "I experienced ~A. This was a ~A moment. ~A"
                   (first experience)
                   event-type
                   (interpret-emotional-impact emotional-impact event-type))))
    (remember-episode model event-type (first experience)
                      :self-relevance self-relevance
                      :emotional-signature (list (if (> emotional-impact 0.5) 0.6 -0.3)
                                                emotional-impact))
    (push narrative-fragment (self-model-self-narrative model))
    (when (> (length (self-model-self-narrative model))
             (self-model-max-narrative-length model))
      (setf (self-model-self-narrative model)
            (subseq (self-model-self-narrative model) 0 
                    (self-model-max-narrative-length model))))
    (update-self-narrative model)
    narrative-fragment))

(defun classify-experience (experience-tokens)
  "Classify the type of experience based on keywords."
  (let ((text (string-downcase (format nil "~{~A~^ ~}" experience-tokens))))
    (cond
      ((or (search "achieve" text) (search "success" text) (search "complete" text))
       :achievement)
      ((or (search "connect" text) (search "friend" text) (search "together" text)
           (search "relationship" text) (search "love" text))
       :relationship)
      ((or (search "difficult" text) (search "struggle" text) (search "challenge" text)
           (search "fail" text) (search "obstacle" text))
       :challenge)
      ((or (search "realize" text) (search "understand" text) (search "insight" text)
           (search "learn" text) (search "discover" text))
       :insight)
      ((or (search "change" text) (search "transform" text) (search "pivot" text)
           (search "turning point" text))
       :turning-point)
      (t :ordinary))))

(defun interpret-emotional-impact (impact event-type)
  "Interpret emotional impact in narrative terms."
  (cond
    ((> impact 0.7) "It was deeply meaningful to me.")
    ((> impact 0.4) "It affected me significantly.")
    ((< impact 0.2) "It was a small moment, but it stayed with me.")
    ((eq event-type :challenge) "It tested me, but I grew from it.")
    (t "It became part of my story.")))

(defun update-self-narrative (model)
  "Update the coherent self-narrative by integrating recent episodes."
  (let* ((recent-episodes (subseq (self-model-significant-episodes model)
                                  0 (min 20 (length (self-model-significant-episodes model)))))
         (themes (extract-themes recent-episodes))
         (coherence (compute-narrative-coherence recent-episodes)))
    (setf (self-model-life-themes model) themes)
    (setf (self-model-narrative-coherence model) coherence)
    (setf (self-model-temporal-continuity model)
          (compute-temporal-continuity model))
    (update-identity-strength model)
    (incf (self-model-version-counter model))
    model))

(defun extract-themes (episodes)
  "Extract recurring themes from episodes."
  (let ((theme-counts (make-hash-table :test 'equal)))
    (dolist (ep episodes)
      (dolist (tag (autobiographical-episode-tags ep))
        (incf (gethash tag theme-counts 0))))
    (let ((themes nil))
      (maphash (lambda (tag count)
                 (when (> count 1)
                   (push (cons tag count) themes)))
               theme-counts)
      (sort themes #'> :key #'cdr))))

(defun compute-narrative-coherence (episodes)
  "Compute how coherently episodes fit together (0.0 to 1.0)."
  (if (< (length episodes) 2)
      0.5
      (let* ((self-relevance-sum (reduce #'+ (mapcar #'autobiographical-episode-self-relevance episodes)))
             (avg-relevance (/ self-relevance-sum (length episodes)))
             (themes (extract-themes episodes))
             (theme-bonus (min 0.3 (* 0.1 (length themes)))))
        (min 1.0 (+ avg-relevance theme-bonus)))))

(defun compute-temporal-continuity (model)
  "Compute sense of temporal continuity across episodes."
  (let ((episodes (self-model-significant-episodes model)))
    (if (< (length episodes) 2)
        0.5
        (let* ((timestamps (mapcar #'autobiographical-episode-timestamp episodes))
               (sorted (sort timestamps #'<))
               (gaps (loop for i from 1 below (length sorted)
                           collect (- (nth i sorted) (nth (1- i) sorted))))
               (avg-gap (if gaps (/ (reduce #'+ gaps) (length gaps)) 0))
               (continuity (if (> avg-gap (* 30 86400)) 0.3 0.8)))
          (* continuity (self-model-narrative-coherence model))))))

(defun update-identity-strength (model)
  "Update overall identity strength based on coherence and continuity."
  (setf (self-model-identity-strength model)
        (* 0.4 (self-model-narrative-coherence model)
           0.3 (self-model-temporal-continuity model)
           0.3 (self-model-agency-attribution model))))

;;; ---------------------------------------------------------------------------
;;; Narrative Retrieval and Reasoning
;;; ---------------------------------------------------------------------------

(defun get-self-narrative (model &key (format :story))
  "Retrieve the current self-narrative in specified format."
  (case format
    (:story (generate-life-story model))
    (:summary (generate-self-summary model))
    (:themes (self-model-life-themes model))
    (:raw (self-model-self-narrative model))
    (t (generate-self-summary model))))

(defun generate-life-story (model)
  "Generate a coherent life story from episodes."
  (let* ((name (or (self-model-name model) "I"))
         (episodes (subseq (self-model-significant-episodes model)
                           0 (min 10 (length (self-model-significant-episodes model)))))
         (themes (self-model-life-themes model)))
    (format nil "~A am someone who values ~{~A~^, ~}. ~
                 My journey has included ~{~A~^; ~}. ~
                 Through it all, I remain ~A."
            name
            (mapcar #'car (subseq (get-core-values model) 0 3))
            (mapcar #'autobiographical-episode-description episodes)
            (if (> (self-model-identity-strength model) 0.6) "grounded" "evolving"))))

(defun generate-self-summary (model)
  "Generate a brief self-summary."
  (format nil "~A ~A self with ~A identity strength."
          (or (self-model-name model) "This")
          (cond ((> (self-model-narrative-coherence model) 0.7) "coherent")
                ((> (self-model-narrative-coherence model) 0.4) "developing")
                (t "fragmented"))
          (cond ((> (self-model-identity-strength model) 0.7) "strong")
                ((> (self-model-identity-strength model) 0.4) "moderate")
                (t "weak"))))

(defun autobiographical-reasoning (model query)
  "Reason about the self based on autobiographical knowledge."
  (let ((relevant-episodes
          (remove-if-not
           (lambda (ep)
             (search (string-downcase query)
                     (string-downcase (autobiographical-episode-description ep))))
           (self-model-significant-episodes model))))
    (if relevant-episodes
        (format nil "Based on my experience, ~A. ~
                    This connects to my theme of ~A."
                (autobiographical-episode-description (first relevant-episodes))
                (or (caar (self-model-life-themes model)) "growth"))
        "I don't have a direct experience with that, but I can imagine how it might feel.")))

(defun life-story-summary (model)
  "Return a comprehensive summary of the life story."
  (let ((episodes (self-model-significant-episodes model)))
    (values
     (self-model-name model)
     (self-model-identity-strength model)
     (self-model-narrative-coherence model)
     (length episodes)
     (self-model-life-themes model)
     (get-core-values model))))

;;; ---------------------------------------------------------------------------
;;; Consistency and Integrity
;;; ---------------------------------------------------------------------------

(defun self-consistency (model statement)
  "Check if a statement is consistent with the established self-narrative."
  (let* ((themes (self-model-life-themes model))
         (values (get-core-values model))
         (consistency-score 0.5))
    (dolist (theme themes)
      (when (search (car theme) (string-downcase statement))
        (incf consistency-score 0.1)))
    (dolist (value values)
      (when (search (car value) (string-downcase statement))
        (incf consistency-score 0.1)))
    (min 1.0 consistency-score)))

(defun identity-strength (model)
  "Return current identity strength."
  (self-model-identity-strength model))

;;; ---------------------------------------------------------------------------
;;; Tests
;;; ---------------------------------------------------------------------------
