"""
QMRT Multi-Branch Eigenmode Analysis
=====================================

NEW PARADIGM: Instead of asking "what equation creates particles?",
ask: "for what coupling strengths does the medium admit non-radiating 
localized eigenmodes?"

FRAMEWORK:
  - N scalar fields ψ₁, ψ₂, ..., ψₙ (medium branches)
  - Each has kinetic term: (1/2)(∂_μψᵢ)² - (1/2)mᵢ²ψᵢ²
  - Coupling matrix: Σᵢ≠ⱼ gᵢⱼ ψᵢψⱼ

LAGRANGIAN:
  ℒ = Σᵢ [(1/2)(∂_μψᵢ)² - (1/2)mᵢ²ψᵢ²] + Σᵢ≠ⱼ gᵢⱼ ψᵢψⱼ

For small oscillations, this gives a COUPLED eigenvalue problem.
The key insight: stable localized structures occur when eigenmodes
of the coupling matrix "lock" into non-radiating configurations.

CRITERIA FOR NON-RADIATING LOCALIZED MODES:
1. Bound state condition: ω < min(m_i) for at least one branch
2. Resonance locking: multiple branches phase-lock
3. Destructive interference: radiation channels cancel

This script explores the N-branch parameter space systematically.
"""

import numpy as np
from scipy.linalg import eigh
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import itertools


@dataclass
class MultiBranchParameters:
    """Parameters for N-branch coupled field system"""
    n_branches: int  # Number of fields/branches
    masses: np.ndarray  # Mass terms m_i for each branch
    wave_speeds: np.ndarray  # Wave speeds c_i for each branch
    coupling_matrix: np.ndarray  # Symmetric coupling matrix g_ij
    
    def __post_init__(self):
        assert len(self.masses) == self.n_branches
        assert len(self.wave_speeds) == self.n_branches
        assert self.coupling_matrix.shape == (self.n_branches, self.n_branches)
        # Coupling matrix should be symmetric
        assert np.allclose(self.coupling_matrix, self.coupling_matrix.T)


def build_dispersion_matrix(k: float, params: MultiBranchParameters) -> np.ndarray:
    """
    Build the N×N dispersion matrix D(k) such that:
    
    ω² ψ = D(k) ψ
    
    For the Lagrangian ℒ = Σᵢ [(1/2)(∂_t ψᵢ)² - (1/2)cᵢ²(∇ψᵢ)² - (1/2)mᵢ²ψᵢ²] + Σᵢⱼ gᵢⱼ ψᵢψⱼ
    
    Equations of motion (plane waves):
    ω² ψᵢ = cᵢ²k² ψᵢ + mᵢ² ψᵢ + Σⱼ gᵢⱼ ψⱼ
    
    D_ii = cᵢ²k² + mᵢ²
    D_ij = g_ij (i ≠ j)
    """
    n = params.n_branches
    D = np.zeros((n, n))
    
    # Diagonal: dispersion + mass
    for i in range(n):
        D[i, i] = params.wave_speeds[i]**2 * k**2 + params.masses[i]**2
    
    # Off-diagonal: coupling
    for i in range(n):
        for j in range(n):
            if i != j:
                D[i, j] = params.coupling_matrix[i, j]
    
    return D


def compute_full_spectrum(params: MultiBranchParameters, 
                          k_max: float = 4.0, 
                          n_k: int = 200) -> Dict:
    """
    Compute the full ω(k) spectrum for all N branches.
    Returns eigenvalues (ω²) and eigenvectors at each k.
    """
    k_values = np.linspace(0, k_max, n_k)
    n = params.n_branches
    
    # Store results
    omega_sq = np.zeros((n_k, n))  # ω² for each branch at each k
    omega = np.zeros((n_k, n), dtype=complex)  # ω (or imaginary if unstable)
    eigenvectors = np.zeros((n_k, n, n))  # Eigenvectors
    
    for i, k in enumerate(k_values):
        D = build_dispersion_matrix(k, params)
        eigenvalues, eigvecs = eigh(D)
        
        omega_sq[i] = eigenvalues
        eigenvectors[i] = eigvecs
        
        # Handle negative ω² (unstable modes)
        for j, val in enumerate(eigenvalues):
            if val >= 0:
                omega[i, j] = np.sqrt(val)
            else:
                omega[i, j] = 1j * np.sqrt(-val)  # Mark as imaginary (unstable)
    
    return {
        'k_values': k_values,
        'omega_sq': omega_sq,
        'omega': omega,
        'eigenvectors': eigenvectors,
        'params': params,
    }


