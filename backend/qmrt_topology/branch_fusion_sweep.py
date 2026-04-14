#!/usr/bin/env python3
"""
QMRT Branch-Fusion Parameter Sweep
===================================

Integrates the Temporal Web framework with the Branch-Fusion framework.
Scans (lambda, alpha, disorder) parameter space to identify regimes where:
  - S_time-web > 0.3 (temporal web coherence threshold)
  - I_TS > 0.5 (spatial-temporal interaction threshold)
  - Spacetime candidate regime emerges

Uses both 2-clock (osc+decay) and 3-clock (osc+decay+event) temporal webs.
"""

import numpy as np
from scipy.stats import spearmanr
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json
import matplotlib.pyplot as plt

# Import from existing frameworks
from temporal_web import (
    ClockScores, analyze_temporal_web, compute_spatial_temporal_interaction,
    classify_regime, compute_clock_usefulness
)
from branch_fusion import (
    BranchScores, FusionMetrics, compute_fusion, 
    compute_space_score, compute_coherence_score, compute_interact_score
)


# ============================================================
# PARAMETER-DEPENDENT CLOCK SCORE MODELS
# ============================================================

def model_oscillator_scores(
    alpha: float,     # backreaction coupling
    lam: float,       # relaxation rate
    disorder: float   # medium disorder
) -> ClockScores:
    """
    Model how oscillator clock scores vary with parameters.
    
    Based on prior test results:
    - Higher alpha → stronger structure → higher D
    - Higher lambda → faster relaxation → slightly lower Q (less memory)
    - Higher disorder → less coherent → lower R, higher C
    """
    # Base values from empirical tests
    D_base = 0.55
    Q_base = 0.112
    I_base = 0.70
    C_base = 0.10
    R_base = 0.90
    
    # Parameter effects
    D = D_base + 0.15 * alpha - 0.05 * disorder
    Q = Q_base + 0.08 * alpha - 0.05 * disorder - 0.02 * lam
    I = I_base - 0.05 * disorder
    C = C_base + 0.08 * disorder  # More disorder → more circular
    R = R_base - 0.10 * disorder
    
    return ClockScores(
        D=float(np.clip(D, 0, 1)),
        Q=float(np.clip(Q, 0, 1)),
        I=float(np.clip(I, 0, 1)),
        C=float(np.clip(C, 0, 1)),
        R=float(np.clip(R, 0, 1)),
    )


def model_decay_scores(
    alpha: float,
    lam: float,
    disorder: float
) -> ClockScores:
    """
    Model how decay clock scores vary with parameters.
    
    Based on prior test results:
    - Higher alpha → stronger localization → higher D
    - Decay is very reproducible, disorder reduces it
    - Lambda affects metastable lifetime
    """
    D_base = 0.82
    Q_base = 0.0  # Decay doesn't improve collapse
    I_base = 0.65
    C_base = 0.05
    R_base = 0.99
    
    # Parameter effects
    D = D_base + 0.10 * alpha - 0.08 * disorder
    Q = Q_base  # Stays zero
    I = I_base + 0.05 * alpha - 0.05 * disorder
    C = C_base + 0.03 * disorder
    R = R_base - 0.05 * disorder - 0.02 * lam
    
    return ClockScores(
        D=float(np.clip(D, 0, 1)),
        Q=float(np.clip(Q, 0, 1)),
        I=float(np.clip(I, 0, 1)),
        C=float(np.clip(C, 0, 1)),
        R=float(np.clip(R, 0, 1)),
    )


def model_event_scores(
    alpha: float,
    lam: float,
    disorder: float
) -> ClockScores:
    """
    Model how event clock scores vary with parameters.
    
    Event clocks are weak - primarily transport diagnostics.
    - Higher disorder → more events but less meaningful
    """
    D_base = 0.10
    Q_base = 0.0
    I_base = 0.40
    C_base = 0.02
    R_base = 0.85
    
    D = D_base + 0.05 * alpha
    Q = Q_base
    I = I_base - 0.10 * disorder
    C = C_base + 0.05 * disorder
    R = R_base - 0.08 * disorder
    
    return ClockScores(
        D=float(np.clip(D, 0, 1)),
        Q=float(np.clip(Q, 0, 1)),
        I=float(np.clip(I, 0, 1)),
        C=float(np.clip(C, 0, 1)),
        R=float(np.clip(R, 0, 1)),
    )


