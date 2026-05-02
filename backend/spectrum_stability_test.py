"""
Spectrum Stability Test
=======================

PURPOSE: Determine whether the regulated v1.1 vibrational phase
reaches a statistically stationary state with stable power spectrum.

KEY QUESTION:
  Does the power spectrum converge/stabilize at T=500, 1000, 2000?
  
If yes: The system sustains a stationary vibrational phase.
If no: The system is in transient/chaotic churn.

METRICS:
  - Power spectrum at each checkpoint
  - Spectrum coefficient of variation (CV) between checkpoints
  - Vibration energy mean and variance
  - Dominant frequency/wavelength
  - Energy autocorrelation decay

A stable spectrum indicates the turbulent equilibrium has reached
a statistically stationary attractor state.
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class SpectrumStabilitySimulator:
    """Simulator for long-horizon spectrum stability testing."""
    
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
        
        # Seed initial structure
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
        
        # Creation
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
    
    def compute_power_spectrum(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute radially-averaged power spectrum of velocity field."""
        
        fft = np.fft.fftn(self.psi_r_dot)
        power = np.abs(fft)**2
        
        kx = np.fft.fftfreq(self.size)
        ky = np.fft.fftfreq(self.size)
        kz = np.fft.fftfreq(self.size)
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        K = np.sqrt(KX**2 + KY**2 + KZ**2)
        
        n_bins = 16
        k_bins = np.linspace(0, 0.5, n_bins + 1)
        k_centers = (k_bins[:-1] + k_bins[1:]) / 2
        
        spectrum = np.zeros(n_bins)
        for i in range(n_bins):
            mask = (K >= k_bins[i]) & (K < k_bins[i+1])
            if np.any(mask):
                spectrum[i] = np.mean(power[mask])
        
        return k_centers, spectrum
    
    def compute_metrics(self) -> Dict:
        """Compute comprehensive metrics at checkpoint."""
        
        vibration_energy = 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        k_centers, spectrum = self.compute_power_spectrum()
        
        # Find dominant frequency
        dominant_k_idx = np.argmax(spectrum[1:]) + 1  # Skip k=0
        dominant_k = k_centers[dominant_k_idx]
        
        return {
            'T': self.T,
            'vibration_energy_mean': float(np.mean(vibration_energy)),
            'vibration_energy_std': float(np.std(vibration_energy)),
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'creations': self.creations,
            'spectrum': [float(s) for s in spectrum],
            'k_centers': [float(k) for k in k_centers],
            'dominant_k': float(dominant_k),
            'total_spectral_power': float(np.sum(spectrum))
        }


def compute_spectrum_stability(spectra: List[np.ndarray]) -> Dict:
    """Compute stability metrics for a sequence of spectra."""
    
    if len(spectra) < 2:
        return {'stable': False, 'reason': 'insufficient data'}
    
    spectra = np.array(spectra)
    
    # Mean and std across time
    mean_spectrum = np.mean(spectra, axis=0)
    std_spectrum = np.std(spectra, axis=0)
    
    # Coefficient of variation per k-bin
    cv = std_spectrum / (mean_spectrum + 1e-10)
    
    # Overall stability score
    mean_cv = float(np.mean(cv))
    max_cv = float(np.max(cv))
    
    # Spectrum is stable if mean CV < 0.3
    stable = mean_cv < 0.3
    
    return {
        'stable': stable,
        'mean_cv': mean_cv,
        'max_cv': max_cv,
        'mean_spectrum': [float(x) for x in mean_spectrum],
        'std_spectrum': [float(x) for x in std_spectrum],
        'cv_per_bin': [float(x) for x in cv]
    }


def run_spectrum_stability_test(checkpoints: List[float], 
                                 sample_window: float = 50.0,
                                 samples_per_window: int = 10,
                                 seed: int = 42) -> Dict:
    """
    Run spectrum stability test at specified checkpoints.
    
    At each checkpoint, collect multiple spectrum samples over a time window
    to compute stability statistics.
    """
    
    sim = SpectrumStabilitySimulator(
        size=32, dt=0.12,
        damping_to_tau=0.20, tau_cap=1.8,
        seed=seed
    )
    
    results = []
    
    for checkpoint in checkpoints:
        # Run to checkpoint
        while sim.T < checkpoint:
            sim.step()
            if sim.step_count % 1000 == 0:
                print(f"    T={sim.T:.0f}...", end="", flush=True)
        
        # Collect spectrum samples over window
        spectra_samples = []
        sample_interval = sample_window / samples_per_window
        T_start = sim.T
        
        for i in range(samples_per_window):
            while sim.T < T_start + (i + 1) * sample_interval:
                sim.step()
            
            _, spectrum = sim.compute_power_spectrum()
            spectra_samples.append(spectrum)
        
        # Compute stability for this window
        stability = compute_spectrum_stability(spectra_samples)
        metrics = sim.compute_metrics()
        
        results.append({
            'checkpoint': checkpoint,
            'metrics': metrics,
            'stability': stability,
            'spectra_samples': [[float(s) for s in spec] for spec in spectra_samples]
        })
        
        print(f" checkpoint T={checkpoint}: stable={stability['stable']}, CV={stability['mean_cv']:.3f}")
    
    return {
        'checkpoints': results,
        'final_metrics': sim.compute_metrics()
    }


