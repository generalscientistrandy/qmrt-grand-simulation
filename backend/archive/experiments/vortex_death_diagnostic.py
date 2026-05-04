"""
Vortex Death Diagnostic
=======================

Goal: Identify HOW vortices die so we know WHAT to target.

Tracked quantities (per timestep):
1. Core amplitude minimum
2. Local phase winding strength  
3. Local gradient magnitude
4. Distance to nearest antivortex (if present)
5. Local Σ (if feedback active)
6. Local γ (effective damping)

Classification questions:
- Does amplitude recover before winding disappears? → Core diffusion
- Does winding collapse before amplitude fills? → Phase unwinding
- Does partner approach cause death? → Annihilation-dominated
- Does background flatten before defect dies? → Homogenization
- Does core shrink progressively? → Core erosion

The answer tells us what mechanism to target.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional
import json


class DiagnosticSimulator:
    """
    Complex scalar simulator with detailed vortex tracking.
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
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.beta = beta
        self.D_medium = D_medium
        self.dt = dt
        
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    @property
    def rho(self) -> np.ndarray:
        return self.psi_r**2 + self.psi_i**2 + self.psi_r_dot**2 + self.psi_i_dot**2
    
    def compute_c_eff(self) -> np.ndarray:
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho: np.ndarray) -> np.ndarray:
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def step(self):
        rho = self.rho
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        c_eff_sq = c_eff**2
        
        lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                 np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
        lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                 np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
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
                         search_radius: int = 10) -> Optional[Tuple[int, int]]:
        """Find amplitude minimum near search_center."""
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
        
        # Verify it's actually a vortex
        if best_pos and min_amp < 0.5:
            winding = self.compute_winding_number(best_pos[0], best_pos[1], radius=2)
            if abs(winding) > 0.5:
                return best_pos
        
        return None
    
    def measure_vortex_diagnostics(self, vortex_pos: Tuple[int, int], 
                                    partner_pos: Optional[Tuple[int, int]] = None) -> Dict:
        """
        Comprehensive diagnostics for a single vortex.
        """
        i, j = vortex_pos
        amp = self.amplitude
        phase = self.phase
        
        # 1. Core amplitude minimum
        core_amp = amp[i, j]
        
        # 2. Local phase winding strength
        winding = self.compute_winding_number(i, j, radius=2)
        winding_strength = abs(winding)
        
        # 3. Local gradient magnitude (around core)
        grad_r_x = (self.psi_r[(i+1)%self.size, j] - self.psi_r[(i-1)%self.size, j]) / 2
        grad_r_y = (self.psi_r[i, (j+1)%self.size] - self.psi_r[i, (j-1)%self.size]) / 2
        grad_i_x = (self.psi_i[(i+1)%self.size, j] - self.psi_i[(i-1)%self.size, j]) / 2
        grad_i_y = (self.psi_i[i, (j+1)%self.size] - self.psi_i[i, (j-1)%self.size]) / 2
        local_grad = np.sqrt(grad_r_x**2 + grad_r_y**2 + grad_i_x**2 + grad_i_y**2)
        
        # 4. Core radius estimate (distance to amplitude = 0.5 * background)
        background_amp = np.mean(amp[amp > np.percentile(amp, 80)])
        threshold = 0.5 * background_amp
        
        core_radius = 0
        for r in range(1, 15):
            ring_amps = []
            for angle in np.linspace(0, 2*np.pi, 16):
                ri = int(i + r * np.cos(angle)) % self.size
                rj = int(j + r * np.sin(angle)) % self.size
                ring_amps.append(amp[ri, rj])
            if np.mean(ring_amps) > threshold:
                core_radius = r
                break
        
        # 5. Distance to partner (if present)
        partner_distance = None
        if partner_pos:
            di = partner_pos[0] - i
            dj = partner_pos[1] - j
            # Handle periodic boundaries
            if abs(di) > self.size // 2:
                di = di - np.sign(di) * self.size
            if abs(dj) > self.size // 2:
                dj = dj - np.sign(dj) * self.size
            partner_distance = np.sqrt(di**2 + dj**2)
        
        # 6. Local energy density
        local_rho = self.rho[i, j]
        
        # 7. Background uniformity (how flat is the field away from vortex)
        mask = np.ones((self.size, self.size), dtype=bool)
        mask[max(0,i-10):min(self.size,i+10), max(0,j-10):min(self.size,j+10)] = False
        background_cv = np.std(amp[mask]) / (np.mean(amp[mask]) + 1e-10)
        
        # 8. Phase coherence in annulus around core
        phase_coherence = 0
        if core_radius > 2:
            annulus_phases = []
            for angle in np.linspace(0, 2*np.pi, 32):
                r = core_radius + 2
                ri = int(i + r * np.cos(angle)) % self.size
                rj = int(j + r * np.sin(angle)) % self.size
                annulus_phases.append(phase[ri, rj])
            # Coherence = how well phases follow expected winding
            expected_phases = np.linspace(0, 2*np.pi * winding, 32)
            phase_diffs = np.array(annulus_phases) - expected_phases
            phase_diffs = np.mod(phase_diffs + np.pi, 2*np.pi) - np.pi
            phase_coherence = 1.0 - np.std(phase_diffs) / np.pi
        
        return {
            'core_amplitude': core_amp,
            'winding_strength': winding_strength,
            'local_gradient': local_grad,
            'core_radius': core_radius,
            'partner_distance': partner_distance,
            'local_rho': local_rho,
            'background_cv': background_cv,
            'phase_coherence': phase_coherence,
            'position': vortex_pos
        }


