"""
QMRT: Level 2 Validation - Berry Phase from Adiabatic Exchange
===============================================================

THE CRITICAL TEST:
  Not just: "antisymmetric is lower energy"
  But: "adiabatic braiding accumulates phase π"

This is different because:
  - Energy selection tells us WHICH state is preferred
  - Berry phase tells us WHAT HAPPENS during exchange

For true fermion topology:
  1. Start with two defects at positions A, B
  2. Adiabatically move defect 1 around defect 2 (full loop)
  3. Configuration returns to original geometry
  4. But wavefunction acquires phase: Ψ → e^{iγ}Ψ
  5. For fermions: γ = π

This requires:
  - Configuration space topology (paths matter)
  - Path-dependent phase accumulation
  - NOT automatic from energy minimization

Reference: Berry phase in quantum mechanics
  γ = i ∮_C ⟨ψ(R)|∇_R|ψ(R)⟩ · dR
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json


@dataclass
class BerryPhaseParams:
    """Parameters for Berry phase calculation."""
    m: float = 1.0
    width: float = 5.0       # Defect width
    lambda_spin: float = 1.0  # Same-spin penalty
    dx: float = 1.0
    
    # Adiabatic transport
    n_steps: int = 200       # Steps around the loop


class BerryPhaseEngine:
    """
    Engine for computing Berry phase from adiabatic transport.
    
    The Berry phase is:
      γ = i ∮ ⟨ψ|∇_R|ψ⟩ · dR
      
    For a closed loop in parameter space (here: defect positions),
    this gives the geometric phase accumulated.
    
    For fermion exchange: γ = π
    """
    
    def __init__(
        self,
        grid_size: int = 64,
        params: Optional[BerryPhaseParams] = None
    ):
        self.grid_size = grid_size
        self.params = params or BerryPhaseParams()
        
        n = grid_size
        x = np.arange(n, dtype=float)
        self.X, self.Y = np.meshgrid(x, x, indexing='ij')
    
    def create_defect_state(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> np.ndarray:
        """
        Create a two-defect state at given positions.
        
        For spinor defects, we use a complex phase that winds around each defect.
        This is the simplest topological defect structure.
        """
        p = self.params
        
        # Distances from each defect
        R1 = np.sqrt((self.X - pos1[0])**2 + (self.Y - pos1[1])**2) + 1e-10
        R2 = np.sqrt((self.X - pos2[0])**2 + (self.Y - pos2[1])**2) + 1e-10
        
        # Angles around each defect
        phi1 = np.arctan2(self.Y - pos1[1], self.X - pos1[0])
        phi2 = np.arctan2(self.Y - pos2[1], self.X - pos2[0])
        
        # Amplitude: localized around each defect
        amp1 = np.exp(-R1**2 / (2 * p.width**2))
        amp2 = np.exp(-R2**2 / (2 * p.width**2))
        
        # For same-spin defects (fermions):
        # The total wavefunction should be antisymmetric
        # We encode this in the RELATIVE phase structure
        
        # Each defect has a vortex-like phase winding
        # For fermion exchange, the relative phase matters
        
        # Simple model: amplitude × phase factor
        # The phase encodes the defect's "spin" orientation
        psi = (amp1 * np.exp(1j * phi1 / 2) + 
               amp2 * np.exp(1j * phi2 / 2))
        
        # Normalize
        norm = np.sqrt(np.sum(np.abs(psi)**2) * p.dx**2)
        psi /= norm
        
        return psi
    
    def create_spinor_defect_state(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create a two-spinor-defect state.
        
        Each defect is a localized spinor excitation.
        For same-spin defects, the exchange should give -1.
        """
        p = self.params
        
        R1 = np.sqrt((self.X - pos1[0])**2 + (self.Y - pos1[1])**2) + 1e-10
        R2 = np.sqrt((self.X - pos2[0])**2 + (self.Y - pos2[1])**2) + 1e-10
        
        # Spinor profiles (both spin-up)
        psi1_up = np.exp(-R1**2 / (2 * p.width**2))
        psi2_up = np.exp(-R2**2 / (2 * p.width**2))
        
        # Normalize each
        psi1_up /= np.sqrt(np.sum(np.abs(psi1_up)**2) * p.dx**2)
        psi2_up /= np.sqrt(np.sum(np.abs(psi2_up)**2) * p.dx**2)
        
        # Down components (zero for spin-up defects)
        psi1_down = np.zeros_like(psi1_up)
        psi2_down = np.zeros_like(psi2_up)
        
        return (psi1_up, psi1_down), (psi2_up, psi2_down)
    
    def compute_berry_connection(
        self,
        psi_R: np.ndarray,
        psi_R_plus_dR: np.ndarray,
        dR: float
    ) -> complex:
        """
        Compute Berry connection A = i⟨ψ|∇_R|ψ⟩ · dR̂
        
        Numerically: A ≈ i⟨ψ(R)|ψ(R+dR) - ψ(R)⟩/dR
        
        The imaginary part of ⟨ψ(R)|ψ(R+dR)⟩ gives the phase change.
        """
        overlap = np.sum(np.conj(psi_R) * psi_R_plus_dR) * self.params.dx**2
        
        # The connection is related to the phase of the overlap
        # A·dR ≈ Im[log(⟨ψ|ψ'⟩)] = arg(⟨ψ|ψ'⟩)
        
        return overlap
    
    def compute_berry_phase_loop(
        self,
        center: Tuple[float, float],
        fixed_defect: Tuple[float, float],
        radius: float
    ) -> Dict:
        """
        Compute Berry phase for moving one defect around another.
        
        Setup:
          - Defect 2 fixed at 'fixed_defect'
          - Defect 1 moves in a circle around 'center' with given 'radius'
          
        Returns accumulated phase after one complete loop.
        """
        p = self.params
        n_steps = p.n_steps
        
        # Initial angle
        theta_0 = 0.0
        
        # Record overlaps around the loop
        overlaps = []
        phases = []
        
        # Initial state
        pos1_initial = (center[0] + radius, center[1])
        psi_prev = self.create_defect_state(pos1_initial, fixed_defect)
        
        accumulated_phase = 0.0
        
        for i in range(n_steps):
            # Move defect 1 around the loop
            theta = 2 * np.pi * (i + 1) / n_steps
            pos1 = (center[0] + radius * np.cos(theta),
                   center[1] + radius * np.sin(theta))
            
            # Create state at new position
            psi_current = self.create_defect_state(pos1, fixed_defect)
            
            # Compute overlap with previous state
            overlap = np.sum(np.conj(psi_prev) * psi_current) * p.dx**2
            overlaps.append(overlap)
            
            # Extract phase increment
            if np.abs(overlap) > 1e-10:
                phase_increment = np.angle(overlap)
                # Ensure continuity (unwrap)
                if len(phases) > 0:
                    while phase_increment - phases[-1] > np.pi:
                        phase_increment -= 2 * np.pi
                    while phase_increment - phases[-1] < -np.pi:
                        phase_increment += 2 * np.pi
            else:
                phase_increment = 0.0
            
            phases.append(phase_increment)
            accumulated_phase += phase_increment
            
            psi_prev = psi_current.copy()
        
        # Also compute direct overlap between initial and final
        psi_final = psi_current
        psi_initial = self.create_defect_state(pos1_initial, fixed_defect)
        final_overlap = np.sum(np.conj(psi_initial) * psi_final) * p.dx**2
        
        return {
            'accumulated_phase': float(accumulated_phase),
            'accumulated_phase_pi': float(accumulated_phase / np.pi),
            'final_overlap_magnitude': float(np.abs(final_overlap)),
            'final_overlap_phase': float(np.angle(final_overlap)),
            'n_steps': n_steps,
            'radius': radius
        }
    
    def compute_berry_phase_exchange(
        self,
        pos1_start: Tuple[float, float],
        pos2_start: Tuple[float, float]
    ) -> Dict:
        """
        Compute Berry phase for EXCHANGE: move defect 1 around defect 2
        such that they swap positions (half-exchange) or full loop.
        
        For fermions:
          Half exchange (swap): γ = π/2 or π depending on convention
          Full exchange (back to start): γ = π
        """
        p = self.params
        n_steps = p.n_steps
        
        # Center between the two defects
        center = ((pos1_start[0] + pos2_start[0]) / 2,
                  (pos1_start[1] + pos2_start[1]) / 2)
        
        # Radius of circular path
        radius = np.sqrt((pos1_start[0] - center[0])**2 + 
                        (pos1_start[1] - center[1])**2)
        
        # Initial angle of defect 1
        theta_0 = np.arctan2(pos1_start[1] - center[1],
                            pos1_start[0] - center[0])
        
        # Record states and phases
        psi_prev = self.create_defect_state(pos1_start, pos2_start)
        
        phase_history = [0.0]
        overlap_history = [1.0 + 0j]
        
        # Move defect 1 in a semicircle (exchange)
        for i in range(n_steps):
            theta = theta_0 + np.pi * (i + 1) / n_steps  # Half circle for exchange
            
            pos1_new = (center[0] + radius * np.cos(theta),
                       center[1] + radius * np.sin(theta))
            
            psi_current = self.create_defect_state(pos1_new, pos2_start)
            
            overlap = np.sum(np.conj(psi_prev) * psi_current) * p.dx**2
            overlap_history.append(overlap)
            
            if np.abs(overlap) > 1e-10:
                phase_step = np.angle(overlap)
            else:
                phase_step = 0.0
            
            phase_history.append(phase_history[-1] + phase_step)
            psi_prev = psi_current.copy()
        
        # After half circle, defects have exchanged positions
        # (pos1 is now where pos2 was, approximately)
        
        total_phase = phase_history[-1]
        
        return {
            'total_phase': float(total_phase),
            'total_phase_pi': float(total_phase / np.pi),
            'phase_history': [float(p) for p in phase_history[::10]],  # Sample
            'type': 'half_exchange',
            'expected_fermion': 'π/2 or π depending on convention'
        }


