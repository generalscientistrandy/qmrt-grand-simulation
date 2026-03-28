"""
QMRT: DECISIVE FLUX CONSERVATION TEST
=====================================

PURPOSE: Test NECESSITY, not just behavior.

KEY QUESTION:
  Does flux conservation FORCE degree = 3, or just ALLOW it?

MEASUREMENTS (per user specification):
1. Degree Distribution Evolution - Track over time
2. Flux Residual per Node - R = |Σᵢ Jᵢ|
3. Energy vs Degree Correlation - Do non-3 nodes carry higher energy?
4. Soft vs Hard Constraint - Two versions compared

SUCCESS CRITERIA (very strict):
  - 70-80% nodes → degree 3
  - Stable over time
  - Independent of initialization

FAILURE CRITERIA:
  Even if Y-junctions increase and angles → 120°,
  if degree distribution still mixed → flux conservation is NOT sufficient
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json
from collections import defaultdict


@dataclass
class FluxBranch:
    """A branch carrying signed flux."""
    node1_id: int
    node2_id: int
    flux: float  # Signed quantity
    tension: float = 1.0


@dataclass
class FluxNode:
    """A node in the flux network."""
    id: int
    position: np.ndarray


class DecisiveFluxNetwork:
    """
    Network with flux conservation constraint.
    
    Two modes:
      - SOFT: penalty term E + λ(ΣJ)²
      - HARD: enforce exactly ΣJ = 0 via projection
    """
    
    def __init__(self, constraint_mode: str = 'soft', 
                 domain_size: float = 100.0, seed: int = None):
        """
        Args:
            constraint_mode: 'soft' (penalty) or 'hard' (exact projection)
        """
        if seed is not None:
            np.random.seed(seed)
        
        self.constraint_mode = constraint_mode
        self.domain_size = domain_size
        self.nodes: Dict[int, FluxNode] = {}
        self.branches: List[FluxBranch] = []
        self.next_id = 0
        
        self.time = 0.0
        
        # MEASUREMENT HISTORY (per user requirement)
        self.degree_history: List[Dict] = []      # Track degree dist over time
        self.flux_residual_history: List[Dict] = []  # Track flux violations
        self.energy_degree_correlation: List[Dict] = []  # E vs degree
    
    def add_node(self, position: np.ndarray) -> int:
        node_id = self.next_id
        self.nodes[node_id] = FluxNode(id=node_id, position=np.array(position))
        self.next_id += 1
        return node_id
    
    def add_branch(self, n1: int, n2: int, flux: float, tension: float = 1.0):
        self.branches.append(FluxBranch(n1, n2, flux, tension))
    
    def get_node_degree(self, node_id: int) -> int:
        return sum(1 for b in self.branches 
                   if b.node1_id == node_id or b.node2_id == node_id)
    
    def get_flux_residual(self, node_id: int) -> float:
        """
        R = |Σᵢ Jᵢ| at this node (absolute flux imbalance)
        
        Convention: flux > 0 flows from node1 → node2
        """
        net_flux = 0.0
        for b in self.branches:
            if b.node1_id == node_id:
                net_flux -= b.flux  # Outgoing
            elif b.node2_id == node_id:
                net_flux += b.flux  # Incoming
        return abs(net_flux)
    
    def get_signed_flux(self, node_id: int) -> float:
        """Signed flux residual (for correction)."""
        net_flux = 0.0
        for b in self.branches:
            if b.node1_id == node_id:
                net_flux -= b.flux
            elif b.node2_id == node_id:
                net_flux += b.flux
        return net_flux
    
    def create_random_network(self, n_nodes: int = 20, connectivity: float = 0.25):
        """
        Create random network with mixed degrees.
        
        Goal: Start with mixed (1-7) degrees, see if flux constraint forces → 3
        """
        # Create nodes
        for _ in range(n_nodes):
            pos = np.random.uniform(10, self.domain_size - 10, 2)
            self.add_node(pos)
        
        node_ids = list(self.nodes.keys())
        n = len(node_ids)
        
        # Create edges randomly with given connectivity probability
        for i in range(n):
            for j in range(i + 1, n):
                if np.random.random() < connectivity:
                    # Random initial flux
                    flux = np.random.uniform(-1.5, 1.5)
                    self.add_branch(node_ids[i], node_ids[j], flux)
    
    def compute_node_energy(self, node_id: int, flux_penalty: float) -> float:
        """
        Energy contribution from a single node.
        
        E_node = Σ (T_i × L_i / 2) + λ × R²
        
        (Each branch contributes half to each endpoint)
        """
        energy = 0.0
        
        # Branch energy (half per endpoint)
        for b in self.branches:
            if b.node1_id == node_id:
                other = self.nodes[b.node2_id].position
            elif b.node2_id == node_id:
                other = self.nodes[b.node1_id].position
            else:
                continue
            
            pos = self.nodes[node_id].position
            length = np.linalg.norm(other - pos)
            energy += 0.5 * b.tension * length
        
        # Flux conservation penalty
        residual = self.get_flux_residual(node_id)
        energy += flux_penalty * residual**2
        
        return energy
    
    def compute_total_energy(self, flux_penalty: float = 10.0) -> float:
        """Total network energy."""
        energy = 0.0
        
        # Branch energy
        for b in self.branches:
            p1 = self.nodes[b.node1_id].position
            p2 = self.nodes[b.node2_id].position
            length = np.linalg.norm(p2 - p1)
            energy += b.tension * length
        
        # Flux penalty
        for node_id in self.nodes:
            residual = self.get_flux_residual(node_id)
            energy += flux_penalty * residual**2
        
        return energy
    
    def enforce_hard_flux_conservation(self):
        """
        HARD CONSTRAINT: Project fluxes to satisfy ΣJ = 0 exactly at each node.
        
        Method: Iteratively adjust fluxes to zero out residuals.
        """
        max_iterations = 100
        tolerance = 1e-10
        
        for _ in range(max_iterations):
            max_residual = 0.0
            
            for node_id in self.nodes:
                signed_residual = self.get_signed_flux(node_id)
                max_residual = max(max_residual, abs(signed_residual))
                
                if abs(signed_residual) < tolerance:
                    continue
                
                # Get branches connected to this node
                connected_branches = []
                for b in self.branches:
                    if b.node1_id == node_id or b.node2_id == node_id:
                        connected_branches.append(b)
                
                if not connected_branches:
                    continue
                
                # Distribute correction equally among connected branches
                correction = signed_residual / len(connected_branches)
                
                for b in connected_branches:
                    if b.node1_id == node_id:
                        b.flux -= correction  # Was outgoing
                    else:
                        b.flux += correction  # Was incoming
            
            if max_residual < tolerance:
                break
    
    def evolve_step(self, dt: float = 0.1, flux_penalty: float = 10.0):
        """
        Evolve network by one timestep.
        
        SOFT mode: Uses penalty in energy
        HARD mode: Projects to exact conservation after each step
        """
        # 1. Move nodes to reduce force imbalance
        for node_id, node in self.nodes.items():
            force = np.zeros(2)
            
            for b in self.branches:
                if b.node1_id == node_id:
                    other_pos = self.nodes[b.node2_id].position
                elif b.node2_id == node_id:
                    other_pos = self.nodes[b.node1_id].position
                else:
                    continue
                
                direction = other_pos - node.position
                dist = np.linalg.norm(direction) + 1e-10
                unit_dir = direction / dist
                force += b.tension * unit_dir
            
            # Damped motion
            damping = 10.0
            displacement = force * dt / damping
            max_disp = 1.0
            if np.linalg.norm(displacement) > max_disp:
                displacement *= max_disp / np.linalg.norm(displacement)
            
            node.position += displacement
            node.position = np.clip(node.position, 5, self.domain_size - 5)
        
        # 2. Adjust fluxes based on constraint mode
        if self.constraint_mode == 'soft':
            # SOFT: Gradient descent on flux penalty
            for b in self.branches:
                violation_1 = self.get_signed_flux(b.node1_id)
                violation_2 = self.get_signed_flux(b.node2_id)
                
                # Move flux to reduce both violations (with damping)
                flux_correction = -0.1 * (violation_1 - violation_2)
                b.flux += flux_correction * dt
                
                # STABILITY: Clamp flux to prevent explosion
                b.flux = np.clip(b.flux, -10.0, 10.0)
        
        elif self.constraint_mode == 'hard':
            # HARD: Project to exact conservation
            self.enforce_hard_flux_conservation()
        
        # Clamp all fluxes for stability
        for b in self.branches:
            b.flux = np.clip(b.flux, -10.0, 10.0)
        
        # 3. Tension equilibration
        avg_tension = np.mean([b.tension for b in self.branches])
        for b in self.branches:
            b.tension += 0.1 * (avg_tension - b.tension) * dt
            b.tension = max(0.1, b.tension)
        
        self.time += dt
    
    def record_measurements(self, flux_penalty: float = 10.0):
        """
        Record all measurements for analysis.
        
        MEASUREMENT 1: Degree distribution
        MEASUREMENT 2: Flux residuals
        MEASUREMENT 3: Energy vs degree correlation
        """
        # 1. Degree distribution
        degrees = [self.get_node_degree(n) for n in self.nodes]
        degree_counts = {}
        for d in degrees:
            degree_counts[d] = degree_counts.get(d, 0) + 1
        
        self.degree_history.append({
            'time': self.time,
            'distribution': dict(degree_counts),
            'frac_degree_3': sum(1 for d in degrees if d == 3) / len(degrees) if degrees else 0
        })
        
        # 2. Flux residuals
        residuals = [self.get_flux_residual(n) for n in self.nodes]
        self.flux_residual_history.append({
            'time': self.time,
            'mean_R': float(np.mean(residuals)) if residuals else 0,
            'max_R': float(np.max(residuals)) if residuals else 0,
            'all_conserved': all(r < 0.01 for r in residuals)
        })
        
        # 3. Energy vs degree correlation
        degree_energy = defaultdict(list)
        for node_id in self.nodes:
            degree = self.get_node_degree(node_id)
            energy = self.compute_node_energy(node_id, flux_penalty)
            degree_energy[degree].append(energy)
        
        correlation_data = {}
        for deg, energies in degree_energy.items():
            correlation_data[deg] = {
                'mean_energy': float(np.mean(energies)),
                'count': len(energies)
            }
        
        self.energy_degree_correlation.append({
            'time': self.time,
            'by_degree': correlation_data
        })
    
    def evolve_and_measure(self, total_time: float, dt: float = 0.1, 
                           record_interval: int = 50, flux_penalty: float = 10.0):
        """Evolve network and record measurements periodically."""
        n_steps = int(total_time / dt)
        
        # Initial measurement
        self.record_measurements(flux_penalty)
        
        for step in range(n_steps):
            self.evolve_step(dt, flux_penalty)
            
            if (step + 1) % record_interval == 0:
                self.record_measurements(flux_penalty)
    
    def get_final_statistics(self) -> Dict:
        """Get comprehensive final statistics."""
        degrees = [self.get_node_degree(n) for n in self.nodes]
        degree_counts = {}
        for d in degrees:
            degree_counts[d] = degree_counts.get(d, 0) + 1
        
        residuals = [self.get_flux_residual(n) for n in self.nodes]
        
        # Count degree-3 fraction
        n_degree_3 = sum(1 for d in degrees if d == 3)
        frac_degree_3 = n_degree_3 / len(degrees) if degrees else 0
        
        return {
            'n_nodes': len(self.nodes),
            'n_branches': len(self.branches),
            'constraint_mode': self.constraint_mode,
            'final_degree_distribution': degree_counts,
            'frac_degree_3': float(frac_degree_3),
            'mean_flux_residual': float(np.mean(residuals)),
            'max_flux_residual': float(np.max(residuals)),
            'flux_conserved': np.max(residuals) < 0.01 if self.constraint_mode == 'hard' else np.mean(residuals) < 0.1
        }


def run_decisive_test():
    """
    THE DECISIVE TEST
    
    Run both SOFT and HARD constraints.
    Compare which (if any) forces degree → 3.
    """
    print("=" * 80)
    print("  DECISIVE FLUX CONSERVATION TEST")
    print("=" * 80)
    print("""
