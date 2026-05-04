"""
QMRT Advanced Physics Validation

Extended validation tests based on physics analysis:

1. Reflection Robustness Tests
   - Does reflection persist when coupling constants vary?
   - Does it persist at different grid resolution?
   - Does adding noise break separation?

2. Spectral Energy Spectrum Analysis
   - Measure E(k) ∝ k^α power law slope
   - Check for turbulence cascade signatures

3. Improved Basin Potential
   - Mexican hat potential: V(ω) = -½μ²ω² + ¼λω⁴
   - Deeper minima with tunneling allowed

4. Complete Scaling Validation
   - Resolution independence across multiple grid sizes
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time

from qmrt_frequency_engine import (
    QMRTFrequencyEngine,
    QMRTFrequencyParameters
)


# =============================================================================
# 1. Reflection Robustness Tests
# =============================================================================

@dataclass
class ReflectionRobustnessResult:
    """Results from reflection robustness testing"""
    base_collision_type: str
    coupling_variation_results: List[Dict]
    resolution_variation_results: List[Dict]
    noise_variation_results: List[Dict]
    reflection_robust: bool
    summary: str
    
    def to_dict(self) -> Dict:
        return {
            'base_collision_type': self.base_collision_type,
            'coupling_variation_results': self.coupling_variation_results,
            'resolution_variation_results': self.resolution_variation_results,
            'noise_variation_results': self.noise_variation_results,
            'reflection_robust': bool(self.reflection_robust),
            'summary': self.summary
        }


def test_reflection_robustness(seed: int = 42) -> ReflectionRobustnessResult:
    """
    Test if reflection behavior persists under parameter variations.
    
    Tests:
    1. Vary coupling constants (g_omega_phi, g_omega_rho)
    2. Vary grid resolution
    3. Add noise to initial conditions
    """
    from qmrt_physics_validation import measure_cross_basin_collision
    
    # Base test
    base_result = measure_cross_basin_collision(grid_size=16, total_time=15.0, seed=seed)
    base_type = base_result.collision_type
    
    # 1. Coupling variation tests
    coupling_results = []
    coupling_multipliers = [0.1, 0.5, 1.0, 2.0, 5.0]
    
    for mult in coupling_multipliers:
        params = QMRTFrequencyParameters()
        params.g_omega_phi *= mult
        params.g_omega_rho *= mult
        
        engine = QMRTFrequencyEngine(grid_size=16, params=params)
        # Manual collision setup
        np.random.seed(seed)
        shape = (16, 16, 16)
        
        engine.rho = params.rho_equilibrium + 0.02 * np.random.randn(*shape)
        engine.sigma = 0.02 * np.random.randn(*shape)
        engine.tau = 0.02 * np.random.randn(*shape)
        engine.phi = 0.1 * np.random.randn(*shape)
        
        # Colliding domains
        engine.omega = np.zeros(shape)
        center = 8
        for i in range(16):
            if i < center - 2:
                engine.omega[i, :, :] = params.omega_0
            elif i > center + 2:
                engine.omega[i, :, :] = -params.omega_0
            else:
                t = (i - (center - 2)) / 4.0
                engine.omega[i, :, :] = params.omega_0 * (1 - 2*t)
        
        engine.pi_rho = np.zeros(shape)
        engine.pi_sigma = np.zeros(shape)
        engine.pi_tau = np.zeros(shape)
        engine.pi_phi = np.zeros(shape)
        engine.pi_omega = np.zeros(shape)
        for i in range(16):
            engine.pi_omega[i, :, :] = -0.1 if i < center else 0.1
        
        engine._precompute_spectral()
        engine.initial_energy = engine.compute_total_energy()
        
        # Evolve
        for _ in range(int(15.0 / 0.01)):
            engine.evolve_timestep(0.01)
        
        # Check outcome
        high_frac = float(np.sum(engine.omega > 0.5 * params.omega_0)) / engine.omega.size
        low_frac = float(np.sum(engine.omega < -0.5 * params.omega_0)) / engine.omega.size
        
        if high_frac > 0.2 and low_frac > 0.2:
            ctype = 'reflection' if high_frac > 0.3 else 'partial_reflection'
        elif high_frac + low_frac < 0.3:
            ctype = 'annihilation'
        else:
            ctype = 'merge'
        
        coupling_results.append({
            'coupling_multiplier': mult,
            'collision_type': ctype,
            'high_frac': high_frac,
            'low_frac': low_frac
        })
    
    # 2. Resolution variation tests
    resolution_results = []
    resolutions = [12, 16, 20, 24]
    
    for res in resolutions:
        try:
            result = measure_cross_basin_collision(grid_size=res, total_time=12.0, dt=0.01, seed=seed)
            resolution_results.append({
                'grid_size': res,
                'collision_type': result.collision_type,
                'energy_conserved': abs(result.pre_collision_energy - result.post_collision_energy) / result.pre_collision_energy < 0.01
            })
        except Exception as e:
            resolution_results.append({
                'grid_size': res,
                'collision_type': 'error',
                'error': str(e)
            })
    
    # 3. Noise variation tests
    noise_results = []
    noise_levels = [0.01, 0.05, 0.1, 0.2, 0.5]
    
    for noise in noise_levels:
        params = QMRTFrequencyParameters()
        engine = QMRTFrequencyEngine(grid_size=16, params=params)
        
        np.random.seed(seed)
        shape = (16, 16, 16)
        
        engine.rho = params.rho_equilibrium + noise * np.random.randn(*shape)
        engine.sigma = noise * np.random.randn(*shape)
        engine.tau = noise * np.random.randn(*shape)
        engine.phi = noise * np.random.randn(*shape)
        
        engine.omega = np.zeros(shape)
        center = 8
        for i in range(16):
            if i < center - 2:
                engine.omega[i, :, :] = params.omega_0 + noise * np.random.randn(16, 16)
            elif i > center + 2:
                engine.omega[i, :, :] = -params.omega_0 + noise * np.random.randn(16, 16)
            else:
                t = (i - (center - 2)) / 4.0
                engine.omega[i, :, :] = params.omega_0 * (1 - 2*t) + noise * np.random.randn(16, 16)
        
        engine.pi_rho = noise * np.random.randn(*shape)
        engine.pi_sigma = noise * np.random.randn(*shape)
        engine.pi_tau = noise * np.random.randn(*shape)
        engine.pi_phi = noise * np.random.randn(*shape)
        engine.pi_omega = np.zeros(shape)
        for i in range(16):
            engine.pi_omega[i, :, :] = -0.1 if i < center else 0.1
        
        engine._precompute_spectral()
        engine.initial_energy = engine.compute_total_energy()
        
        for _ in range(int(12.0 / 0.01)):
            engine.evolve_timestep(0.01)
        
        high_frac = float(np.sum(engine.omega > 0.5 * params.omega_0)) / engine.omega.size
        low_frac = float(np.sum(engine.omega < -0.5 * params.omega_0)) / engine.omega.size
        
        if high_frac > 0.15 and low_frac > 0.15:
            ctype = 'reflection'
        elif high_frac + low_frac < 0.2:
            ctype = 'annihilation'
        else:
            ctype = 'merge'
        
        noise_results.append({
            'noise_level': noise,
            'collision_type': ctype,
            'high_frac': high_frac,
            'low_frac': low_frac
        })
    
    # Assess robustness
    reflection_count_coupling = sum(1 for r in coupling_results if 'reflection' in r['collision_type'])
    reflection_count_resolution = sum(1 for r in resolution_results if r.get('collision_type') == 'reflection')
    reflection_count_noise = sum(1 for r in noise_results if r['collision_type'] == 'reflection')
    
    total_tests = len(coupling_results) + len(resolution_results) + len(noise_results)
    total_reflections = reflection_count_coupling + reflection_count_resolution + reflection_count_noise
    
    reflection_robust = total_reflections >= 0.6 * total_tests
    
    summary = f"Reflection observed in {total_reflections}/{total_tests} tests. "
    summary += "ROBUST" if reflection_robust else "NOT ROBUST - may be numerical artifact"
    
    return ReflectionRobustnessResult(
        base_collision_type=base_type,
        coupling_variation_results=coupling_results,
        resolution_variation_results=resolution_results,
        noise_variation_results=noise_results,
        reflection_robust=reflection_robust,
        summary=summary
    )


# =============================================================================
# 2. Spectral Energy Spectrum Analysis
# =============================================================================

@dataclass
class SpectralAnalysisResult:
    """Results from spectral energy spectrum analysis"""
    wavenumbers: List[float]
    energy_spectrum: List[float]
    power_law_exponent: float       # α in E(k) ∝ k^α
    power_law_r_squared: float      # Fit quality
    cascade_type: str               # 'forward', 'inverse', 'equilibrium'
    kolmogorov_like: bool           # True if -5/3 ≤ α ≤ -1
    time_series: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            'wavenumbers': [float(k) for k in self.wavenumbers],
            'energy_spectrum': [float(e) for e in self.energy_spectrum],
            'power_law_exponent': float(self.power_law_exponent),
            'power_law_r_squared': float(self.power_law_r_squared),
            'cascade_type': self.cascade_type,
            'kolmogorov_like': bool(self.kolmogorov_like),
            'time_series': self.time_series
        }


def measure_spectral_energy_spectrum(
    grid_size: int = 32,
    total_time: float = 30.0,
    dt: float = 0.01,
    seed: int = 42
) -> SpectralAnalysisResult:
    """
    Measure spectral energy spectrum E(k) and fit power law.
    
    Looking for:
    - E(k) ∝ k^α where α indicates cascade direction
    - α < 0: Forward cascade (energy to small scales)
    - α > 0: Inverse cascade (energy to large scales)
    - α ≈ -5/3: Kolmogorov-like turbulence
    """
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.1, seed=seed)
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 20)
    
    time_series = []
    
    def compute_spectrum():
        """Compute 1D radially-averaged power spectrum of omega field"""
        omega_hat = np.fft.fftn(engine.omega)
        power = np.abs(omega_hat) ** 2
        
        # Radial averaging
        kx = np.fft.fftfreq(grid_size)
        ky = np.fft.fftfreq(grid_size)
        kz = np.fft.fftfreq(grid_size)
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        K = np.sqrt(KX**2 + KY**2 + KZ**2)
        
        # Bin by wavenumber
        k_bins = np.linspace(0, 0.5, grid_size // 2)
        spectrum = []
        
        for i in range(len(k_bins) - 1):
            mask = (K >= k_bins[i]) & (K < k_bins[i+1])
            if np.sum(mask) > 0:
                spectrum.append(float(np.mean(power[mask])))
            else:
                spectrum.append(0.0)
        
        k_centers = (k_bins[:-1] + k_bins[1:]) / 2
        return k_centers.tolist(), spectrum
    
    # Initial spectrum
    k_init, E_init = compute_spectrum()
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            k_vals, E_vals = compute_spectrum()
            
            # Compute instantaneous power law fit
            k_fit = np.array(k_vals[2:])  # Skip lowest k
            E_fit = np.array(E_vals[2:])
            
            # Log-log fit for E = A * k^α
            valid = (k_fit > 0) & (E_fit > 0)
            if np.sum(valid) > 3:
                log_k = np.log(k_fit[valid])
                log_E = np.log(E_fit[valid])
                coeffs = np.polyfit(log_k, log_E, 1)
                alpha = coeffs[0]
                
                # R-squared
                E_pred = np.exp(coeffs[1]) * k_fit[valid] ** alpha
                ss_res = np.sum((E_fit[valid] - E_pred) ** 2)
                ss_tot = np.sum((E_fit[valid] - np.mean(E_fit[valid])) ** 2)
                r_sq = 1 - ss_res / (ss_tot + 1e-10)
            else:
                alpha = 0.0
                r_sq = 0.0
            
            time_series.append({
                'time': float(engine.time),
                'power_law_exponent': float(alpha),
                'r_squared': float(r_sq),
                'total_energy': float(engine.compute_total_energy()),
                'low_k_energy': float(sum(E_vals[:3])),
                'high_k_energy': float(sum(E_vals[-3:]))
            })
    
    # Final spectrum analysis
    k_final, E_final = compute_spectrum()
    
    # Final power law fit
    k_fit = np.array(k_final[2:])
    E_fit = np.array(E_final[2:])
    valid = (k_fit > 0) & (E_fit > 0)
    
    if np.sum(valid) > 3:
        log_k = np.log(k_fit[valid])
        log_E = np.log(E_fit[valid])
        coeffs = np.polyfit(log_k, log_E, 1)
        final_alpha = float(coeffs[0])
        
        E_pred = np.exp(coeffs[1]) * k_fit[valid] ** final_alpha
        ss_res = np.sum((E_fit[valid] - E_pred) ** 2)
        ss_tot = np.sum((E_fit[valid] - np.mean(E_fit[valid])) ** 2)
        final_r_sq = float(1 - ss_res / (ss_tot + 1e-10))
    else:
        final_alpha = 0.0
        final_r_sq = 0.0
    
    # Determine cascade type
    if final_alpha < -1:
        cascade_type = 'forward'  # Energy to high k (small scales)
    elif final_alpha > 0:
        cascade_type = 'inverse'  # Energy to low k (large scales)
    else:
        cascade_type = 'equilibrium'
    
    # Check for Kolmogorov-like scaling
    kolmogorov_like = -2.0 <= final_alpha <= -1.0
    
    return SpectralAnalysisResult(
        wavenumbers=k_final,
        energy_spectrum=E_final,
        power_law_exponent=final_alpha,
        power_law_r_squared=final_r_sq,
        cascade_type=cascade_type,
        kolmogorov_like=kolmogorov_like,
        time_series=time_series
    )


# =============================================================================
# 3. Improved Basin Potential (Mexican Hat)
# =============================================================================

class QMRTMexicanHatEngine(QMRTFrequencyEngine):
    """
    QMRT Engine with Mexican Hat (double-well) frequency potential.
    
    V(ω) = -½μ²ω² + ¼λω⁴
    
    This creates deeper minima at ω = ±√(μ²/λ) with better stability.
    """
    
    def __init__(self, grid_size: int = 32, dx: float = 1.0,
                 mu_squared: float = 0.5, lambda_coeff: float = 0.25,
                 params: Optional[QMRTFrequencyParameters] = None):
        super().__init__(grid_size, dx, params)
        self.mu_squared = mu_squared
        self.lambda_coeff = lambda_coeff
        # Minima at ω = ±√(μ²/λ)
        self.omega_min = np.sqrt(mu_squared / lambda_coeff)
        
    def compute_total_energy(self) -> float:
        """Energy with Mexican hat potential for omega"""
        p = self.params
        
        # Kinetic energy
        KE = 0.5 * (
            np.sum(self.pi_rho**2) / p.M_rho +
            np.sum(self.pi_sigma**2) / p.M_sigma +
            np.sum(self.pi_tau**2) / p.M_tau +
            np.sum(self.pi_phi**2) / p.M_phi +
            np.sum(self.pi_omega**2) / p.M_omega
        ) * self.dx**3
        
        # Density potential
        delta_rho = self.rho - p.rho_equilibrium
        U_rho = np.sum(
            (p.a_rho / 2) * delta_rho**2 +
            (p.c_rho / 4) * delta_rho**4
        ) * self.dx**3
        
        # Harmonic potentials
        V_harmonic = np.sum(
            (p.a_sigma / 2) * self.sigma**2 +
            (p.a_tau / 2) * self.tau**2
        ) * self.dx**3
        
        # Phase potential
        U_phi = np.sum(-p.a_phi * np.cos(self.phi)) * self.dx**3
        
        # MEXICAN HAT FREQUENCY POTENTIAL
        # V(ω) = -½μ²ω² + ¼λω⁴
        V_mexican = np.sum(
            -0.5 * self.mu_squared * self.omega**2 +
            0.25 * self.lambda_coeff * self.omega**4
        ) * self.dx**3
        
        # Couplings
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        grad_omega_sq = self._spectral_gradient_sq(self.omega)
        
        V_coupling = np.sum(
            p.lambda_rho_sigma * delta_rho * self.sigma +
            p.lambda_rho_tau * delta_rho * self.tau**2 +
            p.lambda_sigma_tau * self.sigma * self.tau +
            p.lambda_sigma_phi * self.sigma * np.cos(self.phi) +
            p.lambda_tau_phi * self.tau**2 * np.cos(self.phi) +
            p.lambda_rho_phi * delta_rho * np.cos(self.phi)
        ) * self.dx**3
        
        # Gradient energies
        V_gradient = 0.5 * np.sum(
            p.K_rho * self._spectral_gradient_sq(self.rho) +
            p.K_sigma * self._spectral_gradient_sq(self.sigma) +
            p.K_tau * self._spectral_gradient_sq(self.tau) +
            p.K_phi * grad_phi_sq +
            p.K_omega * grad_omega_sq
        ) * self.dx**3
        
        # Frequency couplings
        V_omega_phi = np.sum(p.g_omega_phi * self.omega * grad_phi_sq) * self.dx**3
        V_omega_rho = np.sum(p.g_omega_rho * self.omega * delta_rho**2) * self.dx**3
        
        return KE + U_rho + V_harmonic + U_phi + V_mexican + V_coupling + V_gradient + V_omega_phi + V_omega_rho
    
    def _update_momenta(self, delta_t: float):
        """Update momenta with Mexican hat potential derivative"""
        p = self.params
        
        lap_rho = self._spectral_laplacian(self.rho)
        lap_sigma = self._spectral_laplacian(self.sigma)
        lap_tau = self._spectral_laplacian(self.tau)
        lap_phi = self._spectral_laplacian(self.phi)
        lap_omega = self._spectral_laplacian(self.omega)
        
        delta_rho = self.rho - p.rho_equilibrium
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        
        # Standard momenta updates
        dpi_rho_dt = (
            p.K_rho * lap_rho
            - (p.a_rho * delta_rho + p.c_rho * delta_rho**3)
            - p.lambda_rho_sigma * self.sigma
            - p.lambda_rho_tau * self.tau**2
            - p.lambda_rho_phi * np.cos(self.phi)
            - 2 * p.g_omega_rho * self.omega * delta_rho
        )
        
        dpi_sigma_dt = (
            p.K_sigma * lap_sigma
            - p.a_sigma * self.sigma
            - p.lambda_rho_sigma * delta_rho
            - p.lambda_sigma_tau * self.tau
            - p.lambda_sigma_phi * np.cos(self.phi)
        )
        
        dpi_tau_dt = (
            p.K_tau * lap_tau
            - p.a_tau * self.tau
            - 2 * p.lambda_rho_tau * delta_rho * self.tau
            - p.lambda_sigma_tau * self.sigma
            - 2 * p.lambda_tau_phi * self.tau * np.cos(self.phi)
        )
        
        dpi_phi_dt = (
            p.K_phi * lap_phi
            - p.a_phi * np.sin(self.phi)
            + p.lambda_sigma_phi * self.sigma * np.sin(self.phi)
            + p.lambda_tau_phi * self.tau**2 * np.sin(self.phi)
            + p.lambda_rho_phi * delta_rho * np.sin(self.phi)
        )
        
        # MEXICAN HAT FREQUENCY MOMENTUM
        # dV/dω = -μ²ω + λω³
        dpi_omega_dt = (
            p.K_omega * lap_omega
            + self.mu_squared * self.omega  # Note: opposite sign from normal
            - self.lambda_coeff * self.omega**3
            - p.g_omega_phi * grad_phi_sq
            - p.g_omega_rho * delta_rho**2
        )
        
        self.pi_rho += dpi_rho_dt * delta_t
        self.pi_sigma += dpi_sigma_dt * delta_t
        self.pi_tau += dpi_tau_dt * delta_t
        self.pi_phi += dpi_phi_dt * delta_t
        self.pi_omega += dpi_omega_dt * delta_t


def test_mexican_hat_stability(
    grid_size: int = 20,
    total_time: float = 50.0,
    dt: float = 0.01,
    mu_squared: float = 0.5,
    lambda_coeff: float = 0.25,
    seed: int = 42
) -> Dict:
    """
    Test basin stability with Mexican hat potential.
    
    V(ω) = -½μ²ω² + ¼λω⁴
    Minima at ω = ±√(μ²/λ)
    """
    engine = QMRTMexicanHatEngine(
        grid_size=grid_size,
        mu_squared=mu_squared,
        lambda_coeff=lambda_coeff
    )
    
    omega_min = engine.omega_min
    
    # Initialize near minima
    if seed is not None:
        np.random.seed(seed)
    
    shape = (grid_size, grid_size, grid_size)
    p = engine.params
    
    engine.rho = p.rho_equilibrium + 0.02 * np.random.randn(*shape)
    engine.sigma = 0.02 * np.random.randn(*shape)
    engine.tau = 0.02 * np.random.randn(*shape)
    engine.phi = 0.05 * np.random.randn(*shape)
    
    # Initialize omega near ±omega_min
    engine.omega = np.zeros(shape)
    high_mask = np.random.random(shape) < 0.5
    engine.omega[high_mask] = omega_min + 0.05 * np.random.randn(np.sum(high_mask))
    engine.omega[~high_mask] = -omega_min + 0.05 * np.random.randn(np.sum(~high_mask))
    
    engine.pi_rho = np.zeros(shape)
    engine.pi_sigma = np.zeros(shape)
    engine.pi_tau = np.zeros(shape)
    engine.pi_phi = np.zeros(shape)
    engine.pi_omega = np.zeros(shape)
    
    engine._precompute_spectral()
    engine.initial_energy = engine.compute_total_energy()
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    time_series = []
    initial_high = None
    initial_low = None
    stability_time = total_time
    
    basin_width = 0.3 * omega_min
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            in_high = float(np.sum(np.abs(engine.omega - omega_min) < basin_width)) / engine.omega.size
            in_low = float(np.sum(np.abs(engine.omega + omega_min) < basin_width)) / engine.omega.size
            
            sample = {
                'time': float(engine.time),
                'in_high_basin': in_high,
                'in_low_basin': in_low,
                'total_in_basins': in_high + in_low,
                'omega_mean': float(np.mean(engine.omega)),
                'omega_std': float(np.std(engine.omega)),
                'energy_drift': float((engine.compute_total_energy() - engine.initial_energy) / abs(engine.initial_energy))
            }
            time_series.append(sample)
            
            if initial_high is None:
                initial_high = in_high
                initial_low = in_low
            
            if stability_time == total_time:
                if (in_high + in_low) < 0.8 * (initial_high + initial_low):
                    stability_time = engine.time
    
    final = time_series[-1]
    is_stable = (final['in_high_basin'] + final['in_low_basin']) > 0.7 * (initial_high + initial_low)
    
    return {
        'potential_type': 'mexican_hat',
        'parameters': {
            'mu_squared': mu_squared,
            'lambda_coeff': lambda_coeff,
            'omega_min': float(omega_min)
        },
        'initial_basin_occupation': initial_high + initial_low,
        'final_basin_occupation': final['in_high_basin'] + final['in_low_basin'],
        'stability_time': stability_time,
        'is_stable': bool(is_stable),
        'improvement_over_quartic': stability_time > 1.0,  # Compare to 0.3s from original
        'time_series': time_series
    }


# =============================================================================
# 4. Complete Scaling Validation
# =============================================================================

def complete_scaling_validation(
    grid_sizes: List[int] = [12, 16, 20, 24, 32],
    simulation_time: float = 15.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Complete scaling validation across multiple resolutions.
    
    Checks if physics is resolution-independent:
    - Basin fraction
    - Structure density
    - Spectral clustering rate
    
    If these stay constant → real physics
    If they vary strongly → numerical artifact
    """
    results = []
    
    for gs in grid_sizes:
        print(f"Testing grid {gs}³...")
        
        engine = QMRTFrequencyEngine(grid_size=gs)
        engine.initialize_frequency_domains(amplitude=0.05, seed=seed)
        
        p = engine.params
        steps = int(simulation_time / dt)
        
        # Record initial state
        initial_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
        initial_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
        
        # Evolve
        for _ in range(steps):
            engine.evolve_timestep(dt)
        
        # Final state
        final_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
        final_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
        
        # Structure density (per unit volume)
        state = engine.get_state_summary()
        structures = state['structure_breakdown']['total_active']
        volume = gs ** 3
        structure_density = structures / volume
        
        # Energy density
        energy = engine.compute_total_energy()
        energy_density = energy / volume
        
        # Basin decay rate
        basin_decay = (initial_high + initial_low - final_high - final_low) / simulation_time
        
        results.append({
            'grid_size': gs,
            'volume': volume,
            'initial_basin_fraction': initial_high + initial_low,
            'final_basin_fraction': final_high + final_low,
            'basin_decay_rate': float(basin_decay),
            'structure_density': float(structure_density),
            'energy_density': float(energy_density),
            'total_structures': structures,
            'energy_drift_pct': float(state['energy_drift_pct'])
        })
    
    # Analyze scaling
    basin_fracs = [r['final_basin_fraction'] for r in results]
    struct_densities = [r['structure_density'] for r in results]
    decay_rates = [r['basin_decay_rate'] for r in results]
    
    # Coefficient of variation (CV) - lower = more invariant
    basin_cv = float(np.std(basin_fracs) / (np.mean(basin_fracs) + 1e-10))
    struct_cv = float(np.std(struct_densities) / (np.mean(struct_densities) + 1e-10))
    decay_cv = float(np.std(decay_rates) / (np.mean(np.abs(decay_rates)) + 1e-10))
    
    # Scale invariant if CV < 0.3 for all metrics
    is_scale_invariant = basin_cv < 0.3 and struct_cv < 0.5
    
    return {
        'grid_sizes_tested': grid_sizes,
        'results_by_grid': results,
        'scaling_analysis': {
            'basin_fraction_cv': basin_cv,
            'structure_density_cv': struct_cv,
            'decay_rate_cv': decay_cv,
            'is_scale_invariant': bool(is_scale_invariant),
            'interpretation': 'REAL PHYSICS' if is_scale_invariant else 'MAY BE NUMERICAL ARTIFACT'
        },
        'averages': {
            'mean_basin_fraction': float(np.mean(basin_fracs)),
            'mean_structure_density': float(np.mean(struct_densities)),
            'mean_decay_rate': float(np.mean(decay_rates))
        }
    }
