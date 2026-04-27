"""
Tau-Cap Sensitivity Test
==========================

PURPOSE: Determine if Damping → τ results depend on high τ ceiling.

PARAMETERS:
| tau_cap | damping_to_tau | T   | Purpose                        |
|---------|----------------|-----|--------------------------------|
| 2.0     | 0.10           | 500 | tight regulation               |
| 2.5     | 0.10           | 500 | moderate regulation            |
| 3.0     | 0.10           | 500 | current validated baseline     |
| 2.0     | 0.15           | 500 | stronger coupling, tight cap   |
| 2.5     | 0.15           | 500 | stronger coupling, moderate    |
| 3.0     | 0.15           | 500 | current high-performing case   |

DECISION RULE:
- If tau_cap=2.0 beats baseline: Damping → τ is robust
- If only tau_cap=3.0 works: requires high τ headroom
- If tau_cap=2.0 ≈ 3.0: use 2.0 as safer default

OPTIMIZATIONS:
- Grid size: 32 (vs 36) for ~40% speedup
- dt: 0.12 (vs 0.10) for ~20% speedup
- Combined: ~2x faster simulation-time per wall-clock
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List
import time
import json


class TauCapSimulator:
    """Optimized simulator for tau-cap sensitivity testing."""
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = 0.0,
                 tau_cap: float = 3.0):
        
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
        
        # Simple coupling field (no smooth transition for speed)
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
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
        step_damped = float(np.sum(damped_energy))
        self.total_damped += step_damped
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # Damping → τ coupling
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
        
        # Simplified topology (no gaussian_filter for speed)
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
        return {
            'T': self.T,
            'defects': self.detect_defects(),
            'creations': self.creations,
            'tau_mean': float(np.mean(self.tau)),
            'tau_max': float(np.max(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'energy_total': float(np.mean(self.psi_r**2 + self.psi_i**2)),
            'total_damped': self.total_damped,
            'total_recycled': self.total_recycled,
            'explosion': self.explosion
        }


def run_single_config(tau_cap: float, damping_to_tau: float, seed: int, 
                      T_max: float = 500) -> Dict:
    """Run single configuration to T=500."""
    np.random.seed(seed)
    
    sim = TauCapSimulator(
        size=32, dt=0.12,
        damping_to_tau=damping_to_tau,
        tau_cap=tau_cap
    )
    sim.psi_r += 0.03 * np.random.randn(32, 32, 32)
    sim.psi_i += 0.03 * np.random.randn(32, 32, 32)
    sim.seed_structure(8)
    
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
    print("  TAU-CAP SENSITIVITY TEST")
    print("=" * 80)
    print()
    print("Purpose: Does Damping → τ require high τ ceiling?")
    print("Optimizations: grid=32, dt=0.12 (~2x faster)")
    print()
    
    # Test configurations
    configs = [
        (2.0, 0.10, "tight cap, validated coupling"),
        (2.5, 0.10, "moderate cap, validated coupling"),
        (3.0, 0.10, "current baseline"),
        (2.0, 0.15, "tight cap, strong coupling"),
        (2.5, 0.15, "moderate cap, strong coupling"),
        (3.0, 0.15, "current high performer"),
    ]
    
    # Also need baseline (no damping) for comparison
    configs.insert(0, (3.0, 0.00, "no damping baseline"))
    
    seeds = [10, 42]
    
    all_results = {}
    
    start_time = time.time()
    
    for tau_cap, damping, desc in configs:
        key = f"cap{tau_cap}_d{damping}"
        all_results[key] = {'cap': tau_cap, 'damping': damping, 'desc': desc, 'runs': []}
        
        print(f"Testing tau_cap={tau_cap}, damping={damping} ({desc})...", end=" ", flush=True)
        t0 = time.time()
        
        for seed in seeds:
            result = run_single_config(tau_cap, damping, seed, T_max=500)
            all_results[key]['runs'].append(result)
        
        print(f"done ({time.time()-t0:.1f}s)")
    
    elapsed = time.time() - start_time
    print()
    print(f"Total time: {elapsed:.1f}s")
    print()
    
    # Results table
    print("=" * 80)
    print("  N_defects at T=500 by Tau-Cap Configuration")
    print("=" * 80)
    print()
    
    print(f"{'Config':>20} | {'tau_cap':>7} | {'damping':>7} | {'N_500':>8} | {'tau_mean':>9} | {'tau_max':>9}")
    print("-" * 75)
    
    baseline_n = None
    
    for key, data in all_results.items():
        runs = data['runs']
        t500_data = [r.get(500, {}) for r in runs if 500 in r]
        valid = [d for d in t500_data if not d.get('explosion', False)]
        
        if valid:
            n_mean = np.mean([d['defects'] for d in valid])
            tau_mean = np.mean([d['tau_mean'] for d in valid])
            tau_max = np.mean([d['tau_max'] for d in valid])
            
            if data['damping'] == 0.00:
                baseline_n = n_mean
            
            print(f"{data['desc'][:20]:>20} | {data['cap']:>7.1f} | {data['damping']:>7.2f} | "
                  f"{n_mean:>8.1f} | {tau_mean:>9.4f} | {tau_max:>9.4f}")
        else:
            print(f"{data['desc'][:20]:>20} | {data['cap']:>7.1f} | {data['damping']:>7.2f} | "
                  f"{'EXPLODE':>8} | {'N/A':>9} | {'N/A':>9}")
    
    print()
    
    # Analysis
    print("=" * 80)
    print("  ANALYSIS: Improvement vs Baseline")
    print("=" * 80)
    print()
    
    if baseline_n and baseline_n > 0:
        print(f"Baseline (no damping): N = {baseline_n:.1f}")
        print()
        
        for key, data in all_results.items():
            if data['damping'] > 0:
                runs = data['runs']
                t500_data = [r.get(500, {}) for r in runs if 500 in r]
                valid = [d for d in t500_data if not d.get('explosion', False)]
                
                if valid:
                    n_mean = np.mean([d['defects'] for d in valid])
                    improvement = ((n_mean / baseline_n) - 1) * 100
                    
                    status = "✓" if improvement > 20 else "≈" if improvement > -20 else "✗"
                    print(f"  tau_cap={data['cap']}, damping={data['damping']}: "
                          f"N={n_mean:.1f} ({improvement:+.0f}%) {status}")
    
    print()
    
    # Decision
    print("=" * 80)
    print("  DECISION")
    print("=" * 80)
    print()
    
    # Check if low cap works
    cap2_results = {k: v for k, v in all_results.items() if v['cap'] == 2.0 and v['damping'] > 0}
    cap3_results = {k: v for k, v in all_results.items() if v['cap'] == 3.0 and v['damping'] > 0}
    
    cap2_works = False
    cap3_works = False
    
    for key, data in cap2_results.items():
        runs = data['runs']
        t500_data = [r.get(500, {}) for r in runs if 500 in r]
        valid = [d for d in t500_data if not d.get('explosion', False)]
        if valid and baseline_n:
            n_mean = np.mean([d['defects'] for d in valid])
            if n_mean > baseline_n * 1.2:
                cap2_works = True
    
    for key, data in cap3_results.items():
        runs = data['runs']
        t500_data = [r.get(500, {}) for r in runs if 500 in r]
        valid = [d for d in t500_data if not d.get('explosion', False)]
        if valid and baseline_n:
            n_mean = np.mean([d['defects'] for d in valid])
            if n_mean > baseline_n * 1.2:
                cap3_works = True
    
    if cap2_works and cap3_works:
        print("✓ Damping → τ is ROBUST to tau-cap reduction")
        print("  Both tau_cap=2.0 and 3.0 beat baseline")
        print("  → tau_cap=2.0 can be used as safer default")
    elif cap3_works and not cap2_works:
        print("⚠ Damping → τ requires high τ headroom")
        print("  Only tau_cap=3.0 beats baseline")
        print("  → Keep tau_cap=3.0 for now")
    elif not cap3_works:
        print("✗ Unexpected: even tau_cap=3.0 doesn't beat baseline")
        print("  → Check test configuration")
    
    # Save results
    output = {
        'test': 'tau_cap_sensitivity',
        'parameters': {'grid': 32, 'dt': 0.12, 'T_max': 500, 'seeds': 2},
        'results': all_results
    }
    
    with open('/app/backend/qmrt_topology/papers/tau_cap_sensitivity_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/tau_cap_sensitivity_results.json")


if __name__ == "__main__":
    main()
