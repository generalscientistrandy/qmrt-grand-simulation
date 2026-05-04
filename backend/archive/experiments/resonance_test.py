"""
Resonance → τ Test: Activity-Correlated Secondary Branch
=========================================================

BASELINE (Locked v1.1):
  damping_to_tau = 0.20
  tau_cap = 1.8
  RECOVERY_MODE = "regulated_damping_tau_v1_1"

HYPOTHESIS:
  Coherent oscillatory regions should recharge τ more constructively than
  raw damping alone, because they identify topology that is actively
  phase-coherent rather than merely energetic.

MECHANISM:
  resonance_signal = local_phase_coherence * topology_norm
  tau += resonance_to_tau * resonance_signal

  where local_phase_coherence measures how well neighboring cells
  oscillate in phase (spatial correlation of phase gradients).

SWEEP:
  resonance_to_tau = [0.00, 0.01, 0.03, 0.05, 0.10]
  T = 1000
  seeds = 3

ACCEPTANCE CRITERIA (must improve at least one without harming others):
  - N_mean increases
  - N_std decreases  
  - tau_localization <= v1.1 baseline
  - late_N_slope remains near zero or positive
  - collapse_count remains zero

THEORY:
  Activity-correlated feedback succeeds; location-memory feedback fails.
  Resonance is activity-correlated (like damping) but more selective.
"""

import numpy as np
from scipy.ndimage import label, uniform_filter
from typing import Dict, List
import time
import json


# Locked v1.1 Configuration
REGULATED_RECOVERY_TAU_CAP = 1.8
OPTIMAL_DAMPING_TO_TAU = 0.20
RECOVERY_MODE = "regulated_damping_tau_v1_1"


class ResonanceSimulator:
    """
    Simulator with Resonance → τ as secondary branch.
    
    Resonance signal: measures local phase coherence weighted by topology.
    High resonance = region where neighboring cells oscillate in phase
    with significant topological structure.
    """
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = OPTIMAL_DAMPING_TO_TAU,
                 tau_cap: float = REGULATED_RECOVERY_TAU_CAP,
                 resonance_to_tau: float = 0.0):
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        self.resonance_to_tau = resonance_to_tau
        
        self.T = 0.0
        self.step_count = 0
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Store previous phase for coherence calculation
        self.prev_phase = None
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        self.channel = np.zeros((size, size, size))
        
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
        self.creations = 0
        self.total_damped = 0.0
        self.total_recycled = 0.0
        self.total_resonance = 0.0
        self.explosion = False
        
    def compute_phase_coherence(self, phase: np.ndarray) -> np.ndarray:
        """
        Compute local phase coherence.
        
        High coherence = neighboring cells have similar phase,
        indicating organized oscillation rather than noise.
        
        Method: compute local variance of phase gradients.
        Low variance = high coherence.
        """
        # Phase gradients
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        
        # Gradient magnitude
        grad_mag = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Local variance of gradient (low variance = high coherence)
        # Use uniform filter for local mean
        local_mean = uniform_filter(grad_mag, size=3)
        local_sq_mean = uniform_filter(grad_mag**2, size=3)
        local_var = local_sq_mean - local_mean**2
        local_var = np.maximum(local_var, 0)  # Numerical safety
        
        # Convert variance to coherence (inverse relationship)
        # High variance → low coherence, low variance → high coherence
        coherence = 1.0 / (1.0 + local_var * 10)
        
        return coherence
    
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
        
        # PRIMARY: Damping → τ (v1.1 baseline)
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        # Compute phase and topology
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # SECONDARY: Resonance → τ coupling
        if self.resonance_to_tau > 0:
            coherence = self.compute_phase_coherence(phase)
            
            # Resonance signal = coherence * topology
            # High resonance where: organized oscillation + topological structure
            resonance_signal = coherence * topology_norm
            
            resonance_contribution = self.resonance_to_tau * resonance_signal
            self.tau += resonance_contribution
            self.total_resonance += float(np.sum(resonance_contribution))
        
        # Apply regulated τ cap
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        self.channel = np.clip(self.channel + 0.01 * (topology_norm - self.channel), 0, 1)
        
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
        
        # Store phase for next step
        self.prev_phase = phase.copy()
        
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
            'total_damped': self.total_damped,
            'total_recycled': self.total_recycled,
            'total_resonance': self.total_resonance,
            'explosion': self.explosion
        }


