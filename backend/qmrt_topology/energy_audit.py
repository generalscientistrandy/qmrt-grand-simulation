#!/usr/bin/env python3
"""
QMRT Energy Audit / Numerical Stability Check
==============================================

The phase diagram showed E_ret > 1 everywhere, meaning the solver pumps energy.
This audit checks:

1. Energy growth rate vs damping
2. Energy growth rate vs timestep
3. Energy growth rate vs grid resolution
4. Whether attraction survives under stricter numerical conditions

Goal: Understand if attraction is a physical effect or numerical artifact.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


def compute_energy(field, velocity):
    """Total energy in the field."""
    return np.sum(field**2 + velocity**2)


def run_energy_test(
    size: int = 80,
    n_steps: int = 400,
    alpha: float = 0.0,
    damping: float = 0.01,
    dt: float = 0.04,
    two_pulse: bool = False,
):
    """
    Run simulation tracking energy evolution.
    """
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    center = size / 2
    packet_width = 4.0
    amplitude = 3.0
    
    if two_pulse:
        sep_pixels = 0.3 * size / 2
        pos_A = np.array([center, center - sep_pixels])
        pos_B = np.array([center, center + sep_pixels])
        
        for i in range(size):
            for j in range(size):
                r_A = np.sqrt((i - pos_A[0])**2 + (j - pos_A[1])**2)
                r_B = np.sqrt((i - pos_B[0])**2 + (j - pos_B[1])**2)
                
                if r_A < 4 * packet_width:
                    velocity[i, j] += amplitude * np.exp(-r_A**2 / (2 * packet_width**2))
                if r_B < 4 * packet_width:
                    velocity[i, j] += amplitude * np.exp(-r_B**2 / (2 * packet_width**2))
        
        initial_sep = np.linalg.norm(pos_A - pos_B)
    else:
        for i in range(size):
            for j in range(size):
                r = np.sqrt((i - center)**2 + (j - center)**2)
                if r < 4 * packet_width:
                    velocity[i, j] = amplitude * np.exp(-r**2 / (2 * packet_width**2))
        initial_sep = 0.0
    
    c_0 = 2.0
    
    initial_energy = compute_energy(field, velocity)
    energy_history = [initial_energy]
    
    for t in range(n_steps):
        energy_density = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy_density, sigma=2.0)
        
        rho_max = np.max(energy_smooth) + 1e-10
        c_eff = c_0 * (1 - alpha * energy_smooth / rho_max)
        c_eff = np.clip(c_eff, 0.3, c_0)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        if t % 10 == 0:
            energy_history.append(compute_energy(field, velocity))
    
    energy_history = np.array(energy_history)
    
    # Final separation for two-pulse
    if two_pulse:
        energy_density = field**2 + velocity**2
        energy_for_peaks = energy_density.copy()
        
        peak_A_idx = np.unravel_index(np.argmax(energy_for_peaks), energy_density.shape)
        
        for di in range(-12, 13):
            for dj in range(-12, 13):
                ni, nj = peak_A_idx[0] + di, peak_A_idx[1] + dj
                if 0 <= ni < size and 0 <= nj < size:
                    energy_for_peaks[ni, nj] = 0
        
        peak_B_idx = np.unravel_index(np.argmax(energy_for_peaks), energy_density.shape)
        final_sep = np.linalg.norm(np.array(peak_A_idx) - np.array(peak_B_idx))
        delta_sep = final_sep - initial_sep
    else:
        final_sep = 0.0
        delta_sep = 0.0
    
    return {
        'initial_energy': initial_energy,
        'final_energy': energy_history[-1],
        'energy_ratio': energy_history[-1] / initial_energy,
        'energy_history': energy_history,
        'delta_sep': delta_sep,
    }


def run_energy_audit():
    """
    Main energy audit.
    """
    print("=" * 70)
    print("ENERGY AUDIT / NUMERICAL STABILITY CHECK")
    print("=" * 70)
    print("Checking if energy growth is physical or numerical artifact")
    print()
    
    results = {}
    
    # Test 1: Energy vs Damping
    print("Test 1: Energy growth vs Damping (α=0)...")
    dampings = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]
    
    for damp in dampings:
        result = run_energy_test(damping=damp, alpha=0.0)
        results[f'damp_{damp}'] = result
        print(f"  γ={damp:.3f}: E_ratio={result['energy_ratio']:.3f}")
    
    # Test 2: Energy vs Timestep
    print("\nTest 2: Energy growth vs Timestep (α=0, γ=0.01)...")
    timesteps = [0.01, 0.02, 0.04, 0.08]
    
    for dt in timesteps:
        n_steps = int(400 * 0.04 / dt)  # Keep total time constant
        result = run_energy_test(damping=0.01, alpha=0.0, dt=dt, n_steps=n_steps)
        results[f'dt_{dt}'] = result
        print(f"  dt={dt:.3f}: E_ratio={result['energy_ratio']:.3f}")
    
    # Test 3: Energy vs Grid Size
    print("\nTest 3: Energy growth vs Grid Size (α=0, γ=0.01)...")
    sizes = [60, 80, 100, 120]
    
    for size in sizes:
        result = run_energy_test(size=size, damping=0.01, alpha=0.0)
        results[f'size_{size}'] = result
        print(f"  N={size}: E_ratio={result['energy_ratio']:.3f}")
    
    # Test 4: Energy with Backreaction
    print("\nTest 4: Energy with Backreaction (γ=0.01)...")
    alphas = [0.0, 0.3, 0.5, 0.7]
    
    for alpha in alphas:
        result = run_energy_test(damping=0.01, alpha=alpha)
        results[f'alpha_{alpha}'] = result
        print(f"  α={alpha}: E_ratio={result['energy_ratio']:.3f}")
    
    # Test 5: Two-pulse attraction under different conditions
    print("\nTest 5: Does attraction survive stricter numerics?...")
    
    print("  Baseline (dt=0.04, γ=0.008, α=0.5):", end=" ")
    baseline = run_energy_test(alpha=0.5, damping=0.008, dt=0.04, two_pulse=True)
    results['2p_baseline'] = baseline
    print(f"Δsep={baseline['delta_sep']:.1f}, E_ratio={baseline['energy_ratio']:.2f}")
    
    print("  Smaller dt (dt=0.02, γ=0.008, α=0.5):", end=" ")
    small_dt = run_energy_test(alpha=0.5, damping=0.008, dt=0.02, n_steps=800, two_pulse=True)
    results['2p_small_dt'] = small_dt
    print(f"Δsep={small_dt['delta_sep']:.1f}, E_ratio={small_dt['energy_ratio']:.2f}")
    
    print("  Higher damping (dt=0.04, γ=0.03, α=0.5):", end=" ")
    high_damp = run_energy_test(alpha=0.5, damping=0.03, dt=0.04, two_pulse=True)
    results['2p_high_damp'] = high_damp
    print(f"Δsep={high_damp['delta_sep']:.1f}, E_ratio={high_damp['energy_ratio']:.2f}")
    
    print("  Conservative (dt=0.02, γ=0.03, α=0.5):", end=" ")
    conservative = run_energy_test(alpha=0.5, damping=0.03, dt=0.02, n_steps=800, two_pulse=True)
    results['2p_conservative'] = conservative
    print(f"Δsep={conservative['delta_sep']:.1f}, E_ratio={conservative['energy_ratio']:.2f}")
    
    # =================================
    # ANALYSIS
    # =================================
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Check energy growth patterns
    damp_ratios = [(d, results[f'damp_{d}']['energy_ratio']) for d in dampings]
    dt_ratios = [(dt, results[f'dt_{dt}']['energy_ratio']) for dt in timesteps]
    
    print("\nEnergy growth behavior:")
    
    # Does higher damping reduce energy growth?
    damp_correlation = np.corrcoef([d[0] for d in damp_ratios], [d[1] for d in damp_ratios])[0, 1]
    print(f"  Corr(damping, E_ratio): {damp_correlation:.3f}")
    if damp_correlation < -0.5:
        print("  >>> Higher damping reduces energy growth (as expected)")
    elif damp_correlation > 0.5:
        print("  >>> WARNING: Higher damping increases energy?!")
    
    # Does smaller timestep reduce energy growth?
    dt_correlation = np.corrcoef([d[0] for d in dt_ratios], [d[1] for d in dt_ratios])[0, 1]
    print(f"  Corr(timestep, E_ratio): {dt_correlation:.3f}")
    if dt_correlation > 0.5:
        print("  >>> Smaller timestep reduces energy growth (numerical stability)")
    elif dt_correlation < -0.5:
        print("  >>> WARNING: Smaller timestep increases energy?!")
    
    # Does attraction survive under stricter conditions?
    print("\nAttraction survival:")
    attraction_baseline = baseline['delta_sep']
    attraction_conservative = conservative['delta_sep']
    
    attraction_survives = attraction_conservative < -5  # Still attracting
    print(f"  Baseline: Δsep = {attraction_baseline:.1f}")
    print(f"  Conservative: Δsep = {attraction_conservative:.1f}")
    
    if attraction_survives:
        print("  >>> ATTRACTION SURVIVES stricter numerics!")
        print("  >>> This suggests it's a PHYSICAL effect, not numerical artifact")
    else:
        print("  >>> Attraction disappears under stricter numerics")
        print("  >>> Caution: may be partially numerical")
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 12))
    
    # Energy ratio vs damping
    ax = fig.add_subplot(2, 4, 1)
    ax.plot(dampings, [results[f'damp_{d}']['energy_ratio'] for d in dampings], 'bo-', linewidth=2)
    ax.axhline(y=1, color='r', linestyle='--', label='E conserved')
    ax.set_xlabel('Damping γ')
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Energy Ratio vs Damping')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Energy ratio vs timestep
    ax = fig.add_subplot(2, 4, 2)
    ax.plot(timesteps, [results[f'dt_{dt}']['energy_ratio'] for dt in timesteps], 'go-', linewidth=2)
    ax.axhline(y=1, color='r', linestyle='--', label='E conserved')
    ax.set_xlabel('Timestep dt')
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Energy Ratio vs Timestep')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Energy ratio vs grid size
    ax = fig.add_subplot(2, 4, 3)
    ax.plot(sizes, [results[f'size_{s}']['energy_ratio'] for s in sizes], 'mo-', linewidth=2)
    ax.axhline(y=1, color='r', linestyle='--', label='E conserved')
    ax.set_xlabel('Grid Size N')
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Energy Ratio vs Grid Size')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Energy ratio vs α
    ax = fig.add_subplot(2, 4, 4)
    ax.plot(alphas, [results[f'alpha_{a}']['energy_ratio'] for a in alphas], 'co-', linewidth=2)
    ax.axhline(y=1, color='r', linestyle='--', label='E conserved')
    ax.set_xlabel('Backreaction α')
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Energy Ratio vs Backreaction')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Two-pulse comparison
    ax = fig.add_subplot(2, 4, 5)
    configs = ['Baseline', 'Small dt', 'High damp', 'Conservative']
    keys = ['2p_baseline', '2p_small_dt', '2p_high_damp', '2p_conservative']
    delta_seps = [results[k]['delta_sep'] for k in keys]
    
    colors = ['green' if d < 0 else 'red' for d in delta_seps]
    ax.bar(configs, delta_seps, color=colors)
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.5)
    ax.set_ylabel('ΔSeparation')
    ax.set_title('Attraction Under Different Conditions')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Energy ratios for two-pulse
    ax = fig.add_subplot(2, 4, 6)
    e_ratios = [results[k]['energy_ratio'] for k in keys]
    ax.bar(configs, e_ratios, color='purple', alpha=0.7)
    ax.axhline(y=1, color='r', linestyle='--', label='E conserved')
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Energy Ratio (Two-Pulse)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Summary panel
    ax = fig.add_subplot(2, 4, 7)
    ax.axis('off')
    
    summary_text = f"""