PURPOSE: Test NECESSITY, not just behavior.

QUESTION: Does flux conservation FORCE degree = 3?

MEASUREMENTS:
  1. Degree distribution evolution (Initial mixed → Final peaked at 3?)
  2. Flux residual R = |ΣJ| per node (R → 0?)
  3. Energy vs degree correlation (Non-3 nodes higher energy?)

TWO VERSIONS:
  🟥 SOFT: Penalty term E + λ(ΣJ)²
  🟩 HARD: Enforce exactly ΣJ = 0

SUCCESS CRITERIA (strict):
  ✅ 70-80% nodes → degree 3
  ✅ Stable over time
  ✅ Independent of initialization
""")
    
    results = {}
    
    # =========================================================================
    # VERSION A: SOFT CONSTRAINT
    # =========================================================================
    print("\n" + "=" * 70)
    print("  VERSION A: SOFT FLUX CONSTRAINT (Penalty)")
    print("=" * 70)
    
    soft_results = []
    
    for trial in range(5):
        print(f"\n--- Trial {trial + 1}/5 ---")
        
        network = DecisiveFluxNetwork(constraint_mode='soft', seed=trial * 17)
        network.create_random_network(n_nodes=25, connectivity=0.20)
        
        # Record initial state
        initial_stats = network.get_final_statistics()
        print(f"Initial degree dist: {initial_stats['final_degree_distribution']}")
        print(f"Initial degree-3 frac: {initial_stats['frac_degree_3']:.1%}")
        
        # Evolve
        network.evolve_and_measure(total_time=300.0, dt=0.1, 
                                   record_interval=100, flux_penalty=20.0)
        
        # Final state
        final_stats = network.get_final_statistics()
        print(f"Final degree dist: {final_stats['final_degree_distribution']}")
        print(f"Final degree-3 frac: {final_stats['frac_degree_3']:.1%}")
        print(f"Mean flux residual: {final_stats['mean_flux_residual']:.4f}")
        
        soft_results.append({
            'trial': trial,
            'initial': initial_stats,
            'final': final_stats,
            'degree_history': network.degree_history,
            'flux_history': network.flux_residual_history,
            'energy_correlation': network.energy_degree_correlation
        })
    
    # =========================================================================
    # VERSION B: HARD CONSTRAINT
    # =========================================================================
    print("\n" + "=" * 70)
    print("  VERSION B: HARD FLUX CONSTRAINT (Exact ΣJ = 0)")
    print("=" * 70)
    
    hard_results = []
    
    for trial in range(5):
        print(f"\n--- Trial {trial + 1}/5 ---")
        
        network = DecisiveFluxNetwork(constraint_mode='hard', seed=trial * 17)
        network.create_random_network(n_nodes=25, connectivity=0.20)
        
        # Record initial state
        initial_stats = network.get_final_statistics()
        print(f"Initial degree dist: {initial_stats['final_degree_distribution']}")
        print(f"Initial degree-3 frac: {initial_stats['frac_degree_3']:.1%}")
        
        # Evolve
        network.evolve_and_measure(total_time=300.0, dt=0.1, 
                                   record_interval=100, flux_penalty=20.0)
        
        # Final state
        final_stats = network.get_final_statistics()
        print(f"Final degree dist: {final_stats['final_degree_distribution']}")
        print(f"Final degree-3 frac: {final_stats['frac_degree_3']:.1%}")
        print(f"Max flux residual: {final_stats['max_flux_residual']:.6f}")
        
        hard_results.append({
            'trial': trial,
            'initial': initial_stats,
            'final': final_stats,
            'degree_history': network.degree_history,
            'flux_history': network.flux_residual_history,
            'energy_correlation': network.energy_degree_correlation
        })
    
    results['soft'] = soft_results
    results['hard'] = hard_results
    
    # =========================================================================
    # ANALYSIS
    # =========================================================================
    print("\n" + "=" * 80)
    print("  ANALYSIS")
    print("=" * 80)
    
    # Aggregate degree-3 fractions
    soft_frac_3 = [r['final']['frac_degree_3'] for r in soft_results]
    hard_frac_3 = [r['final']['frac_degree_3'] for r in hard_results]
    
    print(f"""
