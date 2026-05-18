"""
Dimensional Trapping Test
==========================

PURPOSE: Test whether τ-boundary conditions can constrain the medium's
degrees of freedom and delay/prevent 3D emergence.

HYPOTHESIS: If dimensionality is "degrees of freedom, not fixed background,"
then τ geometry should be able to trap the medium in lower-dimensional phases.

CONFIGURATIONS:
  - Free baseline: Normal v1.1 medium (confirm natural 3D emergence)
  - 1D trap: Narrow high-τ channel with low-τ/damped walls
  - 2D trap: High-τ sheet with low-τ/damped upper/lower boundaries

METRICS:
  - D_eff, r2, r3, anisotropy
  - phase_T, escape_time
  - topology_count, tau_leakage
  - boundary_crossing_rate

BASELINE: Regulated Recovery v1.1

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label
from scipy.linalg import eigh
from typing import Dict, List, Optional, Any, Tuple
import time
import json
import os
import argparse


class DimensionalTrappingSimulator:
    """
    Simulator for testing dimensional trapping via τ boundaries.
    
    Supports three geometries:
    - 'free': No boundaries (baseline)
    - '1d_trap': Channel geometry (low-τ walls in y,z)
    - '2d_trap': Sheet geometry (low-τ walls in z only)
    """
    
    def __init__(self, 
                 size: int = 32, 
                 dt: float = 0.12, 
                 seed: int = None,
                 geometry: str = 'free',
                 boundary_tau: float = 0.6,
                 boundary_damping_mult: float = 2.0,
                 channel_width: int = 5,
                 sheet_thickness: int = 5):
        """
        Initialize simulator with specified trapping geometry.
        
        Parameters:
        -----------
        geometry : str
            'free', '1d_trap', or '2d_trap'
        boundary_tau : float
            τ value in boundary regions (lower = more trapping)
        boundary_damping_mult : float
            Damping multiplier in boundary regions
        channel_width : int
            Width of 1D channel (for 1d_trap)
        sheet_thickness : int
            Thickness of 2D sheet (for 2d_trap)
        """
        
        # Configuration
        self.config = {
            'size': size,
            'dt': dt,
            'seed': seed,
            'geometry': geometry,
            'boundary_tau': boundary_tau,
            'boundary_damping_mult': boundary_damping_mult,
            'channel_width': channel_width,
            'sheet_thickness': sheet_thickness,
            # Regulated Recovery v1.1 (LOCKED)
            'damping_to_tau': 0.20,
            'tau_cap': 1.8,
            'tau_creation_threshold': 1.001,
            'creation_rate': 0.15,
            'tau_response': 0.02,
            'tau_relaxation': 0.01,
            'c_0_sq': 4.0,
            'gamma': 0.007,
        }
        
        self.size = size
        self.dt = dt
        self.geometry = geometry
        self.boundary_tau = boundary_tau
        self.boundary_damping_mult = boundary_damping_mult
        self.channel_width = channel_width
        self.sheet_thickness = sheet_thickness
        
        # Set RNG
        if seed is not None:
            np.random.seed(seed)
        
        # Regulated Recovery v1.1 parameters
        self.damping_to_tau = self.config['damping_to_tau']
        self.tau_cap = self.config['tau_cap']
        self.tau_creation_threshold = self.config['tau_creation_threshold']
        self.creation_rate = self.config['creation_rate']
        self.tau_response = self.config['tau_response']
        self.tau_relaxation = self.config['tau_relaxation']
        self.c_0_sq = self.config['c_0_sq']
        self.gamma_base = self.config['gamma']
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Wave field
        self.psi_r = np.ones((size, size, size)) * 1.0
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Medium field - initialize with geometry
        self.tau = np.ones((size, size, size))
        self.tau_target = np.ones((size, size, size))  # Target τ for boundaries
        self.gamma = np.ones((size, size, size)) * self.gamma_base  # Spatially varying damping
        
        # Apply geometry
        self.boundary_mask = np.zeros((size, size, size), dtype=bool)
        self.interior_mask = np.ones((size, size, size), dtype=bool)
        self._setup_geometry()
        
        # Counters (before seeding)
        self.total_creations = 0
        self.boundary_crossings = 0
        
        # Seed initial structure based on geometry
        self._seed_initial_structure()
        
        # Tracking history
        self.metrics_history = []
        
        # Escape detection
        self.escaped = False
        self.escape_T = None
        self.escape_threshold_D_eff = 2.6  # D_eff above this = escaped to 3D
    
    def _setup_geometry(self):
        """Configure τ and damping fields based on geometry type."""
        center = self.size // 2
        
        if self.geometry == 'free':
            # No boundaries - uniform medium
            self.tau_target[:] = 1.0
            self.gamma[:] = self.gamma_base
            self.interior_mask[:] = True
            
        elif self.geometry == '1d_trap':
            # 1D channel: high-τ along z-axis, low-τ walls in x-y
            half_width = self.channel_width // 2
            
            # Create boundary mask (everywhere except the channel)
            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        # Distance from z-axis (at x=center, y=center)
                        dx = abs(x - center)
                        dy = abs(y - center)
                        if dx > half_width or dy > half_width:
                            self.boundary_mask[x, y, z] = True
                            self.interior_mask[x, y, z] = False
            
            # Set boundary properties
            self.tau_target[self.boundary_mask] = self.boundary_tau
            self.tau_target[self.interior_mask] = 1.0  # Normal τ in channel
            self.gamma[self.boundary_mask] = self.gamma_base * self.boundary_damping_mult
            
            # Initialize τ to target
            self.tau = self.tau_target.copy()
            
        elif self.geometry == '2d_trap':
            # 2D sheet: high-τ in x-y plane at z=center, low-τ above/below
            half_thick = self.sheet_thickness // 2
            
            # Create boundary mask (above and below the sheet)
            for z in range(self.size):
                dz = abs(z - center)
                if dz > half_thick:
                    self.boundary_mask[:, :, z] = True
                    self.interior_mask[:, :, z] = False
            
            # Set boundary properties
            self.tau_target[self.boundary_mask] = self.boundary_tau
            self.tau_target[self.interior_mask] = 1.0  # Normal τ in sheet
            self.gamma[self.boundary_mask] = self.gamma_base * self.boundary_damping_mult
            
            # Initialize τ to target
            self.tau = self.tau_target.copy()
        
        else:
            raise ValueError(f"Unknown geometry: {self.geometry}")
        
        print(f"  Geometry: {self.geometry}")
        print(f"  Interior volume: {np.sum(self.interior_mask)} / {self.size**3} cells")
        print(f"  Boundary τ: {self.boundary_tau}, Damping mult: {self.boundary_damping_mult}")
    
    def _seed_initial_structure(self):
        """Seed initial vortices in the interior region."""
        center = self.size // 2
        
        if self.geometry == '1d_trap':
            # Seed along z-axis (the channel direction)
            n_vortices = min(6, self.size // 6)
            for i in range(n_vortices):
                z = center - n_vortices//2 * 3 + i * 3
                z = max(3, min(self.size - 3, z))
                chirality = 1 if i % 2 == 0 else -1
                self._inject_vortex(center, center, z, chirality)
                
        elif self.geometry == '2d_trap':
            # Seed in the x-y plane at z=center
            n_per_side = 3
            spacing = max(3, self.channel_width // 2)
            for i in range(n_per_side):
                for j in range(n_per_side):
                    cx = center - spacing + i * spacing
                    cy = center - spacing + j * spacing
                    chirality = 1 if (i + j) % 2 == 0 else -1
                    self._inject_vortex(cx, cy, center, chirality)
        
        else:  # free
            # Seed a small cluster at center
            self._inject_vortex(center, center, center, 1)
            self._inject_vortex(center+3, center, center, -1)
            self._inject_vortex(center, center+3, center, 1)
        
        # Small noise
        self.psi_r += np.random.randn(self.size, self.size, self.size) * 0.001
        self.psi_i += np.random.randn(self.size, self.size, self.size) * 0.001
    
    def _inject_vortex(self, cx: int, cy: int, cz: int, chirality: int = 1):
        """Inject a vortex at specified location."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / 18)
        
        vortex = np.tanh(r / 2.5) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        blend = 0.15 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
        self.total_creations += 1
    
    def step(self):
        """Advance simulation with boundary-enforced τ geometry."""
        self.step_count += 1
        self.global_T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # τ dynamics with boundary enforcement
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_drive = 1.0 + self.tau_response * (energy - np.mean(energy))
        
        # Interior: normal τ dynamics
        # Boundary: relax toward boundary_tau
        tau_target_dynamic = np.where(
            self.interior_mask,
            tau_drive,
            self.tau_target  # Fixed boundary τ
        )
        
        self.tau += self.tau_relaxation * (tau_target_dynamic - self.tau)
        
        # Damping→τ coupling only in interior
        if self.damping_to_tau > 0:
            tau_addition = self.damping_to_tau * damped_energy
            tau_addition[self.boundary_mask] *= 0.1  # Suppress in boundaries
            self.tau += tau_addition
        
        # Enforce τ bounds
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Stronger enforcement of boundary τ
        self.tau[self.boundary_mask] = 0.9 * self.tau[self.boundary_mask] + 0.1 * self.boundary_tau
        
        # Creation events (only in interior where τ > threshold)
        interior_high_tau = self.interior_mask & (self.tau > self.tau_creation_threshold)
        if np.any(interior_high_tau):
            n_candidates = np.sum(interior_high_tau)
            create_prob = self.creation_rate * (self.tau[interior_high_tau] - self.tau_creation_threshold)
            create_mask_1d = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask_1d):
                coords = np.array(np.where(interior_high_tau)).T
                create_coords = coords[create_mask_1d]
                
                for (cx, cy, cz) in create_coords[:3]:
                    chirality = np.random.choice([-1, 1])
                    self._inject_vortex(cx, cy, cz, chirality)
                    self.tau[cx, cy, cz] = 1.0
        
        # Wave equation with spatially varying damping
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def compute_metrics(self) -> Dict[str, Any]:
        """Compute dimensional and trapping metrics."""
        # Get topology activity field
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Activity in interior vs boundary
        interior_activity = np.mean(topology[self.interior_mask])
        boundary_activity = np.mean(topology[self.boundary_mask]) if np.any(self.boundary_mask) else 0
        
        # τ leakage: how much τ has risen in boundary region
        tau_leakage = np.mean(self.tau[self.boundary_mask]) - self.boundary_tau if np.any(self.boundary_mask) else 0
        
        # Count defects
        labeled, n_defects = label(amp < 0.5)
        defect_count = 0
        interior_defects = 0
        boundary_defects = 0
        
        for i in range(1, n_defects + 1):
            component = (labeled == i)
            if np.sum(component) >= 3:
                defect_count += 1
                # Check if mostly interior or boundary
                if np.sum(component & self.interior_mask) > np.sum(component & self.boundary_mask):
                    interior_defects += 1
                else:
                    boundary_defects += 1
        
        # Boundary crossing rate
        boundary_crossing_rate = boundary_defects / max(1, defect_count) if defect_count > 0 else 0
        
        # Dimensionality analysis (interior only)
        threshold = np.percentile(topology[self.interior_mask], 90) if np.any(self.interior_mask) else 0
        active_mask = self.interior_mask & (topology > threshold)
        n_active = np.sum(active_mask)
        
        if n_active < 10:
            return {
                'valid': False,
                'D_eff': 0.0,
                'r2': 0.0,
                'r3': 0.0,
                'anisotropy': 1.0,
                'n_active': int(n_active),
                'n_defects': defect_count,
                'interior_defects': interior_defects,
                'boundary_defects': boundary_defects,
                'tau_mean': float(np.mean(self.tau[self.interior_mask])),
                'tau_leakage': float(tau_leakage),
                'boundary_crossing_rate': float(boundary_crossing_rate),
                'interior_activity': float(interior_activity),
                'boundary_activity': float(boundary_activity),
            }
        
        # Compute covariance of active positions
        active_coords = np.array(np.where(active_mask)).T
        weights = topology[active_mask]
        weights = weights / np.sum(weights)
        
        centroid = np.average(active_coords, axis=0, weights=weights)
        centered = active_coords - centroid
        
        cov = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                cov[i, j] = np.sum(weights * centered[:, i] * centered[:, j])
        
        eigenvalues, _ = eigh(cov)
        eigenvalues = np.sort(eigenvalues)[::-1]
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        
        lambda1, lambda2, lambda3 = eigenvalues
        
        # D_eff = (λ1 + λ2 + λ3)² / (λ1² + λ2² + λ3²)
        sum_lambda = lambda1 + lambda2 + lambda3
        sum_lambda_sq = lambda1**2 + lambda2**2 + lambda3**2
        D_eff = sum_lambda**2 / sum_lambda_sq if sum_lambda_sq > 0 else 1.0
        
        r2 = lambda2 / lambda1 if lambda1 > 0 else 0.0
        r3 = lambda3 / lambda1 if lambda1 > 0 else 0.0
        anisotropy = 1 - (lambda3 / lambda1) if lambda1 > 0 else 1.0
        
        return {
            'valid': True,
            'D_eff': float(D_eff),
            'r2': float(r2),
            'r3': float(r3),
            'eigenvalues': [float(lambda1), float(lambda2), float(lambda3)],
            'anisotropy': float(anisotropy),
            'n_active': int(n_active),
            'n_defects': defect_count,
            'interior_defects': interior_defects,
            'boundary_defects': boundary_defects,
            'tau_mean': float(np.mean(self.tau[self.interior_mask])),
            'tau_leakage': float(tau_leakage),
            'boundary_crossing_rate': float(boundary_crossing_rate),
            'interior_activity': float(interior_activity),
            'boundary_activity': float(boundary_activity),
        }
    
    def check_escape(self, metrics: Dict) -> bool:
        """Check if system has escaped to 3D."""
        if not metrics['valid']:
            return False
        
        D_eff = metrics['D_eff']
        
        if D_eff >= self.escape_threshold_D_eff and not self.escaped:
            self.escaped = True
            self.escape_T = self.global_T
            return True
        
        return False
    
    def record_metrics(self, metrics: Dict):
        """Record metrics for this checkpoint."""
        record = {
            'global_T': self.global_T,
            'step_count': self.step_count,
            'escaped': self.escaped,
            **metrics
        }
        self.metrics_history.append(record)


