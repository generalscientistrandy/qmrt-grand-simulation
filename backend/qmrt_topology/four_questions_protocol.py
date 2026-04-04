"""
QMRT SELF-CRITIQUE PROTOCOL — FOUR STANDARD QUESTIONS
======================================================

For every claim, we must answer:
  1. What assumption is hidden here?
  2. What parameter is doing the work?
  3. What happens if I distort the system?
  4. What would make this completely fail?

Then convert each into a simulation and RUN BEFORE refining theory.

=============================================================================
CLAIM UNDER SCRUTINY: The Double Selection Mechanism
=============================================================================

CLAIM:
"Loop configurations partition into topological sectors classified by winding
parity. Simple loops are strictly odd-winding and thus fermionic, while 
self-intersecting loops exhibit a strong bias toward even winding."

=============================================================================
"""

import numpy as np
from typing import List, Tuple, Dict
from collections import defaultdict
import json


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def compute_holonomy(positions: List[Tuple[float, float]], 
                     transport_coeff: float = -0.5) -> complex:
    """Compute holonomy with configurable transport coefficient."""
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
        
        total_phase += transport_coeff * turn
    
    return np.exp(1j * total_phase)


def compute_winding(positions: List[Tuple[float, float]]) -> int:
    """Compute winding number."""
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


def is_simple(positions: List[Tuple[float, float]]) -> bool:
    """Check if polygon is simple."""
    n = len(positions)
    
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
    
    def intersects(A, B, C, D):
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
    
    for i in range(n):
        for j in range(i + 2, n):
            if j == (i + n - 1) % n:
                continue
            if intersects(positions[i], positions[(i+1)%n], 
                         positions[j], positions[(j+1)%n]):
                return False
    return True


def classify(holonomy: complex) -> str:
    """Classify holonomy."""
    if abs(holonomy + 1) < 0.3:
        return "F"
    elif abs(holonomy - 1) < 0.3:
        return "B"
    return "A"


# =============================================================================
# QUESTION 1: WHAT ASSUMPTION IS HIDDEN?
# =============================================================================

def question_1_hidden_assumptions(samples: int = 5000) -> Dict:
    """
    QUESTION 1: What assumption is hidden here?
    
    Hidden assumptions in the current theory:
    
    A. Vertices are uniformly distributed
       → What if vertices are clustered or structured?
       
    B. Polygons are closed (return to start)
       → What if we allow open paths?
       
    C. The transport rule T(θ) = -θ/2 is exact
       → What if there's measurement noise?
       
    D. Winding number is well-defined
       → What if polygon is degenerate (collinear points)?
    """
    print("\n" + "=" * 70)
    print("  QUESTION 1: HIDDEN ASSUMPTIONS")
    print("=" * 70)
    
    results = {}
    n = 5
    
    # Test A: Non-uniform vertex distribution
    print("\n  A. Testing non-uniform vertex distributions...")
    
    distributions = {
        'uniform': lambda: (np.random.uniform(0, 1), np.random.uniform(0, 1)),
        'gaussian': lambda: (np.random.normal(0.5, 0.2), np.random.normal(0.5, 0.2)),
        'clustered': lambda: (0.5 + np.random.normal(0, 0.05), 
                              0.5 + np.random.normal(0, 0.05)),
        'edge_biased': lambda: (np.random.beta(0.5, 0.5), np.random.beta(0.5, 0.5)),
    }
    
    for name, gen in distributions.items():
        f_count = 0
        simple_count = 0
        
        for _ in range(samples):
            positions = [gen() for _ in range(n)]
            
            if is_simple(positions):
                simple_count += 1
            
            holonomy = compute_holonomy(positions)
            if classify(holonomy) == "F":
                f_count += 1
        
        p_f = f_count / samples
        p_simple = simple_count / samples
        
        results[f'dist_{name}'] = {'p_f': p_f, 'p_simple': p_simple}
        print(f"     {name:15s}: P(F)={100*p_f:5.1f}%, P(simple)={100*p_simple:5.1f}%")
    
    # Test B: Degenerate polygons (collinear points)
    print("\n  B. Testing degenerate polygons (near-collinear)...")
    
    degenerate_count = 0
    degenerate_winding_defined = 0
    
    for _ in range(samples):
        # Generate nearly collinear points
        t_values = np.sort(np.random.uniform(0, 1, n))
        noise = 0.001
        positions = [(t + np.random.normal(0, noise), 
                      t + np.random.normal(0, noise)) for t in t_values]
        
        winding = compute_winding(positions)
        degenerate_count += 1
        if abs(winding) <= 2:  # Reasonable winding
            degenerate_winding_defined += 1
    
    results['degenerate_winding_stable'] = degenerate_winding_defined / degenerate_count
    print(f"     Winding stable for degenerate: {100*results['degenerate_winding_stable']:.1f}%")
    
    # Check: does the theory hold across distributions?
    f_values = [v['p_f'] for k, v in results.items() if k.startswith('dist_')]
    spread = max(f_values) - min(f_values)
    
    results['distribution_robust'] = spread < 0.15
    print(f"\n  Spread across distributions: {100*spread:.1f}%")
    print(f"  {'✅ ROBUST' if results['distribution_robust'] else '⚠️ DISTRIBUTION-SENSITIVE'}")
    
    return results


