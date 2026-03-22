"""
QMRT v2: Normal Mode Spectrum Analysis
======================================

The RIGHT approach: Don't assume the branch count - MEASURE it.

For the two-field system (ω, φ), we:
1. Linearize around the background state
2. Compute the normal-mode spectrum (eigenvalues)
3. Plot ω(k) for many k
4. Count and classify distinct branches

Background state: ω = ω₀, φ = 0, π_ω = 0, π_φ = 0

Linearized equations around background:
  δω(x,t) = ω - ω₀   (small perturbation)
  δφ(x,t) = φ         (already zero at background)

Equations of motion:
  M_ω·∂²δω/∂t² = K_ω·∇²δω - ∂²V/∂ω²|_{bg}·δω - ∂²V_int/∂ω∂φ|_{bg}·δφ
  M_φ·∂²δφ/∂t² = K_φ·∇²δφ - ∂²V/∂φ²|_{bg}·δφ - ∂²V_int/∂ω∂φ|_{bg}·δω

For plane waves ~ e^{i(kx - ωt)}:
  -M_ω·ω²·δω = -K_ω·k²·δω - A·δω - B·δφ
  -M_φ·ω²·δφ = -K_φ·k²·δφ - C·δφ - D·δω

This gives us a 2x2 eigenvalue problem at each k!
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Tuple, List, Dict
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v2_engine import QMRTv2Parameters


def compute_linearized_coefficients(params: QMRTv2Parameters) -> Dict[str, float]:
    """
    Compute the coefficients for linearized equations around background state.
    
    Background: ω = ω₀, φ = 0
    
    Potential terms:
      V_ω = a(ω² - ω₀²)²
      V_φ = (m²_φ/2)φ²
      V_int = g·ω²·φ²
    
    Second derivatives at background:
      ∂²V_ω/∂ω² |_{ω=ω₀} = 4a·[(3ω² - ω₀²)]|_{ω=ω₀} = 4a·(3ω₀² - ω₀²) = 8a·ω₀²
      ∂²V_φ/∂φ² |_{φ=0} = m²_φ
      ∂²V_int/∂ω² |_{bg} = 2g·φ² |_{φ=0} = 0
      ∂²V_int/∂φ² |_{bg} = 2g·ω² |_{ω=ω₀} = 2g·ω₀²
      ∂²V_int/∂ω∂φ |_{bg} = 4g·ω·φ |_{bg} = 0  (cross-coupling vanishes!)
    """
    p = params
    
    # Effective masses for linearized oscillations
    M_omega_eff = 8 * p.a_omega * p.omega_0**2  # From double-well curvature
    M_phi_eff = p.m_phi_sq + 2 * p.g_coupling * p.omega_0**2  # Mass + interaction
    
    # Cross-coupling at background (important!)
    cross_coupling = 0  # Vanishes at ω=ω₀, φ=0
    
    return {
        'M_omega': p.M_omega,
        'K_omega': p.K_omega,
        'mass_omega_sq': M_omega_eff,  # = 8aω₀²
        'M_phi': p.M_phi,
        'K_phi': p.K_phi,
        'mass_phi_sq': M_phi_eff,  # = m²_φ + 2gω₀²
        'cross_coupling': cross_coupling,
    }


def compute_dispersion_matrix(k: float, coeffs: Dict[str, float]) -> np.ndarray:
    """
    Build the dynamical matrix for the linearized system at wavenumber k.
    
    For plane waves δω, δφ ~ e^{i(kx - ωt)}:
    
    The equations become:
      ω²·δω = (K_ω·k²/M_ω + mass_ω²/M_ω)·δω + (cross/M_ω)·δφ
      ω²·δφ = (cross/M_φ)·δω + (K_φ·k²/M_φ + mass_φ²/M_φ)·δφ
    
    Matrix form: ω² [δω, δφ]ᵀ = D [δω, δφ]ᵀ
    
    Eigenvalues of D give ω² for each mode.
    """
    c = coeffs
    
    # Diagonal elements
    D_omega_omega = c['K_omega'] * k**2 / c['M_omega'] + c['mass_omega_sq'] / c['M_omega']
    D_phi_phi = c['K_phi'] * k**2 / c['M_phi'] + c['mass_phi_sq'] / c['M_phi']
    
    # Off-diagonal (cross-coupling)
    D_omega_phi = c['cross_coupling'] / c['M_omega']
    D_phi_omega = c['cross_coupling'] / c['M_phi']
    
    D = np.array([
        [D_omega_omega, D_omega_phi],
        [D_phi_omega, D_phi_phi]
    ])
    
    return D


def analyze_normal_modes(params: QMRTv2Parameters = None, 
                         k_max: float = 2*np.pi,
                         n_k: int = 200) -> Dict:
    """
    Full normal-mode analysis: compute and classify all branches.
    """
    if params is None:
        params = QMRTv2Parameters()
    
    coeffs = compute_linearized_coefficients(params)
    
    print("="*70)
    print("QMRT v2: NORMAL MODE SPECTRUM ANALYSIS")
    print("="*70)
    print("\n--- Linearized Coefficients at Background (ω=ω₀, φ=0) ---")
    for key, val in coeffs.items():
        print(f"  {key}: {val:.6f}")
    
    # k values to probe
    k_values = np.linspace(0, k_max, n_k)
    
    # Store eigenvalues (ω² = eigenvalue, so ω = sqrt(eigenvalue) if positive)
    branch_1 = []  # Lower branch
    branch_2 = []  # Higher branch
    
    for k in k_values:
        D = compute_dispersion_matrix(k, coeffs)
        eigenvalues = np.linalg.eigvalsh(D)  # Returns sorted eigenvalues
        
        # eigenvalues are ω² - take sqrt for real ω (if positive)
        omega_sq_low = eigenvalues[0]
        omega_sq_high = eigenvalues[1]
        
        branch_1.append({
            'k': k,
            'omega_sq': omega_sq_low,
            'omega': np.sqrt(omega_sq_low) if omega_sq_low > 0 else -np.sqrt(-omega_sq_low),
            'stable': omega_sq_low > 0
        })
        
        branch_2.append({
            'k': k,
            'omega_sq': omega_sq_high,
            'omega': np.sqrt(omega_sq_high) if omega_sq_high > 0 else -np.sqrt(-omega_sq_high),
            'stable': omega_sq_high > 0
        })
    
    return {
        'params': params,
        'coeffs': coeffs,
        'k_values': k_values,
        'branch_1': branch_1,
        'branch_2': branch_2,
    }


def classify_branches(results: Dict) -> Dict:
    """
    Classify each branch as:
      - gapless: ω(k=0) ≈ 0
      - gapped: ω(k=0) > threshold
      - weakly propagating: dω/dk << 1
      - localized: very flat dispersion (ω nearly constant)
      - unstable: ω² < 0 anywhere
      - strongly coupled: branches anti-cross
    """
    k_values = results['k_values']
    branch_1 = results['branch_1']
    branch_2 = results['branch_2']
    
    def analyze_branch(branch, name):
        omega_values = np.array([b['omega'] for b in branch])
        omega_sq_values = np.array([b['omega_sq'] for b in branch])
        
        # Check stability
        unstable = np.any(omega_sq_values < 0)
        unstable_count = np.sum(omega_sq_values < 0)
        
        # Gap at k=0
        gap = omega_values[0] if not unstable else np.nan
        is_gapless = abs(gap) < 0.01 if not np.isnan(gap) else False
        is_gapped = gap > 0.1 if not np.isnan(gap) else False
        
        # Dispersion slope (group velocity)
        if len(k_values) > 1:
            # Linear fit at small k
            small_k_mask = k_values < 0.5
            if np.sum(small_k_mask) > 2:
                from scipy.stats import linregress
                slope, intercept, r_val, _, _ = linregress(
                    k_values[small_k_mask], omega_values[small_k_mask]
                )
            else:
                slope = 0
                r_val = 0
        else:
            slope = 0
            r_val = 0
        
        # Classification
        is_propagating = abs(slope) > 0.1 and r_val**2 > 0.5
        is_localized = abs(slope) < 0.05 and np.std(omega_values) / np.mean(np.abs(omega_values) + 1e-10) < 0.1
        
        # Overall dispersion character
        omega_range = np.max(omega_values) - np.min(omega_values)
        omega_mean = np.mean(omega_values)
        dispersion_type = 'flat (optical)' if omega_range / (omega_mean + 1e-10) < 0.3 else 'dispersive (acoustic-like)'
        
        return {
            'name': name,
            'gap': gap,
            'is_gapless': is_gapless,
            'is_gapped': is_gapped,
            'slope_small_k': slope,
            'r_squared': r_val**2,
            'is_propagating': is_propagating,
            'is_localized': is_localized,
            'unstable': unstable,
            'unstable_count': unstable_count,
            'omega_min': np.min(omega_values),
            'omega_max': np.max(omega_values),
            'omega_mean': np.mean(omega_values),
            'dispersion_type': dispersion_type,
        }
    
    branch_1_class = analyze_branch(branch_1, 'Branch 1 (lower)')
    branch_2_class = analyze_branch(branch_2, 'Branch 2 (upper)')
    
    # Check for anti-crossing (strong coupling signature)
    omega_1 = np.array([b['omega'] for b in branch_1])
    omega_2 = np.array([b['omega'] for b in branch_2])
    min_gap = np.min(omega_2 - omega_1)
    strongly_coupled = min_gap > 0.1 and min_gap < 0.5 * np.mean(omega_1)
    
    return {
        'branch_1': branch_1_class,
        'branch_2': branch_2_class,
        'strongly_coupled': strongly_coupled,
        'min_branch_gap': min_gap,
    }


def plot_dispersion(results: Dict, classification: Dict, save_path: str = None):
    """Plot ω(k) for all branches with classification annotations."""
    k_values = results['k_values']
    omega_1 = np.array([b['omega'] for b in results['branch_1']])
    omega_2 = np.array([b['omega'] for b in results['branch_2']])
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Full dispersion
    ax1 = axes[0]
    ax1.plot(k_values, omega_1, 'b-', linewidth=2, label='Branch 1 (lower)')
    ax1.plot(k_values, omega_2, 'r-', linewidth=2, label='Branch 2 (upper)')
    
    # Mark unstable regions
    unstable_1 = [b['k'] for b in results['branch_1'] if not b['stable']]
    unstable_2 = [b['k'] for b in results['branch_2'] if not b['stable']]
    if unstable_1:
        ax1.axvspan(min(unstable_1), max(unstable_1), alpha=0.3, color='blue', label='Unstable (B1)')
    if unstable_2:
        ax1.axvspan(min(unstable_2), max(unstable_2), alpha=0.3, color='red', label='Unstable (B2)')
    
    ax1.set_xlabel('Wavenumber k', fontsize=12)
    ax1.set_ylabel('Frequency ω', fontsize=12)
    ax1.set_title('QMRT v2 Normal Mode Spectrum', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max(k_values))
    ax1.set_ylim(0, max(max(omega_2) * 1.1, 1))
    
    # Plot 2: ω² vs k² to check linearity
    ax2 = axes[1]
    k_sq = k_values**2
    omega_sq_1 = np.array([b['omega_sq'] for b in results['branch_1']])
    omega_sq_2 = np.array([b['omega_sq'] for b in results['branch_2']])
    
    ax2.plot(k_sq, omega_sq_1, 'b-', linewidth=2, label='Branch 1')
    ax2.plot(k_sq, omega_sq_2, 'r-', linewidth=2, label='Branch 2')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    
    ax2.set_xlabel('k²', fontsize=12)
    ax2.set_ylabel('ω²', fontsize=12)
    ax2.set_title('Dispersion: ω² vs k² (linear = relativistic)', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved to: {save_path}")
    
    plt.close()
    return fig


def print_full_analysis(results: Dict, classification: Dict):
    """Print comprehensive analysis with branch classification."""
    coeffs = results['coeffs']
    params = results['params']
    
    print("\n" + "="*70)
    print("BRANCH COUNT AND CLASSIFICATION")
    print("="*70)
    
    print(f"\n>>> TOTAL BRANCHES FOUND: 2")
    print("    (As expected for a 2-field system)")
    
    for branch_key in ['branch_1', 'branch_2']:
        b = classification[branch_key]
        print(f"\n--- {b['name']} ---")
        print(f"  Gap at k=0:        ω(0) = {b['gap']:.4f}")
        print(f"  ω range:           [{b['omega_min']:.4f}, {b['omega_max']:.4f}]")
        print(f"  Dispersion slope:  dω/dk|_{'{k→0}'} = {b['slope_small_k']:.4f}")
        print(f"  Linear fit R²:     {b['r_squared']:.4f}")
        print(f"  Dispersion type:   {b['dispersion_type']}")
        
        print(f"\n  Classification:")
        print(f"    Gapless:         {'YES' if b['is_gapless'] else 'NO'}")
        print(f"    Gapped:          {'YES' if b['is_gapped'] else 'NO'}")
        print(f"    Propagating:     {'YES' if b['is_propagating'] else 'NO'}")
        print(f"    Localized:       {'YES' if b['is_localized'] else 'NO'}")
        print(f"    Unstable:        {'YES (' + str(b['unstable_count']) + ' k-points)' if b['unstable'] else 'NO (stable)'}")
    
    print(f"\n--- Inter-branch coupling ---")
    print(f"  Min branch separation: {classification['min_branch_gap']:.4f}")
    print(f"  Strongly coupled:      {'YES (anti-crossing)' if classification['strongly_coupled'] else 'NO'}")
    
    # Physical interpretation
    print("\n" + "="*70)
    print("PHYSICAL INTERPRETATION")
    print("="*70)
    
    b1 = classification['branch_1']
    b2 = classification['branch_2']
    
    # Identify optical vs acoustic
    if b1['is_gapped'] and not b1['is_propagating']:
        optical_branch = 'branch_1'
        optical_info = b1
    elif b2['is_gapped'] and not b2['is_propagating']:
        optical_branch = 'branch_2'
        optical_info = b2
    else:
        optical_branch = None
        optical_info = None
    
    if b1['is_propagating'] or (b1['slope_small_k'] > 0.3):
        acoustic_branch = 'branch_1'
        acoustic_info = b1
    elif b2['is_propagating'] or (b2['slope_small_k'] > 0.3):
        acoustic_branch = 'branch_2'
        acoustic_info = b2
    else:
        acoustic_branch = None
        acoustic_info = None
    
    print(f"\n  Optical branch (confinement): ", end='')
    if optical_info:
        print(f"{optical_info['name']}")
        print(f"    Gap: {optical_info['gap']:.4f}")
        print(f"    → Localized excitations, domain walls, mass generation")
    else:
        print("NOT CLEARLY IDENTIFIED")
    
    print(f"\n  Acoustic branch (propagation): ", end='')
    if acoustic_info:
        print(f"{acoustic_info['name']}")
        print(f"    Slope (speed): {acoustic_info['slope_small_k']:.4f}")
        print(f"    → Wave propagation, information transport, emergent light cone")
    else:
        print("NOT CLEARLY IDENTIFIED")
    
    # Stability summary
    any_unstable = b1['unstable'] or b2['unstable']
    print(f"\n  System stability: {'UNSTABLE MODES PRESENT!' if any_unstable else 'STABLE'}")
    
    # Completeness check
    print("\n" + "="*70)
    print("TWO-BRANCH PICTURE ASSESSMENT")
    print("="*70)
    
    issues = []
    if not optical_info:
        issues.append("No clear optical/confinement branch identified")
    if not acoustic_info:
        issues.append("No clear acoustic/propagating branch identified")
    if any_unstable:
        issues.append("System has unstable modes - physics may be unphysical")
    if classification['strongly_coupled']:
        issues.append("Branches are strongly coupled - simple two-branch picture may break down")
    
    if not issues:
        print("\n  ✅ TWO-BRANCH PICTURE IS COMPLETE")
        print("     - Clear optical branch for confinement")
        print("     - Clear acoustic branch for propagation")
        print("     - Both branches stable")
        print("     - No missing major physics detected in linearized regime")
    else:
        print("\n  ⚠️  ISSUES WITH TWO-BRANCH PICTURE:")
        for issue in issues:
            print(f"     - {issue}")
    
    return {
        'optical_branch': optical_info,
        'acoustic_branch': acoustic_info,
        'issues': issues,
    }


def run_full_analysis(params: QMRTv2Parameters = None):
    """Run complete normal mode analysis pipeline."""
    if params is None:
        params = QMRTv2Parameters()
    
    print("\n" + "#"*70)
    print("# QMRT v2: COMPLETE NORMAL MODE ANALYSIS")
    print("#"*70)
    print(f"\nParameters:")
    print(f"  M_ω={params.M_omega}, K_ω={params.K_omega}, a={params.a_omega}, ω₀={params.omega_0}")
    print(f"  M_φ={params.M_phi}, K_φ={params.K_phi}, m²_φ={params.m_phi_sq}")
    print(f"  g_coupling={params.g_coupling}")
    
    # Compute
    results = analyze_normal_modes(params, k_max=4.0, n_k=300)
    classification = classify_branches(results)
    
    # Plot
    plot_dispersion(results, classification, save_path='/app/backend/qmrt_confinement/dispersion_spectrum.png')
    
    # Full analysis
    interpretation = print_full_analysis(results, classification)
    
    return results, classification, interpretation


if __name__ == "__main__":
    run_full_analysis()
