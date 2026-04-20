/**
 * test_sequential_reasoner.cpp
 * Unit tests for SequentialReasoner.
 */

#include "../sequential_reasoner.cpp"
#include <cassert>
#include <iostream>

void test_basic_reasoning() {
    revarie::system_two::SequentialReasoner reasoner;
    auto result = reasoner.reason("What is the meaning of life?");
    assert(!result.conclusion.empty());
    assert(result.trace.size() >= 3);
    assert(result.total_confidence > 0.0 && result.total_confidence <= 1.0);
    std::cout << "[PASS] test_basic_reasoning\n";
}

void test_timeout_handling() {
    revarie::system_two::SequentialReasoner::Config config;
    config.timeout = std::chrono::milliseconds(10);
    config.max_steps = 100;
    revarie::system_two::SequentialReasoner reasoner(config);
    auto result = reasoner.reason("Explain quantum mechanics in detail.");
    assert(result.timed_out || !result.conclusion.empty());
    std::cout << "[PASS] test_timeout_handling\n";
}

void test_empty_input() {
    revarie::system_two::SequentialReasoner reasoner;
    auto result = reasoner.reason("");
    assert(!result.conclusion.empty());
    std::cout << "[PASS] test_empty_input\n";
}

int main() {
    test_basic_reasoning();
    test_timeout_handling();
    test_empty_input();
    std::cout << "All System 2 tests passed.\n";
    return 0;
}
