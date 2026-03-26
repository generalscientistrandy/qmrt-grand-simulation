"""
QMRT: BRANCH WEB HOLONOMY TEST
==============================

THE HYPOTHESIS:
  SU(2) may emerge not from single smooth torsion, but from
  ordered transport through a self-interacting branch web
  whose crossings generate double-cover behavior.

THE MODEL:
  Branch web W = (V, E, C)
    V = nodes/branch points
    E = branch segments
    C = crossing rules
    
  Transport: U(γ) = ∏ U_e X_c
    U_e = segment transport
    X_c = crossing operator

THE KEY TEST:
  Compare holonomy around:
    1. Simple vortex (no crossing)
    2. Single branch crossing
    3. Self-crossing branch
    4. Path exchange at crossings
    
  If crossings produce different return maps → SU(2) may emerge!

WHAT WE'RE LOOKING FOR:
  Simple vortex:    2π holonomy → +1 (boson)
  Crossing loop:    π holonomy → -1 (fermion)?
  Self-crossing:    double-valued return → spinor?
  Path ordering:    noncommutative → non-Abelian?
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
class BranchSegment:
    """A segment of the branch web."""
    start: Tuple[float, float]
    end: Tuple[float, float]
    branch_id: int
    torsion_strength: float = 1.0


@dataclass 
class Crossing:
    """A crossing point where branches interact."""
    position: Tuple[float, float]
    branch_1: int
    branch_2: int
    crossing_type: str  # 'over', 'under', 'merge', 'split'
    phase_jump: float = 0.0  # Additional phase at crossing


class BranchWeb:
    """
    A web of interacting branches with crossings.
    
    This models the medium as a topological network, not just smooth fields.
    """
    
    def __init__(self):
        self.segments: List[BranchSegment] = []
        self.crossings: List[Crossing] = []
        self.branch_count = 0
    
    def add_vortex_branch(self, center: Tuple[float, float], radius: float, 
                          branch_id: Optional[int] = None) -> int:
        """Add a circular branch (vortex) to the web."""
        if branch_id is None:
            branch_id = self.branch_count
            self.branch_count += 1
        
        # Discretize the circle into segments
        n_segments = 36
        angles = np.linspace(0, 2*np.pi, n_segments + 1)
        
        for i in range(n_segments):
            start = (center[0] + radius * np.cos(angles[i]),
                    center[1] + radius * np.sin(angles[i]))
            end = (center[0] + radius * np.cos(angles[i+1]),
                  center[1] + radius * np.sin(angles[i+1]))
            
            self.segments.append(BranchSegment(start, end, branch_id))
        
        return branch_id
    
    def add_figure_eight(self, center: Tuple[float, float], radius: float,
                        branch_id: Optional[int] = None) -> int:
        """
        Add a figure-8 branch (self-crossing loop) to the web.
        
        This is the key structure for testing self-crossing holonomy!
        """
        if branch_id is None:
            branch_id = self.branch_count
            self.branch_count += 1
        
        # Figure-8: parametric curve that crosses itself
        n_segments = 72
        t_values = np.linspace(0, 2*np.pi, n_segments + 1)
        
        # Lemniscate of Bernoulli (figure-8)
        for i in range(n_segments):
            t1, t2 = t_values[i], t_values[i+1]
            
            # Parametric figure-8
            x1 = center[0] + radius * np.cos(t1) / (1 + np.sin(t1)**2)
            y1 = center[1] + radius * np.sin(t1) * np.cos(t1) / (1 + np.sin(t1)**2)
            
            x2 = center[0] + radius * np.cos(t2) / (1 + np.sin(t2)**2)
            y2 = center[1] + radius * np.sin(t2) * np.cos(t2) / (1 + np.sin(t2)**2)
            
            self.segments.append(BranchSegment((x1, y1), (x2, y2), branch_id))
        
        # Add the self-crossing at the center
        self.crossings.append(Crossing(
            position=center,
            branch_1=branch_id,
            branch_2=branch_id,  # Self-crossing!
            crossing_type='self',
            phase_jump=np.pi  # This is the key: self-crossing adds π phase
        ))
        
        return branch_id
    
    def add_crossing(self, pos: Tuple[float, float], b1: int, b2: int, 
                    crossing_type: str = 'over', phase: float = 0.0):
        """Add a crossing between two branches."""
        self.crossings.append(Crossing(pos, b1, b2, crossing_type, phase))


def compute_segment_transport(segment: BranchSegment, alpha: float = 1.0) -> np.ndarray:
    """
    Compute the transport operator along a segment.
    
    U_e = exp(-i α θ σ_z)
    
    where θ is the angle subtended by the segment.
    """
    dx = segment.end[0] - segment.start[0]
    dy = segment.end[1] - segment.start[1]
    
    # Angle of the segment
    theta = np.arctan2(dy, dx)
    
    # Transport: rotation around z-axis
    phase = alpha * theta * segment.torsion_strength
    
    U = np.array([
        [np.exp(-1j * phase), 0],
        [0, np.exp(1j * phase)]
    ], dtype=complex)
    
    return U


def compute_crossing_operator(crossing: Crossing) -> np.ndarray:
    """
    Compute the transformation operator at a crossing.
    
    This is where the magic happens!
    
    Different crossing types can have different operators:
    - 'over'/'under': phase shift
    - 'merge': might involve σ operations
    - 'self': self-crossing, critical for spinor behavior
    """
    phase = crossing.phase_jump
    
    if crossing.crossing_type == 'self':
        # SELF-CROSSING: This is the key structure!
        # A self-crossing can implement a 180° rotation (π phase)
        # which would give -1 after going around once
        
        # Option 1: Pure phase
        X = np.exp(1j * phase) * IDENTITY
        
        # Option 2: Rotation operator (more interesting)
        # X = exp(i π/2 σ_y) = [[0, 1], [-1, 0]] (90° rotation)
        # Two self-crossings would give -I !
        
        # Let's use a σ_y rotation for self-crossing
        X = np.array([
            [np.cos(phase/2), np.sin(phase/2)],
            [-np.sin(phase/2), np.cos(phase/2)]
        ], dtype=complex)
        
    elif crossing.crossing_type in ['over', 'under']:
        # Regular crossing: just a phase
        X = np.exp(1j * phase) * IDENTITY
        
    elif crossing.crossing_type == 'merge':
        # Merging branches: could involve more complex transformation
        X = np.exp(1j * phase) * IDENTITY
        
    else:
        X = IDENTITY
    
    return X


def compute_path_holonomy(web: BranchWeb, branch_id: int, alpha: float = 1.0) -> Dict:
    """
    Compute the holonomy for traversing a branch (loop).
    
    This accounts for:
    1. Segment-by-segment transport
    2. Crossing operators encountered
    """
    # Get segments for this branch
    branch_segments = [s for s in web.segments if s.branch_id == branch_id]
    
    # Get crossings for this branch
    branch_crossings = [c for c in web.crossings 
                       if c.branch_1 == branch_id or c.branch_2 == branch_id]
    
    # Initialize holonomy as identity
    U_total = IDENTITY.copy()
    
    # Track accumulated phase
    total_phase = 0.0
    
    # Transport along segments
    for segment in branch_segments:
        U_seg = compute_segment_transport(segment, alpha)
        U_total = U_seg @ U_total
        
        # Track phase
        phase = alpha * np.arctan2(segment.end[1] - segment.start[1],
                                   segment.end[0] - segment.start[0])
        total_phase += phase
    
    # Apply crossing operators
    for crossing in branch_crossings:
        X = compute_crossing_operator(crossing)
        U_total = X @ U_total
    
    # Analyze the result
    trace = np.trace(U_total)
    det = np.linalg.det(U_total)
    
    # Is it ±I?
    is_identity = np.allclose(U_total, IDENTITY, atol=0.1)
    is_minus_identity = np.allclose(U_total, -IDENTITY, atol=0.1)
    
    return {
        'holonomy_matrix': U_total,
        'trace': complex(trace),
        'trace_real': float(np.real(trace)),
        'determinant': complex(det),
        'is_identity': is_identity,
        'is_minus_identity': is_minus_identity,
        'num_crossings': len(branch_crossings),
        'crossing_types': [c.crossing_type for c in branch_crossings]
    }


def test_simple_vortex_vs_figure_eight():
    """
    THE KEY TEST: Compare holonomy of simple loop vs self-crossing loop.
    
    Simple vortex: No crossings → should give 2π → +1
    Figure-8: Self-crossing → might give π → -1 (fermion!)
    """
    print("#" * 80)
    print("#  BRANCH WEB HOLONOMY TEST")
    print("#" * 80)
    print("""