ENERGY AUDIT SUMMARY
====================

Energy behavior:
  Corr(damping, E): {damp_correlation:.2f}
  Corr(timestep, E): {dt_correlation:.2f}

Current solver:
  E grows even with damping
  {'Growth decreases with dt' if dt_correlation > 0 else 'Growth increases with dt?!'}

This means:
  The solver is NOT energy-conserving
  Results should be interpreted as
  "transport behavior" not "energy dynamics"

Two-pulse attraction:
  Baseline: Δsep = {attraction_baseline:.1f}
  Conservative: Δsep = {attraction_conservative:.1f}
  
  {'>>> ATTRACTION SURVIVES' if attraction_survives else '>>> Attraction is numerical'}
"""
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Verdict panel
    ax = fig.add_subplot(2, 4, 8)
    ax.axis('off')
    
    if attraction_survives:
        verdict = "PHYSICAL"
        color = 'lightgreen'
        explanation = """
The attraction effect SURVIVES
stricter numerical conditions.

This suggests it is a genuine
physical effect of the backreaction
mechanism, not a numerical artifact.

However, the energy non-conservation
means we should:
- Focus on structural/transport
  behavior (strong)
- Be cautious about energy-based
  claims (weaker)
"""
    else:
        verdict = "NUMERICAL?"
        color = 'lightyellow'
        explanation = """
