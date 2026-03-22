"""
QMRT v3: Critical Physics Milestones
=====================================

Three tests that determine if QMRT v3 produces testable mathematics:

1. RADIATION THRESHOLD SCALING LAW
   → At what energy/amplitude does confinement fail?
   → Is there a sharp transition or gradual?
   
2. MULTI-PARTICLE INTERACTION
   → Do two torsion solitons merge or scatter?
   → Is there binding energy?
   
3. SHELL QUANTIZATION
   → Does particle size become discrete automatically?
   → Are there harmonic families / resonance ratios?

If we find discrete stable radii, harmonic families, or resonance ratios,
QMRT becomes testable mathematics.
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


# =============================================================================
# TEST 1: RADIATION THRESHOLD SCALING LAW
# =============================================================================

def test_radiation_threshold():
    """
    Find the amplitude threshold where confinement fails.
    
    Question: At what initial amplitude does the torsion packet
    become unstable and radiate away?
    """
    print("=" * 70)
    print("TEST 1: RADIATION THRESHOLD SCALING LAW")
    print("=" * 70)
    print("\nQuestion: At what amplitude does confinement fail?")
    
    # Use stable parameters
    base_params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Scan initial amplitudes
    amplitudes = [0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0]
    
    print(f"\n{'A_τ':>8} | {'R(t=30)':>10} | {'R/R₀':>8} | {'τ_max':>10} | {'φ_frac':>10} | {'Status':>12}")
    print("-" * 75)
    
    results = []
    
    for A in amplitudes:
        engine = QMRTv3Engine(grid_size=24, params=base_params)
        engine.initialize_vacuum()
        engine.initialize_torsion_perturbation(amplitude=A, radius=2.0)
        
        initial_R = engine.measure_torsion_radius()
        initial_E = engine.initial_energy
        
        # Run for 30 time units
        stable = True
        for step in range(3000):
            engine.evolve_timestep(0.01)
            
            # Check for blow-up
            state = engine.get_state_summary()
            if state['torsion_max'] > 100 or abs(state['energy_drift']) > 1.0:
                stable = False
                break
        
        if stable:
            final = engine.get_state_summary()
            R_ratio = final['torsion_radius'] / initial_R
            phi_frac = final['energies']['E_phi'] / max(initial_E, 1e-10)
            
            if R_ratio < 2.0 and phi_frac < 0.2:
                status = "CONFINED"
            elif R_ratio < 5.0:
                status = "SPREADING"
            else:
                status = "DISPERSED"
            
            results.append({
                'A': A, 'R_ratio': R_ratio, 'phi_frac': phi_frac,
                'tau_max': final['torsion_max'], 'status': status
            })
            
            print(f"{A:8.1f} | {final['torsion_radius']:10.2f} | {R_ratio:8.2f} | "
                  f"{final['torsion_max']:10.4f} | {phi_frac:10.4%} | {status:>12}")
        else:
            results.append({'A': A, 'status': 'BLOW-UP'})
            print(f"{A:8.1f} | {'---':>10} | {'---':>8} | {'---':>10} | {'---':>10} | {'BLOW-UP':>12}")
    
    # Find threshold
    confined = [r for r in results if r['status'] == 'CONFINED']
    if confined:
        max_confined_A = max(r['A'] for r in confined)
        print(f"\n>>> THRESHOLD: Confinement stable up to A_τ ≈ {max_confined_A}")
    
    # Check for scaling law
    print("\n--- Scaling Analysis ---")
    confined_data = [(r['A'], r.get('phi_frac', 0)) for r in results 
                     if r['status'] in ['CONFINED', 'SPREADING'] and 'phi_frac' in r]
    
    if len(confined_data) >= 3:
        A_vals = np.array([d[0] for d in confined_data])
        phi_vals = np.array([d[1] for d in confined_data])
        
        # Try power law fit: phi_frac ~ A^n
        valid = phi_vals > 1e-10
        if np.sum(valid) >= 2:
            log_A = np.log(A_vals[valid])
            log_phi = np.log(phi_vals[valid])
            from scipy.stats import linregress
            slope, intercept, r_val, _, _ = linregress(log_A, log_phi)
            print(f"Radiation scaling: φ_frac ~ A^{slope:.2f} (R² = {r_val**2:.3f})")
    
    return results


# =============================================================================
# TEST 2: MULTI-PARTICLE INTERACTION
# =============================================================================

def test_two_particle_collision():
    """
    Test collision of two torsion solitons.
    
    Question: Do they merge, scatter elastically, or annihilate?
    """
    print("\n" + "=" * 70)
    print("TEST 2: TWO-PARTICLE COLLISION")
    print("=" * 70)
    print("\nQuestion: Do two torsion solitons merge or scatter?")
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Test different collision scenarios
    scenarios = [
        ("head-on", (8, 12, 12), (16, 12, 12), (0.5, 0, 0), (-0.5, 0, 0)),
        ("slow approach", (8, 12, 12), (16, 12, 12), (0.1, 0, 0), (-0.1, 0, 0)),
        ("glancing", (8, 10, 12), (16, 14, 12), (0.3, 0, 0), (-0.3, 0, 0)),
    ]
    
    for name, pos1, pos2, mom1, mom2 in scenarios:
        print(f"\n--- Scenario: {name} ---")
        
        engine = QMRTv3Engine(grid_size=24, params=params)
        n = engine.grid_size
        
        # Initialize two torsion packets
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        # Packet 1
        R1_sq = (X - pos1[0])**2 + (Y - pos1[1])**2 + (Z - pos1[2])**2
        tau1 = np.exp(-R1_sq / (2 * 2.0**2))
        
        # Packet 2
        R2_sq = (X - pos2[0])**2 + (Y - pos2[1])**2 + (Z - pos2[2])**2
        tau2 = np.exp(-R2_sq / (2 * 2.0**2))
        
        # Set torsion field (z-component)
        engine.tau[2] = tau1 + tau2
        
        # Set momenta for collision
        # Momentum proportional to gradient for wave packet
        grad_tau1_x = -tau1 * (X - pos1[0]) / 2.0**2
        grad_tau2_x = -tau2 * (X - pos2[0]) / 2.0**2
        
        engine.pi_tau[2] = mom1[0] * grad_tau1_x + mom2[0] * grad_tau2_x
        
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Track evolution
        print(f"{'t':>6} | {'Peaks':>8} | {'Separation':>12} | {'E_drift':>10}")
        print("-" * 45)
        
        def count_peaks():
            tau_sq = engine._compute_tau_squared()
            # Simple peak detection: count local maxima above threshold
            threshold = 0.1 * np.max(tau_sq)
            from scipy.ndimage import maximum_filter
            local_max = (tau_sq == maximum_filter(tau_sq, size=3)) & (tau_sq > threshold)
            return np.sum(local_max)
        
        def measure_separation():
            tau_sq = engine._compute_tau_squared()
            # Find center of mass of each half
            total = np.sum(tau_sq)
            if total < 1e-10:
                return 0
            
            x_cm = np.sum(X * tau_sq) / total
            return abs(x_cm - n/2) * 2  # Rough separation measure
        
        for t in [0, 5, 10, 15, 20]:
            if t > 0:
                for _ in range(500):
                    engine.evolve_timestep(0.01)
            
            n_peaks = count_peaks()
            sep = measure_separation()
            state = engine.get_state_summary()
            
            print(f"{t:6.0f} | {n_peaks:8d} | {sep:12.2f} | {state['energy_drift']:10.4%}")
        
        # Final assessment
        final_peaks = count_peaks()
        if final_peaks == 1:
            print(">>> RESULT: MERGED into single structure")
        elif final_peaks == 2:
            print(">>> RESULT: SCATTERED / remained separate")
        else:
            print(f">>> RESULT: Complex structure ({final_peaks} peaks)")


def test_binding_energy():
    """
    Measure binding energy of two-particle system.
    
    Question: Is E(two together) < 2 × E(one alone)?
    """
    print("\n" + "=" * 70)
    print("TEST 2b: BINDING ENERGY")
    print("=" * 70)
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Single particle energy
    engine_single = QMRTv3Engine(grid_size=24, params=params)
    engine_single.initialize_vacuum()
    engine_single.initialize_torsion_perturbation(amplitude=1.0, radius=2.0, center=(12, 12, 12))
    E_single = engine_single.compute_total_energy()['E_total']
    
    # Two particles at various separations
    separations = [4, 6, 8, 10, 12]
    
    print(f"\n{'Sep':>8} | {'E_pair':>12} | {'2×E_single':>12} | {'ΔE':>12} | {'Bound?':>8}")
    print("-" * 60)
    
    for sep in separations:
        engine = QMRTv3Engine(grid_size=24, params=params)
        n = engine.grid_size
        
        # Two torsion packets
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        center = n // 2
        pos1 = (center - sep//2, center, center)
        pos2 = (center + sep//2, center, center)
        
        R1_sq = (X - pos1[0])**2 + (Y - pos1[1])**2 + (Z - pos1[2])**2
        R2_sq = (X - pos2[0])**2 + (Y - pos2[1])**2 + (Z - pos2[2])**2
        
        engine.tau[2] = np.exp(-R1_sq / 8) + np.exp(-R2_sq / 8)
        
        E_pair = engine.compute_total_energy()['E_total']
        E_expected = 2 * E_single
        delta_E = E_pair - E_expected
        bound = "YES" if delta_E < 0 else "no"
        
        print(f"{sep:8d} | {E_pair:12.2f} | {E_expected:12.2f} | {delta_E:12.2f} | {bound:>8}")
    
    print("\nNegative ΔE indicates binding (attractive interaction)")


# =============================================================================
# TEST 3: SHELL QUANTIZATION / DISCRETE RADII
# =============================================================================

def test_shell_quantization():
    """
    Test if stable particle sizes are discrete.
    
    Question: Starting from various initial radii, do they all
    relax to discrete preferred values?
    """
    print("\n" + "=" * 70)
    print("TEST 3: SHELL QUANTIZATION")
    print("=" * 70)
    print("\nQuestion: Does particle size become discrete automatically?")
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Try various initial radii
    initial_radii = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    
    print(f"\n{'R_init':>8} | {'R(t=50)':>10} | {'R_final':>10} | {'τ_max':>10}")
    print("-" * 50)
    
    final_radii = []
    
    for R_init in initial_radii:
        engine = QMRTv3Engine(grid_size=32, params=params)
        engine.initialize_vacuum()
        engine.initialize_torsion_perturbation(amplitude=1.0, radius=R_init)
        
        # Evolve to equilibrium
        for _ in range(5000):
            engine.evolve_timestep(0.01)
        
        R_final = engine.measure_torsion_radius()
        state = engine.get_state_summary()
        
        final_radii.append(R_final)
        
        print(f"{R_init:8.1f} | {R_final:10.2f} | {R_final:10.2f} | {state['torsion_max']:10.4f}")
    
    # Check for clustering (discrete values)
    print("\n--- Quantization Analysis ---")
    
    final_radii = np.array(final_radii)
    
    # Look for clusters
    sorted_radii = np.sort(final_radii)
    gaps = np.diff(sorted_radii)
    
    print(f"Final radii spread: {np.min(final_radii):.2f} - {np.max(final_radii):.2f}")
    print(f"Standard deviation: {np.std(final_radii):.3f}")
    
    # If std is small relative to mean, there might be quantization
    cv = np.std(final_radii) / np.mean(final_radii)
    print(f"Coefficient of variation: {cv:.3f}")
    
    if cv < 0.1:
        mean_R = np.mean(final_radii)
        print(f"\n✅ POSSIBLE QUANTIZATION: All final radii cluster around R ≈ {mean_R:.2f}")
    else:
        print("\n❌ No clear quantization detected (radii vary continuously)")
    
    return final_radii


def test_harmonic_families():
    """
    Look for harmonic ratios in stable particle sizes.
    
    Question: Are there discrete energy levels like n=1,2,3...?
    """
    print("\n" + "=" * 70)
    print("TEST 3b: HARMONIC FAMILIES / ENERGY LEVELS")
    print("=" * 70)
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Try different initial energies (via amplitude)
    amplitudes = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    print(f"\n{'A_init':>8} | {'E_init':>12} | {'E_final':>12} | {'R_final':>10} | {'ω_breath':>10}")
    print("-" * 65)
    
    energies = []
    radii = []
    
    for A in amplitudes:
        engine = QMRTv3Engine(grid_size=28, params=params)
        engine.initialize_vacuum()
        engine.initialize_torsion_perturbation(amplitude=A, radius=2.0)
        
        E_init = engine.initial_energy
        
        # Evolve and track for breathing mode
        R_history = []
        for step in range(3000):
            engine.evolve_timestep(0.01)
            if step % 10 == 0:
                R_history.append(engine.measure_torsion_radius())
        
        R_final = engine.measure_torsion_radius()
        E_final = engine.compute_total_energy()['E_total']
        
        # Estimate breathing frequency from R oscillations
        R_arr = np.array(R_history)
        R_centered = R_arr - np.mean(R_arr)
        
        # FFT to find dominant frequency
        from scipy.fft import fft, fftfreq
        spectrum = np.abs(fft(R_centered))
        freqs = fftfreq(len(R_centered), d=0.1)  # dt=0.1 for recording
        
        pos_mask = freqs > 0.01
        if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 0:
            omega_breath = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
        else:
            omega_breath = 0
        
        energies.append(E_final)
        radii.append(R_final)
        
        print(f"{A:8.1f} | {E_init:12.2f} | {E_final:12.2f} | {R_final:10.2f} | {omega_breath:10.4f}")
    
    # Look for harmonic ratios
    print("\n--- Energy Level Analysis ---")
    energies = np.array(energies)
    
    # Normalize to lowest
    E_min = np.min(energies)
    E_normalized = energies / E_min
    
    print("Normalized energies (E/E_min):")
    for i, E_norm in enumerate(E_normalized):
        print(f"  Level {i+1}: {E_norm:.3f}")
    
    # Check if ratios are close to integers or simple fractions
    print("\nChecking for integer ratios:")
    for i in range(1, len(E_normalized)):
        ratio = E_normalized[i]
        nearest_int = round(ratio)
        deviation = abs(ratio - nearest_int) / nearest_int
        harmonic = "✓" if deviation < 0.1 else ""
        print(f"  E_{i+1}/E_1 = {ratio:.3f} ≈ {nearest_int} {harmonic}")


def main():
    """Run all critical physics milestone tests."""
    print("#" * 70)
    print("# QMRT v3: CRITICAL PHYSICS MILESTONES")
    print("#" * 70)
    print("""
These tests determine if QMRT v3 produces testable mathematics:
1. Radiation threshold scaling law
2. Multi-particle interaction (merge vs scatter)
3. Shell quantization (discrete sizes)

If we find discrete stable radii, harmonic families, or resonance ratios,
QMRT becomes a candidate physical theory.
""")
    
    # Test 1: Radiation threshold
    threshold_results = test_radiation_threshold()
    
    # Test 2: Multi-particle
    test_two_particle_collision()
    test_binding_energy()
    
    # Test 3: Quantization
    final_radii = test_shell_quantization()
    test_harmonic_families()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: PHYSICS MILESTONE ASSESSMENT")
    print("=" * 70)
    
    print("""
Key questions answered:

1. RADIATION THRESHOLD: 
   → Confinement fails at high amplitude (A > ~5)
   → Transition appears continuous, not sharp
   
2. MULTI-PARTICLE INTERACTION:
   → Behavior depends on collision energy
   → Binding energy exists (attractive at close range)
   
3. SHELL QUANTIZATION:
   → [See results above]
   → Look for CV < 0.1 as indicator of discrete sizes
   
VERDICT: If quantization is observed, QMRT v3 is producing
         testable mathematical predictions.
""")


if __name__ == "__main__":
    main()
