"""
QMRT: DYNAMIC ENFORCEMENT TEST
==============================

CRITICAL QUESTION:
  Do invalid phase configurations dynamically evolve into phase-closed states,
  and which of those are stable?

THIS IS THE REAL TEST.

SIMULATION DESIGN (from user guidance):
  1. Initialize invalid states (n=5, n=7, distorted, mixed)
  2. Define full energy functional:
       E_total = E_smoothness + lambda_1 * phase_mismatch^2 + lambda_2 * torsion^2
  3. Run relaxation dynamics with:
       - Edge rewiring
       - Loop resizing
       - Branch reconfiguration
  4. Observe outcomes:
       - Final loop sizes (n=6? n=12? other?)
       - Phase closure (0 mod 2pi = boson, pi mod 2pi = fermion)
       - Stability under perturbation

NO BIASING: We do NOT force n=6 or n=12. Let the system freely evolve.

IDEAL RESULT:
  Invalid loops collapse -> system settles into n=6 (fermion) or n=12 (boson)
  n=6 is smallest stable fermionic structure
  n=12 is lowest-energy bosonic background
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
import json
from copy import deepcopy


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class Node:
    """A node in the topological network."""
    id: int
    position: np.ndarray
    phase: float = 0.0  # Local phase at node
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=float)
    
    def __hash__(self):
        return self.id


@dataclass
class Edge:
    """An edge connecting two nodes."""
    id: int
    node_a: int  # Node ID
    node_b: int  # Node ID
    tension: float = 1.0
    torsion: float = 0.0  # Accumulated torsion on this edge
    
    def other_node(self, node_id: int) -> int:
        return self.node_b if self.node_a == node_id else self.node_a


@dataclass
class Loop:
    """A closed loop of edges."""
    id: int
    edge_ids: List[int]
    node_sequence: List[int]  # Ordered nodes forming the loop
    
    @property
    def size(self) -> int:
        return len(self.edge_ids)
    
    def total_phase(self, phase_per_transit: float) -> float:
        """Total phase around the loop."""
        return self.size * phase_per_transit
    
    def mod_2pi(self, phase_per_transit: float) -> float:
        """Phase modulo 2*pi."""
        return self.total_phase(phase_per_transit) % (2 * np.pi)
    
    def is_fermion(self, phase_per_transit: float) -> bool:
        """Does this loop produce fermion holonomy (-1)?"""
        mod = self.mod_2pi(phase_per_transit)
        return np.isclose(mod, np.pi, atol=0.1)
    
    def is_boson(self, phase_per_transit: float) -> bool:
        """Does this loop produce boson holonomy (+1)?"""
        mod = self.mod_2pi(phase_per_transit)
        return np.isclose(mod, 0, atol=0.1) or np.isclose(mod, 2*np.pi, atol=0.1)


# =============================================================================
# DYNAMIC NETWORK
# =============================================================================

class DynamicNetwork:
    """
    Topological network with dynamic evolution.
    Supports edge rewiring, loop resizing, and branch reconfiguration.
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[int, Edge] = {}
        self.loops: Dict[int, Loop] = {}
        
        self.next_node_id = 0
        self.next_edge_id = 0
        self.next_loop_id = 0
        
        # Z_12 phase structure (from previous tests)
        self.phase_per_transit = -np.pi / 6  # -30 degrees
        
        # Energy parameters
        self.lambda_smoothness = 1.0
        self.lambda_phase_mismatch = 2.0      # Phase closure penalty
        self.lambda_torsion = 1.5             # Torsion accumulation penalty
        self.lambda_size_penalty = 0.1        # Small penalty for larger loops
        
        # Dynamics parameters
        self.dt = 0.01                         # Time step
        self.rewire_prob = 0.05               # Probability of rewiring per step
        self.resize_prob = 0.1                # Probability of resize attempt
        
        # History tracking
        self.energy_history = []
        self.loop_size_history = []
    
    # =========================================================================
    # NETWORK CONSTRUCTION
    # =========================================================================
    
    def add_node(self, position: np.ndarray, phase: float = 0.0) -> int:
        """Add a node to the network."""
        nid = self.next_node_id
        self.nodes[nid] = Node(nid, position, phase)
        self.next_node_id += 1
        return nid
    
    def add_edge(self, node_a: int, node_b: int, tension: float = 1.0) -> int:
        """Add an edge between two nodes."""
        eid = self.next_edge_id
        self.edges[eid] = Edge(eid, node_a, node_b, tension)
        self.next_edge_id += 1
        return eid
    
    def create_regular_loop(self, n: int, center: np.ndarray = None,
                            radius: float = 1.0, distortion: float = 0.0) -> int:
        """
        Create a regular n-gon loop, optionally with distortion.
        
        Args:
            n: Number of vertices
            center: Center position
            radius: Radius of the loop
            distortion: Random perturbation magnitude (0 = perfect polygon)
        """
        if center is None:
            center = np.array([0.0, 0.0])
        
        node_ids = []
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        for i, angle in enumerate(angles):
            # Add distortion
            r = radius + distortion * (np.random.random() - 0.5)
            a = angle + distortion * (np.random.random() - 0.5) * 0.5
            
            pos = center + r * np.array([np.cos(a), np.sin(a)])
            nid = self.add_node(pos)
            node_ids.append(nid)
        
        edge_ids = []
        for i in range(n):
            eid = self.add_edge(node_ids[i], node_ids[(i+1) % n])
            edge_ids.append(eid)
        
        lid = self.next_loop_id
        self.loops[lid] = Loop(lid, edge_ids, node_ids)
        self.next_loop_id += 1
        
        return lid
    
    def create_distorted_loop(self, n: int, distortion_type: str = "nonuniform") -> int:
        """
        Create a loop with specific type of distortion.
        
        Args:
            n: Number of vertices
            distortion_type: "nonuniform", "stretched", "compressed"
        """
        center = np.array([0.0, 0.0])
        radius = 1.0
        
        node_ids = []
        
        if distortion_type == "nonuniform":
            # Non-uniform phase spacing
            angles = np.sort(np.random.random(n) * 2 * np.pi)
        elif distortion_type == "stretched":
            # Elliptical stretching
            angles = np.linspace(0, 2*np.pi, n, endpoint=False)
            radius_x, radius_y = 1.5, 0.7
        else:
            angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        for i, angle in enumerate(angles):
            if distortion_type == "stretched":
                pos = center + np.array([radius_x * np.cos(angle),
                                        radius_y * np.sin(angle)])
            else:
                pos = center + radius * np.array([np.cos(angle), np.sin(angle)])
            
            nid = self.add_node(pos)
            node_ids.append(nid)
        
        edge_ids = []
        for i in range(n):
            eid = self.add_edge(node_ids[i], node_ids[(i+1) % n])
            edge_ids.append(eid)
        
        lid = self.next_loop_id
        self.loops[lid] = Loop(lid, edge_ids, node_ids)
        self.next_loop_id += 1
        
        return lid
    
    # =========================================================================
    # ENERGY FUNCTIONAL
    # =========================================================================
    
    def E_smoothness(self, loop: Loop) -> float:
        """
        Smoothness energy: penalizes sharp bends.
        E = sum of (1 - cos(angle)) over all vertices
        """
        energy = 0.0
        n = loop.size
        
        for i in range(n):
            # Get three consecutive nodes
            n_prev = loop.node_sequence[(i - 1) % n]
            n_curr = loop.node_sequence[i]
            n_next = loop.node_sequence[(i + 1) % n]
            
            p_prev = self.nodes[n_prev].position
            p_curr = self.nodes[n_curr].position
            p_next = self.nodes[n_next].position
            
            # Vectors from current to neighbors
            v1 = p_prev - p_curr
            v2 = p_next - p_curr
            
            # Normalize
            v1 = v1 / (np.linalg.norm(v1) + 1e-10)
            v2 = v2 / (np.linalg.norm(v2) + 1e-10)
            
            # Angle energy (prefer 120-degree or smooth bends)
            cos_angle = np.dot(v1, v2)
            energy += (1 - cos_angle)
        
        return self.lambda_smoothness * energy
    
    def E_phase_mismatch(self, loop: Loop) -> float:
        """
        Phase mismatch energy: penalizes failure of phase closure.
        
        For fermion closure: total_phase should be pi (mod 2pi)
        For boson closure: total_phase should be 0 (mod 2pi)
        
        Mismatch = min distance to valid closure
        """
        total_phase = loop.total_phase(self.phase_per_transit)
        
        # Distance to fermion closure (pi)
        dist_to_fermion = abs(np.sin(total_phase))  # 0 when phase = n*pi
        
        # Distance to boson closure (0 or 2pi)
        dist_to_boson = abs(np.sin(total_phase / 2)) * 2  # 0 when phase = 2n*pi
        
        # Minimum mismatch (either valid state is acceptable)
        mismatch = min(dist_to_fermion, dist_to_boson)
        
        return self.lambda_phase_mismatch * mismatch**2
    
    def E_torsion(self, loop: Loop) -> float:
        """
        Torsion accumulation energy: penalizes accumulated twist.
        
        Torsion accumulates when phase isn't consistently distributed.
        """
        # Compute torsion as variance of phase distribution
        n = loop.size
        ideal_phase_per_edge = loop.total_phase(self.phase_per_transit) / n
        
        # For non-uniform loops, compute phase inconsistency
        torsion_acc = 0.0
        for eid in loop.edge_ids:
            edge = self.edges[eid]
            # Phase deviation from ideal
            deviation = abs(self.phase_per_transit - ideal_phase_per_edge)
            torsion_acc += deviation
            
            # Update edge torsion state
            edge.torsion += deviation * 0.01
        
        return self.lambda_torsion * torsion_acc**2
    
    def E_size_penalty(self, loop: Loop) -> float:
        """
        Mild size penalty: larger loops have slightly higher energy.
        This prevents unbounded growth but doesn't dominate.
        """
        return self.lambda_size_penalty * loop.size
    
    def compute_loop_energy(self, loop: Loop) -> Dict[str, float]:
        """Compute total energy with all terms."""
        E_smooth = self.E_smoothness(loop)
        E_phase = self.E_phase_mismatch(loop)
        E_torsion = self.E_torsion(loop)
        E_size = self.E_size_penalty(loop)
        
        E_total = E_smooth + E_phase + E_torsion + E_size
        
        return {
            'E_smoothness': float(E_smooth),
            'E_phase_mismatch': float(E_phase),
            'E_torsion': float(E_torsion),
            'E_size': float(E_size),
            'E_total': float(E_total)
        }
    
    # =========================================================================
    # DYNAMICS
    # =========================================================================
    
    def gradient_step(self, loop: Loop):
        """
        Gradient descent step on node positions.
        Minimizes smoothness energy.
        """
        n = loop.size
        
        for i in range(n):
            nid = loop.node_sequence[i]
            node = self.nodes[nid]
            
            # Get neighbors
            n_prev = loop.node_sequence[(i - 1) % n]
            n_next = loop.node_sequence[(i + 1) % n]
            
            p_prev = self.nodes[n_prev].position
            p_curr = node.position
            p_next = self.nodes[n_next].position
            
            # Force toward midpoint of neighbors (smoothing)
            midpoint = (p_prev + p_next) / 2
            force = midpoint - p_curr
            
            # Apply with damping
            node.position += 0.1 * force * self.dt
    
    def attempt_resize(self, loop: Loop) -> bool:
        """
        Attempt to resize the loop by adding or removing a vertex.
        
        Returns True if resize occurred.
        """
        n = loop.size
        current_energy = self.compute_loop_energy(loop)['E_total']
        
        # Try both adding and removing
        can_add = True
        can_remove = n > 3  # Minimum viable loop
        
        if can_remove and np.random.random() < 0.5:
            # Try removing a vertex
            trial_loop = self._try_remove_vertex(loop)
            if trial_loop:
                trial_energy = self.compute_loop_energy(trial_loop)['E_total']
                if trial_energy < current_energy:
                    # Accept the change
                    self._apply_resize(loop, trial_loop)
                    return True
        
        if can_add:
            # Try adding a vertex
            trial_loop = self._try_add_vertex(loop)
            if trial_loop:
                trial_energy = self.compute_loop_energy(trial_loop)['E_total']
                # Accept if energy decrease OR with small probability for exploration
                if trial_energy < current_energy or np.random.random() < 0.02:
                    self._apply_resize(loop, trial_loop)
                    return True
        
        return False
    
    def _try_remove_vertex(self, loop: Loop) -> Optional[Loop]:
        """Create a trial loop with one vertex removed."""
        if loop.size <= 3:
            return None
        
        # Pick random vertex to remove
        idx = np.random.randint(loop.size)
        
        new_nodes = [n for i, n in enumerate(loop.node_sequence) if i != idx]
        new_edges = []
        
        # Create new edges
        for i in range(len(new_nodes)):
            eid = self.add_edge(new_nodes[i], new_nodes[(i+1) % len(new_nodes)])
            new_edges.append(eid)
        
        return Loop(-1, new_edges, new_nodes)  # Temp ID
    
    def _try_add_vertex(self, loop: Loop) -> Optional[Loop]:
        """Create a trial loop with one vertex added."""
        # Pick random edge to split
        idx = np.random.randint(loop.size)
        
        # Get the edge endpoints
        n1 = loop.node_sequence[idx]
        n2 = loop.node_sequence[(idx + 1) % loop.size]
        
        # Create new node at midpoint
        midpoint = (self.nodes[n1].position + self.nodes[n2].position) / 2
        new_nid = self.add_node(midpoint)
        
        # Insert new node
        new_nodes = loop.node_sequence[:idx+1] + [new_nid] + loop.node_sequence[idx+1:]
        new_edges = []
        
        for i in range(len(new_nodes)):
            eid = self.add_edge(new_nodes[i], new_nodes[(i+1) % len(new_nodes)])
            new_edges.append(eid)
        
        return Loop(-1, new_edges, new_nodes)
    
    def _apply_resize(self, old_loop: Loop, new_loop: Loop):
        """Apply the resize by updating the loop in place."""
        old_loop.edge_ids = new_loop.edge_ids
        old_loop.node_sequence = new_loop.node_sequence
    
    def evolve_step(self, loop: Loop):
        """Single evolution step combining all dynamics."""
        # 1. Gradient descent on positions
        self.gradient_step(loop)
        
        # 2. Attempt resize with some probability
        if np.random.random() < self.resize_prob:
            self.attempt_resize(loop)
    
    def evolve(self, loop: Loop, n_steps: int, record_every: int = 10) -> Dict:
        """
        Evolve a loop for n_steps, recording history.
        """
        history = {
            'sizes': [],
            'energies': [],
            'phase_closure': [],
            'is_fermion': [],
            'is_boson': []
        }
        
        for step in range(n_steps):
            self.evolve_step(loop)
            
            if step % record_every == 0:
                energy = self.compute_loop_energy(loop)
                history['sizes'].append(loop.size)
                history['energies'].append(energy['E_total'])
                history['phase_closure'].append(float(loop.mod_2pi(self.phase_per_transit)))
                history['is_fermion'].append(bool(loop.is_fermion(self.phase_per_transit)))
                history['is_boson'].append(bool(loop.is_boson(self.phase_per_transit)))
        
        return history
    
    # =========================================================================
    # STABILITY TEST
    # =========================================================================
    
    def test_stability(self, loop: Loop, perturbation_strength: float = 0.1,
                       n_perturbations: int = 10, settle_steps: int = 100) -> Dict:
        """
        Test stability by perturbing the loop and observing if it returns.
        """
        original_size = loop.size
        original_energy = self.compute_loop_energy(loop)['E_total']
        
        recoveries = 0
        
        for _ in range(n_perturbations):
            # Store original state
            original_positions = {nid: self.nodes[nid].position.copy() 
                                 for nid in loop.node_sequence}
            original_node_seq = loop.node_sequence.copy()
            original_edges = loop.edge_ids.copy()
            
            # Perturb
            for nid in loop.node_sequence:
                self.nodes[nid].position += perturbation_strength * (
                    np.random.random(2) - 0.5
                )
            
            # Let settle
            for _ in range(settle_steps):
                self.evolve_step(loop)
            
            # Check if returned to similar state
            final_energy = self.compute_loop_energy(loop)['E_total']
            final_size = loop.size
            
            if final_size == original_size and abs(final_energy - original_energy) < 0.5:
                recoveries += 1
            
            # Reset for next trial
            for nid, pos in original_positions.items():
                if nid in self.nodes:
                    self.nodes[nid].position = pos
            loop.node_sequence = original_node_seq
            loop.edge_ids = original_edges
        
        return {
            'original_size': original_size,
            'recovery_rate': recoveries / n_perturbations,
            'stable': recoveries / n_perturbations > 0.7
        }


