"""
Dimensional Saturation and Time Calibration Analysis
=====================================================

PURPOSE:
1. Test if D_eff saturates at 3.0 (suggesting the medium "wants" 4D)
2. Calibrate simulation time to physical time estimates

QUESTIONS:
- Does D_eff persistently stay at exactly 3.0? (suggests 4D pressure)
- What physical timescale does one simulation time unit represent?

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label
from scipy.linalg import eigh
from typing import Dict, List, Any
import json
import os
import time


class DimensionalSaturationAnalyzer:
    """
    Analyze dimensional saturation and time calibration.
    """
    
    def __init__(self, size: int = 48, dt: float = 0.10, seed: int = 42):
        """Initialize with standard Regulated Recovery v1.1."""
        
        self.size = size
        self.dt = dt
        
        np.random.seed(seed)
        
        # Regulated Recovery v1.1 parameters
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0  # Base wave speed squared
        self.gamma = 0.007
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Fields
        self.psi_r = np.ones((size, size, size)) + np.random.randn(size, size, size) * 0.01
        self.psi_i = np.random.randn(size, size, size) * 0.01
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size))
        
        # Tracking
        self.d_eff_history = []
        self.saturation_count = 0  # How many times D_eff > 2.95
        self.total_creations = 0
    
    def step(self):
        """Advance simulation by one timestep."""
        self.step_count += 1
        self.global_T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # τ dynamics
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        if self.damping_to_tau > 0:
            self.tau += self.damping_to_tau * damped_energy
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Creation events
        high_tau_mask = self.tau > self.tau_creation_threshold
        if np.any(high_tau_mask):
            n_candidates = np.sum(high_tau_mask)
            create_prob = self.creation_rate * (self.tau[high_tau_mask] - self.tau_creation_threshold)
            create_mask_1d = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask_1d):
                coords = np.array(np.where(high_tau_mask)).T
                create_coords = coords[create_mask_1d]
                
                for (cx, cy, cz) in create_coords[:3]:
                    self._inject_vortex(cx, cy, cz, np.random.choice([-1, 1]))
                    self.tau[cx, cy, cz] = 1.0
                    self.total_creations += 1
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def _inject_vortex(self, cx, cy, cz, chirality):
        """Inject a vortex."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / 18)
        
        vortex = np.tanh(r / 2.5) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        blend = 0.15 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def compute_d_eff(self) -> Dict[str, float]:
        """Compute D_eff and check for saturation."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        threshold = np.percentile(topology, 90)
        active_mask = topology > threshold
        n_active = np.sum(active_mask)
        
        if n_active < 10:
            return {'D_eff': 0, 'valid': False}
        
        active_coords = np.array(np.where(active_mask)).T
        weights = topology[active_mask]
        weights = weights / np.sum(weights)
        
        centroid = np.average(active_coords, axis=0, weights=weights)
        centered = active_coords - centroid
        
        cov = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                cov[i, j] = np.sum(weights * centered[:, i] * centered[:, j])
        
        eigenvalues, _ = eigh(cov)
        eigenvalues = np.sort(eigenvalues)[::-1]
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        
        lambda1, lambda2, lambda3 = eigenvalues
        
        sum_lambda = lambda1 + lambda2 + lambda3
        sum_lambda_sq = lambda1**2 + lambda2**2 + lambda3**2
        D_eff = sum_lambda**2 / sum_lambda_sq if sum_lambda_sq > 0 else 1.0
        
        # Check for saturation (D_eff very close to 3.0)
        if D_eff > 2.95:
            self.saturation_count += 1
        
        return {
            'D_eff': float(D_eff),
            'lambda1': float(lambda1),
            'lambda2': float(lambda2),
            'lambda3': float(lambda3),
            'r2': float(lambda2/lambda1) if lambda1 > 0 else 0,
            'r3': float(lambda3/lambda1) if lambda1 > 0 else 0,
            'n_active': int(n_active),
            'valid': True,
        }


def compute_time_calibration():
    """
    Calibrate simulation time to physical time.
    
    The simulation uses dimensionless units. To map to physical time:
    
    1. Grid spacing (dx) sets the length scale
    2. c_0 = sqrt(c_0_sq) = 2.0 sets the base wave speed
    3. dt = 0.10-0.12 is the timestep in simulation units
    
    Physical interpretation:
    - If dx = Planck length (1.6e-35 m), then c_0 = 2 dx/dt_sim
    - One simulation time unit = dt_sim / (c_0 / dx)
    
    Alternative: Use dispersion relation ω² = c²k²
    - At k = 2π/L (fundamental mode), ω = c * 2π/L
    - Period T = L/c (crossing time)
    """
    
    print("=" * 70)
    print("  TIME CALIBRATION ANALYSIS")
    print("=" * 70)
    print()
    
    # Simulation parameters
    dt = 0.10  # Simulation timestep
    c_0 = 2.0  # Base wave speed (sqrt of c_0_sq = 4.0)
    dx = 1.0   # Grid spacing (simulation units)
    L = 32     # Grid size
    
    print("Simulation Parameters (dimensionless units):")
    print(f"  dt = {dt}")
    print(f"  c_0 = {c_0}")
    print(f"  dx = {dx}")
    print(f"  L = {L}")
    print()
    
    # Crossing time in simulation units
    T_cross_sim = L / c_0
    print(f"Light crossing time (simulation): T_cross = L/c_0 = {T_cross_sim:.1f}")
    print()
    
    # Physical time interpretation depends on length scale choice
    print("-" * 70)
    print("PHYSICAL TIME MAPPING (depends on length scale assumption)")
    print("-" * 70)
    print()
    
    # Option A: Planck scale
    L_planck = 1.616e-35  # meters
    c_light = 3e8  # m/s
    
    # If dx = L_planck, then c_0 corresponds to 2 * L_planck / (1 sim time unit)
    # So 1 sim time unit = 2 * L_planck / c_0_physical
    # But c_0_physical should be c_light for relativistic behavior
    
    # Time for light to cross one grid cell in physical units
    t_cell_planck = L_planck / c_light
    
    # In simulation, light crosses one cell in dt/c_0 = 0.10/2.0 = 0.05 time units
    dt_per_cell = dt / c_0
    
    # So 1 simulation time unit = t_cell_planck / dt_per_cell
    t_sim_unit_planck = t_cell_planck / dt_per_cell
    
    print("Option A: Planck Scale (dx = Planck length)")
    print(f"  dx = {L_planck:.2e} m")
    print(f"  1 simulation time unit = {t_sim_unit_planck:.2e} seconds")
    print(f"  T=1000 (sim) = {1000 * t_sim_unit_planck:.2e} seconds")
    t_planck = 5.39e-44  # Planck time
    print(f"  1 sim unit = {t_sim_unit_planck / t_planck:.1f} Planck times")
    print()
    
    # Option B: Nuclear scale (1 fm)
    L_fm = 1e-15  # 1 femtometer
    t_cell_fm = L_fm / c_light
    t_sim_unit_fm = t_cell_fm / dt_per_cell
    
    print("Option B: Nuclear Scale (dx = 1 femtometer)")
    print(f"  dx = {L_fm:.2e} m")
    print(f"  1 simulation time unit = {t_sim_unit_fm:.2e} seconds")
    print(f"  T=1000 (sim) = {1000 * t_sim_unit_fm:.2e} seconds")
    print()
    
    # Option C: Atomic scale (1 Angstrom)
    L_angstrom = 1e-10
    t_cell_angstrom = L_angstrom / c_light
    t_sim_unit_angstrom = t_cell_angstrom / dt_per_cell
    
    print("Option C: Atomic Scale (dx = 1 Angstrom)")
    print(f"  dx = {L_angstrom:.2e} m")
    print(f"  1 simulation time unit = {t_sim_unit_angstrom:.2e} seconds")
    print(f"  T=1000 (sim) = {1000 * t_sim_unit_angstrom:.2e} seconds")
    print()
    
    # Summary table
    print("-" * 70)
    print("SUMMARY: Simulation T=1000 corresponds to:")
    print("-" * 70)
    print(f"  Planck scale:  {1000 * t_sim_unit_planck:.2e} s = {1000 * t_sim_unit_planck / t_planck:.0e} Planck times")
    print(f"  Nuclear scale: {1000 * t_sim_unit_fm:.2e} s")
    print(f"  Atomic scale:  {1000 * t_sim_unit_angstrom:.2e} s")
    print()
    
    return {
        'planck': {
            'dx': L_planck,
            't_per_sim_unit': t_sim_unit_planck,
            't_1000': 1000 * t_sim_unit_planck,
        },
        'nuclear': {
            'dx': L_fm,
            't_per_sim_unit': t_sim_unit_fm,
            't_1000': 1000 * t_sim_unit_fm,
        },
        'atomic': {
            'dx': L_angstrom,
            't_per_sim_unit': t_sim_unit_angstrom,
            't_1000': 1000 * t_sim_unit_angstrom,
        }
    }


def run_saturation_test(target_T: float = 1000.0, max_wall_seconds: float = 90.0):
    """
    Run long simulation to test D_eff saturation at 3.0.
    
    If D_eff persistently stays at 3.0, this suggests the medium
    "wants" more degrees of freedom but is constrained by the 3D grid.
    """
    print()
    print("=" * 70)
    print("  DIMENSIONAL SATURATION TEST")
    print("=" * 70)
    print()
    print(f"Target T: {target_T}")
    print("Question: Does D_eff saturate at exactly 3.0?")
    print("          (Would suggest pressure toward 4D)")
    print()
    
    sim = DimensionalSaturationAnalyzer(size=48, dt=0.10, seed=42)
    
    t_start = time.time()
    measure_interval = 25.0
    last_measure = 0.0
    
    d_eff_values = []
    
    print(f"{'T':>8} | {'D_eff':>8} | {'r2':>6} | {'r3':>6} | {'Gap from 3':>12} | Status")
    print("-" * 65)
    
    while sim.global_T < target_T:
        # Check wall time
        if time.time() - t_start > max_wall_seconds:
            print(f"\nWall time limit reached at T={sim.global_T:.1f}")
            break
        
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            metrics = sim.compute_d_eff()
            
            if metrics['valid']:
                d_eff = metrics['D_eff']
                d_eff_values.append(d_eff)
                gap = 3.0 - d_eff
                
                status = "SATURATED" if d_eff > 2.95 else "sub-3D"
                
                print(f"{sim.global_T:>8.1f} | {d_eff:>8.4f} | {metrics['r2']:>6.3f} | "
                      f"{metrics['r3']:>6.3f} | {gap:>12.4f} | {status}")
    
    # Analysis
    print()
    print("=" * 70)
    print("  SATURATION ANALYSIS")
    print("=" * 70)
    
    d_eff_array = np.array(d_eff_values)
    
    print(f"\nTotal measurements: {len(d_eff_values)}")
    print(f"Saturation count (D_eff > 2.95): {sim.saturation_count}")
    print(f"Saturation rate: {100 * sim.saturation_count / len(d_eff_values):.1f}%")
    print()
    print(f"D_eff statistics:")
    print(f"  Mean: {np.mean(d_eff_array):.4f}")
    print(f"  Std:  {np.std(d_eff_array):.4f}")
    print(f"  Max:  {np.max(d_eff_array):.4f}")
    print(f"  Min:  {np.min(d_eff_array):.4f}")
    print()
    
    # Theoretical maximum
    print("Theoretical bounds:")
    print(f"  D_eff maximum in 3D grid: 3.000")
    print(f"  Observed maximum: {np.max(d_eff_array):.4f}")
    print(f"  Gap: {3.0 - np.max(d_eff_array):.4f}")
    print()
    
    # Interpretation
    mean_d_eff = np.mean(d_eff_array)
    if mean_d_eff > 2.9:
        print("INTERPRETATION: D_eff consistently near 3.0")
        print("  → The medium SATURATES at maximum available dimensions")
        print("  → In a 4D grid, D_eff would likely exceed 3.0")
        print("  → This suggests 'dimensional pressure' toward higher D")
    elif mean_d_eff > 2.5:
        print("INTERPRETATION: D_eff high but not saturating")
        print("  → The medium prefers high dimensionality")
        print("  → But does not fully use all available degrees of freedom")
    else:
        print("INTERPRETATION: D_eff moderate")
        print("  → The medium does not strongly prefer maximum dimensions")
    
    return {
        'd_eff_values': d_eff_values,
        'mean': float(np.mean(d_eff_array)),
        'std': float(np.std(d_eff_array)),
        'max': float(np.max(d_eff_array)),
        'saturation_rate': sim.saturation_count / len(d_eff_values),
        'total_T': sim.global_T,
    }


def main():
    """Run saturation and time calibration analysis."""
    
    # Time calibration
    time_cal = compute_time_calibration()
    
    # Saturation test
    sat_results = run_saturation_test(target_T=1000.0, max_wall_seconds=90.0)
    
    # Combined interpretation
    print()
    print("=" * 70)
    print("  COMBINED INTERPRETATION")
    print("=" * 70)
    print()
    print("Q1: Could the medium reach 4D degrees of freedom?")
    print("-" * 50)
    if sat_results['saturation_rate'] > 0.5:
        print("  YES - D_eff saturates at 3.0 in >50% of measurements")
        print("  The medium appears to 'want' more dimensions than available")
        print("  A 4D simulation grid would likely show D_eff > 3")
    else:
        print("  UNCERTAIN - D_eff does not consistently saturate at 3.0")
        print("  The medium may naturally prefer 3D isotropy")
    print()
    
    print("Q2: What physical time does simulation time represent?")
    print("-" * 50)
    print("  The mapping depends on your choice of length scale:")
    print()
    print(f"  If the grid represents PLANCK scale physics:")
    print(f"    T_sim=1000 ≈ {time_cal['planck']['t_1000']:.1e} seconds")
    print(f"    This is {time_cal['planck']['t_1000'] / 5.39e-44:.0e} Planck times")
    print()
    print(f"  If the grid represents NUCLEAR scale physics:")
    print(f"    T_sim=1000 ≈ {time_cal['nuclear']['t_1000']:.1e} seconds")
    print()
    print(f"  If the grid represents ATOMIC scale physics:")
    print(f"    T_sim=1000 ≈ {time_cal['atomic']['t_1000']:.1e} seconds")
    print()
    print("  KEY INSIGHT: Simulation time is MUCH shorter than everyday time")
    print("  because the simulation operates at fundamental physics scales.")
    
    # Save results
    output_dir = '/app/backend/qmrt_topology/papers'
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        'saturation': sat_results,
        'time_calibration': time_cal,
    }
    
    with open(f'{output_dir}/dimensional_saturation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print(f"Results saved to: {output_dir}/dimensional_saturation_results.json")
    
    return results


if __name__ == "__main__":
    main()
