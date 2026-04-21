#!/usr/bin/env python3
"""
Paper 2 Multi-Seed Reproducibility Analysis
============================================
Runs 15 long-path simulations at α=0.5, 6000 steps
Collects per-seed results and analyzes reproducibility
"""

import requests
import json
import numpy as np
import os
import time
from datetime import datetime

API_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://death-world-gen.preview.emergentagent.com')
API = f"{API_URL}/api"

# Configuration
CONFIG = {
    "dimension": "2d",
    "size": 50,
    "alpha": 0.5,
    "lambda_relax": 0.5,
    "gamma_wave": 0.01,
    "steps": 6000,
    "sample_interval": 20
}

N_SEEDS = 15
SEEDS = [12345, 23456, 34567, 45678, 56789, 67890, 78901, 89012, 90123, 
         11111, 22222, 33333, 44444, 55555, 66666][:N_SEEDS]

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/paper2"

def run_single_seed(seed):
    """Run a single long-path simulation"""
    config = {**CONFIG, "seed": seed}
    
    try:
        response = requests.post(
            f"{API}/qmrt-sim/longpath/run",
            json=config,
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error for seed {seed}: {e}")
        return None

def main():
    print("=" * 70)
    print("PAPER 2: MULTI-SEED REPRODUCIBILITY ANALYSIS")
    print("=" * 70)
    print(f"Config: α={CONFIG['alpha']}, steps={CONFIG['steps']}, n_seeds={N_SEEDS}")
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    results = []
    total_start = time.time()
    
    for i, seed in enumerate(SEEDS):
        print(f"Running seed {i+1}/{N_SEEDS} (seed={seed})...", end=" ", flush=True)
        start = time.time()
        result = run_single_seed(seed)
        elapsed = time.time() - start
        
        if result:
            regime = result['analysis']['regime']
            conf = result['analysis']['regime_confidence']
            print(f"Done in {elapsed:.1f}s - {regime} ({conf*100:.0f}%)")
            results.append({
                'seed': seed,
                'result': result
            })
        else:
            print(f"Failed")
    
    total_elapsed = time.time() - total_start
    print()
    print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print()
    
    # ============================================
    # ANALYSIS
    # ============================================
    
    if len(results) < 5:
        print("Not enough successful runs for analysis")
        return
    
    # Extract metrics
    regimes = []
    regime_confs = []
    lifetimes = []
    lifetime_types = []
    structure_counts = []
    structure_cvs = []
    S_lates = []
    I_TS_lates = []
    total_births = []
    total_deaths = []
    total_merges = []
    event_rates = []
    autocorrs_lag5 = []
    
    per_seed_data = []
    
    for r in results:
        a = r['result']['analysis']
        regimes.append(a['regime'])
        regime_confs.append(a['regime_confidence'])
        lifetimes.append(a['lifetime_mean'])
        lifetime_types.append(a['lifetime_distribution_type'])
        structure_counts.append(a['structure_count_mean'])
        structure_cvs.append(a['structure_count_cv'])
        S_lates.append(a['S_late_mean'])
        I_TS_lates.append(a['I_TS_late_mean'])
        total_births.append(r['result']['total_births'])
        total_deaths.append(r['result']['total_deaths'])
        total_merges.append(r['result']['total_merges'])
        autocorrs_lag5.append(a['structure_count_autocorr_lag5'])
        
        # Compute event rate
        n_steps = r['result']['total_timesteps']
        total_events = r['result']['total_births'] + r['result']['total_deaths'] + r['result']['total_merges'] + r['result']['total_splits']
        event_rates.append(total_events / n_steps)
        
        per_seed_data.append({
            'seed': r['seed'],
            'regime': a['regime'],
            'regime_confidence': a['regime_confidence'],
            'lifetime_mean': a['lifetime_mean'],
            'lifetime_type': a['lifetime_distribution_type'],
            'structure_count_mean': a['structure_count_mean'],
            'structure_count_cv': a['structure_count_cv'],
            'S_late_mean': a['S_late_mean'],
            'I_TS_late_mean': a['I_TS_late_mean'],
            'total_births': r['result']['total_births'],
            'total_deaths': r['result']['total_deaths'],
            'total_merges': r['result']['total_merges'],
            'total_splits': r['result']['total_splits'],
            'event_rate': total_events / n_steps,
            'autocorr_lag5': a['structure_count_autocorr_lag5']
        })
    
    # Regime distribution
    regime_counts = {}
    for r in regimes:
        regime_counts[r] = regime_counts.get(r, 0) + 1
    
    dominant_regime = max(regime_counts, key=regime_counts.get)
    regime_agreement = regime_counts[dominant_regime] / len(regimes)
    
    # Lifetime type distribution
    lt_counts = {}
    for lt in lifetime_types:
        lt_counts[lt] = lt_counts.get(lt, 0) + 1
    dominant_lt = max(lt_counts, key=lt_counts.get)
    
    # ============================================
    # PRINT RESULTS
    # ============================================
    
    print("=" * 70)
    print("REPRODUCIBILITY RESULTS")
    print("=" * 70)
    print()
    
    print("REGIME CLASSIFICATION:")
    print("-" * 40)
    for regime, count in sorted(regime_counts.items(), key=lambda x: -x[1]):
        pct = count / len(regimes) * 100
        print(f"  {regime}: {count}/{len(regimes)} ({pct:.0f}%)")
    print(f"  --> Dominant: {dominant_regime} ({regime_agreement*100:.0f}% agreement)")
    print()
    
    print("LIFETIME DISTRIBUTION TYPE:")
    print("-" * 40)
    for lt, count in sorted(lt_counts.items(), key=lambda x: -x[1]):
        pct = count / len(lifetime_types) * 100
        print(f"  {lt}: {count}/{len(lifetime_types)} ({pct:.0f}%)")
    print(f"  --> Consensus: {dominant_lt}")
    print()
    
    print("KEY METRICS (mean ± std across seeds):")
    print("-" * 40)
    print(f"  Lifetime mean:     {np.mean(lifetimes):.3f} ± {np.std(lifetimes):.3f}")
    print(f"  Structure count:   {np.mean(structure_counts):.1f} ± {np.std(structure_counts):.1f}")
    print(f"  Structure CV:      {np.mean(structure_cvs):.3f} ± {np.std(structure_cvs):.3f}")
    print(f"  S (late):          {np.mean(S_lates):.5f} ± {np.std(S_lates):.5f}")
    print(f"  I_TS (late):       {np.mean(I_TS_lates):.4f} ± {np.std(I_TS_lates):.4f}")
    print(f"  Event rate:        {np.mean(event_rates):.2f} ± {np.std(event_rates):.2f} events/step")
    print(f"  Autocorr (lag5):   {np.mean(autocorrs_lag5):.3f} ± {np.std(autocorrs_lag5):.3f}")
    print()
    
    print("EVENT COUNTS (mean ± std):")
    print("-" * 40)
    print(f"  Births:            {np.mean(total_births):.0f} ± {np.std(total_births):.0f}")
    print(f"  Deaths:            {np.mean(total_deaths):.0f} ± {np.std(total_deaths):.0f}")
    print(f"  Merges:            {np.mean(total_merges):.0f} ± {np.std(total_merges):.0f}")
    print()
    
    print("PER-SEED BREAKDOWN:")
    print("-" * 90)
    print(f"{'Seed':>8} {'Regime':>12} {'Conf':>6} {'Life':>7} {'Struct':>7} {'CV':>7} {'S_late':>9} {'Events':>7}")
    print("-" * 90)
    for s in per_seed_data:
        print(f"{s['seed']:>8} {s['regime']:>12} {s['regime_confidence']*100:>5.0f}% {s['lifetime_mean']:>7.2f} {s['structure_count_mean']:>7.1f} {s['structure_count_cv']:>7.3f} {s['S_late_mean']:>9.5f} {s['event_rate']:>7.2f}")
    print()
    
    # ============================================
    # REPRODUCIBILITY ASSESSMENT
    # ============================================
    
    print("=" * 70)
    print("REPRODUCIBILITY ASSESSMENT")
    print("=" * 70)
    
    # Criteria
    regime_stable = regime_agreement >= 0.7
    metrics_stable = np.std(structure_counts) / np.mean(structure_counts) < 0.3
    lifetime_consistent = np.std(lifetimes) / np.mean(lifetimes) < 0.3
    
    print()
    print(f"  Regime agreement ≥ 70%:     {'✓ PASS' if regime_stable else '✗ FAIL'} ({regime_agreement*100:.0f}%)")
    print(f"  Structure count CV < 30%:   {'✓ PASS' if metrics_stable else '✗ FAIL'} ({np.std(structure_counts)/np.mean(structure_counts)*100:.1f}%)")
    print(f"  Lifetime CV < 30%:          {'✓ PASS' if lifetime_consistent else '✗ FAIL'} ({np.std(lifetimes)/np.mean(lifetimes)*100:.1f}%)")
    print()
    
    if regime_stable and metrics_stable:
        print("  --> REPRODUCIBILITY: GOOD")
        print("      Paper 2 foundation is solid. α-sweep can proceed.")
    elif regime_stable:
        print("  --> REPRODUCIBILITY: MODERATE")
        print("      Regime is stable, but metrics show some variation.")
    else:
        print("  --> REPRODUCIBILITY: WEAK")
        print("      Need to investigate before α-sweep.")
    print()
    
    # ============================================
    # SAVE OUTPUT
    # ============================================
    
    output = {
        'config': CONFIG,
        'n_seeds': N_SEEDS,
        'seeds': SEEDS[:len(results)],
        'total_duration_seconds': total_elapsed,
        'timestamp': datetime.now().isoformat(),
        'regime_distribution': regime_counts,
        'dominant_regime': dominant_regime,
        'regime_agreement': regime_agreement,
        'lifetime_type_distribution': lt_counts,
        'lifetime_consensus': dominant_lt,
        'metrics': {
            'lifetime_mean': float(np.mean(lifetimes)),
            'lifetime_std': float(np.std(lifetimes)),
            'structure_count_mean': float(np.mean(structure_counts)),
            'structure_count_std': float(np.std(structure_counts)),
            'S_late_mean': float(np.mean(S_lates)),
            'S_late_std': float(np.std(S_lates)),
            'I_TS_late_mean': float(np.mean(I_TS_lates)),
            'I_TS_late_std': float(np.std(I_TS_lates)),
            'event_rate_mean': float(np.mean(event_rates)),
            'event_rate_std': float(np.std(event_rates)),
            'births_mean': float(np.mean(total_births)),
            'births_std': float(np.std(total_births)),
            'deaths_mean': float(np.mean(total_deaths)),
            'deaths_std': float(np.std(total_deaths)),
            'merges_mean': float(np.mean(total_merges)),
            'merges_std': float(np.std(total_merges)),
        },
        'per_seed_data': per_seed_data,
        'reproducibility': {
            'regime_stable': bool(regime_stable),
            'metrics_stable': bool(metrics_stable),
            'lifetime_consistent': bool(lifetime_consistent),
            'overall': 'good' if (regime_stable and metrics_stable) else ('moderate' if regime_stable else 'weak')
        }
    }
    
    output_file = f"{OUTPUT_DIR}/reproducibility_alpha05_6000steps.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to: {output_file}")
    
    # Save individual time series (for later plotting)
    for r in results:
        seed = r['seed']
        ts_file = f"{OUTPUT_DIR}/timeseries_seed{seed}.json"
        with open(ts_file, 'w') as f:
            json.dump({
                'seed': seed,
                'config': CONFIG,
                'time_series': [ts.dict() if hasattr(ts, 'dict') else ts for ts in r['result']['time_series']],
                'analysis': r['result']['analysis'],
                'all_lifetimes': r['result']['all_lifetimes']
            }, f)
    print(f"Individual time series saved to: {OUTPUT_DIR}/timeseries_seed*.json")

if __name__ == "__main__":
    main()
