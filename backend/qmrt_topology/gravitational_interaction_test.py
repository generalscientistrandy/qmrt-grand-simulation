#!/usr/bin/env python3
"""
QMRT Multi-Pulse Gravitational Interaction Test
================================================

THE CRITICAL TEST: Do energy concentrations interact gravitationally?

If two wave pulses:
- Attract each other → gravitational analog
- Lens each other → curved geodesics from matter
- Merge into wells → gravitational collapse analog

This would be the first demonstration of:
  Matter affecting other matter's motion through geometry

The chain:
  Pulse A → creates c_eff well → Pulse B bends toward it
  
This is analogous to:
  Mass A → curves spacetime → Mass B follows geodesic toward A
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter


def simulate_two_pulse_interaction(size: int = 120, n_steps: int = 600,
                                   coupling: float = 0.5,
                                   separation: float = 40) -> dict:
    """
    Simulate two wave pulses with backreaction and track their interaction.
    
    Key observables:
    1. Do pulses attract/repel?
    2. Do pulses lens each other?
    3. Do pulses merge?
    """
    c0 = 2.0
    
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    # Two pulses separated horizontally
    center1 = np.array([size // 2 - separation // 2, size // 2])
    center2 = np.array([size // 2 + separation // 2, size // 2])
    
    packet_width = 4.0
    
    for i in range(size):
        for j in range(size):
            r1 = np.sqrt((i - center1[0])**2 + (j - center1[1])**2)
            r2 = np.sqrt((i - center2[0])**2 + (j - center2[1])**2)
            
            # Initialize both pulses
            if r1 < 3 * packet_width:
                velocity[i, j] += 5.0 * np.exp(-r1**2 / (2 * packet_width**2))
            if r2 < 3 * packet_width:
                velocity[i, j] += 5.0 * np.exp(-r2**2 / (2 * packet_width**2))
    
    dt = 0.03
    damping = 0.003
    
    snapshots = []
    pulse_positions = []  # Track pulse centers
    separation_history = []
    
    for t in range(n_steps):
        # Energy density
        energy_density = 0.5 * (field**2 + velocity**2)
        
        # Normalize
        rho_max = np.max(energy_density) + 1e-10
        rho_normalized = energy_density / rho_max
        
        # Backreaction
        c_eff = c0 * (1 - coupling * rho_normalized)
        c_eff = np.clip(c_eff, 0.3, c0)
        c_eff = gaussian_filter(c_eff, sigma=1.0)
        
        # Wave equation
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        # Track pulse positions (find two peaks)
        if t % 10 == 0:
            amp = np.abs(field) + np.abs(velocity)
            
            # Find the two highest peaks
            # Mask out the center temporarily
            left_half = amp[:size//2, :]
            right_half = amp[size//2:, :]
            
            if np.max(left_half) > 0.1 and np.max(right_half) > 0.1:
                left_peak = np.unravel_index(np.argmax(left_half), left_half.shape)
                right_peak = np.unravel_index(np.argmax(right_half), right_half.shape)
                right_peak = (right_peak[0] + size//2, right_peak[1])
                
                sep = np.sqrt((right_peak[0] - left_peak[0])**2 + 
                             (right_peak[1] - left_peak[1])**2)
                
                pulse_positions.append({
                    't': t * dt,
                    'left': left_peak,
                    'right': right_peak,
                    'separation': sep,
                })
                separation_history.append(sep)
            
            if t % 50 == 0:
                snapshots.append({
                    't': t * dt,
                    'field': field.copy(),
                    'energy_density': energy_density.copy(),
                    'c_eff': c_eff.copy(),
                })
    
    return {
        'snapshots': snapshots,
        'pulse_positions': pulse_positions,
        'separation_history': separation_history,
        'initial_separation': separation,
        'coupling': coupling,
    }


def analyze_interaction(result: dict) -> dict:
    """
    Analyze the interaction between pulses.
    """
    sep_history = result['separation_history']
    initial_sep = result['initial_separation']
    
    if len(sep_history) < 5:
        return {'verdict': 'INSUFFICIENT DATA'}
    
    # Check if separation decreases (attraction)
    initial_mean = np.mean(sep_history[:5])
    final_mean = np.mean(sep_history[-5:])
    
    separation_change = final_mean - initial_mean
    
    # Fit linear trend
    times = np.arange(len(sep_history))
    if len(times) > 2:
        trend = np.polyfit(times, sep_history, 1)[0]
    else:
        trend = 0
    
    if trend < -0.1:
        behavior = "ATTRACTION (separation decreasing)"
    elif trend > 0.1:
        behavior = "REPULSION (separation increasing)"
    else:
        behavior = "NEUTRAL (no clear trend)"
    
    return {
        'initial_separation': float(initial_mean),
        'final_separation': float(final_mean),
        'separation_change': float(separation_change),
        'trend': float(trend),
        'behavior': behavior,
    }


def run_gravitational_interaction_test():
    """
    Full gravitational interaction test.
    """
    print("=" * 70)
    print("MULTI-PULSE GRAVITATIONAL INTERACTION TEST")
    print("=" * 70)
    print("Question: Do energy concentrations attract each other?")
    print()
    print("Setup: Two wave pulses with backreaction coupling")
    print("Expected (gravity analog): Pulses attract, lensing occurs")
    print()
    
    np.random.seed(42)
    
    size = 120
    
    # Test with different couplings
    couplings = [0.0, 0.4, 0.7]
    results = {}
    
    for α in couplings:
        print(f"\nRunning with coupling α = {α}...")
        result = simulate_two_pulse_interaction(
            size=size, n_steps=600, coupling=α, separation=50
        )
        analysis = analyze_interaction(result)
        result['analysis'] = analysis
        results[α] = result
        
        print(f"  Initial separation: {analysis.get('initial_separation', 'N/A'):.1f}")
        print(f"  Final separation: {analysis.get('final_separation', 'N/A'):.1f}")
        print(f"  Trend: {analysis.get('trend', 0):.3f}")
        print(f"  Behavior: {analysis.get('behavior', 'N/A')}")
    
    # Determine verdict
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Check if higher coupling leads to more attraction
    trends = [results[α]['analysis'].get('trend', 0) for α in couplings]
    
    if trends[-1] < trends[0] - 0.1:
        overall_verdict = "GRAVITATIONAL ATTRACTION DEMONSTRATED"
        print(">>> Higher coupling → more attraction")
        print(f">>> Trend at α=0: {trends[0]:.3f}")
        print(f">>> Trend at α={couplings[-1]}: {trends[-1]:.3f}")
    elif any(t < -0.1 for t in trends):
        overall_verdict = "PARTIAL ATTRACTION OBSERVED"
        print(">>> Some attraction observed")
    else:
        overall_verdict = "NO CLEAR ATTRACTION"
        print(">>> No gravitational-like attraction observed")
    
    print(f"\n>>> VERDICT: {overall_verdict}")
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 15))
    
    # Row 1-3: Energy density evolution for each coupling
    for c_idx, α in enumerate(couplings):
        result = results[α]
        snaps = result['snapshots']
        
        for s_idx, snap in enumerate(snaps[:4]):
            ax = fig.add_subplot(4, 4, c_idx * 4 + s_idx + 1)
            
            energy = snap['energy_density']
            im = ax.imshow(energy.T, origin='lower', cmap='hot',
                          extent=[0, size, 0, size])
            
            if s_idx == 0:
                ax.set_ylabel(f'α = {α}')
            
            ax.set_title(f't = {snap["t"]:.2f}')
            ax.set_xticks([])
            ax.set_yticks([])
    
    # Row 4: Analysis plots
    ax = fig.add_subplot(4, 4, 13)
    for α in couplings:
        sep_history = results[α]['separation_history']
        times = np.arange(len(sep_history)) * 0.03 * 10
        ax.plot(times, sep_history, linewidth=2, label=f'α = {α}')
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Separation')
    ax.set_title('Pulse Separation Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = fig.add_subplot(4, 4, 14)
    trends = [results[α]['analysis'].get('trend', 0) for α in couplings]
    ax.bar([f'α={α}' for α in couplings], trends, 
           color=['gray', 'orange', 'red'])
    ax.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax.set_ylabel('Trend (slope)')
    ax.set_title('Separation Trend\n(Negative = Attraction)')
    
    # c_eff field showing wells
    ax = fig.add_subplot(4, 4, 15)
    high_coupling = max(couplings)
    snap = results[high_coupling]['snapshots'][len(results[high_coupling]['snapshots'])//2]
    im = ax.imshow(snap['c_eff'].T, origin='lower', cmap='viridis_r',
                  extent=[0, size, 0, size])
    ax.set_title(f'c_eff field (α={high_coupling})\nDark = slow = gravitational well')
    plt.colorbar(im, ax=ax, label='c_eff')
    
    # Summary
    ax = fig.add_subplot(4, 4, 16)
    ax.axis('off')
    
    summary_text = f"""
