;;; social_atoms.lisp – Social Interaction: Social Atoms
;;;
;;; Implements primitive units of social cognition – the building blocks
;;; of social interaction. Based on attachment theory and social baseline theory.
;;;
;;; Theoretical Foundations:
;;; - Bowlby (1969): Attachment theory – secure base, safe haven.
;;; - Coan & Sbarra (2015): Social Baseline Theory.
;;; - Tomasello (2014): Shared intentionality.

(defpackage :revarie-social
  (:use :common-lisp)
  (:export :make-social-atoms
           :secure-base
           :safe-haven
           :proximity-seeking
           :separation-distress
           :shared-attention
           :social-reward
           :trust-bond
           :get-attachment-style
           :set-attachment-style
           :evaluate-social-situation))

(in-package :revarie-social)

;;; ---------------------------------------------------------------------------
;;; Social Atoms State
;;; ---------------------------------------------------------------------------

(defstruct (social-atoms (:constructor %make-social-atoms))
  "Primitive social cognition units."
  (attachment-style :secure :type keyword)  ; :secure, :anxious, :avoidant
  (trust-bonds (make-hash-table :test 'equal) :type hash-table)
  (shared-attention-focus nil :type list)
  (proximity-target nil)
  (separation-timer 0 :type fixnum)
  (social-reward-accumulator 0.0 :type float)
  (history nil :type list))

(defun make-social-atoms (&key (attachment-style :secure))
  "Create a new social atoms instance."
  (%make-social-atoms :attachment-style attachment-style))

(defun get-attachment-style (sa)
  (social-atoms-attachment-style sa))

(defun set-attachment-style (sa style)
  (setf (social-atoms-attachment-style sa) style))

;;; ---------------------------------------------------------------------------
;;; Core Social Primitives
;;; ---------------------------------------------------------------------------

(defun secure-base (sa agent presence)
  "Experience security from attachment figure's presence.
   Returns confidence boost (0.0 to 1.0)."
  (let ((boost (case (social-atoms-attachment-style sa)
                 (:secure 0.3)
                 (:anxious 0.15)
                 (:avoidant 0.05)
                 (t 0.1))))
    (push (list :secure-base agent presence boost (get-universal-time))
          (social-atoms-history sa))
    boost))

(defun safe-haven (sa agent distress-level)
  "Seek comfort from attachment figure when distressed.
   Returns comfort received (0.0 to 1.0)."
  (let* ((trust (gethash agent (social-atoms-trust-bonds sa) 0.1))
         (comfort (* trust distress-level 
                    (case (social-atoms-attachment-style sa)
                      (:secure 0.8)
                      (:anxious 0.6)
                      (:avoidant 0.2)))))
    (push (list :safe-haven agent distress-level comfort (get-universal-time))
          (social-atoms-history sa))
    comfort))

(defun proximity-seeking (sa target distance)
  "Drive to maintain proximity to attachment figure.
   Returns motivation intensity (0.0 to 1.0)."
  (let* ((style-factor (case (social-atoms-attachment-style sa)
                         (:secure 0.5)
                         (:anxious 0.9)
                         (:avoidant 0.1)))
         (normalized-distance (/ (min distance 10.0) 10.0))
         (motivation (* style-factor normalized-distance)))
    (setf (social-atoms-proximity-target sa) target)
    (min 1.0 motivation)))

(defun separation-distress (sa agent duration)
  "Experience distress when separated from attachment figure.
   Returns distress level (0.0 to 1.0)."
  (let* ((trust (gethash agent (social-atoms-trust-bonds sa) 0.1))
         (style-factor (case (social-atoms-attachment-style sa)
                         (:secure 0.3)
                         (:anxious 0.9)
                         (:avoidant 0.05)))
         (normalized-duration (/ (min duration 3600.0) 3600.0))
         (distress (* trust style-factor normalized-duration)))
    (incf (social-atoms-separation-timer sa) duration)
    (push (list :separation-distress agent duration distress (get-universal-time))
          (social-atoms-history sa))
    distress))

;;; ---------------------------------------------------------------------------
;;; Shared Intentionality
;;; ---------------------------------------------------------------------------

(defun shared-attention (sa partner focus-object)
  "Establish shared attentional focus.
   Returns coordination success (0.0 to 1.0)."
  (let* ((trust (gethash partner (social-atoms-trust-bonds sa) 0.2))
         (success (* trust 0.9)))
    (setf (social-atoms-shared-attention-focus sa) (list partner focus-object))
    (push (list :shared-attention partner focus-object success (get-universal-time))
          (social-atoms-history sa))
    success))

(defun joint-goal (sa partner goal)
  "Establish joint goal with partner."
  (let ((trust (gethash partner (social-atoms-trust-bonds sa) 0.2)))
    (push (list :joint-goal partner goal trust (get-universal-time))
          (social-atoms-history sa))
    (* trust 0.8)))

;;; ---------------------------------------------------------------------------
;;; Social Reward and Bonding
;;; ---------------------------------------------------------------------------

(defun social-reward (sa source quality)
  "Experience social reward from positive interaction.
   Updates trust bond and returns reward magnitude."
  (let* ((current-trust (gethash source (social-atoms-trust-bonds sa) 0.1))
         (increment (* quality 0.05 (case (social-atoms-attachment-style sa)
                                      (:secure 1.0)
                                      (:anxious 1.2)
                                      (:avoidant 0.3))))
         (new-trust (min 1.0 (+ current-trust increment))))
    (setf (gethash source (social-atoms-trust-bonds sa)) new-trust)
    (incf (social-atoms-social-reward-accumulator sa) increment)
    (push (list :social-reward source quality increment (get-universal-time))
          (social-atoms-history sa))
    increment))

(defun trust-bond (sa agent)
  "Get current trust bond with agent (0.0 to 1.0)."
  (gethash agent (social-atoms-trust-bonds sa) 0.1))

(defun get-all-trust-bonds (sa)
  "Return all trust bonds as alist."
  (let ((bonds nil))
    (maphash (lambda (k v) (push (cons k v) bonds))
             (social-atoms-trust-bonds sa))
    bonds))

;;; ---------------------------------------------------------------------------
;;; Situation Evaluation
;;; ---------------------------------------------------------------------------

(defun evaluate-social-situation (sa context)
  "Evaluate a social situation and return recommended action."
  (let* ((trust (gethash (getf context :agent) (social-atoms-trust-bonds sa) 0.1))
         (distress (getf context :distress 0.0))
         (distance (getf context :distance 1.0))
         (shared-focus (getf context :shared-focus nil)))
    
    (cond
      ((and (> distress 0.5) (> trust 0.3))
       (list :action :seek-comfort :intensity (* distress trust)))
      ((> distance 2.0)
       (list :action :proximity-seeking :intensity (proximity-seeking sa nil distance)))
      ((and shared-focus (> trust 0.4))
       (list :action :engage-jointly :intensity trust))
      (t
       (list :action :observe :intensity 0.2)))))

;;; ---------------------------------------------------------------------------
;;; Tests
;;; ---------------------------------------------------------------------------
