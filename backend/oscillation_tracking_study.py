"""
Branch-Transition Threshold Study v3
=====================================

HANDLING OSCILLATORY DYNAMICS

Key insight: The system oscillates between high and low population states.
We must measure across the oscillation cycle, not at single points.

APPROACH:
1. Run extended simulation with frequent sampling
2. Track PEAK populations and dimension during peaks
3. Classify based on peak behavior
4. Identify if system reaches sustained high-population branch
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


def euclidean_distance_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def quick_measure(defects, size) -> Dict:
    """Quick measurement for tracking oscillations."""
    n = len(defects)
    if n < 15:
        return {'valid': False, 'n': n}
    
    # Sample for efficiency
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
            d = euclidean_distance_periodic(sample[i], sample[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    # Triangles
    triangles = 0
    for node in range(max_n):
        neighbors = list(adj[node])
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    triangles += 1
    triangles //= 3
    
    # Simple dimension estimate from local neighborhood
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    mean_degree = edges * 2 / max_n if max_n > 0 else 0
    tri_per_node = triangles / max_n if max_n > 0 else 0
    
    # Graph-based dimension (simplified)
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
    
    # Correlation
    euc_dists, graph_dists_list = [], []
    for idx in range(max_sources):
        for j in range(idx + 1, max_n):
            if graph_dist[idx, j] < np.inf:
                euc_dists.append(euclidean_distance_periodic(sample[idx], sample[j], size))
                graph_dists_list.append(graph_dist[idx, j])
    
    correlation = pearsonr(euc_dists, graph_dists_list)[0] if len(euc_dists) >= 10 else 0
    
    # Dimension
    radii = [1, 2, 3, 4]
    counts = [np.mean([np.sum((graph_dist[idx, :] <= r) & (graph_dist[idx, :] > 0)) 
                       for idx in range(max_sources)]) for r in radii]
    
    if min(counts) > 0:
        dimension = np.polyfit(np.log(radii), np.log(np.array(counts) + 1), 1)[0]
    else:
        dimension = 0
    
    return {
        'valid': True,
        'n': n,
        'triangles': triangles,
        'tri_per_node': tri_per_node,
        'correlation': correlation,
        'dimension': dimension,
        'mean_degree': mean_degree,
    }


class OscillationTrackingSimulator:
    """Simulator that tracks oscillation dynamics."""
    
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


def analyze_peaks(measurements: List[Dict], pop_threshold: int = 50) -> Dict:
    """
    Analyze peak measurements (high-population states).
    """
    valid = [m for m in measurements if m.get('valid', False)]
    if not valid:
        return {'has_peaks': False}
    
    # Find peaks (above threshold)
    peaks = [m for m in valid if m['n'] >= pop_threshold]
    
    if len(peaks) < 3:
        return {
            'has_peaks': False,
            'max_pop': max(m['n'] for m in valid),
            'peak_count': len(peaks),
        }
    
    # Analyze peak characteristics
    peak_dims = [m['dimension'] for m in peaks]
    peak_pops = [m['n'] for m in peaks]
    peak_corrs = [m['correlation'] for m in peaks]
    peak_tri_per_nodes = [m['tri_per_node'] for m in peaks]
    
    return {
        'has_peaks': True,
        'peak_count': len(peaks),
        'peak_mean_pop': np.mean(peak_pops),
        'peak_max_pop': max(peak_pops),
        'peak_mean_dim': np.mean(peak_dims),
        'peak_dim_std': np.std(peak_dims),
        'peak_mean_corr': np.mean(peak_corrs),
        'peak_mean_tri_per_node': np.mean(peak_tri_per_nodes),
        'total_measurements': len(valid),
        'peak_fraction': len(peaks) / len(valid),
    }


def classify_oscillation_regime(peak_analysis: Dict) -> str:
    """Classify the regime based on peak analysis."""
    if not peak_analysis.get('has_peaks'):
        if peak_analysis.get('max_pop', 0) < 20:
            return 'collapsed_sparse'
        return 'sub_threshold'
    
    dim = peak_analysis.get('peak_mean_dim', 0)
    corr = peak_analysis.get('peak_mean_corr', 0)
    tri = peak_analysis.get('peak_mean_tri_per_node', 0)
    pop = peak_analysis.get('peak_mean_pop', 0)
    peak_frac = peak_analysis.get('peak_fraction', 0)
    
    # Check for sustained vs oscillatory
    is_sustained = peak_frac > 0.5
    
    # 2D-like: high dimension, good correlation, enriched triangles
    if dim > 1.5 and corr > 0.5 and tri > 0.5:
        return 'peak_2D_like_sustained' if is_sustained else 'peak_2D_like_oscillatory'
    
    # Filamentary: low dimension, good correlation
    if dim < 1.4 and corr > 0.5:
        return 'peak_filamentary_sustained' if is_sustained else 'peak_filamentary_oscillatory'
    
    # Transitional
    if 1.3 < dim < 1.6:
        return 'peak_transitional_sustained' if is_sustained else 'peak_transitional_oscillatory'
    
    # Sparse artifact
    if dim > 1.3 and corr < 0.4:
        return 'sparse_artifact'
    
    return 'inconclusive'


def run_oscillation_tracking_study():
    """
    Run the oscillation-aware branch study.
    """
    print("=" * 80)
    print("  OSCILLATION-AWARE BRANCH-TRANSITION STUDY")
    print("=" * 80)
    print()
    print("This study tracks peak states during population oscillations.")
    print()
    
    # Test intervals
    intervals = [50, 100, 200, 300, 500, 750, 1000]
    
    TOTAL_STEPS = 3000
    SAMPLE_INTERVAL = 50
    
    results = []
    
    print("-" * 80)
    print(f"{'Interval':>8} {'Rate':>8} {'#Peaks':>7} {'PeakPop':>8} {'PeakDim':>8} "
          f"{'Corr':>6} {'Tri/N':>6} {'Regime':>28}")
    print("-" * 80)
    
    for interval in intervals:
        # Initialize with dense seeding
        sim = OscillationTrackingSimulator(size=48, injection_interval=interval, injection_count=3)
        np.random.seed(42)
        sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
        
        center = 24
        for i in range(-4, 5):
            for j in range(-4, 5):
                if abs(i) + abs(j) <= 4:
                    sim.inject_vortex(center + i * 3, center + j * 3)
        
        # Run and collect measurements
        measurements = []
        for step in range(TOTAL_STEPS):
            sim.step()
            
            if step % SAMPLE_INTERVAL == 0:
                defects = sim.detect_defects()
                m = quick_measure(defects, sim.size)
                m['step'] = step
                measurements.append(m)
        
        # Analyze peaks
        peak_analysis = analyze_peaks(measurements, pop_threshold=50)
        regime = classify_oscillation_regime(peak_analysis)
        
        result = {
            'interval': interval,
            'driving_rate': 3.0 / interval,
            'peak_analysis': peak_analysis,
            'regime': regime,
            'total_measurements': len(measurements),
        }
        results.append(result)
        
        # Print row
        if peak_analysis.get('has_peaks'):
            print(f"{interval:>8} {result['driving_rate']:>8.4f} "
                  f"{peak_analysis['peak_count']:>7} "
                  f"{peak_analysis['peak_mean_pop']:>8.0f} "
                  f"{peak_analysis['peak_mean_dim']:>8.2f} "
                  f"{peak_analysis['peak_mean_corr']:>6.2f} "
                  f"{peak_analysis['peak_mean_tri_per_node']:>6.2f} "
                  f"{regime:>28}")
        else:
            print(f"{interval:>8} {result['driving_rate']:>8.4f} "
                  f"{'---':>7} {'---':>8} {'---':>8} {'---':>6} {'---':>6} "
                  f"{regime:>28}")
    
    # Analysis
    print()
    print("=" * 80)
    print("REGIME DISTRIBUTION")
    print("=" * 80)
    
    regimes = defaultdict(list)
    for r in results:
        regimes[r['regime']].append(r['interval'])
    
    for regime, ints in sorted(regimes.items()):
        print(f"  {regime}: intervals {ints}")
    
    # Dimension vs driving analysis
    print()
    print("-" * 80)
    print("DIMENSION vs DRIVING RATE (Peak States)")
    print("-" * 80)
    
    with_peaks = [r for r in results if r['peak_analysis'].get('has_peaks')]
    if with_peaks:
        rates = [r['driving_rate'] for r in with_peaks]
        dims = [r['peak_analysis']['peak_mean_dim'] for r in with_peaks]
        
        print(f"{'Rate':>10} {'Peak Dim':>10}")
        for r in sorted(with_peaks, key=lambda x: x['driving_rate']):
            print(f"{r['driving_rate']:>10.4f} {r['peak_analysis']['peak_mean_dim']:>10.2f}")
        
        if len(rates) >= 3:
            corr = pearsonr(rates, dims)[0]
            print(f"\nCorrelation (driving rate vs peak dimension): {corr:.3f}")
    
    # Save
    output_path = '/app/backend/qmrt_topology/papers/oscillation_study_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study_type': 'oscillation_aware',
            'total_steps': TOTAL_STEPS,
            'sample_interval': SAMPLE_INTERVAL,
            'results': results,
        }, f, indent=2, default=str)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    results = run_oscillation_tracking_study()
