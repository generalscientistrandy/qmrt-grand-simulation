"""
QMRT Quark-Level Engine API

API endpoints for dual-basin attractor ontology validation.

Key concepts:
- φ ∈ (−π, +π) symmetric around zero
- Matter basin: φ ≈ 0
- Antimatter basin: φ ≈ ±π (same solution family, phase-inverted)
- Annihilation: opposite-phase overlap → coherence collapse
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging
import traceback

from qmrt_quark_engine import (
    QMRTQuarkEngine,
    QMRTQuarkParameters,
    run_dual_basin_validation,
    run_annihilation_test,
    run_structure_persistence_test
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qmrt_quark", tags=["QMRT Quark Engine"])

# Active engines
engines: Dict[str, QMRTQuarkEngine] = {}


class DualBasinValidationRequest(BaseModel):
    """Request for dual-basin attractor validation test"""
    grid_size: int = Field(default=24, ge=8, le=64, description="Grid size (cubed)")
    amplitude: float = Field(default=0.05, ge=0.001, le=1.0, description="Initial fluctuation amplitude")
    total_time: float = Field(default=30.0, ge=1.0, le=200.0, description="Total simulation time")
    dt: float = Field(default=0.01, ge=0.001, le=0.1, description="Timestep")
    matter_fraction: float = Field(default=0.5, ge=0.1, le=0.9, description="Initial fraction in matter basin")
    seed: Optional[int] = Field(default=42, description="Random seed")


class AnnihilationTestRequest(BaseModel):
    """Request for annihilation dynamics test"""
    grid_size: int = Field(default=24, ge=8, le=64)
    amplitude: float = Field(default=0.1, ge=0.001, le=1.0)
    total_time: float = Field(default=20.0, ge=1.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class PersistenceTestRequest(BaseModel):
    """Request for structure persistence test"""
    grid_size: int = Field(default=24, ge=8, le=64)
    amplitude: float = Field(default=0.08, ge=0.001, le=1.0)
    total_time: float = Field(default=50.0, ge=1.0, le=200.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class InitializeEngineRequest(BaseModel):
    """Request for initializing a quark engine"""
    name: str = Field(default="QuarkEngine", description="Engine name")
    grid_size: int = Field(default=24, ge=8, le=64)
    amplitude: float = Field(default=0.05, ge=0.001, le=1.0)
    matter_fraction: float = Field(default=0.5, ge=0.1, le=0.9)
    seed: Optional[int] = Field(default=None)
    
    # Optional parameter overrides
    a_phi: Optional[float] = Field(default=None, description="Phase potential strength")
    S_threshold: Optional[float] = Field(default=None, description="Structure detection threshold")


class EvolveEngineRequest(BaseModel):
    """Request for evolving an engine"""
    steps: int = Field(default=100, ge=1, le=10000)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)


@router.get("/theory")
async def get_theory_summary():
    """
    Return summary of QMRT dual-basin attractor ontology.
    
    This is the foundational physics - validating symmetric
    attractor basins before building higher-order composites.
    """
    return {
        "title": "QMRT Dual-Basin Attractor Ontology",
        "purpose": "Validate stable dual-basin attractors for matter/antimatter phase symmetry",
        "phase_convention": {
            "range": "φ ∈ (−π, +π)",
            "symmetry": "Symmetric around zero",
            "matter_basin": "φ ≈ 0 (|φ| < π/2)",
            "antimatter_basin": "φ ≈ ±π (|φ| ≥ π/2)",
            "note": "Antimatter is NOT a separate species - it's the same solution family, phase-inverted"
        },
        "dual_basin_potential": {
            "form": "U_φ(φ) = -a_φ cos(φ)",
            "minima": "φ = 0 (matter) and φ = ±π (antimatter)",
            "interpretation": "Creates symmetric attractor basins"
        },
        "annihilation_dynamics": {
            "trigger": "Opposite-basin structures overlap",
            "effects": [
                "Coherence collapse of both structures",
                "Rapid phase decoherence cascade",
                "Energy redistribution into substrate wave spectrum",
                "Possible formation of neutral transitional attractors (φ ≈ ±π/2)"
            ]
        },
        "structure_tracking": {
            "methods": ["Centroid-based tracking", "Topological fingerprinting"],
            "combined": "Weighted combination of both methods for robust identity tracking"
        },
        "classification": {
            "approach": "Emergent from field mode properties - NOT hardcoded particle labels",
            "properties": [
                "Binding energy",
                "Winding number (topological charge)",
                "Vorticity",
                "Coherence length",
                "Radial profile"
            ]
        },
        "goal": "Validate ontology before building composite structures (hadrons, atoms, etc.)"
    }


@router.post("/validate_dual_basin")
async def validate_dual_basin(request: DualBasinValidationRequest):
    """
    Run dual-basin attractor validation test.
    
    Tests:
    1. Both matter (φ≈0) and antimatter (φ≈±π) basins remain stable
    2. Structures form in both basins
    3. Basin occupation remains roughly symmetric
    4. Energy is conserved throughout
    """
    try:
        logger.info(f"Starting dual-basin validation: {request.grid_size}³, {request.total_time}s")
        
        result = run_dual_basin_validation(
            grid_size=request.grid_size,
            amplitude=request.amplitude,
            total_time=request.total_time,
            dt=request.dt,
            matter_fraction=request.matter_fraction,
            seed=request.seed
        )
        
        logger.info(f"Validation complete. Basin symmetry: {result['validation_results']['basin_symmetry_preserved']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Dual-basin validation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/test_annihilation")
async def test_annihilation(request: AnnihilationTestRequest):
    """
    Test annihilation dynamics between matter and antimatter structures.
    
    Initializes explicit matter and antimatter blobs in close proximity
    to observe annihilation cascade dynamics.
    """
    try:
        logger.info(f"Starting annihilation test: {request.grid_size}³")
        
        result = run_annihilation_test(
            grid_size=request.grid_size,
            amplitude=request.amplitude,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Annihilation test complete. Events: {result['annihilation_count']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Annihilation test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/test_persistence")
async def test_persistence(request: PersistenceTestRequest):
    """
    Test long-term structure persistence in both basins.
    
    Validates that coherent structures can survive for extended periods
    in both matter and antimatter attractor basins.
    """
    try:
        logger.info(f"Starting persistence test: {request.total_time}s")
        
        result = run_structure_persistence_test(
            grid_size=request.grid_size,
            amplitude=request.amplitude,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info("Persistence test complete")
        
        return result
        
    except Exception as e:
        logger.error(f"Persistence test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/initialize")
async def initialize_engine(request: InitializeEngineRequest):
    """
    Initialize a new quark engine for step-by-step evolution.
    """
    try:
        # Build parameters
        params = QMRTQuarkParameters()
        if request.a_phi is not None:
            params.a_phi = request.a_phi
        if request.S_threshold is not None:
            params.S_threshold = request.S_threshold
        
        engine = QMRTQuarkEngine(grid_size=request.grid_size, params=params)
        engine.initialize_dual_basin(
            amplitude=request.amplitude,
            matter_fraction=request.matter_fraction,
            seed=request.seed
        )
        
        engine_id = f"{request.name}_{id(engine)}"
        engines[engine_id] = engine
        
        return {
            "engine_id": engine_id,
            "phase_convention": "φ ∈ (−π, +π)",
            "initial_state": engine.get_state_summary(),
            "message": "Quark engine initialized for dual-basin attractor validation"
        }
        
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engine_id}/evolve")
async def evolve_engine(engine_id: str, request: EvolveEngineRequest):
    """Evolve an engine for specified steps"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    try:
        engine = engines[engine_id]
        
        evolution_metrics = []
        sample_interval = max(1, request.steps // 10)
        
        for step in range(request.steps):
            metrics = engine.evolve_timestep(request.dt)
            if step % sample_interval == 0:
                evolution_metrics.append(metrics)
        
        return {
            "engine_id": engine_id,
            "steps_completed": request.steps,
            "final_state": engine.get_state_summary(),
            "evolution_summary": evolution_metrics[-1] if evolution_metrics else {},
            "structures": {
                "active": len(engine.active_structures),
                "matter": sum(1 for s in engine.active_structures.values() if s.basin.value == 'matter'),
                "antimatter": sum(1 for s in engine.active_structures.values() if s.basin.value == 'antimatter'),
                "items": [s.to_dict() for s in list(engine.active_structures.values())[:30]]
            },
            "annihilation_events": len(engine.annihilation_events)
        }
        
    except Exception as e:
        logger.error(f"Evolution error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engine_id}/state")
async def get_engine_state(engine_id: str):
    """Get current state of an engine"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    return engine.get_state_summary()


@router.get("/{engine_id}/structures")
async def get_structures(engine_id: str):
    """Get all active structures with their properties"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    
    return {
        "engine_id": engine_id,
        "time": engine.time,
        "active_structures": [s.to_dict() for s in engine.active_structures.values()],
        "deceased_count": len(engine.deceased_structures),
        "basin_statistics": engine.get_basin_resolved_statistics(),
        "mode_census": engine.get_mode_property_census()
    }


@router.get("/{engine_id}/annihilation_events")
async def get_annihilation_events(engine_id: str):
    """Get all annihilation events"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    
    return {
        "engine_id": engine_id,
        "total_events": len(engine.annihilation_events),
        "events": [e.to_dict() for e in engine.annihilation_events]
    }


@router.get("/{engine_id}/lifetime_distribution")
async def get_lifetime_distribution(engine_id: str):
    """Get lifetime distribution broken down by basin"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    
    return {
        "engine_id": engine_id,
        "distribution": engine.get_lifetime_distribution()
    }


@router.get("/list")
async def list_engines():
    """List all active quark engines"""
    return {
        "count": len(engines),
        "engines": [
            {
                "id": eid,
                "time": e.time,
                "active_structures": len(e.active_structures),
                "annihilation_events": len(e.annihilation_events)
            }
            for eid, e in engines.items()
        ]
    }


@router.delete("/{engine_id}")
async def delete_engine(engine_id: str):
    """Delete an engine to free memory"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    del engines[engine_id]
    return {"message": f"Engine {engine_id} deleted", "remaining": len(engines)}
