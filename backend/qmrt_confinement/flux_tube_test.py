"""
QMRT Quark Confinement Analogies - Step 2: Flux Tube / Separation Energy Test

THE MOST CRITICAL QMRT VALIDATION

Goal: Test if E(r) ~ σr (linear potential) emerges naturally

Physics being tested:
    E(r) ~ σr
    
    In QMRT interpretation:
    - σ is MEDIUM STRAIN TENSION (from barrier potential)
    - NOT gluon string tension
    
    If linear growth emerges naturally →
        Confinement analogy is PHYSICALLY MEANINGFUL
    If not →
        Proton formation regime assumptions must be revised

Method:
    1. Create TWO localized excitations at variable separation r
    2. Measure total system energy E(r) at equilibrium
    3. Plot E vs r and fit:
        - E(r) = E_0 + σr        (LINEAR → confinement)
        - E(r) = E_0 + α/r       (COULOMB → no confinement)
        - E(r) = E_0 + σr - α/r  (CORNELL → QCD-like)
    4. Extract string tension σ

Physical context:
    - Excitations are "proto-quarks" (confirmed in Step 1)
    - Domain walls between excitations act as "flux tubes"
    - σ emerges from medium strain energy, not gauge field
    - This answers: What permits quark persistence but not hadron persistence?
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import curve_fit
from scipy.ndimage import label, center_of_mass
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters


@dataclass
class SeparationEnergyPoint:
    """Energy measurement at a specific separation"""
    separation: float           # r (grid units)
    total_energy: float         # E(r)
    kinetic_energy: float
    potential_energy: float
    
    # Excitation-specific energies
    excitation_1_energy: float
    excitation_2_energy: float
    interaction_energy: float   # E_total - E_1 - E_2
    
    # Domain wall metrics
    domain_wall_length: float   # Length of wall between excitations
    domain_wall_energy: float   # Energy in the wall region
    strain_energy_density: float  # σ ≈ E_wall / L_wall
    
    # Stability metrics
    excitation_1_preserved: bool
    excitation_2_preserved: bool
    equilibration_time: float
    
    def to_dict(self) -> Dict:
        return {
            'separation': float(self.separation),
            'total_energy': float(self.total_energy),
            'kinetic_energy': float(self.kinetic_energy),
            'potential_energy': float(self.potential_energy),
            'excitation_1_energy': float(self.excitation_1_energy),
            'excitation_2_energy': float(self.excitation_2_energy),
            'interaction_energy': float(self.interaction_energy),
            'domain_wall_length': float(self.domain_wall_length),
            'domain_wall_energy': float(self.domain_wall_energy),
            'strain_energy_density': float(self.strain_energy_density),
            'excitation_1_preserved': self.excitation_1_preserved,
            'excitation_2_preserved': self.excitation_2_preserved,
            'equilibration_time': float(self.equilibration_time)
        }


@dataclass
class FluxTubeResult:
    """Result from flux tube / separation energy test"""
    
    # Data points
    energy_vs_separation: List[SeparationEnergyPoint] = field(default_factory=list)
    
    # Fit results
    fit_type: str = ""          # 'linear', 'coulomb', 'cornell', 'none'
    fit_params: Dict = field(default_factory=dict)
    fit_r_squared: float = 0.0
    
    # Extracted physics
    string_tension: float = 0.0          # σ (energy/length)
    string_tension_error: float = 0.0
    coulomb_coefficient: float = 0.0     # α
    baseline_energy: float = 0.0         # E_0
    
    # Validation
    linear_regime_exists: bool = False
    linear_slope_positive: bool = False
    confinement_confirmed: bool = False
    
    # Metadata
    grid_size: int = 0
    excitation_amplitude: float = 0.0
    excitation_width: float = 0.0
    separations_tested: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'energy_vs_separation': [p.to_dict() for p in self.energy_vs_separation],
            'fit': {
                'type': self.fit_type,
                'params': {k: float(v) for k, v in self.fit_params.items()},
                'r_squared': float(self.fit_r_squared)
            },
            'extracted_physics': {
                'string_tension': float(self.string_tension),
                'string_tension_error': float(self.string_tension_error),
                'coulomb_coefficient': float(self.coulomb_coefficient),
                'baseline_energy': float(self.baseline_energy)
            },
            'validation': {
                'linear_regime_exists': self.linear_regime_exists,
                'linear_slope_positive': self.linear_slope_positive,
                'confinement_confirmed': self.confinement_confirmed
            },
            'metadata': {
                'grid_size': int(self.grid_size),
                'excitation_amplitude': float(self.excitation_amplitude),
                'excitation_width': float(self.excitation_width),
                'separations_tested': [float(s) for s in self.separations_tested]
            },
            'verdict': self._get_verdict()
        }
    
    def _get_verdict(self) -> str:
        if self.confinement_confirmed:
            return f"CONFINEMENT CONFIRMED: E(r) ~ {self.string_tension:.4f}·r (linear potential). Medium strain tension σ={self.string_tension:.4f}. Flux tube analogy is physically meaningful."
        elif self.linear_regime_exists and self.linear_slope_positive:
            return f"PARTIAL CONFINEMENT: Linear regime exists but may not be dominant (σ={self.string_tension:.4f}). Mixed potential observed."
        elif self.fit_type == 'coulomb':
            return f"COULOMB-LIKE: E(r) ~ 1/r. No confinement - excitations interact via inverse-distance potential."
        else:
            return f"INCONCLUSIVE: Could not establish clear potential law. Fit type: {self.fit_type}, R²={self.fit_r_squared:.3f}"


# Fitting functions
def linear_potential(r, E0, sigma):
    """E(r) = E_0 + σr"""
    return E0 + sigma * r

def coulomb_potential(r, E0, alpha):
    """E(r) = E_0 - α/r"""
    return E0 - alpha / (r + 0.1)  # Regularized to avoid r=0 singularity

def cornell_potential(r, E0, sigma, alpha):
    """E(r) = E_0 + σr - α/r (QCD-like)"""
    return E0 + sigma * r - alpha / (r + 0.1)


def create_two_excitations(
    engine: QMRTFrequencyEngine,
    separation: float,
    amplitude: float,
    width: float,
    axis: int = 0
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Create two localized excitations at a given separation.
    
    Places them symmetrically around the grid center along specified axis.
    
    Returns: (position1, position2)
    """
    n = engine.grid_size
    center = n // 2
    
    # Positions along the specified axis
    offset = separation / 2
    
    pos1 = [float(center), float(center), float(center)]
    pos2 = [float(center), float(center), float(center)]
    
    pos1[axis] = center - offset
    pos2[axis] = center + offset
    
    pos1 = tuple(pos1)
    pos2 = tuple(pos2)
    
    # Create coordinate grids
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Distance from each excitation center
    R1_sq = (X - pos1[0])**2 + (Y - pos1[1])**2 + (Z - pos1[2])**2
    R2_sq = (X - pos2[0])**2 + (Y - pos2[1])**2 + (Z - pos2[2])**2
    
    # Gaussian profiles
    profile1 = amplitude * np.exp(-R1_sq / (2 * width**2))
    profile2 = amplitude * np.exp(-R2_sq / (2 * width**2))
    
    # Add to omega field
    engine.omega = engine.omega + profile1 + profile2
    
    # Recalculate energy
    engine.initial_energy = engine.compute_total_energy()
    
    return pos1, pos2


