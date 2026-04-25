"""
Phase 11: Spacetime Capacity Expansion Test
============================================

CONCEPTUAL DISTINCTION:

1. Geometry Expansion (Phase 10 - ruled out)
   - Scaffold spreads in space
   - Radius, diameter increase
   - Does NOT explain dimensional branching

2. Spacetime Expansion (This test)
   - Medium builds event-supporting capacity
   - More relational states become available
   - Richer structure becomes POSSIBLE
   - Geometry fills the capacity

KEY IDEA:
Spacetime expansion is not increase in geometric size, but increase in the 
medium's capacity to host stable relational structure.

OBSERVABLES FOR SPACETIME CAPACITY:

1. Event Persistence Capacity
   - How long do defects survive on average?
   - Are there more long-lived structures over time?

2. Causal Chain Density
   - How many connected paths exist between nodes?
   - Network redundancy / alternative paths

3. Temporal Overlap
   - How many structures coexist at the same time?
   - Simultaneous event density

4. Loop-Support Capacity
   - Not just triangle count, but capacity for loops
   - How many independent loops can the medium sustain?

5. Relational State Richness
   - Variety of local neighborhood configurations
   - Entropy of degree distribution

6. Geometry-Hosting Capacity
   - Given bounded extent, how much structure fits?
   - Structure density within the attractor region
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr, entropy
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class CapacityTestSimulator:
    """Simulator for spacetime capacity testing."""
    
    def __init__(self, size: int = 48, injection_interval: int = 100):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 3
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.005
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
        # Defect tracking for persistence
        self.defect_history = []  # List of (step, defect_positions)
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = 0.7
                    elif dist >= interior_r + 10.0:
                        coupling[i, j, k] = 0.2
                    else:
                        t = (dist - interior_r) / 10.0
                        coupling[i, j, k] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        return coupling
    
    def inject_vortex(self, cx: int, cy: int):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_random_vortices(self):
        center = self.size // 2
        for _ in range(self.injection_count):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        if self.step_count % self.injection_interval == 0:
            self.inject_random_vortices()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        c_eff_sq = self.c_0_sq * self.tau
        
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
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
        
        self.remnant_field += 0.02 * topology_norm
        self.remnant_field *= 0.999
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
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
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                defects.append((
                    int(np.mean(coords[0])),
                    int(np.mean(coords[1])),
                    int(np.mean(coords[2]))
                ))
        return defects


def euclidean_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_capacity_metrics(defects, size) -> Dict:
    """
    Measure spacetime capacity metrics.
    
    These focus on CAPACITY rather than EXTENT:
    - How much structure can the medium host?
    - How rich is the relational organization?
    - How redundant/robust is the connectivity?
    """
    n = len(defects)
    
    if n < 15:
        return {'valid': False, 'n': n}
    
    # Sample for large populations
    max_n = min(n, 150)
    if n > max_n:
        indices = np.random.choice(n, max_n, replace=False)
        sample = [defects[i] for i in indices]
    else:
        sample = defects
        max_n = n
    
    # Build adjacency
    adj = defaultdict(set)
    for i in range(max_n):
        for j in range(i + 1, max_n):
            d = euclidean_periodic(sample[i], sample[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    # Basic counts
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    degrees = [len(adj[i]) for i in range(max_n)]
    mean_degree = np.mean(degrees) if degrees else 0
    
    # 1. STRUCTURE DENSITY (geometry-hosting capacity)
    # How much structure per unit of occupied volume?
    center = size / 2
    radii = [np.sqrt((d[0]-center)**2 + (d[1]-center)**2 + (d[2]-center)**2) 
             for d in sample]
    occupied_radius = np.percentile(radii, 90) if radii else 1
    occupied_volume = (4/3) * np.pi * occupied_radius**3
    
    structure_density = edges / (occupied_volume + 1) if occupied_volume > 0 else 0
    node_density = max_n / (occupied_volume + 1)
    
    # 2. RELATIONAL STATE RICHNESS (entropy of degree distribution)
    if degrees and max(degrees) > 0:
        degree_counts = np.bincount(degrees)
        degree_probs = degree_counts / sum(degree_counts)
        degree_probs = degree_probs[degree_probs > 0]
        degree_entropy = entropy(degree_probs)
    else:
        degree_entropy = 0
    
    # 3. LOOP CAPACITY (independent cycles)
    # Euler formula: V - E + F = 2 for connected planar, cycles = E - V + 1
    # For general graphs, cycle rank = E - V + C (C = components)
    
    # Find connected components
    visited = set()
    components = 0
    for start in range(max_n):
        if start not in visited:
            components += 1
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    for neighbor in adj[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)
    
    cycle_rank = edges - max_n + components  # Number of independent cycles
    cycle_capacity = cycle_rank / max_n if max_n > 0 else 0  # Cycles per node
    
    # 4. PATH REDUNDANCY (alternative routes)
    # For a sample of node pairs, count number of edge-disjoint paths
    # Simplified: check if removing one edge disconnects the pair
    
    redundancy_samples = []
    sample_pairs = min(50, max_n * (max_n - 1) // 2)
    
    for _ in range(sample_pairs):
        i, j = np.random.choice(max_n, 2, replace=False)
        
        # BFS to find path length
        dist = {i: 0}
        queue = deque([i])
        while queue and j not in dist:
            node = queue.popleft()
            for neighbor in adj[node]:
                if neighbor not in dist:
                    dist[neighbor] = dist[node] + 1
                    queue.append(neighbor)
        
        if j in dist:
            # Found path, now check if there's an alternative
            # by temporarily removing first edge on path
            # (simplified redundancy check)
            redundancy_samples.append(1 if dist[j] > 0 else 0)
    
    path_redundancy = np.mean(redundancy_samples) if redundancy_samples else 0
    
    # 5. TRIANGLES (loop richness at local level)
    triangles = 0
    for node in range(max_n):
        neighbors = list(adj[node])
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    triangles += 1
    triangles //= 3
    
    tri_per_node = triangles / max_n if max_n > 0 else 0
    
    # 6. EFFECTIVE DIMENSION (how space-filling is the structure?)
    max_sources = min(max_n, 30)
    graph_dist = np.full((max_sources, max_n), np.inf)
    
    for idx in range(max_sources):
        graph_dist[idx, idx] = 0
        queue = deque([idx])
        visited_bfs = {idx}
        while queue:
            node = queue.popleft()
            for neighbor in adj[node]:
                if neighbor not in visited_bfs:
                    visited_bfs.add(neighbor)
                    graph_dist[idx, neighbor] = graph_dist[idx, node] + 1
                    queue.append(neighbor)
    
    radii_list = [1, 2, 3, 4, 5]
    counts = [np.mean([np.sum((graph_dist[idx, :] <= r) & (graph_dist[idx, :] > 0)) 
                       for idx in range(max_sources)]) for r in radii_list]
    
    if min(counts) > 0:
        dimension = np.polyfit(np.log(radii_list), np.log(np.array(counts) + 1), 1)[0]
    else:
        dimension = 0
    
    return {
        'valid': True,
        'n': n,
        # Capacity metrics
        'structure_density': structure_density,
        'node_density': node_density,
        'degree_entropy': degree_entropy,
        'cycle_capacity': cycle_capacity,
        'cycle_rank': cycle_rank,
        'tri_per_node': tri_per_node,
        # Traditional metrics for comparison
        'dimension': dimension,
        'edges': edges,
        'mean_degree': mean_degree,
        'occupied_radius': occupied_radius,
    }


def run_capacity_evolution_test():
    """
    Track spacetime capacity metrics over time.
    
    Question: Does the medium's capacity to host structure increase,
    even when geometric extent doesn't?
    """
    print("=" * 75)
    print("  PHASE 11: SPACETIME CAPACITY EXPANSION TEST")
    print("=" * 75)
    print()
    print("Question: Does the medium build capacity for richer structure,")
    print("          even when geometric extent stays bounded?")
    print()
    
    sim = CapacityTestSimulator(size=48, injection_interval=100)
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    print("Tracking capacity metrics over time:")
    print()
    print(f"{'Step':>6} {'Pop':>5} {'Radius':>6} {'StrDen':>7} {'CycleCap':>8} "
          f"{'DegEnt':>6} {'Dim':>5}")
    print("-" * 55)
    
    history = []
    
    for step in range(2500):
        sim.step()
        
        if step % 100 == 0:
            defects = sim.detect_defects()
            m = measure_capacity_metrics(defects, sim.size)
            
            if m['valid']:
                print(f"{step:>6} {m['n']:>5} {m['occupied_radius']:>6.1f} "
                      f"{m['structure_density']:>7.4f} {m['cycle_capacity']:>8.3f} "
                      f"{m['degree_entropy']:>6.2f} {m['dimension']:>5.2f}")
                
                m['step'] = step
                history.append(m)
    
    # Analysis
    print()
    print("=" * 75)
    print("ANALYSIS: Capacity vs Dimension")
    print("=" * 75)
    print()
    
    if len(history) >= 5:
        # Focus on peak states only
        peaks = [h for h in history if h['n'] > 200]
        
        if len(peaks) >= 3:
            print(f"Analyzing {len(peaks)} peak-state measurements:")
            print()
            
            dims = [h['dimension'] for h in peaks]
            str_dens = [h['structure_density'] for h in peaks]
            cycle_caps = [h['cycle_capacity'] for h in peaks]
            deg_ents = [h['degree_entropy'] for h in peaks]
            tri_per_nodes = [h['tri_per_node'] for h in peaks]
            radii = [h['occupied_radius'] for h in peaks]
            
            print("Correlations with effective dimension:")
            print(f"  Structure density vs dim: {pearsonr(str_dens, dims)[0]:.3f}")
            print(f"  Cycle capacity vs dim:    {pearsonr(cycle_caps, dims)[0]:.3f}")
            print(f"  Degree entropy vs dim:    {pearsonr(deg_ents, dims)[0]:.3f}")
            print(f"  Triangles/node vs dim:    {pearsonr(tri_per_nodes, dims)[0]:.3f}")
            print(f"  Occupied radius vs dim:   {pearsonr(radii, dims)[0]:.3f} (Phase 10 control)")
            
            print()
            
            # Find best predictor
            correlations = [
                ('Structure density', pearsonr(str_dens, dims)[0]),
                ('Cycle capacity', pearsonr(cycle_caps, dims)[0]),
                ('Degree entropy', pearsonr(deg_ents, dims)[0]),
                ('Triangles/node', pearsonr(tri_per_nodes, dims)[0]),
                ('Occupied radius', pearsonr(radii, dims)[0]),
            ]
            
            best = max(correlations, key=lambda x: abs(x[1]))
            print(f"Best predictor of dimension: {best[0]} (r = {best[1]:.3f})")
            
            print()
            print("KEY QUESTION: Do capacity metrics predict dimension better than extent?")
            print()
            
            extent_corr = abs(pearsonr(radii, dims)[0])
            capacity_corrs = [abs(c[1]) for c in correlations[:-1]]
            best_capacity = max(capacity_corrs)
            
            if best_capacity > extent_corr:
                print(f"YES: Best capacity metric ({best[0]}) correlates better")
                print(f"     Capacity: r = {best_capacity:.3f}")
                print(f"     Extent:   r = {extent_corr:.3f}")
                print()
                print("→ Supports spacetime CAPACITY expansion over geometric expansion")
            else:
                print(f"NO: Extent still correlates as well or better")
                print(f"     Capacity: r = {best_capacity:.3f}")
                print(f"     Extent:   r = {extent_corr:.3f}")
    
    # Save
    output_path = '/app/backend/qmrt_topology/papers/phase11_capacity_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'spacetime_capacity_expansion',
            'history': history,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history


if __name__ == "__main__":
    results = run_capacity_evolution_test()
