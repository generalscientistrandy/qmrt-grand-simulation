"""
Dimensional Unlocking / Oversaturation Test
=============================================

PURPOSE: Test whether defect saturation in a lower-dimensional phase
can trigger activation of the next degree of freedom.

KEY INSIGHT: Dimensions are not separated by walls. They are separated
by UNAVAILABLE degrees of freedom. When topology/defect density saturates
the available dimensions, pressure builds until a transverse degree of
freedom ACTIVATES.

MECHANISM:
  1D active → defect saturation → τ pressure rises → Y-dimension unlocks
  2D active → network saturation → strain accumulates → Z-dimension unlocks
  3D active → volumetric expansion → possible 4D leakage

IMPLEMENTATION:
  - Dimension activation weights: ax, ay, az (0 = suppressed, 1 = fully active)
  - Laplacian scaled by activation: lap = ax*lap_x + ay*lap_y + az*lap_z
  - Pressure metric = defect_density + τ_pressure + strain_energy
  - Unlock when pressure > threshold

NO FAKE WALLS: Dimensions are not blocked by barriers; they are simply
not dynamically available yet until internal pressure unlocks them.

BASELINE: Regulated Recovery v1.1

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label
from scipy.linalg import eigh
from typing import Dict, List, Any, Tuple
import time
import json
import os


class DimensionalUnlockingSimulator:
    """
    Simulator for testing dimensional unlocking via oversaturation.
    
    Dimensions are not walled off — they are simply not dynamically
    available until internal pressure activates them.
    """
    
    def __init__(self, 
                 size: int = 32, 
                 dt: float = 0.12, 
                 seed: int = 42,
                 unlock_threshold: float = 2.0,
                 unlock_rate: float = 0.01,
                 start_1d: bool = True):
        """
        Initialize with configurable dimensional activation.
        
        Parameters:
        -----------
        unlock_threshold : float
            Pressure threshold to begin unlocking next dimension
        unlock_rate : float
            Rate at which activation weight increases once threshold exceeded
        start_1d : bool
            If True, start with only X dimension active
        """
        
        self.size = size
        self.dt = dt
        self.seed = seed
        
        np.random.seed(seed)
        
        # Regulated Recovery v1.1 parameters (LOCKED)
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Dimensional activation weights
        # 0 = suppressed (degree of freedom not available)
        # 1 = fully active (normal physics in that direction)
        if start_1d:
            self.ax = 1.0  # X always active
            self.ay = 0.0  # Y starts suppressed
            self.az = 0.0  # Z starts suppressed
        else:
            self.ax = 1.0
            self.ay = 1.0
            self.az = 1.0
        
        # Unlocking parameters
        self.unlock_threshold = unlock_threshold
        self.unlock_rate = unlock_rate
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Unlock event tracking
        self.y_unlock_T = None  # When Y dimension unlocked
        self.z_unlock_T = None  # When Z dimension unlocked
        self.unlock_history = []
        
        # Fields
        shape = (size, size, size)
        
        # Initialize with structure concentrated along X axis (1D-like)
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        
        if start_1d:
            # Seed initial perturbations along X axis only
            center = size // 2
            for x in range(size):
                # Perturbation decays away from X axis
                dist_from_axis = np.sqrt((np.arange(size) - center)**2)
                for y in range(size):
                    for z in range(size):
                        d = np.sqrt((y - center)**2 + (z - center)**2)
                        if d < 3:  # Only perturb near the axis
                            self.psi_r[x, y, z] += np.random.randn() * 0.1
                            self.psi_i[x, y, z] += np.random.randn() * 0.1
        else:
            self.psi_r += np.random.randn(*shape) * 0.01
            self.psi_i += np.random.randn(*shape) * 0.01
        
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Counters
        self.total_creations = 0
        
        # History
        self.metrics_history = []
        
        print(f"Dimensional Unlocking Test initialized")
        print(f"  Grid: {size}³")
        print(f"  Starting activation: ax={self.ax:.2f}, ay={self.ay:.2f}, az={self.az:.2f}")
        print(f"  Unlock threshold: {unlock_threshold}")
        print(f"  Unlock rate: {unlock_rate}")
    
    def _weighted_laplacian(self, f):
        """
        Compute Laplacian weighted by dimensional activation.
        
        This is the key mechanism: suppressed dimensions have reduced
        coupling, so the medium can't spread into them until they activate.
        """
        lap = np.zeros_like(f)
        
        # X direction (always active in this test)
        lap += self.ax * (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        
        # Y direction (may be suppressed)
        lap += self.ay * (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        
        # Z direction (may be suppressed)
        lap += self.az * (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        
        return lap
    
    def compute_dimensional_pressure(self) -> Dict[str, float]:
        """
        Compute the pressure metrics that drive dimensional unlocking.
        
        Pressure = defect_density + τ_pressure + strain_energy
        
        When pressure exceeds threshold, the next dimension unlocks.
        """
        # Defect density (topology concentration)
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Defect density: high topology concentration
        defect_density = np.mean(topology) / (np.std(topology) + 0.01)
        
        # τ pressure: how much τ is elevated above baseline
        tau_pressure = np.mean(self.tau - 1.0) * 10  # Scale factor
        tau_max_pressure = (np.max(self.tau) - 1.0) * 5
        
        # Strain energy: kinetic energy density
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        strain_energy = np.mean(kinetic) * 100  # Scale factor
        
        # Total pressure
        total_pressure = defect_density + tau_pressure + tau_max_pressure + strain_energy
        
        return {
            'defect_density': float(defect_density),
            'tau_pressure': float(tau_pressure),
            'tau_max_pressure': float(tau_max_pressure),
            'strain_energy': float(strain_energy),
            'total_pressure': float(total_pressure),
        }
    
    def check_and_apply_unlock(self, pressure: Dict[str, float]):
        """
        Check if pressure exceeds threshold and unlock next dimension.
        
        This is the core oversaturation mechanism.
        """
        total_p = pressure['total_pressure']
        
        # Check for Y unlock (1D → 2D)
        if self.ay < 1.0 and total_p > self.unlock_threshold:
            old_ay = self.ay
            self.ay = min(1.0, self.ay + self.unlock_rate)
            
            if old_ay == 0.0 and self.ay > 0.0:
                self.y_unlock_T = self.global_T
                self.unlock_history.append({
                    'T': self.global_T,
                    'event': 'Y_UNLOCK_START',
                    'pressure': total_p,
                    'ay': self.ay,
                })
                print(f"  *** Y DIMENSION UNLOCKING at T={self.global_T:.1f} (pressure={total_p:.2f})")
            
            if self.ay >= 1.0:
                self.unlock_history.append({
                    'T': self.global_T,
                    'event': 'Y_UNLOCK_COMPLETE',
                    'pressure': total_p,
                })
                print(f"  *** Y DIMENSION FULLY ACTIVE at T={self.global_T:.1f}")
        
        # Check for Z unlock (2D → 3D) - only after Y is substantially active
        if self.ay > 0.5 and self.az < 1.0 and total_p > self.unlock_threshold * 1.5:
            old_az = self.az
            self.az = min(1.0, self.az + self.unlock_rate)
            
            if old_az == 0.0 and self.az > 0.0:
                self.z_unlock_T = self.global_T
                self.unlock_history.append({
                    'T': self.global_T,
                    'event': 'Z_UNLOCK_START',
                    'pressure': total_p,
                    'az': self.az,
                })
                print(f"  *** Z DIMENSION UNLOCKING at T={self.global_T:.1f} (pressure={total_p:.2f})")
            
            if self.az >= 1.0:
                self.unlock_history.append({
                    'T': self.global_T,
                    'event': 'Z_UNLOCK_COMPLETE',
                    'pressure': total_p,
                })
                print(f"  *** Z DIMENSION FULLY ACTIVE at T={self.global_T:.1f}")
    
    def step(self):
        """Advance simulation with dimensional activation dynamics."""
        self.step_count += 1
        self.global_T += self.dt
        
        # τ dynamics (standard)
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
            create_mask = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask):
                coords = np.array(np.where(high_tau_mask)).T[create_mask]
                for coord in coords[:3]:
                    self._inject_perturbation(*coord)
                    self.tau[tuple(coord)] = 1.0
                    self.total_creations += 1
        
        # Wave equation with WEIGHTED Laplacian
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._weighted_laplacian(self.psi_r)
        lap_i = self._weighted_laplacian(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def _inject_perturbation(self, cx, cy, cz):
        """Inject perturbation at location."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), indexing='ij'
        )
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        perturbation = np.exp(-r_sq / 8)
        phase = np.random.uniform(0, 2 * np.pi)
        
        self.psi_r += 0.1 * perturbation * np.cos(phase)
        self.psi_i += 0.1 * perturbation * np.sin(phase)
    
    def compute_d_eff(self) -> float:
        """Compute effective dimensionality."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        threshold = np.percentile(topology, 90)
        active_mask = topology > threshold
        n_active = np.sum(active_mask)
        
        if n_active < 10:
            return 0.0
        
        coords = np.array(np.where(active_mask)).T
        weights = topology[active_mask] / np.sum(topology[active_mask])
        
        centroid = np.average(coords, axis=0, weights=weights)
        centered = coords - centroid
        
        cov = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                cov[i, j] = np.sum(weights * centered[:, i] * centered[:, j])
        
        eigenvalues = np.sort(np.linalg.eigvalsh(cov))[::-1]
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        
        sum_l = sum(eigenvalues)
        sum_l_sq = sum(e**2 for e in eigenvalues)
        
        return sum_l**2 / sum_l_sq if sum_l_sq > 0 else 1.0
    
    def get_full_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics."""
        pressure = self.compute_dimensional_pressure()
        d_eff = self.compute_d_eff()
        
        return {
            'T': self.global_T,
            'ax': self.ax,
            'ay': self.ay,
            'az': self.az,
            'D_eff': d_eff,
            'total_creations': self.total_creations,
            'tau_mean': float(np.mean(self.tau)),
            'tau_max': float(np.max(self.tau)),
            **pressure,
        }


