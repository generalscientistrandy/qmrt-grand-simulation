#!/usr/bin/env python3
"""
Phase 3: Localized Driving Experiment
=====================================

Tests the "matter vs space" hypothesis:
- Apply periodic driving ONLY to a small region (the "matter")
- Leave the rest undriven (the "background/space")
- Measure if organization stays localized

Key questions:
1. Does a stable localized structure form?
2. Does it persist over time?
3. Does it spread or stay contained?
4. What's the contrast between driven and undriven regions?
"""

import requests
import json
import time
import numpy as np
from datetime import datetime

API_BASE = "http://localhost:8001/api/qmrt-sim"


def run_localized_experiment(
    size=80,
    driven_radius=8.0,
    steps=30000,
    pulse_interval=500,
    pulse_amplitude=1.5,
    seed=42
):
    """Run a single localized driving experiment."""
    
    config = {
        "dimension": "2d",
        "size": size,
        "alpha": 0.5,
        "lambda_relax": 0.5,
        "gamma_wave": 0.01,
        "steps": steps,
        "sample_interval": 100,
        "driven_region_radius": driven_radius,
        "pulse_interval": pulse_interval,
        "pulse_amplitude": pulse_amplitude,
        "seed": seed
    }
    
    print(f"\n{'='*60}")
    print(f"LOCALIZED DRIVING EXPERIMENT")
    print(f"{'='*60}")
    print(f"Grid: {size}x{size}")
    print(f"Driven region radius: {driven_radius} (area fraction: {np.pi*driven_radius**2/(size**2)*100:.1f}%)")
    print(f"Steps: {steps}, Pulse interval: {pulse_interval}")
    print(f"Pulse amplitude: {pulse_amplitude}")
    print(f"{'='*60}\n")
    
    print("Running simulation...")
    start = time.time()
    
    response = requests.post(
        f"{API_BASE}/longpath/localized-driving",
        json=config,
        timeout=600  # 10 min timeout
    )
    
    if response.status_code != 200:
        print(f"ERROR: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    elapsed = time.time() - start
    
    print(f"Completed in {elapsed:.1f}s ({result['duration_seconds']:.1f}s simulation time)")
    print(f"Total pulses delivered: {result['total_pulses']}")
    
    return result


def analyze_results(result):
    """Analyze and print results."""
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    print(f"\nDriven region: center={result['driven_center']}, radius={result['driven_radius']}")
    print(f"Driven area fraction: {result['driven_area_fraction']*100:.1f}%")
    
    print("\n--- Late-Time Organization (last 20%) ---")
    print(f"  S inside driven region:  {result['late_S_inside']:.6f}")
    print(f"  S outside (background):  {result['late_S_outside']:.6f}")
    print(f"  S CONTRAST (inside/out): {result['late_S_contrast']:.1f}x")
    
    print("\n--- Late-Time Density ---")
    print(f"  rho inside:  {result['late_rho_inside']:.6f}")
    print(f"  rho outside: {result['late_rho_outside']:.6f}")
    print(f"  rho contrast: {result['late_rho_contrast']:.2f}x")
    
    print("\n--- Late-Time Structures ---")
    print(f"  Structures inside:  {result['late_structures_inside']:.1f}")
    print(f"  Structures outside: {result['late_structures_outside']:.1f}")
    
    print("\n--- Localization Metrics ---")
    print(f"  Boundary sharpness: {result['boundary_sharpness']:.2f}")
    print(f"  Spread rate: {result['spread_rate']:.6f} per time unit")
    print(f"  Localization maintained: {result['localization_maintained']}")
    
    print(f"\n--- EXPERIMENT OUTCOME: {result['experiment_outcome'].upper()} ---")
    print("\nInterpretation:")
    for line in result['interpretation']:
        print(f"  {line}")
    
    return result


def run_parameter_sweep():
    """Run experiments with different parameters."""
    
    results = {}
    
    # Test different driven region sizes
    print("\n" + "#"*70)
    print("# PARAMETER SWEEP: Varying driven region radius")
    print("#"*70)
    
    radii = [5.0, 8.0, 12.0, 15.0]
    
    for radius in radii:
        result = run_localized_experiment(
            size=80,
            driven_radius=radius,
            steps=20000,
            pulse_interval=500,
            pulse_amplitude=1.5,
            seed=42
        )
        if result:
            results[f'radius_{radius}'] = result
            analyze_results(result)
    
    # Test different pulse amplitudes
    print("\n" + "#"*70)
    print("# PARAMETER SWEEP: Varying pulse amplitude")
    print("#"*70)
    
    amplitudes = [0.5, 1.0, 1.5, 2.5]
    
    for amp in amplitudes:
        result = run_localized_experiment(
            size=80,
            driven_radius=8.0,
            steps=20000,
            pulse_interval=500,
            pulse_amplitude=amp,
            seed=42
        )
        if result:
            results[f'amp_{amp}'] = result
            analyze_results(result)
    
    return results


def extract_time_series_summary(result):
    """Extract key time series for plotting."""
    ts = result['time_series']
    
    summary = {
        't': [p['t'] for p in ts],
        'S_inside': [p['spatial']['S_inside'] for p in ts],
        'S_outside': [p['spatial']['S_outside'] for p in ts],
        'S_contrast': [p['spatial']['S_contrast'] for p in ts],
        'leakage': [p['spatial']['leakage_fraction'] for p in ts],
        'boundary_gradient': [p['spatial']['boundary_gradient'] for p in ts],
        'structures_inside': [p['structures_inside'] for p in ts],
        'structures_outside': [p['structures_outside'] for p in ts],
    }
    
    return summary


if __name__ == "__main__":
    print("="*70)
    print("PHASE 3: LOCALIZED DRIVING EXPERIMENT")
    print("Testing 'Matter vs Space' Hypothesis")
    print("="*70)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Run main experiment with default parameters
    result = run_localized_experiment(
        size=80,
        driven_radius=10.0,  # ~5% of area driven
        steps=30000,
        pulse_interval=500,
        pulse_amplitude=1.5,
        seed=42
    )
    
    if result:
        analyze_results(result)
        
        # Extract time series
        ts_summary = extract_time_series_summary(result)
        
        # Save results
        output_dir = "/app/backend/qmrt_topology/test_results/phase3"
        
        with open(f"{output_dir}/localized_driving_result.json", 'w') as f:
            json.dump(result, f, indent=2)
        
        with open(f"{output_dir}/localized_driving_timeseries.json", 'w') as f:
            json.dump(ts_summary, f, indent=2)
        
        print(f"\nResults saved to {output_dir}/")
        
        # Quick summary for report
        print("\n" + "="*70)
        print("SUMMARY FOR PAPER 3")
        print("="*70)
        
        if result['experiment_outcome'] == 'localized_stable':
            print("""
FINDING: LOCALIZED ORGANIZATION IS SUPPORTED

The system supports persistent, localized pockets of organization:
- Driven region maintains S = {:.4f}
- Background (undriven) decays to S = {:.6f}
- Contrast ratio: {:.1f}x

This validates the "matter vs space" interpretation:
> Matter = localized sustained organization in an otherwise dissipative medium

The boundary between "matter" and "space" is maintained by continuous
energy throughput in the driven region.
""".format(
                result['late_S_inside'],
                result['late_S_outside'],
                result['late_S_contrast']
            ))
        elif result['experiment_outcome'] == 'spreads':
            print("""
FINDING: ORGANIZATION SPREADS (NO LOCALIZATION)

The system does NOT support localization:
- Organization spreads throughout the grid
- No stable "matter/space" boundary
- Energy throughput affects the entire system

This suggests the medium is fundamentally non-local.
""")
        else:
            print(f"""
FINDING: {result['experiment_outcome'].upper()}

Further investigation needed. Current parameters may be insufficient.
Try:
- Higher pulse amplitude
- Larger driven region
- Different relaxation rates
""")
