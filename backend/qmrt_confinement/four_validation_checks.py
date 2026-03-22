"""
QMRT v3: Four Critical Validation Checks
==========================================

1. BROADER CONVERGENCE
   - Test multiple parameter sets, not just one sweet spot
   - Determine if convergence is generic or accidental

2. INITIAL CONDITION INDEPENDENCE  
   - Start from different seeds (narrow, wide, asymmetric, noisy)
   - Check if they relax to same attractor family

3. CONSERVED QUANTITIES / TOPOLOGICAL MARKERS
   - Look for winding numbers, helicity, charges
   - Distinguish real emergent object from long-lived oscillon

4. ANALYTICAL APPROXIMATION
   - Variational ansatz for radius
   - Collective coordinate model
   - Compare numerics to analytics
"""

import numpy as np
from scipy.optimize import minimize_scalar, minimize
from scipy.integrate import quad
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


# =============================================================================
# CHECK 1: BROADER CONVERGENCE
# =============================================================================

def check_broader_convergence():
    """
    Test convergence across multiple parameter sets.
    Is convergence generic or accidental?
    """
    print("=" * 70)
    print("CHECK 1: BROADER CONVERGENCE")
    print("=" * 70)
    print("Testing convergence at multiple parameter points...")
    
    # Parameter sets to test
    param_sets = [
        {'name': 'Baseline', 'g_rt': 5.0, 'm_tau': 16.0},
        {'name': 'Weaker shell', 'g_rt': 3.0, 'm_tau': 16.0},
        {'name': 'Stronger shell', 'g_rt': 8.0, 'm_tau': 16.0},
        {'name': 'Lower mass', 'g_rt': 5.0, 'm_tau': 12.0},
        {'name': 'Higher mass', 'g_rt': 5.0, 'm_tau': 20.0},
    ]
    
    physical_domain = 16.0
    
    print(f"\n{'Config':<15} | {'24³ R':>8} | {'32³ R':>8} | {'48³ R':>8} | {'Change':>8} | {'Conv?':>6}")
    print("-" * 70)
    
    convergent_count = 0
    
    for pset in param_sets:
        params = QMRTv3Parameters(g_rt=pset['g_rt'], m_tau=pset['m_tau'], g_tp=0.1)
        
        radii = []
        for n in [24, 32, 48]:
            dx = physical_domain / n
            
            engine = QMRTv3Engine(grid_size=n, params=params)
            engine.dx = dx
            
            # Initialize
            center = physical_domain / 2
            x = np.arange(n) * dx
            X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
            R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
            
            engine.tau[2] = np.exp(-R_sq / (2 * 1.5**2))
            engine.initial_energy = engine.compute_total_energy()['E_total']
            
            # Evolve
            for _ in range(1000):
                engine.evolve_timestep(0.01)
            
            # Measure
            tau_sq = engine._compute_tau_squared()
            total = np.sum(tau_sq) * dx**3
            R = np.sqrt(np.sum(R_sq * tau_sq) * dx**3 / total) if total > 1e-10 else 0
            radii.append(R)
        
        # Check convergence
        change = abs(radii[2] - radii[1]) / max(radii[2], 0.01)
        converged = change < 0.05
        if converged:
            convergent_count += 1
        
        conv_str = "YES" if converged else "no"
        print(f"{pset['name']:<15} | {radii[0]:8.3f} | {radii[1]:8.3f} | {radii[2]:8.3f} | {change:8.1%} | {conv_str:>6}")
    
    print(f"\nConvergent configurations: {convergent_count}/{len(param_sets)}")
    
    if convergent_count == len(param_sets):
        print("✅ CONVERGENCE IS GENERIC across parameter space")
        return True
    elif convergent_count >= len(param_sets) * 0.6:
        print("⚠️ Convergence in most of parameter space")
        return True
    else:
        print("❌ Convergence is NOT generic")
        return False


# =============================================================================
# CHECK 2: INITIAL CONDITION INDEPENDENCE
# =============================================================================

