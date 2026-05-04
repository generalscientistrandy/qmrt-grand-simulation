from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from models import (
    World, WorldCreateRequest, WorldResponse, WorldListResponse,
    SubstrateMetrics, WorldParameters,
    CosmologicalSimulation, CosmologicalSimulationRequest, CosmologicalSimulationResponse,
    SimulationMode
)
from world_generator_v2 import WorldGenerator
from cosmological_simulator import CosmologicalSimulator


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="QMRT Simulation Universe", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# World generator instance
world_gen = WorldGenerator()


@api_router.get("/")
async def root():
    return {
        "message": "QMRT Simulation Universe API",
        "version": "2.0.0",
        "substrate": "Quark Medium Relativity Theory",
        "modes": {
            "mode_1": "Full Cosmological Simulation (primordial → structure formation)",
            "mode_2": "Gameplay Universe Generation (seeded or direct)"
        }
    }


@api_router.post("/worlds", response_model=WorldResponse)
async def create_world(request: WorldCreateRequest):
    """
    Generate a new world using QMRT substrate physics.
    
    Death-world levels:
    - 1-3: Sanctuary worlds (low difficulty)
    - 4-6: Garden/Frontier worlds (moderate)
    - 7-9: Contested/Harsh worlds (challenging)
    - 10: Earth-class world (reference standard)
    - 11-12: Death worlds (extreme)
    - 13-14: Extreme death worlds (apocalyptic)
    - 15: Apocalypse world (maximum chaos)
    """
    try:
        # Generate world using physics engine
        world_data = world_gen.generate_world(
            death_world_level=request.death_world_level,
            seed=request.seed,
            evolution_steps=request.evolution_steps


@api_router.post("/cosmological-simulations", response_model=CosmologicalSimulationResponse)
async def run_cosmological_simulation(request: CosmologicalSimulationRequest):
    """
    MODE 1: Run full cosmological simulation from primordial state to structure formation.
    
    This evolves the universe through:
    1. Primordial quantum fluctuations
    2. Inflationary expansion
    3. Radiation-dominated era
    4. Matter-dominated era
    5. Large-scale structure formation
    
    The resulting structure seeds can be used to generate Mode 2 worlds.
    """
    try:
        # Create cosmological simulator
        simulator = CosmologicalSimulator(
            grid_size=request.grid_size,
            hubble_parameter=0.07
        )
        
        # Run full simulation
        result = simulator.run_full_simulation(seed=request.seed)
        
        # Create database entry
        cosmo_sim = CosmologicalSimulation(
            name=request.name,
            seed=request.seed,
            final_epoch=result['final_epoch'],
            cosmic_time=result['cosmic_time'],
            scale_factor=result['scale_factor'],
            num_structure_seeds=result['num_structure_seeds']
        )
        
        # Save to database
        sim_dict = cosmo_sim.model_dump()
        sim_dict['created_at'] = sim_dict['created_at'].isoformat()
        sim_dict['structure_seeds'] = result['structure_seeds']
        sim_dict['final_metrics'] = result['final_metrics']
        
        await db.cosmological_simulations.insert_one(sim_dict)
        
        return CosmologicalSimulationResponse(
            id=cosmo_sim.id,
            name=cosmo_sim.name,
            seed=cosmo_sim.seed,
            final_epoch=cosmo_sim.final_epoch,
            cosmic_time=cosmo_sim.cosmic_time,
            scale_factor=cosmo_sim.scale_factor,
            num_structure_seeds=cosmo_sim.num_structure_seeds,
            structure_seeds=result['structure_seeds'],
            snapshots=result['snapshots'],
            created_at=sim_dict['created_at']
        )
        
    except Exception as e:
        logging.error(f"Error running cosmological simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@api_router.get("/cosmological-simulations", response_model=List[CosmologicalSimulationResponse])
async def list_cosmological_simulations(limit: int = 50, skip: int = 0):
    """List all cosmological simulations"""
    try:
        sims_cursor = db.cosmological_simulations.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        sims = await sims_cursor.to_list(length=limit)
        
        return [
            CosmologicalSimulationResponse(
                id=s['id'],
                name=s['name'],
                seed=s.get('seed'),
                final_epoch=s['final_epoch'],
                cosmic_time=s['cosmic_time'],
                scale_factor=s['scale_factor'],
                num_structure_seeds=s['num_structure_seeds'],
                structure_seeds=s.get('structure_seeds', []),
                snapshots=0,  # Not stored in list view
                created_at=s['created_at']
            )
            for s in sims
        ]
    except Exception as e:
        logging.error(f"Error listing cosmological simulations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/cosmological-simulations/{sim_id}", response_model=CosmologicalSimulationResponse)
async def get_cosmological_simulation(sim_id: str):
    """Get specific cosmological simulation by ID"""
    sim = await db.cosmological_simulations.find_one({"id": sim_id}, {"_id": 0})
    
    if not sim:
        raise HTTPException(status_code=404, detail="Cosmological simulation not found")
    
    return CosmologicalSimulationResponse(
        id=sim['id'],
        name=sim['name'],
        seed=sim.get('seed'),
        final_epoch=sim['final_epoch'],
        cosmic_time=sim['cosmic_time'],
        scale_factor=sim['scale_factor'],
        num_structure_seeds=sim['num_structure_seeds'],
        structure_seeds=sim.get('structure_seeds', []),
        snapshots=0,
        created_at=sim['created_at']
    )


@api_router.delete("/cosmological-simulations/{sim_id}")
async def delete_cosmological_simulation(sim_id: str):
    """Delete a cosmological simulation"""
    result = await db.cosmological_simulations.delete_one({"id": sim_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cosmological simulation not found")
    
    return {"message": "Cosmological simulation deleted successfully", "id": sim_id}


        )
        
        # Create world model
        world = World(
            name=request.name,
            death_world_level=world_data['death_world_level'],
            seed=world_data['seed'],
            classification=world_data['classification'],
            substrate_metrics=SubstrateMetrics(**world_data['substrate_metrics']),
            world_parameters=WorldParameters(**{k: v for k, v in world_data.items() 
                                                if k not in ['death_world_level', 'seed', 
                                                           'substrate_metrics', 'classification']}),
            apex_qualified=(request.death_world_level >= 10)
        )
        
        # Save to database
        world_dict = world.model_dump()
        world_dict['created_at'] = world_dict['created_at'].isoformat()
        world_dict['last_updated'] = world_dict['last_updated'].isoformat()
        world_dict['substrate_metrics'] = world_dict['substrate_metrics']
        world_dict['world_parameters'] = world_dict['world_parameters']
        
        await db.worlds.insert_one(world_dict)
        
        # Return response
        return WorldResponse(
            id=world.id,
            name=world.name,
            death_world_level=world.death_world_level,
            seed=world.seed,
            classification=world.classification,
            world_parameters=world.world_parameters.model_dump(),
            substrate_metrics=world.substrate_metrics.model_dump(),
            created_at=world_dict['created_at'],
            apex_qualified=world.apex_qualified
        )
        
    except Exception as e:
        logging.error(f"Error generating world: {str(e)}")
        raise HTTPException(status_code=500, detail=f"World generation failed: {str(e)}")


@api_router.get("/worlds", response_model=WorldListResponse)
async def list_worlds(limit: int = 50, skip: int = 0):
    """List all generated worlds"""
    try:
        worlds_cursor = db.worlds.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        worlds = await worlds_cursor.to_list(length=limit)
        total = await db.worlds.count_documents({})
        
        world_responses = [
            WorldResponse(
                id=w['id'],
                name=w['name'],
                death_world_level=w['death_world_level'],
                seed=w.get('seed'),
                classification=w['classification'],
                world_parameters=w['world_parameters'],
                substrate_metrics=w['substrate_metrics'],
                created_at=w['created_at'],
                apex_qualified=w.get('apex_qualified', False)
            )
            for w in worlds
        ]
        
        return WorldListResponse(worlds=world_responses, total=total)
        
    except Exception as e:
        logging.error(f"Error listing worlds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/worlds/{world_id}", response_model=WorldResponse)
async def get_world(world_id: str):
    """Get specific world by ID"""
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    return WorldResponse(
        id=world['id'],
        name=world['name'],
        death_world_level=world['death_world_level'],
        seed=world.get('seed'),
        classification=world['classification'],
        world_parameters=world['world_parameters'],
        substrate_metrics=world['substrate_metrics'],
        created_at=world['created_at'],
        apex_qualified=world.get('apex_qualified', False)
    )


@api_router.delete("/worlds/{world_id}")
async def delete_world(world_id: str):
    """Delete a world"""
    result = await db.worlds.delete_one({"id": world_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="World not found")
    
    return {"message": "World deleted successfully", "id": world_id}


@api_router.get("/substrate/info")
async def substrate_info():
    """Get information about the QMRT substrate physics engine"""
    return {
        "theory": "Quark Medium Relativity Theory (QMRT)",
        "substrate_properties": [
            {"name": "ρΞ (Density)", "description": "Determines inertia and gravitational behavior"},
            {"name": "TΞ (Tension)", "description": "Governs wave speed and electromagnetic analogs"},
            {"name": "τΞ (Torsion)", "description": "Rotational degrees of freedom, spin, magnetic alignment"},
            {"name": "ΦΞ (Coherence Phase)", "description": "Interference, quantum phenomena, biological viability"}
        ],
        "death_world_scaling": {
            "min": 1,
            "max": 15,
            "earth_reference": 10,
            "apex_threshold": 10
        },
        "world_generation": "Worlds emerge from coupled wave equations evolving substrate properties",
        "future_systems": [
            "Ecological simulation (Phase B)",
            "Evolutionary dynamics (Phase B)",
            "Apex qualification tracking (Phase C)",
            "Hidden lineage system (Phase C)",
            "Civilization emergence (Phase C)"
        ]
    }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
