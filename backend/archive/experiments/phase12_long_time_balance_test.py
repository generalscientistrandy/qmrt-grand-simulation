"""
Phase 12a: Long-Time Balance Persistence Test
===============================================

QUESTION: Does the ~50/50 balance between + and - sectors persist over
          very long runs (5000+ steps)?

WHY THIS MATTERS:
- Phase 11f found balance ~0.906 over ~1200 steps
- If balance degrades over time → statistical fluctuations accumulate
- If balance persists → robust symmetry in creation mechanism

THIS TESTS:
- Robustness of the topological dual-sector regime
- Whether the medium has a self-correcting balance mechanism
- Long-term stability of the pre-matter organization

METRICS:
- Population balance over time
- Balance variance and drift
- Any systematic trend toward imbalance
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import linregress
from typing import List, Tuple
import json


class LongTimeSimulator:
    """Simulator for extended balance persistence tests."""
    
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
        # Strictly balanced: 2 positive, 2 negative
        for chirality in [+1, +1, -1, -1]:
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
    
    def detect_signed_defects(self, threshold: float = 0.4) -> Tuple[int, int]:
        """Detect defects and return counts by sign."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        n_pos = 0
        n_neg = 0
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                cz = int(np.mean(coords[2]))
                
                local_vort = vorticity[cx, cy, cz]
                
                if local_vort > 0.05:
                    n_pos += 1
                elif local_vort < -0.05:
                    n_neg += 1
        
        return n_pos, n_neg


def run_long_time_balance_test():
    """
    Test whether population balance persists over extended simulation time.
    
    Run for 5000 steps, sampling every 100 steps = 50 measurements
    """
    print("=" * 75)
    print("  PHASE 12a: LONG-TIME BALANCE PERSISTENCE TEST")
    print("=" * 75)
    print()
    print("Question: Does the ~50/50 balance persist over 5000+ steps?")
    print()
    
    sim = LongTimeSimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Balanced initial seeding
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                chirality = 1 if (i + j) % 2 == 0 else -1
                sim.inject_vortex(center + i * 4, center + j * 4, chirality)
    
    print(f"{'Step':>5} │ {'N+':>4} {'N-':>4} {'Total':>5} │ {'Balance':>7} │ {'Imbal':>6}")
    print("-" * 55)
    
    history = []
    
    # Run for 5000 steps, sample every 100
    for step in range(5000):
        sim.step()
        
        if step % 100 == 0 and step > 0:
            n_pos, n_neg = sim.detect_signed_defects()
            n_total = n_pos + n_neg
            
            if n_total > 0:
                balance = 1 - abs(n_pos - n_neg) / n_total
                imbalance = (n_pos - n_neg) / n_total  # Signed imbalance
            else:
                balance = 0
                imbalance = 0
            
            print(f"{step:>5} │ {n_pos:>4} {n_neg:>4} {n_total:>5} │ {balance:>7.3f} │ {imbalance:>+6.3f}")
            
            history.append({
                'step': step,
                'n_pos': n_pos,
                'n_neg': n_neg,
                'n_total': n_total,
                'balance': balance,
                'imbalance': imbalance,
            })
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("LONG-TIME BALANCE ANALYSIS")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n_total'] > 20]
    
    if len(valid) >= 10:
        # Overall statistics
        balances = [h['balance'] for h in valid]
        imbalances = [h['imbalance'] for h in valid]
        steps = [h['step'] for h in valid]
        
        avg_balance = np.mean(balances)
        std_balance = np.std(balances)
        min_balance = np.min(balances)
        max_balance = np.max(balances)
        
        print(f"Balance Statistics:")
        print(f"  Average:  {avg_balance:.3f}")
        print(f"  Std Dev:  {std_balance:.3f}")
        print(f"  Range:    [{min_balance:.3f}, {max_balance:.3f}]")
        print()
        
        # Check for drift
        slope, intercept, r_value, p_value, std_err = linregress(steps, imbalances)
        
        print(f"Drift Analysis (signed imbalance vs time):")
        print(f"  Slope:    {slope:.6f} per step")
        print(f"  R²:       {r_value**2:.4f}")
        print(f"  p-value:  {p_value:.4f}")
        print()
        
        # Interpret
        if abs(slope) < 1e-5 and p_value > 0.05:
            print("RESULT: NO SIGNIFICANT DRIFT")
            print("        Balance is statistically stable over 5000 steps.")
            drift_verdict = "stable"
        elif slope > 0 and p_value < 0.05:
            print("RESULT: SYSTEMATIC DRIFT TOWARD + DOMINANCE")
            print(f"        Estimated drift: {slope * 1000:.3f} per 1000 steps")
            drift_verdict = "drift_positive"
        elif slope < 0 and p_value < 0.05:
            print("RESULT: SYSTEMATIC DRIFT TOWARD - DOMINANCE")
            print(f"        Estimated drift: {slope * 1000:.3f} per 1000 steps")
            drift_verdict = "drift_negative"
        else:
            print("RESULT: WEAK OR AMBIGUOUS TREND")
            drift_verdict = "ambiguous"
        
        print()
        
        # Time-windowed analysis
        print("Time-Windowed Analysis:")
        windows = [(0, 1000), (1000, 2000), (2000, 3000), (3000, 4000), (4000, 5000)]
        
        for lo, hi in windows:
            window_data = [h for h in valid if lo <= h['step'] < hi]
            if window_data:
                w_bal = np.mean([h['balance'] for h in window_data])
                w_imb = np.mean([h['imbalance'] for h in window_data])
                print(f"  Steps {lo:>4}-{hi:<4}: balance = {w_bal:.3f}, imbalance = {w_imb:+.3f}")
        
        print()
        print("=" * 75)
        print("CONCLUSION")
        print("=" * 75)
        print()
        
        if drift_verdict == "stable" and avg_balance > 0.85:
            print("BALANCE PERSISTS")
            print()
            print(f"The ~50/50 balance (avg = {avg_balance:.3f}) is maintained over")
            print("5000 steps with no significant drift.")
            print()
            print("This confirms the statistical balance mechanism is ROBUST.")
            conclusion = "persistent"
        elif drift_verdict == "stable":
            print("BALANCE PRESENT BUT LOWER THAN EXPECTED")
            print()
            print(f"Average balance = {avg_balance:.3f} (expected ~0.90)")
            print("No drift detected, but balance is weaker than Phase 11f.")
            conclusion = "weak_persistent"
        else:
            print("BALANCE SHOWS DRIFT OR INSTABILITY")
            print()
            print(f"Systematic trend detected: {drift_verdict}")
            print("Balance may not be fully robust over very long times.")
            conclusion = "unstable"
    else:
        conclusion = "insufficient_data"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase12_long_time_balance_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'long_time_balance_persistence',
            'question': 'Does 50/50 balance persist over 5000+ steps?',
            'total_steps': 5000,
            'history': history,
            'avg_balance': avg_balance if 'avg_balance' in dir() else None,
            'drift_verdict': drift_verdict if 'drift_verdict' in dir() else 'unknown',
            'conclusion': conclusion,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, conclusion


if __name__ == "__main__":
    history, conclusion = run_long_time_balance_test()
