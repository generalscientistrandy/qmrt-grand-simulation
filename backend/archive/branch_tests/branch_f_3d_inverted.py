"""
3D Branch F v2 INVERTED: Reversed Spatial Coupling Gradient
============================================================

Stage 3 of 3D validation.

Question: If we invert the coupling gradient, does the population
localization invert too?

Test:
- Spherical coupling gradient INVERTED (low center, high edge)
- Smooth cosine transition (identical to Stage 2)
- Track line density by region

Success criteria:
- Higher line density in PERIPHERY (high-coupling region)
- Clear reversal of Stage 2 bias
- Interior loses privileged status

This is the decisive causal proof in 3D.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Dict, List, Tuple
import time


class BranchF3DInvertedSimulator:
    """
    3D Branch F v2 INVERTED: Reversed spatial coupling gradient.
    High coupling at edges, low coupling at center.
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
        coupling_center: float = 0.2,  # INVERTED: low at center
        coupling_edge: float = 0.7,    # INVERTED: high at edge
        transition_width: float = 10.0,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.beta = beta
        self.D_medium = D_medium
        self.dt = dt
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.transition_width = transition_width
        
        # 3D fields
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size)) * tau_0
        
        # Channel assignment
        self.channel_assignment = np.zeros((size, size, size))
        
        # Spatial coupling field (INVERTED spherical gradient)
        self.channel_coupling_field = self._create_spherical_coupling()
        
        self.step_count = 0
    
    def _create_spherical_coupling(self) -> np.ndarray:
        """
        Create smooth spherical coupling gradient.
        INVERTED: Low coupling in center, high at edges.
        """
        x, y, z = np.meshgrid(
            np.arange(self.size),
            np.arange(self.size),
            np.arange(self.size),
            indexing='ij'
        )
        
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        
        # Interior radius (where coupling is LOWEST in inverted case)
        interior_radius = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        
        # Smooth cosine transition (identical to Stage 2)
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    
                    if dist <= interior_radius:
                        coupling[i, j, k] = self.coupling_center  # 0.2 (low)
                    elif dist >= interior_radius + self.transition_width:
                        coupling[i, j, k] = self.coupling_edge    # 0.7 (high)
                    else:
                        # Cosine interpolation
                        t = (dist - interior_radius) / self.transition_width
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = self.coupling_center + blend * (self.coupling_edge - self.coupling_center)
        
        return coupling
    
    def get_region(self, x: int, y: int, z: int) -> str:
        """Classify position as 'interior', 'transition', or 'periphery'."""
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_radius = self.size * 0.25
        
        if r <= interior_radius:
            return 'interior'
        elif r <= interior_radius + self.transition_width:
            return 'transition'
        return 'periphery'
    
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
        return (
            np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) +
            np.roll(field, 1, axis=2) + np.roll(field, -1, axis=2) -
            6 * field
        )
    
    def compute_topology_indicator_3d(self) -> np.ndarray:
        phase = self.phase
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        grad_mag = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        return gaussian_filter(grad_mag, sigma=1.5)
    
    def update_self_selecting_channels(self):
        topology = self.compute_topology_indicator_3d()
        topology_norm = topology / (np.max(topology) + 1e-10)
        target = topology_norm
        self.channel_assignment += 0.01 * (target - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
    
    def compute_channel_protection(self) -> np.ndarray:
        topology = self.compute_topology_indicator_3d()
        topology_norm = topology / (np.max(topology) + 1e-10)
        return topology_norm * self.channel_assignment
    
    def step(self):
        self.step_count += 1
        self.update_self_selecting_channels()
        
        # Medium dynamics
        rho = self.rho
        rho_smooth = gaussian_filter(rho, sigma=1.5)
        tau_eq = self.tau_0 / (1 + self.beta * rho_smooth / (np.max(rho_smooth) + 1e-10))
        lap_tau = self.compute_laplacian_3d(self.tau)
        self.tau += self.dt * (-self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau)
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave equation
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = self.compute_laplacian_3d(self.psi_r)
        lap_i = self.compute_laplacian_3d(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Core-filling suppression with SPATIAL coupling
        protection = self.compute_channel_protection()
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        # Spatially varying suppression
        suppression = self.channel_coupling_field * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def detect_vortex_lines_by_region(self, amp_threshold: float = 0.5) -> Dict:
        """
        Detect vortex lines and classify by region.
        """
        amp = self.amplitude
        phase = self.phase
        
        low_amp_mask = amp < amp_threshold
        
        vortex_by_region = {'interior': [], 'transition': [], 'periphery': []}
        
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    if not low_amp_mask[i, j, k]:
                        continue
                    
                    # Check for phase winding
                    winding = self._check_vortex_point(phase, i, j, k)
                    
                    if winding:
                        region = self.get_region(i, j, k)
                        vortex_by_region[region].append((i, j, k))
        
        return {
            'interior_count': len(vortex_by_region['interior']),
            'transition_count': len(vortex_by_region['transition']),
            'periphery_count': len(vortex_by_region['periphery']),
            'total_count': sum(len(v) for v in vortex_by_region.values()),
            'positions': vortex_by_region
        }
    
    def _check_vortex_point(self, phase: np.ndarray, i: int, j: int, k: int) -> bool:
        """Check if point is near a vortex line."""
        s = self.size
        
        # Check XY plaquette
        p = [phase[i, j, k], phase[(i+1)%s, j, k], 
             phase[(i+1)%s, (j+1)%s, k], phase[i, (j+1)%s, k]]
        winding_xy = sum(np.angle(np.exp(1j * (p[(n+1)%4] - p[n]))) for n in range(4)) / (2*np.pi)
        
        # Check XZ plaquette
        p = [phase[i, j, k], phase[(i+1)%s, j, k],
             phase[(i+1)%s, j, (k+1)%s], phase[i, j, (k+1)%s]]
        winding_xz = sum(np.angle(np.exp(1j * (p[(n+1)%4] - p[n]))) for n in range(4)) / (2*np.pi)
        
        # Check YZ plaquette
        p = [phase[i, j, k], phase[i, (j+1)%s, k],
             phase[i, (j+1)%s, (k+1)%s], phase[i, j, (k+1)%s]]
        winding_yz = sum(np.angle(np.exp(1j * (p[(n+1)%4] - p[n]))) for n in range(4)) / (2*np.pi)
        
        return abs(winding_xy) > 0.5 or abs(winding_xz) > 0.5 or abs(winding_yz) > 0.5
    
    def add_vortex_line(self, cx: int, cy: int, charge: int = 1):
        """Add a vortex line along z-axis at (cx, cy)."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        amp_profile = 1.2 * np.tanh(r / 3.0)
        
        self.psi_r = amp_profile * np.cos(charge * theta)
        self.psi_i = amp_profile * np.sin(charge * theta)


def run_3d_inverted_coupling_test(size: int = 64, steps: int = 2500, sample_interval: int = 50):
    """
    Stage 3 test: Does inverting the coupling gradient invert the population bias?
    
    This is the decisive causal proof for 3D.
    """
    print("="*70)
    print("3D BRANCH F v2 INVERTED: CAUSAL PROOF TEST")
    print("="*70)
    print()
    print(f"Grid size: {size}³")
    print(f"Coupling: center={0.2} (LOW), edge={0.7} (HIGH)")
    print(f"Steps: {steps}")
    print()
    print("HYPOTHESIS: Vortex lines should now concentrate in the PERIPHERY")
    print("            (the high-coupling region)")
    print()
    
    sim = BranchF3DInvertedSimulator(
        size=size, gamma=0.007,
        coupling_center=0.2,  # INVERTED
        coupling_edge=0.7,    # INVERTED
        transition_width=10.0
    )
    
    # Verify coupling profile
    center = size // 2
    print(f"Coupling at center ({center},{center},{center}): {sim.channel_coupling_field[center, center, center]:.2f}")
    print(f"Coupling at edge (0,0,0): {sim.channel_coupling_field[0, 0, 0]:.2f}")
    print()
    
    # Initialize with vortex lines (identical to Stage 2)
    print("Initializing vortex lines...")
    sim.add_vortex_line(center - 5, center, charge=+1)
    
    # Add antivortex
    x, y, z = np.meshgrid(np.arange(size), np.arange(size), np.arange(size), indexing='ij')
    r2 = np.sqrt((x - (center + 5))**2 + (y - center)**2) + 0.1
    theta2 = np.arctan2(y - center, x - (center + 5))
    amp2 = 1.2 * np.tanh(r2 / 3.0)
    
    psi = sim.psi_r + 1j * sim.psi_i
    psi2 = amp2 * np.exp(-1j * theta2)
    psi_combined = psi * psi2 / 1.2
    
    sim.psi_r = np.real(psi_combined)
    sim.psi_i = np.imag(psi_combined)
    
    np.random.seed(42)  # Same seed as Stage 2
    sim.psi_r += 0.02 * np.random.randn(size, size, size)
    sim.psi_i += 0.02 * np.random.randn(size, size, size)
    
    print("Running simulation...")
    print()
    
    # Track metrics by region
    time_points = []
    interior_counts = []
    transition_counts = []
    periphery_counts = []
    total_counts = []
    
    start_time = time.time()
    
    for step in range(steps):
        sim.step()
        
        if step % sample_interval == 0:
            detection = sim.detect_vortex_lines_by_region(amp_threshold=0.5)
            
            time_points.append(step)
            interior_counts.append(detection['interior_count'])
            transition_counts.append(detection['transition_count'])
            periphery_counts.append(detection['periphery_count'])
            total_counts.append(detection['total_count'])
            
            elapsed = time.time() - start_time
            rate = (step + 1) / elapsed if elapsed > 0 else 0
            
            if step % 250 == 0:
                print(f"Step {step:5d}: interior={detection['interior_count']:4d}, "
                      f"trans={detection['transition_count']:4d}, "
                      f"periph={detection['periphery_count']:4d}, "
                      f"total={detection['total_count']:4d}")
    
    total_time = time.time() - start_time
    print()
    print(f"Total time: {total_time:.1f}s")
    print()
    
    # Analysis
    print("="*70)
    print("RESULTS")
    print("="*70)
    print()
    
    # Late-time statistics
    n = len(total_counts)
    late_start = 3 * n // 4
    
    late_interior = np.mean(interior_counts[late_start:])
    late_transition = np.mean(transition_counts[late_start:])
    late_periphery = np.mean(periphery_counts[late_start:])
    late_total = np.mean(total_counts[late_start:])
    
    print("Late-time vortex distribution (INVERTED gradient):")
    print(f"  Interior (low coupling):   {late_interior:.1f} ({100*late_interior/(late_total+1e-10):.1f}%)")
    print(f"  Transition:                {late_transition:.1f} ({100*late_transition/(late_total+1e-10):.1f}%)")
    print(f"  Periphery (HIGH coupling): {late_periphery:.1f} ({100*late_periphery/(late_total+1e-10):.1f}%)")
    print(f"  Total:                     {late_total:.1f}")
    print()
    
    # Volume fractions for comparison
    interior_radius = size * 0.25
    transition_outer = interior_radius + 10
    
    interior_vol = (4/3) * np.pi * interior_radius**3
    transition_vol = (4/3) * np.pi * transition_outer**3 - interior_vol
    total_vol = size**3
    periphery_vol = total_vol - (4/3) * np.pi * transition_outer**3
    
    interior_vol_frac = interior_vol / total_vol
    periphery_vol_frac = periphery_vol / total_vol
    
    print(f"Volume fractions:")
    print(f"  Interior: {100*interior_vol_frac:.1f}%")
    print(f"  Periphery: {100*periphery_vol_frac:.1f}%")
    print()
    
    # Density comparison
    interior_density = late_interior / interior_vol if interior_vol > 0 else 0
    periphery_density = late_periphery / periphery_vol if periphery_vol > 0 else 0
    
    print(f"Vortex density (count / volume):")
    print(f"  Interior (low coupling):   {interior_density:.6f}")
    print(f"  Periphery (HIGH coupling): {periphery_density:.6f}")
    
    density_ratio = 0
    if periphery_density > 0 and interior_density > 0:
        density_ratio = periphery_density / interior_density
        print(f"  Ratio (periphery/interior): {density_ratio:.2f}×")
    elif periphery_density > 0:
        print(f"  Ratio: periphery >> interior (interior ~0)")
        density_ratio = float('inf')
    print()
    
    # Comparison with Stage 2
    print("="*70)
    print("COMPARISON WITH STAGE 2 (STANDARD GRADIENT)")
    print("="*70)
    print()
    print("Stage 2 (high center, low edge):")
    print("  - Interior density was 11.44× periphery density")
    print("  - Interior held 37% of vortices despite 6.5% volume")
    print()
    print("Stage 3 (low center, HIGH edge) - INVERTED:")
    if density_ratio > 1:
        print(f"  - Periphery density is now {density_ratio:.2f}× interior density")
        print(f"  - Bias REVERSED as predicted!")
    elif density_ratio == float('inf'):
        print(f"  - Periphery dominates completely (interior ~0)")
        print(f"  - Bias REVERSED as predicted!")
    else:
        print(f"  - Density ratio (periph/interior): {density_ratio:.2f}")
    print()
    
    # Success criteria
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()
    
    success = False
    if periphery_density > interior_density * 1.5:
        print("✓ SUCCESS: CAUSAL PROOF ACHIEVED IN 3D")
        print()
        print("  Inverting the coupling gradient REVERSED the population bias.")
        print(f"  Periphery density is now {density_ratio:.2f}× interior density.")
        print()
        print("  CONCLUSION: The causal attractor mechanism survives in 3D")
        print("  and is directionally controlled by the coupling landscape.")
        success = True
    elif periphery_density > interior_density:
        print("~ PARTIAL: Bias reversed but not strongly")
        print(f"  Periphery density only {density_ratio:.2f}× interior")
    else:
        print("✗ FAILURE: Inversion did not reverse the bias")
        print("  This would require revisiting the 3D mechanism")
    
    return {
        'success': success,
        'late_interior': late_interior,
        'late_periphery': late_periphery,
        'late_total': late_total,
        'interior_density': interior_density,
        'periphery_density': periphery_density,
        'density_ratio_periph_over_interior': density_ratio,
        'time_series': {
            'interior': interior_counts,
            'periphery': periphery_counts,
            'total': total_counts
        }
    }


if __name__ == "__main__":
    results = run_3d_inverted_coupling_test(size=64, steps=2500, sample_interval=50)
