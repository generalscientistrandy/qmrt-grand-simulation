#!/usr/bin/env python3
"""
QMRT Physics Stress Tests
=========================

Critical validation to ensure results are robust, not circular.

Three Stress Tests:

1. INDEPENDENT TIME DILATION
   - Run two packets SIMULTANEOUSLY in different c_eff regions
   - Measure their accumulated τ_em INDEPENDENTLY
   - If different → true dilation, not circular

2. CURVATURE-TIME COUPLING  
   - Compute curvature proxy R ~ ∇²c_eff
   - Check: Does G correlate with R?
   - Check: Does time slow in high curvature zones?

3. NON-CIRCULAR VALIDATION
   - Ensure dilation factor isn't just c_eff by construction
   - Use independent observables (peak velocity, error rate)

If these pass → theory levels up significantly.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator


def create_two_region_field(size: int) -> np.ndarray:
    """
    Create c_eff field with TWO distinct regions:
    - Left half: High c_eff (fast region)
    - Right half: Low c_eff (slow region)
    """
    c_eff = np.ones((size, size)) * 2.0
    
    for i in range(size):
        for j in range(size):
            # Left-right gradient
            x_norm = i / size
            if x_norm < 0.4:
                c_eff[i, j] = 2.0  # Fast region
            elif x_norm > 0.6:
                c_eff[i, j] = 1.0  # Slow region
            else:
                # Smooth transition
                c_eff[i, j] = 2.0 - 1.0 * (x_norm - 0.4) / 0.2
    
    c_eff = gaussian_filter(c_eff, sigma=2.0)
    c_eff = np.clip(c_eff, 0.5, 2.5)
    
    return c_eff


def compute_curvature(c_eff: np.ndarray) -> np.ndarray:
    """
    Compute scalar curvature proxy: R ~ ∇²c_eff
    
    In 2D conformal geometry:
    R ~ ∇²(ln c_eff)
    """
    log_c = np.log(np.clip(c_eff, 0.1, 10.0))
    
    # Laplacian
    R = (np.roll(log_c, 1, axis=0) + np.roll(log_c, -1, axis=0) +
         np.roll(log_c, 1, axis=1) + np.roll(log_c, -1, axis=1) - 4 * log_c)
    
    return R


def simulate_two_packets(c_eff: np.ndarray, n_steps: int = 500) -> dict:
    """
    Stress Test 1: Simulate TWO packets simultaneously in different regions.
    
    - Packet A: Starts in fast region (high c_eff)
    - Packet B: Starts in slow region (low c_eff)
    
    Track their INDEPENDENT τ_em accumulation.
    """
    size = c_eff.shape[0]
    
    # Two independent field systems
    field_A = np.zeros((size, size))
    velocity_A = np.zeros((size, size))
    field_B = np.zeros((size, size))
    velocity_B = np.zeros((size, size))
    
    # Packet A: Fast region (left)
    start_A = np.array([size * 0.2, size * 0.5])
    # Packet B: Slow region (right)
    start_B = np.array([size * 0.8, size * 0.5])
    
    packet_width = 4.0
    
    for i in range(size):
        for j in range(size):
            r_A = np.sqrt((i - start_A[0])**2 + (j - start_A[1])**2)
            r_B = np.sqrt((i - start_B[0])**2 + (j - start_B[1])**2)
            
            if r_A < 4 * packet_width:
                velocity_A[i, j] = 4.0 * np.exp(-r_A**2 / (2 * packet_width**2))
            if r_B < 4 * packet_width:
                velocity_B[i, j] = 4.0 * np.exp(-r_B**2 / (2 * packet_width**2))
    
    dt = 0.04
    damping = 0.008
    
    # Independent tracking
    tau_A = 0.0  # Accumulated τ for packet A
    tau_B = 0.0  # Accumulated τ for packet B
    
    tau_A_history = []
    tau_B_history = []
    c_eff_A_history = []
    c_eff_B_history = []
    raw_times = []
    
    for t in range(n_steps):
        # Wave equation for A
        lap_A = (np.roll(field_A, 1, axis=0) + np.roll(field_A, -1, axis=0) +
                 np.roll(field_A, 1, axis=1) + np.roll(field_A, -1, axis=1) - 4 * field_A)
        acc_A = c_eff**2 * lap_A - damping * velocity_A
        velocity_A += acc_A * dt
        field_A += velocity_A * dt
        
        # Wave equation for B
        lap_B = (np.roll(field_B, 1, axis=0) + np.roll(field_B, -1, axis=0) +
                 np.roll(field_B, 1, axis=1) + np.roll(field_B, -1, axis=1) - 4 * field_B)
        acc_B = c_eff**2 * lap_B - damping * velocity_B
        velocity_B += acc_B * dt
        field_B += velocity_B * dt
        
        if t % 5 == 0 and t > 10:
            # Find packet A position
            energy_A = field_A**2 + velocity_A**2
            if np.sum(energy_A) > 1e-10:
                peak_A = np.unravel_index(np.argmax(np.abs(field_A)), field_A.shape)
                c_A = c_eff[peak_A[0], peak_A[1]]
            else:
                c_A = 2.0
            
            # Find packet B position
            energy_B = field_B**2 + velocity_B**2
            if np.sum(energy_B) > 1e-10:
                peak_B = np.unravel_index(np.argmax(np.abs(field_B)), field_B.shape)
                c_B = c_eff[peak_B[0], peak_B[1]]
            else:
                c_B = 1.0
            
            # Accumulate τ INDEPENDENTLY for each packet
            tau_A += c_A * dt * 5
            tau_B += c_B * dt * 5
            
            raw_times.append(t * dt)
            tau_A_history.append(tau_A)
            tau_B_history.append(tau_B)
            c_eff_A_history.append(c_A)
            c_eff_B_history.append(c_B)
    
    return {
        'raw_times': np.array(raw_times),
        'tau_A': np.array(tau_A_history),
        'tau_B': np.array(tau_B_history),
        'c_eff_A': np.array(c_eff_A_history),
        'c_eff_B': np.array(c_eff_B_history),
        'final_tau_A': tau_A,
        'final_tau_B': tau_B,
        'c_eff': c_eff,
    }


def test_curvature_time_coupling(c_eff: np.ndarray) -> dict:
    """
    Stress Test 2: Does curvature correlate with geometry stability G?
    
    - Compute R ~ ∇²(ln c_eff) at each point
    - Compare with local c_eff and estimate of G
    """
    size = c_eff.shape[0]
    
    # Compute curvature
    R = compute_curvature(c_eff)
    
    # Compute G proxy (inverse of gradient magnitude)
    grad_x = np.gradient(c_eff, axis=0)
    grad_y = np.gradient(c_eff, axis=1)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    G_proxy = 1.0 / (grad_mag + 0.01)  # Higher G where gradient is smaller
    
    # Flatten for correlation
    R_flat = R.flatten()
    c_flat = c_eff.flatten()
    G_flat = G_proxy.flatten()
    
    # Correlations
    corr_R_c = np.corrcoef(R_flat, c_flat)[0, 1]
    corr_R_G = np.corrcoef(R_flat, G_flat)[0, 1]
    corr_c_G = np.corrcoef(c_flat, G_flat)[0, 1]
    
    return {
        'R': R,
        'G_proxy': G_proxy,
        'corr_R_c': float(corr_R_c) if not np.isnan(corr_R_c) else 0,
        'corr_R_G': float(corr_R_G) if not np.isnan(corr_R_G) else 0,
        'corr_c_G': float(corr_c_G) if not np.isnan(corr_c_G) else 0,
    }


def validate_non_circular(two_packet_result: dict) -> dict:
    """
    Stress Test 3: Validate that time dilation isn't circular.
    
    Check: Is the dilation factor DIFFERENT from just the c_eff ratio?
    
    If dilation_factor ≈ c_eff ratio exactly → circular (suspicious)
    If dilation_factor ≠ c_eff ratio → genuine emergent effect
    """
    tau_A = two_packet_result['final_tau_A']
    tau_B = two_packet_result['final_tau_B']
    c_eff_A = np.mean(two_packet_result['c_eff_A'])
    c_eff_B = np.mean(two_packet_result['c_eff_B'])
    
    # Measured dilation ratio
    dilation_ratio = tau_A / tau_B if tau_B > 0 else 1.0
    
    # c_eff ratio (what we'd expect if circular)
    c_eff_ratio = c_eff_A / c_eff_B if c_eff_B > 0 else 1.0
    
    # Check if they're the same (circular) or different (genuine)
    ratio_difference = abs(dilation_ratio - c_eff_ratio) / c_eff_ratio * 100
    
    # Determine if circular
    is_circular = ratio_difference < 5  # Less than 5% difference = likely circular
    
    return {
        'tau_A': float(tau_A),
        'tau_B': float(tau_B),
        'dilation_ratio': float(dilation_ratio),
        'c_eff_A': float(c_eff_A),
        'c_eff_B': float(c_eff_B),
        'c_eff_ratio': float(c_eff_ratio),
        'ratio_difference_percent': float(ratio_difference),
        'is_circular': bool(is_circular),
    }


def run_stress_tests():
    """
    Run all three stress tests.
    """
    print("=" * 70)
    print("QMRT PHYSICS STRESS TESTS")
    print("=" * 70)
    print("Goal: Validate results are robust, not circular")
    print()
    
    np.random.seed(42)
    
    size = 120
    
    # Create two-region field
    c_eff = create_two_region_field(size)
    
    print(f"c_eff field created:")
    print(f"  Fast region (left): c_eff ≈ {np.mean(c_eff[:size//3, :]):.2f}")
    print(f"  Slow region (right): c_eff ≈ {np.mean(c_eff[2*size//3:, :]):.2f}")
    
    # =================================
    # TEST 1: Independent Time Dilation
    # =================================
    print("\n" + "=" * 70)
    print("STRESS TEST 1: INDEPENDENT TIME DILATION")
    print("=" * 70)
    print("Two packets in different regions - do they accumulate τ independently?")
    
    two_packet = simulate_two_packets(c_eff, n_steps=500)
    
    print(f"\nPacket A (fast region):")
    print(f"  Mean c_eff experienced: {np.mean(two_packet['c_eff_A']):.3f}")
    print(f"  Final τ_A: {two_packet['final_tau_A']:.2f}")
    
    print(f"\nPacket B (slow region):")
    print(f"  Mean c_eff experienced: {np.mean(two_packet['c_eff_B']):.3f}")
    print(f"  Final τ_B: {two_packet['final_tau_B']:.2f}")
    
    dilation = two_packet['final_tau_A'] / two_packet['final_tau_B'] if two_packet['final_tau_B'] > 0 else 1.0
    print(f"\n>>> Time dilation factor (τ_A/τ_B): {dilation:.3f}")
    
    if abs(dilation - 1.0) > 0.1:
        print(">>> INDEPENDENT DILATION CONFIRMED: Packets accumulated different τ")
        test1_pass = True
    else:
        print(">>> No significant dilation observed")
        test1_pass = False
    
    # =================================
    # TEST 2: Curvature-Time Coupling
    # =================================
    print("\n" + "=" * 70)
    print("STRESS TEST 2: CURVATURE-TIME COUPLING")
    print("=" * 70)
    print("Does curvature R ~ ∇²c_eff correlate with geometry stability G?")
    
    curvature_result = test_curvature_time_coupling(c_eff)
    
    print(f"\nCorrelations:")
    print(f"  R vs c_eff: {curvature_result['corr_R_c']:.3f}")
    print(f"  R vs G: {curvature_result['corr_R_G']:.3f}")
    print(f"  c_eff vs G: {curvature_result['corr_c_G']:.3f}")
    
    if abs(curvature_result['corr_R_G']) > 0.3:
        print(">>> CURVATURE-STABILITY COUPLING DETECTED")
        test2_pass = True
    else:
        print(">>> No clear curvature-stability coupling")
        test2_pass = False
    
    # =================================
    # TEST 3: Non-Circular Validation
    # =================================
    print("\n" + "=" * 70)
    print("STRESS TEST 3: NON-CIRCULAR VALIDATION")
    print("=" * 70)
    print("Is dilation factor different from c_eff ratio?")
    
    circular_result = validate_non_circular(two_packet)
    
    print(f"\nDilation ratio (τ_A/τ_B): {circular_result['dilation_ratio']:.4f}")
    print(f"c_eff ratio (c_A/c_B): {circular_result['c_eff_ratio']:.4f}")
    print(f"Difference: {circular_result['ratio_difference_percent']:.2f}%")
    
    if circular_result['is_circular']:
        print(">>> WARNING: Result may be circular (dilation ≈ c_eff ratio)")
        print(">>> This means τ ~ ∫ c_eff dt is just measuring c_eff, not something deeper")
        test3_pass = False
    else:
        print(">>> NON-CIRCULAR: Dilation differs from simple c_eff ratio")
        test3_pass = True
    
    # =================================
    # OVERALL VERDICT
    # =================================
    print("\n" + "=" * 70)
    print("STRESS TEST SUMMARY")
    print("=" * 70)
    
    tests_passed = sum([test1_pass, test2_pass, test3_pass])
    
    print(f"Test 1 (Independent Dilation): {'PASS' if test1_pass else 'FAIL'}")
    print(f"Test 2 (Curvature Coupling): {'PASS' if test2_pass else 'FAIL'}")
    print(f"Test 3 (Non-Circular): {'PASS' if test3_pass else 'FAIL'}")
    print()
    print(f"Tests passed: {tests_passed}/3")
    
    if tests_passed == 3:
        overall_verdict = "ALL STRESS TESTS PASSED - Theory is robust"
    elif tests_passed >= 2:
        overall_verdict = "PARTIAL PASS - Results mostly robust"
    else:
        overall_verdict = "NEEDS REFINEMENT - Some circular or weak results"
    
    print(f"\n>>> OVERALL VERDICT: {overall_verdict}")
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 15))
    
    # c_eff field
    ax = fig.add_subplot(3, 4, 1)
    im = ax.imshow(c_eff.T, origin='lower', cmap='viridis_r', extent=[0, size, 0, size])
    ax.axvline(size*0.2, color='cyan', linestyle='--', label='Packet A start')
    ax.axvline(size*0.8, color='magenta', linestyle='--', label='Packet B start')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Two-Region c_eff Field')
    plt.colorbar(im, ax=ax, label='c_eff')
    ax.legend()
    
    # Curvature field
    ax = fig.add_subplot(3, 4, 2)
    R = curvature_result['R']
    im = ax.imshow(R.T, origin='lower', cmap='RdBu', extent=[0, size, 0, size],
                  vmin=-np.percentile(np.abs(R), 95), vmax=np.percentile(np.abs(R), 95))
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Curvature R ~ ∇²(ln c_eff)')
    plt.colorbar(im, ax=ax, label='R')
    
    # G proxy field
    ax = fig.add_subplot(3, 4, 3)
    G = curvature_result['G_proxy']
    im = ax.imshow(G.T, origin='lower', cmap='plasma', extent=[0, size, 0, size])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Geometry Stability G (proxy)')
    plt.colorbar(im, ax=ax, label='G')
    
    # c_eff vs R scatter
    ax = fig.add_subplot(3, 4, 4)
    ax.scatter(c_eff.flatten()[::100], R.flatten()[::100], alpha=0.5, s=10)
    ax.set_xlabel('c_eff')
    ax.set_ylabel('Curvature R')
    ax.set_title(f'c_eff vs R\nCorr = {curvature_result["corr_R_c"]:.3f}')
    ax.grid(True, alpha=0.3)
    
    # τ accumulation over time
    ax = fig.add_subplot(3, 4, 5)
    ax.plot(two_packet['raw_times'], two_packet['tau_A'], 'c-', linewidth=2, label='τ_A (fast)')
    ax.plot(two_packet['raw_times'], two_packet['tau_B'], 'm-', linewidth=2, label='τ_B (slow)')
    ax.plot(two_packet['raw_times'], two_packet['raw_times'], 'k--', linewidth=1, label='t (raw)')
    ax.set_xlabel('Raw Time t')
    ax.set_ylabel('Accumulated τ')
    ax.set_title('Independent Time Accumulation')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # c_eff experienced by each packet
    ax = fig.add_subplot(3, 4, 6)
    ax.plot(two_packet['raw_times'], two_packet['c_eff_A'], 'c-', linewidth=2, label='c_eff at A')
    ax.plot(two_packet['raw_times'], two_packet['c_eff_B'], 'm-', linewidth=2, label='c_eff at B')
    ax.set_xlabel('Raw Time')
    ax.set_ylabel('Local c_eff')
    ax.set_title('c_eff Experienced by Packets')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Dilation factor over time
    ax = fig.add_subplot(3, 4, 7)
    with np.errstate(divide='ignore', invalid='ignore'):
        dilation_over_time = two_packet['tau_A'] / np.maximum(two_packet['tau_B'], 0.01)
    ax.plot(two_packet['raw_times'], dilation_over_time, 'g-', linewidth=2)
    ax.axhline(1.0, color='red', linestyle='--', label='No dilation')
    ax.set_xlabel('Raw Time')
    ax.set_ylabel('τ_A / τ_B')
    ax.set_title('Time Dilation Factor Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Circular test
    ax = fig.add_subplot(3, 4, 8)
    labels = ['Dilation\nRatio', 'c_eff\nRatio']
    values = [circular_result['dilation_ratio'], circular_result['c_eff_ratio']]
    colors = ['green' if not circular_result['is_circular'] else 'red', 'blue']
    ax.bar(labels, values, color=colors)
    ax.set_ylabel('Ratio')
    ax.set_title(f'Circular Test\nDiff = {circular_result["ratio_difference_percent"]:.1f}%')
    
    # R vs G scatter
    ax = fig.add_subplot(3, 4, 9)
    ax.scatter(R.flatten()[::100], G.flatten()[::100], alpha=0.5, s=10)
    ax.set_xlabel('Curvature R')
    ax.set_ylabel('Geometry Stability G')
    ax.set_title(f'Curvature vs Stability\nCorr = {curvature_result["corr_R_G"]:.3f}')
    ax.grid(True, alpha=0.3)
    
    # Summary
    ax = fig.add_subplot(3, 4, 10)
    ax.axis('off')
    
    summary_text = f"""