def test_berry_phase_full_loop():
    """
    Test: Berry phase for moving defect around a fixed point.
    
    This tests the basic Berry phase calculation.
    """
    print("\n" + "=" * 80)
    print("TEST 1: BERRY PHASE FOR CIRCULAR MOTION")
    print("=" * 80)
    print("""
Moving defect 1 in a complete circle around a fixed point.
Defect 2 is stationary.

For topological defects:
  - The Berry phase depends on the winding number
  - For spinor defects: γ = π per winding

Testing at various radii...
""")
    
    engine = BerryPhaseEngine(grid_size=64)
    
    center = (32, 32)
    fixed_defect = (32, 32)  # Defect 2 at center
    
    radii = [10, 15, 20, 25]
    
    print(f"\n{'Radius':>8} | {'Accumulated Phase':>18} | {'Phase/π':>10}")
    print("-" * 45)
    
    results = []
    
    for r in radii:
        result = engine.compute_berry_phase_loop(center, fixed_defect, r)
        
        print(f"{r:>8} | {result['accumulated_phase']:>18.4f} | {result['accumulated_phase_pi']:>10.4f}")
        results.append(result)
    
    print("\n" + "-" * 40)
    
    # Check if phase is approximately π
    phases_pi = [r['accumulated_phase_pi'] for r in results]
    mean_phase_pi = np.mean(phases_pi)
    
    print(f"Mean phase/π across radii: {mean_phase_pi:.4f}")
    
    if np.abs(mean_phase_pi - 1.0) < 0.3:
        print("✅ Berry phase ≈ π (fermion signature)")
    elif np.abs(mean_phase_pi) < 0.3:
        print("⚠️ Berry phase ≈ 0 (boson-like)")
    else:
        print(f"⚠️ Berry phase = {mean_phase_pi:.2f}π (neither fermion nor boson)")
    
    return results


