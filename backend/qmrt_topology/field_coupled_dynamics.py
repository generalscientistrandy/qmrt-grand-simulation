#!/usr/bin/env python3
"""
QMRT Field-Coupled Defect Dynamics
==================================
Priority 2: Propagation-medium feedback (backreaction)

Key transition:
- Before: Direct pairwise forces between defects
- After: Field-mediated interaction through continuous medium

This implements:
1. Continuous field φ(x,y) that mediates interactions
2. Defect → field coupling (defects create wells/peaks)
3. Field → defect motion (F = -∇φ)
4. Local energy recycling (annihilation → field → creation)

The goal: Turn particle model into field + defect coupled system
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
import json


@dataclass
class Defect:
    """A topological defect coupled to the medium field."""
    position: np.ndarray
    charge: int                    # +1 or -1 (chirality)
    velocity: np.ndarray = None
    energy: float = 1.0
    core_radius: float = 1.5       # Radius of influence on field
    lifetime: int = 0
    id: int = 0
    
    def __post_init__(self):
        if self.velocity is None:
            self.velocity = np.zeros(2)
        self.position = np.array(self.position, dtype=float)
        self.velocity = np.array(self.velocity, dtype=float)


@dataclass
class FieldParams:
    """Parameters for the coupled field-defect system."""
    # Field dynamics
    field_diffusion: float = 0.2       # How fast field spreads
    field_decay: float = 0.005         # Global dissipation (radiation)
    field_cap: float = 5.0             # Maximum local field value
    
    # Defect → Field coupling
    defect_field_strength: float = 0.5  # How strongly defects affect field
    defect_well_radius: float = 3.0     # Radius of defect's field influence
    
    # Field → Defect coupling  
    field_force_strength: float = 0.8   # How strongly field gradient moves defects
    direct_force_strength: float = 0.3  # Remaining direct pairwise force (reduced)
    
    # Defect dynamics
    damping: float = 0.15
    max_speed: float = 2.0
    
    # Creation/Annihilation
    creation_threshold: float = 1.5     # Field value needed for creation
    creation_rate: float = 0.003
    creation_cost: float = 0.8          # Energy consumed from field
    annihilation_radius: float = 1.5
    annihilation_injection: float = 1.0  # Energy returned to field (recycling!)
    
    # Boundaries
    boundary: str = "periodic"


class CoupledFieldSystem:
    """
    A field-defect coupled system where:
    - Defects create potential wells/peaks in φ(x,y)
    - Defects move according to F = -∇φ
    - Energy circulates through the field
    """
    
    def __init__(self, size: Tuple[int, int], params: FieldParams = None):
        self.size = size
        self.params = params or FieldParams()
        self.defects: List[Defect] = []
        self.time = 0
        self.next_id = 0
        
        # THE FIELD: φ(x,y) - continuous medium state
        # Positive field attracts positive defects (or repels negative)
        self.field = np.zeros(size, dtype=float)
        
        # Secondary fields for visualization/analysis
        self.energy_field = np.zeros(size, dtype=float)  # Available energy for creation
        
        # Precompute gradient kernels (Sobel-like for smooth gradients)
        self._setup_gradient_kernels()
        
        # Metrics
        self.metrics = {
            'defect_count': [],
            'positive_count': [],
            'negative_count': [],
            'field_energy': [],
            'field_max': [],
            'field_min': [],
            'creations': [],
            'annihilations': [],
            'mean_speed': [],
        }
        
        self.events = []
    
    def _setup_gradient_kernels(self):
        """Setup kernels for computing field gradients."""
        # Simple central difference
        self.dx_kernel = np.array([[-1, 0, 1]]) / 2.0
        self.dy_kernel = np.array([[-1], [0], [1]]) / 2.0
    
    def compute_field_gradient(self, position: np.ndarray) -> np.ndarray:
        """Compute ∇φ at a position using interpolation."""
        x, y = position
        xi, yi = int(x) % self.size[0], int(y) % self.size[1]
        
        # Central differences with periodic boundaries
        dx = (self.field[(xi+1) % self.size[0], yi] - 
              self.field[(xi-1) % self.size[0], yi]) / 2.0
        dy = (self.field[xi, (yi+1) % self.size[1]] - 
              self.field[xi, (yi-1) % self.size[1]]) / 2.0
        
        return np.array([dx, dy])
    
    # =========================================================================
    # DEFECT → FIELD COUPLING
    # =========================================================================
    
    def update_field_from_defects(self):
        """
        Defects create potential wells/peaks in the field.
        
        Positive defects (+1) create positive wells (attract other +, repel -)
        Negative defects (-1) create negative wells (attract other -, repel +)
        
        This is the "defect → field" direction of coupling.
        """
        # Start with current field
        defect_contribution = np.zeros_like(self.field)
        
        for defect in self.defects:
            x, y = defect.position
            xi, yi = int(x), int(y)
            r = int(self.params.defect_well_radius) + 1
            
            # Create a well/peak centered on defect
            for i in range(xi - r, xi + r + 1):
                for j in range(yi - r, yi + r + 1):
                    ii = i % self.size[0]
                    jj = j % self.size[1]
                    
                    dist = np.sqrt((i - x)**2 + (j - y)**2)
                    if dist < self.params.defect_well_radius:
                        # Gaussian-like well: strongest at center
                        strength = np.exp(-dist**2 / (2 * defect.core_radius**2))
                        defect_contribution[ii, jj] += (
                            defect.charge * self.params.defect_field_strength * strength
                        )
        
        # Blend defect contribution with existing field (not replace)
        self.field = 0.7 * self.field + 0.3 * defect_contribution
    
    # =========================================================================
    # FIELD → DEFECT COUPLING
    # =========================================================================
    
    def compute_forces(self) -> List[np.ndarray]:
        """
        Compute forces on defects from:
        1. Field gradient: F_field = -q * ∇φ (charge determines attraction/repulsion)
        2. Direct pairwise (reduced): F_direct = k * q1 * q2 / r²
        
        This is the "field → defect" direction of coupling.
        """
        forces = [np.zeros(2) for _ in self.defects]
        p = self.params
        
        for i, defect in enumerate(self.defects):
            # 1. FIELD-MEDIATED FORCE (primary)
            grad = self.compute_field_gradient(defect.position)
            # Positive defect attracted to positive field regions (down gradient)
            # F = -q * ∇φ means +defect moves toward +field
            field_force = -defect.charge * p.field_force_strength * grad
            forces[i] += field_force
            
            # 2. DIRECT PAIRWISE FORCE (secondary, reduced)
            for j, other in enumerate(self.defects):
                if i >= j:
                    continue
                
                delta = self._periodic_delta(defect.position, other.position)
                dist = np.linalg.norm(delta)
                
                if dist < 0.5:
                    continue
                
                # Coulomb-like: same sign repel, opposite attract
                force_mag = (p.direct_force_strength * 
                            defect.charge * other.charge / dist**2)
                force_dir = delta / dist
                
                forces[i] -= force_mag * force_dir
                forces[j] += force_mag * force_dir
        
        return forces
    
    def _periodic_delta(self, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
        """Displacement with periodic boundaries."""
        delta = p2 - p1
        for dim in [0, 1]:
            if abs(delta[dim]) > self.size[dim] / 2:
                delta[dim] -= np.sign(delta[dim]) * self.size[dim]
        return delta
    
    # =========================================================================
    # FIELD EVOLUTION (Wave-like + Diffusion)
    # =========================================================================
    
    def evolve_field(self, dt: float):
        """
        Evolve the field with:
        1. Diffusion (spreads gradients)
        2. Decay (global dissipation)
        3. Cap (prevents runaway)
        """
        p = self.params
        
        # Laplacian for diffusion
        laplacian = (
            np.roll(self.field, 1, axis=0) + np.roll(self.field, -1, axis=0) +
            np.roll(self.field, 1, axis=1) + np.roll(self.field, -1, axis=1) - 
            4 * self.field
        )
        
        # Diffusion + decay
        self.field += p.field_diffusion * laplacian * dt
        self.field *= (1 - p.field_decay * dt)
        
        # Cap values
        np.clip(self.field, -p.field_cap, p.field_cap, out=self.field)
        
        # Energy field also diffuses and decays
        laplacian_e = (
            np.roll(self.energy_field, 1, axis=0) + np.roll(self.energy_field, -1, axis=0) +
            np.roll(self.energy_field, 1, axis=1) + np.roll(self.energy_field, -1, axis=1) - 
            4 * self.energy_field
        )
        self.energy_field += p.field_diffusion * laplacian_e * dt
        self.energy_field *= (1 - p.field_decay * dt)
        np.clip(self.energy_field, 0, p.field_cap, out=self.energy_field)
    
    # =========================================================================
    # CREATION / ANNIHILATION WITH ENERGY RECYCLING
    # =========================================================================
    
    def attempt_creation(self) -> int:
        """
        Create defect pairs where energy field is high enough.
        
        ENERGY RECYCLING: Consumes from energy_field, not created from nothing.
        """
        p = self.params
        created = 0
        n_samples = max(1, int(self.size[0] * self.size[1] * p.creation_rate))
        
        for _ in range(n_samples):
            pos = np.array([
                np.random.uniform(0, self.size[0]),
                np.random.uniform(0, self.size[1])
            ])
            xi, yi = int(pos[0]) % self.size[0], int(pos[1]) % self.size[1]
            
            local_energy = self.energy_field[xi, yi]
            
            if local_energy > p.creation_threshold:
                # Consume energy
                self.energy_field[xi, yi] -= p.creation_cost
                
                # Create pair
                angle = np.random.uniform(0, 2*np.pi)
                sep = 2.0
                offset = sep * np.array([np.cos(angle), np.sin(angle)])
                
                v_mag = 0.3
                v1 = v_mag * np.array([np.cos(angle), np.sin(angle)])
                
                self.add_defect(pos + offset/2, charge=+1, velocity=v1)
                self.add_defect(pos - offset/2, charge=-1, velocity=-v1)
                
                created += 1
                self.events.append({'type': 'creation', 'time': self.time, 'pos': pos.tolist()})
        
        return created
    
    def check_annihilation(self) -> int:
        """
        Annihilate opposite-charge pairs that get too close.
        
        ENERGY RECYCLING: Returns energy to energy_field for future creation.
        """
        p = self.params
        annihilated = 0
        to_remove = set()
        
        for i, d1 in enumerate(self.defects):
            if i in to_remove:
                continue
            for j, d2 in enumerate(self.defects):
                if j <= i or j in to_remove:
                    continue
                if d1.charge * d2.charge >= 0:  # Same sign don't annihilate
                    continue
                
                delta = self._periodic_delta(d1.position, d2.position)
                dist = np.linalg.norm(delta)
                
                if dist < p.annihilation_radius:
                    to_remove.add(i)
                    to_remove.add(j)
                    
                    # ENERGY RECYCLING: Inject energy back into field
                    midpoint = d1.position + delta / 2
                    self._inject_energy(midpoint, p.annihilation_injection)
                    
                    annihilated += 1
                    self.events.append({
                        'type': 'annihilation', 
                        'time': self.time, 
                        'pos': midpoint.tolist()
                    })
        
        self.defects = [d for i, d in enumerate(self.defects) if i not in to_remove]
        return annihilated
    
    def _inject_energy(self, position: np.ndarray, amount: float, radius: float = 3.0):
        """Inject energy into the energy field (for creation recycling)."""
        x, y = int(position[0]), int(position[1])
        r = int(radius)
        
        total_weight = 0
        cells = []
        for i in range(x - r, x + r + 1):
            for j in range(y - r, y + r + 1):
                ii = i % self.size[0]
                jj = j % self.size[1]
                dist = np.sqrt((i - x)**2 + (j - y)**2)
                if dist < radius:
                    weight = 1 - dist / radius
                    cells.append((ii, jj, weight))
                    total_weight += weight
        
        if total_weight > 0:
            for ii, jj, w in cells:
                self.energy_field[ii, jj] += amount * w / total_weight
    
    # =========================================================================
    # DEFECT MOTION
    # =========================================================================
    
    def update_defects(self, dt: float):
        """Update defect velocities and positions."""
        forces = self.compute_forces()
        p = self.params
        
        for defect, force in zip(self.defects, forces):
            # Update velocity
            defect.velocity += force * dt
            defect.velocity *= (1 - p.damping)
            
            # Speed limit
            speed = np.linalg.norm(defect.velocity)
            if speed > p.max_speed:
                defect.velocity *= p.max_speed / speed
            
            # Update position
            defect.position += defect.velocity * dt
            
            # Periodic boundaries
            defect.position[0] %= self.size[0]
            defect.position[1] %= self.size[1]
            
            defect.lifetime += 1
    
    # =========================================================================
    # MAIN STEP
    # =========================================================================
    
    def step(self, dt: float = 0.1) -> dict:
        """Execute one simulation step."""
        # 1. Update field from current defect positions
        self.update_field_from_defects()
        
        # 2. Attempt creation (uses energy field)
        created = self.attempt_creation()
        
        # 3. Compute forces and move defects
        self.update_defects(dt)
        
        # 4. Check annihilation (recycles to energy field)
        annihilated = self.check_annihilation()
        
        # 5. Evolve field (diffusion + decay)
        self.evolve_field(dt)
        
        # 6. Record metrics
        self._record_metrics(created, annihilated)
        
        self.time += 1
        
        return {
            'time': self.time,
            'n_defects': len(self.defects),
            'created': created,
            'annihilated': annihilated,
            'field_energy': np.sum(np.abs(self.field))
        }
    
    def _record_metrics(self, created: int, annihilated: int):
        """Record metrics for analysis."""
        self.metrics['defect_count'].append(len(self.defects))
        self.metrics['positive_count'].append(sum(1 for d in self.defects if d.charge > 0))
        self.metrics['negative_count'].append(sum(1 for d in self.defects if d.charge < 0))
        self.metrics['field_energy'].append(float(np.sum(np.abs(self.field))))
        self.metrics['field_max'].append(float(np.max(self.field)))
        self.metrics['field_min'].append(float(np.min(self.field)))
        self.metrics['creations'].append(created)
        self.metrics['annihilations'].append(annihilated)
        
        if self.defects:
            speeds = [np.linalg.norm(d.velocity) for d in self.defects]
            self.metrics['mean_speed'].append(float(np.mean(speeds)))
        else:
            self.metrics['mean_speed'].append(0)
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def add_defect(self, position: np.ndarray, charge: int, 
                   velocity: np.ndarray = None) -> Defect:
        """Add a defect."""
        defect = Defect(
            position=np.array(position, dtype=float),
            charge=charge,
            velocity=velocity if velocity is not None else np.zeros(2),
            id=self.next_id
        )
        self.next_id += 1
        self.defects.append(defect)
        return defect
    
    def create_random_pairs(self, n_pairs: int):
        """Initialize with random defect pairs."""
        for _ in range(n_pairs):
            center = np.array([
                np.random.uniform(0, self.size[0]),
                np.random.uniform(0, self.size[1])
            ])
            angle = np.random.uniform(0, 2*np.pi)
            sep = 2.0
            offset = sep * np.array([np.cos(angle), np.sin(angle)])
            
            self.add_defect(center + offset/2, charge=+1)
            self.add_defect(center - offset/2, charge=-1)
    
    def inject_energy_pulse(self, position: np.ndarray, amount: float, radius: float = 5.0):
        """Inject an energy pulse for testing propagation."""
        self._inject_energy(position, amount, radius)
    
    def get_summary(self) -> dict:
        """Get simulation summary."""
        return {
            'time': self.time,
            'n_defects': len(self.defects),
            'charge_balance': sum(d.charge for d in self.defects),
            'total_creations': sum(self.metrics['creations']),
            'total_annihilations': sum(self.metrics['annihilations']),
            'metrics': self.metrics
        }


# =============================================================================
# EXPERIMENT: Test field-mediated dynamics
# =============================================================================

def run_field_coupling_test():
    """Test the coupled field-defect system."""
    np.random.seed(42)
    
    params = FieldParams(
        field_diffusion=0.15,
        field_decay=0.003,
        field_cap=4.0,
        defect_field_strength=0.6,
        defect_well_radius=3.0,
        field_force_strength=1.0,
        direct_force_strength=0.2,  # Reduced direct interaction
        damping=0.15,
        max_speed=1.5,
        creation_threshold=2.0,
        creation_rate=0.002,
        creation_cost=1.0,
        annihilation_radius=1.5,
        annihilation_injection=1.2,  # Slightly more than cost for sustained activity
    )
    
    system = CoupledFieldSystem(size=(30, 30), params=params)
    
    # Initialize with some defects
    system.create_random_pairs(10)
    
    # Initialize energy field with some energy
    system.energy_field = np.random.uniform(0.5, 2.0, system.size)
    
    print("=" * 60)
    print("FIELD-COUPLED DEFECT DYNAMICS TEST")
    print("=" * 60)
    print(f"Grid: {system.size}")
    print(f"Initial defects: {len(system.defects)}")
    print(f"Initial energy: {np.sum(system.energy_field):.0f}")
    print("=" * 60)
    
    # Run simulation
    for i in range(500):
        result = system.step(dt=0.1)
        if i % 100 == 0:
            field_e = np.sum(np.abs(system.field))
            energy_e = np.sum(system.energy_field)
            print(f"t={i}: n={result['n_defects']}, "
                  f"field={field_e:.1f}, energy={energy_e:.1f}, "
                  f"+{result['created']}/-{result['annihilated']}")
    
    summary = system.get_summary()
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Final defects: {summary['n_defects']}")
    print(f"Charge balance: {summary['charge_balance']}")
    print(f"Total creations: {summary['total_creations']}")
    print(f"Total annihilations: {summary['total_annihilations']}")
    
    return system, summary


if __name__ == "__main__":
    system, summary = run_field_coupling_test()
    
    # Save results
    with open('/app/backend/qmrt_topology/field_coupled_results.json', 'w') as f:
        json.dump({
            'final_defects': summary['n_defects'],
            'total_creations': summary['total_creations'],
            'total_annihilations': summary['total_annihilations'],
        }, f, indent=2)
    
    print("\nResults saved.")
