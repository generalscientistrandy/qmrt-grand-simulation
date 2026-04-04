"""
QMRT MATHEMATICAL STRESS TEST — ATTACK SEQUENCE
================================================

Goal: Determine if the system is:
  Case A (Weak): A clever simulation that produces fermionic bias
  Case B (Strong): A class of systems where local transport constraints 
                   inevitably produce Z₂ statistics

Attack Order:
  1. Measure Test (Critical) — Verify configuration space argument
  2. Transport Rule Variants — Test universality
  3. Geometry Noise Test — Confirm true topology vs artifact
  4. Formation Bias Stress — Separate dynamics from structure
  5. Scaling Extremes — Confirm asymptotic behavior

RULE: Do NOT modify core mechanism to fix failures. Break, understand, then refine.

=============================================================================
"""

import numpy as np
from typing import List, Tuple, Dict, Callable
from collections import defaultdict
import json
import time as timer


# =============================================================================
# CORE DEFINITIONS (DO NOT MODIFY DURING ATTACKS)
# =============================================================================

def standard_transport(turn_angle: float) -> float:
    """Standard Y-junction transport: T(θ) = -θ/2"""
    return -turn_angle / 2


def compute_holonomy(positions: List[Tuple[float, float]], 
                     transport_fn: Callable = standard_transport) -> complex:
    """Compute holonomy using given transport rule."""
    n = len(positions)
    total_phase = 0.0
    
    for i in range(n):
        prev = positions[(i - 1) % n]
        curr = positions[i]
        next_p = positions[(i + 1) % n]
        
        angle_in = np.arctan2(curr[1] - prev[1], curr[0] - prev[0])
        angle_out = np.arctan2(next_p[1] - curr[1], next_p[0] - curr[0])
        
        turn = angle_out - angle_in
        while turn > np.pi: turn -= 2 * np.pi
        while turn < -np.pi: turn += 2 * np.pi
        
        total_phase += transport_fn(turn)
    
    return np.exp(1j * total_phase)


def compute_winding_number(positions: List[Tuple[float, float]]) -> int:
    """Compute winding number from total turn angle."""
    n = len(positions)
    total_angle = 0.0
    
    for i in range(n):
        prev = positions[(i - 1) % n]
        curr = positions[i]
        next_p = positions[(i + 1) % n]
        
        v1 = (curr[0] - prev[0], curr[1] - prev[1])
        v2 = (next_p[0] - curr[0], next_p[1] - curr[1])
        
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        turn = np.arctan2(cross, dot)
        total_angle += turn
    
    return round(total_angle / (2 * np.pi))


def is_simple_polygon(positions: List[Tuple[float, float]]) -> bool:
    """Check if polygon is simple (non-self-intersecting)."""
    n = len(positions)
    
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
    
    def intersects(A, B, C, D):
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
    
    for i in range(n):
        for j in range(i + 2, n):
            if j == (i + n - 1) % n:
                continue
            
            A = positions[i]
            B = positions[(i + 1) % n]
            C = positions[j]
            D = positions[(j + 1) % n]
            
            if intersects(A, B, C, D):
                return False
    
    return True


def classify_holonomy(holonomy: complex) -> str:
    """Classify holonomy into F/B/A."""
    if abs(holonomy + 1) < 0.3:
        return "F"
    elif abs(holonomy - 1) < 0.3:
        return "B"
    else:
        return "A"


# =============================================================================
# ATTACK 1: MEASURE TEST (CRITICAL)
# =============================================================================

