"""
Data models for persistent simulation universe
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid


class SubstrateMetrics(BaseModel):
    """QMRT substrate physics metrics"""
    mean_density: float
    std_density: float
    mean_tension: float
    std_tension: float
    mean_torsion: float
    max_torsion: float
    mean_coherence_gradient: float
    max_coherence_gradient: float
    mean_temperature: float
    max_temperature: float
    mean_curvature: float
    max_curvature: float


class WorldParameters(BaseModel):
    """Gameplay-relevant world parameters derived from substrate physics"""
    gravity: float
    gravity_variance: float
    energy_potential: float
    em_field_strength: float
    magnetic_field: float
    atmospheric_chaos: float
    rotational_variance: float
    quantum_stability: float
    biological_viability: float
    consciousness_potential: float
    temperature_mean: float
    temperature_extremes: float
    spatial_distortion: float
    hazard_density: float
    resource_density: float
    survival_difficulty: float


class World(BaseModel):
    """Complete world state"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    death_world_level: int = Field(ge=1, le=15)
    seed: Optional[int] = None
    classification: str
    



class UniverseSimulationResponse(BaseModel):
    """Response from full universe simulation"""
    model_config = ConfigDict(extra="ignore")
    
    id: str
    name: str
    seed: Optional[int]
    
    # Cosmological data
    cosmic_time: float
    scale_factor: float
    structure_seeds: int
    
    # Stellar data
    stellar_systems: int
    stellar_distribution: Dict[str, int]
    
    # Planetary data
    total_planets: int
    habitable_worlds: int
    
    created_at: str

    

class WorldCreateRequest(BaseModel):
    """Request to create a new world"""



class LineageRecord(BaseModel):
    """Lineage tracking record"""
    model_config = ConfigDict(extra="ignore")
    
    entity_id: str
    entity_name: str
    generation: int
    birth_world_id: str
    birth_death_level: int
    parent_id: Optional[str] = None
    born_at: str
    
    # Survival metrics
    worlds_survived: List[str]
    total_predator_encounters: int = 0
    successful_hunts: int = 0
    times_hunted: int = 0
    max_death_level_survived: int
    
    # Apex status
    apex_qualified: bool = False
    apex_verified: bool = False
    predator_dominance_score: float = 0.0


class LineageCreateRequest(BaseModel):
    """Request to create lineage"""
    entity_name: str
    birth_world_id: str
    parent_id: Optional[str] = None


class LineageUpdateRequest(BaseModel):
    """Request to update lineage survival metrics"""
    world_id: Optional[str] = None
    death_level: Optional[int] = None
    was_hunter: Optional[bool] = None
    hunt_success: Optional[bool] = None

    name: str
    death_world_level: int = Field(ge=1, le=15, description="Death-world difficulty (1-15, Earth=10)")
    seed: Optional[int] = None
    evolution_steps: int = Field(default=200, ge=50, le=1000)
    cosmological_simulation_id: Optional[str] = Field(default=None, description="ID of cosmological simulation to use as seed")
    structure_seed_index: Optional[int] = Field(default=None, description="Index of structure seed from cosmological simulation")


class WorldResponse(BaseModel):
    """Response with world data"""
    id: str
    name: str
    death_world_level: int
    seed: Optional[int]
    classification: str
    world_parameters: Dict[str, Any]
    substrate_metrics: Dict[str, Any]
    created_at: str
    apex_qualified: bool


class WorldListResponse(BaseModel):
    """List of worlds with summary info"""
    worlds: List[WorldResponse]
    total: int


class CosmologicalSimulation(BaseModel):
    """Complete cosmological simulation state"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    seed: Optional[int] = None
    
    # Simulation results
    final_epoch: str
    cosmic_time: float
    scale_factor: float
    num_structure_seeds: int
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed: bool = True


class CosmologicalSimulationRequest(BaseModel):
    """Request to run cosmological simulation"""
    name: str
    seed: Optional[int] = None
    grid_size: int = Field(default=64, ge=32, le=128)


class CosmologicalSimulationResponse(BaseModel):
    """Response with cosmological simulation data"""
    id: str
    name: str
    seed: Optional[int]
    final_epoch: str
    cosmic_time: float
    scale_factor: float
    num_structure_seeds: int
    structure_seeds: List[Dict[str, Any]]
    snapshots: int
    created_at: str


class SimulationMode(BaseModel):
    """Information about simulation modes"""
    mode: str
    name: str
    description: str
    use_case: str
