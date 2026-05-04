"""
QMRT v3: Tri-Branch Geometric Field Engine
==========================================

Three fundamental substrate fields:
  ρ(x,t) → Compression / Density mode (scalar)
  τᵢ(x,t) → Torsion / Rotational strain mode (vector, 3 components)
  φ(x,t) → Radiation / Phase mode (scalar, massless)

Lagrangian:
  L = L_ρ + L_τ + L_φ + L_int

Where:
  L_ρ = ½(∂_t ρ)² - c_ρ²/2 (∇ρ)² - ½m_ρ²ρ² - λ_ρ ρ⁴
  L_τ = ½(∂_t τᵢ)² - c_τ²/2 (∇τᵢ)² - ½m_τ²τᵢτᵢ - λ_τ(τᵢτᵢ)²
  L_φ = ½(∂_t φ)² - c_φ²/2 (∇φ)²   [NO MASS - defines causality]

Coupling hierarchy:
  L_ρτ = -g_rt ρ (τᵢτᵢ)           [nonlinear, shell formation]
  L_τφ = -g_tp (τᵢτᵢ)(∂_μφ ∂^μφ)  [threshold decay]
  L_ρφ = -g_rp ρ φ                 [weak, gravity-like]

Physical interpretation:
  A particle = coherent locked resonance between ρ and τ,
               below the φ radiation threshold.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Dict, Optional
import json


@dataclass
class QMRTv3Parameters:
    """
    Parameters for the tri-branch QMRT v3 system.
    All values in natural units where m_ρ = c_ρ = λ_ρ = 1.
    """
    # Compression branch (reference scale)
    m_rho: float = 1.0        # Mass
    c_rho: float = 1.0        # Wave speed
    lambda_rho: float = 1.0   # Self-interaction
    
    # Torsion branch
    m_tau: float = 2.0        # Mass (m_τ/m_ρ ≈ 2 for resonance)
    c_tau: float = 0.7        # Wave speed (slower than ρ)
    lambda_tau: float = 1.0   # Self-interaction
    
    # Radiation branch (MASSLESS)
    c_phi: float = 2.0        # Wave speed (fastest - defines light cone)
    # No mass term for φ!
    
    # Coupling strengths
    g_rt: float = 0.5         # ρ-τ shell coupling
    g_tp: float = 0.1         # τ-φ threshold coupling
    g_rp: float = 0.02        # ρ-φ weak coupling
    
    def validate(self):
        """Check parameter constraints for stability."""
        assert self.lambda_rho > 0, "λ_ρ must be positive for stability"
        assert self.lambda_tau > 0, "λ_τ must be positive for stability"
        assert self.c_phi >= self.c_rho, "Radiation must be fastest: c_φ ≥ c_ρ"
        # c_tau can be slower - torsion stores energy, doesn't need to propagate fast
        return True
    
    def to_dict(self) -> Dict:
        return {
            'm_rho': self.m_rho, 'c_rho': self.c_rho, 'lambda_rho': self.lambda_rho,
            'm_tau': self.m_tau, 'c_tau': self.c_tau, 'lambda_tau': self.lambda_tau,
            'c_phi': self.c_phi,
            'g_rt': self.g_rt, 'g_tp': self.g_tp, 'g_rp': self.g_rp,
        }


class QMRTv3Engine:
    """
    Tri-branch field engine implementing the QMRT v3 Lagrangian.
    
    Fields:
      ρ(x,t): scalar compression/density
      τ(x,t): 3-component vector torsion
      φ(x,t): scalar radiation (massless)
    
    Each field has conjugate momentum (π_ρ, π_τᵢ, π_φ).
    Evolution uses Yoshida 4th-order symplectic integrator.
    """
    
    def __init__(self, grid_size: int = 32, params: Optional[QMRTv3Parameters] = None):
        self.grid_size = grid_size
        self.params = params or QMRTv3Parameters()
        self.params.validate()
        self.dx = 1.0
        self.time = 0.0
        
        n = grid_size
        
        # Compression field (scalar)
        self.rho = np.zeros((n, n, n))
        self.pi_rho = np.zeros((n, n, n))
        
        # Torsion field (vector: 3 components)
        self.tau = np.zeros((3, n, n, n))  # tau[i] = τ_i
        self.pi_tau = np.zeros((3, n, n, n))
        
        # Radiation field (scalar, massless)
        self.phi = np.zeros((n, n, n))
        self.pi_phi = np.zeros((n, n, n))
        
        # Precompute spectral Laplacian
        self._precompute_spectral()
        
        self.initial_energy = None
        self.history = []
    
    def _precompute_spectral(self):
        """Precompute k² for spectral Laplacian."""
        n = self.grid_size
        kx = np.fft.fftfreq(n, d=self.dx) * 2 * np.pi
        ky = np.fft.fftfreq(n, d=self.dx) * 2 * np.pi
        kz = np.fft.fftfreq(n, d=self.dx) * 2 * np.pi
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        self._k_sq = KX**2 + KY**2 + KZ**2
    
    def _spectral_laplacian(self, f: np.ndarray) -> np.ndarray:
        """Compute ∇²f using spectral method."""
        f_hat = np.fft.fftn(f)
        lap_hat = -self._k_sq * f_hat
        return np.real(np.fft.ifftn(lap_hat))
    
    def _compute_tau_squared(self) -> np.ndarray:
        """Compute τᵢτᵢ = |τ|²."""
        return self.tau[0]**2 + self.tau[1]**2 + self.tau[2]**2
    
    def _compute_phi_kinetic(self) -> np.ndarray:
        """Compute (∂_t φ)² - c²(∇φ)² for τ-φ coupling."""
        p = self.params
        
        # Time derivative squared (from momentum)
        phi_dot_sq = (self.pi_phi)**2  # ∂_t φ = π_φ
        
        # Spatial gradient squared
        lap_phi = self._spectral_laplacian(self.phi)
        grad_phi_sq = -self.phi * lap_phi  # |∇φ|² ≈ -φ·∇²φ (integration by parts)
        
        # Minkowski-like: (∂_t φ)² - c²|∇φ|²
        return phi_dot_sq - p.c_phi**2 * grad_phi_sq
    
    def compute_total_energy(self) -> Dict[str, float]:
        """Compute total energy broken down by component."""
        p = self.params
        dV = self.dx**3
        
        tau_sq = self._compute_tau_squared()
        
        # ===== Compression (ρ) energy =====
        E_rho_kinetic = 0.5 * np.sum(self.pi_rho**2) * dV
        
        lap_rho = self._spectral_laplacian(self.rho)
        E_rho_gradient = 0.5 * p.c_rho**2 * np.sum(-self.rho * lap_rho) * dV
        
        E_rho_mass = 0.5 * p.m_rho**2 * np.sum(self.rho**2) * dV
        E_rho_self = p.lambda_rho * np.sum(self.rho**4) * dV
        
        E_rho = E_rho_kinetic + E_rho_gradient + E_rho_mass + E_rho_self
        
        # ===== Torsion (τ) energy =====
        E_tau_kinetic = 0.5 * np.sum(self.pi_tau**2) * dV
        
        E_tau_gradient = 0.0
        for i in range(3):
            lap_tau_i = self._spectral_laplacian(self.tau[i])
            E_tau_gradient += 0.5 * p.c_tau**2 * np.sum(-self.tau[i] * lap_tau_i) * dV
        
        E_tau_mass = 0.5 * p.m_tau**2 * np.sum(tau_sq) * dV
        E_tau_self = p.lambda_tau * np.sum(tau_sq**2) * dV
        
        E_tau = E_tau_kinetic + E_tau_gradient + E_tau_mass + E_tau_self
        
        # ===== Radiation (φ) energy =====
        E_phi_kinetic = 0.5 * np.sum(self.pi_phi**2) * dV
        
        lap_phi = self._spectral_laplacian(self.phi)
        E_phi_gradient = 0.5 * p.c_phi**2 * np.sum(-self.phi * lap_phi) * dV
        # No mass term for φ!
        
        E_phi = E_phi_kinetic + E_phi_gradient
        
        # ===== Coupling energies =====
        E_rt = p.g_rt * np.sum(self.rho * tau_sq) * dV
        
        phi_kinetic_density = self._compute_phi_kinetic()
        E_tp = p.g_tp * np.sum(tau_sq * phi_kinetic_density) * dV
        
        E_rp = p.g_rp * np.sum(self.rho * self.phi) * dV
        
        E_coupling = E_rt + E_tp + E_rp
        
        E_total = E_rho + E_tau + E_phi + E_coupling
        
        return {
            'E_rho': E_rho,
            'E_tau': E_tau,
            'E_phi': E_phi,
            'E_coupling': E_coupling,
            'E_rt': E_rt,
            'E_tp': E_tp,
            'E_rp': E_rp,
            'E_total': E_total,
        }
    
    def _compute_forces(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute forces on all fields from the Euler-Lagrange equations.
        
        F_ρ = c_ρ²∇²ρ - m_ρ²ρ - 4λ_ρρ³ - g_rt(τᵢτᵢ) - g_rp·φ
        F_τᵢ = c_τ²∇²τᵢ - m_τ²τᵢ - 4λ_τ(τⱼτⱼ)τᵢ - 2g_rt·ρ·τᵢ - 2g_tp·τᵢ·(∂_μφ∂^μφ)
        F_φ = c_φ²∇²φ - g_rp·ρ + [τ-φ coupling terms]
        """
        p = self.params
        
        tau_sq = self._compute_tau_squared()
        
        # ===== ρ force =====
        lap_rho = self._spectral_laplacian(self.rho)
        
        F_rho = (p.c_rho**2 * lap_rho 
                 - p.m_rho**2 * self.rho 
                 - 4 * p.lambda_rho * self.rho**3
                 - p.g_rt * tau_sq
                 - p.g_rp * self.phi)
        
        # ===== τ force (vector) =====
        F_tau = np.zeros_like(self.tau)
        
        phi_kinetic = self._compute_phi_kinetic()
        
        for i in range(3):
            lap_tau_i = self._spectral_laplacian(self.tau[i])
            
            F_tau[i] = (p.c_tau**2 * lap_tau_i
                        - p.m_tau**2 * self.tau[i]
                        - 4 * p.lambda_tau * tau_sq * self.tau[i]
                        - 2 * p.g_rt * self.rho * self.tau[i]
                        - 2 * p.g_tp * self.tau[i] * phi_kinetic)
        
        # ===== φ force =====
        lap_phi = self._spectral_laplacian(self.phi)
        
        # Basic wave equation + ρ coupling
        F_phi = p.c_phi**2 * lap_phi - p.g_rp * self.rho
        
        # τ-φ coupling: adds effective mass from torsion
        # Simplified: -2g_tp·(τᵢτᵢ)·c_φ²·∇²φ contribution
        F_phi += 2 * p.g_tp * tau_sq * p.c_phi**2 * lap_phi
        
        return F_rho, F_tau, F_phi
    
    def evolve_timestep(self, dt: float):
        """Evolve all fields using Yoshida 4th-order symplectic integrator."""
        
        # Yoshida4 coefficients
        w1 = 1.0 / (2 - 2**(1/3))
        w0 = -2**(1/3) * w1
        c = [w1/2, (w0+w1)/2, (w0+w1)/2, w1/2]
        d = [w1, w0, w1]
        
        for step in range(4):
            # Position update (all fields)
            self.rho += c[step] * dt * self.pi_rho
            self.tau += c[step] * dt * self.pi_tau
            self.phi += c[step] * dt * self.pi_phi
            
            # Momentum update (except last)
            if step < 3:
                F_rho, F_tau, F_phi = self._compute_forces()
                self.pi_rho += d[step] * dt * F_rho
                self.pi_tau += d[step] * dt * F_tau
                self.pi_phi += d[step] * dt * F_phi
        
        self.time += dt
    
    def initialize_torsion_perturbation(self, 
                                        center: Tuple[int, int, int] = None,
                                        amplitude: float = 1.0,
                                        radius: float = 2.0,
                                        direction: Tuple[float, float, float] = (0, 0, 1)):
        """
        Initialize a Gaussian torsion perturbation.
        
        τ(r, 0) = A_τ · n̂ · exp(-r²/2R²)
        
        where n̂ is the direction unit vector.
        """
        n = self.grid_size
        if center is None:
            center = (n // 2, n // 2, n // 2)
        
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        cx, cy, cz = center
        R_sq = (X - cx)**2 + (Y - cy)**2 + (Z - cz)**2
        
        # Gaussian envelope
        envelope = amplitude * np.exp(-R_sq / (2 * radius**2))
        
        # Normalize direction
        norm = np.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
        n_hat = (direction[0]/norm, direction[1]/norm, direction[2]/norm)
        
        # Set torsion components
        self.tau[0] = n_hat[0] * envelope
        self.tau[1] = n_hat[1] * envelope
        self.tau[2] = n_hat[2] * envelope
        
        # Zero momenta
        self.pi_tau = np.zeros_like(self.tau)
        
        # Store initial energy
        self.initial_energy = self.compute_total_energy()['E_total']
    
    def initialize_vacuum(self):
        """Initialize to vacuum state: ρ = 0, τ = 0, φ = 0."""
        n = self.grid_size
        
        self.rho = np.zeros((n, n, n))
        self.pi_rho = np.zeros((n, n, n))
        
        self.tau = np.zeros((3, n, n, n))
        self.pi_tau = np.zeros((3, n, n, n))
        
        self.phi = np.zeros((n, n, n))
        self.pi_phi = np.zeros((n, n, n))
        
        self.initial_energy = 0.0
    
    def measure_torsion_radius(self) -> float:
        """Compute RMS radius of torsion distribution."""
        n = self.grid_size
        x = np.arange(n) - n/2
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = X**2 + Y**2 + Z**2
        
        tau_sq = self._compute_tau_squared()
        total = np.sum(tau_sq)
        
        if total < 1e-10:
            return 0.0
        
        return np.sqrt(np.sum(R_sq * tau_sq) / total)
    
    def measure_core_energy(self, core_radius_factor: float = 2.0) -> float:
        """Compute energy within core_radius_factor × initial radius."""
        n = self.grid_size
        x = np.arange(n) - n/2
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R = np.sqrt(X**2 + Y**2 + Z**2)
        
        # Initial radius (stored or computed)
        R_initial = 2.0  # From initialization
        R_core = core_radius_factor * R_initial
        
        mask = R < R_core
        
        # Simplified: just torsion energy in core
        tau_sq = self._compute_tau_squared()
        p = self.params
        
        E_tau_core = (0.5 * np.sum(self.pi_tau[:, mask]**2) +
                      0.5 * p.m_tau**2 * np.sum(tau_sq[mask]) +
                      p.lambda_tau * np.sum(tau_sq[mask]**2))
        
        return E_tau_core * self.dx**3
    
    def measure_radiation_energy(self) -> float:
        """Compute total energy in φ field."""
        energies = self.compute_total_energy()
        return energies['E_phi']
    
    def get_state_summary(self) -> Dict:
        """Get summary of current state for analysis."""
        energies = self.compute_total_energy()
        
        tau_sq = self._compute_tau_squared()
        
        return {
            'time': self.time,
            'energies': energies,
            'torsion_max': float(np.max(np.sqrt(tau_sq))),
            'torsion_radius': self.measure_torsion_radius(),
            'density_max': float(np.max(np.abs(self.rho))),
            'radiation_max': float(np.max(np.abs(self.phi))),
            'energy_drift': (energies['E_total'] - self.initial_energy) / max(self.initial_energy, 1e-10),
        }
    
    def run_simulation(self, dt: float = 0.01, n_steps: int = 1000, 
                       record_interval: int = 10) -> Dict:
        """Run full simulation and record history."""
        self.history = []
        
        for step in range(n_steps):
            if step % record_interval == 0:
                self.history.append(self.get_state_summary())
            
            self.evolve_timestep(dt)
        
        # Final state
        self.history.append(self.get_state_summary())
        
        return self.analyze_stability()
    
    def analyze_stability(self) -> Dict:
        """Analyze if the simulation produced a stable particle."""
        if len(self.history) < 2:
            return {'stable': False, 'reason': 'insufficient_data'}
        
        initial = self.history[0]
        final = self.history[-1]
        
        R_0 = initial['torsion_radius']
        R_f = final['torsion_radius']
        
        E_total_0 = initial['energies']['E_total']
        E_phi_f = final['energies']['E_phi']
        
        # Stability criteria
        radius_bounded = R_f / max(R_0, 0.1) < 2.0
        energy_conserved = abs(final['energy_drift']) < 0.1
        low_radiation = E_phi_f / max(E_total_0, 1e-10) < 0.2
        
        # Check for runaway
        torsion_history = [h['torsion_max'] for h in self.history]
        no_blowup = max(torsion_history) < 10 * initial['torsion_max']
        
        stable = radius_bounded and energy_conserved and low_radiation and no_blowup
        
        return {
            'stable': stable,
            'radius_bounded': radius_bounded,
            'energy_conserved': energy_conserved,
            'low_radiation': low_radiation,
            'no_blowup': no_blowup,
            'R_ratio': R_f / max(R_0, 0.1),
            'energy_drift': final['energy_drift'],
            'radiation_fraction': E_phi_f / max(E_total_0, 1e-10),
            'max_torsion_ratio': max(torsion_history) / max(initial['torsion_max'], 1e-10),
        }


def test_qmrt_v3_baseline():
    """Test the baseline configuration from parameter guide."""
    print("=" * 70)
    print("QMRT v3: Baseline Configuration Test")
    print("=" * 70)
    
    params = QMRTv3Parameters(
        m_rho=1.0, c_rho=1.0, lambda_rho=1.0,
        m_tau=2.0, c_tau=0.7, lambda_tau=1.0,
        c_phi=2.0,
        g_rt=0.5, g_tp=0.1, g_rp=0.02,
    )
    
    print("\nParameters:")
    for k, v in params.to_dict().items():
        print(f"  {k}: {v}")
    
    engine = QMRTv3Engine(grid_size=24, params=params)
    
    # Initialize torsion perturbation
    engine.initialize_vacuum()
    engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
    
    print(f"\nInitial state:")
    initial = engine.get_state_summary()
    print(f"  Torsion max: {initial['torsion_max']:.4f}")
    print(f"  Torsion radius: {initial['torsion_radius']:.4f}")
    print(f"  Total energy: {initial['energies']['E_total']:.4f}")
    
    # Run simulation
    print("\nRunning simulation (1000 steps, dt=0.01)...")
    results = engine.run_simulation(dt=0.01, n_steps=1000, record_interval=50)
    
    print(f"\nFinal state:")
    final = engine.history[-1]
    print(f"  Torsion max: {final['torsion_max']:.4f}")
    print(f"  Torsion radius: {final['torsion_radius']:.4f}")
    print(f"  Total energy: {final['energies']['E_total']:.4f}")
    print(f"  Energy drift: {final['energy_drift']:.2%}")
    
    print(f"\nStability analysis:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    
    if results['stable']:
        print("\n✅ STABLE PARTICLE CANDIDATE DETECTED!")
    else:
        print("\n❌ Not stable with these parameters")
    
    return engine, results


def scan_shell_coupling():
    """Scan Γ_rt to find the shell formation window."""
    print("\n" + "=" * 70)
    print("QMRT v3: Shell Coupling Scan (Γ_rt)")
    print("=" * 70)
    
    g_rt_values = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.2]
    
    print(f"\n{'Γ_rt':>8} | {'R_ratio':>8} | {'E_drift':>10} | {'φ_frac':>8} | {'Stable':>8}")
    print("-" * 55)
    
    for g_rt in g_rt_values:
        params = QMRTv3Parameters(g_rt=g_rt)
        engine = QMRTv3Engine(grid_size=20, params=params)
        
        engine.initialize_vacuum()
        engine.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
        
        results = engine.run_simulation(dt=0.01, n_steps=500, record_interval=50)
        
        status = "YES" if results['stable'] else "no"
        print(f"{g_rt:8.2f} | {results['R_ratio']:8.2f} | {results['energy_drift']:10.2%} | "
              f"{results['radiation_fraction']:8.2%} | {status:>8}")
    
    print("\nLook for the 'shell formation window' where particles are stable.")


if __name__ == "__main__":
    # Run baseline test
    engine, results = test_qmrt_v3_baseline()
    
    # Scan shell coupling
    scan_shell_coupling()
