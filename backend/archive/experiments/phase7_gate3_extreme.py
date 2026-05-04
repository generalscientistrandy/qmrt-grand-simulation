"""
Phase 7, Gate 3: Extreme Combined Forcing
==========================================

Central Question: Can extreme combined forcing induce a spatial dimension
transition from ~1D filamentary to higher-dimensional organization?

Gate 2 established that individual forcing axes (pressure, confinement,
contrast) do not induce dimension transitions. Gate 3 tests whether
*combined* extreme conditions can push the system into a new geometric regime.

Tests:
1. Triple extreme: High pressure + tight confinement + strong contrast
2. Pressure-dominated extreme: Maximum crowding
3. Confinement-dominated extreme: Minimal boundary space
4. Temporal forcing: Dynamic parameter changes during simulation

Success criterion:
Either find a regime with spatial dimension d > 1.5,
or establish that ~1D is robust even under extreme combined forcing.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import time


class ExtremeForcingSimulator:
    """
    Simulator with extreme parameter configurations for dimension transition testing.
    """
    
    def __init__(
        self,
        size: int = 48,
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        gamma: float = 0.007,
        interior_radius_frac: float = 0.25,
        transition_width: float = 10.0,
        boundary_pressure: float = 0.0,  # Additional boundary forcing
    ):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.gamma = gamma
        self.interior_radius_frac = interior_radius_frac
        self.transition_width = transition_width
        self.boundary_pressure = boundary_pressure
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * self.interior_radius_frac
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = self.coupling_center
                    elif dist >= interior_r + self.transition_width:
                        coupling[i, j, k] = self.coupling_edge
                    else:
                        t = (dist - interior_r) / self.transition_width
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = self.coupling_center + blend * (self.coupling_edge - self.coupling_center)
        
        # Add boundary pressure term for extreme confinement
        if self.boundary_pressure > 0:
            boundary_dist = np.minimum(
                np.minimum(x, self.size - 1 - x),
                np.minimum(y, self.size - 1 - y)
            )
            boundary_dist = np.minimum(boundary_dist, np.minimum(z, self.size - 1 - z))
            boundary_factor = np.exp(-boundary_dist / 3.0) * self.boundary_pressure
            coupling = coupling + boundary_factor
        
        return coupling
    
    def step(self, dt: float = 0.04):
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        c_eff = 2.0
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff**2 * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff**2 * lap_i - self.gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        protection = topology_norm * self.channel_assignment
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
    
    def inject_vortex_dense(self, cx: int, cy: int, cz: int, radius: int = 2):
        """Inject vortex with tighter packing for extreme pressure tests."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / radius) * np.exp(1j * theta)
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


