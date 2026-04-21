/**
 * knowledge_graph.cpp
 * Semantic Memory – Knowledge Graph.
 * Implements a directed graph of concepts and relations representing
 * semantic knowledge. Supports spreading activation, inference, and
 * query answering based on structured semantic networks.
 *
 * Theoretical foundations:
 * - Collins & Quillian (1969): Semantic memory as hierarchical network.
 * - Anderson (1983): ACT-R spreading activation theory.
 * - Quillian (1968): Semantic memory retrieval via intersection search.
 */

#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <memory>
#include <algorithm>
#include <cmath>
#include <cassert>
#include <limits>
#include <functional>

namespace revarie {
namespace memory {

/**
 * A concept node in the knowledge graph.
 */
struct Concept {
    std::string id;
    std::string label;
    std::unordered_map<std::string, std::string> properties;
    double activation = 0.0;
    double base_activation = 0.0;

    Concept() = default;
    Concept(std::string id, std::string label) : id(std::move(id)), label(std::move(label)) {}
};

/**
 * A directed relation between two concepts.
 */
struct Relation {
    std::string id;
    std::string type;           // "isa", "has_property", "causes", etc.
    std::string source_id;
    std::string target_id;
    double weight = 1.0;        // Association strength
    bool bidirectional = false;

    Relation() = default;
    Relation(std::string type, std::string source, std::string target, double w = 1.0)
        : type(std::move(type)), source_id(std::move(source)), target_id(std::move(target)), weight(w) {}
};

/**
 * Knowledge Graph with spreading activation and query capabilities.
 */
class KnowledgeGraph {
public:
    struct Config {
        double decay_rate = 0.5;          // Activation decay per pulse
        double activation_threshold = 0.1; // Minimum activation to propagate
        int max_pulses = 10;              // Maximum spreading pulses
        double base_activation = 0.0;      // Default base activation
    };

    explicit KnowledgeGraph(Config config = Config{}) : config_(std::move(config)) {}

    // =========================================================================
    // Graph Construction
    // =========================================================================

    /**
     * Add a concept node to the graph.
     */
    void add_concept(const std::string& id, const std::string& label) {
        concepts_[id] = Concept(id, label);
        concepts_[id].base_activation = config_.base_activation;
    }

    /**
     * Add a concept with properties.
     */
    void add_concept(const std::string& id, const std::string& label,
                     std::unordered_map<std::string, std::string> props) {
        concepts_[id] = Concept(id, label);
        concepts_[id].properties = std::move(props);
        concepts_[id].base_activation = config_.base_activation;
    }

    /**
     * Add a directed relation between concepts.
     */
    void add_relation(const std::string& type, const std::string& source,
                      const std::string& target, double weight = 1.0,
                      bool bidirectional = false) {
        if (!concepts_.count(source) || !concepts_.count(target)) {
            return; // Missing concept
        }
        std::string rel_id = source + "_" + type + "_" + target;
        Relation rel(type, source, target, weight);
        rel.id = rel_id;
        rel.bidirectional = bidirectional;
        relations_[rel_id] = rel;

        outgoing_[source].push_back(rel_id);
        incoming_[target].push_back(rel_id);

        if (bidirectional) {
            std::string rev_id = target + "_" + type + "_" + source;
            Relation rev_rel(type, target, source, weight);
            rev_rel.id = rev_id;
            rev_rel.bidirectional = true;
            relations_[rev_id] = rev_rel;
            outgoing_[target].push_back(rev_id);
            incoming_[source].push_back(rev_id);
        }
    }

    // =========================================================================
    // Spreading Activation
    // =========================================================================

    /**
     * Set activation on source nodes (e.g., from current context).
     */
    void set_activation(const std::string& concept_id, double value) {
        if (concepts_.count(concept_id)) {
            concepts_[concept_id].activation = std::max(0.0, value);
        }
    }

    /**
     * Perform one pulse of spreading activation.
     */
    void spread_activation_pulse() {
        std::unordered_map<std::string, double> new_activation;

        for (auto& [id, concept] : concepts_) {
            if (concept.activation < config_.activation_threshold) {
                continue;
            }

            // Spread to outgoing neighbors
            for (const auto& rel_id : outgoing_[id]) {
                const auto& rel = relations_[rel_id];
                double spread = concept.activation * rel.weight * (1.0 - config_.decay_rate);
                new_activation[rel.target_id] += spread;
            }

            // Spread to incoming neighbors (backward association)
            for (const auto& rel_id : incoming_[id]) {
                const auto& rel = relations_[rel_id];
                double spread = concept.activation * rel.weight * (1.0 - config_.decay_rate) * 0.5;
                new_activation[rel.source_id] += spread;
            }
        }

        // Apply new activations (additive with decay on previous)
        for (auto& [id, concept] : concepts_) {
            concept.activation = concept.activation * config_.decay_rate;
            if (new_activation.count(id)) {
                concept.activation += new_activation[id];
            }
            concept.activation = std::min(1.0, concept.activation);
        }
    }

    /**
     * Run full spreading activation for multiple pulses.
     */
    void spread_activation(int pulses = -1) {
        int max_pulses = (pulses > 0) ? pulses : config_.max_pulses;
        for (int i = 0; i < max_pulses; ++i) {
            spread_activation_pulse();
        }
    }

    /**
     * Reset all activations to base level.
     */
    void reset_activations() {
        for (auto& [id, concept] : concepts_) {
            concept.activation = concept.base_activation;
        }
    }

    // =========================================================================
    // Query and Retrieval
    // =========================================================================

