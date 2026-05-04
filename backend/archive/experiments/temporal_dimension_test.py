"""
Temporal Dimension Evolution Test
==================================

Core Question: Is the ~1D effective dimension stable over time, or does it 
evolve through stages?

This test tracks effective dimension over long time windows to distinguish:
1. Stable ~1.1 → filamentary state is a true attractor
2. Slowly rising → higher-dimensional organization is latent but slow
3. Rises/falls with population → dimension is a dynamical state variable
4. Changes in stages → supports layered branching hypothesis

Metrics tracked in sliding windows:
- Effective dimension
- Graph-Euclidean correlation
- Edge count / triangle count
- Clustering coefficient
- Population
- Hub count

Looking for: What changes WITH dimension? (connectivity? population? clustering?)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import time


class LongTimeSimulator:
    """Natural dynamics simulator for extended observation."""
    
    def __init__(self, size: int = 48):
        self.size = size
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
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
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = 0.7
                    elif dist >= interior_r + 10.0:
                        coupling[i, j, k] = 0.2
                    else:
                        t = (dist - interior_r) / 10.0
                        coupling[i, j, k] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        return coupling
    
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
    
    def inject_random_vortices(self, n: int = 3):
        center = self.size // 2
        for _ in range(n):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy)
    
    def step(self, dt: float = 0.04, inject: bool = True):
        self.step_count += 1
        
        # Periodic injection to maintain driven state
        if inject and self.step_count % 50 == 0:
            self.inject_random_vortices(3)
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        gamma = 0.007
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = 4.0 * lap_r - gamma * self.psi_r_dot
        acc_i = 4.0 * lap_i - gamma * self.psi_i_dot
        
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
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                defects.append((int(np.mean(coords[0])), int(np.mean(coords[1])), int(np.mean(coords[2]))))
        return defects


def euclidean_distance_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_state(defects, size):
    """Measure all relevant metrics for a single snapshot."""
    n = len(defects)
    if n < 10:
        return {'valid': False, 'n': n}
    
    # Build adjacency
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            d = euclidean_distance_periodic(defects[i], defects[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    # Basic counts
    edges = sum(len(adj[i]) for i in range(n)) // 2
    degrees = [len(adj[i]) for i in range(n)]
    mean_degree = np.mean(degrees)
    
    # Hubs (top 10%)
    hub_threshold = np.percentile(degrees, 90) if degrees else 0
    n_hubs = sum(1 for d in degrees if d >= hub_threshold)
    
    # Triangles
    triangles = 0
    for node in range(n):
        neighbors = list(adj[node])
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    triangles += 1
    triangles //= 3
    
    # Clustering
    clustering_sum = 0
    clustering_count = 0
    for node in range(n):
        neighbors = list(adj[node])
        k = len(neighbors)
        if k >= 2:
            local_tri = sum(1 for i in range(len(neighbors)) 
                          for j in range(i+1, len(neighbors)) 
                          if neighbors[j] in adj[neighbors[i]])
            clustering_sum += local_tri / (k * (k-1) / 2)
            clustering_count += 1
    clustering = clustering_sum / clustering_count if clustering_count > 0 else 0
    
    # Graph distances
    graph_dist = np.full((n, n), np.inf)
    for start in range(n):
        graph_dist[start, start] = 0
        queue = deque([start])
        visited = {start}
        while queue:
            node = queue.popleft()
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    graph_dist[start, neighbor] = graph_dist[start, node] + 1
                    queue.append(neighbor)
    
    # Graph-Euclidean correlation
    euclidean_dists = []
    graph_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(defects[i], defects[j], size))
                graph_dists.append(graph_dist[i, j])
    
    correlation = pearsonr(euclidean_dists, graph_dists)[0] if len(euclidean_dists) >= 10 else 0
    
    # Effective dimension
    radii = list(range(1, 6))
    counts = []
    for r in radii:
        c = [np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0)) for i in range(n)]
        counts.append(np.mean(c))
    
    if min(counts) > 0:
        coeffs = np.polyfit(np.log(radii), np.log(np.array(counts) + 1), 1)
        dimension = coeffs[0]
    else:
        dimension = 0
    
    return {
        'valid': True,
        'n': n,
        'edges': edges,
        'triangles': triangles,
        'clustering': clustering,
        'correlation': correlation,
        'dimension': dimension,
        'mean_degree': mean_degree,
        'n_hubs': n_hubs,
    }


def run_temporal_evolution_test():
    """
    Track dimension evolution over extended time.
    """
    print("=" * 70)
    print("TEMPORAL DIMENSION EVOLUTION TEST")
    print("=" * 70)
    print()
    print("Question: Is ~1D stable, slowly rising, population-dependent, or staged?")
    print()
    
    sim = LongTimeSimulator(size=48)
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Initial seeding
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    print("Running 12 time windows (extended observation)...")
    print()
    
    # Track evolution over 12 windows
    windows = []
    
    for window in range(12):
        print(f"Window {window + 1:2d}:", end=" ", flush=True)
        window_data = []
        
        # Run 400 steps per window
        for step in range(400):
            sim.step(inject=True)
            
            # Measure every 80 steps (5 samples per window)
            if step % 80 == 0:
                defects = sim.detect_defects()
                m = measure_state(defects, sim.size)
                if m['valid']:
                    window_data.append(m)
                    print(".", end="", flush=True)
        
        if window_data:
            # Aggregate window
            agg = {
                'window': window + 1,
                'n': np.mean([d['n'] for d in window_data]),
                'dimension': np.mean([d['dimension'] for d in window_data]),
                'dim_std': np.std([d['dimension'] for d in window_data]),
                'triangles': np.mean([d['triangles'] for d in window_data]),
                'edges': np.mean([d['edges'] for d in window_data]),
                'clustering': np.mean([d['clustering'] for d in window_data]),
                'correlation': np.mean([d['correlation'] for d in window_data]),
                'n_hubs': np.mean([d['n_hubs'] for d in window_data]),
            }
            windows.append(agg)
            print(f" d={agg['dimension']:.2f}±{agg['dim_std']:.2f}, n={agg['n']:.0f}")
        else:
            print(" insufficient data")
    
    # Summary
    print()
    print("=" * 70)
    print("TEMPORAL EVOLUTION SUMMARY")
    print("=" * 70)
    print()
    
    print(f"{'Window':>6} {'Pop':>6} {'Dim':>7} {'±':>5} {'Tri':>8} {'Clust':>7} {'Corr':>7}")
    print("-" * 55)
    for w in windows:
        print(f"{w['window']:>6} {w['n']:>6.0f} {w['dimension']:>7.2f} {w['dim_std']:>5.2f} "
              f"{w['triangles']:>8.0f} {w['clustering']:>7.3f} {w['correlation']:>7.3f}")
    
    # Trend analysis
    print()
    print("-" * 70)
    print("TREND ANALYSIS")
    print("-" * 70)
    print()
    
    if len(windows) >= 4:
        dims = [w['dimension'] for w in windows]
        pops = [w['n'] for w in windows]
        tris = [w['triangles'] for w in windows]
        
        # Overall trend
        early_dim = np.mean(dims[:3])
        late_dim = np.mean(dims[-3:])
        dim_change = late_dim - early_dim
        
        print(f"Early dimension (windows 1-3): {early_dim:.2f}")
        print(f"Late dimension (windows 10-12): {late_dim:.2f}")
        print(f"Change: {dim_change:+.2f}")
        print()
        
        # Correlation with population
        if len(dims) == len(pops):
            dim_pop_corr = pearsonr(dims, pops)[0]
            dim_tri_corr = pearsonr(dims, tris)[0]
            print(f"Dimension-Population correlation: {dim_pop_corr:.3f}")
            print(f"Dimension-Triangles correlation: {dim_tri_corr:.3f}")
        
        # Stability check
        dim_range = max(dims) - min(dims)
        dim_mean = np.mean(dims)
        dim_cv = np.std(dims) / dim_mean if dim_mean > 0 else 0
        
        print()
        print(f"Dimension range: {min(dims):.2f} to {max(dims):.2f} (span={dim_range:.2f})")
        print(f"Dimension CV: {dim_cv:.2%}")
    
    # Verdict
    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    print()
    
    if len(windows) >= 4:
        dim_change_pct = abs(dim_change / early_dim * 100) if early_dim > 0 else 0
        
        if dim_change_pct < 10 and dim_cv < 0.15:
            print("FINDING: DIMENSION IS STABLE")
            print(f"  Change: {dim_change_pct:.1f}%, CV: {dim_cv:.1%}")
            print("  The ~1D filamentary state appears to be a TRUE ATTRACTOR")
            print("  Not a transient or slowly evolving stage")
        
        elif dim_change > 0.15:
            print("FINDING: DIMENSION IS SLOWLY RISING")
            print(f"  Change: {dim_change:+.2f} over 12 windows")
            print("  Higher-dimensional organization may be LATENT BUT SLOW")
            print("  The medium may need longer times to evolve beyond ~1D")
        
        elif abs(dim_pop_corr) > 0.6:
            print("FINDING: DIMENSION TRACKS POPULATION")
            print(f"  Dim-Pop correlation: {dim_pop_corr:.2f}")
            print("  Dimension is a DYNAMICAL STATE VARIABLE, not fixed")
            print("  Changes with population, not independently")
        
        else:
            print("FINDING: DIMENSION FLUCTUATES")
            print(f"  Range: {dim_range:.2f}, CV: {dim_cv:.1%}")
            print("  May indicate STAGED EVOLUTION or transient dynamics")
            print("  Further investigation needed")
    
    return windows


if __name__ == "__main__":
    windows = run_temporal_evolution_test()
