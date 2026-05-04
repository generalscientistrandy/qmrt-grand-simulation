"""
Damping → τ Coupling Test
==========================

HYPOTHESIS: Recycling damped energy back to τ field can close the recovery loop,
allowing self-sustaining topological organization without external injection.

MECHANISM:
- Current: Damping removes energy from the system (lost)
- New: A fraction of damped energy elevates local τ
- τ above threshold → spontaneous pair creation
- Net effect: Energy recycling rather than loss

LOOP:
  Topology → Energy → Damping → τ → Creation → Topology

SUCCESS CRITERIA:
- Damping recycling sustains at lower rate than no-recycling baseline
- OR: Higher late-stage N at equal rate

SWEEP:
- damping_to_tau: 0.0 (baseline), 0.1, 0.25, 0.5, 1.0
- rates: 0.05, 0.075, 0.10, 0.125, 0.15
- seeds: 3 (fast verification)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import Dict, Tuple
import json


class DampingTauSimulator:
    """
    Simulator with Damping → τ energy recycling.
    """
    
    def __init__(self, size: int = 40,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = 0.0):  # Fraction recycled
        
        self.size = size
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        
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
        self.remnant = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.step_count = 0
        self.t = 0.0
        self.dt = 0.04
        
        # Tracking
        self.creations = 0
        self.total_damped = 0.0
        self.total_recycled = 0.0
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        coupling[r <= interior_r] = 0.7
        coupling[r >= interior_r + 8.0] = 0.2
        mask_t = (r > interior_r) & (r < interior_r + 8.0)
        t = (r[mask_t] - interior_r) / 8.0
        coupling[mask_t] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
        return coupling
    
    def inject_vortex_at(self, cx: int, cy: int, cz: int, chirality: int = 1):
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
    
    def seed_structure(self, n_pairs: int = 12):
        center = self.size // 2
        for _ in range(n_pairs):
            angle1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.18)
            cx1 = int(np.clip(center + r1 * np.cos(angle1), 4, self.size - 4))
            cy1 = int(np.clip(center + r1 * np.sin(angle1), 4, self.size - 4))
            
            angle2 = angle1 + np.random.uniform(0.5, 1.5)
            r2 = np.random.uniform(2, self.size * 0.18)
            cx2 = int(np.clip(center + r2 * np.cos(angle2), 4, self.size - 4))
            cy2 = int(np.clip(center + r2 * np.sin(angle2), 4, self.size - 4))
            
            self.inject_vortex_at(cx1, cy1, center, +1)
            self.inject_vortex_at(cx2, cy2, center, -1)
    
    def attempt_creation(self):
        high_tau = self.tau > self.tau_creation_threshold
        if not np.any(high_tau):
            return 0
        
        candidates = np.where(high_tau)
        n = len(candidates[0])
        if n == 0:
            return 0
        
        indices = np.random.choice(n, min(40, n), replace=False)
        
        for idx in indices:
            cx, cy, cz = candidates[0][idx], candidates[1][idx], candidates[2][idx]
            local_tau = self.tau[cx, cy, cz]
            prob = (local_tau - self.tau_creation_threshold) * self.creation_rate
            
            if np.random.random() < prob:
                # Random interior location
                center = self.size // 2
                angle = np.random.uniform(0, 2*np.pi)
                r = np.random.uniform(2, self.size * 0.18)
                loc_cx = int(np.clip(center + r * np.cos(angle), 4, self.size - 4))
                loc_cy = int(np.clip(center + r * np.sin(angle), 4, self.size - 4))
                
                # Pair offset
                a2 = np.random.uniform(0, 2*np.pi)
                d = np.random.uniform(2, 4)
                cx2 = int(np.clip(loc_cx + d * np.cos(a2), 2, self.size - 2))
                cy2 = int(np.clip(loc_cy + d * np.sin(a2), 2, self.size - 2))
                
                self.inject_vortex_at(loc_cx, loc_cy, center, +1)
                self.inject_vortex_at(cx2, cy2, center, -1)
                self.creations += 1
                return 1
        return 0
    
    def step(self):
        self.step_count += 1
        self.t += self.dt
        
        self.attempt_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # Compute damped energy BEFORE applying damping
        damped_energy = self.gamma * (self.psi_r_dot**2 + self.psi_i_dot**2)
        step_damped = float(np.sum(damped_energy))
        self.total_damped += step_damped
        
        # τ dynamics
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # DAMPING → τ COUPLING: Recycle damped energy to τ
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        self.tau = np.clip(self.tau, 0.5, 2.5)
        
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = gaussian_filter(np.sqrt(grad_x**2 + grad_y**2 + grad_z**2), sigma=1.2)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel += 0.01 * (topology_norm - self.channel)
        self.channel = np.clip(self.channel, 0, 1)
        
        self.remnant += 0.02 * topology_norm
        self.remnant *= 0.999
        self.remnant = np.clip(self.remnant, 0, 1)
        
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
    
    def detect_defects(self) -> int:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < 0.4)
        return sum(1 for i in range(1, n + 1) if np.sum(labeled == i) >= 4)


def run_test(seed: int, rate: float, damping_frac: float, steps: int = 600) -> Dict:
    """Run single damping test."""
    np.random.seed(seed)
    
    sim = DampingTauSimulator(
        size=40,
        tau_creation_threshold=1.001,
        creation_rate=rate,
        damping_to_tau=damping_frac
    )
    
    sim.psi_r += 0.03 * np.random.randn(40, 40, 40)
    sim.psi_i += 0.03 * np.random.randn(40, 40, 40)
    sim.seed_structure(n_pairs=12)
    
    # Warmup
    for _ in range(100):
        sim.step()
    
    # Run
    late = []
    for step in range(steps):
        sim.step()
        if step >= steps - 150 and step % 30 == 0:
            late.append(sim.detect_defects())
    
    avg_n = float(np.mean(late)) if late else 0
    
    return {
        'avg_n': avg_n,
        'creations': sim.creations,
        'total_damped': sim.total_damped,
        'total_recycled': sim.total_recycled,
        'sustained': avg_n > 0.3
    }


def main():
    print("=" * 80)
    print("  DAMPING → τ COUPLING TEST")
    print("=" * 80)
    print()
    print("HYPOTHESIS: Recycling damped energy to τ can close the recovery loop")
    print("MECHANISM: tau += damping_to_tau * damped_energy")
    print()
    
    damping_fracs = [0.0, 0.1, 0.25, 0.5, 1.0]
    rates = [0.05, 0.075, 0.10, 0.125, 0.15]
    seeds = [10, 42, 99]
    
    frac_names = {
        0.0: "No Recycle",
        0.1: "10% Recycle",
        0.25: "25% Recycle",
        0.5: "50% Recycle",
        1.0: "100% Recycle"
    }
    
    results = []
    
    print(f"{'Damping':>12} | {'Rate':>6} | {'Sust%':>6} | {'Mean N':>7} | {'Creates':>8} | {'Recycled':>10}")
    print("-" * 70)
    
    for frac in damping_fracs:
        for rate in rates:
            seed_results = [run_test(s, rate, frac) for s in seeds]
            
            sustain_pct = sum(1 for r in seed_results if r['sustained']) / len(seeds) * 100
            mean_n = np.mean([r['avg_n'] for r in seed_results])
            mean_creates = np.mean([r['creations'] for r in seed_results])
            mean_recycled = np.mean([r['total_recycled'] for r in seed_results])
            
            results.append({
                'damping_frac': frac,
                'rate': rate,
                'sustain_pct': sustain_pct,
                'mean_n': mean_n,
                'mean_creates': mean_creates,
                'mean_recycled': mean_recycled
            })
            
            print(f"{frac_names[frac]:>12} | {rate:>6.3f} | {sustain_pct:>5.0f}% | "
                  f"{mean_n:>7.2f} | {mean_creates:>8.1f} | {mean_recycled:>10.1f}")
        print()
    
    # Analysis
    print("=" * 80)
    print("  MINIMAL SUSTAINABLE RATE BY STRATEGY")
    print("=" * 80)
    
    for frac in damping_fracs:
        frac_results = [r for r in results if r['damping_frac'] == frac]
        sustained = [r for r in frac_results if r['sustain_pct'] >= 66]  # 2/3 seeds
        if sustained:
            min_rate = min(r['rate'] for r in sustained)
            print(f"  {frac_names[frac]:>12}: rate = {min_rate:.3f}")
        else:
            print(f"  {frac_names[frac]:>12}: NO SUSTAINED CONFIG")
    
    # Decision
    print()
    print("=" * 80)
    print("  DECISION")
    print("=" * 80)
    
    baseline_min = None
    for r in results:
        if r['damping_frac'] == 0.0 and r['sustain_pct'] >= 66:
            if baseline_min is None or r['rate'] < baseline_min:
                baseline_min = r['rate']
    
    best_recycling = None
    best_rate = 999
    for frac in [0.1, 0.25, 0.5, 1.0]:
        for r in results:
            if r['damping_frac'] == frac and r['sustain_pct'] >= 66:
                if r['rate'] < best_rate:
                    best_rate = r['rate']
                    best_recycling = frac
    
    if baseline_min:
        print(f"\nBaseline (no recycling): min sustainable rate = {baseline_min}")
    else:
        print("\nBaseline: no sustained config")
    
    if best_recycling and best_rate < (baseline_min or 999):
        print(f"Best recycling: {frac_names[best_recycling]} at rate = {best_rate}")
        print(f"\n✓ DAMPING RECYCLING LOWERS THRESHOLD!")
        print(f"  Improvement: {baseline_min} → {best_rate}")
    elif best_recycling and baseline_min and best_rate == baseline_min:
        # Check quality at same rate
        print(f"\nNo threshold improvement, checking quality at rate={baseline_min}:")
        baseline_n = next((r['mean_n'] for r in results 
                          if r['damping_frac'] == 0.0 and r['rate'] == baseline_min), 0)
        for frac in [0.1, 0.25, 0.5, 1.0]:
            frac_n = next((r['mean_n'] for r in results 
                          if r['damping_frac'] == frac and r['rate'] == baseline_min), 0)
            if frac_n > baseline_n * 1.2:
                print(f"  {frac_names[frac]}: N={frac_n:.2f} vs baseline {baseline_n:.2f} (+{(frac_n/baseline_n-1)*100:.0f}%)")
    else:
        print("\n✗ No improvement from damping recycling")
    
    # Save
    output_path = '/app/backend/qmrt_topology/papers/damping_tau_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'damping_tau_coupling',
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
