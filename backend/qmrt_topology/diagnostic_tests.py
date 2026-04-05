#!/usr/bin/env python3
"""
QMRT Critical Diagnostic Tests
==============================
Tests to determine the nature of the field-coupled system:

1. Wave vs Diffusion Test — measure radius growth
   - √t growth = diffusive (heat equation)
   - t growth = wave-like (wave equation)

2. Channel Persistence Test — do paths have memory?
   - Inject pulse, let it create structure
   - Inject second pulse at same location
   - Does it follow the prior path?

3. Regime Mapping — parameter scan
   - Dead medium (nothing happens)
   - Diffusive medium (spreading, no structure)
   - Self-organizing (structure forms)
   - Wave-capable (oscillatory propagation)
"""

import numpy as np
import matplotlib.pyplot as plt
from field_coupled_dynamics import CoupledFieldSystem, FieldParams
from scipy.optimize import curve_fit


def measure_pulse_radius(energy_field: np.ndarray, center: tuple, threshold_frac: float = 0.1) -> float:
    """
    Measure the effective radius of an energy pulse.
    Returns the radius containing (1-threshold_frac) of the peak energy.
    """
    cx, cy = center
    max_val = energy_field[int(cx), int(cy)]
    threshold = max_val * threshold_frac
    
    # Find all cells above threshold
    above = np.where(energy_field > threshold)
    if len(above[0]) == 0:
        return 0.0
    
    # Calculate mean distance from center
    distances = np.sqrt((above[0] - cx)**2 + (above[1] - cy)**2)
    return np.mean(distances)


