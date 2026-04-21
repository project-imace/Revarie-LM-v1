/**
 * acetylcholine_analog.cpp – Affective Modulator: Acetylcholine Analog
 * 
 * Implements a computational analog of the cholinergic system.
 * Acetylcholine mediates attention, sensory processing, learning,
 * and memory encoding. Critical for focused attention and plasticity.
 * 
 * Theoretical Foundations:
 * - Hasselmo (2006): Role of acetylcholine in memory and attention.
 * - Sarter et al. (2001): Cholinergic system and cognition.
 * - Yu & Dayan (2005): Acetylcholine in attention and expected uncertainty.
 */

#include <vector>
#include <deque>
#include <cmath>
#include <algorithm>
#include <chrono>
#include <cassert>

namespace revarie {
namespace persona {

class AcetylcholineAnalog {
public:
    struct Config {
        double baseline = 0.5;
        double attention_boost = 0.3;
        double novelty_boost = 0.2;
        double decay_rate = 0.05;
        double attention_threshold = 0.4;
        double learning_rate = 0.1;
    };

    explicit AcetylcholineAnalog(Config config = Config{}) 
        : config_(std::move(config)), level_(config_.baseline) {
        last_update_ = std::chrono::steady_clock::now();
    }

    /**
     * Boost acetylcholine in response to attentional demand.
     * Returns the phasic response magnitude.
     */
    double focus_attention(double intensity) {
        double clamped = std::clamp(intensity, 0.0, 1.0);
        double phasic = clamped * config_.attention_boost;
        level_ = std::min(1.0, level_ + phasic);
        record_phasic("focus", clamped, phasic);
        update_derived_states();
        return phasic;
    }

    /**
     * Boost acetylcholine in response to novel stimuli.
     */
    double process_novelty(double novelty) {
        double clamped = std::clamp(novelty, 0.0, 1.0);
        double phasic = clamped * config_.novelty_boost;
        level_ = std::min(1.0, level_ + phasic);
        record_phasic("novelty", clamped, phasic);
        update_derived_states();
        return phasic;
    }

    /**
     * Apply tonic decay toward baseline.
     */
    void update_tonic() {
        auto now = std::chrono::steady_clock::now();
        double dt = std::chrono::duration<double>(now - last_update_).count();
        
        double decay = config_.decay_rate * dt * (level_ - config_.baseline);
        level_ = std::max(config_.baseline, level_ - decay);
        
        level_history_.push_back(level_);
        if (level_history_.size() > max_history_) {
            level_history_.pop_front();
        }
        
        update_derived_states();
        last_update_ = now;
    }

    /**
     * Compute current attentional focus quality (0.0 to 1.0).
     */
    double attention_quality() const {
        if (level_ < config_.attention_threshold) {
            return level_ / config_.attention_threshold * 0.5;
        }
        // Inverted-U: optimal around 0.7
        double optimal = 0.7;
        return 1.0 - 0.3 * std::abs(level_ - optimal) / (1.0 - optimal);
    }

    /**
     * Compute learning rate modulation (plasticity).
     * Higher ACh = higher learning rate for attended stimuli.
     */
    double learning_rate_modulation() const {
        return config_.learning_rate * (1.0 + level_);
    }

    /**
     * Whether agent is in focused attentional state.
     */
    bool is_focused() const {
        return level_ > config_.attention_threshold;
    }

    /**
     * Get sensory gain (enhanced processing of attended stimuli).
     */
    double sensory_gain() const {
        return 1.0 + level_ * 0.5;
    }

    double get_level() const { return level_; }
    double get_baseline() const { return config_.baseline; }

    void reset() {
        level_ = config_.baseline;
        level_history_.clear();
        phasic_events_.clear();
        last_update_ = std::chrono::steady_clock::now();
        update_derived_states();
    }

private:
    Config config_;
    double level_;
    double attention_quality_ = 0.5;
    double learning_modulation_ = 0.1;
    
    std::deque<double> level_history_;
    std::deque<std::tuple<std::string, double, double, std::chrono::steady_clock::time_point>> phasic_events_;
    size_t max_history_ = 100;
    std::chrono::steady_clock::time_point last_update_;

    void update_derived_states() {
        attention_quality_ = attention_quality();
        learning_modulation_ = learning_rate_modulation();
    }

    void record_phasic(const std::string& type, double intensity, double response) {
        phasic_events_.push_back({type, intensity, response, std::chrono::steady_clock::now()});
        if (phasic_events_.size() > max_history_) {
            phasic_events_.pop_front();
        }
    }
};

} // namespace persona
} // namespace revarie

// =============================================================================
// Tests
// =============================================================================
#ifdef TEST_ACETYLCHOLINE_ANALOG
#include <iostream>

int main() {
    using namespace revarie::persona;
    
    AcetylcholineAnalog ach;
    
    // Test focus boost
    double initial = ach.get_level();
    ach.focus_attention(0.8);
    assert(ach.get_level() > initial);
    std::cout << "[PASS] Focus boost test\n";
    
    // Test novelty boost
    initial = ach.get_level();
    ach.process_novelty(0.7);
    assert(ach.get_level() > initial);
    std::cout << "[PASS] Novelty boost test\n";
    
    // Test tonic decay
    ach.update_tonic();
    assert(ach.get_level() <= 1.0);
    std::cout << "[PASS] Tonic decay test\n";
    
    // Test attention quality
    double quality = ach.attention_quality();
    assert(quality >= 0.0 && quality <= 1.0);
    std::cout << "[PASS] Attention quality test\n";
    
    std::cout << "All Acetylcholine Analog tests passed.\n";
    return 0;
}
#endif
