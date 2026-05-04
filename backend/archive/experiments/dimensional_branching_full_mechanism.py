"""
Dimensional Branching Study: Full-Mechanism Version
=====================================================

Re-run the dimensional branching investigation using the full QMRT mechanism
(dynamic τ, variable c_eff, active remnant field) to determine:

1. Does the 1D → higher-dimensional transition survive?
2. How does τ self-regulation affect organizational structure?
3. What dimension does the full mechanism achieve?

This is the critical gate for Paper 7.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class FullMechanismBranchingSimulator:
    """Full-mechanism simulator for dimensional branching study."""
    
    def __init__(self, size: int = 48, injection_interval: int = 50):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 3
        
        # Wave field
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Dynamic medium (FULL MECHANISM)
        self.tau = np.ones((size, size, size))
        self.tau_0 = 1.0
        self.c_0_sq = 4.0
        self.tau_relaxation = 0.01
        self.tau_response = 0.005
        
        # Memory fields
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        self.remnant_decay = 0.001
        self.remnant_accumulation = 0.02
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
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
        
        # Dynamic τ
        energy_density = self.psi_r**2 + self.psi_i**2 + \
                        0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy_density - np.mean(energy_density))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        # Variable c_eff
        c_eff_sq = self.c_0_sq * self.tau / self.tau_0
        
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
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
        
        # Active remnant field
        self.remnant_field += self.remnant_accumulation * topology_norm
        self.remnant_field *= (1 - self.remnant_decay)
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
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
                defects.append((
                    int(np.mean(coords[0])),
                    int(np.mean(coords[1])),
                    int(np.mean(coords[2]))
                ))
        return defects


def euclidean_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_dimension_and_structure(defects, size) -> Dict:
    """Measure effective dimension and structural properties."""
    n = len(defects)
    
    if n < 15:
        return {'valid': False, 'n': n}
    
    # Sample for large populations
    max_n = min(n, 150)
    if n > max_n:
        indices = np.random.choice(n, max_n, replace=False)
        sample = [defects[i] for i in indices]
    else:
        sample = defects
        max_n = n
    
    # Build adjacency
    adj = defaultdict(set)
    for i in range(max_n):
        for j in range(i + 1, max_n):
            d = euclidean_periodic(sample[i], sample[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    
    # Triangles
    triangles = 0
    for node in range(max_n):
        neighbors = list(adj[node])
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    triangles += 1
    triangles //= 3
    tri_per_node = triangles / max_n if max_n > 0 else 0
    
    # Graph distances
    max_sources = min(max_n, 40)
    graph_dist = np.full((max_sources, max_n), np.inf)
    for idx in range(max_sources):
        graph_dist[idx, idx] = 0
        queue = deque([idx])
        visited = {idx}
        while queue:
            node = queue.popleft()
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    graph_dist[idx, neighbor] = graph_dist[idx, node] + 1
                    queue.append(neighbor)
    
    # Correlation
    euc_dists, graph_dists = [], []
    for idx in range(max_sources):
        for j in range(idx + 1, max_n):
            if graph_dist[idx, j] < np.inf:
                euc_dists.append(euclidean_periodic(sample[idx], sample[j], size))
                graph_dists.append(graph_dist[idx, j])
    
    correlation = pearsonr(euc_dists, graph_dists)[0] if len(euc_dists) >= 10 else 0
    
    # Dimension
    radii = [1, 2, 3, 4, 5]
    counts = [np.mean([np.sum((graph_dist[idx, :] <= r) & (graph_dist[idx, :] > 0)) 
                       for idx in range(max_sources)]) for r in radii]
    
    if min(counts) > 0:
        dimension = np.polyfit(np.log(radii), np.log(np.array(counts) + 1), 1)[0]
    else:
        dimension = 0
    
    return {
        'valid': True,
        'n': n,
        'edges': edges,
        'triangles': triangles,
        'tri_per_node': tri_per_node,
        'correlation': correlation,
        'dimension': dimension,
    }


def run_full_mechanism_dimensional_study():
    """
    Run dimensional study with full-mechanism simulator.
    
    Compare to reduced-model results to see if 1D→2D branching survives.
    """
    print("=" * 75)
    print("  DIMENSIONAL BRANCHING: FULL-MECHANISM TEST")
    print("=" * 75)
    print()
    print("Testing if dimensional transition survives under τ self-regulation")
    print()
    
    # Test across driving intervals
    intervals = [50, 100, 200, 300, 500, 750, 1000]
    
    BUILD_STEPS = 2500  # Longer build for proper equilibration
    MEASURE_STEPS = 1000  # Steps to collect measurements
    SAMPLE_INTERVAL = 100
    
    results = []
    
    print("-" * 75)
    print(f"{'Interval':>8} {'Rate':>8} {'Pop':>6} {'Dim':>6} {'Tri/N':>6} "
          f"{'Corr':>6} {'τ_mean':>7} {'τ_std':>7}")
    print("-" * 75)
    
    for interval in intervals:
        sim = FullMechanismBranchingSimulator(size=48, injection_interval=interval)
        
        np.random.seed(42)
        sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
        
        # Initial seeding
        center = 24
        for i in range(-4, 5):
            for j in range(-4, 5):
                if abs(i) + abs(j) <= 4:
                    sim.inject_vortex(center + i * 3, center + j * 3)
        
        # Build phase
        for _ in range(BUILD_STEPS):
            sim.step()
        
        # Measurement phase
        measurements = []
        for step in range(MEASURE_STEPS):
            sim.step()
            if step % SAMPLE_INTERVAL == 0:
                defects = sim.detect_defects()
                m = measure_dimension_and_structure(defects, sim.size)
                m['tau_mean'] = float(np.mean(sim.tau))
                m['tau_std'] = float(np.std(sim.tau))
                measurements.append(m)
        
        # Average late-time measurements
        valid = [m for m in measurements if m.get('valid', False)]
        
        if valid:
            mean_n = np.mean([m['n'] for m in valid])
            mean_dim = np.mean([m['dimension'] for m in valid])
            mean_tri = np.mean([m['tri_per_node'] for m in valid])
            mean_corr = np.mean([m['correlation'] for m in valid])
            mean_tau = np.mean([m['tau_mean'] for m in valid])
            mean_tau_std = np.mean([m['tau_std'] for m in valid])
            
            print(f"{interval:>8} {3/interval:>8.4f} {mean_n:>6.0f} {mean_dim:>6.2f} "
                  f"{mean_tri:>6.2f} {mean_corr:>6.2f} {mean_tau:>7.3f} {mean_tau_std:>7.3f}")
            
            results.append({
                'interval': interval,
                'driving_rate': 3.0 / interval,
                'population': mean_n,
                'dimension': mean_dim,
                'tri_per_node': mean_tri,
                'correlation': mean_corr,
                'tau_mean': mean_tau,
                'tau_std': mean_tau_std,
                'mechanism': 'full',
            })
        else:
            print(f"{interval:>8} {3/interval:>8.4f} {'---':>6} {'---':>6} "
                  f"{'---':>6} {'---':>6} {'---':>7} {'---':>7}")
    
    # Analysis
    print()
    print("=" * 75)
    print("ANALYSIS: Does Dimensional Transition Survive?")
    print("=" * 75)
    print()
    
    if len(results) >= 2:
        dims = [(r['interval'], r['dimension']) for r in results]
        dims.sort(key=lambda x: x[0], reverse=True)
        
        print("Dimension vs Driving (weaker → stronger):")
        for interval, dim in dims:
            marker = "***" if dim > 1.5 else ""
            print(f"  Interval {interval:4d} → Dimension {dim:.2f} {marker}")
        
        # Check for transition
        dim_min = min(d for _, d in dims)
        dim_max = max(d for _, d in dims)
        dim_range = dim_max - dim_min
        
        print()
        print(f"Dimension range: {dim_min:.2f} to {dim_max:.2f} (span = {dim_range:.2f})")
        
        if dim_range > 0.3:
            print("→ Dimensional transition DETECTED under full mechanism")
        else:
            print("→ No significant dimensional transition")
        
        # Correlation with τ
        print()
        taus = [r['tau_mean'] for r in results]
        dims_list = [r['dimension'] for r in results]
        if len(taus) >= 3:
            tau_dim_corr = pearsonr(taus, dims_list)[0]
            print(f"Correlation (τ vs dimension): {tau_dim_corr:.3f}")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/full_mechanism_dimensional_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'dimensional_branching_full_mechanism',
            'build_steps': BUILD_STEPS,
            'measure_steps': MEASURE_STEPS,
            'results': results,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    results = run_full_mechanism_dimensional_study()
