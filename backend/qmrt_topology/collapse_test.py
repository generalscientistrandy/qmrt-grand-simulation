#!/usr/bin/env python3
"""
QMRT Oscillator Clock Collapse Test
====================================

KEY QUESTION:
Does the oscillator clock τ_osc parameterize local dynamics 
BETTER than simulation time t_sim?

TEST PROCEDURE:
1. Pick 3 probe regions with different activity levels
2. Record at each probe:
   - t_sim (simulation time)
   - τ_osc = θ/(2π) (continuous oscillator time)
   - O (independent observable: local wave amplitude envelope)
3. Plot O vs t_sim and O vs τ_osc for all probes
4. Measure collapse quality: do curves align better under τ_osc?

PASS/FAIL CRITERION:
- Curves collapse better under τ_osc than under t_sim
- Improvement is nontrivial (>20% variance reduction)

OSCILLATOR EQUATION (process-based):
  dθ/dt = ω₀ + ε|φ(x_i, t)|
  
  - ω₀ fixed across all probes
  - ε weak (0.1)
  - NO direct dependence on τ or c_eff
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import interp1d
import json


class CollapseTestSimulator:
    """
    Simulator for oscillator clock collapse test.
    """
    
    def __init__(
        self,
        size: int = 100,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        beta: float = 1.0,
        lambda_relax: float = 1.5,
        D_medium: float = 0.1,
        gamma_wave: float = 0.008,
        dt: float = 0.04,
        # Oscillator parameters (FIXED across all probes)
        omega_0: float = 1.0,  # Base frequency - SAME for all
        epsilon: float = 0.1,  # Coupling - weak
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
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        # Time
        self.t_sim = 0.0
        
        # Probes
        self.probes = {}
        self.oscillator_phase = {}
        
        # History
        self.history = {
            't_sim': [],
        }
    
    def set_probes(self, probes: dict):
        """Set probe locations."""
        self.probes = probes
        for name in probes:
            self.oscillator_phase[name] = 0.0
            self.history[f'theta_{name}'] = []
            self.history[f'tau_osc_{name}'] = []
            self.history[f'phi_envelope_{name}'] = []  # Independent observable
            self.history[f'energy_{name}'] = []  # Another observable
    
    def compute_c_eff(self):
        """Wave speed from medium state."""
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
        """Advance one timestep."""
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
        
        # Update oscillators at each probe
        # PROCESS-BASED: dθ/dt = ω₀ + ε|φ|
        for name, (ri, rj) in self.probes.items():
            local_phi = self.phi[ri, rj]
            dtheta_dt = self.omega_0 + self.epsilon * np.abs(local_phi)
            self.oscillator_phase[name] += dtheta_dt * self.dt
        
        self.t_sim += self.dt
    
    def record_history(self):
        """Record state for analysis."""
        self.history['t_sim'].append(self.t_sim)
        
        for name, (ri, rj) in self.probes.items():
            theta = self.oscillator_phase[name]
            tau_osc = theta / (2 * np.pi)  # Continuous oscillator time
            
            # Independent observable: smoothed amplitude envelope
            # Use a small window around the probe
            window = 3
            i0, i1 = max(0, ri-window), min(self.size, ri+window+1)
            j0, j1 = max(0, rj-window), min(self.size, rj+window+1)
            phi_local = self.phi[i0:i1, j0:j1]
            phi_envelope = np.sqrt(np.mean(phi_local**2))
            
            # Energy observable
            energy_local = self.phi[ri, rj]**2 + self.phi_dot[ri, rj]**2
            
            self.history[f'theta_{name}'].append(theta)
            self.history[f'tau_osc_{name}'].append(tau_osc)
            self.history[f'phi_envelope_{name}'].append(phi_envelope)
            self.history[f'energy_{name}'].append(energy_local)
    
    def add_pulse(self, center, amplitude=3.0, width=4.0, velocity=True):
        """Add a Gaussian pulse."""
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    if velocity:
                        self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
                    else:
                        self.phi[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))


def compute_collapse_quality(t_values_list, obs_values_list, common_range=None):
    """
    Compute collapse quality: how well do curves from different regions 
    align when parameterized by a given time variable?
    
    Lower variance = better collapse.
    
    Args:
        t_values_list: List of time arrays (one per region)
        obs_values_list: List of observable arrays (one per region)
        common_range: (t_min, t_max) for interpolation
    
    Returns:
        dict with collapse metrics
    """
    # Find common range
    t_mins = [np.min(t) for t in t_values_list]
    t_maxs = [np.max(t) for t in t_values_list]
    
    if common_range is None:
        t_common_min = max(t_mins)
        t_common_max = min(t_maxs)
    else:
        t_common_min, t_common_max = common_range
    
    if t_common_max <= t_common_min:
        return {'variance': np.nan, 'rmse': np.nan, 'correlation': np.nan}
    
    # Create common time grid
    n_points = 100
    t_common = np.linspace(t_common_min, t_common_max, n_points)
    
    # Interpolate all curves onto common grid
    interpolated = []
    for t_arr, obs_arr in zip(t_values_list, obs_values_list):
        # Sort by time
        sort_idx = np.argsort(t_arr)
        t_sorted = np.array(t_arr)[sort_idx]
        obs_sorted = np.array(obs_arr)[sort_idx]
        
        # Interpolate
        try:
            f = interp1d(t_sorted, obs_sorted, kind='linear', 
                        bounds_error=False, fill_value='extrapolate')
            obs_interp = f(t_common)
            interpolated.append(obs_interp)
        except:
            return {'variance': np.nan, 'rmse': np.nan, 'correlation': np.nan}
    
    if len(interpolated) < 2:
        return {'variance': np.nan, 'rmse': np.nan, 'correlation': np.nan}
    
    # Stack and compute metrics
    stacked = np.vstack(interpolated)
    
    # Variance at each time point, averaged
    variance_per_t = np.var(stacked, axis=0)
    mean_variance = np.mean(variance_per_t)
    
    # RMSE between curves
    n_curves = len(interpolated)
    rmse_sum = 0
    count = 0
    for i in range(n_curves):
        for j in range(i+1, n_curves):
            rmse_sum += np.sqrt(np.mean((interpolated[i] - interpolated[j])**2))
            count += 1
    mean_rmse = rmse_sum / count if count > 0 else np.nan
    
    # Mean correlation between curves
    corr_sum = 0
    for i in range(n_curves):
        for j in range(i+1, n_curves):
            corr = np.corrcoef(interpolated[i], interpolated[j])[0, 1]
            if not np.isnan(corr):
                corr_sum += corr
    mean_corr = corr_sum / count if count > 0 else np.nan
    
    return {
        'variance': float(mean_variance),
        'rmse': float(mean_rmse),
        'correlation': float(mean_corr),
    }


def run_collapse_test():
    """
    Main collapse test.
    """
    print("=" * 70)
    print("OSCILLATOR CLOCK COLLAPSE TEST")
    print("=" * 70)
    print()
    print("Question: Does τ_osc parameterize dynamics better than t_sim?")
    print()
    print("Oscillator equation: dθ/dt = ω₀ + ε|φ|")
    print("  ω₀ = 1.0 (fixed across all probes)")
    print("  ε = 0.1 (weak coupling)")
    print()
    
    # Create simulator
    sim = CollapseTestSimulator(
        size=100,
        beta=1.0,
        lambda_relax=1.5,
        omega_0=1.0,  # FIXED
        epsilon=0.1,  # WEAK
    )
    
    # Set up probes
    probes = {
        'high_activity': (50, 50),  # Energy source location
        'transitional': (50, 30),   # Medium distance
        'quiet': (25, 25),          # Far from source
    }
    sim.set_probes(probes)
    
    # Add stationary energy at high_activity location
    sim.add_pulse([50, 50], amplitude=5.0, velocity=False)
    
    # Let medium settle
    print("Phase 1: Medium settling (50 steps)")
    for t in range(50):
        sim.step()
        if t % 5 == 0:
            sim.record_history()
    
    # Add propagating pulse to create dynamics
    print("Phase 2: Adding propagating pulse")
    sim.add_pulse([50, 50], amplitude=4.0, velocity=True)
    
    # Run main simulation
    print("Phase 3: Main simulation (800 steps)")
    for t in range(800):
        sim.step()
        if t % 4 == 0:
            sim.record_history()
    
    # Analysis
    print("\n" + "=" * 70)
    print("COLLAPSE ANALYSIS")
    print("=" * 70)
    
    results = {}
    
    # Extract data
    t_sim = np.array(sim.history['t_sim'])
    
    tau_osc = {}
    phi_envelope = {}
    energy = {}
    
    for name in probes:
        tau_osc[name] = np.array(sim.history[f'tau_osc_{name}'])
        phi_envelope[name] = np.array(sim.history[f'phi_envelope_{name}'])
        energy[name] = np.array(sim.history[f'energy_{name}'])
    
    # Compute collapse quality for phi_envelope observable
    print("\n1. PHI ENVELOPE COLLAPSE")
    print("-" * 50)
    
    # Under t_sim
    t_sim_list = [t_sim, t_sim, t_sim]
    phi_list = [phi_envelope[name] for name in probes]
    
    collapse_t_sim = compute_collapse_quality(t_sim_list, phi_list)
    print(f"  Under t_sim:")
    print(f"    Variance: {collapse_t_sim['variance']:.6f}")
    print(f"    RMSE: {collapse_t_sim['rmse']:.6f}")
    
    # Under tau_osc
    tau_osc_list = [tau_osc[name] for name in probes]
    
    collapse_tau_osc = compute_collapse_quality(tau_osc_list, phi_list)
    print(f"  Under τ_osc:")
    print(f"    Variance: {collapse_tau_osc['variance']:.6f}")
    print(f"    RMSE: {collapse_tau_osc['rmse']:.6f}")
    
    # Improvement
    if collapse_t_sim['variance'] > 0:
        variance_improvement = (collapse_t_sim['variance'] - collapse_tau_osc['variance']) / collapse_t_sim['variance'] * 100
    else:
        variance_improvement = 0
    
    if collapse_t_sim['rmse'] > 0:
        rmse_improvement = (collapse_t_sim['rmse'] - collapse_tau_osc['rmse']) / collapse_t_sim['rmse'] * 100
    else:
        rmse_improvement = 0
    
    print(f"\n  Variance improvement: {variance_improvement:.1f}%")
    print(f"  RMSE improvement: {rmse_improvement:.1f}%")
    
    results['phi_envelope'] = {
        't_sim': collapse_t_sim,
        'tau_osc': collapse_tau_osc,
        'variance_improvement_pct': float(variance_improvement),
        'rmse_improvement_pct': float(rmse_improvement),
    }
    
    # Compute collapse quality for energy observable
    print("\n2. ENERGY COLLAPSE")
    print("-" * 50)
    
    energy_list = [energy[name] for name in probes]
    
    collapse_energy_t_sim = compute_collapse_quality(t_sim_list, energy_list)
    collapse_energy_tau_osc = compute_collapse_quality(tau_osc_list, energy_list)
    
    print(f"  Under t_sim:")
    print(f"    Variance: {collapse_energy_t_sim['variance']:.6f}")
    print(f"  Under τ_osc:")
    print(f"    Variance: {collapse_energy_tau_osc['variance']:.6f}")
    
    if collapse_energy_t_sim['variance'] > 0:
        energy_variance_improvement = (collapse_energy_t_sim['variance'] - collapse_energy_tau_osc['variance']) / collapse_energy_t_sim['variance'] * 100
    else:
        energy_variance_improvement = 0
    
    print(f"\n  Variance improvement: {energy_variance_improvement:.1f}%")
    
    results['energy'] = {
        't_sim': collapse_energy_t_sim,
        'tau_osc': collapse_energy_tau_osc,
        'variance_improvement_pct': float(energy_variance_improvement),
    }
    
    # Final oscillator state
    print("\n3. FINAL OSCILLATOR STATE")
    print("-" * 50)
    
    for name in probes:
        final_tau_osc = tau_osc[name][-1]
        print(f"  {name:15}: τ_osc = {final_tau_osc:.2f} cycles")
    
    tau_osc_spread = max([tau_osc[name][-1] for name in probes]) - min([tau_osc[name][-1] for name in probes])
    print(f"\n  τ_osc spread: {tau_osc_spread:.2f} cycles")
    
    results['final_tau_osc'] = {name: float(tau_osc[name][-1]) for name in probes}
    results['tau_osc_spread'] = float(tau_osc_spread)
    
    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    # Pass criteria: >20% improvement in either metric
    phi_pass = variance_improvement > 20 or rmse_improvement > 20
    energy_pass = energy_variance_improvement > 20
    
    any_pass = phi_pass or energy_pass
    
    print(f"\n  Phi envelope collapse improves: {'PASS' if phi_pass else 'FAIL'} ({variance_improvement:.1f}% variance)")
    print(f"  Energy collapse improves: {'PASS' if energy_pass else 'FAIL'} ({energy_variance_improvement:.1f}% variance)")
    
    if any_pass:
        verdict = "τ_osc PARAMETERIZES LOCAL DYNAMICS BETTER THAN t_sim"
        verdict_short = "PASS"
    else:
        verdict = "τ_osc DOES NOT IMPROVE COLLAPSE - NOT YET A UNIVERSAL TIME"
        verdict_short = "FAIL"
    
    print(f"\n>>> {verdict}")
    
    results['verdict'] = verdict
    results['verdict_short'] = verdict_short
    results['phi_pass'] = bool(phi_pass)
    results['energy_pass'] = bool(energy_pass)
    
    # Plotting
    fig = plt.figure(figsize=(16, 14))
    
    # 1. Phi envelope vs t_sim
    ax = fig.add_subplot(3, 3, 1)
    for name in probes:
        ax.plot(t_sim, phi_envelope[name], label=name, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('t_sim')
    ax.set_ylabel('φ envelope')
    ax.set_title(f'φ envelope vs t_sim\n(variance={collapse_t_sim["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Phi envelope vs tau_osc
    ax = fig.add_subplot(3, 3, 2)
    for name in probes:
        ax.plot(tau_osc[name], phi_envelope[name], label=name, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('τ_osc (cycles)')
    ax.set_ylabel('φ envelope')
    ax.set_title(f'φ envelope vs τ_osc\n(variance={collapse_tau_osc["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Oscillator time evolution
    ax = fig.add_subplot(3, 3, 3)
    for name in probes:
        ax.plot(t_sim, tau_osc[name], label=name, linewidth=2)
    ax.set_xlabel('t_sim')
    ax.set_ylabel('τ_osc (cycles)')
    ax.set_title(f'Oscillator Clock vs Simulation Time\n(spread={tau_osc_spread:.2f} cycles)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Energy vs t_sim
    ax = fig.add_subplot(3, 3, 4)
    for name in probes:
        ax.plot(t_sim, energy[name], label=name, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('t_sim')
    ax.set_ylabel('Local energy')
    ax.set_title(f'Energy vs t_sim\n(variance={collapse_energy_t_sim["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Energy vs tau_osc
    ax = fig.add_subplot(3, 3, 5)
    for name in probes:
        ax.plot(tau_osc[name], energy[name], label=name, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('τ_osc (cycles)')
    ax.set_ylabel('Local energy')
    ax.set_title(f'Energy vs τ_osc\n(variance={collapse_energy_tau_osc["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Collapse quality comparison
    ax = fig.add_subplot(3, 3, 6)
    metrics = ['φ envelope\nVariance', 'φ envelope\nRMSE', 'Energy\nVariance']
    t_sim_vals = [collapse_t_sim['variance'], collapse_t_sim['rmse'], collapse_energy_t_sim['variance']]
    tau_osc_vals = [collapse_tau_osc['variance'], collapse_tau_osc['rmse'], collapse_energy_tau_osc['variance']]
    
    x = np.arange(len(metrics))
    width = 0.35
    ax.bar(x - width/2, t_sim_vals, width, label='t_sim', color='blue', alpha=0.7)
    ax.bar(x + width/2, tau_osc_vals, width, label='τ_osc', color='green', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylabel('Value (lower = better collapse)')
    ax.set_title('Collapse Quality Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 7. Final τ field
    ax = fig.add_subplot(3, 3, 7)
    im = ax.imshow(sim.tau.T, origin='lower', cmap='viridis')
    for name, (ri, rj) in probes.items():
        ax.scatter(ri, rj, c='red', s=100, marker='x', linewidths=2)
        ax.annotate(name, (ri, rj), color='white', fontsize=8)
    ax.set_title('Final Medium State τ')
    plt.colorbar(im, ax=ax, label='τ')
    
    # 8. Improvement bars
    ax = fig.add_subplot(3, 3, 8)
    improvements = [variance_improvement, rmse_improvement, energy_variance_improvement]
    labels = ['φ Variance', 'φ RMSE', 'Energy Variance']
    colors = ['green' if imp > 20 else 'red' for imp in improvements]
    ax.bar(labels, improvements, color=colors)
    ax.axhline(y=20, color='k', linestyle='--', alpha=0.5, label='20% threshold')
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax.set_ylabel('Improvement (%)')
    ax.set_title('Collapse Improvement under τ_osc vs t_sim')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 9. Summary
    ax = fig.add_subplot(3, 3, 9)
    ax.axis('off')
    
    summary = f"""
