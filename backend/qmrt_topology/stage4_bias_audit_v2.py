"""
QMRT STAGE 4 BIAS AUDIT V2 — GEOMETRIC STABILITY DERIVATION
=============================================================

The V1 audit revealed a critical issue: the original Stage 4C used explicit
sector-dependent decay rates, which is algorithmic bias.

This V2 audit implements the CORRECT approach:
- Stability emerges from GEOMETRIC COHERENCE of the holonomy
- NO explicit sector classification during evolution
- Structures with holonomy ≈ ±1 are more stable because they represent
  PHASE-CLOSED loops (returning to the same geometric state)

The key physics insight:
- Holonomy = e^(iφ) where φ is the accumulated transport phase
- Phase-closed: φ = 0 (mod 2π) → holonomy = 1 (boson)
- Phase-antiperiodic: φ = π (mod 2π) → holonomy = -1 (fermion)
- Incoherent: φ random → holonomy scattered

The GEOMETRIC stability should come from:
1. Phase coherence: how close is |holonomy| to 1?
2. Phase closure: how close is holonomy to ±1?
3. The Y-junction geometry naturally produces -1 for hexagonal loops

The question is: does phase closure at -1 give MORE stability than at +1?

From the formal theorem (gauge_obstruction_test.py):
- Holonomy -1 is TOPOLOGICALLY PROTECTED
- The Y-junction geometry SELECTS the -1 sector
- This is not arbitrary — it's geometric selection

The implementation:
- Stability = f(holonomy) where f is derived from geometric coherence
- f(h) should peak at h = ±1
- But the GEOMETRY (Y-junction angles) favors reaching h = -1

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum
import json
import time as timer


# =============================================================================
# CONFIGURATION
# =============================================================================

BASELINE_CONFIG = {
    'grid_size': 15,
    'timesteps': 3000,
    'node_density': 0.4,
    'edge_probability': 0.25,
    'noise_amplitude': 0.05,
    'decay_base_rate': 0.01,
    'runs_per_test': 12,
    'stability_threshold': 50,
}


class Sector(Enum):
    FERMIONIC = "F"
    BOSONIC = "B"
    ANYONIC = "A"
    UNCLASSIFIED = "U"


def classify_holonomy(holonomy: complex) -> Sector:
    """POST-HOC classification only."""
    if abs(holonomy + 1) < 0.3:
        return Sector.FERMIONIC
    elif abs(holonomy - 1) < 0.3:
        return Sector.BOSONIC
    elif abs(abs(holonomy) - 1) < 0.1:
        return Sector.ANYONIC
    return Sector.UNCLASSIFIED


# =============================================================================
# GEOMETRIC STABILITY FUNCTION — THE CRITICAL DERIVATION
# =============================================================================

def compute_geometric_stability(holonomy: complex, loop_size: int) -> float:
    """
    Compute stability from GEOMETRY ONLY.
    
    This is the key function. It must:
    1. Give high stability to phase-coherent states (|h| ≈ 1)
    2. NOT explicitly prefer -1 over +1
    3. Let the GEOMETRY (Y-junction transport) determine which states form
    
    The geometric stability comes from:
    - Unit circle proximity: stable states have |h| = 1
    - Phase coherence: how "clean" is the holonomy?
    
    CRITICAL: This function treats h = +1 and h = -1 EQUALLY.
    The selection of fermions (if it occurs) must come from the
    Y-junction transport rule, not from this stability function.
    """
    # 1. Unit circle proximity — all stable states have |h| ≈ 1
    magnitude = abs(holonomy)
    magnitude_stability = np.exp(-10 * (magnitude - 1)**2)
    
    # 2. Phase coherence — clean phase (0 or π) is more stable
    # This gives EQUAL weight to h = +1 and h = -1
    phase = np.angle(holonomy)
    phase_coherence = np.cos(phase)**2  # Peaks at 0 and π equally
    
    # 3. Size factor — smaller loops slightly more stable
    size_factor = np.exp(-0.05 * loop_size)
    
    # Combined stability
    stability = magnitude_stability * (0.3 + 0.7 * phase_coherence) * size_factor
    
    return stability


def compute_biased_stability(holonomy: complex, loop_size: int, 
                            fermionic_boost: float = 4.0) -> float:
    """
    BIASED stability function (for comparison).
    
    This explicitly boosts fermionic structures.
    Use this to compare against the unbiased version.
    """
    base_stability = compute_geometric_stability(holonomy, loop_size)
    
    # Explicit fermionic boost (THIS IS BIAS)
    if abs(holonomy + 1) < 0.3:
        return base_stability * fermionic_boost
    elif abs(holonomy - 1) < 0.3:
        return base_stability / fermionic_boost
    
    return base_stability


# =============================================================================
# Y-JUNCTION TRANSPORT — THE PHYSICS
# =============================================================================

def yjunction_transport_phase(turn_angle: float) -> float:
    """
    Y-junction transport rule.
    
    When traversing a Y-junction with turn angle θ:
    - The spinor transport gives phase = -θ/2
    
    This is the PHYSICS — it's not arbitrary.
    The factor of 1/2 comes from spinor geometry on the Bloch sphere.
    """
    return -turn_angle / 2


def compute_loop_holonomy(positions: List[Tuple[float, float]]) -> complex:
    """
    Compute holonomy around a loop using Y-junction transport.
    
    For a polygon with n vertices:
    - Each vertex contributes phase = -turn_angle/2
    - Total phase = -Σ(turn_angles)/2
    - For a closed polygon: Σ(turn_angles) = ±2π (depending on orientation)
    - So holonomy = e^(i*(-±2π/2)) = e^(∓iπ) = -1
    
    This is why HEXAGONS get holonomy = -1:
    - 6 turns of 60° each (exterior angles)
    - Total = 360° = 2π
    - Phase = -π
    - Holonomy = e^(-iπ) = -1
    """
    n = len(positions)
    total_phase = 0.0
    
    for i in range(n):
        prev = positions[(i - 1) % n]
        curr = positions[i]
        next_p = positions[(i + 1) % n]
        
        # Incoming and outgoing directions
        angle_in = np.arctan2(curr[1] - prev[1], curr[0] - prev[0])
        angle_out = np.arctan2(next_p[1] - curr[1], next_p[0] - curr[0])
        
        # Turn angle
        turn = angle_out - angle_in
        while turn > np.pi:
            turn -= 2 * np.pi
        while turn < -np.pi:
            turn += 2 * np.pi
        
        # Y-junction transport
        total_phase += yjunction_transport_phase(turn)
    
    return np.exp(1j * total_phase)


# =============================================================================
# SIMULATION WITH GEOMETRIC STABILITY
# =============================================================================

class GeometricMedium:
    """Medium with proper Y-junction geometry."""
    
    def __init__(self, size: int, config: Dict):
        self.size = size
        self.config = config
        self.nodes: Dict[int, Dict] = {}
        self.edges: Dict[int, Dict] = {}
        self.next_node_id = 0
        self.next_edge_id = 0
    
    def initialize(self):
        """Initialize with random nodes and edges."""
        num_nodes = int(self.size**2 * self.config['node_density'])
        
        for _ in range(num_nodes):
            x = np.random.uniform(0, self.size)
            y = np.random.uniform(0, self.size)
            
            self.nodes[self.next_node_id] = {
                'id': self.next_node_id,
                'x': x, 'y': y,
                'edges': [],
            }
            self.next_node_id += 1
        
        # Create edges
        node_list = list(self.nodes.values())
        connection_radius = 2.0
        
        for i, node_a in enumerate(node_list):
            for node_b in node_list[i+1:]:
                dist = np.sqrt(
                    (node_a['x'] - node_b['x'])**2 +
                    (node_a['y'] - node_b['y'])**2
                )
                
                if dist < connection_radius:
                    if np.random.random() < self.config['edge_probability']:
                        edge = {
                            'id': self.next_edge_id,
                            'node_a': node_a['id'],
                            'node_b': node_b['id']
                        }
                        self.edges[self.next_edge_id] = edge
                        node_a['edges'].append(self.next_edge_id)
                        node_b['edges'].append(self.next_edge_id)
                        self.next_edge_id += 1
    
    def find_loops(self, max_size: int = 10) -> List[List[int]]:
        """Find loops in the medium."""
        loops = []
        visited = set()
        
        adjacency = defaultdict(set)
        for edge in self.edges.values():
            adjacency[edge['node_a']].add(edge['node_b'])
            adjacency[edge['node_b']].add(edge['node_a'])
        
        start_nodes = [n for n in self.nodes if len(adjacency[n]) >= 2]
        max_loops = 200
        
        def dfs(start, current, path, depth):
            if len(loops) >= max_loops or depth > max_size:
                return
            
            for neighbor in adjacency[current]:
                if neighbor == start and len(path) >= 3:
                    loop_key = tuple(sorted(path))
                    if loop_key not in visited:
                        visited.add(loop_key)
                        loops.append(list(path))
                elif neighbor not in path and len(loops) < max_loops:
                    dfs(start, neighbor, path + [neighbor], depth + 1)
        
        for node_id in start_nodes[:60]:
            if len(loops) >= max_loops:
                break
            dfs(node_id, node_id, [node_id], 1)
        
        return loops
    
    def get_loop_positions(self, node_ids: List[int]) -> List[Tuple[float, float]]:
        """Get positions of nodes in a loop."""
        return [(self.nodes[nid]['x'], self.nodes[nid]['y']) for nid in node_ids]


@dataclass
class Structure:
    """A tracked structure."""
    id: int
    node_ids: List[int]
    holonomy: complex
    stability: float
    birth_time: int
    death_time: Optional[int] = None
    is_alive: bool = True
    
    @property
    def lifetime(self) -> int:
        return (self.death_time - self.birth_time) if self.death_time else 0


class GeometricSimulation:
    """
    Simulation with GEOMETRIC stability (no explicit sector bias).
    """
    
    def __init__(self, config: Dict, use_bias: bool = False):
        self.config = config
        self.use_bias = use_bias
        
        self.medium = GeometricMedium(config['grid_size'], config)
        self.structures: Dict[int, Structure] = {}
        self.next_id = 0
        self.known_loops: Dict[Tuple[int, ...], int] = {}
        self.time = 0
        
        # History
        self.f_fraction_history: List[float] = []
    
    def initialize(self):
        self.medium.initialize()
    
    def step(self):
        self.time += 1
        
        # Find current loops
        loops = self.medium.find_loops(max_size=10)
        current_loop_keys = set()
        
        for loop_nodes in loops:
            loop_key = tuple(sorted(loop_nodes))
            current_loop_keys.add(loop_key)
            
            if loop_key not in self.known_loops:
                # New structure
                positions = self.medium.get_loop_positions(loop_nodes)
                holonomy = compute_loop_holonomy(positions)
                
                # Compute stability (GEOMETRIC, no bias)
                if self.use_bias:
                    stability = compute_biased_stability(holonomy, len(loop_nodes))
                else:
                    stability = compute_geometric_stability(holonomy, len(loop_nodes))
                
                structure = Structure(
                    id=self.next_id,
                    node_ids=loop_nodes,
                    holonomy=holonomy,
                    stability=stability,
                    birth_time=self.time
                )
                self.structures[self.next_id] = structure
                self.known_loops[loop_key] = self.next_id
                self.next_id += 1
        
        # Apply stability-based decay
        for structure in list(self.structures.values()):
            if not structure.is_alive:
                continue
            
            # Decay rate inversely proportional to stability
            decay_rate = self.config['decay_base_rate'] / max(0.01, structure.stability)
            
            if np.random.random() < decay_rate:
                structure.death_time = self.time
                structure.is_alive = False
                loop_key = tuple(sorted(structure.node_ids))
                if loop_key in self.known_loops:
                    del self.known_loops[loop_key]
        
        # Check for disappeared loops
        for loop_key, sid in list(self.known_loops.items()):
            if loop_key not in current_loop_keys:
                if sid in self.structures and self.structures[sid].is_alive:
                    self.structures[sid].death_time = self.time
                    self.structures[sid].is_alive = False
        
        # Record F-fraction
        alive = [s for s in self.structures.values() if s.is_alive]
        if alive:
            f_count = sum(1 for s in alive if abs(s.holonomy + 1) < 0.3)
            self.f_fraction_history.append(f_count / len(alive))
        else:
            self.f_fraction_history.append(0.5)
    
    def run(self) -> Dict:
        self.initialize()
        
        for _ in range(self.config['timesteps']):
            self.step()
        
        # Post-hoc analysis
        alive = [s for s in self.structures.values() if s.is_alive]
        total = len(alive)
        
        f_count = sum(1 for s in alive if abs(s.holonomy + 1) < 0.3)
        b_count = sum(1 for s in alive if abs(s.holonomy - 1) < 0.3)
        
        f_fraction = f_count / max(1, total)
        
        # Lifetime analysis by sector
        f_lifetimes = [s.lifetime for s in self.structures.values() 
                       if s.death_time and abs(s.holonomy + 1) < 0.3]
        b_lifetimes = [s.lifetime for s in self.structures.values()
                       if s.death_time and abs(s.holonomy - 1) < 0.3]
        
        return {
            'total_alive': total,
            'f_count': f_count,
            'b_count': b_count,
            'f_fraction': f_fraction,
            'total_nucleated': len(self.structures),
            'f_fraction_history': self.f_fraction_history[-100:],
            'mean_f_lifetime': np.mean(f_lifetimes) if f_lifetimes else 0,
            'mean_b_lifetime': np.mean(b_lifetimes) if b_lifetimes else 0,
            'use_bias': self.use_bias
        }


# =============================================================================
# AUDIT TESTS
# =============================================================================

def run_geometric_vs_biased_test(config: Dict) -> Dict:
    """
    Compare geometric stability vs biased stability.
    
    If geometric stability alone produces fermionic dominance,
    then the dominance is truly emergent.
    
    If only biased stability produces it, then the original
    Stage 4C results were artifacts.
    """
    print("\n" + "=" * 60)
    print("  TEST: GEOMETRIC vs BIASED STABILITY")
    print("=" * 60)
    
    results = {'geometric': [], 'biased': []}
    
    print("\n  Running with GEOMETRIC stability (no bias)...")
    for run in range(config['runs_per_test']):
        np.random.seed(run * 7919)
        sim = GeometricSimulation(config, use_bias=False)
        res = sim.run()
        results['geometric'].append(res)
        
        if (run + 1) % 4 == 0:
            print(f"    Run {run+1}: F={res['f_count']}, B={res['b_count']}, "
                  f"F-fraction={100*res['f_fraction']:.0f}%")
    
    print("\n  Running with BIASED stability...")
    for run in range(config['runs_per_test']):
        np.random.seed(run * 7919)  # Same seeds
        sim = GeometricSimulation(config, use_bias=True)
        res = sim.run()
        results['biased'].append(res)
        
        if (run + 1) % 4 == 0:
            print(f"    Run {run+1}: F={res['f_count']}, B={res['b_count']}, "
                  f"F-fraction={100*res['f_fraction']:.0f}%")
    
    # Analysis
    geo_f_fracs = [r['f_fraction'] for r in results['geometric']]
    bias_f_fracs = [r['f_fraction'] for r in results['biased']]
    
    geo_f_lifetimes = [r['mean_f_lifetime'] for r in results['geometric']]
    geo_b_lifetimes = [r['mean_b_lifetime'] for r in results['geometric']]
    
    print(f"\n  Results:")
    print(f"    GEOMETRIC: F-fraction = {100*np.mean(geo_f_fracs):.1f}% +/- {100*np.std(geo_f_fracs):.1f}%")
    print(f"    BIASED:    F-fraction = {100*np.mean(bias_f_fracs):.1f}% +/- {100*np.std(bias_f_fracs):.1f}%")
    print(f"\n    Lifetime comparison (geometric):")
    print(f"      Fermionic: {np.mean(geo_f_lifetimes):.1f}")
    print(f"      Bosonic:   {np.mean(geo_b_lifetimes):.1f}")
    
    # Key question: does geometric stability show F-dominance?
    geo_dominant = np.mean(geo_f_fracs) > 0.55
    
    return {
        'geometric_f_fractions': geo_f_fracs,
        'biased_f_fractions': bias_f_fracs,
        'geometric_mean': np.mean(geo_f_fracs),
        'biased_mean': np.mean(bias_f_fracs),
        'geometric_shows_dominance': geo_dominant,
        'lifetime_ratio': np.mean(geo_f_lifetimes) / max(0.1, np.mean(geo_b_lifetimes))
    }


def run_holonomy_distribution_test(config: Dict) -> Dict:
    """
    Check the distribution of holonomies that FORM.
    
    The key question: does the Y-junction geometry naturally produce
    more loops with holonomy ≈ -1 than ≈ +1?
    
    This is separate from stability — it's about NUCLEATION.
    """
    print("\n" + "=" * 60)
    print("  TEST: HOLONOMY DISTRIBUTION AT NUCLEATION")
    print("=" * 60)
    
    all_holonomies = []
    f_count = 0
    b_count = 0
    a_count = 0
    
    print("\n  Collecting holonomy distribution from nucleation events...")
    
    for run in range(config['runs_per_test']):
        np.random.seed(run * 7919)
        
        medium = GeometricMedium(config['grid_size'], config)
        medium.initialize()
        
        loops = medium.find_loops(max_size=10)
        
        for loop_nodes in loops:
            positions = medium.get_loop_positions(loop_nodes)
            holonomy = compute_loop_holonomy(positions)
            all_holonomies.append(holonomy)
            
            if abs(holonomy + 1) < 0.3:
                f_count += 1
            elif abs(holonomy - 1) < 0.3:
                b_count += 1
            else:
                a_count += 1
    
    total = len(all_holonomies)
    
    print(f"\n  Holonomy distribution (at FORMATION, before any decay):")
    print(f"    Total loops: {total}")
    print(f"    Fermionic (h ≈ -1): {f_count} ({100*f_count/max(1,total):.1f}%)")
    print(f"    Bosonic (h ≈ +1):   {b_count} ({100*b_count/max(1,total):.1f}%)")
    print(f"    Anyonic (other):    {a_count} ({100*a_count/max(1,total):.1f}%)")
    
    # Phase distribution
    phases = [np.angle(h) for h in all_holonomies]
    
    near_pi = sum(1 for p in phases if abs(abs(p) - np.pi) < 0.5)
    near_zero = sum(1 for p in phases if abs(p) < 0.5)
    
    print(f"\n  Phase distribution:")
    print(f"    Near π (fermionic): {100*near_pi/max(1,total):.1f}%")
    print(f"    Near 0 (bosonic):   {100*near_zero/max(1,total):.1f}%")
    
    # Key question: does the geometry FAVOR -1?
    geometry_favors_fermions = f_count > b_count * 1.2
    
    return {
        'total_loops': total,
        'f_count': f_count,
        'b_count': b_count,
        'a_count': a_count,
        'f_fraction_at_nucleation': f_count / max(1, total),
        'b_fraction_at_nucleation': b_count / max(1, total),
        'geometry_favors_fermions': geometry_favors_fermions
    }


def run_loop_size_analysis(config: Dict) -> Dict:
    """
    Analyze holonomy by loop size.
    
    From the formal theorem:
    - Hexagons (n=6) should get holonomy = -1
    - Triangles (n=3) are trivial
    - Other sizes may have intermediate holonomies
    """
    print("\n" + "=" * 60)
    print("  TEST: HOLONOMY BY LOOP SIZE")
    print("=" * 60)
    
    size_to_holonomies: Dict[int, List[complex]] = defaultdict(list)
    
    print("\n  Collecting holonomy by loop size...")
    
    for run in range(config['runs_per_test']):
        np.random.seed(run * 7919)
        
        medium = GeometricMedium(config['grid_size'], config)
        medium.initialize()
        
        loops = medium.find_loops(max_size=10)
        
        for loop_nodes in loops:
            positions = medium.get_loop_positions(loop_nodes)
            holonomy = compute_loop_holonomy(positions)
            size_to_holonomies[len(loop_nodes)].append(holonomy)
    
    print(f"\n  Results by loop size:")
    print(f"    {'Size':<6} {'Count':<8} {'Mean |h|':<10} {'F%':<8} {'B%':<8}")
    print(f"    {'-'*40}")
    
    results_by_size = {}
    
    for size in sorted(size_to_holonomies.keys()):
        holonomies = size_to_holonomies[size]
        count = len(holonomies)
        mean_mag = np.mean([abs(h) for h in holonomies])
        
        f_frac = sum(1 for h in holonomies if abs(h + 1) < 0.3) / count
        b_frac = sum(1 for h in holonomies if abs(h - 1) < 0.3) / count
        
        print(f"    {size:<6} {count:<8} {mean_mag:<10.3f} {100*f_frac:<8.1f} {100*b_frac:<8.1f}")
        
        results_by_size[size] = {
            'count': count,
            'mean_magnitude': mean_mag,
            'f_fraction': f_frac,
            'b_fraction': b_frac
        }
    
    return results_by_size


# =============================================================================
# MAIN
# =============================================================================

def run_bias_audit_v2():
    """Run the V2 bias audit with geometric stability."""
    print("=" * 70)
    print("  QMRT BIAS AUDIT V2 — GEOMETRIC STABILITY DERIVATION")
    print("=" * 70)
    print()
    print("  This audit tests whether fermionic dominance emerges from")
    print("  GEOMETRY alone, without explicit sector-dependent rules.")
    print()
    
    start_time = timer.time()
    
    results = {
        'config': BASELINE_CONFIG,
        'tests': {}
    }
    
    # Test 1: Holonomy distribution at nucleation
    results['tests']['holonomy_distribution'] = run_holonomy_distribution_test(BASELINE_CONFIG)
    
    # Test 2: Loop size analysis
    results['tests']['loop_size_analysis'] = run_loop_size_analysis(BASELINE_CONFIG)
    
    # Test 3: Geometric vs biased stability
    results['tests']['geometric_vs_biased'] = run_geometric_vs_biased_test(BASELINE_CONFIG)
    
    elapsed = timer.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("  BIAS AUDIT V2 SUMMARY")
    print("=" * 70)
    
    hol_test = results['tests']['holonomy_distribution']
    geo_test = results['tests']['geometric_vs_biased']
    
    print(f"""
  1. NUCLEATION DISTRIBUTION:
     F-fraction at formation: {100*hol_test['f_fraction_at_nucleation']:.1f}%
     B-fraction at formation: {100*hol_test['b_fraction_at_nucleation']:.1f}%
     Geometry favors fermions: {'YES' if hol_test['geometry_favors_fermions'] else 'NO'}
     
  2. STABILITY COMPARISON:
     Geometric (no bias): {100*geo_test['geometric_mean']:.1f}%
     Biased:              {100*geo_test['biased_mean']:.1f}%
     Geometric shows dominance: {'YES' if geo_test['geometric_shows_dominance'] else 'NO'}
     Lifetime ratio (F/B): {geo_test['lifetime_ratio']:.2f}
     
  3. KEY FINDING:
    """)
    
    if hol_test['geometry_favors_fermions']:
        print("     ✅ The Y-junction geometry naturally PRODUCES more fermionic loops")
        print("        This is geometric selection at NUCLEATION, not decay.")
    else:
        print("     ⚠️ Geometry does not strongly favor fermions at nucleation")
    
    if geo_test['geometric_shows_dominance']:
        print("     ✅ Geometric stability alone produces fermionic dominance")
        print("        EMERGENCE VALIDATED — no explicit bias needed")
    else:
        print("     ⚠️ Geometric stability alone does NOT produce dominance")
        print("        The original Stage 4C relied on explicit bias")
    
    results['summary'] = {
        'geometry_favors_at_nucleation': hol_test['geometry_favors_fermions'],
        'geometric_stability_sufficient': geo_test['geometric_shows_dominance'],
        'emergence_validated': (
            hol_test['geometry_favors_fermions'] or 
            geo_test['geometric_shows_dominance']
        ),
        'elapsed_seconds': elapsed
    }
    
    print(f"\n  Elapsed time: {elapsed:.1f} seconds")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/stage4_bias_audit_v2_results.json'
    
    def convert_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.floating, float)):
            return float(obj)
        elif isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, complex):
            return {'real': obj.real, 'imag': obj.imag}
        elif isinstance(obj, dict):
            return {str(k): convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(v) for v in obj]
        return obj
    
    with open(output_path, 'w') as f:
        json.dump(convert_numpy(results), f, indent=2)
    
    print(f"\n  Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_bias_audit_v2()
