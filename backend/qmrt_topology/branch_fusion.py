#!/usr/bin/env python3
"""
QMRT Branch-Fusion Framework
=============================

Framework for testing multi-branch emergence and spacetime fusion.

CORE CONCEPT:
Spacetime is not identified by any single branch alone, but by a higher-order
fusion regime where spatial, temporal, interaction, and coherence branches
become mutually consistent.

BRANCHES:
1. Spatial (S_space): geodesic error, causal cone, lensing
2. Clock (S_clock): oscillator sync, event intervals, frequency lock, non-circular
3. Interaction (S_interact): pulse attraction, capture zones
4. Coherence (S_coh): channel persistence, τ stability

FUSION METRIC:
  μ_B = mean(branch scores)
  σ_B = std(branch scores)
  F = μ_B × (1 - σ_B)  [high mean, low variance → high fusion]

REGIME CLASSIFICATION:
  - Pre-emergence: Low branch scores
  - Partial: Some branches high, others low
  - Branch-synchronized: All branches moderate-high, low variance
  - Spacetime candidate: F > 0.6, σ_B < 0.15, F_min > 0.4, collapse_imp > 10%
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import matplotlib.pyplot as plt


@dataclass
class BranchScores:
    """Normalized scores for each emergence branch (0-1)."""
    space: float = 0.0      # Spatial geometry emergence
    clock: float = 0.0      # Temporal process emergence
    interact: float = 0.0   # Interaction dynamics emergence
    coherence: float = 0.0  # Medium coherence
    
    def as_array(self) -> np.ndarray:
        return np.array([self.space, self.clock, self.interact, self.coherence])
    
    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class FusionMetrics:
    """Fusion analysis results."""
    mean: float = 0.0       # μ_B = mean(branch scores)
    std: float = 0.0        # σ_B = std(branch scores)
    score: float = 0.0      # F = μ_B × (1 - σ_B)
    min_branch: float = 0.0 # F_min = min(branch scores)
    regime: str = "unknown"
    
    def as_dict(self) -> Dict:
        return asdict(self)


def compute_space_score(
    geodesic_error: float = 0.0,      # 0 = perfect, 1 = bad (normalized)
    cone_containment: float = 0.0,    # 0-1, higher = better
    lensing_strength: float = 0.0,    # 0-1, normalized lensing effect
    weights: tuple = (0.4, 0.3, 0.3)
) -> float:
    """
    Compute spatial branch score.
    
    S_space = w₁(1 - Ê_geo) + w₂Ĉ_cone + w₃L̂_lens
    """
    w1, w2, w3 = weights
    score = w1 * (1 - geodesic_error) + w2 * cone_containment + w3 * lensing_strength
    return float(np.clip(score, 0, 1))


def compute_clock_score(
    phase_sync: float = 0.0,          # Kuramoto order 0-1
    freq_lock: float = 0.0,           # 1 - freq_variance (normalized)
    collapse_improvement: float = 0.0, # 0-1 (normalized from %)
    circularity: float = 0.0,         # 0-1, higher = more circular (BAD)
    weights: tuple = (0.25, 0.25, 0.3, 0.2)
) -> float:
    """
    Compute clock branch score with circularity penalty.
    
    S_clock = (w₁K + w₂F + w₃C) × (1 - Ĉ_circular)
    """
    w1, w2, w3, w4 = weights
    base_score = w1 * phase_sync + w2 * freq_lock + w3 * collapse_improvement
    # Apply circularity penalty
    penalty = 1 - w4 * circularity
    score = base_score * penalty
    return float(np.clip(score, 0, 1))


def compute_interact_score(
    attraction_magnitude: float = 0.0,  # 0-1, normalized
    capture_robustness: float = 0.0,    # 0-1
    lensing_interaction: float = 0.0,   # 0-1
    weights: tuple = (0.4, 0.3, 0.3)
) -> float:
    """
    Compute interaction branch score.
    
    S_interact = u₁Â_attr + u₂Ẑ_capture + u₃R̂_robust
    """
    w1, w2, w3 = weights
    score = w1 * attraction_magnitude + w2 * capture_robustness + w3 * lensing_interaction
    return float(np.clip(score, 0, 1))


def compute_coherence_score(
    channel_persistence: float = 0.0,  # 0-1
    t_coh_normalized: float = 0.0,     # 0-1
    tau_stability: float = 0.0,        # 1 - τ_variance (normalized)
    weights: tuple = (0.3, 0.3, 0.4)
) -> float:
    """
    Compute coherence branch score.
    
    S_coh = z₁P̂_channel + z₂T̂_coh + z₃(1 - σ̂_τ)
    """
    w1, w2, w3 = weights
    score = w1 * channel_persistence + w2 * t_coh_normalized + w3 * tau_stability
    return float(np.clip(score, 0, 1))


def compute_fusion(branches: BranchScores) -> FusionMetrics:
    """
    Compute fusion metric from branch scores.
    
    F = μ_B × (1 - σ_B)
    
    High fusion requires:
    - All branches high (high mean)
    - All branches similar (low std)
    """
    scores = branches.as_array()
    
    mean = float(np.mean(scores))
    std = float(np.std(scores))
    min_branch = float(np.min(scores))
    
    # Primary fusion score
    score = mean * (1 - std)
    
    # Classify regime
    if score > 0.6 and std < 0.15 and min_branch > 0.4:
        regime = "spacetime_candidate"
    elif mean > 0.5 and std < 0.2:
        regime = "branch_synchronized"
    elif mean > 0.3:
        regime = "partial_emergence"
    else:
        regime = "pre_emergence"
    
    return FusionMetrics(
        mean=mean,
        std=std,
        score=score,
        min_branch=min_branch,
        regime=regime
    )


def compute_branch_correlation(
    results_list: List[Dict],
    branch_names: List[str] = ['space', 'clock', 'interact', 'coherence']
) -> np.ndarray:
    """
    Compute pairwise correlation between branches across runs.
    
    R_ij = Corr(S_i, S_j) across parameter space
    """
    n_branches = len(branch_names)
    
    # Extract branch scores from all runs
    branch_vectors = {name: [] for name in branch_names}
    
    for result in results_list:
        scores = result.get('branch_scores', {})
        for name in branch_names:
            branch_vectors[name].append(scores.get(name, 0.0))
    
    # Convert to arrays
    for name in branch_names:
        branch_vectors[name] = np.array(branch_vectors[name])
    
    # Compute correlation matrix
    corr_matrix = np.zeros((n_branches, n_branches))
    for i, name_i in enumerate(branch_names):
        for j, name_j in enumerate(branch_names):
            if len(branch_vectors[name_i]) > 2:
                corr = np.corrcoef(branch_vectors[name_i], branch_vectors[name_j])[0, 1]
                corr_matrix[i, j] = corr if not np.isnan(corr) else 0
            else:
                corr_matrix[i, j] = 0 if i != j else 1
    
    return corr_matrix


def create_branch_record(
    params: Dict,
    branches: BranchScores,
    fusion: FusionMetrics,
    collapse_improvement: float = 0.0
) -> Dict:
    """
    Create a standardized record for a single simulation run.
    """
    return {
        'params': params,
        'branch_scores': branches.as_dict(),
        'fusion': {
            **fusion.as_dict(),
            'collapse_improvement': collapse_improvement
        },
        'regime': fusion.regime
    }


def plot_branch_radar(
    branches: BranchScores,
    title: str = "Branch Scores",
    ax=None
):
    """
    Plot branch scores as a radar/spider chart.
    """
    labels = ['Space', 'Clock', 'Interact', 'Coherence']
    values = branches.as_array()
    
    # Close the polygon
    values = np.concatenate([values, [values[0]]])
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    angles = np.concatenate([angles, [angles[0]]])
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    
    return ax


def plot_fusion_phase_diagram(
    results_list: List[Dict],
    x_param: str,
    y_param: str,
    output_path: str = None
):
    """
    Plot fusion score as a 2D phase diagram.
    """
    # Extract unique parameter values
    x_values = sorted(set([r['params'].get(x_param, 0) for r in results_list]))
    y_values = sorted(set([r['params'].get(y_param, 0) for r in results_list]))
    
    # Build grid
    fusion_grid = np.zeros((len(y_values), len(x_values)))
    
    for result in results_list:
        x_idx = x_values.index(result['params'].get(x_param, 0))
        y_idx = y_values.index(result['params'].get(y_param, 0))
        fusion_grid[y_idx, x_idx] = result['fusion']['score']
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    im = ax.imshow(fusion_grid, origin='lower', aspect='auto', cmap='viridis',
                   extent=[min(x_values), max(x_values), min(y_values), max(y_values)])
    
    ax.set_xlabel(x_param)
    ax.set_ylabel(y_param)
    ax.set_title('Branch Fusion Score F = μ_B × (1 - σ_B)')
    plt.colorbar(im, ax=ax, label='Fusion Score')
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    
    return fig, ax


# Example usage / test
def test_framework():
    """Test the branch-fusion framework with synthetic data."""
    print("=" * 70)
    print("BRANCH-FUSION FRAMEWORK TEST")
    print("=" * 70)
    print()
    
    # Test 1: Pre-emergence (all low)
    branches1 = BranchScores(space=0.2, clock=0.1, interact=0.15, coherence=0.1)
    fusion1 = compute_fusion(branches1)
    print(f"Test 1 (Pre-emergence):")
    print(f"  Branches: {branches1.as_dict()}")
    print(f"  Fusion: F={fusion1.score:.3f}, regime={fusion1.regime}")
    
    # Test 2: Partial (some high, some low)
    branches2 = BranchScores(space=0.8, clock=0.2, interact=0.7, coherence=0.5)
    fusion2 = compute_fusion(branches2)
    print(f"\nTest 2 (Partial):")
    print(f"  Branches: {branches2.as_dict()}")
    print(f"  Fusion: F={fusion2.score:.3f}, regime={fusion2.regime}")
    
    # Test 3: Branch-synchronized (all moderate-high, balanced)
    branches3 = BranchScores(space=0.7, clock=0.65, interact=0.6, coherence=0.7)
    fusion3 = compute_fusion(branches3)
    print(f"\nTest 3 (Branch-synchronized):")
    print(f"  Branches: {branches3.as_dict()}")
    print(f"  Fusion: F={fusion3.score:.3f}, regime={fusion3.regime}")
    
    # Test 4: Spacetime candidate (all high, balanced)
    branches4 = BranchScores(space=0.85, clock=0.8, interact=0.75, coherence=0.82)
    fusion4 = compute_fusion(branches4)
    print(f"\nTest 4 (Spacetime candidate):")
    print(f"  Branches: {branches4.as_dict()}")
    print(f"  Fusion: F={fusion4.score:.3f}, regime={fusion4.regime}")
    
    # Create records
    records = [
        create_branch_record({'alpha': 0.5, 'kappa': 0.1}, branches1, fusion1, 2.0),
        create_branch_record({'alpha': 0.5, 'kappa': 0.5}, branches2, fusion2, 5.0),
        create_branch_record({'alpha': 0.5, 'kappa': 0.8}, branches3, fusion3, 8.0),
        create_branch_record({'alpha': 0.8, 'kappa': 0.8}, branches4, fusion4, 15.0),
    ]
    
    # Compute branch correlation
    print("\nBranch Correlation Matrix:")
    corr = compute_branch_correlation(records)
    labels = ['space', 'clock', 'interact', 'coherence']
    print("         " + "  ".join([f"{l:>8}" for l in labels]))
    for i, label in enumerate(labels):
        print(f"{label:>8}: " + "  ".join([f"{corr[i,j]:>8.2f}" for j in range(4)]))
    
    # Plot radar
    fig = plt.figure(figsize=(16, 4))
    
    for i, (branches, fusion, title) in enumerate([
        (branches1, fusion1, "Pre-emergence"),
        (branches2, fusion2, "Partial"),
        (branches3, fusion3, "Synchronized"),
        (branches4, fusion4, "Spacetime Candidate"),
    ]):
        ax = fig.add_subplot(1, 4, i+1, projection='polar')
        plot_branch_radar(branches, f"{title}\nF={fusion.score:.2f}", ax)
    
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/branch_fusion_test.png', dpi=150, bbox_inches='tight')
    print("\nSaved branch_fusion_test.png")
    
    # Save test records
    with open('/app/backend/qmrt_topology/branch_fusion_test.json', 'w') as f:
        json.dump({
            'test_records': records,
            'correlation_matrix': corr.tolist(),
        }, f, indent=2)
    print("Saved branch_fusion_test.json")
    
    print("\n" + "=" * 70)
    print("FRAMEWORK READY")
    print("=" * 70)
    print("""
To use in actual tests:

1. Import components:
   from branch_fusion import BranchScores, compute_fusion, create_branch_record

2. Compute branch scores from test results:
   branches = BranchScores(
       space=compute_space_score(geodesic_error, cone, lensing),
       clock=compute_clock_score(kuramoto, freq_lock, collapse, circularity),
       interact=compute_interact_score(attraction, capture, lensing_int),
       coherence=compute_coherence_score(channel, t_coh, tau_stability)
   )

3. Get fusion metrics:
   fusion = compute_fusion(branches)
   print(f"Regime: {fusion.regime}, Score: {fusion.score:.2f}")

4. Build phase diagrams across parameter sweeps.
""")
    
    return records


if __name__ == "__main__":
    test_framework()
