"""
Phase 11e: Larger Domain Test (64³)
====================================

HYPOTHESIS TO TEST:
If geometry is the leading branch driving expansion, then:
  - Larger domain → more room for loops before crowding
  - Transition population should scale with domain volume
  - Loop-dominated regime should persist longer

PREDICTION:
  48³ grid: Transition at ~400 defects
  64³ grid: Transition should be at ~950 defects (volume ratio 64³/48³ ≈ 2.37)

If this holds, it confirms:
  - Transition is a packing/geometric effect
  - Geometry is the leading branch
  - "Expansion" is geometric scaffold development

NOTE: Using 64³ instead of 96³ to stay within computation limits.
      64³/48³ = 2.37x volume increase is sufficient to test scaling.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class LargerDomainSimulator:
    """Simulator with configurable domain size for scaling tests."""
    
    def __init__(self, size: int = 64, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 4  # Slightly more for larger domain
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
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


def measure_branch_metrics(defects, size) -> Dict:
    """Measure Loop-vs-Clustering and density metrics."""
    n = len(defects)
    
    if n < 15:
        return {'valid': False, 'n': n}
    
    max_n = min(n, 80)
    if n > max_n:
        indices = np.random.choice(n, max_n, replace=False)
        sample = [defects[i] for i in indices]
    else:
        sample = defects
        max_n = n
    
    # Pairwise distances
    distances = []
    adj = defaultdict(set)
    
    for i in range(max_n):
        for j in range(i + 1, max_n):
            d = euclidean_periodic(sample[i], sample[j], size)
            distances.append(d)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    avg_distance = np.mean(distances) if distances else 0
    density = max_n / (avg_distance ** 3 + 1) if avg_distance > 0 else 0
    
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    degrees = [len(adj[i]) for i in range(max_n)]
    mean_degree = np.mean(degrees) if degrees else 0
    
    # Components
    visited = set()
    n_components = 0
    for start in range(max_n):
        if start not in visited:
            n_components += 1
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    for neighbor in adj[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)
    
    # Cycle rank (loops)
    cycle_rank = edges - max_n + n_components
    cycles_per_node = cycle_rank / max_n if max_n > 0 else 0
    
    # Clustering
    clustering_coeffs = []
    for node in range(max_n):
        k = len(adj[node])
        if k >= 2:
            neighbors = list(adj[node])
            edges_between = 0
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    if neighbors[j] in adj[neighbors[i]]:
                        edges_between += 1
            max_edges = k * (k - 1) / 2
            clustering_coeffs.append(edges_between / max_edges)
    
    mean_clustering = np.mean(clustering_coeffs) if clustering_coeffs else 0
    
    loop_vs_clust = cycles_per_node - mean_clustering
    
    return {
        'valid': True,
        'n': n,
        'avg_distance': avg_distance,
        'density': density,
        'mean_degree': mean_degree,
        'cycles_per_node': cycles_per_node,
        'mean_clustering': mean_clustering,
        'loop_vs_clust': loop_vs_clust,
    }


def run_larger_domain_test():
    """
    Test whether the transition population scales with domain volume.
    
    This tests the "geometry as leading branch" hypothesis.
    """
    print("=" * 75)
    print("  PHASE 11e: LARGER DOMAIN SCALING TEST (64³)")
    print("=" * 75)
    print()
    print("HYPOTHESIS: If geometry is the leading branch, transition should scale")
    print("            with domain volume.")
    print()
    print("Prediction: 48³ → 64³ (2.37× volume) should shift transition from")
    print("            ~400 defects to ~950 defects.")
    print()
    
    sim = LargerDomainSimulator(size=64, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(64, 64, 64)
    sim.psi_i += 0.03 * np.random.randn(64, 64, 64)
    
    # Scaled seeding for larger domain
    center = 32
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 5, center + j * 5)
    
    print(f"{'Step':>5} {'Pop':>5} │ {'AvgDist':>7} {'Density':>8} │ "
          f"{'Loops':>6} {'Clust':>6} │ {'L-C':>7} {'Dom':>8}")
    print("-" * 75)
    
    history = []
    
    # Need more steps for larger domain to build up
    for step in range(1600):
        sim.step()
        
        if step % 50 == 0:
            defects = sim.detect_defects()
            m = measure_branch_metrics(defects, sim.size)
            
            if m['valid']:
                if m['loop_vs_clust'] > 0.1:
                    dom = 'Loop'
                elif m['loop_vs_clust'] < -0.1:
                    dom = 'Clust'
                else:
                    dom = 'Balanced'
                
                print(f"{step:>5} {m['n']:>5} │ "
                      f"{m['avg_distance']:>7.2f} {m['density']:>8.5f} │ "
                      f"{m['cycles_per_node']:>6.3f} {m['mean_clustering']:>6.3f} │ "
                      f"{m['loop_vs_clust']:>+7.3f} {dom:>8}")
                
                m['step'] = step
                m['dominant'] = dom
                history.append(m)
    
    # === TRANSITION ANALYSIS ===
    print()
    print("=" * 75)
    print("TRANSITION ANALYSIS (64³ Domain)")
    print("=" * 75)
    print()
    
    # Find transition population
    valid = [h for h in history if h['n'] > 50]
    sorted_by_pop = sorted(valid, key=lambda x: x['n'])
    
    transition_pop = None
    for i in range(len(sorted_by_pop) - 1):
        if sorted_by_pop[i]['loop_vs_clust'] > 0 and sorted_by_pop[i+1]['loop_vs_clust'] < 0:
            transition_pop = (sorted_by_pop[i]['n'] + sorted_by_pop[i+1]['n']) / 2
            break
    
    # Population bands
    pop_bins = [(0, 200), (200, 500), (500, 800), (800, 1200), (1200, 2000)]
    
    print("Dominance by population band:")
    print()
    print(f"{'Population':>14} │ {'Loop':>6} {'Bal':>6} {'Clust':>6} │ {'Avg L-C':>8}")
    print("-" * 55)
    
    for lo, hi in pop_bins:
        band = [h for h in valid if lo <= h['n'] < hi]
        if band:
            loop_count = sum(1 for h in band if h['dominant'] == 'Loop')
            bal_count = sum(1 for h in band if h['dominant'] == 'Balanced')
            clust_count = sum(1 for h in band if h['dominant'] == 'Clust')
            avg_lc = np.mean([h['loop_vs_clust'] for h in band])
            
            print(f"{lo:>6}-{hi:<7} │ {loop_count:>6} {bal_count:>6} {clust_count:>6} │ {avg_lc:>+8.3f}")
    
    print()
    
    if transition_pop:
        print(f"ESTIMATED TRANSITION POPULATION (64³): ~{transition_pop:.0f}")
    else:
        # Estimate from where L-C crosses zero
        last_positive = max([h['n'] for h in valid if h['loop_vs_clust'] > 0], default=0)
        first_negative = min([h['n'] for h in valid if h['loop_vs_clust'] < 0], default=float('inf'))
        if last_positive > 0 and first_negative < float('inf'):
            transition_pop = (last_positive + first_negative) / 2
            print(f"ESTIMATED TRANSITION POPULATION (64³): ~{transition_pop:.0f}")
        else:
            avg_lc = np.mean([h['loop_vs_clust'] for h in valid])
            if avg_lc > 0:
                print("No transition detected: Loop dominates throughout")
                transition_pop = "Loop dominant"
            else:
                print("No transition detected: Clustering dominates throughout")
                transition_pop = "Clust dominant"
    
    print()
    print("=" * 75)
    print("SCALING COMPARISON")
    print("=" * 75)
    print()
    print("Reference (48³): Transition at ~400 defects")
    print(f"This test (64³): Transition at ~{transition_pop}")
    print()
    
    if isinstance(transition_pop, (int, float)):
        volume_ratio = (64**3) / (48**3)  # = 2.37
        expected_transition = 400 * volume_ratio  # ~948
        actual_ratio = transition_pop / 400
        
        print(f"Volume ratio (64³/48³): {volume_ratio:.2f}×")
        print(f"Expected transition if scaling holds: ~{expected_transition:.0f}")
        print(f"Actual ratio: {actual_ratio:.2f}×")
        print()
        
        if 0.7 * volume_ratio <= actual_ratio <= 1.5 * volume_ratio:
            print("RESULT: Transition SCALES with volume!")
            print("        Confirms GEOMETRIC PACKING as primary driver.")
            print("        Supports 'geometry as leading branch' hypothesis.")
            scaling_confirmed = True
        elif actual_ratio > 1.5 * volume_ratio:
            print("RESULT: Transition scales SUPER-LINEARLY with volume.")
            print("        Suggests boundary effects suppress loops in small domains.")
            scaling_confirmed = 'superlinear'
        else:
            print("RESULT: Transition does NOT scale with volume as expected.")
            print("        May indicate non-geometric factors at play.")
            scaling_confirmed = False
    else:
        scaling_confirmed = 'inconclusive'
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_domain_scaling_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'larger_domain_scaling_test',
            'hypothesis': 'Transition population scales with domain volume',
            'domain_size': 64,
            'reference_transition': 400,
            'measured_transition': transition_pop if isinstance(transition_pop, (int, float)) else str(transition_pop),
            'volume_ratio': (64**3) / (48**3),
            'scaling_confirmed': scaling_confirmed,
            'history': history,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, transition_pop


if __name__ == "__main__":
    history, transition = run_larger_domain_test()
