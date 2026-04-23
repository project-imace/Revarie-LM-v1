;;; main.lisp
;;; Entry point for the REVARIE LM V1 Symbolic Wrapper

(require 'asdf)

;; 1. Register the root directory so ASDF/Quicklisp finds the .asd file
(push (uiop:getcwd) asdf:*central-registry*)

;; 2. Load the unified cognitive architecture system using QUICKLISP
(format t "Initializing REVARIE Symbolic Wrapper...~%")
(handler-case
    (ql:quickload "revarie-cognitive-architecture")
  (error (e)
    (format *error-output* "Failed to load cognitive architecture: ~A~%" e)
    (uiop:quit 1)))
(format t "All cognitive lobes and psychoanalytic modules successfully loaded.~%")

;; 3. Define the boot sequence for the Symbolic Server
(defun start-symbolic-server ()
  (format t "Starting Symbolic Engine for 14-Day Study...~%")
  (format t "Awaiting logical validation requests from Orchestrator...~%")
  
  ;; This loop keeps the Lisp image alive under supervisord.
  (loop
     (sleep 60)
     ))

;; 4. Execute the boot sequence
(start-symbolic-server)
