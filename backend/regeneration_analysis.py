"""
Topological Regeneration Analysis
=================================

Key Questions:
1. Where do vortices reappear? (Spatial localization)
2. How often? (Nucleation rate)
3. Is regeneration from baseline or remnant amplification?
4. Can a steady-state population be maintained?

Metrics:
- Nucleation rate α
- Annihilation rate β  
- Net population growth
- Spatial heatmap of nucleation events
- Topology indicator between death and rebirth
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class RegenerationAnalysisSimulator:
    """
    Simulator with detailed tracking for regeneration analysis.
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.007,
        lambda_relax: float = 0.5,
        beta: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
        omega_1: float = 0.3,
        omega_2: float = 0.8,
        channel_coupling: float = 0.5,
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
        self.channel_coupling = channel_coupling
        
        # Fields
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        # Channels
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
    
    def compute_topology_indicator(self) -> np.ndarray:
        """Phase gradient magnitude - high near vortex cores."""
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
    
    def step(self, mode: str = 'none'):
        if mode == 'self_selecting':
            self.update_self_selecting_channels()
        
        # Oscillators
        self.chi_1_dot += -self.omega_1**2 * self.chi_1 * self.dt
        self.chi_1 += self.chi_1_dot * self.dt
        self.chi_2_dot += -self.omega_2**2 * self.chi_2 * self.dt
        self.chi_2 += self.chi_2_dot * self.dt
        
        # Medium
        rho = self.rho
        tau_eq = self.tau_0 / (1 + self.beta * gaussian_filter(rho, sigma=2.0) / (np.max(rho) + 1e-10))
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                 np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
        lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                 np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        if mode == 'self_selecting':
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
        """Detect all vortices in the field."""
        vortices = []
        amp = self.amplitude
        checked = set()
        
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                if (i, j) in checked:
                    continue
                    
                if amp[i, j] < amp_threshold:
                    # Check if local minimum
                    region = amp[max(0,i-1):i+2, max(0,j-1):j+2]
                    if amp[i, j] <= np.min(region):
                        winding = self.compute_winding_number(i, j, radius=2)
                        if abs(winding) > 0.5:
                            vortices.append({
                                'position': (i, j),
                                'charge': int(np.round(winding)),
                                'amplitude': float(amp[i, j]),
                                'channel': float(self.channel_assignment[i, j])
                            })
                            # Mark nearby cells as checked
                            for di in range(-3, 4):
                                for dj in range(-3, 4):
                                    checked.add((i+di, j+dj))
        
        return vortices


