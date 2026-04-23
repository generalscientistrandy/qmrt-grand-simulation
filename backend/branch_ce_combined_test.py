"""
Branch C + E Combined Test: Localized Topological Memory
========================================================

Question: Can β-localized organization wells convert remnant amplification 
          into localized, stable topological populations?

Four Key Measurements:
1. Spatial localization — vortex density inside vs outside β wells
2. Hotspot overlap — do regeneration hotspots concentrate in high-β regions?
3. Population persistence by region — mean vortex count inside vs outside
4. Lifetime distribution by region — do vortices live longer in β wells?

Success criteria:
- Nonzero long-time population
- Higher density inside high-β regions
- Regeneration hotspots biased toward β wells
- Longer mean lifetime inside wells
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class CombinedCESimulator:
    """
    Combined Branch C (β-coupling) + Branch E (self-selecting resonance).
    
    Features:
    - β-weighted Laplacian (Branch C)
    - Self-selecting channel dynamics (Branch E)
    - Spatial β wells for localization testing
    """
    
    def __init__(
        self,
        size: int = 100,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.007,
        lambda_relax: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
        # Branch C: β-coupling
        beta_inside: float = 0.8,
        beta_outside: float = 0.25,
        # Branch E: resonance
        omega_1: float = 0.3,
        omega_2: float = 0.8,
        channel_coupling: float = 0.5,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.dt = dt
        self.beta_inside = beta_inside
        self.beta_outside = beta_outside
        self.omega_1 = omega_1
        self.omega_2 = omega_2
        self.channel_coupling = channel_coupling
        
        # Fields
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        # β field (Branch C)
        self.beta_field = np.ones((size, size)) * beta_outside
        self.well_mask = np.zeros((size, size), dtype=bool)
        
        # Channels (Branch E)
        self.chi_1 = np.zeros((size, size))
        self.chi_1_dot = np.zeros((size, size))
        self.chi_2 = np.zeros((size, size))
        self.chi_2_dot = np.zeros((size, size))
        self.channel_assignment = np.zeros((size, size))
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    @property
    def rho(self) -> np.ndarray:
        return self.psi_r**2 + self.psi_i**2 + self.psi_r_dot**2 + self.psi_i_dot**2
    
    def create_beta_wells(self, centers: List[Tuple[int, int]], radii: List[float]):
        """Create high-β wells at specified locations."""
        self.beta_field = np.ones((self.size, self.size)) * self.beta_outside
        self.well_mask = np.zeros((self.size, self.size), dtype=bool)
        
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        
        for center, radius in zip(centers, radii):
            r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            inside = r <= radius
            self.beta_field[inside] = self.beta_inside
            self.well_mask[inside] = True
    
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
    
    def compute_beta_weighted_laplacian(self, f: np.ndarray) -> np.ndarray:
        """∇·(β∇f) = β∇²f + ∇β·∇f"""
        lap_f = (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                 np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
        
        df_dx = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) / 2
        df_dy = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / 2
        
        dbeta_dx = (np.roll(self.beta_field, -1, 0) - np.roll(self.beta_field, 1, 0)) / 2
        dbeta_dy = (np.roll(self.beta_field, -1, 1) - np.roll(self.beta_field, 1, 1)) / 2
        
        return self.beta_field * lap_f + dbeta_dx * df_dx + dbeta_dy * df_dy
    
    def step(self, mode: str = 'combined'):
        """
        Modes:
        - 'none': No special dynamics (baseline)
        - 'beta_only': Only β-coupling (Branch C)
        - 'resonance_only': Only self-selection (Branch E)
        - 'combined': Both β-coupling AND self-selection (C+E)
        """
        use_beta = mode in ['beta_only', 'combined']
        use_resonance = mode in ['resonance_only', 'combined']
        
        # Update channels (Branch E)
        if use_resonance:
            self.update_self_selecting_channels()
        
        # Oscillators
        self.chi_1_dot += -self.omega_1**2 * self.chi_1 * self.dt
        self.chi_1 += self.chi_1_dot * self.dt
        self.chi_2_dot += -self.omega_2**2 * self.chi_2 * self.dt
        self.chi_2 += self.chi_2_dot * self.dt
        
        # Medium
        rho = self.rho
        tau_eq = self.tau_0 / (1 + self.beta_field * gaussian_filter(rho, sigma=2.0) / (np.max(rho) + 1e-10))
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave evolution
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        # Laplacian (β-weighted or standard)
        if use_beta:
            lap_r = self.compute_beta_weighted_laplacian(self.psi_r)
            lap_i = self.compute_beta_weighted_laplacian(self.psi_i)
        else:
            lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                     np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
            lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                     np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Channel protection (Branch E)
        if use_resonance:
            protection = self.compute_channel_protection()
            amp = self.amplitude + 1e-10
            radial_r = self.psi_r / amp
            radial_i = self.psi_i / amp
            acc_radial = acc_r * radial_r + acc_i * radial_i
            suppression = self.channel_coupling * protection * np.maximum(acc_radial, 0)
            acc_r -= suppression * radial_r
            acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def add_vortex(self, center: Tuple[int, int], charge: int = 1, 
                   amplitude: float = 1.0, core_radius: float = 3.0):
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        dx = x - center[0]
        dy = y - center[1]
        r = np.sqrt(dx**2 + dy**2 + 0.01)
        theta = np.arctan2(dy, dx)
        amp_profile = amplitude * np.tanh(r / core_radius)
        phase = charge * theta
        
        if np.max(np.abs(self.psi_r)) < 0.01:
            self.psi_r = amp_profile * np.cos(phase)
            self.psi_i = amp_profile * np.sin(phase)
        else:
            psi_existing = self.psi_r + 1j * self.psi_i
            psi_vortex = amp_profile * np.exp(1j * phase)
            combined = psi_existing * psi_vortex / (amplitude + 0.01)
            self.psi_r = np.real(combined)
            self.psi_i = np.imag(combined)
    
    def seed_oscillators(self, amp: float = 0.1):
        self.chi_1 = amp * np.random.randn(self.size, self.size)
        self.chi_1_dot = self.omega_1 * amp * np.random.randn(self.size, self.size)
        self.chi_2 = amp * np.random.randn(self.size, self.size)
        self.chi_2_dot = self.omega_2 * amp * np.random.randn(self.size, self.size)
    
    def compute_winding_number(self, i: int, j: int, radius: int = 2) -> float:
        phase = self.phase
        loop_points = []
        for dj in range(-radius, radius+1):
            loop_points.append((i-radius, j+dj))
        for di in range(-radius+1, radius+1):
            loop_points.append((i+di, j+radius))
        for dj in range(radius-1, -radius-1, -1):
            loop_points.append((i+radius, j+dj))
        for di in range(radius-1, -radius, -1):
            loop_points.append((i+di, j-radius))
        
        total = 0
        for k in range(len(loop_points)):
            ni, nj = loop_points[k]
            ni_next, nj_next = loop_points[(k+1) % len(loop_points)]
            ni, nj = ni % self.size, nj % self.size
            ni_next, nj_next = ni_next % self.size, nj_next % self.size
            dp = phase[ni_next, nj_next] - phase[ni, nj]
            while dp > np.pi: dp -= 2*np.pi
            while dp < -np.pi: dp += 2*np.pi
            total += dp
        return total / (2*np.pi)
    
    def detect_all_vortices(self, amp_threshold: float = 0.4) -> List[Dict]:
        vortices = []
        amp = self.amplitude
        checked = set()
        
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                if (i, j) in checked:
                    continue
                    
                if amp[i, j] < amp_threshold:
                    region = amp[max(0,i-1):i+2, max(0,j-1):j+2]
                    if amp[i, j] <= np.min(region):
                        winding = self.compute_winding_number(i, j, radius=2)
                        if abs(winding) > 0.5:
                            vortices.append({
                                'position': (i, j),
                                'charge': int(np.round(winding)),
                                'in_well': bool(self.well_mask[i, j]),
                                'beta': float(self.beta_field[i, j]),
                                'channel': float(self.channel_assignment[i, j])
                            })
                            for di in range(-3, 4):
                                for dj in range(-3, 4):
                                    checked.add((i+di, j+dj))
        
        return vortices


def run_combined_test():
    """
    Main test: Compare β-only, resonance-only, and combined modes.
    """
    print("="*70)
    print("BRANCH C + E COMBINED TEST")
    print("="*70)
    print()
    print("Question: Can β wells bias topological memory into localized populations?")
    print()
    
    size = 100
    steps = 6000
    sample_interval = 50
    
    # β well configuration
    well_centers = [(35, 50), (65, 50)]  # Two wells
    well_radii = [15, 15]
    
    modes = ['none', 'beta_only', 'resonance_only', 'combined']
    
    all_results = {}
    
    for mode in modes:
        print(f"--- {mode.upper()} ---")
        
        sim = CombinedCESimulator(size=size, gamma=0.007, beta_inside=0.8, beta_outside=0.25)
        sim.create_beta_wells(well_centers, well_radii)
        sim.channel_assignment[:] = 0
        
        # Seed vortices both inside and outside wells
        sim.psi_r[:] = 1.2
        # Inside wells
        sim.add_vortex((35, 50), charge=+1, amplitude=1.2, core_radius=4.0)
        sim.add_vortex((65, 50), charge=-1, amplitude=1.2, core_radius=4.0)
        # Outside wells
        sim.add_vortex((50, 20), charge=+1, amplitude=1.2, core_radius=4.0)
        sim.add_vortex((50, 80), charge=-1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        # Tracking
        total_counts = []
        inside_counts = []
        outside_counts = []
        nucleation_inside = 0
        nucleation_outside = 0
        nucleation_heatmap = np.zeros((size, size))
        
        prev_positions = set()
        
        for step in range(steps):
            sim.step(mode=mode)
            
            if step % sample_interval == 0:
                vortices = sim.detect_all_vortices(amp_threshold=0.4)
                current_positions = set(v['position'] for v in vortices)
                
                # Count by region
                n_total = len(vortices)
                n_inside = sum(1 for v in vortices if v['in_well'])
                n_outside = n_total - n_inside
                
                total_counts.append(n_total)
                inside_counts.append(n_inside)
                outside_counts.append(n_outside)
                
                # Track nucleation events
                new_positions = current_positions - prev_positions
                for pos in new_positions:
                    nucleation_heatmap[pos[0], pos[1]] += 1
                    if sim.well_mask[pos[0], pos[1]]:
                        nucleation_inside += 1
                    else:
                        nucleation_outside += 1
                
                prev_positions = current_positions
        
        # Analysis
        late_total = np.mean(total_counts[-20:])
        late_inside = np.mean(inside_counts[-20:])
        late_outside = np.mean(outside_counts[-20:])
        
        # Well area fraction
        well_area = np.sum(sim.well_mask)
        total_area = size * size
        well_fraction = well_area / total_area
        
        # Expected inside count if uniform
        expected_inside = late_total * well_fraction
        
        # Localization ratio
        if late_total > 0 and expected_inside > 0:
            localization_ratio = late_inside / expected_inside
        else:
            localization_ratio = 0
        
        # Nucleation bias
        total_nucleations = nucleation_inside + nucleation_outside
        if total_nucleations > 0:
            nucleation_inside_frac = nucleation_inside / total_nucleations
            nucleation_bias = nucleation_inside_frac / well_fraction if well_fraction > 0 else 0
        else:
            nucleation_bias = 0
        
        all_results[mode] = {
            'late_total': late_total,
            'late_inside': late_inside,
            'late_outside': late_outside,
            'localization_ratio': localization_ratio,
            'nucleation_inside': nucleation_inside,
            'nucleation_outside': nucleation_outside,
            'nucleation_bias': nucleation_bias,
            'total_counts': total_counts,
            'inside_counts': inside_counts,
        }
        
        print(f"  Late population: {late_total:.1f} (inside={late_inside:.1f}, outside={late_outside:.1f})")
        print(f"  Localization ratio: {localization_ratio:.2f} (>1 = biased to wells)")
        print(f"  Nucleation: {nucleation_inside} inside, {nucleation_outside} outside")
        print(f"  Nucleation bias: {nucleation_bias:.2f} (>1 = biased to wells)")
        print()
    
    # Summary comparison
    print("="*70)
    print("COMPARISON TABLE")
    print("="*70)
    print()
    print("| Mode | Late Pop | Inside | Outside | Local Ratio | Nucl Bias |")
    print("|------|----------|--------|---------|-------------|-----------|")
    
    for mode in modes:
        r = all_results[mode]
        print(f"| {mode:14} | {r['late_total']:>8.1f} | {r['late_inside']:>6.1f} | "
              f"{r['late_outside']:>7.1f} | {r['localization_ratio']:>11.2f} | {r['nucleation_bias']:>9.2f} |")
    
    print()
    
    # Verdict
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()
    
    combined = all_results['combined']
    resonance = all_results['resonance_only']
    beta = all_results['beta_only']
    
    # Check for co-alignment
    population_maintained = combined['late_total'] > 1
    localization_improved = combined['localization_ratio'] > resonance['localization_ratio'] * 1.2
    nucleation_biased = combined['nucleation_bias'] > 1.5
    
    print(f"1. Population maintained: {'✓ YES' if population_maintained else '✗ NO'} ({combined['late_total']:.1f})")
    print(f"2. Localization improved over E-only: {'✓ YES' if localization_improved else '✗ NO'} "
          f"({combined['localization_ratio']:.2f} vs {resonance['localization_ratio']:.2f})")
    print(f"3. Nucleation biased to wells: {'✓ YES' if nucleation_biased else '✗ NO'} ({combined['nucleation_bias']:.2f})")
    print()
    
    if population_maintained and (localization_improved or nucleation_biased):
        print("CONCLUSION: CO-ALIGNMENT ACHIEVED")
        print("β wells DO bias topological memory toward localized populations.")
        print("This is the first evidence of organization + topology co-aligning.")
    elif population_maintained:
        print("CONCLUSION: POPULATION MAINTAINED BUT NOT LOCALIZED")
        print("Topological memory works, but β wells don't concentrate it.")
    else:
        print("CONCLUSION: NO CO-ALIGNMENT")
        print("Combined mode does not achieve localized topological populations.")
    
    return all_results


def analyze_hotspot_overlap():
    """
    Detailed analysis: Do regeneration hotspots concentrate in β wells?
    """
    print()
    print("="*70)
    print("HOTSPOT OVERLAP ANALYSIS")
    print("="*70)
    print()
    
    size = 100
    steps = 6000
    
    well_centers = [(35, 50), (65, 50)]
    well_radii = [15, 15]
    
    for mode in ['resonance_only', 'combined']:
        print(f"--- {mode.upper()} ---")
        
        sim = CombinedCESimulator(size=size, gamma=0.007)
        sim.create_beta_wells(well_centers, well_radii)
        sim.channel_assignment[:] = 0
        
        sim.psi_r[:] = 1.2
        sim.add_vortex((35, 50), charge=+1, amplitude=1.2, core_radius=4.0)
        sim.add_vortex((65, 50), charge=-1, amplitude=1.2, core_radius=4.0)
        sim.add_vortex((50, 20), charge=+1, amplitude=1.2, core_radius=4.0)
        sim.add_vortex((50, 80), charge=-1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        nucleation_heatmap = np.zeros((size, size))
        prev_positions = set()
        
        for step in range(steps):
            sim.step(mode=mode)
            
            if step % 30 == 0:
                vortices = sim.detect_all_vortices(amp_threshold=0.4)
                current_positions = set(v['position'] for v in vortices)
                new_positions = current_positions - prev_positions
                for pos in new_positions:
                    nucleation_heatmap[pos[0], pos[1]] += 1
                prev_positions = current_positions
        
        # Find hotspots
        hotspots_inside = []
        hotspots_outside = []
        
        for i in range(size):
            for j in range(size):
                if nucleation_heatmap[i, j] >= 2:
                    if sim.well_mask[i, j]:
                        hotspots_inside.append((i, j, nucleation_heatmap[i, j]))
                    else:
                        hotspots_outside.append((i, j, nucleation_heatmap[i, j]))
        
        print(f"  Hotspots inside wells: {len(hotspots_inside)}")
        print(f"  Hotspots outside wells: {len(hotspots_outside)}")
        
        total_hotspots = len(hotspots_inside) + len(hotspots_outside)
        if total_hotspots > 0:
            inside_frac = len(hotspots_inside) / total_hotspots
            well_area_frac = np.sum(sim.well_mask) / (size * size)
            concentration = inside_frac / well_area_frac if well_area_frac > 0 else 0
            print(f"  Hotspot concentration in wells: {concentration:.2f}× expected")
        
        if hotspots_inside:
            print(f"  Top inside hotspots: {sorted(hotspots_inside, key=lambda x: -x[2])[:3]}")
        if hotspots_outside:
            print(f"  Top outside hotspots: {sorted(hotspots_outside, key=lambda x: -x[2])[:3]}")
        print()


def main():
    print("="*70)
    print("BRANCH C + E COMBINED TEST: LOCALIZED TOPOLOGICAL MEMORY")
    print("="*70)
    print()
    print("Goal: Test if β wells can bias where topological memory is maintained")
    print()
    
    results = run_combined_test()
    analyze_hotspot_overlap()
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("Key questions answered:")
    print("1. Does combined mode maintain nonzero population? (Check late_total)")
    print("2. Is population biased toward β wells? (Check localization_ratio)")
    print("3. Does nucleation preferentially occur in wells? (Check nucleation_bias)")
    print("4. Do hotspots concentrate in wells? (Check hotspot analysis)")


if __name__ == "__main__":
    main()
