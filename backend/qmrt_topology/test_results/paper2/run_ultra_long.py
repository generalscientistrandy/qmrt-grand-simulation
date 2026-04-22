#!/usr/bin/env python3
"""
Paper 2: Ultra-Long Simulation (50k steps)
==========================================
Confirms whether S_floor is truly stable or a slow transient.
Also tracks S vs I_TS normalized behavior to check scale separation.
"""

import requests
import json
import numpy as np
from scipy import optimize
import os
import time
from datetime import datetime

API_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://death-world-gen.preview.emergentagent.com')
API = f"{API_URL}/api"

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/paper2"


def plateau_decay(t, S0, S_floor, tau):
    """S(t) = S_floor + (S0 - S_floor) * exp(-t/tau)"""
    return S_floor + (S0 - S_floor) * np.exp(-t / tau)


def fit_plateau(times, values, name="S"):
    """Fit plateau decay model."""
    t = np.array(times)
    v = np.array(values)
    
    mask = np.isfinite(v) & np.isfinite(t) & (t > 0)
    t = t[mask]
    v = v[mask]
    
    if len(t) < 10:
        return None
    
    try:
        popt, pcov = optimize.curve_fit(
            plateau_decay, t, v,
            p0=[v[0], v[-1]*0.5, t[-1]/3],
            bounds=([0, 0, 1], [np.inf, v[0], np.inf]),
            maxfev=10000
        )
        v_pred = plateau_decay(t, *popt)
        ss_res = np.sum((v - v_pred)**2)
        ss_tot = np.sum((v - np.mean(v))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        
        return {
            'V0': popt[0],
            'V_floor': popt[1],
            'tau': popt[2],
            'half_life': popt[2] * np.log(2),
            'r2': r2
        }
    except Exception as e:
        return {'error': str(e)}


def run_ultra_long_simulation(alpha, steps=50000, sample_interval=50):
    """Run ultra-long simulation."""
    config = {
        "dimension": "2d",
        "size": 50,
        "alpha": alpha,
        "lambda_relax": 0.5,
        "gamma_wave": 0.01,
        "steps": steps,
        "sample_interval": sample_interval,
        "seed": 42
    }
    
    try:
        response = requests.post(
            f"{API}/qmrt-sim/longpath/run",
            json=config,
            timeout=600
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None


def analyze_floor_stability(result, alpha):
    """Analyze whether S_floor is stable or still decaying."""
    ts = result['time_series']
    
    times = np.array([p['t'] for p in ts])
    S_values = np.array([p['S_mean'] for p in ts])
    I_TS_values = np.array([p['I_TS'] for p in ts])
    
    n = len(times)
    
    print(f"\n{'='*70}")
    print(f"ULTRA-LONG ANALYSIS: α = {alpha}, {len(ts)} samples")
    print(f"{'='*70}")
    
    # 1. FIT S TO PLATEAU MODEL
    print("\n1. S(t) PLATEAU FIT")
    print("-" * 50)
    
    fit_s = fit_plateau(times, S_values, "S")
    if fit_s and 'r2' in fit_s:
        print(f"  S₀ = {fit_s['V0']:.6f}")
        print(f"  S_floor = {fit_s['V_floor']:.6f}")
        print(f"  τ = {fit_s['tau']:.2f}")
        print(f"  Half-life = {fit_s['half_life']:.2f}")
        print(f"  R² = {fit_s['r2']:.4f}")
    else:
        print(f"  Fit failed: {fit_s}")
    
    # 2. CHECK FLOOR STABILITY
    print("\n2. S_FLOOR STABILITY CHECK")
    print("-" * 50)
    
    # Compare late quarters to see if still decaying
    q1 = slice(0, n//4)
    q2 = slice(n//4, n//2)
    q3 = slice(n//2, 3*n//4)
    q4 = slice(3*n//4, n)
    
    S_q1 = np.mean(S_values[q1])
    S_q2 = np.mean(S_values[q2])
    S_q3 = np.mean(S_values[q3])
    S_q4 = np.mean(S_values[q4])
    
    print(f"  Q1 (t=0-{times[n//4-1]:.0f}):     S = {S_q1:.6f}")
    print(f"  Q2 (t={times[n//4]:.0f}-{times[n//2-1]:.0f}): S = {S_q2:.6f}")
    print(f"  Q3 (t={times[n//2]:.0f}-{times[3*n//4-1]:.0f}): S = {S_q3:.6f}")
    print(f"  Q4 (t={times[3*n//4]:.0f}-{times[-1]:.0f}): S = {S_q4:.6f}")
    
    # Check if Q3→Q4 change is small (indicating floor reached)
    q3_to_q4_change = abs(S_q4 - S_q3) / (S_q3 + 1e-10) * 100
    q2_to_q3_change = abs(S_q3 - S_q2) / (S_q2 + 1e-10) * 100
    
    print(f"\n  Q2→Q3 change: {q2_to_q3_change:.2f}%")
    print(f"  Q3→Q4 change: {q3_to_q4_change:.2f}%")
    
    if q3_to_q4_change < 5:
        floor_status = "STABLE (< 5% change in final quarter)"
    elif q3_to_q4_change < 15:
        floor_status = "NEARLY STABLE (5-15% change)"
    else:
        floor_status = "STILL DECAYING (> 15% change)"
    
    print(f"\n  Floor status: {floor_status}")
    
    # 3. S vs I_TS NORMALIZED COMPARISON
    print("\n3. S vs I_TS NORMALIZED (scale separation check)")
    print("-" * 50)
    
    # Normalize to [0, 1] based on initial values
    S_norm = S_values / (S_values[0] + 1e-10)
    I_TS_norm = I_TS_values / (I_TS_values[0] + 1e-10)
    
    print(f"  S normalized (late): {np.mean(S_norm[q4]):.4f}")
    print(f"  I_TS normalized (late): {np.mean(I_TS_norm[q4]):.4f}")
    
    S_retention = np.mean(S_norm[q4]) * 100
    I_TS_retention = np.mean(I_TS_norm[q4]) * 100
    
    print(f"\n  S retention: {S_retention:.1f}%")
    print(f"  I_TS retention: {I_TS_retention:.1f}%")
    
    if S_retention < 20 and I_TS_retention > 80:
        scale_interpretation = "SCALE SEPARATION: Fine structure (S) degrades, coarse coupling (I_TS) survives"
    elif S_retention < 50 and I_TS_retention > 80:
        scale_interpretation = "PARTIAL SCALE SEPARATION: S degrades significantly more than I_TS"
    else:
        scale_interpretation = "NO CLEAR SCALE SEPARATION"
    
    print(f"  Interpretation: {scale_interpretation}")
    
    # 4. LATE-TIME STATISTICS
    print("\n4. LATE-TIME STATISTICS (final 20%)")
    print("-" * 50)
    
    late = slice(int(0.8*n), n)
    S_late = S_values[late]
    I_TS_late = I_TS_values[late]
    
    print(f"  S: {np.mean(S_late):.6f} ± {np.std(S_late):.6f} (CV = {np.std(S_late)/(np.mean(S_late)+1e-10):.3f})")
    print(f"  I_TS: {np.mean(I_TS_late):.4f} ± {np.std(I_TS_late):.4f} (CV = {np.std(I_TS_late)/(np.mean(I_TS_late)+1e-10):.3f})")
    
    return {
        'alpha': alpha,
        'n_samples': len(ts),
        'total_time': times[-1],
        's_fit': fit_s,
        'floor_stability': {
            'q3_to_q4_change_pct': q3_to_q4_change,
            'status': floor_status
        },
        'scale_separation': {
            'S_retention_pct': S_retention,
            'I_TS_retention_pct': I_TS_retention,
            'interpretation': scale_interpretation
        },
        'late_time_stats': {
            'S_mean': float(np.mean(S_late)),
            'S_std': float(np.std(S_late)),
            'I_TS_mean': float(np.mean(I_TS_late)),
            'I_TS_std': float(np.std(I_TS_late))
        }
    }


def main():
    print("=" * 70)
    print("PAPER 2: ULTRA-LONG SIMULATION (50k steps)")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    alpha = 0.5  # Test at default α first
    steps = 50000
    
    print(f"\nRunning {steps} steps at α = {alpha}...")
    print("(This may take ~30-60 seconds)")
    
    start = time.time()
    result = run_ultra_long_simulation(alpha, steps)
    elapsed = time.time() - start
    
    if result is None:
        print("Simulation failed!")
        return
    
    print(f"Done in {elapsed:.1f}s")
    
    # Analyze
    analysis = analyze_floor_stability(result, alpha)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if analysis['s_fit'] and 'V_floor' in analysis['s_fit']:
        print(f"\n  S_floor estimate: {analysis['s_fit']['V_floor']:.6f}")
        print(f"  Floor status: {analysis['floor_stability']['status']}")
        print(f"  Scale separation: {analysis['scale_separation']['interpretation']}")
    
    # Save results
    output = {
        'config': {'alpha': alpha, 'steps': steps},
        'duration': elapsed,
        'timestamp': datetime.now().isoformat(),
        'analysis': analysis
    }
    
    output_file = f"{OUTPUT_DIR}/ultra_long_50k_alpha{alpha}.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")
    
    # Save time series for plotting
    ts_file = f"{OUTPUT_DIR}/timeseries_ultra_long_alpha{alpha}.json"
    with open(ts_file, 'w') as f:
        json.dump({
            'alpha': alpha,
            'steps': steps,
            'time_series': result['time_series'],
            'analysis': result['analysis']
        }, f)
    print(f"Time series saved to: {ts_file}")


if __name__ == "__main__":
    main()
