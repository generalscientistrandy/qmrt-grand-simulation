#!/usr/bin/env python3
"""
O_STRUCTURE FUNCTIONAL FORM DERIVATION
======================================

GOAL: Define the exact functional relationship between ordering constraints
and spatial geometry:

    O_structure = f(S)

where S = spatial geometry measures (metric, c_eff, gradients)

PREVIOUS RESULT:
  ρ(O_structure, S) = -1.0  (perfect anti-correlation)

This tells us: Higher geometry → Fewer ordering possibilities
             (geometry compresses the causal graph)

FUNCTIONAL FORM CANDIDATES:
---------------------------

1. CAPACITY MODEL:
   O_structure = O_max / (1 + κ·S)
   
   Higher spatial structure S reduces the "capacity" for event orderings.
   Physical: geometry constrains which events can causally influence which.

2. EXPONENTIAL COMPRESSION:
   O_structure = O_max · exp(-λ_O · S)
   
   Geometry exponentially suppresses ordering freedom.
   Physical: strong geometry creates rigid causal structure.

3. POWER LAW:
   O_structure = O_max · S^(-α)
   
   Scale-invariant relationship.
   Physical: self-similar constraint propagation.

4. INFORMATION-THEORETIC:
   O_structure = log(N_orderings) = C - β·I_geom
   
   Ordering as log of possibilities, reduced by geometric information.
   Physical: geometry "uses up" ordering degrees of freedom.

MEASUREMENT STRATEGY:
--------------------
1. Sweep α (backreaction) from 0.1 to 0.9
2. For each α, measure:
   - S = spatial geometry score (from metric structure)
   - O_structure = graph-based ordering measure
3. Fit functional forms
4. Select best fit via R², AIC

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
from scipy.ndimage import gaussian_filter
import json

from dynamical_medium import DynamicalMediumSimulator


# ============================================================
# GEOMETRY MEASURES (S)
# ============================================================

def compute_spatial_geometry_S(sim: DynamicalMediumSimulator) -> dict:
    """
    Compute spatial geometry measures from the simulation state.
    
    S components:
      - S_metric: variation in effective metric (c_eff)
      - S_gradient: spatial inhomogeneity
      - S_structure: overall geometric structure score
    """
    c_eff = sim.compute_c_eff()
    tau = sim.tau
    
    # S_metric: Coefficient of variation of c_eff
    c_mean = np.mean(c_eff)
    c_std = np.std(c_eff)
    S_metric = c_std / (c_mean + 1e-10)
    
    # S_gradient: Mean gradient magnitude of c_eff
    grad_x = np.roll(c_eff, -1, axis=0) - c_eff
    grad_y = np.roll(c_eff, -1, axis=1) - c_eff
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    S_gradient = np.mean(grad_mag)
    
    # S_curvature: Laplacian of c_eff (local curvature proxy)
    laplacian = (np.roll(c_eff, 1, axis=0) + np.roll(c_eff, -1, axis=0) +
                 np.roll(c_eff, 1, axis=1) + np.roll(c_eff, -1, axis=1) - 4*c_eff)
    S_curvature = np.mean(np.abs(laplacian))
    
    # S_tau: Medium field deviation from equilibrium
    S_tau = np.std(tau)
    
    # Combined S_structure (normalized composite)
    S_structure = np.sqrt(S_metric**2 + S_gradient**2 + S_curvature**2)
    
    return {
        'S_metric': float(S_metric),
        'S_gradient': float(S_gradient),
        'S_curvature': float(S_curvature),
        'S_tau': float(S_tau),
        'S_structure': float(S_structure),
        'c_eff_mean': float(c_mean),
        'c_eff_std': float(c_std),
    }


# ============================================================
# ORDERING MEASURES (O_structure)
# ============================================================

def compute_ordering_structure(sim: DynamicalMediumSimulator, n_samples: int = 25) -> dict:
    """
    Compute O_structure from the causal graph properties.
    
    O_structure = measure of how many ordering possibilities exist
    
    Higher geometry → fewer orderings (compression)
    """
    c_eff = sim.compute_c_eff()
    size = sim.size
    
    # Sample random point pairs
    np.random.seed(42)
    points = np.random.randint(10, size-10, (n_samples, 2, 2))  # n_samples pairs of (x,y)
    
    # For each pair, compute causal reachability
    # A can causally reach B if: d(A,B) ≤ c_eff_path × Δt_max
    
    reachability_scores = []
    path_diversities = []
    
    for pair in points:
        A = pair[0]
        B = pair[1]
        
        distance = np.sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)
        
        # Average c_eff along the path
        n_path_points = max(int(distance), 2)
        path_x = np.linspace(A[0], B[0], n_path_points).astype(int)
        path_y = np.linspace(A[1], B[1], n_path_points).astype(int)
        path_x = np.clip(path_x, 0, size-1)
        path_y = np.clip(path_y, 0, size-1)
        
        c_eff_path = np.mean(c_eff[path_y, path_x])
        c_eff_var = np.var(c_eff[path_y, path_x])
        
        # Time needed for signal to traverse
        if c_eff_path > 0.1:
            time_needed = distance / c_eff_path
        else:
            time_needed = float('inf')
        
        # Reachability score: inverse of time (higher c_eff → easier reach)
        reachability = 1.0 / (time_needed + 1e-10)
        reachability_scores.append(reachability)
        
        # Path diversity: variation in c_eff along path
        path_diversities.append(c_eff_var)
    
    # O_structure metrics
    
    # O_reach: Mean reachability (how easily events can connect)
    O_reach = np.mean(reachability_scores)
    
    # O_diversity: How varied the reachability is (more = more ordering freedom)
    O_diversity = np.std(reachability_scores)
    
    # O_capacity: "Room" for different orderings
    # Higher geometry → more uniform c_eff → less diversity → fewer orderings
    O_capacity = O_diversity / (O_reach + 1e-10)
    
    # O_structure: Combined measure (will anti-correlate with S)
    # When S is high, paths are constrained → O_structure drops
    O_structure = O_capacity * np.mean(path_diversities)
    
    return {
        'O_reach': float(O_reach),
        'O_diversity': float(O_diversity),
        'O_capacity': float(O_capacity),
        'O_structure': float(O_structure),
        'mean_path_diversity': float(np.mean(path_diversities)),
    }


# ============================================================
# FUNCTIONAL FORM FITTING
# ============================================================

def capacity_model(S, O_max, kappa):
    """O_structure = O_max / (1 + κ·S)"""
    return O_max / (1 + kappa * S)

def exponential_model(S, O_max, lambda_O):
    """O_structure = O_max · exp(-λ·S)"""
    return O_max * np.exp(-lambda_O * S)

def power_law_model(S, O_max, alpha):
    """O_structure = O_max · S^(-α)"""
    return O_max * np.power(S + 0.01, -alpha)  # Add small constant to avoid S=0

def linear_model(S, a, b):
    """O_structure = a - b·S"""
    return a - b * S


def fit_functional_forms(S_values, O_values):
    """
    Fit all candidate functional forms and return best fit.
    """
    S = np.array(S_values)
    O = np.array(O_values)
    
    results = {}
    
    # 1. Capacity model
    try:
        popt, pcov = curve_fit(capacity_model, S, O, p0=[np.max(O), 1.0], maxfev=5000)
        O_pred = capacity_model(S, *popt)
        ss_res = np.sum((O - O_pred)**2)
        ss_tot = np.sum((O - np.mean(O))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        results['capacity'] = {
            'params': {'O_max': popt[0], 'kappa': popt[1]},
            'R2': r2,
            'residual': np.sqrt(np.mean((O - O_pred)**2)),
            'formula': f'O = {popt[0]:.4f} / (1 + {popt[1]:.4f}·S)',
        }
    except:
        results['capacity'] = {'R2': 0, 'error': 'fit failed'}
    
    # 2. Exponential model
    try:
        popt, pcov = curve_fit(exponential_model, S, O, p0=[np.max(O), 1.0], maxfev=5000)
        O_pred = exponential_model(S, *popt)
        ss_res = np.sum((O - O_pred)**2)
        ss_tot = np.sum((O - np.mean(O))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        results['exponential'] = {
            'params': {'O_max': popt[0], 'lambda': popt[1]},
            'R2': r2,
            'residual': np.sqrt(np.mean((O - O_pred)**2)),
            'formula': f'O = {popt[0]:.4f} · exp(-{popt[1]:.4f}·S)',
        }
    except:
        results['exponential'] = {'R2': 0, 'error': 'fit failed'}
    
    # 3. Power law
    try:
        popt, pcov = curve_fit(power_law_model, S, O, p0=[np.max(O)*0.1, 0.5], maxfev=5000)
        O_pred = power_law_model(S, *popt)
        ss_res = np.sum((O - O_pred)**2)
        ss_tot = np.sum((O - np.mean(O))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        results['power_law'] = {
            'params': {'O_max': popt[0], 'alpha': popt[1]},
            'R2': r2,
            'residual': np.sqrt(np.mean((O - O_pred)**2)),
            'formula': f'O = {popt[0]:.4f} · S^(-{popt[1]:.4f})',
        }
    except:
        results['power_law'] = {'R2': 0, 'error': 'fit failed'}
    
    # 4. Linear model
    try:
        popt, pcov = curve_fit(linear_model, S, O, p0=[np.max(O), 1.0], maxfev=5000)
        O_pred = linear_model(S, *popt)
        ss_res = np.sum((O - O_pred)**2)
        ss_tot = np.sum((O - np.mean(O))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        results['linear'] = {
            'params': {'a': popt[0], 'b': popt[1]},
            'R2': r2,
            'residual': np.sqrt(np.mean((O - O_pred)**2)),
            'formula': f'O = {popt[0]:.4f} - {popt[1]:.4f}·S',
        }
    except:
        results['linear'] = {'R2': 0, 'error': 'fit failed'}
    
    # Find best fit
    valid_results = {k: v for k, v in results.items() if 'R2' in v and v['R2'] > 0}
    if valid_results:
        best_model = max(valid_results.keys(), key=lambda k: valid_results[k]['R2'])
        results['best_model'] = best_model
        results['best_R2'] = valid_results[best_model]['R2']
        results['best_formula'] = valid_results[best_model]['formula']
    else:
        results['best_model'] = None
    
    return results


# ============================================================
# MAIN SWEEP
# ============================================================

def run_O_structure_functional_sweep():
    """
    Sweep α to derive O_structure = f(S) functional form.
    """
    print("=" * 70)
    print("O_STRUCTURE FUNCTIONAL FORM DERIVATION")
    print("=" * 70)
    print()
    print("Goal: Derive O_structure = f(S)")
    print("Method: Sweep backreaction α, measure (S, O_structure) pairs")
    print()
    
    # Parameter sweep
    alpha_values = np.linspace(0.1, 0.9, 12)
    
    S_data = []
    O_data = []
    full_data = []
    
    print("Running sweep...")
    print("-" * 50)
    
    for i, alpha in enumerate(alpha_values):
        # Create and equilibrate simulation
        sim = DynamicalMediumSimulator(
            size=80,
            beta=alpha,
            lambda_relax=0.5,
            D_medium=0.1,
            gamma_wave=0.01,
        )
        
        # Add pulse and evolve
        sim.add_pulse([40, 40], amplitude=3.0)
        
        for _ in range(200):
            sim.step()
        
        # Measure
        S_metrics = compute_spatial_geometry_S(sim)
        O_metrics = compute_ordering_structure(sim)
        
        S = S_metrics['S_structure']
        O = O_metrics['O_structure']
        
        S_data.append(S)
        O_data.append(O)
        
        full_data.append({
            'alpha': float(alpha),
            'S': S_metrics,
            'O': O_metrics,
        })
        
        print(f"  α = {alpha:.2f}: S = {S:.4f}, O_structure = {O:.6f}")
    
    print()
    
    # Correlation check
    rho, p_value = pearsonr(S_data, O_data)
    print(f"Correlation ρ(S, O_structure) = {rho:.4f} (p = {p_value:.2e})")
    
    if rho < -0.8:
        print("  → Strong anti-correlation confirmed (geometry compresses ordering)")
    
    print()
    
    # Fit functional forms
    print("-" * 50)
    print("FUNCTIONAL FORM FITTING")
    print("-" * 50)
    
    fit_results = fit_functional_forms(S_data, O_data)
    
    for model_name in ['capacity', 'exponential', 'power_law', 'linear']:
        result = fit_results.get(model_name, {})
        if 'R2' in result:
            print(f"\n{model_name.upper()} MODEL:")
            print(f"  Formula: {result.get('formula', 'N/A')}")
            print(f"  R² = {result['R2']:.4f}")
            print(f"  RMSE = {result.get('residual', 0):.6f}")
    
    print()
    print("=" * 70)
    print("BEST FIT RESULT")
    print("=" * 70)
    
    best = fit_results.get('best_model')
    if best:
        print(f"\nWINNER: {best.upper()} MODEL")
        print(f"Formula: {fit_results['best_formula']}")
        print(f"R² = {fit_results['best_R2']:.4f}")
    
    # Physical interpretation
    print()
    print("=" * 70)
    print("PHYSICAL INTERPRETATION")
    print("=" * 70)
    
    if best == 'capacity':
        print("""
