"""
topological_invariant.py
Belief Space – Topological Invariant Computation.
Computes topological invariants (Betti numbers, persistence diagrams) to characterize
the global shape of the belief manifold M. This provides a rigorous mathematical
foundation for understanding the structure of the agent's belief space.

Based on persistent homology and computational topology.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
from scipy.spatial import distance_matrix
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import warnings


@dataclass
class PersistenceInterval:
    """A single interval in a persistence diagram."""
    birth: float
    death: float
    dimension: int
    
    @property
    def persistence(self) -> float:
        return self.death - self.birth
    
    def __repr__(self) -> str:
        return f"PersInterval(dim={self.dimension}, birth={self.birth:.3f}, death={self.death:.3f})"


class TopologicalInvariant:
    """
    Computes topological invariants from a point cloud representing samples
    from the belief manifold M.
    """
    
    def __init__(self, points: np.ndarray):
        """
        Initialize with a point cloud.
        
        Args:
            points: Array of shape (n_points, dimension) representing samples from M.
        """
        if points.ndim != 2:
            raise ValueError("Points must be a 2D array")
        self.points = points
        self.n_points = points.shape[0]
        self.dim = points.shape[1]
        
        # Cache for distance matrix
        self._dist_matrix: Optional[np.ndarray] = None
        
    @property
    def distance_matrix(self) -> np.ndarray:
        """Compute pairwise Euclidean distances between points."""
        if self._dist_matrix is None:
            self._dist_matrix = distance_matrix(self.points, self.points)
        return self._dist_matrix
    
    def compute_betti_numbers(self, radius: float) -> Dict[int, int]:
        """
        Estimate Betti numbers using Vietoris-Rips complex at a fixed radius.
        
        Args:
            radius: The radius for constructing the Vietoris-Rips complex.
            
        Returns:
            Dictionary mapping dimension to estimated Betti number.
        """
        # Build adjacency matrix: points i and j are connected if distance <= radius
        adj_matrix = (self.distance_matrix <= radius).astype(int)
        np.fill_diagonal(adj_matrix, 0)
        
        # Find connected components (β₀)
        n_components, labels = connected_components(csr_matrix(adj_matrix), directed=False)
        
        betti = {0: n_components}
        
        # For higher dimensions, we need to compute homology.
        # This is a simplified estimate: count "holes" by checking for cycles
        # that are not filled.
        if self.dim >= 2:
            # Build simplicial complex up to dimension 2
            edges = self._get_edges(radius)
            triangles = self._get_triangles(edges, radius)
            
            # β₁ = rank(H₁) = #edges - #vertices + #components - rank(∂₂)
            # For a 2-complex, we can approximate.
            n_vertices = self.n_points
            n_edges = len(edges)
            n_triangles = len(triangles)
            
            # Euler characteristic: χ = V - E + F
            chi = n_vertices - n_edges + n_triangles
            # β₀ - β₁ + β₂ = χ
            # Assuming β₂ ≈ 0 for typical point clouds
            betti_1 = max(0, n_components - chi)
            betti[1] = betti_1
            
        return betti
    
    def _get_edges(self, radius: float) -> Set[Tuple[int, int]]:
        """Return all edges (i, j) with i < j and distance <= radius."""
        edges = set()
        for i in range(self.n_points):
            for j in range(i + 1, self.n_points):
                if self.distance_matrix[i, j] <= radius:
                    edges.add((i, j))
        return edges
    
    def _get_triangles(self, edges: Set[Tuple[int, int]], radius: float) -> Set[Tuple[int, int, int]]:
        """Return all triangles (i, j, k) with i < j < k that are fully connected."""
        # Build adjacency list for faster lookup
        adj = defaultdict(set)
        for i, j in edges:
            adj[i].add(j)
            adj[j].add(i)
        
        triangles = set()
        for i, j in edges:
            common = adj[i].intersection(adj[j])
            for k in common:
                if i < j < k:
                    triangles.add((i, j, k))
        return triangles
    
    def compute_persistence_diagram(self, max_dim: int = 2, n_filtrations: int = 20) -> List[PersistenceInterval]:
        """
        Compute persistence diagram using a simple filtration by distance.
        
        Args:
            max_dim: Maximum homology dimension to compute.
            n_filtrations: Number of radius steps in the filtration.
            
        Returns:
            List of persistence intervals.
        """
        if self.n_points < 3:
            return []
        
        # Determine radius range
        max_dist = np.max(self.distance_matrix)
        min_dist = np.min(self.distance_matrix[self.distance_matrix > 0]) / 2
        radii = np.linspace(min_dist, max_dist, n_filtrations)
        
        intervals = []
        
        # Track components using Union-Find
        parent = list(range(self.n_points))
        rank = [0] * self.n_points
        birth_time = [0.0] * self.n_points
        
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        
        def union(x, y, time):
            rx, ry = find(x), find(y)
            if rx == ry:
                return False
            if rank[rx] < rank[ry]:
                rx, ry = ry, rx
            parent[ry] = rx
            if rank[rx] == rank[ry]:
                rank[rx] += 1
            # The younger component dies, the older survives
            if birth_time[rx] < birth_time[ry]:
                intervals.append(PersistenceInterval(birth=birth_time[ry], death=time, dimension=0))
            else:
                intervals.append(PersistenceInterval(birth=birth_time[rx], death=time, dimension=0))
                birth_time[rx] = birth_time[ry]
            return True
        
        # Process edges in order of increasing distance
        edges_with_dist = []
        for i in range(self.n_points):
            for j in range(i + 1, self.n_points):
                edges_with_dist.append((self.distance_matrix[i, j], i, j))
        edges_with_dist.sort(key=lambda x: x[0])
        
        for dist, i, j in edges_with_dist:
            union(i, j, dist)
        
        # Components that never die get death = inf
        roots = set()
        for i in range(self.n_points):
            root = find(i)
            if root not in roots:
                roots.add(root)
                intervals.append(PersistenceInterval(birth=0.0, death=float('inf'), dimension=0))
        
        return intervals
    
    def estimate_intrinsic_dimension(self) -> float:
        """
        Estimate the intrinsic dimension of the manifold using the
        Maximum Likelihood Estimation (MLE) method.
        """
        if self.n_points < 10:
            return float(self.dim)
        
        k = min(20, self.n_points - 1)
        dist_matrix = self.distance_matrix
        
        # For each point, find distance to k-th nearest neighbor
        dims = []
        for i in range(self.n_points):
            # FIXED: Use np.sort to return a copy instead of mutating the view in-place
            distances = np.sort(dist_matrix[i, :])
            
            # Distance to k-th neighbor (excluding self)
            r_k = distances[k]
            if r_k > 1e-9:
                # MLE estimate: d = (1/(k-2) * sum log(r_k / r_j))^{-1}
                sum_log = 0.0
                for j in range(1, k):
                    r_j = distances[j]
                    if r_j > 1e-9:
                        sum_log += np.log(r_k / r_j)
                if sum_log > 1e-9:
                    d_est = (k - 1) / sum_log
                    dims.append(d_est)
        
        if dims:
            return float(np.median(dims))
        return float(self.dim)
    
    def connected_components(self, radius: float) -> int:
        """Return the number of connected components (β₀) at given radius."""
        betti = self.compute_betti_numbers(radius)
        return betti.get(0, 0)


# =============================================================================
# Tests (pytest compatible)
# =============================================================================
def test_betti_circle():
    """Test Betti numbers for points sampled from a circle (β₀=1, β₁=1)."""
    np.random.seed(42)
    n_points = 50
    theta = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    points = np.column_stack([np.cos(theta), np.sin(theta)]) + 0.05 * np.random.randn(n_points, 2)
    
    ti = TopologicalInvariant(points)
    # Choose a radius that connects the circle but doesn't fill it
    radius = 0.5
    betti = ti.compute_betti_numbers(radius)
    assert betti[0] == 1, f"Expected β₀=1, got {betti[0]}"
    # β₁ should be 1 for a circle
    assert betti.get(1, 0) >= 1, f"Expected β₁≥1, got {betti.get(1, 0)}"


def test_persistence_diagram():
    """Test persistence diagram generation."""
    np.random.seed(42)
    points = np.random.randn(30, 2)
    ti = TopologicalInvariant(points)
    intervals = ti.compute_persistence_diagram(max_dim=1, n_filtrations=15)
    # Should have some intervals
    assert len(intervals) > 0


def test_intrinsic_dimension():
    """Test intrinsic dimension estimation."""
    np.random.seed(42)
    # Points on a 2D plane
    points = np.random.randn(100, 2)
    ti = TopologicalInvariant(points)
    dim = ti.estimate_intrinsic_dimension()
    assert 1.5 < dim < 3.0, f"Expected dimension near 2, got {dim}"


def test_connected_components():
    """Test connected components count."""
    # Two separated clusters
    cluster1 = np.random.randn(20, 2) + np.array([0, 0])
    cluster2 = np.random.randn(20, 2) + np.array([10, 10])
    points = np.vstack([cluster1, cluster2])
    ti = TopologicalInvariant(points)
    comps = ti.connected_components(radius=2.0)
    assert comps == 2, f"Expected 2 components, got {comps}"
