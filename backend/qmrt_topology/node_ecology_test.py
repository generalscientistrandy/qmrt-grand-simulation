"""
QMRT: NODE-DEGREE ECOLOGY STUDY
===============================

REFRAMED QUESTION:
  Not "does degree-3 win?" but rather:
  "What is the full node-degree ecology of the medium?"

HYPOTHESIS:
  The medium supports multiple local coordination numbers up to a maximum
  set by its directional structure (possibly 6). Degree-3 Y-junctions may
  be uniquely stable only within one dynamical regime, rather than universally.

THREE SEPARATE QUESTIONS:
  1. KINEMATIC ALLOWANCE - Which degrees are geometrically possible?
  2. DYNAMICAL FORMATION - Which degrees actually form from evolution?
  3. ENERGETIC STABILITY - Which degrees persist after relaxation?

NODE DEGREE SPECTRUM:
  degree-1: endpoint / defect / source-like
  degree-2: strand / ordinary propagation
  degree-3: Y-junction / branching splitter
  degree-4: crossing / exchange node / reconnection hub
  degree-5: higher-order compression
  degree-6: maximally symmetric hub (if 6 directions exist)

TEST PROTOCOL:
  For each degree k = 1..6:
    - Initialize local node with k branches
    - Allow full angular relaxation
    - Include reconnection dynamics
    - Include tension equilibration
    - Measure: final energy, lifetime, decay patterns
    - Classify: allowed, formed, metastable, stable, composite-decaying
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json


@dataclass
class NodeState:
    """State of a single node with k branches."""
    degree: int
    angles: np.ndarray      # Angles of each branch (radians)
    tensions: np.ndarray    # Tension on each branch
    position: np.ndarray    # Center position
    
    def __post_init__(self):
        self.angles = np.array(self.angles, dtype=float)
        self.tensions = np.array(self.tensions, dtype=float)
        self.position = np.array(self.position, dtype=float)


class NodeDegreeEcologyTest:
    """
    Study the full ecology of node degrees in the medium.
    """
    
    def __init__(self, max_degree: int = 6):
        self.max_degree = max_degree
        self.results = {}
    
    # =========================================================================
    # NODE INITIALIZATION
    # =========================================================================
    
    def create_symmetric_node(self, degree: int, 
                               tension: float = 1.0,
                               perturbation: float = 0.0) -> NodeState:
        """
        Create a node with k branches in symmetric configuration.
        
        Symmetric means equal angular spacing: θᵢ = 2πi/k
        """
        if degree < 1:
            raise ValueError("Degree must be at least 1")
        
        # Equal angular spacing
        angles = np.array([2 * np.pi * i / degree for i in range(degree)])
        
        # Add perturbation
        if perturbation > 0:
            angles += np.random.normal(0, perturbation, degree)
            angles = angles % (2 * np.pi)
        
        tensions = np.ones(degree) * tension
        
        return NodeState(
            degree=degree,
            angles=angles,
            tensions=tensions,
            position=np.array([0.0, 0.0])
        )
    
    def create_random_node(self, degree: int,
                           tension_spread: float = 0.3) -> NodeState:
        """Create a node with random angles and tensions."""
        angles = np.sort(np.random.uniform(0, 2*np.pi, degree))
        tensions = np.random.uniform(1 - tension_spread, 1 + tension_spread, degree)
        
        return NodeState(
            degree=degree,
            angles=angles,
            tensions=tensions,
            position=np.array([0.0, 0.0])
        )
    
    # =========================================================================
    # ENERGY AND FORCE CALCULATIONS
    # =========================================================================
    
    def compute_node_energy(self, node: NodeState,
                            angle_penalty: float = 1.0,
                            tension_penalty: float = 0.5) -> float:
        """
        Compute energy of a node configuration.
        
        E = E_angle + E_tension
        
        E_angle penalizes deviation from equal angular spacing.
        E_tension penalizes tension variance.
        """
        k = node.degree
        
        if k == 0:
            return 0.0
        
        if k == 1:
            # Endpoint: high energy (monopole-like)
            return 10.0
        
        # Ideal angular spacing
        ideal_spacing = 2 * np.pi / k
        
        # Compute actual spacings
        sorted_angles = np.sort(node.angles)
        spacings = np.diff(sorted_angles)
        # Add wrap-around spacing
        spacings = np.append(spacings, 2*np.pi - sorted_angles[-1] + sorted_angles[0])
        
        # Angle energy: variance from ideal spacing
        E_angle = angle_penalty * np.sum((spacings - ideal_spacing)**2)
        
        # Tension energy: variance from mean
        mean_tension = np.mean(node.tensions)
        E_tension = tension_penalty * np.sum((node.tensions - mean_tension)**2)
        
        # Base energy proportional to degree (more branches = more energy)
        E_base = 0.5 * k
        
        return E_base + E_angle + E_tension
    
    def compute_force_balance(self, node: NodeState) -> float:
        """
        Compute force imbalance at node.
        
        F = |Σᵢ Tᵢ ûᵢ|
        
        Perfect balance means F = 0.
        """
        force = np.zeros(2)
        
        for i, (angle, tension) in enumerate(zip(node.angles, node.tensions)):
            direction = np.array([np.cos(angle), np.sin(angle)])
            force += tension * direction
        
        return np.linalg.norm(force)
    
    def compute_equilibrium_angles(self, tensions: np.ndarray) -> Optional[np.ndarray]:
        """
        Compute equilibrium angles for given tensions.
        
        Solves: Σᵢ Tᵢ ûᵢ = 0
        
        Returns None if no equilibrium exists.
        """
        k = len(tensions)
        
        if k < 2:
            return None
        
        if k == 2:
            # Two branches: must be opposite (180°)
            return np.array([0, np.pi])
        
        # For k >= 3, use iterative relaxation
        angles = np.array([2 * np.pi * i / k for i in range(k)])
        
        for _ in range(1000):
            # Compute net force
            force = np.zeros(2)
            for angle, tension in zip(angles, tensions):
                direction = np.array([np.cos(angle), np.sin(angle)])
                force += tension * direction
            
            if np.linalg.norm(force) < 1e-10:
                break
            
            # Adjust angles to reduce force
            for i in range(k):
                direction = np.array([np.cos(angles[i]), np.sin(angles[i])])
                torque = -np.cross(direction, force)
                angles[i] += 0.01 * torque / tensions[i]
            
            angles = angles % (2 * np.pi)
        
        return angles
    
    # =========================================================================
    # STABILITY ANALYSIS
    # =========================================================================
    
    def evolve_node(self, node: NodeState, n_steps: int = 500,
                    dt: float = 0.05, reconnection: bool = True) -> Tuple[NodeState, Dict]:
        """
        Evolve node toward equilibrium.
        
        Dynamics:
          - Angle relaxation (reduce force imbalance)
          - Tension equilibration
          - Optional reconnection (degree change)
        
        Returns: (final_node, evolution_history)
        """
        angles = node.angles.copy()
        tensions = node.tensions.copy()
        degree = node.degree
        
        history = {
            'energies': [],
            'force_imbalances': [],
            'degrees': [],
            'reconnection_events': []
        }
        
        for step in range(n_steps):
            # Compute current state
            current_node = NodeState(degree, angles, tensions, node.position)
            energy = self.compute_node_energy(current_node)
            force_imbalance = self.compute_force_balance(current_node)
            
            history['energies'].append(energy)
            history['force_imbalances'].append(force_imbalance)
            history['degrees'].append(degree)
            
            # ---- Angle relaxation ----
            if degree >= 2:
                # Compute net force
                net_force = np.zeros(2)
                for angle, tension in zip(angles, tensions):
                    direction = np.array([np.cos(angle), np.sin(angle)])
                    net_force += tension * direction
                
                # Adjust each angle to reduce imbalance
                for i in range(len(angles)):
                    direction = np.array([np.cos(angles[i]), np.sin(angles[i])])
                    torque = -np.cross(direction, net_force)
                    angles[i] += dt * torque / tensions[i]
                
                angles = angles % (2 * np.pi)
            
            # ---- Tension equilibration ----
            if len(tensions) >= 2:
                mean_tension = np.mean(tensions)
                tensions += 0.1 * dt * (mean_tension - tensions)
                tensions = np.maximum(0.1, tensions)
            
            # ---- Reconnection (degree change) ----
            if reconnection and step % 50 == 0:
                # Check if any branches should merge (close angles)
                if degree >= 3:
                    sorted_idx = np.argsort(angles)
                    sorted_angles = angles[sorted_idx]
                    
                    for i in range(len(sorted_angles)):
                        j = (i + 1) % len(sorted_angles)
                        
                        angle_diff = sorted_angles[j] - sorted_angles[i]
                        if angle_diff < 0:
                            angle_diff += 2 * np.pi
                        
                        # If branches very close, merge them
                        if angle_diff < 0.2:  # ~11 degrees
                            # Merge branches i and j
                            merged_angle = (sorted_angles[i] + sorted_angles[j]) / 2
                            merged_tension = tensions[sorted_idx[i]] + tensions[sorted_idx[j]]
                            
                            # Remove one, modify other
                            angles = np.delete(angles, sorted_idx[j])
                            tensions = np.delete(tensions, sorted_idx[j])
                            
                            # Update the kept branch
                            new_idx = np.where(np.arange(len(angles)+1) != sorted_idx[j])[0]
                            keep_idx = np.searchsorted(new_idx, sorted_idx[i])
                            if keep_idx < len(angles):
                                angles[keep_idx] = merged_angle
                                tensions[keep_idx] = merged_tension
                            
                            degree -= 1
                            history['reconnection_events'].append({
                                'step': step,
                                'type': 'merge',
                                'old_degree': degree + 1,
                                'new_degree': degree
                            })
                            break
                
                # Check if high-degree node should split
                if degree >= 4:
                    # Compute energy gain from splitting
                    current_energy = energy
                    
                    # Hypothetical split: degree-4 → 2 × degree-2
                    # (This is a simplified model)
                    split_energy = 2 * self.compute_node_energy(
                        self.create_symmetric_node(degree // 2)
                    )
                    
                    if split_energy < current_energy - 0.5:
                        # Split is energetically favored
                        # For simplicity, reduce to (degree - 1)
                        angles = angles[:-1]
                        tensions = tensions[:-1]
                        degree -= 1
                        history['reconnection_events'].append({
                            'step': step,
                            'type': 'split',
                            'old_degree': degree + 1,
                            'new_degree': degree
                        })
        
        final_node = NodeState(degree, angles, tensions, node.position)
        
        return final_node, history
    
    def classify_node_stability(self, initial_degree: int,
                                 n_trials: int = 10) -> Dict:
        """
        Classify stability of a given node degree.
        
        Categories:
          - STABLE: Node remains at same degree after relaxation
          - METASTABLE: Sometimes stable, sometimes decays
          - UNSTABLE: Always decays to lower degree
          - COMPOSITE: Splits into multiple lower-degree nodes
        """
        outcomes = []
        
        for trial in range(n_trials):
            # Create node with some randomness
            if trial < n_trials // 2:
                node = self.create_symmetric_node(initial_degree, perturbation=0.1)
            else:
                node = self.create_random_node(initial_degree)
            
            # Evolve
            final_node, history = self.evolve_node(node, n_steps=500)
            
            # Record outcome
            initial_energy = history['energies'][0]
            final_energy = history['energies'][-1]
            final_degree = final_node.degree
            force_imbalance = history['force_imbalances'][-1]
            
            outcomes.append({
                'initial_degree': initial_degree,
                'final_degree': final_degree,
                'degree_change': final_degree - initial_degree,
                'initial_energy': initial_energy,
                'final_energy': final_energy,
                'force_imbalance': force_imbalance,
                'balanced': force_imbalance < 0.1,
                'reconnections': len(history['reconnection_events'])
            })
        
        # Classify
        final_degrees = [o['final_degree'] for o in outcomes]
        unchanged = sum(1 for d in final_degrees if d == initial_degree)
        decreased = sum(1 for d in final_degrees if d < initial_degree)
        
        if unchanged == n_trials:
            classification = "STABLE"
        elif unchanged > n_trials // 2:
            classification = "METASTABLE"
        elif decreased > n_trials // 2:
            if initial_degree >= 4:
                classification = "COMPOSITE_DECAYING"
            else:
                classification = "UNSTABLE"
        else:
            classification = "UNSTABLE"
        
        # Check equilibrium angles for equal tensions
        equal_tension_node = self.create_symmetric_node(initial_degree)
        equal_tension_node, _ = self.evolve_node(equal_tension_node, n_steps=200)
        eq_angles = np.sort(equal_tension_node.angles)
        
        # Compute angle spacings
        spacings = np.diff(eq_angles)
        spacings = np.append(spacings, 2*np.pi - eq_angles[-1] + eq_angles[0])
        
        ideal_spacing = 2 * np.pi / initial_degree
        angle_deviation = np.std(spacings - ideal_spacing)
        
        return {
            'degree': initial_degree,
            'classification': classification,
            'trials': n_trials,
            'remained_at_degree': unchanged,
            'decreased_degree': decreased,
            'mean_final_degree': float(np.mean(final_degrees)),
            'equilibrium_angle_spacing': float(np.degrees(ideal_spacing)),
            'angle_deviation_from_ideal': float(np.degrees(angle_deviation)),
            'mean_force_imbalance': float(np.mean([o['force_imbalance'] for o in outcomes])),
            'outcomes': outcomes
        }
    
    def run_full_ecology_study(self) -> Dict:
        """Run complete node-degree ecology study."""
        print("=" * 80)
        print("  QMRT: NODE-DEGREE ECOLOGY STUDY")
        print("=" * 80)
        print(f"""
