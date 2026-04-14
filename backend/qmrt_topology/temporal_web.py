#!/usr/bin/env python3
"""
QMRT Temporal Web Framework
============================

Time is not a single scalar but a composite structure built from multiple
process-based clocks. This framework computes the temporal web coherence
and its interaction with the spatial branch.

TEMPORAL WEB INPUTS (per clock k):
  D_k: region differentiation score
  Q_k: collapse/usefulness score  
  I_k: independence from transport
  C_k: circularity penalty
  R_k: reproducibility score

PER-CLOCK USEFULNESS:
  U_k = (w_D·D_k + w_Q·Q_k + w_I·I_k + w_R·R_k) × (1 - C_k)

CONSISTENCY MATRIX M_T:
  A^rank_ij = (1 + ρ_s(i,j)) / 2
  A^ratio_ij = exp(-Var[log(T_i/T_j)])
  A^regime_ij = (1 + Corr(U_i, U_j)) / 2
  M_T(i,j) = α·A^rank + β·A^ratio + γ·A^regime

TEMPORAL WEB COHERENCE:
  S_time-web = μ_U × μ_M × (1 - σ_U)

SPATIAL-TEMPORAL INTERACTION:
  J_TS = √(S_time-web × S_space)
  A_TS = (1 + Corr(S_time-web, S_space)) / 2
  I_TS = J_TS × A_TS

SPACETIME CANDIDATE CRITERION:
  S_space > 0.6
  S_time-web > 0.3
  I_TS > 0.5
"""

import numpy as np
from scipy.stats import spearmanr
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import json


@dataclass
class ClockScores:
    """Per-clock metrics (normalized 0-1, except C where higher is worse)."""
    D: float = 0.0  # Region differentiation
    Q: float = 0.0  # Collapse/usefulness
    I: float = 0.0  # Independence from transport
    C: float = 0.0  # Circularity penalty
    R: float = 0.0  # Reproducibility
    
    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass 
class TemporalWebResult:
    """Complete temporal web analysis result."""
    clock_scores: Dict[str, ClockScores] = field(default_factory=dict)
    usefulness: Dict[str, float] = field(default_factory=dict)
    M_T: np.ndarray = field(default_factory=lambda: np.eye(2))
    mu_U: float = 0.0
    sigma_U: float = 0.0
    mu_M: float = 0.0
    S_time_web: float = 0.0
    
    def as_dict(self) -> Dict:
        return {
            'clock_scores': {k: v.as_dict() for k, v in self.clock_scores.items()},
            'usefulness': self.usefulness,
            'M_T': self.M_T.tolist() if isinstance(self.M_T, np.ndarray) else self.M_T,
            'mu_U': self.mu_U,
            'sigma_U': self.sigma_U,
            'mu_M': self.mu_M,
            'S_time_web': self.S_time_web,
        }


def compute_clock_usefulness(
    scores: ClockScores,
    weights: Tuple[float, float, float, float] = (0.3, 0.3, 0.2, 0.2)
) -> float:
    """
    Compute per-clock usefulness score.
    
    U_k = (w_D·D_k + w_Q·Q_k + w_I·I_k + w_R·R_k) × (1 - C_k)
    """
    w_D, w_Q, w_I, w_R = weights
    base = w_D * scores.D + w_Q * scores.Q + w_I * scores.I + w_R * scores.R
    U = base * (1 - scores.C)
    return float(np.clip(U, 0, 1))


def compute_rank_agreement(
    values_i: np.ndarray,
    values_j: np.ndarray
) -> float:
    """
    Compute rank-order agreement using Spearman correlation.
    
    A^rank_ij = (1 + ρ_s(i,j)) / 2
    """
    if len(values_i) < 3 or len(values_j) < 3:
        return 0.5  # Neutral if not enough data
    
    rho, _ = spearmanr(values_i, values_j)
    if np.isnan(rho):
        return 0.5
    
    return float((1 + rho) / 2)


