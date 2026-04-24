"""
Phase 6, Gate 4: New Effective Regimes
======================================

Question: Do pressure, confinement, or large gradients produce genuinely
new effective regimes beyond the current proto-spacetime hierarchy?

"New regime" means qualitative change, not just quantitative:
- Sudden increase in clustering/hub dominance
- Transition from diffuse network to modular substructures
- Sharp changes in carrying capacity behavior
- Confinement-induced stable bands or shells
- Pressure-induced collective modes

Tests:
1. PRESSURE: Extreme crowding — does network fragment or form new modes?
2. CONFINEMENT: Tight attractor boundary — do stable substructures appear?
3. STEEP GRADIENTS: Sharp coupling transition — do new zones emerge?

Success criterion:
Evidence of qualitatively new organizational regimes under strong forcing.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist, squareform
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import time


class RegimeTestSimulator:
    """
    Simulator with configurable environmental parameters for regime tests.
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
        self.step_count = 0
        
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
        self.step_count += 1
        
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
    
    def inject_vortex(self, cx: int, cy: int, charge: int = 1):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * charge * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def get_radial_profile(self, defects: List[Tuple]) -> Dict:
        """Compute radial distribution of defects."""
        if not defects:
            return {'bins': [], 'counts': [], 'density': []}
        
        center = self.size / 2
        radii = [np.sqrt((d[0]-center)**2 + (d[1]-center)**2 + (d[2]-center)**2) 
                 for d in defects]
        
        bins = np.linspace(0, self.size/2, 10)
        hist, _ = np.histogram(radii, bins=bins)
        
        # Normalize by shell volume
        density = []
        for i in range(len(hist)):
            r1, r2 = bins[i], bins[i+1]
            vol = (4/3) * np.pi * (r2**3 - r1**3)
            density.append(hist[i] / vol if vol > 0 else 0)
        
        bin_centers = (bins[:-1] + bins[1:]) / 2
        return {'bins': bin_centers, 'counts': hist, 'density': np.array(density)}


