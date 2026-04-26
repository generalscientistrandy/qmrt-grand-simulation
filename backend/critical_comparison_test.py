"""
Critical Comparison Test - 48³ Grid
===================================

Focused test comparing ONLY:
- Pure Random vs Weak Memory (10%) vs Light Memory (25%)
- At rates: 0.10, 0.15, 0.20
- Short runs (500 steps) for quick falsification

Question: Can weak remnant bias sustain at rate < 0.15?
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import cdist
from typing import Dict, Tuple


class MixedSimulator:
    def __init__(self, size: int = 48, creation_rate: float = 0.15, remnant_fraction: float = 0.0):
        self.size = size
        self.tau_creation_threshold = 1.001
        self.creation_rate = creation_rate
        self.remnant_fraction = remnant_fraction
        self.remnant_alpha = 1.0
        self.remnant_epsilon = 0.01
        
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
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), np.arange(self.size), indexing='ij')
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
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), np.arange(self.size), indexing='ij')
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
        for _ in range(n_pairs):
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
    
    def select_creation_location(self) -> Tuple[int, int, int]:
        center = self.size // 2
        
        if np.random.random() < self.remnant_fraction:
            # Remnant-biased
            weights = self.remnant_epsilon + np.power(self.remnant_field + 1e-10, self.remnant_alpha)
            x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), np.arange(self.size), indexing='ij')
            r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
            interior_mask = r < self.size * 0.30
            weights = weights * interior_mask
            weights_sum = np.sum(weights)
            
            if weights_sum > 1e-10:
                weights_flat = weights.flatten() / weights_sum
                idx = np.random.choice(len(weights_flat), p=weights_flat)
                cx = idx // (self.size * self.size)
                cy = (idx % (self.size * self.size)) // self.size
                cz = idx % self.size
                return int(cx), int(cy), int(cz)
        
        # Random fallback
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(3, self.size * 0.20)
        cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
        cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
        return cx, cy, center
    
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
            probability = (local_tau - self.tau_creation_threshold) * self.creation_rate
            
            if np.random.random() < probability:
                loc_cx, loc_cy, loc_cz = self.select_creation_location()
                self.creation_sites.append((loc_cx, loc_cy, loc_cz, self.step_count))
                
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
    
    def detect_defects(self, threshold: float = 0.4) -> int:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        count = 0
        for i in range(1, n + 1):
            if np.sum(labeled == i) >= 5:
                count += 1
        return count
    
    def compute_entropy(self) -> float:
        if len(self.creation_sites) < 3:
            return 0.0
        positions = np.array([(s[0], s[1]) for s in self.creation_sites])
        n_bins = 8
        hist, _, _ = np.histogram2d(positions[:, 0], positions[:, 1],
                                    bins=[np.linspace(0, self.size, n_bins + 1)] * 2)
        hist_flat = hist.flatten()
        hist_norm = hist_flat / np.sum(hist_flat)
        hist_norm = hist_norm[hist_norm > 0]
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10)) / np.log2(n_bins * n_bins)
        return float(entropy)


def run_single(rate: float, frac: float, label: str) -> Dict:
    """Run a single test - 500 steps after 150 warmup."""
    sim = MixedSimulator(size=48, creation_rate=rate, remnant_fraction=frac)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    sim.seed_balanced_structure(n_pairs=15)
    
    # Warmup
    for _ in range(150):
        sim.step()
    
    # Run
    late = []
    for step in range(500):
        sim.step()
        if step >= 300 and step % 40 == 0:
            late.append(sim.detect_defects())
    
    avg_n = float(np.mean(late))
    entropy = sim.compute_entropy()
    
    return {
        'label': label,
        'rate': rate,
        'frac': frac,
        'avg_n': avg_n,
        'creations': sim.spontaneous_creations,
        'entropy': entropy,
        'sustained': avg_n > 0.3
    }


def main():
    print("=" * 75)
    print("  CRITICAL COMPARISON: Random vs Weak Memory")
    print("=" * 75)
    print("\nQuestion: Can weak remnant (10-25%) sustain at rate < 0.15?")
    print()
    
    configs = [
        (0.0, "Random"),
        (0.10, "10% Mem"),
        (0.25, "25% Mem"),
    ]
    
    rates = [0.10, 0.15, 0.20]
    
    results = []
    
    print(f"{'Strategy':>10} │ {'Rate':>6} │ {'Avg N':>6} │ {'Creates':>7} │ {'Entropy':>7} │ {'OK':>4}")
    print("-" * 60)
    
    for frac, name in configs:
        for rate in rates:
            print(f"Running {name} @ rate={rate}...", end=" ", flush=True)
            r = run_single(rate, frac, name)
            results.append(r)
            ok = "YES" if r['sustained'] else "no"
            print(f"\r{name:>10} │ {rate:>6.2f} │ {r['avg_n']:>6.2f} │ {r['creations']:>7} │ {r['entropy']:>7.3f} │ {ok:>4}")
        print()
    
    # Summary
    print("=" * 75)
    print("  MINIMAL SUSTAINABLE RATE")
    print("=" * 75)
    
    for frac, name in configs:
        frac_r = [r for r in results if r['frac'] == frac]
        sus = [r for r in frac_r if r['sustained']]
        if sus:
            min_rate = min(r['rate'] for r in sus)
            print(f"  {name:>10}: {min_rate:.2f}")
        else:
            print(f"  {name:>10}: NONE")
    
    # Decision
    print("\n" + "=" * 75)
    print("  DECISION")
    print("=" * 75)
    
    random_sus = [r for r in results if r['frac'] == 0.0 and r['sustained']]
    random_min = min(r['rate'] for r in random_sus) if random_sus else 999
    
    wins = []
    for frac, name in [(0.10, "10% Mem"), (0.25, "25% Mem")]:
        frac_sus = [r for r in results if r['frac'] == frac and r['sustained']]
        if frac_sus:
            frac_min = min(r['rate'] for r in frac_sus)
            if frac_min < random_min:
                wins.append((name, frac_min))
            elif frac_min == random_min:
                # Check if better metrics at same rate
                random_at_min = next((r for r in results if r['frac'] == 0.0 and r['rate'] == random_min), None)
                frac_at_min = next((r for r in results if r['frac'] == frac and r['rate'] == random_min), None)
                if frac_at_min and random_at_min:
                    if frac_at_min['avg_n'] > random_at_min['avg_n'] * 1.2:
                        wins.append((f"{name} (better N)", frac_min))
    
    if wins:
        print(f"\n✓ MIXED STRATEGY SHOWS PROMISE!")
        for name, rate in wins:
            print(f"  {name}: rate={rate:.2f}")
        print("\n→ Remnant coupling may be viable with weak memory")
    else:
        print(f"\n✗ NO MIXED STRATEGY BEATS RANDOM (baseline: {random_min:.2f})")
        print("\n→ RETIRE Remnant → Creation as primary recovery path")
        print("→ Proceed to Damping → τ coupling")


if __name__ == "__main__":
    main()
