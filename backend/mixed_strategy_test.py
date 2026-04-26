"""
Mixed Remnant/Random Strategy Sweep
====================================

HYPOTHESIS: Pure remnant coupling overfits to dead topology sites, but weak
remnant bias may preserve structural memory while random creation supplies
spatial exploration.

SWEEP:
- Remnant %: 0 (pure random), 10, 25, 50, 75, 100 (pure remnant)
- Rates: 0.10, 0.125, 0.15, 0.175, 0.20
- Alpha: 1.0, 2.0

SUCCESS CRITERIA:
- Primary: Any mixed strategy sustains below rate = 0.15
- Secondary: At rate = 0.15, mixed strategy produces better metrics than pure random

DECISION RULE:
- If no mixed strategy beats random at rate <= 0.15, retire Remnant → Creation
  and proceed to Damping → τ coupling.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist
from typing import Dict, List, Tuple
import json


class MixedStrategySimulator:
    """
    Simulator with mixed remnant/random creation strategy.
    """
    
    def __init__(self, size: int = 48,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 remnant_fraction: float = 0.0,  # 0.0 = pure random, 1.0 = pure remnant
                 remnant_alpha: float = 1.0,
                 remnant_epsilon: float = 0.01):
        
        self.size = size
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.remnant_fraction = remnant_fraction
        self.remnant_alpha = remnant_alpha
        self.remnant_epsilon = remnant_epsilon
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
        # Tracking for metrics
        self.creation_sites = []  # [(x, y, z, step), ...]
        self.annihilation_events = []  # [(step, n_before, n_after), ...]
        self.spontaneous_creations = 0
        self.creations_at_remnant = 0
        self.reoccupation_count = 0  # Creations at sites with recent prior creation
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        mask_interior = r <= interior_r
        mask_exterior = r >= interior_r + 10.0
        mask_transition = ~mask_interior & ~mask_exterior
        
        coupling[mask_interior] = 0.7
        coupling[mask_exterior] = 0.2
        t = (r[mask_transition] - interior_r) / 10.0
        coupling[mask_transition] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
        return coupling
    
    def inject_vortex_at(self, cx: int, cy: int, cz: int, chirality: int = 1):
        """Inject a single vortex at specific 3D location."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / (2 * 3**2))
        
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_balanced_structure(self, n_pairs: int = 15):
        """Initial seeding to build up remnant field."""
        center = self.size // 2
        
        for i in range(n_pairs):
            angle1 = np.random.uniform(0, 2 * np.pi)
            radius1 = np.random.uniform(3, self.size * 0.20)
            cx1 = int(np.clip(center + radius1 * np.cos(angle1), 5, self.size - 5))
            cy1 = int(np.clip(center + radius1 * np.sin(angle1), 5, self.size - 5))
            cz1 = center
            
            angle2 = angle1 + np.random.uniform(0.5, 1.5)
            radius2 = np.random.uniform(3, self.size * 0.20)
            cx2 = int(np.clip(center + radius2 * np.cos(angle2), 5, self.size - 5))
            cy2 = int(np.clip(center + radius2 * np.sin(angle2), 5, self.size - 5))
            cz2 = center
            
            self.inject_vortex_at(cx1, cy1, cz1, +1)
            self.inject_vortex_at(cx2, cy2, cz2, -1)
    
    def select_creation_location_random(self) -> Tuple[int, int, int]:
        """Random location in interior."""
        center = self.size // 2
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(3, self.size * 0.20)
        cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
        cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
        cz = center
        return cx, cy, cz
    
    def select_creation_location_remnant(self) -> Tuple[int, int, int]:
        """Remnant-biased location selection."""
        weights = self.remnant_epsilon + np.power(self.remnant_field + 1e-10, self.remnant_alpha)
        
        center = self.size // 2
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_mask = r < self.size * 0.30
        
        weights = weights * interior_mask
        weights_sum = np.sum(weights)
        
        if weights_sum < 1e-10:
            return self.select_creation_location_random()
        
        weights_flat = weights.flatten() / weights_sum
        idx = np.random.choice(len(weights_flat), p=weights_flat)
        
        cx = idx // (self.size * self.size)
        cy = (idx % (self.size * self.size)) // self.size
        cz = idx % self.size
        
        return int(cx), int(cy), int(cz)
    
    def select_creation_location(self) -> Tuple[int, int, int]:
        """Mixed strategy: remnant_fraction chance of remnant, otherwise random."""
        if np.random.random() < self.remnant_fraction:
            return self.select_creation_location_remnant()
        else:
            return self.select_creation_location_random()
    
    def check_reoccupation(self, cx: int, cy: int, cz: int, window: int = 100) -> bool:
        """Check if this creation site was recently used."""
        recent_sites = [(s[0], s[1], s[2]) for s in self.creation_sites 
                        if self.step_count - s[3] < window]
        
        for sx, sy, sz in recent_sites:
            dist = np.sqrt((cx - sx)**2 + (cy - sy)**2 + (cz - sz)**2)
            if dist < 5:  # Within 5 units = reoccupation
                return True
        return False
    
    def attempt_spontaneous_creation(self):
        """τ-mediated pair creation with mixed strategy."""
        high_tau_mask = self.tau > self.tau_creation_threshold
        
        if not np.any(high_tau_mask):
            return 0
        
        candidates = np.where(high_tau_mask)
        n_candidates = len(candidates[0])
        
        if n_candidates == 0:
            return 0
        
        n_sample = min(50, n_candidates)
        indices = np.random.choice(n_candidates, n_sample, replace=False)
        
        creations = 0
        
        for idx in indices:
            cx = candidates[0][idx]
            cy = candidates[1][idx]
            cz = candidates[2][idx]
            
            local_tau = self.tau[cx, cy, cz]
            tau_excess = local_tau - self.tau_creation_threshold
            probability = tau_excess * self.creation_rate
            
            if np.random.random() < probability:
                loc_cx, loc_cy, loc_cz = self.select_creation_location()
                
                # Track metrics
                self.creation_sites.append((loc_cx, loc_cy, loc_cz, self.step_count))
                
                remnant_at_site = self.remnant_field[loc_cx, loc_cy, loc_cz]
                if remnant_at_site > 0.3:
                    self.creations_at_remnant += 1
                
                if self.check_reoccupation(loc_cx, loc_cy, loc_cz):
                    self.reoccupation_count += 1
                
                # Create balanced pair
                offset_angle = np.random.uniform(0, 2 * np.pi)
                offset_dist = np.random.uniform(3, 6)
                
                cx2 = int(np.clip(loc_cx + offset_dist * np.cos(offset_angle), 3, self.size - 3))
                cy2 = int(np.clip(loc_cy + offset_dist * np.sin(offset_angle), 3, self.size - 3))
                
                self.inject_vortex_at(loc_cx, loc_cy, loc_cz, +1)
                self.inject_vortex_at(cx2, cy2, loc_cz, -1)
                
                creations += 1
                self.spontaneous_creations += 1
                
                break
        
        return creations
    
    def step(self, dt: float = 0.04):
        """Evolution step."""
        self.step_count += 1
        
        # Track defects before
        n_before = self.detect_defects()['n_total']
        
        self.attempt_spontaneous_creation()
        
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
        
        # Track defects after
        n_after = self.detect_defects()['n_total']
        if n_after < n_before - 1:  # Significant drop = annihilation
            self.annihilation_events.append((self.step_count, n_before, n_after))
    
    def detect_defects(self, threshold: float = 0.4) -> Dict:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        n_pos = 0
        n_neg = 0
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                local_vort = vorticity[cx, cy, coords[2][0]]
                
                if local_vort > 0.05:
                    n_pos += 1
                elif local_vort < -0.05:
                    n_neg += 1
        
        return {'n_pos': n_pos, 'n_neg': n_neg, 'n_total': n_pos + n_neg}
    
    def compute_dispersion_metrics(self) -> Dict:
        """Compute spatial dispersion metrics for creation sites."""
        if len(self.creation_sites) < 3:
            return {
                'creation_site_entropy': 0.0,
                'mean_nearest_neighbor_dist': 0.0,
                'annihilation_rate': 0.0,
                'reoccupation_rate': 0.0
            }
        
        # Extract 2D positions (x, y) from creation sites
        positions = np.array([(s[0], s[1]) for s in self.creation_sites])
        
        # Mean nearest neighbor distance
        if len(positions) >= 2:
            distances = pdist(positions)
            # For each point, find its nearest neighbor
            from scipy.spatial.distance import cdist
            dist_matrix = cdist(positions, positions)
            np.fill_diagonal(dist_matrix, np.inf)
            nearest_dists = np.min(dist_matrix, axis=1)
            mean_nn_dist = np.mean(nearest_dists)
        else:
            mean_nn_dist = 0.0
        
        # Spatial entropy (discretize into bins)
        n_bins = 8
        bin_edges = np.linspace(0, self.size, n_bins + 1)
        hist, _, _ = np.histogram2d(
            positions[:, 0], positions[:, 1],
            bins=[bin_edges, bin_edges]
        )
        hist_flat = hist.flatten()
        hist_norm = hist_flat / np.sum(hist_flat)
        hist_norm = hist_norm[hist_norm > 0]  # Remove zeros for entropy
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        max_entropy = np.log2(n_bins * n_bins)
        normalized_entropy = entropy / max_entropy
        
        # Annihilation rate
        n_annihilations = len(self.annihilation_events)
        annihilation_rate = n_annihilations / max(1, self.spontaneous_creations)
        
        # Reoccupation rate
        reoccupation_rate = self.reoccupation_count / max(1, self.spontaneous_creations)
        
        return {
            'creation_site_entropy': float(normalized_entropy),
            'mean_nearest_neighbor_dist': float(mean_nn_dist),
            'annihilation_rate': float(annihilation_rate),
            'reoccupation_rate': float(reoccupation_rate)
        }


