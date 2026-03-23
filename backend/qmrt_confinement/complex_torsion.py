"""
QMRT v3 Complex: Topological Torsion Field
==========================================

Adding complex phase to torsion field to enable:
  - Topological vortex solutions
  - Quantized circulation
  - Phase winding protection
  - Interference phenomena

This is the key modification suggested by the analysis:
  "Your medium may need phase winding conservation,
   torsion circulation quantization, discrete defect charge"

The complex torsion field:
  Ψ = |Ψ| e^{iθ}

Lagrangian:
  L = ½|∂_t Ψ|² - ½|∇Ψ|² - ½m²|Ψ|² - λ|Ψ|⁴

This is essentially the Gross-Pitaevskii equation (superfluid dynamics).
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ComplexQMRTParameters:
    """Parameters for complex torsion QMRT."""
    m: float = 4.0          # Mass (sets the "healing length")
    lambda_: float = 1.0    # Self-interaction
    c: float = 1.0          # Wave speed
    
    # Coupling to background (optional)
    g_rho: float = 0.1      # Coupling to compression field
    
    def healing_length(self):
        """Characteristic length scale: ξ = 1/(m√λ)"""
        return 1.0 / (self.m * np.sqrt(self.lambda_))


class ComplexTorsionEngine:
    """
    QMRT with complex torsion field supporting vortex solutions.
    
    Field: Ψ(x,t) ∈ ℂ (complex scalar)
    
    Equation of motion (Gross-Pitaevskii-like):
      i∂Ψ/∂t = -∇²Ψ + m²Ψ + λ|Ψ|²Ψ
    
    Or in Hamiltonian form:
      ∂Ψ/∂t = ∂H/∂Ψ*
      ∂Ψ*/∂t = -∂H/∂Ψ
    """
    
    def __init__(self, grid_size=64, params=None, dim=2):
        """
        Initialize complex torsion engine.
        
        Args:
            grid_size: Size of grid
            params: ComplexQMRTParameters
            dim: Dimensionality (2 or 3)
        """
        self.grid_size = grid_size
        self.dim = dim
        self.params = params or ComplexQMRTParameters()
        self.dx = 1.0
        self.time = 0.0
        
        n = grid_size
        
        # Complex field Ψ = ψ_r + i·ψ_i
        if dim == 2:
            self.psi = np.zeros((n, n), dtype=complex)
        else:
            self.psi = np.zeros((n, n, n), dtype=complex)
        
        # Precompute spectral Laplacian
        self._precompute_spectral()
        
        self.initial_energy = None
    
    def _precompute_spectral(self):
        """Precompute k² for spectral Laplacian."""
        n = self.grid_size
        k = np.fft.fftfreq(n, d=self.dx) * 2 * np.pi
        
        if self.dim == 2:
            KX, KY = np.meshgrid(k, k, indexing='ij')
            self._k_sq = KX**2 + KY**2
        else:
            KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
            self._k_sq = KX**2 + KY**2 + KZ**2
    
    def _spectral_laplacian(self, f):
        """Compute ∇²f using spectral method."""
        f_hat = np.fft.fftn(f)
        lap_hat = -self._k_sq * f_hat
        return np.fft.ifftn(lap_hat)
    
    def create_vortex(self, winding=1, center=None, core_size=None):
        """
        Create a vortex with given winding number.
        
        Ψ(r,φ) = f(r) e^{inφ}
        
        where f(r) → 0 as r → 0 (vortex core)
              f(r) → 1 as r → ∞ (bulk)
        
        Args:
            winding: Integer winding number n
            center: (x, y) center of vortex
            core_size: Size of vortex core (default: healing length)
        """
        n = self.grid_size
        
        if center is None:
            center = (n // 2, n // 2)
        
        if core_size is None:
            core_size = self.params.healing_length()
        
        if self.dim == 2:
            x = np.arange(n)
            X, Y = np.meshgrid(x, x, indexing='ij')
            
            # Relative coordinates
            dx = X - center[0]
            dy = Y - center[1]
            
            r = np.sqrt(dx**2 + dy**2) + 1e-10  # Avoid division by zero
            phi = np.arctan2(dy, dx)
            
            # Vortex amplitude profile (tanh approach to 1)
            amplitude = np.tanh(r / core_size)
            
            # Phase winds n times around the vortex
            phase = winding * phi
            
            self.psi = amplitude * np.exp(1j * phase)
        
        else:  # 3D: vortex line along z
            x = np.arange(n)
            X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
            
            dx = X - center[0]
            dy = Y - center[1]
            
            r = np.sqrt(dx**2 + dy**2) + 1e-10
            phi = np.arctan2(dy, dx)
            
            amplitude = np.tanh(r / core_size)
            phase = winding * phi
            
            self.psi = amplitude * np.exp(1j * phase)
    
    def create_oscillon(self, amplitude=1.0, width=3.0, center=None):
        """
        Create a smooth oscillon (no winding) for comparison.
        
        This is the CURRENT QMRT structure - should be LESS stable
        against fluctuations than a vortex.
        """
        n = self.grid_size
        
        if center is None:
            center = tuple([n // 2] * self.dim)
        
        if self.dim == 2:
            x = np.arange(n)
            X, Y = np.meshgrid(x, x, indexing='ij')
            R_sq = (X - center[0])**2 + (Y - center[1])**2
            self.psi = amplitude * np.exp(-R_sq / (2 * width**2)).astype(complex)
        else:
            x = np.arange(n)
            X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
            R_sq = (X - center[0])**2 + (Y - center[1])**2 + (Z - center[2])**2
            self.psi = amplitude * np.exp(-R_sq / (2 * width**2)).astype(complex)
    
    def compute_winding_number(self, center=None, radius=None):
        """
        Compute the topological winding number.
        
        n = (1/2π) ∮ ∇θ · dl
        
        Integrated around a circle centered at 'center'.
        """
        n = self.grid_size
        
        if center is None:
            center = (n // 2, n // 2)
        if radius is None:
            radius = n // 4
        
        # Get phase field
        phase = np.angle(self.psi)
        
        # Sample points on a circle
        n_points = 100
        angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        
        x_circle = center[0] + radius * np.cos(angles)
        y_circle = center[1] + radius * np.sin(angles)
        
        # Interpolate phase at these points
        from scipy.interpolate import RegularGridInterpolator
        
        if self.dim == 2:
            x = np.arange(n)
            interp = RegularGridInterpolator((x, x), phase, method='linear', bounds_error=False, fill_value=0)
            points = np.column_stack([x_circle, y_circle])
            phase_circle = interp(points)
        else:
            # For 3D, take slice at z = center
            phase_2d = phase[:, :, n // 2]
            x = np.arange(n)
            interp = RegularGridInterpolator((x, x), phase_2d, method='linear', bounds_error=False, fill_value=0)
            points = np.column_stack([x_circle, y_circle])
            phase_circle = interp(points)
        
        # Compute winding: sum of phase jumps
        phase_diff = np.diff(phase_circle)
        
        # Handle branch cuts (phase jumps > π)
        phase_diff = np.mod(phase_diff + np.pi, 2*np.pi) - np.pi
        
        winding = np.sum(phase_diff) / (2 * np.pi)
        
        return round(winding)
    
    def compute_energy(self) -> Dict[str, float]:
        """Compute total energy broken down by component."""
        p = self.params
        dV = self.dx**self.dim
        
        psi_sq = np.abs(self.psi)**2
        
        # Kinetic energy (gradient): ½|∇Ψ|²
        lap_psi = self._spectral_laplacian(self.psi)
        E_gradient = 0.5 * np.real(np.sum(-np.conj(self.psi) * lap_psi)) * dV
        
        # Mass energy: ½m²|Ψ|²
        E_mass = 0.5 * p.m**2 * np.sum(psi_sq) * dV
        
        # Interaction energy: λ|Ψ|⁴
        E_interaction = p.lambda_ * np.sum(psi_sq**2) * dV
        
        return {
            'E_gradient': E_gradient,
            'E_mass': E_mass,
            'E_interaction': E_interaction,
            'E_total': E_gradient + E_mass + E_interaction
        }
    
    def evolve_timestep(self, dt):
        """
        Evolve using split-step method (common for GP equation).
        
        i∂Ψ/∂t = -∇²Ψ + m²Ψ + λ|Ψ|²Ψ
        """
        p = self.params
        
        # Half-step in real space (potential terms)
        V = p.m**2 + p.lambda_ * np.abs(self.psi)**2
        self.psi *= np.exp(-0.5j * V * dt)
        
        # Full step in Fourier space (kinetic term)
        psi_hat = np.fft.fftn(self.psi)
        psi_hat *= np.exp(-1j * self._k_sq * dt)
        self.psi = np.fft.ifftn(psi_hat)
        
        # Half-step in real space again
        V = p.m**2 + p.lambda_ * np.abs(self.psi)**2
        self.psi *= np.exp(-0.5j * V * dt)
        
        self.time += dt
    
    def add_noise(self, strength):
        """Add complex noise to the field."""
        noise = strength * (np.random.randn(*self.psi.shape) + 1j * np.random.randn(*self.psi.shape))
        self.psi += noise


def test_vortex_stability():
    """
    KEY TEST: Is a vortex more stable than an oscillon?
    
    Vortex: Topologically protected (winding number conserved)
    Oscillon: Not protected (can dissolve)
    """
    print("=" * 70)
    print("TEST: VORTEX vs OSCILLON STABILITY UNDER NOISE")
    print("=" * 70)
    print("""
