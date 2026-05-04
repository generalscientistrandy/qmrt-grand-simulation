"""
Time-Accelerated Simulation Framework
=====================================

Key insight: wall-clock time ≠ simulation time
We want more simulation time per wall-clock second.

This script:
1. Tests dt stability bounds
2. Implements accelerated exploration mode
3. Re-runs remnant comparison at proper simulation-time checkpoints
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import Dict, List, Tuple
import time


class AcceleratedSimulator:
    """
    Simulator with simulation-time tracking and configurable dt.
    """
    
    def __init__(self, size: int = 40,
                 dt: float = 0.04,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 remnant_fraction: float = 0.0):
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.remnant_fraction = remnant_fraction
        
        # Simulation time tracking
        self.T = 0.0  # Internal simulation time
        self.step_count = 0
        
        # Fields
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
        
        # Coupling field
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
        # Tracking
        self.creations = 0
        self.max_tau_seen = 1.0
        self.energy_history = []
        
    def inject_vortex(self, cx: int, cy: int, cz: int, ch: int = 1):
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / 18)
        
        vortex = np.tanh(r / 2.5) * np.exp(1j * ch * theta)
        current = self.psi_r + 1j * self.psi_i
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_structure(self, n_pairs: int = 10):
        center = self.size // 2
        for _ in range(n_pairs):
            a1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.17)
            cx1 = int(np.clip(center + r1 * np.cos(a1), 4, self.size - 4))
            cy1 = int(np.clip(center + r1 * np.sin(a1), 4, self.size - 4))
            
            a2 = a1 + np.random.uniform(0.5, 1.5)
            r2 = np.random.uniform(2, self.size * 0.17)
            cx2 = int(np.clip(center + r2 * np.cos(a2), 4, self.size - 4))
            cy2 = int(np.clip(center + r2 * np.sin(a2), 4, self.size - 4))
            
            self.inject_vortex(cx1, cy1, center, +1)
            self.inject_vortex(cx2, cy2, center, -1)
    
    def select_location(self) -> Tuple[int, int, int]:
        center = self.size // 2
        
        if np.random.random() < self.remnant_fraction and np.sum(self.remnant) > 0.1:
            weights = 0.01 + self.remnant
            x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                                 np.arange(self.size), indexing='ij')
            r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
            weights = weights * (r < self.size * 0.30)
            ws = np.sum(weights)
            if ws > 1e-10:
                wf = weights.flatten() / ws
                idx = np.random.choice(len(wf), p=wf)
                return (int(idx // (self.size**2)), 
                        int((idx % (self.size**2)) // self.size), 
                        int(idx % self.size))
        
        # Random
        angle = np.random.uniform(0, 2*np.pi)
        r = np.random.uniform(2, self.size * 0.17)
        return (int(np.clip(center + r * np.cos(angle), 4, self.size - 4)),
                int(np.clip(center + r * np.sin(angle), 4, self.size - 4)),
                center)
    
    def attempt_creation(self):
        high_tau = self.tau > self.tau_creation_threshold
        if not np.any(high_tau):
            return 0
        
        candidates = np.where(high_tau)
        n = len(candidates[0])
        if n == 0:
            return 0
        
        indices = np.random.choice(n, min(30, n), replace=False)
        
        for idx in indices:
            local_tau = self.tau[candidates[0][idx], candidates[1][idx], candidates[2][idx]]
            prob = (local_tau - self.tau_creation_threshold) * self.creation_rate
            
            if np.random.random() < prob:
                cx, cy, cz = self.select_location()
                a2 = np.random.uniform(0, 2*np.pi)
                d = np.random.uniform(2, 4)
                cx2 = int(np.clip(cx + d * np.cos(a2), 2, self.size - 2))
                cy2 = int(np.clip(cy + d * np.sin(a2), 2, self.size - 2))
                
                self.inject_vortex(cx, cy, cz, +1)
                self.inject_vortex(cx2, cy2, cz, -1)
                self.creations += 1
                return 1
        return 0
    
    def step(self):
        """Single evolution step. Updates T by dt."""
        self.step_count += 1
        self.T += self.dt
        
        self.attempt_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # τ dynamics
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        self.max_tau_seen = max(self.max_tau_seen, float(np.max(self.tau)))
        
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Topology and channel
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = gaussian_filter(np.sqrt(grad_x**2 + grad_y**2 + grad_z**2), sigma=1.0)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel = np.clip(self.channel + 0.01 * (topology_norm - self.channel), 0, 1)
        self.remnant = np.clip(self.remnant * 0.999 + 0.02 * topology_norm, 0, 1)
        
        # Protection
        protection = topology_norm * self.channel
        radial_r, radial_i = self.psi_r / amp, self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        # Update
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        # Track energy for stability check
        total_energy = float(np.mean(energy))
        self.energy_history.append(total_energy)
        
        return total_energy
    
    def detect_defects(self) -> int:
        """Detect defects (expensive - call sparingly)."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < 0.4)
        return sum(1 for i in range(1, n + 1) if np.sum(labeled == i) >= 3)
    
    def check_stability(self) -> Dict:
        """Check if simulation is stable."""
        if len(self.energy_history) < 10:
            return {'stable': True, 'reason': 'too_early'}
        
        recent = self.energy_history[-10:]
        
        # Check for NaN/Inf
        if any(np.isnan(e) or np.isinf(e) for e in recent):
            return {'stable': False, 'reason': 'nan_or_inf'}
        
        # Check for runaway growth
        if recent[-1] > recent[0] * 100:
            return {'stable': False, 'reason': 'runaway_growth'}
        
        # Check for collapse
        if recent[-1] < recent[0] * 0.001:
            return {'stable': False, 'reason': 'collapse'}
        
        return {'stable': True, 'reason': 'ok'}


