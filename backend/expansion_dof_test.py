"""
Expansion-DOF Coupling Test
============================

PURPOSE: Test whether expansion speed increases when new degrees of
freedom unlock, supporting the hypothesis that cosmic acceleration
comes from increasing accessible freedom points.

KEY HYPOTHESIS:
  Expansion is the medium's pressure-release process. As topology and
  τ-motion saturate the currently accessible degrees of freedom, the
  substrate opens additional freedom points. This increases the available
  state-space and appears to 3D observers as accelerated cosmic expansion.

PREDICTION:
  Before unlock: expansion slows or pressure builds
  At unlock: D_eff rises
  After unlock: expansion front accelerates because new pathways available

KEY METRIC:
  dR/dT (expansion velocity) before vs after unlock

COMPARISON:
  A: Unlocking ENABLED - pressure releases into new DOF, expansion continues
  B: Unlocking DISABLED - pressure rises, expansion stalls or destabilizes

THEORY STATEMENT:
  "In QMRT, cosmic expansion is not merely the stretching of space; it is
  the activation of additional accessible degrees of freedom in the medium.
  As persistent motion saturates the current dimensional phase, the expansion
  boundary gives way, allowing the medium to distribute energy into a higher
  state. To observers inside the lower-dimensional phase, this appears as
  accelerating expansion."

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List, Any
import time
import json
import os


class ExpansionDOFSimulator:
    """
    Simulator for testing expansion-DOF coupling.
    
    Measures whether expansion velocity increases after dimensional unlock.
    """
    
    def __init__(self, 
                 size: int = 32, 
                 dt: float = 0.12, 
                 seed: int = 42,
                 unlocking_enabled: bool = True,
                 unlock_threshold: float = 1.5,
                 unlock_rate: float = 0.02):
        """
        Initialize with configurable dimensional unlocking.
        
        Parameters:
        -----------
        unlocking_enabled : bool
            If False, dimensions stay locked (control condition)
        """
        
        self.size = size
        self.dt = dt
        self.seed = seed
        self.unlocking_enabled = unlocking_enabled
        self.unlock_threshold = unlock_threshold
        self.unlock_rate = unlock_rate
        
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
        self.ax = 1.0  # X always active
        self.ay = 0.0  # Y starts suppressed
        self.az = 0.0  # Z starts suppressed
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Unlock events
        self.y_unlock_T = None
        self.z_unlock_T = None
        
        # Fields - seed activity at CENTER to measure expansion outward
        shape = (size, size, size)
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        
        # Concentrated initial perturbation at center
        center = size // 2
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    if r < 3:
                        amp = 0.5 * np.exp(-r**2 / 4)
                        self.psi_r[x, y, z] += amp * np.random.randn()
                        self.psi_i[x, y, z] += amp * np.random.randn()
        
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Expansion tracking
        self.total_creations = 0
        self.metrics_history = []
        self.expansion_radii = []  # Track expansion front over time
        
        mode = "ENABLED" if unlocking_enabled else "DISABLED"
        print(f"Expansion-DOF Test initialized")
        print(f"  Unlocking: {mode}")
        print(f"  Grid: {size}³")
    
    def _weighted_laplacian(self, f):
        """Laplacian weighted by dimensional activation."""
        lap = self.ax * (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += self.ay * (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += self.az * (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def compute_expansion_radius(self) -> float:
        """
        Compute the expansion front radius.
        
        Measures how far activity has spread from the center.
        """
        # Activity field
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        activity = amp + kinetic * 10
        
        # Threshold for "active" region
        threshold = np.mean(activity) + 0.5 * np.std(activity)
        active_mask = activity > threshold
        
        if not np.any(active_mask):
            return 0.0
        
        # Find farthest active point from center
        center = self.size // 2
        active_coords = np.array(np.where(active_mask)).T
        
        distances = np.sqrt(np.sum((active_coords - center)**2, axis=1))
        
        # Use 90th percentile as "front" to avoid outliers
        radius = np.percentile(distances, 90)
        
        return float(radius)
    
    def compute_pressure(self) -> float:
        """Compute total pressure metric."""
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        tau_excess = np.maximum(self.tau - 1.0, 0)
        pressure = np.mean(kinetic) + np.mean(tau_excess) * 5
        return float(pressure)
    
    def compute_d_eff(self) -> float:
        """Compute effective dimensionality."""
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
            return self.ax + self.ay * 0.5 + self.az * 0.5  # Approximate
        
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
    
    def check_unlock(self, pressure: float):
        """Check and apply dimensional unlocking if enabled."""
        if not self.unlocking_enabled:
            return
        
        if self.ay < 1.0 and pressure > self.unlock_threshold:
            self.ay = min(1.0, self.ay + self.unlock_rate)
            if self.y_unlock_T is None and self.ay > 0:
                self.y_unlock_T = self.global_T
                print(f"  *** Y UNLOCKING at T={self.global_T:.1f} (pressure={pressure:.2f})")
        
        if self.ay > 0.5 and self.az < 1.0 and pressure > self.unlock_threshold * 1.5:
            self.az = min(1.0, self.az + self.unlock_rate)
            if self.z_unlock_T is None and self.az > 0:
                self.z_unlock_T = self.global_T
                print(f"  *** Z UNLOCKING at T={self.global_T:.1f} (pressure={pressure:.2f})")
    
    def step(self):
        """Advance simulation."""
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
        lap_r = self._weighted_laplacian(self.psi_r)
        lap_i = self._weighted_laplacian(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def _inject_perturbation(self, cx, cy, cz):
        """Inject perturbation."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), indexing='ij'
        )
        r_sq = (x-cx)**2 + (y-cy)**2 + (z-cz)**2
        perturbation = np.exp(-r_sq / 8)
        phase = np.random.uniform(0, 2*np.pi)
        
        self.psi_r += 0.1 * perturbation * np.cos(phase)
        self.psi_i += 0.1 * perturbation * np.sin(phase)


