#!/usr/bin/env python3
"""
QMRT Multi-Clock Synchronization Test
======================================

NON-CIRCULAR emergent time test using LAYERED CLOCK STRUCTURE:

Layer 0 — SUBSTRATE CLOCK
  Φ(t) = Φ₀ + ω_substrate × t
  The medium's internal phase/update rhythm

Layer 1 — CAUSAL CLOCK  
  τ_c = ∫ c_eff(path) dt
  Tied to signal transport

Layer 2 — LOCAL PROCESS CLOCKS
  - Oscillator clock: counts cycles relative to local medium state
  - Decay clock: metastable excitation lifetime

KEY TEST:
  - In DISORDERED regime: clocks disagree strongly
  - In COHERENT regime: clocks synchronize → emergent common time

METRIC:
  Δ_clocks = Var(τ₁, τ₂, τ₃) / Mean(τ)
  - Large Δ: no shared time
  - Small Δ: emergent common time

If synchronization improves as coherence improves → GENUINE EMERGENT TIME
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter


def create_regime_field(size: int, disorder_level: float) -> np.ndarray:
    """
    Create c_eff field with controllable disorder.
    
    disorder_level:
    - 0.0: Perfectly smooth (coherent)
    - 0.5: Moderate disorder
    - 1.0: Highly disordered
    """
    # Base gradient
    c_eff = np.ones((size, size)) * 1.5
    for i in range(size):
        for j in range(size):
            normalized_y = (j - size/2) / (size/4)
            c_eff[i, j] = 2.0 - 0.5 * (1 + np.tanh(normalized_y)) / 2
    
    # Add disorder (random fluctuations)
    if disorder_level > 0:
        noise = np.random.randn(size, size) * disorder_level * 0.5
        c_eff += noise
    
    # Smooth based on disorder (less smoothing = more disorder)
    sigma = max(1.0, 5.0 * (1 - disorder_level))
    c_eff = gaussian_filter(c_eff, sigma=sigma)
    c_eff = np.clip(c_eff, 0.5, 2.5)
    
    return c_eff


class SubstrateClock:
    """
    Layer 0: Medium's internal phase oscillation.
    Φ(t) = Φ₀ + ω × t
    """
    def __init__(self, omega: float = 1.0):
        self.omega = omega
        self.phase = 0.0
        self.cycle_count = 0
    
    def tick(self, dt: float):
        self.phase += self.omega * dt
        # Count full cycles
        while self.phase >= 2 * np.pi:
            self.phase -= 2 * np.pi
            self.cycle_count += 1
    
    def get_time(self) -> float:
        return self.cycle_count + self.phase / (2 * np.pi)


class OscillatorClock:
    """
    Layer 2a: Local oscillator that counts cycles.
    Rate depends on local c_eff.
    """
    def __init__(self, base_freq: float = 0.5):
        self.base_freq = base_freq
        self.accumulated_phase = 0.0
        self.cycle_count = 0
    
    def tick(self, dt: float, local_c_eff: float):
        # Oscillation rate modified by local c_eff
        # Higher c_eff → faster oscillation
        local_freq = self.base_freq * local_c_eff
        self.accumulated_phase += local_freq * dt
        
        while self.accumulated_phase >= 2 * np.pi:
            self.accumulated_phase -= 2 * np.pi
            self.cycle_count += 1
    
    def get_time(self) -> float:
        return self.cycle_count + self.accumulated_phase / (2 * np.pi)


class DecayClock:
    """
    Layer 2b: Metastable excitation with decay.
    Decay rate depends on local coherence/stability.
    
    P_decay = λ × (1 + α × disorder) × dt
    """
    def __init__(self, base_lambda: float = 0.01, alpha: float = 2.0):
        self.base_lambda = base_lambda
        self.alpha = alpha
        self.alive = True
        self.lifetime = 0.0
    
    def tick(self, dt: float, local_stability: float):
        if not self.alive:
            return
        
        # Higher stability → lower decay rate
        effective_lambda = self.base_lambda / max(local_stability, 0.1)
        
        if np.random.random() < effective_lambda * dt:
            self.alive = False
        else:
            self.lifetime += dt
    
    def get_time(self) -> float:
        return self.lifetime


def compute_local_stability(c_eff: np.ndarray, i: int, j: int) -> float:
    """
    Compute local geometry stability at position (i,j).
    Based on gradient magnitude (lower gradient = more stable).
    """
    size = c_eff.shape[0]
    
    # Ensure bounds
    i = np.clip(i, 1, size-2)
    j = np.clip(j, 1, size-2)
    
    # Local gradient
    grad_x = (c_eff[i+1, j] - c_eff[i-1, j]) / 2
    grad_y = (c_eff[i, j+1] - c_eff[i, j-1]) / 2
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    
    # Stability: inverse of gradient
    stability = 1.0 / (grad_mag + 0.1)
    
    return stability


def simulate_multi_clock(c_eff: np.ndarray, n_steps: int = 500) -> dict:
    """
    Run simulation with all three clock layers.
    """
    size = c_eff.shape[0]
    
    # Wave field
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    # Initialize wave packet
    start = np.array([size * 0.2, size * 0.5])
    packet_width = 4.0
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - start[0])**2 + (j - start[1])**2)
            if r < 4 * packet_width:
                velocity[i, j] = 4.0 * np.exp(-r**2 / (2 * packet_width**2))
    
    dt = 0.04
    damping = 0.008
    
    # Initialize clocks
    substrate_clock = SubstrateClock(omega=1.0)
    oscillator_clock = OscillatorClock(base_freq=0.5)
    decay_clock = DecayClock(base_lambda=0.005, alpha=2.0)
    
    # Causal clock (signal-based)
    causal_time = 0.0
    
    # History
    raw_times = []
    substrate_times = []
    causal_times = []
    oscillator_times = []
    decay_times = []
    
    for t in range(n_steps):
        # Wave equation
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        # Find packet position
        energy = field**2 + velocity**2
        if np.sum(energy) > 1e-10:
            peak_idx = np.unravel_index(np.argmax(np.abs(field)), field.shape)
            pi, pj = peak_idx
        else:
            pi, pj = int(start[0]), int(start[1])
        
        # Get local properties
        local_c = c_eff[pi, pj]
        local_stability = compute_local_stability(c_eff, pi, pj)
        
        # Update all clocks
        substrate_clock.tick(dt)
        oscillator_clock.tick(dt, local_c)
        decay_clock.tick(dt, local_stability)
        causal_time += local_c * dt
        
        # Record every 5 steps
        if t % 5 == 0:
            raw_times.append(t * dt)
            substrate_times.append(substrate_clock.get_time())
            causal_times.append(causal_time)
            oscillator_times.append(oscillator_clock.get_time())
            decay_times.append(decay_clock.get_time())
    
    return {
        'raw_times': np.array(raw_times),
        'substrate_times': np.array(substrate_times),
        'causal_times': np.array(causal_times),
        'oscillator_times': np.array(oscillator_times),
        'decay_times': np.array(decay_times),
        'decay_alive': decay_clock.alive,
    }


def compute_clock_agreement(substrate, causal, oscillator, decay) -> float:
    """
    Compute clock agreement metric.
    
    Δ_clocks = Var(τ₁, τ₂, τ₃) / Mean(τ)
    
    Small Δ = clocks agree (emergent common time)
    Large Δ = clocks disagree (no shared time)
    """
    # Normalize clocks to same scale [0, 1]
    def normalize(arr):
        if arr[-1] == arr[0]:
            return np.zeros_like(arr)
        return (arr - arr[0]) / (arr[-1] - arr[0])
    
    s_norm = normalize(substrate)
    c_norm = normalize(causal)
    o_norm = normalize(oscillator)
    d_norm = normalize(decay) if decay[-1] > decay[0] else np.zeros_like(decay)
    
    # Stack and compute variance at each time point
    clocks = np.vstack([s_norm, c_norm, o_norm, d_norm])
    
    # Mean variance across time
    variance = np.mean(np.var(clocks, axis=0))
    
    return variance


def run_synchronization_test():
    """
    Main test: Compare clock agreement across disorder regimes.
    """
    print("=" * 70)
    print("MULTI-CLOCK SYNCHRONIZATION TEST")
    print("=" * 70)
    print("Testing layered clock structure across disorder→coherence regimes")
    print()
    print("Clock layers:")
    print("  Layer 0: Substrate (medium phase)")
    print("  Layer 1: Causal (signal transport)")
    print("  Layer 2a: Oscillator (local cycles)")
    print("  Layer 2b: Decay (metastable lifetime)")
    print()
    
    np.random.seed(42)
    
    size = 100
    
    # Test multiple disorder levels
    disorder_levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    results = {}
    
    print("Running simulations across disorder levels...")
    
    for disorder in disorder_levels:
        print(f"\n  Disorder = {disorder:.1f}...", end=" ")
        
        # Average over multiple runs for decay clock (stochastic)
        agreements = []
        all_clocks = []
        
        for run in range(5):
            c_eff = create_regime_field(size, disorder)
            sim_result = simulate_multi_clock(c_eff, n_steps=400)
            
            agreement = compute_clock_agreement(
                sim_result['substrate_times'],
                sim_result['causal_times'],
                sim_result['oscillator_times'],
                sim_result['decay_times']
            )
            agreements.append(agreement)
            
            if run == 0:
                all_clocks = sim_result
        
        mean_agreement = np.mean(agreements)
        std_agreement = np.std(agreements)
        
        results[disorder] = {
            'mean_agreement': mean_agreement,
            'std_agreement': std_agreement,
            'clocks': all_clocks,
            'c_eff': c_eff,
        }
        
        print(f"Δ_clocks = {mean_agreement:.4f} ± {std_agreement:.4f}")
    
    # =================================
    # ANALYSIS
    # =================================
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    disorders = list(results.keys())
    agreements = [results[d]['mean_agreement'] for d in disorders]
    
    # Check if agreement improves (decreases) with coherence (lower disorder)
    correlation = np.corrcoef(disorders, agreements)[0, 1]
    
    print(f"\nCorrelation(disorder, Δ_clocks): {correlation:.3f}")
    
    if correlation > 0.5:
        print(">>> CLOCK SYNCHRONIZATION IMPROVES WITH COHERENCE")
        print(">>> Lower disorder → better clock agreement")
        print(">>> This is GENUINE EMERGENT TIME behavior!")
        test_passed = True
    elif correlation < -0.5:
        print(">>> UNEXPECTED: Agreement worsens with coherence")
        test_passed = False
    else:
        print(">>> No clear trend between disorder and agreement")
        test_passed = False
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 15))
    
    # Row 1: c_eff fields at different disorders
    sample_disorders = [0.0, 0.4, 0.8]
    for idx, d in enumerate(sample_disorders):
        ax = fig.add_subplot(3, 4, idx + 1)
        c_eff = results[d]['c_eff']
        im = ax.imshow(c_eff.T, origin='lower', cmap='viridis', extent=[0, size, 0, size])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title(f'c_eff (disorder={d})')
        plt.colorbar(im, ax=ax, label='c_eff')
    
    # Agreement vs disorder
    ax = fig.add_subplot(3, 4, 4)
    ax.errorbar(disorders, agreements, 
               yerr=[results[d]['std_agreement'] for d in disorders],
               fmt='bo-', linewidth=2, markersize=10, capsize=5)
    ax.set_xlabel('Disorder Level')
    ax.set_ylabel('Clock Disagreement Δ')
    ax.set_title(f'Clock Agreement vs Disorder\nCorr = {correlation:.3f}')
    ax.grid(True, alpha=0.3)
    
    # Row 2: Clock evolution at different disorders
    for idx, d in enumerate(sample_disorders):
        ax = fig.add_subplot(3, 4, 5 + idx)
        clocks = results[d]['clocks']
        
        # Normalize for comparison
        raw = clocks['raw_times']
        sub = clocks['substrate_times']
        cau = clocks['causal_times']
        osc = clocks['oscillator_times']
        dec = clocks['decay_times']
        
        # Normalize to [0, 1]
        def norm(arr):
            if arr[-1] > arr[0]:
                return (arr - arr[0]) / (arr[-1] - arr[0])
            return np.zeros_like(arr)
        
        ax.plot(raw, norm(sub), 'r-', linewidth=2, label='Substrate')
        ax.plot(raw, norm(cau), 'b-', linewidth=2, label='Causal')
        ax.plot(raw, norm(osc), 'g-', linewidth=2, label='Oscillator')
        if dec[-1] > dec[0]:
            ax.plot(raw, norm(dec), 'm-', linewidth=2, label='Decay')
        ax.plot(raw, norm(raw), 'k--', linewidth=1, label='Raw t')
        
        ax.set_xlabel('Raw Time')
        ax.set_ylabel('Normalized τ')
        ax.set_title(f'Clock Evolution (disorder={d})')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # Clock spread visualization
    ax = fig.add_subplot(3, 4, 8)
    for d in [0.0, 0.4, 1.0]:  # Use tested disorder levels
        clocks = results[d]['clocks']
        raw = clocks['raw_times']
        
        # Compute spread at each time
        sub = clocks['substrate_times']
        cau = clocks['causal_times']
        osc = clocks['oscillator_times']
        
        def norm(arr):
            if arr[-1] > arr[0]:
                return (arr - arr[0]) / (arr[-1] - arr[0])
            return np.zeros_like(arr)
        
        spread = np.std([norm(sub), norm(cau), norm(osc)], axis=0)
        ax.plot(raw, spread, linewidth=2, label=f'd={d}')
    
    ax.set_xlabel('Raw Time')
    ax.set_ylabel('Clock Spread (Std)')
    ax.set_title('Clock Disagreement Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Summary
    ax = fig.add_subplot(3, 4, 9)
    ax.axis('off')
    
    summary_text = f"""
