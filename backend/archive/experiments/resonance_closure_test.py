"""
Resonance Closure Test
======================

PURPOSE: Quick sweep to determine if weak resonance improves v1.1.
If no setting beats v1.1 while keeping N_std <= 7.35, close resonance branch.

BASELINE: Regulated Recovery v1.1
- damping_to_tau = 0.20
- tau_cap = 1.8

SWEEP:
- resonance_to_tau = [0.000, 0.0025, 0.005, 0.0075, 0.010]
- T = 1000, seeds = 3

DECISION RULE:
- If resonance improves N_mean while N_std <= 7.35 → v1.2 candidate
- Otherwise → close resonance branch
"""

import numpy as np
from scipy.ndimage import label
import time

# Locked v1.1 configuration
REGULATED_RECOVERY_TAU_CAP = 1.8
OPTIMAL_DAMPING_TO_TAU = 0.20


class ResonanceClosureSimulator:
    """Simulator with optional resonance coupling for closure test."""
    
    def __init__(self, size=32, dt=0.12, seed=None,
                 damping_to_tau=0.20, tau_cap=1.8, resonance_to_tau=0.0):
        
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.T = 0.0
        self.step_count = 0
        
        # Configuration
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        self.resonance_to_tau = resonance_to_tau
        
        # Initialize fields
        self.psi_r = np.random.randn(size, size, size) * 0.1 + 1.0
        self.psi_i = np.random.randn(size, size, size) * 0.05
        self.psi_r_dot = np.random.randn(size, size, size) * 0.02
        self.psi_i_dot = np.random.randn(size, size, size) * 0.02
        
        self.tau = np.ones((size, size, size))
        self.channel = np.zeros((size, size, size))
        
        # Standard coupling gradient
        x = np.linspace(0, 1, size)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        center_dist = np.sqrt((X-0.5)**2 + (Y-0.5)**2 + (Z-0.5)**2)
        self.coupling = 0.5 - 0.3 * center_dist
        
        # Physics parameters
        self.c_0_sq = 4.0
        self.gamma = 0.007
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.remnant_decay = 0.995
        self.channel_growth = 0.001
        self.channel_decay = 0.999
        
        # Seed initial defects
        self._seed_defects(n_defects=8)
    
    def _seed_defects(self, n_defects=8):
        margin = self.size // 4
        for _ in range(n_defects):
            cx = np.random.randint(margin, self.size - margin)
            cy = np.random.randint(margin, self.size - margin)
            cz = np.random.randint(margin, self.size - margin)
            
            x, y, z = np.meshgrid(
                np.arange(self.size), np.arange(self.size), np.arange(self.size),
                indexing='ij'
            )
            r = np.sqrt((x-cx)**2 + (y-cy)**2 + (z-cz)**2) + 0.1
            
            chirality = np.random.choice([-1, 1])
            theta = np.arctan2(y - cy, x - cx)
            
            amp = 1.5 * np.exp(-r**2 / 8)
            self.psi_r += amp * np.cos(chirality * theta)
            self.psi_i += amp * np.sin(chirality * theta)
    
    def detect_defects(self):
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        dx = np.diff(phase, axis=0, append=phase[:1, :, :])
        dy = np.diff(phase, axis=1, append=phase[:, :1, :])
        dz = np.diff(phase, axis=2, append=phase[:, :, :1])
        
        dx = np.where(dx > np.pi, dx - 2*np.pi, dx)
        dx = np.where(dx < -np.pi, dx + 2*np.pi, dx)
        dy = np.where(dy > np.pi, dy - 2*np.pi, dy)
        dy = np.where(dy < -np.pi, dy + 2*np.pi, dy)
        dz = np.where(dz > np.pi, dz - 2*np.pi, dz)
        dz = np.where(dz < -np.pi, dz + 2*np.pi, dz)
        
        curl_mag = np.sqrt(
            (np.roll(dz, -1, 1) - dz)**2 +
            (np.roll(dx, -1, 2) - dx)**2 +
            (np.roll(dy, -1, 0) - dy)**2
        )
        
        threshold = 1.5
        defect_mask = curl_mag > threshold
        labeled, n_defects = label(defect_mask)
        
        return n_defects
    
    def step(self):
        self.step_count += 1
        self.T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # Kinetic and damped energy
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        # τ dynamics
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # Damping → τ (v1.1 baseline)
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
        
        # Resonance → τ (optional weak coupling)
        if self.resonance_to_tau > 0:
            # Resonance from local frequency coherence
            phase = np.arctan2(self.psi_i, self.psi_r)
            phase_rate = (self.psi_r * self.psi_i_dot - self.psi_i * self.psi_r_dot) / (self.psi_r**2 + self.psi_i**2 + 1e-10)
            mean_rate = np.mean(phase_rate)
            resonance = np.exp(-0.5 * ((phase_rate - mean_rate) / 0.1)**2)
            self.tau += self.resonance_to_tau * resonance
        
        # Enforce τ cap
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Wave propagation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        return float(np.mean(energy))


