"""
Dimension vs. Driving Rate Sweep
================================

Core Question: Does effective dimension systematically rise with driving 
strength and temporal persistence?

The temporal test showed:
- Higher driving (~1.7-1.8 dimension) vs Phase 7-9 (~1.1)
- Richer structure (more triangles, higher correlation)

This test systematically varies:
- Injection interval (less frequent → more frequent)
- Holds other parameters fixed

Looking for:
- Smooth increase in dimension with driving
- Or threshold-like transition
- Correlation between dimension and population/triangles

Key hypothesis:
Dimension is an activated property of the medium's degrees of freedom,
with time/driving as the activator.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple


class DrivingSweepSimulator:
    """Simulator with configurable driving rate."""
    
    def __init__(self, size: int = 48, injection_interval: int = 100, injection_count: int = 3):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = injection_count
        
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
    
    def inject_random_vortices(self):
        center = self.size // 2
        for _ in range(self.injection_count):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        if self.step_count % self.injection_interval == 0:
            self.inject_random_vortices()
        
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
    """Measure all relevant metrics."""
    n = len(defects)
    if n < 15:
        return {'valid': False, 'n': n}
    
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            d = euclidean_distance_periodic(defects[i], defects[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    edges = sum(len(adj[i]) for i in range(n)) // 2
    degrees = [len(adj[i]) for i in range(n)]
    
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
    
    # Correlation
    euclidean_dists = []
    graph_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(defects[i], defects[j], size))
                graph_dists.append(graph_dist[i, j])
    
    correlation = pearsonr(euclidean_dists, graph_dists)[0] if len(euclidean_dists) >= 10 else 0
    
    # Dimension
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
    }


def run_driving_rate(injection_interval: int, name: str) -> Dict:
    """Run a single driving rate test."""
    print(f"\n  {name} (interval={injection_interval}):", end=" ", flush=True)
    
    sim = DrivingSweepSimulator(size=48, injection_interval=injection_interval, injection_count=3)
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Initial seeding
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    # Equilibration
    for _ in range(400):
        sim.step()
    print("eq", end=" ", flush=True)
    
    # Measurement
    measurements = []
    for step in range(500):
        sim.step()
        if step % 100 == 0:
            defects = sim.detect_defects()
            m = measure_state(defects, sim.size)
            if m['valid']:
                measurements.append(m)
                print(".", end="", flush=True)
    
    if not measurements:
        print(" insufficient")
        return {'valid': False, 'name': name}
    
    result = {
        'valid': True,
        'name': name,
        'interval': injection_interval,
        'driving_rate': 3.0 / injection_interval,  # vortices per step
        'n': np.mean([m['n'] for m in measurements]),
        'dimension': np.mean([m['dimension'] for m in measurements]),
        'dim_std': np.std([m['dimension'] for m in measurements]),
        'triangles': np.mean([m['triangles'] for m in measurements]),
        'clustering': np.mean([m['clustering'] for m in measurements]),
        'correlation': np.mean([m['correlation'] for m in measurements]),
    }
    
    print(f" d={result['dimension']:.2f}, n={result['n']:.0f}")
    return result


def run_driving_sweep():
    """
    Sweep across driving rates to test dimension activation hypothesis.
    """
    print("=" * 70)
    print("DIMENSION vs DRIVING RATE SWEEP")
    print("=" * 70)
    print()
    print("Hypothesis: Dimension is an activated property, with driving as activator")
    print()
    
    # Sweep: interval from 200 (weak) to 30 (strong)
    intervals = [200, 100, 50, 30]
    
    results = []
    
    print("-" * 70)
    print("DRIVING RATE SWEEP")
    print("-" * 70)
    
    for interval in intervals:
        rate_label = f"{3/interval:.3f} v/step"
        result = run_driving_rate(interval, rate_label)
        if result['valid']:
            results.append(result)
    
    # Summary
    print()
    print("=" * 70)
    print("DRIVING SWEEP RESULTS")
    print("=" * 70)
    print()
    
    print(f"{'Interval':>8} {'Rate':>10} {'Pop':>6} {'Dim':>7} {'±':>5} {'Tri':>8} {'Corr':>7}")
    print("-" * 60)
    
    for r in results:
        print(f"{r['interval']:>8} {r['driving_rate']:>10.4f} {r['n']:>6.0f} "
              f"{r['dimension']:>7.2f} {r['dim_std']:>5.2f} "
              f"{r['triangles']:>8.0f} {r['correlation']:>7.3f}")
    
    # Trend analysis
    print()
    print("-" * 70)
    print("TREND ANALYSIS")
    print("-" * 70)
    print()
    
    if len(results) >= 3:
        rates = [r['driving_rate'] for r in results]
        dims = [r['dimension'] for r in results]
        pops = [r['n'] for r in results]
        tris = [r['triangles'] for r in results]
        
        # Correlations
        dim_rate_corr = pearsonr(rates, dims)[0]
        dim_pop_corr = pearsonr(pops, dims)[0]
        pop_rate_corr = pearsonr(rates, pops)[0]
        
        print(f"Dimension-DrivingRate correlation: {dim_rate_corr:.3f}")
        print(f"Dimension-Population correlation: {dim_pop_corr:.3f}")
        print(f"Population-DrivingRate correlation: {pop_rate_corr:.3f}")
        
        print()
        print(f"Dimension range: {min(dims):.2f} to {max(dims):.2f}")
        print(f"Population range: {min(pops):.0f} to {max(pops):.0f}")
    
    # Verdict
    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    print()
    
    if len(results) >= 3:
        if dim_rate_corr > 0.7:
            print("FINDING: DIMENSION RISES SYSTEMATICALLY WITH DRIVING RATE")
            print(f"  Dim-Rate correlation: {dim_rate_corr:.2f}")
            print()
            print("  This STRONGLY SUPPORTS the hypothesis that:")
            print("  Dimension is an ACTIVATED property of the medium's degrees of freedom")
            print("  Time/driving serves as the ACTIVATOR")
            print()
            print("  Interpretation:")
            print("  - Low driving → limited DoF activation → ~1D filamentary")
            print("  - High driving → more DoF activated → higher dimension (~2D)")
        
        elif dim_rate_corr > 0.4:
            print("FINDING: MODERATE POSITIVE RELATIONSHIP")
            print(f"  Dim-Rate correlation: {dim_rate_corr:.2f}")
            print("  Dimension increases with driving, but relationship not linear")
            print("  May indicate threshold effects or saturation")
        
        elif abs(dim_rate_corr) < 0.3:
            print("FINDING: NO CLEAR RELATIONSHIP")
            print(f"  Dim-Rate correlation: {dim_rate_corr:.2f}")
            print("  Dimension does not systematically depend on driving rate")
            print("  Other factors may be more important")
        
        else:
            print("FINDING: UNEXPECTED NEGATIVE RELATIONSHIP")
            print(f"  Dim-Rate correlation: {dim_rate_corr:.2f}")
            print("  Higher driving associated with LOWER dimension")
            print("  Requires further investigation")
    
    return results


if __name__ == "__main__":
    results = run_driving_sweep()
