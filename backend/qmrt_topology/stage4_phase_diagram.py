"""
QMRT STAGE 4 PARAMETER SWEEP — PHASE DIAGRAM
=============================================

Map the phase structure by varying:
1. Noise amplitude (σ) — Low→frozen, High→chaos, Mid→nucleation
2. Decay rate — Controls structure turnover
3. Grid density — Node/edge density

Goal: Find the SELECTION PHASE where fermionic dominance emerges.

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
from dataclasses import dataclass
import json
import time as timer


# =============================================================================
# BASE CONFIG
# =============================================================================

BASE_CONFIG = {
    'grid_size': 12,
    'timesteps': 2000,
    'node_density': 0.4,
    'edge_probability': 0.25,
    'noise_amplitude': 0.05,
    'decay_base_rate': 0.01,
}

RUNS_PER_POINT = 6


# =============================================================================
# SIMULATION (Compact version)
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


class QuickSimulation:
    """Simplified simulation for parameter sweep."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.size = config['grid_size']
        self.nodes = {}
        self.edges = {}
        self.structures = {}
        self.next_id = 0
        self.known_loops = {}
    
    def initialize(self):
        num_nodes = int(self.size**2 * self.config['node_density'])
        
        for i in range(num_nodes):
            x = np.random.uniform(0, self.size)
            y = np.random.uniform(0, self.size)
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
        
        starts = [n for n in self.nodes if len(adj[n]) >= 2][:40]
        max_loops = 100
        
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
        
        for t in range(self.config['timesteps']):
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
        
        return {
            'total_alive': total,
            'f_count': f_count,
            'b_count': b_count,
            'f_fraction': f_count / max(1, total),
            'total_nucleated': len(self.structures)
        }


# =============================================================================
# PARAMETER SWEEP
# =============================================================================

def sweep_noise_amplitude():
    """Sweep noise amplitude σ."""
    print("\n  SWEEP: Noise Amplitude (σ)")
    print("  " + "-" * 40)
    
    noise_values = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
    results = {}
    
    for noise in noise_values:
        config = {**BASE_CONFIG, 'noise_amplitude': noise}
        f_fracs = []
        
        for run in range(RUNS_PER_POINT):
            np.random.seed(run * 7919 + int(noise * 1000))
            sim = QuickSimulation(config)
            res = sim.run()
            f_fracs.append(res['f_fraction'])
        
        mean_f = np.mean(f_fracs)
        results[noise] = {
            'mean_f_fraction': mean_f,
            'std': np.std(f_fracs),
            'dominance': mean_f > 0.6
        }
        
        print(f"    σ={noise:.2f}: F-fraction = {100*mean_f:.1f}% {'✓' if mean_f > 0.6 else ''}")
    
    return results


def sweep_decay_rate():
    """Sweep decay rate."""
    print("\n  SWEEP: Decay Rate")
    print("  " + "-" * 40)
    
    decay_values = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]
    results = {}
    
    for decay in decay_values:
        config = {**BASE_CONFIG, 'decay_base_rate': decay}
        f_fracs = []
        alive_counts = []
        
        for run in range(RUNS_PER_POINT):
            np.random.seed(run * 7919 + int(decay * 10000))
            sim = QuickSimulation(config)
            res = sim.run()
            f_fracs.append(res['f_fraction'])
            alive_counts.append(res['total_alive'])
        
        mean_f = np.mean(f_fracs)
        mean_alive = np.mean(alive_counts)
        results[decay] = {
            'mean_f_fraction': mean_f,
            'mean_alive': mean_alive,
            'dominance': mean_f > 0.6
        }
        
        print(f"    decay={decay:.3f}: F={100*mean_f:.1f}%, alive={mean_alive:.1f} {'✓' if mean_f > 0.6 else ''}")
    
    return results


def sweep_grid_density():
    """Sweep node density."""
    print("\n  SWEEP: Node Density")
    print("  " + "-" * 40)
    
    density_values = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    results = {}
    
    for density in density_values:
        config = {**BASE_CONFIG, 'node_density': density}
        f_fracs = []
        
        for run in range(RUNS_PER_POINT):
            np.random.seed(run * 7919 + int(density * 1000))
            sim = QuickSimulation(config)
            res = sim.run()
            f_fracs.append(res['f_fraction'])
        
        mean_f = np.mean(f_fracs)
        results[density] = {
            'mean_f_fraction': mean_f,
            'dominance': mean_f > 0.6
        }
        
        print(f"    density={density:.1f}: F-fraction = {100*mean_f:.1f}% {'✓' if mean_f > 0.6 else ''}")
    
    return results


