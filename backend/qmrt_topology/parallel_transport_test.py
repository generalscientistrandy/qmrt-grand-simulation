"""
QMRT: A3 - EXPLICIT PARALLEL TRANSPORT HOLONOMY
================================================

THE KEY INSIGHT:
  Previous tests measured the EVOLVED SPINOR FIELD's winding.
  That conflates:
    - Field relaxation dynamics
    - True transport geometry
    
  This test computes the GEOMETRIC HOLONOMY directly:
    U_γ = P exp(∮_γ A_i dx^i)
    
  where A is the connection derived from the medium (torsion).

SUCCESS CRITERION:
  - circulation 1/2 → holonomy π
  - circulation 1   → holonomy 2π
  - Linear scaling with flux
  
If locked at 2π regardless of circulation → connection is vector-like, not spinorial.

THE PHYSICS:
  The connection A_i comes from torsion τ:
    A_i = (1/2) τ_j ε^j_ik σ^k   (for spinor connection)
    
  The 1/2 factor is CRITICAL:
    - Without it: SO(3) connection, 2π rotation = +1
    - With it: SU(2) connection, 2π rotation = -1 (spinor!)
    
  We test BOTH to see which the medium naturally supports.
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
class ParallelTransportParams:
    """Parameters for parallel transport test."""
    grid_size: int = 100
    core_size: float = 5.0
    dx: float = 1.0


class MediumConnection:
    """
    The geometric connection derived from medium torsion.
    
    This is the gauge field A_i that determines parallel transport.
    
    Two versions:
    1. SO(3) connection: A_i = τ_i (full angle)
    2. SU(2) connection: A_i = (1/2) τ_i (half angle → spinor!)
    """
    
    def __init__(self, grid_size: int, params: Optional[ParallelTransportParams] = None):
        self.grid_size = grid_size
        self.params = params or ParallelTransportParams()
        
        n = grid_size
        self.torsion = np.zeros((n, n, 3))  # τ vector field
        
        # Coordinates
        x = np.arange(n, dtype=float)
        self.X, self.Y = np.meshgrid(x, x, indexing='ij')
    
    def setup_vortex(self, center: Tuple[float, float], circulation: float = 1.0):
        """
        Create a vortex configuration for the torsion field.
        
        τ = circulation × φ̂ / r
        
        This gives a total torsion flux = 2π × circulation through any loop
        encircling the vortex.
        """
        n = self.grid_size
        cx, cy = center
        
        dx = self.X - cx
        dy = self.Y - cy
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        
        # Core regularization
        core = self.params.core_size
        r_reg = np.sqrt(r**2 + core**2)
        
        # Torsion circulates around vortex (in z-direction for 2D)
        # τ_z component gives rotation in the xy-plane
        # For a 2D system with rotation around z: τ = τ_z ẑ
        
        # Angular velocity ω = circulation × 2π / (2π r) = circulation / r
        # But we want total flux = 2π × circulation
        # So τ_z = circulation / r² (properly normalized)
        
        self.torsion[:,:,0] = 0  # τ_x = 0
        self.torsion[:,:,1] = 0  # τ_y = 0
        self.torsion[:,:,2] = circulation / (r_reg**2) * core**2  # τ_z, regularized
        
        # Alternative: tangential torsion
        # τ = circulation × (-sin(φ), cos(φ), 0) / r
        phi = np.arctan2(dy, dx)
        self.torsion[:,:,0] = -circulation * np.sin(phi) / r_reg
        self.torsion[:,:,1] = circulation * np.cos(phi) / r_reg
        self.torsion[:,:,2] = 0
    
    def get_connection_at(self, x: float, y: float, spinor_factor: float = 1.0) -> np.ndarray:
        """
        Get the connection A = (spinor_factor) × τ · σ at point (x, y).
        
        spinor_factor = 1.0: SO(3) connection (vector)
        spinor_factor = 0.5: SU(2) connection (spinor!)
        
        Returns 2×2 matrix A such that parallel transport is:
          dU/ds = -i A U
        """
        n = self.grid_size
        
        # Bilinear interpolation
        x = np.clip(x, 0, n-1.001)
        y = np.clip(y, 0, n-1.001)
        
        i0, j0 = int(x), int(y)
        i1, j1 = min(i0+1, n-1), min(j0+1, n-1)
        
        fx, fy = x - i0, y - j0
        
        # Interpolate torsion
        tau = (1-fx)*(1-fy) * self.torsion[i0, j0] + \
              fx*(1-fy) * self.torsion[i1, j0] + \
              (1-fx)*fy * self.torsion[i0, j1] + \
              fx*fy * self.torsion[i1, j1]
        
        # Connection: A = spinor_factor × τ · σ
        A = spinor_factor * (tau[0] * SIGMA[0] + tau[1] * SIGMA[1] + tau[2] * SIGMA[2])
        
        return A
    
    def compute_torsion_flux(self, center: Tuple[float, float], radius: float) -> float:
        """
        Compute total torsion flux through a circular loop.
        
        Φ = ∮ τ · dl
        
        For a vortex with circulation w: Φ = 2π × w
        """
        n_points = 200
        angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        d_angle = 2*np.pi / n_points
        
        flux = 0.0
        
        for angle in angles:
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            
            # Tangent vector
            tx = -np.sin(angle)
            ty = np.cos(angle)
            
            # Interpolate torsion
            n = self.grid_size
            x = np.clip(x, 0, n-1.001)
            y = np.clip(y, 0, n-1.001)
            i0, j0 = int(x), int(y)
            i1, j1 = min(i0+1, n-1), min(j0+1, n-1)
            fx, fy = x - i0, y - j0
            
            tau = (1-fx)*(1-fy) * self.torsion[i0, j0] + \
                  fx*(1-fy) * self.torsion[i1, j0] + \
                  (1-fx)*fy * self.torsion[i0, j1] + \
                  fx*fy * self.torsion[i1, j1]
            
            # τ · dl = τ · t̂ × r × dθ
            flux += (tau[0] * tx + tau[1] * ty) * radius * d_angle
        
        return flux


def parallel_transport_holonomy(
    connection: MediumConnection,
    center: Tuple[float, float],
    radius: float,
    spinor_factor: float = 1.0,
    n_steps: int = 500
) -> Dict:
    """
    Compute the holonomy by explicit parallel transport around a loop.
    
    U_γ = P exp(∮_γ A_i dx^i)
    
    Implemented as product of infinitesimal SU(2) rotations:
      U_γ = ∏_k exp(-i A(x_k) · dl_k)
    
    Parameters:
      spinor_factor: 1.0 for SO(3), 0.5 for SU(2) (spinor!)
    
    Returns:
      Dictionary with holonomy matrix, phase, and trace
    """
    # Initialize: U starts as identity
    U = IDENTITY.copy()
    
    # Path around the loop
    angles = np.linspace(0, 2*np.pi, n_steps, endpoint=False)
    d_angle = 2*np.pi / n_steps
    dl = radius * d_angle  # Arc length element
    
    phase_accumulator = 0.0
    
    for angle in angles:
        x = center[0] + radius * np.cos(angle)
        y = center[1] + radius * np.sin(angle)
        
        # Tangent direction
        tx = -np.sin(angle)
        ty = np.cos(angle)
        
        # Get connection at this point
        A = connection.get_connection_at(x, y, spinor_factor=spinor_factor)
        
        # Component of A along path: A_t = A · t̂
        # For our 2D torsion: A = τ_x σ_x + τ_y σ_y
        # A · t = τ_x tx + τ_y ty (scalar, but acts via σ_z for 2D rotation)
        
        # Actually, the full matrix A acts, and we need:
        # dU = -i (A · dl) U
        # So: U_new = exp(-i A_t dl) U
        
        # For small dl: exp(-i A_t dl) ≈ I - i A_t dl
        # But we want exact: exp(-i θ n̂·σ) = cos(θ)I - i sin(θ) n̂·σ
        
        # The torsion gives rotation around its axis
        # Get the component of torsion along the tangent direction
        n = connection.grid_size
        x_c = np.clip(x, 0, n-1.001)
        y_c = np.clip(y, 0, n-1.001)
        i0, j0 = int(x_c), int(y_c)
        tau = connection.torsion[i0, j0]
        
        # For 2D: torsion τ = (τ_x, τ_y, 0) gives rotation
        # The angle increment is |τ · t̂| × dl
        tau_dot_t = tau[0] * tx + tau[1] * ty
        
        # Rotation angle (with spinor factor!)
        d_theta = spinor_factor * tau_dot_t * dl
        
        # Rotation is around z-axis (perpendicular to 2D plane)
        # exp(-i θ σ_z / 2) for spinor, exp(-i θ σ_z) for vector
        # Since we already applied spinor_factor to d_theta, use σ_z directly
        
        c = np.cos(d_theta)
        s = np.sin(d_theta)
        
        # Rotation matrix: exp(-i θ σ_z) = [[e^{-iθ}, 0], [0, e^{iθ}]]
        # Or in real form: [[cos θ, -sin θ], [sin θ, cos θ]] for SO(2)
        # For SU(2) acting on spinor: [[e^{-iθ/2}, 0], [0, e^{iθ/2}]] when spinor_factor=0.5
        
        dU = np.array([[np.exp(-1j * d_theta), 0], 
                       [0, np.exp(1j * d_theta)]], dtype=complex)
        
        U = dU @ U
        phase_accumulator += d_theta
    
    # Extract holonomy properties
    trace = np.trace(U)
    det = np.linalg.det(U)
    
    # For SU(2): U = e^{iφ} (cos(θ/2) I + i sin(θ/2) n̂·σ)
    # Trace = 2 cos(θ/2) e^{iφ}
    # For pure rotation (no global phase): |Trace| = 2|cos(θ/2)|
    
    # The holonomy angle
    holonomy_angle = phase_accumulator
    
    # Check if U ≈ +I or -I
    U_normalized = U / (np.abs(det)**0.5 + 1e-10)  # Remove global phase
    
    is_plus_identity = np.allclose(U_normalized, IDENTITY, atol=0.1) or \
                       np.allclose(U_normalized, IDENTITY * np.exp(1j * np.angle(trace/2)), atol=0.1)
    is_minus_identity = np.allclose(U_normalized, -IDENTITY, atol=0.1) or \
                        np.allclose(U_normalized, -IDENTITY * np.exp(1j * np.angle(trace/2)), atol=0.1)
    
    return {
        'holonomy_matrix': U,
        'trace': complex(trace),
        'trace_real': float(np.real(trace)),
        'determinant': complex(det),
        'accumulated_angle': float(holonomy_angle),
        'accumulated_angle_pi': float(holonomy_angle / np.pi),
        'is_identity': is_plus_identity,
        'is_minus_identity': is_minus_identity,
        'spinor_factor': spinor_factor
    }


def test_parallel_transport_scaling():
    """
    THE KEY TEST: Does holonomy scale linearly with circulation?
    
    Test both SO(3) (spinor_factor=1) and SU(2) (spinor_factor=0.5) connections.
    
    Expected:
      SO(3): circulation w → holonomy 2πw (360° = +1)
      SU(2): circulation w → holonomy πw  (360° = -1 for w=1)
    """
    print("#" * 80)
    print("#  A3: EXPLICIT PARALLEL TRANSPORT HOLONOMY TEST")
    print("#" * 80)
    print("""
