#!/usr/bin/env python3
"""
QMRT Lifetime-Based Collapse Test
===================================

KEY QUESTION:
Does the decay clock merely differentiate regions, or does it also
parameterize dynamics better than raw t_sim?

TEST:
- Measure an independent observable in different regions
- Reparameterize by τ_decay = t_sim / ⟨T_region⟩
- Compare collapse quality under t_sim vs τ_decay

If decay-based reparameterization helps, the clock branch gets much stronger.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import interp1d
import json


class LifetimeCollapseSimulator:
    """
    Simulator for testing lifetime-based collapse.
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
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        self.t_sim = 0.0
        
        self.probes = {}
        self.history = {'t_sim': []}
    
    def set_probes(self, probes: dict):
        self.probes = probes
        for name in probes:
            self.history[f'phi_envelope_{name}'] = []
            self.history[f'energy_{name}'] = []
            self.history[f'tau_{name}'] = []
    
    def compute_c_eff(self):
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
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
        
        self.t_sim += self.dt
    
    def record_history(self):
        self.history['t_sim'].append(self.t_sim)
        
        for name, (ri, rj) in self.probes.items():
            # Phi envelope
            window = 3
            i0, i1 = max(0, ri-window), min(self.size, ri+window+1)
            j0, j1 = max(0, rj-window), min(self.size, rj+window+1)
            phi_local = self.phi[i0:i1, j0:j1]
            phi_envelope = np.sqrt(np.mean(phi_local**2))
            
            # Local energy
            energy = self.phi[ri, rj]**2 + self.phi_dot[ri, rj]**2
            
            # Local tau
            tau_local = self.tau[ri, rj]
            
            self.history[f'phi_envelope_{name}'].append(phi_envelope)
            self.history[f'energy_{name}'].append(energy)
            self.history[f'tau_{name}'].append(tau_local)
    
    def add_pulse(self, center, amplitude=3.0, width=4.0, velocity=True):
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    if velocity:
                        self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
                    else:
                        self.phi[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
    
    def add_background(self, region_type: str, center: tuple):
        if region_type == 'high_structure':
            for i in range(self.size):
                for j in range(self.size):
                    r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                    if r < 15:
                        self.phi[i, j] += 2.0 * np.exp(-r**2 / 50)
        elif region_type == 'transitional':
            for i in range(self.size):
                for j in range(self.size):
                    r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                    if r < 10:
                        self.phi[i, j] += 0.5 * np.exp(-r**2 / 30)


def compute_collapse_quality(time_arrays, obs_arrays, labels):
    """
    Compute collapse quality across regions.
    Returns variance when interpolated onto common time grid.
    """
    # Find common range
    t_mins = [np.min(t) for t in time_arrays]
    t_maxs = [np.max(t) for t in time_arrays]
    t_common_min = max(t_mins)
    t_common_max = min(t_maxs)
    
    if t_common_max <= t_common_min:
        return {'variance': np.nan, 'rmse': np.nan}
    
    # Common grid
    n_points = 80
    t_common = np.linspace(t_common_min, t_common_max, n_points)
    
    # Interpolate
    interpolated = []
    for t_arr, obs_arr in zip(time_arrays, obs_arrays):
        sort_idx = np.argsort(t_arr)
        t_sorted = np.array(t_arr)[sort_idx]
        obs_sorted = np.array(obs_arr)[sort_idx]
        
        try:
            f = interp1d(t_sorted, obs_sorted, kind='linear',
                        bounds_error=False, fill_value='extrapolate')
            interpolated.append(f(t_common))
        except:
            return {'variance': np.nan, 'rmse': np.nan}
    
    if len(interpolated) < 2:
        return {'variance': np.nan, 'rmse': np.nan}
    
    stacked = np.vstack(interpolated)
    variance = float(np.mean(np.var(stacked, axis=0)))
    
    # RMSE between curves
    rmse_sum = 0
    count = 0
    for i in range(len(interpolated)):
        for j in range(i+1, len(interpolated)):
            rmse_sum += np.sqrt(np.mean((interpolated[i] - interpolated[j])**2))
            count += 1
    rmse = rmse_sum / count if count > 0 else np.nan
    
    return {'variance': variance, 'rmse': float(rmse)}


def run_lifetime_collapse_test():
    """
    Test if lifetime-based reparameterization improves collapse.
    """
    print("=" * 70)
    print("LIFETIME-BASED COLLAPSE TEST")
    print("=" * 70)
    print()
    print("Question: Does τ_decay = t_sim / ⟨T⟩ parameterize better than t_sim?")
    print()
    
    # Region-specific mean lifetimes from decay clock test
    # These are the measured values
    mean_lifetimes = {
        'high_structure': 9.13,
        'transitional': 7.29,
        'quiet': 6.98,
    }
    
    regions = {
        'high_structure': (50, 50),
        'transitional': (50, 25),
        'quiet': (25, 25),
    }
    
    # Run simulation with dynamics
    sim = LifetimeCollapseSimulator(size=100, beta=1.0, lambda_relax=1.5)
    sim.set_probes(regions)
    
    # Add background structure for each region
    for region, center in regions.items():
        sim.add_background(region, center)
    
    # Settle
    for _ in range(50):
        sim.step()
    
    # Add propagating pulses to create dynamics
    for pulse_time in range(6):
        sim.add_pulse([50, 50], amplitude=2.5, velocity=True)
        for t in range(100):
            sim.step()
            if t % 4 == 0:
                sim.record_history()
    
    # Extract data
    t_sim = np.array(sim.history['t_sim'])
    
    # Compute τ_decay for each region
    tau_decay = {}
    phi_envelope = {}
    energy = {}
    
    for region in regions:
        # τ_decay = t_sim / ⟨T⟩ (normalized by region's mean lifetime)
        tau_decay[region] = t_sim / mean_lifetimes[region]
        phi_envelope[region] = np.array(sim.history[f'phi_envelope_{region}'])
        energy[region] = np.array(sim.history[f'energy_{region}'])
    
    region_list = list(regions.keys())
    
    # Test 1: Phi envelope collapse
    print("1. PHI ENVELOPE COLLAPSE")
    print("-" * 50)
    
    # Under t_sim
    t_arrays_sim = [t_sim] * 3
    phi_arrays = [phi_envelope[r] for r in region_list]
    collapse_t_sim = compute_collapse_quality(t_arrays_sim, phi_arrays, region_list)
    
    # Under τ_decay
    t_arrays_decay = [tau_decay[r] for r in region_list]
    collapse_tau_decay = compute_collapse_quality(t_arrays_decay, phi_arrays, region_list)
    
    print(f"  Under t_sim:    variance = {collapse_t_sim['variance']:.6f}")
    print(f"  Under τ_decay:  variance = {collapse_tau_decay['variance']:.6f}")
    
    if collapse_t_sim['variance'] > 0:
        phi_improvement = (collapse_t_sim['variance'] - collapse_tau_decay['variance']) / collapse_t_sim['variance'] * 100
    else:
        phi_improvement = 0
    
    print(f"  Improvement: {phi_improvement:.1f}%")
    
    # Test 2: Energy collapse
    print("\n2. ENERGY COLLAPSE")
    print("-" * 50)
    
    energy_arrays = [energy[r] for r in region_list]
    collapse_energy_t_sim = compute_collapse_quality(t_arrays_sim, energy_arrays, region_list)
    collapse_energy_tau_decay = compute_collapse_quality(t_arrays_decay, energy_arrays, region_list)
    
    print(f"  Under t_sim:    variance = {collapse_energy_t_sim['variance']:.6f}")
    print(f"  Under τ_decay:  variance = {collapse_energy_tau_decay['variance']:.6f}")
    
    if collapse_energy_t_sim['variance'] > 0:
        energy_improvement = (collapse_energy_t_sim['variance'] - collapse_energy_tau_decay['variance']) / collapse_energy_t_sim['variance'] * 100
    else:
        energy_improvement = 0
    
    print(f"  Improvement: {energy_improvement:.1f}%")
    
    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    phi_pass = phi_improvement > 10
    energy_pass = energy_improvement > 10
    any_pass = phi_pass or energy_pass
    
    print(f"\n  Phi envelope improves >10%: {'PASS' if phi_pass else 'FAIL'} ({phi_improvement:.1f}%)")
    print(f"  Energy improves >10%: {'PASS' if energy_pass else 'FAIL'} ({energy_improvement:.1f}%)")
    
    if any_pass:
        verdict = "LIFETIME-BASED REPARAMETERIZATION IMPROVES COLLAPSE"
        verdict_short = "IMPROVES"
    elif phi_improvement > 0 or energy_improvement > 0:
        verdict = "MARGINAL IMPROVEMENT - NOT DECISIVE"
        verdict_short = "MARGINAL"
    else:
        verdict = "LIFETIME REPARAMETERIZATION DOES NOT HELP"
        verdict_short = "NO_IMPROVEMENT"
    
    print(f"\n>>> {verdict}")
    
    # Comparison to oscillator
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"\n  Oscillator collapse improvement: 11.2%")
    print(f"  Decay lifetime collapse improvement: {max(phi_improvement, energy_improvement):.1f}%")
    
    if max(phi_improvement, energy_improvement) > 11.2:
        print("  → Decay clocks are NOW THE BEST temporal branch candidate")
    else:
        print("  → Oscillators remain competitive")
    
    # Plotting
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Phi envelope vs t_sim
    ax = fig.add_subplot(2, 3, 1)
    for region in region_list:
        ax.plot(t_sim, phi_envelope[region], label=region, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('t_sim')
    ax.set_ylabel('φ envelope')
    ax.set_title(f'φ vs t_sim (var={collapse_t_sim["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Phi envelope vs τ_decay
    ax = fig.add_subplot(2, 3, 2)
    for region in region_list:
        ax.plot(tau_decay[region], phi_envelope[region], label=region, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('τ_decay = t_sim / ⟨T⟩')
    ax.set_ylabel('φ envelope')
    ax.set_title(f'φ vs τ_decay (var={collapse_tau_decay["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Energy vs t_sim
    ax = fig.add_subplot(2, 3, 3)
    for region in region_list:
        ax.plot(t_sim, energy[region], label=region, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('t_sim')
    ax.set_ylabel('Energy')
    ax.set_title(f'Energy vs t_sim (var={collapse_energy_t_sim["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Energy vs τ_decay
    ax = fig.add_subplot(2, 3, 4)
    for region in region_list:
        ax.plot(tau_decay[region], energy[region], label=region, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('τ_decay = t_sim / ⟨T⟩')
    ax.set_ylabel('Energy')
    ax.set_title(f'Energy vs τ_decay (var={collapse_energy_tau_decay["variance"]:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Improvement comparison
    ax = fig.add_subplot(2, 3, 5)
    metrics = ['φ envelope', 'Energy']
    improvements = [phi_improvement, energy_improvement]
    colors = ['green' if imp > 10 else 'orange' if imp > 0 else 'red' for imp in improvements]
    ax.bar(metrics, improvements, color=colors)
    ax.axhline(y=10, color='k', linestyle='--', alpha=0.5, label='10% threshold')
    ax.axhline(y=11.2, color='blue', linestyle=':', alpha=0.5, label='Oscillator (11.2%)')
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax.set_ylabel('Improvement (%)')
    ax.set_title('Collapse Improvement: τ_decay vs t_sim')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 6. Summary
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
LIFETIME-BASED COLLAPSE TEST
============================

τ_decay = t_sim / ⟨T_region⟩

Mean lifetimes used:
  high_structure: ⟨T⟩ = {mean_lifetimes['high_structure']:.2f}
  transitional:   ⟨T⟩ = {mean_lifetimes['transitional']:.2f}
  quiet:          ⟨T⟩ = {mean_lifetimes['quiet']:.2f}

Results:
  φ envelope improvement: {phi_improvement:.1f}%
  Energy improvement: {energy_improvement:.1f}%

Comparison:
  Oscillator collapse: 11.2%
  Decay collapse: {max(phi_improvement, energy_improvement):.1f}%

VERDICT: {verdict_short}
"""
    
    color = 'lightgreen' if any_pass else 'lightyellow' if phi_improvement > 0 else 'lightcoral'
    ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'LIFETIME COLLAPSE: {verdict_short}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/lifetime_collapse.png', dpi=150, bbox_inches='tight')
    print("\nSaved lifetime_collapse.png")
    
    # Save JSON
    results_json = {
        'mean_lifetimes': mean_lifetimes,
        'phi_collapse_t_sim': collapse_t_sim,
        'phi_collapse_tau_decay': collapse_tau_decay,
        'phi_improvement_pct': float(phi_improvement),
        'energy_collapse_t_sim': collapse_energy_t_sim,
        'energy_collapse_tau_decay': collapse_energy_tau_decay,
        'energy_improvement_pct': float(energy_improvement),
        'verdict': verdict,
        'verdict_short': verdict_short,
    }
    
    with open('/app/backend/qmrt_topology/lifetime_collapse_results.json', 'w') as f:
        json.dump(results_json, f, indent=2)
    print("Saved lifetime_collapse_results.json")
    
    return results_json


if __name__ == "__main__":
    results = run_lifetime_collapse_test()
