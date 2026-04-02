"""
QMRT: ROTATION TEST - THE CRITICAL EXPERIMENT
==============================================

THE KEY QUESTION:
  Is the −1 holonomy from LOOP TOPOLOGY or TRUE ROTATIONAL GEOMETRY?

  Loop topology → lattice effect (what we have now)
  Rotational geometry → fundamental spinor behavior (what real fermions have)

THE TEST:
  1. Take n=6 loop structure with alternating signs
  2. Embed in continuous 2D space
  3. PHYSICALLY ROTATE the entire structure by 360° (2π)
  4. Measure global phase observable Ψ

EXPECTED OUTCOMES:
  After 2π rotation:
    Ψ → +1 : Classical object (no spinor behavior)
    Ψ → -1 : SPINOR-LIKE behavior!
    
  After 4π rotation:
    Ψ → +1 : True double-cover (spinor)
    Ψ ≠ +1 : Not true spinor

GLOBAL PHASE OBSERVABLE:
  Ψ = Σᵢ e^(iθᵢ) · sᵢ

  Where:
    θᵢ = phase at junction i
    sᵢ = junction sign (+1 or -1)

THIS IS THE EXPERIMENT THAT DETERMINES:
  Path A: Clever lattice topological model
  Path B: Geometry-driven spinor emergence system
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import json


@dataclass
class RotatableJunction:
    """Junction with position that can be rotated."""
    id: int
    position: np.ndarray  # (x, y) in 2D space
    theta: float = 0.0    # Phase
    sign: int = 1         # Junction sign (+1 or -1)
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=float)


class RotatableNetwork:
    """
    Network that can be PHYSICALLY rotated in space.
    
    Rotation affects:
      - Junction positions (geometry)
      - Coupling directions (interaction structure)
      - NOT just index relabeling!
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        
        self.junctions: Dict[int, RotatableJunction] = {}
        self.edges: List[Tuple[int, int]] = []
        
        self.next_id = 0
        
        # Phase physics
        self.phase_per_junction = -np.pi / 6  # -30 degrees
        self.coupling = 1.0
        
        # Reference direction (for tracking rotation)
        self.reference_angle = 0.0
    
    def add_junction(self, position: np.ndarray, theta: float = 0.0,
                     sign: int = 1) -> int:
        jid = self.next_id
        self.junctions[jid] = RotatableJunction(jid, position, theta, sign)
        self.next_id += 1
        return jid
    
    def add_edge(self, i: int, j: int):
        self.edges.append((i, j))
    
    def create_hexagonal_loop(self, radius: float = 1.0,
                               alternating_signs: bool = True) -> List[int]:
        """Create n=6 loop with proper geometry."""
        jids = []
        
        for i in range(6):
            angle = 2 * np.pi * i / 6
            pos = radius * np.array([np.cos(angle), np.sin(angle)])
            
            # Initialize phase with geometric winding
            theta = i * self.phase_per_junction
            
            # Alternating signs
            sign = 1 if (i % 2 == 0) else -1
            if not alternating_signs:
                sign = 1
            
            jid = self.add_junction(pos, theta, sign)
            jids.append(jid)
        
        # Connect in loop
        for i in range(6):
            self.add_edge(jids[i], jids[(i+1) % 6])
        
        return jids
    
    # =========================================================================
    # PHYSICAL ROTATION
    # =========================================================================
    
    def rotate_structure(self, angle: float):
        """
        PHYSICALLY rotate the entire structure by angle (radians).
        
        This rotates:
          - All junction positions
          - Updates coupling directions accordingly
        
        This is NOT just index relabeling!
        """
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        rotation_matrix = np.array([
            [cos_a, -sin_a],
            [sin_a, cos_a]
        ])
        
        for jid, junction in self.junctions.items():
            # Rotate position
            junction.position = rotation_matrix @ junction.position
        
        # Update reference angle
        self.reference_angle += angle
    
    def get_coupling_direction(self, i: int, j: int) -> float:
        """Get angle from junction i to junction j."""
        pos_i = self.junctions[i].position
        pos_j = self.junctions[j].position
        
        delta = pos_j - pos_i
        return np.arctan2(delta[1], delta[0])
    
    # =========================================================================
    # GLOBAL PHASE OBSERVABLE
    # =========================================================================
    
    def compute_psi(self) -> complex:
        """
        Compute global phase observable:
        
        Ψ = Σᵢ e^(iθᵢ) · sᵢ
        
        This combines phase and sign structure.
        """
        psi = 0.0 + 0.0j
        
        for jid, junction in self.junctions.items():
            contribution = np.exp(1j * junction.theta) * junction.sign
            psi += contribution
        
        return psi
    
    def compute_normalized_psi(self) -> complex:
        """Normalized version: Ψ / |Ψ|"""
        psi = self.compute_psi()
        norm = abs(psi)
        if norm < 1e-10:
            return 0.0 + 0.0j
        return psi / norm
    
    def compute_holonomy_observable(self) -> complex:
        """
        Alternative observable: product around the loop.
        
        H = Π_edges e^(iΔθ) × Π_junctions s
        """
        # Phase product
        phase_product = 1.0 + 0.0j
        
        for i, j in self.edges:
            theta_i = self.junctions[i].theta
            theta_j = self.junctions[j].theta
            delta = theta_j - theta_i
            phase_product *= np.exp(1j * delta)
        
        # Sign product
        sign_product = 1
        for jid, junction in self.junctions.items():
            sign_product *= junction.sign
        
        return phase_product * sign_product
    
    # =========================================================================
    # ROTATION-INDUCED PHASE EVOLUTION
    # =========================================================================
    
    def evolve_phases_under_rotation(self, rotation_step: float):
        """
        As the structure rotates, phases evolve.
        
        KEY PHYSICS:
        When the geometry rotates, the coupling directions change.
        This affects the effective phase transport.
        
        In a spinor field:
          - 360° rotation induces phase change
          - The amount depends on spin
        
        We simulate this by having phases respond to geometric rotation.
        """
        # Each junction's phase couples to its neighbors
        # The coupling depends on the RELATIVE direction
        
        for jid, junction in self.junctions.items():
            # Find neighbors
            neighbors = []
            for i, j in self.edges:
                if i == jid:
                    neighbors.append(j)
                elif j == jid:
                    neighbors.append(i)
            
            # Compute coupling force from rotation
            # As structure rotates, phase alignment changes
            phase_adjustment = 0.0
            
            for nid in neighbors:
                # Direction to neighbor
                direction = self.get_coupling_direction(jid, nid)
                
                # The rotation affects effective coupling
                # This creates geometric phase
                phase_adjustment += self.coupling * rotation_step * np.sin(direction)
            
            # Apply adjustment (scaled)
            junction.theta += phase_adjustment * 0.1
    
    # =========================================================================
    # THE ROTATION TEST
    # =========================================================================
    
    def perform_rotation_test(self, total_angle: float, n_steps: int = 100) -> Dict:
        """
        Perform rotation and track observables.
        
        Args:
            total_angle: Total angle to rotate (e.g., 2π for 360°)
            n_steps: Number of discrete rotation steps
        """
        step_angle = total_angle / n_steps
        
        # Initial state
        psi_initial = self.compute_psi()
        H_initial = self.compute_holonomy_observable()
        
        history = {
            'angle': [0.0],
            'psi_real': [psi_initial.real],
            'psi_imag': [psi_initial.imag],
            'psi_norm': [abs(psi_initial)],
            'H_real': [H_initial.real],
            'H_imag': [H_initial.imag],
            'reference': [self.reference_angle]
        }
        
        # Perform rotation
        for step in range(n_steps):
            # Rotate structure
            self.rotate_structure(step_angle)
            
            # Evolve phases due to rotation
            self.evolve_phases_under_rotation(step_angle)
            
            # Measure
            psi = self.compute_psi()
            H = self.compute_holonomy_observable()
            
            history['angle'].append((step + 1) * step_angle)
            history['psi_real'].append(psi.real)
            history['psi_imag'].append(psi.imag)
            history['psi_norm'].append(abs(psi))
            history['H_real'].append(H.real)
            history['H_imag'].append(H.imag)
            history['reference'].append(self.reference_angle)
        
        # Final state
        psi_final = self.compute_psi()
        H_final = self.compute_holonomy_observable()
        
        # Compute change
        psi_ratio = psi_final / (psi_initial + 1e-10)
        H_ratio = H_final / (H_initial + 1e-10)
        
        return {
            'total_angle_deg': np.degrees(total_angle),
            'psi_initial': {'real': psi_initial.real, 'imag': psi_initial.imag},
            'psi_final': {'real': psi_final.real, 'imag': psi_final.imag},
            'psi_ratio': {'real': psi_ratio.real, 'imag': psi_ratio.imag},
            'H_initial': {'real': H_initial.real, 'imag': H_initial.imag},
            'H_final': {'real': H_final.real, 'imag': H_final.imag},
            'H_ratio': {'real': H_ratio.real, 'imag': H_ratio.imag},
            'history': history
        }


