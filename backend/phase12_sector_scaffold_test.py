"""
Phase 12b: Sector-Scaffold Correlation Test
=============================================

QUESTION: Do + and - sectors contribute differently to scaffold organization?

WHY THIS MATTERS:
- Phase 12a showed balance is dynamically maintained
- But are the sectors ORGANIZATIONALLY SYMMETRIC?
- Or does one sector dominate loop formation, clustering, etc.?

IF NO DIFFERENCE:
- Sectors are symmetric in both number AND organizational role
- The dual-sector structure is fully balanced
- This strengthens the topological dual-sector interpretation

IF DIFFERENCE:
- One sector may be more "active" organizationally
- Balance would be numerical but not functional
- Would change the interpretation of dual-sector emergence

METRICS TO COMPARE:

1. LOOP CONTRIBUTION
   - Do + defects form more/fewer loops than - defects?
   - Cycle rank contribution by sector

2. CLUSTERING CONTRIBUTION  
   - Do + defects have higher/lower clustering?
   - Local triangle formation by sector

3. HUB STRUCTURE
   - Are high-degree "hub" nodes more likely to be + or -?
   - Degree distribution by sector

4. INTER-SECTOR VS INTRA-SECTOR CONNECTIVITY
   - Are +→+ and -→- edges different from +→- edges?
   - Cross-sector connectivity patterns
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import ttest_ind, mannwhitneyu
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class SectorScaffoldSimulator:
    """Simulator for sector-scaffold correlation analysis."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 4
        
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
    
    def inject_vortex(self, cx: int, cy: int, chirality: int = 1):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_balanced_vortices(self):
        center = self.size // 2
        for chirality in [+1, +1, -1, -1]:
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy, chirality)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        if self.step_count % self.injection_interval == 0:
            self.inject_balanced_vortices()
        
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
    
    def detect_signed_defects_with_positions(self, threshold: float = 0.4) -> List[Tuple]:
        """Detect defects with position and sign."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        defects = []
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                cz = int(np.mean(coords[2]))
                
                local_vort = vorticity[cx, cy, cz]
                
                if local_vort > 0.05:
                    defects.append(((cx, cy, cz), +1))
                elif local_vort < -0.05:
                    defects.append(((cx, cy, cz), -1))
        
        return defects


def euclidean_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_sector_scaffold_metrics(defects, size) -> Dict:
    """
    Measure organizational metrics separately for + and - sectors.
    
    Compare: degree, clustering, hub-ness by sector.
    Also measure: edge types (++, --, +-).
    """
    n = len(defects)
    
    if n < 20:
        return {'valid': False, 'n': n}
    
    # Separate by sign
    pos_indices = [i for i, (_, sign) in enumerate(defects) if sign == +1]
    neg_indices = [i for i, (_, sign) in enumerate(defects) if sign == -1]
    
    n_pos = len(pos_indices)
    n_neg = len(neg_indices)
    
    if n_pos < 5 or n_neg < 5:
        return {'valid': False, 'n': n, 'n_pos': n_pos, 'n_neg': n_neg}
    
    # Build adjacency with sign information
    adj = defaultdict(set)
    edge_types = {'++': 0, '--': 0, '+-': 0}
    
    for i in range(n):
        pos_i, sign_i = defects[i]
        for j in range(i + 1, n):
            pos_j, sign_j = defects[j]
            d = euclidean_periodic(pos_i, pos_j, size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
                
                # Count edge type
                if sign_i == sign_j == +1:
                    edge_types['++'] += 1
                elif sign_i == sign_j == -1:
                    edge_types['--'] += 1
                else:
                    edge_types['+-'] += 1
    
    # Compute per-node metrics
    pos_degrees = [len(adj[i]) for i in pos_indices]
    neg_degrees = [len(adj[i]) for i in neg_indices]
    
    # Clustering by sector
    def node_clustering(node):
        k = len(adj[node])
        if k < 2:
            return 0
        neighbors = list(adj[node])
        edges_between = sum(1 for i in range(len(neighbors)) 
                           for j in range(i+1, len(neighbors)) 
                           if neighbors[j] in adj[neighbors[i]])
        return edges_between / (k * (k - 1) / 2)
    
    pos_clustering = [node_clustering(i) for i in pos_indices]
    neg_clustering = [node_clustering(i) for i in neg_indices]
    
    # Hub analysis: nodes with degree > median
    all_degrees = [len(adj[i]) for i in range(n)]
    median_degree = np.median(all_degrees)
    
    pos_hubs = sum(1 for i in pos_indices if len(adj[i]) > median_degree)
    neg_hubs = sum(1 for i in neg_indices if len(adj[i]) > median_degree)
    
    pos_hub_fraction = pos_hubs / n_pos if n_pos > 0 else 0
    neg_hub_fraction = neg_hubs / n_neg if n_neg > 0 else 0
    
    # Expected edge counts if random
    total_edges = sum(edge_types.values())
    p_pos = n_pos / n
    p_neg = n_neg / n
    
    expected_pp = total_edges * p_pos * p_pos / (p_pos * p_pos + p_neg * p_neg + 2 * p_pos * p_neg)
    expected_nn = total_edges * p_neg * p_neg / (p_pos * p_pos + p_neg * p_neg + 2 * p_pos * p_neg)
    expected_pn = total_edges * 2 * p_pos * p_neg / (p_pos * p_pos + p_neg * p_neg + 2 * p_pos * p_neg)
    
    return {
        'valid': True,
        'n': n,
        'n_pos': n_pos,
        'n_neg': n_neg,
        # Degree metrics
        'pos_mean_degree': float(np.mean(pos_degrees)),
        'neg_mean_degree': float(np.mean(neg_degrees)),
        'degree_diff': float(np.mean(pos_degrees) - np.mean(neg_degrees)),
        # Clustering metrics
        'pos_mean_clustering': float(np.mean(pos_clustering)),
        'neg_mean_clustering': float(np.mean(neg_clustering)),
        'clustering_diff': float(np.mean(pos_clustering) - np.mean(neg_clustering)),
        # Hub metrics
        'pos_hub_fraction': float(pos_hub_fraction),
        'neg_hub_fraction': float(neg_hub_fraction),
        'hub_diff': float(pos_hub_fraction - neg_hub_fraction),
        # Edge types
        'edges_pp': edge_types['++'],
        'edges_nn': edge_types['--'],
        'edges_pn': edge_types['+-'],
        'edges_pp_expected': float(expected_pp),
        'edges_nn_expected': float(expected_nn),
        'edges_pn_expected': float(expected_pn),
    }


def run_sector_scaffold_test():
    """
    Test whether + and - sectors contribute differently to scaffold organization.
    """
    print("=" * 75)
    print("  PHASE 12b: SECTOR-SCAFFOLD CORRELATION TEST")
    print("=" * 75)
    print()
    print("Question: Do + and - sectors contribute differently to scaffold?")
    print()
    print("Comparing: Degree, Clustering, Hub fraction by sector")
    print()
    
    sim = SectorScaffoldSimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Balanced initial seeding
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                chirality = 1 if (i + j) % 2 == 0 else -1
                sim.inject_vortex(center + i * 4, center + j * 4, chirality)
    
    print(f"{'Step':>5} │ {'N+':>3} {'N-':>3} │ {'Deg+':>5} {'Deg-':>5} │ "
          f"{'Clust+':>6} {'Clust-':>6} │ {'Hub+':>5} {'Hub-':>5}")
    print("-" * 75)
    
    history = []
    
    for step in range(2000):
        sim.step()
        
        if step % 100 == 0 and step > 0:
            defects = sim.detect_signed_defects_with_positions()
            m = measure_sector_scaffold_metrics(defects, sim.size)
            
            if m['valid']:
                print(f"{step:>5} │ {m['n_pos']:>3} {m['n_neg']:>3} │ "
                      f"{m['pos_mean_degree']:>5.2f} {m['neg_mean_degree']:>5.2f} │ "
                      f"{m['pos_mean_clustering']:>6.3f} {m['neg_mean_clustering']:>6.3f} │ "
                      f"{m['pos_hub_fraction']:>5.2f} {m['neg_hub_fraction']:>5.2f}")
                
                m['step'] = step
                history.append(m)
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("SECTOR ORGANIZATIONAL SYMMETRY ANALYSIS")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n'] > 50]
    
    if len(valid) >= 10:
        # Aggregate differences
        degree_diffs = [h['degree_diff'] for h in valid]
        clustering_diffs = [h['clustering_diff'] for h in valid]
        hub_diffs = [h['hub_diff'] for h in valid]
        
        print("1. DEGREE COMPARISON")
        print("-" * 40)
        avg_pos_deg = np.mean([h['pos_mean_degree'] for h in valid])
        avg_neg_deg = np.mean([h['neg_mean_degree'] for h in valid])
        avg_deg_diff = np.mean(degree_diffs)
        std_deg_diff = np.std(degree_diffs)
        
        print(f"  + sector avg degree: {avg_pos_deg:.3f}")
        print(f"  - sector avg degree: {avg_neg_deg:.3f}")
        print(f"  Difference: {avg_deg_diff:+.3f} ± {std_deg_diff:.3f}")
        
        # t-test
        _, p_deg = ttest_ind([h['pos_mean_degree'] for h in valid],
                            [h['neg_mean_degree'] for h in valid])
        print(f"  t-test p-value: {p_deg:.4f}")
        
        if p_deg < 0.05:
            print(f"  → SIGNIFICANT DIFFERENCE in degree")
            deg_verdict = "different"
        else:
            print(f"  → No significant difference in degree")
            deg_verdict = "symmetric"
        
        print()
        
        print("2. CLUSTERING COMPARISON")
        print("-" * 40)
        avg_pos_clust = np.mean([h['pos_mean_clustering'] for h in valid])
        avg_neg_clust = np.mean([h['neg_mean_clustering'] for h in valid])
        avg_clust_diff = np.mean(clustering_diffs)
        std_clust_diff = np.std(clustering_diffs)
        
        print(f"  + sector avg clustering: {avg_pos_clust:.3f}")
        print(f"  - sector avg clustering: {avg_neg_clust:.3f}")
        print(f"  Difference: {avg_clust_diff:+.3f} ± {std_clust_diff:.3f}")
        
        _, p_clust = ttest_ind([h['pos_mean_clustering'] for h in valid],
                              [h['neg_mean_clustering'] for h in valid])
        print(f"  t-test p-value: {p_clust:.4f}")
        
        if p_clust < 0.05:
            print(f"  → SIGNIFICANT DIFFERENCE in clustering")
            clust_verdict = "different"
        else:
            print(f"  → No significant difference in clustering")
            clust_verdict = "symmetric"
        
        print()
        
        print("3. HUB STRUCTURE COMPARISON")
        print("-" * 40)
        avg_pos_hub = np.mean([h['pos_hub_fraction'] for h in valid])
        avg_neg_hub = np.mean([h['neg_hub_fraction'] for h in valid])
        avg_hub_diff = np.mean(hub_diffs)
        std_hub_diff = np.std(hub_diffs)
        
        print(f"  + sector hub fraction: {avg_pos_hub:.3f}")
        print(f"  - sector hub fraction: {avg_neg_hub:.3f}")
        print(f"  Difference: {avg_hub_diff:+.3f} ± {std_hub_diff:.3f}")
        
        _, p_hub = ttest_ind([h['pos_hub_fraction'] for h in valid],
                            [h['neg_hub_fraction'] for h in valid])
        print(f"  t-test p-value: {p_hub:.4f}")
        
        if p_hub < 0.05:
            print(f"  → SIGNIFICANT DIFFERENCE in hub structure")
            hub_verdict = "different"
        else:
            print(f"  → No significant difference in hub structure")
            hub_verdict = "symmetric"
        
        print()
        
        print("4. EDGE TYPE ANALYSIS")
        print("-" * 40)
        total_pp = sum(h['edges_pp'] for h in valid)
        total_nn = sum(h['edges_nn'] for h in valid)
        total_pn = sum(h['edges_pn'] for h in valid)
        total_edges = total_pp + total_nn + total_pn
        
        exp_pp = sum(h['edges_pp_expected'] for h in valid)
        exp_nn = sum(h['edges_nn_expected'] for h in valid)
        exp_pn = sum(h['edges_pn_expected'] for h in valid)
        
        print(f"  ++ edges: {total_pp} (expected {exp_pp:.0f})")
        print(f"  -- edges: {total_nn} (expected {exp_nn:.0f})")
        print(f"  +- edges: {total_pn} (expected {exp_pn:.0f})")
        
        # Ratio of observed to expected
        if exp_pp > 0:
            pp_ratio = total_pp / exp_pp
            nn_ratio = total_nn / exp_nn
            pn_ratio = total_pn / exp_pn
            print(f"  ++ ratio: {pp_ratio:.3f} (1.0 = random)")
            print(f"  -- ratio: {nn_ratio:.3f}")
            print(f"  +- ratio: {pn_ratio:.3f}")
        
        print()
        print("=" * 75)
        print("CONCLUSION")
        print("=" * 75)
        print()
        
        n_different = sum([deg_verdict == "different",
                          clust_verdict == "different", 
                          hub_verdict == "different"])
        
        if n_different == 0:
            print("SECTORS ARE ORGANIZATIONALLY SYMMETRIC")
            print()
            print("Both + and - sectors contribute equally to:")
            print("  - Connectivity (degree)")
            print("  - Local structure (clustering)")
            print("  - Hub formation")
            print()
            print("The dual-sector balance is COMPLETE:")
            print("  - Numerically balanced (Phase 11f, 12a)")
            print("  - Organizationally symmetric (Phase 12b)")
            conclusion = "symmetric"
        elif n_different == 3:
            print("SECTORS SHOW ORGANIZATIONAL ASYMMETRY")
            print()
            print("Significant differences found in all metrics.")
            print("One sector may be more 'active' organizationally.")
            conclusion = "asymmetric"
        else:
            print("PARTIAL ORGANIZATIONAL SYMMETRY")
            print()
            print(f"Differences found in {n_different}/3 metrics.")
            print("Sectors are mostly symmetric but not perfectly.")
            conclusion = "partial"
    else:
        conclusion = "insufficient_data"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase12_sector_scaffold_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'sector_scaffold_correlation',
            'question': 'Do + and - sectors contribute differently to scaffold?',
            'history': history,
            'deg_verdict': deg_verdict if 'deg_verdict' in dir() else 'unknown',
            'clust_verdict': clust_verdict if 'clust_verdict' in dir() else 'unknown',
            'hub_verdict': hub_verdict if 'hub_verdict' in dir() else 'unknown',
            'conclusion': conclusion,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, conclusion


if __name__ == "__main__":
    history, conclusion = run_sector_scaffold_test()
