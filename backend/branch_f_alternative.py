"""
Branch F Alternative: Spatially Varying Channel Coupling
=========================================================

Key insight from testing:
- β-weighted Laplacian interferes with channel self-selection
- The suppression mechanism identified β's effect on wave speed as the culprit

Alternative hypothesis:
Instead of spatially varying β (which affects wave dynamics),
spatially vary the CHANNEL COUPLING strength:
- High coupling in interior: stronger regeneration
- Lower coupling at periphery: weaker regeneration (but existing vortices persist)

This separates the mechanisms more cleanly:
- Wave dynamics: uniform β everywhere
- Regeneration strength: varies spatially via channel coupling
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple
import json


class BranchFAlternativeSimulator:
    """
    Spatially varying channel coupling (not β).
    β is uniform; channel_coupling varies spatially.
    """
    
    def __init__(self, size: int = 100, gamma: float = 0.007,
                 coupling_center: float = 0.6, coupling_edge: float = 0.2,
                 transition_width: float = 20.0):
        self.size = size
        self.gamma = gamma
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.transition_width = transition_width
        
        # Fields
        self.psi_r = np.ones((size, size)) * 1.2
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Channel assignment
        self.channel_assignment = np.zeros((size, size))
        
        # Medium (uniform)
        self.tau = np.ones((size, size)) * 0.5
        self.c_0 = 1.0
        self.tau_0 = 0.5
        
        # Spatially varying channel coupling (high center, low edge)
        self.channel_coupling_field = self._create_coupling_landscape()
        
        self.nucleation_history = []
        self.step_count = 0
    
    def _create_coupling_landscape(self) -> np.ndarray:
        """High coupling in center (regeneration zone), low at edges."""
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
        else:
            return 'periphery'
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    def compute_laplacian(self, field: np.ndarray) -> np.ndarray:
        return (np.roll(field, 1, 0) + np.roll(field, -1, 0) +
                np.roll(field, 1, 1) + np.roll(field, -1, 1) - 4*field)
    
    def compute_topology_indicator(self) -> np.ndarray:
        phase = self.phase
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, 0) - np.roll(phase, 1, 0))))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, 1) - np.roll(phase, 1, 1))))
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        return gaussian_filter(grad_mag, sigma=2.0)
    
    def update_self_selecting_channels(self):
        topology = self.compute_topology_indicator()
        topology_max = np.max(topology)
        topology_norm = topology / (topology_max + 1e-10)
        
        target = topology_norm
        relaxation_rate = 0.01
        self.channel_assignment += relaxation_rate * (target - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
    
    def compute_channel_protection(self) -> np.ndarray:
        topology = self.compute_topology_indicator()
        topology_max = np.max(topology)
        topology_norm = topology / (topology_max + 1e-10)
        return topology_norm * self.channel_assignment
    
    def step(self, dt: float = 0.05):
        self.step_count += 1
        
        self.update_self_selecting_channels()
        
        # Standard Laplacian (NO β weighting)
        lap_r = self.compute_laplacian(self.psi_r)
        lap_i = self.compute_laplacian(self.psi_i)
        
        amp_sq = self.psi_r**2 + self.psi_i**2
        nl_r = self.psi_r * (1 - amp_sq)
        nl_i = self.psi_i * (1 - amp_sq)
        
        acc_r = lap_r + nl_r - self.gamma * self.psi_r_dot
        acc_i = lap_i + nl_i - self.gamma * self.psi_i_dot
        
        # Spatially varying channel coupling for core-filling suppression
        protection = self.compute_channel_protection()
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        # Suppression strength varies spatially
        suppression = self.channel_coupling_field * protection * np.maximum(acc_radial, 0)
        
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_vortices(self, amp_threshold: float = 0.4) -> List[Dict]:
        amp = self.amplitude
        phase = self.phase
        vortices = []
        
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                if amp[i, j] < amp_threshold:
                    phases = [phase[i-1, j], phase[i, j+1], phase[i+1, j], phase[i, j-1]]
                    winding = 0
                    for k in range(4):
                        diff = phases[(k+1) % 4] - phases[k]
                        diff = np.angle(np.exp(1j * diff))
                        winding += diff
                    winding /= (2 * np.pi)
                    
                    if abs(winding) > 0.5:
                        charge = int(np.sign(winding))
                        zone = self.get_zone(i, j)
                        vortices.append({
                            'position': (i, j),
                            'charge': charge,
                            'zone': zone,
                            'coupling_local': self.channel_coupling_field[i, j]
                        })
        return vortices
    
    def add_vortex(self, position: Tuple[int, int], charge: int = +1,
                   amplitude: float = 1.2, core_radius: float = 4.0):
        cx, cy = position
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        amp_profile = amplitude * np.tanh(r / core_radius)
        self.psi_r = amp_profile * np.cos(charge * theta)
        self.psi_i = amp_profile * np.sin(charge * theta)


def run_test():
    print("="*70)
    print("BRANCH F ALTERNATIVE: SPATIALLY VARYING CHANNEL COUPLING")
    print("="*70)
    print()
    print("Hypothesis: Keep β uniform, vary channel_coupling spatially")
    print("  Interior: high coupling (0.6) → strong regeneration")
    print("  Periphery: low coupling (0.2) → structures persist once formed")
    print()
    
    sim = BranchFAlternativeSimulator(size=100, gamma=0.007,
                                       coupling_center=0.6, coupling_edge=0.2,
                                       transition_width=20.0)
    
    # Seed vortex pairs
    center = sim.size // 2
    np.random.seed(42)
    
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    vortex_positions = [
        (center - 5, center),
        (center + 5, center),
        (center, center - 8),
        (center, center + 8),
    ]
    
    for i, pos in enumerate(vortex_positions):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
        r_dist = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        vortex_amp = 1.2 * np.tanh(r_dist / 4.0)
        
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (vortex_amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size)
    
    prev_vortices = []
    prev_positions = set()
    
    population_history = []
    interior_population = []
    periphery_population = []
    total_births = 0
    total_deaths = 0
    
    for step in range(4000):
        sim.step()
        
        if step % 25 == 0:
            vortices = sim.detect_vortices()
            current_positions = set(v['position'] for v in vortices)
            
            births = len(current_positions - prev_positions)
            deaths = len(prev_positions - current_positions)
            
            total_births += births
            total_deaths += deaths
            
            for v in vortices:
                if v['position'] not in prev_positions:
                    sim.nucleation_history.append((step, v['position'][0], v['position'][1], v['zone']))
            
            n_total = len(vortices)
            n_interior = sum(1 for v in vortices if v['zone'] == 'interior')
            n_periphery = sum(1 for v in vortices if v['zone'] == 'periphery')
            
            population_history.append(n_total)
            interior_population.append(n_interior)
            periphery_population.append(n_periphery)
            
            prev_positions = current_positions
    
    # Results
    late_start = int(0.7 * len(population_history))
    late_pop = np.mean(population_history[late_start:]) if population_history else 0
    late_interior = np.mean(interior_population[late_start:]) if interior_population else 0
    late_periphery = np.mean(periphery_population[late_start:]) if periphery_population else 0
    
    if late_pop > 0:
        localization_ratio = late_interior / late_pop
    else:
        localization_ratio = 0
    
    # Nucleation analysis
    interior_births = sum(1 for n in sim.nucleation_history if n[3] == 'interior')
    periphery_births = sum(1 for n in sim.nucleation_history if n[3] == 'periphery')
    
    print("RESULTS:")
    print(f"  Total births: {total_births}")
    print(f"  Total deaths: {total_deaths}")
    print(f"  Late population: {late_pop:.2f}")
    print(f"  Late interior: {late_interior:.2f}")
    print(f"  Late periphery: {late_periphery:.2f}")
    print(f"  Localization (interior/total): {localization_ratio:.3f}")
    print()
    print("Nucleation by zone:")
    print(f"  Interior: {interior_births}")
    print(f"  Periphery: {periphery_births}")
    print()
    
    # Success criteria
    success_pop = late_pop > 1.0
    success_regen = total_births > 50
    success_local = localization_ratio > 0.4
    
    print("Success criteria:")
    print(f"  Population > 1.0: {'✓' if success_pop else '✗'} ({late_pop:.2f})")
    print(f"  Regeneration > 50: {'✓' if success_regen else '✗'} ({total_births})")
    print(f"  Localization > 0.4: {'✓' if success_local else '✗'} ({localization_ratio:.3f})")
    print()
    
    if success_pop and success_regen:
        print("="*70)
        print("✓ BRANCH F ALTERNATIVE SUCCEEDS")
        print("="*70)
        print()
        print("Spatially varying channel coupling achieves co-alignment!")
    else:
        print("Branch F Alternative: needs further refinement")
    
    return {
        'late_population': late_pop,
        'total_births': total_births,
        'localization_ratio': localization_ratio
    }


if __name__ == "__main__":
    run_test()
