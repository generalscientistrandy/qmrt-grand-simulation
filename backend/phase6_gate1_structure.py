"""
Phase 6, Gate 1: Higher-Order Collective Structure
===================================================

Question: Do defect populations remain merely ecological, or do they
produce higher-order collective structure?

"Higher-order structure" means:
- Persistent clusters (defects that stay together as a unit)
- Spatial correlations beyond random placement
- Emergent patterns at scales larger than individual defects
- Correlated behavior between multiple defects

Tests:
1. Clustering analysis - do defects form persistent groups?
2. Pair correlation function - is there structure beyond density?
3. Cluster lifetime - do multi-defect configurations persist?
4. Pressure test - does crowding induce new collective modes?

Success criterion:
Evidence that populations organize beyond simple density distributions
into persistent multi-defect structures or correlated configurations.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import fcluster, linkage
from typing import Dict, List, Tuple
import time


class Phase6Simulator:
    """
    Simulator for Phase 6 higher-order structure tests.
    Enhanced tracking for collective behavior analysis.
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
    
    def get_region(self, x: int, y: int, z: int) -> str:
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        if r <= self.size * 0.25:
            return 'interior'
        elif r <= self.size * 0.25 + 8:
            return 'transition'
        return 'periphery'
    
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


def compute_pair_correlation(defects: List[Tuple], size: int, bins: int = 15) -> Dict:
    """
    Compute pair correlation function g(r).
    g(r) > 1 indicates clustering at distance r.
    g(r) < 1 indicates avoidance at distance r.
    g(r) = 1 indicates random (Poisson) distribution.
    """
    if len(defects) < 2:
        return {'distances': [], 'g_r': [], 'bins': []}
    
    positions = np.array(defects)
    n = len(positions)
    
    # Compute all pairwise distances
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            d = positions[i] - positions[j]
            # Handle periodic boundaries
            d = np.abs(d)
            d = np.minimum(d, size - d)
            distances.append(np.sqrt(np.sum(d**2)))
    
    if not distances:
        return {'distances': [], 'g_r': [], 'bins': []}
    
    distances = np.array(distances)
    
    # Bin the distances
    max_r = size / 2
    bin_edges = np.linspace(0, max_r, bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    hist, _ = np.histogram(distances, bins=bin_edges)
    
    # Normalize by expected count for random distribution
    # Expected pairs in shell [r, r+dr] = n*(n-1)/2 * (4πr²dr) / V
    V = size**3
    density = n / V
    
    g_r = []
    for i in range(len(bin_centers)):
        r = bin_centers[i]
        dr = bin_edges[i + 1] - bin_edges[i]
        shell_vol = 4 * np.pi * r**2 * dr
        expected = n * (n - 1) / 2 * shell_vol / V
        if expected > 0:
            g_r.append(hist[i] / expected)
        else:
            g_r.append(0)
    
    return {
        'bin_centers': bin_centers,
        'g_r': np.array(g_r),
        'raw_hist': hist,
    }


def identify_clusters(defects: List[Tuple], cluster_radius: float = 8.0) -> List[List[int]]:
    """
    Identify clusters of defects within cluster_radius of each other.
    Returns list of cluster memberships.
    """
    if len(defects) < 2:
        return [[i] for i in range(len(defects))]
    
    positions = np.array(defects)
    
    # Compute distance matrix
    n = len(positions)
    dist_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            d = np.abs(positions[i] - positions[j])
            d = np.minimum(d, 48 - d)  # Periodic
            dist = np.sqrt(np.sum(d**2))
            dist_matrix[i, j] = dist
            dist_matrix[j, i] = dist
    
    # Hierarchical clustering
    if n > 1:
        condensed = squareform(dist_matrix)
        Z = linkage(condensed, method='single')
        labels = fcluster(Z, t=cluster_radius, criterion='distance')
    else:
        labels = [1]
    
    # Group by cluster
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(i)
    
    return list(clusters.values())


def track_cluster_persistence(
    sim: Phase6Simulator,
    steps: int = 1500,
    sample_interval: int = 25,
    cluster_radius: float = 8.0,
) -> Dict:
    """
    Track whether clusters persist over time.
    """
    cluster_lifetimes = []
    active_clusters = {}  # cluster_id -> (birth_step, member_indices)
    next_cluster_id = 0
    
    prev_defects = []
    prev_clusters = []
    
    all_cluster_sizes = []
    multi_defect_cluster_counts = []
    
    for step in range(steps):
        sim.step()
        
        if step % sample_interval == 0:
            defects = sim.detect_defects()
            clusters = identify_clusters(defects, cluster_radius)
            
            # Count multi-defect clusters
            multi = sum(1 for c in clusters if len(c) > 1)
            multi_defect_cluster_counts.append(multi)
            
            # Track cluster sizes
            for c in clusters:
                all_cluster_sizes.append(len(c))
            
            prev_defects = defects
            prev_clusters = clusters
    
    return {
        'multi_defect_cluster_counts': multi_defect_cluster_counts,
        'all_cluster_sizes': all_cluster_sizes,
        'mean_cluster_size': np.mean(all_cluster_sizes) if all_cluster_sizes else 0,
        'max_cluster_size': max(all_cluster_sizes) if all_cluster_sizes else 0,
        'fraction_in_clusters': sum(1 for s in all_cluster_sizes if s > 1) / len(all_cluster_sizes) if all_cluster_sizes else 0,
    }


def run_gate_1_test():
    """
    Phase 6, Gate 1: Test for higher-order collective structure.
    """
    print("=" * 70)
    print("PHASE 6, GATE 1: HIGHER-ORDER COLLECTIVE STRUCTURE")
    print("=" * 70)
    print()
    print("Question: Do populations produce structure beyond simple ecology?")
    print()
    
    # Test 1: Pair correlation function
    print("-" * 70)
    print("TEST 1: PAIR CORRELATION FUNCTION")
    print("-" * 70)
    print()
    print("g(r) > 1 indicates clustering")
    print("g(r) < 1 indicates avoidance")
    print("g(r) = 1 indicates random (Poisson)")
    print()
    
    sim = Phase6Simulator(size=48, coupling_center=0.7, coupling_edge=0.2)
    np.random.seed(42)
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    
    # Inject some vortices to seed population
    center = sim.size // 2
    for offset in [(-6, -6), (-6, 6), (6, -6), (6, 6), (0, 0)]:
        sim.inject_vortex(center + offset[0], center + offset[1])
    
    print("Running simulation to equilibrium...")
    for step in range(1000):
        sim.step()
        if step % 250 == 0:
            print(f"  Step {step}")
    
    # Collect pair correlation over late time
    g_r_samples = []
    for step in range(500):
        sim.step()
        if step % 50 == 0:
            defects = sim.detect_defects()
            if len(defects) >= 3:
                pcf = compute_pair_correlation(defects, sim.size)
                if len(pcf['g_r']) > 0:
                    g_r_samples.append(pcf['g_r'])
    
    if g_r_samples:
        mean_g_r = np.mean(g_r_samples, axis=0)
        bin_centers = compute_pair_correlation(defects, sim.size)['bin_centers']
        
        print()
        print("Pair correlation g(r):")
        for i in range(min(8, len(mean_g_r))):
            r = bin_centers[i]
            g = mean_g_r[i]
            status = "CLUSTERING" if g > 1.2 else ("AVOIDANCE" if g < 0.8 else "~random")
            print(f"  r={r:.1f}: g(r)={g:.2f} [{status}]")
        
        # Check for short-range clustering
        short_range_g = np.mean(mean_g_r[:3]) if len(mean_g_r) >= 3 else 0
        print()
        print(f"Short-range (r < {bin_centers[2]:.0f}) mean g(r): {short_range_g:.2f}")
    else:
        print("Insufficient data for pair correlation")
        short_range_g = 1.0
    
    # Test 2: Cluster analysis
    print()
    print("-" * 70)
    print("TEST 2: CLUSTER PERSISTENCE")
    print("-" * 70)
    print()
    
    sim2 = Phase6Simulator(size=48, coupling_center=0.7, coupling_edge=0.2)
    np.random.seed(42)
    sim2.psi_r += 0.05 * np.random.randn(sim2.size, sim2.size, sim2.size)
    sim2.psi_i += 0.05 * np.random.randn(sim2.size, sim2.size, sim2.size)
    
    for offset in [(-6, -6), (-6, 6), (6, -6), (6, 6), (0, 0)]:
        sim2.inject_vortex(center + offset[0], center + offset[1])
    
    print("Tracking cluster formation over 1500 steps...")
    cluster_results = track_cluster_persistence(sim2, steps=1500, cluster_radius=8.0)
    
    print()
    print(f"Mean cluster size: {cluster_results['mean_cluster_size']:.2f}")
    print(f"Max cluster size observed: {cluster_results['max_cluster_size']}")
    print(f"Fraction of defects in multi-defect clusters: {cluster_results['fraction_in_clusters']:.1%}")
    print(f"Mean multi-defect clusters per sample: {np.mean(cluster_results['multi_defect_cluster_counts']):.2f}")
    
    # Test 3: High-pressure clustering
    print()
    print("-" * 70)
    print("TEST 3: HIGH-PRESSURE REGIME")
    print("-" * 70)
    print()
    print("Does crowding induce stronger clustering?")
    print()
    
    sim3 = Phase6Simulator(size=48, coupling_center=0.7, coupling_edge=0.2)
    np.random.seed(42)
    sim3.psi_r += 0.05 * np.random.randn(sim3.size, sim3.size, sim3.size)
    sim3.psi_i += 0.05 * np.random.randn(sim3.size, sim3.size, sim3.size)
    
    # Inject many vortices
    for i in range(-2, 3):
        for j in range(-2, 3):
            sim3.inject_vortex(center + i * 4, center + j * 4)
    
    print("Injected 25 vortices in interior...")
    
    high_pressure_clusters = track_cluster_persistence(sim3, steps=1000, cluster_radius=8.0)
    
    print()
    print(f"High-pressure mean cluster size: {high_pressure_clusters['mean_cluster_size']:.2f}")
    print(f"High-pressure max cluster size: {high_pressure_clusters['max_cluster_size']}")
    print(f"High-pressure fraction in clusters: {high_pressure_clusters['fraction_in_clusters']:.1%}")
    
    # Summary
    print()
    print("=" * 70)
    print("GATE 1 ASSESSMENT")
    print("=" * 70)
    print()
    
    evidence_for_structure = []
    evidence_against = []
    
    if short_range_g > 1.3:
        evidence_for_structure.append(f"Strong short-range clustering (g(r)={short_range_g:.2f})")
    elif short_range_g > 1.1:
        evidence_for_structure.append(f"Weak short-range clustering (g(r)={short_range_g:.2f})")
    else:
        evidence_against.append(f"No significant clustering (g(r)={short_range_g:.2f})")
    
    if cluster_results['mean_cluster_size'] > 1.5:
        evidence_for_structure.append(f"Multi-defect clusters common (mean size {cluster_results['mean_cluster_size']:.2f})")
    else:
        evidence_against.append(f"Clusters mostly single defects (mean size {cluster_results['mean_cluster_size']:.2f})")
    
    if high_pressure_clusters['mean_cluster_size'] > cluster_results['mean_cluster_size'] * 1.3:
        evidence_for_structure.append("Pressure increases clustering")
    
    print("EVIDENCE FOR HIGHER-ORDER STRUCTURE:")
    if evidence_for_structure:
        for e in evidence_for_structure:
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
    if len(evidence_for_structure) > len(evidence_against):
        print("GATE 1 RESULT: EVIDENCE FOR HIGHER-ORDER STRUCTURE")
        print("  Populations show organization beyond simple density distribution")
    else:
        print("GATE 1 RESULT: NO CLEAR HIGHER-ORDER STRUCTURE")
        print("  Populations remain at ecological level without persistent clusters")
    
    return {
        'short_range_g': short_range_g,
        'mean_cluster_size': cluster_results['mean_cluster_size'],
        'high_pressure_cluster_size': high_pressure_clusters['mean_cluster_size'],
        'evidence_for': evidence_for_structure,
        'evidence_against': evidence_against,
    }


if __name__ == "__main__":
    results = run_gate_1_test()
