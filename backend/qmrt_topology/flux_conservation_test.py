"""
QMRT: FLUX CONSERVATION CONSTRAINT TEST
=======================================

THE MISSING PHYSICS:
  Current model has too much freedom → mixed degrees, no dominance
  
  Need: A constraint that FORCES degree = 3

OPTION 1: FLUX CONSERVATION (strongest candidate)

  Constraint: Σᵢ Jᵢ = 0 at each node
  
  Where J is a signed "flux" carried by each branch.
  
  Analysis:
    - 2-branch: J₁ + J₂ = 0 → trivial (just cancels, no network)
    - 3-branch: J₁ + J₂ + J₃ = 0 → MINIMAL non-trivial solution
    - 4+ branch: overconstrained (too many ways to satisfy)
    
  This naturally selects degree = 3!

WHY THIS MIGHT BE PHYSICAL:
  - Torsion flux conservation
  - Phase winding conservation  
  - Current continuity (like Kirchhoff's law)
  - Topological charge conservation
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set
import json


@dataclass
class FluxBranch:
    """A branch carrying signed flux."""
    node1_id: int
    node2_id: int
    flux: float  # Signed quantity, conserved at nodes
    tension: float = 1.0


@dataclass 
class FluxNode:
    """A node where flux is conserved."""
    id: int
    position: np.ndarray


class FluxConservingNetwork:
    """
    Network where flux is conserved at each node: Σ J_in = Σ J_out
    
    Key prediction: This should force degree = 3 as the minimal non-trivial node.
    """
    
    def __init__(self, domain_size: float = 100.0, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.domain_size = domain_size
        self.nodes: Dict[int, FluxNode] = {}
        self.branches: List[FluxBranch] = []
        self.next_id = 0
        
        self.time = 0.0
    
    def add_node(self, position: np.ndarray) -> int:
        """Add a node."""
        node_id = self.next_id
        self.nodes[node_id] = FluxNode(id=node_id, position=np.array(position))
        self.next_id += 1
        return node_id
    
    def add_branch(self, n1: int, n2: int, flux: float, tension: float = 1.0):
        """Add a flux-carrying branch."""
        self.branches.append(FluxBranch(n1, n2, flux, tension))
    
    def get_node_degree(self, node_id: int) -> int:
        """Get degree of a node."""
        return sum(1 for b in self.branches 
                   if b.node1_id == node_id or b.node2_id == node_id)
    
    def get_flux_at_node(self, node_id: int) -> float:
        """
        Compute net flux at a node.
        
        Convention: flux > 0 means flowing away from node1 toward node2
        """
        net_flux = 0.0
        for b in self.branches:
            if b.node1_id == node_id:
                net_flux -= b.flux  # Outgoing
            elif b.node2_id == node_id:
                net_flux += b.flux  # Incoming
        return net_flux
    
    def flux_conservation_violation(self) -> float:
        """Total violation of flux conservation across all nodes."""
        total_violation = 0.0
        for node_id in self.nodes:
            net_flux = self.get_flux_at_node(node_id)
            total_violation += net_flux**2
        return total_violation
    
    def create_random_flux_conserving_network(self, n_nodes: int = 10):
        """
        Create a network that respects flux conservation.
        
        Method: Start with sources/sinks, connect with conserving paths.
        """
        # Create nodes
        for _ in range(n_nodes):
            pos = np.random.uniform(0, self.domain_size, 2)
            self.add_node(pos)
        
        node_ids = list(self.nodes.keys())
        
        # Create flux-conserving structure
        # Method: Create "flow paths" from sources to sinks
        
        # Pick some source nodes (positive flux out) and sink nodes (negative)
        n_sources = n_nodes // 3
        sources = np.random.choice(node_ids, n_sources, replace=False)
        remaining = [n for n in node_ids if n not in sources]
        sinks = np.random.choice(remaining, n_sources, replace=False)
        
        # Connect sources to sinks through intermediate nodes
        for src, snk in zip(sources, sinks):
            # Pick intermediate nodes
            intermediates = [n for n in node_ids if n not in [src, snk]]
            if intermediates:
                mid = np.random.choice(intermediates)
                
                # Create path: src -> mid -> snk
                flux_value = np.random.uniform(0.5, 1.5)
                self.add_branch(src, mid, flux_value)
                self.add_branch(mid, snk, flux_value)
    
    def create_y_junction_network(self, n_junctions: int = 5):
        """
        Create a network composed of Y-junctions (degree-3 nodes).
        
        This explicitly tests the Y-junction structure.
        """
        # Create central Y-junction nodes
        for i in range(n_junctions):
            center_pos = np.random.uniform(20, 80, 2)
            center_id = self.add_node(center_pos)
            
            # Create 3 branches from center
            for j in range(3):
                angle = j * 2*np.pi/3  # 120° apart
                offset = 15 * np.array([np.cos(angle), np.sin(angle)])
                end_pos = center_pos + offset
                end_id = self.add_node(end_pos)
                
                # Flux: alternating signs, sum to zero
                # J1 + J2 + J3 = 0 with equal magnitudes means:
                # e.g., J1 = 1, J2 = 1, J3 = -2 (doesn't quite work)
                # Better: J1 = 1∠0°, J2 = 1∠120°, J3 = 1∠240° as vectors
                # But for scalar flux: J1 + J2 + J3 = 0 with |J| = 1
                # → Two inflow, one outflow (or vice versa)
                
                flux = 1.0 if j < 2 else -2.0  # Two in, one out (×2)
                self.add_branch(center_id, end_id, flux)
    
    def compute_energy(self, flux_penalty: float = 10.0, 
                       degree_penalty: float = 0.0) -> float:
        """
        Compute total energy with flux conservation penalty.
        
        E = Σ T_i L_i + λ_flux × (flux violation)² + λ_degree × f(degree)
        """
        energy = 0.0
        
        # Branch energy
        for b in self.branches:
            p1 = self.nodes[b.node1_id].position
            p2 = self.nodes[b.node2_id].position
            length = np.linalg.norm(p2 - p1)
            energy += b.tension * length
        
        # Flux conservation penalty
        for node_id in self.nodes:
            net_flux = self.get_flux_at_node(node_id)
            energy += flux_penalty * net_flux**2
        
        # Degree penalty (if used)
        if degree_penalty > 0:
            for node_id in self.nodes:
                degree = self.get_node_degree(node_id)
                # Penalty for degree ≠ 3
                energy += degree_penalty * (degree - 3)**2
        
        return energy
    
    def evolve_step(self, dt: float = 0.1, flux_penalty: float = 10.0):
        """
        Evolve network to minimize energy while conserving flux.
        """
        # Move nodes to reduce tension energy
        for node_id, node in self.nodes.items():
            # Force from connected branches
            force = np.zeros(2)
            
            for b in self.branches:
                if b.node1_id == node_id:
                    other_pos = self.nodes[b.node2_id].position
                elif b.node2_id == node_id:
                    other_pos = self.nodes[b.node1_id].position
                else:
                    continue
                
                direction = other_pos - node.position
                dist = np.linalg.norm(direction) + 1e-10
                unit_dir = direction / dist
                
                # Tension pulls toward other node
                force += b.tension * unit_dir
            
            # Damped motion
            damping = 10.0
            displacement = force * dt / damping
            
            # Limit
            max_disp = 1.0
            if np.linalg.norm(displacement) > max_disp:
                displacement = displacement * max_disp / np.linalg.norm(displacement)
            
            node.position += displacement
            node.position = np.clip(node.position, 0, self.domain_size)
        
        # Adjust fluxes to reduce conservation violation
        # (This is the key dynamics for flux conservation)
        for b in self.branches:
            # Compute flux violation at both endpoints
            violation_1 = self.get_flux_at_node(b.node1_id)
            violation_2 = self.get_flux_at_node(b.node2_id)
            
            # Adjust flux to reduce violations
            # If node1 has positive violation (too much outflow), reduce flux
            # If node2 has negative violation (too much inflow), reduce flux
            flux_correction = -0.1 * (violation_1 - violation_2)
            b.flux += flux_correction * dt
        
        # Tension equilibration
        avg_tension = np.mean([b.tension for b in self.branches])
        for b in self.branches:
            b.tension += 0.1 * (avg_tension - b.tension) * dt
            b.tension = max(0.1, b.tension)
        
        self.time += dt
    
    def get_statistics(self) -> Dict:
        """Get network statistics."""
        degrees = [self.get_node_degree(n) for n in self.nodes]
        degree_counts = {}
        for d in degrees:
            degree_counts[d] = degree_counts.get(d, 0) + 1
        
        tensions = [b.tension for b in self.branches]
        fluxes = [b.flux for b in self.branches]
        
        flux_violation = self.flux_conservation_violation()
        
        # Fraction of nodes with degree 3
        n_degree_3 = sum(1 for d in degrees if d == 3)
        frac_degree_3 = n_degree_3 / len(degrees) if degrees else 0
        
        return {
            'n_nodes': len(self.nodes),
            'n_branches': len(self.branches),
            'degree_distribution': degree_counts,
            'frac_degree_3': float(frac_degree_3),
            'tension_mean': float(np.mean(tensions)) if tensions else 0,
            'tension_cv': float(np.std(tensions)/np.mean(tensions)) if tensions else 0,
            'flux_violation': float(flux_violation),
            'flux_conserved': flux_violation < 0.1
        }


def test_flux_conservation_forces_degree_3():
    """
    THE KEY TEST: Does flux conservation force degree = 3?
    
    Theory:
      - 2-branch: trivial (just cancels)
      - 3-branch: minimal non-trivial
      - 4+ branch: overconstrained
    """
    print("#" * 80)
    print("#  FLUX CONSERVATION CONSTRAINT TEST")
    print("#" * 80)
    print("""
