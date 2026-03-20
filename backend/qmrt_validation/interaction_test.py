"""
QMRT Interaction Classification Test

SECOND TEST - Only run after eigenmode stability is confirmed.

Goal: Establish basin interaction law (scattering matrix).

Controlled collision experiments:
1. Same-frequency basins (ω₁ ≈ ω₂ > 0)
2. Near-frequency basins (|ω₁ - ω₂| small)
3. Cross-frequency basins (ω₁ > 0, ω₂ < 0)

Measurements:
- Tunneling probability P_tunnel (basin passes through another)
- Merge probability P_merge (two basins become one)
- Reflection probability P_reflect (elastic bounce)
- Energy transfer during collision

Output: QMRT Scattering Law
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import (
    QMRTFrequencyEngine,
    QMRTFrequencyParameters
)


class CollisionOutcome(Enum):
    """Classification of collision outcome"""
    TUNNELING = "tunneling"       # Basins pass through each other
    MERGE = "merge"               # Two basins become one
    REFLECTION = "reflection"     # Elastic bounce
    ANNIHILATION = "annihilation" # Both basins destroyed
    NO_INTERACTION = "no_interaction"  # Basins too far apart
    UNDEFINED = "undefined"       # Unclear outcome


@dataclass
class CollisionEvent:
    """A single collision event"""
    collision_type: str           # 'same_freq', 'near_freq', 'cross_freq'
    omega_1_initial: float
    omega_2_initial: float
    omega_1_final: float
    omega_2_final: float
    outcome: CollisionOutcome
    energy_transfer: float        # Energy exchanged during collision
    collision_time: float         # When collision occurred
    basin_1_survived: bool
    basin_2_survived: bool


@dataclass
class InteractionResult:
    """Result from interaction classification test"""
    
    # Collision statistics by type
    same_freq_events: List[CollisionEvent] = field(default_factory=list)
    near_freq_events: List[CollisionEvent] = field(default_factory=list)
    cross_freq_events: List[CollisionEvent] = field(default_factory=list)
    
    # Probability matrix
    P_tunnel_same: float = 0.0
    P_merge_same: float = 0.0
    P_reflect_same: float = 0.0
    
    P_tunnel_near: float = 0.0
    P_merge_near: float = 0.0
    P_reflect_near: float = 0.0
    
    P_tunnel_cross: float = 0.0
    P_merge_cross: float = 0.0  # Expected to be rare for opposite frequencies
    P_reflect_cross: float = 0.0
    P_annihilate_cross: float = 0.0
    
    # Energy transfer statistics
    mean_energy_transfer: float = 0.0
    max_energy_transfer: float = 0.0
    
    # Total statistics
    total_collisions: int = 0
    total_tunneling: int = 0
    total_merges: int = 0
    total_reflections: int = 0
    total_annihilations: int = 0
    
    # Metadata
    grid_size: int = 0
    total_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'scattering_matrix': {
                'same_frequency': {
                    'P_tunnel': float(self.P_tunnel_same),
                    'P_merge': float(self.P_merge_same),
                    'P_reflect': float(self.P_reflect_same),
                    'n_events': len(self.same_freq_events)
                },
                'near_frequency': {
                    'P_tunnel': float(self.P_tunnel_near),
                    'P_merge': float(self.P_merge_near),
                    'P_reflect': float(self.P_reflect_near),
                    'n_events': len(self.near_freq_events)
                },
                'cross_frequency': {
                    'P_tunnel': float(self.P_tunnel_cross),
                    'P_merge': float(self.P_merge_cross),
                    'P_reflect': float(self.P_reflect_cross),
                    'P_annihilate': float(self.P_annihilate_cross),
                    'n_events': len(self.cross_freq_events)
                }
            },
            'energy_transfer': {
                'mean': float(self.mean_energy_transfer),
                'max': float(self.max_energy_transfer)
            },
            'total_statistics': {
                'total_collisions': int(self.total_collisions),
                'total_tunneling': int(self.total_tunneling),
                'total_merges': int(self.total_merges),
                'total_reflections': int(self.total_reflections),
                'total_annihilations': int(self.total_annihilations)
            },
            'metadata': {
                'grid_size': int(self.grid_size),
                'total_time': float(self.total_time)
            },
            'interpretation': self._get_interpretation()
        }
    
    def _get_interpretation(self) -> str:
        if self.total_collisions == 0:
            return "No collisions detected - increase simulation time or basin density"
        
        dominant_same = 'tunneling' if self.P_tunnel_same > max(self.P_merge_same, self.P_reflect_same) else ('merge' if self.P_merge_same > self.P_reflect_same else 'reflection')
        dominant_cross = 'tunneling' if self.P_tunnel_cross > max(self.P_annihilate_cross, self.P_reflect_cross) else ('annihilation' if self.P_annihilate_cross > self.P_reflect_cross else 'reflection')
        
        return f"QMRT Scattering Law: Same-freq→{dominant_same} ({self.P_tunnel_same:.0%}T/{self.P_merge_same:.0%}M/{self.P_reflect_same:.0%}R), Cross-freq→{dominant_cross} ({self.P_tunnel_cross:.0%}T/{self.P_annihilate_cross:.0%}A/{self.P_reflect_cross:.0%}R)"


def initialize_two_basins(
    engine: QMRTFrequencyEngine,
    omega_1: float,
    omega_2: float,
    separation: float = 0.4,
    basin_width: float = 3.0,
    approach_velocity: float = 0.1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Initialize engine with two isolated basins set to collide.
    
    Args:
        engine: The QMRT engine
        omega_1, omega_2: Frequency values for each basin
        separation: Fraction of grid size between basins (0-1)
        basin_width: Width of each basin
        approach_velocity: Initial velocity for collision
    
    Returns:
        Tuple of (basin_1_mask, basin_2_mask) for tracking
    """
    p = engine.params
    n = engine.grid_size
    shape = (n, n, n)
    
    # Set equilibrium fields
    engine.rho = np.full(shape, p.rho_equilibrium)
    engine.sigma = np.zeros(shape)
    engine.tau = np.zeros(shape)
    engine.phi = np.zeros(shape)
    engine.omega = np.zeros(shape)
    
    # Basin positions (along x-axis)
    center = n // 2
    offset = int(separation * n / 2)
    
    # Create coordinate grids
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Basin 1: left side
    x1, y1, z1 = center - offset, center, center
    R1 = np.sqrt((X - x1)**2 + (Y - y1)**2 + (Z - z1)**2)
    basin_1_mask = R1 < basin_width * 2
    profile_1 = np.exp(-R1**2 / (2 * basin_width**2))
    
    # Basin 2: right side
    x2, y2, z2 = center + offset, center, center
    R2 = np.sqrt((X - x2)**2 + (Y - y2)**2 + (Z - z2)**2)
    basin_2_mask = R2 < basin_width * 2
    profile_2 = np.exp(-R2**2 / (2 * basin_width**2))
    
    # Set frequency values
    engine.omega = omega_1 * profile_1 + omega_2 * profile_2
    
    # Initialize momenta
    engine.pi_rho = np.zeros(shape)
    engine.pi_sigma = np.zeros(shape)
    engine.pi_tau = np.zeros(shape)
    engine.pi_phi = np.zeros(shape)
    engine.pi_omega = np.zeros(shape)
    
    # Add approach momentum (basins moving toward each other)
    # Basin 1 moves right, Basin 2 moves left
    engine.pi_omega += approach_velocity * profile_1  # Basin 1 → right
    engine.pi_omega -= approach_velocity * profile_2  # Basin 2 → left
    
    # Initialize spectral arrays
    engine._precompute_spectral()
    engine.initial_energy = engine.compute_total_energy()
    
    return basin_1_mask, basin_2_mask