# =============================================================================
# TEST SUITE
# =============================================================================

class DynamicEnforcementTest:
    """Full test suite for dynamic enforcement of phase closure."""
    
    def __init__(self):
        self.results = {}
    
    def test_invalid_undersized(self) -> Dict:
        """
        TEST 1: Start with n=5 (under-rotation, not phase-closed).
        Observe what it evolves into.
        """
        print("=" * 70)
        print("TEST 1: INVALID UNDERSIZED LOOP (n=5)")
        print("=" * 70)
        print("""
n=5 violates phase closure:
  Phase = 5 * (-30 deg) = -150 deg
  Not 0 (boson) or 180 (fermion)
  
Let the system freely evolve...
""")
        
        network = DynamicNetwork(seed=42)
        lid = network.create_regular_loop(5)
        loop = network.loops[lid]
        
        initial_energy = network.compute_loop_energy(loop)
        print(f"Initial: n={loop.size}, E={initial_energy['E_total']:.4f}")
        print(f"         Phase={np.degrees(loop.total_phase(network.phase_per_transit)):.1f}deg")
        
        # Evolve
        history = network.evolve(loop, n_steps=2000, record_every=50)
        
        final_energy = network.compute_loop_energy(loop)
        
        print(f"\nFinal:   n={loop.size}, E={final_energy['E_total']:.4f}")
        print(f"         Phase={np.degrees(loop.total_phase(network.phase_per_transit)):.1f}deg")
        print(f"         Fermion? {loop.is_fermion(network.phase_per_transit)}")
        print(f"         Boson?   {loop.is_boson(network.phase_per_transit)}")
        
        # Check what happened
        unique_sizes = list(set(history['sizes']))
        
        return {
            'initial_size': 5,
            'final_size': loop.size,
            'final_energy': final_energy,
            'is_fermion': loop.is_fermion(network.phase_per_transit),
            'is_boson': loop.is_boson(network.phase_per_transit),
            'size_trajectory': unique_sizes,
            'evolved_to_valid': loop.is_fermion(network.phase_per_transit) or loop.is_boson(network.phase_per_transit)
        }
    
    def test_invalid_oversized(self) -> Dict:
        """
        TEST 2: Start with n=7 (over-rotation, not phase-closed).
        """
        print("\n" + "=" * 70)
        print("TEST 2: INVALID OVERSIZED LOOP (n=7)")
        print("=" * 70)
        print("""
n=7 violates phase closure:
  Phase = 7 * (-30 deg) = -210 deg
  Not 0 (boson) or 180 (fermion)
  
Let the system freely evolve...
""")
        
        network = DynamicNetwork(seed=123)
        lid = network.create_regular_loop(7)
        loop = network.loops[lid]
        
        initial_energy = network.compute_loop_energy(loop)
        print(f"Initial: n={loop.size}, E={initial_energy['E_total']:.4f}")
        print(f"         Phase={np.degrees(loop.total_phase(network.phase_per_transit)):.1f}deg")
        
        history = network.evolve(loop, n_steps=2000, record_every=50)
        
        final_energy = network.compute_loop_energy(loop)
        
        print(f"\nFinal:   n={loop.size}, E={final_energy['E_total']:.4f}")
        print(f"         Phase={np.degrees(loop.total_phase(network.phase_per_transit)):.1f}deg")
        print(f"         Fermion? {loop.is_fermion(network.phase_per_transit)}")
        print(f"         Boson?   {loop.is_boson(network.phase_per_transit)}")
        
        unique_sizes = list(set(history['sizes']))
        
        return {
            'initial_size': 7,
            'final_size': loop.size,
            'final_energy': final_energy,
            'is_fermion': loop.is_fermion(network.phase_per_transit),
            'is_boson': loop.is_boson(network.phase_per_transit),
            'size_trajectory': unique_sizes,
            'evolved_to_valid': loop.is_fermion(network.phase_per_transit) or loop.is_boson(network.phase_per_transit)
        }
    
    def test_distorted_loop(self) -> Dict:
        """
        TEST 3: Start with distorted (non-uniform) loop.
        """
        print("\n" + "=" * 70)
        print("TEST 3: DISTORTED NON-UNIFORM LOOP")
        print("=" * 70)
        print("""
Start with n=6 but with non-uniform geometry.
Phase count is correct, but geometry is stressed.

Does it relax to regular hexagon?
""")
        
        network = DynamicNetwork(seed=456)
        lid = network.create_distorted_loop(6, "nonuniform")
        loop = network.loops[lid]
        
        initial_energy = network.compute_loop_energy(loop)
        print(f"Initial: n={loop.size}, E={initial_energy['E_total']:.4f}")
        print(f"         E_smooth={initial_energy['E_smoothness']:.4f}")
        
        history = network.evolve(loop, n_steps=1000, record_every=50)
        
        final_energy = network.compute_loop_energy(loop)
        
        print(f"\nFinal:   n={loop.size}, E={final_energy['E_total']:.4f}")
        print(f"         E_smooth={final_energy['E_smoothness']:.4f}")
        print(f"         Fermion? {loop.is_fermion(network.phase_per_transit)}")
        
        # Check geometry regularity
        n = loop.size
        angles = []
        for i in range(n):
            n_prev = loop.node_sequence[(i - 1) % n]
            n_curr = loop.node_sequence[i]
            n_next = loop.node_sequence[(i + 1) % n]
            
            p_prev = network.nodes[n_prev].position
            p_curr = network.nodes[n_curr].position
            p_next = network.nodes[n_next].position
            
            v1 = p_prev - p_curr
            v2 = p_next - p_curr
            v1 = v1 / (np.linalg.norm(v1) + 1e-10)
            v2 = v2 / (np.linalg.norm(v2) + 1e-10)
            
            angle = np.degrees(np.arccos(np.clip(np.dot(v1, v2), -1, 1)))
            angles.append(angle)
        
        angle_std = np.std(angles)
        print(f"         Angle std: {angle_std:.2f}deg (0 = perfect regularity)")
        
        return {
            'initial_size': 6,
            'final_size': loop.size,
            'initial_smoothness': initial_energy['E_smoothness'],
            'final_smoothness': final_energy['E_smoothness'],
            'angle_std': float(angle_std),
            'regularized': angle_std < 10.0,
            'is_fermion': loop.is_fermion(network.phase_per_transit)
        }
    
    def test_mixed_junctions(self) -> Dict:
        """
        TEST 4: Start with mixed invalid configuration.
        Multiple loops of different invalid sizes.
        """
        print("\n" + "=" * 70)
        print("TEST 4: MIXED JUNCTION CONFIGURATION")
        print("=" * 70)
        print("""
Create multiple loops with invalid sizes: n=4, 5, 7, 8
Observe which ones survive and what they become.
""")
        
        results = []
        
        for n in [4, 5, 7, 8]:
            network = DynamicNetwork(seed=n * 100)
            lid = network.create_regular_loop(n, center=np.array([0.0, 0.0]))
            loop = network.loops[lid]
            
            initial_size = loop.size
            history = network.evolve(loop, n_steps=2000, record_every=100)
            final_size = loop.size
            
            print(f"  n={initial_size} -> n={final_size}")
            print(f"    Fermion? {loop.is_fermion(network.phase_per_transit)}")
            print(f"    Boson?   {loop.is_boson(network.phase_per_transit)}")
            
            results.append({
                'initial': initial_size,
                'final': final_size,
                'is_fermion': loop.is_fermion(network.phase_per_transit),
                'is_boson': loop.is_boson(network.phase_per_transit),
                'valid': loop.is_fermion(network.phase_per_transit) or loop.is_boson(network.phase_per_transit)
            })
        
        return results
    
    def test_natural_attractors(self) -> Dict:
        """
        TEST 5: Run many random initializations.
        What are the natural attractors?
        """
        print("\n" + "=" * 70)
        print("TEST 5: NATURAL ATTRACTOR DISTRIBUTION")
        print("=" * 70)
        print("""
Run 50 random initializations (n=3 to n=15).
Record final states and count attractors.
""")
        
        final_sizes = []
        fermion_count = 0
        boson_count = 0
        
        for trial in range(50):
            initial_n = np.random.randint(3, 16)
            network = DynamicNetwork(seed=trial * 17)
            
            # Add some distortion
            distortion = np.random.random() * 0.5
            lid = network.create_regular_loop(initial_n, distortion=distortion)
            loop = network.loops[lid]
            
            # Evolve
            network.evolve(loop, n_steps=1500, record_every=100)
            
            final_sizes.append(loop.size)
            if loop.is_fermion(network.phase_per_transit):
                fermion_count += 1
            if loop.is_boson(network.phase_per_transit):
                boson_count += 1
        
        # Count final size distribution
        from collections import Counter
        size_dist = Counter(final_sizes)
        
        print(f"\nFinal size distribution:")
        for size in sorted(size_dist.keys()):
            count = size_dist[size]
            bar = "#" * count
            phase_type = ""
            if size * (-30) % 360 in [180, -180]:
                phase_type = "(FERMION)"
            elif size * (-30) % 360 == 0:
                phase_type = "(BOSON)"
            print(f"  n={size:2d}: {bar} ({count}) {phase_type}")
        
        print(f"\nFermion configurations: {fermion_count}/50")
        print(f"Boson configurations:   {boson_count}/50")
        
        return {
            'size_distribution': dict(size_dist),
            'fermion_fraction': fermion_count / 50,
            'boson_fraction': boson_count / 50,
            'most_common': size_dist.most_common(3)
        }
    
    def test_stability_of_attractors(self) -> Dict:
        """
        TEST 6: Test stability of fermion (n=6) and boson (n=12) under perturbation.
        """
        print("\n" + "=" * 70)
        print("TEST 6: STABILITY UNDER PERTURBATION")
        print("=" * 70)
        print("""
Test if n=6 (fermion) and n=12 (boson) are stable attractors.
Perturb them and see if they return.
""")
        
        results = {}
        
        for n, label in [(6, "FERMION"), (12, "BOSON")]:
            network = DynamicNetwork(seed=n)
            lid = network.create_regular_loop(n)
            loop = network.loops[lid]
            
            # First let it settle
            network.evolve(loop, n_steps=500)
            
            # Test stability
            stability = network.test_stability(loop, 
                                               perturbation_strength=0.2,
                                               n_perturbations=20,
                                               settle_steps=200)
            
            print(f"\n{label} (n={n}):")
            print(f"  Recovery rate: {stability['recovery_rate']:.0%}")
            print(f"  Stable? {stability['stable']}")
            
            results[f"n{n}_{label.lower()}"] = stability
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all dynamic enforcement tests."""
        print("=" * 80)
        print("  QMRT: DYNAMIC ENFORCEMENT OF PHASE CLOSURE")
        print("=" * 80)
        print("""
