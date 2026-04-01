"""
QMRT: TOPOLOGICAL PHASE CONSERVATION TEST
==========================================

THE MISSING PHYSICS (from user guidance):

1. PHASE CONSERVATION
   - What flows in must flow out
   - Cannot just vanish
   → Prevents collapse to 0°

2. TOPOLOGICAL CONSTRAINT  
   - Around a loop: Σ Δθ = 2πk
   - NOT imposed artificially
   - Arises from: continuity + periodicity of phase
   → Creates quantization NATURALLY

3. NO DAMPING (test)
   - Pure wave + conservation
   - Check if damping was killing structure

4. WINDING NUMBER
   - Compute total phase change around loop
   - Check if stable non-zero winding appears
   → TRUE EMERGENCE

KEY INSIGHT:
  "Structure = wave + conservation + topology"
  Not just wave dynamics alone.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json
from collections import Counter


# =============================================================================
# TOPOLOGICAL PHASE MODEL
# =============================================================================

@dataclass
class TopologicalNode:
    """Node with conserved phase current."""
    id: int
    position: np.ndarray
    
    # Phase is periodic: θ ∈ [0, 2π)
    phase: float = 0.0
    phase_velocity: float = 0.0
    
    # Conserved quantity: total phase current through node
    phase_flux_in: float = 0.0
    phase_flux_out: float = 0.0
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=float)


@dataclass
class TopologicalEdge:
    """Edge carrying phase current (conserved flow)."""
    id: int
    node_a: int
    node_b: int
    
    # Phase current flowing from a to b (conserved!)
    current: float = 0.0
    
    # Edge properties
    conductance: float = 1.0  # How easily current flows


class TopologicalNetwork:
    """
    Network with CONSERVED phase current and TOPOLOGICAL winding.
    
    KEY PHYSICS:
    1. Phase is periodic: θ ∈ [0, 2π), wraps around
    2. Current is conserved: Σ I_in = Σ I_out at each node
    3. Winding number: Σ Δθ / 2π around loop (integer!)
    4. NO damping: pure wave + conservation
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        
        self.nodes: Dict[int, TopologicalNode] = {}
        self.edges: Dict[int, TopologicalEdge] = {}
        self.adjacency: Dict[int, List[Tuple[int, int]]] = {}  # node -> [(edge_id, direction)]
        
        self.next_node_id = 0
        self.next_edge_id = 0
        
        # PHYSICS PARAMETERS
        self.coupling = 2.0           # Phase coupling strength
        self.mass = 1.0               # Phase inertia
        self.damping = 0.0            # NO DAMPING (test)
        
        # Geometric phase offset (from Y-junction structure)
        self.phase_per_junction = -np.pi / 6  # -30 degrees
        
        self.dt = 0.005  # Smaller timestep for stability
    
    # =========================================================================
    # NETWORK CONSTRUCTION
    # =========================================================================
    
    def add_node(self, position: np.ndarray, phase: float = None) -> int:
        nid = self.next_node_id
        
        if phase is None:
            phase = np.random.random() * 2 * np.pi
        
        # Ensure phase is in [0, 2π)
        phase = phase % (2 * np.pi)
        
        velocity = (np.random.random() - 0.5) * 0.2
        
        self.nodes[nid] = TopologicalNode(nid, position, phase, velocity)
        self.adjacency[nid] = []
        self.next_node_id += 1
        return nid
    
    def add_edge(self, node_a: int, node_b: int) -> int:
        eid = self.next_edge_id
        
        self.edges[eid] = TopologicalEdge(eid, node_a, node_b)
        
        # Direction: +1 means current flows out from node, -1 means flows in
        self.adjacency[node_a].append((eid, +1))  # Current out
        self.adjacency[node_b].append((eid, -1))  # Current in
        
        self.next_edge_id += 1
        return eid
    
    def create_loop(self, n: int, center: np.ndarray = None,
                    radius: float = 1.0, initial_winding: int = 1) -> List[int]:
        """
        Create a loop with specified initial winding number.
        
        initial_winding: integer winding number to initialize
        """
        if center is None:
            center = np.array([0.0, 0.0])
        
        node_ids = []
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        for i, angle in enumerate(angles):
            pos = center + radius * np.array([np.cos(angle), np.sin(angle)])
            
            # Initialize phase with specified winding
            # Total winding should be 2π * initial_winding around the loop
            phase = (2 * np.pi * initial_winding * i / n) % (2 * np.pi)
            
            nid = self.add_node(pos, phase)
            node_ids.append(nid)
        
        for i in range(n):
            self.add_edge(node_ids[i], node_ids[(i+1) % n])
        
        return node_ids
    
    # =========================================================================
    # PHASE WRAPPING (CRUCIAL FOR TOPOLOGY)
    # =========================================================================
    
    def wrap_phase(self, phase: float) -> float:
        """Wrap phase to [0, 2π)."""
        return phase % (2 * np.pi)
    
    def phase_difference(self, phase_a: float, phase_b: float) -> float:
        """
        Compute CONTINUOUS phase difference accounting for wrapping.
        
        Returns value in [-π, π] that correctly handles the branch cut.
        """
        diff = phase_b - phase_a
        
        # Wrap to [-π, π] for CONTINUOUS difference
        while diff > np.pi:
            diff -= 2 * np.pi
        while diff < -np.pi:
            diff += 2 * np.pi
        
        return diff
    
    # =========================================================================
    # WINDING NUMBER (TOPOLOGICAL INVARIANT)
    # =========================================================================
    
    def compute_winding_number(self, node_ids: List[int]) -> float:
        """
        Compute winding number around a loop.
        
        W = (1/2π) * Σ Δθ
        
        This should be an INTEGER for a consistent configuration!
        If it's not integer → configuration is inconsistent.
        """
        n = len(node_ids)
        total_phase_change = 0.0
        
        for i in range(n):
            phase_a = self.nodes[node_ids[i]].phase
            phase_b = self.nodes[node_ids[(i+1) % n]].phase
            
            # Use continuous phase difference
            delta = self.phase_difference(phase_a, phase_b)
            total_phase_change += delta
        
        winding = total_phase_change / (2 * np.pi)
        return winding
    
    def compute_winding_error(self, node_ids: List[int]) -> float:
        """How far is winding from nearest integer?"""
        winding = self.compute_winding_number(node_ids)
        nearest_int = round(winding)
        return abs(winding - nearest_int)
    
    # =========================================================================
    # PHASE CURRENT CONSERVATION
    # =========================================================================
    
    def compute_edge_current(self, edge_id: int) -> float:
        """
        Compute phase current on an edge.
        
        Current = conductance * (phase_difference - expected_offset)
        
        The current represents how much phase is "flowing" through the edge.
        """
        edge = self.edges[edge_id]
        
        phase_a = self.nodes[edge.node_a].phase
        phase_b = self.nodes[edge.node_b].phase
        
        # Phase difference (continuous)
        diff = self.phase_difference(phase_a, phase_b)
        
        # Expected phase difference from geometry
        expected = self.phase_per_junction
        
        # Current = deviation from expected × conductance
        mismatch = diff - expected
        current = edge.conductance * np.sin(mismatch)  # Bounded current
        
        return current
    
    def compute_flux_imbalance(self, node_id: int) -> float:
        """
        Compute flux imbalance at a node.
        
        Conservation law: Σ I_in - Σ I_out = 0
        
        Returns the imbalance (should be ~0 for conservation).
        """
        edges_with_dir = self.adjacency[node_id]
        
        total_in = 0.0
        total_out = 0.0
        
        for edge_id, direction in edges_with_dir:
            current = self.compute_edge_current(edge_id)
            
            # Direction: +1 = current flows out, -1 = current flows in
            if direction * current > 0:
                total_out += abs(current)
            else:
                total_in += abs(current)
        
        return total_in - total_out
    
    # =========================================================================
    # CONSERVATIVE DYNAMICS
    # =========================================================================
    
    def compute_phase_acceleration(self, node_id: int) -> float:
        """
        Compute phase acceleration from CONSERVED current flow.
        
        Key: the dynamics must preserve winding number!
        """
        node = self.nodes[node_id]
        edges_with_dir = self.adjacency[node_id]
        
        if not edges_with_dir:
            return -self.damping * node.phase_velocity
        
        # Net torque from phase currents
        net_torque = 0.0
        
        for edge_id, direction in edges_with_dir:
            edge = self.edges[edge_id]
            
            # Get neighbor
            neighbor_id = edge.node_a if edge.node_b == node_id else edge.node_b
            neighbor = self.nodes[neighbor_id]
            
            # Phase difference (continuous)
            diff = self.phase_difference(node.phase, neighbor.phase)
            
            # Expected difference from geometry
            expected = self.phase_per_junction
            
            # Mismatch drives dynamics
            mismatch = diff - expected
            
            # Torque: wants to reduce mismatch
            # Using sin for bounded, periodic force
            torque = self.coupling * np.sin(mismatch)
            
            net_torque += torque
        
        net_torque /= len(edges_with_dir)
        
        # Damping (set to 0 for conservation test)
        damping_torque = -self.damping * node.phase_velocity
        
        return (net_torque + damping_torque) / self.mass
    
    def evolve_step(self):
        """
        Evolve with CONSERVATIVE dynamics.
        
        Uses symplectic integrator to preserve energy/topology.
        """
        # Half-step velocity update
        for nid, node in self.nodes.items():
            acc = self.compute_phase_acceleration(nid)
            node.phase_velocity += 0.5 * acc * self.dt
        
        # Full-step position update
        for nid, node in self.nodes.items():
            node.phase += node.phase_velocity * self.dt
            node.phase = self.wrap_phase(node.phase)  # Keep in [0, 2π)
        
        # Half-step velocity update
        for nid, node in self.nodes.items():
            acc = self.compute_phase_acceleration(nid)
            node.phase_velocity += 0.5 * acc * self.dt
    
    def compute_energy(self, node_ids: List[int]) -> Dict[str, float]:
        """Compute kinetic and potential energy."""
        kinetic = 0.0
        potential = 0.0
        
        for nid in node_ids:
            node = self.nodes[nid]
            kinetic += 0.5 * self.mass * node.phase_velocity**2
        
        # Potential from phase mismatch
        n = len(node_ids)
        for i in range(n):
            n1 = node_ids[i]
            n2 = node_ids[(i+1) % n]
            
            diff = self.phase_difference(self.nodes[n1].phase, self.nodes[n2].phase)
            mismatch = diff - self.phase_per_junction
            
            potential += self.coupling * (1 - np.cos(mismatch))
        
        return {
            'kinetic': float(kinetic),
            'potential': float(potential),
            'total': float(kinetic + potential)
        }
    
    def evolve(self, node_ids: List[int], n_steps: int,
               record_every: int = 20) -> Dict:
        """Evolve and track winding number stability."""
        history = {
            'winding': [],
            'winding_error': [],
            'kinetic': [],
            'potential': [],
            'total_energy': []
        }
        
        for step in range(n_steps):
            self.evolve_step()
            
            if step % record_every == 0:
                winding = self.compute_winding_number(node_ids)
                error = self.compute_winding_error(node_ids)
                energy = self.compute_energy(node_ids)
                
                history['winding'].append(winding)
                history['winding_error'].append(error)
                history['kinetic'].append(energy['kinetic'])
                history['potential'].append(energy['potential'])
                history['total_energy'].append(energy['total'])
        
        return history


