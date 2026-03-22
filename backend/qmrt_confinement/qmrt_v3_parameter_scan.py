"""
QMRT v3: Comprehensive Parameter Scan
=====================================

Following the systematic scan order from the parameter guide:
1. Fix baseline, scan Γ_rt to find shell window
2. Then scan m_τ/m_ρ for resonance
3. Then scan Γ_tp for decay threshold

This creates a phase map of the parameter space.
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


def run_single_test(params, grid_size=20, n_steps=500, verbose=False):
    """Run a single parameter configuration and return results."""
    engine = QMRTv3Engine(grid_size=grid_size, params=params)
    engine.initialize_vacuum()
    engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
    
    results = engine.run_simulation(dt=0.01, n_steps=n_steps, record_interval=25)
    
    if verbose:
        print(f"  R_ratio={results['R_ratio']:.2f}, φ_frac={results['radiation_fraction']:.2%}, "
              f"E_drift={results['energy_drift']:.2%}, stable={results['stable']}")
    
    return results


def scan_phase_1_shell_coupling():
    """Phase 1: Scan Γ_rt with fixed other parameters."""
    print("=" * 70)
    print("PHASE 1: Shell Coupling Scan (Γ_rt)")
    print("=" * 70)
    print("\nFixed: m_τ=2, c_τ=0.7, c_φ=2, λ_τ=1, Γ_tp=0.1, Γ_rp=0.02")
    
    g_rt_values = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0]
    
    print(f"\n{'Γ_rt':>8} | {'R_ratio':>8} | {'E_drift':>10} | {'φ_frac':>8} | {'τ_max_ratio':>12} | {'Class':>12}")
    print("-" * 75)
    
    results_map = []
    
    for g_rt in g_rt_values:
        params = QMRTv3Parameters(g_rt=g_rt)
        result = run_single_test(params)
        
        # Classification
        if result['R_ratio'] > 5 or result['max_torsion_ratio'] < 0.1:
            classification = "DISPERSED"
        elif result['max_torsion_ratio'] > 5:
            classification = "COLLAPSED"
        elif not result['stable']:
            classification = "UNSTABLE"
        else:
            classification = "STABLE"
        
        results_map.append({'g_rt': g_rt, 'result': result, 'class': classification})
        
        print(f"{g_rt:8.2f} | {result['R_ratio']:8.2f} | {result['energy_drift']:10.2%} | "
              f"{result['radiation_fraction']:8.2%} | {result['max_torsion_ratio']:12.2f} | {classification:>12}")
    
    return results_map


def scan_phase_2_mass_ratio():
    """Phase 2: Scan m_τ/m_ρ with good Γ_rt."""
    print("\n" + "=" * 70)
    print("PHASE 2: Mass Ratio Scan (m_τ/m_ρ)")
    print("=" * 70)
    print("\nFixed: Γ_rt=0.5, c_τ=0.7, c_φ=2, λ_τ=1, Γ_tp=0.1, Γ_rp=0.02")
    
    m_tau_ratios = [0.5, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    
    print(f"\n{'m_τ/m_ρ':>8} | {'R_ratio':>8} | {'E_drift':>10} | {'φ_frac':>8} | {'τ_max_ratio':>12} | {'Class':>12}")
    print("-" * 75)
    
    results_map = []
    
    for m_ratio in m_tau_ratios:
        params = QMRTv3Parameters(m_tau=m_ratio, g_rt=0.5)
        result = run_single_test(params)
        
        # Classification
        if result['R_ratio'] > 5:
            classification = "DISPERSED"
        elif result['max_torsion_ratio'] > 5:
            classification = "COLLAPSED"
        elif not result['stable']:
            classification = "UNSTABLE"
        else:
            classification = "STABLE"
        
        results_map.append({'m_ratio': m_ratio, 'result': result, 'class': classification})
        
        print(f"{m_ratio:8.2f} | {result['R_ratio']:8.2f} | {result['energy_drift']:10.2%} | "
              f"{result['radiation_fraction']:8.2%} | {result['max_torsion_ratio']:12.2f} | {classification:>12}")
    
    return results_map


def scan_phase_3_radiation_threshold():
    """Phase 3: Scan Γ_tp to find decay threshold."""
    print("\n" + "=" * 70)
    print("PHASE 3: Radiation Threshold Scan (Γ_tp)")
    print("=" * 70)
    print("\nFixed: m_τ=2, Γ_rt=0.5, c_τ=0.7, c_φ=2, λ_τ=1, Γ_rp=0.02")
    
    g_tp_values = [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
    
    print(f"\n{'Γ_tp':>8} | {'R_ratio':>8} | {'E_drift':>10} | {'φ_frac':>8} | {'τ_max_ratio':>12} | {'Class':>12}")
    print("-" * 75)
    
    results_map = []
    
    for g_tp in g_tp_values:
        params = QMRTv3Parameters(g_tp=g_tp, g_rt=0.5)
        result = run_single_test(params)
        
        # Classification focused on radiation
        if result['radiation_fraction'] > 0.3:
            classification = "RADIATIVE"
        elif result['R_ratio'] > 5:
            classification = "DISPERSED"
        elif not result['stable']:
            classification = "UNSTABLE"
        else:
            classification = "STABLE"
        
        results_map.append({'g_tp': g_tp, 'result': result, 'class': classification})
        
        print(f"{g_tp:8.3f} | {result['R_ratio']:8.2f} | {result['energy_drift']:10.2%} | "
              f"{result['radiation_fraction']:8.2%} | {result['max_torsion_ratio']:12.2f} | {classification:>12}")
    
    return results_map


def scan_2d_phase_diagram():
    """Create a 2D phase diagram: Γ_rt vs m_τ/m_ρ."""
    print("\n" + "=" * 70)
    print("2D PHASE DIAGRAM: Γ_rt vs m_τ/m_ρ")
    print("=" * 70)
    
    g_rt_values = [0.2, 0.5, 0.8, 1.2]
    m_ratios = [1.0, 1.5, 2.0, 3.0, 4.0]
    
    # Header
    print(f"\n{'':>10}", end="")
    for m_ratio in m_ratios:
        print(f"{'m_τ=' + str(m_ratio):>12}", end="")
    print()
    print("-" * (10 + 12 * len(m_ratios)))
    
    for g_rt in g_rt_values:
        print(f"{'Γ_rt=' + str(g_rt):>10}", end="")
        for m_ratio in m_ratios:
            params = QMRTv3Parameters(g_rt=g_rt, m_tau=m_ratio)
            result = run_single_test(params, n_steps=300)
            
            # Compact classification
            if result['R_ratio'] > 3:
                symbol = "DISP"
            elif result['max_torsion_ratio'] > 3:
                symbol = "COLL"
            elif result['radiation_fraction'] > 0.2:
                symbol = "RAD"
            elif result['stable']:
                symbol = "✓STAB"
            else:
                symbol = "UNST"
            
            print(f"{symbol:>12}", end="")
        print()
    
    print("\nLegend: STAB=stable, DISP=dispersed, COLL=collapsed, RAD=radiative, UNST=unstable")


def long_time_stability_test():
    """Test stability over longer time."""
    print("\n" + "=" * 70)
    print("LONG-TIME STABILITY TEST")
    print("=" * 70)
    
    params = QMRTv3Parameters(g_rt=0.5, m_tau=2.0, g_tp=0.1)
    
    print("\nRunning baseline for 5000 steps (50 time units)...")
    
    engine = QMRTv3Engine(grid_size=24, params=params)
    engine.initialize_vacuum()
    engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
    
    # Record at intervals
    checkpoints = [0, 500, 1000, 2000, 3000, 5000]
    
    print(f"\n{'Step':>8} | {'Time':>8} | {'R':>8} | {'τ_max':>8} | {'E_drift':>10} | {'φ_frac':>8}")
    print("-" * 65)
    
    for i, step in enumerate(checkpoints):
        if i > 0:
            n_evolve = checkpoints[i] - checkpoints[i-1]
            for _ in range(n_evolve):
                engine.evolve_timestep(0.01)
        
        state = engine.get_state_summary()
        print(f"{step:8d} | {state['time']:8.2f} | {state['torsion_radius']:8.2f} | "
              f"{state['torsion_max']:8.4f} | {state['energy_drift']:10.2%} | "
              f"{state['energies']['E_phi']/max(engine.initial_energy, 1e-10):8.2%}")
    
    # Final stability check
    final = engine.get_state_summary()
    initial_R = 2.45  # From initialization
    
    print(f"\n--- Long-time assessment ---")
    print(f"Radius growth: {final['torsion_radius']/initial_R:.2f}x")
    print(f"Energy drift: {final['energy_drift']:.6%}")
    print(f"Radiation fraction: {final['energies']['E_phi']/max(engine.initial_energy, 1e-10):.4%}")
    
    if final['torsion_radius']/initial_R < 2 and abs(final['energy_drift']) < 0.01:
        print("\n✅ LONG-TIME STABILITY CONFIRMED")
    else:
        print("\n⚠️ Some degradation observed")


def main():
    """Run all parameter scans."""
    print("#" * 70)
    print("# QMRT v3: COMPREHENSIVE PARAMETER SCAN")
    print("#" * 70)
    
    # Phase 1: Shell coupling
    phase1_results = scan_phase_1_shell_coupling()
    
    # Phase 2: Mass ratio
    phase2_results = scan_phase_2_mass_ratio()
    
    # Phase 3: Radiation threshold
    phase3_results = scan_phase_3_radiation_threshold()
    
    # 2D Phase diagram
    scan_2d_phase_diagram()
    
    # Long-time test
    long_time_stability_test()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Find stable windows
    stable_g_rt = [r['g_rt'] for r in phase1_results if r['class'] == 'STABLE']
    stable_m_ratio = [r['m_ratio'] for r in phase2_results if r['class'] == 'STABLE']
    stable_g_tp = [r['g_tp'] for r in phase3_results if r['class'] == 'STABLE']
    
    print(f"\nStable Γ_rt window: {min(stable_g_rt):.2f} - {max(stable_g_rt):.2f}" if stable_g_rt else "No stable Γ_rt found")
    print(f"Stable m_τ/m_ρ window: {min(stable_m_ratio):.2f} - {max(stable_m_ratio):.2f}" if stable_m_ratio else "No stable m_ratio found")
    print(f"Stable Γ_tp window: {min(stable_g_tp):.3f} - {max(stable_g_tp):.3f}" if stable_g_tp else "No stable Γ_tp found")


if __name__ == "__main__":
    main()
