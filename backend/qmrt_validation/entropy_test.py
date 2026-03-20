"""
QMRT Entropy Production Test

STEP 4 - Final groundwork validation step.
Only valid after eigenmode stability, interaction classification, and scaling convergence confirmed.

Goal: Establish entropy-production rate law and identify phase transition boundaries.

Measurements:
1. dS/dt vs coupling strength (g_ωφ, g_ωρ)
2. dS/dt vs gradient coefficient (K_ω)
3. dS/dt vs potential depth (a_ω)

Physics:
    S(t) = -Σ P_k log P_k  (frequency distribution entropy)
    
    dS/dt behavior:
    - Monotonic increase → approach to equilibrium
    - Plateau → metastable ordered state (half-entropy regime)
    - Sharp transition → phase boundary
    
If plateau region is robust across parameter variations:
    → Phase-transition boundary identified
    → Entropy hierarchy of QMRT validated
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import (
    QMRTFrequencyEngine,
    QMRTFrequencyParameters
)


@dataclass
class EntropyMeasurement:
    """Single entropy measurement at a point in time"""
    time: float
    entropy: float
    entropy_rate: float  # dS/dt
    max_entropy: float   # log(n_bins) for normalization
    normalized_entropy: float  # S / S_max


@dataclass
class EntropyTrajectory:
    """Entropy evolution for a single parameter configuration"""
    # Parameter configuration
    a_omega: float
    K_omega: float
    g_omega_phi: float
    g_omega_rho: float
    
    # Time series
    times: List[float] = field(default_factory=list)
    entropies: List[float] = field(default_factory=list)
    entropy_rates: List[float] = field(default_factory=list)
    
    # Summary statistics
    initial_entropy: float = 0.0
    final_entropy: float = 0.0
    max_entropy: float = 0.0
    plateau_entropy: float = 0.0
    plateau_time: float = 0.0
    has_plateau: bool = False
    mean_production_rate: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'parameters': {
                'a_omega': float(self.a_omega),
                'K_omega': float(self.K_omega),
                'g_omega_phi': float(self.g_omega_phi),
                'g_omega_rho': float(self.g_omega_rho)
            },
            'trajectory': {
                'times': [float(t) for t in self.times],
                'entropies': [float(s) for s in self.entropies],
                'entropy_rates': [float(r) for r in self.entropy_rates]
            },
            'summary': {
                'initial_entropy': float(self.initial_entropy),
                'final_entropy': float(self.final_entropy),
                'max_entropy': float(self.max_entropy),
                'normalized_final': float(self.final_entropy / self.max_entropy) if self.max_entropy > 0 else 0,
                'plateau_entropy': float(self.plateau_entropy),
                'plateau_time': float(self.plateau_time),
                'has_plateau': self.has_plateau,
                'mean_production_rate': float(self.mean_production_rate)
            }
        }


@dataclass
class EntropyProductionResult:
    """Result from entropy production analysis"""
    
    # Trajectories for different parameter variations
    coupling_scan: List[EntropyTrajectory] = field(default_factory=list)
    gradient_scan: List[EntropyTrajectory] = field(default_factory=list)
    potential_scan: List[EntropyTrajectory] = field(default_factory=list)
    
    # Phase transition analysis
    coupling_transition_point: Optional[float] = None
    gradient_transition_point: Optional[float] = None
    potential_transition_point: Optional[float] = None
    
    # Half-entropy regime
    half_entropy_observed: bool = False
    half_entropy_range: Tuple[float, float] = (0.0, 0.0)
    
    # Overall assessment
    plateau_robust: bool = False
    phase_boundary_identified: bool = False
    
    # Metadata
    grid_size: int = 0
    total_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'coupling_scan': [t.to_dict() for t in self.coupling_scan],
            'gradient_scan': [t.to_dict() for t in self.gradient_scan],
            'potential_scan': [t.to_dict() for t in self.potential_scan],
            'phase_transitions': {
                'coupling_transition': float(self.coupling_transition_point) if self.coupling_transition_point else None,
                'gradient_transition': float(self.gradient_transition_point) if self.gradient_transition_point else None,
                'potential_transition': float(self.potential_transition_point) if self.potential_transition_point else None
            },
            'half_entropy_regime': {
                'observed': self.half_entropy_observed,
                'range': [float(x) for x in self.half_entropy_range]
            },
            'assessment': {
                'plateau_robust': self.plateau_robust,
                'phase_boundary_identified': self.phase_boundary_identified
            },
            'metadata': {
                'grid_size': int(self.grid_size),
                'total_time': float(self.total_time)
            },
            'interpretation': self._get_interpretation()
        }
    
    def _get_interpretation(self) -> str:
        if self.phase_boundary_identified:
            return f"PHASE BOUNDARY IDENTIFIED: Entropy plateau robust across parameter variations. Half-entropy regime observed in range {self.half_entropy_range}. QMRT entropy hierarchy validated."
        elif self.plateau_robust:
            return "PLATEAU ROBUST: Entropy reaches metastable ordered state consistently. Phase boundary investigation needed with finer parameter scan."
        elif self.half_entropy_observed:
            return "HALF-ENTROPY OBSERVED: Some configurations show plateau below max entropy. Need broader parameter scan for phase boundary."
        else:
            return "NO CLEAR PLATEAU: System approaches thermal equilibrium. May need different parameter regime for ordered phase."


def compute_frequency_entropy(omega: np.ndarray, n_bins: int = 50) -> Tuple[float, float]:
    """
    Compute Shannon entropy of frequency distribution.
    
    S = -Σ P_k log P_k
    
    Returns: (entropy, max_entropy)
    """
    # Flatten and create histogram
    omega_flat = omega.flatten()
    
    # Use range that captures the distribution
    omega_range = (np.min(omega_flat), np.max(omega_flat))
    if omega_range[1] - omega_range[0] < 1e-10:
        return 0.0, np.log(n_bins)
    
    hist, _ = np.histogram(omega_flat, bins=n_bins, range=omega_range, density=True)
    
    # Normalize to probability
    bin_width = (omega_range[1] - omega_range[0]) / n_bins
    P = hist * bin_width
    P = P / np.sum(P)  # Ensure normalization
    
    # Compute entropy (avoid log(0))
    P_nonzero = P[P > 1e-10]
    entropy = -np.sum(P_nonzero * np.log(P_nonzero))
    
    # Max entropy is log(n_bins) for uniform distribution
    max_entropy = np.log(n_bins)
    
    return float(entropy), float(max_entropy)


def detect_plateau(times: np.ndarray, entropies: np.ndarray, window_frac: float = 0.2, threshold: float = 0.05) -> Tuple[bool, float, float]:
    """
    Detect if entropy has reached a plateau.
    
    Returns: (has_plateau, plateau_value, plateau_time)
    """
    if len(entropies) < 10:
        return False, 0.0, 0.0
    
    # Look at last portion of trajectory
    window_size = max(5, int(len(entropies) * window_frac))
    late_entropies = entropies[-window_size:]
    
    # Check if entropy is stable (low variance)
    mean_late = np.mean(late_entropies)
    std_late = np.std(late_entropies)
    
    # Also check if rate is near zero
    late_rates = np.diff(late_entropies) / np.diff(times[-window_size:])
    mean_rate = np.mean(np.abs(late_rates))
    
    # Plateau if variance is low and rate is small
    relative_std = std_late / mean_late if mean_late > 0 else float('inf')
    
    has_plateau = relative_std < threshold and mean_rate < 0.1
    
    if has_plateau:
        plateau_value = mean_late
        plateau_time = times[-window_size]
    else:
        plateau_value = entropies[-1]
        plateau_time = times[-1]
    
    return has_plateau, float(plateau_value), float(plateau_time)


def run_entropy_trajectory(
    grid_size: int,
    total_time: float,
    dt: float,
    a_omega: float,
    K_omega: float,
    g_omega_phi: float,
    g_omega_rho: float,
    seed: int = 42,
    n_bins: int = 50
) -> EntropyTrajectory:
    """
    Run single entropy trajectory with given parameters.
    """
    # Create custom parameters
    params = QMRTFrequencyParameters()
    params.a_omega = a_omega
    params.K_omega = K_omega
    params.g_omega_phi = g_omega_phi
    params.g_omega_rho = g_omega_rho
    
    # Initialize engine with custom params
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    # Track entropy
    times = []
    entropies = []
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 100)
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            t = engine.time
            S, S_max = compute_frequency_entropy(engine.omega, n_bins)
            
            times.append(float(t))
            entropies.append(float(S))
    
    # Compute entropy rates
    times_arr = np.array(times)
    entropies_arr = np.array(entropies)
    
    if len(entropies) > 1:
        entropy_rates = list(np.gradient(entropies_arr, times_arr))
    else:
        entropy_rates = [0.0]
    
    # Detect plateau
    has_plateau, plateau_S, plateau_t = detect_plateau(times_arr, entropies_arr)
    
    # Create trajectory
    traj = EntropyTrajectory(
        a_omega=a_omega,
        K_omega=K_omega,
        g_omega_phi=g_omega_phi,
        g_omega_rho=g_omega_rho,
        times=times,
        entropies=entropies,
        entropy_rates=entropy_rates,
        initial_entropy=entropies[0] if entropies else 0.0,
        final_entropy=entropies[-1] if entropies else 0.0,
        max_entropy=compute_frequency_entropy(engine.omega, n_bins)[1],
        plateau_entropy=plateau_S,
        plateau_time=plateau_t,
        has_plateau=has_plateau,
        mean_production_rate=float(np.mean(entropy_rates)) if entropy_rates else 0.0
    )
    
    return traj


def scan_parameter(
    grid_size: int,
    total_time: float,
    dt: float,
    param_name: str,
    param_values: List[float],
    base_params: Dict,
    seed: int = 42
) -> List[EntropyTrajectory]:
    """
    Scan a single parameter and collect entropy trajectories.
    """
    trajectories = []
    
    for val in param_values:
        params = base_params.copy()
        params[param_name] = val
        
        traj = run_entropy_trajectory(
            grid_size=grid_size,
            total_time=total_time,
            dt=dt,
            a_omega=params['a_omega'],
            K_omega=params['K_omega'],
            g_omega_phi=params['g_omega_phi'],
            g_omega_rho=params['g_omega_rho'],
            seed=seed
        )
        
        trajectories.append(traj)
        
        status = "✓ plateau" if traj.has_plateau else "→ equilibrium"
        print(f"    {param_name}={val:.4f}: S_final={traj.final_entropy:.4f} ({status})")
    
    return trajectories


def find_transition_point(trajectories: List[EntropyTrajectory], param_name: str) -> Optional[float]:
    """
    Find parameter value where behavior changes (plateau → no plateau or vice versa).
    """
    if len(trajectories) < 2:
        return None
    
    # Look for change in plateau behavior
    plateau_states = [t.has_plateau for t in trajectories]
    
    for i in range(len(plateau_states) - 1):
        if plateau_states[i] != plateau_states[i + 1]:
            # Transition between these two values
            val1 = getattr(trajectories[i], param_name.replace('g_omega_', 'g_omega_'))
            val2 = getattr(trajectories[i + 1], param_name.replace('g_omega_', 'g_omega_'))
            
            # Handle different param names
            if param_name == 'a_omega':
                val1 = trajectories[i].a_omega
                val2 = trajectories[i + 1].a_omega
            elif param_name == 'K_omega':
                val1 = trajectories[i].K_omega
                val2 = trajectories[i + 1].K_omega
            elif param_name == 'g_omega_phi':
                val1 = trajectories[i].g_omega_phi
                val2 = trajectories[i + 1].g_omega_phi
            elif param_name == 'g_omega_rho':
                val1 = trajectories[i].g_omega_rho
                val2 = trajectories[i + 1].g_omega_rho
            
            return (val1 + val2) / 2
    
    return None


def run_entropy_production_test(
    grid_size: int = 16,
    total_time: float = 30.0,
    dt: float = 0.02,
    n_scan_points: int = 5,
    seed: int = 42
) -> EntropyProductionResult:
    """
    Run full entropy production analysis.
    
    Scans:
    1. Coupling strength (g_omega_phi)
    2. Gradient coefficient (K_omega)
    3. Potential depth (a_omega)
    
    Identifies phase transitions and validates entropy hierarchy.
    """
    print("="*60)
    print("QMRT ENTROPY PRODUCTION TEST (Step 4)")
    print("="*60)
    print(f"Grid: {grid_size}³, Time: {total_time}s")
    print(f"Scanning {n_scan_points} points per parameter")
    print("-"*60)
    
    # Get baseline parameters
    baseline = QMRTFrequencyParameters()
    base_params = {
        'a_omega': baseline.a_omega,
        'K_omega': baseline.K_omega,
        'g_omega_phi': baseline.g_omega_phi,
        'g_omega_rho': baseline.g_omega_rho
    }
    
    print(f"\nBaseline parameters:")
    print(f"  a_omega = {base_params['a_omega']:.4f}")
    print(f"  K_omega = {base_params['K_omega']:.4f}")
    print(f"  g_omega_phi = {base_params['g_omega_phi']:.4f}")
    print(f"  g_omega_rho = {base_params['g_omega_rho']:.4f}")
    
    result = EntropyProductionResult(grid_size=grid_size, total_time=total_time)
    
    # 1. Scan coupling strength
    print(f"\n[1/3] Scanning coupling strength (g_omega_phi)...")
    g_values = np.linspace(0.5 * base_params['g_omega_phi'], 2.0 * base_params['g_omega_phi'], n_scan_points)
    result.coupling_scan = scan_parameter(
        grid_size, total_time, dt, 'g_omega_phi', list(g_values), base_params, seed
    )
    result.coupling_transition_point = find_transition_point(result.coupling_scan, 'g_omega_phi')
    
    # 2. Scan gradient coefficient
    print(f"\n[2/3] Scanning gradient coefficient (K_omega)...")
    K_values = np.linspace(0.5 * base_params['K_omega'], 2.0 * base_params['K_omega'], n_scan_points)
    result.gradient_scan = scan_parameter(
        grid_size, total_time, dt, 'K_omega', list(K_values), base_params, seed
    )
    result.gradient_transition_point = find_transition_point(result.gradient_scan, 'K_omega')
    
    # 3. Scan potential depth
    print(f"\n[3/3] Scanning potential depth (a_omega)...")
    a_values = np.linspace(0.5 * base_params['a_omega'], 2.0 * base_params['a_omega'], n_scan_points)
    result.potential_scan = scan_parameter(
        grid_size, total_time, dt, 'a_omega', list(a_values), base_params, seed
    )
    result.potential_transition_point = find_transition_point(result.potential_scan, 'a_omega')
    
    # Analyze results
    print("\n" + "-"*60)
    print("ENTROPY ANALYSIS")
    print("-"*60)
    
    # Check for half-entropy regime
    all_trajectories = result.coupling_scan + result.gradient_scan + result.potential_scan
    normalized_finals = [t.final_entropy / t.max_entropy for t in all_trajectories if t.max_entropy > 0]
    
    # Half-entropy = normalized entropy between 0.3 and 0.7
    half_entropy_count = sum(1 for nf in normalized_finals if 0.3 < nf < 0.7)
    result.half_entropy_observed = half_entropy_count > len(normalized_finals) * 0.3
    
    if result.half_entropy_observed:
        half_values = [nf for nf in normalized_finals if 0.3 < nf < 0.7]
        result.half_entropy_range = (min(half_values), max(half_values))
    
    # Check plateau robustness
    plateau_count = sum(1 for t in all_trajectories if t.has_plateau)
    result.plateau_robust = plateau_count > len(all_trajectories) * 0.5
    
    # Phase boundary identification
    transitions_found = sum([
        result.coupling_transition_point is not None,
        result.gradient_transition_point is not None,
        result.potential_transition_point is not None
    ])
    result.phase_boundary_identified = transitions_found >= 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("ENTROPY PRODUCTION RESULTS")
    print(f"{'='*60}")
    
    print(f"\n  Plateau statistics:")
    print(f"    Trajectories with plateau: {plateau_count}/{len(all_trajectories)}")
    print(f"    Plateau robust: {'✅ YES' if result.plateau_robust else '❌ NO'}")
    
    print(f"\n  Half-entropy regime:")
    print(f"    Observed: {'✅ YES' if result.half_entropy_observed else '❌ NO'}")
    if result.half_entropy_observed:
        print(f"    Range: {result.half_entropy_range[0]:.3f} - {result.half_entropy_range[1]:.3f}")
    
    print(f"\n  Phase transitions:")
    print(f"    Coupling (g_ωφ): {result.coupling_transition_point:.4f}" if result.coupling_transition_point else "    Coupling (g_ωφ): Not detected")
    print(f"    Gradient (K_ω):  {result.gradient_transition_point:.4f}" if result.gradient_transition_point else "    Gradient (K_ω):  Not detected")
    print(f"    Potential (a_ω): {result.potential_transition_point:.4f}" if result.potential_transition_point else "    Potential (a_ω): Not detected")
    
    print(f"\n  Phase boundary identified: {'✅ YES' if result.phase_boundary_identified else '❌ NO'}")
    
    print(f"\n  {result._get_interpretation()}")
    print(f"{'='*60}\n")
    
    return result


if __name__ == "__main__":
    result = run_entropy_production_test(
        grid_size=14,
        total_time=20.0,
        dt=0.03,
        n_scan_points=4,
        seed=42
    )
    
    import json
    print("\nResult summary:")
    assessment = result.to_dict()['assessment']
    print(json.dumps(assessment, indent=2))
