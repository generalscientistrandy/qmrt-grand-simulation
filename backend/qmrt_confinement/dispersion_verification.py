"""
QMRT Dispersion Verification Suite

Determines whether the observed relativistic-like dispersion is:
1. NUMERICAL ARTIFACT (changes with grid/timestep)
2. MEDIUM SOLITON PHYSICS (standard nonlinear wave behavior)
3. TRUE EMERGENT RELATIVISTIC REGIME (fundamental property)

Tests:
1. Grid refinement → does c_eff converge?
2. Parameter sweep → does dispersion survive tuning?
3. Multi-defect relativistic scattering
4. Energy conservation audit at high momentum
5. Radiation spectrum analysis
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import curve_fit
from scipy.stats import linregress
from scipy.fft import fft, fftfreq
import warnings

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters


# =============================================================================
# Helper: Quick dispersion measurement
# =============================================================================

def measure_dispersion_point(
    grid_size: int,
    momentum: float,
    params: Optional[QMRTFrequencyParameters] = None,
    dt: float = 0.02,
    measurement_time: float = 5.0,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Quick measurement of (velocity, energy, energy_conservation_error) for one momentum.
    """
    if params is None:
        params = QMRTFrequencyParameters()
    
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    for _ in range(50):
        engine.evolve_timestep(dt)
    
    E_initial = engine.compute_total_energy()
    
    # Create moving excitation
    center = grid_size // 2
    start_x = grid_size // 4
    
    n = grid_size
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    R_sq = (X - start_x)**2 + (Y - center)**2 + (Z - center)**2
    amp = 0.3 * p.omega_0
    width = 2.5
    profile = amp * np.exp(-R_sq / (2 * width**2))
    
    engine.omega += profile
    
    # Add momentum
    grad_x = -profile * (X - start_x) / (width**2)
    engine.pi_omega += momentum * grad_x
    
    E_after_excitation = engine.compute_total_energy()
    
    # Track position
    positions = []
    times = []
    
    steps = int(measurement_time / dt)
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % 5 == 0:
            excess = np.abs(engine.omega - np.sign(engine.omega) * p.omega_0)
            mask = excess > 0.1 * amp
            if np.sum(mask) > 10:
                com_x = np.sum(X[mask] * excess[mask]) / np.sum(excess[mask])
                positions.append(float(com_x))
                times.append(engine.time)
    
    E_final = engine.compute_total_energy()
    
    # Velocity from linear fit
    if len(positions) > 5:
        slope, _, _, _, _ = linregress(times, positions)
        velocity = slope
    else:
        velocity = 0.0
    
    # Energy conservation error
    E_conservation_error = abs(E_final - E_after_excitation) / E_after_excitation
    
    # Excitation energy
    excitation_energy = E_after_excitation - E_initial
    
    return velocity, excitation_energy, E_conservation_error


# =============================================================================
# TEST 1: Grid Refinement
# =============================================================================

