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

from qmrt_physics_validation import (
    measure_basin_stability,
    measure_cross_basin_collision,
    measure_scaling_behavior,
    measure_spectral_energy_transport,
    run_full_physics_validation
)

from qmrt_advanced_validation import (
    test_reflection_robustness,
    measure_spectral_energy_spectrum,
    test_mexican_hat_stability,
    complete_scaling_validation
)

from qmrt_basin_diagnosis import (
    diagnose_basin_decay,
    test_isolated_frequency_dynamics,
    test_gradient_free_dynamics,
    test_stronger_potential,
    test_combined_fixes,
    run_full_basin_diagnosis
)

from qmrt_comprehensive_validation import (
    test_scaling_persistence,
    test_entropy_drift,
    track_basin_identities,
    map_phase_diagram,
    run_comprehensive_validation,
    ScalingPersistenceResult,
    EntropyDriftResult,
    BasinStatistics,
    PhaseDiagramResult
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


class BasinStabilityRequest(BaseModel):
    """Request for basin stability measurement"""
    grid_size: int = Field(default=24, ge=12, le=48)
    total_time: float = Field(default=50.0, ge=10.0, le=200.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class CollisionTestRequest(BaseModel):
    """Request for cross-basin collision test"""
    grid_size: int = Field(default=24, ge=16, le=48)
    total_time: float = Field(default=30.0, ge=10.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class ScalingTestRequest(BaseModel):
    """Request for scaling behavior test"""
    grid_sizes: List[int] = Field(default=[12, 16, 20, 24])
    simulation_time: float = Field(default=15.0, ge=5.0, le=50.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class EnergyTransportRequest(BaseModel):
    """Request for spectral energy transport measurement"""
    grid_size: int = Field(default=24, ge=12, le=48)
    total_time: float = Field(default=30.0, ge=10.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class FullValidationRequest(BaseModel):
    """Request for full physics validation suite"""
    quick_mode: bool = Field(default=True, description="Use smaller grids for faster testing")
    seed: Optional[int] = Field(default=42)


class ReflectionRobustnessRequest(BaseModel):
    """Request for reflection robustness testing"""
    seed: Optional[int] = Field(default=42)


class SpectralAnalysisRequest(BaseModel):
    """Request for spectral energy spectrum analysis"""
    grid_size: int = Field(default=24, ge=16, le=48)
    total_time: float = Field(default=20.0, ge=5.0, le=60.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class MexicanHatRequest(BaseModel):
    """Request for Mexican hat potential stability test"""
    grid_size: int = Field(default=20, ge=12, le=40)
    total_time: float = Field(default=30.0, ge=10.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    mu_squared: float = Field(default=0.5, ge=0.1, le=2.0)
    lambda_coeff: float = Field(default=0.25, ge=0.05, le=1.0)
    seed: Optional[int] = Field(default=42)


class CompleteScalingRequest(BaseModel):
    """Request for complete scaling validation"""
    grid_sizes: List[int] = Field(default=[12, 16, 20, 24])
    simulation_time: float = Field(default=10.0, ge=5.0, le=30.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class BasinDiagnosisRequest(BaseModel):
    """Request for basin decay diagnosis"""
    seed: Optional[int] = Field(default=42)


# =============================================================================
# Comprehensive Validation Request Models
# =============================================================================

class ScalingPersistenceRequest(BaseModel):
    """Request for scaling persistence test"""
    grid_sizes: List[int] = Field(default=[20, 24, 32], description="Grid sizes to test")
    simulation_time: float = Field(default=30.0, ge=5.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class EntropyDriftRequest(BaseModel):
    """Request for long-time entropy drift test"""
    grid_size: int = Field(default=20, ge=12, le=40)
    total_time: float = Field(default=60.0, ge=10.0, le=200.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    n_bins: int = Field(default=50, ge=20, le=100)
    seed: Optional[int] = Field(default=42)


class BasinTrackingRequest(BaseModel):
    """Request for basin identity tracking"""
    grid_size: int = Field(default=20, ge=12, le=40)
    total_time: float = Field(default=30.0, ge=10.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class PhaseDiagramRequest(BaseModel):
    """Request for phase diagram mapping"""
    grid_size: int = Field(default=14, ge=10, le=24)
    test_time: float = Field(default=10.0, ge=5.0, le=30.0)
    dt: float = Field(default=0.01, ge=0.001, le=0.1)
    n_points: int = Field(default=20, ge=10, le=50)
    seed: Optional[int] = Field(default=42)


class ComprehensiveValidationRequest(BaseModel):
    """Request for full comprehensive validation suite"""
    quick_mode: bool = Field(default=True, description="Use smaller grids/times for faster testing")
    seed: Optional[int] = Field(default=42)


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


# =============================================================================
# Physics Validation Endpoints
# =============================================================================

@router.post("/validate/basin_stability")
async def validate_basin_stability(request: BasinStabilityRequest):
    """
    Measure basin stability time.
    
    Tests how long frequency domains survive.
    If they stabilize → supports multiverse band idea.
    """
    try:
        logger.info(f"Starting basin stability test: {request.grid_size}³, {request.total_time}s")
        
        result = measure_basin_stability(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Basin stability test complete. Stable: {result.is_stable}")
        
        return {
            'test_name': 'basin_stability',
            'result': result.to_dict(),
            'interpretation': {
                'is_stable': result.is_stable,
                'stability_time': result.stability_time,
                'half_life': result.half_life,
                'supports_multiverse': result.is_stable,
                'note': 'Basins remain stable' if result.is_stable else 'Basins decay - may need parameter tuning'
            }
        }
        
    except Exception as e:
        logger.error(f"Basin stability test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/validate/cross_basin_collision")
async def validate_cross_basin_collision(request: CollisionTestRequest):
    """
    Test cross-basin collision dynamics.
    
    What happens when opposite-polarity frequency domains collide?
    - Annihilation: Domains destroy each other
    - Reflection: Domains bounce off
    - Merge: Domains combine
    - Tunnel: Domains pass through
    
    Tests the antimatter separation hypothesis.
    """
    try:
        logger.info(f"Starting cross-basin collision test: {request.grid_size}³")
        
        result = measure_cross_basin_collision(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Collision test complete. Type: {result.collision_type}")
        
        return {
            'test_name': 'cross_basin_collision',
            'result': result.to_dict(),
            'interpretation': {
                'collision_type': result.collision_type,
                'supports_antimatter_separation': result.collision_type in ['reflection', 'tunnel'],
                'energy_conserved': abs(result.pre_collision_energy - result.post_collision_energy) / result.pre_collision_energy < 0.01,
                'note': f'Collision outcome: {result.collision_type}'
            }
        }
        
    except Exception as e:
        logger.error(f"Collision test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/validate/scaling_behavior")
async def validate_scaling_behavior(request: ScalingTestRequest):
    """
    Test scaling behavior across different resolutions.
    
    Checks if physics is resolution-independent:
    - If basin size scales and structure density remains invariant → Real physics
    - If physics changes with resolution → Numerical artifact
    """
    try:
        logger.info(f"Starting scaling test: grids {request.grid_sizes}")
        
        result = measure_scaling_behavior(
            grid_sizes=request.grid_sizes,
            simulation_time=request.simulation_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Scaling test complete. Invariant: {result.is_scale_invariant}")
        
        return {
            'test_name': 'scaling_behavior',
            'result': result.to_dict(),
            'interpretation': {
                'is_scale_invariant': result.is_scale_invariant,
                'structure_density_exponent': result.scaling_exponents['structure_density_exponent'],
                'is_real_physics': result.is_scale_invariant,
                'note': 'Real regime physics' if result.is_scale_invariant else 'May be numerical artifact - need finer resolution'
            }
        }
        
    except Exception as e:
        logger.error(f"Scaling test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/validate/energy_transport")
async def validate_energy_transport(request: EnergyTransportRequest):
    """
    Measure spectral energy transport.
    
    Tracks energy flow across frequency gradient:
    - Does energy prefer certain frequency bands?
    - If yes → Shows medium band thermodynamics (original result)
    """
    try:
        logger.info(f"Starting energy transport test: {request.grid_size}³, {request.total_time}s")
        
        result = measure_spectral_energy_transport(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Energy transport test complete. Preferred band: {result.preferred_band}")
        
        return {
            'test_name': 'spectral_energy_transport',
            'result': result.to_dict(),
            'interpretation': {
                'has_preferred_band': result.preferred_band != 'neutral',
                'preferred_band': result.preferred_band,
                'transport_coefficient': result.transport_coefficient,
                'shows_band_thermodynamics': result.transport_coefficient > 0.1,
                'note': 'Shows medium band thermodynamics' if result.transport_coefficient > 0.1 else 'Weak energy transport'
            }
        }
        
    except Exception as e:
        logger.error(f"Energy transport test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/validate/full_suite")
async def validate_full_suite(request: FullValidationRequest):
    """
    Run complete physics validation suite.
    
    Tests all four validation criteria:
    1. Basin stability time
    2. Cross-basin collision dynamics
    3. Scaling behavior
    4. Spectral energy transport
    
    Returns comprehensive assessment of QMRT physics validity.
    """
    try:
        logger.info(f"Starting full validation suite. Quick mode: {request.quick_mode}")
        
        result = run_full_physics_validation(
            quick_mode=request.quick_mode,
            seed=request.seed
        )
        
        logger.info(f"Full validation complete. Validity: {result['overall_assessment']['physics_validity']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Full validation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


# =============================================================================
# Advanced Validation Endpoints
# =============================================================================

@router.post("/validate/reflection_robustness")
async def validate_reflection_robustness(request: ReflectionRobustnessRequest):
    """
    Test if reflection behavior is robust under parameter variations.
    
    Tests:
    1. Vary coupling constants
    2. Vary grid resolution  
    3. Add noise to initial conditions
    
    If reflection persists → real physics
    If it doesn't → numerical artifact
    """
    try:
        logger.info("Starting reflection robustness test")
        
        result = test_reflection_robustness(seed=request.seed)
        
        logger.info(f"Reflection robustness test complete. Robust: {result.reflection_robust}")
        
        return {
            'test_name': 'reflection_robustness',
            'result': result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Reflection robustness test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/validate/spectral_analysis")
async def validate_spectral_analysis(request: SpectralAnalysisRequest):
    """
    Measure spectral energy spectrum E(k) and power law.
    
    Looking for E(k) ∝ k^α where:
    - α < 0: Forward cascade (energy to small scales)
    - α > 0: Inverse cascade (energy to large scales)
    - α ≈ -5/3: Kolmogorov-like turbulence
    """
    try:
        logger.info(f"Starting spectral analysis: {request.grid_size}³, {request.total_time}s")
        
        result = measure_spectral_energy_spectrum(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Spectral analysis complete. α = {result.power_law_exponent:.2f}")
        
        return {
            'test_name': 'spectral_energy_spectrum',
            'result': result.to_dict(),
            'interpretation': {
                'power_law_exponent': result.power_law_exponent,
                'cascade_direction': result.cascade_type,
                'kolmogorov_like': result.kolmogorov_like,
                'fit_quality': result.power_law_r_squared,
                'note': f'E(k) ∝ k^{result.power_law_exponent:.2f}, cascade: {result.cascade_type}'
            }
        }
        
    except Exception as e:
        logger.error(f"Spectral analysis error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/validate/mexican_hat_stability")
async def validate_mexican_hat_stability(request: MexicanHatRequest):
    """
    Test basin stability with Mexican hat potential.
    
    V(ω) = -½μ²ω² + ¼λω⁴
    
    Creates deeper minima at ω = ±√(μ²/λ) for improved stability.
    """
    try:
        logger.info(f"Starting Mexican hat stability test: μ²={request.mu_squared}, λ={request.lambda_coeff}")
        
        result = test_mexican_hat_stability(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            mu_squared=request.mu_squared,
            lambda_coeff=request.lambda_coeff,
            seed=request.seed
        )
        
        logger.info(f"Mexican hat test complete. Stable: {result['is_stable']}")
        
        return {
            'test_name': 'mexican_hat_stability',
            'result': result,
            'interpretation': {
                'is_stable': result['is_stable'],
                'stability_time': result['stability_time'],
                'improvement': 'YES' if result['improvement_over_quartic'] else 'NO',
                'omega_minima': result['parameters']['omega_min'],
                'note': f"Stability time: {result['stability_time']:.1f}s (vs 0.3s baseline)"
            }
        }
        
    except Exception as e:
        logger.error(f"Mexican hat test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/validate/complete_scaling")
async def validate_complete_scaling(request: CompleteScalingRequest):
    """
    Complete scaling validation across multiple resolutions.
    
    Checks if physics is resolution-independent:
    - Basin fraction
    - Structure density
    - Spectral clustering rate
    
    If invariant → real physics, not numerical artifact.
    """
    try:
        logger.info(f"Starting complete scaling validation: grids {request.grid_sizes}")
        
        result = complete_scaling_validation(
            grid_sizes=request.grid_sizes,
            simulation_time=request.simulation_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Scaling validation complete. Invariant: {result['scaling_analysis']['is_scale_invariant']}")
        
        return {
            'test_name': 'complete_scaling_validation',
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Scaling validation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/diagnose/basin_decay")
async def diagnose_basin_decay_endpoint(request: BasinDiagnosisRequest):
    """
    Run comprehensive basin decay diagnosis.
    
    Tests:
    1. Energy component tracking - which terms change most
    2. Isolated frequency dynamics - couplings disabled
    3. Gradient-free test - K_omega = 0
    4. Stronger potential test - a_omega x10
    5. Combined parameter fixes
    
    Identifies root cause of basin instability.
    """
    try:
        logger.info("Starting basin decay diagnosis")
        
        result = run_full_basin_diagnosis(seed=request.seed)
        
        logger.info(f"Basin diagnosis complete. Best stability: {result['summary']['best_stability_time']:.1f}s")
        
        return {
            'test_name': 'basin_decay_diagnosis',
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Basin diagnosis error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Diagnosis error: {str(e)}")


# =============================================================================
# Comprehensive Physics Validation Endpoints (NEW)
# =============================================================================

@router.post("/comprehensive/scaling_persistence")
async def comprehensive_scaling_persistence(request: ScalingPersistenceRequest):
    """
    Test if basin stability persists at larger scales.
    
    Measures:
    - Basin lifetime distribution at different grid sizes
    - Number density (basins per unit volume) 
    - Spectral width (σ_ω)
    
    If stability persists across scales → real physics
    If it varies → resolution-dependent artifact
    """
    try:
        logger.info(f"Starting scaling persistence test: grids {request.grid_sizes}")
        
        result = test_scaling_persistence(
            grid_sizes=request.grid_sizes,
            simulation_time=request.simulation_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Scaling persistence test complete. Stability persists: {result.stability_persists}")
        
        # Ensure all numpy types are converted to Python natives
        result_dict = result.to_dict()
        stability_persists = bool(result.stability_persists)
        scaling_exponents = {k: float(v) for k, v in result.scaling_exponents.items()}
        
        return {
            'test_name': 'scaling_persistence',
            'result': result_dict,
            'interpretation': {
                'stability_persists': stability_persists,
                'scaling_exponents': scaling_exponents,
                'is_scale_invariant': bool(abs(scaling_exponents['density_exponent']) < 0.5),
                'note': 'Real physics - scale invariant' if stability_persists else 'May be numerical artifact'
            }
        }
        
    except Exception as e:
        logger.error(f"Scaling persistence test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/comprehensive/entropy_drift")
async def comprehensive_entropy_drift(request: EntropyDriftRequest):
    """
    Test long-time entropy evolution.
    
    Measures S(t) = -Σ P_k log P_k over the frequency distribution.
    
    If entropy plateaus below max → "half-entropy regime" supported
    This would validate the QMRT entropy hierarchy hypothesis.
    """
    try:
        logger.info(f"Starting entropy drift test: {request.grid_size}³, {request.total_time}s")
        
        result = test_entropy_drift(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            n_bins=request.n_bins,
            seed=request.seed
        )
        
        logger.info(f"Entropy drift test complete. Plateaus: {result.entropy_plateaus}, Half-entropy: {result.half_entropy_regime}")
        
        # Convert numpy types to Python natives
        result_dict = result.to_dict()
        
        return {
            'test_name': 'entropy_drift',
            'result': result_dict,
            'interpretation': {
                'entropy_plateaus': bool(result.entropy_plateaus),
                'half_entropy_regime': bool(result.half_entropy_regime),
                'plateau_value': float(result.entropy_plateau),
                'plateau_time': float(result.plateau_time),
                'supports_entropy_hierarchy': bool(result.half_entropy_regime),
                'note': 'Half-entropy regime confirmed - entropy hierarchy valid' if result.half_entropy_regime else 'Full entropy or no plateau'
            }
        }
        
    except Exception as e:
        logger.error(f"Entropy drift test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/comprehensive/basin_tracking")
async def comprehensive_basin_tracking(request: BasinTrackingRequest):
    """
    Track individual basin identities over time.
    
    Measures:
    - Merge probability (two basins become one)
    - Tunneling probability (basin crosses ω=0)
    - Spontaneous decay rate
    - Spectral drift (change in ω over lifetime)
    
    Establishes "particle statistics" for frequency domains.
    """
    try:
        logger.info(f"Starting basin identity tracking: {request.grid_size}³, {request.total_time}s")
        
        result = track_basin_identities(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        logger.info(f"Basin tracking complete. Basins formed: {result.total_basins_formed}, Tunneling: {result.total_tunneling_events}")
        
        # Convert numpy types to Python natives
        result_dict = result.to_dict()
        
        return {
            'test_name': 'basin_identity_tracking',
            'result': result_dict,
            'interpretation': {
                'total_basins_formed': int(result.total_basins_formed),
                'tunneling_events': int(result.total_tunneling_events),
                'merge_events': int(result.total_merges),
                'decay_events': int(result.total_spontaneous_decays),
                'tunneling_probability': float(result.tunneling_probability),
                'merge_probability': float(result.merge_probability),
                'decay_rate': float(result.decay_rate),
                'mean_lifetime': float(result.lifetime_distribution['mean']),
                'supports_antimatter_tunneling': bool(result.total_tunneling_events > 0),
                'note': f"Tunneling observed: {int(result.total_tunneling_events)} events - supports antimatter separation hypothesis" if result.total_tunneling_events > 0 else "No tunneling observed"
            }
        }
        
    except Exception as e:
        logger.error(f"Basin tracking error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/comprehensive/phase_diagram")
async def comprehensive_phase_diagram(request: PhaseDiagramRequest):
    """
    Map the phase diagram: (a_ω / K_ω) vs (g coupling).
    
    Identifies regions of:
    - Unstable: Basins decay quickly
    - Reflective: Basins bounce off each other
    - Tunneling: Basins pass through each other
    - Equilibrium-locked: Basins frozen in place
    
    Creates a "regime chart" for the QMRT theory.
    """
    try:
        logger.info(f"Starting phase diagram mapping: {request.grid_size}³, {request.n_points} points")
        
        result = map_phase_diagram(
            grid_size=request.grid_size,
            test_time=request.test_time,
            dt=request.dt,
            n_points=request.n_points,
            seed=request.seed
        )
        
        # Count regimes
        regime_counts = {}
        for p in result.points:
            regime_counts[p.regime] = regime_counts.get(p.regime, 0) + 1
        
        logger.info(f"Phase diagram complete. Optimal ratio: {result.optimal_parameters['ratio']}")
        
        # Convert numpy types to Python natives
        result_dict = result.to_dict()
        optimal_params = {k: float(v) for k, v in result.optimal_parameters.items()}
        
        return {
            'test_name': 'phase_diagram_mapping',
            'result': result_dict,
            'interpretation': {
                'total_points_tested': int(len(result.points)),
                'regime_distribution': {k: int(v) for k, v in regime_counts.items()},
                'optimal_parameters': optimal_params,
                'best_regime': 'tunneling' if regime_counts.get('tunneling', 0) > 0 else 'equilibrium',
                'note': f"Optimal a_ω/K_ω ratio: {optimal_params['ratio']:.1f}"
            }
        }
        
    except Exception as e:
        logger.error(f"Phase diagram error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/comprehensive/run_all")
async def comprehensive_run_all(request: ComprehensiveValidationRequest):
    """
    Run all comprehensive validation tests.
    
    Tests:
    1. Scaling Persistence - stability at larger grids
    2. Long-time Entropy Drift - half-entropy regime
    3. Basin Identity Tracking - particle statistics
    4. Phase Diagram Mapping - regime boundaries
    
    Returns complete physics validation assessment.
    """
    try:
        logger.info(f"Starting comprehensive validation suite. Quick mode: {request.quick_mode}")
        
        result = run_comprehensive_validation(
            quick_mode=request.quick_mode,
            seed=request.seed
        )
        
        logger.info("Comprehensive validation complete")
        
        # Extract and convert summary values
        summary = result['summary']
        scaling_persists = bool(summary['scaling_persists'])
        entropy_plateaus = bool(summary['entropy_plateaus'])
        half_entropy_regime = bool(summary['half_entropy_regime'])
        tunneling_observed = bool(summary['tunneling_observed'])
        optimal_parameters = {k: float(v) for k, v in summary['optimal_parameters'].items()}
        
        return {
            'test_name': 'comprehensive_validation_suite',
            'result': result,
            'interpretation': {
                'scaling_persists': scaling_persists,
                'entropy_plateaus': entropy_plateaus,
                'half_entropy_regime': half_entropy_regime,
                'tunneling_observed': tunneling_observed,
                'optimal_parameters': optimal_parameters,
                'physics_validity': 'STRONG' if (scaling_persists and entropy_plateaus) else 'PARTIAL',
                'note': 'Comprehensive validation of QMRT frequency-domain physics'
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive validation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
