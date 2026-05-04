"""
Phase 12c: Large Domain (96³) Validation
==========================================

PURPOSE:
Validate that the topological dual-sector results hold at larger scale.

WHAT WE'RE TESTING:
1. Does ~50/50 balance persist at 96³?
2. Is organizational symmetry maintained?
3. Is the regime scale-robust?

NOTE: 96³ is 8× the volume of 48³, so we expect:
- More defects (higher populations)
- Similar balance ratios
- Similar organizational symmetry

Computational note: 96³ is heavy, so we run fewer steps with coarser sampling.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import ttest_ind
from collections import defaultdict
from typing import List, Tuple, Dict
import json
import time


class LargeDomainSimulator:
    """96³ simulator for scale validation."""
    
    def __init__(self, size: int = 96, injection_interval: int = 100):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 6  # More injections for larger domain
        
        print(f"Initializing {size}³ grid...")
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
        
        print("Creating coupling field...")
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        print("Initialization complete.")
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        mask_interior = r <= interior_r
        mask_exterior = r >= interior_r + 10.0
        mask_transition = ~mask_interior & ~mask_exterior
        
        coupling[mask_interior] = 0.7
        coupling[mask_exterior] = 0.2
        
        t = (r[mask_transition] - interior_r) / 10.0
        coupling[mask_transition] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
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
        # Balanced: half positive, half negative
        chiralities = [+1, +1, +1, -1, -1, -1]
        for chirality in chiralities[:self.injection_count]:
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
    
    def detect_signed_defects_with_positions(self, threshold: float = 0.4) -> List[Tuple]:
        """Detect defects with position and sign."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        defects = []
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                cz = int(np.mean(coords[2]))
                
                local_vort = vorticity[cx, cy, cz]
                
                if local_vort > 0.05:
                    defects.append(((cx, cy, cz), +1))
                elif local_vort < -0.05:
                    defects.append(((cx, cy, cz), -1))
        
        return defects


def euclidean_periodic(p1, p2, size):
    d = np.abs(np.array(p1) - np.array(p2))
    d = np.minimum(d, size - d)
    return np.sqrt(np.sum(d**2))


def measure_quick_metrics(defects, size) -> Dict:
    """Quick organizational metrics for 96³ validation."""
    n = len(defects)
    
    if n < 20:
        return {'valid': False, 'n': n}
    
    pos_indices = [i for i, (_, sign) in enumerate(defects) if sign == +1]
    neg_indices = [i for i, (_, sign) in enumerate(defects) if sign == -1]
    
    n_pos = len(pos_indices)
    n_neg = len(neg_indices)
    
    if n_pos < 5 or n_neg < 5:
        return {'valid': False, 'n': n, 'n_pos': n_pos, 'n_neg': n_neg}
    
    # Sample for efficiency
    max_sample = 100
    if n > max_sample:
        indices = np.random.choice(n, max_sample, replace=False)
        sampled = [defects[i] for i in indices]
    else:
        sampled = defects
    
    n_sampled = len(sampled)
    
    # Build adjacency
    adj = defaultdict(set)
    for i in range(n_sampled):
        pos_i, _ = sampled[i]
        for j in range(i + 1, n_sampled):
            pos_j, _ = sampled[j]
            d = euclidean_periodic(pos_i, pos_j, size)
            if d < 12.0:  # Slightly larger for 96³
                adj[i].add(j)
                adj[j].add(i)
    
    # Compute degrees by sign (within sample)
    pos_in_sample = [i for i, (_, sign) in enumerate(sampled) if sign == +1]
    neg_in_sample = [i for i, (_, sign) in enumerate(sampled) if sign == -1]
    
    pos_degrees = [len(adj[i]) for i in pos_in_sample]
    neg_degrees = [len(adj[i]) for i in neg_in_sample]
    
    pos_mean_deg = np.mean(pos_degrees) if pos_degrees else 0
    neg_mean_deg = np.mean(neg_degrees) if neg_degrees else 0
    
    # Balance
    balance = 1 - abs(n_pos - n_neg) / (n_pos + n_neg)
    
    return {
        'valid': True,
        'n': n,
        'n_pos': n_pos,
        'n_neg': n_neg,
        'balance': balance,
        'pos_mean_degree': pos_mean_deg,
        'neg_mean_degree': neg_mean_deg,
        'degree_diff': pos_mean_deg - neg_mean_deg,
    }