def run_expansion_dof_test(
    target_T: float = 600.0,
    max_wall_seconds: float = 50.0,
    size: int = 32,
    seed: int = 42,
    unlocking_enabled: bool = True,
) -> Dict[str, Any]:
    """Run single expansion-DOF test."""
    
    sim = ExpansionDOFSimulator(
        size=size, dt=0.12, seed=seed,
        unlocking_enabled=unlocking_enabled,
        unlock_threshold=1.5, unlock_rate=0.02
    )
    
    t_start = time.time()
    measure_interval = 15.0
    last_measure = 0.0
    
    print()
    print(f"{'T':>6} | {'Radius':>7} | {'dR/dT':>7} | {'Pressure':>8} | {'D_eff':>6} | DOF")
    print("-" * 60)
    
    prev_radius = 0.0
    prev_T = 0.0
    
    while sim.global_T < target_T:
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - 5:
            break
        
        sim.step()
        
        # Check for unlock
        pressure = sim.compute_pressure()
        sim.check_unlock(pressure)
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            
            radius = sim.compute_expansion_radius()
            d_eff = sim.compute_d_eff()
            
            # Expansion velocity
            dR_dT = (radius - prev_radius) / (sim.global_T - prev_T) if prev_T > 0 else 0
            
            dof = f"{sim.ax:.0f}{sim.ay:.1f}{sim.az:.1f}"
            
            print(f"{sim.global_T:>6.1f} | {radius:>7.2f} | {dR_dT:>7.3f} | "
                  f"{pressure:>8.3f} | {d_eff:>6.2f} | {dof}")
            
            sim.metrics_history.append({
                'T': sim.global_T,
                'radius': radius,
                'dR_dT': dR_dT,
                'pressure': pressure,
                'D_eff': d_eff,
                'ax': sim.ax,
                'ay': sim.ay,
                'az': sim.az,
            })
            sim.expansion_radii.append((sim.global_T, radius))
            
            prev_radius = radius
            prev_T = sim.global_T
    
    return {
        'unlocking_enabled': unlocking_enabled,
        'y_unlock_T': sim.y_unlock_T,
        'z_unlock_T': sim.z_unlock_T,
        'metrics': sim.metrics_history,
        'final_radius': sim.expansion_radii[-1][1] if sim.expansion_radii else 0,
    }


