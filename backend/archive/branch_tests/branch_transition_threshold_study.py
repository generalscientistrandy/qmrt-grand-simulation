"""
Branch-Transition Threshold Study
==================================

OBJECTIVE: Identify whether there is a thresholded transition from a 
filamentary ~1D scaffold to a denser, loop-rich ~2D-like organizational 
branch under sustained driving.

This is NOT a simple parameter sweep. It is a physics experiment where
even failures (collapse, runaway) are informative data.

EXPERIMENTAL DESIGN (per user refinement):

1. OUTCOME CLASSIFICATION per interval:
   - collapse: Population drops to <10 and stays there
   - stable_filamentary: Dimension ~1.0-1.3, stable population
   - stable_2D_like: Dimension >1.5, elevated triangles, strong correlation
   - runaway_overflow: Population exceeds cap
   - inconclusive: Compute limits reached without stable outcome

2. TWO-PASS DESIGN:
   - Coarse scan: 150, 120, 100, 80, 60, 50, 40, 30
   - Refinement scan: Around any detected jump (e.g., 55, 50, 45, 40, 35)

3. POPULATION CAP as measurement truncation:
   - Cap at 500 nodes (measurement limit, not physical rule)
   - Log when cap is hit

4. CORE METRICS (windowed late-time statistics):
   - Population (final + windowed mean)
   - Effective dimension
   - Graph-Euclidean correlation
   - Edge count
   - Triangle count
   - Triangle-per-node (clustering enrichment indicator)
   - Regime classification
   - Whether cap/timeout was reached

5. KEY SIGNATURE for genuine 2D branch:
   - Dimension rises
   - Triangles rise
   - Correlation stays strong (>0.7)
   - WITHOUT sparse-network artifact (correlation < 0.3)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import time
import json


# Constants
POPULATION_CAP = 600  # Measurement truncation limit
WINDOW_STEPS = 150    # Steps per measurement window
NUM_WINDOWS = 4       # Number of late-time windows for statistics
EQUILIBRATION_STEPS = 300  # Equilibration steps
TIMEOUT_SECONDS = 35  # Per interval timeout (tighter)
MEASUREMENT_INTERVAL = 30  # Measure every 30 steps (5 samples per window)


class ThresholdStudySimulator:
    """Simulator with configurable driving rate and population monitoring."""
    
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


def measure_state(defects, size) -> Dict:
    """Measure all relevant metrics for a single snapshot."""
    n = len(defects)
    
    # Handle small populations
    if n < 10:
        return {
            'valid': False,
            'n': n,
            'reason': 'population_too_small'
        }
    
    # For very large populations, sample to keep computation tractable
    MAX_SAMPLE = 200
    if n > MAX_SAMPLE:
        indices = np.random.choice(n, MAX_SAMPLE, replace=False)
        sampled_defects = [defects[i] for i in indices]
        n_sampled = MAX_SAMPLE
        was_sampled = True
    else:
        sampled_defects = defects
        n_sampled = n
        was_sampled = False
    
    # Build adjacency (with edge distance threshold)
    adj = defaultdict(set)
    for i in range(n_sampled):
        for j in range(i + 1, n_sampled):
            d = euclidean_distance_periodic(sampled_defects[i], sampled_defects[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    # Basic counts
    edges = sum(len(adj[i]) for i in range(n_sampled)) // 2
    degrees = [len(adj[i]) for i in range(n_sampled)]
    mean_degree = np.mean(degrees) if degrees else 0
    
    # Triangles and clustering (optimized)
    triangles = 0
    clustering_sum = 0
    clustering_count = 0
    
    for node in range(n_sampled):
        neighbors = list(adj[node])
        k = len(neighbors)
        
        # Count triangles (only check pairs once per node)
        local_tri = 0
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    local_tri += 1
        triangles += local_tri
        
        # Local clustering coefficient
        if k >= 2:
            max_possible = k * (k - 1) / 2
            clustering_sum += local_tri / max_possible
            clustering_count += 1
    
    triangles //= 3  # Each triangle counted 3 times
    clustering = clustering_sum / clustering_count if clustering_count > 0 else 0
    
    # Triangle-per-node (key enrichment metric) - scale if sampled
    tri_per_node = triangles / n_sampled if n_sampled > 0 else 0
    
    # Graph distances via BFS (limited to sample)
    # For large graphs, only compute from a subset of sources
    max_sources = min(n_sampled, 50)
    source_indices = list(range(max_sources))
    
    graph_dist_sample = np.full((max_sources, n_sampled), np.inf)
    for idx, start in enumerate(source_indices):
        graph_dist_sample[idx, start] = 0
        queue = deque([start])
        visited = {start}
        while queue:
            node = queue.popleft()
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    graph_dist_sample[idx, neighbor] = graph_dist_sample[idx, node] + 1
                    queue.append(neighbor)
    
    # Graph-Euclidean correlation (using sample)
    euclidean_dists = []
    graph_dists = []
    for idx, i in enumerate(source_indices):
        for j in range(i + 1, n_sampled):
            if graph_dist_sample[idx, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(sampled_defects[i], sampled_defects[j], size))
                graph_dists.append(graph_dist_sample[idx, j])
    
    if len(euclidean_dists) >= 10:
        correlation = pearsonr(euclidean_dists, graph_dists)[0]
    else:
        correlation = 0
    
    # Effective dimension via graph radius scaling
    radii = list(range(1, 6))
    counts = []
    for r in radii:
        c = [np.sum((graph_dist_sample[idx, :] <= r) & (graph_dist_sample[idx, :] > 0)) 
             for idx in range(max_sources)]
        counts.append(np.mean(c))
    
    if min(counts) > 0 and len([c for c in counts if c > 0]) >= 2:
        log_r = np.log(radii)
        log_c = np.log(np.array(counts) + 1)
        coeffs = np.polyfit(log_r, log_c, 1)
        dimension = coeffs[0]
    else:
        dimension = 0
    
    return {
        'valid': True,
        'n': n,  # Report actual population
        'n_sampled': n_sampled,
        'was_sampled': was_sampled,
        'edges': edges,
        'triangles': triangles,
        'tri_per_node': tri_per_node,
        'clustering': clustering,
        'correlation': correlation,
        'dimension': dimension,
        'mean_degree': mean_degree,
    }


def classify_regime(windows: List[Dict]) -> str:
    """
    Classify the regime based on windowed statistics.
    
    Returns one of:
    - collapse: Population dropped and stayed low
    - stable_filamentary: Stable ~1D organization
    - stable_2D_like: Higher dimension with enriched structure
    - runaway_overflow: Population consistently hits cap
    - oscillatory_filamentary: Oscillating population, ~1D dimension
    - oscillatory_2D_like: Oscillating population, higher dimension
    - inconclusive: Unable to determine
    """
    if not windows:
        return 'inconclusive'
    
    # Check for cap hit frequency
    cap_hits = sum(1 for w in windows if w.get('cap_hit', False))
    cap_hit_ratio = cap_hits / len(windows)
    
    # Get late-window statistics
    valid_windows = [w for w in windows if w.get('valid', False)]
    
    if not valid_windows:
        return 'collapse'
    
    dims = [w['dimension'] for w in valid_windows]
    pops = [w['n'] for w in valid_windows]
    corrs = [w['correlation'] for w in valid_windows]
    tri_per_nodes = [w['tri_per_node'] for w in valid_windows]
    
    mean_dim = np.mean(dims)
    mean_pop = np.mean(pops)
    mean_corr = np.mean(corrs)
    mean_tri_per_node = np.mean(tri_per_nodes)
    
    # Detect oscillation via population CV
    pop_cv = np.std(pops) / (mean_pop + 1e-10)
    is_oscillating = pop_cv > 0.4
    
    # Collapse check
    if mean_pop < 15:
        return 'collapse'
    
    # Runaway check (>50% windows hit cap)
    if cap_hit_ratio > 0.5:
        return 'runaway_overflow'
    
    # 2D-like signature:
    # - Dimension > 1.5
    # - Triangles enriched (tri_per_node > 0.5)
    # - Correlation still strong (> 0.5, not sparse-network artifact)
    if mean_dim > 1.5 and mean_tri_per_node > 0.5 and mean_corr > 0.5:
        if is_oscillating:
            return 'oscillatory_2D_like'
        return 'stable_2D_like'
    
    # Filamentary check
    if 0.8 < mean_dim < 1.4 and mean_corr > 0.6:
        if is_oscillating:
            return 'oscillatory_filamentary'
        return 'stable_filamentary'
    
    # Transitional: dimension rising but not fully 2D
    if 1.3 < mean_dim < 1.6 and mean_corr > 0.5:
        if is_oscillating:
            return 'oscillatory_transitional'
        return 'transitional'
    
    # Check for sparse-network artifact (high dim but low correlation)
    if mean_dim > 1.3 and mean_corr < 0.4:
        return 'sparse_artifact'
    
    return 'inconclusive'


def compute_window_trend(windows: List[Dict], key: str) -> str:
    """Determine trend for a metric across windows."""
    values = [w[key] for w in windows if w.get('valid', False) and key in w]
    if len(values) < 3:
        return 'insufficient_data'
    
    # Simple linear trend
    x = np.arange(len(values))
    slope = np.polyfit(x, values, 1)[0]
    mean_val = np.mean(values)
    
    # Relative change per window
    rel_change = slope / (mean_val + 1e-10)
    
    if rel_change > 0.05:
        return 'rising'
    elif rel_change < -0.05:
        return 'falling'
    else:
        cv = np.std(values) / (mean_val + 1e-10)
        if cv > 0.2:
            return 'oscillating'
        return 'stable'


def run_single_interval(injection_interval: int, timeout_sec: float = TIMEOUT_SECONDS) -> Dict:
    """
    Run a single driving interval test with full diagnostics.
    """
    start_time = time.time()
    
    result = {
        'interval': injection_interval,
        'driving_rate': 3.0 / injection_interval,
        'valid': False,
        'timeout_hit': False,
        'cap_hit': False,
        'regime': 'not_started',
        'windows': [],
    }
    
    try:
        sim = ThresholdStudySimulator(size=48, injection_interval=injection_interval, injection_count=3)
        
        # Reproducible seed
        np.random.seed(42)
        sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
        
        # Initial seeding - LIGHTER to avoid immediate runaway
        # Previous seeding was too dense, causing universal runaway
        center = 24
        for i in range(-2, 3):
            for j in range(-2, 3):
                if abs(i) + abs(j) <= 2:
                    sim.inject_vortex(center + i * 6, center + j * 6)
        
        # Equilibration
        for _ in range(EQUILIBRATION_STEPS):
            sim.step()
            if time.time() - start_time > timeout_sec:
                result['timeout_hit'] = True
                result['regime'] = 'timeout_during_equilibration'
                return result
        
        # Measurement windows
        windows = []
        for window_idx in range(NUM_WINDOWS):
            window_measurements = []
            
            for step in range(WINDOW_STEPS):
                sim.step()
                
                # Check timeout
                if time.time() - start_time > timeout_sec:
                    result['timeout_hit'] = True
                    break
                
                # Measure every MEASUREMENT_INTERVAL steps
                if step % MEASUREMENT_INTERVAL == 0:
                    defects = sim.detect_defects()
                    n_actual = len(defects)
                    
                    # Check population cap - use truncated sample if over cap
                    if n_actual >= POPULATION_CAP:
                        result['cap_hit'] = True
                        m = measure_state(defects[:POPULATION_CAP], sim.size)
                        m['cap_hit'] = True
                        m['actual_population'] = n_actual
                    else:
                        m = measure_state(defects, sim.size)
                        m['cap_hit'] = False
                    
                    window_measurements.append(m)
            
            if result['timeout_hit']:
                break
            
            # Aggregate window
            valid_measurements = [m for m in window_measurements if m.get('valid', False)]
            if valid_measurements:
                window_agg = {
                    'window_idx': window_idx,
                    'valid': True,
                    'n': np.mean([m['n'] for m in valid_measurements]),
                    'n_std': np.std([m['n'] for m in valid_measurements]),
                    'dimension': np.mean([m['dimension'] for m in valid_measurements]),
                    'dim_std': np.std([m['dimension'] for m in valid_measurements]),
                    'edges': np.mean([m['edges'] for m in valid_measurements]),
                    'triangles': np.mean([m['triangles'] for m in valid_measurements]),
                    'tri_per_node': np.mean([m['tri_per_node'] for m in valid_measurements]),
                    'clustering': np.mean([m['clustering'] for m in valid_measurements]),
                    'correlation': np.mean([m['correlation'] for m in valid_measurements]),
                    'cap_hit': any(m.get('cap_hit', False) for m in valid_measurements),
                }
                windows.append(window_agg)
            else:
                windows.append({
                    'window_idx': window_idx,
                    'valid': False,
                    'reason': 'no_valid_measurements'
                })
            
            # Don't break on cap_hit - continue measuring to capture oscillation patterns
            # (cap_hit is tracked per-window for classification)
        
        result['windows'] = windows
        result['regime'] = classify_regime(windows)
        result['valid'] = len([w for w in windows if w.get('valid', False)]) >= 2
        
        # Compute late-time summary
        valid_windows = [w for w in windows if w.get('valid', False)]
        if valid_windows:
            late = valid_windows[-min(3, len(valid_windows)):]
            result['summary'] = {
                'final_population': np.mean([w['n'] for w in late]),
                'final_dimension': np.mean([w['dimension'] for w in late]),
                'final_dim_std': np.mean([w['dim_std'] for w in late]),
                'final_triangles': np.mean([w['triangles'] for w in late]),
                'final_tri_per_node': np.mean([w['tri_per_node'] for w in late]),
                'final_correlation': np.mean([w['correlation'] for w in late]),
                'final_clustering': np.mean([w['clustering'] for w in late]),
                'dim_trend': compute_window_trend(valid_windows, 'dimension'),
                'pop_trend': compute_window_trend(valid_windows, 'n'),
            }
        
    except Exception as e:
        result['error'] = str(e)
        result['regime'] = 'error'
    
    result['elapsed_seconds'] = time.time() - start_time
    return result


def run_coarse_scan() -> List[Dict]:
    """
    Coarse scan across driving intervals.
    
    Note: Higher interval = WEAKER driving (less frequent injection)
          Lower interval = STRONGER driving (more frequent injection)
    
    Based on initial testing:
    - Interval ~1000+: Filamentary regime (~1.1 dimension)
    - Interval ~500: Transitional
    - Interval ~200 and below: 2D-like regime (~1.8 dimension)
    """
    # Wider range to capture full transition
    intervals = [1000, 700, 500, 400, 300, 200, 150, 100]
    results = []
    
    print("=" * 70)
    print("BRANCH-TRANSITION THRESHOLD STUDY: COARSE SCAN")
    print("=" * 70)
    print()
    print(f"Population cap: {POPULATION_CAP} (measurement truncation)")
    print(f"Timeout per interval: {TIMEOUT_SECONDS}s")
    print()
    
    for interval in intervals:
        print(f"Interval {interval:3d} (rate={3/interval:.4f}):", end=" ", flush=True)
        result = run_single_interval(interval)
        results.append(result)
        
        if result['timeout_hit']:
            print(f"TIMEOUT ({result.get('elapsed_seconds', 0):.1f}s)")
        elif result['cap_hit']:
            print(f"CAP HIT → {result['regime']}")
        elif result.get('summary'):
            s = result['summary']
            print(f"d={s['final_dimension']:.2f} n={s['final_population']:.0f} "
                  f"tri/n={s['final_tri_per_node']:.2f} corr={s['final_correlation']:.2f} "
                  f"→ {result['regime']}")
        else:
            print(f"→ {result['regime']}")
    
    return results


def identify_transition_zone(results: List[Dict]) -> Optional[Tuple[int, int]]:
    """
    Identify the transition zone where dimension jumps.
    Returns (lower_interval, upper_interval) or None.
    """
    valid_results = [r for r in results if r.get('valid', False) and r.get('summary')]
    if len(valid_results) < 2:
        return None
    
    # Sort by interval (descending = weaker to stronger driving)
    valid_results.sort(key=lambda r: r['interval'], reverse=True)
    
    # Look for dimension jump
    for i in range(len(valid_results) - 1):
        dim1 = valid_results[i]['summary']['final_dimension']
        dim2 = valid_results[i + 1]['summary']['final_dimension']
        
        # Significant jump (>0.3 dimension units)
        if dim2 - dim1 > 0.3:
            int1 = valid_results[i]['interval']
            int2 = valid_results[i + 1]['interval']
            return (int2, int1)  # (stronger driving, weaker driving)
    
    return None


def run_refinement_scan(lower: int, upper: int) -> List[Dict]:
    """
    Refinement scan around the transition zone.
    """
    # Generate intervals between lower and upper
    step = max(5, (upper - lower) // 5)
    intervals = list(range(lower, upper + 1, step))
    if lower not in intervals:
        intervals.insert(0, lower)
    if upper not in intervals:
        intervals.append(upper)
    intervals = sorted(set(intervals), reverse=True)
    
    results = []
    
    print()
    print("=" * 70)
    print(f"REFINEMENT SCAN: Intervals {lower} to {upper}")
    print("=" * 70)
    print()
    
    for interval in intervals:
        print(f"Interval {interval:3d} (rate={3/interval:.4f}):", end=" ", flush=True)
        result = run_single_interval(interval)
        results.append(result)
        
        if result['timeout_hit']:
            print(f"TIMEOUT")
        elif result['cap_hit']:
            print(f"CAP HIT → {result['regime']}")
        elif result.get('summary'):
            s = result['summary']
            print(f"d={s['final_dimension']:.2f} n={s['final_population']:.0f} "
                  f"tri/n={s['final_tri_per_node']:.2f} corr={s['final_correlation']:.2f} "
                  f"→ {result['regime']}")
        else:
            print(f"→ {result['regime']}")
    
    return results


def print_summary(all_results: List[Dict]):
    """Print final summary table and analysis."""
    print()
    print("=" * 70)
    print("BRANCH-TRANSITION THRESHOLD STUDY: RESULTS")
    print("=" * 70)
    print()
    
    # Results table
    print(f"{'Interval':>8} {'Rate':>8} {'Pop':>6} {'Dim':>6} {'Tri/N':>6} {'Corr':>6} {'Regime':>20}")
    print("-" * 70)
    
    for r in sorted(all_results, key=lambda x: x['interval'], reverse=True):
        if r.get('summary'):
            s = r['summary']
            flags = ""
            if r['timeout_hit']:
                flags += "[T]"
            if r['cap_hit']:
                flags += "[C]"
            print(f"{r['interval']:>8} {r['driving_rate']:>8.4f} {s['final_population']:>6.0f} "
                  f"{s['final_dimension']:>6.2f} {s['final_tri_per_node']:>6.2f} "
                  f"{s['final_correlation']:>6.2f} {r['regime']:>20} {flags}")
        else:
            flags = "[T]" if r['timeout_hit'] else ""
            print(f"{r['interval']:>8} {r['driving_rate']:>8.4f} {'---':>6} {'---':>6} "
                  f"{'---':>6} {'---':>6} {r['regime']:>20} {flags}")
    
    print()
    print("[T] = timeout hit, [C] = population cap hit")
    
    # Regime distribution
    print()
    print("-" * 70)
    print("REGIME DISTRIBUTION")
    print("-" * 70)
    
    regimes = defaultdict(list)
    for r in all_results:
        regimes[r['regime']].append(r['interval'])
    
    for regime, intervals in sorted(regimes.items()):
        print(f"  {regime}: intervals {intervals}")
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    print()
    
    # Find transition
    valid = [r for r in all_results if r.get('valid') and r.get('summary')]
    if len(valid) >= 2:
        # Sort by interval
        valid.sort(key=lambda r: r['interval'], reverse=True)
        
        dims = [(r['interval'], r['summary']['final_dimension']) for r in valid]
        print("Dimension vs Interval:")
        for interval, dim in dims:
            marker = "***" if dim > 1.5 else ""
            print(f"  Interval {interval:3d} → Dimension {dim:.2f} {marker}")
        
        # Look for threshold
        found_threshold = False
        for i in range(len(valid) - 1):
            dim1 = valid[i]['summary']['final_dimension']
            dim2 = valid[i + 1]['summary']['final_dimension']
            if dim2 - dim1 > 0.3:
                print()
                print(f"POTENTIAL THRESHOLD DETECTED between intervals {valid[i]['interval']} and {valid[i+1]['interval']}")
                print(f"  Dimension jump: {dim1:.2f} → {dim2:.2f} (Δ = {dim2-dim1:.2f})")
                found_threshold = True
                break
        
        if not found_threshold:
            print()
            print("No clear threshold detected in tested range.")
            dim_range = max(d for _, d in dims) - min(d for _, d in dims)
            print(f"Dimension range: {min(d for _, d in dims):.2f} to {max(d for _, d in dims):.2f} (span = {dim_range:.2f})")
    
    # Key signature check
    print()
    print("-" * 70)
    print("KEY SIGNATURE CHECK (2D Branch Criteria)")
    print("-" * 70)
    print()
    
    for r in all_results:
        if r.get('regime') == 'stable_2D_like':
            s = r['summary']
            print(f"Interval {r['interval']}:")
            print(f"  Dimension: {s['final_dimension']:.2f} (>1.5 ✓)")
            print(f"  Tri/Node:  {s['final_tri_per_node']:.2f} (>0.5 ✓)")
            print(f"  Correlation: {s['final_correlation']:.2f} (>0.5 ✓)")
            print(f"  → GENUINE 2D-LIKE BRANCH")
            print()
    
    # Sparse artifact check
    sparse_artifacts = [r for r in all_results if r.get('regime') == 'sparse_artifact']
    if sparse_artifacts:
        print("WARNING: Sparse-network artifacts detected:")
        for r in sparse_artifacts:
            print(f"  Interval {r['interval']}: High dimension but low correlation")


def run_threshold_study():
    """
    Main entry point for the branch-transition threshold study.
    """
    print()
    print("=" * 70)
    print("  DIMENSIONAL BRANCHING HYPOTHESIS: THRESHOLD STUDY")
    print("=" * 70)
    print()
    print("OBJECTIVE: Identify whether there is a thresholded transition from")
    print("a filamentary ~1D scaffold to a denser, loop-rich ~2D-like")
    print("organizational branch under sustained driving.")
    print()
    
    # Coarse scan
    coarse_results = run_coarse_scan()
    
    # Identify transition zone
    transition_zone = identify_transition_zone(coarse_results)
    
    all_results = coarse_results.copy()
    
    if transition_zone:
        print()
        print(f"Transition zone identified: intervals {transition_zone[0]} to {transition_zone[1]}")
        refinement_results = run_refinement_scan(transition_zone[0], transition_zone[1])
        all_results.extend(refinement_results)
    else:
        print()
        print("No clear transition zone identified in coarse scan.")
        print("Checking if refinement around lowest intervals helps...")
        
        # Try refinement around strongest driving
        valid_results = [r for r in coarse_results if r.get('valid')]
        if valid_results:
            min_interval = min(r['interval'] for r in valid_results)
            if min_interval >= 35:
                refinement_results = run_refinement_scan(30, min_interval)
                all_results.extend(refinement_results)
    
    # Print final summary
    print_summary(all_results)
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/branch_transition_study_results.json'
    save_data = {
        'coarse_results': coarse_results,
        'all_results': all_results,
        'transition_zone': transition_zone,
        'parameters': {
            'population_cap': POPULATION_CAP,
            'timeout_seconds': TIMEOUT_SECONDS,
            'window_steps': WINDOW_STEPS,
            'num_windows': NUM_WINDOWS,
            'equilibration_steps': EQUILIBRATION_STEPS,
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return all_results


if __name__ == "__main__":
    results = run_threshold_study()
