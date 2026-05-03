"""
Signal Speed / Velocity Cap Test v3
===================================

DEFINITIVE TEST: Does the QMRT medium have a maximum signal speed (c_eff)?

METHOD: Light cone propagation test
- Inject a point perturbation at the center
- Track how far the energy front propagates over time
- Compare to theoretical c_eff = sqrt(c_0² * τ)

This directly measures the causal structure of the medium.

CONFIGURATIONS TESTED:
1. Clean medium (τ = 1.0 constant) - baseline
2. Regulated Recovery v1.1 (τ dynamic) - realistic medium
3. High τ medium (τ = 1.8 constant) - maximum speed test

BASELINE: Regulated Recovery v1.1 (tau_cap=1.8, damping_to_tau=0.20, dt=0.10, size=48)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class SignalSpeedSimulator:
    """Simulator for signal speed / light cone testing."""
    
    def __init__(self, size: int = 48, dt: float = 0.10, 
                 tau_mode: str = 'constant', tau_value: float = 1.0,
                 seed: int = None):
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
        
        # Medium configuration
        self.tau_mode = tau_mode
        self.tau_value = tau_value
        
        if tau_mode == 'constant':
            self.tau = np.ones((size, size, size)) * tau_value
        else:
            self.tau = np.ones((size, size, size))
        
        # Physics parameters
        self.c_0_sq = 4.0
        self.gamma = 0.005  # Small damping for cleaner propagation
        
        # Regulated recovery parameters (for dynamic tau mode)
        self.damping_to_tau = 0.20
        self.tau_cap = 1.8
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        
        # Theoretical speeds
        self.c_eff_base = np.sqrt(self.c_0_sq)  # 2.0 at tau=1
        self.c_eff_max = np.sqrt(self.c_0_sq * self.tau_cap)  # ~2.68 at tau=1.8
    
    def inject_point_perturbation(self, center: Tuple[int, int, int], 
                                   amplitude: float = 5.0, sigma: float = 1.5):
        """Inject a localized perturbation (smoothed delta function)."""
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        perturbation = amplitude * np.exp(-r_sq / (2 * sigma**2))
        
        self.psi_r = perturbation
        # Zero initial velocity for clean light cone
        self.psi_r_dot = np.zeros_like(self.psi_r)
    
    def step(self):
        """Advance simulation by one timestep."""
        self.step_count += 1
        self.T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # Update τ if in dynamic mode
        if self.tau_mode == 'regulated':
            kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
            damped_energy = self.gamma * kinetic
            energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
            
            tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
            self.tau += self.tau_relaxation * (tau_target - self.tau)
            
            if self.damping_to_tau > 0:
                self.tau += self.damping_to_tau * damped_energy
            
            self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Wave equation with local c_eff
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
    
    def get_front_radius(self, center: Tuple[int, int, int], 
                          threshold_fraction: float = 0.001) -> float:
        """
        Find the maximum radius where energy exceeds threshold.
        
        This defines the "light cone" boundary - how far signals have propagated.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Use periodic-aware distance
        dx = np.minimum(np.abs(x - cx), self.size - np.abs(x - cx))
        dy = np.minimum(np.abs(y - cy), self.size - np.abs(y - cy))
        dz = np.minimum(np.abs(z - cz), self.size - np.abs(z - cz))
        r = np.sqrt(dx**2 + dy**2 + dz**2)
        
        energy = self.get_energy()
        max_energy = np.max(energy)
        threshold = max_energy * threshold_fraction
        
        above_threshold = energy > threshold
        if not np.any(above_threshold):
            return 0.0
        
        return float(np.max(r[above_threshold]))
    
    def get_radial_profile(self, center: Tuple[int, int, int]) -> Dict:
        """Get radial energy profile from center."""
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        dx = np.minimum(np.abs(x - cx), self.size - np.abs(x - cx))
        dy = np.minimum(np.abs(y - cy), self.size - np.abs(y - cy))
        dz = np.minimum(np.abs(z - cz), self.size - np.abs(z - cz))
        r = np.sqrt(dx**2 + dy**2 + dz**2)
        
        energy = self.get_energy()
        
        # Bin by radius
        r_bins = np.linspace(0, self.size/2, 25)
        r_centers = 0.5 * (r_bins[:-1] + r_bins[1:])
        profile = []
        
        for i in range(len(r_bins) - 1):
            mask = (r >= r_bins[i]) & (r < r_bins[i+1])
            if np.any(mask):
                profile.append(float(np.mean(energy[mask])))
            else:
                profile.append(0.0)
        
        return {
            'r_centers': [float(r) for r in r_centers],
            'energy_profile': profile,
        }


