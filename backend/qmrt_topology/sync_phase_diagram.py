#!/usr/bin/env python3
"""
QMRT Synchronization Phase Diagram
===================================

KEY QUESTION:
Under what conditions do local process clocks become mutually consistent
enough to support a spacetime-like regime?

TEST DESIGN:
- Add Kuramoto-style oscillator coupling: dθᵢ/dt = ω₀ + ε|φ| + κ Σⱼ sin(θⱼ - θᵢ)
- Sweep coupling strength κ and disorder level σ
- Measure synchronization metrics at each point

METRICS:
1. R = clock ratio stability (variance of θᵢ/θⱼ ratios)
2. S = clock disagreement (variance of phase velocities)
3. Collapse quality (variance reduction under τ_osc vs t_sim)

REGIME CLASSIFICATION:
- Unsynchronized: high S, poor collapse, unstable R
- Partial: moderate S, mixed collapse
- Ratio-locked: low variance of R, but no strong collapse
- Spacetime-like: low S, stable R, improved collapse
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import interp1d
import json


class SynchronizationSimulator:
    """
    Simulator with coupled oscillators for synchronization testing.
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
        # Oscillator parameters
        omega_0: float = 1.0,
        epsilon: float = 0.1,
        # SYNCHRONIZATION COUPLING (Kuramoto)
        kappa: float = 0.0,  # Coupling strength
        # Disorder
        disorder_sigma: float = 0.0,  # Initial condition disorder
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
        self.kappa = kappa
        self.disorder_sigma = disorder_sigma
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        # Add disorder to initial conditions
        if disorder_sigma > 0:
            self.phi += np.random.randn(size, size) * disorder_sigma * 0.5
            self.tau += np.random.randn(size, size) * disorder_sigma * 0.1
            self.tau = np.clip(self.tau, 0.5, 1.5)
        
        self.t_sim = 0.0
        self.probes = {}
        self.oscillator_phase = {}
        self.history = {'t_sim': []}
    
    def set_probes(self, probes: dict):
        """Set probe locations."""
        self.probes = probes
        for name in probes:
            self.oscillator_phase[name] = 0.0
            self.history[f'theta_{name}'] = []
            self.history[f'dtheta_dt_{name}'] = []
            self.history[f'phi_envelope_{name}'] = []
    
    def compute_c_eff(self):
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
        """Advance one timestep with coupled oscillators."""
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
        
        # Update oscillators with COUPLING (Kuramoto-style)
        # dθᵢ/dt = ω₀ + ε|φ(xᵢ)| + κ Σⱼ sin(θⱼ - θᵢ)
        
        probe_names = list(self.probes.keys())
        n_probes = len(probe_names)
        
        # Compute coupling term for each oscillator
        dtheta_dt = {}
        for i, name_i in enumerate(probe_names):
            ri, rj = self.probes[name_i]
            local_phi = self.phi[ri, rj]
            
            # Base rate + local coupling to wave
            rate = self.omega_0 + self.epsilon * np.abs(local_phi)
            
            # Kuramoto coupling to other oscillators
            if self.kappa > 0 and n_probes > 1:
                coupling_sum = 0.0
                for j, name_j in enumerate(probe_names):
                    if i != j:
                        theta_i = self.oscillator_phase[name_i]
                        theta_j = self.oscillator_phase[name_j]
                        coupling_sum += np.sin(theta_j - theta_i)
                rate += self.kappa * coupling_sum / (n_probes - 1)
            
            dtheta_dt[name_i] = rate
        
        # Apply updates
        for name in probe_names:
            self.oscillator_phase[name] += dtheta_dt[name] * self.dt
        
        self.t_sim += self.dt
        
        return dtheta_dt
    
    def record_history(self, dtheta_dt=None):
        """Record state."""
        self.history['t_sim'].append(self.t_sim)
        
        for name, (ri, rj) in self.probes.items():
            theta = self.oscillator_phase[name]
            self.history[f'theta_{name}'].append(theta)
            
            if dtheta_dt is not None:
                self.history[f'dtheta_dt_{name}'].append(dtheta_dt[name])
            
            # Observable
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


