from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone

from models import (
    World, WorldCreateRequest, WorldResponse, WorldListResponse,
    SubstrateMetrics, WorldParameters,
    CosmologicalSimulation, CosmologicalSimulationRequest, CosmologicalSimulationResponse,
    SimulationMode,
    LineageRecord, LineageCreateRequest, LineageUpdateRequest,
    UniverseSimulationResponse
)
from world_generator_v2 import WorldGenerator
from ecological_engine import EcologicalEngine, PredatorTier
from lineage_system import LineageTracker

from cosmological_simulator import CosmologicalSimulator
from universe_simulator import UniverseSimulator
from engine_api import router as engine_router
from mesoscopic_api import router as mesoscopic_router


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="QMRT Simulation Universe", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# World generator instance
world_gen = WorldGenerator()

# Lineage tracker instance
lineage_tracker = LineageTracker()


@api_router.get("/")
async def root():
    return {
        "message": "QMRT Simulation Universe API",
        "version": "2.0.0",
        "substrate": "Quark Medium Relativity Theory",
        "modes": {
            "mode_1": "Full Cosmological Simulation (primordial \u2192 structure formation)",
            "mode_2": "Gameplay Universe Generation (seeded or direct)"
        }
    }


@api_router.get("/simulation-modes", response_model=List[SimulationMode])
async def get_simulation_modes():
    """Get information about the two simulation modes"""
    return [
        SimulationMode(
            mode="mode_1",
            name="Full Cosmological Simulation",
            description="Evolves universe from primordial quantum fluctuations through inflation, radiation era, matter era, to structure formation. Produces structure seeds for Mode 2.",
            use_case="Scientific experimentation, universe evolution studies, generating authentic cosmological seeds"
        ),
        SimulationMode(
            mode="mode_2",
            name="Gameplay Universe Generation",
            description="Generates playable worlds either from cosmological structure seeds (Mode 2A) or direct initialization (Mode 2B). Fast generation for gameplay.",
            use_case="Game world creation, rapid prototyping, seeded from Mode 1 or standalone"
        )
    ]


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
                snapshots=0,
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


