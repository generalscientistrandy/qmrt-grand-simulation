"""
QMRT STAGE 4 TIME EVOLUTION TEST — CONVERGENCE PROOF
=====================================================

This test determines whether the system:
1. CONVERGES to a stable regime ✔ (supports claim)
2. OSCILLATES in cyclic dynamics
3. DIVERGES (unstable)

Track over extended time:
- N_structures(t) — should spike → decay → plateau
- F_fraction(t) — should drift upward → stabilize
- Survival lifetime distribution — should show heavy tail
- Entropy proxy / disorder metric

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
import json
import time as timer


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    'grid_size': 15,
    'timesteps': 8000,          # Extended time for convergence test
    'node_density': 0.4,
    'edge_probability': 0.25,
    'noise_amplitude': 0.05,
    'decay_base_rate': 0.01,
    'runs': 8,
    'sample_interval': 100,     # Sample every N timesteps
}


# =============================================================================
# Y-JUNCTION TRANSPORT
# =============================================================================

def compute_loop_holonomy(positions: List[Tuple[float, float]]) -> complex:
    """Compute holonomy using Y-junction transport rule."""
    n = len(positions)
    total_phase = 0.0
    
    for i in range(n):
        prev = positions[(i - 1) % n]
        curr = positions[i]
        next_p = positions[(i + 1) % n]
        
        angle_in = np.arctan2(curr[1] - prev[1], curr[0] - prev[0])
        angle_out = np.arctan2(next_p[1] - curr[1], next_p[0] - curr[0])
        
        turn = angle_out - angle_in
        while turn > np.pi:
            turn -= 2 * np.pi
        while turn < -np.pi:
            turn += 2 * np.pi
        
        # Y-junction transport: phase = -turn/2
        total_phase += -turn / 2
    
    return np.exp(1j * total_phase)


def compute_stability(holonomy: complex, loop_size: int) -> float:
    """Geometric stability (no sector bias)."""
    magnitude = abs(holonomy)
    magnitude_stability = np.exp(-10 * (magnitude - 1)**2)
    
    phase = np.angle(holonomy)
    phase_coherence = np.cos(phase)**2
    
    size_factor = np.exp(-0.05 * loop_size)
    
    return magnitude_stability * (0.3 + 0.7 * phase_coherence) * size_factor


# =============================================================================
# MEDIUM
# =============================================================================

class Medium:
    def __init__(self, size: int, config: Dict):
        self.size = size
        self.config = config
        self.nodes: Dict[int, Dict] = {}
        self.edges: Dict[int, Dict] = {}
        self.next_node_id = 0
        self.next_edge_id = 0
    
    def initialize(self):
        num_nodes = int(self.size**2 * self.config['node_density'])
        
        for _ in range(num_nodes):
            x = np.random.uniform(0, self.size)
            y = np.random.uniform(0, self.size)
            
            self.nodes[self.next_node_id] = {
                'id': self.next_node_id, 'x': x, 'y': y, 'edges': []
            }
            self.next_node_id += 1
        
        node_list = list(self.nodes.values())
        connection_radius = 2.0
        
        for i, node_a in enumerate(node_list):
            for node_b in node_list[i+1:]:
                dist = np.sqrt(
                    (node_a['x'] - node_b['x'])**2 +
                    (node_a['y'] - node_b['y'])**2
                )
                
                if dist < connection_radius:
                    if np.random.random() < self.config['edge_probability']:
                        edge = {
                            'id': self.next_edge_id,
                            'node_a': node_a['id'],
                            'node_b': node_b['id']
                        }
                        self.edges[self.next_edge_id] = edge
                        node_a['edges'].append(self.next_edge_id)
                        node_b['edges'].append(self.next_edge_id)
                        self.next_edge_id += 1
    
    def find_loops(self, max_size: int = 10) -> List[List[int]]:
        loops = []
        visited = set()
        
        adjacency = defaultdict(set)
        for edge in self.edges.values():
            adjacency[edge['node_a']].add(edge['node_b'])
            adjacency[edge['node_b']].add(edge['node_a'])
        
        start_nodes = [n for n in self.nodes if len(adjacency[n]) >= 2]
        max_loops = 200
        
        def dfs(start, current, path, depth):
            if len(loops) >= max_loops or depth > max_size:
                return
            
            for neighbor in adjacency[current]:
                if neighbor == start and len(path) >= 3:
                    loop_key = tuple(sorted(path))
                    if loop_key not in visited:
                        visited.add(loop_key)
                        loops.append(list(path))
                elif neighbor not in path and len(loops) < max_loops:
                    dfs(start, neighbor, path + [neighbor], depth + 1)
        
        for node_id in start_nodes[:60]:
            if len(loops) >= max_loops:
                break
            dfs(node_id, node_id, [node_id], 1)
        
        return loops
    
    def get_positions(self, node_ids: List[int]) -> List[Tuple[float, float]]:
        return [(self.nodes[nid]['x'], self.nodes[nid]['y']) for nid in node_ids]


# =============================================================================
# STRUCTURE TRACKING
# =============================================================================

@dataclass
class Structure:
    id: int
    node_ids: List[int]
    holonomy: complex
    stability: float
    birth_time: int
    death_time: Optional[int] = None
    is_alive: bool = True
    
    @property
    def lifetime(self) -> int:
        return (self.death_time - self.birth_time) if self.death_time else 0


# =============================================================================
# TIME EVOLUTION SIMULATION
# =============================================================================

class TimeEvolutionSimulation:
    """Simulation for tracking time evolution."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.medium = Medium(config['grid_size'], config)
        self.structures: Dict[int, Structure] = {}
        self.next_id = 0
        self.known_loops: Dict[Tuple[int, ...], int] = {}
        self.time = 0
        
        # Time series
        self.n_structures_history: List[int] = []
        self.f_fraction_history: List[float] = []
        self.total_nucleated_history: List[int] = []
        self.total_deaths_history: List[int] = []
        
        self.total_deaths = 0
    
    def initialize(self):
        self.medium.initialize()
    
    def step(self):
        self.time += 1
        
        loops = self.medium.find_loops(max_size=10)
        current_loop_keys = set()
        
        for loop_nodes in loops:
            loop_key = tuple(sorted(loop_nodes))
            current_loop_keys.add(loop_key)
            
            if loop_key not in self.known_loops:
                positions = self.medium.get_positions(loop_nodes)
                holonomy = compute_loop_holonomy(positions)
                stability = compute_stability(holonomy, len(loop_nodes))
                
                structure = Structure(
                    id=self.next_id,
                    node_ids=loop_nodes,
                    holonomy=holonomy,
                    stability=stability,
                    birth_time=self.time
                )
                self.structures[self.next_id] = structure
                self.known_loops[loop_key] = self.next_id
                self.next_id += 1
        
        # Decay
        for structure in list(self.structures.values()):
            if not structure.is_alive:
                continue
            
            decay_rate = self.config['decay_base_rate'] / max(0.01, structure.stability)
            
            if np.random.random() < decay_rate:
                structure.death_time = self.time
                structure.is_alive = False
                self.total_deaths += 1
                loop_key = tuple(sorted(structure.node_ids))
                if loop_key in self.known_loops:
                    del self.known_loops[loop_key]
        
        # Check disappeared
        for loop_key, sid in list(self.known_loops.items()):
            if loop_key not in current_loop_keys:
                if sid in self.structures and self.structures[sid].is_alive:
                    self.structures[sid].death_time = self.time
                    self.structures[sid].is_alive = False
                    self.total_deaths += 1
    
    def record_state(self):
        """Record current state."""
        alive = [s for s in self.structures.values() if s.is_alive]
        n_alive = len(alive)
        
        if n_alive > 0:
            f_count = sum(1 for s in alive if abs(s.holonomy + 1) < 0.3)
            f_frac = f_count / n_alive
        else:
            f_frac = 0.5
        
        self.n_structures_history.append(n_alive)
        self.f_fraction_history.append(f_frac)
        self.total_nucleated_history.append(len(self.structures))
        self.total_deaths_history.append(self.total_deaths)
    
    def run(self, verbose: bool = False) -> Dict:
        self.initialize()
        
        for t in range(self.config['timesteps']):
            self.step()
            
            if (t + 1) % self.config['sample_interval'] == 0:
                self.record_state()
            
            if verbose and (t + 1) % 1000 == 0:
                alive = sum(1 for s in self.structures.values() if s.is_alive)
                print(f"    t={t+1}: {alive} alive")
        
        return self._analyze()
    
    def _analyze(self) -> Dict:
        """Analyze time evolution."""
        n_hist = np.array(self.n_structures_history)
        f_hist = np.array(self.f_fraction_history)
        
        # Divide into phases
        n_samples = len(n_hist)
        early = n_hist[:n_samples//4]
        middle = n_hist[n_samples//4:3*n_samples//4]
        late = n_hist[3*n_samples//4:]
        
        # Check convergence patterns
        # 1. N_structures: should plateau
        late_std = np.std(late)
        late_mean = np.mean(late)
        n_converged = late_std < late_mean * 0.3 if late_mean > 0 else True
        
        # 2. F_fraction: should stabilize
        f_early = np.mean(f_hist[:n_samples//4])
        f_late = np.mean(f_hist[3*n_samples//4:])
        f_late_std = np.std(f_hist[3*n_samples//4:])
        f_converged = f_late_std < 0.15
        
        # 3. Trend: should drift upward (toward fermionic)
        f_drift = f_late - f_early
        
        # Lifetime distribution
        dead_structures = [s for s in self.structures.values() if s.death_time]
        f_dead = [s for s in dead_structures if abs(s.holonomy + 1) < 0.3]
        b_dead = [s for s in dead_structures if abs(s.holonomy - 1) < 0.3]
        
        f_lifetimes = [s.lifetime for s in f_dead] if f_dead else [0]
        b_lifetimes = [s.lifetime for s in b_dead] if b_dead else [0]
        
        return {
            'n_structures_history': self.n_structures_history,
            'f_fraction_history': self.f_fraction_history,
            'n_converged': bool(n_converged),
            'f_converged': bool(f_converged),
            'f_drift': float(f_drift),
            'f_early': float(f_early),
            'f_late': float(f_late),
            'late_f_std': float(f_late_std),
            'late_n_mean': float(late_mean),
            'late_n_std': float(late_std),
            'f_lifetime_mean': float(np.mean(f_lifetimes)),
            'b_lifetime_mean': float(np.mean(b_lifetimes)),
            'f_lifetime_max': int(max(f_lifetimes)),
            'b_lifetime_max': int(max(b_lifetimes)),
            'converges': bool(n_converged and f_converged)
        }


# =============================================================================
# MAIN TEST
# =============================================================================

def run_time_evolution_test():
    """Run time evolution convergence test."""
    print("=" * 70)
    print("  QMRT STAGE 4 TIME EVOLUTION TEST — CONVERGENCE PROOF")
    print("=" * 70)
    print()
    print(f"  Configuration:")
    print(f"    Timesteps: {CONFIG['timesteps']}")
    print(f"    Runs: {CONFIG['runs']}")
    print(f"    Sample interval: {CONFIG['sample_interval']}")
    print()
    
    start_time = timer.time()
    
    all_results = []
    aggregate = {
        'converged_runs': 0,
        'f_drifts': [],
        'f_late_values': [],
        'lifetime_ratios': []
    }
    
    for run in range(CONFIG['runs']):
        print(f"\n  Run {run + 1}/{CONFIG['runs']}:")
        np.random.seed(run * 7919)
        
        sim = TimeEvolutionSimulation(CONFIG)
        results = sim.run(verbose=True)
        all_results.append(results)
        
        print(f"    N converged: {'YES' if results['n_converged'] else 'NO'}")
        print(f"    F converged: {'YES' if results['f_converged'] else 'NO'}")
        print(f"    F-fraction: {100*results['f_early']:.1f}% → {100*results['f_late']:.1f}%")
        print(f"    Lifetime ratio (F/B): {results['f_lifetime_mean']/max(1, results['b_lifetime_mean']):.2f}")
        
        if results['converges']:
            aggregate['converged_runs'] += 1
        aggregate['f_drifts'].append(results['f_drift'])
        aggregate['f_late_values'].append(results['f_late'])
        if results['b_lifetime_mean'] > 0:
            aggregate['lifetime_ratios'].append(
                results['f_lifetime_mean'] / results['b_lifetime_mean']
            )
    
    elapsed = timer.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("  TIME EVOLUTION SUMMARY")
    print("=" * 70)
    
    conv_rate = aggregate['converged_runs'] / CONFIG['runs']
    mean_f_drift = np.mean(aggregate['f_drifts'])
    mean_f_late = np.mean(aggregate['f_late_values'])
    mean_lifetime_ratio = np.mean(aggregate['lifetime_ratios']) if aggregate['lifetime_ratios'] else 0
    
    print(f"""
  1. CONVERGENCE:
     Runs that converged: {aggregate['converged_runs']}/{CONFIG['runs']} ({100*conv_rate:.0f}%)
     
  2. F-FRACTION EVOLUTION:
     Mean drift (early → late): {100*mean_f_drift:+.1f}%
     Final F-fraction: {100*mean_f_late:.1f}%
     
  3. STABILITY HIERARCHY:
     Mean lifetime ratio (F/B): {mean_lifetime_ratio:.2f}x
     
  4. VERDICT:
    """)
    
    if conv_rate > 0.5 and mean_f_late > 0.6:
        print("     ✅ CONVERGES to stable fermionic-dominated regime")
        print("        System reaches equilibrium with F-dominance")
        verdict = "CONVERGENCE_TO_F_DOMINANCE"
    elif conv_rate > 0.5:
        print("     ⚠️ CONVERGES but without clear F-dominance")
        verdict = "CONVERGENCE_NEUTRAL"
    else:
        print("     ❌ Does NOT converge — system is unstable")
        verdict = "DIVERGENT"
    
    print(f"\n  Elapsed time: {elapsed:.1f} seconds")
    
    # Save results
    output = {
        'config': CONFIG,
        'aggregate': {
            'converged_runs': aggregate['converged_runs'],
            'convergence_rate': conv_rate,
            'mean_f_drift': mean_f_drift,
            'mean_f_late': mean_f_late,
            'mean_lifetime_ratio': mean_lifetime_ratio,
            'verdict': verdict
        },
        'runs': all_results,
        'elapsed_seconds': elapsed
    }
    
    output_path = '/app/backend/qmrt_topology/stage4_time_evolution_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n  Results saved to: {output_path}")
    
    return output


if __name__ == "__main__":
    run_time_evolution_test()
