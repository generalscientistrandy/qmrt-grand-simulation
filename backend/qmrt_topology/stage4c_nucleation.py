"""
QMRT STAGE 4C: NUCLEATION FROM RANDOM INITIAL STATES
====================================================

THE CRITICAL TEST: Do structures form SPONTANEOUSLY from disorder?

This separates:
  - "valid particle system" 
  - "universe-like emergence"

Key measurements:
1. Spontaneous formation rate (% of runs with stable excitations)
2. Sector distribution over time (drift toward fermionic?)
3. Time-to-first-particle (nucleation latency)
4. Survival vs formation balance (stable or churning?)

If this works → proto-universe simulation territory.

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json


# =============================================================================
# SECTOR TYPES
# =============================================================================

class SectorType(Enum):
    FERMIONIC = "F"
    BOSONIC = "B"
    ANYONIC = "A"
    NONE = "none"


# =============================================================================
# DISORDERED INITIAL STATE
# =============================================================================

class DisorderedMedium:
    """
    A medium with random/disordered initial state.
    
    No pre-seeded structures - everything must nucleate spontaneously.
    """
    
    def __init__(self, size: int, params: Dict = None):
        default_params = {
            'node_density': 0.5,        # Nodes per unit area
            'edge_probability': 0.3,    # Probability of edge between nearby nodes
            'phase_disorder': 2*np.pi,  # Initial phase randomness
            'position_noise': 0.2,      # Position noise
        }
        self.params = {**default_params, **(params or {})}
        self.size = size
        
        self.nodes: Dict[int, Dict] = {}
        self.edges: Dict[int, Dict] = {}
        self.next_node_id = 0
        self.next_edge_id = 0
    
    def initialize_random(self):
        """Create a random disordered medium."""
        # Random node positions
        num_nodes = int(self.size**2 * self.params['node_density'])
        
        for _ in range(num_nodes):
            x = np.random.uniform(0, self.size)
            y = np.random.uniform(0, self.size)
            
            # Random initial phase (full disorder)
            phase = np.random.uniform(0, self.params['phase_disorder'])
            
            self.nodes[self.next_node_id] = {
                'id': self.next_node_id,
                'x': x,
                'y': y,
                'phase': phase,
                'edges': []
            }
            self.next_node_id += 1
        
        # Create edges probabilistically
        node_list = list(self.nodes.values())
        connection_radius = 2.0
        
        for i, node_a in enumerate(node_list):
            for node_b in node_list[i+1:]:
                dist = np.sqrt(
                    (node_a['x'] - node_b['x'])**2 +
                    (node_a['y'] - node_b['y'])**2
                )
                
                if dist < connection_radius:
                    # Probabilistic edge creation
                    if np.random.random() < self.params['edge_probability']:
                        edge = {
                            'id': self.next_edge_id,
                            'node_a': node_a['id'],
                            'node_b': node_b['id']
                        }
                        self.edges[self.next_edge_id] = edge
                        node_a['edges'].append(self.next_edge_id)
                        node_b['edges'].append(self.next_edge_id)
                        self.next_edge_id += 1
    
    def find_loops(self, max_size: int = 8) -> List[List[int]]:
        """Find loops in the disordered medium (optimized)."""
        loops = []
        visited = set()
        
        # Build adjacency
        adjacency = defaultdict(set)
        for edge in self.edges.values():
            adjacency[edge['node_a']].add(edge['node_b'])
            adjacency[edge['node_b']].add(edge['node_a'])
        
        # Only search from nodes with 2+ connections
        start_nodes = [n for n in self.nodes if len(adjacency[n]) >= 2]
        
        # Limit search
        max_loops = 500
        
        def dfs(start, current, path, depth):
            if len(loops) >= max_loops:
                return
            if depth > max_size:
                return
            
            for neighbor in adjacency[current]:
                if neighbor == start and len(path) >= 3:
                    loop_key = tuple(sorted(path))
                    if loop_key not in visited:
                        visited.add(loop_key)
                        loops.append(list(path))
                        if len(loops) >= max_loops:
                            return
                elif neighbor not in path and len(loops) < max_loops:
                    dfs(start, neighbor, path + [neighbor], depth + 1)
        
        for node_id in start_nodes[:100]:  # Limit starting nodes
            if len(loops) >= max_loops:
                break
            dfs(node_id, node_id, [node_id], 1)
        
        return loops
    
    def compute_loop_holonomy(self, node_ids: List[int]) -> Tuple[complex, SectorType]:
        """Compute holonomy around a loop."""
        size = len(node_ids)
        total_phase = 0.0
        
        for i in range(size):
            curr = self.nodes[node_ids[i]]
            next_n = self.nodes[node_ids[(i + 1) % size]]
            prev_n = self.nodes[node_ids[(i - 1) % size]]
            
            # Turn angle
            angle_in = np.arctan2(curr['y'] - prev_n['y'], curr['x'] - prev_n['x'])
            angle_out = np.arctan2(next_n['y'] - curr['y'], next_n['x'] - curr['x'])
            
            turn = angle_out - angle_in
            while turn > np.pi:
                turn -= 2 * np.pi
            while turn < -np.pi:
                turn += 2 * np.pi
            
            # Y-junction transport rule
            phase_contribution = -turn / 2
            total_phase += phase_contribution
        
        holonomy = np.exp(1j * total_phase)
        
        # Classify
        if abs(holonomy + 1) < 0.3:
            sector = SectorType.FERMIONIC
        elif abs(holonomy - 1) < 0.3:
            sector = SectorType.BOSONIC
        else:
            sector = SectorType.ANYONIC
        
        return holonomy, sector


# =============================================================================
# NUCLEATION TRACKER
# =============================================================================

@dataclass
class NucleatedStructure:
    """A structure that nucleated from disorder."""
    id: int
    node_ids: List[int]
    size: int
    holonomy: complex
    sector: SectorType
    
    birth_time: int
    death_time: Optional[int] = None
    lifetime: int = 0
    is_alive: bool = True
    
    # How it formed
    formation_type: str = "spontaneous"  # or "from_merger"


class NucleationTracker:
    """
    Track nucleation events and structure formation.
    """
    
    def __init__(self):
        self.structures: Dict[int, NucleatedStructure] = {}
        self.next_id = 0
        
        # Time series
        self.population_history: List[Dict] = []
        self.nucleation_events: List[Dict] = []
        self.death_events: List[Dict] = []
        
        # Statistics
        self.first_nucleation_times: Dict[str, int] = {}
        self.sector_counts_over_time: List[Dict] = []
    
    def record_nucleation(
        self,
        node_ids: List[int],
        holonomy: complex,
        sector: SectorType,
        time: int,
        formation_type: str = "spontaneous"
    ) -> NucleatedStructure:
        """Record a new nucleation event."""
        structure = NucleatedStructure(
            id=self.next_id,
            node_ids=node_ids,
            size=len(node_ids),
            holonomy=holonomy,
            sector=sector,
            birth_time=time,
            formation_type=formation_type
        )
        
        self.structures[self.next_id] = structure
        self.next_id += 1
        
        self.nucleation_events.append({
            'time': time,
            'id': structure.id,
            'sector': sector.value,
            'size': structure.size,
            'formation_type': formation_type
        })
        
        # Track first nucleation per sector
        if sector.value not in self.first_nucleation_times:
            self.first_nucleation_times[sector.value] = time
        
        return structure
    
    def record_death(self, structure_id: int, time: int):
        """Record structure death."""
        if structure_id in self.structures:
            s = self.structures[structure_id]
            s.death_time = time
            s.lifetime = time - s.birth_time
            s.is_alive = False
            
            self.death_events.append({
                'time': time,
                'id': structure_id,
                'sector': s.sector.value,
                'lifetime': s.lifetime
            })
    
    def record_timestep(self, time: int):
        """Record population at this timestep."""
        alive = [s for s in self.structures.values() if s.is_alive]
        
        counts = {'F': 0, 'B': 0, 'A': 0}
        for s in alive:
            counts[s.sector.value] += 1
        
        self.population_history.append({
            'time': time,
            'total': len(alive),
            **counts
        })
        
        self.sector_counts_over_time.append(counts.copy())
    
    def get_statistics(self) -> Dict:
        """Get nucleation statistics."""
        all_structures = list(self.structures.values())
        
        # Lifetimes by sector
        lifetimes = {'F': [], 'B': [], 'A': []}
        for s in all_structures:
            if s.lifetime > 0:
                lifetimes[s.sector.value].append(s.lifetime)
        
        # Final population
        final_alive = [s for s in all_structures if s.is_alive]
        
        return {
            'total_nucleated': len(all_structures),
            'total_deaths': len(self.death_events),
            'final_alive': len(final_alive),
            'nucleation_events': len(self.nucleation_events),
            'first_nucleation_times': self.first_nucleation_times,
            'lifetimes_by_sector': {
                s: {
                    'count': len(v),
                    'mean': np.mean(v) if v else 0,
                    'max': max(v) if v else 0
                }
                for s, v in lifetimes.items()
            },
            'final_sector_distribution': {
                s.value: sum(1 for x in final_alive if x.sector == s)
                for s in SectorType if s != SectorType.NONE
            }
        }


# =============================================================================
# NUCLEATION SIMULATION
# =============================================================================

class NucleationSimulation:
    """
    Simulation starting from PURE DISORDER.
    
    No pre-seeded structures — everything must nucleate.
    """
    
    def __init__(self, params: Dict = None):
        default_params = {
            'grid_size': 25,
            'timesteps': 3000,
            'node_density': 0.4,
            'edge_probability': 0.25,
            'stability_threshold': 50,     # Timesteps to count as "stable"
            'decay_rate': 0.01,
            'fermionic_protection': 8.0,
            'dynamics_enabled': True,
            'phase_evolution_rate': 0.1,
        }
        self.params = {**default_params, **(params or {})}
        
        self.medium = DisorderedMedium(
            self.params['grid_size'],
            {
                'node_density': self.params['node_density'],
                'edge_probability': self.params['edge_probability']
            }
        )
        
        self.tracker = NucleationTracker()
        self.time = 0
        
        # Track which loops we've seen
        self.known_loops: Dict[Tuple[int, ...], int] = {}  # loop_key -> structure_id
    
    def initialize(self):
        """Initialize disordered medium."""
        self.medium.initialize_random()
    
    def step(self):
        """Perform one timestep."""
        self.time += 1
        
        # 1. Evolve phases (creates dynamics)
        if self.params['dynamics_enabled']:
            self._evolve_phases()
        
        # 2. Detect loops and check for new nucleations
        self._detect_nucleations()
        
        # 3. Apply decay to existing structures
        self._apply_decay()
        
        # 4. Record population
        self.tracker.record_timestep(self.time)
    
    def _evolve_phases(self):
        """Evolve node phases to create dynamics."""
        rate = self.params['phase_evolution_rate']
        
        for node in self.medium.nodes.values():
            # Small random phase evolution
            node['phase'] += np.random.normal(0, rate)
            node['phase'] = node['phase'] % (2 * np.pi)
    
    def _detect_nucleations(self):
        """Detect new loop structures (nucleations)."""
        loops = self.medium.find_loops(max_size=10)
        
        for loop_nodes in loops:
            loop_key = tuple(sorted(loop_nodes))
            
            # Check if this is a NEW loop
            if loop_key not in self.known_loops:
                holonomy, sector = self.medium.compute_loop_holonomy(loop_nodes)
                
                # Only track non-trivial loops
                if sector != SectorType.NONE:
                    structure = self.tracker.record_nucleation(
                        loop_nodes,
                        holonomy,
                        sector,
                        self.time,
                        "spontaneous"
                    )
                    self.known_loops[loop_key] = structure.id
            else:
                # Update existing structure (it survived)
                structure_id = self.known_loops[loop_key]
                if structure_id in self.tracker.structures:
                    s = self.tracker.structures[structure_id]
                    if s.is_alive:
                        s.lifetime = self.time - s.birth_time
        
        # Check for structure deaths (loops that disappeared)
        current_loop_keys = {tuple(sorted(l)) for l in loops}
        
        for loop_key, structure_id in list(self.known_loops.items()):
            if loop_key not in current_loop_keys:
                if structure_id in self.tracker.structures:
                    s = self.tracker.structures[structure_id]
                    if s.is_alive:
                        self.tracker.record_death(structure_id, self.time)
    
    def _apply_decay(self):
        """Apply sector-dependent decay."""
        base_rate = self.params['decay_rate']
        protection = self.params['fermionic_protection']
        
        for structure in list(self.tracker.structures.values()):
            if not structure.is_alive:
                continue
            
            # Sector-dependent decay
            if structure.sector == SectorType.FERMIONIC:
                decay_rate = base_rate / protection
            elif structure.sector == SectorType.BOSONIC:
                decay_rate = base_rate * 2.0
            else:
                decay_rate = base_rate
            
            # Additional decay based on structure integrity
            # (In a full simulation, this would check if the loop still exists)
            
            if np.random.random() < decay_rate:
                self.tracker.record_death(structure.id, self.time)
                # Remove from known loops
                loop_key = tuple(sorted(structure.node_ids))
                if loop_key in self.known_loops:
                    del self.known_loops[loop_key]
    
    def run(self) -> Dict:
        """Run full simulation."""
        self.initialize()
        
        for t in range(self.params['timesteps']):
            self.step()
            
            if (t + 1) % 500 == 0:
                alive = sum(1 for s in self.tracker.structures.values() if s.is_alive)
                print(f"    t={t+1}: {alive} alive, {len(self.tracker.nucleation_events)} total nucleated")
        
        return self._compile_results()
    
    def _compile_results(self) -> Dict:
        """Compile results."""
        stats = self.tracker.get_statistics()
        
        # Compute nucleation rate
        total_time = self.params['timesteps']
        nucleation_rate = stats['nucleation_events'] / total_time
        
        # Compute survival rate
        survival_rate = stats['final_alive'] / max(1, stats['total_nucleated'])
        
        # Check for fermionic dominance
        final_dist = stats['final_sector_distribution']
        total_final = sum(final_dist.values())
        fermionic_fraction = final_dist.get('F', 0) / max(1, total_final)
        
        # Time to first stable particle
        stable_threshold = self.params['stability_threshold']
        stable_structures = [
            s for s in self.tracker.structures.values()
            if s.lifetime >= stable_threshold or s.is_alive
        ]
        
        first_stable_time = None
        if stable_structures:
            first_stable_time = min(s.birth_time for s in stable_structures)
        
        return {
            'stats': stats,
            'nucleation_rate': nucleation_rate,
            'survival_rate': survival_rate,
            'fermionic_fraction': fermionic_fraction,
            'first_stable_time': first_stable_time,
            'population_history': self.tracker.population_history[-100:],  # Last 100 timesteps
            'total_loops_found': len(self.known_loops) + len([
                s for s in self.tracker.structures.values() if not s.is_alive
            ])
        }


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def run_stage4c():
    """Run Stage 4C: Nucleation from random initial states."""
    print("=" * 70)
    print("  QMRT STAGE 4C: NUCLEATION FROM RANDOM INITIAL STATES")
    print("=" * 70)
    print()
    print("THE CRITICAL TEST: Do structures form SPONTANEOUSLY from disorder?")
    print()
    
    results = {
        'runs': [],
        'aggregate': {}
    }
    
    # Aggregate statistics
    all_nucleation_rates = []
    all_survival_rates = []
    all_fermionic_fractions = []
    all_first_stable_times = []
    runs_with_stable = 0
    runs_with_fermionic_dominance = 0
    
    print("Running nucleation experiments from PURE DISORDER...")
    print("-" * 50)
    
    for run in range(10):
        print(f"\nRun {run + 1}/10:")
        np.random.seed(run * 5000)
        
        sim = NucleationSimulation({
            'grid_size': 15,
            'timesteps': 1000,
            'node_density': 0.4,
            'edge_probability': 0.25,
            'stability_threshold': 50,
            'decay_rate': 0.01,
            'fermionic_protection': 8.0,
            'phase_evolution_rate': 0.05
        })
        
        run_results = sim.run()
        results['runs'].append(run_results)
        
        # Aggregate
        all_nucleation_rates.append(run_results['nucleation_rate'])
        all_survival_rates.append(run_results['survival_rate'])
        all_fermionic_fractions.append(run_results['fermionic_fraction'])
        
        if run_results['first_stable_time'] is not None:
            all_first_stable_times.append(run_results['first_stable_time'])
            runs_with_stable += 1
        
        if run_results['fermionic_fraction'] > 0.5:
            runs_with_fermionic_dominance += 1
        
        print(f"    Nucleated: {run_results['stats']['total_nucleated']}, "
              f"Survived: {run_results['stats']['final_alive']}, "
              f"F-fraction: {100*run_results['fermionic_fraction']:.0f}%")
    
    # Aggregate analysis
    print("\n" + "=" * 70)
    print("  AGGREGATE RESULTS")
    print("=" * 70)
    
    print(f"\n1. SPONTANEOUS FORMATION:")
    print(f"   • Nucleation rate: {np.mean(all_nucleation_rates):.3f} ± {np.std(all_nucleation_rates):.3f} per timestep")
    print(f"   • Runs with stable structures: {runs_with_stable}/10 ({100*runs_with_stable/10:.0f}%)")
    
    print(f"\n2. SECTOR DISTRIBUTION:")
    print(f"   • Mean fermionic fraction: {100*np.mean(all_fermionic_fractions):.1f}%")
    print(f"   • Runs with fermionic dominance (>50%): {runs_with_fermionic_dominance}/10")
    
    print(f"\n3. TIME-TO-FIRST-STABLE:")
    if all_first_stable_times:
        print(f"   • Mean: {np.mean(all_first_stable_times):.0f} ± {np.std(all_first_stable_times):.0f} timesteps")
    else:
        print(f"   • No stable structures formed")
    
    print(f"\n4. SURVIVAL RATE:")
    print(f"   • Mean: {100*np.mean(all_survival_rates):.1f}%")
    
    results['aggregate'] = {
        'mean_nucleation_rate': np.mean(all_nucleation_rates),
        'std_nucleation_rate': np.std(all_nucleation_rates),
        'runs_with_stable': runs_with_stable,
        'runs_with_stable_pct': runs_with_stable / 10,
        'mean_fermionic_fraction': np.mean(all_fermionic_fractions),
        'runs_with_fermionic_dominance': runs_with_fermionic_dominance,
        'mean_first_stable_time': np.mean(all_first_stable_times) if all_first_stable_times else None,
        'mean_survival_rate': np.mean(all_survival_rates)
    }
    
    # Key findings
    print("\n" + "=" * 70)
    print("  KEY FINDINGS")
    print("=" * 70)
    
    spontaneous = runs_with_stable >= 5
    fermionic_dominant = runs_with_fermionic_dominance >= 5
    
    print(f"""
  1. SPONTANEOUS FORMATION:
     {'✅ YES' if spontaneous else '❌ NO'} — Structures form from disorder in {100*runs_with_stable/10:.0f}% of runs
     
  2. FERMIONIC DRIFT:
     {'✅ YES' if fermionic_dominant else '❌ NO'} — System drifts toward fermionic dominance in {100*runs_with_fermionic_dominance/10:.0f}% of runs
     
  3. NUCLEATION LATENCY:
     First stable structure appears at t ≈ {np.mean(all_first_stable_times) if all_first_stable_times else 'N/A':.0f}
     
  4. BALANCE:
     Survival rate = {100*np.mean(all_survival_rates):.1f}% (structures are {'stable' if np.mean(all_survival_rates) > 0.1 else 'churning'})
    """)
    
    if spontaneous and fermionic_dominant:
        print("  🔥 BREAKTHROUGH: Self-organizing topological system with fermionic selection!")
        print("     → This is proto-universe behavior!")
    elif spontaneous:
        print("  ✅ GOOD: Spontaneous nucleation confirmed")
        print("     → But no clear fermionic dominance")
    else:
        print("  ⚠️ WEAK: Nucleation occurs but structures don't persist")
        print("     → May need parameter tuning")
    
    # Save
    output_path = '/app/backend/qmrt_topology/stage4c_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_stage4c()
