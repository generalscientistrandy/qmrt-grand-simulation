"""
QMRT Asymmetric τ-Lens Test
============================

PURPOSE: Verify that asymmetric τ structures can produce actual wavefront 
focusing, analogous to gravitational lensing in general relativity.

HYPOTHESIS:
  τ gradients create an effective refractive index for wave propagation.
  An asymmetric τ structure should:
  1. Bend passing wavefronts
  2. Create a focal point behind the lens
  3. Produce measurable intensity amplification at the focus

TEST DESIGN:
  1. Create an asymmetric τ structure (lens)
  2. Send a planar wavefront toward the lens
  3. Measure:
     - Wavefront curvature before/after lens
     - Intensity distribution behind lens
     - Focal point location and amplification

PASS CONDITION:
  - Wavefronts curve toward the lens axis after passing
  - Intensity peaks at a focal point behind the lens
  - Amplification factor > 1 at focus

PHYSICAL ANALOGY:
  In GR, mass curves spacetime, bending light paths.
  In QMRT, τ gradients create effective refractive index, bending wave paths.
  Both produce gravitational lensing effects.

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Dict, List, Any, Tuple
import time
import json
import os


class AsymmetricLensSimulator:
    """
    Simulator for testing wavefront focusing through τ-lens structures.
    
    Creates an asymmetric τ lens and measures wavefront bending/focusing.
    """
    
    def __init__(self, 
                 size: int = 64,
                 dt: float = 0.08,  # Smaller timestep for wave accuracy
                 seed: int = 42,
                 lens_strength: float = 0.5,
                 lens_asymmetry: float = 0.3):
        """
        Initialize asymmetric lens test.
        
        Parameters:
        -----------
        lens_strength : float
            How much τ deviates from 1.0 at lens center
        lens_asymmetry : float
            Asymmetry factor (0 = symmetric, 1 = highly asymmetric)
        """
        
        self.size = size
        self.dt = dt
        self.seed = seed
        self.lens_strength = lens_strength
        self.lens_asymmetry = lens_asymmetry
        
        np.random.seed(seed)
        
        # Wave physics (simplified - no τ evolution, just static lens)
        self.c_0_sq = 4.0
        self.gamma = 0.003  # Low damping for clean wave propagation
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Initialize fields
        shape = (size, size, size)
        self.psi_r = np.zeros(shape)
        self.psi_i = np.zeros(shape)
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        
        # Create static τ lens
        self.tau = np.ones(shape)
        self._create_asymmetric_lens()
        
        # Lens position (for reference)
        self.lens_x = size // 3
        self.lens_y = size // 2
        self.lens_z = size // 2
        
        # Metrics
        self.intensity_history = []
        self.wavefront_snapshots = []
        
        print(f"Asymmetric τ-Lens Test initialized")
        print(f"  Grid: {size}³")
        print(f"  Lens strength: {lens_strength}")
        print(f"  Lens asymmetry: {lens_asymmetry}")
        print(f"  Lens position: x={self.lens_x}")
    
    def _create_asymmetric_lens(self):
        """
        Create an asymmetric τ structure that acts as a lens.
        
        The lens has:
        - Higher τ on one side (slower wave speed)
        - Lower τ on other side (faster wave speed)
        This creates differential bending → focusing
        """
        lens_x = self.size // 3
        lens_y = self.size // 2
        lens_z = self.size // 2
        lens_radius = self.size // 8
        
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    # Distance to lens center
                    dx = x - lens_x
                    dy = y - lens_y
                    dz = z - lens_z
                    r = np.sqrt(dx**2 + dy**2 + dz**2)
                    
                    if r < lens_radius * 2:
                        # Base lens profile (Gaussian-like)
                        base_profile = np.exp(-r**2 / (2 * lens_radius**2))
                        
                        # Asymmetry: higher τ on +y side, lower on -y side
                        # This creates differential refraction
                        asymmetry_factor = 1.0 + self.lens_asymmetry * (dy / lens_radius)
                        
                        # τ deviation from 1.0
                        tau_deviation = self.lens_strength * base_profile * asymmetry_factor
                        
                        self.tau[x, y, z] = 1.0 + tau_deviation
        
        # Ensure τ stays in valid range
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        # Store lens properties
        self.lens_tau_max = float(np.max(self.tau))
        self.lens_tau_min = float(np.min(self.tau))
        
        print(f"  Lens τ range: {self.lens_tau_min:.3f} - {self.lens_tau_max:.3f}")
    
    def inject_planar_wave(self, x_start: int = 5, wavelength: float = 8.0, amplitude: float = 1.0):
        """
        Inject a planar wavefront traveling in +x direction.
        
        The wave starts at x=x_start and propagates toward the lens.
        """
        k = 2 * np.pi / wavelength  # Wave number
        
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    # Only inject in the source region
                    if x < x_start + 3:
                        # Planar wave: psi = A * cos(kx - ωt), at t=0: psi = A * cos(kx)
                        phase = k * (x - x_start)
                        envelope = np.exp(-((x - x_start) / 2)**2)  # Smooth start
                        
                        self.psi_r[x, y, z] = amplitude * envelope * np.cos(phase)
                        self.psi_i[x, y, z] = amplitude * envelope * np.sin(phase)
                        
                        # Initial velocity for propagation in +x
                        omega = np.sqrt(self.c_0_sq) * k
                        self.psi_r_dot[x, y, z] = amplitude * envelope * omega * np.sin(phase)
                        self.psi_i_dot[x, y, z] = -amplitude * envelope * omega * np.cos(phase)
        
        print(f"  Planar wave injected: wavelength={wavelength}, amplitude={amplitude}")
    
    def _laplacian(self, f):
        """3D Laplacian."""
        lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def step(self):
        """Advance simulation one timestep."""
        self.step_count += 1
        self.global_T += self.dt
        
        # Wave equation with τ-dependent speed
        # c_eff² = c_0² * τ
        c_eff_sq = self.c_0_sq * self.tau
        
        lap_r = self._laplacian(self.psi_r)
        lap_i = self._laplacian(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def compute_intensity(self) -> np.ndarray:
        """Compute wave intensity field."""
        return self.psi_r**2 + self.psi_i**2
    
    def compute_intensity_profile(self, x_pos: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute intensity profile at a given x position (y-z plane).
        Returns y coordinates and intensity values along the central z slice.
        """
        intensity = self.compute_intensity()
        z_center = self.size // 2
        
        # Profile along y at fixed x, z
        y_coords = np.arange(self.size)
        intensity_profile = intensity[x_pos, :, z_center]
        
        return y_coords, intensity_profile
    
    def find_focal_point(self) -> Tuple[int, float, float]:
        """
        Find the focal point behind the lens by looking for intensity maximum.
        
        Returns:
            (x_focal, y_focal, max_intensity)
        """
        intensity = self.compute_intensity()
        
        # Search region: behind the lens (x > lens_x + radius)
        search_start = self.lens_x + self.size // 8
        search_end = min(self.lens_x + self.size // 2, self.size - 5)
        
        z_center = self.size // 2
        
        max_intensity = 0
        focal_x = search_start
        focal_y = self.size // 2
        
        for x in range(search_start, search_end):
            # Look for maximum along y at this x
            y_profile = intensity[x, :, z_center]
            max_at_x = np.max(y_profile)
            
            if max_at_x > max_intensity:
                max_intensity = max_at_x
                focal_x = x
                focal_y = np.argmax(y_profile)
        
        return focal_x, focal_y, max_intensity
    
    def compute_wavefront_curvature(self, x_pos: int) -> float:
        """
        Estimate wavefront curvature at given x position.
        
        Positive curvature = converging (focusing)
        Negative curvature = diverging
        Zero = planar
        """
        intensity = self.compute_intensity()
        z_center = self.size // 2
        
        # Get phase field
        phase = np.arctan2(self.psi_i, self.psi_r + 1e-10)
        
        # Phase gradient in y direction at this x
        phase_slice = phase[x_pos, :, z_center]
        
        # Unwrap phase
        phase_unwrapped = np.unwrap(phase_slice)
        
        # Curvature from second derivative of phase
        y_center = self.size // 2
        margin = self.size // 4
        
        if y_center - margin > 0 and y_center + margin < self.size:
            region = phase_unwrapped[y_center - margin:y_center + margin]
            if len(region) > 4:
                # Fit quadratic to get curvature
                y_local = np.arange(len(region)) - len(region) // 2
                try:
                    coeffs = np.polyfit(y_local, region, 2)
                    curvature = 2 * coeffs[0]  # Second derivative
                    return float(curvature)
                except:
                    return 0.0
        
        return 0.0


def run_lens_test(
    target_T: float = 50.0,
    max_wall_seconds: float = 60.0,
    size: int = 64,
    seed: int = 42,
    lens_strength: float = 0.5,
    lens_asymmetry: float = 0.3,
) -> Dict[str, Any]:
    """Run single lens test."""
    
    sim = AsymmetricLensSimulator(
        size=size, dt=0.08, seed=seed,
        lens_strength=lens_strength,
        lens_asymmetry=lens_asymmetry
    )
    
    # Inject planar wave
    sim.inject_planar_wave(x_start=5, wavelength=8.0, amplitude=1.0)
    
    t_start = time.time()
    measure_interval = 5.0
    last_measure = 0.0
    
    print()
    print(f"{'T':>6} | {'Wave_x':>7} | {'Focus_x':>7} | {'Peak_I':>8} | {'Curv':>8}")
    print("-" * 55)
    
    results = {
        'snapshots': [],
        'config': {
            'lens_strength': lens_strength,
            'lens_asymmetry': lens_asymmetry,
            'lens_x': sim.lens_x,
        }
    }
    
    # Initial wave front position
    wave_front_x = 5
    
    while sim.global_T < target_T:
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - 3:
            break
        
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            
            # Track wave front (where intensity is significant)
            intensity = sim.compute_intensity()
            x_profile = np.max(np.max(intensity, axis=2), axis=1)
            threshold = np.max(x_profile) * 0.1
            wave_positions = np.where(x_profile > threshold)[0]
            if len(wave_positions) > 0:
                wave_front_x = int(np.max(wave_positions))
            
            # Find focal point
            focal_x, focal_y, peak_intensity = sim.find_focal_point()
            
            # Compute curvature at wave front
            if wave_front_x < size - 5:
                curvature = sim.compute_wavefront_curvature(wave_front_x)
            else:
                curvature = 0.0
            
            print(f"{sim.global_T:>6.1f} | {wave_front_x:>7} | {focal_x:>7} | "
                  f"{peak_intensity:>8.4f} | {curvature:>+8.4f}")
            
            results['snapshots'].append({
                'T': sim.global_T,
                'wave_front_x': wave_front_x,
                'focal_x': focal_x,
                'focal_y': focal_y,
                'peak_intensity': float(peak_intensity),
                'curvature': float(curvature),
            })
    
    # Final analysis
    focal_x, focal_y, final_peak = sim.find_focal_point()
    
    results['final'] = {
        'focal_x': focal_x,
        'focal_y': focal_y,
        'peak_intensity': float(final_peak),
        'lens_x': sim.lens_x,
        'focal_distance': focal_x - sim.lens_x,
    }
    
    return sim, results


def run_full_lens_test(
    max_wall_seconds: float = 180.0,
    size: int = 64,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run full asymmetric lens test with multiple configurations.
    """
    
    print("=" * 70)
    print("  QMRT ASYMMETRIC τ-LENS TEST")
    print("=" * 70)
    print()
    print("HYPOTHESIS: Asymmetric τ structures can focus wavefronts,")
    print("            analogous to gravitational lensing.")
    print()
    print("TEST: Send planar wave through τ lens, measure focusing.")
    print()
    
    all_results = {
        'variants': {},
        'analysis': {},
    }
    
    # Variant 1: No lens (control)
    print("\n--- Variant: No Lens (Control) ---")
    sim_ctrl, results_ctrl = run_lens_test(
        target_T=50.0, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        lens_strength=0.0, lens_asymmetry=0.0
    )
    all_results['variants']['no_lens'] = results_ctrl
    
    # Variant 2: Symmetric lens
    print("\n--- Variant: Symmetric Lens ---")
    sim_sym, results_sym = run_lens_test(
        target_T=50.0, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        lens_strength=0.5, lens_asymmetry=0.0
    )
    all_results['variants']['symmetric'] = results_sym
    
    # Variant 3: Asymmetric lens (main test)
    print("\n--- Variant: Asymmetric Lens (Main) ---")
    sim_asym, results_asym = run_lens_test(
        target_T=50.0, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        lens_strength=0.5, lens_asymmetry=0.4
    )
    all_results['variants']['asymmetric'] = results_asym
    
    # Variant 4: Strong asymmetric lens
    print("\n--- Variant: Strong Asymmetric Lens ---")
    sim_strong, results_strong = run_lens_test(
        target_T=50.0, max_wall_seconds=max_wall_seconds/4,
        size=size, seed=seed,
        lens_strength=0.8, lens_asymmetry=0.5
    )
    all_results['variants']['strong_asymmetric'] = results_strong
    
    # Analysis
    print()
    print("=" * 70)
    print("  ANALYSIS")
    print("=" * 70)
    print()
    
    print(f"{'Variant':>20} | {'Peak I':>10} | {'Focal Dist':>10} | {'Focus?':>10}")
    print("-" * 60)
    
    control_peak = results_ctrl['final']['peak_intensity']
    
    for name, data in all_results['variants'].items():
        peak_i = data['final']['peak_intensity']
        focal_dist = data['final']['focal_distance']
        
        # Focusing criterion: peak > control AND focal point exists
        amplification = peak_i / control_peak if control_peak > 0 else 1.0
        has_focus = amplification > 1.2 and focal_dist > 5
        
        focus_str = f"YES ({amplification:.2f}x)" if has_focus else "NO"
        
        print(f"{name:>20} | {peak_i:>10.4f} | {focal_dist:>10} | {focus_str:>10}")
        
        all_results['analysis'][name] = {
            'peak_intensity': peak_i,
            'focal_distance': focal_dist,
            'amplification': amplification,
            'has_focus': has_focus,
        }
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    # Check if any lens variant shows focusing
    lens_variants = ['symmetric', 'asymmetric', 'strong_asymmetric']
    focusing_results = [all_results['analysis'][v]['has_focus'] for v in lens_variants]
    amplifications = [all_results['analysis'][v]['amplification'] for v in lens_variants]
    
    any_focusing = any(focusing_results)
    max_amplification = max(amplifications)
    
    # Check asymmetric vs symmetric
    asym_amp = all_results['analysis']['asymmetric']['amplification']
    sym_amp = all_results['analysis']['symmetric']['amplification']
    asym_stronger = asym_amp > sym_amp
    
    print()
    print(f"  Control peak intensity: {control_peak:.4f}")
    print(f"  Maximum amplification: {max_amplification:.2f}x")
    print(f"  Any focusing observed: {'YES' if any_focusing else 'NO'}")
    print(f"  Asymmetric > Symmetric: {'YES' if asym_stronger else 'NO'}")
    
    if any_focusing and max_amplification > 1.5:
        verdict = "CONFIRMED: τ-lens produces wavefront focusing"
    elif any_focusing:
        verdict = "PARTIAL: Weak focusing observed"
    else:
        verdict = "NOT CONFIRMED: No clear focusing effect"
    
    print()
    print(f"  {verdict}")
    
    all_results['verdict'] = verdict
    all_results['max_amplification'] = max_amplification
    all_results['any_focusing'] = any_focusing
    all_results['asymmetric_stronger'] = asym_stronger
    
    # Save results
    output_dir = '/app/backend/qmrt_topology/papers/tau_lens'
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert for JSON
    def convert_for_json(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_for_json(v) for v in obj]
        else:
            return obj
    
    with open(f'{output_dir}/tau_lens_results.json', 'w') as f:
        json.dump(convert_for_json(all_results), f, indent=2)
    
    print()
    print(f"Results saved to: {output_dir}/tau_lens_results.json")
    
    return all_results


def main():
    results = run_full_lens_test(
        max_wall_seconds=180.0,
        size=64,
        seed=42,
    )
    return results


if __name__ == "__main__":
    main()