def test_berry_phase_exchange():
    """
    THE CRITICAL TEST: Berry phase for particle EXCHANGE.
    
    Move defect 1 around defect 2 such that they swap positions.
    For fermions: this should give phase π.
    """
    print("\n" + "=" * 80)
    print("TEST 2: BERRY PHASE FOR PARTICLE EXCHANGE")
    print("=" * 80)
    print("""
THE CRITICAL LEVEL-2 TEST:

Setup:
  - Two defects at positions A and B
  - Move defect 1 in a semicircle around the midpoint
  - After semicircle: defect 1 is at B, defect 2 still at A
  - This is a PHYSICAL EXCHANGE

For fermions:
  - The wavefunction should acquire phase e^{iπ} = -1
  - This is the TOPOLOGICAL signature, not just energetic preference

Testing exchange at various separations...
""")
    
    engine = BerryPhaseEngine(grid_size=64, params=BerryPhaseParams(n_steps=200))
    
    separations = [20, 25, 30, 35]
    
    print(f"\n{'Separation':>12} | {'Exchange Phase':>15} | {'Phase/π':>10}")
    print("-" * 45)
    
    results = []
    
    for sep in separations:
        pos1 = (32 - sep/2, 32)
        pos2 = (32 + sep/2, 32)
        
        result = engine.compute_berry_phase_exchange(pos1, pos2)
        
        print(f"{sep:>12} | {result['total_phase']:>15.4f} | {result['total_phase_pi']:>10.4f}")
        results.append(result)
    
    print("\n" + "-" * 40)
    
    # Analyze
    phases_pi = [r['total_phase_pi'] for r in results]
    mean_phase = np.mean(phases_pi)
    
    print(f"Mean exchange phase/π: {mean_phase:.4f}")
    
    # For half-exchange (semicircle), the phase depends on the model
    # Full exchange (complete circle around other particle) should give π
    
    print("""
INTERPRETATION:

The Berry phase from adiabatic exchange depends on:
1. The topological structure of the defects
2. The path taken in configuration space
3. The gauge structure of the wavefunction

For our simple Gaussian defect model:
- The phase comes from the position-dependent phase factors
- Half-exchange (semicircle) may give π/2 or other values
- Full exchange (particle around another) should approach π for true fermions
""")
    
    return results


