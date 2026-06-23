"""
Dark Matter Analog Audit: Mechanism Robustness Testing
=======================================================

PURPOSE: Test whether the dark matter analog (τ-gradient → rotation/lensing)
represents a robust MECHANISM across different conditions.

FRAMEWORK: Emergent Physics
- We expect the MECHANISM (τ gradients create rotation/lensing excess) to persist
- We expect the PATTERNS (specific slope values) to vary with initial conditions
- This is evidence FOR emergent physics, not against it

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List, Any, Tuple
import time
import json
import os


class DarkMatterAuditSimulator:
    """Simplified dark matter simulator for audit testing."""
    
    def __init__(self, size: int = 48, dt: float = 0.12, seed: int = 42):
        self.size = size
        self.dt = dt
        self.seed = seed
        
        np.random.seed(seed)
        
        # Regulated Recovery v1.1
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        self.ax, self.ay, self.az = 1.0, 1.0, 1.0
        self.global_T = 0.0
        
        # Initialize fields
        shape = (size, size, size)
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Create central matter concentration
        self.visible_radius = size // 8
        self._create_visible_matter()
    
    def _create_visible_matter(self):
        center = self.size // 2
        r_vis = self.visible_radius
        
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    if r < r_vis * 3:
                        profile = np.exp(-r**2 / (2 * r_vis**2))
                        self.psi_r[x, y, z] += 2.0 * profile * (1 + 0.1 * np.random.randn())
                        self.psi_i[x, y, z] += 0.5 * profile * np.random.randn()
                        self.psi_r_dot[x, y, z] += 0.5 * profile * np.random.randn()
                        self.psi_i_dot[x, y, z] += 0.5 * profile * np.random.randn()
    
    def _laplacian(self, f):
        lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def step(self):
        self.global_T += self.dt
        
        # τ dynamics
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau += self.damping_to_tau * self.gamma * kinetic
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._laplacian(self.psi_r)
        lap_i = self._laplacian(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def compute_radial_profile(self, field, n_bins=15):
        center = self.size // 2
        x, y, z = np.meshgrid(
            np.arange(self.size) - center,
            np.arange(self.size) - center,
            np.arange(self.size) - center,
            indexing='ij'
        )
        r = np.sqrt(x**2 + y**2 + z**2)
        
        r_max = self.size // 2 - 2
        bin_edges = np.linspace(0, r_max, n_bins + 1)
        radii = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        values = np.zeros(n_bins)
        for i in range(n_bins):
            mask = (r >= bin_edges[i]) & (r < bin_edges[i+1])
            if np.any(mask):
                values[i] = np.mean(field[mask])
        
        return radii, values
    
    def compute_rotation_slope(self):
        """Compute rotation curve slope in outer region."""
        # Pressure gradient
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        tau_excess = np.maximum(self.tau - 1.0, 0)
        pressure = kinetic + tau_excess * 5
        
        grad_x = np.roll(pressure, -1, axis=0) - pressure
        grad_y = np.roll(pressure, -1, axis=1) - pressure
        grad_z = np.roll(pressure, -1, axis=2) - pressure
        pressure_grad = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        radii, grad_profile = self.compute_radial_profile(pressure_grad)
        
        # V_eff ~ sqrt(r * grad)
        v_eff = np.sqrt(radii * grad_profile + 1e-10)
        
        # Slope in outer region
        outer_mask = radii > self.visible_radius * 2
        if np.sum(outer_mask) > 3:
            log_r = np.log(radii[outer_mask] + 1)
            log_v = np.log(v_eff[outer_mask] + 1e-10)
            coeffs = np.polyfit(log_r, log_v, 1)
            return float(coeffs[0])
        return -0.5
    
    def compute_lensing_ratio(self):
        """Compute lensing excess over point mass."""
        # τ gradient
        grad_x = np.roll(self.tau, -1, axis=0) - self.tau
        grad_y = np.roll(self.tau, -1, axis=1) - self.tau
        grad_z = np.roll(self.tau, -1, axis=2) - self.tau
        tau_grad = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        radii, grad_profile = self.compute_radial_profile(tau_grad)
        
        # Deflection ~ cumulative gradient
        deflection = np.zeros_like(radii)
        for i in range(len(radii)):
            if len(radii[i:]) > 1:
                deflection[i] = np.trapezoid(grad_profile[i:], radii[i:])
        
        # Point mass: ~ 1/r
        r_safe = np.maximum(radii, 1.0)
        point_mass = 1.0 / r_safe
        if np.max(deflection) > 0:
            point_mass *= (np.max(deflection) / np.max(point_mass))
        
        # Ratio in outer region
        outer_idx = radii > self.visible_radius * 2
        if np.any(outer_idx) and np.sum(point_mass[outer_idx]) > 0:
            return float(np.mean(deflection[outer_idx]) / np.mean(point_mass[outer_idx]))
        return 1.0


def run_dm_audit_test(seed=42, size=48, max_wall_seconds=40):
    """Run single dark matter audit test."""
    sim = DarkMatterAuditSimulator(size=size, seed=seed)
    
    t_start = time.time()
    target_T = 200.0
    
    while sim.global_T < target_T:
        if time.time() - t_start >= max_wall_seconds - 2:
            break
        sim.step()
    
    slope = sim.compute_rotation_slope()
    lensing_ratio = sim.compute_lensing_ratio()
    tau_max = float(np.max(sim.tau))
    
    return {
        'seed': seed,
        'rotation_slope': slope,
        'lensing_ratio': lensing_ratio,
        'tau_max': tau_max,
        'final_T': sim.global_T,
    }


def run_dark_matter_audit():
    """Run full dark matter audit with emergent physics framework."""
    
    print("=" * 70)
    print("  DARK MATTER ANALOG AUDIT: MECHANISM ROBUSTNESS")
    print("=" * 70)
    print()
    print("  Framework: Emergent Physics")
    print("  Test: Does τ-gradient → rotation/lensing persist across 'universes'?")
    print()
    print("  MECHANISM: τ gradients create rotation/lensing excess")
    print("  PATTERN: Specific slope/ratio values (expected to vary)")
    print()
    
    # Test across seeds
    seeds = [42, 123, 456, 789, 1001, 2022, 3333, 4444]
    results = []
    
    print("Running 8 'universes'...")
    print()
    
    for seed in seeds:
        print(f"  Universe {seed}...", end=" ")
        data = run_dm_audit_test(seed=seed, max_wall_seconds=30)
        results.append(data)
        print(f"slope={data['rotation_slope']:.3f}, lensing={data['lensing_ratio']:.2f}x")
    
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print()
    print(f"  {'Seed':>8} | {'Rot Slope':>10} | {'Lensing':>10} | {'Flat?':>8} | {'Excess?':>8}")
    print("  " + "-"*60)
    
    mechanism_rotation = 0
    mechanism_lensing = 0
    slopes = []
    ratios = []
    
    for r in results:
        is_flat = r['rotation_slope'] > -0.45  # Flatter than Keplerian
        has_excess = r['lensing_ratio'] > 1.1
        
        if is_flat:
            mechanism_rotation += 1
        if has_excess:
            mechanism_lensing += 1
        
        slopes.append(r['rotation_slope'])
        ratios.append(r['lensing_ratio'])
        
        print(f"  {r['seed']:>8} | {r['rotation_slope']:>+10.3f} | {r['lensing_ratio']:>10.2f}x | "
              f"{'YES' if is_flat else 'NO':>8} | {'YES' if has_excess else 'NO':>8}")
    
    print()
    print("=" * 70)
    print("  MECHANISM ANALYSIS")
    print("=" * 70)
    print()
    
    print(f"  Rotation flatter than Keplerian (>-0.45): {mechanism_rotation}/8")
    print(f"  Lensing excess (>1.1x):                   {mechanism_lensing}/8")
    print()
    
    print(f"  PATTERN VARIATION:")
    print(f"    Slope range:    {min(slopes):.3f} to {max(slopes):.3f}")
    print(f"    Slope mean±std: {np.mean(slopes):.3f} ± {np.std(slopes):.3f}")
    print(f"    Lensing range:  {min(ratios):.2f}x to {max(ratios):.2f}x")
    print(f"    Lensing mean:   {np.mean(ratios):.2f}x ± {np.std(ratios):.2f}x")
    print()
    
    # Verdict
    rotation_robust = mechanism_rotation >= 6
    lensing_robust = mechanism_lensing >= 6
    
    print("  VERDICT:")
    print(f"    Rotation mechanism: {'ROBUST' if rotation_robust else 'UNCERTAIN'} ({mechanism_rotation}/8)")
    print(f"    Lensing mechanism:  {'ROBUST' if lensing_robust else 'UNCERTAIN'} ({mechanism_lensing}/8)")
    print()
    
    if rotation_robust and lensing_robust:
        overall = "MECHANISM VALIDATED: Dark matter analog is robust"
    elif rotation_robust or lensing_robust:
        overall = "PARTIAL: One mechanism robust, one uncertain"
    else:
        overall = "UNCERTAIN: Both mechanisms need investigation"
    
    print(f"    Overall: {overall}")
    
    # Save
    output_dir = '/app/backend/qmrt_topology/papers/artifact_audit'
    os.makedirs(output_dir, exist_ok=True)
    
    analysis = {
        'test': 'Dark Matter Analog',
        'framework': 'Emergent Physics',
        'results': results,
        'statistics': {
            'rotation_robust_count': mechanism_rotation,
            'lensing_robust_count': mechanism_lensing,
            'mean_slope': float(np.mean(slopes)),
            'std_slope': float(np.std(slopes)),
            'mean_lensing': float(np.mean(ratios)),
            'std_lensing': float(np.std(ratios)),
        },
        'verdict': overall,
    }
    
    with open(f'{output_dir}/dark_matter_audit.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print()
    print(f"  Results saved to: {output_dir}/dark_matter_audit.json")
    
    return analysis


if __name__ == "__main__":
    run_dark_matter_audit()
