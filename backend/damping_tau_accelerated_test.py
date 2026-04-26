"""
Time-Accelerated Damping → τ Coupling Test
=============================================

HYPOTHESIS: Recycling damped energy back to τ field can close the recovery loop,
allowing self-sustaining topological organization.

MECHANISM:
  tau += damping_to_tau * damped_energy

LOOP:
  Topology → Energy → Damping → τ → Creation → Topology

TEST PARAMETERS:
  dt = 0.10 (time-accelerated)
  T checkpoints = 25, 50, 100, 200, 500
  measure_every = 50 steps
  seeds = 3 first, then 10 if promising
  
COUPLING STRENGTHS:
  damping_to_tau = 0.00 (baseline), 0.01, 0.03, 0.05, 0.10

SAFETY DIAGNOSTICS:
  tau_mean, tau_max, tau_std
  energy_total
  defect_count, creation_count
  explosion/instability flag
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import Dict, List, Tuple
import time
import json


class DampingTauAcceleratedSimulator:
    """
    Simulator with time-accelerated Damping → τ coupling.
    
    Key features:
    - dt=0.10 for faster simulation time
    - Simulation time T tracking
    - Damping energy recycling to τ
    - Full safety diagnostics
    """
    
    def __init__(self, size: int = 40,
                 dt: float = 0.10,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = 0.0):
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        
        # Simulation time tracking
        self.T = 0.0
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
        
        # Coupling field (spatial gradient)
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = size * 0.25
        
        self.coupling = np.zeros((size, size, size))
        self.coupling[r <= interior_r] = 0.7
        self.coupling[r >= interior_r + 8.0] = 0.2
        mask_t = (r > interior_r) & (r < interior_r + 8.0)
        if np.any(mask_t):
            t = (r[mask_t] - interior_r) / 8.0
            self.coupling[mask_t] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
        # Tracking
        self.creations = 0
        self.total_damped = 0.0
        self.total_recycled = 0.0
        
        # Safety tracking
        self.energy_history = []
        self.tau_history = []
        self.explosion_detected = False
        self.explosion_reason = None
        
    def inject_vortex(self, cx: int, cy: int, cz: int, chirality: int = 1):
        """Inject a vortex at the specified location."""
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
        """Seed initial vortex-antivortex pairs."""
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
            
            self.inject_vortex(cx1, cy1, center, +1)
            self.inject_vortex(cx2, cy2, center, -1)
    
    def attempt_creation(self) -> int:
        """Attempt τ-mediated vortex creation."""
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
                center = self.size // 2
                angle = np.random.uniform(0, 2*np.pi)
                r = np.random.uniform(2, self.size * 0.18)
                loc_cx = int(np.clip(center + r * np.cos(angle), 4, self.size - 4))
                loc_cy = int(np.clip(center + r * np.sin(angle), 4, self.size - 4))
                
                a2 = np.random.uniform(0, 2*np.pi)
                d = np.random.uniform(2, 4)
                cx2 = int(np.clip(loc_cx + d * np.cos(a2), 2, self.size - 2))
                cy2 = int(np.clip(loc_cy + d * np.sin(a2), 2, self.size - 2))
                
                self.inject_vortex(loc_cx, loc_cy, center, +1)
                self.inject_vortex(cx2, cy2, center, -1)
                self.creations += 1
                return 1
        return 0
    
    def step(self) -> Dict:
        """Single evolution step with full diagnostics."""
        self.step_count += 1
        self.T += self.dt
        
        created = self.attempt_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # Compute damped energy BEFORE applying damping
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        step_damped = float(np.sum(damped_energy))
        self.total_damped += step_damped
        
        # τ dynamics (standard energy response)
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # DAMPING → τ COUPLING: Recycle damped energy to τ
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        self.tau = np.clip(self.tau, 0.5, 3.0)  # Allow slightly higher ceiling for recycling
        
        # Wave dynamics
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
        topology = gaussian_filter(np.sqrt(grad_x**2 + grad_y**2 + grad_z**2), sigma=1.2)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel = np.clip(self.channel + 0.01 * (topology_norm - self.channel), 0, 1)
        
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
        
        # Safety tracking
        total_energy = float(np.mean(energy))
        tau_mean = float(np.mean(self.tau))
        tau_max = float(np.max(self.tau))
        tau_std = float(np.std(self.tau))
        
        self.energy_history.append(total_energy)
        self.tau_history.append({'mean': tau_mean, 'max': tau_max, 'std': tau_std})
        
        # Check for instability
        if np.isnan(total_energy) or np.isinf(total_energy):
            self.explosion_detected = True
            self.explosion_reason = 'nan_or_inf_energy'
        elif total_energy > 1000:
            self.explosion_detected = True
            self.explosion_reason = 'energy_explosion'
        elif tau_max > 10:
            self.explosion_detected = True
            self.explosion_reason = 'tau_explosion'
        
        return {
            'T': self.T,
            'energy': total_energy,
            'tau_mean': tau_mean,
            'tau_max': tau_max,
            'tau_std': tau_std,
            'created': created
        }
    
    def detect_defects(self) -> int:
        """Detect topological defects (expensive - call sparingly)."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < 0.4)
        return sum(1 for i in range(1, n + 1) if np.sum(labeled == i) >= 4)
    
    def get_diagnostics(self) -> Dict:
        """Get full diagnostic snapshot."""
        return {
            'T': self.T,
            'step_count': self.step_count,
            'defects': self.detect_defects(),
            'creations': self.creations,
            'tau_mean': float(np.mean(self.tau)),
            'tau_max': float(np.max(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'energy_total': float(np.mean(self.psi_r**2 + self.psi_i**2)),
            'total_damped': self.total_damped,
            'total_recycled': self.total_recycled,
            'explosion': self.explosion_detected,
            'explosion_reason': self.explosion_reason
        }


def run_single_test(seed: int, damping_to_tau: float, 
                    T_checkpoints: List[float],
                    size: int = 36,
                    measure_every: int = 50) -> Dict:
    """
    Run a single damping → τ test with simulation-time checkpoints.
    
    Args:
        seed: Random seed
        damping_to_tau: Coupling strength (0.0 = baseline)
        T_checkpoints: Simulation time checkpoints to measure
        size: Grid size (default 36 for speed)
        measure_every: Steps between defect measurements
    
    Returns:
        Dict with results at each checkpoint
    """
    np.random.seed(seed)
    
    sim = DampingTauAcceleratedSimulator(
        size=size,
        dt=0.10,
        tau_creation_threshold=1.001,
        creation_rate=0.15,
        damping_to_tau=damping_to_tau
    )
    
    # Add noise and seed
    sim.psi_r += 0.03 * np.random.randn(size, size, size)
    sim.psi_i += 0.03 * np.random.randn(size, size, size)
    sim.seed_structure(n_pairs=10)
    
    # Results at each checkpoint
    checkpoint_results = {}
    checkpoint_idx = 0
    
    max_T = max(T_checkpoints)
    
    while sim.T < max_T + sim.dt and not sim.explosion_detected:
        sim.step()
        
        # Check if we've reached a checkpoint
        while (checkpoint_idx < len(T_checkpoints) and 
               sim.T >= T_checkpoints[checkpoint_idx]):
            T = T_checkpoints[checkpoint_idx]
            diag = sim.get_diagnostics()
            checkpoint_results[T] = diag
            checkpoint_idx += 1
    
    # If explosion occurred, fill remaining checkpoints with explosion data
    if sim.explosion_detected:
        for T in T_checkpoints:
            if T not in checkpoint_results:
                checkpoint_results[T] = {
                    'T': sim.T,
                    'defects': 0,
                    'creations': sim.creations,
                    'tau_mean': float(np.mean(sim.tau)),
                    'tau_max': float(np.max(sim.tau)),
                    'tau_std': float(np.std(sim.tau)),
                    'explosion': True,
                    'explosion_reason': sim.explosion_reason
                }
    
    return checkpoint_results


def run_coupling_sweep(n_seeds: int = 3, max_T: int = 200):
    """
    Run full damping → τ coupling sweep.
    
    Parameters from user specification:
    - damping_to_tau: 0.00, 0.01, 0.03, 0.05, 0.10
    - T checkpoints: 25, 50, 100, 200 (extend to 500 if promising)
    - seeds: 3 first, then 10 if promising
    """
    print("=" * 80)
    print("  TIME-ACCELERATED DAMPING → τ COUPLING TEST")
    print("=" * 80)
    print()
    print("dt = 0.10 (time-accelerated), grid=36")
    print(f"T checkpoints up to {max_T}")
    print(f"Seeds = {n_seeds}")
    print()
    
    coupling_strengths = [0.00, 0.03, 0.05, 0.10, 0.15]  # T=500 validation sweep
    # Adaptive checkpoints based on max_T
    all_checkpoints = [25, 50, 100, 200, 500]
    T_checkpoints = [t for t in all_checkpoints if t <= max_T]
    seeds = list(range(10, 10 + n_seeds))  # [10, 11, 12] for n=3
    
    # Results structure
    all_results = {
        coupling: {T: [] for T in T_checkpoints}
        for coupling in coupling_strengths
    }
    
    start_time = time.time()
    
    for coupling in coupling_strengths:
        coupling_name = f"{coupling:.2f}" if coupling > 0 else "baseline"
        print(f"Testing damping_to_tau = {coupling_name}...", end=" ", flush=True)
        seed_start = time.time()
        
        for seed in seeds:
            results = run_single_test(seed, coupling, T_checkpoints, size=36)
            
            for T in T_checkpoints:
                if T in results:
                    all_results[coupling][T].append(results[T])
        
        # Print summary for this coupling
        seed_elapsed = time.time() - seed_start
        print(f"done ({seed_elapsed:.1f}s)")
    
    elapsed = time.time() - start_time
    print()
    print(f"Total wall-clock time: {elapsed:.1f} seconds")
    print(f"Efficiency: {500 * len(coupling_strengths) * n_seeds / elapsed:.1f} T-seeds per second")
    print()
    
    return all_results, T_checkpoints, coupling_strengths


def analyze_results(all_results: Dict, T_checkpoints: List[float], 
                    coupling_strengths: List[float]):
    """Analyze and print results."""
    
    print("=" * 80)
    print("  RESULTS: N_defects at Simulation Time Checkpoints")
    print("=" * 80)
    print()
    
    # Header
    header = f"{'T':>6} |"
    for c in coupling_strengths:
        name = "Base" if c == 0 else f"{c:.2f}"
        header += f" {name:>7} |"
    print(header)
    print("-" * len(header))
    
    # Data rows
    for T in T_checkpoints:
        row = f"{T:>6} |"
        for c in coupling_strengths:
            results = all_results[c][T]
            if results:
                # Check for explosions
                explosions = sum(1 for r in results if r.get('explosion', False))
                if explosions == len(results):
                    row += f" {'EXPLOD':>7} |"
                else:
                    mean_n = np.mean([r['defects'] for r in results 
                                      if not r.get('explosion', False)])
                    row += f" {mean_n:>7.1f} |"
            else:
                row += f" {'N/A':>7} |"
        print(row)
    
    print()
    
    # Safety diagnostics
    print("=" * 80)
    print("  SAFETY DIAGNOSTICS: τ Statistics")
    print("=" * 80)
    print()
    
    print(f"{'Coupling':>8} | {'T':>6} | {'tau_mean':>9} | {'tau_max':>9} | {'tau_std':>9} | {'Exploded':>8}")
    print("-" * 70)
    
    for c in coupling_strengths:
        for T in [100, 200, 500]:  # Focus on late times
            results = all_results[c].get(T, [])
            if results:
                tau_means = [r.get('tau_mean', 1.0) for r in results if not r.get('explosion', False)]
                tau_maxs = [r.get('tau_max', 1.0) for r in results if not r.get('explosion', False)]
                tau_stds = [r.get('tau_std', 0.0) for r in results if not r.get('explosion', False)]
                explosions = sum(1 for r in results if r.get('explosion', False))
                
                if tau_means:
                    name = "Base" if c == 0 else f"{c:.2f}"
                    print(f"{name:>8} | {T:>6} | {np.mean(tau_means):>9.4f} | "
                          f"{np.mean(tau_maxs):>9.4f} | {np.mean(tau_stds):>9.4f} | {explosions:>8}")
        print()
    
    # Analysis: Compare late-time defect counts
    print("=" * 80)
    print("  ANALYSIS: Late-Time (T=200, 500) Performance")
    print("=" * 80)
    print()
    
    late_Ts = [200, 500]  # Extended late-time analysis
    
    baseline_late = []
    for T in late_Ts:
        for r in all_results[0.0].get(T, []):
            if not r.get('explosion', False):
                baseline_late.append(r['defects'])
    
    baseline_mean = np.mean(baseline_late) if baseline_late else 0
    print(f"Baseline (damping_to_tau=0.00) mean late N: {baseline_mean:.2f}")
    print()
    
    improvements = []
    
    for c in coupling_strengths[1:]:  # Skip baseline
        recycled_late = []
        for T in late_Ts:
            for r in all_results[c].get(T, []):
                if not r.get('explosion', False):
                    recycled_late.append(r['defects'])
        
        if recycled_late:
            recycled_mean = np.mean(recycled_late)
            delta_pct = ((recycled_mean / baseline_mean) - 1) * 100 if baseline_mean > 0 else 0
            
            status = "✓" if recycled_mean > baseline_mean * 1.1 else "≈" if abs(delta_pct) < 20 else "✗"
            print(f"damping_to_tau={c:.2f}: mean late N = {recycled_mean:.2f} "
                  f"({delta_pct:+.0f}% vs baseline) {status}")
            
            improvements.append({
                'coupling': c,
                'mean_n': recycled_mean,
                'delta_pct': delta_pct
            })
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    best = max(improvements, key=lambda x: x['delta_pct']) if improvements else None
    
    if best and best['delta_pct'] > 20:
        print(f"✓ DAMPING → τ COUPLING SHOWS IMPROVEMENT!")
        print(f"  Best coupling: damping_to_tau = {best['coupling']:.2f}")
        print(f"  Improvement: +{best['delta_pct']:.0f}% defects at late times")
        print()
        print("→ Recommend extended testing with 10 seeds")
    elif best and best['delta_pct'] > 0:
        print(f"? MARGINAL IMPROVEMENT (within noise)")
        print(f"  Best coupling: damping_to_tau = {best['coupling']:.2f}")
        print(f"  Delta: +{best['delta_pct']:.0f}%")
        print()
        print("→ Recommend extended testing with more seeds to confirm")
    else:
        print("✗ NO IMPROVEMENT from damping → τ coupling")
        print()
        if baseline_mean > 0:
            print("→ Proceed to Channel release → τ coupling")
        else:
            print("→ Check baseline viability first")
    
    return improvements


def save_results(all_results: Dict, T_checkpoints: List[float], 
                 coupling_strengths: List[float], filename: str):
    """Save results to JSON."""
    
    # Convert to serializable format
    serializable = {
        'test': 'damping_tau_accelerated',
        'parameters': {
            'dt': 0.10,
            'T_checkpoints': T_checkpoints,
            'coupling_strengths': coupling_strengths
        },
        'results': {}
    }
    
    for c in coupling_strengths:
        c_key = f"{c:.2f}"
        serializable['results'][c_key] = {}
        for T in T_checkpoints:
            serializable['results'][c_key][str(T)] = all_results[c][T]
    
    with open(filename, 'w') as f:
        json.dump(serializable, f, indent=2)
    
    print(f"Results saved to: {filename}")


def main():
    print()
    print("=" * 80)
    print("  DAMPING → τ COUPLING: TIME-ACCELERATED TEST")
    print("=" * 80)
    print()
    print("HYPOTHESIS: Recycling damped energy to τ closes the recovery loop")
    print("MECHANISM: tau += damping_to_tau * gamma * (psi_dot)^2")
    print()
    print("Expected loop closure:")
    print("  Topology → Energy → Damping → τ → Creation → Topology")
    print()
    
    # Run T=500 validation with 5 seeds
    all_results, T_checkpoints, coupling_strengths = run_coupling_sweep(n_seeds=5, max_T=500)
    
    # Analyze
    improvements = analyze_results(all_results, T_checkpoints, coupling_strengths)
    
    # Save
    save_results(all_results, T_checkpoints, coupling_strengths,
                '/app/backend/qmrt_topology/papers/damping_tau_accelerated_results.json')
    
    print()
    print("=" * 80)
    print("  TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
