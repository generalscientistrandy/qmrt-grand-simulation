#!/usr/bin/env python3
"""
QMRT Temporal Web v2: Layered Time Structure
=============================================

THEORETICAL CORRECTION:
Time is not a scalar quantity but a structured system combining:
  1. ORDERING (event clocks) → causal structure, timelines
  2. RATE (oscillator clocks) → how fast things evolve  
  3. PERSISTENCE (decay clocks) → how long things last

A timeline (event structure) is NECESSARY for time, but without rate 
and persistence, it cannot become a measurable temporal dimension.

STRUCTURE:
  T_structure = {
      ordering: event_clocks,      # defines what can happen before/after
      rate: oscillator_clocks,     # defines flow speed
      persistence: decay_clocks    # defines duration/stability
  }

LAYER METRICS:
  O (Ordering):    Causal consistency, sequence validity, timeline coherence
  R (Rate):        Phase coherence, frequency stability, cycle regularity
  P (Persistence): Lifetime consistency, decay predictability, stability

TEMPORAL EMERGENCE:
  S_time = f(O, R, P) where all three must be present and mutually consistent

KEY INSIGHT:
  Event clocks "failed" as scalar time but SUCCEED as ordering structure.
  They don't produce a good number—they produce a valid timeline.
"""

import numpy as np
from scipy.stats import spearmanr, kendalltau
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import json


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class OrderingMetrics:
    """Metrics for the ORDERING layer (event clocks)."""
    causal_consistency: float = 0.0   # Do events respect cause→effect?
    sequence_validity: float = 0.0    # Is the ordering well-defined?
    timeline_coherence: float = 0.0   # Do different event types agree on order?
    
    def score(self, weights: Tuple[float, float, float] = (0.4, 0.3, 0.3)) -> float:
        """Compute ordering layer score O."""
        w1, w2, w3 = weights
        return float(np.clip(
            w1 * self.causal_consistency + 
            w2 * self.sequence_validity + 
            w3 * self.timeline_coherence, 0, 1))
    
    def as_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RateMetrics:
    """Metrics for the RATE layer (oscillator clocks)."""
    phase_coherence: float = 0.0      # Are oscillators in sync across regions?
    frequency_stability: float = 0.0   # Is the frequency consistent over time?
    cycle_regularity: float = 0.0      # Are individual cycles regular?
    
    def score(self, weights: Tuple[float, float, float] = (0.35, 0.35, 0.3)) -> float:
        """Compute rate layer score R."""
        w1, w2, w3 = weights
        return float(np.clip(
            w1 * self.phase_coherence + 
            w2 * self.frequency_stability + 
            w3 * self.cycle_regularity, 0, 1))
    
    def as_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PersistenceMetrics:
    """Metrics for the PERSISTENCE layer (decay clocks)."""
    lifetime_consistency: float = 0.0  # Are lifetimes reproducible?
    decay_predictability: float = 0.0  # Can we predict when decay occurs?
    stability_uniformity: float = 0.0  # Is stability uniform across regions?
    
    def score(self, weights: Tuple[float, float, float] = (0.4, 0.3, 0.3)) -> float:
        """Compute persistence layer score P."""
        w1, w2, w3 = weights
        return float(np.clip(
            w1 * self.lifetime_consistency + 
            w2 * self.decay_predictability + 
            w3 * self.stability_uniformity, 0, 1))
    
    def as_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LayeredTemporalWeb:
    """Complete three-layer temporal structure."""
    ordering: OrderingMetrics = field(default_factory=OrderingMetrics)
    rate: RateMetrics = field(default_factory=RateMetrics)
    persistence: PersistenceMetrics = field(default_factory=PersistenceMetrics)
    
    # Layer scores
    O: float = 0.0  # Ordering score
    R: float = 0.0  # Rate score  
    P: float = 0.0  # Persistence score
    
    # Cross-layer consistency
    consistency_OR: float = 0.0  # Ordering-Rate alignment
    consistency_OP: float = 0.0  # Ordering-Persistence alignment
    consistency_RP: float = 0.0  # Rate-Persistence alignment
    
    # Combined metrics
    S_time: float = 0.0          # Overall temporal emergence score
    layer_balance: float = 0.0   # How balanced are the layers?
    
    def as_dict(self) -> Dict:
        return {
            'ordering': self.ordering.as_dict(),
            'rate': self.rate.as_dict(),
            'persistence': self.persistence.as_dict(),
            'layer_scores': {'O': self.O, 'R': self.R, 'P': self.P},
            'cross_layer_consistency': {
                'OR': self.consistency_OR,
                'OP': self.consistency_OP,
                'RP': self.consistency_RP,
            },
            'S_time': self.S_time,
            'layer_balance': self.layer_balance,
        }