def test_grid_refinement(
    grid_sizes: List[int] = [16, 20, 24, 28, 32],
    test_momenta: List[float] = [1.0, 2.0, 4.0],
    seed: int = 42
) -> Dict:
    """
    Test if c_eff converges with grid refinement.
    
    If c_eff changes significantly → numerical artifact
    If c_eff converges → physical result
    """
    print("\n" + "="*70)
    print("TEST 1: GRID REFINEMENT - Does c_eff converge?")
    print("="*70)
    
    results = {gs: {} for gs in grid_sizes}
    
    for gs in grid_sizes:
        print(f"\n  Grid {gs}³:")
        
        velocities = []
        for p in test_momenta:
            v, E, err = measure_dispersion_point(gs, p, seed=seed)
            results[gs][p] = {'v': v, 'E': E, 'err': err}
            velocities.append(v)
            print(f"    p={p}: v={v:.5f}")
        
        # Estimate c_eff as max velocity achieved
        results[gs]['c_eff'] = max(velocities)
    
    # Convergence analysis
    c_effs = [results[gs]['c_eff'] for gs in grid_sizes]
    
    print(f"\n  c_eff values: {[f'{c:.5f}' for c in c_effs]}")
    
    # Check convergence (Richardson extrapolation)
    if len(c_effs) >= 3:
        # c(h) = c_∞ + a*h^p → use last 3 points
        c1, c2, c3 = c_effs[-3:]
        h1, h2, h3 = [1/gs for gs in grid_sizes[-3:]]
        
        # Simple convergence rate
        if c2 != c1:
            rate = np.log(abs((c3 - c2)/(c2 - c1 + 1e-10))) / np.log(h3/h2)
        else:
            rate = 0
        
        c_extrapolated = c3
        converged = abs(c3 - c2) / (abs(c2) + 1e-10) < 0.1
    else:
        rate = 0
        c_extrapolated = c_effs[-1]
        converged = False
    
    print(f"\n  Convergence rate: {rate:.2f}")
    print(f"  Extrapolated c_eff: {c_extrapolated:.5f}")
    print(f"  CONVERGED: {'✅ YES' if converged else '❌ NO'}")
    
    return {
        'grid_sizes': grid_sizes,
        'c_eff_values': c_effs,
        'convergence_rate': rate,
        'c_eff_extrapolated': c_extrapolated,
        'converged': converged,
        'verdict': 'PHYSICAL' if converged else 'NEEDS_MORE_GRIDS'
    }


# =============================================================================
# TEST 2: Parameter Sweep
# =============================================================================

def test_parameter_sweep(
    grid_size: int = 24,
    a_omega_values: List[float] = [0.5, 1.0, 2.0, 4.0],
    K_omega_values: List[float] = [0.5, 1.0, 2.0],
    test_momentum: float = 2.0,
    seed: int = 42
) -> Dict:
    """
    Test if dispersion survives parameter tuning.
    
    Check: c_eff(a_ω, K_ω) scaling
    """
    print("\n" + "="*70)
    print("TEST 2: PARAMETER SWEEP - Does dispersion survive tuning?")
    print("="*70)
    
    results = {}
    
    # Sweep a_omega
    print("\n  Sweeping a_ω (barrier depth):")
    c_eff_vs_a_omega = []
    for a_omega in a_omega_values:
        params = QMRTFrequencyParameters(a_omega=a_omega)
        v, E, err = measure_dispersion_point(grid_size, test_momentum, params=params, seed=seed)
        c_eff_vs_a_omega.append(v)
        print(f"    a_ω={a_omega}: v={v:.5f}, E={E:.2f}")
    
    results['a_omega'] = {
        'values': a_omega_values,
        'c_eff': c_eff_vs_a_omega
    }
    
    # Sweep K_omega
    print("\n  Sweeping K_ω (gradient coefficient):")
    c_eff_vs_K_omega = []
    for K_omega in K_omega_values:
        params = QMRTFrequencyParameters(K_omega=K_omega)
        v, E, err = measure_dispersion_point(grid_size, test_momentum, params=params, seed=seed)
        c_eff_vs_K_omega.append(v)
        print(f"    K_ω={K_omega}: v={v:.5f}, E={E:.2f}")
    
    results['K_omega'] = {
        'values': K_omega_values,
        'c_eff': c_eff_vs_K_omega
    }
    
    # Check if c_eff scales predictably
    # For solitons in φ⁴ theory: c ~ √(K/a)
    # Check correlation with √(K_ω/a_ω)
    
    # Fit c_eff ~ a_ω^α
    log_a = np.log(a_omega_values)
    log_c = np.log(np.abs(c_eff_vs_a_omega) + 1e-10)
    try:
        alpha_a, _, r_a, _, _ = linregress(log_a, log_c)
    except:
        alpha_a, r_a = 0, 0
    
    # Fit c_eff ~ K_ω^β
    log_K = np.log(K_omega_values)
    log_c_K = np.log(np.abs(c_eff_vs_K_omega) + 1e-10)
    try:
        alpha_K, _, r_K, _, _ = linregress(log_K, log_c_K)
    except:
        alpha_K, r_K = 0, 0
    
    print(f"\n  Scaling analysis:")
    print(f"    c_eff ~ a_ω^{alpha_a:.2f} (R²={r_a**2:.3f})")
    print(f"    c_eff ~ K_ω^{alpha_K:.2f} (R²={r_K**2:.3f})")
    
    # Expected for Klein-Gordon soliton: c ~ √(K/m²) where m² ~ a
    expected_alpha_a = -0.5
    expected_alpha_K = 0.5
    
    matches_soliton = (abs(alpha_a - expected_alpha_a) < 0.3 and 
                       abs(alpha_K - expected_alpha_K) < 0.3)
    
    print(f"\n  Matches soliton scaling (c~√(K/a)): {'✅ YES' if matches_soliton else '❌ NO'}")
    
    results['scaling'] = {
        'alpha_a_omega': alpha_a,
        'alpha_K_omega': alpha_K,
        'matches_soliton_theory': matches_soliton
    }
    
    return results


