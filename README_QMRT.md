# QMRT Simulation Universe - Phase A Complete

## Overview
A persistent simulation universe system powered by **Quark Medium Relativity Theory (QMRT)** - a unified physics framework that serves as the authoritative substrate for world generation, ecological systems, and evolutionary dynamics.

## Phase A: World Generation & Death-World Scaling ✅

### Core Implementation

#### 1. QMRT Physics Engine (`/app/backend/physics_engine.py`)
Implements the four fundamental substrate properties:

- **ρΞ (Density)** - Determines inertia and gravitational behavior
- **TΞ (Tension)** - Governs wave speed and electromagnetic analogs  
- **τΞ (Torsion)** - Rotational degrees of freedom, spin, magnetic alignment
- **ΦΞ (Coherence Phase)** - Interference, quantum phenomena, biological viability

**Key Equations Implemented:**
```
∂²(ΦΞ)/∂t² = A_φ ∇²(ΦΞ) + B_φ ∇²(ρΞ) + C_φ ∇²(TΞ)
∂²(ρΞ)/∂t² = A_ρ ∇²(ρΞ) + B_ρ ∇²(TΞ)
∂²(TΞ)/∂t² = A_T ∇²(TΞ) + B_T ∇²(ρΞ)
∂²(τΞ)/∂t² = A_τ ∇²(τΞ) + curl_terms
```

#### 2. World Generator (`/app/backend/world_generator.py`)
Translates substrate physics to gameplay parameters:

**Translation Layer:**
- Substrate density → Gravity, matter concentration
- Substrate tension → Energy potential, EM field strength
- Substrate torsion → Magnetic fields, atmospheric chaos
- Coherence phase → Quantum stability, biological viability

**Death-World Scaling (1-15):**
- **1-3**: Sanctuary Worlds (low difficulty, stable)
- **4-6**: Garden/Frontier Worlds (moderate)
- **7-9**: Contested/Harsh Worlds (challenging)
- **10**: Earth-Class World (reference standard) ⭐
- **11-12**: Death Worlds (extreme)
- **13-14**: Extreme Death Worlds (apocalyptic)
- **15**: Apocalypse World (maximum chaos)

**Apex Qualification:** Enabled for worlds level 10+

#### 3. Backend API (`/app/backend/server.py`)

**Endpoints:**
- `GET /api/` - API info
- `GET /api/substrate/info` - QMRT theory information
- `POST /api/worlds` - Generate new world
- `GET /api/worlds` - List all worlds
- `GET /api/worlds/{id}` - Get world details
- `DELETE /api/worlds/{id}` - Delete world

**World Generation Parameters:**
```json
{
  "name": "World Name",
  "death_world_level": 10,
  "seed": 12345,
  "evolution_steps": 200
}
```

#### 4. Frontend Dashboard

**Components:**
- `Layout.js` - Main app structure with scientific cyberpunk design
- `Dashboard.js` - Universe catalog with stats and world grid
- `WorldCard.js` - Individual world display with key metrics
- `CreateWorldModal.js` - World generation interface with slider
- `WorldDetailModal.js` - Detailed view with parameters & substrate tabs
- `SubstrateInfoModal.js` - QMRT theory education

**Design System:**
- Scientific brutalism meets cyberpunk HUD aesthetic
- Dark theme (#050505) with neon cyan accents (#00F0FF)
- Typography: Rajdhani (display), Inter (body), JetBrains Mono (data)
- Glassmorphism cards with backdrop blur
- Grid background pattern for depth

## Usage

### Backend
```bash
# Requirements installed
cd /app/backend
pip install -r requirements.txt

# Server runs on 0.0.0.0:8001
```

### Frontend
```bash
cd /app/frontend
yarn install
yarn start
# Runs on port 3000
```

### Environment Variables
**Backend (.env):**
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name
- `CORS_ORIGINS` - Allowed origins

**Frontend (.env):**
- `REACT_APP_BACKEND_URL` - Backend API URL

## Testing Results
✅ 100% Backend Tests Passed (12/12)  
✅ 100% Frontend Integration Working  
✅ All UI Components Functional  
✅ Physics Engine Validated

## Future Phases

### Phase B: Ecological & Evolutionary Simulation
**Planned Systems:**
- Morphogenesis equations: `∂ρ_bio/∂t = D_bio ∇²(ρ_bio) + f_growth(ρ_bio, ΦΞ, TΞ)`
- Predator-prey dynamics
- Population evolution with mutation rates
- Homeostasis systems
- Resource distribution

### Phase C: Apex Qualification & Lineage Tracking
**Planned Systems:**
- Hidden death-world lineage tracking
- Apex status qualification (level 10+ origin)
- Scan-detection systems
- Origin-world discovery mechanics
- Lineage memory persistence

### Phase D: Civilization Emergence
**Planned Systems:**
- Settlement scaling
- Building mechanics
- Multi-world persistence
- Civilization state management

## Unreal Engine Integration
Ready for integration via:
1. REST API endpoints for world state
2. JSON world parameter exports
3. Modular translation layer for UE5 variables
4. Persistent world state in MongoDB

## Technical Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  - Dashboard UI                         │
│  - World Creation/Management            │
│  - Data Visualization                   │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────┐
│         Backend (FastAPI)               │
│  - API Endpoints                        │
│  - Request Validation                   │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼────┐  ┌────▼─────┐  ┌───▼────┐
│ QMRT   │  │  World   │  │ MongoDB│
│Physics │  │Generator │  │ (State)│
│Engine  │  │          │  │        │
└────────┘  └──────────┘  └────────┘
```

## Key Files
- `/app/backend/physics_engine.py` - QMRT substrate simulation
- `/app/backend/world_generator.py` - Parameter translation
- `/app/backend/models.py` - Data models
- `/app/backend/server.py` - API server
- `/app/frontend/src/components/Dashboard.js` - Main UI
- `/app/design_guidelines.json` - Design system spec

## Performance Notes
- World generation: ~2-5 seconds (200 evolution steps)
- Grid size: 32³ for balance between accuracy and speed
- Can scale up for production (64³ or 128³ grids)

## Scientific Foundation
Based on uploaded QMRT research equations:
- Part 1: Substrate manifold and field operators
- Part 2: Unified wave dynamics and dispersion relations
- Part 3: Thermodynamics, biology, and emergence equations

All world generation is derived from these authoritative equations, not invented physics.

---

**Status:** Phase A Complete ✅  
**Next:** Phase B - Ecological & Evolutionary Simulation  
**Version:** 1.0.0  
**Built with:** FastAPI, React, MongoDB, NumPy, QMRT Theory