CAPACITY MODEL: O_structure = O_max / (1 + κ·S)

Physical meaning:
  - Geometry acts as a "constraint" that limits ordering possibilities
  - When S → 0 (flat spacetime): O → O_max (maximal freedom)
  - When S → ∞ (strong geometry): O → 0 (fully constrained)
  - κ controls how quickly geometry saturates ordering

Thermodynamic analogy:
  - O_structure ↔ available microstates
  - S ↔ external constraint (like pressure or magnetic field)
  - Higher constraint → fewer states
""")
    elif best == 'exponential':
        print("""
EXPONENTIAL MODEL: O_structure = O_max · exp(-λ·S)

Physical meaning:
  - Each unit of geometry exponentially reduces ordering freedom
  - No saturation: geometry always has an effect
  - λ is the "compression rate"

Information-theoretic interpretation:
  - log(O_structure) = log(O_max) - λ·S
  - Geometry linearly reduces the log-space of orderings
  - This is entropy-like behavior
""")
    elif best == 'power_law':
        print("""
POWER LAW MODEL: O_structure = O_max · S^(-α)

Physical meaning:
  - Scale-invariant relationship
  - No characteristic scale in the geometry-ordering coupling
  - α is the "compression exponent"

Critical phenomena analogy:
  - Near a phase transition, power laws emerge
  - May indicate the spacetime emergence is a critical phenomenon
