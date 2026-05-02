"""
Vibration Field Isotropy Test
==============================

PURPOSE: Determine whether the statistically stationary vibrational phase
is also statistically isotropic.

KEY QUESTION:
  Is the turbulent vibration field the same in all directions?

If yes: The active medium phase has emergent Lorentz-like isotropy.
If no: The medium has directional bias (possibly from initial conditions or lattice).

METRICS:
  - Directional vibration energy (E_x, E_y, E_z)
  - k-space power anisotropy
  - Correlation function isotropy
  - Velocity component variances

A statistically isotropic phase would show:
  - E_x ≈ E_y ≈ E_z
  - Power spectrum spherically symmetric in k-space
  - Correlation functions identical in all directions
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class VibrationIsotropySimulator:
    """Simulator for vibration field isotropy testing."""
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 damping_to_tau: float = 0.20, tau_cap: float = 1.8,
                 seed: int = None):
        
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        
        self.T = 0.0
        self.step_count = 0
        
        self.psi_r = np.ones((size, size, size)) * 1.0
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
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
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
        
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
    
    def compute_isotropy_metrics(self) -> Dict:
        """Compute isotropy metrics for the vibration field."""
        
        # 1. Directional gradient energies
        # These measure how much the field varies in each direction
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
        E_std = np.std([E_x, E_y, E_z])
        gradient_anisotropy = E_std / (E_mean + 1e-10)
        
        # 2. Velocity component variances (for kinetic isotropy)
        # In an isotropic field, variance should be equal in all directions
        # We use velocity gradients as proxy
        dx_v = np.diff(self.psi_r_dot, axis=0, append=self.psi_r_dot[:1, :, :])
        dy_v = np.diff(self.psi_r_dot, axis=1, append=self.psi_r_dot[:, :1, :])
        dz_v = np.diff(self.psi_r_dot, axis=2, append=self.psi_r_dot[:, :, :1])
        
        V_x = np.var(dx_v)
        V_y = np.var(dy_v)
        V_z = np.var(dz_v)
        
        V_mean = (V_x + V_y + V_z) / 3
        V_std = np.std([V_x, V_y, V_z])
        velocity_anisotropy = V_std / (V_mean + 1e-10)
        
        # 3. k-space power anisotropy
        fft = np.fft.fftn(self.psi_r_dot)
        power = np.abs(fft)**2
        
        # Measure power along each axis
        kx = np.fft.fftfreq(self.size)
        ky = np.fft.fftfreq(self.size)
        kz = np.fft.fftfreq(self.size)
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        K = np.sqrt(KX**2 + KY**2 + KZ**2)
        
        # Power in different k-cones
        k_threshold = 0.2
        
        x_cone = np.abs(KX) > k_threshold
        y_cone = np.abs(KY) > k_threshold
        z_cone = np.abs(KZ) > k_threshold
        
        P_x = np.mean(power[x_cone]) if np.any(x_cone) else 0
        P_y = np.mean(power[y_cone]) if np.any(y_cone) else 0
        P_z = np.mean(power[z_cone]) if np.any(z_cone) else 0
        
        P_mean = (P_x + P_y + P_z) / 3
        P_std = np.std([P_x, P_y, P_z])
        kspace_anisotropy = P_std / (P_mean + 1e-10)
        
        # 4. Spatial correlation isotropy
        # Compute 1D correlations along each axis at center
        center = self.size // 2
        
        # Extract 1D slices
        x_slice = self.psi_r_dot[:, center, center]
        y_slice = self.psi_r_dot[center, :, center]
        z_slice = self.psi_r_dot[center, center, :]
        
        # Autocorrelation
        def autocorr(x):
            result = np.correlate(x - np.mean(x), x - np.mean(x), mode='full')
            result = result[len(result)//2:]
            return result / (result[0] + 1e-10)
        
        corr_x = autocorr(x_slice)
        corr_y = autocorr(y_slice)
        corr_z = autocorr(z_slice)
        
        # Correlation length (first zero crossing or half-length)
        def corr_length(c):
            zeros = np.where(c < 0)[0]
            if len(zeros) > 0:
                return zeros[0]
            return len(c) // 2
        
        L_x = corr_length(corr_x)
        L_y = corr_length(corr_y)
        L_z = corr_length(corr_z)
        
        L_mean = (L_x + L_y + L_z) / 3
        L_std = np.std([L_x, L_y, L_z])
        correlation_anisotropy = L_std / (L_mean + 1e-10)
        
        # 5. Combined isotropy index
        combined_anisotropy = (gradient_anisotropy + velocity_anisotropy + 
                               kspace_anisotropy + correlation_anisotropy) / 4
        
        return {
            'T': self.T,
            'gradient_energy': {'x': float(E_x), 'y': float(E_y), 'z': float(E_z)},
            'gradient_anisotropy': float(gradient_anisotropy),
            'velocity_variance': {'x': float(V_x), 'y': float(V_y), 'z': float(V_z)},
            'velocity_anisotropy': float(velocity_anisotropy),
            'kspace_power': {'x': float(P_x), 'y': float(P_y), 'z': float(P_z)},
            'kspace_anisotropy': float(kspace_anisotropy),
            'correlation_length': {'x': int(L_x), 'y': int(L_y), 'z': int(L_z)},
            'correlation_anisotropy': float(correlation_anisotropy),
            'combined_anisotropy': float(combined_anisotropy),
            'vibration_energy': float(np.mean(0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2))),
            'creations': self.creations
        }


def run_isotropy_test(T_target: float = 300.0, 
                      n_samples: int = 10,
                      seed: int = 42) -> List[Dict]:
    """
    Run isotropy test, collecting multiple samples at steady state.
    """
    
    sim = VibrationIsotropySimulator(
        size=32, dt=0.12,
        damping_to_tau=0.20, tau_cap=1.8,
        seed=seed
    )
    
    # Run to steady state
    print(f"  Running to T={T_target}...", end="", flush=True)
    while sim.T < T_target:
        sim.step()
        if sim.step_count % 500 == 0:
            print(f" T={sim.T:.0f}", end="", flush=True)
    
    print(f" (collecting {n_samples} samples)")
    
    # Collect samples
    samples = []
    sample_interval = 20.0  # Time between samples
    
    for i in range(n_samples):
        # Run for sample interval
        T_start = sim.T
        while sim.T < T_start + sample_interval:
            sim.step()
        
        metrics = sim.compute_isotropy_metrics()
        samples.append(metrics)
    
    return samples


def analyze_isotropy(samples: List[Dict]) -> Dict:
    """Analyze isotropy from collected samples."""
    
    # Extract anisotropy values
    gradient_anisos = [s['gradient_anisotropy'] for s in samples]
    velocity_anisos = [s['velocity_anisotropy'] for s in samples]
    kspace_anisos = [s['kspace_anisotropy'] for s in samples]
    corr_anisos = [s['correlation_anisotropy'] for s in samples]
    combined_anisos = [s['combined_anisotropy'] for s in samples]
    
    return {
        'gradient': {
            'mean': float(np.mean(gradient_anisos)),
            'std': float(np.std(gradient_anisos))
        },
        'velocity': {
            'mean': float(np.mean(velocity_anisos)),
            'std': float(np.std(velocity_anisos))
        },
        'kspace': {
            'mean': float(np.mean(kspace_anisos)),
            'std': float(np.std(kspace_anisos))
        },
        'correlation': {
            'mean': float(np.mean(corr_anisos)),
            'std': float(np.std(corr_anisos))
        },
        'combined': {
            'mean': float(np.mean(combined_anisos)),
            'std': float(np.std(combined_anisos))
        }
    }


def main():
    print("=" * 80)
    print("  VIBRATION FIELD ISOTROPY TEST")
    print("=" * 80)
    print()
    print("Question: Is the stationary vibrational phase statistically isotropic?")
    print()
    
    t0 = time.time()
    
    # Run test
    samples = run_isotropy_test(T_target=300.0, n_samples=10, seed=42)
    
    print()
    print(f"Total time: {time.time()-t0:.1f}s")
    print()
    
    # Analyze
    analysis = analyze_isotropy(samples)
    
    # Results
    print("=" * 80)
    print("  RESULTS: ANISOTROPY INDICES")
    print("=" * 80)
    print()
    
    print(f"{'Metric':>20} | {'Mean':>10} | {'Std':>10} | {'Interpretation':>20}")
    print("-" * 70)
    
    thresholds = {'strong': 0.15, 'moderate': 0.30, 'weak': 0.50}
    
    for metric, values in analysis.items():
        mean = values['mean']
        std = values['std']
        
        if mean < thresholds['strong']:
            interp = "ISOTROPIC"
        elif mean < thresholds['moderate']:
            interp = "MODERATE"
        elif mean < thresholds['weak']:
            interp = "WEAK"
        else:
            interp = "ANISOTROPIC"
        
        print(f"{metric:>20} | {mean:>10.4f} | {std:>10.4f} | {interp:>20}")
    
    print()
    
    # Directional breakdown (last sample)
    last = samples[-1]
    print("=" * 80)
    print("  DIRECTIONAL BREAKDOWN (Last Sample)")
    print("=" * 80)
    print()
    
    print("Gradient Energy:")
    E = last['gradient_energy']
    print(f"  E_x = {E['x']:.6f}")
    print(f"  E_y = {E['y']:.6f}")
    print(f"  E_z = {E['z']:.6f}")
    print(f"  Ratio max/min = {max(E.values())/min(E.values()):.3f}")
    print()
    
    print("Correlation Length:")
    L = last['correlation_length']
    print(f"  L_x = {L['x']}")
    print(f"  L_y = {L['y']}")
    print(f"  L_z = {L['z']}")
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    combined_mean = analysis['combined']['mean']
    
    if combined_mean < 0.15:
        verdict = "ISOTROPIC"
        print("✓ VIBRATION FIELD IS STATISTICALLY ISOTROPIC")
        print(f"  Combined anisotropy = {combined_mean:.4f} < 0.15")
        print("  The turbulent phase has emergent rotational symmetry.")
    elif combined_mean < 0.30:
        verdict = "MODERATELY_ISOTROPIC"
        print("? VIBRATION FIELD IS MODERATELY ISOTROPIC")
        print(f"  Combined anisotropy = {combined_mean:.4f}")
        print("  Some directional bias present, but not severe.")
    elif combined_mean < 0.50:
        verdict = "WEAKLY_ISOTROPIC"
        print("? VIBRATION FIELD HAS WEAK ISOTROPY")
        print(f"  Combined anisotropy = {combined_mean:.4f}")
        print("  Significant directional bias detected.")
    else:
        verdict = "ANISOTROPIC"
        print("✗ VIBRATION FIELD IS ANISOTROPIC")
        print(f"  Combined anisotropy = {combined_mean:.4f} > 0.50")
        print("  Strong directional bias in the turbulent phase.")
    
    print()
    
    # Physical interpretation
    print("Physical Interpretation:")
    gradient_mean = analysis['gradient']['mean']
    kspace_mean = analysis['kspace']['mean']
    
    if gradient_mean < 0.20:
        print("  - Gradient energy is well-distributed across directions")
    else:
        print("  - Gradient energy shows directional preference")
    
    if kspace_mean < 0.20:
        print("  - k-space power is approximately spherically symmetric")
    else:
        print("  - k-space power has directional structure")
    
    # Save results
    output = {
        'test': 'vibration_isotropy',
        'date': 'December 2025',
        'question': 'Is the stationary vibrational phase isotropic?',
        'T_target': 300.0,
        'n_samples': 10,
        'verdict': verdict,
        'analysis': analysis,
        'thresholds': thresholds,
        'last_sample': {
            'gradient_energy': last['gradient_energy'],
            'correlation_length': last['correlation_length'],
            'combined_anisotropy': last['combined_anisotropy']
        }
    }
    
    with open('/app/backend/qmrt_topology/papers/VIBRATION_ISOTROPY_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/VIBRATION_ISOTROPY_RESULTS.json")


if __name__ == "__main__":
    main()