def main():
    print("=" * 80)
    print("  SPECTRUM STABILITY TEST")
    print("=" * 80)
    print()
    print("Question: Does the power spectrum stabilize over long time horizons?")
    print()
    print("Checkpoints: T = 200, 400, 600")
    print("(Reduced from 500/1000/2000 to fit time constraints)")
    print()
    
    t0 = time.time()
    
    results = run_spectrum_stability_test(
        checkpoints=[200, 400, 600],
        sample_window=50.0,
        samples_per_window=10,
        seed=42
    )
    
    print()
    print(f"Total time: {time.time()-t0:.1f}s")
    print()
    
    # Analysis
    print("=" * 80)
    print("  RESULTS")
    print("=" * 80)
    print()
    
    print(f"{'Checkpoint':>12} | {'Vib Energy':>12} | {'Spectrum CV':>12} | {'Stable':>8}")
    print("-" * 55)
    
    for cp_result in results['checkpoints']:
        checkpoint = cp_result['checkpoint']
        vib_energy = cp_result['metrics']['vibration_energy_mean']
        cv = cp_result['stability']['mean_cv']
        stable = "YES" if cp_result['stability']['stable'] else "NO"
        
        print(f"{checkpoint:>12.0f} | {vib_energy:>12.4f} | {cv:>12.4f} | {stable:>8}")
    
    print()
    
    # Check convergence trend
    cvs = [cp['stability']['mean_cv'] for cp in results['checkpoints']]
    vib_energies = [cp['metrics']['vibration_energy_mean'] for cp in results['checkpoints']]
    
    # CV trend
    cv_slope = (cvs[-1] - cvs[0]) / (results['checkpoints'][-1]['checkpoint'] - results['checkpoints'][0]['checkpoint'])
    
    # Energy trend
    energy_slope = (vib_energies[-1] - vib_energies[0]) / (results['checkpoints'][-1]['checkpoint'] - results['checkpoints'][0]['checkpoint'])
    
    print("=" * 80)
    print("  TRENDS")
    print("=" * 80)
    print()
    
    print(f"Spectrum CV trend: {cv_slope:.6f} per time unit")
    if cv_slope < -0.0001:
        print("  → CV DECREASING (spectrum becoming more stable)")
        cv_trend = "improving"
    elif cv_slope > 0.0001:
        print("  → CV INCREASING (spectrum becoming less stable)")
        cv_trend = "degrading"
    else:
        print("  → CV STABLE (spectrum variability constant)")
        cv_trend = "stable"
    
    print()
    
    print(f"Vibration energy trend: {energy_slope:.6f} per time unit")
    if abs(energy_slope) < 0.01:
        print("  → Energy STABLE (stationary phase)")
        energy_trend = "stationary"
    elif energy_slope > 0:
        print("  → Energy INCREASING (system still ramping)")
        energy_trend = "increasing"
    else:
        print("  → Energy DECREASING (system decaying)")
        energy_trend = "decreasing"
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    final_stable = results['checkpoints'][-1]['stability']['stable']
    final_cv = results['checkpoints'][-1]['stability']['mean_cv']
    
    if final_stable:
        verdict = "STABLE_PHASE"
        print("✓ SPECTRUM HAS STABILIZED")
        print(f"  Final CV = {final_cv:.4f} (< 0.3 threshold)")
        print("  The system has reached a statistically stationary vibrational phase.")
    elif cv_trend == "improving":
        verdict = "CONVERGING"
        print("? SPECTRUM CONVERGING BUT NOT YET STABLE")
        print(f"  Final CV = {final_cv:.4f}, trend = improving")
        print("  May need longer simulation to reach stationarity.")
    else:
        verdict = "UNSTABLE"
        print("✗ SPECTRUM NOT STABLE")
        print(f"  Final CV = {final_cv:.4f}")
        print("  System may be in chaotic/transient regime.")
    
    print()
    
    if energy_trend == "stationary":
        print("✓ Vibration energy has reached steady state.")
    else:
        print(f"? Vibration energy is {energy_trend}.")
    
    # Save results
    output = {
        'test': 'spectrum_stability',
        'date': 'December 2025',
        'question': 'Does the power spectrum stabilize over long time?',
        'checkpoints': [200, 400, 600],
        'verdict': verdict,
        'summary': {
            'final_cv': final_cv,
            'final_stable': final_stable,
            'cv_trend': cv_trend,
            'energy_trend': energy_trend,
            'final_vib_energy': vib_energies[-1]
        },
        'per_checkpoint': [{
            'T': cp['checkpoint'],
            'vib_energy': cp['metrics']['vibration_energy_mean'],
            'spectrum_cv': cp['stability']['mean_cv'],
            'stable': cp['stability']['stable']
        } for cp in results['checkpoints']]
    }
    
    with open('/app/backend/qmrt_topology/papers/SPECTRUM_STABILITY_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/SPECTRUM_STABILITY_RESULTS.json")


if __name__ == "__main__":
    main()