def run_comparison_test(
    max_wall_seconds: float = 100.0,
    size: int = 32,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Compare expansion with unlocking enabled vs disabled.
    """
    print("=" * 70)
    print("  EXPANSION-DOF COUPLING TEST")
    print("=" * 70)
    print()
    print("HYPOTHESIS: Expansion velocity increases after DOF unlock")
    print()
    print("Comparison:")
    print("  A: Unlocking ENABLED - new pathways become available")
    print("  B: Unlocking DISABLED - pressure builds, expansion limited")
    print()
    
    results = {}
    
    # Test A: Unlocking enabled
    print("=" * 60)
    print("  CONDITION A: UNLOCKING ENABLED")
    print("=" * 60)
    results['enabled'] = run_expansion_dof_test(
        target_T=500, max_wall_seconds=max_wall_seconds/2,
        size=size, seed=seed, unlocking_enabled=True
    )
    
    print()
    print("=" * 60)
    print("  CONDITION B: UNLOCKING DISABLED")
    print("=" * 60)
    results['disabled'] = run_expansion_dof_test(
        target_T=500, max_wall_seconds=max_wall_seconds/2,
        size=size, seed=seed, unlocking_enabled=False
    )
    
    # Analysis
    print()
    print("=" * 70)
    print("  ANALYSIS")
    print("=" * 70)
    
    for condition in ['enabled', 'disabled']:
        metrics = results[condition]['metrics']
        if not metrics:
            continue
        
        # Split into pre-unlock and post-unlock phases
        y_unlock = results[condition].get('y_unlock_T')
        
        if y_unlock and condition == 'enabled':
            pre = [m for m in metrics if m['T'] < y_unlock]
            post = [m for m in metrics if m['T'] >= y_unlock]
        else:
            mid = len(metrics) // 2
            pre = metrics[:mid]
            post = metrics[mid:]
        
        if pre and post:
            pre_velocity = np.mean([m['dR_dT'] for m in pre if m['dR_dT'] > 0])
            post_velocity = np.mean([m['dR_dT'] for m in post if m['dR_dT'] > 0])
            pre_pressure = np.mean([m['pressure'] for m in pre])
            post_pressure = np.mean([m['pressure'] for m in post])
            
            print(f"\n{condition.upper()}:")
            print(f"  Pre-unlock:  velocity={pre_velocity:.4f}, pressure={pre_pressure:.3f}")
            print(f"  Post-unlock: velocity={post_velocity:.4f}, pressure={post_pressure:.3f}")
            
            if pre_velocity > 0:
                accel = (post_velocity - pre_velocity) / pre_velocity * 100
                print(f"  Velocity change: {accel:+.1f}%")
            
            results[condition]['pre_velocity'] = pre_velocity
            results[condition]['post_velocity'] = post_velocity
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    enabled_final = results['enabled']['final_radius']
    disabled_final = results['disabled']['final_radius']
    
    enabled_accel = results['enabled'].get('post_velocity', 0) - results['enabled'].get('pre_velocity', 0)
    disabled_accel = results['disabled'].get('post_velocity', 0) - results['disabled'].get('pre_velocity', 0)
    
    print(f"\nFinal expansion radius:")
    print(f"  Enabled:  {enabled_final:.2f}")
    print(f"  Disabled: {disabled_final:.2f}")
    
    print(f"\nVelocity acceleration:")
    print(f"  Enabled:  {enabled_accel:+.4f}")
    print(f"  Disabled: {disabled_accel:+.4f}")
    
    if enabled_accel > disabled_accel and enabled_final > disabled_final:
        verdict = "CONFIRMED: Unlocking increases expansion velocity"
    elif enabled_final > disabled_final:
        verdict = "PARTIAL: Unlocking increases total expansion but not velocity"
    else:
        verdict = "NOT CONFIRMED: No clear expansion-DOF coupling"
    
    print(f"\n{verdict}")
    
    # Save
    output_dir = '/app/backend/qmrt_topology/papers/expansion_dof'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/expansion_comparison.json', 'w') as f:
        json.dump({
            'verdict': verdict,
            'enabled_final_radius': enabled_final,
            'disabled_final_radius': disabled_final,
            'enabled_y_unlock': results['enabled']['y_unlock_T'],
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_dir}/expansion_comparison.json")
    
    return results


def main():
    results = run_comparison_test(
        max_wall_seconds=100.0,
        size=32,
        seed=42,
    )
    return results


if __name__ == "__main__":
    main()
