#!/usr/bin/env python3
"""
QMRT Wave Physics Verification Tests
=====================================
Critical tests to verify true wave behavior:

1. Interference Test - constructive/destructive superposition
2. Energy Conservation Audit - E = ∫((∂tφ)² + c²|∇φ|²)dV
3. Dispersion Test - does speed depend on wavelength?
4. Channel-Wave Interaction - do waves prefer existing channels?
"""

import numpy as np
import matplotlib.pyplot as plt
from wave_field_dynamics import WaveFieldSystem, WaveParams


def test_interference():
    """
    Test 1: Wave Interference
    
    Inject two pulses:
    - Same phase → constructive interference (amplification)
    - Opposite phase → destructive interference (cancellation)
    """
    print("=" * 60)
    print("TEST 1: WAVE INTERFERENCE")
    print("=" * 60)
    
    np.random.seed(42)
    
    params = WaveParams(
        wave_speed=1.5,
        wave_damping=0.01,  # Low damping for clean interference
        creation_threshold=100,
        creation_rate=0,
    )
    
    # Test A: Same phase (constructive)
    print("\n--- Test A: Same Phase (Constructive) ---")
    system_a = WaveFieldSystem(size=(60, 60), params=params)
    
    # Two pulses approaching each other
    system_a.inject_wave_pulse(np.array([20.0, 30.0]), amplitude=2.0, radius=3.0)
    system_a.inject_wave_pulse(np.array([40.0, 30.0]), amplitude=2.0, radius=3.0)
    
    # Track max amplitude at center
    max_at_center_a = []
    center_x, center_y = 30, 30
    
    for t in range(150):
        system_a.step(dt=0.1)
        max_at_center_a.append(abs(system_a.field[center_x, center_y]))
    
    peak_constructive = max(max_at_center_a)
    print(f"Peak amplitude at center: {peak_constructive:.3f}")
    print(f"Expected (constructive ≈ 2x individual): ~{2 * 2.0 * 0.5:.1f}")
    
    # Test B: Opposite phase (destructive)
    print("\n--- Test B: Opposite Phase (Destructive) ---")
    system_b = WaveFieldSystem(size=(60, 60), params=params)
    
    # Opposite amplitudes
    system_b.inject_wave_pulse(np.array([20.0, 30.0]), amplitude=2.0, radius=3.0)
    system_b.inject_wave_pulse(np.array([40.0, 30.0]), amplitude=-2.0, radius=3.0)
    
    max_at_center_b = []
    
    for t in range(150):
        system_b.step(dt=0.1)
        max_at_center_b.append(abs(system_b.field[center_x, center_y]))
    
    peak_destructive = max(max_at_center_b)
    print(f"Peak amplitude at center: {peak_destructive:.3f}")
    print(f"Expected (destructive ≈ cancellation): ~0")
    
    # Analysis
    print("\n--- Interference Analysis ---")
    ratio = peak_constructive / max(peak_destructive, 0.001)
    print(f"Constructive/Destructive ratio: {ratio:.1f}")
    
    if ratio > 3:
        result = "INTERFERENCE CONFIRMED"
        print(f"✓ {result} — clear superposition behavior")
    elif ratio > 1.5:
        result = "PARTIAL INTERFERENCE"
        print(f"~ {result} — some superposition")
    else:
        result = "NO INTERFERENCE"
        print(f"✗ {result} — waves not superposing properly")
    
    # Plot
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    
    # Constructive snapshots
    system_a_vis = WaveFieldSystem(size=(60, 60), params=params)
    system_a_vis.inject_wave_pulse(np.array([20.0, 30.0]), amplitude=2.0, radius=3.0)
    system_a_vis.inject_wave_pulse(np.array([40.0, 30.0]), amplitude=2.0, radius=3.0)
    
    for idx, t_target in enumerate([0, 50, 100]):
        for _ in range(t_target if idx == 0 else 50):
            system_a_vis.step(dt=0.1)
        ax = axes[0, idx]
        im = ax.imshow(system_a_vis.field.T, origin='lower', cmap='RdBu', 
                       vmin=-3, vmax=3, extent=[0, 60, 0, 60])
        ax.set_title(f'Constructive t={t_target}')
        ax.scatter([20, 40], [30, 30], marker='x', c='white', s=50)
    
    # Destructive snapshots
    system_b_vis = WaveFieldSystem(size=(60, 60), params=params)
    system_b_vis.inject_wave_pulse(np.array([20.0, 30.0]), amplitude=2.0, radius=3.0)
    system_b_vis.inject_wave_pulse(np.array([40.0, 30.0]), amplitude=-2.0, radius=3.0)
    
    for idx, t_target in enumerate([0, 50, 100]):
        for _ in range(t_target if idx == 0 else 50):
            system_b_vis.step(dt=0.1)
        ax = axes[1, idx]
        im = ax.imshow(system_b_vis.field.T, origin='lower', cmap='RdBu', 
                       vmin=-3, vmax=3, extent=[0, 60, 0, 60])
        ax.set_title(f'Destructive t={t_target}')
        ax.scatter([20, 40], [30, 30], marker='x', c='white', s=50)
    
    plt.suptitle(f'Wave Interference Test\nConstructive peak: {peak_constructive:.2f}, Destructive peak: {peak_destructive:.2f}\nResult: {result}', 
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_interference.png', dpi=150)
    print("\nSaved test_interference.png")
    
    return result, peak_constructive, peak_destructive


def test_energy_conservation():
    """
    Test 2: Energy Conservation Audit
    
    Track total wave energy: E = ∫((∂tφ)² + c²|∇φ|²)dV
    Should be conserved (or decay smoothly with damping γ)
    """
    print("\n" + "=" * 60)
    print("TEST 2: ENERGY CONSERVATION")
    print("=" * 60)
    
    np.random.seed(42)
    
    # Low damping first
    params = WaveParams(
        wave_speed=1.5,
        wave_damping=0.01,
        creation_threshold=100,
        creation_rate=0,
    )
    
    system = WaveFieldSystem(size=(50, 50), params=params)
    system.inject_wave_pulse(np.array([25.0, 25.0]), amplitude=3.0, radius=4.0)
    
    energies = []
    kinetic = []
    potential = []
    
    c2 = params.wave_speed**2
    
    for t in range(300):
        system.step(dt=0.1)
        
        # Kinetic: (1/2)∫(∂φ/∂t)²
        K = 0.5 * np.sum(system.field_velocity**2)
        
        # Potential: (1/2)c²∫|∇φ|²
        grad_x = np.roll(system.field, -1, axis=0) - system.field
        grad_y = np.roll(system.field, -1, axis=1) - system.field
        U = 0.5 * c2 * np.sum(grad_x**2 + grad_y**2)
        
        E_total = K + U
        
        energies.append(E_total)
        kinetic.append(K)
        potential.append(U)
    
    # Analysis
    E_initial = energies[10]  # Skip transient
    E_final = energies[-1]
    E_ratio = E_final / E_initial
    
    print(f"Initial energy: {E_initial:.2f}")
    print(f"Final energy: {E_final:.2f}")
    print(f"Retention: {E_ratio*100:.1f}%")
    
    # Expected decay from damping: E ~ E0 * exp(-2γt)
    expected_ratio = np.exp(-2 * params.wave_damping * 300 * 0.1)
    print(f"Expected from damping (γ={params.wave_damping}): {expected_ratio*100:.1f}%")
    
    if abs(E_ratio - expected_ratio) < 0.2:
        result = "ENERGY CONSERVED (with expected damping)"
        print(f"✓ {result}")
    elif E_ratio > 0.5:
        result = "APPROXIMATE CONSERVATION"
        print(f"~ {result}")
    else:
        result = "ENERGY NOT CONSERVED"
        print(f"✗ {result}")
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    times = np.arange(len(energies)) * 0.1
    
    ax.plot(times, energies, 'b-', linewidth=2, label='Total E')
    ax.plot(times, kinetic, 'r--', linewidth=1, alpha=0.7, label='Kinetic')
    ax.plot(times, potential, 'g--', linewidth=1, alpha=0.7, label='Potential')
    
    # Expected decay curve
    expected = E_initial * np.exp(-2 * params.wave_damping * times)
    ax.plot(times, expected, 'k:', linewidth=2, label=f'Expected decay (γ={params.wave_damping})')
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Energy', fontsize=12)
    ax.set_title(f'Energy Conservation Test\n{result}', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_energy_conservation.png', dpi=150)
    print("Saved test_energy_conservation.png")
    
    return result, E_ratio


def test_dispersion():
    """
    Test 3: Dispersion Test
    
    Check if wave speed depends on wavelength.
    - No dispersion: c = constant (ideal wave medium)
    - Dispersion: c(k) varies (structured medium)
    """
    print("\n" + "=" * 60)
    print("TEST 3: DISPERSION")
    print("=" * 60)
    
    np.random.seed(42)
    
    params = WaveParams(
        wave_speed=1.5,
        wave_damping=0.005,
        creation_threshold=100,
        creation_rate=0,
    )
    
    # Test different pulse sizes (proxy for wavelength)
    radii = [2.0, 4.0, 6.0]
    speeds = []
    
    for radius in radii:
        system = WaveFieldSystem(size=(80, 80), params=params)
        system.inject_wave_pulse(np.array([40.0, 40.0]), amplitude=2.0, radius=radius)
        
        # Track wavefront
        wavefront_radii = []
        times_measured = []
        
        for t in range(100):
            system.step(dt=0.1)
            
            if t % 10 == 0 and t > 10:
                threshold = 0.1
                above = np.where(np.abs(system.field) > threshold)
                if len(above[0]) > 0:
                    distances = np.sqrt((above[0] - 40)**2 + (above[1] - 40)**2)
                    r = np.max(distances)
                    wavefront_radii.append(r)
                    times_measured.append(t * 0.1)
        
        # Fit speed
        if len(times_measured) > 2:
            speed = np.polyfit(times_measured, wavefront_radii, 1)[0]
            speeds.append(speed)
            print(f"  Pulse radius {radius}: measured speed = {speed:.3f}")
    
    # Check dispersion
    if len(speeds) >= 2:
        speed_variation = (max(speeds) - min(speeds)) / np.mean(speeds)
        print(f"\nSpeed variation: {speed_variation*100:.1f}%")
        
        if speed_variation < 0.1:
            result = "NO DISPERSION (ideal medium)"
            print(f"✓ {result}")
        elif speed_variation < 0.3:
            result = "WEAK DISPERSION"
            print(f"~ {result}")
        else:
            result = "SIGNIFICANT DISPERSION"
            print(f"! {result} — speed depends on wavelength")
    else:
        result = "INSUFFICIENT DATA"
        speed_variation = 0
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(range(len(radii)), speeds, tick_label=[f'r={r}' for r in radii])
    ax.axhline(params.wave_speed, color='r', linestyle='--', label=f'Expected c={params.wave_speed}')
    ax.set_xlabel('Pulse Size', fontsize=12)
    ax.set_ylabel('Measured Speed', fontsize=12)
    ax.set_title(f'Dispersion Test\nVariation: {speed_variation*100:.1f}% — {result}', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_dispersion.png', dpi=150)
    print("Saved test_dispersion.png")
    
    return result, speeds


def test_channel_wave_interaction():
    """
    Test 4: Channel-Wave Interaction
    
    THE KEY TEST: Do waves prefer existing channels?
    
    1. Create a medium with established channel structure
    2. Inject wave
    3. Check if wave follows channels preferentially
    """
    print("\n" + "=" * 60)
    print("TEST 4: CHANNEL-WAVE INTERACTION")
    print("=" * 60)
    
    np.random.seed(42)
    
    params = WaveParams(
        wave_speed=1.5,
        wave_damping=0.02,
        defect_field_strength=0.8,  # Strong defect-field coupling
        field_force_strength=0.5,
        creation_threshold=1.5,
        creation_rate=0.003,
        creation_cost=0.6,
        annihilation_injection=0.5,
    )
    
    # Phase 1: Build channel structure with defects
    print("Phase 1: Building channel structure...")
    system = WaveFieldSystem(size=(50, 50), params=params)
    system.energy_field = np.random.uniform(0.8, 1.5, system.size)
    system.create_random_pairs(15)
    
    for t in range(300):
        system.step(dt=0.1)
    
    # Record channel structure
    channel_structure = system.field.copy()
    channel_strength = np.var(channel_structure)
    print(f"Channel structure variance: {channel_strength:.3f}")
    
    # Phase 2: Inject wave at edge
    print("Phase 2: Injecting wave into structured medium...")
    system.inject_wave_pulse(np.array([10.0, 25.0]), amplitude=3.0, radius=4.0)
    
    # Track wave propagation
    wave_in_channel = []
    wave_outside = []
    
    # Define "channel" as where |field| > threshold
    channel_threshold = np.percentile(np.abs(channel_structure), 70)
    channel_mask = np.abs(channel_structure) > channel_threshold
    
    for t in range(150):
        system.step(dt=0.1)
        
        if t % 10 == 0:
            # Measure wave energy in channels vs outside
            wave_amplitude = np.abs(system.field - channel_structure)
            
            in_channel = np.mean(wave_amplitude[channel_mask])
            outside = np.mean(wave_amplitude[~channel_mask])
            
            wave_in_channel.append(in_channel)
            wave_outside.append(outside)
    
    # Analysis
    avg_in = np.mean(wave_in_channel[5:])  # Skip initial
    avg_out = np.mean(wave_outside[5:])
    preference_ratio = avg_in / max(avg_out, 0.001)
    
    print(f"\nWave amplitude in channels: {avg_in:.4f}")
    print(f"Wave amplitude outside: {avg_out:.4f}")
    print(f"Channel preference ratio: {preference_ratio:.2f}")
    
    if preference_ratio > 1.5:
        result = "WAVES PREFER CHANNELS"
        print(f"✓ {result} — guided wave propagation!")
    elif preference_ratio > 1.1:
        result = "WEAK CHANNEL PREFERENCE"
        print(f"~ {result}")
    else:
        result = "NO CHANNEL PREFERENCE"
        print(f"✗ {result}")
    
    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    
    ax = axes[0]
    im = ax.imshow(channel_structure.T, origin='lower', cmap='RdBu', extent=[0, 50, 0, 50])
    ax.set_title('Channel Structure (before wave)')
    ax.scatter(10, 25, marker='*', c='yellow', s=200, label='Wave source')
    ax.legend()
    
    ax = axes[1]
    im = ax.imshow(system.field.T, origin='lower', cmap='RdBu', extent=[0, 50, 0, 50])
    ax.set_title('Field (after wave propagation)')
    
    ax = axes[2]
    ax.plot(wave_in_channel, 'b-', linewidth=2, label='In channels')
    ax.plot(wave_outside, 'r--', linewidth=2, label='Outside channels')
    ax.set_xlabel('Time step')
    ax.set_ylabel('Wave amplitude')
    ax.set_title(f'Channel preference: {preference_ratio:.2f}x')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.suptitle(f'Channel-Wave Interaction Test\n{result}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_channel_wave.png', dpi=150)
    print("Saved test_channel_wave.png")
    
    return result, preference_ratio


if __name__ == "__main__":
    print("\nQMRT WAVE PHYSICS VERIFICATION")
    print("=" * 60)
    
    # Run all tests
    interference_result, c_peak, d_peak = test_interference()
    energy_result, e_ratio = test_energy_conservation()
    dispersion_result, speeds = test_dispersion()
    channel_result, preference = test_channel_wave_interaction()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"1. Interference: {interference_result}")
    print(f"   Constructive/Destructive ratio: {c_peak/max(d_peak,0.001):.1f}x")
    print(f"2. Energy: {energy_result}")
    print(f"   Retention: {e_ratio*100:.1f}%")
    print(f"3. Dispersion: {dispersion_result}")
    print(f"4. Channel-Wave: {channel_result}")
    print(f"   Preference ratio: {preference:.2f}x")
    
    # Save summary
    import json
    summary = {
        'interference': interference_result,
        'interference_ratio': float(c_peak/max(d_peak,0.001)),
        'energy': energy_result,
        'energy_retention': float(e_ratio),
        'dispersion': dispersion_result,
        'channel_wave': channel_result,
        'channel_preference': float(preference),
    }
    
    with open('/app/backend/qmrt_topology/wave_verification_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\nResults saved to wave_verification_results.json")
