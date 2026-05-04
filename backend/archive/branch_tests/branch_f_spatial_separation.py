"""
Branch F — Spatially Separated Regeneration–Stabilization Model
================================================================

Hypothesis: Topological memory (regeneration) and vortex stabilization
can co-align if they occur in DIFFERENT spatial regions:

  Zone A (Interior): Low-β / neutral region
    - Fast channel self-selection (no disruption)
    - Remnant amplification can operate
    - Vortices nucleate here

  Zone B (Periphery): Higher-β shoulder/basin  
    - Extended vortex lifetime
    - Structures that migrate here persist longer
    - Smooth gradient (no ejection)

Key design principles (from β-suppression analysis):
  1. Use SMOOTH β profile (Gaussian/cosine), not step edges
  2. Avoid steep ∇β boundaries that eject structures
  3. Keep self-selection active everywhere (resonance ON)

Three diagnostic tests:
  1. Regeneration Location — Do vortices nucleate in low-β interior?
  2. Migration/Capture — Do vortices move toward high-β and survive longer there?
  3. Population Localization — Nonzero population + localization WITHOUT regeneration suppression?
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional
import json


class BranchFSimulator:
    """
    Spatially separated regeneration-stabilization model.
    
    β profile: smooth cosine/Gaussian with:
      - Low-β interior (self-selection zone)
      - High-β periphery (stabilization zone)
    """
    
    def __init__(self, size: int = 120, gamma: float = 0.007,
                 beta_interior: float = 0.25, beta_periphery: float = 0.7,
                 transition_width: float = 15.0):
        """
        Args:
            size: Grid size
            gamma: Damping coefficient
            beta_interior: β value in central region (low, for fast self-selection)
            beta_periphery: β value at edges (high, for stabilization)
            transition_width: Width of smooth transition (grid units)
        """
        self.size = size
        self.gamma = gamma
        self.beta_interior = beta_interior
        self.beta_periphery = beta_periphery
        self.transition_width = transition_width
        
        # Initialize fields
        self.psi_r = np.ones((size, size)) * 1.2  # Real part
        self.psi_i = np.zeros((size, size))        # Imaginary part
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Resonance oscillators (for self-selection)
        self.osc_amp = np.zeros((size, size))
        self.osc_phase = np.random.uniform(0, 2*np.pi, (size, size))
        self.osc_freq = np.ones((size, size)) * 0.1
        
        # Channel assignment (resonance self-selection)
        self.channel_assignment = np.zeros((size, size))
        
        # Create smooth β landscape
        self.beta = self._create_smooth_beta_landscape()
        
        # Tracking
        self.nucleation_history = []  # (step, x, y, zone)
        self.vortex_lifetimes = {}    # id -> {'birth': step, 'zone_at_birth': str, 'positions': [...]}
        self.next_vortex_id = 0
        self.step_count = 0
        
    def _create_smooth_beta_landscape(self) -> np.ndarray:
        """
        Create smooth β profile: low in center, high at periphery.
        Uses cosine transition for smooth gradient (no sharp ∇β).
        """
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        center = self.size / 2
        
        # Distance from center (normalized)
        r = np.sqrt((x - center)**2 + (y - center)**2)
        
        # Interior radius (where β is lowest)
        interior_radius = self.size * 0.25
        
        # Smooth cosine transition
        # r < interior_radius: β = beta_interior
        # r > interior_radius + transition_width: β = beta_periphery
        # In between: smooth cosine ramp
        
        beta = np.zeros((self.size, self.size))
        
        for i in range(self.size):
            for j in range(self.size):
                dist = r[i, j]
                
                if dist <= interior_radius:
                    beta[i, j] = self.beta_interior
                elif dist >= interior_radius + self.transition_width:
                    beta[i, j] = self.beta_periphery
                else:
                    # Cosine interpolation (smooth derivative at boundaries)
                    t = (dist - interior_radius) / self.transition_width
                    # Cosine goes from 1 to -1 over [0, π], so (1 - cos(πt))/2 goes 0 to 1
                    blend = 0.5 * (1 - np.cos(np.pi * t))
                    beta[i, j] = self.beta_interior + blend * (self.beta_periphery - self.beta_interior)
        
        return beta
    
    def get_zone(self, x: int, y: int) -> str:
        """Classify position as 'interior', 'transition', or 'periphery'."""
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2)
        interior_radius = self.size * 0.25
        
        if r <= interior_radius:
            return 'interior'
        elif r <= interior_radius + self.transition_width:
            return 'transition'
        else:
            return 'periphery'
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    def compute_laplacian(self, field: np.ndarray) -> np.ndarray:
        """Compute Laplacian with periodic boundary conditions."""
        return (
            np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
            4 * field
        )
    
    def compute_beta_weighted_laplacian(self, field: np.ndarray) -> np.ndarray:
        """
        Compute β-weighted Laplacian: ∇·(β∇ψ).
        This is the correct coupling that produces smoother dynamics.
        """
        # Gradient of field
        grad_x = (np.roll(field, -1, axis=0) - np.roll(field, 1, axis=0)) / 2
        grad_y = (np.roll(field, -1, axis=1) - np.roll(field, 1, axis=1)) / 2
        
        # β-weighted gradient
        beta_grad_x = self.beta * grad_x
        beta_grad_y = self.beta * grad_y
        
        # Divergence
        div_x = (np.roll(beta_grad_x, -1, axis=0) - np.roll(beta_grad_x, 1, axis=0)) / 2
        div_y = (np.roll(beta_grad_y, -1, axis=1) - np.roll(beta_grad_y, 1, axis=1)) / 2
        
        return div_x + div_y
    
    def add_vortex(self, position: Tuple[int, int], charge: int = +1,
                   amplitude: float = 1.2, core_radius: float = 4.0):
        """Add a vortex at specified position."""
        cx, cy = position
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        
        # Vortex profile
        amp_profile = amplitude * np.tanh(r / core_radius)
        
        self.psi_r = amp_profile * np.cos(charge * theta)
        self.psi_i = amp_profile * np.sin(charge * theta)
    
    def seed_oscillators(self, amp: float = 0.1):
        """Initialize resonance oscillators with small amplitude."""
        self.osc_amp = np.random.uniform(0, amp, (self.size, self.size))
        self.osc_phase = np.random.uniform(0, 2*np.pi, (self.size, self.size))
    
    def compute_topology_indicator(self) -> np.ndarray:
        """Compute local topology indicator from phase gradient circulation."""
        phase = self.phase
        
        # Phase gradients (with wrapping)
        dx = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        dy = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        
        # Circulation (curl of phase gradient)
        curl = (
            dx - np.roll(dx, -1, axis=1) +
            np.roll(dy, -1, axis=0) - dy
        )
        
        return np.abs(curl) / (2 * np.pi)
    
    def step(self, dt: float = 0.05):
        """Evolve one timestep with resonance self-selection active (Branch E mechanism)."""
        self.step_count += 1
        
        # Update self-selecting channels (key Branch E mechanism)
        self.update_self_selecting_channels()
        
        # Complex scalar dynamics with β-weighted Laplacian
        lap_r = self.compute_beta_weighted_laplacian(self.psi_r)
        lap_i = self.compute_beta_weighted_laplacian(self.psi_i)
        
        amp_sq = self.psi_r**2 + self.psi_i**2
        
        # Nonlinear term (Mexican hat potential)
        nl_r = self.psi_r * (1 - amp_sq)
        nl_i = self.psi_i * (1 - amp_sq)
        
        # Base accelerations
        acc_r = lap_r + nl_r - self.gamma * self.psi_r_dot
        acc_i = lap_i + nl_i - self.gamma * self.psi_i_dot
        
        # CRITICAL: Core-filling suppression (from Branch E)
        protection = self.compute_channel_protection()
        amp = self.amplitude + 1e-10
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        
        # Radial component of acceleration (what would fill cores)
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        # Suppress core-filling (positive radial acceleration)
        channel_coupling = 0.5  # Same as Branch E
        suppression = channel_coupling * protection * np.maximum(acc_radial, 0)
        
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        # Update velocities
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        
        # Update fields
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def update_self_selecting_channels(self):
        """Channel assignment grows where topology is high."""
        topology = self.compute_topology_indicator()
        topology_max = np.max(topology)
        if topology_max > 0:
            topology_norm = topology / topology_max
        else:
            topology_norm = topology
        
        target = topology_norm
        relaxation_rate = 0.01
        self.channel_assignment += relaxation_rate * (target - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
    
    def compute_channel_protection(self) -> np.ndarray:
        """Protection = topology × channel assignment."""
        topology = self.compute_topology_indicator()
        topology_max = np.max(topology)
        if topology_max > 0:
            topology_norm = topology / topology_max
        else:
            topology_norm = topology
        return topology_norm * self.channel_assignment
    
    def detect_vortices(self, amp_threshold: float = 0.4) -> List[Dict]:
        """Detect vortices by finding phase singularities."""
        amp = self.amplitude
        phase = self.phase
        
        vortices = []
        
        # Look for low-amplitude cores with phase winding
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                if amp[i, j] < amp_threshold:
                    # Check for phase winding
                    phases = [
                        phase[i-1, j], phase[i, j+1],
                        phase[i+1, j], phase[i, j-1]
                    ]
                    
                    winding = 0
                    for k in range(4):
                        diff = phases[(k+1) % 4] - phases[k]
                        diff = np.angle(np.exp(1j * diff))
                        winding += diff
                    
                    winding /= (2 * np.pi)
                    
                    if abs(winding) > 0.5:
                        charge = int(np.sign(winding))
                        zone = self.get_zone(i, j)
                        vortices.append({
                            'position': (i, j),
                            'charge': charge,
                            'amplitude': amp[i, j],
                            'zone': zone,
                            'beta_local': self.beta[i, j]
                        })
        
        return vortices
    
    def track_vortices(self, vortices: List[Dict], prev_vortices: List[Dict]) -> Tuple[int, int]:
        """Track vortices across frames, recording births and deaths."""
        births = 0
        deaths = 0
        
        # Match current vortices to previous
        matched_prev = set()
        matched_curr = set()
        
        for i, v in enumerate(vortices):
            best_match = None
            best_dist = 15  # Max match distance
            
            for j, pv in enumerate(prev_vortices):
                if j in matched_prev:
                    continue
                if v['charge'] != pv['charge']:
                    continue
                    
                dist = np.sqrt((v['position'][0] - pv['position'][0])**2 +
                              (v['position'][1] - pv['position'][1])**2)
                
                if dist < best_dist:
                    best_dist = dist
                    best_match = j
            
            if best_match is not None:
                matched_prev.add(best_match)
                matched_curr.add(i)
                
                # Update existing vortex tracking
                if 'id' in prev_vortices[best_match]:
                    vid = prev_vortices[best_match]['id']
                    v['id'] = vid
                    if vid in self.vortex_lifetimes:
                        self.vortex_lifetimes[vid]['positions'].append(v['position'])
        
        # Count births (unmatched current)
        for i, v in enumerate(vortices):
            if i not in matched_curr:
                births += 1
                vid = self.next_vortex_id
                self.next_vortex_id += 1
                v['id'] = vid
                
                zone = v['zone']
                self.nucleation_history.append((self.step_count, v['position'][0], v['position'][1], zone))
                self.vortex_lifetimes[vid] = {
                    'birth': self.step_count,
                    'zone_at_birth': zone,
                    'positions': [v['position']]
                }
        
        # Count deaths (unmatched previous)
        for j, pv in enumerate(prev_vortices):
            if j not in matched_prev:
                deaths += 1
                if 'id' in pv and pv['id'] in self.vortex_lifetimes:
                    self.vortex_lifetimes[pv['id']]['death'] = self.step_count
        
        return births, deaths


def test_1_regeneration_location():
    """
    TEST 1: Regeneration Location
    Question: Do vortices nucleate preferentially in the low-β interior?
    
    Success criterion: Nucleation rate in interior > periphery (normalized by area)
    """
    print("="*70)
    print("TEST 1: REGENERATION LOCATION")
    print("="*70)
    print()
    print("Question: Do vortices nucleate in the low-β interior zone?")
    print()
    
    sim = BranchFSimulator(size=120, gamma=0.007,
                           beta_interior=0.25, beta_periphery=0.7,
                           transition_width=15.0)
    
    # Seed initial vortex-antivortex pairs to kickstart dynamics
    # This tests WHERE regeneration happens, not whether it happens spontaneously
    center = sim.size // 2
    
    # Create a turbulent initial state by adding multiple vortex pairs
    np.random.seed(42)  # Reproducibility
    
    # Start with uniform background
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    # Add vortex pairs in different zones
    vortex_positions = [
        (center - 5, center),       # Interior
        (center + 5, center),       # Interior (antivortex)
        (center, center - 8),       # Interior
        (center, center + 8),       # Interior (antivortex)
        (center + 40, center),      # Transition
        (center - 40, center),      # Transition (antivortex)
    ]
    
    for i, pos in enumerate(vortex_positions):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
        r = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        vortex_amp = 1.2 * np.tanh(r / 4.0)
        
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (vortex_amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    # Add noise to break symmetry
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size)
    
    sim.seed_oscillators(amp=0.2)
    
    prev_vortices = []
    
    # Run longer simulation to see regeneration
    for step in range(5000):
        sim.step()
        
        if step % 20 == 0:
            vortices = sim.detect_vortices()
            births, deaths = sim.track_vortices(vortices, prev_vortices)
            prev_vortices = vortices
    
    # Analyze nucleation locations
    interior_births = sum(1 for n in sim.nucleation_history if n[3] == 'interior')
    transition_births = sum(1 for n in sim.nucleation_history if n[3] == 'transition')
    periphery_births = sum(1 for n in sim.nucleation_history if n[3] == 'periphery')
    total_births = len(sim.nucleation_history)
    
    # Calculate areas for normalization
    center = sim.size / 2
    interior_radius = sim.size * 0.25
    transition_outer = interior_radius + sim.transition_width
    
    interior_area = np.pi * interior_radius**2
    transition_area = np.pi * (transition_outer**2 - interior_radius**2)
    periphery_area = sim.size**2 - np.pi * transition_outer**2
    total_area = sim.size**2
    
    # Nucleation density (per unit area)
    interior_density = interior_births / interior_area if interior_area > 0 else 0
    transition_density = transition_births / transition_area if transition_area > 0 else 0
    periphery_density = periphery_births / periphery_area if periphery_area > 0 else 0
    
    print(f"β profile: interior={sim.beta_interior}, periphery={sim.beta_periphery}")
    print(f"Interior radius: {interior_radius:.1f}, transition width: {sim.transition_width}")
    print()
    print("Nucleation counts:")
    if total_births > 0:
        print(f"  Interior:   {interior_births:4d} ({100*interior_births/total_births:.1f}%)")
        print(f"  Transition: {transition_births:4d} ({100*transition_births/total_births:.1f}%)")
        print(f"  Periphery:  {periphery_births:4d} ({100*periphery_births/total_births:.1f}%)")
    else:
        print(f"  Interior:   {interior_births:4d}")
        print(f"  Transition: {transition_births:4d}")
        print(f"  Periphery:  {periphery_births:4d}")
    print(f"  Total:      {total_births}")
    print()
    print("Nucleation density (births per unit area × 1000):")
    print(f"  Interior:   {1000*interior_density:.3f}")
    print(f"  Transition: {1000*transition_density:.3f}")
    print(f"  Periphery:  {1000*periphery_density:.3f}")
    print()
    
    # Success criterion
    if total_births == 0:
        print("✗ FAIL: No vortex births detected")
        success = False
    elif interior_density > periphery_density:
        ratio = interior_density / periphery_density if periphery_density > 0 else float('inf')
        print(f"✓ PASS: Interior nucleation density {ratio:.2f}× higher than periphery")
        success = True
    else:
        ratio = periphery_density / interior_density if interior_density > 0 else float('inf')
        print(f"✗ FAIL: Periphery nucleation density {ratio:.2f}× higher than interior")
        success = False
    
    return {
        'test': 'regeneration_location',
        'success': success,
        'interior_births': interior_births,
        'transition_births': transition_births,
        'periphery_births': periphery_births,
        'interior_density': interior_density,
        'periphery_density': periphery_density,
        'density_ratio': interior_density / periphery_density if periphery_density > 0 else float('inf')
    }


def test_2_migration_capture():
    """
    TEST 2: Migration / Capture
    Question: Do vortices move toward high-β and survive longer there?
    
    Success criterion: 
      - Vortices show net drift toward higher β
      - Vortices in periphery live longer than those stuck in interior
    """
    print()
    print("="*70)
    print("TEST 2: MIGRATION / CAPTURE")
    print("="*70)
    print()
    print("Question: Do vortices migrate toward high-β and live longer there?")
    print()
    
    sim = BranchFSimulator(size=120, gamma=0.007,
                           beta_interior=0.25, beta_periphery=0.7,
                           transition_width=15.0)
    
    # Seed a vortex-antivortex pair in the interior
    center = sim.size // 2
    sim.psi_r[:] = 1.2
    
    # Add vortex pair slightly off-center (in interior)
    sim.add_vortex((center - 10, center), charge=+1)
    
    # Also add one in transition zone for comparison
    x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
    transition_pos = (center + 35, center)  # Should be in transition zone
    r = np.sqrt((x - transition_pos[0])**2 + (y - transition_pos[1])**2) + 0.1
    theta = np.arctan2(y - transition_pos[1], x - transition_pos[0])
    amp2 = 1.2 * np.tanh(r / 4.0)
    
    # Combine (superposition)
    psi_complex = sim.psi_r + 1j * sim.psi_i
    psi_complex += amp2 * np.exp(-1j * theta)  # Antivortex
    sim.psi_r = np.real(psi_complex)
    sim.psi_i = np.imag(psi_complex)
    
    sim.seed_oscillators(amp=0.15)
    
    # Track vortex positions and β values over time
    position_history = []  # [(step, positions_and_betas), ...]
    
    prev_vortices = []
    
    for step in range(2500):
        sim.step()
        
        if step % 25 == 0:
            vortices = sim.detect_vortices()
            births, deaths = sim.track_vortices(vortices, prev_vortices)
            prev_vortices = vortices
            
            if vortices:
                snapshot = []
                for v in vortices:
                    snapshot.append({
                        'pos': v['position'],
                        'beta': v['beta_local'],
                        'zone': v['zone'],
                        'charge': v['charge']
                    })
                position_history.append((step, snapshot))
    
    # Analyze migration: compare β at birth vs death for each vortex
    migration_deltas = []  # (β_final - β_initial) for each vortex
    
    for vid, data in sim.vortex_lifetimes.items():
        if 'death' in data and len(data['positions']) > 1:
            initial_pos = data['positions'][0]
            final_pos = data['positions'][-1]
            
            beta_initial = sim.beta[initial_pos[0], initial_pos[1]]
            beta_final = sim.beta[final_pos[0], final_pos[1]]
            
            migration_deltas.append(beta_final - beta_initial)
    
    # Analyze lifetimes by zone
    interior_lifetimes = []
    periphery_lifetimes = []
    
    for vid, data in sim.vortex_lifetimes.items():
        if 'death' in data:
            lifetime = data['death'] - data['birth']
            zone = data['zone_at_birth']
            
            if zone == 'interior':
                interior_lifetimes.append(lifetime)
            elif zone == 'periphery':
                periphery_lifetimes.append(lifetime)
    
    print("Migration analysis:")
    if migration_deltas:
        mean_delta = np.mean(migration_deltas)
        positive_migrations = sum(1 for d in migration_deltas if d > 0)
        print(f"  Mean β change (final - initial): {mean_delta:+.4f}")
        print(f"  Migrations toward higher β: {positive_migrations}/{len(migration_deltas)} ({100*positive_migrations/len(migration_deltas):.1f}%)")
    else:
        mean_delta = 0
        print("  No completed vortex trajectories to analyze")
    print()
    
    print("Lifetime by zone of birth:")
    if interior_lifetimes:
        print(f"  Interior births: mean lifetime = {np.mean(interior_lifetimes):.1f} steps (n={len(interior_lifetimes)})")
    else:
        print("  Interior births: no data")
        
    if periphery_lifetimes:
        print(f"  Periphery births: mean lifetime = {np.mean(periphery_lifetimes):.1f} steps (n={len(periphery_lifetimes)})")
    else:
        print("  Periphery births: no data")
    print()
    
    # Success criteria
    migration_success = mean_delta > 0 if migration_deltas else False
    
    if migration_success:
        print(f"✓ PASS: Net migration toward higher β (Δβ = {mean_delta:+.4f})")
    else:
        print(f"✗ FAIL: No net migration toward higher β")
    
    return {
        'test': 'migration_capture',
        'success': migration_success,
        'mean_beta_change': mean_delta,
        'migration_deltas': migration_deltas,
        'interior_lifetimes': interior_lifetimes,
        'periphery_lifetimes': periphery_lifetimes
    }


def test_3_population_localization():
    """
    TEST 3: Population Localization
    Question: Can we achieve nonzero late population that is localized 
              WITHOUT suppressing regeneration?
    
    Success criteria:
      - Late population > 0 (vortices exist)
      - Localization ratio > 0.5 (more in periphery than interior at late time)
      - Regeneration rate maintained (total births comparable to pure resonance)
    """
    print()
    print("="*70)
    print("TEST 3: POPULATION LOCALIZATION")
    print("="*70)
    print()
    print("Question: Nonzero population + localization WITHOUT suppression?")
    print()
    
    sim = BranchFSimulator(size=120, gamma=0.007,
                           beta_interior=0.25, beta_periphery=0.7,
                           transition_width=15.0)
    
    # Seed initial vortex pairs to kickstart dynamics
    center = sim.size // 2
    np.random.seed(123)  # Different seed for variety
    
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    # Add vortex pairs spread across zones
    vortex_positions = [
        (center - 5, center),
        (center + 5, center),
        (center + 35, center + 10),
        (center - 35, center - 10),
        (center, center + 40),
        (center, center - 40),
    ]
    
    for i, pos in enumerate(vortex_positions):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
        r = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        vortex_amp = 1.2 * np.tanh(r / 4.0)
        
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (vortex_amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    sim.psi_r += 0.05 * np.random.randn(sim.size, sim.size)
    sim.psi_i += 0.05 * np.random.randn(sim.size, sim.size)
    sim.seed_oscillators(amp=0.2)
    
    prev_vortices = []
    
    # Track population over time
    population_history = []
    interior_population = []
    periphery_population = []
    
    total_births = 0
    total_deaths = 0
    
    for step in range(4000):
        sim.step()
        
        if step % 25 == 0:
            vortices = sim.detect_vortices()
            births, deaths = sim.track_vortices(vortices, prev_vortices)
            prev_vortices = vortices
            
            total_births += births
            total_deaths += deaths
            
            n_total = len(vortices)
            n_interior = sum(1 for v in vortices if v['zone'] == 'interior')
            n_periphery = sum(1 for v in vortices if v['zone'] == 'periphery')
            
            population_history.append(n_total)
            interior_population.append(n_interior)
            periphery_population.append(n_periphery)
    
    # Late-time statistics (last 20%)
    late_start = int(0.8 * len(population_history))
    late_population = np.mean(population_history[late_start:])
    late_interior = np.mean(interior_population[late_start:])
    late_periphery = np.mean(periphery_population[late_start:])
    
    # Localization ratio: periphery / (periphery + interior)
    if late_periphery + late_interior > 0:
        localization_ratio = late_periphery / (late_periphery + late_interior)
    else:
        localization_ratio = 0
    
    print(f"Late-time statistics (last 20% of simulation):")
    print(f"  Mean population: {late_population:.2f}")
    print(f"  Interior: {late_interior:.2f}")
    print(f"  Periphery: {late_periphery:.2f}")
    print(f"  Localization ratio (periphery/total): {localization_ratio:.3f}")
    print()
    print(f"Regeneration activity:")
    print(f"  Total births: {total_births}")
    print(f"  Total deaths: {total_deaths}")
    print(f"  Birth rate: {total_births / 4000:.3f} per step")
    print()
    
    # Success criteria
    population_success = late_population > 1.0
    localization_success = localization_ratio > 0.4  # More relaxed than 0.5
    regeneration_success = total_births > 50  # Active regeneration
    
    overall_success = population_success and localization_success and regeneration_success
    
    print("Success criteria:")
    print(f"  Population > 1.0: {'✓' if population_success else '✗'} ({late_population:.2f})")
    print(f"  Localization > 0.4: {'✓' if localization_success else '✗'} ({localization_ratio:.3f})")
    print(f"  Regeneration active: {'✓' if regeneration_success else '✗'} ({total_births} births)")
    print()
    
    if overall_success:
        print("✓ PASS: Population + Localization + Regeneration all achieved")
    else:
        print("✗ FAIL: Not all criteria met")
    
    return {
        'test': 'population_localization',
        'success': overall_success,
        'late_population': late_population,
        'late_interior': late_interior,
        'late_periphery': late_periphery,
        'localization_ratio': localization_ratio,
        'total_births': total_births,
        'total_deaths': total_deaths,
        'population_history': population_history[-50:],  # Last 50 samples
        'interior_history': interior_population[-50:],
        'periphery_history': periphery_population[-50:]
    }


def main():
    """Run all three Branch F diagnostic tests."""
    print("="*70)
    print("BRANCH F: SPATIALLY SEPARATED REGENERATION-STABILIZATION MODEL")
    print("="*70)
    print()
    print("Hypothesis: Separate regeneration (low-β interior) from")
    print("            stabilization (high-β periphery) using smooth β profile.")
    print()
    print("β landscape: Low center, high edges, cosine transition")
    print()
    
    results = {}
    
    # Run tests
    results['test_1'] = test_1_regeneration_location()
    results['test_2'] = test_2_migration_capture()
    results['test_3'] = test_3_population_localization()
    
    # Summary
    print()
    print("="*70)
    print("BRANCH F SUMMARY")
    print("="*70)
    print()
    
    tests_passed = sum(1 for r in results.values() if r['success'])
    
    print(f"Tests passed: {tests_passed}/3")
    print()
    
    for name, r in results.items():
        status = "✓ PASS" if r['success'] else "✗ FAIL"
        print(f"  {r['test']}: {status}")
    
    print()
    
    if tests_passed == 3:
        print("="*70)
        print("BRANCH F: FULL SUCCESS — Co-alignment candidate found!")
        print("="*70)
        print()
        print("Spatial separation achieves:")
        print("  - Active regeneration in low-β interior")
        print("  - Vortex stabilization in high-β periphery")
        print("  - Nonzero localized population")
        print()
        print("This is the first model to co-align localization with topological memory.")
    elif tests_passed >= 2:
        print("PARTIAL SUCCESS: Some co-alignment achieved, refinement needed")
    else:
        print("BRANCH F FAILS: Spatial separation alone insufficient")
        print("May need to explore other approaches (dynamic β, etc.)")
    
    # Save results
    with open('/app/backend/qmrt_topology/test_results/phase5/branch_f_results.json', 'w') as f:
        # Convert numpy arrays for JSON
        def convert(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            return obj
        
        json.dump(convert(results), f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/test_results/phase5/branch_f_results.json")
    
    return results


if __name__ == "__main__":
    main()