# =============================================================================
# QUESTION 2: WHAT PARAMETER IS DOING THE WORK?
# =============================================================================

def question_2_parameter_sensitivity(samples: int = 5000) -> Dict:
    """
    QUESTION 2: What parameter is doing the work?
    
    Parameters in the theory:
    
    A. Transport coefficient α in T(θ) = α·θ
       → Standard: α = -1/2
       → What if α varies?
       
    B. Classification threshold (0.3 for |H ± 1|)
       → What if we change the threshold?
       
    C. Loop size n
       → Already tested, but check sensitivity
    """
    print("\n" + "=" * 70)
    print("  QUESTION 2: PARAMETER SENSITIVITY")
    print("=" * 70)
    
    results = {}
    n = 5
    
    # Test A: Transport coefficient sweep
    print("\n  A. Transport coefficient α sweep...")
    
    coefficients = [-1.0, -0.75, -0.5, -0.25, -0.1, 0.0, 0.1, 0.5]
    
    for alpha in coefficients:
        f_count = 0
        b_count = 0
        anyonic_count = 0
        
        for _ in range(samples):
            positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                         for _ in range(n)]
            
            holonomy = compute_holonomy(positions, transport_coeff=alpha)
            sector = classify(holonomy)
            
            if sector == "F":
                f_count += 1
            elif sector == "B":
                b_count += 1
            else:
                anyonic_count += 1
        
        p_f = f_count / samples
        p_a = anyonic_count / samples
        
        results[f'alpha_{alpha}'] = {'p_f': p_f, 'p_anyonic': p_a}
        
        status = "F-dom" if p_f > 0.55 else ("B-dom" if p_f < 0.45 else "neutral")
        print(f"     α={alpha:+5.2f}: P(F)={100*p_f:5.1f}%, P(A)={100*p_a:5.1f}% [{status}]")
    
    # Test B: Classification threshold
    print("\n  B. Classification threshold sweep...")
    
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    for thresh in thresholds:
        f_count = 0
        
        for _ in range(samples):
            positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                         for _ in range(n)]
            
            holonomy = compute_holonomy(positions)
            
            if abs(holonomy + 1) < thresh:
                f_count += 1
        
        p_f = f_count / samples
        results[f'thresh_{thresh}'] = p_f
        print(f"     threshold={thresh}: P(F)={100*p_f:5.1f}%")
    
    # Critical check: is α = -0.5 special?
    alpha_half = results['alpha_-0.5']['p_f']
    alpha_others = [v['p_f'] for k, v in results.items() 
                    if k.startswith('alpha_') and k != 'alpha_-0.5']
    
    results['alpha_half_special'] = abs(alpha_half - 0.5) > 0.05 and \
                                     all(abs(a - 0.5) < 0.1 for a in alpha_others 
                                         if abs(float(k.split('_')[1])) != 0.5 
                                         for k, v in results.items() 
                                         if k.startswith('alpha_'))
    
    print(f"\n  Is α = -0.5 special? Analysis needed manually")
    
    return results


# =============================================================================
# QUESTION 3: WHAT HAPPENS IF I DISTORT THE SYSTEM?
# =============================================================================

