/**
 * test_rate_limit_monitor.cpp – Unit tests for Rate Limit Monitor
 * Compile with: g++ -std=c++17 -DTEST_RATE_LIMIT_MONITOR -o test_rlm test_rate_limit_monitor.cpp
 */

#define TEST_RATE_LIMIT_MONITOR
#include "../rate_limit_monitor.cpp"
#include <cassert>
#include <iostream>
#include <thread>
#include <chrono>

using namespace revarie::orchestrator;

void test_token_bucket_consumption() {
    TokenBucket bucket(10.0, 10);  // 10 tokens/sec, capacity 10
    
    // Should be able to consume up to capacity
    assert(bucket.try_consume(5));
    assert(bucket.try_consume(3));
    assert(bucket.try_consume(2));
    assert(!bucket.try_consume(1));  // empty
    
    std::cout << "[PASS] Token bucket consumption\n";
}

void test_token_bucket_refill() {
    TokenBucket bucket(100.0, 10);  // 100 tokens/sec
    
    bucket.try_consume(10);  // empty
    assert(!bucket.try_consume(1));
    
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    bucket.refill();
    assert(bucket.try_consume(5));  // should have ~5 tokens
    
    std::cout << "[PASS] Token bucket refill\n";
}

void test_rate_limit_monitor_registration() {
    RateLimitMonitor monitor;
    monitor.register_provider("groq", "llama-3.3-70b", {30, 6000});
    
    // Should allow requests up to RPM
    for (int i = 0; i < 30; i++) {
        assert(monitor.can_request("groq", "llama-3.3-70b"));
    }
    // 31st should be blocked
    assert(!monitor.can_request("groq", "llama-3.3-70b"));
    
    std::cout << "[PASS] Rate limit monitor registration\n";
}

void test_available_capacity() {
    RateLimitMonitor monitor;
    monitor.register_provider("cerebras", "qwen-235b", {30, 60000});
    
    double initial = monitor.available_capacity("cerebras", "qwen-235b");
    assert(initial > 0.9);
    
    for (int i = 0; i < 15; i++) {
        monitor.can_request("cerebras", "qwen-235b");
    }
    
    double after = monitor.available_capacity("cerebras", "qwen-235b");
    assert(after < initial);
    
    std::cout << "[PASS] Available capacity tracking\n";
}

int main() {
    test_token_bucket_consumption();
    test_token_bucket_refill();
    test_rate_limit_monitor_registration();
    test_available_capacity();
    
    std::cout << "All Rate Limit Monitor tests passed.\n";
    return 0;
}
