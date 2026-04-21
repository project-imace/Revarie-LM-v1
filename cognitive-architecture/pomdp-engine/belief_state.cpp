/**
 * belief_state.cpp
 * POMDP Engine – Belief State Representation.
 * Implements a probability distribution over hidden states in a Partially
 * Observable Markov Decision Process. Provides Bayesian belief updates
 * and utilities for state estimation under uncertainty.
 *
 * Theoretical foundations:
 * - Kaelbling, Littman, & Cassandra (1998): Planning and acting in partially observable stochastic domains.
 * - Åström (1965): Optimal control of Markov processes with incomplete state information.
 */

#include <vector>
#include <unordered_map>
#include <string>
#include <stdexcept>
#include <numeric>
#include <cmath>
#include <random>
#include <algorithm>
#include <cassert>

namespace revarie {
namespace pomdp {

/**
 * Belief state: a probability distribution over hidden states.
 * States are identified by integer indices 0..n-1 for efficiency.
 */
class BeliefState {
public:
    /**
     * Construct a belief state of given dimension.
     * @param n_states Number of possible hidden states.
     * @param uniform If true, initialize as uniform distribution; otherwise zero.
     */
    explicit BeliefState(size_t n_states, bool uniform = true) 
        : probs_(n_states, 0.0) {
        if (uniform && n_states > 0) {
            double p = 1.0 / static_cast<double>(n_states);
            std::fill(probs_.begin(), probs_.end(), p);
        }
    }

    /**
     * Construct a belief state from explicit probability vector.
     * Automatically normalizes the input.
     */
    explicit BeliefState(const std::vector<double>& probabilities) {
        double sum = std::accumulate(probabilities.begin(), probabilities.end(), 0.0);
        if (sum <= 0.0) {
            throw std::invalid_argument("Probabilities must sum to a positive value");
        }
        probs_.reserve(probabilities.size());
        for (double p : probabilities) {
            probs_.push_back(p / sum);
        }
    }

    // Accessors
    size_t size() const { return probs_.size(); }
    double operator[](size_t i) const { return probs_[i]; }
    double& operator[](size_t i) { return probs_[i]; }
    const std::vector<double>& probabilities() const { return probs_; }

    /**
     * Bayesian belief update given an observation.
     * b'(s') = η * P(o | s') * Σ_s P(s' | s, a) * b(s)
     * * @param observation Observation index (0..n_obs-1).
     * @param action Action index (0..n_act-1).
     * @param observation_model P(o | s) matrix: [state][obs] -> probability.
     * @param transition_model P(s' | s, a) tensor: [action][from_state][to_state] -> probability.
     * @return New belief state after update.
     */
    BeliefState update(
        size_t observation,
        size_t action,
        const std::vector<std::vector<double>>& observation_model,
        const std::vector<std::vector<std::vector<double>>>& transition_model) const {

        const size_t n = size();
        std::vector<double> new_probs(n, 0.0);
        double total = 0.0;

        for (size_t s_prime = 0; s_prime < n; ++s_prime) {
            // P(o | s')
            double obs_prob = observation_model[s_prime][observation];
            
            // Σ_s P(s' | s, a) * b(s)
            double trans_prob = 0.0;
            for (size_t s = 0; s < n; ++s) {
                trans_prob += transition_model[action][s][s_prime] * probs_[s];
            }
            
            new_probs[s_prime] = obs_prob * trans_prob;
            total += new_probs[s_prime];
        }

        // Normalize
        if (total > 0.0) {
            for (double& p : new_probs) {
                p /= total;
            }
        } else {
            // Fallback to uniform if total is zero (numerical issue)
            double uniform = 1.0 / static_cast<double>(n);
            std::fill(new_probs.begin(), new_probs.end(), uniform);
        }

        return BeliefState(new_probs);
    }

    /**
     * Predict belief state after taking an action (before observation).
     * b'(s') = Σ_s P(s' | s, a) * b(s)
     */
    BeliefState predict(
        size_t action,
        const std::vector<std::vector<std::vector<double>>>& transition_model) const {

        const size_t n = size();
        std::vector<double> new_probs(n, 0.0);

        for (size_t s_prime = 0; s_prime < n; ++s_prime) {
            for (size_t s = 0; s < n; ++s) {
                new_probs[s_prime] += transition_model[action][s][s_prime] * probs_[s];
            }
        }
        return BeliefState(new_probs);
    }

