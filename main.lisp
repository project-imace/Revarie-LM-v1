;;; main.lisp
;;; Entry point for the REVARIE LM V1 Symbolic Wrapper

(require 'asdf)

;; 1. Register the root directory so ASDF finds revarie.asd
(push (uiop:getcwd) asdf:*central-registry*)

;; 2. Load the unified cognitive architecture system
(format t "Initializing REVARIE Symbolic Wrapper...~%")
(handler-case
    (asdf:load-system "revarie-cognitive-architecture")
  (error (e)
    (format *error-output* "Failed to load cognitive architecture: ~A~%" e)
    (uiop:quit 1)))
(format t "All cognitive lobes and psychoanalytic modules successfully loaded.~%")

;; 3. Define the boot sequence for the Symbolic Server
(defun start-symbolic-server ()
  (format t "Starting Symbolic Engine for 14-Day Study...~%")
  (format t "Awaiting logical validation requests from Orchestrator...~%")
  
  ;; This loop keeps the Lisp image alive under supervisord.
  ;; If you eventually add a local TCP server (like USOCKET) to receive 
  ;; JSON from Python/Rust, it would bind and listen inside this loop.
  (loop
     ;; Sleep to prevent CPU thrashing while waiting for input
     (sleep 60)
     ;; (Optional) Trigger garbage collection or background memory sweeps here
     ))

;; 4. Execute the boot sequence
(start-symbolic-server)
