"""
QMRT v3: Deep Stability Investigation
=====================================

The parameter scan showed:
1. Short-time stability across wide parameter range
2. But long-time dispersion (R grows to ~5x)
3. Perfect energy conservation

This suggests we need to investigate:
- Stronger shell coupling (Γ_rt)
- Different mass ratios
- The breathing dynamics in detail
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


def test_stronger_confinement():
    """Test with stronger shell coupling to prevent dispersion."""
    print("=" * 70)
    print("TEST: Stronger Confinement (Higher Γ_rt)")
    print("=" * 70)
    
    g_rt_values = [1.0, 2.0, 3.0, 5.0, 8.0]
    
    print(f"\n{'Γ_rt':>8} | {'R(t=50)':>10} | {'R_ratio':>10} | {'τ_max':>10} | {'E_drift':>10}")
    print("-" * 60)
    
    for g_rt in g_rt_values:
        params = QMRTv3Parameters(g_rt=g_rt, m_tau=2.0)
        engine = QMRTv3Engine(grid_size=24, params=params)
        engine.initialize_vacuum()
        engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
        
        initial_R = engine.measure_torsion_radius()
        
        # Run for 50 time units
        for _ in range(5000):
            engine.evolve_timestep(0.01)
        
        final = engine.get_state_summary()
        R_ratio = final['torsion_radius'] / initial_R
        
        print(f"{g_rt:8.1f} | {final['torsion_radius']:10.2f} | {R_ratio:10.2f} | "
              f"{final['torsion_max']:10.4f} | {final['energy_drift']:10.6%}")


def test_mass_hierarchy():
    """Test different mass hierarchies for better localization."""
    print("\n" + "=" * 70)
    print("TEST: Mass Hierarchy Effect")
    print("=" * 70)
    
    # Higher m_tau means torsion is more "stiff" and should localize better
    m_tau_values = [2.0, 4.0, 8.0, 16.0]
    
    print(f"\n{'m_τ':>8} | {'R(t=50)':>10} | {'R_ratio':>10} | {'τ_max':>10} | {'Note':>15}")
    print("-" * 65)
    
    for m_tau in m_tau_values:
        params = QMRTv3Parameters(m_tau=m_tau, g_rt=1.0)
        engine = QMRTv3Engine(grid_size=24, params=params)
        engine.initialize_vacuum()
        engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
        
        initial_R = engine.measure_torsion_radius()
        
        # Run for 50 time units
        for _ in range(5000):
            engine.evolve_timestep(0.01)
        
        final = engine.get_state_summary()
        R_ratio = final['torsion_radius'] / initial_R
        
        note = "localized" if R_ratio < 2 else "spreading"
        
        print(f"{m_tau:8.1f} | {final['torsion_radius']:10.2f} | {R_ratio:10.2f} | "
              f"{final['torsion_max']:10.4f} | {note:>15}")


def detailed_evolution_tracking():
    """Track detailed evolution to understand the dynamics."""
    print("\n" + "=" * 70)
    print("DETAILED EVOLUTION: Baseline vs Strong Confinement")
    print("=" * 70)
    
    configs = [
        ("Baseline", QMRTv3Parameters(g_rt=0.5, m_tau=2.0)),
        ("Strong shell", QMRTv3Parameters(g_rt=3.0, m_tau=2.0)),
        ("High mass", QMRTv3Parameters(g_rt=1.0, m_tau=8.0)),
        ("Combined", QMRTv3Parameters(g_rt=3.0, m_tau=8.0)),
    ]
    
    results = {}
    
    for name, params in configs:
        print(f"\n--- {name} ---")
        engine = QMRTv3Engine(grid_size=24, params=params)
        engine.initialize_vacuum()
        engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
        
        initial_R = engine.measure_torsion_radius()
        
        # Track at specific times
        times = [0, 10, 20, 30, 40, 50]
        R_values = [initial_R]
        tau_max_values = [1.0]
        
        print(f"{'t':>6} | {'R':>8} | {'R/R₀':>8} | {'τ_max':>8}")
        print("-" * 40)
        print(f"{0:6.0f} | {initial_R:8.2f} | {1.0:8.2f} | {1.0:8.4f}")
        
        current_step = 0
        for t in times[1:]:
            target_step = int(t / 0.01)
            while current_step < target_step:
                engine.evolve_timestep(0.01)
                current_step += 1
            
            R = engine.measure_torsion_radius()
            tau_max = engine.get_state_summary()['torsion_max']
            R_values.append(R)
            tau_max_values.append(tau_max)
            
            print(f"{t:6.0f} | {R:8.2f} | {R/initial_R:8.2f} | {tau_max:8.4f}")
        
        results[name] = {
            'R_values': R_values,
            'tau_max_values': tau_max_values,
            'final_R_ratio': R_values[-1] / initial_R,
        }
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Long-Time Localization")
    print("=" * 70)
    
    print(f"\n{'Config':>15} | {'Final R/R₀':>12} | {'Assessment':>20}")
    print("-" * 55)
    
    for name, data in results.items():
        ratio = data['final_R_ratio']
        if ratio < 1.5:
            assessment = "WELL LOCALIZED"
        elif ratio < 2.0:
            assessment = "STABLE"
        elif ratio < 3.0:
            assessment = "SLOW SPREAD"
        else:
            assessment = "DISPERSING"
        
        print(f"{name:>15} | {ratio:12.2f} | {assessment:>20}")


def test_optimal_configuration():
    """Test the best configuration from our search."""
    print("\n" + "=" * 70)
    print("TEST: Optimal Configuration")
    print("=" * 70)
    
    # Based on previous tests: stronger confinement + higher mass
    params = QMRTv3Parameters(
        m_tau=8.0,      # Higher mass for stiffer torsion
        g_rt=3.0,       # Stronger shell coupling
        g_tp=0.1,       # Same radiation threshold
        c_tau=0.5,      # Slower torsion waves
    )
    
    print(f"\nParameters: m_τ={params.m_tau}, Γ_rt={params.g_rt}, c_τ={params.c_tau}")
    
    engine = QMRTv3Engine(grid_size=32, params=params)
    engine.initialize_vacuum()
    engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
    
    initial_R = engine.measure_torsion_radius()
    initial_E = engine.initial_energy
    
    print(f"\nInitial: R={initial_R:.2f}, E={initial_E:.2f}")
    
    # Run for 100 time units
    print("\nEvolution:")
    print(f"{'t':>6} | {'R':>8} | {'R/R₀':>8} | {'τ_max':>8} | {'E_φ/E':>8}")
    print("-" * 50)
    
    for t in [0, 20, 40, 60, 80, 100]:
        if t > 0:
            for _ in range(2000):
                engine.evolve_timestep(0.01)
        
        state = engine.get_state_summary()
        R = state['torsion_radius']
        phi_frac = state['energies']['E_phi'] / initial_E
        
        print(f"{t:6.0f} | {R:8.2f} | {R/initial_R:8.2f} | {state['torsion_max']:8.4f} | {phi_frac:8.4%}")
    
    final_R_ratio = state['torsion_radius'] / initial_R
    
    if final_R_ratio < 2.0:
        print(f"\n✅ STABLE PARTICLE at t=100: R/R₀ = {final_R_ratio:.2f}")
    else:
        print(f"\n⚠️ Still spreading: R/R₀ = {final_R_ratio:.2f}")


def main():
    """Run deep stability investigation."""
    test_stronger_confinement()
    test_mass_hierarchy()
    detailed_evolution_tracking()
    test_optimal_configuration()


if __name__ == "__main__":
    main()