# ============================================================
# ORDERING LAYER METRICS (Event Clocks)
# ============================================================

def compute_causal_consistency(
    event_sequences: List[List[str]],
    expected_order: List[str] = None
) -> float:
    """
    Measure whether events respect causal ordering.
    
    Example: For a rock throw, [release, flight, impact] should never
    become [impact, release, flight].
    
    Args:
        event_sequences: List of observed event sequences
        expected_order: The causally required order (if known)
    
    Returns:
        Fraction of sequences that respect causal order
    """
    if not event_sequences:
        return 0.5  # Neutral if no data
    
    if expected_order is None:
        # Use majority voting to determine expected order
        # For now, assume first sequence is reference
        expected_order = event_sequences[0]
    
    valid_count = 0
    for seq in event_sequences:
        # Check if sequence respects the expected order
        # (events can be missing, but those present must be in order)
        last_idx = -1
        is_valid = True
        for event in seq:
            if event in expected_order:
                idx = expected_order.index(event)
                if idx < last_idx:
                    is_valid = False
                    break
                last_idx = idx
        if is_valid:
            valid_count += 1
    
    return float(valid_count / len(event_sequences))


def compute_sequence_validity(
    event_times: Dict[str, List[float]],
    min_events: int = 3
) -> float:
    """
    Measure whether event timestamps define a valid sequence.
    
    Valid means: no simultaneity conflicts, monotonic where expected.
    
    Args:
        event_times: Dict mapping event_type -> list of occurrence times
        min_events: Minimum events needed for validity assessment
    """
    if not event_times:
        return 0.5
    
    total_events = sum(len(times) for times in event_times.values())
    if total_events < min_events:
        return 0.5  # Insufficient data
    
    # Check for monotonicity within each event type
    monotonic_count = 0
    total_types = 0
    
    for event_type, times in event_times.items():
        if len(times) < 2:
            continue
        total_types += 1
        times_arr = np.array(times)
        if np.all(times_arr[1:] >= times_arr[:-1]):
            monotonic_count += 1
    
    if total_types == 0:
        return 0.5
    
    return float(monotonic_count / total_types)


def compute_timeline_coherence(
    ordering_by_type: Dict[str, np.ndarray],
    reference_ordering: np.ndarray = None
) -> float:
    """
    Measure whether different event types agree on temporal ordering.
    
    If event type A says region 1 < region 2 < region 3,
    and event type B says region 1 < region 3 < region 2,
    they disagree on the timeline.
    
    Args:
        ordering_by_type: Dict mapping event_type -> rank array across regions
        reference_ordering: Optional reference to compare against
    """
    if len(ordering_by_type) < 2:
        return 0.5  # Need at least 2 event types to compare
    
    types = list(ordering_by_type.keys())
    n_pairs = 0
    agreement_sum = 0.0
    
    for i, type_i in enumerate(types):
        for j, type_j in enumerate(types):
            if i >= j:
                continue
            
            arr_i = ordering_by_type[type_i]
            arr_j = ordering_by_type[type_j]
            
            if len(arr_i) != len(arr_j) or len(arr_i) < 3:
                continue
            
            # Use Kendall tau for rank correlation
            tau, _ = kendalltau(arr_i, arr_j)
            if not np.isnan(tau):
                agreement_sum += (1 + tau) / 2  # Map [-1,1] to [0,1]
                n_pairs += 1
    
    if n_pairs == 0:
        return 0.5
    
    return float(agreement_sum / n_pairs)


def compute_ordering_layer(
    event_sequences: List[List[str]] = None,
    event_times: Dict[str, List[float]] = None,
    ordering_by_type: Dict[str, np.ndarray] = None,
    expected_order: List[str] = None
) -> OrderingMetrics:
    """Compute all ordering layer metrics."""
    
    causal = compute_causal_consistency(event_sequences or [], expected_order)
    validity = compute_sequence_validity(event_times or {})
    coherence = compute_timeline_coherence(ordering_by_type or {})
    
    return OrderingMetrics(
        causal_consistency=causal,
        sequence_validity=validity,
        timeline_coherence=coherence
    )


# ============================================================
# RATE LAYER METRICS (Oscillator Clocks)
# ============================================================

