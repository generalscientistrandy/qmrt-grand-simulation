"""
Phase 11c: Branch Dominance Transition Analysis
================================================

FINDING FROM PHASE 11b:
- Loop structure leads during early build-up (63%)
- Clustering takes over as population grows
- This suggests a DEVELOPMENTAL TRANSITION

KEY QUESTION:
Is there a characteristic population threshold where leadership transitions
from Loop-dominant to Clustering-dominant?

If so, this would support the "staggered branch maturation" hypothesis:
  - Branch 2 (loops) matures first at lower population
  - Branch 3 (clustering) matures later at higher population
  - This transition could explain why dimensionality increases with population
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class TransitionAnalysisSimulator:
    """Simulator configured for branch transition analysis."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 3
        
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


def measure_branch_dominance(defects, size) -> Dict:
    """
    Measure which branch is dominant and compute dominance ratio.
    Also compute effective dimension for correlation with dominance.
    """
    n = len(defects)
    
    if n < 15:
        return {'valid': False, 'n': n}
    
    max_n = min(n, 70)
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
    
    # Effective dimension (simplified)
    max_sources = min(max_n, 15)
    radii_list = [1, 2, 3]
    counts = []
    
    for r in radii_list:
        r_counts = []
        for src in range(max_sources):
            dist = {src: 0}
            queue = deque([src])
            while queue:
                node = queue.popleft()
                if dist[node] < r:
                    for neighbor in adj[node]:
                        if neighbor not in dist:
                            dist[neighbor] = dist[node] + 1
                            queue.append(neighbor)
            r_counts.append(sum(1 for d in dist.values() if 0 < d <= r))
        counts.append(np.mean(r_counts))
    
    if min(counts) > 0:
        dimension = np.polyfit(np.log(radii_list), np.log(np.array(counts) + 1), 1)[0]
    else:
        dimension = 0
    
    # Compute dominance
    loop_vs_clust = cycles_per_node - mean_clustering
    
    if loop_vs_clust > 0.1:
        dominant = 'Loop'
    elif loop_vs_clust < -0.1:
        dominant = 'Clustering'
    else:
        dominant = 'Balanced'
    
    return {
        'valid': True,
        'n': n,
        'mean_degree': mean_degree,
        'cycles_per_node': cycles_per_node,
        'mean_clustering': mean_clustering,
        'loop_vs_clust': loop_vs_clust,
        'dominant': dominant,
        'dimension': dimension,
    }