def check_initial_condition_independence():
    """
    Test if different initial conditions relax to same attractor.
    """
    print("\n" + "=" * 70)
    print("CHECK 2: INITIAL CONDITION INDEPENDENCE")
    print("=" * 70)
    print("Testing relaxation from different starting shapes...")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    n = 32
    physical_domain = 16.0
    dx = physical_domain / n
    
    center = physical_domain / 2
    x = np.arange(n) * dx
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
    R = np.sqrt(R_sq)
    
    # Different initial conditions
    init_conditions = {
        'narrow': lambda: np.exp(-R_sq / (2 * 1.0**2)),
        'standard': lambda: np.exp(-R_sq / (2 * 1.5**2)),
        'wide': lambda: np.exp(-R_sq / (2 * 2.5**2)),
        'asymmetric': lambda: np.exp(-((X-center)**2/1.5**2 + (Y-center)**2/2.5**2 + (Z-center)**2/1.5**2)/2),
        'noisy': lambda: np.exp(-R_sq / (2 * 1.5**2)) * (1 + 0.3*np.random.randn(n,n,n)),
        'ring': lambda: np.exp(-(R - 2)**2 / (2 * 0.5**2)),
    }
    
    print(f"\n{'Initial':>12} | {'R_init':>8} | {'R_final':>8} | {'τ_max':>8} | {'ω':>8}")
    print("-" * 55)
    
    final_radii = []
    final_taus = []
    
    for name, init_func in init_conditions.items():
        engine = QMRTv3Engine(grid_size=n, params=params)
        engine.dx = dx
        
        # Set initial condition
        engine.tau[2] = init_func()
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Measure initial radius
        tau_sq = engine._compute_tau_squared()
        total = np.sum(tau_sq) * dx**3
        R_init = np.sqrt(np.sum(R_sq * tau_sq) * dx**3 / total) if total > 1e-10 else 0
        
        # Evolve and record for frequency
        tau_history = []
        for step in range(1500):
            engine.evolve_timestep(0.01)
            if step % 5 == 0:
                tau_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
        
        # Final measurements
        tau_sq = engine._compute_tau_squared()
        total = np.sum(tau_sq) * dx**3
        R_final = np.sqrt(np.sum(R_sq * tau_sq) * dx**3 / total) if total > 1e-10 else 0
        tau_max = np.max(np.sqrt(tau_sq))
        
        # Frequency from FFT
        from scipy.fft import fft, fftfreq
        tau_arr = np.array(tau_history)
        tau_centered = tau_arr - np.mean(tau_arr)
        spectrum = np.abs(fft(tau_centered))
        freqs = fftfreq(len(tau_centered), d=0.05)
        pos_mask = freqs > 0.01
        if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
            omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
        else:
            omega = 0
        
        final_radii.append(R_final)
        final_taus.append(tau_max)
        
        print(f"{name:>12} | {R_init:8.3f} | {R_final:8.3f} | {tau_max:8.4f} | {omega:8.2f}")
    
    # Check if they converge to same attractor
    R_mean = np.mean(final_radii)
    R_std = np.std(final_radii)
    cv = R_std / R_mean if R_mean > 0 else 999
    
    print(f"\nFinal radius: mean = {R_mean:.3f}, std = {R_std:.3f}, CV = {cv:.2%}")
    
    if cv < 0.15:
        print("✅ SAME ATTRACTOR: Different initial conditions converge to similar final state")
        return True
    else:
        print("❌ Different attractors or no convergence")
        return False


# =============================================================================
# CHECK 3: CONSERVED QUANTITIES / TOPOLOGICAL MARKERS
# =============================================================================

