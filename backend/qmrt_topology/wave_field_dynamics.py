#!/usr/bin/env python3
"""
QMRT Wave-Capable Field Dynamics
================================
Upgrade from parabolic (heat equation) to hyperbolic (wave equation):

Before: ∂φ/∂t = D∇²φ + sources  (diffusive, no causality)
After:  ∂²φ/∂t² = c²∇²φ - γ∂φ/∂t + sources  (wave + damping)

This gives:
- Finite propagation speed (c)
- Wavefronts
- Interference
- Causality structure (light-cone precursor)
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import json


@dataclass
class Defect:
    """A topological defect."""
    position: np.ndarray
    charge: int
    velocity: np.ndarray = None
    core_radius: float = 1.5
    lifetime: int = 0
    id: int = 0
    
    def __post_init__(self):
        if self.velocity is None:
            self.velocity = np.zeros(2)
        self.position = np.array(self.position, dtype=float)
        self.velocity = np.array(self.velocity, dtype=float)


@dataclass
class WaveParams:
    """Parameters for wave-capable field dynamics."""
    # Wave equation parameters
    wave_speed: float = 1.0          # c in ∂²φ/∂t² = c²∇²φ
    wave_damping: float = 0.05       # γ in -γ∂φ/∂t (prevents infinite ringing)
    
    # Field properties
    field_cap: float = 5.0
    
    # Defect-field coupling
    defect_field_strength: float = 0.5
    defect_well_radius: float = 3.0
    field_force_strength: float = 0.8
    direct_force_strength: float = 0.2
    
    # Defect dynamics
    damping: float = 0.15
    max_speed: float = 2.0
    
    # Creation/Annihilation  
    creation_threshold: float = 2.0
    creation_rate: float = 0.002
    creation_cost: float = 0.8
    annihilation_radius: float = 1.5
    annihilation_injection: float = 0.6
    
    # Boundary
    boundary: str = "periodic"


class WaveFieldSystem:
    """
    A wave-capable field-defect system.
    
    Key upgrade: Field now obeys damped wave equation:
    ∂²φ/∂t² = c²∇²φ - γ∂φ/∂t + sources
    
    This gives finite-speed propagation instead of instant diffusion.
    """
    
    def __init__(self, size: Tuple[int, int], params: WaveParams = None):
        self.size = size
        self.params = params or WaveParams()
        self.defects: List[Defect] = []
        self.time = 0
        self.next_id = 0
        
        # THE FIELD: φ(x,y)
        self.field = np.zeros(size, dtype=float)
        
        # FIELD VELOCITY: ∂φ/∂t (needed for second-order dynamics)
        self.field_velocity = np.zeros(size, dtype=float)
        
        # Energy field for creation
        self.energy_field = np.zeros(size, dtype=float)
        self.energy_velocity = np.zeros(size, dtype=float)
        
        # Metrics
        self.metrics = {
            'defect_count': [],
            'field_energy': [],
            'kinetic_energy': [],  # (∂φ/∂t)² term
            'potential_energy': [],  # (∇φ)² term
            'creations': [],
            'annihilations': [],
            'max_field': [],
            'wavefront_radius': [],
        }
        
        self.events = []
    
    def compute_laplacian(self, field: np.ndarray) -> np.ndarray:
        """Compute ∇²φ with periodic boundaries."""
        return (
            np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
            4 * field
        )
    
    def compute_field_gradient(self, position: np.ndarray) -> np.ndarray:
        """Compute ∇φ at position."""
        x, y = position
        xi, yi = int(x) % self.size[0], int(y) % self.size[1]
        
        dx = (self.field[(xi+1) % self.size[0], yi] - 
              self.field[(xi-1) % self.size[0], yi]) / 2.0
        dy = (self.field[xi, (yi+1) % self.size[1]] - 
              self.field[xi, (yi-1) % self.size[1]]) / 2.0
        
        return np.array([dx, dy])
    
    # =========================================================================
    # WAVE EQUATION EVOLUTION (THE KEY UPGRADE)
    # =========================================================================
    
    def evolve_field_wave(self, dt: float):
        """
        Evolve field using damped wave equation with VARIABLE SPEED:
        
        ∂²φ/∂t² = c_eff(x)²∇²φ - γ∂φ/∂t
        
        Where c_eff DECREASES in high-energy regions (channel guiding)
        This creates waveguide behavior: waves slow down and concentrate in channels
        """
        p = self.params
        
        # VARIABLE WAVE SPEED: LOWER in channels (high energy)
        # This traps/guides waves in channel regions
        c_local = p.wave_speed / (1 + 0.4 * self.energy_field / (1 + self.energy_field))
        
        # Compute Laplacian
        laplacian = self.compute_laplacian(self.field)
        
        # Wave equation with local c
        acceleration = (c_local**2 * laplacian - 
                       p.wave_damping * self.field_velocity)
        
        # Update velocity
        self.field_velocity += acceleration * dt
        
        # Update field
        self.field += self.field_velocity * dt
        
        # Cap field
        np.clip(self.field, -p.field_cap, p.field_cap, out=self.field)
        
        # Evolve energy field (slow diffusion to maintain structure)
        energy_laplacian = self.compute_laplacian(self.energy_field)
        self.energy_field += 0.02 * energy_laplacian * dt  # Slower diffusion
        self.energy_field *= (1 - 0.001 * dt)  # Very slow decay
        np.clip(self.energy_field, 0, p.field_cap, out=self.energy_field)
    
    # =========================================================================
    # DEFECT-FIELD COUPLING (same as before)
    # =========================================================================
    
    def update_field_from_defects(self, dt: float):
        """Defects inject into field velocity (act as sources)."""
        p = self.params
        
        for defect in self.defects:
            x, y = defect.position
            xi, yi = int(x), int(y)
            r = int(p.defect_well_radius) + 1
            
            for i in range(xi - r, xi + r + 1):
                for j in range(yi - r, yi + r + 1):
                    ii = i % self.size[0]
                    jj = j % self.size[1]
                    
                    dist = np.sqrt((i - x)**2 + (j - y)**2)
                    if dist < p.defect_well_radius and dist > 0.1:
                        # Inject into field velocity (source term)
                        strength = np.exp(-dist**2 / (2 * defect.core_radius**2))
                        self.field_velocity[ii, jj] += (
                            defect.charge * p.defect_field_strength * strength * dt
                        )
    
    def compute_forces(self) -> List[np.ndarray]:
        """Compute forces on defects from field gradient."""
        forces = [np.zeros(2) for _ in self.defects]
        p = self.params
        
        for i, defect in enumerate(self.defects):
            # Field gradient force
            grad = self.compute_field_gradient(defect.position)
            field_force = -defect.charge * p.field_force_strength * grad
            forces[i] += field_force
            
            # Direct pairwise
            for j, other in enumerate(self.defects):
                if i >= j:
                    continue
                
                delta = self._periodic_delta(defect.position, other.position)
                dist = np.linalg.norm(delta)
                
                if dist < 0.5:
                    continue
                
                force_mag = p.direct_force_strength * defect.charge * other.charge / dist**2
                force_dir = delta / dist
                
                forces[i] -= force_mag * force_dir
                forces[j] += force_mag * force_dir
        
        return forces
    
    def _periodic_delta(self, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
        delta = p2 - p1
        for dim in [0, 1]:
            if abs(delta[dim]) > self.size[dim] / 2:
                delta[dim] -= np.sign(delta[dim]) * self.size[dim]
        return delta
    
    def update_defects(self, dt: float):
        """Update defect motion."""
        forces = self.compute_forces()
        p = self.params
        
        for defect, force in zip(self.defects, forces):
            defect.velocity += force * dt
            defect.velocity *= (1 - p.damping)
            
            speed = np.linalg.norm(defect.velocity)
            if speed > p.max_speed:
                defect.velocity *= p.max_speed / speed
            
            defect.position += defect.velocity * dt
            defect.position[0] %= self.size[0]
            defect.position[1] %= self.size[1]
            defect.lifetime += 1
    
    # =========================================================================
    # CREATION / ANNIHILATION
    # =========================================================================
    
    def attempt_creation(self) -> int:
        """Create defect pairs from energy field."""
        p = self.params
        created = 0
        n_samples = max(1, int(self.size[0] * self.size[1] * p.creation_rate))
        
        for _ in range(n_samples):
            pos = np.array([
                np.random.uniform(0, self.size[0]),
                np.random.uniform(0, self.size[1])
            ])
            xi, yi = int(pos[0]) % self.size[0], int(pos[1]) % self.size[1]
            
            if self.energy_field[xi, yi] > p.creation_threshold:
                self.energy_field[xi, yi] -= p.creation_cost
                
                angle = np.random.uniform(0, 2*np.pi)
                offset = 2.0 * np.array([np.cos(angle), np.sin(angle)])
                v = 0.3 * np.array([np.cos(angle), np.sin(angle)])
                
                self.add_defect(pos + offset/2, charge=+1, velocity=v)
                self.add_defect(pos - offset/2, charge=-1, velocity=-v)
                created += 1
        
        return created
    
    def check_annihilation(self) -> int:
        """Annihilate opposite pairs."""
        p = self.params
        annihilated = 0
        to_remove = set()
        
        for i, d1 in enumerate(self.defects):
            if i in to_remove:
                continue
            for j, d2 in enumerate(self.defects):
                if j <= i or j in to_remove:
                    continue
                if d1.charge * d2.charge >= 0:
                    continue
                
                delta = self._periodic_delta(d1.position, d2.position)
                dist = np.linalg.norm(delta)
                
                if dist < p.annihilation_radius:
                    to_remove.add(i)
                    to_remove.add(j)
                    
                    midpoint = d1.position + delta / 2
                    self._inject_energy(midpoint, p.annihilation_injection)
                    
                    # Also create a field pulse (wave source)
                    xi, yi = int(midpoint[0]) % self.size[0], int(midpoint[1]) % self.size[1]
                    self.field_velocity[xi, yi] += 1.0  # Impulse
                    
                    annihilated += 1
        
        self.defects = [d for i, d in enumerate(self.defects) if i not in to_remove]
        return annihilated
    
    def _inject_energy(self, position: np.ndarray, amount: float, radius: float = 3.0):
        """Inject energy for recycling."""
        x, y = int(position[0]), int(position[1])
        r = int(radius)
        
        cells = []
        total_w = 0
        for i in range(x - r, x + r + 1):
            for j in range(y - r, y + r + 1):
                ii, jj = i % self.size[0], j % self.size[1]
                dist = np.sqrt((i - x)**2 + (j - y)**2)
                if dist < radius:
                    w = 1 - dist / radius
                    cells.append((ii, jj, w))
                    total_w += w
        
        if total_w > 0:
            for ii, jj, w in cells:
                self.energy_field[ii, jj] += amount * w / total_w
    
    # =========================================================================
    # WAVE PULSE INJECTION
    # =========================================================================
    
    def inject_wave_pulse(self, position: np.ndarray, amplitude: float, radius: float = 3.0):
        """
        Inject a wave pulse (impulse to field velocity).
        This creates an outgoing circular wave.
        """
        x, y = int(position[0]), int(position[1])
        r = int(radius) + 1
        
        for i in range(x - r, x + r + 1):
            for j in range(y - r, y + r + 1):
                ii, jj = i % self.size[0], j % self.size[1]
                dist = np.sqrt((i - x)**2 + (j - y)**2)
                if dist < radius:
                    # Gaussian pulse
                    strength = amplitude * np.exp(-dist**2 / (2 * (radius/2)**2))
                    self.field_velocity[ii, jj] += strength
    
    # =========================================================================
    # MAIN STEP
    # =========================================================================
    
    def step(self, dt: float = 0.1) -> dict:
        """Execute one step."""
        # Defects act as sources
        self.update_field_from_defects(dt)
        
        # Wave equation evolution
        self.evolve_field_wave(dt)
        
        # Creation
        created = self.attempt_creation()
        
        # Defect motion
        self.update_defects(dt)
        
        # Annihilation
        annihilated = self.check_annihilation()
        
        # Metrics
        self._record_metrics(created, annihilated)
        
        self.time += 1
        
        return {
            'time': self.time,
            'n_defects': len(self.defects),
            'created': created,
            'annihilated': annihilated,
        }
    
    def _record_metrics(self, created: int, annihilated: int):
        """Record metrics."""
        self.metrics['defect_count'].append(len(self.defects))
        self.metrics['field_energy'].append(float(np.sum(np.abs(self.field))))
        
        # Wave energy: kinetic (velocity²) + potential (gradient²)
        kinetic = 0.5 * np.sum(self.field_velocity**2)
        
        grad_x = np.roll(self.field, -1, axis=0) - self.field
        grad_y = np.roll(self.field, -1, axis=1) - self.field
        potential = 0.5 * self.params.wave_speed**2 * np.sum(grad_x**2 + grad_y**2)
        
        self.metrics['kinetic_energy'].append(float(kinetic))
        self.metrics['potential_energy'].append(float(potential))
        self.metrics['creations'].append(created)
        self.metrics['annihilations'].append(annihilated)
        self.metrics['max_field'].append(float(np.max(np.abs(self.field))))
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def add_defect(self, position, charge, velocity=None):
        defect = Defect(
            position=np.array(position, dtype=float),
            charge=charge,
            velocity=velocity if velocity is not None else np.zeros(2),
            id=self.next_id
        )
        self.next_id += 1
        self.defects.append(defect)
        return defect
    
    def create_random_pairs(self, n_pairs):
        for _ in range(n_pairs):
            center = np.array([
                np.random.uniform(0, self.size[0]),
                np.random.uniform(0, self.size[1])
            ])
            angle = np.random.uniform(0, 2*np.pi)
            offset = 2.0 * np.array([np.cos(angle), np.sin(angle)])
            
            self.add_defect(center + offset/2, charge=+1)
            self.add_defect(center - offset/2, charge=-1)
    
    def get_summary(self):
        return {
            'time': self.time,
            'n_defects': len(self.defects),
            'total_creations': sum(self.metrics['creations']),
            'total_annihilations': sum(self.metrics['annihilations']),
            'metrics': self.metrics
        }


# =============================================================================
# WAVE PROPAGATION TEST
# =============================================================================

def test_wave_propagation():
    """Test that pulses now propagate as waves, not diffusion."""
    print("=" * 60)
    print("WAVE PROPAGATION TEST")
    print("=" * 60)
    
    np.random.seed(42)
    
    params = WaveParams(
        wave_speed=2.0,           # Propagation speed
        wave_damping=0.02,        # Light damping
        creation_threshold=100,   # Disable creation
        creation_rate=0,
    )
    
    system = WaveFieldSystem(size=(60, 60), params=params)
    
    # Inject wave pulse at center
    center = np.array([30.0, 30.0])
    system.inject_wave_pulse(center, amplitude=3.0, radius=3.0)
    
    print(f"Injected wave pulse at center")
    print(f"Wave speed c = {params.wave_speed}")
    print(f"Expected radius at t=100: r ≈ {params.wave_speed * 100 * 0.1:.1f}")
    
    # Track wavefront
    times = []
    radii = []
    
    for t in range(200):
        system.step(dt=0.1)
        
        if t % 20 == 0 and t > 0:
            # Find wavefront radius (where |φ| > threshold)
            threshold = 0.1
            above = np.where(np.abs(system.field) > threshold)
            
            if len(above[0]) > 0:
                distances = np.sqrt((above[0] - 30)**2 + (above[1] - 30)**2)
                radius = np.max(distances)  # Leading edge
            else:
                radius = 0
            
            times.append(t * 0.1)  # Real time
            radii.append(radius)
            print(f"  t={t*0.1:.1f}: wavefront radius = {radius:.1f}")
    
    # Analyze: wave (r~t) or diffusion (r~√t)?
    times = np.array(times)
    radii = np.array(radii)
    
    # Linear fit for wave
    if len(times) > 3:
        slope = np.polyfit(times, radii, 1)[0]
        print(f"\nWavefront velocity: {slope:.2f} (expected: {params.wave_speed})")
        
        if slope > params.wave_speed * 0.5:
            print("✓ WAVE-LIKE propagation detected!")
        else:
            print("~ Still partially diffusive")
    
    return system, times, radii


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    system, times, radii = test_wave_propagation()
    
    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Wavefront radius vs time
    ax = axes[0]
    ax.plot(times, radii, 'bo-', markersize=8, linewidth=2)
    
    # Expected wave line
    expected = system.params.wave_speed * times
    ax.plot(times, expected, 'r--', linewidth=2, label=f'Expected (c={system.params.wave_speed})')
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Wavefront Radius', fontsize=12)
    ax.set_title('Wave Propagation Test\n(Should be linear, not √t)', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Final field state
    ax = axes[1]
    im = ax.imshow(system.field.T, origin='lower', cmap='RdBu', 
                   vmin=-1, vmax=1, extent=[0, 60, 0, 60])
    ax.scatter(30, 30, marker='x', c='white', s=100, linewidth=2)
    ax.set_title(f'Field at t={system.time * 0.1:.1f}', fontsize=12)
    plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/wave_propagation_test.png', dpi=150)
    print("\nSaved wave_propagation_test.png")
