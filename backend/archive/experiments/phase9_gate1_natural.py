"""
Phase 9, Gate 1: Long-Time Natural Dynamics
============================================

Core Question: Does the native filamentary regime remain static, or does it
accumulate higher-order structure along the scaffold over time?

This is OBSERVATIONAL science, not interventional:
- No promotion mechanisms
- No forcing
- Just watch what the medium naturally does over extended timescales

Metrics to track:
1. Effective dimension (does it drift?)
2. Motif counts (triangles, chains, hubs)
3. Hub persistence (do the same nodes stay highly connected?)
4. Community structure (do stable clusters form?)
5. Network statistics (degree distribution evolution)

Success criterion:
Not a breakthrough, but understanding:
- Is the scaffold static or slowly evolving?
- Does complexity accumulate without dimensional transition?
- What natural structures form along the filaments?
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque, Counter
from typing import Dict, List, Tuple, Set
import time


class NaturalDynamicsSimulator:
    """
    Standard simulator with NO promotion mechanisms.
    Pure natural dynamics for long-time observation.
    """
    
    def __init__(self, size: int = 48):
        self.size = size
        
        # Field state
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Standard layers only
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
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
        
        # Standard channel assignment
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        # Standard remnant field
        self.remnant_field += 0.005 * (topology_norm - 0.3 * self.remnant_field)
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        # Standard protection (NO extra mechanisms)
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


def measure_scaffold_state(defects: List[Tuple], size: int) -> Dict:
    """Comprehensive scaffold state measurement."""
    n = len(defects)
    if n < 10:
        return {'valid': False, 'n_defects': n}
    
    adj = build_adjacency(defects, size, radius=10.0)
    graph_dist = compute_graph_distances(adj, n)
    
    # Basic counts
    total_edges = sum(len(adj[i]) for i in range(n)) // 2
    degrees = [len(adj[i]) for i in range(n)]
    mean_degree = np.mean(degrees)
    max_degree = max(degrees) if degrees else 0
    
    # Degree distribution shape
    degree_counts = Counter(degrees)
    
    # Triangles
    triangles = 0
    for node in range(n):
        neighbors = list(adj[node])
        for i_idx in range(len(neighbors)):
            for j_idx in range(i_idx + 1, len(neighbors)):
                if neighbors[j_idx] in adj[neighbors[i_idx]]:
                    triangles += 1
    triangles //= 3
    
    # Clustering
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
    
    pearson_r = pearsonr(euclidean_dists, graph_dists)[0] if len(euclidean_dists) >= 10 else 0
    
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
    
    # Hub identification (top 10% by degree)
    degree_threshold = np.percentile(degrees, 90)
    hubs = [i for i in range(n) if degrees[i] >= degree_threshold]
    n_hubs = len(hubs)
    
    # Chain nodes (degree = 2, linear)
    chain_nodes = sum(1 for d in degrees if d == 2)
    chain_fraction = chain_nodes / n if n > 0 else 0
    
    # Leaf nodes (degree = 1)
    leaf_nodes = sum(1 for d in degrees if d == 1)
    leaf_fraction = leaf_nodes / n if n > 0 else 0
    
    # Junction nodes (degree >= 3)
    junction_nodes = sum(1 for d in degrees if d >= 3)
    junction_fraction = junction_nodes / n if n > 0 else 0
    
    return {
        'valid': True,
        'n_defects': n,
        'total_edges': total_edges,
        'mean_degree': mean_degree,
        'max_degree': max_degree,
        'triangles': triangles,
        'avg_clustering': avg_clustering,
        'pearson_r': pearson_r,
        'effective_dimension': effective_dimension,
        'n_hubs': n_hubs,
        'chain_fraction': chain_fraction,
        'leaf_fraction': leaf_fraction,
        'junction_fraction': junction_fraction,
    }


def run_long_time_observation():
    """
    Run extended natural dynamics and track scaffold evolution.
    """
    print("=" * 70)
    print("PHASE 9, GATE 1: LONG-TIME NATURAL DYNAMICS")
    print("=" * 70)
    print()
    print("Core question: Does the filamentary scaffold remain static or evolve?")
    print()
    print("This is OBSERVATIONAL - no promotion mechanisms, just watching.")
    print()
    
    sim = NaturalDynamicsSimulator(size=48)
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Inject vortices
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    # Equilibration
    print("-" * 70)
    print("EQUILIBRATION PHASE (800 steps)")
    print("-" * 70)
    print()
    
    for step in range(800):
        sim.step()
        if step % 200 == 0:
            defects = sim.detect_defects()
            print(f"  Step {step}: {len(defects)} defects")
    
    # Long-time observation in epochs
    print()
    print("-" * 70)
    print("LONG-TIME OBSERVATION (4 epochs × 500 steps)")
    print("-" * 70)
    print()
    
    epochs = []
    
    for epoch in range(4):
        print(f"Epoch {epoch + 1}:", end=" ", flush=True)
        epoch_metrics = []
        
        for step in range(500):
            sim.step()
            if step % 100 == 0:
                defects = sim.detect_defects()
                metrics = measure_scaffold_state(defects, sim.size)
                if metrics['valid']:
                    epoch_metrics.append(metrics)
                    print(".", end="", flush=True)
        
        if epoch_metrics:
            # Aggregate epoch
            aggregated = {
                'epoch': epoch + 1,
                'n_samples': len(epoch_metrics),
            }
            for key in epoch_metrics[0].keys():
                if key not in ['valid']:
                    vals = [m[key] for m in epoch_metrics]
                    aggregated[f'mean_{key}'] = np.mean(vals)
                    aggregated[f'std_{key}'] = np.std(vals)
            
            epochs.append(aggregated)
            print(f" d={aggregated['mean_effective_dimension']:.2f}, "
                  f"tri={aggregated['mean_triangles']:.0f}, "
                  f"edges={aggregated['mean_total_edges']:.0f}")
        else:
            print(" insufficient data")
    
    # Summary
    print()
    print("=" * 70)
    print("SCAFFOLD EVOLUTION SUMMARY")
    print("=" * 70)
    print()
    
    print(f"{'Epoch':>6} {'Dim':>7} {'Triangles':>10} {'Edges':>8} {'Hubs':>6} "
          f"{'Chain%':>8} {'Junct%':>8}")
    print("-" * 65)
    
    for e in epochs:
        print(f"{e['epoch']:>6} {e['mean_effective_dimension']:>7.2f} "
              f"{e['mean_triangles']:>10.0f} {e['mean_total_edges']:>8.0f} "
              f"{e['mean_n_hubs']:>6.1f} {e['mean_chain_fraction']*100:>7.1f}% "
              f"{e['mean_junction_fraction']*100:>7.1f}%")
    
    # Trend analysis
    print()
    print("-" * 70)
    print("TREND ANALYSIS")
    print("-" * 70)
    print()
    
    if len(epochs) >= 2:
        first = epochs[0]
        last = epochs[-1]
        
        def trend(metric):
            f_val = first.get(f'mean_{metric}', 0)
            l_val = last.get(f'mean_{metric}', 0)
            change = l_val - f_val
            pct = (change / f_val * 100) if f_val != 0 else 0
            return f_val, l_val, change, pct
        
        metrics_to_check = [
            ('effective_dimension', 'Dimension'),
            ('triangles', 'Triangles'),
            ('total_edges', 'Edges'),
            ('avg_clustering', 'Clustering'),
            ('chain_fraction', 'Chain %'),
            ('junction_fraction', 'Junction %'),
        ]
        
        print(f"{'Metric':<15} {'First':>10} {'Last':>10} {'Change':>10} {'Trend':>10}")
        print("-" * 55)
        
        stable_count = 0
        for metric, label in metrics_to_check:
            f_val, l_val, change, pct = trend(metric)
            
            if abs(pct) < 5:
                trend_str = "STABLE"
                stable_count += 1
            elif pct > 0:
                trend_str = f"+{pct:.1f}%"
            else:
                trend_str = f"{pct:.1f}%"
            
            print(f"{label:<15} {f_val:>10.2f} {l_val:>10.2f} {change:>+10.2f} {trend_str:>10}")
    
    # Verdict
    print()
    print("=" * 70)
    print("GATE 1 ASSESSMENT")
    print("=" * 70)
    print()
    
    if len(epochs) >= 2 and stable_count >= 4:
        print("FINDING: SCAFFOLD IS STABLE")
        print("  Most metrics show <5% change across epochs")
        print("  The filamentary regime appears to be a stable attractor")
        print()
        print("  The ~1D structure is not slowly evolving toward higher dimension")
        print("  It is the terminal geometric state under current dynamics")
    elif len(epochs) >= 2:
        print("FINDING: SCAFFOLD IS EVOLVING")
        print(f"  {6 - stable_count} of 6 metrics show >5% change")
        print("  The filamentary regime is not static")
        print()
        print("  Further investigation needed to characterize evolution direction")
    else:
        print("INSUFFICIENT DATA for trend analysis")
    
    return epochs


if __name__ == "__main__":
    epochs = run_long_time_observation()