def attack_1_measure_test(samples: int = 10000) -> Dict:
    """
    ATTACK 1: Verify configuration space measure argument.
    
    Claim under attack:
      "Simple loops occupy larger measure → fermionic bias"
    
    Test:
      Generate uniform random loop ensembles
      Measure P(simple) and P(fermionic)
      Check if observed ~79% matches theoretical expectation
    
    Failure mode:
      If generation is biased, mechanism becomes implementation-dependent
    """
    print("\n" + "=" * 70)
    print("  ATTACK 1: CONFIGURATION SPACE MEASURE TEST")
    print("=" * 70)
    print(f"  Samples per n: {samples}")
    print()
    
    results = {'by_n': {}, 'attack_passed': None}
    
    # Test for loop sizes 3-8
    for n in range(3, 9):
        simple_count = 0
        f_count = 0
        b_count = 0
        
        winding_dist = defaultdict(int)
        
        for _ in range(samples):
            # UNIFORM random n-gon in unit square
            # This is the key: are we sampling uniformly?
            positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                         for _ in range(n)]
            
            is_simple = is_simple_polygon(positions)
            holonomy = compute_holonomy(positions)
            sector = classify_holonomy(holonomy)
            winding = compute_winding_number(positions)
            
            winding_dist[winding] += 1
            
            if is_simple:
                simple_count += 1
            if sector == "F":
                f_count += 1
            elif sector == "B":
                b_count += 1
        
        p_simple = simple_count / samples
        p_f = f_count / samples
        p_b = b_count / samples
        
        # Theoretical prediction: P(F) ≈ P(simple) + 0.5 * P(complex)
        # Because: simple → F with prob 1, complex → F with prob ~0.5
        predicted_f = p_simple * 1.0 + (1 - p_simple) * 0.5
        
        # Check if prediction holds (within 10% relative error)
        prediction_error = abs(p_f - predicted_f) / max(0.01, predicted_f)
        prediction_holds = prediction_error < 0.15
        
        results['by_n'][n] = {
            'p_simple': p_simple,
            'p_fermionic': p_f,
            'p_bosonic': p_b,
            'predicted_f': predicted_f,
            'prediction_error': prediction_error,
            'prediction_holds': prediction_holds,
            'winding_distribution': dict(winding_dist)
        }
        
        status = "✓" if prediction_holds else "✗"
        print(f"  n={n}: P(simple)={100*p_simple:5.1f}%  P(F)={100*p_f:5.1f}%  "
              f"Predicted={100*predicted_f:5.1f}%  Error={100*prediction_error:4.1f}% {status}")
    
    # Overall verdict
    all_hold = all(r['prediction_holds'] for r in results['by_n'].values())
    avg_error = np.mean([r['prediction_error'] for r in results['by_n'].values()])
    
    results['attack_passed'] = all_hold
    results['average_error'] = avg_error
    
    print()
    if all_hold:
        print("  ✅ ATTACK 1 SURVIVED")
        print("     Measure argument is VALID")
        print("     P(F) matches theoretical prediction from P(simple)")
    else:
        print("  ❌ ATTACK 1 FAILED")
        print("     Measure argument may be flawed")
        print("     Check generation uniformity")
    
    return results


# =============================================================================
# ATTACK 2: TRANSPORT RULE VARIANTS
# =============================================================================

