"""
Phase 8, Gate 2: Loop/Motif Stabilization
==========================================

Central Question: Can stabilizing closed local motifs (triangles) raise
effective dimension while INCREASING local structure?

Gate 1 diagnostic showed:
- The cross-link mechanism created SPARSER networks
- Dimension increase was an artifact of diffuse structure
- True 2D enrichment requires MORE local structure, not less

Gate 2 design principle:
- Directly reward defects that participate in TRIANGLES
- These defects get additional protection
- Should increase: triangle count, edges, clustering
- Should not degrade: graph-Euclidean correlation

The mechanism:
1. Detect low-amplitude regions (potential defects)
2. For each potential defect location, check if it would form triangles
   with nearby existing topological features
3. Provide extra protection to defects that are part of triangular configurations

Success criteria:
- Triangle count INCREASES
- Edge count INCREASES or stays constant
- Effective dimension rises WITH richer local structure
- Graph-Euclidean correlation maintained
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import time


class LoopStabilizationSimulator:
    """
    Simulator with loop/motif stabilization layer.
    
    The loop layer works by:
    1. Tracking local topological structure
    2. Identifying regions where triangular configurations exist
    3. Providing additional protection for defects in those regions
    """
    
    def __init__(
        self,
        size: int = 48,
        loop_strength: float = 0.0,  # 0 = baseline, >0 = loop reward
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
    ):
        self.size = size
        self.loop_strength = loop_strength
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
        
        # NEW: Loop coherence field
        # This field is high where local triangular structure exists
        self.loop_field = np.zeros((size, size, size))
        
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
    
    def _compute_loop_field(self, topology_norm: np.ndarray) -> np.ndarray:
        """
        Compute the loop coherence field (optimized version).
        
        Strategy: Use Gaussian blur to efficiently count nearby high-topology regions.
        Points with topology AND multiple nearby topology neighbors get high loop field.
        """
        # Threshold for "significant topology"
        topo_thresh = 0.3
        high_topo = (topology_norm > topo_thresh).astype(float)
        
        # Use Gaussian blur to efficiently count nearby high-topology neighbors
        # Sigma=3 gives effective radius ~9 (3*sigma) which covers potential triangle partners
        neighbor_density = gaussian_filter(high_topo, sigma=3.0)
        
        # Normalize
        max_density = neighbor_density.max() + 1e-10
        neighbor_density = neighbor_density / max_density
        
        # Loop field is high where:
        # 1. This point has topology (is a defect)
        # 2. AND there are multiple nearby high-topology neighbors (potential triangle)
        multi_neighbor = (neighbor_density > 0.2)  # Require substantial neighbors
        
        loop_field = topology_norm * multi_neighbor.astype(float) * neighbor_density
        
        # Smooth slightly
        loop_field = gaussian_filter(loop_field, sigma=1.0)
        
        return loop_field
    
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
        
        # NEW: Loop field computation and update
        if self.loop_strength > 0:
            current_loop = self._compute_loop_field(topology_norm)
            # Loop field builds up where triangular configurations exist
            self.loop_field += 0.02 * (current_loop - 0.1 * self.loop_field)
            self.loop_field = np.clip(self.loop_field, 0, 1)
        
        # Protection mechanism (standard + loop enhancement)
        protection = topology_norm * self.channel_assignment
        
        # NEW: Loop enhancement to protection
        # Defects in loop regions (triangular configurations) get additional protection
        if self.loop_strength > 0:
            loop_boost = self.loop_strength * self.loop_field
            protection = protection + loop_boost * topology_norm
        
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


def comprehensive_metrics(defects: List[Tuple], size: int) -> Dict:
    """Compute all diagnostic metrics."""
    n = len(defects)
    if n < 10:
        return {'valid': False}
    
    adj = build_adjacency(defects, size, radius=10.0)
    graph_dist = compute_graph_distances(adj, n)
    
    # Edge count
    total_edges = sum(len(adj[i]) for i in range(n)) // 2
    
    # Degrees
    degrees = [len(adj[i]) for i in range(n)]
    mean_degree = np.mean(degrees)
    
    # Triangles
    triangles = 0
    for node in range(n):
        neighbors = list(adj[node])
        for i_idx in range(len(neighbors)):
            for j_idx in range(i_idx + 1, len(neighbors)):
                if neighbors[j_idx] in adj[neighbors[i_idx]]:
                    triangles += 1
    triangles //= 3
    
    # Clustering coefficient
    clustering_sum = 0
    clustering_count = 0
    for node in range(n):
        neighbors = list(adj[node])
        k = len(neighbors)
        if k >= 2:
            local_tri = 0
            for i_idx in range(len(neighbors)):
                for j_idx in range(i_idx + 1, len(neighbors)):
                    if neighbors[j_idx] in adj[neighbors[i_idx]]:
                        local_tri += 1
            max_tri = k * (k - 1) / 2
            clustering_sum += local_tri / max_tri
            clustering_count += 1
    avg_clustering = clustering_sum / clustering_count if clustering_count > 0 else 0
    
    # Graph-Euclidean correlation
    euclidean_dists = []
    graph_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(defects[i], defects[j], size))
                graph_dists.append(graph_dist[i, j])
    
    if len(euclidean_dists) >= 10:
        pearson_r, _ = pearsonr(euclidean_dists, graph_dists)
    else:
        pearson_r = 0
    
    # Effective dimension
    radii = list(range(1, 7))
    mean_counts = []
    for r in radii:
        counts = [np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0)) for i in range(n)]
        mean_counts.append(np.mean(counts))
    
    log_r = np.log(radii)
    log_n = np.log(np.array(mean_counts) + 1)
    coeffs = np.polyfit(log_r, log_n, 1)
    effective_dimension = coeffs[0]
    
    # Path length
    path_lengths = []
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:
                path_lengths.append(graph_dist[i, j])
    mean_path_length = np.mean(path_lengths) if path_lengths else 0
    
    # NN distance
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
    
    # Filling fraction
    cell_size = size // 8
    occupied_cells = set()
    for p in defects:
        cell = (int(p[0] // cell_size), int(p[1] // cell_size), int(p[2] // cell_size))
        occupied_cells.add(cell)
    filling_fraction = len(occupied_cells) / (8 * 8 * 8)
    
    return {
        'valid': True,
        'n_defects': n,
        'total_edges': total_edges,
        'mean_degree': mean_degree,
        'triangles': triangles,
        'avg_clustering': avg_clustering,
        'pearson_r': pearson_r,
        'effective_dimension': effective_dimension,
        'mean_path_length': mean_path_length,
        'mean_nn_distance': mean_nn_distance,
        'filling_fraction': filling_fraction,
    }


def run_loop_test(loop_strength: float, name: str) -> Dict:
    """Run a single test with given loop strength."""
    print(f"\n  Test: {name} (strength={loop_strength})")
    
    sim = LoopStabilizationSimulator(size=48, loop_strength=loop_strength)
    
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
            metrics = comprehensive_metrics(defects, sim.size)
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
        'strength': loop_strength,
        'n_samples': len(all_metrics),
    }
    
    for key in all_metrics[0].keys():
        if key != 'valid':
            vals = [m[key] for m in all_metrics]
            result[f'mean_{key}'] = np.mean(vals)
            result[f'std_{key}'] = np.std(vals)
    
    print(f"    Result: d={result['mean_effective_dimension']:.2f}, "
          f"triangles={result['mean_triangles']:.0f}, "
          f"edges={result['mean_total_edges']:.0f}, "
          f"r={result['mean_pearson_r']:.3f}")
    
    return result


def run_phase8_gate2():
    """
    Phase 8 Gate 2: Test whether loop stabilization raises effective dimension
    while INCREASING local structure.
    """
    print("=" * 70)
    print("PHASE 8, GATE 2: LOOP/MOTIF STABILIZATION")
    print("=" * 70)
    print()
    print("Question: Can stabilizing triangular motifs raise dimension while")
    print("          INCREASING local structure (not decreasing it)?")
    print()
    print("Success criteria:")
    print("  - Triangle count INCREASES")
    print("  - Edge count INCREASES or stays constant")
    print("  - Graph-Euclidean correlation maintained")
    print("  - Effective dimension rises WITH richer structure")
    print()
    
    results = []
    
    # Test range of loop strengths (fewer tests for speed)
    strengths = [0.0, 0.5, 1.0, 1.5]
    
    print("-" * 70)
    print("TESTING LOOP STRENGTH GRADIENT")
    print("-" * 70)
    
    for strength in strengths:
        if strength == 0.0:
            name = "Baseline (no loop)"
        else:
            name = f"Loop {strength:.1f}"
        results.append(run_loop_test(strength, name))
    
    # Summary comparison
    print()
    print("=" * 70)
    print("PHASE 8 GATE 2 RESULTS SUMMARY")
    print("=" * 70)
    print()
    
    valid_results = [r for r in results if r['valid']]
    
    print(f"{'Strength':>8} {'Dim':>7} {'Triangles':>10} {'Edges':>8} {'Degree':>8} {'G-E r':>8} {'Cluster':>9}")
    print("-" * 70)
    
    for r in valid_results:
        print(f"{r['strength']:>8.1f} {r['mean_effective_dimension']:>7.2f} "
              f"{r['mean_triangles']:>10.0f} {r['mean_total_edges']:>8.0f} "
              f"{r['mean_mean_degree']:>8.1f} {r['mean_pearson_r']:>8.3f} "
              f"{r['mean_avg_clustering']:>9.3f}")
    
    # Causal analysis
    print()
    print("-" * 70)
    print("CAUSAL ANALYSIS: BASELINE vs BEST")
    print("-" * 70)
    print()
    
    if valid_results:
        baseline = valid_results[0]
        best_dim = max(valid_results, key=lambda x: x['mean_effective_dimension'])
        best_tri = max(valid_results, key=lambda x: x['mean_triangles'])
        
        # Compare baseline vs highest dimension
        def compare(b, h, metric, label):
            b_val = b.get(f'mean_{metric}', 0)
            h_val = h.get(f'mean_{metric}', 0)
            change = h_val - b_val
            pct = (change / b_val * 100) if b_val != 0 else 0
            marker = " **" if abs(pct) > 15 else " *" if abs(pct) > 8 else ""
            print(f"  {label:<20} {b_val:>10.2f} → {h_val:>10.2f} ({pct:>+6.1f}%){marker}")
        
        print(f"Comparing: Baseline vs {best_dim['name']} (highest dimension)")
        print()
        compare(baseline, best_dim, 'effective_dimension', 'Dimension')
        compare(baseline, best_dim, 'triangles', 'Triangles')
        compare(baseline, best_dim, 'total_edges', 'Edges')
        compare(baseline, best_dim, 'mean_degree', 'Mean degree')
        compare(baseline, best_dim, 'pearson_r', 'Graph-Euclidean r')
        compare(baseline, best_dim, 'avg_clustering', 'Clustering')
        compare(baseline, best_dim, 'mean_path_length', 'Path length')
        
        # Check success criteria
        print()
        print("-" * 70)
        print("SUCCESS CRITERIA CHECK")
        print("-" * 70)
        print()
        
        b_tri = baseline['mean_triangles']
        h_tri = best_dim['mean_triangles']
        tri_increased = h_tri > b_tri
        
        b_edges = baseline['mean_total_edges']
        h_edges = best_dim['mean_total_edges']
        edges_maintained = h_edges >= b_edges * 0.9
        
        b_r = baseline['mean_pearson_r']
        h_r = best_dim['mean_pearson_r']
        correlation_maintained = h_r >= b_r * 0.85
        
        b_dim = baseline['mean_effective_dimension']
        h_dim = best_dim['mean_effective_dimension']
        dim_increased = h_dim > b_dim + 0.1
        
        print(f"✓ Triangle count increased: {'YES' if tri_increased else 'NO'} ({b_tri:.0f} → {h_tri:.0f})")
        print(f"✓ Edge count maintained: {'YES' if edges_maintained else 'NO'} ({b_edges:.0f} → {h_edges:.0f})")
        print(f"✓ G-E correlation maintained: {'YES' if correlation_maintained else 'NO'} ({b_r:.3f} → {h_r:.3f})")
        print(f"✓ Dimension increased: {'YES' if dim_increased else 'NO'} ({b_dim:.2f} → {h_dim:.2f})")
        
        all_criteria_met = tri_increased and edges_maintained and correlation_maintained and dim_increased
    
    # Gate assessment
    print()
    print("=" * 70)
    print("GATE 2 ASSESSMENT")
    print("=" * 70)
    print()
    
    if valid_results:
        if all_criteria_met:
            print("GATE 2 RESULT: SUCCESS — TRUE 2D ENRICHMENT")
            print("  Loop stabilization increased dimension WITH richer local structure")
            print("  This is a genuine dimensional breakthrough, not an artifact")
            print()
            print("  The recursive branching hypothesis is SUPPORTED:")
            print("  Stabilizing closed motifs can raise effective dimension")
        elif dim_increased and not tri_increased:
            print("GATE 2 RESULT: FALSE POSITIVE — SAME AS GATE 1")
            print("  Dimension increased but triangles decreased")
            print("  This is the same diffuse-network artifact")
        elif tri_increased and not dim_increased:
            print("GATE 2 RESULT: PARTIAL — LOCAL ENRICHMENT WITHOUT GLOBAL CHANGE")
            print("  Triangles increased but dimension unchanged")
            print("  Loop stabilization enriches locally but doesn't change global geometry")
        else:
            print("GATE 2 RESULT: NO EFFECT")
            print("  Loop stabilization had minimal impact")
            print("  The ~1D filamentary regime remains robust")
    
    return results


if __name__ == "__main__":
    results = run_phase8_gate2()