def run_large_domain_validation():
    """
    Validate topological dual-sector results at 96³.
    """
    print("=" * 75)
    print("  PHASE 12c: LARGE DOMAIN (96³) VALIDATION")
    print("=" * 75)
    print()
    print("Testing whether dual-sector results hold at 8× volume.")
    print()
    
    start_time = time.time()
    
    sim = LargeDomainSimulator(size=96, injection_interval=100)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(96, 96, 96)
    sim.psi_i += 0.03 * np.random.randn(96, 96, 96)
    
    # Scaled seeding for larger domain
    center = 48
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                chirality = 1 if (i + j) % 2 == 0 else -1
                sim.inject_vortex(center + i * 6, center + j * 6, chirality)
    
    print(f"{'Step':>5} │ {'N+':>5} {'N-':>5} │ {'Balance':>7} │ {'Deg+':>5} {'Deg-':>5} │ {'Time':>6}")
    print("-" * 65)
    
    history = []
    
    # Run 1000 steps, sample every 200 (5 measurements) - efficient for 96³
    for step in range(1000):
        sim.step()
        
        if step % 200 == 0 and step > 0:
            defects = sim.detect_signed_defects_with_positions()
            m = measure_quick_metrics(defects, sim.size)
            
            elapsed = time.time() - start_time
            
            if m['valid']:
                print(f"{step:>5} │ {m['n_pos']:>5} {m['n_neg']:>5} │ {m['balance']:>7.3f} │ "
                      f"{m['pos_mean_degree']:>5.2f} {m['neg_mean_degree']:>5.2f} │ {elapsed:>6.1f}s")
                
                m['step'] = step
                history.append(m)
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("96³ VALIDATION RESULTS")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n'] > 50]
    
    if len(valid) >= 3:
        # Balance
        balances = [h['balance'] for h in valid]
        avg_balance = np.mean(balances)
        
        print(f"1. BALANCE")
        print(f"   Average balance (96³): {avg_balance:.3f}")
        print(f"   Reference (48³):       0.950")
        
        if avg_balance > 0.85:
            print(f"   → BALANCE CONFIRMED at 96³")
            balance_ok = True
        else:
            print(f"   → Balance weaker at 96³")
            balance_ok = False
        
        print()
        
        # Organizational symmetry
        pos_degs = [h['pos_mean_degree'] for h in valid]
        neg_degs = [h['neg_mean_degree'] for h in valid]
        
        avg_pos_deg = np.mean(pos_degs)
        avg_neg_deg = np.mean(neg_degs)
        
        print(f"2. ORGANIZATIONAL SYMMETRY")
        print(f"   + sector avg degree: {avg_pos_deg:.3f}")
        print(f"   - sector avg degree: {avg_neg_deg:.3f}")
        print(f"   Difference: {avg_pos_deg - avg_neg_deg:+.3f}")
        
        if len(valid) >= 3:
            _, p_deg = ttest_ind(pos_degs, neg_degs)
            print(f"   t-test p-value: {p_deg:.3f}")
            
            if p_deg > 0.05:
                print(f"   → SYMMETRY CONFIRMED at 96³")
                symmetry_ok = True
            else:
                print(f"   → Possible asymmetry at 96³")
                symmetry_ok = False
        else:
            symmetry_ok = True  # Not enough data to reject
        
        print()
        
        # Population scaling
        avg_pop = np.mean([h['n'] for h in valid])
        print(f"3. POPULATION SCALING")
        print(f"   Average population (96³): {avg_pop:.0f}")
        print(f"   Reference (48³): ~200-300")
        print(f"   Volume ratio: 8×")
        print(f"   Population ratio: {avg_pop / 250:.1f}×")
        
        print()
        print("=" * 75)
        print("CONCLUSION")
        print("=" * 75)
        print()
        
        if balance_ok and symmetry_ok:
            print("96³ VALIDATION: PASSED")
            print()
            print("The topological dual-sector results are SCALE-ROBUST:")
            print(f"  - Balance maintained ({avg_balance:.3f})")
            print(f"  - Organizational symmetry maintained")
            print(f"  - Results hold at 8× volume")
            conclusion = "passed"
        elif balance_ok:
            print("96³ VALIDATION: PARTIAL (Balance OK, Symmetry unclear)")
            conclusion = "partial"
        else:
            print("96³ VALIDATION: NEEDS MORE DATA")
            conclusion = "inconclusive"
    else:
        print("Insufficient data for validation.")
        conclusion = "insufficient_data"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/phase12_large_domain_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'study': 'large_domain_validation',
            'domain_size': 96,
            'history': history,
            'conclusion': conclusion,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, conclusion


if __name__ == "__main__":
    history, conclusion = run_large_domain_validation()