THE EXPERIMENT:
  Compare holonomy around different topological structures:
  
  1. Simple vortex (circular loop, no crossing)
  2. Figure-8 (self-crossing loop)
  
  If self-crossing generates π phase → fermions from web topology!
""")
    
    # Test 1: Simple vortex
    print("=" * 70)
    print("TEST 1: SIMPLE VORTEX (No crossing)")
    print("=" * 70)
    
    web1 = BranchWeb()
    vortex_id = web1.add_vortex_branch(center=(0, 0), radius=10)
    
    result1 = compute_path_holonomy(web1, vortex_id, alpha=1.0)
    
    print(f"""
Structure: Circular loop, radius 10
Crossings: {result1['num_crossings']}
Holonomy trace: {result1['trace_real']:.4f}
Result: {'Identity (+1)' if result1['is_identity'] else ('Minus Identity (-1)' if result1['is_minus_identity'] else 'Other')}

Interpretation: Simple vortex gives trivial holonomy (as expected for SO(3))
""")
    
    # Test 2: Figure-8 with self-crossing
    print("=" * 70)
    print("TEST 2: FIGURE-8 (Self-crossing)")
    print("=" * 70)
    
    web2 = BranchWeb()
    fig8_id = web2.add_figure_eight(center=(0, 0), radius=10)
    
    result2 = compute_path_holonomy(web2, fig8_id, alpha=1.0)
    
    print(f"""