def compute_synchronization_metrics(history, probe_names):
    """
    Compute synchronization metrics from simulation history.
    """
    n_probes = len(probe_names)
    
    # Get final phases
    final_phases = {name: history[f'theta_{name}'][-1] for name in probe_names}
    
    # Ratio stability: variance of θᵢ/θⱼ over time
    ratio_variances = []
    for i, name_i in enumerate(probe_names):
        for j, name_j in enumerate(probe_names):
            if i < j:
                theta_i = np.array(history[f'theta_{name_i}'])
                theta_j = np.array(history[f'theta_{name_j}'])
                ratio = theta_i / (theta_j + 1e-10)
                half = len(ratio) // 2
                if half > 0:
                    ratio_var = np.var(ratio[half:])
                    ratio_variances.append(ratio_var)
    
    ratio_stability = np.mean(ratio_variances) if ratio_variances else np.nan
    
    # Phase velocity variance
    if f'dtheta_dt_{probe_names[0]}' in history and len(history[f'dtheta_dt_{probe_names[0]}']) > 0:
        half = len(history[f'dtheta_dt_{probe_names[0]}']) // 2
        phase_velocities_end = []
        for name in probe_names:
            dtheta_dt = np.array(history[f'dtheta_dt_{name}'])
            if half > 0:
                phase_velocities_end.append(np.mean(dtheta_dt[half:]))
        phase_velocity_variance = np.var(phase_velocities_end)
    else:
        phase_velocity_variance = np.nan
    
    # Kuramoto order parameter
    phases = np.array([final_phases[name] for name in probe_names])
    complex_order = np.mean(np.exp(1j * phases))
    kuramoto_order = np.abs(complex_order)
    
    # Clock disagreement S
    if not np.isnan(phase_velocity_variance):
        S = phase_velocity_variance
    else:
        final_phases_arr = np.array([final_phases[name] for name in probe_names])
        S = np.var(final_phases_arr / (history['t_sim'][-1] + 1e-10))
    
    return {
        'ratio_stability': float(ratio_stability),
        'phase_velocity_variance': float(phase_velocity_variance),
        'kuramoto_order': float(kuramoto_order),
        'S': float(S),
        'final_phases': {name: float(final_phases[name]) for name in probe_names},
    }


def compute_collapse_quality(history, probe_names):
    """
    Compute collapse quality.
    """
    t_sim = np.array(history['t_sim'])
    
    tau_osc = {}
    phi_envelope = {}
    
    for name in probe_names:
        tau_osc[name] = np.array(history[f'theta_{name}']) / (2 * np.pi)
        phi_envelope[name] = np.array(history[f'phi_envelope_{name}'])
    
    # Variance under t_sim
    obs_stack = np.vstack([phi_envelope[name] for name in probe_names])
    variance_t_sim = np.mean(np.var(obs_stack, axis=0))
    
    # Variance under tau_osc
    tau_mins = [np.min(tau_osc[name]) for name in probe_names]
    tau_maxs = [np.max(tau_osc[name]) for name in probe_names]
    tau_common_min = max(tau_mins)
    tau_common_max = min(tau_maxs)
    
    if tau_common_max > tau_common_min:
        n_points = 50
        tau_common = np.linspace(tau_common_min, tau_common_max, n_points)
        
        interpolated = []
        for name in probe_names:
            sort_idx = np.argsort(tau_osc[name])
            tau_sorted = tau_osc[name][sort_idx]
            obs_sorted = phi_envelope[name][sort_idx]
            
            try:
                f = interp1d(tau_sorted, obs_sorted, kind='linear', 
                            bounds_error=False, fill_value='extrapolate')
                obs_interp = f(tau_common)
                interpolated.append(obs_interp)
            except:
                pass
        
        if len(interpolated) >= 2:
            interp_stack = np.vstack(interpolated)
            variance_tau_osc = np.mean(np.var(interp_stack, axis=0))
        else:
            variance_tau_osc = variance_t_sim
    else:
        variance_tau_osc = variance_t_sim
    
    # Improvement
    if variance_t_sim > 0:
        improvement = (variance_t_sim - variance_tau_osc) / variance_t_sim * 100
    else:
        improvement = 0
    
    return {
        'variance_t_sim': float(variance_t_sim),
        'variance_tau_osc': float(variance_tau_osc),
        'improvement_pct': float(improvement),
    }


def run_single_point(kappa, disorder_sigma, n_steps=500):
    """
    Run simulation at a single parameter point.
    """
    sim = SynchronizationSimulator(
        size=80,
        beta=1.0,
        lambda_relax=1.5,
        omega_0=1.0,
        epsilon=0.1,
        kappa=kappa,
        disorder_sigma=disorder_sigma,
    )
    
    probes = {
        'A': (40, 40),
        'B': (40, 25),
        'C': (25, 25),
    }
    sim.set_probes(probes)
    
    sim.add_pulse([40, 40], amplitude=4.0, velocity=False)
    
    for _ in range(30):
        dtheta_dt = sim.step()
    
    sim.add_pulse([40, 40], amplitude=3.0, velocity=True)
    
    for t in range(n_steps):
        dtheta_dt = sim.step()
        if t % 5 == 0:
            sim.record_history(dtheta_dt)
    
    probe_names = list(probes.keys())
    sync_metrics = compute_synchronization_metrics(sim.history, probe_names)
    collapse_metrics = compute_collapse_quality(sim.history, probe_names)
    
    return {
        'kappa': kappa,
        'disorder_sigma': disorder_sigma,
        **sync_metrics,
        **collapse_metrics,
    }