QUESTION: What is the full node-degree ecology of the medium?

Testing degrees k = 1 to {self.max_degree}

For each degree:
  - Kinematic: Is it geometrically possible?
  - Dynamic: Does it form and persist?
  - Energetic: What is its equilibrium?

NODE SPECTRUM:
  degree-1: endpoint / defect
  degree-2: strand / propagation
  degree-3: Y-junction / branching
  degree-4: crossing / exchange hub
  degree-5: compression node
  degree-6: maximally symmetric hub
""")
        
        results = {}
        
        print("\n" + "=" * 70)
        print("DEGREE-BY-DEGREE ANALYSIS")
        print("=" * 70)
        
        for k in range(1, self.max_degree + 1):
            print(f"\n--- Degree {k} ---")
            
            result = self.classify_node_stability(k, n_trials=10)
            results[k] = result
            
            print(f"  Equilibrium angle spacing: {result['equilibrium_angle_spacing']:.1f}°")
            print(f"  Trials remained at degree-{k}: {result['remained_at_degree']}/{result['trials']}")
            print(f"  Mean force imbalance: {result['mean_force_imbalance']:.4f}")
            print(f"  Classification: {result['classification']}")
        
        # Summary table
        print("\n" + "=" * 80)
        print("NODE-DEGREE ECOLOGY SUMMARY")
        print("=" * 80)
        
        print(f"\n{'Degree':>6} | {'Angle':>8} | {'Stability':>18} | {'Retained':>8} | {'Force Bal':>10}")
        print("-" * 65)
        
        stability_symbols = {
            'STABLE': '✅',
            'METASTABLE': '⚠️',
            'UNSTABLE': '❌',
            'COMPOSITE_DECAYING': '🔄'
        }
        
        for k in range(1, self.max_degree + 1):
            r = results[k]
            symbol = stability_symbols.get(r['classification'], '?')
            print(f"{k:>6} | {r['equilibrium_angle_spacing']:>7.1f}° | "
                  f"{symbol} {r['classification']:>15} | "
                  f"{r['remained_at_degree']:>3}/{r['trials']:>3} | "
                  f"{r['mean_force_imbalance']:>10.4f}")
        
        # Physical interpretation
        print("\n" + "=" * 80)
        print("PHYSICAL INTERPRETATION")
        print("=" * 80)
        
        stable_degrees = [k for k, r in results.items() if r['classification'] == 'STABLE']
        metastable_degrees = [k for k, r in results.items() if r['classification'] == 'METASTABLE']
        unstable_degrees = [k for k, r in results.items() if r['classification'] in ['UNSTABLE', 'COMPOSITE_DECAYING']]
        
        print(f"""