def test_wave_vs_diffusion():
    """
    Test 1: Wave vs Diffusion
    
    Measure how the pulse radius grows over time:
    - Diffusion: r(t) ∝ √t  (heat equation)
    - Wave: r(t) ∝ t (wave equation)
    """
    print("=" * 60)
    print("TEST 1: WAVE VS DIFFUSION")
    print("=" * 60)
    
    np.random.seed(42)
    
    params = FieldParams(
        field_diffusion=0.25,
        field_decay=0.001,
        field_cap=10.0,
        creation_threshold=100.0,  # Disable creation
        creation_rate=0.0,
    )
    
    system = CoupledFieldSystem(size=(60, 60), params=params)
    system.energy_field = np.zeros(system.size)
    
    # Inject sharp pulse at center
    center = (30, 30)
    system.inject_energy_pulse(np.array([30.0, 30.0]), amount=50.0, radius=2.0)
    
    times = []
    radii = []
    
    print("Measuring pulse spread...")
    for t in range(300):
        if t % 20 == 0 and t > 0:
            r = measure_pulse_radius(system.energy_field, center, threshold_frac=0.2)
            times.append(t)
            radii.append(r)
            print(f"  t={t}: radius={r:.2f}")
        
        system.evolve_field(dt=0.1)
    
    times = np.array(times)
    radii = np.array(radii)
    
    # Fit both models
    def diffusion_model(t, D, r0):
        return np.sqrt(4 * D * t + r0**2)
    
    def wave_model(t, v, r0):
        return v * t + r0
    
    try:
        popt_diff, _ = curve_fit(diffusion_model, times, radii, p0=[0.1, 2.0], maxfev=5000)
        diff_fit = diffusion_model(times, *popt_diff)
        diff_residual = np.sum((radii - diff_fit)**2)
        
        popt_wave, _ = curve_fit(wave_model, times, radii, p0=[0.1, 2.0], maxfev=5000)
        wave_fit = wave_model(times, *popt_wave)
        wave_residual = np.sum((radii - wave_fit)**2)
        
        print(f"\nFit results:")
        print(f"  Diffusion (r ~ √t): D={popt_diff[0]:.4f}, residual={diff_residual:.2f}")
        print(f"  Wave (r ~ t): v={popt_wave[0]:.4f}, residual={diff_residual:.2f}")
        
        if diff_residual < wave_residual * 0.8:
            result = "DIFFUSIVE"
            print(f"\n✓ RESULT: {result} — radius grows as √t")
        elif wave_residual < diff_residual * 0.8:
            result = "WAVE-LIKE"
            print(f"\n✓ RESULT: {result} — radius grows as t")
        else:
            result = "MIXED"
            print(f"\n~ RESULT: {result} — neither model clearly dominant")
    except Exception as e:
        print(f"Fit failed: {e}")
        result = "UNKNOWN"
        popt_diff = [0, 0]
        popt_wave = [0, 0]
        diff_fit = radii
        wave_fit = radii
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(times, radii, c='blue', s=50, label='Measured', zorder=3)
    ax.plot(times, diff_fit, 'g--', linewidth=2, label=f'Diffusion fit (r~√t)')
    ax.plot(times, wave_fit, 'r--', linewidth=2, label=f'Wave fit (r~t)')
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Pulse Radius', fontsize=12)
    ax.set_title(f'Wave vs Diffusion Test\nResult: {result}', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_wave_vs_diffusion.png', dpi=150)
    print("\nSaved test_wave_vs_diffusion.png")
    
    return result


def test_channel_persistence():
    """
    Test 2: Channel Persistence
    
    Does the medium remember prior transport paths?
    - Inject pulse, let it create structure
    - Inject second pulse at same location
    - Measure if second pulse follows prior path
    """
    print("\n" + "=" * 60)
    print("TEST 2: CHANNEL PERSISTENCE")
    print("=" * 60)
    
    np.random.seed(42)
    
    params = FieldParams(
        field_diffusion=0.15,
        field_decay=0.002,
        field_cap=5.0,
        defect_field_strength=0.4,
        field_force_strength=0.6,
        creation_threshold=1.5,
        creation_rate=0.003,
        creation_cost=0.6,
        annihilation_injection=0.5,
    )
    
    system = CoupledFieldSystem(size=(40, 40), params=params)
    system.energy_field = np.random.uniform(0.5, 1.0, system.size)
    system.create_random_pairs(8)
    
    # Phase 1: Run system to establish baseline structure
    print("Phase 1: Establishing baseline structure...")
    for i in range(200):
        system.step(dt=0.1)
    
    baseline_field = system.field.copy()
    
    # Phase 2: Inject pulse at corner
    print("Phase 2: Injecting first pulse at (10, 10)...")
    system.inject_energy_pulse(np.array([10.0, 10.0]), amount=10.0, radius=3.0)
    
    # Let it propagate
    field_after_first = []
    for i in range(100):
        system.step(dt=0.1)
        if i in [0, 25, 50, 75, 99]:
            field_after_first.append(system.field.copy())
    
    # Phase 3: Record field structure created by first pulse
    structure_after_first = system.field.copy()
    
    # Phase 4: Inject second pulse at same location
    print("Phase 3: Injecting second pulse at same location...")
    system.inject_energy_pulse(np.array([10.0, 10.0]), amount=10.0, radius=3.0)
    
    # Let it propagate
    field_after_second = []
    for i in range(100):
        system.step(dt=0.1)
        if i in [0, 25, 50, 75, 99]:
            field_after_second.append(system.field.copy())
    
    # Compare paths: correlation between first and second pulse evolution
    correlations = []
    for f1, f2 in zip(field_after_first, field_after_second):
        corr = np.corrcoef(f1.flatten(), f2.flatten())[0, 1]
        correlations.append(corr)
    
    mean_corr = np.mean(correlations)
    
    print(f"\nPath correlation (first vs second pulse): {mean_corr:.3f}")
    
    if mean_corr > 0.7:
        result = "STRONG MEMORY"
        print(f"✓ RESULT: {result} — second pulse follows prior path")
    elif mean_corr > 0.4:
        result = "PARTIAL MEMORY"
        print(f"~ RESULT: {result} — some path preference")
    else:
        result = "NO MEMORY"
        print(f"✗ RESULT: {result} — paths are independent")
    
    # Plot
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    
    # First pulse evolution
    for idx, (f, t) in enumerate(zip(field_after_first[:3], [0, 25, 50])):
        ax = axes[0, idx]
        ax.imshow(f.T, origin='lower', cmap='RdBu', vmin=-2, vmax=2)
        ax.set_title(f'First Pulse t={t}')
        ax.scatter(10, 10, marker='x', c='white', s=100)
    
    # Second pulse evolution
    for idx, (f, t) in enumerate(zip(field_after_second[:3], [0, 25, 50])):
        ax = axes[1, idx]
        ax.imshow(f.T, origin='lower', cmap='RdBu', vmin=-2, vmax=2)
        ax.set_title(f'Second Pulse t={t}')
        ax.scatter(10, 10, marker='x', c='white', s=100)
    
    plt.suptitle(f'Channel Persistence Test\nPath Correlation: {mean_corr:.3f} ({result})', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_channel_persistence.png', dpi=150)
    print("Saved test_channel_persistence.png")
    
    return result, mean_corr


def test_regime_mapping():
    """
    Test 3: Regime Mapping
    
    Scan coupling parameters to identify:
    - Dead medium (nothing happens)
    - Diffusive medium (spreading, no structure)
    - Self-organizing (structure forms)
    - Unstable (runaway)
    """
    print("\n" + "=" * 60)
    print("TEST 3: REGIME MAPPING")
    print("=" * 60)
    
    # Parameters to scan
    field_strengths = [0.1, 0.3, 0.5, 0.8]
    force_strengths = [0.2, 0.5, 0.8, 1.2]
    
    results = np.zeros((len(field_strengths), len(force_strengths)))
    regime_names = np.empty((len(field_strengths), len(force_strengths)), dtype=object)
    
    for i, fs in enumerate(field_strengths):
        for j, ff in enumerate(force_strengths):
            np.random.seed(42)
            
            params = FieldParams(
                field_diffusion=0.15,
                field_decay=0.003,
                defect_field_strength=fs,
                field_force_strength=ff,
                creation_threshold=1.2,
                creation_rate=0.004,
                creation_cost=0.7,
                annihilation_injection=0.6,
            )
            
            system = CoupledFieldSystem(size=(25, 25), params=params)
            system.energy_field = np.random.uniform(1.0, 2.0, system.size)
            system.create_random_pairs(10)
            
            # Run for 300 steps
            for _ in range(300):
                system.step(dt=0.1)
            
            # Classify regime
            n_defects = len(system.defects)
            field_var = np.var(system.field)
            field_max = np.max(np.abs(system.field))
            
            if n_defects == 0 and field_var < 0.01:
                regime = "DEAD"
                score = 0
            elif field_max > 4.5:
                regime = "RUNAWAY"
                score = -1
            elif n_defects > 0 and field_var > 0.5:
                regime = "SELF-ORG"
                score = 2
            elif n_defects > 0 and field_var > 0.1:
                regime = "DIFFUSE"
                score = 1
            else:
                regime = "WEAK"
                score = 0.5
            
            results[i, j] = score
            regime_names[i, j] = regime
            print(f"  field={fs:.1f}, force={ff:.1f}: {regime} (n={n_defects}, var={field_var:.2f})")
    
    # Plot regime map
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(results, cmap='RdYlGn', vmin=-1, vmax=2, origin='lower')
    
    # Add regime labels
    for i in range(len(field_strengths)):
        for j in range(len(force_strengths)):
            ax.text(j, i, regime_names[i, j], ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax.set_xticks(range(len(force_strengths)))
    ax.set_xticklabels([f'{f:.1f}' for f in force_strengths])
    ax.set_yticks(range(len(field_strengths)))
    ax.set_yticklabels([f'{f:.1f}' for f in field_strengths])
    ax.set_xlabel('Field → Defect Force Strength', fontsize=12)
    ax.set_ylabel('Defect → Field Coupling', fontsize=12)
    ax.set_title('QMRT Regime Map\n(Green=Self-Organizing, Yellow=Diffusive, Red=Dead/Runaway)', 
                fontsize=12, fontweight='bold')
    
    plt.colorbar(im, ax=ax, label='Regime Score')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_regime_map.png', dpi=150)
    print("\nSaved test_regime_map.png")
    
    return results, regime_names


if __name__ == "__main__":
    print("\nQMRT CRITICAL DIAGNOSTIC TESTS")
    print("=" * 60)
    
    # Test 1: Wave vs Diffusion
    wave_result = test_wave_vs_diffusion()
    
    # Test 2: Channel Persistence
    memory_result, correlation = test_channel_persistence()
    
    # Test 3: Regime Mapping
    regimes, names = test_regime_mapping()
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"Propagation type: {wave_result}")
    print(f"Channel memory: {memory_result} (correlation={correlation:.3f})")
    print(f"Optimal regime: Look for SELF-ORG in regime map")
    
    # Save summary
    summary = {
        'wave_vs_diffusion': wave_result,
        'channel_memory': memory_result,
        'memory_correlation': float(correlation),
        'timestamp': '2026-04'
    }
    
    import json
    with open('/app/backend/qmrt_topology/diagnostic_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\nResults saved to diagnostic_results.json")
