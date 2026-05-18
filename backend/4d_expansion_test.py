"""
4D Dimensional Expansion Test
==============================

PURPOSE: Test whether the QMRT medium expands into 4D when available.

CRITICAL QUESTION:
  If a fourth spatial degree of freedom is available, does D_eff rise above 3?

HYPOTHESIS:
  Based on 3D saturation (D_eff ≈ 2.999), we expect D_eff_4D > 3.0 in free 4D medium.

PASS CONDITIONS:
  - Weak pass: D_eff > 3.2 and λ4/λ1 > 0.1
  - Strong pass: D_eff > 3.7 approaching 4.0

METRICS:
  D_eff_4D = (λ1 + λ2 + λ3 + λ4)² / (λ1² + λ2² + λ3² + λ4²)

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.linalg import eigh
from typing import Dict, Any
import time
import json
import os


class Simulator4D:
    """
    4D QMRT simulator with Regulated Recovery v1.1 physics.
    
    Adapted for 4-dimensional spatial grid.
    Memory-conscious: uses smaller grids.
    """
    
    def __init__(self, size: int = 12, dt: float = 0.12, seed: int = 42):
        """
        Initialize 4D simulator.
        
        Parameters:
        -----------
        size : int
            Grid size in each dimension. 12⁴ = 20,736 cells (manageable).
            16⁴ = 65,536 cells (larger but still feasible).
        """
        
        self.size = size
        self.dt = dt
        self.ndim = 4
        
        np.random.seed(seed)
        
        # Regulated Recovery v1.1 parameters (same as 3D)
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
        
        # 4D fields
        shape = (size, size, size, size)
        self.psi_r = np.ones(shape) + np.random.randn(*shape) * 0.01
        self.psi_i = np.random.randn(*shape) * 0.01
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Counters
        self.total_creations = 0
        
        # Memory usage estimate
        n_cells = size ** 4
        mem_per_field = n_cells * 8 / 1e6  # MB (float64)
        total_mem = mem_per_field * 5  # 5 main fields
        print(f"  Grid: {size}⁴ = {n_cells:,} cells")
        print(f"  Memory estimate: ~{total_mem:.1f} MB for main fields")
    
    def _laplacian_4d(self, f):
        """
        4D discrete Laplacian.
        
        ∇²f = sum over all 4 axes of (f[+1] + f[-1] - 2f)
        In 4D: 8 neighbors, so -8f in the center term.
        """
        lap = -8 * f
        for axis in range(4):
            lap += np.roll(f, 1, axis=axis) + np.roll(f, -1, axis=axis)
        return lap
    
    def _inject_perturbation_4d(self, cx, cy, cz, cw):
        """
        Inject a localized perturbation in 4D.
        
        Simplified compared to 3D vortex: just a Gaussian bump.
        4D vortices are topologically more complex.
        """
        coords = np.meshgrid(
            np.arange(self.size), np.arange(self.size),
            np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        x, y, z, w = coords
        
        # 4D distance from center
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2 + (w - cw)**2
        
        # Gaussian perturbation
        sigma = 2.0
        perturbation = np.exp(-r_sq / (2 * sigma**2))
        
        # Random phase
        phase = np.random.uniform(0, 2 * np.pi)
        
        self.psi_r += 0.1 * perturbation * np.cos(phase)
        self.psi_i += 0.1 * perturbation * np.sin(phase)
        self.total_creations += 1
    
    def step(self):
        """Advance simulation by one timestep."""
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
        
        # Creation events
        high_tau_mask = self.tau > self.tau_creation_threshold
        if np.any(high_tau_mask):
            n_candidates = np.sum(high_tau_mask)
            create_prob = self.creation_rate * (self.tau[high_tau_mask] - self.tau_creation_threshold)
            create_mask_1d = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask_1d):
                coords = np.array(np.where(high_tau_mask)).T
                create_coords = coords[create_mask_1d]
                
                for coord in create_coords[:2]:  # Limit to 2 per step
                    cx, cy, cz, cw = coord
                    self._inject_perturbation_4d(cx, cy, cz, cw)
                    self.tau[cx, cy, cz, cw] = 1.0
        
        # Wave equation with 4D Laplacian
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._laplacian_4d(self.psi_r)
        lap_i = self._laplacian_4d(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def compute_d_eff_4d(self) -> Dict[str, Any]:
        """
        Compute 4D effective dimension.
        
        D_eff_4D = (λ1 + λ2 + λ3 + λ4)² / (λ1² + λ2² + λ3² + λ4²)
        
        Ranges from 1 (line) to 4 (full 4D isotropy).
        """
        # Compute activity field (gradient magnitude in 4D)
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        # Gradient in each of 4 directions
        grad_sq = 0
        for axis in range(4):
            grad = np.angle(np.exp(1j * (np.roll(phase, -1, axis=axis) - phase)))
            grad_sq += grad**2
        topology = np.sqrt(grad_sq)
        
        # Active cells (top 10% of activity)
        threshold = np.percentile(topology, 90)
        active_mask = topology > threshold
        n_active = np.sum(active_mask)
        
        if n_active < 20:
            return {'D_eff': 0, 'valid': False, 'n_active': int(n_active)}
        
        # Get active coordinates (4D)
        active_coords = np.array(np.where(active_mask)).T  # Shape: (n_active, 4)
        
        # Weights
        weights = topology[active_mask]
        weights = weights / np.sum(weights)
        
        # Centroid
        centroid = np.average(active_coords, axis=0, weights=weights)
        
        # 4x4 covariance matrix
        centered = active_coords - centroid
        cov = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                cov[i, j] = np.sum(weights * centered[:, i] * centered[:, j])
        
        # Eigenvalues
        eigenvalues, _ = eigh(cov)
        eigenvalues = np.sort(eigenvalues)[::-1]  # Descending
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        
        lambda1, lambda2, lambda3, lambda4 = eigenvalues
        
        # D_eff_4D = (Σλ)² / Σλ²
        sum_lambda = lambda1 + lambda2 + lambda3 + lambda4
        sum_lambda_sq = lambda1**2 + lambda2**2 + lambda3**2 + lambda4**2
        D_eff = sum_lambda**2 / sum_lambda_sq if sum_lambda_sq > 0 else 1.0
        
        # Ratios
        r2 = lambda2 / lambda1 if lambda1 > 0 else 0
        r3 = lambda3 / lambda1 if lambda1 > 0 else 0
        r4 = lambda4 / lambda1 if lambda1 > 0 else 0
        
        # 4D anisotropy
        anisotropy = 1 - (lambda4 / lambda1) if lambda1 > 0 else 1.0
        
        return {
            'D_eff': float(D_eff),
            'lambda1': float(lambda1),
            'lambda2': float(lambda2),
            'lambda3': float(lambda3),
            'lambda4': float(lambda4),
            'r2': float(r2),
            'r3': float(r3),
            'r4': float(r4),
            'anisotropy': float(anisotropy),
            'n_active': int(n_active),
            'valid': True,
        }


def run_4d_test(
    size: int = 12,
    target_T: float = 200.0,
    max_wall_seconds: float = 90.0,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run 4D dimensional expansion test.
    """
    print("=" * 70)
    print("  4D DIMENSIONAL EXPANSION TEST")
    print("=" * 70)
    print()
    print("CRITICAL QUESTION: Does D_eff rise above 3.0 in 4D?")
    print()
    print("Pass conditions:")
    print("  Weak pass:   D_eff > 3.2, λ4/λ1 > 0.1")
    print("  Strong pass: D_eff > 3.7")
    print()
    
    print(f"Parameters: size={size}⁴, target_T={target_T}, seed={seed}")
    print()
    
    sim = Simulator4D(size=size, dt=0.12, seed=seed)
    print()
    
    t_start = time.time()
    measure_interval = 20.0
    last_measure = 0.0
    
    results_history = []
    
    print(f"{'T':>6} | {'D_eff':>7} | {'r2':>5} | {'r3':>5} | {'r4':>5} | {'n_active':>8} | Status")
    print("-" * 70)
    
    while sim.global_T < target_T:
        # Check wall time
        if time.time() - t_start > max_wall_seconds:
            print(f"\nWall time limit ({max_wall_seconds}s) reached at T={sim.global_T:.1f}")
            break
        
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            metrics = sim.compute_d_eff_4d()
            
            if metrics['valid']:
                results_history.append({
                    'T': sim.global_T,
                    **metrics
                })
                
                d_eff = metrics['D_eff']
                r4 = metrics['r4']
                
                if d_eff > 3.7:
                    status = "STRONG 4D"
                elif d_eff > 3.2:
                    status = "4D EXPANSION"
                elif d_eff > 3.0:
                    status = "above 3D"
                else:
                    status = "≤3D"
                
                print(f"{sim.global_T:>6.1f} | {d_eff:>7.4f} | {metrics['r2']:>5.3f} | "
                      f"{metrics['r3']:>5.3f} | {r4:>5.3f} | {metrics['n_active']:>8} | {status}")
    
    # Analysis
    print()
    print("=" * 70)
    print("  RESULTS ANALYSIS")
    print("=" * 70)
    
    if not results_history:
        print("\nNo valid measurements obtained.")
        return {'success': False, 'reason': 'no_data'}
    
    d_eff_values = [r['D_eff'] for r in results_history]
    r4_values = [r['r4'] for r in results_history]
    
    d_eff_mean = np.mean(d_eff_values)
    d_eff_max = np.max(d_eff_values)
    r4_mean = np.mean(r4_values)
    
    print(f"\nD_eff statistics:")
    print(f"  Mean: {d_eff_mean:.4f}")
    print(f"  Max:  {d_eff_max:.4f}")
    print(f"  Min:  {np.min(d_eff_values):.4f}")
    print()
    print(f"Fourth dimension engagement (r4 = λ4/λ1):")
    print(f"  Mean: {r4_mean:.4f}")
    print(f"  Max:  {np.max(r4_values):.4f}")
    print()
    
    # Verdict
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    exceeded_3 = sum(1 for d in d_eff_values if d > 3.0) / len(d_eff_values)
    exceeded_3_2 = sum(1 for d in d_eff_values if d > 3.2) / len(d_eff_values)
    exceeded_3_7 = sum(1 for d in d_eff_values if d > 3.7) / len(d_eff_values)
    
    print(f"\nD_eff > 3.0: {100*exceeded_3:.0f}% of measurements")
    print(f"D_eff > 3.2: {100*exceeded_3_2:.0f}% of measurements")
    print(f"D_eff > 3.7: {100*exceeded_3_7:.0f}% of measurements")
    print()
    
    if exceeded_3_7 > 0.5:
        verdict = "STRONG PASS"
        interpretation = "The medium saturates at ~4D when 4 dimensions are available."
    elif exceeded_3_2 > 0.5:
        verdict = "WEAK PASS"
        interpretation = "The medium expands significantly into 4D."
    elif exceeded_3 > 0.5:
        verdict = "MARGINAL"
        interpretation = "The medium shows some 4D expansion but not saturating."
    else:
        verdict = "NOT CONFIRMED"
        interpretation = "The medium does not significantly expand into 4D."
    
    print(f"VERDICT: {verdict}")
    print(f"  {interpretation}")
    print()
    
    # Comparison to 3D
    print("Comparison to 3D saturation test:")
    print(f"  3D test: D_eff = 2.999 (saturated at 3.0 ceiling)")
    print(f"  4D test: D_eff = {d_eff_mean:.3f} (max = {d_eff_max:.3f})")
    
    if d_eff_max > 3.0:
        print()
        print("  ★ D_eff EXCEEDS 3.0 — The medium uses the 4th dimension!")
        print("  ★ This confirms: 3D was a grid-limited saturation, not a preferred state.")
    
    result = {
        'verdict': verdict,
        'interpretation': interpretation,
        'd_eff_mean': d_eff_mean,
        'd_eff_max': d_eff_max,
        'r4_mean': r4_mean,
        'exceeded_3': exceeded_3,
        'exceeded_3_2': exceeded_3_2,
        'exceeded_3_7': exceeded_3_7,
        'history': results_history,
        'config': {
            'size': size,
            'target_T': target_T,
            'seed': seed,
        }
    }
    
    # Save results
    output_dir = '/app/backend/qmrt_topology/papers'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/4d_expansion_results.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print()
    print(f"Results saved to: {output_dir}/4d_expansion_results.json")
    
    return result


def main():
    """Run 4D test with conservative parameters first."""
    
    # First test: small grid, short time
    print("Running 4D expansion test (small grid first)...")
    print()
    
    result = run_4d_test(
        size=12,  # 12⁴ = 20,736 cells
        target_T=200.0,
        max_wall_seconds=90.0,
        seed=42,
    )
    
    return result


if __name__ == "__main__":
    main()