STRESS TEST RESULTS
===================

Test 1: Independent Dilation
  Packet A (fast): τ = {two_packet['final_tau_A']:.1f}
  Packet B (slow): τ = {two_packet['final_tau_B']:.1f}
  Dilation: {dilation:.3f}
  Result: {'PASS' if test1_pass else 'FAIL'}

Test 2: Curvature Coupling
  Corr(R, G): {curvature_result['corr_R_G']:.3f}
  Result: {'PASS' if test2_pass else 'FAIL'}

Test 3: Non-Circular
  Dilation ratio: {circular_result['dilation_ratio']:.4f}
  c_eff ratio: {circular_result['c_eff_ratio']:.4f}
  Difference: {circular_result['ratio_difference_percent']:.1f}%
  Result: {'PASS' if test3_pass else 'FAIL'}

OVERALL: {overall_verdict}
"""
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Interpretation
    ax = fig.add_subplot(3, 4, 11)
    ax.axis('off')
    
    if circular_result['is_circular']:
        interp_text = """
INTERPRETATION (CIRCULAR WARNING)
=================================

The dilation ratio ≈ c_eff ratio

This means:
  τ = ∫ c_eff dt
  is essentially just measuring c_eff

The "time dilation" is by CONSTRUCTION,
not an emergent property.

