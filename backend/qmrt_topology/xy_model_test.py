"""
QMRT: CORRECTED SYMPLECTIC INTEGRATOR
=====================================

PROBLEM: Energy was still growing (17000% drift)
CAUSE: Force computation had sign errors

FIX: Use standard XY model Hamiltonian with correct derivatives.

H = Σ_i π_i²/2 - K Σ_<ij> cos(θ_i - θ_j)

dH/dθ_i = K Σ_j sin(θ_i - θ_j)
F_i = -dH/dθ_i = -K Σ_j sin(θ_i - θ_j)

Simple, well-tested physics.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List
import json


@dataclass
class Node:
    theta: float = 0.0  # Phase
    pi: float = 0.0     # Momentum


class XYModel:
    """
    Standard XY model with symplectic integration.
    
    H = Σ_i π_i²/2 - K Σ_<ij> cos(θ_i - θ_j - φ)
    
    This is textbook physics that MUST conserve energy.
    """
    
    def __init__(self, n: int, K: float = 1.0, phi: float = 0.0):
        self.n = n
        self.K = K
        self.phi = phi  # Geometric offset
        
        # Create ring
        self.nodes = [Node() for _ in range(n)]
        
        self.dt = 0.01
    
    def initialize_winding(self, W: int):
        """Initialize with winding number W."""
        for i in range(self.n):
            self.nodes[i].theta = (2 * np.pi * W * i / self.n) % (2 * np.pi)
            self.nodes[i].pi = 0.0
    
    def initialize_random(self):
        """Random initialization."""
        for node in self.nodes:
            node.theta = np.random.random() * 2 * np.pi
            node.pi = (np.random.random() - 0.5) * 0.5
    
    def wrap(self, theta):
        return theta % (2 * np.pi)
    
    def diff(self, theta_i, theta_j):
        """Phase difference in [-π, π]."""
        d = theta_j - theta_i
        while d > np.pi: d -= 2*np.pi
        while d < -np.pi: d += 2*np.pi
        return d
    
    def kinetic_energy(self):
        return sum(0.5 * node.pi**2 for node in self.nodes)
    
    def potential_energy(self):
        """V = -K Σ cos(θ_i - θ_{i+1} - φ)"""
        V = 0.0
        for i in range(self.n):
            j = (i + 1) % self.n
            d = self.diff(self.nodes[i].theta, self.nodes[j].theta) - self.phi
            V += -self.K * np.cos(d)
        return V
    
    def total_energy(self):
        return self.kinetic_energy() + self.potential_energy()
    
    def force(self, i):
        """
        F_i = -∂V/∂θ_i
        
        V = -K Σ_<jk> cos(θ_j - θ_k - φ)
        
        Only terms involving i:
          -K cos(θ_{i-1} - θ_i - φ)  → derivative: -K sin(θ_{i-1} - θ_i - φ)
          -K cos(θ_i - θ_{i+1} - φ)  → derivative: +K sin(θ_i - θ_{i+1} - φ)
        
        F_i = K sin(θ_{i-1} - θ_i - φ) - K sin(θ_i - θ_{i+1} - φ)
        """
        i_prev = (i - 1) % self.n
        i_next = (i + 1) % self.n
        
        d_prev = self.diff(self.nodes[i_prev].theta, self.nodes[i].theta) - self.phi
        d_next = self.diff(self.nodes[i].theta, self.nodes[i_next].theta) - self.phi
        
        F = self.K * np.sin(d_prev) - self.K * np.sin(d_next)
        return F
    
    def step(self):
        """Störmer-Verlet step."""
        dt = self.dt
        
        # Half-step θ
        for node in self.nodes:
            node.theta += 0.5 * dt * node.pi
            node.theta = self.wrap(node.theta)
        
        # Full-step π
        forces = [self.force(i) for i in range(self.n)]
        for i, node in enumerate(self.nodes):
            node.pi += dt * forces[i]
        
        # Half-step θ
        for node in self.nodes:
            node.theta += 0.5 * dt * node.pi
            node.theta = self.wrap(node.theta)
    
    def winding(self):
        """Compute winding number."""
        total = 0.0
        for i in range(self.n):
            j = (i + 1) % self.n
            total += self.diff(self.nodes[i].theta, self.nodes[j].theta)
        return total / (2 * np.pi)
    
    def evolve(self, n_steps, record_every=10):
        history = {'T': [], 'V': [], 'E': [], 'W': []}
        
        for step in range(n_steps):
            self.step()
            
            if step % record_every == 0:
                history['T'].append(self.kinetic_energy())
                history['V'].append(self.potential_energy())
                history['E'].append(self.total_energy())
                history['W'].append(self.winding())
        
        return history


def test_energy_conservation():
    """Verify energy is conserved."""
    print("=" * 70)
    print("TEST: ENERGY CONSERVATION (XY MODEL)")
    print("=" * 70)
    
    model = XYModel(n=6, K=1.0, phi=-np.pi/6)
    model.initialize_winding(1)
    
    E0 = model.total_energy()
    print(f"Initial energy: {E0:.6f}")
    
    history = model.evolve(50000, record_every=100)
    
    Ef = model.total_energy()
    drift = abs(Ef - E0) / abs(E0)
    
    print(f"Final energy:   {Ef:.6f}")
    print(f"Drift:          {drift:.6%}")
    
    energies = history['E']
    E_std = np.std(energies)
    E_mean = np.mean(energies)
    
    print(f"Mean:           {E_mean:.6f}")
    print(f"Std:            {E_std:.6f}")
    print(f"Relative std:   {E_std/abs(E_mean):.6%}")
    
    print(f"\n{'✓ ENERGY CONSERVED' if drift < 0.001 else '✗ Energy NOT conserved'}")
    
    return drift < 0.001


def test_winding_preservation():
    """Verify winding is preserved."""
    print("\n" + "=" * 70)
    print("TEST: WINDING PRESERVATION")
    print("=" * 70)
    
    results = []
    
    print(f"\n{'n':>4} | {'K':>6} | {'phi':>8} | {'Init W':>8} | {'Final W':>8} | {'OK':>4}")
    print("-" * 55)
    
    for n in [4, 6, 8, 12]:
        for init_W in [0, 1, 2]:
            model = XYModel(n=n, K=1.0, phi=-np.pi/6)
            model.initialize_winding(init_W)
            
            W0 = model.winding()
            model.evolve(20000, record_every=500)
            Wf = model.winding()
            
            ok = abs(round(Wf) - init_W) == 0
            
            print(f"{n:>4} | {1.0:>6.1f} | {-30:>7}° | {init_W:>8} | {Wf:>8.2f} | {'✓' if ok else '✗':>4}")
            
            results.append({'n': n, 'init_W': init_W, 'final_W': round(Wf), 'ok': ok})
    
    rate = sum(1 for r in results if r['ok']) / len(results)
    print(f"\nPreservation rate: {rate:.0%}")
    
    return rate


def test_geometric_phase():
    """Test if geometric phase offset affects stable states."""
    print("\n" + "=" * 70)
    print("TEST: GEOMETRIC PHASE EFFECT")
    print("=" * 70)
    print("""
