/**
 * sensing_function.cpp – Jungian Sensing Function
 * 
 * Implements Jung's Sensing psychological function: concrete perception,
 * detail orientation, and present-moment awareness. Sensing perceives
 * through the five senses, accumulating factual data without interpretation.
 * 
 * Theoretical Foundations:
 * - Jung (1921): "Psychological Types" – Sensing as irrational function
 *   oriented by concrete sensory data.
 * - von Franz (1971): "The Inferior Function" – Sensing's relationship with Intuition.
 * - Nardi (2011): "Neuroscience of Personality" – Sensing associated with
 *   sensorimotor cortex activation.
 * 
 * Mathematical Model:
 * - Detail salience S(d) = σ(contrast * recency * novelty)
 * - Sensory memory decay = e^{-λt}
 * - Pattern matching via feature vector similarity.
 */

#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <deque>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <sstream>
#include <cassert>

namespace revarie {
namespace jungian {

enum class SensoryModality {
    VISUAL,
    AUDITORY,
    TACTILE,
    OLFACTORY,
    GUSTATORY
};

struct SensoryDetail {
    std::string id;
    SensoryModality modality;
    std::string description;
    std::unordered_map<std::string, double> features;
    double salience;
    double intensity;
    std::chrono::steady_clock::time_point timestamp;
    int observation_count;
    
    SensoryDetail() : salience(0.5), intensity(0.5), observation_count(1) {
        timestamp = std::chrono::steady_clock::now();
    }
};

class SensingFunction {
public:
    struct Config {
        double decay_rate = 0.1;           // λ for memory decay
        double salience_threshold = 0.3;   // Minimum salience to store
        size_t max_details = 1000;         // Maximum stored details
        double recency_weight = 0.4;       // Weight for recent observations
        double novelty_weight = 0.3;       // Weight for novel stimuli
        double intensity_weight = 0.3;     // Weight for stimulus intensity
    };

    explicit SensingFunction(const std::string& name = "Sensing", Config config = Config{})
        : name_(name), config_(std::move(config)) {}

    /**
     * Perceive and record a concrete sensory detail.
     */
    std::string perceive(const std::string& description,
                         SensoryModality modality = SensoryModality::VISUAL,
                         double intensity = 0.5,
                         const std::unordered_map<std::string, double>& features = {}) {
        SensoryDetail detail;
        detail.id = generate_id(description);
        detail.modality = modality;
        detail.description = description;
        detail.intensity = std::clamp(intensity, 0.0, 1.0);
        detail.features = features;
        detail.timestamp = std::chrono::steady_clock::now();
        
        // Check if similar detail exists
        auto existing = find_similar(detail);
        if (existing != details_.end()) {
            existing->observation_count++;
            existing->timestamp = detail.timestamp;
            existing->intensity = (existing->intensity + intensity) / 2.0;
            compute_salience(*existing);
            return existing->id;
        }
        
        compute_salience(detail);
        
        if (detail.salience >= config_.salience_threshold) {
            details_.push_back(detail);
            if (details_.size() > config_.max_details) {
                evict_lowest_salience();
            }
        }
        
        return detail.id;
    }

    /**
     * Retrieve all details of a specific modality.
     */
    std::vector<SensoryDetail> get_details(SensoryModality modality,
                                           size_t limit = 50) const {
        std::vector<SensoryDetail> result;
        for (const auto& d : details_) {
            if (d.modality == modality) {
                result.push_back(d);
            }
        }
        std::sort(result.begin(), result.end(),
                  [](const SensoryDetail& a, const SensoryDetail& b) {
                      return a.salience > b.salience;
                  });
        if (result.size() > limit) {
            result.resize(limit);
        }
        return result;
    }

    /**
     * Retrieve details matching keywords.
     */
    std::vector<SensoryDetail> query(const std::string& keyword, size_t limit = 20) const {
        std::vector<SensoryDetail> result;
        std::string lower_kw = keyword;
        std::transform(lower_kw.begin(), lower_kw.end(), lower_kw.begin(), ::tolower);
        
        for (const auto& d : details_) {
            std::string lower_desc = d.description;
            std::transform(lower_desc.begin(), lower_desc.end(), lower_desc.begin(), ::tolower);
            if (lower_desc.find(lower_kw) != std::string::npos) {
                result.push_back(d);
            }
        }
        
        std::sort(result.begin(), result.end(),
                  [](const SensoryDetail& a, const SensoryDetail& b) {
                      return a.salience > b.salience;
                  });
        if (result.size() > limit) {
            result.resize(limit);
        }
        return result;
    }

    /**
     * Apply memory decay to all stored details.
     */
    void apply_decay() {
        auto now = std::chrono::steady_clock::now();
        // Pass 1: Apply decay math safely
        for (auto& detail : details_) {
            auto age = std::chrono::duration_cast<std::chrono::seconds>(now - detail.timestamp).count();
            double decay_factor = std::exp(-config_.decay_rate * age / 86400.0);
            detail.salience *= decay_factor;
        }
        // Pass 2: Safe erase-remove idiom
        details_.erase(
            std::remove_if(details_.begin(), details_.end(),
                           [](const SensoryDetail& d) { return d.salience < 0.01; }),
            details_.end()
        );
    }

