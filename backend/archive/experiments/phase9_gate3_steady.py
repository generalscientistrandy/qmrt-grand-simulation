"""
Phase 9, Gate 3: Driven Steady State Characterization
======================================================

Core Question: What is the carrying capacity / steady state of the driven scaffold?

Gate 2 showed the driven scaffold grows but hasn't saturated.
Gate 3 runs longer to find:
- Saturation population
- Steady-state dimension
- Steady-state structure metrics
- Whether a true NESS (non-equilibrium steady state) exists
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from collections import defaultdict, deque
from typing import Dict, List, Tuple


class SteadyStateSimulator:
    """Standard simulator with periodic injection."""
    
    def __init__(self, size: int = 48):
        self.size = size
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        self.coupling = self._create_coupling()
        self.step_count = 0
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = 0.7
                    elif dist >= interior_r + 10.0:
                        coupling[i, j, k] = 0.2
                    else:
                        t = (dist - interior_r) / 10.0
                        coupling[i, j, k] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        return coupling
    
    def inject_vortex(self, cx: int, cy: int):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_random_vortices(self, n: int = 5):
        center = self.size // 2
        for _ in range(n):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        if self.step_count % 50 == 0:
            self.inject_random_vortices(5)
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        gamma = 0.007
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = 4.0 * lap_r - gamma * self.psi_r_dot
        acc_i = 4.0 * lap_i - gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                defects.append((int(np.mean(coords[0])), int(np.mean(coords[1])), int(np.mean(coords[2]))))
        return defects


def measure_quick(defects, size):
    n = len(defects)
    if n < 10:
        return {'valid': False, 'n': n}
    
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            d = np.abs(np.array(defects[i]) - np.array(defects[j]))
            d = np.minimum(d, size - d)
            if np.sqrt(np.sum(d**2)) < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    edges = sum(len(adj[i]) for i in range(n)) // 2
    degrees = [len(adj[i]) for i in range(n)]
    
    triangles = 0
    for node in range(n):
        neighbors = list(adj[node])
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    triangles += 1
    triangles //= 3
    
    # Quick dimension estimate
    graph_dist = np.full((n, n), np.inf)
    for start in range(n):
        graph_dist[start, start] = 0
        queue = [start]
        visited = {start}
        while queue:
            node = queue.pop(0)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    graph_dist[start, neighbor] = graph_dist[start, node] + 1
                    queue.append(neighbor)
    
    radii = list(range(1, 6))
    counts = []
    for r in radii:
        c = [np.sum((graph_dist[i, :] <= r) & (graph_dist[i, :] > 0)) for i in range(n)]
        counts.append(np.mean(c))
    
    if min(counts) > 0:
        coeffs = np.polyfit(np.log(radii), np.log(np.array(counts) + 1), 1)
        dim = coeffs[0]
    else:
        dim = 0
    
    return {'valid': True, 'n': n, 'edges': edges, 'triangles': triangles, 'dim': dim, 'mean_deg': np.mean(degrees)}


def run_steady_state_test():
    print("=" * 70)
    print("PHASE 9, GATE 3: STEADY STATE CHARACTERIZATION")
    print("=" * 70)
    print()
    print("Question: What is the carrying capacity of the driven scaffold?")
    print()
    
    sim = SteadyStateSimulator(size=48)
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Initial seeding
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    print("Running 8 epochs (extended observation)...")
    print()
    
    epochs = []
    
    for epoch in range(8):
        print(f"Epoch {epoch + 1}:", end=" ", flush=True)
        epoch_data = []
        
        for step in range(500):
            sim.step()
            if step % 100 == 0:
                defects = sim.detect_defects()
                m = measure_quick(defects, sim.size)
                if m['valid']:
                    epoch_data.append(m)
                    print(".", end="", flush=True)
        
        if epoch_data:
            agg = {
                'epoch': epoch + 1,
                'n': np.mean([d['n'] for d in epoch_data]),
                'dim': np.mean([d['dim'] for d in epoch_data]),
                'tri': np.mean([d['triangles'] for d in epoch_data]),
                'edges': np.mean([d['edges'] for d in epoch_data]),
            }
            epochs.append(agg)
            print(f" N={agg['n']:.0f}, d={agg['dim']:.2f}, tri={agg['tri']:.0f}")
        else:
            print(" insufficient")
    
    # Summary
    print()
    print("=" * 70)
    print("STEADY STATE ANALYSIS")
    print("=" * 70)
    print()
    
    print(f"{'Epoch':>6} {'Pop':>8} {'Dim':>8} {'Tri':>10} {'Edges':>8}")
    print("-" * 45)
    for e in epochs:
        print(f"{e['epoch']:>6} {e['n']:>8.0f} {e['dim']:>8.2f} {e['tri']:>10.0f} {e['edges']:>8.0f}")
    
    # Check for saturation
    if len(epochs) >= 4:
        late = epochs[-2:]
        early = epochs[:2]
        
        late_n = np.mean([e['n'] for e in late])
        early_n = np.mean([e['n'] for e in early])
        
        late_dim = np.mean([e['dim'] for e in late])
        
        growth_rate = (late_n - early_n) / early_n * 100 if early_n > 0 else 0
        
        print()
        print(f"Early population (epochs 1-2): {early_n:.0f}")
        print(f"Late population (epochs 7-8): {late_n:.0f}")
        print(f"Growth rate: {growth_rate:+.1f}%")
        print(f"Late dimension: {late_dim:.2f}")
        print()
        
        if abs(growth_rate) < 20:
            print("FINDING: STEADY STATE REACHED")
            print(f"  Carrying capacity: ~{late_n:.0f} defects")
            print(f"  Steady-state dimension: ~{late_dim:.2f}")
        elif growth_rate > 0:
            print("FINDING: STILL GROWING")
            print(f"  Not yet saturated (growth rate {growth_rate:+.1f}%)")
        else:
            print("FINDING: DECLINING")
            print(f"  System is decaying despite driving")
    
    return epochs


if __name__ == "__main__":
    epochs = run_steady_state_test()
