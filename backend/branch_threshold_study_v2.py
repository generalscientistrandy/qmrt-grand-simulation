"""
Branch-Transition Threshold Study v2
=====================================

REVISED METHODOLOGY based on diagnostic insight:
The system needs significant time to build into its sustained branch.
Early measurements capture build-up phase, not regime characteristics.

KEY CHANGES:
1. Population-threshold equilibration (wait for n > 150, not fixed steps)
2. Measure ONLY late-time windows
3. Track TIME-TO-BRANCH as a key metric
4. Longer total runtime per interval

NEW QUESTION:
For each driving rate, does the system eventually enter the richer ~2D-like 
branch, and how long does it take?

BRANCH-STATE CLASSIFICATION:
- pre_branch_sparse: Population never exceeds threshold
- filamentary_branch: Stable ~1D organization (d < 1.4)
- enriched_2D_like: Stable ~2D organization (d > 1.5, tri/n > 0.5, corr > 0.5)
- runaway_overflow: Population exceeds measurement cap
- unstable_oscillating: High population variance, no stable branch
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import time
import json


# Revised Constants
POPULATION_THRESHOLD = 150  # Minimum population to consider "branched"
POPULATION_CAP = 400        # Measurement truncation (for sampling)
MAX_EQUILIBRATION_STEPS = 4000  # Maximum steps to wait for branching
MEASUREMENT_WINDOWS = 5     # Number of late-time windows
STEPS_PER_WINDOW = 200      # Steps per measurement window
SAMPLES_PER_WINDOW = 5      # Measurements per window
TIMEOUT_SECONDS = 90        # Per interval timeout (longer for proper equilibration)


class BranchStudySimulator:
    """Simulator for branch-transition study."""
    
    def __init__(self, size: int = 48, injection_interval: int = 50, injection_count: int = 3):
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


def measure_state(defects, size) -> Dict:
    """Measure all relevant metrics for a single snapshot."""
    n = len(defects)
    
    if n < 10:
        return {'valid': False, 'n': n, 'reason': 'population_too_small'}
    
    # Sample for large populations
    MAX_SAMPLE = 200
    if n > MAX_SAMPLE:
        indices = np.random.choice(n, MAX_SAMPLE, replace=False)
        sampled_defects = [defects[i] for i in indices]
        n_sampled = MAX_SAMPLE
    else:
        sampled_defects = defects
        n_sampled = n
    
    # Build adjacency
    adj = defaultdict(set)
    for i in range(n_sampled):
        for j in range(i + 1, n_sampled):
            d = euclidean_distance_periodic(sampled_defects[i], sampled_defects[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    edges = sum(len(adj[i]) for i in range(n_sampled)) // 2
    degrees = [len(adj[i]) for i in range(n_sampled)]
    mean_degree = np.mean(degrees) if degrees else 0
    
    # Triangles and clustering
    triangles = 0
    clustering_sum = 0
    clustering_count = 0
    
    for node in range(n_sampled):
        neighbors = list(adj[node])
        k = len(neighbors)
        local_tri = sum(1 for i in range(len(neighbors)) 
                       for j in range(i+1, len(neighbors)) 
                       if neighbors[j] in adj[neighbors[i]])
        triangles += local_tri
        if k >= 2:
            clustering_sum += local_tri / (k * (k-1) / 2)
            clustering_count += 1
    
    triangles //= 3
    clustering = clustering_sum / clustering_count if clustering_count > 0 else 0
    tri_per_node = triangles / n_sampled if n_sampled > 0 else 0
    
    # Graph distances (limited sources for efficiency)
    max_sources = min(n_sampled, 50)
    graph_dist = np.full((max_sources, n_sampled), np.inf)
    
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
    euclidean_dists = []
    graph_dists = []
    for idx in range(max_sources):
        for j in range(idx + 1, n_sampled):
            if graph_dist[idx, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(sampled_defects[idx], sampled_defects[j], size))
                graph_dists.append(graph_dist[idx, j])
    
    correlation = pearsonr(euclidean_dists, graph_dists)[0] if len(euclidean_dists) >= 10 else 0
    
    # Dimension
    radii = list(range(1, 6))
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
        'clustering': clustering,
        'correlation': correlation,
        'dimension': dimension,
        'mean_degree': mean_degree,
    }


def classify_branch_state(windows: List[Dict], time_to_branch: Optional[int], 
                          branched: bool, cap_hit_count: int) -> str:
    """
    Classify the branch state based on late-time windows.
    """
    if not branched:
        return 'pre_branch_sparse'
    
    if not windows:
        return 'inconclusive'
    
    valid = [w for w in windows if w.get('valid', False)]
    if not valid:
        return 'inconclusive'
    
    dims = [w['dimension'] for w in valid]
    pops = [w['n'] for w in valid]
    corrs = [w['correlation'] for w in valid]
    tri_per_nodes = [w['tri_per_node'] for w in valid]
    
    mean_dim = np.mean(dims)
    mean_pop = np.mean(pops)
    mean_corr = np.mean(corrs)
    mean_tri = np.mean(tri_per_nodes)
    pop_cv = np.std(pops) / (mean_pop + 1e-10)
    
    # Runaway check
    if cap_hit_count > len(windows) // 2:
        return 'runaway_overflow'
    
    # Unstable oscillating
    if pop_cv > 0.5:
        return 'unstable_oscillating'
    
    # Enriched 2D-like: dimension > 1.5, triangles enriched, correlation strong
    if mean_dim > 1.5 and mean_tri > 0.5 and mean_corr > 0.5:
        return 'enriched_2D_like'
    
    # Filamentary: dimension < 1.4, correlation strong
    if mean_dim < 1.4 and mean_corr > 0.5:
        return 'filamentary_branch'
    
    # Transitional
    if 1.3 < mean_dim < 1.6:
        return 'transitional'
    
    # Sparse artifact check
    if mean_dim > 1.3 and mean_corr < 0.4:
        return 'sparse_artifact'
    
    return 'inconclusive'


def run_single_interval_v2(injection_interval: int) -> Dict:
    """
    Run a single driving interval with proper equilibration.
    
    Key features:
    1. Wait for population to cross threshold (or max steps)
    2. Measure ONLY late-time windows after branching
    3. Track time-to-branch
    """
    start_time = time.time()
    
    result = {
        'interval': injection_interval,
        'driving_rate': 3.0 / injection_interval,
        'branched': False,
        'time_to_branch': None,
        'cap_hit_count': 0,
        'windows': [],
        'population_history': [],  # Track build-up
    }
    
    try:
        sim = BranchStudySimulator(size=48, injection_interval=injection_interval, injection_count=3)
        
        np.random.seed(42)
        sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
        
        # Light initial seeding
        center = 24
        for i in range(-2, 3):
            for j in range(-2, 3):
                if abs(i) + abs(j) <= 2:
                    sim.inject_vortex(center + i * 6, center + j * 6)
        
        # PHASE 1: Wait for branching (population threshold)
        branch_step = None
        for step in range(MAX_EQUILIBRATION_STEPS):
            sim.step()
            
            if time.time() - start_time > TIMEOUT_SECONDS:
                result['timeout_hit'] = True
                break
            
            # Check population every 100 steps
            if step % 100 == 0:
                defects = sim.detect_defects()
                n = len(defects)
                result['population_history'].append({'step': step, 'n': n})
                
                if n >= POPULATION_THRESHOLD and branch_step is None:
                    branch_step = step
                    result['branched'] = True
                    result['time_to_branch'] = step
        
        if not result['branched']:
            result['branch_state'] = 'pre_branch_sparse'
            result['elapsed_seconds'] = time.time() - start_time
            return result
        
        # PHASE 2: Measure late-time windows
        windows = []
        for window_idx in range(MEASUREMENT_WINDOWS):
            window_measurements = []
            
            for step in range(STEPS_PER_WINDOW):
                sim.step()
                
                if time.time() - start_time > TIMEOUT_SECONDS:
                    result['timeout_hit'] = True
                    break
                
                # Sample periodically
                if step % (STEPS_PER_WINDOW // SAMPLES_PER_WINDOW) == 0:
                    defects = sim.detect_defects()
                    n = len(defects)
                    
                    if n >= POPULATION_CAP:
                        result['cap_hit_count'] += 1
                        m = measure_state(defects[:POPULATION_CAP], sim.size)
                        m['cap_hit'] = True
                    else:
                        m = measure_state(defects, sim.size)
                        m['cap_hit'] = False
                    
                    window_measurements.append(m)
            
            if result.get('timeout_hit'):
                break
            
            # Aggregate window
            valid = [m for m in window_measurements if m.get('valid', False)]
            if valid:
                windows.append({
                    'window_idx': window_idx,
                    'valid': True,
                    'n': np.mean([m['n'] for m in valid]),
                    'n_std': np.std([m['n'] for m in valid]),
                    'dimension': np.mean([m['dimension'] for m in valid]),
                    'dim_std': np.std([m['dimension'] for m in valid]),
                    'triangles': np.mean([m['triangles'] for m in valid]),
                    'tri_per_node': np.mean([m['tri_per_node'] for m in valid]),
                    'clustering': np.mean([m['clustering'] for m in valid]),
                    'correlation': np.mean([m['correlation'] for m in valid]),
                })
        
        result['windows'] = windows
        result['branch_state'] = classify_branch_state(
            windows, result['time_to_branch'], result['branched'], result['cap_hit_count']
        )
        
        # Late-time summary
        if windows:
            late = windows[-min(3, len(windows)):]
            valid_late = [w for w in late if w.get('valid', False)]
            if valid_late:
                result['summary'] = {
                    'final_population': np.mean([w['n'] for w in valid_late]),
                    'final_dimension': np.mean([w['dimension'] for w in valid_late]),
                    'final_dim_std': np.mean([w['dim_std'] for w in valid_late]),
                    'final_triangles': np.mean([w['triangles'] for w in valid_late]),
                    'final_tri_per_node': np.mean([w['tri_per_node'] for w in valid_late]),
                    'final_correlation': np.mean([w['correlation'] for w in valid_late]),
                }
        
    except Exception as e:
        result['error'] = str(e)
        result['branch_state'] = 'error'
    
    result['elapsed_seconds'] = time.time() - start_time
    return result


def run_branch_threshold_study_v2():
    """
    Run the revised branch-transition threshold study.
    
    Key question: For each driving rate, does the system eventually enter 
    the richer ~2D-like branch, and how long does it take?
    """
    print("=" * 75)
    print("  BRANCH-TRANSITION THRESHOLD STUDY v2")
    print("  (With proper equilibration and time-to-branch tracking)")
    print("=" * 75)
    print()
    print(f"Population threshold for branching: {POPULATION_THRESHOLD}")
    print(f"Max equilibration steps: {MAX_EQUILIBRATION_STEPS}")
    print(f"Measurement windows: {MEASUREMENT_WINDOWS} × {STEPS_PER_WINDOW} steps")
    print(f"Timeout per interval: {TIMEOUT_SECONDS}s")
    print()
    
    # Test across driving intervals
    intervals = [50, 75, 100, 150, 200, 300, 500, 750, 1000]
    results = []
    
    print("-" * 75)
    print(f"{'Interval':>8} {'Rate':>8} {'Branch?':>8} {'T_branch':>10} {'Pop':>6} "
          f"{'Dim':>6} {'Tri/N':>6} {'State':>22}")
    print("-" * 75)
    
    for interval in intervals:
        result = run_single_interval_v2(interval)
        results.append(result)
        
        if result.get('summary'):
            s = result['summary']
            t_branch = result.get('time_to_branch', '---')
            if t_branch is not None:
                t_branch = f"{t_branch:>6}"
            print(f"{interval:>8} {result['driving_rate']:>8.4f} "
                  f"{'YES':>8} {t_branch:>10} "
                  f"{s['final_population']:>6.0f} {s['final_dimension']:>6.2f} "
                  f"{s['final_tri_per_node']:>6.2f} {result['branch_state']:>22}")
        else:
            t_branch = result.get('time_to_branch', '---')
            print(f"{interval:>8} {result['driving_rate']:>8.4f} "
                  f"{'NO':>8} {'---':>10} "
                  f"{'---':>6} {'---':>6} "
                  f"{'---':>6} {result['branch_state']:>22}")
    
    # Analysis
    print()
    print("=" * 75)
    print("ANALYSIS: Time-to-Branch vs Driving Rate")
    print("=" * 75)
    print()
    
    branched = [r for r in results if r['branched'] and r.get('time_to_branch')]
    if branched:
        print(f"{'Interval':>8} {'Rate':>10} {'Time-to-Branch':>15} {'Final Dim':>12}")
        print("-" * 50)
        for r in sorted(branched, key=lambda x: x['interval']):
            dim = r['summary']['final_dimension'] if r.get('summary') else 0
            print(f"{r['interval']:>8} {r['driving_rate']:>10.4f} "
                  f"{r['time_to_branch']:>15} {dim:>12.2f}")
        
        # Correlation between driving rate and time-to-branch
        rates = [r['driving_rate'] for r in branched]
        times = [r['time_to_branch'] for r in branched]
        if len(rates) >= 3:
            corr = pearsonr(rates, times)[0]
            print()
            print(f"Correlation (driving rate vs time-to-branch): {corr:.3f}")
            if corr < -0.5:
                print("→ Higher driving = faster branching (expected)")
            elif corr > 0.5:
                print("→ Higher driving = slower branching (unexpected)")
            else:
                print("→ No strong relationship")
    
    # Branch state distribution
    print()
    print("-" * 75)
    print("BRANCH STATE DISTRIBUTION")
    print("-" * 75)
    
    states = defaultdict(list)
    for r in results:
        states[r.get('branch_state', 'unknown')].append(r['interval'])
    
    for state, intervals_list in sorted(states.items()):
        print(f"  {state}: intervals {intervals_list}")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/branch_threshold_study_v2_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study_version': 'v2',
            'parameters': {
                'population_threshold': POPULATION_THRESHOLD,
                'max_equilibration_steps': MAX_EQUILIBRATION_STEPS,
                'measurement_windows': MEASUREMENT_WINDOWS,
                'steps_per_window': STEPS_PER_WINDOW,
            },
            'results': results,
        }, f, indent=2, default=str)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    results = run_branch_threshold_study_v2()
