"""
QMRT Quark-Level Substrate Engine

Foundational implementation focusing on:
1. Dual-phase attractors (matter φ≈0, antimatter φ≈π)
2. Structure identity tracking across timesteps
3. Phase-resolved stability and lifetime metrics
4. Quark-like structure emergence from substrate dynamics

QMRT is the foundational theory - quarks emerge from the quark medium substrate.
All other physics (hadrons, atoms, etc.) branches from this foundation.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid


class PhaseType(Enum):
    """Classification based on coherence phase φ"""
    MATTER = "matter"           # φ ≈ 0 (or 2πn)
    ANTIMATTER = "antimatter"   # φ ≈ π (or π + 2πn)
    TRANSITIONAL = "transitional"  # Intermediate phase (unstable)


class QuarkType(Enum):
    """
    Quark classification based on substrate properties.
    In QMRT, quark flavors emerge from different stable configurations
    of the substrate fields (ρ, σ, τ, φ).
    """
    # First generation (lightest, most stable)
    UP = "up"           # Charge +2/3
    DOWN = "down"       # Charge -1/3
    
    # Second generation
    CHARM = "charm"     # Charge +2/3, heavier
    STRANGE = "strange" # Charge -1/3, heavier
    
    # Third generation (heaviest)
    TOP = "top"         # Charge +2/3, heaviest
    BOTTOM = "bottom"   # Charge -1/3, heaviest
    
    # Undetermined (structure exists but doesn't match known quark)
    PROTO = "proto"     # Proto-quark, not yet classified
    UNSTABLE = "unstable"  # Unstable configuration


@dataclass
class QuarkStructure:
    """
    A quark-like structure emerging from QMRT substrate dynamics.
    
    Quarks in QMRT are stable vortex-like configurations in the
    quark medium with specific phase, torsion, and density characteristics.
    """
    # Identity
    id: str
    
    # Spatial location (can change over time)
    position: Tuple[float, float, float]
    
    # Phase classification (matter/antimatter)
    phase_type: PhaseType
    phase_value: float  # Actual φ value at structure center
    
    # Quark classification
    quark_type: QuarkType
    is_antiquark: bool  # True if antimatter phase
    
    # Substrate field values at structure
    rho: float      # Density
    sigma: float    # Tension
    tau: float      # Torsion magnitude
    tau_vector: Tuple[float, float, float]  # Torsion direction (for color?)
    
    # Stability metrics
    S_value: float          # Stabilization functional
    xi_value: float         # Coherence length
    binding_energy: float   # Local energy concentration
    
    # Lifetime tracking
    formation_time: float
    last_seen_time: float
    lifetime: float = 0.0
    is_alive: bool = True
    
    # Tracking history
    position_history: List[Tuple[float, float, float]] = field(default_factory=list)
    stability_history: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'position': self.position,
            'phase_type': self.phase_type.value,
            'phase_value': float(self.phase_value),
            'quark_type': self.quark_type.value,
            'is_antiquark': self.is_antiquark,
            'rho': float(self.rho),
            'sigma': float(self.sigma),
            'tau': float(self.tau),
            'S_value': float(self.S_value),
            'xi_value': float(self.xi_value),
            'binding_energy': float(self.binding_energy),
            'formation_time': float(self.formation_time),
            'lifetime': float(self.lifetime),
            'is_alive': self.is_alive
        }


@dataclass 
class QMRTQuarkParameters:
    """
    Parameters for quark-level QMRT simulation.
    
    These parameters control the dual-phase attractor dynamics
    and quark structure formation.
    """
    # Mass parameters
    M_rho: float = 1.0
    M_sigma: float = 1.0
    M_tau: float = 1.0
    M_phi: float = 1.0
    
    # Density potential (equilibrium at ρ=1)
    rho_equilibrium: float = 1.0
    a_rho: float = 0.1
    c_rho: float = 0.02
    
    # Other field potentials
    a_sigma: float = 0.1
    a_tau: float = 0.1
    
    # PHASE POTENTIAL - Critical for dual-phase attractors
    # U_φ(φ) = -a_phi * cos(φ) creates minima at φ=0 and φ=π
    # This is the key to matter/antimatter symmetry
    a_phi: float = 0.2  # Strength of phase potential
    
    # Coupling constants
    lambda_rho_sigma: float = 0.02
    lambda_rho_tau: float = 0.02
    lambda_sigma_tau: float = 0.02
    lambda_sigma_phi: float = 0.02
    lambda_tau_phi: float = 0.02
    lambda_rho_phi: float = 0.02
    
    # Gradient energy coefficients
    K_rho: float = 0.5
    K_sigma: float = 0.5
    K_tau: float = 0.5
    K_phi: float = 0.5
    
    # Stabilization functional parameters
    alpha_stab: float = 1.0
    beta_stab: float = 0.5
    gamma_stab: float = 0.3
    D0: float = 0.1
    eta_phi: float = 0.5
    kappa: float = 0.2
    xi0: float = 1.0
    
    # Phase classification thresholds
    phase_matter_threshold: float = np.pi / 4      # |φ| < π/4 → matter
    phase_antimatter_threshold: float = 3 * np.pi / 4  # |φ - π| < π/4 → antimatter
    
    # Quark classification thresholds (based on S_value and binding energy)
    quark_S_threshold: float = 0.3  # Minimum S for quark-like structure
    
    # Structure tracking parameters
    tracking_radius: float = 2.0  # Max distance to match structure across timesteps
    min_lifetime_for_stable: float = 1.0  # Minimum lifetime to be "stable"


class QMRTQuarkEngine:
    """
    QMRT engine focused on quark-level substrate dynamics.
    
    Key features:
    1. Dual-phase potential creating symmetric matter/antimatter attractors
    2. Structure identity tracking across timesteps
    3. Phase-resolved lifetime metrics
    4. Quark classification based on substrate properties
    """
    
    def __init__(self, grid_size: int = 32, dx: float = 1.0,
                 params: Optional[QMRTQuarkParameters] = None):
        self.grid_size = grid_size
        self.dx = dx
        self.time = 0.0
        
        self.params = params or QMRTQuarkParameters()
        
        # Fields
        self.rho = None    # Density
        self.sigma = None  # Tension
        self.tau = None    # Torsion (scalar for now)
        self.phi = None    # Phase (critical for matter/antimatter)
        
        # Conjugate momenta
        self.pi_rho = None
        self.pi_sigma = None
        self.pi_tau = None
        self.pi_phi = None
        
        # Structure tracking
        self.active_structures: Dict[str, QuarkStructure] = {}
        self.deceased_structures: List[QuarkStructure] = []
        self.structure_counter = 0
        
        # Energy tracking
        self.initial_energy = None
        self.energy_history: List[float] = []
        
        # Spectral Laplacian precomputation
        self._k_sq = None
        self._kx = None
        self._ky = None
        self._kz = None
        
    def initialize_dual_phase(self, amplitude: float = 0.05, 
                              matter_fraction: float = 0.5,
                              seed: Optional[int] = None):
        """
        Initialize substrate with dual-phase seeds.
        
        Creates initial conditions with both matter (φ≈0) and 
        antimatter (φ≈π) regions to test symmetric attractor dynamics.
        
        Args:
            amplitude: Fluctuation amplitude for fields
            matter_fraction: Fraction of domain initialized as matter vs antimatter
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)
            
        shape = (self.grid_size, self.grid_size, self.grid_size)
        p = self.params
        
        # Initialize density at equilibrium with small fluctuations
        self.rho = p.rho_equilibrium + amplitude * self._balanced_noise(shape)
        
        # Initialize tension and torsion with small fluctuations
        self.sigma = amplitude * self._balanced_noise(shape)
        self.tau = amplitude * self._balanced_noise(shape)
        
        # Initialize phase with DUAL-PHASE structure
        # Create matter (φ≈0) and antimatter (φ≈π) regions
        self.phi = np.zeros(shape)
        
        # Random assignment of matter/antimatter regions
        matter_mask = np.random.random(shape) < matter_fraction
        self.phi[matter_mask] = amplitude * np.random.randn(np.sum(matter_mask))  # Near 0
        self.phi[~matter_mask] = np.pi + amplitude * np.random.randn(np.sum(~matter_mask))  # Near π
        
        # Initialize momenta at zero
        self.pi_rho = np.zeros(shape)
        self.pi_sigma = np.zeros(shape)
        self.pi_tau = np.zeros(shape)
        self.pi_phi = np.zeros(shape)
        
        # Precompute spectral coefficients
        self._precompute_spectral()
        
        # Record initial energy
        self.initial_energy = self.compute_total_energy()
        
        # Count initial phase distribution
        matter_count = np.sum(np.abs(self.phi) < np.pi/2)
        antimatter_count = np.sum(np.abs(self.phi - np.pi) < np.pi/2)
        
        print(f"QMRT Quark Engine initialized")
        print(f"  Grid: {self.grid_size}³")
        print(f"  Initial energy: {self.initial_energy:.4f}")
        print(f"  Matter regions: {matter_count} ({100*matter_count/self.phi.size:.1f}%)")
        print(f"  Antimatter regions: {antimatter_count} ({100*antimatter_count/self.phi.size:.1f}%)")
        
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
        
        Includes the dual-phase potential U_φ = -a_φ cos(φ)
        which creates symmetric minima at φ=0 and φ=π.
        """
        p = self.params
        
        # Kinetic energy
        KE = 0.5 * (
            np.sum(self.pi_rho**2) / p.M_rho +
            np.sum(self.pi_sigma**2) / p.M_sigma +
            np.sum(self.pi_tau**2) / p.M_tau +
            np.sum(self.pi_phi**2) / p.M_phi
        ) * self.dx**3
        
        # Density potential (centered at equilibrium)
        delta_rho = self.rho - p.rho_equilibrium
        U_rho = np.sum(
            (p.a_rho / 2) * delta_rho**2 +
            (p.c_rho / 4) * delta_rho**4
        ) * self.dx**3
        
        # Harmonic potentials for σ and τ
        V_harmonic = np.sum(
            (p.a_sigma / 2) * self.sigma**2 +
            (p.a_tau / 2) * self.tau**2
        ) * self.dx**3
        
        # DUAL-PHASE POTENTIAL: U_φ = -a_φ cos(φ)
        # This creates symmetric minima at φ=0 (matter) and φ=π (antimatter)
        U_phi = np.sum(-p.a_phi * np.cos(self.phi)) * self.dx**3
        
        # Coupling energies
        V_coupling = np.sum(
            p.lambda_rho_sigma * delta_rho * self.sigma +
            p.lambda_rho_tau * delta_rho * self.tau**2 +
            p.lambda_sigma_tau * self.sigma * self.tau +
            p.lambda_sigma_phi * self.sigma * np.cos(self.phi) +  # Phase-dependent coupling
            p.lambda_tau_phi * self.tau**2 * np.cos(self.phi) +
            p.lambda_rho_phi * delta_rho * np.cos(self.phi)
        ) * self.dx**3
        
        # Gradient energies
        V_gradient = 0.5 * np.sum(
            p.K_rho * self._spectral_gradient_sq(self.rho) +
            p.K_sigma * self._spectral_gradient_sq(self.sigma) +
            p.K_tau * self._spectral_gradient_sq(self.tau) +
            p.K_phi * self._spectral_gradient_sq(self.phi)
        ) * self.dx**3
        
        return KE + U_rho + V_harmonic + U_phi + V_coupling + V_gradient
    
    def _compute_kinetic_energy(self) -> float:
        """Compute kinetic energy only"""
        p = self.params
        return 0.5 * (
            np.sum(self.pi_rho**2) / p.M_rho +
            np.sum(self.pi_sigma**2) / p.M_sigma +
            np.sum(self.pi_tau**2) / p.M_tau +
            np.sum(self.pi_phi**2) / p.M_phi
        ) * self.dx**3
    
    def evolve_timestep(self, dt: float, enforce_conservation: bool = True) -> Dict:
        """
        Evolve one timestep using Yoshida 4th-order symplectic integrator.
        
        The phase potential U_φ = -a_φ cos(φ) ensures symmetric evolution
        toward the two attractor states (matter and antimatter).
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
        
        # Enforce energy conservation
        if enforce_conservation:
            self._enforce_energy_conservation()
        
        self.time += dt
        
        # Track energy
        current_energy = self.compute_total_energy()
        self.energy_history.append(current_energy)
        
        # Update structure tracking
        self._update_structure_tracking()
        
        # Compute phase statistics
        phase_stats = self._compute_phase_statistics()
        
        return {
            'time': self.time,
            'energy': current_energy,
            'energy_drift': (current_energy - self.initial_energy) / abs(self.initial_energy) if self.initial_energy else 0,
            'mean_rho': float(np.mean(self.rho)),
            'mean_phi': float(np.mean(self.phi)),
            **phase_stats,
            'active_structures': len(self.active_structures),
            'total_formed': self.structure_counter,
            'total_deceased': len(self.deceased_structures)
        }
    
    def _update_momenta(self, delta_t: float):
        """Update momenta using Hamilton's equations with dual-phase potential"""
        p = self.params
        
        # Spectral Laplacians
        lap_rho = self._spectral_laplacian(self.rho)
        lap_sigma = self._spectral_laplacian(self.sigma)
        lap_tau = self._spectral_laplacian(self.tau)
        lap_phi = self._spectral_laplacian(self.phi)
        
        delta_rho = self.rho - p.rho_equilibrium
        
        # Density momentum: standard terms
        dpi_rho_dt = (
            p.K_rho * lap_rho
            - (p.a_rho * delta_rho + p.c_rho * delta_rho**3)
            - p.lambda_rho_sigma * self.sigma
            - p.lambda_rho_tau * self.tau**2
            - p.lambda_rho_phi * np.cos(self.phi)
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
        
        # PHASE MOMENTUM - includes dual-phase potential derivative
        # dU_φ/dφ = a_φ sin(φ) → pushes toward minima at 0 and π
        dpi_phi_dt = (
            p.K_phi * lap_phi
            - p.a_phi * np.sin(self.phi)  # Dual-phase attractor force
            + p.lambda_sigma_phi * self.sigma * np.sin(self.phi)
            + p.lambda_tau_phi * self.tau**2 * np.sin(self.phi)
            + p.lambda_rho_phi * delta_rho * np.sin(self.phi)
        )
        
        self.pi_rho += dpi_rho_dt * delta_t
        self.pi_sigma += dpi_sigma_dt * delta_t
        self.pi_tau += dpi_tau_dt * delta_t
        self.pi_phi += dpi_phi_dt * delta_t
    
    def _update_fields(self, delta_t: float):
        """Update field values"""
        p = self.params
        self.rho += (self.pi_rho / p.M_rho) * delta_t
        self.sigma += (self.pi_sigma / p.M_sigma) * delta_t
        self.tau += (self.pi_tau / p.M_tau) * delta_t
        self.phi += (self.pi_phi / p.M_phi) * delta_t
    
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
    
    def _compute_phase_statistics(self) -> Dict:
        """Compute statistics about phase distribution"""
        p = self.params
        
        # Normalize phase to [-π, π]
        phi_norm = np.mod(self.phi + np.pi, 2*np.pi) - np.pi
        
        # Count matter (near 0) and antimatter (near ±π)
        matter_count = np.sum(np.abs(phi_norm) < p.phase_matter_threshold)
        antimatter_count = np.sum(np.abs(np.abs(phi_norm) - np.pi) < (np.pi - p.phase_antimatter_threshold))
        transitional_count = self.phi.size - matter_count - antimatter_count
        
        return {
            'matter_fraction': matter_count / self.phi.size,
            'antimatter_fraction': antimatter_count / self.phi.size,
            'transitional_fraction': transitional_count / self.phi.size,
            'phase_mean': float(np.mean(phi_norm)),
            'phase_std': float(np.std(phi_norm))
        }
    
    def _classify_phase(self, phi_value: float) -> PhaseType:
        """Classify a phase value as matter, antimatter, or transitional"""
        p = self.params
        
        # Normalize to [-π, π]
        phi_norm = np.mod(phi_value + np.pi, 2*np.pi) - np.pi
        
        if np.abs(phi_norm) < p.phase_matter_threshold:
            return PhaseType.MATTER
        elif np.abs(np.abs(phi_norm) - np.pi) < (np.pi - p.phase_antimatter_threshold):
            return PhaseType.ANTIMATTER
        else:
            return PhaseType.TRANSITIONAL
    
    def _classify_quark(self, structure: QuarkStructure) -> QuarkType:
        """
        Classify a structure as a specific quark type based on properties.
        
        In QMRT, different quark flavors correspond to different stable
        configurations of the substrate fields. This is a simplified
        classification based on stability and binding energy.
        """
        p = self.params
        
        # Not stable enough to be a quark
        if structure.S_value < p.quark_S_threshold:
            return QuarkType.UNSTABLE
        
        # Classification based on binding energy and other properties
        # This is a simplified model - real QMRT would have more detailed criteria
        
        # Higher binding energy → heavier quarks
        # Torsion sign/magnitude affects charge-like properties
        
        if structure.binding_energy < 0.5:
            # Light quarks (first generation)
            if structure.tau > 0:
                return QuarkType.UP
            else:
                return QuarkType.DOWN
        elif structure.binding_energy < 1.0:
            # Medium quarks (second generation)
            if structure.tau > 0:
                return QuarkType.CHARM
            else:
                return QuarkType.STRANGE
        else:
            # Heavy quarks (third generation)
            if structure.tau > 0:
                return QuarkType.TOP
            else:
                return QuarkType.BOTTOM
    
    def compute_stabilization_functional(self) -> np.ndarray:
        """Compute S(x,t) for structure detection"""
        p = self.params
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        
        numerator = (
            p.alpha_stab * np.abs(self.rho - p.rho_equilibrium) +
            p.beta_stab * np.abs(self.sigma) +
            p.gamma_stab * self.tau**2
        )
        denominator = p.D0 + p.eta_phi * grad_phi_sq
        
        S = (numerator / denominator) * np.exp(-p.kappa * grad_phi_sq)
        return S
    
    def compute_coherence_length(self) -> np.ndarray:
        """Compute ξ(x,t)"""
        p = self.params
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        return p.xi0 * np.exp(-p.kappa * grad_phi_sq)
    
    def compute_binding_energy(self) -> np.ndarray:
        """
        Compute local binding energy density.
        
        High binding energy indicates strongly bound structure.
        """
        p = self.params
        
        # Kinetic energy density
        KE_density = 0.5 * (
            self.pi_rho**2 / p.M_rho +
            self.pi_sigma**2 / p.M_sigma +
            self.pi_tau**2 / p.M_tau +
            self.pi_phi**2 / p.M_phi
        )
        
        # Potential energy density
        delta_rho = self.rho - p.rho_equilibrium
        PE_density = (
            (p.a_rho / 2) * delta_rho**2 +
            (p.a_sigma / 2) * self.sigma**2 +
            (p.a_tau / 2) * self.tau**2 +
            (-p.a_phi * np.cos(self.phi))
        )
        
        return KE_density + PE_density
    
    def detect_structures(self) -> List[QuarkStructure]:
        """
        Detect quark-like structures in the substrate.
        
        Returns new structures found this timestep.
        """
        p = self.params
        
        S = self.compute_stabilization_functional()
        xi = self.compute_coherence_length()
        binding = self.compute_binding_energy()
        
        new_structures = []
        
        # Find local maxima of S above threshold
        for i in range(2, self.grid_size - 2):
            for j in range(2, self.grid_size - 2):
                for k in range(2, self.grid_size - 2):
                    S_val = S[i, j, k]
                    
                    if S_val >= p.quark_S_threshold:
                        # Check if local maximum
                        local_region = S[i-1:i+2, j-1:j+2, k-1:k+2]
                        if S_val >= np.max(local_region) - 1e-10:
                            # This is a structure
                            self.structure_counter += 1
                            
                            phi_val = self.phi[i, j, k]
                            phase_type = self._classify_phase(phi_val)
                            
                            structure = QuarkStructure(
                                id=f"quark_{self.structure_counter}",
                                position=(float(i), float(j), float(k)),
                                phase_type=phase_type,
                                phase_value=float(phi_val),
                                quark_type=QuarkType.PROTO,  # Will classify after
                                is_antiquark=(phase_type == PhaseType.ANTIMATTER),
                                rho=float(self.rho[i, j, k]),
                                sigma=float(self.sigma[i, j, k]),
                                tau=float(self.tau[i, j, k]),
                                tau_vector=(0.0, 0.0, float(self.tau[i, j, k])),
                                S_value=float(S_val),
                                xi_value=float(xi[i, j, k]),
                                binding_energy=float(binding[i, j, k]),
                                formation_time=self.time,
                                last_seen_time=self.time
                            )
                            
                            # Classify quark type
                            structure.quark_type = self._classify_quark(structure)
                            
                            new_structures.append(structure)
        
        return new_structures
    
    def _update_structure_tracking(self):
        """
        Update structure tracking across timesteps.
        
        Matches current structures to previously known ones,
        updates lifetimes, and marks deceased structures.
        """
        p = self.params
        
        # Detect current structures
        current_structures = self.detect_structures()
        
        # Build position lookup for current structures
        current_positions = {s.id: np.array(s.position) for s in current_structures}
        
        # Try to match existing structures to current ones
        matched_current = set()
        
        for struct_id, old_struct in list(self.active_structures.items()):
            old_pos = np.array(old_struct.position)
            
            # Find closest current structure within tracking radius
            best_match = None
            best_dist = float('inf')
            
            for curr in current_structures:
                if curr.id in matched_current:
                    continue
                    
                curr_pos = np.array(curr.position)
                dist = np.linalg.norm(curr_pos - old_pos)
                
                if dist < p.tracking_radius and dist < best_dist:
                    # Also check phase consistency
                    if old_struct.phase_type == curr.phase_type:
                        best_match = curr
                        best_dist = dist
            
            if best_match is not None:
                # Match found - update existing structure
                matched_current.add(best_match.id)
                
                old_struct.position = best_match.position
                old_struct.last_seen_time = self.time
                old_struct.lifetime = self.time - old_struct.formation_time
                old_struct.S_value = best_match.S_value
                old_struct.rho = best_match.rho
                old_struct.sigma = best_match.sigma
                old_struct.tau = best_match.tau
                old_struct.phase_value = best_match.phase_value
                old_struct.binding_energy = best_match.binding_energy
                
                # Track history
                old_struct.position_history.append(best_match.position)
                old_struct.stability_history.append(best_match.S_value)
                
                # Keep only recent history
                if len(old_struct.position_history) > 100:
                    old_struct.position_history = old_struct.position_history[-100:]
                    old_struct.stability_history = old_struct.stability_history[-100:]
            else:
                # No match - structure has died
                old_struct.is_alive = False
                old_struct.lifetime = self.time - old_struct.formation_time
                self.deceased_structures.append(old_struct)
                del self.active_structures[struct_id]
        
        # Add new structures (those not matched to existing)
        for curr in current_structures:
            if curr.id not in matched_current:
                self.active_structures[curr.id] = curr
    
    def get_phase_resolved_statistics(self) -> Dict:
        """
        Get detailed statistics broken down by phase type.
        """
        matter_structures = [s for s in self.active_structures.values() 
                           if s.phase_type == PhaseType.MATTER]
        antimatter_structures = [s for s in self.active_structures.values() 
                                if s.phase_type == PhaseType.ANTIMATTER]
        
        def compute_stats(structures: List[QuarkStructure]) -> Dict:
            if not structures:
                return {'count': 0, 'avg_lifetime': 0, 'avg_S': 0, 'avg_binding': 0}
            return {
                'count': len(structures),
                'avg_lifetime': np.mean([s.lifetime for s in structures]),
                'avg_S': np.mean([s.S_value for s in structures]),
                'avg_binding': np.mean([s.binding_energy for s in structures])
            }
        
        return {
            'matter': compute_stats(matter_structures),
            'antimatter': compute_stats(antimatter_structures),
            'total_active': len(self.active_structures),
            'total_deceased': len(self.deceased_structures)
        }
    
    def get_quark_census(self) -> Dict:
        """
        Get census of quark types (including antiquarks).
        """
        census = {qt.value: {'matter': 0, 'antimatter': 0} for qt in QuarkType}
        
        for s in self.active_structures.values():
            phase_key = 'antimatter' if s.is_antiquark else 'matter'
            census[s.quark_type.value][phase_key] += 1
        
        return census
    
    def get_lifetime_distribution(self) -> Dict:
        """
        Get lifetime distribution for matter vs antimatter structures.
        """
        matter_lifetimes = [s.lifetime for s in self.deceased_structures 
                          if s.phase_type == PhaseType.MATTER]
        antimatter_lifetimes = [s.lifetime for s in self.deceased_structures 
                               if s.phase_type == PhaseType.ANTIMATTER]
        
        def compute_distribution(lifetimes: List[float]) -> Dict:
            if not lifetimes:
                return {'count': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0}
            return {
                'count': len(lifetimes),
                'mean': float(np.mean(lifetimes)),
                'std': float(np.std(lifetimes)),
                'max': float(np.max(lifetimes)),
                'min': float(np.min(lifetimes))
            }
        
        return {
            'matter': compute_distribution(matter_lifetimes),
            'antimatter': compute_distribution(antimatter_lifetimes)
        }
    
    def get_state_summary(self) -> Dict:
        """Get comprehensive state summary"""
        current_energy = self.compute_total_energy()
        phase_stats = self._compute_phase_statistics()
        quark_census = self.get_quark_census()
        lifetime_dist = self.get_lifetime_distribution()
        
        return {
            'time': self.time,
            'grid_size': self.grid_size,
            'total_energy': current_energy,
            'initial_energy': self.initial_energy,
            'energy_drift_pct': (current_energy - self.initial_energy) / abs(self.initial_energy) * 100 if self.initial_energy else 0,
            'phase_statistics': phase_stats,
            'structure_statistics': self.get_phase_resolved_statistics(),
            'quark_census': quark_census,
            'lifetime_distribution': lifetime_dist,
            'mean_rho': float(np.mean(self.rho)),
            'mean_phi': float(np.mean(self.phi))
        }


def run_dual_phase_test(
    grid_size: int = 24,
    amplitude: float = 0.05,
    total_time: float = 20.0,
    dt: float = 0.01,
    matter_fraction: float = 0.5,
    seed: int = 42
) -> Dict:
    """
    Run a test of dual-phase attractor dynamics.
    
    Tests whether matter (φ≈0) and antimatter (φ≈π) states
    are symmetric stable attractors.
    """
    engine = QMRTQuarkEngine(grid_size=grid_size)
    engine.initialize_dual_phase(amplitude=amplitude, matter_fraction=matter_fraction, seed=seed)
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 20)
    
    evolution_samples = []
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            sample = {
                **metrics,
                'step': step
            }
            evolution_samples.append(sample)
    
    return {
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'dt': dt,
            'matter_fraction': matter_fraction
        },
        'final_state': engine.get_state_summary(),
        'evolution_samples': evolution_samples,
        'phase_symmetry': {
            'matter_fraction_initial': matter_fraction,
            'matter_fraction_final': evolution_samples[-1]['matter_fraction'] if evolution_samples else 0,
            'antimatter_fraction_final': evolution_samples[-1]['antimatter_fraction'] if evolution_samples else 0,
            'symmetric': abs(evolution_samples[-1]['matter_fraction'] - evolution_samples[-1]['antimatter_fraction']) < 0.1 if evolution_samples else False
        }
    }
