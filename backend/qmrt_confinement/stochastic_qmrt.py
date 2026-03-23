"""
QMRT v3 Stochastic Extension: Exploring Rung 3
===============================================

Adding Langevin noise to explore the transition from:
  Rung 2 (Nonlinear Relativistic Wave) → Rung 3 (Fluctuation-Dominated Coherent)

Key equation:
  ∂²φ/∂t² = ∇²φ - V'(φ) + η(x,t)

where η is white noise with:
  ⟨η(x,t)⟩ = 0
  ⟨η(x,t)η(x',t')⟩ = 2D δ(x-x') δ(t-t')

D is the noise strength - the key parameter.

RESEARCH QUESTIONS:
1. Does uncertainty relation (ΔxΔp) change sign with noise?
2. Is there a preferred D value where structures are stable?
3. Does energy discretization emerge?
4. What fixes D to be "ℏ-like"?
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


class StochasticQMRTEngine(QMRTv3Engine):
    """
    QMRT v3 with Langevin noise term.
    
    Extends deterministic QMRT to explore fluctuation-dominated regime.
    """
    
    def __init__(self, grid_size=28, params=None, noise_strength=0.0):
        """
        Initialize stochastic engine.
        
        Args:
            grid_size: Size of 3D grid
            params: QMRTv3Parameters
            noise_strength: D parameter (0 = deterministic, >0 = stochastic)
        """
        super().__init__(grid_size, params)
        self.D = noise_strength  # Noise strength (candidate for ℏ_eff)
    
    def evolve_timestep_stochastic(self, dt):
        """
        Single timestep with Langevin noise.
        
        Equation: ∂²τ/∂t² = ∇²τ - m_τ²τ - g_rt|τ|²τ·ρ + η
        """
        # Compute deterministic forces (same as parent)
        rho_laplacian = self._compute_laplacian_scalar(self.rho)
        d_rho = self.pi_rho
        tau_sq = self._compute_tau_squared()
        d_pi_rho = (
            rho_laplacian 
            - self.params.m_rho**2 * (self.rho - 1)
            + self.params.lambda_rho * (self.rho - 1)**2
            + self.params.g_rt * tau_sq
        )
        
        d_tau = self.pi_tau.copy()
        d_pi_tau = np.zeros_like(self.tau)
        
        for i in range(3):
            tau_laplacian = self._compute_laplacian_scalar(self.tau[i])
            d_pi_tau[i] = (
                tau_laplacian
                - self.params.m_tau**2 * self.tau[i]
                - self.params.g_rt * tau_sq * self.tau[i] * self.rho
                - self.params.g_tp * self.tau[i] * self._compute_phi_squared()
            )
        
        phi_laplacian = self._compute_laplacian_scalar(self.phi)
        d_phi = self.pi_phi
        d_pi_phi = (
            phi_laplacian
            - self.params.m_phi**2 * self.phi
            - self.params.g_tp * tau_sq * self.phi
        )
        
        # ADD LANGEVIN NOISE to momentum equations
        if self.D > 0:
            noise_amplitude = np.sqrt(2 * self.D / dt)
            
            # Noise on torsion momentum (main field)
            for i in range(3):
                noise = noise_amplitude * np.random.randn(*self.tau[i].shape)
                d_pi_tau[i] += noise
            
            # Optionally add noise to other fields too
            # d_pi_rho += noise_amplitude * np.random.randn(*self.rho.shape)
            # d_pi_phi += noise_amplitude * np.random.randn(*self.phi.shape)
        
        # Symplectic integration
        self.rho += d_rho * dt
        self.pi_rho += d_pi_rho * dt
        self.tau += d_tau * dt
        self.pi_tau += d_pi_tau * dt
        self.phi += d_phi * dt
        self.pi_phi += d_pi_phi * dt
        
        self.time += dt


def test_noise_vs_uncertainty():
    """
    KEY TEST: Does adding noise change the Δx-Δp correlation?
    
    In deterministic QMRT: Δx and Δp are POSITIVELY correlated (opposite to QM)
    With noise: Does correlation become NEGATIVE (like QM uncertainty)?
    """
    print("=" * 70)
    print("TEST: NOISE EFFECT ON UNCERTAINTY RELATION")
    print("=" * 70)
    print("""
In deterministic QMRT: corr(Δx, Δp) = +0.83 (OPPOSITE to QM)
In quantum mechanics: corr(Δx, Δp) < 0 (uncertainty relation)