def run_dominance_transition_test():
    """
    Test for population-dependent transition in branch dominance.
    
    KEY QUESTION: Is there a characteristic population where the system
    transitions from Loop-dominant to Clustering-dominant?
    """
    print("=" * 75)
    print("  PHASE 11c: BRANCH DOMINANCE TRANSITION ANALYSIS")
    print("=" * 75)
    print()
    print("Question: Is there a population threshold where branch dominance")
    print("          transitions from Loop to Clustering?")
    print()
    
    sim = TransitionAnalysisSimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Moderate seeding
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    print(f"{'Step':>5} {'Pop':>4} │ {'Loops':>5} {'Clust':>5} {'L-C':>6} │ "
          f"{'Dom':>8} {'Dim':>5}")
    print("-" * 60)
    
    history = []
    
    for step in range(1200):
        sim.step()
        
        if step % 40 == 0:
            defects = sim.detect_defects()
            m = measure_branch_dominance(defects, sim.size)
            
            if m['valid']:
                print(f"{step:>5} {m['n']:>4} │ "
                      f"{m['cycles_per_node']:>5.3f} {m['mean_clustering']:>5.3f} "
                      f"{m['loop_vs_clust']:>+6.3f} │ "
                      f"{m['dominant']:>8} {m['dimension']:>5.2f}")
                
                m['step'] = step
                history.append(m)
    
    # === TRANSITION ANALYSIS ===
    print()
    print("=" * 75)
    print("POPULATION-DEPENDENT DOMINANCE ANALYSIS")
    print("=" * 75)
    print()
    
    # Bin by population
    pop_bins = [(0, 100), (100, 300), (300, 500), (500, 800), (800, 2000)]
    
    print("Dominance by population band:")
    print()
    print(f"{'Population':>12} │ {'Loop':>6} {'Balanced':>8} {'Clust':>6} │ {'Avg L-C':>8} {'Avg Dim':>8}")
    print("-" * 65)
    
    for lo, hi in pop_bins:
        band = [h for h in history if lo <= h['n'] < hi]
        if band:
            loop_count = sum(1 for h in band if h['dominant'] == 'Loop')
            bal_count = sum(1 for h in band if h['dominant'] == 'Balanced')
            clust_count = sum(1 for h in band if h['dominant'] == 'Clustering')
            avg_lc = np.mean([h['loop_vs_clust'] for h in band])
            avg_dim = np.mean([h['dimension'] for h in band])
            
            print(f"{lo:>5}-{hi:<6} │ {loop_count:>6} {bal_count:>8} {clust_count:>6} │ "
                  f"{avg_lc:>+8.3f} {avg_dim:>8.2f}")
    
    print()
    
    # Find transition point
    valid_history = [h for h in history if h['n'] > 50]
    if valid_history:
        # Sort by population
        sorted_by_pop = sorted(valid_history, key=lambda x: x['n'])
        
        # Find population where L-C crosses zero
        transition_pop = None
        for i in range(len(sorted_by_pop) - 1):
            if sorted_by_pop[i]['loop_vs_clust'] > 0 and sorted_by_pop[i+1]['loop_vs_clust'] < 0:
                transition_pop = (sorted_by_pop[i]['n'] + sorted_by_pop[i+1]['n']) / 2
                break
        
        if transition_pop:
            print(f"ESTIMATED TRANSITION POPULATION: ~{transition_pop:.0f}")
            print()
            print("Interpretation: Below this population, loops dominate.")
            print("                Above this population, clustering dominates.")
        else:
            # Check which dominates overall
            avg_lc = np.mean([h['loop_vs_clust'] for h in valid_history])
            if avg_lc > 0:
                print("No transition detected: Loop structure dominates throughout.")
            else:
                print("No transition detected: Clustering dominates throughout.")
    
    print()
    print("=" * 75)
    print("DIMENSION VS BRANCH DOMINANCE")
    print("=" * 75)
    print()
    
    # Correlation of dimension with loop-vs-clustering
    if len(valid_history) >= 5:
        dims = [h['dimension'] for h in valid_history]
        lc_ratios = [h['loop_vs_clust'] for h in valid_history]
        pops = [h['n'] for h in valid_history]
        
        r_dim_lc, p_dim_lc = pearsonr(lc_ratios, dims)
        r_dim_pop, p_dim_pop = pearsonr(pops, dims)
        
        print(f"Correlation of dimension with:")
        print(f"  Loop-vs-Clustering (L-C):  r = {r_dim_lc:+.3f} (p = {p_dim_lc:.3f})")
        print(f"  Population:                r = {r_dim_pop:+.3f} (p = {p_dim_pop:.3f})")
        print()
        
        if r_dim_lc < -0.3:
            print("FINDING: Dimension INCREASES as clustering becomes more dominant.")
            print("         Supports: Higher dimension ↔ deeper organizational maturation.")
        elif r_dim_lc > 0.3:
            print("FINDING: Dimension increases with loop dominance.")
            print("         Suggests: Loops are the primary dimensional scaffold.")
        else:
            print("FINDING: Dimension not strongly tied to Loop-vs-Clustering balance.")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_dominance_transition_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'branch_dominance_transition',
            'hypothesis': 'Population-dependent transition in organizational dominance',
            'history': history,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history


if __name__ == "__main__":
    history = run_dominance_transition_test()
