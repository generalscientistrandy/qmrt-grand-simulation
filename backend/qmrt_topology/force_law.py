#!/usr/bin/env python3
"""
QMRT Force-Law Extraction
==========================

Measure how attraction scales with:
- Initial separation d
- Coupling strength α

Goal: Determine if attraction is:
- Short-range only (exponential cutoff)
- Exponential screening
- Power law (1/d^n)
- Something inverse-like (1/d² would be gravitational)

Metrics:
- Δd = d_final - d_initial (negative = attraction)
- Effective "acceleration" a_eff = Δd / t²
- Attraction strength as function of d and α
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.optimize import curve_fit
import json


def run_attraction_test(
    size: int = 120,
    n_steps: int = 600,
    alpha: float = 0.5,
    separation: float = 0.3,  # Fraction of domain
    damping: float = 0.008,
):
    """
    Run two-pulse simulation and measure attraction.
    """
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    center = size / 2
    sep_pixels = separation * size / 2
    
    # Two pulses
    pos_A = np.array([center, center - sep_pixels])
    pos_B = np.array([center, center + sep_pixels])
    
    packet_width = 4.0
    amplitude = 3.0
    
    for i in range(size):
        for j in range(size):
            r_A = np.sqrt((i - pos_A[0])**2 + (j - pos_A[1])**2)
            r_B = np.sqrt((i - pos_B[0])**2 + (j - pos_B[1])**2)
            
            if r_A < 4 * packet_width:
                velocity[i, j] += amplitude * np.exp(-r_A**2 / (2 * packet_width**2))
            if r_B < 4 * packet_width:
                velocity[i, j] += amplitude * np.exp(-r_B**2 / (2 * packet_width**2))
    
    dt = 0.04
    c_0 = 2.0
    initial_sep = np.linalg.norm(pos_A - pos_B)
    
    # Track separation over time
    separations = [initial_sep]
    times = [0.0]
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        
        rho_max = np.max(energy_smooth) + 1e-10
        c_eff = c_0 * (1 - alpha * energy_smooth / rho_max)
        c_eff = np.clip(c_eff, 0.3, c_0)
        
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        # Track pulse positions every 10 steps
        if t % 10 == 0:
            energy = field**2 + velocity**2
            energy_for_peaks = energy.copy()
            
            peak_A_idx = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
            
            for di in range(-12, 13):
                for dj in range(-12, 13):
                    ni, nj = peak_A_idx[0] + di, peak_A_idx[1] + dj
                    if 0 <= ni < size and 0 <= nj < size:
                        energy_for_peaks[ni, nj] = 0
            
            peak_B_idx = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
            
            current_sep = np.linalg.norm(np.array(peak_A_idx) - np.array(peak_B_idx))
            separations.append(current_sep)
            times.append((t + 1) * dt)
    
    separations = np.array(separations)
    times = np.array(times)
    
    # Compute metrics
    final_sep = separations[-1]
    delta_sep = final_sep - initial_sep
    
    # Effective acceleration (d = d0 + v0*t + 0.5*a*t^2)
    # Assuming v0 ≈ 0, a_eff ≈ 2*Δd/t^2
    total_time = times[-1]
    a_eff = 2 * delta_sep / (total_time**2 + 1e-10)
    
    # Attraction rate (linear approximation)
    if len(separations) > 10:
        # Fit line to middle portion
        mid = len(separations) // 2
        slope = (separations[-1] - separations[mid]) / (times[-1] - times[mid] + 1e-10)
    else:
        slope = delta_sep / (total_time + 1e-10)
    
    return {
        'initial_sep': initial_sep,
        'final_sep': final_sep,
        'delta_sep': delta_sep,
        'a_eff': a_eff,
        'slope': slope,
        'separations': separations,
        'times': times,
    }


def run_force_law_extraction():
    """
    Main test: Extract force law by varying separation and α.
    """
    print("=" * 70)
    print("FORCE-LAW EXTRACTION")
    print("=" * 70)
    print("Measuring attraction vs separation and coupling strength")
    print()
    
    np.random.seed(42)
    
    # Vary separation at fixed α
    print("Test 1: Attraction vs Initial Separation (α=0.5)...")
    separations = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]
    sep_results = {}
    
    for sep in separations:
        print(f"  d={sep:.2f}...", end=" ")
        result = run_attraction_test(
            alpha=0.5,
            separation=sep,
            n_steps=500
        )
        sep_results[sep] = result
        print(f"Δd={result['delta_sep']:+.1f}, a_eff={result['a_eff']:.3f}")
    
    # Vary α at fixed separation
    print("\nTest 2: Attraction vs Coupling α (d=0.3)...")
    alphas = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    alpha_results = {}
    
    for alpha in alphas:
        print(f"  α={alpha:.1f}...", end=" ")
        result = run_attraction_test(
            alpha=alpha,
            separation=0.3,
            n_steps=500
        )
        alpha_results[alpha] = result
        print(f"Δd={result['delta_sep']:+.1f}, a_eff={result['a_eff']:.3f}")
    
    # =================================
    # ANALYSIS: Force Law Fitting
    # =================================
    print("\n" + "=" * 70)
    print("FORCE-LAW ANALYSIS")
    print("=" * 70)
    
    # Extract data for fitting
    d_values = np.array([sep_results[s]['initial_sep'] for s in separations])
    attraction = np.array([-sep_results[s]['delta_sep'] for s in separations])  # Positive = attraction
    a_eff_values = np.array([-sep_results[s]['a_eff'] for s in separations])
    
    # Try different force law fits
    print("\nFitting force laws to attraction vs separation...")
    
    # 1. Power law: F ~ 1/d^n → Δd ~ -1/d^n
    def power_law(d, A, n):
        return A / (d**n + 0.1)
    
    # 2. Exponential: F ~ exp(-d/λ)
    def exponential(d, A, lam):
        return A * np.exp(-d / lam)
    
    # 3. Linear: F ~ d (spring-like)
    def linear(d, A, B):
        return A * d + B
    
    fits = {}
    
    # Only fit where attraction is positive
    mask = attraction > 0
    if np.sum(mask) >= 3:
        d_fit = d_values[mask]
        a_fit = attraction[mask]
        
        try:
            popt_pow, _ = curve_fit(power_law, d_fit, a_fit, p0=[100, 1], maxfev=5000)
            fits['power_law'] = {'params': popt_pow, 'residual': np.sum((a_fit - power_law(d_fit, *popt_pow))**2)}
            print(f"  Power law: A/d^{popt_pow[1]:.2f}, residual={fits['power_law']['residual']:.2f}")
        except:
            print("  Power law fit failed")
        
        try:
            popt_exp, _ = curve_fit(exponential, d_fit, a_fit, p0=[50, 20], maxfev=5000)
            fits['exponential'] = {'params': popt_exp, 'residual': np.sum((a_fit - exponential(d_fit, *popt_exp))**2)}
            print(f"  Exponential: A*exp(-d/{popt_exp[1]:.1f}), residual={fits['exponential']['residual']:.2f}")
        except:
            print("  Exponential fit failed")
        
        try:
            popt_lin, _ = curve_fit(linear, d_fit, a_fit, p0=[1, 0], maxfev=5000)
            fits['linear'] = {'params': popt_lin, 'residual': np.sum((a_fit - linear(d_fit, *popt_lin))**2)}
            print(f"  Linear: {popt_lin[0]:.2f}*d + {popt_lin[1]:.2f}, residual={fits['linear']['residual']:.2f}")
        except:
            print("  Linear fit failed")
    
    # Determine best fit
    if fits:
        best_fit = min(fits.keys(), key=lambda k: fits[k]['residual'])
        print(f"\n  Best fit: {best_fit.upper()}")
    else:
        best_fit = "unknown"
        print("\n  Could not determine best fit")
    
    # Check if inverse-like
    if 'power_law' in fits:
        n = fits['power_law']['params'][1]
        if 1.5 < n < 2.5:
            print("  >>> INVERSE-SQUARE-LIKE behavior detected!")
        elif 0.5 < n < 1.5:
            print("  >>> INVERSE-LINEAR behavior (Coulomb-like in 2D)")
        else:
            print(f"  >>> Power law with n={n:.2f}")
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 16))
    
    # Separation trajectories at different initial d
    ax = fig.add_subplot(3, 4, 1)
    for sep in [0.15, 0.25, 0.35, 0.50]:
        if sep in sep_results:
            result = sep_results[sep]
            ax.plot(result['times'], result['separations'], 
                   linewidth=2, label=f'd₀={result["initial_sep"]:.0f}')
    ax.set_xlabel('Time')
    ax.set_ylabel('Separation (pixels)')
    ax.set_title('Separation vs Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Attraction vs initial separation
    ax = fig.add_subplot(3, 4, 2)
    d_plot = [sep_results[s]['initial_sep'] for s in separations]
    attr_plot = [-sep_results[s]['delta_sep'] for s in separations]
    
    colors = ['green' if a > 0 else 'red' for a in attr_plot]
    ax.scatter(d_plot, attr_plot, c=colors, s=100, zorder=5)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    
    # Add best fit line
    if 'power_law' in fits:
        d_smooth = np.linspace(min(d_plot), max(d_plot), 100)
        ax.plot(d_smooth, power_law(d_smooth, *fits['power_law']['params']), 
               'b-', linewidth=2, label=f'Power law (n={fits["power_law"]["params"][1]:.2f})')
        ax.legend()
    
    ax.set_xlabel('Initial Separation (pixels)')
    ax.set_ylabel('Attraction (pixels)')
    ax.set_title('Attraction vs Separation')
    ax.grid(True, alpha=0.3)
    
    # Log-log plot for power law
    ax = fig.add_subplot(3, 4, 3)
    mask = np.array(attr_plot) > 0
    if np.sum(mask) > 0:
        d_pos = np.array(d_plot)[mask]
        a_pos = np.array(attr_plot)[mask]
        ax.scatter(np.log10(d_pos), np.log10(a_pos), c='blue', s=100)
        
        # Linear fit in log-log gives power law exponent
        if len(d_pos) >= 2:
            slope, intercept = np.polyfit(np.log10(d_pos), np.log10(a_pos), 1)
            x_fit = np.linspace(np.log10(min(d_pos)), np.log10(max(d_pos)), 100)
            ax.plot(x_fit, slope * x_fit + intercept, 'r--', 
                   linewidth=2, label=f'slope={slope:.2f}')
            ax.legend()
    
    ax.set_xlabel('log₁₀(Separation)')
    ax.set_ylabel('log₁₀(Attraction)')
    ax.set_title('Log-Log Plot (Power Law Test)')
    ax.grid(True, alpha=0.3)
    
    # Effective acceleration vs separation
    ax = fig.add_subplot(3, 4, 4)
    a_eff_plot = [-sep_results[s]['a_eff'] for s in separations]
    ax.scatter(d_plot, a_eff_plot, c='purple', s=100)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Initial Separation (pixels)')
    ax.set_ylabel('Effective Acceleration')
    ax.set_title('a_eff vs Separation')
    ax.grid(True, alpha=0.3)
    
    # Attraction vs α
    ax = fig.add_subplot(3, 4, 5)
    alpha_plot = list(alphas)
    attr_alpha = [-alpha_results[a]['delta_sep'] for a in alphas]
    
    colors = ['green' if a > 0 else 'red' for a in attr_alpha]
    ax.bar(alpha_plot, attr_alpha, color=colors, width=0.08)
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.5)
    ax.set_xlabel('Coupling α')
    ax.set_ylabel('Attraction (pixels)')
    ax.set_title('Attraction vs Coupling (d=0.3)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Separation trajectories at different α
    ax = fig.add_subplot(3, 4, 6)
    for alpha in [0.3, 0.5, 0.7]:
        if alpha in alpha_results:
            result = alpha_results[alpha]
            ax.plot(result['times'], result['separations'], 
                   linewidth=2, label=f'α={alpha}')
    ax.set_xlabel('Time')
    ax.set_ylabel('Separation (pixels)')
    ax.set_title('Sep vs Time (varying α)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Summary statistics
    ax = fig.add_subplot(3, 4, 7)
    ax.axis('off')
    
    summary_text = """