def compute_ratio_stability(
    T_i: np.ndarray,
    T_j: np.ndarray,
    t0_fraction: float = 0.5,
    epsilon: float = 1e-6
) -> float:
    """
    Compute ratio stability between two clocks.
    
    A^ratio_ij = exp(-Var[log((T_i + ε)/(T_j + ε))])
    
    Only computed for t > T_0 (latter half by default).
    """
    n = len(T_i)
    start = int(n * t0_fraction)
    
    if n - start < 3:
        return 0.5  # Neutral if not enough data
    
    T_i_late = T_i[start:] + epsilon
    T_j_late = T_j[start:] + epsilon
    
    log_ratio = np.log(T_i_late / T_j_late)
    variance = np.var(log_ratio)
    
    return float(np.exp(-variance))


def compute_regime_coresponse(
    U_i_across_runs: np.ndarray,
    U_j_across_runs: np.ndarray
) -> float:
    """
    Compute regime co-response (correlation of usefulness across sweeps).
    
    A^regime_ij = (1 + Corr(U_i, U_j)) / 2
    """
    if len(U_i_across_runs) < 3:
        return 0.5  # Neutral if not enough data
    
    corr = np.corrcoef(U_i_across_runs, U_j_across_runs)[0, 1]
    if np.isnan(corr):
        return 0.5
    
    return float((1 + corr) / 2)


def compute_consistency_matrix(
    clock_names: List[str],
    rank_values: Dict[str, np.ndarray],  # Clock values across regions
    time_series: Dict[str, np.ndarray] = None,  # Optional: clock time series
    usefulness_across_runs: Dict[str, np.ndarray] = None,  # Optional: U across runs
    weights: Tuple[float, float, float] = (0.5, 0.25, 0.25)  # α, β, γ
) -> np.ndarray:
    """
    Compute consistency matrix M_T.
    
    M_T(i,j) = α·A^rank + β·A^ratio + γ·A^regime  for i ≠ j
    M_T(i,i) = 1
    """
    n = len(clock_names)
    M_T = np.eye(n)
    alpha, beta, gamma = weights
    
    for i, name_i in enumerate(clock_names):
        for j, name_j in enumerate(clock_names):
            if i >= j:
                continue
            
            # Rank agreement
            if name_i in rank_values and name_j in rank_values:
                A_rank = compute_rank_agreement(rank_values[name_i], rank_values[name_j])
            else:
                A_rank = 0.5
            
            # Ratio stability
            if time_series and name_i in time_series and name_j in time_series:
                A_ratio = compute_ratio_stability(time_series[name_i], time_series[name_j])
            else:
                A_ratio = 0.5
            
            # Regime co-response
            if usefulness_across_runs and name_i in usefulness_across_runs and name_j in usefulness_across_runs:
                A_regime = compute_regime_coresponse(
                    usefulness_across_runs[name_i], 
                    usefulness_across_runs[name_j]
                )
            else:
                A_regime = 0.5
            
            # Combine
            M_ij = alpha * A_rank + beta * A_ratio + gamma * A_regime
            M_T[i, j] = M_ij
            M_T[j, i] = M_ij  # Symmetric
    
    return M_T


def compute_temporal_web_score(
    usefulness: Dict[str, float],
    M_T: np.ndarray,
    min_usefulness_threshold: float = 0.1
) -> Tuple[float, float, float, float]:
    """
    Compute temporal web coherence score.
    
    S_time-web = μ_U × μ_M × (1 - σ_U)
    
    Returns: (S_time_web, mu_U, sigma_U, mu_M)
    """
    # Filter out clocks below threshold
    U_values = [u for u in usefulness.values() if u > min_usefulness_threshold]
    
    if len(U_values) == 0:
        return 0.0, 0.0, 1.0, 0.0
    
    N = len(U_values)
    
    # Mean usefulness
    mu_U = np.mean(U_values)
    
    # Usefulness balance (std)
    sigma_U = np.std(U_values) if N > 1 else 0.0
    
    # Mean pairwise consistency (off-diagonal elements)
    if N > 1:
        off_diag = []
        for i in range(N):
            for j in range(N):
                if i != j:
                    off_diag.append(M_T[i, j])
        mu_M = np.mean(off_diag) if off_diag else 0.5
    else:
        mu_M = 0.5
    
    # Temporal web score
    S_time_web = mu_U * mu_M * (1 - sigma_U)
    
    return float(S_time_web), float(mu_U), float(sigma_U), float(mu_M)


