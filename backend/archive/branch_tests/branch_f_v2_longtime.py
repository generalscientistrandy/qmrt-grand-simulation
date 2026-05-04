"""
Branch F v2: Long-Time Verification
====================================

Critical questions:
1. Does interior birth bias stay high over 10k+ steps?
2. Does late population plateau, oscillate, or decay?
3. Does localization persist or wash out?

This is the most important verification before claiming Branch F v2 is a stable result.
"""

import numpy as np
from branch_f_v2 import BranchFv2Simulator
from typing import Dict, List
import json


def run_long_time_test(steps: int = 12000, sample_interval: int = 100) -> Dict:
    """
    Run extended simulation with detailed tracking.
    """
    print(f"Running {steps} steps with sampling every {sample_interval}...")
    
    sim = BranchFv2Simulator(
        size=100, gamma=0.007,
        coupling_center=0.8, coupling_edge=0.2,
        transition_width=20.0
    )
    
    # Seed vortex pairs
    center = sim.size // 2
    np.random.seed(42)
    
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    vortex_positions = [
        (center - 5, center),
        (center + 5, center),
        (center, center - 8),
        (center, center + 8),
    ]
    
    for i, pos in enumerate(vortex_positions):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
        r_dist = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        vortex_amp = 1.2 * np.tanh(r_dist / 4.0)
        
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (vortex_amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size)
    
    # Tracking
    prev_positions = set()
    
    # Time series
    time_points = []
    population_series = []
    interior_pop_series = []
    periphery_pop_series = []
    
    # Cumulative by epoch (1000-step windows)
    epoch_births = {'interior': [], 'transition': [], 'periphery': []}
    current_epoch_births = {'interior': 0, 'transition': 0, 'periphery': 0}
    epoch_size = 1000
    
    for step in range(steps):
        sim.step()
        
        if step % sample_interval == 0:
            vortices = sim.detect_vortices()
            current_positions = set(v['position'] for v in vortices)
            
            # Count births by zone
            new_positions = current_positions - prev_positions
            for v in vortices:
                if v['position'] in new_positions:
                    zone = v['zone']
                    current_epoch_births[zone] += 1
            
            # Population by zone
            n_interior = sum(1 for v in vortices if v['zone'] == 'interior')
            n_periphery = sum(1 for v in vortices if v['zone'] == 'periphery')
            
            time_points.append(step)
            population_series.append(len(vortices))
            interior_pop_series.append(n_interior)
            periphery_pop_series.append(n_periphery)
            
            prev_positions = current_positions
        
        # Epoch checkpoint
        if (step + 1) % epoch_size == 0:
            epoch_births['interior'].append(current_epoch_births['interior'])
            epoch_births['transition'].append(current_epoch_births['transition'])
            epoch_births['periphery'].append(current_epoch_births['periphery'])
            current_epoch_births = {'interior': 0, 'transition': 0, 'periphery': 0}
            
            epoch_num = (step + 1) // epoch_size
            total_epoch = epoch_births['interior'][-1] + epoch_births['transition'][-1] + epoch_births['periphery'][-1]
            interior_pct = 100 * epoch_births['interior'][-1] / total_epoch if total_epoch > 0 else 0
            print(f"  Epoch {epoch_num}: {total_epoch} births, {interior_pct:.1f}% interior, pop={population_series[-1]}")
    
    return {
        'time_points': time_points,
        'population_series': population_series,
        'interior_pop_series': interior_pop_series,
        'periphery_pop_series': periphery_pop_series,
        'epoch_births': epoch_births,
        'steps': steps
    }


