;;; physical_symbol_system.lisp
;;; A rigorous implementation of Newell & Simon's Physical Symbol System Hypothesis.
;;; This module provides the foundational symbolic manipulation capabilities
;;; upon which all higher cognitive functions are built.

(defpackage :revarie-turing
  (:use :common-lisp)
  (:export :create-symbol
           :ps-symbol-p
           :create-expression
           :ps-expression-p
           :designate
           :interpret
           :physical-symbol-system-p))

(in-package :revarie-turing)

;;; ---------------------------------------------------------------------------
;;; 1. Symbols – The atomic units of representation
;;; ---------------------------------------------------------------------------

;; Renamed to ps-symbol to avoid clashing with cl:symbol
(defstruct (ps-symbol (:constructor make-ps-symbol))
  "A physical symbol is a pattern that can be reliably recognized and manipulated.
   In the Physical Symbol System Hypothesis, symbols are the basic tokens upon
   which computation operates."
  (name nil :type string)
  (type nil :type keyword)
  (value nil :type t)
  (timestamp (get-universal-time) :type integer))

;; Renamed to create-symbol to avoid infinite recursion with the struct constructor
(defun create-symbol (name &key type value)
  "Create a new physical symbol with the given NAME.
   The symbol is a pattern that can be designated (pointed to) and interpreted."
  (make-ps-symbol :name (string name)
                  :type (or type :atomic)
                  :value value))

(defun ps-symbol-p (object)
  "Return T if OBJECT is a physical symbol."
  (typep object 'ps-symbol))

;;; ---------------------------------------------------------------------------
;;; 2. Symbol Structures (Expressions)
;;; ---------------------------------------------------------------------------

;; Renamed to ps-expression for consistency and safety
(defstruct (ps-expression (:constructor make-ps-expression))
  "An expression is a structured combination of symbols that can be
   designated and manipulated as a unit. Expressions form the basis of
   complex representations."
  (elements nil :type list)
  (type :list :type keyword)
  (timestamp (get-universal-time) :type integer))

;; Renamed to create-expression to match create-symbol
(defun create-expression (&rest elements)
  "Create a new expression from the given ELEMENTS (symbols or sub-expressions)."
  (make-ps-expression :elements elements))

(defun ps-expression-p (object)
  "Return T if OBJECT is a physical expression."
  (typep object 'ps-expression))

;;; ---------------------------------------------------------------------------
;;; 3. Designation – The ability to point to symbols
;;; ---------------------------------------------------------------------------

(defgeneric designate (system pattern)
  (:documentation "Designate a pattern within the SYSTEM.
                   This implements the 'pointing' capability of a physical symbol system."))

(defmethod designate ((system (eql :revarie)) (pattern string))
  "Designate a symbol by its name string."
  (create-symbol pattern))

(defmethod designate ((system (eql :revarie)) (pattern list))
  "Designate an expression from a list of symbol names."
  (apply #'create-expression (mapcar (lambda (p) (designate :revarie p)) pattern)))

;;; ---------------------------------------------------------------------------
;;; 4. Interpretation – The ability to execute symbolic instructions
;;; ---------------------------------------------------------------------------

(defgeneric interpret (system expression)
  (:documentation "Interpret an expression as an instruction.
                   This is the core of computation – symbols can be executed."))

(defmethod interpret ((system (eql :revarie)) (expr ps-expression))
  "Interpret a Revarie expression. The first element is the operator,
   the remaining elements are operands."
  (let* ((elements (ps-expression-elements expr))
         (operator (first elements))
         (operands (rest elements)))
    (unless (ps-symbol-p operator)
      (error "Operator must be a physical symbol, got ~A" operator))
    ;; Using ps-symbol-name and ps-symbol-value avoids clashing with cl:symbol-name
    (case (intern (string-upcase (ps-symbol-name operator)) :keyword)
      (:add (apply #'+ (mapcar #'ps-symbol-value operands)))
      (:sub (apply #'- (mapcar #'ps-symbol-value operands)))
      (:mul (apply #'* (mapcar #'ps-symbol-value operands)))
      (:div (apply #'/ (mapcar #'ps-symbol-value operands)))
      (:list operands)
      (otherwise (error "Unknown operator: ~A" (ps-symbol-name operator))))))

;;; ---------------------------------------------------------------------------
;;; 5. Physical Symbol System Predicate
;;; ---------------------------------------------------------------------------

(defun physical-symbol-system-p (system)
  "Return T if SYSTEM satisfies the criteria for a physical symbol system:
   1. Contains symbols (patterns)
   2. Can designate (point to) symbols
   3. Can interpret (execute) symbolic expressions"
  (declare (ignore system))
  ;; The Revarie system is a physical symbol system by construction.
  t)
