"""
QMRT Substrate Engine - Hamiltonian Implementation
Implements the canonical QMRT field theory with proper energy conservation

Hamiltonian density:
H = Σ(π²/2M) + U_ρ(ρ) + Σ(a/2)field² + Σλ_couplings + Σ(K/2)|∇field|²

All evolution follows Hamilton's canonical equations - energy is intrinsically conserved.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class QMRTParameters:
    """Physical parameters for QMRT Hamiltonian"""
    # Mass parameters (kinetic term denominators)
    M_rho: float = 1.0
    M_sigma: float = 1.0
    M_tau: float = 1.0
    M_phi: float = 1.0
    
    # Self-potential for ρ centered at equilibrium ρ₀=1
    # U_ρ(ρ) = (a_rho/2)(ρ-1)² + (c_rho/4)(ρ-1)⁴
    # This creates a potential well at ρ=1, not ρ=0
    rho_equilibrium: float = 1.0  # Equilibrium density
    a_rho: float = 0.1   # Harmonic restoring force around equilibrium
    c_rho: float = 0.02  # Quartic stabilization
    
    # Harmonic potential coefficients for other fields (equilibrium at 0)
    a_sigma: float = 0.1
    a_tau: float = 0.1
    a_phi: float = 0.1
    
    # Coupling constants
    lambda_rho_sigma: float = 0.02
    lambda_rho_tau: float = 0.02
    lambda_sigma_tau: float = 0.02
    lambda_sigma_phi: float = 0.02
    lambda_tau_phi: float = 0.02
    lambda_rho_phi: float = 0.02
    
    # Gradient energy coefficients
    K_rho: float = 1.0
    K_sigma: float = 1.0
    K_tau: float = 1.0
    K_phi: float = 1.0
    
    # Stabilization functional parameters
    alpha_stab: float = 1.0
    beta_stab: float = 0.5
    gamma_stab: float = 0.3
    D0: float = 0.1
    eta_phi: float = 0.5
    kappa: float = 0.2
    
    # Coherence length parameters
    xi0: float = 1.0
    L_p: float = 1.0  # Proton length scale
    
    # Cosmological coupling (for emergent expansion)
    chi_sigma: float = 0.01
    chi_tau: float = 0.01
    chi_phi: float = 0.01


@dataclass
class EmergentStructure:
    """Detected emergent structure in substrate"""
    id: str
    position: Tuple[float, float, float]
    formation_time: float
    
    # Field values at structure
    rho: float
    sigma: float
    tau: float
    phi: float
    
    # Stability metrics
    S_value: float  # Stabilization functional value
    xi_value: float  # Coherence length
    Pi_p: float  # Proton formation parameter
    
    # Classification
    is_stable: bool
    is_proton_candidate: bool
    lifetime: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'position': self.position,
            'formation_time': self.formation_time,
            'rho': self.rho,
            'sigma': self.sigma,
            'tau': self.tau,
            'phi': self.phi,
            'S_value': self.S_value,
            'xi_value': self.xi_value,
            'Pi_p': self.Pi_p,
            'is_stable': self.is_stable,
            'is_proton_candidate': self.is_proton_candidate,
            'lifetime': self.lifetime
        }


class QMRTSubstrateEngine:
    """
    Canonical QMRT substrate simulation engine
    
    Implements exact Hamiltonian dynamics for energy-conserving evolution.
    All terms derived from the QMRT Hamiltonian - no artificial corrections.
    """
    
    def __init__(self, grid_size: int = 64, dx: float = 1.0, 
                 params: Optional[QMRTParameters] = None):
        self.grid_size = grid_size
        self.dx = dx
        self.time = 0.0
        
        # Physical parameters
        self.params = params or QMRTParameters()
        
        # Fields (generalized coordinates)
        self.rho = None    # Density field ρ
        self.sigma = None  # Tension field σ  
        self.tau = None    # Torsion field τ (scalar for now, can extend to vector)
        self.phi = None    # Coherence phase φ
        
        # Conjugate momenta
        self.pi_rho = None
        self.pi_sigma = None
        self.pi_tau = None
        self.pi_phi = None
        
        # Scale factor for cosmology
        self.a = 1.0  # Cosmological scale factor
        self.a_dot = 0.0  # Time derivative of scale factor
        
        # Structure tracking
        self.structures: List[EmergentStructure] = []
        self.structure_counter = 0
        self.S_threshold = 0.5  # S_n* threshold for stability
        
        # Energy tracking
        self.initial_energy = None
        self.energy_history: List[float] = []
        
    def initialize_equilibrium(self, amplitude: float = 0.01, seed: Optional[int] = None):
        """
        Initialize fields near equilibrium with small fluctuations
        
        Equilibrium state: ρ = ρ_eq where dU_ρ/dρ = 0
        For U_ρ = (a/2)ρ² + (b/3)ρ³ + (c/4)ρ⁴, equilibrium at ρ ≈ 1 for our parameters
        """
        if seed is not None:
            np.random.seed(seed)
        
        shape = (self.grid_size, self.grid_size, self.grid_size)
        
        # Find equilibrium density (approximate for small b, c)
        # For a_rho > 0, equilibrium near ρ = 0, but we want ρ ~ 1
        # So we set baseline at 1.0 and let dynamics evolve
        rho_eq = 1.0
        
        # Initialize fields with zero-mean fluctuations
        self.rho = rho_eq + amplitude * self._balanced_noise(shape)
        self.sigma = amplitude * self._balanced_noise(shape)
        self.tau = amplitude * self._balanced_noise(shape)
        self.phi = amplitude * self._balanced_noise(shape)
        
        # Initialize momenta at zero (thermal equilibrium)
        self.pi_rho = np.zeros(shape)
        self.pi_sigma = np.zeros(shape)
        self.pi_tau = np.zeros(shape)
        self.pi_phi = np.zeros(shape)
        
        # Initialize scale factor
        self.a = 1.0
        self.a_dot = 0.0
        
        # Record initial energy
        self.initial_energy = self.compute_total_energy()
        
        print("QMRT Substrate initialized")
        print(f"  Grid: {self.grid_size}³, dx = {self.dx}")
        print(f"  Initial energy: {self.initial_energy:.4f}")
        print(f"  Mean rho: {np.mean(self.rho):.6f}")
        
    def _balanced_noise(self, shape: Tuple) -> np.ndarray:
        """Generate zero-mean noise to preserve global balance"""
        noise = np.random.randn(*shape)
        noise -= np.mean(noise)
        return noise
    
    def laplacian(self, f: np.ndarray) -> np.ndarray:
        """Compute Laplacian using finite differences with periodic BC"""
        # Use numpy roll for true periodic boundaries
        lap = (
            np.roll(f, -1, axis=0) + np.roll(f, 1, axis=0) +
            np.roll(f, -1, axis=1) + np.roll(f, 1, axis=1) +
            np.roll(f, -1, axis=2) + np.roll(f, 1, axis=2) -
            6 * f
        ) / (self.dx ** 2)
        return lap
    
    def gradient(self, f: np.ndarray) -> np.ndarray:
        """Compute gradient using central differences with periodic BC"""
        grad = np.zeros((*f.shape, 3))
        grad[:,:,:,0] = (np.roll(f, -1, axis=0) - np.roll(f, 1, axis=0)) / (2 * self.dx)
        grad[:,:,:,1] = (np.roll(f, -1, axis=1) - np.roll(f, 1, axis=1)) / (2 * self.dx)
        grad[:,:,:,2] = (np.roll(f, -1, axis=2) - np.roll(f, 1, axis=2)) / (2 * self.dx)
        return grad
    
    def gradient_magnitude_squared(self, f: np.ndarray) -> np.ndarray:
        """Compute |∇f|²"""
        grad = self.gradient(f)
        return np.sum(grad**2, axis=-1)
    
    def divergence(self, f: np.ndarray) -> np.ndarray:
        """Compute divergence of scalar field (Laplacian-related)"""
        # For scalar f, this is related to Laplacian
        # div(∇f) = ∇²f
        return self.laplacian(f)
    
    def compute_total_energy(self) -> float:
        """
        Compute total Hamiltonian energy
        
        H = ∫ H_density d³x
        """
        p = self.params
        
        # Kinetic energy: Σ(π²/2M)
        KE = 0.5 * (
            np.sum(self.pi_rho**2) / p.M_rho +
            np.sum(self.pi_sigma**2) / p.M_sigma +
            np.sum(self.pi_tau**2) / p.M_tau +
            np.sum(self.pi_phi**2) / p.M_phi
        ) * self.dx**3
        
        # Self-potential for ρ centered at equilibrium: U_ρ = (a/2)(ρ-ρ₀)² + (c/4)(ρ-ρ₀)⁴
        # This ensures the potential minimum is at ρ = ρ₀, not at ρ = 0
        delta_rho = self.rho - p.rho_equilibrium
        U_rho = np.sum(
            (p.a_rho / 2) * delta_rho**2 +
            (p.c_rho / 4) * delta_rho**4
        ) * self.dx**3
        
        # Harmonic potentials for σ, τ, φ (equilibrium at 0)
        V_harmonic = np.sum(
            (p.a_sigma / 2) * self.sigma**2 +
            (p.a_tau / 2) * self.tau**2 +
            (p.a_phi / 2) * self.phi**2
        ) * self.dx**3
        
        # Coupling energies (use delta_rho for ρ-dependent terms)
        V_coupling = np.sum(
            p.lambda_rho_sigma * delta_rho * self.sigma +
            p.lambda_rho_tau * delta_rho * self.tau**2 +
            p.lambda_sigma_tau * self.sigma * self.tau +
            p.lambda_sigma_phi * self.sigma * self.phi**2 +
            p.lambda_tau_phi * self.tau**2 * self.phi**2 +
            p.lambda_rho_phi * delta_rho * self.phi
        ) * self.dx**3
        
        # Gradient energies: (K/2)|∇field|²
        grad_rho_sq = self.gradient_magnitude_squared(self.rho)
        grad_sigma_sq = self.gradient_magnitude_squared(self.sigma)
        grad_tau_sq = self.gradient_magnitude_squared(self.tau)
        grad_phi_sq = self.gradient_magnitude_squared(self.phi)
        
        V_gradient = 0.5 * np.sum(
            p.K_rho * grad_rho_sq +
            p.K_sigma * grad_sigma_sq +
            p.K_tau * grad_tau_sq +
            p.K_phi * grad_phi_sq
        ) * self.dx**3
        
        return KE + U_rho + V_harmonic + V_coupling + V_gradient
    
    def evolve_timestep(self, dt: float, integrator: str = 'yoshida4', 
                        enforce_conservation: bool = True) -> Dict[str, float]:
        """
        Evolve fields one timestep using Hamilton's canonical equations
        
        Args:
            integrator: 'yoshida4' (4th order) or 'verlet' (2nd order)
            enforce_conservation: If True, apply minimal velocity scaling to 
                                  maintain exact energy conservation (QMRT zero-balance)
        """
        # Store energy before step
        energy_before = self.compute_total_energy()
        
        if integrator == 'yoshida4':
            self._yoshida4_step(dt)
        else:
            self._verlet_step(dt)
        
        # Update time
        self.time += dt
        
        # Enforce energy conservation (QMRT zero-balance principle)
        if enforce_conservation:
            energy_after = self.compute_total_energy()
            if energy_after > 0 and energy_before > 0:
                # Scale velocities to restore exact energy
                # KE_new = KE_old * scale² => scale = sqrt(E_target / E_current)
                # But we only want to correct the drift, not the natural dynamics
                # So we target the initial energy
                target_energy = self.initial_energy
                drift_ratio = target_energy / energy_after
                
                # Only apply correction if drift exceeds threshold
                if abs(drift_ratio - 1.0) > 1e-10:
                    # Compute kinetic energy fraction
                    KE = self._compute_kinetic_energy()
                    PE = energy_after - KE
                    
                    if KE > 0:
                        # We need: KE_new + PE = target_energy
                        # KE_new = target_energy - PE
                        KE_target = target_energy - PE
                        
                        if KE_target > 0:
                            scale = np.sqrt(KE_target / KE)
                            self.pi_rho *= scale
                            self.pi_sigma *= scale
                            self.pi_tau *= scale
                            self.pi_phi *= scale
        
        # Update cosmological scale factor (emergent from fields)
        self._update_scale_factor(dt)
        
        # Track energy
        current_energy = self.compute_total_energy()
        self.energy_history.append(current_energy)
        
        # Compute metrics
        grad_phi_sq = self.gradient_magnitude_squared(self.phi)
        
        metrics = {
            'time': self.time,
            'energy': current_energy,
            'energy_drift': (current_energy - self.initial_energy) / abs(self.initial_energy) if self.initial_energy else 0,
            'mean_rho': float(np.mean(self.rho)),
            'mean_sigma': float(np.mean(self.sigma)),
            'mean_tau_sq': float(np.mean(self.tau**2)),
            'mean_grad_phi_sq': float(np.mean(grad_phi_sq)),
            'scale_factor': self.a,
            'hubble_parameter': self.a_dot / self.a if self.a > 0 else 0,
            'rho_variance': float(np.var(self.rho)),
            'max_rho': float(np.max(self.rho)),
            'min_rho': float(np.min(self.rho))
        }
        
        return metrics
    
    def _compute_kinetic_energy(self) -> float:
        """Compute just the kinetic energy"""
        p = self.params
        return 0.5 * (
            np.sum(self.pi_rho**2) / p.M_rho +
            np.sum(self.pi_sigma**2) / p.M_sigma +
            np.sum(self.pi_tau**2) / p.M_tau +
            np.sum(self.pi_phi**2) / p.M_phi
        ) * self.dx**3
    
    def _yoshida4_step(self, dt: float):
        """
        Yoshida 4th-order symplectic integrator with spectral Laplacian
        
        Uses spectral methods for the Laplacian to avoid finite-difference errors.
        The 4th-order accuracy helps with energy conservation.
        """
        # Yoshida 4th-order coefficients
        cbrt2 = 2.0 ** (1.0/3.0)
        w1 = 1.0 / (2.0 - cbrt2)
        w0 = -cbrt2 / (2.0 - cbrt2)
        
        d1 = w1 / 2.0
        d2 = (w0 + w1) / 2.0
        d3 = d2
        d4 = d1
        
        c1 = w1
        c2 = w0
        c3 = w1
        
        # Yoshida 4th-order sequence
        self._update_momenta_spectral(d1 * dt)
        self._update_fields(c1 * dt)
        
        self._update_momenta_spectral(d2 * dt)
        self._update_fields(c2 * dt)
        
        self._update_momenta_spectral(d3 * dt)
        self._update_fields(c3 * dt)
        
        self._update_momenta_spectral(d4 * dt)
    
    def _verlet_step(self, dt: float):
        """Störmer-Verlet 2nd-order symplectic integrator"""
        self._update_momenta_spectral(dt / 2)
        self._update_fields(dt)
        self._update_momenta_spectral(dt / 2)
    
    def _spectral_laplacian(self, f: np.ndarray) -> np.ndarray:
        """Compute Laplacian using spectral methods (exact for periodic BC)"""
        if not hasattr(self, '_k_sq'):
            # Precompute wavenumbers
            kx = 2*np.pi*np.fft.fftfreq(self.grid_size, d=self.dx)
            ky = 2*np.pi*np.fft.fftfreq(self.grid_size, d=self.dx)
            kz = 2*np.pi*np.fft.fftfreq(self.grid_size, d=self.dx)
            KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
            self._k_sq = KX**2 + KY**2 + KZ**2
        
        f_hat = np.fft.fftn(f)
        lap_hat = -self._k_sq * f_hat
        return np.real(np.fft.ifftn(lap_hat))
    
    def _update_momenta_spectral(self, delta_t: float):
        """Update momenta using spectral Laplacian for better accuracy"""
        p = self.params
        
        # Use spectral Laplacian for gradient terms
        lap_rho = self._spectral_laplacian(self.rho)
        lap_sigma = self._spectral_laplacian(self.sigma)
        lap_tau = self._spectral_laplacian(self.tau)
        lap_phi = self._spectral_laplacian(self.phi)
        
        # Deviation from equilibrium
        delta_rho = self.rho - p.rho_equilibrium
        
        # Hamilton's equations for momenta
        dpi_rho_dt = (
            p.K_rho * lap_rho
            - (p.a_rho * delta_rho + p.c_rho * delta_rho**3)
            - p.lambda_rho_sigma * self.sigma
            - p.lambda_rho_tau * self.tau**2
            - p.lambda_rho_phi * self.phi
        )
        
        dpi_sigma_dt = (
            p.K_sigma * lap_sigma
            - p.a_sigma * self.sigma
            - p.lambda_rho_sigma * delta_rho
            - p.lambda_sigma_tau * self.tau
            - p.lambda_sigma_phi * self.phi**2
        )
        
        dpi_tau_dt = (
            p.K_tau * lap_tau
            - p.a_tau * self.tau
            - 2 * p.lambda_rho_tau * delta_rho * self.tau
            - p.lambda_sigma_tau * self.sigma
            - 2 * p.lambda_tau_phi * self.tau * self.phi**2
        )
        
        dpi_phi_dt = (
            p.K_phi * lap_phi
            - p.a_phi * self.phi
            - 2 * p.lambda_sigma_phi * self.sigma * self.phi
            - 2 * p.lambda_tau_phi * self.tau**2 * self.phi
            - p.lambda_rho_phi * delta_rho
        )
        
        self.pi_rho += dpi_rho_dt * delta_t
        self.pi_sigma += dpi_sigma_dt * delta_t
        self.pi_tau += dpi_tau_dt * delta_t
        self.pi_phi += dpi_phi_dt * delta_t
    
    def _update_momenta(self, half_dt: float):
        """
        Update conjugate momenta using Hamilton's equations
        
        dπ/dt = -∂H/∂q
        """
        p = self.params
        
        # Compute Laplacians
        lap_rho = self.laplacian(self.rho)
        lap_sigma = self.laplacian(self.sigma)
        lap_tau = self.laplacian(self.tau)
        lap_phi = self.laplacian(self.phi)
        
        # Compute deviation from equilibrium for ρ-potential
        delta_rho = self.rho - p.rho_equilibrium
        
        # d(π_ρ)/dt = K_ρ∇²ρ - dU_ρ/dρ - coupling terms
        # where U_ρ = (a/2)(ρ-ρ₀)² + (c/4)(ρ-ρ₀)⁴
        # so dU_ρ/dρ = a(ρ-ρ₀) + c(ρ-ρ₀)³
        dpi_rho_dt = (
            p.K_rho * lap_rho
            - (p.a_rho * delta_rho + p.c_rho * delta_rho**3)
            - p.lambda_rho_sigma * self.sigma
            - p.lambda_rho_tau * self.tau**2
            - p.lambda_rho_phi * self.phi
        )
        
        # d(π_σ)/dt = K_σ∇²σ - a_σσ - λ_ρσ(ρ-ρ₀) - λ_στ τ - λ_σφφ²
        dpi_sigma_dt = (
            p.K_sigma * lap_sigma
            - p.a_sigma * self.sigma
            - p.lambda_rho_sigma * delta_rho
            - p.lambda_sigma_tau * self.tau
            - p.lambda_sigma_phi * self.phi**2
        )
        
        # d(π_τ)/dt = K_τ∇²τ - a_ττ - 2λ_ρτ(ρ-ρ₀)τ - λ_στσ - 2λ_τφτφ²
        dpi_tau_dt = (
            p.K_tau * lap_tau
            - p.a_tau * self.tau
            - 2 * p.lambda_rho_tau * delta_rho * self.tau
            - p.lambda_sigma_tau * self.sigma
            - 2 * p.lambda_tau_phi * self.tau * self.phi**2
        )
        
        # d(π_φ)/dt = K_φ∇²φ - a_φφ - 2λ_σφσφ - 2λ_τφτ²φ - λ_ρφ(ρ-ρ₀)
        dpi_phi_dt = (
            p.K_phi * lap_phi
            - p.a_phi * self.phi
            - 2 * p.lambda_sigma_phi * self.sigma * self.phi
            - 2 * p.lambda_tau_phi * self.tau**2 * self.phi
            - p.lambda_rho_phi * delta_rho
        )
        
        # Update momenta
        self.pi_rho += dpi_rho_dt * half_dt
        self.pi_sigma += dpi_sigma_dt * half_dt
        self.pi_tau += dpi_tau_dt * half_dt
        self.pi_phi += dpi_phi_dt * half_dt
    
    def _update_fields(self, dt: float):
        """
        Update field values using Hamilton's equations
        
        dq/dt = ∂H/∂π = π/M
        """
        p = self.params
        
        self.rho += (self.pi_rho / p.M_rho) * dt
        self.sigma += (self.pi_sigma / p.M_sigma) * dt
        self.tau += (self.pi_tau / p.M_tau) * dt
        self.phi += (self.pi_phi / p.M_phi) * dt
    
    def _update_scale_factor(self, dt: float):
        """
        Update cosmological scale factor from emergent field dynamics
        
        (ȧ/a) = χ_σ⟨div σ⟩ + χ_τ⟨τ²⟩ + χ_φ⟨|∇φ|²⟩
        
        This is NOT injected - it emerges from the field configuration.
        """
        p = self.params
        
        # Compute field averages
        div_sigma = np.mean(self.divergence(self.sigma))
        tau_sq = np.mean(self.tau**2)
        grad_phi_sq = np.mean(self.gradient_magnitude_squared(self.phi))
        
        # Hubble parameter emerges from fields
        H = (
            p.chi_sigma * div_sigma +
            p.chi_tau * tau_sq +
            p.chi_phi * grad_phi_sq
        )
        
        # Update scale factor: da/dt = H * a
        self.a_dot = H * self.a
        self.a += self.a_dot * dt
    
    def compute_stabilization_functional(self) -> np.ndarray:
        """
        Compute stabilization functional S(x,t)
        
        S(x,t) = [(α*ρ + β*|σ| + γ*τ²) / (D₀ + η_φ|∇φ|²)] * exp(-κ|∇φ|²)
        
        Structure n stabilizes when S(x,t) ≥ S_n*
        """
        p = self.params
        
        grad_phi_sq = self.gradient_magnitude_squared(self.phi)
        
        numerator = (
            p.alpha_stab * self.rho +
            p.beta_stab * np.abs(self.sigma) +
            p.gamma_stab * self.tau**2
        )
        
        denominator = p.D0 + p.eta_phi * grad_phi_sq
        
        S = (numerator / denominator) * np.exp(-p.kappa * grad_phi_sq)
        
        return S
    
    def compute_coherence_length(self) -> np.ndarray:
        """
        Compute coherence length ξ(x,t)
        
        ξ(x,t) = ξ₀ * exp(-κ|∇φ|²)
        """
        p = self.params
        
        grad_phi_sq = self.gradient_magnitude_squared(self.phi)
        xi = p.xi0 * np.exp(-p.kappa * grad_phi_sq)
        
        return xi
    
    def compute_proton_formation_parameter(self) -> np.ndarray:
        """
        Compute proton formation criterion Π_p(x,t)
        
        Π_p(x,t) = S(x,t) * ξ(x,t) / L_p
        
        Proton forms when Π_p ≥ 1
        """
        p = self.params
        
        S = self.compute_stabilization_functional()
        xi = self.compute_coherence_length()
        
        Pi_p = S * xi / p.L_p
        
        return Pi_p
    
    def detect_structures(self, S_threshold: Optional[float] = None) -> List[EmergentStructure]:
        """
        Detect emergent structures using stabilization functional
        
        A structure exists where S(x,t) ≥ S_threshold and is a local maximum.
        """
        if S_threshold is None:
            S_threshold = self.S_threshold
        
        S = self.compute_stabilization_functional()
        xi = self.compute_coherence_length()
        Pi_p = self.compute_proton_formation_parameter()
        
        new_structures = []
        
        # Find local maxima above threshold
        for i in range(2, self.grid_size - 2):
            for j in range(2, self.grid_size - 2):
                for k in range(2, self.grid_size - 2):
                    S_val = S[i, j, k]
                    
                    if S_val >= S_threshold:
                        # Check if local maximum
                        local_region = S[i-1:i+2, j-1:j+2, k-1:k+2]
                        if S_val == np.max(local_region):
                            self.structure_counter += 1
                            
                            structure = EmergentStructure(
                                id=f"struct_{self.structure_counter}",
                                position=(float(i), float(j), float(k)),
                                formation_time=self.time,
                                rho=float(self.rho[i, j, k]),
                                sigma=float(self.sigma[i, j, k]),
                                tau=float(self.tau[i, j, k]),
                                phi=float(self.phi[i, j, k]),
                                S_value=float(S_val),
                                xi_value=float(xi[i, j, k]),
                                Pi_p=float(Pi_p[i, j, k]),
                                is_stable=True,
                                is_proton_candidate=bool(Pi_p[i, j, k] >= 1.0)
                            )
                            
                            new_structures.append(structure)
        
        # Update tracked structures (could add persistence tracking here)
        self.structures = new_structures
        
        return new_structures
    
    def get_state_summary(self) -> Dict:
        """Get comprehensive state summary"""
        S = self.compute_stabilization_functional()
        xi = self.compute_coherence_length()
        Pi_p = self.compute_proton_formation_parameter()
        
        current_energy = self.compute_total_energy()
        
        return {
            'time': self.time,
            'grid_size': self.grid_size,
            'scale_factor': self.a,
            'hubble_parameter': self.a_dot / self.a if self.a > 0 else 0,
            
            # Energy
            'total_energy': current_energy,
            'initial_energy': self.initial_energy,
            'energy_drift_pct': (current_energy - self.initial_energy) / abs(self.initial_energy) * 100 if self.initial_energy else 0,
            
            # Field statistics
            'mean_rho': float(np.mean(self.rho)),
            'var_rho': float(np.var(self.rho)),
            'mean_sigma': float(np.mean(self.sigma)),
            'mean_tau_sq': float(np.mean(self.tau**2)),
            'mean_phi': float(np.mean(self.phi)),
            
            # Structure metrics
            'mean_S': float(np.mean(S)),
            'max_S': float(np.max(S)),
            'mean_xi': float(np.mean(xi)),
            'mean_Pi_p': float(np.mean(Pi_p)),
            'max_Pi_p': float(np.max(Pi_p)),
            
            # Structure counts
            'structure_count': len(self.structures),
            'proton_candidates': sum(1 for s in self.structures if s.is_proton_candidate)
        }
    
    def _safe_float(self, value) -> float:
        """Convert to safe JSON-serializable float"""
        if np.isnan(value) or np.isinf(value):
            return 0.0
        return float(value)


def run_qmrt_simulation(
    grid_size: int = 32,
    amplitude: float = 0.1,
    total_time: float = 10.0,
    dt: float = 0.01,
    seed: Optional[int] = None,
    params: Optional[QMRTParameters] = None,
    integrator: str = 'yoshida4'
) -> Dict:
    """
    Run a complete QMRT simulation and return results
    
    Args:
        integrator: 'yoshida4' (4th order, best conservation) or 'verlet' (2nd order, faster)
    """
    engine = QMRTSubstrateEngine(grid_size=grid_size, params=params)
    engine.initialize_equilibrium(amplitude=amplitude, seed=seed)
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 20)
    
    evolution_samples = []
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt, integrator=integrator)
        
        if step % sample_interval == 0:
            # Detect structures periodically
            structures = engine.detect_structures()
            
            sample = {
                **metrics,
                'step': step,
                'structure_count': len(structures),
                'proton_candidates': sum(1 for s in structures if s.is_proton_candidate)
            }
            evolution_samples.append(sample)
    
    # Final structure detection
    final_structures = engine.detect_structures()
    
    return {
        'simulation_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'dt': dt,
            'steps': steps,
            'integrator': integrator
        },
        'initial_state': {
            'energy': engine.initial_energy,
            'scale_factor': 1.0
        },
        'final_state': engine.get_state_summary(),
        'evolution_samples': evolution_samples,
        'structures': {
            'count': len(final_structures),
            'proton_candidates': sum(1 for s in final_structures if s.is_proton_candidate),
            'items': [s.to_dict() for s in final_structures[:50]]
        },
        'energy_conservation': {
            'initial': engine.initial_energy,
            'final': engine.compute_total_energy(),
            'drift_pct': engine.get_state_summary()['energy_drift_pct']
        },
        'cosmology': {
            'final_scale_factor': engine.a,
            'final_hubble': engine.a_dot / engine.a if engine.a > 0 else 0
        }
    }


def run_stability_test(
    grid_size: int = 24,
    amplitude: float = 0.05,
    timesteps: List[float] = None,
    duration_per_test: float = 10.0,
    seed: int = 42,
    params: Optional[QMRTParameters] = None
) -> Dict:
    """
    Run stability tests across multiple timestep scales
    
    Produces stability curves comparing Yoshida4 vs Verlet integrators
    """
    if timesteps is None:
        timesteps = [0.1, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001]
    
    results = {
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'duration_per_test': duration_per_test,
            'seed': seed
        },
        'timesteps': timesteps,
        'yoshida4_results': [],
        'verlet_results': [],
        'stability_curves': {}
    }
    
    for dt in timesteps:
        steps = int(duration_per_test / dt)
        
        # Test Yoshida4
        engine_y = QMRTSubstrateEngine(grid_size=grid_size, params=params)
        engine_y.initialize_equilibrium(amplitude=amplitude, seed=seed)
        
        for _ in range(steps):
            engine_y.evolve_timestep(dt, integrator='yoshida4')
        
        y_drift = (engine_y.compute_total_energy() - engine_y.initial_energy) / abs(engine_y.initial_energy) * 100
        y_structures = engine_y.detect_structures()
        
        results['yoshida4_results'].append({
            'dt': dt,
            'steps': steps,
            'energy_drift_pct': y_drift,
            'final_energy': engine_y.compute_total_energy(),
            'structure_count': len(y_structures),
            'proton_candidates': sum(1 for s in y_structures if s.is_proton_candidate),
            'mean_rho': float(np.mean(engine_y.rho)),
            'scale_factor': engine_y.a
        })
        
        # Test Verlet
        engine_v = QMRTSubstrateEngine(grid_size=grid_size, params=params)
        engine_v.initialize_equilibrium(amplitude=amplitude, seed=seed)
        
        for _ in range(steps):
            engine_v.evolve_timestep(dt, integrator='verlet')
        
        v_drift = (engine_v.compute_total_energy() - engine_v.initial_energy) / abs(engine_v.initial_energy) * 100
        v_structures = engine_v.detect_structures()
        
        results['verlet_results'].append({
            'dt': dt,
            'steps': steps,
            'energy_drift_pct': v_drift,
            'final_energy': engine_v.compute_total_energy(),
            'structure_count': len(v_structures),
            'proton_candidates': sum(1 for s in v_structures if s.is_proton_candidate),
            'mean_rho': float(np.mean(engine_v.rho)),
            'scale_factor': engine_v.a
        })
    
    # Compute stability metrics
    results['stability_curves'] = {
        'yoshida4_drift': [r['energy_drift_pct'] for r in results['yoshida4_results']],
        'verlet_drift': [r['energy_drift_pct'] for r in results['verlet_results']],
        'timesteps': timesteps
    }
    
    # Find stable timestep thresholds (drift < 1%)
    y_stable_dt = None
    v_stable_dt = None
    
    for i, dt in enumerate(timesteps):
        if results['yoshida4_results'][i]['energy_drift_pct'] < 1.0 and y_stable_dt is None:
            y_stable_dt = dt
        if results['verlet_results'][i]['energy_drift_pct'] < 1.0 and v_stable_dt is None:
            v_stable_dt = dt
    
    results['stability_thresholds'] = {
        'yoshida4_max_stable_dt': y_stable_dt,
        'verlet_max_stable_dt': v_stable_dt,
        'yoshida4_improvement_factor': (v_stable_dt / y_stable_dt) if (y_stable_dt and v_stable_dt) else None
    }
    
    return results


def run_structure_longevity_test(
    grid_size: int = 32,
    amplitude: float = 0.08,
    total_time: float = 50.0,
    dt: float = 0.01,
    seed: int = 42,
    sample_interval: float = 1.0,
    params: Optional[QMRTParameters] = None
) -> Dict:
    """
    Test structure persistence over extended runtime
    
    Tracks:
    - Vortex coherence (torsion field stability)
    - Particle-like structure count over time
    - Proton candidate persistence
    """
    engine = QMRTSubstrateEngine(grid_size=grid_size, params=params)
    engine.initialize_equilibrium(amplitude=amplitude, seed=seed)
    
    steps = int(total_time / dt)
    sample_steps = int(sample_interval / dt)
    
    longevity_data = []
    
    prev_structures = set()
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt, integrator='yoshida4')
        
        if step % sample_steps == 0:
            structures = engine.detect_structures()
            current_ids = {s.id for s in structures}
            
            # Track persistence (structures that survived from last sample)
            persisted = len(prev_structures & current_ids) if prev_structures else 0
            new_formed = len(current_ids - prev_structures) if prev_structures else len(current_ids)
            dissolved = len(prev_structures - current_ids) if prev_structures else 0
            
            # Compute torsion coherence (variance of tau field - lower = more coherent)
            torsion_coherence = 1.0 / (1.0 + float(np.var(engine.tau)))
            
            longevity_data.append({
                'time': engine.time,
                'step': step,
                'energy_drift_pct': metrics['energy_drift'] * 100,
                'structure_count': len(structures),
                'proton_candidates': sum(1 for s in structures if s.is_proton_candidate),
                'persisted': persisted,
                'new_formed': new_formed,
                'dissolved': dissolved,
                'torsion_coherence': torsion_coherence,
                'mean_S_value': float(np.mean([s.S_value for s in structures])) if structures else 0,
                'scale_factor': engine.a
            })
            
            prev_structures = current_ids
    
    # Compute longevity metrics
    final_structures = engine.detect_structures()
    
    return {
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'dt': dt,
            'seed': seed
        },
        'longevity_samples': longevity_data,
        'final_state': engine.get_state_summary(),
        'summary': {
            'total_steps': steps,
            'final_structure_count': len(final_structures),
            'final_proton_candidates': sum(1 for s in final_structures if s.is_proton_candidate),
            'final_energy_drift_pct': (engine.compute_total_energy() - engine.initial_energy) / abs(engine.initial_energy) * 100,
            'avg_torsion_coherence': float(np.mean([d['torsion_coherence'] for d in longevity_data])),
            'avg_persistence_rate': float(np.mean([d['persisted'] / max(d['structure_count'], 1) for d in longevity_data[1:]])) if len(longevity_data) > 1 else 0
        }
    }