@api_router.post("/worlds", response_model=WorldResponse)
async def create_world(request: WorldCreateRequest):
    """
    MODE 2: Generate a new world using QMRT substrate physics.
    
    Can be initialized in two ways:
    - Mode 2A: From cosmological simulation structure seed (if cosmological_simulation_id provided)
    - Mode 2B: Direct initialization with random perturbations (default, fast)
    
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
        cosmological_seed = None
        
        # If cosmological simulation ID provided, fetch structure seed
        if request.cosmological_simulation_id:
            cosmo_sim = await db.cosmological_simulations.find_one(
                {"id": request.cosmological_simulation_id}, 
                {"_id": 0}
            )
            
            if not cosmo_sim:
                raise HTTPException(status_code=404, detail="Cosmological simulation not found")
            
            structure_seeds = cosmo_sim.get('structure_seeds', [])
            if not structure_seeds:
                raise HTTPException(status_code=400, detail="No structure seeds in cosmological simulation")
            
            # Use specified seed index or random one
            if request.structure_seed_index is not None:
                if request.structure_seed_index >= len(structure_seeds):
                    raise HTTPException(status_code=400, detail="Structure seed index out of range")
                cosmological_seed = structure_seeds[request.structure_seed_index]
            else:
                import random
                cosmological_seed = random.choice(structure_seeds)
        
        # Generate world using physics engine
        world_data = world_gen.generate_world(
            death_world_level=request.death_world_level,
            seed=request.seed,
            evolution_steps=request.evolution_steps,
            cosmological_seed=cosmological_seed
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
                                                           'substrate_metrics', 'classification',
                                                           'cosmological_origin', 'cosmological_seed_position']}),
            apex_qualified=(request.death_world_level >= 10)
        )
        
        # Save to database
        world_dict = world.model_dump()
        world_dict['created_at'] = world_dict['created_at'].isoformat()
        world_dict['last_updated'] = world_dict['last_updated'].isoformat()
        world_dict['substrate_metrics'] = world_dict['substrate_metrics']
        world_dict['world_parameters'] = world_dict['world_parameters']
        world_dict['cosmological_origin'] = world_data.get('cosmological_origin', False)
        if request.cosmological_simulation_id:
            world_dict['cosmological_simulation_id'] = request.cosmological_simulation_id
            world_dict['cosmological_seed_position'] = world_data.get('cosmological_seed_position')
        
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
        
    except HTTPException:
        raise
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
            {"name": "\u03c1\u039e (Density)", "description": "Determines inertia and gravitational behavior"},
            {"name": "T\u039e (Tension)", "description": "Governs wave speed and electromagnetic analogs"},
            {"name": "\u03c4\u039e (Torsion)", "description": "Rotational degrees of freedom, spin, magnetic alignment"},
            {"name": "\u03a6\u039e (Coherence Phase)", "description": "Interference, quantum phenomena, biological viability"}
        ],
        "simulation_modes": {
            "mode_1": {
                "name": "Full Cosmological Simulation",
                "epochs": ["primordial", "inflation", "radiation", "matter", "structure", "stellar", "planetary"],
                "purpose": "Scientific universe evolution from quantum fluctuations to structure formation"
            },
            "mode_2": {
                "name": "Gameplay Universe Generation",
                "variants": {
                    "mode_2a": "Seeded from Mode 1 cosmological structure seeds",
                    "mode_2b": "Direct initialization for fast gameplay world generation"
                },
                "purpose": "Rapid playable world creation"
            }
        },
        "death_world_scaling": {
            "min": 1,
            "max": 15,
            "earth_reference": 10,
            "apex_threshold": 10
        },
        "shared_equations": "Both modes use identical QMRT substrate equations - Mode 1 for full evolution, Mode 2 for snapshot-based generation"
    }


# Include the router in the main app
@api_router.post("/worlds/{world_id}/ecology/initialize")
async def initialize_world_ecology(world_id: str, species_count: int = 10):
    """
    PHASE B: Initialize ecological simulation for a world
    
    Spawns species with substrate-derived traits and sets up predator-prey dynamics
    """
    try:
        world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        
        # Create ecological engine
        ecology = EcologicalEngine(world)
        
        # Spawn species
        species = ecology.spawn_species(count=species_count)
        
        # Run initial evolution
        evolution_log = ecology.evolve_ecosystem(generations=100)
        
        # Get ecosystem summary
        eco_summary = ecology.get_ecosystem_summary()
        eco_summary['evolution_log'] = evolution_log
        eco_summary['species_count'] = len(species)
        
        # Update world in database
        await db.worlds.update_one(
            {"id": world_id},
            {
                "$set": {
                    "ecology_initialized": True,
                    "ecology_summary": eco_summary,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "world_id": world_id,
            "ecology_initialized": True,
            "ecosystem_summary": eco_summary,
            "message": f"Ecology initialized with {eco_summary['total_species']} species"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error initializing ecology: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ecology initialization failed: {str(e)}")


@api_router.get("/worlds/{world_id}/ecology")
async def get_world_ecology(world_id: str):
    """Get ecological state of a world"""
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    if not world.get('ecology_initialized'):
        raise HTTPException(status_code=404, detail="Ecology not initialized for this world")
    
    return {
        "world_id": world_id,
        "world_name": world['name'],
        "death_world_level": world['death_world_level'],
        "ecology_summary": world.get('ecology_summary'),
        "ecology_initialized": world.get('ecology_initialized', False)
    }


@api_router.get("/predator-tiers")
async def get_predator_tiers():
    """Get information about predator tier system"""
    return {
        "tiers": [
            {
                "tier": PredatorTier.TIER_0,
                "name": "Herbivore",
                "description": "Base consumers, prey species",
                "death_world_range": "1-15",
                "threat_level": 0
            },
            {
                "tier": PredatorTier.TIER_1,
                "name": "Apex Predator",
                "description": "Planetary apex predators",
                "death_world_range": "1-9",
                "threat_level": 3
            },
            {
                "tier": PredatorTier.TIER_2,
                "name": "Mega Predator",
                "description": "Death-world level predators",
                "death_world_range": "10-12",
                "threat_level": 7
            },
            {
                "tier": PredatorTier.TIER_3,
                "name": "Titan Predator",
                "description": "Extreme death-world hunters",
                "death_world_range": "13-14",
                "threat_level": 9
            },
            {
                "tier": PredatorTier.TIER_4,
                "name": "World Eater",
                "description": "Apocalypse-level predators",
                "death_world_range": "15",
                "threat_level": 10
            }
        ],
        "pressure_scaling": "Exponential with death-world level, modified by substrate torsion and temperature extremes"
    }





@api_router.post("/universe/simulate", response_model=UniverseSimulationResponse)
async def run_universe_simulation(name: str, seed: Optional[int] = None, grid_size: int = 32):
    """
    Run full universe simulation: Big Bang → Stellar Systems → Planetary Formation
    
    This extends cosmological simulation through stellar and planetary formation,
    identifying habitable worlds that can seed gameplay (Mode 2) worlds.
    """
    try:
        # Create universe simulator
        universe = UniverseSimulator(grid_size=grid_size, hubble_parameter=0.07)
        
        # Run full simulation
        result = universe.run_full_universe_simulation(seed=seed)
        
        # Create database entry
        universe_sim = {
            'id': str(uuid.uuid4()),
            'name': name,
            'seed': seed,
            'cosmic_time': result['cosmological_time'],
            'scale_factor': result['scale_factor'],
            'structure_seeds': result['structure_seeds'],
            'stellar_systems': result['stellar_systems'],
            'stellar_distribution': result['stellar_distribution'],
            'total_planets': result['total_planets'],
            'habitable_worlds': result['habitable_worlds'],
            'habitable_worlds_data': result['habitable_worlds_data'],
            'stellar_systems_data': result['stellar_systems_data'],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'simulation_type': 'universe_full'
        }
        
        await db.universe_simulations.insert_one(universe_sim)
        
        return UniverseSimulationResponse(**universe_sim)
        
    except Exception as e:
        logging.error(f"Error running universe simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Universe simulation failed: {str(e)}")


@api_router.get("/universe/simulations")
async def list_universe_simulations(limit: int = 20):
    """List all universe simulations"""
    try:
        sims_cursor = db.universe_simulations.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        sims = await sims_cursor.to_list(length=limit)
        return sims
    except Exception as e:
        logging.error(f"Error listing universe simulations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/universe/{universe_id}")
async def get_universe_simulation(universe_id: str):
    """Get specific universe simulation"""
    sim = await db.universe_simulations.find_one({"id": universe_id}, {"_id": 0})
    if not sim:
        raise HTTPException(status_code=404, detail="Universe simulation not found")
    return sim


@api_router.get("/universe/{universe_id}/habitable-worlds")
async def get_habitable_worlds(universe_id: str):
    """Get all habitable worlds from a universe simulation"""
    sim = await db.universe_simulations.find_one({"id": universe_id}, {"_id": 0})
    if not sim:
        raise HTTPException(status_code=404, detail="Universe simulation not found")
    
    habitable = sim.get('habitable_worlds_data', [])
    
    # Calculate gameplay-ready seeds
    seeds = []
    for i, hw in enumerate(habitable):
        substrate = hw.get('substrate_origin', {})
        density_contrast = substrate.get('density_contrast', 1.0)
        torsion = substrate.get('torsion', 0.05)
        
        # Estimate death-world level
        death_level = 5
        death_level += min(int(density_contrast * 3), 5)
        death_level += min(int(torsion * 30), 5)
        death_level = max(1, min(15, death_level))
        
        seeds.append({
            'habitable_world_id': i,
            'stellar_system_id': hw.get('stellar_system_id'),
            'star_type': hw.get('star_type'),
            'planet_mass_earth': hw.get('mass_earth'),
            'orbit_au': hw.get('orbit_au'),
            'estimated_death_level': death_level,
            'substrate_seed': substrate
        })
    
    return {
        'universe_id': universe_id,
        'universe_name': sim.get('name'),
        'total_habitable_worlds': len(habitable),
        'habitable_worlds': seeds
    }


app.include_router(api_router)
app.include_router(engine_router, prefix="/api")
app.include_router(mesoscopic_router, prefix="/api")


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)



@api_router.post("/lineage/create", response_model=Dict)
async def create_lineage(request: LineageCreateRequest):
    """
    Create new lineage entry for entity (player, species, civilization)
    
    Tracks origin world, generation, and cross-session identity
    """
    try:
        # Get birth world
        world = await db.worlds.find_one({"id": request.birth_world_id}, {"_id": 0})
        if not world:
            raise HTTPException(status_code=404, detail="Birth world not found")
        
        # Create lineage
        node = lineage_tracker.create_lineage(
            entity_name=request.entity_name,
            birth_world_id=request.birth_world_id,
            birth_death_level=world['death_world_level'],
            parent_id=request.parent_id
        )
        
        # Save to database
        lineage_dict = lineage_tracker.to_dict(node.entity_id)
        await db.lineages.insert_one(lineage_dict)
        
        return {
            "entity_id": node.entity_id,
            "entity_name": node.entity_name,
            "generation": node.generation,
            "birth_death_level": node.birth_death_level,
            "apex_qualified": node.apex_qualified,
            "message": f"Lineage created for {node.entity_name} (Generation {node.generation})"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating lineage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lineage creation failed: {str(e)}")


@api_router.get("/lineage/{entity_id}")
async def get_lineage(entity_id: str):
    """Get complete lineage information for entity"""
    # Try memory first
    if entity_id in lineage_tracker.lineages:
        return lineage_tracker.get_lineage_summary(entity_id)
    
    # Load from database
    lineage_data = await db.lineages.find_one({"entity_id": entity_id}, {"_id": 0})
    if not lineage_data:
        raise HTTPException(status_code=404, detail="Lineage not found")
    
    # Load into tracker
    lineage_tracker.from_dict(lineage_data)
    
    # Load ancestry if needed
    current_parent = lineage_data.get("parent_id")
    while current_parent:
        if current_parent not in lineage_tracker.lineages:
            parent_data = await db.lineages.find_one({"entity_id": current_parent}, {"_id": 0})
            if parent_data:
                lineage_tracker.from_dict(parent_data)
                current_parent = parent_data.get("parent_id")
            else:
                break
        else:
            break
    
    return lineage_tracker.get_lineage_summary(entity_id)


@api_router.post("/lineage/{entity_id}/record-survival")
async def record_survival(entity_id: str, world_id: str, death_level: int):
    """Record that entity survived in a world"""
    # Load lineage if needed
    if entity_id not in lineage_tracker.lineages:
        lineage_data = await db.lineages.find_one({"entity_id": entity_id}, {"_id": 0})
        if not lineage_data:
            raise HTTPException(status_code=404, detail="Lineage not found")
        lineage_tracker.from_dict(lineage_data)
    
    # Record survival
    lineage_tracker.record_world_survival(entity_id, world_id, death_level)
    
    # Update database
    updated = lineage_tracker.to_dict(entity_id)
    await db.lineages.update_one(
        {"entity_id": entity_id},
        {"$set": updated}
    )
    
    return {
        "entity_id": entity_id,
        "world_id": world_id,
        "death_level": death_level,
        "message": "Survival recorded"
    }


@api_router.post("/lineage/{entity_id}/record-encounter")
async def record_encounter(entity_id: str, was_hunter: bool, success: bool):
    """Record predator-prey encounter"""
    # Load lineage if needed
    if entity_id not in lineage_tracker.lineages:
        lineage_data = await db.lineages.find_one({"entity_id": entity_id}, {"_id": 0})
        if not lineage_data:
            raise HTTPException(status_code=404, detail="Lineage not found")
        lineage_tracker.from_dict(lineage_data)
    
    # Record encounter
    lineage_tracker.record_predator_encounter(entity_id, was_hunter, success)
    
    # Update database
    updated = lineage_tracker.to_dict(entity_id)
    await db.lineages.update_one(
        {"entity_id": entity_id},
        {"$set": updated}
    )
    
    node = lineage_tracker.lineages[entity_id]
    return {
        "entity_id": entity_id,
        "was_hunter": was_hunter,
        "success": success,
        "predator_dominance_score": round(node.predator_dominance_score, 3),
        "message": "Encounter recorded"
    }


@api_router.get("/lineage/{entity_id}/apex-check")
async def check_apex_qualification(entity_id: str):
    """Check if entity qualifies for apex status"""
    # Load lineage if needed
    if entity_id not in lineage_tracker.lineages:
        lineage_data = await db.lineages.find_one({"entity_id": entity_id}, {"_id": 0})
        if not lineage_data:
            raise HTTPException(status_code=404, detail="Lineage not found")
        lineage_tracker.from_dict(lineage_data)
        
        # Load ancestry
        current_parent = lineage_data.get("parent_id")
        while current_parent:
            if current_parent not in lineage_tracker.lineages:
                parent_data = await db.lineages.find_one({"entity_id": current_parent}, {"_id": 0})
                if parent_data:
                    lineage_tracker.from_dict(parent_data)
                    current_parent = parent_data.get("parent_id")
                else:
                    break
            else:
                break
    
    result = lineage_tracker.check_apex_qualification(entity_id)
    
    # If qualified and not verified, mark as verified
    if result["qualified"] and entity_id in lineage_tracker.lineages:
        node = lineage_tracker.lineages[entity_id]
        if not node.apex_verified:
            node.apex_verified = True
            await db.lineages.update_one(
                {"entity_id": entity_id},
                {"$set": {"apex_verified": True}}
            )
    
    return result


@api_router.get("/lineage/{entity_id}/ancestry")
async def get_ancestry_chain(entity_id: str):
    """Get full ancestry chain"""
    # Load lineage and ancestors
    if entity_id not in lineage_tracker.lineages:
        lineage_data = await db.lineages.find_one({"entity_id": entity_id}, {"_id": 0})
        if not lineage_data:
            raise HTTPException(status_code=404, detail="Lineage not found")
        lineage_tracker.from_dict(lineage_data)
        
        # Load all ancestors
        current_parent = lineage_data.get("parent_id")
        while current_parent:
            if current_parent not in lineage_tracker.lineages:
                parent_data = await db.lineages.find_one({"entity_id": current_parent}, {"_id": 0})
                if parent_data:
                    lineage_tracker.from_dict(parent_data)
                    current_parent = parent_data.get("parent_id")
                else:
                    break
            else:
                parent = lineage_tracker.lineages[current_parent]
                current_parent = parent.parent_id
    
    chain = lineage_tracker.get_ancestry_chain(entity_id)
    origin = lineage_tracker.get_origin_classification(entity_id)
    
    return {
        "entity_id": entity_id,
        "ancestry_chain": [
            {
                "entity_id": node.entity_id,
                "entity_name": node.entity_name,
                "generation": node.generation,
                "birth_death_level": node.birth_death_level,
                "predator_dominance": round(node.predator_dominance_score, 3),
                "apex_verified": node.apex_verified
            }
            for node in chain
        ],
        "origin_classification": origin
    }




# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