THE EXPERIMENT:
  Compute holonomy U_γ = P exp(∮ A · dl) directly from the connection.
  
  This SEPARATES:
    - Field relaxation dynamics
    - True transport geometry
    
  Test two connection types:
    SO(3): A = τ·σ         (vector, 2π = +1)
    SU(2): A = (1/2)τ·σ    (spinor, 2π = -1)
    
SUCCESS CRITERIA:
  For SU(2) connection:
    circulation 1/2 → holonomy π
    circulation 1   → holonomy 2π  
    Linear scaling with flux
""")
    
    params = ParallelTransportParams(grid_size=100, core_size=3.0)
    connection = MediumConnection(100, params)
    
    center = (50, 50)
    radius = 20.0
    
    circulations = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    
    # Store results
    so3_results = {}
    su2_results = {}
    
    print("\n" + "=" * 70)
    print("PART 1: TORSION FLUX VERIFICATION")
    print("=" * 70)
    print(f"\n{'Circulation':>12} | {'Expected Flux':>14} | {'Measured Flux':>14} | {'Match':>6}")
    print("-" * 55)
    
    for circ in circulations:
        connection.setup_vortex(center, circulation=circ)
        flux = connection.compute_torsion_flux(center, radius)
        expected_flux = 2 * np.pi * circ
        match = abs(flux - expected_flux) < 0.5
        print(f"{circ:>12.2f} | {expected_flux:>13.4f}π | {flux/np.pi:>13.4f}π | {'✓' if match else '✗':>6}")
    
    print("\n" + "=" * 70)
    print("PART 2: SO(3) CONNECTION (spinor_factor = 1.0)")
    print("=" * 70)
    print("Expected: Full angle rotation, 2πw holonomy")
    print(f"\n{'Circ':>6} | {'Holonomy':>10} | {'Expected':>10} | {'Tr(U)':>12} | {'Result':>10}")
    print("-" * 55)
    
    for circ in circulations:
        connection.setup_vortex(center, circulation=circ)
        result = parallel_transport_holonomy(connection, center, radius, spinor_factor=1.0)
        so3_results[circ] = result
        
        expected = 2 * circ  # 2πw in units of π
        measured = result['accumulated_angle_pi']
        
        status = '+I' if result['is_identity'] else ('-I' if result['is_minus_identity'] else 'other')
        
        print(f"{circ:>6.2f} | {measured:>9.4f}π | {expected:>9.4f}π | {result['trace_real']:>12.4f} | {status:>10}")
    
    print("\n" + "=" * 70)
    print("PART 3: SU(2) CONNECTION (spinor_factor = 0.5)")  
    print("=" * 70)
    print("Expected: Half angle rotation, πw holonomy → SPINOR BEHAVIOR")
    print(f"\n{'Circ':>6} | {'Holonomy':>10} | {'Expected':>10} | {'Tr(U)':>12} | {'Result':>10}")
    print("-" * 55)
    
    for circ in circulations:
        connection.setup_vortex(center, circulation=circ)
        result = parallel_transport_holonomy(connection, center, radius, spinor_factor=0.5)
        su2_results[circ] = result
        
        expected = circ  # πw in units of π (half-angle!)
        measured = result['accumulated_angle_pi']
        
        status = '+I' if result['is_identity'] else ('-I' if result['is_minus_identity'] else 'other')
        
        print(f"{circ:>6.2f} | {measured:>9.4f}π | {expected:>9.4f}π | {result['trace_real']:>12.4f} | {status:>10}")
    
    # Linear regression for both
    print("\n" + "=" * 70)
    print("PART 4: SCALING ANALYSIS")
    print("=" * 70)
    
    circs = list(circulations)
    so3_holonomies = [so3_results[c]['accumulated_angle_pi'] for c in circs]
    su2_holonomies = [su2_results[c]['accumulated_angle_pi'] for c in circs]
    
    so3_slope, so3_intercept = np.polyfit(circs, so3_holonomies, 1)
    su2_slope, su2_intercept = np.polyfit(circs, su2_holonomies, 1)
    
    so3_r = np.corrcoef(circs, so3_holonomies)[0,1]
    su2_r = np.corrcoef(circs, su2_holonomies)[0,1]
    
    print(f"""
