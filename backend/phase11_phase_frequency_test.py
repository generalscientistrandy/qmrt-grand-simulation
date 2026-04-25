"""
Phase 11h: Phase-Frequency Separation Test
============================================

THEORETICAL REFINEMENT:

Phase 11g showed balance is statistical, not relational (by sign).
But if matter/antimatter are PHASE-OPPOSED wave organizations
separated by FREQUENCY LAYERS, then:
  - Sign is too crude a label
  - The real distinction is phase timing (0° vs 180°)
  - Coexistence is enabled by frequency/channel separation

KEY QUESTIONS:

1. PHASE OPPOSITION
   - Are + and - defects actually at opposite phases (~π offset)?
   - Is phase offset correlated with sign?

2. FREQUENCY/CHANNEL SEPARATION  
   - Do opposite sectors occupy different resonance bands?
   - Is channel_assignment or remnant_field different between sectors?

3. CANCELLATION CONDITIONS
   - When do population drops occur?
   - Are they correlated with phase AND channel alignment?

PREDICTION:
If coexistence requires phase opposition + frequency separation:
  - + and - defects should show ~π phase difference
  - They should occupy different channel/remnant regions
  - Annihilation should occur when both phase AND channel align
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr, circmean, circstd
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class PhaseFrequencySimulator:
    """Simulator with phase and channel tracking for separation analysis."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 4
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.005
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = 0.7
                    elif dist >= interior_r + 10.0:
                        coupling[i, j, k] = 0.2
                    else:
                        t = (dist - interior_r) / 10.0
                        coupling[i, j, k] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        return coupling
    
    def inject_vortex(self, cx: int, cy: int, chirality: int = 1):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_balanced_vortices(self):
        center = self.size // 2
        for i, chirality in enumerate([+1, +1, -1, -1]):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy, chirality)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        if self.step_count % self.injection_interval == 0:
            self.inject_balanced_vortices()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        c_eff_sq = self.c_0_sq * self.tau
        
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        self.remnant_field += 0.02 * topology_norm
        self.remnant_field *= 0.999
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects_with_phase(self, threshold: float = 0.4) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect defects with full phase and channel information.
        
        Returns detailed defect info including:
          - position
          - sign (chirality)
          - local phase
          - channel assignment
          - remnant field value
        """
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        positive_defects = []
        negative_defects = []
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                cz = int(np.mean(coords[2]))
                
                local_vort = vorticity[cx, cy, cz]
                local_phase = phase[cx, cy, cz]
                local_channel = self.channel_assignment[cx, cy, cz]
                local_remnant = self.remnant_field[cx, cy, cz]
                local_tau = self.tau[cx, cy, cz]
                
                defect_info = {
                    'pos': (cx, cy, cz),
                    'phase': float(local_phase),  # -π to π
                    'channel': float(local_channel),
                    'remnant': float(local_remnant),
                    'tau': float(local_tau),
                }
                
                if local_vort > 0.05:
                    defect_info['sign'] = +1
                    positive_defects.append(defect_info)
                elif local_vort < -0.05:
                    defect_info['sign'] = -1
                    negative_defects.append(defect_info)
        
        return positive_defects, negative_defects


def measure_phase_frequency_separation(pos_defects, neg_defects) -> Dict:
    """
    Measure phase and frequency/channel separation between sectors.
    
    KEY METRICS:
    1. Phase opposition: Is there a ~π phase offset between sectors?
    2. Channel separation: Do sectors occupy different channel values?
    3. Remnant separation: Do sectors have different remnant field association?
    """
    n_pos = len(pos_defects)
    n_neg = len(neg_defects)
    n_total = n_pos + n_neg
    
    if n_total < 10 or n_pos < 3 or n_neg < 3:
        return {'valid': False, 'n_total': n_total}
    
    # Extract values
    pos_phases = np.array([d['phase'] for d in pos_defects])
    neg_phases = np.array([d['phase'] for d in neg_defects])
    
    pos_channels = np.array([d['channel'] for d in pos_defects])
    neg_channels = np.array([d['channel'] for d in neg_defects])
    
    pos_remnants = np.array([d['remnant'] for d in pos_defects])
    neg_remnants = np.array([d['remnant'] for d in neg_defects])
    
    pos_taus = np.array([d['tau'] for d in pos_defects])
    neg_taus = np.array([d['tau'] for d in neg_defects])
    
    # 1. PHASE ANALYSIS
    # Circular mean of each sector's phases
    pos_phase_mean = circmean(pos_phases, high=np.pi, low=-np.pi)
    neg_phase_mean = circmean(neg_phases, high=np.pi, low=-np.pi)
    
    # Phase offset between sectors (should be ~π for phase opposition)
    phase_offset = np.abs(np.angle(np.exp(1j * (pos_phase_mean - neg_phase_mean))))
    
    # Phase spread within each sector
    pos_phase_std = circstd(pos_phases, high=np.pi, low=-np.pi)
    neg_phase_std = circstd(neg_phases, high=np.pi, low=-np.pi)
    
    # 2. CHANNEL SEPARATION
    pos_channel_mean = np.mean(pos_channels)
    neg_channel_mean = np.mean(neg_channels)
    channel_separation = abs(pos_channel_mean - neg_channel_mean)
    
    # 3. REMNANT SEPARATION
    pos_remnant_mean = np.mean(pos_remnants)
    neg_remnant_mean = np.mean(neg_remnants)
    remnant_separation = abs(pos_remnant_mean - neg_remnant_mean)
    
    # 4. TAU SEPARATION
    pos_tau_mean = np.mean(pos_taus)
    neg_tau_mean = np.mean(neg_taus)
    tau_separation = abs(pos_tau_mean - neg_tau_mean)
    
    return {
        'valid': True,
        'n_pos': n_pos,
        'n_neg': n_neg,
        # Phase metrics
        'pos_phase_mean': float(pos_phase_mean),
        'neg_phase_mean': float(neg_phase_mean),
        'phase_offset': float(phase_offset),  # Ideally ~π
        'phase_offset_pi': float(phase_offset / np.pi),  # Normalized: 1.0 = π offset
        'pos_phase_std': float(pos_phase_std),
        'neg_phase_std': float(neg_phase_std),
        # Channel metrics
        'pos_channel_mean': float(pos_channel_mean),
        'neg_channel_mean': float(neg_channel_mean),
        'channel_separation': float(channel_separation),
        # Remnant metrics
        'pos_remnant_mean': float(pos_remnant_mean),
        'neg_remnant_mean': float(neg_remnant_mean),
        'remnant_separation': float(remnant_separation),
        # Tau metrics
        'pos_tau_mean': float(pos_tau_mean),
        'neg_tau_mean': float(neg_tau_mean),
        'tau_separation': float(tau_separation),
    }


def run_phase_frequency_test():
    """
    Test whether + and - sectors show phase opposition and frequency/channel separation.
    """
    print("=" * 75)
    print("  PHASE 11h: PHASE-FREQUENCY SEPARATION TEST")
    print("=" * 75)
    print()
    print("Hypothesis: Matter/antimatter are phase-opposed (0° vs 180°) wave")
    print("            organizations, separated by frequency/channel layers.")
    print()
    print("Key Metrics:")
    print("  - Phase offset: Should be ~π (1.0 normalized) if phase-opposed")
    print("  - Channel separation: Should be non-zero if frequency-separated")
    print()
    
    sim = PhaseFrequencySimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Balanced initial seeding
    center = 24
    for i, chirality in zip(range(-3, 4), [+1, -1, +1, -1, +1, -1, +1]):
        for j, chirality2 in zip(range(-3, 4), [-1, +1, -1, +1, -1, +1, -1]):
            if abs(i) + abs(j) <= 3:
                c = chirality * chirality2
                sim.inject_vortex(center + i * 4, center + j * 4, c)
    
    print(f"{'Step':>5} │ {'N+':>3} {'N-':>3} │ {'φ+':>6} {'φ-':>6} │ "
          f"{'Δφ/π':>5} │ {'ΔChan':>6} {'ΔRem':>6} │ {'Δτ':>6}")
    print("-" * 75)
    
    history = []
    
    for step in range(1200):
        sim.step()
        
        if step % 50 == 0:
            pos_defects, neg_defects = sim.detect_defects_with_phase()
            m = measure_phase_frequency_separation(pos_defects, neg_defects)
            
            if m['valid']:
                print(f"{step:>5} │ {m['n_pos']:>3} {m['n_neg']:>3} │ "
                      f"{m['pos_phase_mean']:>+6.2f} {m['neg_phase_mean']:>+6.2f} │ "
                      f"{m['phase_offset_pi']:>5.3f} │ "
                      f"{m['channel_separation']:>6.4f} {m['remnant_separation']:>6.4f} │ "
                      f"{m['tau_separation']:>6.4f}")
                
                m['step'] = step
                history.append(m)
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("PHASE-FREQUENCY ANALYSIS")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n_pos'] > 5 and h['n_neg'] > 5]
    
    if len(valid) >= 5:
        # 1. PHASE OPPOSITION
        print("1. PHASE OPPOSITION")
        print("-" * 40)
        
        avg_offset_pi = np.mean([h['phase_offset_pi'] for h in valid])
        std_offset_pi = np.std([h['phase_offset_pi'] for h in valid])
        
        print(f"  Average phase offset: {avg_offset_pi:.3f}π ± {std_offset_pi:.3f}")
        print(f"  (1.0 = perfect opposition, 0.5 = orthogonal, 0.0 = aligned)")
        print()
        
        if avg_offset_pi > 0.7:
            print(f"  → STRONG PHASE OPPOSITION (near π)")
            phase_verdict = "opposition"
        elif avg_offset_pi > 0.4:
            print(f"  → MODERATE PHASE OFFSET")
            phase_verdict = "moderate"
        else:
            print(f"  → WEAK PHASE OFFSET (near aligned)")
            phase_verdict = "aligned"
        
        print()
        
        # 2. CHANNEL SEPARATION
        print("2. CHANNEL/FREQUENCY SEPARATION")
        print("-" * 40)
        
        avg_channel_sep = np.mean([h['channel_separation'] for h in valid])
        avg_remnant_sep = np.mean([h['remnant_separation'] for h in valid])
        avg_tau_sep = np.mean([h['tau_separation'] for h in valid])
        
        # Compare to typical within-sector spread
        pos_channel_vals = [h['pos_channel_mean'] for h in valid]
        neg_channel_vals = [h['neg_channel_mean'] for h in valid]
        within_spread = (np.std(pos_channel_vals) + np.std(neg_channel_vals)) / 2
        
        print(f"  Channel separation:  {avg_channel_sep:.4f}")
        print(f"  Remnant separation:  {avg_remnant_sep:.4f}")
        print(f"  τ separation:        {avg_tau_sep:.4f}")
        print(f"  Within-sector spread: {within_spread:.4f}")
        print()
        
        # Is separation larger than noise?
        if avg_channel_sep > 2 * within_spread:
            print(f"  → SIGNIFICANT CHANNEL SEPARATION")
            channel_verdict = "separated"
        elif avg_channel_sep > within_spread:
            print(f"  → WEAK CHANNEL SEPARATION")
            channel_verdict = "weak"
        else:
            print(f"  → NO CHANNEL SEPARATION (within noise)")
            channel_verdict = "none"
        
        print()
        print("=" * 75)
        print("CONCLUSION")
        print("=" * 75)
        print()
        
        if phase_verdict == "opposition" and channel_verdict in ["separated", "weak"]:
            print("PHASE-FREQUENCY SEPARATION CONFIRMED")
            print()
            print("+ and - sectors show:")
            print(f"  - Phase opposition: {avg_offset_pi:.2f}π")
            print(f"  - Channel separation: {avg_channel_sep:.4f}")
            print()
            print("This supports the theory that coexistence is enabled by:")
            print("  - Phase-opposed wave organization (0° vs 180°)")
            print("  - Frequency/channel layer separation")
            conclusion = "confirmed"
        elif phase_verdict == "opposition":
            print("PHASE OPPOSITION ONLY")
            print()
            print(f"Sectors show phase opposition ({avg_offset_pi:.2f}π) but")
            print("no significant channel separation.")
            print()
            print("Phase opposition may be sufficient for sign distinction,")
            print("but frequency separation is not clearly present.")
            conclusion = "phase_only"
        elif channel_verdict in ["separated", "weak"]:
            print("CHANNEL SEPARATION ONLY")
            print()
            print(f"Sectors show channel separation ({avg_channel_sep:.4f}) but")
            print("no strong phase opposition.")
            print()
            print("Sign distinction may come from channel, not phase.")
            conclusion = "channel_only"
        else:
            print("NO CLEAR SEPARATION PATTERN")
            print()
            print("Neither phase opposition nor channel separation is strong.")
            print("Sign distinction may be purely topological (vorticity).")
            conclusion = "none"
    else:
        conclusion = "insufficient_data"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase11_phase_frequency_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'phase_frequency_separation',
            'hypothesis': 'Coexistence via phase opposition + frequency separation',
            'history': history,
            'phase_verdict': phase_verdict if 'phase_verdict' in dir() else 'unknown',
            'channel_verdict': channel_verdict if 'channel_verdict' in dir() else 'unknown',
            'conclusion': conclusion,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, conclusion


if __name__ == "__main__":
    history, conclusion = run_phase_frequency_test()
