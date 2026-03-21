"""
QMRT Flux Tube Robustness Verification

Systematic validation of E(r) ~ σr finding:

1. Grid resolution independence
2. Timestep convergence  
3. Boundary condition sensitivity
4. Energy conservation diagnostics
5. Scaling robustness

Only after passing these checks can we interpret the physics.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import curve_fit
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters
from qmrt_confinement.flux_tube_test import (
    create_two_excitations,
    measure_separation_energy,
    linear_potential,
    SeparationEnergyPoint
)


@dataclass
class RobustnessResult:
    """Result from robustness verification"""
    test_name: str
    parameter_values: List[float]
    string_tensions: List[float]
    r_squared_values: List[float]
    energy_drifts: List[float]
    
    # Convergence metrics
    tension_mean: float = 0.0
    tension_std: float = 0.0
    tension_cv: float = 0.0  # Coefficient of variation
    converged: bool = False
    convergence_threshold: float = 0.1  # 10% variation acceptable
    
    def to_dict(self) -> Dict:
        return {
            'test_name': self.test_name,
            'parameter_values': [float(v) for v in self.parameter_values],
            'string_tensions': [float(s) for s in self.string_tensions],
            'r_squared_values': [float(r) for r in self.r_squared_values],
            'energy_drifts': [float(e) for e in self.energy_drifts],
            'convergence': {
                'tension_mean': float(self.tension_mean),
                'tension_std': float(self.tension_std),
                'tension_cv': float(self.tension_cv),
                'converged': self.converged,
                'threshold': float(self.convergence_threshold)
            }
        }


def fit_wall_energy(separations: List[float], wall_energies: List[float]) -> Tuple[float, float, float]:
    """
    Fit E_wall(r) = E0 + σr and return (sigma, E0, r_squared)
    """
    r_data = np.array(separations)
    E_data = np.array(wall_energies)
    
    # Filter valid data
    valid = E_data > 0.01
    if np.sum(valid) < 3:
        return 0.0, 0.0, 0.0
    
    r_valid = r_data[valid]
    E_valid = E_data[valid]
    
    try:
        popt, _ = curve_fit(linear_potential, r_valid, E_valid, p0=[0.0, 0.5], maxfev=5000)
        E0, sigma = popt
        E_fit = linear_potential(r_valid, *popt)
        ss_res = np.sum((E_valid - E_fit)**2)
        ss_tot = np.sum((E_valid - np.mean(E_valid))**2)
        r_squared = 1 - ss_res / (ss_tot + 1e-10)
        return sigma, E0, r_squared
    except:
        return 0.0, 0.0, 0.0


def run_single_flux_tube_measurement(
    grid_size: int,
    separations: List[float],
    dt: float,
    equilibration_time: float,
    amplitude: float = 0.3,
    width: float = 2.0,
    seed: int = 42
) -> Tuple[float, float, float, List[float]]:
    """
    Run single flux tube measurement, return (sigma, r_squared, energy_drift, wall_energies)
    """
    wall_energies = []
    energy_drifts = []
    
    for i, sep in enumerate(separations):
        engine = QMRTFrequencyEngine(grid_size=grid_size)
        engine.initialize_frequency_domains(amplitude=0.02, seed=seed + i)
        p = engine.params
        
        # Stabilize
        for _ in range(50):
            engine.evolve_timestep(dt)
        
        initial_energy = engine.compute_total_energy()
        
        # Create excitations
        actual_amplitude = amplitude * p.omega_0
        pos1, pos2 = create_two_excitations(engine, sep, actual_amplitude, width, axis=0)
        
        # Measure
        point = measure_separation_energy(
            engine, pos1, pos2,
            excitation_radius=width * 2,
            equilibration_time=equilibration_time,
            dt=dt
        )
        
        wall_energies.append(point.domain_wall_energy)
        
        # Energy drift
        final_energy = engine.compute_total_energy()
        drift = abs(final_energy - initial_energy) / abs(initial_energy) * 100
        energy_drifts.append(drift)
    
    sigma, E0, r_squared = fit_wall_energy(separations, wall_energies)
    avg_drift = np.mean(energy_drifts)
    
    return sigma, r_squared, avg_drift, wall_energies


# =============================================================================
# TEST 1: Grid Resolution Independence
# =============================================================================

def test_grid_resolution_independence(
    grid_sizes: List[int] = [16, 20, 24, 28],
    seed: int = 42
) -> RobustnessResult:
    """
    Test if string tension σ is independent of grid resolution.
    
    If σ varies significantly with grid size → numerical artifact
    If σ converges → physical result
    """
    print("="*70)
    print("TEST 1: GRID RESOLUTION INDEPENDENCE")
    print("="*70)
    
    string_tensions = []
    r_squared_values = []
    energy_drifts = []
    
    for gs in grid_sizes:
        print(f"\nGrid size: {gs}³")
        
        # Separations scaled to grid
        min_sep = 6
        max_sep = gs - 8
        separations = np.linspace(min_sep, max_sep, 6).tolist()
        
        sigma, r2, drift, _ = run_single_flux_tube_measurement(
            grid_size=gs,
            separations=separations,
            dt=0.02,
            equilibration_time=4.0,
            seed=seed
        )
        
        string_tensions.append(sigma)
        r_squared_values.append(r2)
        energy_drifts.append(drift)
        
        print(f"  σ = {sigma:.4f}, R² = {r2:.4f}, Energy drift = {drift:.4f}%")
    
    # Analyze convergence
    tension_mean = np.mean(string_tensions)
    tension_std = np.std(string_tensions)
    tension_cv = tension_std / (tension_mean + 1e-10)
    
    result = RobustnessResult(
        test_name="grid_resolution_independence",
        parameter_values=grid_sizes,
        string_tensions=string_tensions,
        r_squared_values=r_squared_values,
        energy_drifts=energy_drifts,
        tension_mean=tension_mean,
        tension_std=tension_std,
        tension_cv=tension_cv,
        converged=tension_cv < 0.1
    )
    
    print(f"\n{'='*70}")
    print(f"RESULT: σ = {tension_mean:.4f} ± {tension_std:.4f} (CV = {tension_cv:.2%})")
    print(f"CONVERGED: {'✅ YES' if result.converged else '❌ NO'}")
    print(f"{'='*70}\n")
    
    return result


# =============================================================================
# TEST 2: Timestep Convergence
# =============================================================================

def test_timestep_convergence(
    timesteps: List[float] = [0.04, 0.02, 0.01, 0.005],
    grid_size: int = 20,
    seed: int = 42
) -> RobustnessResult:
    """
    Test if string tension σ converges with decreasing timestep.
    
    Smaller dt should give more accurate result.
    If σ changes significantly → need smaller dt
    """
    print("="*70)
    print("TEST 2: TIMESTEP CONVERGENCE")
    print("="*70)
    
    separations = [6, 8, 10, 12, 14, 16]
    
    string_tensions = []
    r_squared_values = []
    energy_drifts = []
    
    for dt in timesteps:
        print(f"\nTimestep: dt = {dt}")
        
        # Adjust equilibration time to keep same physical time
        equilibration_time = 4.0
        
        sigma, r2, drift, _ = run_single_flux_tube_measurement(
            grid_size=grid_size,
            separations=separations,
            dt=dt,
            equilibration_time=equilibration_time,
            seed=seed
        )
        
        string_tensions.append(sigma)
        r_squared_values.append(r2)
        energy_drifts.append(drift)
        
        print(f"  σ = {sigma:.4f}, R² = {r2:.4f}, Energy drift = {drift:.4f}%")
    
    # Analyze convergence
    tension_mean = np.mean(string_tensions[-2:])  # Use smallest dt values
    tension_std = np.std(string_tensions[-2:])
    tension_cv = tension_std / (tension_mean + 1e-10)
    
    result = RobustnessResult(
        test_name="timestep_convergence",
        parameter_values=timesteps,
        string_tensions=string_tensions,
        r_squared_values=r_squared_values,
        energy_drifts=energy_drifts,
        tension_mean=tension_mean,
        tension_std=tension_std,
        tension_cv=tension_cv,
        converged=tension_cv < 0.1
    )
    
    print(f"\n{'='*70}")
    print(f"RESULT: σ (converged) = {tension_mean:.4f} ± {tension_std:.4f}")
    print(f"CONVERGED: {'✅ YES' if result.converged else '❌ NO'}")
    print(f"{'='*70}\n")
    
    return result


# =============================================================================
# TEST 3: Boundary Condition Sensitivity
# =============================================================================

def test_boundary_sensitivity(
    grid_sizes: List[int] = [20, 24, 28],
    seed: int = 42
) -> RobustnessResult:
    """
    Test boundary condition sensitivity by varying how close excitations get to boundaries.
    
    Uses same physical separations but different grid sizes → different boundary proximity.
    """
    print("="*70)
    print("TEST 3: BOUNDARY CONDITION SENSITIVITY")
    print("="*70)
    
    # Fixed physical separations
    separations = [6, 8, 10, 12]
    
    string_tensions = []
    r_squared_values = []
    energy_drifts = []
    boundary_distances = []  # Min distance from excitation to boundary
    
    for gs in grid_sizes:
        print(f"\nGrid size: {gs}³")
        
        # Calculate min boundary distance
        max_sep = max(separations)
        boundary_dist = (gs - max_sep) / 2
        boundary_distances.append(boundary_dist)
        
        print(f"  Min boundary distance: {boundary_dist:.1f}")
        
        sigma, r2, drift, _ = run_single_flux_tube_measurement(
            grid_size=gs,
            separations=separations,
            dt=0.02,
            equilibration_time=4.0,
            seed=seed
        )
        
        string_tensions.append(sigma)
        r_squared_values.append(r2)
        energy_drifts.append(drift)
        
        print(f"  σ = {sigma:.4f}, R² = {r2:.4f}")
    
    # Analyze
    tension_mean = np.mean(string_tensions)
    tension_std = np.std(string_tensions)
    tension_cv = tension_std / (tension_mean + 1e-10)
    
    result = RobustnessResult(
        test_name="boundary_sensitivity",
        parameter_values=boundary_distances,
        string_tensions=string_tensions,
        r_squared_values=r_squared_values,
        energy_drifts=energy_drifts,
        tension_mean=tension_mean,
        tension_std=tension_std,
        tension_cv=tension_cv,
        converged=tension_cv < 0.15  # Slightly more lenient
    )
    
    print(f"\n{'='*70}")
    print(f"RESULT: σ = {tension_mean:.4f} ± {tension_std:.4f} (CV = {tension_cv:.2%})")
    print(f"BOUNDARY INSENSITIVE: {'✅ YES' if result.converged else '❌ NO'}")
    print(f"{'='*70}\n")
    
    return result


# =============================================================================
# TEST 4: Energy Conservation Diagnostics
# =============================================================================

def test_energy_conservation(
    grid_size: int = 20,
    total_time: float = 20.0,
    dt: float = 0.02,
    seed: int = 42
) -> Dict:
    """
    Detailed energy conservation diagnostics during flux tube evolution.
    """
    print("="*70)
    print("TEST 4: ENERGY CONSERVATION DIAGNOSTICS")
    print("="*70)
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    # Stabilize
    for _ in range(100):
        engine.evolve_timestep(dt)
    
    # Create two excitations
    sep = 10.0
    amplitude = 0.3 * p.omega_0
    pos1, pos2 = create_two_excitations(engine, sep, amplitude, 2.0, axis=0)
    
    initial_energy = engine.compute_total_energy()
    
    # Track energy over time
    time_points = []
    total_energies = []
    kinetic_energies = []
    potential_energies = []
    energy_drifts = []
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    print(f"\nEvolving for {total_time}s with dt={dt}...")
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            E_total = engine.compute_total_energy()
            
            # Kinetic energy
            KE = 0.5 * (
                np.sum(engine.pi_rho**2) / p.M_rho +
                np.sum(engine.pi_sigma**2) / p.M_sigma +
                np.sum(engine.pi_tau**2) / p.M_tau +
                np.sum(engine.pi_phi**2) / p.M_phi +
                np.sum(engine.pi_omega**2) / p.M_omega
            ) * engine.dx**3
            PE = E_total - KE
            
            drift = (E_total - initial_energy) / abs(initial_energy) * 100
            
            time_points.append(engine.time)
            total_energies.append(E_total)
            kinetic_energies.append(KE)
            potential_energies.append(PE)
            energy_drifts.append(drift)
    
    # Statistics
    max_drift = max(abs(d) for d in energy_drifts)
    mean_drift = np.mean(energy_drifts)
    std_drift = np.std(energy_drifts)
    
    # KE/PE ratio stability
    KE_PE_ratios = [k/(p+1e-10) for k, p in zip(kinetic_energies, potential_energies)]
    ratio_mean = np.mean(KE_PE_ratios)
    ratio_std = np.std(KE_PE_ratios)
    
    print(f"\n  Initial energy: {initial_energy:.4f}")
    print(f"  Final energy:   {total_energies[-1]:.4f}")
    print(f"  Max drift:      {max_drift:.6f}%")
    print(f"  Mean drift:     {mean_drift:.6f}%")
    print(f"  Drift std:      {std_drift:.6f}%")
    print(f"  KE/PE ratio:    {ratio_mean:.4f} ± {ratio_std:.4f}")
    
    energy_conserved = max_drift < 0.1  # < 0.1% drift
    
    result = {
        'test_name': 'energy_conservation',
        'initial_energy': float(initial_energy),
        'final_energy': float(total_energies[-1]),
        'max_drift_pct': float(max_drift),
        'mean_drift_pct': float(mean_drift),
        'std_drift_pct': float(std_drift),
        'ke_pe_ratio_mean': float(ratio_mean),
        'ke_pe_ratio_std': float(ratio_std),
        'energy_conserved': energy_conserved,
        'time_series': {
            'time': [float(t) for t in time_points],
            'total_energy': [float(e) for e in total_energies],
            'drift_pct': [float(d) for d in energy_drifts]
        }
    }
    
    print(f"\n{'='*70}")
    print(f"ENERGY CONSERVED: {'✅ YES' if energy_conserved else '❌ NO'} (max drift {max_drift:.6f}%)")
    print(f"{'='*70}\n")
    
    return result


# =============================================================================
# TEST 5: Parameter Scaling Robustness
# =============================================================================

def test_scaling_robustness(
    a_omega_values: List[float] = [0.5, 1.0, 2.0],
    grid_size: int = 20,
    seed: int = 42
) -> RobustnessResult:
    """
    Test if string tension scales predictably with potential depth a_ω.
    
    σ should scale with √a_ω (domain wall thickness ~ 1/√a_ω)
    """
    print("="*70)
    print("TEST 5: PARAMETER SCALING ROBUSTNESS")
    print("="*70)
    
    separations = [6, 8, 10, 12, 14]
    
    string_tensions = []
    r_squared_values = []
    energy_drifts = []
    
    for a_omega in a_omega_values:
        print(f"\na_ω = {a_omega}")
        
        # Create engine with modified parameters
        params = QMRTFrequencyParameters(a_omega=a_omega)
        engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
        engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
        
        wall_energies = []
        
        for i, sep in enumerate(separations):
            engine_i = QMRTFrequencyEngine(grid_size=grid_size, params=params)
            engine_i.initialize_frequency_domains(amplitude=0.02, seed=seed + i)
            
            for _ in range(50):
                engine_i.evolve_timestep(0.02)
            
            amplitude = 0.3 * params.omega_0
            pos1, pos2 = create_two_excitations(engine_i, sep, amplitude, 2.0, axis=0)
            
            point = measure_separation_energy(
                engine_i, pos1, pos2,
                excitation_radius=4.0,
                equilibration_time=4.0,
                dt=0.02
            )
            
            wall_energies.append(point.domain_wall_energy)
        
        sigma, E0, r2 = fit_wall_energy(separations, wall_energies)
        
        string_tensions.append(sigma)
        r_squared_values.append(r2)
        energy_drifts.append(0.0)  # Not tracked here
        
        print(f"  σ = {sigma:.4f}, R² = {r2:.4f}")
    
    # Check scaling: σ should scale with √a_ω
    # Normalize by √a_ω
    normalized_tensions = [s / np.sqrt(a) for s, a in zip(string_tensions, a_omega_values)]
    
    tension_mean = np.mean(normalized_tensions)
    tension_std = np.std(normalized_tensions)
    tension_cv = tension_std / (tension_mean + 1e-10)
    
    result = RobustnessResult(
        test_name="scaling_robustness",
        parameter_values=a_omega_values,
        string_tensions=string_tensions,
        r_squared_values=r_squared_values,
        energy_drifts=energy_drifts,
        tension_mean=tension_mean,
        tension_std=tension_std,
        tension_cv=tension_cv,
        converged=tension_cv < 0.2
    )
    
    print(f"\n{'='*70}")
    print(f"σ/√a_ω = {tension_mean:.4f} ± {tension_std:.4f} (CV = {tension_cv:.2%})")
    print(f"SCALING CONSISTENT: {'✅ YES' if result.converged else '❌ NO'}")
    print(f"{'='*70}\n")
    
    return result


# =============================================================================
# MAIN: Run All Robustness Tests
# =============================================================================

def run_all_robustness_tests(seed: int = 42) -> Dict:
    """
    Run all 5 robustness verification tests.
    """
    print("\n" + "="*70)
    print("FLUX TUBE ROBUSTNESS VERIFICATION SUITE")
    print("="*70)
    print("5 systematic tests to validate E(r) ~ σr finding")
    print("="*70 + "\n")
    
    results = {}
    
    # Test 1: Grid resolution
    results['grid_resolution'] = test_grid_resolution_independence(
        grid_sizes=[16, 20, 24],
        seed=seed
    )
    
    # Test 2: Timestep
    results['timestep'] = test_timestep_convergence(
        timesteps=[0.04, 0.02, 0.01],
        grid_size=20,
        seed=seed
    )
    
    # Test 3: Boundary
    results['boundary'] = test_boundary_sensitivity(
        grid_sizes=[20, 24, 28],
        seed=seed
    )
    
    # Test 4: Energy conservation
    results['energy'] = test_energy_conservation(
        grid_size=20,
        total_time=15.0,
        dt=0.02,
        seed=seed
    )
    
    # Test 5: Parameter scaling
    results['scaling'] = test_scaling_robustness(
        a_omega_values=[0.5, 1.0, 2.0],
        grid_size=20,
        seed=seed
    )
    
    # Summary
    print("\n" + "="*70)
    print("ROBUSTNESS VERIFICATION SUMMARY")
    print("="*70)
    
    all_passed = True
    
    for name, result in results.items():
        if isinstance(result, dict):
            passed = result.get('energy_conserved', False)
        else:
            passed = result.converged
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:25s}: {status}")
        
        if not passed:
            all_passed = False
    
    print(f"\n  OVERALL: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("="*70 + "\n")
    
    return {
        'results': {k: (v.to_dict() if hasattr(v, 'to_dict') else v) for k, v in results.items()},
        'all_passed': all_passed
    }


if __name__ == "__main__":
    results = run_all_robustness_tests(seed=42)
    print("\nAll tests complete.")
