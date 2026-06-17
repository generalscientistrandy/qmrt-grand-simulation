"""
QMRT Artifact Audit - Using Original Test Configuration
=========================================================

This audit uses the EXACT same code as the original expansion_dof_test.py
to ensure we're testing the actual claimed effect, not a simplified version.

Key insight from initial audit: The effect is parameter-sensitive.
This audit tests whether the TUNED effect survives robustness checks.

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List, Any
import time
import json
import os


class ExpansionDOFSimulatorForAudit:
    """
    EXACT COPY of the original ExpansionDOFSimulator from expansion_dof_test.py
    with added configurability for audit purposes.
    """
    
    def __init__(self, 
                 size: int = 32, 
                 dt: float = 0.12, 
                 seed: int = 42,
                 unlocking_enabled: bool = True,
                 unlock_threshold: float = 0.025,
                 unlock_rate: float = 0.03,
                 # Audit parameters
                 integrator: str = 'euler',
                 boundary: str = 'periodic'):
        
        self.size = size
        self.dt = dt
        self.seed = seed
        self.unlocking_enabled = unlocking_enabled
        self.unlock_threshold = unlock_threshold
        self.unlock_rate = unlock_rate
        self.integrator = integrator
        self.boundary = boundary
        
        np.random.seed(seed)
        
        # Regulated Recovery v1.1 (LOCKED)
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Dimensional activation
        self.ax = 1.0
        self.ay = 0.0
        self.az = 0.0
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Unlock events
        self.y_unlock_T = None
        self.z_unlock_T = None
        
        # Fields
        shape = (size, size, size)
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        
        # ORIGINAL initial perturbation (moderate)
        center = size // 2
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    if r < 4:
                        amp = 0.8 * np.exp(-r**2 / 6)
                        self.psi_r[x, y, z] += amp * np.random.randn()
                        self.psi_i[x, y, z] += amp * np.random.randn()
        
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # ORIGINAL initial velocity
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    if r < 3:
                        vel_amp = 0.3 * np.exp(-r**2 / 4)
                        self.psi_r_dot[x, y, z] += vel_amp * np.random.randn()
                        self.psi_i_dot[x, y, z] += vel_amp * np.random.randn()
        
        # Tracking
        self.total_creations = 0
        self.metrics_history = []
        self.expansion_radii = []
        self.initial_energy = self._compute_energy()
    
    def _compute_energy(self):
        """Total system energy."""
        kinetic = 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        potential = self.psi_r**2 + self.psi_i**2
        tau_energy = (self.tau - 1.0)**2
        return float(np.sum(kinetic + potential + tau_energy))
    
    def _laplacian(self, f):
        """3D Laplacian with configurable boundary."""
        if self.boundary == 'periodic':
            lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
            lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
            lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        elif self.boundary == 'reflecting':
            lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
            lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
            lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
            # Zero gradient at boundaries
            lap[0, :, :] = lap[1, :, :]
            lap[-1, :, :] = lap[-2, :, :]
            lap[:, 0, :] = lap[:, 1, :]
            lap[:, -1, :] = lap[:, -2, :]
            lap[:, :, 0] = lap[:, :, 1]
            lap[:, :, -1] = lap[:, :, -2]
        else:
            lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
            lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
            lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def compute_pressure(self) -> float:
        """ORIGINAL pressure calculation."""
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        tau_excess = np.maximum(self.tau - 1.0, 0)
        return float(np.mean(kinetic) + np.mean(tau_excess) * 5)
    
    def check_unlock(self, pressure: float):
        """ORIGINAL unlock logic."""
        if not self.unlocking_enabled:
            return
        
        if self.ay < 1.0 and pressure > self.unlock_threshold:
            self.ay = min(1.0, self.ay + self.unlock_rate)
            if self.y_unlock_T is None and self.ay > 0.01:
                self.y_unlock_T = self.global_T
        
        if self.ay > 0.5 and self.az < 1.0 and pressure > self.unlock_threshold * 1.2:
            self.az = min(1.0, self.az + self.unlock_rate)
            if self.z_unlock_T is None and self.az > 0.01:
                self.z_unlock_T = self.global_T
    
    def compute_expansion_radius(self) -> float:
        """ORIGINAL expansion radius calculation."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        threshold = np.percentile(amp, 80)
        active = amp > threshold
        
        if not np.any(active):
            return 1.0
        
        coords = np.array(np.where(active)).T
        centroid = np.mean(coords, axis=0)
        distances = np.sqrt(np.sum((coords - centroid)**2, axis=1))
        
        return float(np.percentile(distances, 90))
    
    def compute_d_eff(self) -> float:
        """ORIGINAL D_eff calculation."""
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
            return self.ax + self.ay * 0.5 + self.az * 0.5
        
        coords = np.array(np.where(active_mask)).T
        weights = topology[active_mask] / np.sum(topology[active_mask])
        
        centroid = np.average(coords, axis=0, weights=weights)
        centered = coords - centroid
        
        cov = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                cov[i, j] = np.sum(weights * centered[:, i] * centered[:, j])
        
        eigenvalues = np.sort(np.linalg.eigvalsh(cov))[::-1]
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        
        sum_l = sum(eigenvalues)
        sum_l_sq = sum(e**2 for e in eigenvalues)
        
        return sum_l**2 / sum_l_sq if sum_l_sq > 0 else 1.0
    
    def step(self):
        """Advance one timestep with configurable integrator."""
        self.step_count += 1
        self.global_T += self.dt
        
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
            create_mask = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask):
                coords = np.array(np.where(high_tau_mask)).T[create_mask]
                for coord in coords[:3]:
                    self._inject_perturbation(*coord)
                    self.tau[tuple(coord)] = 1.0
                    self.total_creations += 1
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._laplacian(self.psi_r)
        lap_i = self._laplacian(self.psi_i)
        
        if self.integrator == 'euler':
            acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
            acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
            self.psi_r_dot += acc_r * self.dt
            self.psi_i_dot += acc_i * self.dt
            self.psi_r += self.psi_r_dot * self.dt
            self.psi_i += self.psi_i_dot * self.dt
            
        elif self.integrator == 'verlet':
            acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
            acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
            self.psi_r += self.psi_r_dot * self.dt + 0.5 * acc_r * self.dt**2
            self.psi_i += self.psi_i_dot * self.dt + 0.5 * acc_i * self.dt**2
            lap_r_new = self._laplacian(self.psi_r)
            lap_i_new = self._laplacian(self.psi_i)
            acc_r_new = c_eff_sq * lap_r_new - self.gamma * self.psi_r_dot
            acc_i_new = c_eff_sq * lap_i_new - self.gamma * self.psi_i_dot
            self.psi_r_dot += 0.5 * (acc_r + acc_r_new) * self.dt
            self.psi_i_dot += 0.5 * (acc_i + acc_i_new) * self.dt
            
        elif self.integrator == 'leapfrog':
            acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
            acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
            self.psi_r_dot += 0.5 * self.dt * acc_r
            self.psi_i_dot += 0.5 * self.dt * acc_i
            self.psi_r += self.dt * self.psi_r_dot
            self.psi_i += self.dt * self.psi_i_dot
            lap_r = self._laplacian(self.psi_r)
            lap_i = self._laplacian(self.psi_i)
            acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
            acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
            self.psi_r_dot += 0.5 * self.dt * acc_r
            self.psi_i_dot += 0.5 * self.dt * acc_i
            
        else:  # default euler
            acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
            acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
            self.psi_r_dot += acc_r * self.dt
            self.psi_i_dot += acc_i * self.dt
            self.psi_r += self.psi_r_dot * self.dt
            self.psi_i += self.psi_i_dot * self.dt
    
    def _inject_perturbation(self, cx, cy, cz):
        """Inject small perturbation."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), indexing='ij'
        )
        r_sq = (x-cx)**2 + (y-cy)**2 + (z-cz)**2
        perturbation = np.exp(-r_sq / 8)
        phase = np.random.uniform(0, 2*np.pi)
        
        self.psi_r += 0.1 * perturbation * np.cos(phase)
        self.psi_i += 0.1 * perturbation * np.sin(phase)


def run_audit_test(
    size: int = 32,
    dt: float = 0.12,
    seed: int = 42,
    unlocking_enabled: bool = True,
    integrator: str = 'euler',
    boundary: str = 'periodic',
    target_T: float = 500.0,
    max_wall_seconds: float = 45.0,
) -> Dict[str, Any]:
    """Run single audit test with ORIGINAL configuration."""
    
    sim = ExpansionDOFSimulatorForAudit(
        size=size, dt=dt, seed=seed,
        unlocking_enabled=unlocking_enabled,
        unlock_threshold=0.025, unlock_rate=0.03,
        integrator=integrator, boundary=boundary
    )
    
    t_start = time.time()
    measure_interval = 20.0
    last_measure = 0.0
    
    prev_radius = 0.0
    prev_T = 0.0
    velocities = []
    
    while sim.global_T < target_T:
        if time.time() - t_start >= max_wall_seconds - 2:
            break
        
        sim.step()
        
        pressure = sim.compute_pressure()
        sim.check_unlock(pressure)
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            
            radius = sim.compute_expansion_radius()
            d_eff = sim.compute_d_eff()
            
            if prev_T > 0:
                dR_dT = (radius - prev_radius) / (sim.global_T - prev_T)
                velocities.append(dR_dT)
            
            prev_radius = radius
            prev_T = sim.global_T
    
    # Compute metrics
    y_unlock = sim.y_unlock_T
    
    if y_unlock and len(velocities) > 4:
        unlock_idx = int(y_unlock / measure_interval)
        pre_vels = velocities[:max(1, unlock_idx)]
        post_vels = velocities[unlock_idx:] if unlock_idx < len(velocities) else velocities[-2:]
        
        pre_vel = np.mean([v for v in pre_vels if v > 0]) if any(v > 0 for v in pre_vels) else 0.001
        post_vel = np.mean([v for v in post_vels if v > 0]) if any(v > 0 for v in post_vels) else 0
        vel_change = (post_vel - pre_vel) / pre_vel * 100 if pre_vel > 0 else 0
    else:
        pre_vel = np.mean(velocities[:len(velocities)//2]) if velocities else 0
        post_vel = np.mean(velocities[len(velocities)//2:]) if velocities else 0
        vel_change = (post_vel - pre_vel) / pre_vel * 100 if pre_vel > 0.001 else 0
    
    final_energy = sim._compute_energy()
    energy_change = (final_energy - sim.initial_energy) / sim.initial_energy * 100
    
    return {
        'final_T': sim.global_T,
        'y_unlock_T': y_unlock,
        'z_unlock_T': sim.z_unlock_T,
        'pre_velocity': float(pre_vel),
        'post_velocity': float(post_vel),
        'velocity_change_pct': float(vel_change),
        'final_d_eff': sim.compute_d_eff(),
        'ax': sim.ax, 'ay': sim.ay, 'az': sim.az,
        'energy_change_pct': float(energy_change),
    }


def run_proper_audit():
    """Run artifact audit with ORIGINAL test configuration."""
    
    print("=" * 70)
    print("  QMRT ARTIFACT AUDIT - ORIGINAL CONFIGURATION")
    print("=" * 70)
    print()
    print("  Using EXACT same code as expansion_dof_test.py")
    print()
    
    results = {}
    
    # Test 1: Baseline - reproduce original result
    print("=" * 70)
    print("  TEST 1: REPRODUCE ORIGINAL RESULT")
    print("=" * 70)
    
    print("  Running: Unlock ENABLED")
    enabled = run_audit_test(unlocking_enabled=True)
    print("  Running: Unlock DISABLED")
    disabled = run_audit_test(unlocking_enabled=False)
    
    print()
    print(f"  {'Config':>15} | {'Y Unlock':>10} | {'Vel Δ':>12} | {'D_eff':>8}")
    print("  " + "-"*55)
    print(f"  {'Enabled':>15} | {enabled['y_unlock_T'] or 'Never':>10} | {enabled['velocity_change_pct']:>+12.1f}% | {enabled['final_d_eff']:>8.2f}")
    print(f"  {'Disabled':>15} | {disabled['y_unlock_T'] or 'Never':>10} | {disabled['velocity_change_pct']:>+12.1f}% | {disabled['final_d_eff']:>8.2f}")
    
    # Check if we reproduce the original effect
    original_reproduced = enabled['velocity_change_pct'] > 100 and enabled['y_unlock_T'] is not None
    print()
    print(f"  Original effect reproduced: {'YES' if original_reproduced else 'NO'}")
    
    results['baseline'] = {
        'enabled': enabled,
        'disabled': disabled,
        'reproduced': original_reproduced,
    }
    
    if not original_reproduced:
        print()
        print("  WARNING: Cannot reproduce original effect!")
        print("  This may indicate parameter sensitivity.")
        print("  Checking with longer runtime...")
        
        enabled_long = run_audit_test(unlocking_enabled=True, max_wall_seconds=60)
        print(f"  Longer run: Y_unlock={enabled_long['y_unlock_T']}, Vel Δ={enabled_long['velocity_change_pct']:.1f}%")
        results['baseline']['enabled_long'] = enabled_long
    
    # Test 2: Integrator comparison
    print()
    print("=" * 70)
    print("  TEST 2: INTEGRATOR COMPARISON")
    print("=" * 70)
    
    integrators = ['euler', 'verlet', 'leapfrog']
    int_results = {}
    
    for integ in integrators:
        print(f"  Running: {integ}")
        int_results[integ] = run_audit_test(integrator=integ)
    
    print()
    print(f"  {'Integrator':>12} | {'Y Unlock':>10} | {'Vel Δ':>12} | {'D_eff':>8}")
    print("  " + "-"*50)
    for integ, data in int_results.items():
        unlock_str = f"{data['y_unlock_T']:.1f}" if data['y_unlock_T'] else "Never"
        print(f"  {integ:>12} | {unlock_str:>10} | {data['velocity_change_pct']:>+12.1f}% | {data['final_d_eff']:>8.2f}")
    
    # Check consistency
    unlocks = [data['y_unlock_T'] is not None for data in int_results.values()]
    all_unlock = all(unlocks)
    vel_changes = [data['velocity_change_pct'] for data in int_results.values() if data['y_unlock_T']]
    
    results['integrator'] = {
        'results': int_results,
        'all_unlock': all_unlock,
        'consistent': np.std(vel_changes) < np.mean(vel_changes) * 0.5 if vel_changes else False,
    }
    
    print()
    print(f"  All integrators show unlock: {all_unlock}")
    
    # Test 3: Seed sweep
    print()
    print("=" * 70)
    print("  TEST 3: SEED SWEEP")
    print("=" * 70)
    
    seeds = [42, 123, 456, 789, 1001]
    seed_results = {}
    
    for seed in seeds:
        print(f"  Running: seed={seed}")
        seed_results[seed] = run_audit_test(seed=seed, max_wall_seconds=35)
    
    print()
    print(f"  {'Seed':>8} | {'Y Unlock':>10} | {'Vel Δ':>12} | {'D_eff':>8}")
    print("  " + "-"*45)
    for seed, data in seed_results.items():
        unlock_str = f"{data['y_unlock_T']:.1f}" if data['y_unlock_T'] else "Never"
        print(f"  {seed:>8} | {unlock_str:>10} | {data['velocity_change_pct']:>+12.1f}% | {data['final_d_eff']:>8.2f}")
    
    unlock_count = sum(1 for data in seed_results.values() if data['y_unlock_T'] is not None)
    
    results['seed_sweep'] = {
        'results': seed_results,
        'unlock_count': unlock_count,
        'total': len(seeds),
    }
    
    print()
    print(f"  Seeds showing unlock: {unlock_count}/{len(seeds)}")
    
    # Test 4: Resolution
    print()
    print("=" * 70)
    print("  TEST 4: RESOLUTION SCALING")
    print("=" * 70)
    
    resolutions = [24, 32, 40]
    res_results = {}
    
    for res in resolutions:
        print(f"  Running: {res}³")
        wall_time = 30 if res <= 32 else 40
        res_results[res] = run_audit_test(size=res, max_wall_seconds=wall_time)
    
    print()
    print(f"  {'Resolution':>12} | {'Y Unlock':>10} | {'Vel Δ':>12}")
    print("  " + "-"*40)
    for res, data in res_results.items():
        unlock_str = f"{data['y_unlock_T']:.1f}" if data['y_unlock_T'] else "Never"
        print(f"  {res:>12} | {unlock_str:>10} | {data['velocity_change_pct']:>+12.1f}%")
    
    results['resolution'] = res_results
    
    # Final Summary
    print()
    print("=" * 70)
    print("  AUDIT SUMMARY")
    print("=" * 70)
    
    # Compile verdicts
    baseline_pass = results['baseline']['reproduced'] or results['baseline'].get('enabled_long', {}).get('y_unlock_T') is not None
    integrator_pass = results['integrator']['all_unlock']
    seed_pass = results['seed_sweep']['unlock_count'] >= 3
    
    print()
    print(f"  Baseline effect reproduced:  {'PASS' if baseline_pass else 'FAIL'}")
    print(f"  Integrator-independent:      {'PASS' if integrator_pass else 'FAIL'}")
    print(f"  Seed-robust ({results['seed_sweep']['unlock_count']}/5): {'PASS' if seed_pass else 'FAIL'}")
    
    total_pass = sum([baseline_pass, integrator_pass, seed_pass])
    
    print()
    print(f"  Overall: {total_pass}/3 tests passed")
    
    if total_pass == 3:
        verdict = "LIKELY PHYSICAL: Effect passes key robustness tests"
    elif total_pass >= 2:
        verdict = "PROBABLY PHYSICAL: Effect passes most tests"
    else:
        verdict = "PARAMETER-SENSITIVE: Effect depends on specific conditions"
    
    print()
    print(f"  VERDICT: {verdict}")
    
    results['verdict'] = verdict
    results['pass_count'] = total_pass
    
    # Save
    output_dir = '/app/backend/qmrt_topology/papers/artifact_audit'
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert for JSON
    def convert(obj):
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        else:
            return obj
    
    with open(f'{output_dir}/proper_audit_results.json', 'w') as f:
        json.dump(convert(results), f, indent=2)
    
    print()
    print(f"  Results saved to: {output_dir}/proper_audit_results.json")
    
    return results


if __name__ == "__main__":
    run_proper_audit()
