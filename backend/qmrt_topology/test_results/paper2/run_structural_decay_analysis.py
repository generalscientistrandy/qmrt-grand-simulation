#!/usr/bin/env python3
"""
Paper 2: Structural Decay Analysis
===================================
Investigates why S declines even when birth-death is balanced.

Key analyses:
1. S(t) curve fitting (exponential, power-law, plateau)
2. S normalized by structure count
3. Spatial correlation length
4. Energy distribution evolution
"""

import requests
import json
import numpy as np
from scipy import optimize
from scipy import stats
from scipy.ndimage import gaussian_filter
import os
import time
from datetime import datetime

API_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://death-world-gen.preview.emergentagent.com')
API = f"{API_URL}/api"

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/paper2"

# ============================================================
# CURVE FITTING FUNCTIONS
# ============================================================

def exponential_decay(t, S0, tau):
    """S(t) = S0 * exp(-t/tau)"""
    return S0 * np.exp(-t / tau)

def power_law_decay(t, S0, beta, t0):
    """S(t) = S0 * (t + t0)^(-beta)"""
    return S0 * np.power(t + t0, -beta)

def plateau_decay(t, S0, S_floor, tau):
    """S(t) = S_floor + (S0 - S_floor) * exp(-t/tau)"""
    return S_floor + (S0 - S_floor) * np.exp(-t / tau)

