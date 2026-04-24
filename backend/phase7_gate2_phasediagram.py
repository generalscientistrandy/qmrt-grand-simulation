"""
Phase 7, Gate 2: Phase Diagram / Regime Boundaries
===================================================

Central Question: Is the ~1D effective dimension universal, or can it
transition to higher-dimensional geometry under different conditions?

The anomalous scaling (d≈1) from Gate 1 raises the key question:
- Is filamentary geometry intrinsic to the medium?
- Or is it regime-dependent?

Tests:
1. Dimension vs Pressure: Does crowding create space-filling networks?
2. Dimension vs Confinement: Do tight boundaries increase regularity?
3. Dimension vs Coupling Contrast: Does stronger gradient change structure?

Success criterion:
Either find regime(s) with higher effective dimension (d > 1.5),
or establish that ~1D is universal across tested parameter space.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import time


class PhaseDiagramSimulator:
    """
    Simulator with configurable parameters for phase diagram mapping.
    """
    
    def __init__(
        self,
        size: int = 48,
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        gamma: float = 0.007,
        interior_radius_frac: float = 0.25,
        transition_width: float = 10.0,
    ):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.gamma = gamma
        self.interior_radius_frac = interior_radius_frac
        self.transition_width = transition_width
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * self.interior_radius_frac
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = self.coupling_center
                    elif dist >= interior_r + self.transition_width:
                        coupling[i, j, k] = self.coupling_edge
                    else:
                        t = (dist - interior_r) / self.transition_width
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = self.coupling_center + blend * (self.coupling_edge - self.coupling_center)
        return coupling
    
    def step(self, dt: float = 0.04):
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        c_eff = 2.0
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff**2 * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff**2 * lap_i - self.gamma * self.psi_i_dot
        
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
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple[int, int, int]]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        low_amp = amp < threshold
        labeled, n = label(low_amp)
        
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) < 5:
                continue
            coords = np.where(component)
            cx = int(np.mean(coords[0]))
            cy = int(np.mean(coords[1]))
            cz = int(np.mean(coords[2]))
            defects.append((cx, cy, cz))
        
        return defects
    
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


def euclidean_distance_periodic(p1: Tuple, p2: Tuple, size: int) -> float:
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def build_adjacency(defects: List[Tuple], size: int, radius: float = 10.0) -> Dict[int, set]:
    adj = defaultdict(set)
    for i in range(len(defects)):
        for j in range(i + 1, len(defects)):
            d = euclidean_distance_periodic(defects[i], defects[j], size)
            if d < radius:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def compute_graph_distances(adj: Dict[int, set], n: int) -> np.ndarray:
    distances = np.full((n, n), np.inf)
    for start in range(n):
        distances[start, start] = 0
        queue = deque([start])
        visited = {start}
        while queue:
            node = queue.popleft()
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[start, neighbor] = distances[start, node] + 1
                    queue.append(neighbor)
    return distances


def measure_metrics(defects: List[Tuple], size: int) -> Dict:
    """Measure key metrics for a defect configuration."""
    if len(defects) < 15:
        return {'valid': False, 'n_defects': len(defects)}
    
    adj = build_adjacency(defects, size, radius=10.0)
    n = len(defects)
    graph_dist = compute_graph_distances(adj, n)
    
    # Distance correlation
    euclidean_dists = []
    graph_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            if graph_dist[i, j] < np.inf:
                euclidean_dists.append(euclidean_distance_periodic(defects[i], defects[j], size))
                graph_dists.append(graph_dist[i, j])
    
    if len(euclidean_dists) < 10:
        return {'valid': False, 'n_defects': n}
    
    pearson_r, _ = pearsonr(euclidean_dists, graph_dists)
    
    # Neighborhood scaling
    radii = list(range(1, 7))
    mean_counts = []
    for r in radii:
        counts = [np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0)) for i in range(n)]
        mean_counts.append(np.mean(counts))
    
    log_r = np.log(radii)
    log_n = np.log(np.array(mean_counts) + 1)
    coeffs = np.polyfit(log_r, log_n, 1)
    scaling_exponent = coeffs[0]
    
    # Fit quality
    fit = np.polyval(coeffs, log_r)
    ss_res = np.sum((log_n - fit)**2)
    ss_tot = np.sum((log_n - np.mean(log_n))**2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    return {
        'valid': True,
        'n_defects': n,
        'pearson_r': pearson_r,
        'scaling_exponent': scaling_exponent,
        'r_squared': r_squared,
        'mean_counts': mean_counts,
    }


def run_single_regime(
    n_vortices: int,
    coupling_center: float,
    coupling_edge: float,
    interior_radius_frac: float,
    transition_width: float,
    equilibration_steps: int = 600,
    measurement_steps: int = 400,
) -> Dict:
    """Run a single regime configuration and measure metrics."""
    sim = PhaseDiagramSimulator(
        size=48,
        coupling_center=coupling_center,
        coupling_edge=coupling_edge,
        interior_radius_frac=interior_radius_frac,
        transition_width=transition_width,
    )
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Inject vortices
    center = 24
    injected = 0
    for i in range(-5, 6):
        for j in range(-5, 6):
            if injected >= n_vortices:
                break
            if abs(i) + abs(j) <= 5:
                sim.inject_vortex(center + i * 3, center + j * 3)
                injected += 1
        if injected >= n_vortices:
            break
    
    # Equilibrate
    for _ in range(equilibration_steps):
        sim.step()
    
    # Measure
    all_metrics = []
    for step in range(measurement_steps):
        sim.step()
        if step % 50 == 0:
            defects = sim.detect_defects()
            metrics = measure_metrics(defects, sim.size)
            if metrics['valid']:
                all_metrics.append(metrics)
    
    if not all_metrics:
        return {'valid': False}
    
    return {
        'valid': True,
        'n_samples': len(all_metrics),
        'mean_defects': np.mean([m['n_defects'] for m in all_metrics]),
        'mean_pearson': np.mean([m['pearson_r'] for m in all_metrics]),
        'mean_dimension': np.mean([m['scaling_exponent'] for m in all_metrics]),
        'std_dimension': np.std([m['scaling_exponent'] for m in all_metrics]),
        'mean_r_squared': np.mean([m['r_squared'] for m in all_metrics]),
    }


def run_phase_diagram():
    """
    Map effective dimension across parameter space.
    """
    print("=" * 70)
    print("PHASE 7, GATE 2: PHASE DIAGRAM / REGIME BOUNDARIES")
    print("=" * 70)
    print()
    print("Question: Is ~1D scaling universal, or regime-dependent?")
    print()
    
    results = {}
    
    # Axis 1: Pressure (number of injected vortices)
    print("-" * 70)
    print("AXIS 1: PRESSURE (Injection Count)")
    print("-" * 70)
    print()
    
    pressure_levels = [10, 25, 50, 75]
    pressure_results = []
    
    for n_vort in pressure_levels:
        print(f"  Testing {n_vort} vortices...", end=" ", flush=True)
        r = run_single_regime(
            n_vortices=n_vort,
            coupling_center=0.7,
            coupling_edge=0.2,
            interior_radius_frac=0.25,
            transition_width=10.0,
        )
        if r['valid']:
            print(f"d={r['mean_dimension']:.2f}, r={r['mean_pearson']:.2f}, "
                  f"n={r['mean_defects']:.0f}")
            pressure_results.append({
                'n_vortices': n_vort,
                **r
            })
        else:
            print("insufficient data")
    
    results['pressure'] = pressure_results
    
    # Axis 2: Confinement (interior radius)
    print()
    print("-" * 70)
    print("AXIS 2: CONFINEMENT (Interior Radius)")
    print("-" * 70)
    print()
    
    confinement_levels = [0.35, 0.25, 0.15, 0.10]  # Fraction of grid
    confinement_results = []
    
    for r_frac in confinement_levels:
        interior_r = int(48 * r_frac)
        print(f"  Testing r={interior_r} ({r_frac:.0%})...", end=" ", flush=True)
        r = run_single_regime(
            n_vortices=25,
            coupling_center=0.7,
            coupling_edge=0.2,
            interior_radius_frac=r_frac,
            transition_width=5.0,
        )
        if r['valid']:
            print(f"d={r['mean_dimension']:.2f}, r={r['mean_pearson']:.2f}, "
                  f"n={r['mean_defects']:.0f}")
            confinement_results.append({
                'interior_frac': r_frac,
                'interior_r': interior_r,
                **r
            })
        else:
            print("insufficient data")
    
    results['confinement'] = confinement_results
    
    # Axis 3: Coupling Contrast
    print()
    print("-" * 70)
    print("AXIS 3: COUPLING CONTRAST")
    print("-" * 70)
    print()
    
    contrast_levels = [
        (0.5, 0.4),   # Weak contrast
        (0.7, 0.2),   # Standard
        (0.9, 0.1),   # Strong contrast
        (0.95, 0.05), # Extreme contrast
    ]
    contrast_results = []
    
    for c_center, c_edge in contrast_levels:
        contrast = c_center - c_edge
        print(f"  Testing contrast={contrast:.2f} ({c_center}/{c_edge})...", end=" ", flush=True)
        r = run_single_regime(
            n_vortices=25,
            coupling_center=c_center,
            coupling_edge=c_edge,
            interior_radius_frac=0.25,
            transition_width=10.0,
        )
        if r['valid']:
            print(f"d={r['mean_dimension']:.2f}, r={r['mean_pearson']:.2f}, "
                  f"n={r['mean_defects']:.0f}")
            contrast_results.append({
                'coupling_center': c_center,
                'coupling_edge': c_edge,
                'contrast': contrast,
                **r
            })
        else:
            print("insufficient data")
    
    results['contrast'] = contrast_results
    
    # Summary
    print()
    print("=" * 70)
    print("PHASE DIAGRAM SUMMARY")
    print("=" * 70)
    print()
    
    all_dimensions = []
    
    print("PRESSURE AXIS:")
    for r in pressure_results:
        print(f"  {r['n_vortices']:3d} vortices: d = {r['mean_dimension']:.2f} ± {r['std_dimension']:.2f}")
        all_dimensions.append(r['mean_dimension'])
    
    print()
    print("CONFINEMENT AXIS:")
    for r in confinement_results:
        print(f"  r = {r['interior_r']:2d} ({r['interior_frac']:.0%}): d = {r['mean_dimension']:.2f} ± {r['std_dimension']:.2f}")
        all_dimensions.append(r['mean_dimension'])
    
    print()
    print("CONTRAST AXIS:")
    for r in contrast_results:
        print(f"  Δκ = {r['contrast']:.2f}: d = {r['mean_dimension']:.2f} ± {r['std_dimension']:.2f}")
        all_dimensions.append(r['mean_dimension'])
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    print()
    
    if all_dimensions:
        min_d = min(all_dimensions)
        max_d = max(all_dimensions)
        range_d = max_d - min_d
        
        print(f"Dimension range: {min_d:.2f} to {max_d:.2f} (span = {range_d:.2f})")
        print()
        
        # Check for regime transitions
        found_higher_d = any(d > 1.5 for d in all_dimensions)
        found_2d = any(d > 1.8 for d in all_dimensions)
        
        if found_2d:
            print("FINDING: 2D-like regime detected (d > 1.8)")
            high_d_regimes = []
            for r in pressure_results:
                if r['mean_dimension'] > 1.8:
                    high_d_regimes.append(f"pressure={r['n_vortices']}")
            for r in confinement_results:
                if r['mean_dimension'] > 1.8:
                    high_d_regimes.append(f"confinement={r['interior_frac']:.0%}")
            for r in contrast_results:
                if r['mean_dimension'] > 1.8:
                    high_d_regimes.append(f"contrast={r['contrast']:.2f}")
            print(f"  Regimes: {', '.join(high_d_regimes)}")
        elif found_higher_d:
            print("FINDING: Higher-dimensional regime detected (d > 1.5)")
        elif range_d > 0.3:
            print("FINDING: Dimension varies significantly across regimes")
        else:
            print("FINDING: ~1D scaling appears universal across tested regimes")
        
        # Find the highest dimension regime
        if pressure_results:
            best_pressure = max(pressure_results, key=lambda x: x['mean_dimension'])
            print(f"\nHighest d from pressure: {best_pressure['mean_dimension']:.2f} "
                  f"at {best_pressure['n_vortices']} vortices")
        
        if confinement_results:
            best_conf = max(confinement_results, key=lambda x: x['mean_dimension'])
            print(f"Highest d from confinement: {best_conf['mean_dimension']:.2f} "
                  f"at {best_conf['interior_frac']:.0%} radius")
        
        if contrast_results:
            best_contrast = max(contrast_results, key=lambda x: x['mean_dimension'])
            print(f"Highest d from contrast: {best_contrast['mean_dimension']:.2f} "
                  f"at Δκ={best_contrast['contrast']:.2f}")
    
    # Gate assessment
    print()
    print("=" * 70)
    print("GATE 2 ASSESSMENT")
    print("=" * 70)
    print()
    
    if found_2d:
        print("GATE 2 RESULT: REGIME-DEPENDENT GEOMETRY")
        print("  Effective dimension varies, with 2D-like regimes achievable")
        print("  The filamentary geometry is NOT universal")
    elif found_higher_d:
        print("GATE 2 RESULT: PARTIAL REGIME DEPENDENCE")
        print("  Dimension varies but stays below 2D")
        print("  Geometry is constrained but not fixed")
    elif range_d > 0.3:
        print("GATE 2 RESULT: WEAK REGIME DEPENDENCE")
        print("  Dimension varies but stays ~1D")
        print("  Filamentary structure is approximately universal")
    else:
        print("GATE 2 RESULT: UNIVERSAL ~1D GEOMETRY")
        print("  Effective dimension is stable across all tested regimes")
        print("  Filamentary structure appears intrinsic")
    
    return results


if __name__ == "__main__":
    results = run_phase_diagram()