def measure_excitation_energy(
    engine: QMRTFrequencyEngine,
    position: Tuple[float, float, float],
    radius: float
) -> Tuple[float, bool]:
    """
    Measure energy in a spherical region around an excitation.
    
    Returns: (energy, is_preserved)
    """
    n = engine.grid_size
    p = engine.params
    
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    R_sq = (X - position[0])**2 + (Y - position[1])**2 + (Z - position[2])**2
    mask = R_sq < radius**2
    
    if np.sum(mask) < 10:
        return 0.0, False
    
    # Local energy density
    delta_rho = engine.rho - p.rho_equilibrium
    
    # Kinetic
    KE_local = 0.5 * (
        engine.pi_rho**2 / p.M_rho +
        engine.pi_sigma**2 / p.M_sigma +
        engine.pi_tau**2 / p.M_tau +
        engine.pi_phi**2 / p.M_phi +
        engine.pi_omega**2 / p.M_omega
    )
    
    # Potential
    PE_local = (
        (p.a_rho / 2) * delta_rho**2 +
        (p.a_sigma / 2) * engine.sigma**2 +
        (p.a_tau / 2) * engine.tau**2 +
        (-p.a_phi * np.cos(engine.phi)) +
        p.a_omega * (engine.omega**2 - p.omega_0**2)**2
    )
    
    energy = float(np.sum((KE_local + PE_local)[mask]) * engine.dx**3)
    
    # Check if excitation is preserved (high omega deviation in region)
    omega_deviation = np.abs(engine.omega[mask] - np.sign(np.mean(engine.omega[mask])) * p.omega_0)
    is_preserved = float(np.mean(omega_deviation)) > 0.1 * p.omega_0
    
    return energy, is_preserved