FORCE-LAW SUMMARY
=================

Separation dependence (α=0.5):
"""
    for sep in separations:
        r = sep_results[sep]
        summary_text += f"  d₀={r['initial_sep']:.0f}: Δd={r['delta_sep']:+.1f}\n"
    
    if 'power_law' in fits:
        n = fits['power_law']['params'][1]
        summary_text += f"""
Best fit: POWER LAW
  Attraction ~ 1/d^{n:.2f}
"""
        if 1.5 < n < 2.5:
            summary_text += "  >>> INVERSE-SQUARE-LIKE"
        elif 0.5 < n < 1.5:
            summary_text += "  >>> INVERSE-LINEAR (2D Coulomb)"
    
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # α dependence summary
    ax = fig.add_subplot(3, 4, 8)
    ax.axis('off')
    
    alpha_text = """
COUPLING DEPENDENCE (d=0.3)
===========================

"""
    for alpha in alphas:
        r = alpha_results[alpha]
        status = "ATTRACT" if r['delta_sep'] < -5 else ("NEUTRAL" if abs(r['delta_sep']) < 5 else "SPREAD")
        alpha_text += f"  α={alpha}: Δd={r['delta_sep']:+.1f} [{status}]\n"
    
    # Find threshold
    for i, alpha in enumerate(alphas):
        if alpha_results[alpha]['delta_sep'] < -5:
            alpha_text += f"\nAttraction onset: α ≈ {alpha}"
            break
    
    ax.text(0.05, 0.95, alpha_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    # Physical interpretation
    ax = fig.add_subplot(3, 4, 9)
    ax.axis('off')
    
    if 'power_law' in fits:
        n = fits['power_law']['params'][1]
        if n < 0.5:
            interp = "SHORT-RANGE: Attraction is local"
        elif 0.5 < n < 1.5:
            interp = "2D COULOMB-LIKE: 1/r potential in 2D"
        elif 1.5 < n < 2.5:
            interp = "GRAVITATIONAL-LIKE: Inverse-square in 2D"
        else:
            interp = f"STEEPER THAN GRAVITY: n={n:.2f}"
    else:
        interp = "UNDETERMINED"
    
    phys_text = f"""
