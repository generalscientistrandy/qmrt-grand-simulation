"""
Branch F Rate-Balance Sweep
===========================

Goal: Find parameters that achieve nonzero late population by balancing:
  - Regeneration rate (controlled by channel_coupling)
  - Lifetime (controlled by gamma/damping)

The Branch F spatial separation mechanism is already validated (Tests 1&2 pass).
Now we tune birth-survival balance to sustain a population.

Sweep parameters:
  - channel_coupling: [0.5, 0.7, 0.9] (higher = more core protection = more births)
  - gamma: [0.007, 0.005, 0.003] (lower = less damping = longer lifetime)

Record for each run:
  - Total births
  - Mean lifetime (of vortices that died)
  - Late-time population
  - Births by region
  - Localization maintained?
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple
import json


class RateBalanceSimulator:
    """Branch F with tunable rate-balance parameters."""
    
    def __init__(self, size: int = 100, gamma: float = 0.007,
                 channel_coupling: float = 0.5,
                 beta_interior: float = 0.25, beta_periphery: float = 0.7,
                 transition_width: float = 15.0,
                 channel_relaxation: float = 0.01):
        self.size = size
        self.gamma = gamma
        self.channel_coupling = channel_coupling
        self.channel_relaxation = channel_relaxation
        self.beta_interior = beta_interior
        self.beta_periphery = beta_periphery
        self.transition_width = transition_width
        
        # Fields
        self.psi_r = np.ones((size, size)) * 1.2
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Channel assignment
        self.channel_assignment = np.zeros((size, size))
        
        # β landscape
        self.beta = self._create_beta_landscape()
        
        # Tracking
        self.step_count = 0
        self.vortex_lifetimes = {}
        self.next_vortex_id = 0
        self.nucleation_history = []
    
    def _create_beta_landscape(self) -> np.ndarray:
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2)
        interior_radius = self.size * 0.25
        
        beta = np.zeros((self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                dist = r[i, j]
                if dist <= interior_radius:
                    beta[i, j] = self.beta_interior
                elif dist >= interior_radius + self.transition_width:
                    beta[i, j] = self.beta_periphery
                else:
                    t = (dist - interior_radius) / self.transition_width
                    blend = 0.5 * (1 - np.cos(np.pi * t))
                    beta[i, j] = self.beta_interior + blend * (self.beta_periphery - self.beta_interior)
        return beta
    
    def get_zone(self, x: int, y: int) -> str:
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2)
        interior_radius = self.size * 0.25
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
    
    def compute_beta_weighted_laplacian(self, field: np.ndarray) -> np.ndarray:
        grad_x = (np.roll(field, -1, axis=0) - np.roll(field, 1, axis=0)) / 2
        grad_y = (np.roll(field, -1, axis=1) - np.roll(field, 1, axis=1)) / 2
        beta_grad_x = self.beta * grad_x
        beta_grad_y = self.beta * grad_y
        div_x = (np.roll(beta_grad_x, -1, axis=0) - np.roll(beta_grad_x, 1, axis=0)) / 2
        div_y = (np.roll(beta_grad_y, -1, axis=1) - np.roll(beta_grad_y, 1, axis=1)) / 2
        return div_x + div_y
    
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
        self.channel_assignment += self.channel_relaxation * (target - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
    
    def compute_channel_protection(self) -> np.ndarray:
        topology = self.compute_topology_indicator()
        topology_max = np.max(topology)
        topology_norm = topology / (topology_max + 1e-10)
        return topology_norm * self.channel_assignment
    
    def step(self, dt: float = 0.05):
        self.step_count += 1
        self.update_self_selecting_channels()
        
        lap_r = self.compute_beta_weighted_laplacian(self.psi_r)
        lap_i = self.compute_beta_weighted_laplacian(self.psi_i)
        
        amp_sq = self.psi_r**2 + self.psi_i**2
        nl_r = self.psi_r * (1 - amp_sq)
        nl_i = self.psi_i * (1 - amp_sq)
        
        acc_r = lap_r + nl_r - self.gamma * self.psi_r_dot
        acc_i = lap_i + nl_i - self.gamma * self.psi_i_dot
        
        # Core-filling suppression with tunable coupling
        protection = self.compute_channel_protection()
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.channel_coupling * protection * np.maximum(acc_radial, 0)
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
                        zone = self.get_zone(i, j)
                        vortices.append({
                            'position': (i, j),
                            'charge': int(np.sign(winding)),
                            'zone': zone
                        })
        return vortices


def run_single_test(gamma: float, channel_coupling: float, 
                    channel_relaxation: float = 0.01,
                    steps: int = 4000) -> Dict:
    """Run a single rate-balance test."""
    sim = RateBalanceSimulator(
        size=100, gamma=gamma, channel_coupling=channel_coupling,
        channel_relaxation=channel_relaxation,
        beta_interior=0.25, beta_periphery=0.7, transition_width=15.0
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
    
    vortex_birth_times = {}  # position -> birth_step
    lifetimes = []
    
    for step in range(steps):
        sim.step()
        
        if step % 25 == 0:
            vortices = sim.detect_vortices()
            current_positions = set(v['position'] for v in vortices)
            
            # Births
            new_positions = current_positions - prev_positions
            for v in vortices:
                if v['position'] in new_positions:
                    if v['zone'] == 'interior':
                        interior_births += 1
                    elif v['zone'] == 'transition':
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
    
    # Compute statistics
    total_births = interior_births + transition_births + periphery_births
    late_start = int(0.7 * len(population_history))
    late_population = np.mean(population_history[late_start:]) if population_history else 0
    mean_lifetime = np.mean(lifetimes) if lifetimes else 0
    
    # Localization check: interior+transition vs periphery births
    regen_zone_births = interior_births + transition_births
    localization_maintained = (regen_zone_births > periphery_births) if total_births > 0 else False
    
    return {
        'gamma': gamma,
        'channel_coupling': channel_coupling,
        'total_births': total_births,
        'interior_births': interior_births,
        'transition_births': transition_births,
        'periphery_births': periphery_births,
        'total_deaths': total_deaths,
        'mean_lifetime': mean_lifetime,
        'late_population': late_population,
        'localization_maintained': localization_maintained,
        'population_history_last10': population_history[-10:] if len(population_history) >= 10 else population_history
    }


def main():
    print("="*70)
    print("BRANCH F: RATE-BALANCE SWEEP")
    print("="*70)
    print()
    print("Goal: Find γ, coupling that achieve late_population > 0")
    print("      while maintaining spatial localization")
    print()
    
    # Parameter grid
    gammas = [0.007, 0.005, 0.003]  # damping: baseline, lower, much lower
    couplings = [0.5, 0.7, 0.9]    # channel coupling: baseline, higher, much higher
    
    results = []
    best_result = None
    best_late_pop = 0
    
    print("γ\\coupling |  0.5   |  0.7   |  0.9   |")
    print("-" * 45)
    
    for gamma in gammas:
        row = f"  {gamma:.3f}   |"
        for coupling in couplings:
            result = run_single_test(gamma=gamma, channel_coupling=coupling)
            results.append(result)
            
            late_pop = result['late_population']
            births = result['total_births']
            localized = "✓" if result['localization_maintained'] else " "
            
            row += f" {late_pop:4.1f}{localized} |"
            
            if late_pop > best_late_pop:
                best_late_pop = late_pop
                best_result = result
        
        print(row)
    
    print()
    print("Legend: value = late_population, ✓ = localization maintained")
    print()
    
    # Detailed results
    print("="*70)
    print("DETAILED RESULTS")
    print("="*70)
    print()
    
    for r in results:
        status = "✓" if r['late_population'] > 0.5 else " "
        loc = "✓" if r['localization_maintained'] else "✗"
        print(f"{status} γ={r['gamma']:.3f}, coupling={r['channel_coupling']:.1f}: "
              f"births={r['total_births']:3d}, "
              f"lifetime={r['mean_lifetime']:.0f}, "
              f"late_pop={r['late_population']:.2f}, "
              f"loc={loc}")
        print(f"    Interior:{r['interior_births']:3d}, Trans:{r['transition_births']:3d}, "
              f"Periph:{r['periphery_births']:3d}")
    
    print()
    print("="*70)
    print("BEST CONFIGURATION")
    print("="*70)
    
    if best_result and best_result['late_population'] > 0.5:
        print(f"✓ SUCCESS: Found nonzero late population!")
        print(f"  γ = {best_result['gamma']}")
        print(f"  channel_coupling = {best_result['channel_coupling']}")
        print(f"  late_population = {best_result['late_population']:.2f}")
        print(f"  total_births = {best_result['total_births']}")
        print(f"  mean_lifetime = {best_result['mean_lifetime']:.0f}")
        print(f"  localization_maintained = {best_result['localization_maintained']}")
        print()
        print("The spatial separation mechanism can sustain a nonzero population")
        print("when regeneration and decay rates are properly balanced.")
    else:
        print(f"Best result: late_pop = {best_late_pop:.2f}")
        if best_result:
            print(f"  γ = {best_result['gamma']}, coupling = {best_result['channel_coupling']}")
            print(f"  births = {best_result['total_births']}, lifetime = {best_result['mean_lifetime']:.0f}")
        print()
        print("Regeneration rate still insufficient. Consider:")
        print("  - Even lower damping")
        print("  - Even higher coupling")
        print("  - Faster channel relaxation")
    
    # Save results
    with open('/app/backend/qmrt_topology/test_results/phase5/branch_f_rate_balance.json', 'w') as f:
        json.dump(results, f, indent=2, default=lambda x: bool(x) if isinstance(x, np.bool_) else x)
    
    print()
    print("Results saved to branch_f_rate_balance.json")
    
    return results


if __name__ == "__main__":
    main()