def compute_spatial_temporal_interaction(
    S_time_web: float,
    S_space: float,
    S_time_web_across_runs: np.ndarray = None,
    S_space_across_runs: np.ndarray = None
) -> Dict[str, float]:
    """
    Compute spatial-temporal interaction metrics.
    
    J_TS = √(S_time-web × S_space)  (joint strength)
    A_TS = (1 + Corr(S_time-web, S_space)) / 2  (alignment across runs)
    I_TS = J_TS × A_TS  (interaction score)
    """
    # Joint strength
    J_TS = np.sqrt(S_time_web * S_space) if S_time_web > 0 and S_space > 0 else 0.0
    
    # Alignment (if we have data across runs)
    if S_time_web_across_runs is not None and S_space_across_runs is not None:
        if len(S_time_web_across_runs) >= 3:
            corr = np.corrcoef(S_time_web_across_runs, S_space_across_runs)[0, 1]
            A_TS = (1 + corr) / 2 if not np.isnan(corr) else 0.5
        else:
            A_TS = 0.5
    else:
        A_TS = 0.5
    
    # Interaction score
    I_TS = J_TS * A_TS
    
    return {
        'J_TS': float(J_TS),
        'A_TS': float(A_TS),
        'I_TS': float(I_TS),
    }


def classify_regime(
    S_space: float,
    S_time_web: float,
    I_TS: float,
    min_clock_U: float = 0.0,
    thresholds: Dict[str, float] = None
) -> str:
    """
    Classify the emergence regime.
    
    Spacetime candidate requires:
      S_space > 0.6
      S_time_web > 0.3
      I_TS > 0.5
      min_k U_k > 0.2 (optional)
    """
    if thresholds is None:
        thresholds = {
            's_space': 0.6,
            's_time': 0.3,
            'i_ts': 0.5,
            'u_min': 0.2,
        }
    
    # Check all criteria
    space_ok = S_space > thresholds['s_space']
    time_ok = S_time_web > thresholds['s_time']
    interaction_ok = I_TS > thresholds['i_ts']
    min_clock_ok = min_clock_U > thresholds['u_min']
    
    if space_ok and time_ok and interaction_ok and min_clock_ok:
        return 'spacetime_candidate'
    elif space_ok and time_ok:
        return 'both_branches_present'
    elif space_ok and I_TS > 0.2:
        return 'space_dominant_partial_time'
    elif time_ok and S_space > 0.3:
        return 'time_web_forming'
    elif space_ok:
        return 'space_only'
    elif time_ok:
        return 'time_web_only'
    else:
        return 'pre_emergence'


