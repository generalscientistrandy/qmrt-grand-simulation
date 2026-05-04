"""
Mesoscopic Substrate API - QMRT-native microstructure simulation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from mesoscopic_substrate import MesoscopicSubstrate
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global substrate instances
substrates: Dict[str, MesoscopicSubstrate] = {}

router = APIRouter(prefix="/mesoscopic", tags=["Mesoscopic Substrate"])


class SubstrateInitRequest(BaseModel):
    """Initialize mesoscopic substrate"""
    name: str
    grid_size: int = 64
    grid_spacing: float = 1.0
    amplitude: float = 0.01
    seed: Optional[int] = None


class EvolutionRequest(BaseModel):
    """Run substrate evolution"""
    steps: int
    dt: float = 0.01
    detect_structures: bool = True


@router.post("/initialize")
async def initialize_substrate(request: SubstrateInitRequest):
    """Initialize QMRT mesoscopic substrate with balanced fluctuations"""
    try:
        substrate = MesoscopicSubstrate(
            grid_size=request.grid_size,
            grid_spacing=request.grid_spacing
        )
        
        substrate.initialize_balanced_fluctuations(
            amplitude=request.amplitude,
            seed=request.seed
        )
        
        substrate_id = f"{request.name}_{id(substrate)}"
        substrates[substrate_id] = substrate
        
        state = substrate.get_substrate_state()
        
        return {
            "substrate_id": substrate_id,
            "name": request.name,
            "grid_size": request.grid_size,
            "initial_state": state,
            "message": f"Mesoscopic substrate initialized: {request.name}"
        }
        
    except Exception as e:
        logging.error(f"Error initializing substrate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{substrate_id}/evolve")
async def evolve_substrate(substrate_id: str, request: EvolutionRequest):
    """Evolve substrate using QMRT equations with stability monitoring"""
    if substrate_id not in substrates:
        raise HTTPException(status_code=404, detail="Substrate not found")
    
    try:
        substrate = substrates[substrate_id]
        
        evolution_metrics = []
        stability_warnings = []
        
        for step in range(request.steps):
            metrics = substrate.evolve_timestep(request.dt)
            
            # Monitor for instability
            if metrics['mean_density'] > 5.0 or metrics['mean_density'] < 0.1:
                stability_warnings.append(f"Step {step}: Density diverging ({metrics['mean_density']:.4f})")
            
            if step % max(1, request.steps // 10) == 0:  # Sample every 10%
                evolution_metrics.append(metrics)
        
        # Always include final metrics
        if evolution_metrics[-1] != metrics:
            evolution_metrics.append(metrics)
        
        # Detect emergent structures
        structures = {}
        if request.detect_structures:
            vortices = substrate.detect_torsion_vortices()
            strain_nodes = substrate.detect_strain_energy_nodes()
            coherence_clusters = substrate.detect_coherence_clusters()
            particle_nodes = substrate.identify_particle_like_nodes()
            
            structures = {
                'torsion_vortices': [v.to_dict() for v in vortices],
                'strain_nodes': [s.to_dict() for s in strain_nodes],
                'coherence_clusters': [c.to_dict() for c in coherence_clusters],
                'particle_nodes': [p.to_dict() for p in particle_nodes]
            }
        
        final_state = substrate.get_substrate_state()
        
        # Compute evolution summary with safe values
        initial_metrics = evolution_metrics[0] if evolution_metrics else {}
        final_metrics = evolution_metrics[-1] if evolution_metrics else {}
        
        return {
            "substrate_id": substrate_id,
            "steps_completed": request.steps,
            "final_time": substrate.time,
            "final_state": final_state,
            "structures": structures,
            "evolution_summary": {
                "initial_density": initial_metrics.get('mean_density', 1.0),
                "final_density": final_metrics.get('mean_density', 1.0),
                "density_change": final_metrics.get('mean_density', 1.0) - initial_metrics.get('mean_density', 1.0),
                "max_strain_reached": max((m.get('max_strain', 0) for m in evolution_metrics), default=0),
                "max_torsion_reached": max((m.get('max_torsion', 0) for m in evolution_metrics), default=0)
            },
            "stability": {
                "stable": len(stability_warnings) == 0,
                "warnings": stability_warnings[:10]  # Limit warnings
            },
            "structure_summary": {
                "vortices": len(structures.get('torsion_vortices', [])),
                "strain_nodes": len(structures.get('strain_nodes', [])),
                "coherence_clusters": len(structures.get('coherence_clusters', [])),
                "particle_nodes": len(structures.get('particle_nodes', []))
            }
        }
        
    except Exception as e:
        logger.error(f"Error evolving substrate: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Evolution error: {str(e)}")


@router.get("/{substrate_id}/state")
async def get_substrate_state(substrate_id: str):
    """Get current substrate state"""
    if substrate_id not in substrates:
        raise HTTPException(status_code=404, detail="Substrate not found")
    
    substrate = substrates[substrate_id]
    return substrate.get_substrate_state()


@router.get("/{substrate_id}/structures")
async def get_structures(substrate_id: str):
    """Get all detected emergent structures"""
    if substrate_id not in substrates:
        raise HTTPException(status_code=404, detail="Substrate not found")
    
    substrate = substrates[substrate_id]
    
    vortices = substrate.detect_torsion_vortices()
    strain_nodes = substrate.detect_strain_energy_nodes()
    coherence_clusters = substrate.detect_coherence_clusters()
    particle_nodes = substrate.identify_particle_like_nodes()
    
    return {
        "substrate_id": substrate_id,
        "time": substrate.time,
        "torsion_vortices": [v.to_dict() for v in vortices],
        "strain_nodes": [s.to_dict() for s in strain_nodes],
        "coherence_clusters": [c.to_dict() for c in coherence_clusters],
        "particle_nodes": [p.to_dict() for p in particle_nodes],
        "summary": {
            "vortex_count": len(vortices),
            "strain_node_count": len(strain_nodes),
            "cluster_count": len(coherence_clusters),
            "particle_node_count": len(particle_nodes),
            "stable_particles": sum(1 for p in particle_nodes if p.structure_type == 'stable')
        }
    }


@router.get("/{substrate_id}/particle-nodes")
async def get_particle_nodes(substrate_id: str):
    """Get emergent particle-like structures"""
    if substrate_id not in substrates:
        raise HTTPException(status_code=404, detail="Substrate not found")
    
    substrate = substrates[substrate_id]
    particle_nodes = substrate.identify_particle_like_nodes()
    
    # Classify by type
    stable = [p for p in particle_nodes if p.structure_type == 'stable']
    proto = [p for p in particle_nodes if p.structure_type == 'proto-particle']
    transient = [p for p in particle_nodes if p.structure_type == 'transient']
    
    return {
        "substrate_id": substrate_id,
        "time": substrate.time,
        "total_nodes": len(particle_nodes),
        "classification": {
            "stable": len(stable),
            "proto_particle": len(proto),
            "transient": len(transient)
        },
        "stable_nodes": [p.to_dict() for p in stable],
        "proto_nodes": [p.to_dict() for p in proto],
        "transient_nodes": [p.to_dict() for p in transient]
    }


@router.get("/list")
async def list_substrates():
    """List all active substrates"""
    return {
        "total_substrates": len(substrates),
        "substrates": [
            {
                "substrate_id": sid,
                "time": substrate.time,
                "particle_nodes": len(substrate.particle_nodes)
            }
            for sid, substrate in substrates.items()
        ]
    }



class StabilityTestRequest(BaseModel):
    """Run a stability test on substrate evolution"""
    grid_size: int = 32
    amplitude: float = 0.1
    total_time: float = 10.0
    dt: float = 0.01
    seed: Optional[int] = 42


class FullSimulationRequest(BaseModel):
    """Run a complete simulation from initialization to structure detection"""
    name: str = "QMRT_Simulation"
    grid_size: int = 48
    amplitude: float = 0.1
    total_time: float = 20.0
    dt: float = 0.01
    seed: Optional[int] = None


@router.post("/run")
async def run_mesoscopic_simulation(request: FullSimulationRequest):
    """
    Run a complete QMRT mesoscopic simulation from initialization to structure detection.
    
    This is a convenience endpoint that:
    1. Initializes a substrate with balanced fluctuations
    2. Evolves it for the specified time
    3. Detects emergent structures
    4. Returns comprehensive results
    """
    try:
        # Initialize substrate
        substrate = MesoscopicSubstrate(
            grid_size=request.grid_size,
            grid_spacing=1.0
        )
        
        substrate.initialize_balanced_fluctuations(
            amplitude=request.amplitude,
            seed=request.seed
        )
        
        substrate_id = f"{request.name}_{id(substrate)}"
        substrates[substrate_id] = substrate
        
        initial_state = substrate.get_substrate_state()
        
        # Calculate number of steps
        steps = int(request.total_time / request.dt)
        
        # Evolution with periodic sampling
        evolution_samples = []
        sample_interval = max(1, steps // 20)  # 20 samples
        
        logger.info(f"Starting mesoscopic simulation: {steps} steps, dt={request.dt}")
        
        for step in range(steps):
            metrics = substrate.evolve_timestep(request.dt)
            
            if step % sample_interval == 0:
                # Also detect structures at sample points
                substrate.detect_torsion_vortices()
                substrate.detect_strain_energy_nodes()
                substrate.detect_coherence_clusters()
                substrate.identify_particle_like_nodes()
                
                sample = {
                    'step': step,
                    'time': metrics['time'],
                    'mean_density': metrics['mean_density'],
                    'density_variance': metrics['density_variance'],
                    'max_torsion': metrics.get('max_torsion', 0),
                    'max_strain': metrics['max_strain'],
                    'vortices': len(substrate.torsion_vortices),
                    'strain_nodes': len(substrate.strain_nodes),
                    'particle_nodes': len(substrate.particle_nodes)
                }
                evolution_samples.append(sample)
        
        # Final structure detection
        vortices = substrate.detect_torsion_vortices()
        strain_nodes = substrate.detect_strain_energy_nodes()
        coherence_clusters = substrate.detect_coherence_clusters()
        particle_nodes = substrate.identify_particle_like_nodes()
        
        final_state = substrate.get_substrate_state()
        
        logger.info(f"Simulation complete: {len(vortices)} vortices, {len(strain_nodes)} strain nodes, {len(particle_nodes)} particles")
        
        return {
            "substrate_id": substrate_id,
            "simulation_params": {
                "grid_size": request.grid_size,
                "amplitude": request.amplitude,
                "total_time": request.total_time,
                "dt": request.dt,
                "total_steps": steps
            },
            "initial_state": initial_state,
            "final_state": final_state,
            "evolution_samples": evolution_samples,
            "emergent_structures": {
                "torsion_vortices": {
                    "count": len(vortices),
                    "items": [v.to_dict() for v in vortices[:20]]  # Limit to 20
                },
                "strain_nodes": {
                    "count": len(strain_nodes),
                    "items": [s.to_dict() for s in strain_nodes[:20]]
                },
                "coherence_clusters": {
                    "count": len(coherence_clusters),
                    "items": [c.to_dict() for c in coherence_clusters[:20]]
                },
                "particle_nodes": {
                    "count": len(particle_nodes),
                    "stable": sum(1 for p in particle_nodes if p.structure_type == 'stable'),
                    "proto_particle": sum(1 for p in particle_nodes if p.structure_type == 'proto-particle'),
                    "transient": sum(1 for p in particle_nodes if p.structure_type == 'transient'),
                    "items": [p.to_dict() for p in particle_nodes[:20]]
                }
            },
            "stability_analysis": {
                "stable": final_state['mean_density'] > 0.5 and final_state['mean_density'] < 2.0,
                "density_preserved": abs(final_state['mean_density'] - 1.0) < 0.1,
                "energy_total": final_state.get('energy_total', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in mesoscopic simulation: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/stability-test")
async def run_stability_test(request: StabilityTestRequest):
    """
    Run a stability test on the mesoscopic substrate evolution.
    
    This tests whether the numerical integration remains stable over time.
    Returns detailed metrics at each step for analysis.
    """
    try:
        substrate = MesoscopicSubstrate(
            grid_size=request.grid_size,
            grid_spacing=1.0
        )
        
        substrate.initialize_balanced_fluctuations(
            amplitude=request.amplitude,
            seed=request.seed
        )
        
        steps = int(request.total_time / request.dt)
        
        # Track detailed metrics
        density_history = []
        variance_history = []
        energy_history = []
        stability_flags = []
        
        initial_energy = substrate._compute_total_energy()
        
        for step in range(steps):
            metrics = substrate.evolve_timestep(request.dt)
            
            # Sample every 10 steps
            if step % 10 == 0:
                density_history.append(metrics['mean_density'])
                variance_history.append(metrics['density_variance'])
                energy_history.append(substrate._compute_total_energy())
                
                # Check stability conditions
                is_stable = (
                    0.1 < metrics['mean_density'] < 10.0 and
                    metrics['density_variance'] < 100.0 and
                    not any(map(lambda x: x != x, [metrics['mean_density'], metrics['density_variance']]))  # NaN check
                )
                stability_flags.append(is_stable)
        
        final_state = substrate.get_substrate_state()
        final_energy = substrate._compute_total_energy()
        
        # Analyze stability
        all_stable = all(stability_flags)
        density_drift = abs(final_state['mean_density'] - 1.0)
        energy_conservation = abs(final_energy - initial_energy) / max(initial_energy, 1e-10)
        
        return {
            "test_params": {
                "grid_size": request.grid_size,
                "amplitude": request.amplitude,
                "total_time": request.total_time,
                "dt": request.dt,
                "steps": steps
            },
            "stability_result": {
                "overall_stable": all_stable,
                "density_preserved": density_drift < 0.5,
                "density_drift": density_drift,
                "energy_conservation_ratio": energy_conservation,
                "unstable_steps": sum(1 for s in stability_flags if not s)
            },
            "final_state": final_state,
            "history_samples": {
                "density": density_history[-10:],  # Last 10 samples
                "variance": variance_history[-10:],
                "energy": energy_history[-10:]
            },
            "diagnosis": {
                "message": "Simulation is stable" if all_stable else "Instability detected",
                "recommendations": []
            }
        }
        
    except Exception as e:
        logger.error(f"Error in stability test: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Stability test error: {str(e)}")


@router.delete("/{substrate_id}")
async def delete_substrate(substrate_id: str):
    """Delete a substrate instance to free memory"""
    if substrate_id not in substrates:
        raise HTTPException(status_code=404, detail="Substrate not found")
    
    del substrates[substrate_id]
    return {"message": f"Substrate {substrate_id} deleted", "remaining": len(substrates)}
