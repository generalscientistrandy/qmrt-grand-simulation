"""
Phase 8 Diagnostic: What Caused the +0.16 Dimension Increase?

The cross-link mechanism increased dimension from 1.18 to 1.33,
but created 0 actual cross-links. This script diagnoses the real cause.

Key metrics to compare (baseline vs strength=1.0):
1. Edge count / density
2. Component count  
3. Mean path length
4. Mean Euclidean edge length
5. Degree distribution
6. Community structure
7. Spatial filling fraction
8. Graph-Euclidean distance relationship
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque, Counter
from typing import Dict, List, Tuple
import time


class DiagnosticSimulator:
    """Same as CrossLinkSimulator for consistent comparison."""
    
    def __init__(self, size: int = 48, cross_link_strength: float = 0.0):
        self.size = size
        self.cross_link_strength = cross_link_strength
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
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
                        coupling[i, j, k] = 0.7
                    elif dist >= interior_r + transition_width:
                        coupling[i, j, k] = 0.2
                    else:
                        t = (dist - interior_r) / transition_width
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = 0.7 + blend * (0.2 - 0.7)
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
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        self.remnant_field += 0.005 * (topology_norm - 0.3 * self.remnant_field)
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        if self.cross_link_strength > 0:
            topo_x = np.abs(grad_x)
            topo_y = np.abs(grad_y)
            topo_z = np.abs(grad_z)
            directional_spread = np.minimum(topo_x, topo_y) + np.minimum(topo_y, topo_z) + np.minimum(topo_x, topo_z)
            directional_spread = gaussian_filter(directional_spread, sigma=2.0)
            directional_spread = directional_spread / (np.max(directional_spread) + 1e-10)
            self.cross_link_field += 0.02 * (directional_spread - 0.2 * self.cross_link_field)
            self.cross_link_field = np.clip(self.cross_link_field, 0, 1)
        
        protection = topology_norm * self.channel_assignment
        
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


def find_connected_components(adj: Dict[int, set], n: int) -> List[set]:
    """Find all connected components."""
    visited = set()
    components = []
    
    for start in range(n):
        if start in visited:
            continue
        component = set()
        queue = deque([start])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)
    
    return components


def comprehensive_diagnostic(defects: List[Tuple], size: int) -> Dict:
    """Compute comprehensive diagnostic metrics."""
    n = len(defects)
    if n < 10:
        return {'valid': False}
    
    adj = build_adjacency(defects, size, radius=10.0)
    graph_dist = compute_graph_distances(adj, n)
    
    # 1. Basic counts
    total_edges = sum(len(adj[i]) for i in range(n)) // 2
    density = total_edges / (n * (n - 1) / 2) if n > 1 else 0
    
    # 2. Connected components
    components = find_connected_components(adj, n)
    n_components = len(components)
    largest_component_size = max(len(c) for c in components) if components else 0
    
    # 3. Degree distribution
    degrees = [len(adj[i]) for i in range(n)]
    mean_degree = np.mean(degrees)
    max_degree = max(degrees) if degrees else 0
    degree_variance = np.var(degrees) if degrees else 0
    
    # 4. Path lengths (within largest component)
    largest_component = max(components, key=len) if components else set()
    path_lengths = []
    for i in largest_component:
        for j in largest_component:
            if i < j and graph_dist[i, j] < np.inf:
                path_lengths.append(graph_dist[i, j])
    
    mean_path_length = np.mean(path_lengths) if path_lengths else 0
    max_path_length = max(path_lengths) if path_lengths else 0
    
    # 5. Euclidean edge lengths
    euclidean_edge_lengths = []
    for i in range(n):
        for j in adj[i]:
            if i < j:
                euclidean_edge_lengths.append(
                    euclidean_distance_periodic(defects[i], defects[j], size)
                )
    
    mean_edge_length = np.mean(euclidean_edge_lengths) if euclidean_edge_lengths else 0
    
    # 6. Graph-Euclidean relationship
    euclidean_dists = []
    graph_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(defects[i], defects[j], size))
                graph_dists.append(graph_dist[i, j])
    
    if len(euclidean_dists) >= 10:
        pearson_r, _ = pearsonr(euclidean_dists, graph_dists)
        # Linear fit: graph_dist = slope * euclidean_dist + intercept
        slope, intercept = np.polyfit(euclidean_dists, graph_dists, 1)
    else:
        pearson_r = 0
        slope = 0
        intercept = 0
    
    # 7. Effective dimension
    radii = list(range(1, 7))
    mean_counts = []
    for r in radii:
        counts = [np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0)) for i in range(n)]
        mean_counts.append(np.mean(counts))
    
    log_r = np.log(radii)
    log_n = np.log(np.array(mean_counts) + 1)
    coeffs = np.polyfit(log_r, log_n, 1)
    effective_dimension = coeffs[0]
    
    # 8. Triangles
    triangles = 0
    for node in range(n):
        neighbors = list(adj[node])
        for i_idx in range(len(neighbors)):
            for j_idx in range(i_idx + 1, len(neighbors)):
                if neighbors[j_idx] in adj[neighbors[i_idx]]:
                    triangles += 1
    triangles //= 3
    
    # 9. Spatial spread (how spread out are the defects?)
    positions = np.array(defects)
    centroid = np.mean(positions, axis=0)
    radial_distances = [np.sqrt(np.sum((p - centroid)**2)) for p in positions]
    mean_radial_dist = np.mean(radial_distances)
    std_radial_dist = np.std(radial_distances)
    
    # 10. Filling fraction (coarse-grained)
    # Divide space into 8x8x8 cells, count occupied cells
    cell_size = size // 8
    occupied_cells = set()
    for p in defects:
        cell = (int(p[0] // cell_size), int(p[1] // cell_size), int(p[2] // cell_size))
        occupied_cells.add(cell)
    filling_fraction = len(occupied_cells) / (8 * 8 * 8)
    
    # 11. Nearest neighbor distances
    nn_distances = []
    for i in range(n):
        min_dist = float('inf')
        for j in range(n):
            if i != j:
                d = euclidean_distance_periodic(defects[i], defects[j], size)
                if d < min_dist:
                    min_dist = d
        if min_dist < float('inf'):
            nn_distances.append(min_dist)
    
    mean_nn_distance = np.mean(nn_distances) if nn_distances else 0
    
    return {
        'valid': True,
        'n_defects': n,
        'total_edges': total_edges,
        'density': density,
        'n_components': n_components,
        'largest_component_size': largest_component_size,
        'mean_degree': mean_degree,
        'max_degree': max_degree,
        'degree_variance': degree_variance,
        'mean_path_length': mean_path_length,
        'max_path_length': max_path_length,
        'mean_edge_length': mean_edge_length,
        'pearson_r': pearson_r,
        'graph_euclidean_slope': slope,
        'effective_dimension': effective_dimension,
        'triangles': triangles,
        'mean_radial_dist': mean_radial_dist,
        'std_radial_dist': std_radial_dist,
        'filling_fraction': filling_fraction,
        'mean_nn_distance': mean_nn_distance,
    }


def run_diagnostic(strength: float, name: str) -> Dict:
    """Run simulation and collect diagnostic metrics."""
    print(f"\n  Running: {name} (strength={strength})")
    
    sim = DiagnosticSimulator(size=48, cross_link_strength=strength)
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    print(f"    Equilibrating...", end=" ", flush=True)
    for _ in range(800):
        sim.step()
    print("done")
    
    print(f"    Measuring...", end=" ", flush=True)
    all_metrics = []
    for step in range(500):
        sim.step()
        if step % 50 == 0:
            defects = sim.detect_defects()
            metrics = comprehensive_diagnostic(defects, sim.size)
            if metrics['valid']:
                all_metrics.append(metrics)
                print(".", end="", flush=True)
    print()
    
    if not all_metrics:
        return {'valid': False, 'name': name}
    
    # Aggregate all metrics
    keys = [k for k in all_metrics[0].keys() if k not in ['valid']]
    aggregated = {'valid': True, 'name': name, 'strength': strength, 'n_samples': len(all_metrics)}
    
    for key in keys:
        vals = [m[key] for m in all_metrics]
        aggregated[f'mean_{key}'] = np.mean(vals)
        aggregated[f'std_{key}'] = np.std(vals)
    
    return aggregated


def run_causal_audit():
    """
    Compare baseline vs strength=1.0 to diagnose dimension increase cause.
    """
    print("=" * 70)
    print("PHASE 8 DIAGNOSTIC: CAUSAL AUDIT")
    print("=" * 70)
    print()
    print("Question: What actually caused the +0.16 dimension increase?")
    print()
    
    baseline = run_diagnostic(0.0, "Baseline")
    high_strength = run_diagnostic(1.0, "High Strength")
    
    print()
    print("=" * 70)
    print("COMPARISON: BASELINE vs HIGH STRENGTH")
    print("=" * 70)
    print()
    
    # Key metrics to compare
    metrics = [
        ('mean_n_defects', 'Defect count'),
        ('mean_total_edges', 'Edge count'),
        ('mean_density', 'Graph density'),
        ('mean_n_components', 'Component count'),
        ('mean_largest_component_size', 'Largest component'),
        ('mean_mean_degree', 'Mean degree'),
        ('mean_max_degree', 'Max degree'),
        ('mean_degree_variance', 'Degree variance'),
        ('mean_mean_path_length', 'Mean path length'),
        ('mean_max_path_length', 'Max path length'),
        ('mean_mean_edge_length', 'Mean edge length'),
        ('mean_pearson_r', 'Graph-Euclidean r'),
        ('mean_graph_euclidean_slope', 'G-E slope'),
        ('mean_effective_dimension', 'Effective dim'),
        ('mean_triangles', 'Triangles'),
        ('mean_filling_fraction', 'Filling fraction'),
        ('mean_mean_nn_distance', 'Mean NN distance'),
        ('mean_mean_radial_dist', 'Radial spread'),
    ]
    
    print(f"{'Metric':<25} {'Baseline':>12} {'High':>12} {'Change':>12} {'%':>8}")
    print("-" * 70)
    
    for key, label in metrics:
        b_val = baseline.get(key, 0)
        h_val = high_strength.get(key, 0)
        change = h_val - b_val
        pct = (change / b_val * 100) if b_val != 0 else 0
        
        # Highlight significant changes
        marker = ""
        if abs(pct) > 20:
            marker = " **"
        elif abs(pct) > 10:
            marker = " *"
        
        print(f"{label:<25} {b_val:>12.3f} {h_val:>12.3f} {change:>+12.3f} {pct:>+7.1f}%{marker}")
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    print()
    
    # Check key hypotheses
    b_edges = baseline.get('mean_total_edges', 0)
    h_edges = high_strength.get('mean_total_edges', 0)
    edge_change = (h_edges - b_edges) / b_edges * 100 if b_edges > 0 else 0
    
    b_tri = baseline.get('mean_triangles', 0)
    h_tri = high_strength.get('mean_triangles', 0)
    tri_change = (h_tri - b_tri) / b_tri * 100 if b_tri > 0 else 0
    
    b_dim = baseline.get('mean_effective_dimension', 0)
    h_dim = high_strength.get('mean_effective_dimension', 0)
    
    b_path = baseline.get('mean_mean_path_length', 0)
    h_path = high_strength.get('mean_mean_path_length', 0)
    
    b_fill = baseline.get('mean_filling_fraction', 0)
    h_fill = high_strength.get('mean_filling_fraction', 0)
    
    b_nn = baseline.get('mean_mean_nn_distance', 0)
    h_nn = high_strength.get('mean_mean_nn_distance', 0)
    
    print("Hypothesis 1: Sparser network → appears more space-filling?")
    print(f"  Edge count: {b_edges:.0f} → {h_edges:.0f} ({edge_change:+.1f}%)")
    print(f"  Triangle count: {b_tri:.0f} → {h_tri:.0f} ({tri_change:+.1f}%)")
    if edge_change < -10 and tri_change < -20:
        print("  → SUPPORTED: Network became sparser")
    else:
        print("  → NOT SUPPORTED")
    
    print()
    print("Hypothesis 2: Longer paths → higher effective dimension?")
    path_change = (h_path - b_path) / b_path * 100 if b_path > 0 else 0
    print(f"  Mean path length: {b_path:.2f} → {h_path:.2f} ({path_change:+.1f}%)")
    if path_change > 10:
        print("  → SUPPORTED: Paths got longer")
    else:
        print("  → NOT SUPPORTED")
    
    print()
    print("Hypothesis 3: More spatially spread → higher dimension?")
    fill_change = (h_fill - b_fill) / b_fill * 100 if b_fill > 0 else 0
    nn_change = (h_nn - b_nn) / b_nn * 100 if b_nn > 0 else 0
    print(f"  Filling fraction: {b_fill:.3f} → {h_fill:.3f} ({fill_change:+.1f}%)")
    print(f"  Mean NN distance: {b_nn:.2f} → {h_nn:.2f} ({nn_change:+.1f}%)")
    if fill_change > 5 or nn_change > 5:
        print("  → SUPPORTED: Network more spatially spread")
    else:
        print("  → NOT SUPPORTED")
    
    print()
    print("Hypothesis 4: Dimension estimator artifact?")
    slope_b = baseline.get('mean_graph_euclidean_slope', 0)
    slope_h = high_strength.get('mean_graph_euclidean_slope', 0)
    slope_change = (slope_h - slope_b) / slope_b * 100 if slope_b > 0 else 0
    print(f"  Graph-Euclidean slope: {slope_b:.3f} → {slope_h:.3f} ({slope_change:+.1f}%)")
    print(f"  If slope decreased, graph distances grew faster relative to Euclidean")
    
    # Verdict
    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    print()
    
    if edge_change < -15 and tri_change < -30:
        print("PRIMARY CAUSE: Network became SPARSER and LESS LOCALLY CONNECTED")
        print()
        print("The dimension increase is NOT a true 2D enrichment.")
        print("It appears to be an artifact of:")
        print("  - Fewer edges → graph distances scale differently")
        print("  - Fewer triangles → less local clustering")
        print("  - Same spatial extent with fewer connections")
        print()
        print("The 'cross-link field' is actually suppressing local structure,")
        print("making the network more diffuse, which inflates the dimension estimate.")
    else:
        print("CAUSE UNCLEAR - needs further investigation")
    
    return {'baseline': baseline, 'high_strength': high_strength}


if __name__ == "__main__":
    results = run_causal_audit()
