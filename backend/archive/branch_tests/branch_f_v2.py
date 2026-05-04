"""
Branch F v2: True Branch E Dynamics + Spatial Channel Coupling
===============================================================

The previous Branch F attempts failed because they simplified Branch E dynamics.
This version uses the EXACT Branch E wave equation with:
- Dynamic tau field
- Oscillator coupling (chi_1, chi_2)
- c_eff² * laplacian (not β-weighted)

Spatial variation is added ONLY to channel_coupling, not wave dynamics.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict
import json


class BranchFv2Simulator:
    """
    Uses exact Branch E dynamics from regeneration_analysis.py
    with spatially varying channel coupling.
    """
    
    def __init__(
        self,
        size: int = 100,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.007,
        lambda_relax: float = 0.5,
        beta: float = 0.5,  # For tau dynamics, NOT for Laplacian
        D_medium: float = 0.1,
        dt: float = 0.04,
        omega_1: float = 0.3,
        omega_2: float = 0.8,
        coupling_center: float = 0.6,   # High coupling in center
        coupling_edge: float = 0.3,     # Lower coupling at edges
        transition_width: float = 20.0,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.beta = beta
        self.D_medium = D_medium
        self.dt = dt
        self.omega_1 = omega_1
        self.omega_2 = omega_2
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.transition_width = transition_width
        
        # Fields
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        # Oscillators (from Branch E)
        self.chi_1 = np.zeros((size, size))
        self.chi_1_dot = np.zeros((size, size))
        self.chi_2 = np.zeros((size, size))
        self.chi_2_dot = np.zeros((size, size))
        self.channel_assignment = np.zeros((size, size))
        
        # Spatially varying channel coupling
        self.channel_coupling_field = self._create_coupling_landscape()
        
        self.step_count = 0
    
    def _create_coupling_landscape(self) -> np.ndarray:
        """High coupling in center, low at edges."""
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
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        return gaussian_filter(grad_mag, sigma=2.0)
    
    def compute_channel_protection(self) -> np.ndarray:
        topology = self.compute_topology_indicator()
        topology_norm = topology / (np.max(topology) + 1e-10)
        return topology_norm * self.channel_assignment
    
    def update_self_selecting_channels(self):
        topology = self.compute_topology_indicator()
        topology_norm = topology / (np.max(topology) + 1e-10)
        target = topology_norm
        relaxation_rate = 0.01
        self.channel_assignment += relaxation_rate * (target - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
    
    def step(self):
        """EXACT Branch E dynamics with spatial channel coupling."""
        self.step_count += 1
        self.update_self_selecting_channels()
        
        # Oscillators (from Branch E)
        self.chi_1_dot += -self.omega_1**2 * self.chi_1 * self.dt
        self.chi_1 += self.chi_1_dot * self.dt
        self.chi_2_dot += -self.omega_2**2 * self.chi_2 * self.dt
        self.chi_2 += self.chi_2_dot * self.dt
        
        # Medium dynamics (from Branch E)
        rho = self.rho
        tau_eq = self.tau_0 / (1 + self.beta * gaussian_filter(rho, sigma=2.0) / (np.max(rho) + 1e-10))
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave equation (from Branch E)
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                 np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
        lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                 np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Core-filling suppression with SPATIAL channel coupling
        protection = self.compute_channel_protection()
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        # Spatially varying suppression
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
                    winding = 0
                    for k in range(4):
                        diff = phases[(k+1) % 4] - phases[k]
                        diff = np.angle(np.exp(1j * diff))
                        winding += diff
                    winding /= (2 * np.pi)
                    
                    if abs(winding) > 0.5:
                        zone = self.get_zone(i, j)
                        vortices.append({
                            'position': (i, j),
                            'charge': int(np.sign(winding)),
                            'zone': zone,
                            'coupling_local': self.channel_coupling_field[i, j]
                        })
        return vortices


def run_test(coupling_center: float = 0.6, coupling_edge: float = 0.3, steps: int = 4000):
    """Run Branch F v2 test with exact Branch E dynamics."""
    sim = BranchFv2Simulator(
        size=100, gamma=0.007,
        coupling_center=coupling_center, coupling_edge=coupling_edge,
        transition_width=20.0
    )
    
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
    
    # Run simulation
    prev_positions = set()
    population_history = []
    interior_births = 0
    transition_births = 0
    periphery_births = 0
    total_deaths = 0
    lifetimes = []
    vortex_birth_times = {}
    
    for step in range(steps):
        sim.step()
        
        if step % 25 == 0:
            vortices = sim.detect_vortices()
            current_positions = set(v['position'] for v in vortices)
            
            # Births
            new_positions = current_positions - prev_positions
            for v in vortices:
                if v['position'] in new_positions:
                    zone = v['zone']
                    if zone == 'interior':
                        interior_births += 1
                    elif zone == 'transition':
                        transition_births += 1
                    else:
                        periphery_births += 1
                    vortex_birth_times[v['position']] = step
            
            # Deaths
            lost_positions = prev_positions - current_positions
            for pos in lost_positions:
                total_deaths += 1
                if pos in vortex_birth_times:
                    lifetime = step - vortex_birth_times[pos]
                    lifetimes.append(lifetime)
                    del vortex_birth_times[pos]
            
            population_history.append(len(vortices))
            prev_positions = current_positions
    
    # Results
    total_births = interior_births + transition_births + periphery_births
    late_start = int(0.7 * len(population_history))
    late_population = np.mean(population_history[late_start:]) if population_history else 0
    mean_lifetime = np.mean(lifetimes) if lifetimes else 0
    
    return {
        'coupling_center': coupling_center,
        'coupling_edge': coupling_edge,
        'total_births': total_births,
        'interior_births': interior_births,
        'transition_births': transition_births,
        'periphery_births': periphery_births,
        'total_deaths': total_deaths,
        'mean_lifetime': mean_lifetime,
        'late_population': late_population,
        'population_history_last10': population_history[-10:]
    }


def main():
    print("="*70)
    print("BRANCH F v2: TRUE BRANCH E DYNAMICS + SPATIAL COUPLING")
    print("="*70)
    print()
    print("Using EXACT Branch E dynamics (tau, oscillators, c_eff²)")
    print("with spatially varying channel coupling only")
    print()
    
    # First test: uniform coupling (pure Branch E baseline)
    print("--- BASELINE: Uniform coupling = 0.5 ---")
    result_uniform = run_test(coupling_center=0.5, coupling_edge=0.5, steps=4000)
    print(f"Total births: {result_uniform['total_births']}")
    print(f"Late population: {result_uniform['late_population']:.2f}")
    print(f"Mean lifetime: {result_uniform['mean_lifetime']:.0f}")
    print(f"Interior: {result_uniform['interior_births']}, Trans: {result_uniform['transition_births']}, Periph: {result_uniform['periphery_births']}")
    print()
    
    # Second test: spatial coupling (high center, low edge)
    print("--- SPATIAL: center=0.6, edge=0.3 ---")
    result_spatial = run_test(coupling_center=0.6, coupling_edge=0.3, steps=4000)
    print(f"Total births: {result_spatial['total_births']}")
    print(f"Late population: {result_spatial['late_population']:.2f}")
    print(f"Mean lifetime: {result_spatial['mean_lifetime']:.0f}")
    print(f"Interior: {result_spatial['interior_births']}, Trans: {result_spatial['transition_births']}, Periph: {result_spatial['periphery_births']}")
    print()
    
    # Third test: stronger contrast
    print("--- STRONG SPATIAL: center=0.8, edge=0.2 ---")
    result_strong = run_test(coupling_center=0.8, coupling_edge=0.2, steps=4000)
    print(f"Total births: {result_strong['total_births']}")
    print(f"Late population: {result_strong['late_population']:.2f}")
    print(f"Mean lifetime: {result_strong['mean_lifetime']:.0f}")
    print(f"Interior: {result_strong['interior_births']}, Trans: {result_strong['transition_births']}, Periph: {result_strong['periphery_births']}")
    print()
    
    # Analysis
    print("="*70)
    print("ANALYSIS")
    print("="*70)
    print()
    
    if result_uniform['total_births'] > 100:
        print("✓ Branch E dynamics restored: high regeneration rate")
        
        # Check localization
        if result_spatial['interior_births'] > result_spatial['periphery_births']:
            interior_ratio = result_spatial['interior_births'] / (result_spatial['total_births'] + 1)
            print(f"✓ Spatial localization working: {interior_ratio*100:.1f}% births in interior")
        else:
            print("✗ Localization not achieved")
        
        # Check population
        if result_spatial['late_population'] > 0.5:
            print(f"✓ Sustained population: {result_spatial['late_population']:.2f}")
        else:
            print(f"✗ Population not sustained: {result_spatial['late_population']:.2f}")
    else:
        print(f"✗ Regeneration rate still low: {result_uniform['total_births']} births")
        print("  Branch E dynamics may not be correctly implemented")
    
    # Save
    results = {
        'uniform': result_uniform,
        'spatial': result_spatial,
        'strong': result_strong
    }
    
    with open('/app/backend/qmrt_topology/test_results/phase5/branch_f_v2_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("Results saved to branch_f_v2_results.json")


if __name__ == "__main__":
    main()