def test_berry_phase_with_antisymmetric_structure():
    """
    Test Berry phase when we explicitly use antisymmetric wavefunctions.
    
    The key insight: for antisymmetric states, exchange gives -1 automatically,
    but the Berry phase should ALSO be π for consistency.
    """
    print("\n" + "=" * 80)
    print("TEST 3: BERRY PHASE WITH EXPLICIT ANTISYMMETRIC STRUCTURE")
    print("=" * 80)
    print("""
Using explicitly antisymmetric two-particle wavefunctions:
  Ψ(r₁,r₂) = φ(r₁)χ(r₂) - φ(r₂)χ(r₁)

When we exchange particle positions:
  Ψ(r₂,r₁) = φ(r₂)χ(r₁) - φ(r₁)χ(r₂) = -Ψ(r₁,r₂)

This is ALGEBRAICALLY -1.

But what is the BERRY PHASE during adiabatic transport?
This should ALSO be π for physical consistency.
""")
    
    # For this test, we need to track the antisymmetric structure
    # during adiabatic motion
    
    n = 64
    dx = 1.0
    width = 5.0
    
    x = np.arange(n, dtype=float)
    X, Y = np.meshgrid(x, x, indexing='ij')
    
    def make_antisym_state(pos1, pos2):
        """Create antisymmetric two-particle wavefunction."""
        R1 = np.sqrt((X - pos1[0])**2 + (Y - pos1[1])**2)
        R2 = np.sqrt((X - pos2[0])**2 + (Y - pos2[1])**2)
        
        phi = np.exp(-R1**2 / (2 * width**2))
        chi = np.exp(-R2**2 / (2 * width**2))
        
        # Antisymmetric combination
        # In single-particle picture: represent as difference
        psi = phi - chi
        
        norm = np.sqrt(np.sum(np.abs(psi)**2) * dx**2)
        if norm > 1e-10:
            psi /= norm
        
        return psi
    
    # Initial configuration
    pos1_start = (22, 32)
    pos2_start = (42, 32)
    
    psi_initial = make_antisym_state(pos1_start, pos2_start)
    
    # Move particle 1 in semicircle around midpoint
    center = (32, 32)
    radius = 10
    theta_0 = np.pi  # Start at left
    
    n_steps = 100
    
    psi_prev = psi_initial.copy()
    accumulated_phase = 0.0
    
    for i in range(n_steps):
        theta = theta_0 + np.pi * (i + 1) / n_steps  # Half circle
        
        pos1_new = (center[0] + radius * np.cos(theta),
                   center[1] + radius * np.sin(theta))
        
        psi_new = make_antisym_state(pos1_new, pos2_start)
        
        overlap = np.sum(np.conj(psi_prev) * psi_new) * dx**2
        
        if np.abs(overlap) > 1e-10:
            phase_step = np.angle(overlap)
            accumulated_phase += phase_step
        
        psi_prev = psi_new.copy()
    
    # After half circle, check final state
    psi_final = psi_prev
    
    # Compare with exchanged initial state
    psi_exchanged = make_antisym_state(pos2_start, pos1_start)
    
    overlap_with_exchanged = np.sum(np.conj(psi_exchanged) * psi_final) * dx**2
    
    print(f"Accumulated Berry phase: {accumulated_phase:.4f} rad = {accumulated_phase/np.pi:.4f}π")
    print(f"Overlap |⟨Ψ_exchanged|Ψ_final⟩|: {np.abs(overlap_with_exchanged):.4f}")
    print(f"Phase of overlap: {np.angle(overlap_with_exchanged):.4f} rad")
    
    # For true fermion behavior:
    # 1. Accumulated Berry phase should be ≈ π/2 for half exchange
    # 2. Overlap with exchanged state should be ≈ 1 (same state up to phase)
    
    print("\n" + "-" * 40)
    print("ANALYSIS:")
    print(f"  Berry phase from transport: {accumulated_phase/np.pi:.2f}π")
    print(f"  Algebraic exchange factor: -1 (by construction)")
    
    # The consistency check
    is_consistent = np.abs(overlap_with_exchanged) > 0.9
    
    if is_consistent:
        print("\n✅ Berry phase transport and algebraic exchange are CONSISTENT")
    else:
        print("\n⚠️ Transport gives different state than algebraic exchange")
        print("   This indicates the model needs refinement")
    
    return accumulated_phase


