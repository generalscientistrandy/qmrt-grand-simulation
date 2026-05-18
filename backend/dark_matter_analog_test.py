"""
QMRT Dark-Matter Analog Test
==============================

PURPOSE: Test whether the regulated QMRT medium can reproduce dark-matter-like
observational signatures through τ-gradient and pressure-flow structure, 
WITHOUT requiring invisible particles.

HYPOTHESIS:
  Dark matter effects (flat rotation curves, gravitational lensing excess)
  arise from structured medium dynamics:
  - Persistent τ gradients around visible matter concentrations
  - Pressure-flow envelopes that extend beyond visible matter
  - These create additional "effective attraction" and refractive lensing

TEST DESIGN:
  1. Create a visible-matter-like disk/cluster in the center
  2. Let the regulated medium respond (τ gradients form, pressure redistributes)
  3. Measure:
     - Orbital velocity vs radius V(r)
     - Lensing deflection vs radius θ(r)
  4. Compare with:
     - Keplerian falloff: V ~ r^(-0.5) from visible matter only
     - Medium-enhanced: Flat or rising V(r) from τ/pressure envelope

PASS CONDITION:
  The medium response produces:
  - V(r) that is FLATTER than Keplerian (not falling as r^-0.5)
  - Lensing deflection that exceeds point-mass expectation
  Without adding any hidden mass particles.

QMRT DARK MATTER STATEMENT:
  "Dark matter is the gravitational and refractive signature of structured
  quark-medium dynamics (persistent τ gradients, pressure-flow envelopes)
  around visible matter concentrations. It is not invisible particles but
  the medium's organized response to matter."

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label, gaussian_filter
from scipy.optimize import curve_fit
from typing import Dict, List, Any, Tuple
import time
import json
import os


class DarkMatterAnalogSimulator:
    """
    Simulator for testing dark-matter-like behavior from medium response.
    
    Creates a central "visible matter" concentration and measures:
    - How the medium responds (τ gradients, pressure)
    - Effective orbital velocity from pressure gradients
    - Lensing from τ gradients
    """
    
    def __init__(self, 
                 size: int = 48,  # Larger grid for better radial resolution
                 dt: float = 0.12, 
                 seed: int = 42):
        """Initialize dark matter analog test."""
        
        self.size = size
        self.dt = dt
        self.seed = seed
        
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
        
        # All dimensions active (3D)
        self.ax = 1.0
        self.ay = 1.0
        self.az = 1.0
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Initialize fields
        shape = (size, size, size)
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Create central "visible matter" concentration
        self.visible_mass_radius = size // 8  # Core visible matter radius
        self._create_visible_matter()
        
        # Metrics history
        self.metrics_history = []
        
        print(f"Dark Matter Analog Test initialized")
        print(f"  Grid: {size}³")
        print(f"  Visible matter radius: {self.visible_mass_radius}")
    
    def _create_visible_matter(self):
        """
        Create a central concentration of "visible matter" - 
        localized energy/activity that will source τ gradients.
        """
        center = self.size // 2
        r_vis = self.visible_mass_radius
        
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    
                    # Exponential profile for visible matter
                    if r < r_vis * 3:
                        # Higher amplitude in center -> sources τ gradients
                        profile = np.exp(-r**2 / (2 * r_vis**2))
                        self.psi_r[x, y, z] += 2.0 * profile * (1 + 0.1 * np.random.randn())
                        self.psi_i[x, y, z] += 0.5 * profile * np.random.randn()
                        
                        # Initial velocity to create dynamics
                        self.psi_r_dot[x, y, z] += 0.5 * profile * np.random.randn()
                        self.psi_i_dot[x, y, z] += 0.5 * profile * np.random.randn()
    
    def _laplacian(self, f):
        """3D Laplacian."""
        lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def compute_radial_profile(self, field: np.ndarray, 
                               n_bins: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute radially averaged profile of a field.
        
        Returns:
            radii: Bin centers
            values: Mean field value in each radial bin
        """
        center = self.size // 2
        
        # Create radial distance array
        x, y, z = np.meshgrid(
            np.arange(self.size) - center,
            np.arange(self.size) - center,
            np.arange(self.size) - center,
            indexing='ij'
        )
        r = np.sqrt(x**2 + y**2 + z**2)
        
        # Bin edges
        r_max = self.size // 2 - 2
        bin_edges = np.linspace(0, r_max, n_bins + 1)
        radii = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Compute mean in each bin
        values = np.zeros(n_bins)
        for i in range(n_bins):
            mask = (r >= bin_edges[i]) & (r < bin_edges[i+1])
            if np.any(mask):
                values[i] = np.mean(field[mask])
        
        return radii, values
    
    def compute_pressure_gradient(self) -> np.ndarray:
        """
        Compute pressure gradient magnitude.
        Pressure = kinetic energy + τ excess.
        """
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        tau_excess = np.maximum(self.tau - 1.0, 0)
        pressure = kinetic + tau_excess * 5
        
        # Gradient
        grad_x = np.roll(pressure, -1, axis=0) - pressure
        grad_y = np.roll(pressure, -1, axis=1) - pressure
        grad_z = np.roll(pressure, -1, axis=2) - pressure
        
        return np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
    
    def compute_tau_gradient(self) -> np.ndarray:
        """Compute τ gradient magnitude."""
        grad_x = np.roll(self.tau, -1, axis=0) - self.tau
        grad_y = np.roll(self.tau, -1, axis=1) - self.tau
        grad_z = np.roll(self.tau, -1, axis=2) - self.tau
        
        return np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
    
    def compute_effective_velocity(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute effective orbital velocity from pressure gradients.
        
        In a system with radial pressure gradient dP/dr, 
        circular orbit velocity satisfies: v² = r * |dP/dr| / ρ
        
        We compute V(r) = sqrt(r * |∇P|) as a proxy.
        """
        pressure_grad = self.compute_pressure_gradient()
        
        # Radial profile of pressure gradient
        radii, grad_profile = self.compute_radial_profile(pressure_grad)
        
        # Effective velocity: V ~ sqrt(r * grad)
        # Add small epsilon to avoid sqrt of zero
        v_eff = np.sqrt(radii * grad_profile + 1e-10)
        
        return radii, v_eff
    
    def compute_keplerian_velocity(self, radii: np.ndarray) -> np.ndarray:
        """
        Compute Keplerian velocity profile for point mass at center.
        V_kep(r) ~ r^(-0.5)
        
        Normalized to match the inner regions of the observed profile.
        """
        # Avoid division by zero
        r_safe = np.maximum(radii, 1.0)
        
        # V ~ r^(-0.5)
        v_kep = 1.0 / np.sqrt(r_safe)
        
        return v_kep
    
    def compute_lensing_deflection(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute effective lensing deflection from τ gradients.
        
        In QMRT, τ gradients bend wave propagation (refractive index effect).
        Deflection angle θ ~ ∫ ∇τ dr along path
        
        We compute radial profile of cumulative τ gradient as proxy.
        """
        tau_grad = self.compute_tau_gradient()
        
        # Radial profile of τ gradient
        radii, grad_profile = self.compute_radial_profile(tau_grad)
        
        # Cumulative deflection (integral from r to ∞)
        # θ(r) ~ ∫_r^∞ |∇τ| dr
        deflection = np.zeros_like(radii)
        for i in range(len(radii)):
            if len(radii[i:]) > 1:
                deflection[i] = np.trapezoid(grad_profile[i:], radii[i:])
            else:
                deflection[i] = 0.0
        
        return radii, deflection
    
    def compute_enclosed_effective_mass(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute enclosed "effective mass" from τ and pressure structure.
        
        This is the mass a Keplerian observer would infer to explain V(r).
        M_eff(r) = V(r)² * r
        """
        radii, v_eff = self.compute_effective_velocity()
        
        m_eff = v_eff**2 * radii
        
        return radii, m_eff
    
    def step(self):
        """Advance simulation one timestep."""
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


def run_dark_matter_test(
    target_T: float = 300.0,
    max_wall_seconds: float = 80.0,
    size: int = 48,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run dark matter analog test.
    
    Measures rotation curve and lensing profile at multiple time points
    to see how the medium response develops.
    """
    
    print("=" * 70)
    print("  QMRT DARK-MATTER ANALOG TEST")
    print("=" * 70)
    print()
    print("HYPOTHESIS: Dark matter effects arise from medium τ-gradient and")
    print("            pressure-flow structure, not invisible particles.")
    print()
    print("TEST: Create visible matter concentration, let medium respond,")
    print("      measure V(r) and lensing deflection θ(r)")
    print()
    print("PASS CONDITION: V(r) flatter than Keplerian, lensing exceeds point-mass")
    print()
    
    sim = DarkMatterAnalogSimulator(size=size, dt=0.12, seed=seed)
    
    t_start = time.time()
    measure_interval = 30.0
    last_measure = 0.0
    
    results = {
        'snapshots': [],
        'final_profiles': {},
    }
    
    print(f"{'T':>6} | {'τ_max':>6} | {'τ_center':>8} | {'Grad_max':>8} | Status")
    print("-" * 60)
    
    while sim.global_T < target_T:
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - 5:
            print(f"\nWall time limit reached at T={sim.global_T:.1f}")
            break
        
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            
            # Compute metrics
            tau_max = float(np.max(sim.tau))
            center = size // 2
            tau_center = float(sim.tau[center, center, center])
            tau_grad = sim.compute_tau_gradient()
            grad_max = float(np.max(tau_grad))
            
            # Compute profiles
            radii, v_eff = sim.compute_effective_velocity()
            _, deflection = sim.compute_lensing_deflection()
            _, tau_profile = sim.compute_radial_profile(sim.tau)
            _, pressure_grad_profile = sim.compute_radial_profile(sim.compute_pressure_gradient())
            
            print(f"{sim.global_T:>6.1f} | {tau_max:>6.3f} | {tau_center:>8.4f} | {grad_max:>8.5f} | Measuring")
            
            # Store snapshot
            results['snapshots'].append({
                'T': sim.global_T,
                'tau_max': tau_max,
                'tau_center': tau_center,
                'grad_max': grad_max,
                'radii': radii.tolist(),
                'v_eff': v_eff.tolist(),
                'deflection': deflection.tolist(),
                'tau_profile': tau_profile.tolist(),
                'pressure_grad_profile': pressure_grad_profile.tolist(),
            })
    
    # Final detailed analysis
    print()
    print("=" * 70)
    print("  FINAL ANALYSIS")
    print("=" * 70)
    
    # Get final profiles
    radii, v_eff = sim.compute_effective_velocity()
    _, deflection = sim.compute_lensing_deflection()
    _, m_eff = sim.compute_enclosed_effective_mass()
    v_kep = sim.compute_keplerian_velocity(radii)
    
    # Normalize Keplerian to match inner region
    inner_mask = (radii > 2) & (radii < 8)
    if np.any(inner_mask):
        scale = np.mean(v_eff[inner_mask]) / np.mean(v_kep[inner_mask])
        v_kep_scaled = v_kep * scale
    else:
        v_kep_scaled = v_kep
    
    # Compute rotation curve flatness
    # Keplerian: d(log V)/d(log r) = -0.5
    # Flat: d(log V)/d(log r) = 0
    outer_mask = radii > sim.visible_mass_radius * 2
    if np.sum(outer_mask) > 3:
        log_r = np.log(radii[outer_mask] + 1)
        log_v = np.log(v_eff[outer_mask] + 1e-10)
        
        # Linear fit to get slope
        if len(log_r) > 2:
            coeffs = np.polyfit(log_r, log_v, 1)
            slope = coeffs[0]
        else:
            slope = -0.5
    else:
        slope = -0.5
    
    print()
    print(f"Visible matter radius: {sim.visible_mass_radius}")
    print()
    print("ROTATION CURVE ANALYSIS:")
    print(f"  Keplerian slope: -0.50")
    print(f"  Measured slope:  {slope:.3f}")
    print(f"  Flatness: {'FLATTER than Keplerian' if slope > -0.45 else 'Near Keplerian'}")
    
    # Compute lensing excess
    # Point mass: θ ~ 1/r
    # Medium enhancement: θ > 1/r at large r
    r_safe = np.maximum(radii, 1.0)
    point_mass_deflection = 1.0 / r_safe
    if np.max(deflection) > 0:
        point_mass_deflection *= (np.max(deflection) / np.max(point_mass_deflection))
    
    # Lensing excess at outer radii
    outer_idx = radii > sim.visible_mass_radius * 2
    if np.any(outer_idx) and np.sum(point_mass_deflection[outer_idx]) > 0:
        lensing_ratio = np.mean(deflection[outer_idx]) / np.mean(point_mass_deflection[outer_idx])
    else:
        lensing_ratio = 1.0
    
    print()
    print("LENSING ANALYSIS:")
    print(f"  Outer lensing ratio (observed/point-mass): {lensing_ratio:.2f}")
    print(f"  Lensing excess: {'YES' if lensing_ratio > 1.1 else 'NO'}")
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    rotation_pass = slope > -0.45  # Flatter than Keplerian
    lensing_pass = lensing_ratio > 1.1  # 10% excess
    
    if rotation_pass and lensing_pass:
        verdict = "CONFIRMED: Medium produces dark-matter-like signatures"
    elif rotation_pass:
        verdict = "PARTIAL: Flat rotation but no lensing excess"
    elif lensing_pass:
        verdict = "PARTIAL: Lensing excess but Keplerian rotation"
    else:
        verdict = "NOT CONFIRMED: No clear dark-matter analog"
    
    print()
    print(f"  Rotation curve flatness: {'PASS' if rotation_pass else 'FAIL'}")
    print(f"  Lensing excess:          {'PASS' if lensing_pass else 'FAIL'}")
    print()
    print(f"  {verdict}")
    
    # Store final results
    results['final_profiles'] = {
        'radii': radii.tolist(),
        'v_eff': v_eff.tolist(),
        'v_kep_scaled': v_kep_scaled.tolist(),
        'deflection': deflection.tolist(),
        'point_mass_deflection': point_mass_deflection.tolist(),
        'm_eff': m_eff.tolist(),
    }
    
    results['analysis'] = {
        'rotation_slope': float(slope),
        'keplerian_slope': -0.5,
        'rotation_flatter_than_keplerian': bool(rotation_pass),
        'lensing_ratio': float(lensing_ratio),
        'lensing_excess': bool(lensing_pass),
        'visible_matter_radius': int(sim.visible_mass_radius),
        'verdict': verdict,
    }
    
    # Save results
    output_dir = '/app/backend/qmrt_topology/papers/dark_matter'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/dark_matter_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print(f"Results saved to: {output_dir}/dark_matter_results.json")
    
    return results


def main():
    results = run_dark_matter_test(
        target_T=300.0,
        max_wall_seconds=80.0,
        size=48,
        seed=42,
    )
    return results


if __name__ == "__main__":
    main()