def compute_phase_coherence(
    phases: np.ndarray,
    times: np.ndarray = None
) -> float:
    """
    Measure phase coherence across oscillators (Kuramoto order parameter).
    
    r = |⟨e^{iφ}⟩| where r ∈ [0,1]
    r = 1: perfect sync
    r = 0: random phases
    """
    if len(phases) < 2:
        return 0.5
    
    # Kuramoto order parameter
    r = np.abs(np.mean(np.exp(1j * phases)))
    return float(r)


def compute_frequency_stability(
    frequencies: np.ndarray,
    times: np.ndarray = None
) -> float:
    """
    Measure how stable frequencies are over time/space.
    
    Returns 1 - normalized_variance (high stability = low variance).
    """
    if len(frequencies) < 2:
        return 0.5
    
    mean_freq = np.mean(frequencies)
    if mean_freq == 0:
        return 0.5
    
    cv = np.std(frequencies) / mean_freq  # Coefficient of variation
    stability = np.exp(-cv)  # Map CV to [0,1], high CV → low stability
    
    return float(np.clip(stability, 0, 1))


def compute_cycle_regularity(
    cycle_periods: np.ndarray
) -> float:
    """
    Measure how regular individual oscillation cycles are.
    
    Regular cycles have consistent period lengths.
    """
    if len(cycle_periods) < 2:
        return 0.5
    
    mean_period = np.mean(cycle_periods)
    if mean_period == 0:
        return 0.5
    
    cv = np.std(cycle_periods) / mean_period
    regularity = np.exp(-2 * cv)  # More sensitive to irregularity
    
    return float(np.clip(regularity, 0, 1))


def compute_rate_layer(
    phases: np.ndarray = None,
    frequencies: np.ndarray = None,
    cycle_periods: np.ndarray = None
) -> RateMetrics:
    """Compute all rate layer metrics."""
    
    phase_coh = compute_phase_coherence(phases if phases is not None else np.array([]))
    freq_stab = compute_frequency_stability(frequencies if frequencies is not None else np.array([]))
    cycle_reg = compute_cycle_regularity(cycle_periods if cycle_periods is not None else np.array([]))
    
    return RateMetrics(
        phase_coherence=phase_coh,
        frequency_stability=freq_stab,
        cycle_regularity=cycle_reg
    )


# ============================================================
# PERSISTENCE LAYER METRICS (Decay Clocks)
# ============================================================

def compute_lifetime_consistency(
    lifetimes: np.ndarray,
    by_region: Dict[str, np.ndarray] = None
) -> float:
    """
    Measure how consistent/reproducible lifetimes are.
    
    Low coefficient of variation = high consistency.
    """
    if len(lifetimes) < 2:
        return 0.5
    
    mean_life = np.mean(lifetimes)
    if mean_life == 0:
        return 0.5
    
    cv = np.std(lifetimes) / mean_life
    consistency = np.exp(-cv)
    
    return float(np.clip(consistency, 0, 1))


def compute_decay_predictability(
    actual_lifetimes: np.ndarray,
    predicted_lifetimes: np.ndarray = None
) -> float:
    """
    Measure how predictable decay events are.
    
    If predicted lifetimes are provided, compute correlation.
    Otherwise, use autocorrelation of lifetime series.
    """
    if len(actual_lifetimes) < 3:
        return 0.5
    
    if predicted_lifetimes is not None and len(predicted_lifetimes) == len(actual_lifetimes):
        corr = np.corrcoef(actual_lifetimes, predicted_lifetimes)[0, 1]
        if np.isnan(corr):
            return 0.5
        return float((1 + corr) / 2)  # Map to [0,1]
    
    # Use lag-1 autocorrelation as proxy for predictability
    if len(actual_lifetimes) < 4:
        return 0.5
    
    autocorr = np.corrcoef(actual_lifetimes[:-1], actual_lifetimes[1:])[0, 1]
    if np.isnan(autocorr):
        return 0.5
    
    return float((1 + autocorr) / 2)


def compute_stability_uniformity(
    lifetimes_by_region: Dict[str, np.ndarray]
) -> float:
    """
    Measure how uniform stability is across different regions.
    
    High uniformity = similar mean lifetimes across regions.
    """
    if len(lifetimes_by_region) < 2:
        return 0.5
    
    region_means = []
    for region, lifetimes in lifetimes_by_region.items():
        if len(lifetimes) > 0:
            region_means.append(np.mean(lifetimes))
    
    if len(region_means) < 2:
        return 0.5
    
    region_means = np.array(region_means)
    global_mean = np.mean(region_means)
    
    if global_mean == 0:
        return 0.5
    
    cv = np.std(region_means) / global_mean
    uniformity = np.exp(-cv)
    
    return float(np.clip(uniformity, 0, 1))


