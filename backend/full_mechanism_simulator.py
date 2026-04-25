"""
Full-Mechanism QMRT Simulator
==============================

This implements the COMPLETE intended QMRT theory, including:
1. Dynamic medium τ field (responds to energy density)
2. Variable effective wave speed c_eff = c₀ τ/τ₀
3. Active remnant field (topological memory for regeneration)
4. Channel assignment (topological protection)
5. Spatial coupling gradient (attractor landscape)

Purpose: Compare full-mechanism behavior to the reduced simulator
to understand which effects depend on which mechanisms.

Based on Papers 3-5 specifications.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json


class FullMechanismSimulator:
    """
    Complete QMRT simulator with all intended mechanisms.
    
    State variables:
    - psi_r, psi_i: Complex scalar field (real/imag)
    - psi_r_dot, psi_i_dot: Field momentum
    - tau: Dynamic medium field (responds to energy density)
    - channel_assignment: Topological memory (protection)
    - remnant_field: Historical memory (regeneration sites)
    - coupling: Spatial attractor gradient
    """
    
    def __init__(self, size: int = 48):
        self.size = size
        
        # Wave field
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Dynamic medium (NEW - was missing)
        self.tau = np.ones((size, size, size))  # Medium density
        self.tau_0 = 1.0  # Reference value
        self.c_0_sq = 4.0  # Base wave speed squared
        self.tau_relaxation = 0.01  # Rate tau returns to equilibrium
        self.tau_response = 0.005  # Rate tau responds to energy
        
        # Topological memory
        self.channel_assignment = np.zeros((size, size, size))
        
        # Remnant field (NEW - was dead code)
        self.remnant_field = np.zeros((size, size, size))
        self.remnant_decay = 0.001  # Slow decay rate
        self.remnant_accumulation = 0.02  # Rate of accumulation from defects
        
        # Spatial coupling
        self.coupling = self._create_coupling()
        
        # Parameters
        self.gamma = 0.007  # Damping
        self.step_count = 0
        
        # Driving configuration
        self.driving_mode = 'external'
        self.injection_interval = 50
        self.injection_count = 3
        self.cutoff_step = None
        
        # Tracking
        self.injections_this_run = 0
        
    def _create_coupling(self) -> np.ndarray:
        """Create radial coupling gradient (per Paper 4)."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25  # = 12 for size 48
        
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
    
    def inject_vortex(self, cx: int, cy: int):
        """Inject a topological vortex at (cx, cy)."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_random_vortices(self, n: int = None):
        """Inject random vortices in the interior region."""
        if n is None:
            n = self.injection_count
        center = self.size // 2
        for _ in range(n):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy)
        self.injections_this_run += n
    
    def inject_at_remnant_sites(self, n: int = 1):
        """
        Inject vortices preferentially at high-remnant locations.
        This is the key regeneration mechanism from Branch E.
        """
        # Find high-remnant locations
        threshold = np.percentile(self.remnant_field, 90)
        high_remnant = self.remnant_field > threshold
        
        if not np.any(high_remnant):
            return  # No strong remnant sites
        
        coords = np.where(high_remnant)
        n_sites = len(coords[0])
        
        for _ in range(min(n, n_sites)):
            idx = np.random.randint(n_sites)
            cx, cy = coords[0][idx], coords[1][idx]
            self.inject_vortex(cx, cy)
            self.injections_this_run += 1
    
    def should_inject(self) -> bool:
        """Determine whether to inject based on driving mode."""
        if self.driving_mode == 'external':
            return self.step_count % self.injection_interval == 0
        elif self.driving_mode == 'cutoff':
            if self.cutoff_step is not None and self.step_count >= self.cutoff_step:
                return False
            return self.step_count % self.injection_interval == 0
        elif self.driving_mode == 'remnant':
            # Inject at remnant sites instead of random locations
            if self.step_count % self.injection_interval == 0:
                self.inject_at_remnant_sites(self.injection_count)
            return False  # Already handled
        return False
    
    def step(self, dt: float = 0.04):
        """
        Advance simulation by one timestep.
        
        Full mechanism includes:
        1. Conditional vortex injection
        2. Dynamic medium (τ) evolution
        3. Wave equation with variable c_eff
        4. Channel protection
        5. Remnant field update
        """
        self.step_count += 1
        
        # 1. Conditional injection
        if self.should_inject():
            self.inject_random_vortices()
        
        # Laplacian operator
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # 2. Update dynamic medium τ
        # τ responds to local energy density
        energy_density = self.psi_r**2 + self.psi_i**2 + \
                        0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # τ is attracted to equilibrium but responds to energy
        tau_target = 1.0 + self.tau_response * (energy_density - np.mean(energy_density))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)  # Bounded
        
        # 3. Variable effective wave speed
        c_eff_sq = self.c_0_sq * self.tau / self.tau_0
        
        # Wave equation: ∂²ψ/∂t² = c_eff² ∇²ψ - γ ∂ψ/∂t
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # 4. Topology and channel protection
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Update channel assignment
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        # Protection suppresses radial acceleration
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        # 5. Update remnant field (NEW - was dead code)
        # Remnant accumulates where topology is strong, decays slowly
        self.remnant_field += self.remnant_accumulation * topology_norm
        self.remnant_field *= (1 - self.remnant_decay)
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        # Integrate momentum and position
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple]:
        """Detect topological defects (amplitude minima)."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                defects.append((
                    int(np.mean(coords[0])),
                    int(np.mean(coords[1])),
                    int(np.mean(coords[2]))
                ))
        return defects
    
    def get_diagnostics(self) -> Dict:
        """Return diagnostic information about current state."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        mom = np.sqrt(self.psi_r_dot**2 + self.psi_i_dot**2)
        
        return {
            'amp_mean': float(np.mean(amp)),
            'amp_std': float(np.std(amp)),
            'mom_mean': float(np.mean(mom)),
            'mom_max': float(np.max(mom)),
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'channel_mean': float(np.mean(self.channel_assignment)),
            'remnant_mean': float(np.mean(self.remnant_field)),
            'remnant_max': float(np.max(self.remnant_field)),
        }


class ReducedSimulator:
    """
    Reduced simulator (current implementation) for comparison.
    
    Differences from FullMechanismSimulator:
    - No dynamic τ (constant wave speed)
    - Remnant field not active
    """
    
    def __init__(self, size: int = 48):
        self.size = size
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        self.coupling = self._create_coupling()
        self.step_count = 0
        
        self.driving_mode = 'external'
        self.injection_interval = 50
        self.injection_count = 3
        self.cutoff_step = None
        self.injections_this_run = 0
        
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
    
    def inject_vortex(self, cx: int, cy: int):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_random_vortices(self, n: int = None):
        if n is None:
            n = self.injection_count
        center = self.size // 2
        for _ in range(n):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy)
        self.injections_this_run += n
    
    def should_inject(self) -> bool:
        if self.driving_mode == 'external':
            return self.step_count % self.injection_interval == 0
        elif self.driving_mode == 'cutoff':
            if self.cutoff_step is not None and self.step_count >= self.cutoff_step:
                return False
            return self.step_count % self.injection_interval == 0
        return False
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        if self.should_inject():
            self.inject_random_vortices()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        gamma = 0.007
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        # CONSTANT wave speed (reduced model)
        acc_r = 4.0 * lap_r - gamma * self.psi_r_dot
        acc_i = 4.0 * lap_i - gamma * self.psi_i_dot
        
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
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                defects.append((
                    int(np.mean(coords[0])),
                    int(np.mean(coords[1])),
                    int(np.mean(coords[2]))
                ))
        return defects
    
    def get_diagnostics(self) -> Dict:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        mom = np.sqrt(self.psi_r_dot**2 + self.psi_i_dot**2)
        return {
            'amp_mean': float(np.mean(amp)),
            'mom_mean': float(np.mean(mom)),
            'channel_mean': float(np.mean(self.channel_assignment)),
        }


def run_mechanism_comparison():
    """
    Compare full-mechanism vs reduced simulator behavior.
    """
    print("=" * 75)
    print("  MECHANISM COMPARISON: Full vs Reduced Simulator")
    print("=" * 75)
    print()
    print("Full mechanism includes: dynamic τ, variable c_eff, active remnant field")
    print("Reduced model has:       constant c², no remnant field")
    print()
    
    # Initialize both with identical conditions
    np.random.seed(42)
    noise_r = 0.04 * np.random.randn(48, 48, 48)
    noise_i = 0.04 * np.random.randn(48, 48, 48)
    
    sim_full = FullMechanismSimulator(size=48)
    sim_full.psi_r += noise_r
    sim_full.psi_i += noise_i
    
    sim_reduced = ReducedSimulator(size=48)
    sim_reduced.psi_r += noise_r
    sim_reduced.psi_i += noise_i
    
    # Initial seeding
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim_full.inject_vortex(center + i * 3, center + j * 3)
                sim_reduced.inject_vortex(center + i * 3, center + j * 3)
    
    print("Phase 1: Build with external driving (1000 steps)")
    print("-" * 75)
    
    for step in range(1000):
        sim_full.step()
        sim_reduced.step()
        
        if step % 200 == 0:
            d_full = sim_full.detect_defects()
            d_reduced = sim_reduced.detect_defects()
            diag_full = sim_full.get_diagnostics()
            diag_reduced = sim_reduced.get_diagnostics()
            print(f"Step {step:4d}: Full: n={len(d_full):3d}, τ={diag_full['tau_mean']:.3f}, "
                  f"remnant={diag_full['remnant_max']:.3f} | "
                  f"Reduced: n={len(d_reduced):3d}")
    
    print()
    print("Phase 2: Cutoff (no more injection)")
    print("-" * 75)
    
    sim_full.driving_mode = 'cutoff'
    sim_full.cutoff_step = sim_full.step_count
    
    sim_reduced.driving_mode = 'cutoff'
    sim_reduced.cutoff_step = sim_reduced.step_count
    
    for step in range(2000):
        sim_full.step()
        sim_reduced.step()
        
        if step % 200 == 0:
            d_full = sim_full.detect_defects()
            d_reduced = sim_reduced.detect_defects()
            diag_full = sim_full.get_diagnostics()
            print(f"Step +{step:4d}: Full: n={len(d_full):3d}, τ={diag_full['tau_mean']:.3f}, "
                  f"remnant={diag_full['remnant_max']:.3f} | "
                  f"Reduced: n={len(d_reduced):3d}")
    
    print()
    print("=" * 75)
    print("SUMMARY")
    print("=" * 75)
    
    final_full = len(sim_full.detect_defects())
    final_reduced = len(sim_reduced.detect_defects())
    
    print(f"Final defect count - Full: {final_full}, Reduced: {final_reduced}")
    print(f"Ratio (Full/Reduced): {final_full / max(1, final_reduced):.2f}x")
    
    diag_full = sim_full.get_diagnostics()
    print()
    print(f"Full mechanism diagnostics:")
    print(f"  τ (medium): mean={diag_full['tau_mean']:.3f}, std={diag_full['tau_std']:.3f}")
    print(f"  Remnant:    mean={diag_full['remnant_mean']:.3f}, max={diag_full['remnant_max']:.3f}")
    print(f"  Channel:    mean={diag_full['channel_mean']:.3f}")
    print(f"  Momentum:   mean={diag_full['mom_mean']:.3f}")
    
    return {
        'full_final': final_full,
        'reduced_final': final_reduced,
        'full_diagnostics': diag_full,
    }


if __name__ == "__main__":
    results = run_mechanism_comparison()
