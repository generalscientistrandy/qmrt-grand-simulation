"""
Phase 11: Staggered Branch Activation Test
===========================================

CONCEPTUAL FRAMEWORK (User-Guided Reframing):

"Spacetime expansion" may not be uniform metric expansion, but rather:
  - Asynchronous activation of different organizational branches
  - Each branch opens new degrees of freedom at different rates
  - Geometry emerges to fill what becomes available

BRANCH HIERARCHY (Hypothesized):

  Branch 1 (Early/Fast):
    - Basic connectivity, edge formation
    - Gives initial filamentary scaffold
    - Looks ~1D

  Branch 2 (Intermediate):
    - Cross-relational structure, loops, mesh behavior
    - Pushes toward ~2D-like organization
    
  Branch 3 (Late/Slow):
    - Higher-order clustering, volumetric organization
    - Possible route toward 3D-like richness

KEY TEST:
  Do different observables "turn on" at different characteristic times?
  Is there a lag structure between connectivity → loops → higher-order?

OBSERVABLES BY BRANCH:

  Branch 1 (Connectivity):
    - Edge count, mean degree
    - Giant component fraction
    
  Branch 2 (Loop Structure):
    - Cycle rank (independent loops)
    - Triangle density
    
  Branch 3 (Higher-Order):
    - Clustering coefficient
    - Path redundancy / mesh richness
    - Degree entropy (relational state diversity)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class BranchActivationSimulator:
    """Simulator optimized for branch activation tracking."""
    
    def __init__(self, size: int = 48, injection_interval: int = 100):
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


def measure_branch_metrics(defects, size) -> Dict:
    """
    Measure observables for each organizational branch.
    
    Branch 1: Connectivity (early)
    Branch 2: Loop structure (intermediate)  
    Branch 3: Higher-order (late)
    """
    n = len(defects)
    
    if n < 10:
        return {'valid': False, 'n': n}
    
    # Aggressive sampling for efficiency
    max_n = min(n, 80)
    if n > max_n:
        indices = np.random.choice(n, max_n, replace=False)
        sample = [defects[i] for i in indices]
    else:
        sample = defects
        max_n = n
    
    # Build adjacency (connectivity threshold)
    adj = defaultdict(set)
    for i in range(max_n):
        for j in range(i + 1, max_n):
            d = euclidean_periodic(sample[i], sample[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    # === BRANCH 1: CONNECTIVITY (Early/Fast) ===
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    degrees = [len(adj[i]) for i in range(max_n)]
    mean_degree = np.mean(degrees) if degrees else 0
    
    # Giant component fraction
    visited = set()
    component_sizes = []
    for start in range(max_n):
        if start not in visited:
            queue = deque([start])
            comp_size = 0
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    comp_size += 1
                    for neighbor in adj[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)
            component_sizes.append(comp_size)
    
    giant_component_frac = max(component_sizes) / max_n if component_sizes else 0
    n_components = len(component_sizes)
    
    # === BRANCH 2: LOOP STRUCTURE (Intermediate) ===
    # Cycle rank = E - V + C (number of independent cycles)
    cycle_rank = edges - max_n + n_components
    cycles_per_node = cycle_rank / max_n if max_n > 0 else 0
    
    # Triangle counting (optimized: only check nodes with degree >= 2)
    triangles = 0
    for node in range(max_n):
        if len(adj[node]) >= 2:
            neighbors = list(adj[node])
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    if neighbors[j] in adj[neighbors[i]]:
                        triangles += 1
    triangles //= 3
    tri_per_node = triangles / max_n if max_n > 0 else 0
    
    # === BRANCH 3: HIGHER-ORDER STRUCTURE (Late/Slow) ===
    # Clustering coefficient
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
    
    # Degree entropy (relational state diversity)
    if degrees and max(degrees) > 0:
        degree_counts = np.bincount(degrees)
        degree_probs = degree_counts / sum(degree_counts)
        degree_probs = degree_probs[degree_probs > 0]
        degree_entropy = -np.sum(degree_probs * np.log(degree_probs + 1e-10))
    else:
        degree_entropy = 0
    
    # === EFFECTIVE DIMENSION (Overall Outcome) ===
    # Simplified BFS dimension estimate
    max_sources = min(max_n, 20)
    radii_list = [1, 2, 3, 4]
    counts = []
    
    for r in radii_list:
        r_counts = []
        for src in range(max_sources):
            # BFS to radius r
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
    
    return {
        'valid': True,
        'n': n,
        # Branch 1: Connectivity
        'edges': edges,
        'mean_degree': mean_degree,
        'giant_component_frac': giant_component_frac,
        # Branch 2: Loops
        'cycle_rank': cycle_rank,
        'cycles_per_node': cycles_per_node,
        'tri_per_node': tri_per_node,
        # Branch 3: Higher-order
        'mean_clustering': mean_clustering,
        'degree_entropy': degree_entropy,
        # Outcome
        'dimension': dimension,
    }


def detect_activation_time(history: List[Dict], metric: str, threshold: float) -> int:
    """Find first step where metric exceeds threshold."""
    for h in history:
        if h.get(metric, 0) >= threshold:
            return h['step']
    return -1  # Never activated


def run_branch_activation_test():
    """
    Test whether different organizational branches activate at different times.
    
    Key Question: Is there a lag structure between:
      Branch 1 (connectivity) → Branch 2 (loops) → Branch 3 (higher-order)?
    """
    print("=" * 75)
    print("  PHASE 11: STAGGERED BRANCH ACTIVATION TEST")
    print("=" * 75)
    print()
    print("Hypothesis: Spacetime expansion is asynchronous branch development,")
    print("            not uniform metric expansion.")
    print()
    print("Testing for activation lag between organizational layers:")
    print("  Branch 1: Connectivity (edges, degree, giant component)")
    print("  Branch 2: Loop structure (cycle rank, triangles)")
    print("  Branch 3: Higher-order (clustering, degree entropy)")
    print()
    
    sim = BranchActivationSimulator(size=48, injection_interval=100)
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Initial seeding
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    print(f"{'Step':>6} {'Pop':>5} │ {'Degree':>6} {'Giant':>5} │ "
          f"{'Cycles':>6} {'Tri':>5} │ {'Clust':>5} {'Ent':>4} │ {'Dim':>5}")
    print("-" * 75)
    
    history = []
    
    # Run 1500 steps, sample every 150 (10 measurements, efficient)
    for step in range(1500):
        sim.step()
        
        if step % 150 == 0 and step > 0:
            defects = sim.detect_defects()
            m = measure_branch_metrics(defects, sim.size)
            
            if m['valid']:
                print(f"{step:>6} {m['n']:>5} │ "
                      f"{m['mean_degree']:>6.2f} {m['giant_component_frac']:>5.2f} │ "
                      f"{m['cycles_per_node']:>6.3f} {m['tri_per_node']:>5.3f} │ "
                      f"{m['mean_clustering']:>5.3f} {m['degree_entropy']:>4.2f} │ "
                      f"{m['dimension']:>5.2f}")
                
                m['step'] = step
                history.append(m)
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("ACTIVATION TIME ANALYSIS")
    print("=" * 75)
    print()
    
    # Define activation thresholds (when a branch "turns on")
    thresholds = {
        # Branch 1
        'mean_degree': 3.0,
        'giant_component_frac': 0.5,
        # Branch 2
        'cycles_per_node': 0.3,
        'tri_per_node': 0.5,
        # Branch 3
        'mean_clustering': 0.2,
        'degree_entropy': 1.5,
    }
    
    print("Activation times (first step where metric exceeds threshold):")
    print()
    
    activation_times = {}
    for metric, threshold in thresholds.items():
        t = detect_activation_time(history, metric, threshold)
        activation_times[metric] = t
        status = f"step {t}" if t > 0 else "NOT REACHED"
        print(f"  {metric:25s} (>{threshold:4.1f}): {status}")
    
    print()
    print("=" * 75)
    print("LAG STRUCTURE ANALYSIS")
    print("=" * 75)
    print()
    
    # Compute branch activation order
    branch1_metrics = ['mean_degree', 'giant_component_frac']
    branch2_metrics = ['cycles_per_node', 'tri_per_node']
    branch3_metrics = ['mean_clustering', 'degree_entropy']
    
    def branch_activation_time(metrics):
        times = [activation_times[m] for m in metrics if activation_times[m] > 0]
        return np.mean(times) if times else float('inf')
    
    t1 = branch_activation_time(branch1_metrics)
    t2 = branch_activation_time(branch2_metrics)
    t3 = branch_activation_time(branch3_metrics)
    
    print(f"Branch 1 (Connectivity) mean activation: {t1:.0f}")
    print(f"Branch 2 (Loops)        mean activation: {t2:.0f}")
    print(f"Branch 3 (Higher-order) mean activation: {t3:.0f}")
    print()
    
    if t1 < t2 < t3:
        print("RESULT: Branch activation follows expected order (1 → 2 → 3)")
        print("        Supports staggered branch development hypothesis.")
        lag_12 = t2 - t1
        lag_23 = t3 - t2
        print(f"        Lag 1→2: {lag_12:.0f} steps")
        print(f"        Lag 2→3: {lag_23:.0f} steps")
    elif t1 < t2:
        print("RESULT: Partial ordering (Branch 1 before Branch 2)")
        print("        Branch 3 may require longer runs or stronger driving.")
    else:
        print("RESULT: No clear ordering detected.")
        print("        Branches may activate simultaneously or data is insufficient.")
    
    print()
    print("=" * 75)
    print("DIMENSION VS BRANCH ACTIVATION")
    print("=" * 75)
    print()
    
    # Only analyze peak states (population > 100)
    peaks = [h for h in history if h['n'] > 100]
    
    if len(peaks) >= 3:
        dims = [h['dimension'] for h in peaks]
        
        # Correlation with each branch's metrics
        print("Correlation of dimension with branch metrics (peak states only):")
        print()
        
        for metric in ['mean_degree', 'giant_component_frac', 'cycles_per_node', 
                       'tri_per_node', 'mean_clustering', 'degree_entropy']:
            values = [h[metric] for h in peaks]
            if len(set(values)) > 1:
                r, p = pearsonr(values, dims)
                branch = "B1" if metric in branch1_metrics else ("B2" if metric in branch2_metrics else "B3")
                print(f"  [{branch}] {metric:25s}: r = {r:+.3f} (p = {p:.3f})")
        
        print()
        
        # Which branch predicts dimension best?
        correlations = []
        for metric in ['mean_degree', 'cycles_per_node', 'mean_clustering']:
            values = [h[metric] for h in peaks]
            if len(set(values)) > 1:
                r, _ = pearsonr(values, dims)
                correlations.append((metric, abs(r)))
        
        if correlations:
            best = max(correlations, key=lambda x: x[1])
            print(f"Best predictor of dimension: {best[0]} (|r| = {best[1]:.3f})")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_branch_activation_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'staggered_branch_activation',
            'hypothesis': 'Spacetime expansion is asynchronous branch development',
            'history': history,
            'activation_times': activation_times,
            'branch_means': {
                'branch1': t1 if t1 != float('inf') else None,
                'branch2': t2 if t2 != float('inf') else None,
                'branch3': t3 if t3 != float('inf') else None,
            }
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, activation_times


if __name__ == "__main__":
    history, activation_times = run_branch_activation_test()