# =============================================================================
# TOPOLOGICAL TEST SUITE
# =============================================================================

class TopologicalEmergenceTest:
    """Test whether winding number is preserved and quantized."""
    
    def __init__(self):
        self.results = {}
    
    def test_winding_preservation(self) -> Dict:
        """
        TEST A: Is winding number PRESERVED by dynamics?
        
        Start with integer winding, evolve, check if it stays integer.
        """
        print("=" * 70)
        print("TEST A: WINDING NUMBER PRESERVATION")
        print("=" * 70)
        print("""
Start with loops having integer winding number.
Evolve with CONSERVATIVE dynamics (no damping).
Check if winding remains integer (topologically stable).
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Initial W':>10} | {'Final W':>10} | {'Error':>10} | {'Preserved':>10}")
        print("-" * 60)
        
        for n in [4, 5, 6, 7, 8, 10, 12]:
            for initial_w in [0, 1, 2]:
                network = TopologicalNetwork(seed=n * 100 + initial_w)
                node_ids = network.create_loop(n, initial_winding=initial_w)
                
                # Measure initial
                initial_winding = network.compute_winding_number(node_ids)
                
                # Evolve
                history = network.evolve(node_ids, n_steps=5000, record_every=50)
                
                # Measure final
                final_winding = network.compute_winding_number(node_ids)
                error = network.compute_winding_error(node_ids)
                
                preserved = error < 0.1
                
                print(f"{n:>4} | {initial_winding:>10.2f} | {final_winding:>10.2f} | "
                      f"{error:>10.3f} | {'YES' if preserved else 'NO':>10}")
                
                results.append({
                    'n': n,
                    'initial_winding': float(initial_winding),
                    'final_winding': float(final_winding),
                    'error': float(error),
                    'preserved': preserved
                })
        
        preserved_count = sum(1 for r in results if r['preserved'])
        print(f"\nWinding preserved: {preserved_count}/{len(results)}")
        
        return results
    
    def test_spontaneous_winding(self) -> Dict:
        """
        TEST B: Does non-zero winding EMERGE from random initial conditions?
        
        Start with random phases (winding ≈ 0).
        Check if stable non-zero winding appears.
        """
        print("\n" + "=" * 70)
        print("TEST B: SPONTANEOUS WINDING EMERGENCE")
        print("=" * 70)
        print("""
Start with RANDOM phases (winding ≈ 0).
Evolve and check if stable non-zero winding emerges.
This would be TRUE topological emergence.
""")
        
        results = []
        
        for trial in range(30):
            n = np.random.randint(4, 13)
            
            network = TopologicalNetwork(seed=trial * 17)
            
            # Create loop with RANDOM phases (not specified winding)
            node_ids = []
            center = np.array([0.0, 0.0])
            angles = np.linspace(0, 2*np.pi, n, endpoint=False)
            
            for angle in angles:
                pos = center + np.array([np.cos(angle), np.sin(angle)])
                phase = np.random.random() * 2 * np.pi  # RANDOM
                nid = network.add_node(pos, phase)
                node_ids.append(nid)
            
            for i in range(n):
                network.add_edge(node_ids[i], node_ids[(i+1) % n])
            
            # Measure initial winding
            initial_winding = network.compute_winding_number(node_ids)
            
            # Evolve
            history = network.evolve(node_ids, n_steps=8000, record_every=100)
            
            # Final state
            final_winding = network.compute_winding_number(node_ids)
            final_error = network.compute_winding_error(node_ids)
            
            results.append({
                'n': n,
                'initial_winding': float(initial_winding),
                'final_winding': float(final_winding),
                'final_error': float(final_error),
                'quantized': final_error < 0.15
            })
        
        # Distribution of final windings
        final_windings = [round(r['final_winding']) for r in results if r['quantized']]
        winding_dist = Counter(final_windings)
        
        print(f"\nFinal winding distribution (quantized trials):")
        for w in sorted(winding_dist.keys()):
            count = winding_dist[w]
            bar = "#" * count
            print(f"  W={w:>2}: {bar} ({count})")
        
        quantized_count = sum(1 for r in results if r['quantized'])
        nonzero_count = sum(1 for r in results if r['quantized'] and abs(round(r['final_winding'])) > 0)
        
        print(f"\nQuantized to integer: {quantized_count}/{len(results)}")
        print(f"Non-zero winding:     {nonzero_count}/{len(results)}")
        
        return {
            'details': results,
            'winding_distribution': dict(winding_dist),
            'quantized_fraction': quantized_count / len(results),
            'nonzero_fraction': nonzero_count / len(results)
        }
    
    def test_winding_vs_loop_size(self) -> Dict:
        """
        TEST C: Does preferred winding depend on loop size?
        
        The key question: Does n=6 prefer W=1 (fermion-like)?
        """
        print("\n" + "=" * 70)
        print("TEST C: PREFERRED WINDING VS LOOP SIZE")
        print("=" * 70)
        print("""
For each loop size, find the STABLE winding number.
Key question: Does n=6 prefer a specific winding?
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Expected Geo':>12} | {'Stable W':>10} | {'Energy':>10}")
        print("-" * 50)
        
        for n in range(3, 16):
            stable_windings = []
            energies = []
            
            for trial in range(5):
                # Try different initial windings, see which is stable
                for init_w in [0, 1, -1, 2]:
                    network = TopologicalNetwork(seed=n * 50 + trial * 10 + init_w)
                    node_ids = network.create_loop(n, initial_winding=init_w)
                    
                    history = network.evolve(node_ids, n_steps=5000, record_every=100)
                    
                    final_w = round(network.compute_winding_number(node_ids))
                    final_e = network.compute_energy(node_ids)['total']
                    
                    if network.compute_winding_error(node_ids) < 0.15:
                        stable_windings.append(final_w)
                        energies.append(final_e)
            
            if stable_windings:
                # Find most common stable winding
                w_dist = Counter(stable_windings)
                most_common_w = w_dist.most_common(1)[0][0]
                avg_energy = np.mean([e for w, e in zip(stable_windings, energies) 
                                     if w == most_common_w])
            else:
                most_common_w = "?"
                avg_energy = 0
            
            # Expected geometric winding from -30° per junction
            expected_geo = n * (-30) / 360  # Winding from geometry
            
            marker = ""
            if n == 6:
                marker = " ← FERMION?"
            elif n == 12:
                marker = " ← BOSON?"
            
            print(f"{n:>4} | {expected_geo:>12.2f} | {most_common_w:>10} | {avg_energy:>10.2f}{marker}")
            
            results.append({
                'n': n,
                'expected_geometric': expected_geo,
                'stable_winding': most_common_w,
                'avg_energy': float(avg_energy) if avg_energy else None
            })
        
        return results
    
    def test_energy_conservation(self) -> Dict:
        """
        TEST D: Is energy conserved (no damping)?
        
        With damping=0, total energy should be constant.
        This verifies the dynamics are truly conservative.
        """
        print("\n" + "=" * 70)
        print("TEST D: ENERGY CONSERVATION (NO DAMPING)")
        print("=" * 70)
        
        network = TopologicalNetwork(seed=42)
        network.damping = 0.0  # Explicitly no damping
        
        node_ids = network.create_loop(6, initial_winding=1)
        
        history = network.evolve(node_ids, n_steps=10000, record_every=20)
        
        energies = history['total_energy']
        initial_E = energies[0]
        final_E = energies[-1]
        max_E = max(energies)
        min_E = min(energies)
        
        drift = abs(final_E - initial_E) / initial_E
        fluctuation = (max_E - min_E) / initial_E
        
        print(f"\nInitial energy: {initial_E:.4f}")
        print(f"Final energy:   {final_E:.4f}")
        print(f"Max energy:     {max_E:.4f}")
        print(f"Min energy:     {min_E:.4f}")
        print(f"\nEnergy drift:       {drift:.4%}")
        print(f"Energy fluctuation: {fluctuation:.4%}")
        
        conserved = drift < 0.01
        print(f"\nEnergy conserved: {'YES' if conserved else 'NO'}")
        
        return {
            'initial_energy': initial_E,
            'final_energy': final_E,
            'drift': drift,
            'fluctuation': fluctuation,
            'conserved': conserved
        }
    
    def run_all_tests(self) -> Dict:
        """Run all topological emergence tests."""
        print("=" * 80)
        print("  QMRT: TOPOLOGICAL PHASE CONSERVATION TEST")
        print("=" * 80)
        print("""
THE KEY PHYSICS:
  1. Phase is periodic: θ ∈ [0, 2π)
  2. Conservation: no net phase loss
  3. Winding number: W = (1/2π) Σ Δθ (integer!)
  4. NO DAMPING: pure conservative dynamics

QUESTION: Does integer winding emerge and persist?
""")
        
        results = {}
        
        results['preservation'] = self.test_winding_preservation()
        results['spontaneous'] = self.test_spontaneous_winding()
        results['vs_size'] = self.test_winding_vs_loop_size()
        results['energy'] = self.test_energy_conservation()
        
        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        preservation_rate = sum(1 for r in results['preservation'] if r['preserved']) / len(results['preservation'])
        quantized_rate = results['spontaneous']['quantized_fraction']
        nonzero_rate = results['spontaneous']['nonzero_fraction']
        energy_conserved = results['energy']['conserved']
        
        print(f"""
TOPOLOGICAL RESULTS:

1. Winding preservation: {preservation_rate:.0%}
   {"✓ Winding is CONSERVED" if preservation_rate > 0.8 else "✗ Winding NOT conserved"}

2. Spontaneous quantization: {quantized_rate:.0%}
   {"✓ Phases QUANTIZE to integer winding" if quantized_rate > 0.5 else "✗ Phases NOT quantizing"}

3. Non-zero winding emergence: {nonzero_rate:.0%}
   {"✓ Non-trivial topology EMERGES" if nonzero_rate > 0.1 else "✗ Only trivial topology"}

4. Energy conservation: {results['energy']['drift']:.2%} drift
   {"✓ Dynamics are CONSERVATIVE" if energy_conserved else "✗ Energy leaking"}
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        topology_works = preservation_rate > 0.7 and quantized_rate > 0.4
        nontrivial_emerges = nonzero_rate > 0.05
        
        if topology_works and nontrivial_emerges:
            verdict = "TOPOLOGICAL_EMERGENCE_CONFIRMED"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ TOPOLOGICAL QUANTIZATION EMERGES                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  1. Winding number is CONSERVED by dynamics                                   ║
║  2. Phases spontaneously QUANTIZE to integer winding                          ║
║  3. Non-trivial winding (W ≠ 0) emerges and persists                         ║
║                                                                              ║
║  This is TRUE topological emergence from:                                     ║
║    - Phase periodicity (θ ∈ [0, 2π))                                         ║
║    - Conservation (no phase loss)                                            ║
║    - Continuity (smooth dynamics)                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        elif topology_works:
            verdict = "WINDING_CONSERVED_NOT_EMERGING"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ WINDING CONSERVED BUT NOT SPONTANEOUSLY EMERGING                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Winding number is stable once set, but doesn't emerge from random.          ║
║  Need mechanism to CREATE non-zero winding (not just preserve it).           ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "TOPOLOGY_NOT_STABLE"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ❌ TOPOLOGICAL STRUCTURE NOT STABLE                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Winding number is not being preserved.                                       ║
║  Need stronger conservation or different dynamics.                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Save
        output = {
            'test': 'Topological_Phase_Conservation',
            'verdict': verdict,
            'winding_preservation': results['preservation'],
            'spontaneous_emergence': results['spontaneous'],
            'winding_vs_size': results['vs_size'],
            'energy_conservation': results['energy'],
            'conclusions': {
                'preservation_rate': preservation_rate,
                'quantized_rate': quantized_rate,
                'nonzero_rate': nonzero_rate,
                'energy_conserved': energy_conserved
            }
        }
        
        output_path = '/app/backend/qmrt_topology/topological_emergence_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = TopologicalEmergenceTest()
    results = test.run_all_tests()
