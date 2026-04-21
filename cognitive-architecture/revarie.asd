;;; revarie.asd
;;; ASDF system definition for REVARIE Cognitive Architecture (Common Lisp modules)

(defsystem "revarie-cognitive-architecture"
  :description "Cognitive Architecture core for REVARIE LM v1.0 (Lisp modules)"
  :version "1.0.0"
  :author "Project IMACE <research@imace.online>"
  :license "Apache-2.0"
  :depends-on ("alexandria"
               "serapeum"
               "cl-ppcre"
               "fiveam")
  :components ((:module "turing-machine"
                :components ((:file "symbol-system/physical_symbol_system")))
               (:module "dual-process"
                :components ((:file "system_two/counterfactual_simulator")))
               (:module "global-workspace"
                :components ((:file "attention_controller")))
               (:module "active-inference"
                :components ((:file "markov_blanket")))
               (:module "belief-space"
                :components ((:file "belief_atoms")))
               (:module "rebound-mechanism"
                :components ((:file "saddle_point_seeker")))
               (:module "pomdp-engine"
                :components ((:file "value_iteration"))))
  :in-order-to ((test-op (test-op "revarie-cognitive-architecture/tests"))))

(defsystem "revarie-cognitive-architecture/tests"
  :description "Test suite for REVARIE Cognitive Architecture (Lisp)"
  :depends-on ("revarie-cognitive-architecture" "fiveam")
  :components ((:module "turing-machine"
                :components ((:file "symbol-system/tests/test_physical_symbols")))
               (:module "dual-process"
                :components ((:file "system_two/tests/test_counterfactual")))
               (:module "global-workspace"
                :components ((:file "tests/test_attention_controller")))
               (:module "active-inference"
                :components ((:file "tests/test_markov_blanket")))
               (:module "belief-space"
                :components ((:file "tests/test_belief_atoms")))
               (:module "rebound-mechanism"
                :components ((:file "tests/test_saddle_point")))
               (:module "pomdp-engine"
                :components ((:file "tests/test_value_iteration"))))
  :perform (test-op (op c) (uiop:symbol-call :fiveam :run! :revarie-cognitive-architecture)))