Comparing stability of:
  1. Vortex (winding number n=1) - topologically protected
  2. Oscillon (winding number n=0) - not protected

Both subjected to the same noise. Which survives?
""")
    
    params = ComplexQMRTParameters(m=4.0, lambda_=1.0)
    
    noise_strengths = [0, 0.01, 0.05, 0.1, 0.2]
    
    print(f"\n{'Noise':>10} | {'Vortex n':>12} | {'Vortex |Ψ|':>12} | {'Oscillon |Ψ|':>14}")
    print("-" * 55)
    
    for noise in noise_strengths:
        # Test vortex
        engine_vortex = ComplexTorsionEngine(grid_size=64, params=params, dim=2)
        engine_vortex.create_vortex(winding=1)
        initial_winding = engine_vortex.compute_winding_number()
        
        # Test oscillon
        engine_oscillon = ComplexTorsionEngine(grid_size=64, params=params, dim=2)
        engine_oscillon.create_oscillon(amplitude=1.0, width=3.0)
        
        # Add noise and evolve
        if noise > 0:
            engine_vortex.add_noise(noise)
            engine_oscillon.add_noise(noise)
        
        for _ in range(500):
            engine_vortex.evolve_timestep(0.01)
            engine_oscillon.evolve_timestep(0.01)
        
        # Measure final state
        final_winding = engine_vortex.compute_winding_number()
        vortex_max = np.max(np.abs(engine_vortex.psi))
        oscillon_max = np.max(np.abs(engine_oscillon.psi))
        
        print(f"{noise:>10.2f} | {final_winding:>12} | {vortex_max:>12.4f} | {oscillon_max:>14.4f}")
    
    print("""
