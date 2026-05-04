"""
Branch F v2: Inverted Gradient Test
====================================

CRITICAL CAUSAL TEST:
- Original: high coupling at center (0.8), low at edge (0.2) → inward drift
- Inverted: high coupling at edge (0.8), low at center (0.2) → outward drift?

If drift reverses, the coupling gradient causally controls defect transport direction.
This would be one of the cleanest results in the program.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Dict, List
import json


class InvertedGradientSimulator:
    """
    Same as BranchFv2Simulator but with INVERTED coupling gradient:
    - LOW coupling at center
    - HIGH coupling at periphery
    """
    
    def __init__(
        self,
        size: int = 100,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.007,
        lambda_relax: float = 0.5,
        beta: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
        omega_1: float = 0.3,
        omega_2: float = 0.8,
        coupling_center: float = 0.2,   # LOW at center (inverted)
        coupling_edge: float = 0.8,     # HIGH at edge (inverted)
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
        
        # Oscillators
        self.chi_1 = np.zeros((size, size))
        self.chi_1_dot = np.zeros((size, size))
        self.chi_2 = np.zeros((size, size))
        self.chi_2_dot = np.zeros((size, size))
        self.channel_assignment = np.zeros((size, size))
        
        # Spatially varying channel coupling (INVERTED)
        self.channel_coupling_field = self._create_inverted_coupling_landscape()
        
        self.step_count = 0
    
    def _create_inverted_coupling_landscape(self) -> np.ndarray:
        """LOW coupling in center, HIGH at edges (inverted from original)."""
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2)
        
        interior_radius = self.size * 0.3
        
        coupling = np.zeros((self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                dist = r[i, j]
                if dist <= interior_radius:
                    coupling[i, j] = self.coupling_center  # LOW
                elif dist >= interior_radius + self.transition_width:
                    coupling[i, j] = self.coupling_edge    # HIGH
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
        self.step_count += 1
        self.update_self_selecting_channels()
        
        # Oscillators
        self.chi_1_dot += -self.omega_1**2 * self.chi_1 * self.dt
        self.chi_1 += self.chi_1_dot * self.dt
        self.chi_2_dot += -self.omega_2**2 * self.chi_2 * self.dt
        self.chi_2 += self.chi_2_dot * self.dt
        
        # Medium dynamics
        rho = self.rho
        tau_eq = self.tau_0 / (1 + self.beta * gaussian_filter(rho, sigma=2.0) / (np.max(rho) + 1e-10))
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
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
        
        # Core-filling suppression with INVERTED spatial coupling
        protection = self.compute_channel_protection()
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


def run_comparison_test(steps: int = 8000):
    """
    Run both original and inverted gradients, compare migration.
    """
    from branch_f_v2 import BranchFv2Simulator
    
    results = {}
    
    for label, SimClass, cc, ce in [
        ('ORIGINAL (high center)', BranchFv2Simulator, 0.8, 0.2),
        ('INVERTED (high edge)', InvertedGradientSimulator, 0.2, 0.8),
    ]:
        print(f"\n--- {label} ---")
        print(f"Center coupling: {cc}, Edge coupling: {ce}")
        
        sim = SimClass(
            size=100, gamma=0.007,
            coupling_center=cc, coupling_edge=ce,
            transition_width=20.0
        )
        
        # Verify coupling landscape
        print(f"  Coupling at (50,50): {sim.channel_coupling_field[50, 50]:.2f}")
        print(f"  Coupling at (90,50): {sim.channel_coupling_field[90, 50]:.2f}")
        
        # Seed
        center = sim.size // 2
        np.random.seed(42)
        sim.psi_r[:] = 1.2
        sim.psi_i[:] = 0.0
        
        for i, pos in enumerate([(center-5, center), (center+5, center), (center, center-8), (center, center+8)]):
            charge = 1 if i % 2 == 0 else -1
            x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
            r = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
            theta = np.arctan2(y - pos[1], x - pos[0])
            amp = 1.2 * np.tanh(r / 4.0)
            psi = sim.psi_r + 1j * sim.psi_i
            psi *= (amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
            sim.psi_r = np.real(psi)
            sim.psi_i = np.imag(psi)
        
        sim.psi_r += 0.05 * np.random.randn(100, 100)
        sim.psi_i += 0.05 * np.random.randn(100, 100)
        
        # Track vortices and migration
        vortex_tracks = {}
        next_id = 0
        prev_vortices = {}
        
        population_history = []
        interior_pop_history = []
        periphery_pop_history = []
        
        for step in range(steps):
            sim.step()
            
            if step % 25 == 0:
                vortices = sim.detect_vortices()
                current_positions = {v['position']: v for v in vortices}
                
                # Track
                new_prev = {}
                matched_ids = set()
                
                for pos, v in current_positions.items():
                    best_id = None
                    best_dist = 15
                    
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
                        vortex_tracks[best_id]['positions'].append(pos)
                    else:
                        vid = next_id
                        next_id += 1
                        new_prev[pos] = vid
                        vortex_tracks[vid] = {
                            'birth_step': step,
                            'positions': [pos]
                        }
                
                for prev_pos, prev_id in prev_vortices.items():
                    if prev_id not in matched_ids:
                        vortex_tracks[prev_id]['death_step'] = step
                
                prev_vortices = new_prev
                
                # Population by zone
                n_interior = sum(1 for v in vortices if v['zone'] == 'interior')
                n_periphery = sum(1 for v in vortices if v['zone'] == 'periphery')
                population_history.append(len(vortices))
                interior_pop_history.append(n_interior)
                periphery_pop_history.append(n_periphery)
        
        # Analyze radial displacement
        radial_displacements = []
        for vid, track in vortex_tracks.items():
            if 'death_step' in track and len(track['positions']) >= 2:
                start_pos = track['positions'][0]
                end_pos = track['positions'][-1]
                
                center = 50
                r_start = np.sqrt((start_pos[0] - center)**2 + (start_pos[1] - center)**2)
                r_end = np.sqrt((end_pos[0] - center)**2 + (end_pos[1] - center)**2)
                
                radial_displacements.append(r_end - r_start)
        
        mean_radial = np.mean(radial_displacements) if radial_displacements else 0
        
        # Late-time population
        late_start = int(0.7 * len(population_history))
        late_pop = np.mean(population_history[late_start:])
        late_interior = np.mean(interior_pop_history[late_start:])
        late_periphery = np.mean(periphery_pop_history[late_start:])
        
        print(f"  Mean radial displacement: {mean_radial:+.2f} (+ = outward)")
        print(f"  Late population: {late_pop:.1f}")
        print(f"  Late interior: {late_interior:.1f} ({100*late_interior/late_pop:.1f}%)")
        print(f"  Late periphery: {late_periphery:.1f} ({100*late_periphery/late_pop:.1f}%)")
        
        results[label] = {
            'mean_radial_displacement': mean_radial,
            'late_population': late_pop,
            'late_interior_fraction': late_interior / late_pop if late_pop > 0 else 0,
            'late_periphery_fraction': late_periphery / late_pop if late_pop > 0 else 0,
            'n_tracks': len(radial_displacements)
        }
    
    return results


def main():
    print("="*70)
    print("BRANCH F v2: INVERTED GRADIENT TEST")
    print("="*70)
    print()
    print("CRITICAL CAUSAL TEST:")
    print("  Original: high coupling at center → inward drift?")
    print("  Inverted: high coupling at edge → outward drift?")
    print()
    print("If drift REVERSES, coupling gradient causally controls defect transport.")
    
    results = run_comparison_test(steps=8000)
    
    print()
    print("="*70)
    print("COMPARISON")
    print("="*70)
    print()
    
    orig = results['ORIGINAL (high center)']
    inv = results['INVERTED (high edge)']
    
    print(f"{'Metric':<30} | {'Original':>12} | {'Inverted':>12}")
    print("-"*60)
    print(f"{'Mean radial displacement':<30} | {orig['mean_radial_displacement']:>+12.2f} | {inv['mean_radial_displacement']:>+12.2f}")
    print(f"{'Late population':<30} | {orig['late_population']:>12.1f} | {inv['late_population']:>12.1f}")
    print(f"{'Interior fraction':<30} | {orig['late_interior_fraction']*100:>11.1f}% | {inv['late_interior_fraction']*100:>11.1f}%")
    print(f"{'Periphery fraction':<30} | {orig['late_periphery_fraction']*100:>11.1f}% | {inv['late_periphery_fraction']*100:>11.1f}%")
    
    print()
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()
    
    # Check if drift reversed
    drift_reversed = (orig['mean_radial_displacement'] < 0 and inv['mean_radial_displacement'] > 0)
    
    # Check if localization flipped
    localization_flipped = (orig['late_interior_fraction'] > orig['late_periphery_fraction'] and
                            inv['late_periphery_fraction'] > inv['late_interior_fraction'])
    
    if drift_reversed:
        print("✓✓ DRIFT REVERSED: Coupling gradient CAUSALLY CONTROLS defect transport direction")
        print(f"   Original: {orig['mean_radial_displacement']:+.2f} (inward)")
        print(f"   Inverted: {inv['mean_radial_displacement']:+.2f} (outward)")
    elif inv['mean_radial_displacement'] > orig['mean_radial_displacement']:
        print("~ PARTIAL: Inverted gradient shows MORE outward drift")
        print(f"   Original: {orig['mean_radial_displacement']:+.2f}")
        print(f"   Inverted: {inv['mean_radial_displacement']:+.2f}")
    else:
        print("✗ No drift reversal detected")
    
    print()
    
    if localization_flipped:
        print("✓✓ LOCALIZATION FLIPPED: Population now concentrated at PERIPHERY")
        print(f"   Original: {orig['late_interior_fraction']*100:.1f}% interior, {orig['late_periphery_fraction']*100:.1f}% periphery")
        print(f"   Inverted: {inv['late_interior_fraction']*100:.1f}% interior, {inv['late_periphery_fraction']*100:.1f}% periphery")
    elif inv['late_periphery_fraction'] > orig['late_periphery_fraction']:
        print("~ PARTIAL: Inverted gradient has MORE periphery population")
    else:
        print("✗ Localization did not flip")
    
    print()
    
    if drift_reversed and localization_flipped:
        print("="*70)
        print("★ CAUSAL CONTROL DEMONSTRATED ★")
        print("="*70)
        print()
        print("The coupling gradient direction determines:")
        print("  1. Defect drift direction")
        print("  2. Population localization")
        print()
        print("This is one of the cleanest causal results in the program.")
    
    # Save results
    with open('/app/backend/qmrt_topology/test_results/phase5/inverted_gradient_test.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("Results saved to inverted_gradient_test.json")


if __name__ == "__main__":
    main()
