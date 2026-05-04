"""
Core Universe Evolution Engine
Manages simulation state, timesteps, snapshots, and timeline branching
"""
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
import json
import uuid
from enum import Enum


class SimulationPhase(Enum):
    """Evolution phases"""
    INITIALIZED = "initialized"
    PRIMORDIAL = "primordial"
    INFLATION = "inflation"
    RADIATION_ERA = "radiation_era"
    MATTER_ERA = "matter_era"
    STRUCTURE_FORMATION = "structure_formation"
    GALAXY_FORMATION = "galaxy_formation"
    STELLAR_ERA = "stellar_era"
    PLANETARY_ERA = "planetary_era"
    COMPLETE = "complete"


@dataclass
class SubstrateState:
    """Complete substrate field state at a timestep"""
    time: float
    scale_factor: float
    
    # Field arrays (stored as lists for JSON serialization)
    density: List[List[List[float]]]
    tension: List[List[List[float]]]
    torsion: List[List[List[List[float]]]]  # Vector field
    coherence: List[List[List[float]]]
    
    # Derived quantities
    mean_density: float
    density_variance: float
    mean_temperature: float
    
    def to_numpy(self) -> Dict[str, np.ndarray]:
        """Convert to numpy arrays for computation"""
        return {
            'density': np.array(self.density),
            'tension': np.array(self.tension),
            'torsion': np.array(self.torsion),
            'coherence': np.array(self.coherence)
        }
    
    @staticmethod
    def from_numpy(time: float, scale_factor: float, fields: Dict[str, np.ndarray], 
                   stats: Dict[str, float]) -> 'SubstrateState':
        """Create from numpy arrays"""
        return SubstrateState(
            time=time,
            scale_factor=scale_factor,
            density=fields['density'].tolist(),
            tension=fields['tension'].tolist(),
            torsion=fields['torsion'].tolist(),
            coherence=fields['coherence'].tolist(),
            mean_density=stats['mean_density'],
            density_variance=stats['density_variance'],
            mean_temperature=stats['mean_temperature']
        )


@dataclass
class HierarchicalObject:
    """Base class for hierarchical cosmic structures"""
    id: str
    object_type: str  # 'galaxy', 'stellar_system', 'planet'
    parent_id: Optional[str]
    position: Tuple[float, float, float]
    formation_time: float
    
    # Physical properties
    mass: float
    substrate_origin: Dict[str, float]
    
    # Hierarchy
    children: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return asdict(self)


@dataclass
class Galaxy(HierarchicalObject):
    """Galaxy structure"""
    num_stellar_systems: int = 0
    total_mass: float = 0.0
    
    def __init__(self, id: str, position: Tuple[float, float, float], 
                 formation_time: float, substrate_origin: Dict[str, float]):
        super().__init__(
            id=id,
            object_type='galaxy',
            parent_id=None,
            position=position,
            formation_time=formation_time,
            mass=0.0,
            substrate_origin=substrate_origin
        )
        self.num_stellar_systems = 0
        self.total_mass = 0.0


@dataclass
class StellarSystem(HierarchicalObject):
    """Stellar system with planets"""
    star_mass: float = 0.0
    star_type: str = ""
    num_planets: int = 0
    
    def __init__(self, id: str, parent_id: str, position: Tuple[float, float, float],
                 formation_time: float, substrate_origin: Dict[str, float],
                 star_mass: float, star_type: str):
        super().__init__(
            id=id,
            object_type='stellar_system',
            parent_id=parent_id,
            position=position,
            formation_time=formation_time,
            mass=star_mass,
            substrate_origin=substrate_origin
        )
        self.star_mass = star_mass
        self.star_type = star_type
        self.num_planets = 0


@dataclass
class Planet(HierarchicalObject):
    """Individual planet"""
    planet_type: str = "rocky"
    orbit_au: float = 0.0
    habitable: bool = False
    
    def __init__(self, id: str, parent_id: str, position: Tuple[float, float, float],
                 formation_time: float, substrate_origin: Dict[str, float],
                 mass: float, planet_type: str, orbit_au: float, habitable: bool):
        super().__init__(
            id=id,
            object_type='planet',
            parent_id=parent_id,
            position=position,
            formation_time=formation_time,
            mass=mass,
            substrate_origin=substrate_origin
        )
        self.planet_type = planet_type
        self.orbit_au = orbit_au
        self.habitable = habitable