def measure_extended_metrics(defects: List[Tuple], size: int) -> Dict:
    """Measure metrics including local structure indicators."""
    if len(defects) < 15:
        return {'valid': False, 'n_defects': len(defects)}
    
    adj = build_adjacency(defects, size, radius=10.0)
    n = len(defects)
    graph_dist = compute_graph_distances(adj, n)
    
    # Distance correlation
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
    
    # Neighborhood scaling
    radii = list(range(1, 7))
    mean_counts = []
    for r in radii:
        counts = [np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0)) for i in range(n)]
        mean_counts.append(np.mean(counts))
    
    log_r = np.log(radii)
    log_n = np.log(np.array(mean_counts) + 1)
    coeffs = np.polyfit(log_r, log_n, 1)
    scaling_exponent = coeffs[0]
    
    # Fit quality
    fit = np.polyval(coeffs, log_r)
    ss_res = np.sum((log_n - fit)**2)
    ss_tot = np.sum((log_n - np.mean(log_n))**2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    # Local clustering coefficient (triangles)
    triangles = 0
    total_triplets = 0
    for node in range(n):
        neighbors = list(adj[node])
        k = len(neighbors)
        if k >= 2:
            for i_idx in range(len(neighbors)):
                for j_idx in range(i_idx + 1, len(neighbors)):
                    total_triplets += 1
                    if neighbors[j_idx] in adj[neighbors[i_idx]]:
                        triangles += 1
    
    clustering_coeff = triangles / total_triplets if total_triplets > 0 else 0
    
    # Average degree
    degrees = [len(adj[i]) for i in range(n)]
    avg_degree = np.mean(degrees) if degrees else 0
    
    # Network density
    max_edges = n * (n - 1) / 2
    actual_edges = sum(len(adj[i]) for i in range(n)) / 2
    density = actual_edges / max_edges if max_edges > 0 else 0
    
    return {
        'valid': True,
        'n_defects': n,
        'pearson_r': pearson_r,
        'scaling_exponent': scaling_exponent,
        'r_squared': r_squared,
        'mean_counts': mean_counts,
        'clustering_coeff': clustering_coeff,
        'avg_degree': avg_degree,
        'density': density,
        'n_triangles': triangles,
    }


def run_extreme_regime(
    name: str,
    n_vortices: int,
    coupling_center: float,
    coupling_edge: float,
    interior_radius_frac: float,
    transition_width: float,
    boundary_pressure: float = 0.0,
    vortex_spacing: int = 3,
    equilibration_steps: int = 800,
    measurement_steps: int = 500,
) -> Dict:
    """Run an extreme regime configuration and measure metrics."""
    print(f"\n  Regime: {name}")
    print(f"    Params: {n_vortices} vortices, r={interior_radius_frac:.0%}, "
          f"Δκ={coupling_center-coupling_edge:.2f}, bp={boundary_pressure:.1f}")
    
    sim = ExtremeForcingSimulator(
        size=48,
        coupling_center=coupling_center,
        coupling_edge=coupling_edge,
        interior_radius_frac=interior_radius_frac,
        transition_width=transition_width,
        boundary_pressure=boundary_pressure,
    )
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Dense vortex injection for extreme pressure
    center = 24
    injected = 0
    for i in range(-8, 9):
        for j in range(-8, 9):
            if injected >= n_vortices:
                break
            if abs(i) + abs(j) <= 8:
                sim.inject_vortex_dense(center + i * vortex_spacing, center + j * vortex_spacing, center)
                injected += 1
        if injected >= n_vortices:
            break
    
    print(f"    Equilibrating ({equilibration_steps} steps)...", end=" ", flush=True)
    for step in range(equilibration_steps):
        sim.step()
        if step % 200 == 0:
            defects = sim.detect_defects()
            print(f"{len(defects)}", end=" ", flush=True)
    print()
    
    # Measure
    print(f"    Measuring ({measurement_steps} steps)...", end=" ", flush=True)
    all_metrics = []
    for step in range(measurement_steps):
        sim.step()
        if step % 50 == 0:
            defects = sim.detect_defects()
            metrics = measure_extended_metrics(defects, sim.size)
            if metrics['valid']:
                all_metrics.append(metrics)
                print(f"d={metrics['scaling_exponent']:.2f}", end=" ", flush=True)
    print()
    
    if not all_metrics:
        print("    Result: INSUFFICIENT DATA")
        return {'valid': False, 'name': name}
    
    result = {
        'valid': True,
        'name': name,
        'n_samples': len(all_metrics),
        'mean_defects': np.mean([m['n_defects'] for m in all_metrics]),
        'mean_pearson': np.mean([m['pearson_r'] for m in all_metrics]),
        'mean_dimension': np.mean([m['scaling_exponent'] for m in all_metrics]),
        'std_dimension': np.std([m['scaling_exponent'] for m in all_metrics]),
        'mean_r_squared': np.mean([m['r_squared'] for m in all_metrics]),
        'mean_clustering': np.mean([m['clustering_coeff'] for m in all_metrics]),
        'mean_degree': np.mean([m['avg_degree'] for m in all_metrics]),
        'mean_density': np.mean([m['density'] for m in all_metrics]),
        'mean_triangles': np.mean([m['n_triangles'] for m in all_metrics]),
    }
    
    print(f"    Result: d = {result['mean_dimension']:.2f} ± {result['std_dimension']:.2f}, "
          f"clustering = {result['mean_clustering']:.3f}, triangles = {result['mean_triangles']:.1f}")
    
    return result


def run_gate3_tests():
    """
    Run extreme combined forcing tests to probe dimension transitions.
    """
    print("=" * 70)
    print("PHASE 7, GATE 3: EXTREME COMBINED FORCING")
    print("=" * 70)
    print()
    print("Question: Can extreme combined forcing induce spatial dimension transitions?")
    print()
    
    results = []
    
    # Control: Standard regime
    print("-" * 70)
    print("CONTROL: STANDARD REGIME")
    print("-" * 70)
    
    results.append(run_extreme_regime(
        name="Standard (baseline)",
        n_vortices=25,
        coupling_center=0.7,
        coupling_edge=0.2,
        interior_radius_frac=0.25,
        transition_width=10.0,
    ))
    
    # Test 1: Triple extreme
    print()
    print("-" * 70)
    print("TEST 1: TRIPLE EXTREME (Pressure + Confinement + Contrast)")
    print("-" * 70)
    
    results.append(run_extreme_regime(
        name="Triple Extreme",
        n_vortices=100,
        coupling_center=0.95,
        coupling_edge=0.02,
        interior_radius_frac=0.08,
        transition_width=3.0,
        vortex_spacing=2,
    ))
    
    # Test 2: Maximum pressure
    print()
    print("-" * 70)
    print("TEST 2: MAXIMUM PRESSURE (Dense packing)")
    print("-" * 70)
    
    results.append(run_extreme_regime(
        name="Maximum Pressure",
        n_vortices=150,
        coupling_center=0.7,
        coupling_edge=0.2,
        interior_radius_frac=0.25,
        transition_width=10.0,
        vortex_spacing=2,
    ))
    
    # Test 3: Extreme confinement with boundary pressure
    print()
    print("-" * 70)
    print("TEST 3: EXTREME CONFINEMENT (Boundary pressure)")
    print("-" * 70)
    
    results.append(run_extreme_regime(
        name="Extreme Confinement",
        n_vortices=30,
        coupling_center=0.9,
        coupling_edge=0.1,
        interior_radius_frac=0.06,
        transition_width=2.0,
        boundary_pressure=0.3,
    ))
    
    # Test 4: Moderate combined (to see gradient)
    print()
    print("-" * 70)
    print("TEST 4: MODERATE COMBINED")
    print("-" * 70)
    
    results.append(run_extreme_regime(
        name="Moderate Combined",
        n_vortices=60,
        coupling_center=0.85,
        coupling_edge=0.1,
        interior_radius_frac=0.15,
        transition_width=5.0,
    ))
    
    # Summary
    print()
    print("=" * 70)
    print("GATE 3 RESULTS SUMMARY")
    print("=" * 70)
    print()
    
    valid_results = [r for r in results if r['valid']]
    
    print(f"{'Regime':<25} {'Dim':>6} {'±':>5} {'Clust':>7} {'Tri':>6} {'Deg':>5}")
    print("-" * 60)
    
    for r in valid_results:
        print(f"{r['name']:<25} {r['mean_dimension']:>6.2f} {r['std_dimension']:>5.2f} "
              f"{r['mean_clustering']:>7.3f} {r['mean_triangles']:>6.1f} {r['mean_degree']:>5.1f}")
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    print()
    
    if valid_results:
        dimensions = [r['mean_dimension'] for r in valid_results]
        clusterings = [r['mean_clustering'] for r in valid_results]
        
        min_d = min(dimensions)
        max_d = max(dimensions)
        range_d = max_d - min_d
        
        print(f"Dimension range: {min_d:.2f} to {max_d:.2f} (span = {range_d:.2f})")
        print(f"Clustering range: {min(clusterings):.3f} to {max(clusterings):.3f}")
        print()
        
        # Check for transitions
        found_2d = any(d > 1.8 for d in dimensions)
        found_higher = any(d > 1.5 for d in dimensions)
        high_clustering = any(c > 0.1 for c in clusterings)
        
        if found_2d:
            print("MAJOR FINDING: 2D-like geometry achieved (d > 1.8)")
            high_d_regimes = [r['name'] for r in valid_results if r['mean_dimension'] > 1.8]
            print(f"  Regimes: {', '.join(high_d_regimes)}")
        elif found_higher:
            print("PARTIAL FINDING: Higher dimension regime found (d > 1.5)")
            high_d_regimes = [r['name'] for r in valid_results if r['mean_dimension'] > 1.5]
            print(f"  Regimes: {', '.join(high_d_regimes)}")
        else:
            print("NO DIMENSION TRANSITION: All regimes remain ~1D (d < 1.5)")
        
        print()
        if high_clustering:
            print("STRUCTURE FINDING: Significant clustering detected")
            high_c_regimes = [(r['name'], r['mean_clustering']) for r in valid_results if r['mean_clustering'] > 0.1]
            for name, c in high_c_regimes:
                print(f"  {name}: clustering = {c:.3f}")
        else:
            print("NO SIGNIFICANT CLUSTERING: Network remains predominantly linear")
        
        # Best candidate
        best_d = max(valid_results, key=lambda x: x['mean_dimension'])
        best_c = max(valid_results, key=lambda x: x['mean_clustering'])
        
        print()
        print(f"Highest dimension: {best_d['name']} (d = {best_d['mean_dimension']:.2f})")
        print(f"Highest clustering: {best_c['name']} (c = {best_c['mean_clustering']:.3f})")
    
    # Gate assessment
    print()
    print("=" * 70)
    print("GATE 3 ASSESSMENT")
    print("=" * 70)
    print()
    
    if valid_results:
        max_d = max(r['mean_dimension'] for r in valid_results)
        max_c = max(r['mean_clustering'] for r in valid_results)
        
        if max_d > 1.8:
            print("GATE 3 RESULT: DIMENSION TRANSITION ACHIEVED")
            print("  Extreme forcing can induce 2D-like spatial geometry")
            print("  Filamentary structure is NOT fundamental")
        elif max_d > 1.5:
            print("GATE 3 RESULT: PARTIAL TRANSITION")
            print("  Extreme forcing increases dimension but doesn't reach 2D")
            print("  There may be a higher-forcing transition threshold")
        elif max_c > 0.15:
            print("GATE 3 RESULT: STRUCTURAL ENRICHMENT WITHOUT DIMENSION CHANGE")
            print("  Extreme forcing creates local structure (clusters, triangles)")
            print("  But global geometry remains 1D")
        else:
            print("GATE 3 RESULT: ~1D GEOMETRY IS ROBUST")
            print("  Even extreme combined forcing cannot induce dimension transition")
            print("  Filamentary spatial structure appears fundamental to this regime")
        
        print()
        print("Key insight: Spatial dimension and local structure are partially independent")
        print("  - Dimension: How far structure extends in graph space")
        print("  - Clustering: How densely local neighborhoods are connected")
    
    return results


if __name__ == "__main__":
    results = run_gate3_tests()
