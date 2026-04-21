#!/usr/bin/env python3
"""
Paper 2 Alpha Sweep
===================
Maps regimes across α ∈ {0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8}
Since the system is deterministic, single runs are sufficient.
"""

import requests
import json
import numpy as np
import os
import time
from datetime import datetime

API_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://death-world-gen.preview.emergentagent.com')
API = f"{API_URL}/api"

# Base configuration
BASE_CONFIG = {
    "dimension": "2d",
    "size": 50,
    "lambda_relax": 0.5,
    "gamma_wave": 0.01,
    "steps": 6000,
    "sample_interval": 20,
    "seed": 42  # Deterministic - seed doesn't matter
}

# Alpha values to sweep
ALPHA_VALUES = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/paper2"

def run_alpha(alpha):
    """Run a single long-path simulation at given alpha"""
    config = {**BASE_CONFIG, "alpha": alpha}
    
    try:
        response = requests.post(
            f"{API}/qmrt-sim/longpath/run",
            json=config,
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error for α={alpha}: {e}")
        return None

def main():
    print("=" * 70)
    print("PAPER 2: ALPHA SWEEP")
    print("=" * 70)
    print(f"Alpha values: {ALPHA_VALUES}")
    print(f"Steps: {BASE_CONFIG['steps']}, Size: {BASE_CONFIG['size']}")
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    results = []
    total_start = time.time()
    
    for alpha in ALPHA_VALUES:
        print(f"Running α = {alpha:.2f}...", end=" ", flush=True)
        start = time.time()
        result = run_alpha(alpha)
        elapsed = time.time() - start
        
        if result:
            a = result['analysis']
            regime = a['regime']
            print(f"Done in {elapsed:.1f}s - {regime} | structs={a['structure_count_mean']:.1f} | S={a['S_late_mean']:.5f}")
            results.append({
                'alpha': alpha,
                'result': result
            })
        else:
            print("Failed")
    
    total_elapsed = time.time() - total_start
    print()
    print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print()
    
    # ============================================
    # ANALYSIS
    # ============================================
    
    print("=" * 70)
    print("ALPHA SWEEP RESULTS")
    print("=" * 70)
    print()
    
    # Create summary table
    print("REGIME MAP:")
    print("-" * 90)
    print(f"{'α':>6} {'Regime':>12} {'Conf':>6} {'Structs':>8} {'CV':>7} {'S_late':>10} {'I_TS':>8} {'LifeType':>12}")
    print("-" * 90)
    
    sweep_data = []
    for r in results:
        alpha = r['alpha']
        a = r['result']['analysis']
        row = {
            'alpha': alpha,
            'regime': a['regime'],
            'regime_confidence': a['regime_confidence'],
            'structure_count': a['structure_count_mean'],
            'structure_cv': a['structure_count_cv'],
            'S_late': a['S_late_mean'],
            'I_TS_late': a['I_TS_late_mean'],
            'lifetime_type': a['lifetime_distribution_type'],
            'lifetime_mean': a['lifetime_mean'],
            'stabilized': a['structure_count_stabilized'],
            'autocorr_lag5': a['structure_count_autocorr_lag5'],
            'total_births': r['result']['total_births'],
            'total_deaths': r['result']['total_deaths'],
            'total_merges': r['result']['total_merges'],
            'event_rate': a['event_rate_mean']
        }
        sweep_data.append(row)
        
        print(f"{alpha:>6.2f} {a['regime']:>12} {a['regime_confidence']*100:>5.0f}% {a['structure_count_mean']:>8.1f} {a['structure_count_cv']:>7.3f} {a['S_late_mean']:>10.5f} {a['I_TS_late_mean']:>8.4f} {a['lifetime_distribution_type']:>12}")
    
    print()
    
    # Regime transitions
    print("REGIME TRANSITIONS:")
    print("-" * 40)
    regimes = [d['regime'] for d in sweep_data]
    unique_regimes = list(dict.fromkeys(regimes))
    print(f"  Unique regimes seen: {unique_regimes}")
    
    # Find transition points
    transitions = []
    for i in range(1, len(sweep_data)):
        if sweep_data[i]['regime'] != sweep_data[i-1]['regime']:
            transitions.append({
                'from_alpha': sweep_data[i-1]['alpha'],
                'to_alpha': sweep_data[i]['alpha'],
                'from_regime': sweep_data[i-1]['regime'],
                'to_regime': sweep_data[i]['regime']
            })
    
    if transitions:
        print("  Transitions:")
        for t in transitions:
            print(f"    α = {t['from_alpha']:.2f} → {t['to_alpha']:.2f}: {t['from_regime']} → {t['to_regime']}")
    else:
        print(f"  No transitions - all α values in {regimes[0]} regime")
    print()
    
    # Key trends
    print("KEY TRENDS ACROSS α:")
    print("-" * 40)
    alphas = [d['alpha'] for d in sweep_data]
    structs = [d['structure_count'] for d in sweep_data]
    S_vals = [d['S_late'] for d in sweep_data]
    I_TS_vals = [d['I_TS_late'] for d in sweep_data]
    births = [d['total_births'] for d in sweep_data]
    
    # Correlation with alpha
    corr_struct = np.corrcoef(alphas, structs)[0, 1]
    corr_S = np.corrcoef(alphas, S_vals)[0, 1]
    corr_I_TS = np.corrcoef(alphas, I_TS_vals)[0, 1]
    corr_births = np.corrcoef(alphas, births)[0, 1]
    
    print(f"  Structure count vs α: r = {corr_struct:.3f}")
    print(f"  S (late) vs α:        r = {corr_S:.3f}")
    print(f"  I_TS (late) vs α:     r = {corr_I_TS:.3f}")
    print(f"  Total births vs α:    r = {corr_births:.3f}")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    if len(unique_regimes) == 1:
        print(f"All α values in [{ALPHA_VALUES[0]}, {ALPHA_VALUES[-1]}] produce {unique_regimes[0]} regime.")
        print("No regime transitions observed in this parameter range.")
    else:
        print(f"Regime transitions observed across α:")
        for t in transitions:
            print(f"  - {t['from_regime']} → {t['to_regime']} between α={t['from_alpha']:.2f} and α={t['to_alpha']:.2f}")
    print()
    
    # Interpretation
    print("PHYSICAL INTERPRETATION:")
    print("-" * 40)
    if corr_S < -0.5:
        print("  S decreases with α: Higher coupling → less spatial organization")
    elif corr_S > 0.5:
        print("  S increases with α: Higher coupling → more spatial organization")
    else:
        print("  S roughly constant across α")
    
    if corr_births < -0.5:
        print("  Births decrease with α: Higher coupling → less activity")
    elif corr_births > 0.5:
        print("  Births increase with α: Higher coupling → more activity")
    else:
        print("  Birth rate roughly constant across α")
    print()
    
    # ============================================
    # SAVE OUTPUT
    # ============================================
    
    output = {
        'config': BASE_CONFIG,
        'alpha_values': ALPHA_VALUES,
        'total_duration_seconds': total_elapsed,
        'timestamp': datetime.now().isoformat(),
        'sweep_data': sweep_data,
        'regime_transitions': transitions,
        'correlations': {
            'structure_vs_alpha': float(corr_struct),
            'S_vs_alpha': float(corr_S),
            'I_TS_vs_alpha': float(corr_I_TS),
            'births_vs_alpha': float(corr_births)
        },
        'unique_regimes': unique_regimes
    }
    
    output_file = f"{OUTPUT_DIR}/alpha_sweep_6000steps.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to: {output_file}")
    
    # Save individual time series for plotting
    for r in results:
        alpha = r['alpha']
        ts_file = f"{OUTPUT_DIR}/timeseries_alpha{alpha:.1f}.json"
        with open(ts_file, 'w') as f:
            json.dump({
                'alpha': alpha,
                'config': {**BASE_CONFIG, 'alpha': alpha},
                'time_series': r['result']['time_series'],
                'analysis': r['result']['analysis'],
                'all_lifetimes': r['result']['all_lifetimes']
            }, f)
    print(f"Individual time series saved to: {OUTPUT_DIR}/timeseries_alpha*.json")

if __name__ == "__main__":
    main()
