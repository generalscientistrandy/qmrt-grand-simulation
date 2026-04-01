"""
QMRT: LOOP ENERGY AND LIFETIME TEST
====================================

THE CRITICAL MISSING PIECE:
  We found 6-transit loops → -1 holonomy.
  But physics doesn't care what CAN happen.
  It cares what DOMINATES statistically and energetically.

TESTS:
  1. E(n-loop): Energy vs loop size - Is 6 a local minimum?
  2. τ(n-loop): Lifetime vs loop size - Does 6 maximize lifetime?
  3. Perturbation stability: Do 6-loops persist under disturbance?

IF 6 IS ENERGETICALLY FAVORED OR MAXIMALLY STABLE:
  → Fermion-like behavior is dynamically selected
  → "Spin is selected topology under dynamics"

IF NOT:
  → Mechanism exists but is not physically realized
  → Additional constraints needed
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json


@dataclass
class LoopState:
    """State of a closed loop in the network."""
    size: int                    # Number of junctions
    positions: np.ndarray        # Junction positions
    tensions: np.ndarray         # Edge tensions
    
    def __post_init__(self):
        self.positions = np.array(self.positions, dtype=float)
        self.tensions = np.array(self.tensions, dtype=float)


class LoopEnergyTest:
    """Test energy and lifetime of loops of different sizes."""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.results = {}
    
    def create_regular_loop(self, n: int, radius: float = 1.0,
                            tension: float = 1.0) -> LoopState:
        """Create a regular n-gon loop."""
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        positions = np.array([[radius * np.cos(a), radius * np.sin(a)] 
                              for a in angles])
        tensions = np.ones(n) * tension
        
        return LoopState(size=n, positions=positions, tensions=tensions)
    
    def compute_loop_energy(self, loop: LoopState) -> Dict[str, float]:
        """
        Compute energy of a loop.
        
        Energy components:
          1. Edge length energy: E_edge = Σ T_i × L_i
          2. Angle energy: E_angle = penalty for deviation from ideal angle
          3. Curvature energy: E_curv = penalty for sharp bends
        """
        n = loop.size
        
        # Edge lengths
        edge_lengths = []
        for i in range(n):
            j = (i + 1) % n
            length = np.linalg.norm(loop.positions[j] - loop.positions[i])
            edge_lengths.append(length)
        
        edge_lengths = np.array(edge_lengths)
        
        # Edge energy
        E_edge = np.sum(loop.tensions * edge_lengths)
        
        # Interior angles
        angles = []
        for i in range(n):
            prev_idx = (i - 1) % n
            next_idx = (i + 1) % n
            
            v1 = loop.positions[prev_idx] - loop.positions[i]
            v2 = loop.positions[next_idx] - loop.positions[i]
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
            cos_angle = np.clip(cos_angle, -1, 1)
            angle = np.arccos(cos_angle)
            angles.append(angle)
        
        angles = np.array(angles)
        
        # Ideal interior angle for regular n-gon: (n-2)π/n
        ideal_angle = (n - 2) * np.pi / n
        
        # Angle energy: deviation from ideal
        E_angle = np.sum((angles - ideal_angle)**2)
        
        # Curvature energy: penalty for deviation from 180° (straight)
        curvature_penalty = 0.1
        E_curv = curvature_penalty * np.sum((np.pi - angles)**2)
        
        # Total energy
        E_total = E_edge + E_angle + E_curv
        
        # Perimeter (for normalization)
        perimeter = np.sum(edge_lengths)
        
        return {
            'E_total': float(E_total),
            'E_edge': float(E_edge),
            'E_angle': float(E_angle),
            'E_curv': float(E_curv),
            'E_per_vertex': float(E_total / n),
            'E_per_length': float(E_total / perimeter),
            'perimeter': float(perimeter),
            'mean_angle_deg': float(np.degrees(np.mean(angles))),
            'ideal_angle_deg': float(np.degrees(ideal_angle))
        }
    
    def evolve_loop(self, loop: LoopState, n_steps: int = 100,
                    dt: float = 0.01) -> Tuple[LoopState, List[Dict]]:
        """
        Evolve loop toward equilibrium.
        
        Track whether it collapses, expands, or stabilizes.
        """
        positions = loop.positions.copy()
        tensions = loop.tensions.copy()
        n = loop.size
        
        history = []
        
        for step in range(n_steps):
            # Compute forces on each vertex
            forces = np.zeros_like(positions)
            
            for i in range(n):
                prev_idx = (i - 1) % n
                next_idx = (i + 1) % n
                
                # Spring forces from neighbors
                to_prev = positions[prev_idx] - positions[i]
                to_next = positions[next_idx] - positions[i]
                
                dist_prev = np.linalg.norm(to_prev) + 1e-10
                dist_next = np.linalg.norm(to_next) + 1e-10
                
                # Target edge length (maintain current average)
                target_length = 1.0
                
                force_prev = tensions[prev_idx] * (dist_prev - target_length) * to_prev / dist_prev
                force_next = tensions[i] * (dist_next - target_length) * to_next / dist_next
                
                forces[i] = force_prev + force_next
            
            # Apply forces
            damping = 5.0
            positions += dt * forces / damping
            
            # Record state
            current_loop = LoopState(n, positions.copy(), tensions)
            energy = self.compute_loop_energy(current_loop)
            
            history.append({
                'step': step,
                'E_total': energy['E_total'],
                'perimeter': energy['perimeter']
            })
            
            # Check for collapse (perimeter too small)
            if energy['perimeter'] < 0.1 * n:
                break
        
        final_loop = LoopState(n, positions, tensions)
        return final_loop, history
    
    def measure_loop_lifetime(self, n: int, n_trials: int = 10,
                               perturbation: float = 0.1) -> Dict:
        """
        Measure lifetime of n-loop under perturbations.
        
        Lifetime = number of steps before collapse or instability.
        """
        lifetimes = []
        
        for trial in range(n_trials):
            # Create perturbed loop
            loop = self.create_regular_loop(n)
            
            # Add random perturbation
            loop.positions += np.random.normal(0, perturbation, loop.positions.shape)
            
            # Evolve and measure lifetime
            _, history = self.evolve_loop(loop, n_steps=200)
            
            # Lifetime = steps before energy diverges or perimeter collapses
            lifetime = len(history)
            
            # Check if loop survived
            if history:
                final_perimeter = history[-1]['perimeter']
                initial_perimeter = history[0]['perimeter']
                
                # If perimeter changed dramatically, loop is unstable
                if abs(final_perimeter - initial_perimeter) > 0.5 * initial_perimeter:
                    lifetime = next(
                        (h['step'] for h in history 
                         if abs(h['perimeter'] - initial_perimeter) > 0.3 * initial_perimeter),
                        lifetime
                    )
            
            lifetimes.append(lifetime)
        
        return {
            'n': n,
            'mean_lifetime': float(np.mean(lifetimes)),
            'std_lifetime': float(np.std(lifetimes)),
            'min_lifetime': int(np.min(lifetimes)),
            'max_lifetime': int(np.max(lifetimes)),
            'survival_rate': float(np.mean([l >= 200 for l in lifetimes]))
        }
    
    def run_energy_test(self) -> Dict:
        """Test energy vs loop size."""
        print("=" * 70)
        print("TEST 1: ENERGY vs LOOP SIZE")
        print("=" * 70)
        print("""
