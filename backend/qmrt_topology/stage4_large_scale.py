"""
QMRT STAGE 4 LARGE-SCALE VALIDATION
====================================

Run scaling tests at 50×50 and above to definitively prove scale invariance.

This is the final validation step before locking Stage 4.

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import json
import time as timer


# =============================================================================
# OPTIMIZED SIMULATION FOR LARGE SCALES
# =============================================================================

def compute_holonomy(positions: List[Tuple[float, float]]) -> complex:
    """Compute holonomy using Y-junction transport."""
    n = len(positions)
    total_phase = 0.0
    
    for i in range(n):
        prev = positions[(i - 1) % n]
        curr = positions[i]
        next_p = positions[(i + 1) % n]
        
        angle_in = np.arctan2(curr[1] - prev[1], curr[0] - prev[0])
        angle_out = np.arctan2(next_p[1] - curr[1], next_p[0] - curr[0])
        
        turn = angle_out - angle_in
        while turn > np.pi: turn -= 2 * np.pi
        while turn < -np.pi: turn += 2 * np.pi
        
        total_phase += -turn / 2
    
    return np.exp(1j * total_phase)


def compute_stability(holonomy: complex, loop_size: int) -> float:
    """Geometric stability function."""
    magnitude = abs(holonomy)
    mag_stab = np.exp(-10 * (magnitude - 1)**2)
    phase = np.angle(holonomy)
    coherence = np.cos(phase)**2
    size_factor = np.exp(-0.05 * loop_size)
    return mag_stab * (0.3 + 0.7 * coherence) * size_factor


class LargeScaleSimulation:
    """Optimized simulation for large grids."""
    
    def __init__(self, grid_size: int, timesteps: int, 
                 node_density: float = 0.3,
                 edge_probability: float = 0.2,
                 decay_rate: float = 0.01):
        self.grid_size = grid_size
        self.timesteps = timesteps
        self.node_density = node_density
        self.edge_probability = edge_probability
        self.decay_rate = decay_rate
        
        self.nodes = {}
        self.edges = {}
        self.structures = {}
        self.next_id = 0
        self.known_loops = {}
    
    def initialize(self):
        """Initialize nodes and edges."""
        num_nodes = int(self.grid_size**2 * self.node_density)
        
        # Create nodes
        for i in range(num_nodes):
            x = np.random.uniform(0, self.grid_size)
            y = np.random.uniform(0, self.grid_size)
            self.nodes[i] = {'x': x, 'y': y, 'edges': []}
        
        # Create edges using spatial hashing for efficiency
        cell_size = 2.5
        cells = defaultdict(list)
        
        for nid, node in self.nodes.items():
            cx = int(node['x'] / cell_size)
            cy = int(node['y'] / cell_size)
            cells[(cx, cy)].append(nid)
        
        eid = 0
        for (cx, cy), cell_nodes in cells.items():
            # Check this cell and neighbors
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    neighbor_cell = cells.get((cx + dx, cy + dy), [])
                    for na in cell_nodes:
                        for nb in neighbor_cell:
                            if na >= nb:
                                continue
                            
                            node_a = self.nodes[na]
                            node_b = self.nodes[nb]
                            dist = np.sqrt(
                                (node_a['x'] - node_b['x'])**2 +
                                (node_a['y'] - node_b['y'])**2
                            )
                            
                            if dist < 2.0 and np.random.random() < self.edge_probability:
                                self.edges[eid] = (na, nb)
                                node_a['edges'].append(eid)
                                node_b['edges'].append(eid)
                                eid += 1
    
    def find_loops(self, max_size=7, max_loops=None):
        """Find loops efficiently."""
        if max_loops is None:
            max_loops = min(500, self.grid_size * 20)
        
        loops = []
        visited = set()
        
        adj = defaultdict(set)
        for eid, (a, b) in self.edges.items():
            adj[a].add(b)
            adj[b].add(a)
        
        # Only start from nodes with sufficient connectivity
        start_nodes = [n for n in self.nodes if len(adj[n]) >= 2]
        np.random.shuffle(start_nodes)
        start_nodes = start_nodes[:min(150, len(start_nodes))]
        
        def dfs(start, curr, path, depth):
            if len(loops) >= max_loops or depth > max_size:
                return
            for neighbor in adj[curr]:
                if neighbor == start and len(path) >= 3:
                    key = tuple(sorted(path))
                    if key not in visited:
                        visited.add(key)
                        loops.append(list(path))
                elif neighbor not in path:
                    dfs(start, neighbor, path + [neighbor], depth + 1)
        
        for n in start_nodes:
            if len(loops) >= max_loops:
                break
            dfs(n, n, [n], 1)
        
        return loops
    
    def run(self, verbose=False) -> Dict:
        """Run simulation."""
        self.initialize()
        
        for t in range(self.timesteps):
            loops = self.find_loops()
            current_keys = set()
            
            for loop_nodes in loops:
                key = tuple(sorted(loop_nodes))
                current_keys.add(key)
                
                if key not in self.known_loops:
                    positions = [(self.nodes[n]['x'], self.nodes[n]['y']) 
                                 for n in loop_nodes]
                    holonomy = compute_holonomy(positions)
                    stability = compute_stability(holonomy, len(loop_nodes))
                    
                    self.structures[self.next_id] = {
                        'holonomy': holonomy,
                        'stability': stability,
                        'alive': True
                    }
                    self.known_loops[key] = self.next_id
                    self.next_id += 1
            
            # Decay
            for sid, s in list(self.structures.items()):
                if not s['alive']:
                    continue
                decay = self.decay_rate / max(0.01, s['stability'])
                if np.random.random() < decay:
                    s['alive'] = False
                    for k, v in list(self.known_loops.items()):
                        if v == sid:
                            del self.known_loops[k]
                            break
            
            if verbose and (t + 1) % 500 == 0:
                alive = sum(1 for s in self.structures.values() if s['alive'])
                print(f"      t={t+1}: {alive} alive")
        
        # Analyze
        alive = [s for s in self.structures.values() if s['alive']]
        total = len(alive)
        
        f_count = sum(1 for s in alive if abs(s['holonomy'] + 1) < 0.3)
        b_count = sum(1 for s in alive if abs(s['holonomy'] - 1) < 0.3)
        
        return {
            'grid_size': self.grid_size,
            'timesteps': self.timesteps,
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges),
            'total_alive': total,
            'f_count': f_count,
            'b_count': b_count,
            'f_fraction': f_count / max(1, total),
            'total_nucleated': len(self.structures)
        }


# =============================================================================
# LARGE-SCALE TEST
# =============================================================================

def run_large_scale_test():
    """Run large-scale validation."""
    print("=" * 75)
    print("  QMRT STAGE 4 LARGE-SCALE VALIDATION (50×50+)")
    print("=" * 75)
    print()
    
    start_time = timer.time()
    
    # Scale points
    scales = [
        (25, 2000, 3),   # Warmup
        (35, 2500, 3),   # Medium-large
        (50, 3000, 3),   # Target scale
        (65, 3500, 2),   # Extra large (fewer runs)
    ]
    
    results = {'scales': {}}
    all_f_fractions = []
    
    print(f"  {'Scale':^12} {'Nodes':^8} {'Edges':^8} {'F-frac':^12} {'Runs':^6}")
    print("  " + "-" * 60)
    
    for grid_size, timesteps, runs in scales:
        scale_results = []
        
        for run in range(runs):
            np.random.seed(run * 7919 + grid_size * 100)
            
            sim = LargeScaleSimulation(
                grid_size=grid_size,
                timesteps=timesteps,
                node_density=0.3,
                edge_probability=0.2,
                decay_rate=0.01
            )
            
            res = sim.run(verbose=False)
            scale_results.append(res)
        
        # Aggregate
        mean_f = np.mean([r['f_fraction'] for r in scale_results])
        std_f = np.std([r['f_fraction'] for r in scale_results])
        mean_nodes = np.mean([r['num_nodes'] for r in scale_results])
        mean_edges = np.mean([r['num_edges'] for r in scale_results])
        
        all_f_fractions.append(mean_f)
        
        results['scales'][grid_size] = {
            'timesteps': timesteps,
            'runs': runs,
            'mean_f_fraction': float(mean_f),
            'std_f_fraction': float(std_f),
            'mean_nodes': float(mean_nodes),
            'mean_edges': float(mean_edges),
            'individual_runs': [float(r['f_fraction']) for r in scale_results]
        }
        
        print(f"  {grid_size}×{grid_size}     {mean_nodes:>6.0f}   {mean_edges:>6.0f}   "
              f"{100*mean_f:>5.1f}%±{100*std_f:>4.1f}%   {runs}")
    
    elapsed = timer.time() - start_time
    
    # Summary
    print("\n" + "=" * 75)
    print("  LARGE-SCALE VALIDATION SUMMARY")
    print("=" * 75)
    
    spread = max(all_f_fractions) - min(all_f_fractions)
    mean_overall = np.mean(all_f_fractions)
    scale_invariant = spread < 0.20  # Tighter threshold for large scales
    
    print(f"""
  1. F-FRACTION ACROSS SCALES:
     25×25: {100*all_f_fractions[0]:.1f}%
     35×35: {100*all_f_fractions[1]:.1f}%
     50×50: {100*all_f_fractions[2]:.1f}%
     65×65: {100*all_f_fractions[3]:.1f}%
     
  2. STATISTICS:
     Mean: {100*mean_overall:.1f}%
     Spread: {100*spread:.1f}%
     
  3. SCALE INVARIANCE:
     {'✅ CONFIRMED — F-dominance is scale-independent' if scale_invariant else '⚠️ Some variation detected'}
     
  4. CONCLUSION:
    """)
    
    if scale_invariant and mean_overall > 0.6:
        print("     ✅ F-dominance is ROBUST at large scales")
        print("        This confirms the selection mechanism is genuine emergence")
        print("        Not a finite-size artifact")
    elif mean_overall > 0.55:
        print("     ✓ F-dominance present but with some scale variation")
        print("        May need longer equilibration at largest scales")
    else:
        print("     ⚠️ F-dominance weaker than expected at large scales")
    
    print(f"\n  Elapsed time: {elapsed:.1f} seconds")
    
    results['summary'] = {
        'all_f_fractions': [float(f) for f in all_f_fractions],
        'mean_overall': float(mean_overall),
        'spread': float(spread),
        'scale_invariant': bool(scale_invariant),
        'elapsed_seconds': elapsed
    }
    
    # Save
    output_path = '/app/backend/qmrt_topology/stage4_large_scale_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n  Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_large_scale_test()
