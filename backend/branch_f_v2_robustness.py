"""
Branch F v2: Robustness Test
=============================

Test whether Branch F v2 is a stable regime or a finely tuned point.

Vary:
1. Random seeds (different initial conditions)
2. Damping (γ)
3. Coupling amplitude (center/edge)
"""

import numpy as np
from branch_f_v2 import BranchFv2Simulator
from typing import Dict


def run_test(seed: int, gamma: float, coupling_center: float, coupling_edge: float, 
             steps: int = 4000) -> Dict:
    """Run a single robustness test."""
    sim = BranchFv2Simulator(
        size=100, gamma=gamma,
        coupling_center=coupling_center, coupling_edge=coupling_edge,
        transition_width=20.0
    )
    
    center = sim.size // 2
    np.random.seed(seed)
    
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    for i, pos in enumerate([(center-5, center), (center+5, center), (center, center-8), (center, center+8)]):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
        r = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        amp = 1.2 * np.tanh(r / 4.0)
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    sim.psi_r += 0.05 * np.random.randn(100, 100)
    sim.psi_i += 0.05 * np.random.randn(100, 100)
    
    prev_positions = set()
    population_history = []
    interior_births = 0
    total_births = 0
    
    for step in range(steps):
        sim.step()
        
        if step % 50 == 0:
            vortices = sim.detect_vortices()
            current_positions = set(v['position'] for v in vortices)
            
            new_positions = current_positions - prev_positions
            for v in vortices:
                if v['position'] in new_positions:
                    total_births += 1
                    if v['zone'] == 'interior':
                        interior_births += 1
            
            population_history.append(len(vortices))
            prev_positions = current_positions
    
    late_start = int(0.7 * len(population_history))
    late_pop = np.mean(population_history[late_start:])
    interior_ratio = interior_births / total_births if total_births > 0 else 0
    
    return {
        'late_population': late_pop,
        'total_births': total_births,
        'interior_ratio': interior_ratio
    }


def main():
    print("="*70)
    print("BRANCH F v2: ROBUSTNESS TEST")
    print("="*70)
    print()
    
    # Baseline
    baseline = run_test(seed=42, gamma=0.007, coupling_center=0.8, coupling_edge=0.2)
    print(f"Baseline (seed=42, γ=0.007, c=0.8/0.2):")
    print(f"  Late population: {baseline['late_population']:.1f}")
    print(f"  Total births: {baseline['total_births']}")
    print(f"  Interior ratio: {baseline['interior_ratio']*100:.1f}%")
    print()
    
    # 1. Seed variation
    print("--- SEED VARIATION ---")
    seed_results = []
    for seed in [1, 17, 42, 99, 256]:
        r = run_test(seed=seed, gamma=0.007, coupling_center=0.8, coupling_edge=0.2)
        seed_results.append(r['late_population'])
        print(f"  Seed {seed:3d}: late_pop={r['late_population']:6.1f}, births={r['total_births']:5d}, int%={r['interior_ratio']*100:.1f}%")
    
    print(f"  Mean: {np.mean(seed_results):.1f}, Std: {np.std(seed_results):.1f}, CV: {np.std(seed_results)/np.mean(seed_results):.2f}")
    print()
    
    # 2. Damping variation
    print("--- DAMPING VARIATION ---")
    damping_results = []
    for gamma in [0.004, 0.006, 0.007, 0.008, 0.010]:
        r = run_test(seed=42, gamma=gamma, coupling_center=0.8, coupling_edge=0.2)
        damping_results.append(r['late_population'])
        print(f"  γ={gamma:.3f}: late_pop={r['late_population']:6.1f}, births={r['total_births']:5d}, int%={r['interior_ratio']*100:.1f}%")
    
    print(f"  Mean: {np.mean(damping_results):.1f}, Std: {np.std(damping_results):.1f}, CV: {np.std(damping_results)/np.mean(damping_results):.2f}")
    print()
    
    # 3. Coupling amplitude variation
    print("--- COUPLING VARIATION ---")
    coupling_results = []
    coupling_configs = [
        (0.5, 0.3),  # Low contrast
        (0.6, 0.3),  # Medium
        (0.8, 0.2),  # Baseline
        (0.9, 0.1),  # High contrast
        (0.5, 0.5),  # Uniform (control)
    ]
    for cc, ce in coupling_configs:
        r = run_test(seed=42, gamma=0.007, coupling_center=cc, coupling_edge=ce)
        coupling_results.append(r['late_population'])
        label = "UNIFORM" if cc == ce else f"{cc}/{ce}"
        print(f"  {label:7s}: late_pop={r['late_population']:6.1f}, births={r['total_births']:5d}, int%={r['interior_ratio']*100:.1f}%")
    
    print()
    print("="*70)
    print("ROBUSTNESS VERDICT")
    print("="*70)
    print()
    
    # Check stability criteria
    seed_cv = np.std(seed_results) / np.mean(seed_results)
    damping_cv = np.std(damping_results) / np.mean(damping_results)
    
    if seed_cv < 0.3 and damping_cv < 0.5:
        print("✓ ROBUST: Branch F v2 is stable across seeds and moderate parameter changes")
    elif seed_cv < 0.3:
        print("~ Seed-stable but parameter-sensitive")
    else:
        print("✗ Branch F v2 is sensitive to initial conditions")
    
    print(f"  Seed CV: {seed_cv:.2f}")
    print(f"  Damping CV: {damping_cv:.2f}")


if __name__ == "__main__":
    main()
