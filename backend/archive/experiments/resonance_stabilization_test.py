"""
Resonance Stabilization Test
============================

Hypothesis: Vortex stability may require resonance compatibility 
            across multiple frequency layers, not just topology.

The current model has:
    - Topology (phase winding) ✓
    - Organization (spatial structure) ✓
    - But only ONE effective frequency scale

This test introduces:
    - A secondary oscillator field χ(x,t) with its own frequency
    - Local resonance matching between vortex core and background
    - Stability enhancement when frequencies align

Question: Does vortex lifetime increase when core frequency 
          matches a local resonance channel?

Model:
    Primary field: ψ (complex, supports vortices)
    Secondary field: χ (oscillator field with local frequency ω(x))
    
    Coupling: When vortex core oscillation matches local χ frequency,
              core-filling is suppressed.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional
import json


class ResonanceStabilizationSimulator:
    """
    Complex scalar field with secondary oscillator for resonance stabilization.
    
    The idea: vortex cores have intrinsic oscillation (phase rotation rate).
    If this matches a local "resonance channel" provided by χ, the core
    becomes energetically favored to stay open.
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
        # Resonance parameters
        omega_base: float = 0.5,          # Base oscillator frequency
        resonance_width: float = 0.2,     # Width of resonance window
        resonance_strength: float = 0.5,  # Coupling strength
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.beta = beta
        self.D_medium = D_medium
        self.dt = dt
        
        # Resonance parameters
        self.omega_base = omega_base
        self.resonance_width = resonance_width
        self.resonance_strength = resonance_strength
        
        # Primary complex field ψ
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Medium
        self.tau = np.ones((size, size)) * tau_0
        
        # Secondary oscillator field χ (provides resonance channel)
        self.chi = np.zeros((size, size))
        self.chi_dot = np.zeros((size, size))
        
        # Local frequency field ω(x) - can vary spatially
        self.omega_field = np.ones((size, size)) * omega_base
        
        # Track vortex core frequencies
        self.core_frequency_history = []
    
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
        """
        Compute local phase rotation rate (instantaneous frequency).
        This is d(phase)/dt at each point.
        """
        # Phase rate = (psi_r * psi_i_dot - psi_i * psi_r_dot) / |psi|^2
        amp_sq = self.psi_r**2 + self.psi_i**2 + 1e-10
        phase_rate = (self.psi_r * self.psi_i_dot - self.psi_i * self.psi_r_dot) / amp_sq
        return phase_rate
    
    def compute_resonance_factor(self) -> np.ndarray:
        """
        Compute how well local ψ frequency matches χ frequency.
        Returns 1 where resonant, 0 where mismatched.
        
        R(x) = exp(-(ω_ψ - ω_χ)² / (2σ²))
        """
        psi_freq = np.abs(self.compute_local_phase_rate())
        chi_freq = self.omega_field
        
        mismatch = (psi_freq - chi_freq)**2
        resonance = np.exp(-mismatch / (2 * self.resonance_width**2))
        
        return resonance
    
    def compute_core_protection(self) -> np.ndarray:
        """
        Core protection: suppress amplitude growth where topology + resonance align.
        
        High protection where:
        - Phase gradient is high (near vortex core)
        - Resonance factor is high (frequency match)
        """
        # Phase gradient magnitude (high at vortex cores)
        phase = self.phase
        grad_phase_x = np.angle(np.exp(1j * (np.roll(phase, -1, 0) - np.roll(phase, 1, 0))))
        grad_phase_y = np.angle(np.exp(1j * (np.roll(phase, -1, 1) - np.roll(phase, 1, 1))))
        phase_grad_mag = np.sqrt(grad_phase_x**2 + grad_phase_y**2)
        
        # Normalize
        phase_grad_norm = phase_grad_mag / (np.max(phase_grad_mag) + 1e-10)
        
        # Resonance factor
        resonance = self.compute_resonance_factor()
        
        # Core protection = phase_gradient * resonance
        # High where there's topology AND resonance match
        protection = phase_grad_norm * resonance
        
        return protection
    
    def step(self, use_resonance: bool = True):
        """Step with optional resonance-based core protection."""
        
        # 1. Update secondary oscillator χ
        # Simple harmonic oscillator: χ̈ = -ω² χ
        self.chi_dot += -self.omega_field**2 * self.chi * self.dt
        self.chi += self.chi_dot * self.dt
        
        # 2. Medium evolution
        rho = self.rho
        tau_eq = self.tau_0 / (1 + self.beta * gaussian_filter(rho, sigma=2.0) / (np.max(rho) + 1e-10))
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # 3. Wave evolution with optional resonance protection
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                 np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
        lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                 np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        if use_resonance:
            # Core protection: reduce amplitude growth where protected
            protection = self.compute_core_protection()
            
            # Where protection is high, suppress amplitude-increasing acceleration
            amp = self.amplitude + 1e-10
            radial_acc_r = (self.psi_r / amp) * (acc_r * self.psi_r + acc_i * self.psi_i) / amp
            radial_acc_i = (self.psi_i / amp) * (acc_r * self.psi_r + acc_i * self.psi_i) / amp
            
            # Reduce radial (amplitude-changing) component where protected
            suppression = 1 - self.resonance_strength * protection
            acc_r = acc_r - radial_acc_r * (1 - suppression)
            acc_i = acc_i - radial_acc_i * (1 - suppression)
        
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
    
    def set_resonance_well(self, center: Tuple[int, int], radius: float, 
                           omega_inside: float):
        """Create a region with different resonance frequency."""
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        inside = r <= radius
        self.omega_field[inside] = omega_inside
    
    def seed_oscillator(self, amplitude: float = 0.1):
        """Seed the secondary oscillator with initial excitation."""
        self.chi = amplitude * np.sin(self.omega_field * 0)  # Initial phase
        self.chi_dot = amplitude * self.omega_field * np.cos(self.omega_field * 0)
    
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


