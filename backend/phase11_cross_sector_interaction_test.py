"""
Phase 11g: Cross-Sector Interaction Test
==========================================

DECISIVE QUESTION:
Do opposite-sign defects interact differently from same-sign defects?

If YES → Balance is enforced by a relational/interaction law
If NO  → Balance is purely statistical

WHAT TO MEASURE:

1. SPATIAL RELATIONSHIPS
   - Average distance: ++ pairs vs +- pairs vs -- pairs
   - Do opposite signs attract? Same signs repel?

2. CONNECTIVITY PATTERNS
   - Are +- edges more/less common than expected by chance?
   - Do same-sign defects form separate clusters?

3. ANNIHILATION PROXIMITY
   - When populations drop, are +- pairs closer (suggesting annihilation)?
   - Do same-sign pairs survive longer when distant?

4. LOCAL NEIGHBORHOOD
   - For a given + defect, is its neighborhood enriched in + or -?
   - Is there sign segregation or mixing?

PREDICTION (Strong Balance Hypothesis):
Opposite-sign defects should attract (shorter +- distances) and
same-sign defects should avoid each other (longer ++ and -- distances).
This would enforce balance through a relational mechanism.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr, ttest_ind
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class InteractionTestSimulator:
    """Simulator for cross-sector interaction analysis."""
    
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
        for i, chirality in enumerate([+1, +1, -1, -1]):
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
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        
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
                
                local_vort = vorticity[cx, cy, cz]
                
                if local_vort > 0.05:
                    positive_defects.append((cx, cy, cz))
                elif local_vort < -0.05:
                    negative_defects.append((cx, cy, cz))
        
        return positive_defects, negative_defects


def euclidean_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_cross_sector_interactions(pos_defects, neg_defects, size) -> Dict:
    """
    Measure interaction patterns between and within signed sectors.
    
    KEY METRICS:
    1. Distance statistics: ++ vs +- vs --
    2. Nearest-neighbor sign: Is NN more likely same or opposite?
    3. Mixing index: How intermixed are the populations?
    """
    n_pos = len(pos_defects)
    n_neg = len(neg_defects)
    n_total = n_pos + n_neg
    
    if n_total < 10 or n_pos < 3 or n_neg < 3:
        return {'valid': False, 'n_total': n_total, 'n_pos': n_pos, 'n_neg': n_neg}
    
    # Compute all pairwise distances by pair type
    pp_distances = []  # ++ pairs
    nn_distances = []  # -- pairs
    pn_distances = []  # +- pairs
    
    # ++ pairs
    for i in range(n_pos):
        for j in range(i + 1, n_pos):
            d = euclidean_periodic(pos_defects[i], pos_defects[j], size)
            pp_distances.append(d)
    
    # -- pairs
    for i in range(n_neg):
        for j in range(i + 1, n_neg):
            d = euclidean_periodic(neg_defects[i], neg_defects[j], size)
            nn_distances.append(d)
    
    # +- pairs
    for i in range(n_pos):
        for j in range(n_neg):
            d = euclidean_periodic(pos_defects[i], neg_defects[j], size)
            pn_distances.append(d)
    
    # Distance statistics
    avg_pp = np.mean(pp_distances) if pp_distances else 0
    avg_nn = np.mean(nn_distances) if nn_distances else 0
    avg_pn = np.mean(pn_distances) if pn_distances else 0
    avg_same = np.mean(pp_distances + nn_distances) if (pp_distances or nn_distances) else 0
    
    # NEAREST NEIGHBOR ANALYSIS
    # For each defect, find its nearest neighbor and record the sign
    all_defects = [(p, +1) for p in pos_defects] + [(p, -1) for p in neg_defects]
    
    same_sign_nn = 0
    opposite_sign_nn = 0
    
    for i, (pos_i, sign_i) in enumerate(all_defects):
        min_dist = float('inf')
        nn_sign = None
        
        for j, (pos_j, sign_j) in enumerate(all_defects):
            if i != j:
                d = euclidean_periodic(pos_i, pos_j, size)
                if d < min_dist:
                    min_dist = d
                    nn_sign = sign_j
        
        if nn_sign is not None:
            if nn_sign == sign_i:
                same_sign_nn += 1
            else:
                opposite_sign_nn += 1
    
    # NN sign ratio
    if same_sign_nn + opposite_sign_nn > 0:
        nn_same_ratio = same_sign_nn / (same_sign_nn + opposite_sign_nn)
    else:
        nn_same_ratio = 0.5
    
    # Expected ratio if random: depends on population fractions
    p_same_random = (n_pos * (n_pos - 1) + n_neg * (n_neg - 1)) / (n_total * (n_total - 1))
    
    # MIXING INDEX
    # How intermixed are the populations spatially?
    # Compute: for each defect, count same-sign vs opposite-sign neighbors within radius
    radius = 12.0
    same_in_radius = 0
    opposite_in_radius = 0
    
    for i, (pos_i, sign_i) in enumerate(all_defects):
        for j, (pos_j, sign_j) in enumerate(all_defects):
            if i != j:
                d = euclidean_periodic(pos_i, pos_j, size)
                if d < radius:
                    if sign_j == sign_i:
                        same_in_radius += 1
                    else:
                        opposite_in_radius += 1
    
    if same_in_radius + opposite_in_radius > 0:
        mixing_index = opposite_in_radius / (same_in_radius + opposite_in_radius)
    else:
        mixing_index = 0.5
    
    # Expected mixing if random
    mixing_random = 2 * n_pos * n_neg / (n_total * (n_total - 1))
    
    return {
        'valid': True,
        'n_total': n_total,
        'n_pos': n_pos,
        'n_neg': n_neg,
        # Distance statistics
        'avg_pp': avg_pp,
        'avg_nn': avg_nn,
        'avg_pn': avg_pn,
        'avg_same': avg_same,
        'distance_ratio': avg_pn / avg_same if avg_same > 0 else 1.0,
        # NN analysis
        'nn_same_ratio': nn_same_ratio,
        'nn_same_expected': p_same_random,
        'nn_enrichment': nn_same_ratio / p_same_random if p_same_random > 0 else 1.0,
        # Mixing index
        'mixing_index': mixing_index,
        'mixing_expected': mixing_random,
        'mixing_enrichment': mixing_index / mixing_random if mixing_random > 0 else 1.0,
    }


def run_cross_sector_interaction_test():
    """
    Test whether opposite-sign defects interact differently from same-sign.
    
    DECISIVE QUESTION: Is balance enforced by a relational law?
    """
    print("=" * 75)
    print("  PHASE 11g: CROSS-SECTOR INTERACTION TEST")
    print("=" * 75)
    print()
    print("Decisive Question: Do +/- defects interact differently from ++/-- pairs?")
    print()
    print("Predictions for RELATIONAL BALANCE:")
    print("  - +- pairs should be CLOSER (attraction)")
    print("  - ++ and -- pairs should be FARTHER (repulsion)")
    print("  - Nearest neighbor should be more likely opposite-sign")
    print()
    
    sim = InteractionTestSimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Balanced initial seeding
    center = 24
    for i, chirality in zip(range(-3, 4), [+1, -1, +1, -1, +1, -1, +1]):
        for j, chirality2 in zip(range(-3, 4), [-1, +1, -1, +1, -1, +1, -1]):
            if abs(i) + abs(j) <= 3:
                c = chirality * chirality2
                sim.inject_vortex(center + i * 4, center + j * 4, c)
    
    print(f"{'Step':>5} │ {'N+':>3} {'N-':>3} │ {'d++':>5} {'d--':>5} {'d+-':>5} │ "
          f"{'+-/same':>7} │ {'NN same':>7} │ {'Mix':>5}")
    print("-" * 70)
    
    history = []
    
    for step in range(1200):
        sim.step()
        
        if step % 50 == 0:
            pos_defects, neg_defects = sim.detect_signed_defects()
            m = measure_cross_sector_interactions(pos_defects, neg_defects, sim.size)
            
            if m['valid']:
                print(f"{step:>5} │ {m['n_pos']:>3} {m['n_neg']:>3} │ "
                      f"{m['avg_pp']:>5.1f} {m['avg_nn']:>5.1f} {m['avg_pn']:>5.1f} │ "
                      f"{m['distance_ratio']:>7.3f} │ {m['nn_same_ratio']:>7.3f} │ "
                      f"{m['mixing_index']:>5.3f}")
                
                m['step'] = step
                history.append(m)
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("INTERACTION ANALYSIS")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n_total'] > 20]
    
    if len(valid) >= 5:
        # 1. DISTANCE ANALYSIS
        print("1. DISTANCE STATISTICS")
        print("-" * 40)
        
        avg_pp_all = np.mean([h['avg_pp'] for h in valid])
        avg_nn_all = np.mean([h['avg_nn'] for h in valid])
        avg_pn_all = np.mean([h['avg_pn'] for h in valid])
        avg_same_all = np.mean([h['avg_same'] for h in valid])
        avg_ratio = np.mean([h['distance_ratio'] for h in valid])
        
        print(f"  Average ++ distance: {avg_pp_all:.2f}")
        print(f"  Average -- distance: {avg_nn_all:.2f}")
        print(f"  Average +- distance: {avg_pn_all:.2f}")
        print(f"  Average same-sign:   {avg_same_all:.2f}")
        print()
        print(f"  Ratio (+-/same):     {avg_ratio:.3f}")
        
        if avg_ratio < 0.9:
            print(f"  → +- pairs are CLOSER than same-sign → ATTRACTION")
            distance_verdict = "attraction"
        elif avg_ratio > 1.1:
            print(f"  → +- pairs are FARTHER than same-sign → REPULSION")
            distance_verdict = "repulsion"
        else:
            print(f"  → No significant distance difference → NEUTRAL")
            distance_verdict = "neutral"
        
        print()
        
        # 2. NEAREST NEIGHBOR ANALYSIS
        print("2. NEAREST NEIGHBOR ANALYSIS")
        print("-" * 40)
        
        avg_nn_same = np.mean([h['nn_same_ratio'] for h in valid])
        avg_nn_expected = np.mean([h['nn_same_expected'] for h in valid])
        avg_nn_enrich = np.mean([h['nn_enrichment'] for h in valid])
        
        print(f"  NN same-sign fraction:    {avg_nn_same:.3f}")
        print(f"  Expected if random:       {avg_nn_expected:.3f}")
        print(f"  Enrichment factor:        {avg_nn_enrich:.3f}")
        
        if avg_nn_enrich < 0.8:
            print(f"  → NN more likely OPPOSITE sign → OPPOSITE ATTRACTION")
            nn_verdict = "opposite_attraction"
        elif avg_nn_enrich > 1.2:
            print(f"  → NN more likely SAME sign → SAME-SIGN CLUSTERING")
            nn_verdict = "same_clustering"
        else:
            print(f"  → NN sign is near random → NO PREFERENCE")
            nn_verdict = "neutral"
        
        print()
        
        # 3. MIXING ANALYSIS
        print("3. SPATIAL MIXING ANALYSIS")
        print("-" * 40)
        
        avg_mixing = np.mean([h['mixing_index'] for h in valid])
        avg_mixing_expected = np.mean([h['mixing_expected'] for h in valid])
        avg_mixing_enrich = np.mean([h['mixing_enrichment'] for h in valid])
        
        print(f"  Mixing index:             {avg_mixing:.3f}")
        print(f"  Expected if random:       {avg_mixing_expected:.3f}")
        print(f"  Enrichment factor:        {avg_mixing_enrich:.3f}")
        
        if avg_mixing_enrich > 1.2:
            print(f"  → MORE mixing than random → POPULATIONS INTERLEAVE")
            mixing_verdict = "interleaved"
        elif avg_mixing_enrich < 0.8:
            print(f"  → LESS mixing than random → POPULATIONS SEGREGATE")
            mixing_verdict = "segregated"
        else:
            print(f"  → Mixing near random → NO SPATIAL PREFERENCE")
            mixing_verdict = "neutral"
        
        print()
        print("=" * 75)
        print("CONCLUSION: Is balance RELATIONAL or STATISTICAL?")
        print("=" * 75)
        print()
        
        relational_score = 0
        if distance_verdict == "attraction":
            relational_score += 1
        if nn_verdict == "opposite_attraction":
            relational_score += 1
        if mixing_verdict == "interleaved":
            relational_score += 1
        
        if relational_score >= 2:
            print("RELATIONAL BALANCE SUPPORTED")
            print()
            print("Evidence: Opposite-sign defects show preferential interaction:")
            if distance_verdict == "attraction":
                print("  - +- pairs are closer (attraction)")
            if nn_verdict == "opposite_attraction":
                print("  - Nearest neighbors favor opposite sign")
            if mixing_verdict == "interleaved":
                print("  - Populations spatially interleave")
            print()
            print("→ Balance is enforced by INTERACTION DYNAMICS, not just statistics.")
            conclusion = "relational"
        elif relational_score == 0 and (distance_verdict == "repulsion" or nn_verdict == "same_clustering"):
            print("SEGREGATION PATTERN FOUND")
            print()
            print("Same-sign defects cluster together:")
            if distance_verdict == "repulsion":
                print("  - +- pairs are farther apart")
            if nn_verdict == "same_clustering":
                print("  - NN favors same sign")
            if mixing_verdict == "segregated":
                print("  - Populations spatially segregate")
            print()
            print("→ Sectors may be competing rather than balancing.")
            conclusion = "segregation"
        else:
            print("STATISTICAL BALANCE (No strong interaction pattern)")
            print()
            print("No preferential interaction between opposite-sign defects.")
            print("Balance appears to be maintained statistically, not relationally.")
            conclusion = "statistical"
    else:
        conclusion = "insufficient_data"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_cross_sector_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'cross_sector_interaction',
            'question': 'Is balance relational or statistical?',
            'history': history,
            'distance_verdict': distance_verdict if 'distance_verdict' in dir() else 'unknown',
            'nn_verdict': nn_verdict if 'nn_verdict' in dir() else 'unknown',
            'mixing_verdict': mixing_verdict if 'mixing_verdict' in dir() else 'unknown',
            'conclusion': conclusion,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, conclusion


if __name__ == "__main__":
    history, conclusion = run_cross_sector_interaction_test()