Question: Does adding noise flip the correlation?
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    noise_strengths = [0, 0.01, 0.1, 1.0, 10.0]
    
    print(f"\n{'D (noise)':>12} | {'corr(Δx,Δp)':>15} | {'Min ΔxΔp':>12} | {'Interpretation':>20}")
    print("-" * 70)
    
    for D in noise_strengths:
        results = measure_uncertainty_with_noise(params, D)
        
        if results:
            corr, min_product = results
            
            if corr < -0.3:
                interp = "QM-LIKE ✓"
            elif corr > 0.3:
                interp = "CLASSICAL (opposite)"
            else:
                interp = "UNCORRELATED"
            
            print(f"{D:>12.2f} | {corr:>15.3f} | {min_product:>12.2f} | {interp:>20}")
        else:
            print(f"{D:>12.2f} | {'UNSTABLE':>15} | {'-':>12} | {'BLOWS UP':>20}")


def measure_uncertainty_with_noise(params, D, n_widths=5):
    """
    Measure Δx-Δp correlation for different initial widths.
    """
    widths = [1.5, 2.0, 2.5, 3.0, 3.5]
    
    delta_xs = []
    delta_ps = []
    
    for W in widths[:n_widths]:
        engine = StochasticQMRTEngine(grid_size=28, params=params, noise_strength=D)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = np.exp(-R_sq / (2 * W**2))
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Evolve with noise
        try:
            for step in range(800):
                engine.evolve_timestep_stochastic(0.01)
                
                # Check for blowup
                tau_max = np.max(np.abs(engine.tau))
                if tau_max > 1000 or np.isnan(tau_max):
                    return None
        except:
            return None
        
        # Measure Δx and Δp
        tau_sq = engine._compute_tau_squared()
        total = np.sum(tau_sq)
        
        if total > 1e-10:
            x_cm = np.sum(X * tau_sq) / total
            y_cm = np.sum(Y * tau_sq) / total
            z_cm = np.sum(Z * tau_sq) / total
            
            R_sq_from_cm = (X - x_cm)**2 + (Y - y_cm)**2 + (Z - z_cm)**2
            delta_x = np.sqrt(np.sum(R_sq_from_cm * tau_sq) / total)
            
            pi_sq = np.sum(engine.pi_tau**2)
            delta_p = np.sqrt(pi_sq / total)
            
            delta_xs.append(delta_x)
            delta_ps.append(delta_p)
    
    if len(delta_xs) >= 3:
        corr = np.corrcoef(delta_xs, delta_ps)[0, 1]
        products = [dx * dp for dx, dp in zip(delta_xs, delta_ps)]
        min_product = min(products)
        return corr, min_product
    
    return None