def analyze_results(results: Dict):
    """Analyze long-time behavior."""
    print()
    print("="*70)
    print("LONG-TIME ANALYSIS")
    print("="*70)
    print()
    
    pop = np.array(results['population_series'])
    interior_pop = np.array(results['interior_pop_series'])
    
    # Split into early, mid, late
    n = len(pop)
    early = pop[:n//3]
    mid = pop[n//3:2*n//3]
    late = pop[2*n//3:]
    
    print("Population by phase:")
    print(f"  Early (0-{results['steps']//3}):   mean={np.mean(early):.1f}, std={np.std(early):.1f}")
    print(f"  Mid ({results['steps']//3}-{2*results['steps']//3}):     mean={np.mean(mid):.1f}, std={np.std(mid):.1f}")
    print(f"  Late ({2*results['steps']//3}-{results['steps']}):  mean={np.mean(late):.1f}, std={np.std(late):.1f}")
    print()
    
    # Trend detection
    late_trend = np.polyfit(range(len(late)), late, 1)[0]
    if abs(late_trend) < 0.001:
        trend_label = "PLATEAU"
    elif late_trend > 0.001:
        trend_label = "INCREASING"
    else:
        trend_label = "DECREASING"
    
    print(f"Late-time trend: {trend_label} (slope={late_trend:.4f})")
    print()
    
    # Birth localization by epoch
    epoch_births = results['epoch_births']
    n_epochs = len(epoch_births['interior'])
    
    print("Birth localization by epoch:")
    print("Epoch | Interior | Trans | Periph | Interior%")
    print("-"*50)
    
    interior_ratios = []
    for i in range(n_epochs):
        total = epoch_births['interior'][i] + epoch_births['transition'][i] + epoch_births['periphery'][i]
        if total > 0:
            interior_pct = 100 * epoch_births['interior'][i] / total
            interior_ratios.append(interior_pct)
        else:
            interior_pct = 0
            interior_ratios.append(0)
        
        print(f"  {i+1:2d}  |  {epoch_births['interior'][i]:5d}  | {epoch_births['transition'][i]:5d} |  {epoch_births['periphery'][i]:5d}  |  {interior_pct:5.1f}%")
    
    print()
    
    # Localization persistence
    early_ratio = np.mean(interior_ratios[:n_epochs//3])
    late_ratio = np.mean(interior_ratios[2*n_epochs//3:])
    
    print(f"Localization persistence:")
    print(f"  Early epochs interior%: {early_ratio:.1f}%")
    print(f"  Late epochs interior%:  {late_ratio:.1f}%")
    
    if late_ratio >= early_ratio * 0.9:
        print("  ✓ LOCALIZATION PERSISTS")
        localization_stable = True
    else:
        print(f"  ✗ Localization degraded ({late_ratio/early_ratio:.2f}× of early)")
        localization_stable = False
    
    print()
    
    # Summary verdict
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()
    
    population_stable = np.mean(late) > 50 and np.std(late) / np.mean(late) < 0.5
    
    if population_stable and localization_stable:
        print("✓ BRANCH F v2 IS STABLE OVER LONG TIME")
        print(f"  - Population: {np.mean(late):.1f} ± {np.std(late):.1f}")
        print(f"  - Interior birth ratio: {late_ratio:.1f}%")
        print(f"  - Trend: {trend_label}")
    elif population_stable:
        print("~ Population stable, but localization degraded")
    elif localization_stable:
        print("~ Localization stable, but population declining")
    else:
        print("✗ BRANCH F v2 IS NOT STABLE")
    
    return {
        'early_mean': float(np.mean(early)),
        'late_mean': float(np.mean(late)),
        'late_std': float(np.std(late)),
        'trend': trend_label,
        'trend_slope': float(late_trend),
        'early_interior_ratio': float(early_ratio),
        'late_interior_ratio': float(late_ratio),
        'localization_stable': localization_stable,
        'population_stable': population_stable
    }


def main():
    print("="*70)
    print("BRANCH F v2: LONG-TIME VERIFICATION (12,000 steps)")
    print("="*70)
    print()
    
    results = run_long_time_test(steps=12000, sample_interval=50)
    analysis = analyze_results(results)
    
    # Save
    output = {
        'results': {
            'steps': results['steps'],
            'epoch_births': results['epoch_births'],
            'population_final_100': results['population_series'][-100:],
        },
        'analysis': {k: (bool(v) if isinstance(v, np.bool_) else v) for k, v in analysis.items()}
    }
    
    with open('/app/backend/qmrt_topology/test_results/phase5/branch_f_v2_longtime.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to branch_f_v2_longtime.json")


if __name__ == "__main__":
    main()