Key question: Does the vortex preserve its winding number n=1
even under noise, while the oscillon dissolves?
""")


def test_winding_conservation():
    """
    Test that winding number is conserved during evolution.
    
    This is the TOPOLOGICAL PROTECTION we need.
    """
    print("\n" + "=" * 70)
    print("TEST: WINDING NUMBER CONSERVATION")
    print("=" * 70)
    print("""
Winding number n = (1/2π) ∮ ∇θ · dl

This is a TOPOLOGICAL INVARIANT.
It cannot change under continuous evolution!

Testing if n is preserved over time.
""")
    
    params = ComplexQMRTParameters(m=4.0, lambda_=1.0)
    
    for n_init in [1, 2, -1]:
        engine = ComplexTorsionEngine(grid_size=64, params=params, dim=2)
        engine.create_vortex(winding=n_init)
        
        windings = []
        
        for step in range(600):
            engine.evolve_timestep(0.01)
            if step % 50 == 0:
                n = engine.compute_winding_number()
                windings.append(n)
        
        all_same = all(w == n_init for w in windings)
        status = "✅ CONSERVED" if all_same else "❌ CHANGED"
        
        print(f"Initial n = {n_init:+d}: {windings} → {status}")


def test_interference():
    """
    Test if two vortices produce interference patterns.
    
    This is a KEY quantum signature!
    """
    print("\n" + "=" * 70)
    print("TEST: INTERFERENCE FROM PHASE")
    print("=" * 70)
    print("""
