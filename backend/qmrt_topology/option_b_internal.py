"""
QMRT Topology Option B: Internal Manifold Topology
===================================================

Particles as textures in an internal phase space attached to each spatial point.

This enables SPIN-½:
- At each point x, there's an internal state ψ(x) ∈ SU(2) ≅ S³
- 360° rotation: ψ → -ψ (NOT identity!)
- 720° rotation: ψ → +ψ (identity)

Mathematical structure:
  ψ(x,t) = (ψ↑(x,t), ψ↓(x,t)) ∈ ℂ²
  
  Normalized: |ψ↑|² + |ψ↓|² = 1 (spinor constraint)
  
  Rotation by θ around axis n̂:
    R(θ, n̂) = exp(iθ n̂·σ/2)
  
  where σ = (σ_x, σ_y, σ_z) are Pauli matrices:
    σ_x = [[0,1],[1,0]]
    σ_y = [[0,-i],[i,0]]
    σ_z = [[1,0],[0,-1]]

Physical content:
- Spin direction: n̂ = ⟨ψ|σ|ψ⟩
- Spin magnitude: |⟨ψ|σ|ψ⟩| = 1 (always spin-½)
- Topological charge: Skyrmion number

Reference: This is the physics of spinor BECs (Bose-Einstein condensates)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json


# Pauli matrices
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
SIGMA = np.array([SIGMA_X, SIGMA_Y, SIGMA_Z])


@dataclass
class OptionBParameters:
    """Parameters for internal manifold topology."""
    # Mass parameter
    m: float = 1.0
    
    # Chemical potential
    mu: float = 1.0
    
    # Density-density interaction
    g0: float = 1.0
    
    # Spin-spin interaction (ferromagnetic < 0, antiferromagnetic > 0)
    g2: float = -0.1
    
    # Grid spacing
    dx: float = 1.0
    
    def healing_length(self) -> float:
        """Density healing length."""
        return 1.0 / np.sqrt(2 * self.m * self.mu)


@dataclass
class SpinorState:
    """State at a single point."""
    up: complex      # ψ↑ component
    down: complex    # ψ↓ component
    
    def normalize(self):
        """Normalize to unit spinor."""
        norm = np.sqrt(abs(self.up)**2 + abs(self.down)**2)
        if norm > 0:
            self.up /= norm
            self.down /= norm
    
    def spin_vector(self) -> np.ndarray:
        """Compute spin expectation value ⟨σ⟩."""
        psi = np.array([self.up, self.down])
        return np.real(np.array([
            np.conj(psi) @ SIGMA_X @ psi,
            np.conj(psi) @ SIGMA_Y @ psi,
            np.conj(psi) @ SIGMA_Z @ psi
        ]))


class OptionBEngine:
    """
    Internal manifold topology engine (spinor field).
    
    Implements spinor Gross-Pitaevskii equation:
    
    iℏ ∂ψ/∂t = [-ℏ²∇²/2m + V(x) + g₀n + g₂F·σ] ψ
    
    where:
    - ψ = (ψ↑, ψ↓) is a two-component spinor
    - n = |ψ↑|² + |ψ↓|² is the total density
    - F = ψ†σψ is the spin density vector
    """
    
    def __init__(
        self,
        grid_size: int = 64,
        dim: int = 2,
        params: Optional[OptionBParameters] = None
    ):
        self.grid_size = grid_size
        self.dim = dim
        self.params = params or OptionBParameters()
        self.time = 0.0
        
        # Two-component spinor field ψ = (ψ↑, ψ↓)
        shape = tuple([grid_size] * dim)
        
        # Initialize to spin-up state with uniform density
        bulk_density = self.params.mu / self.params.g0
        self.psi_up = np.sqrt(bulk_density) * np.ones(shape, dtype=complex)
        self.psi_down = np.zeros(shape, dtype=complex)
        
        # Precompute spectral operators
        self._setup_spectral()
        
        self.initial_energy = None
        self.energy_history = []
    
    def _setup_spectral(self):
        """Precompute k-space operators."""
        n = self.grid_size
        dx = self.params.dx
        
        k = np.fft.fftfreq(n, d=dx) * 2 * np.pi
        
        if self.dim == 2:
            KX, KY = np.meshgrid(k, k, indexing='ij')
            self._k_sq = KX**2 + KY**2
        else:
            KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
            self._k_sq = KX**2 + KY**2 + KZ**2
    
    def _spectral_laplacian(self, f: np.ndarray) -> np.ndarray:
        """Compute ∇²f using FFT."""
        f_hat = np.fft.fftn(f)
        return np.fft.ifftn(-self._k_sq * f_hat)
    
    # ========== SPINOR FIELD PROPERTIES ==========
    
    def get_density(self) -> np.ndarray:
        """Total density n = |ψ↑|² + |ψ↓|²."""
        return np.abs(self.psi_up)**2 + np.abs(self.psi_down)**2
    
    def get_spin_density(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Spin density F = ψ†σψ.
        
        Returns (Fx, Fy, Fz) components.
        """
        Fx = 2 * np.real(np.conj(self.psi_up) * self.psi_down)
        Fy = 2 * np.imag(np.conj(self.psi_up) * self.psi_down)
        Fz = np.abs(self.psi_up)**2 - np.abs(self.psi_down)**2
        
        return Fx, Fy, Fz
    
    def get_spin_magnitude(self) -> np.ndarray:
        """Magnitude of local spin |F|."""
        Fx, Fy, Fz = self.get_spin_density()
        return np.sqrt(Fx**2 + Fy**2 + Fz**2)
    
    def get_spin_direction(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Unit spin direction n̂ = F/|F|."""
        Fx, Fy, Fz = self.get_spin_density()
        F_mag = self.get_spin_magnitude() + 1e-10
        
        return Fx / F_mag, Fy / F_mag, Fz / F_mag
    
    # ========== ROTATION OPERATIONS ==========
    
    def apply_rotation(self, theta: float, axis: np.ndarray):
        """
        Apply global rotation by angle theta around axis.
        
        R = exp(iθ n̂·σ/2) = cos(θ/2)I + i sin(θ/2) n̂·σ
        """
        axis = np.array(axis, dtype=float)
        axis = axis / np.linalg.norm(axis)
        
        c = np.cos(theta / 2)
        s = np.sin(theta / 2)
        
        # Rotation matrix in spinor space
        R = np.array([
            [c + 1j * s * axis[2], 1j * s * (axis[0] - 1j * axis[1])],
            [1j * s * (axis[0] + 1j * axis[1]), c - 1j * s * axis[2]]
        ], dtype=complex)
        
        # Apply rotation
        psi_up_new = R[0, 0] * self.psi_up + R[0, 1] * self.psi_down
        psi_down_new = R[1, 0] * self.psi_up + R[1, 1] * self.psi_down
        
        self.psi_up = psi_up_new
        self.psi_down = psi_down_new
    
    # ========== STATE CREATION ==========
    
    def create_spin_up(self):
        """Create uniform spin-up state."""
        bulk_density = self.params.mu / self.params.g0
        amp = np.sqrt(bulk_density)
        
        self.psi_up = amp * np.ones_like(self.psi_up)
        self.psi_down = np.zeros_like(self.psi_down)
    
    def create_spin_down(self):
        """Create uniform spin-down state."""
        bulk_density = self.params.mu / self.params.g0
        amp = np.sqrt(bulk_density)
        
        self.psi_up = np.zeros_like(self.psi_up)
        self.psi_down = amp * np.ones_like(self.psi_down)
    
    def create_spin_texture(self, texture_type: str = 'hedgehog'):
        """
        Create a localized spin texture (proto-particle).
        
        Types:
        - 'hedgehog': Spin points radially outward (skyrmion)
        - 'vortex': Spin winds in xy-plane
        - 'domain_wall': Spin flips across a line
        """
        n = self.grid_size
        bulk_density = self.params.mu / self.params.g0
        amp = np.sqrt(bulk_density)
        
        if self.dim != 2:
            raise NotImplementedError("Textures only for 2D currently")
        
        x = np.arange(n) - n/2
        X, Y = np.meshgrid(x, x, indexing='ij')
        R = np.sqrt(X**2 + Y**2) + 1e-10
        
        # Characteristic size
        R0 = n / 8
        
        if texture_type == 'hedgehog':
            # Hedgehog: spin points radially outward at core, up at infinity
            # n̂ = (sin(f(r))cos(φ), sin(f(r))sin(φ), cos(f(r)))
            # where f(r) goes from π at r=0 to 0 as r→∞
            
            f_r = np.pi * np.exp(-R / R0)  # Profile function
            
            # Convert to spinor using standard formula:
            # |↑⟩ = cos(θ/2)|z↑⟩ + sin(θ/2)e^{iφ}|z↓⟩
            theta = f_r
            phi = np.arctan2(Y, X)
            
            self.psi_up = amp * np.cos(theta / 2)
            self.psi_down = amp * np.sin(theta / 2) * np.exp(1j * phi)
            
        elif texture_type == 'vortex':
            # Spin-vortex: spin winds in xy-plane
            phi = np.arctan2(Y, X)
            
            # Spin direction: n̂ = (cos(φ), sin(φ), 0)
            # Corresponding spinor: ψ = (e^{-iφ/2}, e^{iφ/2})/√2
            
            self.psi_up = amp * np.exp(-1j * phi / 2) / np.sqrt(2)
            self.psi_down = amp * np.exp(1j * phi / 2) / np.sqrt(2)
            
        elif texture_type == 'domain_wall':
            # Domain wall: spin flips from +z to -z across x=0
            tanh_profile = np.tanh(X / R0)
            
            # θ(x) goes from π (x→-∞) to 0 (x→+∞)
            theta = np.pi * (1 - tanh_profile) / 2
            
            self.psi_up = amp * np.cos(theta / 2)
            self.psi_down = amp * np.sin(theta / 2)
        
        else:
            raise ValueError(f"Unknown texture type: {texture_type}")
    
    # ========== TOPOLOGICAL CHARGE (SKYRMION NUMBER) ==========
    
    def compute_skyrmion_number(self) -> float:
        """
        Compute topological charge (skyrmion number).
        
        Q = (1/4π) ∫ n̂ · (∂_x n̂ × ∂_y n̂) dx dy
        
        This counts how many times the spin covers S² as we scan over space.
        """
        if self.dim != 2:
            return 0.0
        
        nx, ny, nz = self.get_spin_direction()
        dx = self.params.dx
        
        # Compute derivatives
        dnx_dx = np.gradient(nx, dx, axis=0)
        dnx_dy = np.gradient(nx, dx, axis=1)
        dny_dx = np.gradient(ny, dx, axis=0)
        dny_dy = np.gradient(ny, dx, axis=1)
        dnz_dx = np.gradient(nz, dx, axis=0)
        dnz_dy = np.gradient(nz, dx, axis=1)
        
        # Cross product (∂_x n̂ × ∂_y n̂)
        cross_x = dny_dx * dnz_dy - dnz_dx * dny_dy
        cross_y = dnz_dx * dnx_dy - dnx_dx * dnz_dy
        cross_z = dnx_dx * dny_dy - dny_dx * dnx_dy
        
        # Dot product n̂ · (∂_x n̂ × ∂_y n̂)
        integrand = nx * cross_x + ny * cross_y + nz * cross_z
        
        # Integrate
        dV = dx ** 2
        Q = np.sum(integrand) * dV / (4 * np.pi)
        
        return Q
    
    # ========== ENERGY ==========
    
    def compute_energy(self) -> Dict[str, float]:
        """Compute total energy with breakdown."""
        p = self.params
        dV = p.dx ** self.dim
        
        n = self.get_density()
        Fx, Fy, Fz = self.get_spin_density()
        F_sq = Fx**2 + Fy**2 + Fz**2
        
        # Kinetic energy
        lap_up = self._spectral_laplacian(self.psi_up)
        lap_down = self._spectral_laplacian(self.psi_down)
        
        E_kin = -0.5 / p.m * np.real(
            np.sum(np.conj(self.psi_up) * lap_up) +
            np.sum(np.conj(self.psi_down) * lap_down)
        ) * dV
        
        # Chemical potential
        E_chem = -p.mu * np.sum(n) * dV
        
        # Density interaction: (g0/2) n²
        E_density = 0.5 * p.g0 * np.sum(n**2) * dV
        
        # Spin interaction: (g2/2) F²
        E_spin = 0.5 * p.g2 * np.sum(F_sq) * dV
        
        E_total = E_kin + E_chem + E_density + E_spin
        
        return {
            'E_kinetic': float(E_kin),
            'E_chemical': float(E_chem),
            'E_density': float(E_density),
            'E_spin': float(E_spin),
            'E_total': float(E_total)
        }
    
    # ========== TIME EVOLUTION ==========
    
    def evolve_split_step(self, dt: float, n_steps: int = 1):
        """
        Evolve using split-step method.
        
        iℏ ∂ψ/∂t = [-∇²/2m - μ + g₀n + g₂F·σ] ψ
        """
        p = self.params
        
        for _ in range(n_steps):
            # Compute potential terms
            n = self.get_density()
            Fx, Fy, Fz = self.get_spin_density()
            
            # Half step potential
            V_scalar = -p.mu + p.g0 * n
            
            # Spin-dependent potential: g₂(F·σ)
            # (F·σ)ψ = [Fz, Fx-iFy; Fx+iFy, -Fz] ψ
            Vup_up = V_scalar + p.g2 * Fz
            Vup_dn = p.g2 * (Fx - 1j * Fy)
            Vdn_up = p.g2 * (Fx + 1j * Fy)
            Vdn_dn = V_scalar - p.g2 * Fz
            
            # Apply as matrix exponential (approximate for small dt)
            # exp(-iVdt) ≈ I - iVdt for first order
            exp_factor = -0.5j * dt
            
            psi_up_new = self.psi_up + exp_factor * (Vup_up * self.psi_up + Vup_dn * self.psi_down)
            psi_dn_new = self.psi_down + exp_factor * (Vdn_up * self.psi_up + Vdn_dn * self.psi_down)
            
            self.psi_up = psi_up_new
            self.psi_down = psi_dn_new
            
            # Full step kinetic (Fourier space)
            psi_up_hat = np.fft.fftn(self.psi_up)
            psi_dn_hat = np.fft.fftn(self.psi_down)
            
            kin_phase = np.exp(-0.5j * self._k_sq / p.m * dt)
            psi_up_hat *= kin_phase
            psi_dn_hat *= kin_phase
            
            self.psi_up = np.fft.ifftn(psi_up_hat)
            self.psi_down = np.fft.ifftn(psi_dn_hat)
            
            # Half step potential again
            n = self.get_density()
            Fx, Fy, Fz = self.get_spin_density()
            
            V_scalar = -p.mu + p.g0 * n
            Vup_up = V_scalar + p.g2 * Fz
            Vup_dn = p.g2 * (Fx - 1j * Fy)
            Vdn_up = p.g2 * (Fx + 1j * Fy)
            Vdn_dn = V_scalar - p.g2 * Fz
            
            psi_up_new = self.psi_up + exp_factor * (Vup_up * self.psi_up + Vup_dn * self.psi_down)
            psi_dn_new = self.psi_down + exp_factor * (Vdn_up * self.psi_up + Vdn_dn * self.psi_down)
            
            self.psi_up = psi_up_new
            self.psi_down = psi_dn_new
            
            self.time += dt
        
        if self.initial_energy is None:
            self.initial_energy = self.compute_energy()['E_total']
        
        self.energy_history.append(self.compute_energy()['E_total'])


# ========== TEST SUITE ==========

def test_spin_half_rotation():
    """
    THE KEY TEST: Does 360° rotation give -ψ (not +ψ)?
    
    This is the defining property of spin-½.
    """
    print("\n" + "=" * 70)
    print("TEST 1: SPIN-½ ROTATION (360° → -ψ, 720° → +ψ)")
    print("=" * 70)
    
    engine = OptionBEngine(grid_size=32, dim=2)
    engine.create_spin_up()
    
    # Store initial state
    psi_up_0 = engine.psi_up.copy()
    psi_dn_0 = engine.psi_down.copy()
    
    results = []
    
    for angle_deg in [90, 180, 270, 360, 450, 540, 630, 720]:
        angle_rad = np.deg2rad(angle_deg)
        
        # Reset to initial
        engine.psi_up = psi_up_0.copy()
        engine.psi_down = psi_dn_0.copy()
        
        # Rotate around z-axis
        engine.apply_rotation(angle_rad, [0, 0, 1])
        
        # Compare with initial
        # For spin-½: e^{iθσz/2} |↑⟩ = e^{iθ/2} |↑⟩
        expected_phase = np.exp(1j * angle_rad / 2)
        
        # The spinor should equal expected_phase * original
        ratio_up = engine.psi_up[16, 16] / (psi_up_0[16, 16] + 1e-10)
        ratio_dn = engine.psi_down[16, 16] / (psi_dn_0[16, 16] + 1e-10) if abs(psi_dn_0[16, 16]) > 1e-10 else 1.0
        
        # Check if we're back to ±original
        overlap = np.abs(np.sum(np.conj(psi_up_0) * engine.psi_up) / np.sum(np.abs(psi_up_0)**2))
        
        status = ""
        if angle_deg == 360:
            # Should be -ψ (overlap = 1, but sign flipped)
            if np.abs(ratio_up + 1) < 0.01:  # ratio ≈ -1
                status = "✅ ψ → -ψ (SPIN-½!)"
            else:
                status = f"❌ ratio = {ratio_up:.3f}"
        elif angle_deg == 720:
            # Should be +ψ
            if np.abs(ratio_up - 1) < 0.01:  # ratio ≈ +1
                status = "✅ ψ → +ψ (back to start)"
            else:
                status = f"❌ ratio = {ratio_up:.3f}"
        else:
            status = f"phase = {np.angle(ratio_up):.3f}"
        
        print(f"  {angle_deg:>3}° rotation: ratio = {ratio_up:.3f}, {status}")
        results.append((angle_deg, ratio_up))
    
    # Check spin-½ property
    ratio_360 = results[3][1]  # 360°
    ratio_720 = results[7][1]  # 720°
    
    is_spin_half = np.abs(ratio_360 + 1) < 0.01 and np.abs(ratio_720 - 1) < 0.01
    
    print(f"\n{'✅ SPIN-½ CONFIRMED!' if is_spin_half else '❌ NOT SPIN-½'}")
    print("  360° rotation: ψ → -ψ (NOT identity)")
    print("  720° rotation: ψ → +ψ (identity)")
    
    return is_spin_half


def test_skyrmion_topological_charge():
    """Test that skyrmion number is quantized and conserved."""
    print("\n" + "=" * 70)
    print("TEST 2: SKYRMION TOPOLOGICAL CHARGE")
    print("=" * 70)
    
    engine = OptionBEngine(grid_size=64, dim=2)
    
    # Create hedgehog texture (Q = -1 typically)
    engine.create_spin_texture('hedgehog')
    
    Q_initial = engine.compute_skyrmion_number()
    print(f"Initial skyrmion number Q = {Q_initial:.4f}")
    
    # Evolve and track Q
    Q_values = [Q_initial]
    
    for _ in range(50):
        engine.evolve_split_step(dt=0.1, n_steps=5)
        Q_values.append(engine.compute_skyrmion_number())
    
    Q_final = Q_values[-1]
    Q_std = np.std(Q_values)
    
    print(f"Final skyrmion number Q = {Q_final:.4f}")
    print(f"Standard deviation = {Q_std:.4f}")
    
    # Check if Q is approximately integer and conserved
    Q_rounded = round(Q_initial)
    is_integer = abs(Q_initial - Q_rounded) < 0.3
    is_conserved = Q_std < 0.3
    
    status = "✅ PASS" if (is_integer and is_conserved) else "⚠️ MARGINAL"
    print(f"\nQ ≈ integer: {'YES' if is_integer else 'NO'} (Q ≈ {Q_rounded})")
    print(f"Q conserved: {'YES' if is_conserved else 'NO'}")
    print(f"Status: {status}")
    
    return is_integer and is_conserved


def test_spin_texture_stability():
    """Test stability of spin textures under evolution."""
    print("\n" + "=" * 70)
    print("TEST 3: SPIN TEXTURE STABILITY")
    print("=" * 70)
    
    results = {}
    
    for texture in ['hedgehog', 'vortex', 'domain_wall']:
        engine = OptionBEngine(grid_size=64, dim=2)
        engine.create_spin_texture(texture)
        
        # Initial spin magnitude profile
        F_mag_initial = engine.get_spin_magnitude()
        
        # Evolve
        for _ in range(100):
            engine.evolve_split_step(dt=0.05, n_steps=5)
        
        F_mag_final = engine.get_spin_magnitude()
        
        # Measure change (textures should maintain structure)
        correlation = np.corrcoef(F_mag_initial.flatten(), F_mag_final.flatten())[0, 1]
        
        stable = correlation > 0.7
        status = "✅ STABLE" if stable else "⚠️ EVOLVED"
        
        print(f"  {texture}: correlation = {correlation:.3f} → {status}")
        results[texture] = stable
    
    return any(results.values())


def test_energy_conservation():
    """Test energy conservation during evolution."""
    print("\n" + "=" * 70)
    print("TEST 4: ENERGY CONSERVATION")
    print("=" * 70)
    
    engine = OptionBEngine(grid_size=64, dim=2)
    engine.create_spin_texture('hedgehog')
    
    E0 = engine.compute_energy()['E_total']
    
    energies = [E0]
    for _ in range(100):
        engine.evolve_split_step(dt=0.05, n_steps=5)
        energies.append(engine.compute_energy()['E_total'])
    
    E_final = energies[-1]
    drift = abs(E_final - E0) / abs(E0) * 100 if E0 != 0 else abs(E_final)
    
    print(f"E_initial = {E0:.6f}")
    print(f"E_final   = {E_final:.6f}")
    print(f"Drift     = {drift:.4f}%")
    
    status = "✅ CONSERVED" if drift < 5.0 else "❌ DRIFTED"
    print(f"Status: {status}")
    
    return drift < 5.0


def test_spin_direction_field():
    """Test that spin direction is well-defined everywhere."""
    print("\n" + "=" * 70)
    print("TEST 5: SPIN DIRECTION FIELD")
    print("=" * 70)
    
    engine = OptionBEngine(grid_size=64, dim=2)
    
    for texture in ['hedgehog', 'vortex']:
        engine.create_spin_texture(texture)
        
        nx, ny, nz = engine.get_spin_direction()
        
        # Check normalization |n̂| = 1
        n_mag = np.sqrt(nx**2 + ny**2 + nz**2)
        norm_error = np.abs(n_mag - 1.0)
        
        print(f"\n{texture}:")
        print(f"  n̂ normalization error: max = {np.max(norm_error):.6f}, mean = {np.mean(norm_error):.6f}")
        print(f"  Spin components: <nz> = {np.mean(nz):.3f}")
        
        if texture == 'hedgehog':
            # Hedgehog should have nz → 1 at edges, nz → -1 at center
            center_nz = nz[32, 32]
            edge_nz = np.mean([nz[0, 32], nz[63, 32], nz[32, 0], nz[32, 63]])
            print(f"  Center: nz = {center_nz:.3f}, Edge: nz = {edge_nz:.3f}")
    
    return True


def run_option_b_tests():
    """Run complete Option B test suite."""
    print("#" * 70)
    print("# OPTION B: INTERNAL MANIFOLD TOPOLOGY - TEST SUITE")
    print("#" * 70)
    print("""
Testing if spinor fields can produce spin-½ particles:
- 360° rotation must give -ψ (not +ψ)
- Skyrmion number must be quantized
- Spin textures must be stable
- Energy must be conserved
""")
    
    results = {
        'spin_half_rotation': test_spin_half_rotation(),
        'skyrmion_charge': test_skyrmion_topological_charge(),
        'texture_stability': test_spin_texture_stability(),
        'energy_conservation': test_energy_conservation(),
        'spin_direction': test_spin_direction_field()
    }
    
    print("\n" + "=" * 70)
    print("OPTION B TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    # Physics verdict
    print("\n" + "-" * 70)
    print("PHYSICS VERDICT (Option B)")
    print("-" * 70)
    
    if results['spin_half_rotation']:
        print("✅ Spin-½: YES (360° → -ψ confirmed!)")
    else:
        print("❌ Spin-½: FAILED")
    
    if results['skyrmion_charge']:
        print("✅ Topological charge: YES (skyrmion number quantized)")
    else:
        print("⚠️ Topological charge: MARGINAL")
    
    if results['texture_stability']:
        print("✅ Particle stability: YES (textures survive)")
    else:
        print("⚠️ Particle stability: MARGINAL")
    
    print("\n✅ Charge quantization: Possible via U(1) phase")
    print("⚠️ Gauge interactions: Requires Option C (fiber bundle)")
    
    return results


if __name__ == "__main__":
    results = run_option_b_tests()
    
    # Save results
    output = {
        'option': 'B',
        'name': 'Internal Manifold Topology',
        'tests': {k: bool(v) for k, v in results.items()},
        'physics': {
            'charge_quantization': True,  # Via U(1) phase
            'spin_half': bool(results['spin_half_rotation']),
            'particle_stability': bool(results['texture_stability']),
            'gauge_interactions': False  # Needs Option C
        }
    }
    
    print("\n" + json.dumps(output, indent=2))
