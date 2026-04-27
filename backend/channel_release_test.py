"""
Channel Release → τ Test: Secondary Recovery Branch
====================================================

PURPOSE: Test Channel release as additive mechanism to v1.1 baseline.

HYPOTHESIS: Channel-bound energy can reinforce τ recharge when topology
decays or migrates, providing a secondary reservoir mechanism.

BASELINE (Locked v1.1):
  damping_to_tau = 0.20
  tau_cap = 1.8

SWEEP:
  channel_release_to_tau = [0.00, 0.02, 0.05, 0.10]
  T = 1000
  seeds = 5

MECHANISM:
  When topology decays (channel decreases), release energy to τ:
  tau += channel_release_to_tau * delta_channel_negative * channel_energy

DECISION RULE:
  Accept Channel release only if:
  - N_mean increases OR remains comparable
  - N_std decreases (more stable)
  - tau_localization does not rise above v1.1 (1.35)
  - No spike-then-crash pattern

  If N_mean increases but tau_loc also increases: risky overdrive branch.

TRACKING:
  N_mean, N_std, tau_localization_index, channel_energy,
  release_events, creation_count, late_N_trend
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List
import time
import json


# Locked v1.1 Configuration
REGULATED_RECOVERY_TAU_CAP = 1.8
OPTIMAL_DAMPING_TO_TAU = 0.20


class ChannelReleaseSimulator:
    """
    Simulator with Channel release → τ as secondary branch.
    
    Mechanism: When channel field decreases (topology decays/migrates),
    release a fraction of the channel-bound energy to τ.
    """
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = OPTIMAL_DAMPING_TO_TAU,
                 tau_cap: float = REGULATED_RECOVERY_TAU_CAP,
                 channel_release_to_tau: float = 0.0):
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        self.channel_release_to_tau = channel_release_to_tau
        
        self.T = 0.0
        self.step_count = 0
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        self.channel = np.zeros((size, size, size))
        self.prev_channel = np.zeros((size, size, size))
        
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
        # Tracking
        self.creations = 0
        self.total_damped = 0.0
        self.total_recycled = 0.0
        self.total_channel_released = 0.0
        self.release_events = 0
        self.explosion = False
        
    def inject_vortex(self, cx, cy, cz, chirality=1):
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / 18)
        
        vortex = np.tanh(r / 2.5) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_structure(self, n_pairs=8):
        center = self.size // 2
        for _ in range(n_pairs):
            a1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.17)
            cx1 = int(np.clip(center + r1 * np.cos(a1), 3, self.size - 3))
            cy1 = int(np.clip(center + r1 * np.sin(a1), 3, self.size - 3))
            
            a2 = a1 + np.random.uniform(0.5, 1.5)
            r2 = np.random.uniform(2, self.size * 0.17)
            cx2 = int(np.clip(center + r2 * np.cos(a2), 3, self.size - 3))
            cy2 = int(np.clip(center + r2 * np.sin(a2), 3, self.size - 3))
            
            self.inject_vortex(cx1, cy1, center, +1)
            self.inject_vortex(cx2, cy2, center, -1)
    
    def attempt_creation(self):
        high_tau = self.tau > self.tau_creation_threshold
        if not np.any(high_tau):
            return 0
        
        candidates = np.where(high_tau)
        n = len(candidates[0])
        if n == 0:
            return 0
        
        indices = np.random.choice(n, min(25, n), replace=False)
        
        for idx in indices:
            local_tau = self.tau[candidates[0][idx], candidates[1][idx], candidates[2][idx]]
            prob = (local_tau - self.tau_creation_threshold) * self.creation_rate
            
            if np.random.random() < prob:
                center = self.size // 2
                angle = np.random.uniform(0, 2*np.pi)
                r = np.random.uniform(2, self.size * 0.16)
                cx = int(np.clip(center + r * np.cos(angle), 3, self.size - 3))
                cy = int(np.clip(center + r * np.sin(angle), 3, self.size - 3))
                
                a2 = np.random.uniform(0, 2*np.pi)
                d = np.random.uniform(2, 4)
                cx2 = int(np.clip(cx + d * np.cos(a2), 2, self.size - 2))
                cy2 = int(np.clip(cy + d * np.sin(a2), 2, self.size - 2))
                
                self.inject_vortex(cx, cy, center, +1)
                self.inject_vortex(cx2, cy2, center, -1)
                self.creations += 1
                return 1
        return 0
    
    def step(self):
        self.step_count += 1
        self.T += self.dt
        
        self.attempt_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        self.total_damped += float(np.sum(damped_energy))
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # PRIMARY: Damping → τ coupling (v1.1 baseline)
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        # Compute topology and update channel
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Store previous channel for release calculation
        self.prev_channel = self.channel.copy()
        
        # Update channel
        self.channel = np.clip(self.channel + 0.01 * (topology_norm - self.channel), 0, 1)
        
        # SECONDARY: Channel release → τ coupling
        if self.channel_release_to_tau > 0:
            # Where channel decreased (topology decayed/migrated)
            delta_channel = self.channel - self.prev_channel
            channel_decrease = np.maximum(-delta_channel, 0)  # Only decreases
            
            # Energy in channel is proportional to channel value and local energy
            channel_energy = self.prev_channel * energy
            
            # Release to τ
            release = self.channel_release_to_tau * channel_decrease * channel_energy
            release_amount = float(np.sum(release))
            
            if release_amount > 0:
                self.tau += release
                self.total_channel_released += release_amount
                self.release_events += 1
        
        # Apply regulated τ cap
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        protection = topology_norm * self.channel
        radial_r, radial_i = self.psi_r / amp, self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        total_energy = float(np.mean(energy))
        if np.isnan(total_energy) or total_energy > 1000:
            self.explosion = True
        
        return total_energy
    
    def detect_defects(self):
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < 0.4)
        return sum(1 for i in range(1, n + 1) if np.sum(labeled == i) >= 3)
    
    def get_snapshot(self):
        tau_mean = float(np.mean(self.tau))
        tau_max = float(np.max(self.tau))
        
        return {
            'T': self.T,
            'defects': self.detect_defects(),
            'creations': self.creations,
            'tau_mean': tau_mean,
            'tau_max': tau_max,
            'tau_std': float(np.std(self.tau)),
            'tau_localization_index': tau_max / tau_mean if tau_mean > 0 else 0,
            'channel_mean': float(np.mean(self.channel)),
            'total_damped': self.total_damped,
            'total_recycled': self.total_recycled,
            'total_channel_released': self.total_channel_released,
            'release_events': self.release_events,
            'explosion': self.explosion
        }


def run_channel_test(channel_release: float, seed: int, T_max: float = 1000) -> Dict:
    """Run single channel release test."""
    np.random.seed(seed)
    
    sim = ChannelReleaseSimulator(
        size=32, dt=0.12,
        damping_to_tau=OPTIMAL_DAMPING_TO_TAU,
        tau_cap=REGULATED_RECOVERY_TAU_CAP,
        channel_release_to_tau=channel_release
    )
    sim.psi_r += 0.03 * np.random.randn(32, 32, 32)
    sim.psi_i += 0.03 * np.random.randn(32, 32, 32)
    sim.seed_structure(8)
    
    checkpoints = [500, 1000]
    results = {}
    cp_idx = 0
    
    while sim.T < T_max + sim.dt and not sim.explosion:
        sim.step()
        
        while cp_idx < len(checkpoints) and sim.T >= checkpoints[cp_idx]:
            results[checkpoints[cp_idx]] = sim.get_snapshot()
            cp_idx += 1
    
    return results


def main():
    print("=" * 80)
    print("  CHANNEL RELEASE → τ TEST: SECONDARY RECOVERY BRANCH")
    print("=" * 80)
    print()
    print("Baseline (locked v1.1): damping=0.20, cap=1.8")
    print("Testing: channel_release_to_tau = [0.00, 0.02, 0.05, 0.10]")
    print()
    
    channel_strengths = [0.00, 0.02, 0.05, 0.10]
    seeds = [10, 42, 99, 123, 456]
    
    all_results = {c: [] for c in channel_strengths}
    
    start_time = time.time()
    
    for channel_release in channel_strengths:
        name = "v1.1 only" if channel_release == 0 else f"v1.1 + ch={channel_release}"
        print(f"Testing {name}...", end=" ", flush=True)
        t0 = time.time()
        
        for seed in seeds:
            result = run_channel_test(channel_release, seed, T_max=1000)
            all_results[channel_release].append({'seed': seed, 'data': result})
        
        # Quick summary
        n_vals = [r['data'][1000]['defects'] for r in all_results[channel_release] 
                  if 1000 in r['data']]
        tau_loc_vals = [r['data'][1000]['tau_localization_index'] for r in all_results[channel_release] 
                        if 1000 in r['data']]
        
        if n_vals:
            print(f"N={np.mean(n_vals):.1f}±{np.std(n_vals):.1f}, tau_loc={np.mean(tau_loc_vals):.3f} ({time.time()-t0:.0f}s)")
        else:
            print("INCOMPLETE")
    
    elapsed = time.time() - start_time
    print()
    print(f"Total time: {elapsed:.1f}s")
    print()
    
    # Full results
    print("=" * 80)
    print("  RESULTS AT T=1000")
    print("=" * 80)
    print()
    
    print(f"{'Config':>15} | {'N_mean':>8} | {'N_std':>7} | {'tau_loc':>8} | {'ch_released':>12}")
    print("-" * 65)
    
    baseline_n = None
    baseline_std = None
    baseline_loc = None
    
    for channel_release in channel_strengths:
        results = all_results[channel_release]
        t1000_data = [r['data'][1000] for r in results if 1000 in r['data']]
        
        if t1000_data:
            n_vals = [d['defects'] for d in t1000_data]
            tau_loc_vals = [d['tau_localization_index'] for d in t1000_data]
            ch_released = [d['total_channel_released'] for d in t1000_data]
            
            n_mean = np.mean(n_vals)
            n_std = np.std(n_vals)
            tau_loc_mean = np.mean(tau_loc_vals)
            ch_mean = np.mean(ch_released)
            
            if channel_release == 0:
                baseline_n = n_mean
                baseline_std = n_std
                baseline_loc = tau_loc_mean
            
            name = "v1.1 baseline" if channel_release == 0 else f"v1.1 + ch={channel_release}"
            print(f"{name:>15} | {n_mean:>8.1f} | {n_std:>7.1f} | {tau_loc_mean:>8.3f} | {ch_mean:>12.0f}")
    
    print()
    
    # Decision analysis
    print("=" * 80)
    print("  DECISION ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"Baseline (v1.1): N={baseline_n:.1f}±{baseline_std:.1f}, tau_loc={baseline_loc:.3f}")
    print()
    
    winners = []
    
    for channel_release in channel_strengths[1:]:  # Skip baseline
        results = all_results[channel_release]
        t1000_data = [r['data'][1000] for r in results if 1000 in r['data']]
        
        if t1000_data:
            n_vals = [d['defects'] for d in t1000_data]
            tau_loc_vals = [d['tau_localization_index'] for d in t1000_data]
            
            n_mean = np.mean(n_vals)
            n_std = np.std(n_vals)
            tau_loc_mean = np.mean(tau_loc_vals)
            
            # Decision criteria
            n_comparable = n_mean >= baseline_n * 0.9
            std_improved = n_std <= baseline_std
            loc_ok = tau_loc_mean <= baseline_loc * 1.05
            
            status = []
            if n_mean > baseline_n * 1.1:
                status.append("N↑")
            elif n_comparable:
                status.append("N≈")
            else:
                status.append("N↓")
            
            if std_improved:
                status.append("std↓")
            else:
                status.append("std↑")
            
            if loc_ok:
                status.append("loc✓")
            else:
                status.append("loc↑")
            
            status_str = " ".join(status)
            
            # Overall verdict
            if n_comparable and std_improved and loc_ok:
                verdict = "✓ ACCEPT"
                winners.append(channel_release)
            elif n_mean > baseline_n and tau_loc_mean > baseline_loc:
                verdict = "⚠ RISKY OVERDRIVE"
            else:
                verdict = "✗ REJECT"
            
            print(f"ch={channel_release}: {status_str} → {verdict}")
    
    print()
    
    # Final decision
    print("=" * 80)
    print("  FINAL DECISION")
    print("=" * 80)
    print()
    
    if winners:
        best = winners[0]  # Prefer lower strength
        print(f"✓ CHANNEL RELEASE ACCEPTED at strength {best}")
        print(f"  Secondary branch adds to v1.1 baseline")
    else:
        print("✗ NO CHANNEL RELEASE CONFIGURATION IMPROVES STABILITY")
        print("  v1.1 baseline remains optimal")
    
    # Save results
    output = {
        'test': 'channel_release_to_tau',
        'date': 'December 2025',
        'baseline': {
            'damping_to_tau': OPTIMAL_DAMPING_TO_TAU,
            'tau_cap': REGULATED_RECOVERY_TAU_CAP
        },
        'sweep': channel_strengths,
        'results': {str(c): all_results[c] for c in channel_strengths},
        'winners': winners
    }
    
    with open('/app/backend/qmrt_topology/papers/channel_release_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/channel_release_results.json")


if __name__ == "__main__":
    main()