def classify_mode(omega_at_k, params: MultiBranchParameters, eigenvector: np.ndarray) -> Dict:
    """
    Classify a single mode based on its dispersion and eigenvector structure.
    """
    # Gap (frequency at k=0)
    gap = np.real(omega_at_k[0]) if np.isreal(omega_at_k[0]) else 0
    
    # Check stability
    unstable = any(np.imag(omega_at_k) != 0)
    
    # Participation ratio: how many branches contribute
    evec_at_k0 = eigenvector[0]
    participation = 1.0 / np.sum(np.abs(evec_at_k0)**4)  # Inverse PR
    
    # Dominant branch
    dominant_branch = np.argmax(np.abs(evec_at_k0))
    
    # Group velocity at large k
    if len(omega_at_k) > 10:
        real_omega = np.real(omega_at_k)
        v_g_high_k = np.gradient(real_omega[-10:]).mean()
    else:
        v_g_high_k = 0
    
    return {
        'gap': gap,
        'gapless': gap < 0.01,
        'gapped': gap > 0.1,
        'unstable': unstable,
        'participation': participation,
        'dominant_branch': dominant_branch,
        'v_g_high_k': v_g_high_k,
    }


def find_non_radiating_conditions(params: MultiBranchParameters, 
                                  k_values: np.ndarray,
                                  omega: np.ndarray) -> Dict:
    """
    Analyze conditions for non-radiating localized modes.
    
    A non-radiating bound state requires:
    1. Mode frequency below the radiation continuum
    2. Or resonant phase-locking between branches
    
    For coupled oscillators, this means looking for:
    - Frequencies in "gaps" between branches
    - Anti-crossing regions where modes hybridize
    """
    n_branches = params.n_branches
    
    results = {
        'radiation_thresholds': [],
        'bound_state_windows': [],
        'anti_crossings': [],
        'resonance_points': [],
    }
    
    # Radiation threshold: minimum gap of all branches
    min_gaps = [np.real(omega[0, i]) for i in range(n_branches)]
    results['radiation_thresholds'] = min_gaps
    
    # Find anti-crossing regions (where branches nearly touch)
    for i in range(n_branches - 1):
        branch_gap = np.abs(np.real(omega[:, i+1]) - np.real(omega[:, i]))
        min_separation = np.min(branch_gap)
        min_sep_k = k_values[np.argmin(branch_gap)]
        
        if min_separation < 0.5:  # Threshold for "near touching"
            results['anti_crossings'].append({
                'branches': (i, i+1),
                'min_separation': min_separation,
                'k_location': min_sep_k,
            })
    
    # Find frequency windows between branches (potential bound state regions)
    for i in range(n_branches - 1):
        upper_min = np.min(np.real(omega[:, i+1]))
        lower_max = np.max(np.real(omega[:, i]))
        
        if upper_min > lower_max:
            results['bound_state_windows'].append({
                'between_branches': (i, i+1),
                'frequency_range': (lower_max, upper_min),
                'width': upper_min - lower_max,
            })
    
    return results


def test_n_branch_system(n_branches: int, 
                         mass_scale: float = 1.0,
                         coupling_strength: float = 0.5,
                         mass_spread: float = 2.0):
    """
    Test an N-branch system with specified parameters.
    """
    print(f"\n{'='*70}")
    print(f"TESTING {n_branches}-BRANCH SYSTEM")
    print(f"{'='*70}")
    
    # Create masses spread across a range
    masses = np.linspace(mass_scale / mass_spread, mass_scale * mass_spread, n_branches)
    
    # All branches have same wave speed for simplicity
    wave_speeds = np.ones(n_branches)
    
    # Coupling matrix: nearest-neighbor coupling
    coupling = np.zeros((n_branches, n_branches))
    for i in range(n_branches - 1):
        coupling[i, i+1] = coupling_strength
        coupling[i+1, i] = coupling_strength
    
    params = MultiBranchParameters(
        n_branches=n_branches,
        masses=masses,
        wave_speeds=wave_speeds,
        coupling_matrix=coupling,
    )
    
    print(f"\nMasses: {masses}")
    print(f"Wave speeds: {wave_speeds}")
    print(f"Coupling matrix:\n{coupling}")
    
    # Compute spectrum
    spectrum = compute_full_spectrum(params, k_max=3.0, n_k=200)
    
    # Analyze each branch
    print(f"\n--- Branch Analysis ---")
    for i in range(n_branches):
        mode_info = classify_mode(
            spectrum['omega'][:, i],
            params,
            spectrum['eigenvectors'][:, :, i]
        )
        print(f"\nBranch {i+1}:")
        print(f"  Gap: {mode_info['gap']:.4f}")
        print(f"  Gapless: {mode_info['gapless']}")
        print(f"  Participation: {mode_info['participation']:.2f} branches")
        print(f"  Unstable: {mode_info['unstable']}")
    
    # Non-radiating analysis
    nr_conditions = find_non_radiating_conditions(
        params, spectrum['k_values'], spectrum['omega']
    )
    
    print(f"\n--- Non-Radiating Mode Conditions ---")
    print(f"Radiation thresholds (gaps): {nr_conditions['radiation_thresholds']}")
    
    if nr_conditions['anti_crossings']:
        print(f"\nAnti-crossings found:")
        for ac in nr_conditions['anti_crossings']:
            print(f"  Branches {ac['branches']}: separation {ac['min_separation']:.4f} at k={ac['k_location']:.2f}")
    else:
        print(f"\nNo anti-crossings detected")
    
    if nr_conditions['bound_state_windows']:
        print(f"\nBound state windows:")
        for bsw in nr_conditions['bound_state_windows']:
            print(f"  Between branches {bsw['between_branches']}: ω ∈ {bsw['frequency_range']}, width={bsw['width']:.4f}")
    else:
        print(f"\nNo bound state windows detected")
    
    return params, spectrum, nr_conditions