MEASUREMENT 1: DEGREE DISTRIBUTION
----------------------------------
                    SOFT Constraint      HARD Constraint
Mean degree-3 frac: {np.mean(soft_frac_3):>10.1%}          {np.mean(hard_frac_3):>10.1%}
Std deviation:      {np.std(soft_frac_3):>10.1%}          {np.std(hard_frac_3):>10.1%}
Min:                {np.min(soft_frac_3):>10.1%}          {np.min(hard_frac_3):>10.1%}
Max:                {np.max(soft_frac_3):>10.1%}          {np.max(hard_frac_3):>10.1%}

SUCCESS THRESHOLD: 70-80% degree-3
""")
    
    soft_success = np.mean(soft_frac_3) > 0.7
    hard_success = np.mean(hard_frac_3) > 0.7
    
    # MEASUREMENT 2: Flux Residuals
    print(f"""
MEASUREMENT 2: FLUX RESIDUALS
-----------------------------
""")
    
    for name, res_list in [('SOFT', soft_results), ('HARD', hard_results)]:
        final_residuals = [r['final']['mean_flux_residual'] for r in res_list]
        print(f"{name}: Mean residual = {np.mean(final_residuals):.6f}")
    
    # MEASUREMENT 3: Energy vs Degree Correlation
    print(f"""
