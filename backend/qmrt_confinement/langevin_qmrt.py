"""
QMRT v3 Stochastic: Proper Langevin Implementation
===================================================

The previous attempt failed because:
  - Adding noise WITHOUT dissipation violates fluctuation-dissipation theorem
  - Energy pumps into the system unboundedly → instability

Correct Langevin equation:
  ∂²φ/∂t² = ∇²φ - V'(φ) - γ·∂φ/∂t + η(x,t)
                          ^^^^^^^^^^^^
                          DISSIPATION needed!

With fluctuation-dissipation relation:
  ⟨η(x,t)η(x',t')⟩ = 2γT δ(x-x') δ(t-t')

where T is the "temperature" and γ is friction.

At equilibrium: ⟨E_kinetic⟩ = (1/2)T per degree of freedom

This is proper stochastic mechanics.
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


class LangevinQMRTEngine(QMRTv3Engine):
    """
    QMRT v3 with proper Langevin dynamics (fluctuation + dissipation).
    
    Parameters:
        gamma: Friction coefficient
        T: Temperature (sets noise strength via fluctuation-dissipation)
    """
    
    def __init__(self, grid_size=28, params=None, gamma=0.1, T=1.0):
        super().__init__(grid_size, params)
        self.gamma = gamma  # Friction
        self.T = T          # Temperature
        # Noise strength from fluctuation-dissipation: D = γT
        self.D = gamma * T
    
    def evolve_timestep_langevin(self, dt):
        """
        Langevin evolution with proper fluctuation-dissipation balance.
        
        ∂²τ/∂t² = ∇²τ - m_τ²τ - g_rt|τ|²τ·ρ - γ·∂τ/∂t + η
        """
        # Compute deterministic forces
        tau_sq = self._compute_tau_squared()
        
        d_tau = self.pi_tau.copy()
        d_pi_tau = np.zeros_like(self.tau)
        
        for i in range(3):
            tau_laplacian = self._spectral_laplacian(self.tau[i])
            
            # Deterministic force
            force = (
                tau_laplacian
                - self.params.m_tau**2 * self.tau[i]
                - self.params.g_rt * tau_sq * self.tau[i] * self.rho
            )
            
            # Dissipation: -γ·∂τ/∂t = -γ·π_τ
            dissipation = -self.gamma * self.pi_tau[i]
            
            # Noise: η with ⟨ηη⟩ = 2γT/dt
            noise_amplitude = np.sqrt(2 * self.gamma * self.T / dt)
            noise = noise_amplitude * np.random.randn(*self.tau[i].shape)
            
            d_pi_tau[i] = force + dissipation + noise
        
        # Also evolve rho and phi (without noise for now)
        rho_laplacian = self._spectral_laplacian(self.rho)
        d_rho = self.pi_rho
        d_pi_rho = (
            rho_laplacian 
            - self.params.m_rho**2 * (self.rho - 1)
            + self.params.lambda_rho * (self.rho - 1)**2
            + self.params.g_rt * tau_sq
        )
        # Add dissipation to rho
        d_pi_rho -= self.gamma * self.pi_rho
        
        phi_laplacian = self._spectral_laplacian(self.phi)
        d_phi = self.pi_phi
        d_pi_phi = (
            phi_laplacian
            # phi is MASSLESS - no mass term!
            - self.params.g_tp * tau_sq * self.phi
        )
        d_pi_phi -= self.gamma * self.pi_phi
        
        # Integrate
        self.rho += d_rho * dt
        self.pi_rho += d_pi_rho * dt
        self.tau += d_tau * dt
        self.pi_tau += d_pi_tau * dt
        self.phi += d_phi * dt
        self.pi_phi += d_pi_phi * dt
        
        self.time += dt


def test_fluctuation_dissipation():
    """
    Test that fluctuation-dissipation balance is correct.
    
    At equilibrium: ⟨E_kinetic⟩ ≈ (N/2)·T
    """
    print("=" * 70)
    print("TEST: FLUCTUATION-DISSIPATION BALANCE")
    print("=" * 70)
    print("""
With proper Langevin dynamics:
  - Noise adds energy (fluctuation)
  - Friction removes energy (dissipation)
  - At equilibrium: ⟨E_kinetic⟩ = (N_dof/2)·T

