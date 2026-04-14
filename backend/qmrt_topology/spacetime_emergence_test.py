#!/usr/bin/env python3
"""
QMRT Spacetime Emergence Test (Live PDE Simulations)
=====================================================

THE REAL TEST: Run actual dynamical medium simulations and measure
whether (O, R, P) couple with spatial score S across parameter space.

This integrates:
  - dynamical_medium.py (PDE solver)
  - temporal_web_v2.py (layered time metrics)
  - spacetime_coupling.py (cross-branch correlation)

GOAL:
  Measure Corr(O, S), Corr(R, S), Corr(P, S) from real simulations
  to determine if the QMRT system exhibits spacetime emergence.
"""

import numpy as np
import json
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

# Import existing components
from dynamical_medium import DynamicalMediumSimulator
from temporal_web_v2 import OrderingMetrics, RateMetrics, PersistenceMetrics
from spacetime_coupling import (
    compute_spacetime_coupling, 
    compute_full_spacetime_analysis,
    interpret_coupling
)


def measure_spatial_score(sim: DynamicalMediumSimulator, t_obs: int = 100) -> Dict:
    """
    Measure spatial branch metrics from simulation.
    
    S_space components:
    - Geodesic following (do waves bend toward low c_eff?)
    - Causal containment (is energy inside light cone?)
    - Lensing strength (how much do probes deflect?)
    """
    # Inject test pulse
    cx, cy = sim.size // 4, sim.size // 2
    x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size))
    sigma = 4.0
    pulse = 5.0 * np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * sigma**2))
    sim.phi += pulse
    
    initial_cx = cx
    initial_cy = cy
    
    # Run simulation
    for _ in range(t_obs):
        sim.step()
    
    # Measure final energy centroid
    phi_sq = sim.phi**2
    total = np.sum(phi_sq) + 1e-10
    final_cx = np.sum(x * phi_sq) / total
    final_cy = np.sum(y * phi_sq) / total
    
    # C_eff field
    c_eff = sim.compute_c_eff()
    
    # Light cone radius
    c_mean = np.mean(c_eff)
    light_cone_radius = c_mean * t_obs * sim.dt
    
    # Actual spread radius
    dx = final_cx - initial_cx
    dy = final_cy - initial_cy
    spread_radius = np.sqrt(dx**2 + dy**2)
    
    # Metrics
    # 1. Causal containment (is spread < light cone?)
    causal_containment = min(1.0, light_cone_radius / (spread_radius + 1e-10))
    
    # 2. C_eff gradient strength (measures spatial structure)
    grad_x = np.gradient(c_eff, axis=1)
    grad_y = np.gradient(c_eff, axis=0)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    gradient_strength = np.mean(grad_mag) / (c_mean + 1e-10)
    
    # 3. Tau variation (medium structure)
    tau_variation = np.std(sim.tau) / (np.mean(sim.tau) + 1e-10)
    
    # Combined spatial score
    S_space = 0.4 * min(1.0, causal_containment) + \
              0.3 * min(1.0, gradient_strength * 10) + \
              0.3 * min(1.0, tau_variation * 5)
    
    return {
        'S_space': float(S_space),
        'causal_containment': float(causal_containment),
        'gradient_strength': float(gradient_strength),
        'tau_variation': float(tau_variation),
        'c_eff_mean': float(c_mean),
    }