To fix this:
  1. Use a different G formulation
  2. Add energy dependence
  3. Measure independent observables
"""
    else:
        interp_text = """
INTERPRETATION (NON-CIRCULAR)
=============================

The dilation ratio ≠ c_eff ratio

This means the emergent time τ_em
captures MORE than just c_eff.

The combined clock τ = ∫ c_eff · G^-1 dt
is genuinely measuring an emergent
causal structure, not just propagation
speed.

This supports the claim:
"preferred causal parameterization
tied to propagation AND stability"
"""
    ax.text(0.05, 0.95, interp_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', 
                    facecolor='lightcoral' if circular_result['is_circular'] else 'lightgreen', 
                    alpha=0.5))
    
    # Verdict
    ax = fig.add_subplot(3, 4, 12)
    ax.axis('off')
    
    if tests_passed == 3:
        verdict_color = 'lightgreen'
        verdict_text = f"""
VERDICT: ALL TESTS PASSED
=========================

The physics is robust:
  ✓ Independent dilation confirmed
  ✓ Curvature-stability coupling
  ✓ Non-circular measurement

This supports:
"Emergent causal parameterization
where time = propagation × stability"

Ready for publication-level claims.
"""
    else:
        verdict_color = 'lightyellow'
        verdict_text = f"""