Question: Is n=6 (hexagon) energetically special?

Computing E(n-loop) for n = 3, 4, 5, 6, 7, 8, 9, 10, 12
""")
        
        results = []
        
        print(f"{'n':>4} | {'E_total':>10} | {'E/vertex':>10} | {'E/length':>10} | {'Angle (°)':>10}")
        print("-" * 55)
        
        for n in [3, 4, 5, 6, 7, 8, 9, 10, 12]:
            loop = self.create_regular_loop(n)
            energy = self.compute_loop_energy(loop)
            
            marker = " ← FERMION" if n == 6 else ""
            print(f"{n:>4} | {energy['E_total']:>10.4f} | {energy['E_per_vertex']:>10.4f} | "
                  f"{energy['E_per_length']:>10.4f} | {energy['ideal_angle_deg']:>10.1f}{marker}")
            
            results.append({
                'n': n,
                **energy
            })
        
        # Find minimum
        min_energy_per_vertex = min(results, key=lambda x: x['E_per_vertex'])
        min_energy_per_length = min(results, key=lambda x: x['E_per_length'])
        
        print(f"\nMinimum E/vertex at n = {min_energy_per_vertex['n']}")
        print(f"Minimum E/length at n = {min_energy_per_length['n']}")
        
        return results
    
    def run_lifetime_test(self) -> Dict:
        """Test lifetime vs loop size."""
        print("\n" + "=" * 70)
        print("TEST 2: LIFETIME vs LOOP SIZE")
        print("=" * 70)
        print("""
