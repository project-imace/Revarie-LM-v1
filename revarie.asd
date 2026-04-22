;;; revarie.asd
;;; ASDF system definition for REVARIE Cognitive Architecture (Common Lisp modules)
;;; Updated for Root-Level Polyglot Orchestration

(defsystem "revarie-cognitive-architecture"
  :description "Unified Symbolic Engine for REVARIE LM v1.0"
  :version "1.0.0"
  :author "Project IMACE <research@imace.online>"
  :license "Apache-2.0"
  :depends-on ("alexandria" "serapeum" "cl-ppcre" "fiveam")
  :components (
               ;; Turing Machine (Already at root level)
               (:module "turing-machine"
                :pathname "turing-machine"
                :components ((:file "symbol-system/physical_symbol_system")))
               
               ;; Cognitive Architecture (Shifted down)
               (:module "dual-process"
                :pathname "cognitive-architecture/dual-process"
                :components ((:file "system_two/counterfactual_simulator")))
               (:module "global-workspace"
                :pathname "cognitive-architecture/global-workspace"
                :components ((:file "attention_controller")))
               (:module "active-inference"
                :pathname "cognitive-architecture/active-inference"
                :components ((:file "markov_blanket")))
               (:module "belief-space"
                :pathname "cognitive-architecture/belief-space"
                :components ((:file "belief_atoms")))
               (:module "rebound-mechanism"
                :pathname "cognitive-architecture/rebound-mechanism"
                :components ((:file "saddle_point_seeker")))
               (:module "pomdp-engine"
                :pathname "cognitive-architecture/pomdp-engine"
                :components ((:file "value_iteration")))

               ;; Memory Systems
               (:module "semantic-memory"
                :pathname "memory-systems/semantic-memory"
                :components ((:file "concept_network")))

               ;; Theory of Mind
               (:module "theory-of-mind"
                :pathname "theory-of-mind"
                :components ((:file "recursive_belief_hierarchy")))

               ;; Psychoanalytic Modules
               (:module "id-module"
                :pathname "psychoanalytic-modules/id-module"
                :components ((:file "primary_process")))
               (:module "ego-module"
                :pathname "psychoanalytic-modules/ego-module"
                :components ((:file "defense_mechanisms")))
               (:module "superego-module"
                :pathname "psychoanalytic-modules/superego-module"
                :components ((:file "ideal_self")))
               (:module "jungian-functions"
                :pathname "psychoanalytic-modules/jungian-functions"
                :components ((:file "intuiting_function")))

               ;; Persona Engine
               (:module "social-interaction"
                :pathname "persona-engine/social-interaction"
                :components ((:file "social_atoms")))
               (:module "narrative-self"
                :pathname "persona-engine/narrative-self"
                :components ((:file "self_model")))

               ;; RAG Pipeline
               (:module "context-assembler"
                :pathname "rag-pipeline/context-assembler"
                :components ((:file "memory_fusion")))
              )
  :in-order-to ((test-op (test-op "revarie-cognitive-architecture/tests"))))

(defsystem "revarie-cognitive-architecture/tests"
  :description "Test suite for REVARIE Cognitive Architecture (Lisp)"
  :depends-on ("revarie-cognitive-architecture" "fiveam")
  :components (
               ;; Cognitive Core Tests
               (:module "turing-machine"
                :pathname "turing-machine"
                :components ((:file "symbol-system/tests/test_physical_symbols")))
               (:module "dual-process"
                :pathname "cognitive-architecture/dual-process"
                :components ((:file "system_two/tests/test_counterfactual")))
               (:module "global-workspace"
                :pathname "cognitive-architecture/global-workspace"
                :components ((:file "tests/test_attention_controller")))
               (:module "active-inference"
                :pathname "cognitive-architecture/active-inference"
                :components ((:file "tests/test_markov_blanket")))
               (:module "belief-space"
                :pathname "cognitive-architecture/belief-space"
                :components ((:file "tests/test_belief_atoms")))
               (:module "rebound-mechanism"
                :pathname "cognitive-architecture/rebound-mechanism"
                :components ((:file "tests/test_saddle_point")))
               (:module "pomdp-engine"
                :pathname "cognitive-architecture/pomdp-engine"
                :components ((:file "tests/test_value_iteration")))
                
               ;; Psychoanalytic & Persona Tests
               (:module "id-module-tests"
                :pathname "psychoanalytic-modules/id-module"
                :components ((:file "tests/test_primary_process")))
               (:module "ego-module-tests"
                :pathname "psychoanalytic-modules/ego-module"
                :components ((:file "tests/test_defense_mechanisms")))
               (:module "superego-module-tests"
                :pathname "psychoanalytic-modules/superego-module"
                :components ((:file "tests/test_ideal_self")))
               (:module "jungian-functions-tests"
                :pathname "psychoanalytic-modules/jungian-functions"
                :components ((:file "tests/test_intuiting")))
               (:module "social-interaction-tests"
                :pathname "persona-engine/social-interaction"
                :components ((:file "tests/test_social_atoms")))
               (:module "narrative-self-tests"
                :pathname "persona-engine/narrative-self"
                :components ((:file "tests/test_self_model")))
               
               ;; External Modality Tests
               (:module "theory-of-mind-tests"
                :pathname "theory-of-mind"
                :components ((:file "tests/test_recursive_belief")))
               (:module "semantic-memory-tests"
                :pathname "memory-systems/semantic-memory"
                :components ((:file "tests/test_concept_network")))
               (:module "context-assembler-tests"
                :pathname "rag-pipeline/context-assembler"
                :components ((:file "tests/test_memory_fusion")))
              )
  :perform (test-op (op c)
    (uiop:symbol-call :fiveam :run! (uiop:find-symbol* '#:system-two-tests :revarie-system-two-tests))
    (uiop:symbol-call :fiveam :run! (uiop:find-symbol* '#:gwt-attention-tests :revarie-gwt-tests))
    (uiop:symbol-call :fiveam :run! (uiop:find-symbol* '#:active-inference-tests :revarie-active-inference-tests))
    (uiop:symbol-call :fiveam :run! (uiop:find-symbol* '#:belief-atoms-tests :revarie-belief-space-tests))
    (uiop:symbol-call :fiveam :run! (uiop:find-symbol* '#:rebound-tests :revarie-rebound-tests))
    (uiop:symbol-call :fiveam :run! (uiop:find-symbol* '#:pomdp-tests :revarie-pomdp-tests))))
