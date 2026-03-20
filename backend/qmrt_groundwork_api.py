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
                "status": "PENDING",
                "depends_on": [1, 2],
                "description": "Resolution independence of KNOWN structures"
            },
            {
                "step": 4,
                "name": "Entropy Production",
                "endpoint": "/entropy",
                "status": "PENDING",
                "depends_on": [1, 2, 3],
                "description": "Thermodynamics after structure identity known"
            }
        ],
        "current_results": {
            "step_1_eigenmode": "BARRIER STABILITY confirmed - phase separation physics",
            "step_2_interaction": "100% REFLECTION - elastic scattering dominant"
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
