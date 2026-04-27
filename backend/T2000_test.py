"""
T=2000 Ultra-Long-Horizon Test: Regulated Recovery v1.1
========================================================

PURPOSE: Confirm v1.1 maintains stability over T=2000 (4× initial validation window).

LOCKED CONFIGURATION (v1.1):
  damping_to_tau = 0.20
  tau_cap = 1.8
  grid = 32
  dt = 0.12

KEY NEW METRIC:
  late_N_slope = (N_T2000 - N_T1000) / (2000 - 1000)
  
DECISION RULES:
  - late_N_slope positive or ~0: v1.1 is long-horizon stable
  - late_N_slope mildly negative but N high: sustained but saturating
  - late_N_slope strongly negative: investigate delayed depletion

THEORETICAL STATEMENT:
  "The system benefits from recycling energy where topology is actively
   doing work, not from being guided back to where topology died."
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List
import time
import json


# Locked v1.1 Configuration
REGULATED_RECOVERY_TAU_CAP = 1.8
OPTIMAL_DAMPING_TO_TAU = 0.20


class UltraLongHorizonSimulator:
    """Simulator for T=2000 ultra-long-horizon testing."""
    
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
            'total_damped': self.total_damped,
            'total_recycled': self.total_recycled,
            'explosion': self.explosion
        }


def run_T2000_test(seed: int) -> Dict:
    """Run single T=2000 test."""
    np.random.seed(seed)
    
    sim = UltraLongHorizonSimulator(
        size=32, dt=0.12,
        damping_to_tau=OPTIMAL_DAMPING_TO_TAU,
        tau_cap=REGULATED_RECOVERY_TAU_CAP
    )
    sim.psi_r += 0.03 * np.random.randn(32, 32, 32)
    sim.psi_i += 0.03 * np.random.randn(32, 32, 32)
    sim.seed_structure(8)
    
    checkpoints = [500, 1000, 1500, 2000]
    results = {}
    cp_idx = 0
    
    while sim.T < 2000 + sim.dt and not sim.explosion:
        sim.step()
        
        while cp_idx < len(checkpoints) and sim.T >= checkpoints[cp_idx]:
            results[checkpoints[cp_idx]] = sim.get_snapshot()
            cp_idx += 1
    
    return results


def compute_late_slope(results: Dict) -> float:
    """Compute late_N_slope from T=1000 to T=2000."""
    if 1000 not in results or 2000 not in results:
        return None
    
    n_1000 = results[1000]['defects']
    n_2000 = results[2000]['defects']
    
    return (n_2000 - n_1000) / 1000.0


def main():
    print("=" * 80)
    print("  T=2000 ULTRA-LONG-HORIZON TEST: REGULATED RECOVERY v1.1")
    print("=" * 80)
    print()
    print(f"Locked configuration:")
    print(f"  damping_to_tau = {OPTIMAL_DAMPING_TO_TAU}")
    print(f"  tau_cap = {REGULATED_RECOVERY_TAU_CAP}")
    print()
    
    seeds = [10, 42, 99]
    all_results = []
    
    start_time = time.time()
    
    for seed in seeds:
        print(f"Running seed {seed}...", end=" ", flush=True)
        t0 = time.time()
        
        result = run_T2000_test(seed)
        all_results.append({'seed': seed, 'data': result})
        
        if 2000 in result:
            d = result[2000]
            slope = compute_late_slope(result)
            n_1000 = result[1000]['defects'] if 1000 in result else '?'
            n_2000 = d['defects']
            print(f"N: {n_1000}→{n_2000}, slope={slope:.4f}, tau_loc={d['tau_localization_index']:.3f} ({time.time()-t0:.0f}s)")
        else:
            print("INCOMPLETE")
    
    elapsed = time.time() - start_time
    print()
    print(f"Total time: {elapsed:.1f}s")
    print()
    
    # Analysis
    print("=" * 80)
    print("  RESULTS BY CHECKPOINT")
    print("=" * 80)
    print()
    
    checkpoints = [500, 1000, 1500, 2000]
    
    print(f"{'T':>6} | {'N_mean':>8} | {'N_std':>7} | {'tau_loc':>8}")
    print("-" * 45)
    
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
            print(f"{T:>6} | {np.mean(n_vals):>8.1f} | {np.std(n_vals):>7.1f} | {np.mean(tau_loc_vals):>8.3f}")
    
    print()
    
    # Late slope analysis
    print("=" * 80)
    print("  LATE_N_SLOPE ANALYSIS (T=1000 → T=2000)")
    print("=" * 80)
    print()
    
    slopes = []
    
    for r in all_results:
        seed = r['seed']
        data = r['data']
        
        if 1000 in data and 2000 in data:
            n_1000 = data[1000]['defects']
            n_2000 = data[2000]['defects']
            slope = compute_late_slope(data)
            slopes.append(slope)
            
            if slope > 0.01:
                trend = "GROWING ↑"
            elif slope > -0.01:
                trend = "STABLE →"
            elif slope > -0.05:
                trend = "DECLINING ↓"
            else:
                trend = "DROPPING ↓↓"
            
            print(f"  Seed {seed}: N={n_1000}→{n_2000}, slope={slope:.4f}, {trend}")
    
    print()
    
    if slopes:
        mean_slope = np.mean(slopes)
        print(f"Mean late_N_slope: {mean_slope:.4f}")
        print()
        
        # Decision
        print("=" * 80)
        print("  DECISION")
        print("=" * 80)
        print()
        
        if mean_slope > -0.01:
            print("✓ v1.1 IS LONG-HORIZON STABLE")
            print("  late_N_slope is near zero or positive")
            print("  Recovery loop maintains topology through T=2000")
        elif mean_slope > -0.03:
            print("? v1.1 IS SUSTAINED BUT SATURATING")
            print("  late_N_slope is mildly negative")
            print("  N remains high but may be approaching equilibrium")
        else:
            print("⚠ INVESTIGATE DELAYED DEPLETION")
            print("  late_N_slope is strongly negative")
            print("  May need additional support mechanisms")
    
    # Save results
    output = {
        'test': 'T2000_ultra_long_horizon',
        'date': 'December 2025',
        'configuration': {
            'damping_to_tau': OPTIMAL_DAMPING_TO_TAU,
            'tau_cap': REGULATED_RECOVERY_TAU_CAP,
            'grid': 32,
            'dt': 0.12,
            'T_max': 2000
        },
        'results': all_results,
        'late_N_slopes': slopes,
        'mean_late_N_slope': float(np.mean(slopes)) if slopes else None
    }
    
    with open('/app/backend/qmrt_topology/papers/T2000_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/T2000_results.json")


if __name__ == "__main__":
    main()