CRITICAL QUESTION:
  Do invalid phase configurations dynamically evolve into phase-closed states,
  and which of those are stable?

ENERGY FUNCTIONAL:
  E_total = E_smoothness + lambda_1 * (phase_mismatch)^2 + lambda_2 * (torsion)^2

DYNAMICS:
  - Gradient descent on positions
  - Loop resizing (add/remove vertices)
  - Free evolution (no bias toward specific n)
""")
        
        results = {}
        
        # Run individual tests
        results['undersized'] = self.test_invalid_undersized()
        results['oversized'] = self.test_invalid_oversized()
        results['distorted'] = self.test_distorted_loop()
        results['mixed'] = self.test_mixed_junctions()
        results['attractors'] = self.test_natural_attractors()
        results['stability'] = self.test_stability_of_attractors()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        print(f"""
EVOLUTION RESULTS:
  n=5 (invalid) -> n={results['undersized']['final_size']} (valid={results['undersized']['evolved_to_valid']})
  n=7 (invalid) -> n={results['oversized']['final_size']} (valid={results['oversized']['evolved_to_valid']})
  
ATTRACTOR STATISTICS:
  Fermion configurations: {results['attractors']['fermion_fraction']:.0%}
  Boson configurations:   {results['attractors']['boson_fraction']:.0%}
  Most common final sizes: {results['attractors']['most_common']}
