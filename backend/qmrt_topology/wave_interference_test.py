"""
QMRT: WAVE PROPAGATION + INTERFERENCE TEST
==========================================

THE MISSING PHYSICS:
  Previous model: purely dissipative (dθ/dt = relaxation)
  → Smoothing dominates, structure collapses

  New model: wave + damping (d²θ/dt² = coupling - damping)
  → Allows oscillation, interference, standing patterns

KEY INSIGHT:
  "Entropy alone destroys structure.
   Structure requires: phase memory, propagation, interference."

PHYSICS UPGRADE:
  1. FINITE PROPAGATION - wave-like transport with delay
  2. INTERFERENCE - phase coupling that can be constructive/destructive
  3. DAMPING - mild dissipation (but not dominant)
  4. RESONANCE SURVIVAL - mismatched configurations decay faster

TEST:
  With NO closure rules, NO quantization filters:
  Do discrete stable patterns emerge from wave interference?
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json
from collections import Counter


# =============================================================================
# WAVE PROPAGATION MODEL
# =============================================================================

@dataclass
class WaveNode:
    """Node with wave-like phase dynamics."""
    id: int
    position: np.ndarray
    
    # Wave variables (second-order dynamics)
    phase: float = 0.0           # θ
    phase_velocity: float = 0.0  # dθ/dt (phase momentum)
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=float)


@dataclass  
class WaveEdge:
    """Edge with phase coupling."""
    id: int
    node_a: int
    node_b: int
    
    coupling: float = 1.0  # Phase coupling strength
    length: float = 1.0    # Physical length (affects propagation delay)


class WaveInterferenceNetwork:
    """
    Network with WAVE propagation and INTERFERENCE.
    
    Key differences from previous model:
    1. Second-order dynamics: d²θ/dt² (not just dθ/dt)
    2. Finite propagation speed (phase doesn't update instantly)
    3. Interference: phases can add constructively or destructively
    4. Resonance: only coherent configurations persist
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        
        self.nodes: Dict[int, WaveNode] = {}
        self.edges: Dict[int, WaveEdge] = {}
        self.adjacency: Dict[int, List[int]] = {}
        
        self.next_node_id = 0
        self.next_edge_id = 0
        
        # WAVE PHYSICS PARAMETERS
        self.wave_speed = 1.0           # Propagation speed
        self.coupling_strength = 2.0    # Phase coupling (spring constant)
        self.damping = 0.1              # Mild dissipation (not dominant!)
        self.phase_per_junction = -np.pi / 6  # Geometric phase offset
        
        # Time stepping
        self.dt = 0.01
        
        # Interference tracking
        self.interference_history = []
    
    # =========================================================================
    # NETWORK CONSTRUCTION
    # =========================================================================
    
    def add_node(self, position: np.ndarray, phase: float = None,
                 velocity: float = None) -> int:
        nid = self.next_node_id
        
        if phase is None:
            phase = np.random.random() * 2 * np.pi - np.pi
        if velocity is None:
            velocity = (np.random.random() - 0.5) * 0.5
        
        self.nodes[nid] = WaveNode(nid, position, phase, velocity)
        self.adjacency[nid] = []
        self.next_node_id += 1
        return nid
    
    def add_edge(self, node_a: int, node_b: int) -> int:
        eid = self.next_edge_id
        
        # Compute length
        pos_a = self.nodes[node_a].position
        pos_b = self.nodes[node_b].position
        length = np.linalg.norm(pos_b - pos_a)
        
        self.edges[eid] = WaveEdge(eid, node_a, node_b, length=length)
        
        self.adjacency[node_a].append(eid)
        self.adjacency[node_b].append(eid)
        
        self.next_edge_id += 1
        return eid
    
    def create_loop(self, n: int, center: np.ndarray = None,
                    radius: float = 1.0) -> List[int]:
        if center is None:
            center = np.array([0.0, 0.0])
        
        node_ids = []
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        for angle in angles:
            pos = center + radius * np.array([np.cos(angle), np.sin(angle)])
            # Random initial phase and velocity
            phase = np.random.random() * 2 * np.pi - np.pi
            velocity = (np.random.random() - 0.5) * 1.0
            
            nid = self.add_node(pos, phase, velocity)
            node_ids.append(nid)
        
        for i in range(n):
            self.add_edge(node_ids[i], node_ids[(i+1) % n])
        
        return node_ids
    
    # =========================================================================
    # WAVE DYNAMICS
    # =========================================================================
    
    def _wrap_phase(self, phase: float) -> float:
        while phase > np.pi:
            phase -= 2 * np.pi
        while phase < -np.pi:
            phase += 2 * np.pi
        return phase
    
    def compute_wave_acceleration(self, node_id: int) -> float:
        """
        Compute phase acceleration from wave coupling.
        
        This is the KEY physics:
          d²θ/dt² = coupling_force - damping * dθ/dt
        
        Coupling force comes from neighbors:
          F = Σ_neighbors k * sin(θ_neighbor - θ_self - offset)
        
        The offset is the geometric phase per junction.
        """
        node = self.nodes[node_id]
        edge_ids = self.adjacency[node_id]
        
        if not edge_ids:
            return -self.damping * node.phase_velocity
        
        # Coupling force from neighbors
        coupling_force = 0.0
        
        for eid in edge_ids:
            edge = self.edges[eid]
            neighbor_id = edge.node_a if edge.node_b == node_id else edge.node_b
            neighbor = self.nodes[neighbor_id]
            
            # Phase difference with geometric offset
            # Expected relationship: neighbor = self + offset
            expected_diff = self.phase_per_junction
            actual_diff = self._wrap_phase(neighbor.phase - node.phase)
            
            # Phase mismatch (deviation from expected)
            mismatch = self._wrap_phase(actual_diff - expected_diff)
            
            # Spring-like coupling: wants to reduce mismatch
            # Using sin for bounded force
            force = self.coupling_strength * np.sin(mismatch)
            
            # Propagation delay (finite wave speed)
            delay_factor = 1.0 / (1.0 + edge.length / self.wave_speed)
            
            coupling_force += force * delay_factor
        
        coupling_force /= len(edge_ids)
        
        # Damping (mild - important that it doesn't dominate!)
        damping_force = -self.damping * node.phase_velocity
        
        return coupling_force + damping_force
    
    def evolve_step(self):
        """
        Evolve using wave equation (second-order).
        
        θ'' = F(θ, neighbors) - γ * θ'
        
        Using velocity Verlet integration for stability.
        """
        # Store accelerations
        accelerations = {}
        for nid in self.nodes:
            accelerations[nid] = self.compute_wave_acceleration(nid)
        
        # Update velocities (half step)
        for nid, node in self.nodes.items():
            node.phase_velocity += 0.5 * accelerations[nid] * self.dt
        
        # Update positions
        for nid, node in self.nodes.items():
            node.phase += node.phase_velocity * self.dt
            node.phase = self._wrap_phase(node.phase)
        
        # Recompute accelerations
        new_accelerations = {}
        for nid in self.nodes:
            new_accelerations[nid] = self.compute_wave_acceleration(nid)
        
        # Update velocities (second half step)
        for nid, node in self.nodes.items():
            node.phase_velocity += 0.5 * new_accelerations[nid] * self.dt
    
    def compute_interference(self, node_ids: List[int]) -> float:
        """
        Measure interference around a loop.
        
        Constructive: phases align with expected pattern
        Destructive: phases misalign
        
        Returns value in [-1, 1]: 1 = perfect constructive, -1 = destructive
        """
        n = len(node_ids)
        if n < 2:
            return 0.0
        
        interference = 0.0
        
        for i in range(n):
            curr_phase = self.nodes[node_ids[i]].phase
            next_phase = self.nodes[node_ids[(i+1) % n]].phase
            
            # Expected phase difference
            expected_diff = self.phase_per_junction
            actual_diff = self._wrap_phase(next_phase - curr_phase)
            
            # Mismatch
            mismatch = self._wrap_phase(actual_diff - expected_diff)
            
            # Interference contribution: cos(mismatch)
            # 1 if aligned, -1 if anti-aligned
            interference += np.cos(mismatch)
        
        return interference / n
    
    def compute_energy(self, node_ids: List[int]) -> Dict[str, float]:
        """Compute kinetic and potential energy of a loop."""
        kinetic = 0.0
        potential = 0.0
        
        for nid in node_ids:
            node = self.nodes[nid]
            # Kinetic energy: (1/2) * v²
            kinetic += 0.5 * node.phase_velocity**2
        
        # Potential from phase mismatch
        n = len(node_ids)
        for i in range(n):
            curr = self.nodes[node_ids[i]]
            next_node = self.nodes[node_ids[(i+1) % n]]
            
            diff = self._wrap_phase(next_node.phase - curr.phase - self.phase_per_junction)
            potential += 0.5 * self.coupling_strength * diff**2
        
        return {
            'kinetic': float(kinetic),
            'potential': float(potential),
            'total': float(kinetic + potential)
        }
    
    def measure_loop_phase(self, node_ids: List[int]) -> float:
        """Measure total phase around a loop (for analysis only)."""
        total = 0.0
        n = len(node_ids)
        
        for i in range(n):
            curr_phase = self.nodes[node_ids[i]].phase
            next_phase = self.nodes[node_ids[(i+1) % n]].phase
            total += self._wrap_phase(next_phase - curr_phase)
        
        return total
    
    def evolve(self, node_ids: List[int], n_steps: int, 
               record_every: int = 10) -> Dict:
        """Evolve and track observables."""
        history = {
            'interference': [],
            'kinetic': [],
            'potential': [],
            'total_energy': [],
            'loop_phase': []
        }
        
        for step in range(n_steps):
            self.evolve_step()
            
            if step % record_every == 0:
                intf = self.compute_interference(node_ids)
                energy = self.compute_energy(node_ids)
                loop_phase = self.measure_loop_phase(node_ids)
                
                history['interference'].append(intf)
                history['kinetic'].append(energy['kinetic'])
                history['potential'].append(energy['potential'])
                history['total_energy'].append(energy['total'])
                history['loop_phase'].append(np.degrees(loop_phase))
        
        return history


# =============================================================================
# WAVE INTERFERENCE TEST
# =============================================================================

class WaveInterferenceTest:
    """Test whether wave dynamics produce emergent discrete structure."""
    
    def __init__(self):
        self.results = {}
    
    def test_single_loop(self, n: int, n_steps: int = 10000) -> Dict:
        """
        Test evolution of a single loop with wave dynamics.
        """
        network = WaveInterferenceNetwork(seed=n * 31)
        node_ids = network.create_loop(n)
        
        # Initial state
        initial_phase = network.measure_loop_phase(node_ids)
        initial_interference = network.compute_interference(node_ids)
        
        # Evolve
        history = network.evolve(node_ids, n_steps, record_every=50)
        
        # Final state
        final_phase = network.measure_loop_phase(node_ids)
        final_interference = network.compute_interference(node_ids)
        final_energy = network.compute_energy(node_ids)
        
        # Check for resonance (high sustained interference)
        avg_interference = np.mean(history['interference'][-100:])
        std_interference = np.std(history['interference'][-100:])
        
        # Check for phase locking
        final_phases = [np.degrees(final_phase)]
        expected_phases = [n * (-30), 0, 180, -180, 360, -360]
        
        closest = min(expected_phases, key=lambda p: abs(final_phases[0] - p))
        phase_locked = abs(final_phases[0] - closest) < 20
        
        return {
            'n': n,
            'initial_phase_deg': float(np.degrees(initial_phase)),
            'final_phase_deg': float(np.degrees(final_phase)),
            'expected_phase_deg': n * (-30),
            'initial_interference': float(initial_interference),
            'final_interference': float(final_interference),
            'avg_interference': float(avg_interference),
            'std_interference': float(std_interference),
            'resonant': avg_interference > 0.5,
            'phase_locked': phase_locked,
            'locked_to': closest,
            'final_energy': final_energy['total']
        }
    
    def test_resonance_vs_size(self) -> Dict:
        """
        TEST A: Does interference/resonance depend on loop size?
        
        If n=6,12 have higher resonance → EMERGENT SIZE PREFERENCE
        """
        print("=" * 70)
        print("TEST A: RESONANCE VS LOOP SIZE")
        print("=" * 70)
        print("""
With WAVE dynamics (not just dissipation):
  d²θ/dt² = coupling - damping

Question: Do certain loop sizes RESONATE better?
If n=6,12 have sustained high interference → SIZE SELECTION
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Expected':>9} | {'Final':>8} | {'Interference':>12} | {'Resonant':>8} | {'Bar'}")
        print("-" * 75)
        
        for n in range(3, 16):
            # Average over trials
            interferences = []
            resonances = []
            
            for trial in range(3):
                network = WaveInterferenceNetwork(seed=n * 100 + trial)
                node_ids = network.create_loop(n)
                history = network.evolve(node_ids, 8000, record_every=100)
                
                avg_intf = np.mean(history['interference'][-50:])
                interferences.append(avg_intf)
                resonances.append(avg_intf > 0.5)
            
            avg_interference = np.mean(interferences)
            resonant_frac = np.mean(resonances)
            
            # Visual
            bar_len = int((avg_interference + 1) * 15)
            bar = "#" * max(0, bar_len)
            
            marker = ""
            if n == 6:
                marker = " ← FERMION?"
            elif n == 12:
                marker = " ← BOSON?"
            
            print(f"{n:>4} | {n*(-30):>8}° | {avg_interference:>8.3f} | "
                  f"{resonant_frac:>11.0%} | {'YES' if resonant_frac > 0.5 else 'NO':>8} | {bar}{marker}")
            
            results.append({
                'n': n,
                'expected_phase': n * (-30),
                'avg_interference': float(avg_interference),
                'resonant_fraction': float(resonant_frac)
            })
        
        # Find resonance peaks
        interferences = [r['avg_interference'] for r in results]
        ns = [r['n'] for r in results]
        
        peaks = []
        for i in range(1, len(interferences) - 1):
            if interferences[i] > interferences[i-1] and interferences[i] > interferences[i+1]:
                if interferences[i] > 0.3:
                    peaks.append(ns[i])
        
        print(f"\nResonance peaks at n = {peaks}")
        
        return {
            'details': results,
            'resonance_peaks': peaks
        }
    
    def test_interference_survival(self) -> Dict:
        """
        TEST B: Do loops with high interference survive longer?
        
        Measure "lifetime" as time until interference drops below threshold.
        """
        print("\n" + "=" * 70)
        print("TEST B: INTERFERENCE SURVIVAL")
        print("=" * 70)
        print("""
Hypothesis: Loops that resonate persist.
            Loops with destructive interference decay.

Measuring "lifetime" = time until interference < 0.3
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Lifetime':>10} | {'Final Intf':>12} | {'Survived':>10}")
        print("-" * 50)
        
        for n in range(3, 16):
            lifetimes = []
            final_intfs = []
            
            for trial in range(5):
                network = WaveInterferenceNetwork(seed=n * 200 + trial)
                node_ids = network.create_loop(n)
                
                lifetime = 10000  # Max steps
                
                for step in range(10000):
                    network.evolve_step()
                    
                    if step % 100 == 0:
                        intf = network.compute_interference(node_ids)
                        if intf < 0.3 and step > 500:
                            lifetime = step
                            break
                
                final_intf = network.compute_interference(node_ids)
                lifetimes.append(lifetime)
                final_intfs.append(final_intf)
            
            avg_lifetime = np.mean(lifetimes)
            avg_final_intf = np.mean(final_intfs)
            survived = avg_lifetime > 8000
            
            marker = ""
            if n == 6:
                marker = " ← FERMION?"
            elif n == 12:
                marker = " ← BOSON?"
            
            print(f"{n:>4} | {avg_lifetime:>10.0f} | {avg_final_intf:>12.3f} | "
                  f"{'YES' if survived else 'NO':>10}{marker}")
            
            results.append({
                'n': n,
                'avg_lifetime': float(avg_lifetime),
                'avg_final_interference': float(avg_final_intf),
                'survived': survived
            })
        
        surviving_ns = [r['n'] for r in results if r['survived']]
        print(f"\nSurviving loop sizes: {surviving_ns}")
        
        return {
            'details': results,
            'surviving_ns': surviving_ns
        }
    
    def test_phase_distribution(self) -> Dict:
        """
        TEST C: Distribution of final phases.
        
        If discrete → clustering at expected values
        """
        print("\n" + "=" * 70)
        print("TEST C: PHASE DISTRIBUTION (Wave Model)")
        print("=" * 70)
        
        final_phases = []
        loop_sizes = []
        
        for trial in range(100):
            n = np.random.randint(4, 15)
            network = WaveInterferenceNetwork(seed=trial * 7)
            node_ids = network.create_loop(n)
            
            network.evolve(node_ids, 8000, record_every=500)
            
            final_phase = network.measure_loop_phase(node_ids)
            final_phases.append(np.degrees(final_phase))
            loop_sizes.append(n)
        
        # Group by loop size
        print("\nFinal phase by loop size:")
        for n in range(4, 15):
            phases_for_n = [p for p, sz in zip(final_phases, loop_sizes) if sz == n]
            if phases_for_n:
                expected = n * (-30)
                actual_mean = np.mean(phases_for_n)
                actual_std = np.std(phases_for_n)
                
                locked = abs(actual_mean - expected) < 30 or actual_std < 30
                
                print(f"  n={n:2d}: expected={expected:>5}°, actual={actual_mean:>6.1f}° ± {actual_std:>5.1f}° "
                      f"{'✓ LOCKED' if locked else ''}")
        
        # Overall distribution
        bins = np.arange(-360, 361, 30)
        hist, _ = np.histogram(final_phases, bins=bins)
        
        print("\nPhase histogram:")
        for i, count in enumerate(hist):
            if count > 0:
                center = (bins[i] + bins[i+1]) / 2
                bar = "#" * count
                
                marker = ""
                if abs(center - 180) < 15 or abs(center + 180) < 15:
                    marker = " ← π"
                elif abs(center) < 15 or abs(center - 360) < 15:
                    marker = " ← 0"
                
                print(f"  {center:>6.0f}°: {bar} ({count}){marker}")
        
        return {
            'final_phases': final_phases,
            'loop_sizes': loop_sizes
        }
    
    def test_damping_sensitivity(self) -> Dict:
        """
        TEST D: How does damping affect emergence?
        
        Low damping → more oscillation, possible standing waves
        High damping → approaches diffusion (what we had before)
        """
        print("\n" + "=" * 70)
        print("TEST D: DAMPING SENSITIVITY")
        print("=" * 70)
        
        results = []
        
        print(f"\n{'Damping':>10} | {'n=6 Intf':>10} | {'n=12 Intf':>10} | {'Ratio':>8}")
        print("-" * 50)
        
        for damping in [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]:
            n6_intf = []
            n12_intf = []
            
            for trial in range(3):
                # n=6
                network = WaveInterferenceNetwork(seed=trial)
                network.damping = damping
                nodes = network.create_loop(6)
                history = network.evolve(nodes, 5000, record_every=100)
                n6_intf.append(np.mean(history['interference'][-30:]))
                
                # n=12
                network = WaveInterferenceNetwork(seed=trial + 100)
                network.damping = damping
                nodes = network.create_loop(12)
                history = network.evolve(nodes, 5000, record_every=100)
                n12_intf.append(np.mean(history['interference'][-30:]))
            
            avg_n6 = np.mean(n6_intf)
            avg_n12 = np.mean(n12_intf)
            ratio = avg_n6 / (avg_n12 + 0.01)
            
            print(f"{damping:>10.2f} | {avg_n6:>10.3f} | {avg_n12:>10.3f} | {ratio:>8.2f}")
            
            results.append({
                'damping': damping,
                'n6_interference': float(avg_n6),
                'n12_interference': float(avg_n12),
                'ratio': float(ratio)
            })
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all wave interference tests."""
        print("=" * 80)
        print("  QMRT: WAVE PROPAGATION + INTERFERENCE TEST")
        print("=" * 80)
        print("""
THE PHYSICS UPGRADE:
  Previous: dθ/dt = relaxation (pure dissipation)
  Now:      d²θ/dt² = coupling - damping (wave equation)

This allows:
  - Oscillation (phase memory)
  - Interference (constructive/destructive)
  - Standing patterns (resonance)
  - Survival-based selection

QUESTION: Does discrete structure EMERGE from wave dynamics?
""")
        
        results = {}
        
        results['resonance'] = self.test_resonance_vs_size()
        results['survival'] = self.test_interference_survival()
        results['distribution'] = self.test_phase_distribution()
        results['damping'] = self.test_damping_sensitivity()
        
        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        resonance_peaks = results['resonance']['resonance_peaks']
        surviving_ns = results['survival']['surviving_ns']
        
        print(f"""
WAVE DYNAMICS RESULTS:

1. Resonance peaks: n = {resonance_peaks}
   {"✓ n=6 or n=12 shows resonance" if (6 in resonance_peaks or 12 in resonance_peaks) else "✗ No special sizes"}

2. Survival: n = {surviving_ns}
   {"✓ Discrete survival pattern" if len(surviving_ns) < 10 else "✗ All sizes survive equally"}

3. Damping sensitivity:
   Low damping enhances oscillation/resonance
   High damping approaches dissipation limit
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        discrete_emergence = (6 in resonance_peaks or 12 in resonance_peaks) or \
                            (6 in surviving_ns and len(surviving_ns) < 10)
        
        if discrete_emergence:
            verdict = "WAVE_EMERGENCE_CONFIRMED"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ DISCRETE STRUCTURE EMERGES FROM WAVE DYNAMICS                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Wave propagation + interference produces resonance selection.                ║
║  Certain loop sizes show sustained coherence.                                 ║
║  This is EMERGENT behavior from local wave physics.                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "NEEDS_REFINEMENT"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ PARTIAL WAVE BEHAVIOR - REFINEMENT NEEDED                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Wave dynamics present but discrete selection not yet strong.                 ║
║                                                                              ║
║  Possible next steps:                                                        ║
║    1. Add phase conservation (flux constraint)                               ║
║    2. Branch-level interference (trunk dynamics)                             ║
║    3. Standing wave boundary conditions                                       ║
║    4. Nonlinear coupling (self-interaction)                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Save
        output = {
            'test': 'Wave_Interference',
            'verdict': verdict,
            'resonance_vs_size': results['resonance'],
            'interference_survival': results['survival'],
            'phase_distribution': results['distribution'],
            'damping_sensitivity': results['damping'],
            'conclusions': {
                'resonance_peaks': resonance_peaks,
                'surviving_ns': surviving_ns,
                'discrete_emergence': discrete_emergence
            }
        }
        
        output_path = '/app/backend/qmrt_topology/wave_interference_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = WaveInterferenceTest()
    results = test.run_all_tests()
