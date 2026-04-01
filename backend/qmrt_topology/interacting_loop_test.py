"""
QMRT: INTERACTING LOOP MODEL
============================

THE UPGRADE (from user guidance):

  Current: E_total = Σ(loop energy)  [isolated]
  
  Needed:  E_total = Σ(loop energy)
                   + Σ(branch interaction)
                   + Σ(torsion coupling)
                   + Σ(self-interaction/localization)

KEY PRINCIPLE:
  "Topology alone defines what is POSSIBLE.
   Interaction determines what is REALIZED."

INTERACTION TERMS:
  1. Branch-branch: phase alignment penalty, angle mismatch
  2. Loop-medium feedback: torsion accumulation, back-reaction
  3. Self-interaction: localization reward, spreading penalty
  4. Emergent-emergent: loop-loop interaction

HYPOTHESIS:
  With interactions, 6-loops may become special because they:
  - Are smallest loops that close phase consistently
  - Trap torsion efficiently
  - Minimize frustration in coupled system
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json


@dataclass
class Branch:
    """A branch segment with phase and torsion."""
    id: int
    start_pos: np.ndarray
    end_pos: np.ndarray
    phase: float = 0.0           # Local phase
    torsion: float = 0.0         # Accumulated torsion
    tension: float = 1.0
    
    def __post_init__(self):
        self.start_pos = np.array(self.start_pos, dtype=float)
        self.end_pos = np.array(self.end_pos, dtype=float)
    
    @property
    def direction(self) -> np.ndarray:
        d = self.end_pos - self.start_pos
        return d / (np.linalg.norm(d) + 1e-10)
    
    @property
    def length(self) -> float:
        return np.linalg.norm(self.end_pos - self.start_pos)
    
    @property
    def midpoint(self) -> np.ndarray:
        return (self.start_pos + self.end_pos) / 2


@dataclass
class Loop:
    """A closed loop of branches."""
    id: int
    branch_ids: List[int]
    total_phase: float = 0.0     # Phase around loop
    localization: float = 1.0    # How localized (vs spread out)


class InteractingMedium:
    """
    Medium with full interaction terms.
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.branches: Dict[int, Branch] = {}
        self.loops: Dict[int, Loop] = {}
        self.next_branch_id = 0
        self.next_loop_id = 0
        
        # INTERACTION PARAMETERS
        self.phase_mismatch_penalty = 1.0      # Branch-branch
        self.angle_mismatch_penalty = 0.5      # Branch-branch
        self.torsion_coupling = 0.3            # Loop-medium
        self.torsion_concentration_bonus = 0.5 # Loop-medium
        self.localization_reward = 2.0         # Self-interaction
        self.spreading_penalty = 1.0           # Self-interaction
        self.loop_loop_coupling = 0.2          # Emergent-emergent
        
        # Phase per transit (from our Z_12 finding)
        self.phase_per_transit = -np.pi / 6    # -30 degrees
    
    def add_branch(self, start: np.ndarray, end: np.ndarray) -> int:
        bid = self.next_branch_id
        self.branches[bid] = Branch(bid, start, end)
        self.next_branch_id += 1
        return bid
    
    def create_regular_loop(self, n: int, center: np.ndarray = None,
                            radius: float = 1.0) -> int:
        """Create a regular n-gon loop."""
        if center is None:
            center = np.array([0.0, 0.0])
        
        branch_ids = []
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        for i in range(n):
            start_angle = angles[i]
            end_angle = angles[(i + 1) % n]
            
            start = center + radius * np.array([np.cos(start_angle), np.sin(start_angle)])
            end = center + radius * np.array([np.cos(end_angle), np.sin(end_angle)])
            
            bid = self.add_branch(start, end)
            branch_ids.append(bid)
        
        # Create loop
        lid = self.next_loop_id
        total_phase = n * self.phase_per_transit
        
        self.loops[lid] = Loop(
            id=lid,
            branch_ids=branch_ids,
            total_phase=total_phase,
            localization=1.0 / radius  # Smaller radius = more localized
        )
        self.next_loop_id += 1
        
        return lid
    
    # =========================================================================
    # ENERGY TERMS
    # =========================================================================
    
    def E_branch_interaction(self) -> float:
        """
        Branch-branch interaction energy.
        
        1. Phase mismatch: neighboring branches want aligned phases
        2. Angle mismatch: smooth bending costs less energy
        """
        energy = 0.0
        branches = list(self.branches.values())
        
        for i, b1 in enumerate(branches):
            for b2 in branches[i+1:]:
                # Check if neighbors (share endpoint)
                dist = min(
                    np.linalg.norm(b1.end_pos - b2.start_pos),
                    np.linalg.norm(b1.start_pos - b2.end_pos),
                    np.linalg.norm(b1.end_pos - b2.end_pos),
                    np.linalg.norm(b1.start_pos - b2.start_pos)
                )
                
                if dist < 0.1:  # Connected
                    # Phase mismatch
                    phase_diff = b1.phase - b2.phase
                    energy += self.phase_mismatch_penalty * (1 - np.cos(phase_diff))
                    
                    # Angle mismatch (sharp bends cost energy)
                    cos_angle = np.dot(b1.direction, b2.direction)
                    bend_angle = np.arccos(np.clip(cos_angle, -1, 1))
                    energy += self.angle_mismatch_penalty * bend_angle**2
        
        return energy
    
    def E_torsion_coupling(self, loop: Loop) -> float:
        """
        Loop-medium feedback via torsion.
        
        Torsion accumulates around loops.
        There's a bonus for concentrating torsion (localized vortex)
        and a penalty for spreading it (delocalized).
        """
        n = len(loop.branch_ids)
        
        # Torsion density = total phase / perimeter
        perimeter = sum(self.branches[bid].length for bid in loop.branch_ids)
        torsion_density = abs(loop.total_phase) / (perimeter + 0.1)
        
        # Bonus for concentrated torsion (smaller loops)
        concentration_bonus = -self.torsion_concentration_bonus * torsion_density
        
        # Back-reaction: update branch torsion
        for bid in loop.branch_ids:
            self.branches[bid].torsion += torsion_density * 0.1
        
        return concentration_bonus
    
    def E_self_interaction(self, loop: Loop) -> float:
        """
        Self-interaction / localization energy.
        
        Particles want to be localized (not spread out).
        This creates effective mass.
        """
        # Localization factor (inverse of effective radius)
        loc = loop.localization
        
        # Reward for localization, penalty for spreading
        energy = -self.localization_reward * loc + self.spreading_penalty / (loc + 0.1)
        
        return energy
    
    def E_loop_loop(self) -> float:
        """
        Emergent-emergent interaction.
        
        Loops interact with each other:
        - Same phase loops repel (Pauli-like)
        - Opposite phase loops can bind
        """
        energy = 0.0
        loops = list(self.loops.values())
        
        for i, l1 in enumerate(loops):
            for l2 in loops[i+1:]:
                # Distance between loop centers
                c1 = self._loop_center(l1)
                c2 = self._loop_center(l2)
                dist = np.linalg.norm(c2 - c1) + 0.1
                
                # Phase overlap
                phase_diff = l1.total_phase - l2.total_phase
                
                # Same phase = repulsion (Pauli), opposite = possible binding
                interaction = self.loop_loop_coupling * np.cos(phase_diff) / dist**2
                
                energy += interaction
        
        return energy
    
    def _loop_center(self, loop: Loop) -> np.ndarray:
        """Compute center of a loop."""
        positions = []
        for bid in loop.branch_ids:
            positions.append(self.branches[bid].midpoint)
        return np.mean(positions, axis=0)
    
    def E_base_loop(self, loop: Loop) -> float:
        """Base loop energy (geometry only)."""
        n = len(loop.branch_ids)
        perimeter = sum(self.branches[bid].length for bid in loop.branch_ids)
        
        # Base energy: tension × length
        E_tension = perimeter
        
        # Angle energy (deviation from ideal n-gon)
        ideal_angle = (n - 2) * np.pi / n
        angle_deviation = 0.0
        
        for i, bid in enumerate(loop.branch_ids):
            next_bid = loop.branch_ids[(i + 1) % n]
            b1 = self.branches[bid]
            b2 = self.branches[next_bid]
            
            cos_angle = -np.dot(b1.direction, b2.direction)  # Interior angle
            actual_angle = np.arccos(np.clip(cos_angle, -1, 1))
            angle_deviation += (actual_angle - ideal_angle)**2
        
        E_angle = 0.1 * angle_deviation
        
        return E_tension + E_angle
    
    def compute_total_loop_energy(self, loop: Loop) -> Dict[str, float]:
        """
        COMPLETE energy with all interaction terms.
        
        E_total = E_base + E_branch + E_torsion + E_self + E_loop_loop
        """
        E_base = self.E_base_loop(loop)
        E_branch = self.E_branch_interaction()
        E_torsion = self.E_torsion_coupling(loop)
        E_self = self.E_self_interaction(loop)
        E_loop_loop = self.E_loop_loop()
        
        E_total = E_base + E_branch + E_torsion + E_self + E_loop_loop
        
        return {
            'E_base': float(E_base),
            'E_branch': float(E_branch),
            'E_torsion': float(E_torsion),
            'E_self': float(E_self),
            'E_loop_loop': float(E_loop_loop),
            'E_total': float(E_total),
            'n': len(loop.branch_ids)
        }


