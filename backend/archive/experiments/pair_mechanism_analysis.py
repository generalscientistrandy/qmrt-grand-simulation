"""
Branch E Pair Stabilization Mechanism Analysis
===============================================

The 32-48× pair lifetime improvement is the key Branch E result.
This script investigates WHY self-selection suppresses annihilation.

Three candidate mechanisms:
A. Mobility effect — vortices approach more slowly
B. Channel decoupling — different frequency niches reduce interaction
C. Core protection — resonance stabilizes local defect structure

Tracked quantities:
- Pair separation d(t)
- Individual channel assignments A₁, A₂
- Channel divergence |A₁ - A₂|
- Core amplitudes
- Winding strengths
- Annihilation time and mode

Goal: Identify which mechanism(s) explain the annihilation suppression.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional
import json


class MechanismAnalysisSimulator:
    """
    Simulator with detailed pair tracking for mechanism analysis.
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
    
    def set_partitioned_regions(self, centers: List[Tuple[int, int]], radii: List[float]):
        self.channel_assignment = np.zeros((self.size, self.size))
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        for center, radius in zip(centers, radii):
            r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            self.channel_assignment = np.maximum(self.channel_assignment, (r <= radius).astype(float))
    
    def step(self, mode: str = 'none'):
        if mode == 'self_selecting' or mode == 'combined':
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
        
        if mode in ['partitioned', 'self_selecting', 'combined']:
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
    
    def find_vortex_core(self, search_center: Tuple[int, int], 
                         search_radius: int = 15, charge_hint: int = None) -> Optional[Tuple[int, int]]:
        amp = self.amplitude
        best_pos = None
        min_amp = float('inf')
        
        for di in range(-search_radius, search_radius+1):
            for dj in range(-search_radius, search_radius+1):
                i = (search_center[0] + di) % self.size
                j = (search_center[1] + dj) % self.size
                if amp[i, j] < min_amp:
                    min_amp = amp[i, j]
                    best_pos = (i, j)
        
        if best_pos and min_amp < 0.5:
            winding = self.compute_winding_number(best_pos[0], best_pos[1], radius=2)
            if abs(winding) > 0.5:
                # Just check there's valid winding, ignore charge_hint sign
                # (winding sign convention differs from add_vortex)
                return best_pos
        return None