# ============================================================
# TEST 1: Does resonance protection extend single vortex lifetime?
# ============================================================

def test_resonance_lifetime():
    """
    Compare vortex lifetime with and without resonance protection.
    """
    print("="*70)
    print("TEST 1: RESONANCE PROTECTION LIFETIME")
    print("="*70)
    print()
    print("Question: Does resonance matching extend vortex lifetime?")
    print()
    
    size = 80
    steps = 4000
    n_trials = 5
    
    results = {}
    
    for use_resonance in [False, True]:
        label = "with_resonance" if use_resonance else "no_resonance"
        print(f"--- {label} ---")
        
        lifetimes = []
        
        for trial in range(n_trials):
            sim = ResonanceStabilizationSimulator(
                size=size,
                gamma=0.008,
                omega_base=0.5,
                resonance_width=0.3,
                resonance_strength=0.6
            )
            
            sim.psi_r[:] = 1.2
            center = (size//2, size//2)
            sim.add_vortex(center, charge=1, amplitude=1.2, core_radius=4.0)
            
            # Seed oscillator
            sim.seed_oscillator(amplitude=0.1)
            
            lifetime = 0
            last_pos = center
            
            for step in range(steps):
                sim.step(use_resonance=use_resonance)
                
                if step % 50 == 0:
                    current_pos = sim.find_vortex_core(last_pos, search_radius=15)
                    if current_pos:
                        lifetime = step
                        last_pos = current_pos
            
            lifetimes.append(lifetime)
        
        avg_lifetime = np.mean(lifetimes)
        std_lifetime = np.std(lifetimes)
        
        results[label] = {
            'avg_lifetime': avg_lifetime,
            'std_lifetime': std_lifetime,
            'lifetimes': lifetimes
        }
        
        print(f"  Avg lifetime: {avg_lifetime:.0f} ± {std_lifetime:.0f}")
    
    print()
    improvement = results['with_resonance']['avg_lifetime'] / (results['no_resonance']['avg_lifetime'] + 1)
    
    if improvement > 1.3:
        print(f"✓ RESONANCE EXTENDS LIFETIME: {improvement:.2f}× improvement")
    else:
        print(f"- No significant improvement from resonance ({improvement:.2f}×)")
    
    return results


# ============================================================
# TEST 2: Does resonance well create localized stability?
# ============================================================

def test_resonance_well():
    """
    Create a region with matching resonance frequency.
    Does a vortex inside the well survive longer?
    """
    print()
    print("="*70)
    print("TEST 2: RESONANCE WELL LOCALIZATION")
    print("="*70)
    print()
    print("Question: Does vortex survive longer inside resonance-matched region?")
    print()
    
    size = 80
    steps = 4000
    n_trials = 5
    center = (size//2, size//2)
    
    configs = [
        ("outside_well", (20, 40)),           # Start outside resonance well
        ("inside_well", (size//2, size//2)),  # Start inside resonance well
    ]
    
    results = {}
    
    for config_name, start_pos in configs:
        print(f"--- {config_name} ---")
        
        lifetimes = []
        
        for trial in range(n_trials):
            sim = ResonanceStabilizationSimulator(
                size=size,
                gamma=0.008,
                omega_base=0.3,  # Background frequency
                resonance_width=0.25,
                resonance_strength=0.7
            )
            
            # Create resonance well at center with different frequency
            sim.set_resonance_well(center, radius=20, omega_inside=0.5)
            
            sim.psi_r[:] = 1.2
            sim.add_vortex(start_pos, charge=1, amplitude=1.2, core_radius=4.0)
            sim.seed_oscillator(amplitude=0.1)
            
            lifetime = 0
            last_pos = start_pos
            
            for step in range(steps):
                sim.step(use_resonance=True)
                
                if step % 50 == 0:
                    current_pos = sim.find_vortex_core(last_pos, search_radius=15)
                    if current_pos:
                        lifetime = step
                        last_pos = current_pos
            
            lifetimes.append(lifetime)
        
        avg_lifetime = np.mean(lifetimes)
        results[config_name] = {
            'avg_lifetime': avg_lifetime,
            'lifetimes': lifetimes
        }
        
        print(f"  Avg lifetime: {avg_lifetime:.0f}")
    
    print()
    ratio = results['inside_well']['avg_lifetime'] / (results['outside_well']['avg_lifetime'] + 1)
    
    if ratio > 1.3:
        print(f"✓ WELL PROVIDES LOCALIZED STABILITY: {ratio:.2f}× longer inside")
    else:
        print(f"- No significant well effect ({ratio:.2f}×)")
    
    return results


# ============================================================
# TEST 3: Frequency sweep - find optimal resonance
# ============================================================

def test_frequency_sweep():
    """
    Sweep the oscillator frequency to find where vortex lifetime peaks.
    """
    print()
    print("="*70)
    print("TEST 3: FREQUENCY SWEEP")
    print("="*70)
    print()
    print("Question: Is there an optimal resonance frequency for vortex stability?")
    print()
    
    size = 80
    steps = 3000
    
    frequencies = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]
    results = []
    
    for omega in frequencies:
        sim = ResonanceStabilizationSimulator(
            size=size,
            gamma=0.008,
            omega_base=omega,
            resonance_width=0.25,
            resonance_strength=0.6
        )
        
        sim.psi_r[:] = 1.2
        sim.add_vortex((size//2, size//2), charge=1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillator(amplitude=0.1)
        
        lifetime = 0
        last_pos = (size//2, size//2)
        
        for step in range(steps):
            sim.step(use_resonance=True)
            
            if step % 50 == 0:
                current_pos = sim.find_vortex_core(last_pos, search_radius=15)
                if current_pos:
                    lifetime = step
                    last_pos = current_pos
        
        results.append({'omega': omega, 'lifetime': lifetime})
        print(f"  ω = {omega:.1f}: lifetime = {lifetime}")
    
    print()
    
    # Find peak
    best = max(results, key=lambda x: x['lifetime'])
    print(f"Peak lifetime at ω = {best['omega']:.1f} (lifetime = {best['lifetime']})")
    
    # Check if there's a clear peak
    lifetimes = [r['lifetime'] for r in results]
    if max(lifetimes) > 1.3 * np.mean(lifetimes):
        print("✓ Clear resonance peak exists")
    else:
        print("- No clear resonance peak")
    
    return results


# ============================================================
# TEST 4: Does resonance prevent core filling?
# ============================================================

def test_core_filling_prevention():
    """
    Track core amplitude over time with and without resonance.
    Does resonance keep the core open longer?
    """
    print()
    print("="*70)
    print("TEST 4: CORE FILLING PREVENTION")
    print("="*70)
    print()
    print("Question: Does resonance prevent the core-filling death mode?")
    print()
    
    size = 80
    steps = 2000
    
    results = {}
    
    for use_resonance in [False, True]:
        label = "with_resonance" if use_resonance else "no_resonance"
        
        sim = ResonanceStabilizationSimulator(
            size=size,
            gamma=0.008,
            omega_base=0.5,
            resonance_width=0.3,
            resonance_strength=0.7
        )
        
        sim.psi_r[:] = 1.2
        center = (size//2, size//2)
        sim.add_vortex(center, charge=1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillator(amplitude=0.1)
        
        core_amplitudes = []
        last_pos = center
        
        for step in range(steps):
            sim.step(use_resonance=use_resonance)
            
            if step % 25 == 0:
                current_pos = sim.find_vortex_core(last_pos, search_radius=15)
                if current_pos:
                    core_amp = sim.amplitude[current_pos[0], current_pos[1]]
                    core_amplitudes.append(core_amp)
                    last_pos = current_pos
                else:
                    # Vortex died - record high amplitude
                    core_amplitudes.append(1.0)
        
        results[label] = core_amplitudes
        
        print(f"--- {label} ---")
        print(f"  Core amp (early): {np.mean(core_amplitudes[:5]):.3f}")
        print(f"  Core amp (late):  {np.mean(core_amplitudes[-5:]):.3f}")
    
    print()
    
    # Compare filling rates
    no_res_fill = np.mean(results['no_resonance'][-5:])
    with_res_fill = np.mean(results['with_resonance'][-5:])
    
    if with_res_fill < no_res_fill * 0.8:
        print(f"✓ RESONANCE PREVENTS CORE FILLING")
        print(f"  Core amplitude {(1 - with_res_fill/no_res_fill)*100:.0f}% lower with resonance")
    else:
        print("- Core filling not significantly reduced")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*70)
    print("RESONANCE STABILIZATION TEST")
    print("="*70)
    print()
    print("Hypothesis: Vortex stability requires resonance compatibility")
    print("            across multiple frequency layers of the medium.")
    print()
    print("Model: ψ (complex field) + χ (secondary oscillator)")
    print("       Core protection when local frequencies match")
    print()
    
    test1_results = test_resonance_lifetime()
    test2_results = test_resonance_well()
    test3_results = test_frequency_sweep()
    test4_results = test_core_filling_prevention()
    
    print()
    print("="*70)
    print("FINAL VERDICT")
    print("="*70)
    print()
    
    # Evaluate
    lifetime_improved = test1_results['with_resonance']['avg_lifetime'] > test1_results['no_resonance']['avg_lifetime'] * 1.2
    well_works = test2_results['inside_well']['avg_lifetime'] > test2_results['outside_well']['avg_lifetime'] * 1.2
    peak_exists = max([r['lifetime'] for r in test3_results]) > 1.2 * np.mean([r['lifetime'] for r in test3_results])
    core_protected = np.mean(test4_results['with_resonance'][-5:]) < np.mean(test4_results['no_resonance'][-5:]) * 0.9
    
    print(f"Test 1 (Lifetime extension): {'✓ PASS' if lifetime_improved else '✗ FAIL'}")
    print(f"Test 2 (Resonance well):     {'✓ PASS' if well_works else '✗ FAIL'}")
    print(f"Test 3 (Frequency peak):     {'✓ PASS' if peak_exists else '✗ FAIL'}")
    print(f"Test 4 (Core protection):    {'✓ PASS' if core_protected else '✗ FAIL'}")
    print()
    
    passed = sum([lifetime_improved, well_works, peak_exists, core_protected])
    
    if passed >= 3:
        print("CONCLUSION: RESONANCE STABILIZATION IS A VIABLE MECHANISM")
        print("            Multi-frequency structure can provide core protection.")
        print("            This supports the 'layered resonance' hypothesis.")
    elif passed >= 2:
        print("CONCLUSION: PARTIAL SUPPORT FOR RESONANCE STABILIZATION")
        print("            Some evidence, but mechanism needs refinement.")
    else:
        print("CONCLUSION: RESONANCE MECHANISM NOT CLEARLY EFFECTIVE")
        print("            The implementation may need different coupling.")
