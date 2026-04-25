"""
Phase 11f: Signed Branch Expansion Test
========================================

CONCEPTUAL REFRAMING:

Previous tests treated expansion as unsigned — just "how much organization."
But if the medium is fundamentally balanced, expansion may involve:
  - PAIRED complementary branch expansions
  - Positive and negative sectors developing in dual ways
  - Global balance preserved while local asymmetry develops

KEY QUESTION:
Do positive and negative chirality defects develop different organizational
structures? Is expansion actually DUAL-BRANCH expansion?

WHAT WE CAN MEASURE:

1. Defect Chirality
   - The phase field has winding structure
   - Vortices can have positive or negative winding (chirality)
   - We can separate populations by sign

2. Signed Branch Development
   - Do + and - populations develop loops at different rates?
   - Do they cluster differently?
   - Do they occupy different spatial regions?

3. Global Balance
   - Is the total signed population near zero?
   - Does imbalance correlate with organizational asymmetry?

HYPOTHESIS:
"Expansion is dual-branch: positive and negative sectors co-emerge
and co-expand, with complementary organizational development."
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class SignedExpansionSimulator:
    """Simulator with chirality tracking for signed branch analysis."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 3
        
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
        """Inject vortex with specified chirality (+1 or -1)."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        # Chirality determines winding direction
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_balanced_vortices(self):
        """Inject equal numbers of + and - chirality vortices."""
        center = self.size // 2
        # Half positive, half negative to maintain balance
        for i, chirality in enumerate([+1, +1, -1, -1][:self.injection_count]):
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
    
    def detect_signed_defects(self, threshold: float = 0.4) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Detect defects and separate by chirality (sign of local vorticity).
        
        Returns: (positive_defects, negative_defects)
        """
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        # Compute local vorticity (curl of phase gradient)
        # In 2D slice: vorticity = d(phase)/dx crossed with d(phase)/dy
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        
        # Curl in z-direction (for each z-slice)
        # vorticity = dgrad_y/dx - dgrad_x/dy
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        positive_defects = []
        negative_defects = []
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                cz = int(np.mean(coords[2]))
                
                # Determine chirality from local vorticity
                local_vort = vorticity[cx, cy, cz]
                
                if local_vort > 0.05:
                    positive_defects.append((cx, cy, cz))
                elif local_vort < -0.05:
                    negative_defects.append((cx, cy, cz))
                # Near-zero vorticity defects are ambiguous, skip them
        
        return positive_defects, negative_defects