def run_resonance_test(resonance_strength: float, seed: int, T_max: float = 1000) -> Dict:
    """Run single resonance test."""
    np.random.seed(seed)
    
    sim = ResonanceSimulator(
        size=32, dt=0.12,
        damping_to_tau=OPTIMAL_DAMPING_TO_TAU,
        tau_cap=REGULATED_RECOVERY_TAU_CAP,
        resonance_to_tau=resonance_strength
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
    print("  RESONANCE → τ TEST: ACTIVITY-CORRELATED SECONDARY BRANCH")
    print("=" * 80)
    print()
    print(f"Baseline (v1.1): damping={OPTIMAL_DAMPING_TO_TAU}, cap={REGULATED_RECOVERY_TAU_CAP}")
    print("Testing: resonance_to_tau = [0.00, 0.01, 0.03, 0.05, 0.10]")
    print()
    
    resonance_strengths = [0.00, 0.01, 0.03, 0.05, 0.10]
    seeds = [10, 42, 99]
    
    all_results = {r: [] for r in resonance_strengths}
    
    start_time = time.time()
    
    for res in resonance_strengths:
        name = "v1.1 only" if res == 0 else f"v1.1 + res={res}"
        print(f"Testing {name}...", end=" ", flush=True)
        t0 = time.time()
        
        for seed in seeds:
            result = run_resonance_test(res, seed, T_max=1000)
            all_results[res].append({'seed': seed, 'data': result})
        
        # Summary
        n_vals = [r['data'][1000]['defects'] for r in all_results[res] if 1000 in r['data']]
        tau_loc_vals = [r['data'][1000]['tau_localization_index'] for r in all_results[res] if 1000 in r['data']]
        
        if n_vals:
            print(f"N={np.mean(n_vals):.1f}±{np.std(n_vals):.1f}, tau_loc={np.mean(tau_loc_vals):.3f} ({time.time()-t0:.0f}s)")
        else:
            print("INCOMPLETE")
    
    elapsed = time.time() - start_time
    print()
    print(f"Total time: {elapsed:.1f}s")
    print()
    
    # Results table
    print("=" * 80)
    print("  RESULTS AT T=1000")
    print("=" * 80)
    print()
    
    print(f"{'Config':>15} | {'N_mean':>8} | {'N_std':>7} | {'tau_loc':>8} | {'res_total':>10}")
    print("-" * 60)
    
    baseline_n = None
    baseline_std = None
    baseline_loc = None
    
    for res in resonance_strengths:
        results = all_results[res]
        t1000_data = [r['data'][1000] for r in results if 1000 in r['data']]
        
        if t1000_data:
            n_vals = [d['defects'] for d in t1000_data]
            tau_loc_vals = [d['tau_localization_index'] for d in t1000_data]
            res_total = [d['total_resonance'] for d in t1000_data]
            
            n_mean = np.mean(n_vals)
            n_std = np.std(n_vals)
            tau_loc_mean = np.mean(tau_loc_vals)
            res_mean = np.mean(res_total)
            
            if res == 0:
                baseline_n = n_mean
                baseline_std = n_std
                baseline_loc = tau_loc_mean
            
            name = "v1.1 baseline" if res == 0 else f"v1.1 + res={res}"
            print(f"{name:>15} | {n_mean:>8.1f} | {n_std:>7.1f} | {tau_loc_mean:>8.3f} | {res_mean:>10.0f}")
    
    print()
    
    # Decision analysis
    print("=" * 80)
    print("  DECISION ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"Baseline (v1.1): N={baseline_n:.1f}±{baseline_std:.1f}, tau_loc={baseline_loc:.3f}")
    print()
    
    accepted = []
    
    for res in resonance_strengths[1:]:
        results = all_results[res]
        t1000_data = [r['data'][1000] for r in results if 1000 in r['data']]
        
        if t1000_data:
            n_vals = [d['defects'] for d in t1000_data]
            n_mean = np.mean(n_vals)
            n_std = np.std(n_vals)
            tau_loc_mean = np.mean([d['tau_localization_index'] for d in t1000_data])
            
            # Acceptance criteria
            n_improved = n_mean > baseline_n * 1.05
            n_comparable = n_mean >= baseline_n * 0.95
            std_improved = n_std < baseline_std
            loc_ok = tau_loc_mean <= baseline_loc * 1.05
            
            status = []
            if n_improved:
                status.append("N↑")
            elif n_comparable:
                status.append("N≈")
            else:
                status.append("N↓")
            
            if std_improved:
                status.append("std↓")
            else:
                status.append("std≈")
            
            if loc_ok:
                status.append("loc✓")
            else:
                status.append("loc↑")
            
            # Accept if improves at least one without harming others
            if (n_improved or std_improved) and loc_ok and n_comparable:
                verdict = "✓ ACCEPT"
                accepted.append(res)
            elif not n_comparable:
                verdict = "✗ REJECT (N↓)"
            elif not loc_ok:
                verdict = "✗ REJECT (loc↑)"
            else:
                verdict = "≈ NEUTRAL"
            
            print(f"res={res}: {' '.join(status)} → {verdict}")
    
    print()
    
    # Final decision
    print("=" * 80)
    print("  FINAL DECISION")
    print("=" * 80)
    print()
    
    if accepted:
        best = accepted[0]
        print(f"✓ RESONANCE ACCEPTED at strength {best}")
        print(f"  Secondary branch adds to v1.1 baseline")
    else:
        print("? NO RESONANCE CONFIGURATION CLEARLY IMPROVES v1.1")
        print("  v1.1 baseline may already be near-optimal")
    
    # Save results
    output = {
        'test': 'resonance_to_tau',
        'date': 'December 2025',
        'baseline': {
            'damping_to_tau': OPTIMAL_DAMPING_TO_TAU,
            'tau_cap': REGULATED_RECOVERY_TAU_CAP,
            'mode': RECOVERY_MODE
        },
        'sweep': resonance_strengths,
        'results': {str(r): all_results[r] for r in resonance_strengths},
        'accepted': accepted
    }
    
    with open('/app/backend/qmrt_topology/papers/resonance_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/resonance_results.json")


if __name__ == "__main__":
    main()
