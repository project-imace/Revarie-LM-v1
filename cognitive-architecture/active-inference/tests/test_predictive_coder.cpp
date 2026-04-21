/**
 * test_predictive_coder.cpp
 * Unit tests for the Hierarchical Predictive Coder.
 * Compile with: g++ -std=c++17 -o test_pc test_predictive_coder.cpp
 */

#include "../predictive_coder.cpp"
#include <cassert>
#include <iostream>
#include <vector>
#include <cmath>

using namespace revarie::active_inference;

void test_initialization() {
    PredictiveCoder pc({4, 3, 2});
    assert(pc.num_levels() == 3);
    assert(pc.get_state(0).size() == 4);
    assert(pc.get_state(1).size() == 3);
    assert(pc.get_state(2).size() == 2);
    std::cout << "[PASS] test_initialization\n";
}

void test_set_observation() {
    PredictiveCoder pc({3, 2});
    std::vector<double> obs = {1.0, 0.5, -0.2};
    pc.set_observation(obs);
    auto state = pc.get_state(0);
    for (size_t i = 0; i < obs.size(); ++i) {
        assert(std::abs(state[i] - obs[i]) < 1e-9);
    }
    std::cout << "[PASS] test_set_observation\n";
}

void test_inference_converges() {
    PredictiveCoder pc({2, 2});
    pc.set_observation({1.0, 0.0});
    pc.infer(50);
    auto state_l1 = pc.get_state(1);
    // Hidden state should approach the observation
    double err = std::abs(state_l1[0] - 1.0) + std::abs(state_l1[1] - 0.0);
    assert(err < 0.5);
    std::cout << "[PASS] test_inference_converges\n";
}

void test_free_energy_decreases() {
    PredictiveCoder pc({3, 2});
    pc.set_observation({1.0, 0.5, -0.5});
    double fe_before = pc.compute_free_energy();
    pc.infer(30);
    double fe_after = pc.compute_free_energy();
    assert(fe_after < fe_before);
    std::cout << "[PASS] test_free_energy_decreases\n";
}

void test_get_error() {
    PredictiveCoder pc({2, 2});
    pc.set_observation({1.0, 0.0});
    pc.infer(20);
    auto error = pc.get_error(0);
    assert(error.size() == 2);
    std::cout << "[PASS] test_get_error\n";
}

void test_dimension_mismatch_throws() {
    PredictiveCoder pc({3, 2});
    bool caught = false;
    try {
        pc.set_observation({1.0, 0.0}); // Wrong size
    } catch (const std::invalid_argument&) {
        caught = true;
    }
    assert(caught);
    std::cout << "[PASS] test_dimension_mismatch_throws\n";
}

int main() {
    test_initialization();
    test_set_observation();
    test_inference_converges();
    test_free_energy_decreases();
    test_get_error();
    test_dimension_mismatch_throws();
    std::cout << "All Predictive Coder tests passed.\n";
    return 0;
}
