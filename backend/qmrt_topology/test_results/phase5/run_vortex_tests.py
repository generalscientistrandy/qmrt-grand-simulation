#!/usr/bin/env python3
"""
Phase 5: Vortex Topology Tests
==============================

Three decisive probes to answer:
Can topology supply the interaction that β asymmetry alone cannot?

1. PINNING TEST - Do vortices preferentially form/persist in high-β regions?
2. MOBILITY TEST - Are vortices free or pinned by β-gradient?
3. INTERACTION TEST - Do two vortices attract/repel/merge?
"""

import sys
sys.path.insert(0, '/app/backend')

import numpy as np
import json
from datetime import datetime
from qmrt_simulation_api import BiasedMediumSimulator2D

# ============================================================
# TEST 1: PINNING TEST
# ============================================================

def run_pinning_test():
    """
    Test: Do vortices preferentially form/persist in high-β regions?
    
    Method:
    - Run with β-asymmetry (high-β region in center)
    - Run without β-asymmetry (uniform β)
    - Compare vortex density and lifetime inside vs outside
    """
    print("="*70)
    print("TEST 1: VORTEX PINNING")
    print("="*70)
    print()
    print("Question: Do vortices preferentially form/persist in high-β regions?")
    print()
    
    size = 80
    spot_radius = 15
    center = (size//2, size//2)
    steps = 20000
    sample_interval = 100
    
    # Create region mask
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    inside_mask = r <= spot_radius
    
    results = {}
    
    for condition in ['biased', 'uniform']:
        print(f"\n--- Running {condition} condition ---")
        
        sim = BiasedMediumSimulator2D(size=size, D_medium=0.05)
        
        if condition == 'biased':
            sim.set_biased_region(
                center=center,
                radius=spot_radius,
                beta_inside=0.8, beta_outside=0.3,
                gamma_inside=0.005, gamma_outside=0.02,
                lambda_inside=0.3, lambda_outside=0.6
            )
        else:
            # Uniform parameters
            sim.beta_field[:] = 0.5
            sim.gamma_field[:] = 0.01
            sim.lambda_field[:] = 0.5
        
        # Initial noise
        sim.add_uniform_noise(amplitude=0.5)
        
        # Track vortices
        vortex_counts_inside = []
        vortex_counts_outside = []
        vortex_lifetimes_inside = []
        vortex_lifetimes_outside = []
        
        # Simple tracking: track vortices by position
        active_vortices = {}  # {(i,j): birth_step}
        
        for step in range(steps):
            sim.step()
            
            if step % sample_interval == 0:
                vortices = sim.detect_torsion_vortices(vortex_threshold=0.02)
                
                # Count inside/outside
                n_inside = 0
                n_outside = 0
                
                current_positions = set()
                
                for v in vortices:
                    pos = tuple(v['position'])
                    current_positions.add(pos)
                    
                    i, j = pos
                    if 0 <= i < size and 0 <= j < size:
                        if inside_mask[i, j]:
                            n_inside += 1
                        else:
                            n_outside += 1
                    
                    # Track birth
                    if pos not in active_vortices:
                        active_vortices[pos] = step
                
                # Track deaths
                dead = []
                for pos, birth in active_vortices.items():
                    if pos not in current_positions:
                        lifetime = step - birth
                        i, j = pos
                        if 0 <= i < size and 0 <= j < size:
                            if inside_mask[i, j]:
                                vortex_lifetimes_inside.append(lifetime)
                            else:
                                vortex_lifetimes_outside.append(lifetime)
                        dead.append(pos)
                
                for pos in dead:
                    del active_vortices[pos]
                
                vortex_counts_inside.append(n_inside)
                vortex_counts_outside.append(n_outside)
        
        # Compute statistics
        area_inside = np.sum(inside_mask)
        area_outside = size*size - area_inside
        
        mean_count_inside = np.mean(vortex_counts_inside)
        mean_count_outside = np.mean(vortex_counts_outside)
        
        # Density = count / area
        density_inside = mean_count_inside / area_inside
        density_outside = mean_count_outside / area_outside
        density_ratio = density_inside / (density_outside + 1e-10)
        
        # Mean lifetimes
        mean_life_inside = np.mean(vortex_lifetimes_inside) if vortex_lifetimes_inside else 0
        mean_life_outside = np.mean(vortex_lifetimes_outside) if vortex_lifetimes_outside else 0
        life_ratio = mean_life_inside / (mean_life_outside + 1e-10)
        
        results[condition] = {
            'mean_count_inside': mean_count_inside,
            'mean_count_outside': mean_count_outside,
            'density_inside': density_inside,
            'density_outside': density_outside,
            'density_ratio': density_ratio,
            'mean_lifetime_inside': mean_life_inside,
            'mean_lifetime_outside': mean_life_outside,
            'lifetime_ratio': life_ratio,
            'n_lifetimes_inside': len(vortex_lifetimes_inside),
            'n_lifetimes_outside': len(vortex_lifetimes_outside),
        }
        
        print(f"  Density inside: {density_inside:.6f}")
        print(f"  Density outside: {density_outside:.6f}")
        print(f"  Density ratio (in/out): {density_ratio:.2f}")
        print(f"  Mean lifetime inside: {mean_life_inside:.1f} steps")
        print(f"  Mean lifetime outside: {mean_life_outside:.1f} steps")
        print(f"  Lifetime ratio: {life_ratio:.2f}")
    
    print()
    print("="*70)
    print("PINNING TEST RESULTS")
    print("="*70)
    print()
    
    biased = results['biased']
    uniform = results['uniform']
    
    print("| Condition | Density Ratio | Lifetime Ratio |")
    print("|-----------|---------------|----------------|")
    print(f"| Uniform   | {uniform['density_ratio']:.2f}          | {uniform['lifetime_ratio']:.2f}           |")
    print(f"| Biased    | {biased['density_ratio']:.2f}          | {biased['lifetime_ratio']:.2f}           |")
    print()
    
    # Success criteria
    pinning_success = (
        biased['density_ratio'] > 1.5 and 
        biased['density_ratio'] > uniform['density_ratio'] * 1.2
    )
    
    persistence_success = (
        biased['lifetime_ratio'] > 1.5 and
        biased['lifetime_ratio'] > uniform['lifetime_ratio'] * 1.2
    )
    
    if pinning_success:
        print("✓ PINNING: Vortices preferentially FORM in high-β regions")
    else:
        print("✗ PINNING: No preferential formation in high-β regions")
    
    if persistence_success:
        print("✓ PERSISTENCE: Vortices LIVE LONGER in high-β regions")
    else:
        print("✗ PERSISTENCE: No preferential persistence in high-β regions")
    
    return results


# ============================================================
# TEST 2: MOBILITY TEST
# ============================================================

def run_mobility_test():
    """
    Test: Are vortices free or pinned by β-gradient?
    
    Method:
    - Initialize a vortex near the boundary of a biased region
    - Track its trajectory
    - Compare drift with vs without β-gradient
    """
    print()
    print("="*70)
    print("TEST 2: VORTEX MOBILITY")
    print("="*70)
    print()
    print("Question: Are vortices free or pinned by β-gradient?")
    print()
    
    size = 80
    spot_radius = 15
    center = (size//2, size//2)
    steps = 15000
    sample_interval = 50
    
    results = {}
    
    for condition in ['with_gradient', 'no_gradient']:
        print(f"\n--- Running {condition} ---")
        
        sim = BiasedMediumSimulator2D(size=size, D_medium=0.05)
        
        if condition == 'with_gradient':
            # Create β-gradient: high on left, low on right
            for i in range(size):
                beta_val = 0.8 - 0.5 * (i / size)  # 0.8 at left, 0.3 at right
                sim.beta_field[i, :] = beta_val
            sim.gamma_field[:] = 0.01
            sim.lambda_field[:] = 0.5
        else:
            # Uniform
            sim.beta_field[:] = 0.5
            sim.gamma_field[:] = 0.01
            sim.lambda_field[:] = 0.5
        
        # Initialize vortex-like perturbation near center
        # Create a swirling pattern
        vortex_center = (size//2, size//2)
        x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
        r = np.sqrt((x - vortex_center[0])**2 + (y - vortex_center[1])**2)
        theta = np.arctan2(y - vortex_center[1], x - vortex_center[0])
        
        # Add angular momentum to create vortex
        vortex_amp = 1.0
        vortex_width = 5.0
        angular_pattern = vortex_amp * np.exp(-r**2 / (2*vortex_width**2)) * np.sin(theta)
        sim.phi_dot += angular_pattern
        
        # Track vortex position
        positions = []
        
        for step in range(steps):
            sim.step()
            
            if step % sample_interval == 0:
                vortices = sim.detect_torsion_vortices(vortex_threshold=0.01)
                
                if vortices:
                    # Find strongest vortex near center
                    best = max(vortices, key=lambda v: v['strength'])
                    positions.append({
                        'step': step,
                        'x': best['position'][0],
                        'y': best['position'][1],
                        'strength': best['strength'],
                        'chirality': best['chirality']
                    })
        
        # Analyze trajectory
        if len(positions) > 10:
            xs = [p['x'] for p in positions]
            ys = [p['y'] for p in positions]
            
            # Drift velocity
            if len(xs) > 1:
                dx = xs[-1] - xs[0]
                dy = ys[-1] - ys[0]
                dt = (positions[-1]['step'] - positions[0]['step']) * 0.04
                drift_speed = np.sqrt(dx**2 + dy**2) / (dt + 1e-10)
                drift_direction = np.arctan2(dy, dx) * 180 / np.pi
            else:
                drift_speed = 0
                drift_direction = 0
            
            # Displacement from initial
            displacement = np.sqrt((xs[-1] - xs[0])**2 + (ys[-1] - ys[0])**2)
            
            # Wandering (std of position)
            x_std = np.std(xs)
            y_std = np.std(ys)
            
            results[condition] = {
                'n_tracked': len(positions),
                'displacement': displacement,
                'drift_speed': drift_speed,
                'drift_direction': drift_direction,
                'x_std': x_std,
                'y_std': y_std,
                'trajectory': positions[:20]  # First 20 for brevity
            }
            
            print(f"  Tracked {len(positions)} positions")
            print(f"  Total displacement: {displacement:.1f} grid units")
            print(f"  Drift speed: {drift_speed:.3f} units/time")
            print(f"  Drift direction: {drift_direction:.1f}°")
            print(f"  Position std: x={x_std:.1f}, y={y_std:.1f}")
        else:
            print(f"  Insufficient tracking data ({len(positions)} points)")
            results[condition] = {'n_tracked': len(positions), 'error': 'insufficient_data'}
    
    print()
    print("="*70)
    print("MOBILITY TEST RESULTS")
    print("="*70)
    print()
    
    if 'displacement' in results.get('with_gradient', {}) and 'displacement' in results.get('no_gradient', {}):
        grad = results['with_gradient']
        no_grad = results['no_gradient']
        
        print("| Condition | Displacement | Drift Speed | Direction |")
        print("|-----------|--------------|-------------|-----------|")
        print(f"| No gradient | {no_grad['displacement']:.1f} | {no_grad['drift_speed']:.3f} | {no_grad['drift_direction']:.0f}° |")
        print(f"| With gradient | {grad['displacement']:.1f} | {grad['drift_speed']:.3f} | {grad['drift_direction']:.0f}° |")
        print()
        
        # Interpretation
        if grad['displacement'] < no_grad['displacement'] * 0.5:
            print("✓ PINNED: Vortex stays more localized with β-gradient")
        elif grad['drift_direction'] > 90 or grad['drift_direction'] < -90:
            print("→ DRIFTS TOWARD HIGH β: Vortex moves along gradient")
        else:
            print("✗ FREE: Vortex ignores β-gradient")
    
    return results


# ============================================================
# TEST 3: INTERACTION TEST
# ============================================================

def run_interaction_test():
    """
    Test: Do two vortices interact?
    
    Method:
    - Initialize two vortices with controlled separation
    - Track separation vs time
    - Check for merger/annihilation
    """
    print()
    print("="*70)
    print("TEST 3: VORTEX INTERACTION")
    print("="*70)
    print()
    print("Question: Do two vortices attract, repel, or ignore each other?")
    print()
    
    size = 100
    steps = 20000
    sample_interval = 50
    
    results = {}
    
    # Test different chirality combinations
    for chirality_config in ['same', 'opposite']:
        print(f"\n--- Testing {chirality_config} chirality ---")
        
        sim = BiasedMediumSimulator2D(size=size, D_medium=0.05)
        sim.beta_field[:] = 0.5
        sim.gamma_field[:] = 0.01
        sim.lambda_field[:] = 0.5
        
        # Initialize two vortices
        v1_center = (size//2 - 15, size//2)
        v2_center = (size//2 + 15, size//2)
        initial_separation = 30
        
        x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
        
        # Vortex 1 (positive chirality)
        r1 = np.sqrt((x - v1_center[0])**2 + (y - v1_center[1])**2)
        theta1 = np.arctan2(y - v1_center[1], x - v1_center[0])
        vortex1 = 1.0 * np.exp(-r1**2 / 50) * np.sin(theta1)
        
        # Vortex 2 (same or opposite chirality)
        r2 = np.sqrt((x - v2_center[0])**2 + (y - v2_center[1])**2)
        theta2 = np.arctan2(y - v2_center[1], x - v2_center[0])
        chirality_sign = 1 if chirality_config == 'same' else -1
        vortex2 = chirality_sign * 1.0 * np.exp(-r2**2 / 50) * np.sin(theta2)
        
        sim.phi_dot += vortex1 + vortex2
        
        # Track separation
        separations = []
        
        for step in range(steps):
            sim.step()
            
            if step % sample_interval == 0:
                vortices = sim.detect_torsion_vortices(vortex_threshold=0.01)
                
                if len(vortices) >= 2:
                    # Sort by x position to identify vortex 1 (left) and 2 (right)
                    vortices_sorted = sorted(vortices, key=lambda v: v['position'][0])
                    v1 = vortices_sorted[0]
                    v2 = vortices_sorted[-1]
                    
                    sep = np.sqrt(
                        (v1['position'][0] - v2['position'][0])**2 +
                        (v1['position'][1] - v2['position'][1])**2
                    )
                    
                    separations.append({
                        'step': step,
                        't': step * 0.04,
                        'separation': sep,
                        'v1_pos': v1['position'],
                        'v2_pos': v2['position'],
                        'v1_strength': v1['strength'],
                        'v2_strength': v2['strength']
                    })
                elif len(vortices) == 1:
                    # Possible merger
                    separations.append({
                        'step': step,
                        't': step * 0.04,
                        'separation': 0,
                        'merged': True
                    })
                elif len(vortices) == 0:
                    # Annihilation
                    separations.append({
                        'step': step,
                        't': step * 0.04,
                        'separation': None,
                        'annihilated': True
                    })
        
        # Analyze
        if separations:
            valid_seps = [s['separation'] for s in separations if s['separation'] is not None and s['separation'] > 0]
            
            if valid_seps:
                initial_sep = valid_seps[0]
                final_sep = valid_seps[-1] if valid_seps else 0
                
                # Check for merger/annihilation
                merged = any(s.get('merged', False) for s in separations)
                annihilated = any(s.get('annihilated', False) for s in separations)
                
                # Rate of change
                if len(valid_seps) > 10:
                    early_sep = np.mean(valid_seps[:10])
                    late_sep = np.mean(valid_seps[-10:])
                    sep_change = late_sep - early_sep
                    sep_rate = sep_change / ((separations[-1]['t'] - separations[0]['t']) + 1e-10)
                else:
                    sep_change = final_sep - initial_sep
                    sep_rate = 0
                
                results[chirality_config] = {
                    'initial_separation': initial_sep,
                    'final_separation': final_sep,
                    'separation_change': final_sep - initial_sep,
                    'separation_rate': sep_rate,
                    'merged': merged,
                    'annihilated': annihilated,
                    'n_tracked': len(valid_seps)
                }
                
                print(f"  Initial separation: {initial_sep:.1f}")
                print(f"  Final separation: {final_sep:.1f}")
                print(f"  Change: {final_sep - initial_sep:.1f}")
                print(f"  Merged: {merged}, Annihilated: {annihilated}")
            else:
                print("  No valid separation data")
                results[chirality_config] = {'error': 'no_valid_data'}
        else:
            print("  No tracking data")
            results[chirality_config] = {'error': 'no_data'}
    
    print()
    print("="*70)
    print("INTERACTION TEST RESULTS")
    print("="*70)
    print()
    
    if 'initial_separation' in results.get('same', {}) and 'initial_separation' in results.get('opposite', {}):
        same = results['same']
        opp = results['opposite']
        
        print("| Chirality | Initial | Final | Change | Merged? |")
        print("|-----------|---------|-------|--------|---------|")
        print(f"| Same | {same['initial_separation']:.1f} | {same['final_separation']:.1f} | {same['separation_change']:+.1f} | {same['merged']} |")
        print(f"| Opposite | {opp['initial_separation']:.1f} | {opp['final_separation']:.1f} | {opp['separation_change']:+.1f} | {opp['merged']} |")
        print()
        
        # Interpretation
        if same['separation_change'] > 5:
            print("Same chirality: REPEL (separation increases)")
        elif same['separation_change'] < -5:
            print("Same chirality: ATTRACT (separation decreases)")
        else:
            print("Same chirality: NEUTRAL (separation stable)")
        
        if opp['merged'] or opp['annihilated']:
            print("Opposite chirality: ANNIHILATE/MERGE")
        elif opp['separation_change'] < -5:
            print("Opposite chirality: ATTRACT")
        elif opp['separation_change'] > 5:
            print("Opposite chirality: REPEL")
        else:
            print("Opposite chirality: NEUTRAL")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*70)
    print("PHASE 5: VORTEX TOPOLOGY TESTS")
    print("="*70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    print("Central question: Can topology supply interaction that β asymmetry cannot?")
    print()
    
    # Run all three tests
    pinning_results = run_pinning_test()
    mobility_results = run_mobility_test()
    interaction_results = run_interaction_test()
    
    # Save results
    all_results = {
        'pinning': pinning_results,
        'mobility': mobility_results,
        'interaction': interaction_results
    }
    
    output_dir = "/app/backend/qmrt_topology/test_results/phase5"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/vortex_tests_results.json", 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print()
    print("="*70)
    print("OVERALL SUMMARY")
    print("="*70)
    print()
    
    # Final verdict
    pinning_works = (
        pinning_results.get('biased', {}).get('density_ratio', 0) > 1.5 and
        pinning_results.get('biased', {}).get('lifetime_ratio', 0) > 1.2
    )
    
    interaction_works = (
        interaction_results.get('opposite', {}).get('merged', False) or
        interaction_results.get('opposite', {}).get('annihilated', False) or
        abs(interaction_results.get('opposite', {}).get('separation_change', 0)) > 10
    )
    
    print(f"Pinning (localization via topology): {'YES' if pinning_works else 'NO'}")
    print(f"Interaction (vortex-vortex forces): {'YES' if interaction_works else 'NO/UNCLEAR'}")
    print()
    
    if pinning_works and interaction_works:
        print("✓ TOPOLOGY PROVIDES BOTH LOCALIZATION AND INTERACTION")
        print("  This is the missing ingredient from β-asymmetry alone!")
    elif interaction_works:
        print("✓ TOPOLOGY PROVIDES INTERACTION (but not pinning)")
        print("  Vortices interact but don't preferentially localize in high-β regions")
    elif pinning_works:
        print("✓ TOPOLOGY ENHANCES LOCALIZATION (but not interaction)")
        print("  Vortices pin to high-β regions but don't interact")
    else:
        print("✗ TOPOLOGY ALONE INSUFFICIENT")
        print("  Need nonlinear extensions for matter-like behavior")
    
    print()
    print(f"Results saved to {output_dir}/")