def test_dt_stability():
    """Test which dt values are numerically stable."""
    print("=" * 70)
    print("  DT STABILITY TEST")
    print("=" * 70)
    print()
    print("Testing CFL-like stability bounds for different dt values.")
    print("c_eff_max ≈ sqrt(8) ≈ 2.83 when tau→2.0")
    print("Theoretical upper bound: dt < 1/(sqrt(3)*c_eff) ≈ 0.20")
    print()
    
    dt_values = [0.04, 0.06, 0.08, 0.10, 0.12, 0.15]
    results = []
    
    for dt in dt_values:
        np.random.seed(42)
        sim = AcceleratedSimulator(size=36, dt=dt, creation_rate=0.15, remnant_fraction=0.0)
        sim.psi_r += 0.03 * np.random.randn(36, 36, 36)
        sim.psi_i += 0.03 * np.random.randn(36, 36, 36)
        sim.seed_structure(10)
        
        # Run for fixed simulation time T=20
        target_T = 20.0
        steps_needed = int(target_T / dt)
        
        stable = True
        final_energy = 0
        max_tau = 1.0
        
        for _ in range(steps_needed):
            energy = sim.step()
            stability = sim.check_stability()
            if not stability['stable']:
                stable = False
                break
            final_energy = energy
            max_tau = sim.max_tau_seen
        
        results.append({
            'dt': dt,
            'stable': stable,
            'steps': steps_needed,
            'T_reached': sim.T,
            'final_energy': final_energy,
            'max_tau': max_tau
        })
        
        status = "✓ STABLE" if stable else "✗ UNSTABLE"
        print(f"dt={dt:.2f}: {status}, steps={steps_needed}, T={sim.T:.1f}, E={final_energy:.2f}")
    
    # Find safe maximum dt
    safe_dts = [r['dt'] for r in results if r['stable']]
    max_safe_dt = max(safe_dts) if safe_dts else 0.04
    
    print()
    print(f"Maximum safe dt: {max_safe_dt}")
    print()
    
    return max_safe_dt, results


