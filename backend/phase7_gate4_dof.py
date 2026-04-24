"""
Phase 7, Gate 4: Degrees of Freedom Enumeration
================================================

Central Question: Which degrees of freedom carry the richer organizational
behavior in the proto-spacetime regime?

Gates 1-3 established:
- Metric-like structure exists
- Spatial dimension is robustly ~1D (filamentary)
- Extreme forcing enriches local structure but not global dimension

The key question is now:
WHERE is the organizational complexity actually living?

Candidate Degrees of Freedom:
A. Spatial/Geometric
   - Position (x, y, z)
   - Graph connectivity / neighborhood

B. Coupling Landscape
   - Local coupling value κ(x)
   - Gradient magnitude |∇κ|

C. Topology/Winding
   - Vorticity / winding number
   - Defect charge

D. Resonance/Channel
   - Channel assignment state
   - Resonance amplitude

E. Memory/Remnant
   - Remnant field strength
   - Memory persistence

F. Population Context
   - Local defect density
   - Nearest-neighbor distances

This gate will measure the correlation between each candidate DoF
and the richer organizational features (clustering, hubs, regeneration).

Success criterion:
Identify which DoF(s) best predict organizational richness.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr, spearmanr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import time


class DoFEnumerationSimulator:
    """
    Simulator that tracks all candidate degrees of freedom.
    """
    
    def __init__(self, size: int = 48):
        self.size = size
        
        # Field state
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Channel/resonance state (DoF)
        self.channel_assignment = np.zeros((size, size, size))
        
        # Memory/remnant state (DoF)
        self.remnant_field = np.zeros((size, size, size))
        
        # Coupling landscape (DoF)
        self.coupling = self._create_coupling()
        
        # Topology tracking
        self.topology_history = []
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        transition_width = 10.0
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = 0.7
                    elif dist >= interior_r + transition_width:
                        coupling[i, j, k] = 0.2
                    else:
                        t = (dist - interior_r) / transition_width
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = 0.7 + blend * (0.2 - 0.7)
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
        
        # Topology computation
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Update channel assignment (resonance DoF)
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        # Update remnant field (memory DoF)
        # Remnant grows where topology is high, decays slowly elsewhere
        self.remnant_field += 0.005 * (topology_norm - 0.3 * self.remnant_field)
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        # Protection mechanism
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
        """Detect defects and measure all DoF values at each defect location."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        # Topology field
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Coupling gradient
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
            
            # Measure all DoF values at defect center
            defect = {
                # Position (geometric DoF)
                'position': (cx, cy, cz),
                'radial_dist': np.sqrt((cx - 24)**2 + (cy - 24)**2 + (cz - 24)**2),
                
                # Coupling landscape (κ DoF)
                'coupling_value': float(self.coupling[cx, cy, cz]),
                'coupling_gradient': float(coupling_grad[cx, cy, cz]),
                
                # Topology/winding (topological DoF)
                'topology_strength': float(topology[cx, cy, cz]),
                
                # Channel/resonance (resonance DoF)
                'channel_assignment': float(self.channel_assignment[cx, cy, cz]),
                
                # Memory/remnant (memory DoF)
                'remnant_strength': float(self.remnant_field[cx, cy, cz]),
                
                # Local amplitude (field state)
                'local_amplitude': float(amp[cx, cy, cz]),
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
    """Compute clustering coefficient for a single node."""
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


def analyze_dof_correlations(defects: List[Dict], adj: Dict[int, set]) -> Dict:
    """
    Analyze correlations between each DoF and organizational features.
    """
    n = len(defects)
    if n < 10:
        return {'valid': False}
    
    # Compute organizational features for each defect
    degrees = [len(adj[i]) for i in range(n)]
    clusterings = [compute_local_clustering(adj, i) for i in range(n)]
    
    # Identify hubs (high degree nodes)
    degree_threshold = np.percentile(degrees, 80)
    is_hub = [1 if d >= degree_threshold else 0 for d in degrees]
    
    # Extract DoF values
    dof_values = {
        'radial_dist': [d['radial_dist'] for d in defects],
        'coupling_value': [d['coupling_value'] for d in defects],
        'coupling_gradient': [d['coupling_gradient'] for d in defects],
        'topology_strength': [d['topology_strength'] for d in defects],
        'channel_assignment': [d['channel_assignment'] for d in defects],
        'remnant_strength': [d['remnant_strength'] for d in defects],
    }
    
    # Compute correlations
    correlations = {}
    for dof_name, dof_vals in dof_values.items():
        correlations[dof_name] = {
            'degree': pearsonr(dof_vals, degrees)[0] if np.std(dof_vals) > 0 else 0,
            'clustering': pearsonr(dof_vals, clusterings)[0] if np.std(dof_vals) > 0 else 0,
            'is_hub': pearsonr(dof_vals, is_hub)[0] if np.std(dof_vals) > 0 else 0,
        }
    
    return {
        'valid': True,
        'n_defects': n,
        'correlations': correlations,
        'mean_degree': np.mean(degrees),
        'mean_clustering': np.mean(clusterings),
        'n_hubs': sum(is_hub),
    }


def run_dof_enumeration():
    """
    Main Gate 4 test: Enumerate which DoFs carry organizational behavior.
    """
    print("=" * 70)
    print("PHASE 7, GATE 4: DEGREES OF FREEDOM ENUMERATION")
    print("=" * 70)
    print()
    print("Question: Which degrees of freedom carry the richer organizational behavior?")
    print()
    
    # Candidate DoFs
    print("Candidate Degrees of Freedom:")
    print("  A. Geometric: radial_dist (position from center)")
    print("  B. Coupling: coupling_value, coupling_gradient")
    print("  C. Topological: topology_strength")
    print("  D. Resonance: channel_assignment")
    print("  E. Memory: remnant_strength")
    print()
    
    # Run simulation
    print("-" * 70)
    print("RUNNING SIMULATION")
    print("-" * 70)
    print()
    
    sim = DoFEnumerationSimulator(size=48)
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Inject vortices
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    print("Equilibrating (800 steps)...", end=" ", flush=True)
    for step in range(800):
        sim.step()
        if step % 200 == 0:
            defects = sim.detect_defects_with_properties()
            print(f"{len(defects)}", end=" ", flush=True)
    print()
    
    # Collect measurements over time
    print("Measuring DoF correlations (600 steps)...", end=" ", flush=True)
    all_correlations = []
    
    for step in range(600):
        sim.step()
        if step % 60 == 0:
            defects = sim.detect_defects_with_properties()
            if len(defects) >= 15:
                adj = build_adjacency(defects, sim.size)
                analysis = analyze_dof_correlations(defects, adj)
                if analysis['valid']:
                    all_correlations.append(analysis)
                    print(".", end="", flush=True)
    print()
    
    if not all_correlations:
        print("INSUFFICIENT DATA")
        return
    
    # Aggregate correlations
    print()
    print("-" * 70)
    print("DOF-ORGANIZATION CORRELATIONS")
    print("-" * 70)
    print()
    
    dof_names = ['radial_dist', 'coupling_value', 'coupling_gradient',
                 'topology_strength', 'channel_assignment', 'remnant_strength']
    
    aggregated = {}
    for dof in dof_names:
        degree_corrs = [a['correlations'][dof]['degree'] for a in all_correlations]
        clustering_corrs = [a['correlations'][dof]['clustering'] for a in all_correlations]
        hub_corrs = [a['correlations'][dof]['is_hub'] for a in all_correlations]
        
        aggregated[dof] = {
            'degree': (np.mean(degree_corrs), np.std(degree_corrs)),
            'clustering': (np.mean(clustering_corrs), np.std(clustering_corrs)),
            'is_hub': (np.mean(hub_corrs), np.std(hub_corrs)),
        }
    
    # Display correlation table
    print(f"{'DoF':<22} {'→ Degree':>12} {'→ Clustering':>14} {'→ Hub':>10}")
    print("-" * 60)
    
    for dof in dof_names:
        d_mean, d_std = aggregated[dof]['degree']
        c_mean, c_std = aggregated[dof]['clustering']
        h_mean, h_std = aggregated[dof]['is_hub']
        
        # Flag strong correlations
        d_flag = "**" if abs(d_mean) > 0.3 else ""
        c_flag = "**" if abs(c_mean) > 0.3 else ""
        h_flag = "**" if abs(h_mean) > 0.3 else ""
        
        print(f"{dof:<22} {d_mean:>+6.3f}{d_flag:<4} {c_mean:>+6.3f}{c_flag:<6} {h_mean:>+6.3f}{h_flag}")
    
    print()
    print("(**) indicates strong correlation (|r| > 0.3)")
    
    # Identify dominant DoFs
    print()
    print("-" * 70)
    print("ANALYSIS: WHICH DOF CARRIES ORGANIZATION?")
    print("-" * 70)
    print()
    
    # Score each DoF by total explanatory power
    dof_scores = {}
    for dof in dof_names:
        total_abs_corr = (
            abs(aggregated[dof]['degree'][0]) +
            abs(aggregated[dof]['clustering'][0]) +
            abs(aggregated[dof]['is_hub'][0])
        )
        dof_scores[dof] = total_abs_corr
    
    # Rank by explanatory power
    ranked = sorted(dof_scores.items(), key=lambda x: x[1], reverse=True)
    
    print("DoF Ranking by Total Explanatory Power:")
    for i, (dof, score) in enumerate(ranked, 1):
        category = ""
        if dof == 'radial_dist':
            category = "(Geometric)"
        elif dof in ['coupling_value', 'coupling_gradient']:
            category = "(Coupling)"
        elif dof == 'topology_strength':
            category = "(Topological)"
        elif dof == 'channel_assignment':
            category = "(Resonance)"
        elif dof == 'remnant_strength':
            category = "(Memory)"
        
        print(f"  {i}. {dof:<22} score={score:.3f}  {category}")
    
    # Categorize the dominant DoFs
    print()
    top_dof = ranked[0][0]
    second_dof = ranked[1][0] if len(ranked) > 1 else None
    
    # Determine category
    geometric_dofs = ['radial_dist']
    coupling_dofs = ['coupling_value', 'coupling_gradient']
    topological_dofs = ['topology_strength']
    resonance_dofs = ['channel_assignment']
    memory_dofs = ['remnant_strength']
    
    def get_category(dof):
        if dof in geometric_dofs:
            return 'geometric'
        elif dof in coupling_dofs:
            return 'coupling'
        elif dof in topological_dofs:
            return 'topological'
        elif dof in resonance_dofs:
            return 'resonance'
        elif dof in memory_dofs:
            return 'memory'
        return 'unknown'
    
    top_category = get_category(top_dof)
    second_category = get_category(second_dof) if second_dof else None
    
    print(f"Dominant DoF: {top_dof} ({top_category})")
    if second_dof:
        print(f"Second DoF: {second_dof} ({second_category})")
    
    # Determine organization type
    print()
    print("-" * 70)
    print("ORGANIZATION TYPE ASSESSMENT")
    print("-" * 70)
    print()
    
    if top_category == 'geometric':
        print("FINDING: Organization is MOSTLY GEOMETRIC")
        print("  Position/location is the primary predictor of connectivity")
    elif top_category == 'coupling':
        print("FINDING: Organization is MOSTLY COUPLING-DRIVEN")
        print("  The κ-landscape is the primary predictor of connectivity")
    elif top_category == 'topological':
        print("FINDING: Organization is MOSTLY TOPOLOGICAL")
        print("  Winding/vorticity strength predicts connectivity")
    elif top_category == 'resonance':
        print("FINDING: Organization is MOSTLY RESONANCE-DRIVEN")
        print("  Channel assignment state predicts connectivity")
    elif top_category == 'memory':
        print("FINDING: Organization is MOSTLY MEMORY-DRIVEN")
        print("  Remnant field strength predicts connectivity")
    
    # Check for hybrid
    if second_dof and dof_scores[second_dof] > 0.8 * dof_scores[top_dof]:
        print()
        print(f"HYBRID SIGNAL: {second_dof} ({second_category}) is almost as strong")
        print(f"  Organization may be genuinely HYBRID ({top_category} + {second_category})")
    
    # Gate assessment
    print()
    print("=" * 70)
    print("GATE 4 ASSESSMENT")
    print("=" * 70)
    print()
    
    print("FINDING: Degrees of Freedom Hierarchy Established")
    print()
    print("Organizational complexity in the proto-spacetime regime is carried by:")
    for i, (dof, score) in enumerate(ranked[:3], 1):
        print(f"  {i}. {dof} (score={score:.3f})")
    
    print()
    if top_category in ['topological', 'resonance', 'memory']:
        print("KEY RESULT: Non-spatial DoFs dominate organization")
        print("  The filamentary spatial scaffold is NOT the primary carrier of complexity")
        print("  Internal medium states (topology/resonance/memory) carry the richer behavior")
    elif top_category == 'coupling':
        print("KEY RESULT: Coupling landscape dominates organization")
        print("  The κ-field shapes connectivity more than pure position")
        print("  This is a field-mediated organizational mode")
    else:
        print("KEY RESULT: Geometric/spatial DoFs dominate organization")
        print("  Position remains the primary predictor")
        print("  This may indicate the spatial scaffold is more important than expected")
    
    return aggregated


if __name__ == "__main__":
    results = run_dof_enumeration()