    /**
     * Sample a state from the belief distribution.
     */
    size_t sample(std::mt19937& rng) const {
        std::uniform_real_distribution<double> dist(0.0, 1.0);
        double r = dist(rng);
        double cumulative = 0.0;
        for (size_t i = 0; i < probs_.size(); ++i) {
            cumulative += probs_[i];
            if (r <= cumulative) {
                return i;
            }
        }
        return probs_.size() - 1;
    }

    /**
     * Compute entropy of the belief state.
     * H(b) = -Σ b(s) log b(s)
     */
    double entropy() const {
        double h = 0.0;
        for (double p : probs_) {
            if (p > 1e-12) {
                h -= p * std::log(p);
            }
        }
        return h;
    }

    /**
     * Return the most likely state (MAP estimate).
     */
    size_t map_state() const {
        return std::distance(probs_.begin(),
            std::max_element(probs_.begin(), probs_.end()));
    }

    /**
     * Check if belief is deterministic (one state has probability 1).
     */
    bool is_deterministic(double epsilon = 1e-9) const {
        for (double p : probs_) {
            if (p > epsilon && p < 1.0 - epsilon) {
                return false;
            }
        }
        return true;
    }

private:
    std::vector<double> probs_;
};

/**
 * Maintains a history of belief states for temporal reasoning.
 */
class BeliefHistory {
public:
    void push(const BeliefState& b) { history_.push_back(b); }
    const BeliefState& current() const { return history_.back(); }
    const BeliefState& operator[](size_t i) const { return history_[i]; }
    size_t size() const { return history_.size(); }
    void clear() { history_.clear(); }

private:
    std::vector<BeliefState> history_;
};

} // namespace pomdp
} // namespace revarie

// =============================================================================
// Unit tests (compile with -DTEST_BELIEF_STATE)
// =============================================================================
#ifdef TEST_BELIEF_STATE
#include <iostream>

int main() {
    using namespace revarie::pomdp;

    // Test 1: Uniform initialization
    {
        BeliefState b(4);
        assert(b.size() == 4);
        for (size_t i = 0; i < 4; ++i) {
            assert(std::abs(b[i] - 0.25) < 1e-9);
        }
        std::cout << "[PASS] Uniform initialization\n";
    }

    // Test 2: Custom initialization with normalization
    {
        BeliefState b(std::vector<double>{2.0, 3.0, 5.0});
        assert(b.size() == 3);
        assert(std::abs(b[0] - 0.2) < 1e-9);
        assert(std::abs(b[1] - 0.3) < 1e-9);
        assert(std::abs(b[2] - 0.5) < 1e-9);
        std::cout << "[PASS] Custom initialization\n";
    }

    // Test 3: Belief update (simple identity transitions)
    {
        BeliefState b(2);  // uniform [0.5, 0.5]
        std::vector<std::vector<double>> obs_model = {
            {0.9, 0.1},  // state 0: P(o0)=0.9, P(o1)=0.1
            {0.1, 0.9}   // state 1: P(o0)=0.1, P(o1)=0.9
        };
        std::vector<std::vector<std::vector<double>>> trans_model = {
            // action 0: identity
            { {1.0, 0.0}, {0.0, 1.0} }
        };

        BeliefState b2 = b.update(0, 0, obs_model, trans_model);
        // After observing o0, state 0 should be more probable
        assert(b2[0] > b2[1]);
        std::cout << "[PASS] Belief update\n";
    }

    // Test 4: Entropy
    {
        BeliefState b(std::vector<double>{1.0, 0.0});
        assert(b.entropy() < 1e-9);
        
        BeliefState b2(2, true);
        double h_uniform = b2.entropy();
        assert(std::abs(h_uniform - std::log(2.0)) < 1e-9);
        std::cout << "[PASS] Entropy calculation\n";
    }

    // Test 5: MAP state
    {
        BeliefState b(std::vector<double>{0.1, 0.7, 0.2});
        assert(b.map_state() == 1);
        std::cout << "[PASS] MAP state\n";
    }

    // Test 6: Predict step
    {
        BeliefState b(std::vector<double>{1.0, 0.0});  // certain in state 0
        std::vector<std::vector<std::vector<double>>> trans = {
            // action 0: stochastic transition
            { {0.8, 0.2}, {0.3, 0.7} }
        };
        BeliefState predicted = b.predict(0, trans);
        assert(std::abs(predicted[0] - 0.8) < 1e-9);
        assert(std::abs(predicted[1] - 0.2) < 1e-9);
        std::cout << "[PASS] Predict step\n";
    }

    std::cout << "All Belief State tests passed.\n";
    return 0;
}
#endif
