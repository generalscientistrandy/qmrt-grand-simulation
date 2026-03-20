"""
QMRT Quark-Level Substrate Engine - Dual-Basin Attractor Ontology

PURPOSE: Validate stable dual-basin attractor dynamics capable of forming 
         higher-order composite structures.

This is NOT about reproducing Standard Model quarks - it's about validating
that the QMRT substrate naturally produces:
1. Symmetric dual-phase attractors: φ ≈ 0 (matter-like) and φ ≈ ±π (antimatter-like)
2. Persistent coherent structures in both basins
3. Annihilation cascade when opposite-phase structures overlap

Phase Convention: φ ∈ (−π, +π)
- Symmetric around zero
- Natural dual-basin representation
- φ ≈ 0: Matter-like attractor basin
- φ ≈ ±π: Antimatter-like attractor basin (same solution family, phase-inverted)

Antimatter is NOT a separate particle species - it is a phase-inverted attractor
basin of the SAME field solution family.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid


class AttractorBasin(Enum):
    """
    Classification based on which attractor basin φ resides in.
    φ ∈ (−π, +π) symmetric around zero.
    """
    MATTER = "matter"           # φ ≈ 0 (|φ| < π/2)
    ANTIMATTER = "antimatter"   # φ ≈ ±π (|φ| > π/2)
    TRANSITIONAL = "transitional"  # Near basin boundary (unstable)


@dataclass
class FieldModeProperties:
    """
    Emergent properties from substrate field modes.
    
    Classification emerges from these properties - NOT hardcoded labels.
    Different stable configurations in the field produce different
    emergent "flavors" based on mode structure, energy, and topology.
    """
    # Energy-related modes
    binding_energy: float       # Local energy concentration
    kinetic_fraction: float     # KE / Total local energy
    
    # Spatial mode structure
    coherence_length: float     # ξ - spatial extent of structure
    mode_number: int            # Dominant spatial frequency mode
    radial_profile: str         # 'gaussian', 'vortex', 'shell', etc.
    
    # Topological properties
    winding_number: int         # Phase winding around structure (topological charge)
    vorticity: float            # Curl of phase gradient
    
    # Field amplitude modes
    rho_deviation: float        # Deviation from equilibrium density
    sigma_amplitude: float      # Tension field amplitude
    tau_magnitude: float        # Torsion magnitude
    
    # Stability metric
    S_value: float              # Stabilization functional value
    
    def to_dict(self) -> Dict:
        return {
            'binding_energy': float(self.binding_energy),
            'kinetic_fraction': float(self.kinetic_fraction),
            'coherence_length': float(self.coherence_length),
            'mode_number': int(self.mode_number),
            'radial_profile': self.radial_profile,
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
    A coherent structure emerging from QMRT substrate dynamics.
    
    NOT a "quark" in the Standard Model sense - this is a stable
    configuration in one of the dual attractor basins, with properties
    that emerge from field mode analysis.
    """
    # Identity (persistent across timesteps)
    id: str
    
    # Spatial tracking
    centroid: Tuple[float, float, float]      # Center of mass position
    extent: float                              # Spatial extent (radius)
    
    # Attractor basin
    basin: AttractorBasin
    phase_value: float          # Central φ value in (−π, +π)
    
    # Raw substrate field values at centroid
    rho: float
    sigma: float
    tau: float
    phi: float
    
    # Emergent field mode properties (basis for classification)
    mode_properties: FieldModeProperties
    
    # Topological fingerprint for tracking
    # (winding_number, dominant_mode, sign(tau))
    topological_signature: Tuple[int, int, int]
    
    # Lifetime tracking
    formation_time: float
    last_seen_time: float
    lifetime: float = 0.0
    is_alive: bool = True
    
    # History for tracking
    centroid_history: List[Tuple[float, float, float]] = field(default_factory=list)
    S_history: List[float] = field(default_factory=list)
    phase_history: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'centroid': self.centroid,
            'extent': float(self.extent),
            'basin': self.basin.value,
            'phase_value': float(self.phase_value),
            'rho': float(self.rho),
            'sigma': float(self.sigma),
            'tau': float(self.tau),
            'phi': float(self.phi),
            'mode_properties': self.mode_properties.to_dict(),
            'topological_signature': self.topological_signature,
            'formation_time': float(self.formation_time),
            'lifetime': float(self.lifetime),
            'is_alive': self.is_alive
        }


@dataclass
class AnnihilationEvent:
    """
    Records when opposite-basin structures overlap and annihilate.
    
    Annihilation causes:
    - Coherence collapse of both structures
    - Rapid phase decoherence cascade
    - Energy redistribution into substrate wave spectrum
    - Possible formation of neutral transitional attractors
    """
    time: float
    position: Tuple[float, float, float]
    
    # Participating structures
    matter_structure_id: str
    antimatter_structure_id: str
    
    # Pre-annihilation properties
    matter_energy: float
    antimatter_energy: float
    
    # Post-annihilation
    released_energy: float      # Energy released into wave spectrum
    formed_neutral: bool        # Did a neutral transitional form?
    
    def to_dict(self) -> Dict:
        return {
            'time': float(self.time),
            'position': self.position,
            'matter_structure_id': self.matter_structure_id,
            'antimatter_structure_id': self.antimatter_structure_id,
            'matter_energy': float(self.matter_energy),
            'antimatter_energy': float(self.antimatter_energy),
            'released_energy': float(self.released_energy),
            'formed_neutral': self.formed_neutral
        }


