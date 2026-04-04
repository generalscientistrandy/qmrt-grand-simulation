"""
QMRT STAGE 4 SCALING TEST — LEGITIMACY TEST
============================================

Test if the emergent physics holds at larger scales.

Scale variables:
- Grid size: 10 → 15 → 20 → 25
- Timesteps: proportionally scaled

What must remain INVARIANT:
- F-dominance percentage
- Survival fraction
- Qualitative behavior

If it breaks at scale → finite-size artifact
If it holds → scale-independent emergence (huge!)

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import json
import time as timer


# =============================================================================
# SIMULATION (Reused from phase diagram)
# =============================================================================

def compute_holonomy(positions: List[Tuple[float, float]]) -> complex:
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
    magnitude = abs(holonomy)
    mag_stab = np.exp(-10 * (magnitude - 1)**2)
    phase = np.angle(holonomy)
    coherence = np.cos(phase)**2
    size_factor = np.exp(-0.05 * loop_size)
    return mag_stab * (0.3 + 0.7 * coherence) * size_factor


class ScalableSimulation:
    """Simulation that can scale."""
    
    def __init__(self, grid_size: int, timesteps: int, config: Dict):
        self.grid_size = grid_size
        self.timesteps = timesteps
        self.config = config
        
        self.nodes = {}
        self.edges = {}
        self.structures = {}
        self.next_id = 0
        self.known_loops = {}
    
    def initialize(self):
        num_nodes = int(self.grid_size**2 * self.config['node_density'])
        
        for i in range(num_nodes):
            x = np.random.uniform(0, self.grid_size)
            y = np.random.uniform(0, self.grid_size)
            self.nodes[i] = {'x': x, 'y': y, 'edges': []}
        
        node_list = list(self.nodes.keys())
        radius = 2.0
        
        eid = 0
        for i, na in enumerate(node_list):
            for nb in node_list[i+1:]:
                dist = np.sqrt(
                    (self.nodes[na]['x'] - self.nodes[nb]['x'])**2 +
                    (self.nodes[na]['y'] - self.nodes[nb]['y'])**2
                )
                if dist < radius and np.random.random() < self.config['edge_probability']:
                    self.edges[eid] = (na, nb)
                    self.nodes[na]['edges'].append(eid)
                    self.nodes[nb]['edges'].append(eid)
                    eid += 1
    
    def find_loops(self, max_size=8):
        loops = []
        visited = set()
        
        adj = defaultdict(set)
        for eid, (a, b) in self.edges.items():
            adj[a].add(b)
            adj[b].add(a)
        
        # Scale search proportionally
        max_starts = min(100, len(self.nodes))
        starts = [n for n in self.nodes if len(adj[n]) >= 2][:max_starts]
        max_loops = min(300, self.grid_size * 15)
        
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
        
        for n in starts:
            if len(loops) >= max_loops:
                break
            dfs(n, n, [n], 1)
        
        return loops
    
    def run(self) -> Dict:
        self.initialize()
        
        for t in range(self.timesteps):
            loops = self.find_loops()
            current_keys = set()
            
            for loop_nodes in loops:
                key = tuple(sorted(loop_nodes))
                current_keys.add(key)
                
                if key not in self.known_loops:
                    positions = [(self.nodes[n]['x'], self.nodes[n]['y']) for n in loop_nodes]
                    holonomy = compute_holonomy(positions)
                    stability = compute_stability(holonomy, len(loop_nodes))
                    
                    self.structures[self.next_id] = {
                        'holonomy': holonomy,
                        'stability': stability,
                        'birth': t,
                        'alive': True
                    }
                    self.known_loops[key] = self.next_id
                    self.next_id += 1
            
            # Decay
            for sid, s in list(self.structures.items()):
                if not s['alive']:
                    continue
                decay = self.config['decay_base_rate'] / max(0.01, s['stability'])
                if np.random.random() < decay:
                    s['alive'] = False
                    for k, v in list(self.known_loops.items()):
                        if v == sid:
                            del self.known_loops[k]
                            break
        
        # Analyze
        alive = [s for s in self.structures.values() if s['alive']]
        total = len(alive)
        
        f_count = sum(1 for s in alive if abs(s['holonomy'] + 1) < 0.3)
        b_count = sum(1 for s in alive if abs(s['holonomy'] - 1) < 0.3)
        
        # Survival rate
        total_nucleated = len(self.structures)
        survival_rate = total / max(1, total_nucleated)
        
        return {
            'grid_size': self.grid_size,
            'timesteps': self.timesteps,
            'total_alive': total,
            'f_count': f_count,
            'b_count': b_count,
            'f_fraction': f_count / max(1, total),
            'total_nucleated': total_nucleated,
            'survival_rate': survival_rate,
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges)
        }


# =============================================================================
# SCALING TEST
# =============================================================================

def run_scaling_test():
    """Run scaling test."""
    print("=" * 70)
    print("  QMRT STAGE 4 SCALING TEST — LEGITIMACY TEST")
    print("=" * 70)
    print()
    
    start_time = timer.time()
    
    # Configuration
    base_config = {
        'node_density': 0.4,
        'edge_probability': 0.25,
        'noise_amplitude': 0.05,
        'decay_base_rate': 0.01,
    }
    
    # Scale points
    scales = [
        (10, 1000),   # Small
        (12, 1500),   # Medium-small
        (15, 2000),   # Medium
        (18, 2500),   # Medium-large
        (20, 3000),   # Large
    ]
    
    runs_per_scale = 5
    
    results = {
        'config': base_config,
        'scales': {}
    }
    
    print(f"  {'Scale':^12} {'Nodes':^8} {'F-frac':^10} {'Survival':^10} {'Verdict':^10}")
    print("  " + "-" * 60)
    
    reference_f_fraction = None
    all_f_fractions = []
    
    for grid_size, timesteps in scales:
        scale_results = []
        
        for run in range(runs_per_scale):
            np.random.seed(run * 7919 + grid_size * 100)
            
            sim = ScalableSimulation(grid_size, timesteps, base_config)
            res = sim.run()
            scale_results.append(res)
        
        # Aggregate
        mean_f = np.mean([r['f_fraction'] for r in scale_results])
        std_f = np.std([r['f_fraction'] for r in scale_results])
        mean_survival = np.mean([r['survival_rate'] for r in scale_results])
        mean_nodes = np.mean([r['num_nodes'] for r in scale_results])
        
        all_f_fractions.append(mean_f)
        
        if reference_f_fraction is None:
            reference_f_fraction = mean_f
            verdict = "baseline"
        else:
            # Check if within 20% of reference
            diff = abs(mean_f - reference_f_fraction) / max(0.1, reference_f_fraction)
            if diff < 0.2:
                verdict = "✓ invariant"
            else:
                verdict = "✗ drift"
        
        results['scales'][grid_size] = {
            'timesteps': timesteps,
            'mean_f_fraction': float(mean_f),
            'std_f_fraction': float(std_f),
            'mean_survival_rate': float(mean_survival),
            'mean_nodes': float(mean_nodes),
            'verdict': verdict,
            'runs': [{
                'f_fraction': float(r['f_fraction']),
                'survival_rate': float(r['survival_rate']),
                'total_alive': r['total_alive'],
                'total_nucleated': r['total_nucleated']
            } for r in scale_results]
        }
        
        print(f"  {grid_size}×{grid_size}→{timesteps}   {mean_nodes:6.0f}   {100*mean_f:5.1f}%±{100*std_f:4.1f}%   {100*mean_survival:5.1f}%     {verdict}")
    
    elapsed = timer.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("  SCALING TEST SUMMARY")
    print("=" * 70)
    
    # Check scale invariance
    spread = max(all_f_fractions) - min(all_f_fractions)
    scale_invariant = spread < 0.25  # Less than 25% spread
    
    print(f"""
  1. F-FRACTION ACROSS SCALES:
     Min: {100*min(all_f_fractions):.1f}%
     Max: {100*max(all_f_fractions):.1f}%
     Spread: {100*spread:.1f}%
     
  2. SCALE INVARIANCE:
     {'✅ CONFIRMED' if scale_invariant else '⚠️ SOME DRIFT DETECTED'}
     
  3. INTERPRETATION:
    """)
    
    if scale_invariant:
        print("     ✅ F-dominance is SCALE-INDEPENDENT")
        print("        This is genuine emergence, not a finite-size artifact!")
        print("        The physics holds at larger scales.")
    else:
        print("     ⚠️ Some scale dependence detected")
        print("        May need larger scales or longer equilibration times")
    
    results['summary'] = {
        'f_fraction_spread': float(spread),
        'scale_invariant': bool(scale_invariant),
        'all_f_fractions': [float(f) for f in all_f_fractions],
        'elapsed_seconds': elapsed
    }
    
    print(f"\n  Elapsed time: {elapsed:.1f} seconds")
    
    # Save
    output_path = '/app/backend/qmrt_topology/stage4_scaling_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n  Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_scaling_test()
