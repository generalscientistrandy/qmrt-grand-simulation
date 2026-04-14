#!/usr/bin/env python3
"""
QMRT Frequency-Locking Test
============================

Phase-locking (Kuramoto) achieved K → 1.0, but collapse didn't improve.
Now test FREQUENCY-LOCKING: force oscillators to have same rate, not just phase.

KEY QUESTION:
Does forcing identical frequencies (not just phase alignment) improve collapse?

OSCILLATOR EQUATION:
  dθᵢ/dt = ω₀ + ε|φ| + κ_phase Σⱼ sin(θⱼ - θᵢ) + κ_freq (ω̄ - ωᵢ)

where:
  κ_phase = phase coupling (Kuramoto)
  κ_freq = frequency coupling (forces rates to converge)
  ω̄ = mean frequency across oscillators
  ωᵢ = instantaneous frequency of oscillator i
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import interp1d
import json


class FrequencyLockSimulator:
    """
    Simulator with both phase and frequency coupling.
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        beta: float = 1.0,
        lambda_relax: float = 1.5,
        D_medium: float = 0.1,
        gamma_wave: float = 0.008,
        dt: float = 0.04,
        omega_0: float = 1.0,
        epsilon: float = 0.1,
        # Phase coupling (Kuramoto)
        kappa_phase: float = 0.0,
        # Frequency coupling (NEW)
        kappa_freq: float = 0.0,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        self.omega_0 = omega_0
        self.epsilon = epsilon
        self.kappa_phase = kappa_phase
        self.kappa_freq = kappa_freq
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        self.t_sim = 0.0
        self.probes = {}
        self.oscillator_phase = {}
        self.oscillator_freq = {}  # Track instantaneous frequencies
        self.history = {'t_sim': []}
    
    def set_probes(self, probes: dict):
        self.probes = probes
        for name in probes:
            self.oscillator_phase[name] = 0.0
            self.oscillator_freq[name] = self.omega_0
            self.history[f'theta_{name}'] = []
            self.history[f'freq_{name}'] = []
            self.history[f'phi_envelope_{name}'] = []
    
    def compute_c_eff(self):
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
        """Advance with phase + frequency coupling."""
        rho = self.phi**2 + self.phi_dot**2
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        
        tau_eq = self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
        
        lap_tau = (np.roll(self.tau, 1, axis=0) + np.roll(self.tau, -1, axis=0) +
                   np.roll(self.tau, 1, axis=1) + np.roll(self.tau, -1, axis=1) - 
                   4 * self.tau)
        
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        
        lap_phi = (np.roll(self.phi, 1, axis=0) + np.roll(self.phi, -1, axis=0) +
                   np.roll(self.phi, 1, axis=1) + np.roll(self.phi, -1, axis=1) - 
                   4 * self.phi)
        
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
        
        probe_names = list(self.probes.keys())
        n_probes = len(probe_names)
        
        # Compute base frequencies for each oscillator
        base_freqs = {}
        for name in probe_names:
            ri, rj = self.probes[name]
            local_phi = self.phi[ri, rj]
            base_freqs[name] = self.omega_0 + self.epsilon * np.abs(local_phi)
        
        # Mean frequency (for frequency coupling)
        mean_freq = np.mean(list(base_freqs.values()))
        
        # Update each oscillator
        dtheta_dt = {}
        for i, name_i in enumerate(probe_names):
            rate = base_freqs[name_i]
            
            # Phase coupling (Kuramoto)
            if self.kappa_phase > 0 and n_probes > 1:
                coupling_sum = 0.0
                for j, name_j in enumerate(probe_names):
                    if i != j:
                        theta_i = self.oscillator_phase[name_i]
                        theta_j = self.oscillator_phase[name_j]
                        coupling_sum += np.sin(theta_j - theta_i)
                rate += self.kappa_phase * coupling_sum / (n_probes - 1)
            
            # Frequency coupling (NEW)
            # Pull instantaneous frequency toward mean
            if self.kappa_freq > 0:
                current_freq = self.oscillator_freq[name_i]
                rate += self.kappa_freq * (mean_freq - current_freq)
            
            dtheta_dt[name_i] = rate
            self.oscillator_freq[name_i] = rate  # Update stored frequency
        
        # Apply phase updates
        for name in probe_names:
            self.oscillator_phase[name] += dtheta_dt[name] * self.dt
        
        self.t_sim += self.dt
        return dtheta_dt
    
    def record_history(self, dtheta_dt=None):
        self.history['t_sim'].append(self.t_sim)
        
        for name, (ri, rj) in self.probes.items():
            self.history[f'theta_{name}'].append(self.oscillator_phase[name])
            self.history[f'freq_{name}'].append(self.oscillator_freq[name])
            
            window = 3
            i0, i1 = max(0, ri-window), min(self.size, ri+window+1)
            j0, j1 = max(0, rj-window), min(self.size, rj+window+1)
            phi_local = self.phi[i0:i1, j0:j1]
            phi_envelope = np.sqrt(np.mean(phi_local**2))
            self.history[f'phi_envelope_{name}'].append(phi_envelope)
    
    def add_pulse(self, center, amplitude=3.0, width=4.0, velocity=True):
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    if velocity:
                        self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
                    else:
                        self.phi[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))


