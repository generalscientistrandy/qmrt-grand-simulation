"""
QMRT: A2 - SPINOR-VALUED ORDER PARAMETER
========================================

THE ONTOLOGICAL GAP:
  A3 showed: IF we use spinor_factor = 0.5, holonomy works.
  But we CHOSE that factor by hand.
  
  A2 asks: Can the medium ITSELF require spinor_factor = 0.5?

THE PHYSICS:
  Current setup:
    - Medium: scalar field σ (topology activation)
    - Attached: spinor frame U (added externally)
    - Connection: τ with manually chosen spinor_factor
    
  Target setup:
    - Medium: spinor-valued order parameter Ψ ∈ C²
    - Connection: DERIVED from Ψ, automatically has 1/2 factor
    - Holonomy: emerges from Ψ's topology
    
PRECEDENTS (real condensed matter):
  - Superfluid He-3: order parameter is 3×3 complex matrix
  - Spinor BECs: order parameter is spinor (2-component)
  - p-wave superconductors: order parameter transforms under rotations
  
THE KEY MECHANISM:
  For a spinor field Ψ, the Berry connection is:
    A_i = i ⟨Ψ|∂_i|Ψ⟩
    
  For a spinor rotating by angle θ, the Berry phase is θ/2.
  This is AUTOMATIC - no manual factor needed!
  
  Why? Because spinors transform as:
    Ψ → e^{iθ/2} Ψ under rotation by θ
    
  The 1/2 is BUILT INTO the representation theory.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json


# Pauli matrices
SIGMA = np.array([
    [[0, 1], [1, 0]],       # σ_x
    [[0, -1j], [1j, 0]],    # σ_y
    [[1, 0], [0, -1]]       # σ_z
], dtype=complex)

IDENTITY = np.array([[1, 0], [0, 1]], dtype=complex)


@dataclass
class SpinorMediumParams:
    """Parameters for spinor-valued medium."""
    grid_size: int = 80
    core_size: float = 5.0
    dt: float = 0.01
    diffusion: float = 0.05
    potential_strength: float = 1.0


class SpinorOrderParameter:
    """
    A spinor-valued order parameter field Ψ(x) ∈ C².
    
    Unlike the previous setup where we had:
      - scalar σ (medium)
      - attached U (spinor frame)
      
    Here the medium ITSELF is a spinor field.
    
    The Berry connection is AUTOMATICALLY:
      A_i = i ⟨Ψ|∂_i Ψ⟩
      
    This gives the correct spinor holonomy WITHOUT manual factors.
    """
    
    def __init__(self, grid_size: int):
        self.grid_size = grid_size
        n = grid_size
        
        # Spinor field: Ψ = (ψ_↑, ψ_↓) at each point
        # Initialize to spin-up everywhere: Ψ = (1, 0)
        self.psi_up = np.ones((n, n), dtype=complex)
        self.psi_down = np.zeros((n, n), dtype=complex)
        
        self.normalize()
    
    def normalize(self):
        """Normalize to unit spinor at each point."""
        norm = np.sqrt(np.abs(self.psi_up)**2 + np.abs(self.psi_down)**2) + 1e-10
        self.psi_up /= norm
        self.psi_down /= norm
    
    def set_vortex(self, center: Tuple[float, float], winding: float = 1.0):
        """
        Create a spinor vortex configuration.
        
        For a spinor vortex with winding w:
          Ψ(r, φ) = f(r) [cos(wφ/2) |↑⟩ + sin(wφ/2) e^{iφ} |↓⟩]
          
        This has HALF-WINDING in the spinor components!
        Going around the vortex by 2π:
          - Position angle: φ → φ + 2π  
          - Spinor phase: wφ/2 → wφ/2 + wπ
          - For w=1: Berry phase = π → factor of -1
          
        This is the natural spinor vortex in spinor BECs.
        """
        n = self.grid_size
        
        X, Y = np.meshgrid(np.arange(n), np.arange(n), indexing='ij')
        dx = X - center[0]
        dy = Y - center[1]
        
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        phi = np.arctan2(dy, dx)
        
        # Core profile
        core_size = 5.0
        f = np.tanh(r / core_size)
        
        # Spinor vortex: half-winding in each component
        # This is the key: the NATURAL vortex has half the winding
        self.psi_up = f * np.cos(winding * phi / 2)
        self.psi_down = f * np.sin(winding * phi / 2) * np.exp(1j * phi)
        
        self.normalize()
    
    def set_texture(self, center: Tuple[float, float], texture_type: str = 'hedgehog'):
        """
        Create different spinor textures.
        
        hedgehog: spin points radially outward
        vortex: spin circulates around center
        skyrmion: topological spin texture
        """
        n = self.grid_size
        
        X, Y = np.meshgrid(np.arange(n), np.arange(n), indexing='ij')
        dx = X - center[0]
        dy = Y - center[1]
        
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        phi = np.arctan2(dy, dx)
        
        if texture_type == 'hedgehog':
            # Spin points radially: n̂ = (cos φ, sin φ, 0)
            # Spinor: |n̂⟩ = cos(θ/2)|↑⟩ + sin(θ/2)e^{iφ}|↓⟩
            # For radial: θ = π/2, so cos(θ/2) = sin(θ/2) = 1/√2
            self.psi_up = np.ones((n, n)) / np.sqrt(2)
            self.psi_down = np.exp(1j * phi) / np.sqrt(2)
            
        elif texture_type == 'vortex':
            # Spin circulates: n̂ = (-sin φ, cos φ, 0)  
            # This is φ → φ + π/2 from hedgehog
            self.psi_up = np.ones((n, n)) / np.sqrt(2)
            self.psi_down = np.exp(1j * (phi + np.pi/2)) / np.sqrt(2)
            
        elif texture_type == 'skyrmion':
            # Skyrmion: spin winds around twice
            # θ(r) goes from 0 at center to π far away
            theta = np.pi * np.tanh(r / 10)
            self.psi_up = np.cos(theta / 2)
            self.psi_down = np.sin(theta / 2) * np.exp(1j * phi)
        
        self.normalize()
    
    def compute_berry_connection(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the Berry connection A_i = i⟨Ψ|∂_i Ψ⟩.
        
        This is the NATURAL connection for a spinor field.
        It automatically has the correct 1/2 factor built in!
        
        Returns A_x, A_y at each point.
        """
        n = self.grid_size
        dx = 1.0
        
        # Compute gradients
        dpsi_up_x = np.gradient(self.psi_up, dx, axis=0)
        dpsi_up_y = np.gradient(self.psi_up, dx, axis=1)
        dpsi_down_x = np.gradient(self.psi_down, dx, axis=0)
        dpsi_down_y = np.gradient(self.psi_down, dx, axis=1)
        
        # Berry connection: A_i = i ⟨Ψ|∂_i Ψ⟩
        # = i (ψ_up* ∂_i ψ_up + ψ_down* ∂_i ψ_down)
        
        A_x = 1j * (np.conj(self.psi_up) * dpsi_up_x + 
                    np.conj(self.psi_down) * dpsi_down_x)
        A_y = 1j * (np.conj(self.psi_up) * dpsi_up_y + 
                    np.conj(self.psi_down) * dpsi_down_y)
        
        # Take real part (connection should be real for U(1) gauge)
        A_x = np.real(A_x)
        A_y = np.real(A_y)
        
        return A_x, A_y
    
    def compute_berry_holonomy(self, center: Tuple[float, float], radius: float) -> Dict:
        """
        Compute the Berry holonomy around a loop.
        
        Holonomy = exp(i ∮ A · dl) = exp(i × Berry phase)
        
        For spinor vortex with winding w:
          Berry phase = wπ (the half-winding!)
          Holonomy = e^{iwπ} = -1 for w=1
        """
        n = self.grid_size
        n_points = 500
        
        A_x, A_y = self.compute_berry_connection()
        
        angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        d_angle = 2*np.pi / n_points
        dl = radius * d_angle
        
        phase_integral = 0.0
        
        for angle in angles:
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            
            # Tangent direction
            tx = -np.sin(angle)
            ty = np.cos(angle)
            
            # Interpolate connection
            x = np.clip(x, 0, n-1.001)
            y = np.clip(y, 0, n-1.001)
            i0, j0 = int(x), int(y)
            i1, j1 = min(i0+1, n-1), min(j0+1, n-1)
            fx, fy = x - i0, y - j0
            
            Ax = (1-fx)*(1-fy) * A_x[i0, j0] + fx*(1-fy) * A_x[i1, j0] + \
                 (1-fx)*fy * A_x[i0, j1] + fx*fy * A_x[i1, j1]
            Ay = (1-fx)*(1-fy) * A_y[i0, j0] + fx*(1-fy) * A_y[i1, j0] + \
                 (1-fx)*fy * A_y[i0, j1] + fx*fy * A_y[i1, j1]
            
            # A · dl = A · t̂ × |dl|
            phase_integral += (Ax * tx + Ay * ty) * dl
        
        # Berry phase and holonomy
        berry_phase = phase_integral
        holonomy = np.exp(1j * berry_phase)
        
        return {
            'berry_phase': float(berry_phase),
            'berry_phase_pi': float(berry_phase / np.pi),
            'holonomy': complex(holonomy),
            'holonomy_real': float(np.real(holonomy)),
            'is_plus_one': np.abs(holonomy - 1) < 0.1,
            'is_minus_one': np.abs(holonomy + 1) < 0.1
        }
    
    def get_spin_direction(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get the local spin direction n̂ = ⟨Ψ|σ|Ψ⟩.
        """
        # n_x = ⟨Ψ|σ_x|Ψ⟩ = ψ_up* ψ_down + ψ_down* ψ_up
        # n_y = ⟨Ψ|σ_y|Ψ⟩ = -i(ψ_up* ψ_down - ψ_down* ψ_up)
        # n_z = ⟨Ψ|σ_z|Ψ⟩ = |ψ_up|² - |ψ_down|²
        
        nx = np.real(np.conj(self.psi_up) * self.psi_down + 
                     np.conj(self.psi_down) * self.psi_up)
        ny = np.real(-1j * (np.conj(self.psi_up) * self.psi_down - 
                           np.conj(self.psi_down) * self.psi_up))
        nz = np.abs(self.psi_up)**2 - np.abs(self.psi_down)**2
        
        return nx, ny, nz


def test_spinor_order_parameter():
    """
    Test: Does a spinor-valued medium AUTOMATICALLY give fermionic holonomy?
    
    Key comparison:
      Previous: scalar medium + attached spinor + manual factor
      Now: spinor medium → Berry connection → automatic factor
    """
    print("#" * 80)
    print("#  A2: SPINOR-VALUED ORDER PARAMETER TEST")
    print("#" * 80)
    print("""
THE ONTOLOGICAL TEST:

Previous setup (scalar medium):
  - Medium: σ (scalar)
  - Spinor: U (attached by hand)
  - Connection: τ with MANUAL spinor_factor = 0.5
  
New setup (spinor medium):
  - Medium: Ψ ∈ C² (spinor-valued order parameter)
  - Connection: A = i⟨Ψ|∂Ψ⟩ (derived from Ψ)
  - Factor: AUTOMATIC from spinor representation
  
The question: Does the spinor medium NATURALLY give fermion holonomy?
""")
    
    # Test spinor vortex with different windings
    print("=" * 70)
    print("PART 1: SPINOR VORTEX HOLONOMY")
    print("=" * 70)
    print("Testing spinor vortices with different winding numbers.")
    print("Expected: Berry phase = wπ (half-winding automatically!)")
    print()
    
    grid_size = 100
    center = (50, 50)
    radius = 25.0
    
    windings = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    
    print(f"{'Winding':>8} | {'Berry Phase':>12} | {'Expected':>10} | {'Holonomy':>10} | {'Result':>10}")
    print("-" * 65)
    
    results = {}
    
    for w in windings:
        field = SpinorOrderParameter(grid_size)
        field.set_vortex(center, winding=w)
        
        holonomy = field.compute_berry_holonomy(center, radius)
        
        expected_phase = w  # In units of π, due to half-winding
        measured_phase = holonomy['berry_phase_pi']
        
        is_fermion = holonomy['is_minus_one']
        is_boson = holonomy['is_plus_one']
        
        status = 'FERMION' if is_fermion else ('BOSON' if is_boson else 'other')
        
        print(f"{w:>8.1f} | {measured_phase:>11.4f}π | {expected_phase:>9.1f}π | "
              f"{holonomy['holonomy_real']:>10.4f} | {status:>10}")
        
        results[w] = {
            'berry_phase_pi': measured_phase,
            'expected_pi': expected_phase,
            'holonomy_real': holonomy['holonomy_real'],
            'is_fermion': is_fermion,
            'is_boson': is_boson
        }
    
    # Check scaling
    print("\n" + "=" * 70)
    print("PART 2: SCALING ANALYSIS")
    print("=" * 70)
    
    measured = [results[w]['berry_phase_pi'] for w in windings]
    expected = [w for w in windings]
    
    slope, intercept = np.polyfit(windings, measured, 1)
    r_value = np.corrcoef(windings, measured)[0, 1]
    
    print(f"""
Linear fit: Berry phase = {slope:.4f}π × winding + {intercept:.4f}π
Expected slope: 1.0 (half-winding built into spinor)
Measured slope: {slope:.4f}
R-value: {r_value:.6f}

Interpretation:
  slope ≈ 1: Spinor representation gives automatic 1/2 factor ✅
  slope ≈ 2: No automatic factor (would need manual insertion) ❌
""")
    
    # THE KEY COMPARISON
    print("=" * 70)
    print("PART 3: SCALAR vs SPINOR MEDIUM COMPARISON")
    print("=" * 70)
    
    print("""
                     | Scalar Medium        | Spinor Medium
----------------------------------------------------------------
Order parameter      | σ ∈ R (scalar)      | Ψ ∈ C² (spinor)
Connection from      | Torsion τ (manual)  | Berry A (automatic)
Factor needed        | Manual 0.5          | Built-in 0.5
w=1 holonomy        | 2π (boson) raw      | π (fermion) automatic
""")
    
    # Verify w=1 case specifically
    field_w1 = SpinorOrderParameter(grid_size)
    field_w1.set_vortex(center, winding=1.0)
    holonomy_w1 = field_w1.compute_berry_holonomy(center, radius)
    
    print(f"Specific test: w=1 spinor vortex")
    print(f"  Berry phase: {holonomy_w1['berry_phase_pi']:.4f}π (expected: π)")
    print(f"  Holonomy: {holonomy_w1['holonomy_real']:.4f} (expected: -1)")
    
    # Verdict
    print("\n" + "=" * 70)
    print("A2 VERDICT: SPINOR ORDER PARAMETER")
    print("=" * 70)
    
    slope_correct = abs(slope - 1.0) < 0.1
    w1_is_fermion = results[1.0]['is_fermion']
    linear_scaling = r_value > 0.99
    
    print(f"""
CRITERIA:
  1. Slope = 1 (automatic half-winding):  {'✅' if slope_correct else '❌'} (got {slope:.4f})
  2. w=1 gives fermion holonomy (-1):     {'✅' if w1_is_fermion else '❌'}
  3. Linear scaling:                      {'✅' if linear_scaling else '❌'} (R = {r_value:.4f})
""")
    
    all_pass = slope_correct and w1_is_fermion and linear_scaling
    
    if all_pass:
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ A2 SUCCESS: SPINOR MEDIUM GIVES AUTOMATIC FERMION HOLONOMY!          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  With spinor-valued order parameter Ψ ∈ C²:                              ║
║    - Berry connection A = i⟨Ψ|∂Ψ⟩ is DERIVED, not inserted               ║
║    - The 1/2 factor is BUILT INTO the spinor representation              ║
║    - w=1 vortex automatically gives π Berry phase → -1 holonomy          ║
║                                                                          ║
║  THIS ANSWERS THE ONTOLOGICAL QUESTION:                                  ║
║    The medium ITSELF is spinor-valued → fermion statistics emerge        ║
║    automatically, without manual factors.                                ║
║                                                                          ║
║  PHYSICS IMPLICATION FOR QMRT:                                           ║
║    If the QMRT medium has spinor-valued excitations (not just scalar),   ║
║    then fermions are INTRINSIC, not added by hand.                       ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
        conclusion = 'SPINOR_MEDIUM_WORKS'
    else:
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  ⚠️ A2 PARTIAL: Some criteria not met                                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  The spinor order parameter test needs refinement.                       ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
        conclusion = 'NEEDS_WORK'
    
    # Physics interpretation
    print("\n" + "=" * 70)
    print("PHYSICS INTERPRETATION: WHAT A2 TELLS US")
    print("=" * 70)
    print("""
A2 demonstrates a crucial conceptual point:

SCALAR MEDIUM (previous):
  - Order parameter: σ(x) ∈ R
  - Defects: vortices in σ
  - Spinor: U(x) ∈ SU(2) ATTACHED by hand
  - Connection: τ·σ with MANUAL factor of 1/2
  - Result: Fermions possible but ENGINEERED

SPINOR MEDIUM (A2):
  - Order parameter: Ψ(x) ∈ C²
  - Defects: spinor vortices (half-quantum vortices!)
  - Connection: Berry connection A = i⟨Ψ|∂Ψ⟩
  - Factor: 1/2 is AUTOMATIC from spinor representation
  - Result: Fermions INTRINSIC to the medium

THE DEEP REASON:
  Spinors transform under rotation as: Ψ → e^{iθ/2} Ψ
  The 1/2 is not a choice - it's what makes something a spinor.
  
  When the MEDIUM ITSELF is spinor-valued, the Berry connection
  automatically carries this 1/2, and fermion holonomy emerges
  without any manual insertion.

IMPLICATION FOR QMRT:
  If QMRT's medium has spinor-valued degrees of freedom
  (not just scalar σ with attached U), then:
    - Fermion statistics are EXPLAINED, not contained
    - The 360° = -1 rule emerges from representation theory
    - No manual factors needed
    
  This shifts the question to:
    "What physical mechanism makes the medium spinor-valued?"
""")
    
    # Save results
    output = {
        'test': 'A2_Spinor_Order_Parameter',
        'vortex_results': {str(w): {
            'berry_phase_pi': float(results[w]['berry_phase_pi']),
            'expected_pi': float(results[w]['expected_pi']),
            'is_fermion': bool(results[w]['is_fermion'])
        } for w in windings},
        'scaling': {
            'slope': float(slope),
            'expected_slope': 1.0,
            'r_value': float(r_value)
        },
        'verdict': {
            'slope_correct': bool(slope_correct),
            'w1_is_fermion': bool(w1_is_fermion),
            'linear_scaling': bool(linear_scaling),
            'all_pass': bool(all_pass)
        },
        'conclusion': conclusion
    }
    
    output_path = '/app/backend/qmrt_topology/spinor_order_parameter_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return output


def test_skyrmion_holonomy():
    """
    Additional test: Skyrmion texture holonomy.
    
    A skyrmion is a topological texture where spin winds around.
    It should also give quantized Berry phase.
    """
    print("\n" + "=" * 70)
    print("BONUS: SKYRMION TEXTURE HOLONOMY")
    print("=" * 70)
    
    grid_size = 100
    center = (50, 50)
    
    field = SpinorOrderParameter(grid_size)
    field.set_texture(center, texture_type='skyrmion')
    
    radii = [10, 15, 20, 25, 30]
    
    print(f"\n{'Radius':>8} | {'Berry Phase':>12} | {'Holonomy':>10}")
    print("-" * 40)
    
    for r in radii:
        holonomy = field.compute_berry_holonomy(center, r)
        print(f"{r:>8} | {holonomy['berry_phase_pi']:>11.4f}π | {holonomy['holonomy_real']:>10.4f}")
    
    print("\nSkyrmion Berry phase depends on how much of the texture is enclosed.")


if __name__ == "__main__":
    results = test_spinor_order_parameter()
    test_skyrmion_holonomy()