@dataclass 
class QMRTQuarkParameters:
    """
    Parameters for dual-basin attractor QMRT simulation.
    
    The key physics is the dual-basin phase potential:
    U_φ(φ) = -a_φ cos(φ)
    
    This creates symmetric minima at φ = 0 and φ = ±π.
    """
    # Mass parameters (kinetic denominators)
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
    
    # DUAL-BASIN PHASE POTENTIAL
    # U_φ(φ) = -a_phi * cos(φ) creates minima at φ=0 and φ=±π
    a_phi: float = 0.2
    
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
    
    # Basin classification threshold
    # φ ∈ (−π, +π): |φ| < π/2 → matter basin, |φ| > π/2 → antimatter basin
    basin_boundary: float = np.pi / 2
    
    # Structure detection threshold
    S_threshold: float = 0.3
    
    # Tracking parameters
    tracking_radius: float = 2.5        # Centroid matching radius
    topology_weight: float = 0.5        # Weight for topological matching (vs centroid)
    min_stable_lifetime: float = 1.0
    
    # Annihilation parameters
    annihilation_overlap_radius: float = 1.5  # Structures closer than this interact
    annihilation_phase_threshold: float = 2.5  # Phase difference for annihilation (near 2π)
    decoherence_rate: float = 0.5             # How fast phase decoherences cascade


