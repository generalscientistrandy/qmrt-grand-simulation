"""
QMRT: EMERGENT BERRY PHASE FROM BRANCH TRANSPORT
=================================================

THE REAL TEST:
  Can the 1/2 factor EMERGE from junction geometry,
  rather than being inserted manually?

THE APPROACH:
  Instead of: phase += α × rotation  (manual)
  
  Do this:
    - Phase accumulates from TURNING ANGLE at each junction
    - Δθ_phase = f(∠ between incoming and outgoing branch)
    - NO manual α parameter
    - See what factor emerges naturally

THE KEY QUESTION:
  What is the natural relationship between:
    - Geometric turning angle (how much path bends)
    - Phase accumulation (Berry phase)
  
  In Y-junction geometry?

THE PHYSICS:
  At a Y-junction with 120° branch separations:
    - Incoming branch direction: ê_in
    - Outgoing branch direction: ê_out
    - Turning angle: Δφ = angle between them
    
  The phase should accumulate based on this turning.
  
  Question: Does this naturally give θ_phase = ½ × total_turning?
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json


@dataclass
class DirectedBranch:
    """A branch with explicit direction."""
    id: int
    junction_id: int
    direction: float  # Angle in radians (direction branch points)
    
    def direction_vector(self) -> np.ndarray:
        """Unit vector in branch direction."""
        return np.array([np.cos(self.direction), np.sin(self.direction)])


@dataclass
class TransportJunction:
    """Junction where phase transport occurs."""
    id: int
    position: np.ndarray
    branches: List[int] = field(default_factory=list)  # Branch IDs
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=float)


class BranchTransportNetwork:
    """
    Network with phase transport based on TURNING ANGLES.
    
    NO MANUAL α PARAMETER.
    
    Phase accumulates from geometry:
      - At each junction, compute turning angle
      - Phase change = f(turning angle)
      - The function f is derived from geometry, not inserted
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        
        self.junctions: Dict[int, TransportJunction] = {}
        self.branches: Dict[int, DirectedBranch] = {}
        self.connections: List[Tuple[int, int]] = []  # (branch_id, branch_id) pairs
        
        self.next_junction_id = 0
        self.next_branch_id = 0
    
    def add_junction(self, position: np.ndarray) -> int:
        jid = self.next_junction_id
        self.junctions[jid] = TransportJunction(jid, position)
        self.next_junction_id += 1
        return jid
    
    def add_branch(self, junction_id: int, direction: float) -> int:
        bid = self.next_branch_id
        self.branches[bid] = DirectedBranch(bid, junction_id, direction)
        self.junctions[junction_id].branches.append(bid)
        self.next_branch_id += 1
        return bid
    
    def connect_branches(self, branch1: int, branch2: int):
        """Connect two branches (forming an edge between junctions)."""
        self.connections.append((branch1, branch2))
    
    def create_hexagonal_loop(self) -> List[int]:
        """
        Create hexagonal loop with proper branch directions.
        
        Each junction has 3 branches at 120° separation.
        """
        jids = []
        
        # Create 6 junctions in hexagonal arrangement
        for i in range(6):
            angle = 2 * np.pi * i / 6
            pos = np.array([np.cos(angle), np.sin(angle)])
            jid = self.add_junction(pos)
            jids.append(jid)
        
        # Create branches for each junction
        # Each junction has 3 branches: to prev, to next, and outward
        branch_to_next = {}
        branch_to_prev = {}
        
        for i, jid in enumerate(jids):
            junction = self.junctions[jid]
            
            # Direction to previous junction
            prev_i = (i - 1) % 6
            prev_pos = self.junctions[jids[prev_i]].position
            dir_to_prev = np.arctan2(
                prev_pos[1] - junction.position[1],
                prev_pos[0] - junction.position[0]
            )
            
            # Direction to next junction
            next_i = (i + 1) % 6
            next_pos = self.junctions[jids[next_i]].position
            dir_to_next = np.arctan2(
                next_pos[1] - junction.position[1],
                next_pos[0] - junction.position[0]
            )
            
            # Outward direction (radial)
            dir_out = np.arctan2(junction.position[1], junction.position[0])
            
            # Add branches
            b_prev = self.add_branch(jid, dir_to_prev)
            b_next = self.add_branch(jid, dir_to_next)
            b_out = self.add_branch(jid, dir_out)
            
            branch_to_next[jid] = b_next
            branch_to_prev[jid] = b_prev
        
        # Connect branches between adjacent junctions
        for i, jid in enumerate(jids):
            next_jid = jids[(i + 1) % 6]
            
            # Branch from jid pointing to next
            b_from = branch_to_next[jid]
            # Branch from next pointing back
            b_to = branch_to_prev[next_jid]
            
            self.connect_branches(b_from, b_to)
        
        return jids
    
    # =========================================================================
    # TURNING ANGLE COMPUTATION (THE KEY)
    # =========================================================================
    
    def compute_turning_angle(self, in_branch: int, out_branch: int) -> float:
        """
        Compute the TURNING ANGLE when transitioning from in_branch to out_branch.
        
        This is the angle the path bends at the junction.
        
        Turning angle = angle(out_direction) - angle(in_direction)
        
        Positive = left turn, Negative = right turn
        """
        b_in = self.branches[in_branch]
        b_out = self.branches[out_branch]
        
        # Verify same junction
        if b_in.junction_id != b_out.junction_id:
            raise ValueError("Branches must be at same junction")
        
        # Incoming direction (reversed - we're coming IN on this branch)
        in_dir = b_in.direction + np.pi  # Flip to get incoming direction
        
        # Outgoing direction
        out_dir = b_out.direction
        
        # Turning angle
        turn = out_dir - in_dir
        
        # Wrap to [-π, π]
        while turn > np.pi:
            turn -= 2 * np.pi
        while turn < -np.pi:
            turn += 2 * np.pi
        
        return turn
    
    def compute_total_turning_around_loop(self, junction_ids: List[int]) -> float:
        """
        Compute TOTAL TURNING ANGLE around a loop.
        
        This should equal 2π for a simple closed loop (exterior angle sum).
        """
        n = len(junction_ids)
        total_turning = 0.0
        
        for i in range(n):
            jid = junction_ids[i]
            prev_jid = junction_ids[(i - 1) % n]
            next_jid = junction_ids[(i + 1) % n]
            
            # Find branches
            junction = self.junctions[jid]
            
            # Branch from prev (incoming)
            in_branch = None
            out_branch = None
            
            for bid in junction.branches:
                branch = self.branches[bid]
                # Check if this branch points toward prev_jid
                target = self.junctions[prev_jid].position
                branch_target = junction.position + branch.direction_vector()
                # Approximate: branch pointing toward prev
                if self._branch_points_toward(jid, bid, prev_jid):
                    in_branch = bid
                if self._branch_points_toward(jid, bid, next_jid):
                    out_branch = bid
            
            if in_branch is not None and out_branch is not None:
                turn = self.compute_turning_angle(in_branch, out_branch)
                total_turning += turn
        
        return total_turning
    
    def _branch_points_toward(self, from_jid: int, branch_id: int, to_jid: int) -> bool:
        """Check if a branch approximately points toward another junction."""
        from_pos = self.junctions[from_jid].position
        to_pos = self.junctions[to_jid].position
        
        # Direction to target
        dir_to_target = np.arctan2(to_pos[1] - from_pos[1], to_pos[0] - from_pos[0])
        
        # Branch direction
        branch_dir = self.branches[branch_id].direction
        
        # Check if close
        diff = abs(branch_dir - dir_to_target)
        if diff > np.pi:
            diff = 2 * np.pi - diff
        
        return diff < 0.5  # Within ~30 degrees
    
    # =========================================================================
    # PHASE TRANSPORT MODELS (TO TEST)
    # =========================================================================
    
    def transport_phase_model_A(self, turn_angle: float) -> float:
        """
        Model A: Phase = Turning angle directly.
        
        θ_phase = turn_angle
        
        If total turning = 2π, phase = 2π → holonomy = +1 (boson)
        """
        return turn_angle
    
    def transport_phase_model_B(self, turn_angle: float) -> float:
        """
        Model B: Phase = Half of turning angle.
        
        θ_phase = turn_angle / 2
        
        If total turning = 2π, phase = π → holonomy = -1 (fermion!)
        
        But WHY would this be natural?
        """
        return turn_angle / 2
    
    def transport_phase_model_C_projection(self, in_branch: int, out_branch: int) -> float:
        """
        Model C: Phase from PROJECTION between branch directions.
        
        This is the KEY candidate for emergent 1/2 factor.
        
        At a Y-junction:
          - 3 branches at 120° separation
          - Projection = cos(angle between branches)
          - For adjacent branches: cos(120°) = -0.5
        
        Phase contribution = arccos(projection) perhaps?
        Or something more natural from the geometry.
        """
        b_in = self.branches[in_branch]
        b_out = self.branches[out_branch]
        
        # Incoming direction (flip for incoming)
        in_vec = -b_in.direction_vector()  # Negative because incoming
        out_vec = b_out.direction_vector()
        
        # Projection (dot product)
        projection = np.dot(in_vec, out_vec)
        
        # The projection IS the geometric factor
        # cos(120°) = -0.5 for adjacent Y-junction branches
        
        # One natural choice: phase = arccos(projection) / 2
        # This gives phase = 60° for 120° turn... not quite right
        
        # Another: phase proportional to (1 - projection) / 2
        # For 120° turn: (1 - (-0.5)) / 2 = 0.75... also not clean
        
        # Let's just return the projection for analysis
        return projection
    
    def transport_phase_model_D_parallel_transport(self, in_branch: int, out_branch: int) -> float:
        """
        Model D: True parallel transport.
        
        In differential geometry, parallel transport around a curve
        accumulates holonomy equal to the enclosed solid angle.
        
        For a flat hexagon enclosing solid angle Ω:
          Holonomy phase = Ω/2 (for spin-1/2)
        
        But we need to derive this from DISCRETE junction rules.
        """
        turn = self.compute_turning_angle(in_branch, out_branch)
        
        # In true parallel transport, the phase shift equals
        # half the rotation angle (for spinors)
        # But we want this to EMERGE, not be inserted!
        
        # Let's try: phase = area element traced by transport
        # For a small turn Δφ, the area element is ~ Δφ² / 2
        # That's quadratic, not linear...
        
        # Actually, in 2D, the Berry phase for spin-1/2 IS:
        #   θ_Berry = (1/2) × (enclosed solid angle)
        #   
        # For a flat loop, solid angle = 2π × (1 - cos(cone_angle))
        # For our hexagon... this gets complicated
        
        return turn  # Placeholder
    
    # =========================================================================
    # TEST DIFFERENT MODELS
    # =========================================================================
    
    def test_transport_model(self, junction_ids: List[int], model_name: str) -> Dict:
        """
        Test a transport model around the loop.
        """
        n = len(junction_ids)
        total_phase = 0.0
        total_turn = 0.0
        
        for i in range(n):
            jid = junction_ids[i]
            prev_jid = junction_ids[(i - 1) % n]
            next_jid = junction_ids[(i + 1) % n]
            
            junction = self.junctions[jid]
            
            # Find branches
            in_branch = None
            out_branch = None
            
            for bid in junction.branches:
                if self._branch_points_toward(jid, bid, prev_jid):
                    in_branch = bid
                if self._branch_points_toward(jid, bid, next_jid):
                    out_branch = bid
            
            if in_branch is None or out_branch is None:
                continue
            
            # Compute turning angle
            turn = self.compute_turning_angle(in_branch, out_branch)
            total_turn += turn
            
            # Compute phase based on model
            if model_name == "A_direct":
                phase = self.transport_phase_model_A(turn)
            elif model_name == "B_half":
                phase = self.transport_phase_model_B(turn)
            elif model_name == "C_projection":
                phase = self.transport_phase_model_C_projection(in_branch, out_branch)
            else:
                phase = turn
            
            total_phase += phase
        
        # Compute holonomy
        holonomy = np.exp(1j * total_phase)
        
        return {
            'model': model_name,
            'total_turning_deg': np.degrees(total_turn),
            'total_phase_deg': np.degrees(total_phase),
            'holonomy_real': holonomy.real,
            'holonomy_imag': holonomy.imag,
            'is_fermion': np.isclose(holonomy, -1, atol=0.1),
            'is_boson': np.isclose(holonomy, 1, atol=0.1)
        }