def run_pair_mechanism_analysis(mode: str, label: str):
    """
    Detailed tracking of vortex pair dynamics.
    """
    size = 80
    steps = 4000
    sample_interval = 20
    
    sim = MechanismAnalysisSimulator(size=size, gamma=0.007)
    
    v1_init = (size//2 - 12, size//2)
    v2_init = (size//2 + 12, size//2)
    
    if mode == 'partitioned':
        sim.set_partitioned_regions([v1_init, v2_init], [10, 10])
    elif mode == 'combined':
        sim.set_partitioned_regions([v1_init, v2_init], [10, 10])
    
    sim.psi_r[:] = 1.2
    sim.add_vortex(v1_init, charge=+1, amplitude=1.2, core_radius=4.0)
    sim.add_vortex(v2_init, charge=-1, amplitude=1.2, core_radius=4.0)
    sim.seed_oscillators(amp=0.1)
    
    # Tracking arrays
    times = []
    separations = []
    v1_channels = []
    v2_channels = []
    channel_divergences = []
    v1_core_amps = []
    v2_core_amps = []
    v1_windings = []
    v2_windings = []
    v1_positions = []
    v2_positions = []
    
    last_v1 = v1_init
    last_v2 = v2_init
    annihilation_time = None
    
    for step in range(steps):
        sim.step(mode=mode)
        
        if step % sample_interval == 0:
            # Find vortices
            current_v1 = sim.find_vortex_core(last_v1, search_radius=15, charge_hint=+1)
            current_v2 = sim.find_vortex_core(last_v2, search_radius=15, charge_hint=-1)
            
            times.append(step)
            
            if current_v1 and current_v2:
                # Both alive
                i1, j1 = current_v1
                i2, j2 = current_v2
                
                # Separation (with periodic boundary handling)
                di = i2 - i1
                dj = j2 - j1
                if abs(di) > size // 2:
                    di = di - np.sign(di) * size
                if abs(dj) > size // 2:
                    dj = dj - np.sign(dj) * size
                sep = np.sqrt(di**2 + dj**2)
                
                separations.append(sep)
                v1_positions.append(current_v1)
                v2_positions.append(current_v2)
                
                # Channel assignments
                ch1 = sim.channel_assignment[i1, j1]
                ch2 = sim.channel_assignment[i2, j2]
                v1_channels.append(ch1)
                v2_channels.append(ch2)
                channel_divergences.append(abs(ch1 - ch2))
                
                # Core amplitudes
                v1_core_amps.append(sim.amplitude[i1, j1])
                v2_core_amps.append(sim.amplitude[i2, j2])
                
                # Windings
                v1_windings.append(abs(sim.compute_winding_number(i1, j1, radius=2)))
                v2_windings.append(abs(sim.compute_winding_number(i2, j2, radius=2)))
                
                last_v1 = current_v1
                last_v2 = current_v2
                
            else:
                # At least one died
                if annihilation_time is None:
                    annihilation_time = step
                
                # Fill with NaN or last values
                separations.append(0)
                v1_channels.append(v1_channels[-1] if v1_channels else 0)
                v2_channels.append(v2_channels[-1] if v2_channels else 0)
                channel_divergences.append(channel_divergences[-1] if channel_divergences else 0)
                v1_core_amps.append(1.0)
                v2_core_amps.append(1.0)
                v1_windings.append(0)
                v2_windings.append(0)
                v1_positions.append(last_v1)
                v2_positions.append(last_v2)
    
    return {
        'mode': mode,
        'label': label,
        'annihilation_time': annihilation_time if annihilation_time else steps,
        'times': times,
        'separations': separations,
        'v1_channels': v1_channels,
        'v2_channels': v2_channels,
        'channel_divergences': channel_divergences,
        'v1_core_amps': v1_core_amps,
        'v2_core_amps': v2_core_amps,
        'v1_windings': v1_windings,
        'v2_windings': v2_windings,
    }


def analyze_separation_dynamics(results: Dict):
    """Analyze separation trajectory to detect mobility effects."""
    seps = results['separations']
    times = results['times']
    
    # Find when both vortices are still alive
    alive_mask = [s > 0 for s in seps]
    alive_times = [t for t, alive in zip(times, alive_mask) if alive]
    alive_seps = [s for s, alive in zip(seps, alive_mask) if alive]
    
    if len(alive_seps) < 5:
        return {'approach_rate': None, 'initial_sep': None, 'final_sep': None}
    
    initial_sep = alive_seps[0]
    final_sep = alive_seps[-1]
    
    # Linear fit to get approach rate
    if len(alive_times) > 2:
        coeffs = np.polyfit(alive_times, alive_seps, 1)
        approach_rate = coeffs[0]  # Negative = approaching
    else:
        approach_rate = (final_sep - initial_sep) / (alive_times[-1] - alive_times[0] + 1)
    
    return {
        'approach_rate': approach_rate,
        'initial_sep': initial_sep,
        'final_sep': final_sep,
        'duration': len(alive_times) * 20,  # sample interval
    }


def analyze_channel_divergence(results: Dict):
    """Analyze channel divergence correlation with survival."""
    divs = results['channel_divergences']
    v1_ch = results['v1_channels']
    v2_ch = results['v2_channels']
    
    alive_mask = [results['separations'][i] > 0 for i in range(len(divs))]
    alive_divs = [d for d, alive in zip(divs, alive_mask) if alive]
    
    if len(alive_divs) < 3:
        return {'avg_divergence': 0, 'peak_divergence': 0, 'divergence_trend': 0}
    
    avg_div = np.mean(alive_divs)
    peak_div = np.max(alive_divs)
    
    # Trend: is divergence increasing over time?
    early_div = np.mean(alive_divs[:len(alive_divs)//3])
    late_div = np.mean(alive_divs[-len(alive_divs)//3:])
    div_trend = late_div - early_div
    
    return {
        'avg_divergence': avg_div,
        'peak_divergence': peak_div,
        'divergence_trend': div_trend,
        'early_v1_channel': v1_ch[0] if v1_ch else 0,
        'late_v1_channel': v1_ch[len(alive_divs)-1] if v1_ch else 0,
        'early_v2_channel': v2_ch[0] if v2_ch else 0,
        'late_v2_channel': v2_ch[len(alive_divs)-1] if v2_ch else 0,
    }


def analyze_core_protection(results: Dict):
    """Analyze core amplitude evolution."""
    v1_amps = results['v1_core_amps']
    v2_amps = results['v2_core_amps']
    v1_winds = results['v1_windings']
    v2_winds = results['v2_windings']
    
    alive_mask = [results['separations'][i] > 0 for i in range(len(v1_amps))]
    
    alive_v1_amps = [a for a, alive in zip(v1_amps, alive_mask) if alive]
    alive_v2_amps = [a for a, alive in zip(v2_amps, alive_mask) if alive]
    alive_v1_winds = [w for w, alive in zip(v1_winds, alive_mask) if alive]
    alive_v2_winds = [w for w, alive in zip(v2_winds, alive_mask) if alive]
    
    if len(alive_v1_amps) < 3:
        return {'avg_core_amp': 1.0, 'core_amp_trend': 0, 'winding_stable': False, 
                'early_core_amp': 1.0, 'late_core_amp': 1.0}
    
    avg_core = (np.mean(alive_v1_amps) + np.mean(alive_v2_amps)) / 2
    
    early_amp = (np.mean(alive_v1_amps[:len(alive_v1_amps)//3]) + 
                 np.mean(alive_v2_amps[:len(alive_v2_amps)//3])) / 2
    late_amp = (np.mean(alive_v1_amps[-len(alive_v1_amps)//3:]) + 
                np.mean(alive_v2_amps[-len(alive_v2_amps)//3:])) / 2
    
    core_trend = late_amp - early_amp
    
    # Check if winding stays stable
    winding_stable = all(w > 0.5 for w in alive_v1_winds + alive_v2_winds)
    
    return {
        'avg_core_amp': avg_core,
        'core_amp_trend': core_trend,
        'winding_stable': winding_stable,
        'early_core_amp': early_amp,
        'late_core_amp': late_amp,
    }


def main():
    print("="*70)
    print("BRANCH E PAIR MECHANISM ANALYSIS")
    print("="*70)
    print()
    print("Question: WHY does self-selection suppress annihilation?")
    print()
    print("Candidates:")
    print("  A. Mobility effect — vortices approach more slowly")
    print("  B. Channel decoupling — different frequency niches")
    print("  C. Core protection — resonance stabilizes defect structure")
    print()
    
    modes = [
        ('none', 'Baseline'),
        ('partitioned', 'Partitioned'),
        ('self_selecting', 'Self-selecting'),
        ('combined', 'Combined'),
    ]
    
    all_results = {}
    all_sep_analysis = {}
    all_div_analysis = {}
    all_core_analysis = {}
    
    for mode, label in modes:
        print(f"Running {label}...")
        results = run_pair_mechanism_analysis(mode, label)
        all_results[mode] = results
        all_sep_analysis[mode] = analyze_separation_dynamics(results)
        all_div_analysis[mode] = analyze_channel_divergence(results)
        all_core_analysis[mode] = analyze_core_protection(results)
    
    print()
    print("="*70)
    print("ANALYSIS A: SEPARATION DYNAMICS (Mobility Effect)")
    print("="*70)
    print()
    print("| Mode | Lifetime | Initial Sep | Final Sep | Approach Rate |")
    print("|------|----------|-------------|-----------|---------------|")
    
    for mode, label in modes:
        r = all_results[mode]
        s = all_sep_analysis[mode]
        rate = s['approach_rate'] if s['approach_rate'] else 0
        init_s = s['initial_sep'] if s['initial_sep'] else 0
        fin_s = s['final_sep'] if s['final_sep'] else 0
        print(f"| {label:12} | {r['annihilation_time']:>6} | {init_s:>11.1f} | {fin_s:>9.1f} | {rate:>+13.4f} |")
    
    print()
    
    # Interpret mobility
    baseline_rate = all_sep_analysis['none']['approach_rate'] or -0.1
    self_rate = all_sep_analysis['self_selecting']['approach_rate'] or -0.1
    
    if self_rate and baseline_rate and abs(self_rate) < abs(baseline_rate) * 0.7:
        print("✓ MOBILITY EFFECT DETECTED: Self-selecting slows approach significantly")
        mobility_effect = True
    else:
        print("- No clear mobility effect (approach rates similar)")
        mobility_effect = False
    
    print()
    print("="*70)
    print("ANALYSIS B: CHANNEL DIVERGENCE (Decoupling Effect)")
    print("="*70)
    print()
    print("| Mode | Avg Divergence | Peak Div | Trend | V1 ch | V2 ch |")
    print("|------|----------------|----------|-------|-------|-------|")
    
    for mode, label in modes:
        d = all_div_analysis[mode]
        print(f"| {label:12} | {d['avg_divergence']:>14.3f} | {d['peak_divergence']:>8.3f} | "
              f"{d['divergence_trend']:>+5.3f} | {d.get('late_v1_channel', 0):>5.2f} | {d.get('late_v2_channel', 0):>5.2f} |")
    
    print()
    
    # Interpret channel divergence
    self_div = all_div_analysis['self_selecting']['avg_divergence']
    combined_div = all_div_analysis['combined']['avg_divergence']
    
    if self_div > 0.05 or combined_div > 0.05:
        print("✓ CHANNEL DIVERGENCE DETECTED: Vortices develop different channel signatures")
        channel_effect = True
    else:
        print("- No significant channel divergence")
        channel_effect = False
    
    # Check if divergence correlates with lifetime
    lifetimes = [all_results[m]['annihilation_time'] for m, _ in modes]
    divergences = [all_div_analysis[m]['avg_divergence'] for m, _ in modes]
    
    if len(set(divergences)) > 1:  # Not all same
        corr = np.corrcoef(lifetimes, divergences)[0, 1]
        print(f"  Correlation(divergence, lifetime): {corr:.3f}")
        if corr > 0.5:
            print("  ✓ Higher divergence correlates with longer lifetime")
    
    print()
    print("="*70)
    print("ANALYSIS C: CORE PROTECTION")
    print("="*70)
    print()
    print("| Mode | Avg Core Amp | Early | Late | Trend | Winding Stable |")
    print("|------|--------------|-------|------|-------|----------------|")
    
    for mode, label in modes:
        c = all_core_analysis[mode]
        stable = "Yes" if c['winding_stable'] else "No"
        print(f"| {label:12} | {c['avg_core_amp']:>12.3f} | {c['early_core_amp']:>5.3f} | "
              f"{c['late_core_amp']:>4.3f} | {c['core_amp_trend']:>+5.3f} | {stable:>14} |")
    
    print()
    
    # Interpret core protection
    baseline_core = all_core_analysis['none']['avg_core_amp']
    self_core = all_core_analysis['self_selecting']['avg_core_amp']
    
    if self_core < baseline_core * 0.8:
        print("✓ CORE PROTECTION DETECTED: Resonance keeps cores more defined")
        core_effect = True
    else:
        print("- No clear core protection effect")
        core_effect = False
    
    print()
    print("="*70)
    print("MECHANISM SUMMARY")
    print("="*70)
    print()
    
    effects = []
    if mobility_effect:
        effects.append("MOBILITY (slowed approach)")
    if channel_effect:
        effects.append("CHANNEL DIVERGENCE (frequency separation)")
    if core_effect:
        effects.append("CORE PROTECTION (maintained structure)")
    
    if effects:
        print(f"Detected mechanisms: {', '.join(effects)}")
    else:
        print("No clear single mechanism detected — may be combination or different effect")
    
    print()
    print("="*70)
    print("INTERPRETATION")
    print("="*70)
    print()
    
    # Detailed interpretation
    if mobility_effect and channel_effect:
        print("CONCLUSION: COMBINED MOBILITY + CHANNEL EFFECT")
        print()
        print("Self-selection appears to work through multiple mechanisms:")
        print("1. Vortices approach each other more slowly")
        print("2. They develop different frequency signatures as they evolve")
        print("3. This frequency separation may reduce their effective interaction")
        print()
        print("Physical interpretation:")
        print("→ Each vortex finds its own resonance niche")
        print("→ Different niches = reduced phase overlap")
        print("→ Reduced overlap = slower approach + weaker annihilation")
        
    elif channel_effect:
        print("CONCLUSION: CHANNEL DECOUPLING EFFECT")
        print()
        print("Self-selection works primarily through frequency separation:")
        print("- Vortices develop different channel assignments")
        print("- This creates effective 'phase space separation'")
        print("- Separated vortices interact more weakly")
        print()
        print("Physical interpretation:")
        print("→ Resonance channels act like 'species'")
        print("→ Vortices in different channels don't 'see' each other as strongly")
        print("→ Annihilation requires frequency matching, which self-selection breaks")
        
    elif mobility_effect:
        print("CONCLUSION: MOBILITY EFFECT")
        print()
        print("Self-selection works primarily through reduced mobility:")
        print("- Vortices move more slowly toward each other")
        print("- This delays but may not prevent annihilation")
        print()
        print("Physical interpretation:")
        print("→ Resonance creates effective viscosity")
        print("→ Defects get 'stuck' in their frequency channel")
        
    else:
        print("CONCLUSION: MECHANISM UNCLEAR")
        print()
        print("The stabilization may work through:")
        print("- Subtle phase interactions not captured by these metrics")
        print("- Threshold effects that activate under specific conditions")
        print("- Combination of weak effects")
        print()
        print("Recommend: More detailed tracking of phase relationship between vortices")
    
    return {
        'all_results': all_results,
        'separation_analysis': all_sep_analysis,
        'divergence_analysis': all_div_analysis,
        'core_analysis': all_core_analysis,
        'mobility_effect': mobility_effect,
        'channel_effect': channel_effect,
        'core_effect': core_effect,
    }


if __name__ == "__main__":
    results = main()
