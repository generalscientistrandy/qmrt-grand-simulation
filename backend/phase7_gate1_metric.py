"""
Phase 7, Gate 1: Metric-Like Properties
========================================

Central Question: Can the relational structure begin to behave like a geometry?

"Metric-like" means:
- Graph distance correlates with spatial (Euclidean) distance
- Neighborhoods grow with consistent scaling (dimension-like)
- Locality is preserved (graph neighbors are spatially nearby)
- Structure survives coarse-graining

Tests (in order of priority):
1. Graph distance vs Euclidean distance correlation
2. Neighborhood growth scaling
3. Locality consistency
4. Coarse-grained stability

Success criterion:
Positive correlation between relational and spatial distance,
with consistent scaling that suggests emergent geometric structure.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist, squareform
from scipy.stats import pearsonr, spearmanr
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Set, Optional
import time


class MetricTestSimulator:
    """
    Simulator for metric property analysis.
    """
    
    def __init__(
        self,
        size: int = 48,
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        gamma: float = 0.007,
    ):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.gamma = gamma
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.step_count = 0
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        return np.where(r <= interior_r, self.coupling_center, self.coupling_edge)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
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
    
    def inject_vortex(self, cx: int, cy: int, charge: int = 1):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * charge * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)


def euclidean_distance_periodic(p1: Tuple, p2: Tuple, size: int) -> float:
    """Compute Euclidean distance with periodic boundaries."""
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def build_adjacency_graph(defects: List[Tuple], size: int, radius: float = 10.0) -> Dict[int, Set[int]]:
    """Build adjacency graph from defect positions."""
    adj = defaultdict(set)
    
    for i in range(len(defects)):
        for j in range(i + 1, len(defects)):
            d = euclidean_distance_periodic(defects[i], defects[j], size)
            if d < radius:
                adj[i].add(j)
                adj[j].add(i)
    
    return adj


def compute_graph_distances(adj: Dict[int, Set[int]], n_nodes: int) -> np.ndarray:
    """Compute all-pairs shortest path distances using BFS."""
    distances = np.full((n_nodes, n_nodes), np.inf)
    
    for start in range(n_nodes):
        # BFS from start
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


def test_distance_correlation(defects: List[Tuple], adj: Dict[int, Set[int]], size: int) -> Dict:
    """
    TEST 1: Graph distance vs Euclidean distance correlation.
    This is the anchor test for metric-like properties.
    """
    n = len(defects)
    if n < 10:
        return {'pearson_r': 0, 'spearman_r': 0, 'n_pairs': 0, 'valid': False}
    
    # Compute graph distances
    graph_dist = compute_graph_distances(adj, n)
    
    # Collect distance pairs
    euclidean_dists = []
    graph_dists = []
    
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:  # Connected
                e_dist = euclidean_distance_periodic(defects[i], defects[j], size)
                g_dist = graph_dist[i, j]
                euclidean_dists.append(e_dist)
                graph_dists.append(g_dist)
    
    if len(euclidean_dists) < 10:
        return {'pearson_r': 0, 'spearman_r': 0, 'n_pairs': len(euclidean_dists), 'valid': False}
    
    euclidean_dists = np.array(euclidean_dists)
    graph_dists = np.array(graph_dists)
    
    # Compute correlations
    pearson_r, pearson_p = pearsonr(euclidean_dists, graph_dists)
    spearman_r, spearman_p = spearmanr(euclidean_dists, graph_dists)
    
    # Bin analysis: mean graph distance in Euclidean distance bins
    bins = np.linspace(0, size/2, 8)
    binned_means = []
    bin_centers = []
    
    for i in range(len(bins) - 1):
        mask = (euclidean_dists >= bins[i]) & (euclidean_dists < bins[i+1])
        if np.sum(mask) > 5:
            binned_means.append(np.mean(graph_dists[mask]))
            bin_centers.append((bins[i] + bins[i+1]) / 2)
    
    # Check monotonicity
    monotonic = True
    if len(binned_means) >= 3:
        for i in range(len(binned_means) - 1):
            if binned_means[i+1] < binned_means[i] * 0.9:  # Allow 10% noise
                monotonic = False
                break
    
    return {
        'pearson_r': pearson_r,
        'pearson_p': pearson_p,
        'spearman_r': spearman_r,
        'spearman_p': spearman_p,
        'n_pairs': len(euclidean_dists),
        'bin_centers': bin_centers,
        'binned_means': binned_means,
        'monotonic': monotonic,
        'valid': True,
    }


def test_neighborhood_scaling(defects: List[Tuple], adj: Dict[int, Set[int]], max_radius: int = 6) -> Dict:
    """
    TEST 2: Neighborhood growth scaling.
    In d dimensions, N(r) ~ r^d for small r.
    """
    n = len(defects)
    if n < 10:
        return {'scaling_exponent': 0, 'valid': False}
    
    graph_dist = compute_graph_distances(adj, n)
    
    # For each node, count neighbors within graph radius r
    radii = list(range(1, max_radius + 1))
    mean_counts = []
    
    for r in radii:
        counts = []
        for i in range(n):
            count = np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0))
            counts.append(count)
        mean_counts.append(np.mean(counts))
    
    # Fit power law: N(r) ~ r^d
    # log(N) = d * log(r) + const
    log_r = np.log(radii)
    log_n = np.log(np.array(mean_counts) + 1)  # +1 to avoid log(0)
    
    if len(log_r) >= 3:
        # Linear regression
        coeffs = np.polyfit(log_r, log_n, 1)
        scaling_exponent = coeffs[0]
        
        # Compute fit quality (R²)
        fit = np.polyval(coeffs, log_r)
        ss_res = np.sum((log_n - fit)**2)
        ss_tot = np.sum((log_n - np.mean(log_n))**2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    else:
        scaling_exponent = 0
        r_squared = 0
    
    return {
        'radii': radii,
        'mean_counts': mean_counts,
        'scaling_exponent': scaling_exponent,
        'r_squared': r_squared,
        'valid': len(radii) >= 3,
    }


def test_locality(defects: List[Tuple], adj: Dict[int, Set[int]], size: int) -> Dict:
    """
    TEST 3: Locality consistency.
    Are graph neighbors spatially nearby? Are there long-range shortcuts?
    """
    n = len(defects)
    if n < 10:
        return {'mean_neighbor_dist': 0, 'valid': False}
    
    neighbor_distances = []
    non_neighbor_distances = []
    
    for i in range(n):
        for j in range(i + 1, n):
            e_dist = euclidean_distance_periodic(defects[i], defects[j], size)
            
            if j in adj[i]:  # Graph neighbors
                neighbor_distances.append(e_dist)
            else:
                non_neighbor_distances.append(e_dist)
    
    if not neighbor_distances:
        return {'mean_neighbor_dist': 0, 'valid': False}
    
    mean_neighbor_dist = np.mean(neighbor_distances)
    mean_non_neighbor_dist = np.mean(non_neighbor_distances) if non_neighbor_distances else np.inf
    
    # Count "long-range" shortcuts (neighbors more than 2× interaction radius apart)
    interaction_radius = 10.0
    long_range_count = sum(1 for d in neighbor_distances if d > 2 * interaction_radius)
    long_range_fraction = long_range_count / len(neighbor_distances)
    
    # Locality ratio: how much closer are neighbors than non-neighbors?
    locality_ratio = mean_non_neighbor_dist / mean_neighbor_dist if mean_neighbor_dist > 0 else 0
    
    return {
        'mean_neighbor_dist': mean_neighbor_dist,
        'std_neighbor_dist': np.std(neighbor_distances),
        'mean_non_neighbor_dist': mean_non_neighbor_dist,
        'locality_ratio': locality_ratio,
        'long_range_fraction': long_range_fraction,
        'n_edges': len(neighbor_distances),
        'valid': True,
    }


def test_coarse_grained_stability(defects: List[Tuple], adj: Dict[int, Set[int]], size: int) -> Dict:
    """
    TEST 4: Does distance structure survive coarse-graining?
    Merge nearby nodes and check if correlations persist.
    """
    n = len(defects)
    if n < 15:
        return {'coarse_pearson_r': 0, 'valid': False}
    
    # Coarse-grain: merge nodes within distance 8
    merge_radius = 8
    
    # Assign nodes to clusters
    visited = set()
    clusters = []
    
    for i in range(n):
        if i in visited:
            continue
        
        cluster = [i]
        visited.add(i)
        
        for j in range(n):
            if j in visited:
                continue
            if euclidean_distance_periodic(defects[i], defects[j], size) < merge_radius:
                cluster.append(j)
                visited.add(j)
        
        clusters.append(cluster)
    
    if len(clusters) < 5:
        return {'coarse_pearson_r': 0, 'n_clusters': len(clusters), 'valid': False}
    
    # Compute cluster centroids
    centroids = []
    for cluster in clusters:
        cx = np.mean([defects[i][0] for i in cluster])
        cy = np.mean([defects[i][1] for i in cluster])
        cz = np.mean([defects[i][2] for i in cluster])
        centroids.append((cx, cy, cz))
    
    # Compute coarse-grained graph distances
    # Two clusters are connected if any of their members are connected
    coarse_adj = defaultdict(set)
    for ci, c1 in enumerate(clusters):
        for cj, c2 in enumerate(clusters):
            if ci >= cj:
                continue
            # Check if any nodes in c1 connect to any in c2
            connected = False
            for i in c1:
                for j in c2:
                    if j in adj[i]:
                        connected = True
                        break
                if connected:
                    break
            if connected:
                coarse_adj[ci].add(cj)
                coarse_adj[cj].add(ci)
    
    coarse_graph_dist = compute_graph_distances(coarse_adj, len(clusters))
    
    # Compute correlation at coarse level
    euclidean_dists = []
    graph_dists = []
    
    for ci in range(len(clusters)):
        for cj in range(ci + 1, len(clusters)):
            if coarse_graph_dist[ci, cj] < np.inf:
                e_dist = euclidean_distance_periodic(centroids[ci], centroids[cj], size)
                g_dist = coarse_graph_dist[ci, cj]
                euclidean_dists.append(e_dist)
                graph_dists.append(g_dist)
    
    if len(euclidean_dists) < 5:
        return {'coarse_pearson_r': 0, 'n_clusters': len(clusters), 'valid': False}
    
    coarse_pearson_r, _ = pearsonr(euclidean_dists, graph_dists)
    
    return {
        'n_clusters': len(clusters),
        'coarse_pearson_r': coarse_pearson_r,
        'n_coarse_pairs': len(euclidean_dists),
        'valid': True,
    }


def run_gate_1_test():
    """
    Phase 7, Gate 1: Test for metric-like properties.
    """
    print("=" * 70)
    print("PHASE 7, GATE 1: METRIC-LIKE PROPERTIES")
    print("=" * 70)
    print()
    print("Central Question: Does relational distance encode spatial distance?")
    print()
    
    # Setup simulation
    sim = MetricTestSimulator(size=48, coupling_center=0.7, coupling_edge=0.2)
    np.random.seed(42)
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    
    # Inject vortices
    center = sim.size // 2
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) + abs(j) <= 3:
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    print("Equilibrating (800 steps)...")
    for _ in range(800):
        sim.step()
    
    print("Collecting data (1000 steps)...")
    
    # Collect multiple snapshots for robustness
    all_results = {
        'distance_corr': [],
        'scaling': [],
        'locality': [],
        'coarse': [],
    }
    
    for step in range(1000):
        sim.step()
        
        if step % 100 == 0:
            defects = sim.detect_defects()
            if len(defects) >= 15:
                adj = build_adjacency_graph(defects, sim.size, radius=10.0)
                
                all_results['distance_corr'].append(
                    test_distance_correlation(defects, adj, sim.size)
                )
                all_results['scaling'].append(
                    test_neighborhood_scaling(defects, adj)
                )
                all_results['locality'].append(
                    test_locality(defects, adj, sim.size)
                )
                all_results['coarse'].append(
                    test_coarse_grained_stability(defects, adj, sim.size)
                )
            
            if step % 200 == 0:
                print(f"  Step {step}: {len(defects)} defects")
    
    print()
    
    # TEST 1: Distance Correlation
    print("-" * 70)
    print("TEST 1: GRAPH DISTANCE vs EUCLIDEAN DISTANCE")
    print("-" * 70)
    print()
    
    valid_corr = [r for r in all_results['distance_corr'] if r.get('valid', False)]
    
    if valid_corr:
        mean_pearson = np.mean([r['pearson_r'] for r in valid_corr])
        mean_spearman = np.mean([r['spearman_r'] for r in valid_corr])
        n_monotonic = sum(1 for r in valid_corr if r['monotonic'])
        
        print(f"Samples: {len(valid_corr)}")
        print(f"Mean Pearson r: {mean_pearson:.3f}")
        print(f"Mean Spearman r: {mean_spearman:.3f}")
        print(f"Monotonic samples: {n_monotonic}/{len(valid_corr)}")
        
        # Show binned relationship from last sample
        if valid_corr[-1]['bin_centers']:
            print("\nBinned graph distance vs Euclidean distance:")
            for bc, bm in zip(valid_corr[-1]['bin_centers'], valid_corr[-1]['binned_means']):
                print(f"  Euclidean {bc:.0f}: mean graph dist = {bm:.2f}")
    else:
        print("Insufficient data for distance correlation")
        mean_pearson = 0
        mean_spearman = 0
    
    # TEST 2: Neighborhood Scaling
    print()
    print("-" * 70)
    print("TEST 2: NEIGHBORHOOD GROWTH SCALING")
    print("-" * 70)
    print()
    
    valid_scaling = [r for r in all_results['scaling'] if r.get('valid', False)]
    
    if valid_scaling:
        mean_exponent = np.mean([r['scaling_exponent'] for r in valid_scaling])
        mean_r2 = np.mean([r['r_squared'] for r in valid_scaling])
        
        print(f"Mean scaling exponent: {mean_exponent:.2f}")
        print(f"Mean R² of fit: {mean_r2:.3f}")
        print()
        print(f"Interpretation:")
        print(f"  Exponent ~1 → 1D-like growth")
        print(f"  Exponent ~2 → 2D-like growth")
        print(f"  Exponent ~3 → 3D-like growth")
        print(f"  Observed: {mean_exponent:.2f} → ~{int(round(mean_exponent))}D-like")
        
        # Show growth curve from last sample
        if valid_scaling[-1]['radii']:
            print("\nNeighborhood growth N(r):")
            for r, n in zip(valid_scaling[-1]['radii'], valid_scaling[-1]['mean_counts']):
                print(f"  r={r}: N={n:.1f}")
    else:
        print("Insufficient data for scaling analysis")
        mean_exponent = 0
    
    # TEST 3: Locality
    print()
    print("-" * 70)
    print("TEST 3: LOCALITY CONSISTENCY")
    print("-" * 70)
    print()
    
    valid_locality = [r for r in all_results['locality'] if r.get('valid', False)]
    
    if valid_locality:
        mean_neighbor_dist = np.mean([r['mean_neighbor_dist'] for r in valid_locality])
        mean_locality_ratio = np.mean([r['locality_ratio'] for r in valid_locality])
        mean_long_range = np.mean([r['long_range_fraction'] for r in valid_locality])
        
        print(f"Mean neighbor Euclidean distance: {mean_neighbor_dist:.2f}")
        print(f"Locality ratio (non-neighbor/neighbor): {mean_locality_ratio:.2f}×")
        print(f"Long-range edge fraction: {mean_long_range:.1%}")
        print()
        print(f"Interpretation:")
        if mean_long_range < 0.05:
            print(f"  Strong locality: edges are almost all short-range")
        elif mean_long_range < 0.15:
            print(f"  Moderate locality: mostly short-range with some shortcuts")
        else:
            print(f"  Weak locality: many long-range connections")
    else:
        print("Insufficient data for locality analysis")
        mean_locality_ratio = 0
        mean_long_range = 1
    
    # TEST 4: Coarse-Grained Stability
    print()
    print("-" * 70)
    print("TEST 4: COARSE-GRAINED STABILITY")
    print("-" * 70)
    print()
    
    valid_coarse = [r for r in all_results['coarse'] if r.get('valid', False)]
    
    if valid_coarse:
        mean_coarse_r = np.mean([r['coarse_pearson_r'] for r in valid_coarse])
        mean_n_clusters = np.mean([r['n_clusters'] for r in valid_coarse])
        
        print(f"Mean clusters after coarse-graining: {mean_n_clusters:.1f}")
        print(f"Coarse-grained Pearson r: {mean_coarse_r:.3f}")
        print()
        print(f"Interpretation:")
        if mean_coarse_r > 0.5:
            print(f"  Strong: distance structure survives coarse-graining")
        elif mean_coarse_r > 0.3:
            print(f"  Moderate: partial survival under coarse-graining")
        else:
            print(f"  Weak: structure does not survive coarse-graining well")
    else:
        print("Insufficient data for coarse-graining analysis")
        mean_coarse_r = 0
    
    # Summary
    print()
    print("=" * 70)
    print("GATE 1 ASSESSMENT")
    print("=" * 70)
    print()
    
    evidence_for = []
    evidence_against = []
    
    # Distance correlation
    if mean_pearson > 0.5:
        evidence_for.append(f"Strong distance correlation (r={mean_pearson:.2f})")
    elif mean_pearson > 0.3:
        evidence_for.append(f"Moderate distance correlation (r={mean_pearson:.2f})")
    elif mean_pearson > 0.1:
        evidence_against.append(f"Weak distance correlation (r={mean_pearson:.2f})")
    else:
        evidence_against.append(f"No meaningful distance correlation (r={mean_pearson:.2f})")
    
    # Scaling
    if valid_scaling and mean_exponent > 1.5 and mean_exponent < 4:
        evidence_for.append(f"Consistent dimension-like scaling (d≈{mean_exponent:.1f})")
    elif valid_scaling:
        evidence_against.append(f"Anomalous scaling exponent (d={mean_exponent:.1f})")
    
    # Locality
    if mean_long_range < 0.1:
        evidence_for.append(f"Strong locality ({mean_long_range:.0%} long-range)")
    elif mean_long_range < 0.2:
        evidence_for.append(f"Moderate locality ({mean_long_range:.0%} long-range)")
    else:
        evidence_against.append(f"Weak locality ({mean_long_range:.0%} long-range)")
    
    # Coarse-graining
    if mean_coarse_r > 0.4:
        evidence_for.append(f"Coarse-graining stable (r={mean_coarse_r:.2f})")
    elif mean_coarse_r > 0.2:
        evidence_for.append(f"Partial coarse-graining stability (r={mean_coarse_r:.2f})")
    else:
        evidence_against.append(f"Unstable under coarse-graining (r={mean_coarse_r:.2f})")
    
    print("EVIDENCE FOR METRIC-LIKE STRUCTURE:")
    if evidence_for:
        for e in evidence_for:
            print(f"  + {e}")
    else:
        print("  (none)")
    
    print()
    print("EVIDENCE AGAINST:")
    if evidence_against:
        for e in evidence_against:
            print(f"  - {e}")
    else:
        print("  (none)")
    
    print()
    if len(evidence_for) >= 3 and mean_pearson > 0.3:
        print("GATE 1 RESULT: STRONG EVIDENCE FOR METRIC-LIKE PROPERTIES")
        print("  Relational distance encodes spatial distance with consistent scaling")
    elif len(evidence_for) >= 2:
        print("GATE 1 RESULT: MODERATE EVIDENCE FOR METRIC-LIKE PROPERTIES")
        print("  Some metric-like behavior, but not fully geometric")
    else:
        print("GATE 1 RESULT: LIMITED METRIC-LIKE PROPERTIES")
        print("  Relational structure does not yet behave like a geometry")
    
    return {
        'mean_pearson': mean_pearson,
        'mean_spearman': mean_spearman,
        'mean_scaling_exponent': mean_exponent if valid_scaling else 0,
        'mean_locality_ratio': mean_locality_ratio if valid_locality else 0,
        'mean_coarse_r': mean_coarse_r if valid_coarse else 0,
        'evidence_for': evidence_for,
        'evidence_against': evidence_against,
    }


if __name__ == "__main__":
    results = run_gate_1_test()