    /**
     * Find the most salient detail currently.
     */
    SensoryDetail most_salient() const {
        if (details_.empty()) {
            return SensoryDetail{};
        }
        return *std::max_element(details_.begin(), details_.end(),
                                 [](const SensoryDetail& a, const SensoryDetail& b) {
                                     return a.salience < b.salience;
                                 });
    }

    /**
     * Count details by modality.
     */
    std::unordered_map<SensoryModality, size_t> count_by_modality() const {
        std::unordered_map<SensoryModality, size_t> counts;
        for (const auto& d : details_) {
            counts[d.modality]++;
        }
        return counts;
    }

    size_t size() const { return details_.size(); }
    bool empty() const { return details_.empty(); }
    void clear() { details_.clear(); }

private:
    std::string name_;
    Config config_;
    std::deque<SensoryDetail> details_;

    std::string generate_id(const std::string& desc) {
        auto now = std::chrono::steady_clock::now().time_since_epoch().count();
        return std::to_string(std::hash<std::string>{}(desc) ^ now);
    }

    void compute_salience(SensoryDetail& detail) {
        auto age = std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::steady_clock::now() - detail.timestamp).count();
        double recency = std::exp(-config_.decay_rate * age / 3600.0);
        
        double novelty = 1.0;
        if (!details_.empty()) {
            double similarity_sum = 0.0;
            for (const auto& existing : details_) {
                similarity_sum += compute_similarity(detail, existing);
            }
            novelty = 1.0 - (similarity_sum / details_.size());
        }
        
        detail.salience = config_.recency_weight * recency
                        + config_.novelty_weight * novelty
                        + config_.intensity_weight * detail.intensity;
        detail.salience = std::clamp(detail.salience, 0.0, 1.0);
    }

    double compute_similarity(const SensoryDetail& a, const SensoryDetail& b) const {
        if (a.modality != b.modality) return 0.0;
        if (a.features.empty() || b.features.empty()) return 0.0;
        
        double dot = 0.0, norm_a = 0.0, norm_b = 0.0;
        for (const auto& [k, v] : a.features) {
            auto it = b.features.find(k);
            if (it != b.features.end()) {
                dot += v * it->second;
            }
            norm_a += v * v;
        }
        for (const auto& [_, v] : b.features) {
            norm_b += v * v;
        }
        
        if (norm_a < 1e-9 || norm_b < 1e-9) return 0.0;
        return dot / (std::sqrt(norm_a) * std::sqrt(norm_b));
    }

    auto find_similar(const SensoryDetail& target, double threshold = 0.7) {
        return std::find_if(details_.begin(), details_.end(),
                            [&](const SensoryDetail& existing) {
                                return compute_similarity(target, existing) > threshold;
                            });
    }

    void evict_lowest_salience() {
        auto lowest = std::min_element(details_.begin(), details_.end(),
                                       [](const SensoryDetail& a, const SensoryDetail& b) {
                                           return a.salience < b.salience;
                                       });
        if (lowest != details_.end()) {
            details_.erase(lowest);
        }
    }
};

} // namespace jungian
} // namespace revarie

// =============================================================================
// Tests
// =============================================================================
#ifdef TEST_SENSING_FUNCTION
int main() {
    using namespace revarie::jungian;
    
    SensingFunction sf("Test");
    
    // Test perception
    std::string id1 = sf.perceive("Red apple on the table", SensoryModality::VISUAL, 0.8);
    assert(!id1.empty());
    assert(sf.size() == 1);
    std::cout << "[PASS] Perception test\n";
    
    // Test duplicate perception
    std::string id2 = sf.perceive("Red apple on the table", SensoryModality::VISUAL, 0.8);
    assert(id1 == id2);
    assert(sf.size() == 1);
    std::cout << "[PASS] Duplicate perception test\n";
    
    // Test query
    sf.perceive("Blue car outside", SensoryModality::VISUAL, 0.6);
    auto results = sf.query("apple", 10);
    assert(results.size() == 1);
    assert(results[0].description.find("apple") != std::string::npos);
    std::cout << "[PASS] Query test\n";
    
    // Test modality filter
    sf.perceive("Loud noise", SensoryModality::AUDITORY, 0.9);
    auto visual = sf.get_details(SensoryModality::VISUAL, 10);
    assert(visual.size() == 2);
    std::cout << "[PASS] Modality filter test\n";
    
    // Test most salient
    auto salient = sf.most_salient();
    assert(salient.modality == SensoryModality::AUDITORY);
    std::cout << "[PASS] Most salient test\n";
    
    std::cout << "All Sensing Function tests passed.\n";
    return 0;
}
#endif
