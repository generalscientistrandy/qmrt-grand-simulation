"""
τ-Well Focusing Test
====================

PURPOSE: Test whether a localized τ-well (lower τ region in higher τ background)
acts as an attractive lens, focusing wave propagation toward/through the well.

HYPOTHESIS:
  Since waves bend toward slower (lower τ) regions, a central τ-well should
  act as a focusing lens, converging wavefronts that pass near it.

SETUP:
  - Background τ = 1.8 (fast propagation)
  - Central well τ = 1.8 - Δτ (slower propagation)
  - Plane wave propagates through the region
  - Track convergence/focusing behind the well

METRICS:
  - focal_strength: intensity enhancement at/behind well
  - wavefront_convergence: width narrowing behind well
  - deflection_symmetry: left/right balance
  - focal_distance: where maximum concentration occurs
  - intensity_profile: cross-sectional intensity distribution

SWEEP:
  - well_depth Δτ = [0.0, 0.2, 0.4, 0.6, 0.8]
  - well_radius = [4, 6, 8]

PASS CONDITION:
  Stronger τ wells produce stronger focusing and more consistent convergence.

BASELINE: Regulated Recovery v1.1 parameters (but controlled τ field)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class TauWellSimulator:
    """Simulator for τ-well focusing measurement."""
    
    def __init__(self, size: int = 64, dt: float = 0.08, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.T = 0.0
        self.step_count = 0
        
        # Wave field - start quiescent
        self.psi_r = np.zeros((size, size, size))
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # τ field - will be set by setup_tau_well
        self.tau = np.ones((size, size, size))
        
        # Physics parameters
        self.c_0_sq = 4.0
        self.gamma = 0.002  # Very low damping for clean propagation
        
        # Well parameters (stored for reference)
        self.well_center = None
        self.well_radius = None
        self.well_depth = None
    
    def setup_tau_well(self, tau_background: float, well_depth: float, 
                       well_radius: float, well_center: Tuple[int, int, int] = None):
        """
        Set up a spherical τ-well (lower τ region).
        
        tau_background: τ value outside the well
        well_depth: Δτ below background (well τ = background - depth)
        well_radius: radius of the well in grid cells
        well_center: (x, y, z) center of well (default: grid center)
        """
        if well_center is None:
            well_center = (self.size // 2, self.size // 2, self.size // 2)
        
        cx, cy, cz = well_center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Distance from well center
        r = np.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
        
        # Sharper well profile (super-Gaussian for more lens-like behavior)
        # Use tanh for sharper edge
        well_profile = 0.5 * (1 - np.tanh((r - well_radius) / 2))
        self.tau = tau_background - well_depth * well_profile
        
        # Ensure τ stays positive
        self.tau = np.maximum(self.tau, 0.5)
        
        # Store parameters
        self.well_center = well_center
        self.well_radius = well_radius
        self.well_depth = well_depth
        
        return {
            'tau_background': tau_background,
            'tau_well_center': tau_background - well_depth,
            'well_depth': well_depth,
            'well_radius': well_radius,
            'c_eff_background': np.sqrt(self.c_0_sq * tau_background),
            'c_eff_well_center': np.sqrt(self.c_0_sq * max(0.5, tau_background - well_depth)),
        }
    
    def inject_plane_wave(self, propagation_dir: np.ndarray, 
                          start_position: float = None,
                          width: float = None,
                          k_magnitude: float = 0.5,
                          amplitude: float = 2.0):
        """
        Inject a plane wave front propagating in the specified direction.
        
        The wave is a wide Gaussian beam to see focusing effects clearly.
        """
        if start_position is None:
            start_position = self.size // 4  # Start 1/4 into grid
        if width is None:
            width = self.size * 0.6  # Wide beam
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        prop_dir = propagation_dir / (np.linalg.norm(propagation_dir) + 1e-10)
        
        # Position along propagation direction
        pos_along = prop_dir[0] * x + prop_dir[1] * y + prop_dir[2] * z
        
        # Distance perpendicular to propagation (for beam width)
        center = self.size / 2
        if abs(prop_dir[1]) > 0.5:  # Propagating in y
            perp_dist_sq = (x - center)**2 + (z - center)**2
        else:
            perp_dist_sq = (y - center)**2 + (z - center)**2
        
        # Gaussian beam profile
        beam_profile = np.exp(-perp_dist_sq / (2 * (width/2)**2))
        
        # Wave packet along propagation direction
        longitudinal = np.exp(-((pos_along - start_position) / 4)**2)
        
        # Combined envelope
        envelope = amplitude * beam_profile * longitudinal
        
        # Plane wave phase
        phase = k_magnitude * pos_along
        
        self.psi_r = envelope * np.cos(phase)
        self.psi_i = envelope * np.sin(phase)
        
        # Initial momentum
        local_tau = np.mean(self.tau[:, :self.size//4, :])  # τ at injection region
        c_eff = np.sqrt(self.c_0_sq * local_tau)
        omega = c_eff * k_magnitude
        
        self.psi_r_dot = omega * self.psi_i.copy()
        self.psi_i_dot = -omega * self.psi_r.copy()
    
    def step(self):
        """Advance simulation by one timestep."""
        self.step_count += 1
        self.T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        c_eff_sq = self.c_0_sq * self.tau
        
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def get_energy(self) -> np.ndarray:
        return self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
    
    def get_cross_section_intensity(self, y_position: int, axis: str = 'xz') -> Dict:
        """
        Get intensity cross-section at a given y position.
        
        Returns intensity integrated over z, giving x-profile.
        """
        energy = self.get_energy()
        
        if axis == 'xz':
            # Slice at y_position, sum over z
            slice_2d = energy[:, y_position, :]
            profile = np.sum(slice_2d, axis=1)  # Sum over z → x profile
        else:
            # Slice at y_position, sum over x
            slice_2d = energy[:, y_position, :]
            profile = np.sum(slice_2d, axis=0)  # Sum over x → z profile
        
        # Find peak and width
        peak_idx = np.argmax(profile)
        peak_value = profile[peak_idx]
        
        # FWHM calculation
        half_max = peak_value / 2
        above_half = profile > half_max
        if np.any(above_half):
            indices = np.where(above_half)[0]
            fwhm = indices[-1] - indices[0]
        else:
            fwhm = self.size
        
        return {
            'profile': profile.tolist(),
            'peak_position': int(peak_idx),
            'peak_value': float(peak_value),
            'fwhm': int(fwhm),
            'total_intensity': float(np.sum(profile)),
        }
    
    def get_focusing_metrics(self, propagation_dir: np.ndarray) -> Dict:
        """
        Compute focusing metrics: compare beam width before and after well.
        """
        energy = self.get_energy()
        
        # Assuming propagation in +y direction
        # Compare beam width at different y positions
        
        y_before = self.size // 4  # Before well
        y_at = self.size // 2      # At well
        y_after = 3 * self.size // 4  # After well
        
        before = self.get_cross_section_intensity(y_before)
        at_well = self.get_cross_section_intensity(y_at)
        after = self.get_cross_section_intensity(y_after)
        
        # Focusing ratio: width_before / width_after
        # > 1 means focusing (beam narrowed)
        if after['fwhm'] > 0:
            focusing_ratio = before['fwhm'] / after['fwhm']
        else:
            focusing_ratio = 1.0
        
        # Intensity enhancement: peak_after / peak_before
        if before['peak_value'] > 1e-10:
            intensity_enhancement = after['peak_value'] / before['peak_value']
        else:
            intensity_enhancement = 1.0
        
        # Concentration: how much energy is near the axis after well
        center = self.size // 2
        near_axis_width = self.size // 6
        
        after_profile = np.array(after['profile'])
        near_axis_mask = (np.arange(len(after_profile)) > center - near_axis_width) & \
                         (np.arange(len(after_profile)) < center + near_axis_width)
        
        concentration = np.sum(after_profile[near_axis_mask]) / (np.sum(after_profile) + 1e-10)
        
        return {
            'fwhm_before': before['fwhm'],
            'fwhm_at_well': at_well['fwhm'],
            'fwhm_after': after['fwhm'],
            'focusing_ratio': float(focusing_ratio),
            'peak_before': float(before['peak_value']),
            'peak_at_well': float(at_well['peak_value']),
            'peak_after': float(after['peak_value']),
            'intensity_enhancement': float(intensity_enhancement),
            'near_axis_concentration': float(concentration),
        }


def run_focusing_test(well_depth: float, well_radius: float, seed: int,
                       T_max: float = 14.0, baseline_fwhm: float = None) -> Dict:
    """
    Run a single τ-well focusing test.
    """
    tau_background = 1.8
    
    sim = TauWellSimulator(size=64, dt=0.08, seed=seed)
    
    # Setup well at center
    well_info = sim.setup_tau_well(
        tau_background=tau_background,
        well_depth=well_depth,
        well_radius=well_radius
    )
    
    # Inject plane wave propagating in +y direction
    propagation_dir = np.array([0.0, 1.0, 0.0])
    sim.inject_plane_wave(propagation_dir, start_position=sim.size // 6,
                          width=sim.size * 0.7, k_magnitude=0.4, amplitude=2.0)
    
    # Run until wave has passed through well
    while sim.T < T_max:
        sim.step()
    
    # Measure focusing
    focusing = sim.get_focusing_metrics(propagation_dir)
    
    # Calculate relative focusing (compared to baseline if provided)
    if baseline_fwhm is not None and baseline_fwhm > 0:
        relative_focusing = baseline_fwhm / focusing['fwhm_after'] if focusing['fwhm_after'] > 0 else 1.0
    else:
        relative_focusing = 1.0
    
    return {
        'well_depth': float(well_depth),
        'well_radius': float(well_radius),
        'tau_background': float(tau_background),
        'tau_well_center': float(well_info['tau_well_center']),
        'c_eff_ratio': float(well_info['c_eff_well_center'] / well_info['c_eff_background']),
        'seed': seed,
        'relative_focusing': float(relative_focusing),
        **focusing,
    }


def main():
    print("=" * 80)
    print("  τ-WELL FOCUSING TEST")
    print("=" * 80)
    print()
    print("Hypothesis: A τ-well (lower τ region) acts as a focusing lens,")
    print("            converging waves that pass near it.")
    print()
    print("Setup:")
    print("  - Background τ = 1.8 (fast)")
    print("  - Well τ = 1.8 - Δτ (slower)")
    print("  - Plane wave propagates in +y through the well")
    print()
    print("Physics: Waves bend toward slower regions → convergence toward well center")
    print()
    
    seeds = [42, 123, 456]
    well_depths = [0.0, 0.2, 0.4, 0.6, 0.8]
    well_radii = [4, 6, 8]
    fixed_radius = 6
    fixed_depth = 0.6
    
    all_results = []
    
    print("-" * 80)
    print("Running tests...")
    print("-" * 80)
    
    t0_total = time.time()
    
    # First run baseline (no well) to get reference FWHM
    print("Getting baseline (no well)...")
    baseline_results = []
    for seed in seeds:
        result = run_focusing_test(
            well_depth=0.0,
            well_radius=fixed_radius,
            seed=seed,
            T_max=14.0
        )
        baseline_results.append(result)
        all_results.append(result)
    
    baseline_fwhm = np.mean([r['fwhm_after'] for r in baseline_results])
    print(f"Baseline FWHM after propagation: {baseline_fwhm:.1f}")
    print()
    
    # Test different well depths at fixed radius
    print(f"Sweeping well depth (radius = {fixed_radius}):")
    
    for depth in well_depths[1:]:  # Skip 0.0, already done
        seed_results = []
        for seed in seeds:
            result = run_focusing_test(
                well_depth=depth,
                well_radius=fixed_radius,
                seed=seed,
                T_max=14.0,
                baseline_fwhm=baseline_fwhm
            )
            seed_results.append(result)
            all_results.append(result)
        
        focus_avg = np.mean([r['focusing_ratio'] for r in seed_results])
        enhance_avg = np.mean([r['intensity_enhancement'] for r in seed_results])
        conc_avg = np.mean([r['near_axis_concentration'] for r in seed_results])
        
        print(f"  Δτ={depth:.1f}: focus_ratio={focus_avg:.3f}, "
              f"intensity={enhance_avg:.3f}, concentration={conc_avg:.3f}")
    
    # Test different radii at fixed depth
    fixed_depth = 0.6
    print(f"\nSweeping well radius (depth = {fixed_depth}):")
    
    for radius in well_radii:
        if radius == fixed_radius:  # Already tested
            continue
        
        seed_results = []
        for seed in seeds:
            result = run_focusing_test(
                well_depth=fixed_depth,
                well_radius=radius,
                seed=seed,
                T_max=14.0,
                baseline_fwhm=baseline_fwhm
            )
            seed_results.append(result)
            all_results.append(result)
        
        focus_avg = np.mean([r['focusing_ratio'] for r in seed_results])
        enhance_avg = np.mean([r['intensity_enhancement'] for r in seed_results])
        
        print(f"  r={radius}: focus_ratio={focus_avg:.3f}, intensity={enhance_avg:.3f}")
    
    print(f"\nTotal time: {time.time()-t0_total:.1f}s")
    print()
    
    # Aggregate by well depth (fixed radius = 6)
    by_depth = {}
    for r in all_results:
        if r['well_radius'] == fixed_radius:
            d = r['well_depth']
            if d not in by_depth:
                by_depth[d] = []
            by_depth[d].append(r)
    
    aggregated_depth = []
    for d in sorted(by_depth.keys()):
        runs = by_depth[d]
        agg = {
            'well_depth': d,
            'well_radius': fixed_radius,
            'focusing_ratio': np.mean([r['focusing_ratio'] for r in runs]),
            'focusing_std': np.std([r['focusing_ratio'] for r in runs]),
            'intensity_enhancement': np.mean([r['intensity_enhancement'] for r in runs]),
            'near_axis_concentration': np.mean([r['near_axis_concentration'] for r in runs]),
            'fwhm_after': np.mean([r['fwhm_after'] for r in runs]),
        }
        aggregated_depth.append(agg)
    
    # Print results
    print("=" * 80)
    print("  RESULTS: WELL DEPTH SWEEP (radius = 6)")
    print("=" * 80)
    print()
    
    print(f"{'Δτ':>5} | {'τ_well':>7} | {'focus_ratio':>12} | {'intensity':>10} | {'concentration':>13}")
    print("-" * 65)
    
    for r in aggregated_depth:
        tau_well = 1.8 - r['well_depth']
        print(f"{r['well_depth']:>5.1f} | {tau_well:>7.2f} | {r['focusing_ratio']:>12.3f} | "
              f"{r['intensity_enhancement']:>10.3f} | {r['near_axis_concentration']:>13.3f}")
    
    print()
    
    # Analysis
    print("=" * 80)
    print("  FOCUSING ANALYSIS")
    print("=" * 80)
    print()
    
    # Check if focusing increases with well depth
    depths = [r['well_depth'] for r in aggregated_depth if r['well_depth'] > 0]
    focus_ratios = [r['focusing_ratio'] for r in aggregated_depth if r['well_depth'] > 0]
    concentrations = [r['near_axis_concentration'] for r in aggregated_depth if r['well_depth'] > 0]
    
    if len(depths) >= 2:
        corr_focus = np.corrcoef(depths, focus_ratios)[0, 1]
        corr_focus = corr_focus if not np.isnan(corr_focus) else 0.0
        
        corr_conc = np.corrcoef(depths, concentrations)[0, 1]
        corr_conc = corr_conc if not np.isnan(corr_conc) else 0.0
    else:
        corr_focus = 0.0
        corr_conc = 0.0
    
    # Baseline check
    baseline = [r for r in aggregated_depth if r['well_depth'] == 0.0]
    if baseline:
        baseline_focus = baseline[0]['focusing_ratio']
        baseline_conc = baseline[0]['near_axis_concentration']
    else:
        baseline_focus = 1.0
        baseline_conc = 0.33  # ~1/3 if uniform
    
    # Maximum focusing
    max_focus = max([r['focusing_ratio'] for r in aggregated_depth])
    max_depth = [r['well_depth'] for r in aggregated_depth if r['focusing_ratio'] == max_focus][0]
    
    print(f"Focusing-depth correlation: {corr_focus:.3f}")
    print(f"Concentration-depth correlation: {corr_conc:.3f}")
    print(f"Baseline focusing (Δτ=0): {baseline_focus:.3f}")
    print(f"Maximum focusing: {max_focus:.3f} at Δτ={max_depth:.1f}")
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    # Pass conditions:
    # 1. Focusing ratio > 1 for deep wells (beam narrows)
    # 2. Concentration increases with depth
    # 3. Positive correlation between depth and focusing
    
    deepest = [r for r in aggregated_depth if r['well_depth'] >= 0.6]
    if deepest:
        deep_focus = deepest[0]['focusing_ratio']
        deep_conc = deepest[0]['near_axis_concentration']
    else:
        deep_focus = 1.0
        deep_conc = 0.33
    
    cond1 = deep_focus > 1.05  # At least 5% focusing
    cond2 = corr_conc > 0.3    # Concentration increases with depth
    cond3 = corr_focus > 0.3   # Focusing increases with depth
    
    if cond1 and (cond2 or cond3):
        verdict = "FOCUSING_CONFIRMED"
        print("★ τ-WELL FOCUSING CONFIRMED")
        print()
        print("  τ-wells act as attractive lenses:")
        print(f"    - Focusing ratio at Δτ=0.6: {deep_focus:.3f} (> 1 = narrowing)")
        print(f"    - Focusing-depth correlation: {corr_focus:.3f}")
        print(f"    - Concentration-depth correlation: {corr_conc:.3f}")
        print()
        print("  Waves converge toward the slower (lower τ) region,")
        print("  consistent with τ acting as an effective refractive geometry.")
    elif cond1:
        verdict = "WEAK_FOCUSING"
        print("✓ WEAK τ-WELL FOCUSING")
        print()
        print("  Some focusing observed, but correlation with depth is weak.")
    else:
        verdict = "NO_FOCUSING"
        print("✗ NO CLEAR FOCUSING")
        print()
        print("  τ-wells do not produce systematic focusing.")
        print(f"  Deep well focusing ratio: {deep_focus:.3f}")
    
    print()
    print("Physical interpretation:")
    print("  A τ-well with lower τ (slower c_eff) acts like a converging lens")
    print("  in optics. Waves bend toward the slower region, causing the beam")
    print("  to narrow and concentrate as it passes through the well.")
    
    # Convert for JSON
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    # Save results
    output = convert({
        'test': 'tau_well_focusing',
        'date': 'December 2025',
        'baseline': 'Regulated Recovery v1.1',
        'hypothesis': 'τ-wells act as focusing lenses',
        'configuration': {
            'tau_background': 1.8,
            'well_depths': well_depths,
            'well_radii': well_radii,
            'fixed_radius': fixed_radius,
            'fixed_depth': fixed_depth,
            'seeds': seeds,
            'grid_size': 64,
            'dt': 0.08,
            'T_max': 14.0,
        },
        'verdict': verdict,
        'analysis': {
            'focusing_depth_correlation': float(corr_focus),
            'concentration_depth_correlation': float(corr_conc),
            'baseline_focusing': float(baseline_focus),
            'max_focusing': float(max_focus),
            'max_focusing_depth': float(max_depth),
        },
        'aggregated_by_depth': aggregated_depth,
        'all_runs': all_results,
    })
    
    with open('/app/backend/qmrt_topology/papers/TAU_WELL_FOCUSING_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/TAU_WELL_FOCUSING_RESULTS.json")
    
    return output


if __name__ == "__main__":
    main()