def compute_persistence_layer(
    lifetimes: np.ndarray = None,
    predicted_lifetimes: np.ndarray = None,
    lifetimes_by_region: Dict[str, np.ndarray] = None
) -> PersistenceMetrics:
    """Compute all persistence layer metrics."""
    
    consistency = compute_lifetime_consistency(lifetimes if lifetimes is not None else np.array([]))
    predictability = compute_decay_predictability(
        lifetimes if lifetimes is not None else np.array([]),
        predicted_lifetimes
    )
    uniformity = compute_stability_uniformity(lifetimes_by_region or {})
    
    return PersistenceMetrics(
        lifetime_consistency=consistency,
        decay_predictability=predictability,
        stability_uniformity=uniformity
    )


# ============================================================
# CROSS-LAYER CONSISTENCY
# ============================================================

def compute_cross_layer_consistency(
    ordering_ranks: np.ndarray,
    rate_values: np.ndarray,
    persistence_values: np.ndarray
) -> Tuple[float, float, float]:
    """
    Compute consistency between temporal layers.
    
    High consistency means the layers agree on which regions are "fast" or "slow".
    
    Returns: (OR_consistency, OP_consistency, RP_consistency)
    """
    n = min(len(ordering_ranks), len(rate_values), len(persistence_values))
    
    if n < 3:
        return 0.5, 0.5, 0.5
    
    O = ordering_ranks[:n]
    R = rate_values[:n]
    P = persistence_values[:n]
    
    # Spearman correlations
    rho_OR, _ = spearmanr(O, R)
    rho_OP, _ = spearmanr(O, P)
    rho_RP, _ = spearmanr(R, P)
    
    # Map to [0,1]
    def map_corr(rho):
        if np.isnan(rho):
            return 0.5
        return float((1 + rho) / 2)
    
    return map_corr(rho_OR), map_corr(rho_OP), map_corr(rho_RP)


# ============================================================
# COMBINED TEMPORAL EMERGENCE
# ============================================================

def compute_temporal_emergence(
    O: float,
    R: float, 
    P: float,
    consistency_OR: float,
    consistency_OP: float,
    consistency_RP: float,
    weights: Dict[str, float] = None
) -> Tuple[float, float]:
    """
    Compute overall temporal emergence score.
    
    Time emerges when:
    1. All three layers are present (O, R, P > threshold)
    2. Layers are mutually consistent
    3. Layers are balanced (no single layer dominates)
    
    Returns: (S_time, layer_balance)
    """
    if weights is None:
        weights = {
            'O': 0.25,      # Ordering weight
            'R': 0.35,      # Rate weight (slightly higher - most measurable)
            'P': 0.25,      # Persistence weight
            'consistency': 0.15  # Cross-layer consistency weight
        }
    
    # Layer average
    layer_mean = weights['O'] * O + weights['R'] * R + weights['P'] * P
    
    # Consistency average
    consistency_mean = (consistency_OR + consistency_OP + consistency_RP) / 3
    
    # Layer balance (1 - normalized spread)
    layer_std = np.std([O, R, P])
    layer_balance = 1 - layer_std
    
    # Combined score
    # High score requires: all layers present, consistent, and balanced
    S_time = layer_mean * (1 + weights['consistency'] * (consistency_mean - 0.5)) * layer_balance
    
    return float(np.clip(S_time, 0, 1)), float(layer_balance)