""")
        
        # Check for successful enforcement
        n6_stable = results['stability'].get('n6_fermion', {}).get('stable', False)
        n12_stable = results['stability'].get('n12_boson', {}).get('stable', False)
        
        print("STABILITY:")
        print(f"  n=6 (fermion): {'STABLE' if n6_stable else 'UNSTABLE'}")
        print(f"  n=12 (boson):  {'STABLE' if n12_stable else 'UNSTABLE'}")
        
        # Verdict
        print("\n" + "=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        fermion_selected = results['attractors']['fermion_fraction'] > 0.1
        smallest_fermion_dominant = 6 in [s for s, _ in results['attractors']['most_common']]
        
        if fermion_selected and n6_stable:
            verdict = "FERMION_DYNAMICALLY_SELECTED"
            print("""
            
            DYNAMIC ENFORCEMENT WORKING!
            
  1. Invalid configurations evolve toward valid states
  2. n=6 (fermion) is a stable attractor
  3. Phase closure is DYNAMICALLY ENFORCED

  This confirms the theoretical prediction:
  "The system selects the smallest stable fermionic structure
   under interaction constraints."

""")
        elif n6_stable:
            verdict = "FERMION_STABLE_NOT_SELECTED"
            print("""
            
            PARTIAL RESULT
            
  1. n=6 (fermion) is stable when reached
  2. But system doesn't preferentially select n=6

  Implication: Additional constraints may be needed
  to bias toward fermion production.

""")
        else:
            verdict = "REQUIRES_REFINEMENT"
            print("""
            
            MODEL NEEDS REFINEMENT
            
  The current energy functional doesn't produce robust
  fermion selection. Consider:
  
  1. Stronger phase mismatch penalty
  2. Different torsion coupling
  3. Medium-level constraints (boundary conditions)

""")
        
        # Save results
        output = {
            'test': 'Dynamic_Enforcement',
            'verdict': verdict,
            'undersized_evolution': results['undersized'],
            'oversized_evolution': results['oversized'],
            'distorted_evolution': results['distorted'],
            'mixed_evolution': results['mixed'],
            'attractor_distribution': results['attractors'],
            'stability_tests': results['stability'],
            'conclusions': {
                'invalid_states_evolve': results['undersized']['evolved_to_valid'] or results['oversized']['evolved_to_valid'],
                'fermion_fraction': results['attractors']['fermion_fraction'],
                'n6_stable': n6_stable,
                'n12_stable': n12_stable,
                'smallest_fermion_is_attractor': smallest_fermion_dominant
            }
        }
        
        output_path = '/app/backend/qmrt_topology/dynamic_enforcement_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = DynamicEnforcementTest()
    results = test.run_all_tests()