def distance_periodic(p1: Tuple, p2: Tuple, size: int) -> float:
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def compute_network_stats(defects: List[Tuple], size: int, radius: float = 10.0) -> Dict:
    """Compute network statistics for regime comparison."""
    if len(defects) < 2:
        return {
            'num_defects': len(defects),
            'num_edges': 0,
            'mean_degree': 0,
            'max_degree': 0,
            'num_components': len(defects),
            'largest_component': len(defects),
            'clustering_coef': 0,
        }
    
    # Build adjacency
    adj = defaultdict(set)
    num_edges = 0
    
    for i in range(len(defects)):
        for j in range(i + 1, len(defects)):
            d = distance_periodic(defects[i], defects[j], size)
            if d < radius:
                adj[i].add(j)
                adj[j].add(i)
                num_edges += 1
    
    # Degrees
    degrees = [len(adj[i]) for i in range(len(defects))]
    mean_degree = np.mean(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0
    
    # Components
    visited = set()
    components = []
    
    for start in range(len(defects)):
        if start in visited:
            continue
        component = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            queue.extend(adj[node] - visited)
        components.append(component)
    
    # Clustering coefficient
    clustering = 0
    count = 0
    for i in range(len(defects)):
        neighbors = list(adj[i])
        if len(neighbors) < 2:
            continue
        # Count triangles
        triangles = 0
        possible = len(neighbors) * (len(neighbors) - 1) / 2
        for ni in range(len(neighbors)):
            for nj in range(ni + 1, len(neighbors)):
                if neighbors[nj] in adj[neighbors[ni]]:
                    triangles += 1
        if possible > 0:
            clustering += triangles / possible
            count += 1
    
    clustering = clustering / count if count > 0 else 0
    
    return {
        'num_defects': len(defects),
        'num_edges': num_edges,
        'mean_degree': mean_degree,
        'max_degree': max_degree,
        'num_components': len(components),
        'largest_component': max(len(c) for c in components) if components else 0,
        'clustering_coef': clustering,
    }


def run_pressure_test():
    """Test 1: Extreme pressure/crowding."""
    print("-" * 70)
    print("TEST 1: EXTREME PRESSURE")
    print("-" * 70)
    print()
    print("Does extreme crowding produce a qualitatively new regime?")
    print()
    
    # Baseline: moderate injection
    sim_baseline = RegimeTestSimulator(size=48)
    np.random.seed(42)
    sim_baseline.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim_baseline.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    center = 24
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) + abs(j) <= 2:
                sim_baseline.inject_vortex(center + i * 5, center + j * 5)
    
    # Extreme: massive injection
    sim_extreme = RegimeTestSimulator(size=48)
    np.random.seed(42)
    sim_extreme.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim_extreme.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    for i in range(-4, 5):
        for j in range(-4, 5):
            sim_extreme.inject_vortex(center + i * 3, center + j * 3)
    
    print("Running baseline (13 vortices)...")
    for _ in range(800):
        sim_baseline.step()
    
    print("Running extreme pressure (81 vortices)...")
    for _ in range(800):
        sim_extreme.step()
    
    # Compare
    base_defects = sim_baseline.detect_defects()
    extreme_defects = sim_extreme.detect_defects()
    
    base_stats = compute_network_stats(base_defects, 48)
    extreme_stats = compute_network_stats(extreme_defects, 48)
    
    print()
    print(f"Baseline:  {base_stats['num_defects']} defects, "
          f"mean_deg={base_stats['mean_degree']:.1f}, "
          f"max_deg={base_stats['max_degree']}, "
          f"clustering={base_stats['clustering_coef']:.3f}")
    print(f"Extreme:   {extreme_stats['num_defects']} defects, "
          f"mean_deg={extreme_stats['mean_degree']:.1f}, "
          f"max_deg={extreme_stats['max_degree']}, "
          f"clustering={extreme_stats['clustering_coef']:.3f}")
    
    # Check for regime change
    regime_change = False
    changes = []
    
    if extreme_stats['clustering_coef'] > base_stats['clustering_coef'] * 1.5:
        changes.append(f"Clustering jumped {extreme_stats['clustering_coef']/base_stats['clustering_coef']:.1f}×")
        regime_change = True
    
    if extreme_stats['max_degree'] > base_stats['max_degree'] * 2:
        changes.append(f"Hub dominance increased (max degree {base_stats['max_degree']}→{extreme_stats['max_degree']})")
        regime_change = True
    
    if extreme_stats['num_components'] > base_stats['num_components'] * 2:
        changes.append(f"Network fragmented ({base_stats['num_components']}→{extreme_stats['num_components']} components)")
        regime_change = True
    
    return {
        'baseline': base_stats,
        'extreme': extreme_stats,
        'regime_change': regime_change,
        'changes': changes,
    }