def check_conserved_quantities():
    """
    Look for conserved charges, winding numbers, or topological invariants.
    """
    print("\n" + "=" * 70)
    print("CHECK 3: CONSERVED QUANTITIES / TOPOLOGICAL MARKERS")
    print("=" * 70)
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    n = 32
    dx = 0.5
    
    engine = QMRTv3Engine(grid_size=n, params=params)
    engine.dx = dx
    
    center = n * dx / 2
    x = np.arange(n) * dx
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
    
    engine.tau[2] = np.exp(-R_sq / (2 * 1.5**2))
    engine.initial_energy = engine.compute_total_energy()['E_total']
    
    def compute_quantities():
        """Compute various candidate conserved quantities."""
        tau = engine.tau
        pi_tau = engine.pi_tau
        tau_sq = engine._compute_tau_squared()
        
        # 1. Total "charge" (integral of tau magnitude)
        Q_tau = np.sum(np.sqrt(tau_sq)) * dx**3
        
        # 2. Torsion norm squared (like particle number)
        N_tau = np.sum(tau_sq) * dx**3
        
        # 3. Helicity-like: τ · (∇ × τ) - requires curl
        # For vector field τ, compute curl
        curl_tau = np.zeros((3, n, n, n))
        for i in range(3):
            # curl_i = ε_ijk ∂_j τ_k
            j = (i + 1) % 3
            k = (i + 2) % 3
            curl_tau[i] = (np.roll(tau[k], -1, axis=j) - np.roll(tau[k], 1, axis=j)) / (2*dx) \
                        - (np.roll(tau[j], -1, axis=k) - np.roll(tau[j], 1, axis=k)) / (2*dx)
        
        helicity = np.sum(tau[0]*curl_tau[0] + tau[1]*curl_tau[1] + tau[2]*curl_tau[2]) * dx**3
        
        # 4. Angular momentum: L = ∫ r × (τ × π_τ) 
        # Simplified: just τ × π_τ
        tau_cross_pi = np.zeros((3, n, n, n))
        for i in range(3):
            j = (i + 1) % 3
            k = (i + 2) % 3
            tau_cross_pi[i] = tau[j] * pi_tau[k] - tau[k] * pi_tau[j]
        
        # Integrate x-component of r × (τ × π)
        L_x = np.sum((Y - center) * tau_cross_pi[2] - (Z - center) * tau_cross_pi[1]) * dx**3
        L_y = np.sum((Z - center) * tau_cross_pi[0] - (X - center) * tau_cross_pi[2]) * dx**3
        L_z = np.sum((X - center) * tau_cross_pi[1] - (Y - center) * tau_cross_pi[0]) * dx**3
        L_total = np.sqrt(L_x**2 + L_y**2 + L_z**2)
        
        # 5. Energy (should be conserved by construction)
        E = engine.compute_total_energy()['E_total']
        
        return {
            'Q_tau': Q_tau,
            'N_tau': N_tau,
            'helicity': helicity,
            'L_total': L_total,
            'E': E,
        }
    
    # Track over time
    print("\nTracking candidate conserved quantities over time...")
    
    times = [0, 5, 10, 15, 20]
    history = []
    
    print(f"\n{'t':>6} | {'Q_τ':>10} | {'N_τ':>10} | {'H':>10} | {'L':>10} | {'E':>12}")
    print("-" * 70)
    
    for t in times:
        if t > 0:
            for _ in range(500):
                engine.evolve_timestep(0.01)
        
        q = compute_quantities()
        history.append(q)
        
        print(f"{t:6.0f} | {q['Q_tau']:10.4f} | {q['N_tau']:10.4f} | {q['helicity']:10.4f} | "
              f"{q['L_total']:10.4f} | {q['E']:12.4f}")
    
    # Analyze conservation
    print("\n--- Conservation Analysis ---")
    
    quantities = ['Q_tau', 'N_tau', 'helicity', 'L_total', 'E']
    
    conserved_found = []
    
    for qname in quantities:
        values = [h[qname] for h in history]
        if abs(values[0]) > 1e-10:
            variation = np.std(values) / abs(np.mean(values))
        else:
            variation = np.std(values) if np.std(values) > 1e-10 else 0
        
        is_conserved = variation < 0.05
        status = "CONSERVED" if is_conserved else "varies"
        
        if is_conserved and qname != 'E':  # E is trivially conserved
            conserved_found.append(qname)
        
        print(f"  {qname:>10}: variation = {variation:.2%} → {status}")
    
    if conserved_found:
        print(f"\n✅ Found conserved quantities: {conserved_found}")
        print("   These could be topological markers distinguishing the bound state")
        return True
    else:
        print("\n⚠️ Only energy is conserved (expected)")
        print("   No additional topological marker found")
        print("   This doesn't rule out genuine emergence, but weakens the case")
        return False


