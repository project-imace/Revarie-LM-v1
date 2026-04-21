/**
 * test_belief_state.cpp
 * Unit tests for Belief State representation.
 * Compile with: g++ -std=c++17 -o test_bs test_belief_state.cpp
 */

#include "../belief_state.cpp"
#include <cassert>
#include <iostream>
#include <vector>
#include <random>

using namespace revarie::pomdp;

void test_uniform_initialization() {
    BeliefState b(4);
    assert(b.size() == 4);
    for (size_t i = 0; i < 4; ++i) {
        assert(std::abs(b[i] - 0.25) < 1e-9);
    }
    std::cout << "[PASS] test_uniform_initialization\n";
}

void test_custom_initialization() {
    BeliefState b(std::vector<double>{2.0, 3.0, 5.0});
    assert(b.size() == 3);
    assert(std::abs(b[0] - 0.2) < 1e-9);
    assert(std::abs(b[1] - 0.3) < 1e-9);
    assert(std::abs(b[2] - 0.5) < 1e-9);
    std::cout << "[PASS] test_custom_initialization\n";
}

void test_belief_update() {
    BeliefState b(2);  // uniform [0.5, 0.5]
    std::vector<std::vector<double>> obs_model = {
        {0.9, 0.1},
        {0.1, 0.9}
    };
    std::vector<std::vector<std::vector<double>>> trans_model = {
        { {1.0, 0.0}, {0.0, 1.0} }  // action 0: identity
    };

    BeliefState b2 = b.update(0, 0, obs_model, trans_model);
    assert(b2[0] > b2[1]);
    std::cout << "[PASS] test_belief_update\n";
}

void test_predict_step() {
    BeliefState b(std::vector<double>{1.0, 0.0});
    std::vector<std::vector<std::vector<double>>> trans = {
        { {0.8, 0.2}, {0.3, 0.7} }
    };
    BeliefState predicted = b.predict(0, trans);
    assert(std::abs(predicted[0] - 0.8) < 1e-9);
    assert(std::abs(predicted[1] - 0.2) < 1e-9);
    std::cout << "[PASS] test_predict_step\n";
}

void test_entropy() {
    BeliefState b(std::vector<double>{1.0, 0.0});
    assert(b.entropy() < 1e-9);
    
    BeliefState b2(2, true);
    double h = b2.entropy();
    assert(std::abs(h - std::log(2.0)) < 1e-9);
    std::cout << "[PASS] test_entropy\n";
}

void test_map_state() {
    BeliefState b(std::vector<double>{0.1, 0.7, 0.2});
    assert(b.map_state() == 1);
    std::cout << "[PASS] test_map_state\n";
}

void test_is_deterministic() {
    BeliefState b1(std::vector<double>{1.0, 0.0});
    assert(b1.is_deterministic());
    
    BeliefState b2(std::vector<double>{0.5, 0.5});
    assert(!b2.is_deterministic());
    std::cout << "[PASS] test_is_deterministic\n";
}

void test_sampling() {
    std::mt19937 rng(42);
    BeliefState b(std::vector<double>{1.0, 0.0, 0.0});
    for (int i = 0; i < 10; ++i) {
        assert(b.sample(rng) == 0);
    }
    std::cout << "[PASS] test_sampling\n";
}

void test_belief_history() {
    BeliefHistory history;
    history.push(BeliefState(2, true));
    history.push(BeliefState(std::vector<double>{0.8, 0.2}));
    assert(history.size() == 2);
    assert(std::abs(history.current()[0] - 0.8) < 1e-9);
    std::cout << "[PASS] test_belief_history\n";
}

int main() {
    test_uniform_initialization();
    test_custom_initialization();
    test_belief_update();
    test_predict_step();
    test_entropy();
    test_map_state();
    test_is_deterministic();
    test_sampling();
    test_belief_history();
    std::cout << "All Belief State tests passed.\n";
    return 0;
}