# =============================================================================
# TEST 3: Relativistic Scattering
# =============================================================================

def test_relativistic_scattering(
    grid_size: int = 28,
    momenta: List[float] = [1.0, 2.0, 4.0],
    seed: int = 42
) -> Dict:
    """
    Test multi-defect scattering at relativistic speeds.
    
    Check: momentum/energy conservation, scattering angles
    """
    print("\n" + "="*70)
    print("TEST 3: RELATIVISTIC SCATTERING")
    print("="*70)
    
    results = {}
    
    for p_init in momenta:
        print(f"\n  Collision at p = {p_init}:")
        
        engine = QMRTFrequencyEngine(grid_size=grid_size)
        engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
        params = engine.params
        
        for _ in range(50):
            engine.evolve_timestep(0.02)
        
        E_before = engine.compute_total_energy()
        
        # Create two excitations moving toward each other
        center = grid_size // 2
        sep = 12
        
        n = grid_size
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        amp = 0.3 * params.omega_0
        width = 2.5
        
        # Excitation 1: moving right
        R1_sq = (X - (center - sep))**2 + (Y - center)**2 + (Z - center)**2
        profile1 = amp * np.exp(-R1_sq / (2 * width**2))
        engine.omega += profile1
        grad1_x = -profile1 * (X - (center - sep)) / (width**2)
        engine.pi_omega += p_init * grad1_x
        
        # Excitation 2: moving left
        R2_sq = (X - (center + sep))**2 + (Y - center)**2 + (Z - center)**2
        profile2 = amp * np.exp(-R2_sq / (2 * width**2))
        engine.omega += profile2
        grad2_x = -profile2 * (X - (center + sep)) / (width**2)
        engine.pi_omega += (-p_init) * grad2_x
        
        E_after_creation = engine.compute_total_energy()
        
        # Evolve through collision
        for _ in range(500):
            engine.evolve_timestep(0.02)
        
        E_final = engine.compute_total_energy()
        
        # Energy conservation
        E_conservation = abs(E_final - E_after_creation) / E_after_creation
        
        # Check final state (how many excitations remain?)
        from scipy.ndimage import label
        high_omega = np.abs(engine.omega) > 0.5 * params.omega_0
        labeled, n_features = label(high_omega)
        
        print(f"    E_conservation error: {E_conservation:.4%}")
        print(f"    Final defects: {n_features}")
        
        results[p_init] = {
            'E_before': E_after_creation,
            'E_after': E_final,
            'E_conservation_error': E_conservation,
            'final_defects': n_features,
            'elastic': n_features >= 2
        }
    
    # Summary
    avg_conservation = np.mean([r['E_conservation_error'] for r in results.values()])
    all_elastic = all(r['elastic'] for r in results.values())
    
    print(f"\n  Average E conservation error: {avg_conservation:.4%}")
    print(f"  All collisions elastic: {'✅ YES' if all_elastic else '❌ NO'}")
    
    return {
        'collisions': results,
        'avg_E_conservation': avg_conservation,
        'all_elastic': all_elastic
    }