def run_single_trap_test(
    geometry: str = 'free',
    boundary_tau: float = 0.6,
    boundary_damping_mult: float = 2.0,
    channel_width: int = 5,
    sheet_thickness: int = 5,
    target_T: float = 500.0,
    seed: int = 42,
    size: int = 32,
    measure_interval: float = 25.0,
) -> Dict[str, Any]:
    """Run a single trapping test configuration."""
    
    print(f"\n{'='*60}")
    print(f"  TRAP TEST: {geometry}")
    print(f"{'='*60}")
    print(f"  boundary_tau={boundary_tau}, damping_mult={boundary_damping_mult}")
    if geometry == '1d_trap':
        print(f"  channel_width={channel_width}")
    elif geometry == '2d_trap':
        print(f"  sheet_thickness={sheet_thickness}")
    print()
    
    sim = DimensionalTrappingSimulator(
        size=size,
        dt=0.12,
        seed=seed,
        geometry=geometry,
        boundary_tau=boundary_tau,
        boundary_damping_mult=boundary_damping_mult,
        channel_width=channel_width,
        sheet_thickness=sheet_thickness,
    )
    
    last_measure = 0.0
    
    while sim.global_T < target_T:
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            metrics = sim.compute_metrics()
            sim.record_metrics(metrics)
            sim.check_escape(metrics)
            
            status = "ESCAPED" if sim.escaped else "trapped"
            print(f"T={sim.global_T:>6.1f} | D_eff={metrics['D_eff']:.3f} | "
                  f"r2={metrics['r2']:.3f} | r3={metrics['r3']:.3f} | "
                  f"defects={metrics['n_defects']:>3} | τ_leak={metrics['tau_leakage']:.3f} | {status}")
    
    # Final metrics
    final_metrics = sim.compute_metrics()
    
    result = {
        'geometry': geometry,
        'config': sim.config,
        'seed': seed,
        'target_T': target_T,
        'final_T': sim.global_T,
        'escaped': sim.escaped,
        'escape_T': sim.escape_T,
        'final_metrics': final_metrics,
        'metrics_history': sim.metrics_history,
    }
    
    print()
    print(f"  Final D_eff: {final_metrics['D_eff']:.3f}")
    print(f"  Escaped: {sim.escaped}" + (f" at T={sim.escape_T:.1f}" if sim.escape_T else ""))
    
    return result