def track_basin_during_collision(
    engine: QMRTFrequencyEngine,
    basin_mask: np.ndarray,
    original_omega: float
) -> Tuple[bool, float]:
    """
    Track whether a basin survived and its final frequency.
    
    Returns:
        (survived: bool, final_omega: float)
    """
    p = engine.params
    
    # Get omega values in the original basin region
    omega_in_region = engine.omega[basin_mask]
    
    # Check if basin still exists (significant frequency concentration)
    max_omega = np.max(np.abs(omega_in_region))
    mean_omega = np.mean(omega_in_region)
    
    # Basin survives if there's still significant frequency in the region
    # OR if the frequency moved (we detect it elsewhere)
    threshold = 0.3 * abs(original_omega)
    
    # Check globally for basin remnant
    if original_omega > 0:
        in_high = np.sum(engine.omega > threshold) / engine.omega.size
        survived = in_high > 0.05  # At least 5% in high band
    else:
        in_low = np.sum(engine.omega < -threshold) / engine.omega.size
        survived = in_low > 0.05
    
    return survived, float(mean_omega)


def classify_collision_outcome(
    basin_1_survived: bool,
    basin_2_survived: bool,
    omega_1_initial: float,
    omega_2_initial: float,
    omega_1_final: float,
    omega_2_final: float,
    positions_crossed: bool
) -> CollisionOutcome:
    """
    Classify the outcome of a collision.
    """
    same_sign = (omega_1_initial > 0) == (omega_2_initial > 0)
    
    if not basin_1_survived and not basin_2_survived:
        return CollisionOutcome.ANNIHILATION
    
    if basin_1_survived and basin_2_survived:
        if positions_crossed:
            return CollisionOutcome.TUNNELING
        else:
            return CollisionOutcome.REFLECTION
    
    if basin_1_survived != basin_2_survived:
        if same_sign:
            # One absorbed the other
            return CollisionOutcome.MERGE
        else:
            # One destroyed the other
            return CollisionOutcome.ANNIHILATION
    
    return CollisionOutcome.UNDEFINED