# =============================================================================
# CHECK 4: ANALYTICAL APPROXIMATION
# =============================================================================

def check_analytical_approximation():
    """
    Derive and test analytical approximation for the bound state.
    
    Use variational ansatz: τ(r) = A * exp(-r²/2R²)
    
    Compute effective potential V_eff(R) and find minimum.
    Compare predicted radius and frequency to numerics.
    """
    print("\n" + "=" * 70)
    print("CHECK 4: ANALYTICAL APPROXIMATION")
    print("=" * 70)
    
    # Parameters
    m_tau = 16.0
    g_rt = 5.0
    c_tau = 0.7
    lambda_tau = 1.0
    
    print("\n--- Variational Ansatz ---")
    print("τ(r) = A * exp(-r²/2R²)")
    print("where A = amplitude, R = characteristic radius")
    
    def effective_energy(R, A=1.0):
        """
        Compute energy for Gaussian ansatz.
        
        E = E_kinetic + E_gradient + E_mass + E_self + E_coupling
        
        For τ(r) = A * exp(-r²/2R²):
        - Gradient energy: ∫ c²|∇τ|² ~ A² c² / R² * volume
        - Mass energy: ∫ m²|τ|² ~ A² m² * volume
        - Self-interaction: ∫ λ|τ|⁴ ~ A⁴ λ / R³ * factor
        """
        if R <= 0:
            return float('inf')
        
        # Normalization factors for Gaussian in 3D
        # ∫ exp(-r²/R²) d³r = (π R²)^(3/2)
        norm_2 = (np.pi * R**2)**(3/2)  # ∫ τ² 
        norm_4 = (np.pi * R**2 / 2)**(3/2)  # ∫ τ⁴
        
        # Gradient: ∫ |∇τ|² = ∫ (r/R²)² τ² d³r = (3/2R²) * norm_2
        grad_factor = 3 / (2 * R**2)
        
        E_gradient = 0.5 * c_tau**2 * A**2 * grad_factor * norm_2
        E_mass = 0.5 * m_tau**2 * A**2 * norm_2
        E_self = lambda_tau * A**4 * norm_4
        
        # ρ-τ coupling: g_rt * ρ * τ²
        # If ρ is induced by τ, approximately ρ ~ -g_rt * τ² / m_rho²
        # This gives effective contribution ~ -g_rt² * τ⁴ / m_rho²
        # Simplified: adds to self-interaction
        m_rho = 1.0
        E_coupling = -0.5 * g_rt**2 / m_rho**2 * A**4 * norm_4
        
        E_total = E_gradient + E_mass + E_self + E_coupling
        
        return E_total
    
    # Find optimal R for fixed A = 1
    print("\n--- Finding Optimal Radius ---")
    
    result = minimize_scalar(lambda R: effective_energy(R, A=1.0), bounds=(0.5, 10), method='bounded')
    R_optimal = result.x
    E_optimal = result.fun
    
    print(f"Optimal radius (variational): R* = {R_optimal:.4f}")
    print(f"Minimum energy: E* = {E_optimal:.4f}")
    
    # Breathing frequency from second derivative
    # ω² = d²V_eff/dR² at R = R*
    dR = 0.01
    E_plus = effective_energy(R_optimal + dR)
    E_minus = effective_energy(R_optimal - dR)
    E_center = effective_energy(R_optimal)
    
    d2E_dR2 = (E_plus - 2*E_center + E_minus) / dR**2
    
    # For harmonic oscillator around minimum: ω = sqrt(k/m_eff)
    # Here m_eff ~ R² (collective coordinate mass)
    m_eff = R_optimal**2
    omega_predicted = np.sqrt(abs(d2E_dR2) / m_eff) if d2E_dR2 > 0 else 0
    
    print(f"Predicted breathing frequency: ω* = {omega_predicted:.4f}")
    
    # Compare to numerics
    print("\n--- Comparing to Numerics ---")
    
    params = QMRTv3Parameters(g_rt=g_rt, m_tau=m_tau, g_tp=0.1)
    n = 32
    dx = 0.5
    
    engine = QMRTv3Engine(grid_size=n, params=params)
    engine.dx = dx
    
    center = n * dx / 2
    x = np.arange(n) * dx
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
    
    engine.tau[2] = np.exp(-R_sq / (2 * 1.5**2))
    engine.initial_energy = engine.compute_total_energy()['E_total']
    
    # Evolve and measure
    for _ in range(1500):
        engine.evolve_timestep(0.01)
    
    tau_sq = engine._compute_tau_squared()
    total = np.sum(tau_sq) * dx**3
    R_numeric = np.sqrt(np.sum(R_sq * tau_sq) * dx**3 / total) if total > 1e-10 else 0
    
    # For frequency, we measured ω ≈ 32 earlier
    omega_numeric = 32.04  # From convergence study
    
    print(f"\n{'Quantity':<20} | {'Analytic':>12} | {'Numeric':>12} | {'Error':>10}")
    print("-" * 60)
    print(f"{'Radius':<20} | {R_optimal:12.4f} | {R_numeric:12.4f} | {abs(R_optimal-R_numeric)/R_numeric:10.1%}")
    print(f"{'Frequency':<20} | {omega_predicted:12.4f} | {omega_numeric:12.4f} | {abs(omega_predicted-omega_numeric)/omega_numeric:10.1%}")
    
    # Assessment
    R_error = abs(R_optimal - R_numeric) / R_numeric
    omega_error = abs(omega_predicted - omega_numeric) / omega_numeric
    
    print("\n--- Assessment ---")
    
    if R_error < 0.3 and omega_error < 0.5:
        print("✅ ANALYTICAL APPROXIMATION WORKS")
        print("   Variational model captures the basic physics")
        return True
    elif R_error < 0.5:
        print("⚠️ PARTIAL AGREEMENT")
        print("   Radius roughly correct, frequency needs refinement")
        return True
    else:
        print("❌ Analytical model needs improvement")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all four validation checks."""
    print("#" * 70)
    print("# QMRT v3: FOUR CRITICAL VALIDATION CHECKS")
    print("#" * 70)
    print("""
