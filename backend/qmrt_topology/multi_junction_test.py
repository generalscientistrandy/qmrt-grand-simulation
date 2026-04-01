"""
QMRT: MULTI-JUNCTION LOOP TEST
==============================

CORRECTED UNDERSTANDING:
  Single Y-junction loop: Δφ = -π/2 (quarter phase)
  This is Z₄ holonomy: {1, -i, -1, i}
  NOT yet SU(2) fermion behavior

TRUE SPIN-1/2:
  1 loop → -1
  2 loops → +1
  
OUR SYSTEM:
  1 loop → -i
  2 loops → -1
  4 loops → +1

CRITICAL QUESTION:
  Can MULTIPLE junctions combine to give:
    Δφ = π in a SINGLE effective loop?
  
  If YES → approach to true fermion
  If NO → stays at Z₄ pre-spinor level

TESTS:
  1. Loop through 2 Y-junctions
  2. Loop through 3 Y-junctions
  3. Loop through 4 Y-junctions
  4. Path dependence (same endpoints, different paths)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json


@dataclass
class ProbeState:
    """Probe state with accumulated phase."""
    amplitude: complex
    phase: float
    
    def rotate(self, angle: float) -> 'ProbeState':
        return ProbeState(
            self.amplitude * np.exp(1j * angle),
            self.phase + angle
        )
    
    @property
    def holonomy(self) -> complex:
        return np.exp(1j * self.phase)


class YJunction:
    """A Y-junction with 120° branch spacing."""
    
    def __init__(self, position: np.ndarray, orientation: float = 0):
        """
        Args:
            position: 2D position of junction center
            orientation: Rotation of junction (radians)
        """
        self.position = np.array(position)
        self.orientation = orientation
        
        # Branch angles (120° spacing + orientation)
        self.angles = np.array([
            orientation,
            orientation + 2*np.pi/3,
            orientation + 4*np.pi/3
        ]) % (2 * np.pi)
    
    def get_turning_angle(self, entry_branch: int, exit_branch: int) -> float:
        """Get turning angle for transit through junction."""
        entry_dir = self.angles[entry_branch] + np.pi  # Pointing inward
        exit_dir = self.angles[exit_branch]  # Pointing outward
        
        turn = exit_dir - entry_dir
        while turn > np.pi:
            turn -= 2 * np.pi
        while turn < -np.pi:
            turn += 2 * np.pi
        
        return turn
    
    def get_phase_shift(self, entry_branch: int, exit_branch: int) -> float:
        """Get geometric phase shift for transit."""
        turn = self.get_turning_angle(entry_branch, exit_branch)
        return turn / 2  # Half the turning angle


class MultiJunctionTest:
    """Test phase accumulation through multiple junctions."""
    
    def __init__(self):
        self.results = {}
    
    def transport_through_junction(self, junction: YJunction,
                                    entry: int, exit_branch: int,
                                    probe: ProbeState) -> ProbeState:
        """Transport probe through a junction."""
        phase_shift = junction.get_phase_shift(entry, exit_branch)
        return probe.rotate(phase_shift)
    
    def test_single_junction_loop(self) -> Dict:
        """Baseline: single junction, single loop."""
        print("=" * 70)
        print("TEST: SINGLE JUNCTION (BASELINE)")
        print("=" * 70)
        
        junction = YJunction(position=[0, 0])
        probe = ProbeState(1.0, 0.0)
        
        # One loop (3 transits)
        for i in range(3):
            probe = self.transport_through_junction(junction, i, (i+1)%3, probe)
        
        print(f"  1 loop: phase = {np.degrees(probe.phase):.1f}°, holonomy = {probe.holonomy:.4f}")
        
        single_result = {
            'loops': 1,
            'phase_deg': float(np.degrees(probe.phase)),
            'holonomy': complex(probe.holonomy)
        }
        
        return single_result
    
    def test_two_junction_loop(self) -> Dict:
        """Loop through 2 junctions."""
        print("\n" + "=" * 70)
        print("TEST: TWO JUNCTIONS IN A LOOP")
        print("=" * 70)
        print("""
Topology:
     J1
    / | 
   /  |
  J2--+
  