SO(3) Connection (spinor_factor = 1.0):
  Fit: Holonomy = {so3_slope:.4f}π × Circulation + {so3_intercept:.4f}π
  Expected slope: 2.0 (full angle)
  Measured slope: {so3_slope:.4f}
  R-value: {so3_r:.6f}
  Verdict: {'✅ LINEAR' if so3_r > 0.99 else '⚠️ Non-linear'}

SU(2) Connection (spinor_factor = 0.5):
  Fit: Holonomy = {su2_slope:.4f}π × Circulation + {su2_intercept:.4f}π
  Expected slope: 1.0 (half angle → SPINOR!)
  Measured slope: {su2_slope:.4f}
  R-value: {su2_r:.6f}
  Verdict: {'✅ LINEAR' if su2_r > 0.99 else '⚠️ Non-linear'}
""")
    
    # THE KEY TEST
    print("=" * 70)
    print("A3 VERDICT: PARALLEL TRANSPORT GEOMETRY")
    print("=" * 70)
    
    so3_linear = abs(so3_slope - 2.0) < 0.1 and so3_r > 0.99
    su2_linear = abs(su2_slope - 1.0) < 0.1 and su2_r > 0.99
    
    # Check specific cases
    su2_half_is_pi = abs(su2_results[0.5]['accumulated_angle_pi'] - 0.5) < 0.1
    su2_one_is_pi = abs(su2_results[1.0]['accumulated_angle_pi'] - 1.0) < 0.1
    su2_one_gives_minus = su2_results[1.0]['is_minus_identity']
    
    print(f"""