def analyze_temporal_web(
    clock_data: Dict[str, ClockScores],
    rank_values: Dict[str, np.ndarray] = None,
    time_series: Dict[str, np.ndarray] = None,
    usefulness_weights: Tuple[float, float, float, float] = (0.3, 0.3, 0.2, 0.2),
    consistency_weights: Tuple[float, float, float] = (0.5, 0.25, 0.25),
    min_usefulness: float = 0.1
) -> TemporalWebResult:
    """
    Complete temporal web analysis.
    """
    clock_names = list(clock_data.keys())
    
    # Compute usefulness for each clock
    usefulness = {}
    for name, scores in clock_data.items():
        usefulness[name] = compute_clock_usefulness(scores, usefulness_weights)
    
    # Filter active clocks
    active_clocks = [name for name, u in usefulness.items() if u > min_usefulness]
    
    if len(active_clocks) < 2:
        # Not enough clocks for meaningful web
        return TemporalWebResult(
            clock_scores=clock_data,
            usefulness=usefulness,
            M_T=np.eye(len(clock_names)),
            mu_U=np.mean(list(usefulness.values())),
            sigma_U=np.std(list(usefulness.values())),
            mu_M=0.5,
            S_time_web=0.0,
        )
    
    # Compute consistency matrix
    if rank_values is None:
        rank_values = {}
    
    M_T = compute_consistency_matrix(
        active_clocks,
        rank_values,
        time_series,
        weights=consistency_weights
    )
    
    # Compute web score
    active_usefulness = {k: usefulness[k] for k in active_clocks}
    S_time_web, mu_U, sigma_U, mu_M = compute_temporal_web_score(active_usefulness, M_T)
    
    return TemporalWebResult(
        clock_scores=clock_data,
        usefulness=usefulness,
        M_T=M_T,
        mu_U=mu_U,
        sigma_U=sigma_U,
        mu_M=mu_M,
        S_time_web=S_time_web,
    )


def create_temporal_web_record(
    params: Dict,
    clock_data: Dict[str, ClockScores],
    S_space: float,
    rank_values: Dict[str, np.ndarray] = None,
    time_series: Dict[str, np.ndarray] = None,
) -> Dict:
    """
    Create a complete record for one simulation run.
    """
    # Analyze temporal web
    web_result = analyze_temporal_web(clock_data, rank_values, time_series)
    
    # Compute interaction with space
    interaction = compute_spatial_temporal_interaction(
        web_result.S_time_web,
        S_space
    )
    
    # Classify regime
    min_U = min(web_result.usefulness.values()) if web_result.usefulness else 0
    regime = classify_regime(
        S_space,
        web_result.S_time_web,
        interaction['I_TS'],
        min_U
    )
    
    return {
        'params': params,
        'clock_scores': {k: v.as_dict() for k, v in clock_data.items()},
        'temporal_web': {
            'usefulness': web_result.usefulness,
            'M_T': web_result.M_T.tolist(),
            'mu_U': web_result.mu_U,
            'sigma_U': web_result.sigma_U,
            'mu_M': web_result.mu_M,
            'S_time_web': web_result.S_time_web,
        },
        'space': {
            'S_space': S_space,
        },
        'interaction_TS': interaction,
        'regime': regime,
    }