def run_confinement_test():
    """Test 2: Tight confinement."""
    print()
    print("-" * 70)
    print("TEST 2: TIGHT CONFINEMENT")
    print("-" * 70)
    print()
    print("Does tight confinement produce stable substructures?")
    print()
    
    # Normal attractor
    sim_normal = RegimeTestSimulator(
        size=48, 
        interior_radius_frac=0.25,  # 12 units
        coupling_center=0.7,
        coupling_edge=0.2,
        transition_width=10.0,
    )
    
    # Tight confinement
    sim_tight = RegimeTestSimulator(
        size=48,
        interior_radius_frac=0.15,  # 7 units - smaller attractor
        coupling_center=0.9,        # Stronger coupling
        coupling_edge=0.1,          # Weaker outside
        transition_width=3.0,       # Sharp boundary
    )
    
    np.random.seed(42)
    for sim in [sim_normal, sim_tight]:
        sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
        
        center = 24
        for i in range(-2, 3):
            for j in range(-2, 3):
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    print("Running normal attractor...")
    for _ in range(1000):
        sim_normal.step()
    
    print("Running tight confinement...")
    for _ in range(1000):
        sim_tight.step()
    
    normal_defects = sim_normal.detect_defects()
    tight_defects = sim_tight.detect_defects()
    
    normal_profile = sim_normal.get_radial_profile(normal_defects)
    tight_profile = sim_tight.get_radial_profile(tight_defects)
    
    print()
    print("Radial density profiles:")
    print("  Normal attractor:")
    for i, (r, d) in enumerate(zip(normal_profile['bins'][:5], normal_profile['density'][:5])):
        print(f"    r={r:.0f}: density={d:.4f}")
    
    print("  Tight confinement:")
    for i, (r, d) in enumerate(zip(tight_profile['bins'][:5], tight_profile['density'][:5])):
        print(f"    r={r:.0f}: density={d:.4f}")
    
    # Check for shell formation or sharp boundary
    regime_change = False
    changes = []
    
    if len(tight_profile['density']) > 2:
        # Check for density peak (shell formation)
        max_idx = np.argmax(tight_profile['density'])
        if max_idx > 0 and max_idx < len(tight_profile['density']) - 1:
            changes.append(f"Density peak at r={tight_profile['bins'][max_idx]:.0f} (possible shell)")
            regime_change = True
        
        # Check for sharp boundary
        if len(tight_profile['density']) > 3:
            gradient = np.diff(tight_profile['density'])
            if np.min(gradient) < -0.001:  # Sharp drop
                changes.append("Sharp density boundary formed")
                regime_change = True
    
    normal_stats = compute_network_stats(normal_defects, 48)
    tight_stats = compute_network_stats(tight_defects, 48)
    
    if tight_stats['clustering_coef'] > normal_stats['clustering_coef'] * 1.5:
        changes.append(f"Clustering increased under confinement")
        regime_change = True
    
    return {
        'normal': normal_stats,
        'tight': tight_stats,
        'normal_profile': normal_profile,
        'tight_profile': tight_profile,
        'regime_change': regime_change,
        'changes': changes,
    }


def run_gradient_test():
    """Test 3: Steep gradients."""
    print()
    print("-" * 70)
    print("TEST 3: STEEP GRADIENTS")
    print("-" * 70)
    print()
    print("Do steep coupling gradients produce new transport/segregation regimes?")
    print()
    
    # Smooth gradient
    sim_smooth = RegimeTestSimulator(
        size=48,
        coupling_center=0.7,
        coupling_edge=0.2,
        transition_width=15.0,  # Very gradual
    )
    
    # Steep gradient
    sim_steep = RegimeTestSimulator(
        size=48,
        coupling_center=0.9,
        coupling_edge=0.05,      # Much stronger contrast
        transition_width=2.0,    # Very sharp
    )
    
    np.random.seed(42)
    for sim in [sim_smooth, sim_steep]:
        sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
        
        # Inject across regions
        center = 24
        for r_offset in [0, 8, 16]:  # Different radii
            for angle in range(4):
                theta = angle * np.pi / 2
                cx = int(center + r_offset * np.cos(theta))
                cy = int(center + r_offset * np.sin(theta))
                sim.inject_vortex(cx, cy)
    
    print("Running smooth gradient...")
    for _ in range(1000):
        sim_smooth.step()
    
    print("Running steep gradient...")
    for _ in range(1000):
        sim_steep.step()
    
    smooth_defects = sim_smooth.detect_defects()
    steep_defects = sim_steep.detect_defects()
    
    smooth_profile = sim_smooth.get_radial_profile(smooth_defects)
    steep_profile = sim_steep.get_radial_profile(steep_defects)
    
    # Compute interior/exterior ratio
    def compute_io_ratio(profile, boundary_idx=3):
        if len(profile['density']) <= boundary_idx:
            return 1.0
        interior = np.mean(profile['density'][:boundary_idx])
        exterior = np.mean(profile['density'][boundary_idx:])
        return interior / (exterior + 1e-6)
    
    smooth_ratio = compute_io_ratio(smooth_profile)
    steep_ratio = compute_io_ratio(steep_profile)
    
    print()
    print(f"Interior/Exterior density ratio:")
    print(f"  Smooth gradient: {smooth_ratio:.1f}×")
    print(f"  Steep gradient:  {steep_ratio:.1f}×")
    
    regime_change = False
    changes = []
    
    if steep_ratio > smooth_ratio * 2:
        changes.append(f"Strong segregation under steep gradient ({steep_ratio:.0f}× vs {smooth_ratio:.0f}×)")
        regime_change = True
    
    smooth_stats = compute_network_stats(smooth_defects, 48)
    steep_stats = compute_network_stats(steep_defects, 48)
    
    if steep_stats['num_components'] > smooth_stats['num_components'] * 2:
        changes.append(f"Network fragmentation under steep gradient")
        regime_change = True
    
    if steep_stats['clustering_coef'] > smooth_stats['clustering_coef'] * 1.5:
        changes.append("Enhanced clustering under steep gradient")
        regime_change = True
    
    return {
        'smooth': smooth_stats,
        'steep': steep_stats,
        'smooth_ratio': smooth_ratio,
        'steep_ratio': steep_ratio,
        'regime_change': regime_change,
        'changes': changes,
    }


