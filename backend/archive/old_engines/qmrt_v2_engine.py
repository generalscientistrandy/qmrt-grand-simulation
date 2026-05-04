"""
QMRT v2: Two-Field Substrate Theory
═══════════════════════════════════

The minimal upgrade to achieve:
  ✓ Keep confinement behavior (ω field)
  ✓ Add acoustic propagation (φ field)
  ✓ Enable emergent relativistic dispersion

TWO-FIELD STRUCTURE:
  ω(x,t) = ordering field (medium structure, double-well)
  φ(x,t) = propagating field (information carrier, massless/light)

COUPLED LAGRANGIAN:
  ℒ = ℒ_ω + ℒ_φ + ℒ_int

  ℒ_ω = (M_ω/2)(∂_t ω)² - (K_ω/2)|∇ω|² - a(ω² - ω₀²)²
  ℒ_φ = (M_φ/2)(∂_t φ)² - (K_φ/2)|∇φ|² - (m_φ²/2)φ²
  ℒ_int = -g·ω²·φ²  (coupling)

This gives:
  - ω: optical phonon (confinement, domain walls)
  - φ: acoustic/propagating (with speed c_φ = √(K_φ/M_φ))
  - Coupling: φ propagation modified by ω structure
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Dict, Optional


@dataclass
class QMRTv2Parameters:
    """Parameters for the two-field QMRT v2 system"""
    
    # ω field (ordering/structure) - same as v1
    M_omega: float = 1.0      # Field mass
    K_omega: float = 0.05     # Gradient coefficient
    a_omega: float = 1.0      # Double-well depth
    omega_0: float = 1.0      # Basin center
    
    # φ field (propagating mode) - NEW
    M_phi: float = 1.0        # Field mass
    K_phi: float = 1.0        # Gradient coefficient (determines wave speed!)
    m_phi_sq: float = 0.01    # Mass term (small for nearly massless)
    
    # Coupling
    g_coupling: float = 0.1   # ω-φ interaction strength
    
    @property
    def c_phi(self) -> float:
        """Speed of φ waves: c = √(K_φ/M_φ)"""
        return np.sqrt(self.K_phi / self.M_phi)
    
    @property
    def omega_gap(self) -> float:
        """Gap frequency for ω field"""
        return np.sqrt(8 * self.a_omega * self.omega_0**2 / self.M_omega)


class QMRTv2Engine:
    """
    Two-field QMRT engine with:
      - ω(x,t): ordering field (optical phonon, confinement)
      - φ(x,t): propagating field (acoustic, information carrier)
    
    Equations of motion:
      M_ω·∂²ω/∂t² = K_ω·∇²ω - 4a·ω(ω² - ω₀²) - 2g·ω·φ²
      M_φ·∂²φ/∂t² = K_φ·∇²φ - m²_φ·φ - 2g·ω²·φ
    """
    
    def __init__(self, grid_size: int = 16, params: Optional[QMRTv2Parameters] = None):
        self.grid_size = grid_size
        self.params = params or QMRTv2Parameters()
        self.dx = 1.0
        self.time = 0.0
        
        n = grid_size
        p = self.params
        
        # ω field and momentum
        self.omega = np.ones((n, n, n)) * p.omega_0
        self.pi_omega = np.zeros((n, n, n))
        
        # φ field and momentum (NEW)
        self.phi = np.zeros((n, n, n))
        self.pi_phi = np.zeros((n, n, n))
        
        # Precompute spectral Laplacian
        self._precompute_spectral()
        
        self.initial_energy = None
    
    def _precompute_spectral(self):
        """Precompute k² for spectral Laplacian"""
        n = self.grid_size
        kx = np.fft.fftfreq(n, d=self.dx) * 2 * np.pi
        ky = np.fft.fftfreq(n, d=self.dx) * 2 * np.pi
        kz = np.fft.fftfreq(n, d=self.dx) * 2 * np.pi
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        self._k_sq = KX**2 + KY**2 + KZ**2
    
    def _spectral_laplacian(self, f: np.ndarray) -> np.ndarray:
        """Compute ∇²f using spectral method"""
        f_hat = np.fft.fftn(f)
        lap_hat = -self._k_sq * f_hat
        return np.real(np.fft.ifftn(lap_hat))
    
    def compute_total_energy(self) -> float:
        """Compute total energy of both fields"""
        p = self.params
        
        # ω field energy
        E_omega_kinetic = 0.5 * np.sum(self.pi_omega**2) / p.M_omega * self.dx**3
        
        lap_omega = self._spectral_laplacian(self.omega)
        E_omega_gradient = -0.5 * p.K_omega * np.sum(self.omega * lap_omega) * self.dx**3
        
        V_omega = p.a_omega * (self.omega**2 - p.omega_0**2)**2
        E_omega_potential = np.sum(V_omega) * self.dx**3
        
        # φ field energy (NEW)
        E_phi_kinetic = 0.5 * np.sum(self.pi_phi**2) / p.M_phi * self.dx**3
        
        lap_phi = self._spectral_laplacian(self.phi)
        E_phi_gradient = -0.5 * p.K_phi * np.sum(self.phi * lap_phi) * self.dx**3
        
        E_phi_mass = 0.5 * p.m_phi_sq * np.sum(self.phi**2) * self.dx**3
        
        # Coupling energy
        E_coupling = p.g_coupling * np.sum(self.omega**2 * self.phi**2) * self.dx**3
        
        return (E_omega_kinetic + E_omega_gradient + E_omega_potential +
                E_phi_kinetic + E_phi_gradient + E_phi_mass + E_coupling)
    
    def _compute_forces(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute forces on both fields"""
        p = self.params
        
        # ω field force: F_ω = K_ω·∇²ω - V'(ω) - ∂V_int/∂ω
        lap_omega = self._spectral_laplacian(self.omega)
        
        # Double-well: V'(ω) = 4a·ω(ω² - ω₀²)
        dV_omega = 4 * p.a_omega * self.omega * (self.omega**2 - p.omega_0**2)
        
        # Coupling: ∂(g·ω²·φ²)/∂ω = 2g·ω·φ²
        dV_coupling_omega = 2 * p.g_coupling * self.omega * self.phi**2
        
        F_omega = p.K_omega * lap_omega - dV_omega - dV_coupling_omega
        
        # φ field force: F_φ = K_φ·∇²φ - m²_φ·φ - ∂V_int/∂φ
        lap_phi = self._spectral_laplacian(self.phi)
        
        # Mass term
        dV_phi = p.m_phi_sq * self.phi
        
        # Coupling: ∂(g·ω²·φ²)/∂φ = 2g·ω²·φ
        dV_coupling_phi = 2 * p.g_coupling * self.omega**2 * self.phi
        
        F_phi = p.K_phi * lap_phi - dV_phi - dV_coupling_phi
        
        return F_omega, F_phi
    
    def evolve_timestep(self, dt: float):
        """Evolve both fields using Yoshida4 symplectic integrator"""
        p = self.params
        
        # Yoshida4 coefficients
        w1 = 1.0 / (2 - 2**(1/3))
        w0 = -2**(1/3) * w1
        c = [w1/2, (w0+w1)/2, (w0+w1)/2, w1/2]
        d = [w1, w0, w1]
        
        for i in range(4):
            # Position update
            self.omega += c[i] * dt * self.pi_omega / p.M_omega
            self.phi += c[i] * dt * self.pi_phi / p.M_phi
            
            # Momentum update (except last)
            if i < 3:
                F_omega, F_phi = self._compute_forces()
                self.pi_omega += d[i] * dt * F_omega
                self.pi_phi += d[i] * dt * F_phi
        
        self.time += dt
    
    def initialize_uniform_omega(self, phase: str = 'high'):
        """Initialize ω to uniform state (no domain walls)"""
        p = self.params
        n = self.grid_size
        
        if phase == 'high':
            self.omega = np.ones((n, n, n)) * p.omega_0
        else:
            self.omega = np.ones((n, n, n)) * (-p.omega_0)
        
        self.pi_omega = np.zeros((n, n, n))
        self.phi = np.zeros((n, n, n))
        self.pi_phi = np.zeros((n, n, n))
        
        self.initial_energy = self.compute_total_energy()
    
    def create_phi_wave(self, k_mode: int, amplitude: float = 0.1):
        """Create a propagating φ wave with wavenumber k"""
        n = self.grid_size
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        k = 2 * np.pi * k_mode / n
        self.phi = amplitude * np.sin(k * X)
    
    def create_phi_packet(self, center: Tuple[int, int, int], 
                         width: float = 2.0, amplitude: float = 0.1,
                         momentum: Tuple[float, float, float] = (0, 0, 0)):
        """Create a localized φ wave packet"""
        n = self.grid_size
        p = self.params
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        cx, cy, cz = center
        R_sq = (X - cx)**2 + (Y - cy)**2 + (Z - cz)**2
        
        # Gaussian envelope
        self.phi = amplitude * np.exp(-R_sq / (2 * width**2))
        
        # Add momentum
        px, py, pz = momentum
        if any(m != 0 for m in momentum):
            grad_x = -self.phi * (X - cx) / (width**2)
            grad_y = -self.phi * (Y - cy) / (width**2)
            grad_z = -self.phi * (Z - cz) / (width**2)
            
            self.pi_phi = px * grad_x + py * grad_y + pz * grad_z


