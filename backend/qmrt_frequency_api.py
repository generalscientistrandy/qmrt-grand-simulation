"""
QMRT Frequency-Domain Engine API

API for the foundational QMRT physics with explicit frequency field.

Key concept: Frequency (ω) is a medium state variable that enables
spectral universe formation - different frequency bands act as
separate dynamical layers of the same universal medium.

Fields: (ρ, σ, τ, φ, ω) with conjugate momenta
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging
import traceback

from qmrt_frequency_engine import (
    QMRTFrequencyEngine,
    QMRTFrequencyParameters,
    run_frequency_domain_test,
    run_spectral_universe_test
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qmrt_frequency", tags=["QMRT Frequency Engine"])

# Active engines
engines: Dict[str, QMRTFrequencyEngine] = {}


class FrequencyDomainTestRequest(BaseModel):
    """Request for frequency domain separation test"""
    grid_size: int = Field(default=20, ge=8, le=48)
    amplitude: float = Field(default=0.05, ge=0.001, le=1.0)
    total_time: float = Field(default=20.0, ge=1.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    matter_fraction: float = Field(default=0.5, ge=0.1, le=0.9)
    high_freq_fraction: float = Field(default=0.5, ge=0.1, le=0.9)
    seed: Optional[int] = Field(default=42)


class SpectralUniverseTestRequest(BaseModel):
    """Request for spectral universe formation test"""
    grid_size: int = Field(default=20, ge=8, le=48)
    amplitude: float = Field(default=0.1, ge=0.001, le=1.0)
    total_time: float = Field(default=30.0, ge=1.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class InitializeEngineRequest(BaseModel):
    """Request for initializing a frequency engine"""
    name: str = Field(default="FrequencyEngine")
    grid_size: int = Field(default=20, ge=8, le=48)
    amplitude: float = Field(default=0.05, ge=0.001, le=1.0)
    matter_fraction: float = Field(default=0.5, ge=0.1, le=0.9)
    high_freq_fraction: float = Field(default=0.5, ge=0.1, le=0.9)
    seed: Optional[int] = Field(default=None)
    
    # Optional parameter overrides
    omega_0: Optional[float] = Field(default=None, description="Frequency basin center")
    a_omega: Optional[float] = Field(default=None, description="Frequency potential strength")
    g_omega_phi: Optional[float] = Field(default=None, description="Frequency-phase coupling")


class EvolveRequest(BaseModel):
    """Request for evolving an engine"""
    steps: int = Field(default=100, ge=1, le=5000)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)


@router.get("/theory")
async def get_theory_summary():
    """
    Return summary of QMRT frequency-domain physics.
    
    This is the foundational layer where frequency is treated as
    a medium state variable enabling spectral universe formation.
    """
    return {
        "title": "QMRT Frequency-Domain Substrate Engine",
        "purpose": "Foundational physics with explicit frequency field for spectral universe formation",
        "fields": {
            "ρ (rho)": "Density field - determines inertia, gravitational behavior",
            "σ (sigma)": "Tension field - governs wave speed",
            "τ (tau)": "Torsion field - rotational degrees of freedom",
            "φ (phi)": "Phase field ∈ (−π, +π) - matter/antimatter separation",
            "ω (omega)": "Frequency field - spectral universe selector (NEW)"
        },
        "frequency_physics": {
            "band_potential": "V_band(ω) = a_ω(ω² − ω₀²)²",
            "interpretation": "Double-well potential with minima at ω = ±ω₀",
            "creates": "Frequency basins = spectral universes",
            "coupling_to_phase": "g_ωφ · ω · |∇φ|² - matter prefers certain frequency bands",
            "coupling_to_density": "g_ωρ · ω · (ρ − ρ₀)² - density-frequency coupling"
        },
        "multiverse_interpretation": {
            "concept": "Spectral universes in one elastic substrate",
            "mechanism": "Frequency-domain separation via band potential",
            "interaction": "Cross-band coupling suppressed when resonance ≈ 0",
            "antimatter": "May preferentially occupy different frequency bands"
        },
        "entropy_hierarchy": {
            "fundamental_layer": "Weak entropy - governed by field coherence",
            "composite_layer": "Stronger entropy - statistical mechanics emerges",
            "thermodynamic_layer": "Dominant entropy - macroscopic irreversibility"
        },
        "scale_ladder": [
            "1. Fundamental medium (this layer)",
            "2. Frequency stabilization (spectral universes)",
            "3. Quark-like node persistence",
            "4. Hadron confinement",
            "5. EM phase locking",
            "6. Atomic orbital resonance",
            "7. Thermodynamic arrow strengthening"
        ]
    }


@router.post("/test_frequency_domains")
async def test_frequency_domains(request: FrequencyDomainTestRequest):
    """
    Test frequency-domain separation (spectral universe formation).
    
    Validates:
    1. Frequency basins remain stable (ω → ±ω₀)
    2. Phase basins remain stable (φ → 0 or ±π)
    3. Cross-coupling between phase and frequency
    4. Energy conservation
    """
    try:
        logger.info(f"Starting frequency domain test: {request.grid_size}³, {request.total_time}s")
        
        result = run_frequency_domain_test(
            grid_size=request.grid_size,
            amplitude=request.amplitude,
            total_time=request.total_time,
            dt=request.dt,
            matter_fraction=request.matter_fraction,
            high_freq_fraction=request.high_freq_fraction,
            seed=request.seed
        )
        
        logger.info(f"Frequency domain test complete. Energy drift: {result['final_state']['energy_drift_pct']:.4f}%")
        
        return result
        
    except Exception as e:
        logger.error(f"Frequency domain test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/test_spectral_universes")
async def test_spectral_universes(request: SpectralUniverseTestRequest):
    """
    Test spectral universe formation from turbulent initial conditions.
    
    This is the key QMRT multiverse mechanism:
    - Starts with turbulent frequency distribution
    - Observes clustering into frequency basins (spectral universes)
    - Tracks phase ordering within frequency domains
    """
    try:
        logger.info(f"Starting spectral universe test: {request.grid_size}³, {request.total_time}s")
        
        result = run_spectral_universe_test(
            grid_size=request.grid_size,
            amplitude=request.amplitude,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Spectral universe test complete. Clustering: {result['spectral_universe_metrics']['frequency_clustering']:.2%}")
        
        return result
        
    except Exception as e:
        logger.error(f"Spectral universe test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/initialize")
async def initialize_engine(request: InitializeEngineRequest):
    """
    Initialize a new frequency-domain engine for step-by-step evolution.
    """
    try:
        params = QMRTFrequencyParameters()
        if request.omega_0 is not None:
            params.omega_0 = request.omega_0
        if request.a_omega is not None:
            params.a_omega = request.a_omega
        if request.g_omega_phi is not None:
            params.g_omega_phi = request.g_omega_phi
        
        engine = QMRTFrequencyEngine(grid_size=request.grid_size, params=params)
        engine.initialize_frequency_domains(
            amplitude=request.amplitude,
            matter_fraction=request.matter_fraction,
            high_freq_fraction=request.high_freq_fraction,
            seed=request.seed
        )
        
        engine_id = f"{request.name}_{id(engine)}"
        engines[engine_id] = engine
        
        return {
            "engine_id": engine_id,
            "fields": "(ρ, σ, τ, φ, ω) with momenta",
            "initial_state": engine.get_state_summary(),
            "message": "Frequency-domain engine initialized"
        }
        
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engine_id}/evolve")
async def evolve_engine(engine_id: str, request: EvolveRequest):
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
                "items": [s.to_dict() for s in list(engine.active_structures.values())[:20]]
            }
        }
        
    except Exception as e:
        logger.error(f"Evolution error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engine_id}/state")
async def get_engine_state(engine_id: str):
    """Get current state of an engine"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    return engines[engine_id].get_state_summary()


@router.get("/{engine_id}/structures")
async def get_structures(engine_id: str):
    """Get all active structures with phase AND frequency classification"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    
    return {
        "engine_id": engine_id,
        "time": engine.time,
        "structures": [s.to_dict() for s in engine.active_structures.values()],
        "breakdown": engine.get_state_summary()['structure_breakdown']
    }


@router.get("/list")
async def list_engines():
    """List all active frequency engines"""
    return {
        "count": len(engines),
        "engines": [
            {
                "id": eid,
                "time": e.time,
                "active_structures": len(e.active_structures)
            }
            for eid, e in engines.items()
        ]
    }


@router.delete("/{engine_id}")
async def delete_engine(engine_id: str):
    """Delete an engine"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    del engines[engine_id]
    return {"message": f"Engine {engine_id} deleted", "remaining": len(engines)}
