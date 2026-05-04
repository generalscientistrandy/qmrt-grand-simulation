"""
3D Branch E: Topological Memory in Three Dimensions
====================================================

Stage 1 of 3D validation.

Gate question: Can topological memory and remnant amplification sustain
a nonzero vortex-line population in 3D?

Key differences from 2D:
- Topological defects are vortex LINES, not point vortices
- Detection requires finding where phase winds around plaquettes
- Lines can have length, can reconnect

Metrics to track:
- Total vortex-line length
- Number of connected line segments
- Late-time population (does it survive?)
- Birth/regeneration activity

Success criterion: Nonzero maintained vortex-line population
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Dict, List, Tuple
import time


class BranchE3DSimulator:
    """
    3D extension of Branch E dynamics with topological memory.
    """
    
    def __init__(
        self,
        size: int = 64,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.007,
        lambda_relax: float = 0.5,
        beta: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
        channel_coupling: float = 0.5,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.beta = beta
        self.D_medium = D_medium
        self.dt = dt
        self.channel_coupling = channel_coupling
        
        # 3D fields
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size)) * tau_0
        
        # Channel assignment (3D)
        self.channel_assignment = np.zeros((size, size, size))
        
        self.step_count = 0
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    @property
    def rho(self) -> np.ndarray:
        return self.amplitude**2
    
    def compute_laplacian_3d(self, field: np.ndarray) -> np.ndarray:
        """3D Laplacian with periodic boundaries."""
        return (
            np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) +
            np.roll(field, 1, axis=2) + np.roll(field, -1, axis=2) -
            6 * field
        )
    
    def compute_topology_indicator_3d(self) -> np.ndarray:
        """
        3D topology indicator based on phase gradient magnitude.
        High values indicate proximity to vortex lines.
        """
        phase = self.phase
        
        # Phase gradients in each direction (with wrapping)
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        
        # Gradient magnitude
        grad_mag = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Smooth to get indicator field
        return gaussian_filter(grad_mag, sigma=1.5)
    
    def update_self_selecting_channels(self):
        """Channel assignment grows where topology is high."""
        topology = self.compute_topology_indicator_3d()
        topology_max = np.max(topology)
        topology_norm = topology / (topology_max + 1e-10)
        
        target = topology_norm
        relaxation_rate = 0.01
        self.channel_assignment += relaxation_rate * (target - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
    
    def compute_channel_protection(self) -> np.ndarray:
        """Protection = topology × channel assignment."""
        topology = self.compute_topology_indicator_3d()
        topology_max = np.max(topology)
        topology_norm = topology / (topology_max + 1e-10)
        return topology_norm * self.channel_assignment
    
    def step(self):
        """Evolve one timestep with 3D Branch E dynamics."""
        self.step_count += 1
        
        # Update channels
        self.update_self_selecting_channels()
        
        # Medium dynamics
        rho = self.rho
        rho_smooth = gaussian_filter(rho, sigma=1.5)
        tau_eq = self.tau_0 / (1 + self.beta * rho_smooth / (np.max(rho_smooth) + 1e-10))
        lap_tau = self.compute_laplacian_3d(self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave equation
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = self.compute_laplacian_3d(self.psi_r)
        lap_i = self.compute_laplacian_3d(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Core-filling suppression
        protection = self.compute_channel_protection()
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.channel_coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def detect_vortex_lines(self, amp_threshold: float = 0.5) -> Dict:
        """
        Detect vortex lines by finding plaquettes with phase winding.
        
        Returns dict with:
        - total_length: approximate total vortex line length
        - num_points: number of grid points near vortex cores
        - core_positions: list of (x, y, z) positions
        """
        amp = self.amplitude
        phase = self.phase
        
        # Find low-amplitude regions (potential vortex cores)
        low_amp_mask = amp < amp_threshold
        
        # For each low-amp point, check for phase winding on surrounding plaquettes
        vortex_points = []
        
        # Check XY plaquettes
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    if not low_amp_mask[i, j, k]:
                        continue
                    
                    # Check phase winding around this point
                    # XY plaquette
                    winding_xy = self._compute_plaquette_winding(phase, i, j, k, 'xy')
                    # XZ plaquette
                    winding_xz = self._compute_plaquette_winding(phase, i, j, k, 'xz')
                    # YZ plaquette
                    winding_yz = self._compute_plaquette_winding(phase, i, j, k, 'yz')
                    
                    if abs(winding_xy) > 0.5 or abs(winding_xz) > 0.5 or abs(winding_yz) > 0.5:
                        vortex_points.append((i, j, k))
        
        # Estimate total line length (rough: count points, assume each spans ~1 grid unit)
        total_length = len(vortex_points)
        
        return {
            'total_length': total_length,
            'num_points': len(vortex_points),
            'core_positions': vortex_points
        }
    
    def _compute_plaquette_winding(self, phase: np.ndarray, i: int, j: int, k: int, 
                                    plane: str) -> float:
        """Compute phase winding around a plaquette."""
        s = self.size
        
        if plane == 'xy':
            # Corners of plaquette in XY plane at z=k
            p1 = phase[i, j, k]
            p2 = phase[(i+1) % s, j, k]
            p3 = phase[(i+1) % s, (j+1) % s, k]
            p4 = phase[i, (j+1) % s, k]
        elif plane == 'xz':
            p1 = phase[i, j, k]
            p2 = phase[(i+1) % s, j, k]
            p3 = phase[(i+1) % s, j, (k+1) % s]
            p4 = phase[i, j, (k+1) % s]
        else:  # yz
            p1 = phase[i, j, k]
            p2 = phase[i, (j+1) % s, k]
            p3 = phase[i, (j+1) % s, (k+1) % s]
            p4 = phase[i, j, (k+1) % s]
        
        # Sum of phase differences around plaquette
        winding = (
            np.angle(np.exp(1j * (p2 - p1))) +
            np.angle(np.exp(1j * (p3 - p2))) +
            np.angle(np.exp(1j * (p4 - p3))) +
            np.angle(np.exp(1j * (p1 - p4)))
        )
        
        return winding / (2 * np.pi)
    
    def add_vortex_line(self, start: Tuple[int, int, int], direction: str = 'z',
                        length: int = None, charge: int = 1):
        """
        Add a straight vortex line to the field.
        
        Args:
            start: (x, y, z) starting position
            direction: 'x', 'y', or 'z' - direction the line extends
            length: length of line (defaults to full domain)
            charge: +1 or -1
        """
        if length is None:
            length = self.size
        
        cx, cy, cz = start
        
        x, y, z = np.meshgrid(
            np.arange(self.size),
            np.arange(self.size),
            np.arange(self.size),
            indexing='ij'
        )
        
        if direction == 'z':
            # Line along z-axis at (cx, cy)
            r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
            theta = np.arctan2(y - cy, x - cx)
        elif direction == 'y':
            r = np.sqrt((x - cx)**2 + (z - cz)**2) + 0.1
            theta = np.arctan2(z - cz, x - cx)
        else:  # x
            r = np.sqrt((y - cy)**2 + (z - cz)**2) + 0.1
            theta = np.arctan2(z - cz, y - cy)
        
        # Vortex profile
        core_radius = 3.0
        amp_profile = 1.2 * np.tanh(r / core_radius)
        
        self.psi_r = amp_profile * np.cos(charge * theta)
        self.psi_i = amp_profile * np.sin(charge * theta)


def run_3d_branch_e_test(size: int = 64, steps: int = 2000, sample_interval: int = 50):
    """
    Stage 1 test: Can 3D Branch E maintain a vortex-line population?
    """
    print("="*70)
    print("3D BRANCH E: TOPOLOGICAL MEMORY TEST")
    print("="*70)
    print()
    print(f"Grid size: {size}³")
    print(f"Steps: {steps}")
    print()
    
    sim = BranchE3DSimulator(size=size, gamma=0.007, channel_coupling=0.5)
    
    # Initialize with vortex lines
    print("Initializing vortex lines...")
    center = size // 2
    
    # Add a vortex-antivortex pair (two parallel lines with opposite charge)
    sim.add_vortex_line((center - 5, center, 0), direction='z', charge=+1)
    
    # Superimpose antivortex
    x, y, z = np.meshgrid(np.arange(size), np.arange(size), np.arange(size), indexing='ij')
    r2 = np.sqrt((x - (center + 5))**2 + (y - center)**2) + 0.1
    theta2 = np.arctan2(y - center, x - (center + 5))
    amp2 = 1.2 * np.tanh(r2 / 3.0)
    
    psi = sim.psi_r + 1j * sim.psi_i
    psi2 = amp2 * np.exp(-1j * theta2)  # Opposite charge
    psi_combined = psi * psi2 / 1.2  # Combine
    
    sim.psi_r = np.real(psi_combined)
    sim.psi_i = np.imag(psi_combined)
    
    # Add noise
    np.random.seed(42)
    sim.psi_r += 0.02 * np.random.randn(size, size, size)
    sim.psi_i += 0.02 * np.random.randn(size, size, size)
    
    print("Running simulation...")
    print()
    
    # Track metrics
    time_points = []
    vortex_lengths = []
    vortex_counts = []
    
    start_time = time.time()
    
    for step in range(steps):
        sim.step()
        
        if step % sample_interval == 0:
            detection = sim.detect_vortex_lines(amp_threshold=0.5)
            
            time_points.append(step)
            vortex_lengths.append(detection['total_length'])
            vortex_counts.append(detection['num_points'])
            
            elapsed = time.time() - start_time
            rate = (step + 1) / elapsed if elapsed > 0 else 0
            
            print(f"Step {step:5d}: vortex_length={detection['total_length']:4d}, "
                  f"points={detection['num_points']:4d}, "
                  f"rate={rate:.1f} steps/s")
    
    total_time = time.time() - start_time
    print()
    print(f"Total time: {total_time:.1f}s")
    print()
    
    # Analysis
    print("="*70)
    print("RESULTS")
    print("="*70)
    print()
    
    # Early vs late comparison
    n = len(vortex_lengths)
    early_length = np.mean(vortex_lengths[:n//4])
    late_length = np.mean(vortex_lengths[3*n//4:])
    
    print(f"Early vortex length (first 25%): {early_length:.1f}")
    print(f"Late vortex length (last 25%):  {late_length:.1f}")
    print()
    
    # Success criterion
    if late_length > 10:
        print("✓ SUCCESS: Nonzero vortex-line population maintained in 3D")
        success = True
    elif late_length > 0:
        print("~ PARTIAL: Some vortex structure remains, but reduced")
        success = False
    else:
        print("✗ FAILURE: Vortex-line population collapsed to zero")
        success = False
    
    print()
    
    return {
        'success': success,
        'time_points': time_points,
        'vortex_lengths': vortex_lengths,
        'early_length': early_length,
        'late_length': late_length,
        'total_time': total_time
    }


if __name__ == "__main__":
    results = run_3d_branch_e_test(size=64, steps=2000, sample_interval=50)
