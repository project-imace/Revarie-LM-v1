#include <iostream>
#include <vector>
#include <string>
#include <deque>
#include <chrono>
#include <algorithm>
#include <cmath>

namespace revarie {
namespace jungian {

struct SensoryDetail {
    std::string description;
    double salience;
    std::chrono::steady_clock::time_point timestamp;
};

class SensingFunction {
public:
    void perceive(const std::string& desc, double intensity = 0.5) {
        SensoryDetail detail = {desc, intensity, std::chrono::steady_clock::now()};
        details_.push_back(detail);
        if (details_.size() > 100) details_.pop_front();
    }

    // FIXED: Corrected iterator invalidation bug using erase-remove idiom
    void apply_decay(double rate = 0.1) {
        auto now = std::chrono::steady_clock::now();
        details_.erase(
            std::remove_if(details_.begin(), details_.end(), [&](const SensoryDetail& d) {
                auto age = std::chrono::duration_cast<std::chrono::seconds>(now - d.timestamp).count();
                return std::exp(-rate * age / 3600.0) < 0.01;
            }),
            details_.end()
        );
    }

    size_t size() const { return details_.size(); }

private:
    std::deque<SensoryDetail> details_;
};

}
}