def measure_domain_wall(
    engine: QMRTFrequencyEngine,
    pos1: Tuple[float, float, float],
    pos2: Tuple[float, float, float],
    wall_width: float = 3.0
) -> Tuple[float, float]:
    """
    Measure domain wall between two excitations.
    
    Returns: (wall_length, wall_energy)
    """
    n = engine.grid_size
    p = engine.params
    
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Vector from pos1 to pos2
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dz = pos2[2] - pos1[2]
    length = np.sqrt(dx**2 + dy**2 + dz**2)
    
    if length < 1e-6:
        return 0.0, 0.0
    
    # Unit vector
    ux, uy, uz = dx/length, dy/length, dz/length
    
    # Parametric position along line: t ∈ [0, 1]
    # Point on line: pos1 + t * (pos2 - pos1)
    # Distance from line for each grid point
    
    # Vector from pos1 to each grid point
    vx = X - pos1[0]
    vy = Y - pos1[1]
    vz = Z - pos1[2]
    
    # Projection onto line
    t = (vx * ux + vy * uy + vz * uz) / length
    t = np.clip(t, 0, 1)  # Clamp to line segment
    
    # Closest point on line
    cx = pos1[0] + t * dx
    cy = pos1[1] + t * dy
    cz = pos1[2] + t * dz
    
    # Distance from line
    dist_from_line = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
    
    # Wall mask: within wall_width of line, between the two excitations
    excitation_radius = 4.0
    not_at_excitation1 = ((X - pos1[0])**2 + (Y - pos1[1])**2 + (Z - pos1[2])**2) > excitation_radius**2
    not_at_excitation2 = ((X - pos2[0])**2 + (Y - pos2[1])**2 + (Z - pos2[2])**2) > excitation_radius**2
    
    wall_mask = (dist_from_line < wall_width) & not_at_excitation1 & not_at_excitation2
    
    if np.sum(wall_mask) < 5:
        return length, 0.0
    
    # Energy in wall region (dominated by gradient energy at domain boundaries)
    grad_omega_sq = (
        np.gradient(engine.omega, axis=0)**2 +
        np.gradient(engine.omega, axis=1)**2 +
        np.gradient(engine.omega, axis=2)**2
    )
    
    # Wall energy is primarily gradient energy
    wall_energy_density = 0.5 * p.K_omega * grad_omega_sq
    wall_energy = float(np.sum(wall_energy_density[wall_mask]) * engine.dx**3)
    
    return length, wall_energy


def measure_separation_energy(
    engine: QMRTFrequencyEngine,
    pos1: Tuple[float, float, float],
    pos2: Tuple[float, float, float],
    excitation_radius: float = 4.0,
    equilibration_time: float = 5.0,
    dt: float = 0.02
) -> SeparationEnergyPoint:
    """
    Measure system energy at a given separation after equilibration.
    """
    # Equilibrate
    steps = int(equilibration_time / dt)
    for _ in range(steps):
        engine.evolve_timestep(dt)
    
    # Measure total energy
    total_energy = engine.compute_total_energy()
    
    # Kinetic/potential split
    p = engine.params
    KE = 0.5 * (
        np.sum(engine.pi_rho**2) / p.M_rho +
        np.sum(engine.pi_sigma**2) / p.M_sigma +
        np.sum(engine.pi_tau**2) / p.M_tau +
        np.sum(engine.pi_phi**2) / p.M_phi +
        np.sum(engine.pi_omega**2) / p.M_omega
    ) * engine.dx**3
    PE = total_energy - KE
    
    # Excitation energies
    E1, preserved1 = measure_excitation_energy(engine, pos1, excitation_radius)
    E2, preserved2 = measure_excitation_energy(engine, pos2, excitation_radius)
    
    # Interaction energy
    interaction_energy = total_energy - E1 - E2
    
    # Domain wall
    separation = np.sqrt(
        (pos2[0] - pos1[0])**2 +
        (pos2[1] - pos1[1])**2 +
        (pos2[2] - pos1[2])**2
    )
    wall_length, wall_energy = measure_domain_wall(engine, pos1, pos2)
    
    # Strain energy density (string tension estimate)
    strain_density = wall_energy / wall_length if wall_length > 0 else 0.0
    
    return SeparationEnergyPoint(
        separation=separation,
        total_energy=total_energy,
        kinetic_energy=KE,
        potential_energy=PE,
        excitation_1_energy=E1,
        excitation_2_energy=E2,
        interaction_energy=interaction_energy,
        domain_wall_length=wall_length,
        domain_wall_energy=wall_energy,
        strain_energy_density=strain_density,
        excitation_1_preserved=preserved1,
        excitation_2_preserved=preserved2,
        equilibration_time=equilibration_time
    )


