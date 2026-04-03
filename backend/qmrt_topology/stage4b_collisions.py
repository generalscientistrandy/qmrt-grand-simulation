"""
QMRT STAGE 4B: COLLISION + COMPOSITE FORMATION
==============================================

Goal: Understand interaction physics and composite stability

Key measurements:
1. Collision outcome matrix (F+F→?, F+B→?, etc.)
2. Composite stability (do merged objects live longer?)
3. Size/energy proxy scaling (larger = more stable?)
4. Post-collision survival curves

This determines whether "particles" are actually robust.

=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json


# =============================================================================
# SECTOR AND OUTCOME TYPES
# =============================================================================

class SectorType(Enum):
    FERMIONIC = "F"
    BOSONIC = "B"
    ANYONIC = "A"


class OutcomeType(Enum):
    SCATTER = "scatter"
    MERGE = "merge"
    SPLIT = "split"
    ANNIHILATE = "annihilate"
    ASYMMETRIC = "asymmetric"  # One survives


# =============================================================================
# COLLISION MATRIX TRACKER
# =============================================================================

class CollisionMatrix:
    """
    Track collision outcomes by sector pair.
    
    Builds a matrix: (SectorA, SectorB) → {outcome: probability}
    """
    
    def __init__(self):
        # outcomes[(sector_a, sector_b)][outcome] = count
        self.outcomes: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.total_by_pair: Dict[Tuple[str, str], int] = defaultdict(int)
    
    def record(self, sector_a: SectorType, sector_b: SectorType, outcome: OutcomeType):
        """Record a collision outcome."""
        # Normalize order (F, B) same as (B, F)
        pair = tuple(sorted([sector_a.value, sector_b.value]))
        self.outcomes[pair][outcome.value] += 1
        self.total_by_pair[pair] += 1
    
    def get_probabilities(self) -> Dict:
        """Get outcome probabilities for each pair."""
        result = {}
        for pair, outcomes in self.outcomes.items():
            total = self.total_by_pair[pair]
            result[f"{pair[0]}+{pair[1]}"] = {
                outcome: count / total
                for outcome, count in outcomes.items()
            }
            result[f"{pair[0]}+{pair[1]}"]['total'] = total
        return result
    
    def print_matrix(self):
        """Print collision matrix."""
        print("\nCOLLISION OUTCOME MATRIX:")
        print("-" * 60)
        print(f"{'Pair':<10} | {'Scatter':>8} | {'Merge':>8} | {'Annihil':>8} | {'Asymm':>8} | {'Total':>6}")
        print("-" * 60)
        
        for pair in [('A', 'A'), ('A', 'B'), ('A', 'F'), ('B', 'B'), ('B', 'F'), ('F', 'F')]:
            key = f"{pair[0]}+{pair[1]}"
            probs = self.get_probabilities().get(key, {})
            total = probs.get('total', 0)
            
            scatter = probs.get('scatter', 0)
            merge = probs.get('merge', 0)
            annihil = probs.get('annihilate', 0)
            asymm = probs.get('asymmetric', 0)
            
            print(f"{key:<10} | {100*scatter:>7.1f}% | {100*merge:>7.1f}% | "
                  f"{100*annihil:>7.1f}% | {100*asymm:>7.1f}% | {total:>6}")


# =============================================================================
# COMPOSITE TRACKER
# =============================================================================

@dataclass
class Composite:
    """A merged composite object."""
    id: int
    parent_ids: List[int]
    parent_sectors: List[SectorType]
    
    # Properties
    sector: SectorType
    holonomy_phase: float
    size: int  # Combined size
    
    # Dynamics
    birth_time: int
    death_time: Optional[int] = None
    lifetime: int = 0
    is_alive: bool = True
    
    # Tracking
    collision_count: int = 0
    survived_collisions: int = 0


class CompositeTracker:
    """
    Track composite formation and stability.
    """
    
    def __init__(self):
        self.composites: Dict[int, Composite] = {}
        self.composite_lifetimes: List[int] = []
        self.non_composite_lifetimes: List[int] = []
        
        # Size vs stability data
        self.size_lifetime_data: List[Tuple[int, int]] = []
    
    def create_composite(
        self,
        composite_id: int,
        parent_ids: List[int],
        parent_sectors: List[SectorType],
        parent_sizes: List[int],
        parent_phases: List[float],
        birth_time: int
    ) -> Composite:
        """Create a composite from merged parents."""
        # Combined size
        combined_size = sum(parent_sizes)
        
        # Combined phase (determines new sector)
        combined_phase = sum(parent_phases) / len(parent_phases)
        
        # Determine new sector
        holonomy = np.exp(1j * combined_phase)
        if abs(holonomy + 1) < 0.3:
            new_sector = SectorType.FERMIONIC
        elif abs(holonomy - 1) < 0.3:
            new_sector = SectorType.BOSONIC
        else:
            new_sector = SectorType.ANYONIC
        
        composite = Composite(
            id=composite_id,
            parent_ids=parent_ids,
            parent_sectors=parent_sectors,
            sector=new_sector,
            holonomy_phase=combined_phase,
            size=combined_size,
            birth_time=birth_time
        )
        
        self.composites[composite_id] = composite
        return composite
    
    def record_death(self, composite_id: int, death_time: int):
        """Record composite death."""
        if composite_id in self.composites:
            comp = self.composites[composite_id]
            comp.death_time = death_time
            comp.lifetime = death_time - comp.birth_time
            comp.is_alive = False
            
            self.composite_lifetimes.append(comp.lifetime)
            self.size_lifetime_data.append((comp.size, comp.lifetime))
    
    def record_non_composite_death(self, lifetime: int, size: int):
        """Record non-composite object death for comparison."""
        self.non_composite_lifetimes.append(lifetime)
        self.size_lifetime_data.append((size, lifetime))
    
    def get_statistics(self) -> Dict:
        """Get composite vs non-composite statistics."""
        return {
            'composite_count': len(self.composites),
            'composite_mean_lifetime': (
                np.mean(self.composite_lifetimes) if self.composite_lifetimes else 0
            ),
            'non_composite_mean_lifetime': (
                np.mean(self.non_composite_lifetimes) if self.non_composite_lifetimes else 0
            ),
            'composite_alive': sum(1 for c in self.composites.values() if c.is_alive),
            'lifetime_ratio': (
                np.mean(self.composite_lifetimes) / max(1, np.mean(self.non_composite_lifetimes))
                if self.composite_lifetimes and self.non_composite_lifetimes else 0
            )
        }


# =============================================================================
# SIZE-STABILITY ANALYZER
# =============================================================================

class SizeStabilityAnalyzer:
    """
    Analyze correlation between size and stability.
    
    Uses size as energy proxy.
    """
    
    def __init__(self):
        self.data: List[Dict] = []
    
    def record(self, size: int, lifetime: int, sector: SectorType, is_composite: bool):
        """Record size-lifetime data point."""
        self.data.append({
            'size': size,
            'lifetime': lifetime,
            'sector': sector.value,
            'is_composite': is_composite
        })
    
    def analyze(self) -> Dict:
        """Analyze size-stability correlation."""
        if not self.data:
            return {'note': 'No data'}
        
        sizes = np.array([d['size'] for d in self.data])
        lifetimes = np.array([d['lifetime'] for d in self.data])
        
        # Correlation
        if len(sizes) > 1 and np.std(sizes) > 0 and np.std(lifetimes) > 0:
            correlation = np.corrcoef(sizes, lifetimes)[0, 1]
        else:
            correlation = 0
        
        # Size bins
        size_bins = {}
        for d in self.data:
            size_bin = (d['size'] // 4) * 4  # Bin by 4
            if size_bin not in size_bins:
                size_bins[size_bin] = []
            size_bins[size_bin].append(d['lifetime'])
        
        binned_stats = {
            f"size_{b}-{b+3}": {
                'count': len(v),
                'mean_lifetime': np.mean(v),
                'std': np.std(v)
            }
            for b, v in sorted(size_bins.items())
        }
        
        return {
            'correlation': correlation,
            'interpretation': (
                'Larger = more stable' if correlation > 0.2 else
                'Larger = less stable' if correlation < -0.2 else
                'No clear correlation'
            ),
            'binned_stats': binned_stats
        }


# =============================================================================
# POST-COLLISION SURVIVAL ANALYZER
# =============================================================================

class PostCollisionSurvival:
    """
    Compare isolated lifetime vs collision-exposed lifetime.
    """
    
    def __init__(self):
        self.isolated_lifetimes: Dict[str, List[int]] = defaultdict(list)
        self.exposed_lifetimes: Dict[str, List[int]] = defaultdict(list)
        self.survival_after_collision: Dict[str, List[int]] = defaultdict(list)
    
    def record_isolated(self, sector: SectorType, lifetime: int):
        """Record lifetime of isolated (no collision) object."""
        self.isolated_lifetimes[sector.value].append(lifetime)
    
    def record_exposed(self, sector: SectorType, lifetime: int, collision_count: int):
        """Record lifetime of collision-exposed object."""
        if collision_count > 0:
            self.exposed_lifetimes[sector.value].append(lifetime)
    
    def record_post_collision_survival(self, sector: SectorType, time_after: int):
        """Record survival time after a collision."""
        self.survival_after_collision[sector.value].append(time_after)
    
    def analyze(self) -> Dict:
        """Analyze survival patterns."""
        result = {}
        
        for sector in ['F', 'B', 'A']:
            isolated = self.isolated_lifetimes[sector]
            exposed = self.exposed_lifetimes[sector]
            
            result[sector] = {
                'isolated_mean': np.mean(isolated) if isolated else 0,
                'exposed_mean': np.mean(exposed) if exposed else 0,
                'robustness_ratio': (
                    np.mean(exposed) / max(1, np.mean(isolated))
                    if exposed and isolated else 0
                )
            }
        
        return result


# =============================================================================
# COLLISION SIMULATION ENGINE
# =============================================================================

class CollisionSimulation:
    """
    Simulation focused on collision physics and composite formation.
    """
    
    def __init__(self, params: Dict = None):
        default_params = {
            'grid_size': 15,
            'num_objects': 60,
            'timesteps': 2000,
            'collision_radius': 1.5,
            'movement_speed': 0.2,
            'base_decay_rate': 0.002,
            'fermionic_protection': 10.0,
            'merge_probability': 0.25,
            'annihilate_probability': 0.1,
        }
        self.params = {**default_params, **(params or {})}
        
        # Objects
        self.objects: Dict[int, Dict] = {}
        self.next_id = 0
        self.time = 0
        
        # Trackers
        self.collision_matrix = CollisionMatrix()
        self.composite_tracker = CompositeTracker()
        self.size_analyzer = SizeStabilityAnalyzer()
        self.survival_analyzer = PostCollisionSurvival()
        
        # Logs
        self.all_lifetimes: Dict[str, List[int]] = defaultdict(list)
    
    def create_object(
        self,
        x: float,
        y: float,
        sector: SectorType = None,
        size: int = None,
        is_composite: bool = False,
        parent_ids: List[int] = None
    ) -> Dict:
        """Create a new object."""
        if sector is None:
            r = np.random.random()
            if r < 0.4:
                sector = SectorType.FERMIONIC
            elif r < 0.7:
                sector = SectorType.BOSONIC
            else:
                sector = SectorType.ANYONIC
        
        if size is None:
            size = np.random.choice([4, 6, 8, 10])
        
        # Phase based on sector
        if sector == SectorType.FERMIONIC:
            phase = np.pi + np.random.normal(0, 0.1)
        elif sector == SectorType.BOSONIC:
            phase = np.random.normal(0, 0.1)
        else:
            phase = np.random.uniform(0.5, 2.5)
        
        obj = {
            'id': self.next_id,
            'x': x,
            'y': y,
            'sector': sector,
            'size': size,
            'phase': phase,
            'birth_time': self.time,
            'death_time': None,
            'is_alive': True,
            'collision_count': 0,
            'survived_collisions': 0,
            'is_composite': is_composite,
            'parent_ids': parent_ids or []
        }
        
        self.objects[self.next_id] = obj
        self.next_id += 1
        
        return obj
    
    def initialize(self):
        """Initialize with random objects."""
        grid_size = self.params['grid_size']
        n = self.params['num_objects']
        
        for _ in range(n):
            x = np.random.uniform(0, grid_size)
            y = np.random.uniform(0, grid_size)
            self.create_object(x, y)
    
    def step(self):
        """Perform one timestep."""
        self.time += 1
        grid_size = self.params['grid_size']
        
        # 1. Move objects
        for obj in self.objects.values():
            if not obj['is_alive']:
                continue
            
            speed = self.params['movement_speed']
            obj['x'] = (obj['x'] + np.random.normal(0, speed)) % grid_size
            obj['y'] = (obj['y'] + np.random.normal(0, speed)) % grid_size
        
        # 2. Detect and resolve collisions
        alive = [o for o in self.objects.values() if o['is_alive']]
        
        for i, obj_a in enumerate(alive):
            for obj_b in alive[i+1:]:
                dist = np.sqrt(
                    (obj_a['x'] - obj_b['x'])**2 + 
                    (obj_a['y'] - obj_b['y'])**2
                )
                
                if dist < self.params['collision_radius']:
                    self._resolve_collision(obj_a, obj_b)
        
        # 3. Apply decay
        self._apply_decay()
    
    def _resolve_collision(self, obj_a: Dict, obj_b: Dict):
        """Resolve collision between two objects."""
        if not obj_a['is_alive'] or not obj_b['is_alive']:
            return
        
        obj_a['collision_count'] += 1
        obj_b['collision_count'] += 1
        
        sector_a = obj_a['sector']
        sector_b = obj_b['sector']
        
        r = np.random.random()
        
        # Sector-dependent outcome probabilities
        merge_prob = self.params['merge_probability']
        annihil_prob = self.params['annihilate_probability']
        
        # F+F tends to scatter (both protected)
        # F+B tends to have F survive
        # B+B more likely to annihilate
        
        if sector_a == SectorType.FERMIONIC and sector_b == SectorType.FERMIONIC:
            merge_prob *= 0.5  # Less likely to merge
            annihil_prob *= 0.2  # Much less likely to annihilate
        elif sector_a == SectorType.BOSONIC and sector_b == SectorType.BOSONIC:
            annihil_prob *= 2.0  # More likely to annihilate
        
        if r < annihil_prob:
            # Annihilate
            outcome = OutcomeType.ANNIHILATE
            self._kill_object(obj_a)
            self._kill_object(obj_b)
            
        elif r < annihil_prob + merge_prob:
            # Merge into composite
            outcome = OutcomeType.MERGE
            
            new_size = obj_a['size'] + obj_b['size']
            new_phase = (obj_a['phase'] + obj_b['phase']) / 2
            new_holonomy = np.exp(1j * new_phase)
            
            if abs(new_holonomy + 1) < 0.3:
                new_sector = SectorType.FERMIONIC
            elif abs(new_holonomy - 1) < 0.3:
                new_sector = SectorType.BOSONIC
            else:
                new_sector = SectorType.ANYONIC
            
            # Kill parents
            self._kill_object(obj_a)
            self._kill_object(obj_b)
            
            # Create composite
            composite = self.create_object(
                (obj_a['x'] + obj_b['x']) / 2,
                (obj_a['y'] + obj_b['y']) / 2,
                sector=new_sector,
                size=new_size,
                is_composite=True,
                parent_ids=[obj_a['id'], obj_b['id']]
            )
            
            # Track in composite tracker
            self.composite_tracker.create_composite(
                composite['id'],
                [obj_a['id'], obj_b['id']],
                [sector_a, sector_b],
                [obj_a['size'], obj_b['size']],
                [obj_a['phase'], obj_b['phase']],
                self.time
            )
            
        elif r < annihil_prob + merge_prob + 0.15:
            # Asymmetric - one survives
            outcome = OutcomeType.ASYMMETRIC
            
            # Fermions more likely to survive
            if sector_a == SectorType.FERMIONIC and sector_b != SectorType.FERMIONIC:
                self._kill_object(obj_b)
                obj_a['survived_collisions'] += 1
            elif sector_b == SectorType.FERMIONIC and sector_a != SectorType.FERMIONIC:
                self._kill_object(obj_a)
                obj_b['survived_collisions'] += 1
            else:
                if np.random.random() < 0.5:
                    self._kill_object(obj_b)
                    obj_a['survived_collisions'] += 1
                else:
                    self._kill_object(obj_a)
                    obj_b['survived_collisions'] += 1
        else:
            # Scatter
            outcome = OutcomeType.SCATTER
            
            dx = obj_b['x'] - obj_a['x']
            dy = obj_b['y'] - obj_a['y']
            norm = np.sqrt(dx**2 + dy**2) + 0.01
            
            obj_a['x'] -= 0.3 * dx / norm
            obj_a['y'] -= 0.3 * dy / norm
            obj_b['x'] += 0.3 * dx / norm
            obj_b['y'] += 0.3 * dy / norm
            
            obj_a['survived_collisions'] += 1
            obj_b['survived_collisions'] += 1
        
        # Record in collision matrix
        self.collision_matrix.record(sector_a, sector_b, outcome)
    
    def _apply_decay(self):
        """Apply sector-dependent decay."""
        base_rate = self.params['base_decay_rate']
        protection = self.params['fermionic_protection']
        
        for obj in list(self.objects.values()):
            if not obj['is_alive']:
                continue
            
            sector = obj['sector']
            
            # Sector-dependent decay
            if sector == SectorType.FERMIONIC:
                decay_rate = base_rate / protection
            elif sector == SectorType.BOSONIC:
                decay_rate = base_rate * 2.0
            else:
                decay_rate = base_rate
            
            # Size factor (larger = slightly more stable)
            size_factor = 1.0 - 0.02 * (obj['size'] - 6)
            decay_rate *= max(0.5, size_factor)
            
            if np.random.random() < decay_rate:
                self._kill_object(obj)
    
    def _kill_object(self, obj: Dict):
        """Kill an object and record statistics."""
        if not obj['is_alive']:
            return
        
        obj['is_alive'] = False
        obj['death_time'] = self.time
        lifetime = self.time - obj['birth_time']
        
        sector = obj['sector']
        self.all_lifetimes[sector.value].append(lifetime)
        
        # Record in analyzers
        self.size_analyzer.record(
            obj['size'], lifetime, sector, obj['is_composite']
        )
        
        if obj['collision_count'] == 0:
            self.survival_analyzer.record_isolated(sector, lifetime)
        else:
            self.survival_analyzer.record_exposed(sector, lifetime, obj['collision_count'])
        
        # If composite, record in composite tracker
        if obj['is_composite'] and obj['id'] in self.composite_tracker.composites:
            self.composite_tracker.record_death(obj['id'], self.time)
        elif not obj['is_composite']:
            self.composite_tracker.record_non_composite_death(lifetime, obj['size'])
    
    def run(self) -> Dict:
        """Run full simulation."""
        self.initialize()
        
        for t in range(self.params['timesteps']):
            self.step()
            
            if (t + 1) % 500 == 0:
                alive = sum(1 for o in self.objects.values() if o['is_alive'])
                print(f"    t={t+1}: {alive} alive")
        
        return self._compile_results()
    
    def _compile_results(self) -> Dict:
        """Compile all results."""
        return {
            'collision_matrix': self.collision_matrix.get_probabilities(),
            'composite_stats': self.composite_tracker.get_statistics(),
            'size_stability': self.size_analyzer.analyze(),
            'survival_analysis': self.survival_analyzer.analyze(),
            'lifetime_by_sector': {
                s: {
                    'mean': np.mean(v) if v else 0,
                    'count': len(v)
                }
                for s, v in self.all_lifetimes.items()
            },
            'final_alive': sum(1 for o in self.objects.values() if o['is_alive'])
        }


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def run_stage4b():
    """Run Stage 4B: Collision + Composite Formation."""
    print("=" * 70)
    print("  QMRT STAGE 4B: COLLISION + COMPOSITE FORMATION")
    print("=" * 70)
    print()
    
    results = {
        'runs': [],
        'aggregate': {}
    }
    
    # Aggregate trackers
    all_collision_probs = defaultdict(lambda: defaultdict(list))
    all_composite_ratios = []
    all_size_correlations = []
    
    print("Running collision simulations...")
    print("-" * 50)
    
    for run in range(5):
        print(f"\nRun {run + 1}/5:")
        np.random.seed(run * 2000)
        
        sim = CollisionSimulation({
            'grid_size': 20,
            'num_objects': 80,
            'timesteps': 2500,
            'collision_radius': 1.3,
            'movement_speed': 0.25,
            'base_decay_rate': 0.002,
            'fermionic_protection': 12.0,
            'merge_probability': 0.20,
            'annihilate_probability': 0.08
        })
        
        run_results = sim.run()
        results['runs'].append(run_results)
        
        # Aggregate collision probabilities
        for pair, probs in run_results['collision_matrix'].items():
            for outcome, prob in probs.items():
                if outcome != 'total':
                    all_collision_probs[pair][outcome].append(prob)
        
        # Composite ratio
        if run_results['composite_stats']['lifetime_ratio'] > 0:
            all_composite_ratios.append(run_results['composite_stats']['lifetime_ratio'])
        
        # Size correlation
        if run_results['size_stability'].get('correlation'):
            all_size_correlations.append(run_results['size_stability']['correlation'])
        
        # Print collision matrix for this run
        sim.collision_matrix.print_matrix()
    
    # Aggregate analysis
    print("\n" + "=" * 70)
    print("  AGGREGATE RESULTS")
    print("=" * 70)
    
    # 1. Average collision matrix
    print("\nAVERAGE COLLISION OUTCOME MATRIX:")
    print("-" * 60)
    print(f"{'Pair':<10} | {'Scatter':>10} | {'Merge':>10} | {'Annihil':>10}")
    print("-" * 60)
    
    avg_collision_probs = {}
    for pair in ['A+A', 'A+B', 'A+F', 'B+B', 'B+F', 'F+F']:
        scatter = np.mean(all_collision_probs[pair].get('scatter', [0]))
        merge = np.mean(all_collision_probs[pair].get('merge', [0]))
        annihil = np.mean(all_collision_probs[pair].get('annihilate', [0]))
        
        print(f"{pair:<10} | {100*scatter:>9.1f}% | {100*merge:>9.1f}% | {100*annihil:>9.1f}%")
        
        avg_collision_probs[pair] = {
            'scatter': scatter,
            'merge': merge,
            'annihilate': annihil
        }
    
    results['aggregate']['collision_matrix'] = avg_collision_probs
    
    # 2. Composite stability
    print("\nCOMPOSITE vs NON-COMPOSITE STABILITY:")
    print("-" * 50)
    if all_composite_ratios:
        mean_ratio = np.mean(all_composite_ratios)
        print(f"  Composite/Non-composite lifetime ratio: {mean_ratio:.2f}x")
        if mean_ratio > 1.2:
            print("  → Composites are MORE stable than components")
        elif mean_ratio < 0.8:
            print("  → Composites are LESS stable than components")
        else:
            print("  → Composites have similar stability to components")
        results['aggregate']['composite_lifetime_ratio'] = mean_ratio
    
    # 3. Size-stability correlation
    print("\nSIZE-STABILITY CORRELATION:")
    print("-" * 50)
    if all_size_correlations:
        mean_corr = np.mean(all_size_correlations)
        print(f"  Size-lifetime correlation: {mean_corr:.3f}")
        if mean_corr > 0.2:
            print("  → Larger objects ARE more stable")
        elif mean_corr < -0.2:
            print("  → Larger objects are LESS stable")
        else:
            print("  → Size has weak effect on stability")
        results['aggregate']['size_correlation'] = mean_corr
    
    # Key findings
    print("\n" + "=" * 70)
    print("  KEY FINDINGS")
    print("=" * 70)
    
    # Check F+F stability
    ff_scatter = avg_collision_probs.get('F+F', {}).get('scatter', 0)
    bb_annihil = avg_collision_probs.get('B+B', {}).get('annihilate', 0)
    
    print(f"""
  1. COLLISION OUTCOMES:
     • F+F scatters {100*ff_scatter:.0f}% of time (protected)
     • B+B annihilates {100*bb_annihil:.0f}% of time (fragile)
     
  2. COMPOSITE STABILITY:
     • Composites live {np.mean(all_composite_ratios) if all_composite_ratios else 0:.1f}x longer than components
     
  3. SIZE EFFECT:
     • Correlation = {np.mean(all_size_correlations) if all_size_correlations else 0:.3f}
    """)
    
    # Check if fermions are collision-robust
    if ff_scatter > 0.7:
        print("  ✅ FERMIONS ARE COLLISION-ROBUST (scatter dominates)")
    
    if bb_annihil > 0.15:
        print("  ✅ BOSONS ARE COLLISION-FRAGILE (higher annihilation)")
    
    # Save
    output_path = '/app/backend/qmrt_topology/stage4b_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_stage4b()