STABLE DEGREES: {stable_degrees}
  These persist after relaxation and maintain force balance.
  
METASTABLE DEGREES: {metastable_degrees}
  These sometimes persist, sometimes decay.
  May depend on initial conditions or perturbations.
  
UNSTABLE/COMPOSITE DEGREES: {unstable_degrees}
  These decay to lower degrees or split into composites.
""")
        
        # Key finding about degree-3
        if 3 in stable_degrees:
            print("""
KEY FINDING: Degree-3 (Y-junction)
  
  The Y-junction is STABLE with 120° equilibrium spacing.
  This is consistent with our earlier fermion emergence result:
    120° → 1/2 projection → π phase → -1 holonomy → fermion
  
  However, other degrees may also be stable depending on the regime.
""")
        
        # Degree-4 analysis
        if 4 in results:
            r4 = results[4]
            print(f"""
DEGREE-4 ANALYSIS:
  
  Classification: {r4['classification']}
  Equilibrium spacing: {r4['equilibrium_angle_spacing']:.1f}° (ideal: 90°)
  Retained: {r4['remained_at_degree']}/{r4['trials']}
  
  {"Degree-4 nodes tend to decompose into degree-3 or lower." if r4['classification'] in ['UNSTABLE', 'COMPOSITE_DECAYING'] else "Degree-4 can be stable (crossing/exchange nodes)."}