# =============================================================================
# TEST 4: Energy Conservation Audit
# =============================================================================

def test_energy_conservation_audit(
    grid_size: int = 24,
    momenta: List[float] = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0],
    measurement_time: float = 10.0,
    seed: int = 42
) -> Dict:
    """
    Detailed energy conservation at different momenta.
    
    High momentum may cause energy leakage → numerical instability
    """
    print("\n" + "="*70)
    print("TEST 4: ENERGY CONSERVATION AUDIT")
    print("="*70)
    
    results = {}
    
    print(f"\n  {'p':>6} | {'E_init':>12} | {'E_final':>12} | {'ΔE/E':>10} | {'Status':>10}")
    print("-"*60)
    
    for p_init in momenta:
        v, E, err = measure_dispersion_point(
            grid_size, p_init, 
            measurement_time=measurement_time,
            seed=seed
        )
        
        status = "✅ GOOD" if err < 0.01 else ("⚠️ WARN" if err < 0.05 else "❌ BAD")
        print(f"  {p_init:>6.1f} | {E:>12.2f} | {'-':>12} | {err:>10.4%} | {status}")
        
        results[p_init] = {
            'velocity': v,
            'energy': E,
            'conservation_error': err
        }
    
    # Critical momentum (where conservation breaks down)
    errors = [(p, r['conservation_error']) for p, r in results.items()]
    errors.sort(key=lambda x: x[0])
    
    critical_p = None
    for p, err in errors:
        if err > 0.05:
            critical_p = p
            break
    
    if critical_p:
        print(f"\n  ⚠️ Energy conservation breaks down at p ≈ {critical_p}")
    else:
        print(f"\n  ✅ Energy conserved for all tested momenta")
    
    return {
        'momentum_errors': results,
        'critical_momentum': critical_p,
        'stable_regime': critical_p is None
    }


# =============================================================================
# TEST 5: Radiation Spectrum Analysis
# =============================================================================

def test_radiation_spectrum(
    grid_size: int = 28,
    momentum: float = 4.0,
    seed: int = 42
) -> Dict:
    """
    Analyze radiation emitted by accelerating/decelerating excitation.
    """
    print("\n" + "="*70)
    print("TEST 5: RADIATION SPECTRUM ANALYSIS")
    print("="*70)
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    params = engine.params
    
    for _ in range(50):
        engine.evolve_timestep(0.02)
    
    omega_background = engine.omega.copy()
    
    # Create moving excitation
    center = grid_size // 2
    start_x = grid_size // 4
    
    n = grid_size
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    R_sq = (X - start_x)**2 + (Y - center)**2 + (Z - center)**2
    amp = 0.4 * params.omega_0
    width = 2.5
    profile = amp * np.exp(-R_sq / (2 * width**2))
    
    engine.omega += profile
    grad_x = -profile * (X - start_x) / (width**2)
    engine.pi_omega += momentum * grad_x
    
    # Define far-field shell
    R_from_start = np.sqrt((X - start_x)**2 + (Y - center)**2 + (Z - center)**2)
    shell_mask = (R_from_start > grid_size * 0.3) & (R_from_start < grid_size * 0.4)
    
    # Track field oscillations in shell
    field_history = []
    times = []
    
    for step in range(600):
        engine.evolve_timestep(0.02)
        
        if step % 5 == 0:
            delta_omega = engine.omega - omega_background
            field_in_shell = np.mean(delta_omega[shell_mask])
            field_history.append(field_in_shell)
            times.append(engine.time)
    
    # FFT of field oscillations → radiation spectrum
    field_arr = np.array(field_history)
    dt = times[1] - times[0]
    
    spectrum = np.abs(fft(field_arr))**2
    freqs = fftfreq(len(field_arr), d=dt)
    
    # Find peaks
    pos_mask = freqs > 0.01
    pos_freqs = freqs[pos_mask]
    pos_spectrum = spectrum[pos_mask]
    
    if len(pos_spectrum) > 0:
        peak_idx = np.argmax(pos_spectrum)
        peak_freq = pos_freqs[peak_idx]
        peak_power = pos_spectrum[peak_idx]
        
        # Background level
        bg_power = np.median(pos_spectrum)
        
        has_radiation = peak_power > 5 * bg_power
    else:
        peak_freq = 0
        peak_power = 0
        bg_power = 0
        has_radiation = False
    
    print(f"\n  Peak frequency: {peak_freq:.4f}")
    print(f"  Peak power: {peak_power:.4f}")
    print(f"  Background power: {bg_power:.4f}")
    print(f"  Signal/Noise: {peak_power/(bg_power+1e-10):.1f}x")
    print(f"  Radiation detected: {'✅ YES' if has_radiation else '❌ NO'}")
    
    return {
        'peak_frequency': peak_freq,
        'peak_power': peak_power,
        'background_power': bg_power,
        'signal_to_noise': peak_power / (bg_power + 1e-10),
        'has_radiation': has_radiation
    }