def model_spatial_score(
    alpha: float,
    lam: float,
    disorder: float
) -> float:
    """
    Model spatial branch score.
    
    From prior tests:
    - Optimal at moderate alpha (0.4-0.6)
    - Higher lambda → better relaxation → better geodesics
    - Disorder reduces spatial coherence
    """
    # Spatial score peaks around alpha=0.5
    alpha_effect = 1 - 2 * (alpha - 0.5)**2
    lam_effect = 0.8 + 0.2 * np.tanh(lam - 1)
    disorder_penalty = 1 - 0.3 * disorder
    
    S_space = 0.85 * alpha_effect * lam_effect * disorder_penalty
    return float(np.clip(S_space, 0, 1))


def model_coherence_score(
    alpha: float,
    lam: float,
    disorder: float
) -> float:
    """
    Model coherence branch score.
    
    From prior tests:
    - Higher lambda → faster equilibration → higher coherence
    - Moderate alpha is best
    - Disorder reduces coherence
    """
    lam_effect = 0.6 + 0.3 * np.tanh(lam - 1)
    alpha_effect = 1 - (alpha - 0.5)**2
    disorder_penalty = 1 - 0.4 * disorder
    
    S_coh = 0.75 * lam_effect * alpha_effect * disorder_penalty
    return float(np.clip(S_coh, 0, 1))


def model_interact_score(
    alpha: float,
    lam: float,
    disorder: float
) -> float:
    """
    Model interaction branch score.
    
    From prior tests:
    - Higher alpha → stronger attraction
    - Lambda has moderate effect
    - Disorder reduces structured interaction
    """
    alpha_effect = alpha  # Linear increase
    lam_effect = 0.7 + 0.2 * np.tanh(lam - 1)
    disorder_penalty = 1 - 0.25 * disorder
    
    S_interact = alpha_effect * lam_effect * disorder_penalty
    return float(np.clip(S_interact, 0, 1))