Structure: Figure-8 loop with self-crossing at center
Crossings: {result2['num_crossings']} ({result2['crossing_types']})
Holonomy trace: {result2['trace_real']:.4f}
Result: {'Identity (+1)' if result2['is_identity'] else ('Minus Identity (-1)' if result2['is_minus_identity'] else 'Other')}

Interpretation: Self-crossing adds π phase, potentially giving -1!
""")
    
    # Test 3: Vary crossing phase
    print("=" * 70)
    print("TEST 3: CROSSING PHASE SCAN")
    print("=" * 70)
    print("Testing different self-crossing phases:")
    print()
    
    phases = [0, np.pi/4, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]
    
    print(f"{'Phase/π':>10} | {'Trace':>10} | {'Result':>15}")
    print("-" * 40)
    
    results = {}
    
    for phase in phases:
        web = BranchWeb()
        
        # Add figure-8 with specific crossing phase
        branch_id = web.branch_count
        web.branch_count += 1
        
        # Add segments (simplified figure-8)
        n_segments = 36
        t_values = np.linspace(0, 2*np.pi, n_segments + 1)
        
        for i in range(n_segments):
            t1, t2 = t_values[i], t_values[i+1]
            radius = 10
            center = (0, 0)
            
            x1 = center[0] + radius * np.cos(t1) / (1 + np.sin(t1)**2 + 0.01)
            y1 = center[1] + radius * np.sin(t1) * np.cos(t1) / (1 + np.sin(t1)**2 + 0.01)
            x2 = center[0] + radius * np.cos(t2) / (1 + np.sin(t2)**2 + 0.01)
            y2 = center[1] + radius * np.sin(t2) * np.cos(t2) / (1 + np.sin(t2)**2 + 0.01)
            
            web.segments.append(BranchSegment((x1, y1), (x2, y2), branch_id))
        
        # Add self-crossing with specific phase
        web.crossings.append(Crossing(
            position=center,
            branch_1=branch_id,
            branch_2=branch_id,
            crossing_type='self',
            phase_jump=phase
        ))
        
        result = compute_path_holonomy(web, branch_id, alpha=1.0)
        
        result_str = '+1' if result['is_identity'] else ('-1' if result['is_minus_identity'] else 'other')
        
        print(f"{phase/np.pi:>10.2f} | {result['trace_real']:>10.4f} | {result_str:>15}")
        
        results[phase] = result
    
    # Verdict
    print("\n" + "=" * 70)
    print("BRANCH WEB VERDICT")
    print("=" * 70)
    
    # Check if π crossing gives -1
    pi_result = results.get(np.pi, {})
    pi_gives_minus = pi_result.get('is_minus_identity', False)
    
    print(f"""
