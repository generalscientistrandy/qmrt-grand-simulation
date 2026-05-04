"""
Phase 6, Gate 3: Multi-Scale Organization
==========================================

Question: Does the relational structure persist and organize across
multiple scales, rather than only existing as one dense connected web?

"Multi-scale organization" means:
- Structure visible at coarse-grained levels
- Correlation lengths that extend beyond local clustering
- Community/modular organization
- Hierarchical or scale-invariant properties
- Coarse-graining stability

Tests:
1. Spatial correlation at multiple scales
2. Coarse-graining: merge cells, check if structure survives
3. Community detection: modular vs monolithic organization
4. Scale-dependent clustering: structure at different thresholds
5. Correlation length measurement

Success criterion:
Evidence that organization exists across multiple scales, not just
as a single-scale dense network.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist, squareform
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import time


class MultiScaleSimulator:
    """
    Simulator for multi-scale analysis.
    """
    
    def __init__(
        self,
        size: int = 48,
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        gamma: float = 0.007,
    ):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.gamma = gamma
        
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
        return np.where(r <= interior_r, self.coupling_center, self.coupling_edge)
    
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
    
    def get_density_field(self, defects: List[Tuple], cell_size: int = 4) -> np.ndarray:
        """Create a coarse-grained density field."""
        n_cells = self.size // cell_size
        density = np.zeros((n_cells, n_cells, n_cells))
        
        for d in defects:
            cx = min(d[0] // cell_size, n_cells - 1)
            cy = min(d[1] // cell_size, n_cells - 1)
            cz = min(d[2] // cell_size, n_cells - 1)
            density[cx, cy, cz] += 1
        
        return density


def distance_periodic(p1: Tuple, p2: Tuple, size: int) -> float:
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def compute_spatial_correlation(defects: List[Tuple], size: int, max_r: float = None) -> Dict:
    """
    Compute spatial correlation function C(r).
    C(r) = <ρ(x)ρ(x+r)> / <ρ>²
    """
    if len(defects) < 10:
        return {'radii': [], 'correlation': []}
    
    if max_r is None:
        max_r = size / 2
    
    # Create density field at fine scale
    density = np.zeros((size, size, size))
    for d in defects:
        density[d[0], d[1], d[2]] = 1
    
    # Smooth to get continuous field
    density_smooth = gaussian_filter(density.astype(float), sigma=2.0)
    
    mean_density = np.mean(density_smooth)
    if mean_density < 1e-10:
        return {'radii': [], 'correlation': []}
    
    # Compute correlation at different radii
    radii = np.arange(2, int(max_r), 2)
    correlations = []
    
    for r in radii:
        # Sample point pairs at distance r
        samples = 0
        corr_sum = 0
        
        for _ in range(500):  # Monte Carlo sampling
            x1 = np.random.randint(0, size, 3)
            
            # Random direction
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, np.pi)
            dx = int(r * np.sin(phi) * np.cos(theta))
            dy = int(r * np.sin(phi) * np.sin(theta))
            dz = int(r * np.cos(phi))
            
            x2 = (x1 + np.array([dx, dy, dz])) % size
            
            d1 = density_smooth[x1[0], x1[1], x1[2]]
            d2 = density_smooth[x2[0], x2[1], x2[2]]
            
            corr_sum += d1 * d2
            samples += 1
        
        if samples > 0:
            corr = corr_sum / samples / (mean_density ** 2)
            correlations.append(corr)
        else:
            correlations.append(0)
    
    return {'radii': radii, 'correlation': np.array(correlations)}


def estimate_correlation_length(radii: np.ndarray, correlation: np.ndarray) -> float:
    """
    Estimate correlation length from C(r).
    Find r where C(r) drops to 1/e of C(0).
    """
    if len(correlation) < 2:
        return 0
    
    c0 = correlation[0]
    target = c0 / np.e
    
    for i, c in enumerate(correlation):
        if c < target:
            if i > 0:
                # Linear interpolation
                r1, r2 = radii[i-1], radii[i]
                c1, c2 = correlation[i-1], correlation[i]
                if c1 != c2:
                    xi = r1 + (target - c1) * (r2 - r1) / (c2 - c1)
                    return xi
            return radii[i]
    
    return radii[-1]  # Correlation extends beyond measured range


def coarse_grain_defects(defects: List[Tuple], cell_size: int, grid_size: int) -> List[Tuple]:
    """
    Coarse-grain defects into cells. Return cell centroids with defect counts.
    """
    n_cells = grid_size // cell_size
    cell_counts = defaultdict(int)
    cell_positions = defaultdict(list)
    
    for d in defects:
        cx = min(d[0] // cell_size, n_cells - 1)
        cy = min(d[1] // cell_size, n_cells - 1)
        cz = min(d[2] // cell_size, n_cells - 1)
        cell_counts[(cx, cy, cz)] += 1
        cell_positions[(cx, cy, cz)].append(d)
    
    # Return non-empty cell centers
    coarse_defects = []
    for cell, count in cell_counts.items():
        if count > 0:
            # Use cell center as position
            cx = cell[0] * cell_size + cell_size // 2
            cy = cell[1] * cell_size + cell_size // 2
            cz = cell[2] * cell_size + cell_size // 2
            coarse_defects.append((cx, cy, cz, count))  # Include count as weight
    
    return coarse_defects


def compute_structure_at_scale(defects: List[Tuple], cell_size: int, grid_size: int) -> Dict:
    """
    Analyze structure at a given coarse-graining scale.
    """
    coarse = coarse_grain_defects(defects, cell_size, grid_size)
    
    if len(coarse) < 2:
        return {
            'num_cells': len(coarse),
            'mean_occupancy': 0,
            'occupancy_variance': 0,
            'clustering_coefficient': 0,
        }
    
    positions = [(c[0], c[1], c[2]) for c in coarse]
    weights = [c[3] for c in coarse]
    
    mean_occ = np.mean(weights)
    var_occ = np.var(weights)
    
    # Compute clustering at this scale
    # Using pair correlation at interaction radius = 2 * cell_size
    interaction_r = 2 * cell_size
    
    n_pairs = 0
    n_close = 0
    
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            d = distance_periodic(positions[i], positions[j], grid_size)
            n_pairs += 1
            if d < interaction_r:
                n_close += 1
    
    clustering = n_close / n_pairs if n_pairs > 0 else 0
    
    return {
        'num_cells': len(coarse),
        'mean_occupancy': mean_occ,
        'occupancy_variance': var_occ,
        'clustering_coefficient': clustering,
        'total_defects': sum(weights),
    }


def detect_communities(defects: List[Tuple], size: int, interaction_radius: float = 10.0) -> List[Set[int]]:
    """
    Simple community detection via connected components at given radius.
    """
    if len(defects) < 2:
        return [set(range(len(defects)))]
    
    # Build adjacency
    adj = defaultdict(set)
    for i in range(len(defects)):
        for j in range(i + 1, len(defects)):
            d = distance_periodic(defects[i], defects[j], size)
            if d < interaction_radius:
                adj[i].add(j)
                adj[j].add(i)
    
    # Find connected components
    visited = set()
    communities = []
    
    for start in range(len(defects)):
        if start in visited:
            continue
        
        community = set()
        queue = [start]
        
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            community.add(node)
            queue.extend(adj[node] - visited)
        
        communities.append(community)
    
    return communities


def run_gate_3_test():
    """
    Phase 6, Gate 3: Test for multi-scale organization.
    """
    print("=" * 70)
    print("PHASE 6, GATE 3: MULTI-SCALE ORGANIZATION")
    print("=" * 70)
    print()
    print("Question: Does organization persist across multiple scales?")
    print()
    
    sim = MultiScaleSimulator(size=48, coupling_center=0.7, coupling_edge=0.2)
    np.random.seed(42)
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    
    # Inject vortices
    center = sim.size // 2
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) + abs(j) <= 3:
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    print("Equilibrating (500 steps)...")
    for _ in range(500):
        sim.step()
    
    print("Collecting multi-scale data (1500 steps)...")
    print()
    
    # Collect defect configurations over time
    all_defects = []
    for step in range(1500):
        sim.step()
        if step % 50 == 0:
            defects = sim.detect_defects()
            all_defects.append(defects)
            if step % 500 == 0:
                print(f"  Step {step}: {len(defects)} defects")
    
    # Combine all snapshots for better statistics
    combined_defects = []
    for d_list in all_defects[-20:]:  # Last 20 snapshots
        combined_defects.extend(d_list)
    
    print()
    print(f"Total defect observations: {len(combined_defects)}")
    print()
    
    # TEST 1: Spatial correlation and correlation length
    print("-" * 70)
    print("TEST 1: SPATIAL CORRELATION FUNCTION")
    print("-" * 70)
    print()
    
    # Use a representative snapshot
    test_defects = all_defects[-10] if all_defects else []
    
    if len(test_defects) >= 10:
        corr_result = compute_spatial_correlation(test_defects, sim.size)
        
        if len(corr_result['correlation']) > 0:
            print("C(r) at different scales:")
            for i in range(0, len(corr_result['radii']), 2):
                r = corr_result['radii'][i]
                c = corr_result['correlation'][i]
                print(f"  r={r:4.0f}: C(r)={c:.3f}")
            
            xi = estimate_correlation_length(
                np.array(corr_result['radii']), 
                corr_result['correlation']
            )
            print(f"\nCorrelation length ξ ≈ {xi:.1f} grid units")
            print(f"System size L = {sim.size}")
            print(f"ξ/L = {xi/sim.size:.2f}")
        else:
            print("Insufficient data for correlation function")
            xi = 0
    else:
        print("Too few defects for correlation analysis")
        xi = 0
    
    # TEST 2: Coarse-graining stability
    print()
    print("-" * 70)
    print("TEST 2: COARSE-GRAINING STABILITY")
    print("-" * 70)
    print()
    print("Does structure survive when we coarse-grain?")
    print()
    
    cell_sizes = [2, 4, 8, 12, 16]
    scale_results = []
    
    for cell_size in cell_sizes:
        result = compute_structure_at_scale(test_defects, cell_size, sim.size)
        scale_results.append(result)
        
        print(f"Cell size {cell_size:2d}: "
              f"{result['num_cells']:3d} cells, "
              f"mean occ={result['mean_occupancy']:.2f}, "
              f"var={result['occupancy_variance']:.2f}, "
              f"clustering={result['clustering_coefficient']:.3f}")
    
    # Check if structure persists
    # Structure persists if variance/mean (coefficient of variation) stays significant
    cv_values = []
    for r in scale_results:
        if r['mean_occupancy'] > 0:
            cv = np.sqrt(r['occupancy_variance']) / r['mean_occupancy']
            cv_values.append(cv)
        else:
            cv_values.append(0)
    
    print()
    print("Coefficient of variation (CV) by scale:")
    for i, cell_size in enumerate(cell_sizes):
        print(f"  Cell {cell_size:2d}: CV = {cv_values[i]:.2f}")
    
    # TEST 3: Community structure at multiple scales
    print()
    print("-" * 70)
    print("TEST 3: COMMUNITY STRUCTURE AT MULTIPLE SCALES")
    print("-" * 70)
    print()
    
    interaction_radii = [6, 10, 15, 20]
    
    for radius in interaction_radii:
        communities = detect_communities(test_defects, sim.size, radius)
        sizes = sorted([len(c) for c in communities], reverse=True)
        
        print(f"Interaction radius {radius:2d}: "
              f"{len(communities)} communities, "
              f"sizes: {sizes[:5]}")
    
    # TEST 4: Scale-dependent clustering statistics
    print()
    print("-" * 70)
    print("TEST 4: CLUSTERING ACROSS SCALES")
    print("-" * 70)
    print()
    
    # Compute clustering at different scales using multiple snapshots
    scale_clustering = defaultdict(list)
    
    for defects in all_defects[-10:]:
        if len(defects) < 5:
            continue
        
        for radius in [5, 10, 15, 20]:
            communities = detect_communities(defects, sim.size, radius)
            if len(communities) > 0:
                largest_frac = max(len(c) for c in communities) / len(defects)
                scale_clustering[radius].append(largest_frac)
    
    print("Largest community fraction by interaction scale:")
    for radius in sorted(scale_clustering.keys()):
        fracs = scale_clustering[radius]
        if fracs:
            print(f"  Radius {radius:2d}: mean={np.mean(fracs):.2f}, "
                  f"std={np.std(fracs):.2f}")
    
    # Summary
    print()
    print("=" * 70)
    print("GATE 3 ASSESSMENT")
    print("=" * 70)
    print()
    
    evidence_for_multiscale = []
    evidence_against = []
    
    # Correlation length
    if xi > sim.size * 0.2:
        evidence_for_multiscale.append(f"Long correlation length (ξ={xi:.1f}, ξ/L={xi/sim.size:.2f})")
    elif xi > sim.size * 0.1:
        evidence_for_multiscale.append(f"Moderate correlation length (ξ={xi:.1f})")
    else:
        evidence_against.append(f"Short correlation length (ξ={xi:.1f})")
    
    # Coarse-graining
    if len(cv_values) >= 3 and all(cv > 0.3 for cv in cv_values[:3]):
        evidence_for_multiscale.append("Structure survives coarse-graining (CV > 0.3 at all scales)")
    elif len(cv_values) >= 2 and cv_values[0] > 0.3 and cv_values[1] > 0.3:
        evidence_for_multiscale.append("Structure survives to intermediate scale")
    else:
        evidence_against.append("Structure lost under coarse-graining")
    
    # Community structure
    if scale_clustering:
        small_scale = scale_clustering.get(5, [])
        large_scale = scale_clustering.get(20, [])
        
        if small_scale and large_scale:
            if np.mean(large_scale) < 0.9:  # Not fully connected at large scale
                evidence_for_multiscale.append("Modular structure (not monolithic at large scale)")
            else:
                evidence_against.append("Monolithic structure at large scale")
    
    # Multi-scale community hierarchy
    if len(scale_clustering) >= 3:
        # Check if there's a hierarchy (different structure at different scales)
        means = [np.mean(scale_clustering[r]) for r in sorted(scale_clustering.keys())]
        if max(means) - min(means) > 0.2:
            evidence_for_multiscale.append("Hierarchical community structure across scales")
    
    print("EVIDENCE FOR MULTI-SCALE ORGANIZATION:")
    if evidence_for_multiscale:
        for e in evidence_for_multiscale:
            print(f"  + {e}")
    else:
        print("  (none)")
    
    print()
    print("EVIDENCE AGAINST:")
    if evidence_against:
        for e in evidence_against:
            print(f"  - {e}")
    else:
        print("  (none)")
    
    print()
    if len(evidence_for_multiscale) >= 3:
        print("GATE 3 RESULT: STRONG EVIDENCE FOR MULTI-SCALE ORGANIZATION")
        print("  Structure persists and organizes across multiple spatial scales")
    elif len(evidence_for_multiscale) >= 2:
        print("GATE 3 RESULT: MODERATE EVIDENCE FOR MULTI-SCALE ORGANIZATION")
        print("  Some multi-scale structure, but not fully hierarchical")
    else:
        print("GATE 3 RESULT: LIMITED MULTI-SCALE ORGANIZATION")
        print("  Structure primarily exists at single scale")
    
    return {
        'correlation_length': xi,
        'cv_values': cv_values,
        'scale_clustering': dict(scale_clustering),
        'evidence_for': evidence_for_multiscale,
        'evidence_against': evidence_against,
    }


if __name__ == "__main__":
    results = run_gate_3_test()
