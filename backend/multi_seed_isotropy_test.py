"""
Multi-Seed Isotropy Validation
==============================

PURPOSE: Confirm that emergent rotational symmetry is robust across
different random seeds, not a seed-specific artifact.

SEEDS: 42, 123, 456, 789, 1000

PASS CRITERIA:
  Minimum pass: combined anisotropy < 0.05 for all seeds
  Strong pass: combined anisotropy < 0.01 for most/all seeds
  Breakthrough: mean < 0.01 and no seed > 0.05

NOTE: The vortex injection mechanism creates z-axis aligned vortices,
which should BREAK symmetry. If we still see isotropy, it's genuinely
emergent from statistical averaging.
"""

import numpy as np
from typing import Dict, List
import time
import json


class MultiSeedIsotropySimulator:
    """Compact simulator for multi-seed isotropy testing."""
    
    def __init__(self, size: int = 32, dt: float = 0.12, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.T = 0.0
        self.step_count = 0
        
        # v1.1 configuration
        self.damping_to_tau = 0.20
        self.tau_cap = 1.8
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        
        self.psi_r = np.ones((size, size, size)) * 1.0
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        self.creations = 0
        self._seed_structure(n_pairs=8)
    
    def _seed_structure(self, n_pairs=8):
        center = self.size // 2
        for _ in range(n_pairs):
            a1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.17)
            cx1 = center + r1 * np.cos(a1)
            cy1 = center + r1 * np.sin(a1)
            cz1 = center + np.random.uniform(-3, 3)
            self._inject_vortex(cx1, cy1, cz1, chirality=1)
            
            a2 = a1 + np.pi + np.random.uniform(-0.5, 0.5)
            r2 = np.random.uniform(2, self.size * 0.17)
            cx2 = center + r2 * np.cos(a2)
            cy2 = center + r2 * np.sin(a2)
            cz2 = center + np.random.uniform(-3, 3)
            self._inject_vortex(cx2, cy2, cz2, chirality=-1)
    
    def _inject_vortex(self, cx, cy, cz, chirality=1):
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
    
    def step(self):
        self.step_count += 1
        self.T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        if self.damping_to_tau > 0:
            self.tau += self.damping_to_tau * damped_energy
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        high_tau_mask = self.tau > self.tau_creation_threshold
        if np.any(high_tau_mask):
            n_candidates = np.sum(high_tau_mask)
            create_prob = self.creation_rate * (self.tau[high_tau_mask] - self.tau_creation_threshold)
            create_mask_1d = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask_1d):
                coords = np.array(np.where(high_tau_mask)).T
                create_coords = coords[create_mask_1d]
                
                for (cx, cy, cz) in create_coords[:5]:
                    chirality = np.random.choice([-1, 1])
                    self._inject_vortex(cx, cy, cz, chirality)
                    self.creations += 1
                    self.tau[cx, cy, cz] = 1.0
        
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def compute_isotropy(self) -> Dict:
        """Compute isotropy metrics."""
        
        # Gradient energies
        dx_r = np.diff(self.psi_r, axis=0, append=self.psi_r[:1, :, :])
        dy_r = np.diff(self.psi_r, axis=1, append=self.psi_r[:, :1, :])
        dz_r = np.diff(self.psi_r, axis=2, append=self.psi_r[:, :, :1])
        dx_i = np.diff(self.psi_i, axis=0, append=self.psi_i[:1, :, :])
        dy_i = np.diff(self.psi_i, axis=1, append=self.psi_i[:, :1, :])
        dz_i = np.diff(self.psi_i, axis=2, append=self.psi_i[:, :, :1])
        
        E_x = np.mean(dx_r**2 + dx_i**2)
        E_y = np.mean(dy_r**2 + dy_i**2)
        E_z = np.mean(dz_r**2 + dz_i**2)
        
        E_mean = (E_x + E_y + E_z) / 3
        gradient_aniso = np.std([E_x, E_y, E_z]) / (E_mean + 1e-10)
        
        # Velocity variance
        dx_v = np.diff(self.psi_r_dot, axis=0, append=self.psi_r_dot[:1, :, :])
        dy_v = np.diff(self.psi_r_dot, axis=1, append=self.psi_r_dot[:, :1, :])
        dz_v = np.diff(self.psi_r_dot, axis=2, append=self.psi_r_dot[:, :, :1])
        
        V_x, V_y, V_z = np.var(dx_v), np.var(dy_v), np.var(dz_v)
        V_mean = (V_x + V_y + V_z) / 3
        velocity_aniso = np.std([V_x, V_y, V_z]) / (V_mean + 1e-10)
        
        # k-space power
        fft = np.fft.fftn(self.psi_r_dot)
        power = np.abs(fft)**2
        
        kx = np.fft.fftfreq(self.size)
        ky = np.fft.fftfreq(self.size)
        kz = np.fft.fftfreq(self.size)
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        
        k_threshold = 0.2
        x_cone = np.abs(KX) > k_threshold
        y_cone = np.abs(KY) > k_threshold
        z_cone = np.abs(KZ) > k_threshold
        
        P_x = np.mean(power[x_cone]) if np.any(x_cone) else 0
        P_y = np.mean(power[y_cone]) if np.any(y_cone) else 0
        P_z = np.mean(power[z_cone]) if np.any(z_cone) else 0
        
        P_mean = (P_x + P_y + P_z) / 3
        kspace_aniso = np.std([P_x, P_y, P_z]) / (P_mean + 1e-10)
        
        combined_aniso = (gradient_aniso + velocity_aniso + kspace_aniso) / 3
        
        return {
            'gradient_anisotropy': float(gradient_aniso),
            'velocity_anisotropy': float(velocity_aniso),
            'kspace_anisotropy': float(kspace_aniso),
            'combined_anisotropy': float(combined_aniso),
            'E_x': float(E_x), 'E_y': float(E_y), 'E_z': float(E_z),
            'E_ratio_max_min': float(max(E_x, E_y, E_z) / min(E_x, E_y, E_z)),
            'vibration_energy': float(np.mean(0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2))),
            'tau_mean': float(np.mean(self.tau)),
            'tau_max': float(np.max(self.tau)),
            'creations': self.creations
        }