def run_accelerated_comparison(dt: float = 0.08):
    """
    Run remnant vs random comparison at proper simulation-time checkpoints.
    
    Checkpoints are at equal T values, not equal step counts.
    """
    print("=" * 70)
    print(f"  ACCELERATED REMNANT COMPARISON (dt={dt})")
    print("=" * 70)
    print()
    print("Comparing at simulation-time checkpoints T = 10, 25, 50, 100, 200")
    print()
    
    # Simulation time checkpoints
    T_checkpoints = [10, 25, 50, 100, 200]
    
    strategies = [
        (0.0, "Random"),
        (0.10, "10%Mem"),
        (0.25, "25%Mem"),
    ]
    
    seeds = [10, 42, 99]
    
    # Results: {strategy: {T: [n_defects per seed]}}
    results = {name: {T: [] for T in T_checkpoints} for _, name in strategies}
    remnant_accumulation = {name: {T: [] for T in T_checkpoints} for _, name in strategies}
    
    for frac, name in strategies:
        print(f"{name}:")
        
        for seed in seeds:
            np.random.seed(seed)
            sim = AcceleratedSimulator(
                size=36, dt=dt, 
                creation_rate=0.15, 
                remnant_fraction=frac
            )
            sim.psi_r += 0.03 * np.random.randn(36, 36, 36)
            sim.psi_i += 0.03 * np.random.randn(36, 36, 36)
            sim.seed_structure(10)
            
            # Run to each checkpoint
            checkpoint_idx = 0
            while checkpoint_idx < len(T_checkpoints) and sim.T < T_checkpoints[-1] + dt:
                sim.step()
                
                # Check if we've reached a checkpoint
                while (checkpoint_idx < len(T_checkpoints) and 
                       sim.T >= T_checkpoints[checkpoint_idx]):
                    T = T_checkpoints[checkpoint_idx]
                    n = sim.detect_defects()
                    results[name][T].append(n)
                    remnant_accumulation[name][T].append(float(np.mean(sim.remnant)))
                    checkpoint_idx += 1
        
        # Print summary for this strategy
        for T in T_checkpoints:
            if results[name][T]:
                mean_n = np.mean(results[name][T])
                mean_r = np.mean(remnant_accumulation[name][T])
                print(f"  T={T:3}: N={mean_n:.1f}, remnant={mean_r:.4f}")
        print()
    
    # Comparison table
    print("=" * 70)
    print("  COMPARISON: N_defects at each simulation time T")
    print("=" * 70)
    print()
    print(f"{'T':>6} | {'Random':>8} | {'10%Mem':>8} | {'25%Mem':>8} | {'10% vs R':>10} | {'25% vs R':>10}")
    print("-" * 70)
    
    for T in T_checkpoints:
        rand_n = np.mean(results['Random'][T]) if results['Random'][T] else 0
        mem10_n = np.mean(results['10%Mem'][T]) if results['10%Mem'][T] else 0
        mem25_n = np.mean(results['25%Mem'][T]) if results['25%Mem'][T] else 0
        
        delta10 = ((mem10_n / rand_n) - 1) * 100 if rand_n > 0 else 0
        delta25 = ((mem25_n / rand_n) - 1) * 100 if rand_n > 0 else 0
        
        print(f"{T:>6} | {rand_n:>8.1f} | {mem10_n:>8.1f} | {mem25_n:>8.1f} | "
              f"{delta10:>+9.0f}% | {delta25:>+9.0f}%")
    
    print()
    print("=" * 70)
    print("  REMNANT ACCUMULATION OVER TIME")
    print("=" * 70)
    print()
    print(f"{'T':>6} | {'Random':>10} | {'10%Mem':>10} | {'25%Mem':>10}")
    print("-" * 50)
    
    for T in T_checkpoints:
        rand_r = np.mean(remnant_accumulation['Random'][T]) if remnant_accumulation['Random'][T] else 0
        mem10_r = np.mean(remnant_accumulation['10%Mem'][T]) if remnant_accumulation['10%Mem'][T] else 0
        mem25_r = np.mean(remnant_accumulation['25%Mem'][T]) if remnant_accumulation['25%Mem'][T] else 0
        
        print(f"{T:>6} | {rand_r:>10.4f} | {mem10_r:>10.4f} | {mem25_r:>10.4f}")
    
    return results, remnant_accumulation


def main():
    print("=" * 70)
    print("  TIME-ACCELERATED SIMULATION FRAMEWORK")
    print("=" * 70)
    print()
    print("Key insight: wall-clock time ≠ simulation time")
    print("Goal: More simulation time per wall-clock second")
    print()
    
    start_time = time.time()
    
    # Step 1: Find safe maximum dt
    print("STEP 1: Testing dt stability bounds")
    print("-" * 70)
    max_safe_dt, stability_results = test_dt_stability()
    
    # Step 2: Run accelerated comparison
    print()
    print("STEP 2: Accelerated remnant comparison")
    print("-" * 70)
    
    # Use the max safe dt, or fall back to 0.08 if testing failed
    use_dt = min(max_safe_dt, 0.10)
    print(f"Using dt = {use_dt}")
    print()
    
    results, remnant_data = run_accelerated_comparison(dt=use_dt)
    
    elapsed = time.time() - start_time
    print()
    print(f"Total wall-clock time: {elapsed:.1f} seconds")
    print(f"Simulation time reached: T = 200")
    print(f"Efficiency: {200/elapsed:.1f} simulation-time units per wall-clock second")
    
    # Decision
    print()
    print("=" * 70)
    print("  DECISION")
    print("=" * 70)
    
    # Check if memory strategies show improvement at late times
    late_T = 200
    rand_late = np.mean(results['Random'][late_T]) if results['Random'][late_T] else 0
    mem10_late = np.mean(results['10%Mem'][late_T]) if results['10%Mem'][late_T] else 0
    mem25_late = np.mean(results['25%Mem'][late_T]) if results['25%Mem'][late_T] else 0
    
    if mem10_late > rand_late * 1.2 or mem25_late > rand_late * 1.2:
        print()
        print("✓ MEMORY SHOWS IMPROVEMENT AT LONG SIMULATION TIME!")
        if mem25_late > mem10_late:
            print(f"  25% Memory: N={mem25_late:.1f} vs Random N={rand_late:.1f}")
        else:
            print(f"  10% Memory: N={mem10_late:.1f} vs Random N={rand_late:.1f}")
        print()
        print("→ Remnant coupling MAY be viable at longer timescales")
    else:
        print()
        print("✗ No improvement from memory at T=200")
        print(f"  Random: {rand_late:.1f}, 10%Mem: {mem10_late:.1f}, 25%Mem: {mem25_late:.1f}")
        print()
        print("→ Remnant coupling does not help even at longer simulation times")
        print("→ Proceed to Damping → τ coupling")


if __name__ == "__main__":
    main()
