#!/usr/bin/env python3
"""
QMRT Spacetime Coupling Test
=============================

THE REAL TEST: Does the temporal structure (O, R, P) couple with space?

Time exists when O, R, P are mutually consistent.
SPACETIME exists when T = (O, R, P) becomes correlated with S (space).

METRICS:
  S_time = μ(O,R,P) × (1 - σ(O,R,P))     # Temporal strength
  
  Cross-branch correlations:
    ρ_OS = Corr(O, S) across parameter space
    ρ_RS = Corr(R, S) across parameter space  
    ρ_PS = Corr(P, S) across parameter space
    
  Spacetime coupling:
    I_TS = f(ρ_OS, ρ_RS, ρ_PS)

INTERPRETATION:
  | Corr(T, S) | Meaning |
  |------------|---------|
  | Low (<0.3) | Time independent of space |
  | Moderate   | Partial coupling |
  | High (>0.8)| SPACETIME REGIME |

KEY INSIGHT:
  - O (ordering) should remain relatively independent (causality preserved)
  - R (rate) should couple strongly (time dilation effect)
  - P (persistence) should couple moderately (stability varies with geometry)
"""

import numpy as np
from scipy.stats import spearmanr, pearsonr
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
import json

# Import from existing frameworks
from temporal_web_v2 import (
    LayeredTemporalWeb, 
    compute_ordering_layer, 
    compute_rate_layer, 
    compute_persistence_layer,
    compute_temporal_emergence
)


@dataclass
class SpacetimeCoupling:
    """Spacetime coupling metrics."""
    # Individual layer-space correlations
    rho_OS: float = 0.0  # Ordering ↔ Space correlation
    rho_RS: float = 0.0  # Rate ↔ Space correlation
    rho_PS: float = 0.0  # Persistence ↔ Space correlation
    
    # Combined metrics
    I_TS: float = 0.0           # Spacetime interaction score
    coupling_balance: float = 0.0  # How balanced are the layer couplings?
    
    # Regime classification
    regime: str = "unknown"
    
    def as_dict(self) -> Dict:
        return asdict(self)


def compute_layer_space_correlation(
    layer_values: np.ndarray,
    space_values: np.ndarray,
    method: str = 'spearman'
) -> float:
    """
    Compute correlation between a temporal layer and spatial score.
    
    Args:
        layer_values: Array of layer scores across runs/regions
        space_values: Array of spatial scores across same runs/regions
        method: 'spearman' or 'pearson'
    
    Returns:
        Correlation coefficient mapped to [0, 1]
    """
    if len(layer_values) < 3 or len(space_values) < 3:
        return 0.5  # Neutral if insufficient data
    
    if len(layer_values) != len(space_values):
        n = min(len(layer_values), len(space_values))
        layer_values = layer_values[:n]
        space_values = space_values[:n]
    
    if method == 'spearman':
        rho, _ = spearmanr(layer_values, space_values)
    else:
        rho, _ = pearsonr(layer_values, space_values)
    
    if np.isnan(rho):
        return 0.5
    
    # Map [-1, 1] to [0, 1]
    return float((1 + rho) / 2)


def compute_spacetime_coupling(
    O_values: np.ndarray,
    R_values: np.ndarray,
    P_values: np.ndarray,
    S_values: np.ndarray,
    weights: Tuple[float, float, float] = (0.2, 0.5, 0.3)
) -> SpacetimeCoupling:
    """
    Compute spacetime coupling from layer-space correlations.
    
    The weights reflect expected physics:
    - O (ordering): Low weight — causality should be independent of space
    - R (rate): High weight — time dilation is the main coupling mechanism
    - P (persistence): Moderate — stability varies with geometry
    
    I_TS = w_O × ρ_OS + w_R × ρ_RS + w_P × ρ_PS
    
    But with a penalty if O correlates too strongly (violates causality preservation).
    """
    w_O, w_R, w_P = weights
    
    # Compute correlations
    rho_OS = compute_layer_space_correlation(O_values, S_values)
    rho_RS = compute_layer_space_correlation(R_values, S_values)
    rho_PS = compute_layer_space_correlation(P_values, S_values)
    
    # Base coupling score
    I_base = w_O * rho_OS + w_R * rho_RS + w_P * rho_PS
    
    # Causality preservation check
    # If O correlates too strongly with S (> 0.8), that's suspicious
    # Ordering should be more universal
    if rho_OS > 0.8:
        causality_penalty = 0.9  # Slight penalty
    else:
        causality_penalty = 1.0
    
    # Time dilation signature check
    # R should couple more strongly than O (this is the "time slows near mass" analog)
    if rho_RS > rho_OS + 0.1:
        dilation_bonus = 1.1  # Slight bonus for expected physics
    else:
        dilation_bonus = 1.0
    
    I_TS = I_base * causality_penalty * dilation_bonus
    I_TS = float(np.clip(I_TS, 0, 1))
    
    # Coupling balance
    correlations = [rho_OS, rho_RS, rho_PS]
    coupling_balance = 1 - np.std(correlations)
    
    # Classify regime
    regime = classify_spacetime_regime(rho_OS, rho_RS, rho_PS, I_TS)
    
    return SpacetimeCoupling(
        rho_OS=rho_OS,
        rho_RS=rho_RS,
        rho_PS=rho_PS,
        I_TS=I_TS,
        coupling_balance=coupling_balance,
        regime=regime
    )