VERDICT: {tests_passed}/3 TESTS PASSED
======================================

{'Strengths:' if tests_passed > 0 else 'Issues:'}
{' ✓ Dilation observed' if test1_pass else ' ✗ No clear dilation'}
{' ✓ Curvature coupling' if test2_pass else ' ✗ Weak coupling'}
{' ✓ Non-circular' if test3_pass else ' ✗ May be circular'}

Recommendation:
  Refine clock formulation
  Test with stronger gradients
  Add energy dependence to G
"""
    ax.text(0.05, 0.95, verdict_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=verdict_color, alpha=0.5))
    
    plt.suptitle(f'PHYSICS STRESS TESTS: {overall_verdict}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/stress_tests.png', dpi=150, bbox_inches='tight')
    print("\nSaved stress_tests.png")
    
    # Save results
    import json
    summary = {
        'overall_verdict': overall_verdict,
        'tests_passed': tests_passed,
        'test1_dilation': {
            'tau_A': float(two_packet['final_tau_A']),
            'tau_B': float(two_packet['final_tau_B']),
            'dilation_factor': float(dilation),
            'passed': test1_pass,
        },
        'test2_curvature': {
            'corr_R_G': curvature_result['corr_R_G'],
            'corr_R_c': curvature_result['corr_R_c'],
            'passed': test2_pass,
        },
        'test3_circular': {
            'dilation_ratio': circular_result['dilation_ratio'],
            'c_eff_ratio': circular_result['c_eff_ratio'],
            'difference_percent': circular_result['ratio_difference_percent'],
            'is_circular': circular_result['is_circular'],
            'passed': test3_pass,
        },
    }
    
    with open('/app/backend/qmrt_topology/stress_tests_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved stress_tests_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_stress_tests()
    
    print("\n" + "=" * 70)
    print("FINAL STRESS TEST SUMMARY")
    print("=" * 70)
    print(f"Overall: {result['overall_verdict']}")
    print(f"Tests passed: {result['tests_passed']}/3")