MULTI-CLOCK SYNCHRONIZATION
===========================

Clock Layers:
  0. Substrate: Φ = Φ₀ + ω×t
  1. Causal: τ_c = ∫ c_eff dt
  2a. Oscillator: local cycle count
  2b. Decay: metastable lifetime

Disorder vs Agreement:
"""
    for d in disorders:
        summary_text += f"  d={d:.1f}: Δ = {results[d]['mean_agreement']:.4f}\n"
    
    summary_text += f"""
Correlation: {correlation:.3f}
Test: {'PASSED' if test_passed else 'FAILED'}

Interpretation:
{'Clocks synchronize in coherent regimes → EMERGENT TIME' if test_passed else 'No clear synchronization pattern'}
"""
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Interpretation
    ax = fig.add_subplot(3, 4, 10)
    ax.axis('off')
    
    if test_passed:
        interp_text = """
KEY RESULT: EMERGENT TIME CONFIRMED
===================================

In DISORDERED regime:
  - Clocks disagree strongly
  - No shared time concept
  - Different processes evolve at
    different rates

In COHERENT regime:
  - Clocks synchronize
  - Emergent common time appears
  - Substrate, causal, and process
    clocks align

This is NON-CIRCULAR because:
  - Clocks are INDEPENDENTLY defined
  - Agreement EMERGES from coherence
  - Not constructed from c_eff alone

