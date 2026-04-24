"""
Transition-Zone Lifetime Analysis
==================================

Question: Is the transition zone's longer lifetime (231 vs 203 steps) a robust,
meaningful, mechanistically distinct effect?

Tests:
1. Original gradient (high center)
2. Inverted gradient (high edge)
3. Parameter variation (different damping)

Decision criteria:
- Robust: survives across settings
- Meaningful: lifetime advantage is not tiny/noisy
- Mechanistically distinct: survival optimum ≠ transport destination

If all three pass → include in Paper 4 as "attractor + survival ridge"
If any fail → keep Paper 4 focused on clean causal result
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Dict, List


class LifetimeAnalysisSimulator:
    """Configurable simulator for lifetime analysis."""
    
    def __init__(self, size: int = 100, gamma: float = 0.007,
                 coupling_center: float = 0.8, coupling_edge: float = 0.2,
                 transition_width: float = 20.0):
        self.size = size
        self.gamma = gamma
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.transition_width = transition_width
        
        # Standard Branch E parameters
        self.c_0 = 2.0
        self.tau_0 = 1.0
        self.lambda_relax = 0.5
        self.beta = 0.5
        self.D_medium = 0.1
        self.dt = 0.04
        
        # Fields
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * self.tau_0
        self.channel_assignment = np.zeros((size, size))
        
        # Coupling landscape
        self.channel_coupling_field = self._create_coupling_landscape()
    
    def _create_coupling_landscape(self) -> np.ndarray:
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2)
        interior_radius = self.size * 0.3
        
        coupling = np.zeros((self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                dist = r[i, j]
                if dist <= interior_radius:
                    coupling[i, j] = self.coupling_center
                elif dist >= interior_radius + self.transition_width:
                    coupling[i, j] = self.coupling_edge
                else:
                    t = (dist - interior_radius) / self.transition_width
                    blend = 0.5 * (1 - np.cos(np.pi * t))
                    coupling[i, j] = self.coupling_center + blend * (self.coupling_edge - self.coupling_center)
        return coupling
    
    def get_zone(self, x: int, y: int) -> str:
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2)
        interior_radius = self.size * 0.3
        if r <= interior_radius:
            return 'interior'
        elif r <= interior_radius + self.transition_width:
            return 'transition'
        return 'periphery'
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    @property
    def rho(self) -> np.ndarray:
        return self.amplitude**2
    
    def compute_topology_indicator(self) -> np.ndarray:
        phase = self.phase
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, 0) - np.roll(phase, 1, 0))))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, 1) - np.roll(phase, 1, 1))))
        return gaussian_filter(np.sqrt(grad_x**2 + grad_y**2), sigma=2.0)
    
    def step(self):
        # Channel assignment
        topology = self.compute_topology_indicator()
        topology_norm = topology / (np.max(topology) + 1e-10)
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        # Medium dynamics
        rho = self.rho
        tau_eq = self.tau_0 / (1 + self.beta * gaussian_filter(rho, sigma=2.0) / (np.max(rho) + 1e-10))
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        self.tau += self.dt * (-self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau)
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave equation
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                 np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
        lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                 np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Core-filling suppression
        protection = topology_norm * self.channel_assignment
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.channel_coupling_field * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def detect_vortices(self, amp_threshold: float = 0.4) -> List[Dict]:
        amp = self.amplitude
        phase = self.phase
        vortices = []
        
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                if amp[i, j] < amp_threshold:
                    phases = [phase[i-1, j], phase[i, j+1], phase[i+1, j], phase[i, j-1]]
                    winding = sum(np.angle(np.exp(1j * (phases[(k+1)%4] - phases[k]))) for k in range(4))
                    winding /= (2 * np.pi)
                    
                    if abs(winding) > 0.5:
                        vortices.append({
                            'position': (i, j),
                            'zone': self.get_zone(i, j)
                        })
        return vortices


def measure_lifetimes(coupling_center: float, coupling_edge: float, 
                      gamma: float, steps: int = 6000, seed: int = 42) -> Dict:
    """Run simulation and measure lifetimes by birth zone."""
    
    sim = LifetimeAnalysisSimulator(
        size=100, gamma=gamma,
        coupling_center=coupling_center, coupling_edge=coupling_edge
    )
    
    # Initialize
    center = sim.size // 2
    np.random.seed(seed)
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    for i, pos in enumerate([(center-5, center), (center+5, center), 
                              (center, center-8), (center, center+8)]):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(100), np.arange(100), indexing='ij')
        r = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        amp = 1.2 * np.tanh(r / 4.0)
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    sim.psi_r += 0.05 * np.random.randn(100, 100)
    sim.psi_i += 0.05 * np.random.randn(100, 100)
    
    # Track vortices
    vortex_data = {}  # id -> {birth_step, birth_zone, death_step}
    next_id = 0
    prev_vortices = {}  # position -> id
    
    for step in range(steps):
        sim.step()
        
        if step % 20 == 0:
            vortices = sim.detect_vortices()
            current_positions = {v['position']: v for v in vortices}
            
            new_prev = {}
            matched_ids = set()
            
            for pos, v in current_positions.items():
                best_id = None
                best_dist = 12
                
                for prev_pos, prev_id in prev_vortices.items():
                    if prev_id in matched_ids:
                        continue
                    dist = np.sqrt((pos[0] - prev_pos[0])**2 + (pos[1] - prev_pos[1])**2)
                    if dist < best_dist:
                        best_dist = dist
                        best_id = prev_id
                
                if best_id is not None:
                    matched_ids.add(best_id)
                    new_prev[pos] = best_id
                else:
                    vid = next_id
                    next_id += 1
                    new_prev[pos] = vid
                    vortex_data[vid] = {'birth_step': step, 'birth_zone': v['zone']}
            
            for prev_pos, prev_id in prev_vortices.items():
                if prev_id not in matched_ids:
                    vortex_data[prev_id]['death_step'] = step
            
            prev_vortices = new_prev
    
    # Compute lifetimes by zone
    lifetimes = {'interior': [], 'transition': [], 'periphery': []}
    
    for vid, data in vortex_data.items():
        if 'death_step' in data:
            lifetime = data['death_step'] - data['birth_step']
            lifetimes[data['birth_zone']].append(lifetime)
    
    return {zone: (np.mean(lt) if lt else 0, len(lt)) for zone, lt in lifetimes.items()}


def main():
    print("="*70)
    print("TRANSITION-ZONE LIFETIME ANALYSIS")
    print("="*70)
    print()
    print("Question: Is the transition zone's longer lifetime robust and meaningful?")
    print()
    
    results = {}
    
    # Test configurations
    configs = [
        ('Original (high center)', 0.8, 0.2, 0.007),
        ('Inverted (high edge)', 0.2, 0.8, 0.007),
        ('Lower damping', 0.8, 0.2, 0.005),
        ('Higher damping', 0.8, 0.2, 0.009),
    ]
    
    print(f"{'Config':<25} | {'Interior':>12} | {'Transition':>12} | {'Periphery':>12} | {'Longest':<12}")
    print("-"*82)
    
    for label, cc, ce, gamma in configs:
        lt = measure_lifetimes(cc, ce, gamma, steps=6000)
        
        zones = ['interior', 'transition', 'periphery']
        means = {z: lt[z][0] for z in zones}
        counts = {z: lt[z][1] for z in zones}
        
        longest = max(zones, key=lambda z: means[z] if counts[z] > 10 else 0)
        
        row = f"{label:<25} |"
        for z in zones:
            if counts[z] > 10:
                row += f" {means[z]:>5.0f} (n={counts[z]:>3d}) |"
            else:
                row += f"       n={counts[z]:>3d}  |"
        row += f" {longest}"
        print(row)
        
        results[label] = {'means': means, 'counts': counts, 'longest': longest}
    
    print()
    print("="*70)
    print("ANALYSIS")
    print("="*70)
    print()
    
    # Check robustness
    transition_longest_count = sum(1 for r in results.values() if r['longest'] == 'transition')
    
    print(f"Transition zone longest in {transition_longest_count}/4 configurations")
    print()
    
    # Check if transition is always in between
    for label, r in results.items():
        if r['counts']['transition'] > 10 and r['counts']['interior'] > 10 and r['counts']['periphery'] > 10:
            trans = r['means']['transition']
            int_m = r['means']['interior']
            per_m = r['means']['periphery']
            high_coupling_zone = 'interior' if 'Original' in label or 'damping' in label else 'periphery'
            
            print(f"{label}:")
            print(f"  High-coupling zone ({high_coupling_zone}): {r['means'][high_coupling_zone]:.0f}")
            print(f"  Transition zone: {trans:.0f}")
            print(f"  Low-coupling zone: {r['means']['periphery' if high_coupling_zone == 'interior' else 'interior']:.0f}")
    
    print()
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()
    
    # Decision criteria
    robust = transition_longest_count >= 3
    
    # Check if meaningful (>10% advantage over high-coupling zone)
    orig = results['Original (high center)']
    if orig['counts']['transition'] > 10 and orig['counts']['interior'] > 10:
        advantage = (orig['means']['transition'] - orig['means']['interior']) / orig['means']['interior']
        meaningful = advantage > 0.1
    else:
        meaningful = False
        advantage = 0
    
    # Check mechanistically distinct
    inv = results['Inverted (high edge)']
    if inv['counts']['transition'] > 10:
        distinct = (inv['longest'] == 'transition' or 
                    inv['means']['transition'] > inv['means']['periphery'])
    else:
        distinct = False
    
    print(f"Robust (transition longest in ≥3/4 configs): {'✓' if robust else '✗'}")
    print(f"Meaningful (>10% advantage): {'✓' if meaningful else '✗'} ({advantage*100:.1f}%)")
    print(f"Mechanistically distinct: {'✓' if distinct else '✗'}")
    print()
    
    if robust and meaningful and distinct:
        print("★ INCLUDE IN PAPER 4: Attractor + Survival Ridge")
        print()
        print("The transition zone represents a survival optimum distinct from")
        print("the transport attractor (high-coupling region).")
        paper_version = "attractor + survival ridge"
    else:
        print("→ KEEP PAPER 4 FOCUSED: Clean causal attractor result")
        print()
        print("The transition-zone effect is not robust/meaningful enough to include.")
        print("Mention briefly as future work.")
        paper_version = "clean causal attractor"
    
    return paper_version, results


if __name__ == "__main__":
    main()