def run_single_config(resonance_to_tau, seed, T_max=1000):
    """Run single configuration and return results."""
    
    sim = ResonanceClosureSimulator(
        size=32, dt=0.12, seed=seed,
        damping_to_tau=OPTIMAL_DAMPING_TO_TAU,
        tau_cap=REGULATED_RECOVERY_TAU_CAP,
        resonance_to_tau=resonance_to_tau
    )
    
    steps_per_T = int(1.0 / sim.dt)
    
    # Run to T_max
    while sim.T < T_max:
        sim.step()
    
    # Final measurement
    N_final = sim.detect_defects()
    tau_loc = float(np.max(sim.tau) / np.mean(sim.tau))
    
    return {
        'N_final': N_final,
        'tau_loc': tau_loc,
        'T': sim.T
    }


def run_resonance_sweep_chunk(resonance_values, seeds):
    """Run a chunk of the sweep."""
    results = {}
    
    for res in resonance_values:
        results[res] = []
        for seed in seeds:
            print(f"  res={res:.4f}, seed={seed}...", end=" ", flush=True)
            t0 = time.time()
            r = run_single_config(res, seed, T_max=1000)
            print(f"N={r['N_final']}, tau_loc={r['tau_loc']:.2f} ({time.time()-t0:.1f}s)")
            results[res].append(r)
    
    return results


def analyze_results(all_results):
    """Analyze sweep results and make decision."""
    
    print("\n" + "=" * 70)
    print("  RESONANCE CLOSURE ANALYSIS")
    print("=" * 70)
    print()
    
    stats = {}
    for res, runs in all_results.items():
        N_vals = [r['N_final'] for r in runs]
        stats[res] = {
            'N_mean': np.mean(N_vals),
            'N_std': np.std(N_vals),
            'N_vals': N_vals
        }
    
    # Reference: v1.1 (res=0.0)
    baseline = stats.get(0.0, stats[list(stats.keys())[0]])
    baseline_N = baseline['N_mean']
    baseline_std = baseline['N_std']
    
    print(f"{'res':>10} | {'N_mean':>8} | {'N_std':>8} | {'vs v1.1':>10} | {'Decision':>15}")
    print("-" * 65)
    
    best_candidate = None
    
    for res in sorted(stats.keys()):
        s = stats[res]
        delta = ((s['N_mean'] - baseline_N) / baseline_N * 100) if baseline_N > 0 else 0
        
        # Decision logic
        if res == 0.0:
            decision = "BASELINE (v1.1)"
        elif s['N_std'] > 7.35:
            decision = "REJECT (variance)"
        elif s['N_mean'] > baseline_N:
            decision = "v1.2 CANDIDATE"
            if best_candidate is None or s['N_mean'] > best_candidate[1]:
                best_candidate = (res, s['N_mean'], s['N_std'])
        else:
            decision = "no improvement"
        
        print(f"{res:>10.4f} | {s['N_mean']:>8.1f} | {s['N_std']:>8.2f} | {delta:>+9.1f}% | {decision:>15}")
    
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    print()
    
    if best_candidate:
        print(f"v1.2 CANDIDATE FOUND: res={best_candidate[0]:.4f}")
        print(f"  N_mean={best_candidate[1]:.1f}, N_std={best_candidate[2]:.2f}")
        print()
        print("RECOMMENDATION: Mark as potential v1.2, but DO NOT delay Lorentz tests.")
    else:
        print("NO IMPROVEMENT FROM RESONANCE")
        print()
        print("RECOMMENDATION: CLOSE RESONANCE BRANCH. Proceed with Lorentz tests.")
    
    return stats, best_candidate


if __name__ == "__main__":
    print("=" * 70)
    print("  RESONANCE CLOSURE TEST")
    print("=" * 70)
    print()
    print("Baseline: Regulated Recovery v1.1")
    print(f"  damping_to_tau = {OPTIMAL_DAMPING_TO_TAU}")
    print(f"  tau_cap = {REGULATED_RECOVERY_TAU_CAP}")
    print()
    print("Sweep: resonance_to_tau = [0.0, 0.0025, 0.005, 0.0075, 0.010]")
    print("       T=1000, seeds=3")
    print()
    
    # Run in chunks to avoid timeout
    resonance_values = [0.0, 0.0025, 0.005, 0.0075, 0.010]
    seeds = [42, 123, 456]
    
    print("Running sweep (chunked for timeout safety)...")
    print()
    
    all_results = run_resonance_sweep_chunk(resonance_values, seeds)
    
    stats, best_candidate = analyze_results(all_results)
    
    # Save results
    import json
    output = {
        'test': 'resonance_closure',
        'baseline': {'damping_to_tau': OPTIMAL_DAMPING_TO_TAU, 'tau_cap': REGULATED_RECOVERY_TAU_CAP},
        'sweep': {'resonance_values': resonance_values, 'seeds': seeds, 'T': 1000},
        'results': {str(k): v for k, v in all_results.items()},
        'stats': {str(k): {'N_mean': v['N_mean'], 'N_std': v['N_std']} for k, v in stats.items()},
        'verdict': 'v1.2_candidate' if best_candidate else 'close_resonance',
        'best_candidate': best_candidate
    }
    
    with open('/app/backend/qmrt_topology/papers/RESONANCE_CLOSURE_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/RESONANCE_CLOSURE_RESULTS.json")