def test_qmrt_v2_dispersion():
    """Test if φ field has acoustic dispersion ω ~ k"""
    from scipy.fft import fft, fftfreq
    
    print("="*70)
    print("QMRT v2: Testing φ field dispersion")
    print("="*70)
    print("Goal: Check if φ has ω ~ ck (acoustic) instead of ω = const (optical)")
    print("="*70)
    
    params = QMRTv2Parameters(K_phi=1.0, m_phi_sq=0.01)
    print(f"\nParameters: K_φ = {params.K_phi}, M_φ = {params.M_phi}")
    print(f"Expected c_φ = √(K_φ/M_φ) = {params.c_phi:.4f}")
    print()
    
    results = []
    
    for k_mode in [1, 2, 3, 4]:
        engine = QMRTv2Engine(grid_size=12, params=params)
        engine.initialize_uniform_omega(phase='high')
        
        # Create φ wave with specific k
        k = 2 * np.pi * k_mode / 12
        engine.create_phi_wave(k_mode, amplitude=0.1)
        
        # Track φ at center
        center = 6
        history = []
        for step in range(150):
            engine.evolve_timestep(0.01)
            if step % 3 == 0:
                history.append(engine.phi[center, center, center])
        
        # FFT to get frequency
        arr = np.array(history) - np.mean(history)
        spectrum = np.abs(fft(arr))**2
        freqs = fftfreq(len(arr), d=0.03)
        
        pos = freqs > 0.05
        if np.any(pos):
            omega = 2 * np.pi * freqs[pos][np.argmax(spectrum[pos])]
        else:
            omega = 0
        
        omega_theory = np.sqrt(params.c_phi**2 * k**2 + params.m_phi_sq)
        
        results.append({'k': k, 'omega': omega, 'omega_theory': omega_theory})
        print(f"k_mode={k_mode}: k={k:.3f}, ω_meas={omega:.3f}, ω_theory={omega_theory:.3f}")
    
    # Check if ω ~ k (acoustic) or ω ~ const (optical)
    k_arr = np.array([r['k'] for r in results])
    omega_arr = np.array([r['omega'] for r in results])
    
    from scipy.stats import linregress
    slope, intercept, r_value, _, _ = linregress(k_arr, omega_arr)
    
    print(f"\nLinear fit: ω = {slope:.3f}·k + {intercept:.3f}")
    print(f"R² = {r_value**2:.4f}")
    print(f"Effective c = {slope:.4f} (theory: {params.c_phi:.4f})")
    
    if r_value**2 > 0.9 and slope > 0.5 * params.c_phi:
        print("\n✅ ACOUSTIC DISPERSION CONFIRMED!")
        print("   φ field propagates with ω ~ c·k")
        print("   → This is the missing propagation sector!")
    else:
        print("\n❌ Dispersion check failed")
    
    return results