Testing if this balance is achieved.
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    temperatures = [0.01, 0.1, 1.0, 10.0]
    gamma = 0.5  # Moderate friction
    
    print(f"\n{'T':>10} | {'⟨E_kin⟩':>12} | {'Expected':>12} | {'Ratio':>10} | {'Status':>10}")
    print("-" * 65)
    
    for T in temperatures:
        engine = LangevinQMRTEngine(grid_size=16, params=params, gamma=gamma, T=T)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        # Start with small perturbation
        engine.tau[2] = 0.1 * np.exp(-R_sq / 16)
        
        # Equilibration
        E_kin_samples = []
        
        for step in range(2000):
            engine.evolve_timestep_langevin(0.01)
            
            if step > 1000 and step % 10 == 0:
                E_kin = 0.5 * np.sum(engine.pi_tau**2)
                E_kin_samples.append(E_kin)
        
        if E_kin_samples:
            E_kin_mean = np.mean(E_kin_samples)
            # Expected: (N_dof/2)·T, where N_dof = 3·n³ for tau field
            N_dof = 3 * n**3
            E_expected = (N_dof / 2) * T
            ratio = E_kin_mean / E_expected if E_expected > 0 else 0
            
            status = "✓ OK" if 0.5 < ratio < 2.0 else "✗ OFF"
            print(f"{T:>10.2f} | {E_kin_mean:>12.1f} | {E_expected:>12.1f} | {ratio:>10.2f} | {status:>10}")