def test_robustness():
    """
    Test robustness of Berry phase under:
    - Different grid sizes
    - Different defect widths
    - Different paths
    """
    print("\n" + "=" * 80)
    print("TEST 4: ROBUSTNESS OF BERRY PHASE")
    print("=" * 80)
    print("""
Testing if Berry phase is robust (not numerical artifact).

A TRUE topological result should be:
- Independent of grid resolution
- Independent of path details
- Independent of defect shape (within reason)
""")
    
    results = []
    
    # Test 1: Grid size dependence
    print("\n--- Grid Size Dependence ---")
    grid_sizes = [32, 64, 96, 128]
    
    for gs in grid_sizes:
        engine = BerryPhaseEngine(grid_size=gs, params=BerryPhaseParams(n_steps=100))
        result = engine.compute_berry_phase_loop((gs/2, gs/2), (gs/2, gs/2), gs/4)
        print(f"Grid {gs}: phase/π = {result['accumulated_phase_pi']:.4f}")
        results.append(('grid_size', gs, result['accumulated_phase_pi']))
    
    # Test 2: Path steps dependence
    print("\n--- Path Steps Dependence ---")
    step_counts = [50, 100, 200, 400]
    
    for ns in step_counts:
        params = BerryPhaseParams(n_steps=ns)
        engine = BerryPhaseEngine(grid_size=64, params=params)
        result = engine.compute_berry_phase_loop((32, 32), (32, 32), 15)
        print(f"Steps {ns}: phase/π = {result['accumulated_phase_pi']:.4f}")
        results.append(('n_steps', ns, result['accumulated_phase_pi']))
    
    # Test 3: Defect width dependence
    print("\n--- Defect Width Dependence ---")
    widths = [3.0, 5.0, 7.0, 10.0]
    
    for w in widths:
        params = BerryPhaseParams(width=w, n_steps=100)
        engine = BerryPhaseEngine(grid_size=64, params=params)
        result = engine.compute_berry_phase_loop((32, 32), (32, 32), 15)
        print(f"Width {w}: phase/π = {result['accumulated_phase_pi']:.4f}")
        results.append(('width', w, result['accumulated_phase_pi']))
    
    # Analyze
    print("\n" + "-" * 40)
    
    phases = [r[2] for r in results]
    mean = np.mean(phases)
    std = np.std(phases)
    
    print(f"Mean phase/π: {mean:.4f} ± {std:.4f}")
    
    is_robust = std < 0.2
    
    if is_robust:
        print("✅ Berry phase is ROBUST (not numerical artifact)")
    else:
        print("⚠️ Berry phase has significant variation")
        print("   May depend on model details, not pure topology")
    
    return results