HYPOTHESIS:
  Flux conservation Σᵢ Jᵢ = 0 at each node forces degree = 3
  
  Because:
    - 2-branch: trivial (J₁ = -J₂, no network structure)
    - 3-branch: minimal non-trivial solution
    - 4+ branch: overconstrained, unstable
    
  If true → Fermions emerge from flux conservation!
""")
    
    print("=" * 70)
    print("TEST 1: EXPLICIT Y-JUNCTION NETWORK")
    print("=" * 70)
    
    # Create explicit Y-junction network
    network = FluxConservingNetwork(seed=42)
    network.create_y_junction_network(n_junctions=5)
    
    stats = network.get_statistics()
    
    print(f"\nInitial state:")
    print(f"  Nodes: {stats['n_nodes']}")
    print(f"  Branches: {stats['n_branches']}")
    print(f"  Degree distribution: {stats['degree_distribution']}")
    print(f"  Fraction degree-3: {stats['frac_degree_3']:.1%}")
    print(f"  Flux violation: {stats['flux_violation']:.4f}")
    
    # Note: In this explicit construction, degree-3 should dominate
    
    print("\n" + "=" * 70)
    print("TEST 2: RANDOM NETWORK WITH FLUX CONSERVATION PENALTY")
    print("=" * 70)
    
    results = []
    
    for trial in range(5):
        network2 = FluxConservingNetwork(seed=trial*17)
        network2.create_random_flux_conserving_network(n_nodes=12)
        
        # Evolve with flux penalty
        for _ in range(500):
            network2.evolve_step(dt=0.1, flux_penalty=10.0)
        
        stats2 = network2.get_statistics()
        results.append(stats2)
        
        print(f"Trial {trial}: Degree dist = {stats2['degree_distribution']}, "
              f"Flux violation = {stats2['flux_violation']:.4f}")
    
    print("\n" + "=" * 70)
    print("ANALYSIS: DOES FLUX CONSERVATION SELECT DEGREE-3?")
    print("=" * 70)
    
    # Aggregate degree distribution
    total_degrees = {}
    for r in results:
        for deg, count in r['degree_distribution'].items():
            total_degrees[deg] = total_degrees.get(deg, 0) + count
    
    total_nodes = sum(total_degrees.values())
    
    print(f"\n{'Degree':>8} | {'Count':>8} | {'Fraction':>10}")
    print("-" * 32)
    for deg in sorted(total_degrees.keys()):
        count = total_degrees[deg]
        frac = count / total_nodes if total_nodes > 0 else 0
        marker = " ← TARGET" if deg == 3 else ""
        print(f"{deg:>8} | {count:>8} | {frac:>10.1%}{marker}")
    
    # Check if degree-3 dominates
    frac_3 = total_degrees.get(3, 0) / total_nodes if total_nodes > 0 else 0
    
    print(f"\nDegree-3 fraction: {frac_3:.1%}")
    
    return results, frac_3


def analyze_why_flux_selects_degree_3():
    """
    Theoretical analysis of why flux conservation selects degree 3.
    """
    print("\n" + "=" * 70)
    print("THEORETICAL ANALYSIS: WHY FLUX → DEGREE 3")
    print("=" * 70)
    
    print("""
