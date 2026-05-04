"""
Resonance Contrast Tests: Partitioned vs Self-Selecting
========================================================

Mode A: FREQUENCY-PARTITIONED MODEL (Controlled)
    Question: If the medium has distinct resonance regions, 
              does frequency contrast protect vortices?

Mode B: SELF-SELECTING RESONANCE (Intrinsic)
    Question: Can structures generate their own protected 
              frequency channel without external imposition?

Shared Metrics:
    - Vortex lifetime
    - Core amplitude minimum over time
    - Winding persistence
    - Frequency separation (local vs background)
    - Drift / confinement

Goal: Determine if resonance contrast is a viable stabilizing channel,
      and whether it can be intrinsic or must be imposed.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional
import json


class DualChannelSimulator:
    """
    Complex scalar field with two frequency channels.
    
    Channel 1: Background oscillator (ω₁)
    Channel 2: Structure oscillator (ω₂)
    
    The coupling determines whether structures prefer one channel over another.
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.008,
        lambda_relax: float = 0.5,
        beta: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
        # Dual channel parameters
        omega_1: float = 0.3,          # Background channel frequency
        omega_2: float = 0.7,          # Structure channel frequency
        channel_coupling: float = 0.3,  # How strongly ψ couples to channels
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.beta = beta
        self.D_medium = D_medium
        self.dt = dt
        
        # Channel parameters
        self.omega_1 = omega_1
        self.omega_2 = omega_2
        self.channel_coupling = channel_coupling
        
        # Primary complex field ψ
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Medium
        self.tau = np.ones((size, size)) * tau_0
        
        # Channel 1: Background oscillator
        self.chi_1 = np.zeros((size, size))
        self.chi_1_dot = np.zeros((size, size))
        
        # Channel 2: Structure oscillator
        self.chi_2 = np.zeros((size, size))
        self.chi_2_dot = np.zeros((size, size))
        
        # Channel assignment field: 0 = channel 1, 1 = channel 2
        # In partitioned mode: externally set
        # In self-selecting mode: evolves dynamically
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
    
    def compute_local_phase_rate(self) -> np.ndarray:
        """Instantaneous phase rotation rate."""
        amp_sq = self.psi_r**2 + self.psi_i**2 + 1e-10
        phase_rate = (self.psi_r * self.psi_i_dot - self.psi_i * self.psi_r_dot) / amp_sq
        return phase_rate
    
    def compute_topology_indicator(self) -> np.ndarray:
        """
        Indicator of topological structure (high near vortex cores).
        Uses phase gradient magnitude.
        """
        phase = self.phase
        # Phase gradient with proper wrapping
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, 0) - np.roll(phase, 1, 0))))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, 1) - np.roll(phase, 1, 1))))
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        return gaussian_filter(grad_mag, sigma=2.0)
    
    def compute_effective_frequency(self) -> np.ndarray:
        """
        Compute effective local frequency based on channel assignment.
        """
        return self.omega_1 * (1 - self.channel_assignment) + self.omega_2 * self.channel_assignment
    
    def set_partitioned_regions(self, centers: List[Tuple[int, int]], radii: List[float]):
        """
        Mode A: Externally partition the domain into channel 2 regions.
        """
        self.channel_assignment = np.zeros((self.size, self.size))
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        
        for center, radius in zip(centers, radii):
            r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            self.channel_assignment = np.maximum(self.channel_assignment, (r <= radius).astype(float))
    
    def update_self_selecting_channels(self):
        """
        Mode B: Channel assignment evolves based on local field properties.
        
        Rule: Regions with high topology indicator drift toward channel 2.
              Regions with low topology drift toward channel 1.
        """
        topology = self.compute_topology_indicator()
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Relaxation toward topology-determined assignment
        target = topology_norm  # High topology → channel 2
        relaxation_rate = 0.01
        
        self.channel_assignment += relaxation_rate * (target - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
    
    def compute_channel_protection(self) -> np.ndarray:
        """
        Protection factor based on being in "correct" channel.
        
        Vortex cores (high topology) should be in channel 2.
        When they are, they get protection against core filling.
        """
        topology = self.compute_topology_indicator()
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Protection when topology matches channel 2 assignment
        # High protection where: high topology AND channel 2
        match_quality = topology_norm * self.channel_assignment
        
        return match_quality
    
    def step(self, mode: str = 'partitioned'):
        """
        Step the simulation.
        mode: 'partitioned' (fixed channels), 'self_selecting' (dynamic channels), 'none' (no channel effects)
        """
        
        # 1. Update channel assignment (only in self-selecting mode)
        if mode == 'self_selecting':
            self.update_self_selecting_channels()
        
        # 2. Update oscillator channels
        eff_omega = self.compute_effective_frequency()
        
        self.chi_1_dot += -self.omega_1**2 * self.chi_1 * self.dt
        self.chi_1 += self.chi_1_dot * self.dt
        
        self.chi_2_dot += -self.omega_2**2 * self.chi_2 * self.dt
        self.chi_2 += self.chi_2_dot * self.dt
        
        # 3. Medium evolution
        rho = self.rho
        tau_eq = self.tau_0 / (1 + self.beta * gaussian_filter(rho, sigma=2.0) / (np.max(rho) + 1e-10))
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # 4. Wave evolution
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                 np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
        lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                 np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # 5. Channel-based protection (if not 'none' mode)
        if mode in ['partitioned', 'self_selecting']:
            protection = self.compute_channel_protection()
            
            # Reduce core-filling acceleration where protected
            amp = self.amplitude + 1e-10
            
            # Radial component of acceleration (amplitude-changing)
            radial_r = self.psi_r / amp
            radial_i = self.psi_i / amp
            acc_radial = acc_r * radial_r + acc_i * radial_i
            
            # Suppress positive radial acceleration (core filling) where protected
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
        """Initialize both oscillator channels."""
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
                         search_radius: int = 15) -> Optional[Tuple[int, int]]:
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
                return best_pos
        return None
    
    def measure_vortex_metrics(self, vortex_pos: Tuple[int, int]) -> Dict:
        """Comprehensive metrics for a vortex."""
        i, j = vortex_pos
        
        return {
            'core_amplitude': float(self.amplitude[i, j]),
            'winding': float(abs(self.compute_winding_number(i, j, radius=2))),
            'channel_assignment': float(self.channel_assignment[i, j]),
            'local_freq': float(self.compute_effective_frequency()[i, j]),
            'background_freq': float(np.mean(self.compute_effective_frequency())),
            'freq_contrast': float(abs(self.compute_effective_frequency()[i, j] - np.mean(self.compute_effective_frequency()))),
            'protection': float(self.compute_channel_protection()[i, j]),
            'position': vortex_pos
        }