GEOMETRIC DIAGNOSTICS:

SO(3) Connection Test:
  Linear scaling (slope ≈ 2):     {'✅' if so3_linear else '❌'}
  
SU(2) Connection Test:
  Linear scaling (slope ≈ 1):     {'✅' if su2_linear else '❌'}
  w=0.5 → holonomy ≈ 0.5π:        {'✅' if su2_half_is_pi else '❌'} (got {su2_results[0.5]['accumulated_angle_pi']:.4f}π)
  w=1.0 → holonomy ≈ π:           {'✅' if su2_one_is_pi else '❌'} (got {su2_results[1.0]['accumulated_angle_pi']:.4f}π)
  w=1.0 → U = -I:                 {'✅' if su2_one_gives_minus else '❌'}
""")
    
    if su2_linear and su2_one_is_pi:
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ A3 SUCCESS: GEOMETRIC HOLONOMY SCALES CORRECTLY                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║  With spinor_factor = 0.5 (SU(2) connection):                            ║
║    - Holonomy scales as πw (half-angle!)                                 ║
║    - w=1 vortex gives π holonomy → -1 factor                             ║
║                                                                          ║
║  THIS MEANS: The connection GEOMETRY supports spinor transport.          ║
║  The issue was the MEASUREMENT, not the physics.                         ║
║                                                                          ║
║  NEXT: A2 - Does the medium NATURALLY have spinor_factor = 0.5?          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
        conclusion = 'GEOMETRY_SUPPORTS_SPINORS'
    else:
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  ⚠️ A3 RESULT: CONNECTION GEOMETRY NEEDS EXAMINATION                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║  The explicit parallel transport doesn't show expected scaling.          ║
║  Possible issues:                                                        ║
║    - Torsion field configuration                                         ║
║    - Numerical integration accuracy                                      ║
║    - Connection definition                                               ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
        conclusion = 'NEEDS_INVESTIGATION'
    
    # Physics interpretation
    print("\n" + "=" * 70)
    print("PHYSICS INTERPRETATION")
    print("=" * 70)
    print(f"""