def measure_ordering_metrics(sim: DynamicalMediumSimulator, n_probes: int = 5) -> Tuple[float, np.ndarray]:
    """
    Measure ordering (O) layer from simulation.
    
    O measures: Do events happen in consistent causal order?
    - Inject multiple probes at different times
    - Check if arrival order respects injection order
    """
    # Reset simulation
    sim.phi *= 0
    sim.phi_dot *= 0
    
    # Define probe injection and detection points
    inject_x = sim.size // 4
    detect_x = 3 * sim.size // 4
    cy = sim.size // 2
    
    arrival_times = []
    
    for i in range(n_probes):
        # Inject probe
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size))
        sigma = 3.0
        pulse = 2.0 * np.exp(-((x - inject_x)**2 + (y - cy)**2) / (2 * sigma**2))
        sim.phi += pulse
        
        # Run until detection or timeout
        arrival_t = None
        for t in range(200):
            sim.step()
            # Check amplitude at detection point
            if sim.phi[cy, detect_x] > 0.1:
                arrival_t = t
                break
        
        if arrival_t is not None:
            arrival_times.append(arrival_t)
        else:
            arrival_times.append(200)  # Timeout
        
        # Small gap between probes
        for _ in range(10):
            sim.step()
    
    arrival_times = np.array(arrival_times)
    
    # Check if arrivals are monotonic (causality preserved)
    if len(arrival_times) >= 2:
        monotonic = np.all(np.diff(arrival_times) >= -5)  # Allow small tolerance
        O_score = 1.0 if monotonic else 0.5
    else:
        O_score = 0.5
    
    # Also check consistency
    if len(arrival_times) >= 3:
        cv = np.std(arrival_times) / (np.mean(arrival_times) + 1e-10)
        consistency = np.exp(-cv)
        O_score = 0.5 * O_score + 0.5 * consistency
    
    return float(O_score), arrival_times


