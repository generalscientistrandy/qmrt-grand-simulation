"""
Focused Mixed Strategy Test
============================

Reduced sweep to answer: Can weak remnant bias beat pure random at rate ≤ 0.15?

Focus on:
- rates: 0.10, 0.125, 0.15 (at/below random threshold)
- remnant fracs: 0.0 (baseline), 0.10, 0.25 (best candidates)
- alpha: 1.0 only (simpler dynamics)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist, cdist
from typing import Dict, Tuple
import json


class MixedStrategySimulator:
    def __init__(self, size: int = 48,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 remnant_fraction: float = 0.0,
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
        
        self.creation_sites = []
        self.spontaneous_creations = 0
        self.reoccupation_count = 0
        
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
        center = self.size // 2
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(3, self.size * 0.20)
        cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
        cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
        cz = center
        return cx, cy, cz
    
    def select_creation_location_remnant(self) -> Tuple[int, int, int]:
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
        if np.random.random() < self.remnant_fraction:
            return self.select_creation_location_remnant()
        else:
            return self.select_creation_location_random()
    
    def check_reoccupation(self, cx: int, cy: int, cz: int, window: int = 100) -> bool:
        recent_sites = [(s[0], s[1], s[2]) for s in self.creation_sites 
                        if self.step_count - s[3] < window]
        for sx, sy, sz in recent_sites:
            dist = np.sqrt((cx - sx)**2 + (cy - sy)**2 + (cz - sz)**2)
            if dist < 5:
                return True
        return False
    
    def attempt_spontaneous_creation(self):
        high_tau_mask = self.tau > self.tau_creation_threshold
        if not np.any(high_tau_mask):
            return 0
        
        candidates = np.where(high_tau_mask)
        n_candidates = len(candidates[0])
        if n_candidates == 0:
            return 0
        
        n_sample = min(50, n_candidates)
        indices = np.random.choice(n_candidates, n_sample, replace=False)
        
        for idx in indices:
            cx = candidates[0][idx]
            cy = candidates[1][idx]
            cz = candidates[2][idx]
            
            local_tau = self.tau[cx, cy, cz]
            tau_excess = local_tau - self.tau_creation_threshold
            probability = tau_excess * self.creation_rate
            
            if np.random.random() < probability:
                loc_cx, loc_cy, loc_cz = self.select_creation_location()
                self.creation_sites.append((loc_cx, loc_cy, loc_cz, self.step_count))
                
                if self.check_reoccupation(loc_cx, loc_cy, loc_cz):
                    self.reoccupation_count += 1
                
                offset_angle = np.random.uniform(0, 2 * np.pi)
                offset_dist = np.random.uniform(3, 6)
                cx2 = int(np.clip(loc_cx + offset_dist * np.cos(offset_angle), 3, self.size - 3))
                cy2 = int(np.clip(loc_cy + offset_dist * np.sin(offset_angle), 3, self.size - 3))
                
                self.inject_vortex_at(loc_cx, loc_cy, loc_cz, +1)
                self.inject_vortex_at(cx2, cy2, loc_cz, -1)
                
                self.spontaneous_creations += 1
                return 1
        
        return 0
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
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
    
    def detect_defects(self, threshold: float = 0.4) -> Dict:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        n_pos, n_neg = 0, 0
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
        if len(self.creation_sites) < 3:
            return {'entropy': 0.0, 'mean_nn_dist': 0.0, 'reocc_rate': 0.0}
        
        positions = np.array([(s[0], s[1]) for s in self.creation_sites])
        
        # Nearest neighbor distance
        dist_matrix = cdist(positions, positions)
        np.fill_diagonal(dist_matrix, np.inf)
        nearest_dists = np.min(dist_matrix, axis=1)
        mean_nn_dist = np.mean(nearest_dists)
        
        # Spatial entropy
        n_bins = 8
        bin_edges = np.linspace(0, self.size, n_bins + 1)
        hist, _, _ = np.histogram2d(positions[:, 0], positions[:, 1], bins=[bin_edges, bin_edges])
        hist_flat = hist.flatten()
        hist_norm = hist_flat / np.sum(hist_flat)
        hist_norm = hist_norm[hist_norm > 0]
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        max_entropy = np.log2(n_bins * n_bins)
        normalized_entropy = entropy / max_entropy
        
        reocc_rate = self.reoccupation_count / max(1, self.spontaneous_creations)
        
        return {
            'entropy': float(normalized_entropy),
            'mean_nn_dist': float(mean_nn_dist),
            'reocc_rate': float(reocc_rate)
        }


def run_test(rate: float, remnant_frac: float, steps: int = 800) -> Dict:
    sim = MixedStrategySimulator(
        size=48,
        tau_creation_threshold=1.001,
        creation_rate=rate,
        remnant_fraction=remnant_frac,
        remnant_alpha=1.0,
        remnant_epsilon=0.01
    )
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    sim.seed_balanced_structure(n_pairs=15)
    
    for _ in range(150):
        sim.step()
    
    late_activity = []
    for step in range(steps):
        sim.step()
        if step >= steps - 300 and step % 50 == 0:
            defects = sim.detect_defects()
            late_activity.append(defects['n_total'])
    
    avg_late_n = float(np.mean(late_activity))
    dispersion = sim.compute_dispersion_metrics()
    
    return {
        'rate': rate,
        'remnant_frac': remnant_frac,
        'avg_late_n': avg_late_n,
        'creations': sim.spontaneous_creations,
        'sustained': avg_late_n > 0.3,
        **dispersion
    }


def main():
    print("=" * 80)
    print("  FOCUSED MIXED STRATEGY TEST")
    print("=" * 80)
    print("\nQuestion: Can weak remnant bias beat pure random at rate ≤ 0.15?")
    print()
    
    # Critical configurations
    remnant_fracs = [0.0, 0.10, 0.25]
    rates = [0.10, 0.125, 0.15]
    
    frac_names = {0.0: "Pure Random", 0.10: "Weak (10%)", 0.25: "Light (25%)"}
    
    all_results = []
    
    print(f"{'Strategy':>15} │ {'Rate':>6} │ {'Avg N':>7} │ {'Creates':>8} │ {'Entropy':>8} │ {'NN Dist':>8} │ {'Reocc%':>7} │ {'OK':>4}")
    print("-" * 90)
    
    for frac in remnant_fracs:
        for rate in rates:
            r = run_test(rate, frac)
            all_results.append(r)
            
            ok = "YES" if r['sustained'] else "no"
            print(f"{frac_names[frac]:>15} │ {rate:>6.3f} │ {r['avg_late_n']:>7.2f} │ "
                  f"{r['creations']:>8} │ {r['entropy']:>8.3f} │ {r['mean_nn_dist']:>8.2f} │ "
                  f"{r['reocc_rate']*100:>6.1f}% │ {ok:>4}")
    
    # Analysis
    print("\n" + "=" * 80)
    print("  ANALYSIS")
    print("=" * 80)
    
    # Find min sustainable rate for each strategy
    print("\nMinimal Sustainable Rate:")
    for frac in remnant_fracs:
        frac_results = [r for r in all_results if r['remnant_frac'] == frac]
        sustained = [r for r in frac_results if r['sustained']]
        if sustained:
            min_rate = min(r['rate'] for r in sustained)
            print(f"  {frac_names[frac]:>15}: {min_rate:.3f}")
        else:
            print(f"  {frac_names[frac]:>15}: NONE (all failed)")
    
    # Decision
    print("\n" + "=" * 80)
    print("  DECISION")
    print("=" * 80)
    
    random_sustained = [r for r in all_results if r['remnant_frac'] == 0.0 and r['sustained']]
    random_min = min(r['rate'] for r in random_sustained) if random_sustained else 999
    
    mixed_wins = []
    for frac in [0.10, 0.25]:
        frac_sustained = [r for r in all_results if r['remnant_frac'] == frac and r['sustained']]
        if frac_sustained:
            frac_min = min(r['rate'] for r in frac_sustained)
            if frac_min < random_min:
                mixed_wins.append((frac, frac_min))
    
    if mixed_wins:
        print(f"\n✓ MIXED STRATEGY BEATS RANDOM!")
        for frac, rate in mixed_wins:
            print(f"  {frac_names[frac]} sustains at rate={rate:.3f} < random {random_min:.3f}")
        print(f"  → Remnant coupling VIABLE with weak memory bias")
    else:
        print(f"\n✗ NO MIXED STRATEGY BEATS RANDOM (baseline: {random_min:.3f})")
        print(f"  → RETIRE Remnant → Creation as primary recovery path")
        print(f"  → Proceed to Damping → τ coupling")
    
    # Save
    output_path = '/app/backend/qmrt_topology/papers/mixed_strategy_focused_results.json'
    clean_results = [{k: (bool(v) if isinstance(v, (np.bool_, bool)) else 
                         float(v) if isinstance(v, (np.integer, np.floating)) else v)
                     for k, v in r.items()} for r in all_results]
    
    with open(output_path, 'w') as f:
        json.dump({'test': 'mixed_strategy_focused', 'results': clean_results}, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return all_results


if __name__ == "__main__":
    main()
