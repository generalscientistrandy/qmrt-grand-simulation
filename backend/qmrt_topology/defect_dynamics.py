#!/usr/bin/env python3
"""
QMRT Defect Dynamics Engine
===========================
A proto-physics engine for time-evolving topological defects.

This implements:
1. Defect creation (pair nucleation from local strain)
2. Mobility (force-law driven movement)
3. Annihilation (with energy redistribution)
4. Clustering (stability tracking)
5. Chirality interactions (configurable potentials)

Key principle: Dynamics → Structure → Emergent Laws
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import json
from datetime import datetime

# =============================================================================
# DEFECT REPRESENTATION
# =============================================================================

@dataclass
class Defect:
    """A topological defect in the medium."""
    position: np.ndarray          # [x, y] coordinates
    charge: int                   # +1 or -1 (chirality τ)
    energy: float = 1.0           # Internal energy
    velocity: np.ndarray = None   # [vx, vy] 
    core_size: float = 0.5        # Interaction radius
    phase_angle: float = 0.0      # Optional: phase information
    lifetime: int = 0             # Timesteps survived
    id: int = 0                   # Unique identifier
    
    def __post_init__(self):
        if self.velocity is None:
            self.velocity = np.zeros(2)
        self.position = np.array(self.position, dtype=float)
        self.velocity = np.array(self.velocity, dtype=float)


@dataclass
class Cluster:
    """A stable grouping of defects."""
    defect_ids: List[int]
    center: np.ndarray
    net_charge: int
    formation_time: int
    lifetime: int = 0
    stable: bool = False


# =============================================================================
# MEDIUM STATE
# =============================================================================

@dataclass
class MediumState:
    """The state of the medium at a given time."""
    energy_field: np.ndarray      # Local energy density
    strain_field: np.ndarray      # Local strain (drives creation)
    size: Tuple[int, int]         # Grid dimensions
    
    # Energy budget tracking
    total_injected: float = 0.0   # Total energy injected
    total_dissipated: float = 0.0 # Total energy lost to dissipation
    total_consumed: float = 0.0   # Total energy consumed (creation)
    
    @classmethod
    def create(cls, size: Tuple[int, int], noise_level: float = 0.1):
        """Create medium with random noise."""
        energy = np.random.uniform(0, noise_level, size)
        strain = np.random.uniform(-noise_level, noise_level, size)
        return cls(energy_field=energy, strain_field=strain, size=size)
    
    def inject_energy(self, position: np.ndarray, amount: float, radius: float = 2.0):
        """Inject energy at a position (redistributes, doesn't create from nothing)."""
        x, y = int(position[0]), int(position[1])
        r = int(radius)
        injected = 0.0
        # Count cells in radius for even distribution
        cells = []
        for i in range(max(0, x-r), min(self.size[0], x+r+1)):
            for j in range(max(0, y-r), min(self.size[1], y+r+1)):
                dist = np.sqrt((i-x)**2 + (j-y)**2)
                if dist < radius:
                    cells.append((i, j, 1 - dist/radius))
        
        if cells:
            total_weight = sum(w for _, _, w in cells)
            for i, j, w in cells:
                delta = amount * w / total_weight
                self.energy_field[i, j] += delta
                injected += delta
        
        self.total_injected += injected
        return injected
    
    def consume_energy(self, position: np.ndarray, amount: float, radius: float = 2.0) -> float:
        """Consume energy from a position (for pair creation). Returns actual consumed."""
        x, y = int(position[0]), int(position[1])
        r = int(radius)
        
        # First pass: calculate total available energy
        available_total = 0.0
        cells = []
        for i in range(max(0, x-r), min(self.size[0], x+r+1)):
            for j in range(max(0, y-r), min(self.size[1], y+r+1)):
                dist = np.sqrt((i-x)**2 + (j-y)**2)
                if dist < radius:
                    weight = 1 - dist/radius
                    available_total += self.energy_field[i, j] * weight
                    cells.append((i, j, weight))
        
        # Calculate how much we can actually take
        actual_amount = min(amount, available_total)
        
        if actual_amount > 0 and cells:
            # Second pass: take proportionally from each cell
            total_weight = sum(w for _, _, w in cells)
            consumed = 0.0
            for i, j, w in cells:
                take = actual_amount * w / total_weight
                take = min(take, self.energy_field[i, j])
                self.energy_field[i, j] -= take
                consumed += take
            self.total_consumed += consumed
            return consumed
        return 0.0
    
    def get_local_strain(self, position: np.ndarray) -> float:
        """Get strain at a position (with interpolation)."""
        x, y = position
        xi, yi = int(x) % self.size[0], int(y) % self.size[1]
        return self.strain_field[xi, yi]
    
    def get_local_energy(self, position: np.ndarray) -> float:
        """Get energy at a position."""
        x, y = position
        xi, yi = int(x) % self.size[0], int(y) % self.size[1]
        return self.energy_field[xi, yi]
    
    def get_total_energy(self) -> float:
        """Get total energy in the field."""
        return float(np.sum(self.energy_field))


# =============================================================================
# PHYSICS PARAMETERS
# =============================================================================

@dataclass
class PhysicsParams:
    """Configurable physics parameters."""
    # Creation
    creation_threshold: float = 0.8      # Energy threshold for pair creation
    pair_separation: float = 2.0         # Initial separation of created pairs
    creation_rate: float = 0.01          # Probability multiplier
    creation_energy_cost: float = 1.0    # Energy consumed per pair creation
    
    # Mobility
    interaction_strength: float = 1.0    # k in F = k * q_i * q_j / r^n
    force_exponent: float = 2.0          # n in 1/r^n (2 = inverse square)
    damping: float = 0.1                 # Velocity damping
    max_speed: float = 2.0               # Speed limit
    
    # Annihilation
    annihilation_radius: float = 1.0     # Distance for annihilation
    annihilation_energy: float = 2.0     # Energy released (redistributed, not created)
    
    # Clustering
    cluster_radius: float = 5.0          # Radius to consider for clustering
    stability_threshold: float = 0.1     # Force threshold for stability
    
    # Medium - ENERGY CONSERVATION
    energy_decay: float = 0.01           # Global dissipation rate (radiation loss)
    energy_diffusion: float = 0.1        # Energy spreads locally
    strain_diffusion: float = 0.05       # Strain spreading rate
    energy_cap: float = 5.0              # Maximum local energy (prevents runaway)
    
    # Energy budget tracking
    track_energy_budget: bool = True     # Track total system energy
    
    # Boundaries
    boundary_mode: str = "periodic"      # "periodic" or "reflective"


# =============================================================================
# DEFECT DYNAMICS ENGINE
# =============================================================================

class DefectDynamicsEngine:
    """
    The core physics engine for defect evolution.
    
    Implements: creation, mobility, annihilation, clustering, chirality interactions
    """
    
    def __init__(self, size: Tuple[int, int], params: PhysicsParams = None):
        self.size = size
        self.params = params or PhysicsParams()
        self.medium = MediumState.create(size)
        self.defects: List[Defect] = []
        self.clusters: List[Cluster] = []
        self.time = 0
        self.next_id = 0
        
        # Metrics tracking - including energy budget
        self.metrics = {
            'defect_count': [],
            'positive_count': [],
            'negative_count': [],
            'total_energy': [],
            'kinetic_energy': [],           # Defect motion energy
            'energy_injected': [],          # Cumulative injected
            'energy_dissipated': [],        # Cumulative dissipated
            'annihilation_events': [],
            'creation_events': [],
            'cluster_count': [],
            'mean_cluster_size': [],
            'spatial_correlation': [],
        }
        
        # Event log
        self.events = []
    
    def add_defect(self, position: np.ndarray, charge: int, 
                   velocity: np.ndarray = None, energy: float = 1.0) -> Defect:
        """Add a defect to the system."""
        defect = Defect(
            position=position,
            charge=charge,
            energy=energy,
            velocity=velocity if velocity is not None else np.zeros(2),
            id=self.next_id
        )
        self.next_id += 1
        self.defects.append(defect)
        return defect
    
    def create_random_pairs(self, n_pairs: int):
        """Initialize with random defect pairs (preserves neutrality)."""
        for _ in range(n_pairs):
            # Random position for the pair center
            center = np.array([
                np.random.uniform(0, self.size[0]),
                np.random.uniform(0, self.size[1])
            ])
            # Random direction for separation
            angle = np.random.uniform(0, 2*np.pi)
            offset = self.params.pair_separation * np.array([np.cos(angle), np.sin(angle)])
            
            # Create +/- pair
            self.add_defect(center + offset/2, charge=+1)
            self.add_defect(center - offset/2, charge=-1)
    
    # -------------------------------------------------------------------------
    # CREATION: Pair nucleation from local strain - ENERGY CONSERVING
    # -------------------------------------------------------------------------
    
    def _attempt_creation(self):
        """Attempt to create defect pairs based on local energy/strain.
        
        ENERGY CONSERVATION: Pairs are only created if there's enough
        local energy to pay for them. Energy is consumed, not created.
        """
        creation_events = 0
        
        # Sample random positions for potential creation
        n_samples = max(1, int(self.size[0] * self.size[1] * self.params.creation_rate))
        
        for _ in range(n_samples):
            pos = np.array([
                np.random.uniform(0, self.size[0]),
                np.random.uniform(0, self.size[1])
            ])
            
            local_energy = self.medium.get_local_energy(pos)
            local_strain = abs(self.medium.get_local_strain(pos))
            
            # Must have enough energy to create a pair
            energy_required = self.params.creation_energy_cost
            
            # Creation probability based on excess energy + strain
            if local_energy < energy_required:
                continue
                
            excess_energy = local_energy - energy_required * 0.5
            creation_prob = (excess_energy + local_strain) / self.params.creation_threshold
            
            if np.random.random() < creation_prob:
                # CONSUME energy to create the pair (energy conservation)
                consumed = self.medium.consume_energy(pos, energy_required, radius=3.0)
                
                if consumed < energy_required * 0.5:
                    # Not enough energy available - abort creation
                    # Return the consumed energy
                    self.medium.inject_energy(pos, consumed, radius=2.0)
                    continue
                
                # Create pair with small separation
                angle = np.random.uniform(0, 2*np.pi)
                offset = self.params.pair_separation * np.array([np.cos(angle), np.sin(angle)])
                
                # Initial velocities: moving apart (kinetic energy from consumed energy)
                v_mag = np.sqrt(consumed * 0.3)  # Some energy goes to motion
                v1 = v_mag * np.array([np.cos(angle), np.sin(angle)])
                v2 = -v1
                
                self.add_defect(pos + offset/2, charge=+1, velocity=v1)
                self.add_defect(pos - offset/2, charge=-1, velocity=v2)
                
                creation_events += 1
                self.events.append({
                    'type': 'creation',
                    'time': self.time,
                    'position': pos.tolist(),
                    'energy_consumed': consumed
                })
        
        return creation_events
    
    # -------------------------------------------------------------------------
    # MOBILITY: Force-law driven movement
    # -------------------------------------------------------------------------
    
    def _compute_forces(self) -> List[np.ndarray]:
        """Compute forces on all defects."""
        forces = [np.zeros(2) for _ in self.defects]
        
        for i, d1 in enumerate(self.defects):
            for j, d2 in enumerate(self.defects):
                if i >= j:
                    continue
                
                # Vector from d1 to d2
                delta = self._periodic_delta(d1.position, d2.position)
                dist = np.linalg.norm(delta)
                
                if dist < 0.1:  # Avoid singularity
                    continue
                
                # Force magnitude: F = k * q1 * q2 / r^n
                # Same sign → repel (positive force outward)
                # Opposite sign → attract (negative force, toward each other)
                force_mag = (self.params.interaction_strength * 
                            d1.charge * d2.charge / 
                            (dist ** self.params.force_exponent))
                
                # Force direction (normalized delta)
                force_dir = delta / dist
                
                # Apply forces (Newton's third law)
                forces[i] -= force_mag * force_dir  # Force on d1
                forces[j] += force_mag * force_dir  # Force on d2
        
        return forces
    
    def _update_velocities(self, forces: List[np.ndarray], dt: float):
        """Update defect velocities based on forces."""
        for defect, force in zip(self.defects, forces):
            # F = ma, assume m = 1
            defect.velocity += force * dt
            
            # Apply damping
            defect.velocity *= (1 - self.params.damping)
            
            # Speed limit
            speed = np.linalg.norm(defect.velocity)
            if speed > self.params.max_speed:
                defect.velocity *= self.params.max_speed / speed
    
    def _update_positions(self, dt: float):
        """Update defect positions based on velocities."""
        for defect in self.defects:
            defect.position += defect.velocity * dt
            
            # Apply boundary conditions
            if self.params.boundary_mode == "periodic":
                defect.position[0] %= self.size[0]
                defect.position[1] %= self.size[1]
            elif self.params.boundary_mode == "reflective":
                for dim in [0, 1]:
                    if defect.position[dim] < 0:
                        defect.position[dim] = -defect.position[dim]
                        defect.velocity[dim] = -defect.velocity[dim]
                    elif defect.position[dim] >= self.size[dim]:
                        defect.position[dim] = 2*self.size[dim] - defect.position[dim]
                        defect.velocity[dim] = -defect.velocity[dim]
    
    def _periodic_delta(self, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
        """Compute displacement vector with periodic boundaries."""
        delta = p2 - p1
        for dim in [0, 1]:
            if abs(delta[dim]) > self.size[dim] / 2:
                delta[dim] -= np.sign(delta[dim]) * self.size[dim]
        return delta
    
    # -------------------------------------------------------------------------
    # ANNIHILATION: With energy redistribution
    # -------------------------------------------------------------------------
    
    def _check_annihilation(self) -> int:
        """Check for and process annihilation events."""
        annihilation_events = 0
        to_remove = set()
        
        for i, d1 in enumerate(self.defects):
            if i in to_remove:
                continue
            for j, d2 in enumerate(self.defects):
                if j <= i or j in to_remove:
                    continue
                
                # Only opposite charges can annihilate
                if d1.charge * d2.charge >= 0:
                    continue
                
                delta = self._periodic_delta(d1.position, d2.position)
                dist = np.linalg.norm(delta)
                
                if dist < self.params.annihilation_radius:
                    to_remove.add(i)
                    to_remove.add(j)
                    
                    # Inject energy at annihilation site
                    midpoint = d1.position + delta / 2
                    self.medium.inject_energy(
                        midpoint, 
                        self.params.annihilation_energy,
                        radius=3.0
                    )
                    
                    annihilation_events += 1
                    self.events.append({
                        'type': 'annihilation',
                        'time': self.time,
                        'position': midpoint.tolist(),
                        'charges': [d1.charge, d2.charge]
                    })
        
        # Remove annihilated defects
        self.defects = [d for i, d in enumerate(self.defects) if i not in to_remove]
        
        return annihilation_events
    
    # -------------------------------------------------------------------------
    # CLUSTERING: Stability tracking
    # -------------------------------------------------------------------------
    
    def _identify_clusters(self) -> List[Cluster]:
        """Identify defect clusters."""
        clusters = []
        used = set()
        
        for i, d1 in enumerate(self.defects):
            if i in used:
                continue
            
            # Find all defects within cluster radius
            cluster_members = [i]
            for j, d2 in enumerate(self.defects):
                if j == i or j in used:
                    continue
                delta = self._periodic_delta(d1.position, d2.position)
                if np.linalg.norm(delta) < self.params.cluster_radius:
                    cluster_members.append(j)
            
            if len(cluster_members) > 1:
                used.update(cluster_members)
                
                # Compute cluster properties
                positions = np.array([self.defects[k].position for k in cluster_members])
                charges = [self.defects[k].charge for k in cluster_members]
                
                cluster = Cluster(
                    defect_ids=[self.defects[k].id for k in cluster_members],
                    center=positions.mean(axis=0),
                    net_charge=sum(charges),
                    formation_time=self.time
                )
                
                # Check stability: net force on cluster ≈ 0
                cluster_forces = [np.zeros(2) for _ in cluster_members]
                for ii, ki in enumerate(cluster_members):
                    for jj, kj in enumerate(cluster_members):
                        if ii >= jj:
                            continue
                        d1, d2 = self.defects[ki], self.defects[kj]
                        delta = self._periodic_delta(d1.position, d2.position)
                        dist = np.linalg.norm(delta)
                        if dist > 0.1:
                            force_mag = (self.params.interaction_strength * 
                                        d1.charge * d2.charge / 
                                        (dist ** self.params.force_exponent))
                            force_dir = delta / dist
                            cluster_forces[ii] -= force_mag * force_dir
                            cluster_forces[jj] += force_mag * force_dir
                
                total_force = sum(np.linalg.norm(f) for f in cluster_forces)
                cluster.stable = total_force < self.params.stability_threshold * len(cluster_members)
                
                clusters.append(cluster)
        
        return clusters
    
    # -------------------------------------------------------------------------
    # MEDIUM EVOLUTION - WITH ENERGY CONSERVATION
    # -------------------------------------------------------------------------
    
    def _evolve_medium(self, dt: float):
        """Evolve the medium state with proper energy conservation."""
        # 1. Global dissipation (energy radiates away)
        #    This is the key fix - represents energy leaving the system
        energy_before = np.sum(self.medium.energy_field)
        dissipation_factor = (1 - self.params.energy_decay * dt)
        self.medium.energy_field *= dissipation_factor
        energy_after = np.sum(self.medium.energy_field)
        self.medium.total_dissipated += (energy_before - energy_after)
        
        # 2. Energy diffusion (spreads locally, conserves total)
        energy = self.medium.energy_field
        laplacian_e = (
            np.roll(energy, 1, axis=0) + np.roll(energy, -1, axis=0) +
            np.roll(energy, 1, axis=1) + np.roll(energy, -1, axis=1) - 4 * energy
        )
        self.medium.energy_field += self.params.energy_diffusion * laplacian_e * dt
        
        # 3. Cap local energy (prevents runaway hotspots)
        np.clip(self.medium.energy_field, 0, self.params.energy_cap, out=self.medium.energy_field)
        
        # 4. Strain diffusion (simple Laplacian)
        strain = self.medium.strain_field
        laplacian_s = (
            np.roll(strain, 1, axis=0) + np.roll(strain, -1, axis=0) +
            np.roll(strain, 1, axis=1) + np.roll(strain, -1, axis=1) - 4 * strain
        )
        self.medium.strain_field += self.params.strain_diffusion * laplacian_s * dt
        
        # 5. Defects influence local strain (but not energy - that's from annihilation only)
        for defect in self.defects:
            x, y = int(defect.position[0]) % self.size[0], int(defect.position[1]) % self.size[1]
            self.medium.strain_field[x, y] += defect.charge * 0.01
    
    # -------------------------------------------------------------------------
    # MAIN SIMULATION STEP
    # -------------------------------------------------------------------------
    
    def step(self, dt: float = 0.1) -> dict:
        """Execute one simulation timestep."""
        # 1. Attempt creation
        creation_events = self._attempt_creation()
        
        # 2. Compute forces and update motion
        forces = self._compute_forces()
        self._update_velocities(forces, dt)
        self._update_positions(dt)
        
        # 3. Check annihilation
        annihilation_events = self._check_annihilation()
        
        # 4. Identify clusters
        self.clusters = self._identify_clusters()
        
        # 5. Evolve medium
        self._evolve_medium(dt)
        
        # 6. Update defect lifetimes
        for defect in self.defects:
            defect.lifetime += 1
        
        # 7. Record metrics
        self._record_metrics(creation_events, annihilation_events)
        
        self.time += 1
        
        return {
            'time': self.time,
            'n_defects': len(self.defects),
            'n_clusters': len(self.clusters),
            'creations': creation_events,
            'annihilations': annihilation_events
        }
    
    def _record_metrics(self, creations: int, annihilations: int):
        """Record metrics for analysis including energy budget."""
        self.metrics['defect_count'].append(len(self.defects))
        self.metrics['positive_count'].append(sum(1 for d in self.defects if d.charge > 0))
        self.metrics['negative_count'].append(sum(1 for d in self.defects if d.charge < 0))
        self.metrics['total_energy'].append(np.sum(self.medium.energy_field))
        
        # Kinetic energy of defects
        kinetic = sum(0.5 * np.dot(d.velocity, d.velocity) for d in self.defects)
        self.metrics['kinetic_energy'].append(kinetic)
        
        # Energy budget tracking
        self.metrics['energy_injected'].append(self.medium.total_injected)
        self.metrics['energy_dissipated'].append(self.medium.total_dissipated)
        
        self.metrics['annihilation_events'].append(annihilations)
        self.metrics['creation_events'].append(creations)
        self.metrics['cluster_count'].append(len(self.clusters))
        
        if self.clusters:
            self.metrics['mean_cluster_size'].append(
                np.mean([len(c.defect_ids) for c in self.clusters])
            )
        else:
            self.metrics['mean_cluster_size'].append(0)
        
        # Spatial correlation (simplified)
        if len(self.defects) > 1:
            positions = np.array([d.position for d in self.defects])
            center = positions.mean(axis=0)
            deviations = positions - center
            correlation = np.mean([np.dot(deviations[i], deviations[j]) 
                                   for i in range(len(deviations)) 
                                   for j in range(i+1, len(deviations))])
            self.metrics['spatial_correlation'].append(correlation)
            self.metrics['spatial_correlation'].append(correlation)
        else:
            self.metrics['spatial_correlation'].append(0)
    
    # -------------------------------------------------------------------------
    # RUN SIMULATION
    # -------------------------------------------------------------------------
    
    def run(self, n_steps: int, dt: float = 0.1, 
            progress_interval: int = 100) -> dict:
        """Run simulation for n_steps."""
        print(f"Starting simulation: {n_steps} steps, dt={dt}")
        print(f"Initial defects: {len(self.defects)}")
        
        for step in range(n_steps):
            result = self.step(dt)
            
            if (step + 1) % progress_interval == 0:
                print(f"  Step {step+1}/{n_steps}: "
                      f"defects={result['n_defects']}, "
                      f"clusters={result['n_clusters']}, "
                      f"created={result['creations']}, "
                      f"annihilated={result['annihilations']}")
        
        return self.get_summary()
    
    def get_summary(self) -> dict:
        """Get simulation summary."""
        return {
            'final_time': self.time,
            'final_defect_count': len(self.defects),
            'final_cluster_count': len(self.clusters),
            'stable_clusters': sum(1 for c in self.clusters if c.stable),
            'total_creations': sum(self.metrics['creation_events']),
            'total_annihilations': sum(self.metrics['annihilation_events']),
            'charge_balance': sum(d.charge for d in self.defects),
            'metrics': self.metrics
        }
    
    def get_state(self) -> dict:
        """Get current state for visualization."""
        return {
            'time': self.time,
            'defects': [
                {
                    'id': d.id,
                    'position': d.position.tolist(),
                    'charge': d.charge,
                    'velocity': d.velocity.tolist(),
                    'lifetime': d.lifetime
                }
                for d in self.defects
            ],
            'clusters': [
                {
                    'defect_ids': c.defect_ids,
                    'center': c.center.tolist(),
                    'net_charge': c.net_charge,
                    'stable': c.stable,
                    'lifetime': c.lifetime
                }
                for c in self.clusters
            ],
            'medium': {
                'energy': self.medium.energy_field.tolist(),
                'strain': self.medium.strain_field.tolist()
            }
        }


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

def run_chaos_to_order_experiment(
    grid_size: int = 50,
    n_initial_pairs: int = 50,
    n_steps: int = 5000,
    seed: int = 42
) -> dict:
    """
    The first critical experiment:
    Start with random/chaotic initial conditions.
    Observe whether stable structures emerge.
    """
    np.random.seed(seed)
    
    # Create engine with tuned parameters
    params = PhysicsParams(
        creation_threshold=1.0,
        pair_separation=2.0,
        creation_rate=0.005,
        interaction_strength=1.0,
        force_exponent=2.0,
        damping=0.15,
        max_speed=1.5,
        annihilation_radius=1.5,
        annihilation_energy=1.5,
        cluster_radius=6.0,
        stability_threshold=0.15,
        energy_decay=0.02,
        strain_diffusion=0.03,
        boundary_mode="periodic"
    )
    
    engine = DefectDynamicsEngine(size=(grid_size, grid_size), params=params)
    
    # Initialize with random pairs
    engine.create_random_pairs(n_initial_pairs)
    
    # Add initial noise to medium
    engine.medium.energy_field = np.random.uniform(0, 0.5, engine.size)
    engine.medium.strain_field = np.random.uniform(-0.3, 0.3, engine.size)
    
    print("=" * 60)
    print("CHAOS TO ORDER EXPERIMENT")
    print("=" * 60)
    print(f"Grid: {grid_size}x{grid_size}")
    print(f"Initial pairs: {n_initial_pairs}")
    print(f"Total steps: {n_steps}")
    print("=" * 60)
    
    # Run simulation
    summary = engine.run(n_steps, dt=0.1, progress_interval=500)
    
    # Analysis
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Final defect count: {summary['final_defect_count']}")
    print(f"Final cluster count: {summary['final_cluster_count']}")
    print(f"Stable clusters: {summary['stable_clusters']}")
    print(f"Charge balance: {summary['charge_balance']} (should be ~0)")
    print(f"Total creations: {summary['total_creations']}")
    print(f"Total annihilations: {summary['total_annihilations']}")
    
    # Check for emergence indicators
    metrics = summary['metrics']
    
    # Did defect count stabilize?
    if len(metrics['defect_count']) > 100:
        early = np.mean(metrics['defect_count'][:100])
        late = np.mean(metrics['defect_count'][-100:])
        variance_late = np.var(metrics['defect_count'][-100:])
        print(f"\nDefect count: early={early:.1f}, late={late:.1f}, late_var={variance_late:.2f}")
        
        if variance_late < early * 0.1:
            print("✓ System reached equilibrium (low variance)")
        else:
            print("✗ System still evolving (high variance)")
    
    # Did clusters form?
    if summary['final_cluster_count'] > 0:
        print(f"\n✓ Clusters formed: {summary['final_cluster_count']}")
        if summary['stable_clusters'] > 0:
            print(f"  ✓ Stable clusters: {summary['stable_clusters']}")
        else:
            print("  ✗ No stable clusters yet")
    else:
        print("\n✗ No clusters formed")
    
    # Spatial organization
    if len(metrics['spatial_correlation']) > 100:
        early_corr = np.mean(metrics['spatial_correlation'][:100])
        late_corr = np.mean(metrics['spatial_correlation'][-100:])
        print(f"\nSpatial correlation: early={early_corr:.2f}, late={late_corr:.2f}")
        if abs(late_corr) > abs(early_corr) * 1.5:
            print("✓ Spatial organization increased")
        else:
            print("~ Spatial organization similar")
    
    return {
        'engine': engine,
        'summary': summary,
        'params': params
    }


if __name__ == "__main__":
    result = run_chaos_to_order_experiment()
    
    # Save results
    summary = result['summary']
    summary_serializable = {
        k: v if not isinstance(v, np.ndarray) else v.tolist()
        for k, v in summary.items()
    }
    
    with open('/app/backend/qmrt_topology/defect_dynamics_results.json', 'w') as f:
        json.dump(summary_serializable, f, indent=2)
    
    print("\nResults saved to defect_dynamics_results.json")