""")
    elif best == 'linear':
        print("""
LINEAR MODEL: O_structure = a - b·S

Physical meaning:
  - Simplest relationship: direct subtraction
  - Each unit of geometry removes a fixed amount of ordering
  - Only valid for S < a/b (otherwise O goes negative)

This is an approximation valid for small S.
""")
    
    return {
        'S_data': S_data,
        'O_data': O_data,
        'full_data': full_data,
        'correlation': {'rho': rho, 'p_value': p_value},
        'fit_results': fit_results,
    }


def generate_O_structure_figures(results):
    """Generate publication figures."""
    
    S = np.array(results['S_data'])
    O = np.array(results['O_data'])
    alpha_values = [d['alpha'] for d in results['full_data']]
    
    fig = plt.figure(figsize=(16, 10))
    
    # Panel 1: O vs S scatter with fit
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.scatter(S, O, c=alpha_values, cmap='viridis', s=80, edgecolors='k', linewidths=0.5)
    
    # Plot best fit line
    fit = results['fit_results']
    S_fit = np.linspace(S.min(), S.max(), 100)
    
    if fit.get('best_model') == 'capacity':
        p = fit['capacity']['params']
        O_fit = capacity_model(S_fit, p['O_max'], p['kappa'])
        ax1.plot(S_fit, O_fit, 'r-', linewidth=2, label=f"Capacity (R²={fit['capacity']['R2']:.3f})")
    elif fit.get('best_model') == 'exponential':
        p = fit['exponential']['params']
        O_fit = exponential_model(S_fit, p['O_max'], p['lambda'])
        ax1.plot(S_fit, O_fit, 'r-', linewidth=2, label=f"Exponential (R²={fit['exponential']['R2']:.3f})")
    elif fit.get('best_model') == 'linear':
        p = fit['linear']['params']
        O_fit = linear_model(S_fit, p['a'], p['b'])
        ax1.plot(S_fit, O_fit, 'r-', linewidth=2, label=f"Linear (R²={fit['linear']['R2']:.3f})")
    
    ax1.set_xlabel('S (Spatial Geometry)', fontsize=12)
    ax1.set_ylabel('O_structure', fontsize=12)
    ax1.set_title('O_structure = f(S)', fontsize=12, fontweight='bold')
    ax1.legend()
    cbar = plt.colorbar(ax1.collections[0], ax=ax1)
    cbar.set_label('α (backreaction)')
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: All model fits
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.scatter(S, O, c='gray', s=50, alpha=0.6, label='Data')
    
    colors = ['red', 'blue', 'green', 'orange']
    models = ['capacity', 'exponential', 'power_law', 'linear']
    
    for model, color in zip(models, colors):
        if model in fit and 'params' in fit[model]:
            p = fit[model]['params']
            if model == 'capacity':
                O_fit = capacity_model(S_fit, p['O_max'], p['kappa'])
            elif model == 'exponential':
                O_fit = exponential_model(S_fit, p['O_max'], p['lambda'])
            elif model == 'power_law':
                O_fit = power_law_model(S_fit, p['O_max'], p['alpha'])
            elif model == 'linear':
                O_fit = linear_model(S_fit, p['a'], p['b'])
            
            r2 = fit[model]['R2']
            ax2.plot(S_fit, O_fit, color=color, linewidth=1.5, 
                    label=f'{model} (R²={r2:.3f})', alpha=0.8)
    
    ax2.set_xlabel('S', fontsize=12)
    ax2.set_ylabel('O_structure', fontsize=12)
    ax2.set_title('Model Comparison', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: α vs S
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.plot(alpha_values, S, 'bo-', linewidth=2, markersize=8)
    ax3.set_xlabel('α (backreaction)', fontsize=12)
    ax3.set_ylabel('S (Spatial Geometry)', fontsize=12)
    ax3.set_title('Geometry vs Backreaction', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: α vs O_structure  
    ax4 = fig.add_subplot(2, 3, 4)
    ax4.plot(alpha_values, O, 'ro-', linewidth=2, markersize=8)
    ax4.set_xlabel('α (backreaction)', fontsize=12)
    ax4.set_ylabel('O_structure', fontsize=12)
    ax4.set_title('Ordering vs Backreaction', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Panel 5: R² comparison
    ax5 = fig.add_subplot(2, 3, 5)
    model_names = []
    r2_values = []
    for model in models:
        if model in fit and 'R2' in fit[model]:
            model_names.append(model)
            r2_values.append(fit[model]['R2'])
    
    colors_bar = ['green' if r == max(r2_values) else 'steelblue' for r in r2_values]
    ax5.barh(model_names, r2_values, color=colors_bar)
    ax5.set_xlabel('R²', fontsize=12)
    ax5.set_title('Model Fit Quality', fontsize=12, fontweight='bold')
    ax5.set_xlim(0, 1)
    for i, v in enumerate(r2_values):
        ax5.text(v + 0.02, i, f'{v:.3f}', va='center')
    
    # Panel 6: Summary text
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')
    
    rho = results['correlation']['rho']
    best = fit.get('best_model', 'N/A')
    best_r2 = fit.get('best_R2', 0)
    best_formula = fit.get('best_formula', 'N/A')
    
    summary = f"""
