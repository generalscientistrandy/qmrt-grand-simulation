"""
QMRT Eigenmode Stability Test

FOUNDATIONAL TEST - Must pass before any other validation is meaningful.

Goal: Prove basin = true attractor solution, not transient turbulence knot.

Physics:
    δψ(t) ~ e^(λt)
    
    Re(λ) < 0  → STABLE BASIN (true attractor)
    Re(λ) ≈ 0  → MARGINAL SOLITON (metastable)
    Re(λ) > 0  → FAKE STRUCTURE (transient turbulence)

Measurements:
    1. Perturbation decay rate (γ = -Re(λ))
    2. Oscillation eigenfrequency (ω_eigen = Im(λ))
    3. Spectral leakage rate (how fast energy leaves the basin mode)

Method:
    1. Initialize system with a clean single basin
    2. Apply small perturbation δψ
    3. Track perturbation amplitude A(t) = |δψ(t)|
    4. Fit A(t) = A_0 * exp(-γt) * cos(ω_eigen * t + φ)
    5. Extract eigenvalue λ = -γ + i*ω_eigen
    6. Classify stability based on Re(λ)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import time
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import (
    QMRTFrequencyEngine,
    QMRTFrequencyParameters
)


class BasinStabilityClass(Enum):
    """Classification based on eigenmode analysis"""
    STABLE_ATTRACTOR = "stable_attractor"      # Re(λ) < -threshold, perturbations decay
    BARRIER_STABLE = "barrier_stable"          # Perturbations grow but basin occupation preserved
    MARGINAL_SOLITON = "marginal_soliton"      # |Re(λ)| < threshold
    UNSTABLE_FAKE = "unstable_fake"            # Re(λ) > threshold AND basin occupation lost
    UNDETERMINED = "undetermined"              # Fit failed


@dataclass
class EigenmodeResult:
    """Result from eigenmode stability analysis"""
    
    # Primary eigenvalue estimate
    decay_rate: float              # γ = -Re(λ), positive if decaying
    oscillation_frequency: float   # ω_eigen = Im(λ)
    complex_eigenvalue: complex    # λ = -γ + i*ω_eigen
    
    # Classification
    stability_class: BasinStabilityClass
    confidence: float              # 0-1, based on fit quality
    
    # Raw measurements
    perturbation_amplitude_initial: float
    perturbation_amplitude_final: float
    amplitude_ratio: float         # A_final / A_initial
    
    # Spectral analysis
    spectral_leakage_rate: float   # Rate of energy leaving basin mode
    spectral_width_initial: float
    spectral_width_final: float
    
    # Fit quality metrics
    fit_r_squared: float
    fit_residual_std: float
    
    # Time series for plotting
    time_points: List[float]
    amplitude_history: List[float]
    fitted_curve: List[float]
    
    # Metadata
    perturbation_type: str
    perturbation_magnitude: float
    basin_type: str                # 'high' or 'low' frequency basin
    grid_size: int
    total_time: float
    
    def to_dict(self) -> Dict:
        return {
            'decay_rate': float(self.decay_rate),
            'oscillation_frequency': float(self.oscillation_frequency),
            'complex_eigenvalue': {
                'real': float(self.complex_eigenvalue.real),
                'imag': float(self.complex_eigenvalue.imag)
            },
            'stability_class': self.stability_class.value,
            'confidence': float(self.confidence),
            'perturbation_amplitude_initial': float(self.perturbation_amplitude_initial),
            'perturbation_amplitude_final': float(self.perturbation_amplitude_final),
            'amplitude_ratio': float(self.amplitude_ratio),
            'spectral_leakage_rate': float(self.spectral_leakage_rate),
            'spectral_width_initial': float(self.spectral_width_initial),
            'spectral_width_final': float(self.spectral_width_final),
            'fit_r_squared': float(self.fit_r_squared),
            'fit_residual_std': float(self.fit_residual_std),
            'time_points': [float(t) for t in self.time_points],
            'amplitude_history': [float(a) for a in self.amplitude_history],
            'fitted_curve': [float(f) for f in self.fitted_curve],
            'perturbation_type': self.perturbation_type,
            'perturbation_magnitude': float(self.perturbation_magnitude),
            'basin_type': self.basin_type,
            'grid_size': int(self.grid_size),
            'total_time': float(self.total_time),
            'interpretation': self._get_interpretation()
        }
    
    def _get_interpretation(self) -> str:
        if self.stability_class == BasinStabilityClass.STABLE_ATTRACTOR:
            return f"TRUE ATTRACTOR: Perturbations decay with γ={self.decay_rate:.4f}. Basin is dynamically stable."
        elif self.stability_class == BasinStabilityClass.MARGINAL_SOLITON:
            return f"MARGINAL SOLITON: Near-zero decay rate γ={self.decay_rate:.4f}. Structure is metastable."
        elif self.stability_class == BasinStabilityClass.UNSTABLE_FAKE:
            return f"FAKE STRUCTURE: Perturbations grow (γ={self.decay_rate:.4f} < 0). This is transient turbulence, not a real basin."
        else:
            return "UNDETERMINED: Eigenmode fit failed. Need more data or different parameters."


def damped_oscillation(t: np.ndarray, A0: float, gamma: float, omega: float, phi: float, offset: float) -> np.ndarray:
    """
    Model function for damped oscillation:
    A(t) = A0 * exp(-gamma*t) * cos(omega*t + phi) + offset
    """
    return A0 * np.exp(-gamma * t) * np.cos(omega * t + phi) + offset


def pure_exponential(t: np.ndarray, A0: float, gamma: float, offset: float) -> np.ndarray:
    """
    Pure exponential decay (no oscillation):
    A(t) = A0 * exp(-gamma*t) + offset
    """
    return A0 * np.exp(-gamma * t) + offset


def classify_basin_stability(decay_rate: float, threshold: float = 0.01) -> BasinStabilityClass:
    """
    Classify basin stability based on decay rate.
    
    Args:
        decay_rate: γ = -Re(λ). Positive means decaying (stable).
        threshold: Classification boundary
    
    Returns:
        BasinStabilityClass enum
    """
    if decay_rate > threshold:
        return BasinStabilityClass.STABLE_ATTRACTOR
    elif decay_rate < -threshold:
        return BasinStabilityClass.UNSTABLE_FAKE
    else:
        return BasinStabilityClass.MARGINAL_SOLITON


def initialize_clean_basin(
    engine: QMRTFrequencyEngine,
    basin_type: str = 'high',
    smoothness: float = 2.0
) -> None:
    """
    Initialize engine with a single, clean frequency basin.
    
    No turbulence, no noise - just one coherent basin structure.
    """
    p = engine.params
    shape = (engine.grid_size, engine.grid_size, engine.grid_size)
    
    # Set equilibrium fields
    engine.rho = np.full(shape, p.rho_equilibrium)
    engine.sigma = np.zeros(shape)
    engine.tau = np.zeros(shape)
    engine.phi = np.zeros(shape)  # Matter basin
    
    # Create smooth single-frequency basin
    # Use Gaussian profile centered in the box
    center = engine.grid_size // 2
    x = np.arange(engine.grid_size) - center
    y = np.arange(engine.grid_size) - center
    z = np.arange(engine.grid_size) - center
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    R = np.sqrt(X**2 + Y**2 + Z**2)
    
    # Smooth transition to basin value
    sigma_r = engine.grid_size / smoothness
    profile = np.exp(-R**2 / (2 * sigma_r**2))
    
    if basin_type == 'high':
        engine.omega = p.omega_0 * profile
    else:
        engine.omega = -p.omega_0 * profile
    
    # Zero momenta (stationary initial condition)
    engine.pi_rho = np.zeros(shape)
    engine.pi_sigma = np.zeros(shape)
    engine.pi_tau = np.zeros(shape)
    engine.pi_phi = np.zeros(shape)
    engine.pi_omega = np.zeros(shape)
    
    # Initialize spectral arrays
    engine._precompute_spectral()
    engine.initial_energy = engine.compute_total_energy()


def apply_perturbation(
    engine: QMRTFrequencyEngine,
    perturbation_type: str = 'gaussian_noise',
    magnitude: float = 0.01,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Apply a small perturbation to the basin and return the perturbation field.
    
    Types:
        'gaussian_noise': Random Gaussian perturbation to omega
        'localized_bump': Localized perturbation at center
        'spectral_mode': Single Fourier mode perturbation
    
    Returns:
        The perturbation field δω for tracking
    """
    if seed is not None:
        np.random.seed(seed)
    
    shape = engine.omega.shape
    
    if perturbation_type == 'gaussian_noise':
        delta_omega = magnitude * np.random.randn(*shape)
        # Smooth it slightly to avoid grid-scale noise
        from scipy.ndimage import gaussian_filter
        delta_omega = gaussian_filter(delta_omega, sigma=1.0)
        
    elif perturbation_type == 'localized_bump':
        center = engine.grid_size // 2
        x = np.arange(engine.grid_size) - center
        y = np.arange(engine.grid_size) - center
        z = np.arange(engine.grid_size) - center
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        R = np.sqrt(X**2 + Y**2 + Z**2)
        delta_omega = magnitude * np.exp(-R**2 / 8)
        
    elif perturbation_type == 'spectral_mode':
        # Single low-k Fourier mode
        k_mode = 2  # Low wavenumber
        x = np.linspace(0, 2*np.pi, engine.grid_size)
        y = np.linspace(0, 2*np.pi, engine.grid_size)
        z = np.linspace(0, 2*np.pi, engine.grid_size)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        delta_omega = magnitude * np.sin(k_mode * X) * np.sin(k_mode * Y) * np.sin(k_mode * Z)
    
    else:
        raise ValueError(f"Unknown perturbation type: {perturbation_type}")
    
    # Apply perturbation
    engine.omega = engine.omega + delta_omega
    
    # Also perturb momentum slightly to excite dynamics
    engine.pi_omega = engine.pi_omega + 0.1 * magnitude * np.random.randn(*shape)
    
    # Update energy
    engine.initial_energy = engine.compute_total_energy()
    
    return delta_omega