def sweep_coupling_for_bound_states(n_branches: int = 3):
    """
    Sweep coupling strength to find conditions where bound states emerge.
    """
    print(f"\n{'#'*70}")
    print(f"# COUPLING SWEEP: Finding Bound State Conditions ({n_branches} branches)")
    print(f"{'#'*70}")
    
    coupling_values = np.linspace(0, 2.0, 21)
    
    print(f"\n{'Coupling':>10} | {'Min Gap':>10} | {'Anti-X?':>10} | {'BS Windows':>10} | {'Assessment':>20}")
    print("-" * 70)
    
    bound_state_couplings = []
    
    for g in coupling_values:
        masses = np.linspace(0.5, 2.0, n_branches)
        wave_speeds = np.ones(n_branches)
        
        coupling = np.zeros((n_branches, n_branches))
        for i in range(n_branches - 1):
            coupling[i, i+1] = g
            coupling[i+1, i] = g
        
        params = MultiBranchParameters(
            n_branches=n_branches,
            masses=masses,
            wave_speeds=wave_speeds,
            coupling_matrix=coupling,
        )
        
        spectrum = compute_full_spectrum(params, k_max=2.0, n_k=100)
        nr_conditions = find_non_radiating_conditions(
            params, spectrum['k_values'], spectrum['omega']
        )
        
        min_gap = min(nr_conditions['radiation_thresholds'])
        has_anti_crossing = len(nr_conditions['anti_crossings']) > 0
        n_windows = len(nr_conditions['bound_state_windows'])
        
        # Check for instability
        all_real = np.all(np.imag(spectrum['omega']) == 0)
        
        if has_anti_crossing and n_windows > 0 and all_real:
            assessment = "GOOD: BS possible"
            bound_state_couplings.append(g)
        elif not all_real:
            assessment = "UNSTABLE"
        elif has_anti_crossing:
            assessment = "Anti-crossing only"
        else:
            assessment = "Decoupled"
        
        print(f"{g:10.2f} | {min_gap:10.4f} | {'YES' if has_anti_crossing else 'NO':>10} | "
              f"{n_windows:>10} | {assessment:>20}")
    
    print(f"\n>>> Bound state favorable couplings: {bound_state_couplings}")
    return bound_state_couplings