def classify_regime(metrics):
    """
    Classify the regime.
    """
    S = metrics['S']
    improvement = metrics['improvement_pct']
    kuramoto = metrics['kuramoto_order']
    
    S_high = 0.1
    improvement_threshold = 10
    kuramoto_high = 0.8
    
    if kuramoto > kuramoto_high and improvement > improvement_threshold:
        return 'spacetime_candidate'
    elif kuramoto > 0.6 and S < S_high:
        return 'ratio_locked'
    elif S < S_high or kuramoto > 0.5:
        return 'partial'
    else:
        return 'unsynchronized'


def run_phase_diagram():
    """
    Main phase diagram scan.
    """
    print("=" * 70)
    print("SYNCHRONIZATION PHASE DIAGRAM")
    print("=" * 70)
    print()
    print("Scanning: coupling strength κ × disorder σ")
    print("Oscillator: dθᵢ/dt = ω₀ + ε|φ| + κ Σⱼ sin(θⱼ - θᵢ)")
    print()
    
    # Parameter grid
    kappa_values = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8]
    disorder_values = [0.0, 0.2, 0.5, 1.0, 1.5, 2.0]
    
    n_kappa = len(kappa_values)
    n_disorder = len(disorder_values)
    
    S_grid = np.zeros((n_disorder, n_kappa))
    R_grid = np.zeros((n_disorder, n_kappa))
    improvement_grid = np.zeros((n_disorder, n_kappa))
    kuramoto_grid = np.zeros((n_disorder, n_kappa))
    regime_grid = np.empty((n_disorder, n_kappa), dtype=object)
    
    total_points = n_kappa * n_disorder
    point_count = 0
    
    for i, disorder in enumerate(disorder_values):
        for j, kappa in enumerate(kappa_values):
            point_count += 1
            print(f"  [{point_count}/{total_points}] κ={kappa:.2f}, σ={disorder:.1f}", end="")
            
            metrics = run_single_point(kappa, disorder, n_steps=400)
            
            S_grid[i, j] = metrics['S']
            R_grid[i, j] = metrics['ratio_stability']
            improvement_grid[i, j] = metrics['improvement_pct']
            kuramoto_grid[i, j] = metrics['kuramoto_order']
            
            regime = classify_regime(metrics)
            regime_grid[i, j] = regime
            
            print(f" → {regime} (K={metrics['kuramoto_order']:.2f}, imp={metrics['improvement_pct']:.1f}%)")
    
    print("\n" + "=" * 70)
    print("PHASE DIAGRAM ANALYSIS")
    print("=" * 70)
    
    regime_counts = {}
    for i in range(n_disorder):
        for j in range(n_kappa):
            r = regime_grid[i, j]
            regime_counts[r] = regime_counts.get(r, 0) + 1
    
    print("\nRegime distribution:")
    for regime, count in sorted(regime_counts.items()):
        pct = count / total_points * 100
        print(f"  {regime:20}: {count} ({pct:.1f}%)")
    
    spacetime_points = []
    for i, disorder in enumerate(disorder_values):
        for j, kappa in enumerate(kappa_values):
            if regime_grid[i, j] == 'spacetime_candidate':
                spacetime_points.append((kappa, disorder))
    
    print(f"\nSpacetime candidate points: {len(spacetime_points)}")
    for kappa, disorder in spacetime_points:
        print(f"  κ={kappa:.2f}, σ={disorder:.1f}")
    
    # Plotting
    fig = plt.figure(figsize=(18, 14))
    
    ax = fig.add_subplot(2, 3, 1)
    im = ax.imshow(kuramoto_grid, origin='lower', aspect='auto', cmap='viridis',
                   extent=[kappa_values[0], kappa_values[-1], disorder_values[0], disorder_values[-1]])
    ax.set_xlabel('Coupling κ')
    ax.set_ylabel('Disorder σ')
    ax.set_title('Kuramoto Order Parameter\n(higher = more synchronized)')
    plt.colorbar(im, ax=ax, label='K')
    
    ax = fig.add_subplot(2, 3, 2)
    im = ax.imshow(np.log10(S_grid + 1e-10), origin='lower', aspect='auto', cmap='viridis_r',
                   extent=[kappa_values[0], kappa_values[-1], disorder_values[0], disorder_values[-1]])
    ax.set_xlabel('Coupling κ')
    ax.set_ylabel('Disorder σ')
    ax.set_title('Clock Disagreement S (log scale)\n(lower = more synchronized)')
    plt.colorbar(im, ax=ax, label='log₁₀(S)')
    
    ax = fig.add_subplot(2, 3, 3)
    im = ax.imshow(improvement_grid, origin='lower', aspect='auto', cmap='RdYlGn',
                   extent=[kappa_values[0], kappa_values[-1], disorder_values[0], disorder_values[-1]],
                   vmin=-30, vmax=30)
    ax.set_xlabel('Coupling κ')
    ax.set_ylabel('Disorder σ')
    ax.set_title('Collapse Improvement (%)\n(>10% = spacetime candidate)')
    plt.colorbar(im, ax=ax, label='%')
    
    ax = fig.add_subplot(2, 3, 4)
    regime_colors = {
        'unsynchronized': 0,
        'partial': 1,
        'ratio_locked': 2,
        'spacetime_candidate': 3,
    }
    regime_numeric = np.zeros_like(kuramoto_grid)
    for i in range(n_disorder):
        for j in range(n_kappa):
            regime_numeric[i, j] = regime_colors.get(regime_grid[i, j], 0)
    
    im = ax.imshow(regime_numeric, origin='lower', aspect='auto', cmap='coolwarm',
                   extent=[kappa_values[0], kappa_values[-1], disorder_values[0], disorder_values[-1]],
                   vmin=0, vmax=3)
    ax.set_xlabel('Coupling κ')
    ax.set_ylabel('Disorder σ')
    ax.set_title('Regime Classification\n(0=unsync, 1=partial, 2=locked, 3=spacetime)')
    plt.colorbar(im, ax=ax, label='Regime')
    
    ax = fig.add_subplot(2, 3, 5)
    for disorder in [0.0, 0.5, 1.0, 2.0]:
        if disorder in disorder_values:
            idx = disorder_values.index(disorder)
            ax.plot(kappa_values, kuramoto_grid[idx, :], 'o-', label=f'σ={disorder}', linewidth=2)
    ax.set_xlabel('Coupling κ')
    ax.set_ylabel('Kuramoto Order K')
    ax.set_title('Synchronization vs Coupling')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.8, color='k', linestyle='--', alpha=0.5)
    
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
SYNCHRONIZATION PHASE DIAGRAM
=============================