GRAVITATIONAL INTERACTION TEST
==============================

Two pulses with backreaction coupling

Results:
"""
    for α in couplings:
        analysis = results[α]['analysis']
        summary_text += f"\nα = {α}:"
        summary_text += f"\n  Separation change: {analysis.get('separation_change', 0):+.1f}"
        summary_text += f"\n  Trend: {analysis.get('trend', 0):.3f}"
        summary_text += f"\n  {analysis.get('behavior', 'N/A')}"
    
    summary_text += f"""

VERDICT: {overall_verdict}

Interpretation:
Energy concentrations create "gravitational
wells" (low c_eff regions). Other energy
follows geodesics toward these wells,
producing attraction-like behavior.
"""
    
    ax.text(0.1, 0.95, summary_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.suptitle(f'GRAVITATIONAL INTERACTION: {overall_verdict}', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/gravitational_interaction.png', dpi=150,
               bbox_inches='tight')
    print("\nSaved gravitational_interaction.png")
    
    # Save results
    import json
    summary = {
        'verdict': overall_verdict,
        'results': {
            str(α): {
                'trend': float(results[α]['analysis'].get('trend', 0)),
                'separation_change': float(results[α]['analysis'].get('separation_change', 0)),
                'behavior': results[α]['analysis'].get('behavior', 'N/A'),
            }
            for α in couplings
        }
    }
    
    with open('/app/backend/qmrt_topology/gravitational_interaction_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved gravitational_interaction_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_gravitational_interaction_test()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Verdict: {result['verdict']}")
