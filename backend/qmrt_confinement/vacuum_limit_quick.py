"""
QMRT VACUUM LIMIT TEST - QUICK VERSION
Optimized for faster execution with smaller grid and shorter times
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy.optimize import curve_fit
from scipy.stats import linregress

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters


def initialize_uniform_substrate(engine, phase='high', stabilization_steps=50, dt=0.02):
    """Initialize engine to uniform phase state (no domain walls)."""
    p = engine.params
    n = engine.grid_size
    
    # Set uniform omega field
    if phase == 'high':
        engine.omega = np.ones((n, n, n)) * p.omega_0
    else:
        engine.omega = np.ones((n, n, n)) * (-p.omega_0)
    
    # Zero all momenta
    engine.pi_omega = np.zeros((n, n, n))
    engine.pi_rho = np.zeros((n, n, n))
    engine.pi_sigma = np.zeros((n, n, n))
    engine.pi_tau = np.zeros((n, n, n))
    engine.pi_phi = np.zeros((n, n, n))
    
    # Set other fields to equilibrium
    engine.rho = np.ones((n, n, n)) * p.rho_equilibrium
    engine.sigma = np.zeros((n, n, n))
    engine.tau = np.zeros((n, n, n))
    engine.phi = np.zeros((n, n, n))
    
    # Precompute spectral coefficients
    engine._precompute_spectral()
    engine.initial_energy = engine.compute_total_energy()
    
    # Brief stabilization
    for _ in range(stabilization_steps):
        engine.evolve_timestep(dt)
    
    return engine.compute_total_energy()


def verify_uniform_substrate(engine):
    """Verify substrate is truly uniform (no domain walls)."""
    p = engine.params
    
    omega_mean = np.mean(engine.omega)
    omega_std = np.std(engine.omega)
    omega_deviation = omega_std / (abs(omega_mean) + 1e-10)
    
    # Domain wall count
    sign_changes = np.sum(np.abs(np.diff(np.sign(engine.omega), axis=0)) > 0)
    sign_changes += np.sum(np.abs(np.diff(np.sign(engine.omega), axis=1)) > 0)
    sign_changes += np.sum(np.abs(np.diff(np.sign(engine.omega), axis=2)) > 0)
    
    is_uniform = (omega_deviation < 0.01) and (sign_changes == 0)
    
    return {
        'omega_mean': float(omega_mean),
        'omega_std': float(omega_std),
        'omega_deviation': float(omega_deviation),
        'sign_changes': int(sign_changes),
        'is_uniform': is_uniform
    }


def create_localized_excitation(engine, position, amplitude, width, momentum=(0, 0, 0)):
    """Create a localized excitation (perturbation) in uniform medium."""
    n = engine.grid_size
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    px, py, pz = position
    R_sq = (X - px)**2 + (Y - py)**2 + (Z - pz)**2
    
    # Gaussian profile
    profile = amplitude * np.exp(-R_sq / (2 * width**2))
    
    E_before = engine.compute_total_energy()
    engine.omega = engine.omega + profile
    
    # Add momentum
    if any(m != 0 for m in momentum):
        grad_x = -profile * (X - px) / (width**2)
        grad_y = -profile * (Y - py) / (width**2)
        grad_z = -profile * (Z - pz) / (width**2)
        
        engine.pi_omega += (
            momentum[0] * grad_x +
            momentum[1] * grad_y +
            momentum[2] * grad_z
        )
    
    E_after = engine.compute_total_energy()
    
    return {'energy_added': E_after - E_before}


def measure_velocity(engine, initial_x, total_time=8.0, dt=0.02):
    """Measure excitation velocity from trajectory."""
    n = engine.grid_size
    p = engine.params
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    omega_background = p.omega_0  # Uniform background
    
    positions = []
    times = []
    
    steps = int(total_time / dt)
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % 10 == 0:
            excess = engine.omega - omega_background
            threshold = 0.1 * np.max(np.abs(excess))
            mask = np.abs(excess) > threshold
            
            if np.sum(mask) > 5:
                weights = np.abs(excess[mask])
                com_x = np.sum(X[mask] * weights) / np.sum(weights)
                positions.append(float(com_x))
                times.append(engine.time)
    
    # Linear fit for velocity
    if len(positions) > 3:
        slope, _, r_value, _, _ = linregress(times, positions)
        return slope, r_value**2
    return 0.0, 0.0


def run_quick_dispersion_test(grid_size=16, momenta=[0.0, 0.5, 1.0, 2.0, 4.0, 8.0]):
    """Quick dispersion test in uniform medium."""
    print("\n" + "="*70)
    print("VACUUM LIMIT TEST: Dispersion in Uniform Substrate")
    print("="*70)
    print(f"Grid: {grid_size}³, NO domain walls")
    print("="*70)
    
    results = []
    
    for p_init in momenta:
        print(f"\n  Testing p = {p_init}...", end=" ", flush=True)
        
        # Fresh engine
        engine = QMRTFrequencyEngine(grid_size=grid_size)
        params = engine.params
        
        # Initialize UNIFORM substrate
        E_bg = initialize_uniform_substrate(engine, phase='high', stabilization_steps=30, dt=0.02)
        
        # Verify uniformity
        uniform_check = verify_uniform_substrate(engine)
        
        # Create excitation with momentum (along x)
        center = grid_size // 2
        start_x = grid_size // 4
        
        exc_info = create_localized_excitation(
            engine,
            position=(start_x, center, center),
            amplitude=0.2 * params.omega_0,
            width=2.5,
            momentum=(p_init, 0, 0)
        )
        
        E_initial = engine.compute_total_energy()
        
        # Measure velocity
        velocity, r_squared = measure_velocity(engine, start_x, total_time=6.0, dt=0.02)
        
        E_final = engine.compute_total_energy()
        E_conservation_error = abs(E_final - E_initial) / E_initial
        
        result = {
            'momentum': p_init,
            'velocity': velocity,
            'r_squared': r_squared,
            'energy_added': exc_info['energy_added'],
            'E_conservation_error': E_conservation_error,
            'uniform': uniform_check['is_uniform']
        }
        results.append(result)
        
        print(f"v = {velocity:.5f} (R²={r_squared:.3f})")
    
    # Analysis
    print("\n" + "="*70)
    print("DISPERSION ANALYSIS")
    print("="*70)
    
    p_data = np.array([r['momentum'] for r in results])
    v_data = np.array([r['velocity'] for r in results])
    
    print(f"\n  {'p':>8} | {'v':>12} | {'m_eff=p/v':>12}")
    print("-"*40)
    for r in results:
        m_eff = r['momentum'] / (r['velocity'] + 1e-10) if r['velocity'] > 0.001 else float('inf')
        print(f"  {r['momentum']:>8.2f} | {r['velocity']:>12.5f} | {m_eff:>12.1f}")
    
    # Fit models
    valid_mask = (p_data > 0.1) & (v_data > 0.001)
    fits = {}
    
    if np.sum(valid_mask) >= 3:
        p_fit = p_data[valid_mask]
        v_fit = v_data[valid_mask]
        
        # Model 1: v = p/m (free particle, Galilean)
        try:
            m_free = np.sum(p_fit) / np.sum(v_fit)
            v_pred = p_fit / m_free
            r2 = 1 - np.sum((v_fit - v_pred)**2) / (np.sum((v_fit - np.mean(v_fit))**2) + 1e-10)
            fits['free_particle'] = {'m': m_free, 'r_squared': r2}
            print(f"\n  FREE PARTICLE: v = p/{m_free:.1f}  (R²={r2:.4f})")
        except:
            pass
        
        # Model 2: v = v_max * tanh(p/p0) (saturating)
        try:
            def saturating(p, v_max, p0):
                return v_max * np.tanh(p / p0)
            
            popt, _ = curve_fit(saturating, p_fit, v_fit, p0=[0.1, 2.0], maxfev=5000)
            v_max, p0 = popt
            v_pred = saturating(p_fit, *popt)
            r2 = 1 - np.sum((v_fit - v_pred)**2) / (np.sum((v_fit - np.mean(v_fit))**2) + 1e-10)
            fits['saturating'] = {'v_max': v_max, 'p0': p0, 'r_squared': r2}
            print(f"  SATURATING: v = {v_max:.5f} * tanh(p/{p0:.2f})  (R²={r2:.4f})")
        except Exception as e:
            print(f"  SATURATING: fit failed - {e}")
        
        # Model 3: v = c * p / sqrt(m²c² + p²) (relativistic)
        try:
            def relativistic_v(p, m, c):
                return c * p / np.sqrt(m**2 * c**2 + p**2)
            
            popt, _ = curve_fit(relativistic_v, p_fit, v_fit, p0=[10, 0.1], 
                               bounds=([0.1, 0.001], [1000, 10]), maxfev=5000)
            m_rel, c_rel = popt
            v_pred = relativistic_v(p_fit, *popt)
            r2 = 1 - np.sum((v_fit - v_pred)**2) / (np.sum((v_fit - np.mean(v_fit))**2) + 1e-10)
            fits['relativistic'] = {'m': m_rel, 'c': c_rel, 'r_squared': r2}
            print(f"  RELATIVISTIC: v = {c_rel:.5f}*p/√({m_rel:.1f}²*{c_rel:.5f}² + p²)  (R²={r2:.4f})")
        except Exception as e:
            print(f"  RELATIVISTIC: fit failed - {e}")
    
    # Best model
    best_model = None
    best_r2 = -1
    for name, fit in fits.items():
        if fit['r_squared'] > best_r2:
            best_r2 = fit['r_squared']
            best_model = name
    
    # Final verdict
    print("\n" + "="*70)
    print("VACUUM LIMIT VERDICT")
    print("="*70)
    
    if best_model == 'free_particle':
        print(f"\n  DISPERSION TYPE: GALILEAN (Free Particle)")
        print(f"  v = p/m with m = {fits['free_particle']['m']:.2f}")
        print(f"  NO speed limit (non-relativistic)")
        verdict = "GALILEAN"
    elif best_model == 'relativistic':
        print(f"\n  DISPERSION TYPE: RELATIVISTIC-LIKE")
        print(f"  Intrinsic mass: m₀ = {fits['relativistic']['m']:.2f}")
        print(f"  Speed limit: c_eff = {fits['relativistic']['c']:.5f}")
        print(f"  v → c_eff as p → ∞")
        verdict = "RELATIVISTIC"
    elif best_model == 'saturating':
        print(f"\n  DISPERSION TYPE: MEDIUM-LIMITED SATURATION")
        print(f"  Maximum velocity: v_max = {fits['saturating']['v_max']:.5f}")
        print(f"  Characteristic momentum: p₀ = {fits['saturating']['p0']:.2f}")
        verdict = "SATURATING"
    else:
        print(f"\n  DISPERSION TYPE: INCONCLUSIVE")
        verdict = "INCONCLUSIVE"
    
    print("="*70)
    
    return {
        'results': results,
        'fits': fits,
        'best_model': best_model,
        'verdict': verdict
    }


def run_stability_test(grid_size=16, total_time=20.0):
    """Test if excitation is stable in uniform medium."""
    print("\n" + "="*70)
    print("STABILITY TEST: Excitation in Uniform Substrate")
    print("="*70)
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    params = engine.params
    
    # Initialize uniform
    E_bg = initialize_uniform_substrate(engine, phase='high', stabilization_steps=30, dt=0.02)
    
    uniform_check = verify_uniform_substrate(engine)
    print(f"  Substrate uniform: {'YES' if uniform_check['is_uniform'] else 'NO'}")
    
    # Create stationary excitation
    center = grid_size // 2
    create_localized_excitation(
        engine,
        position=(center, center, center),
        amplitude=0.2 * params.omega_0,
        width=2.5,
        momentum=(0, 0, 0)
    )
    
    initial_amplitude = 0.2 * params.omega_0
    
    # Track over time
    times = []
    amplitudes = []
    
    n = grid_size
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    omega_bg = params.omega_0
    
    steps = int(total_time / 0.02)
    
    for step in range(steps):
        engine.evolve_timestep(0.02)
        
        if step % 20 == 0:
            excess = engine.omega - omega_bg
            amp = float(np.max(np.abs(excess)))
            amplitudes.append(amp)
            times.append(engine.time)
    
    # Find half-life
    half_life = total_time
    for i, (t, a) in enumerate(zip(times, amplitudes)):
        if a < 0.5 * initial_amplitude:
            half_life = t
            break
    
    final_amplitude = amplitudes[-1] if amplitudes else 0
    decay_ratio = final_amplitude / initial_amplitude
    
    print(f"\n  Initial amplitude: {initial_amplitude:.4f}")
    print(f"  Final amplitude: {final_amplitude:.4f}")
    print(f"  Decay ratio: {decay_ratio:.2%}")
    print(f"  Half-life: {half_life:.1f}s (test time: {total_time:.1f}s)")
    
    stable = half_life >= total_time * 0.9
    print(f"\n  STABLE: {'YES - excitation persists' if stable else 'NO - disperses/decays'}")
    
    return {
        'initial_amplitude': initial_amplitude,
        'final_amplitude': final_amplitude,
        'decay_ratio': decay_ratio,
        'half_life': half_life,
        'stable': stable
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("QMRT VACUUM LIMIT TEST SUITE (QUICK VERSION)")
    print("="*70)
    print("Testing in UNIFORM substrate - NO domain walls")
    print("This isolates TRUE FREE-PARTICLE properties")
    print("="*70)
    
    # Test 1: Stability
    stability = run_stability_test(grid_size=16, total_time=15.0)
    
    # Test 2: Dispersion
    dispersion = run_quick_dispersion_test(grid_size=16, momenta=[0.0, 0.5, 1.0, 2.0, 4.0, 8.0])
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"""
  STABILITY:
    Excitation stable: {'YES' if stability['stable'] else 'NO'}
    Decay ratio: {stability['decay_ratio']:.1%}
    Half-life: {stability['half_life']:.1f}s
    
  DISPERSION:
    Best model: {dispersion['best_model']}
    Verdict: {dispersion['verdict']}
""")
    
    if dispersion['verdict'] == 'GALILEAN':
        print("  CONCLUSION: QMRT vacuum has NON-RELATIVISTIC free particles")
        print("  → No fundamental speed limit in uniform medium")
        print("  → 'Relativistic' effects are MEDIUM GEOMETRY artifacts")
    elif dispersion['verdict'] == 'RELATIVISTIC':
        print("  CONCLUSION: QMRT vacuum has EMERGENT RELATIVITY")
        print("  → Fundamental speed limit c_eff exists")
        print("  → Lorentz-like symmetry may emerge")
    elif dispersion['verdict'] == 'SATURATING':
        print("  CONCLUSION: QMRT vacuum has MEDIUM-LIMITED dynamics")
        print("  → Speed saturates but NOT relativistic form")
        print("  → Non-linear medium response")
    
    print("="*70)