class QMRTQuarkEngine:
    """
    QMRT engine for validating dual-basin attractor ontology.
    
    Goal: Prove that the substrate naturally produces symmetric,
    stable attractor basins at φ ≈ 0 and φ ≈ ±π, with proper
    annihilation dynamics when opposite-basin structures overlap.
    
    Phase convention: φ ∈ (−π, +π) throughout.
    """
    
    def __init__(self, grid_size: int = 32, dx: float = 1.0,
                 params: Optional[QMRTQuarkParameters] = None):
        self.grid_size = grid_size
        self.dx = dx
        self.time = 0.0
        
        self.params = params or QMRTQuarkParameters()
        
        # Fields (all real-valued)
        self.rho = None    # Density
        self.sigma = None  # Tension
        self.tau = None    # Torsion
        self.phi = None    # Phase φ ∈ (−π, +π)
        
        # Conjugate momenta
        self.pi_rho = None
        self.pi_sigma = None
        self.pi_tau = None
        self.pi_phi = None
        
        # Structure tracking
        self.active_structures: Dict[str, CoherentStructure] = {}
        self.deceased_structures: List[CoherentStructure] = []
        self.structure_counter = 0
        
        # Annihilation events
        self.annihilation_events: List[AnnihilationEvent] = []
        
        # Energy tracking
        self.initial_energy = None
        self.energy_history: List[float] = []
        
        # Spectral precomputation
        self._k_sq = None
        self._kx = None
        self._ky = None
        self._kz = None
        
    def initialize_dual_basin(self, amplitude: float = 0.05, 
                              matter_fraction: float = 0.5,
                              seed: Optional[int] = None):
        """
        Initialize substrate with structures in both attractor basins.
        
        Creates initial conditions with:
        - Matter-like regions: φ ≈ 0
        - Antimatter-like regions: φ ≈ ±π
        
        Phase is kept in (−π, +π) throughout.
        
        Args:
            amplitude: Fluctuation amplitude
            matter_fraction: Fraction of volume initialized near φ=0
            seed: Random seed for reproducibility
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
        
        # Initialize phase with DUAL-BASIN seeds
        self.phi = np.zeros(shape)
        
        # Randomly assign cells to basins
        matter_mask = np.random.random(shape) < matter_fraction
        
        # Matter basin: small fluctuations around φ = 0
        self.phi[matter_mask] = amplitude * np.random.randn(np.sum(matter_mask))
        
        # Antimatter basin: fluctuations around φ = π (will wrap to ±π)
        # Use both +π and -π randomly for symmetry
        antimatter_count = np.sum(~matter_mask)
        antimatter_signs = 2 * (np.random.random(antimatter_count) > 0.5) - 1  # ±1
        self.phi[~matter_mask] = antimatter_signs * (np.pi - amplitude * np.abs(np.random.randn(antimatter_count)))
        
        # Enforce φ ∈ (−π, +π)
        self.phi = self._wrap_phase(self.phi)
        
        # Initialize momenta at zero
        self.pi_rho = np.zeros(shape)
        self.pi_sigma = np.zeros(shape)
        self.pi_tau = np.zeros(shape)
        self.pi_phi = np.zeros(shape)
        
        # Precompute spectral coefficients
        self._precompute_spectral()
        
        # Record initial energy
        self.initial_energy = self.compute_total_energy()
        
        # Initial basin statistics
        matter_count = np.sum(np.abs(self.phi) < p.basin_boundary)
        antimatter_count = np.sum(np.abs(self.phi) >= p.basin_boundary)
        
        print("QMRT Dual-Basin Engine initialized")
        print(f"  Grid: {self.grid_size}³, dx={self.dx}")
        print("  Phase range: φ ∈ (−π, +π)")
        print(f"  Initial energy: {self.initial_energy:.4f}")
        print(f"  Matter basin (|φ| < π/2): {100*matter_count/self.phi.size:.1f}%")
        print(f"  Antimatter basin (|φ| ≥ π/2): {100*antimatter_count/self.phi.size:.1f}%")
        
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
        """Compute Laplacian using spectral method (exact for periodic BC)"""
        f_hat = np.fft.fftn(f)
        lap_hat = -self._k_sq * f_hat
        return np.real(np.fft.ifftn(lap_hat))
    
    def _spectral_gradient(self, f: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute gradient components using spectral method"""
        f_hat = np.fft.fftn(f)
        gx = np.real(np.fft.ifftn(1j * self._kx * f_hat))
        gy = np.real(np.fft.ifftn(1j * self._ky * f_hat))
        gz = np.real(np.fft.ifftn(1j * self._kz * f_hat))
        return gx, gy, gz
    
    def _spectral_gradient_sq(self, f: np.ndarray) -> np.ndarray:
        """Compute |∇f|² using spectral method"""
        gx, gy, gz = self._spectral_gradient(f)
        return gx**2 + gy**2 + gz**2
    
    def compute_total_energy(self) -> float:
        """
        Compute total Hamiltonian energy.
        
        Includes dual-basin potential: U_φ = -a_φ cos(φ)
        Symmetric minima at φ = 0 and φ = ±π.
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
        
        # DUAL-BASIN PHASE POTENTIAL
        # U_φ = -a_φ cos(φ)
        # Minima at φ = 0 (matter) and φ = ±π (antimatter)
        U_phi = np.sum(-p.a_phi * np.cos(self.phi)) * self.dx**3
        
        # Coupling energies (phase-dependent)
        V_coupling = np.sum(
            p.lambda_rho_sigma * delta_rho * self.sigma +
            p.lambda_rho_tau * delta_rho * self.tau**2 +
            p.lambda_sigma_tau * self.sigma * self.tau +
            p.lambda_sigma_phi * self.sigma * np.cos(self.phi) +
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
        
        After field evolution:
        1. Wrap phase to (−π, +π)
        2. Check for annihilation events (opposite-basin overlap)
        3. Update structure tracking
        """
        # Yoshida4 coefficients
        cbrt2 = 2.0 ** (1.0/3.0)
        w1 = 1.0 / (2.0 - cbrt2)
        w0 = -cbrt2 / (2.0 - cbrt2)
        
        d1 = w1 / 2.0
        d2 = (w0 + w1) / 2.0
        d3, d4 = d2, d1
        c1, c2, c3 = w1, w0, w1
        
        # Yoshida4 integration sequence
        self._update_momenta(d1 * dt)
        self._update_fields(c1 * dt)
        self._update_momenta(d2 * dt)
        self._update_fields(c2 * dt)
        self._update_momenta(d3 * dt)
        self._update_fields(c3 * dt)
        self._update_momenta(d4 * dt)
        
        # Wrap phase to (−π, +π)
        self.phi = self._wrap_phase(self.phi)
        
        # Enforce energy conservation
        if enforce_conservation:
            self._enforce_energy_conservation()
        
        self.time += dt
        
        # Track energy
        current_energy = self.compute_total_energy()
        self.energy_history.append(current_energy)
        
        # Check for annihilation events
        new_annihilations = self._check_annihilation_events()
        
        # Update structure tracking (combined centroid + topological)
        self._update_structure_tracking()
        
        # Compute basin statistics
        basin_stats = self._compute_basin_statistics()
        
        return {
            'time': float(self.time),
            'energy': float(current_energy),
            'energy_drift': float((current_energy - self.initial_energy) / abs(self.initial_energy)) if self.initial_energy else 0.0,
            'mean_rho': float(np.mean(self.rho)),
            'mean_phi': float(np.mean(self.phi)),
            **basin_stats,
            'active_structures': len(self.active_structures),
            'matter_structures': sum(1 for s in self.active_structures.values() if s.basin == AttractorBasin.MATTER),
            'antimatter_structures': sum(1 for s in self.active_structures.values() if s.basin == AttractorBasin.ANTIMATTER),
            'total_formed': self.structure_counter,
            'total_deceased': len(self.deceased_structures),
            'annihilation_events_this_step': len(new_annihilations),
            'total_annihilations': len(self.annihilation_events)
        }
    
    def _update_momenta(self, delta_t: float):
        """
        Update momenta using Hamilton's equations.
        
        Key: dU_φ/dφ = a_φ sin(φ) pushes phase toward basins.
        """
        p = self.params
        
        # Spectral Laplacians
        lap_rho = self._spectral_laplacian(self.rho)
        lap_sigma = self._spectral_laplacian(self.sigma)
        lap_tau = self._spectral_laplacian(self.tau)
        lap_phi = self._spectral_laplacian(self.phi)
        
        delta_rho = self.rho - p.rho_equilibrium
        
        # Density momentum
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
        
        # PHASE MOMENTUM - dual-basin attractor dynamics
        # dU_φ/dφ = a_φ sin(φ)
        # This creates restoring force toward φ=0 and φ=±π
        dpi_phi_dt = (
            p.K_phi * lap_phi
            - p.a_phi * np.sin(self.phi)  # Dual-basin attractor force
            + p.lambda_sigma_phi * self.sigma * np.sin(self.phi)
            + p.lambda_tau_phi * self.tau**2 * np.sin(self.phi)
            + p.lambda_rho_phi * delta_rho * np.sin(self.phi)
        )
        
        self.pi_rho += dpi_rho_dt * delta_t
        self.pi_sigma += dpi_sigma_dt * delta_t
        self.pi_tau += dpi_tau_dt * delta_t
        self.pi_phi += dpi_phi_dt * delta_t
    
    def _update_fields(self, delta_t: float):
        """Update field values: dq/dt = π/M"""
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
    
    def _compute_basin_statistics(self) -> Dict:
        """Compute basin occupation statistics"""
        p = self.params
        
        # Count cells in each basin
        matter_count = int(np.sum(np.abs(self.phi) < p.basin_boundary))
        antimatter_count = int(np.sum(np.abs(self.phi) >= p.basin_boundary))
        total = int(self.phi.size)
        
        # Transitional region (near boundary)
        boundary_width = np.pi / 8
        transitional = int(np.sum(np.abs(np.abs(self.phi) - p.basin_boundary) < boundary_width))
        
        return {
            'matter_fraction': float(matter_count / total),
            'antimatter_fraction': float(antimatter_count / total),
            'transitional_fraction': float(transitional / total),
            'phase_mean': float(np.mean(self.phi)),
            'phase_std': float(np.std(self.phi)),
            'phase_min': float(np.min(self.phi)),
            'phase_max': float(np.max(self.phi))
        }
    
    def _classify_basin(self, phi_value: float) -> AttractorBasin:
        """Classify which attractor basin a phase value belongs to"""
        p = self.params
        phi_wrapped = self._wrap_phase(np.array([phi_value]))[0]
        
        if np.abs(phi_wrapped) < p.basin_boundary:
            return AttractorBasin.MATTER
        else:
            return AttractorBasin.ANTIMATTER
    
    def compute_stabilization_functional(self) -> np.ndarray:
        """
        Compute S(x,t) for structure detection.
        
        High S indicates a stable, coherent configuration.
        """
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
        """Compute coherence length ξ(x,t)"""
        p = self.params
        grad_phi_sq = self._spectral_gradient_sq(self.phi)
        return p.xi0 * np.exp(-p.kappa * grad_phi_sq)
    
    def _compute_local_binding_energy(self, i: int, j: int, k: int) -> float:
        """Compute binding energy at a specific point"""
        p = self.params
        
        KE_local = 0.5 * (
            self.pi_rho[i,j,k]**2 / p.M_rho +
            self.pi_sigma[i,j,k]**2 / p.M_sigma +
            self.pi_tau[i,j,k]**2 / p.M_tau +
            self.pi_phi[i,j,k]**2 / p.M_phi
        )
        
        delta_rho = self.rho[i,j,k] - p.rho_equilibrium
        PE_local = (
            (p.a_rho / 2) * delta_rho**2 +
            (p.a_sigma / 2) * self.sigma[i,j,k]**2 +
            (p.a_tau / 2) * self.tau[i,j,k]**2 +
            (-p.a_phi * np.cos(self.phi[i,j,k]))
        )
        
        return float(KE_local + PE_local)
    
    def _compute_winding_number(self, i: int, j: int, k: int, radius: int = 2) -> int:
        """
        Compute topological winding number around a point.
        
        Winding = (1/2π) ∮ ∇φ · dl around the structure.
        """
        # Sample phase around a small loop
        phase_diff_total = 0.0
        
        # Sample 4 points in x-y plane
        offsets = [(radius, 0, 0), (0, radius, 0), (-radius, 0, 0), (0, -radius, 0)]
        
        for idx in range(len(offsets)):
            di1, dj1, dk1 = offsets[idx]
            di2, dj2, dk2 = offsets[(idx + 1) % len(offsets)]
            
            i1 = (i + di1) % self.grid_size
            j1 = (j + dj1) % self.grid_size
            k1 = (k + dk1) % self.grid_size
            
            i2 = (i + di2) % self.grid_size
            j2 = (j + dj2) % self.grid_size
            k2 = (k + dk2) % self.grid_size
            
            dphi = self.phi[i2, j2, k2] - self.phi[i1, j1, k1]
            # Unwrap phase difference
            dphi = np.mod(dphi + np.pi, 2*np.pi) - np.pi
            phase_diff_total += dphi
        
        # Winding number is total phase change / 2π
        winding = int(round(phase_diff_total / (2 * np.pi)))
        return winding
    
    def _compute_vorticity(self, i: int, j: int, k: int) -> float:
        """Compute local vorticity (curl of phase gradient)"""
        # Use central differences
        h = self.dx
        
        # ∂φ/∂y at (i+1,j,k) and (i-1,j,k)
        dphi_dy_plus = (self.phi[(i+1)%self.grid_size, (j+1)%self.grid_size, k] - 
                        self.phi[(i+1)%self.grid_size, (j-1)%self.grid_size, k]) / (2*h)
        dphi_dy_minus = (self.phi[(i-1)%self.grid_size, (j+1)%self.grid_size, k] - 
                         self.phi[(i-1)%self.grid_size, (j-1)%self.grid_size, k]) / (2*h)
        
        # ∂φ/∂x at (i,j+1,k) and (i,j-1,k)
        dphi_dx_plus = (self.phi[(i+1)%self.grid_size, (j+1)%self.grid_size, k] - 
                        self.phi[(i-1)%self.grid_size, (j+1)%self.grid_size, k]) / (2*h)
        dphi_dx_minus = (self.phi[(i+1)%self.grid_size, (j-1)%self.grid_size, k] - 
                         self.phi[(i-1)%self.grid_size, (j-1)%self.grid_size, k]) / (2*h)
        
        # Curl_z = ∂(∂φ/∂y)/∂x - ∂(∂φ/∂x)/∂y
        curl_z = (dphi_dy_plus - dphi_dy_minus) / (2*h) - (dphi_dx_plus - dphi_dx_minus) / (2*h)
        
        return float(curl_z)
    
    def _compute_mode_properties(self, i: int, j: int, k: int, S_val: float) -> FieldModeProperties:
        """
        Extract emergent field mode properties at a structure location.
        
        These properties form the basis for structure classification -
        NOT hardcoded quark types.
        """
        p = self.params
        
        binding_energy = self._compute_local_binding_energy(i, j, k)
        KE_local = 0.5 * (
            self.pi_rho[i,j,k]**2 / p.M_rho +
            self.pi_sigma[i,j,k]**2 / p.M_sigma +
            self.pi_tau[i,j,k]**2 / p.M_tau +
            self.pi_phi[i,j,k]**2 / p.M_phi
        )
        kinetic_fraction = KE_local / max(abs(binding_energy), 1e-10)
        
        # Coherence length
        grad_phi_sq = self._spectral_gradient_sq(self.phi)[i, j, k]
        xi = p.xi0 * np.exp(-p.kappa * grad_phi_sq)
        
        # Dominant mode number (from local FFT - simplified)
        # For now, estimate based on structure extent
        mode_number = max(1, int(self.grid_size / (2 * max(xi, 1))))
        
        # Radial profile classification (simplified)
        if self.tau[i,j,k]**2 > np.mean(self.tau**2):
            radial_profile = 'vortex'
        elif abs(self.rho[i,j,k] - p.rho_equilibrium) > np.std(self.rho):
            radial_profile = 'gaussian'
        else:
            radial_profile = 'shell'
        
        # Topological properties
        winding = self._compute_winding_number(i, j, k)
        vorticity = self._compute_vorticity(i, j, k)
        
        return FieldModeProperties(
            binding_energy=binding_energy,
            kinetic_fraction=kinetic_fraction,
            coherence_length=xi,
            mode_number=mode_number,
            radial_profile=radial_profile,
            winding_number=winding,
            vorticity=vorticity,
            rho_deviation=float(self.rho[i,j,k] - p.rho_equilibrium),
            sigma_amplitude=float(self.sigma[i,j,k]),
            tau_magnitude=float(self.tau[i,j,k]),
            S_value=S_val
        )
    
    def detect_structures(self) -> List[CoherentStructure]:
        """
        Detect coherent structures in both attractor basins.
        
        Returns newly detected structures (not yet in active tracking).
        """
        p = self.params
        
        S = self.compute_stabilization_functional()
        xi = self.compute_coherence_length()
        
        new_structures = []
        
        # Find local maxima of S above threshold
        margin = 2
        for i in range(margin, self.grid_size - margin):
            for j in range(margin, self.grid_size - margin):
                for k in range(margin, self.grid_size - margin):
                    S_val = S[i, j, k]
                    
                    if S_val >= p.S_threshold:
                        # Check if local maximum
                        local_region = S[i-1:i+2, j-1:j+2, k-1:k+2]
                        if S_val >= np.max(local_region) - 1e-10:
                            self.structure_counter += 1
                            
                            phi_val = self.phi[i, j, k]
                            basin = self._classify_basin(phi_val)
                            
                            # Compute emergent mode properties
                            mode_props = self._compute_mode_properties(i, j, k, S_val)
                            
                            # Topological signature for tracking
                            topo_sig = (
                                mode_props.winding_number,
                                mode_props.mode_number,
                                np.sign(self.tau[i, j, k])
                            )
                            
                            structure = CoherentStructure(
                                id=f"struct_{self.structure_counter}",
                                centroid=(float(i), float(j), float(k)),
                                extent=float(xi[i, j, k]),
                                basin=basin,
                                phase_value=float(phi_val),
                                rho=float(self.rho[i, j, k]),
                                sigma=float(self.sigma[i, j, k]),
                                tau=float(self.tau[i, j, k]),
                                phi=float(phi_val),
                                mode_properties=mode_props,
                                topological_signature=topo_sig,
                                formation_time=self.time,
                                last_seen_time=self.time
                            )
                            
                            new_structures.append(structure)
        
        return new_structures
    
    def _update_structure_tracking(self):
        """
        Update structure tracking using BOTH centroid and topological methods.
        
        Combined matching score = (1 - topology_weight) * centroid_match + topology_weight * topo_match
        """
        p = self.params
        
        current_structures = self.detect_structures()
        
        # Build matching matrix
        matched_current = set()
        
        for struct_id, old_struct in list(self.active_structures.items()):
            old_pos = np.array(old_struct.centroid)
            old_topo = old_struct.topological_signature
            old_basin = old_struct.basin
            
            best_match = None
            best_score = -np.inf
            
            for curr in current_structures:
                if curr.id in matched_current:
                    continue
                
                # Must be same basin (matter stays matter, antimatter stays antimatter)
                if curr.basin != old_basin:
                    continue
                
                curr_pos = np.array(curr.centroid)
                curr_topo = curr.topological_signature
                
                # Centroid distance score (0 to 1, higher is better)
                dist = np.linalg.norm(curr_pos - old_pos)
                if dist > p.tracking_radius:
                    continue
                centroid_score = 1.0 - dist / p.tracking_radius
                
                # Topological similarity score (0 to 1)
                topo_match = sum(1 for a, b in zip(old_topo, curr_topo) if a == b) / len(old_topo)
                
                # Combined score
                combined_score = (1 - p.topology_weight) * centroid_score + p.topology_weight * topo_match
                
                if combined_score > best_score:
                    best_match = curr
                    best_score = combined_score
            
            if best_match is not None:
                # Match found - update existing structure
                matched_current.add(best_match.id)
                
                old_struct.centroid = best_match.centroid
                old_struct.extent = best_match.extent
                old_struct.last_seen_time = self.time
                old_struct.lifetime = self.time - old_struct.formation_time
                old_struct.phase_value = best_match.phase_value
                old_struct.rho = best_match.rho
                old_struct.sigma = best_match.sigma
                old_struct.tau = best_match.tau
                old_struct.phi = best_match.phi
                old_struct.mode_properties = best_match.mode_properties
                old_struct.topological_signature = best_match.topological_signature
                
                # Track history
                old_struct.centroid_history.append(best_match.centroid)
                old_struct.S_history.append(best_match.mode_properties.S_value)
                old_struct.phase_history.append(best_match.phase_value)
                
                # Keep recent history only
                max_history = 100
                if len(old_struct.centroid_history) > max_history:
                    old_struct.centroid_history = old_struct.centroid_history[-max_history:]
                    old_struct.S_history = old_struct.S_history[-max_history:]
                    old_struct.phase_history = old_struct.phase_history[-max_history:]
            else:
                # No match - structure has died
                old_struct.is_alive = False
                old_struct.lifetime = self.time - old_struct.formation_time
                self.deceased_structures.append(old_struct)
                del self.active_structures[struct_id]
        
        # Add new structures
        for curr in current_structures:
            if curr.id not in matched_current:
                self.active_structures[curr.id] = curr
    
    def _check_annihilation_events(self) -> List[AnnihilationEvent]:
        """
        Check for annihilation when opposite-basin structures overlap.
        
        Annihilation triggers:
        - Coherence collapse (destroy both structures)
        - Rapid phase decoherence cascade (spread instability)
        - Energy redistribution into substrate wave spectrum
        """
        p = self.params
        
        new_events = []
        
        # Get matter and antimatter structures
        matter_structs = [s for s in self.active_structures.values() if s.basin == AttractorBasin.MATTER]
        antimatter_structs = [s for s in self.active_structures.values() if s.basin == AttractorBasin.ANTIMATTER]
        
        # Check all matter-antimatter pairs for overlap
        annihilated_ids = set()
        
        for m_struct in matter_structs:
            if m_struct.id in annihilated_ids:
                continue
                
            m_pos = np.array(m_struct.centroid)
            
            for a_struct in antimatter_structs:
                if a_struct.id in annihilated_ids:
                    continue
                    
                a_pos = np.array(a_struct.centroid)
                dist = np.linalg.norm(m_pos - a_pos)
                
                # Check if overlap
                overlap_threshold = p.annihilation_overlap_radius
                if dist < overlap_threshold:
                    # ANNIHILATION EVENT
                    event = self._perform_annihilation(m_struct, a_struct)
                    new_events.append(event)
                    self.annihilation_events.append(event)
                    
                    annihilated_ids.add(m_struct.id)
                    annihilated_ids.add(a_struct.id)
                    break
        
        # Remove annihilated structures
        for struct_id in annihilated_ids:
            if struct_id in self.active_structures:
                s = self.active_structures[struct_id]
                s.is_alive = False
                s.lifetime = self.time - s.formation_time
                self.deceased_structures.append(s)
                del self.active_structures[struct_id]
        
        return new_events
    
    def _perform_annihilation(self, matter: CoherentStructure, antimatter: CoherentStructure) -> AnnihilationEvent:
        """
        Perform annihilation between opposite-basin structures.
        
        Effects:
        1. Coherence collapse - set S to near zero at both locations
        2. Phase decoherence cascade - add noise to phase field
        3. Energy redistribution - add kinetic energy to wave spectrum
        4. Possible neutral transitional - leave φ ≈ ±π/2 region
        """
        p = self.params
        
        # Midpoint of annihilation
        mid_pos = tuple(
            (matter.centroid[i] + antimatter.centroid[i]) / 2 
            for i in range(3)
        )
        mi, mj, mk = int(mid_pos[0]), int(mid_pos[1]), int(mid_pos[2])
        
        # Energy being released
        matter_energy = matter.mode_properties.binding_energy
        antimatter_energy = antimatter.mode_properties.binding_energy
        released_energy = abs(matter_energy) + abs(antimatter_energy)
        
        # 1. Coherence collapse - flatten fields toward equilibrium near annihilation
        radius = int(p.annihilation_overlap_radius) + 1
        for di in range(-radius, radius+1):
            for dj in range(-radius, radius+1):
                for dk in range(-radius, radius+1):
                    ni = (mi + di) % self.grid_size
                    nj = (mj + dj) % self.grid_size
                    nk = (mk + dk) % self.grid_size
                    
                    dist = np.sqrt(di**2 + dj**2 + dk**2)
                    if dist <= radius:
                        decay = np.exp(-dist / radius)
                        
                        # Push fields toward equilibrium
                        self.rho[ni, nj, nk] = (1-decay) * self.rho[ni,nj,nk] + decay * p.rho_equilibrium
                        self.sigma[ni, nj, nk] *= (1 - decay)
                        self.tau[ni, nj, nk] *= (1 - decay)
        
        # 2. Phase decoherence cascade - randomize phase in affected region
        for di in range(-radius, radius+1):
            for dj in range(-radius, radius+1):
                for dk in range(-radius, radius+1):
                    ni = (mi + di) % self.grid_size
                    nj = (mj + dj) % self.grid_size
                    nk = (mk + dk) % self.grid_size
                    
                    dist = np.sqrt(di**2 + dj**2 + dk**2)
                    if dist <= radius:
                        # Add random phase noise (decoherence)
                        noise_strength = p.decoherence_rate * np.exp(-dist / radius)
                        self.phi[ni, nj, nk] += noise_strength * np.random.randn()
        
        # Wrap phase after modification
        self.phi = self._wrap_phase(self.phi)
        
        # 3. Energy redistribution - add kinetic energy (wave spectrum)
        # Distribute released energy as random momenta
        energy_per_cell = released_energy / (8 * radius**3)
        for di in range(-radius, radius+1):
            for dj in range(-radius, radius+1):
                for dk in range(-radius, radius+1):
                    ni = (mi + di) % self.grid_size
                    nj = (mj + dj) % self.grid_size
                    nk = (mk + dk) % self.grid_size
                    
                    dist = np.sqrt(di**2 + dj**2 + dk**2)
                    if dist <= radius:
                        # Add random momentum (energy goes into waves)
                        sign = 2 * np.random.randint(0, 2) - 1
                        self.pi_phi[ni, nj, nk] += sign * np.sqrt(2 * energy_per_cell * p.M_phi)
        
        # 4. Check for neutral transitional (phase near ±π/2)
        formed_neutral = np.abs(np.abs(self.phi[mi, mj, mk]) - np.pi/2) < np.pi/8
        
        return AnnihilationEvent(
            time=self.time,
            position=mid_pos,
            matter_structure_id=matter.id,
            antimatter_structure_id=antimatter.id,
            matter_energy=matter_energy,
            antimatter_energy=antimatter_energy,
            released_energy=released_energy,
            formed_neutral=formed_neutral
        )
    
    def get_basin_resolved_statistics(self) -> Dict:
        """Get statistics broken down by attractor basin"""
        matter_structs = [s for s in self.active_structures.values() if s.basin == AttractorBasin.MATTER]
        antimatter_structs = [s for s in self.active_structures.values() if s.basin == AttractorBasin.ANTIMATTER]
        
        def compute_stats(structs: List[CoherentStructure]) -> Dict:
            if not structs:
                return {'count': 0, 'avg_lifetime': 0.0, 'avg_S': 0.0, 'avg_binding_energy': 0.0}
            return {
                'count': len(structs),
                'avg_lifetime': float(np.mean([s.lifetime for s in structs])),
                'avg_S': float(np.mean([s.mode_properties.S_value for s in structs])),
                'avg_binding_energy': float(np.mean([s.mode_properties.binding_energy for s in structs]))
            }
        
        return {
            'matter': compute_stats(matter_structs),
            'antimatter': compute_stats(antimatter_structs),
            'total_active': len(self.active_structures),
            'total_deceased': len(self.deceased_structures),
            'total_annihilations': len(self.annihilation_events)
        }
    
    def get_mode_property_census(self) -> Dict:
        """
        Get census of emergent mode properties across structures.
        
        This is the basis for emergent classification - NOT hardcoded quark types.
        """
        all_structs = list(self.active_structures.values())
        
        if not all_structs:
            return {
                'count': 0,
                'winding_numbers': {},
                'radial_profiles': {},
                'avg_binding_energy': 0.0,
                'avg_coherence_length': 0.0,
                'avg_vorticity': 0.0
            }
        
        # Winding number distribution
        winding_counts = {}
        for s in all_structs:
            w = int(s.mode_properties.winding_number)
            winding_counts[w] = winding_counts.get(w, 0) + 1
        
        # Radial profile distribution
        profile_counts = {}
        for s in all_structs:
            p = s.mode_properties.radial_profile
            profile_counts[p] = profile_counts.get(p, 0) + 1
        
        return {
            'count': len(all_structs),
            'winding_numbers': winding_counts,
            'radial_profiles': profile_counts,
            'avg_binding_energy': float(np.mean([s.mode_properties.binding_energy for s in all_structs])),
            'avg_coherence_length': float(np.mean([s.mode_properties.coherence_length for s in all_structs])),
            'avg_vorticity': float(np.mean([s.mode_properties.vorticity for s in all_structs]))
        }
    
    def get_lifetime_distribution(self) -> Dict:
        """Get lifetime distribution for matter vs antimatter structures"""
        matter_lifetimes = [s.lifetime for s in self.deceased_structures if s.basin == AttractorBasin.MATTER]
        antimatter_lifetimes = [s.lifetime for s in self.deceased_structures if s.basin == AttractorBasin.ANTIMATTER]
        
        def compute_dist(lifetimes: List[float]) -> Dict:
            if not lifetimes:
                return {'count': 0, 'mean': 0.0, 'std': 0.0, 'max': 0.0}
            return {
                'count': len(lifetimes),
                'mean': float(np.mean(lifetimes)),
                'std': float(np.std(lifetimes)),
                'max': float(np.max(lifetimes))
            }
        
        return {
            'matter': compute_dist(matter_lifetimes),
            'antimatter': compute_dist(antimatter_lifetimes)
        }
    
    def get_state_summary(self) -> Dict:
        """Get comprehensive state summary"""
        current_energy = self.compute_total_energy()
        basin_stats = self._compute_basin_statistics()
        
        return {
            'time': self.time,
            'grid_size': self.grid_size,
            'phase_range': '(-pi, +pi)',
            'total_energy': current_energy,
            'initial_energy': self.initial_energy,
            'energy_drift_pct': (current_energy - self.initial_energy) / abs(self.initial_energy) * 100 if self.initial_energy else 0,
            'basin_statistics': basin_stats,
            'structure_statistics': self.get_basin_resolved_statistics(),
            'mode_property_census': self.get_mode_property_census(),
            'lifetime_distribution': self.get_lifetime_distribution(),
            'annihilation_events': len(self.annihilation_events),
            'mean_rho': float(np.mean(self.rho)),
            'mean_phi': float(np.mean(self.phi))
        }