def measure_rate_metrics(sim: DynamicalMediumSimulator, t_measure: int = 100) -> Tuple[float, np.ndarray]:
    """
    Measure rate (R) layer from simulation.
    
    R measures: How fast do oscillations occur in different regions?
    - Place oscillator probes in different regions
    - Compare cycle counts
    """
    # Reset
    sim.phi *= 0
    sim.phi_dot *= 0
    
    # Define measurement points
    regions = {
        'high_c': (sim.size // 4, sim.size // 2),
        'mid': (sim.size // 2, sim.size // 2),
        'low_c': (3 * sim.size // 4, sim.size // 2),
    }
    
    # Inject oscillatory perturbation
    x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size))
    for name, (rx, ry) in regions.items():
        pulse = np.exp(-((x - rx)**2 + (y - ry)**2) / 18)
        sim.phi += pulse
    
    # Track phi values at each region
    traces = {name: [] for name in regions}
    
    for t in range(t_measure):
        sim.step()
        for name, (rx, ry) in regions.items():
            traces[name].append(sim.phi[ry, rx])
    
    # Count zero crossings (cycles)
    cycle_counts = {}
    for name, trace in traces.items():
        trace = np.array(trace)
        zero_crossings = np.sum(np.diff(np.sign(trace)) != 0)
        cycle_counts[name] = zero_crossings / 2  # Each full cycle has 2 crossings
    
    # Rate score based on cycle count variation
    counts = np.array(list(cycle_counts.values()))
    
    if np.mean(counts) > 0:
        # Higher differentiation = better rate measurement
        cv = np.std(counts) / np.mean(counts)
        differentiation = min(1.0, cv * 2)  # Scale up
        # Also want regularity
        regularity = np.exp(-cv * 0.5)  # Not too variable
        R_score = 0.6 * differentiation + 0.4 * regularity
    else:
        R_score = 0.3
    
    return float(np.clip(R_score, 0, 1)), counts


def measure_persistence_metrics(sim: DynamicalMediumSimulator, n_decays: int = 3) -> Tuple[float, np.ndarray]:
    """
    Measure persistence (P) layer from simulation.
    
    P measures: How long do localized excitations persist?
    - Create metastable excitations
    - Measure decay times
    """
    lifetimes = []
    
    for _ in range(n_decays):
        # Reset
        sim.phi *= 0.1  # Don't fully reset to maintain medium state
        sim.phi_dot *= 0.1
        
        # Inject localized excitation
        cx = np.random.randint(sim.size // 4, 3 * sim.size // 4)
        cy = np.random.randint(sim.size // 4, 3 * sim.size // 4)
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size))
        
        excitation = 3.0 * np.exp(-((x - cx)**2 + (y - cy)**2) / 8)
        sim.phi += excitation
        
        initial_energy = np.sum(sim.phi**2)
        threshold = initial_energy * 0.37  # e-folding time
        
        # Measure decay time
        for t in range(300):
            sim.step()
            current_energy = np.sum(sim.phi**2)
            if current_energy < threshold:
                lifetimes.append(t)
                break
        else:
            lifetimes.append(300)  # Long-lived
    
    lifetimes = np.array(lifetimes)
    
    # Persistence score
    if len(lifetimes) >= 2:
        mean_life = np.mean(lifetimes)
        cv = np.std(lifetimes) / (mean_life + 1e-10)
        # High consistency = good persistence measurement
        consistency = np.exp(-cv)
        # Long lifetimes = strong persistence
        longevity = min(1.0, mean_life / 100)
        P_score = 0.5 * consistency + 0.5 * longevity
    else:
        P_score = 0.5
    
    return float(np.clip(P_score, 0, 1)), lifetimes


def run_parameter_point(
    alpha: float,
    lam: float,
    disorder: float,
    size: int = 80
) -> Dict:
    """
    Run simulation at a single parameter point and measure all metrics.
    """
    # Create simulator with parameters
    beta = alpha  # Map alpha to coupling strength
    lambda_relax = lam
    
    sim = DynamicalMediumSimulator(
        size=size,
        beta=beta,
        lambda_relax=lambda_relax,
        D_medium=0.1,
        gamma_wave=0.01,
    )
    
    # Add disorder to initial medium state
    if disorder > 0:
        noise = disorder * np.random.randn(size, size)
        sim.tau += noise * sim.tau_0 * 0.1
        sim.tau = np.clip(sim.tau, 0.3 * sim.tau_0, 1.5 * sim.tau_0)
    
    # Measure spatial
    spatial = measure_spatial_score(sim, t_obs=80)
    
    # Reset and measure ordering
    sim.phi *= 0
    sim.phi_dot *= 0
    O, arrivals = measure_ordering_metrics(sim, n_probes=4)
    
    # Reset and measure rate
    sim.phi *= 0
    sim.phi_dot *= 0
    R, cycles = measure_rate_metrics(sim, t_measure=80)
    
    # Reset and measure persistence
    sim.phi *= 0
    sim.phi_dot *= 0
    P, lifetimes = measure_persistence_metrics(sim, n_decays=3)
    
    # Compute temporal strength
    S_time = np.mean([O, R, P]) * (1 - np.std([O, R, P]))
    
    return {
        'params': {'alpha': alpha, 'lambda': lam, 'disorder': disorder},
        'spatial': spatial,
        'temporal': {
            'O': float(O),
            'R': float(R),
            'P': float(P),
            'S_time': float(S_time),
        },
        'raw': {
            'arrivals': arrivals.tolist() if isinstance(arrivals, np.ndarray) else list(arrivals),
            'cycles': cycles.tolist() if isinstance(cycles, np.ndarray) else list(cycles),
            'lifetimes': lifetimes.tolist() if isinstance(lifetimes, np.ndarray) else list(lifetimes),
        }
    }


def run_spacetime_sweep():
    """
    Run parameter sweep and analyze spacetime coupling.
    """
    print("=" * 70)
    print("SPACETIME EMERGENCE TEST (Live PDE Simulations)")
    print("=" * 70)
    print()
    
    # Parameter grid (reduced for speed)
    alphas = [0.3, 0.5, 0.7]
    lambdas = [0.5, 1.0, 1.5]
    disorders = [0.0, 0.3]
    
    total = len(alphas) * len(lambdas) * len(disorders)
    print(f"Running {total} simulations...")
    print()
    
    results = []
    count = 0
    
    for alpha in alphas:
        for lam in lambdas:
            for disorder in disorders:
                count += 1
                print(f"  [{count}/{total}] α={alpha}, λ={lam}, d={disorder}...", end=" ")
                
                result = run_parameter_point(alpha, lam, disorder, size=60)
                results.append(result)
                
                print(f"O={result['temporal']['O']:.2f}, R={result['temporal']['R']:.2f}, "
                      f"P={result['temporal']['P']:.2f}, S={result['spatial']['S_space']:.2f}")
    
    print()
    print("-" * 70)
    print("ANALYZING SPACETIME COUPLING")
    print("-" * 70)
    
    # Extract arrays
    O_arr = np.array([r['temporal']['O'] for r in results])
    R_arr = np.array([r['temporal']['R'] for r in results])
    P_arr = np.array([r['temporal']['P'] for r in results])
    S_arr = np.array([r['spatial']['S_space'] for r in results])
    
    # Compute coupling
    coupling = compute_spacetime_coupling(O_arr, R_arr, P_arr, S_arr)
    
    print(f"\nLayer-Space Correlations:")
    print(f"  ρ(O, S) = {coupling.rho_OS:.3f}  {'✓ Independent' if coupling.rho_OS < 0.6 else '→ Coupled'}")
    print(f"  ρ(R, S) = {coupling.rho_RS:.3f}  {'✓ Time dilation' if coupling.rho_RS > 0.7 else ''}")
    print(f"  ρ(P, S) = {coupling.rho_PS:.3f}")
    
    print(f"\nSpacetime Coupling:")
    print(f"  I_TS = {coupling.I_TS:.3f}")
    print(f"  Regime: {coupling.regime}")
    
    # Full analysis
    analysis = compute_full_spacetime_analysis(O_arr, R_arr, P_arr, S_arr)
    
    print(f"\nInterpretation:")
    print(f"  O: {analysis['interpretation']['ordering_behavior']}")
    print(f"  R: {analysis['interpretation']['rate_behavior']}")
    print(f"  P: {analysis['interpretation']['persistence_behavior']}")
    print(f"\n  → {analysis['interpretation']['overall']}")
    
    # Summary statistics
    print()
    print("-" * 70)
    print("SUMMARY STATISTICS")
    print("-" * 70)
    print(f"\nTemporal Layer Means:")
    print(f"  O (Ordering):    {np.mean(O_arr):.3f} ± {np.std(O_arr):.3f}")
    print(f"  R (Rate):        {np.mean(R_arr):.3f} ± {np.std(R_arr):.3f}")
    print(f"  P (Persistence): {np.mean(P_arr):.3f} ± {np.std(P_arr):.3f}")
    
    print(f"\nSpatial:")
    print(f"  S_space:         {np.mean(S_arr):.3f} ± {np.std(S_arr):.3f}")
    
    # Save results
    output = {
        'results': results,
        'coupling': coupling.as_dict(),
        'analysis': analysis,
        'summary': {
            'O_mean': float(np.mean(O_arr)),
            'R_mean': float(np.mean(R_arr)),
            'P_mean': float(np.mean(P_arr)),
            'S_mean': float(np.mean(S_arr)),
        }
    }
    
    with open('/app/backend/qmrt_topology/spacetime_emergence_test.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    
    if coupling.regime == 'spacetime_candidate':
        print("\n✅ SPACETIME REGIME ACHIEVED")
        print("   Temporal structure (O, R, P) couples with spatial branch S")
    elif coupling.regime in ['spacetime_partial', 'coupling_forming']:
        print("\n⚠️  APPROACHING SPACETIME")
        print("   Coupling forming but not yet complete")
    else:
        print("\n⚠️  TIME EXISTS BUT NOT SPACETIME")
        print("   Temporal structure exists independently of space")
    
    print("\nSaved: spacetime_emergence_test.json")
    
    return results, coupling, analysis


if __name__ == "__main__":
    run_spacetime_sweep()