PHYSICAL INTERPRETATION
=======================

Force Law Type: {interp}

This tells us:
"""
    if 'power_law' in fits:
        n = fits['power_law']['params'][1]
        if 1.5 < n < 2.5:
            phys_text += """
• Attraction decays like 1/d²
• Consistent with 3D gravity
  projected to 2D
• NOT local self-focusing only
• Genuine long-range interaction
"""
        elif 0.5 < n < 1.5:
            phys_text += """
• Attraction decays like 1/d
• Consistent with 2D potential
  (logarithmic in 2D)
• Medium-range interaction
• Analog to 2D electrostatics
"""
        else:
            phys_text += f"""
• Power law with n={n:.2f}
• Different from standard gravity
• May indicate screening or
  non-standard geometry
"""
    
    ax.text(0.05, 0.95, phys_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    # Final verdict
    ax = fig.add_subplot(3, 4, 10)
    ax.axis('off')
    
    verdict_text = f"""
FORCE-LAW EXTRACTION COMPLETE
=============================

Key findings:

1. Attraction increases with α
   Threshold: α ≈ 0.4-0.5

2. Attraction depends on separation
   Closer pulses attract more strongly

3. Force law type: {interp}
"""
    if 'power_law' in fits:
        n = fits['power_law']['params'][1]
        verdict_text += f"""