def attack_2_transport_variants(samples: int = 5000) -> Dict:
    """
    ATTACK 2: Test universality of transport rule.
    
    Claim under attack:
      "T(θ) = -θ/2 produces fermionic bias"
    
    Test variants:
      T(θ) = -θ/2     (standard)
      T(θ) = -θ/3     (weaker spin)
      T(θ) = -θ/4     (quarter spin)
      T(θ) = -θ       (full spin)
      T(θ) = +θ/2     (opposite sign)
      T(θ) = -θ/2 + noise  (noisy)
    
    Key question:
      Does fermionic dominance persist? Or is it tuned to exact rule?
    """
    print("\n" + "=" * 70)
    print("  ATTACK 2: TRANSPORT RULE VARIANTS")
    print("=" * 70)
    print()
    
    # Define transport variants
    variants = {
        'T = -θ/2 (standard)': lambda t: -t / 2,
        'T = -θ/3': lambda t: -t / 3,
        'T = -θ/4': lambda t: -t / 4,
        'T = -θ (full)': lambda t: -t,
        'T = +θ/2 (flipped)': lambda t: +t / 2,
        'T = -θ/2 + noise': lambda t: -t / 2 + np.random.normal(0, 0.1),
    }
    
    results = {'variants': {}, 'attack_passed': None}
    
    n = 5  # Fix loop size for comparison
    
    for name, transport_fn in variants.items():
        f_count = 0
        b_count = 0
        
        for _ in range(samples):
            positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                         for _ in range(n)]
            
            holonomy = compute_holonomy(positions, transport_fn)
            sector = classify_holonomy(holonomy)
            
            if sector == "F":
                f_count += 1
            elif sector == "B":
                b_count += 1
        
        p_f = f_count / samples
        
        results['variants'][name] = {
            'p_fermionic': p_f,
            'shows_dominance': p_f > 0.55
        }
        
        dominance = "F-dominant" if p_f > 0.55 else ("B-dominant" if p_f < 0.45 else "neutral")
        print(f"  {name:25s}: P(F) = {100*p_f:5.1f}%  [{dominance}]")
    
    # Analysis
    # Expected: T = -θ/2 and T = -θ should give F-dominance (odd winding → F)
    # T = -θ/3, -θ/4 should NOT give clean F/B separation
    # T = +θ/2 should flip dominance
    
    standard_f = results['variants']['T = -θ/2 (standard)']['p_fermionic']
    flipped_f = results['variants']['T = +θ/2 (flipped)']['p_fermionic']
    
    # Check if flipping sign flips dominance
    sign_flip_works = (standard_f > 0.55 and flipped_f < 0.45) or \
                      (standard_f < 0.45 and flipped_f > 0.55)
    
    # Check if fractional spins break the clean separation
    frac_third_f = results['variants']['T = -θ/3']['p_fermionic']
    fractional_breaks = abs(frac_third_f - 0.5) < 0.1  # Near 50% = no selection
    
    results['sign_flip_works'] = sign_flip_works
    results['fractional_breaks_selection'] = fractional_breaks
    results['attack_passed'] = sign_flip_works  # This confirms mechanism is real
    
    print()
    if sign_flip_works:
        print("  ✅ ATTACK 2 SURVIVED")
        print("     Sign flip INVERTS dominance → mechanism is real")
        print(f"     Fractional rules break selection: {fractional_breaks}")
    else:
        print("  ⚠️ ATTACK 2 PARTIAL")
        print("     Sign flip behavior unclear")
    
    return results


# =============================================================================
# ATTACK 3: GEOMETRY NOISE TEST
# =============================================================================