Path: Start at J1 branch 0, go to J2, return to J1
""")
        
        j1 = YJunction(position=[0, 1], orientation=0)
        j2 = YJunction(position=[0, 0], orientation=np.pi/3)  # Rotated
        
        probe = ProbeState(1.0, 0.0)
        
        # J1: enter branch 0, exit branch 1 (toward J2)
        probe = self.transport_through_junction(j1, 0, 1, probe)
        print(f"  After J1 (0→1): phase = {np.degrees(probe.phase):.1f}°")
        
        # J2: enter, exit (different branch back to J1)
        probe = self.transport_through_junction(j2, 1, 2, probe)
        print(f"  After J2 (1→2): phase = {np.degrees(probe.phase):.1f}°")
        
        # Back to J1: enter branch 2, exit branch 0 (close loop)
        probe = self.transport_through_junction(j1, 2, 0, probe)
        print(f"  After J1 (2→0): phase = {np.degrees(probe.phase):.1f}°")
        
        print(f"\n  Total: phase = {np.degrees(probe.phase):.1f}°, holonomy = {probe.holonomy:.4f}")
        
        return {
            'junctions': 2,
            'phase_deg': float(np.degrees(probe.phase)),
            'holonomy': complex(probe.holonomy),
            'is_minus_one': np.isclose(probe.holonomy, -1, atol=0.01)
        }
    
    def test_three_junction_triangle(self) -> Dict:
        """Triangle of 3 junctions."""
        print("\n" + "=" * 70)
        print("TEST: THREE JUNCTIONS (TRIANGLE)")
        print("=" * 70)
        print("""
Topology:
       J1
      /  \\
     /    \\
    J2----J3
    
Path: J1 → J2 → J3 → J1
""")
        
        # Equilateral triangle of junctions
        j1 = YJunction(position=[0, 1], orientation=0)
        j2 = YJunction(position=[-0.866, -0.5], orientation=2*np.pi/3)
        j3 = YJunction(position=[0.866, -0.5], orientation=4*np.pi/3)
        
        probe = ProbeState(1.0, 0.0)
        
        # J1 → J2
        probe = self.transport_through_junction(j1, 0, 1, probe)
        print(f"  After J1: phase = {np.degrees(probe.phase):.1f}°")
        
        # J2 → J3
        probe = self.transport_through_junction(j2, 0, 1, probe)
        print(f"  After J2: phase = {np.degrees(probe.phase):.1f}°")
        
        # J3 → J1
        probe = self.transport_through_junction(j3, 0, 1, probe)
        print(f"  After J3: phase = {np.degrees(probe.phase):.1f}°")
        
        print(f"\n  Total: phase = {np.degrees(probe.phase):.1f}°, holonomy = {probe.holonomy:.4f}")
        
        return {
            'junctions': 3,
            'phase_deg': float(np.degrees(probe.phase)),
            'holonomy': complex(probe.holonomy),
            'is_minus_one': np.isclose(probe.holonomy, -1, atol=0.01)
        }
    
    def test_four_junction_square(self) -> Dict:
        """Square of 4 junctions."""
        print("\n" + "=" * 70)
        print("TEST: FOUR JUNCTIONS (SQUARE)")
        print("=" * 70)
        print("""
Topology:
    J1----J2
    |      |
    |      |
    J4----J3
    
Path: J1 → J2 → J3 → J4 → J1
""")
        
        j1 = YJunction(position=[0, 1], orientation=0)
        j2 = YJunction(position=[1, 1], orientation=np.pi/2)
        j3 = YJunction(position=[1, 0], orientation=np.pi)
        j4 = YJunction(position=[0, 0], orientation=3*np.pi/2)
        
        probe = ProbeState(1.0, 0.0)
        
        # Around the square
        probe = self.transport_through_junction(j1, 0, 1, probe)
        print(f"  After J1: phase = {np.degrees(probe.phase):.1f}°")
        
        probe = self.transport_through_junction(j2, 0, 1, probe)
        print(f"  After J2: phase = {np.degrees(probe.phase):.1f}°")
        
        probe = self.transport_through_junction(j3, 0, 1, probe)
        print(f"  After J3: phase = {np.degrees(probe.phase):.1f}°")
        
        probe = self.transport_through_junction(j4, 0, 1, probe)
        print(f"  After J4: phase = {np.degrees(probe.phase):.1f}°")
        
        print(f"\n  Total: phase = {np.degrees(probe.phase):.1f}°, holonomy = {probe.holonomy:.4f}")
        
        return {
            'junctions': 4,
            'phase_deg': float(np.degrees(probe.phase)),
            'holonomy': complex(probe.holonomy),
            'is_minus_one': np.isclose(probe.holonomy, -1, atol=0.01)
        }
    
    def test_path_dependence(self) -> Dict:
        """Test if different paths give different phases (true holonomy)."""
        print("\n" + "=" * 70)
        print("TEST: PATH DEPENDENCE")
        print("=" * 70)
        print("""