def run_single_vortex_death_diagnostic():
    """
    Track a single vortex from birth to death.
    """
    print("="*70)
    print("DIAGNOSTIC 1: SINGLE VORTEX DEATH")
    print("="*70)
    print()
    
    size = 80
    sim = DiagnosticSimulator(size=size, gamma=0.008)
    
    sim.psi_r[:] = 1.2
    initial_pos = (size//2, size//2)
    sim.add_vortex(initial_pos, charge=1, amplitude=1.2, core_radius=4.0)
    
    timeline = []
    last_known_pos = initial_pos
    death_step = None
    
    for step in range(6000):
        sim.step()
        
        if step % 25 == 0:  # Fine-grained tracking
            # Find current vortex position
            current_pos = sim.find_vortex_core(last_known_pos, search_radius=15)
            
            if current_pos:
                diag = sim.measure_vortex_diagnostics(current_pos)
                diag['step'] = step
                diag['alive'] = True
                timeline.append(diag)
                last_known_pos = current_pos
            else:
                # Vortex died - record death diagnostics at last known position
                diag = sim.measure_vortex_diagnostics(last_known_pos)
                diag['step'] = step
                diag['alive'] = False
                timeline.append(diag)
                
                if death_step is None:
                    death_step = step
                    print(f"Vortex died at step {step}")
                
                # Continue tracking for a bit after death
                if step > death_step + 500:
                    break
    
    return timeline, death_step


def run_pair_death_diagnostic():
    """
    Track a vortex-antivortex pair from birth to annihilation.
    """
    print()
    print("="*70)
    print("DIAGNOSTIC 2: VORTEX-ANTIVORTEX PAIR DEATH")
    print("="*70)
    print()
    
    size = 80
    sim = DiagnosticSimulator(size=size, gamma=0.008)
    
    sim.psi_r[:] = 1.2
    v1_pos = (size//2 - 12, size//2)  # Vortex
    v2_pos = (size//2 + 12, size//2)  # Antivortex
    
    sim.add_vortex(v1_pos, charge=+1, amplitude=1.2, core_radius=4.0)
    sim.add_vortex(v2_pos, charge=-1, amplitude=1.2, core_radius=4.0)
    
    timeline_v1 = []
    timeline_v2 = []
    last_v1 = v1_pos
    last_v2 = v2_pos
    annihilation_step = None
    
    for step in range(4000):
        sim.step()
        
        if step % 20 == 0:
            # Find both vortices
            current_v1 = sim.find_vortex_core(last_v1, search_radius=15)
            current_v2 = sim.find_vortex_core(last_v2, search_radius=15)
            
            if current_v1:
                partner = current_v2 if current_v2 else last_v2
                diag = sim.measure_vortex_diagnostics(current_v1, partner_pos=partner)
                diag['step'] = step
                diag['alive'] = True
                timeline_v1.append(diag)
                last_v1 = current_v1
            else:
                diag = sim.measure_vortex_diagnostics(last_v1, partner_pos=last_v2)
                diag['step'] = step
                diag['alive'] = False
                timeline_v1.append(diag)
            
            if current_v2:
                partner = current_v1 if current_v1 else last_v1
                diag = sim.measure_vortex_diagnostics(current_v2, partner_pos=partner)
                diag['step'] = step
                diag['alive'] = True
                timeline_v2.append(diag)
                last_v2 = current_v2
            else:
                diag = sim.measure_vortex_diagnostics(last_v2, partner_pos=last_v1)
                diag['step'] = step
                diag['alive'] = False
                timeline_v2.append(diag)
            
            # Check for annihilation
            if not current_v1 and not current_v2 and annihilation_step is None:
                annihilation_step = step
                print(f"Pair annihilated at step {step}")
            
            if annihilation_step and step > annihilation_step + 200:
                break
    
    return timeline_v1, timeline_v2, annihilation_step


def analyze_death_sequence(timeline: List[Dict], label: str = "Vortex"):
    """
    Analyze the timeline to classify the death mode.
    """
    print()
    print(f"--- {label} Death Analysis ---")
    print()
    
    # Find death point
    death_idx = None
    for i, t in enumerate(timeline):
        if not t['alive']:
            death_idx = i
            break
    
    if death_idx is None:
        print("Vortex survived entire simulation")
        return None
    
    if death_idx < 5:
        print("Vortex died too quickly for analysis")
        return None
    
    # Extract pre-death sequence (last 10 samples before death)
    pre_death = timeline[max(0, death_idx-10):death_idx]
    
    # Track key quantities
    core_amps = [t['core_amplitude'] for t in pre_death]
    windings = [t['winding_strength'] for t in pre_death]
    gradients = [t['local_gradient'] for t in pre_death]
    core_radii = [t['core_radius'] for t in pre_death]
    distances = [t['partner_distance'] for t in pre_death if t['partner_distance'] is not None]
    coherences = [t['phase_coherence'] for t in pre_death]
    
    print("Pre-death sequence (last 10 samples):")
    print(f"  Core amplitude: {core_amps[0]:.3f} → {core_amps[-1]:.3f}")
    print(f"  Winding strength: {windings[0]:.3f} → {windings[-1]:.3f}")
    print(f"  Local gradient: {gradients[0]:.3f} → {gradients[-1]:.3f}")
    print(f"  Core radius: {core_radii[0]} → {core_radii[-1]}")
    print(f"  Phase coherence: {coherences[0]:.3f} → {coherences[-1]:.3f}")
    if distances:
        print(f"  Partner distance: {distances[0]:.1f} → {distances[-1]:.1f}")
    print()
    
    # Classify death mode
    death_mode = "UNKNOWN"
    
    # Calculate rates of change
    amp_trend = (core_amps[-1] - core_amps[0]) / (len(core_amps) * 0.001 + 0.001)
    winding_trend = (windings[-1] - windings[0]) / (len(windings) * 0.001 + 0.001)
    radius_trend = (core_radii[-1] - core_radii[0]) / (len(core_radii) * 0.001 + 0.001)
    
    # Check for different death modes
    if distances and len(distances) >= 2:
        distance_trend = distances[-1] - distances[0]
        if distance_trend < -5:  # Partner approached significantly
            death_mode = "ANNIHILATION"
            print(f"→ Death mode: ANNIHILATION (partner approached by {-distance_trend:.1f} units)")
    
    if death_mode == "UNKNOWN":
        # Check if amplitude filled in while winding persisted
        if core_amps[-1] > 0.3 and windings[-1] < 0.5:
            death_mode = "PHASE_UNWINDING"
            print("→ Death mode: PHASE UNWINDING (winding collapsed before amplitude filled)")
        
        elif core_amps[-1] > core_amps[0] * 1.5 and windings[-1] > 0.5:
            death_mode = "CORE_FILLING"
            print("→ Death mode: CORE FILLING (amplitude increased, smothering core)")
        
        elif core_radii[-1] > core_radii[0] * 1.5:
            death_mode = "CORE_DIFFUSION"
            print("→ Death mode: CORE DIFFUSION (core expanded and dispersed)")
        
        elif coherences[-1] < coherences[0] * 0.5:
            death_mode = "DECOHERENCE"
            print("→ Death mode: DECOHERENCE (phase structure broke down)")
        
        else:
            death_mode = "GRADUAL_DECAY"
            print("→ Death mode: GRADUAL DECAY (slow erosion, no single dominant channel)")
    
    # Additional insights
    print()
    print("Quantitative summary:")
    print(f"  Amplitude change rate: {amp_trend:+.4f}")
    print(f"  Winding change rate: {winding_trend:+.4f}")
    print(f"  Core radius change rate: {radius_trend:+.2f}")
    
    return {
        'death_mode': death_mode,
        'final_core_amp': core_amps[-1],
        'final_winding': windings[-1],
        'amp_trend': amp_trend,
        'winding_trend': winding_trend,
        'pre_death_sequence': pre_death
    }


def main():
    print("="*70)
    print("VORTEX DEATH DIAGNOSTIC")
    print("="*70)
    print()
    print("Goal: Identify HOW vortices die to know WHAT to target")
    print()
    
    # Diagnostic 1: Single vortex
    timeline_single, death_single = run_single_vortex_death_diagnostic()
    analysis_single = analyze_death_sequence(timeline_single, "Single Vortex")
    
    # Diagnostic 2: Vortex-antivortex pair
    timeline_v1, timeline_v2, annihilation_step = run_pair_death_diagnostic()
    analysis_v1 = analyze_death_sequence(timeline_v1, "Vortex (+1)")
    analysis_v2 = analyze_death_sequence(timeline_v2, "Antivortex (-1)")
    
    # Summary
    print()
    print("="*70)
    print("DIAGNOSTIC SUMMARY")
    print("="*70)
    print()
    
    modes = []
    if analysis_single:
        modes.append(('Single vortex', analysis_single['death_mode']))
    if analysis_v1:
        modes.append(('Pair vortex', analysis_v1['death_mode']))
    if analysis_v2:
        modes.append(('Pair antivortex', analysis_v2['death_mode']))
    
    print("Death modes observed:")
    for label, mode in modes:
        print(f"  {label}: {mode}")
    
    # Determine dominant failure channel
    print()
    print("="*70)
    print("IMPLICATIONS FOR STABILIZATION")
    print("="*70)
    print()
    
    mode_counts = {}
    for _, mode in modes:
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    
    dominant_mode = max(mode_counts, key=mode_counts.get) if mode_counts else "UNKNOWN"
    
    print(f"Dominant failure mode: {dominant_mode}")
    print()
    
    if dominant_mode == "ANNIHILATION":
        print("→ IMPLICATION: Need to prevent vortex-antivortex approach")
        print("   Options:")
        print("   - Reduce vortex mobility")
        print("   - Create repulsive barrier")
        print("   - Pin vortices spatially")
        print("   - Increase annihilation radius (make approach costly)")
    
    elif dominant_mode == "CORE_FILLING":
        print("→ IMPLICATION: Need to prevent amplitude from filling core")
        print("   Options:")
        print("   - Core-stiffening potential")
        print("   - Local amplitude suppression at winding sites")
        print("   - Phase-amplitude coupling that maintains core")
    
    elif dominant_mode == "PHASE_UNWINDING":
        print("→ IMPLICATION: Need to stabilize phase winding")
        print("   Options:")
        print("   - Penalize phase gradient reduction")
        print("   - Topological protection term")
        print("   - Phase-locking mechanism")
    
    elif dominant_mode == "CORE_DIFFUSION":
        print("→ IMPLICATION: Need to prevent core spreading")
        print("   Options:")
        print("   - Core-confining potential")
        print("   - Negative diffusion at low amplitude")
        print("   - Local β increase to stiffen core")
    
    elif dominant_mode == "DECOHERENCE":
        print("→ IMPLICATION: Need to maintain phase coherence")
        print("   Options:")
        print("   - Phase-locking to neighbors")
        print("   - Coherence-preserving dynamics")
        print("   - Reduce environmental noise")
    
    elif dominant_mode == "GRADUAL_DECAY":
        print("→ IMPLICATION: Multiple channels contribute")
        print("   Options:")
        print("   - General lifetime extension (reduce γ)")
        print("   - May need compound stabilization")
        print("   - Consider if single intervention is sufficient")
    
    print()
    print("This diagnostic should inform the next model modification.")
    
    return {
        'single_analysis': analysis_single,
        'pair_v1_analysis': analysis_v1,
        'pair_v2_analysis': analysis_v2,
        'dominant_mode': dominant_mode
    }


if __name__ == "__main__":
    results = main()