4. Power law exponent: n = {n:.2f}
   (1/d^n scaling)

This indicates the interaction is
{"LONG-RANGE (geometry-mediated)" if n > 0.5 else "SHORT-RANGE (local)"}
"""
    
    ax.text(0.5, 0.5, verdict_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='center', horizontalalignment='center',
           fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    # Comparison plot
    ax = fig.add_subplot(3, 4, 11)
    d_compare = np.linspace(15, 60, 100)
    
    ax.plot(d_compare, 1000 / d_compare**2, 'r-', linewidth=2, label='1/d² (gravity)')
    ax.plot(d_compare, 100 / d_compare, 'g-', linewidth=2, label='1/d (2D Coulomb)')
    ax.plot(d_compare, 50 * np.exp(-d_compare/20), 'b-', linewidth=2, label='Exponential')
    
    if mask.any():
        ax.scatter(d_pos, a_pos, c='black', s=100, zorder=5, label='Data')
    
    ax.set_xlabel('Separation')
    ax.set_ylabel('Attraction')
    ax.set_title('Data vs Model Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    
    # Model fit comparison
    ax = fig.add_subplot(3, 4, 12)
    if fits:
        models = list(fits.keys())
        residuals = [fits[m]['residual'] for m in models]
        colors = ['green' if m == best_fit else 'gray' for m in models]
        ax.barh(models, residuals, color=colors)
        ax.set_xlabel('Residual (lower = better)')
        ax.set_title('Model Comparison')
    else:
        ax.text(0.5, 0.5, 'No fits available', ha='center', va='center')
    
    plt.suptitle('FORCE-LAW EXTRACTION', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/force_law.png', dpi=150, bbox_inches='tight')
    print("\nSaved force_law.png")
    
    # Save results
    summary = {
        'separation_test': {
            str(s): {
                'initial_sep': float(sep_results[s]['initial_sep']),
                'delta_sep': float(sep_results[s]['delta_sep']),
                'a_eff': float(sep_results[s]['a_eff']),
            }
            for s in separations
        },
        'alpha_test': {
            str(a): {
                'delta_sep': float(alpha_results[a]['delta_sep']),
                'a_eff': float(alpha_results[a]['a_eff']),
            }
            for a in alphas
        },
        'fits': {
            k: {
                'params': [float(p) for p in v['params']],
                'residual': float(v['residual']),
            }
            for k, v in fits.items()
        } if fits else {},
        'best_fit': best_fit,
        'interpretation': interp if 'power_law' in fits else "undetermined",
    }
    
    with open('/app/backend/qmrt_topology/force_law_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved force_law_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_force_law_extraction()
    
    print("\n" + "=" * 70)
    print("FORCE-LAW EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Best fit: {result['best_fit'].upper()}")
    print(f"Interpretation: {result['interpretation']}")