    /**
     * Get currently activated concepts above threshold.
     */
    std::vector<std::pair<std::string, double>> get_active_concepts(double threshold = 0.0) const {
        std::vector<std::pair<std::string, double>> active;
        for (const auto& [id, concept] : concepts_) {
            if (concept.activation >= threshold) {
                active.emplace_back(id, concept.activation);
            }
        }
        std::sort(active.begin(), active.end(),
                  [](const auto& a, const auto& b) { return a.second > b.second; });
        return active;
    }

    /**
     * Find the shortest path between two concepts using BFS.
     */
    std::vector<std::string> shortest_path(const std::string& source,
                                           const std::string& target) const {
        if (!concepts_.count(source) || !concepts_.count(target)) {
            return {};
        }

        std::unordered_map<std::string, std::string> parent;
        std::unordered_set<std::string> visited;
        std::queue<std::string> q;

        q.push(source);
        visited.insert(source);

        while (!q.empty()) {
            std::string current = q.front();
            q.pop();

            if (current == target) {
                // Reconstruct path
                std::vector<std::string> path;
                std::string node = target;
                while (node != source) {
                    path.push_back(node);
                    node = parent[node];
                }
                path.push_back(source);
                std::reverse(path.begin(), path.end());
                return path;
            }

            for (const auto& rel_id : outgoing_.at(current)) {
                const auto& rel = relations_.at(rel_id);
                if (!visited.count(rel.target_id)) {
                    visited.insert(rel.target_id);
                    parent[rel.target_id] = current;
                    q.push(rel.target_id);
                }
            }
        }
        return {};
    }

    /**
     * Query concepts by property.
     */
    std::vector<std::string> find_by_property(const std::string& key,
                                              const std::string& value) const {
        std::vector<std::string> results;
        for (const auto& [id, concept] : concepts_) {
            auto it = concept.properties.find(key);
            if (it != concept.properties.end() && it->second == value) {
                results.push_back(id);
            }
        }
        return results;
    }

    /**
     * Get all relations of a specific type from a concept.
     */
    std::vector<std::string> get_relations_by_type(const std::string& source_id,
                                                   const std::string& rel_type) const {
        std::vector<std::string> targets;
        if (outgoing_.count(source_id)) {
            for (const auto& rel_id : outgoing_.at(source_id)) {
                const auto& rel = relations_.at(rel_id);
                if (rel.type == rel_type) {
                    targets.push_back(rel.target_id);
                }
            }
        }
        return targets;
    }

    // =========================================================================
    // Accessors
    // =========================================================================

    const Concept* get_concept(const std::string& id) const {
        auto it = concepts_.find(id);
        return it != concepts_.end() ? &it->second : nullptr;
    }

    size_t concept_count() const { return concepts_.size(); }
    size_t relation_count() const { return relations_.size(); }

private:
    Config config_;
    std::unordered_map<std::string, Concept> concepts_;
    std::unordered_map<std::string, Relation> relations_;
    std::unordered_map<std::string, std::vector<std::string>> outgoing_;
    std::unordered_map<std::string, std::vector<std::string>> incoming_;
};

} // namespace memory
} // namespace revarie

// =============================================================================
// Unit tests (compile with g++ -std=c++17)
// =============================================================================
#ifdef TEST_KNOWLEDGE_GRAPH

int main() {
    using namespace revarie::memory;

    // Test 1: Concept and relation creation
    {
        KnowledgeGraph kg;
        kg.add_concept("dog", "Dog");
        kg.add_concept("animal", "Animal");
        kg.add_concept("mammal", "Mammal");
        kg.add_relation("isa", "dog", "mammal", 1.0);
        kg.add_relation("isa", "mammal", "animal", 1.0);

        assert(kg.concept_count() == 3);
        assert(kg.relation_count() == 2);
        std::cout << "[PASS] Concept and relation creation\n";
    }

    // Test 2: Shortest path
    {
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
        std::cout << "[PASS] Shortest path\n";
    }

    // Test 3: Spreading activation
    {
        KnowledgeGraph kg;
        kg.add_concept("source", "Source");
        kg.add_concept("target1", "Target1");
        kg.add_concept("target2", "Target2");
        kg.add_relation("assoc", "source", "target1", 0.8);
        kg.add_relation("assoc", "source", "target2", 0.5);

        kg.set_activation("source", 1.0);
        kg.spread_activation(1);

        auto active = kg.get_active_concepts(0.1);
        assert(active.size() >= 2); // source + target1 at least

        // Find target1 activation
        double t1_act = 0.0;
        for (const auto& [id, act] : active) {
            if (id == "target1") t1_act = act;
        }
        assert(t1_act > 0.0);
        std::cout << "[PASS] Spreading activation\n";
    }

    // Test 4: Property query
    {
        KnowledgeGraph kg;
        kg.add_concept("apple", "Apple", {{"color", "red"}, {"taste", "sweet"}});
        kg.add_concept("banana", "Banana", {{"color", "yellow"}, {"taste", "sweet"}});

        auto red_fruits = kg.find_by_property("color", "red");
        assert(red_fruits.size() == 1);
        assert(red_fruits[0] == "apple");

        auto sweet_fruits = kg.find_by_property("taste", "sweet");
        assert(sweet_fruits.size() == 2);
        std::cout << "[PASS] Property query\n";
    }

    // Test 5: Bidirectional relation
    {
        KnowledgeGraph kg;
        kg.add_concept("A", "A");
        kg.add_concept("B", "B");
        kg.add_relation("friend", "A", "B", 1.0, true);

        auto a_to_b = kg.shortest_path("A", "B");
        assert(a_to_b.size() == 2);
        auto b_to_a = kg.shortest_path("B", "A");
        assert(b_to_a.size() == 2);
        std::cout << "[PASS] Bidirectional relation\n";
    }

    std::cout << "All Knowledge Graph tests passed.\n";
    return 0;
}
#endif
