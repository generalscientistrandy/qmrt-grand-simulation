"""
QMRT: SYMPLECTIC DYNAMICS WITH ENERGY FUNCTIONAL
=================================================

CRITICAL FIXES:
1. SYMPLECTIC INTEGRATOR (Störmer-Verlet) - conserves energy
2. ENERGY FUNCTIONAL: E = (∇θ)² + V(θ)
3. WEAK NONLINEARITY - phase locking, self-interaction

GOAL: Test if STABILITY emerges with correct physics.

Current status:
  ✅ Geometry
  ✅ Topology  
  ✅ Emergence
  ❌ Stability (need to prove)
  ❌ Energy correctness (need symplectic)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json
from collections import Counter


# =============================================================================
# SYMPLECTIC PHASE FIELD
# =============================================================================

@dataclass
class PhaseNode:
    """Node in phase field with position and momentum."""
    id: int
    position: np.ndarray
    
    # Canonical variables
    theta: float = 0.0      # Phase (position-like)
    pi: float = 0.0         # Conjugate momentum
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=float)


class SymplecticNetwork:
    """
    Network with SYMPLECTIC dynamics and proper ENERGY FUNCTIONAL.
    
    Hamiltonian:
      H = Σ_i (π_i²/2m) + Σ_<ij> K(1 - cos(θ_i - θ_j - φ_ij)) + Σ_i V(θ_i)
    
    Where:
      - First term: kinetic energy
      - Second term: gradient energy (XY model)
      - Third term: potential energy (self-interaction/nonlinearity)
    
    Dynamics via Störmer-Verlet (symplectic, energy-conserving).
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        
        self.nodes: Dict[int, PhaseNode] = {}
        self.edges: List[Tuple[int, int]] = []
        self.adjacency: Dict[int, List[int]] = {}
        
        self.next_node_id = 0
        
        # PHYSICS PARAMETERS
        self.mass = 1.0                    # Inertia
        self.K = 2.0                       # Coupling (gradient energy)
        self.V_strength = 0.0              # Potential strength (nonlinearity)
        self.V_order = 1                   # Potential periodicity
        
        # Geometric phase offset
        self.phi_offset = -np.pi / 6       # -30 degrees per junction
        
        # Time step (smaller for stability)
        self.dt = 0.002
    
    # =========================================================================
    # NETWORK CONSTRUCTION
    # =========================================================================
    
    def add_node(self, position: np.ndarray, theta: float = None,
                 pi: float = None) -> int:
        nid = self.next_node_id
        
        if theta is None:
            theta = np.random.random() * 2 * np.pi
        if pi is None:
            pi = (np.random.random() - 0.5) * 0.5
        
        self.nodes[nid] = PhaseNode(nid, position, theta, pi)
        self.adjacency[nid] = []
        self.next_node_id += 1
        return nid
    
    def add_edge(self, i: int, j: int):
        self.edges.append((i, j))
        self.adjacency[i].append(j)
        self.adjacency[j].append(i)
    
    def create_loop(self, n: int, center: np.ndarray = None,
                    radius: float = 1.0, initial_winding: int = 0) -> List[int]:
        if center is None:
            center = np.array([0.0, 0.0])
        
        node_ids = []
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        for i, angle in enumerate(angles):
            pos = center + radius * np.array([np.cos(angle), np.sin(angle)])
            
            # Initialize with winding
            theta = (2 * np.pi * initial_winding * i / n) % (2 * np.pi)
            # Small random momentum
            pi = (np.random.random() - 0.5) * 0.1
            
            nid = self.add_node(pos, theta, pi)
            node_ids.append(nid)
        
        for i in range(n):
            self.add_edge(node_ids[i], node_ids[(i+1) % n])
        
        return node_ids
    
    # =========================================================================
    # PHASE OPERATIONS
    # =========================================================================
    
    def wrap_phase(self, theta: float) -> float:
        """Wrap to [0, 2π)."""
        return theta % (2 * np.pi)
    
    def phase_diff(self, theta_i: float, theta_j: float) -> float:
        """Continuous phase difference in [-π, π]."""
        diff = theta_j - theta_i
        while diff > np.pi:
            diff -= 2 * np.pi
        while diff < -np.pi:
            diff += 2 * np.pi
        return diff
    
    # =========================================================================
    # HAMILTONIAN AND FORCES
    # =========================================================================
    
    def compute_kinetic_energy(self) -> float:
        """T = Σ π²/2m"""
        return sum(0.5 * node.pi**2 / self.mass for node in self.nodes.values())
    
    def compute_gradient_energy(self) -> float:
        """
        U_grad = Σ_<ij> K(1 - cos(θ_i - θ_j - φ))
        
        This is the XY model energy with geometric offset.
        """
        energy = 0.0
        for i, j in self.edges:
            theta_i = self.nodes[i].theta
            theta_j = self.nodes[j].theta
            diff = self.phase_diff(theta_i, theta_j) - self.phi_offset
            energy += self.K * (1 - np.cos(diff))
        return energy
    
    def compute_potential_energy(self) -> float:
        """
        V = Σ_i V_strength * (1 - cos(V_order * θ_i))
        
        Self-interaction / on-site potential.
        Creates preferred phase values (nonlinearity).
        """
        if self.V_strength == 0:
            return 0.0
        energy = 0.0
        for node in self.nodes.values():
            energy += self.V_strength * (1 - np.cos(self.V_order * node.theta))
        return energy
    
    def compute_total_energy(self) -> Dict[str, float]:
        """Compute full Hamiltonian."""
        T = self.compute_kinetic_energy()
        U_grad = self.compute_gradient_energy()
        V = self.compute_potential_energy()
        
        return {
            'kinetic': float(T),
            'gradient': float(U_grad),
            'potential': float(V),
            'total': float(T + U_grad + V)
        }
    
    def compute_force(self, node_id: int) -> float:
        """
        Force on node i: F_i = -∂H/∂θ_i
        
        From gradient energy:
          F_grad = Σ_j K * sin(θ_i - θ_j - φ)
        
        From potential:
          F_pot = V_strength * V_order * sin(V_order * θ_i)
        """
        node = self.nodes[node_id]
        
        # Gradient force from neighbors
        F_grad = 0.0
        for neighbor_id in self.adjacency[node_id]:
            neighbor = self.nodes[neighbor_id]
            diff = self.phase_diff(node.theta, neighbor.theta) - self.phi_offset
            F_grad += self.K * np.sin(diff)
        
        # Potential force (on-site)
        F_pot = self.V_strength * self.V_order * np.sin(self.V_order * node.theta)
        
        return F_grad + F_pot
    
    # =========================================================================
    # STÖRMER-VERLET INTEGRATOR (SYMPLECTIC)
    # =========================================================================
    
    def evolve_step(self):
        """
        Störmer-Verlet integration (position Verlet form):
        
        1. θ(t + dt/2) = θ(t) + (dt/2) * π(t)/m
        2. π(t + dt) = π(t) + dt * F(θ(t + dt/2))
        3. θ(t + dt) = θ(t + dt/2) + (dt/2) * π(t + dt)/m
        
        This is SYMPLECTIC and conserves energy to O(dt²).
        """
        dt = self.dt
        m = self.mass
        
        # Step 1: Half-step position update
        for node in self.nodes.values():
            node.theta += 0.5 * dt * node.pi / m
            node.theta = self.wrap_phase(node.theta)
        
        # Step 2: Full-step momentum update (using half-step positions)
        forces = {}
        for nid in self.nodes:
            forces[nid] = self.compute_force(nid)
        
        for nid, node in self.nodes.items():
            node.pi += dt * forces[nid]
        
        # Step 3: Second half-step position update
        for node in self.nodes.values():
            node.theta += 0.5 * dt * node.pi / m
            node.theta = self.wrap_phase(node.theta)
    
    # =========================================================================
    # MEASUREMENTS
    # =========================================================================
    
    def compute_winding(self, node_ids: List[int]) -> float:
        """Winding number around a loop."""
        n = len(node_ids)
        total = 0.0
        
        for i in range(n):
            theta_i = self.nodes[node_ids[i]].theta
            theta_j = self.nodes[node_ids[(i+1) % n]].theta
            total += self.phase_diff(theta_i, theta_j)
        
        return total / (2 * np.pi)
    
    def compute_order_parameter(self, node_ids: List[int]) -> float:
        """
        Order parameter: |Σ e^(iθ)| / N
        
        = 1 if all phases aligned
        = 0 if random phases
        """
        if not node_ids:
            return 0.0
        
        psi = sum(np.exp(1j * self.nodes[nid].theta) for nid in node_ids)
        return abs(psi) / len(node_ids)
    
    def evolve(self, node_ids: List[int], n_steps: int,
               record_every: int = 20) -> Dict:
        """Evolve and track observables."""
        history = {
            'time': [],
            'kinetic': [],
            'gradient': [],
            'potential': [],
            'total': [],
            'winding': [],
            'order': []
        }
        
        for step in range(n_steps):
            self.evolve_step()
            
            if step % record_every == 0:
                E = self.compute_total_energy()
                W = self.compute_winding(node_ids)
                psi = self.compute_order_parameter(node_ids)
                
                history['time'].append(step * self.dt)
                history['kinetic'].append(E['kinetic'])
                history['gradient'].append(E['gradient'])
                history['potential'].append(E['potential'])
                history['total'].append(E['total'])
                history['winding'].append(W)
                history['order'].append(psi)
        
        return history