def classify_spacetime_regime(
    rho_OS: float,
    rho_RS: float,
    rho_PS: float,
    I_TS: float,
    thresholds: Dict[str, float] = None
) -> str:
    """
    Classify the spacetime emergence regime.
    
    Expected physics:
    - Spacetime: R and P couple with S, O remains independent
    - Time-only: T exists but doesn't couple with S
    - Pre-emergence: Neither T nor coupling present
    """
    if thresholds is None:
        thresholds = {
            'I_TS_high': 0.7,
            'I_TS_moderate': 0.5,
            'rho_RS_high': 0.7,
            'rho_OS_independent': 0.6,  # O should be below this
        }
    
    # Check for spacetime regime
    R_coupled = rho_RS > thresholds['rho_RS_high']
    O_independent = rho_OS < thresholds['rho_OS_independent']
    I_strong = I_TS > thresholds['I_TS_high']
    I_moderate = I_TS > thresholds['I_TS_moderate']
    
    if I_strong and R_coupled and O_independent:
        return "spacetime_candidate"
    elif I_strong and R_coupled:
        return "spacetime_partial"  # R couples but O not independent
    elif I_moderate and (R_coupled or rho_PS > 0.6):
        return "coupling_forming"
    elif I_TS > 0.4:
        return "weak_coupling"
    else:
        return "time_only"  # Time exists but doesn't couple


def compute_full_spacetime_analysis(
    # Arrays across parameter sweep
    O_array: np.ndarray,
    R_array: np.ndarray,
    P_array: np.ndarray,
    S_space_array: np.ndarray,
    params_list: List[Dict] = None
) -> Dict:
    """
    Complete spacetime analysis from a parameter sweep.
    
    Args:
        O_array: Ordering scores across all runs
        R_array: Rate scores across all runs
        P_array: Persistence scores across all runs
        S_space_array: Spatial scores across all runs
        params_list: Optional list of parameter dicts for each run
    """
    n = len(O_array)
    
    # Temporal strength for each run
    S_time_array = np.array([
        np.mean([O, R, P]) * (1 - np.std([O, R, P]))
        for O, R, P in zip(O_array, R_array, P_array)
    ])
    
    # Compute coupling
    coupling = compute_spacetime_coupling(O_array, R_array, P_array, S_space_array)
    
    # Also compute correlation of S_time with S_space
    rho_TS = compute_layer_space_correlation(S_time_array, S_space_array)
    
    # Summary statistics
    analysis = {
        'n_runs': n,
        'temporal': {
            'O_mean': float(np.mean(O_array)),
            'R_mean': float(np.mean(R_array)),
            'P_mean': float(np.mean(P_array)),
            'S_time_mean': float(np.mean(S_time_array)),
            'S_time_std': float(np.std(S_time_array)),
        },
        'spatial': {
            'S_space_mean': float(np.mean(S_space_array)),
            'S_space_std': float(np.std(S_space_array)),
        },
        'coupling': coupling.as_dict(),
        'rho_TS_direct': float(rho_TS),  # Direct S_time ↔ S_space correlation
        'interpretation': interpret_coupling(coupling, rho_TS),
    }
    
    return analysis


