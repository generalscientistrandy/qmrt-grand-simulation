"""
QMRT STAGE 1: LOCAL DYNAMICS SIMULATION ENGINE
===============================================

Goal: Validate that Y-junction rules produce persistent structures

This is the foundation for emergence:
- Time stepping engine
- Structure detection  
- Persistence tracking
- Event logging

We are testing:
- Stability
- Defect formation
- Loop persistence
- Sector conservation

This is where "particles" first appear.

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict
import random


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class NodeType(Enum):
    """Types of nodes in the Y-junction network."""
    JUNCTION = "junction"      # Standard 3-way Y-junction
    DEFECT = "defect"          # Topological defect (winding mismatch)
    BOUNDARY = "boundary"      # Edge of simulation domain


@dataclass
class Node:
    """A node (junction) in the Y-junction network."""
    id: int
    x: float
    y: float
    node_type: NodeType = NodeType.JUNCTION
    
    # Local state
    phase: float = 0.0                    # Local U(1) phase
    spinor: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0]))
    
    # Connectivity (edge IDs)
    edges: List[int] = field(default_factory=list)
    
    # Dynamics tracking
    birth_time: int = 0
    last_update: int = 0
    frustration_score: float = 0.0        # Mismatch with neighbors


@dataclass 
class Edge:
    """An edge (connection) between two nodes."""
    id: int
    node_a: int
    node_b: int
    
    # Transport phase accumulated along this edge
    transport_phase: float = 0.0
    
    # Edge state
    active: bool = True
    
    # Direction angle (for spinor transport)
    angle: float = 0.0


@dataclass
class Loop:
    """A detected loop structure (potential particle)."""
    id: int
    node_ids: List[int]
    edge_ids: List[int]
    
    # Topology
    size: int = 0                         # Number of nodes
    winding_number: int = 0               # Topological winding
    total_phase: float = 0.0              # Accumulated phase around loop
    holonomy: complex = 1.0               # exp(i * total_phase)
    
    # Classification
    loop_class: str = "unknown"           # "trivial", "frustrated", "hexagon", etc.
    is_fermionic: bool = False            # holonomy ≈ -1
    
    # Dynamics
    birth_time: int = 0
    last_seen: int = 0
    persistence: int = 0                  # How many timesteps it has survived
    
    # Stability
    stability_score: float = 0.0          # Higher = more stable


@dataclass
class Event:
    """An event in the simulation (birth, decay, collision, etc.)."""
    time: int
    event_type: str                       # "birth", "decay", "merge", "split"
    structure_id: int
    details: Dict = field(default_factory=dict)


# =============================================================================
# SIMULATION STATE
# =============================================================================

@dataclass
class SimulationState:
    """Complete state of the simulation at a given time."""
    time: int = 0
    
    # Network
    nodes: Dict[int, Node] = field(default_factory=dict)
    edges: Dict[int, Edge] = field(default_factory=dict)
    
    # Detected structures
    loops: Dict[int, Loop] = field(default_factory=dict)
    
    # Event log
    events: List[Event] = field(default_factory=list)
    
    # Counters
    next_node_id: int = 0
    next_edge_id: int = 0
    next_loop_id: int = 0
    
    # Observables history
    observables_history: List[Dict] = field(default_factory=list)


# =============================================================================
# Y-JUNCTION TRANSPORT RULES
# =============================================================================

class YJunctionTransport:
    """
    Implements the Y-junction spinor transport rules.
    
    This is the PHYSICS of the simulation:
    - 120° branch angles
    - Spinor overlap: ⟨e_out|e_in⟩ = cos(Δα/2) · exp(-iΔα/2)
    - Phase contribution: φ = -Δα/2 per turn
    """
    
    BRANCH_ANGLE = 120.0  # degrees
    BRANCH_ANGLE_RAD = np.radians(120.0)
    
    @staticmethod
    def spinor_from_angle(angle: float) -> np.ndarray:
        """Convert direction angle to spinor."""
        half_angle = angle / 2
        return np.array([np.cos(half_angle), np.sin(half_angle)])
    
    @staticmethod
    def spinor_overlap(angle_in: float, angle_out: float) -> Tuple[float, float]:
        """
        Compute spinor overlap for transport from angle_in to angle_out.
        
        Returns:
            (magnitude, phase) where overlap = magnitude * exp(i * phase)
        """
        delta = angle_out - angle_in
        half_delta = delta / 2
        
        magnitude = np.cos(half_delta)
        phase = -half_delta
        
        return magnitude, phase
    
    @staticmethod
    def phase_per_turn(turn_angle: float) -> float:
        """Phase contribution for a single turn."""
        return -turn_angle / 2
    
    @staticmethod
    def compute_frustration(node: Node, neighbors: List[Node], edges: List[Edge]) -> float:
        """
        Compute frustration score for a node.
        
        High frustration = geometry doesn't match Y-junction ideal.
        """
        if len(neighbors) != 3:
            return 1.0  # Non-junction nodes are maximally frustrated
        
        # Compute angles to neighbors
        angles = []
        for neighbor in neighbors:
            dx = neighbor.x - node.x
            dy = neighbor.y - node.y
            angle = np.arctan2(dy, dx)
            angles.append(angle)
        
        angles = sorted(angles)
        
        # Ideal Y-junction has 120° between each pair
        ideal_spacing = 2 * np.pi / 3
        
        frustration = 0.0
        for i in range(3):
            actual_spacing = angles[(i + 1) % 3] - angles[i]
            if actual_spacing < 0:
                actual_spacing += 2 * np.pi
            
            deviation = abs(actual_spacing - ideal_spacing)
            frustration += deviation
        
        return frustration / (3 * ideal_spacing)  # Normalize to [0, 1]


# =============================================================================
# STRUCTURE DETECTION
# =============================================================================

class StructureDetector:
    """
    Detects loops and other structures in the network.
    
    A particle-like object is:
    - Localized in space
    - Persists for N timesteps
    - Has identifiable topology (loop / defect / branch cluster)
    - Survives perturbation
    - Optionally carries holonomy or phase class
    """
    
    def __init__(self, state: SimulationState):
        self.state = state
    
    def find_all_loops(self, max_size: int = 12) -> List[List[int]]:
        """
        Find all simple loops in the network up to max_size.
        
        Returns list of loops, where each loop is a list of node IDs.
        """
        loops = []
        visited_loops: Set[Tuple[int, ...]] = set()
        
        # Build adjacency from edges
        adjacency = defaultdict(set)
        for edge in self.state.edges.values():
            if edge.active:
                adjacency[edge.node_a].add(edge.node_b)
                adjacency[edge.node_b].add(edge.node_a)
        
        # DFS to find cycles
        def dfs(start: int, current: int, path: List[int], depth: int):
            if depth > max_size:
                return
            
            for neighbor in adjacency[current]:
                if neighbor == start and len(path) >= 3:
                    # Found a loop
                    loop = tuple(sorted(path))
                    if loop not in visited_loops:
                        visited_loops.add(loop)
                        loops.append(list(path))
                elif neighbor not in path:
                    dfs(start, neighbor, path + [neighbor], depth + 1)
        
        # Start DFS from each node
        for node_id in self.state.nodes:
            dfs(node_id, node_id, [node_id], 1)
        
        return loops
    
    def classify_loop(self, node_ids: List[int]) -> Dict:
        """
        Classify a loop based on its topology.
        
        Returns dict with:
        - size: number of nodes
        - total_phase: accumulated phase around loop
        - holonomy: exp(i * total_phase)
        - loop_class: "trivial", "frustrated", "hexagon", etc.
        - is_fermionic: True if holonomy ≈ -1
        """
        size = len(node_ids)
        
        # Compute total phase around loop
        total_phase = 0.0
        
        for i in range(size):
            current = self.state.nodes[node_ids[i]]
            next_node = self.state.nodes[node_ids[(i + 1) % size]]
            prev_node = self.state.nodes[node_ids[(i - 1) % size]]
            
            # Angle from prev to current
            angle_in = np.arctan2(current.y - prev_node.y, current.x - prev_node.x)
            # Angle from current to next
            angle_out = np.arctan2(next_node.y - current.y, next_node.x - current.x)
            
            # Turn angle
            turn = angle_out - angle_in
            # Normalize to [-pi, pi]
            while turn > np.pi:
                turn -= 2 * np.pi
            while turn < -np.pi:
                turn += 2 * np.pi
            
            # Phase contribution (spinor transport rule)
            phase_contribution = YJunctionTransport.phase_per_turn(turn)
            total_phase += phase_contribution
        
        # Compute holonomy
        holonomy = np.exp(1j * total_phase)
        
        # Classify
        loop_class = "unknown"
        is_fermionic = False
        
        # Check if trivial (holonomy ≈ +1)
        if np.abs(holonomy - 1) < 0.1:
            loop_class = "trivial"
        # Check if fermionic (holonomy ≈ -1)
        elif np.abs(holonomy + 1) < 0.1:
            loop_class = "fermionic"
            is_fermionic = True
        # Check for hexagon
        elif size == 6:
            loop_class = "hexagon"
            if np.abs(holonomy + 1) < 0.2:
                is_fermionic = True
        # Check for triangle
        elif size == 3:
            loop_class = "triangle"
        else:
            loop_class = f"n{size}_loop"
        
        return {
            'size': size,
            'total_phase': total_phase,
            'holonomy': holonomy,
            'holonomy_real': float(holonomy.real),
            'holonomy_imag': float(holonomy.imag),
            'loop_class': loop_class,
            'is_fermionic': is_fermionic
        }
    
    def compute_stability_score(self, node_ids: List[int]) -> float:
        """
        Compute stability score for a loop.
        
        Higher score = more likely to persist.
        
        Factors:
        - Low frustration at nodes
        - Size matches commensurate values (3, 6, 9, ...)
        - Fermionic holonomy (protected by topology)
        """
        score = 0.0
        
        # Size factor (hexagons are most stable)
        size = len(node_ids)
        if size == 6:
            score += 1.0
        elif size % 3 == 0:
            score += 0.5
        
        # Frustration factor (low frustration = stable)
        total_frustration = 0.0
        for nid in node_ids:
            total_frustration += self.state.nodes[nid].frustration_score
        avg_frustration = total_frustration / size
        score += (1.0 - avg_frustration)
        
        # Fermionic factor (topologically protected)
        classification = self.classify_loop(node_ids)
        if classification['is_fermionic']:
            score += 1.0
        
        return score


# =============================================================================
# TIME EVOLUTION ENGINE
# =============================================================================

class TimeEvolution:
    """
    Time stepping engine for the Y-junction network.
    
    Each timestep:
    1. Apply local transport (Y-junction rules)
    2. Update phase/spinor states
    3. Resolve incompatibilities (collapse/decay)
    4. Update connections if needed
    5. Record observables
    """
    
    def __init__(self, state: SimulationState, params: Dict = None):
        self.state = state
        default_params = {
            'decay_threshold': 0.8,        # Frustration above this → decay
            'stability_threshold': 1.5,    # Stability below this → decay
            'perturbation_strength': 0.1,  # Random noise strength
            'persistence_threshold': 10,   # Timesteps to count as "persistent"
        }
        self.params = {**default_params, **(params or {})}
        self.detector = StructureDetector(state)
    
    def step(self) -> Dict:
        """
        Perform one timestep of evolution.
        
        Returns dict of observables for this step.
        """
        self.state.time += 1
        t = self.state.time
        
        # 1. Update phases via transport
        self._apply_transport()
        
        # 2. Compute frustration at each node
        self._compute_frustrations()
        
        # 3. Apply perturbations (thermal noise)
        self._apply_perturbations()
        
        # 4. Detect structures
        self._detect_structures()
        
        # 5. Resolve instabilities (decay high-frustration regions)
        self._resolve_instabilities()
        
        # 6. Record observables
        observables = self._record_observables()
        self.state.observables_history.append(observables)
        
        return observables
    
    def _apply_transport(self):
        """Apply Y-junction transport rules to update phases."""
        for node in self.state.nodes.values():
            if node.node_type != NodeType.JUNCTION:
                continue
            
            # Get neighboring nodes
            neighbor_ids = []
            for eid in node.edges:
                edge = self.state.edges.get(eid)
                if edge and edge.active:
                    other = edge.node_b if edge.node_a == node.id else edge.node_a
                    neighbor_ids.append(other)
            
            if len(neighbor_ids) < 2:
                continue
            
            # Compute phase update from transport
            phase_update = 0.0
            for nid in neighbor_ids:
                neighbor = self.state.nodes.get(nid)
                if neighbor:
                    # Direction to neighbor
                    dx = neighbor.x - node.x
                    dy = neighbor.y - node.y
                    angle = np.arctan2(dy, dx)
                    
                    # Transport contribution
                    phase_diff = neighbor.phase - node.phase
                    _, transport_phase = YJunctionTransport.spinor_overlap(
                        node.phase, angle
                    )
                    phase_update += 0.1 * (transport_phase + phase_diff)
            
            node.phase += phase_update
            node.last_update = self.state.time
    
    def _compute_frustrations(self):
        """Compute frustration score at each node."""
        for node in self.state.nodes.values():
            if node.node_type != NodeType.JUNCTION:
                continue
            
            neighbors = []
            for eid in node.edges:
                edge = self.state.edges.get(eid)
                if edge and edge.active:
                    other_id = edge.node_b if edge.node_a == node.id else edge.node_a
                    other = self.state.nodes.get(other_id)
                    if other:
                        neighbors.append(other)
            
            edges = [self.state.edges[eid] for eid in node.edges 
                     if eid in self.state.edges]
            
            node.frustration_score = YJunctionTransport.compute_frustration(
                node, neighbors, edges
            )
    
    def _apply_perturbations(self):
        """Apply random perturbations (thermal noise)."""
        strength = self.params['perturbation_strength']
        
        for node in self.state.nodes.values():
            if node.node_type == NodeType.JUNCTION:
                node.phase += np.random.normal(0, strength)
    
    def _detect_structures(self):
        """Detect and track loop structures."""
        current_loops = self.detector.find_all_loops(max_size=12)
        
        # Track which loops are still present
        seen_loop_ids = set()
        
        for node_ids in current_loops:
            # Check if this loop already exists
            loop_key = tuple(sorted(node_ids))
            
            existing = None
            for loop in self.state.loops.values():
                if tuple(sorted(loop.node_ids)) == loop_key:
                    existing = loop
                    break
            
            if existing:
                # Update existing loop
                existing.last_seen = self.state.time
                existing.persistence = self.state.time - existing.birth_time
                seen_loop_ids.add(existing.id)
            else:
                # Create new loop
                classification = self.detector.classify_loop(node_ids)
                stability = self.detector.compute_stability_score(node_ids)
                
                new_loop = Loop(
                    id=self.state.next_loop_id,
                    node_ids=node_ids,
                    edge_ids=[],  # TODO: compute edge IDs
                    size=classification['size'],
                    total_phase=classification['total_phase'],
                    holonomy=classification['holonomy'],
                    loop_class=classification['loop_class'],
                    is_fermionic=classification['is_fermionic'],
                    birth_time=self.state.time,
                    last_seen=self.state.time,
                    persistence=0,
                    stability_score=stability
                )
                
                self.state.loops[new_loop.id] = new_loop
                self.state.next_loop_id += 1
                seen_loop_ids.add(new_loop.id)
                
                # Log birth event
                self.state.events.append(Event(
                    time=self.state.time,
                    event_type="birth",
                    structure_id=new_loop.id,
                    details={
                        'size': new_loop.size,
                        'loop_class': new_loop.loop_class,
                        'is_fermionic': new_loop.is_fermionic,
                        'stability': stability
                    }
                ))
        
        # Check for decayed loops
        for loop_id, loop in list(self.state.loops.items()):
            if loop_id not in seen_loop_ids:
                if self.state.time - loop.last_seen > 1:
                    # Loop has decayed
                    self.state.events.append(Event(
                        time=self.state.time,
                        event_type="decay",
                        structure_id=loop_id,
                        details={
                            'lifetime': loop.persistence,
                            'loop_class': loop.loop_class
                        }
                    ))
                    del self.state.loops[loop_id]
    
    def _resolve_instabilities(self):
        """Remove or modify highly frustrated regions."""
        decay_threshold = self.params['decay_threshold']
        
        # For now, just mark highly frustrated nodes
        for node in self.state.nodes.values():
            if node.frustration_score > decay_threshold:
                node.node_type = NodeType.DEFECT
    
    def _record_observables(self) -> Dict:
        """Record observables for this timestep."""
        # Count structures by type
        loop_counts = defaultdict(int)
        fermionic_count = 0
        total_persistence = 0
        
        for loop in self.state.loops.values():
            loop_counts[loop.loop_class] += 1
            if loop.is_fermionic:
                fermionic_count += 1
            total_persistence += loop.persistence
        
        # Count persistent structures (survived > threshold timesteps)
        persistent_count = sum(
            1 for loop in self.state.loops.values()
            if loop.persistence >= self.params['persistence_threshold']
        )
        
        # Average frustration
        frustrations = [n.frustration_score for n in self.state.nodes.values()
                        if n.node_type == NodeType.JUNCTION]
        avg_frustration = np.mean(frustrations) if frustrations else 0.0
        
        # Defect count
        defect_count = sum(
            1 for n in self.state.nodes.values()
            if n.node_type == NodeType.DEFECT
        )
        
        return {
            'time': self.state.time,
            'total_loops': len(self.state.loops),
            'loop_counts': dict(loop_counts),
            'fermionic_count': fermionic_count,
            'persistent_count': persistent_count,
            'avg_persistence': total_persistence / max(1, len(self.state.loops)),
            'avg_frustration': float(avg_frustration),
            'defect_count': defect_count,
            'total_nodes': len(self.state.nodes),
            'total_events': len(self.state.events)
        }


# =============================================================================
# NETWORK INITIALIZATION
# =============================================================================

class NetworkInitializer:
    """Initialize Y-junction networks for simulation."""
    
    @staticmethod
    def create_hexagonal_lattice(rows: int, cols: int, spacing: float = 1.0) -> SimulationState:
        """
        Create a hexagonal lattice of Y-junctions.
        
        This is the natural structure for Y-junction networks.
        Each node connects to ~3 neighbors in a honeycomb pattern.
        """
        state = SimulationState()
        
        # Honeycomb lattice spacing
        dx = spacing * 1.5
        dy = spacing * np.sqrt(3) / 2
        
        # Create nodes in hexagonal pattern
        for row in range(rows):
            for col in range(cols):
                x = col * dx
                y = row * dy
                # Offset odd rows
                if row % 2 == 1:
                    x += dx / 2
                
                node = Node(
                    id=state.next_node_id,
                    x=x,
                    y=y,
                    node_type=NodeType.JUNCTION,
                    phase=np.random.uniform(0, 2 * np.pi),
                    birth_time=0
                )
                state.nodes[node.id] = node
                state.next_node_id += 1
        
        # Create edges (connect nodes within connection radius)
        # For honeycomb, nearest neighbors are at distance ~spacing
        connection_radius = spacing * 1.2
        
        node_list = list(state.nodes.values())
        for i, node_a in enumerate(node_list):
            for node_b in node_list[i+1:]:
                dist = np.sqrt((node_a.x - node_b.x)**2 + (node_a.y - node_b.y)**2)
                
                if dist < connection_radius and dist > 0.1:
                    edge = Edge(
                        id=state.next_edge_id,
                        node_a=node_a.id,
                        node_b=node_b.id,
                        angle=np.arctan2(node_b.y - node_a.y, node_b.x - node_a.x)
                    )
                    state.edges[edge.id] = edge
                    node_a.edges.append(edge.id)
                    node_b.edges.append(edge.id)
                    state.next_edge_id += 1
        
        return state
    
    @staticmethod
    def create_random_network(num_nodes: int, density: float = 0.3) -> SimulationState:
        """Create a random Y-junction network."""
        state = SimulationState()
        
        # Random node positions
        for i in range(num_nodes):
            node = Node(
                id=i,
                x=np.random.uniform(0, 10),
                y=np.random.uniform(0, 10),
                node_type=NodeType.JUNCTION,
                phase=np.random.uniform(0, 2 * np.pi),
                birth_time=0
            )
            state.nodes[node.id] = node
            state.next_node_id = num_nodes
        
        # Connect nodes based on distance
        node_list = list(state.nodes.values())
        for i, node_a in enumerate(node_list):
            for node_b in node_list[i+1:]:
                dist = np.sqrt((node_a.x - node_b.x)**2 + (node_a.y - node_b.y)**2)
                
                # Connect with probability based on distance
                if dist < 2.0 and np.random.random() < density:
                    edge = Edge(
                        id=state.next_edge_id,
                        node_a=node_a.id,
                        node_b=node_b.id,
                        angle=np.arctan2(node_b.y - node_a.y, node_b.x - node_a.x)
                    )
                    state.edges[edge.id] = edge
                    node_a.edges.append(edge.id)
                    node_b.edges.append(edge.id)
                    state.next_edge_id += 1
        
        return state


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

class EmergenceExperiment:
    """
    Run emergence experiments to test for stable structure formation.
    
    "Free Emergence Stability Sweep":
    - Run 20-50 simulations
    - Same rules, different random seeds
    - Measure: persistent structures, lifetime, dominant types
    """
    
    def __init__(self, params: Dict = None):
        self.params = params or {
            'num_runs': 20,
            'timesteps_per_run': 100,
            'grid_rows': 8,
            'grid_cols': 8,
            'persistence_threshold': 10
        }
        self.results = []
    
    def run_single(self, seed: int) -> Dict:
        """Run a single simulation with given seed."""
        np.random.seed(seed)
        random.seed(seed)
        
        # Initialize network
        state = NetworkInitializer.create_hexagonal_lattice(
            self.params['grid_rows'],
            self.params['grid_cols']
        )
        
        # Create evolution engine
        evolution = TimeEvolution(state, {
            'persistence_threshold': self.params['persistence_threshold']
        })
        
        # Run simulation
        for _ in range(self.params['timesteps_per_run']):
            evolution.step()
        
        # Collect results
        final_obs = state.observables_history[-1] if state.observables_history else {}
        
        # Analyze events
        births = [e for e in state.events if e.event_type == "birth"]
        decays = [e for e in state.events if e.event_type == "decay"]
        
        # Lifetimes of decayed structures
        lifetimes = [e.details.get('lifetime', 0) for e in decays]
        
        # Persistent structures (still alive at end)
        persistent = [
            loop for loop in state.loops.values()
            if loop.persistence >= self.params['persistence_threshold']
        ]
        
        # Dominant loop types
        loop_type_counts = defaultdict(int)
        for loop in state.loops.values():
            loop_type_counts[loop.loop_class] += 1
        
        return {
            'seed': seed,
            'total_births': len(births),
            'total_decays': len(decays),
            'final_loop_count': len(state.loops),
            'persistent_count': len(persistent),
            'fermionic_persistent': sum(1 for l in persistent if l.is_fermionic),
            'avg_lifetime': np.mean(lifetimes) if lifetimes else 0,
            'max_lifetime': max(lifetimes) if lifetimes else 0,
            'loop_type_counts': dict(loop_type_counts),
            'final_observables': final_obs,
            'persistent_types': [l.loop_class for l in persistent]
        }
    
    def run_sweep(self) -> Dict:
        """Run full emergence stability sweep."""
        print("=" * 60)
        print("QMRT STAGE 1: FREE EMERGENCE STABILITY SWEEP")
        print("=" * 60)
        print(f"Running {self.params['num_runs']} simulations...")
        print(f"Timesteps per run: {self.params['timesteps_per_run']}")
        print(f"Grid size: {self.params['grid_rows']}x{self.params['grid_cols']}")
        print()
        
        self.results = []
        
        for i in range(self.params['num_runs']):
            seed = 1000 + i
            result = self.run_single(seed)
            self.results.append(result)
            
            if (i + 1) % 5 == 0:
                print(f"  Completed {i + 1}/{self.params['num_runs']} runs...")
        
        # Aggregate analysis
        analysis = self._analyze_results()
        
        return analysis
    
    def _analyze_results(self) -> Dict:
        """Analyze results across all runs."""
        print("\n" + "=" * 60)
        print("RESULTS ANALYSIS")
        print("=" * 60)
        
        # Aggregate statistics
        persistent_counts = [r['persistent_count'] for r in self.results]
        avg_lifetimes = [r['avg_lifetime'] for r in self.results]
        fermionic_counts = [r['fermionic_persistent'] for r in self.results]
        
        # Loop type frequency across all runs
        all_types = defaultdict(int)
        persistent_types = defaultdict(int)
        for r in self.results:
            for ltype, count in r['loop_type_counts'].items():
                all_types[ltype] += count
            for ptype in r['persistent_types']:
                persistent_types[ptype] += 1
        
        analysis = {
            'num_runs': len(self.results),
            'avg_persistent_structures': np.mean(persistent_counts),
            'std_persistent_structures': np.std(persistent_counts),
            'max_persistent_structures': max(persistent_counts),
            'min_persistent_structures': min(persistent_counts),
            'avg_lifetime': np.mean(avg_lifetimes),
            'avg_fermionic_persistent': np.mean(fermionic_counts),
            'total_loop_types': dict(all_types),
            'persistent_loop_types': dict(persistent_types),
            'runs_with_persistent': sum(1 for p in persistent_counts if p > 0),
            'runs_with_fermionic': sum(1 for f in fermionic_counts if f > 0)
        }
        
        # Print summary
        print(f"\nPERSISTENT STRUCTURES:")
        print(f"  Average per run: {analysis['avg_persistent_structures']:.2f} ± {analysis['std_persistent_structures']:.2f}")
        print(f"  Max in single run: {analysis['max_persistent_structures']}")
        print(f"  Runs with persistent: {analysis['runs_with_persistent']}/{len(self.results)}")
        
        print(f"\nFERMIONIC STRUCTURES:")
        print(f"  Average fermionic persistent: {analysis['avg_fermionic_persistent']:.2f}")
        print(f"  Runs with fermionic: {analysis['runs_with_fermionic']}/{len(self.results)}")
        
        print(f"\nLOOP TYPE DISTRIBUTION (all):")
        for ltype, count in sorted(all_types.items(), key=lambda x: -x[1]):
            print(f"  {ltype}: {count}")
        
        print(f"\nPERSISTENT LOOP TYPES:")
        for ltype, count in sorted(persistent_types.items(), key=lambda x: -x[1]):
            print(f"  {ltype}: {count}")
        
        print(f"\nAVERAGE LIFETIME: {analysis['avg_lifetime']:.2f} timesteps")
        
        # Determine emergence quality
        print("\n" + "=" * 60)
        print("EMERGENCE ASSESSMENT")
        print("=" * 60)
        
        if analysis['avg_persistent_structures'] > 1:
            print("✅ STRONG SIGNAL: Multiple persistent structures emerge")
        elif analysis['avg_persistent_structures'] > 0.5:
            print("🟡 MODERATE SIGNAL: Some persistent structures emerge")
        else:
            print("🔴 WEAK SIGNAL: Few persistent structures")
        
        if analysis['runs_with_fermionic'] > len(self.results) * 0.3:
            print("✅ FERMIONIC: Fermionic loops appear frequently")
        else:
            print("🟡 FERMIONIC: Fermionic loops are rare")
        
        if 'hexagon' in persistent_types and persistent_types['hexagon'] > 0:
            print("✅ HEXAGON DOMINANCE: Hexagons persist as predicted")
        
        return analysis


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the Stage 1 emergence experiment."""
    print("\n" * 2)
    print("=" * 70)
    print("  QMRT STAGE 1: LOCAL DYNAMICS SIMULATION")
    print("  Testing for Spontaneous Structure Emergence")
    print("=" * 70)
    print()
    
    # Run emergence sweep
    experiment = EmergenceExperiment({
        'num_runs': 20,
        'timesteps_per_run': 50,
        'grid_rows': 6,
        'grid_cols': 6,
        'persistence_threshold': 5
    })
    
    analysis = experiment.run_sweep()
    
    # Save results
    output = {
        'experiment_params': experiment.params,
        'analysis': {k: v for k, v in analysis.items() 
                     if not isinstance(v, np.ndarray)},
        'individual_runs': experiment.results
    }
    
    output_path = '/app/backend/qmrt_topology/stage1_emergence_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_path}")
    print("\n" + "=" * 70)
    
    return analysis


if __name__ == "__main__":
    main()