# =============================================================================
# THE REAL DERIVATION TEST
# =============================================================================

class EmergentBerryPhaseTest:
    """
    Test whether the 1/2 factor EMERGES from junction geometry.
    """
    
    def __init__(self):
        self.results = {}
    
    def test_basic_turning(self) -> Dict:
        """
        TEST 1: What is the total turning angle around a hexagon?
        """
        print("=" * 70)
        print("TEST 1: BASIC TURNING GEOMETRY")
        print("=" * 70)
        print("""
For a regular hexagon traversed counterclockwise:
  - External angle at each vertex = 60°
  - Total external turning = 6 × 60° = 360° = 2π

This is a fundamental geometric fact.
""")
        
        network = BranchTransportNetwork()
        jids = network.create_hexagonal_loop()
        
        total_turning = network.compute_total_turning_around_loop(jids)
        
        print(f"Total turning around hexagon: {np.degrees(total_turning):.1f}°")
        print(f"Expected: 360°")
        print(f"Match: {np.isclose(total_turning, 2*np.pi, atol=0.3)}")
        
        return {'total_turning_deg': np.degrees(total_turning)}
    
    def test_transport_models(self) -> Dict:
        """
        TEST 2: Compare different transport models.
        
        Which one naturally gives fermion holonomy?
        """
        print("\n" + "=" * 70)
        print("TEST 2: TRANSPORT MODEL COMPARISON")
        print("=" * 70)
        print("""
Model A: phase = turning angle (directly)
         If total turn = 2π → phase = 2π → holonomy = +1 (boson)

Model B: phase = turning angle / 2
         If total turn = 2π → phase = π → holonomy = -1 (fermion)

Which model is NATURAL from Y-junction geometry?
""")
        
        network = BranchTransportNetwork()
        jids = network.create_hexagonal_loop()
        
        results = []
        
        print(f"\n{'Model':>15} | {'Total Turn':>12} | {'Total Phase':>12} | {'Holonomy':>15} | {'Type':>8}")
        print("-" * 75)
        
        for model in ["A_direct", "B_half"]:
            result = network.test_transport_model(jids, model)
            
            hol_str = f"{result['holonomy_real']:.2f}+{result['holonomy_imag']:.2f}i"
            type_str = "FERMION" if result['is_fermion'] else ("BOSON" if result['is_boson'] else "OTHER")
            
            print(f"{model:>15} | {result['total_turning_deg']:>11.1f}° | "
                  f"{result['total_phase_deg']:>11.1f}° | {hol_str:>15} | {type_str:>8}")
            
            results.append(result)
        
        return results
    
    def test_why_half(self) -> Dict:
        """
        TEST 3: WHY would phase = 1/2 × turning be natural?
        
        This is the key derivation question.
        """
        print("\n" + "=" * 70)
        print("TEST 3: WHY WOULD 1/2 EMERGE?")
        print("=" * 70)
        print("""
The 1/2 factor must come from SOMETHING in the Y-junction geometry.
Let's examine what's special about 120° branch separation.

At each Y-junction:
  - 3 branches at 120° separation
  - Adjacent branch angle = 120°
  - cos(120°) = -0.5
  - |cos(120°)| = 0.5

HYPOTHESIS 1: Projection factor
  When signal moves from one branch to another,
  it projects onto the new direction.
  Projection = cos(angle) = -0.5
  But this doesn't directly give phase = 1/2 × turn

HYPOTHESIS 2: Solid angle / 2
  In spin-1/2 physics, Berry phase = solid_angle / 2
  For our hexagon, if we consider it as bounding a surface...
  Solid angle of flat hexagon = 2π (steradians)
  Berry phase = 2π / 2 = π → holonomy = -1
  
  This DOES give the right answer!

HYPOTHESIS 3: Double-cover from path space
  The path space has a double cover.
  Going around once in real space = going around half in phase space.
  This is abstract but might be derivable.
""")
        
        # Test projection at Y-junction
        branch_sep = 120  # degrees
        projection = np.cos(np.radians(branch_sep))
        
        print(f"\nY-junction branch separation: {branch_sep}°")
        print(f"Projection factor: cos({branch_sep}°) = {projection:.4f}")
        print(f"|Projection|: {abs(projection):.4f}")
        
        # For hexagon as bounding surface
        print(f"\nSolid angle interpretation:")
        print(f"  Flat hexagon bounds solid angle = 2π (half of sphere)")
        print(f"  Spin-1/2 Berry phase = solid_angle / 2 = π")
        print(f"  Holonomy = e^(iπ) = -1 ✓")
        
        return {
            'branch_separation': branch_sep,
            'projection': projection,
            'solid_angle_argument': 'Berry phase = Ω/2 for spin-1/2'
        }
    
    def test_solid_angle_derivation(self) -> Dict:
        """
        TEST 4: Solid angle derivation.
        
        The Berry phase for a spin-s particle going around a loop
        enclosing solid angle Ω is:
        
            θ_Berry = s × Ω
        
        For spin-1/2: θ_Berry = Ω/2
        
        For a flat loop (like our hexagon), the solid angle subtended
        at the center is 2π steradians (half of 4π sphere).
        
        Therefore: θ_Berry = 2π/2 = π → holonomy = -1 (fermion)
        
        THE QUESTION: Can this be derived from Y-junction rules?
        """
        print("\n" + "=" * 70)
        print("TEST 4: SOLID ANGLE DERIVATION")
        print("=" * 70)
        print("""
KEY INSIGHT from differential geometry:

For a spin-1/2 particle parallel-transported around a loop:
    θ_Berry = (1/2) × Ω

Where Ω is the solid angle enclosed by the loop.

For a FLAT loop in 2D (like our hexagon):
    Ω = 2π steradians (half the sphere)

Therefore:
    θ_Berry = (1/2) × 2π = π
    Holonomy = e^(iπ) = -1 ✓ FERMION!

This is the STANDARD derivation of spinor holonomy.

THE QMRT QUESTION:
    Does Y-junction geometry NATURALLY implement spin-1/2 transport?
    
    If each junction contributes solid angle Ω_j,
    and Ω_j = (total turning at junction) somehow...
    
    For hexagon:
        Total turning = 2π
        If spin = 1/2: phase = π
        
    The 1/2 factor comes from SPIN VALUE, not from geometry!
""")
        
        # The solid angle argument
        solid_angle = 2 * np.pi  # For flat loop
        spin = 0.5
        berry_phase = spin * solid_angle
        holonomy = np.exp(1j * berry_phase)
        
        print(f"\nSolid angle of flat hexagon: {solid_angle:.4f} rad = {np.degrees(solid_angle):.1f}°")
        print(f"Spin value: {spin}")
        print(f"Berry phase = spin × Ω = {berry_phase:.4f} rad = {np.degrees(berry_phase):.1f}°")
        print(f"Holonomy = e^(i×{berry_phase:.4f}) = {holonomy.real:.3f} + {holonomy.imag:.3f}i")
        print(f"Is fermion: {np.isclose(holonomy, -1)}")
        
        return {
            'solid_angle': solid_angle,
            'spin': spin,
            'berry_phase': berry_phase,
            'holonomy': holonomy,
            'is_fermion': np.isclose(holonomy, -1)
        }
    
    def test_y_junction_spin_value(self) -> Dict:
        """
        TEST 5: Does Y-junction geometry IMPLY spin = 1/2?
        
        This is the key derivation we need.
        """
        print("\n" + "=" * 70)
        print("TEST 5: DOES Y-JUNCTION IMPLY SPIN = 1/2?")
        print("=" * 70)
        print("""
THE CRITICAL QUESTION:

We know that spin-1/2 gives: phase = (1/2) × turning

But can we DERIVE spin = 1/2 from Y-junction structure?

CANDIDATE DERIVATION:

Y-junction has 3 branches at 120° separation.
The "spin" might be related to the symmetry:
    - Z₃ symmetry (3-fold)
    - 120° = 360° / 3

Consider: what "spin" is consistent with 3-fold symmetry?

For spin-s, rotation by angle θ gives phase s×θ.
For 120° rotation to give trivial phase (as required by Z₃ symmetry):
    s × 120° = n × 360° for some integer n
    s = 3n

So Z₃ symmetry requires spin = 0, 3, 6, ... (integers mult of 3)

That's NOT spin-1/2!

ALTERNATIVE: The 1/2 comes from DOUBLE COVER, not Z₃.

The Y-junction has a SIGN structure (±1).
Alternating signs create a Z₂ quotient on top of Z₃.
The combination (Z₃ × Z₂) / some relation might give effective spin-1/2.

Let me check: with alternating signs around the hexagon:
    Product of 6 alternating signs = (-1)^3 = -1
    
This -1 factor COMBINED with phase transport gives fermion!
""")
        
        # Check sign product
        signs = [1, -1, 1, -1, 1, -1]  # Alternating
        sign_product = np.prod(signs)
        
        print(f"\nAlternating signs: {signs}")
        print(f"Sign product: {sign_product}")
        
        # The holonomy has two parts:
        # 1. Phase from turning (needs to give +1 or -1 depending on spin)
        # 2. Sign from junction signs
        
        # If phase transport gives +1 (boson) and signs give -1:
        #   Total holonomy = (+1) × (-1) = -1 → FERMION
        
        # If phase transport gives -1 (fermion) and signs give +1:
        #   Total holonomy = (-1) × (+1) = -1 → FERMION
        
        # With ALTERNATING signs (6 of them):
        #   sign_product = -1
        
        # If phase around loop = 0 (trivial transport):
        #   holonomy = 1 × (-1) = -1 → FERMION!
        
        # This is DIFFERENT from the spin-1/2 explanation!
        
        print(f"""
IMPORTANT REALIZATION:

The fermion holonomy in QMRT comes from TWO sources:

1. Phase transport around loop → some phase factor
2. Sign structure (alternating ±1) → product = -1

If phase transport gives holonomy +1 (trivial),
and sign structure gives -1,
then TOTAL holonomy = -1 (fermion).

The "1/2 factor" may be MISATTRIBUTED.

Actually, in the branch model we tested earlier:
    - Loop gives -1 from SIGNS alone
    - No spin-1/2 parallel transport needed!

This is a DIFFERENT mechanism from Berry phase!
""")
        
        return {
            'z3_compatible_spins': [0, 3, 6],
            'sign_product': sign_product,
            'mechanism': 'Sign structure, not Berry phase spin-1/2'
        }
    
    def run_all_tests(self) -> Dict:
        """Run all emergence tests."""
        print("=" * 80)
        print("  QMRT: EMERGENT BERRY PHASE TEST")
        print("=" * 80)
        print("""
THE QUESTION:
    Does the 1/2 factor EMERGE from Y-junction geometry,
    or is it inserted manually?

APPROACH:
    1. Compute total turning around hexagon
    2. Test different phase transport models
    3. Analyze why 1/2 might emerge
    4. Check solid angle / Berry phase argument
    5. Examine if Y-junction implies spin-1/2
""")
        
        results = {}
        
        results['turning'] = self.test_basic_turning()
        results['models'] = self.test_transport_models()
        results['why_half'] = self.test_why_half()
        results['solid_angle'] = self.test_solid_angle_derivation()
        results['spin_value'] = self.test_y_junction_spin_value()
        
        # Final analysis
        print("\n" + "=" * 80)
        print("FINAL ANALYSIS")
        print("=" * 80)
        
        print("""
CONCLUSION:

The fermion holonomy in QMRT can arise from TWO distinct mechanisms:

MECHANISM 1: Spin-1/2 Berry Phase
    - Phase = (1/2) × total_turning
    - Requires: spin value s = 1/2 built into transport
    - This INSERTS the 1/2 factor (not truly emergent)

MECHANISM 2: Sign Structure (Z₂)
    - Alternating junction signs: +1, -1, +1, -1, +1, -1
    - Sign product = (-1)^3 = -1
    - Phase transport can be trivial (holonomy = +1)
    - Total holonomy = phase × sign = (+1) × (-1) = -1

MECHANISM 2 is what we already tested and found working!

The 1/2 factor for ROTATION coupling is a SEPARATE question:
    - Rotation changes orientation of the whole structure
    - This IS equivalent to Berry phase
    - For flat 2D structure, solid angle = 2π
    - Berry phase = (1/2) × 2π = π for spin-1/2

So the honest statement is:

"QMRT produces fermion loop holonomy via the Z₂ sign structure,
without requiring spin-1/2 transport. The rotation behavior
(360° → -1) requires an ADDITIONAL geometric coupling that
implements effective spin-1/2 parallel transport."
""")
        
        # Save
        output = {
            'test': 'Emergent_Berry_Phase',
            'turning_geometry': results['turning'],
            'transport_models': results['models'],
            'why_half_analysis': results['why_half'],
            'solid_angle_derivation': results['solid_angle'],
            'spin_value_analysis': results['spin_value'],
            'conclusion': {
                'mechanism_1': 'Berry phase spin-1/2 (requires inserting 1/2)',
                'mechanism_2': 'Z₂ sign structure (naturally gives -1)',
                'loop_holonomy_source': 'Sign structure (proven)',
                'rotation_behavior_source': 'Berry phase (requires assumption)'
            }
        }
        
        output_path = '/app/backend/qmrt_topology/emergent_berry_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = EmergentBerryPhaseTest()
    results = test.run_all_tests()
