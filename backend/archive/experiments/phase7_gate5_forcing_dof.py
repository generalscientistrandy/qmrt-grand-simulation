"""
Phase 7, Gate 5: DoF Hierarchy Under Forcing
=============================================

Central Question: Is the hybrid DoF hierarchy universal, or does forcing
shift the system into different organizational control regimes?

Gate 4 established that organization is hybrid:
- Position (geometric): ~0.42 score
- Coupling (κ-landscape): ~0.34 score
- Resonance (channel state): ~0.33 score

The key question is now:
Does extreme forcing change this hierarchy?

Tests:
1. Baseline (control): Standard parameters
2. Pressure extreme: High vortex density
3. Confinement extreme: Tight boundaries
4. Contrast extreme: Strong coupling gradient
5. Triple extreme: All three combined

For each regime, measure the DoF hierarchy and detect shifts.

Success criterion:
Either find regime(s) with different DoF dominance,
or establish that hybrid control is universal.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict
from typing import Dict, List, Tuple


class ForcingDoFSimulator:
    """
    Simulator with configurable forcing for DoF hierarchy testing.
    """
    
    def __init__(
        self,
        size: int = 48,
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        interior_radius_frac: float = 0.25,
        transition_width: float = 10.0,
    ):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.interior_radius_frac = interior_radius_frac
        self.transition_width = transition_width
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
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
        
        gamma = 0.007
        c_eff = 2.0
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff**2 * lap_r - gamma * self.psi_r_dot
        acc_i = c_eff**2 * lap_i - gamma * self.psi_i_dot
        
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
        
        self.remnant_field += 0.005 * (topology_norm - 0.3 * self.remnant_field)
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
    
    def detect_defects_with_properties(self, threshold: float = 0.4) -> List[Dict]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        coupling_grad = np.sqrt(
            np.gradient(self.coupling, axis=0)**2 +
            np.gradient(self.coupling, axis=1)**2 +
            np.gradient(self.coupling, axis=2)**2
        )
        
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
            
            defect = {
                'position': (cx, cy, cz),
                'radial_dist': np.sqrt((cx - 24)**2 + (cy - 24)**2 + (cz - 24)**2),
                'coupling_value': float(self.coupling[cx, cy, cz]),
                'coupling_gradient': float(coupling_grad[cx, cy, cz]),
                'topology_strength': float(topology[cx, cy, cz]),
                'channel_assignment': float(self.channel_assignment[cx, cy, cz]),
                'remnant_strength': float(self.remnant_field[cx, cy, cz]),
            }
            defects.append(defect)
        
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


def build_adjacency(defects: List[Dict], size: int, radius: float = 10.0) -> Dict[int, set]:
    adj = defaultdict(set)
    for i in range(len(defects)):
        for j in range(i + 1, len(defects)):
            d = euclidean_distance_periodic(
                defects[i]['position'], defects[j]['position'], size
            )
            if d < radius:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def compute_local_clustering(adj: Dict[int, set], node: int) -> float:
    neighbors = list(adj[node])
    k = len(neighbors)
    if k < 2:
        return 0.0
    
    triangles = 0
    for i_idx in range(len(neighbors)):
        for j_idx in range(i_idx + 1, len(neighbors)):
            if neighbors[j_idx] in adj[neighbors[i_idx]]:
                triangles += 1
    
    max_triangles = k * (k - 1) / 2
    return triangles / max_triangles if max_triangles > 0 else 0


def analyze_dof_hierarchy(defects: List[Dict], adj: Dict[int, set]) -> Dict:
    """Compute DoF hierarchy for a single snapshot."""
    n = len(defects)
    if n < 10:
        return {'valid': False}
    
    degrees = [len(adj[i]) for i in range(n)]
    clusterings = [compute_local_clustering(adj, i) for i in range(n)]
    degree_threshold = np.percentile(degrees, 80)
    is_hub = [1 if d >= degree_threshold else 0 for d in degrees]
    
    dof_values = {
        'radial_dist': [d['radial_dist'] for d in defects],
        'coupling_value': [d['coupling_value'] for d in defects],
        'coupling_gradient': [d['coupling_gradient'] for d in defects],
        'topology_strength': [d['topology_strength'] for d in defects],
        'channel_assignment': [d['channel_assignment'] for d in defects],
        'remnant_strength': [d['remnant_strength'] for d in defects],
    }
    
    scores = {}
    for dof_name, dof_vals in dof_values.items():
        if np.std(dof_vals) > 0:
            degree_corr = abs(pearsonr(dof_vals, degrees)[0])
            clustering_corr = abs(pearsonr(dof_vals, clusterings)[0])
            hub_corr = abs(pearsonr(dof_vals, is_hub)[0])
        else:
            degree_corr = clustering_corr = hub_corr = 0
        scores[dof_name] = degree_corr + clustering_corr + hub_corr
    
    return {'valid': True, 'scores': scores, 'n_defects': n}


def run_forcing_regime(
    name: str,
    n_vortices: int,
    coupling_center: float,
    coupling_edge: float,
    interior_radius_frac: float,
    transition_width: float,
    vortex_spacing: int = 3,
) -> Dict:
    """Run a single forcing regime and measure DoF hierarchy."""
    print(f"\n  Regime: {name}")
    print(f"    Params: {n_vortices} vortices, r={interior_radius_frac:.0%}, "
          f"Δκ={coupling_center-coupling_edge:.2f}")
    
    sim = ForcingDoFSimulator(
        size=48,
        coupling_center=coupling_center,
        coupling_edge=coupling_edge,
        interior_radius_frac=interior_radius_frac,
        transition_width=transition_width,
    )
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    center = 24
    injected = 0
    for i in range(-8, 9):
        for j in range(-8, 9):
            if injected >= n_vortices:
                break
            if abs(i) + abs(j) <= 8:
                sim.inject_vortex(center + i * vortex_spacing, center + j * vortex_spacing)
                injected += 1
        if injected >= n_vortices:
            break
    
    print(f"    Equilibrating...", end=" ", flush=True)
    for _ in range(700):
        sim.step()
    print("done")
    
    print(f"    Measuring...", end=" ", flush=True)
    all_scores = []
    for step in range(500):
        sim.step()
        if step % 50 == 0:
            defects = sim.detect_defects_with_properties()
            if len(defects) >= 15:
                adj = build_adjacency(defects, sim.size)
                result = analyze_dof_hierarchy(defects, adj)
                if result['valid']:
                    all_scores.append(result['scores'])
                    print(".", end="", flush=True)
    print()
    
    if not all_scores:
        return {'valid': False, 'name': name}
    
    # Aggregate scores
    dof_names = ['radial_dist', 'coupling_value', 'coupling_gradient',
                 'topology_strength', 'channel_assignment', 'remnant_strength']
    
    mean_scores = {}
    for dof in dof_names:
        vals = [s[dof] for s in all_scores]
        mean_scores[dof] = np.mean(vals)
    
    # Rank
    ranked = sorted(mean_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Determine dominant category
    top_dof = ranked[0][0]
    if top_dof == 'radial_dist':
        dominant = 'GEOMETRIC'
    elif top_dof in ['coupling_value', 'coupling_gradient']:
        dominant = 'COUPLING'
    elif top_dof == 'channel_assignment':
        dominant = 'RESONANCE'
    elif top_dof == 'topology_strength':
        dominant = 'TOPOLOGICAL'
    else:
        dominant = 'MEMORY'
    
    # Check for hybrid (top 3 within 30% of each other)
    top3_scores = [ranked[i][1] for i in range(min(3, len(ranked)))]
    if max(top3_scores) > 0 and (max(top3_scores) - min(top3_scores)) / max(top3_scores) < 0.30:
        dominant = 'HYBRID'
    
    return {
        'valid': True,
        'name': name,
        'scores': mean_scores,
        'ranked': ranked,
        'dominant': dominant,
        'top_dof': top_dof,
        'n_samples': len(all_scores),
    }


def run_gate5_tests():
    """
    Run Gate 5: DoF hierarchy under different forcing regimes.
    """
    print("=" * 70)
    print("PHASE 7, GATE 5: DOF HIERARCHY UNDER FORCING")
    print("=" * 70)
    print()
    print("Question: Is the hybrid DoF hierarchy universal or regime-dependent?")
    print()
    
    results = []
    
    # Test 1: Baseline
    print("-" * 70)
    print("TEST 1: BASELINE (Control)")
    print("-" * 70)
    results.append(run_forcing_regime(
        name="Baseline",
        n_vortices=25,
        coupling_center=0.7,
        coupling_edge=0.2,
        interior_radius_frac=0.25,
        transition_width=10.0,
    ))
    
    # Test 2: Pressure extreme
    print()
    print("-" * 70)
    print("TEST 2: PRESSURE EXTREME (High density)")
    print("-" * 70)
    results.append(run_forcing_regime(
        name="Pressure Extreme",
        n_vortices=120,
        coupling_center=0.7,
        coupling_edge=0.2,
        interior_radius_frac=0.25,
        transition_width=10.0,
        vortex_spacing=2,
    ))
    
    # Test 3: Confinement extreme
    print()
    print("-" * 70)
    print("TEST 3: CONFINEMENT EXTREME (Tight boundaries)")
    print("-" * 70)
    results.append(run_forcing_regime(
        name="Confinement Extreme",
        n_vortices=30,
        coupling_center=0.9,
        coupling_edge=0.1,
        interior_radius_frac=0.08,
        transition_width=3.0,
    ))
    
    # Test 4: Contrast extreme
    print()
    print("-" * 70)
    print("TEST 4: CONTRAST EXTREME (Strong gradient)")
    print("-" * 70)
    results.append(run_forcing_regime(
        name="Contrast Extreme",
        n_vortices=25,
        coupling_center=0.98,
        coupling_edge=0.02,
        interior_radius_frac=0.25,
        transition_width=5.0,
    ))
    
    # Test 5: Triple extreme
    print()
    print("-" * 70)
    print("TEST 5: TRIPLE EXTREME (All combined)")
    print("-" * 70)
    results.append(run_forcing_regime(
        name="Triple Extreme",
        n_vortices=100,
        coupling_center=0.95,
        coupling_edge=0.02,
        interior_radius_frac=0.08,
        transition_width=3.0,
        vortex_spacing=2,
    ))
    
    # Summary
    print()
    print("=" * 70)
    print("GATE 5 RESULTS SUMMARY")
    print("=" * 70)
    print()
    
    valid_results = [r for r in results if r['valid']]
    
    print(f"{'Regime':<22} {'Top DoF':<22} {'Score':>7} {'Dominant':>12}")
    print("-" * 65)
    
    for r in valid_results:
        print(f"{r['name']:<22} {r['top_dof']:<22} {r['scores'][r['top_dof']]:>7.3f} {r['dominant']:>12}")
    
    # Detailed scores
    print()
    print("-" * 70)
    print("DETAILED DOF SCORES BY REGIME")
    print("-" * 70)
    print()
    
    dof_names = ['radial_dist', 'coupling_value', 'channel_assignment']
    
    print(f"{'Regime':<22}", end="")
    for dof in dof_names:
        short_name = dof[:10]
        print(f" {short_name:>10}", end="")
    print()
    print("-" * 55)
    
    for r in valid_results:
        print(f"{r['name']:<22}", end="")
        for dof in dof_names:
            print(f" {r['scores'][dof]:>10.3f}", end="")
        print()
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS: HIERARCHY STABILITY")
    print("-" * 70)
    print()
    
    dominants = [r['dominant'] for r in valid_results]
    unique_dominants = set(dominants)
    
    if len(unique_dominants) == 1:
        print(f"FINDING: DoF hierarchy is UNIVERSAL")
        print(f"  All regimes show {dominants[0]} organization")
        print(f"  Extreme forcing does not change the dominant control structure")
    else:
        print(f"FINDING: DoF hierarchy is REGIME-DEPENDENT")
        print(f"  Different regimes show different dominant DoFs:")
        for r in valid_results:
            print(f"    {r['name']}: {r['dominant']} ({r['top_dof']})")
    
    # Check for specific transitions
    baseline_top = valid_results[0]['top_dof'] if valid_results else None
    shifts = []
    for r in valid_results[1:]:
        if r['top_dof'] != baseline_top:
            shifts.append((r['name'], baseline_top, r['top_dof']))
    
    if shifts:
        print()
        print("HIERARCHY SHIFTS DETECTED:")
        for regime, from_dof, to_dof in shifts:
            print(f"  {regime}: {from_dof} → {to_dof}")
    
    # Gate assessment
    print()
    print("=" * 70)
    print("GATE 5 ASSESSMENT")
    print("=" * 70)
    print()
    
    if len(unique_dominants) == 1 and dominants[0] == 'HYBRID':
        print("GATE 5 RESULT: UNIVERSAL HYBRID CONTROL")
        print("  The distributed DoF hierarchy is stable across all forcing regimes")
        print("  Position, coupling, and resonance contribute comparably everywhere")
        print()
        print("IMPLICATION: Hybrid control is a fundamental property of proto-spacetime")
    elif len(unique_dominants) == 1:
        dom = dominants[0]
        print(f"GATE 5 RESULT: UNIVERSAL {dom} CONTROL")
        print(f"  All regimes show {dom}-dominated organization")
        print(f"  Extreme forcing does not induce organizational phase transitions")
    else:
        print("GATE 5 RESULT: MULTIPLE ORGANIZATIONAL PHASES")
        print("  Different forcing regimes produce different DoF hierarchies")
        print("  The system can be pushed into different organizational modes")
        print()
        print("IMPLICATION: Proto-spacetime has multiple organizational phases")
        for dom in unique_dominants:
            matching = [r['name'] for r in valid_results if r['dominant'] == dom]
            print(f"  {dom}: {', '.join(matching)}")
    
    return results


if __name__ == "__main__":
    results = run_gate5_tests()