def interpret_coupling(coupling: SpacetimeCoupling, rho_TS: float) -> Dict:
    """Generate interpretation of the coupling results."""
    
    interpretation = {
        'ordering_behavior': '',
        'rate_behavior': '',
        'persistence_behavior': '',
        'overall': '',
        'physics_signature': [],
    }
    
    # Ordering interpretation
    if coupling.rho_OS < 0.4:
        interpretation['ordering_behavior'] = 'INDEPENDENT (causality preserved)'
        interpretation['physics_signature'].append('causality_preserved')
    elif coupling.rho_OS < 0.6:
        interpretation['ordering_behavior'] = 'WEAKLY COUPLED'
    else:
        interpretation['ordering_behavior'] = 'STRONGLY COUPLED (unexpected)'
    
    # Rate interpretation
    if coupling.rho_RS > 0.7:
        interpretation['rate_behavior'] = 'STRONGLY COUPLED (time dilation signature)'
        interpretation['physics_signature'].append('time_dilation')
    elif coupling.rho_RS > 0.5:
        interpretation['rate_behavior'] = 'MODERATELY COUPLED'
    else:
        interpretation['rate_behavior'] = 'WEAKLY COUPLED'
    
    # Persistence interpretation
    if coupling.rho_PS > 0.6:
        interpretation['persistence_behavior'] = 'COUPLED (geometry affects stability)'
        interpretation['physics_signature'].append('geometry_stability_link')
    elif coupling.rho_PS > 0.4:
        interpretation['persistence_behavior'] = 'PARTIALLY COUPLED'
    else:
        interpretation['persistence_behavior'] = 'INDEPENDENT'
    
    # Overall
    if coupling.regime == 'spacetime_candidate':
        interpretation['overall'] = 'SPACETIME REGIME: T and S are mutually predictive'
    elif coupling.regime in ['spacetime_partial', 'coupling_forming']:
        interpretation['overall'] = 'APPROACHING SPACETIME: Coupling forming but not complete'
    elif coupling.regime == 'weak_coupling':
        interpretation['overall'] = 'WEAK COUPLING: Time exists, partial space correlation'
    else:
        interpretation['overall'] = 'TIME-ONLY: Temporal structure exists but independent of space'
    
    return interpretation


# ============================================================
# TEST WITH SIMULATED DATA
# ============================================================