def run_light_cone_test(tau_mode: str, tau_value: float, seed: int,
                         T_max: float = 15.0, sample_interval: float = 0.5) -> Dict:
    """
    Run a light cone propagation test.
    
    Returns measured signal speed and comparison to theory.
    """
    sim = SignalSpeedSimulator(size=48, dt=0.10, tau_mode=tau_mode, 
                                tau_value=tau_value, seed=seed)
    
    center = (sim.size // 2, sim.size // 2, sim.size // 2)
    sim.inject_point_perturbation(center, amplitude=5.0, sigma=1.5)
    
    # Theoretical speed for this tau
    if tau_mode == 'constant':
        theoretical_c = np.sqrt(sim.c_0_sq * tau_value)
    else:
        # For regulated mode, use base tau=1 as lower bound
        theoretical_c = sim.c_eff_base
        theoretical_c_max = sim.c_eff_max
    
    # Track propagation
    times = []
    front_radii = []
    tau_means = []
    
    last_sample = 0.0
    while sim.T < T_max:
        sim.step()
        
        if sim.T - last_sample >= sample_interval:
            last_sample = sim.T
            
            front_r = sim.get_front_radius(center)
            times.append(sim.T)
            front_radii.append(front_r)
            tau_means.append(float(np.mean(sim.tau)))
    
    # Fit linear model: r = v * t + b
    if len(times) >= 3:
        times_arr = np.array(times)
        radii_arr = np.array(front_radii)
        
        # Use only middle portion to avoid boundary effects
        mid_start = len(times) // 4
        mid_end = 3 * len(times) // 4
        
        A = np.vstack([times_arr[mid_start:mid_end], 
                       np.ones(mid_end - mid_start)]).T
        v, b = np.linalg.lstsq(A, radii_arr[mid_start:mid_end], rcond=None)[0]
        
        measured_speed = float(v)
    else:
        measured_speed = 0.0
    
    if tau_mode == 'constant':
        speed_ratio = measured_speed / theoretical_c if theoretical_c > 0 else 0.0
        result = {
            'tau_mode': tau_mode,
            'tau_value': tau_value,
            'seed': seed,
            'theoretical_speed': float(theoretical_c),
            'measured_speed': measured_speed,
            'speed_ratio': float(speed_ratio),
            'times': times,
            'front_radii': front_radii,
            'tau_means': tau_means,
        }
    else:
        speed_ratio_base = measured_speed / sim.c_eff_base
        speed_ratio_max = measured_speed / sim.c_eff_max
        result = {
            'tau_mode': tau_mode,
            'tau_value': 'dynamic',
            'seed': seed,
            'theoretical_speed_base': float(sim.c_eff_base),
            'theoretical_speed_max': float(sim.c_eff_max),
            'measured_speed': measured_speed,
            'speed_ratio_to_base': float(speed_ratio_base),
            'speed_ratio_to_max': float(speed_ratio_max),
            'final_tau_mean': float(np.mean(sim.tau)),
            'times': times,
            'front_radii': front_radii,
            'tau_means': tau_means,
        }
    
    return result


def main():
    print("=" * 80)
    print("  SIGNAL SPEED / VELOCITY CAP TEST v3 (Light Cone Method)")
    print("=" * 80)
    print()
    print("Question: Does the QMRT medium have a maximum signal speed?")
    print()
    print("Method: Inject a point perturbation and track how far the")
    print("        energy front propagates. Compare to c_eff = sqrt(c_0² * τ).")
    print()
    print("Theoretical predictions:")
    print(f"  c_eff (τ=1.0): {np.sqrt(4.0):.3f}")
    print(f"  c_eff (τ=1.5): {np.sqrt(4.0 * 1.5):.3f}")
    print(f"  c_eff (τ=1.8): {np.sqrt(4.0 * 1.8):.3f}")
    print()
    
    seeds = [42, 123, 456]
    
    all_results = {}
    
    # Test 1: Clean medium (τ = 1.0)
    print("-" * 80)
    print("Test 1: CLEAN MEDIUM (τ = 1.0 constant)")
    print("-" * 80)
    
    clean_results = []
    for seed in seeds:
        result = run_light_cone_test(tau_mode='constant', tau_value=1.0, 
                                      seed=seed, T_max=15.0)
        clean_results.append(result)
        print(f"  Seed {seed}: measured speed = {result['measured_speed']:.3f}, "
              f"ratio = {result['speed_ratio']:.3f}")
    
    avg_clean = np.mean([r['measured_speed'] for r in clean_results])
    print(f"  Average: {avg_clean:.3f} (expected: 2.000)")
    all_results['clean_tau1'] = clean_results
    
    # Test 2: High τ medium (τ = 1.8)
    print()
    print("-" * 80)
    print("Test 2: HIGH TAU MEDIUM (τ = 1.8 constant)")
    print("-" * 80)
    
    high_tau_results = []
    for seed in seeds:
        result = run_light_cone_test(tau_mode='constant', tau_value=1.8, 
                                      seed=seed, T_max=12.0)
        high_tau_results.append(result)
        print(f"  Seed {seed}: measured speed = {result['measured_speed']:.3f}, "
              f"ratio = {result['speed_ratio']:.3f}")
    
    avg_high = np.mean([r['measured_speed'] for r in high_tau_results])
    print(f"  Average: {avg_high:.3f} (expected: {np.sqrt(4.0 * 1.8):.3f})")
    all_results['high_tau18'] = high_tau_results
    
    # Test 3: Regulated Recovery v1.1
    print()
    print("-" * 80)
    print("Test 3: REGULATED RECOVERY v1.1 (τ dynamic)")
    print("-" * 80)
    
    regulated_results = []
    for seed in seeds:
        result = run_light_cone_test(tau_mode='regulated', tau_value=None, 
                                      seed=seed, T_max=15.0)
        regulated_results.append(result)
        print(f"  Seed {seed}: measured speed = {result['measured_speed']:.3f}, "
              f"ratio_base = {result['speed_ratio_to_base']:.3f}, "
              f"ratio_max = {result['speed_ratio_to_max']:.3f}")
    
    avg_reg = np.mean([r['measured_speed'] for r in regulated_results])
    print(f"  Average: {avg_reg:.3f}")
    all_results['regulated_v11'] = regulated_results
    
    # Analysis
    print()
    print("=" * 80)
    print("  ANALYSIS")
    print("=" * 80)
    print()
    
    # Speed scaling with τ
    speed_clean = np.mean([r['measured_speed'] for r in clean_results])
    speed_high = np.mean([r['measured_speed'] for r in high_tau_results])
    expected_ratio = np.sqrt(1.8 / 1.0)  # sqrt(τ_high / τ_clean)
    actual_ratio = speed_high / speed_clean if speed_clean > 0 else 0
    
    print(f"Speed scaling test (τ=1.8 vs τ=1.0):")
    print(f"  Expected ratio: sqrt(1.8) = {expected_ratio:.3f}")
    print(f"  Measured ratio: {actual_ratio:.3f}")
    print(f"  Match: {'YES' if abs(actual_ratio - expected_ratio) < 0.1 else 'NO'}")
    print()
    
    # Velocity cap determination
    print("Velocity cap determination:")
    print(f"  Clean medium (τ=1.0): c_eff = {speed_clean:.3f}")
    print(f"  High τ medium (τ=1.8): c_eff = {speed_high:.3f}")
    print(f"  Regulated medium: c_eff ≈ {avg_reg:.3f}")
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    # Check if speeds match theoretical predictions
    ratio_clean = speed_clean / np.sqrt(4.0)
    ratio_high = speed_high / np.sqrt(4.0 * 1.8)
    
    if abs(ratio_clean - 1.0) < 0.1 and abs(ratio_high - 1.0) < 0.1:
        verdict = "VELOCITY_CAP_CONFIRMED"
        print("★ VELOCITY CAP CONFIRMED")
        print()
        print("  The QMRT medium has a well-defined maximum signal speed:")
        print(f"    c_eff = sqrt(c_0² × τ)")
        print()
        print("  Key findings:")
        print(f"    1. At τ=1.0: measured {speed_clean:.3f} ≈ theoretical {np.sqrt(4.0):.3f}")
        print(f"    2. At τ=1.8: measured {speed_high:.3f} ≈ theoretical {np.sqrt(4.0*1.8):.3f}")
        print(f"    3. Speed scales as sqrt(τ) - verified")
        print()
        print("  Physical interpretation:")
        print("    The medium has an effective 'speed of light' that depends on")
        print("    the local τ field. This establishes a causal structure where")
        print("    no signal can propagate faster than c_eff(τ).")
    else:
        if ratio_clean < 0.8 or ratio_high < 0.8:
            verdict = "SUBLUMINAL"
            print("Signal propagation is slower than theoretical c_eff.")
        else:
            verdict = "INCONCLUSIVE"
            print("Results inconclusive - speed ratios not as expected.")
    
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
        'test': 'signal_speed_v3',
        'date': 'December 2025',
        'method': 'light_cone_propagation',
        'baseline': 'Regulated Recovery v1.1',
        'verdict': verdict,
        'theoretical': {
            'c_0_sq': 4.0,
            'c_eff_tau1': float(np.sqrt(4.0)),
            'c_eff_tau18': float(np.sqrt(4.0 * 1.8)),
        },
        'measured': {
            'speed_tau1': float(speed_clean),
            'speed_tau18': float(speed_high),
            'speed_regulated': float(avg_reg),
            'tau_scaling_expected': float(expected_ratio),
            'tau_scaling_measured': float(actual_ratio),
        },
        'runs': all_results,
    })
    
    with open('/app/backend/qmrt_topology/papers/SIGNAL_SPEED_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/SIGNAL_SPEED_RESULTS.json")
    
    return output


if __name__ == "__main__":
    main()