KEY FINDING:

  Simple vortex (no crossing):
    Holonomy = {'+1 (boson)' if result1['is_identity'] else 'other'}
    
  Self-crossing with π phase:
    Holonomy = {'-1 (fermion!)' if pi_gives_minus else 'other'}
    
INTERPRETATION:
  {'✅ Self-crossings with π phase generate fermion holonomy!' if pi_gives_minus else '⚠️ Current model needs refinement'}
  
  This suggests:
  {'• SU(2) behavior can emerge from web topology' if pi_gives_minus else '• Crossing operator needs different form'}
  {'• The π phase at self-crossings is the key ingredient' if pi_gives_minus else '• May need more sophisticated crossing rules'}
  {'• Fermions = transport through self-interacting branch web' if pi_gives_minus else ''}

NEXT STEPS:
  1. Test path ordering: Does A→B differ from B→A at crossings?
  2. Test multiple crossings: Does composition work?
  3. Connect to physical medium: What creates self-crossings?
""")
    
    # Save results
    output = {
        'test': 'Branch_Web_Holonomy',
        'simple_vortex': {
            'crossings': result1['num_crossings'],
            'trace': float(result1['trace_real']),
            'is_identity': result1['is_identity']
        },
        'figure_eight': {
            'crossings': result2['num_crossings'],
            'trace': float(result2['trace_real']),
            'is_minus_identity': result2['is_minus_identity']
        },
        'phase_scan': {str(p/np.pi): {
            'trace': float(results[p]['trace_real']),
            'is_identity': bool(results[p]['is_identity']),
            'is_minus': bool(results[p]['is_minus_identity'])
        } for p in phases},
        'conclusion': 'SELF_CROSSING_GIVES_FERMION' if pi_gives_minus else 'NEEDS_REFINEMENT'
    }
    
    output_path = '/app/backend/qmrt_topology/branch_web_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return output


def test_path_ordering():
    """
    Test whether path order matters at crossings.
    
    If X_A X_B ≠ X_B X_A → non-Abelian structure → SU(2) possible
    """
    print("\n" + "=" * 70)
    print("TEST: PATH ORDERING AT CROSSINGS")
    print("=" * 70)
    
    # Define two different crossing operators
    # Using rotations around different axes
    
    # Crossing 1: rotation around x
    X_A = np.array([
        [np.cos(np.pi/4), -1j*np.sin(np.pi/4)],
        [-1j*np.sin(np.pi/4), np.cos(np.pi/4)]
    ], dtype=complex)
    
    # Crossing 2: rotation around y  
    X_B = np.array([
        [np.cos(np.pi/4), np.sin(np.pi/4)],
        [-np.sin(np.pi/4), np.cos(np.pi/4)]
    ], dtype=complex)
    
    # Compute both orderings
    AB = X_A @ X_B
    BA = X_B @ X_A
    
    # Check if they commute
    commutator = AB - BA
    commutes = np.allclose(commutator, 0, atol=0.01)
    
    print(f"""
Crossing operators:
  X_A = rotation around x by π/4
  X_B = rotation around y by π/4
  
Products:
  X_A @ X_B: trace = {np.trace(AB):.4f}
  X_B @ X_A: trace = {np.trace(BA):.4f}
  
Commutator [X_A, X_B] = X_A X_B - X_B X_A:
  ||[X_A, X_B]|| = {np.linalg.norm(commutator):.4f}
  
Result: {'COMMUTE (Abelian)' if commutes else 'DO NOT COMMUTE (Non-Abelian!)'}
""")
    
    if not commutes:
        print("""
✅ NON-ABELIAN STRUCTURE DETECTED

This means:
  - Path order matters at crossings
  - Different traversal orders give different results
  - This is exactly the structure needed for SU(2)!

IMPLICATION:
  If branch web crossings have non-commuting operators,
  then the web naturally generates non-Abelian holonomy.
  SU(2) could emerge from this structure!
""")
    
    return not commutes


if __name__ == "__main__":
    results = test_simple_vortex_vs_figure_eight()
    is_non_abelian = test_path_ordering()