# Test with current QMRT data
def test_with_current_data():
    """
    Test the temporal web framework with current QMRT test results.
    """
    print("=" * 70)
    print("TEMPORAL WEB FRAMEWORK TEST")
    print("=" * 70)
    print()
    
    # Clock scores from current tests
    # Oscillator: 6 cycle divergence, 11.2% collapse, moderate circularity
    osc_scores = ClockScores(
        D=0.55,  # 6 cycles / ~11 max = moderate differentiation
        Q=0.112,  # 11.2% collapse improvement
        I=0.70,  # Moderate independence (not perfectly correlated with τ)
        C=0.10,  # Low circularity (phase-based, not field integral)
        R=0.90,  # High reproducibility
    )
    
    # Decay: 27.6% differentiation, -7.6% collapse (worse), very reproducible
    decay_scores = ClockScores(
        D=0.82,  # 27.6% / ~35% max = strong differentiation
        Q=0.0,   # No collapse improvement (actually made it worse)
        I=0.65,  # Monotonic with structure, but state-transition based
        C=0.05,  # Very low circularity (state transition, not field)
        R=0.99,  # Extremely reproducible (0.3% within-region CV)
    )
    
    # Event: weak, mostly edge-triggered
    event_scores = ClockScores(
        D=0.10,  # Only edge region different
        Q=0.0,   # No collapse
        I=0.40,  # Transport marker, not independent
        C=0.02,  # Not circular, just not informative
        R=0.85,  # Moderate reproducibility
    )
    
    clock_data = {
        'osc': osc_scores,
        'decay': decay_scores,
        'event': event_scores,
    }
    
    # Rank values (differentiation across regions)
    # Oscillator cycles: high_structure=10, edge=5, quiet=4
    # Decay lifetimes: high_structure=9.13, transitional=7.29, quiet=6.98
    rank_values = {
        'osc': np.array([10, 5, 4]),  # cycles
        'decay': np.array([9.13, 7.29, 6.98]),  # lifetimes
        'event': np.array([1, 35, 1]),  # event counts (edge anomaly)
    }
    
    # Current spatial score (from lensing/causal tests)
    S_space = 0.85  # Strong spatial emergence
    
    print("Clock Scores:")
    for name, scores in clock_data.items():
        print(f"  {name}: D={scores.D:.2f}, Q={scores.Q:.2f}, I={scores.I:.2f}, C={scores.C:.2f}, R={scores.R:.2f}")
    
    # Analyze
    web_result = analyze_temporal_web(clock_data, rank_values)
    
    print(f"\nClock Usefulness:")
    for name, U in web_result.usefulness.items():
        print(f"  {name}: U = {U:.3f}")
    
    print(f"\nConsistency Matrix M_T:")
    clock_names = list(clock_data.keys())
    print("       " + "  ".join([f"{n:>6}" for n in clock_names]))
    for i, name in enumerate(clock_names):
        row = web_result.M_T[i, :] if i < len(web_result.M_T) else [0] * len(clock_names)
        print(f"  {name:>4}: " + "  ".join([f"{v:>6.2f}" for v in row[:len(clock_names)]]))
    
    print(f"\nTemporal Web Metrics:")
    print(f"  μ_U (mean usefulness): {web_result.mu_U:.3f}")
    print(f"  σ_U (usefulness spread): {web_result.sigma_U:.3f}")
    print(f"  μ_M (mean consistency): {web_result.mu_M:.3f}")
    print(f"  S_time-web: {web_result.S_time_web:.3f}")
    
    # Interaction with space
    interaction = compute_spatial_temporal_interaction(web_result.S_time_web, S_space)
    
    print(f"\nSpatial-Temporal Interaction:")
    print(f"  S_space: {S_space:.3f}")
    print(f"  J_TS (joint strength): {interaction['J_TS']:.3f}")
    print(f"  A_TS (alignment): {interaction['A_TS']:.3f}")
    print(f"  I_TS (interaction): {interaction['I_TS']:.3f}")
    
    # Classify
    min_U = min(web_result.usefulness.values())
    regime = classify_regime(S_space, web_result.S_time_web, interaction['I_TS'], min_U)
    
    print(f"\nRegime: {regime}")
    
    # Interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    
    if web_result.S_time_web < 0.3:
        print("\n  Temporal web is FRAGMENTED")
        print("  - Clocks exist but don't form coherent structure")
    elif web_result.S_time_web >= 0.3 and interaction['I_TS'] < 0.5:
        print("\n  Temporal web is ORDERED but NOT COUPLED to space")
        print("  - Time-like structure present, not yet spacetime")
    else:
        print("\n  Temporal web is COUPLING with spatial branch")
        print("  - Spacetime-candidate regime")
    
    # Create full record
    record = create_temporal_web_record(
        params={'beta': 1.0, 'lambda': 1.5},
        clock_data=clock_data,
        S_space=S_space,
        rank_values=rank_values,
    )
    
    # Save
    with open('/app/backend/qmrt_topology/temporal_web_test.json', 'w') as f:
        json.dump(record, f, indent=2)
    print("\nSaved temporal_web_test.json")
    
    return record


if __name__ == "__main__":
    test_with_current_data()