def run_dimensional_trapping_sweep(
    target_T: float = 500.0,
    seeds: List[int] = [42, 123, 456],
    size: int = 32,
) -> Dict[str, Any]:
    """
    Run full dimensional trapping sweep.
    
    Tests:
    - Free baseline (3 seeds)
    - 1D trap sweep (boundary_tau, channel_width)
    - 2D trap sweep (boundary_tau, sheet_thickness)
    """
    
    print("=" * 70)
    print("  DIMENSIONAL TRAPPING SWEEP")
    print("=" * 70)
    print()
    print(f"Target T: {target_T}, Grid: {size}³, Seeds: {seeds}")
    print()
    
    results = {
        'target_T': target_T,
        'seeds': seeds,
        'size': size,
        'tests': [],
    }
    
    # 1. Free baseline
    print("\n" + "="*70)
    print("  PHASE 1: FREE BASELINE")
    print("="*70)
    
    for seed in seeds:
        result = run_single_trap_test(
            geometry='free',
            seed=seed,
            target_T=target_T,
            size=size,
        )
        results['tests'].append(result)
    
    # 2. 1D trap sweep
    print("\n" + "="*70)
    print("  PHASE 2: 1D TRAP SWEEP")
    print("="*70)
    
    boundary_taus = [0.6, 0.8]
    channel_widths = [3, 5, 7]
    
    for b_tau in boundary_taus:
        for width in channel_widths:
            result = run_single_trap_test(
                geometry='1d_trap',
                boundary_tau=b_tau,
                boundary_damping_mult=2.0,
                channel_width=width,
                seed=seeds[0],  # Use first seed for sweep
                target_T=target_T,
                size=size,
            )
            results['tests'].append(result)
    
    # 3. 2D trap sweep
    print("\n" + "="*70)
    print("  PHASE 3: 2D TRAP SWEEP")
    print("="*70)
    
    sheet_thicknesses = [3, 5, 7]
    
    for b_tau in boundary_taus:
        for thick in sheet_thicknesses:
            result = run_single_trap_test(
                geometry='2d_trap',
                boundary_tau=b_tau,
                boundary_damping_mult=2.0,
                sheet_thickness=thick,
                seed=seeds[0],
                target_T=target_T,
                size=size,
            )
            results['tests'].append(result)
    
    return results