def fit_s_decay(times, S_values):
    """Fit S(t) to exponential, power-law, and plateau models."""
    t = np.array(times)
    S = np.array(S_values)
    
    # Remove any NaN or zero values
    mask = (S > 0) & np.isfinite(S) & np.isfinite(t) & (t > 0)
    t = t[mask]
    S = S[mask]
    
    if len(t) < 10:
        return None
    
    results = {}
    
    # 1. Exponential decay: S(t) = S0 * exp(-t/tau)
    try:
        popt, pcov = optimize.curve_fit(
            exponential_decay, t, S,
            p0=[S[0], t[-1]/2],
            bounds=([0, 1], [np.inf, np.inf]),
            maxfev=5000
        )
        S_pred = exponential_decay(t, *popt)
        ss_res = np.sum((S - S_pred)**2)
        ss_tot = np.sum((S - np.mean(S))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        results['exponential'] = {
            'params': {'S0': popt[0], 'tau': popt[1]},
            'r2': r2,
            'half_life': popt[1] * np.log(2),
            'asymptotic_S': 0
        }
    except Exception as e:
        results['exponential'] = {'error': str(e)}
    
    # 2. Power-law decay: S(t) = S0 * (t + t0)^(-beta)
    try:
        popt, pcov = optimize.curve_fit(
            power_law_decay, t, S,
            p0=[S[0] * t[0]**0.5, 0.5, 1],
            bounds=([0, 0.01, 0.1], [np.inf, 5, 100]),
            maxfev=5000
        )
        S_pred = power_law_decay(t, *popt)
        ss_res = np.sum((S - S_pred)**2)
        ss_tot = np.sum((S - np.mean(S))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        results['power_law'] = {
            'params': {'S0': popt[0], 'beta': popt[1], 't0': popt[2]},
            'r2': r2,
            'decay_exponent': popt[1],
            'asymptotic_S': 0
        }
    except Exception as e:
        results['power_law'] = {'error': str(e)}
    
    # 3. Plateau decay: S(t) = S_floor + (S0 - S_floor) * exp(-t/tau)
    try:
        popt, pcov = optimize.curve_fit(
            plateau_decay, t, S,
            p0=[S[0], S[-1]*0.5, t[-1]/2],
            bounds=([0, 0, 1], [np.inf, S[0], np.inf]),
            maxfev=5000
        )
        S_pred = plateau_decay(t, *popt)
        ss_res = np.sum((S - S_pred)**2)
        ss_tot = np.sum((S - np.mean(S))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        results['plateau'] = {
            'params': {'S0': popt[0], 'S_floor': popt[1], 'tau': popt[2]},
            'r2': r2,
            'half_life': popt[2] * np.log(2),
            'asymptotic_S': popt[1]
        }
    except Exception as e:
        results['plateau'] = {'error': str(e)}
    
    # Determine best fit
    best_model = None
    best_r2 = -1
    for model, data in results.items():
        if 'r2' in data and data['r2'] > best_r2:
            best_r2 = data['r2']
            best_model = model
    
    results['best_model'] = best_model
    results['best_r2'] = best_r2
    
    return results


def run_extended_simulation(alpha, steps, sample_interval=20):
    """Run a single extended simulation and return raw time series."""
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
            timeout=300
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None


def analyze_structural_decay(result):
    """Comprehensive structural decay analysis."""
    ts = result['time_series']
    
    times = np.array([p['t'] for p in ts])
    S_values = np.array([p['S_mean'] for p in ts])
    structure_counts = np.array([p['total_structures'] for p in ts])
    rho_means = np.array([p['rho_mean'] for p in ts])
    rho_stds = np.array([p['rho_std'] for p in ts])
    I_TS_values = np.array([p['I_TS'] for p in ts])
    
    analysis = {}
    
    # 1. S(t) CURVE FITTING
    print("\n1. S(t) CURVE FITTING")
    print("-" * 50)
    
    fit_results = fit_s_decay(times, S_values)
    analysis['s_decay_fit'] = fit_results
    
    if fit_results:
        for model in ['exponential', 'power_law', 'plateau']:
            if model in fit_results and 'r2' in fit_results[model]:
                data = fit_results[model]
                print(f"\n  {model.upper()}:")
                print(f"    R² = {data['r2']:.4f}")
                for k, v in data['params'].items():
                    print(f"    {k} = {v:.4f}")
                if 'half_life' in data:
                    print(f"    half-life = {data['half_life']:.2f}")
                if 'asymptotic_S' in data:
                    print(f"    asymptotic S = {data['asymptotic_S']:.6f}")
        
        print(f"\n  BEST FIT: {fit_results['best_model']} (R² = {fit_results['best_r2']:.4f})")
    
    # 2. S NORMALIZED BY STRUCTURE COUNT
    print("\n2. S NORMALIZED BY STRUCTURE COUNT (S_per_structure)")
    print("-" * 50)
    
    # Avoid division by zero
    S_per_struct = np.where(structure_counts > 0, 
                           S_values / structure_counts, 
                           np.nan)
    
    # Split into windows
    n = len(times)
    w1, w2, w3 = n//3, 2*n//3, n
    
    early_S_per = S_per_struct[:w1]
    mid_S_per = S_per_struct[w1:w2]
    late_S_per = S_per_struct[w2:]
    
    early_S_per = early_S_per[np.isfinite(early_S_per)]
    mid_S_per = mid_S_per[np.isfinite(mid_S_per)]
    late_S_per = late_S_per[np.isfinite(late_S_per)]
    
    print(f"  Early:  S/N = {np.mean(early_S_per):.6f} ± {np.std(early_S_per):.6f}")
    print(f"  Middle: S/N = {np.mean(mid_S_per):.6f} ± {np.std(mid_S_per):.6f}")
    print(f"  Late:   S/N = {np.mean(late_S_per):.6f} ± {np.std(late_S_per):.6f}")
    
    # Trend
    if len(late_S_per) > 0 and len(early_S_per) > 0:
        rel_change = (np.mean(late_S_per) - np.mean(early_S_per)) / (np.mean(early_S_per) + 1e-10)
        print(f"\n  Relative change (early → late): {rel_change*100:.1f}%")
        
        if abs(rel_change) < 0.1:
            interpretation = "S_per_structure STABLE → organization per unit is constant"
        elif rel_change < -0.1:
            interpretation = "S_per_structure DECLINING → true structural degradation"
        else:
            interpretation = "S_per_structure INCREASING → structures becoming more organized"
        print(f"  Interpretation: {interpretation}")
    
    analysis['s_per_structure'] = {
        'early_mean': float(np.mean(early_S_per)) if len(early_S_per) > 0 else None,
        'mid_mean': float(np.mean(mid_S_per)) if len(mid_S_per) > 0 else None,
        'late_mean': float(np.mean(late_S_per)) if len(late_S_per) > 0 else None,
        'relative_change': float(rel_change) if len(late_S_per) > 0 and len(early_S_per) > 0 else None
    }
    
    # 3. ENERGY DISTRIBUTION EVOLUTION
    print("\n3. ENERGY DISTRIBUTION EVOLUTION")
    print("-" * 50)
    
    # Coefficient of variation of rho (proxy for energy heterogeneity)
    rho_cv = rho_stds / (rho_means + 1e-10)
    
    early_cv = np.mean(rho_cv[:w1])
    mid_cv = np.mean(rho_cv[w1:w2])
    late_cv = np.mean(rho_cv[w2:])
    
    print(f"  ρ coefficient of variation (heterogeneity):")
    print(f"    Early:  CV = {early_cv:.4f}")
    print(f"    Middle: CV = {mid_cv:.4f}")
    print(f"    Late:   CV = {late_cv:.4f}")
    
    if late_cv < early_cv * 0.8:
        energy_interpretation = "Energy HOMOGENIZING → system flattening"
    elif late_cv > early_cv * 1.2:
        energy_interpretation = "Energy CONCENTRATING → peaks forming"
    else:
        energy_interpretation = "Energy distribution STABLE"
    print(f"\n  Interpretation: {energy_interpretation}")
    
    analysis['energy_evolution'] = {
        'early_cv': float(early_cv),
        'mid_cv': float(mid_cv),
        'late_cv': float(late_cv),
        'interpretation': energy_interpretation
    }
    
    # 4. I_TS EVOLUTION (spacetime coupling)
    print("\n4. I_TS EVOLUTION (spacetime coupling)")
    print("-" * 50)
    
    early_I = np.mean(I_TS_values[:w1])
    mid_I = np.mean(I_TS_values[w1:w2])
    late_I = np.mean(I_TS_values[w2:])
    
    print(f"  Early:  I_TS = {early_I:.4f}")
    print(f"  Middle: I_TS = {mid_I:.4f}")
    print(f"  Late:   I_TS = {late_I:.4f}")
    
    analysis['I_TS_evolution'] = {
        'early': float(early_I),
        'mid': float(mid_I),
        'late': float(late_I)
    }
    
    return analysis


def main():
    print("=" * 70)
    print("PAPER 2: STRUCTURAL DECAY ANALYSIS")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    # Run extended simulations at different α values
    alphas = [0.3, 0.5, 0.7]
    steps = 20000  # Much longer to see asymptotic behavior
    
    all_results = {}
    
    for alpha in alphas:
        print(f"\n{'='*70}")
        print(f"ALPHA = {alpha}")
        print(f"{'='*70}")
        
        print(f"Running {steps} steps simulation...", end=" ", flush=True)
        start = time.time()
        result = run_extended_simulation(alpha, steps)
        elapsed = time.time() - start
        print(f"Done in {elapsed:.1f}s")
        
        if result:
            analysis = analyze_structural_decay(result)
            all_results[f'alpha_{alpha}'] = {
                'config': {'alpha': alpha, 'steps': steps},
                'duration': elapsed,
                'analysis': analysis,
                'final_regime': result['analysis']['regime']
            }
            
            # Save individual time series
            ts_file = f"{OUTPUT_DIR}/extended_timeseries_alpha{alpha}.json"
            with open(ts_file, 'w') as f:
                json.dump({
                    'alpha': alpha,
                    'steps': steps,
                    'time_series': result['time_series'],
                    'analysis': result['analysis']
                }, f)
            print(f"\nTime series saved to: {ts_file}")
    
    # Summary across alphas
    print("\n" + "=" * 70)
    print("SUMMARY ACROSS ALPHA VALUES")
    print("=" * 70)
    
    print("\n  S DECAY BEST FIT MODEL:")
    print("-" * 50)
    for alpha in alphas:
        key = f'alpha_{alpha}'
        if key in all_results:
            fit = all_results[key]['analysis']['s_decay_fit']
            if fit and fit['best_model']:
                print(f"  α = {alpha}: {fit['best_model']} (R² = {fit['best_r2']:.4f})")
    
    print("\n  S_PER_STRUCTURE RELATIVE CHANGE:")
    print("-" * 50)
    for alpha in alphas:
        key = f'alpha_{alpha}'
        if key in all_results:
            sps = all_results[key]['analysis']['s_per_structure']
            if sps['relative_change'] is not None:
                change = sps['relative_change'] * 100
                print(f"  α = {alpha}: {change:+.1f}%")
    
    print("\n  ENERGY HOMOGENIZATION:")
    print("-" * 50)
    for alpha in alphas:
        key = f'alpha_{alpha}'
        if key in all_results:
            ee = all_results[key]['analysis']['energy_evolution']
            print(f"  α = {alpha}: {ee['interpretation']}")
    
    # Save comprehensive results
    output_file = f"{OUTPUT_DIR}/structural_decay_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
