"""
QMRT Canonical Hamiltonian API - Proper physics implementation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import logging
import traceback

from qmrt_hamiltonian_engine import (
    QMRTSubstrateEngine, 
    QMRTParameters, 
    run_qmrt_simulation
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qmrt", tags=["QMRT Canonical"])

# Active engines
engines: Dict[str, QMRTSubstrateEngine] = {}


class SimulationRequest(BaseModel):
    """Request for running QMRT simulation"""
    name: str = "QMRT_Simulation"
    grid_size: int = 32
    amplitude: float = 0.1
    total_time: float = 10.0
    dt: float = 0.01
    seed: Optional[int] = None
    
    # Optional parameter overrides
    a_rho: Optional[float] = None
    b_rho: Optional[float] = None
    c_rho: Optional[float] = None
    chi_sigma: Optional[float] = None
    chi_tau: Optional[float] = None
    chi_phi: Optional[float] = None


class InitializeRequest(BaseModel):
    """Request for initializing a QMRT engine"""
    name: str = "QMRT_Engine"
    grid_size: int = 32
    amplitude: float = 0.1
    seed: Optional[int] = None


class EvolveRequest(BaseModel):
    """Request for evolving an engine"""
    steps: int = 100
    dt: float = 0.01
    detect_structures: bool = True


@router.post("/run")
async def run_simulation(request: SimulationRequest):
    """
    Run a complete QMRT canonical simulation
    
    This uses the proper Hamiltonian formulation with:
    - Exact energy conservation (symplectic integration)
    - Emergent expansion from field dynamics
    - Structure detection via stabilization functional
    - Proton formation criterion
    """
    try:
        # Build parameters
        params = QMRTParameters()
        
        if request.a_rho is not None:
            params.a_rho = request.a_rho
        if request.b_rho is not None:
            params.b_rho = request.b_rho
        if request.c_rho is not None:
            params.c_rho = request.c_rho
        if request.chi_sigma is not None:
            params.chi_sigma = request.chi_sigma
        if request.chi_tau is not None:
            params.chi_tau = request.chi_tau
        if request.chi_phi is not None:
            params.chi_phi = request.chi_phi
        
        logger.info(f"Starting QMRT simulation: {request.grid_size}³, {request.total_time}s")
        
        result = run_qmrt_simulation(
            grid_size=request.grid_size,
            amplitude=request.amplitude,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed,
            params=params
        )
        
        logger.info(f"Simulation complete: energy drift = {result['energy_conservation']['drift_pct']:.4f}%")
        
        return result
        
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/initialize")
async def initialize_engine(request: InitializeRequest):
    """Initialize a new QMRT engine for step-by-step evolution"""
    try:
        engine = QMRTSubstrateEngine(grid_size=request.grid_size)
        engine.initialize_equilibrium(amplitude=request.amplitude, seed=request.seed)
        
        engine_id = f"{request.name}_{id(engine)}"
        engines[engine_id] = engine
        
        return {
            "engine_id": engine_id,
            "initial_state": engine.get_state_summary(),
            "message": "QMRT engine initialized with canonical Hamiltonian dynamics"
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
        for step in range(request.steps):
            metrics = engine.evolve_timestep(request.dt)
            if step % max(1, request.steps // 10) == 0:
                evolution_metrics.append(metrics)
        
        structures = []
        if request.detect_structures:
            detected = engine.detect_structures()
            structures = [s.to_dict() for s in detected[:30]]
        
        return {
            "engine_id": engine_id,
            "steps_completed": request.steps,
            "final_state": engine.get_state_summary(),
            "evolution_summary": evolution_metrics[-1] if evolution_metrics else {},
            "structures": {
                "count": len(engine.structures),
                "proton_candidates": sum(1 for s in engine.structures if s.is_proton_candidate),
                "items": structures
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
    
    engine = engines[engine_id]
    return engine.get_state_summary()


@router.get("/{engine_id}/energy-history")
async def get_energy_history(engine_id: str):
    """Get energy conservation history"""
    if engine_id not in engines:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    engine = engines[engine_id]
    
    return {
        "initial_energy": engine.initial_energy,
        "current_energy": engine.compute_total_energy(),
        "history_length": len(engine.energy_history),
        "recent_values": engine.energy_history[-100:] if engine.energy_history else [],
        "drift_pct": engine.get_state_summary()['energy_drift_pct']
    }


@router.get("/list")
async def list_engines():
    """List all active QMRT engines"""
    return {
        "count": len(engines),
        "engines": [
            {
                "id": eid,
                "time": e.time,
                "scale_factor": e.a,
                "structures": len(e.structures)
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


@router.get("/theory")
async def get_theory_summary():
    """Return summary of implemented QMRT physics"""
    return {
        "title": "QMRT Canonical Hamiltonian Implementation",
        "hamiltonian": {
            "kinetic": "Σ(π²/2M) for ρ, σ, τ, φ",
            "potential_rho": "U_ρ(ρ) = (a/2)ρ² + (b/3)ρ³ + (c/4)ρ⁴",
            "harmonic": "(a_σ/2)σ² + (a_τ/2)τ² + (a_φ/2)φ²",
            "couplings": "λ_ρσ·ρσ + λ_ρτ·ρτ² + λ_στ·στ + λ_σφ·σφ² + λ_τφ·τ²φ² + λ_ρφ·ρφ",
            "gradient": "(K/2)|∇field|² for all fields"
        },
        "evolution": {
            "method": "Störmer-Verlet symplectic integration",
            "energy_conservation": "Intrinsic (no artificial correction needed)",
            "equations": "Hamilton's canonical equations: dq/dt = ∂H/∂π, dπ/dt = -∂H/∂q"
        },
        "emergent_features": {
            "expansion": "ȧ/a = χ_σ⟨div σ⟩ + χ_τ⟨τ²⟩ + χ_φ⟨|∇φ|²⟩",
            "stabilization": "S(x,t) = [(αρ + β|σ| + γτ²)/(D₀ + η|∇φ|²)]·exp(-κ|∇φ|²)",
            "coherence_length": "ξ(x,t) = ξ₀·exp(-κ|∇φ|²)",
            "proton_criterion": "Π_p = S·ξ/L_p ≥ 1"
        },
        "no_forbidden_concepts": {
            "dark_matter": "Effects emerge from field couplings, not hidden mass",
            "dark_energy": "Expansion emerges from tension gradients, not cosmological constant",
            "singularities": "No point sources - only smooth field configurations"
        }
    }
