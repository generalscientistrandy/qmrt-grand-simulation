"""
QMRT: RULE INDEPENDENCE TEST
=============================

CRITICAL QUESTION:
  Does phase closure EMERGE from local dynamics,
  or was it IMPOSED by the algorithm?

METHODOLOGY:
  REMOVE all explicit closure checks:
    - No phase closure evaluation
    - No discrete quantization filters
    - No n=6k selection rules
    - No "is_fermion" or "is_boson" checks during evolution

  KEEP only local physics:
    - Local phase transport between neighbors
    - Local phase mismatch penalty at junctions
    - Local torsion accumulation
    - Local energy gradients
    - Local structural updates

  OBSERVE:
    - What loop sizes naturally stabilize?
    - Does discrete structure emerge?
    - Are there preferred attractors?

SUCCESS CRITERION:
  If n=6,12,18... emerge WITHOUT explicit selection → EMERGENT
  If they don't emerge → IMPOSED (model incomplete)

THIS IS THE MOST IMPORTANT TEST.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
import json
from collections import Counter
from copy import deepcopy


# =============================================================================
# PURE LOCAL PHYSICS - NO GLOBAL CLOSURE CHECKS
# =============================================================================

@dataclass
class LocalNode:
    """A node with local phase state."""
    id: int
    position: np.ndarray
    phase: float = 0.0  # Local phase value
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=float)


@dataclass
class LocalEdge:
    """An edge with local tension and phase transport."""
    id: int
    node_a: int
    node_b: int
    tension: float = 1.0
    phase_gradient: float = 0.0  # Phase difference across edge
    torsion: float = 0.0         # Accumulated torsion on this edge


class LocalPhysicsNetwork:
    """
    Network with ONLY local physics.
    
    NO GLOBAL MEASUREMENTS:
      - No loop phase sums
      - No closure checks
      - No "is_fermion" tests
      - No discrete quantization
    
    ONLY LOCAL:
      - Phase at each node
      - Phase gradient across edges
      - Local mismatch at junctions
      - Local torsion accumulation
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        
        self.nodes: Dict[int, LocalNode] = {}
        self.edges: Dict[int, LocalEdge] = {}
        self.adjacency: Dict[int, List[int]] = {}  # node_id -> list of edge_ids
        
        self.next_node_id = 0
        self.next_edge_id = 0
        
        # LOCAL PHYSICS PARAMETERS
        # Phase transport
        self.phase_per_junction = -np.pi / 6  # -30 degrees (from Z_12 structure)
        self.phase_transport_rate = 0.1       # How fast phase propagates
        
        # LOCAL energy terms (no global evaluation)
        self.lambda_tension = 1.0             # Edge tension
        self.lambda_phase_gradient = 2.0      # Penalty for phase discontinuity
        self.lambda_torsion = 1.5             # Torsion accumulation
        self.lambda_angle_mismatch = 1.0      # Junction angle mismatch
        
        # Dynamics
        self.dt = 0.01
        self.noise_strength = 0.01
    
    # =========================================================================
    # NETWORK CONSTRUCTION
    # =========================================================================
    
    def add_node(self, position: np.ndarray, phase: float = None) -> int:
        """Add a node. If phase not specified, randomize."""
        nid = self.next_node_id
        if phase is None:
            phase = np.random.random() * 2 * np.pi
        self.nodes[nid] = LocalNode(nid, position, phase)
        self.adjacency[nid] = []
        self.next_node_id += 1
        return nid
    
    def add_edge(self, node_a: int, node_b: int) -> int:
        """Add an edge between two nodes."""
        eid = self.next_edge_id
        
        # Compute initial phase gradient
        phase_a = self.nodes[node_a].phase
        phase_b = self.nodes[node_b].phase
        gradient = self._wrap_phase(phase_b - phase_a)
        
        self.edges[eid] = LocalEdge(eid, node_a, node_b, phase_gradient=gradient)
        
        # Update adjacency
        self.adjacency[node_a].append(eid)
        self.adjacency[node_b].append(eid)
        
        self.next_edge_id += 1
        return eid
    
    def _wrap_phase(self, phase: float) -> float:
        """Wrap phase to [-π, π]."""
        while phase > np.pi:
            phase -= 2 * np.pi
        while phase < -np.pi:
            phase += 2 * np.pi
        return phase
    
    def create_loop(self, n: int, center: np.ndarray = None, 
                    radius: float = 1.0, random_phase: bool = True) -> List[int]:
        """
        Create a loop of n nodes.
        Returns list of node IDs.
        """
        if center is None:
            center = np.array([0.0, 0.0])
        
        node_ids = []
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        for i, angle in enumerate(angles):
            pos = center + radius * np.array([np.cos(angle), np.sin(angle)])
            
            if random_phase:
                phase = np.random.random() * 2 * np.pi
            else:
                # Initialize with expected phase transport
                phase = i * self.phase_per_junction
            
            nid = self.add_node(pos, phase)
            node_ids.append(nid)
        
        # Connect nodes in a loop
        edge_ids = []
        for i in range(n):
            eid = self.add_edge(node_ids[i], node_ids[(i+1) % n])
            edge_ids.append(eid)
        
        return node_ids
    
    # =========================================================================
    # LOCAL PHYSICS - NO GLOBAL CHECKS
    # =========================================================================
    
    def local_phase_mismatch_at_node(self, node_id: int) -> float:
        """
        Compute LOCAL phase mismatch at a single node.
        
        This measures how well phase transport is consistent
        around this node. NO GLOBAL LOOP SUMS.
        """
        edge_ids = self.adjacency[node_id]
        if len(edge_ids) < 2:
            return 0.0
        
        node_phase = self.nodes[node_id].phase
        
        # Check consistency of incoming/outgoing phases
        mismatch = 0.0
        for eid in edge_ids:
            edge = self.edges[eid]
            
            # Get neighbor phase
            neighbor_id = edge.node_a if edge.node_b == node_id else edge.node_b
            neighbor_phase = self.nodes[neighbor_id].phase
            
            # Expected phase difference (from geometry)
            expected_diff = self.phase_per_junction
            actual_diff = self._wrap_phase(neighbor_phase - node_phase)
            
            # Local mismatch
            local_err = self._wrap_phase(actual_diff - expected_diff)
            mismatch += local_err**2
        
        return mismatch / len(edge_ids)
    
    def local_torsion_at_edge(self, edge_id: int) -> float:
        """
        Compute LOCAL torsion on an edge.
        
        Torsion accumulates when phase transport is inconsistent.
        """
        edge = self.edges[edge_id]
        
        # Phase gradient across edge
        phase_a = self.nodes[edge.node_a].phase
        phase_b = self.nodes[edge.node_b].phase
        actual_gradient = self._wrap_phase(phase_b - phase_a)
        
        # Expected gradient (from geometry)
        expected_gradient = self.phase_per_junction
        
        # Torsion = deviation from expected
        torsion = abs(self._wrap_phase(actual_gradient - expected_gradient))
        
        return torsion
    
    def local_angle_energy_at_node(self, node_id: int) -> float:
        """
        Compute LOCAL angle energy at a junction.
        
        Penalizes deviations from ideal branch angles.
        """
        edge_ids = self.adjacency[node_id]
        degree = len(edge_ids)
        
        if degree < 2:
            return 0.0
        
        node_pos = self.nodes[node_id].position
        
        # Compute directions to neighbors
        directions = []
        for eid in edge_ids:
            edge = self.edges[eid]
            neighbor_id = edge.node_a if edge.node_b == node_id else edge.node_b
            neighbor_pos = self.nodes[neighbor_id].position
            
            d = neighbor_pos - node_pos
            d = d / (np.linalg.norm(d) + 1e-10)
            directions.append(d)
        
        # Compute angles between consecutive directions
        angles = []
        for i in range(len(directions)):
            d1 = directions[i]
            d2 = directions[(i+1) % len(directions)]
            cos_angle = np.clip(np.dot(d1, d2), -1, 1)
            angle = np.arccos(cos_angle)
            angles.append(angle)
        
        # Ideal angle for this degree
        ideal_angle = 2 * np.pi / degree
        
        # Angle deviation energy
        energy = sum((a - ideal_angle)**2 for a in angles)
        
        return energy
    
    def compute_total_local_energy(self) -> Dict[str, float]:
        """
        Compute total energy using ONLY LOCAL measurements.
        
        NO GLOBAL LOOP SUMS OR CLOSURE CHECKS.
        """
        E_tension = 0.0
        E_gradient = 0.0
        E_torsion = 0.0
        E_angle = 0.0
        
        # Edge-local energies
        for eid, edge in self.edges.items():
            # Tension
            node_a_pos = self.nodes[edge.node_a].position
            node_b_pos = self.nodes[edge.node_b].position
            length = np.linalg.norm(node_b_pos - node_a_pos)
            E_tension += self.lambda_tension * length
            
            # Phase gradient penalty
            gradient = abs(edge.phase_gradient)
            E_gradient += self.lambda_phase_gradient * gradient**2
            
            # Torsion
            torsion = self.local_torsion_at_edge(eid)
            E_torsion += self.lambda_torsion * torsion**2
        
        # Node-local energies
        for nid in self.nodes:
            E_angle += self.lambda_angle_mismatch * self.local_angle_energy_at_node(nid)
        
        E_total = E_tension + E_gradient + E_torsion + E_angle
        
        return {
            'E_tension': float(E_tension),
            'E_gradient': float(E_gradient),
            'E_torsion': float(E_torsion),
            'E_angle': float(E_angle),
            'E_total': float(E_total)
        }
    
    # =========================================================================
    # LOCAL DYNAMICS - NO GLOBAL SELECTION
    # =========================================================================
    
    def update_phases_locally(self):
        """
        Update phases using ONLY local transport rules.
        
        Phase flows from node to node based on local gradients.
        NO GLOBAL CLOSURE ENFORCEMENT.
        """
        new_phases = {}
        
        for nid, node in self.nodes.items():
            edge_ids = self.adjacency[nid]
            if not edge_ids:
                new_phases[nid] = node.phase
                continue
            
            # Collect phase influence from neighbors
            phase_influence = 0.0
            
            for eid in edge_ids:
                edge = self.edges[eid]
                neighbor_id = edge.node_a if edge.node_b == nid else edge.node_b
                neighbor_phase = self.nodes[neighbor_id].phase
                
                # Expected phase relationship (from geometry)
                expected_phase = neighbor_phase - self.phase_per_junction
                
                # Phase wants to align with expectation
                diff = self._wrap_phase(expected_phase - node.phase)
                phase_influence += diff
            
            phase_influence /= len(edge_ids)
            
            # Update with noise
            new_phase = node.phase + self.phase_transport_rate * phase_influence * self.dt
            new_phase += self.noise_strength * (np.random.random() - 0.5) * self.dt
            new_phase = self._wrap_phase(new_phase)
            
            new_phases[nid] = new_phase
        
        # Apply updates
        for nid, phase in new_phases.items():
            self.nodes[nid].phase = phase
        
        # Update edge gradients
        for eid, edge in self.edges.items():
            phase_a = self.nodes[edge.node_a].phase
            phase_b = self.nodes[edge.node_b].phase
            edge.phase_gradient = self._wrap_phase(phase_b - phase_a)
    
    def update_positions_locally(self):
        """
        Update positions using local forces.
        """
        forces = {nid: np.zeros(2) for nid in self.nodes}
        
        for eid, edge in self.edges.items():
            node_a = self.nodes[edge.node_a]
            node_b = self.nodes[edge.node_b]
            
            # Direction
            d = node_b.position - node_a.position
            length = np.linalg.norm(d) + 1e-10
            d_hat = d / length
            
            # Tension force (constant length spring)
            target_length = 1.0
            force_mag = edge.tension * (length - target_length)
            
            forces[edge.node_a] += force_mag * d_hat
            forces[edge.node_b] -= force_mag * d_hat
        
        # Apply forces
        for nid, force in forces.items():
            self.nodes[nid].position += 0.01 * force * self.dt
    
    def update_torsion_locally(self):
        """
        Accumulate torsion based on local phase inconsistency.
        """
        for eid, edge in self.edges.items():
            local_torsion = self.local_torsion_at_edge(eid)
            
            # Torsion accumulates over time
            edge.torsion += local_torsion * self.dt
            
            # Torsion also dissipates
            edge.torsion *= 0.99
    
    def evolve_step(self):
        """Single evolution step using ONLY local physics."""
        self.update_phases_locally()
        self.update_positions_locally()
        self.update_torsion_locally()
    
    def evolve(self, n_steps: int) -> Dict:
        """Evolve the system and track local observables."""
        history = {
            'energies': [],
            'phase_coherence': [],
            'torsion_total': []
        }
        
        for step in range(n_steps):
            self.evolve_step()
            
            if step % 50 == 0:
                energy = self.compute_total_local_energy()
                history['energies'].append(energy['E_total'])
                
                # Measure phase coherence (local)
                coherence = self._measure_local_phase_coherence()
                history['phase_coherence'].append(coherence)
                
                # Total torsion
                total_torsion = sum(e.torsion for e in self.edges.values())
                history['torsion_total'].append(total_torsion)
        
        return history
    
    def _measure_local_phase_coherence(self) -> float:
        """
        Measure how coherent the phase structure is.
        
        This is a LOCAL measurement - average consistency
        of phase transport across all edges.
        """
        if not self.edges:
            return 0.0
        
        coherence = 0.0
        for eid, edge in self.edges.items():
            # Check if gradient matches expected
            expected = self.phase_per_junction
            actual = edge.phase_gradient
            
            diff = abs(self._wrap_phase(actual - expected))
            coherence += np.cos(diff)  # 1 if perfect, -1 if opposite
        
        return coherence / len(self.edges)
    
    # =========================================================================
    # MEASUREMENT (post-evolution, no influence on dynamics)
    # =========================================================================
    
    def measure_loop_phase_sum(self, node_ids: List[int]) -> float:
        """
        MEASUREMENT ONLY: Compute total phase around a loop.
        
        This is NOT used during evolution - only for analysis after.
        """
        total_phase = 0.0
        n = len(node_ids)
        
        for i in range(n):
            curr_phase = self.nodes[node_ids[i]].phase
            next_phase = self.nodes[node_ids[(i+1) % n]].phase
            
            # Phase difference
            diff = self._wrap_phase(next_phase - curr_phase)
            total_phase += diff
        
        return total_phase
    
    def measure_effective_loop_size(self, node_ids: List[int]) -> float:
        """
        MEASUREMENT ONLY: What "effective n" does this loop have?
        
        effective_n = total_phase / phase_per_junction
        """
        total_phase = self.measure_loop_phase_sum(node_ids)
        effective_n = abs(total_phase / self.phase_per_junction)
        return effective_n