def run_berry_phase_tests():
    """Run complete Berry phase test suite."""
    print("#" * 80)
    print("#  QMRT: BERRY PHASE FROM ADIABATIC EXCHANGE")
    print("#" * 80)
    print("""
LEVEL 2 VALIDATION:

Not just "antisymmetric is lower energy" (Level 1)
But "adiabatic braiding gives phase π" (Level 2)

This is the TOPOLOGICAL signature of fermions.
""")
    
    results = {}
    
    results['full_loop'] = test_berry_phase_full_loop()
    results['exchange'] = test_berry_phase_exchange()
    results['antisymmetric'] = test_berry_phase_with_antisymmetric_structure()
    results['robustness'] = test_robustness()
    
    # Summary
    print("\n" + "=" * 80)
    print("BERRY PHASE SUMMARY")
    print("=" * 80)
    
    print("""
RESULTS:

Level 1 (previously shown): Antisymmetric states have lower energy ✅
Level 2 (this test):        Berry phase from adiabatic transport

The Berry phase tests show:
""")
    
    # Extract key findings
    if results['full_loop']:
        mean_loop = np.mean([r['accumulated_phase_pi'] for r in results['full_loop']])
        print(f"  Full loop around defect:    γ/π ≈ {mean_loop:.2f}")
    
    if results['exchange']:
        mean_exchange = np.mean([r['total_phase_pi'] for r in results['exchange']])
        print(f"  Half-exchange (semicircle): γ/π ≈ {mean_exchange:.2f}")
    
    print(f"  Antisymmetric transport:    γ/π ≈ {results['antisymmetric']/np.pi:.2f}")
    
    print("""
INTERPRETATION:

The Berry phase depends on:
1. Defect structure (how phase winds around each defect)
2. Path topology (whether path encloses other defects)
3. Gauge choice (how we define the wavefunction phase)

For EXACT fermion behavior (γ = π):
- Need defects with half-integer topological charge
- The "spin" structure must be properly encoded
- Our simple Gaussian model is a first approximation

The connection to Level 1:
- Energy penalty FORCES antisymmetric ground state
- Antisymmetric state has BUILT-IN exchange sign
- Berry phase should be CONSISTENT with this
""")
    
    # Save results
    output = {
        'test_suite': 'Berry Phase Level 2',
        'full_loop_mean_phase_pi': float(mean_loop) if results['full_loop'] else None,
        'exchange_mean_phase_pi': float(mean_exchange) if results['exchange'] else None,
        'antisymmetric_phase_pi': float(results['antisymmetric'] / np.pi),
        'conclusion': 'Berry phase tests provide geometric insight but require refined defect model for exact π'
    }
    
    output_path = '/app/backend/qmrt_topology/berry_phase_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    results = run_berry_phase_tests()
