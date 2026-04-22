(require 'asdf)
(asdf:load-asd (merge-pathnames "revarie.asd" (uiop:getcwd)))
(asdf:load-system "revarie-cognitive-architecture")
;; Initialize your symbolic server here
