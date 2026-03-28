"""
QMRT: DEGREE SELECTION MECHANISM TEST
=====================================

PREVIOUS RESULT:
  Flux conservation FAILED to select degree = 3.
  Reason: Network topology was FIXED. Only flux values changed.

NEW APPROACH:
  Allow RECONNECTION DYNAMICS - nodes can split/merge edges.
  
  Test two mechanisms:
  1. ENERGY PENALTY: E_penalty = λ × (degree - 3)²
  2. TOPOLOGICAL CHARGE: Degree must sum to conserved total

KEY QUESTION:
  Can we find dynamics where degree = 3 is an ATTRACTOR?

PHYSICS ANALOGY:
  - Soap films: Plateau's laws (3 films meet at 120°)
  - Crystal defects: Specific coordination numbers preferred
  - Network flow: Optimal branching (Murray's law: arteries branch ~3)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional
import json
from collections import defaultdict


@dataclass
class Node:
    """A node in the reconnectable network."""
    id: int
    position: np.ndarray


@dataclass
class Edge:
    """An edge between nodes."""
    node1_id: int
    node2_id: int
    tension: float = 1.0
    
    def other_node(self, node_id: int) -> int:
        if self.node1_id == node_id:
            return self.node2_id
        return self.node1_id


class ReconnectableNetwork:
    """
    Network with reconnection dynamics.
    
    Edges can:
      - Split high-degree nodes (>3 → 3 + 3)
      - Merge at low-degree nodes (1 + 1 → merged)
      - Reconnect to reduce energy
    """
    
    def __init__(self, domain_size: float = 100.0, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.domain_size = domain_size
        self.nodes: Dict[int, Node] = {}
        self.edges: List[Edge] = []
        self.next_id = 0
        
        self.time = 0.0
        self.degree_history: List[Dict] = []
    
    def add_node(self, position: np.ndarray) -> int:
        node_id = self.next_id
        self.nodes[node_id] = Node(id=node_id, position=np.array(position))
        self.next_id += 1
        return node_id
    
    def add_edge(self, n1: int, n2: int, tension: float = 1.0):
        if n1 != n2 and not self._edge_exists(n1, n2):
            self.edges.append(Edge(n1, n2, tension))
    
    def remove_edge(self, edge: Edge):
        if edge in self.edges:
            self.edges.remove(edge)
    
    def _edge_exists(self, n1: int, n2: int) -> bool:
        for e in self.edges:
            if (e.node1_id == n1 and e.node2_id == n2) or \
               (e.node1_id == n2 and e.node2_id == n1):
                return True
        return False
    
    def get_edge(self, n1: int, n2: int) -> Optional[Edge]:
        for e in self.edges:
            if (e.node1_id == n1 and e.node2_id == n2) or \
               (e.node1_id == n2 and e.node2_id == n1):
                return e
        return None
    
    def get_node_degree(self, node_id: int) -> int:
        return sum(1 for e in self.edges 
                   if e.node1_id == node_id or e.node2_id == node_id)
    
    def get_neighbors(self, node_id: int) -> List[Tuple[int, Edge]]:
        neighbors = []
        for e in self.edges:
            if e.node1_id == node_id:
                neighbors.append((e.node2_id, e))
            elif e.node2_id == node_id:
                neighbors.append((e.node1_id, e))
        return neighbors
    
    def _distance(self, n1: int, n2: int) -> float:
        p1 = self.nodes[n1].position
        p2 = self.nodes[n2].position
        return np.linalg.norm(p2 - p1)
    
    def create_random_network(self, n_nodes: int = 20, connectivity: float = 0.25):
        """Create random network with mixed degrees."""
        for _ in range(n_nodes):
            pos = np.random.uniform(10, self.domain_size - 10, 2)
            self.add_node(pos)
        
        node_ids = list(self.nodes.keys())
        
        # Create random edges
        for i, n1 in enumerate(node_ids):
            for n2 in node_ids[i+1:]:
                if np.random.random() < connectivity:
                    self.add_edge(n1, n2)
    
    def compute_energy(self, degree_penalty_weight: float = 10.0) -> float:
        """
        Total energy with degree penalty.
        
        E = Σ T_i L_i + λ × Σ (degree_i - 3)²
        """
        energy = 0.0
        
        # Edge energy
        for e in self.edges:
            length = self._distance(e.node1_id, e.node2_id)
            energy += e.tension * length
        
        # Degree penalty (target = 3)
        for node_id in self.nodes:
            degree = self.get_node_degree(node_id)
            energy += degree_penalty_weight * (degree - 3)**2
        
        return energy
    
    def compute_node_degree_energy(self, node_id: int, degree_penalty_weight: float) -> float:
        """Energy contribution from one node's degree."""
        degree = self.get_node_degree(node_id)
        return degree_penalty_weight * (degree - 3)**2
    
    def try_node_split(self, node_id: int, degree_penalty_weight: float) -> bool:
        """
        Try to split a high-degree node into two degree-3 nodes.
        
        If degree > 3, split into:
          - Original node with 3 edges
          - New node with remaining edges
        """
        degree = self.get_node_degree(node_id)
        
        if degree <= 3:
            return False  # No need to split
        
        neighbors = self.get_neighbors(node_id)
        
        # Split: keep 2 edges on original, move rest to new node
        # (2 edges to original + 1 edge to new node = 3 edges each)
        
        if len(neighbors) < 4:
            return False  # Can't split effectively
        
        # Calculate energy before split
        energy_before = self.compute_energy(degree_penalty_weight)
        
        # Create new node near original
        original_pos = self.nodes[node_id].position
        offset = np.random.normal(0, 5, 2)
        new_pos = original_pos + offset
        new_pos = np.clip(new_pos, 5, self.domain_size - 5)
        new_node_id = self.add_node(new_pos)
        
        # Keep first 2 neighbors on original
        # Move rest to new node
        edges_to_move = neighbors[2:]  # All except first 2
        
        for neighbor_id, edge in edges_to_move:
            # Remove old edge
            self.remove_edge(edge)
            # Add new edge from new_node to neighbor
            self.add_edge(new_node_id, neighbor_id, edge.tension)
        
        # Add edge between original and new node
        self.add_edge(node_id, new_node_id)
        
        # Calculate energy after split
        energy_after = self.compute_energy(degree_penalty_weight)
        
        # Accept if energy decreased, or with some probability if increased
        if energy_after < energy_before:
            return True  # Accept split
        else:
            # Reject: undo split
            # Remove edge to new node
            edge_to_new = self.get_edge(node_id, new_node_id)
            if edge_to_new:
                self.remove_edge(edge_to_new)
            
            # Move edges back
            for neighbor_id, old_edge in edges_to_move:
                # Remove edge from new node
                edge_from_new = self.get_edge(new_node_id, neighbor_id)
                if edge_from_new:
                    self.remove_edge(edge_from_new)
                # Restore original edge
                self.add_edge(node_id, neighbor_id, old_edge.tension)
            
            # Remove new node
            del self.nodes[new_node_id]
            
            return False
    
    def try_node_merge(self, node_id: int, degree_penalty_weight: float) -> bool:
        """
        Try to merge a low-degree node with a neighbor.
        
        If degree < 3 and neighbor has degree < 3, merge them.
        """
        degree = self.get_node_degree(node_id)
        
        if degree >= 3 or degree == 0:
            return False  # Don't merge degree-3 or isolated nodes
        
        neighbors = self.get_neighbors(node_id)
        
        # Find a neighbor with low degree
        for neighbor_id, connecting_edge in neighbors:
            neighbor_degree = self.get_node_degree(neighbor_id)
            
            if neighbor_degree < 3:
                # Try to merge: redirect node's other edges to neighbor
                energy_before = self.compute_energy(degree_penalty_weight)
                
                # Get all edges of node_id except the connecting edge
                other_neighbors = [(n, e) for n, e in neighbors if n != neighbor_id]
                
                # Redirect edges
                for other_n, edge in other_neighbors:
                    self.remove_edge(edge)
                    if not self._edge_exists(neighbor_id, other_n):
                        self.add_edge(neighbor_id, other_n, edge.tension)
                
                # Remove connecting edge and node
                self.remove_edge(connecting_edge)
                
                # Check if node still has edges
                if self.get_node_degree(node_id) == 0:
                    del self.nodes[node_id]
                
                energy_after = self.compute_energy(degree_penalty_weight)
                
                if energy_after < energy_before:
                    return True
                # else: we already made the change, keep it (could add reversal logic)
        
        return False
    
    def try_edge_reconnect(self, degree_penalty_weight: float) -> bool:
        """
        Try to reconnect an edge to reduce degree penalty.
        
        Find an edge where moving one endpoint reduces total degree penalty.
        """
        if len(self.edges) < 2 or len(self.nodes) < 3:
            return False
        
        # Pick random edge
        edge = np.random.choice(self.edges)
        
        # Pick endpoint to potentially move
        if np.random.random() < 0.5:
            moving_endpoint = edge.node1_id
            fixed_endpoint = edge.node2_id
        else:
            moving_endpoint = edge.node2_id
            fixed_endpoint = edge.node1_id
        
        # Find candidate new endpoint (different from current)
        candidates = [n for n in self.nodes 
                      if n != moving_endpoint 
                      and n != fixed_endpoint
                      and not self._edge_exists(fixed_endpoint, n)]
        
        if not candidates:
            return False
        
        # Pick candidate that would most reduce degree penalty
        best_candidate = None
        best_improvement = 0
        
        current_penalty = (self.get_node_degree(moving_endpoint) - 3)**2 + \
                         (self.get_node_degree(fixed_endpoint) - 3)**2
        
        for cand in candidates:
            # New degrees if we reconnect
            new_moving_deg = self.get_node_degree(moving_endpoint) - 1
            new_cand_deg = self.get_node_degree(cand) + 1
            
            new_penalty = (new_moving_deg - 3)**2 + (new_cand_deg - 3)**2
            
            improvement = current_penalty - new_penalty
            
            if improvement > best_improvement:
                best_improvement = improvement
                best_candidate = cand
        
        if best_candidate is not None and best_improvement > 0:
            # Reconnect edge
            self.remove_edge(edge)
            self.add_edge(fixed_endpoint, best_candidate, edge.tension)
            return True
        
        return False
    
    def evolve_step(self, dt: float = 0.1, degree_penalty_weight: float = 10.0,
                    reconnect_prob: float = 0.1, split_prob: float = 0.05):
        """
        Evolve network with reconnection dynamics.
        """
        # 1. Node position dynamics (force balance)
        for node_id, node in self.nodes.items():
            force = np.zeros(2)
            
            for neighbor_id, edge in self.get_neighbors(node_id):
                neighbor_pos = self.nodes[neighbor_id].position
                direction = neighbor_pos - node.position
                dist = np.linalg.norm(direction) + 1e-10
                unit_dir = direction / dist
                force += edge.tension * unit_dir
            
            # Damped motion
            damping = 10.0
            displacement = force * dt / damping
            max_disp = 1.0
            if np.linalg.norm(displacement) > max_disp:
                displacement *= max_disp / np.linalg.norm(displacement)
            
            node.position += displacement
            node.position = np.clip(node.position, 5, self.domain_size - 5)
        
        # 2. Reconnection dynamics
        node_ids = list(self.nodes.keys())
        
        # Try splits on high-degree nodes
        for node_id in node_ids:
            if node_id not in self.nodes:
                continue  # Node may have been removed
            if np.random.random() < split_prob:
                if self.get_node_degree(node_id) > 3:
                    self.try_node_split(node_id, degree_penalty_weight)
        
        # Try edge reconnection
        if np.random.random() < reconnect_prob:
            self.try_edge_reconnect(degree_penalty_weight)
        
        # 3. Tension equilibration
        if self.edges:
            avg_tension = np.mean([e.tension for e in self.edges])
            for e in self.edges:
                e.tension += 0.1 * (avg_tension - e.tension) * dt
                e.tension = max(0.1, e.tension)
        
        self.time += dt
    
    def record_state(self):
        """Record current degree distribution."""
        degrees = [self.get_node_degree(n) for n in self.nodes]
        degree_counts = {}
        for d in degrees:
            degree_counts[d] = degree_counts.get(d, 0) + 1
        
        n_degree_3 = sum(1 for d in degrees if d == 3)
        frac_3 = n_degree_3 / len(degrees) if degrees else 0
        
        self.degree_history.append({
            'time': self.time,
            'distribution': dict(degree_counts),
            'frac_degree_3': float(frac_3),
            'n_nodes': len(self.nodes),
            'n_edges': len(self.edges)
        })
    
    def evolve_and_record(self, total_time: float, dt: float = 0.1,
                          record_interval: int = 50,
                          degree_penalty_weight: float = 10.0):
        """Evolve and record periodically."""
        n_steps = int(total_time / dt)
        
        self.record_state()  # Initial state
        
        for step in range(n_steps):
            self.evolve_step(dt, degree_penalty_weight)
            
            if (step + 1) % record_interval == 0:
                self.record_state()
    
    def get_statistics(self) -> Dict:
        """Get final statistics."""
        degrees = [self.get_node_degree(n) for n in self.nodes]
        degree_counts = {}
        for d in degrees:
            degree_counts[d] = degree_counts.get(d, 0) + 1
        
        n_degree_3 = sum(1 for d in degrees if d == 3)
        frac_3 = n_degree_3 / len(degrees) if degrees else 0
        
        return {
            'n_nodes': len(self.nodes),
            'n_edges': len(self.edges),
            'degree_distribution': degree_counts,
            'frac_degree_3': float(frac_3),
            'mean_degree': float(np.mean(degrees)) if degrees else 0
        }