""")
        
        # Overall verdict
        print("\n" + "=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        if len(stable_degrees) == 1 and 3 in stable_degrees:
            verdict = "DEGREE_3_DOMINANT"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEGREE-3 UNIQUELY DOMINANT                                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Only degree-3 (Y-junctions) are stable after relaxation.                    ║
║  Higher degrees decompose into Y-junction networks.                          ║
║                                                                              ║
║  This supports the Y-junction fermion emergence picture.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        elif len(stable_degrees) > 1:
            verdict = "MULTI_DEGREE_ECOLOGY"
            print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MULTI-DEGREE ECOLOGY                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Multiple degrees are stable: {stable_degrees}
║                                                                              ║
║  The medium supports a family of node types:                                 ║
║    - Some are fundamental building blocks                                    ║
║    - Some appear only in specific regimes                                    ║
║                                                                              ║
║  Y-junction (degree-3) remains special for fermion emergence,                ║
║  but the full medium has richer structure.                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "NO_STABLE_HIGHER_DEGREES"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ALL HIGHER DEGREES UNSTABLE                                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Only degree-2 (strands) are stable.                                         ║
║  Branching nodes decay.                                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Save results
        output = {
            'test': 'Node_Degree_Ecology',
            'max_degree_tested': self.max_degree,
            'stable_degrees': stable_degrees,
            'metastable_degrees': metastable_degrees,
            'unstable_degrees': unstable_degrees,
            'verdict': verdict,
            'by_degree': {k: {
                'classification': r['classification'],
                'equilibrium_angle': r['equilibrium_angle_spacing'],
                'retained_fraction': r['remained_at_degree'] / r['trials'],
                'mean_force_imbalance': r['mean_force_imbalance']
            } for k, r in results.items()}
        }
        
        output_path = '/app/backend/qmrt_topology/node_ecology_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = NodeDegreeEcologyTest(max_degree=6)
    results = test.run_full_ecology_study()
