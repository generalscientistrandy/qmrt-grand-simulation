"""
Phase 11b: Branch Development Sequence Test
============================================

REFINED APPROACH:
The previous test showed all branches activating simultaneously because
the system was pre-seeded with rich structure. 

This test tracks the DEVELOPMENTAL SEQUENCE within a single build-up cycle:
  - Start with minimal seeding
  - Watch how structure develops from scratch
  - Track the ORDER in which different organizational features emerge

KEY QUESTION:
When the medium builds up from a low state to a peak state, do different 
organizational features emerge in a specific sequence?

PREDICTION (Staggered Activation Hypothesis):
  1. Connectivity forms first (nodes connect)
  2. Loops emerge second (cycles close)
  3. Higher-order clustering emerges last (local neighborhoods densify)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class MinimalSeedSimulator:
    """Simulator with minimal seeding to observe developmental sequence."""
    
    def __init__(self, size: int = 48, injection_interval: int = 50):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 2  # Fewer injections for slower build-up
        
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


def measure_development_metrics(defects, size) -> Dict:
    """
    Measure developmental state of each organizational branch.
    Returns NORMALIZED metrics (0-1 scale) for comparing activation rates.
    """
    n = len(defects)
    
    if n < 5:
        return {
            'valid': False, 
            'n': n,
            # Return zeros for all metrics when insufficient data
            'connectivity_score': 0,
            'loop_score': 0,
            'clustering_score': 0,
            'mean_degree': 0,
            'cycles_per_node': 0,
            'mean_clustering': 0,
        }
    
    max_n = min(n, 60)
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
    
    # === Branch 1: CONNECTIVITY ===
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    degrees = [len(adj[i]) for i in range(max_n)]
    mean_degree = np.mean(degrees) if degrees else 0
    
    # Normalized connectivity: degree / max possible degree
    max_degree = max_n - 1
    connectivity_score = mean_degree / max_degree if max_degree > 0 else 0
    
    # === Branch 2: LOOPS ===
    # Find components
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
    
    cycle_rank = edges - max_n + n_components
    cycles_per_node = cycle_rank / max_n if max_n > 0 else 0
    
    # Normalized loop score: cycles / nodes (capped at 1)
    loop_score = min(cycles_per_node, 1.0)
    
    # === Branch 3: CLUSTERING ===
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
    clustering_score = mean_clustering  # Already 0-1
    
    return {
        'valid': True,
        'n': n,
        # Raw metrics
        'mean_degree': mean_degree,
        'cycles_per_node': cycles_per_node,
        'mean_clustering': mean_clustering,
        # Normalized scores (0-1)
        'connectivity_score': connectivity_score,
        'loop_score': loop_score,
        'clustering_score': clustering_score,
    }


def run_developmental_sequence_test():
    """
    Track the developmental sequence as the medium builds up from minimal state.
    
    KEY QUESTION: When population grows, which organizational features emerge first?
    """
    print("=" * 75)
    print("  PHASE 11b: BRANCH DEVELOPMENT SEQUENCE TEST")
    print("=" * 75)
    print()
    print("Starting from MINIMAL seeding to observe developmental sequence.")
    print("Question: Do branches develop in a specific order as the medium builds up?")
    print()
    
    sim = MinimalSeedSimulator(size=48, injection_interval=50)
    
    np.random.seed(42)
    sim.psi_r += 0.02 * np.random.randn(48, 48, 48)  # Minimal noise
    sim.psi_i += 0.02 * np.random.randn(48, 48, 48)
    
    # Minimal initial seeding (just 3 vortices)
    center = 24
    sim.inject_vortex(center, center)
    sim.inject_vortex(center + 5, center)
    sim.inject_vortex(center, center + 5)
    
    print(f"{'Step':>5} {'Pop':>4} │ {'Conn':>5} {'Loop':>5} {'Clust':>5} │ "
          f"{'Lead':>6}")
    print("-" * 55)
    
    history = []
    
    # Fine-grained sampling during build-up (every 30 steps)
    for step in range(900):
        sim.step()
        
        if step % 30 == 0:
            defects = sim.detect_defects()
            m = measure_development_metrics(defects, sim.size)
            
            # Determine which branch is "leading"
            scores = {
                'Conn': m['connectivity_score'],
                'Loop': m['loop_score'],
                'Clust': m['clustering_score'],
            }
            lead = max(scores, key=scores.get) if m['n'] > 0 else '-'
            
            print(f"{step:>5} {m['n']:>4} │ "
                  f"{m['connectivity_score']:>5.3f} {m['loop_score']:>5.3f} "
                  f"{m['clustering_score']:>5.3f} │ {lead:>6}")
            
            m['step'] = step
            m['lead'] = lead
            history.append(m)
    
    # === SEQUENCE ANALYSIS ===
    print()
    print("=" * 75)
    print("DEVELOPMENTAL SEQUENCE ANALYSIS")
    print("=" * 75)
    print()
    
    # Find first step where each branch exceeds threshold
    thresholds = {
        'connectivity_score': 0.05,
        'loop_score': 0.1,
        'clustering_score': 0.15,
    }
    
    activation_order = []
    for metric, thresh in thresholds.items():
        for h in history:
            if h.get(metric, 0) >= thresh:
                activation_order.append((metric.replace('_score', ''), h['step']))
                break
    
    # Sort by step
    activation_order.sort(key=lambda x: x[1])
    
    print("Activation sequence (order in which branches cross threshold):")
    for i, (metric, step) in enumerate(activation_order, 1):
        print(f"  {i}. {metric:15s} activated at step {step}")
    
    print()
    
    # Analyze build-up phase (when population is growing)
    build_up_phases = []
    for i in range(1, len(history)):
        if history[i]['n'] > history[i-1]['n'] + 10:  # Population increasing
            build_up_phases.append(history[i])
    
    if build_up_phases:
        print(f"Build-up phases detected: {len(build_up_phases)} samples")
        
        # Average lead branch during build-up
        lead_counts = defaultdict(int)
        for h in build_up_phases:
            lead_counts[h['lead']] += 1
        
        print(f"Lead branch during build-up:")
        for branch, count in sorted(lead_counts.items(), key=lambda x: -x[1]):
            pct = 100 * count / len(build_up_phases)
            print(f"  {branch}: {count} ({pct:.1f}%)")
    
    print()
    print("=" * 75)
    print("BRANCH RATE COMPARISON")
    print("=" * 75)
    print()
    
    # Compute average rate of change for each branch
    def compute_rate(history, metric):
        values = [(h['step'], h[metric]) for h in history if h['n'] > 20]
        if len(values) < 3:
            return 0
        steps = [v[0] for v in values]
        vals = [v[1] for v in values]
        # Linear fit
        if len(set(steps)) > 1:
            slope = np.polyfit(steps, vals, 1)[0]
            return slope * 100  # Rate per 100 steps
        return 0
    
    conn_rate = compute_rate(history, 'connectivity_score')
    loop_rate = compute_rate(history, 'loop_score')
    clust_rate = compute_rate(history, 'clustering_score')
    
    print(f"Development rates (per 100 steps):")
    print(f"  Connectivity: {conn_rate:+.4f}")
    print(f"  Loop:         {loop_rate:+.4f}")
    print(f"  Clustering:   {clust_rate:+.4f}")
    
    if conn_rate > loop_rate > clust_rate:
        print()
        print("RESULT: Connectivity develops fastest, clustering slowest.")
        print("        Supports staggered branch activation hypothesis.")
    elif conn_rate > 0 and loop_rate > 0 and clust_rate > 0:
        print()
        print("RESULT: All branches developing. Rates suggest different dynamics.")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_development_sequence_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'branch_development_sequence',
            'hypothesis': 'Branches develop at different rates during medium build-up',
            'history': history,
            'activation_order': activation_order,
            'development_rates': {
                'connectivity': conn_rate,
                'loop': loop_rate,
                'clustering': clust_rate,
            }
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history


if __name__ == "__main__":
    history = run_developmental_sequence_test()
