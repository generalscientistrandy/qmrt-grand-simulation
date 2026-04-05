#!/usr/bin/env python3
"""
QMRT Tanh Coupling Full Revalidation
=====================================

Re-run the entire core test suite with tanh-saturating backreaction
and compare against the original linear coupling.

TANH COUPLING:
  c_eff = c₀ × (1 - 0.5 × tanh(α × ρ/ρ_max))
  
Properties:
  - Bounded: c_eff ∈ [0.5c₀, c₀]
  - Monotone: higher ρ → lower c_eff
  - Saturating: strong response, no runaway

TESTS TO RUN:
1. Energy behavior
2. Metric emergence (wave vs geodesic)
3. Causal cone confinement
4. Lensing analog
5. Pulse attraction
6. Phase diagram snapshot

COMPARISON OUTPUT:
  Property          | Original | Tanh
  ------------------|----------|------
  Energy ratio      |          |
  Metric error      |          |
  Cone confinement  |          |
  Lensing Δx        |          |
  Attraction Δsep   |          |
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


def compute_c_eff(energy_smooth, c_0, alpha, rho_max, law='tanh'):
    """Compute c_eff using specified coupling law."""
    rho_norm = energy_smooth / (rho_max + 1e-10)
    
    if law == 'original':
        c_eff = c_0 * (1 - alpha * rho_norm)
        c_eff = np.clip(c_eff, 0.3, c_0)
    elif law == 'tanh':
        c_eff = c_0 * (1 - 0.5 * np.tanh(alpha * rho_norm))
    else:
        raise ValueError(f"Unknown law: {law}")
    
    return c_eff


# =====================================================
# TEST 1: ENERGY BEHAVIOR
# =====================================================
def test_energy(law, alpha=2.0):
    """Test energy conservation."""
    size = 80
    n_steps = 400
    
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    center = size / 2
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - center)**2 + (j - center)**2)
            if r < 16:
                velocity[i, j] = 3.0 * np.exp(-r**2 / 32)
    
    dt = 0.04
    c_0 = 2.0
    initial_energy = np.sum(field**2 + velocity**2)
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        velocity += c_eff**2 * lap * dt
        field += velocity * dt
    
    final_energy = np.sum(field**2 + velocity**2)
    return final_energy / initial_energy


# =====================================================
# TEST 2: METRIC EMERGENCE (simplified)
# =====================================================
def test_metric_emergence(law, alpha=2.0):
    """
    Test if wave packet follows geodesic path.
    Returns average deviation from geodesic.
    """
    size = 100
    n_steps = 300
    
    # Create c_eff field with gradient
    c_eff_base = np.ones((size, size)) * 2.0
    for i in range(size):
        for j in range(size):
            y_norm = (j - size/2) / (size/4)
            c_eff_base[i, j] = 2.0 - 0.5 * (1 + np.tanh(y_norm)) / 2
    
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    # Start wave packet
    start = np.array([size * 0.2, size * 0.5])
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - start[0])**2 + (j - start[1])**2)
            if r < 12:
                velocity[i, j] = 3.0 * np.exp(-r**2 / 32)
    
    dt = 0.04
    c_0 = 2.0
    damping = 0.008
    
    # Track wave peak
    wave_path = [start.copy()]
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        # Combine base field with backreaction
        c_eff = c_eff_base * (1 - 0.3 * energy_smooth / rho_max) if law == 'original' else \
                c_eff_base * (1 - 0.25 * np.tanh(alpha * energy_smooth / rho_max))
        c_eff = np.clip(c_eff, 0.3, 2.5)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        velocity += (c_eff**2 * lap - damping * velocity) * dt
        field += velocity * dt
        
        if t % 10 == 0:
            energy = field**2 + velocity**2
            if np.max(energy) > 0.01:
                peak_idx = np.unravel_index(np.argmax(energy), energy.shape)
                wave_path.append(np.array(peak_idx, dtype=float))
    
    wave_path = np.array(wave_path)
    
    # Compute geodesic (straight line in x, follows c_eff gradient in y)
    # Simplified: measure deviation from straight horizontal path
    if len(wave_path) > 5:
        y_deviation = np.std(wave_path[:, 1] - wave_path[0, 1])
        x_progress = wave_path[-1, 0] - wave_path[0, 0]
        # Metric error: how much it deviates from expected bending
        metric_error = y_deviation / (x_progress + 1) * 10
    else:
        metric_error = 99.0
    
    return metric_error


# =====================================================
# TEST 3: CAUSAL CONE CONFINEMENT
# =====================================================
def test_causal_cone(law, alpha=2.0):
    """Test energy confinement within causal cone."""
    size = 100
    n_steps = 200
    
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    # Point source at center
    center = size // 2
    velocity[center, center] = 10.0
    
    dt = 0.04
    c_0 = 2.0
    damping = 0.005
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        velocity += (c_eff**2 * lap - damping * velocity) * dt
        field += velocity * dt
    
    # Compute energy in cone vs outside
    energy = field**2 + velocity**2
    total_time = n_steps * dt
    cone_radius = c_0 * total_time
    
    y_coords, x_coords = np.meshgrid(range(size), range(size))
    r = np.sqrt((x_coords - center)**2 + (y_coords - center)**2)
    
    energy_in_cone = np.sum(energy[r <= cone_radius])
    energy_total = np.sum(energy)
    
    confinement = energy_in_cone / (energy_total + 1e-10) * 100
    return confinement


# =====================================================
# TEST 4: LENSING ANALOG
# =====================================================
def test_lensing(law, alpha=2.0):
    """Test gravitational lensing analog."""
    size = 150
    n_steps = 600
    
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    # Lens
    lens_pos = np.array([size * 0.5, size * 0.6])
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - lens_pos[0])**2 + (j - lens_pos[1])**2)
            if r < 24:
                field[i, j] = 8.0 * np.exp(-r**2 / 72)
    
    # Probe
    probe_start = np.array([size * 0.5 + 15, size * 0.15])
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - probe_start[0])**2 + (j - probe_start[1])**2)
            if r < 12:
                velocity[i, j] += 0.5 * np.exp(-r**2 / 18)
    
    dt = 0.04
    c_0 = 2.0
    damping = 0.006
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        velocity += (c_eff**2 * lap - damping * velocity) * dt
        field += velocity * dt
    
    # Find probe
    energy = field**2 + velocity**2
    probe_energy = energy.copy()
    li, lj = int(lens_pos[0]), int(lens_pos[1])
    for di in range(-24, 25):
        for dj in range(-24, 25):
            ni, nj = li + di, lj + dj
            if 0 <= ni < size and 0 <= nj < size:
                probe_energy[ni, nj] = 0
    
    if np.max(probe_energy) > 0.01:
        probe_idx = np.unravel_index(np.argmax(probe_energy), probe_energy.shape)
        deflection = probe_idx[0] - probe_start[0]
    else:
        deflection = 0
    
    return deflection


# =====================================================
# TEST 5: PULSE ATTRACTION
# =====================================================
def test_attraction(law, alpha=2.0):
    """Test two-pulse attraction."""
    size = 100
    n_steps = 500
    
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    center = size / 2
    sep_pixels = 15
    
    for i in range(size):
        for j in range(size):
            r_A = np.sqrt((i - center)**2 + (j - (center - sep_pixels))**2)
            r_B = np.sqrt((i - center)**2 + (j - (center + sep_pixels))**2)
            if r_A < 16:
                velocity[i, j] += 3.0 * np.exp(-r_A**2 / 32)
            if r_B < 16:
                velocity[i, j] += 3.0 * np.exp(-r_B**2 / 32)
    
    initial_sep = 2 * sep_pixels
    dt = 0.04
    c_0 = 2.0
    damping = 0.008
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        velocity += (c_eff**2 * lap - damping * velocity) * dt
        field += velocity * dt
    
    # Find peaks
    energy = field**2 + velocity**2
    energy_for_peaks = energy.copy()
    peak_A = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
    for di in range(-12, 13):
        for dj in range(-12, 13):
            ni, nj = peak_A[0] + di, peak_A[1] + dj
            if 0 <= ni < size and 0 <= nj < size:
                energy_for_peaks[ni, nj] = 0
    peak_B = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
    
    final_sep = np.sqrt((peak_A[0] - peak_B[0])**2 + (peak_A[1] - peak_B[1])**2)
    return final_sep - initial_sep


# =====================================================
# TEST 6: PHASE DIAGRAM SNAPSHOT
# =====================================================
def test_phase_diagram(law, alpha=2.0):
    """Quick phase check: diffusive, wave, or self-focusing."""
    size = 80
    n_steps = 300
    
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    center = size / 2
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - center)**2 + (j - center)**2)
            if r < 16:
                velocity[i, j] = 3.0 * np.exp(-r**2 / 32)
    
    dt = 0.04
    c_0 = 2.0
    damping = 0.008
    
    # Track spread
    initial_spread = 8.0  # packet width
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        rho_max = np.max(energy_smooth) + 1e-10
        
        c_eff = compute_c_eff(energy_smooth, c_0, alpha, rho_max, law)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        velocity += (c_eff**2 * lap - damping * velocity) * dt
        field += velocity * dt
    
    # Compute final spread
    energy = field**2 + velocity**2
    total_e = np.sum(energy)
    if total_e > 1e-10:
        y_coords, x_coords = np.meshgrid(range(size), range(size))
        cx = np.sum(x_coords * energy) / total_e
        cy = np.sum(y_coords * energy) / total_e
        r = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
        final_spread = np.sqrt(np.sum(r**2 * energy) / total_e)
    else:
        final_spread = 0
    
    spread_ratio = final_spread / initial_spread
    
    if spread_ratio < 0.8:
        return 'SELF-FOCUSING'
    elif spread_ratio > 2.0:
        return 'DIFFUSIVE'
    else:
        return 'WAVE'


# =====================================================
# MAIN REVALIDATION
# =====================================================
def run_revalidation():
    """Full revalidation: Original vs Tanh."""
    print("=" * 70)
    print("TANH COUPLING FULL REVALIDATION")
    print("=" * 70)
    print("Comparing original vs tanh-saturating backreaction")
    print()
    print("Tanh: c_eff = c₀ × (1 - 0.5 × tanh(α × ρ/ρ_max))")
    print("α = 2.0 for tanh, α = 0.5 for original")
    print()
    
    results = {'original': {}, 'tanh': {}}
    
    # Test 1: Energy
    print("Test 1: Energy Behavior...")
    for law in ['original', 'tanh']:
        alpha = 0.5 if law == 'original' else 2.0
        ratio = test_energy(law, alpha)
        results[law]['energy_ratio'] = ratio
        print(f"  {law}: E_ratio = {ratio:.2f}")
    
    # Test 2: Metric Emergence
    print("\nTest 2: Metric Emergence...")
    for law in ['original', 'tanh']:
        alpha = 0.5 if law == 'original' else 2.0
        error = test_metric_emergence(law, alpha)
        results[law]['metric_error'] = error
        print(f"  {law}: metric_error = {error:.2f}")
    
    # Test 3: Causal Cone
    print("\nTest 3: Causal Cone Confinement...")
    for law in ['original', 'tanh']:
        alpha = 0.5 if law == 'original' else 2.0
        conf = test_causal_cone(law, alpha)
        results[law]['cone_confinement'] = conf
        print(f"  {law}: confinement = {conf:.1f}%")
    
    # Test 4: Lensing
    print("\nTest 4: Lensing Analog...")
    for law in ['original', 'tanh']:
        alpha = 0.5 if law == 'original' else 2.0
        defl = test_lensing(law, alpha)
        results[law]['lensing_deflection'] = defl
        toward = "TOWARD" if defl < 0 else "away"
        print(f"  {law}: Δx = {defl:+.1f} ({toward})")
    
    # Test 5: Attraction
    print("\nTest 5: Pulse Attraction...")
    for law in ['original', 'tanh']:
        alpha = 0.5 if law == 'original' else 2.0
        delta = test_attraction(law, alpha)
        results[law]['attraction_delta'] = delta
        status = "ATTRACT" if delta < -5 else "spread"
        print(f"  {law}: Δsep = {delta:+.1f} ({status})")
    
    # Test 6: Phase
    print("\nTest 6: Phase Diagram...")
    for law in ['original', 'tanh']:
        alpha = 0.5 if law == 'original' else 2.0
        phase = test_phase_diagram(law, alpha)
        results[law]['phase'] = phase
        print(f"  {law}: {phase}")
    
    # =====================================================
    # COMPARISON TABLE
    # =====================================================
    print("\n" + "=" * 70)
    print("COMPARISON TABLE")
    print("=" * 70)
    print()
    print(f"{'Property':<25} {'Original':<15} {'Tanh':<15} {'Winner':<10}")
    print("-" * 65)
    
    # Energy (lower is better)
    e_orig = results['original']['energy_ratio']
    e_tanh = results['tanh']['energy_ratio']
    winner = 'Tanh' if e_tanh < e_orig else 'Original'
    print(f"{'Energy ratio':<25} {e_orig:<15.2f} {e_tanh:<15.2f} {winner:<10}")
    
    # Metric (lower error is better)
    m_orig = results['original']['metric_error']
    m_tanh = results['tanh']['metric_error']
    winner = 'Tanh' if m_tanh < m_orig else ('Tie' if abs(m_tanh - m_orig) < 0.5 else 'Original')
    print(f"{'Metric error':<25} {m_orig:<15.2f} {m_tanh:<15.2f} {winner:<10}")
    
    # Cone (higher is better)
    c_orig = results['original']['cone_confinement']
    c_tanh = results['tanh']['cone_confinement']
    winner = 'Tanh' if c_tanh > c_orig else ('Tie' if abs(c_tanh - c_orig) < 2 else 'Original')
    print(f"{'Cone confinement %':<25} {c_orig:<15.1f} {c_tanh:<15.1f} {winner:<10}")
    
    # Lensing (negative = toward = good)
    l_orig = results['original']['lensing_deflection']
    l_tanh = results['tanh']['lensing_deflection']
    o_toward = l_orig < 0
    t_toward = l_tanh < 0
    winner = 'Both' if o_toward and t_toward else ('Tanh' if t_toward else 'Original')
    print(f"{'Lensing Δx':<25} {l_orig:<+15.1f} {l_tanh:<+15.1f} {winner:<10}")
    
    # Attraction (negative = attract = good)
    a_orig = results['original']['attraction_delta']
    a_tanh = results['tanh']['attraction_delta']
    o_attract = a_orig < -5
    t_attract = a_tanh < -5
    winner = 'Both' if o_attract and t_attract else ('Tanh' if t_attract else 'Original')
    print(f"{'Attraction Δsep':<25} {a_orig:<+15.1f} {a_tanh:<+15.1f} {winner:<10}")
    
    # Phase
    p_orig = results['original']['phase']
    p_tanh = results['tanh']['phase']
    winner = 'Both' if p_orig == p_tanh else 'Different'
    print(f"{'Phase regime':<25} {p_orig:<15} {p_tanh:<15} {winner:<10}")
    
    print("-" * 65)
    
    # =====================================================
    # VERDICT
    # =====================================================
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    # Score
    tanh_better = 0
    tanh_preserved = 0
    
    if e_tanh < e_orig:
        tanh_better += 1
    if l_tanh < 0:
        tanh_preserved += 1
    if a_tanh < -5:
        tanh_preserved += 1
    if c_tanh > 80:
        tanh_preserved += 1
    
    print(f"\nTanh improvements: {tanh_better}/1 (energy)")
    print(f"Tanh preservations: {tanh_preserved}/3 (lensing, attraction, cone)")
    
    if tanh_preserved >= 2 and e_tanh < e_orig:
        print("\n>>> TANH VALIDATED AS NEW BASELINE")
        print(">>> Preserves structural phenomena with better energy behavior")
        verdict = "VALIDATED"
    elif tanh_preserved >= 2:
        print("\n>>> TANH PRESERVES PHYSICS")
        print(">>> Consider as alternative closure")
        verdict = "PRESERVED"
    else:
        print("\n>>> TANH BREAKS SOME PHENOMENA")
        print(">>> Original remains baseline")
        verdict = "REJECTED"
    
    results['verdict'] = verdict
    
    # =====================================================
    # PLOTTING
    # =====================================================
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Energy comparison
    ax = axes[0, 0]
    ax.bar(['Original', 'Tanh'], [e_orig, e_tanh], color=['red', 'blue'])
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Energy Ratio (lower = better)')
    ax.set_ylim(0, max(e_orig, e_tanh) * 1.2)
    
    # Cone confinement
    ax = axes[0, 1]
    ax.bar(['Original', 'Tanh'], [c_orig, c_tanh], color=['red', 'blue'])
    ax.axhline(y=90, color='g', linestyle='--', alpha=0.5, label='90% target')
    ax.set_ylabel('% in cone')
    ax.set_title('Causal Cone Confinement')
    ax.legend()
    
    # Lensing
    ax = axes[0, 2]
    colors = ['green' if l < 0 else 'red' for l in [l_orig, l_tanh]]
    ax.bar(['Original', 'Tanh'], [l_orig, l_tanh], color=colors)
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.5)
    ax.set_ylabel('Vertical Deflection')
    ax.set_title('Lensing (negative = toward)')
    
    # Attraction
    ax = axes[1, 0]
    colors = ['green' if a < -5 else 'red' for a in [a_orig, a_tanh]]
    ax.bar(['Original', 'Tanh'], [a_orig, a_tanh], color=colors)
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.5)
    ax.set_ylabel('ΔSeparation')
    ax.set_title('Attraction (negative = attract)')
    
    # Metric error
    ax = axes[1, 1]
    ax.bar(['Original', 'Tanh'], [m_orig, m_tanh], color=['red', 'blue'])
    ax.set_ylabel('Metric Error')
    ax.set_title('Metric Emergence')
    
    # Summary
    ax = axes[1, 2]
    ax.axis('off')
    
    summary = f"""