def model_rank_values(
    alpha: float,
    disorder: float
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """
    Generate simulated rank values for consistency matrix.
    
    Returns (rank_values_2clock, rank_values_3clock)
    """
    # Base differentiation across regions
    osc_base = np.array([10, 5, 4])
    decay_base = np.array([9.13, 7.29, 6.98])
    event_base = np.array([1, 35, 1])
    
    # Apply parameter effects
    osc = osc_base * (1 + 0.2 * alpha - 0.1 * disorder)
    decay = decay_base * (1 + 0.15 * alpha - 0.1 * disorder)
    event = event_base * (1 - 0.2 * disorder)  # Events degrade with disorder
    
    rank_2clock = {'osc': osc, 'decay': decay}
    rank_3clock = {'osc': osc, 'decay': decay, 'event': event}
    
    return rank_2clock, rank_3clock


# ============================================================
# MAIN SWEEP FUNCTION
# ============================================================

def run_parameter_sweep(
    alphas: List[float],
    lambdas: List[float],
    disorders: List[float],
) -> List[Dict]:
    """
    Run full parameter sweep and compute temporal web + branch fusion metrics.
    """
    results = []
    
    total = len(alphas) * len(lambdas) * len(disorders)
    count = 0
    
    for alpha in alphas:
        for lam in lambdas:
            for disorder in disorders:
                count += 1
                
                # Generate clock scores
                osc = model_oscillator_scores(alpha, lam, disorder)
                decay = model_decay_scores(alpha, lam, disorder)
                event = model_event_scores(alpha, lam, disorder)
                
                clock_data_2 = {'osc': osc, 'decay': decay}
                clock_data_3 = {'osc': osc, 'decay': decay, 'event': event}
                
                # Generate rank values
                rank_2, rank_3 = model_rank_values(alpha, disorder)
                
                # Analyze temporal webs
                web_2 = analyze_temporal_web(clock_data_2, rank_2)
                web_3 = analyze_temporal_web(clock_data_3, rank_3)
                
                # Get spatial score
                S_space = model_spatial_score(alpha, lam, disorder)
                
                # Compute interactions
                interaction_2 = compute_spatial_temporal_interaction(web_2.S_time_web, S_space)
                interaction_3 = compute_spatial_temporal_interaction(web_3.S_time_web, S_space)
                
                # Classify regimes
                min_U_2 = min(web_2.usefulness.values()) if web_2.usefulness else 0
                min_U_3 = min(web_3.usefulness.values()) if web_3.usefulness else 0
                regime_2 = classify_regime(S_space, web_2.S_time_web, interaction_2['I_TS'], min_U_2)
                regime_3 = classify_regime(S_space, web_3.S_time_web, interaction_3['I_TS'], min_U_3)
                
                # Compute branch fusion scores
                S_coh = model_coherence_score(alpha, lam, disorder)
                S_interact = model_interact_score(alpha, lam, disorder)
                
                # Use temporal web as clock score for branch fusion
                branches_2 = BranchScores(
                    space=S_space,
                    clock=web_2.S_time_web,  # Use temporal web score
                    interact=S_interact,
                    coherence=S_coh
                )
                branches_3 = BranchScores(
                    space=S_space,
                    clock=web_3.S_time_web,
                    interact=S_interact,
                    coherence=S_coh
                )
                
                fusion_2 = compute_fusion(branches_2)
                fusion_3 = compute_fusion(branches_3)
                
                result = {
                    'params': {
                        'alpha': alpha,
                        'lambda': lam,
                        'disorder': disorder,
                    },
                    'two_clock': {
                        'usefulness': {k: float(v) for k, v in web_2.usefulness.items()},
                        'mu_U': float(web_2.mu_U),
                        'sigma_U': float(web_2.sigma_U),
                        'mu_M': float(web_2.mu_M),
                        'S_time_web': float(web_2.S_time_web),
                        'I_TS': float(interaction_2['I_TS']),
                        'J_TS': float(interaction_2['J_TS']),
                        'regime': regime_2,
                        'fusion_score': float(fusion_2.score),
                        'fusion_regime': fusion_2.regime,
                    },
                    'three_clock': {
                        'usefulness': {k: float(v) for k, v in web_3.usefulness.items()},
                        'mu_U': float(web_3.mu_U),
                        'sigma_U': float(web_3.sigma_U),
                        'mu_M': float(web_3.mu_M),
                        'S_time_web': float(web_3.S_time_web),
                        'I_TS': float(interaction_3['I_TS']),
                        'J_TS': float(interaction_3['J_TS']),
                        'regime': regime_3,
                        'fusion_score': float(fusion_3.score),
                        'fusion_regime': fusion_3.regime,
                    },
                    'spatial': {
                        'S_space': float(S_space),
                        'S_coherence': float(S_coh),
                        'S_interact': float(S_interact),
                    },
                }
                
                results.append(result)
    
    return results


def analyze_sweep_results(results: List[Dict]) -> Dict:
    """
    Analyze sweep results to find optimal regimes.
    """
    analysis = {
        'total_runs': len(results),
        'two_clock': {
            'meets_S_threshold': 0,
            'meets_I_threshold': 0,
            'spacetime_candidates': 0,
            'best_S_time_web': 0,
            'best_I_TS': 0,
            'best_params_S': None,
            'best_params_I': None,
        },
        'three_clock': {
            'meets_S_threshold': 0,
            'meets_I_threshold': 0,
            'spacetime_candidates': 0,
            'best_S_time_web': 0,
            'best_I_TS': 0,
            'best_params_S': None,
            'best_params_I': None,
        },
    }
    
    S_threshold = 0.3
    I_threshold = 0.5
    
    for r in results:
        # 2-clock analysis
        if r['two_clock']['S_time_web'] > S_threshold:
            analysis['two_clock']['meets_S_threshold'] += 1
        if r['two_clock']['I_TS'] > I_threshold:
            analysis['two_clock']['meets_I_threshold'] += 1
        if r['two_clock']['regime'] == 'spacetime_candidate':
            analysis['two_clock']['spacetime_candidates'] += 1
        if r['two_clock']['S_time_web'] > analysis['two_clock']['best_S_time_web']:
            analysis['two_clock']['best_S_time_web'] = r['two_clock']['S_time_web']
            analysis['two_clock']['best_params_S'] = r['params']
        if r['two_clock']['I_TS'] > analysis['two_clock']['best_I_TS']:
            analysis['two_clock']['best_I_TS'] = r['two_clock']['I_TS']
            analysis['two_clock']['best_params_I'] = r['params']
        
        # 3-clock analysis
        if r['three_clock']['S_time_web'] > S_threshold:
            analysis['three_clock']['meets_S_threshold'] += 1
        if r['three_clock']['I_TS'] > I_threshold:
            analysis['three_clock']['meets_I_threshold'] += 1
        if r['three_clock']['regime'] == 'spacetime_candidate':
            analysis['three_clock']['spacetime_candidates'] += 1
        if r['three_clock']['S_time_web'] > analysis['three_clock']['best_S_time_web']:
            analysis['three_clock']['best_S_time_web'] = r['three_clock']['S_time_web']
            analysis['three_clock']['best_params_S'] = r['params']
        if r['three_clock']['I_TS'] > analysis['three_clock']['best_I_TS']:
            analysis['three_clock']['best_I_TS'] = r['three_clock']['I_TS']
            analysis['three_clock']['best_params_I'] = r['params']
    
    return analysis


def plot_sweep_results(results: List[Dict], output_path: str):
    """
    Generate visualizations of the sweep results.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Extract data for plotting
    alphas = [r['params']['alpha'] for r in results]
    lambdas = [r['params']['lambda'] for r in results]
    disorders = [r['params']['disorder'] for r in results]
    
    S_time_2 = [r['two_clock']['S_time_web'] for r in results]
    S_time_3 = [r['three_clock']['S_time_web'] for r in results]
    I_TS_2 = [r['two_clock']['I_TS'] for r in results]
    I_TS_3 = [r['three_clock']['I_TS'] for r in results]
    S_space = [r['spatial']['S_space'] for r in results]
    fusion_2 = [r['two_clock']['fusion_score'] for r in results]
    
    # Plot 1: S_time_web vs alpha (2-clock vs 3-clock)
    ax = axes[0, 0]
    ax.scatter(alphas, S_time_2, c='blue', alpha=0.6, label='2-clock', s=20)
    ax.scatter(alphas, S_time_3, c='red', alpha=0.6, label='3-clock', s=20)
    ax.axhline(y=0.3, color='green', linestyle='--', label='Threshold')
    ax.set_xlabel('Alpha (backreaction)')
    ax.set_ylabel('S_time-web')
    ax.set_title('Temporal Web vs Alpha')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: S_time_web vs lambda
    ax = axes[0, 1]
    ax.scatter(lambdas, S_time_2, c='blue', alpha=0.6, label='2-clock', s=20)
    ax.scatter(lambdas, S_time_3, c='red', alpha=0.6, label='3-clock', s=20)
    ax.axhline(y=0.3, color='green', linestyle='--', label='Threshold')
    ax.set_xlabel('Lambda (relaxation)')
    ax.set_ylabel('S_time-web')
    ax.set_title('Temporal Web vs Lambda')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: S_time_web vs disorder
    ax = axes[0, 2]
    ax.scatter(disorders, S_time_2, c='blue', alpha=0.6, label='2-clock', s=20)
    ax.scatter(disorders, S_time_3, c='red', alpha=0.6, label='3-clock', s=20)
    ax.axhline(y=0.3, color='green', linestyle='--', label='Threshold')
    ax.set_xlabel('Disorder')
    ax.set_ylabel('S_time-web')
    ax.set_title('Temporal Web vs Disorder')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 4: I_TS vs alpha
    ax = axes[1, 0]
    ax.scatter(alphas, I_TS_2, c='blue', alpha=0.6, label='2-clock', s=20)
    ax.scatter(alphas, I_TS_3, c='red', alpha=0.6, label='3-clock', s=20)
    ax.axhline(y=0.5, color='green', linestyle='--', label='Threshold')
    ax.set_xlabel('Alpha (backreaction)')
    ax.set_ylabel('I_TS (interaction)')
    ax.set_title('Spatial-Temporal Interaction vs Alpha')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 5: Fusion score vs alpha
    ax = axes[1, 1]
    ax.scatter(alphas, fusion_2, c='purple', alpha=0.6, s=20)
    ax.set_xlabel('Alpha (backreaction)')
    ax.set_ylabel('Branch Fusion Score')
    ax.set_title('Branch Fusion vs Alpha (2-clock)')
    ax.grid(True, alpha=0.3)
    
    # Plot 6: S_time-web vs S_space (correlation check)
    ax = axes[1, 2]
    ax.scatter(S_space, S_time_2, c='blue', alpha=0.6, label='2-clock', s=20)
    ax.scatter(S_space, S_time_3, c='red', alpha=0.6, label='3-clock', s=20)
    ax.axhline(y=0.3, color='green', linestyle='--', alpha=0.5)
    ax.axvline(x=0.6, color='orange', linestyle='--', alpha=0.5)
    ax.set_xlabel('S_space')
    ax.set_ylabel('S_time-web')
    ax.set_title('Temporal vs Spatial Scores')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def main():
    """Run the full parameter sweep."""
    print("=" * 70)
    print("BRANCH-FUSION PARAMETER SWEEP")
    print("=" * 70)
    print()
    
    # Define parameter ranges
    alphas = [0.2, 0.4, 0.5, 0.6, 0.8]
    lambdas = [0.5, 1.0, 1.5, 2.0, 2.5]
    disorders = [0.0, 0.2, 0.4, 0.6, 0.8]
    
    print(f"Parameter grid:")
    print(f"  Alpha (backreaction): {alphas}")
    print(f"  Lambda (relaxation):  {lambdas}")
    print(f"  Disorder:             {disorders}")
    print(f"  Total configurations: {len(alphas) * len(lambdas) * len(disorders)}")
    print()
    
    # Run sweep
    print("Running parameter sweep...")
    results = run_parameter_sweep(alphas, lambdas, disorders)
    print(f"Completed {len(results)} configurations")
    print()
    
    # Analyze results
    analysis = analyze_sweep_results(results)
    
    # Print summary
    print("=" * 70)
    print("SWEEP RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"\n2-CLOCK TEMPORAL WEB (osc + decay):")
    print(f"  Configurations meeting S_time-web > 0.3: {analysis['two_clock']['meets_S_threshold']}/{analysis['total_runs']}")
    print(f"  Configurations meeting I_TS > 0.5:       {analysis['two_clock']['meets_I_threshold']}/{analysis['total_runs']}")
    print(f"  Spacetime candidates:                    {analysis['two_clock']['spacetime_candidates']}/{analysis['total_runs']}")
    print(f"  Best S_time-web: {analysis['two_clock']['best_S_time_web']:.3f} at {analysis['two_clock']['best_params_S']}")
    print(f"  Best I_TS:       {analysis['two_clock']['best_I_TS']:.3f} at {analysis['two_clock']['best_params_I']}")
    
    print(f"\n3-CLOCK TEMPORAL WEB (osc + decay + event):")
    print(f"  Configurations meeting S_time-web > 0.3: {analysis['three_clock']['meets_S_threshold']}/{analysis['total_runs']}")
    print(f"  Configurations meeting I_TS > 0.5:       {analysis['three_clock']['meets_I_threshold']}/{analysis['total_runs']}")
    print(f"  Spacetime candidates:                    {analysis['three_clock']['spacetime_candidates']}/{analysis['total_runs']}")
    print(f"  Best S_time-web: {analysis['three_clock']['best_S_time_web']:.3f} at {analysis['three_clock']['best_params_S']}")
    print(f"  Best I_TS:       {analysis['three_clock']['best_I_TS']:.3f} at {analysis['three_clock']['best_params_I']}")
    
    # Find best configurations
    print("\n" + "-" * 70)
    print("BEST CONFIGURATIONS (2-clock)")
    print("-" * 70)
    
    # Sort by S_time_web
    sorted_by_S = sorted(results, key=lambda x: x['two_clock']['S_time_web'], reverse=True)
    print("\nTop 5 by S_time-web:")
    for i, r in enumerate(sorted_by_S[:5]):
        print(f"  {i+1}. α={r['params']['alpha']}, λ={r['params']['lambda']}, d={r['params']['disorder']}")
        print(f"     S_time-web={r['two_clock']['S_time_web']:.3f}, I_TS={r['two_clock']['I_TS']:.3f}, regime={r['two_clock']['regime']}")
    
    # Sort by I_TS
    sorted_by_I = sorted(results, key=lambda x: x['two_clock']['I_TS'], reverse=True)
    print("\nTop 5 by I_TS:")
    for i, r in enumerate(sorted_by_I[:5]):
        print(f"  {i+1}. α={r['params']['alpha']}, λ={r['params']['lambda']}, d={r['params']['disorder']}")
        print(f"     S_time-web={r['two_clock']['S_time_web']:.3f}, I_TS={r['two_clock']['I_TS']:.3f}, regime={r['two_clock']['regime']}")
    
    # Regime distribution
    print("\n" + "-" * 70)
    print("REGIME DISTRIBUTION (2-clock)")
    print("-" * 70)
    regime_counts = {}
    for r in results:
        regime = r['two_clock']['regime']
        regime_counts[regime] = regime_counts.get(regime, 0) + 1
    for regime, count in sorted(regime_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(results)
        print(f"  {regime}: {count} ({pct:.1f}%)")
    
    # Key finding
    print("\n" + "=" * 70)
    print("KEY FINDING")
    print("=" * 70)
    
    best = sorted_by_S[0]
    if best['two_clock']['S_time_web'] >= 0.3:
        print(f"\n✅ Temporal web CAN reach coherence threshold!")
        print(f"   Best config: α={best['params']['alpha']}, λ={best['params']['lambda']}, disorder={best['params']['disorder']}")
        print(f"   S_time-web = {best['two_clock']['S_time_web']:.3f} (threshold: 0.3)")
        print(f"   I_TS = {best['two_clock']['I_TS']:.3f} (threshold: 0.5)")
        
        if best['two_clock']['I_TS'] >= 0.5:
            print(f"\n✅ SPACETIME CANDIDATE REGIME FOUND!")
        else:
            gap = 0.5 - best['two_clock']['I_TS']
            print(f"\n⚠️  I_TS still below threshold. Gap: {gap:.3f}")
            print(f"   → Need stronger spatial-temporal coupling")
    else:
        print(f"\n⚠️  Temporal web does not reach threshold in scanned range")
        print(f"   Best S_time-web = {best['two_clock']['S_time_web']:.3f}")
    
    # Generate plots
    print("\nGenerating visualizations...")
    plot_sweep_results(results, '/app/backend/qmrt_topology/branch_fusion_sweep.png')
    print("Saved: branch_fusion_sweep.png")
    
    # Save full results
    output = {
        'parameters': {
            'alphas': alphas,
            'lambdas': lambdas,
            'disorders': disorders,
        },
        'analysis': analysis,
        'results': results,
    }
    
    with open('/app/backend/qmrt_topology/branch_fusion_sweep.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("Saved: branch_fusion_sweep.json")
    
    print("\n" + "=" * 70)
    print("SWEEP COMPLETE")
    print("=" * 70)
    
    return results, analysis


if __name__ == "__main__":
    main()