# =============================================================================
# Simulation Functions
# =============================================================================

def run_dual_basin_validation(
    grid_size: int = 24,
    amplitude: float = 0.05,
    total_time: float = 30.0,
    dt: float = 0.01,
    matter_fraction: float = 0.5,
    seed: int = 42
) -> Dict:
    """
    Run validation test for dual-basin attractor ontology.
    
    Tests:
    1. Symmetric basin stability (both matter and antimatter basins persist)
    2. Structure formation in both basins
    3. Annihilation when opposite basins overlap
    4. Energy conservation throughout
    """
    engine = QMRTQuarkEngine(grid_size=grid_size)
    engine.initialize_dual_basin(amplitude=amplitude, matter_fraction=matter_fraction, seed=seed)
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 30)
    
    evolution_samples = []
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            sample = {
                **metrics,
                'step': step
            }
            evolution_samples.append(sample)
    
    final_state = engine.get_state_summary()
    
    # Validate dual-basin symmetry
    final_matter = final_state['basin_statistics']['matter_fraction']
    final_antimatter = final_state['basin_statistics']['antimatter_fraction']
    basin_symmetry = abs(final_matter - final_antimatter) < 0.15  # Within 15%
    
    return {
        'test_name': 'dual_basin_validation',
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'dt': dt,
            'matter_fraction': matter_fraction
        },
        'final_state': final_state,
        'evolution_samples': evolution_samples,
        'validation_results': {
            'basin_symmetry_preserved': bool(basin_symmetry),
            'initial_matter_fraction': float(matter_fraction),
            'final_matter_fraction': float(final_matter),
            'final_antimatter_fraction': float(final_antimatter),
            'structures_formed': int(final_state['structure_statistics']['total_active'] + final_state['structure_statistics']['total_deceased']),
            'annihilations_occurred': int(final_state['annihilation_events']),
            'energy_conserved': bool(abs(final_state['energy_drift_pct']) < 1.0)
        },
        'annihilation_events': [e.to_dict() for e in engine.annihilation_events[:20]]
    }