Complex fields can interfere:
  |Ψ₁ + Ψ₂|² = |Ψ₁|² + |Ψ₂|² + 2Re(Ψ₁*Ψ₂)
  
The cross-term gives INTERFERENCE FRINGES!
""")
    
    params = ComplexQMRTParameters(m=2.0, lambda_=0.5)
    engine = ComplexTorsionEngine(grid_size=64, params=params, dim=2)
    
    n = engine.grid_size
    x = np.arange(n)
    X, Y = np.meshgrid(x, x, indexing='ij')
    
    # Two wave packets with different phases
    center1 = (n//3, n//2)
    center2 = (2*n//3, n//2)
    
    R_sq1 = (X - center1[0])**2 + (Y - center1[1])**2
    R_sq2 = (X - center2[0])**2 + (Y - center2[1])**2
    
    width = 5.0
    k = 0.5  # Wave vector
    
    psi1 = np.exp(-R_sq1 / (2 * width**2)) * np.exp(1j * k * X)
    psi2 = np.exp(-R_sq2 / (2 * width**2)) * np.exp(-1j * k * X)
    
    engine.psi = psi1 + psi2
    
    # Measure interference
    intensity = np.abs(engine.psi)**2
    
    # Check for fringes (oscillations in intensity)
    intensity_line = intensity[n//2, :]
    
    # FFT to detect periodic structure
    from scipy.fft import fft, fftfreq
    spectrum = np.abs(fft(intensity_line - np.mean(intensity_line)))
    freqs = fftfreq(len(intensity_line))
    
    # Find dominant frequency
    pos_mask = freqs > 0.01
    if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 0:
        dominant_freq = freqs[pos_mask][np.argmax(spectrum[pos_mask])]
        
        print(f"Interference fringe spacing: {1/dominant_freq:.1f} grid units")
        print(f"Expected from k: {np.pi/k:.1f} grid units")
        
        if dominant_freq > 0.01:
            print("\n✅ INTERFERENCE FRINGES DETECTED!")
        else:
            print("\n⚠️ No clear interference pattern")


def test_circulation_quantization():
    """
    Test if circulation is quantized.
    
    Γ = ∮ v · dl = (h/m) × n
    
    where v = (ℏ/m)∇θ is the "superfluid velocity"
    """
    print("\n" + "=" * 70)
    print("TEST: CIRCULATION QUANTIZATION")
    print("=" * 70)
    print("""
In a superfluid, circulation is quantized:
  Γ = ∮ v·dl = (h/m) × n

where n is the winding number (integer).

