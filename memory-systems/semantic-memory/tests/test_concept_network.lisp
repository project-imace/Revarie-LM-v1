;;; test_concept_network.lisp
;;; Unit tests for Concept Network.

(require :fiveam)
(load "../concept_network.lisp")

(defpackage :revarie-semantic-memory-tests
  (:use :common-lisp :fiveam :revarie-semantic-memory))

(in-package :revarie-semantic-memory-tests)

(def-suite semantic-memory-tests
  :description "Tests for Semantic Memory Concept Network")
(in-suite semantic-memory-tests)

(test concept-creation
  "Test creation of concepts."
  (let ((c (revarie-semantic-memory::make-concept "dog" "Dog" :properties '(("color" . "brown")))))
    (is (string= "dog" (revarie-semantic-memory::concept-id c)))
    (is (string= "Dog" (revarie-semantic-memory::concept-label c)))
    (is (string= "brown" (gethash "color" (revarie-semantic-memory::concept-properties c))))))

(test network-construction
  "Test building a concept network."
  (let ((net (make-concept-network)))
    (add-concept net "dog" "Dog")
    (add-concept net "animal" "Animal")
    (add-relation net "isa" "dog" "animal")
    (is (= 2 (hash-table-count (revarie-semantic-memory::concepts net))))
    (is (= 1 (hash-table-count (revarie-semantic-memory::relations net))))))

(test spreading-activation
  "Test activation spread through network."
  (let ((net (make-concept-network)))
    (add-concept net "source" "Source")
    (add-concept net "target" "Target")
    (add-relation net "assoc" "source" "target" :weight 0.8)
    (set-activation net "source" 1.0)
    (spread-activation net 1)
    (let ((active (get-active-concepts net 0.1)))
      (is (>= (length active) 1)))))

(test shortest-path
  "Test finding shortest path between concepts."
  (let ((net (make-concept-network)))
    (add-concept net "A" "A")
    (add-concept net "B" "B")
    (add-concept net "C" "C")
    (add-relation net "link" "A" "B")
    (add-relation net "link" "B" "C")
    (let ((path (find-shortest-path net "A" "C")))
      (is (equal '("A" "B" "C") path)))))

(test property-query
  "Test querying concepts by property."
  (let ((net (make-concept-network)))
    (add-concept net "apple" "Apple" :properties '(("color" . "red")))
    (add-concept net "banana" "Banana" :properties '(("color" . "yellow")))
    (let ((red (query-by-property net "color" "red")))
      (is (equal '("apple") red)))))

(run! 'semantic-memory-tests)
