"""
Multi-Seed Baseline Verification
================================

Purpose: Determine if mixed remnant strategies provide real improvement
over random, or if initial results were seed-dependent artifacts.

Seeds: 10 different seeds
Rates: 0.075, 0.10, 0.125, 0.15, 0.175
Strategies: random, 10% memory, 25% memory

Decision rule:
- A strategy wins only if it improves sustain_probability or mean_late_N
  across multiple seeds at the same or lower rate.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import Dict, List
import json


class MultiSeedSimulator:
    def __init__(self, size=48, rate=0.15, remnant_frac=0.0):
        self.size = size
        self.rate = rate
        self.remnant_frac = remnant_frac
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        self.step_count = 0
        self.creations = 0
        
        # Build coupling field
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = size * 0.25
        
        self.coupling = np.zeros((size, size, size))
        self.coupling[r <= interior_r] = 0.7
        self.coupling[r >= interior_r + 10.0] = 0.2
        mask_t = (r > interior_r) & (r < interior_r + 10.0)
        t = (r[mask_t] - interior_r) / 10.0
        self.coupling[mask_t] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
        self.channel = np.zeros((size, size, size))
        self.remnant = np.zeros((size, size, size))
        
        self.creation_sites = []
    
    def inject_vortex_at(self, cx, cy, cz, chirality=1):
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
    
    def seed_structure(self, n_pairs=15):
        center = self.size // 2
        for _ in range(n_pairs):
            angle1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(3, self.size*0.20)
            cx1 = int(np.clip(center + r1*np.cos(angle1), 5, self.size-5))
            cy1 = int(np.clip(center + r1*np.sin(angle1), 5, self.size-5))
            
            angle2 = angle1 + np.random.uniform(0.5, 1.5)
            r2 = np.random.uniform(3, self.size*0.20)
            cx2 = int(np.clip(center + r2*np.cos(angle2), 5, self.size-5))
            cy2 = int(np.clip(center + r2*np.sin(angle2), 5, self.size-5))
            
            self.inject_vortex_at(cx1, cy1, center, +1)
            self.inject_vortex_at(cx2, cy2, center, -1)
    
    def select_location(self):
        center = self.size // 2
        
        if np.random.random() < self.remnant_frac:
            weights = 0.01 + self.remnant
            x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), np.arange(self.size), indexing='ij')
            r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
            weights = weights * (r < self.size * 0.30)
            ws = np.sum(weights)
            if ws > 1e-10:
                wf = weights.flatten() / ws
                idx = np.random.choice(len(wf), p=wf)
                cx = idx // (self.size * self.size)
                cy = (idx % (self.size * self.size)) // self.size
                cz = idx % self.size
                return int(cx), int(cy), int(cz)
        
        angle = np.random.uniform(0, 2*np.pi)
        r = np.random.uniform(3, self.size*0.20)
        cx = int(np.clip(center + r*np.cos(angle), 5, self.size-5))
        cy = int(np.clip(center + r*np.sin(angle), 5, self.size-5))
        return cx, cy, center
    
    def attempt_creation(self):
        high_tau = self.tau > 1.001
        if not np.any(high_tau):
            return 0
        
        candidates = np.where(high_tau)
        n = len(candidates[0])
        if n == 0:
            return 0
        
        indices = np.random.choice(n, min(50, n), replace=False)
        
        for idx in indices:
            local_tau = self.tau[candidates[0][idx], candidates[1][idx], candidates[2][idx]]
            prob = (local_tau - 1.001) * self.rate
            
            if np.random.random() < prob:
                cx, cy, cz = self.select_location()
                self.creation_sites.append((cx, cy, cz, self.step_count))
                
                angle2 = np.random.uniform(0, 2*np.pi)
                d = np.random.uniform(3, 6)
                cx2 = int(np.clip(cx + d*np.cos(angle2), 3, self.size-3))
                cy2 = int(np.clip(cy + d*np.sin(angle2), 3, self.size-3))
                
                self.inject_vortex_at(cx, cy, cz, +1)
                self.inject_vortex_at(cx2, cy2, cz, -1)
                self.creations += 1
                return 1
        return 0
    
    def step(self, dt=0.04):
        self.step_count += 1
        self.attempt_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6*f)
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
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
        
        self.channel += 0.01 * (topology_norm - self.channel)
        self.channel = np.clip(self.channel, 0, 1)
        
        self.remnant += 0.02 * topology_norm
        self.remnant *= 0.999
        self.remnant = np.clip(self.remnant, 0, 1)
        
        protection = topology_norm * self.channel
        radial_r, radial_i = self.psi_r / amp, self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects(self):
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < 0.4)
        return sum(1 for i in range(1, n+1) if np.sum(labeled == i) >= 5)
    
    def compute_entropy(self):
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


def run_single(seed: int, rate: float, remnant_frac: float, warmup: int = 150, run: int = 500):
    """Run single configuration with given seed."""
    np.random.seed(seed)
    
    sim = MultiSeedSimulator(size=48, rate=rate, remnant_frac=remnant_frac)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    sim.seed_structure(n_pairs=15)
    
    # Warmup
    for _ in range(warmup):
        sim.step()
    
    # Run and track late activity
    late = []
    for step in range(run):
        sim.step()
        if step >= run - 200 and step % 40 == 0:
            late.append(sim.detect_defects())
    
    avg_n = float(np.mean(late))
    
    return {
        'seed': seed,
        'rate': rate,
        'remnant_frac': remnant_frac,
        'avg_late_n': avg_n,
        'creations': sim.creations,
        'entropy': sim.compute_entropy(),
        'sustained': avg_n > 0.3
    }


def main():
    print("=" * 80)
    print("  MULTI-SEED BASELINE VERIFICATION")
    print("=" * 80)
    print()
    print("Purpose: Distinguish real signal from single-seed noise")
    print()
    
    # Configuration
    seeds = [10, 20, 30, 40, 50, 60, 70, 80]  # 8 seeds
    rates = [0.075, 0.10, 0.125, 0.15]  # 4 rates
    strategies = [
        (0.0, "Random"),
        (0.10, "10% Mem"),
        (0.25, "25% Mem"),
    ]
    
    all_results = []
    
    # Run all configurations
    total = len(seeds) * len(rates) * len(strategies)
    done = 0
    
    for frac, name in strategies:
        print(f"\n{name}:")
        print("-" * 70)
        
        for rate in rates:
            seed_results = []
            for seed in seeds:
                r = run_single(seed, rate, frac)
                all_results.append(r)
                seed_results.append(r)
                done += 1
            
            # Aggregate for this rate
            sustained_count = sum(1 for r in seed_results if r['sustained'])
            avg_n_list = [r['avg_late_n'] for r in seed_results]
            mean_n = np.mean(avg_n_list)
            std_n = np.std(avg_n_list)
            median_n = np.median(avg_n_list)
            sustain_prob = sustained_count / len(seeds)
            
            print(f"  rate={rate:.3f}: sustain={sustain_prob*100:5.1f}%, "
                  f"mean_N={mean_n:5.2f} (±{std_n:4.2f}), median_N={median_n:5.2f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("  AGGREGATE SUMMARY")
    print("=" * 80)
    
    print(f"\n{'Strategy':>10} | {'Rate':>6} | {'Sustain%':>8} | {'Mean N':>7} | {'Std N':>6} | {'Median N':>8}")
    print("-" * 70)
    
    summary = {}
    for frac, name in strategies:
        summary[name] = {}
        for rate in rates:
            rate_results = [r for r in all_results if r['remnant_frac'] == frac and r['rate'] == rate]
            
            sustained_count = sum(1 for r in rate_results if r['sustained'])
            avg_n_list = [r['avg_late_n'] for r in rate_results]
            mean_n = np.mean(avg_n_list)
            std_n = np.std(avg_n_list)
            median_n = np.median(avg_n_list)
            sustain_prob = sustained_count / len(seeds)
            
            summary[name][rate] = {
                'sustain_prob': sustain_prob,
                'mean_n': mean_n,
                'std_n': std_n,
                'median_n': median_n
            }
            
            print(f"{name:>10} | {rate:>6.3f} | {sustain_prob*100:>7.1f}% | "
                  f"{mean_n:>7.2f} | {std_n:>6.2f} | {median_n:>8.2f}")
        print()
    
    # Decision
    print("=" * 80)
    print("  DECISION ANALYSIS")
    print("=" * 80)
    
    # Compare at each rate
    for rate in rates:
        print(f"\nAt rate={rate:.3f}:")
        random_data = summary["Random"][rate]
        
        for name in ["10% Mem", "25% Mem"]:
            mixed_data = summary[name][rate]
            
            # Compare sustain probability
            sustain_diff = mixed_data['sustain_prob'] - random_data['sustain_prob']
            mean_diff = mixed_data['mean_n'] - random_data['mean_n']
            mean_ratio = mixed_data['mean_n'] / max(0.01, random_data['mean_n'])
            
            print(f"  {name} vs Random:")
            print(f"    sustain: {mixed_data['sustain_prob']*100:.0f}% vs {random_data['sustain_prob']*100:.0f}% "
                  f"({'+'if sustain_diff>=0 else ''}{sustain_diff*100:.0f}%)")
            print(f"    mean_N: {mixed_data['mean_n']:.2f} vs {random_data['mean_n']:.2f} "
                  f"({mean_ratio:.2f}x)")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("  VERDICT")
    print("=" * 80)
    
    # Check if any mixed strategy consistently beats random
    wins = []
    for name in ["10% Mem", "25% Mem"]:
        win_count = 0
        for rate in rates:
            random_data = summary["Random"][rate]
            mixed_data = summary[name][rate]
            
            # Win if: higher sustain_prob OR (equal sustain_prob AND higher mean_n)
            if mixed_data['sustain_prob'] > random_data['sustain_prob']:
                win_count += 1
            elif (mixed_data['sustain_prob'] == random_data['sustain_prob'] and 
                  mixed_data['mean_n'] > random_data['mean_n'] * 1.2):
                win_count += 1
        
        if win_count >= len(rates) // 2:
            wins.append(name)
    
    if wins:
        print(f"\nMixed strategy shows consistent improvement: {', '.join(wins)}")
        print("→ Remnant coupling VALIDATED for integration")
    else:
        print("\nNo mixed strategy shows consistent improvement over random.")
        print("→ Results are seed-dependent; remnant coupling remains AMBIGUOUS")
        print("→ Consider: more seeds, longer runs, or proceed to Damping → τ")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/multi_seed_results.json'
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
            'test': 'multi_seed_verification',
            'seeds': seeds,
            'rates': rates,
            'results': clean_results,
            'summary': {name: {str(rate): data for rate, data in rate_dict.items()} 
                       for name, rate_dict in summary.items()}
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
