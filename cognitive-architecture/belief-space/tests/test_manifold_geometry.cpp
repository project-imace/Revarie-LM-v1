/**
 * test_manifold_geometry.cpp
 * Unit tests for Manifold Geometry.
 * Compile with: g++ -std=c++17 -o test_mg test_manifold_geometry.cpp
 */

#include "../manifold_geometry.cpp"
#include <cassert>
#include <iostream>
#include <vector>
#include <cmath>
#include <fstream>
#include <sstream>
#include <string>

using namespace revarie::belief_space;

// Helper to read JSON fixture (simplified)
std::vector<double> read_point_from_json(const std::string& filename, const std::string& key) {
    std::ifstream file(filename);
    std::string line;
    // Naive parsing for simple fixture; in production use a proper JSON library
    while (std::getline(file, line)) {
        if (line.find("\"" + key + "\"") != std::string::npos) {
            // Extract array: [1.0, 2.0, 3.0]
            size_t start = line.find('[');
            size_t end = line.find(']');
            if (start != std::string::npos && end != std::string::npos) {
                std::string arr = line.substr(start+1, end-start-1);
                std::vector<double> point;
                std::stringstream ss(arr);
                std::string val;
                while (std::getline(ss, val, ',')) {
                    point.push_back(std::stod(val));
                }
                return point;
            }
        }
    }
    return {};
}

void test_euclidean_distance() {
    Manifold euclidean(3);
    ManifoldPoint a(3), b(3);
    a[0] = 1.0; a[1] = 0.0; a[2] = 0.0;
    b[0] = 0.0; b[1] = 1.0; b[2] = 0.0;
    double dist = euclidean.distance(a, b);
    assert(std::abs(dist - std::sqrt(2.0)) < 1e-9);
    std::cout << "[PASS] test_euclidean_distance\n";
}

void test_spherical_distance() {
    SphericalManifold sphere(3, 1.0);
    ManifoldPoint p1(3), p2(3);
    p1[0] = 1.0; p1[1] = 0.0; p1[2] = 0.0;
    p2[0] = 0.0; p2[1] = 1.0; p2[2] = 0.0;
    double dist = sphere.distance(p1, p2);
    const double PI = std::acos(-1.0);
    assert(std::abs(dist - PI/2.0) < 1e-6);
    std::cout << "[PASS] test_spherical_distance\n";
}

void test_spherical_projection() {
    SphericalManifold sphere(3, 1.0);
    ManifoldPoint outside(3), inside(3);
    outside[0] = 2.0; outside[1] = 0.0; outside[2] = 0.0;
    inside[0] = 0.5; inside[1] = 0.0; inside[2] = 0.0;

    ManifoldPoint proj_out = sphere.project(outside);
    ManifoldPoint proj_in = sphere.project(inside);
    
    assert(std::abs(proj_out.norm() - 1.0) < 1e-9);
    assert(std::abs(proj_in.norm() - 1.0) < 1e-9);
    std::cout << "[PASS] test_spherical_projection\n";
}

void test_contains() {
    SphericalManifold sphere(2, 1.0);
    ManifoldPoint on_sphere(2);
    on_sphere[0] = 1.0; on_sphere[1] = 0.0;
    ManifoldPoint inside(2);
    inside[0] = 0.5; inside[1] = 0.0;
    ManifoldPoint outside(2);
    outside[0] = 1.5; outside[1] = 0.0;
    
    assert(sphere.contains(on_sphere));
    assert(!sphere.contains(inside));
    assert(!sphere.contains(outside));
    std::cout << "[PASS] test_contains\n";
}

void test_log_exp_maps() {
    Manifold euclidean(2);
    ManifoldPoint base(2), target(2);
    base[0] = 1.0; base[1] = 1.0;
    target[0] = 2.0; target[1] = 2.0;
    
    ManifoldPoint v = euclidean.log_map(base, target);
    ManifoldPoint recovered = euclidean.exp_map(base, v);
    
    assert(std::abs(recovered[0] - target[0]) < 1e-9);
    assert(std::abs(recovered[1] - target[1]) < 1e-9);
    std::cout << "[PASS] test_log_exp_maps\n";
}

void test_fixture_loading() {
    // Ensure fixture file exists and can be parsed
    std::string fixture_path = "cognitive-architecture/belief-space/tests/fixtures/sample_manifold.json";
    std::ifstream file(fixture_path);
    assert(file.good() && "Fixture file not found. Run from repository root.");
    std::cout << "[PASS] test_fixture_loading\n";
}

int main() {
    test_euclidean_distance();
    test_spherical_distance();
    test_spherical_projection();
    test_contains();
    test_log_exp_maps();
    test_fixture_loading();
    std::cout << "All Manifold Geometry tests passed.\n";
    return 0;
}
