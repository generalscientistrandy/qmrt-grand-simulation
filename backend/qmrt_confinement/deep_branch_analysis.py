"""
QMRT v2: Deep Branch Analysis
=============================

Key questions from the initial analysis:
1. Branch 1 is labeled "acoustic" but has a GAP (ω(0) = 0.458) - this is NOT gapless acoustic!
2. The ω² vs k² linearity needs checking for relativistic signature
3. Need to verify if the "propagating" branch is truly massless or has an effective mass

This script performs:
- Detailed analysis of each branch's character
- Dispersion relation fitting (ω² = c²k² + m²)
- Group velocity calculation
- Phase velocity calculation
- Comparison with Klein-Gordon vs acoustic limits
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v2_engine import QMRTv2Parameters


def compute_linearized_coefficients(params: QMRTv2Parameters):
    """Compute linearized coefficients at background."""
    p = params
    M_omega_eff = 8 * p.a_omega * p.omega_0**2
    M_phi_eff = p.m_phi_sq + 2 * p.g_coupling * p.omega_0**2
    
    return {
        'M_omega': p.M_omega, 'K_omega': p.K_omega, 'mass_omega_sq': M_omega_eff,
        'M_phi': p.M_phi, 'K_phi': p.K_phi, 'mass_phi_sq': M_phi_eff,
        'cross_coupling': 0,
    }


def compute_dispersion(k, coeffs):
    """Compute eigenfrequencies at wavenumber k."""
    c = coeffs
    D_11 = c['K_omega'] * k**2 / c['M_omega'] + c['mass_omega_sq'] / c['M_omega']
    D_22 = c['K_phi'] * k**2 / c['M_phi'] + c['mass_phi_sq'] / c['M_phi']
    D_12 = c['cross_coupling'] / c['M_omega']
    D_21 = c['cross_coupling'] / c['M_phi']
    
    D = np.array([[D_11, D_12], [D_21, D_22]])
    eigenvalues = np.linalg.eigvalsh(D)
    return np.sqrt(np.maximum(eigenvalues, 0))


def klein_gordon_dispersion(k, c, m):
    """Klein-Gordon: ω² = c²k² + m² → ω = sqrt(c²k² + m²)"""
    return np.sqrt(c**2 * k**2 + m**2)


def acoustic_dispersion(k, c):
    """Pure acoustic: ω = c·k"""
    return c * k


def analyze_branch_physics(k_values, omega_values, branch_name):
    """Detailed physics analysis of a single branch."""
    print(f"\n{'='*60}")
    print(f"DEEP ANALYSIS: {branch_name}")
    print(f"{'='*60}")
    
    omega_sq = omega_values**2
    k_sq = k_values**2
    
    # 1. Gap analysis
    gap = omega_values[0]
    is_gapped = gap > 0.01
    print(f"\n1. GAP ANALYSIS")
    print(f"   ω(k=0) = {gap:.6f}")
    print(f"   Gapped: {'YES' if is_gapped else 'NO (gapless)'}")
    
    # 2. Fit to Klein-Gordon: ω² = c²k² + m²
    print(f"\n2. KLEIN-GORDON FIT: ω² = c²k² + m²")
    
    # Linear regression on ω² vs k²
    slope, intercept, r_value, _, _ = linregress(k_sq, omega_sq)
    c_eff = np.sqrt(slope) if slope > 0 else 0
    m_eff = np.sqrt(intercept) if intercept > 0 else 0
    
    print(f"   Linear fit (ω² vs k²): slope={slope:.6f}, intercept={intercept:.6f}")
    print(f"   R² = {r_value**2:.6f}")
    print(f"   → Effective speed c = {c_eff:.6f}")
    print(f"   → Effective mass m = {m_eff:.6f}")
    
    # Calculate predicted ω² and residuals
    omega_sq_pred = slope * k_sq + intercept
    residuals = omega_sq - omega_sq_pred
    rms_residual = np.sqrt(np.mean(residuals**2))
    max_residual = np.max(np.abs(residuals))
    
    print(f"   RMS residual: {rms_residual:.6f}")
    print(f"   Max residual: {max_residual:.6f}")
    
    # 3. Test pure acoustic (gapless)
    print(f"\n3. PURE ACOUSTIC TEST: ω = c·k")
    try:
        popt, _ = curve_fit(acoustic_dispersion, k_values[1:], omega_values[1:])  # Skip k=0
        c_acoustic = popt[0]
        omega_acoustic = acoustic_dispersion(k_values, c_acoustic)
        residual_acoustic = np.sqrt(np.mean((omega_values - omega_acoustic)**2))
        print(f"   Best fit c = {c_acoustic:.6f}")
        print(f"   RMS residual: {residual_acoustic:.6f}")
        print(f"   → {'GOOD FIT' if residual_acoustic < 0.1 else 'POOR FIT'}")
    except:
        print("   → Fit failed (probably not acoustic)")
        residual_acoustic = float('inf')
    
    # 4. Group velocity
    print(f"\n4. GROUP VELOCITY: v_g = dω/dk")
    # Numerical derivative
    v_g = np.gradient(omega_values, k_values)
    print(f"   v_g at k=0:      {v_g[0]:.6f}")
    print(f"   v_g at k=1:      {v_g[np.argmin(np.abs(k_values - 1))]:.6f}")
    print(f"   v_g at k=2:      {v_g[np.argmin(np.abs(k_values - 2))]:.6f}")
    print(f"   v_g range:       [{np.min(v_g):.6f}, {np.max(v_g):.6f}]")
    
    # Phase velocity
    print(f"\n5. PHASE VELOCITY: v_p = ω/k")
    with np.errstate(divide='ignore', invalid='ignore'):
        v_p = omega_values / k_values
        v_p[0] = np.nan  # Undefined at k=0
    valid_vp = v_p[~np.isnan(v_p)]
    print(f"   v_p range:       [{np.min(valid_vp):.6f}, {np.max(valid_vp):.6f}]")
    
    # 6. Classification
    print(f"\n6. BRANCH CLASSIFICATION")
    
    kg_fit_quality = r_value**2
    
    if is_gapped:
        if kg_fit_quality > 0.99:
            classification = "MASSIVE KLEIN-GORDON"
            physics = "Relativistic massive particle (ω² = c²k² + m²)"
        else:
            classification = "GAPPED (NON-RELATIVISTIC)"
            physics = "Optical phonon / Higgs-like"
    else:
        if residual_acoustic < 0.1:
            classification = "ACOUSTIC (GAPLESS)"
            physics = "Sound wave / emergent photon"
        else:
            classification = "UNKNOWN"
            physics = "Does not match standard patterns"
    
    print(f"   → {classification}")
    print(f"   Physics: {physics}")
    
    return {
        'gap': gap,
        'is_gapped': is_gapped,
        'c_eff': c_eff,
        'm_eff': m_eff,
        'kg_fit_r2': r_value**2,
        'classification': classification,
        'v_g_at_0': v_g[0],
        'v_g_at_1': v_g[np.argmin(np.abs(k_values - 1))],
    }


def run_deep_analysis():
    """Run complete deep analysis of both branches."""
    params = QMRTv2Parameters()
    coeffs = compute_linearized_coefficients(params)
    
    print("#" * 70)
    print("# QMRT v2: DEEP BRANCH PHYSICS ANALYSIS")
    print("#" * 70)
    print(f"\nParameters:")
    print(f"  ω field: M={params.M_omega}, K={params.K_omega}, a={params.a_omega}, ω₀={params.omega_0}")
    print(f"  φ field: M={params.M_phi}, K={params.K_phi}, m²={params.m_phi_sq}")
    print(f"  Coupling: g={params.g_coupling}")
    
    print(f"\nTheoretical speeds:")
    print(f"  c_φ = √(K_φ/M_φ) = {np.sqrt(params.K_phi/params.M_phi):.6f}")
    print(f"  c_ω = √(K_ω/M_ω) = {np.sqrt(params.K_omega/params.M_omega):.6f}")
    
    print(f"\nTheoretical gaps (linearized):")
    print(f"  ω field gap: √(8aω₀²/M_ω) = {np.sqrt(8*params.a_omega*params.omega_0**2/params.M_omega):.6f}")
    effective_phi_mass_sq = params.m_phi_sq + 2*params.g_coupling*params.omega_0**2
    print(f"  φ field effective mass²: m²_eff = m²_φ + 2gω₀² = {effective_phi_mass_sq:.6f}")
    print(f"  φ field gap: √(m²_eff/M_φ) = {np.sqrt(effective_phi_mass_sq/params.M_phi):.6f}")
    
    # Compute dispersion
    k_values = np.linspace(0, 4.0, 500)
    omega_all = np.array([compute_dispersion(k, coeffs) for k in k_values])
    omega_1 = omega_all[:, 0]  # Lower branch
    omega_2 = omega_all[:, 1]  # Upper branch
    
    # Analyze each branch
    result_1 = analyze_branch_physics(k_values, omega_1, "BRANCH 1 (Lower)")
    result_2 = analyze_branch_physics(k_values, omega_2, "BRANCH 2 (Upper)")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: COMPLETE BRANCH STRUCTURE")
    print("=" * 70)
    
    print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│ Branch │ Gap ω(0) │ Speed c  │ Mass m │ Classification              │
├────────┼──────────┼──────────┼────────┼─────────────────────────────┤
│   1    │ {result_1['gap']:8.4f} │ {result_1['c_eff']:8.4f} │ {result_1['m_eff']:6.4f} │ {result_1['classification']:27} │
│   2    │ {result_2['gap']:8.4f} │ {result_2['c_eff']:8.4f} │ {result_2['m_eff']:6.4f} │ {result_2['classification']:27} │
└─────────────────────────────────────────────────────────────────────┘
""")
    
    # Critical physics assessment
    print("\n" + "=" * 70)
    print("CRITICAL PHYSICS ASSESSMENT")
    print("=" * 70)
    
    issues = []
    
    # Check if we have a TRUE acoustic mode
    if result_1['is_gapped'] and result_2['is_gapped']:
        issues.append("BOTH branches are gapped - NO true acoustic (gapless) mode exists!")
        issues.append("→ System has NO massless propagating field (no photon analog)")
        issues.append("→ Both modes are massive/optical")
    
    # Check Klein-Gordon fit quality
    if result_1['kg_fit_r2'] > 0.99:
        print(f"\n  Branch 1: Excellent Klein-Gordon fit (R²={result_1['kg_fit_r2']:.4f})")
        print(f"            This is a MASSIVE relativistic mode")
    
    if result_2['kg_fit_r2'] > 0.99:
        print(f"\n  Branch 2: Excellent Klein-Gordon fit (R²={result_2['kg_fit_r2']:.4f})")
        print(f"            This is a MASSIVE relativistic mode")
    
    if issues:
        print("\n  ⚠️  IMPORTANT FINDINGS:")
        for issue in issues:
            print(f"     {issue}")
    
    # The key question
    print("\n" + "=" * 70)
    print("KEY QUESTION: Is there emergent relativity?")
    print("=" * 70)
    
    lower_branch_kg = result_1['kg_fit_r2'] > 0.99
    
    if lower_branch_kg and result_1['c_eff'] > 0.1:
        print(f"""
  YES, BRANCH 1 exhibits massive Klein-Gordon dispersion:
    ω² = c²k² + m²
    
  With effective parameters:
    c = {result_1['c_eff']:.4f}  (emergent speed of light)
    m = {result_1['m_eff']:.4f}  (effective mass)
    
  This is the MASSIVE relativistic scalar field equation.
  
  At high k: ω ≈ c·k (relativistic limit)
  At low k:  ω ≈ m   (rest mass energy)
  
  GROUP VELOCITY at k→0: v_g = {result_1['v_g_at_0']:.4f}
  GROUP VELOCITY at k=1: v_g = {result_1['v_g_at_1']:.4f}
  
  → This branch CAN carry information at speeds up to c!
""")
    else:
        print("\n  NO clear Klein-Gordon mode detected.")
    
    return result_1, result_2


if __name__ == "__main__":
    run_deep_analysis()