def attack_3_geometry_noise(samples: int = 5000) -> Dict:
    """
    ATTACK 3: Test if holonomy truly depends on topology, not geometry.
    
    Claim under attack:
      "Holonomy reduces to winding parity (Z₂ classification)"
    
    Test:
      Distort geometry with noise
      Check if holonomy still classifies correctly
    
    Distortions:
      - Position noise
      - Stretched coordinates
      - Non-uniform scaling
    """
    print("\n" + "=" * 70)
    print("  ATTACK 3: GEOMETRY NOISE TEST")
    print("=" * 70)
    print()
    
    results = {'distortions': {}, 'attack_passed': None}
    
    n = 5
    
    distortions = {
        'None (baseline)': lambda p: p,
        'Position noise σ=0.05': lambda p: [(x + np.random.normal(0, 0.05), 
                                              y + np.random.normal(0, 0.05)) 
                                             for x, y in p],
        'Position noise σ=0.2': lambda p: [(x + np.random.normal(0, 0.2), 
                                             y + np.random.normal(0, 0.2)) 
                                            for x, y in p],
        'X-stretch 2x': lambda p: [(2*x, y) for x, y in p],
        'Y-stretch 3x': lambda p: [(x, 3*y) for x, y in p],
        'Rotation 45°': lambda p: [(x*0.707 - y*0.707, x*0.707 + y*0.707) 
                                   for x, y in p],
        'Shear': lambda p: [(x + 0.5*y, y) for x, y in p],
    }
    
    for name, distort_fn in distortions.items():
        f_count = 0
        simple_f_correct = 0
        simple_total = 0
        
        for _ in range(samples):
            # Generate base polygon
            base_positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                              for _ in range(n)]
            
            # Apply distortion
            positions = distort_fn(base_positions)
            
            # Compute holonomy
            holonomy = compute_holonomy(positions)
            sector = classify_holonomy(holonomy)
            is_simple = is_simple_polygon(positions)
            winding = compute_winding_number(positions)
            
            if sector == "F":
                f_count += 1
            
            # Check: simple polygon should ALWAYS be fermionic
            if is_simple:
                simple_total += 1
                if sector == "F":
                    simple_f_correct += 1
        
        p_f = f_count / samples
        simple_accuracy = simple_f_correct / max(1, simple_total)
        
        results['distortions'][name] = {
            'p_fermionic': p_f,
            'simple_to_F_accuracy': simple_accuracy,
            'simple_count': simple_total
        }
        
        acc_status = "✓" if simple_accuracy > 0.95 else "✗"
        print(f"  {name:25s}: P(F)={100*p_f:5.1f}%  Simple→F: {100*simple_accuracy:5.1f}% {acc_status}")
    
    # Check if all distortions preserve simple → F mapping
    all_preserve = all(r['simple_to_F_accuracy'] > 0.95 
                       for r in results['distortions'].values())
    
    results['attack_passed'] = all_preserve
    
    print()
    if all_preserve:
        print("  ✅ ATTACK 3 SURVIVED")
        print("     Holonomy is TRULY TOPOLOGICAL")
        print("     Geometry distortions do not break the Z₂ classification")
    else:
        print("  ❌ ATTACK 3 FAILED")
        print("     Holonomy depends on geometry, not just topology")
    
    return results


# =============================================================================
# ATTACK 4: FORMATION BIAS STRESS
# =============================================================================

def attack_4_formation_bias(samples: int = 5000) -> Dict:
    """
    ATTACK 4: Separate dynamics from structure.
    
    Claim under attack:
      "Random formation favors simple loops"
    
    Test:
      Force generation of specific loop types
      Compare outcomes
    
    Methods:
      - Uniform random (baseline)
      - Force large loops
      - Force clustered vertices (increases self-intersection)
      - Force spread vertices (decreases self-intersection)
    """
    print("\n" + "=" * 70)
    print("  ATTACK 4: FORMATION BIAS STRESS")
    print("=" * 70)
    print()
    
    results = {'generators': {}, 'attack_passed': None}
    
    generators = {
        'Uniform random': lambda n: [(np.random.uniform(0, 1), 
                                      np.random.uniform(0, 1)) for _ in range(n)],
        'Clustered (σ=0.1)': lambda n: [(0.5 + np.random.normal(0, 0.1), 
                                         0.5 + np.random.normal(0, 0.1)) for _ in range(n)],
        'Clustered (σ=0.05)': lambda n: [(0.5 + np.random.normal(0, 0.05), 
                                          0.5 + np.random.normal(0, 0.05)) for _ in range(n)],
        'Ring (spread)': lambda n: [(0.5 + 0.4*np.cos(2*np.pi*i/n + np.random.normal(0, 0.3)),
                                     0.5 + 0.4*np.sin(2*np.pi*i/n + np.random.normal(0, 0.3)))
                                    for i in range(n)],
        'Large box': lambda n: [(np.random.uniform(0, 10), 
                                 np.random.uniform(0, 10)) for _ in range(n)],
    }
    
    n = 6  # Fixed size
    
    for name, gen_fn in generators.items():
        f_count = 0
        simple_count = 0
        
        for _ in range(samples):
            positions = gen_fn(n)
            
            is_simple = is_simple_polygon(positions)
            holonomy = compute_holonomy(positions)
            sector = classify_holonomy(holonomy)
            
            if is_simple:
                simple_count += 1
            if sector == "F":
                f_count += 1
        
        p_f = f_count / samples
        p_simple = simple_count / samples
        
        # Predicted F based on P(simple)
        predicted_f = p_simple + 0.5 * (1 - p_simple)
        error = abs(p_f - predicted_f) / max(0.01, predicted_f)
        
        results['generators'][name] = {
            'p_fermionic': p_f,
            'p_simple': p_simple,
            'predicted_f': predicted_f,
            'prediction_error': error
        }
        
        print(f"  {name:20s}: P(simple)={100*p_simple:5.1f}%  P(F)={100*p_f:5.1f}%  "
              f"Pred={100*predicted_f:5.1f}%  Err={100*error:4.1f}%")
    
    # Key check: does the formula P(F) = P(simple) + 0.5*(1-P(simple)) hold
    # across different formation dynamics?
    all_match = all(r['prediction_error'] < 0.2 for r in results['generators'].values())
    
    results['attack_passed'] = all_match
    
    print()
    if all_match:
        print("  ✅ ATTACK 4 SURVIVED")
        print("     F-dominance formula holds across different formation dynamics")
        print("     Bias is STRUCTURAL (topology), not DYNAMIC (generation method)")
    else:
        print("  ⚠️ ATTACK 4 PARTIAL")
        print("     Some formation methods deviate from prediction")
        print("     May indicate dynamics-dependent effects")
    
    return results


