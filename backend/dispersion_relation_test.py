"""
Dispersion Relation Test
=========================

PURPOSE: Test whether the medium supports the correct frequency-wavelength
relationship ω² ≈ c² k² (linear dispersion).

HYPOTHESIS:
  If the medium supports Lorentz-like propagation, plane waves should
  satisfy ω² = c² k² with minimal deviation.

TEST PROTOCOL:
  1. Inject sinusoidal perturbations of varying wavelength λ
  2. Measure the resulting oscillation frequency ω
  3. Compute k = 2π/λ
  4. Fit ω² vs k² to extract effective c²
  5. Measure fit quality (R²) and frequency broadening

MODES:
  A: Clean medium (no defects, uniform τ)
  B: Unregulated + defects
  C: Regulated v1.1 + defects

KEY METRICS:
  - fit_R2: Quality of ω² = c²k² fit
  - c_eff_sq: Effective wave speed squared from slope
  - residual_error: Mean deviation from linear fit
  - frequency_broadening: Spread of measured frequencies
  - mode_damping_rate: How fast oscillations decay
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class DispersionSimulator:
    """
    Simulator for dispersion relation testing.
    Injects plane waves and measures frequency response.
    """
    
    def __init__(self, size: int = 32, dt: float = 0.05,
                 damping_to_tau: float = 0.0, tau_cap: float = 3.0,
                 seed: int = None, with_defects: bool = True):
        
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        self.with_defects = with_defects
        
        self.T = 0.0
        self.step_count = 0
        
        # Initialize field
        if with_defects:
            self.psi_r = np.random.randn(size, size, size) * 0.1 + 1.0
            self.psi_i = np.random.randn(size, size, size) * 0.05
            self.psi_r_dot = np.random.randn(size, size, size) * 0.02
            self.psi_i_dot = np.random.randn(size, size, size) * 0.02
        else:
            # Clean initial state
            self.psi_r = np.ones((size, size, size)) * 1.0
            self.psi_i = np.zeros((size, size, size))
            self.psi_r_dot = np.zeros((size, size, size))
            self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Coupling gradient
        x = np.linspace(0, 1, size)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        center_dist = np.sqrt((X-0.5)**2 + (Y-0.5)**2 + (Z-0.5)**2)
        self.coupling = 0.5 - 0.3 * center_dist
        
        if with_defects:
            self._seed_defects(n_defects=8)
    
    def _seed_defects(self, n_defects=8):
        margin = self.size // 4
        for _ in range(n_defects):
            cx = np.random.randint(margin, self.size - margin)
            cy = np.random.randint(margin, self.size - margin)
            cz = np.random.randint(margin, self.size - margin)
            
            x, y, z = np.meshgrid(
                np.arange(self.size), np.arange(self.size), np.arange(self.size),
                indexing='ij'
            )
            r = np.sqrt((x-cx)**2 + (y-cy)**2 + (z-cz)**2) + 0.1
            
            chirality = np.random.choice([-1, 1])
            theta = np.arctan2(y - cy, x - cx)
            
            amp = 1.5 * np.exp(-r**2 / 8)
            self.psi_r += amp * np.cos(chirality * theta)
            self.psi_i += amp * np.sin(chirality * theta)
    
    def inject_plane_wave(self, k_vec: Tuple[float, float, float], amplitude: float = 0.1):
        """
        Inject a plane wave perturbation with wavevector k.
        
        Args:
            k_vec: (kx, ky, kz) wavevector components (in units of 2π/L)
            amplitude: Wave amplitude
        """
        kx, ky, kz = k_vec
        x = np.arange(self.size)
        y = np.arange(self.size)
        z = np.arange(self.size)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Phase = k · r
        phase = (2 * np.pi / self.size) * (kx * X + ky * Y + kz * Z)
        
        # Add sinusoidal perturbation to velocity (impulse)
        self.psi_r_dot += amplitude * np.cos(phase)
    
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
        
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        return float(np.mean(energy))
    
    def get_fourier_mode(self, k_vec: Tuple[int, int, int]) -> complex:
        """Get the amplitude of a specific Fourier mode."""
        kx, ky, kz = k_vec
        
        # FFT of field
        fft = np.fft.fftn(self.psi_r)
        
        # Shift to center
        fft_shifted = np.fft.fftshift(fft)
        center = self.size // 2
        
        # Get mode amplitude (with index wrapping)
        idx_x = (center + kx) % self.size
        idx_y = (center + ky) % self.size
        idx_z = (center + kz) % self.size
        
        return fft[kx % self.size, ky % self.size, kz % self.size]


def measure_frequency(sim: DispersionSimulator, k_vec: Tuple[int, int, int],
                      measurement_T: float = 20.0) -> Dict:
    """
    Measure the oscillation frequency for a given wavevector.
    
    Returns frequency, amplitude decay, and quality metrics.
    """
    # Track mode amplitude over time
    T_vals = []
    amplitude_vals = []
    phase_vals = []
    
    T_start = sim.T
    
    while sim.T - T_start < measurement_T:
        sim.step()
        
        if sim.step_count % 5 == 0:  # Sample every 5 steps
            mode = sim.get_fourier_mode(k_vec)
            amplitude = np.abs(mode)
            phase = np.angle(mode)
            
            T_vals.append(sim.T - T_start)
            amplitude_vals.append(amplitude)
            phase_vals.append(phase)
    
    T_arr = np.array(T_vals)
    amp_arr = np.array(amplitude_vals)
    phase_arr = np.array(phase_vals)
    
    # Unwrap phase to get continuous values
    phase_unwrapped = np.unwrap(phase_arr)
    
    # Fit frequency from phase evolution: phase = ω*t + φ₀
    if len(T_arr) > 5:
        # Linear fit to unwrapped phase
        coeffs = np.polyfit(T_arr, phase_unwrapped, 1)
        omega = np.abs(coeffs[0])  # Angular frequency
        
        # Compute fit quality
        phase_pred = coeffs[0] * T_arr + coeffs[1]
        residuals = phase_unwrapped - phase_pred
        phase_r_squared = 1 - np.var(residuals) / np.var(phase_unwrapped) if np.var(phase_unwrapped) > 0 else 0
        
        # Frequency broadening: std of instantaneous frequency
        if len(T_arr) > 10:
            d_phase = np.diff(phase_unwrapped)
            d_T = np.diff(T_arr)
            instant_omega = np.abs(d_phase / d_T)
            freq_broadening = np.std(instant_omega) / np.mean(instant_omega) if np.mean(instant_omega) > 0 else 1.0
        else:
            freq_broadening = 1.0
    else:
        omega = 0
        phase_r_squared = 0
        freq_broadening = 1.0
    
    # Amplitude decay (damping rate)
    if len(amp_arr) > 5 and amp_arr[0] > 0:
        # Fit exponential decay: A(t) = A₀ * exp(-γt)
        # log(A) = log(A₀) - γt
        log_amp = np.log(amp_arr + 1e-10)
        decay_coeffs = np.polyfit(T_arr, log_amp, 1)
        damping_rate = -decay_coeffs[0]  # Positive = decaying
        
        # Normalized amplitude retention
        amp_retention = amp_arr[-1] / amp_arr[0] if amp_arr[0] > 0 else 0
    else:
        damping_rate = 0
        amp_retention = 0
    
    return {
        'omega': omega,
        'phase_r_squared': phase_r_squared,
        'freq_broadening': freq_broadening,
        'damping_rate': damping_rate,
        'amp_retention': amp_retention,
        'initial_amplitude': amp_arr[0] if len(amp_arr) > 0 else 0,
        'final_amplitude': amp_arr[-1] if len(amp_arr) > 0 else 0
    }


def run_dispersion_test(damping_to_tau: float, tau_cap: float,
                        mode_name: str, seed: int = 42,
                        with_defects: bool = True,
                        warmup_T: float = 30.0) -> Dict:
    """
    Run dispersion relation test across multiple wavelengths.
    """
    # Wavevectors to test (along x-direction for simplicity)
    # k in units of 2π/L, so k_mag = 2π * n / L
    k_values = [1, 2, 3, 4, 5, 6, 7, 8]  # Mode numbers
    
    results = []
    
    for k_n in k_values:
        # Create fresh simulator for each wavelength
        sim = DispersionSimulator(
            size=32, dt=0.05,
            damping_to_tau=damping_to_tau,
            tau_cap=tau_cap,
            seed=seed,
            with_defects=with_defects
        )
        
        # Warmup to establish τ structure (if defect-active)
        if with_defects:
            while sim.T < warmup_T:
                sim.step()
        
        tau_mean = float(np.mean(sim.tau))
        tau_std = float(np.std(sim.tau))
        
        # Inject plane wave
        k_vec = (k_n, 0, 0)
        sim.inject_plane_wave(k_vec, amplitude=0.1)
        
        # Measure frequency
        freq_result = measure_frequency(sim, k_vec, measurement_T=15.0)
        
        # Compute k magnitude
        # k = 2π * n / L, and we measure in grid units where L = size
        k_mag = 2 * np.pi * k_n / sim.size
        
        results.append({
            'k_n': k_n,
            'k_mag': k_mag,
            'k_sq': k_mag**2,
            'omega': freq_result['omega'],
            'omega_sq': freq_result['omega']**2,
            'phase_r_squared': freq_result['phase_r_squared'],
            'freq_broadening': freq_result['freq_broadening'],
            'damping_rate': freq_result['damping_rate'],
            'tau_mean': tau_mean,
            'tau_std': tau_std
        })
    
    # Fit ω² vs k²
    k_sq_arr = np.array([r['k_sq'] for r in results])
    omega_sq_arr = np.array([r['omega_sq'] for r in results])
    
    # Linear fit: ω² = c² k²
    if len(k_sq_arr) > 2 and np.var(k_sq_arr) > 0:
        # Fit through origin: ω² = c² k²
        # c² = Σ(ω²k²) / Σ(k⁴)
        c_eff_sq = np.sum(omega_sq_arr * k_sq_arr) / np.sum(k_sq_arr**2)
        
        # Compute R² for the fit
        omega_sq_pred = c_eff_sq * k_sq_arr
        residuals = omega_sq_arr - omega_sq_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((omega_sq_arr - np.mean(omega_sq_arr))**2)
        fit_r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        # Mean residual error (normalized)
        residual_error = np.sqrt(np.mean(residuals**2)) / np.mean(omega_sq_arr) if np.mean(omega_sq_arr) > 0 else 1.0
    else:
        c_eff_sq = 0
        fit_r_squared = 0
        residual_error = 1.0
    
    # Average frequency broadening
    avg_broadening = np.mean([r['freq_broadening'] for r in results])
    avg_damping = np.mean([r['damping_rate'] for r in results])
    
    return {
        'mode': mode_name,
        'config': {
            'damping_to_tau': damping_to_tau,
            'tau_cap': tau_cap,
            'with_defects': with_defects
        },
        'dispersion': {
            'c_eff_sq': c_eff_sq,
            'c_eff': np.sqrt(c_eff_sq) if c_eff_sq > 0 else 0,
            'fit_r_squared': fit_r_squared,
            'residual_error': residual_error,
            'theoretical_c_sq': 4.0  # c₀²
        },
        'quality': {
            'avg_freq_broadening': avg_broadening,
            'avg_damping_rate': avg_damping
        },
        'per_wavelength': results
    }


def main():
    print("=" * 80)
    print("  DISPERSION RELATION TEST")
    print("=" * 80)
    print()
    print("Hypothesis: Medium supports ω² = c² k² (linear dispersion)")
    print()
    print("Wavelengths tested: k = 1,2,3,4,5,6,7,8 (mode numbers)")
    print("Key metric: fit_R² for ω² vs k²")
    print()
    
    all_results = {}
    
    # Mode A: Clean medium
    print("Mode A: Clean medium (no defects)...")
    t0 = time.time()
    results_clean = run_dispersion_test(
        damping_to_tau=0.0, tau_cap=3.0,
        mode_name='clean', seed=42, with_defects=False
    )
    print(f"  c_eff = {results_clean['dispersion']['c_eff']:.3f} (theoretical: 2.0)")
    print(f"  fit_R² = {results_clean['dispersion']['fit_r_squared']:.4f}")
    print(f"  residual_error = {results_clean['dispersion']['residual_error']:.4f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    all_results['clean'] = results_clean
    
    # Mode B: Unregulated + defects
    print("Mode B: Unregulated (damping=0, cap=3.0, with defects)...")
    t0 = time.time()
    results_unreg = run_dispersion_test(
        damping_to_tau=0.0, tau_cap=3.0,
        mode_name='unregulated', seed=42, with_defects=True
    )
    print(f"  c_eff = {results_unreg['dispersion']['c_eff']:.3f}")
    print(f"  fit_R² = {results_unreg['dispersion']['fit_r_squared']:.4f}")
    print(f"  residual_error = {results_unreg['dispersion']['residual_error']:.4f}")
    print(f"  avg_broadening = {results_unreg['quality']['avg_freq_broadening']:.4f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    all_results['unregulated'] = results_unreg
    
    # Mode C: Regulated v1.1 + defects
    print("Mode C: Regulated v1.1 (damping=0.20, cap=1.8, with defects)...")
    t0 = time.time()
    results_reg = run_dispersion_test(
        damping_to_tau=0.20, tau_cap=1.8,
        mode_name='regulated_v1_1', seed=42, with_defects=True
    )
    print(f"  c_eff = {results_reg['dispersion']['c_eff']:.3f}")
    print(f"  fit_R² = {results_reg['dispersion']['fit_r_squared']:.4f}")
    print(f"  residual_error = {results_reg['dispersion']['residual_error']:.4f}")
    print(f"  avg_broadening = {results_reg['quality']['avg_freq_broadening']:.4f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    all_results['regulated_v1_1'] = results_reg
    
    # Comparison
    print("=" * 80)
    print("  COMPARISON: DISPERSION RELATION QUALITY")
    print("=" * 80)
    print()
    
    print(f"{'Mode':>20} | {'c_eff':>8} | {'fit_R²':>10} | {'Residual':>10} | {'Broadening':>10}")
    print("-" * 70)
    
    for mode_name, r in [('Clean', results_clean), 
                         ('Unregulated', results_unreg),
                         ('Regulated v1.1', results_reg)]:
        print(f"{mode_name:>20} | {r['dispersion']['c_eff']:>8.3f} | {r['dispersion']['fit_r_squared']:>10.4f} | {r['dispersion']['residual_error']:>10.4f} | {r['quality']['avg_freq_broadening']:>10.4f}")
    
    print()
    
    # Per-wavelength data
    print("=" * 80)
    print("  PER-WAVELENGTH DATA (ω² vs k²)")
    print("=" * 80)
    print()
    
    print(f"{'k_n':>5} | {'Clean ω²':>12} | {'Unreg ω²':>12} | {'Reg ω²':>12} | {'k²':>10}")
    print("-" * 60)
    
    for i, k_n in enumerate([1, 2, 3, 4, 5, 6, 7, 8]):
        clean_omega_sq = results_clean['per_wavelength'][i]['omega_sq']
        unreg_omega_sq = results_unreg['per_wavelength'][i]['omega_sq']
        reg_omega_sq = results_reg['per_wavelength'][i]['omega_sq']
        k_sq = results_clean['per_wavelength'][i]['k_sq']
        
        print(f"{k_n:>5} | {clean_omega_sq:>12.4f} | {unreg_omega_sq:>12.4f} | {reg_omega_sq:>12.4f} | {k_sq:>10.4f}")
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    # Compare fit quality
    clean_r2 = results_clean['dispersion']['fit_r_squared']
    unreg_r2 = results_unreg['dispersion']['fit_r_squared']
    reg_r2 = results_reg['dispersion']['fit_r_squared']
    
    reg_better_than_unreg = reg_r2 > unreg_r2
    
    print(f"Clean medium baseline R²: {clean_r2:.4f}")
    print(f"Regulated vs Unregulated: ", end="")
    if reg_better_than_unreg:
        improvement = (reg_r2 - unreg_r2) / (1 - unreg_r2 + 1e-9) * 100
        print(f"Regulated BETTER (R² improvement: {improvement:.1f}%)")
    else:
        print(f"Unregulated better or equal")
    
    print()
    
    # Classify result
    if reg_r2 > 0.95:
        verdict = "EXCELLENT_DISPERSION"
        print("✓ EXCELLENT: Regulated medium maintains clean dispersion relation")
    elif reg_r2 > 0.80 and reg_better_than_unreg:
        verdict = "GOOD_DISPERSION"
        print("✓ GOOD: Regulated recovery improves dispersion relation")
    elif reg_r2 > 0.50:
        verdict = "MODERATE_DISPERSION"
        print("? MODERATE: Dispersion relation present but degraded")
    else:
        verdict = "POOR_DISPERSION"
        print("✗ POOR: Dispersion relation significantly disrupted")
    
    print()
    
    # Scientific interpretation
    print("INTERPRETATION:")
    if clean_r2 > 0.95:
        print("  - Clean medium confirms ω² ∝ k² relationship")
    if reg_better_than_unreg:
        print("  - Regulated recovery preserves dispersion better than unregulated")
    else:
        print("  - Defect dynamics disrupt dispersion regardless of regulation")
    
    # Save results
    output = {
        'test': 'dispersion_relation',
        'date': 'December 2025',
        'hypothesis': 'Medium supports omega^2 = c^2 k^2 linear dispersion',
        'config': {
            'size': 32, 'dt': 0.05,
            'warmup_T': 30.0, 'measurement_T': 15.0,
            'k_values': [1, 2, 3, 4, 5, 6, 7, 8]
        },
        'verdict': verdict,
        'summary': {
            'clean_fit_r2': float(clean_r2),
            'unreg_fit_r2': float(unreg_r2),
            'reg_fit_r2': float(reg_r2),
            'reg_better': bool(reg_better_than_unreg),
            'clean_c_eff': float(results_clean['dispersion']['c_eff']),
            'unreg_c_eff': float(results_unreg['dispersion']['c_eff']),
            'reg_c_eff': float(results_reg['dispersion']['c_eff'])
        },
        'results': {
            'clean': {
                'c_eff': float(results_clean['dispersion']['c_eff']),
                'fit_r2': float(results_clean['dispersion']['fit_r_squared']),
                'residual_error': float(results_clean['dispersion']['residual_error'])
            },
            'unregulated': {
                'c_eff': float(results_unreg['dispersion']['c_eff']),
                'fit_r2': float(results_unreg['dispersion']['fit_r_squared']),
                'residual_error': float(results_unreg['dispersion']['residual_error'])
            },
            'regulated_v1_1': {
                'c_eff': float(results_reg['dispersion']['c_eff']),
                'fit_r2': float(results_reg['dispersion']['fit_r_squared']),
                'residual_error': float(results_reg['dispersion']['residual_error'])
            }
        }
    }
    
    with open('/app/backend/qmrt_topology/papers/DISPERSION_RELATION_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/DISPERSION_RELATION_RESULTS.json")


if __name__ == "__main__":
    main()
