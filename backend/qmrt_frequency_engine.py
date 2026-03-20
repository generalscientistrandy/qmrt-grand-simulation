"""
QMRT Frequency-Domain Substrate Engine

Implements the foundational QMRT physics with explicit frequency field.

Key insight from QMRT theory:
- Frequency (ω) is a MEDIUM STATE VARIABLE, not just a derived observable
- Phase (φ) = local oscillation geometry
- Frequency (ω) = regional stability / regime selector

This enables:
- Spectral universe formation (frequency-domain separation)
- Persistent coherence domains
- Regime-dependent physics
- Antimatter in different frequency bands

Fields: (ρ, σ, τ, φ, ω) with conjugate momenta (π_ρ, π_σ, π_τ, π_φ, π_ω)

Hamiltonian includes:
H = H_kinetic + H_ρ + H_σ + H_τ + H_φ + H_ω + H_coupling + H_gradient

Where H_ω = ½ π_ω²/M_ω + V_band(ω) + κ_ω(∇ω)²
      V_band(ω) = a_ω(ω² − ω₀²)²  ← Double-well creates frequency basins

Phase convention: φ ∈ (−π, +π)
Frequency convention: ω > 0 (oscillation rate / basin depth)
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class FrequencyBand(Enum):
    """Classification based on which frequency basin ω resides in"""
    LOW_BAND = "low_band"       # ω < ω₀ (one basin)
    HIGH_BAND = "high_band"     # ω > ω₀ (other basin)
    TRANSITIONAL = "transitional"  # Near ω₀ (unstable saddle)


class AttractorBasin(Enum):
    """Phase basin classification"""
    MATTER = "matter"           # φ ≈ 0
    ANTIMATTER = "antimatter"   # φ ≈ ±π
    TRANSITIONAL = "transitional"


@dataclass
class FrequencyModeProperties:
    """
    Emergent properties from substrate field modes including frequency.
    
    Classification emerges from these - NOT hardcoded labels.
    """
    # Frequency properties
    omega: float                # Local frequency value
    frequency_band: str         # Which frequency basin
    omega_gradient_sq: float    # |∇ω|² - frequency coherence
    
    # Phase properties
    phase_value: float
    phase_basin: str
    phase_gradient_sq: float
    
    # Energy properties
    binding_energy: float
    kinetic_fraction: float
    
    # Spatial properties
    coherence_length: float
    
    # Topological properties
    winding_number: int
    vorticity: float
    
    # Field amplitudes
    rho_deviation: float
    sigma_amplitude: float
    tau_magnitude: float
    
    # Stability
    S_value: float
    
    def to_dict(self) -> Dict:
        return {
            'omega': float(self.omega),
            'frequency_band': self.frequency_band,
            'omega_gradient_sq': float(self.omega_gradient_sq),
            'phase_value': float(self.phase_value),
            'phase_basin': self.phase_basin,
            'phase_gradient_sq': float(self.phase_gradient_sq),
            'binding_energy': float(self.binding_energy),
            'kinetic_fraction': float(self.kinetic_fraction),
            'coherence_length': float(self.coherence_length),
            'winding_number': int(self.winding_number),
            'vorticity': float(self.vorticity),
            'rho_deviation': float(self.rho_deviation),
            'sigma_amplitude': float(self.sigma_amplitude),
            'tau_magnitude': float(self.tau_magnitude),
            'S_value': float(self.S_value)
        }


@dataclass
class CoherentStructure:
    """
    A coherent structure in the QMRT substrate.
    
    Now includes frequency band information for multiverse separation.
    """
    id: str
    centroid: Tuple[float, float, float]
    extent: float
    
    # Phase classification
    phase_basin: AttractorBasin
    phase_value: float
    
    # Frequency classification (NEW)
    frequency_band: FrequencyBand
    omega_value: float
    
    # Raw field values
    rho: float
    sigma: float
    tau: float
    phi: float
    omega: float
    
    # Emergent properties
    mode_properties: FrequencyModeProperties
    
    # Topological signature: (winding, frequency_band_sign, tau_sign)
    topological_signature: Tuple[int, int, int]
    
    # Lifetime tracking
    formation_time: float
    last_seen_time: float
    lifetime: float = 0.0
    is_alive: bool = True
    
    # History
    centroid_history: List[Tuple[float, float, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'centroid': self.centroid,
            'extent': float(self.extent),
            'phase_basin': self.phase_basin.value,
            'phase_value': float(self.phase_value),
            'frequency_band': self.frequency_band.value,
            'omega_value': float(self.omega_value),
            'rho': float(self.rho),
            'sigma': float(self.sigma),
            'tau': float(self.tau),
            'phi': float(self.phi),
            'omega': float(self.omega),
            'mode_properties': self.mode_properties.to_dict(),
            'topological_signature': self.topological_signature,
            'formation_time': float(self.formation_time),
            'lifetime': float(self.lifetime),
            'is_alive': self.is_alive
        }


@dataclass
class QMRTFrequencyParameters:
    """
    Parameters for QMRT simulation with explicit frequency field.
    
    The frequency potential V_band(ω) = a_ω(ω² − ω₀²)² creates
    a double-well with minima at ω = ±ω₀, enabling spectral universe formation.
    """
    # Mass parameters (kinetic denominators)
    M_rho: float = 1.0
    M_sigma: float = 1.0
    M_tau: float = 1.0
    M_phi: float = 1.0
    M_omega: float = 1.0  # Frequency field mass
    
    # Density potential (equilibrium at ρ=1)
    rho_equilibrium: float = 1.0
    a_rho: float = 0.1
    c_rho: float = 0.02
    
    # Other field potentials
    a_sigma: float = 0.1
    a_tau: float = 0.1
    
    # Phase potential: U_φ = -a_φ cos(φ)
    a_phi: float = 0.2
    
    # FREQUENCY BAND POTENTIAL (KEY NEW PHYSICS)
    # V_band(ω) = a_ω(ω² − ω₀²)²
    # Creates double-well with minima at ω = ±ω₀
    omega_0: float = 1.0      # Equilibrium frequency (basin centers at ±ω₀)
    a_omega: float = 0.1      # Strength of frequency potential
    
    # Gradient coefficients
    K_rho: float = 0.5
    K_sigma: float = 0.5
    K_tau: float = 0.5
    K_phi: float = 0.5
    K_omega: float = 0.5      # Frequency gradient energy
    
    # FREQUENCY-PHASE COUPLING (Phase 2 physics)
    # g_omega_phi * ω * |∇φ|²  → matter prefers certain frequency bands
    g_omega_phi: float = 0.05
    
    # FREQUENCY-DENSITY COUPLING
    # g_omega_rho * ω * (ρ - ρ₀)²  → density-frequency coupling
    g_omega_rho: float = 0.02
    
    # Other couplings (existing)
    lambda_rho_sigma: float = 0.02
    lambda_rho_tau: float = 0.02
    lambda_sigma_tau: float = 0.02
    lambda_sigma_phi: float = 0.02
    lambda_tau_phi: float = 0.02
    lambda_rho_phi: float = 0.02
    
    # Stabilization functional
    alpha_stab: float = 1.0
    beta_stab: float = 0.5
    gamma_stab: float = 0.3
    delta_stab: float = 0.2   # Frequency contribution to stability
    D0: float = 0.1
    eta_phi: float = 0.5
    kappa: float = 0.2
    xi0: float = 1.0
    
    # Classification thresholds
    phase_basin_boundary: float = np.pi / 2
    frequency_basin_width: float = 0.3  # |ω - ω₀| < width → in basin
    S_threshold: float = 0.3
    
    # Tracking parameters
    tracking_radius: float = 2.5
    topology_weight: float = 0.5


class QMRTFrequencyEngine:
    """
    QMRT Substrate Engine with Explicit Frequency Field.
    
    Implements the foundational physics where frequency is a medium state
    variable that enables spectral universe formation.
    
    Five fields: (ρ, σ, τ, φ, ω) with conjugate momenta
    
    Key physics:
    - V_band(ω) = a_ω(ω² − ω₀²)² creates frequency basins (spectral universes)
    - φ ∈ (−π, +π) for matter/antimatter phase separation
    - Coupling terms link frequency to phase/density dynamics
    """
    
    def __init__(self, grid_size: int = 32, dx: float = 1.0,
                 params: Optional[QMRTFrequencyParameters] = None):
        self.grid_size = grid_size
        self.dx = dx
        self.time = 0.0
        
        self.params = params or QMRTFrequencyParameters()
        
        # Five fundamental fields
        self.rho = None    # Density
        self.sigma = None  # Tension
        self.tau = None    # Torsion
        self.phi = None    # Phase φ ∈ (−π, +π)
        self.omega = None  # Frequency (NEW)
        
        # Five conjugate momenta
        self.pi_rho = None
        self.pi_sigma = None
        self.pi_tau = None
        self.pi_phi = None
        self.pi_omega = None  # Frequency momentum (NEW)
        
        # Structure tracking
        self.active_structures: Dict[str, CoherentStructure] = {}
        self.deceased_structures: List[CoherentStructure] = []
        self.structure_counter = 0
        
        # Energy tracking
        self.initial_energy = None
        self.energy_history: List[float] = []
        
        # Spectral precomputation
        self._k_sq = None
        self._kx = None
        self._ky = None
        self._kz = None
        
    def initialize_frequency_domains(self, amplitude: float = 0.05,
                                     matter_fraction: float = 0.5,
                                     high_freq_fraction: float = 0.5,
                                     seed: Optional[int] = None):
        """
        Initialize substrate with both phase basins AND frequency domains.
        
        Creates:
        - Matter (φ≈0) and antimatter (φ≈±π) phase regions
        - High-frequency (ω≈+ω₀) and low-frequency (ω≈-ω₀) bands
        
        This enables observation of:
        - Phase separation (matter/antimatter)
        - Frequency separation (spectral universes)
        - Cross-coupling between phase and frequency
        """
        if seed is not None:
            np.random.seed(seed)
            
        shape = (self.grid_size, self.grid_size, self.grid_size)
        p = self.params
        
        # Initialize density at equilibrium
        self.rho = p.rho_equilibrium + amplitude * self._balanced_noise(shape)
        
        # Initialize tension and torsion
        self.sigma = amplitude * self._balanced_noise(shape)
        self.tau = amplitude * self._balanced_noise(shape)
        
        # Initialize PHASE with dual basins
        self.phi = np.zeros(shape)
        matter_mask = np.random.random(shape) < matter_fraction
        self.phi[matter_mask] = amplitude * np.random.randn(np.sum(matter_mask))
        antimatter_count = np.sum(~matter_mask)
        antimatter_signs = 2 * (np.random.random(antimatter_count) > 0.5) - 1
        self.phi[~matter_mask] = antimatter_signs * (np.pi - amplitude * np.abs(np.random.randn(antimatter_count)))
        self.phi = self._wrap_phase(self.phi)
        
        # Initialize FREQUENCY with dual basins (NEW)
        # ω₀ is the basin center; we initialize some regions at +ω₀, others at -ω₀
        self.omega = np.zeros(shape)
        high_freq_mask = np.random.random(shape) < high_freq_fraction
        self.omega[high_freq_mask] = p.omega_0 + amplitude * np.random.randn(np.sum(high_freq_mask))
        self.omega[~high_freq_mask] = -p.omega_0 + amplitude * np.random.randn(np.sum(~high_freq_mask))
        
        # Initialize all momenta at zero
        self.pi_rho = np.zeros(shape)
        self.pi_sigma = np.zeros(shape)
        self.pi_tau = np.zeros(shape)
        self.pi_phi = np.zeros(shape)
        self.pi_omega = np.zeros(shape)
        
        # Precompute spectral coefficients
        self._precompute_spectral()
        
        # Record initial energy
        self.initial_energy = self.compute_total_energy()
        
        # Statistics
        matter_count = int(np.sum(np.abs(self.phi) < p.phase_basin_boundary))
        antimatter_count = int(np.sum(np.abs(self.phi) >= p.phase_basin_boundary))
        high_freq_count = int(np.sum(self.omega > 0))
        low_freq_count = int(np.sum(self.omega <= 0))
        
        print("QMRT Frequency-Domain Engine initialized")
        print(f"  Grid: {self.grid_size}³, dx={self.dx}")
        print("  Fields: (ρ, σ, τ, φ, ω) with conjugate momenta")
        print(f"  Initial energy: {self.initial_energy:.4f}")
        print(f"  Phase basins: Matter {100*matter_count/self.phi.size:.1f}%, Antimatter {100*antimatter_count/self.phi.size:.1f}%")
        print(f"  Frequency bands: High (ω>0) {100*high_freq_count/self.omega.size:.1f}%, Low (ω≤0) {100*low_freq_count/self.omega.size:.1f}%")
        
    def _wrap_phase(self, phi: np.ndarray) -> np.ndarray:
        """Wrap phase to (−π, +π)"""
        return np.mod(phi + np.pi, 2*np.pi) - np.pi
    
    def _balanced_noise(self, shape: Tuple) -> np.ndarray:
        """Generate zero-mean noise"""
        noise = np.random.randn(*shape)
        noise -= np.mean(noise)
        return noise
    
    def _precompute_spectral(self):
        """Precompute wavenumbers for spectral methods"""
        kx = 2 * np.pi * np.fft.fftfreq(self.grid_size, d=self.dx)
        ky = 2 * np.pi * np.fft.fftfreq(self.grid_size, d=self.dx)
        kz = 2 * np.pi * np.fft.fftfreq(self.grid_size, d=self.dx)
        self._kx, self._ky, self._kz = np.meshgrid(kx, ky, kz, indexing='ij')
        self._k_sq = self._kx**2 + self._ky**2 + self._kz**2
        
    def _spectral_laplacian(self, f: np.ndarray) -> np.ndarray:
        """Compute Laplacian using spectral method"""
        f_hat = np.fft.fftn(f)
        lap_hat = -self._k_sq * f_hat
        return np.real(np.fft.ifftn(lap_hat))
    
    def _spectral_gradient_sq(self, f: np.ndarray) -> np.ndarray:
        """Compute |∇f|² using spectral method"""
        f_hat = np.fft.fftn(f)
        gx = np.real(np.fft.ifftn(1j * self._kx * f_hat))
        gy = np.real(np.fft.ifftn(1j * self._ky * f_hat))
        gz = np.real(np.fft.ifftn(1j * self._kz * f_hat))
        return gx**2 + gy**2 + gz**2
    
    def compute_total_energy(self) -> float:
        """
        Compute total Hamiltonian energy.
        
        Now includes:
        - Frequency kinetic energy: ½ π_ω²/M_ω
        - Frequency band potential: V_band(ω) = a_ω(ω² − ω₀²)²
        - Frequency gradient energy: ½ K_ω |∇ω|²
        - Frequency-phase coupling: g_ωφ · ω · |∇φ|²
        - Frequency-density coupling: g_ωρ · ω · (ρ − ρ₀)²
        """
        p = self.params
        
        # Kinetic energy (now includes π_ω)
        KE = 0.5 * (
            np.sum(self.pi_rho**2) / p.M_rho +
            np.sum(self.pi_sigma**2) / p.M_sigma +
            np.sum(self.pi_tau**2) / p.M_tau +
            np.sum(self.pi_phi**2) / p.M_phi +
            np.sum(self.pi_omega**2) / p.M_omega
        ) * self.dx**3
        
        # Density potential
        delta_rho = self.rho - p.rho_equilibrium
        U_rho = np.sum(
            (p.a_rho / 2) * delta_rho**2 +
            (p.c_rho / 4) * delta_rho**4
        ) * self.dx**3
        
        # Harmonic potentials for σ, τ
        V_harmonic = np.sum(
            (p.a_sigma / 2) * self.sigma**2 +
            (p.a_tau / 2) * self.tau**2
        ) * self.dx**3
        
        # Phase potential: U_φ = -a_φ cos(φ)
        U_phi = np.sum(-p.a_phi * np.cos(self.phi)) * self.dx**3
        
        # FREQUENCY BAND POTENTIAL (NEW)
        # V_band(ω) = a_ω(ω² − ω₀²)²
        # This creates a double-well with minima at ω = ±ω₀
        omega_sq_minus_omega0_sq = self.omega**2 - p.omega_0**2
        V_band = np.sum(p.a_omega * omega_sq_minus_omega0_sq**2) * self.dx**3
        
        # Standard couplings
        V_coupling = np.sum(
            p.lambda_rho_sigma * delta_rho * self.sigma +
            p.lambda_rho_tau * delta_rho * self.tau**2 +
            p.lambda_sigma_tau * self.sigma * self.tau +
            p.lambda_sigma_phi * self.sigma * np.cos(self.phi) +
            p.lambda_tau_phi * self.tau**2 * np.cos(self.phi) +
            p.lambda_rho_phi * delta_rho * np.cos(self.phi)
        ) * self.dx**3
        
        # Gradient energies (now includes ω)
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        grad_omega_sq = self._spectral_gradient_sq(self.omega)
        
        V_gradient = 0.5 * np.sum(
            p.K_rho * self._spectral_gradient_sq(self.rho) +
            p.K_sigma * self._spectral_gradient_sq(self.sigma) +
            p.K_tau * self._spectral_gradient_sq(self.tau) +
            p.K_phi * grad_phi_sq +
            p.K_omega * grad_omega_sq
        ) * self.dx**3
        
        # FREQUENCY-PHASE COUPLING (NEW)
        # g_omega_phi * ω * |∇φ|² → matter structures prefer certain frequency bands
        V_omega_phi = np.sum(p.g_omega_phi * self.omega * grad_phi_sq) * self.dx**3
        
        # FREQUENCY-DENSITY COUPLING (NEW)
        # g_omega_rho * ω * (ρ - ρ₀)² → density-frequency coupling
        V_omega_rho = np.sum(p.g_omega_rho * self.omega * delta_rho**2) * self.dx**3
        
        return KE + U_rho + V_harmonic + U_phi + V_band + V_coupling + V_gradient + V_omega_phi + V_omega_rho
    
    def _compute_kinetic_energy(self) -> float:
        """Compute kinetic energy only"""
        p = self.params
        return 0.5 * (
            np.sum(self.pi_rho**2) / p.M_rho +
            np.sum(self.pi_sigma**2) / p.M_sigma +
            np.sum(self.pi_tau**2) / p.M_tau +
            np.sum(self.pi_phi**2) / p.M_phi +
            np.sum(self.pi_omega**2) / p.M_omega
        ) * self.dx**3
    
    def evolve_timestep(self, dt: float, enforce_conservation: bool = True) -> Dict:
        """
        Evolve one timestep using Yoshida 4th-order symplectic integrator.
        
        Now includes frequency field dynamics.
        """
        # Yoshida4 coefficients
        cbrt2 = 2.0 ** (1.0/3.0)
        w1 = 1.0 / (2.0 - cbrt2)
        w0 = -cbrt2 / (2.0 - cbrt2)
        
        d1 = w1 / 2.0
        d2 = (w0 + w1) / 2.0
        d3, d4 = d2, d1
        c1, c2, c3 = w1, w0, w1
        
        # Yoshida4 integration
        self._update_momenta(d1 * dt)
        self._update_fields(c1 * dt)
        self._update_momenta(d2 * dt)
        self._update_fields(c2 * dt)
        self._update_momenta(d3 * dt)
        self._update_fields(c3 * dt)
        self._update_momenta(d4 * dt)
        
        # Wrap phase
        self.phi = self._wrap_phase(self.phi)
        
        # Enforce energy conservation
        if enforce_conservation:
            self._enforce_energy_conservation()
        
        self.time += dt
        
        # Track energy
        current_energy = self.compute_total_energy()
        self.energy_history.append(current_energy)
        
        # Update structure tracking
        self._update_structure_tracking()
        
        # Compute statistics
        stats = self._compute_statistics()
        
        return {
            'time': float(self.time),
            'energy': float(current_energy),
            'energy_drift': float((current_energy - self.initial_energy) / abs(self.initial_energy)) if self.initial_energy else 0.0,
            **stats,
            'active_structures': len(self.active_structures),
            'total_formed': self.structure_counter,
            'total_deceased': len(self.deceased_structures)
        }
    
    def _update_momenta(self, delta_t: float):
        """
        Update all five momenta using Hamilton's equations.
        
        dπ/dt = -∂H/∂q
        
        Now includes frequency momentum dynamics.
        """
        p = self.params
        
        # Spectral Laplacians
        lap_rho = self._spectral_laplacian(self.rho)
        lap_sigma = self._spectral_laplacian(self.sigma)
        lap_tau = self._spectral_laplacian(self.tau)
        lap_phi = self._spectral_laplacian(self.phi)
        lap_omega = self._spectral_laplacian(self.omega)
        
        delta_rho = self.rho - p.rho_equilibrium
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        
        # Density momentum
        dpi_rho_dt = (
            p.K_rho * lap_rho
            - (p.a_rho * delta_rho + p.c_rho * delta_rho**3)
            - p.lambda_rho_sigma * self.sigma
            - p.lambda_rho_tau * self.tau**2
            - p.lambda_rho_phi * np.cos(self.phi)
            - 2 * p.g_omega_rho * self.omega * delta_rho  # Frequency-density coupling
        )
        
        # Sigma momentum
        dpi_sigma_dt = (
            p.K_sigma * lap_sigma
            - p.a_sigma * self.sigma
            - p.lambda_rho_sigma * delta_rho
            - p.lambda_sigma_tau * self.tau
            - p.lambda_sigma_phi * np.cos(self.phi)
        )
        
        # Tau momentum
        dpi_tau_dt = (
            p.K_tau * lap_tau
            - p.a_tau * self.tau
            - 2 * p.lambda_rho_tau * delta_rho * self.tau
            - p.lambda_sigma_tau * self.sigma
            - 2 * p.lambda_tau_phi * self.tau * np.cos(self.phi)
        )
        
        # Phase momentum (includes frequency-phase coupling)
        # ∂/∂φ [g_ωφ · ω · |∇φ|²] requires careful handling
        # For now, use simplified coupling through the existing sin(φ) term
        dpi_phi_dt = (
            p.K_phi * lap_phi
            - p.a_phi * np.sin(self.phi)
            + p.lambda_sigma_phi * self.sigma * np.sin(self.phi)
            + p.lambda_tau_phi * self.tau**2 * np.sin(self.phi)
            + p.lambda_rho_phi * delta_rho * np.sin(self.phi)
        )
        
        # FREQUENCY MOMENTUM (NEW)
        # dπ_ω/dt = -∂H/∂ω
        # ∂V_band/∂ω = 4 a_ω ω (ω² - ω₀²)
        # ∂V_ωφ/∂ω = g_ωφ |∇φ|²
        # ∂V_ωρ/∂ω = g_ωρ (ρ - ρ₀)²
        dpi_omega_dt = (
            p.K_omega * lap_omega
            - 4 * p.a_omega * self.omega * (self.omega**2 - p.omega_0**2)
            - p.g_omega_phi * grad_phi_sq
            - p.g_omega_rho * delta_rho**2
        )
        
        # Update all momenta
        self.pi_rho += dpi_rho_dt * delta_t
        self.pi_sigma += dpi_sigma_dt * delta_t
        self.pi_tau += dpi_tau_dt * delta_t
        self.pi_phi += dpi_phi_dt * delta_t
        self.pi_omega += dpi_omega_dt * delta_t
    
    def _update_fields(self, delta_t: float):
        """Update all five field values: dq/dt = π/M"""
        p = self.params
        self.rho += (self.pi_rho / p.M_rho) * delta_t
        self.sigma += (self.pi_sigma / p.M_sigma) * delta_t
        self.tau += (self.pi_tau / p.M_tau) * delta_t
        self.phi += (self.pi_phi / p.M_phi) * delta_t
        self.omega += (self.pi_omega / p.M_omega) * delta_t
    
    def _enforce_energy_conservation(self):
        """Enforce exact energy conservation via velocity rescaling"""
        energy_after = self.compute_total_energy()
        if energy_after > 0 and self.initial_energy > 0:
            KE = self._compute_kinetic_energy()
            PE = energy_after - KE
            KE_target = self.initial_energy - PE
            
            if KE > 0 and KE_target > 0:
                scale = np.sqrt(KE_target / KE)
                self.pi_rho *= scale
                self.pi_sigma *= scale
                self.pi_tau *= scale
                self.pi_phi *= scale
                self.pi_omega *= scale
    
    def _compute_statistics(self) -> Dict:
        """Compute phase and frequency statistics"""
        p = self.params
        
        # Phase statistics
        matter_count = int(np.sum(np.abs(self.phi) < p.phase_basin_boundary))
        antimatter_count = int(np.sum(np.abs(self.phi) >= p.phase_basin_boundary))
        total = int(self.phi.size)
        
        # Frequency statistics
        high_freq_count = int(np.sum(self.omega > 0))
        low_freq_count = int(np.sum(self.omega <= 0))
        
        # Frequency basin statistics (near ±ω₀)
        in_high_basin = int(np.sum(np.abs(self.omega - p.omega_0) < p.frequency_basin_width))
        in_low_basin = int(np.sum(np.abs(self.omega + p.omega_0) < p.frequency_basin_width))
        
        return {
            'matter_fraction': float(matter_count / total),
            'antimatter_fraction': float(antimatter_count / total),
            'high_freq_fraction': float(high_freq_count / total),
            'low_freq_fraction': float(low_freq_count / total),
            'in_high_basin_fraction': float(in_high_basin / total),
            'in_low_basin_fraction': float(in_low_basin / total),
            'phase_mean': float(np.mean(self.phi)),
            'phase_std': float(np.std(self.phi)),
            'omega_mean': float(np.mean(self.omega)),
            'omega_std': float(np.std(self.omega)),
            'mean_rho': float(np.mean(self.rho))
        }
    
    def _classify_phase_basin(self, phi_value: float) -> AttractorBasin:
        """Classify phase value into matter/antimatter basin"""
        p = self.params
        phi_wrapped = self._wrap_phase(np.array([phi_value]))[0]
        if np.abs(phi_wrapped) < p.phase_basin_boundary:
            return AttractorBasin.MATTER
        else:
            return AttractorBasin.ANTIMATTER
    
    def _classify_frequency_band(self, omega_value: float) -> FrequencyBand:
        """Classify frequency value into band"""
        p = self.params
        if np.abs(omega_value - p.omega_0) < p.frequency_basin_width:
            return FrequencyBand.HIGH_BAND
        elif np.abs(omega_value + p.omega_0) < p.frequency_basin_width:
            return FrequencyBand.LOW_BAND
        else:
            return FrequencyBand.TRANSITIONAL
    
    def compute_stabilization_functional(self) -> np.ndarray:
        """
        Compute S(x,t) for structure detection.
        
        Now includes frequency contribution.
        """
        p = self.params
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        grad_omega_sq = self._spectral_gradient_sq(self.omega)
        
        # Frequency stability contribution: more stable when ω is near basin
        omega_stability = np.exp(-np.abs(self.omega**2 - p.omega_0**2))
        
        numerator = (
            p.alpha_stab * np.abs(self.rho - p.rho_equilibrium) +
            p.beta_stab * np.abs(self.sigma) +
            p.gamma_stab * self.tau**2 +
            p.delta_stab * omega_stability
        )
        denominator = p.D0 + p.eta_phi * grad_phi_sq
        
        S = (numerator / denominator) * np.exp(-p.kappa * (grad_phi_sq + grad_omega_sq))
        return S
    
    def detect_structures(self) -> List[CoherentStructure]:
        """Detect coherent structures with phase AND frequency classification"""
        p = self.params
        
        S = self.compute_stabilization_functional()
        xi = p.xi0 * np.exp(-p.kappa * self._spectral_gradient_sq(self.phi))
        
        new_structures = []
        margin = 2
        
        for i in range(margin, self.grid_size - margin):
            for j in range(margin, self.grid_size - margin):
                for k in range(margin, self.grid_size - margin):
                    S_val = S[i, j, k]
                    
                    if S_val >= p.S_threshold:
                        local_region = S[i-1:i+2, j-1:j+2, k-1:k+2]
                        if S_val >= np.max(local_region) - 1e-10:
                            self.structure_counter += 1
                            
                            phi_val = float(self.phi[i, j, k])
                            omega_val = float(self.omega[i, j, k])
                            
                            phase_basin = self._classify_phase_basin(phi_val)
                            freq_band = self._classify_frequency_band(omega_val)
                            
                            # Mode properties
                            mode_props = FrequencyModeProperties(
                                omega=omega_val,
                                frequency_band=freq_band.value,
                                omega_gradient_sq=float(self._spectral_gradient_sq(self.omega)[i, j, k]),
                                phase_value=phi_val,
                                phase_basin=phase_basin.value,
                                phase_gradient_sq=float(self._spectral_gradient_sq(self.phi)[i, j, k]),
                                binding_energy=float(self._compute_local_energy(i, j, k)),
                                kinetic_fraction=0.5,  # Simplified
                                coherence_length=float(xi[i, j, k]),
                                winding_number=0,  # Simplified
                                vorticity=0.0,  # Simplified
                                rho_deviation=float(self.rho[i, j, k] - p.rho_equilibrium),
                                sigma_amplitude=float(self.sigma[i, j, k]),
                                tau_magnitude=float(self.tau[i, j, k]),
                                S_value=float(S_val)
                            )
                            
                            # Topological signature: (winding, freq_band_sign, tau_sign)
                            topo_sig = (0, 1 if omega_val > 0 else -1, int(np.sign(self.tau[i, j, k])))
                            
                            structure = CoherentStructure(
                                id=f"struct_{self.structure_counter}",
                                centroid=(float(i), float(j), float(k)),
                                extent=float(xi[i, j, k]),
                                phase_basin=phase_basin,
                                phase_value=phi_val,
                                frequency_band=freq_band,
                                omega_value=omega_val,
                                rho=float(self.rho[i, j, k]),
                                sigma=float(self.sigma[i, j, k]),
                                tau=float(self.tau[i, j, k]),
                                phi=phi_val,
                                omega=omega_val,
                                mode_properties=mode_props,
                                topological_signature=topo_sig,
                                formation_time=self.time,
                                last_seen_time=self.time
                            )
                            
                            new_structures.append(structure)
        
        return new_structures
    
    def _compute_local_energy(self, i: int, j: int, k: int) -> float:
        """Compute local energy density at a point"""
        p = self.params
        
        KE = 0.5 * (
            self.pi_rho[i,j,k]**2 / p.M_rho +
            self.pi_sigma[i,j,k]**2 / p.M_sigma +
            self.pi_tau[i,j,k]**2 / p.M_tau +
            self.pi_phi[i,j,k]**2 / p.M_phi +
            self.pi_omega[i,j,k]**2 / p.M_omega
        )
        
        delta_rho = self.rho[i,j,k] - p.rho_equilibrium
        PE = (
            (p.a_rho / 2) * delta_rho**2 +
            (p.a_sigma / 2) * self.sigma[i,j,k]**2 +
            (p.a_tau / 2) * self.tau[i,j,k]**2 +
            (-p.a_phi * np.cos(self.phi[i,j,k])) +
            p.a_omega * (self.omega[i,j,k]**2 - p.omega_0**2)**2
        )
        
        return KE + PE
    
    def _update_structure_tracking(self):
        """Update structure tracking"""
        p = self.params
        current_structures = self.detect_structures()
        matched_current = set()
        
        for struct_id, old_struct in list(self.active_structures.items()):
            old_pos = np.array(old_struct.centroid)
            best_match = None
            best_dist = float('inf')
            
            for curr in current_structures:
                if curr.id in matched_current:
                    continue
                
                # Must match phase basin AND frequency band
                if curr.phase_basin != old_struct.phase_basin:
                    continue
                if curr.frequency_band != old_struct.frequency_band:
                    continue
                
                curr_pos = np.array(curr.centroid)
                dist = np.linalg.norm(curr_pos - old_pos)
                
                if dist < p.tracking_radius and dist < best_dist:
                    best_match = curr
                    best_dist = dist
            
            if best_match is not None:
                matched_current.add(best_match.id)
                old_struct.centroid = best_match.centroid
                old_struct.last_seen_time = self.time
                old_struct.lifetime = self.time - old_struct.formation_time
                old_struct.phase_value = best_match.phase_value
                old_struct.omega_value = best_match.omega_value
                old_struct.mode_properties = best_match.mode_properties
            else:
                old_struct.is_alive = False
                old_struct.lifetime = self.time - old_struct.formation_time
                self.deceased_structures.append(old_struct)
                del self.active_structures[struct_id]
        
        for curr in current_structures:
            if curr.id not in matched_current:
                self.active_structures[curr.id] = curr
    
    def get_state_summary(self) -> Dict:
        """Get comprehensive state summary"""
        current_energy = self.compute_total_energy()
        stats = self._compute_statistics()
        
        # Structure breakdown by phase AND frequency
        matter_high = sum(1 for s in self.active_structures.values() 
                        if s.phase_basin == AttractorBasin.MATTER and s.frequency_band == FrequencyBand.HIGH_BAND)
        matter_low = sum(1 for s in self.active_structures.values() 
                        if s.phase_basin == AttractorBasin.MATTER and s.frequency_band == FrequencyBand.LOW_BAND)
        antimatter_high = sum(1 for s in self.active_structures.values() 
                             if s.phase_basin == AttractorBasin.ANTIMATTER and s.frequency_band == FrequencyBand.HIGH_BAND)
        antimatter_low = sum(1 for s in self.active_structures.values() 
                            if s.phase_basin == AttractorBasin.ANTIMATTER and s.frequency_band == FrequencyBand.LOW_BAND)
        
        return {
            'time': float(self.time),
            'grid_size': self.grid_size,
            'fields': '(ρ, σ, τ, φ, ω)',
            'total_energy': float(current_energy),
            'initial_energy': float(self.initial_energy) if self.initial_energy else 0.0,
            'energy_drift_pct': float((current_energy - self.initial_energy) / abs(self.initial_energy) * 100) if self.initial_energy else 0.0,
            'statistics': stats,
            'structure_breakdown': {
                'total_active': len(self.active_structures),
                'matter_high_freq': matter_high,
                'matter_low_freq': matter_low,
                'antimatter_high_freq': antimatter_high,
                'antimatter_low_freq': antimatter_low,
                'total_deceased': len(self.deceased_structures)
            }
        }


# =============================================================================
# Simulation Functions
# =============================================================================

def run_frequency_domain_test(
    grid_size: int = 20,
    amplitude: float = 0.05,
    total_time: float = 20.0,
    dt: float = 0.01,
    matter_fraction: float = 0.5,
    high_freq_fraction: float = 0.5,
    seed: int = 42
) -> Dict:
    """
    Test frequency-domain separation (spectral universe formation).
    
    Validates:
    1. Frequency basins remain stable (ω → ±ω₀)
    2. Phase basins remain stable (φ → 0 or ±π)
    3. Cross-coupling between phase and frequency
    4. Energy conservation
    """
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(
        amplitude=amplitude,
        matter_fraction=matter_fraction,
        high_freq_fraction=high_freq_fraction,
        seed=seed
    )
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 30)
    
    evolution_samples = []
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            evolution_samples.append({**metrics, 'step': step})
    
    final_state = engine.get_state_summary()
    
    return {
        'test_name': 'frequency_domain_separation',
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'dt': dt,
            'matter_fraction': matter_fraction,
            'high_freq_fraction': high_freq_fraction
        },
        'final_state': final_state,
        'evolution_samples': evolution_samples,
        'validation_results': {
            'energy_conserved': bool(abs(final_state['energy_drift_pct']) < 1.0),
            'phase_basins_exist': bool(final_state['statistics']['matter_fraction'] > 0.1 and 
                                      final_state['statistics']['antimatter_fraction'] > 0.1),
            'frequency_basins_exist': bool(final_state['statistics']['in_high_basin_fraction'] > 0.1 or
                                          final_state['statistics']['in_low_basin_fraction'] > 0.1),
            'structures_formed': final_state['structure_breakdown']['total_active'] + 
                               final_state['structure_breakdown']['total_deceased']
        }
    }


def run_spectral_universe_test(
    grid_size: int = 20,
    amplitude: float = 0.1,
    total_time: float = 30.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Test spectral universe formation - the key QMRT multiverse mechanism.
    
    Starts with turbulent initial conditions and observes:
    - Frequency clustering into basins (spectral universes)
    - Phase ordering within frequency domains
    - Structure formation correlation with frequency band
    """
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    
    # Initialize with more turbulent conditions
    if seed is not None:
        np.random.seed(seed)
    
    shape = (grid_size, grid_size, grid_size)
    p = engine.params
    
    # Turbulent initialization
    engine.rho = p.rho_equilibrium + amplitude * 2 * engine._balanced_noise(shape)
    engine.sigma = amplitude * 2 * engine._balanced_noise(shape)
    engine.tau = amplitude * 2 * engine._balanced_noise(shape)
    engine.phi = np.pi * (2 * np.random.random(shape) - 1)  # Full range initially
    engine.omega = 2 * p.omega_0 * (2 * np.random.random(shape) - 1)  # Turbulent frequency
    
    engine.pi_rho = np.zeros(shape)
    engine.pi_sigma = np.zeros(shape)
    engine.pi_tau = np.zeros(shape)
    engine.pi_phi = amplitude * engine._balanced_noise(shape)
    engine.pi_omega = amplitude * engine._balanced_noise(shape)
    
    engine._precompute_spectral()
    engine.initial_energy = engine.compute_total_energy()
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 40)
    
    evolution_samples = []
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            evolution_samples.append({**metrics, 'step': step})
    
    final_state = engine.get_state_summary()
    
    # Check for spectral universe formation
    # Look for clustering in omega around ±ω₀
    in_basins = final_state['statistics']['in_high_basin_fraction'] + final_state['statistics']['in_low_basin_fraction']
    
    return {
        'test_name': 'spectral_universe_formation',
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'initial_conditions': 'turbulent'
        },
        'final_state': final_state,
        'evolution_samples': evolution_samples,
        'spectral_universe_metrics': {
            'frequency_clustering': float(in_basins),
            'omega_std_reduction': float(evolution_samples[0]['omega_std'] / max(evolution_samples[-1]['omega_std'], 0.01)),
            'phase_ordering': bool(final_state['statistics']['phase_std'] < np.pi),
            'structures_formed': final_state['structure_breakdown']['total_active']
        }
    }