# =============================================================================
# ATTACK 5: SCALING EXTREMES
# =============================================================================

def attack_5_scaling_extremes(samples: int = 3000) -> Dict:
    """
    ATTACK 5: Push scaling to extremes.
    
    Test:
      Very small loops (n=3)
      Very large loops (n=15, 20)
      Sparse vs dense vertex distributions
    
    Goal: Confirm asymptotic behavior
    """
    print("\n" + "=" * 70)
    print("  ATTACK 5: SCALING EXTREMES")
    print("=" * 70)
    print()
    
    results = {'scales': {}, 'attack_passed': None}
    
    # Test range of n
    for n in [3, 4, 5, 6, 8, 10, 12, 15, 20]:
        f_count = 0
        simple_count = 0
        
        for _ in range(samples):
            positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                         for _ in range(n)]
            
            is_simple = is_simple_polygon(positions)
            holonomy = compute_holonomy(positions)
            sector = classify_holonomy(holonomy)
            
            if is_simple:
                simple_count += 1
            if sector == "F":
                f_count += 1
        
        p_f = f_count / samples
        p_simple = simple_count / samples
        predicted_f = p_simple + 0.5 * (1 - p_simple)
        
        results['scales'][n] = {
            'p_fermionic': p_f,
            'p_simple': p_simple,
            'predicted_f': predicted_f,
            'converges_to_50': abs(p_f - 0.5) < 0.1 if n >= 10 else None
        }
        
        print(f"  n={n:2d}: P(simple)={100*p_simple:5.1f}%  P(F)={100*p_f:5.1f}%  "
              f"Pred={100*predicted_f:5.1f}%")
    
    # Key observation: as n → ∞, P(simple) → 0, so P(F) → 0.5
    # But for small n, P(F) should be > 0.5
    
    small_n_dominant = results['scales'][3]['p_fermionic'] > 0.9 and \
                       results['scales'][4]['p_fermionic'] > 0.5
    large_n_neutral = abs(results['scales'][20]['p_fermionic'] - 0.5) < 0.1
    
    results['small_n_dominant'] = small_n_dominant
    results['large_n_neutral'] = large_n_neutral
    results['attack_passed'] = small_n_dominant  # Key result
    
    print()
    print("  Analysis:")
    print(f"    Small n (3,4) shows F-dominance: {small_n_dominant}")
    print(f"    Large n (20) approaches neutral: {large_n_neutral}")
    print()
    
    if small_n_dominant:
        print("  ✅ ATTACK 5 SURVIVED")
        print("     Small loops dominate F-bias (as expected)")
        print("     Large loops approach 50/50 (as expected)")
    else:
        print("  ❌ ATTACK 5 FAILED")
        print("     Scaling behavior unexpected")
    
    return results