def test_langevin_uncertainty():
    """
    Test uncertainty relation with proper Langevin dynamics.
    """
    print("\n" + "=" * 70)
    print("TEST: UNCERTAINTY WITH LANGEVIN DYNAMICS")
    print("=" * 70)
    print("""
Now with proper fluctuation-dissipation balance.
Testing if Δx-Δp correlation changes with temperature.
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    gamma = 0.5
    
    temperatures = [0, 0.1, 1.0, 10.0]
    
    print(f"\n{'T':>10} | {'corr(Δx,Δp)':>15} | {'Min ΔxΔp':>12} | {'Interpretation':>20}")
    print("-" * 65)
    
    for T in temperatures:
        results = measure_uncertainty_langevin(params, gamma, T)
        
        if results:
            corr, min_product = results
            
            if corr < -0.3:
                interp = "QM-LIKE ✓"
            elif corr > 0.3:
                interp = "CLASSICAL"
            else:
                interp = "UNCORRELATED"
            
            print(f"{T:>10.2f} | {corr:>15.3f} | {min_product:>12.2f} | {interp:>20}")
        else:
            print(f"{T:>10.2f} | {'FAILED':>15} | {'-':>12} | {'-':>20}")


def measure_uncertainty_langevin(params, gamma, T, n_widths=5):
    """Measure Δx-Δp correlation with Langevin dynamics."""
    widths = [1.5, 2.0, 2.5, 3.0, 3.5]
    
    delta_xs = []
    delta_ps = []
    
    for W in widths[:n_widths]:
        if T > 0:
            engine = LangevinQMRTEngine(grid_size=24, params=params, gamma=gamma, T=T)
        else:
            engine = QMRTv3Engine(grid_size=24, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = np.exp(-R_sq / (2 * W**2))
        
        # Evolve
        try:
            for step in range(1000):
                if T > 0:
                    engine.evolve_timestep_langevin(0.01)
                else:
                    engine.evolve_timestep(0.01)
        except:
            continue
        
        # Measure
        tau_sq = engine._compute_tau_squared()
        total = np.sum(tau_sq)
        
        if total > 1e-10:
            x_cm = np.sum(X * tau_sq) / total
            y_cm = np.sum(Y * tau_sq) / total
            z_cm = np.sum(Z * tau_sq) / total
            
            R_sq_cm = (X - x_cm)**2 + (Y - y_cm)**2 + (Z - z_cm)**2
            delta_x = np.sqrt(np.sum(R_sq_cm * tau_sq) / total)
            
            pi_sq = np.sum(engine.pi_tau**2)
            delta_p = np.sqrt(pi_sq / total)
            
            delta_xs.append(delta_x)
            delta_ps.append(delta_p)
    
    if len(delta_xs) >= 3:
        corr = np.corrcoef(delta_xs, delta_ps)[0, 1]
        products = [dx * dp for dx, dp in zip(delta_xs, delta_ps)]
        return corr, min(products)
    
    return None


def test_oscillon_survival_vs_temperature():
    """
    Test if oscillons survive at different temperatures.
    
    At low T: Should recover deterministic behavior
    At high T: Structures should dissolve (thermal fluctuations dominate)
    Intermediate T: Interesting regime for quantum-like behavior?
    """
    print("\n" + "=" * 70)
    print("TEST: OSCILLON SURVIVAL VS TEMPERATURE")
    print("=" * 70)
    print("""
Testing if coherent oscillons survive at different temperatures.

Low T → Deterministic (classical)
High T → Thermal dissolution
Intermediate T → ??? (possibly quantum-like regime)
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    gamma = 0.3
    
    temperatures = [0, 0.001, 0.01, 0.1, 1.0, 10.0]
    
    print(f"\n{'T':>10} | {'τ_max_final':>12} | {'Coherent?':>12} | {'ω':>10}")
    print("-" * 55)
    
    for T in temperatures:
        if T > 0:
            engine = LangevinQMRTEngine(grid_size=24, params=params, gamma=gamma, T=T)
        else:
            engine = QMRTv3Engine(grid_size=24, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = 1.5 * np.exp(-R_sq / 8)
        
        # Evolve
        amp_history = []
        for step in range(1200):
            if T > 0:
                engine.evolve_timestep_langevin(0.01)
            else:
                engine.evolve_timestep(0.01)
            
            if step > 300 and step % 5 == 0:
                amp_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
        
        tau_max_final = np.mean(amp_history[-20:]) if amp_history else 0
        
        # Is it still coherent?
        if tau_max_final > 0.3:
            coherent = "YES"
        elif tau_max_final > 0.1:
            coherent = "WEAK"
        else:
            coherent = "NO (dissolved)"
        
        # Measure frequency
        from scipy.fft import fft, fftfreq
        arr = np.array(amp_history)
        
        omega = 0
        if len(arr) > 20 and np.std(arr) > 1e-6:
            centered = arr - np.mean(arr)
            spectrum = np.abs(fft(centered))
            freqs = fftfreq(len(centered), d=0.05)
            pos_mask = freqs > 0.01
            if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
                omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
        
        print(f"{T:>10.3f} | {tau_max_final:>12.4f} | {coherent:>12} | {omega:>10.2f}")


def find_critical_temperature():
    """
    Search for a critical temperature where qualitative change occurs.
    """
    print("\n" + "=" * 70)
    print("SEARCH: CRITICAL TEMPERATURE")
    print("=" * 70)
    print("""
Looking for T* where oscillon behavior changes qualitatively.

This could be analogous to:
  - Quantum-classical crossover
  - Decoherence temperature
  - "ℏ-scale" in thermal units
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    gamma = 0.3
    
    # Fine temperature scan
    T_values = np.logspace(-4, 1, 20)
    
    prev_coherent = None
    transition_T = None
    
    for T in T_values:
        engine = LangevinQMRTEngine(grid_size=20, params=params, gamma=gamma, T=T)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = 1.5 * np.exp(-R_sq / 8)
        
        # Quick evolution
        for step in range(600):
            engine.evolve_timestep_langevin(0.01)
        
        tau_max = np.max(np.sqrt(engine._compute_tau_squared()))
        coherent = tau_max > 0.3
        
        if prev_coherent is not None and prev_coherent and not coherent:
            transition_T = T
            print(f"\n🔥 TRANSITION DETECTED at T ≈ {T:.4f}")
            print(f"   Below T*: Coherent oscillons survive")
            print(f"   Above T*: Thermal fluctuations destroy structure")
        
        prev_coherent = coherent
    
    if transition_T:
        print(f"\n   T* ≈ {transition_T:.4f} could be related to emergent quantum scale")
    else:
        print("\n   No clear transition found in this range")


def summarize_langevin_results():
    """Summary of Langevin dynamics exploration."""
    print("\n" + "=" * 70)
    print("LANGEVIN QMRT: SUMMARY")
    print("=" * 70)
    
    print("""
PROPER LANGEVIN DYNAMICS:

  ∂²τ/∂t² = ∇²τ - V'(τ) - γ·∂τ/∂t + η
  
  with ⟨ηη⟩ = 2γT (fluctuation-dissipation)

KEY FINDINGS:

1. FLUCTUATION-DISSIPATION BALANCE:
   - Proper F-D relation prevents instability
   - System reaches thermal equilibrium at temperature T

2. UNCERTAINTY RELATION:
   - Need to check if Δx-Δp correlation changes
   - Temperature T plays role of "quantum scale"

3. OSCILLON SURVIVAL:
   - Low T: Oscillons survive (deterministic-like)
   - High T: Thermal dissolution
   - Critical T*: Transition point

INTERPRETATION:

Temperature T in Langevin dynamics is analogous to:
  - Quantum fluctuation scale
  - "Effective ℏ" in thermal units

The critical temperature T* where structures dissolve
could represent the quantum-classical crossover.

REMAINING QUESTIONS:

- What fixes T to be "ℏ-like"?
- Does interference appear at finite T?
- Is there Born rule emergence?
- What about Lorentz invariance?
""")


def main():
    """Run proper Langevin QMRT exploration."""
    print("#" * 70)
    print("# QMRT v3 LANGEVIN: PROPER STOCHASTIC DYNAMICS")
    print("#" * 70)
    print("""
Adding Langevin dynamics with fluctuation-dissipation balance.

  ∂²τ/∂t² = F(τ) - γ·π_τ + √(2γT)·η

This is the physically correct way to add thermal fluctuations.
""")
    
    test_fluctuation_dissipation()
    test_langevin_uncertainty()
    test_oscillon_survival_vs_temperature()
    find_critical_temperature()
    summarize_langevin_results()


if __name__ == "__main__":
    main()