def analyze_layered_temporal_web(
    # Ordering layer inputs
    event_sequences: List[List[str]] = None,
    event_times: Dict[str, List[float]] = None,
    ordering_by_type: Dict[str, np.ndarray] = None,
    # Rate layer inputs
    phases: np.ndarray = None,
    frequencies: np.ndarray = None,
    cycle_periods: np.ndarray = None,
    # Persistence layer inputs
    lifetimes: np.ndarray = None,
    lifetimes_by_region: Dict[str, np.ndarray] = None,
    # Cross-layer inputs
    ordering_ranks: np.ndarray = None,
    rate_values: np.ndarray = None,
    persistence_values: np.ndarray = None,
) -> LayeredTemporalWeb:
    """
    Complete layered temporal web analysis.
    """
    # Compute each layer
    ordering = compute_ordering_layer(event_sequences, event_times, ordering_by_type)
    rate = compute_rate_layer(phases, frequencies, cycle_periods)
    persistence = compute_persistence_layer(lifetimes, None, lifetimes_by_region)
    
    # Layer scores
    O = ordering.score()
    R = rate.score()
    P = persistence.score()
    
    # Cross-layer consistency
    if ordering_ranks is not None and rate_values is not None and persistence_values is not None:
        consistency_OR, consistency_OP, consistency_RP = compute_cross_layer_consistency(
            ordering_ranks, rate_values, persistence_values
        )
    else:
        consistency_OR = consistency_OP = consistency_RP = 0.5
    
    # Combined emergence
    S_time, layer_balance = compute_temporal_emergence(
        O, R, P, consistency_OR, consistency_OP, consistency_RP
    )
    
    return LayeredTemporalWeb(
        ordering=ordering,
        rate=rate,
        persistence=persistence,
        O=O,
        R=R,
        P=P,
        consistency_OR=consistency_OR,
        consistency_OP=consistency_OP,
        consistency_RP=consistency_RP,
        S_time=S_time,
        layer_balance=layer_balance,
    )


# ============================================================
# TEST WITH CURRENT QMRT DATA
# ============================================================