def run_dimensional_unlocking_test(
    target_T: float = 2000.0,
    max_wall_seconds: float = 100.0,
    size: int = 32,
    seed: int = 42,
    unlock_threshold: float = 1.5,
    unlock_rate: float = 0.02,
) -> Dict[str, Any]:
    """
    Run dimensional unlocking test.
    
    Start with 1D active, let oversaturation unlock 2D, then 3D.
    """
    print("=" * 70)
    print("  DIMENSIONAL UNLOCKING / OVERSATURATION TEST")
    print("=" * 70)
    print()
    print("HYPOTHESIS: Dimensions unlock via internal pressure, not external forcing.")
    print()
    print("Mechanism:")
    print("  1D saturates → pressure builds → Y dimension unlocks → 2D")
    print("  2D saturates → pressure builds → Z dimension unlocks → 3D")
    print()
    
    sim = DimensionalUnlockingSimulator(
        size=size,
        dt=0.12,
        seed=seed,
        unlock_threshold=unlock_threshold,
        unlock_rate=unlock_rate,
        start_1d=True,
    )
    
    print()
    print("-" * 80)
    print(f"{'T':>6} | {'ax':>5} {'ay':>5} {'az':>5} | {'D_eff':>6} | {'Pressure':>8} | {'τ_max':>6} | Phase")
    print("-" * 80)
    
    t_start = time.time()
    measure_interval = 25.0
    last_measure = 0.0
    
    while sim.global_T < target_T:
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - 10:
            print(f"\nWall time limit reached at T={sim.global_T:.1f}")
            break
        
        sim.step()
        
        # Compute pressure and check for unlock
        pressure = sim.compute_dimensional_pressure()
        sim.check_and_apply_unlock(pressure)
        
        # Periodic measurement
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            metrics = sim.get_full_metrics()
            sim.metrics_history.append(metrics)
            
            # Determine phase
            if sim.az > 0.5:
                phase = "3D active"
            elif sim.ay > 0.5:
                phase = "2D active"
            else:
                phase = "1D active"
            
            print(f"{sim.global_T:>6.1f} | {sim.ax:>5.2f} {sim.ay:>5.2f} {sim.az:>5.2f} | "
                  f"{metrics['D_eff']:>6.2f} | {metrics['total_pressure']:>8.2f} | "
                  f"{metrics['tau_max']:>6.2f} | {phase}")
    
    # Final analysis
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    
    print(f"\nFinal dimensional activation:")
    print(f"  ax = {sim.ax:.2f}")
    print(f"  ay = {sim.ay:.2f}")
    print(f"  az = {sim.az:.2f}")
    
    print(f"\nUnlock events:")
    if sim.y_unlock_T:
        print(f"  Y dimension began unlocking at T = {sim.y_unlock_T:.1f}")
    else:
        print(f"  Y dimension did NOT unlock")
    
    if sim.z_unlock_T:
        print(f"  Z dimension began unlocking at T = {sim.z_unlock_T:.1f}")
    else:
        print(f"  Z dimension did NOT unlock")
    
    # Check if oversaturation mechanism worked
    if sim.metrics_history:
        d_effs = [m['D_eff'] for m in sim.metrics_history]
        pressures = [m['total_pressure'] for m in sim.metrics_history]
        
        print(f"\nD_eff evolution:")
        print(f"  Initial: {d_effs[0]:.2f}")
        print(f"  Final:   {d_effs[-1]:.2f}")
        print(f"  Max:     {max(d_effs):.2f}")
        
        # Check for pressure → unlock correlation
        if sim.y_unlock_T or sim.az > 0:
            print(f"\n✓ Dimensional unlocking occurred via oversaturation!")
        else:
            print(f"\n✗ No dimensional unlocking (pressure may not have exceeded threshold)")
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    y_unlocked = sim.ay > 0.5
    z_unlocked = sim.az > 0.5
    
    if z_unlocked:
        verdict = "FULL SUCCESS: 1D → 2D → 3D transition achieved"
    elif y_unlocked:
        verdict = "PARTIAL SUCCESS: 1D → 2D transition achieved"
    else:
        verdict = "NO TRANSITION: System remained in 1D phase"
    
    print(f"\n{verdict}")
    
    result = {
        'seed': seed,
        'target_T': target_T,
        'final_T': sim.global_T,
        'unlock_threshold': unlock_threshold,
        'unlock_rate': unlock_rate,
        'final_ax': sim.ax,
        'final_ay': sim.ay,
        'final_az': sim.az,
        'y_unlock_T': sim.y_unlock_T,
        'z_unlock_T': sim.z_unlock_T,
        'unlock_history': sim.unlock_history,
        'metrics_history': sim.metrics_history,
        'verdict': verdict,
    }
    
    # Save
    output_dir = '/app/backend/qmrt_topology/papers/dimensional_unlocking'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/unlocking_seed{seed}.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_dir}/unlocking_seed{seed}.json")
    
    return result


def main():
    result = run_dimensional_unlocking_test(
        target_T=2000.0,
        max_wall_seconds=100.0,
        size=32,
        seed=42,
        unlock_threshold=1.5,
        unlock_rate=0.02,
    )
    return result


if __name__ == "__main__":
    main()
