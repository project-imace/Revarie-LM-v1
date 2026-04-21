/**
 * predictive_coder.cpp
 * Active Inference – Hierarchical Predictive Coding.
 * Implements gradient descent on prediction errors to infer hidden causes.
 * Based on Friston's Free Energy Principle and Rao & Ballard (1999).
 */

#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <random>
#include <cassert>

namespace revarie {
namespace active_inference {

/**
 * A single level in the predictive coding hierarchy.
 * Each level maintains a belief about a hidden state and generates
 * predictions for the level below.
 */
struct PredictiveCodingLevel {
    // Current estimate of the hidden state (belief).
    std::vector<double> state;
    // Predicted state from the level above (top-down).
    std::vector<double> prediction;
    // Prediction error (difference between state and prediction).
    std::vector<double> error;
    
    // Generative weights mapping THIS state to the level BELOW.
    // Row count = dim of level below. Col count = dim of this state.
    std::vector<std::vector<double>> gen_weights;
    
    double learning_rate = 0.1;
    
    PredictiveCodingLevel(size_t dim, size_t dim_below = 0) 
        : state(dim, 0.0), prediction(dim, 0.0), error(dim, 0.0) {
        
        // Initialize projection matrix if there is a level below
        if (dim_below > 0) {
            gen_weights.resize(dim_below, std::vector<double>(dim, 0.1));
            for (size_t i = 0; i < std::min(dim_below, dim); ++i) {
                gen_weights[i][i] = 1.0; // Identity-like base mapping
            }
        }
    }
    
    /**
     * Update the state by minimizing prediction error.
     * dE/dx = (x - pred) - W^T * bottom_up_error
     */
    void update_state(const std::vector<double>& bottom_up_error) {
        for (size_t i = 0; i < state.size(); ++i) {
            double top_down_grad = state[i] - prediction[i];
            
            // Multiply bottom-up error by the transpose of the generative weights
            double bottom_up_grad = 0.0;
            if (!gen_weights.empty()) {
                for (size_t j = 0; j < bottom_up_error.size(); ++j) {
                    bottom_up_grad += gen_weights[j][i] * bottom_up_error[j];
                }
            }
            
            double grad = top_down_grad - bottom_up_grad;
            state[i] -= learning_rate * grad;
        }
        
        // Recompute local prediction error after update.
        for (size_t i = 0; i < error.size(); ++i) {
            error[i] = state[i] - prediction[i];
        }
    }
};

/**
 * Hierarchical Predictive Coder.
 */
class PredictiveCoder {
public:
    /**
     * Initialize the hierarchy with given dimensions for each level.
     * Level 0 is the sensory input level.
     */
    explicit PredictiveCoder(const std::vector<size_t>& level_dims) {
        for (size_t i = 0; i < level_dims.size(); ++i) {
            size_t dim_below = (i == 0) ? 0 : level_dims[i-1];
            levels_.emplace_back(level_dims[i], dim_below);
        }
    }
    
    /**
     * Set the sensory observation (level 0 state).
     */
    void set_observation(const std::vector<double>& observation) {
        if (observation.size() != levels_[0].state.size()) {
            throw std::invalid_argument("Observation dimension mismatch");
        }
        levels_[0].state = observation;
        std::fill(levels_[0].error.begin(), levels_[0].error.end(), 0.0);
    }
    
    /**
     * Perform inference: update all hidden states to minimize prediction errors.
     */
    void infer(size_t iterations = 20) {
        for (size_t iter = 0; iter < iterations; ++iter) {
            // Top-down pass: generate predictions through the weight matrix.
            for (size_t l = 1; l < levels_.size(); ++l) {
                for (size_t i = 0; i < levels_[l-1].state.size(); ++i) {
                    double expected = 0.0;
                    for (size_t j = 0; j < levels_[l].state.size(); ++j) {
                        expected += levels_[l].gen_weights[i][j] * levels_[l].state[j];
                    }
                    levels_[l-1].prediction[i] = expected;
                }
            }
            
            // Bottom-up pass: compute errors and update states.
            for (size_t l = 0; l < levels_.size(); ++l) {
                if (l == 0) {
                    // Level 0: Sensory prediction error.
                    for (size_t i = 0; i < levels_[l].error.size(); ++i) {
                        levels_[l].error[i] = levels_[l].state[i] - levels_[l].prediction[i];
                    }
                } else {
                    // Higher levels: update state using bottom-up error.
                    levels_[l].update_state(levels_[l-1].error);
                }
            }
        }
    }
    
    std::vector<double> get_state(size_t level) const {
        if (level >= levels_.size()) return {};
        return levels_[level].state;
    }
    
    std::vector<double> get_error(size_t level) const {
        if (level >= levels_.size()) return {};
        return levels_[level].error;
    }
    
    double compute_free_energy() const {
        double fe = 0.0;
        for (const auto& level : levels_) {
            for (double e : level.error) {
                fe += 0.5 * e * e; 
            }
        }
        return fe;
    }
    
    size_t num_levels() const { return levels_.size(); }

private:
    std::vector<PredictiveCodingLevel> levels_;
};

} // namespace active_inference
} // namespace revarie

// =============================================================================
// Unit tests (compile with -DTEST_PREDICTIVE_CODER)
// =============================================================================
#ifdef TEST_PREDICTIVE_CODER
int main() {
    using namespace revarie::active_inference;
    
    // Test 1: Simple two-level hierarchy.
    {
        PredictiveCoder pc({2, 2});  
        pc.set_observation({1.0, 0.0});
        pc.infer(50);
        
        auto state_l1 = pc.get_state(1);
        double err = std::abs(state_l1[0] - 1.0) + std::abs(state_l1[1] - 0.0);
        assert(err < 0.5);
        std::cout << "[PASS] Test 1: Inference converges.\n";
    }
    
    // Test 2: Free energy decreases during inference.
    {
        PredictiveCoder pc({3, 2});
        pc.set_observation({1.0, 0.5, -0.5});
        
        double fe_before = pc.compute_free_energy();
        pc.infer(30);
        double fe_after = pc.compute_free_energy();
        
        assert(fe_after < fe_before);
        std::cout << "[PASS] Test 2: Free energy decreases.\n";
    }
    
    // Test 3: Multiple levels.
    {
        PredictiveCoder pc({4, 3, 2});
        pc.set_observation({1.0, 0.8, 0.2, -0.3});
        pc.infer(40);
        
        assert(pc.get_state(0).size() == 4);
        assert(pc.get_state(1).size() == 3);
        assert(pc.get_state(2).size() == 2);
        std::cout << "[PASS] Test 3: Multi-level hierarchy.\n";
    }
    
    std::cout << "All Predictive Coder tests passed.\n";
    return 0;
}
#endif