def run_comprehensive_test(mode: str, label: str, n_trials: int = 5):
    """
    Run a comprehensive test with all metrics tracked.
    """
    size = 80
    steps = 4000
    center = (size//2, size//2)
    
    all_lifetimes = []
    all_core_amps = []
    all_windings = []
    all_freq_contrasts = []
    all_channel_assignments = []
    
    for trial in range(n_trials):
        sim = DualChannelSimulator(
            size=size,
            gamma=0.007,
            omega_1=0.3,
            omega_2=0.8,
            channel_coupling=0.5
        )
        
        # Setup based on mode
        if mode == 'partitioned':
            # Create channel 2 region at center
            sim.set_partitioned_regions([center], [20])
        elif mode == 'self_selecting':
            # Start with uniform channel 1, let it evolve
            sim.channel_assignment[:] = 0
        else:  # 'none'
            sim.channel_assignment[:] = 0
        
        # Initialize
        sim.psi_r[:] = 1.2
        sim.add_vortex(center, charge=1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        # Track
        lifetime = 0
        core_amps = []
        windings = []
        freq_contrasts = []
        channel_assigns = []
        last_pos = center
        
        for step in range(steps):
            sim.step(mode=mode)
            
            if step % 50 == 0:
                current_pos = sim.find_vortex_core(last_pos, search_radius=15)
                
                if current_pos:
                    metrics = sim.measure_vortex_metrics(current_pos)
                    lifetime = step
                    core_amps.append(metrics['core_amplitude'])
                    windings.append(metrics['winding'])
                    freq_contrasts.append(metrics['freq_contrast'])
                    channel_assigns.append(metrics['channel_assignment'])
                    last_pos = current_pos
                else:
                    # Vortex died
                    core_amps.append(1.0)
                    windings.append(0.0)
                    freq_contrasts.append(0.0)
                    channel_assigns.append(sim.channel_assignment[last_pos[0], last_pos[1]])
        
        all_lifetimes.append(lifetime)
        all_core_amps.append(core_amps)
        all_windings.append(windings)
        all_freq_contrasts.append(freq_contrasts)
        all_channel_assignments.append(channel_assigns)
    
    # Aggregate results
    avg_lifetime = np.mean(all_lifetimes)
    std_lifetime = np.std(all_lifetimes)
    
    # Average core amplitude trajectory
    min_len = min(len(ca) for ca in all_core_amps)
    avg_core_amps = np.mean([ca[:min_len] for ca in all_core_amps], axis=0)
    
    # Average channel assignment trajectory
    avg_channel = np.mean([ca[:min_len] for ca in all_channel_assignments], axis=0)
    
    # Average frequency contrast
    avg_freq_contrast = np.mean([fc[:min_len] for fc in all_freq_contrasts], axis=0)
    
    return {
        'label': label,
        'mode': mode,
        'avg_lifetime': avg_lifetime,
        'std_lifetime': std_lifetime,
        'lifetimes': all_lifetimes,
        'avg_core_amps': avg_core_amps.tolist() if len(avg_core_amps) > 0 else [],
        'avg_channel_assignment': avg_channel.tolist() if len(avg_channel) > 0 else [],
        'avg_freq_contrast': avg_freq_contrast.tolist() if len(avg_freq_contrast) > 0 else [],
    }


def run_pair_test(mode: str, label: str, n_trials: int = 5):
    """
    Test with vortex-antivortex pair to check annihilation behavior.
    """
    size = 80
    steps = 3000
    
    all_lifetimes = []
    all_separations = []
    
    for trial in range(n_trials):
        sim = DualChannelSimulator(
            size=size,
            gamma=0.007,
            omega_1=0.3,
            omega_2=0.8,
            channel_coupling=0.5
        )
        
        v1_pos = (size//2 - 12, size//2)
        v2_pos = (size//2 + 12, size//2)
        
        if mode == 'partitioned':
            # Create separate channel 2 regions for each vortex
            sim.set_partitioned_regions([v1_pos, v2_pos], [8, 8])
        elif mode == 'self_selecting':
            sim.channel_assignment[:] = 0
        else:
            sim.channel_assignment[:] = 0
        
        sim.psi_r[:] = 1.2
        sim.add_vortex(v1_pos, charge=+1, amplitude=1.2, core_radius=4.0)
        sim.add_vortex(v2_pos, charge=-1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        lifetime = 0
        separations = []
        last_v1 = v1_pos
        last_v2 = v2_pos
        
        for step in range(steps):
            sim.step(mode=mode)
            
            if step % 40 == 0:
                current_v1 = sim.find_vortex_core(last_v1, search_radius=15)
                current_v2 = sim.find_vortex_core(last_v2, search_radius=15)
                
                if current_v1 and current_v2:
                    lifetime = step
                    sep = np.sqrt((current_v1[0] - current_v2[0])**2 + 
                                  (current_v1[1] - current_v2[1])**2)
                    separations.append(sep)
                    last_v1 = current_v1
                    last_v2 = current_v2
                elif current_v1 or current_v2:
                    # One died
                    lifetime = step
                    separations.append(0)
                else:
                    # Both died (annihilated)
                    separations.append(0)
        
        all_lifetimes.append(lifetime)
        all_separations.append(separations)
    
    avg_lifetime = np.mean(all_lifetimes)
    
    return {
        'label': label,
        'mode': mode,
        'avg_pair_lifetime': avg_lifetime,
        'lifetimes': all_lifetimes,
    }


# ============================================================
# MODE A: FREQUENCY-PARTITIONED MODEL
# ============================================================

def test_mode_a():
    """
    Mode A: External frequency partitioning.
    Question: Does externally imposed frequency contrast protect vortices?
    """
    print("="*70)
    print("MODE A: FREQUENCY-PARTITIONED MODEL")
    print("="*70)
    print()
    print("Question: Does externally imposed frequency contrast protect vortices?")
    print()
    
    # Test 1: Single vortex comparison
    print("--- Test A.1: Single Vortex ---")
    
    results_none = run_comprehensive_test('none', 'No channels', n_trials=5)
    results_part = run_comprehensive_test('partitioned', 'Partitioned', n_trials=5)
    
    print(f"  No channels:  {results_none['avg_lifetime']:.0f} ± {results_none['std_lifetime']:.0f}")
    print(f"  Partitioned:  {results_part['avg_lifetime']:.0f} ± {results_part['std_lifetime']:.0f}")
    
    improvement_a1 = results_part['avg_lifetime'] / (results_none['avg_lifetime'] + 1)
    print(f"  Improvement: {improvement_a1:.2f}×")
    print()
    
    # Test 2: Pair annihilation
    print("--- Test A.2: Vortex-Antivortex Pair ---")
    
    pair_none = run_pair_test('none', 'No channels', n_trials=5)
    pair_part = run_pair_test('partitioned', 'Partitioned', n_trials=5)
    
    print(f"  No channels:  {pair_none['avg_pair_lifetime']:.0f}")
    print(f"  Partitioned:  {pair_part['avg_pair_lifetime']:.0f}")
    
    improvement_a2 = pair_part['avg_pair_lifetime'] / (pair_none['avg_pair_lifetime'] + 1)
    print(f"  Improvement: {improvement_a2:.2f}×")
    print()
    
    # Test 3: Contrast strength sweep
    print("--- Test A.3: Frequency Contrast Sweep ---")
    
    contrasts = []
    lifetimes = []
    
    for omega_2 in [0.35, 0.5, 0.7, 0.9, 1.2]:
        sim = DualChannelSimulator(size=80, gamma=0.007, omega_1=0.3, omega_2=omega_2, channel_coupling=0.5)
        sim.set_partitioned_regions([(40, 40)], [20])
        sim.psi_r[:] = 1.2
        sim.add_vortex((40, 40), charge=1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        lifetime = 0
        last_pos = (40, 40)
        for step in range(3000):
            sim.step(mode='partitioned')
            if step % 50 == 0:
                pos = sim.find_vortex_core(last_pos, search_radius=15)
                if pos:
                    lifetime = step
                    last_pos = pos
        
        contrast = abs(omega_2 - 0.3)
        contrasts.append(contrast)
        lifetimes.append(lifetime)
        print(f"  Δω = {contrast:.2f}: lifetime = {lifetime}")
    
    # Check if lifetime correlates with contrast
    correlation = np.corrcoef(contrasts, lifetimes)[0, 1]
    print(f"  Correlation(Δω, lifetime): {correlation:.3f}")
    print()
    
    return {
        'single_improvement': improvement_a1,
        'pair_improvement': improvement_a2,
        'contrast_correlation': correlation,
        'results_none': results_none,
        'results_partitioned': results_part
    }


# ============================================================
# MODE B: SELF-SELECTING RESONANCE
# ============================================================

def test_mode_b():
    """
    Mode B: Self-selecting frequency channels.
    Question: Can structures spontaneously generate protected frequency niches?
    """
    print("="*70)
    print("MODE B: SELF-SELECTING RESONANCE")
    print("="*70)
    print()
    print("Question: Can structures generate their own protected frequency channel?")
    print()
    
    # Test 1: Single vortex - does it develop distinct channel?
    print("--- Test B.1: Single Vortex Self-Selection ---")
    
    results_none = run_comprehensive_test('none', 'No channels', n_trials=5)
    results_self = run_comprehensive_test('self_selecting', 'Self-selecting', n_trials=5)
    
    print(f"  No channels:     {results_none['avg_lifetime']:.0f} ± {results_none['std_lifetime']:.0f}")
    print(f"  Self-selecting:  {results_self['avg_lifetime']:.0f} ± {results_self['std_lifetime']:.0f}")
    
    improvement_b1 = results_self['avg_lifetime'] / (results_none['avg_lifetime'] + 1)
    print(f"  Improvement: {improvement_b1:.2f}×")
    
    # Check if channel assignment developed
    if results_self['avg_channel_assignment']:
        early_channel = np.mean(results_self['avg_channel_assignment'][:5])
        late_channel = np.mean(results_self['avg_channel_assignment'][-5:]) if len(results_self['avg_channel_assignment']) > 5 else early_channel
        print(f"  Channel assignment: {early_channel:.3f} → {late_channel:.3f}")
        channel_developed = late_channel > early_channel + 0.1
    else:
        channel_developed = False
    print()
    
    # Test 2: Does channel assignment correlate with survival?
    print("--- Test B.2: Channel-Survival Correlation ---")
    
    # Run with tracking
    channel_at_death = []
    lifetimes_b2 = []
    
    for trial in range(10):
        sim = DualChannelSimulator(size=80, gamma=0.007, omega_1=0.3, omega_2=0.8, channel_coupling=0.5)
        sim.channel_assignment[:] = 0
        sim.psi_r[:] = 1.2
        sim.add_vortex((40, 40), charge=1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        lifetime = 0
        last_pos = (40, 40)
        last_channel = 0
        
        for step in range(3000):
            sim.step(mode='self_selecting')
            if step % 50 == 0:
                pos = sim.find_vortex_core(last_pos, search_radius=15)
                if pos:
                    lifetime = step
                    last_channel = sim.channel_assignment[pos[0], pos[1]]
                    last_pos = pos
        
        channel_at_death.append(last_channel)
        lifetimes_b2.append(lifetime)
    
    correlation_b2 = np.corrcoef(channel_at_death, lifetimes_b2)[0, 1]
    print(f"  Correlation(channel_at_death, lifetime): {correlation_b2:.3f}")
    print(f"  Avg channel at death: {np.mean(channel_at_death):.3f}")
    print()
    
    # Test 3: Pair behavior with self-selection
    print("--- Test B.3: Pair Self-Selection ---")
    
    pair_none = run_pair_test('none', 'No channels', n_trials=5)
    pair_self = run_pair_test('self_selecting', 'Self-selecting', n_trials=5)
    
    print(f"  No channels:     {pair_none['avg_pair_lifetime']:.0f}")
    print(f"  Self-selecting:  {pair_self['avg_pair_lifetime']:.0f}")
    
    improvement_b3 = pair_self['avg_pair_lifetime'] / (pair_none['avg_pair_lifetime'] + 1)
    print(f"  Improvement: {improvement_b3:.2f}×")
    print()
    
    return {
        'single_improvement': improvement_b1,
        'channel_developed': channel_developed,
        'channel_survival_correlation': correlation_b2,
        'pair_improvement': improvement_b3,
        'results_self': results_self
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*70)
    print("RESONANCE CONTRAST TESTS")
    print("="*70)
    print()
    print("Mode A: Externally partitioned frequency channels")
    print("Mode B: Self-selecting frequency channels")
    print()
    print("Shared question: Does frequency contrast stabilize topology?")
    print()
    
    mode_a_results = test_mode_a()
    mode_b_results = test_mode_b()
    
    print()
    print("="*70)
    print("FINAL COMPARISON")
    print("="*70)
    print()
    
    print("| Mode | Single Vortex | Pair | Key Finding |")
    print("|------|---------------|------|-------------|")
    print(f"| A (Partitioned) | {mode_a_results['single_improvement']:.2f}× | {mode_a_results['pair_improvement']:.2f}× | Contrast corr = {mode_a_results['contrast_correlation']:.2f} |")
    print(f"| B (Self-select) | {mode_b_results['single_improvement']:.2f}× | {mode_b_results['pair_improvement']:.2f}× | Channel corr = {mode_b_results['channel_survival_correlation']:.2f} |")
    print()
    
    # Verdict
    a_works = mode_a_results['single_improvement'] > 1.2 or mode_a_results['pair_improvement'] > 1.2
    b_works = mode_b_results['single_improvement'] > 1.2 or mode_b_results['channel_developed']
    
    print("="*70)
    print("CONCLUSIONS")
    print("="*70)
    print()
    
    if a_works and b_works:
        print("BOTH MODES SHOW POSITIVE RESULTS")
        print("→ Resonance contrast IS a viable stabilizing channel")
        print("→ Structures CAN spontaneously generate protected niches")
        print("→ This supports the 'layered resonance' hypothesis")
    elif a_works and not b_works:
        print("MODE A WORKS, MODE B FAILS")
        print("→ Frequency partitioning CAN stabilize, but it must be imposed")
        print("→ Structures cannot spontaneously generate their own protection")
        print("→ Resonance contrast is real but not intrinsic")
    elif not a_works and b_works:
        print("MODE A FAILS, MODE B WORKS (unexpected)")
        print("→ Self-organization provides benefit even without strong external contrast")
        print("→ Dynamic adaptation matters more than static partitioning")
    else:
        print("BOTH MODES FAIL")
        print("→ Resonance contrast alone is not sufficient")
        print("→ The core-filling death mode requires different intervention")
        print("→ Consider targeting the failure channel more directly")
