/**
 * rebound_force.cpp
 * Rebound Mechanism – Elastic Feedback Force.
 * Implements F_rebound = -k · Δ(M, A), the core mathematical innovation
 * of the REVARIE framework. This mechanism ensures the agent remains
 * within its axiomatic boundaries (Belief Space M) by applying a
 * corrective force proportional to the geometric distance from the manifold.
 */

#include <vector>
#include <cmath>
#include <stdexcept>
#include <cassert>

namespace revarie {
namespace rebound {

/**
 * Compute the rebound force vector.
 * * @param belief_point The current belief state (point in manifold coordinates).
 * @param manifold_distance Signed distance to the manifold M (positive if outside, negative if inside).
 * @param manifold_gradient Gradient of the distance function at belief_point.
 * @param k Elasticity constant of the persona.
 * @return The rebound force vector F_rebound = -k · d · ∇d, where d = manifold_distance.
 */
std::vector<double> compute_rebound_force(
    const std::vector<double>& belief_point,
    double manifold_distance,
    const std::vector<double>& manifold_gradient,
    double k) {
    
    if (belief_point.size() != manifold_gradient.size()) {
        throw std::invalid_argument("Dimension mismatch between belief point and gradient");
    }
    
    std::vector<double> force(belief_point.size(), 0.0);
    double magnitude = -k * manifold_distance;
    
    for (size_t i = 0; i < belief_point.size(); ++i) {
        force[i] = magnitude * manifold_gradient[i];
    }
    
    return force;
}

/**
 * Apply the rebound force to update the belief state.
 * * @param belief_point Current belief state (modified in place).
 * @param manifold_distance Signed distance to M.
 * @param manifold_gradient Gradient of distance at belief_point.
 * @param k Elasticity constant.
 * @param step_size Integration step size (default 0.1).
 */
void apply_rebound(
    std::vector<double>& belief_point,
    double manifold_distance,
    const std::vector<double>& manifold_gradient,
    double k,
    double step_size = 0.1) {
    
    auto force = compute_rebound_force(belief_point, manifold_distance, manifold_gradient, k);
    for (size_t i = 0; i < belief_point.size(); ++i) {
        belief_point[i] += step_size * force[i];
    }
}

/**
 * Elasticity constants for different personas.
 * Samara: low k (organic, human-like deviation allowed).
 * Artery 1.0: high k (immediate, surgical correction).
 */
namespace Elasticity {
    constexpr double SAMARA = 0.1;      // Low elasticity – allows gentle drift
    constexpr double ARTERY = 10.0;     // High elasticity – rapid snap-back
    constexpr double DEFAULT = 1.0;
}

} // namespace rebound
} // namespace revarie

// =============================================================================
// Unit tests (compile with -DTEST_REBOUND_FORCE)
// =============================================================================
#ifdef TEST_REBOUND_FORCE
#include <iostream>

int main() {
    using namespace revarie::rebound;
    
    // Test 1: Force direction is opposite to gradient for positive distance
    {
        std::vector<double> point = {2.0, 0.0};  // Outside unit circle
        double distance = 1.0;  // 2.0 - 1.0
        std::vector<double> gradient = {1.0, 0.0};  // Points outward
        double k = 1.0;
        
        auto force = compute_rebound_force(point, distance, gradient, k);
        // Force should be inward (negative x direction)
        assert(force[0] < 0.0);
        assert(force[1] == 0.0);
        assert(std::abs(force[0] + 1.0) < 1e-9);
        std::cout << "[PASS] Force direction test\n";
    }
    
    // Test 2: Samara vs Artery 1.0 elasticity
    {
        std::vector<double> point = {1.5, 0.0};
        double distance = 0.5;
        std::vector<double> gradient = {1.0, 0.0};
        
        auto force_samara = compute_rebound_force(point, distance, gradient, Elasticity::SAMARA);
        auto force_artery = compute_rebound_force(point, distance, gradient, Elasticity::ARTERY);
        
        // Artery's force should be 100x stronger than Samara's
        assert(std::abs(force_artery[0]) > std::abs(force_samara[0]) * 50.0);
        std::cout << "[PASS] Samara vs Artery 1.0 elasticity test\n";
    }
    
    // Test 3: Apply rebound updates point toward manifold
    {
        std::vector<double> point = {1.8, 0.0};
        double distance = 0.8;  // Outside unit circle
        std::vector<double> gradient = {1.0, 0.0};
        double k = 1.0;
        
        apply_rebound(point, distance, gradient, k, 0.5);
        // Point should move inward
        assert(point[0] < 1.8);
        assert(point[0] > 0.0);
        std::cout << "[PASS] Apply rebound test\n";
    }
    
    // Test 4: Negative distance (inside manifold) produces outward force
    {
        std::vector<double> point = {0.5, 0.0};
        double distance = -0.5;  // Inside unit circle
        std::vector<double> gradient = {1.0, 0.0};
        double k = 1.0;
        
        auto force = compute_rebound_force(point, distance, gradient, k);
        // Force should be outward (positive x direction)
        assert(force[0] > 0.0);
        std::cout << "[PASS] Negative distance test\n";
    }
    
    std::cout << "All Rebound Force tests passed.\n";
    return 0;
}
#endif
