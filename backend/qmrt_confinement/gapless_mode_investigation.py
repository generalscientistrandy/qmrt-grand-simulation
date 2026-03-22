"""
QMRT v2: Parameter Sweep to Find Gapless Mode
==============================================

The discovery: Both branches are gapped with current parameters.
The φ field has effective mass: m²_eff = m²_φ + 2g·ω₀²

To achieve a TRUE gapless (acoustic/photon-like) mode, we need:
  m²_eff → 0
  
Options:
1. Set m²_φ = 0 and g = 0 (trivial decoupling)
2. Set m²_φ = -2g·ω₀² (requires negative mass, could be unstable)
3. Explore parameter space to understand when gapless modes appear

This script sweeps parameters to map the branch structure.
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v2_engine import QMRTv2Parameters


def compute_gaps_for_params(M_omega, K_omega, a, omega_0, M_phi, K_phi, m_phi_sq, g):
    """Compute both gaps for given parameters."""
    # Effective coefficients
    mass_omega_sq = 8 * a * omega_0**2
    mass_phi_sq_eff = m_phi_sq + 2 * g * omega_0**2
    
    # At k=0, the matrix is diagonal (no coupling in linearized system)
    # eigenvalues are just the diagonal elements
    omega_sq_1 = mass_omega_sq / M_omega
    omega_sq_2 = mass_phi_sq_eff / M_phi
    
    gap_omega = np.sqrt(max(omega_sq_1, 0)) if omega_sq_1 > 0 else -np.sqrt(-omega_sq_1)
    gap_phi = np.sqrt(max(omega_sq_2, 0)) if omega_sq_2 > 0 else -np.sqrt(-omega_sq_2)
    
    # Speeds at high k (asymptotic)
    c_omega = np.sqrt(K_omega / M_omega)
    c_phi = np.sqrt(K_phi / M_phi)
    
    # Check stability
    stable = omega_sq_1 > 0 and omega_sq_2 > 0
    
    return {
        'gap_omega': gap_omega,
        'gap_phi': gap_phi,
        'c_omega': c_omega,
        'c_phi': c_phi,
        'stable': stable,
        'mass_phi_sq_eff': mass_phi_sq_eff,
    }


def sweep_coupling_strength():
    """Sweep g coupling to see how φ gap changes."""
    print("=" * 70)
    print("PARAMETER SWEEP: Coupling strength g")
    print("=" * 70)
    print("\nFixed: M_φ=1, K_φ=1, m²_φ=0.01, ω₀=1")
    print("Vary:  g from 0 to 0.5")
    print("\nEffective φ mass²: m²_eff = 0.01 + 2g")
    print("-" * 70)
    
    g_values = np.linspace(0, 0.5, 11)
    
    print(f"\n{'g':>8} | {'m²_eff':>10} | {'gap_φ':>10} | {'gap_ω':>10} | {'Stable':>8}")
    print("-" * 60)
    
    for g in g_values:
        result = compute_gaps_for_params(
            M_omega=1.0, K_omega=0.05, a=1.0, omega_0=1.0,
            M_phi=1.0, K_phi=1.0, m_phi_sq=0.01, g=g
        )
        print(f"{g:8.3f} | {result['mass_phi_sq_eff']:10.4f} | {result['gap_phi']:10.4f} | "
              f"{result['gap_omega']:10.4f} | {'YES' if result['stable'] else 'NO':>8}")


def explore_gapless_conditions():
    """Find conditions for gapless φ mode."""
    print("\n" + "=" * 70)
    print("EXPLORING CONDITIONS FOR GAPLESS φ MODE")
    print("=" * 70)
    
    print("""
To have gap_φ = 0, we need:
  m²_eff = m²_φ + 2g·ω₀² = 0
  
This requires m²_φ < 0 if g > 0 and ω₀ ≠ 0.

Option A: m²_φ = 0, g = 0 (decoupled fields)
Option B: m²_φ = -2g·ω₀² (requires negative bare mass)

