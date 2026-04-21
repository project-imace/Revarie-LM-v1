/**
 * test_rebound_force.cpp
 * Unit tests for Rebound Force mechanism.
 * Compile with: g++ -std=c++17 -o test_rf test_rebound_force.cpp
 */

#include "../rebound_force.cpp"
#include <cassert>
#include <iostream>
#include <vector>
#include <cmath>

using namespace revarie::rebound;

void test_force_computation() {
    std::vector<double> point = {2.0, 0.0};
    double distance = 1.0;
    std::vector<double> gradient = {1.0, 0.0};
    double k = 1.0;
    
    auto force = compute_rebound_force(point, distance, gradient, k);
    assert(force.size() == 2);
    assert(force[0] < 0.0);
    assert(force[1] == 0.0);
    assert(std::abs(force[0] + 1.0) < 1e-9);
    std::cout << "[PASS] test_force_computation\n";
}

void test_samara_vs_artery() {
    std::vector<double> point = {1.5, 0.0};
    double distance = 0.5;
    std::vector<double> gradient = {1.0, 0.0};
    
    auto force_samara = compute_rebound_force(point, distance, gradient, Elasticity::SAMARA);
    auto force_artery = compute_rebound_force(point, distance, gradient, Elasticity::ARTERY);
    
    assert(std::abs(force_artery[0]) > std::abs(force_samara[0]) * 50.0);
    std::cout << "[PASS] test_samara_vs_artery\n";
}

void test_apply_rebound() {
    std::vector<double> point = {1.8, 0.0};
    double distance = 0.8;
    std::vector<double> gradient = {1.0, 0.0};
    double k = 1.0;
    
    double original = point[0];
    apply_rebound(point, distance, gradient, k, 0.5);
    assert(point[0] < original);
    assert(point[0] > 0.0);
    std::cout << "[PASS] test_apply_rebound\n";
}

void test_negative_distance() {
    std::vector<double> point = {0.5, 0.0};
    double distance = -0.5;
    std::vector<double> gradient = {1.0, 0.0};
    double k = 1.0;
    
    auto force = compute_rebound_force(point, distance, gradient, k);
    assert(force[0] > 0.0);
    std::cout << "[PASS] test_negative_distance\n";
}

void test_dimension_mismatch() {
    std::vector<double> point = {2.0, 0.0};
    double distance = 1.0;
    std::vector<double> gradient = {1.0};  // Wrong dimension
    double k = 1.0;
    
    bool caught = false;
    try {
        compute_rebound_force(point, distance, gradient, k);
    } catch (const std::invalid_argument&) {
        caught = true;
    }
    assert(caught);
    std::cout << "[PASS] test_dimension_mismatch\n";
}

int main() {
    test_force_computation();
    test_samara_vs_artery();
    test_apply_rebound();
    test_negative_distance();
    test_dimension_mismatch();
    std::cout << "All Rebound Force tests passed.\n";
    return 0;
}