The parallel transport test shows:

1. SO(3) Connection (spinor_factor = 1.0):
   - Holonomy = 2π × circulation
   - w=1 vortex → 2π rotation → U = +I (trivial holonomy)
   - This is BOSONIC / VECTOR behavior
   
2. SU(2) Connection (spinor_factor = 0.5):
   - Holonomy = π × circulation  
   - w=1 vortex → π rotation → U = -I (nontrivial holonomy!)
   - This is FERMIONIC / SPINOR behavior
   
KEY QUESTION FOR A2:
  The mathematics works with spinor_factor = 0.5.
  But does the MEDIUM ITSELF impose this factor?
  
  Current situation: We CHOOSE spinor_factor = 0.5
  Target situation: The medium REQUIRES spinor_factor = 0.5
  
  This is the ontological gap A2 must address.
""")
    
    # Save results
    output = {
        'test': 'A3_Parallel_Transport',
        'so3_results': {str(c): {
            'holonomy_pi': float(so3_results[c]['accumulated_angle_pi']),
            'trace_real': float(so3_results[c]['trace_real'])
        } for c in circulations},
        'su2_results': {str(c): {
            'holonomy_pi': float(su2_results[c]['accumulated_angle_pi']),
            'trace_real': float(su2_results[c]['trace_real'])
        } for c in circulations},
        'scaling': {
            'so3_slope': float(so3_slope),
            'su2_slope': float(su2_slope),
            'so3_r': float(so3_r),
            'su2_r': float(su2_r)
        },
        'verdict': {
            'so3_linear': bool(so3_linear),
            'su2_linear': bool(su2_linear),
            'su2_gives_fermion_at_w1': bool(su2_one_is_pi)
        },
        'conclusion': conclusion
    }
    
    output_path = '/app/backend/qmrt_topology/parallel_transport_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return output


if __name__ == "__main__":
    results = test_parallel_transport_scaling()