With phi = -30° per junction:
  n=6: expected geometric winding = -0.5 (half-integer = FERMION)
  n=12: expected geometric winding = -1 (integer = BOSON)

Testing if these are stable...
""")
    
    results = []
    
    for n in [6, 12]:
        expected_W = -n / 12  # From -30° per junction
        
        # Initialize with geometric winding
        model = XYModel(n=n, K=2.0, phi=-np.pi/6)
        
        for i in range(n):
            # Phase that gives expected winding
            model.nodes[i].theta = (2 * np.pi * expected_W * i / n) % (2 * np.pi)
            model.nodes[i].pi = 0.01  # Small perturbation
        
        W0 = model.winding()
        history = model.evolve(30000, record_every=100)
        Wf = model.winding()
        
        # Check stability
        windings = history['W']
        W_mean = np.mean(windings)
        W_std = np.std(windings)
        
        marker = "FERMION" if n == 6 else "BOSON"
        stable = W_std < 0.1
        
        print(f"n={n} ({marker}):")
        print(f"  Expected W: {expected_W:.3f}")
        print(f"  Initial W:  {W0:.3f}")
        print(f"  Final W:    {Wf:.3f}")
        print(f"  Mean W:     {W_mean:.3f}")
        print(f"  Std W:      {W_std:.3f}")
        print(f"  Stable:     {'YES' if stable else 'NO'}")
        print()
        
        results.append({
            'n': n,
            'expected_W': expected_W,
            'final_W': Wf,
            'W_std': W_std,
            'stable': stable
        })
    
    return results


def test_spontaneous_emergence():
    """Test if specific windings emerge from random initialization."""
    print("=" * 70)
    print("TEST: SPONTANEOUS WINDING EMERGENCE")
    print("=" * 70)
    
    winding_counts = {}
    
    for trial in range(50):
        n = 6
        model = XYModel(n=n, K=1.0, phi=-np.pi/6)
        model.initialize_random()
        
        model.evolve(20000, record_every=500)
        
        Wf = round(model.winding())
        winding_counts[Wf] = winding_counts.get(Wf, 0) + 1
    
    print("\nFinal winding distribution (n=6, 50 trials):")
    for W in sorted(winding_counts.keys()):
        count = winding_counts[W]
        bar = '#' * count
        print(f"  W={W:>2}: {bar} ({count})")
    
    return winding_counts


if __name__ == "__main__":
    print("=" * 80)
    print("  CORRECTED XY MODEL TEST")
    print("=" * 80)
    print()
    
    energy_ok = test_energy_conservation()
    winding_rate = test_winding_preservation()
    geometric_results = test_geometric_phase()
    emergence = test_spontaneous_emergence()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
Energy conserved:     {'YES' if energy_ok else 'NO'}
Winding preserved:    {winding_rate:.0%}
Geometric W stable:   {[r['n'] for r in geometric_results if r['stable']]}
""")
    
    # Save results
    output = {
        'energy_conserved': energy_ok,
        'winding_rate': winding_rate,
        'geometric': geometric_results,
        'emergence_distribution': emergence
    }
    
    with open('/app/backend/qmrt_topology/xy_model_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print("Results saved to /app/backend/qmrt_topology/xy_model_results.json")