def question_3_distortion_tests(samples: int = 5000) -> Dict:
    """
    QUESTION 3: What happens if I distort the system?
    
    Distortions to test:
    
    A. Add noise to vertex positions
    B. Discretize angles (lattice-like)
    C. Add measurement noise to holonomy
    D. Use integer coordinates only
    """
    print("\n" + "=" * 70)
    print("  QUESTION 3: DISTORTION TESTS")
    print("=" * 70)
    
    results = {}
    n = 5
    
    # Test A: Vertex position noise
    print("\n  A. Vertex position noise...")
    
    noise_levels = [0.0, 0.01, 0.05, 0.1, 0.2]
    
    for noise in noise_levels:
        f_count = 0
        
        for _ in range(samples):
            positions = [(np.random.uniform(0, 1) + np.random.normal(0, noise), 
                          np.random.uniform(0, 1) + np.random.normal(0, noise)) 
                         for _ in range(n)]
            
            holonomy = compute_holonomy(positions)
            if classify(holonomy) == "F":
                f_count += 1
        
        p_f = f_count / samples
        results[f'noise_{noise}'] = p_f
        print(f"     noise σ={noise}: P(F)={100*p_f:5.1f}%")
    
    # Test B: Discretized angles (lattice)
    print("\n  B. Lattice coordinates (integer grid)...")
    
    grid_sizes = [10, 20, 50, 100]
    
    for grid in grid_sizes:
        f_count = 0
        
        for _ in range(samples):
            positions = [(np.random.randint(0, grid) / grid, 
                          np.random.randint(0, grid) / grid) 
                         for _ in range(n)]
            
            holonomy = compute_holonomy(positions)
            if classify(holonomy) == "F":
                f_count += 1
        
        p_f = f_count / samples
        results[f'grid_{grid}'] = p_f
        print(f"     grid={grid}: P(F)={100*p_f:5.1f}%")
    
    # Test C: Holonomy measurement noise
    print("\n  C. Holonomy measurement noise...")
    
    hol_noise_levels = [0.0, 0.05, 0.1, 0.2]
    
    for hnoise in hol_noise_levels:
        f_count = 0
        
        for _ in range(samples):
            positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                         for _ in range(n)]
            
            holonomy = compute_holonomy(positions)
            # Add noise to holonomy phase
            phase = np.angle(holonomy) + np.random.normal(0, hnoise)
            noisy_holonomy = np.exp(1j * phase)
            
            if classify(noisy_holonomy) == "F":
                f_count += 1
        
        p_f = f_count / samples
        results[f'hol_noise_{hnoise}'] = p_f
        print(f"     hol_noise={hnoise}: P(F)={100*p_f:5.1f}%")
    
    # Check robustness
    baseline = results.get('noise_0.0', 0.5)
    max_deviation = max(abs(v - baseline) for k, v in results.items() 
                        if isinstance(v, float))
    
    results['robust_to_distortion'] = max_deviation < 0.1
    print(f"\n  Max deviation from baseline: {100*max_deviation:.1f}%")
    print(f"  {'✅ ROBUST' if results['robust_to_distortion'] else '⚠️ SENSITIVE'}")
    
    return results


# =============================================================================
# QUESTION 4: WHAT WOULD MAKE THIS COMPLETELY FAIL?
# =============================================================================

