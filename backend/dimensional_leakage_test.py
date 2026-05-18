"""
Higher-Dimensional Leakage / Persistent Gravity Test
=====================================================

PURPOSE: Test whether a higher-dimensional leakage channel keeps the
3D region in persistent non-equilibrium with active gravity-like drift.

KEY HYPOTHESIS:
  If a saturated 3D region can leak pressure into a higher-dimensional
  channel (W dimension), then:
  - Local pressure gradients persist longer
  - Gravity-like drift/accretion remains active
  - Sink nodes become "persistent leakage interfaces"
  - Equilibrium is never truly reached locally

REFINED FRAMEWORK:
  The medium does not stop filling. It reaches local balance, then
  pressure redistributes into a broader degree-of-freedom state.
  
  Underfilled → Filling → Local saturation → Leakage/overflow → 
  Higher-state access → New filling cycle

BLACK HOLE INTERPRETATION:
  A black-hole-like node is a localized region where 3D medium pressure
  remains above local capacity and continuously couples to a deeper or
  higher-dimensional channel. It is a PERSISTENT LEAKAGE INTERFACE,
  not just a static mass.

COMPARISON:
  - Closed 3D: filling peak → equilibrium → drift weakens
  - Leaky 4D:  filling peak → sustained gradient → continued drift

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label, center_of_mass
from typing import Dict, List, Any, Tuple
import time
import json
import os


class LeakageSimulator:
    """
    Simulator with controllable higher-dimensional leakage.
    
    Models pressure bleeding from 3D into a 4th dimension (W),
    testing whether this maintains persistent non-equilibrium.
    """
    
    def __init__(self, 
                 size: int = 24,  # Smaller for 4D memory
                 dt: float = 0.12, 
                 seed: int = 42,
                 leakage_mode: str = 'closed',  # 'closed', 'weak', 'medium', 'strong'
                 w_size: int = 8):  # Size of W dimension
        """
        Initialize with leakage configuration.
        
        Parameters:
        -----------
        leakage_mode : str
            'closed': No W dimension (pure 3D)
            'weak': Small pressure bleed into W
            'medium': Sustained bleed
            'strong': Rapid pressure escape
        w_size : int
            Size of the W dimension (if active)
        """
        
        self.size = size
        self.dt = dt
        self.seed = seed
        self.leakage_mode = leakage_mode
        self.w_size = w_size if leakage_mode != 'closed' else 1
        
        np.random.seed(seed)
        
        # Leakage parameters
        self.leakage_rates = {
            'closed': 0.0,
            'weak': 0.01,
            'medium': 0.05,
            'strong': 0.15,
        }
        self.leakage_rate = self.leakage_rates[leakage_mode]
        
        # Regulated Recovery v1.1 (LOCKED)
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # 4D fields (X, Y, Z, W)
        shape = (size, size, size, self.w_size)
        
        # Initialize with structure in 3D center, uniform in W
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        
        # Seed perturbations in 3D center
        center = size // 2
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    d = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    if d < 5:
                        self.psi_r[x, y, z, :] += np.random.randn() * 0.1
                        self.psi_i[x, y, z, :] += np.random.randn() * 0.1
        
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # W-dimension coupling (starts weak, can be activated)
        self.w_coupling = 0.0 if leakage_mode == 'closed' else 0.1
        
        # Tracking
        self.total_creations = 0
        self.total_leakage = 0.0  # Accumulated pressure leaked to W
        self.metrics_history = []
        
        # Memory tracking
        n_cells = size**3 * self.w_size
        mem_mb = n_cells * 8 * 5 / 1e6
        print(f"Leakage Test initialized")
        print(f"  Mode: {leakage_mode} (rate={self.leakage_rate})")
        print(f"  Grid: {size}³ × {self.w_size} (W) = {n_cells:,} cells (~{mem_mb:.0f} MB)")
    
    def _laplacian_4d(self, f, include_w: bool = True):
        """
        4D Laplacian with controllable W coupling.
        """
        # 3D Laplacian (always active)
        lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) +
               np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) +
               np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 6 * f)
        
        # W coupling (if active and multi-cell)
        if include_w and self.w_size > 1 and self.w_coupling > 0:
            lap_w = (np.roll(f, 1, axis=3) + np.roll(f, -1, axis=3) - 2 * f)
            lap += self.w_coupling * lap_w
        
        return lap
    
    def compute_leakage_flux(self) -> float:
        """
        Compute pressure flux from 3D into W dimension.
        
        This is the KEY MECHANISM for persistent non-equilibrium.
        """
        if self.leakage_mode == 'closed' or self.w_size <= 1:
            return 0.0
        
        # Local pressure in 3D
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        potential = self.psi_r**2 + self.psi_i**2
        local_pressure = kinetic + potential + (self.tau - 1.0) * 5
        
        # Pressure gradient in W direction
        if self.w_size > 1:
            p_grad_w = np.gradient(local_pressure, axis=3)
            flux = self.leakage_rate * np.mean(np.abs(p_grad_w))
        else:
            flux = 0.0
        
        return float(flux)
    
    def apply_leakage(self):
        """
        Apply pressure leakage from high-pressure 3D regions into W.
        
        This keeps the 3D region from reaching true equilibrium.
        """
        if self.leakage_mode == 'closed' or self.w_size <= 1:
            return
        
        # Identify high-pressure regions
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        local_pressure = kinetic + (self.tau - 1.0) * 5
        
        # Pressure threshold for leakage
        threshold = np.percentile(local_pressure, 80)
        high_p_mask = local_pressure > threshold
        
        if np.any(high_p_mask):
            # Leak energy from high-pressure 3D cells into adjacent W cells
            leak_amount = self.leakage_rate * (local_pressure[high_p_mask] - threshold)
            
            # Reduce velocity in high-pressure regions (energy leaves)
            self.psi_r_dot[high_p_mask] *= (1 - self.leakage_rate * 0.1)
            self.psi_i_dot[high_p_mask] *= (1 - self.leakage_rate * 0.1)
            
            # Transfer to W neighbors (simplified model)
            if self.w_size > 1:
                # Energy spreads in W direction
                self.psi_r = 0.99 * self.psi_r + 0.005 * (np.roll(self.psi_r, 1, axis=3) + np.roll(self.psi_r, -1, axis=3))
            
            self.total_leakage += float(np.sum(leak_amount))
    
    def step(self):
        """Advance simulation with leakage dynamics."""
        self.step_count += 1
        self.global_T += self.dt
        
        # τ dynamics
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        if self.damping_to_tau > 0:
            self.tau += self.damping_to_tau * damped_energy
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Creation events (in 3D, any W slice)
        high_tau_mask = self.tau > self.tau_creation_threshold
        if np.any(high_tau_mask):
            n_candidates = np.sum(high_tau_mask)
            create_prob = self.creation_rate * (self.tau[high_tau_mask] - self.tau_creation_threshold)
            create_mask = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask):
                coords = np.array(np.where(high_tau_mask)).T[create_mask]
                for coord in coords[:2]:
                    self._inject_perturbation(*coord)
                    self.tau[tuple(coord)] = 1.0
                    self.total_creations += 1
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._laplacian_4d(self.psi_r)
        lap_i = self._laplacian_4d(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        # Apply leakage (the key mechanism)
        self.apply_leakage()
    
    def _inject_perturbation(self, cx, cy, cz, cw):
        """Inject perturbation."""
        x, y, z, w = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), np.arange(self.w_size),
            indexing='ij'
        )
        r_sq = (x-cx)**2 + (y-cy)**2 + (z-cz)**2 + (w-cw)**2
        perturbation = np.exp(-r_sq / 8)
        phase = np.random.uniform(0, 2*np.pi)
        
        self.psi_r += 0.1 * perturbation * np.cos(phase)
        self.psi_i += 0.1 * perturbation * np.sin(phase)
    
    def compute_3d_metrics(self) -> Dict[str, Any]:
        """
        Compute metrics for the 3D projection.
        
        This measures whether 3D remains in non-equilibrium.
        """
        # Project to 3D by averaging over W
        psi_r_3d = np.mean(self.psi_r, axis=3)
        psi_i_3d = np.mean(self.psi_i, axis=3)
        psi_r_dot_3d = np.mean(self.psi_r_dot, axis=3)
        psi_i_dot_3d = np.mean(self.psi_i_dot, axis=3)
        tau_3d = np.mean(self.tau, axis=3)
        
        # Topology field (3D)
        amp = np.sqrt(psi_r_3d**2 + psi_i_3d**2) + 1e-10
        phase = np.arctan2(psi_i_3d, psi_r_3d)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Pressure field (3D)
        kinetic = psi_r_dot_3d**2 + psi_i_dot_3d**2
        local_pressure = kinetic + psi_r_3d**2 + psi_i_3d**2 + (tau_3d - 1.0) * 5
        
        # Pressure gradient (key metric for non-equilibrium)
        grad_p = np.sqrt(
            np.gradient(local_pressure, axis=0)**2 +
            np.gradient(local_pressure, axis=1)**2 +
            np.gradient(local_pressure, axis=2)**2
        )
        
        # Sink nodes (high-pressure concentrations)
        threshold = np.percentile(local_pressure, 95)
        labeled, n_sinks = label(local_pressure > threshold)
        
        # Topology clusters for drift
        top_threshold = np.percentile(topology, 90)
        top_labeled, n_clusters = label(topology > top_threshold)
        
        clusters = []
        for i in range(1, min(n_clusters + 1, 20)):  # Limit for speed
            mask = (top_labeled == i)
            if np.sum(mask) >= 5:
                com = center_of_mass(topology, top_labeled, i)
                mass = np.sum(topology[mask])
                clusters.append({'com': list(com), 'mass': float(mass)})
        
        # Saturation metrics
        topology_density = np.mean(topology)
        saturation_ratio = topology_density / 0.1  # Normalized
        
        # Leakage flux
        leakage_flux = self.compute_leakage_flux()
        
        return {
            'T': self.global_T,
            'mean_pressure': float(np.mean(local_pressure)),
            'max_pressure': float(np.max(local_pressure)),
            'mean_gradient': float(np.mean(grad_p)),
            'max_gradient': float(np.max(grad_p)),
            'n_sink_nodes': n_sinks,
            'n_clusters': len(clusters),
            'topology_density': float(topology_density),
            'saturation_ratio': float(saturation_ratio),
            'tau_mean': float(np.mean(tau_3d)),
            'tau_max': float(np.max(tau_3d)),
            'leakage_flux': leakage_flux,
            'total_leakage': self.total_leakage,
            'clusters': clusters,
        }
    
    def compute_drift(self, prev_clusters: List, curr_clusters: List) -> float:
        """Compute topology drift between timesteps."""
        if not prev_clusters or not curr_clusters:
            return 0.0
        
        total_drift = 0.0
        n_matched = 0
        
        for prev in prev_clusters:
            prev_com = np.array(prev['com'])
            min_dist = float('inf')
            
            for curr in curr_clusters:
                curr_com = np.array(curr['com'])
                dist = np.linalg.norm(curr_com - prev_com)
                if dist < min_dist and dist < 8:
                    min_dist = dist
            
            if min_dist < 8:
                total_drift += min_dist
                n_matched += 1
        
        return total_drift / max(1, n_matched)


def run_leakage_comparison(
    max_wall_seconds: float = 90.0,
    size: int = 20,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run comparison between closed 3D and leaky 4D.
    """
    print("=" * 70)
    print("  HIGHER-DIMENSIONAL LEAKAGE / PERSISTENT GRAVITY TEST")
    print("=" * 70)
    print()
    print("HYPOTHESIS: Leakage into W keeps 3D in persistent non-equilibrium")
    print("            with active gravity-like drift.")
    print()
    print("Comparison:")
    print("  Closed 3D: filling → equilibrium → drift weakens")
    print("  Leaky 4D:  filling → sustained gradient → continued drift")
    print()
    
    results = {}
    modes = ['closed', 'weak', 'medium']
    target_T = 400.0
    
    for mode in modes:
        print()
        print(f"{'='*60}")
        print(f"  MODE: {mode.upper()}")
        print(f"{'='*60}")
        
        w_size = 1 if mode == 'closed' else 4
        sim = LeakageSimulator(
            size=size, dt=0.12, seed=seed,
            leakage_mode=mode, w_size=w_size
        )
        
        t_start = time.time()
        measure_interval = 25.0
        last_measure = 0.0
        prev_clusters = None
        
        mode_metrics = []
        
        print()
        print(f"{'T':>6} | {'Gradient':>8} | {'Sinks':>5} | {'Drift':>6} | {'Leakage':>8} | {'SatRatio':>8}")
        print("-" * 60)
        
        while sim.global_T < target_T:
            elapsed = time.time() - t_start
            if elapsed >= max_wall_seconds / len(modes) - 5:
                print(f"  [Wall time limit at T={sim.global_T:.1f}]")
                break
            
            sim.step()
            
            if sim.global_T - last_measure >= measure_interval:
                last_measure = sim.global_T
                metrics = sim.compute_3d_metrics()
                
                drift = sim.compute_drift(prev_clusters, metrics['clusters'])
                metrics['drift'] = drift
                mode_metrics.append(metrics)
                
                print(f"{sim.global_T:>6.1f} | {metrics['mean_gradient']:>8.4f} | "
                      f"{metrics['n_sink_nodes']:>5} | {drift:>6.2f} | "
                      f"{metrics['leakage_flux']:>8.4f} | {metrics['saturation_ratio']:>8.3f}")
                
                prev_clusters = metrics['clusters']
        
        results[mode] = {
            'metrics': mode_metrics,
            'final_T': sim.global_T,
            'total_leakage': sim.total_leakage,
        }
    
    # Analysis
    print()
    print("=" * 70)
    print("  COMPARISON ANALYSIS")
    print("=" * 70)
    
    for mode in modes:
        metrics = results[mode]['metrics']
        if not metrics:
            continue
        
        # Split into early (filling) and late (post-filling) phases
        mid_point = len(metrics) // 2
        early = metrics[:mid_point] if mid_point > 0 else metrics
        late = metrics[mid_point:] if mid_point > 0 else metrics
        
        early_gradient = np.mean([m['mean_gradient'] for m in early])
        late_gradient = np.mean([m['mean_gradient'] for m in late])
        early_drift = np.mean([m['drift'] for m in early])
        late_drift = np.mean([m['drift'] for m in late])
        
        gradient_retention = late_gradient / (early_gradient + 0.001)
        drift_retention = late_drift / (early_drift + 0.001)
        
        print(f"\n{mode.upper()}:")
        print(f"  Early gradient: {early_gradient:.4f}")
        print(f"  Late gradient:  {late_gradient:.4f}")
        print(f"  Gradient retention: {100*gradient_retention:.1f}%")
        print(f"  Early drift: {early_drift:.2f}")
        print(f"  Late drift:  {late_drift:.2f}")
        print(f"  Drift retention: {100*drift_retention:.1f}%")
        
        results[mode]['early_gradient'] = early_gradient
        results[mode]['late_gradient'] = late_gradient
        results[mode]['gradient_retention'] = gradient_retention
        results[mode]['drift_retention'] = drift_retention
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    closed_retention = results.get('closed', {}).get('gradient_retention', 0)
    leaky_retention = results.get('medium', {}).get('gradient_retention', 0)
    
    if leaky_retention > closed_retention * 1.2:
        verdict = "CONFIRMED: Leakage maintains persistent non-equilibrium"
    elif leaky_retention > closed_retention:
        verdict = "PARTIAL: Leakage shows some persistence improvement"
    else:
        verdict = "NOT CONFIRMED: No clear leakage effect"
    
    print(f"\n{verdict}")
    print()
    print(f"Closed gradient retention: {100*closed_retention:.1f}%")
    print(f"Leaky gradient retention:  {100*leaky_retention:.1f}%")
    
    # Save
    output_dir = '/app/backend/qmrt_topology/papers/dimensional_leakage'
    os.makedirs(output_dir, exist_ok=True)
    
    save_results = {
        'verdict': verdict,
        'modes': {mode: {
            'gradient_retention': results[mode].get('gradient_retention', 0),
            'drift_retention': results[mode].get('drift_retention', 0),
            'total_leakage': results[mode].get('total_leakage', 0),
        } for mode in modes if mode in results}
    }
    
    with open(f'{output_dir}/leakage_comparison.json', 'w') as f:
        json.dump(save_results, f, indent=2)
    
    print(f"\nResults saved to: {output_dir}/leakage_comparison.json")
    
    return results


def main():
    results = run_leakage_comparison(
        max_wall_seconds=100.0,
        size=20,
        seed=42,
    )
    return results


if __name__ == "__main__":
    main()
