#!/usr/bin/env python3
"""
Local Extended Test Suite for QMRT Simulator
=============================================

This script enables long-horizon testing that exceeds cloud environment time limits.
Run on your local machine for proper scientific validation.

Usage:
    python local_extended_test.py --test remnant --steps 5000 --seeds 10
    python local_extended_test.py --test damping --steps 3000
    python local_extended_test.py --test sweep --rates 0.05,0.10,0.15 --seeds 20

Requirements:
    pip install numpy scipy
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.ndimage import gaussian_filter, label


class ExtendedSimulator:
    """
    Full-featured simulator for long-horizon testing.
    Includes all branches: Geometry, Channel, Remnant, τ, Damping.
    """
    
    def __init__(self, size: int = 48,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 remnant_fraction: float = 0.0,
                 remnant_alpha: float = 1.0,
                 damping_to_tau: float = 0.0,  # New: recycled energy fraction
                 use_stability_weighted_remnant: bool = False):
        
        self.size = size
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.remnant_fraction = remnant_fraction
        self.remnant_alpha = remnant_alpha
        self.damping_to_tau = damping_to_tau
        self.use_stability_weighted_remnant = use_stability_weighted_remnant
        
        # Fields
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        self.stability_field = np.zeros((size, size, size))  # For stability-weighted remnant
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        
        self.t = 0.0
        self.dt = 0.04
        self.step_count = 0
        
        # Tracking
        self.spontaneous_creations = 0
        self.total_damped_energy = 0.0
        self.history = {
            't': [], 'n_defects': [], 'creations': [],
            'mean_remnant': [], 'mean_tau': [], 'damped_energy': []
        }
        
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
    
    def inject_vortex_at(self, cx: int, cy: int, cz: int, chirality: int = 1):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / (2 * 3**2))
        
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_balanced_structure(self, n_pairs: int = 15):
        center = self.size // 2
        
        for i in range(n_pairs):
            angle1 = np.random.uniform(0, 2 * np.pi)
            radius1 = np.random.uniform(3, self.size * 0.20)
            cx1 = int(np.clip(center + radius1 * np.cos(angle1), 5, self.size - 5))
            cy1 = int(np.clip(center + radius1 * np.sin(angle1), 5, self.size - 5))
            cz1 = center
            
            angle2 = angle1 + np.random.uniform(0.5, 1.5)
            radius2 = np.random.uniform(3, self.size * 0.20)
            cx2 = int(np.clip(center + radius2 * np.cos(angle2), 5, self.size - 5))
            cy2 = int(np.clip(center + radius2 * np.sin(angle2), 5, self.size - 5))
            cz2 = center
            
            self.inject_vortex_at(cx1, cy1, cz1, +1)
            self.inject_vortex_at(cx2, cy2, cz2, -1)
    
    def select_creation_location(self) -> Tuple[int, int, int]:
        center = self.size // 2
        
        use_remnant = np.random.random() < self.remnant_fraction
        
        if use_remnant:
            if self.use_stability_weighted_remnant:
                weights = 0.01 + self.stability_field
            else:
                weights = 0.01 + np.power(self.remnant_field + 1e-10, self.remnant_alpha)
            
            x, y, z = np.meshgrid(
                np.arange(self.size), np.arange(self.size), np.arange(self.size),
                indexing='ij'
            )
            r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
            interior_mask = r < self.size * 0.30
            
            weights = weights * interior_mask
            weights_sum = np.sum(weights)
            
            if weights_sum > 1e-10:
                weights_flat = weights.flatten() / weights_sum
                idx = np.random.choice(len(weights_flat), p=weights_flat)
                cx = idx // (self.size * self.size)
                cy = (idx % (self.size * self.size)) // self.size
                cz = idx % self.size
                return int(cx), int(cy), int(cz)
        
        # Random fallback
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(3, self.size * 0.20)
        cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
        cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
        return cx, cy, center
    
    def attempt_spontaneous_creation(self):
        high_tau_mask = self.tau > self.tau_creation_threshold
        
        if not np.any(high_tau_mask):
            return 0
        
        candidates = np.where(high_tau_mask)
        n_candidates = len(candidates[0])
        
        if n_candidates == 0:
            return 0
        
        n_sample = min(50, n_candidates)
        indices = np.random.choice(n_candidates, n_sample, replace=False)
        
        for idx in indices:
            cx = candidates[0][idx]
            cy = candidates[1][idx]
            cz = candidates[2][idx]
            
            local_tau = self.tau[cx, cy, cz]
            tau_excess = local_tau - self.tau_creation_threshold
            probability = tau_excess * self.creation_rate
            
            if np.random.random() < probability:
                loc_cx, loc_cy, loc_cz = self.select_creation_location()
                
                offset_angle = np.random.uniform(0, 2 * np.pi)
                offset_dist = np.random.uniform(3, 6)
                
                cx2 = int(np.clip(loc_cx + offset_dist * np.cos(offset_angle), 3, self.size - 3))
                cy2 = int(np.clip(loc_cy + offset_dist * np.sin(offset_angle), 3, self.size - 3))
                
                self.inject_vortex_at(loc_cx, loc_cy, loc_cz, +1)
                self.inject_vortex_at(cx2, cy2, loc_cz, -1)
                
                self.spontaneous_creations += 1
                return 1
        
        return 0
    
    def step(self):
        self.step_count += 1
        self.t += self.dt
        
        self.attempt_spontaneous_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # Energy and τ dynamics
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        c_eff_sq = self.c_0_sq * self.tau
        
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Damping energy tracking and recycling
        damped_energy = self.gamma * (self.psi_r_dot**2 + self.psi_i_dot**2)
        step_damped = float(np.sum(damped_energy))
        self.total_damped_energy += step_damped
        
        # Damping → τ coupling: recycled energy elevates τ
        if self.damping_to_tau > 0:
            tau_injection = self.damping_to_tau * damped_energy
            self.tau += tau_injection
            self.tau = np.clip(self.tau, 0.5, 2.5)  # Slightly higher ceiling for recycling
        
        # Topology detection and branch updates
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Channel update
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        # Remnant update
        self.remnant_field += 0.02 * topology_norm
        self.remnant_field *= 0.999
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        # Stability field: accumulates where topology persists
        topology_threshold = 0.3
        stable_mask = topology_norm > topology_threshold
        self.stability_field[stable_mask] += 0.01
        self.stability_field[~stable_mask] *= 0.995  # Slower decay for stability
        self.stability_field = np.clip(self.stability_field, 0, 1)
        
        # Channel protection
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        # Update velocities and positions
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def detect_defects(self, threshold: float = 0.4) -> Dict:
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
                local_vort = vorticity[cx, cy, coords[2][0]]
                
                if local_vort > 0.05:
                    n_pos += 1
                elif local_vort < -0.05:
                    n_neg += 1
        
        return {'n_pos': n_pos, 'n_neg': n_neg, 'n_total': n_pos + n_neg}
    
    def record(self):
        defects = self.detect_defects()
        self.history['t'].append(round(self.t, 2))
        self.history['n_defects'].append(defects['n_total'])
        self.history['creations'].append(self.spontaneous_creations)
        self.history['mean_remnant'].append(float(np.mean(self.remnant_field)))
        self.history['mean_tau'].append(float(np.mean(self.tau)))
        self.history['damped_energy'].append(self.total_damped_energy)


def run_extended_test(config: Dict) -> Dict:
    """Run a single extended test configuration."""
    sim = ExtendedSimulator(
        size=config.get('size', 48),
        tau_creation_threshold=config.get('threshold', 1.001),
        creation_rate=config.get('rate', 0.15),
        remnant_fraction=config.get('remnant_frac', 0.0),
        remnant_alpha=config.get('remnant_alpha', 1.0),
        damping_to_tau=config.get('damping_to_tau', 0.0),
        use_stability_weighted_remnant=config.get('stability_remnant', False)
    )
    
    seed = config.get('seed', 42)
    np.random.seed(seed)
    
    sim.psi_r += 0.03 * np.random.randn(sim.size, sim.size, sim.size)
    sim.psi_i += 0.03 * np.random.randn(sim.size, sim.size, sim.size)
    sim.seed_balanced_structure(n_pairs=config.get('n_pairs', 15))
    
    warmup = config.get('warmup', 200)
    steps = config.get('steps', 1000)
    record_interval = config.get('record_interval', 50)
    
    # Warmup
    for _ in range(warmup):
        sim.step()
    
    # Main run with recording
    for step in range(steps):
        sim.step()
        if step % record_interval == 0:
            sim.record()
    
    # Final measurement
    late_n = [sim.history['n_defects'][i] for i in range(-min(10, len(sim.history['n_defects'])), 0)]
    
    return {
        'config': config,
        'history': sim.history,
        'summary': {
            'final_n': sim.detect_defects()['n_total'],
            'avg_late_n': float(np.mean(late_n)) if late_n else 0,
            'total_creations': sim.spontaneous_creations,
            'total_damped_energy': sim.total_damped_energy,
            'sustained': float(np.mean(late_n)) > 0.3 if late_n else False
        }
    }


def run_remnant_sweep(args):
    """Long-horizon remnant coupling sweep."""
    print("=" * 80)
    print("  EXTENDED REMNANT COUPLING SWEEP")
    print("=" * 80)
    print(f"  Steps: {args.steps}, Seeds: {args.seeds}")
    print()
    
    rates = [float(r) for r in args.rates.split(',')]
    fracs = [float(f) for f in args.memory_fracs.split(',')]
    seeds = list(range(args.seeds))
    
    results = []
    
    for frac in fracs:
        name = "Random" if frac == 0 else f"{int(frac*100)}%Mem"
        print(f"\n{name}:")
        
        for rate in rates:
            seed_results = []
            for seed in seeds:
                config = {
                    'size': args.size,
                    'rate': rate,
                    'remnant_frac': frac,
                    'seed': seed,
                    'steps': args.steps,
                    'warmup': 200,
                    'record_interval': 100
                }
                r = run_extended_test(config)
                seed_results.append(r['summary'])
            
            avg_n = np.mean([r['avg_late_n'] for r in seed_results])
            sustain_pct = sum(1 for r in seed_results if r['sustained']) / len(seeds) * 100
            
            print(f"  rate={rate:.3f}: sustain={sustain_pct:.0f}%, avg_N={avg_n:.2f}")
            
            results.append({
                'strategy': name,
                'rate': rate,
                'sustain_pct': sustain_pct,
                'avg_n': avg_n,
                'per_seed': [r['avg_late_n'] for r in seed_results]
            })
    
    # Save results
    output_path = Path('qmrt_topology/papers/extended_remnant_results.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'extended_remnant_sweep',
            'timestamp': datetime.now().isoformat(),
            'params': vars(args),
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")


def run_damping_test(args):
    """Test Damping → τ coupling."""
    print("=" * 80)
    print("  DAMPING → τ COUPLING TEST")
    print("=" * 80)
    print(f"  Steps: {args.steps}")
    print()
    
    damping_fracs = [0.0, 0.1, 0.25, 0.5, 1.0]
    rates = [0.10, 0.15, 0.20]
    seeds = list(range(5))
    
    results = []
    
    for damping in damping_fracs:
        name = "No recycle" if damping == 0 else f"{int(damping*100)}% recycle"
        print(f"\n{name}:")
        
        for rate in rates:
            seed_results = []
            for seed in seeds:
                config = {
                    'size': args.size,
                    'rate': rate,
                    'damping_to_tau': damping,
                    'seed': seed,
                    'steps': args.steps,
                    'warmup': 200,
                    'record_interval': 100
                }
                r = run_extended_test(config)
                seed_results.append(r['summary'])
            
            avg_n = np.mean([r['avg_late_n'] for r in seed_results])
            sustain_pct = sum(1 for r in seed_results if r['sustained']) / len(seeds) * 100
            
            print(f"  rate={rate:.2f}: sustain={sustain_pct:.0f}%, avg_N={avg_n:.2f}")
            
            results.append({
                'damping_recycle': damping,
                'rate': rate,
                'sustain_pct': sustain_pct,
                'avg_n': avg_n
            })
    
    # Save results
    output_path = Path('qmrt_topology/papers/damping_tau_results.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'damping_tau_coupling',
            'timestamp': datetime.now().isoformat(),
            'params': vars(args),
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")


def run_stability_remnant_test(args):
    """Test stability-weighted remnant vs raw remnant."""
    print("=" * 80)
    print("  STABILITY-WEIGHTED REMNANT TEST")
    print("=" * 80)
    print("  Comparing: 'where topology existed' vs 'where topology survived'")
    print()
    
    configs = [
        ('Random', 0.0, False),
        ('Raw Remnant 25%', 0.25, False),
        ('Stability Remnant 25%', 0.25, True),
    ]
    
    rates = [0.10, 0.15]
    seeds = list(range(5))
    
    for name, frac, stability in configs:
        print(f"\n{name}:")
        
        for rate in rates:
            seed_results = []
            for seed in seeds:
                config = {
                    'size': args.size,
                    'rate': rate,
                    'remnant_frac': frac,
                    'stability_remnant': stability,
                    'seed': seed,
                    'steps': args.steps,
                    'warmup': 200,
                    'record_interval': 100
                }
                r = run_extended_test(config)
                seed_results.append(r['summary'])
            
            avg_n = np.mean([r['avg_late_n'] for r in seed_results])
            sustain_pct = sum(1 for r in seed_results if r['sustained']) / len(seeds) * 100
            
            print(f"  rate={rate:.2f}: sustain={sustain_pct:.0f}%, avg_N={avg_n:.2f}")


def main():
    parser = argparse.ArgumentParser(description='QMRT Extended Test Suite')
    parser.add_argument('--test', type=str, required=True,
                        choices=['remnant', 'damping', 'stability_remnant', 'sweep'],
                        help='Test type to run')
    parser.add_argument('--steps', type=int, default=3000,
                        help='Simulation steps (default: 3000)')
    parser.add_argument('--seeds', type=int, default=10,
                        help='Number of random seeds (default: 10)')
    parser.add_argument('--size', type=int, default=48,
                        help='Grid size (default: 48)')
    parser.add_argument('--rates', type=str, default='0.10,0.15,0.20',
                        help='Comma-separated creation rates')
    parser.add_argument('--memory_fracs', type=str, default='0.0,0.10,0.25',
                        help='Comma-separated memory fractions')
    
    args = parser.parse_args()
    
    print(f"\nStarting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    start_time = time.time()
    
    if args.test == 'remnant':
        run_remnant_sweep(args)
    elif args.test == 'damping':
        run_damping_test(args)
    elif args.test == 'stability_remnant':
        run_stability_remnant_test(args)
    elif args.test == 'sweep':
        run_remnant_sweep(args)
    
    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed/60:.1f} minutes")


if __name__ == "__main__":
    main()