class InteractingLoopTest:
    """Test loop selection with full interactions."""
    
    def __init__(self):
        self.results = {}
    
    def test_isolated_vs_interacting(self) -> Dict:
        """Compare loop ranking with and without interactions."""
        print("=" * 70)
        print("TEST 1: ISOLATED vs INTERACTING LOOP ENERGY")
        print("=" * 70)
        print("""
Comparing energy rankings:
  ISOLATED: E = E_base only (what we had before)
  INTERACTING: E = E_base + E_branch + E_torsion + E_self
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'E_isolated':>12} | {'E_interacting':>14} | {'E_total/n':>12}")
        print("-" * 55)
        
        for n in [3, 4, 5, 6, 7, 8, 9, 10, 12]:
            # Create medium with single loop
            medium = InteractingMedium()
            lid = medium.create_regular_loop(n, radius=1.0)
            loop = medium.loops[lid]
            
            # Isolated energy (base only)
            E_isolated = medium.E_base_loop(loop)
            
            # Full interacting energy
            energy = medium.compute_total_loop_energy(loop)
            E_total = energy['E_total']
            
            marker = " ← FERMION" if n == 6 else ""
            print(f"{n:>4} | {E_isolated:>12.4f} | {E_total:>14.4f} | {E_total/n:>12.4f}{marker}")
            
            results.append({
                'n': n,
                'E_isolated': E_isolated,
                'E_total': E_total,
                'E_per_vertex': E_total / n,
                **energy
            })
        
        # Find rankings
        isolated_ranking = sorted(results, key=lambda x: x['E_isolated'])
        interacting_ranking = sorted(results, key=lambda x: x['E_per_vertex'])
        
        print(f"\nBest by E_isolated: n = {isolated_ranking[0]['n']}")
        print(f"Best by E_total/n:  n = {interacting_ranking[0]['n']}")
        
        # Where is n=6?
        six_isolated_rank = next(i+1 for i, x in enumerate(isolated_ranking) if x['n'] == 6)
        six_interact_rank = next(i+1 for i, x in enumerate(interacting_ranking) if x['n'] == 6)
        
        print(f"\nn=6 ranking: Isolated #{six_isolated_rank}, Interacting #{six_interact_rank}")
        
        return {
            'isolated_best': isolated_ranking[0]['n'],
            'interacting_best': interacting_ranking[0]['n'],
            'six_isolated_rank': six_isolated_rank,
            'six_interact_rank': six_interact_rank,
            'details': results
        }
    
    def test_localization_effect(self) -> Dict:
        """Test how localization affects loop energy."""
        print("\n" + "=" * 70)
        print("TEST 2: LOCALIZATION EFFECT")
        print("=" * 70)
        print("""
Question: Does self-interaction favor certain loop sizes?

Testing loops at different radii (localization levels).
""")
        
        results = []
        
        for n in [3, 6, 12]:
            print(f"\n--- n = {n} ---")
            
            radius_results = []
            for radius in [0.5, 1.0, 2.0, 4.0]:
                medium = InteractingMedium()
                lid = medium.create_regular_loop(n, radius=radius)
                loop = medium.loops[lid]
                
                energy = medium.compute_total_loop_energy(loop)
                
                print(f"  r={radius:.1f}: E_self={energy['E_self']:.3f}, E_total={energy['E_total']:.3f}")
                
                radius_results.append({
                    'radius': radius,
                    **energy
                })
            
            # Find optimal radius
            optimal = min(radius_results, key=lambda x: x['E_total'])
            print(f"  Optimal radius: {optimal['radius']}")
            
            results.append({
                'n': n,
                'optimal_radius': optimal['radius'],
                'radius_scan': radius_results
            })
        
        return results
    
    def test_torsion_concentration(self) -> Dict:
        """Test torsion concentration effect."""
        print("\n" + "=" * 70)
        print("TEST 3: TORSION CONCENTRATION")
        print("=" * 70)
        print("""
Question: Does torsion concentration favor specific loop sizes?

Torsion density = |total_phase| / perimeter
Higher density = more concentrated vortex
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Phase':>10} | {'Perimeter':>10} | {'Torsion ρ':>10} | {'E_torsion':>10}")
        print("-" * 60)
        
        for n in [3, 4, 5, 6, 7, 8, 9, 10, 12]:
            medium = InteractingMedium()
            lid = medium.create_regular_loop(n, radius=1.0)
            loop = medium.loops[lid]
            
            perimeter = sum(medium.branches[bid].length for bid in loop.branch_ids)
            torsion_density = abs(loop.total_phase) / perimeter
            
            energy = medium.compute_total_loop_energy(loop)
            
            marker = " ← FERMION" if n == 6 else ""
            print(f"{n:>4} | {np.degrees(loop.total_phase):>9.1f}° | {perimeter:>10.3f} | {torsion_density:>10.4f} | {energy['E_torsion']:>10.4f}{marker}")
            
            results.append({
                'n': n,
                'total_phase': float(loop.total_phase),
                'perimeter': float(perimeter),
                'torsion_density': float(torsion_density),
                'E_torsion': energy['E_torsion']
            })
        
        # Which has best (most negative) torsion energy?
        best_torsion = min(results, key=lambda x: x['E_torsion'])
        print(f"\nBest torsion energy: n = {best_torsion['n']}")
        
        return results
    
    def test_phase_closure_constraint(self) -> Dict:
        """Test phase closure as a selection mechanism."""
        print("\n" + "=" * 70)
        print("TEST 4: PHASE CLOSURE CONSTRAINT")
        print("=" * 70)
        print("""
Key insight: Some loop sizes close phase more "cleanly" than others.

Phase per transit: -30° = -π/6
Total phase for n transits: n × (-30°)

Clean closure means total phase is multiple of 2π (or π for fermions).
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Phase (°)':>10} | {'mod 360°':>10} | {'mod 180°':>10} | {'Fermion?':>10}")
        print("-" * 60)
        
        for n in range(3, 25):
            phase_deg = n * (-30)
            mod_360 = phase_deg % 360
            mod_180 = phase_deg % 180
            
            # Fermion condition: total phase = π (mod 2π)
            is_fermion = abs(mod_360 - 180) < 1 or abs(mod_360 + 180) < 1
            
            # Boson condition: total phase = 0 (mod 2π)
            is_boson = abs(mod_360) < 1 or abs(mod_360 - 360) < 1
            
            if n <= 12 or is_fermion or is_boson:
                marker = ""
                if is_fermion:
                    marker = " ← FERMION"
                elif is_boson:
                    marker = " ← BOSON"
                
                print(f"{n:>4} | {phase_deg:>10} | {mod_360:>10.1f} | {mod_180:>10.1f} | {'✅' if is_fermion else '❌':>10}{marker}")
            
            results.append({
                'n': n,
                'phase_deg': phase_deg,
                'mod_360': mod_360,
                'is_fermion': is_fermion,
                'is_boson': is_boson
            })
        
        fermion_sizes = [r['n'] for r in results if r['is_fermion']]
        boson_sizes = [r['n'] for r in results if r['is_boson']]
        
        print(f"\nFermion loop sizes (phase = ±180°): {fermion_sizes[:5]}...")
        print(f"Boson loop sizes (phase = 0°, 360°): {boson_sizes[:5]}...")
        
        return {
            'fermion_sizes': fermion_sizes,
            'boson_sizes': boson_sizes,
            'details': results
        }
    
    def run_all_tests(self) -> Dict:
        """Run all interacting model tests."""
        print("=" * 80)
        print("  QMRT: INTERACTING LOOP MODEL")
        print("=" * 80)
        print("""
THE UPGRADE:
  E_total = E_base + E_branch + E_torsion + E_self + E_loop_loop

PRINCIPLE:
  "Topology alone defines what is POSSIBLE.
   Interaction determines what is REALIZED."
""")
        
        results = {}
        
        results['isolated_vs_interacting'] = self.test_isolated_vs_interacting()
        results['localization'] = self.test_localization_effect()
        results['torsion'] = self.test_torsion_concentration()
        results['phase_closure'] = self.test_phase_closure_constraint()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        iso_best = results['isolated_vs_interacting']['isolated_best']
        int_best = results['isolated_vs_interacting']['interacting_best']
        six_rank = results['isolated_vs_interacting']['six_interact_rank']
        
        fermion_sizes = results['phase_closure']['fermion_sizes'][:5]
        
        print(f"""
LOOP SELECTION RESULTS:

  Isolated model best:     n = {iso_best}
  Interacting model best:  n = {int_best}
  n=6 rank (interacting):  #{six_rank}
  
  Fermion loop sizes (phase closure): {fermion_sizes}
  
PHASE CLOSURE INSIGHT:
  n=6:  phase = -180° = π  → FERMION ✅
  n=12: phase = -360° = 0  → BOSON
  n=18: phase = -540° = π  → FERMION ✅
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        six_improved = six_rank < results['isolated_vs_interacting']['six_isolated_rank']
        six_is_fermion = 6 in fermion_sizes
        
        if six_improved and six_is_fermion:
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ INTERACTION IMPROVES 6-LOOP SELECTION                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  With interactions, n=6 becomes more favorable.                              ║
║  Phase closure confirms: n=6 is a FERMION loop (phase = π → holonomy = -1)   ║
║                                                                              ║
║  The principle holds:                                                        ║
║    "Topology defines possible. Interaction selects realized."                ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        elif six_is_fermion:
            print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ 6-LOOP IS FERMION BY PHASE, NOT BY ENERGY                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Phase closure: n=6 gives π phase → fermion holonomy = -1 ✅                 ║
║  Energy ranking: n=6 is #{six_rank} (not optimal)                              ║
║                                                                              ║
║  Selection may require:                                                      ║
║    - Stronger torsion concentration                                          ║
║    - Phase closure constraint (only π-phase loops allowed)                   ║
║    - Boundary conditions favoring hexagonal structure                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  Interaction model needs further refinement                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # The key insight
        print("""
🔥 KEY INSIGHT FROM PHASE CLOSURE:

  n=6 is the SMALLEST loop that gives FERMION holonomy (-1).
  
  Loop sizes that give fermion behavior: n = 6, 18, 30, 42, ...
  (All satisfy: n × 30° = 180° mod 360°)
  
  n=6 is special because:
    1. It's the MINIMUM fermion loop size
    2. It naturally tiles in hexagonal structure
    3. It closes phase to exactly π
    
  Even if it's not the absolute energy minimum,
  it may be SELECTED by phase closure constraints!
""")
        
        # Save results
        output = {
            'test': 'Interacting_Loop_Model',
            'isolated_vs_interacting': {
                'isolated_best': iso_best,
                'interacting_best': int_best,
                'six_rank': six_rank
            },
            'phase_closure': {
                'fermion_sizes': fermion_sizes,
                'smallest_fermion': min(fermion_sizes) if fermion_sizes else None
            }
        }
        
        output_path = '/app/backend/qmrt_topology/interacting_loop_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = InteractingLoopTest()
    results = test.run_all_tests()