def analyze_regeneration_dynamics():
    """
    Track nucleation and annihilation events to understand regeneration.
    """
    print("="*70)
    print("REGENERATION DYNAMICS ANALYSIS")
    print("="*70)
    print()
    
    size = 80
    steps = 4000
    sample_interval = 20
    
    for mode in ['none', 'self_selecting']:
        print(f"--- {mode.upper()} ---")
        print()
        
        sim = RegenerationAnalysisSimulator(size=size, gamma=0.007)
        sim.channel_assignment[:] = 0
        
        # Seed with a pair
        v1_pos = (size//2 - 12, size//2)
        v2_pos = (size//2 + 12, size//2)
        sim.psi_r[:] = 1.2
        sim.add_vortex(v1_pos, charge=+1, amplitude=1.2, core_radius=4.0)
        sim.add_vortex(v2_pos, charge=-1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        # Tracking
        vortex_counts = []
        topology_indicators = []  # Max topology indicator (for remnant detection)
        nucleation_events = []
        annihilation_events = []
        nucleation_heatmap = np.zeros((size, size))
        
        prev_vortices = set()
        prev_count = 0
        
        for step in range(steps):
            sim.step(mode=mode)
            
            if step % sample_interval == 0:
                vortices = sim.detect_all_vortices(amp_threshold=0.4)
                current_positions = set(v['position'] for v in vortices)
                count = len(vortices)
                
                vortex_counts.append(count)
                topology_indicators.append(np.max(sim.compute_topology_indicator()))
                
                # Detect nucleation (new positions)
                new_positions = current_positions - prev_vortices
                for pos in new_positions:
                    nucleation_events.append({'step': step, 'position': pos})
                    nucleation_heatmap[pos[0], pos[1]] += 1
                
                # Detect annihilation (disappeared positions)
                lost_positions = prev_vortices - current_positions
                for pos in lost_positions:
                    annihilation_events.append({'step': step, 'position': pos})
                
                prev_vortices = current_positions
                prev_count = count
        
        # Analysis
        print(f"Total nucleation events: {len(nucleation_events)}")
        print(f"Total annihilation events: {len(annihilation_events)}")
        print()
        
        # Population over time
        print("Vortex count trajectory:")
        for i in range(0, len(vortex_counts), 50):
            t = i * sample_interval
            print(f"  t={t:>4}: count={vortex_counts[i]:>3}, max_topology={topology_indicators[i]:.3f}")
        print()
        
        # Nucleation rate (events per 1000 steps)
        if len(nucleation_events) > 0:
            nucleation_rate = len(nucleation_events) / (steps / 1000)
            print(f"Nucleation rate: {nucleation_rate:.2f} events per 1000 steps")
        
        # Spatial distribution of nucleation
        if np.sum(nucleation_heatmap) > 0:
            # Find hotspots
            hotspots = []
            for i in range(size):
                for j in range(size):
                    if nucleation_heatmap[i, j] >= 2:
                        hotspots.append((i, j, nucleation_heatmap[i, j]))
            
            if hotspots:
                print(f"Nucleation hotspots (>=2 events): {len(hotspots)}")
                for h in sorted(hotspots, key=lambda x: -x[2])[:5]:
                    print(f"  ({h[0]}, {h[1]}): {h[2]:.0f} events")
        
        print()
        print("-"*40)
        print()


def test_remnant_vs_spontaneous():
    """
    Test whether regeneration is from remnants or truly spontaneous.
    
    Key diagnostic: Does topology indicator return to baseline 
    between annihilation and re-nucleation?
    """
    print("="*70)
    print("REMNANT VS SPONTANEOUS NUCLEATION TEST")
    print("="*70)
    print()
    print("Question: Does topology indicator return to baseline before rebirth?")
    print()
    
    size = 80
    steps = 3000
    
    sim = RegenerationAnalysisSimulator(size=size, gamma=0.007)
    sim.channel_assignment[:] = 0
    
    v1_pos = (size//2 - 12, size//2)
    v2_pos = (size//2 + 12, size//2)
    sim.psi_r[:] = 1.2
    sim.add_vortex(v1_pos, charge=+1, amplitude=1.2, core_radius=4.0)
    sim.add_vortex(v2_pos, charge=-1, amplitude=1.2, core_radius=4.0)
    sim.seed_oscillators(amp=0.1)
    
    # Track topology indicator over time
    times = []
    max_topology = []
    mean_topology = []
    vortex_counts = []
    
    for step in range(steps):
        sim.step(mode='self_selecting')
        
        if step % 10 == 0:
            topo = sim.compute_topology_indicator()
            vortices = sim.detect_all_vortices(amp_threshold=0.4)
            
            times.append(step)
            max_topology.append(np.max(topo))
            mean_topology.append(np.mean(topo))
            vortex_counts.append(len(vortices))
    
    print("Time | Vortices | Max Topo | Mean Topo | Status")
    print("-"*55)
    
    # Find key transitions
    prev_count = 2
    zero_topo_seen = False
    
    for i, (t, count, max_t, mean_t) in enumerate(zip(times, vortex_counts, max_topology, mean_topology)):
        if t % 100 == 0 or (prev_count > 0 and count == 0) or (prev_count == 0 and count > 0):
            status = ""
            if prev_count > 0 and count == 0:
                status = "← DEATH"
            elif prev_count == 0 and count > 0:
                status = "← REBIRTH"
                if zero_topo_seen:
                    status += " (after baseline)"
                else:
                    status += " (from remnant?)"
            
            # Check if topology returned to baseline (< 0.1)
            if count == 0 and max_t < 0.1:
                zero_topo_seen = True
                status = "  (baseline reached)"
            
            print(f"{t:>4} | {count:>8} | {max_t:>8.3f} | {mean_t:>9.4f} | {status}")
        
        prev_count = count
    
    print()
    
    # Verdict
    print("="*55)
    if zero_topo_seen:
        print("VERDICT: Topology indicator DID return to baseline")
        print("         This supports SPONTANEOUS re-nucleation")
    else:
        print("VERDICT: Topology indicator did NOT return to baseline")
        print("         This suggests REMNANT amplification")


def test_steady_state_population():
    """
    Test whether the system can maintain a steady-state vortex population.
    """
    print()
    print("="*70)
    print("STEADY-STATE POPULATION TEST")
    print("="*70)
    print()
    print("Question: Can Branch E maintain a stable vortex population?")
    print()
    
    size = 80
    steps = 6000
    
    for mode in ['none', 'self_selecting']:
        print(f"--- {mode.upper()} ---")
        
        sim = RegenerationAnalysisSimulator(size=size, gamma=0.007)
        sim.channel_assignment[:] = 0
        
        # Seed with multiple pairs to create population
        positions = [
            (20, 20), (60, 20), (20, 60), (60, 60), (40, 40)
        ]
        sim.psi_r[:] = 1.2
        for i, pos in enumerate(positions):
            charge = 1 if i % 2 == 0 else -1
            sim.add_vortex(pos, charge=charge, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        # Track population
        counts = []
        
        for step in range(steps):
            sim.step(mode=mode)
            
            if step % 50 == 0:
                vortices = sim.detect_all_vortices(amp_threshold=0.4)
                counts.append(len(vortices))
        
        # Analyze
        early_mean = np.mean(counts[:20])
        late_mean = np.mean(counts[-20:])
        overall_mean = np.mean(counts)
        
        print(f"  Initial population: {counts[0]}")
        print(f"  Early mean (t<1000): {early_mean:.1f}")
        print(f"  Late mean (t>5000): {late_mean:.1f}")
        print(f"  Overall mean: {overall_mean:.1f}")
        
        # Check for plateau
        late_std = np.std(counts[-20:])
        if late_mean > 0 and late_std < late_mean * 0.5:
            print(f"  ✓ STEADY STATE: Late population stable at ~{late_mean:.0f}")
        elif late_mean > 0:
            print(f"  ~ FLUCTUATING: Population varies (std={late_std:.1f})")
        else:
            print(f"  ✗ EXTINCT: Population died out")
        
        print()


def main():
    print("="*70)
    print("TOPOLOGICAL REGENERATION ANALYSIS")
    print("="*70)
    print()
    print("Goal: Understand HOW vortices regenerate in self-selecting mode")
    print()
    
    analyze_regeneration_dynamics()
    test_remnant_vs_spontaneous()
    test_steady_state_population()
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("Key findings to extract:")
    print("1. Nucleation rate in self-selecting vs baseline")
    print("2. Whether nucleation is spatially localized")
    print("3. Whether topology returns to baseline before rebirth")
    print("4. Whether a steady-state population can be maintained")


if __name__ == "__main__":
    main()