def compute_metrics(history, probe_names):
    """Compute synchronization and collapse metrics."""
    
    # Final phases
    final_phases = {name: history[f'theta_{name}'][-1] for name in probe_names}
    
    # Kuramoto order
    phases = np.array([final_phases[name] for name in probe_names])
    kuramoto = np.abs(np.mean(np.exp(1j * phases)))
    
    # Frequency variance (latter half)
    half = len(history[f'freq_{probe_names[0]}']) // 2
    freq_variances = []
    for t_idx in range(half, len(history['t_sim'])):
        freqs_at_t = [history[f'freq_{name}'][t_idx] for name in probe_names]
        freq_variances.append(np.var(freqs_at_t))
    mean_freq_variance = np.mean(freq_variances)
    
    # Collapse quality
    t_sim = np.array(history['t_sim'])
    tau_osc = {name: np.array(history[f'theta_{name}']) / (2 * np.pi) for name in probe_names}
    phi_envelope = {name: np.array(history[f'phi_envelope_{name}']) for name in probe_names}
    
    # Variance under t_sim
    obs_stack = np.vstack([phi_envelope[name] for name in probe_names])
    variance_t_sim = np.mean(np.var(obs_stack, axis=0))
    
    # Variance under tau_osc
    tau_mins = [np.min(tau_osc[name]) for name in probe_names]
    tau_maxs = [np.max(tau_osc[name]) for name in probe_names]
    tau_common_min = max(tau_mins)
    tau_common_max = min(tau_maxs)
    
    if tau_common_max > tau_common_min:
        tau_common = np.linspace(tau_common_min, tau_common_max, 50)
        interpolated = []
        for name in probe_names:
            sort_idx = np.argsort(tau_osc[name])
            tau_sorted = tau_osc[name][sort_idx]
            obs_sorted = phi_envelope[name][sort_idx]
            try:
                f = interp1d(tau_sorted, obs_sorted, kind='linear', 
                            bounds_error=False, fill_value='extrapolate')
                interpolated.append(f(tau_common))
            except:
                pass
        if len(interpolated) >= 2:
            variance_tau_osc = np.mean(np.var(np.vstack(interpolated), axis=0))
        else:
            variance_tau_osc = variance_t_sim
    else:
        variance_tau_osc = variance_t_sim
    
    improvement = (variance_t_sim - variance_tau_osc) / variance_t_sim * 100 if variance_t_sim > 0 else 0
    
    return {
        'kuramoto': float(kuramoto),
        'freq_variance': float(mean_freq_variance),
        'variance_t_sim': float(variance_t_sim),
        'variance_tau_osc': float(variance_tau_osc),
        'improvement_pct': float(improvement),
    }


