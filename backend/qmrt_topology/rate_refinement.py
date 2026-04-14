#!/usr/bin/env python3
"""
QMRT Rate Layer Measurement Refinement
=======================================

Goal: Get R (Rate) to show meaningful variation across parameters.

Current problem:
  R is constant at 0.40 because the measurement isn't sensitive enough.

The rate layer should capture:
  - How fast processes evolve locally
  - How that varies with spatial structure
  
Refined approach:
  1. Longer observation windows
  2. Multiple probe points with different c_eff values
  3. Frequency extraction via FFT
  4. Phase velocity measurement
"""

import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks
import json

from dynamical_medium import DynamicalMediumSimulator


def measure_local_frequency(trace: np.ndarray, dt: float = 0.04) -> dict:
    """
    Extract dominant frequency from a time series using FFT.
    """
    n = len(trace)
    if n < 10:
        return {'freq': 0, 'power': 0, 'quality': 0}
    
    # Remove DC component
    trace = trace - np.mean(trace)
    
    # FFT
    yf = np.abs(fft(trace))[:n//2]
    xf = fftfreq(n, dt)[:n//2]
    
    # Find dominant frequency (excluding DC)
    if len(yf) > 2:
        yf[0] = 0  # Remove DC
        peak_idx = np.argmax(yf)
        freq = xf[peak_idx]
        power = yf[peak_idx]
        
        # Quality: ratio of peak to mean
        quality = power / (np.mean(yf) + 1e-10)
    else:
        freq, power, quality = 0, 0, 0
    
    return {'freq': float(freq), 'power': float(power), 'quality': float(quality)}


def measure_phase_velocity(
    sim: DynamicalMediumSimulator,
    source_x: int,
    source_y: int,
    detect_x: int,
    detect_y: int,
    t_max: int = 150
) -> float:
    """
    Measure phase velocity by timing pulse arrival.
    """
    # Inject pulse at source
    x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size))
    pulse = 3.0 * np.exp(-((x - source_x)**2 + (y - source_y)**2) / 12)
    sim.phi += pulse
    
    # Track amplitude at detector
    threshold = 0.15
    arrival_t = None
    
    for t in range(t_max):
        sim.step()
        if sim.phi[detect_y, detect_x] > threshold:
            arrival_t = t
            break
    
    if arrival_t is None or arrival_t < 1:
        return 0.0
    
    # Distance
    dist = np.sqrt((detect_x - source_x)**2 + (detect_y - source_y)**2)
    
    # Phase velocity
    v_phase = dist / (arrival_t * sim.dt)
    
    return float(v_phase)