REVALIDATION SUMMARY
====================

Energy:
  Original: {e_orig:.1f}x
  Tanh: {e_tanh:.1f}x
  Improvement: {e_orig/e_tanh:.1f}x

Lensing:
  Original: {'✓' if l_orig < 0 else '✗'}
  Tanh: {'✓' if l_tanh < 0 else '✗'}

Attraction:
  Original: {'✓' if a_orig < -5 else '✗'}
  Tanh: {'✓' if a_tanh < -5 else '✗'}

Cone:
  Original: {c_orig:.0f}%
  Tanh: {c_tanh:.0f}%

VERDICT: {verdict}
"""
    ax.text(0.1, 0.9, summary, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', 
                    facecolor='lightgreen' if verdict == 'VALIDATED' else 'lightyellow',
                    alpha=0.5))
    
    plt.suptitle(f'TANH REVALIDATION: {verdict}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/tanh_revalidation.png', dpi=150, bbox_inches='tight')
    print("\nSaved tanh_revalidation.png")
    
    # Save JSON
    with open('/app/backend/qmrt_topology/tanh_revalidation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("Saved tanh_revalidation_results.json")
    
    return results


if __name__ == "__main__":
    results = run_revalidation()
    
    print("\n" + "=" * 70)
    print("REVALIDATION COMPLETE")
    print("=" * 70)
    print(f"Verdict: {results['verdict']}")