def test_spacetime_coupling():
    """Test spacetime coupling with simulated parameter sweep data."""
    
    print("=" * 70)
    print("SPACETIME COUPLING TEST")
    print("=" * 70)
    print()
    print("The Question: Does the temporal structure (O, R, P) couple with space?")
    print()
    
    # Simulate a parameter sweep
    # In reality, these would come from actual PDE simulations
    np.random.seed(42)
    n_runs = 50
    
    # Generate correlated data to simulate different coupling regimes
    
    # Scenario 1: Expected physics (R couples with S, O independent)
    print("-" * 70)
    print("SCENARIO 1: Expected Physics (R couples, O independent)")
    print("-" * 70)
    
    S_space = np.random.uniform(0.5, 0.9, n_runs)  # Spatial scores
    
    # O: independent of space (low correlation)
    O = 0.7 + 0.1 * np.random.randn(n_runs)
    O = np.clip(O, 0.4, 0.9)
    
    # R: correlated with space (time dilation analog)
    R = 0.3 + 0.6 * S_space + 0.05 * np.random.randn(n_runs)
    R = np.clip(R, 0.3, 0.95)
    
    # P: moderately correlated with space
    P = 0.5 + 0.3 * S_space + 0.1 * np.random.randn(n_runs)
    P = np.clip(P, 0.5, 0.95)
    
    analysis1 = compute_full_spacetime_analysis(O, R, P, S_space)
    
    print(f"\nLayer-Space Correlations:")
    print(f"  ρ(O, S) = {analysis1['coupling']['rho_OS']:.3f}  {'✓ Independent' if analysis1['coupling']['rho_OS'] < 0.6 else '✗ Coupled'}")
    print(f"  ρ(R, S) = {analysis1['coupling']['rho_RS']:.3f}  {'✓ Time dilation' if analysis1['coupling']['rho_RS'] > 0.7 else ''}")
    print(f"  ρ(P, S) = {analysis1['coupling']['rho_PS']:.3f}")
    print(f"\nSpacetime Coupling:")
    print(f"  I_TS = {analysis1['coupling']['I_TS']:.3f}")
    print(f"  Regime: {analysis1['coupling']['regime']}")
    print(f"\nInterpretation:")
    print(f"  O: {analysis1['interpretation']['ordering_behavior']}")
    print(f"  R: {analysis1['interpretation']['rate_behavior']}")
    print(f"  P: {analysis1['interpretation']['persistence_behavior']}")
    print(f"  → {analysis1['interpretation']['overall']}")
    
    # Scenario 2: Time-only (no spatial coupling)
    print()
    print("-" * 70)
    print("SCENARIO 2: Time-Only (no spatial coupling)")
    print("-" * 70)
    
    S_space2 = np.random.uniform(0.5, 0.9, n_runs)
    O2 = 0.7 + 0.15 * np.random.randn(n_runs)  # Independent
    R2 = 0.75 + 0.1 * np.random.randn(n_runs)  # Independent
    P2 = 0.85 + 0.08 * np.random.randn(n_runs)  # Independent
    
    O2 = np.clip(O2, 0.4, 0.9)
    R2 = np.clip(R2, 0.4, 0.95)
    P2 = np.clip(P2, 0.5, 0.98)
    
    analysis2 = compute_full_spacetime_analysis(O2, R2, P2, S_space2)
    
    print(f"\nLayer-Space Correlations:")
    print(f"  ρ(O, S) = {analysis2['coupling']['rho_OS']:.3f}")
    print(f"  ρ(R, S) = {analysis2['coupling']['rho_RS']:.3f}")
    print(f"  ρ(P, S) = {analysis2['coupling']['rho_PS']:.3f}")
    print(f"\nSpacetime Coupling:")
    print(f"  I_TS = {analysis2['coupling']['I_TS']:.3f}")
    print(f"  Regime: {analysis2['coupling']['regime']}")
    print(f"\n  → {analysis2['interpretation']['overall']}")
    
    # Scenario 3: Using actual QMRT-like data structure
    print()
    print("-" * 70)
    print("SCENARIO 3: QMRT-like Parameter Variation")
    print("-" * 70)
    
    # Simulate varying alpha (backreaction) and measuring responses
    alphas = np.linspace(0.2, 0.8, n_runs)
    
    # Space improves with moderate alpha, peaks around 0.5
    S_space3 = 0.5 + 0.4 * np.exp(-5 * (alphas - 0.5)**2) + 0.02 * np.random.randn(n_runs)
    S_space3 = np.clip(S_space3, 0.3, 0.95)
    
    # O: mostly stable (causality preserved)
    O3 = 0.72 + 0.05 * np.random.randn(n_runs)
    O3 = np.clip(O3, 0.5, 0.85)
    
    # R: improves with alpha (stronger backreaction → more pronounced rate differences)
    R3 = 0.5 + 0.4 * alphas + 0.05 * np.random.randn(n_runs)
    R3 = np.clip(R3, 0.4, 0.95)
    
    # P: also improves with alpha
    P3 = 0.6 + 0.3 * alphas + 0.05 * np.random.randn(n_runs)
    P3 = np.clip(P3, 0.5, 0.95)
    
    analysis3 = compute_full_spacetime_analysis(O3, R3, P3, S_space3)
    
    print(f"\nTemporal Means:")
    print(f"  O = {analysis3['temporal']['O_mean']:.3f}")
    print(f"  R = {analysis3['temporal']['R_mean']:.3f}")
    print(f"  P = {analysis3['temporal']['P_mean']:.3f}")
    print(f"  S_time = {analysis3['temporal']['S_time_mean']:.3f}")
    
    print(f"\nSpatial Mean:")
    print(f"  S_space = {analysis3['spatial']['S_space_mean']:.3f}")
    
    print(f"\nLayer-Space Correlations:")
    print(f"  ρ(O, S) = {analysis3['coupling']['rho_OS']:.3f}")
    print(f"  ρ(R, S) = {analysis3['coupling']['rho_RS']:.3f}")
    print(f"  ρ(P, S) = {analysis3['coupling']['rho_PS']:.3f}")
    
    print(f"\nSpacetime Coupling:")
    print(f"  I_TS = {analysis3['coupling']['I_TS']:.3f}")
    print(f"  Regime: {analysis3['coupling']['regime']}")
    
    print(f"\nInterpretation:")
    for sig in analysis3['interpretation']['physics_signature']:
        print(f"  ✓ {sig}")
    print(f"\n  → {analysis3['interpretation']['overall']}")
    
    # Save results
    results = {
        'scenario_1_expected_physics': analysis1,
        'scenario_2_time_only': analysis2,
        'scenario_3_qmrt_like': analysis3,
    }
    
    with open('/app/backend/qmrt_topology/spacetime_coupling_test.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
  | Scenario | I_TS  | Regime |
  |----------|-------|--------|
  | Expected physics | {analysis1['coupling']['I_TS']:.2f}  | {analysis1['coupling']['regime']} |
  | Time-only        | {analysis2['coupling']['I_TS']:.2f}  | {analysis2['coupling']['regime']} |
  | QMRT-like        | {analysis3['coupling']['I_TS']:.2f}  | {analysis3['coupling']['regime']} |
  
  The framework can distinguish between:
  - Time existing independently (no spatial coupling)
  - Time coupling with space (spacetime emergence)
  
  Key signature of spacetime:
  - R (rate) strongly couples with S (time dilation analog)
  - O (ordering) remains independent (causality preserved)
  
  Saved: spacetime_coupling_test.json
""")
    
    return results


if __name__ == "__main__":
    test_spacetime_coupling()