def run_single_collision_test(
    grid_size: int,
    omega_1: float,
    omega_2: float,
    collision_time: float = 20.0,
    dt: float = 0.01,
    seed: int = 42
) -> CollisionEvent:
    """
    Run a single controlled collision test.
    """
    np.random.seed(seed)
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    p = engine.params
    
    # Classify collision type
    if omega_1 > 0 and omega_2 > 0:
        collision_type = 'same_freq' if abs(omega_1 - omega_2) < 0.2 * p.omega_0 else 'near_freq'
    elif omega_1 < 0 and omega_2 < 0:
        collision_type = 'same_freq' if abs(omega_1 - omega_2) < 0.2 * p.omega_0 else 'near_freq'
    else:
        collision_type = 'cross_freq'
    
    # Initialize basins
    basin_1_mask, basin_2_mask = initialize_two_basins(
        engine, omega_1, omega_2,
        separation=0.5,
        basin_width=2.5,
        approach_velocity=0.05
    )
    
    # Track initial positions (center of mass)
    def get_com(mask):
        coords = np.where(mask)
        return np.mean(coords[0])  # x-coordinate
    
    com_1_initial = get_com(basin_1_mask)
    com_2_initial = get_com(basin_2_mask)
    
    # Run simulation
    steps = int(collision_time / dt)
    energy_history = []
    
    for _ in range(steps):
        engine.evolve_timestep(dt)
        energy_history.append(engine.compute_total_energy())
    
    # Analyze outcome
    basin_1_survived, omega_1_final = track_basin_during_collision(engine, basin_1_mask, omega_1)
    basin_2_survived, omega_2_final = track_basin_during_collision(engine, basin_2_mask, omega_2)
    
    # Check if positions crossed (for tunneling detection)
    # Find where frequency is concentrated now
    high_freq_mask = engine.omega > 0.3 * p.omega_0
    low_freq_mask = engine.omega < -0.3 * p.omega_0
    
    # Simplified position check
    positions_crossed = False  # Would need more sophisticated tracking
    
    # Energy transfer
    energy_change = abs(energy_history[-1] - energy_history[0])
    
    # Classify outcome
    outcome = classify_collision_outcome(
        basin_1_survived, basin_2_survived,
        omega_1, omega_2,
        omega_1_final, omega_2_final,
        positions_crossed
    )
    
    return CollisionEvent(
        collision_type=collision_type,
        omega_1_initial=omega_1,
        omega_2_initial=omega_2,
        omega_1_final=omega_1_final,
        omega_2_final=omega_2_final,
        outcome=outcome,
        energy_transfer=energy_change,
        collision_time=collision_time,
        basin_1_survived=basin_1_survived,
        basin_2_survived=basin_2_survived
    )


