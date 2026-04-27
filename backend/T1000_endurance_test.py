"""
T=1000 Endurance Test: Regulated Recovery v1.1
===============================================

PURPOSE: Confirm v1.1 maintains stability over twice the validation window.

CONFIGURATION (Regulated Recovery v1.1):
  damping_to_tau = 0.20
  tau_cap = 1.8
  grid = 32
  dt = 0.12
  max_T = 1000
  n_seeds = 5
  measure_every = 100

DECISION RULES:
  - If N stable/increases at T=1000: lock v1.1 as primary recovery mode
  - If N slowly declines but >> baseline: needs Channel release → τ support
  - If N spikes then collapses: d=0.20 overdriven, fall back to d=0.15
  - If tau_loc > 2.0: test tau_cap=1.6 or add τ smoothing

TRACKING:
  N_defects, N_std, tau_mean, tau_max, tau_localization_index,
  creation_count, energy_total, late_N trend, extinction_count
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List
import time
import json


# Regulated Recovery v1.1 Configuration
REGULATED_RECOVERY_TAU_CAP = 1.8
OPTIMAL_DAMPING_TO_TAU = 0.20


class EnduranceSimulator:
    """Simulator for T=1000 endurance testing."""
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = OPTIMAL_DAMPING_TO_TAU,
                 tau_cap: float = REGULATED_RECOVERY_TAU_CAP):
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        
        self.T = 0.0
        self.step_count = 0
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        self.channel = np.zeros((size, size, size))
        
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
        self.creations = 0
        self.total_damped = 0.0
        self.total_recycled = 0.0
        self.explosion = False
        
    def inject_vortex(self, cx, cy, cz, chirality=1):
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / 18)
        
        vortex = np.tanh(r / 2.5) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_structure(self, n_pairs=8):
        center = self.size // 2
        for _ in range(n_pairs):
            a1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.17)
            cx1 = int(np.clip(center + r1 * np.cos(a1), 3, self.size - 3))
            cy1 = int(np.clip(center + r1 * np.sin(a1), 3, self.size - 3))
            
            a2 = a1 + np.random.uniform(0.5, 1.5)
            r2 = np.random.uniform(2, self.size * 0.17)
            cx2 = int(np.clip(center + r2 * np.cos(a2), 3, self.size - 3))
            cy2 = int(np.clip(center + r2 * np.sin(a2), 3, self.size - 3))
            
            self.inject_vortex(cx1, cy1, center, +1)
            self.inject_vortex(cx2, cy2, center, -1)
    
    def attempt_creation(self):
        high_tau = self.tau > self.tau_creation_threshold
        if not np.any(high_tau):
            return 0
        
        candidates = np.where(high_tau)
        n = len(candidates[0])
        if n == 0:
            return 0
        
        indices = np.random.choice(n, min(25, n), replace=False)
        
        for idx in indices:
            local_tau = self.tau[candidates[0][idx], candidates[1][idx], candidates[2][idx]]
            prob = (local_tau - self.tau_creation_threshold) * self.creation_rate
            
            if np.random.random() < prob:
                center = self.size // 2
                angle = np.random.uniform(0, 2*np.pi)
                r = np.random.uniform(2, self.size * 0.16)
                cx = int(np.clip(center + r * np.cos(angle), 3, self.size - 3))
                cy = int(np.clip(center + r * np.sin(angle), 3, self.size - 3))
                
                a2 = np.random.uniform(0, 2*np.pi)
                d = np.random.uniform(2, 4)
                cx2 = int(np.clip(cx + d * np.cos(a2), 2, self.size - 2))
                cy2 = int(np.clip(cy + d * np.sin(a2), 2, self.size - 2))
                
                self.inject_vortex(cx, cy, center, +1)
                self.inject_vortex(cx2, cy2, center, -1)
                self.creations += 1
                return 1
        return 0
    
    def step(self):
        self.step_count += 1
        self.T += self.dt
        
        self.attempt_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        self.total_damped += float(np.sum(damped_energy))
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
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
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel = np.clip(self.channel + 0.01 * (topology_norm - self.channel), 0, 1)
        
        protection = topology_norm * self.channel
        radial_r, radial_i = self.psi_r / amp, self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        total_energy = float(np.mean(energy))
        if np.isnan(total_energy) or total_energy > 1000:
            self.explosion = True
        
        return total_energy
    
    def detect_defects(self):
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < 0.4)
        return sum(1 for i in range(1, n + 1) if np.sum(labeled == i) >= 3)
    
    def get_snapshot(self):
        tau_mean = float(np.mean(self.tau))
        tau_max = float(np.max(self.tau))
        
        return {
            'T': self.T,
            'defects': self.detect_defects(),
            'creations': self.creations,
            'tau_mean': tau_mean,
            'tau_max': tau_max,
            'tau_std': float(np.std(self.tau)),
            'tau_localization_index': tau_max / tau_mean if tau_mean > 0 else 0,
            'energy_total': float(np.mean(self.psi_r**2 + self.psi_i**2)),
            'total_damped': self.total_damped,
            'total_recycled': self.total_recycled,
            'explosion': self.explosion
        }


def run_endurance_test(seed: int, T_max: float = 1000) -> Dict:
    """Run single T=1000 endurance test."""
    np.random.seed(seed)
    
    sim = EnduranceSimulator(
        size=32, dt=0.12,
        damping_to_tau=OPTIMAL_DAMPING_TO_TAU,
        tau_cap=REGULATED_RECOVERY_TAU_CAP
    )
    sim.psi_r += 0.03 * np.random.randn(32, 32, 32)
    sim.psi_i += 0.03 * np.random.randn(32, 32, 32)
    sim.seed_structure(8)
    
    checkpoints = [200, 500, 750, 1000]
    results = {}
    cp_idx = 0
    
    while sim.T < T_max + sim.dt and not sim.explosion:
        sim.step()
        
        while cp_idx < len(checkpoints) and sim.T >= checkpoints[cp_idx]:
            results[checkpoints[cp_idx]] = sim.get_snapshot()
            cp_idx += 1
    
    return results


def analyze_trend(results: Dict) -> str:
    """Analyze N_defects trend over time."""
    if 500 not in results or 1000 not in results:
        return "incomplete"
    
    n_500 = results[500].get('defects', 0)
    n_1000 = results[1000].get('defects', 0)
    
    if n_500 == 0:
        return "extinct_early"
    
    ratio = n_1000 / n_500
    
    if ratio > 1.2:
        return "GROWING"
    elif ratio > 0.8:
        return "STABLE"
    elif ratio > 0.3:
        return "DECLINING"
    else:
        return "COLLAPSED"


def main():
    print("=" * 80)
    print("  T=1000 ENDURANCE TEST: REGULATED RECOVERY v1.1")
    print("=" * 80)
    print()
    print(f"Configuration:")
    print(f"  damping_to_tau = {OPTIMAL_DAMPING_TO_TAU}")
    print(f"  tau_cap = {REGULATED_RECOVERY_TAU_CAP}")
    print(f"  grid = 32, dt = 0.12, T_max = 1000")
    print()
    
    seeds = [10, 42, 99, 123, 456]
    all_results = []
    
    start_time = time.time()
    
    for seed in seeds:
        print(f"Running seed {seed}...", end=" ", flush=True)
        t0 = time.time()
        
        result = run_endurance_test(seed, T_max=1000)
        all_results.append({'seed': seed, 'data': result})
        
        if 1000 in result:
            d = result[1000]
            trend = analyze_trend(result)
            print(f"N={d['defects']}, tau_loc={d['tau_localization_index']:.3f}, trend={trend} ({time.time()-t0:.1f}s)")
        else:
            print(f"DID NOT COMPLETE ({time.time()-t0:.1f}s)")
    
    elapsed = time.time() - start_time
    print()
    print(f"Total time: {elapsed:.1f}s")
    print()
    
    # Analysis
    print("=" * 80)
    print("  RESULTS BY CHECKPOINT")
    print("=" * 80)
    print()
    
    checkpoints = [200, 500, 750, 1000]
    
    print(f"{'Checkpoint':>10} | {'N_mean':>8} | {'N_std':>7} | {'tau_loc':>8} | {'Trend':>10}")
    print("-" * 60)
    
    for T in checkpoints:
        n_vals = []
        tau_loc_vals = []
        
        for r in all_results:
            if T in r['data']:
                d = r['data'][T]
                if not d.get('explosion', False):
                    n_vals.append(d['defects'])
                    tau_loc_vals.append(d['tau_localization_index'])
        
        if n_vals:
            n_mean = np.mean(n_vals)
            n_std = np.std(n_vals)
            tau_loc_mean = np.mean(tau_loc_vals)
            
            # Trend from T=500 to current
            if T > 500:
                n_500_vals = [r['data'][500]['defects'] for r in all_results 
                             if 500 in r['data'] and not r['data'][500].get('explosion', False)]
                if n_500_vals:
                    ratio = n_mean / np.mean(n_500_vals)
                    if ratio > 1.1:
                        trend = "↑"
                    elif ratio > 0.9:
                        trend = "→"
                    else:
                        trend = "↓"
                else:
                    trend = "?"
            else:
                trend = "-"
            
            print(f"{T:>10} | {n_mean:>8.1f} | {n_std:>7.1f} | {tau_loc_mean:>8.3f} | {trend:>10}")
    
    print()
    
    # Individual seed trends
    print("=" * 80)
    print("  INDIVIDUAL SEED TRENDS (T=500 → T=1000)")
    print("=" * 80)
    print()
    
    trends = []
    extinctions = 0
    collapses = 0
    
    for r in all_results:
        seed = r['seed']
        data = r['data']
        
        if 500 in data and 1000 in data:
            n_500 = data[500]['defects']
            n_1000 = data[1000]['defects']
            tau_loc_1000 = data[1000]['tau_localization_index']
            
            trend = analyze_trend(data)
            trends.append(trend)
            
            if n_1000 == 0:
                extinctions += 1
            if trend == "COLLAPSED":
                collapses += 1
            
            print(f"  Seed {seed}: N={n_500}→{n_1000}, tau_loc={tau_loc_1000:.3f}, trend={trend}")
        else:
            print(f"  Seed {seed}: INCOMPLETE")
    
    print()
    
    # Decision
    print("=" * 80)
    print("  DECISION")
    print("=" * 80)
    print()
    
    # Get T=1000 stats
    n_1000_vals = [r['data'][1000]['defects'] for r in all_results 
                  if 1000 in r['data'] and not r['data'][1000].get('explosion', False)]
    tau_loc_1000_vals = [r['data'][1000]['tau_localization_index'] for r in all_results 
                        if 1000 in r['data'] and not r['data'][1000].get('explosion', False)]
    
    if n_1000_vals:
        n_mean = np.mean(n_1000_vals)
        n_std = np.std(n_1000_vals)
        tau_loc_mean = np.mean(tau_loc_1000_vals)
        
        stable_or_growing = sum(1 for t in trends if t in ['STABLE', 'GROWING'])
        
        print(f"At T=1000:")
        print(f"  N_mean = {n_mean:.1f} ± {n_std:.1f}")
        print(f"  tau_localization = {tau_loc_mean:.3f}")
        print(f"  Trend distribution: {trends}")
        print(f"  Stable/Growing: {stable_or_growing}/{len(trends)}")
        print(f"  Extinctions: {extinctions}")
        print(f"  Collapses: {collapses}")
        print()
        
        if stable_or_growing >= 3 and tau_loc_mean < 2.0:
            print("✓ LOCK Regulated Recovery v1.1 as PRIMARY VALIDATED RECOVERY MODE")
            print("  N remains stable, tau_localization bounded")
        elif n_mean > 20 and collapses == 0:
            print("? v1.1 is VALID but shows decline")
            print("  Consider Channel release → τ for long-horizon support")
        elif collapses >= 2:
            print("✗ d=0.20 shows COLLAPSE pattern")
            print("  Fall back to d=0.15, cap=1.8")
        elif tau_loc_mean > 2.0:
            print("⚠ tau_localization rising above safe threshold")
            print("  Test tau_cap=1.6 or add τ diffusion")
        else:
            print("? INCONCLUSIVE — need more analysis")
    
    # Save results
    output = {
        'test': 'T1000_endurance_v1.1',
        'date': 'December 2025',
        'configuration': {
            'damping_to_tau': OPTIMAL_DAMPING_TO_TAU,
            'tau_cap': REGULATED_RECOVERY_TAU_CAP,
            'grid': 32,
            'dt': 0.12,
            'T_max': 1000
        },
        'results': all_results,
        'summary': {
            'n_mean_T1000': float(np.mean(n_1000_vals)) if n_1000_vals else None,
            'n_std_T1000': float(np.std(n_1000_vals)) if n_1000_vals else None,
            'tau_loc_T1000': float(np.mean(tau_loc_1000_vals)) if tau_loc_1000_vals else None,
            'trends': trends
        }
    }
    
    with open('/app/backend/qmrt_topology/papers/T1000_endurance_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/T1000_endurance_results.json")


if __name__ == "__main__":
    main()