Question: Does n=6 maximize stability/lifetime?

Measuring τ(n-loop) under perturbations.
""")
        
        results = []
        
        print(f"{'n':>4} | {'Mean τ':>10} | {'Std τ':>10} | {'Survival':>10}")
        print("-" * 45)
        
        for n in [3, 4, 5, 6, 7, 8, 9, 10, 12]:
            lifetime_data = self.measure_loop_lifetime(n, n_trials=10)
            
            marker = " ← FERMION" if n == 6 else ""
            print(f"{n:>4} | {lifetime_data['mean_lifetime']:>10.1f} | "
                  f"{lifetime_data['std_lifetime']:>10.1f} | "
                  f"{lifetime_data['survival_rate']:>9.0%}{marker}")
            
            results.append(lifetime_data)
        
        # Find maximum lifetime
        max_lifetime = max(results, key=lambda x: x['mean_lifetime'])
        max_survival = max(results, key=lambda x: x['survival_rate'])
        
        print(f"\nMaximum mean lifetime at n = {max_lifetime['n']}")
        print(f"Maximum survival rate at n = {max_survival['n']}")
        
        return results
    
    def run_perturbation_test(self) -> Dict:
        """Test stability under perturbation for n=6."""
        print("\n" + "=" * 70)
        print("TEST 3: HEXAGON PERTURBATION STABILITY")
        print("=" * 70)
        print("""
Question: How robust is the 6-loop under perturbations?

