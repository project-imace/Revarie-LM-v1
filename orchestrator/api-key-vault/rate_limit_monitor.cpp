/**
 * rate_limit_monitor.cpp – Real‑time Rate Limit Monitor
 * 
 * Tracks API rate limits using token bucket algorithm.
 * Provides predictive rate limit avoidance.
 */

#include <iostream>
#include <unordered_map>
#include <string>
#include <chrono>
#include <atomic>
#include <mutex>
#include <cassert>

namespace revarie {
namespace orchestrator {

class TokenBucket {
public:
    TokenBucket() = default;
public:
    TokenBucket(double rate, int capacity)
        : rate_(rate), capacity_(capacity), tokens_(capacity) {
        last_refill_ = std::chrono::steady_clock::now();
    }

    bool try_consume(int tokens = 1) {
        refill();
        if (tokens_ >= tokens) {
            tokens_ -= tokens;
            return true;
        }
        return false;
    }

    void refill() {
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double>(now - last_refill_).count();
        double new_tokens = elapsed * rate_;
        tokens_ = std::min(static_cast<double>(capacity_), tokens_ + new_tokens);
        last_refill_ = now;
    }

    double available() const { return tokens_; }
    int capacity() const { return capacity_; }

private:
    double rate_;      // tokens per second
    int capacity_;
    double tokens_;
    std::chrono::steady_clock::time_point last_refill_;
};

class RateLimitMonitor {
public:
    struct LimitConfig {
        int rpm;  // requests per minute
        int tpm;  // tokens per minute
    };

    void register_provider(const std::string& provider, const std::string& model, LimitConfig config) {
        std::lock_guard<std::mutex> lock(mutex_);
        std::string key = provider + ":" + model;
        double request_rate = static_cast<double>(config.rpm) / 60.0;
        buckets_[key] = TokenBucket(request_rate, config.rpm);
    }

    bool can_request(const std::string& provider, const std::string& model) {
        std::lock_guard<std::mutex> lock(mutex_);
        std::string key = provider + ":" + model;
        auto it = buckets_.find(key);
        if (it == buckets_.end()) {
            return true;  // no limit configured
        }
        return it->second.try_consume(1);
    }

    void record_request(const std::string& provider, const std::string& model) {
        // Already consumed in can_request
    }

    double available_capacity(const std::string& provider, const std::string& model) {
        std::lock_guard<std::mutex> lock(mutex_);
        std::string key = provider + ":" + model;
        auto it = buckets_.find(key);
        if (it == buckets_.end()) {
            return 1.0;
        }
        it->second.refill();
        return it->second.available() / it->second.capacity();
    }

private:
    std::unordered_map<std::string, TokenBucket> buckets_;
    std::mutex mutex_;
};

} // namespace orchestrator
} // namespace revarie

// =============================================================================
// Tests
// =============================================================================