def run_frequency_locking_test():
    """
    Compare phase-only vs phase+frequency coupling.
    """
    print("=" * 70)
    print("FREQUENCY-LOCKING TEST")
    print("=" * 70)
    print()
    print("Comparing:")
    print("  1. Phase coupling only (Kuramoto)")
    print("  2. Phase + Frequency coupling")
    print()
    
    probes = {
        'A': (40, 40),
        'B': (40, 25),
        'C': (25, 25),
    }
    probe_names = list(probes.keys())
    
    # Test configurations
    configs = [
        {'name': 'No coupling', 'kappa_phase': 0.0, 'kappa_freq': 0.0},
        {'name': 'Phase only (κ_p=0.5)', 'kappa_phase': 0.5, 'kappa_freq': 0.0},
        {'name': 'Phase only (κ_p=0.8)', 'kappa_phase': 0.8, 'kappa_freq': 0.0},
        {'name': 'Freq only (κ_f=0.5)', 'kappa_phase': 0.0, 'kappa_freq': 0.5},
        {'name': 'Freq only (κ_f=0.8)', 'kappa_phase': 0.0, 'kappa_freq': 0.8},
        {'name': 'Phase+Freq (0.5,0.5)', 'kappa_phase': 0.5, 'kappa_freq': 0.5},
        {'name': 'Phase+Freq (0.8,0.8)', 'kappa_phase': 0.8, 'kappa_freq': 0.8},
    ]
    
    results = []
    
    for config in configs:
        print(f"Running: {config['name']}...", end=" ")
        
        sim = FrequencyLockSimulator(
            size=80,
            beta=1.0,
            lambda_relax=1.5,
            omega_0=1.0,
            epsilon=0.1,
            kappa_phase=config['kappa_phase'],
            kappa_freq=config['kappa_freq'],
        )
        sim.set_probes(probes)
        
        sim.add_pulse([40, 40], amplitude=4.0, velocity=False)
        
        for _ in range(30):
            sim.step()
        
        sim.add_pulse([40, 40], amplitude=3.0, velocity=True)
        
        for t in range(500):
            dtheta_dt = sim.step()
            if t % 5 == 0:
                sim.record_history(dtheta_dt)
        
        metrics = compute_metrics(sim.history, probe_names)
        metrics['config'] = config['name']
        metrics['kappa_phase'] = config['kappa_phase']
        metrics['kappa_freq'] = config['kappa_freq']
        results.append(metrics)
        
        print(f"K={metrics['kuramoto']:.2f}, freq_var={metrics['freq_variance']:.4f}, imp={metrics['improvement_pct']:.1f}%")
    
    # Analysis
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)
    print()
    print(f"{'Config':<25} {'K':>6} {'Freq Var':>10} {'Collapse Imp':>12}")
    print("-" * 55)
    for r in results:
        print(f"{r['config']:<25} {r['kuramoto']:>6.2f} {r['freq_variance']:>10.4f} {r['improvement_pct']:>11.1f}%")
    
    # Find best
    best_idx = np.argmax([r['improvement_pct'] for r in results])
    best = results[best_idx]
    
    print()
    print(f"Best configuration: {best['config']}")
    print(f"  Kuramoto order: {best['kuramoto']:.2f}")
    print(f"  Frequency variance: {best['freq_variance']:.4f}")
    print(f"  Collapse improvement: {best['improvement_pct']:.1f}%")
    
    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    # Check if frequency coupling helps
    phase_only_best = max([r['improvement_pct'] for r in results if r['kappa_freq'] == 0])
    freq_best = max([r['improvement_pct'] for r in results if r['kappa_freq'] > 0])
    
    print(f"\n  Best with phase-only: {phase_only_best:.1f}%")
    print(f"  Best with frequency coupling: {freq_best:.1f}%")
    
    if freq_best > phase_only_best + 5:
        verdict = "FREQUENCY COUPLING HELPS"
        verdict_short = "FREQ_HELPS"
    elif freq_best > 10:
        verdict = "FREQUENCY COUPLING REACHES THRESHOLD"
        verdict_short = "THRESHOLD_REACHED"
    else:
        verdict = "FREQUENCY COUPLING NOT SUFFICIENT"
        verdict_short = "NOT_SUFFICIENT"
    
    print(f"\n>>> {verdict}")
    
    # Plotting
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Comparison bar chart
    ax = fig.add_subplot(2, 3, 1)
    names = [r['config'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    colors = ['green' if imp > 10 else 'orange' if imp > 0 else 'red' for imp in improvements]
    ax.barh(names, improvements, color=colors)
    ax.axvline(x=10, color='k', linestyle='--', alpha=0.5, label='10% threshold')
    ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    ax.set_xlabel('Collapse Improvement (%)')
    ax.set_title('Collapse Improvement by Configuration')
    ax.legend()
    
    # 2. Kuramoto order
    ax = fig.add_subplot(2, 3, 2)
    kuramatos = [r['kuramoto'] for r in results]
    ax.barh(names, kuramatos, color='blue', alpha=0.7)
    ax.axvline(x=0.8, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Kuramoto Order K')
    ax.set_title('Phase Synchronization')
    
    # 3. Frequency variance
    ax = fig.add_subplot(2, 3, 3)
    freq_vars = [r['freq_variance'] for r in results]
    ax.barh(names, freq_vars, color='purple', alpha=0.7)
    ax.set_xlabel('Frequency Variance')
    ax.set_title('Frequency Disagreement (lower = more locked)')
    
    # 4. Phase vs Frequency coupling heatmap
    ax = fig.add_subplot(2, 3, 4)
    kp_values = sorted(set([r['kappa_phase'] for r in results]))
    kf_values = sorted(set([r['kappa_freq'] for r in results]))
    
    grid = np.zeros((len(kf_values), len(kp_values)))
    for r in results:
        i = kf_values.index(r['kappa_freq'])
        j = kp_values.index(r['kappa_phase'])
        grid[i, j] = r['improvement_pct']
    
    im = ax.imshow(grid, origin='lower', aspect='auto', cmap='RdYlGn',
                   extent=[min(kp_values)-0.1, max(kp_values)+0.1, 
                          min(kf_values)-0.1, max(kf_values)+0.1],
                   vmin=-10, vmax=20)
    ax.set_xlabel('κ_phase')
    ax.set_ylabel('κ_freq')
    ax.set_title('Collapse Improvement (%)')
    plt.colorbar(im, ax=ax)
    
    # 5. K vs improvement scatter
    ax = fig.add_subplot(2, 3, 5)
    ax.scatter(kuramatos, improvements, c=[r['kappa_freq'] for r in results], 
               cmap='viridis', s=100)
    ax.set_xlabel('Kuramoto Order K')
    ax.set_ylabel('Collapse Improvement (%)')
    ax.set_title('Phase Sync vs Collapse (color=κ_freq)')
    ax.axhline(y=10, color='k', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3)
    
    # 6. Summary
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
FREQUENCY-LOCKING TEST
======================

Question: Does forcing identical frequencies
(not just phases) improve collapse?

Configurations tested: {len(results)}

Best results:
  Phase-only best: {phase_only_best:.1f}%
  Frequency-coupling best: {freq_best:.1f}%
  
  Best overall: {best['config']}
    Improvement: {best['improvement_pct']:.1f}%
    Kuramoto K: {best['kuramoto']:.2f}
    Freq variance: {best['freq_variance']:.4f}

VERDICT: {verdict}

Clock branch input:
  Freq lock achieved: {freq_best > 5}
  Rate synchronization: {np.min(freq_vars):.4f}
"""
    
    color = 'lightgreen' if verdict_short == 'FREQ_HELPS' else 'lightyellow' if verdict_short == 'THRESHOLD_REACHED' else 'lightcoral'
    ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'FREQUENCY-LOCKING TEST: {verdict_short}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/frequency_locking.png', dpi=150, bbox_inches='tight')
    print("\nSaved frequency_locking.png")
    
    # Save JSON
    results_json = {
        'configs': results,
        'phase_only_best': float(phase_only_best),
        'freq_best': float(freq_best),
        'verdict': verdict,
        'verdict_short': verdict_short,
    }
    
    with open('/app/backend/qmrt_topology/frequency_locking_results.json', 'w') as f:
        json.dump(results_json, f, indent=2)
    print("Saved frequency_locking_results.json")
    
    return results_json


if __name__ == "__main__":
    results = run_frequency_locking_test()