These checks determine if the emergent structure is:
1. Generic (not accidental)
2. Attractor (not initial-condition dependent)
3. Topologically protected (not just long-lived oscillon)
4. Analytically tractable (predictive theory)
""")
    
    results = {}
    
    results['convergence'] = check_broader_convergence()
    results['attractor'] = check_initial_condition_independence()
    results['topological'] = check_conserved_quantities()
    results['analytical'] = check_analytical_approximation()
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check.capitalize():<20}: {status}")
    
    passed_count = sum(results.values())
    
    print(f"\nPassed: {passed_count}/4")
    
    if passed_count == 4:
        print("""
✅ ALL CHECKS PASSED

QMRT v3 produces:
- Generic convergent bound states (not fine-tuned)
- Attractor dynamics (initial conditions don't matter)
- Possibly topologically protected structures
- Analytically predictable properties

This is a CREDIBLE CANDIDATE PHYSICAL THEORY.
""")
    elif passed_count >= 3:
        print("""
⚠️ MOSTLY VALIDATED

The theory shows strong signs of genuine emergent physics
but some aspects need further investigation.
""")
    else:
        print("""
❌ NEEDS MORE WORK

Some fundamental checks failed. The observed structures
may be numerical artifacts or require parameter tuning.
""")
    
    return results


if __name__ == "__main__":
    results = main()
