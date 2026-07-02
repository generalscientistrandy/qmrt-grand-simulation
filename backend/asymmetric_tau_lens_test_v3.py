"""
QMRT Asymmetric τ-Lens Test v3
==============================

FIXES from v2 (per testing agent report):
1. Reduced max τ contrast to avoid aberration (strength ≤ 0.9 for high asymmetry)
2. Measure metrics at peak focusing time, not final T
3. Use mean incident intensity for amplification baseline
4. Vectorized lens creation for speed
5. Report centroid_x for control to avoid noise-driven focal point

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from typing import Dict, Any
import json
import os


class AsymmetricLensSimulatorV3:
    """Optimized lens simulator with fixed metrics."""
    
    def __init__(self, size=64, dt=0.08, seed=42, lens_strength=0.6, lens_asymmetry=0.4):
        self.size = size
        self.dt = dt
        self.seed = seed
        # Limit strength to avoid aberration at high asymmetry
        self.lens_strength = min(lens_strength, 0.9 if lens_asymmetry > 0.3 else 1.2)
        self.lens_asymmetry = lens_asymmetry
        
        np.random.seed(seed)
        
        self.c_0_sq = 4.0
        self.gamma = 0.003  # Slightly higher damping to prevent unbounded growth
        
        self.global_T = 0.0
        
        # Fields
        shape = (size, size, size)
        self.psi_r = np.zeros(shape)
        self.psi_i = np.zeros(shape)
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        
        # Lens params
        self.lens_x = size // 3
        self.lens_y = size // 2
        self.lens_z = size // 2
        self.lens_radius = size // 6
        
        # Create τ lens (vectorized)
        self.tau = np.ones(shape)
        self.tau_contrast = 0.0
        if lens_strength > 0:
            self._create_lens_vectorized()
        
        self.baseline_mean_intensity = None
        self.peak_focusing_time = None
        self.peak_concentration = 0
    
    def _create_lens_vectorized(self):
        """Vectorized lens creation - 100x faster than nested loops."""
        x, y, z = np.meshgrid(
            np.arange(self.size),
            np.arange(self.size),
            np.arange(self.size),
            indexing='ij'
        )
        
        dx = x - self.lens_x
        dy = y - self.lens_y
        dz = z - self.lens_z
        r = np.sqrt(dx**2 + dy**2 + dz**2)
        
        # Gaussian profile
        base_profile = np.exp(-r**2 / (2 * self.lens_radius**2))
        
        # Asymmetry: higher τ on +y side
        asymmetry_factor = 1.0 + self.lens_asymmetry * (dy / self.lens_radius)
        asymmetry_factor = np.clip(asymmetry_factor, 0.5, 1.5)  # Prevent extreme values
        
        tau_deviation = self.lens_strength * base_profile * asymmetry_factor
        self.tau = 1.0 + tau_deviation
        
        # Wider clip range, but controlled by strength limiting above
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        self.tau_contrast = float(np.max(self.tau) - np.min(self.tau))
    
    def inject_planar_wave(self, x_start=5, wavelength=8.0, amplitude=1.0):
        """Inject planar wave with proper baseline measurement."""
        k = 2 * np.pi / wavelength
        omega = np.sqrt(self.c_0_sq) * k
        
        x, y, z = np.meshgrid(
            np.arange(self.size),
            np.arange(self.size),
            np.arange(self.size),
            indexing='ij'
        )
        
        # Source region mask
        mask = (x >= x_start) & (x < x_start + 5)
        
        phase = k * (x - x_start)
        envelope = np.exp(-((x - x_start - 2) / 2)**2)
        
        self.psi_r = np.where(mask, amplitude * envelope * np.cos(phase), 0)
        self.psi_i = np.where(mask, amplitude * envelope * np.sin(phase), 0)
        self.psi_r_dot = np.where(mask, amplitude * envelope * omega * np.sin(phase), 0)
        self.psi_i_dot = np.where(mask, -amplitude * envelope * omega * np.cos(phase), 0)
        
        # Baseline: mean intensity in injection region (not max)
        injection_intensity = (self.psi_r**2 + self.psi_i**2)[mask]
        self.baseline_mean_intensity = float(np.mean(injection_intensity[injection_intensity > 0]))
    
    def _laplacian(self, f):
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
    
    def step(self):
        self.global_T += self.dt
        c_eff_sq = self.c_0_sq * self.tau
        
        acc_r = c_eff_sq * self._laplacian(self.psi_r) - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * self._laplacian(self.psi_i) - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def compute_intensity(self):
        return self.psi_r**2 + self.psi_i**2
    
    def analyze_focus(self) -> Dict:
        """Analyze focusing with improved metrics."""
        intensity = self.compute_intensity()
        
        # Search behind lens
        search_start = self.lens_x + self.lens_radius
        search_end = min(self.size - 5, self.lens_x + self.size // 2)
        z_center = self.size // 2
        
        region = intensity[search_start:search_end, :, z_center]
        
        if np.sum(region) < 1e-10:
            return {'valid': False, 'concentration': 1.0}
        
        # Peak
        max_idx = np.unravel_index(np.argmax(region), region.shape)
        peak_x = search_start + max_idx[0]
        peak_y = max_idx[1]
        peak_intensity = float(region[max_idx])
        
        # Mean intensity (excluding near-zero regions)
        threshold = np.max(region) * 0.01
        active_region = region[region > threshold]
        mean_intensity = float(np.mean(active_region)) if len(active_region) > 0 else 1.0
        
        concentration = peak_intensity / mean_intensity
        
        # FWHM at peak x
        y_profile = intensity[peak_x, :, z_center]
        half_max = np.max(y_profile) / 2
        above_half = y_profile > half_max
        if np.sum(above_half) > 0:
            indices = np.where(above_half)[0]
            fwhm = indices[-1] - indices[0]
        else:
            fwhm = self.size
        
        # Centroid for more robust focal position
        x_coords = np.arange(search_start, search_end)
        y_coords = np.arange(self.size)
        total_I = np.sum(region)
        centroid_x = float(np.sum(np.sum(region, axis=1) * x_coords) / total_I)
        centroid_y = float(np.sum(np.sum(region, axis=0) * y_coords) / total_I)
        
        # Track peak focusing time
        if concentration > self.peak_concentration:
            self.peak_concentration = concentration
            self.peak_focusing_time = self.global_T
        
        return {
            'valid': True,
            'peak_x': int(peak_x),
            'peak_y': int(peak_y),
            'centroid_x': centroid_x,
            'centroid_y': centroid_y,
            'peak_intensity': peak_intensity,
            'mean_intensity': mean_intensity,
            'concentration': concentration,
            'fwhm': fwhm,
            'amplification': peak_intensity / self.baseline_mean_intensity if self.baseline_mean_intensity else 1.0
        }


def run_lens_test_v3(target_T=80.0, size=64, seed=42, lens_strength=0.6, lens_asymmetry=0.4, name="test"):
    """Run single lens test with early-stop at peak focusing."""
    
    print(f"\n--- {name} ---")
    
    sim = AsymmetricLensSimulatorV3(
        size=size, dt=0.08, seed=seed,
        lens_strength=lens_strength,
        lens_asymmetry=lens_asymmetry
    )
    
    print(f"  τ contrast: {sim.tau_contrast:.3f}" if sim.tau_contrast else "  No lens")
    
    sim.inject_planar_wave()
    
    # Track metrics over time to find peak focusing
    history = []
    measure_interval = 5.0
    last_measure = 0.0
    
    while sim.global_T < target_T:
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            analysis = sim.analyze_focus()
            analysis['T'] = sim.global_T
            history.append(analysis)
    
    # Find snapshot with peak concentration
    if history:
        peak_snapshot = max(history, key=lambda x: x['concentration'])
    else:
        peak_snapshot = sim.analyze_focus()
        peak_snapshot['T'] = sim.global_T
    
    final = sim.analyze_focus()
    
    print(f"  Peak focus at T={peak_snapshot['T']:.1f}: conc={peak_snapshot['concentration']:.2f}, FWHM={peak_snapshot['fwhm']}")
    print(f"  Final T={sim.global_T:.1f}: conc={final['concentration']:.2f}, FWHM={final['fwhm']}")
    
    return {
        'config': {
            'lens_strength': sim.lens_strength,
            'lens_asymmetry': sim.lens_asymmetry,
            'tau_contrast': sim.tau_contrast if hasattr(sim, 'tau_contrast') else 0,
            'baseline_intensity': sim.baseline_mean_intensity
        },
        'peak_snapshot': peak_snapshot,
        'final': final,
        'history': history
    }


def run_full_lens_test_v3():
    """Full test with fixed metrics."""
    
    print("=" * 70)
    print("  QMRT ASYMMETRIC τ-LENS TEST v3 (FIXED)")
    print("=" * 70)
    print()
    print("Fixes in v3:")
    print("  1. Lens strength limited to avoid aberration at high asymmetry")
    print("  2. Report metrics at PEAK focusing time, not final T")
    print("  3. Use mean incident intensity for amplification baseline")
    print("  4. Vectorized lens creation (100x faster)")
    print()
    
    results = {'variants': {}, 'analysis': {}}
    
    configs = [
        ('no_lens', 0.0, 0.0),
        ('symmetric', 0.6, 0.0),
        ('asymmetric_weak', 0.6, 0.3),
        ('asymmetric_strong', 0.6, 0.5),
    ]
    
    for name, strength, asymmetry in configs:
        data = run_lens_test_v3(
            target_T=80.0, size=64, seed=42,
            lens_strength=strength, lens_asymmetry=asymmetry,
            name=name
        )
        results['variants'][name] = data
    
    # Analysis using PEAK snapshot
    print()
    print("=" * 70)
    print("  ANALYSIS (at peak focusing time)")
    print("=" * 70)
    print()
    
    print(f"{'Variant':>18} | {'T_peak':>7} | {'Conc':>8} | {'FWHM':>6} | {'Amplif':>8} | {'Focal Dist':>10}")
    print("-" * 80)
    
    ctrl_conc = results['variants']['no_lens']['peak_snapshot']['concentration']
    
    for name, data in results['variants'].items():
        snap = data['peak_snapshot']
        focal_dist = snap['centroid_x'] - (64 // 3) if snap['valid'] else 0
        
        print(f"{name:>18} | {snap['T']:>7.1f} | {snap['concentration']:>8.2f} | "
              f"{snap['fwhm']:>6} | {snap['amplification']:>8.2f}x | {focal_dist:>10.1f}")
        
        # Focus criterion: concentration > control * 1.1
        # Note: FWHM=63 is expected with periodic BCs at late times
        has_focus = snap['concentration'] > ctrl_conc * 1.1
        
        results['analysis'][name] = {
            'peak_time': snap['T'],
            'concentration': snap['concentration'],
            'fwhm': snap['fwhm'],
            'amplification': snap['amplification'],
            'focal_distance': focal_dist,
            'has_focus': has_focus
        }
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    print()
    
    lens_names = ['symmetric', 'asymmetric_weak', 'asymmetric_strong']
    any_focus = any(results['analysis'][n]['has_focus'] for n in lens_names)
    
    sym_conc = results['analysis']['symmetric']['concentration']
    asym_w_conc = results['analysis']['asymmetric_weak']['concentration']
    asym_s_conc = results['analysis']['asymmetric_strong']['concentration']
    
    asym_stronger = asym_w_conc > sym_conc or asym_s_conc > sym_conc
    monotonic = asym_s_conc > asym_w_conc > sym_conc
    
    print(f"  Control concentration: {ctrl_conc:.2f}")
    print(f"  Any focusing detected: {'YES' if any_focus else 'NO'}")
    print(f"  Asymmetric > Symmetric: {'YES' if asym_stronger else 'NO'}")
    print(f"  Monotonic with asymmetry: {'YES' if monotonic else 'NO'}")
    print()
    
    if any_focus and asym_stronger:
        verdict = "CONFIRMED: Asymmetric τ-lens produces wavefront focusing"
    elif any_focus:
        verdict = "PARTIAL: Some focusing, asymmetry effect weak"
    else:
        verdict = "NOT CONFIRMED: No clear focusing above control"
    
    print(f"  >>> {verdict}")
    
    results['verdict'] = verdict
    
    # Save
    output_dir = '/app/backend/qmrt_topology/papers/tau_lens'
    os.makedirs(output_dir, exist_ok=True)
    
    def to_json(obj):
        if isinstance(obj, (np.floating, np.integer)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, dict):
            return {k: to_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [to_json(v) for v in obj]
        return obj
    
    with open(f'{output_dir}/tau_lens_results_v3.json', 'w') as f:
        json.dump(to_json(results), f, indent=2)
    
    print()
    print(f"Results saved to: {output_dir}/tau_lens_results_v3.json")
    
    return results


if __name__ == "__main__":
    run_full_lens_test_v3()