def question_4_failure_conditions(samples: int = 5000) -> Dict:
    """
    QUESTION 4: What would make this completely fail?
    
    Potential failure modes:
    
    A. Force all self-intersecting loops → expect P(F) = P(W odd | self) < 0.5
    B. Force all simple loops → expect P(F) = 1.0
    C. Higher dimensions (3D) → winding is different
    D. Non-planar embeddings → winding undefined
    """
    print("\n" + "=" * 70)
    print("  QUESTION 4: FAILURE CONDITIONS")
    print("=" * 70)
    
    results = {}
    n = 6
    
    # Test A: Force self-intersecting (tight cluster)
    print("\n  A. Forcing self-intersecting loops (tight cluster)...")
    
    f_count = 0
    simple_count = 0
    
    for _ in range(samples):
        # Very tight cluster → high self-intersection probability
        positions = [(0.5 + np.random.normal(0, 0.02), 
                      0.5 + np.random.normal(0, 0.02)) 
                     for _ in range(n)]
        
        if is_simple(positions):
            simple_count += 1
        
        holonomy = compute_holonomy(positions)
        if classify(holonomy) == "F":
            f_count += 1
    
    p_f = f_count / samples
    p_simple = simple_count / samples
    
    results['forced_self_intersecting'] = {'p_f': p_f, 'p_simple': p_simple}
    print(f"     P(simple)={100*p_simple:.1f}%, P(F)={100*p_f:.1f}%")
    
    # Expected: if mostly self-intersecting, P(F) should be < 0.5
    expected_fail = p_simple < 0.1 and p_f < 0.5
    print(f"     {'✅ EXPECTED' if expected_fail else '⚠️ UNEXPECTED'}: "
          f"Self-intersecting → P(F) < 0.5")
    
    # Test B: Force simple (ring arrangement)
    print("\n  B. Forcing simple loops (ring arrangement)...")
    
    f_count = 0
    simple_count = 0
    
    for _ in range(samples):
        # Ring arrangement → always simple
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        noise = np.random.normal(0, 0.1, n)
        positions = [(0.5 + 0.4*np.cos(a + noise[i]), 
                      0.5 + 0.4*np.sin(a + noise[i])) 
                     for i, a in enumerate(angles)]
        
        if is_simple(positions):
            simple_count += 1
        
        holonomy = compute_holonomy(positions)
        if classify(holonomy) == "F":
            f_count += 1
    
    p_f = f_count / samples
    p_simple = simple_count / samples
    
    results['forced_simple'] = {'p_f': p_f, 'p_simple': p_simple}
    print(f"     P(simple)={100*p_simple:.1f}%, P(F)={100*p_f:.1f}%")
    
    # Expected: if all simple, P(F) should be ~100%
    expected_pass = p_simple > 0.9 and p_f > 0.95
    print(f"     {'✅ EXPECTED' if expected_pass else '⚠️ UNEXPECTED'}: "
          f"Simple → P(F) ≈ 100%")
    
    # Test C: What breaks the mechanism?
    print("\n  C. Identifying breaking conditions...")
    
    # Try very large n where simple probability → 0
    large_n = 20
    f_count = 0
    
    for _ in range(samples):
        positions = [(np.random.uniform(0, 1), np.random.uniform(0, 1)) 
                     for _ in range(large_n)]
        
        holonomy = compute_holonomy(positions)
        if classify(holonomy) == "F":
            f_count += 1
    
    p_f_large = f_count / samples
    results['large_n_neutral'] = abs(p_f_large - 0.5) < 0.05
    print(f"     n={large_n}: P(F)={100*p_f_large:.1f}% "
          f"{'(neutral ✅)' if results['large_n_neutral'] else '(not neutral ⚠️)'}")
    
    # Summary of failure conditions
    print("\n  FAILURE CONDITION SUMMARY:")
    print(f"     • Forced self-intersecting → P(F) < 0.5: {'✅' if expected_fail else '❌'}")
    print(f"     • Forced simple → P(F) ≈ 100%: {'✅' if expected_pass else '❌'}")
    print(f"     • Large n → P(F) ≈ 50%: {'✅' if results['large_n_neutral'] else '❌'}")
    
    results['all_failure_conditions_correct'] = expected_fail and expected_pass and results['large_n_neutral']
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def run_four_questions():
    """Run all four standard questions."""
    print("=" * 75)
    print("  QMRT SELF-CRITIQUE PROTOCOL — FOUR STANDARD QUESTIONS")
    print("=" * 75)
    print()
    print("  CLAIM UNDER SCRUTINY:")
    print("  'Loop configurations partition into topological sectors classified")
    print("   by winding parity. Simple loops are strictly odd-winding and thus")
    print("   fermionic, while self-intersecting loops exhibit a strong bias")
    print("   toward even winding.'")
    print()
    
    results = {}
    
    # Question 1
    results['q1_hidden_assumptions'] = question_1_hidden_assumptions()
    
    # Question 2
    results['q2_parameter_sensitivity'] = question_2_parameter_sensitivity()
    
    # Question 3
    results['q3_distortion'] = question_3_distortion_tests()
    
    # Question 4
    results['q4_failure'] = question_4_failure_conditions()
    
    # Summary
    print("\n" + "=" * 75)
    print("  FOUR QUESTIONS SUMMARY")
    print("=" * 75)
    
    q1_pass = results['q1_hidden_assumptions'].get('distribution_robust', False)
    q2_pass = True  # Manual analysis needed
    q3_pass = results['q3_distortion'].get('robust_to_distortion', False)
    q4_pass = results['q4_failure'].get('all_failure_conditions_correct', False)
    
    print(f"""
  Q1. Hidden Assumptions:     {'✅ ROBUST' if q1_pass else '⚠️ NEEDS ATTENTION'}
  Q2. Parameter Sensitivity:  Needs manual analysis (α sweep shows structure)
  Q3. Distortion Tests:       {'✅ ROBUST' if q3_pass else '⚠️ SENSITIVE'}
  Q4. Failure Conditions:     {'✅ ALL CORRECT' if q4_pass else '⚠️ UNEXPECTED'}
    """)
    
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
    
    output_path = '/app/backend/qmrt_topology/four_questions_results.json'
    with open(output_path, 'w') as f:
        json.dump(convert(results), f, indent=2)
    
    print(f"\n  Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_four_questions()