def analyze_results(results: Dict) -> Dict[str, Any]:
    """Analyze trapping sweep results."""
    
    analysis = {
        'free_baseline': [],
        '1d_traps': [],
        '2d_traps': [],
        'summary': {},
    }
    
    for test in results['tests']:
        geometry = test['geometry']
        
        entry = {
            'config': test['config'],
            'seed': test['seed'],
            'escaped': test['escaped'],
            'escape_T': test['escape_T'],
            'final_D_eff': test['final_metrics']['D_eff'],
            'final_r2': test['final_metrics']['r2'],
            'final_r3': test['final_metrics']['r3'],
            'final_anisotropy': test['final_metrics']['anisotropy'],
            'tau_leakage': test['final_metrics']['tau_leakage'],
        }
        
        if geometry == 'free':
            analysis['free_baseline'].append(entry)
        elif geometry == '1d_trap':
            analysis['1d_traps'].append(entry)
        elif geometry == '2d_trap':
            analysis['2d_traps'].append(entry)
    
    # Compute summary statistics
    free_escape_times = [t['escape_T'] for t in analysis['free_baseline'] if t['escape_T']]
    analysis['summary']['free_mean_escape_T'] = np.mean(free_escape_times) if free_escape_times else None
    analysis['summary']['free_all_escaped'] = all(t['escaped'] for t in analysis['free_baseline'])
    
    # Trapping effectiveness
    analysis['summary']['1d_escape_rate'] = sum(1 for t in analysis['1d_traps'] if t['escaped']) / len(analysis['1d_traps']) if analysis['1d_traps'] else 0
    analysis['summary']['2d_escape_rate'] = sum(1 for t in analysis['2d_traps'] if t['escaped']) / len(analysis['2d_traps']) if analysis['2d_traps'] else 0
    
    # Best trapping configurations
    analysis['summary']['best_1d_trap'] = min(analysis['1d_traps'], key=lambda x: x['final_D_eff']) if analysis['1d_traps'] else None
    analysis['summary']['best_2d_trap'] = min(analysis['2d_traps'], key=lambda x: x['final_D_eff']) if analysis['2d_traps'] else None
    
    return analysis


