"""
Branch F Parameter Sweep
========================

The initial Branch F tests show:
- Test 1 (Regeneration Location): PASS - nucleation in low-β interior
- Test 2 (Migration): PASS - net drift toward higher β
- Test 3 (Population): FAIL - population too low, regeneration rate insufficient

This script sweeps parameters to find configurations that achieve sustained
population with localization.

Key parameters to explore:
1. β ratio (periphery/interior) - affects stabilization strength
2. Transition width - affects how smooth the gradient is
3. Interior radius - affects regeneration zone size
4. Resonance strength - affects regeneration rate
"""

import numpy as np
from branch_f_spatial_separation import BranchFSimulator
import json


def run_population_test(beta_interior: float, beta_periphery: float,
                        transition_width: float, interior_radius_frac: float,
                        resonance_mult: float = 1.0,
                        steps: int = 3000):
    """
    Run a quick population sustainability test with given parameters.
    Returns late-time population and birth count.
    """
    size = 100
    
    # Create simulator with modified parameters
    sim = BranchFSimulator(size=size, gamma=0.007,
                           beta_interior=beta_interior,
                           beta_periphery=beta_periphery,
                           transition_width=transition_width)
    
    # Override interior radius
    center = size / 2
    interior_radius = size * interior_radius_frac
    
    # Recreate β landscape with new interior radius
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - center)**2 + (y - center)**2)
    
    beta = np.zeros((size, size))
    for i in range(size):
        for j in range(size):
            dist = r[i, j]
            if dist <= interior_radius:
                beta[i, j] = beta_interior
            elif dist >= interior_radius + transition_width:
                beta[i, j] = beta_periphery
            else:
                t = (dist - interior_radius) / transition_width
                blend = 0.5 * (1 - np.cos(np.pi * t))
                beta[i, j] = beta_interior + blend * (beta_periphery - beta_interior)
    
    sim.beta = beta
    
    # Seed vortex pairs
    np.random.seed(42)
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    vortex_positions = [
        (size//2 - 5, size//2),
        (size//2 + 5, size//2),
        (size//2, size//2 - 8),
        (size//2, size//2 + 8),
    ]
    
    for i, pos in enumerate(vortex_positions):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
        r_dist = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        vortex_amp = 1.2 * np.tanh(r_dist / 4.0)
        
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (vortex_amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    sim.psi_r += 0.05 * np.random.randn(size, size)
    sim.psi_i += 0.05 * np.random.randn(size, size)
    sim.seed_oscillators(amp=0.25 * resonance_mult)
    
    prev_vortices = []
    population_history = []
    total_births = 0
    
    for step in range(steps):
        sim.step()
        
        if step % 30 == 0:
            vortices = sim.detect_vortices()
            births, deaths = sim.track_vortices(vortices, prev_vortices)
            prev_vortices = vortices
            total_births += births
            population_history.append(len(vortices))
    
    # Late-time stats
    late_start = int(0.7 * len(population_history))
    late_pop = np.mean(population_history[late_start:]) if population_history else 0
    
    return {
        'late_population': late_pop,
        'total_births': total_births,
        'max_population': max(population_history) if population_history else 0
    }


def main():
    print("="*70)
    print("BRANCH F PARAMETER SWEEP")
    print("="*70)
    print()
    print("Goal: Find parameters that achieve sustained population")
    print()
    
    results = []
    
    # Sweep parameters
    beta_ratios = [2.0, 3.0, 4.0]  # periphery/interior
    transition_widths = [10, 20, 30]
    interior_fracs = [0.2, 0.3, 0.4]
    
    best_result = None
    best_late_pop = 0
    
    for beta_ratio in beta_ratios:
        for tw in transition_widths:
            for int_frac in interior_fracs:
                beta_interior = 0.2
                beta_periphery = beta_interior * beta_ratio
                
                result = run_population_test(
                    beta_interior=beta_interior,
                    beta_periphery=beta_periphery,
                    transition_width=tw,
                    interior_radius_frac=int_frac
                )
                
                result['params'] = {
                    'beta_interior': beta_interior,
                    'beta_periphery': beta_periphery,
                    'beta_ratio': beta_ratio,
                    'transition_width': tw,
                    'interior_radius_frac': int_frac
                }
                
                results.append(result)
                
                status = "✓" if result['late_population'] > 0.5 else " "
                print(f"{status} β_ratio={beta_ratio:.1f}, tw={tw:2d}, int={int_frac:.1f} → "
                      f"late_pop={result['late_population']:.2f}, births={result['total_births']}")
                
                if result['late_population'] > best_late_pop:
                    best_late_pop = result['late_population']
                    best_result = result
    
    print()
    print("="*70)
    print("BEST CONFIGURATION")
    print("="*70)
    
    if best_result:
        print(f"Parameters: {best_result['params']}")
        print(f"Late population: {best_result['late_population']:.2f}")
        print(f"Total births: {best_result['total_births']}")
        print(f"Max population: {best_result['max_population']}")
    
    # Save results
    with open('/app/backend/qmrt_topology/test_results/phase5/branch_f_sweep.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("Results saved to branch_f_sweep.json")
    
    return results


if __name__ == "__main__":
    main()
