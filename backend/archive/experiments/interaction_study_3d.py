"""
3D Defect-Defect Interaction Study — Stage 1
=============================================

Phase: Interaction Studies (Post-3D Validation)

Question: Do defect-defect interactions change inside the
causal attractor landscape, or does the attractor only
control population distribution?

Test Design:
- Place two vortex lines with controlled:
  - Separation
  - Charge (same / opposite chirality)
  - Location (both inside attractor / both outside / mixed)

Measurements:
- Separation vs time
- Annihilation time (if applicable)
- Trajectory drift (toward/away from each other)
- Comparison: inside vs outside attractor region

Success would be showing that the attractor landscape
modifies interaction dynamics, not just occupancy.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Dict, List, Tuple, Optional
import time


class InteractionStudySimulator:
    """
    3D simulator for defect-defect interaction studies.
    Builds on Branch F 3D with controlled defect placement.
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
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        transition_width: float = 10.0,
        use_spatial_coupling: bool = True,
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
        self.use_spatial_coupling = use_spatial_coupling
        
        # 3D fields
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size)) * tau_0
        
        # Channel assignment
        self.channel_assignment = np.zeros((size, size, size))
        
        # Spatial coupling field
        if use_spatial_coupling:
            self.channel_coupling_field = self._create_spherical_coupling()
        else:
            self.channel_coupling_field = np.ones((size, size, size)) * coupling_center
        
        self.step_count = 0
    
    def _create_spherical_coupling(self) -> np.ndarray:
        """Create smooth spherical coupling gradient."""
        x, y, z = np.meshgrid(
            np.arange(self.size),
            np.arange(self.size),
            np.arange(self.size),
            indexing='ij'
        )
        
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_radius = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_radius:
                        coupling[i, j, k] = self.coupling_center
                    elif dist >= interior_radius + self.transition_width:
                        coupling[i, j, k] = self.coupling_edge
                    else:
                        t = (dist - interior_radius) / self.transition_width
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = self.coupling_center + blend * (self.coupling_edge - self.coupling_center)
        
        return coupling
    
    def get_region(self, x: int, y: int, z: int) -> str:
        """Classify position."""
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
        
        rho = self.rho
        rho_smooth = gaussian_filter(rho, sigma=1.5)
        tau_eq = self.tau_0 / (1 + self.beta * rho_smooth / (np.max(rho_smooth) + 1e-10))
        lap_tau = self.compute_laplacian_3d(self.tau)
        self.tau += self.dt * (-self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau)
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
        c_eff_sq = c_eff**2
        
        lap_r = self.compute_laplacian_3d(self.psi_r)
        lap_i = self.compute_laplacian_3d(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        protection = self.compute_channel_protection()
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.channel_coupling_field * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def place_vortex_line(self, cx: int, cy: int, charge: int = 1):
        """
        Place a vortex line along z-axis at (cx, cy).
        Modifies psi multiplicatively to allow multiple vortices.
        """
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        amp_profile = np.tanh(r / 3.0)
        
        vortex_psi = amp_profile * np.exp(1j * charge * theta)
        current_psi = self.psi_r + 1j * self.psi_i
        combined = current_psi * vortex_psi / (np.abs(current_psi) + 1e-10)
        
        # Renormalize amplitude
        combined *= 1.2 / (np.mean(np.abs(combined)) + 1e-10)
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def initialize_uniform(self, amplitude: float = 1.2):
        """Reset to uniform field."""
        self.psi_r = np.ones((self.size, self.size, self.size)) * amplitude
        self.psi_i = np.zeros((self.size, self.size, self.size))
        self.psi_r_dot = np.zeros((self.size, self.size, self.size))
        self.psi_i_dot = np.zeros((self.size, self.size, self.size))
        self.channel_assignment = np.zeros((self.size, self.size, self.size))
    
    def find_vortex_cores(self, amp_threshold: float = 0.5) -> List[Tuple[float, float, float]]:
        """
        Find vortex line core positions (centroids of low-amplitude regions).
        Returns list of (x, y, z) centroid positions.
        """
        amp = self.amplitude
        phase = self.phase
        
        # Find low amplitude points with phase winding
        cores = []
        low_amp_mask = amp < amp_threshold
        
        # Find connected components of low amplitude
        from scipy.ndimage import label
        labeled, num_features = label(low_amp_mask)
        
        for i in range(1, num_features + 1):
            component = (labeled == i)
            if np.sum(component) < 3:
                continue
            
            # Check for phase winding in this component
            coords = np.where(component)
            if len(coords[0]) == 0:
                continue
            
            # Compute centroid
            cx = np.mean(coords[0])
            cy = np.mean(coords[1])
            cz = np.mean(coords[2])
            cores.append((cx, cy, cz))
        
        return cores
    
    def compute_core_separation(self, cores: List[Tuple[float, float, float]]) -> float:
        """Compute separation between two cores (for two-defect tests)."""
        if len(cores) < 2:
            return 0.0
        
        # Find the two largest / most distinct cores
        c1, c2 = cores[0], cores[1]
        dx = c1[0] - c2[0]
        dy = c1[1] - c2[1]
        dz = c1[2] - c2[2]
        
        # Handle periodic boundaries
        dx = min(abs(dx), self.size - abs(dx))
        dy = min(abs(dy), self.size - abs(dy))
        dz = min(abs(dz), self.size - abs(dz))
        
        return np.sqrt(dx**2 + dy**2 + dz**2)


def run_two_defect_test(
    location: str = 'interior',  # 'interior', 'periphery', or 'mixed'
    charges: Tuple[int, int] = (+1, -1),  # Same or opposite chirality
    initial_separation: int = 10,
    steps: int = 1500,
    use_attractor: bool = True,
) -> Dict:
    """
    Run a controlled two-defect interaction test.
    
    Parameters:
    - location: Where to place defects relative to attractor
    - charges: Chirality of the two vortex lines
    - initial_separation: Starting separation in grid units
    - steps: Simulation steps
    - use_attractor: Whether to use spatial coupling gradient
    """
    size = 64
    center = size // 2
    
    print(f"\n{'='*60}")
    print(f"TWO-DEFECT INTERACTION TEST")
    print(f"{'='*60}")
    print(f"Location: {location}")
    print(f"Charges: {charges}")
    print(f"Initial separation: {initial_separation}")
    print(f"Attractor: {'ON' if use_attractor else 'OFF'}")
    print()
    
    sim = InteractionStudySimulator(
        size=size,
        gamma=0.007,
        coupling_center=0.7,
        coupling_edge=0.2,
        use_spatial_coupling=use_attractor,
    )
    
    # Determine defect positions based on location
    if location == 'interior':
        # Both defects inside attractor (near center)
        pos1 = (center - initial_separation // 2, center, center)
        pos2 = (center + initial_separation // 2, center, center)
    elif location == 'periphery':
        # Both defects outside attractor (near edge)
        offset = size // 4 + 5  # Just outside interior radius
        pos1 = (center + offset - initial_separation // 2, center, center)
        pos2 = (center + offset + initial_separation // 2, center, center)
    else:  # mixed
        # One inside, one outside
        pos1 = (center, center, center)  # Inside
        pos2 = (center + size // 4 + 10, center, center)  # Outside
    
    # Initialize uniform field and place vortices
    sim.initialize_uniform()
    sim.place_vortex_line(pos1[0], pos1[1], charge=charges[0])
    sim.place_vortex_line(pos2[0], pos2[1], charge=charges[1])
    
    # Add small noise
    np.random.seed(42)
    sim.psi_r += 0.01 * np.random.randn(size, size, size)
    sim.psi_i += 0.01 * np.random.randn(size, size, size)
    
    region1 = sim.get_region(pos1[0], pos1[1], pos1[2])
    region2 = sim.get_region(pos2[0], pos2[1], pos2[2])
    print(f"Defect 1 at {pos1} → {region1}")
    print(f"Defect 2 at {pos2} → {region2}")
    print()
    
    # Track separation over time
    separations = []
    times = []
    core_counts = []
    annihilation_step = None
    
    sample_interval = 25
    
    print("Running simulation...")
    start_time = time.time()
    
    for step in range(steps):
        sim.step()
        
        if step % sample_interval == 0:
            cores = sim.find_vortex_cores(amp_threshold=0.5)
            sep = sim.compute_core_separation(cores) if len(cores) >= 2 else 0
            
            separations.append(sep)
            times.append(step)
            core_counts.append(len(cores))
            
            if len(cores) < 2 and annihilation_step is None and step > 50:
                annihilation_step = step
            
            if step % 250 == 0:
                print(f"Step {step:4d}: cores={len(cores)}, separation={sep:.1f}")
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f}s")
    
    # Analysis
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    
    # Did defects annihilate?
    final_cores = core_counts[-1] if core_counts else 0
    annihilated = final_cores < 2
    
    print(f"\nFinal core count: {final_cores}")
    print(f"Annihilated: {'YES' if annihilated else 'NO'}")
    
    if annihilation_step:
        print(f"Annihilation step: {annihilation_step}")
    
    # Separation dynamics
    if len(separations) > 5:
        early_sep = np.mean(separations[:5])
        late_sep = np.mean(separations[-5:]) if not annihilated else 0
        
        print(f"\nEarly separation: {early_sep:.1f}")
        print(f"Late separation: {late_sep:.1f}")
        
        if not annihilated and early_sep > 0:
            change = late_sep - early_sep
            pct_change = 100 * change / early_sep
            print(f"Change: {change:+.1f} ({pct_change:+.1f}%)")
            
            if change < -2:
                print("→ Defects ATTRACTED (moved closer)")
            elif change > 2:
                print("→ Defects REPELLED (moved apart)")
            else:
                print("→ Separation roughly STABLE")
    
    return {
        'location': location,
        'charges': charges,
        'initial_separation': initial_separation,
        'use_attractor': use_attractor,
        'annihilated': annihilated,
        'annihilation_step': annihilation_step,
        'separations': separations,
        'times': times,
        'core_counts': core_counts,
        'final_cores': final_cores,
    }


def run_interaction_comparison():
    """
    Compare defect interactions inside vs outside the attractor.
    """
    print("="*70)
    print("3D DEFECT-DEFECT INTERACTION STUDY")
    print("="*70)
    print()
    print("Question: Does the attractor landscape change interaction dynamics,")
    print("          or only population distribution?")
    print()
    
    results = {}
    
    # Test 1: Opposite charges inside attractor (should attract/annihilate)
    print("\n" + "="*70)
    print("TEST 1: Opposite charges INSIDE attractor")
    print("="*70)
    results['inside_opposite'] = run_two_defect_test(
        location='interior',
        charges=(+1, -1),
        initial_separation=10,
        steps=1500,
        use_attractor=True
    )
    
    # Test 2: Opposite charges outside attractor
    print("\n" + "="*70)
    print("TEST 2: Opposite charges OUTSIDE attractor")
    print("="*70)
    results['outside_opposite'] = run_two_defect_test(
        location='periphery',
        charges=(+1, -1),
        initial_separation=10,
        steps=1500,
        use_attractor=True
    )
    
    # Test 3: Same charges inside attractor (should repel or coexist)
    print("\n" + "="*70)
    print("TEST 3: Same charges INSIDE attractor")
    print("="*70)
    results['inside_same'] = run_two_defect_test(
        location='interior',
        charges=(+1, +1),
        initial_separation=10,
        steps=1500,
        use_attractor=True
    )
    
    # Test 4: Same charges outside attractor
    print("\n" + "="*70)
    print("TEST 4: Same charges OUTSIDE attractor")
    print("="*70)
    results['outside_same'] = run_two_defect_test(
        location='periphery',
        charges=(+1, +1),
        initial_separation=10,
        steps=1500,
        use_attractor=True
    )
    
    # Summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print()
    print(f"{'Test':<25} {'Annihilated':<12} {'Ann.Step':<10} {'Final Cores'}")
    print("-"*60)
    
    for name, r in results.items():
        ann = 'YES' if r['annihilated'] else 'NO'
        step = str(r['annihilation_step']) if r['annihilation_step'] else '-'
        print(f"{name:<25} {ann:<12} {step:<10} {r['final_cores']}")
    
    print()
    
    # Key comparison: Does attractor affect annihilation rate?
    inside_opp = results['inside_opposite']
    outside_opp = results['outside_opposite']
    
    print("KEY COMPARISON: Opposite charges")
    print(f"  Inside attractor:  annihilated={inside_opp['annihilated']}, step={inside_opp['annihilation_step']}")
    print(f"  Outside attractor: annihilated={outside_opp['annihilated']}, step={outside_opp['annihilation_step']}")
    
    if inside_opp['annihilation_step'] and outside_opp['annihilation_step']:
        ratio = inside_opp['annihilation_step'] / outside_opp['annihilation_step']
        if ratio > 1.2:
            print(f"  → Attractor DELAYS annihilation ({ratio:.2f}× slower)")
        elif ratio < 0.8:
            print(f"  → Attractor ACCELERATES annihilation ({1/ratio:.2f}× faster)")
        else:
            print(f"  → Annihilation rate similar (ratio={ratio:.2f})")
    
    return results


if __name__ == "__main__":
    results = run_interaction_comparison()