O_STRUCTURE FUNCTIONAL FORM
===========================

Correlation:
  ρ(S, O_structure) = {rho:.4f}
  → {'Anti-correlation: Geometry compresses ordering' if rho < -0.5 else 'Weak correlation'}

Best Fit Model: {best.upper() if best else 'N/A'}
  Formula: {best_formula}
  R² = {best_r2:.4f}

Physical Interpretation:
  O_structure = capacity for causal orderings
  S = strength of spatial geometry
  
  As geometry strengthens (higher α):
    → c_eff becomes more structured
    → Causal paths become more constrained  
    → Fewer valid event orderings possible
    → O_structure decreases

DERIVED RELATIONSHIP:
  {best_formula if best_formula != 'N/A' else '(fit failed)'}

This completes the O-layer characterization:
  • O_valid = binary gate (allows/forbids spacetime)
  • O_structure = f(S) (geometry constrains ordering)
"""
    
    ax6.text(0.02, 0.98, summary, transform=ax6.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    plt.suptitle('O_structure = f(S): Geometry-Ordering Functional Relationship', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/O_structure_functional.png', dpi=150, bbox_inches='tight')
    print("\nSaved: O_structure_functional.png")
    
    # Save JSON
    output = {
        'correlation': results['correlation'],
        'fit_results': {k: {kk: vv for kk, vv in v.items() if kk != 'error'} 
                       for k, v in fit.items() if isinstance(v, dict)},
        'best_model': best,
        'best_formula': best_formula,
        'best_R2': best_r2,
        'data_points': len(S),
        'alpha_range': [min(alpha_values), max(alpha_values)],
        'S_range': [float(S.min()), float(S.max())],
        'O_range': [float(O.min()), float(O.max())],
    }
    
    with open('/app/backend/qmrt_topology/O_structure_functional.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("Saved: O_structure_functional.json")


if __name__ == "__main__":
    results = run_O_structure_functional_sweep()
    generate_O_structure_figures(results)