def compute_perturbation_amplitude(
    omega_current: np.ndarray,
    omega_reference: np.ndarray,
    method: str = 'rms'
) -> float:
    """
    Compute amplitude of perturbation from reference state.
    
    Methods:
        'rms': Root mean square deviation
        'max': Maximum absolute deviation
        'l2': L2 norm
    """
    delta = omega_current - omega_reference
    
    if method == 'rms':
        return float(np.sqrt(np.mean(delta**2)))
    elif method == 'max':
        return float(np.max(np.abs(delta)))
    elif method == 'l2':
        return float(np.linalg.norm(delta.flatten()))
    else:
        return float(np.sqrt(np.mean(delta**2)))


def compute_spectral_width(omega: np.ndarray) -> float:
    """
    Compute spectral width of omega field in Fourier space.
    
    This measures how spread out the energy is in k-space.
    """
    omega_hat = np.fft.fftn(omega)
    power = np.abs(omega_hat)**2
    
    # Compute k values
    n = omega.shape[0]
    kx = np.fft.fftfreq(n)
    ky = np.fft.fftfreq(n)
    kz = np.fft.fftfreq(n)
    KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
    K_mag = np.sqrt(KX**2 + KY**2 + KZ**2)
    
    # Weighted average k (spectral centroid)
    total_power = np.sum(power)
    if total_power < 1e-10:
        return 0.0
    
    k_mean = np.sum(K_mag * power) / total_power
    k_sq_mean = np.sum(K_mag**2 * power) / total_power
    
    # Spectral width = std of k
    spectral_width = np.sqrt(k_sq_mean - k_mean**2)
    
    return float(spectral_width)


