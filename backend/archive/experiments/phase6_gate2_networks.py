"""
Phase 6, Gate 2: Persistent Interaction Networks
=================================================

Question: Can clustered populations form persistent interaction networks?

"Persistent interaction network" means:
- Defects/clusters that repeatedly interact
- Stable relational structure over time
- Connected components rather than isolated blobs
- Network that survives across many timesteps

Tests:
1. Interaction graph construction - track proximity contacts over time
2. Network persistence - do edges survive across windows?
3. Component structure - connected network vs isolated clusters
4. Degree distribution - hubs vs uniform local clumps
5. Edge turnover - stable vs reshuffled contacts

Success criterion:
Evidence of persistent, connected relational structure that maintains
identity over time—not just transient clustering.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist, squareform
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import time


class NetworkTrackingSimulator:
    """
    Simulator with defect tracking for network analysis.
    """
    
    def __init__(
        self,
        size: int = 48,
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        gamma: float = 0.007,
    ):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.gamma = gamma
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.step_count = 0
        
        # Tracking
        self.defect_ids = {}  # position -> id
        self.next_id = 0
        self.id_positions = {}  # id -> position history
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        return np.where(r <= interior_r, self.coupling_center, self.coupling_edge)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        c_eff = 2.0
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff**2 * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff**2 * lap_i - self.gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple[int, int, int]]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        low_amp = amp < threshold
        labeled, n = label(low_amp)
        
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) < 5:
                continue
            coords = np.where(component)
            cx = int(np.mean(coords[0]))
            cy = int(np.mean(coords[1]))
            cz = int(np.mean(coords[2]))
            defects.append((cx, cy, cz))
        
        return defects
    
    def inject_vortex(self, cx: int, cy: int, charge: int = 1):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * charge * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)


def distance_periodic(p1: Tuple, p2: Tuple, size: int) -> float:
    """Compute distance with periodic boundary conditions."""
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def track_defects_with_ids(
    current_defects: List[Tuple],
    prev_defects: Dict[int, Tuple],
    next_id: int,
    size: int,
    match_radius: float = 5.0,
) -> Tuple[Dict[int, Tuple], int]:
    """
    Match current defects to previous ones by proximity.
    Returns: (id -> position dict, next available id)
    """
    current_ids = {}
    used_prev = set()
    
    for pos in current_defects:
        # Find closest previous defect
        best_id = None
        best_dist = float('inf')
        
        for prev_id, prev_pos in prev_defects.items():
            if prev_id in used_prev:
                continue
            d = distance_periodic(pos, prev_pos, size)
            if d < best_dist and d < match_radius:
                best_dist = d
                best_id = prev_id
        
        if best_id is not None:
            current_ids[best_id] = pos
            used_prev.add(best_id)
        else:
            # New defect
            current_ids[next_id] = pos
            next_id += 1
    
    return current_ids, next_id


class InteractionNetwork:
    """
    Track interaction network between defects over time.
    """
    
    def __init__(self, interaction_radius: float = 10.0):
        self.interaction_radius = interaction_radius
        self.edge_counts = defaultdict(int)  # (id1, id2) -> count
        self.node_history = defaultdict(list)  # id -> list of steps present
        self.edges_by_step = []  # list of edge sets per step
        
    def update(self, defect_ids: Dict[int, Tuple], step: int, size: int):
        """Record interactions at this step."""
        ids = list(defect_ids.keys())
        positions = [defect_ids[i] for i in ids]
        
        # Record node presence
        for i in ids:
            self.node_history[i].append(step)
        
        # Find interacting pairs
        current_edges = set()
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                d = distance_periodic(positions[i], positions[j], size)
                if d < self.interaction_radius:
                    edge = (min(ids[i], ids[j]), max(ids[i], ids[j]))
                    self.edge_counts[edge] += 1
                    current_edges.add(edge)
        
        self.edges_by_step.append(current_edges)
    
    def get_persistent_edges(self, min_count: int = 3) -> Set[Tuple[int, int]]:
        """Get edges that appeared at least min_count times."""
        return {e for e, c in self.edge_counts.items() if c >= min_count}
    
    def compute_edge_persistence(self, window: int = 5) -> List[float]:
        """
        Compute what fraction of edges persist across sliding windows.
        """
        if len(self.edges_by_step) < window:
            return []
        
        persistence = []
        for i in range(len(self.edges_by_step) - window):
            base_edges = self.edges_by_step[i]
            if not base_edges:
                continue
            
            # How many base edges still exist at end of window?
            end_edges = self.edges_by_step[i + window]
            survived = len(base_edges & end_edges)
            persistence.append(survived / len(base_edges) if base_edges else 0)
        
        return persistence
    
    def compute_degree_distribution(self, min_edge_count: int = 2) -> Dict[int, int]:
        """Compute degree distribution for persistent network."""
        persistent = self.get_persistent_edges(min_edge_count)
        degrees = defaultdict(int)
        
        for e in persistent:
            degrees[e[0]] += 1
            degrees[e[1]] += 1
        
        # Distribution
        dist = defaultdict(int)
        for d in degrees.values():
            dist[d] += 1
        
        return dict(dist)
    
    def find_connected_components(self, min_edge_count: int = 2) -> List[Set[int]]:
        """Find connected components in persistent network."""
        persistent = self.get_persistent_edges(min_edge_count)
        
        if not persistent:
            return []
        
        # Build adjacency
        adj = defaultdict(set)
        nodes = set()
        for e in persistent:
            adj[e[0]].add(e[1])
            adj[e[1]].add(e[0])
            nodes.add(e[0])
            nodes.add(e[1])
        
        # BFS to find components
        visited = set()
        components = []
        
        for start in nodes:
            if start in visited:
                continue
            
            component = set()
            queue = [start]
            
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                queue.extend(adj[node] - visited)
            
            components.append(component)
        
        return components


def run_gate_2_test():
    """
    Phase 6, Gate 2: Test for persistent interaction networks.
    """
    print("=" * 70)
    print("PHASE 6, GATE 2: PERSISTENT INTERACTION NETWORKS")
    print("=" * 70)
    print()
    print("Question: Can clustered populations form persistent relational structure?")
    print()
    
    sim = NetworkTrackingSimulator(size=48, coupling_center=0.7, coupling_edge=0.2)
    np.random.seed(42)
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size, sim.size)
    
    # Inject vortices
    center = sim.size // 2
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) + abs(j) <= 3:  # Diamond pattern
                sim.inject_vortex(center + i * 4, center + j * 4)
    
    print("Initialized with diamond pattern of vortices")
    print()
    
    # Let system equilibrate
    print("Equilibrating (500 steps)...")
    for _ in range(500):
        sim.step()
    
    # Track network
    print("Building interaction network (2000 steps)...")
    print()
    
    network = InteractionNetwork(interaction_radius=10.0)
    defect_ids = {}
    next_id = 0
    
    sample_interval = 10
    
    node_counts = []
    edge_counts = []
    
    for step in range(2000):
        sim.step()
        
        if step % sample_interval == 0:
            defects = sim.detect_defects()
            defect_ids, next_id = track_defects_with_ids(
                defects, defect_ids, next_id, sim.size, match_radius=5.0
            )
            
            network.update(defect_ids, step, sim.size)
            
            node_counts.append(len(defect_ids))
            edge_counts.append(len(network.edges_by_step[-1]))
            
            if step % 500 == 0:
                print(f"  Step {step}: {len(defect_ids)} defects, "
                      f"{len(network.edges_by_step[-1])} current edges")
    
    print()
    
    # Analysis
    print("-" * 70)
    print("TEST 1: NETWORK STATISTICS")
    print("-" * 70)
    print()
    
    total_unique_edges = len(network.edge_counts)
    persistent_3 = len(network.get_persistent_edges(3))
    persistent_5 = len(network.get_persistent_edges(5))
    persistent_10 = len(network.get_persistent_edges(10))
    
    print(f"Total unique edges observed: {total_unique_edges}")
    print(f"Edges appearing ≥3 times: {persistent_3} ({100*persistent_3/(total_unique_edges+1):.1f}%)")
    print(f"Edges appearing ≥5 times: {persistent_5} ({100*persistent_5/(total_unique_edges+1):.1f}%)")
    print(f"Edges appearing ≥10 times: {persistent_10} ({100*persistent_10/(total_unique_edges+1):.1f}%)")
    
    # Edge persistence across windows
    print()
    print("-" * 70)
    print("TEST 2: EDGE PERSISTENCE ACROSS TIME")
    print("-" * 70)
    print()
    
    persistence_5 = network.compute_edge_persistence(window=5)
    persistence_10 = network.compute_edge_persistence(window=10)
    persistence_20 = network.compute_edge_persistence(window=20)
    
    if persistence_5:
        print(f"Edge survival (5-step window): {100*np.mean(persistence_5):.1f}%")
    if persistence_10:
        print(f"Edge survival (10-step window): {100*np.mean(persistence_10):.1f}%")
    if persistence_20:
        print(f"Edge survival (20-step window): {100*np.mean(persistence_20):.1f}%")
    
    # Connected components
    print()
    print("-" * 70)
    print("TEST 3: NETWORK STRUCTURE")
    print("-" * 70)
    print()
    
    components = network.find_connected_components(min_edge_count=3)
    
    if components:
        sizes = [len(c) for c in components]
        print(f"Connected components (persistent edges ≥3): {len(components)}")
        print(f"  Largest component: {max(sizes)} nodes")
        print(f"  Component sizes: {sorted(sizes, reverse=True)[:5]}")
        
        # Is there a giant component?
        total_nodes = sum(sizes)
        largest_frac = max(sizes) / total_nodes if total_nodes > 0 else 0
        print(f"  Largest component fraction: {100*largest_frac:.1f}%")
    else:
        print("No persistent connected components found")
        largest_frac = 0
    
    # Degree distribution
    print()
    print("-" * 70)
    print("TEST 4: DEGREE DISTRIBUTION")
    print("-" * 70)
    print()
    
    degree_dist = network.compute_degree_distribution(min_edge_count=3)
    
    if degree_dist:
        print("Degree distribution (persistent edges ≥3):")
        for d in sorted(degree_dist.keys()):
            print(f"  Degree {d}: {degree_dist[d]} nodes")
        
        max_degree = max(degree_dist.keys())
        mean_degree = sum(d * c for d, c in degree_dist.items()) / sum(degree_dist.values())
        print(f"\n  Max degree: {max_degree}")
        print(f"  Mean degree: {mean_degree:.2f}")
        
        # Check for hubs
        high_degree_nodes = sum(c for d, c in degree_dist.items() if d >= 4)
        print(f"  High-degree nodes (≥4): {high_degree_nodes}")
    else:
        print("Insufficient persistent edges for degree analysis")
        max_degree = 0
        mean_degree = 0
    
    # Summary
    print()
    print("=" * 70)
    print("GATE 2 ASSESSMENT")
    print("=" * 70)
    print()
    
    evidence_for_networks = []
    evidence_against = []
    
    # Persistent edges
    if persistent_5 > 10:
        evidence_for_networks.append(f"Many persistent edges ({persistent_5} appearing ≥5 times)")
    elif persistent_3 > 5:
        evidence_for_networks.append(f"Some persistent edges ({persistent_3} appearing ≥3 times)")
    else:
        evidence_against.append("Few persistent edges")
    
    # Edge survival
    if persistence_10 and np.mean(persistence_10) > 0.3:
        evidence_for_networks.append(f"Good edge survival ({100*np.mean(persistence_10):.0f}% over 10 steps)")
    elif persistence_5 and np.mean(persistence_5) > 0.3:
        evidence_for_networks.append(f"Short-term edge survival ({100*np.mean(persistence_5):.0f}% over 5 steps)")
    else:
        evidence_against.append("Edges rapidly turn over")
    
    # Connected structure
    if components and largest_frac > 0.5:
        evidence_for_networks.append(f"Giant connected component ({100*largest_frac:.0f}% of nodes)")
    elif components and len(components) < 5:
        evidence_for_networks.append(f"Network is mostly connected ({len(components)} components)")
    else:
        evidence_against.append("Network is fragmented or absent")
    
    # Hubs
    if max_degree >= 4:
        evidence_for_networks.append(f"Hub nodes exist (max degree {max_degree})")
    
    print("EVIDENCE FOR PERSISTENT INTERACTION NETWORKS:")
    if evidence_for_networks:
        for e in evidence_for_networks:
            print(f"  + {e}")
    else:
        print("  (none)")
    
    print()
    print("EVIDENCE AGAINST:")
    if evidence_against:
        for e in evidence_against:
            print(f"  - {e}")
    else:
        print("  (none)")
    
    print()
    if len(evidence_for_networks) >= 3:
        print("GATE 2 RESULT: STRONG EVIDENCE FOR PERSISTENT NETWORKS")
        print("  Defect populations form stable relational structure")
    elif len(evidence_for_networks) >= 2:
        print("GATE 2 RESULT: MODERATE EVIDENCE FOR PERSISTENT NETWORKS")
        print("  Some network structure, but not fully stable")
    else:
        print("GATE 2 RESULT: NO CLEAR PERSISTENT NETWORK")
        print("  Interactions are transient, not forming stable structure")
    
    return {
        'total_edges': total_unique_edges,
        'persistent_edges_5': persistent_5,
        'edge_survival_10': np.mean(persistence_10) if persistence_10 else 0,
        'num_components': len(components),
        'largest_component_frac': largest_frac,
        'max_degree': max_degree,
        'evidence_for': evidence_for_networks,
        'evidence_against': evidence_against,
    }


if __name__ == "__main__":
    results = run_gate_2_test()
