;;; test_physical_symbols.lisp
;;; Unit tests for the Physical Symbol System.

(require :fiveam)

(defpackage :revarie-turing-tests
  (:use :common-lisp :fiveam)
  (:import-from :revarie-turing
                :create-symbol
                :ps-symbol-p
                :create-expression
                :ps-expression-p
                :designate
                :interpret))

(in-package :revarie-turing-tests)

(def-suite turing-tests
  :description "Tests for the Turing Machine foundational layer.")

(in-suite turing-tests)

(test symbol-creation
  "Test creation and properties of physical symbols."
  (let ((sym (create-symbol "X" :type :atomic :value 42)))
    (is (ps-symbol-p sym))
    (is (equal "X" (revarie-turing::ps-symbol-name sym)))
    (is (eql :atomic (revarie-turing::ps-symbol-type sym)))
    (is (= 42 (revarie-turing::ps-symbol-value sym)))))

(test expression-creation
  "Test creation of expressions from symbols."
  (let ((s1 (create-symbol "A"))
        (s2 (create-symbol "B")))
    (let ((expr (create-expression s1 s2)))
      (is (ps-expression-p expr))
      (is (= 2 (length (revarie-turing::ps-expression-elements expr)))))))

(test designation
  "Test designation (pointing) to symbols."
  (let ((sym (designate :revarie "TEST")))
    (is (ps-symbol-p sym))
    (is (equal "TEST" (revarie-turing::ps-symbol-name sym)))))

(test interpretation
  "Test interpretation of symbolic expressions."
  (let ((add-expr (create-expression
                    (create-symbol "ADD")
                    (create-symbol "A" :value 10)
                    (create-symbol "B" :value 20))))
    (is (= 30 (interpret :revarie add-expr)))))

(run! 'turing-tests)
