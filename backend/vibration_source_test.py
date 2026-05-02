"""
Defect-Driven Vibration Source Test
====================================

PURPOSE: Validate the new conceptual model where defects are active
vibration sources, not byproducts of medium dynamics.

HYPOTHESIS:
  In a perfectly balanced medium, no vibration occurs because no gradients
  exist. Defects provide the symmetry-breaking sources that generate
  oscillatory activity. Regulated damping-to-τ recycling sustains a dynamic
  equilibrium where defects seed vibrations and vibrations recycle into
  new topology.

NEW CONCEPTUAL MODEL:
  defects/topology
  → local strain, torsion, phase gradients
  → vibration / wave emission
  → damping converts activity into τ recharge
  → τ enables new defect creation
  → sustained turbulent topology

KEY QUESTIONS:
  1. Is a clean medium truly "silent" (no self-generated vibration)?
  2. Do defects generate localized wave activity?
  3. Does v1.1 sustain a stable vibrational phase?
  4. Do creation events correlate with vibration bursts?
  5. Does the power spectrum stabilize over time?

METRICS:
  - vibration_energy: 0.5 * (psi_r_dot² + psi_i_dot²)
  - strain_energy: |∇ψ|²
  - vorticity: |curl(phase_gradient)|
  - power_spectrum: FFT of vibration field
  - creation_rate: creations per time unit
  - energy_autocorrelation: temporal stability

CONDITIONS:
  A: Clean medium, no defects (expect: silent)
  B: Clean medium + injected defect (expect: localized waves)
  C: Regulated v1.1 (expect: sustained broadband vibration)
  D: No damping recovery (expect: decay or instability)
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List, Tuple
import time
import json


class VibrationSourceSimulator:
    """
    Simulator for testing defect-driven vibration dynamics.
    """
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = 0.0,
                 tau_cap: float = 3.0,
                 seed: int = None,
                 with_initial_structure: bool = True):
        
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        
        self.T = 0.0
        self.step_count = 0
        
        # Initialize field - quiet state
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
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
        self.creations = 0
        self.creations_this_step = 0
        self.total_damped = 0.0
        self.total_recycled = 0.0
        
        if with_initial_structure:
            self.seed_structure(n_pairs=8)
    
    def inject_vortex(self, cx, cy, cz, chirality=1):
        """Inject a single vortex defect."""
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
        """Seed initial defect structure."""
        center = self.size // 2
        for _ in range(n_pairs):
            a1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.17)
            cx1 = center + r1 * np.cos(a1)
            cy1 = center + r1 * np.sin(a1)
            cz1 = center + np.random.uniform(-3, 3)
            
            a2 = a1 + np.pi + np.random.uniform(-0.5, 0.5)
            r2 = np.random.uniform(2, self.size * 0.17)
            cx2 = center + r2 * np.cos(a2)
            cy2 = center + r2 * np.sin(a2)
            cz2 = center + np.random.uniform(-3, 3)
            
            self.inject_vortex(cx1, cy1, cz1, chirality=1)
            self.inject_vortex(cx2, cy2, cz2, chirality=-1)
    
    def step(self):
        self.step_count += 1
        self.T += self.dt
        self.creations_this_step = 0
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        self.total_damped += float(np.sum(damped_energy))
        
        # Energy and tau dynamics
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # Damping → τ coupling
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Creation from high τ regions
        if self.creation_rate > 0:
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
                        self.inject_vortex(cx, cy, cz, chirality)
                        self.creations += 1
                        self.creations_this_step += 1
                        self.tau[cx, cy, cz] = 1.0
        
        # Wave propagation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        return float(np.mean(energy))
    
    def compute_vibration_metrics(self) -> Dict:
        """Compute vibration field statistics."""
        
        # Vibration energy: kinetic energy of field oscillation
        vibration_energy = 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Strain energy: |∇ψ|²
        dx_r = np.diff(self.psi_r, axis=0, append=self.psi_r[:1, :, :])
        dy_r = np.diff(self.psi_r, axis=1, append=self.psi_r[:, :1, :])
        dz_r = np.diff(self.psi_r, axis=2, append=self.psi_r[:, :, :1])
        dx_i = np.diff(self.psi_i, axis=0, append=self.psi_i[:1, :, :])
        dy_i = np.diff(self.psi_i, axis=1, append=self.psi_i[:, :1, :])
        dz_i = np.diff(self.psi_i, axis=2, append=self.psi_i[:, :, :1])
        
        strain_energy = dx_r**2 + dy_r**2 + dz_r**2 + dx_i**2 + dy_i**2 + dz_i**2
        
        # Phase and vorticity
        phase = np.arctan2(self.psi_i, self.psi_r)
        dx_phase = np.diff(phase, axis=0, append=phase[:1, :, :])
        dy_phase = np.diff(phase, axis=1, append=phase[:, :1, :])
        dz_phase = np.diff(phase, axis=2, append=phase[:, :, :1])
        
        # Wrap phases
        dx_phase = np.where(dx_phase > np.pi, dx_phase - 2*np.pi, dx_phase)
        dx_phase = np.where(dx_phase < -np.pi, dx_phase + 2*np.pi, dx_phase)
        dy_phase = np.where(dy_phase > np.pi, dy_phase - 2*np.pi, dy_phase)
        dy_phase = np.where(dy_phase < -np.pi, dy_phase + 2*np.pi, dy_phase)
        dz_phase = np.where(dz_phase > np.pi, dz_phase - 2*np.pi, dz_phase)
        dz_phase = np.where(dz_phase < -np.pi, dz_phase + 2*np.pi, dz_phase)
        
        vorticity = np.sqrt(
            (np.roll(dz_phase, -1, 1) - dz_phase)**2 +
            (np.roll(dx_phase, -1, 2) - dx_phase)**2 +
            (np.roll(dy_phase, -1, 0) - dy_phase)**2
        )
        
        # Power spectrum (radially averaged)
        fft = np.fft.fftn(self.psi_r_dot)
        power = np.abs(fft)**2
        
        # Radial averaging
        kx = np.fft.fftfreq(self.size)
        ky = np.fft.fftfreq(self.size)
        kz = np.fft.fftfreq(self.size)
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        K = np.sqrt(KX**2 + KY**2 + KZ**2)
        
        k_bins = np.linspace(0, 0.5, 16)
        power_spectrum = []
        for i in range(len(k_bins) - 1):
            mask = (K >= k_bins[i]) & (K < k_bins[i+1])
            if np.any(mask):
                power_spectrum.append(float(np.mean(power[mask])))
            else:
                power_spectrum.append(0.0)
        
        return {
            'T': self.T,
            'vibration_energy_mean': float(np.mean(vibration_energy)),
            'vibration_energy_max': float(np.max(vibration_energy)),
            'vibration_energy_total': float(np.sum(vibration_energy)),
            'strain_energy_mean': float(np.mean(strain_energy)),
            'strain_energy_total': float(np.sum(strain_energy)),
            'vorticity_mean': float(np.mean(vorticity)),
            'vorticity_max': float(np.max(vorticity)),
            'tau_mean': float(np.mean(self.tau)),
            'tau_max': float(np.max(self.tau)),
            'creations_total': self.creations,
            'creations_this_step': self.creations_this_step,
            'power_spectrum': power_spectrum,
            'k_bins': [(k_bins[i] + k_bins[i+1])/2 for i in range(len(k_bins)-1)]
        }


def run_vibration_test(mode: str, T_max: float = 100.0, 
                       measure_interval: float = 10.0) -> Tuple[List[Dict], str]:
    """
    Run vibration test for a specific mode.
    
    Modes:
        'clean': No defects, no creation (expect: silent)
        'single_defect': One injected defect, no creation (expect: localized waves)
        'regulated_v1_1': Full v1.1 with defects and creation (expect: sustained)
        'no_recovery': Defects but no damping-to-tau (expect: decay)
    """
    
    if mode == 'clean':
        sim = VibrationSourceSimulator(
            size=32, dt=0.12,
            damping_to_tau=0.0, tau_cap=3.0,
            creation_rate=0.0,
            with_initial_structure=False,
            seed=42
        )
        description = "Clean medium, no defects"
        
    elif mode == 'single_defect':
        sim = VibrationSourceSimulator(
            size=32, dt=0.12,
            damping_to_tau=0.0, tau_cap=3.0,
            creation_rate=0.0,
            with_initial_structure=False,
            seed=42
        )
        # Inject single defect
        sim.inject_vortex(16, 16, 16, chirality=1)
        description = "Single injected defect"
        
    elif mode == 'regulated_v1_1':
        sim = VibrationSourceSimulator(
            size=32, dt=0.12,
            damping_to_tau=0.20, tau_cap=1.8,
            creation_rate=0.15,
            with_initial_structure=True,
            seed=42
        )
        description = "Regulated v1.1 (full system)"
        
    elif mode == 'no_recovery':
        sim = VibrationSourceSimulator(
            size=32, dt=0.12,
            damping_to_tau=0.0, tau_cap=3.0,
            creation_rate=0.15,
            with_initial_structure=True,
            seed=42
        )
        description = "Defects but no damping recovery"
    
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    history = []
    
    # Initial measurement
    metrics = sim.compute_vibration_metrics()
    history.append(metrics)
    
    while sim.T < T_max:
        sim.step()
        
        if sim.T >= len(history) * measure_interval:
            metrics = sim.compute_vibration_metrics()
            history.append(metrics)
    
    return history, description


def analyze_spectrum_stability(history: List[Dict]) -> Dict:
    """Analyze stability of power spectrum over time."""
    
    if len(history) < 3:
        return {'stable': False, 'reason': 'insufficient data'}
    
    # Get spectra from different time points
    spectra = [h['power_spectrum'] for h in history[2:]]  # Skip initial transient
    
    if not spectra:
        return {'stable': False, 'reason': 'no spectra'}
    
    spectra = np.array(spectra)
    
    # Compute mean spectrum and variation
    mean_spectrum = np.mean(spectra, axis=0)
    std_spectrum = np.std(spectra, axis=0)
    
    # Coefficient of variation for each k-bin
    cv = std_spectrum / (mean_spectrum + 1e-10)
    
    # Spectrum is stable if CV < 0.5 for most bins
    stable_bins = np.sum(cv < 0.5)
    total_bins = len(cv)
    
    return {
        'stable': stable_bins >= total_bins * 0.7,
        'stable_fraction': stable_bins / total_bins,
        'mean_cv': float(np.mean(cv)),
        'mean_spectrum': [float(x) for x in mean_spectrum],
        'std_spectrum': [float(x) for x in std_spectrum]
    }


def main():
    print("=" * 80)
    print("  DEFECT-DRIVEN VIBRATION SOURCE TEST")
    print("=" * 80)
    print()
    print("New Conceptual Model:")
    print("  Defects are active vibration sources, not noise.")
    print("  A perfect medium is 'silent' with no gradients.")
    print("  Regulated recovery sustains turbulent vibrational phase.")
    print()
    
    modes = ['clean', 'single_defect', 'regulated_v1_1', 'no_recovery']
    all_results = {}
    
    for mode in modes:
        print(f"Testing: {mode}...")
        t0 = time.time()
        
        history, description = run_vibration_test(mode, T_max=100.0, measure_interval=10.0)
        spectrum_analysis = analyze_spectrum_stability(history)
        
        all_results[mode] = {
            'description': description,
            'history': history,
            'spectrum_stability': spectrum_analysis
        }
        
        # Summary
        final = history[-1]
        print(f"  {description}")
        print(f"  Final T={final['T']:.0f}: vib_energy={final['vibration_energy_mean']:.6f}, "
              f"vorticity={final['vorticity_mean']:.3f}, creations={final['creations_total']}")
        print(f"  Spectrum stable: {spectrum_analysis['stable']} "
              f"(CV={spectrum_analysis.get('mean_cv', 0):.3f})")
        print(f"  Time: {time.time()-t0:.1f}s")
        print()
    
    # Comparison
    print("=" * 80)
    print("  COMPARISON: VIBRATION ACTIVITY")
    print("=" * 80)
    print()
    
    header = f"{'Mode':>20} | {'Vib Energy':>12} | {'Vorticity':>10} | {'Creations':>10} | {'Spectrum':>10}"
    print(header)
    print("-" * 75)
    
    for mode, data in all_results.items():
        final = data['history'][-1]
        spectrum_status = "STABLE" if data['spectrum_stability']['stable'] else "UNSTABLE"
        print(f"{mode:>20} | {final['vibration_energy_mean']:>12.6f} | "
              f"{final['vorticity_mean']:>10.3f} | {final['creations_total']:>10} | "
              f"{spectrum_status:>10}")
    
    print()
    
    # Vibration energy evolution
    print("=" * 80)
    print("  VIBRATION ENERGY EVOLUTION")
    print("=" * 80)
    print()
    
    print(f"{'T':>6}", end="")
    for mode in modes:
        print(f" | {mode:>15}", end="")
    print()
    print("-" * 80)
    
    # Get common time points
    times = [h['T'] for h in all_results['clean']['history']]
    for i, t in enumerate(times[:6]):  # First 6 time points
        print(f"{t:>6.0f}", end="")
        for mode in modes:
            hist = all_results[mode]['history']
            if i < len(hist):
                vib = hist[i]['vibration_energy_mean']
                print(f" | {vib:>15.6f}", end="")
            else:
                print(f" | {'N/A':>15}", end="")
        print()
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    clean_vib = all_results['clean']['history'][-1]['vibration_energy_mean']
    single_vib = all_results['single_defect']['history'][-1]['vibration_energy_mean']
    reg_vib = all_results['regulated_v1_1']['history'][-1]['vibration_energy_mean']
    no_rec_vib = all_results['no_recovery']['history'][-1]['vibration_energy_mean']
    
    print("Question 1: Is clean medium 'silent'?")
    if clean_vib < 1e-6:
        print(f"  YES - Vibration energy = {clean_vib:.2e} (effectively zero)")
        q1_pass = True
    else:
        print(f"  NO - Vibration energy = {clean_vib:.2e}")
        q1_pass = False
    print()
    
    print("Question 2: Does single defect generate waves?")
    if single_vib > 1e-6 and single_vib > clean_vib + 1e-6:
        ratio = single_vib / (clean_vib + 1e-10)
        print(f"  YES - Defect creates vibration ({single_vib:.6f} vs clean {clean_vib:.6f})")
        q2_pass = True
    else:
        print(f"  UNCLEAR - Single defect vibration = {single_vib:.2e}")
        q2_pass = False
    print()
    
    print("Question 3: Does v1.1 sustain vibration?")
    reg_stable = all_results['regulated_v1_1']['spectrum_stability']['stable']
    if reg_vib > single_vib and reg_stable:
        print(f"  YES - High sustained vibration ({reg_vib:.4f}) with stable spectrum")
        q3_pass = True
    elif reg_vib > single_vib:
        print(f"  PARTIAL - High vibration but spectrum unstable")
        q3_pass = False
    else:
        print(f"  NO - Vibration not sustained")
        q3_pass = False
    print()
    
    print("Question 4: Does removal of recovery cause decay?")
    if no_rec_vib < reg_vib * 0.5:
        print(f"  YES - Without recovery: {no_rec_vib:.4f} vs with: {reg_vib:.4f}")
        q4_pass = True
    else:
        print(f"  NO - Similar vibration with/without recovery")
        q4_pass = False
    print()
    
    # Overall verdict
    passes = sum([q1_pass, q2_pass, q3_pass, q4_pass])
    print(f"SCORE: {passes}/4 questions confirmed")
    print()
    
    if passes >= 3:
        verdict = "CONFIRMED"
        print("✓ NEW MODEL CONFIRMED:")
        print("  Defects are active vibration sources.")
        print("  Clean medium is silent.")
        print("  Regulated recovery sustains vibrational phase.")
    elif passes >= 2:
        verdict = "PARTIAL"
        print("? PARTIAL SUPPORT for new model")
    else:
        verdict = "NOT_CONFIRMED"
        print("✗ NEW MODEL NOT CONFIRMED")
    
    # Save results
    output = {
        'test': 'defect_driven_vibration',
        'date': 'December 2025',
        'hypothesis': 'Defects are active vibration sources; clean medium is silent',
        'verdict': verdict,
        'score': f'{passes}/4',
        'questions': {
            'clean_silent': q1_pass,
            'defect_generates_waves': q2_pass,
            'v1_1_sustained': q3_pass,
            'recovery_essential': q4_pass
        },
        'summary': {
            'clean_vib': float(clean_vib),
            'single_defect_vib': float(single_vib),
            'regulated_vib': float(reg_vib),
            'no_recovery_vib': float(no_rec_vib),
            'reg_spectrum_stable': reg_stable
        }
    }
    
    # Simplified history for JSON
    for mode in modes:
        output[mode] = {
            'description': all_results[mode]['description'],
            'final_metrics': {
                'T': all_results[mode]['history'][-1]['T'],
                'vibration_energy': all_results[mode]['history'][-1]['vibration_energy_mean'],
                'vorticity': all_results[mode]['history'][-1]['vorticity_mean'],
                'creations': all_results[mode]['history'][-1]['creations_total']
            },
            'spectrum_stability': all_results[mode]['spectrum_stability']['stable']
        }
    
    with open('/app/backend/qmrt_topology/papers/VIBRATION_SOURCE_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/VIBRATION_SOURCE_RESULTS.json")


if __name__ == "__main__":
    main()
