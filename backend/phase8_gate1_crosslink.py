"""
Phase 8, Gate 1: Cross-Link Stabilization Layer
================================================

Central Question: Can a mechanism that specifically rewards cross-filament
connectivity raise the effective dimension above ~1D?

Phase 7 established:
- Proto-spacetime is robustly filamentary (~1D)
- Forcing alone cannot break the ~1D barrier
- The system favors chain-like extension over lateral branching

Phase 8 hypothesis:
Higher-dimensional organization emerges from RECURSIVE BRANCHING LAYERS
that specifically promote cross-filament connectivity.

The Cross-Link Stabilization Layer:
- Identifies neighboring filaments (defects on different chains)
- Rewards connections between them (cross-links)
- Stabilizes loops and sheet-like structures
- Does NOT just add more complexity to existing filaments

Success criterion:
Effective dimension d > 1.5 (breaking the ~1.2 ceiling from Phase 7)
AND increased loop/triangle density relative to baseline

Key metrics:
1. Effective dimension (scaling exponent)
2. Loop density (triangles per defect)
3. Cross-link ratio (transverse vs longitudinal edges)
4. Sheet-like motif count
5. Coarse-grained filling fraction
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Set
import time


class CrossLinkSimulator:
    """
    Simulator with cross-link stabilization layer.
    
    The cross-link layer works by:
    1. Tracking which defects are on the same "filament" (chain-connected)
    2. Identifying potential cross-links (edges between different filaments)
    3. Providing additional stabilization for cross-linked defects
    """
    
    def __init__(
        self,
        size: int = 48,
        cross_link_strength: float = 0.0,  # 0 = baseline, >0 = cross-link reward
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
    ):
        self.size = size
        self.cross_link_strength = cross_link_strength
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        
        # Field state
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Standard layers
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        # NEW: Cross-link field
        # This field is high where cross-links exist or are forming
        self.cross_link_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        transition_width = 10.0
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = self.coupling_center
                    elif dist >= interior_r + transition_width:
                        coupling[i, j, k] = self.coupling_edge
                    else:
                        t = (dist - interior_r) / transition_width
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = self.coupling_center + blend * (self.coupling_edge - self.coupling_center)
        return coupling
    
    def step(self, dt: float = 0.04):
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        gamma = 0.007
        c_eff = 2.0
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff**2 * lap_r - gamma * self.psi_r_dot
        acc_i = c_eff**2 * lap_i - gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        # Topology computation
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Standard channel assignment
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        # Standard remnant field
        self.remnant_field += 0.005 * (topology_norm - 0.3 * self.remnant_field)
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        # NEW: Cross-link field update
        # Cross-link field is enhanced where topology is high AND there's
        # significant topology in neighboring directions (not just along one axis)
        if self.cross_link_strength > 0:
            # Compute directional topology spread
            topo_x = np.abs(grad_x)
            topo_y = np.abs(grad_y)
            topo_z = np.abs(grad_z)
            
            # Multi-directional topology indicator
            # High when topology exists in multiple directions (potential cross-links)
            directional_spread = np.minimum(topo_x, topo_y) + np.minimum(topo_y, topo_z) + np.minimum(topo_x, topo_z)
            directional_spread = gaussian_filter(directional_spread, sigma=2.0)
            directional_spread = directional_spread / (np.max(directional_spread) + 1e-10)
            
            # Cross-link field grows where multi-directional topology exists
            self.cross_link_field += 0.02 * (directional_spread - 0.2 * self.cross_link_field)
            self.cross_link_field = np.clip(self.cross_link_field, 0, 1)
        
        # Protection mechanism (standard + cross-link enhancement)
        protection = topology_norm * self.channel_assignment
        
        # NEW: Cross-link enhancement to protection
        # Defects in cross-link regions get additional protection
        if self.cross_link_strength > 0:
            cross_link_boost = self.cross_link_strength * self.cross_link_field
            protection = protection + cross_link_boost * topology_norm
        
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple[int, int, int]]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        low_amp = amp < threshold
        labeled, n = label(low_amp)
        
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) < 5:
                continue
            coords = np.where(component)
            cx = int(np.mean(coords[0]))
            cy = int(np.mean(coords[1]))
            cz = int(np.mean(coords[2]))
            defects.append((cx, cy, cz))
        
        return defects
    
    def inject_vortex(self, cx: int, cy: int):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)


def euclidean_distance_periodic(p1: Tuple, p2: Tuple, size: int) -> float:
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def build_adjacency(defects: List[Tuple], size: int, radius: float = 10.0) -> Dict[int, set]:
    adj = defaultdict(set)
    for i in range(len(defects)):
        for j in range(i + 1, len(defects)):
            d = euclidean_distance_periodic(defects[i], defects[j], size)
            if d < radius:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def compute_graph_distances(adj: Dict[int, set], n: int) -> np.ndarray:
    distances = np.full((n, n), np.inf)
    for start in range(n):
        distances[start, start] = 0
        queue = deque([start])
        visited = {start}
        while queue:
            node = queue.popleft()
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[start, neighbor] = distances[start, node] + 1
                    queue.append(neighbor)
    return distances


def identify_filaments(adj: Dict[int, set], n: int) -> List[Set[int]]:
    """
    Identify filaments as connected components where each node has degree <= 2.
    Cross-links are edges that connect different filaments.
    """
    # Find linear chains (degree <= 2)
    linear_nodes = {i for i in range(n) if len(adj[i]) <= 2}
    
    # Build subgraph of linear nodes
    linear_adj = defaultdict(set)
    for i in linear_nodes:
        for j in adj[i]:
            if j in linear_nodes:
                linear_adj[i].add(j)
                linear_adj[j].add(i)
    
    # Find connected components in linear subgraph
    visited = set()
    filaments = []
    
    for start in linear_nodes:
        if start in visited:
            continue
        filament = set()
        queue = deque([start])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            filament.add(node)
            for neighbor in linear_adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        if len(filament) >= 2:
            filaments.append(filament)
    
    return filaments


def count_cross_links(adj: Dict[int, set], filaments: List[Set[int]]) -> int:
    """Count edges that connect different filaments."""
    # Map each node to its filament
    node_to_filament = {}
    for i, filament in enumerate(filaments):
        for node in filament:
            node_to_filament[node] = i
    
    cross_links = 0
    counted_edges = set()
    
    for node, neighbors in adj.items():
        if node not in node_to_filament:
            continue
        node_filament = node_to_filament[node]
        for neighbor in neighbors:
            if neighbor not in node_to_filament:
                continue
            edge = tuple(sorted([node, neighbor]))
            if edge in counted_edges:
                continue
            counted_edges.add(edge)
            if node_to_filament[neighbor] != node_filament:
                cross_links += 1
    
    return cross_links


def measure_geometry(defects: List[Tuple], size: int) -> Dict:
    """Comprehensive geometric measurement."""
    if len(defects) < 15:
        return {'valid': False, 'n_defects': len(defects)}
    
    n = len(defects)
    adj = build_adjacency(defects, size, radius=10.0)
    graph_dist = compute_graph_distances(adj, n)
    
    # 1. Graph-Euclidean correlation
    euclidean_dists = []
    graph_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(defects[i], defects[j], size))
                graph_dists.append(graph_dist[i, j])
    
    if len(euclidean_dists) < 10:
        return {'valid': False, 'n_defects': n}
    
    pearson_r, _ = pearsonr(euclidean_dists, graph_dists)
    
    # 2. Effective dimension (neighborhood scaling)
    radii = list(range(1, 7))
    mean_counts = []
    for r in radii:
        counts = [np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0)) for i in range(n)]
        mean_counts.append(np.mean(counts))
    
    log_r = np.log(radii)
    log_n = np.log(np.array(mean_counts) + 1)
    coeffs = np.polyfit(log_r, log_n, 1)
    effective_dimension = coeffs[0]
    
    # 3. Triangle count and density
    triangles = 0
    for node in range(n):
        neighbors = list(adj[node])
        for i_idx in range(len(neighbors)):
            for j_idx in range(i_idx + 1, len(neighbors)):
                if neighbors[j_idx] in adj[neighbors[i_idx]]:
                    triangles += 1
    triangles //= 3  # Each triangle counted 3 times
    triangle_density = triangles / n if n > 0 else 0
    
    # 4. Filament analysis and cross-links
    filaments = identify_filaments(adj, n)
    n_filaments = len(filaments)
    cross_links = count_cross_links(adj, filaments)
    
    total_edges = sum(len(adj[i]) for i in range(n)) // 2
    cross_link_ratio = cross_links / total_edges if total_edges > 0 else 0
    
    # 5. Clustering coefficient
    clustering_sum = 0
    clustering_count = 0
    for node in range(n):
        neighbors = list(adj[node])
        k = len(neighbors)
        if k >= 2:
            local_triangles = 0
            for i_idx in range(len(neighbors)):
                for j_idx in range(i_idx + 1, len(neighbors)):
                    if neighbors[j_idx] in adj[neighbors[i_idx]]:
                        local_triangles += 1
            max_triangles = k * (k - 1) / 2
            clustering_sum += local_triangles / max_triangles
            clustering_count += 1
    
    avg_clustering = clustering_sum / clustering_count if clustering_count > 0 else 0
    
    # 6. Average degree
    avg_degree = sum(len(adj[i]) for i in range(n)) / n if n > 0 else 0
    
    return {
        'valid': True,
        'n_defects': n,
        'pearson_r': pearson_r,
        'effective_dimension': effective_dimension,
        'triangles': triangles,
        'triangle_density': triangle_density,
        'n_filaments': n_filaments,
        'cross_links': cross_links,
        'cross_link_ratio': cross_link_ratio,
        'avg_clustering': avg_clustering,
        'avg_degree': avg_degree,
        'total_edges': total_edges,
    }


def run_cross_link_test(cross_link_strength: float, name: str) -> Dict:
    """Run a single test with given cross-link strength."""
    print(f"\n  Test: {name} (strength={cross_link_strength})")
    
    sim = CrossLinkSimulator(
        size=48,
        cross_link_strength=cross_link_strength,
    )
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Inject vortices
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    print(f"    Equilibrating...", end=" ", flush=True)
    for step in range(800):
        sim.step()
        if step % 200 == 0:
            defects = sim.detect_defects()
            print(f"{len(defects)}", end=" ", flush=True)
    print()
    
    print(f"    Measuring...", end=" ", flush=True)
    all_metrics = []
    for step in range(500):
        sim.step()
        if step % 50 == 0:
            defects = sim.detect_defects()
            metrics = measure_geometry(defects, sim.size)
            if metrics['valid']:
                all_metrics.append(metrics)
                print(f"d={metrics['effective_dimension']:.2f}", end=" ", flush=True)
    print()
    
    if not all_metrics:
        return {'valid': False, 'name': name}
    
    # Aggregate
    result = {
        'valid': True,
        'name': name,
        'strength': cross_link_strength,
        'n_samples': len(all_metrics),
        'mean_defects': np.mean([m['n_defects'] for m in all_metrics]),
        'mean_dimension': np.mean([m['effective_dimension'] for m in all_metrics]),
        'std_dimension': np.std([m['effective_dimension'] for m in all_metrics]),
        'mean_triangles': np.mean([m['triangles'] for m in all_metrics]),
        'mean_triangle_density': np.mean([m['triangle_density'] for m in all_metrics]),
        'mean_cross_links': np.mean([m['cross_links'] for m in all_metrics]),
        'mean_cross_link_ratio': np.mean([m['cross_link_ratio'] for m in all_metrics]),
        'mean_clustering': np.mean([m['avg_clustering'] for m in all_metrics]),
        'mean_degree': np.mean([m['avg_degree'] for m in all_metrics]),
    }
    
    print(f"    Result: d={result['mean_dimension']:.2f}±{result['std_dimension']:.2f}, "
          f"triangles={result['mean_triangles']:.0f}, cross-link ratio={result['mean_cross_link_ratio']:.3f}")
    
    return result


def run_phase8_gate1():
    """
    Phase 8 Gate 1: Test whether cross-link stabilization raises effective dimension.
    """
    print("=" * 70)
    print("PHASE 8, GATE 1: CROSS-LINK STABILIZATION LAYER")
    print("=" * 70)
    print()
    print("Question: Can cross-link stabilization raise effective dimension above ~1D?")
    print()
    print("Mechanism: Additional protection for defects in regions with multi-directional")
    print("           topological structure (potential cross-link sites)")
    print()
    
    results = []
    
    # Test range of cross-link strengths
    strengths = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    
    print("-" * 70)
    print("TESTING CROSS-LINK STRENGTH GRADIENT")
    print("-" * 70)
    
    for strength in strengths:
        if strength == 0.0:
            name = "Baseline (no cross-link)"
        else:
            name = f"Cross-link {strength:.1f}"
        results.append(run_cross_link_test(strength, name))
    
    # Summary
    print()
    print("=" * 70)
    print("PHASE 8 GATE 1 RESULTS SUMMARY")
    print("=" * 70)
    print()
    
    valid_results = [r for r in results if r['valid']]
    
    print(f"{'Strength':>8} {'Dimension':>10} {'Triangles':>10} {'CrossLinks':>11} {'Clustering':>11}")
    print("-" * 55)
    
    for r in valid_results:
        print(f"{r['strength']:>8.1f} {r['mean_dimension']:>10.2f} "
              f"{r['mean_triangles']:>10.0f} {r['mean_cross_links']:>11.0f} "
              f"{r['mean_clustering']:>11.3f}")
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    print()
    
    if valid_results:
        baseline = valid_results[0]
        best = max(valid_results, key=lambda x: x['mean_dimension'])
        
        baseline_d = baseline['mean_dimension']
        best_d = best['mean_dimension']
        dimension_increase = best_d - baseline_d
        
        print(f"Baseline dimension: {baseline_d:.2f}")
        print(f"Best dimension: {best_d:.2f} (at strength={best['strength']:.1f})")
        print(f"Dimension increase: {dimension_increase:+.2f}")
        print()
        
        # Check for breakthrough
        breakthrough = best_d > 1.5
        significant = dimension_increase > 0.2
        
        if breakthrough:
            print("BREAKTHROUGH: Effective dimension > 1.5 achieved!")
            print(f"  Cross-link stabilization successfully raised dimension to {best_d:.2f}")
        elif significant:
            print("PARTIAL SUCCESS: Significant dimension increase detected")
            print(f"  Dimension rose by {dimension_increase:.2f}, but stays below 1.5")
        else:
            print("NO BREAKTHROUGH: Dimension remains in ~1D regime")
            print(f"  Cross-link stabilization did not significantly raise dimension")
        
        # Cross-link analysis
        print()
        baseline_xl = baseline['mean_cross_links']
        best_xl = best['mean_cross_links']
        
        print(f"Cross-link count: {baseline_xl:.0f} (baseline) → {best_xl:.0f} (best)")
        
        if best_xl > baseline_xl * 1.5:
            print("  Cross-links increased significantly")
        else:
            print("  Cross-links did not increase substantially")
    
    # Gate assessment
    print()
    print("=" * 70)
    print("GATE 1 ASSESSMENT")
    print("=" * 70)
    print()
    
    if valid_results:
        best_d = max(r['mean_dimension'] for r in valid_results)
        baseline_d = valid_results[0]['mean_dimension']
        
        if best_d > 1.8:
            print("GATE 1 RESULT: MAJOR BREAKTHROUGH")
            print("  Cross-link stabilization can induce 2D-like geometry")
            print("  The recursive branching hypothesis is SUPPORTED")
        elif best_d > 1.5:
            print("GATE 1 RESULT: PARTIAL BREAKTHROUGH")
            print("  Cross-link stabilization raises dimension above the ~1.2 ceiling")
            print("  The recursive branching hypothesis shows promise")
        elif best_d > baseline_d + 0.15:
            print("GATE 1 RESULT: INCREMENTAL PROGRESS")
            print("  Cross-link stabilization increases dimension but not enough")
            print("  May need stronger mechanism or different approach")
        else:
            print("GATE 1 RESULT: NO BREAKTHROUGH")
            print("  Cross-link stabilization does not significantly raise dimension")
            print("  The ~1D filamentary regime remains robust")
            print()
            print("  Possible interpretations:")
            print("  - Cross-link mechanism is too weak")
            print("  - Different mechanism needed (area coherence? multi-channel?)")
            print("  - The ~1D structure may be truly fundamental")
    
    return results


if __name__ == "__main__":
    results = run_phase8_gate1()
