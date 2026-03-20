"""
QMRT Groundwork Validation API

API endpoints for rigorous physics validation following proper scientific order:
1. Eigenmode stability (FIRST - foundational)
2. Interaction classification (SECOND - scattering law)
3. Scaling laws (THIRD - only after 1,2)
4. Entropy production (FOURTH - only after 1,2,3)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import traceback

from qmrt_validation.eigenmode_test import (
    run_eigenmode_stability_test,
    run_comprehensive_stability_test,
    run_multi_perturbation_test
)

from qmrt_validation.interaction_test import (
    run_interaction_classification,
    run_single_collision_test
)

from qmrt_validation.scaling_test import (
    run_scaling_convergence_test,
    run_scaling_at_resolution
)

from qmrt_validation.entropy_test import (
    run_entropy_production_test
)

from qmrt_validation.phase_diagram import (
    run_phase_diagram_refinement,
    run_hysteresis_scan,
    run_long_time_plateau_test,
    run_interaction_regime_map
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qmrt_groundwork", tags=["QMRT Groundwork Validation"])


# =============================================================================
# Request Models
# =============================================================================

class EigenmodeTestRequest(BaseModel):
    """Request for eigenmode stability test"""
    grid_size: int = Field(default=20, ge=10, le=40)
    total_time: float = Field(default=30.0, ge=10.0, le=100.0)
    dt: float = Field(default=0.01, ge=0.005, le=0.05)
    basin_type: str = Field(default='high', description="'high' or 'low' frequency basin")
    perturbation_type: str = Field(default='gaussian_noise', 
                                   description="'gaussian_noise', 'localized_bump', or 'spectral_mode'")
    perturbation_magnitude: float = Field(default=0.01, ge=0.001, le=0.1)
    seed: Optional[int] = Field(default=42)


class ComprehensiveStabilityRequest(BaseModel):
    """Request for comprehensive stability test (local + global)"""
    grid_size: int = Field(default=20, ge=12, le=40)
    stabilization_time: float = Field(default=10.0, ge=5.0, le=30.0)
    perturbation_time: float = Field(default=20.0, ge=10.0, le=60.0)
    dt: float = Field(default=0.01, ge=0.005, le=0.05)
    perturbation_magnitude: float = Field(default=0.05, ge=0.01, le=0.2)
    seed: Optional[int] = Field(default=42)


class MultiPerturbationRequest(BaseModel):
    """Request for multi-perturbation robustness test"""
    grid_size: int = Field(default=16, ge=10, le=32)
    total_time: float = Field(default=20.0, ge=10.0, le=50.0)
    dt: float = Field(default=0.02, ge=0.005, le=0.05)
    seed: Optional[int] = Field(default=42)


class InteractionClassificationRequest(BaseModel):
    """Request for interaction classification test (Step 2)"""
    grid_size: int = Field(default=14, ge=10, le=24)
    collision_time: float = Field(default=10.0, ge=5.0, le=30.0)
    dt: float = Field(default=0.02, ge=0.01, le=0.05)
    n_trials_per_type: int = Field(default=3, ge=1, le=10)
    seed: Optional[int] = Field(default=42)


class ScalingConvergenceRequest(BaseModel):
    """Request for scaling convergence test (Step 3)"""
    grid_sizes: List[int] = Field(default=[12, 16, 20, 24], description="Grid sizes to test")
    stabilization_time: float = Field(default=6.0, ge=3.0, le=20.0)
    measurement_time: float = Field(default=6.0, ge=3.0, le=20.0)
    dt: float = Field(default=0.02, ge=0.01, le=0.05)
    convergence_threshold: float = Field(default=0.15, ge=0.05, le=0.3)
    seed: Optional[int] = Field(default=42)


class EntropyProductionRequest(BaseModel):
    """Request for entropy production test (Step 4)"""
    grid_size: int = Field(default=14, ge=10, le=24)
    total_time: float = Field(default=20.0, ge=10.0, le=60.0)
    dt: float = Field(default=0.02, ge=0.01, le=0.05)
    n_scan_points: int = Field(default=4, ge=3, le=8)
    seed: Optional[int] = Field(default=42)


class PhaseDiagramRequest(BaseModel):
    """Request for phase diagram refinement"""
    grid_size: int = Field(default=14, ge=10, le=20)
    seed: Optional[int] = Field(default=42)


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/")
async def groundwork_info():
    """
    Information about the groundwork validation suite.
    """
    return {
        "title": "QMRT Groundwork Validation Suite",
        "purpose": "Rigorous physics validation with proper scientific order",
        "validation_order": [
            {
                "step": 1,
                "name": "Eigenmode Stability",
                "endpoint": "/eigenmode",
                "status": "IMPLEMENTED",
                "must_pass": True,
                "description": "Prove basin = true attractor OR barrier-stable structure"
            },
            {
                "step": 2,
                "name": "Interaction Classification",
                "endpoint": "/interaction",
                "status": "IMPLEMENTED",
                "depends_on": [1],
                "description": "Basin collision scattering law"
            },
            {
                "step": 3,
                "name": "Scaling Laws",
                "endpoint": "/scaling",
                "status": "IMPLEMENTED",
                "depends_on": [1, 2],
                "description": "Resolution independence of KNOWN structures"
            },
            {
                "step": 4,
                "name": "Entropy Production",
                "endpoint": "/entropy",
                "status": "IMPLEMENTED",
                "depends_on": [1, 2, 3],
                "description": "Thermodynamics after structure identity known"
            }
        ],
        "current_results": {
            "step_1_eigenmode": "BARRIER STABILITY confirmed - phase separation physics",
            "step_2_interaction": "100% REFLECTION - elastic scattering dominant",
            "step_3_scaling": "CONTINUUM LIMIT EXISTS - 75% confidence, multi-frequency Landau system",
            "step_4_entropy": "PHASE BOUNDARY at a_ω=0.75, half-entropy regime 0.54-0.69",
            "phase_diagram": "HYSTERESIS confirmed (~0.14 width), REFLECTION UNIVERSAL, plateau at S/S_max≈0.73"
        }
    }


@router.post("/eigenmode")
async def run_eigenmode_test(request: EigenmodeTestRequest):
    """
    Step 1: Eigenmode Stability Test (FOUNDATIONAL)
    
    Proves whether basin = true attractor OR identifies other stability type.
    
    Physics:
        δψ(t) ~ e^(λt)
        Re(λ) < 0 → STABLE ATTRACTOR
        Re(λ) ≈ 0 → MARGINAL SOLITON  
        Re(λ) > 0 → NOT ATTRACTOR (check barrier stability)
    
    This test MUST be run first. All other validation depends on this.
    """
    try:
        logger.info(f"Starting eigenmode test: {request.grid_size}³, {request.basin_type} basin")
        
        result = run_eigenmode_stability_test(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            basin_type=request.basin_type,
            perturbation_type=request.perturbation_type,
            perturbation_magnitude=request.perturbation_magnitude,
            seed=request.seed
        )
        
        result_dict = result.to_dict()
        
        return {
            'test_name': 'eigenmode_stability',
            'validation_step': 1,
            'result': result_dict,
            'next_step': 'If stability proven, proceed to interaction classification'
        }
        
    except Exception as e:
        logger.error(f"Eigenmode test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/comprehensive_stability")
async def run_comprehensive_test(request: ComprehensiveStabilityRequest):
    """
    Step 1 (Enhanced): Comprehensive Stability Test
    
    Distinguishes between:
    - ATTRACTOR stability: Local perturbations decay
    - BARRIER stability: Local perturbations grow but basin occupation preserved
    - UNSTABLE: Both local and global instability
    
    This is the RECOMMENDED test for QMRT basins, as they exhibit barrier stability.
    """
    try:
        logger.info(f"Starting comprehensive stability test: {request.grid_size}³")
        
        result = run_comprehensive_stability_test(
            grid_size=request.grid_size,
            stabilization_time=request.stabilization_time,
            perturbation_time=request.perturbation_time,
            dt=request.dt,
            perturbation_magnitude=request.perturbation_magnitude,
            seed=request.seed
        )
        
        result_dict = result.to_dict()
        
        # Determine if we can proceed
        can_proceed = result.stability_type in ['attractor', 'barrier', 'marginal']
        
        return {
            'test_name': 'comprehensive_stability',
            'validation_step': 1,
            'result': result_dict,
            'can_proceed_to_step_2': can_proceed,
            'scientific_interpretation': {
                'stability_type': result.stability_type,
                'physics_type': 'soliton/attractor' if result.stability_type == 'attractor' else 'phase separation',
                'basin_preservation': f"{result.basin_preservation_ratio:.1%}",
                'local_growth': f"{result.local_growth_factor:.2f}x"
            },
            'next_step': 'Proceed to interaction classification (Step 2)' if can_proceed else 'Basin stability insufficient - investigate parameters'
        }
        
    except Exception as e:
        logger.error(f"Comprehensive test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/multi_perturbation")
async def run_multi_pert_test(request: MultiPerturbationRequest):
    """
    Step 1 (Robustness): Multi-Perturbation Test
    
    Runs eigenmode test with multiple perturbation types for higher confidence.
    Tests: gaussian_noise, localized_bump, spectral_mode
    Basins: high and low frequency
    
    Provides aggregate classification with confidence score.
    """
    try:
        logger.info(f"Starting multi-perturbation test: {request.grid_size}³")
        
        result = run_multi_perturbation_test(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            seed=request.seed
        )
        
        return {
            'test_name': 'multi_perturbation_robustness',
            'validation_step': 1,
            'result': result,
            'next_step': 'Use comprehensive_stability test for barrier vs attractor distinction'
        }
        
    except Exception as e:
        logger.error(f"Multi-perturbation test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


# =============================================================================
# Step 2: Interaction Classification
# =============================================================================

@router.post("/interaction")
async def run_interaction_test(request: InteractionClassificationRequest):
    """
    Step 2: Interaction Classification (SCATTERING LAW)
    
    PREREQUISITE: Step 1 (eigenmode stability) must show stable/barrier-stable basins.
    
    Performs controlled collision experiments:
    - Same-frequency basins (ω₁ ≈ ω₂ > 0)
    - Near-frequency basins (|ω₁ - ω₂| small)
    - Cross-frequency basins (ω₁ > 0, ω₂ < 0) - matter/antimatter analog
    
    Outputs:
    - Tunneling probability P_tunnel
    - Merge probability P_merge
    - Reflection probability P_reflect
    - Annihilation probability P_annihilate (cross-frequency only)
    
    This establishes the QMRT SCATTERING LAW.
    """
    try:
        logger.info(f"Starting interaction classification: {request.grid_size}³, {request.n_trials_per_type} trials")
        
        result = run_interaction_classification(
            grid_size=request.grid_size,
            collision_time=request.collision_time,
            dt=request.dt,
            n_trials_per_type=request.n_trials_per_type,
            seed=request.seed
        )
        
        result_dict = result.to_dict()
        
        # Determine dominant behavior
        sm = result_dict['scattering_matrix']
        
        return {
            'test_name': 'interaction_classification',
            'validation_step': 2,
            'result': result_dict,
            'scattering_law': {
                'same_frequency': f"T={sm['same_frequency']['P_tunnel']:.0%} M={sm['same_frequency']['P_merge']:.0%} R={sm['same_frequency']['P_reflect']:.0%}",
                'near_frequency': f"T={sm['near_frequency']['P_tunnel']:.0%} M={sm['near_frequency']['P_merge']:.0%} R={sm['near_frequency']['P_reflect']:.0%}",
                'cross_frequency': f"T={sm['cross_frequency']['P_tunnel']:.0%} A={sm['cross_frequency']['P_annihilate']:.0%} R={sm['cross_frequency']['P_reflect']:.0%}"
            },
            'physics_interpretation': result_dict['interpretation'],
            'next_step': 'Proceed to scaling law extraction (Step 3) - now testing resolution independence of KNOWN structures'
        }
        
    except Exception as e:
        logger.error(f"Interaction test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


# =============================================================================
# Step 3: Scaling Convergence
# =============================================================================

@router.post("/scaling")
async def run_scaling_test(request: ScalingConvergenceRequest):
    """
    Step 3: Scaling Convergence Test (CONTINUUM LIMIT)
    
    PREREQUISITE: Steps 1 and 2 must confirm stable/barrier-stable basins with defined scattering.
    
    Tests whether the simulation has a well-defined continuum limit by measuring
    convergence of key metrics as grid resolution increases:
    
    1. Domain wall thickness / grid spacing → should converge to physical thickness
    2. Basin energy density → should be resolution-independent
    3. Reflection coefficient → scattering law should be physical
    4. Spectral peak sharpness (Q) → frequency structure should converge
    
    If 3+ metrics converge:
        → CONTINUUM LIMIT EXISTS
        → This is a multi-frequency Landau free-energy system
        → F = Σᵢ aᵢ|ψᵢ|² + bᵢ|ψᵢ|⁴ + κ|∇ψᵢ|² + γ|ψᵢ - ψⱼ|²
    
    This naturally creates: basin locking, reflection scattering, phase tension,
    multi-domain universe segmentation.
    """
    try:
        logger.info(f"Starting scaling convergence test: grids {request.grid_sizes}")
        
        result = run_scaling_convergence_test(
            grid_sizes=request.grid_sizes,
            stabilization_time=request.stabilization_time,
            measurement_time=request.measurement_time,
            dt=request.dt,
            seed=request.seed,
            convergence_threshold=request.convergence_threshold
        )
        
        result_dict = result.to_dict()
        conv = result_dict['convergence_analysis']
        
        return {
            'test_name': 'scaling_convergence',
            'validation_step': 3,
            'result': result_dict,
            'convergence_summary': {
                'domain_wall_thickness': f"{'✅' if conv['domain_wall_thickness']['converges'] else '❌'} → {conv['domain_wall_thickness']['extrapolated_value']:.4f}",
                'energy_density': f"{'✅' if conv['energy_density']['converges'] else '❌'} → {conv['energy_density']['extrapolated_value']:.4f}",
                'reflection_coefficient': f"{'✅' if conv['reflection_coefficient']['converges'] else '❌'} → {conv['reflection_coefficient']['extrapolated_value']:.4f}",
                'spectral_sharpness': f"{'✅' if conv['spectral_sharpness']['converges'] else '❌'} → {conv['spectral_sharpness']['extrapolated_value']:.4f}"
            },
            'verdict': result_dict['verdict'],
            'physics_interpretation': 'Multi-frequency Landau free-energy system with real physical domain walls' if result.continuum_limit_exists else 'Need more resolution or parameter tuning',
            'next_step': 'Proceed to entropy production (Step 4) - thermodynamics of KNOWN continuum structures' if result.continuum_limit_exists else 'Investigate non-converging metrics'
        }
        
    except Exception as e:
        logger.error(f"Scaling test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


# =============================================================================
# Step 4: Entropy Production
# =============================================================================

@router.post("/entropy")
async def run_entropy_test(request: EntropyProductionRequest):
    """
    Step 4: Entropy Production Test (FINAL GROUNDWORK VALIDATION)
    
    PREREQUISITE: Steps 1-3 must confirm stable basins, scattering law, and continuum limit.
    
    Measures entropy production rate dS/dt across parameter space:
    1. dS/dt vs coupling strength (g_ωφ)
    2. dS/dt vs gradient coefficient (K_ω)
    3. dS/dt vs potential depth (a_ω)
    
    Physics:
        S(t) = -Σ P_k log P_k (frequency distribution entropy)
        
    Outcomes:
    - If plateau robust → ORDERED METASTABLE STATE (half-entropy regime)
    - If phase transition found → PHASE BOUNDARY IDENTIFIED
    - Validates QMRT entropy hierarchy
    
    This completes the groundwork validation suite.
    """
    try:
        logger.info(f"Starting entropy production test: {request.grid_size}³, {request.n_scan_points} points")
        
        result = run_entropy_production_test(
            grid_size=request.grid_size,
            total_time=request.total_time,
            dt=request.dt,
            n_scan_points=request.n_scan_points,
            seed=request.seed
        )
        
        result_dict = result.to_dict()
        
        return {
            'test_name': 'entropy_production',
            'validation_step': 4,
            'result': result_dict,
            'entropy_summary': {
                'half_entropy_observed': result.half_entropy_observed,
                'half_entropy_range': list(result.half_entropy_range) if result.half_entropy_observed else None,
                'plateau_robust': result.plateau_robust,
                'phase_boundary_identified': result.phase_boundary_identified
            },
            'phase_transitions': {
                'coupling_g_omega_phi': result.coupling_transition_point,
                'gradient_K_omega': result.gradient_transition_point,
                'potential_a_omega': result.potential_transition_point
            },
            'physics_interpretation': result_dict['interpretation'],
            'groundwork_complete': result.phase_boundary_identified or result.half_entropy_observed,
            'next_step': 'GROUNDWORK VALIDATION COMPLETE - Ready for quark confinement analogies and phase-domain universe models' if (result.phase_boundary_identified or result.half_entropy_observed) else 'Need broader parameter scan or longer simulation time'
        }
        
    except Exception as e:
        logger.error(f"Entropy test error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


# =============================================================================
# Phase Diagram Refinement
# =============================================================================

@router.post("/phase_diagram")
async def run_phase_diagram_test(request: PhaseDiagramRequest):
    """
    Phase Diagram Refinement (Final Tightening Pass)
    
    Tightens the substrate layer before quark-like analogies:
    
    1. HYSTERESIS SCAN around a_ω ≈ 0.75 phase boundary
       - Scan a_ω in both directions
       - Detect first-order vs continuous transition
       
    2. FINITE-SIZE SCALING near phase boundary
       - Test multiple grid sizes
       - Estimate critical exponents
       
    3. LONG-TIME PLATEAU test
       - Confirm entropy plateau survives 40+ seconds
       - Measure drift rate
       
    4. INTERACTION REGIME MAP
       - Test reflection vs tunneling vs merging across (a_ω, K_ω) space
       - Identify if any tunneling/merge windows exist
    
    Establishes the REAL PHASE DIAGRAM for QMRT.
    """
    try:
        logger.info(f"Starting phase diagram refinement: {request.grid_size}³")
        
        result = run_phase_diagram_refinement(
            grid_size=request.grid_size,
            seed=request.seed
        )
        
        result_dict = result.to_dict()
        
        return {
            'test_name': 'phase_diagram_refinement',
            'result': result_dict,
            'key_findings': {
                'hysteresis': {
                    'width': result.hysteresis_width,
                    'boundary_range': [result.phase_boundary_lower, result.phase_boundary_upper],
                    'transition_type': 'first-order' if result.hysteresis_width > 0.05 else 'continuous'
                },
                'plateau': {
                    'stable': result.plateau_stable,
                    'drift_rate': result.plateau_drift_rate
                },
                'interaction': {
                    'reflection_universal': not result.tunneling_window_exists and not result.merge_window_exists,
                    'tunneling_window': result.tunneling_window_range if result.tunneling_window_exists else None,
                    'merge_window': result.merge_window_exists
                }
            },
            'summary': result_dict['summary'],
            'ready_for_quark_analogies': result.plateau_stable or result.plateau_drift_rate < 0.005
        }
        
    except Exception as e:
        logger.error(f"Phase diagram error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")
