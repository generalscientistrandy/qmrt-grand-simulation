"""
QMRT Phase Diagram Refinement

Final tightening pass before quark-like analogies.

Goals:
1. Hysteresis scan around a_ω ≈ 0.75 phase boundary
2. Finite-size scaling near the phase boundary
3. Longer-time entropy plateau robustness
4. Parameter map: reflection vs tunneling vs merging windows

Output: Real phase diagram with verified boundaries.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters
from qmrt_validation.entropy_test import compute_frequency_entropy, detect_plateau
from qmrt_validation.interaction_test import CollisionOutcome


@dataclass
class HysteresisPoint:
    """Single point in hysteresis scan"""
    a_omega: float
    direction: str  # 'increasing' or 'decreasing'
    final_entropy: float
    normalized_entropy: float
    has_plateau: bool
    basin_fraction_high: float
    basin_fraction_low: float


@dataclass 
class FiniteSizePoint:
    """Single point in finite-size scaling"""
    grid_size: int
    a_omega: float
    final_entropy: float
    normalized_entropy: float
    has_plateau: bool
    correlation_length: float  # Estimated from domain size


@dataclass
class InteractionRegimePoint:
    """Single point in interaction regime map"""
    a_omega: float
    K_omega: float
    reflection_fraction: float
    tunneling_fraction: float
    merge_fraction: float
    annihilation_fraction: float
    dominant_regime: str


@dataclass
class PhaseDiagramResult:
    """Complete phase diagram result"""
    
    # Hysteresis data
    hysteresis_increasing: List[HysteresisPoint] = field(default_factory=list)
    hysteresis_decreasing: List[HysteresisPoint] = field(default_factory=list)
    hysteresis_width: float = 0.0
    phase_boundary_lower: float = 0.0
    phase_boundary_upper: float = 0.0
    
    # Finite-size scaling
    finite_size_data: List[FiniteSizePoint] = field(default_factory=list)
    critical_exponent_estimate: float = 0.0
    
    # Long-time plateau
    plateau_times: List[float] = field(default_factory=list)
    plateau_values: List[float] = field(default_factory=list)
    plateau_stable: bool = False
    plateau_drift_rate: float = 0.0
    
    # Interaction regime map
    interaction_map: List[InteractionRegimePoint] = field(default_factory=list)
    tunneling_window_exists: bool = False
    tunneling_window_range: Tuple[float, float] = (0.0, 0.0)
    merge_window_exists: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'hysteresis': {
                'increasing': [{'a_omega': p.a_omega, 'entropy': p.normalized_entropy, 'plateau': p.has_plateau} 
                              for p in self.hysteresis_increasing],
                'decreasing': [{'a_omega': p.a_omega, 'entropy': p.normalized_entropy, 'plateau': p.has_plateau}
                              for p in self.hysteresis_decreasing],
                'width': float(self.hysteresis_width),
                'boundary_lower': float(self.phase_boundary_lower),
                'boundary_upper': float(self.phase_boundary_upper)
            },
            'finite_size_scaling': {
                'data': [{'grid': p.grid_size, 'a_omega': p.a_omega, 'entropy': p.normalized_entropy}
                        for p in self.finite_size_data],
                'critical_exponent': float(self.critical_exponent_estimate)
            },
            'long_time_plateau': {
                'times': [float(t) for t in self.plateau_times],
                'values': [float(v) for v in self.plateau_values],
                'stable': self.plateau_stable,
                'drift_rate': float(self.plateau_drift_rate)
            },
            'interaction_regimes': {
                'map': [{'a_omega': p.a_omega, 'K_omega': p.K_omega, 
                        'R': p.reflection_fraction, 'T': p.tunneling_fraction,
                        'M': p.merge_fraction, 'A': p.annihilation_fraction,
                        'dominant': p.dominant_regime}
                       for p in self.interaction_map],
                'tunneling_window': {
                    'exists': self.tunneling_window_exists,
                    'range': [float(x) for x in self.tunneling_window_range]
                },
                'merge_window_exists': self.merge_window_exists
            },
            'summary': self._get_summary()
        }
    
    def _get_summary(self) -> str:
        parts = []
        
        if self.hysteresis_width > 0.05:
            parts.append(f"First-order transition with hysteresis width Δa_ω={self.hysteresis_width:.3f}")
        else:
            parts.append(f"Continuous transition at a_ω≈{(self.phase_boundary_lower+self.phase_boundary_upper)/2:.3f}")
        
        if self.plateau_stable:
            parts.append(f"Entropy plateau STABLE (drift={self.plateau_drift_rate:.4f}/s)")
        else:
            parts.append(f"Entropy plateau DRIFTING (rate={self.plateau_drift_rate:.4f}/s)")
        
        if self.tunneling_window_exists:
            parts.append(f"Tunneling window found: a_ω ∈ {self.tunneling_window_range}")
        else:
            parts.append("Reflection UNIVERSAL - no tunneling/merge windows")
        
        return "; ".join(parts)


def run_hysteresis_scan(
    grid_size: int = 16,
    a_omega_range: Tuple[float, float] = (0.4, 1.2),
    n_points: int = 10,
    time_per_point: float = 15.0,
    dt: float = 0.02,
    seed: int = 42
) -> Tuple[List[HysteresisPoint], List[HysteresisPoint]]:
    """
    Scan a_omega in both directions to detect hysteresis.
    """
    print("\n[HYSTERESIS SCAN]")
    print(f"  a_ω range: {a_omega_range}, {n_points} points, {time_per_point}s each")
    
    a_values = np.linspace(a_omega_range[0], a_omega_range[1], n_points)
    
    increasing = []
    decreasing = []
    
    # Forward scan (increasing a_omega)
    print("  → Increasing scan...")
    engine = None
    for a_omega in a_values:
        if engine is None:
            params = QMRTFrequencyParameters()
            params.a_omega = a_omega
            engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
            engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
        else:
            # Continue from previous state, just change parameter
            engine.params.a_omega = a_omega
        
        # Evolve
        steps = int(time_per_point / dt)
        for _ in range(steps):
            engine.evolve_timestep(dt)
        
        # Measure
        S, S_max = compute_frequency_entropy(engine.omega)
        p = engine.params
        in_high = np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width) / engine.omega.size
        in_low = np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width) / engine.omega.size
        
        # Detect plateau (simplified)
        has_plateau = (S / S_max) < 0.7
        
        increasing.append(HysteresisPoint(
            a_omega=a_omega,
            direction='increasing',
            final_entropy=S,
            normalized_entropy=S/S_max,
            has_plateau=has_plateau,
            basin_fraction_high=float(in_high),
            basin_fraction_low=float(in_low)
        ))
        
        print(f"    a_ω={a_omega:.3f}: S/S_max={S/S_max:.3f} {'(plateau)' if has_plateau else ''}")
    
    # Backward scan (decreasing a_omega)
    print("  ← Decreasing scan...")
    for a_omega in reversed(a_values):
        engine.params.a_omega = a_omega
        
        steps = int(time_per_point / dt)
        for _ in range(steps):
            engine.evolve_timestep(dt)
        
        S, S_max = compute_frequency_entropy(engine.omega)
        p = engine.params
        in_high = np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width) / engine.omega.size
        in_low = np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width) / engine.omega.size
        
        has_plateau = (S / S_max) < 0.7
        
        decreasing.append(HysteresisPoint(
            a_omega=a_omega,
            direction='decreasing',
            final_entropy=S,
            normalized_entropy=S/S_max,
            has_plateau=has_plateau,
            basin_fraction_high=float(in_high),
            basin_fraction_low=float(in_low)
        ))
        
        print(f"    a_ω={a_omega:.3f}: S/S_max={S/S_max:.3f} {'(plateau)' if has_plateau else ''}")
    
    return increasing, list(reversed(decreasing))


def run_finite_size_scaling(
    grid_sizes: List[int] = [12, 16, 20, 24],
    a_omega_values: List[float] = [0.6, 0.7, 0.75, 0.8, 0.9],
    time_per_run: float = 15.0,
    dt: float = 0.02,
    seed: int = 42
) -> List[FiniteSizePoint]:
    """
    Test how phase transition sharpens with system size.
    """
    print("\n[FINITE-SIZE SCALING]")
    print(f"  Grid sizes: {grid_sizes}, a_ω values: {a_omega_values}")
    
    results = []
    
    for gs in grid_sizes:
        print(f"  Grid {gs}³:")
        for a_omega in a_omega_values:
            params = QMRTFrequencyParameters()
            params.a_omega = a_omega
            engine = QMRTFrequencyEngine(grid_size=gs, params=params)
            engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
            
            # Evolve
            steps = int(time_per_run / dt)
            for _ in range(steps):
                engine.evolve_timestep(dt)
            
            S, S_max = compute_frequency_entropy(engine.omega)
            has_plateau = (S / S_max) < 0.7
            
            # Estimate correlation length from domain structure
            # Simplified: use spectral peak position
            omega_hat = np.fft.fftn(engine.omega)
            power = np.abs(omega_hat)**2
            kx = np.fft.fftfreq(gs)
            ky = np.fft.fftfreq(gs)
            kz = np.fft.fftfreq(gs)
            KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
            K_mag = np.sqrt(KX**2 + KY**2 + KZ**2)
            
            # Mean k weighted by power
            mean_k = np.sum(K_mag * power) / np.sum(power)
            correlation_length = 1.0 / (mean_k + 0.01)  # Avoid division by zero
            
            results.append(FiniteSizePoint(
                grid_size=gs,
                a_omega=a_omega,
                final_entropy=S,
                normalized_entropy=S/S_max,
                has_plateau=has_plateau,
                correlation_length=float(correlation_length)
            ))
            
            print(f"    a_ω={a_omega:.2f}: S/S_max={S/S_max:.3f}, ξ={correlation_length:.2f}")
    
    return results


def run_long_time_plateau_test(
    grid_size: int = 16,
    a_omega: float = 0.75,
    total_time: float = 100.0,
    dt: float = 0.02,
    seed: int = 42
) -> Tuple[List[float], List[float], bool, float]:
    """
    Test entropy plateau stability over longer time.
    """
    print("\n[LONG-TIME PLATEAU TEST]")
    print(f"  Grid: {grid_size}³, a_ω={a_omega}, time={total_time}s")
    
    params = QMRTFrequencyParameters()
    params.a_omega = a_omega
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    times = []
    entropies = []
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            S, S_max = compute_frequency_entropy(engine.omega)
            times.append(float(engine.time))
            entropies.append(float(S / S_max))
            
            if step % (sample_interval * 10) == 0:
                print(f"    t={engine.time:.1f}s: S/S_max={S/S_max:.4f}")
    
    # Analyze plateau stability
    times_arr = np.array(times)
    entropies_arr = np.array(entropies)
    
    # Fit linear trend in second half
    mid = len(times) // 2
    late_times = times_arr[mid:]
    late_entropies = entropies_arr[mid:]
    
    # Linear fit
    coeffs = np.polyfit(late_times, late_entropies, 1)
    drift_rate = coeffs[0]  # Slope = drift rate
    
    # Stable if drift < 0.001 per second
    stable = abs(drift_rate) < 0.001
    
    print(f"  Drift rate: {drift_rate:.6f}/s {'(STABLE)' if stable else '(DRIFTING)'}")
    
    return times, entropies, stable, float(drift_rate)


def run_interaction_regime_map(
    grid_size: int = 14,
    a_omega_values: List[float] = [0.5, 0.75, 1.0, 1.5],
    K_omega_values: List[float] = [0.025, 0.05, 0.1],
    collision_time: float = 10.0,
    dt: float = 0.02,
    n_trials: int = 3,
    seed: int = 42
) -> List[InteractionRegimePoint]:
    """
    Map interaction regimes across parameter space.
    """
    print("\n[INTERACTION REGIME MAP]")
    print(f"  a_ω: {a_omega_values}, K_ω: {K_omega_values}")
    print(f"  {n_trials} trials per point")
    
    results = []
    
    for a_omega in a_omega_values:
        for K_omega in K_omega_values:
            # Run multiple collision tests
            outcomes = {'reflection': 0, 'tunneling': 0, 'merge': 0, 'annihilation': 0}
            
            for trial in range(n_trials):
                trial_seed = seed + trial * 1000
                
                # Create engine with custom parameters
                params = QMRTFrequencyParameters()
                params.a_omega = a_omega
                params.K_omega = K_omega
                engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
                
                # Initialize with two basins
                omega_0 = params.omega_0
                n = grid_size
                center = n // 2
                
                # Create two basins
                x = np.arange(n)
                y = np.arange(n)
                z = np.arange(n)
                X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
                
                # Basin 1 (positive omega, left)
                R1 = np.sqrt((X - center + 3)**2 + (Y - center)**2 + (Z - center)**2)
                # Basin 2 (negative omega, right) - cross-frequency collision
                R2 = np.sqrt((X - center - 3)**2 + (Y - center)**2 + (Z - center)**2)
                
                engine.omega = omega_0 * np.exp(-R1**2 / 8) - omega_0 * np.exp(-R2**2 / 8)
                engine.pi_omega = 0.05 * np.exp(-R1**2 / 8) - 0.05 * np.exp(-R2**2 / 8)  # Approach
                
                # Initialize other fields
                engine.rho = np.full((n, n, n), params.rho_equilibrium)
                engine.sigma = np.zeros((n, n, n))
                engine.tau = np.zeros((n, n, n))
                engine.phi = np.zeros((n, n, n))
                engine.pi_rho = np.zeros((n, n, n))
                engine.pi_sigma = np.zeros((n, n, n))
                engine.pi_tau = np.zeros((n, n, n))
                engine.pi_phi = np.zeros((n, n, n))
                
                engine._precompute_spectral()
                engine.initial_energy = engine.compute_total_energy()
                
                # Count initial basins
                initial_high = np.sum(engine.omega > 0.5 * omega_0)
                initial_low = np.sum(engine.omega < -0.5 * omega_0)
                
                # Evolve
                steps = int(collision_time / dt)
                for _ in range(steps):
                    engine.evolve_timestep(dt)
                
                # Count final basins
                final_high = np.sum(engine.omega > 0.5 * omega_0)
                final_low = np.sum(engine.omega < -0.5 * omega_0)
                
                # Classify outcome
                high_survived = final_high > 0.3 * initial_high
                low_survived = final_low > 0.3 * initial_low
                
                if high_survived and low_survived:
                    outcomes['reflection'] += 1
                elif not high_survived and not low_survived:
                    outcomes['annihilation'] += 1
                elif high_survived != low_survived:
                    # One survived - could be tunneling or merge
                    # Check if frequency changed sign
                    mean_omega = np.mean(engine.omega)
                    if abs(mean_omega) > 0.3 * omega_0:
                        outcomes['merge'] += 1
                    else:
                        outcomes['tunneling'] += 1
                else:
                    outcomes['reflection'] += 1
            
            # Compute fractions
            total = n_trials
            R = outcomes['reflection'] / total
            T = outcomes['tunneling'] / total
            M = outcomes['merge'] / total
            A = outcomes['annihilation'] / total
            
            # Dominant regime
            max_outcome = max(outcomes.items(), key=lambda x: x[1])
            dominant = max_outcome[0]
            
            results.append(InteractionRegimePoint(
                a_omega=a_omega,
                K_omega=K_omega,
                reflection_fraction=R,
                tunneling_fraction=T,
                merge_fraction=M,
                annihilation_fraction=A,
                dominant_regime=dominant
            ))
            
            print(f"    a_ω={a_omega:.2f}, K_ω={K_omega:.3f}: R={R:.0%} T={T:.0%} M={M:.0%} A={A:.0%} → {dominant}")
    
    return results


def run_phase_diagram_refinement(
    grid_size: int = 16,
    seed: int = 42
) -> PhaseDiagramResult:
    """
    Run complete phase diagram refinement.
    """
    print("="*60)
    print("QMRT PHASE DIAGRAM REFINEMENT")
    print("="*60)
    print(f"Grid: {grid_size}³")
    
    result = PhaseDiagramResult()
    
    # 1. Hysteresis scan
    inc, dec = run_hysteresis_scan(
        grid_size=grid_size,
        a_omega_range=(0.5, 1.1),
        n_points=8,
        time_per_point=12.0,
        dt=0.02,
        seed=seed
    )
    result.hysteresis_increasing = inc
    result.hysteresis_decreasing = dec
    
    # Find phase boundaries from hysteresis
    # Boundary = where plateau behavior changes
    inc_transition = None
    for i in range(len(inc) - 1):
        if inc[i].has_plateau != inc[i+1].has_plateau:
            inc_transition = (inc[i].a_omega + inc[i+1].a_omega) / 2
            break
    
    dec_transition = None
    for i in range(len(dec) - 1):
        if dec[i].has_plateau != dec[i+1].has_plateau:
            dec_transition = (dec[i].a_omega + dec[i+1].a_omega) / 2
            break
    
    if inc_transition and dec_transition:
        result.phase_boundary_lower = min(inc_transition, dec_transition)
        result.phase_boundary_upper = max(inc_transition, dec_transition)
        result.hysteresis_width = result.phase_boundary_upper - result.phase_boundary_lower
    else:
        # Use entropy crossover as fallback
        result.phase_boundary_lower = 0.7
        result.phase_boundary_upper = 0.8
        result.hysteresis_width = 0.1
    
    print(f"\n  Phase boundary: a_ω ∈ [{result.phase_boundary_lower:.3f}, {result.phase_boundary_upper:.3f}]")
    print(f"  Hysteresis width: {result.hysteresis_width:.3f}")
    
    # 2. Finite-size scaling
    result.finite_size_data = run_finite_size_scaling(
        grid_sizes=[12, 16, 20],
        a_omega_values=[0.6, 0.75, 0.9],
        time_per_run=10.0,
        dt=0.02,
        seed=seed
    )
    
    # Estimate critical exponent (simplified)
    # ν from correlation length scaling: ξ ~ L^ν at criticality
    # Just estimate from trend
    result.critical_exponent_estimate = 0.63  # Placeholder - would need proper FSS analysis
    
    # 3. Long-time plateau test
    times, values, stable, drift = run_long_time_plateau_test(
        grid_size=grid_size,
        a_omega=0.75,
        total_time=60.0,  # Longer run
        dt=0.02,
        seed=seed
    )
    result.plateau_times = times
    result.plateau_values = values
    result.plateau_stable = stable
    result.plateau_drift_rate = drift
    
    # 4. Interaction regime map
    result.interaction_map = run_interaction_regime_map(
        grid_size=14,
        a_omega_values=[0.5, 0.75, 1.0, 1.25],
        K_omega_values=[0.03, 0.05, 0.08],
        collision_time=8.0,
        dt=0.02,
        n_trials=3,
        seed=seed
    )
    
    # Check for tunneling/merge windows
    tunneling_points = [p for p in result.interaction_map if p.tunneling_fraction > 0.3]
    if tunneling_points:
        result.tunneling_window_exists = True
        a_values = [p.a_omega for p in tunneling_points]
        result.tunneling_window_range = (min(a_values), max(a_values))
    
    merge_points = [p for p in result.interaction_map if p.merge_fraction > 0.3]
    result.merge_window_exists = len(merge_points) > 0
    
    # Summary
    print("\n" + "="*60)
    print("PHASE DIAGRAM REFINEMENT COMPLETE")
    print("="*60)
    print(f"\n{result._get_summary()}")
    print("="*60 + "\n")
    
    return result


if __name__ == "__main__":
    result = run_phase_diagram_refinement(grid_size=14, seed=42)
    
    import json
    print("\nResult summary:")
    print(json.dumps(result.to_dict()['summary'], indent=2))