def run_eigenmode_stability_test(
    grid_size: int = 24,
    total_time: float = 50.0,
    dt: float = 0.01,
    basin_type: str = 'high',
    perturbation_type: str = 'gaussian_noise',
    perturbation_magnitude: float = 0.01,
    seed: int = 42,
    stability_threshold: float = 0.01
) -> EigenmodeResult:
    """
    Run the full eigenmode stability test.
    
    This is the FOUNDATIONAL test for QMRT basin physics.
    
    Args:
        grid_size: Simulation grid size
        total_time: Total simulation time
        dt: Timestep
        basin_type: 'high' or 'low' frequency basin
        perturbation_type: Type of perturbation to apply
        perturbation_magnitude: Size of perturbation (relative to omega_0)
        seed: Random seed
        stability_threshold: Threshold for classification
    
    Returns:
        EigenmodeResult with full stability analysis
    """
    print(f"="*60)
    print("QMRT EIGENMODE STABILITY TEST")
    print(f"="*60)
    print(f"Grid: {grid_size}³, Time: {total_time}s, Basin: {basin_type}")
    print(f"Perturbation: {perturbation_type}, magnitude={perturbation_magnitude}")
    
    # Initialize engine
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    
    # Create clean basin (no turbulence)
    print("\n[1/5] Initializing clean basin...")
    initialize_clean_basin(engine, basin_type=basin_type)
    
    # Store reference state (unperturbed basin)
    omega_reference = engine.omega.copy()
    
    # Apply perturbation
    print("[2/5] Applying perturbation...")
    delta_omega_initial = apply_perturbation(
        engine, 
        perturbation_type=perturbation_type,
        magnitude=perturbation_magnitude * engine.params.omega_0,
        seed=seed
    )
    
    # Initial measurements
    A_initial = compute_perturbation_amplitude(engine.omega, omega_reference)
    spectral_width_initial = compute_spectral_width(engine.omega)
    
    print(f"    Initial perturbation amplitude: {A_initial:.6f}")
    print(f"    Initial spectral width: {spectral_width_initial:.6f}")
    
    # Evolution tracking
    print("[3/5] Evolving system and tracking perturbation...")
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 200)  # ~200 samples
    
    time_points = []
    amplitude_history = []
    spectral_width_history = []
    
    for step in range(steps):
        engine.evolve_timestep(dt, enforce_conservation=True)
        
        if step % sample_interval == 0:
            t = float(engine.time)
            A = compute_perturbation_amplitude(engine.omega, omega_reference)
            sw = compute_spectral_width(engine.omega)
            
            time_points.append(t)
            amplitude_history.append(A)
            spectral_width_history.append(sw)
    
    # Final measurements
    A_final = amplitude_history[-1]
    spectral_width_final = spectral_width_history[-1]
    amplitude_ratio = A_final / A_initial if A_initial > 1e-10 else 0.0
    
    print(f"    Final perturbation amplitude: {A_final:.6f}")
    print(f"    Amplitude ratio (final/initial): {amplitude_ratio:.4f}")
    
    # Fit eigenmode dynamics
    print("[4/5] Fitting eigenmode dynamics...")
    
    t_arr = np.array(time_points)
    A_arr = np.array(amplitude_history)
    
    # Normalize for fitting
    A_norm = A_arr / A_initial
    
    # Try damped oscillation fit first
    fit_success = False
    decay_rate = 0.0
    oscillation_freq = 0.0
    fitted_curve = np.zeros_like(A_arr)
    r_squared = 0.0
    residual_std = float('inf')
    
    # Method 1: Damped oscillation A(t) = A0 * exp(-γt) * cos(ωt + φ) + offset
    try:
        # Initial guesses
        gamma_guess = -np.log(amplitude_ratio + 1e-10) / total_time
        omega_guess = 2 * np.pi / (total_time / 5)  # Assume ~5 oscillations
        
        popt, pcov = curve_fit(
            damped_oscillation,
            t_arr, A_norm,
            p0=[1.0, max(gamma_guess, 0.001), omega_guess, 0.0, 0.0],
            bounds=([0.1, -1.0, 0.0, -np.pi, -0.5], [2.0, 2.0, 50.0, np.pi, 0.5]),
            maxfev=5000
        )
        
        A0_fit, gamma_fit, omega_fit, phi_fit, offset_fit = popt
        
        fitted_curve = damped_oscillation(t_arr, *popt) * A_initial
        
        # Compute R-squared
        ss_res = np.sum((A_arr - fitted_curve)**2)
        ss_tot = np.sum((A_arr - np.mean(A_arr))**2)
        r_squared = 1 - ss_res / (ss_tot + 1e-10)
        residual_std = np.sqrt(ss_res / len(A_arr))
        
        if r_squared > 0.5:  # Reasonable fit
            decay_rate = gamma_fit
            oscillation_freq = omega_fit
            fit_success = True
            print(f"    Damped oscillation fit: γ={gamma_fit:.4f}, ω={omega_fit:.4f}, R²={r_squared:.4f}")
    
    except Exception as e:
        print(f"    Damped oscillation fit failed: {e}")
    
    # Method 2: Pure exponential if oscillation fit fails
    if not fit_success or r_squared < 0.5:
        try:
            gamma_guess = -np.log(amplitude_ratio + 1e-10) / total_time
            
            popt2, pcov2 = curve_fit(
                pure_exponential,
                t_arr, A_norm,
                p0=[1.0, max(gamma_guess, 0.001), 0.0],
                bounds=([0.1, -1.0, -0.5], [2.0, 2.0, 0.5]),
                maxfev=5000
            )
            
            A0_fit2, gamma_fit2, offset_fit2 = popt2
            
            fitted_curve2 = pure_exponential(t_arr, *popt2) * A_initial
            
            ss_res2 = np.sum((A_arr - fitted_curve2)**2)
            ss_tot2 = np.sum((A_arr - np.mean(A_arr))**2)
            r_squared2 = 1 - ss_res2 / (ss_tot2 + 1e-10)
            
            if r_squared2 > r_squared:
                decay_rate = gamma_fit2
                oscillation_freq = 0.0
                fitted_curve = fitted_curve2
                r_squared = r_squared2
                residual_std = np.sqrt(ss_res2 / len(A_arr))
                fit_success = True
                print(f"    Pure exponential fit: γ={gamma_fit2:.4f}, R²={r_squared2:.4f}")
        
        except Exception as e:
            print(f"    Pure exponential fit also failed: {e}")
    
    # Method 3: Simple log-linear fit as fallback
    if not fit_success:
        try:
            # log(A) = log(A0) - γt
            log_A = np.log(A_norm + 1e-10)
            coeffs = np.polyfit(t_arr, log_A, 1)
            decay_rate = -coeffs[0]
            oscillation_freq = 0.0
            
            fitted_curve = A_initial * np.exp(-decay_rate * t_arr)
            
            ss_res3 = np.sum((A_arr - fitted_curve)**2)
            ss_tot3 = np.sum((A_arr - np.mean(A_arr))**2)
            r_squared = 1 - ss_res3 / (ss_tot3 + 1e-10)
            residual_std = np.sqrt(ss_res3 / len(A_arr))
            fit_success = True
            print(f"    Log-linear fit: γ={decay_rate:.4f}, R²={r_squared:.4f}")
        
        except Exception as e:
            print(f"    All fits failed: {e}")
            decay_rate = -np.log(amplitude_ratio + 1e-10) / total_time
    
    # Compute spectral leakage rate
    if len(spectral_width_history) > 1:
        sw_arr = np.array(spectral_width_history)
        sw_change = (sw_arr[-1] - sw_arr[0]) / total_time
        spectral_leakage_rate = float(sw_change)
    else:
        spectral_leakage_rate = 0.0
    
    # Classification
    print("[5/5] Classifying stability...")
    stability_class = classify_basin_stability(decay_rate, stability_threshold)
    
    # Confidence based on fit quality
    confidence = min(1.0, max(0.0, r_squared))
    if not fit_success:
        stability_class = BasinStabilityClass.UNDETERMINED
        confidence = 0.0
    
    # Construct complex eigenvalue
    complex_eigenvalue = complex(-decay_rate, oscillation_freq)
    
    # Results
    result = EigenmodeResult(
        decay_rate=decay_rate,
        oscillation_frequency=oscillation_freq,
        complex_eigenvalue=complex_eigenvalue,
        stability_class=stability_class,
        confidence=confidence,
        perturbation_amplitude_initial=A_initial,
        perturbation_amplitude_final=A_final,
        amplitude_ratio=amplitude_ratio,
        spectral_leakage_rate=spectral_leakage_rate,
        spectral_width_initial=spectral_width_initial,
        spectral_width_final=spectral_width_final,
        fit_r_squared=r_squared,
        fit_residual_std=residual_std,
        time_points=time_points,
        amplitude_history=amplitude_history,
        fitted_curve=fitted_curve.tolist() if isinstance(fitted_curve, np.ndarray) else fitted_curve,
        perturbation_type=perturbation_type,
        perturbation_magnitude=perturbation_magnitude,
        basin_type=basin_type,
        grid_size=grid_size,
        total_time=total_time
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("EIGENMODE STABILITY RESULT")
    print(f"{'='*60}")
    print(f"  Decay rate (γ):         {decay_rate:.6f}")
    print(f"  Oscillation freq (ω):   {oscillation_freq:.6f}")
    print(f"  Complex eigenvalue:     λ = {complex_eigenvalue}")
    print(f"  Fit R²:                 {r_squared:.4f}")
    print(f"  Stability class:        {stability_class.value}")
    print(f"  Confidence:             {confidence:.2%}")
    print(f"\n  INTERPRETATION: {result._get_interpretation()}")
    print(f"{'='*60}\n")
    
    return result


def run_multi_perturbation_test(
    grid_size: int = 20,
    total_time: float = 30.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Run eigenmode test with multiple perturbation types for robustness.
    
    This gives higher confidence in the stability classification.
    """
    perturbation_types = ['gaussian_noise', 'localized_bump', 'spectral_mode']
    basin_types = ['high', 'low']
    
    results = []
    
    for basin in basin_types:
        for pert in perturbation_types:
            print(f"\n>>> Testing: basin={basin}, perturbation={pert}")
            
            result = run_eigenmode_stability_test(
                grid_size=grid_size,
                total_time=total_time,
                dt=dt,
                basin_type=basin,
                perturbation_type=pert,
                seed=seed
            )
            
            results.append({
                'basin_type': basin,
                'perturbation_type': pert,
                'decay_rate': float(result.decay_rate),
                'oscillation_frequency': float(result.oscillation_frequency),
                'stability_class': result.stability_class.value,
                'confidence': float(result.confidence),
                'fit_r_squared': float(result.fit_r_squared)
            })
    
    # Aggregate analysis
    stable_count = sum(1 for r in results if r['stability_class'] == 'stable_attractor')
    marginal_count = sum(1 for r in results if r['stability_class'] == 'marginal_soliton')
    unstable_count = sum(1 for r in results if r['stability_class'] == 'unstable_fake')
    
    mean_decay = np.mean([r['decay_rate'] for r in results])
    std_decay = np.std([r['decay_rate'] for r in results])
    mean_confidence = np.mean([r['confidence'] for r in results])
    
    # Overall classification
    if stable_count >= len(results) * 0.7:
        overall_class = 'STABLE_ATTRACTOR'
    elif unstable_count >= len(results) * 0.5:
        overall_class = 'UNSTABLE_FAKE'
    elif marginal_count >= len(results) * 0.5:
        overall_class = 'MARGINAL_SOLITON'
    else:
        overall_class = 'MIXED'
    
    return {
        'individual_results': results,
        'summary': {
            'total_tests': len(results),
            'stable_count': stable_count,
            'marginal_count': marginal_count,
            'unstable_count': unstable_count,
            'mean_decay_rate': float(mean_decay),
            'std_decay_rate': float(std_decay),
            'mean_confidence': float(mean_confidence),
            'overall_classification': overall_class,
            'interpretation': f"Basin is classified as {overall_class} based on {len(results)} perturbation tests."
        }
    }


# =============================================================================
# COMPREHENSIVE STABILITY TEST (Local + Global)
# =============================================================================

@dataclass
class ComprehensiveStabilityResult:
    """
    Result from comprehensive stability analysis.
    
    Distinguishes between:
    - Attractor stability (local perturbations decay)
    - Barrier stability (local perturbations grow but basin occupation preserved)
    - True instability (both local and global instability)
    """
    
    # Local eigenmode analysis
    local_decay_rate: float           # γ for local perturbations
    local_growth_factor: float        # A_final / A_initial
    local_oscillation_freq: float
    
    # Global basin preservation
    basin_high_initial: float
    basin_high_final: float
    basin_low_initial: float
    basin_low_final: float
    basin_preservation_ratio: float   # How much basin occupation is preserved (0-1)
    
    # Classification
    stability_type: str               # 'attractor', 'barrier', 'marginal', 'unstable'
    eigenvalue: complex
    
    # Time series
    time_points: List[float]
    local_amplitude_history: List[float]
    basin_high_history: List[float]
    basin_low_history: List[float]
    
    # Metadata
    grid_size: int
    total_time: float
    perturbation_magnitude: float
    
    def to_dict(self) -> Dict:
        return {
            'local_decay_rate': float(self.local_decay_rate),
            'local_growth_factor': float(self.local_growth_factor),
            'local_oscillation_freq': float(self.local_oscillation_freq),
            'basin_high_initial': float(self.basin_high_initial),
            'basin_high_final': float(self.basin_high_final),
            'basin_low_initial': float(self.basin_low_initial),
            'basin_low_final': float(self.basin_low_final),
            'basin_preservation_ratio': float(self.basin_preservation_ratio),
            'stability_type': self.stability_type,
            'eigenvalue': {
                'real': float(self.eigenvalue.real),
                'imag': float(self.eigenvalue.imag)
            },
            'time_points': [float(t) for t in self.time_points],
            'local_amplitude_history': [float(a) for a in self.local_amplitude_history],
            'basin_high_history': [float(h) for h in self.basin_high_history],
            'basin_low_history': [float(l) for l in self.basin_low_history],
            'grid_size': int(self.grid_size),
            'total_time': float(self.total_time),
            'perturbation_magnitude': float(self.perturbation_magnitude),
            'interpretation': self._get_interpretation()
        }
    
    def _get_interpretation(self) -> str:
        if self.stability_type == 'attractor':
            return f"TRUE ATTRACTOR: Local perturbations decay (γ={self.local_decay_rate:.4f}). Basin is dynamically stable."
        elif self.stability_type == 'barrier':
            return f"BARRIER STABILITY: Local perturbations grow ({self.local_growth_factor:.2f}x) but basin occupation preserved ({self.basin_preservation_ratio:.1%}). This is phase-separation physics."
        elif self.stability_type == 'marginal':
            return f"MARGINAL STABILITY: Neither strong decay nor growth. Basin preservation: {self.basin_preservation_ratio:.1%}"
        else:
            return f"UNSTABLE: Both local growth and basin occupation loss. Not a stable structure."


def run_comprehensive_stability_test(
    grid_size: int = 20,
    stabilization_time: float = 10.0,
    perturbation_time: float = 20.0,
    dt: float = 0.01,
    perturbation_magnitude: float = 0.05,
    seed: int = 42
) -> ComprehensiveStabilityResult:
    """
    Run comprehensive stability test that distinguishes attractor vs barrier stability.
    
    Method:
    1. Initialize with frequency domains
    2. Let system stabilize (form natural basins)
    3. Apply perturbation
    4. Track BOTH local perturbation amplitude AND global basin occupation
    5. Classify based on both metrics
    """
    print("="*60)
    print("COMPREHENSIVE STABILITY TEST")
    print("="*60)
    print(f"Grid: {grid_size}³, Stabilization: {stabilization_time}s, Tracking: {perturbation_time}s")
    
    np.random.seed(seed)
    
    # Initialize engine
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    p = engine.params
    
    # Helper function for basin metrics
    def get_basin_occupation():
        in_high = np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width) / engine.omega.size
        in_low = np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width) / engine.omega.size
        return float(in_high), float(in_low)
    
    # Phase 1: Stabilization
    print(f"\n[1/4] Stabilization phase ({stabilization_time}s)...")
    stabilization_steps = int(stabilization_time / dt)
    for _ in range(stabilization_steps):
        engine.evolve_timestep(dt)
    
    h0, l0 = get_basin_occupation()
    print(f"    Basin occupation: High={h0:.2%}, Low={l0:.2%}")
    
    # Store reference state
    omega_ref = engine.omega.copy()
    
    # Phase 2: Apply perturbation
    print(f"\n[2/4] Applying perturbation (magnitude={perturbation_magnitude})...")
    from scipy.ndimage import gaussian_filter
    perturbation = perturbation_magnitude * p.omega_0 * np.random.randn(*engine.omega.shape)
    perturbation = gaussian_filter(perturbation, sigma=1.0)  # Smooth to avoid grid noise
    engine.omega += perturbation
    
    A_initial = np.sqrt(np.mean((engine.omega - omega_ref)**2))
    h1, l1 = get_basin_occupation()
    print(f"    Initial perturbation amplitude: {A_initial:.6f}")
    print(f"    Post-perturbation basins: High={h1:.2%}, Low={l1:.2%}")
    
    # Phase 3: Track evolution
    print(f"\n[3/4] Tracking evolution ({perturbation_time}s)...")
    tracking_steps = int(perturbation_time / dt)
    sample_interval = max(1, tracking_steps // 100)
    
    time_points = []
    local_amplitudes = []
    basin_high_history = []
    basin_low_history = []
    
    for step in range(tracking_steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            t = engine.time - stabilization_time
            A = np.sqrt(np.mean((engine.omega - omega_ref)**2))
            h, l = get_basin_occupation()
            
            time_points.append(float(t))
            local_amplitudes.append(float(A))
            basin_high_history.append(h)
            basin_low_history.append(l)
    
    # Final measurements
    A_final = local_amplitudes[-1]
    h_final = basin_high_history[-1]
    l_final = basin_low_history[-1]
    
    # Compute metrics
    local_growth_factor = A_final / A_initial if A_initial > 1e-10 else 0.0
    
    # Basin preservation: how much of original basin occupation remains
    high_preservation = 1.0 - abs(h_final - h0) / max(h0, 0.1)
    low_preservation = 1.0 - abs(l_final - l0) / max(l0, 0.1)
    basin_preservation = (high_preservation + low_preservation) / 2
    basin_preservation = max(0.0, min(1.0, basin_preservation))
    
    # Fit decay rate
    t_arr = np.array(time_points)
    A_arr = np.array(local_amplitudes)
    
    try:
        log_A = np.log(A_arr / A_initial + 1e-10)
        coeffs = np.polyfit(t_arr, log_A, 1)
        local_decay_rate = -coeffs[0]
    except:
        local_decay_rate = -np.log(local_growth_factor + 1e-10) / perturbation_time
    
    # Phase 4: Classification
    print(f"\n[4/4] Classification...")
    print(f"    Local growth factor: {local_growth_factor:.2f}x")
    print(f"    Local decay rate: {local_decay_rate:.4f}")
    print(f"    Basin preservation: {basin_preservation:.1%}")
    
    # Classification logic
    if local_decay_rate > 0.01:  # Perturbations decay
        stability_type = 'attractor'
    elif basin_preservation > 0.9:
        # Basins are preserved despite local perturbation growth
        # This is barrier stability (phase separation physics)
        stability_type = 'barrier'
    elif local_growth_factor < 2.0:
        stability_type = 'marginal'
    else:
        stability_type = 'unstable'
    
    eigenvalue = complex(-local_decay_rate, 0.0)  # Simplified, no oscillation measured
    
    result = ComprehensiveStabilityResult(
        local_decay_rate=local_decay_rate,
        local_growth_factor=local_growth_factor,
        local_oscillation_freq=0.0,
        basin_high_initial=h0,
        basin_high_final=h_final,
        basin_low_initial=l0,
        basin_low_final=l_final,
        basin_preservation_ratio=basin_preservation,
        stability_type=stability_type,
        eigenvalue=eigenvalue,
        time_points=time_points,
        local_amplitude_history=local_amplitudes,
        basin_high_history=basin_high_history,
        basin_low_history=basin_low_history,
        grid_size=grid_size,
        total_time=stabilization_time + perturbation_time,
        perturbation_magnitude=perturbation_magnitude
    )
    
    print(f"\n{'='*60}")
    print("COMPREHENSIVE STABILITY RESULT")
    print(f"{'='*60}")
    print(f"  Stability type:        {stability_type.upper()}")
    print(f"  Local decay rate:      {local_decay_rate:.4f}")
    print(f"  Local growth factor:   {local_growth_factor:.2f}x")
    print(f"  Basin preservation:    {basin_preservation:.1%}")
    print(f"\n  {result._get_interpretation()}")
    print(f"{'='*60}\n")
    
    return result


if __name__ == "__main__":
    # Run comprehensive test
    result = run_comprehensive_stability_test(
        grid_size=16,
        stabilization_time=5.0,
        perturbation_time=10.0,
        dt=0.02,
        perturbation_magnitude=0.05,
        seed=42
    )
    
    print("\nResult dict keys:", result.to_dict().keys())