def euclidean_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_sector_metrics(defects, size) -> Dict:
    """Measure organizational metrics for a single sector (+ or -)."""
    n = len(defects)
    
    if n < 8:
        return {'valid': False, 'n': n}
    
    max_n = min(n, 60)
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
            d = euclidean_periodic(sample[i], sample[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    degrees = [len(adj[i]) for i in range(max_n)]
    mean_degree = np.mean(degrees) if degrees else 0
    
    # Components
    visited = set()
    n_components = 0
    for start in range(max_n):
        if start not in visited:
            n_components += 1
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    for neighbor in adj[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)
    
    # Cycle rank (loops)
    cycle_rank = edges - max_n + n_components
    cycles_per_node = cycle_rank / max_n if max_n > 0 else 0
    
    # Clustering
    clustering_coeffs = []
    for node in range(max_n):
        k = len(adj[node])
        if k >= 2:
            neighbors = list(adj[node])
            edges_between = 0
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    if neighbors[j] in adj[neighbors[i]]:
                        edges_between += 1
            max_edges = k * (k - 1) / 2
            clustering_coeffs.append(edges_between / max_edges)
    
    mean_clustering = np.mean(clustering_coeffs) if clustering_coeffs else 0
    
    loop_vs_clust = cycles_per_node - mean_clustering
    
    # Spatial centroid
    if sample:
        centroid = np.mean(sample, axis=0)
    else:
        centroid = [0, 0, 0]
    
    return {
        'valid': True,
        'n': n,
        'mean_degree': mean_degree,
        'cycles_per_node': cycles_per_node,
        'mean_clustering': mean_clustering,
        'loop_vs_clust': loop_vs_clust,
        'centroid': list(centroid),
    }


def run_signed_expansion_test():
    """
    Test whether positive and negative chirality sectors develop differently.
    
    KEY QUESTION: Is expansion dual-branch?
    """
    print("=" * 75)
    print("  PHASE 11f: SIGNED BRANCH EXPANSION TEST")
    print("=" * 75)
    print()
    print("Hypothesis: Expansion is dual-branch — positive and negative sectors")
    print("            co-emerge with complementary organizational development.")
    print()
    
    sim = SignedExpansionSimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Balanced initial seeding
    center = 24
    for i, chirality in zip(range(-3, 4), [+1, -1, +1, -1, +1, -1, +1]):
        for j, chirality2 in zip(range(-3, 4), [+1, -1, +1, -1, +1, -1, +1]):
            if abs(i) + abs(j) <= 3:
                c = chirality * chirality2  # Alternating pattern
                sim.inject_vortex(center + i * 4, center + j * 4, c)
    
    print(f"{'Step':>5} │ {'N+':>4} {'N-':>4} {'Bal':>5} │ "
          f"{'L-C+':>6} {'L-C-':>6} {'Diff':>6} │ {'Verdict':>10}")
    print("-" * 70)
    
    history = []
    
    for step in range(1200):
        sim.step()
        
        if step % 50 == 0:
            pos_defects, neg_defects = sim.detect_signed_defects()
            
            n_pos = len(pos_defects)
            n_neg = len(neg_defects)
            n_total = n_pos + n_neg
            
            # Balance: how close to 50/50?
            if n_total > 0:
                balance = 1 - abs(n_pos - n_neg) / n_total
            else:
                balance = 0
            
            # Measure each sector
            pos_metrics = measure_sector_metrics(pos_defects, sim.size)
            neg_metrics = measure_sector_metrics(neg_defects, sim.size)
            
            lc_pos = pos_metrics['loop_vs_clust'] if pos_metrics['valid'] else 0
            lc_neg = neg_metrics['loop_vs_clust'] if neg_metrics['valid'] else 0
            lc_diff = lc_pos - lc_neg
            
            # Verdict
            if abs(lc_diff) < 0.1:
                verdict = "Symmetric"
            elif lc_diff > 0.1:
                verdict = "+ Loop-dom"
            else:
                verdict = "- Loop-dom"
            
            print(f"{step:>5} │ {n_pos:>4} {n_neg:>4} {balance:>5.2f} │ "
                  f"{lc_pos:>+6.3f} {lc_neg:>+6.3f} {lc_diff:>+6.3f} │ {verdict:>10}")
            
            m = {
                'step': step,
                'n_pos': n_pos,
                'n_neg': n_neg,
                'n_total': n_total,
                'balance': balance,
                'lc_pos': lc_pos,
                'lc_neg': lc_neg,
                'lc_diff': lc_diff,
                'pos_metrics': pos_metrics,
                'neg_metrics': neg_metrics,
            }
            history.append(m)
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("DUAL-BRANCH ANALYSIS")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n_total'] > 30]
    
    if len(valid) >= 5:
        # Global balance
        avg_balance = np.mean([h['balance'] for h in valid])
        print(f"Average population balance: {avg_balance:.3f}")
        print(f"  (1.0 = perfect 50/50, 0.0 = all one sign)")
        print()
        
        # L-C correlation between sectors
        lc_pos_vals = [h['lc_pos'] for h in valid if h['pos_metrics']['valid']]
        lc_neg_vals = [h['lc_neg'] for h in valid if h['neg_metrics']['valid']]
        
        if len(lc_pos_vals) >= 5 and len(lc_neg_vals) >= 5:
            min_len = min(len(lc_pos_vals), len(lc_neg_vals))
            r_sectors, p_sectors = pearsonr(lc_pos_vals[:min_len], lc_neg_vals[:min_len])
            print(f"Correlation between + and - sector L-C: r = {r_sectors:+.3f}")
            print()
            
            if r_sectors > 0.5:
                print("FINDING: Sectors develop IN SYNC (correlated)")
                print("         Both follow same Loop→Clustering trajectory")
                sync_type = "synchronized"
            elif r_sectors < -0.3:
                print("FINDING: Sectors develop ANTI-CORRELATED")
                print("         When + goes Loop, - goes Clustering and vice versa")
                print("         → DUAL-BRANCH expansion confirmed!")
                sync_type = "anti-correlated"
            else:
                print("FINDING: Sectors develop INDEPENDENTLY")
                print("         No strong correlation between branches")
                sync_type = "independent"
        else:
            sync_type = "insufficient_data"
        
        print()
        
        # Asymmetry development
        print("Asymmetry over time:")
        early = [h for h in valid if h['step'] < 400]
        late = [h for h in valid if h['step'] > 800]
        
        if early and late:
            early_diff = np.mean([abs(h['lc_diff']) for h in early])
            late_diff = np.mean([abs(h['lc_diff']) for h in late])
            
            print(f"  Early |L-C difference|: {early_diff:.3f}")
            print(f"  Late  |L-C difference|: {late_diff:.3f}")
            
            if late_diff > early_diff * 1.3:
                print("  → Asymmetry GROWS over time")
                asymmetry_trend = "growing"
            elif late_diff < early_diff * 0.7:
                print("  → Asymmetry DECREASES over time")
                asymmetry_trend = "decreasing"
            else:
                print("  → Asymmetry roughly STABLE")
                asymmetry_trend = "stable"
        else:
            asymmetry_trend = "insufficient_data"
        
        print()
        print("=" * 75)
        print("CONCLUSION")
        print("=" * 75)
        print()
        
        if sync_type == "anti-correlated":
            print("DUAL-BRANCH EXPANSION CONFIRMED")
            print()
            print("Positive and negative chirality sectors develop in complementary ways.")
            print("When one sector favors loops, the other favors clustering.")
            print("This is consistent with balanced paired expansion.")
        elif sync_type == "synchronized":
            print("SINGLE-BRANCH EXPANSION (Synchronized)")
            print()
            print("Both sectors follow the same organizational trajectory.")
            print("Chirality does not determine branch development.")
        else:
            print("INCONCLUSIVE")
            print()
            print("No clear dual-branch or single-branch pattern detected.")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_signed_expansion_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'signed_branch_expansion',
            'hypothesis': 'Expansion is dual-branch with complementary +/- sectors',
            'history': [
                {k: v for k, v in h.items() if k not in ['pos_metrics', 'neg_metrics']}
                for h in history
            ],
            'sync_type': sync_type if 'sync_type' in dir() else 'unknown',
            'asymmetry_trend': asymmetry_trend if 'asymmetry_trend' in dir() else 'unknown',
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history


if __name__ == "__main__":
    history = run_signed_expansion_test()
