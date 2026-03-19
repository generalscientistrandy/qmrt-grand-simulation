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
    
    # Physics substrate
    substrate_metrics: SubstrateMetrics
    
    # World parameters
    world_parameters: WorldParameters
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Phase B: Ecology
    ecology_initialized: bool = False
    ecology_summary: Optional[Dict[str, Any]] = None
    
    # Future: lineage, apex qualification
    lineage_origin: Optional[str] = None
    apex_qualified: bool = False
    

class WorldCreateRequest(BaseModel):
    """Request to create a new world"""
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