def print_summary(analysis: Dict):
    """Print formatted summary of results."""
    
    print("\n" + "="*70)
    print("  DIMENSIONAL TRAPPING RESULTS SUMMARY")
    print("="*70)
    
    # Free baseline
    print("\n--- FREE BASELINE ---")
    print(f"{'Seed':<8} {'Escaped':<10} {'Escape T':<12} {'Final D_eff':<12}")
    print("-" * 45)
    for entry in analysis['free_baseline']:
        esc_t = f"{entry['escape_T']:.1f}" if entry['escape_T'] else "N/A"
        print(f"{entry['seed']:<8} {str(entry['escaped']):<10} {esc_t:<12} {entry['final_D_eff']:.3f}")
    
    if analysis['summary']['free_mean_escape_T']:
        print(f"\nMean escape T: {analysis['summary']['free_mean_escape_T']:.1f}")
    
    # 1D traps
    print("\n--- 1D TRAP RESULTS ---")
    print(f"{'τ_bound':<8} {'Width':<8} {'Escaped':<10} {'D_eff':<10} {'r2':<8} {'τ_leak':<8}")
    print("-" * 55)
    for entry in analysis['1d_traps']:
        cfg = entry['config']
        print(f"{cfg['boundary_tau']:<8.1f} {cfg['channel_width']:<8} {str(entry['escaped']):<10} "
              f"{entry['final_D_eff']:<10.3f} {entry['final_r2']:<8.3f} {entry['tau_leakage']:<8.3f}")
    
    print(f"\n1D escape rate: {analysis['summary']['1d_escape_rate']*100:.0f}%")
    
    # 2D traps
    print("\n--- 2D TRAP RESULTS ---")
    print(f"{'τ_bound':<8} {'Thick':<8} {'Escaped':<10} {'D_eff':<10} {'r3':<8} {'τ_leak':<8}")
    print("-" * 55)
    for entry in analysis['2d_traps']:
        cfg = entry['config']
        print(f"{cfg['boundary_tau']:<8.1f} {cfg['sheet_thickness']:<8} {str(entry['escaped']):<10} "
              f"{entry['final_D_eff']:<10.3f} {entry['final_r3']:<8.3f} {entry['tau_leakage']:<8.3f}")
    
    print(f"\n2D escape rate: {analysis['summary']['2d_escape_rate']*100:.0f}%")
    
    # Overall conclusion
    print("\n" + "="*70)
    print("  CONCLUSION")
    print("="*70)
    
    if analysis['summary']['free_all_escaped']:
        print("\nFree baseline: All seeds escaped to 3D (confirmed natural 3D preference)")
    
    if analysis['summary']['1d_escape_rate'] < 1.0:
        best = analysis['summary']['best_1d_trap']
        print(f"\n1D trapping: EFFECTIVE")
        print(f"  Best config: τ={best['config']['boundary_tau']}, width={best['config']['channel_width']}")
        print(f"  Final D_eff: {best['final_D_eff']:.3f}")
    else:
        print("\n1D trapping: INEFFECTIVE (all escaped)")
    
    if analysis['summary']['2d_escape_rate'] < 1.0:
        best = analysis['summary']['best_2d_trap']
        print(f"\n2D trapping: EFFECTIVE")
        print(f"  Best config: τ={best['config']['boundary_tau']}, thickness={best['config']['sheet_thickness']}")
        print(f"  Final D_eff: {best['final_D_eff']:.3f}")
    else:
        print("\n2D trapping: INEFFECTIVE (all escaped)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Dimensional Trapping Test')
    parser.add_argument('--mode', choices=['single', 'sweep'], default='sweep',
                       help='Mode: single test or full sweep')
    parser.add_argument('--geometry', choices=['free', '1d_trap', '2d_trap'], default='free',
                       help='Geometry for single test')
    parser.add_argument('--target-T', type=float, default=500.0,
                       help='Target simulation time')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--size', type=int, default=32,
                       help='Grid size')
    parser.add_argument('--boundary-tau', type=float, default=0.6,
                       help='Boundary τ value')
    parser.add_argument('--channel-width', type=int, default=5,
                       help='Channel width for 1D trap')
    parser.add_argument('--sheet-thickness', type=int, default=5,
                       help='Sheet thickness for 2D trap')
    
    args = parser.parse_args()
    
    output_dir = '/app/backend/qmrt_topology/papers/dimensional_trapping'
    os.makedirs(output_dir, exist_ok=True)
    
    if args.mode == 'single':
        result = run_single_trap_test(
            geometry=args.geometry,
            boundary_tau=args.boundary_tau,
            channel_width=args.channel_width,
            sheet_thickness=args.sheet_thickness,
            target_T=args.target_T,
            seed=args.seed,
            size=args.size,
        )
        
        output_file = f'{output_dir}/single_{args.geometry}_seed{args.seed}.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {output_file}")
        
    else:  # sweep
        results = run_dimensional_trapping_sweep(
            target_T=args.target_T,
            seeds=[42, 123, 456],
            size=args.size,
        )
        
        analysis = analyze_results(results)
        print_summary(analysis)
        
        # Save results
        output_file = f'{output_dir}/trapping_sweep_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nFull results saved to: {output_file}")
        
        analysis_file = f'{output_dir}/trapping_analysis.json'
        with open(analysis_file, 'w') as f:
            # Convert numpy types for JSON
            def convert(obj):
                if isinstance(obj, dict):
                    return {k: convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert(i) for i in obj]
                elif isinstance(obj, (np.bool_, bool)):
                    return bool(obj)
                elif isinstance(obj, (np.integer,)):
                    return int(obj)
                elif isinstance(obj, (np.floating,)):
                    return float(obj)
                elif obj is None:
                    return None
                return obj
            json.dump(convert(analysis), f, indent=2)
        print(f"Analysis saved to: {analysis_file}")
    
    return results if args.mode == 'sweep' else result


if __name__ == "__main__":
    main()
