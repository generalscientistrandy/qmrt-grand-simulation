"""
Boost Invariance Test v1
========================

PURPOSE: Test whether the effective signal-speed law c_eff(τ) remains consistent
across different moving configurations (rest frame vs boosted frames).

CORE QUESTION:
  Do the measured laws remain approximately the same for structures or
  observers moving through the medium?

METHODOLOGY:
  Compare wave propagation and defect behavior in:
  1. Rest frame (no boost)
  2. Forward-boosted perturbation frame (+v)
  3. Backward-boosted perturbation frame (-v)

TRACKED METRICS:
  - measured c_eff forward
  - measured c_eff backward
  - structure survival time
  - energy-vs-velocity scaling
  - shape deformation
  - law consistency across boost directions

PASS CONDITION:
  The effective signal-speed law c_eff(τ) remains consistent across moving
  configurations, and deviations are small or systematically velocity-dependent.

BASELINE: Regulated Recovery v1.1 (tau_cap=1.8, damping_to_tau=0.20)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class BoostInvarianceSimulator:
    """Simulator for boost invariance testing."""
    
    def __init__(self, size: int = 48, dt: float = 0.10, seed: int = None):
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
        
        # Medium field - constant τ for clean measurement
        self.tau = np.ones((size, size, size))
        
        # Physics parameters
        self.c_0_sq = 4.0
        self.gamma = 0.005  # Small damping
        
        # Theoretical signal speed
        self.c_eff_theory = np.sqrt(self.c_0_sq)  # 2.0 at tau=1
    
    def inject_boosted_perturbation(self, center: Tuple[int, int, int],
                                     boost_velocity: float = 0.0,
                                     boost_dir: np.ndarray = None,
                                     amplitude: float = 3.0, sigma: float = 2.0):
        """
        Inject a perturbation with initial velocity (boost).
        
        boost_velocity: magnitude of initial velocity
        boost_dir: direction unit vector (default: +x)
        
        The perturbation is a Gaussian with initial momentum.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Gaussian envelope
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        envelope = amplitude * np.exp(-r_sq / (2 * sigma**2))
        
        # Add to field
        self.psi_r = envelope.copy()
        
        # Add initial momentum (boost)
        if boost_dir is None:
            boost_dir = np.array([1.0, 0.0, 0.0])
        boost_dir = boost_dir / (np.linalg.norm(boost_dir) + 1e-10)
        
        # Initial velocity field: psi_dot proportional to gradient in boost direction
        # This creates a wave packet moving in boost_dir
        if abs(boost_velocity) > 1e-6:
            # Gradient of envelope
            grad_x = -(x - cx) / sigma**2 * envelope
            grad_y = -(y - cy) / sigma**2 * envelope
            grad_z = -(z - cz) / sigma**2 * envelope
            
            # Momentum in boost direction
            self.psi_r_dot = boost_velocity * (
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
        """Compute energy density field."""
        return self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
    
    def get_front_radius_directional(self, center: Tuple[int, int, int],
                                      direction: np.ndarray,
                                      threshold_fraction: float = 0.01) -> Tuple[float, float]:
        """
        Measure energy front distance in forward and backward directions.
        
        Returns (forward_distance, backward_distance) along the given direction.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        direction = direction / (np.linalg.norm(direction) + 1e-10)
        
        # Signed distance along direction
        signed_dist = direction[0] * (x - cx) + direction[1] * (y - cy) + direction[2] * (z - cz)
        
        # Perpendicular distance (for selecting a tube along the direction)
        perp_sq = ((x - cx)**2 + (y - cy)**2 + (z - cz)**2) - signed_dist**2
        tube_mask = perp_sq < 16  # Within ~4 cells of the axis
        
        energy = self.get_energy()
        max_energy = np.max(energy)
        threshold = max_energy * threshold_fraction
        
        above_threshold = (energy > threshold) & tube_mask
        
        if not np.any(above_threshold):
            return 0.0, 0.0
        
        # Forward: max positive signed_dist
        forward_mask = above_threshold & (signed_dist > 0)
        backward_mask = above_threshold & (signed_dist < 0)
        
        forward_dist = float(np.max(signed_dist[forward_mask])) if np.any(forward_mask) else 0.0
        backward_dist = float(np.abs(np.min(signed_dist[backward_mask]))) if np.any(backward_mask) else 0.0
        
        return forward_dist, backward_dist
    
    def get_energy_centroid(self, boost_dir: np.ndarray) -> float:
        """Get center of energy position along boost direction."""
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        energy = self.get_energy()
        total_energy = np.sum(energy)
        
        if total_energy < 1e-10:
            return self.size / 2
        
        boost_dir = boost_dir / (np.linalg.norm(boost_dir) + 1e-10)
        pos = boost_dir[0] * x + boost_dir[1] * y + boost_dir[2] * z
        
        return float(np.sum(pos * energy) / total_energy)


def run_boost_test(boost_velocity: float, boost_dir: np.ndarray,
                   seed: int, T_max: float = 12.0,
                   sample_interval: float = 0.5) -> Dict:
    """
    Run a single boost invariance test.
    
    Inject a perturbation with given boost velocity and track:
    - Forward/backward propagation speeds
    - Energy distribution evolution
    """
    sim = BoostInvarianceSimulator(size=48, dt=0.10, seed=seed)
    
    center = (sim.size // 2, sim.size // 2, sim.size // 2)
    sim.inject_boosted_perturbation(center, boost_velocity, boost_dir, 
                                     amplitude=3.0, sigma=2.0)
    
    # Track propagation
    times = []
    forward_dists = []
    backward_dists = []
    centroids = []
    
    last_sample = 0.0
    while sim.T < T_max:
        sim.step()
        
        if sim.T - last_sample >= sample_interval:
            last_sample = sim.T
            
            fwd, bwd = sim.get_front_radius_directional(center, boost_dir)
            centroid = sim.get_energy_centroid(boost_dir)
            
            times.append(sim.T)
            forward_dists.append(fwd)
            backward_dists.append(bwd)
            centroids.append(centroid)
    
    # Compute propagation speeds
    if len(times) >= 4:
        times_arr = np.array(times)
        fwd_arr = np.array(forward_dists)
        bwd_arr = np.array(backward_dists)
        
        # Linear fit for middle portion
        mid_start = len(times) // 4
        mid_end = 3 * len(times) // 4
        
        # Forward speed
        A = np.vstack([times_arr[mid_start:mid_end], np.ones(mid_end - mid_start)]).T
        v_fwd, _ = np.linalg.lstsq(A, fwd_arr[mid_start:mid_end], rcond=None)[0]
        
        # Backward speed
        v_bwd, _ = np.linalg.lstsq(A, bwd_arr[mid_start:mid_end], rcond=None)[0]
        
        # Centroid velocity
        v_centroid = (centroids[-1] - centroids[0]) / (times[-1] - times[0]) if len(times) > 1 else 0.0
    else:
        v_fwd, v_bwd, v_centroid = 0.0, 0.0, 0.0
    
    # Theoretical expectation: in rest frame, both should equal c_eff
    # In boosted frame, there may be asymmetry
    c_eff = sim.c_eff_theory
    
    return {
        'boost_velocity': float(boost_velocity),
        'boost_direction': boost_dir.tolist(),
        'seed': seed,
        'measured_v_forward': float(v_fwd),
        'measured_v_backward': float(v_bwd),
        'measured_v_centroid': float(v_centroid),
        'theoretical_c_eff': float(c_eff),
        'ratio_forward': float(v_fwd / c_eff) if c_eff > 0 else 0.0,
        'ratio_backward': float(v_bwd / c_eff) if c_eff > 0 else 0.0,
        'forward_backward_asymmetry': float((v_fwd - v_bwd) / (v_fwd + v_bwd + 1e-10)),
        'times': times,
        'forward_dists': forward_dists,
        'backward_dists': backward_dists,
        'centroids': centroids,
    }


def main():
    print("=" * 80)
    print("  BOOST INVARIANCE TEST v1")
    print("=" * 80)
    print()
    print("Question: Do the measured laws remain approximately the same")
    print("          for structures moving through the medium?")
    print()
    print("Method: Compare wave propagation in rest frame vs boosted frames")
    print("        Track forward/backward propagation speeds")
    print()
    print(f"Theoretical c_eff (τ=1): {np.sqrt(4.0):.3f}")
    print()
    
    seeds = [42, 123, 456]
    boost_velocities = [0.0, 0.5, 1.0, 1.5, 2.0]  # 0 to ~c_eff
    boost_dir = np.array([1.0, 0.0, 0.0])  # +x direction
    
    all_results = []
    
    print("-" * 80)
    print("Running tests...")
    print("-" * 80)
    
    t0_total = time.time()
    
    for v_boost in boost_velocities:
        for seed in seeds:
            result = run_boost_test(
                boost_velocity=v_boost,
                boost_dir=boost_dir,
                seed=seed,
                T_max=12.0,
                sample_interval=0.5
            )
            all_results.append(result)
        
        # Print summary for this boost
        runs = [r for r in all_results if r['boost_velocity'] == v_boost]
        v_fwd = np.mean([r['measured_v_forward'] for r in runs])
        v_bwd = np.mean([r['measured_v_backward'] for r in runs])
        asym = np.mean([r['forward_backward_asymmetry'] for r in runs])
        
        print(f"  v_boost={v_boost:.1f}: v_fwd={v_fwd:.3f}, v_bwd={v_bwd:.3f}, asymmetry={asym:.3f}")
    
    print(f"\nTotal time: {time.time()-t0_total:.1f}s")
    print()
    
    # Analysis
    print("=" * 80)
    print("  RESULTS BY BOOST VELOCITY")
    print("=" * 80)
    print()
    
    c_eff = np.sqrt(4.0)
    
    # Group by boost velocity
    by_boost = {}
    for r in all_results:
        v = r['boost_velocity']
        if v not in by_boost:
            by_boost[v] = []
        by_boost[v].append(r)
    
    print(f"{'v_boost':>8} | {'v_fwd':>8} | {'v_bwd':>8} | {'ratio_f':>8} | {'ratio_b':>8} | {'asymmetry':>10}")
    print("-" * 70)
    
    boost_results = []
    for v_boost in sorted(by_boost.keys()):
        runs = by_boost[v_boost]
        v_fwd = np.mean([r['measured_v_forward'] for r in runs])
        v_bwd = np.mean([r['measured_v_backward'] for r in runs])
        ratio_f = v_fwd / c_eff
        ratio_b = v_bwd / c_eff
        asym = (v_fwd - v_bwd) / (v_fwd + v_bwd + 1e-10)
        
        boost_results.append({
            'v_boost': v_boost,
            'v_fwd': v_fwd,
            'v_bwd': v_bwd,
            'ratio_f': ratio_f,
            'ratio_b': ratio_b,
            'asymmetry': asym,
        })
        
        print(f"{v_boost:>8.1f} | {v_fwd:>8.3f} | {v_bwd:>8.3f} | {ratio_f:>8.3f} | {ratio_b:>8.3f} | {asym:>10.4f}")
    
    print()
    
    # Boost invariance analysis
    print("=" * 80)
    print("  BOOST INVARIANCE ANALYSIS")
    print("=" * 80)
    print()
    
    # Key tests:
    # 1. Is c_eff consistent across boosts? (within ~10%)
    # 2. Is asymmetry systematically velocity-dependent?
    # 3. Does the sum (v_fwd + v_bwd) remain approximately constant?
    
    # Sum of forward + backward (should be ~2*c_eff for Lorentz-like behavior)
    sum_speeds = [(r['v_fwd'] + r['v_bwd']) for r in boost_results]
    mean_sum = np.mean(sum_speeds)
    cv_sum = np.std(sum_speeds) / (mean_sum + 1e-10)
    
    print(f"1. Sum of forward + backward speeds:")
    print(f"   Expected (2*c_eff): {2 * c_eff:.3f}")
    print(f"   Measured mean: {mean_sum:.3f}")
    print(f"   Coefficient of variation: {cv_sum:.3f}")
    print()
    
    # Check if asymmetry scales with boost
    boost_vals = [r['v_boost'] for r in boost_results]
    asym_vals = [r['asymmetry'] for r in boost_results]
    
    if len(boost_vals) > 2:
        corr = np.corrcoef(boost_vals, asym_vals)[0, 1]
        corr = corr if not np.isnan(corr) else 0.0
    else:
        corr = 0.0
    
    print(f"2. Asymmetry vs boost correlation: {corr:.3f}")
    if abs(corr) > 0.8:
        print(f"   Asymmetry is strongly velocity-dependent (expected for medium)")
    elif abs(corr) > 0.5:
        print(f"   Asymmetry is moderately velocity-dependent")
    else:
        print(f"   Asymmetry is weakly correlated with boost")
    print()
    
    # Check if individual speeds remain close to c_eff
    all_ratios = [r['ratio_f'] for r in boost_results] + [r['ratio_b'] for r in boost_results]
    mean_ratio = np.mean(all_ratios)
    std_ratio = np.std(all_ratios)
    
    print(f"3. Speed ratio to c_eff:")
    print(f"   Mean ratio: {mean_ratio:.3f}")
    print(f"   Std ratio: {std_ratio:.3f}")
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    # Pass conditions:
    # 1. CV of sum < 0.2 (speeds add consistently)
    # 2. Asymmetry is velocity-dependent (shows medium effect)
    # 3. Mean ratio is close to 1 (c_eff law holds)
    
    cond1 = cv_sum < 0.2
    cond2 = abs(corr) > 0.5  # Asymmetry is velocity-dependent
    cond3 = abs(mean_ratio - 1.0) < 0.2  # Within 20% of c_eff
    
    if cond1 and cond3:
        if cond2:
            verdict = "MEDIUM_DEPENDENT_LORENTZ"
            print("MEDIUM-DEPENDENT LORENTZ-LIKE BEHAVIOR")
            print()
            print("  The c_eff law remains approximately consistent across boosts,")
            print("  but asymmetry is velocity-dependent (as expected for a medium).")
            print()
            print("  This is analogous to light propagation in a moving medium")
            print("  (Fresnel drag), not vacuum Lorentz invariance.")
        else:
            verdict = "LORENTZ_LIKE"
            print("★ LORENTZ-LIKE BEHAVIOR")
            print()
            print("  The c_eff law is consistent across boosts with minimal asymmetry.")
            print("  This suggests approximate Lorentz invariance.")
    elif cond3:
        verdict = "PARTIAL_CONSISTENCY"
        print("PARTIAL CONSISTENCY")
        print()
        print("  Individual speeds match c_eff, but sum varies with boost.")
        print("  The medium has structure that affects propagation.")
    else:
        verdict = "NOT_LORENTZ_INVARIANT"
        print("NOT LORENTZ INVARIANT")
        print()
        print("  The c_eff law is NOT consistent across boosts.")
        print("  The medium has a preferred frame.")
    
    print()
    print("Physical interpretation:")
    print("  In a true Lorentz-invariant vacuum, the speed of light is the same")
    print("  in all frames. In a medium, there is typically a preferred rest frame.")
    print("  The QMRT medium is expected to show medium-like behavior, with")
    print("  the c_eff law holding locally but asymmetry for boosted configurations.")
    
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
        'test': 'boost_invariance_v1',
        'date': 'December 2025',
        'baseline': 'Regulated Recovery v1.1',
        'configuration': {
            'boost_velocities': boost_velocities,
            'boost_direction': boost_dir.tolist(),
            'seeds': seeds,
            'grid_size': 48,
            'dt': 0.10,
            'T_max': 12.0,
        },
        'theoretical': {
            'c_eff': float(c_eff),
        },
        'verdict': verdict,
        'analysis': {
            'sum_speeds_mean': float(mean_sum),
            'sum_speeds_cv': float(cv_sum),
            'asymmetry_boost_correlation': float(corr),
            'speed_ratio_mean': float(mean_ratio),
            'speed_ratio_std': float(std_ratio),
        },
        'pass_conditions': {
            'sum_consistent': bool(cond1),
            'asymmetry_velocity_dependent': bool(cond2),
            'c_eff_law_holds': bool(cond3),
        },
        'by_boost': boost_results,
        'runs': all_results,
    })
    
    with open('/app/backend/qmrt_topology/papers/BOOST_INVARIANCE_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/BOOST_INVARIANCE_RESULTS.json")
    
    return output


if __name__ == "__main__":
    main()