FLUX CONSERVATION: Σᵢ Jᵢ = 0 at each node

ANALYSIS BY DEGREE:

DEGREE 1 (leaf node):
  Constraint: J₁ = 0
  → No flux through this branch
  → Effectively disconnected, not useful
  
DEGREE 2 (pass-through):
  Constraint: J₁ + J₂ = 0 → J₁ = -J₂
  → Flux just passes through
  → No "processing" at this node
  → Can be eliminated (merge into single branch)
  
DEGREE 3 (Y-junction): ✅ MINIMAL NON-TRIVIAL
  Constraint: J₁ + J₂ + J₃ = 0
  → Non-trivial relationship between 3 fluxes
  → Cannot be simplified further
  → First node that actually "does something"
  
DEGREE 4 (X-junction):
  Constraint: J₁ + J₂ + J₃ + J₄ = 0
  → One equation, four unknowns
  → Many solutions, unstable under perturbation
  → Tends to split into two degree-3 nodes
  
DEGREE 5+:
  Even more overconstrained
  → Unstable, splits into degree-3 components

CONCLUSION:
  Flux conservation + stability → degree 3 is the ATTRACTOR.
  
  This is analogous to:
    - Kirchhoff's laws in circuits (3-way junctions are basic)
    - Soap film networks (Plateau's laws: 3 films meet at 120°)
    - River networks (typically branch as Y-junctions)
""")


def test_degree_4_instability():
    """
    Test whether degree-4 nodes are unstable and split into degree-3.
    """
    print("\n" + "=" * 70)
    print("TEST 3: DEGREE-4 INSTABILITY")
    print("=" * 70)
    print("""
If flux conservation truly selects degree-3, then:
  Degree-4 nodes should be UNSTABLE
  They should SPLIT into two degree-3 nodes
""")
    
    # Create a network with explicit degree-4 nodes
    network = FluxConservingNetwork(seed=42)
    
    # Create central X-junction (degree 4)
    center = network.add_node(np.array([50.0, 50.0]))
    
    # Add 4 branches
    for i in range(4):
        angle = i * np.pi/2  # 90° apart
        offset = 20 * np.array([np.cos(angle), np.sin(angle)])
        end = network.add_node(np.array([50.0, 50.0]) + offset)
        
        # Flux: need J₁ + J₂ + J₃ + J₄ = 0
        # Use alternating: +1, -1, +1, -1
        flux = 1.0 if i % 2 == 0 else -1.0
        network.add_branch(center, end, flux)
    
    initial_degree = network.get_node_degree(center)
    print(f"\nInitial central node degree: {initial_degree}")
    
    # Check stability under perturbation
    # Add random perturbation to positions
    for node in network.nodes.values():
        node.position += np.random.normal(0, 2, 2)
    
    # Evolve
    for _ in range(200):
        network.evolve_step(dt=0.1, flux_penalty=10.0)
    
    final_stats = network.get_statistics()
    
    print(f"Final degree distribution: {final_stats['degree_distribution']}")
    print(f"Flux conservation violation: {final_stats['flux_violation']:.4f}")
    
    # Check if degree-4 persisted or split
    has_degree_4 = 4 in final_stats['degree_distribution']
    
    if has_degree_4:
        print("\n⚠️ Degree-4 node persisted (may need reconnection dynamics)")
    else:
        print("\n✅ Degree-4 node split/transformed (supports instability hypothesis)")


def comprehensive_flux_summary():
    """Summarize flux conservation findings."""
    print("\n" + "=" * 80)
    print("FLUX CONSERVATION SUMMARY")
    print("=" * 80)
    
    print("""
FINDINGS:

1. THEORETICAL ARGUMENT ✅
   - Degree 1: trivial (no flux)
   - Degree 2: trivial (pass-through)
   - Degree 3: MINIMAL non-trivial
   - Degree 4+: overconstrained, unstable
   
2. NUMERICAL TEST ⚠️
   - Mixed results in current implementation
   - Degree-3 fraction varies
   - Need reconnection dynamics to fully test
   
3. ANALOGY TO KNOWN PHYSICS ✅
   - Kirchhoff's laws: 3-way junctions
   - Soap films: Plateau's laws (120° at triple junctions)
   - River networks: Y-branching

IMPLICATIONS FOR QMRT:

  IF the medium has a conserved flux-like quantity:
    → Nodes naturally tend toward degree 3
    → Combined with tension equilibration → 120° angles
    → Combined with projection factor → 1/2
    → Result: FERMION STATISTICS
    
  This would complete the emergence chain:
    Flux conservation → degree 3 → 120° → 1/2 → π → -1 → FERMION

REMAINING WORK:

  1. Implement reconnection dynamics (nodes can split/merge)
  2. Show degree-4 instability more clearly
  3. Identify what plays the role of "flux" in QMRT (torsion? phase? charge?)
""")


def run_flux_tests():
    """Run all flux conservation tests."""
    
    results, frac_3 = test_flux_conservation_forces_degree_3()
    
    analyze_why_flux_selects_degree_3()
    
    test_degree_4_instability()
    
    comprehensive_flux_summary()
    
    # Verdict
    print("\n" + "=" * 70)
    print("FLUX CONSTRAINT VERDICT")
    print("=" * 70)
    
    # Check if degree-3 dominates
    degree_3_dominant = frac_3 > 0.4  # More than 40% are degree-3
    
    if degree_3_dominant:
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ FLUX CONSERVATION SELECTS DEGREE-3                                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Degree-3 nodes dominate under flux conservation constraint.             ║
║                                                                          ║
║  Combined with:                                                          ║
║    • Tension equilibration → equal tensions                              ║
║    • Force balance → 120° angles                                         ║
║    • Projection → 1/2 factor                                             ║
║                                                                          ║
║  This provides a complete emergence mechanism for fermions!              ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
        conclusion = "FLUX_SELECTS_DEGREE_3"
    else:
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ⚠️ PARTIAL RESULT: Degree-3 fraction = {frac_3:.1%}                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Flux conservation alone doesn't strongly select degree-3.               ║
║                                                                          ║
║  May need:                                                               ║
║    • Reconnection dynamics (node splitting)                              ║
║    • Stronger flux penalty                                               ║
║    • Additional constraints (energy, topology)                           ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
        conclusion = "PARTIAL"
    
    # Save results
    output = {
        'test': 'Flux_Conservation_Constraint',
        'degree_3_fraction': float(frac_3),
        'degree_3_dominant': bool(degree_3_dominant),
        'conclusion': conclusion
    }
    
    output_path = '/app/backend/qmrt_topology/flux_conservation_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return output


if __name__ == "__main__":
    results = run_flux_tests()