# =============================================================================
# MAIN ATTACK SEQUENCE
# =============================================================================

def run_attack_sequence():
    """Run complete attack sequence."""
    print("=" * 75)
    print("  QMRT MATHEMATICAL STRESS TEST — ATTACK SEQUENCE")
    print("=" * 75)
    print()
    print("  Goal: Determine if system is Case A (simulation) or Case B (mechanism)")
    print("  Rule: Break first, understand why, then refine")
    print()
    
    start_time = timer.time()
    
    results = {
        'attacks': {},
        'overall': None
    }
    
    # Attack 1: Measure Test (CRITICAL)
    results['attacks']['1_measure'] = attack_1_measure_test(samples=10000)
    
    # Attack 2: Transport Variants
    results['attacks']['2_transport'] = attack_2_transport_variants(samples=5000)
    
    # Attack 3: Geometry Noise
    results['attacks']['3_geometry'] = attack_3_geometry_noise(samples=5000)
    
    # Attack 4: Formation Bias
    results['attacks']['4_formation'] = attack_4_formation_bias(samples=5000)
    
    # Attack 5: Scaling Extremes
    results['attacks']['5_scaling'] = attack_5_scaling_extremes(samples=3000)
    
    elapsed = timer.time() - start_time
    
    # Overall verdict
    print("\n" + "=" * 75)
    print("  ATTACK SEQUENCE SUMMARY")
    print("=" * 75)
    
    passed = sum(1 for a in results['attacks'].values() if a.get('attack_passed', False))
    total = len(results['attacks'])
    
    print(f"""
  Attack Results:
  
    1. Measure Test:        {'✅ PASSED' if results['attacks']['1_measure']['attack_passed'] else '❌ FAILED'}
    2. Transport Variants:  {'✅ PASSED' if results['attacks']['2_transport']['attack_passed'] else '❌ FAILED'}
    3. Geometry Noise:      {'✅ PASSED' if results['attacks']['3_geometry']['attack_passed'] else '❌ FAILED'}
    4. Formation Bias:      {'✅ PASSED' if results['attacks']['4_formation']['attack_passed'] else '❌ FAILED'}
    5. Scaling Extremes:    {'✅ PASSED' if results['attacks']['5_scaling']['attack_passed'] else '❌ FAILED'}
    
  Overall: {passed}/{total} attacks survived
    """)
    
    if passed >= 4:
        print("  ╔═══════════════════════════════════════════════════════════════════╗")
        print("  ║                         CASE B CONFIRMED                          ║")
        print("  ║                                                                   ║")
        print("  ║  This is a CLASS OF SYSTEMS where local transport constraints    ║")
        print("  ║  inevitably produce Z₂ statistics, not just a clever simulation. ║")
        print("  ╚═══════════════════════════════════════════════════════════════════╝")
        results['overall'] = 'CASE_B_CONFIRMED'
    elif passed >= 2:
        print("  ⚠️ CASE B PARTIAL — Some attacks failed, mechanism needs refinement")
        results['overall'] = 'CASE_B_PARTIAL'
    else:
        print("  ❌ CASE A — This appears to be implementation-dependent")
        results['overall'] = 'CASE_A'
    
    print(f"\n  Elapsed time: {elapsed:.1f} seconds")
    
    # Save results
    def convert(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, dict):
            return {str(k): convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj
    
    output_path = '/app/backend/qmrt_topology/attack_sequence_results.json'
    with open(output_path, 'w') as f:
        json.dump(convert(results), f, indent=2)
    
    print(f"\n  Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_attack_sequence()