Perturbing hexagonal loop and tracking evolution.
""")
        
        # Create hexagonal loop
        loop = self.create_regular_loop(6)
        initial_energy = self.compute_loop_energy(loop)
        
        print(f"Initial hexagon energy: {initial_energy['E_total']:.4f}")
        
        # Apply perturbation
        perturbation_sizes = [0.05, 0.1, 0.2, 0.3, 0.5]
        results = []
        
        print(f"\n{'Perturbation':>12} | {'Final E':>10} | {'ΔE':>10} | {'Stable?':>8}")
        print("-" * 50)
        
        for pert in perturbation_sizes:
            perturbed = self.create_regular_loop(6)
            perturbed.positions += np.random.normal(0, pert, perturbed.positions.shape)
            
            # Evolve
            final_loop, history = self.evolve_loop(perturbed, n_steps=200)
            final_energy = self.compute_loop_energy(final_loop)
            
            delta_E = final_energy['E_total'] - initial_energy['E_total']
            stable = abs(delta_E) < 0.5 and len(history) >= 200
            
            print(f"{pert:>12.2f} | {final_energy['E_total']:>10.4f} | "
                  f"{delta_E:>+10.4f} | {'✅' if stable else '❌':>8}")
            
            results.append({
                'perturbation': pert,
                'final_energy': final_energy['E_total'],
                'delta_E': delta_E,
                'stable': stable,
                'steps_survived': len(history)
            })
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all energy and lifetime tests."""
        print("=" * 80)
        print("  QMRT: LOOP ENERGY AND LIFETIME TEST")
        print("=" * 80)
        print("""
CRITICAL QUESTION:
  We found 6-transit loops → -1 holonomy (fermion mechanism).
  But is 6 energetically favored or maximally stable?
  
  IF YES → fermion behavior is dynamically selected
  IF NO  → mechanism exists but isn't physically realized
""")
        
        energy_results = self.run_energy_test()
        lifetime_results = self.run_lifetime_test()
        perturbation_results = self.run_perturbation_test()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        # Find where n=6 ranks
        energy_sorted = sorted(energy_results, key=lambda x: x['E_per_vertex'])
        lifetime_sorted = sorted(lifetime_results, key=lambda x: -x['mean_lifetime'])
        
        six_energy_rank = next(i+1 for i, x in enumerate(energy_sorted) if x['n'] == 6)
        six_lifetime_rank = next(i+1 for i, x in enumerate(lifetime_sorted) if x['n'] == 6)
        
        print(f"""
HEXAGON (n=6) RANKING:
  Energy (E/vertex):  Rank {six_energy_rank} of {len(energy_results)}
  Lifetime:           Rank {six_lifetime_rank} of {len(lifetime_results)}
  
Lowest energy: n = {energy_sorted[0]['n']}
Highest lifetime: n = {lifetime_sorted[0]['n']}
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        six_is_best = (six_energy_rank == 1 or six_lifetime_rank == 1)
        six_is_good = (six_energy_rank <= 3 and six_lifetime_rank <= 3)
        
        if six_is_best:
            verdict = "HEXAGON_OPTIMAL"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ HEXAGON (n=6) IS OPTIMAL                                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  6-loops are energetically favored or maximally stable.                      ║
║  This means:                                                                 ║
║    → Fermion-like behavior IS dynamically selected                           ║
║    → The mechanism is not just possible, it's physically realized            ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        elif six_is_good:
            verdict = "HEXAGON_COMPETITIVE"
            print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ HEXAGON (n=6) IS COMPETITIVE BUT NOT OPTIMAL                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  6-loops are among the better options but not the absolute best.             ║
║  Fermion behavior can emerge but isn't uniquely selected.                    ║
║  Additional physical constraints may be needed.                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "HEXAGON_NOT_FAVORED"
            print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ❌ HEXAGON (n=6) IS NOT ENERGETICALLY FAVORED                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Other loop sizes are more stable.                                           ║
║  The fermion mechanism exists but is not physically selected.                ║
║  Different dynamics or constraints would be needed.                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # The precise claim
        print("""
PRECISE THEORETICAL CLAIM:

  "QMRT exhibits a discrete Z₁₂ geometric phase structure arising from 
   Y-junction transport, with each transit contributing Δφ = −π/6.
   
   Closed loops of six transits produce a −1 holonomy, yielding 
   fermion-like sign behavior.
   
   However, this behavior is not intrinsic; it emerges only in network 
   regimes that dynamically support stable 6-transit loops.
   
   This indicates that particle statistics arise from topology and 
   medium dynamics rather than fundamental point properties."
""")
        
        # Save results
        output = {
            'test': 'Loop_Energy_Lifetime',
            'verdict': verdict,
            'hexagon_energy_rank': six_energy_rank,
            'hexagon_lifetime_rank': six_lifetime_rank,
            'best_energy_n': energy_sorted[0]['n'],
            'best_lifetime_n': lifetime_sorted[0]['n'],
            'energy_results': energy_results,
            'lifetime_results': lifetime_results,
            'perturbation_results': perturbation_results
        }
        
        output_path = '/app/backend/qmrt_topology/loop_energy_lifetime_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = LoopEnergyTest()
    results = test.run_all_tests()