def test_with_current_data():
    """Test the layered framework with current QMRT results."""
    
    print("=" * 70)
    print("LAYERED TEMPORAL WEB TEST")
    print("=" * 70)
    print()
    print("Time = Ordering + Rate + Persistence")
    print("       (event)    (osc)   (decay)")
    print()
    
    # --------------------------------------------------------
    # ORDERING LAYER (Event Clocks)
    # --------------------------------------------------------
    print("-" * 70)
    print("1. ORDERING LAYER (Event Clocks)")
    print("-" * 70)
    
    # From prior tests: events primarily at transport edges
    # Ordering by region: [1, 35, 1] - only edge has events
    ordering_by_type = {
        'threshold_crossing': np.array([1, 35, 1]),  # high, edge, quiet
        'amplitude_peak': np.array([8, 15, 3]),      # follows structure somewhat
    }
    
    # Simulated event sequences (causal order should be: excite → propagate → absorb)
    event_sequences = [
        ['excite', 'propagate', 'absorb'],
        ['excite', 'propagate', 'absorb'],
        ['excite', 'absorb'],  # Missing propagate but order preserved
        ['propagate', 'excite', 'absorb'],  # VIOLATION
    ]
    
    ordering = compute_ordering_layer(
        event_sequences=event_sequences,
        ordering_by_type=ordering_by_type,
        expected_order=['excite', 'propagate', 'absorb']
    )
    O = ordering.score()
    
    print(f"  Causal consistency:  {ordering.causal_consistency:.3f}")
    print(f"  Sequence validity:   {ordering.sequence_validity:.3f}")
    print(f"  Timeline coherence:  {ordering.timeline_coherence:.3f}")
    print(f"  → O (Ordering score): {O:.3f}")
    
    # --------------------------------------------------------
    # RATE LAYER (Oscillator Clocks)
    # --------------------------------------------------------
    print()
    print("-" * 70)
    print("2. RATE LAYER (Oscillator Clocks)")
    print("-" * 70)
    
    # From prior tests: 6 cycle divergence, 11.2% collapse improvement
    # Phases across regions at t=final
    phases = np.array([63.9, 31.6, 27.9])  # radians (from process_clocks_test)
    frequencies = np.array([0.95, 0.92, 0.90])  # normalized frequencies
    cycle_periods = np.array([6.5, 6.8, 7.0, 6.6, 6.9])  # individual cycle lengths
    
    rate = compute_rate_layer(phases, frequencies, cycle_periods)
    R = rate.score()
    
    print(f"  Phase coherence:     {rate.phase_coherence:.3f}")
    print(f"  Frequency stability: {rate.frequency_stability:.3f}")
    print(f"  Cycle regularity:    {rate.cycle_regularity:.3f}")
    print(f"  → R (Rate score):    {R:.3f}")
    
    # --------------------------------------------------------
    # PERSISTENCE LAYER (Decay Clocks)
    # --------------------------------------------------------
    print()
    print("-" * 70)
    print("3. PERSISTENCE LAYER (Decay Clocks)")
    print("-" * 70)
    
    # From prior tests: 27.6% lifetime spread, 0.3% within-region CV
    lifetimes = np.array([9.13, 9.10, 9.15, 7.29, 7.31, 7.27, 6.98, 7.01, 6.95])
    lifetimes_by_region = {
        'high_structure': np.array([9.13, 9.10, 9.15, 9.12, 9.14]),
        'transitional': np.array([7.29, 7.31, 7.27, 7.30, 7.28]),
        'quiet': np.array([6.98, 7.01, 6.95, 6.99, 7.00]),
    }
    
    persistence = compute_persistence_layer(lifetimes, None, lifetimes_by_region)
    P = persistence.score()
    
    print(f"  Lifetime consistency:  {persistence.lifetime_consistency:.3f}")
    print(f"  Decay predictability:  {persistence.decay_predictability:.3f}")
    print(f"  Stability uniformity:  {persistence.stability_uniformity:.3f}")
    print(f"  → P (Persistence score): {P:.3f}")
    
    # --------------------------------------------------------
    # CROSS-LAYER CONSISTENCY
    # --------------------------------------------------------
    print()
    print("-" * 70)
    print("4. CROSS-LAYER CONSISTENCY")
    print("-" * 70)
    
    # Values across regions for cross-layer comparison
    ordering_ranks = np.array([3, 1, 2])  # Event count ranks (edge=1, high=3, quiet=2)
    rate_values = np.array([10, 5, 4])     # Oscillator cycles
    persistence_values = np.array([9.13, 7.29, 6.98])  # Mean lifetimes
    
    consistency_OR, consistency_OP, consistency_RP = compute_cross_layer_consistency(
        ordering_ranks, rate_values, persistence_values
    )
    
    print(f"  Ordering ↔ Rate:       {consistency_OR:.3f}")
    print(f"  Ordering ↔ Persistence: {consistency_OP:.3f}")
    print(f"  Rate ↔ Persistence:    {consistency_RP:.3f}")
    
    # --------------------------------------------------------
    # TEMPORAL EMERGENCE
    # --------------------------------------------------------
    print()
    print("-" * 70)
    print("5. TEMPORAL EMERGENCE")
    print("-" * 70)
    
    S_time, layer_balance = compute_temporal_emergence(
        O, R, P, consistency_OR, consistency_OP, consistency_RP
    )
    
    print(f"\n  Layer Scores:")
    print(f"    O (Ordering):    {O:.3f}")
    print(f"    R (Rate):        {R:.3f}")
    print(f"    P (Persistence): {P:.3f}")
    print(f"    Layer balance:   {layer_balance:.3f}")
    print()
    print(f"  Cross-Layer Consistency:")
    print(f"    Mean:            {(consistency_OR + consistency_OP + consistency_RP)/3:.3f}")
    print()
    print(f"  → S_time (Temporal Emergence): {S_time:.3f}")
    
    # --------------------------------------------------------
    # INTERPRETATION
    # --------------------------------------------------------
    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    
    print(f"""
  TIME STRUCTURE ANALYSIS:
  
  Ordering (O = {O:.2f}): {"PRESENT" if O > 0.4 else "WEAK" if O > 0.2 else "ABSENT"}
    → Event clocks define the causal skeleton
    → Sequences mostly respect cause→effect
    
  Rate (R = {R:.2f}): {"PRESENT" if R > 0.4 else "WEAK" if R > 0.2 else "ABSENT"}
    → Oscillators provide measurable flow
    → 6-cycle divergence shows local rate variation
    
  Persistence (P = {P:.2f}): {"STRONG" if P > 0.6 else "PRESENT" if P > 0.4 else "WEAK"}
    → Decay clocks show high reproducibility
    → 27.6% lifetime spread differentiates regions
    
  CONCLUSION:
    {"All three layers present → TIME CAN EMERGE" if min(O,R,P) > 0.3 else "Missing layers → TIME INCOMPLETE"}
    
  KEY INSIGHT:
    Event clocks don't fail—they succeed at defining ORDERING.
    Time requires: skeleton (events) + flow (oscillators) + duration (decay)
""")
    
    # Save results
    result = LayeredTemporalWeb(
        ordering=ordering,
        rate=rate,
        persistence=persistence,
        O=O, R=R, P=P,
        consistency_OR=consistency_OR,
        consistency_OP=consistency_OP,
        consistency_RP=consistency_RP,
        S_time=S_time,
        layer_balance=layer_balance,
    )
    
    with open('/app/backend/qmrt_topology/temporal_web_v2_test.json', 'w') as f:
        json.dump(result.as_dict(), f, indent=2)
    print("\nSaved: temporal_web_v2_test.json")
    
    return result


if __name__ == "__main__":
    test_with_current_data()
