"""
5-Seed Confirmation Test: Regulated Damping → τ Recovery Loop
==============================================================

PURPOSE: Confirm the validated optimal configuration with proper statistics.

CONFIGURATION:
  tau_cap = 2.0 (REGULATED_RECOVERY mode)
  damping_to_tau = 0.15 (optimal)
  grid = 36 (physics accuracy, not reduced)
  dt = 0.12 (accelerated but stable)
  max_T = 500
  n_seeds = 5

BASELINE:
  tau_cap = 2.0
  damping_to_tau = 0.00
  (Same regulated τ conditions for fair comparison)

KEY INSIGHT:
  "Damping-to-τ recycling is constructive only when τ is bounded tightly enough
   to prevent localized over-recharge; under regulated τ, dissipated energy
   becomes a distributed creation resource rather than a hot-spot instability."

NEW METRIC:
  tau_localization_index = tau_max / tau_mean
  (Lower is better - indicates distributed τ vs localized hot spots)

DECISION RULE:
  Prefer configuration with high N_defects, low seed variance, and low
  tau_localization_index — not necessarily the highest N.
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List
import time
import json


# Configuration constants
DEFAULT_TAU_CAP = 3.0
REGULATED_RECOVERY_TAU_CAP = 2.0


class RegulatedRecoverySimulator:
    """
    Simulator with regulated τ for recovery-loop testing.
    
    Key difference from default simulator:
    - tau_cap = 2.0 (regulated recovery mode)
    - Tracks tau_localization_index
    """
    
    def __init__(self, size: int = 36, dt: float = 0.12,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = 0.0,
                 tau_cap: float = REGULATED_RECOVERY_TAU_CAP):
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        
        self.T = 0.0
        self.step_count = 0
        
        # Fields
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
        
        # Coupling field with smooth transition
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = size * 0.25
        
        self.coupling = np.zeros((size, size, size))
        self.coupling[r <= interior_r] = 0.7
        self.coupling[r >= interior_r + 8.0] = 0.2
        mask_t = (r > interior_r) & (r < interior_r + 8.0)
        if np.any(mask_t):
            t = (r[mask_t] - interior_r) / 8.0
            self.coupling[mask_t] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
        # Tracking
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
    
    def seed_structure(self, n_pairs=10):
        center = self.size // 2
        for _ in range(n_pairs):
            a1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.17)
            cx1 = int(np.clip(center + r1 * np.cos(a1), 4, self.size - 4))
            cy1 = int(np.clip(center + r1 * np.sin(a1), 4, self.size - 4))
            
            a2 = a1 + np.random.uniform(0.5, 1.5)
            r2 = np.random.uniform(2, self.size * 0.17)
            cx2 = int(np.clip(center + r2 * np.cos(a2), 4, self.size - 4))
            cy2 = int(np.clip(center + r2 * np.sin(a2), 4, self.size - 4))
            
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
        
        indices = np.random.choice(n, min(30, n), replace=False)
        
        for idx in indices:
            local_tau = self.tau[candidates[0][idx], candidates[1][idx], candidates[2][idx]]
            prob = (local_tau - self.tau_creation_threshold) * self.creation_rate
            
            if np.random.random() < prob:
                center = self.size // 2
                angle = np.random.uniform(0, 2*np.pi)
                r = np.random.uniform(2, self.size * 0.17)
                cx = int(np.clip(center + r * np.cos(angle), 4, self.size - 4))
                cy = int(np.clip(center + r * np.sin(angle), 4, self.size - 4))
                
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
        step_damped = float(np.sum(damped_energy))
        self.total_damped += step_damped
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # Damping → τ coupling (REGULATED)
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        # REGULATED τ cap - this is part of the physics
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
        
        # Safety
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
        tau_localization_index = tau_max / tau_mean if tau_mean > 0 else 0
        
        return {
            'T': self.T,
            'defects': self.detect_defects(),
            'creations': self.creations,
            'tau_mean': tau_mean,
            'tau_max': tau_max,
            'tau_std': float(np.std(self.tau)),
            'tau_localization_index': tau_localization_index,
            'energy_total': float(np.mean(self.psi_r**2 + self.psi_i**2)),
            'total_damped': self.total_damped,
            'total_recycled': self.total_recycled,
            'explosion': self.explosion
        }


def run_single_seed(damping_to_tau: float, seed: int, T_max: float = 500) -> Dict:
    """Run single seed to T_max."""
    np.random.seed(seed)
    
    sim = RegulatedRecoverySimulator(
        size=36, dt=0.12,
        damping_to_tau=damping_to_tau,
        tau_cap=REGULATED_RECOVERY_TAU_CAP
    )
    sim.psi_r += 0.03 * np.random.randn(36, 36, 36)
    sim.psi_i += 0.03 * np.random.randn(36, 36, 36)
    sim.seed_structure(10)
    
    checkpoints = [100, 200, 500]
    results = {}
    cp_idx = 0
    
    while sim.T < T_max + sim.dt and not sim.explosion:
        sim.step()
        
        while cp_idx < len(checkpoints) and sim.T >= checkpoints[cp_idx]:
            results[checkpoints[cp_idx]] = sim.get_snapshot()
            cp_idx += 1
    
    return results


def main():
    print("=" * 80)
    print("  5-SEED CONFIRMATION: REGULATED DAMPING → τ RECOVERY LOOP")
    print("=" * 80)
    print()
    print("Configuration:")
    print(f"  tau_cap = {REGULATED_RECOVERY_TAU_CAP} (REGULATED_RECOVERY mode)")
    print("  grid = 36, dt = 0.12, T_max = 500")
    print()
    print("Key insight:")
    print("  'Damping-to-τ recycling is constructive only when τ is bounded")
    print("   tightly enough to prevent localized over-recharge.'")
    print()
    
    seeds = [10, 42, 99, 123, 456]
    configs = [
        (0.00, "baseline (regulated τ, no damping)"),
        (0.15, "optimal (regulated τ + damping)"),
    ]
    
    all_results = {}
    
    start_time = time.time()
    
    for damping, desc in configs:
        key = f"d{damping:.2f}"
        all_results[key] = {'damping': damping, 'desc': desc, 'runs': []}
        
        print(f"Testing {desc}...")
        
        for i, seed in enumerate(seeds):
            t0 = time.time()
            result = run_single_seed(damping, seed, T_max=500)
            all_results[key]['runs'].append(result)
            
            if 500 in result:
                d = result[500]
                print(f"  Seed {seed}: N={d['defects']}, tau_loc={d['tau_localization_index']:.3f} ({time.time()-t0:.1f}s)")
            else:
                print(f"  Seed {seed}: DID NOT REACH T=500")
        
        print()
    
    elapsed = time.time() - start_time
    print(f"Total time: {elapsed:.1f}s")
    print()
    
    # Analysis
    print("=" * 80)
    print("  RESULTS AT T=500")
    print("=" * 80)
    print()
    
    for key, data in all_results.items():
        t500_data = [r.get(500, {}) for r in data['runs'] if 500 in r]
        valid = [d for d in t500_data if not d.get('explosion', False)]
        
        if valid:
            n_vals = [d['defects'] for d in valid]
            tau_loc_vals = [d['tau_localization_index'] for d in valid]
            
            n_mean = np.mean(n_vals)
            n_std = np.std(n_vals)
            tau_loc_mean = np.mean(tau_loc_vals)
            
            print(f"{data['desc']}:")
            print(f"  N_defects:  mean={n_mean:.1f}, std={n_std:.1f}, range=[{min(n_vals)}, {max(n_vals)}]")
            print(f"  tau_loc:    mean={tau_loc_mean:.3f}")
            print(f"  Seeds:      {len(valid)}/{len(seeds)} completed")
            print()
    
    # Statistical comparison
    print("=" * 80)
    print("  STATISTICAL COMPARISON")
    print("=" * 80)
    print()
    
    baseline_data = all_results.get('d0.00', {}).get('runs', [])
    optimal_data = all_results.get('d0.15', {}).get('runs', [])
    
    baseline_n = [r.get(500, {}).get('defects', 0) for r in baseline_data if 500 in r]
    optimal_n = [r.get(500, {}).get('defects', 0) for r in optimal_data if 500 in r]
    
    if baseline_n and optimal_n:
        baseline_mean = np.mean(baseline_n)
        optimal_mean = np.mean(optimal_n)
        
        improvement = ((optimal_mean / baseline_mean) - 1) * 100 if baseline_mean > 0 else 0
        
        print(f"Baseline (d=0.00): mean N = {baseline_mean:.1f}")
        print(f"Optimal (d=0.15):  mean N = {optimal_mean:.1f}")
        print(f"Improvement: {improvement:+.0f}%")
        print()
        
        if improvement > 50:
            print("✓ CONFIRMED: Regulated damping → τ coupling significantly improves")
            print("  recovery-loop sustainability under bounded τ conditions.")
        elif improvement > 0:
            print("? MARGINAL: Some improvement, but more seeds needed for confidence.")
        else:
            print("✗ UNEXPECTED: No improvement observed. Check configuration.")
    
    # Save results
    output = {
        'test': '5_seed_confirmation_regulated_recovery',
        'theoretical_statement': (
            "Damping-to-τ recycling is constructive only when τ is bounded "
            "tightly enough to prevent localized over-recharge; under regulated τ, "
            "dissipated energy becomes a distributed creation resource rather "
            "than a hot-spot instability."
        ),
        'parameters': {
            'tau_cap': REGULATED_RECOVERY_TAU_CAP,
            'grid': 36,
            'dt': 0.12,
            'T_max': 500,
            'n_seeds': len(seeds)
        },
        'results': all_results
    }
    
    with open('/app/backend/qmrt_topology/papers/5_seed_confirmation_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/5_seed_confirmation_results.json")


if __name__ == "__main__":
    main()