This is the ORIGIN of quantization in superfluids!
""")
    
    params = ComplexQMRTParameters(m=4.0, lambda_=1.0)
    
    print(f"\n{'Winding n':>12} | {'Circulation Γ':>15} | {'Γ/n':>12} | {'Γ₀ = Γ/n':>12}")
    print("-" * 60)
    
    circulations = []
    
    for n_wind in [1, 2, 3, -1, -2]:
        engine = ComplexTorsionEngine(grid_size=64, params=params, dim=2)
        engine.create_vortex(winding=n_wind)
        
        # Compute circulation numerically
        # Γ = ∮ (ℏ/m)∇θ · dl
        
        phase = np.angle(engine.psi)
        
        # Gradient of phase
        grad_phase_x = np.gradient(phase, axis=0)
        grad_phase_y = np.gradient(phase, axis=1)
        
        # Integrate around a circle
        n_grid = engine.grid_size
        center = (n_grid // 2, n_grid // 2)
        radius = n_grid // 4
        
        n_points = 200
        angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        d_angle = angles[1] - angles[0]
        
        circulation = 0
        for angle in angles:
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            
            if 0 <= x < n_grid and 0 <= y < n_grid:
                # Tangent direction
                tx = -np.sin(angle)
                ty = np.cos(angle)
                
                # v · dl = (grad_θ · t̂) × r × dθ
                v_dot_t = grad_phase_x[x, y] * tx + grad_phase_y[x, y] * ty
                circulation += v_dot_t * radius * d_angle
        
        # In units where ℏ = 1: Γ = n × 2π
        ratio = circulation / n_wind if n_wind != 0 else 0
        
        circulations.append(ratio)
        print(f"{n_wind:>12} | {circulation:>15.4f} | {ratio:>12.4f} | {ratio/(2*np.pi):>12.4f}")
    
    # Check if Γ/n is constant
    valid_ratios = [c for c in circulations if abs(c) > 0.1]
    if valid_ratios:
        mean_ratio = np.mean([abs(r) for r in valid_ratios])
        std_ratio = np.std([abs(r) for r in valid_ratios])
        cv = std_ratio / mean_ratio if mean_ratio > 0 else float('inf')
        
        print(f"\nΓ₀ = Γ/n statistics: mean = {mean_ratio:.4f}, CV = {cv:.1%}")
        
        if cv < 0.05:
            print("\n✅ CIRCULATION IS QUANTIZED!")
            print(f"   Quantum of circulation: Γ₀ = {mean_ratio:.4f}")
            print(f"   This is the EMERGENT ℏ!")


def summarize_complex_torsion():
    """Summary of complex torsion exploration."""
    print("\n" + "=" * 70)
    print("COMPLEX TORSION: SUMMARY")
    print("=" * 70)
    
    print("""
WHAT WE'RE TESTING:

Adding complex phase to torsion field:
  τ → Ψ = |Ψ| e^{iθ}

This enables:
  1. Vortex solutions (topological defects)
  2. Winding number conservation
  3. Quantized circulation
  4. Interference phenomena

KEY QUESTIONS:

1. Are vortices more stable than oscillons under noise?
   → If yes, topology provides the protection we need

2. Is winding number conserved?
   → If yes, we have topological quantum numbers

3. Is circulation quantized?
   → If yes, Γ₀ = h/m defines emergent ℏ

4. Do we see interference?
   → If yes, phase matters and Born rule may emerge

THIS IS THE PATH FORWARD:

"Topology before stochasticity"

First establish topologically protected structures.
Then add fluctuations.
The protection ensures stability.
The quantization gives ℏ.
""")


def main():
    """Run complex torsion exploration."""
    print("#" * 70)
    print("# QMRT COMPLEX TORSION: TOPOLOGICAL PROTECTION")
    print("#" * 70)
    print("""
Exploring the missing ingredient: complex phase with topology.

"Your medium may need phase winding conservation,
 torsion circulation quantization, discrete defect charge"
""")
    
    test_vortex_stability()
    test_winding_conservation()
    test_circulation_quantization()
    test_interference()
    summarize_complex_torsion()


if __name__ == "__main__":
    main()
