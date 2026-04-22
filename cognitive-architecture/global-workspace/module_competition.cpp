/**
 * module_competition.cpp
 * Global Workspace Theory – Module competition for conscious access.
 * Specialized processors compete to broadcast their content to the workspace.
 * Implements the competitive selection process described by Baars (1988).
 */

#include <iostream>
#include <vector>
#include <string>
#include <queue>
#include <memory>
#include <unordered_map>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <tuple> // FIXED: Added missing tuple header

namespace revarie {
namespace gwt {

/**
 * Types of specialized modules in the cognitive architecture.
 */
enum class ModuleType {
    SENSORY,
    AFFECTIVE,
    REASONING,
    MEMORY,
    SOCIAL,
    METACOGNITIVE,
    UNKNOWN
};

/**
 * A signal from a module competing for workspace access.
 */
struct ModuleSignal {
    std::string module_id;
    ModuleType module_type;
    std::string content;           // The information to broadcast
    double salience;               // 0.0–1.0 – importance/urgency
    double confidence;             // 0.0–1.0 – certainty
    double novelty;                // 0.0–1.0 – unexpectedness
    std::chrono::steady_clock::time_point timestamp;
    std::unordered_map<std::string, std::string> metadata;

    // Default constructor
    ModuleSignal() : salience(0.0), confidence(0.0), novelty(0.0) {
        timestamp = std::chrono::steady_clock::now();
    }

    // Compute activation strength (weighted sum + recency bonus)
    double compute_activation(double w_salience = 0.4,
                              double w_confidence = 0.3,
                              double w_novelty = 0.3) const {
        auto now = std::chrono::steady_clock::now();
        auto age_ms = std::chrono::duration_cast<std::chrono::milliseconds>(now - timestamp).count();
        double age_sec = age_ms / 1000.0;
        
        // Recency bonus: up to 0.1 for signals less than 5 seconds old
        double recency_boost = std::max(0.0, 0.1 * (1.0 - std::min(age_sec / 5.0, 1.0)));
        
        double base = w_salience * salience + w_confidence * confidence + w_novelty * novelty;
        return std::min(1.0, base + recency_boost);
    }
};

/**
 * Comparator for priority queue (higher activation = higher priority).
 */
struct SignalComparator {
    bool operator()(const ModuleSignal& a, const ModuleSignal& b) const {
        // We'll compute activation on the fly; for heap we need a strict ordering.
        // This is a placeholder – actual heap uses pre‑computed activation.
        return a.salience < b.salience;
    }
};

/**
 * ModuleCompetition – manages the competitive selection of signals.
 */
class ModuleCompetition {
public:
    struct Config {
        double w_salience = 0.4;
        double w_confidence = 0.3;
        double w_novelty = 0.3;
        size_t history_size = 100;
    };

    ModuleCompetition() : config_({}) {} explicit ModuleCompetition(Config config) : config_(std::move(config)) {}

    /**
     * Submit a signal from a module for competition.
     */
    void submit_signal(const ModuleSignal& signal) {
        double activation = signal.compute_activation(
            config_.w_salience, config_.w_confidence, config_.w_novelty);
        // Store as pair (activation, signal) in a max‑heap fashion.
        // Using negative activation for max‑heap via std::priority_queue.
        pending_signals_.push({activation, next_id_++, signal});
    }

    /**
     * Select the winner – the signal with highest activation.
     * Returns true if a winner was selected, false if no signals pending.
     */
    bool select_winner(ModuleSignal& winner) {
        if (pending_signals_.empty()) {
            return false;
        }
        auto top = pending_signals_.top();
        pending_signals_.pop();
        winner = std::get<2>(top);
        
        // Record in history.
        history_.push_back(winner);
        if (history_.size() > config_.history_size) {
            history_.erase(history_.begin());
        }
        return true;
    }

    /**
     * Peek at the top N signals without removing them.
     */
    std::vector<ModuleSignal> peek_top_n(size_t n) const {
        std::vector<ModuleSignal> result;
        auto copy = pending_signals_;  // copy of priority queue
        for (size_t i = 0; i < n && !copy.empty(); ++i) {
            result.push_back(std::get<2>(copy.top()));
            copy.pop();
        }
        return result;
    }

    /**
     * Clear all pending signals.
     */
    void clear() {
        while (!pending_signals_.empty()) {
            pending_signals_.pop();
        }
    }

    /**
     * Get recent winners.
     */
    std::vector<ModuleSignal> get_recent_winners(size_t n = 5) const {
        std::vector<ModuleSignal> result;
        size_t start = (history_.size() > n) ? history_.size() - n : 0;
        for (size_t i = start; i < history_.size(); ++i) {
            result.push_back(history_[i]);
        }
        return result;
    }

    /**
     * Check if there are pending signals.
     */
    bool has_pending() const {
        return !pending_signals_.empty();
    }

    /**
     * Get the number of pending signals.
     */
    size_t pending_count() const {
        return pending_signals_.size();
    }

private:
    Config config_;
    
    // Max‑heap using negative activation for ordering (higher activation first).
    // Tuple: (activation, tie_breaker, signal)
    using QueueItem = std::tuple<double, uint64_t, ModuleSignal>;
    struct CompareQueueItem {
        bool operator()(const QueueItem& a, const QueueItem& b) const {
            // Higher activation comes first.
            if (std::get<0>(a) != std::get<0>(b)) {
                return std::get<0>(a) < std::get<0>(b);
            }
            // Tie‑breaker: lower ID (older) first.
            return std::get<1>(a) > std::get<1>(b);
        }
    };
    
    std::priority_queue<QueueItem, std::vector<QueueItem>, CompareQueueItem> pending_signals_;
    uint64_t next_id_ = 0;
    std::vector<ModuleSignal> history_;
};

} // namespace gwt
} // namespace revarie

// =============================================================================
// Simple test harness (compile with -DTEST_MODULE_COMPETITION)
// =============================================================================
#ifdef TEST_MODULE_COMPETITION
#include <cassert>
#include <thread>

int main() {
    using namespace revarie::gwt;
    
    // Test signal activation.
    ModuleSignal signal;
    signal.module_id = "affective_1";
    signal.module_type = ModuleType::AFFECTIVE;
    signal.content = "User distressed";
    signal.salience = 0.9;
    signal.confidence = 0.8;
    signal.novelty = 0.7;
    
    double activation = signal.compute_activation();
    double expected = 0.4*0.9 + 0.3*0.8 + 0.3*0.7;
    // Allow for recency boost (signal just created).
    assert(std::abs(activation - expected) <= 0.11);
    std::cout << "[PASS] signal activation\n";
    
    // Test competition.
    ModuleCompetition comp;
    ModuleSignal s1, s2;
    s1.module_id = "low";
    s1.salience = 0.3;
    s2.module_id = "high";
    s2.salience = 0.9;
    
    comp.submit_signal(s1);
    comp.submit_signal(s2);
    
    ModuleSignal winner;
    assert(comp.select_winner(winner));
    assert(winner.module_id == "high");
    std::cout << "[PASS] competition winner\n";
    
    // Test empty.
    ModuleCompetition empty_comp;
    ModuleSignal dummy;
    assert(!empty_comp.select_winner(dummy));
    std::cout << "[PASS] empty competition\n";
    
    std::cout << "All ModuleCompetition tests passed.\n";
    return 0;
}
#endif