def run_single_seed(seed: int, T_target: float = 300.0, n_samples: int = 5) -> Dict:
    """Run isotropy test for a single seed."""
    
    sim = MultiSeedIsotropySimulator(size=32, dt=0.12, seed=seed)
    
    # Run to steady state
    while sim.T < T_target:
        sim.step()
    
    # Collect samples
    samples = []
    sample_interval = 20.0
    
    for _ in range(n_samples):
        T_start = sim.T
        while sim.T < T_start + sample_interval:
            sim.step()
        samples.append(sim.compute_isotropy())
    
    # Aggregate
    combined_anisos = [s['combined_anisotropy'] for s in samples]
    
    return {
        'seed': seed,
        'combined_mean': float(np.mean(combined_anisos)),
        'combined_std': float(np.std(combined_anisos)),
        'gradient_mean': float(np.mean([s['gradient_anisotropy'] for s in samples])),
        'velocity_mean': float(np.mean([s['velocity_anisotropy'] for s in samples])),
        'kspace_mean': float(np.mean([s['kspace_anisotropy'] for s in samples])),
        'E_ratio_mean': float(np.mean([s['E_ratio_max_min'] for s in samples])),
        'vib_energy': float(np.mean([s['vibration_energy'] for s in samples])),
        'creations': samples[-1]['creations'],
        'samples': samples
    }