def run_gate_4_test():
    """
    Phase 6, Gate 4: Test for new effective regimes.
    """
    print("=" * 70)
    print("PHASE 6, GATE 4: NEW EFFECTIVE REGIMES")
    print("=" * 70)
    print()
    print("Question: Do strong environmental forces produce qualitatively new regimes?")
    print()
    
    pressure_results = run_pressure_test()
    confinement_results = run_confinement_test()
    gradient_results = run_gradient_test()
    
    # Summary
    print()
    print("=" * 70)
    print("GATE 4 ASSESSMENT")
    print("=" * 70)
    print()
    
    all_changes = []
    
    print("PRESSURE TEST:")
    if pressure_results['regime_change']:
        print(f"  REGIME CHANGE DETECTED")
        for c in pressure_results['changes']:
            print(f"    + {c}")
            all_changes.append(f"Pressure: {c}")
    else:
        print("  No qualitative regime change")
    
    print()
    print("CONFINEMENT TEST:")
    if confinement_results['regime_change']:
        print(f"  REGIME CHANGE DETECTED")
        for c in confinement_results['changes']:
            print(f"    + {c}")
            all_changes.append(f"Confinement: {c}")
    else:
        print("  No qualitative regime change")
    
    print()
    print("GRADIENT TEST:")
    if gradient_results['regime_change']:
        print(f"  REGIME CHANGE DETECTED")
        for c in gradient_results['changes']:
            print(f"    + {c}")
            all_changes.append(f"Gradient: {c}")
    else:
        print("  No qualitative regime change")
    
    print()
    print("-" * 70)
    print()
    
    num_regime_changes = sum([
        pressure_results['regime_change'],
        confinement_results['regime_change'],
        gradient_results['regime_change'],
    ])
    
    if num_regime_changes >= 2:
        print("GATE 4 RESULT: STRONG EVIDENCE FOR NEW REGIMES")
        print("  Multiple forcing conditions produce qualitative regime changes")
        print()
        print("  New regimes observed:")
        for c in all_changes:
            print(f"    - {c}")
    elif num_regime_changes == 1:
        print("GATE 4 RESULT: PARTIAL EVIDENCE FOR NEW REGIMES")
        print("  One forcing condition produces qualitative change")
        print()
        print("  Change observed:")
        for c in all_changes:
            print(f"    - {c}")
    else:
        print("GATE 4 RESULT: NO CLEAR NEW REGIMES")
        print("  System remains in same qualitative regime under all forcing")
    
    return {
        'pressure': pressure_results,
        'confinement': confinement_results,
        'gradient': gradient_results,
        'num_regime_changes': num_regime_changes,
        'all_changes': all_changes,
    }


if __name__ == "__main__":
    results = run_gate_4_test()