# =============================================================================
# RULE INDEPENDENCE TEST
# =============================================================================

class RuleIndependenceTest:
    """
    Test whether phase closure EMERGES from local dynamics
    or is IMPOSED by global rules.
    """
    
    def __init__(self):
        self.results = {}
    
    def test_single_loop_evolution(self, n: int, n_steps: int = 5000) -> Dict:
        """
        Evolve a single loop with LOCAL physics only.
        Measure what phase structure emerges.
        """
        network = LocalPhysicsNetwork(seed=n * 17)
        node_ids = network.create_loop(n, random_phase=True)
        
        # Initial measurement
        initial_phase = network.measure_loop_phase_sum(node_ids)
        initial_effective_n = network.measure_effective_loop_size(node_ids)
        
        # Evolve with LOCAL PHYSICS ONLY
        history = network.evolve(n_steps)
        
        # Final measurement
        final_phase = network.measure_loop_phase_sum(node_ids)
        final_effective_n = network.measure_effective_loop_size(node_ids)
        
        # Check if phase locked to discrete value
        expected_phases = [k * np.pi for k in range(-4, 5)]  # multiples of π
        closest_expected = min(expected_phases, key=lambda p: abs(self._wrap(final_phase) - p))
        phase_locked = abs(self._wrap(final_phase) - closest_expected) < 0.3
        
        return {
            'n': n,
            'initial_phase_deg': float(np.degrees(initial_phase)),
            'final_phase_deg': float(np.degrees(final_phase)),
            'initial_effective_n': float(initial_effective_n),
            'final_effective_n': float(final_effective_n),
            'phase_locked': phase_locked,
            'locked_to': float(np.degrees(closest_expected)),
            'final_coherence': history['phase_coherence'][-1] if history['phase_coherence'] else 0,
            'final_energy': history['energies'][-1] if history['energies'] else 0
        }
    
    def _wrap(self, phase: float) -> float:
        while phase > np.pi:
            phase -= 2 * np.pi
        while phase < -np.pi:
            phase += 2 * np.pi
        return phase
    
    def test_emergence_from_random(self) -> Dict:
        """
        TEST A: Start from random phases.
        Does discrete structure EMERGE?
        """
        print("=" * 70)
        print("TEST A: EMERGENCE FROM RANDOM INITIAL CONDITIONS")
        print("=" * 70)
        print("""
Starting loops with RANDOM phases.
Evolving with LOCAL physics ONLY (no closure checks).
Measuring what phase structure emerges.

If n=6,12,18 phase structures emerge → DISCRETE CLOSURE IS EMERGENT
If random/continuous → CLOSURE WAS IMPOSED (model incomplete)
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Init Phase':>12} | {'Final Phase':>12} | {'Locked?':>8} | {'To':>10} | {'Coherence':>10}")
        print("-" * 75)
        
        for n in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
            result = self.test_single_loop_evolution(n, n_steps=5000)
            
            marker = "✓" if result['phase_locked'] else " "
            print(f"{n:>4} | {result['initial_phase_deg']:>11.1f}° | {result['final_phase_deg']:>11.1f}° | "
                  f"{marker:>8} | {result['locked_to']:>9.0f}° | {result['final_coherence']:>10.3f}")
            
            results.append(result)
        
        # Analysis
        locked_count = sum(1 for r in results if r['phase_locked'])
        
        print(f"\nPhase-locked loops: {locked_count}/{len(results)}")
        
        # Check if locking correlates with n
        locked_ns = [r['n'] for r in results if r['phase_locked']]
        print(f"Locked at n = {locked_ns}")
        
        return {
            'locked_count': locked_count,
            'locked_ns': locked_ns,
            'details': results
        }
    
    def test_coherence_vs_loop_size(self) -> Dict:
        """
        TEST B: Does phase coherence depend on loop size?
        Higher coherence for n=6,12 would suggest emergent selection.
        """
        print("\n" + "=" * 70)
        print("TEST B: COHERENCE VS LOOP SIZE")
        print("=" * 70)
        print("""
Measuring phase coherence (how well local transport matches expected).
If n=6,12 have higher coherence → those sizes are PREFERRED by dynamics
If coherence is uniform → no size selection
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Coherence':>10} | {'Final Energy':>12} | {'Bar'}")
        print("-" * 60)
        
        for n in range(3, 19):
            # Average over multiple trials
            coherences = []
            energies = []
            
            for trial in range(5):
                network = LocalPhysicsNetwork(seed=n * 100 + trial)
                node_ids = network.create_loop(n, random_phase=True)
                history = network.evolve(3000)
                
                coherences.append(history['phase_coherence'][-1])
                energies.append(history['energies'][-1])
            
            avg_coherence = np.mean(coherences)
            avg_energy = np.mean(energies)
            
            # Visual bar
            bar_len = int((avg_coherence + 1) * 15)  # coherence in [-1, 1]
            bar = "#" * max(0, bar_len)
            
            marker = ""
            if n == 6:
                marker = " ← FERMION?"
            elif n == 12:
                marker = " ← BOSON?"
            
            print(f"{n:>4} | {avg_coherence:>10.3f} | {avg_energy:>12.2f} | {bar}{marker}")
            
            results.append({
                'n': n,
                'coherence': float(avg_coherence),
                'energy': float(avg_energy)
            })
        
        # Find peaks
        coherences = [r['coherence'] for r in results]
        ns = [r['n'] for r in results]
        
        # Simple peak detection
        peaks = []
        for i in range(1, len(coherences) - 1):
            if coherences[i] > coherences[i-1] and coherences[i] > coherences[i+1]:
                peaks.append(ns[i])
        
        print(f"\nCoherence peaks at n = {peaks}")
        
        return {
            'details': results,
            'coherence_peaks': peaks
        }
    
    def test_phase_distribution(self) -> Dict:
        """
        TEST C: Distribution of final phases across many trials.
        If quantized → clustering at discrete values
        If continuous → uniform distribution
        """
        print("\n" + "=" * 70)
        print("TEST C: PHASE DISTRIBUTION (Many Trials)")
        print("=" * 70)
        print("""
Running 100 trials with random initial conditions.
Measuring distribution of final loop phases.

If phases cluster at 180°, 360° → DISCRETE EMERGENCE
If phases are uniform → NO EMERGENCE
""")
        
        final_phases = []
        
        for trial in range(100):
            n = np.random.randint(4, 15)
            network = LocalPhysicsNetwork(seed=trial)
            node_ids = network.create_loop(n, random_phase=True)
            
            network.evolve(3000)
            
            final_phase = network.measure_loop_phase_sum(node_ids)
            final_phases.append(np.degrees(final_phase))
        
        # Bin phases
        bins = np.arange(-360, 361, 30)
        hist, bin_edges = np.histogram(final_phases, bins=bins)
        
        print("\nPhase distribution (30° bins):")
        for i, count in enumerate(hist):
            if count > 0:
                bin_center = (bin_edges[i] + bin_edges[i+1]) / 2
                bar = "#" * count
                
                marker = ""
                if abs(bin_center - 180) < 15 or abs(bin_center + 180) < 15:
                    marker = " ← π (fermion)"
                elif abs(bin_center) < 15 or abs(bin_center - 360) < 15 or abs(bin_center + 360) < 15:
                    marker = " ← 0 (boson)"
                
                print(f"  {bin_center:>6.0f}°: {bar} ({count}){marker}")
        
        # Check for clustering
        # Compute clustering metric
        target_phases = [0, 180, -180, 360, -360]
        close_to_target = sum(1 for p in final_phases 
                              if any(abs(p - t) < 30 for t in target_phases))
        
        print(f"\nPhases within 30° of 0° or 180°: {close_to_target}/100")
        
        return {
            'phase_distribution': list(zip(bins[:-1].tolist(), hist.tolist())),
            'clustering_fraction': close_to_target / 100
        }
    
    def test_sensitivity(self) -> Dict:
        """
        TEST D: Sensitivity to parameters.
        Vary key parameters and check if emergence is robust.
        """
        print("\n" + "=" * 70)
        print("TEST D: PARAMETER SENSITIVITY")
        print("=" * 70)
        print("""
Testing robustness of emergence across parameter variations.
""")
        
        results = []
        
        base_params = {
            'phase_transport_rate': 0.1,
            'lambda_phase_gradient': 2.0,
            'lambda_torsion': 1.5,
            'noise_strength': 0.01
        }
        
        # Test variations
        variations = [
            ('baseline', {}),
            ('high_transport', {'phase_transport_rate': 0.3}),
            ('low_transport', {'phase_transport_rate': 0.03}),
            ('high_gradient_penalty', {'lambda_phase_gradient': 5.0}),
            ('low_gradient_penalty', {'lambda_phase_gradient': 0.5}),
            ('high_noise', {'noise_strength': 0.05}),
            ('no_noise', {'noise_strength': 0.0}),
        ]
        
        print(f"\n{'Variation':>25} | {'Coherence':>10} | {'Phase Locked':>12}")
        print("-" * 55)
        
        for name, changes in variations:
            # Create network with modified parameters
            network = LocalPhysicsNetwork(seed=42)
            
            # Apply changes
            for key, value in changes.items():
                setattr(network, key, value)
            
            # Test with n=6
            node_ids = network.create_loop(6, random_phase=True)
            history = network.evolve(5000)
            
            final_phase = network.measure_loop_phase_sum(node_ids)
            final_coherence = history['phase_coherence'][-1]
            
            # Check if locked to π
            locked = abs(abs(final_phase) - np.pi) < 0.3
            
            print(f"{name:>25} | {final_coherence:>10.3f} | {'YES' if locked else 'NO':>12}")
            
            results.append({
                'name': name,
                'coherence': final_coherence,
                'locked': locked,
                'final_phase_deg': float(np.degrees(final_phase))
            })
        
        robust = sum(1 for r in results if r['locked'])
        print(f"\nPhase locked in {robust}/{len(results)} variations")
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all rule independence tests."""
        print("=" * 80)
        print("  QMRT: RULE INDEPENDENCE TEST")
        print("=" * 80)
        print("""
CRITICAL QUESTION:
  Does phase closure EMERGE from local dynamics,
  or was it IMPOSED by the algorithm?

METHODOLOGY:
  - REMOVED: All global closure checks
  - REMOVED: Discrete quantization filters
  - REMOVED: n=6k selection rules
  
  - KEPT: Local phase transport
  - KEPT: Local mismatch penalties
  - KEPT: Local torsion accumulation

NOW: Does discrete structure emerge anyway?
""")
        
        results = {}
        
        results['emergence'] = self.test_emergence_from_random()
        results['coherence'] = self.test_coherence_vs_loop_size()
        results['distribution'] = self.test_phase_distribution()
        results['sensitivity'] = self.test_sensitivity()
        
        # Final Analysis
        print("\n" + "=" * 80)
        print("FINAL ANALYSIS")
        print("=" * 80)
        
        # Check for emergence
        locked_ns = results['emergence']['locked_ns']
        coherence_peaks = results['coherence']['coherence_peaks']
        clustering = results['distribution']['clustering_fraction']
        sensitivity_robust = sum(1 for r in results['sensitivity'] if r['locked'])
        
        print(f"""
EMERGENCE INDICATORS:

1. Phase locking from random start:
   Locked at n = {locked_ns}
   {"✓ DISCRETE EMERGENCE" if 6 in locked_ns or 12 in locked_ns else "✗ No special sizes"}

2. Coherence peaks:
   Peaks at n = {coherence_peaks}
   {"✓ SIZE PREFERENCE" if 6 in coherence_peaks or 12 in coherence_peaks else "✗ No preference"}

3. Phase clustering:
   {clustering:.0%} cluster near 0° or 180°
   {"✓ DISCRETE DISTRIBUTION" if clustering > 0.3 else "✗ Continuous distribution"}

4. Parameter robustness:
   {sensitivity_robust}/{len(results['sensitivity'])} variations show locking
   {"✓ ROBUST" if sensitivity_robust > 4 else "✗ Sensitive"}
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        emergence_score = 0
        if 6 in locked_ns or 12 in locked_ns:
            emergence_score += 1
        if 6 in coherence_peaks or 12 in coherence_peaks:
            emergence_score += 1
        if clustering > 0.3:
            emergence_score += 1
        if sensitivity_robust > 4:
            emergence_score += 1
        
        if emergence_score >= 3:
            verdict = "EMERGENCE_CONFIRMED"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ DISCRETE PHASE CLOSURE IS EMERGENT                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Local physics alone produces discrete phase structure.                       ║
║  No global closure rules were needed.                                         ║
║  The medium dynamically selects phase-closed states.                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        elif emergence_score >= 1:
            verdict = "PARTIAL_EMERGENCE"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ PARTIAL EMERGENCE                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Some discrete structure appears, but not robustly.                          ║
║  Additional physics may be needed:                                            ║
║    - Phase conservation constraints                                           ║
║    - Branch-level dynamics                                                    ║
║    - Stronger torsion feedback                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "NO_EMERGENCE"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ❌ DISCRETE CLOSURE DOES NOT EMERGE FROM CURRENT LOCAL PHYSICS              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  The previous results depended on IMPOSED quantization.                       ║
║  Local phase transport alone is insufficient.                                 ║
║                                                                              ║
║  Missing physics candidates:                                                  ║
║    1. Phase conservation / finite transport speed                            ║
║    2. Structure-stability feedback loop                                       ║
║    3. Branch-level interference (trunk dynamics)                              ║
║    4. Resonance from standing wave conditions                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Save results
        output = {
            'test': 'Rule_Independence',
            'verdict': verdict,
            'emergence_score': emergence_score,
            'emergence_from_random': results['emergence'],
            'coherence_analysis': results['coherence'],
            'phase_distribution': results['distribution'],
            'sensitivity_analysis': results['sensitivity'],
            'conclusions': {
                'locked_ns': locked_ns,
                'coherence_peaks': coherence_peaks,
                'clustering_fraction': clustering,
                'sensitivity_robust': sensitivity_robust
            }
        }
        
        output_path = '/app/backend/qmrt_topology/rule_independence_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = RuleIndependenceTest()
    results = test.run_all_tests()