def run_annihilation_test(
    grid_size: int = 24,
    amplitude: float = 0.1,
    total_time: float = 20.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Test annihilation dynamics by initializing matter and antimatter regions
    in close proximity.
    """
    engine = QMRTQuarkEngine(grid_size=grid_size)
    
    # Initialize with explicit matter/antimatter blobs
    if seed is not None:
        np.random.seed(seed)
    
    shape = (grid_size, grid_size, grid_size)
    p = engine.params
    
    engine.rho = p.rho_equilibrium + amplitude * engine._balanced_noise(shape)
    engine.sigma = amplitude * engine._balanced_noise(shape)
    engine.tau = amplitude * engine._balanced_noise(shape)
    
    # Create explicit matter blob at (grid/4, grid/2, grid/2)
    # and antimatter blob at (3*grid/4, grid/2, grid/2)
    engine.phi = np.zeros(shape)
    
    center = grid_size // 2
    quarter = grid_size // 4
    blob_radius = grid_size // 6
    
    for i in range(grid_size):
        for j in range(grid_size):
            for k in range(grid_size):
                # Distance to matter center
                dm = np.sqrt((i-quarter)**2 + (j-center)**2 + (k-center)**2)
                # Distance to antimatter center
                da = np.sqrt((i-(grid_size-quarter))**2 + (j-center)**2 + (k-center)**2)
                
                if dm < blob_radius:
                    # Matter region: φ ≈ 0
                    engine.phi[i,j,k] = amplitude * np.random.randn()
                elif da < blob_radius:
                    # Antimatter region: φ ≈ ±π
                    sign = 2 * (np.random.random() > 0.5) - 1
                    engine.phi[i,j,k] = sign * (np.pi - amplitude * abs(np.random.randn()))
                else:
                    # Background: random basin
                    if np.random.random() < 0.5:
                        engine.phi[i,j,k] = amplitude * np.random.randn()
                    else:
                        engine.phi[i,j,k] = np.pi + amplitude * np.random.randn()
    
    engine.phi = engine._wrap_phase(engine.phi)
    
    engine.pi_rho = np.zeros(shape)
    engine.pi_sigma = np.zeros(shape)
    engine.pi_tau = np.zeros(shape)
    engine.pi_phi = np.zeros(shape)
    
    engine._precompute_spectral()
    engine.initial_energy = engine.compute_total_energy()
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 30)
    
    evolution_samples = []
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            evolution_samples.append({**metrics, 'step': step})
    
    return {
        'test_name': 'annihilation_test',
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'blob_separation': grid_size // 2,
            'blob_radius': blob_radius
        },
        'final_state': engine.get_state_summary(),
        'evolution_samples': evolution_samples,
        'annihilation_events': [e.to_dict() for e in engine.annihilation_events],
        'annihilation_count': len(engine.annihilation_events)
    }


def run_structure_persistence_test(
    grid_size: int = 24,
    amplitude: float = 0.08,
    total_time: float = 50.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Test long-term persistence of structures in both basins.
    
    Validates that coherent structures can survive for extended periods
    in both the matter and antimatter attractor basins.
    """
    engine = QMRTQuarkEngine(grid_size=grid_size)
    engine.initialize_dual_basin(amplitude=amplitude, seed=seed)
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    persistence_data = []
    
    for step in range(steps):
        metrics = engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            stats = engine.get_basin_resolved_statistics()
            persistence_data.append({
                'time': engine.time,
                'step': step,
                'matter_count': stats['matter']['count'],
                'antimatter_count': stats['antimatter']['count'],
                'matter_avg_lifetime': stats['matter']['avg_lifetime'],
                'antimatter_avg_lifetime': stats['antimatter']['avg_lifetime'],
                'total_active': stats['total_active'],
                'annihilations': stats['total_annihilations'],
                'energy_drift': metrics['energy_drift']
            })
    
    return {
        'test_name': 'structure_persistence',
        'test_params': {
            'grid_size': grid_size,
            'amplitude': amplitude,
            'total_time': total_time,
            'dt': dt
        },
        'final_state': engine.get_state_summary(),
        'persistence_data': persistence_data,
        'lifetime_distribution': engine.get_lifetime_distribution(),
        'mode_census': engine.get_mode_property_census()
    }