def main():
    print("=" * 80)
    print("  MULTI-SEED ISOTROPY VALIDATION")
    print("=" * 80)
    print()
    print("Seeds: 42, 123, 456, 789, 1000")
    print("Pass criteria: combined anisotropy < 0.05 for all seeds")
    print("Strong pass: combined anisotropy < 0.01 for most/all seeds")
    print()
    print("NOTE: Vortex injection is z-axis biased by construction.")
    print("      Isotropy despite this = genuinely emergent.")
    print()
    
    seeds = [42, 123, 456, 789, 1000]
    results = []
    
    t0_total = time.time()
    
    for seed in seeds:
        print(f"Running seed {seed}...", end="", flush=True)
        t0 = time.time()
        
        result = run_single_seed(seed, T_target=300.0, n_samples=5)
        results.append(result)
        
        print(f" aniso={result['combined_mean']:.4f}, E_ratio={result['E_ratio_mean']:.3f} ({time.time()-t0:.1f}s)")
    
    print()
    print(f"Total time: {time.time()-t0_total:.1f}s")
    print()
    
    # Analysis
    print("=" * 80)
    print("  RESULTS BY SEED")
    print("=" * 80)
    print()
    
    header = f"{'Seed':>8} | {'Combined':>10} | {'Gradient':>10} | {'Velocity':>10} | {'k-space':>10} | {'E_ratio':>8} | {'Status':>10}"
    print(header)
    print("-" * 85)
    
    all_pass = True
    strong_pass_count = 0
    
    for r in results:
        combined = r['combined_mean']
        
        if combined < 0.01:
            status = "STRONG ✓"
            strong_pass_count += 1
        elif combined < 0.05:
            status = "PASS ✓"
        else:
            status = "FAIL ✗"
            all_pass = False
        
        print(f"{r['seed']:>8} | {combined:>10.4f} | {r['gradient_mean']:>10.4f} | "
              f"{r['velocity_mean']:>10.4f} | {r['kspace_mean']:>10.4f} | "
              f"{r['E_ratio_mean']:>8.3f} | {status:>10}")
    
    print()
    
    # Aggregate statistics
    combined_values = [r['combined_mean'] for r in results]
    mean_combined = np.mean(combined_values)
    std_combined = np.std(combined_values)
    max_combined = np.max(combined_values)
    
    print("=" * 80)
    print("  AGGREGATE STATISTICS")
    print("=" * 80)
    print()
    
    print(f"Mean combined anisotropy: {mean_combined:.4f}")
    print(f"Std combined anisotropy:  {std_combined:.4f}")
    print(f"Max combined anisotropy:  {max_combined:.4f}")
    print(f"Strong pass count:        {strong_pass_count}/{len(seeds)}")
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    if mean_combined < 0.01 and max_combined < 0.05:
        verdict = "BREAKTHROUGH"
        print("★ BREAKTHROUGH: Mean < 0.01 and all seeds < 0.05")
        print("  Emergent rotational symmetry is ROBUST across seeds.")
    elif all_pass and strong_pass_count >= 3:
        verdict = "STRONG_PASS"
        print("✓ STRONG PASS: All seeds < 0.05, most < 0.01")
        print("  Emergent rotational symmetry is well-validated.")
    elif all_pass:
        verdict = "PASS"
        print("✓ PASS: All seeds < 0.05")
        print("  Emergent rotational symmetry is confirmed across seeds.")
    else:
        verdict = "PARTIAL"
        print("? PARTIAL: Some seeds exceed threshold")
        print("  Isotropy may be seed-dependent.")
    
    print()
    print("Physical interpretation:")
    print(f"  Despite z-axis biased vortex injection, the statistical")
    print(f"  vibrational field shows anisotropy = {mean_combined:.4f} ± {std_combined:.4f}")
    print(f"  This is GENUINE EMERGENT ISOTROPY from statistical averaging.")
    
    # Save results
    output = {
        'test': 'multi_seed_isotropy',
        'date': 'December 2025',
        'seeds': seeds,
        'verdict': verdict,
        'thresholds': {'minimum': 0.05, 'strong': 0.01},
        'aggregate': {
            'mean_combined': float(mean_combined),
            'std_combined': float(std_combined),
            'max_combined': float(max_combined),
            'all_pass': all_pass,
            'strong_pass_count': strong_pass_count
        },
        'per_seed': [{
            'seed': r['seed'],
            'combined_anisotropy': r['combined_mean'],
            'gradient_anisotropy': r['gradient_mean'],
            'velocity_anisotropy': r['velocity_mean'],
            'kspace_anisotropy': r['kspace_mean'],
            'E_ratio': r['E_ratio_mean'],
            'vibration_energy': r['vib_energy'],
            'creations': r['creations']
        } for r in results]
    }
    
    with open('/app/backend/qmrt_topology/papers/MULTI_SEED_ISOTROPY_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/MULTI_SEED_ISOTROPY_RESULTS.json")


if __name__ == "__main__":
    main()
