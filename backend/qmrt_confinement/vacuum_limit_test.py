"""
QMRT VACUUM LIMIT TEST: Uniform Substrate Experiment

Test excitation propagation in FULLY HOMOGENEOUS medium:
- No domain walls
- No phase boundaries  
- No defect traps

This isolates:
1. TRUE FREE-PARTICLE DISPERSION
2. INTRINSIC INERTIA
3. INTRINSIC SPEED LIMIT
4. ENTROPY LEAKAGE PATHWAYS

Only in uniform phase can we determine fundamental particle properties
separate from medium geometry effects.
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
# Uniform Substrate Initialization
# =============================================================================

def initialize_uniform_substrate(
    engine: QMRTFrequencyEngine,
    phase: str = 'high',  # 'high' (+ω₀) or 'low' (-ω₀)
    stabilization_steps: int = 200,
    dt: float = 0.02
) -> float:
    """
    Initialize engine to uniform phase state (no domain walls).
    
    Args:
        engine: QMRT engine
        phase: 'high' for +ω₀, 'low' for -ω₀
        stabilization_steps: Steps to let system relax
        dt: Timestep
    
    Returns:
        Background energy after stabilization
    """
    p = engine.params
    n = engine.grid_size
    
    # Set uniform omega field
    if phase == 'high':
        engine.omega = np.ones((n, n, n)) * p.omega_0
    else:
        engine.omega = np.ones((n, n, n)) * (-p.omega_0)
    
    # Zero all momenta (start at rest)
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
    
    # Precompute spectral coefficients (required for evolution)
    engine._precompute_spectral()
    engine.initial_energy = engine.compute_total_energy()
    
    # Let system relax to true equilibrium
    for _ in range(stabilization_steps):
        engine.evolve_timestep(dt)
    
    return engine.compute_total_energy()


def verify_uniform_substrate(engine: QMRTFrequencyEngine) -> Dict:
    """
    Verify substrate is truly uniform (no domain walls).
    """
    p = engine.params
    n = engine.grid_size
    
    # Check omega uniformity
    omega_mean = np.mean(engine.omega)
    omega_std = np.std(engine.omega)
    omega_deviation = omega_std / (abs(omega_mean) + 1e-10)
    
    # Check for domain walls (gradient energy)
    grad_omega_sq = (
        np.gradient(engine.omega, axis=0)**2 +
        np.gradient(engine.omega, axis=1)**2 +
        np.gradient(engine.omega, axis=2)**2
    )
    gradient_energy = np.sum(0.5 * p.K_omega * grad_omega_sq)
    
    # Domain wall count
    sign_changes_x = np.sum(np.abs(np.diff(np.sign(engine.omega), axis=0)) > 0)
    sign_changes_y = np.sum(np.abs(np.diff(np.sign(engine.omega), axis=1)) > 0)
    sign_changes_z = np.sum(np.abs(np.diff(np.sign(engine.omega), axis=2)) > 0)
    total_sign_changes = sign_changes_x + sign_changes_y + sign_changes_z
    
    is_uniform = (omega_deviation < 0.01) and (total_sign_changes == 0)
    
    return {
        'omega_mean': float(omega_mean),
        'omega_std': float(omega_std),
        'omega_deviation': float(omega_deviation),
        'gradient_energy': float(gradient_energy),
        'sign_changes': int(total_sign_changes),
        'is_uniform': is_uniform
    }


# =============================================================================
# Excitation Creation in Uniform Medium
# =============================================================================

def create_localized_excitation(
    engine: QMRTFrequencyEngine,
    position: Tuple[float, float, float],
    amplitude: float,
    width: float,
    momentum: Tuple[float, float, float] = (0, 0, 0)
) -> Dict:
    """
    Create a localized excitation (perturbation) in uniform medium.
    
    The excitation is a Gaussian deviation from the uniform background.
    
    Returns: excitation properties
    """
    p = engine.params
    n = engine.grid_size
    
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    px, py, pz = position
    R_sq = (X - px)**2 + (Y - py)**2 + (Z - pz)**2
    
    # Gaussian profile as perturbation
    profile = amplitude * np.exp(-R_sq / (2 * width**2))
    
    E_before = engine.compute_total_energy()
    
    # Add perturbation to omega
    engine.omega = engine.omega + profile
    
    # Add momentum if specified
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
    
    return {
        'position': position,
        'amplitude': amplitude,
        'width': width,
        'momentum': momentum,
        'energy_added': E_after - E_before
    }


# =============================================================================
# Propagation Tracking
# =============================================================================

def track_excitation_propagation(
    engine: QMRTFrequencyEngine,
    initial_position: Tuple[float, float, float],
    total_time: float = 20.0,
    dt: float = 0.02,
    amplitude_threshold: float = 0.1
) -> Dict:
    """
    Track excitation position, width, amplitude over time.
    
    Returns detailed trajectory and derived quantities.
    """
    p = engine.params
    n = engine.grid_size
    
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    # Reference background (uniform)
    omega_background = np.mean(engine.omega)
    
    trajectory = []
    energies = []
    entropies = []
    
    steps = int(total_time / dt)
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % 5 == 0:
            t = engine.time
            
            # Find excitation (deviation from background)
            excess = engine.omega - omega_background
            threshold = amplitude_threshold * np.max(np.abs(excess))
            mask = np.abs(excess) > threshold
            
            if np.sum(mask) > 5:
                # Center of mass
                weights = np.abs(excess[mask])
                total_weight = np.sum(weights)
                
                com_x = np.sum(X[mask] * weights) / total_weight
                com_y = np.sum(Y[mask] * weights) / total_weight
                com_z = np.sum(Z[mask] * weights) / total_weight
                
                # Amplitude (max deviation)
                amplitude = float(np.max(np.abs(excess)))
                
                # Width (RMS)
                R_sq_from_com = (X[mask] - com_x)**2 + (Y[mask] - com_y)**2 + (Z[mask] - com_z)**2
                width = float(np.sqrt(np.sum(R_sq_from_com * weights) / total_weight))
                
                # Local energy
                KE_local = 0.5 * engine.pi_omega**2 / p.M_omega
                PE_local = p.a_omega * (engine.omega**2 - p.omega_0**2)**2
                E_local = float(np.sum((KE_local + PE_local)[mask]))
                
                trajectory.append({
                    'time': t,
                    'position': (float(com_x), float(com_y), float(com_z)),
                    'amplitude': amplitude,
                    'width': width,
                    'local_energy': E_local
                })
            else:
                # Excitation dispersed
                trajectory.append({
                    'time': t,
                    'position': None,
                    'amplitude': 0.0,
                    'width': float('inf'),
                    'local_energy': 0.0
                })
            
            # Total energy
            energies.append(engine.compute_total_energy())
            
            # Entropy (spectral)
            omega_fft = np.abs(np.fft.fftn(engine.omega))**2
            omega_fft_norm = omega_fft / (np.sum(omega_fft) + 1e-10)
            spectral_entropy = -np.sum(omega_fft_norm * np.log(omega_fft_norm + 1e-10))
            entropies.append(spectral_entropy)
    
    return {
        'trajectory': trajectory,
        'energies': energies,
        'entropies': entropies,
        'total_time': total_time
    }


# =============================================================================
# Dispersion Analysis
# =============================================================================

def analyze_uniform_dispersion(
    grid_size: int = 32,
    momenta: List[float] = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0],
    excitation_amplitude: float = 0.2,
    measurement_time: float = 15.0,
    dt: float = 0.02
) -> Dict:
    """
    Measure dispersion relation E(p), v(p) in uniform substrate.
    
    This is the VACUUM LIMIT - no domain walls.
    """
    print("\n" + "="*70)
    print("VACUUM LIMIT TEST: Dispersion in Uniform Substrate")
    print("="*70)
    print("No domain walls, no phase boundaries, no defect traps")
    print("="*70)
    
    results = []
    
    for p_init in momenta:
        print(f"\n  Testing p = {p_init}...")
        
        # Fresh engine
        engine = QMRTFrequencyEngine(grid_size=grid_size)
        params = engine.params
        
        # Initialize UNIFORM substrate
        E_bg = initialize_uniform_substrate(engine, phase='high', stabilization_steps=100, dt=dt)
        
        # Verify uniformity
        uniform_check = verify_uniform_substrate(engine)
        if not uniform_check['is_uniform']:
            print(f"    ⚠️ Substrate not uniform! std/mean = {uniform_check['omega_deviation']:.4f}")
        
        # Create excitation with momentum (along x)
        center = grid_size // 2
        start_x = grid_size // 4
        
        exc_info = create_localized_excitation(
            engine,
            position=(start_x, center, center),
            amplitude=excitation_amplitude * params.omega_0,
            width=3.0,
            momentum=(p_init, 0, 0)
        )
        
        E_initial = engine.compute_total_energy()
        
        # Track propagation
        tracking = track_excitation_propagation(
            engine,
            initial_position=(start_x, center, center),
            total_time=measurement_time,
            dt=dt
        )
        
        # Extract velocity from trajectory
        valid_points = [t for t in tracking['trajectory'] if t['position'] is not None]
        
        if len(valid_points) > 5:
            times = [t['time'] for t in valid_points]
            x_positions = [t['position'][0] for t in valid_points]
            
            # Linear fit for velocity
            slope, intercept, r_value, _, _ = linregress(times, x_positions)
            velocity = slope
            r_squared = r_value**2
            
            # Average amplitude (stability)
            amplitudes = [t['amplitude'] for t in valid_points]
            avg_amplitude = np.mean(amplitudes)
            amplitude_decay = (amplitudes[0] - amplitudes[-1]) / (amplitudes[0] + 1e-10)
            
            # Average width (dispersion)
            widths = [t['width'] for t in valid_points if t['width'] < float('inf')]
            if widths:
                avg_width = np.mean(widths)
                width_growth = (widths[-1] - widths[0]) / (widths[0] + 1e-10)
            else:
                avg_width = float('inf')
                width_growth = float('inf')
            
            # Energy at excitation
            local_energies = [t['local_energy'] for t in valid_points]
            avg_local_energy = np.mean(local_energies)
        else:
            velocity = 0.0
            r_squared = 0.0
            avg_amplitude = 0.0
            amplitude_decay = 1.0
            avg_width = float('inf')
            width_growth = float('inf')
            avg_local_energy = 0.0
        
        # Energy conservation
        E_final = tracking['energies'][-1] if tracking['energies'] else E_initial
        E_conservation_error = abs(E_final - E_initial) / E_initial
        
        # Entropy change (leakage)
        if tracking['entropies']:
            S_initial = tracking['entropies'][0]
            S_final = tracking['entropies'][-1]
            entropy_change = S_final - S_initial
        else:
            entropy_change = 0.0
        
        result = {
            'momentum': p_init,
            'velocity': velocity,
            'velocity_r_squared': r_squared,
            'energy_added': exc_info['energy_added'],
            'local_energy': avg_local_energy,
            'amplitude_decay': amplitude_decay,
            'width_growth': width_growth,
            'E_conservation_error': E_conservation_error,
            'entropy_change': entropy_change
        }
        results.append(result)
        
        print(f"    v = {velocity:.5f} (R²={r_squared:.3f})")
        print(f"    E_local = {avg_local_energy:.2f}")
        print(f"    Amplitude decay: {amplitude_decay:.1%}")
        print(f"    Width growth: {width_growth:.1%}")
        print(f"    ΔS = {entropy_change:.4f}")
    
    # Dispersion analysis
    print("\n" + "="*70)
    print("DISPERSION ANALYSIS (Uniform Substrate)")
    print("="*70)
    
    p_data = np.array([r['momentum'] for r in results])
    v_data = np.array([r['velocity'] for r in results])
    E_data = np.array([r['local_energy'] for r in results])
    
    print(f"\n  {'p':>8} | {'v':>12} | {'E':>12} | {'m_eff':>12}")
    print("-"*50)
    for r in results:
        m_eff = r['momentum'] / (r['velocity'] + 1e-10) if r['velocity'] > 0.001 else float('inf')
        print(f"  {r['momentum']:>8.2f} | {r['velocity']:>12.5f} | {r['local_energy']:>12.2f} | {m_eff:>12.1f}")
    
    # Fit dispersion models
    valid_mask = (p_data > 0.1) & (v_data > 0.001)
    
    fits = {}
    
    if np.sum(valid_mask) >= 3:
        p_fit = p_data[valid_mask]
        v_fit = v_data[valid_mask]
        E_fit = E_data[valid_mask]
        
        # Model 1: v = p/m (free particle)
        try:
            m_free = np.sum(p_fit) / np.sum(v_fit)
            v_pred = p_fit / m_free
            r2 = 1 - np.sum((v_fit - v_pred)**2) / (np.sum((v_fit - np.mean(v_fit))**2) + 1e-10)
            fits['free_particle'] = {'m': m_free, 'r_squared': r2}
            print(f"\n  Free particle: v = p/{m_free:.1f}  (R²={r2:.4f})")
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
            print(f"  Saturating: v = {v_max:.4f} * tanh(p/{p0:.2f})  (R²={r2:.4f})")
        except:
            pass
        
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
            print(f"  Relativistic: v = {c_rel:.4f}*p/√({m_rel:.1f}²*{c_rel:.4f}² + p²)  (R²={r2:.4f})")
        except:
            pass
    
    # Determine best fit
    best_model = None
    best_r2 = -1
    for name, fit in fits.items():
        if fit['r_squared'] > best_r2:
            best_r2 = fit['r_squared']
            best_model = name
    
    # Intrinsic properties
    print("\n" + "="*70)
    print("INTRINSIC PARTICLE PROPERTIES (Vacuum Limit)")
    print("="*70)
    
    if best_model == 'free_particle':
        print(f"\n  DISPERSION TYPE: FREE PARTICLE (Galilean)")
        print(f"  Intrinsic mass: m = {fits['free_particle']['m']:.2f}")
        print(f"  Dispersion: E = p²/2m (non-relativistic)")
        intrinsic_mass = fits['free_particle']['m']
        speed_limit = float('inf')
        
    elif best_model == 'relativistic':
        print(f"\n  DISPERSION TYPE: RELATIVISTIC-LIKE")
        print(f"  Intrinsic mass: m₀ = {fits['relativistic']['m']:.2f}")
        print(f"  Speed limit: c_eff = {fits['relativistic']['c']:.5f}")
        print(f"  Dispersion: E² = p²c² + m²c⁴")
        intrinsic_mass = fits['relativistic']['m']
        speed_limit = fits['relativistic']['c']
        
    elif best_model == 'saturating':
        print(f"\n  DISPERSION TYPE: SATURATING (Medium-Limited)")
        print(f"  Maximum velocity: v_max = {fits['saturating']['v_max']:.5f}")
        print(f"  Characteristic momentum: p₀ = {fits['saturating']['p0']:.2f}")
        intrinsic_mass = fits['saturating']['p0'] / fits['saturating']['v_max']
        speed_limit = fits['saturating']['v_max']
        
    else:
        print(f"\n  DISPERSION TYPE: ANOMALOUS / INCONCLUSIVE")
        intrinsic_mass = 0
        speed_limit = 0
    
    # Entropy leakage analysis
    entropy_changes = [r['entropy_change'] for r in results]
    avg_entropy_rate = np.mean(entropy_changes) / measurement_time
    
    print(f"\n  Entropy leakage rate: {avg_entropy_rate:.6f} per unit time")
    if avg_entropy_rate > 0.001:
        print("  ⚠️ Significant entropy production (not truly conservative)")
    else:
        print("  ✅ Low entropy production (quasi-conservative)")
    
    return {
        'dispersion_data': results,
        'fits': fits,
        'best_model': best_model,
        'intrinsic_mass': intrinsic_mass,
        'speed_limit': speed_limit,
        'entropy_rate': avg_entropy_rate
    }


# =============================================================================
# Stability Test in Uniform Medium
# =============================================================================

def test_excitation_stability_uniform(
    grid_size: int = 32,
    amplitude: float = 0.2,
    total_time: float = 50.0,
    dt: float = 0.02
) -> Dict:
    """
    Test if excitation is stable in uniform medium (no momentum).
    
    Measures:
    - Lifetime (time until amplitude drops to 50%)
    - Dispersion rate (width growth)
    - Energy localization
    """
    print("\n" + "="*70)
    print("STABILITY TEST: Excitation in Uniform Substrate")
    print("="*70)
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    params = engine.params
    
    # Initialize uniform
    E_bg = initialize_uniform_substrate(engine, phase='high', stabilization_steps=100, dt=dt)
    
    uniform_check = verify_uniform_substrate(engine)
    print(f"  Substrate uniform: {'✅' if uniform_check['is_uniform'] else '❌'}")
    
    # Create stationary excitation
    center = grid_size // 2
    exc_info = create_localized_excitation(
        engine,
        position=(center, center, center),
        amplitude=amplitude * params.omega_0,
        width=3.0,
        momentum=(0, 0, 0)
    )
    
    initial_amplitude = amplitude * params.omega_0
    
    # Track over time
    times = []
    amplitudes = []
    widths = []
    
    n = grid_size
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    omega_bg = params.omega_0
    
    steps = int(total_time / dt)
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % 10 == 0:
            excess = engine.omega - omega_bg
            
            # Amplitude
            amp = float(np.max(np.abs(excess)))
            amplitudes.append(amp)
            times.append(engine.time)
            
            # Width
            mask = np.abs(excess) > 0.1 * amp
            if np.sum(mask) > 5:
                weights = np.abs(excess[mask])
                total_weight = np.sum(weights)
                com_x = np.sum(X[mask] * weights) / total_weight
                com_y = np.sum(Y[mask] * weights) / total_weight
                com_z = np.sum(Z[mask] * weights) / total_weight
                R_sq = (X[mask] - com_x)**2 + (Y[mask] - com_y)**2 + (Z[mask] - com_z)**2
                width = float(np.sqrt(np.sum(R_sq * weights) / total_weight))
            else:
                width = float('inf')
            widths.append(width)
    
    # Find half-life
    half_life = total_time
    for i, (t, a) in enumerate(zip(times, amplitudes)):
        if a < 0.5 * initial_amplitude:
            half_life = t
            break
    
    # Dispersion rate (width growth rate)
    valid_widths = [(t, w) for t, w in zip(times, widths) if w < float('inf')]
    if len(valid_widths) > 5:
        t_arr = np.array([v[0] for v in valid_widths])
        w_arr = np.array([v[1] for v in valid_widths])
        dispersion_rate, _, _, _, _ = linregress(t_arr, w_arr)
    else:
        dispersion_rate = 0.0
    
    print(f"\n  Initial amplitude: {initial_amplitude:.4f}")
    print(f"  Final amplitude: {amplitudes[-1]:.4f}")
    print(f"  Half-life: {half_life:.1f}s")
    print(f"  Dispersion rate: {dispersion_rate:.4f} /s")
    
    stable = half_life >= total_time * 0.9
    print(f"\n  STABLE: {'✅ YES' if stable else '❌ NO (disperses)'}")
    
    return {
        'initial_amplitude': initial_amplitude,
        'final_amplitude': amplitudes[-1],
        'half_life': half_life,
        'dispersion_rate': dispersion_rate,
        'stable': stable,
        'times': times,
        'amplitudes': amplitudes,
        'widths': widths
    }


# =============================================================================
# Main: Complete Vacuum Limit Test Suite
# =============================================================================

def run_vacuum_limit_tests(grid_size: int = 28) -> Dict:
    """
    Run complete vacuum limit test suite.
    """
    print("\n" + "="*70)
    print("QMRT VACUUM LIMIT TEST SUITE")
    print("="*70)
    print("Testing in uniform substrate (no domain walls)")
    print("="*70)
    
    results = {}
    
    # Test 1: Stability
    results['stability'] = test_excitation_stability_uniform(
        grid_size=grid_size,
        amplitude=0.2,
        total_time=30.0
    )
    
    # Test 2: Dispersion relation
    results['dispersion'] = analyze_uniform_dispersion(
        grid_size=grid_size,
        momenta=[0.0, 0.5, 1.0, 2.0, 4.0, 8.0],
        excitation_amplitude=0.2,
        measurement_time=12.0
    )
    
    # Summary
    print("\n" + "="*70)
    print("VACUUM LIMIT RESULTS SUMMARY")
    print("="*70)
    
    print(f"""
  STABILITY:
    Excitation half-life: {results['stability']['half_life']:.1f}s
    Dispersion rate: {results['stability']['dispersion_rate']:.4f}/s
    Stable: {'✅' if results['stability']['stable'] else '❌'}
    
  DISPERSION:
    Best model: {results['dispersion']['best_model']}
    Intrinsic mass: {results['dispersion']['intrinsic_mass']:.2f}
    Speed limit: {results['dispersion']['speed_limit']:.5f}
    Entropy rate: {results['dispersion']['entropy_rate']:.6f}/s
    
  INTERPRETATION:
""")
    
    if results['stability']['stable']:
        if results['dispersion']['best_model'] == 'free_particle':
            print("    → STABLE FREE PARTICLES (Galilean, non-relativistic)")
        elif results['dispersion']['best_model'] == 'relativistic':
            print("    → STABLE RELATIVISTIC PARTICLES (with effective c)")
        elif results['dispersion']['best_model'] == 'saturating':
            print("    → STABLE PARTICLES with MEDIUM-LIMITED VELOCITY")
        else:
            print("    → STABLE but ANOMALOUS dispersion")
    else:
        print("    → UNSTABLE: Excitations disperse in uniform medium")
        print("    → Localized particles may REQUIRE domain structure")
    
    print("="*70)
    
    return results


if __name__ == "__main__":
    results = run_vacuum_limit_tests(grid_size=28)