def test_qmrt_v2_two_branches():
    """Test that v2 has BOTH optical (ω) and acoustic (φ) branches"""
    from scipy.fft import fft, fftfreq
    
    print("\n" + "="*70)
    print("QMRT v2: Testing TWO-BRANCH structure")
    print("="*70)
    
    params = QMRTv2Parameters()
    engine = QMRTv2Engine(grid_size=12, params=params)
    engine.initialize_uniform_omega(phase='high')
    
    # Test ω field (should be optical = flat)
    print("\n--- ω field (ordering/confinement) ---")
    
    omega_results = []
    for k_mode in [1, 2, 3]:
        engine_omega = QMRTv2Engine(grid_size=12, params=params)
        engine_omega.initialize_uniform_omega(phase='high')
        
        # Perturb ω
        x = np.arange(12)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        k = 2 * np.pi * k_mode / 12
        engine_omega.omega += 0.02 * params.omega_0 * np.sin(k * X)
        
        center = 6
        history = []
        for step in range(100):
            engine_omega.evolve_timestep(0.01)
            if step % 2 == 0:
                history.append(engine_omega.omega[center, center, center] - params.omega_0)
        
        arr = np.array(history) - np.mean(history)
        spectrum = np.abs(fft(arr))**2
        freqs = fftfreq(len(arr), d=0.02)
        
        pos = freqs > 0.05
        omega_freq = 2 * np.pi * freqs[pos][np.argmax(spectrum[pos])] if np.any(pos) else 0
        omega_results.append({'k': k, 'omega': omega_freq})
        print(f"  k={k:.3f}: ω = {omega_freq:.3f}")
    
    # Test φ field (should be acoustic = linear)
    print("\n--- φ field (propagating/information) ---")
    
    phi_results = []
    for k_mode in [1, 2, 3]:
        engine_phi = QMRTv2Engine(grid_size=12, params=params)
        engine_phi.initialize_uniform_omega(phase='high')
        
        k = 2 * np.pi * k_mode / 12
        engine_phi.create_phi_wave(k_mode, amplitude=0.1)
        
        center = 6
        history = []
        for step in range(100):
            engine_phi.evolve_timestep(0.01)
            if step % 2 == 0:
                history.append(engine_phi.phi[center, center, center])
        
        arr = np.array(history) - np.mean(history)
        spectrum = np.abs(fft(arr))**2
        freqs = fftfreq(len(arr), d=0.02)
        
        pos = freqs > 0.05
        phi_freq = 2 * np.pi * freqs[pos][np.argmax(spectrum[pos])] if np.any(pos) else 0
        phi_results.append({'k': k, 'omega': phi_freq})
        print(f"  k={k:.3f}: ω = {phi_freq:.3f}")
    
    # Analysis
    print("\n--- BRANCH ANALYSIS ---")
    
    omega_freqs = [r['omega'] for r in omega_results]
    phi_freqs = [r['omega'] for r in phi_results]
    
    omega_std = np.std(omega_freqs)
    omega_mean = np.mean(omega_freqs)
    
    from scipy.stats import linregress
    k_arr = np.array([r['k'] for r in phi_results])
    phi_arr = np.array(phi_freqs)
    slope, _, r_value, _, _ = linregress(k_arr, phi_arr)
    
    print(f"\nω field: ω = {omega_mean:.3f} ± {omega_std:.3f} (CV = {omega_std/omega_mean:.2%})")
    print(f"  → {'OPTICAL (flat)' if omega_std/omega_mean < 0.1 else 'NOT optical'}")
    
    print(f"\nφ field: ω ≈ {slope:.3f}·k (R² = {r_value**2:.3f})")
    print(f"  → {'ACOUSTIC (linear)' if r_value**2 > 0.8 else 'NOT acoustic'}")
    
    if omega_std/omega_mean < 0.1 and r_value**2 > 0.8:
        print("\n" + "="*70)
        print("✅ TWO-BRANCH STRUCTURE CONFIRMED!")
        print("="*70)
        print("""
  ω field: OPTICAL branch (ω ≈ const, v_g ≈ 0)
           → Confinement, domain walls, localization
           
  φ field: ACOUSTIC branch (ω ≈ c·k, v_g = c)
           → Propagation, information transport, light-cone
           
  This is the structure needed for emergent relativistic physics!
""")
    
    return omega_results, phi_results


if __name__ == "__main__":
    test_qmrt_v2_dispersion()
    test_qmrt_v2_two_branches()
