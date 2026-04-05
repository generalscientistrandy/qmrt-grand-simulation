#!/usr/bin/env python3
"""
QMRT Bounded Backreaction Laws Test
=====================================

Problem: The current coupling c_eff = c₀(1 - α·ρ) creates runaway energy growth.

Solution: Test bounded, refractive-style couplings that are:
- Bounded from below
- Monotone
- Refractive-index-like

COUPLING LAWS TO TEST:
----------------------

1. ORIGINAL (baseline):
   c_eff = c₀ × (1 - α × ρ/ρ_max)
   → Unbounded below, can go negative

2. SQRT (refractive):
   c_eff = c₀ / √(1 + α × ρ/ρ_max)
   → Bounded: c_eff ∈ (0, c₀]
   → Similar to optical refractive index

3. LINEAR DENOM:
   c_eff = c₀ / (1 + α × ρ/ρ_max)
   → Bounded: c_eff ∈ (0, c₀]
   → Stronger slowdown than SQRT

4. EXPONENTIAL:
   c_eff = c₀ × exp(-α × ρ/ρ_max)
   → Bounded: c_eff ∈ (0, c₀]
   → Smoothest decay

TESTS TO RUN:
-------------
1. Energy conservation (no damping)
2. Lensing analog
3. Two-pulse attraction
4. Phase behavior

DECISION CRITERION:
-------------------
Prefer the simplest bounded coupling that preserves structural phenomena
while reducing or eliminating runaway energy growth.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


def compute_c_eff(energy_smooth, c_0, alpha, rho_max, law='original'):
    """
    Compute c_eff using different coupling laws.
    """
    rho_norm = energy_smooth / (rho_max + 1e-10)
    
    if law == 'original':
        # c_eff = c₀ × (1 - α × ρ/ρ_max)
        c_eff = c_0 * (1 - alpha * rho_norm)
        c_eff = np.clip(c_eff, 0.3, c_0)
        
    elif law == 'sqrt':
        # c_eff = c₀ / √(1 + α × ρ/ρ_max)
        c_eff = c_0 / np.sqrt(1 + alpha * rho_norm)
        
    elif law == 'linear_denom':
        # c_eff = c₀ / (1 + α × ρ/ρ_max)
        c_eff = c_0 / (1 + alpha * rho_norm)
        
    elif law == 'exponential':
        # c_eff = c₀ × exp(-α × ρ/ρ_max)
        c_eff = c_0 * np.exp(-alpha * rho_norm)
        
    else:
        raise ValueError(f"Unknown law: {law}")
    
    return c_eff


def compute_energy(field, velocity):
    """Total field energy."""
    return np.sum(field**2 + velocity**2)


def run_energy_test(law: str, size: int = 80, n_steps: int = 400, alpha: float = 0.5):
    """
    Test energy conservation with a given coupling law.
    """
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    center = size / 2
    packet_width = 4.0
    amplitude = 3.0
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - center)**2 + (j - center)**2)
            if r < 4 * packet_width:
                velocity[i, j] = amplitude * np.exp(-r**2 / (2 * packet_width**2))
    
    dt = 0.04
    c_0 = 2.0
    damping = 0.0  # No damping for energy test
    
    initial_energy = compute_energy(field, velocity)
    energy_history = [initial_energy]
    
    for t in range(n_steps):
        energy_density = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy_density, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        if t % 10 == 0:
            energy_history.append(compute_energy(field, velocity))
    
    energy_history = np.array(energy_history)
    
    return {
        'initial': initial_energy,
        'final': energy_history[-1],
        'ratio': energy_history[-1] / initial_energy,
        'history': energy_history,
        'max_ratio': np.max(energy_history) / initial_energy,
    }


def run_lensing_test(law: str, size: int = 150, n_steps: int = 600, alpha: float = 0.5):
    """
    Test lensing with a given coupling law.
    """
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    # Lens
    lens_pos = np.array([size * 0.5, size * 0.6])
    lens_width = 6.0
    lens_amplitude = 8.0
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - lens_pos[0])**2 + (j - lens_pos[1])**2)
            if r < 4 * lens_width:
                field[i, j] = lens_amplitude * np.exp(-r**2 / (2 * lens_width**2))
    
    # Probe
    impact_parameter = 0.10
    impact_pixels = impact_parameter * size
    probe_start = np.array([size * 0.5 + impact_pixels, size * 0.15])
    probe_width = 3.0
    probe_amplitude = 0.5
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - probe_start[0])**2 + (j - probe_start[1])**2)
            if r < 4 * probe_width:
                velocity[i, j] += probe_amplitude * np.exp(-r**2 / (2 * probe_width**2))
    
    dt = 0.04
    c_0 = 2.0
    damping = 0.006
    
    probe_positions = [probe_start.copy()]
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        if t % 5 == 0:
            probe_energy = energy.copy()
            lens_mask_radius = int(lens_width * 4)
            li, lj = int(lens_pos[0]), int(lens_pos[1])
            for di in range(-lens_mask_radius, lens_mask_radius + 1):
                for dj in range(-lens_mask_radius, lens_mask_radius + 1):
                    ni, nj = li + di, lj + dj
                    if 0 <= ni < size and 0 <= nj < size:
                        probe_energy[ni, nj] = 0
            
            if np.max(probe_energy) > 0.01:
                probe_idx = np.unravel_index(np.argmax(probe_energy), probe_energy.shape)
                probe_positions.append(np.array(probe_idx, dtype=float))
    
    probe_positions = np.array(probe_positions)
    
    if len(probe_positions) > 10:
        expected_end_x = probe_start[0]
        actual_end_x = probe_positions[-1][0]
        vertical_deflection = actual_end_x - expected_end_x
        bent_toward_lens = vertical_deflection < 0  # Probe above lens should bend down
    else:
        vertical_deflection = 0.0
        bent_toward_lens = False
    
    return {
        'probe_positions': probe_positions,
        'vertical_deflection': vertical_deflection,
        'bent_toward_lens': bent_toward_lens,
    }


def run_attraction_test(law: str, size: int = 100, n_steps: int = 500, alpha: float = 0.5):
    """
    Test two-pulse attraction with a given coupling law.
    """
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    center = size / 2
    sep_pixels = 0.3 * size / 2
    
    pos_A = np.array([center, center - sep_pixels])
    pos_B = np.array([center, center + sep_pixels])
    
    packet_width = 4.0
    amplitude = 3.0
    
    for i in range(size):
        for j in range(size):
            r_A = np.sqrt((i - pos_A[0])**2 + (j - pos_A[1])**2)
            r_B = np.sqrt((i - pos_B[0])**2 + (j - pos_B[1])**2)
            
            if r_A < 4 * packet_width:
                velocity[i, j] += amplitude * np.exp(-r_A**2 / (2 * packet_width**2))
            if r_B < 4 * packet_width:
                velocity[i, j] += amplitude * np.exp(-r_B**2 / (2 * packet_width**2))
    
    dt = 0.04
    c_0 = 2.0
    damping = 0.008
    
    initial_sep = np.linalg.norm(pos_A - pos_B)
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
    
    # Find final separation
    energy = field**2 + velocity**2
    energy_for_peaks = energy.copy()
    
    peak_A_idx = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
    
    for di in range(-12, 13):
        for dj in range(-12, 13):
            ni, nj = peak_A_idx[0] + di, peak_A_idx[1] + dj
            if 0 <= ni < size and 0 <= nj < size:
                energy_for_peaks[ni, nj] = 0
    
    peak_B_idx = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
    final_sep = np.linalg.norm(np.array(peak_A_idx) - np.array(peak_B_idx))
    
    delta_sep = final_sep - initial_sep
    attracted = delta_sep < -5  # Significant attraction
    
    return {
        'initial_sep': initial_sep,
        'final_sep': final_sep,
        'delta_sep': delta_sep,
        'attracted': attracted,
    }


def run_bounded_laws_test():
    """
    Main test: Compare bounded backreaction laws.
    """
    print("=" * 70)
    print("BOUNDED BACKREACTION LAWS TEST")
    print("=" * 70)
    print("Testing bounded, refractive-style couplings")
    print()
    
    laws = ['original', 'sqrt', 'linear_denom', 'exponential']
    law_names = {
        'original': 'c₀(1 - αρ)',
        'sqrt': 'c₀/√(1 + αρ)',
        'linear_denom': 'c₀/(1 + αρ)',
        'exponential': 'c₀·exp(-αρ)',
    }
    
    results = {}
    
    # Test 1: Energy conservation
    print("Test 1: Energy Conservation (α=0.5, no damping)...")
    for law in laws:
        print(f"  {law_names[law]}...", end=" ")
        result = run_energy_test(law, alpha=0.5)
        results[f'{law}_energy'] = result
        print(f"E_ratio = {result['ratio']:.4f}, max = {result['max_ratio']:.4f}")
    
    # Test 2: Lensing
    print("\nTest 2: Lensing Analog (α=0.5, b=0.10)...")
    for law in laws:
        print(f"  {law_names[law]}...", end=" ")
        result = run_lensing_test(law, alpha=0.5)
        results[f'{law}_lensing'] = result
        toward = "TOWARD" if result['bent_toward_lens'] else "away"
        print(f"Δx = {result['vertical_deflection']:+.1f}, {toward}")
    
    # Test 3: Two-pulse attraction
    print("\nTest 3: Two-Pulse Attraction (α=0.5)...")
    for law in laws:
        print(f"  {law_names[law]}...", end=" ")
        result = run_attraction_test(law, alpha=0.5)
        results[f'{law}_attraction'] = result
        status = "ATTRACT" if result['attracted'] else "spread"
        print(f"Δsep = {result['delta_sep']:+.1f}, {status}")
    
    # =================================
    # ANALYSIS
    # =================================
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    print("\nComparison Table:")
    print("-" * 60)
    print(f"{'Law':<20} {'E_ratio':<12} {'Lensing':<12} {'Attraction':<12}")
    print("-" * 60)
    
    for law in laws:
        e_ratio = results[f'{law}_energy']['ratio']
        lensing = "TOWARD" if results[f'{law}_lensing']['bent_toward_lens'] else "away"
        attract = "YES" if results[f'{law}_attraction']['attracted'] else "no"
        print(f"{law_names[law]:<20} {e_ratio:<12.4f} {lensing:<12} {attract:<12}")
    
    print("-" * 60)
    
    # Find best law
    best_law = None
    best_score = -1
    
    for law in laws:
        score = 0
        
        # Energy: closer to 1 is better
        e_ratio = results[f'{law}_energy']['ratio']
        if 0.5 < e_ratio < 2.0:
            score += 2
        elif 0.1 < e_ratio < 5.0:
            score += 1
        
        # Lensing: must work
        if results[f'{law}_lensing']['bent_toward_lens']:
            score += 2
        
        # Attraction: must work
        if results[f'{law}_attraction']['attracted']:
            score += 2
        
        if score > best_score:
            best_score = score
            best_law = law
    
    print(f"\nBest law: {law_names[best_law]} (score: {best_score}/6)")
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 12))
    
    # Energy evolution comparison
    ax = fig.add_subplot(2, 3, 1)
    colors = {'original': 'red', 'sqrt': 'blue', 'linear_denom': 'green', 'exponential': 'purple'}
    
    for law in laws:
        history = results[f'{law}_energy']['history']
        times = np.arange(len(history)) * 0.04 * 10
        initial = results[f'{law}_energy']['initial']
        ax.plot(times, history / initial, color=colors[law], linewidth=2, label=law_names[law])
    
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Time')
    ax.set_ylabel('E / E₀')
    ax.set_title('Energy Evolution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Energy ratio bar chart
    ax = fig.add_subplot(2, 3, 2)
    e_ratios = [results[f'{law}_energy']['ratio'] for law in laws]
    bar_colors = ['green' if 0.5 < r < 2.0 else 'red' for r in e_ratios]
    ax.bar([law_names[l] for l in laws], e_ratios, color=bar_colors)
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Final Energy Ratio')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Lensing comparison
    ax = fig.add_subplot(2, 3, 3)
    deflections = [results[f'{law}_lensing']['vertical_deflection'] for law in laws]
    bar_colors = ['green' if d < 0 else 'red' for d in deflections]
    ax.bar([law_names[l] for l in laws], deflections, color=bar_colors)
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.5)
    ax.set_ylabel('Vertical Deflection (pixels)')
    ax.set_title('Lensing: Deflection (negative = toward)')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Attraction comparison
    ax = fig.add_subplot(2, 3, 4)
    delta_seps = [results[f'{law}_attraction']['delta_sep'] for law in laws]
    bar_colors = ['green' if d < -5 else 'red' for d in delta_seps]
    ax.bar([law_names[l] for l in laws], delta_seps, color=bar_colors)
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.5)
    ax.set_ylabel('ΔSeparation (pixels)')
    ax.set_title('Attraction: ΔSep (negative = attract)')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Lensing trajectories
    ax = fig.add_subplot(2, 3, 5)
    for law in laws:
        pos = results[f'{law}_lensing']['probe_positions']
        if len(pos) > 0:
            ax.plot(pos[:, 1], pos[:, 0], color=colors[law], linewidth=2, label=law_names[law])
    
    ax.scatter([90], [75], c='black', s=200, marker='*', zorder=10, label='Lens')
    ax.set_xlabel('Y position')
    ax.set_ylabel('X position')
    ax.set_title('Lensing Trajectories')
    ax.legend(fontsize=8)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    # Summary panel
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary_text = f"""
BOUNDED LAWS COMPARISON
=======================