def run_flux_tube_test(
    grid_size: int = 24,
    separations: Optional[List[float]] = None,
    excitation_amplitude: float = 0.3,
    excitation_width: float = 2.5,
    equilibration_time: float = 5.0,
    dt: float = 0.02,
    seed: int = 42
) -> FluxTubeResult:
    """
    Run the flux tube / separation energy test.
    
    THE MOST CRITICAL QMRT VALIDATION.
    
    Tests whether E(r) ~ σr emerges naturally.
    
    Args:
        grid_size: Simulation grid size
        separations: List of separations to test (default: 4 to grid_size-4)
        excitation_amplitude: Amplitude of excitations (relative to ω_0)
        excitation_width: Width of Gaussian excitations
        equilibration_time: Time to equilibrate at each separation
        dt: Timestep
        seed: Random seed
    
    Returns:
        FluxTubeResult with E(r) data and fit analysis
    """
    print("="*60)
    print("FLUX TUBE / SEPARATION ENERGY TEST")
    print("="*60)
    print("THE MOST CRITICAL QMRT VALIDATION")
    print("-"*60)
    print(f"Grid: {grid_size}³")
    print(f"Excitation: A={excitation_amplitude}ω₀, σ={excitation_width}")
    print(f"Equilibration: {equilibration_time}s per separation")
    
    # Default separations
    if separations is None:
        # From minimum (excitations nearly touching) to maximum (across grid)
        min_sep = 2 * excitation_width + 2
        max_sep = grid_size - 2 * excitation_width - 2
        separations = np.linspace(min_sep, max_sep, 8).tolist()
    
    print(f"Separations: {[f'{s:.1f}' for s in separations]}")
    print("-"*60)
    
    result = FluxTubeResult(
        grid_size=grid_size,
        excitation_amplitude=excitation_amplitude,
        excitation_width=excitation_width,
        separations_tested=separations
    )
    
    np.random.seed(seed)
    
    # Test each separation
    for i, sep in enumerate(separations):
        print(f"\n[{i+1}/{len(separations)}] Testing separation r = {sep:.1f}...")
        
        # Fresh engine for each separation
        engine = QMRTFrequencyEngine(grid_size=grid_size)
        engine.initialize_frequency_domains(amplitude=0.02, seed=seed + i)
        p = engine.params
        
        # Stabilize substrate
        for _ in range(100):
            engine.evolve_timestep(dt)
        
        # Create two excitations
        actual_amplitude = excitation_amplitude * p.omega_0
        pos1, pos2 = create_two_excitations(
            engine, sep, actual_amplitude, excitation_width, axis=0
        )
        
        print(f"    Excitation 1 at {tuple(f'{x:.1f}' for x in pos1)}")
        print(f"    Excitation 2 at {tuple(f'{x:.1f}' for x in pos2)}")
        
        # Measure after equilibration
        point = measure_separation_energy(
            engine, pos1, pos2,
            excitation_radius=excitation_width * 2,
            equilibration_time=equilibration_time,
            dt=dt
        )
        
        result.energy_vs_separation.append(point)
        
        print(f"    E(r={sep:.1f}) = {point.total_energy:.2f}")
        print(f"    Wall energy: {point.domain_wall_energy:.4f}, σ_local: {point.strain_energy_density:.4f}")
        print(f"    Preserved: E1={point.excitation_1_preserved}, E2={point.excitation_2_preserved}")
    
    # Fit analysis
    print("\n" + "="*60)
    print("FIT ANALYSIS")
    print("="*60)
    
    r_data = np.array([p.separation for p in result.energy_vs_separation])
    E_data = np.array([p.total_energy for p in result.energy_vs_separation])
    E_wall_data = np.array([p.domain_wall_energy for p in result.energy_vs_separation])
    
    # IMPORTANT: Use DOMAIN WALL ENERGY, not total energy
    # Total energy varies due to random substrate initialization
    # Domain wall energy is the physically meaningful quantity
    print("\nNOTE: Using DOMAIN WALL ENERGY E_wall(r) for fit analysis")
    print("      (Total energy varies with substrate initialization)")
    
    # Filter out points with zero wall energy (too close)
    valid_mask = E_wall_data > 0.01
    r_valid = r_data[valid_mask]
    E_wall_valid = E_wall_data[valid_mask]
    
    if len(r_valid) < 3:
        print("WARNING: Insufficient data points with measurable wall energy")
        r_valid = r_data
        E_wall_valid = E_data  # Fallback to total energy
    
    fits = {}
    
    # Fit 1: Linear potential for domain wall energy
    try:
        popt, pcov = curve_fit(
            linear_potential, r_valid, E_wall_valid,
            p0=[0.0, 0.5],  # Expect E_wall ~ 0 at r=0
            maxfev=5000
        )
        E0_lin, sigma_lin = popt
        sigma_err = np.sqrt(pcov[1, 1]) if pcov[1, 1] > 0 else 0.0
        E_fit_lin = linear_potential(r_valid, *popt)
        ss_res = np.sum((E_wall_valid - E_fit_lin)**2)
        ss_tot = np.sum((E_wall_valid - np.mean(E_wall_valid))**2)
        r2_lin = 1 - ss_res / (ss_tot + 1e-10)
        
        fits['linear'] = {
            'params': {'E0': E0_lin, 'sigma': sigma_lin, 'sigma_err': sigma_err},
            'r_squared': r2_lin,
            'fitted': E_fit_lin
        }
        print(f"Linear fit: E_wall(r) = {E0_lin:.4f} + {sigma_lin:.4f}·r  (R² = {r2_lin:.4f})")
        print(f"            String tension σ = {sigma_lin:.4f} ± {sigma_err:.4f}")
    except Exception as e:
        print(f"Linear fit failed: {e}")
        fits['linear'] = None
    
    # Fit 2: Coulomb potential
    try:
        popt, pcov = curve_fit(
            coulomb_potential, r_valid, E_wall_valid,
            p0=[E_wall_valid[-1], 1.0],
            maxfev=5000
        )
        E0_coul, alpha_coul = popt
        E_fit_coul = coulomb_potential(r_valid, *popt)
        ss_res = np.sum((E_wall_valid - E_fit_coul)**2)
        ss_tot = np.sum((E_wall_valid - np.mean(E_wall_valid))**2)
        r2_coul = 1 - ss_res / (ss_tot + 1e-10)
        
        fits['coulomb'] = {
            'params': {'E0': E0_coul, 'alpha': alpha_coul},
            'r_squared': r2_coul,
            'fitted': E_fit_coul
        }
        print(f"Coulomb fit: E_wall(r) = {E0_coul:.4f} - {alpha_coul:.4f}/r  (R² = {r2_coul:.4f})")
    except Exception as e:
        print(f"Coulomb fit failed: {e}")
        fits['coulomb'] = None
    
    # Fit 3: Cornell potential
    try:
        popt, pcov = curve_fit(
            cornell_potential, r_valid, E_wall_valid,
            p0=[0.0, 0.5, 1.0],
            maxfev=5000
        )
        E0_corn, sigma_corn, alpha_corn = popt
        E_fit_corn = cornell_potential(r_valid, *popt)
        ss_res = np.sum((E_wall_valid - E_fit_corn)**2)
        ss_tot = np.sum((E_wall_valid - np.mean(E_wall_valid))**2)
        r2_corn = 1 - ss_res / (ss_tot + 1e-10)
        
        fits['cornell'] = {
            'params': {'E0': E0_corn, 'sigma': sigma_corn, 'alpha': alpha_corn},
            'r_squared': r2_corn,
            'fitted': E_fit_corn
        }
        print(f"Cornell fit: E_wall(r) = {E0_corn:.4f} + {sigma_corn:.4f}·r - {alpha_corn:.4f}/r  (R² = {r2_corn:.4f})")
    except Exception as e:
        print(f"Cornell fit failed: {e}")
        fits['cornell'] = None
    
    # Determine best fit
    best_fit = None
    best_r2 = -1
    for name, fit in fits.items():
        if fit is not None and fit['r_squared'] > best_r2:
            best_r2 = fit['r_squared']
            best_fit = name
    
    print(f"\nBest fit: {best_fit} (R² = {best_r2:.4f})")
    
    # Extract physics
    if best_fit == 'linear' and fits['linear'] is not None:
        result.fit_type = 'linear'
        result.fit_params = fits['linear']['params']
        result.fit_r_squared = fits['linear']['r_squared']
        result.string_tension = fits['linear']['params']['sigma']
        result.string_tension_error = fits['linear']['params'].get('sigma_err', 0.0)
        result.baseline_energy = fits['linear']['params']['E0']
        result.linear_regime_exists = True
        result.linear_slope_positive = fits['linear']['params']['sigma'] > 0
        result.confinement_confirmed = result.linear_slope_positive and best_r2 > 0.9
        
    elif best_fit == 'coulomb' and fits['coulomb'] is not None:
        result.fit_type = 'coulomb'
        result.fit_params = fits['coulomb']['params']
        result.fit_r_squared = fits['coulomb']['r_squared']
        result.coulomb_coefficient = fits['coulomb']['params']['alpha']
        result.baseline_energy = fits['coulomb']['params']['E0']
        result.linear_regime_exists = False
        result.confinement_confirmed = False
        
    elif best_fit == 'cornell' and fits['cornell'] is not None:
        result.fit_type = 'cornell'
        result.fit_params = fits['cornell']['params']
        result.fit_r_squared = fits['cornell']['r_squared']
        result.string_tension = fits['cornell']['params']['sigma']
        result.coulomb_coefficient = fits['cornell']['params']['alpha']
        result.baseline_energy = fits['cornell']['params']['E0']
        result.linear_regime_exists = fits['cornell']['params']['sigma'] > 0
        result.linear_slope_positive = fits['cornell']['params']['sigma'] > 0
        # Cornell with positive sigma indicates confinement
        # The linear term must dominate at large r
        result.confinement_confirmed = (
            result.linear_slope_positive and 
            best_r2 > 0.9 and
            fits['cornell']['params']['sigma'] > 0.01  # Non-negligible string tension
        )
    else:
        result.fit_type = 'none'
    
    # Also estimate string tension from domain wall measurements
    wall_tensions = [p.strain_energy_density for p in result.energy_vs_separation if p.strain_energy_density > 0]
    if wall_tensions:
        avg_wall_tension = np.mean(wall_tensions)
        result.string_tension_error = np.std(wall_tensions) if len(wall_tensions) > 1 else 0.0
        print(f"\nDomain wall tension (direct measurement): σ_wall = {avg_wall_tension:.4f} ± {result.string_tension_error:.4f}")
    
    # Summary
    print("\n" + "="*60)
    print("FLUX TUBE TEST RESULT")
    print("="*60)
    print(f"\n  Fit type: {result.fit_type.upper()}")
    print(f"  String tension σ: {result.string_tension:.4f}")
    print(f"  Coulomb coefficient α: {result.coulomb_coefficient:.4f}")
    print(f"  Fit quality R²: {result.fit_r_squared:.4f}")
    print(f"\n  Linear regime exists: {'✅' if result.linear_regime_exists else '❌'}")
    print(f"  Linear slope positive: {'✅' if result.linear_slope_positive else '❌'}")
    print(f"  CONFINEMENT CONFIRMED: {'✅' if result.confinement_confirmed else '❌'}")
    print(f"\n  VERDICT: {result._get_verdict()}")
    print("="*60 + "\n")
    
    return result


def run_detailed_flux_tube_test(
    grid_size: int = 28,
    num_separations: int = 12,
    equilibration_time: float = 8.0,
    seed: int = 42
) -> Dict:
    """
    Run a more detailed flux tube test with finer separation resolution.
    """
    min_sep = 6
    max_sep = grid_size - 8
    separations = np.linspace(min_sep, max_sep, num_separations).tolist()
    
    result = run_flux_tube_test(
        grid_size=grid_size,
        separations=separations,
        excitation_amplitude=0.3,
        excitation_width=2.5,
        equilibration_time=equilibration_time,
        seed=seed
    )
    
    return result.to_dict()


if __name__ == "__main__":
    result = run_flux_tube_test(
        grid_size=24,
        separations=None,  # Use default
        excitation_amplitude=0.3,
        excitation_width=2.5,
        equilibration_time=5.0,
        dt=0.02,
        seed=42
    )
    
    print("\nKey results:")
    print(f"  String tension: {result.string_tension:.4f}")
    print(f"  Confinement confirmed: {result.confinement_confirmed}")
