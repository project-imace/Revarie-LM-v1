"""Unit tests for TopologicalInvariant."""

import sys
import os
import importlib.util

import pytest
import numpy as np

# Dynamically load the module from its actual filesystem path (handles hyphens)
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "topological_invariant.py")
)
spec = importlib.util.spec_from_file_location("topological_invariant", module_path)
topo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topo)

TopologicalInvariant = topo.TopologicalInvariant
PersistenceInterval = topo.PersistenceInterval


def test_initialization():
    """Test that TopologicalInvariant initializes correctly."""
    points = np.random.randn(20, 3)
    ti = TopologicalInvariant(points)
    assert ti.n_points == 20
    assert ti.dim == 3
    assert ti.distance_matrix.shape == (20, 20)


def test_distance_matrix_caching():
    """Test that distance matrix is cached properly."""
    points = np.random.randn(15, 2)
    ti = TopologicalInvariant(points)
    dm1 = ti.distance_matrix
    dm2 = ti.distance_matrix
    assert dm1 is dm2  # Should return cached version


def test_betti_circle():
    """Test Betti numbers for points sampled from a circle (β₀=1, β₁=1)."""
    np.random.seed(42)
    n_points = 50
    theta = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    points = np.column_stack([np.cos(theta), np.sin(theta)]) + 0.01 * np.random.randn(n_points, 2)
    
    ti = TopologicalInvariant(points)
    radius = 0.25
    betti = ti.compute_betti_numbers(radius)
    assert betti[0] == 1, f"Expected β₀=1, got {betti[0]}"
    assert betti.get(1, 0) >= 1, f"Expected β₁≥1, got {betti.get(1, 0)}"


def test_betti_two_clusters():
    """Test Betti numbers for two well-separated clusters (β₀=2, β₁=0)."""
    np.random.seed(42)
    cluster1 = np.random.randn(20, 2) + np.array([0, 0])
    cluster2 = np.random.randn(20, 2) + np.array([10, 10])
    points = np.vstack([cluster1, cluster2])
    
    ti = TopologicalInvariant(points)
    radius = 2.0
    betti = ti.compute_betti_numbers(radius)
    assert betti[0] == 2, f"Expected β₀=2, got {betti[0]}"


def test_persistence_diagram():
    """Test persistence diagram generation."""
    np.random.seed(42)
    points = np.random.randn(30, 2)
    ti = TopologicalInvariant(points)
    intervals = ti.compute_persistence_diagram(max_dim=1, n_filtrations=15)
    assert len(intervals) > 0
    # All intervals should be dimension 0 for this filtration
    assert all(iv.dimension == 0 for iv in intervals)


def test_persistence_interval_properties():
    """Test PersistenceInterval dataclass."""
    iv = PersistenceInterval(birth=0.5, death=2.0, dimension=1)
    assert iv.birth == 0.5
    assert iv.death == 2.0
    assert iv.dimension == 1
    assert iv.persistence == 1.5
    assert "PersInterval" in repr(iv)


def test_intrinsic_dimension_plane():
    """Test intrinsic dimension estimation for a 2D plane."""
    np.random.seed(42)
    points = np.random.randn(100, 2)
    ti = TopologicalInvariant(points)
    dim = ti.estimate_intrinsic_dimension()
    assert 1.5 < dim < 3.0, f"Expected dimension near 2, got {dim}"


def test_intrinsic_dimension_line():
    """Test intrinsic dimension estimation for a 1D line."""
    np.random.seed(42)
    t = np.linspace(0, 10, 100)
    points = np.column_stack([t, np.zeros_like(t)]) + 0.01 * np.random.randn(100, 2)
    ti = TopologicalInvariant(points)
    dim = ti.estimate_intrinsic_dimension()
    assert 0.8 < dim < 1.8, f"Expected dimension near 1, got {dim}"


def test_intrinsic_dimension_small_sample():
    """Test intrinsic dimension with too few points falls back to ambient dimension."""
    points = np.random.randn(5, 3)
    ti = TopologicalInvariant(points)
    dim = ti.estimate_intrinsic_dimension()
    assert dim == 3.0


def test_connected_components():
    """Test connected components count."""
    cluster1 = np.random.randn(15, 2) + np.array([0, 0])
    cluster2 = np.random.randn(15, 2) + np.array([10, 10])
    cluster3 = np.random.randn(15, 2) + np.array([20, 20])
    points = np.vstack([cluster1, cluster2, cluster3])
    ti = TopologicalInvariant(points)
    comps = ti.connected_components(radius=2.5)
    assert comps == 3, f"Expected 3 components, got {comps}"


def test_invalid_input():
    """Test that invalid input raises appropriate errors."""
    points_1d = np.random.randn(10)
    with pytest.raises(ValueError, match="Points must be a 2D array"):
        TopologicalInvariant(points_1d)


def test_empty_persistence_diagram():
    """Test persistence diagram with too few points returns empty list."""
    points = np.random.randn(2, 2)
    ti = TopologicalInvariant(points)
    intervals = ti.compute_persistence_diagram()
    assert intervals == []