OSCILLATOR CLOCK COLLAPSE TEST
==============================

Oscillator: dθ/dt = ω₀ + ε|φ|
  ω₀ = 1.0 (fixed)
  ε = 0.1 (weak)

Final oscillator times:
  high_activity: {tau_osc['high_activity'][-1]:.2f} cycles
  transitional: {tau_osc['transitional'][-1]:.2f} cycles
  quiet: {tau_osc['quiet'][-1]:.2f} cycles
  Spread: {tau_osc_spread:.2f} cycles

COLLAPSE QUALITY (lower = better):

φ envelope:
  t_sim variance: {collapse_t_sim['variance']:.4f}
  τ_osc variance: {collapse_tau_osc['variance']:.4f}
  Improvement: {variance_improvement:.1f}%

Energy:
  t_sim variance: {collapse_energy_t_sim['variance']:.4f}
  τ_osc variance: {collapse_energy_tau_osc['variance']:.4f}
  Improvement: {energy_variance_improvement:.1f}%

VERDICT: {verdict_short}
"""
    
    color = 'lightgreen' if any_pass else 'lightcoral'
    ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'COLLAPSE TEST: {verdict_short}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/collapse_test.png', dpi=150, bbox_inches='tight')
    print("\nSaved collapse_test.png")
    
    # Save JSON
    with open('/app/backend/qmrt_topology/collapse_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved collapse_test_results.json")
    
    return results


if __name__ == "__main__":
    results = run_collapse_test()