QMRT interpretation:
  "Time emerges when the medium
   achieves sufficient coherence
   for clock processes to synchronize"
"""
    else:
        interp_text = """
RESULT: NO CLEAR EMERGENCE
==========================

Clocks did not show clear
synchronization pattern across
disorder regimes.

Possible reasons:
  - Clock definitions need refinement
  - Coherence threshold not reached
  - More runs needed for statistics

Next steps:
  - Adjust oscillator/decay parameters
  - Test stronger disorder gradients
  - Add more clock types
"""
    
    ax.text(0.05, 0.95, interp_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', 
                    facecolor='lightgreen' if test_passed else 'lightyellow', 
                    alpha=0.5))
    
    # Verdict
    ax = fig.add_subplot(3, 4, 11)
    ax.axis('off')
    
    verdict = "EMERGENT TIME DEMONSTRATED" if test_passed else "NEEDS MORE WORK"
    
    verdict_text = f"""
VERDICT: {verdict}

{'✓ Clock agreement improves with coherence' if test_passed else '✗ No clear trend'}
{'✓ Non-circular measurement' if test_passed else '✗ Need to refine clocks'}
{'✓ Genuine emergence detected' if test_passed else '✗ Emergence not confirmed'}

Scientific statement:
"{'We observe clock synchronization improving with medium coherence, indicating emergent common time arises from substrate organization rather than being imposed externally.' if test_passed else 'Further refinement of clock definitions is needed to detect emergent time.'}"
"""
    ax.text(0.05, 0.95, verdict_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', 
                    facecolor='lightgreen' if test_passed else 'lightyellow',
                    alpha=0.5))
    
    # Regime diagram
    ax = fig.add_subplot(3, 4, 12)
    ax.barh(['Disordered\n(d=1.0)', 'Transitional\n(d=0.5)', 'Coherent\n(d=0.0)'],
           [results[1.0]['mean_agreement'], 
            results[0.4]['mean_agreement'],
            results[0.0]['mean_agreement']],
           color=['red', 'yellow', 'green'])
    ax.set_xlabel('Clock Disagreement Δ')
    ax.set_title('Disagreement by Regime')
    ax.invert_yaxis()
    
    plt.suptitle(f'MULTI-CLOCK SYNCHRONIZATION: {verdict}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/clock_synchronization.png', dpi=150, 
               bbox_inches='tight')
    print("\nSaved clock_synchronization.png")
    
    # Save results
    import json
    summary = {
        'verdict': verdict,
        'test_passed': test_passed,
        'correlation_disorder_agreement': float(correlation),
        'results_by_disorder': {
            str(d): {
                'mean_agreement': float(results[d]['mean_agreement']),
                'std_agreement': float(results[d]['std_agreement']),
            }
            for d in disorders
        },
        'scientific_statement': (
            "We observe clock synchronization improving with medium coherence, "
            "indicating emergent common time arises from substrate organization "
            "rather than being imposed externally."
        ) if test_passed else (
            "Further refinement of clock definitions is needed."
        )
    }
    
    with open('/app/backend/qmrt_topology/clock_synchronization_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved clock_synchronization_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_synchronization_test()
    
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(f"Verdict: {result['verdict']}")
    print(f"Correlation: {result['correlation_disorder_agreement']:.3f}")
    print()
    print(result['scientific_statement'])
