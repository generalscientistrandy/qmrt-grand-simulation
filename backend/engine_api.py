"""
Universe Engine API - State management, snapshots, and timeline control
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from universe_engine import (
    UniverseEvolutionEngine, SimulationPhase, TimelineManager
)
import logging

# Global engine instances (in production, use proper state management)
engines: Dict[str, UniverseEvolutionEngine] = {}
timeline_managers: Dict[str, TimelineManager] = {}


class EngineInitRequest(BaseModel):
    """Initialize universe engine"""
    name: str
    grid_size: int = 32
    hubble_parameter: float = 0.07
    initial_amplitude: float = 1e-5
    seed: Optional[int] = None


class EvolutionRequest(BaseModel):
    """Run evolution phase"""
    phase: str  # SimulationPhase enum value
    duration: float
    snapshot_interval: Optional[float] = None


class SnapshotRequest(BaseModel):
    """Create manual snapshot"""
    description: str


class BranchRequest(BaseModel):
    """Branch timeline from snapshot"""
    snapshot_id: str
    new_timeline_name: str


router = APIRouter(prefix="/engine", tags=["Universe Engine"])


@router.post("/initialize")
async def initialize_engine(request: EngineInitRequest):
    """Initialize new universe evolution engine"""
    try:
        engine = UniverseEvolutionEngine(
            grid_size=request.grid_size,
            hubble_parameter=request.hubble_parameter,
            timeline_name=request.name
        )
        
        engine.initialize_substrate(
            amplitude=request.initial_amplitude,
            seed=request.seed
        )
        
        engine_id = engine.current_timeline_id
        engines[engine_id] = engine
        
        return {
            "engine_id": engine_id,
            "timeline_id": engine.current_timeline_id,
            "name": request.name,
            "grid_size": request.grid_size,
            "current_time": engine.current_time,
            "phase": engine.current_phase.value,
            "message": f"Engine initialized: {request.name}"
        }
        
    except Exception as e:
        logging.error(f"Error initializing engine: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engine_id}/evolve")
async def evolve_phase(engine_id: str, request: EvolutionRequest):
    """Run evolution for a specific phase"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    try:
        engine = engines[engine_id]
        
        # Parse phase
        phase = SimulationPhase(request.phase)
        
        # Run evolution
        snapshot_ids = engine.run_evolution_phase(
            phase=phase,
            duration=request.duration,
            snapshot_interval=request.snapshot_interval
        )
        
        return {
            "engine_id": engine_id,
            "phase": phase.value,
            "duration": request.duration,
            "current_time": engine.current_time,
            "snapshots_created": len(snapshot_ids),
            "snapshot_ids": snapshot_ids
        }
        
    except Exception as e:
        logging.error(f"Error in evolution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engine_id}/snapshot")
async def create_snapshot(engine_id: str, request: SnapshotRequest):
    """Create manual snapshot of current state"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    snapshot_id = engine._create_snapshot(request.description)
    
    return {
        "snapshot_id": snapshot_id,
        "simulation_time": engine.current_time,
        "phase": engine.current_phase.value,
        "description": request.description
    }


@router.get("/{engine_id}/snapshots")
async def list_snapshots(engine_id: str):
    """List all snapshots for engine timeline"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    snapshots = engine.timeline_manager.get_timeline_snapshots(engine.current_timeline_id)
    
    return {
        "engine_id": engine_id,
        "timeline_id": engine.current_timeline_id,
        "total_snapshots": len(snapshots),
        "snapshots": [
            {
                "snapshot_id": s.snapshot_id,
                "simulation_time": s.simulation_time,
                "phase": s.phase,
                "real_timestamp": s.real_timestamp,
                "description": s.metadata.get('description', '')
            }
            for s in snapshots
        ]
    }


@router.post("/{engine_id}/load-snapshot/{snapshot_id}")
async def load_snapshot(engine_id: str, snapshot_id: str):
    """Load simulation state from snapshot"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    try:
        engine = engines[engine_id]
        engine.load_snapshot(snapshot_id)
        
        return {
            "snapshot_id": snapshot_id,
            "loaded_time": engine.current_time,
            "loaded_phase": engine.current_phase.value,
            "message": "Snapshot loaded successfully"
        }
        
    except Exception as e:
        logging.error(f"Error loading snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engine_id}/branch")
async def branch_timeline(engine_id: str, request: BranchRequest):
    """Create new timeline branch from snapshot"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    try:
        engine = engines[engine_id]
        new_timeline_id = engine.timeline_manager.branch_timeline(
            source_snapshot_id=request.snapshot_id,
            new_name=request.new_timeline_name
        )
        
        # Create new engine for branch
        new_engine = UniverseEvolutionEngine(
            grid_size=engine.grid_size,
            hubble_parameter=engine.H0,
            timeline_name=request.new_timeline_name
        )
        new_engine.timeline_manager = engine.timeline_manager
        new_engine.current_timeline_id = new_timeline_id
        new_engine.load_snapshot(request.snapshot_id)
        
        engines[new_timeline_id] = new_engine
        
        return {
            "source_engine_id": engine_id,
            "new_engine_id": new_timeline_id,
            "new_timeline_id": new_timeline_id,
            "branched_from_snapshot": request.snapshot_id,
            "branch_name": request.new_timeline_name,
            "message": f"Timeline branched: {request.new_timeline_name}"
        }
        
    except Exception as e:
        logging.error(f"Error branching timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engine_id}/state")
async def get_engine_state(engine_id: str):
    """Get current engine state"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    
    return {
        "engine_id": engine_id,
        "timeline_id": engine.current_timeline_id,
        "current_time": engine.current_time,
        "current_phase": engine.current_phase.value,
        "scale_factor": engine.scale_factor,
        "grid_size": engine.grid_size,
        "hubble_parameter": engine.H0,
        "hierarchical_objects": {
            "galaxies": len(engine.galaxies),
            "stellar_systems": len(engine.stellar_systems),
            "planets": len(engine.planets)
        }
    }


@router.get("/{engine_id}/export")
async def export_state(engine_id: str):
    """Export complete state for external systems (Unreal, etc)"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    return engine.export_state()


@router.get("/{engine_id}/timeline-tree")
async def get_timeline_tree(engine_id: str):
    """Get timeline branch structure"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    return engine.timeline_manager.get_timeline_tree(engine.current_timeline_id)


@router.get("/list")
async def list_engines():
    """List all active engines"""
    return {
        "total_engines": len(engines),
        "engines": [
            {
                "engine_id": eid,
                "timeline_id": engine.current_timeline_id,
                "current_time": engine.current_time,
                "phase": engine.current_phase.value
            }
            for eid, engine in engines.items()
        ]
    }
