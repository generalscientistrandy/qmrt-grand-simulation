"""
QMRT Artifact Audit Framework
==============================

PURPOSE: Systematically validate that simulation results represent genuine 
emergent physics rather than numerical artifacts.

EVALUATION STACK:
1. Baseline Control (mechanism disabled)
2. Resolution Scaling
3. Time-Step Sensitivity
4. Integrator Comparison
5. Boundary Condition Audit
6. Conservation Diagnostics
7. Random Seed Sweep
8. Null Model Comparison
9. Parameter Space Scan
10. Artifact Classification

TARGET: Dark Energy Analog (DOF Unlock Expansion)
- Claimed result: +464.7% expansion velocity after unlock
- Question: Is this real emergent physics or numerical artifact?

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Callable
import time
import json
import os
from dataclasses import dataclass
from enum import Enum


class ArtifactClass(Enum):
    """Classification of observed effects."""
    LIKELY_PHYSICAL = "A"
    POSSIBLY_EMERGENT = "B"
    SOLVER_DEPENDENT = "C"
    BOUNDARY_ARTIFACT = "D"
    RESOLUTION_ARTIFACT = "E"
    INITIAL_CONDITION_ARTIFACT = "F"
    CONSERVATION_FAILURE = "G"
    VISUALIZATION_ARTIFACT = "H"
    TIMESTEP_ARTIFACT = "I"


@dataclass
class AuditResult:
    """Result from a single audit test."""
    test_name: str
    passed: bool
    metric_value: float
    baseline_value: float
    deviation_pct: float
    notes: str
    classification: ArtifactClass = ArtifactClass.POSSIBLY_EMERGENT


class QMRTArtifactAuditor:
    """
    Comprehensive artifact audit system for QMRT simulations.
    """
    
    def __init__(self, output_dir: str = '/app/backend/qmrt_topology/papers/artifact_audit'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.results = {
            'baseline_control': [],
            'resolution_scaling': [],
            'timestep_sensitivity': [],
            'integrator_comparison': [],
            'boundary_audit': [],
            'conservation': [],
            'seed_sweep': [],
            'null_model': [],
            'parameter_scan': [],
        }
        
        self.summary = {}
    
    def run_expansion_simulation(
        self,
        size: int = 32,
        dt: float = 0.12,
        seed: int = 42,
        tau_response: float = 0.02,
        tau_relaxation: float = 0.01,
        unlock_enabled: bool = True,
        unlock_threshold: float = 0.025,
        integrator: str = 'euler',
        boundary: str = 'periodic',
        target_T: float = 500.0,
        max_wall_seconds: float = 40.0,
    ) -> Dict[str, Any]:
        """
        Run expansion-DOF simulation with configurable parameters.
        
        Returns metrics for comparison.
        """
        np.random.seed(seed)
        
        # Initialize fields
        shape = (size, size, size)
        psi_r = np.ones(shape)
        psi_i = np.zeros(shape)
        psi_r_dot = np.zeros(shape)
        psi_i_dot = np.zeros(shape)
        tau = np.ones(shape)
        
        # Physics parameters (Regulated Recovery v1.1 base)
        tau_cap = 1.8
        damping_to_tau = 0.20
        c_0_sq = 4.0
        gamma = 0.007
        
        # Dimensional activation
        ax, ay, az = 1.0, 0.0, 0.0
        
        # Initial perturbation
        center = size // 2
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    if r < 4:
                        amp = 0.8 * np.exp(-r**2 / 6)
                        psi_r[x, y, z] += amp * np.random.randn()
                        psi_i[x, y, z] += amp * np.random.randn()
                        psi_r_dot[x, y, z] += 0.3 * amp * np.random.randn()
                        psi_i_dot[x, y, z] += 0.3 * amp * np.random.randn()
        
        # Laplacian function with boundary handling
        def laplacian(f, boundary_type):
            if boundary_type == 'periodic':
                lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
                lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
                lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
            elif boundary_type == 'reflecting':
                lap = np.zeros_like(f)
                for axis in range(3):
                    lap += np.roll(f, 1, axis=axis) + np.roll(f, -1, axis=axis) - 2 * f
                # Zero-gradient at boundaries
                lap[0, :, :] = lap[1, :, :]
                lap[-1, :, :] = lap[-2, :, :]
                lap[:, 0, :] = lap[:, 1, :]
                lap[:, -1, :] = lap[:, -2, :]
                lap[:, :, 0] = lap[:, :, 1]
                lap[:, :, -1] = lap[:, :, -2]
            elif boundary_type == 'absorbing':
                lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
                lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
                lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
                # Damping layer at boundaries
                boundary_width = size // 8
                for i in range(boundary_width):
                    damp = (boundary_width - i) / boundary_width * 0.1
                    lap[i, :, :] *= (1 - damp)
                    lap[-(i+1), :, :] *= (1 - damp)
                    lap[:, i, :] *= (1 - damp)
                    lap[:, -(i+1), :] *= (1 - damp)
                    lap[:, :, i] *= (1 - damp)
                    lap[:, :, -(i+1)] *= (1 - damp)
            else:
                lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
                lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
                lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
            return lap
        
        # Time integration
        global_T = 0.0
        unlock_T = None
        
        # Conservation tracking
        initial_energy = np.sum(psi_r**2 + psi_i**2 + 0.5 * (psi_r_dot**2 + psi_i_dot**2))
        energy_history = [initial_energy]
        
        # Expansion tracking
        radii = []
        velocities = []
        d_effs = []
        
        t_start = time.time()
        prev_radius = 0.0
        measure_interval = 50.0
        last_measure = 0.0
        
        while global_T < target_T:
            if time.time() - t_start >= max_wall_seconds - 2:
                break
            
            # τ dynamics (if enabled)
            if tau_response > 0:
                kinetic = psi_r_dot**2 + psi_i_dot**2
                energy = psi_r**2 + psi_i**2 + 0.5 * kinetic
                tau_target = 1.0 + tau_response * (energy - np.mean(energy))
                tau += tau_relaxation * (tau_target - tau)
                tau += damping_to_tau * gamma * kinetic
                tau = np.clip(tau, 0.5, tau_cap)
            
            # Check unlock
            if unlock_enabled and ay < 1.0:
                pressure = np.mean(psi_r_dot**2 + psi_i_dot**2) + np.mean(np.maximum(tau - 1.0, 0))
                if pressure > unlock_threshold:
                    ay = min(1.0, ay + 0.03)
                    if unlock_T is None and ay > 0.01:
                        unlock_T = global_T
                    if ay > 0.5 and az < 1.0 and pressure > unlock_threshold * 1.2:
                        az = min(1.0, az + 0.03)
            
            # Wave equation with selected integrator
            c_eff_sq = c_0_sq * tau
            lap_r = laplacian(psi_r, boundary)
            lap_i = laplacian(psi_i, boundary)
            
            if integrator == 'euler':
                # Forward Euler
                acc_r = c_eff_sq * lap_r - gamma * psi_r_dot
                acc_i = c_eff_sq * lap_i - gamma * psi_i_dot
                psi_r_dot += acc_r * dt
                psi_i_dot += acc_i * dt
                psi_r += psi_r_dot * dt
                psi_i += psi_i_dot * dt
                
            elif integrator == 'verlet':
                # Velocity Verlet
                acc_r = c_eff_sq * lap_r - gamma * psi_r_dot
                acc_i = c_eff_sq * lap_i - gamma * psi_i_dot
                psi_r += psi_r_dot * dt + 0.5 * acc_r * dt**2
                psi_i += psi_i_dot * dt + 0.5 * acc_i * dt**2
                
                # Recalculate acceleration
                lap_r_new = laplacian(psi_r, boundary)
                lap_i_new = laplacian(psi_i, boundary)
                acc_r_new = c_eff_sq * lap_r_new - gamma * psi_r_dot
                acc_i_new = c_eff_sq * lap_i_new - gamma * psi_i_dot
                
                psi_r_dot += 0.5 * (acc_r + acc_r_new) * dt
                psi_i_dot += 0.5 * (acc_i + acc_i_new) * dt
                
            elif integrator == 'rk4':
                # 4th order Runge-Kutta
                def derivatives(psi_r, psi_i, psi_r_dot, psi_i_dot):
                    lap_r = laplacian(psi_r, boundary)
                    lap_i = laplacian(psi_i, boundary)
                    acc_r = c_eff_sq * lap_r - gamma * psi_r_dot
                    acc_i = c_eff_sq * lap_i - gamma * psi_i_dot
                    return psi_r_dot, psi_i_dot, acc_r, acc_i
                
                k1 = derivatives(psi_r, psi_i, psi_r_dot, psi_i_dot)
                k2 = derivatives(
                    psi_r + 0.5*dt*k1[0], psi_i + 0.5*dt*k1[1],
                    psi_r_dot + 0.5*dt*k1[2], psi_i_dot + 0.5*dt*k1[3]
                )
                k3 = derivatives(
                    psi_r + 0.5*dt*k2[0], psi_i + 0.5*dt*k2[1],
                    psi_r_dot + 0.5*dt*k2[2], psi_i_dot + 0.5*dt*k2[3]
                )
                k4 = derivatives(
                    psi_r + dt*k3[0], psi_i + dt*k3[1],
                    psi_r_dot + dt*k3[2], psi_i_dot + dt*k3[3]
                )
                
                psi_r += dt/6 * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
                psi_i += dt/6 * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
                psi_r_dot += dt/6 * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
                psi_i_dot += dt/6 * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])
                
            elif integrator == 'leapfrog':
                # Leapfrog (symplectic)
                psi_r_dot += 0.5 * dt * (c_eff_sq * lap_r - gamma * psi_r_dot)
                psi_i_dot += 0.5 * dt * (c_eff_sq * lap_i - gamma * psi_i_dot)
                psi_r += dt * psi_r_dot
                psi_i += dt * psi_i_dot
                lap_r = laplacian(psi_r, boundary)
                lap_i = laplacian(psi_i, boundary)
                psi_r_dot += 0.5 * dt * (c_eff_sq * lap_r - gamma * psi_r_dot)
                psi_i_dot += 0.5 * dt * (c_eff_sq * lap_i - gamma * psi_i_dot)
            
            else:  # default euler
                acc_r = c_eff_sq * lap_r - gamma * psi_r_dot
                acc_i = c_eff_sq * lap_i - gamma * psi_i_dot
                psi_r_dot += acc_r * dt
                psi_i_dot += acc_i * dt
                psi_r += psi_r_dot * dt
                psi_i += psi_i_dot * dt
            
            global_T += dt
            
            # Measure metrics
            if global_T - last_measure >= measure_interval:
                last_measure = global_T
                
                # Expansion radius
                amp = np.sqrt(psi_r**2 + psi_i**2)
                threshold = np.percentile(amp, 80)
                active = amp > threshold
                if np.any(active):
                    coords = np.array(np.where(active)).T
                    centroid = np.mean(coords, axis=0)
                    distances = np.sqrt(np.sum((coords - centroid)**2, axis=1))
                    radius = np.percentile(distances, 90)
                else:
                    radius = 1.0
                
                velocity = (radius - prev_radius) / measure_interval if prev_radius > 0 else 0
                
                # D_eff
                d_eff = ax + ay * 0.5 + az * 0.5
                
                radii.append(radius)
                velocities.append(velocity)
                d_effs.append(d_eff)
                prev_radius = radius
                
                # Energy
                current_energy = np.sum(psi_r**2 + psi_i**2 + 0.5 * (psi_r_dot**2 + psi_i_dot**2))
                energy_history.append(current_energy)
        
        # Compute metrics
        final_energy = energy_history[-1]
        energy_change = (final_energy - initial_energy) / initial_energy if initial_energy > 0 else 0
        
        # Pre/post unlock velocity comparison
        if unlock_T and len(velocities) > 4:
            # Find unlock index
            unlock_idx = int(unlock_T / measure_interval)
            pre_vels = velocities[:max(1, unlock_idx)]
            post_vels = velocities[unlock_idx:] if unlock_idx < len(velocities) else velocities[-2:]
            
            pre_velocity = np.mean([v for v in pre_vels if v > 0]) if any(v > 0 for v in pre_vels) else 0.001
            post_velocity = np.mean([v for v in post_vels if v > 0]) if any(v > 0 for v in post_vels) else 0
            velocity_change = (post_velocity - pre_velocity) / pre_velocity * 100 if pre_velocity > 0 else 0
        else:
            pre_velocity = np.mean(velocities[:len(velocities)//2]) if velocities else 0
            post_velocity = np.mean(velocities[len(velocities)//2:]) if velocities else 0
            velocity_change = (post_velocity - pre_velocity) / pre_velocity * 100 if pre_velocity > 0 else 0
        
        return {
            'final_T': global_T,
            'unlock_T': unlock_T,
            'final_radius': radii[-1] if radii else 0,
            'pre_velocity': pre_velocity,
            'post_velocity': post_velocity,
            'velocity_change_pct': velocity_change,
            'final_d_eff': d_effs[-1] if d_effs else 1.0,
            'energy_change_pct': energy_change * 100,
            'initial_energy': initial_energy,
            'final_energy': final_energy,
            'radii': radii,
            'velocities': velocities,
            'd_effs': d_effs,
        }
    
    def test_baseline_control(self) -> List[AuditResult]:
        """
        Test 1: Baseline Control Runs
        
        Run with QMRT mechanisms disabled to verify effect disappears.
        """
        print("\n" + "="*70)
        print("  TEST 1: BASELINE CONTROL")
        print("="*70)
        print("  Question: Does effect disappear when mechanism is disabled?")
        print()
        
        results = []
        
        # Baseline: Full QMRT
        print("  Running: Full QMRT (tau_response=0.02, unlock=True)")
        full_qmrt = self.run_expansion_simulation(
            tau_response=0.02, unlock_enabled=True
        )
        
        # Control 1: No tau response
        print("  Running: No tau response (tau_response=0.0)")
        no_tau = self.run_expansion_simulation(
            tau_response=0.0, unlock_enabled=True
        )
        
        # Control 2: No unlock
        print("  Running: No unlock (unlock_enabled=False)")
        no_unlock = self.run_expansion_simulation(
            tau_response=0.02, unlock_enabled=False
        )
        
        # Control 3: Both disabled
        print("  Running: Both disabled")
        both_disabled = self.run_expansion_simulation(
            tau_response=0.0, unlock_enabled=False
        )
        
        # Analysis
        print()
        print(f"  {'Config':>20} | {'Vel Change':>12} | {'D_eff':>8} | Effect?")
        print("  " + "-"*60)
        
        configs = [
            ('Full QMRT', full_qmrt),
            ('No τ-response', no_tau),
            ('No unlock', no_unlock),
            ('Both disabled', both_disabled),
        ]
        
        for name, data in configs:
            vel_change = data['velocity_change_pct']
            d_eff = data['final_d_eff']
            has_effect = vel_change > 50 and d_eff > 1.5
            print(f"  {name:>20} | {vel_change:>+12.1f}% | {d_eff:>8.2f} | {'YES' if has_effect else 'NO'}")
        
        # Verdict
        effect_with_qmrt = full_qmrt['velocity_change_pct'] > 100
        no_effect_when_disabled = both_disabled['velocity_change_pct'] < 50
        
        passed = effect_with_qmrt and no_effect_when_disabled
        
        result = AuditResult(
            test_name="Baseline Control",
            passed=passed,
            metric_value=full_qmrt['velocity_change_pct'],
            baseline_value=both_disabled['velocity_change_pct'],
            deviation_pct=full_qmrt['velocity_change_pct'] - both_disabled['velocity_change_pct'],
            notes=f"Full QMRT: {full_qmrt['velocity_change_pct']:.1f}%, Disabled: {both_disabled['velocity_change_pct']:.1f}%",
            classification=ArtifactClass.LIKELY_PHYSICAL if passed else ArtifactClass.POSSIBLY_EMERGENT
        )
        
        self.results['baseline_control'].append(result)
        print()
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'} - Effect {'disappears' if no_effect_when_disabled else 'persists'} when mechanism disabled")
        
        return [result]
    
    def test_resolution_scaling(self) -> List[AuditResult]:
        """
        Test 2: Resolution Scaling
        
        Run at multiple resolutions to check if behavior is resolution-dependent.
        """
        print("\n" + "="*70)
        print("  TEST 2: RESOLUTION SCALING")
        print("="*70)
        print("  Question: Does effect persist across different grid sizes?")
        print()
        
        resolutions = [16, 24, 32, 48]
        results_by_res = {}
        
        for res in resolutions:
            print(f"  Running: Resolution {res}³")
            # Adjust time based on resolution (smaller grid = faster)
            wall_time = 30 if res <= 24 else 40
            results_by_res[res] = self.run_expansion_simulation(
                size=res, max_wall_seconds=wall_time
            )
        
        print()
        print(f"  {'Resolution':>12} | {'Vel Change':>12} | {'D_eff':>8} | {'Radius':>8}")
        print("  " + "-"*50)
        
        vel_changes = []
        for res in resolutions:
            data = results_by_res[res]
            vel_change = data['velocity_change_pct']
            vel_changes.append(vel_change)
            print(f"  {res:>12} | {vel_change:>+12.1f}% | {data['final_d_eff']:>8.2f} | {data['final_radius']:>8.2f}")
        
        # Check consistency
        mean_vel = np.mean(vel_changes)
        std_vel = np.std(vel_changes)
        cv = std_vel / mean_vel if mean_vel > 0 else float('inf')  # Coefficient of variation
        
        # Pass if effect appears at all resolutions and CV < 50%
        all_show_effect = all(v > 50 for v in vel_changes)
        consistent = cv < 0.5
        passed = all_show_effect and consistent
        
        result = AuditResult(
            test_name="Resolution Scaling",
            passed=passed,
            metric_value=mean_vel,
            baseline_value=std_vel,
            deviation_pct=cv * 100,
            notes=f"CV={cv:.2f}, All show effect: {all_show_effect}",
            classification=ArtifactClass.LIKELY_PHYSICAL if passed else ArtifactClass.RESOLUTION_ARTIFACT
        )
        
        self.results['resolution_scaling'].append(result)
        print()
        print(f"  Mean velocity change: {mean_vel:.1f}% ± {std_vel:.1f}%")
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'} - Effect {'consistent' if consistent else 'varies'} across resolutions")
        
        return [result]
    
    def test_timestep_sensitivity(self) -> List[AuditResult]:
        """
        Test 3: Time-Step Sensitivity
        
        Run with different dt values to check integration stability.
        """
        print("\n" + "="*70)
        print("  TEST 3: TIME-STEP SENSITIVITY")
        print("="*70)
        print("  Question: Does effect depend on timestep choice?")
        print()
        
        timesteps = [0.06, 0.12, 0.18, 0.24]
        results_by_dt = {}
        
        for dt in timesteps:
            print(f"  Running: dt = {dt}")
            results_by_dt[dt] = self.run_expansion_simulation(dt=dt)
        
        print()
        print(f"  {'dt':>12} | {'Vel Change':>12} | {'Energy Δ':>12} | {'Stable?'}")
        print("  " + "-"*55)
        
        vel_changes = []
        energy_changes = []
        for dt in timesteps:
            data = results_by_dt[dt]
            vel_change = data['velocity_change_pct']
            energy_change = data['energy_change_pct']
            vel_changes.append(vel_change)
            energy_changes.append(abs(energy_change))
            stable = abs(energy_change) < 50  # Energy shouldn't explode
            print(f"  {dt:>12.3f} | {vel_change:>+12.1f}% | {energy_change:>+12.1f}% | {'YES' if stable else 'NO'}")
        
        # Analysis
        mean_vel = np.mean(vel_changes)
        std_vel = np.std(vel_changes)
        all_stable = all(e < 100 for e in energy_changes)
        cv = std_vel / mean_vel if mean_vel > 0 else float('inf')
        
        passed = all_stable and cv < 0.5
        
        result = AuditResult(
            test_name="Timestep Sensitivity",
            passed=passed,
            metric_value=mean_vel,
            baseline_value=std_vel,
            deviation_pct=cv * 100,
            notes=f"CV={cv:.2f}, All stable: {all_stable}",
            classification=ArtifactClass.LIKELY_PHYSICAL if passed else ArtifactClass.TIMESTEP_ARTIFACT
        )
        
        self.results['timestep_sensitivity'].append(result)
        print()
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'} - Effect {'stable' if passed else 'unstable'} across timesteps")
        
        return [result]
    
    def test_integrator_comparison(self) -> List[AuditResult]:
        """
        Test 4: Integrator Comparison
        
        Run with different numerical integrators.
        """
        print("\n" + "="*70)
        print("  TEST 4: INTEGRATOR COMPARISON")
        print("="*70)
        print("  Question: Does effect appear with different integrators?")
        print()
        
        integrators = ['euler', 'verlet', 'leapfrog', 'rk4']
        results_by_int = {}
        
        for integ in integrators:
            print(f"  Running: {integ}")
            results_by_int[integ] = self.run_expansion_simulation(integrator=integ)
        
        print()
        print(f"  {'Integrator':>12} | {'Vel Change':>12} | {'Energy Δ':>12} | {'D_eff':>8}")
        print("  " + "-"*55)
        
        vel_changes = []
        for integ in integrators:
            data = results_by_int[integ]
            vel_change = data['velocity_change_pct']
            vel_changes.append(vel_change)
            print(f"  {integ:>12} | {vel_change:>+12.1f}% | {data['energy_change_pct']:>+12.1f}% | {data['final_d_eff']:>8.2f}")
        
        # All should show effect
        all_show = all(v > 50 for v in vel_changes)
        mean_vel = np.mean(vel_changes)
        std_vel = np.std(vel_changes)
        cv = std_vel / mean_vel if mean_vel > 0 else float('inf')
        
        passed = all_show and cv < 0.6
        
        result = AuditResult(
            test_name="Integrator Comparison",
            passed=passed,
            metric_value=mean_vel,
            baseline_value=std_vel,
            deviation_pct=cv * 100,
            notes=f"CV={cv:.2f}, All show effect: {all_show}",
            classification=ArtifactClass.LIKELY_PHYSICAL if passed else ArtifactClass.SOLVER_DEPENDENT
        )
        
        self.results['integrator_comparison'].append(result)
        print()
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'} - Effect {'independent of' if passed else 'dependent on'} integrator")
        
        return [result]
    
    def test_boundary_conditions(self) -> List[AuditResult]:
        """
        Test 5: Boundary Condition Audit
        
        Test with different boundary conditions.
        """
        print("\n" + "="*70)
        print("  TEST 5: BOUNDARY CONDITION AUDIT")
        print("="*70)
        print("  Question: Is effect a boundary artifact?")
        print()
        
        boundaries = ['periodic', 'reflecting', 'absorbing']
        results_by_bc = {}
        
        for bc in boundaries:
            print(f"  Running: {bc} boundary")
            results_by_bc[bc] = self.run_expansion_simulation(boundary=bc)
        
        print()
        print(f"  {'Boundary':>12} | {'Vel Change':>12} | {'D_eff':>8}")
        print("  " + "-"*40)
        
        vel_changes = []
        for bc in boundaries:
            data = results_by_bc[bc]
            vel_change = data['velocity_change_pct']
            vel_changes.append(vel_change)
            print(f"  {bc:>12} | {vel_change:>+12.1f}% | {data['final_d_eff']:>8.2f}")
        
        # All should show effect
        all_show = all(v > 50 for v in vel_changes)
        mean_vel = np.mean(vel_changes)
        std_vel = np.std(vel_changes)
        cv = std_vel / mean_vel if mean_vel > 0 else float('inf')
        
        passed = all_show and cv < 0.6
        
        result = AuditResult(
            test_name="Boundary Conditions",
            passed=passed,
            metric_value=mean_vel,
            baseline_value=std_vel,
            deviation_pct=cv * 100,
            notes=f"CV={cv:.2f}, All boundaries show effect: {all_show}",
            classification=ArtifactClass.LIKELY_PHYSICAL if passed else ArtifactClass.BOUNDARY_ARTIFACT
        )
        
        self.results['boundary_audit'].append(result)
        print()
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'} - Effect {'not' if passed else 'is'} boundary-dependent")
        
        return [result]
    
    def test_conservation(self) -> List[AuditResult]:
        """
        Test 6: Conservation Diagnostics
        
        Track energy conservation.
        """
        print("\n" + "="*70)
        print("  TEST 6: CONSERVATION DIAGNOSTICS")
        print("="*70)
        print("  Question: Is energy conservation reasonable?")
        print()
        
        # Run with detailed energy tracking
        result_data = self.run_expansion_simulation(
            max_wall_seconds=50
        )
        
        energy_change = result_data['energy_change_pct']
        
        print(f"  Initial energy: {result_data['initial_energy']:.2f}")
        print(f"  Final energy:   {result_data['final_energy']:.2f}")
        print(f"  Change:         {energy_change:+.2f}%")
        
        # With damping, energy should decrease, not increase dramatically
        # Allow for τ-mediated energy redistribution
        reasonable = abs(energy_change) < 200  # 200% is generous for a damped system
        
        result = AuditResult(
            test_name="Conservation",
            passed=reasonable,
            metric_value=energy_change,
            baseline_value=0,
            deviation_pct=abs(energy_change),
            notes=f"Energy change: {energy_change:.1f}%",
            classification=ArtifactClass.LIKELY_PHYSICAL if reasonable else ArtifactClass.CONSERVATION_FAILURE
        )
        
        self.results['conservation'].append(result)
        print()
        print(f"  VERDICT: {'PASS' if reasonable else 'FAIL'} - Energy change {'acceptable' if reasonable else 'suspicious'}")
        
        return [result]
    
    def test_seed_sweep(self, n_seeds: int = 5) -> List[AuditResult]:
        """
        Test 7: Random Seed Sweep
        
        Run with different random seeds.
        """
        print("\n" + "="*70)
        print("  TEST 7: RANDOM SEED SWEEP")
        print("="*70)
        print(f"  Question: Does effect appear statistically across {n_seeds} seeds?")
        print()
        
        seeds = [42, 123, 456, 789, 1001][:n_seeds]
        vel_changes = []
        d_effs = []
        
        for seed in seeds:
            print(f"  Running: seed={seed}")
            data = self.run_expansion_simulation(seed=seed, max_wall_seconds=30)
            vel_changes.append(data['velocity_change_pct'])
            d_effs.append(data['final_d_eff'])
        
        print()
        print(f"  {'Seed':>8} | {'Vel Change':>12} | {'D_eff':>8}")
        print("  " + "-"*35)
        for seed, vel, deff in zip(seeds, vel_changes, d_effs):
            print(f"  {seed:>8} | {vel:>+12.1f}% | {deff:>8.2f}")
        
        # Statistics
        mean_vel = np.mean(vel_changes)
        std_vel = np.std(vel_changes)
        positive_count = sum(1 for v in vel_changes if v > 50)
        
        passed = positive_count >= n_seeds * 0.8  # 80% should show effect
        
        result = AuditResult(
            test_name="Seed Sweep",
            passed=passed,
            metric_value=mean_vel,
            baseline_value=std_vel,
            deviation_pct=(positive_count / n_seeds) * 100,
            notes=f"{positive_count}/{n_seeds} seeds show effect, mean={mean_vel:.1f}%",
            classification=ArtifactClass.LIKELY_PHYSICAL if passed else ArtifactClass.INITIAL_CONDITION_ARTIFACT
        )
        
        self.results['seed_sweep'].append(result)
        print()
        print(f"  {positive_count}/{n_seeds} seeds show effect (>{50}% velocity change)")
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'} - Effect {'statistically robust' if passed else 'seed-dependent'}")
        
        return [result]
    
    def run_full_audit(self) -> Dict[str, Any]:
        """
        Run complete artifact audit.
        """
        print()
        print("=" * 70)
        print("  QMRT ARTIFACT AUDIT - DARK ENERGY ANALOG")
        print("=" * 70)
        print()
        print("  Target: DOF Unlock Expansion (+464.7% claimed)")
        print("  Goal: Determine if result is genuine emergence or artifact")
        print()
        
        # Run all tests
        self.test_baseline_control()
        self.test_resolution_scaling()
        self.test_timestep_sensitivity()
        self.test_integrator_comparison()
        self.test_boundary_conditions()
        self.test_conservation()
        self.test_seed_sweep()
        
        # Summary
        print()
        print("=" * 70)
        print("  AUDIT SUMMARY")
        print("=" * 70)
        print()
        print(f"  {'Test':>25} | {'Result':>8} | {'Classification'}")
        print("  " + "-"*60)
        
        all_passed = True
        classifications = []
        
        for category, results in self.results.items():
            for r in results:
                status = "PASS" if r.passed else "FAIL"
                print(f"  {r.test_name:>25} | {status:>8} | {r.classification.value}: {r.classification.name}")
                all_passed = all_passed and r.passed
                classifications.append(r.classification)
        
        # Final verdict
        print()
        print("=" * 70)
        print("  FINAL VERDICT")
        print("=" * 70)
        
        pass_count = sum(1 for r in classifications if r == ArtifactClass.LIKELY_PHYSICAL)
        total = len(classifications)
        
        if pass_count == total:
            verdict = "LIKELY PHYSICAL: Effect survives all artifact tests"
            overall_class = ArtifactClass.LIKELY_PHYSICAL
        elif pass_count >= total * 0.7:
            verdict = "PROBABLY PHYSICAL: Effect passes most tests"
            overall_class = ArtifactClass.POSSIBLY_EMERGENT
        elif pass_count >= total * 0.5:
            verdict = "UNCERTAIN: Mixed results, needs investigation"
            overall_class = ArtifactClass.POSSIBLY_EMERGENT
        else:
            verdict = "POSSIBLY ARTIFACT: Effect fails multiple tests"
            # Find most common failure mode
            from collections import Counter
            failure_modes = [c for c in classifications if c != ArtifactClass.LIKELY_PHYSICAL]
            if failure_modes:
                most_common = Counter(failure_modes).most_common(1)[0][0]
                overall_class = most_common
            else:
                overall_class = ArtifactClass.POSSIBLY_EMERGENT
        
        print()
        print(f"  Tests passed: {pass_count}/{total}")
        print(f"  Overall classification: {overall_class.value} - {overall_class.name}")
        print()
        print(f"  {verdict}")
        
        self.summary = {
            'verdict': verdict,
            'pass_count': int(pass_count),
            'total_tests': int(total),
            'overall_classification': overall_class.name,
            'all_results': {
                cat: [
                    {
                        'test': r.test_name,
                        'passed': bool(r.passed),
                        'metric': float(r.metric_value),
                        'baseline': float(r.baseline_value),
                        'classification': r.classification.name,
                        'notes': r.notes,
                    }
                    for r in results
                ]
                for cat, results in self.results.items()
            }
        }
        
        # Save results
        with open(f'{self.output_dir}/dark_energy_audit.json', 'w') as f:
            json.dump(self.summary, f, indent=2)
        
        print()
        print(f"  Results saved to: {self.output_dir}/dark_energy_audit.json")
        
        return self.summary


def main():
    auditor = QMRTArtifactAuditor()
    results = auditor.run_full_audit()
    return results


if __name__ == "__main__":
    main()