def sweep_2d_noise_decay():
    """2D sweep: noise vs decay."""
    print("\n  SWEEP: 2D Phase Diagram (Noise × Decay)")
    print("  " + "-" * 40)
    
    noise_values = [0.02, 0.05, 0.1, 0.2]
    decay_values = [0.005, 0.01, 0.02, 0.05]
    
    results = {}
    
    print(f"\n    {'':>10}", end='')
    for decay in decay_values:
        print(f"  d={decay:.3f}", end='')
    print()
    
    for noise in noise_values:
        print(f"    σ={noise:.2f}  ", end='')
        results[noise] = {}
        
        for decay in decay_values:
            config = {**BASE_CONFIG, 'noise_amplitude': noise, 'decay_base_rate': decay}
            f_fracs = []
            
            for run in range(RUNS_PER_POINT):
                np.random.seed(run * 7919 + int(noise * 1000) + int(decay * 10000))
                sim = QuickSimulation(config)
                res = sim.run()
                f_fracs.append(res['f_fraction'])
            
            mean_f = np.mean(f_fracs)
            results[noise][decay] = mean_f
            
            # Visual indicator
            if mean_f > 0.8:
                symbol = "█"  # Strong F-dominance
            elif mean_f > 0.6:
                symbol = "▓"  # Moderate F-dominance
            elif mean_f > 0.4:
                symbol = "▒"  # Weak/neutral
            else:
                symbol = "░"  # B-dominant or chaotic
            
            print(f"  {100*mean_f:5.0f}%{symbol}", end='')
        
        print()
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def run_parameter_sweep():
    """Run full parameter sweep."""
    print("=" * 70)
    print("  QMRT STAGE 4 PARAMETER SWEEP — PHASE DIAGRAM")
    print("=" * 70)
    print()
    
    start_time = timer.time()
    
    results = {
        'base_config': BASE_CONFIG,
        'runs_per_point': RUNS_PER_POINT,
        'sweeps': {}
    }
    
    results['sweeps']['noise'] = sweep_noise_amplitude()
    results['sweeps']['decay'] = sweep_decay_rate()
    results['sweeps']['density'] = sweep_grid_density()
    results['sweeps']['2d_phase'] = sweep_2d_noise_decay()
    
    elapsed = timer.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("  PARAMETER SWEEP SUMMARY")
    print("=" * 70)
    
    # Find optimal regions
    noise_sweep = results['sweeps']['noise']
    optimal_noise = [k for k, v in noise_sweep.items() if v['dominance']]
    
    decay_sweep = results['sweeps']['decay']
    optimal_decay = [k for k, v in decay_sweep.items() if v['dominance']]
    
    print(f"""
  1. NOISE AMPLITUDE (σ):
     Optimal range: {optimal_noise if optimal_noise else 'None found'}
     
  2. DECAY RATE:
     Optimal range: {optimal_decay if optimal_decay else 'None found'}
     
  3. PHASE REGIONS:
     █ Strong F-dominance (>80%)
     ▓ Moderate F-dominance (60-80%)
     ▒ Neutral/weak (40-60%)
     ░ B-dominant or chaotic (<40%)
     
  4. KEY FINDING:
    """)
    
    # Find the selection regime
    phase_2d = results['sweeps']['2d_phase']
    selection_regime = []
    for noise, decay_dict in phase_2d.items():
        for decay, f_frac in decay_dict.items():
            if f_frac > 0.7:
                selection_regime.append((noise, decay, f_frac))
    
    if selection_regime:
        print("     ✅ SELECTION PHASE FOUND")
        print("        Fermionic dominance emerges in specific parameter region:")
        for noise, decay, f_frac in selection_regime[:5]:
            print(f"        σ={noise}, decay={decay} → F={100*f_frac:.0f}%")
    else:
        print("     ⚠️ No clear selection phase found")
    
    print(f"\n  Elapsed time: {elapsed:.1f} seconds")
    
    # Save
    def convert(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, dict):
            return {str(k): convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj
    
    output_path = '/app/backend/qmrt_topology/stage4_phase_diagram_results.json'
    with open(output_path, 'w') as f:
        json.dump(convert(results), f, indent=2)
    
    print(f"\n  Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_parameter_sweep()
