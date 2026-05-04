"""
Fresnel Drag Coefficient Quantification
========================================

PURPOSE: Quantify the medium-dependent drag behavior observed in the boost
invariance test. Derive the Fresnel-like drag coefficient for the QMRT medium.

HYPOTHESIS:
  The regulated QMRT medium exhibits Fresnel-like drag behavior, where
  observed forward/backward propagation speeds depend systematically on
  medium drift velocity while preserving the summed causal speed scale.

CLASSICAL FRESNEL DRAG (Reference):
  In classical optics for a medium with refractive index n moving at velocity v:
    c_forward  = c/n + v(1 - 1/n²)
    c_backward = c/n - v(1 - 1/n²)
  
  The drag coefficient is: f = 1 - 1/n²

QMRT ANALOG:
  We measure c_forward and c_backward at various "medium drift" velocities
  (simulated via boosted perturbations) and fit to:
    c_forward  = c_eff + α·v
    c_backward = c_eff - α·v
  
  Where α is the QMRT drag coefficient analog.

METRICS:
  - medium_velocity (boost strength)
  - c_forward, c_backward
  - speed_sum = c_forward + c_backward (should be ~2·c_eff)
  - speed_difference = c_forward - c_backward
  - drag_coefficient α (from linear fit)
  - asymmetry_vs_velocity_slope
  - fit_quality_R²

BASELINE: Regulated Recovery v1.1 (tau_cap=1.8, damping_to_tau=0.20)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class FresnelDragSimulator:
    """Simulator for Fresnel drag coefficient measurement."""
    
    def __init__(self, size: int = 48, dt: float = 0.10, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.T = 0.0
        self.step_count = 0
        
        # Wave field - quiescent start
        self.psi_r = np.zeros((size, size, size))
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Medium field - constant τ for clean measurement
        self.tau = np.ones((size, size, size))
        
        # Physics parameters
        self.c_0_sq = 4.0
        self.gamma = 0.003  # Very small damping for clean propagation
        
        # Theoretical signal speed
        self.c_eff = np.sqrt(self.c_0_sq)  # 2.0 at tau=1
    
    def inject_point_perturbation(self, center: Tuple[int, int, int],
                                   amplitude: float = 5.0, sigma: float = 2.0):
        """Inject a localized perturbation for light cone measurement."""
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        perturbation = amplitude * np.exp(-r_sq / (2 * sigma**2))
        
        self.psi_r = perturbation.copy()
        self.psi_r_dot = np.zeros_like(self.psi_r)
    
    def apply_medium_boost(self, boost_velocity: float, boost_dir: np.ndarray):
        """
        Simulate a "medium drift" by applying a Galilean-like transformation
        to the wave field momentum.
        
        This creates an effective moving medium frame.
        """
        if abs(boost_velocity) < 1e-6:
            return
        
        boost_dir = boost_dir / (np.linalg.norm(boost_dir) + 1e-10)
        
        # Apply momentum shift to the entire field
        # This simulates viewing from a frame where the medium is moving
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Gradient of psi gives spatial structure
        grad_x = np.roll(self.psi_r, -1, axis=0) - self.psi_r
        grad_y = np.roll(self.psi_r, -1, axis=1) - self.psi_r
        grad_z = np.roll(self.psi_r, -1, axis=2) - self.psi_r
        
        # Add drift momentum
        self.psi_r_dot += boost_velocity * (
            boost_dir[0] * grad_x +
            boost_dir[1] * grad_y +
            boost_dir[2] * grad_z
        )
    
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
    
    def get_directional_front(self, center: Tuple[int, int, int],
                               direction: np.ndarray,
                               threshold_fraction: float = 0.005) -> Tuple[float, float]:
        """
        Measure energy front distance in forward (+direction) and 
        backward (-direction) along a specific axis.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        direction = direction / (np.linalg.norm(direction) + 1e-10)
        
        # Signed distance along direction
        signed_dist = direction[0] * (x - cx) + direction[1] * (y - cy) + direction[2] * (z - cz)
        
        # Select a tube along the direction (within ~4 cells of axis)
        perp_sq = ((x - cx)**2 + (y - cy)**2 + (z - cz)**2) - signed_dist**2
        tube_mask = perp_sq < 16
        
        energy = self.get_energy()
        max_energy = np.max(energy)
        threshold = max_energy * threshold_fraction
        
        above_threshold = (energy > threshold) & tube_mask
        
        if not np.any(above_threshold):
            return 0.0, 0.0
        
        # Forward: max positive distance
        forward_mask = above_threshold & (signed_dist > 0)
        backward_mask = above_threshold & (signed_dist < 0)
        
        forward_dist = float(np.max(signed_dist[forward_mask])) if np.any(forward_mask) else 0.0
        backward_dist = float(np.abs(np.min(signed_dist[backward_mask]))) if np.any(backward_mask) else 0.0
        
        return forward_dist, backward_dist


