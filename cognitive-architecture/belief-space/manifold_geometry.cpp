/**
 * manifold_geometry.cpp
 * Belief Space – Manifold Geometry.
 * Implements a non‑Euclidean manifold M that represents the absolute boundary
 * conditions of the agent's existence. The manifold is defined by topological
 * invariants and provides distance metrics and boundary projections.
 */

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>
#include <cassert>

namespace revarie {
namespace belief_space {

/**
 * A point in the non‑Euclidean manifold M.
 * The dimension of the manifold is fixed at construction.
 */
class ManifoldPoint {
public:
    explicit ManifoldPoint(size_t dim) : coordinates_(dim, 0.0) {}
    explicit ManifoldPoint(const std::vector<double>& coords) : coordinates_(coords) {}
    
    double& operator[](size_t i) { return coordinates_[i]; }
    const double& operator[](size_t i) const { return coordinates_[i]; }
    size_t dimension() const { return coordinates_.size(); }
    
    ManifoldPoint operator+(const ManifoldPoint& other) const {
        if (dimension() != other.dimension())
            throw std::invalid_argument("Dimension mismatch");
        ManifoldPoint result(dimension());
        for (size_t i = 0; i < dimension(); ++i)
            result[i] = coordinates_[i] + other[i];
        return result;
    }
    
    ManifoldPoint operator-(const ManifoldPoint& other) const {
        if (dimension() != other.dimension())
            throw std::invalid_argument("Dimension mismatch");
        ManifoldPoint result(dimension());
        for (size_t i = 0; i < dimension(); ++i)
            result[i] = coordinates_[i] - other[i];
        return result;
    }
    
    ManifoldPoint operator*(double scalar) const {
        ManifoldPoint result(dimension());
        for (size_t i = 0; i < dimension(); ++i)
            result[i] = coordinates_[i] * scalar;
        return result;
    }
    
    double norm() const {
        double sum = 0.0;
        for (double x : coordinates_) sum += x * x;
        return std::sqrt(sum);
    }
    
    double dot(const ManifoldPoint& other) const {
        if (dimension() != other.dimension())
            throw std::invalid_argument("Dimension mismatch");
        double sum = 0.0;
        for (size_t i = 0; i < dimension(); ++i)
            sum += coordinates_[i] * other[i];
        return sum;
    }
    
private:
    std::vector<double> coordinates_;
};

/**
 * The non‑Euclidean manifold M.
 * Defined by a metric tensor that may vary across the manifold.
 */
class Manifold {
public:
    explicit Manifold(size_t dim) : dim_(dim) {}
    
    virtual ~Manifold() = default;
    
    size_t dimension() const { return dim_; }
    
    /**
     * Compute the squared geodesic distance between two points.
     * Default: Euclidean distance squared.
     */
    virtual double distance_sq(const ManifoldPoint& a, const ManifoldPoint& b) const {
        if (a.dimension() != dim_ || b.dimension() != dim_)
            throw std::invalid_argument("Dimension mismatch");
        double dist = 0.0;
        for (size_t i = 0; i < dim_; ++i) {
            double diff = a[i] - b[i];
            dist += diff * diff;
        }
        return dist;
    }
    
    /**
     * Compute the geodesic distance between two points.
     */
    virtual double distance(const ManifoldPoint& a, const ManifoldPoint& b) const {
        return std::sqrt(distance_sq(a, b));
    }
    
    virtual ManifoldPoint project(const ManifoldPoint& p) const {
        return p;
    }
    
    virtual bool contains(const ManifoldPoint& p) const {
        return true;
    }
    
    virtual ManifoldPoint log_map(const ManifoldPoint& base, const ManifoldPoint& target) const {
        return target - base;
    }
    
    virtual ManifoldPoint exp_map(const ManifoldPoint& base, const ManifoldPoint& v) const {
        return base + v;
    }

protected:
    size_t dim_;
};

/**
 * A spherical manifold (boundary of a ball) – simple non‑Euclidean example.
 * Constrains points strictly to the surface.
 */
class SphericalManifold : public Manifold {
public:
    SphericalManifold(size_t dim, double radius) : Manifold(dim), radius_(radius) {}
    
    double distance(const ManifoldPoint& a, const ManifoldPoint& b) const override {
        double dot = a.dot(b);
        double cos_theta = dot / (radius_ * radius_);
        cos_theta = std::max(-1.0, std::min(1.0, cos_theta));
        return radius_ * std::acos(cos_theta);
    }
    
    // FIXED: Ensure distance_sq routes to the spherical metric, not Euclidean
    double distance_sq(const ManifoldPoint& a, const ManifoldPoint& b) const override {
        double dist = distance(a, b);
        return dist * dist;
    }
    
    // FIXED: Project points from both inside and outside onto the surface boundary
    ManifoldPoint project(const ManifoldPoint& p) const override {
        double n = p.norm();
        if (n < 1e-12) {
            // Handle origin edge-case: arbitrarily project to first axis
            ManifoldPoint proj(dim_);
            proj[0] = radius_;
            return proj;
        }
        return p * (radius_ / n);
    }
    
    // FIXED: Mathematical consistency - surface of sphere means norm == radius
    bool contains(const ManifoldPoint& p) const override {
        return std::abs(p.norm() - radius_) <= 1e-9;
    }

private:
    double radius_;
};

} // namespace belief_space
} // namespace revarie

// =============================================================================
// Unit tests (compile with -DTEST_MANIFOLD_GEOMETRY)
// =============================================================================
#ifdef TEST_MANIFOLD_GEOMETRY
#include <iostream>

int main() {
    using namespace revarie::belief_space;
    const double PI = std::acos(-1.0); // FIXED: Replaced non-standard M_PI
    
    // Test Euclidean manifold
    Manifold euclidean(3);
    ManifoldPoint a(3), b(3);
    a[0] = 1.0; a[1] = 0.0; a[2] = 0.0;
    b[0] = 0.0; b[1] = 1.0; b[2] = 0.0;
    double dist = euclidean.distance(a, b);
    assert(std::abs(dist - std::sqrt(2.0)) < 1e-9);
    std::cout << "[PASS] Euclidean distance\n";
    
    // Test Spherical manifold
    SphericalManifold sphere(3, 1.0);
    ManifoldPoint p1(3), p2(3);
    p1[0] = 1.0; p1[1] = 0.0; p1[2] = 0.0;
    p2[0] = 0.0; p2[1] = 1.0; p2[2] = 0.0;
    double sphere_dist = sphere.distance(p1, p2);
    assert(std::abs(sphere_dist - PI/2.0) < 1e-6);
    std::cout << "[PASS] Spherical distance\n";
    
    // Test projection (from outside and inside)
    ManifoldPoint outside(3), inside(3);
    outside[0] = 2.0; outside[1] = 0.0; outside[2] = 0.0;
    inside[0] = 0.5; inside[1] = 0.0; inside[2] = 0.0;
    
    ManifoldPoint proj_out = sphere.project(outside);
    ManifoldPoint proj_in = sphere.project(inside);
    
    assert(std::abs(proj_out.norm() - 1.0) < 1e-9);
    assert(std::abs(proj_in.norm() - 1.0) < 1e-9);
    std::cout << "[PASS] Spherical projection\n";
    
    // Test contains
    assert(sphere.contains(p1));
    assert(!sphere.contains(outside));
    assert(!sphere.contains(inside));
    std::cout << "[PASS] Contains check\n";
    
    std::cout << "All Manifold Geometry tests passed.\n";
    return 0;
}
#endif