Oscillator: dθᵢ/dt = ω₀ + ε|φ| + κ Σⱼ sin(θⱼ - θᵢ)

Parameter scan:
  κ (coupling): {kappa_values[0]} → {kappa_values[-1]}
  σ (disorder): {disorder_values[0]} → {disorder_values[-1]}

Regime distribution:
"""
    for regime, count in sorted(regime_counts.items()):
        pct = count / total_points * 100
        summary += f"  {regime}: {count} ({pct:.0f}%)\n"
    
    summary += f"""
Spacetime candidates: {len(spacetime_points)}

KEY FINDING:
"""
    if len(spacetime_points) > 0:
        summary += "Spacetime-like regime EXISTS at high coupling + low disorder"
        verdict = "PHASE TRANSITION OBSERVED"
    elif regime_counts.get('ratio_locked', 0) > 0:
        summary += "Ratio-locking achieved but collapse not improved"
        verdict = "PARTIAL SYNCHRONIZATION"
    else:
        summary += "No synchronized regime found in parameter range"
        verdict = "NO TRANSITION"
    
    summary += f"\n\nVERDICT: {verdict}"
    
    color = 'lightgreen' if len(spacetime_points) > 0 else 'lightyellow' if regime_counts.get('ratio_locked', 0) > 0 else 'lightcoral'
    ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'SYNCHRONIZATION PHASE DIAGRAM: {verdict}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/sync_phase_diagram.png', dpi=150, bbox_inches='tight')
    print("\nSaved sync_phase_diagram.png")
    
    results_json = {
        'kappa_values': kappa_values,
        'disorder_values': disorder_values,
        'regime_counts': regime_counts,
        'spacetime_points': spacetime_points,
        'kuramoto_grid': kuramoto_grid.tolist(),
        'S_grid': S_grid.tolist(),
        'improvement_grid': improvement_grid.tolist(),
        'regime_grid': regime_grid.tolist(),
        'verdict': verdict,
    }
    
    with open('/app/backend/qmrt_topology/sync_phase_diagram_results.json', 'w') as f:
        json.dump(results_json, f, indent=2)
    print("Saved sync_phase_diagram_results.json")
    
    return results_json


if __name__ == "__main__":
    results = run_phase_diagram()