def measure_rate_layer_refined(
    sim: DynamicalMediumSimulator,
    t_observe: int = 200,
    n_regions: int = 3
) -> dict:
    """
    Refined rate measurement using multiple methods.
    """
    # Reset simulation
    sim.phi *= 0
    sim.phi_dot *= 0
    
    size = sim.size
    
    # Define probe regions based on expected c_eff structure
    # After medium relaxation, c_eff varies spatially
    regions = {
        'center': (size // 2, size // 2),
        'left': (size // 4, size // 2),
        'right': (3 * size // 4, size // 2),
        'top': (size // 2, size // 4),
        'bottom': (size // 2, 3 * size // 4),
    }
    
    # ===========================================
    # Method 1: Local frequency measurement
    # ===========================================
    
    # Inject broadband excitation
    x, y = np.meshgrid(np.arange(size), np.arange(size))
    for rx, ry in regions.values():
        pulse = 2.0 * np.exp(-((x - rx)**2 + (y - ry)**2) / 25)
        sim.phi += pulse
    
    # Collect time traces
    traces = {name: [] for name in regions}
    
    for t in range(t_observe):
        sim.step()
        for name, (rx, ry) in regions.items():
            traces[name].append(sim.phi[ry, rx])
    
    # Extract frequencies
    frequencies = {}
    for name, trace in traces.items():
        result = measure_local_frequency(np.array(trace), sim.dt)
        frequencies[name] = result
    
    # Frequency variation score
    freq_values = [f['freq'] for f in frequencies.values() if f['freq'] > 0]
    if len(freq_values) >= 2:
        freq_mean = np.mean(freq_values)
        freq_std = np.std(freq_values)
        freq_cv = freq_std / (freq_mean + 1e-10)
        freq_variation = min(1.0, freq_cv * 3)  # Scale up
    else:
        freq_variation = 0.3
    
    # ===========================================
    # Method 2: Phase velocity across regions
    # ===========================================
    
    # Reset
    sim.phi *= 0.1
    sim.phi_dot *= 0.1
    
    velocities = []
    
    # Measure velocity in different directions
    paths = [
        ((size//4, size//2), (3*size//4, size//2)),  # Left to right
        ((size//2, size//4), (size//2, 3*size//4)),  # Top to bottom
    ]
    
    for (sx, sy), (dx, dy) in paths:
        v = measure_phase_velocity(sim, sx, sy, dx, dy, t_max=120)
        if v > 0:
            velocities.append(v)
        # Reset between measurements
        sim.phi *= 0.2
        sim.phi_dot *= 0.2
    
    if len(velocities) >= 1:
        v_mean = np.mean(velocities)
        # Compare to expected c_0
        v_ratio = v_mean / sim.c_0
        velocity_score = min(1.0, v_ratio)  # Higher velocity = faster rate
    else:
        velocity_score = 0.3
    
    # ===========================================
    # Method 3: C_eff variation as proxy
    # ===========================================
    
    c_eff = sim.compute_c_eff()
    c_mean = np.mean(c_eff)
    c_std = np.std(c_eff)
    c_cv = c_std / (c_mean + 1e-10)
    
    # C_eff variation indicates rate variation potential
    c_eff_score = min(1.0, c_cv * 5)
    
    # ===========================================
    # Combined Rate Score
    # ===========================================
    
    # Weight the methods
    R = 0.35 * freq_variation + 0.35 * velocity_score + 0.30 * c_eff_score
    R = float(np.clip(R, 0, 1))
    
    return {
        'R': R,
        'freq_variation': float(freq_variation),
        'velocity_score': float(velocity_score),
        'c_eff_score': float(c_eff_score),
        'frequencies': {k: v['freq'] for k, v in frequencies.items()},
        'velocities': velocities,
        'c_eff_mean': float(c_mean),
        'c_eff_std': float(c_std),
    }


def test_rate_refinement():
    """
    Test refined rate measurement across parameters.
    """
    print("=" * 70)
    print("RATE LAYER MEASUREMENT REFINEMENT")
    print("=" * 70)
    print()
    
    # Parameter grid
    alphas = [0.2, 0.4, 0.6, 0.8]
    lambdas = [0.5, 1.0, 2.0]
    
    results = []
    
    print("Running rate measurements...")
    print()
    
    for alpha in alphas:
        for lam in lambdas:
            sim = DynamicalMediumSimulator(
                size=80,
                beta=alpha,
                lambda_relax=lam,
                D_medium=0.1,
                gamma_wave=0.01,
            )
            
            # Let medium equilibrate
            for _ in range(50):
                sim.step()
            
            rate = measure_rate_layer_refined(sim, t_observe=150)
            
            print(f"  α={alpha}, λ={lam}: R={rate['R']:.3f} "
                  f"(freq_var={rate['freq_variation']:.2f}, "
                  f"vel={rate['velocity_score']:.2f}, "
                  f"c_eff={rate['c_eff_score']:.2f})")
            
            results.append({
                'alpha': alpha,
                'lambda': lam,
                **rate
            })
    
    # Analyze variation
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    
    R_values = [r['R'] for r in results]
    R_mean = np.mean(R_values)
    R_std = np.std(R_values)
    R_range = max(R_values) - min(R_values)
    
    print(f"\nR statistics:")
    print(f"  Mean: {R_mean:.3f}")
    print(f"  Std:  {R_std:.3f}")
    print(f"  Range: {R_range:.3f}")
    print(f"  Min:  {min(R_values):.3f}")
    print(f"  Max:  {max(R_values):.3f}")
    
    if R_range > 0.1:
        print(f"\n✅ R shows meaningful variation ({R_range:.2f} range)")
    else:
        print(f"\n⚠️  R variation still limited ({R_range:.2f} range)")
    
    # Check correlation with alpha and lambda
    alphas_arr = np.array([r['alpha'] for r in results])
    lambdas_arr = np.array([r['lambda'] for r in results])
    R_arr = np.array(R_values)
    
    from scipy.stats import spearmanr
    rho_R_alpha, _ = spearmanr(R_arr, alphas_arr)
    rho_R_lambda, _ = spearmanr(R_arr, lambdas_arr)
    
    print(f"\nParameter correlations:")
    print(f"  ρ(R, α) = {rho_R_alpha:.3f}")
    print(f"  ρ(R, λ) = {rho_R_lambda:.3f}")
    
    # Best and worst configs
    best_idx = np.argmax(R_values)
    worst_idx = np.argmin(R_values)
    
    print(f"\nBest R:  α={results[best_idx]['alpha']}, λ={results[best_idx]['lambda']} → R={R_values[best_idx]:.3f}")
    print(f"Worst R: α={results[worst_idx]['alpha']}, λ={results[worst_idx]['lambda']} → R={R_values[worst_idx]:.3f}")
    
    # Save
    output = {
        'results': results,
        'summary': {
            'R_mean': float(R_mean),
            'R_std': float(R_std),
            'R_range': float(R_range),
            'rho_R_alpha': float(rho_R_alpha) if not np.isnan(rho_R_alpha) else 0,
            'rho_R_lambda': float(rho_R_lambda) if not np.isnan(rho_R_lambda) else 0,
        }
    }
    
    with open('/app/backend/qmrt_topology/rate_refinement_test.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\nSaved: rate_refinement_test.json")
    
    return results


if __name__ == "__main__":
    test_rate_refinement()