def run_fresnel_measurement(medium_velocity: float, measure_dir: np.ndarray,
                             seed: int, T_max: float = 12.0,
                             sample_interval: float = 0.5) -> Dict:
    """
    Run a single Fresnel drag measurement using boosted perturbation method.
    
    This matches the methodology from boost_invariance_test.py for consistency.
    """
    sim = FresnelDragSimulator(size=48, dt=0.10, seed=seed)
    
    center = (sim.size // 2, sim.size // 2, sim.size // 2)
    
    # Inject perturbation with initial momentum (same as boost invariance test)
    cx, cy, cz = center
    x, y, z = np.meshgrid(np.arange(sim.size), np.arange(sim.size),
                         np.arange(sim.size), indexing='ij')
    
    r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
    sigma = 2.0
    amplitude = 3.0
    envelope = amplitude * np.exp(-r_sq / (2 * sigma**2))
    
    sim.psi_r = envelope.copy()
    
    # Apply boost as momentum in the perturbation's gradient direction
    if abs(medium_velocity) > 1e-6:
        measure_dir_norm = measure_dir / (np.linalg.norm(measure_dir) + 1e-10)
        
        grad_x = -(x - cx) / sigma**2 * envelope
        grad_y = -(y - cy) / sigma**2 * envelope
        grad_z = -(z - cz) / sigma**2 * envelope
        
        sim.psi_r_dot = medium_velocity * (
            measure_dir_norm[0] * grad_x +
            measure_dir_norm[1] * grad_y +
            measure_dir_norm[2] * grad_z
        )
    
    # Track propagation
    times = []
    forward_dists = []
    backward_dists = []
    
    last_sample = 0.0
    while sim.T < T_max:
        sim.step()
        
        if sim.T - last_sample >= sample_interval:
            last_sample = sim.T
            
            fwd, bwd = sim.get_directional_front(center, measure_dir)
            
            times.append(sim.T)
            forward_dists.append(fwd)
            backward_dists.append(bwd)
    
    # Compute speeds via linear fit
    if len(times) >= 4:
        times_arr = np.array(times)
        fwd_arr = np.array(forward_dists)
        bwd_arr = np.array(backward_dists)
        
        # Use middle portion
        mid_start = len(times) // 4
        mid_end = 3 * len(times) // 4
        
        A = np.vstack([times_arr[mid_start:mid_end], np.ones(mid_end - mid_start)]).T
        
        v_fwd, _ = np.linalg.lstsq(A, fwd_arr[mid_start:mid_end], rcond=None)[0]
        v_bwd, _ = np.linalg.lstsq(A, bwd_arr[mid_start:mid_end], rcond=None)[0]
    else:
        v_fwd, v_bwd = 0.0, 0.0
    
    return {
        'medium_velocity': float(medium_velocity),
        'seed': seed,
        'c_forward': float(v_fwd),
        'c_backward': float(v_bwd),
        'speed_sum': float(v_fwd + v_bwd),
        'speed_difference': float(v_fwd - v_bwd),
        'c_eff_theoretical': float(sim.c_eff),
        'times': times,
        'forward_dists': forward_dists,
        'backward_dists': backward_dists,
    }


def fit_fresnel_drag_coefficient(results: List[Dict]) -> Dict:
    """
    Fit the Fresnel drag coefficient from measurement data.
    
    Model: 
      c_forward  = c_eff + α·v
      c_backward = c_eff - α·v
      
    Where α is the drag coefficient.
    """
    velocities = np.array([r['medium_velocity'] for r in results])
    c_forward = np.array([r['c_forward'] for r in results])
    c_backward = np.array([r['c_backward'] for r in results])
    speed_diff = np.array([r['speed_difference'] for r in results])
    speed_sum = np.array([r['speed_sum'] for r in results])
    
    # Fit 1: speed_difference = 2·α·v
    # Linear regression: speed_diff = slope * v + intercept
    if len(velocities) > 2 and np.std(velocities) > 0:
        A = np.vstack([velocities, np.ones(len(velocities))]).T
        slope_diff, intercept_diff = np.linalg.lstsq(A, speed_diff, rcond=None)[0]
        
        # α = slope_diff / 2
        alpha_from_diff = slope_diff / 2
        
        # R² for the fit
        predicted_diff = slope_diff * velocities + intercept_diff
        ss_res = np.sum((speed_diff - predicted_diff)**2)
        ss_tot = np.sum((speed_diff - np.mean(speed_diff))**2)
        r2_diff = 1 - ss_res / (ss_tot + 1e-10)
    else:
        alpha_from_diff = 0.0
        r2_diff = 0.0
        slope_diff = 0.0
        intercept_diff = 0.0
    
    # Fit 2: Check if speed_sum is constant
    speed_sum_mean = np.mean(speed_sum)
    speed_sum_std = np.std(speed_sum)
    speed_sum_cv = speed_sum_std / (speed_sum_mean + 1e-10)
    
    # Theoretical c_eff
    c_eff = results[0]['c_eff_theoretical'] if results else 2.0
    
    # Expected sum: 2 * c_eff
    sum_ratio = speed_sum_mean / (2 * c_eff)
    
    return {
        'drag_coefficient_alpha': float(alpha_from_diff),
        'asymmetry_vs_velocity_slope': float(slope_diff),
        'asymmetry_intercept': float(intercept_diff),
        'fit_R2': float(r2_diff),
        'speed_sum_mean': float(speed_sum_mean),
        'speed_sum_std': float(speed_sum_std),
        'speed_sum_cv': float(speed_sum_cv),
        'sum_ratio_to_2ceff': float(sum_ratio),
        'c_eff_theoretical': float(c_eff),
    }


def main():
    print("=" * 80)
    print("  FRESNEL DRAG COEFFICIENT QUANTIFICATION")
    print("=" * 80)
    print()
    print("Hypothesis: The QMRT medium exhibits Fresnel-like drag behavior,")
    print("            where c_forward and c_backward depend systematically")
    print("            on medium drift velocity.")
    print()
    print("Model: c_forward  = c_eff + α·v")
    print("       c_backward = c_eff - α·v")
    print()
    print(f"Theoretical c_eff (τ=1): {np.sqrt(4.0):.3f}")
    print()
    
    seeds = [42, 123, 456]
    # Fine-grained velocity sweep for drag coefficient fitting
    medium_velocities = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    measure_dir = np.array([1.0, 0.0, 0.0])  # x-direction
    
    all_results = []
    
    print("-" * 80)
    print("Running measurements...")
    print("-" * 80)
    
    t0_total = time.time()
    
    for v_med in medium_velocities:
        seed_results = []
        for seed in seeds:
            result = run_fresnel_measurement(
                medium_velocity=v_med,
                measure_dir=measure_dir,
                seed=seed,
                T_max=12.0,
                sample_interval=0.5
            )
            seed_results.append(result)
            all_results.append(result)
        
        # Average for this velocity
        c_fwd_avg = np.mean([r['c_forward'] for r in seed_results])
        c_bwd_avg = np.mean([r['c_backward'] for r in seed_results])
        diff_avg = np.mean([r['speed_difference'] for r in seed_results])
        
        print(f"  v_med={v_med:.2f}: c_fwd={c_fwd_avg:.3f}, c_bwd={c_bwd_avg:.3f}, diff={diff_avg:.3f}")
    
    print(f"\nTotal time: {time.time()-t0_total:.1f}s")
    print()
    
    # Aggregate by velocity (average over seeds)
    by_velocity = {}
    for r in all_results:
        v = r['medium_velocity']
        if v not in by_velocity:
            by_velocity[v] = []
        by_velocity[v].append(r)
    
    aggregated = []
    for v in sorted(by_velocity.keys()):
        runs = by_velocity[v]
        agg = {
            'medium_velocity': v,
            'c_forward': np.mean([r['c_forward'] for r in runs]),
            'c_backward': np.mean([r['c_backward'] for r in runs]),
            'speed_sum': np.mean([r['speed_sum'] for r in runs]),
            'speed_difference': np.mean([r['speed_difference'] for r in runs]),
            'c_eff_theoretical': runs[0]['c_eff_theoretical'],
            'c_forward_std': np.std([r['c_forward'] for r in runs]),
            'c_backward_std': np.std([r['c_backward'] for r in runs]),
        }
        aggregated.append(agg)
    
    # Fit drag coefficient
    fit_results = fit_fresnel_drag_coefficient(aggregated)
    
    # Print results
    print("=" * 80)
    print("  RESULTS TABLE")
    print("=" * 80)
    print()
    
    print(f"{'v_med':>6} | {'c_fwd':>8} | {'c_bwd':>8} | {'sum':>8} | {'diff':>8}")
    print("-" * 55)
    
    for r in aggregated:
        print(f"{r['medium_velocity']:>6.2f} | {r['c_forward']:>8.3f} | {r['c_backward']:>8.3f} | "
              f"{r['speed_sum']:>8.3f} | {r['speed_difference']:>8.3f}")
    
    print()
    print("=" * 80)
    print("  FRESNEL DRAG ANALYSIS")
    print("=" * 80)
    print()
    
    c_eff = fit_results['c_eff_theoretical']
    alpha = fit_results['drag_coefficient_alpha']
    
    print(f"Theoretical c_eff: {c_eff:.3f}")
    print()
    print("Drag Coefficient Fit (speed_diff = 2α·v):")
    print(f"  Drag coefficient α: {alpha:.4f}")
    print(f"  Asymmetry slope: {fit_results['asymmetry_vs_velocity_slope']:.4f}")
    print(f"  Fit R²: {fit_results['fit_R2']:.4f}")
    print()
    print("Speed Sum Analysis (should be ~2·c_eff):")
    print(f"  Mean sum: {fit_results['speed_sum_mean']:.3f}")
    print(f"  Expected (2·c_eff): {2 * c_eff:.3f}")
    print(f"  Ratio: {fit_results['sum_ratio_to_2ceff']:.3f}")
    print(f"  CV: {fit_results['speed_sum_cv']:.3f}")
    print()
    
    # Classical Fresnel comparison
    # In classical optics: α = 1 - 1/n²
    # If α ≈ 0.5, then n ≈ √2
    if abs(alpha) > 0.01:
        n_equiv = 1.0 / np.sqrt(1 - abs(alpha)) if abs(alpha) < 1 else float('inf')
        print(f"Classical Fresnel analogy:")
        print(f"  If α = 1 - 1/n², then equivalent n ≈ {n_equiv:.3f}")
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    r2_good = fit_results['fit_R2'] > 0.7
    sum_conserved = fit_results['speed_sum_cv'] < 0.15
    alpha_nonzero = abs(alpha) > 0.01
    
    if r2_good and sum_conserved and alpha_nonzero:
        verdict = "FRESNEL_DRAG_CONFIRMED"
        print("★ FRESNEL-LIKE DRAG CONFIRMED")
        print()
        print(f"  The QMRT medium exhibits Fresnel-like drag with:")
        print(f"    - Drag coefficient α = {alpha:.4f}")
        print(f"    - Linear asymmetry (R² = {fit_results['fit_R2']:.3f})")
        print(f"    - Conserved speed sum (CV = {fit_results['speed_sum_cv']:.3f})")
        print()
        print("  This quantifies the medium-dependent boost asymmetry found")
        print("  in the previous test as a systematic Fresnel-like effect.")
    elif sum_conserved:
        verdict = "WEAK_DRAG"
        print("✓ WEAK FRESNEL-LIKE DRAG")
        print()
        print("  Speed sum is conserved, but drag coefficient is weak or")
        print("  the fit quality is low.")
    else:
        verdict = "NO_FRESNEL_DRAG"
        print("✗ NO CLEAR FRESNEL DRAG")
        print()
        print("  The data does not fit the Fresnel drag model well.")
    
    print()
    print("Physical interpretation:")
    print("  In the Fresnel drag model, the drag coefficient α characterizes")
    print("  how much the medium 'drags' the wave along with it. A non-zero α")
    print("  indicates the medium has a preferred rest frame, consistent with")
    print("  the earlier boost invariance finding of medium-dependent asymmetry.")
    
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
        'test': 'fresnel_drag_coefficient',
        'date': 'December 2025',
        'baseline': 'Regulated Recovery v1.1',
        'hypothesis': 'QMRT medium exhibits Fresnel-like drag behavior',
        'configuration': {
            'medium_velocities': medium_velocities,
            'measure_direction': measure_dir.tolist(),
            'seeds': seeds,
            'grid_size': 48,
            'dt': 0.10,
            'T_max': 10.0,
        },
        'verdict': verdict,
        'drag_analysis': fit_results,
        'aggregated_by_velocity': aggregated,
        'all_runs': all_results,
    })
    
    with open('/app/backend/qmrt_topology/papers/FRESNEL_DRAG_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/FRESNEL_DRAG_RESULTS.json")
    
    return output


if __name__ == "__main__":
    main()