ORIGINAL: c_eff = c₀(1 - αρ)
  Energy: {results['original_energy']['ratio']:.2f}x
  Lensing: {'✓' if results['original_lensing']['bent_toward_lens'] else '✗'}
  Attract: {'✓' if results['original_attraction']['attracted'] else '✗'}

SQRT: c_eff = c₀/√(1 + αρ)
  Energy: {results['sqrt_energy']['ratio']:.2f}x
  Lensing: {'✓' if results['sqrt_lensing']['bent_toward_lens'] else '✗'}
  Attract: {'✓' if results['sqrt_attraction']['attracted'] else '✗'}

LINEAR: c_eff = c₀/(1 + αρ)
  Energy: {results['linear_denom_energy']['ratio']:.2f}x
  Lensing: {'✓' if results['linear_denom_lensing']['bent_toward_lens'] else '✗'}
  Attract: {'✓' if results['linear_denom_attraction']['attracted'] else '✗'}

EXP: c_eff = c₀·exp(-αρ)
  Energy: {results['exponential_energy']['ratio']:.2f}x
  Lensing: {'✓' if results['exponential_lensing']['bent_toward_lens'] else '✗'}
  Attract: {'✓' if results['exponential_attraction']['attracted'] else '✗'}

>>> BEST: {law_names[best_law]}
"""
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.suptitle('BOUNDED BACKREACTION LAWS TEST', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/bounded_laws.png', dpi=150, bbox_inches='tight')
    print("\nSaved bounded_laws.png")
    
    # Save results
    summary = {
        'best_law': best_law,
        'best_law_name': law_names[best_law],
        'results': {
            law: {
                'energy_ratio': float(results[f'{law}_energy']['ratio']),
                'lensing_toward': bool(results[f'{law}_lensing']['bent_toward_lens']),
                'lensing_deflection': float(results[f'{law}_lensing']['vertical_deflection']),
                'attraction': bool(results[f'{law}_attraction']['attracted']),
                'delta_sep': float(results[f'{law}_attraction']['delta_sep']),
            }
            for law in laws
        },
        'recommendation': (
            f"The {law_names[best_law]} coupling is recommended: it preserves structural phenomena "
            f"(lensing, attraction) while providing {'better' if results[f'{best_law}_energy']['ratio'] < 2 else 'some'} "
            f"energy behavior (E_ratio = {results[f'{best_law}_energy']['ratio']:.2f})."
        )
    }
    
    with open('/app/backend/qmrt_topology/bounded_laws_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved bounded_laws_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_bounded_laws_test()
    
    print("\n" + "=" * 70)
    print("BOUNDED LAWS TEST COMPLETE")
    print("=" * 70)
    print(f"Best law: {result['best_law_name']}")
    print(f"\n{result['recommendation']}")