The attraction effect WEAKENS
under stricter conditions.

This suggests it may be partially
a numerical artifact of energy
pumping by the solver.

To resolve:
- Implement symplectic integrator
- Use energy-conserving scheme
- Verify with different solvers
"""
    
    verdict_text = f"""
VERDICT: {verdict}
{'='*30}
{explanation}
"""
    ax.text(0.5, 0.5, verdict_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='center', horizontalalignment='center',
           fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle('ENERGY AUDIT: Numerical Stability Check', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/energy_audit.png', dpi=150, bbox_inches='tight')
    print("\nSaved energy_audit.png")
    
    # Save results
    summary = {
        'damping_correlation': float(damp_correlation),
        'timestep_correlation': float(dt_correlation),
        'attraction_survives': bool(attraction_survives),
        'two_pulse_results': {
            'baseline': {
                'delta_sep': float(baseline['delta_sep']),
                'energy_ratio': float(baseline['energy_ratio']),
            },
            'conservative': {
                'delta_sep': float(conservative['delta_sep']),
                'energy_ratio': float(conservative['energy_ratio']),
            },
        },
        'verdict': 'physical' if attraction_survives else 'numerical',
    }
    
    with open('/app/backend/qmrt_topology/energy_audit_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved energy_audit_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_energy_audit()
    
    print("\n" + "=" * 70)
    print("ENERGY AUDIT COMPLETE")
    print("=" * 70)
    print(f"Verdict: {result['verdict'].upper()}")
    print(f"Attraction survives stricter numerics: {result['attraction_survives']}")