# =============================================================================
# ROTATION TEST SUITE
# =============================================================================

class SpinorRotationTest:
    """Test for spinor behavior under rotation."""
    
    def __init__(self):
        self.results = {}
    
    def test_2pi_rotation(self) -> Dict:
        """
        TEST 1: 360° (2π) rotation.
        
        Classical object: returns to same state (+1)
        Spinor: flips sign (-1)
        """
        print("=" * 70)
        print("TEST 1: 2π (360°) ROTATION")
        print("=" * 70)
        print("""
If spinor-like:
  Ψ(2π) = -Ψ(0)  [sign flip]
  H(2π) = -H(0)  [holonomy flips]

If classical:
  Ψ(2π) = +Ψ(0)  [returns to same]
  H(2π) = +H(0)
""")
        
        network = RotatableNetwork(seed=42)
        jids = network.create_hexagonal_loop(alternating_signs=True)
        
        result = network.perform_rotation_test(2 * np.pi, n_steps=100)
        
        # Analyze
        psi_ratio = complex(result['psi_ratio']['real'], result['psi_ratio']['imag'])
        H_ratio = complex(result['H_ratio']['real'], result['H_ratio']['imag'])
        
        print(f"\nInitial Ψ: {result['psi_initial']['real']:.3f} + {result['psi_initial']['imag']:.3f}i")
        print(f"Final Ψ:   {result['psi_final']['real']:.3f} + {result['psi_final']['imag']:.3f}i")
        print(f"Ratio:     {psi_ratio.real:.3f} + {psi_ratio.imag:.3f}i")
        
        print(f"\nInitial H: {result['H_initial']['real']:.3f} + {result['H_initial']['imag']:.3f}i")
        print(f"Final H:   {result['H_final']['real']:.3f} + {result['H_final']['imag']:.3f}i")
        print(f"Ratio:     {H_ratio.real:.3f} + {H_ratio.imag:.3f}i")
        
        # Check for spinor behavior
        is_spinor_psi = np.isclose(psi_ratio, -1, atol=0.2)
        is_spinor_H = np.isclose(H_ratio, -1, atol=0.2)
        is_classical = np.isclose(psi_ratio, 1, atol=0.2)
        
        print(f"\nΨ shows spinor behavior (ratio ≈ -1): {is_spinor_psi}")
        print(f"H shows spinor behavior (ratio ≈ -1): {is_spinor_H}")
        print(f"Classical behavior (ratio ≈ +1):       {is_classical}")
        
        return {
            'angle': '2π',
            'psi_ratio': psi_ratio,
            'H_ratio': H_ratio,
            'is_spinor': is_spinor_psi or is_spinor_H,
            'is_classical': is_classical
        }
    
    def test_4pi_rotation(self) -> Dict:
        """
        TEST 2: 720° (4π) rotation.
        
        True spinor: returns to original (+1)
        Not spinor: something else
        """
        print("\n" + "=" * 70)
        print("TEST 2: 4π (720°) ROTATION")
        print("=" * 70)
        print("""
If true spinor:
  Ψ(4π) = +Ψ(0)  [returns after double rotation]
  
This confirms double-cover: need 720° to return.
""")
        
        network = RotatableNetwork(seed=42)
        jids = network.create_hexagonal_loop(alternating_signs=True)
        
        result = network.perform_rotation_test(4 * np.pi, n_steps=200)
        
        psi_ratio = complex(result['psi_ratio']['real'], result['psi_ratio']['imag'])
        H_ratio = complex(result['H_ratio']['real'], result['H_ratio']['imag'])
        
        print(f"\nΨ ratio after 4π: {psi_ratio.real:.3f} + {psi_ratio.imag:.3f}i")
        print(f"H ratio after 4π: {H_ratio.real:.3f} + {H_ratio.imag:.3f}i")
        
        returns_after_4pi = np.isclose(psi_ratio, 1, atol=0.2)
        
        print(f"\nReturns to +1 after 4π: {returns_after_4pi}")
        
        return {
            'angle': '4π',
            'psi_ratio': psi_ratio,
            'H_ratio': H_ratio,
            'returns_to_identity': returns_after_4pi
        }
    
    def test_incremental_rotation(self) -> Dict:
        """
        TEST 3: Track Ψ continuously during rotation.
        
        This shows the full trajectory.
        """
        print("\n" + "=" * 70)
        print("TEST 3: CONTINUOUS ROTATION TRAJECTORY")
        print("=" * 70)
        
        network = RotatableNetwork(seed=42)
        jids = network.create_hexagonal_loop(alternating_signs=True)
        
        result = network.perform_rotation_test(4 * np.pi, n_steps=200)
        
        history = result['history']
        
        # Print key points
        print(f"\n{'Angle':>10} | {'Ψ real':>10} | {'Ψ imag':>10} | {'|Ψ|':>10}")
        print("-" * 50)
        
        for i in range(0, len(history['angle']), 25):
            angle_deg = np.degrees(history['angle'][i])
            psi_r = history['psi_real'][i]
            psi_i = history['psi_imag'][i]
            psi_n = history['psi_norm'][i]
            
            print(f"{angle_deg:>9.0f}° | {psi_r:>10.3f} | {psi_i:>10.3f} | {psi_n:>10.3f}")
        
        return result
    
    def test_sign_structure_dependence(self) -> Dict:
        """
        TEST 4: Compare alternating vs uniform signs.
        
        The sign structure should affect spinor behavior.
        """
        print("\n" + "=" * 70)
        print("TEST 4: SIGN STRUCTURE DEPENDENCE")
        print("=" * 70)
        
        results = {}
        
        for alt_signs, name in [(True, "Alternating"), (False, "Uniform")]:
            network = RotatableNetwork(seed=42)
            jids = network.create_hexagonal_loop(alternating_signs=alt_signs)
            
            # 2π rotation
            result = network.perform_rotation_test(2 * np.pi, n_steps=100)
            
            psi_ratio = complex(result['psi_ratio']['real'], result['psi_ratio']['imag'])
            
            print(f"\n{name} signs:")
            print(f"  Ψ ratio after 2π: {psi_ratio.real:.3f} + {psi_ratio.imag:.3f}i")
            print(f"  Spinor-like: {np.isclose(psi_ratio, -1, atol=0.2)}")
            
            results[name] = {
                'psi_ratio': psi_ratio,
                'is_spinor': np.isclose(psi_ratio, -1, atol=0.2)
            }
        
        return results
    
    def test_geometric_phase_accumulation(self) -> Dict:
        """
        TEST 5: Does rotation accumulate geometric phase?
        
        This tests if the rotation is truly affecting the physics.
        """
        print("\n" + "=" * 70)
        print("TEST 5: GEOMETRIC PHASE ACCUMULATION")
        print("=" * 70)
        print("""
Tracking total phase around the loop during rotation.
If geometric phase accumulates, we should see drift.
""")
        
        network = RotatableNetwork(seed=42)
        jids = network.create_hexagonal_loop(alternating_signs=True)
        
        # Track loop phase at different rotation angles
        phases = []
        angles = np.linspace(0, 4*np.pi, 100)
        
        for angle in angles:
            # Reset and rotate
            network2 = RotatableNetwork(seed=42)
            jids2 = network2.create_hexagonal_loop(alternating_signs=True)
            network2.rotate_structure(angle)
            
            # Measure loop phase (sum of phase differences)
            total_phase = 0.0
            for i in range(6):
                j = (i + 1) % 6
                theta_i = network2.junctions[jids2[i]].theta
                theta_j = network2.junctions[jids2[j]].theta
                total_phase += theta_j - theta_i
            
            phases.append(total_phase)
        
        # Analyze
        print(f"\nLoop phase at 0°:   {np.degrees(phases[0]):.1f}°")
        print(f"Loop phase at 360°: {np.degrees(phases[25]):.1f}°")
        print(f"Loop phase at 720°: {np.degrees(phases[50]):.1f}°")
        
        phase_drift = phases[-1] - phases[0]
        print(f"\nPhase drift over 4π rotation: {np.degrees(phase_drift):.1f}°")
        
        return {
            'phases': phases,
            'drift': np.degrees(phase_drift)
        }
    
    def run_all_tests(self) -> Dict:
        """Run all rotation tests."""
        print("=" * 80)
        print("  QMRT: ROTATION TEST - SPINOR VS CLASSICAL")
        print("=" * 80)
        print("""
THE CRITICAL QUESTION:
  Is the −1 holonomy from LOOP TOPOLOGY or TRUE ROTATIONAL GEOMETRY?

TEST CRITERIA:
  SPINOR: 360° → -1, 720° → +1
  CLASSICAL: 360° → +1, 720° → +1

This determines if we have real spinor behavior.
""")
        
        results = {}
        
        results['2pi'] = self.test_2pi_rotation()
        results['4pi'] = self.test_4pi_rotation()
        results['trajectory'] = self.test_incremental_rotation()
        results['signs'] = self.test_sign_structure_dependence()
        results['geometric'] = self.test_geometric_phase_accumulation()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        is_spinor_2pi = results['2pi']['is_spinor']
        returns_4pi = results['4pi']['returns_to_identity']
        
        print(f"""
ROTATION TEST RESULTS:

2π (360°) rotation:
  Ψ ratio: {results['2pi']['psi_ratio'].real:.3f} + {results['2pi']['psi_ratio'].imag:.3f}i
  Shows spinor behavior (≈ -1): {is_spinor_2pi}

4π (720°) rotation:
  Ψ ratio: {results['4pi']['psi_ratio'].real:.3f} + {results['4pi']['psi_ratio'].imag:.3f}i
  Returns to +1: {returns_4pi}
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        if is_spinor_2pi and returns_4pi:
            verdict = "TRUE_SPINOR_BEHAVIOR"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ TRUE SPINOR BEHAVIOR DETECTED                                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  360° rotation → -1 (sign flip)                                              ║
║  720° rotation → +1 (returns to identity)                                    ║
║                                                                              ║
║  This is REAL double-cover behavior from rotational geometry!                ║
║  Not just loop topology - actual spinor-like structure.                      ║
║                                                                              ║
║  QMRT has achieved: graph topology → geometric spinor                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        elif is_spinor_2pi:
            verdict = "PARTIAL_SPINOR"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ PARTIAL SPINOR BEHAVIOR                                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  360° rotation shows -1, but 4π doesn't cleanly return.                      ║
║  The rotation coupling needs refinement.                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "LATTICE_TOPOLOGY_ONLY"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ℹ️ LATTICE TOPOLOGY (NOT YET SPINOR)                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  The -1 holonomy comes from LOOP TOPOLOGY, not rotational geometry.          ║
║                                                                              ║
║  Current system: U(1) × Z₂ lattice gauge                                     ║
║  Not yet: SO(3) → SU(2) spinor structure                                     ║
║                                                                              ║
║  This is still valuable! But different from true spinors.                    ║
║                                                                              ║
║  Next step: Need to add rotation-phase coupling that produces                ║
║  geometric phase under spatial rotation.                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Save
        output = {
            'test': 'Rotation_Spinor_Test',
            'verdict': verdict,
            'test_2pi': {
                'psi_ratio': str(results['2pi']['psi_ratio']),
                'is_spinor': results['2pi']['is_spinor']
            },
            'test_4pi': {
                'psi_ratio': str(results['4pi']['psi_ratio']),
                'returns_to_identity': results['4pi']['returns_to_identity']
            },
            'sign_dependence': {
                k: {'is_spinor': v['is_spinor']} 
                for k, v in results['signs'].items()
            }
        }
        
        output_path = '/app/backend/qmrt_topology/rotation_test_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = SpinorRotationTest()
    results = test.run_all_tests()