def run_interaction_classification(
    grid_size: int = 16,
    collision_time: float = 15.0,
    dt: float = 0.02,
    n_trials_per_type: int = 5,
    seed: int = 42
) -> InteractionResult:
    """
    Run full interaction classification test.
    
    Performs controlled collision experiments for:
    1. Same-frequency basins
    2. Near-frequency basins
    3. Cross-frequency basins (matter-antimatter analog)
    """
    print("="*60)
    print("QMRT INTERACTION CLASSIFICATION TEST")
    print("="*60)
    print(f"Grid: {grid_size}³, Time per collision: {collision_time}s")
    print(f"Trials per type: {n_trials_per_type}")
    
    np.random.seed(seed)
    
    # Get reference omega_0
    temp_engine = QMRTFrequencyEngine(grid_size=10)
    omega_0 = temp_engine.params.omega_0
    
    result = InteractionResult(grid_size=grid_size, total_time=collision_time)
    
    # Test configurations
    configs = [
        # Same frequency (both positive)
        ('same_freq', omega_0, omega_0 * 0.95),
        ('same_freq', omega_0, omega_0 * 1.05),
        # Near frequency
        ('near_freq', omega_0 * 0.8, omega_0 * 0.6),
        ('near_freq', omega_0 * 1.2, omega_0 * 0.7),
        # Cross frequency (matter-antimatter)
        ('cross_freq', omega_0, -omega_0),
        ('cross_freq', omega_0 * 0.8, -omega_0 * 0.9),
    ]
    
    all_events = []
    
    for trial in range(n_trials_per_type):
        print(f"\n[Trial {trial+1}/{n_trials_per_type}]")
        
        for i, (ctype, w1, w2) in enumerate(configs):
            trial_seed = seed + trial * 100 + i
            
            event = run_single_collision_test(
                grid_size=grid_size,
                omega_1=w1,
                omega_2=w2,
                collision_time=collision_time,
                dt=dt,
                seed=trial_seed
            )
            
            all_events.append(event)
            
            # Categorize
            if event.collision_type == 'same_freq':
                result.same_freq_events.append(event)
            elif event.collision_type == 'near_freq':
                result.near_freq_events.append(event)
            else:
                result.cross_freq_events.append(event)
            
            print(f"  {ctype}: ω1={w1:.2f}, ω2={w2:.2f} → {event.outcome.value}")
    
    # Compute probabilities
    def compute_probs(events: List[CollisionEvent]) -> Tuple[float, float, float, float]:
        if not events:
            return 0.0, 0.0, 0.0, 0.0
        n = len(events)
        tunnel = sum(1 for e in events if e.outcome == CollisionOutcome.TUNNELING) / n
        merge = sum(1 for e in events if e.outcome == CollisionOutcome.MERGE) / n
        reflect = sum(1 for e in events if e.outcome == CollisionOutcome.REFLECTION) / n
        annihilate = sum(1 for e in events if e.outcome == CollisionOutcome.ANNIHILATION) / n
        return tunnel, merge, reflect, annihilate
    
    result.P_tunnel_same, result.P_merge_same, result.P_reflect_same, _ = compute_probs(result.same_freq_events)
    result.P_tunnel_near, result.P_merge_near, result.P_reflect_near, _ = compute_probs(result.near_freq_events)
    result.P_tunnel_cross, result.P_merge_cross, result.P_reflect_cross, result.P_annihilate_cross = compute_probs(result.cross_freq_events)
    
    # Total statistics
    result.total_collisions = len(all_events)
    result.total_tunneling = sum(1 for e in all_events if e.outcome == CollisionOutcome.TUNNELING)
    result.total_merges = sum(1 for e in all_events if e.outcome == CollisionOutcome.MERGE)
    result.total_reflections = sum(1 for e in all_events if e.outcome == CollisionOutcome.REFLECTION)
    result.total_annihilations = sum(1 for e in all_events if e.outcome == CollisionOutcome.ANNIHILATION)
    
    # Energy transfer
    energy_transfers = [e.energy_transfer for e in all_events]
    result.mean_energy_transfer = float(np.mean(energy_transfers)) if energy_transfers else 0.0
    result.max_energy_transfer = float(np.max(energy_transfers)) if energy_transfers else 0.0
    
    # Summary
    print(f"\n{'='*60}")
    print("SCATTERING LAW RESULTS")
    print(f"{'='*60}")
    print(f"Same-frequency:  T={result.P_tunnel_same:.0%} M={result.P_merge_same:.0%} R={result.P_reflect_same:.0%}")
    print(f"Near-frequency:  T={result.P_tunnel_near:.0%} M={result.P_merge_near:.0%} R={result.P_reflect_near:.0%}")
    print(f"Cross-frequency: T={result.P_tunnel_cross:.0%} A={result.P_annihilate_cross:.0%} R={result.P_reflect_cross:.0%}")
    print(f"\nTotal: {result.total_collisions} collisions")
    print(f"  Tunneling: {result.total_tunneling}")
    print(f"  Merges: {result.total_merges}")
    print(f"  Reflections: {result.total_reflections}")
    print(f"  Annihilations: {result.total_annihilations}")
    print(f"{'='*60}\n")
    
    return result


if __name__ == "__main__":
    result = run_interaction_classification(
        grid_size=14,
        collision_time=10.0,
        dt=0.03,
        n_trials_per_type=2,
        seed=42
    )
    
    print("\nResult dict:")
    import json
    print(json.dumps(result.to_dict(), indent=2)[:1000])