# =============================================================================
# TEST SUITE
# =============================================================================

class SymplecticTest:
    """Test symplectic dynamics with energy conservation."""
    
    def __init__(self):
        self.results = {}
    
    def test_energy_conservation(self) -> Dict:
        """
        TEST A: Does the symplectic integrator conserve energy?
        """
        print("=" * 70)
        print("TEST A: ENERGY CONSERVATION (SYMPLECTIC)")
        print("=" * 70)
        
        network = SymplecticNetwork(seed=42)
        node_ids = network.create_loop(6, initial_winding=1)
        
        # Initial energy
        E0 = network.compute_total_energy()
        
        # Evolve for a long time
        history = network.evolve(node_ids, n_steps=20000, record_every=100)
        
        # Final energy
        Ef = network.compute_total_energy()
        
        # Statistics
        energies = history['total']
        E_mean = np.mean(energies)
        E_std = np.std(energies)
        drift = abs(Ef['total'] - E0['total']) / E0['total']
        
        print(f"\nInitial energy: {E0['total']:.6f}")
        print(f"Final energy:   {Ef['total']:.6f}")
        print(f"Mean energy:    {E_mean:.6f}")
        print(f"Std dev:        {E_std:.6f}")
        print(f"Drift:          {drift:.4%}")
        
        conserved = drift < 0.01
        print(f"\n✓ Energy CONSERVED" if conserved else "✗ Energy NOT conserved")
        
        return {
            'E_initial': E0['total'],
            'E_final': Ef['total'],
            'drift': drift,
            'conserved': conserved
        }
    
    def test_winding_preservation(self) -> Dict:
        """
        TEST B: Is winding number preserved?
        """
        print("\n" + "=" * 70)
        print("TEST B: WINDING NUMBER PRESERVATION")
        print("=" * 70)
        
        results = []
        
        print(f"\n{'n':>4} | {'Init W':>8} | {'Final W':>8} | {'Error':>8} | {'Preserved':>10}")
        print("-" * 50)
        
        for n in [4, 6, 8, 10, 12]:
            for init_w in [0, 1, 2]:
                network = SymplecticNetwork(seed=n * 10 + init_w)
                node_ids = network.create_loop(n, initial_winding=init_w)
                
                W0 = network.compute_winding(node_ids)
                history = network.evolve(node_ids, n_steps=10000, record_every=200)
                Wf = network.compute_winding(node_ids)
                
                error = abs(round(Wf) - round(W0))
                preserved = error < 0.5
                
                print(f"{n:>4} | {W0:>8.2f} | {Wf:>8.2f} | {error:>8.2f} | "
                      f"{'YES' if preserved else 'NO':>10}")
                
                results.append({
                    'n': n,
                    'init_W': round(W0),
                    'final_W': round(Wf),
                    'preserved': preserved
                })
        
        rate = sum(1 for r in results if r['preserved']) / len(results)
        print(f"\nPreservation rate: {rate:.0%}")
        
        return results
    
    def test_stability_vs_size(self) -> Dict:
        """
        TEST C: Which loop sizes are most STABLE?
        
        Measure energy fluctuations for different sizes.
        Lower fluctuation = more stable.
        """
        print("\n" + "=" * 70)
        print("TEST C: STABILITY VS LOOP SIZE")
        print("=" * 70)
        print("""
Measuring energy fluctuations as a proxy for stability.
Lower σ(E)/E = more stable oscillation pattern.
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'<E>':>10} | {'σ(E)':>10} | {'σ/E':>10} | {'Stable':>8}")
        print("-" * 55)
        
        for n in range(3, 16):
            network = SymplecticNetwork(seed=n * 7)
            node_ids = network.create_loop(n, initial_winding=1)
            
            history = network.evolve(node_ids, n_steps=15000, record_every=50)
            
            # Exclude initial transient
            energies = history['total'][50:]
            
            E_mean = np.mean(energies)
            E_std = np.std(energies)
            stability = E_std / (E_mean + 0.01)
            
            stable = stability < 0.1
            
            marker = ""
            if n == 6:
                marker = " ← FERMION?"
            elif n == 12:
                marker = " ← BOSON?"
            
            print(f"{n:>4} | {E_mean:>10.3f} | {E_std:>10.4f} | {stability:>10.4f} | "
                  f"{'YES' if stable else 'NO':>8}{marker}")
            
            results.append({
                'n': n,
                'E_mean': float(E_mean),
                'E_std': float(E_std),
                'stability': float(stability),
                'stable': stable
            })
        
        # Find most stable sizes
        sorted_by_stability = sorted(results, key=lambda x: x['stability'])
        most_stable = [r['n'] for r in sorted_by_stability[:3]]
        
        print(f"\nMost stable sizes: {most_stable}")
        
        return results
    
    def test_nonlinearity_effect(self) -> Dict:
        """
        TEST D: Effect of nonlinearity (self-interaction).
        
        Does adding V(θ) create preferred configurations?
        """
        print("\n" + "=" * 70)
        print("TEST D: NONLINEARITY EFFECT")
        print("=" * 70)
        print("""
Testing effect of on-site potential V(θ).
This creates preferred phase values (nonlinear self-interaction).
""")
        
        results = []
        
        print(f"\n{'V_strength':>12} | {'V_order':>8} | {'Order Param':>12} | {'E_final':>10}")
        print("-" * 55)
        
        for V_strength in [0, 0.1, 0.5, 1.0, 2.0]:
            for V_order in [1, 2, 6]:
                if V_strength == 0 and V_order > 1:
                    continue
                
                network = SymplecticNetwork(seed=42)
                network.V_strength = V_strength
                network.V_order = V_order
                
                node_ids = network.create_loop(6, initial_winding=1)
                
                history = network.evolve(node_ids, n_steps=10000, record_every=100)
                
                order_param = np.mean(history['order'][-30:])
                E_final = np.mean(history['total'][-30:])
                
                print(f"{V_strength:>12.1f} | {V_order:>8} | {order_param:>12.3f} | {E_final:>10.3f}")
                
                results.append({
                    'V_strength': V_strength,
                    'V_order': V_order,
                    'order_param': float(order_param),
                    'E_final': float(E_final)
                })
        
        return results
    
    def test_geometric_winding(self) -> Dict:
        """
        TEST E: Does geometric winding (n × -30°) emerge or persist?
        """
        print("\n" + "=" * 70)
        print("TEST E: GEOMETRIC WINDING")
        print("=" * 70)
        print("""
The geometric phase offset is -30° per junction.
For n junctions: expected winding = n × (-30°) / 360° = -n/12

Testing if this winding is STABLE.
""")
        
        results = []
        
        print(f"\n{'n':>4} | {'Expected W':>10} | {'Actual W':>10} | {'Match':>8}")
        print("-" * 45)
        
        for n in [3, 6, 9, 12, 15, 18]:
            expected_w = -n / 12  # From -30° per junction
            
            network = SymplecticNetwork(seed=n)
            
            # Initialize with geometric winding
            node_ids = []
            center = np.array([0.0, 0.0])
            for i in range(n):
                angle = 2 * np.pi * i / n
                pos = center + np.array([np.cos(angle), np.sin(angle)])
                
                # Initialize phase to match expected winding
                theta = (2 * np.pi * expected_w * i / n) % (2 * np.pi)
                nid = network.add_node(pos, theta, pi=0.01)
                node_ids.append(nid)
            
            for i in range(n):
                network.add_edge(node_ids[i], node_ids[(i+1) % n])
            
            W0 = network.compute_winding(node_ids)
            
            history = network.evolve(node_ids, n_steps=15000, record_every=200)
            
            Wf = network.compute_winding(node_ids)
            
            match = abs(Wf - expected_w) < 0.2
            
            marker = ""
            if n == 6:
                marker = " ← W=-0.5 (FERMION)"
            elif n == 12:
                marker = " ← W=-1 (BOSON)"
            
            print(f"{n:>4} | {expected_w:>10.3f} | {Wf:>10.3f} | "
                  f"{'YES' if match else 'NO':>8}{marker}")
            
            results.append({
                'n': n,
                'expected_W': expected_w,
                'actual_W': float(Wf),
                'match': match
            })
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all symplectic tests."""
        print("=" * 80)
        print("  QMRT: SYMPLECTIC DYNAMICS TEST")
        print("=" * 80)
        print("""
PHYSICS:
  Hamiltonian: H = T + U_grad + V
    T = Σ π²/2m                         (kinetic)
    U = Σ K(1 - cos(Δθ - φ))           (gradient)
    V = Σ V_str(1 - cos(V_ord × θ))     (potential/nonlinearity)

  Integrator: Störmer-Verlet (symplectic)

GOAL: Verify energy conservation and test stability.
""")
        
        results = {}
        
        results['energy'] = self.test_energy_conservation()
        results['winding'] = self.test_winding_preservation()
        results['stability'] = self.test_stability_vs_size()
        results['nonlinearity'] = self.test_nonlinearity_effect()
        results['geometric'] = self.test_geometric_winding()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        energy_ok = results['energy']['conserved']
        winding_rate = sum(1 for r in results['winding'] if r['preserved']) / len(results['winding'])
        stable_sizes = [r['n'] for r in results['stability'] if r['stable']]
        geo_matches = [r['n'] for r in results['geometric'] if r['match']]
        
        print(f"""
RESULTS:

1. Energy conservation: {results['energy']['drift']:.4%} drift
   {"✓ SYMPLECTIC WORKING" if energy_ok else "✗ Still leaking"}

2. Winding preservation: {winding_rate:.0%}
   {"✓ TOPOLOGY STABLE" if winding_rate > 0.8 else "✗ Winding unstable"}

3. Most stable sizes: {stable_sizes[:5]}

4. Geometric winding preserved for: n = {geo_matches}
   {"✓ n=6 (fermion) preserves W=-0.5" if 6 in geo_matches else "✗ n=6 not preserving geometric W"}
""")
        
        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        if energy_ok and winding_rate > 0.8:
            verdict = "SYMPLECTIC_WORKING"
            if 6 in geo_matches:
                verdict = "FERMION_WINDING_STABLE"
                print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ FERMION WINDING IS STABLE                                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  1. Symplectic integrator conserves energy                                    ║
║  2. Winding number is topologically preserved                                 ║
║  3. Geometric winding W = -0.5 persists for n=6                               ║
║                                                                              ║
║  This is STABILITY from correct physics!                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
            else:
                print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ SYMPLECTIC DYNAMICS WORKING                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  1. Energy is conserved                                                       ║
║  2. Winding number is stable                                                  ║
║  3. But geometric winding (n × -30°) not yet preserved                       ║
║                                                                              ║
║  Need additional physics for geometric phase to persist.                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        else:
            verdict = "NEEDS_REFINEMENT"
            print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ DYNAMICS NEED REFINEMENT                                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Save
        output = {
            'test': 'Symplectic_Dynamics',
            'verdict': verdict,
            'energy_conservation': results['energy'],
            'winding_preservation': results['winding'],
            'stability_vs_size': results['stability'],
            'nonlinearity_effect': results['nonlinearity'],
            'geometric_winding': results['geometric'],
            'conclusions': {
                'energy_conserved': energy_ok,
                'winding_rate': winding_rate,
                'stable_sizes': stable_sizes,
                'geometric_matches': geo_matches
            }
        }
        
        output_path = '/app/backend/qmrt_topology/symplectic_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return output


if __name__ == "__main__":
    test = SymplecticTest()
    results = test.run_all_tests()