MEASUREMENT 3: ENERGY VS DEGREE CORRELATION
-------------------------------------------
Question: Do non-3 nodes carry higher energy?
""")
    
    for name, res_list in [('SOFT', soft_results), ('HARD', hard_results)]:
        # Aggregate final energy by degree
        all_degree_energy = defaultdict(list)
        for r in res_list:
            if r['energy_correlation']:
                final_corr = r['energy_correlation'][-1]['by_degree']
                for deg, data in final_corr.items():
                    all_degree_energy[int(deg)].append(data['mean_energy'])
        
        print(f"\n{name} - Mean energy by degree:")
        for deg in sorted(all_degree_energy.keys()):
            avg_e = np.mean(all_degree_energy[deg])
            marker = " <-- TARGET" if deg == 3 else ""
            print(f"  Degree {deg}: E = {avg_e:.4f}{marker}")
    
    # =========================================================================
    # VERDICT
    # =========================================================================
    print("\n" + "=" * 80)
    print("  VERDICT")
    print("=" * 80)
    
    if hard_success:
        verdict = "STRONG_SUCCESS"
        description = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ FLUX CONSERVATION FORCES DEGREE = 3                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Hard constraint (exact ΣJ = 0) drives 70%+ of nodes to degree 3.            ║
║                                                                              ║
║  PHYSICAL INTERPRETATION:                                                    ║
║  If the medium has a strict flux conservation law, network topology          ║
║  is FORCED into the Y-junction dominated regime.                             ║
║                                                                              ║
║  Combined with Layer 1 (120° angles → 1/2 factor):                           ║
║    Flux conservation → Degree 3 → 120° → Fermion statistics                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    elif soft_success:
        verdict = "SOFT_SUCCESS"
        description = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ SOFT FLUX PENALTY SELECTS DEGREE = 3                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Even weak flux conservation (penalty term) drives degree → 3.               ║
║                                                                              ║
║  This suggests natural emergence is likely:                                  ║
║  No strict conservation needed, just energetic preference.                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    elif np.mean(hard_frac_3) > 0.5 or np.mean(soft_frac_3) > 0.5:
        verdict = "PARTIAL"
        description = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ PARTIAL RESULT                                                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Degree-3 fraction: SOFT = {np.mean(soft_frac_3):.1%}, HARD = {np.mean(hard_frac_3):.1%}                           ║
║                                                                              ║
║  Flux conservation HELPS but doesn't FORCE degree = 3.                       ║
║  May need additional constraints (energy penalty, topological charge).       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    else:
        verdict = "FAILURE"
        description = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ❌ FLUX CONSERVATION INSUFFICIENT                                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Degree-3 fraction: SOFT = {np.mean(soft_frac_3):.1%}, HARD = {np.mean(hard_frac_3):.1%}                           ║
║                                                                              ║
║  Flux conservation ALONE does not select degree = 3.                         ║
║  Need to test alternative constraints:                                       ║
║    - Topological charge quantization                                         ║
║    - Energy penalization for degree ≠ 3                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    print(description)
    
    # =========================================================================
    # DEGREE EVOLUTION PLOT (text-based)
    # =========================================================================
    print("\n" + "=" * 80)
    print("  DEGREE-3 FRACTION EVOLUTION (HARD constraint, Trial 0)")
    print("=" * 80)
    
    if hard_results and hard_results[0]['degree_history']:
        history = hard_results[0]['degree_history']
        print("\nTime     | Deg-3 Frac | Bar")
        print("-" * 50)
        for h in history:
            t = h['time']
            f3 = h['frac_degree_3']
            bar = "#" * int(f3 * 40)
            print(f"{t:>8.1f} | {f3:>10.1%} | {bar}")
    
    # =========================================================================
    # SAVE RESULTS
    # =========================================================================
    output = {
        'test': 'Decisive_Flux_Conservation',
        'soft_constraint': {
            'mean_degree_3_fraction': float(np.mean(soft_frac_3)),
            'std_degree_3_fraction': float(np.std(soft_frac_3)),
            'success': bool(soft_success)
        },
        'hard_constraint': {
            'mean_degree_3_fraction': float(np.mean(hard_frac_3)),
            'std_degree_3_fraction': float(np.std(hard_frac_3)),
            'success': bool(hard_success)
        },
        'verdict': verdict,
        'success_threshold': 0.70,
        'interpretation': {
            'STRONG_SUCCESS': 'Flux conservation FORCES degree=3. Missing physics found.',
            'SOFT_SUCCESS': 'Flux penalty selects degree=3. Natural emergence likely.',
            'PARTIAL': 'Flux helps but doesnt force. Additional constraints needed.',
            'FAILURE': 'Flux insufficient. Try topological charge or energy penalty.'
        }[verdict]
    }
    
    output_path = '/app/backend/qmrt_topology/decisive_flux_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return output


if __name__ == "__main__":
    results = run_decisive_test()