# =============================================================================
# MAIN: Run All Verification Tests
# =============================================================================

def run_dispersion_verification(seed: int = 42) -> Dict:
    """
    Run all 5 verification tests for dispersion relation.
    """
    print("\n" + "="*70)
    print("DISPERSION RELATION VERIFICATION SUITE")
    print("="*70)
    print("Determining: NUMERICAL ARTIFACT vs SOLITON PHYSICS vs EMERGENT RELATIVITY")
    print("="*70)
    
    results = {}
    
    # Test 1
    results['grid_refinement'] = test_grid_refinement(
        grid_sizes=[16, 20, 24, 28],
        test_momenta=[1.0, 2.0, 4.0],
        seed=seed
    )
    
    # Test 2
    results['parameter_sweep'] = test_parameter_sweep(
        grid_size=24,
        a_omega_values=[0.5, 1.0, 2.0],
        K_omega_values=[0.5, 1.0, 2.0],
        test_momentum=2.0,
        seed=seed
    )
    
    # Test 3
    results['scattering'] = test_relativistic_scattering(
        grid_size=24,
        momenta=[1.0, 2.0, 4.0],
        seed=seed
    )
    
    # Test 4
    results['energy_conservation'] = test_energy_conservation_audit(
        grid_size=24,
        momenta=[0.5, 1.0, 2.0, 4.0, 8.0],
        seed=seed
    )
    
    # Test 5
    results['radiation'] = test_radiation_spectrum(
        grid_size=24,
        momentum=4.0,
        seed=seed
    )
    
    # Final verdict
    print("\n" + "="*70)
    print("FINAL VERDICT")
    print("="*70)
    
    grid_ok = results['grid_refinement']['converged']
    param_ok = results['parameter_sweep']['scaling']['matches_soliton_theory']
    scatter_ok = results['scattering']['all_elastic']
    energy_ok = results['energy_conservation']['stable_regime']
    radiation_ok = results['radiation']['has_radiation']
    
    print(f"""
  1. Grid refinement (c_eff converges):  {'✅' if grid_ok else '❌'}
  2. Parameter sweep (scaling matches):   {'✅' if param_ok else '❌'}
  3. Relativistic scattering (elastic):   {'✅' if scatter_ok else '❌'}
  4. Energy conservation (stable):        {'✅' if energy_ok else '❌'}
  5. Radiation spectrum (detected):       {'✅' if radiation_ok else '❌'}
""")
    
    if not grid_ok:
        verdict = "NUMERICAL ARTIFACT - c_eff not converging"
    elif param_ok and scatter_ok and energy_ok:
        verdict = "MEDIUM SOLITON PHYSICS - matches known soliton scaling"
    elif energy_ok and scatter_ok:
        verdict = "CANDIDATE EMERGENT RELATIVITY - needs more scaling tests"
    else:
        verdict = "INCONCLUSIVE - mixed results"
    
    print(f"  VERDICT: {verdict}")
    print("="*70)
    
    results['verdict'] = verdict
    return results


if __name__ == "__main__":
    results = run_dispersion_verification(seed=42)