def search_critical_noise():
    """
    Search for a critical noise strength where behavior changes.
    
    This could indicate a preferred "ℏ_eff" value.
    """
    print("\n" + "=" * 70)
    print("SEARCH FOR CRITICAL NOISE STRENGTH")
    print("=" * 70)
    print("""
Looking for a noise strength D* where:
  - Structures remain stable
  - Uncertainty relation flips sign
  - Energy shows discretization

D* could be the emergent "ℏ_eff".
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Fine-grained search
    D_values = np.logspace(-3, 2, 20)  # 0.001 to 100
    
    print(f"\n{'D':>12} | {'Stable?':>10} | {'E_mean':>12} | {'E_std':>12} | {'ω':>10}")
    print("-" * 65)
    
    for D in D_values:
        result = test_stability_at_noise(params, D)
        
        if result:
            stable, E_mean, E_std, omega = result
            status = "YES" if stable else "NO"
            print(f"{D:>12.4f} | {status:>10} | {E_mean:>12.1f} | {E_std:>12.1f} | {omega:>10.2f}")
        else:
            print(f"{D:>12.4f} | {'UNSTABLE':>10} | {'-':>12} | {'-':>12} | {'-':>10}")


def test_stability_at_noise(params, D, n_runs=5):
    """
    Test if oscillons remain stable at given noise strength.
    Also measure energy mean/std and frequency.
    """
    energies = []
    frequencies = []
    
    for run in range(n_runs):
        np.random.seed(42 + run)
        engine = StochasticQMRTEngine(grid_size=24, params=params, noise_strength=D)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = 1.5 * np.exp(-R_sq / 8)
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Evolve
        amp_history = []
        E_history = []
        stable = True
        
        try:
            for step in range(1000):
                engine.evolve_timestep_stochastic(0.01)
                
                tau_max = np.max(np.sqrt(engine._compute_tau_squared()))
                
                if tau_max > 100 or np.isnan(tau_max):
                    stable = False
                    break
                
                if step > 200 and step % 5 == 0:
                    amp_history.append(tau_max)
                    E_history.append(engine.compute_total_energy()['E_total'])
        except:
            stable = False
        
        if not stable:
            return None
        
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
        
        if E_history:
            energies.append(np.mean(E_history))
        frequencies.append(omega)
    
    if energies:
        return True, np.mean(energies), np.std(energies), np.mean(frequencies)
    
    return None


def test_energy_discretization_with_noise():
    """
    Test if noise induces energy discretization.
    
    In deterministic QMRT: energy is continuous
    With noise: might energy cluster at discrete levels?
    """
    print("\n" + "=" * 70)
    print("TEST: ENERGY DISCRETIZATION WITH NOISE")
    print("=" * 70)
    print("""
Without noise: Energy is continuous (no discretization)
With noise: Does energy cluster at discrete levels?

If yes, this would suggest emergent quantization!
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    for D in [0, 0.1, 1.0]:
        print(f"\n--- D = {D} ---")
        
        # Run many trials with random initial conditions
        np.random.seed(42)
        final_energies = []
        
        for trial in range(15):
            engine = StochasticQMRTEngine(grid_size=24, params=params, noise_strength=D)
            
            n = engine.grid_size
            center = n // 2
            x = np.arange(n)
            X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
            R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
            
            # Random initial amplitude
            A = 0.5 + 2.0 * np.random.random()
            engine.tau[2] = A * np.exp(-R_sq / 8)
            engine.initial_energy = engine.compute_total_energy()['E_total']
            
            # Evolve
            try:
                for step in range(1000):
                    if D > 0:
                        engine.evolve_timestep_stochastic(0.01)
                    else:
                        engine.evolve_timestep(0.01)
                
                E_final = engine.compute_total_energy()['E_total']
                if not np.isnan(E_final) and E_final < 1e6:
                    final_energies.append(E_final)
            except:
                pass
        
        if final_energies:
            E_arr = np.array(final_energies)
            print(f"  N samples: {len(E_arr)}")
            print(f"  E range: [{E_arr.min():.1f}, {E_arr.max():.1f}]")
            print(f"  E mean: {E_arr.mean():.1f}, std: {E_arr.std():.1f}")
            
            # Check for clustering
            n_bins = 5
            hist, edges = np.histogram(E_arr, bins=n_bins)
            max_count = max(hist)
            
            if max_count > len(E_arr) * 0.5:
                print(f"  ⚠️ Strong clustering detected (max bin: {max_count}/{len(E_arr)})")
            else:
                print(f"  Energy spread (no clear discretization)")


def summarize_stochastic_exploration():
    """Summary of stochastic QMRT exploration."""
    print("\n" + "=" * 70)
    print("STOCHASTIC QMRT: EXPLORATION SUMMARY")
    print("=" * 70)
    
    print("""
WHAT WE'RE TESTING:

The transition from Rung 2 → Rung 3 in the emergence ladder:
  Rung 2: Nonlinear Relativistic Wave (deterministic)
  Rung 3: Fluctuation-Dominated Coherent (stochastic)

KEY QUESTIONS:

1. Does noise flip the Δx-Δp correlation from + to -?
   (Would indicate uncertainty-like behavior)

2. Is there a critical noise strength D*?
   (Would be candidate for emergent ℏ_eff)

3. Does noise induce energy discretization?
   (Would suggest quantization)

THE HARD PROBLEM REMAINS:

Even if these tests show positive results, we still need:
  - Complex phase evolution
  - Interference phenomena
  - Born probability rule
  - Lorentz invariance of D

This is exploratory research, not proof of quantum emergence.
""")


def main():
    """Run stochastic QMRT exploration."""
    print("#" * 70)
    print("# QMRT v3 STOCHASTIC: EXPLORING RUNG 3")
    print("#" * 70)
    print("""
Adding Langevin noise to explore fluctuation-dominated regime.

This is a recognized research pathway:
  - Parisi-Wu stochastic quantization
  - Nelson stochastic mechanics
  - Emergent quantum hydrodynamics
""")
    
    test_noise_vs_uncertainty()
    search_critical_noise()
    test_energy_discretization_with_noise()
    summarize_stochastic_exploration()


if __name__ == "__main__":
    main()