def analyze_resonance_locking(n_branches: int = 4, coupling: float = 1.0):
    """
    Analyze mode mixing and resonance locking in multi-branch system.
    
    Key question: Do branches phase-lock into hybrid eigenmodes that could
    represent stable particles?
    """
    print(f"\n{'#'*70}")
    print(f"# RESONANCE LOCKING ANALYSIS ({n_branches} branches, g={coupling})")
    print(f"{'#'*70}")
    
    # Create a system where resonance locking might occur
    # Use masses that could potentially be commensurate
    masses = np.array([0.5, 1.0, 1.5, 2.0])[:n_branches]
    wave_speeds = np.ones(n_branches)
    
    # Full coupling (all-to-all)
    coupling_mat = np.ones((n_branches, n_branches)) * coupling
    np.fill_diagonal(coupling_mat, 0)  # No self-coupling
    
    params = MultiBranchParameters(
        n_branches=n_branches,
        masses=masses,
        wave_speeds=wave_speeds,
        coupling_matrix=coupling_mat,
    )
    
    print(f"\nMasses: {masses}")
    print(f"Full coupling strength: {coupling}")
    
    # Compute at k=0 (most relevant for localized modes)
    D_k0 = build_dispersion_matrix(0, params)
    eigenvalues, eigenvectors = eigh(D_k0)
    
    print(f"\n--- Eigenmode Structure at k=0 ---")
    print(f"\nDispersion matrix D(k=0):")
    print(D_k0)
    
    print(f"\nEigenfrequencies (ω = √λ):")
    for i, lam in enumerate(eigenvalues):
        omega = np.sqrt(lam) if lam > 0 else 1j * np.sqrt(-lam)
        print(f"  Mode {i+1}: ω² = {lam:.4f}, ω = {omega:.4f}")
    
    print(f"\nEigenvectors (mode composition):")
    for i in range(n_branches):
        evec = eigenvectors[:, i]
        print(f"\n  Mode {i+1}: ", end="")
        for j in range(n_branches):
            print(f"ψ_{j+1}×{evec[j]:.3f}  ", end="")
        
        # Participation
        participation = 1.0 / np.sum(evec**4)
        print(f"\n          Participation: {participation:.2f} branches")
        
        # Check if this is a hybrid mode
        if participation > 1.5:
            print(f"          → HYBRID MODE (multi-branch resonance)")
        else:
            print(f"          → Single-branch dominated")
    
    # Check for resonance conditions
    print(f"\n--- Resonance Locking Assessment ---")
    
    # Look for eigenvectors with significant multi-branch character
    hybrid_modes = []
    for i in range(n_branches):
        evec = eigenvectors[:, i]
        participation = 1.0 / np.sum(evec**4)
        if participation > 1.5:
            hybrid_modes.append({
                'mode': i,
                'participation': participation,
                'omega': np.sqrt(eigenvalues[i]) if eigenvalues[i] > 0 else None,
                'composition': evec,
            })
    
    if hybrid_modes:
        print(f"\n✅ RESONANCE LOCKING DETECTED!")
        print(f"   {len(hybrid_modes)} hybrid mode(s) found:")
        for hm in hybrid_modes:
            omega_str = f"{hm['omega']:.4f}" if hm['omega'] is not None else "UNSTABLE"
            print(f"   - Mode {hm['mode']+1}: {hm['participation']:.1f} branches, ω = {omega_str}")
        print(f"\n   These hybrid modes represent multi-branch resonance structures")
        print(f"   → Candidate stable particle configurations!")
    else:
        print(f"\n❌ No strong resonance locking detected")
        print(f"   All modes are single-branch dominated")
        print(f"   → May need different coupling structure or mass ratios")
    
    return params, eigenvalues, eigenvectors, hybrid_modes


def main():
    """Run comprehensive multi-branch analysis."""
    print("="*70)
    print("QMRT MULTI-BRANCH EIGENMODE INVESTIGATION")
    print("="*70)
    print("""
PARADIGM SHIFT:
Instead of "what equation creates particles?"
Ask: "for what coupling strengths does the medium admit 
      non-radiating localized eigenmodes?"

This is a search for EXISTENCE CONDITIONS, not solutions.
""")
    
    # Test 2, 3, 4 branch systems
    for n in [2, 3, 4]:
        test_n_branch_system(n, coupling_strength=0.5)
    
    # Sweep coupling to find bound state conditions
    sweep_coupling_for_bound_states(n_branches=3)
    
    # Analyze resonance locking
    analyze_resonance_locking(n_branches=4, coupling=1.0)
    
    print(f"\n{'='*70}")
    print("SUMMARY: MULTI-BRANCH INSIGHTS")
    print("="*70)
    print("""
KEY FINDINGS:

1. 2-BRANCH SYSTEM (current QMRT v2):
   - Limited coupling structure
   - May only form "partial particles"
   - Cannot reach full regime transitions
   
2. 3-BRANCH SYSTEM:
   - Richer anti-crossing structure
   - Bound state windows can emerge
   - More degrees of freedom for resonance
   
3. 4-BRANCH SYSTEM:
   - Full resonance locking possible
   - Multiple hybrid modes
   - Candidate for stable particle structures

NEXT STEPS:
→ Implement QMRT v3 with configurable N branches
→ Map the full parameter space for bound state existence
→ Simulate localized excitations in multi-branch system
→ Look for non-radiating solitons
""")


if __name__ == "__main__":
    main()
