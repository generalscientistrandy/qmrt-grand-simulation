"""
QMRT DECISIVE TEST: Dispersion Relation Extraction

This is THE test that determines the particle theory character.

Measure: E(p) or ω(k) for moving excitations

Possible outcomes:
1. E² = p²c² + m²c⁴  → Relativistic particles
2. E = p²/2m         → Non-relativistic (Galilean)
3. ω = ω₀√(1 + ξ²k²) → Nonlinear medium-limited velocity
4. E = √(m² + p²/c²) with c = c(ρ) → Medium-dependent "speed of light"
5. m_eff(v) varying  → Frequency-mass coupling

Method:
1. Create excitations with different momenta
2. Measure velocity v = dx/dt
3. Measure energy E
4. Extract dispersion relation E(p) where p = m_eff * v
5. Fit to candidate forms
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import curve_fit
from scipy.stats import linregress
import warnings

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters


@dataclass
class DispersionPoint:
    """Single measurement point on dispersion curve"""
    initial_momentum: float  # Applied momentum
    measured_velocity: float  # Actual velocity achieved
    measured_energy: float   # Total excitation energy
    kinetic_energy: float    # E - E_rest
    effective_momentum: float  # m_eff * v
    
    def to_dict(self) -> Dict:
        return {
            'p_initial': float(self.initial_momentum),
            'v_measured': float(self.measured_velocity),
            'E_measured': float(self.measured_energy),
            'E_kinetic': float(self.kinetic_energy),
            'p_effective': float(self.effective_momentum)
        }


@dataclass  
class DispersionResult:
    """Result from dispersion relation measurement"""
    
    # Raw data
    points: List[DispersionPoint] = field(default_factory=list)
    
    # Rest mass and energy
    rest_mass: float = 0.0
    rest_energy: float = 0.0
    
    # Fit results for different models
    fits: Dict = field(default_factory=dict)
    
    # Best fit
    best_model: str = ""
    best_params: Dict = field(default_factory=dict)
    best_r_squared: float = 0.0
    
    # Extracted physics
    effective_speed_limit: float = 0.0  # "c" analog
    mass_velocity_coupling: bool = False
    dispersion_type: str = ""  # 'relativistic', 'galilean', 'medium_limited', 'anomalous'
    
    def to_dict(self) -> Dict:
        return {
            'data_points': [p.to_dict() for p in self.points],
            'rest_mass': float(self.rest_mass),
            'rest_energy': float(self.rest_energy),
            'fits': self.fits,
            'best_model': self.best_model,
            'best_params': {k: float(v) for k, v in self.best_params.items()},
            'best_r_squared': float(self.best_r_squared),
            'effective_speed_limit': float(self.effective_speed_limit),
            'mass_velocity_coupling': self.mass_velocity_coupling,
            'dispersion_type': self.dispersion_type,
            'verdict': self._get_verdict()
        }
    
    def _get_verdict(self) -> str:
        if self.dispersion_type == 'relativistic':
            return f"RELATIVISTIC: E² = p²c² + m²c⁴ with c_eff = {self.effective_speed_limit:.4f}"
        elif self.dispersion_type == 'galilean':
            return f"NON-RELATIVISTIC (Galilean): E = p²/2m with m = {self.rest_mass:.2f}"
        elif self.dispersion_type == 'medium_limited':
            return f"MEDIUM-LIMITED: Velocity saturates at v_max = {self.effective_speed_limit:.4f}"
        elif self.dispersion_type == 'anomalous':
            return f"ANOMALOUS DISPERSION: Non-standard E(p) relation"
        else:
            return "INCONCLUSIVE: Could not determine dispersion type"


# =============================================================================
# Dispersion Model Functions
# =============================================================================

def relativistic_dispersion(p, m, c):
    """E² = p²c² + m²c⁴ → E = √(p²c² + m²c⁴)"""
    return np.sqrt(p**2 * c**2 + m**2 * c**4)

def galilean_dispersion(p, m, E0):
    """E = E₀ + p²/(2m)"""
    return E0 + p**2 / (2 * m)

def medium_limited_dispersion(p, m, v_max, E0):
    """
    E = E₀ + m*v_max² * (√(1 + (p/(m*v_max))²) - 1)
    This gives v → v_max as p → ∞
    """
    x = p / (m * v_max + 1e-10)
    return E0 + m * v_max**2 * (np.sqrt(1 + x**2) - 1)

def polynomial_dispersion(p, a0, a2, a4):
    """E = a₀ + a₂p² + a₄p⁴ (phenomenological)"""
    return a0 + a2 * p**2 + a4 * p**4


def velocity_from_dispersion(E, p, dp=0.01):
    """v = dE/dp (group velocity)"""
    # Numerical derivative
    return (E - np.roll(E, 1)) / dp


# =============================================================================
# Measurement Functions
# =============================================================================

def create_moving_excitation(
    engine: QMRTFrequencyEngine,
    position: Tuple[float, float, float],
    momentum: float,
    amplitude: float = 0.3,
    width: float = 2.5
) -> float:
    """
    Create an excitation with specified momentum.
    
    Returns: actual energy added
    """
    p = engine.params
    n = engine.grid_size
    
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    px, py, pz = position
    R_sq = (X - px)**2 + (Y - py)**2 + (Z - pz)**2
    
    # Gaussian profile
    amp = amplitude * p.omega_0
    profile = amp * np.exp(-R_sq / (2 * width**2))
    
    E_before = engine.compute_total_energy()
    engine.omega += profile
    
    # Add momentum (motion along x-axis)
    # p = M * v, and v ~ d(omega)/dt ~ pi_omega / M
    # So pi_omega ~ momentum * profile_shape
    grad_x = -profile * (X - px) / (width**2)
    engine.pi_omega += momentum * grad_x
    
    E_after = engine.compute_total_energy()
    
    return E_after - E_before


def measure_excitation_velocity(
    engine: QMRTFrequencyEngine,
    dt: float = 0.02,
    measurement_time: float = 5.0,
    threshold_fraction: float = 0.1
) -> Tuple[float, List[Tuple[float, float]]]:
    """
    Measure velocity of excitation by tracking center of mass.
    
    Returns: (average_velocity, trajectory[(t, x)])
    """
    p = engine.params
    n = engine.grid_size
    
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    steps = int(measurement_time / dt)
    trajectory = []
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % 5 == 0:
            # Find excitation center
            excess = np.abs(engine.omega - np.sign(engine.omega) * p.omega_0)
            threshold = threshold_fraction * p.omega_0
            mask = excess > threshold
            
            if np.sum(mask) > 10:
                total_weight = np.sum(excess[mask])
                com_x = np.sum(X[mask] * excess[mask]) / total_weight
                trajectory.append((engine.time, float(com_x)))
    
    # Fit velocity from trajectory
    if len(trajectory) > 5:
        times = np.array([t for t, x in trajectory])
        positions = np.array([x for t, x in trajectory])
        
        # Linear fit: x = x0 + v*t
        slope, intercept, r, p_val, std_err = linregress(times, positions)
        velocity = slope
    else:
        velocity = 0.0
    
    return velocity, trajectory


def measure_excitation_energy(
    engine: QMRTFrequencyEngine,
    center: Tuple[float, float, float],
    radius: float = 6.0
) -> float:
    """
    Measure energy localized around excitation.
    """
    p = engine.params
    n = engine.grid_size
    
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    cx, cy, cz = center
    R_sq = (X - cx)**2 + (Y - cy)**2 + (Z - cz)**2
    mask = R_sq < radius**2
    
    # Local energy density
    KE = 0.5 * engine.pi_omega**2 / p.M_omega
    PE = p.a_omega * (engine.omega**2 - p.omega_0**2)**2
    grad_sq = (np.gradient(engine.omega, axis=0)**2 + 
               np.gradient(engine.omega, axis=1)**2 + 
               np.gradient(engine.omega, axis=2)**2)
    GE = 0.5 * p.K_omega * grad_sq
    
    E_local = float(np.sum((KE + PE + GE)[mask]) * engine.dx**3)
    
    return E_local


# =============================================================================
# Main Dispersion Relation Test
# =============================================================================

def extract_dispersion_relation(
    grid_size: int = 28,
    momenta: Optional[List[float]] = None,
    measurement_time: float = 8.0,
    dt: float = 0.02,
    seed: int = 42
) -> DispersionResult:
    """
    THE DECISIVE TEST: Extract E(p) dispersion relation.
    
    Args:
        grid_size: Simulation grid
        momenta: List of initial momenta to test
        measurement_time: Time to measure each velocity
        dt: Timestep
        seed: Random seed
    """
    print("\n" + "="*70)
    print("DECISIVE TEST: DISPERSION RELATION EXTRACTION")
    print("="*70)
    print("Measuring E(p) for moving excitations")
    print("="*70)
    
    if momenta is None:
        # Range of momenta from rest to high
        momenta = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
    
    result = DispersionResult()
    
    # First measure rest energy/mass
    print("\n[1] Measuring rest state...")
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    for _ in range(100):
        engine.evolve_timestep(dt)
    
    E_background = engine.compute_total_energy()
    
    # Create stationary excitation
    center = grid_size // 2
    E_added = create_moving_excitation(
        engine, 
        (center, center, center),
        momentum=0.0,
        amplitude=0.3,
        width=2.5
    )
    
    # Let it settle
    for _ in range(100):
        engine.evolve_timestep(dt)
    
    # Measure rest energy
    E_rest = measure_excitation_energy(engine, (center, center, center))
    result.rest_energy = E_rest
    
    print(f"  Rest energy E₀ = {E_rest:.4f}")
    
    # Measure at different momenta
    print("\n[2] Measuring dispersion points...")
    print(f"{'p_init':>10} | {'v':>10} | {'E':>12} | {'E_kin':>12}")
    print("-"*50)
    
    for p_init in momenta:
        # Fresh engine for each measurement
        engine = QMRTFrequencyEngine(grid_size=grid_size)
        engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
        
        for _ in range(50):
            engine.evolve_timestep(dt)
        
        # Create excitation with momentum
        start_x = grid_size // 4  # Start away from center to have room to move
        E_added = create_moving_excitation(
            engine,
            (start_x, center, center),
            momentum=p_init,
            amplitude=0.3,
            width=2.5
        )
        
        # Measure velocity
        v, trajectory = measure_excitation_velocity(
            engine, dt=dt, measurement_time=measurement_time
        )
        
        # Measure energy (at final position)
        if trajectory:
            final_x = trajectory[-1][1]
        else:
            final_x = start_x
        
        E_measured = measure_excitation_energy(engine, (final_x, center, center))
        E_kinetic = E_measured - E_rest
        
        # Effective momentum (for fitting)
        # If we knew m_rest, p_eff = m_rest * v
        # For now, use p_init as proxy
        p_eff = p_init
        
        point = DispersionPoint(
            initial_momentum=p_init,
            measured_velocity=v,
            measured_energy=E_measured,
            kinetic_energy=E_kinetic,
            effective_momentum=p_eff
        )
        result.points.append(point)
        
        print(f"{p_init:>10.2f} | {v:>10.4f} | {E_measured:>12.4f} | {E_kinetic:>12.4f}")
    
    # Fit dispersion relations
    print("\n[3] Fitting dispersion models...")
    
    p_data = np.array([pt.initial_momentum for pt in result.points])
    E_data = np.array([pt.measured_energy for pt in result.points])
    v_data = np.array([pt.measured_velocity for pt in result.points])
    
    # Filter out zero momentum for fits requiring p > 0
    nonzero_mask = p_data > 0.1
    p_nz = p_data[nonzero_mask]
    E_nz = E_data[nonzero_mask]
    v_nz = v_data[nonzero_mask]
    
    fits = {}
    
    # Fit 1: Galilean (non-relativistic)
    try:
        popt, _ = curve_fit(
            galilean_dispersion, p_data, E_data,
            p0=[1000.0, E_rest],
            maxfev=5000
        )
        m_gal, E0_gal = popt
        E_fit = galilean_dispersion(p_data, *popt)
        ss_res = np.sum((E_data - E_fit)**2)
        ss_tot = np.sum((E_data - np.mean(E_data))**2)
        r2 = 1 - ss_res / (ss_tot + 1e-10)
        
        fits['galilean'] = {
            'params': {'m': m_gal, 'E0': E0_gal},
            'r_squared': r2
        }
        print(f"  Galilean: E = {E0_gal:.2f} + p²/(2×{m_gal:.2f})  R² = {r2:.4f}")
    except Exception as e:
        print(f"  Galilean fit failed: {e}")
    
    # Fit 2: Relativistic
    try:
        popt, _ = curve_fit(
            relativistic_dispersion, p_data, E_data,
            p0=[100.0, 1.0],
            bounds=([0.1, 0.01], [1e6, 100]),
            maxfev=5000
        )
        m_rel, c_rel = popt
        E_fit = relativistic_dispersion(p_data, *popt)
        ss_res = np.sum((E_data - E_fit)**2)
        ss_tot = np.sum((E_data - np.mean(E_data))**2)
        r2 = 1 - ss_res / (ss_tot + 1e-10)
        
        fits['relativistic'] = {
            'params': {'m': m_rel, 'c': c_rel},
            'r_squared': r2
        }
        print(f"  Relativistic: E² = p²×{c_rel:.4f}² + {m_rel:.2f}²×{c_rel:.4f}⁴  R² = {r2:.4f}")
    except Exception as e:
        print(f"  Relativistic fit failed: {e}")
    
    # Fit 3: Medium-limited
    try:
        # Estimate v_max from data
        v_max_est = np.max(v_nz) * 1.2 if len(v_nz) > 0 else 1.0
        
        popt, _ = curve_fit(
            medium_limited_dispersion, p_data, E_data,
            p0=[1000.0, v_max_est, E_rest],
            bounds=([1, 0.01, 0], [1e6, 10, 1e6]),
            maxfev=5000
        )
        m_med, v_max, E0_med = popt
        E_fit = medium_limited_dispersion(p_data, *popt)
        ss_res = np.sum((E_data - E_fit)**2)
        ss_tot = np.sum((E_data - np.mean(E_data))**2)
        r2 = 1 - ss_res / (ss_tot + 1e-10)
        
        fits['medium_limited'] = {
            'params': {'m': m_med, 'v_max': v_max, 'E0': E0_med},
            'r_squared': r2
        }
        print(f"  Medium-limited: v_max = {v_max:.4f}, m = {m_med:.2f}  R² = {r2:.4f}")
    except Exception as e:
        print(f"  Medium-limited fit failed: {e}")
    
    # Fit 4: Polynomial (phenomenological)
    try:
        popt, _ = curve_fit(
            polynomial_dispersion, p_data, E_data,
            p0=[E_rest, 0.001, 0.0],
            maxfev=5000
        )
        a0, a2, a4 = popt
        E_fit = polynomial_dispersion(p_data, *popt)
        ss_res = np.sum((E_data - E_fit)**2)
        ss_tot = np.sum((E_data - np.mean(E_data))**2)
        r2 = 1 - ss_res / (ss_tot + 1e-10)
        
        fits['polynomial'] = {
            'params': {'a0': a0, 'a2': a2, 'a4': a4},
            'r_squared': r2
        }
        print(f"  Polynomial: E = {a0:.2f} + {a2:.6f}p² + {a4:.8f}p⁴  R² = {r2:.4f}")
    except Exception as e:
        print(f"  Polynomial fit failed: {e}")
    
    result.fits = fits
    
    # Determine best model
    best_r2 = -1
    best_model = ""
    for name, fit in fits.items():
        if fit['r_squared'] > best_r2:
            best_r2 = fit['r_squared']
            best_model = name
    
    result.best_model = best_model
    result.best_r_squared = best_r2
    if best_model in fits:
        result.best_params = fits[best_model]['params']
    
    # Extract physics
    if best_model == 'relativistic' and best_r2 > 0.9:
        result.dispersion_type = 'relativistic'
        result.effective_speed_limit = fits['relativistic']['params']['c']
        result.rest_mass = fits['relativistic']['params']['m']
    elif best_model == 'galilean' and best_r2 > 0.9:
        result.dispersion_type = 'galilean'
        result.rest_mass = fits['galilean']['params']['m']
    elif best_model == 'medium_limited' and best_r2 > 0.9:
        result.dispersion_type = 'medium_limited'
        result.effective_speed_limit = fits['medium_limited']['params']['v_max']
        result.rest_mass = fits['medium_limited']['params']['m']
    else:
        result.dispersion_type = 'anomalous'
    
    # Check for mass-velocity coupling
    if len(v_nz) > 2 and len(p_nz) > 2:
        # m_eff(v) = p/v
        m_eff = p_nz / (v_nz + 1e-10)
        m_variation = np.std(m_eff) / (np.mean(m_eff) + 1e-10)
        result.mass_velocity_coupling = m_variation > 0.1
    
    # Summary
    print("\n" + "="*70)
    print("DISPERSION RELATION RESULT")
    print("="*70)
    print(f"\n  Best model: {best_model.upper()}")
    print(f"  R² = {best_r2:.4f}")
    print(f"  Parameters: {result.best_params}")
    print(f"\n  Dispersion type: {result.dispersion_type.upper()}")
    print(f"  Effective speed limit: {result.effective_speed_limit:.4f}")
    print(f"  Rest mass: {result.rest_mass:.2f}")
    print(f"  Mass-velocity coupling: {result.mass_velocity_coupling}")
    print(f"\n  VERDICT: {result._get_verdict()}")
    print("="*70 + "\n")
    
    return result


def run_velocity_saturation_test(
    grid_size: int = 28,
    max_momentum: float = 50.0,
    n_points: int = 10,
    seed: int = 42
) -> Dict:
    """
    Test specifically for velocity saturation (v → v_max as p → ∞).
    """
    print("\n" + "="*60)
    print("VELOCITY SATURATION TEST")
    print("="*60)
    
    momenta = np.linspace(0, max_momentum, n_points)
    velocities = []
    
    for p_init in momenta:
        engine = QMRTFrequencyEngine(grid_size=grid_size)
        engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
        p = engine.params
        
        for _ in range(50):
            engine.evolve_timestep(0.02)
        
        center = grid_size // 2
        start_x = grid_size // 4
        
        create_moving_excitation(
            engine, (start_x, center, center),
            momentum=p_init, amplitude=0.3, width=2.5
        )
        
        v, _ = measure_excitation_velocity(engine, dt=0.02, measurement_time=5.0)
        velocities.append(v)
        
        print(f"  p = {p_init:6.2f}: v = {v:.4f}")
    
    # Check for saturation
    v_arr = np.array(velocities)
    p_arr = np.array(momenta)
    
    # If saturating, v should plateau
    if len(v_arr) > 3:
        v_high = np.mean(v_arr[-3:])
        v_low = np.mean(v_arr[1:4])  # Skip p=0
        
        saturation_ratio = v_high / (v_low + 1e-10)
        saturates = saturation_ratio < 1.5  # v doesn't grow much at high p
    else:
        saturates = False
        saturation_ratio = 0
    
    print(f"\n  High-p velocity: {v_arr[-1]:.4f}")
    print(f"  Low-p velocity: {v_arr[1]:.4f}" if len(v_arr) > 1 else "")
    print(f"  Saturation: {'✅ YES' if saturates else '❌ NO'}")
    
    return {
        'momenta': momenta.tolist(),
        'velocities': velocities,
        'saturates': saturates,
        'saturation_ratio': saturation_ratio
    }


if __name__ == "__main__":
    # Run the decisive dispersion test
    result = extract_dispersion_relation(
        grid_size=24,
        momenta=[0.0, 1.0, 2.0, 4.0, 8.0, 16.0],
        measurement_time=6.0,
        seed=42
    )
    
    print("\nDispersion type:", result.dispersion_type)