@dataclass
class SimulationSnapshot:
    """Complete simulation state at a specific time"""
    snapshot_id: str
    timeline_id: str
    parent_snapshot_id: Optional[str]
    
    # Time metadata
    simulation_time: float
    real_timestamp: str
    phase: str
    
    # Substrate state
    substrate: SubstrateState
    
    # Hierarchical objects
    galaxies: List[Dict]
    stellar_systems: List[Dict]
    planets: List[Dict]
    
    # Evolution parameters
    hubble_parameter: float
    grid_size: int
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Serialize complete snapshot"""
        return {
            'snapshot_id': self.snapshot_id,
            'timeline_id': self.timeline_id,
            'parent_snapshot_id': self.parent_snapshot_id,
            'simulation_time': self.simulation_time,
            'real_timestamp': self.real_timestamp,
            'phase': self.phase,
            'substrate': asdict(self.substrate),
            'galaxies': self.galaxies,
            'stellar_systems': self.stellar_systems,
            'planets': self.planets,
            'hubble_parameter': self.hubble_parameter,
            'grid_size': self.grid_size,
            'metadata': self.metadata
        }


class TimelineManager:
    """Manages simulation timelines and branching"""
    
    def __init__(self):
        self.timelines: Dict[str, List[str]] = {}  # timeline_id -> [snapshot_ids]
        self.snapshots: Dict[str, SimulationSnapshot] = {}  # snapshot_id -> snapshot
        
    def create_timeline(self, name: str) -> str:
        """Create new timeline"""
        timeline_id = str(uuid.uuid4())
        self.timelines[timeline_id] = []
        return timeline_id
    
    def add_snapshot(self, snapshot: SimulationSnapshot):
        """Add snapshot to timeline"""
        self.snapshots[snapshot.snapshot_id] = snapshot
        if snapshot.timeline_id in self.timelines:
            self.timelines[snapshot.timeline_id].append(snapshot.snapshot_id)
        else:
            self.timelines[snapshot.timeline_id] = [snapshot.snapshot_id]
    
    def get_snapshot(self, snapshot_id: str) -> Optional[SimulationSnapshot]:
        """Retrieve specific snapshot"""
        return self.snapshots.get(snapshot_id)
    
    def get_timeline_snapshots(self, timeline_id: str) -> List[SimulationSnapshot]:
        """Get all snapshots in timeline chronologically"""
        snapshot_ids = self.timelines.get(timeline_id, [])
        snapshots = [self.snapshots[sid] for sid in snapshot_ids if sid in self.snapshots]
        return sorted(snapshots, key=lambda s: s.simulation_time)
    
    def branch_timeline(self, source_snapshot_id: str, new_name: str) -> str:
        """Create new timeline branching from a snapshot"""
        if source_snapshot_id not in self.snapshots:
            raise ValueError(f"Source snapshot {source_snapshot_id} not found")
        
        new_timeline_id = self.create_timeline(new_name)
        source_snapshot = self.snapshots[source_snapshot_id]
        
        # Create branch snapshot
        branch_snapshot = SimulationSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timeline_id=new_timeline_id,
            parent_snapshot_id=source_snapshot_id,
            simulation_time=source_snapshot.simulation_time,
            real_timestamp=datetime.now(timezone.utc).isoformat(),
            phase=source_snapshot.phase,
            substrate=source_snapshot.substrate,
            galaxies=source_snapshot.galaxies.copy(),
            stellar_systems=source_snapshot.stellar_systems.copy(),
            planets=source_snapshot.planets.copy(),
            hubble_parameter=source_snapshot.hubble_parameter,
            grid_size=source_snapshot.grid_size,
            metadata={'branched_from': source_snapshot_id, 'branch_name': new_name}
        )
        
        self.add_snapshot(branch_snapshot)
        return new_timeline_id
    
    def get_timeline_tree(self, timeline_id: str) -> Dict:
        """Get tree structure of timeline branches"""
        snapshots = self.get_timeline_snapshots(timeline_id)
        
        tree = {
            'timeline_id': timeline_id,
            'snapshots': [
                {
                    'snapshot_id': s.snapshot_id,
                    'time': s.simulation_time,
                    'phase': s.phase,
                    'branches': [
                        tid for tid, snaps in self.timelines.items()
                        if snaps and self.snapshots[snaps[0]].parent_snapshot_id == s.snapshot_id
                    ]
                }
                for s in snapshots
            ]
        }
        
        return tree


class EvolutionController:
    """Manages adaptive timestep evolution"""
    
    def __init__(self, base_dt: float = 0.01, max_dt: float = 1.0, min_dt: float = 0.001):
        self.base_dt = base_dt
        self.max_dt = max_dt
        self.min_dt = min_dt
        
        self.current_dt = base_dt
        self.accumulated_error = 0.0
        
    def adapt_timestep(self, field_change_rate: float, stability_threshold: float = 0.1) -> float:
        """Adjust timestep based on field evolution rate
        
        If fields are changing rapidly (high gradient), reduce timestep
        If fields are stable, increase timestep
        """
        if field_change_rate > stability_threshold:
            # Rapid change - reduce timestep
            self.current_dt = max(self.min_dt, self.current_dt * 0.8)
        elif field_change_rate < stability_threshold * 0.1:
            # Slow change - increase timestep
            self.current_dt = min(self.max_dt, self.current_dt * 1.2)
        
        return self.current_dt
    
    def get_phase_timestep(self, phase: SimulationPhase) -> float:
        """Get appropriate timestep for evolution phase"""
        phase_dt_map = {
            SimulationPhase.PRIMORDIAL: 0.001,
            SimulationPhase.INFLATION: 0.005,
            SimulationPhase.RADIATION_ERA: 0.01,
            SimulationPhase.MATTER_ERA: 0.02,
            SimulationPhase.STRUCTURE_FORMATION: 0.01,
            SimulationPhase.GALAXY_FORMATION: 0.05,
            SimulationPhase.STELLAR_ERA: 0.1,
            SimulationPhase.PLANETARY_ERA: 0.2
        }
        
        return phase_dt_map.get(phase, self.base_dt)


class UniverseEvolutionEngine:
    """Core simulation engine managing universe evolution"""
    
    def __init__(self, grid_size: int = 32, hubble_parameter: float = 0.07,
                 timeline_name: str = "main"):
        self.grid_size = grid_size
        self.H0 = hubble_parameter
        
        # Timeline management
        self.timeline_manager = TimelineManager()
        self.current_timeline_id = self.timeline_manager.create_timeline(timeline_name)
        
        # Evolution control
        self.evolution_controller = EvolutionController()
        
        # Current simulation state
        self.current_time = 0.0
        self.current_phase = SimulationPhase.INITIALIZED
        self.scale_factor = 1e-6
        
        # Hierarchical objects
        self.galaxies: Dict[str, Galaxy] = {}
        self.stellar_systems: Dict[str, StellarSystem] = {}
        self.planets: Dict[str, Planet] = {}
        
        # Substrate fields (will be initialized)
        self.rho_xi = None
        self.T_xi = None
        self.tau_xi = None
        self.phi_xi = None
        
    def initialize_substrate(self, amplitude: float = 1e-5, seed: Optional[int] = None):
        """Initialize quantum fluctuations in primordial substrate"""
        if seed is not None:
            np.random.seed(seed)
        
        self.rho_xi = np.ones((self.grid_size, self.grid_size, self.grid_size)) + \
                     amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size)
        self.T_xi = np.ones((self.grid_size, self.grid_size, self.grid_size)) + \
                   amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size)
        self.tau_xi = amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size, 3)
        self.phi_xi = amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size)
        
        self.current_phase = SimulationPhase.PRIMORDIAL
        self._create_snapshot("Initial quantum fluctuations")
        
    def evolve_timestep(self, dt: float) -> Dict[str, float]:
        """Evolve substrate one timestep using QMRT equations
        
        Returns metrics about evolution stability
        """
        # Simple finite difference Laplacian
        def laplacian(field):
            lap = np.zeros_like(field)
            if field.ndim == 3:
                lap[1:-1, 1:-1, 1:-1] = (
                    field[2:, 1:-1, 1:-1] + field[:-2, 1:-1, 1:-1] +
                    field[1:-1, 2:, 1:-1] + field[1:-1, :-2, 1:-1] +
                    field[1:-1, 1:-1, 2:] + field[1:-1, 1:-1, :-2] -
                    6 * field[1:-1, 1:-1, 1:-1]
                )
            return lap
        
        # Store previous state
        rho_old = self.rho_xi.copy()
        
        # Coupled wave equations (simplified)
        lap_rho = laplacian(self.rho_xi)
        lap_T = laplacian(self.T_xi)
        lap_phi = laplacian(self.phi_xi)
        
        # Update fields
        self.rho_xi += dt * lap_rho * 0.1
        self.T_xi += dt * lap_T * 0.1
        self.phi_xi += dt * lap_phi * 0.1
        
        # Damping
        self.rho_xi *= 0.999
        self.T_xi *= 0.999
        
        # Normalize periodically
        if self.current_time % 100 < dt:
            self.rho_xi = 1.0 + (self.rho_xi - np.mean(self.rho_xi)) * 0.8
        
        # Calculate stability metrics
        change_rate = np.mean(np.abs(self.rho_xi - rho_old)) / dt
        
        self.current_time += dt
        
        return {
            'time': self.current_time,
            'change_rate': float(change_rate),
            'mean_density': float(np.mean(self.rho_xi)),
            'density_variance': float(np.var(self.rho_xi))
        }
    
    def run_evolution_phase(self, phase: SimulationPhase, duration: float, 
                           snapshot_interval: Optional[float] = None) -> List[str]:
        """Run evolution for a specific phase with automatic snapshots"""
        self.current_phase = phase
        dt = self.evolution_controller.get_phase_timestep(phase)
        
        steps = int(duration / dt)
        snapshot_step = int(snapshot_interval / dt) if snapshot_interval else steps
        
        snapshot_ids = []
        
        print(f"🔄 Phase: {phase.value}")
        print(f"   Duration: {duration:.1f}, Steps: {steps}, dt: {dt:.4f}")
        
        for step in range(steps):
            metrics = self.evolve_timestep(dt)
            
            # Adaptive timestep
            dt = self.evolution_controller.adapt_timestep(metrics['change_rate'])
            
            # Create snapshot
            if step % snapshot_step == 0:
                snapshot_id = self._create_snapshot(f"{phase.value}_step_{step}")
                snapshot_ids.append(snapshot_id)
        
        print(f"   ✓ Complete. Final time: {self.current_time:.1f}")
        return snapshot_ids
    
    def _create_snapshot(self, description: str) -> str:
        """Create snapshot of current simulation state"""
        # Calculate statistics
        stats = {
            'mean_density': float(np.mean(self.rho_xi)),
            'density_variance': float(np.var(self.rho_xi)),
            'mean_temperature': float(np.mean(self.T_xi))
        }
        
        # Create substrate state
        substrate = SubstrateState.from_numpy(
            time=self.current_time,
            scale_factor=self.scale_factor,
            fields={
                'density': self.rho_xi,
                'tension': self.T_xi,
                'torsion': self.tau_xi,
                'coherence': self.phi_xi
            },
            stats=stats
        )
        
        # Create snapshot
        snapshot = SimulationSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timeline_id=self.current_timeline_id,
            parent_snapshot_id=None,  # TODO: track parent
            simulation_time=self.current_time,
            real_timestamp=datetime.now(timezone.utc).isoformat(),
            phase=self.current_phase.value,
            substrate=substrate,
            galaxies=[g.to_dict() for g in self.galaxies.values()],
            stellar_systems=[s.to_dict() for s in self.stellar_systems.values()],
            planets=[p.to_dict() for p in self.planets.values()],
            hubble_parameter=self.H0,
            grid_size=self.grid_size,
            metadata={'description': description}
        )
        
        self.timeline_manager.add_snapshot(snapshot)
        return snapshot.snapshot_id
    
    def load_snapshot(self, snapshot_id: str):
        """Load simulation state from snapshot"""
        snapshot = self.timeline_manager.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Restore substrate state
        fields = snapshot.substrate.to_numpy()
        self.rho_xi = fields['density']
        self.T_xi = fields['tension']
        self.tau_xi = fields['torsion']
        self.phi_xi = fields['coherence']
        
        # Restore metadata
        self.current_time = snapshot.simulation_time
        self.current_phase = SimulationPhase(snapshot.phase)
        self.scale_factor = snapshot.substrate.scale_factor
        self.current_timeline_id = snapshot.timeline_id
        
        print(f"✓ Loaded snapshot from t={self.current_time:.1f}, phase={self.current_phase.value}")
    
    def export_state(self) -> Dict:
        """Export complete simulation state for external systems (Unreal, etc)"""
        return {
            'metadata': {
                'timeline_id': self.current_timeline_id,
                'simulation_time': self.current_time,
                'phase': self.current_phase.value,
                'grid_size': self.grid_size
            },
            'substrate': {
                'mean_density': float(np.mean(self.rho_xi)),
                'mean_tension': float(np.mean(self.T_xi)),
                'mean_torsion': float(np.mean(np.linalg.norm(self.tau_xi, axis=-1))),
                'density_field_downsampled': self.rho_xi[::4, ::4, ::4].tolist()
            },
            'hierarchical_objects': {
                'galaxies': len(self.galaxies),
                'stellar_systems': len(self.stellar_systems),
                'planets': len(self.planets),
                'galaxy_list': [g.to_dict() for g in self.galaxies.values()],
                'system_list': [s.to_dict() for s in self.stellar_systems.values()],
                'planet_list': [p.to_dict() for p in self.planets.values()]
            }
        }