def run_single_test(rate: float, remnant_frac: float, alpha: float, steps: int = 1000) -> Dict:
    """Run a single test configuration."""
    sim = MixedStrategySimulator(
        size=48,
        tau_creation_threshold=1.001,
        creation_rate=rate,
        remnant_fraction=remnant_frac,
        remnant_alpha=alpha,
        remnant_epsilon=0.01
    )
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    sim.seed_balanced_structure(n_pairs=15)
    
    # Warmup to build remnant
    for _ in range(200):
        sim.step()
    
    # Track late activity
    late_activity = []
    for step in range(steps):
        sim.step()
        if step >= steps - 400 and step % 50 == 0:
            defects = sim.detect_defects()
            late_activity.append(defects['n_total'])
    
    avg_late_n = float(np.mean(late_activity))
    dispersion = sim.compute_dispersion_metrics()
    
    return {
        'rate': rate,
        'remnant_frac': remnant_frac,
        'alpha': alpha,
        'avg_late_n': avg_late_n,
        'creations': sim.spontaneous_creations,
        'sustained': avg_late_n > 0.3,
        **dispersion
    }


def run_mixed_strategy_sweep():
    """Run the full mixed strategy sweep."""
    print("=" * 90)
    print("  MIXED REMNANT/RANDOM STRATEGY SWEEP")
    print("=" * 90)
    print()
    print("HYPOTHESIS: Weak remnant bias preserves memory while random supplies exploration.")
    print("SUCCESS: Any mixed strategy sustains below rate = 0.15 (random baseline).")
    print()
    
    # Configuration
    remnant_fracs = [0.0, 0.10, 0.25, 0.50, 0.75, 1.0]
    rates = [0.10, 0.125, 0.15, 0.175, 0.20]
    alphas = [1.0, 2.0]
    
    frac_names = {
        0.0: "Pure Random",
        0.10: "Weak Memory (10%)",
        0.25: "Light Memory (25%)",
        0.50: "Balanced (50%)",
        0.75: "Strong Memory (75%)",
        1.0: "Pure Remnant"
    }
    
    all_results = []
    
    for alpha in alphas:
        print(f"\n{'='*90}")
        print(f"  ALPHA = {alpha}")
        print(f"{'='*90}")
        
        for frac in remnant_fracs:
            print(f"\n{frac_names[frac]} (remnant={int(frac*100)}%, random={int((1-frac)*100)}%):")
            print("-" * 85)
            print(f"{'Rate':>6} │ {'Avg N':>7} │ {'Creates':>8} │ {'Entropy':>8} │ {'NN Dist':>8} │ {'Reocc%':>7} │ {'OK':>4}")
            print("-" * 85)
            
            for rate in rates:
                r = run_single_test(rate, frac, alpha)
                all_results.append(r)
                
                ok = "YES" if r['sustained'] else "no"
                print(f"{rate:>6.3f} │ {r['avg_late_n']:>7.2f} │ {r['creations']:>8} │ "
                      f"{r['creation_site_entropy']:>8.3f} │ {r['mean_nearest_neighbor_dist']:>8.2f} │ "
                      f"{r['reoccupation_rate']*100:>6.1f}% │ {ok:>4}")
    
    # Summary analysis
    print("\n" + "=" * 90)
    print("  SUMMARY: MINIMAL SUSTAINABLE RATE BY STRATEGY")
    print("=" * 90)
    
    for alpha in alphas:
        print(f"\nAlpha = {alpha}:")
        print("-" * 60)
        
        for frac in remnant_fracs:
            frac_results = [r for r in all_results 
                          if r['remnant_frac'] == frac and r['alpha'] == alpha]
            sustained = [r for r in frac_results if r['sustained']]
            
            if sustained:
                min_rate = min(r['rate'] for r in sustained)
                min_result = next(r for r in sustained if r['rate'] == min_rate)
                print(f"  {frac_names[frac]:>25}: rate={min_rate:.3f}, "
                      f"N={min_result['avg_late_n']:.1f}, entropy={min_result['creation_site_entropy']:.3f}")
            else:
                print(f"  {frac_names[frac]:>25}: NO SUSTAINED CONFIG")
    
    # Critical comparison at rate = 0.15
    print("\n" + "=" * 90)
    print("  COMPARISON AT RATE = 0.15 (Random baseline threshold)")
    print("=" * 90)
    
    rate_15_results = [r for r in all_results if abs(r['rate'] - 0.15) < 0.01]
    
    print(f"\n{'Strategy':>25} │ {'Alpha':>5} │ {'Avg N':>7} │ {'Entropy':>8} │ {'NN Dist':>8} │ {'Reocc%':>7} │ {'OK':>4}")
    print("-" * 90)
    
    for r in sorted(rate_15_results, key=lambda x: (x['alpha'], x['remnant_frac'])):
        name = frac_names[r['remnant_frac']]
        ok = "YES" if r['sustained'] else "no"
        print(f"{name:>25} │ {r['alpha']:>5.1f} │ {r['avg_late_n']:>7.2f} │ "
              f"{r['creation_site_entropy']:>8.3f} │ {r['mean_nearest_neighbor_dist']:>8.2f} │ "
              f"{r['reoccupation_rate']*100:>6.1f}% │ {ok:>4}")
    
    # Decision
    print("\n" + "=" * 90)
    print("  DECISION")
    print("=" * 90)
    
    # Check if any mixed strategy beats random at rate < 0.15
    random_min = 0.15  # Known baseline
    
    best_mixed = None
    for r in all_results:
        if 0 < r['remnant_frac'] < 1.0 and r['sustained']:
            if best_mixed is None or r['rate'] < best_mixed['rate']:
                best_mixed = r
    
    if best_mixed and best_mixed['rate'] < random_min:
        print(f"\n✓ MIXED STRATEGY BEATS RANDOM!")
        print(f"  Best: {frac_names[best_mixed['remnant_frac']]} at rate={best_mixed['rate']:.3f}")
        print(f"  → Remnant coupling is VIABLE with weak memory bias")
    else:
        print(f"\n✗ NO MIXED STRATEGY BEATS RANDOM (min rate = {random_min})")
        if best_mixed:
            print(f"  Best mixed: {frac_names[best_mixed['remnant_frac']]} at rate={best_mixed['rate']:.3f}")
        print(f"  → RETIRE Remnant → Creation as primary recovery path")
        print(f"  → Proceed to Damping → τ coupling")
    
    # Check secondary criterion: better metrics at rate=0.15
    print("\n  Secondary check at rate=0.15:")
    random_at_15 = next((r for r in rate_15_results if r['remnant_frac'] == 0.0 and r['alpha'] == 1.0), None)
    
    if random_at_15:
        improvements = []
        for r in rate_15_results:
            if 0 < r['remnant_frac'] < 1.0 and r['sustained']:
                if r['avg_late_n'] > random_at_15['avg_late_n'] * 1.1:  # 10% better
                    improvements.append(('avg_late_n', r))
                if r['creation_site_entropy'] > random_at_15['creation_site_entropy'] * 1.05:
                    improvements.append(('entropy', r))
        
        if improvements:
            print(f"  Some mixed strategies show improvement at rate=0.15:")
            for metric, r in improvements:
                print(f"    - {frac_names[r['remnant_frac']]} (α={r['alpha']}): better {metric}")
        else:
            print(f"  No mixed strategy clearly outperforms random at rate=0.15")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/mixed_strategy_results.json'
    clean_results = []
    for r in all_results:
        clean_r = {}
        for k, v in r.items():
            if isinstance(v, (np.bool_, bool)):
                clean_r[k] = bool(v)
            elif isinstance(v, (np.integer, np.floating)):
                clean_r[k] = float(v)
            else:
                clean_r[k] = v
        clean_results.append(clean_r)
    
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'mixed_remnant_random_strategy',
            'hypothesis': 'Weak remnant bias preserves memory while random supplies exploration',
            'decision_rule': 'If no mixed strategy beats random at rate <= 0.15, retire remnant coupling',
            'results': clean_results,
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return all_results


if __name__ == "__main__":
    results = run_mixed_strategy_sweep()