Let's test Option B with various g values:
""")
    
    print(f"{'g':>8} | {'m²_φ needed':>12} | {'gap_φ':>10} | {'Stable':>8}")
    print("-" * 50)
    
    for g in [0.0, 0.05, 0.1, 0.2]:
        omega_0 = 1.0
        m_phi_sq_needed = -2 * g * omega_0**2
        
        result = compute_gaps_for_params(
            M_omega=1.0, K_omega=0.05, a=1.0, omega_0=omega_0,
            M_phi=1.0, K_phi=1.0, m_phi_sq=m_phi_sq_needed, g=g
        )
        print(f"{g:8.3f} | {m_phi_sq_needed:12.4f} | {result['gap_phi']:10.6f} | "
              f"{'YES' if result['stable'] else 'NO':>8}")
    
    print("\n→ We can achieve gapless φ mode, but it requires negative bare mass m²_φ < 0")
    print("   when there's coupling to the ω field.")


def test_decoupled_limit():
    """Test the g=0 decoupled limit."""
    print("\n" + "=" * 70)
    print("TEST: DECOUPLED LIMIT (g = 0)")
    print("=" * 70)
    print("\nWhen g = 0, the fields don't interact.")
    print("Each field has independent dispersion.\n")
    
    result = compute_gaps_for_params(
        M_omega=1.0, K_omega=0.05, a=1.0, omega_0=1.0,
        M_phi=1.0, K_phi=1.0, m_phi_sq=0.0, g=0.0  # Massless φ!
    )
    
    print(f"ω field (optical):")
    print(f"  Gap:   {result['gap_omega']:.4f}")
    print(f"  Speed: {result['c_omega']:.4f}")
    
    print(f"\nφ field (with m²_φ = 0):")
    print(f"  Gap:   {result['gap_phi']:.6f}")
    print(f"  Speed: {result['c_phi']:.4f}")
    
    if result['gap_phi'] < 0.001:
        print("\n✅ With g=0 and m²_φ=0, the φ field IS gapless!")
        print("   Dispersion: ω = c_φ·k (pure acoustic/photon-like)")


def test_small_mass_regime():
    """Test with small but nonzero coupling and bare mass."""
    print("\n" + "=" * 70)
    print("TEST: SMALL MASS REGIME")
    print("=" * 70)
    print("\nParameters that give a SMALL gap for φ (quasi-gapless):")
    
    # Try different combinations
    test_cases = [
        {'m_phi_sq': 0.001, 'g': 0.001, 'desc': 'Tiny mass, tiny coupling'},
        {'m_phi_sq': 0.01, 'g': 0.0, 'desc': 'Small mass, no coupling'},
        {'m_phi_sq': 0.0, 'g': 0.01, 'desc': 'No mass, small coupling'},
        {'m_phi_sq': -0.01, 'g': 0.01, 'desc': 'Negative mass canceling coupling'},
    ]
    
    print(f"\n{'Case':>40} | {'m²_eff':>10} | {'gap_φ':>10} | {'Stable':>8}")
    print("-" * 80)
    
    for case in test_cases:
        result = compute_gaps_for_params(
            M_omega=1.0, K_omega=0.05, a=1.0, omega_0=1.0,
            M_phi=1.0, K_phi=1.0, m_phi_sq=case['m_phi_sq'], g=case['g']
        )
        print(f"{case['desc']:>40} | {result['mass_phi_sq_eff']:10.4f} | "
              f"{result['gap_phi']:10.6f} | {'YES' if result['stable'] else 'NO':>8}")


def analyze_physical_interpretation():
    """Provide physical interpretation of findings."""
    print("\n" + "=" * 70)
    print("PHYSICAL INTERPRETATION")
    print("=" * 70)
    
    print("""
KEY FINDINGS:

1. CURRENT PARAMETERS (g=0.1, m²_φ=0.01):
   - BOTH branches are gapped (massive)
   - No true "photon" (gapless propagating) mode
   - Both modes behave like massive particles
   
2. THE COUPLING GENERATES MASS:
   - The interaction term g·ω²·φ² gives φ an effective mass
   - m²_eff = m²_φ + 2g·⟨ω⟩² = m²_φ + 2g·ω₀²
   - This is EXACTLY like Higgs mechanism!
   
3. TO GET A GAPLESS MODE:
   Option A: Decouple (g=0) and set m²_φ=0
   Option B: Fine-tune m²_φ = -2g·ω₀² (negative bare mass)
   
4. PHYSICAL MEANING:
   - The ω field (with nonzero VEV ω₀) acts like a Higgs condensate
   - The φ field "acquires mass" from the condensate
   - This is spontaneous mass generation!
   
5. IS THIS BAD FOR THE THEORY?
   - Not necessarily! The Standard Model has ONLY massive particles
     (except the photon and graviton)
   - A massive φ field is like a massive scalar (like the Higgs itself)
   - For emergent relativity, we need ω² = c²k² + m² (Klein-Gordon)
     which IS satisfied, just with m > 0
   
6. FOR A TRUE PHOTON ANALOG:
   - We would need gauge symmetry (vector field)
   - Or a Goldstone mode from continuous symmetry breaking
   - Current model has discrete symmetry (ω → -ω)
""")


def run_all_tests():
    """Run all parameter tests."""
    print("#" * 70)
    print("# QMRT v2: GAPLESS MODE INVESTIGATION")
    print("#" * 70)
    
    sweep_coupling_strength()
    explore_gapless_conditions()
    test_decoupled_limit()
    test_small_mass_regime()
    analyze_physical_interpretation()
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print("""
For QMRT v2 to have a true gapless (photon-like) propagating mode:

OPTION 1: Use g = 0 and m²_φ = 0
  - Simplest solution
  - φ becomes a free massless field
  - Decoupled from ω structure
  - Con: No interaction means φ doesn't "feel" the medium

OPTION 2: Introduce gauge symmetry
  - Make the theory U(1) gauge invariant
  - Requires vector (spin-1) field instead of scalar φ
  - More complex but physically motivated

OPTION 3: Accept massive φ
  - Current setup with m²_eff > 0
  - φ behaves like a massive Klein-Gordon field
  - Still has emergent relativity (just with mass)
  - Analogous to massive particles in QFT

The choice depends on what physical phenomena you want to model:
  - Light propagation → Need gapless mode (Option 1 or 2)
  - Massive particle dynamics → Option 3 is fine
  - Full QFT-like theory → Probably need Option 2
""")


if __name__ == "__main__":
    run_all_tests()
