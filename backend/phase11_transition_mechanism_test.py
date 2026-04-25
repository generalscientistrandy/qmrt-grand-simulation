"""
Phase 11d: Transition Mechanism Investigation
==============================================

QUESTION: What drives the Loop → Clustering transition at ~400 defects?

CANDIDATE MECHANISMS:

1. GEOMETRIC (Packing/Crowding)
   - At high density, nodes are closer together
   - More triangles form automatically
   - Loops become "filled in" by clustering
   - TEST: Compute average inter-node distance at transition

2. REMNANT FIELD (Memory-Mediated)
   - Remnant field accumulates where defects have been
   - Could bias toward clustering in high-remnant regions
   - TEST: Compare remnant field intensity at transition

3. CHANNEL ASSIGNMENT (Topological Memory)
   - Channel assignment builds up over time
   - Could change how new structure forms
   - TEST: Compare channel assignment at transition

4. τ FIELD (Dynamic Medium)
   - τ responds to energy density
   - Could change effective dynamics at high population
   - TEST: Compare τ distribution at transition

5. HYBRID (Population-Dependent Threshold)
   - Combination of above factors crossing a threshold
   - TEST: Multi-factor correlation analysis

APPROACH:
Track all candidate variables alongside Loop-vs-Clustering ratio.
Identify which variable(s) correlate most strongly with the transition.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr, spearmanr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class TransitionMechanismSimulator:
    """Simulator with full diagnostics for transition mechanism analysis."""
    
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
    
    def get_field_diagnostics(self, defects) -> Dict:
        """Get diagnostic information about medium state."""
        # τ field statistics
        tau_mean = float(np.mean(self.tau))
        tau_std = float(np.std(self.tau))
        tau_max = float(np.max(self.tau))
        
        # Remnant field statistics
        remnant_mean = float(np.mean(self.remnant_field))
        remnant_max = float(np.max(self.remnant_field))
        remnant_coverage = float(np.mean(self.remnant_field > 0.1))  # Fraction > 0.1
        
        # Channel assignment statistics
        channel_mean = float(np.mean(self.channel_assignment))
        channel_max = float(np.max(self.channel_assignment))
        channel_coverage = float(np.mean(self.channel_assignment > 0.1))
        
        # Sample field values at defect locations
        if len(defects) > 0:
            tau_at_defects = [self.tau[d[0], d[1], d[2]] for d in defects[:50]]
            remnant_at_defects = [self.remnant_field[d[0], d[1], d[2]] for d in defects[:50]]
            channel_at_defects = [self.channel_assignment[d[0], d[1], d[2]] for d in defects[:50]]
            
            tau_defect_mean = float(np.mean(tau_at_defects))
            remnant_defect_mean = float(np.mean(remnant_at_defects))
            channel_defect_mean = float(np.mean(channel_at_defects))
        else:
            tau_defect_mean = 0
            remnant_defect_mean = 0
            channel_defect_mean = 0
        
        return {
            'tau_mean': tau_mean,
            'tau_std': tau_std,
            'tau_max': tau_max,
            'tau_defect_mean': tau_defect_mean,
            'remnant_mean': remnant_mean,
            'remnant_max': remnant_max,
            'remnant_coverage': remnant_coverage,
            'remnant_defect_mean': remnant_defect_mean,
            'channel_mean': channel_mean,
            'channel_max': channel_max,
            'channel_coverage': channel_coverage,
            'channel_defect_mean': channel_defect_mean,
        }


def euclidean_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_graph_metrics(defects, size) -> Dict:
    """Measure graph metrics including average inter-node distance."""
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
    
    # Compute all pairwise distances
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
    min_distance = np.min(distances) if distances else 0
    
    # Density metric: how tightly packed
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
    
    # Loop vs Clustering ratio
    loop_vs_clust = cycles_per_node - mean_clustering
    
    return {
        'valid': True,
        'n': n,
        'avg_distance': avg_distance,
        'min_distance': min_distance,
        'density': density,
        'mean_degree': mean_degree,
        'cycles_per_node': cycles_per_node,
        'mean_clustering': mean_clustering,
        'loop_vs_clust': loop_vs_clust,
    }


def run_transition_mechanism_test():
    """
    Identify what drives the Loop → Clustering transition.
    
    Track candidate variables and correlate with L-C ratio.
    """
    print("=" * 75)
    print("  PHASE 11d: TRANSITION MECHANISM INVESTIGATION")
    print("=" * 75)
    print()
    print("Question: What drives the ~400-defect transition?")
    print()
    print("Candidates: Geometric packing, Remnant field, Channel memory, τ field")
    print()
    
    sim = TransitionMechanismSimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Moderate seeding
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    print(f"{'Step':>5} {'Pop':>4} │ {'AvgDist':>7} {'Density':>7} │ "
          f"{'RemCov':>6} {'ChanCov':>7} │ {'L-C':>6}")
    print("-" * 65)
    
    history = []
    
    for step in range(1200):
        sim.step()
        
        if step % 40 == 0:
            defects = sim.detect_defects()
            graph = measure_graph_metrics(defects, sim.size)
            field = sim.get_field_diagnostics(defects)
            
            if graph['valid']:
                m = {**graph, **field, 'step': step}
                
                print(f"{step:>5} {m['n']:>4} │ "
                      f"{m['avg_distance']:>7.2f} {m['density']:>7.4f} │ "
                      f"{m['remnant_coverage']:>6.3f} {m['channel_coverage']:>7.3f} │ "
                      f"{m['loop_vs_clust']:>+6.3f}")
                
                history.append(m)
    
    # === CORRELATION ANALYSIS ===
    print()
    print("=" * 75)
    print("CORRELATION ANALYSIS: What predicts Loop-vs-Clustering?")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n'] > 50]
    
    if len(valid) >= 5:
        lc = [h['loop_vs_clust'] for h in valid]
        
        candidates = [
            ('Population', [h['n'] for h in valid]),
            ('Avg Distance', [h['avg_distance'] for h in valid]),
            ('Density', [h['density'] for h in valid]),
            ('Remnant Coverage', [h['remnant_coverage'] for h in valid]),
            ('Remnant at Defects', [h['remnant_defect_mean'] for h in valid]),
            ('Channel Coverage', [h['channel_coverage'] for h in valid]),
            ('Channel at Defects', [h['channel_defect_mean'] for h in valid]),
            ('τ at Defects', [h['tau_defect_mean'] for h in valid]),
            ('τ Std', [h['tau_std'] for h in valid]),
        ]
        
        print(f"{'Variable':25s} │ {'Pearson r':>10} {'p-value':>10} │ {'Spearman ρ':>10}")
        print("-" * 65)
        
        correlations = []
        for name, values in candidates:
            if len(set(values)) > 1:
                r_p, p_p = pearsonr(values, lc)
                r_s, p_s = spearmanr(values, lc)
                print(f"{name:25s} │ {r_p:>+10.3f} {p_p:>10.3f} │ {r_s:>+10.3f}")
                correlations.append((name, r_p, p_p, r_s))
        
        print()
        print("=" * 75)
        print("MECHANISM IDENTIFICATION")
        print("=" * 75)
        print()
        
        # Find strongest predictor
        by_strength = sorted(correlations, key=lambda x: abs(x[1]), reverse=True)
        
        print("Ranked by |correlation| with Loop-vs-Clustering:")
        for i, (name, r, p, rs) in enumerate(by_strength[:5], 1):
            sig = "*" if p < 0.05 else ""
            print(f"  {i}. {name:25s}: r = {r:+.3f} {sig}")
        
        best = by_strength[0]
        print()
        
        if 'Distance' in best[0] or 'Density' in best[0]:
            print(f"PRIMARY DRIVER: GEOMETRIC ({best[0]})")
            print()
            print("Interpretation: The transition is driven by packing effects.")
            print("As population increases, nodes get closer together,")
            print("which automatically creates more triangles (clustering).")
            mechanism = 'geometric'
        elif 'Remnant' in best[0]:
            print(f"PRIMARY DRIVER: REMNANT FIELD ({best[0]})")
            print()
            print("Interpretation: The transition is memory-mediated.")
            print("Accumulated remnant field biases structure formation")
            print("toward clustering in high-memory regions.")
            mechanism = 'remnant'
        elif 'Channel' in best[0]:
            print(f"PRIMARY DRIVER: CHANNEL MEMORY ({best[0]})")
            print()
            print("Interpretation: The transition is topology-memory-mediated.")
            print("Channel assignment builds up and changes how new")
            print("structure forms, favoring local clustering.")
            mechanism = 'channel'
        elif 'τ' in best[0]:
            print(f"PRIMARY DRIVER: τ FIELD ({best[0]})")
            print()
            print("Interpretation: The transition is medium-dynamics-mediated.")
            print("τ field variations at high population change effective")
            print("wave speed, altering how structure organizes.")
            mechanism = 'tau'
        elif 'Population' in best[0]:
            print(f"PRIMARY DRIVER: POPULATION DIRECTLY ({best[0]})")
            print()
            print("Interpretation: The transition is a pure population effect.")
            print("May indicate a more fundamental threshold behavior.")
            mechanism = 'population'
        else:
            print(f"PRIMARY DRIVER: {best[0]}")
            mechanism = 'unknown'
        
        # Check for hybrid
        print()
        significant = [c for c in correlations if abs(c[1]) > 0.3]
        if len(significant) > 1:
            print(f"Note: {len(significant)} variables show |r| > 0.3")
            print("This suggests a HYBRID mechanism involving multiple factors:")
            for name, r, p, rs in significant:
                print(f"  - {name}: r = {r:+.3f}")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_transition_mechanism_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'transition_mechanism_investigation',
            'question': 'What drives the Loop→Clustering transition at ~400 defects?',
            'history': history,
            'correlations': [(c[0], c[1], c[2]) for c in correlations] if 'correlations' in dir() else [],
            'primary_mechanism': mechanism if 'mechanism' in dir() else 'unknown',
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history


if __name__ == "__main__":
    history = run_transition_mechanism_test()
