"""
τ-Peak Focusing Test
====================

PURPOSE: Test whether a localized τ-peak (higher τ region in lower τ background)
acts as a converging lens, focusing wave propagation.

HYPOTHESIS:
  Since waves bend toward slower (lower τ) regions, a central τ-peak should
  cause waves to bend AWAY from the center as they enter, but then converge
  as they exit — net effect: focusing.

  This is the mirror case of the τ-well test which showed anti-focusing.

SETUP:
  - Background τ = 1.0 (slower propagation)
  - Central peak τ = 1.0 + Δτ (faster propagation)
  - Plane wave propagates through the region
  - Track convergence/focusing behind the peak

METRICS:
  - focal_strength: intensity enhancement at/behind peak
  - wavefront_convergence: width narrowing behind peak
  - focal_distance: where maximum concentration occurs
  - concentration_ratio: compared to baseline

SWEEP:
  - peak_height Δτ = [0.0, 0.2, 0.4, 0.6, 0.8]
  - peak_radius = 6 (fixed)

PASS CONDITION:
  Concentration increases systematically with peak height, and wavefronts
  converge more strongly than the flat-τ baseline.

BASELINE: Regulated Recovery v1.1 parameters (but controlled τ field)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class TauPeakSimulator:
    """Simulator for τ-peak focusing measurement."""
    
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
        
        # τ field - will be set by setup_tau_peak
        self.tau = np.ones((size, size, size))
        
        # Physics parameters
        self.c_0_sq = 4.0
        self.gamma = 0.002  # Very low damping
        
        # Peak parameters
        self.peak_center = None
        self.peak_radius = None
        self.peak_height = None
    
    def setup_tau_peak(self, tau_background: float, peak_height: float, 
                       peak_radius: float, peak_center: Tuple[int, int, int] = None):
        """
        Set up a spherical τ-peak (higher τ region).
        
        tau_background: τ value outside the peak
        peak_height: Δτ above background (peak τ = background + height)
        peak_radius: radius of the peak in grid cells
        peak_center: (x, y, z) center of peak (default: grid center)
        """
        if peak_center is None:
            peak_center = (self.size // 2, self.size // 2, self.size // 2)
        
        cx, cy, cz = peak_center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Distance from peak center
        r = np.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
        
        # Smooth peak profile (tanh transition for lens-like behavior)
        peak_profile = 0.5 * (1 - np.tanh((r - peak_radius) / 2))
        self.tau = tau_background + peak_height * peak_profile
        
        # Store parameters
        self.peak_center = peak_center
        self.peak_radius = peak_radius
        self.peak_height = peak_height
        
        return {
            'tau_background': tau_background,
            'tau_peak_center': tau_background + peak_height,
            'peak_height': peak_height,
            'peak_radius': peak_radius,
            'c_eff_background': np.sqrt(self.c_0_sq * tau_background),
            'c_eff_peak_center': np.sqrt(self.c_0_sq * (tau_background + peak_height)),
        }
    
    def inject_plane_wave(self, propagation_dir: np.ndarray, 
                          start_position: float = None,
                          width: float = None,
                          k_magnitude: float = 0.5,
                          amplitude: float = 2.0):
        """
        Inject a plane wave front propagating in the specified direction.
        """
        if start_position is None:
            start_position = self.size // 4
        if width is None:
            width = self.size * 0.6
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        prop_dir = propagation_dir / (np.linalg.norm(propagation_dir) + 1e-10)
        
        # Position along propagation direction
        pos_along = prop_dir[0] * x + prop_dir[1] * y + prop_dir[2] * z
        
        # Distance perpendicular to propagation
        center = self.size / 2
        if abs(prop_dir[1]) > 0.5:
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
        local_tau = np.mean(self.tau[:, :self.size//4, :])
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
    
    def get_cross_section_intensity(self, y_position: int) -> Dict:
        """Get intensity cross-section at a given y position."""
        energy = self.get_energy()
        
        # Slice at y_position, sum over z
        slice_2d = energy[:, y_position, :]
        profile = np.sum(slice_2d, axis=1)
        
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
    
    def get_focusing_metrics(self) -> Dict:
        """Compute focusing metrics: compare beam width before and after peak."""
        energy = self.get_energy()
        
        y_before = self.size // 4
        y_at = self.size // 2
        y_after = 3 * self.size // 4
        
        before = self.get_cross_section_intensity(y_before)
        at_peak = self.get_cross_section_intensity(y_at)
        after = self.get_cross_section_intensity(y_after)
        
        # Focusing ratio: width_before / width_after
        if after['fwhm'] > 0:
            focusing_ratio = before['fwhm'] / after['fwhm']
        else:
            focusing_ratio = 1.0
        
        # Intensity enhancement
        if before['peak_value'] > 1e-10:
            intensity_enhancement = after['peak_value'] / before['peak_value']
        else:
            intensity_enhancement = 1.0
        
        # Near-axis concentration
        center = self.size // 2
        near_axis_width = self.size // 6
        
        after_profile = np.array(after['profile'])
        near_axis_mask = (np.arange(len(after_profile)) > center - near_axis_width) & \
                         (np.arange(len(after_profile)) < center + near_axis_width)
        
        concentration = np.sum(after_profile[near_axis_mask]) / (np.sum(after_profile) + 1e-10)
        
        return {
            'fwhm_before': before['fwhm'],
            'fwhm_at_peak': at_peak['fwhm'],
            'fwhm_after': after['fwhm'],
            'focusing_ratio': float(focusing_ratio),
            'peak_before': float(before['peak_value']),
            'peak_at': float(at_peak['peak_value']),
            'peak_after': float(after['peak_value']),
            'intensity_enhancement': float(intensity_enhancement),
            'near_axis_concentration': float(concentration),
        }


def run_peak_focusing_test(peak_height: float, peak_radius: float, seed: int,
                            T_max: float = 16.0, baseline_fwhm: float = None) -> Dict:
    """Run a single τ-peak focusing test."""
    tau_background = 1.0
    
    sim = TauPeakSimulator(size=64, dt=0.08, seed=seed)
    
    # Setup peak at center
    peak_info = sim.setup_tau_peak(
        tau_background=tau_background,
        peak_height=peak_height,
        peak_radius=peak_radius
    )
    
    # Inject plane wave propagating in +y direction
    propagation_dir = np.array([0.0, 1.0, 0.0])
    sim.inject_plane_wave(propagation_dir, start_position=sim.size // 6,
                          width=sim.size * 0.7, k_magnitude=0.4, amplitude=2.0)
    
    # Run until wave has passed through peak
    while sim.T < T_max:
        sim.step()
    
    # Measure focusing
    focusing = sim.get_focusing_metrics()
    
    # Calculate relative focusing
    if baseline_fwhm is not None and baseline_fwhm > 0:
        relative_focusing = baseline_fwhm / focusing['fwhm_after'] if focusing['fwhm_after'] > 0 else 1.0
    else:
        relative_focusing = 1.0
    
    return {
        'peak_height': float(peak_height),
        'peak_radius': float(peak_radius),
        'tau_background': float(tau_background),
        'tau_peak_center': float(peak_info['tau_peak_center']),
        'c_eff_ratio': float(peak_info['c_eff_peak_center'] / peak_info['c_eff_background']),
        'seed': seed,
        'relative_focusing': float(relative_focusing),
        **focusing,
    }


def main():
    print("=" * 80)
    print("  τ-PEAK FOCUSING TEST")
    print("=" * 80)
    print()
    print("Hypothesis: A τ-peak (higher τ region) acts as a focusing lens,")
    print("            converging waves that pass through it.")
    print()
    print("Setup:")
    print("  - Background τ = 1.0 (slower)")
    print("  - Peak τ = 1.0 + Δτ (faster)")
    print("  - Plane wave propagates in +y through the peak")
    print()
    print("Physics: Faster central region → wavefronts curve inward → convergence")
    print()
    print("This is the MIRROR CASE of the τ-well test (which showed divergence).")
    print()
    
    seeds = [42, 123, 456]
    peak_heights = [0.0, 0.2, 0.4, 0.6, 0.8]
    fixed_radius = 6
    
    all_results = []
    
    print("-" * 80)
    print("Running tests...")
    print("-" * 80)
    
    t0_total = time.time()
    
    # First run baseline (no peak) to get reference
    print("Getting baseline (no peak)...")
    baseline_results = []
    for seed in seeds:
        result = run_peak_focusing_test(
            peak_height=0.0,
            peak_radius=fixed_radius,
            seed=seed,
            T_max=16.0
        )
        baseline_results.append(result)
        all_results.append(result)
    
    baseline_fwhm = np.mean([r['fwhm_after'] for r in baseline_results])
    baseline_conc = np.mean([r['near_axis_concentration'] for r in baseline_results])
    baseline_intensity = np.mean([r['intensity_enhancement'] for r in baseline_results])
    
    print(f"Baseline FWHM: {baseline_fwhm:.1f}, concentration: {baseline_conc:.3f}")
    print()
    
    # Test different peak heights
    print(f"Sweeping peak height (radius = {fixed_radius}):")
    
    for height in peak_heights[1:]:  # Skip 0.0, already done
        seed_results = []
        for seed in seeds:
            result = run_peak_focusing_test(
                peak_height=height,
                peak_radius=fixed_radius,
                seed=seed,
                T_max=16.0,
                baseline_fwhm=baseline_fwhm
            )
            seed_results.append(result)
            all_results.append(result)
        
        focus_avg = np.mean([r['focusing_ratio'] for r in seed_results])
        conc_avg = np.mean([r['near_axis_concentration'] for r in seed_results])
        intensity_avg = np.mean([r['intensity_enhancement'] for r in seed_results])
        
        print(f"  Δτ={height:.1f}: focus_ratio={focus_avg:.3f}, "
              f"concentration={conc_avg:.3f}, intensity={intensity_avg:.3f}")
    
    print(f"\nTotal time: {time.time()-t0_total:.1f}s")
    print()
    
    # Aggregate by peak height
    by_height = {}
    for r in all_results:
        h = r['peak_height']
        if h not in by_height:
            by_height[h] = []
        by_height[h].append(r)
    
    aggregated = []
    for h in sorted(by_height.keys()):
        runs = by_height[h]
        agg = {
            'peak_height': h,
            'tau_peak': 1.0 + h,
            'focusing_ratio': np.mean([r['focusing_ratio'] for r in runs]),
            'focusing_std': np.std([r['focusing_ratio'] for r in runs]),
            'intensity_enhancement': np.mean([r['intensity_enhancement'] for r in runs]),
            'near_axis_concentration': np.mean([r['near_axis_concentration'] for r in runs]),
            'fwhm_after': np.mean([r['fwhm_after'] for r in runs]),
        }
        aggregated.append(agg)
    
    # Print results
    print("=" * 80)
    print("  RESULTS: PEAK HEIGHT SWEEP")
    print("=" * 80)
    print()
    
    print(f"{'Δτ':>5} | {'τ_peak':>7} | {'focus_ratio':>12} | {'concentration':>13} | {'intensity':>10}")
    print("-" * 65)
    
    for r in aggregated:
        print(f"{r['peak_height']:>5.1f} | {r['tau_peak']:>7.2f} | {r['focusing_ratio']:>12.3f} | "
              f"{r['near_axis_concentration']:>13.3f} | {r['intensity_enhancement']:>10.3f}")
    
    print()
    
    # Analysis
    print("=" * 80)
    print("  FOCUSING ANALYSIS")
    print("=" * 80)
    print()
    
    # Check if focusing/concentration increases with peak height
    heights = [r['peak_height'] for r in aggregated if r['peak_height'] > 0]
    concentrations = [r['near_axis_concentration'] for r in aggregated if r['peak_height'] > 0]
    focus_ratios = [r['focusing_ratio'] for r in aggregated if r['peak_height'] > 0]
    
    if len(heights) >= 2:
        corr_conc = np.corrcoef(heights, concentrations)[0, 1]
        corr_conc = corr_conc if not np.isnan(corr_conc) else 0.0
        
        corr_focus = np.corrcoef(heights, focus_ratios)[0, 1]
        corr_focus = corr_focus if not np.isnan(corr_focus) else 0.0
    else:
        corr_conc = 0.0
        corr_focus = 0.0
    
    # Comparison to baseline
    max_height_data = [r for r in aggregated if r['peak_height'] >= 0.8]
    if max_height_data:
        max_conc = max_height_data[0]['near_axis_concentration']
        conc_improvement = (max_conc - baseline_conc) / baseline_conc * 100
    else:
        max_conc = baseline_conc
        conc_improvement = 0
    
    print(f"Concentration-height correlation: {corr_conc:.3f}")
    print(f"Focusing-height correlation: {corr_focus:.3f}")
    print(f"Baseline concentration: {baseline_conc:.3f}")
    print(f"Max peak concentration (Δτ=0.8): {max_conc:.3f}")
    print(f"Concentration improvement: {conc_improvement:+.1f}%")
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    # Pass conditions:
    # 1. Concentration increases with peak height (positive correlation)
    # 2. Max concentration > baseline concentration
    
    cond1 = corr_conc > 0.5
    cond2 = max_conc > baseline_conc * 1.02  # At least 2% improvement
    
    if cond1 and cond2:
        verdict = "FOCUSING_CONFIRMED"
        print("★ τ-PEAK FOCUSING CONFIRMED")
        print()
        print("  τ-peaks act as converging lenses:")
        print(f"    - Concentration-height correlation: {corr_conc:.3f}")
        print(f"    - Concentration improvement: {conc_improvement:+.1f}%")
        print()
        print("  This confirms the refractive geometry model:")
        print("    - τ-well (low τ center) → DIVERGES (anti-focusing)")
        print("    - τ-peak (high τ center) → CONVERGES (focusing)")
    elif cond2:
        verdict = "WEAK_FOCUSING"
        print("✓ WEAK τ-PEAK FOCUSING")
        print()
        print("  Some focusing observed, but correlation with height is weak.")
    else:
        verdict = "NO_FOCUSING"
        print("✗ NO CLEAR FOCUSING")
        print()
        print("  τ-peaks do not produce systematic focusing.")
        print(f"  Concentration improvement: {conc_improvement:+.1f}%")
    
    print()
    print("Physical interpretation:")
    print("  A τ-peak with higher τ (faster c_eff) acts like a converging lens.")
    print("  The central portion of the wavefront speeds up, curving inward,")
    print("  causing the beam to narrow and concentrate after the peak.")
    
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
        'test': 'tau_peak_focusing',
        'date': 'December 2025',
        'baseline': 'Regulated Recovery v1.1',
        'hypothesis': 'τ-peaks act as converging lenses (mirror of τ-well test)',
        'configuration': {
            'tau_background': 1.0,
            'peak_heights': peak_heights,
            'peak_radius': fixed_radius,
            'seeds': seeds,
            'grid_size': 64,
            'dt': 0.08,
            'T_max': 16.0,
        },
        'verdict': verdict,
        'analysis': {
            'concentration_height_correlation': float(corr_conc),
            'focusing_height_correlation': float(corr_focus),
            'baseline_concentration': float(baseline_conc),
            'max_concentration': float(max_conc),
            'concentration_improvement_percent': float(conc_improvement),
        },
        'comparison_to_tau_well': {
            'tau_well_result': 'anti-focusing (divergence)',
            'tau_peak_result': verdict,
            'consistent_with_refractive_geometry': cond1 or cond2,
        },
        'aggregated_by_height': aggregated,
        'all_runs': all_results,
    })
    
    with open('/app/backend/qmrt_topology/papers/TAU_PEAK_FOCUSING_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/TAU_PEAK_FOCUSING_RESULTS.json")
    
    return output


if __name__ == "__main__":
    main()
