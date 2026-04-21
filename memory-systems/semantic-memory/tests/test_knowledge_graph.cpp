/**
 * test_knowledge_graph.cpp
 * Unit tests for Knowledge Graph.
 * Compile with: g++ -std=c++17 -o test_kg test_knowledge_graph.cpp
 */

#include "../knowledge_graph.cpp"
#include <cassert>
#include <iostream>

using namespace revarie::memory;

void test_concept_creation() {
    KnowledgeGraph kg;
    kg.add_concept("dog", "Dog");
    kg.add_concept("animal", "Animal");
    assert(kg.concept_count() == 2);
    const Concept* c = kg.get_concept("dog");
    assert(c != nullptr);
    assert(c->label == "Dog");
    std::cout << "[PASS] test_concept_creation\n";
}

void test_relation_creation() {
    KnowledgeGraph kg;
    kg.add_concept("dog", "Dog");
    kg.add_concept("animal", "Animal");
    kg.add_relation("isa", "dog", "animal", 1.0);
    assert(kg.relation_count() == 1);
    std::cout << "[PASS] test_relation_creation\n";
}

void test_shortest_path() {
    KnowledgeGraph kg;
    kg.add_concept("A", "A");
    kg.add_concept("B", "B");
    kg.add_concept("C", "C");
    kg.add_concept("D", "D");
    kg.add_relation("link", "A", "B");
    kg.add_relation("link", "B", "C");
    kg.add_relation("link", "C", "D");
    auto path = kg.shortest_path("A", "D");
    assert(path.size() == 4);
    assert(path[0] == "A");
    assert(path[3] == "D");
    std::cout << "[PASS] test_shortest_path\n";
}

void test_spreading_activation() {
    KnowledgeGraph kg;
    kg.add_concept("source", "Source");
    kg.add_concept("target1", "Target1");
    kg.add_concept("target2", "Target2");
    kg.add_relation("assoc", "source", "target1", 0.8);
    kg.add_relation("assoc", "source", "target2", 0.5);
    kg.set_activation("source", 1.0);
    kg.spread_activation(1);
    auto active = kg.get_active_concepts(0.1);
    bool found_target1 = false;
    for (const auto& [id, act] : active) {
        if (id == "target1") found_target1 = true;
    }
    assert(found_target1);
    std::cout << "[PASS] test_spreading_activation\n";
}

void test_property_query() {
    KnowledgeGraph kg;
    kg.add_concept("apple", "Apple", {{"color", "red"}, {"taste", "sweet"}});
    kg.add_concept("banana", "Banana", {{"color", "yellow"}, {"taste", "sweet"}});
    auto red = kg.find_by_property("color", "red");
    assert(red.size() == 1);
    assert(red[0] == "apple");
    std::cout << "[PASS] test_property_query\n";
}

void test_bidirectional_relation() {
    KnowledgeGraph kg;
    kg.add_concept("A", "A");
    kg.add_concept("B", "B");
    kg.add_relation("friend", "A", "B", 1.0, true);
    auto path_ab = kg.shortest_path("A", "B");
    assert(path_ab.size() == 2);
    auto path_ba = kg.shortest_path("B", "A");
    assert(path_ba.size() == 2);
    std::cout << "[PASS] test_bidirectional_relation\n";
}

int main() {
    test_concept_creation();
    test_relation_creation();
    test_shortest_path();
    test_spreading_activation();
    test_property_query();
    test_bidirectional_relation();
    std::cout << "All Knowledge Graph tests passed.\n";
    return 0;
}
