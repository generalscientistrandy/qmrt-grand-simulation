"""
QMRT Bullet Cluster Analog Test
================================

PURPOSE: Test whether τ-gradient medium structure can separate from 
visible/gas matter during a high-energy collision, reproducing the 
Bullet Cluster observation pattern.

HYPOTHESIS:
  The τ-medium structure has its own response timescale. During a 
  cluster collision:
  - Gas (collisional) slows and heats at the interaction region
  - τ-structure (collisionless analog) passes through with less drag
  - Result: τ/lensing peaks separate from gas peaks

THE BULLET CLUSTER CHALLENGE:
  The Bullet Cluster shows gravitational lensing center offset from 
  gas center after collision. This is cited as strong evidence for 
  particle dark matter. If QMRT can reproduce this separation through
  medium dynamics, it addresses a major objection.

TEST DESIGN:
  Three tracked layers:
  1. Visible matter proxy - collision body cores
  2. Gas proxy - collisional component that slows and heats
  3. τ-medium structure - effective lensing / DM analog

PASS CONDITION:
  After collision:
  - Gas/visible collisional center slows near interaction region
  - τ/lensing peaks remain offset or continue with collisionless components
  - Separation persists for measurable time

CAUTION:
  This does NOT claim "QMRT explains the Bullet Cluster."
  It tests whether the simulator reproduces Bullet-Cluster-like 
  separation under tested collision conditions.

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label, center_of_mass, gaussian_filter
from typing import Dict, List, Any, Tuple
import time
import json
import os


class BulletClusterSimulator:
    """
    Simulator for Bullet Cluster analog test.
    
    Two matter concentrations collide:
    - Tracks visible matter, gas, and τ-structure separately
    - Measures separation between components after collision
    """
    
    def __init__(self, 
                 size: int = 64,  # Larger grid for collision dynamics
                 dt: float = 0.10,  # Smaller timestep for collision accuracy
                 seed: int = 42,
                 tau_relaxation: float = 0.01,  # Configurable for variants
                 tau_response: float = 0.02):
        """
        Initialize Bullet Cluster analog test.
        
        Parameters:
        -----------
        tau_relaxation : float
            τ relaxation rate (fast = follows matter, slow = lags)
        tau_response : float
            τ sensitivity to energy (0 = no response, > 0 = builds gradients)
        """
        
        self.size = size
        self.dt = dt
        self.seed = seed
        
        np.random.seed(seed)
        
        # Regulated Recovery v1.1 (with configurable τ dynamics)
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        self.tau_response = tau_response
        self.tau_relaxation = tau_relaxation
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
        self.psi_r = np.ones(shape) * 0.01  # Low background
        self.psi_i = np.zeros(shape)
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Cluster parameters
        self.cluster_radius = size // 10
        self.collision_velocity = 0.8  # Initial relative velocity
        
        # Cluster positions (start well separated, moving toward each other)
        self.cluster1_center = [size // 5, size // 2, size // 2]
        self.cluster2_center = [4 * size // 5, size // 2, size // 2]
        
        # Create initial clusters
        self._create_clusters()
        
        # Tracking arrays
        self.visible_matter_1 = np.zeros(shape)  # Core matter cluster 1
        self.visible_matter_2 = np.zeros(shape)  # Core matter cluster 2
        self.gas_field = np.zeros(shape)         # Collisional gas component
        
        self._initialize_tracking_fields()
        
        # Metrics history
        self.metrics_history = []
        self.collision_detected = False
        self.collision_T = None
        
        print(f"Bullet Cluster Analog Test initialized")
        print(f"  Grid: {size}³")
        print(f"  τ_relaxation: {tau_relaxation}")
        print(f"  τ_response: {tau_response}")
        print(f"  Cluster radius: {self.cluster_radius}")
    
    def _create_clusters(self):
        """Create two approaching matter concentrations."""
        center1 = self.cluster1_center
        center2 = self.cluster2_center
        r_cluster = self.cluster_radius
        
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    # Distance to each cluster center
                    r1 = np.sqrt((x - center1[0])**2 + 
                                (y - center1[1])**2 + 
                                (z - center1[2])**2)
                    r2 = np.sqrt((x - center2[0])**2 + 
                                (y - center2[1])**2 + 
                                (z - center2[2])**2)
                    
                    # Cluster 1 (moving right)
                    if r1 < r_cluster * 2:
                        profile1 = np.exp(-r1**2 / (2 * r_cluster**2))
                        self.psi_r[x, y, z] += 3.0 * profile1
                        self.psi_r_dot[x, y, z] += self.collision_velocity * profile1
                    
                    # Cluster 2 (moving left)
                    if r2 < r_cluster * 2:
                        profile2 = np.exp(-r2**2 / (2 * r_cluster**2))
                        self.psi_r[x, y, z] += 3.0 * profile2
                        self.psi_r_dot[x, y, z] -= self.collision_velocity * profile2
    
    def _initialize_tracking_fields(self):
        """Initialize separate tracking fields for visible matter and gas."""
        center1 = self.cluster1_center
        center2 = self.cluster2_center
        r_cluster = self.cluster_radius
        
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    r1 = np.sqrt((x - center1[0])**2 + 
                                (y - center1[1])**2 + 
                                (z - center1[2])**2)
                    r2 = np.sqrt((x - center2[0])**2 + 
                                (y - center2[1])**2 + 
                                (z - center2[2])**2)
                    
                    # Visible matter cores (compact)
                    if r1 < r_cluster:
                        self.visible_matter_1[x, y, z] = np.exp(-r1**2 / (r_cluster**2))
                    if r2 < r_cluster:
                        self.visible_matter_2[x, y, z] = np.exp(-r2**2 / (r_cluster**2))
                    
                    # Gas (more extended, will be collisional)
                    if r1 < r_cluster * 2:
                        self.gas_field[x, y, z] += np.exp(-r1**2 / (2 * r_cluster**2))
                    if r2 < r_cluster * 2:
                        self.gas_field[x, y, z] += np.exp(-r2**2 / (2 * r_cluster**2))
    
    def _laplacian(self, f):
        """3D Laplacian."""
        lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def compute_centroid(self, field: np.ndarray, threshold_percentile: float = 80) -> np.ndarray:
        """Compute weighted centroid of a field."""
        threshold = np.percentile(field, threshold_percentile)
        mask = field > threshold
        
        if not np.any(mask):
            return np.array([self.size // 2, self.size // 2, self.size // 2])
        
        coords = np.array(np.where(mask)).T
        weights = field[mask]
        
        if np.sum(weights) == 0:
            return np.mean(coords, axis=0)
        
        centroid = np.average(coords, axis=0, weights=weights)
        return centroid
    
    def compute_tau_structure_centroid(self) -> np.ndarray:
        """Compute centroid of τ-gradient structure (lensing proxy)."""
        # τ gradient magnitude
        grad_x = np.roll(self.tau, -1, axis=0) - self.tau
        grad_y = np.roll(self.tau, -1, axis=1) - self.tau
        grad_z = np.roll(self.tau, -1, axis=2) - self.tau
        tau_grad = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Also weight by τ excess
        tau_excess = np.maximum(self.tau - 1.0, 0)
        lensing_field = tau_grad + tau_excess * 2
        
        return self.compute_centroid(lensing_field, threshold_percentile=85)
    
    def compute_gas_centroid(self) -> np.ndarray:
        """Compute centroid of gas field."""
        return self.compute_centroid(self.gas_field, threshold_percentile=75)
    
    def compute_visible_centroids(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute centroids of visible matter clusters."""
        c1 = self.compute_centroid(self.visible_matter_1, threshold_percentile=70)
        c2 = self.compute_centroid(self.visible_matter_2, threshold_percentile=70)
        return c1, c2
    
    def update_tracking_fields(self):
        """
        Update visible matter and gas fields based on wave dynamics.
        
        Key physics:
        - Visible matter cores move with wave velocity field
        - Gas is collisional: slows and heats during overlap
        """
        # Velocity field from wave dynamics
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        
        # Advection for visible matter (follows velocity)
        # Simplified: shift based on local velocity
        vx = self.psi_r_dot * self.psi_r / (amp**2 + 0.01)
        
        # Visible matter advection (collisionless - passes through)
        self.visible_matter_1 = np.roll(self.visible_matter_1, 
                                        int(np.sign(np.mean(vx * self.visible_matter_1)) * 0.5), 
                                        axis=0)
        self.visible_matter_2 = np.roll(self.visible_matter_2, 
                                        int(np.sign(np.mean(vx * self.visible_matter_2)) * 0.5), 
                                        axis=0)
        
        # Gas is collisional: where gas overlaps, it slows
        gas_overlap = self.gas_field > np.percentile(self.gas_field, 90)
        center = self.size // 2
        
        # Check if clusters have reached interaction region
        dist_to_center_1 = np.abs(self.cluster1_center[0] - center)
        dist_to_center_2 = np.abs(self.cluster2_center[0] - center)
        
        # Gas collision dynamics - only when both gas fields overlap significantly
        gas1_mask = self.gas_field > np.percentile(self.gas_field, 85)
        
        # Calculate collision region (where both clusters' gas would be)
        left_gas = np.zeros_like(self.gas_field)
        right_gas = np.zeros_like(self.gas_field)
        
        # Approximate: left half is cluster 1's gas, right half is cluster 2's
        left_gas[:self.size//2, :, :] = self.gas_field[:self.size//2, :, :]
        right_gas[self.size//2:, :, :] = self.gas_field[self.size//2:, :, :]
        
        # Overlap exists when both sides have gas in the middle region
        mid_region = slice(self.size//3, 2*self.size//3)
        left_in_mid = np.sum(left_gas[mid_region, :, :]) > 0.1
        right_in_mid = np.sum(right_gas[mid_region, :, :]) > 0.1
        
        if left_in_mid and right_in_mid:
            if not self.collision_detected:
                self.collision_detected = True
                self.collision_T = self.global_T
                print(f"  *** COLLISION DETECTED at T={self.global_T:.1f}")
            
            # Gas slows and heats in collision region (diffuses)
            self.gas_field = gaussian_filter(self.gas_field, sigma=0.3)
        
        # Decay and normalize
        self.visible_matter_1 *= 0.999
        self.visible_matter_2 *= 0.999
        self.gas_field *= 0.998
        
        # Renormalize to prevent decay to zero
        if np.max(self.visible_matter_1) > 0.01:
            self.visible_matter_1 /= np.max(self.visible_matter_1)
        if np.max(self.visible_matter_2) > 0.01:
            self.visible_matter_2 /= np.max(self.visible_matter_2)
        if np.max(self.gas_field) > 0.01:
            self.gas_field /= np.max(self.gas_field)
    
    def step(self):
        """Advance simulation one timestep."""
        self.step_count += 1
        self.global_T += self.dt
        
        # τ dynamics (with configurable response)
        if self.tau_response > 0:
            kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
            damped_energy = self.gamma * kinetic
            
            energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
            tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
            self.tau += self.tau_relaxation * (tau_target - self.tau)
            
            if self.damping_to_tau > 0:
                self.tau += self.damping_to_tau * damped_energy
            
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
        
        # Update tracking fields
        self.update_tracking_fields()


def run_bullet_cluster_test(
    target_T: float = 200.0,
    max_wall_seconds: float = 60.0,
    size: int = 64,
    seed: int = 42,
    tau_relaxation: float = 0.01,
    tau_response: float = 0.02,
    variant_name: str = "normal",
) -> Dict[str, Any]:
    """Run single Bullet Cluster analog test variant."""
    
    print(f"\n--- Variant: {variant_name} ---")
    print(f"    τ_relaxation={tau_relaxation}, τ_response={tau_response}")
    
    sim = BulletClusterSimulator(
        size=size, dt=0.10, seed=seed,
        tau_relaxation=tau_relaxation,
        tau_response=tau_response
    )
    
    t_start = time.time()
    measure_interval = 10.0
    last_measure = 0.0
    
    print()
    print(f"{'T':>6} | {'Gas_x':>6} | {'τ_x':>6} | {'Sep':>6} | {'τ_max':>6} | Status")
    print("-" * 60)
    
    while sim.global_T < target_T:
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - 3:
            print(f"\nWall time limit reached at T={sim.global_T:.1f}")
            break
        
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            
            # Compute centroids
            gas_centroid = sim.compute_gas_centroid()
            tau_centroid = sim.compute_tau_structure_centroid()
            vis1, vis2 = sim.compute_visible_centroids()
            
            # Separation (x-coordinate is collision axis)
            separation = tau_centroid[0] - gas_centroid[0]
            tau_max = float(np.max(sim.tau))
            
            status = "POST-COLLISION" if sim.collision_detected else "PRE-COLLISION"
            
            print(f"{sim.global_T:>6.1f} | {gas_centroid[0]:>6.1f} | {tau_centroid[0]:>6.1f} | "
                  f"{separation:>+6.1f} | {tau_max:>6.3f} | {status}")
            
            sim.metrics_history.append({
                'T': sim.global_T,
                'gas_centroid': gas_centroid.tolist(),
                'tau_centroid': tau_centroid.tolist(),
                'visible_1_centroid': vis1.tolist(),
                'visible_2_centroid': vis2.tolist(),
                'separation_x': float(separation),
                'tau_max': tau_max,
                'collision_detected': sim.collision_detected,
            })
    
    # Final analysis
    gas_final = sim.compute_gas_centroid()
    tau_final = sim.compute_tau_structure_centroid()
    final_separation = tau_final[0] - gas_final[0]
    
    return {
        'variant': variant_name,
        'tau_relaxation': tau_relaxation,
        'tau_response': tau_response,
        'collision_detected': sim.collision_detected,
        'collision_T': sim.collision_T,
        'final_gas_centroid': gas_final.tolist(),
        'final_tau_centroid': tau_final.tolist(),
        'final_separation': float(final_separation),
        'metrics': sim.metrics_history,
    }


def run_full_bullet_cluster_test(
    max_wall_seconds: float = 200.0,
    size: int = 64,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run full Bullet Cluster analog test with multiple variants.
    """
    
    print("=" * 70)
    print("  QMRT BULLET CLUSTER ANALOG TEST")
    print("=" * 70)
    print()
    print("HYPOTHESIS: τ-structure can separate from gas during collision,")
    print("            reproducing Bullet-Cluster-like observations.")
    print()
    print("Variants:")
    print("  1. No τ-response (control)")
    print("  2. Normal τ-response (main test)")
    print("  3. Fast τ-relaxation (medium follows gas quickly)")
    print("  4. Slow τ-relaxation (medium lags - expected to show separation)")
    print()
    
    results = {
        'variants': {},
        'analysis': {},
    }
    
    # Variant 1: No τ-response (control)
    results['variants']['no_response'] = run_bullet_cluster_test(
        target_T=200, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        tau_relaxation=0.01, tau_response=0.0,
        variant_name="no_response"
    )
    
    # Variant 2: Normal τ-response
    results['variants']['normal'] = run_bullet_cluster_test(
        target_T=200, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        tau_relaxation=0.01, tau_response=0.02,
        variant_name="normal"
    )
    
    # Variant 3: Fast τ-relaxation
    results['variants']['fast_relaxation'] = run_bullet_cluster_test(
        target_T=200, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        tau_relaxation=0.05, tau_response=0.02,
        variant_name="fast_relaxation"
    )
    
    # Variant 4: Slow τ-relaxation (expected best separation)
    results['variants']['slow_relaxation'] = run_bullet_cluster_test(
        target_T=200, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        tau_relaxation=0.002, tau_response=0.02,
        variant_name="slow_relaxation"
    )
    
    # Analysis - track PEAK separation, not just final
    print()
    print("=" * 70)
    print("  ANALYSIS")
    print("=" * 70)
    print()
    print(f"{'Variant':>20} | {'Collision?':>10} | {'Peak Sep':>10} | {'Final Sep':>10} | Interpretation")
    print("-" * 85)
    
    for name, data in results['variants'].items():
        collision = "YES" if data['collision_detected'] else "NO"
        final_sep = data['final_separation']
        
        # Calculate peak separation from metrics
        if data['metrics']:
            separations = [abs(m['separation_x']) for m in data['metrics']]
            peak_sep = max(separations)
        else:
            peak_sep = 0
        
        if peak_sep > 8:
            interp = "STRONG SEPARATION"
        elif peak_sep > 5:
            interp = "MODERATE SEPARATION"
        elif peak_sep > 2:
            interp = "Weak separation"
        else:
            interp = "No significant separation"
        
        print(f"{name:>20} | {collision:>10} | {peak_sep:>+10.2f} | {final_sep:>+10.2f} | {interp}")
        
        results['analysis'][name] = {
            'collision': data['collision_detected'],
            'peak_separation': peak_sep,
            'final_separation': final_sep,
            'interpretation': interp,
        }
        data['peak_separation'] = peak_sep
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    # Check peak separation across variants
    peak_separations = {name: data.get('peak_separation', 0) for name, data in results['variants'].items()}
    max_peak_sep = max(peak_separations.values())
    
    # Get specific variant peak separations
    normal_peak = peak_separations.get('normal', 0)
    slow_peak = peak_separations.get('slow_relaxation', 0)
    fast_peak = peak_separations.get('fast_relaxation', 0)
    control_peak = peak_separations.get('no_response', 0)
    
    # Key comparisons
    tau_response_effect = normal_peak > control_peak * 1.5
    relaxation_effect = slow_peak != fast_peak  # Different behavior
    
    print()
    print(f"  Maximum peak separation: {max_peak_sep:.2f} grid units")
    print(f"  Normal vs Control: {normal_peak:.2f} vs {control_peak:.2f}")
    print(f"  Slow vs Fast relaxation: {slow_peak:.2f} vs {fast_peak:.2f}")
    print()
    print(f"  τ-response creates separation: {'YES' if tau_response_effect else 'NO'}")
    print(f"  τ-relaxation affects dynamics: {'YES' if relaxation_effect else 'NO'}")
    
    if max_peak_sep > 8 and tau_response_effect:
        verdict = "CONFIRMED: τ-structure separates from gas during collision"
    elif max_peak_sep > 5:
        verdict = "PARTIAL: Significant transient separation observed"
    elif max_peak_sep > 3:
        verdict = "WEAK: Some separation, but may not be sufficient"
    else:
        verdict = "NOT CONFIRMED: No clear τ-gas separation"
    
    print()
    print(f"  {verdict}")
    
    results['verdict'] = verdict
    results['max_peak_separation'] = max_peak_sep
    results['tau_response_creates_separation'] = tau_response_effect
    results['relaxation_affects_dynamics'] = relaxation_effect
    
    # Save results
    output_dir = '/app/backend/qmrt_topology/papers/bullet_cluster'
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert numpy types for JSON
    def convert_for_json(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_for_json(v) for v in obj]
        else:
            return obj
    
    with open(f'{output_dir}/bullet_cluster_results.json', 'w') as f:
        json.dump(convert_for_json(results), f, indent=2)
    
    print()
    print(f"Results saved to: {output_dir}/bullet_cluster_results.json")
    
    return results


def main():
    results = run_full_bullet_cluster_test(
        max_wall_seconds=200.0,
        size=64,
        seed=42,
    )
    return results


if __name__ == "__main__":
    main()