Question: Do different paths between same points give different phases?
If YES → true holonomy (gauge-like behavior)
If NO → trivial phase structure
""")
        
        # Two paths from A to B
        j1 = YJunction(position=[0, 0])
        j2 = YJunction(position=[1, 0], orientation=np.pi/6)
        j3 = YJunction(position=[0.5, 0.866], orientation=np.pi/3)
        
        # Path 1: Direct (through J1 only)
        probe1 = ProbeState(1.0, 0.0)
        probe1 = self.transport_through_junction(j1, 0, 1, probe1)
        print(f"  Path 1 (direct through J1): phase = {np.degrees(probe1.phase):.1f}°")
        
        # Path 2: Via J2 and J3
        probe2 = ProbeState(1.0, 0.0)
        probe2 = self.transport_through_junction(j1, 0, 2, probe2)  # Different exit
        probe2 = self.transport_through_junction(j3, 1, 0, probe2)
        probe2 = self.transport_through_junction(j2, 2, 1, probe2)
        print(f"  Path 2 (via J3, J2): phase = {np.degrees(probe2.phase):.1f}°")
        
        phase_diff = probe2.phase - probe1.phase
        print(f"\n  Phase difference: {np.degrees(phase_diff):.1f}°")
        
        path_dependent = abs(phase_diff) > 0.01
        
        if path_dependent:
            print("  → PATH DEPENDENT: True holonomy!")
        else:
            print("  → PATH INDEPENDENT: Trivial structure")
        
        return {
            'path1_phase_deg': float(np.degrees(probe1.phase)),
            'path2_phase_deg': float(np.degrees(probe2.phase)),
            'phase_difference_deg': float(np.degrees(phase_diff)),
            'path_dependent': bool(path_dependent)
        }
    
    def test_scaling(self) -> Dict:
        """Test how phase scales with number of junctions."""
        print("\n" + "=" * 70)
        print("TEST: PHASE SCALING WITH JUNCTION COUNT")
        print("=" * 70)
        
        results = []
        
        print(f"{'Junctions':>10} | {'Phase (deg)':>12} | {'Holonomy':>15} | {'Per Junction':>12}")
        print("-" * 60)
        
        for n_junctions in range(1, 9):
            # Create n junctions in a ring
            junctions = []
            for i in range(n_junctions):
                angle = 2 * np.pi * i / n_junctions
                pos = [np.cos(angle), np.sin(angle)]
                orientation = angle + np.pi/2  # Tangent orientation
                junctions.append(YJunction(pos, orientation))
            
            # Transport through all
            probe = ProbeState(1.0, 0.0)
            for i, j in enumerate(junctions):
                probe = self.transport_through_junction(j, 0, 1, probe)
            
            phase_per_junction = probe.phase / n_junctions if n_junctions > 0 else 0
            
            print(f"{n_junctions:>10} | {np.degrees(probe.phase):>12.1f} | {probe.holonomy.real:>7.4f}{probe.holonomy.imag:+7.4f}j | {np.degrees(phase_per_junction):>12.1f}°")
            
            results.append({
                'n_junctions': n_junctions,
                'total_phase_deg': float(np.degrees(probe.phase)),
                'phase_per_junction_deg': float(np.degrees(phase_per_junction)),
                'holonomy': complex(probe.holonomy)
            })
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all multi-junction tests."""
        print("=" * 80)
        print("  QMRT: MULTI-JUNCTION LOOP TEST")
        print("=" * 80)
        print("""
GOAL: Determine if Z₄ structure can approach SU(2) with multiple junctions.

CURRENT STATUS:
  Single Y-junction: Δφ = -π/2 per loop (Z₄)
  
QUESTION:
  Can multiple junctions produce Δφ = π in single effective loop?
  That would indicate approach to true fermion behavior.
""")
        
        results = {}
        
        results['single_junction'] = self.test_single_junction_loop()
        results['two_junctions'] = self.test_two_junction_loop()
        results['three_junctions'] = self.test_three_junction_triangle()
        results['four_junctions'] = self.test_four_junction_square()
        results['path_dependence'] = self.test_path_dependence()
        results['scaling'] = self.test_scaling()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        print(f"""
PHASE ACCUMULATION BY CONFIGURATION:

  Single junction (1 loop):     {results['single_junction']['phase_deg']:.1f}°
  Two junctions (loop):         {results['two_junctions']['phase_deg']:.1f}°
  Three junctions (triangle):   {results['three_junctions']['phase_deg']:.1f}°
  Four junctions (square):      {results['four_junctions']['phase_deg']:.1f}°

PATH DEPENDENCE:
  Different paths give different phases: {results['path_dependence']['path_dependent']}
  Phase difference: {results['path_dependence']['phase_difference_deg']:.1f}°
""")
        
        # Analysis
        print("=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        # Check if any configuration gives -1 holonomy in single loop
        configs_with_minus_one = []
        for name, data in results.items():
            if isinstance(data, dict) and data.get('is_minus_one', False):
                configs_with_minus_one.append(name)
        
        # Check scaling pattern
        scaling = results['scaling']
        phases_per_junction = [s['phase_per_junction_deg'] for s in scaling]
        
        print(f"""
PHASE PER JUNCTION (from scaling test):
  Average: {np.mean(phases_per_junction):.1f}°
  Std dev: {np.std(phases_per_junction):.1f}°
  
  → Phase accumulates {'linearly' if np.std(phases_per_junction) < 5 else 'non-linearly'}
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        if configs_with_minus_one:
            verdict = "FERMION_POSSIBLE"
            print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ FERMION-LIKE HOLONOMY FOUND IN: {configs_with_minus_one}
╠══════════════════════════════════════════════════════════════════════════════╣
║  Some multi-junction configurations produce -1 holonomy.                     ║
║  This suggests fermion behavior can emerge from junction networks.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        elif results['path_dependence']['path_dependent']:
            verdict = "PRE_SPINOR_WITH_HOLONOMY"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ Z₄ PRE-SPINOR WITH TRUE HOLONOMY                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Phase is path-dependent (true gauge-like behavior).                         ║
║  But individual loops don't yet give -1 holonomy.                            ║
║                                                                              ║
║  This is a PRE-SPINOR structure that could underlie fermions.                ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "DISCRETE_Z4"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  Z₄ DISCRETE HOLONOMY                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Phase accumulates in quarter steps.                                         ║
║  Single loops give -i (quarter rotation).                                    ║
║  Double loops give -1 (sign flip).                                           ║
║  Four loops return to +1.                                                    ║
║                                                                              ║
║  This is the MECHANISM that could generate fermions with additional          ║
║  structure (e.g., continuous limit, multi-junction interference).            ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # The corrected theoretical statement
        print("""
CORRECTED THEORETICAL CLAIM:

  "A discrete Z₄ geometric phase structure emerges from Y-junction transport.
   Each junction transit contributes Δφ = -π/2 (quarter phase).
   
   Double-loop holonomy produces -1 phase, indicating a pre-spinor topology.
   This is NOT yet full SU(2) fermionic behavior, but it is the MECHANISM
   that could generate fermions with additional structure."

LAYER STRUCTURE:
  Layer 1 — Geometry:    Y-junction, 120° structure
  Layer 2 — Transport:   Discrete branch transitions
  Layer 3 — Phase:       ±i, ±1 (Z₄ structure)
  Layer 4 — Emergence:   (NOT YET REACHED) continuous rotation, SU(2)
""")
        
        # Save results
        output = {
            'test': 'Multi_Junction_Loop',
            'verdict': verdict,
            'single_junction': results['single_junction'],
            'two_junctions': results['two_junctions'],
            'three_junctions': results['three_junctions'],
            'four_junctions': results['four_junctions'],
            'path_dependence': results['path_dependence'],
            'scaling_summary': {
                'mean_phase_per_junction': float(np.mean(phases_per_junction)),
                'std_phase_per_junction': float(np.std(phases_per_junction))
            }
        }
        
        # Convert complex numbers for JSON
        def convert_for_json(obj):
            if isinstance(obj, complex):
                return f"{obj.real:.4f}{obj.imag:+.4f}j"
            elif isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(i) for i in obj]
            return obj
        
        output_path = '/app/backend/qmrt_topology/multi_junction_results.json'
        with open(output_path, 'w') as f:
            json.dump(convert_for_json(output), f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = MultiJunctionTest()
    results = test.run_all_tests()