def run_degree_selection_test():
    """
    Test whether degree penalty with reconnection forces degree → 3.
    """
    print("=" * 80)
    print("  DEGREE SELECTION TEST (with Reconnection Dynamics)")
    print("=" * 80)
    print("""
APPROACH:
  - Allow network topology to change (split/reconnect)
  - Add energy penalty: E_penalty = λ × (degree - 3)²
  
QUESTION:
  Does this penalty FORCE degree → 3 as an ATTRACTOR?

SUCCESS CRITERIA:
  - 70%+ nodes converge to degree 3
  - Stable over time
""")
    
    results = []
    
    print("\n" + "=" * 70)
    print("TRIALS")
    print("=" * 70)
    
    for trial in range(5):
        print(f"\n--- Trial {trial + 1}/5 ---")
        
        network = ReconnectableNetwork(seed=trial * 17)
        network.create_random_network(n_nodes=25, connectivity=0.22)
        
        initial_stats = network.get_statistics()
        print(f"Initial: {initial_stats['degree_distribution']}, "
              f"deg-3 = {initial_stats['frac_degree_3']:.1%}")
        
        # Evolve with degree penalty
        network.evolve_and_record(
            total_time=200.0, dt=0.1, record_interval=100,
            degree_penalty_weight=15.0
        )
        
        final_stats = network.get_statistics()
        print(f"Final:   {final_stats['degree_distribution']}, "
              f"deg-3 = {final_stats['frac_degree_3']:.1%}")
        
        results.append({
            'trial': trial,
            'initial': initial_stats,
            'final': final_stats,
            'history': network.degree_history
        })
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    initial_fracs = [r['initial']['frac_degree_3'] for r in results]
    final_fracs = [r['final']['frac_degree_3'] for r in results]
    
    print(f"""
DEGREE-3 FRACTION:
                    Initial         Final
Mean:               {np.mean(initial_fracs):>10.1%}     {np.mean(final_fracs):>10.1%}
Std:                {np.std(initial_fracs):>10.1%}     {np.std(final_fracs):>10.1%}
Max:                {np.max(initial_fracs):>10.1%}     {np.max(final_fracs):>10.1%}

Change: {np.mean(final_fracs) - np.mean(initial_fracs):+.1%}
""")
    
    # Aggregate degree distribution
    all_degrees = defaultdict(int)
    for r in results:
        for deg, count in r['final']['degree_distribution'].items():
            all_degrees[deg] += count
    
    total = sum(all_degrees.values())
    
    print("FINAL DEGREE DISTRIBUTION (aggregated):")
    print(f"{'Degree':>8} | {'Count':>8} | {'Fraction':>10}")
    print("-" * 35)
    for deg in sorted(all_degrees.keys()):
        count = all_degrees[deg]
        frac = count / total if total > 0 else 0
        marker = " <-- TARGET" if deg == 3 else ""
        print(f"{deg:>8} | {count:>8} | {frac:>10.1%}{marker}")
    
    # Verdict
    success = np.mean(final_fracs) > 0.70
    
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    
    if success:
        verdict = "SUCCESS"
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ DEGREE PENALTY WITH RECONNECTION FORCES DEGREE = 3                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Energy penalty (degree - 3)² + reconnection dynamics → degree-3 attractor   ║
║                                                                              ║
║  PHYSICAL INTERPRETATION:                                                    ║
║  If the medium penalizes non-3 junctions energetically, and can reconnect,   ║
║  then Y-junctions emerge as the stable configuration.                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    else:
        verdict = "PARTIAL" if np.mean(final_fracs) > np.mean(initial_fracs) else "FAILURE"
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ RESULT: {verdict:<68}║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Mean deg-3: {np.mean(initial_fracs):.1%} → {np.mean(final_fracs):.1%} (threshold: 70%)                          ║
║                                                                              ║
║  The penalty helps but current reconnection dynamics may be insufficient.    ║
║  Next steps:                                                                 ║
║    1. Increase penalty weight                                                ║
║    2. Add more aggressive reconnection (edge swap, node merge)               ║
║    3. Try Metropolis-style acceptance                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Time evolution plot
    print("\n" + "=" * 80)
    print("DEGREE-3 FRACTION EVOLUTION (Trial 0)")
    print("=" * 80)
    
    if results[0]['history']:
        print("\nTime     | Deg-3 Frac | Bar")
        print("-" * 50)
        for h in results[0]['history']:
            t = h['time']
            f3 = h['frac_degree_3']
            bar = "#" * int(f3 * 40)
            print(f"{t:>8.1f} | {f3:>10.1%} | {bar}")
    
    # Save results
    output = {
        'test': 'Degree_Selection_With_Reconnection',
        'initial_mean_frac_3': float(np.mean(initial_fracs)),
        'final_mean_frac_3': float(np.mean(final_fracs)),
        'improvement': float(np.mean(final_fracs) - np.mean(initial_fracs)),
        'success': bool(success),
        'verdict': verdict,
        'success_threshold': 0.70
    }
    
    output_path = '/app/backend/qmrt_topology/degree_selection_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return output


if __name__ == "__main__":
    results = run_degree_selection_test()
