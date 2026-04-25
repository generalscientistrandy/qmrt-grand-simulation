"""
Phase 10: Geometric Expansion and Freedom Activation Test
==========================================================

CENTRAL QUESTION:
Does increasing scaffold extent or relational spread activate higher effective 
dimension even at fixed local rules?

This tests whether dimensional branching is tied to:
- Expansion of geometric support volume
- Growth in available relational degrees of freedom
- Not just driving rate

CONCEPTUAL DISTINCTION:

1. Population Expansion
   - More defects, more triangles
   - Denser network
   - Tested: YES (Papers 1-7)

2. Geometric Expansion
   - Scaffold occupies larger effective extent
   - Graph distances expand (like scale factor)
   - Correlation length increases
   - Tested: NOT DIRECTLY

3. Freedom Expansion
   - Medium gains more active degrees of freedom
   - Higher-dimensional organization becomes possible
   - Expansion unlocks branching
   - Tested: NOT DIRECTLY

KEY OBSERVABLES:
- Occupied radius vs time
- Graph diameter vs time
- Correlation length vs time
- Effective dimension vs occupied extent
- Dimension vs total relational volume

HYPOTHESIS:
The ~1D → ~1.7D transition may not be driven by injection rate alone, but by 
how much relational extent the medium has accumulated. Expansion may be what 
unlocks higher-dimensional organization.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class ExpansionTestSimulator:
    """Simulator for geometric expansion testing."""
    
    def __init__(self, size: int = 48, injection_interval: int = 100):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 3
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Full mechanism
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.005
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
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
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        c_eff_sq = self.c_0_sq * self.tau
        
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
        
        self.remnant_field += 0.02 * topology_norm
        self.remnant_field *= 0.999
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


def measure_expansion_metrics(defects, size) -> Dict:
    """
    Measure geometric expansion metrics.
    
    Key observables:
    1. Occupied radius: How far from center defects extend
    2. Graph diameter: Maximum graph distance between any two nodes
    3. Mean graph distance: Average pairwise graph distance
    4. Effective dimension: Graph scaling exponent
    5. Relational volume: Total edge count (connectivity)
    """
    n = len(defects)
    
    if n < 10:
        return {'valid': False, 'n': n}
    
    center = size / 2
    
    # 1. Occupied radius (geometric extent)
    radii = [np.sqrt((d[0]-center)**2 + (d[1]-center)**2 + (d[2]-center)**2) 
             for d in defects]
    occupied_radius = np.percentile(radii, 90)  # 90th percentile radius
    mean_radius = np.mean(radii)
    
    # Sample for large populations
    max_n = min(n, 120)
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
    
    # 5. Relational volume (total edges)
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    
    # Graph distances via BFS
    max_sources = min(max_n, 30)
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
    
    # 2. Graph diameter (maximum graph distance)
    finite_dists = graph_dist[graph_dist < np.inf]
    if len(finite_dists) > 0:
        graph_diameter = np.max(finite_dists)
        mean_graph_dist = np.mean(finite_dists[finite_dists > 0])
    else:
        graph_diameter = 0
        mean_graph_dist = 0
    
    # 4. Effective dimension
    radii_list = [1, 2, 3, 4, 5]
    counts = [np.mean([np.sum((graph_dist[idx, :] <= r) & (graph_dist[idx, :] > 0)) 
                       for idx in range(max_sources)]) for r in radii_list]
    
    if min(counts) > 0:
        dimension = np.polyfit(np.log(radii_list), np.log(np.array(counts) + 1), 1)[0]
    else:
        dimension = 0
    
    # Graph-Euclidean correlation
    euc_dists, graph_dists = [], []
    for idx in range(max_sources):
        for j in range(idx + 1, max_n):
            if graph_dist[idx, j] < np.inf:
                euc_dists.append(euclidean_periodic(sample[idx], sample[j], size))
                graph_dists.append(graph_dist[idx, j])
    
    correlation = pearsonr(euc_dists, graph_dists)[0] if len(euc_dists) >= 10 else 0
    
    # Triangles
    triangles = 0
    for node in range(max_n):
        neighbors = list(adj[node])
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    triangles += 1
    triangles //= 3
    
    return {
        'valid': True,
        'n': n,
        # Geometric expansion
        'occupied_radius': occupied_radius,
        'mean_radius': mean_radius,
        # Relational expansion
        'graph_diameter': graph_diameter,
        'mean_graph_dist': mean_graph_dist,
        'relational_volume': edges,
        # Dimensional structure
        'dimension': dimension,
        'correlation': correlation,
        'triangles': triangles,
        'tri_per_node': triangles / max_n if max_n > 0 else 0,
    }


def run_expansion_tracking_test():
    """
    Track expansion metrics over time to see if geometric/relational 
    expansion precedes or correlates with dimensional transitions.
    """
    print("=" * 75)
    print("  PHASE 10: GEOMETRIC EXPANSION AND FREEDOM ACTIVATION TEST")
    print("=" * 75)
    print()
    print("Question: Does increasing scaffold extent activate higher dimension?")
    print()
    
    sim = ExpansionTestSimulator(size=48, injection_interval=100)
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Start with small seeding in center only
    center = 24
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) + abs(j) <= 2:
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    print("Tracking expansion metrics over time:")
    print()
    print(f"{'Step':>6} {'Pop':>5} {'Radius':>7} {'GDiam':>6} {'Edges':>6} "
          f"{'Dim':>5} {'Tri/N':>6}")
    print("-" * 50)
    
    history = []
    
    for step in range(2500):
        sim.step()
        
        if step % 100 == 0:
            defects = sim.detect_defects()
            m = measure_expansion_metrics(defects, sim.size)
            
            if m['valid']:
                print(f"{step:>6} {m['n']:>5} {m['occupied_radius']:>7.1f} "
                      f"{m['graph_diameter']:>6.0f} {m['relational_volume']:>6} "
                      f"{m['dimension']:>5.2f} {m['tri_per_node']:>6.2f}")
                
                history.append({
                    'step': step,
                    **m
                })
    
    # Analysis
    print()
    print("=" * 75)
    print("ANALYSIS: Expansion vs Dimension Relationship")
    print("=" * 75)
    print()
    
    if len(history) >= 5:
        # Correlate expansion metrics with dimension
        radii = [h['occupied_radius'] for h in history]
        diams = [h['graph_diameter'] for h in history]
        edges = [h['relational_volume'] for h in history]
        dims = [h['dimension'] for h in history]
        pops = [h['n'] for h in history]
        
        print("Correlations with effective dimension:")
        
        if len(radii) >= 3:
            r_rad = pearsonr(radii, dims)[0]
            r_diam = pearsonr(diams, dims)[0]
            r_edge = pearsonr(edges, dims)[0]
            r_pop = pearsonr(pops, dims)[0]
            
            print(f"  Occupied radius vs dimension: {r_rad:.3f}")
            print(f"  Graph diameter vs dimension:  {r_diam:.3f}")
            print(f"  Relational volume vs dimension: {r_edge:.3f}")
            print(f"  Population vs dimension:      {r_pop:.3f}")
            
            print()
            
            # Which expansion metric best predicts dimension?
            correlations = [
                ('Occupied radius', r_rad),
                ('Graph diameter', r_diam),
                ('Relational volume', r_edge),
                ('Population', r_pop),
            ]
            
            best = max(correlations, key=lambda x: abs(x[1]))
            print(f"Best predictor of dimension: {best[0]} (r = {best[1]:.3f})")
            
            # Check if expansion precedes dimensional increase
            print()
            print("Time evolution:")
            early = history[:len(history)//3]
            late = history[-len(history)//3:]
            
            if early and late:
                early_dim = np.mean([h['dimension'] for h in early])
                late_dim = np.mean([h['dimension'] for h in late])
                early_radius = np.mean([h['occupied_radius'] for h in early])
                late_radius = np.mean([h['occupied_radius'] for h in late])
                early_diam = np.mean([h['graph_diameter'] for h in early])
                late_diam = np.mean([h['graph_diameter'] for h in late])
                
                print(f"  Early phase: dim={early_dim:.2f}, radius={early_radius:.1f}, diameter={early_diam:.1f}")
                print(f"  Late phase:  dim={late_dim:.2f}, radius={late_radius:.1f}, diameter={late_diam:.1f}")
                
                print()
                if late_dim > early_dim and late_radius > early_radius:
                    print("FINDING: Both dimension and geometric extent increase together")
                    print("  → Consistent with expansion-activated dimensional branching")
                elif late_dim > early_dim:
                    print("FINDING: Dimension increases without significant radius expansion")
                    print("  → Dimensional branching may be population/connectivity driven")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase10_expansion_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'geometric_expansion_test',
            'history': history,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history


if __name__ == "__main__":
    results = run_expansion_tracking_test()
