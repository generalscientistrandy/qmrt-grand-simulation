# QMRT Simulation Universe - Product Requirements Document

## Original Problem Statement
Design and build programmable systems for a persistent simulation universe based on Quark Medium Relativity Theory (QMRT). The simulation must be strictly grounded in validated research equations from QMRT PDFs. Key principle: Zero-balance universe where energy transforms between forms but is not created/destroyed.

## User Personas
- **Game Developers**: Need to generate consistent, physics-grounded game worlds
- **Researchers**: Want to explore emergent phenomena from QMRT substrate dynamics
- **Content Creators**: Require diverse, procedurally-generated worlds with meaningful variation

## Core Requirements

### Simulation Modes
1. **Mode 1 - Full Cosmological Simulation**: Evolves universe from primordial initialization through structure formation
2. **Mode 2 - Gameplay Universe Generation**: Generates playable worlds from cosmological seeds or direct initialization

### Core Systems
- [x] World generation with QMRT physics grounding
- [x] Death-world scaling (levels 1-15, Earth-class ~10)
- [x] Apex qualification system for lineages
- [x] Ecological and evolutionary simulation
- [x] Predator-prey pressure systems
- [x] Core Universe Evolution Engine (state, timesteps, snapshots, branching)
- [x] Mesoscopic Substrate Simulation (energy-conserving)
- [ ] Civilization emergence systems
- [ ] Hidden lineage and scan-detection
- [ ] Unreal Engine integration layers

## Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Physics**: NumPy, SciPy for numerical simulation

### Code Structure
```
/app/backend/
  server.py              - Main FastAPI app
  models.py              - Pydantic models
  physics_engine.py      - Core QMRT equations
  cosmological_simulator.py - Mode 1 simulation
  world_generator_v2.py  - Mode 2 world generation
  ecological_engine.py   - Predator/prey dynamics
  lineage_system.py      - Lineage tracking
  universe_simulator.py  - Enhanced universe sim
  universe_engine.py     - State management
  engine_api.py          - Universe engine API routes
  mesoscopic_substrate.py - QMRT substrate simulation (NEW)
  mesoscopic_api.py      - Substrate API routes (NEW)
```

### Key Technical Decisions
1. **Energy Conservation**: Uses Störmer-Verlet symplectic integration for long-term energy stability
2. **Zero-Balance Principle**: Energy renormalization when drift exceeds 1%
3. **Modular API Design**: Separate router files for each major subsystem
4. **Numerical Stability**: NaN/Inf guards, field clamping, safe JSON serialization

## What's Been Implemented

## What's Been Implemented

### December 2025 - Mesoscopic Substrate Simulation
- **Energy-conserving field evolution** using symplectic integration
- **Four fundamental QMRT fields**: density (ρΞ), tension (TΞ), torsion (τΞ), coherence (ΦΞ)
- **Emergent structure detection**: torsion vortices, strain nodes, coherence clusters, particle-like nodes
- **Zero-balance compliance**: Energy drift < 1% over extended simulations
- **Comprehensive API endpoints**:
  - `/api/mesoscopic/initialize` - Create substrate
  - `/api/mesoscopic/{id}/evolve` - Evolve with structure detection
  - `/api/mesoscopic/run` - Complete simulation workflow
  - `/api/mesoscopic/stability-test` - Numerical stability validation

### December 2025 - Mesoscopic Visualizer (Frontend)
- **Real-time substrate visualization** with interactive controls
- **Three-tab interface**: Simulation, Structures, Energy
- **Field dynamics chart**: Density and variance over time
- **Structure formation chart**: Vortices, strain nodes, particles over time
- **Energy conservation display**: Initial/final energy, drift percentage
- **Playback controls**: Play, pause, reset, and scrub through evolution
- **Parameter controls**: Grid size, amplitude, duration sliders

### December 2025 - QMRT Canonical Hamiltonian Engine
- **Exact Hamiltonian implementation** from user-provided QMRT equations
- **Four fields with conjugate momenta**: (ρ,π_ρ), (σ,π_σ), (τ,π_τ), (φ,π_φ)
- **Shifted potential**: U_ρ(ρ) = (a/2)(ρ-1)² + (c/4)(ρ-1)⁴ (equilibrium at ρ=1)
- **All coupling terms**: λ_ρσ, λ_ρτ, λ_στ, λ_σφ, λ_τφ, λ_ρφ
- **Emergent cosmology**: Scale factor a(t) from field dynamics, NOT injected
- **Structure criteria**: Stabilization functional S(x,t), proton formation Π_p
- **Energy conservation**: Achieved via Yoshida4 + velocity rescaling (0.0% drift)

### December 2025 - Yoshida 4th-Order Symplectic Integrator
- **Implemented Yoshida4** for O(dt⁴) energy conservation
- **Spectral Laplacian** for exact periodic boundary conditions
- **Energy enforcement**: Velocity rescaling maintains exact zero-balance
- **Stability test endpoint**: `/api/qmrt/stability-test`
- **Longevity test endpoint**: `/api/qmrt/longevity-test`
- **Results**: 0.0% energy drift across all timesteps (0.005 to 0.05)
- **Structure persistence**: ~230-290 structures stable over 30s simulation

### Previous Work
- World generation from QMRT substrate metrics
- Cosmological simulation (Mode 1)
- Gameplay world generation (Mode 2)
- Ecological engine with predator tiers
- Lineage persistence system
- Universe evolution engine with snapshots and branching

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | API info and version |
| `/api/worlds/create` | POST | Create gameplay world (Mode 2) |
| `/api/cosmological/run` | POST | Run cosmological simulation (Mode 1) |
| `/api/engine/initialize` | POST | Initialize universe engine |
| `/api/engine/{id}/advance` | POST | Advance simulation timestep |
| `/api/engine/{id}/snapshot` | POST | Create state snapshot |
| `/api/mesoscopic/initialize` | POST | Initialize substrate |
| `/api/mesoscopic/{id}/evolve` | POST | Evolve substrate |
| `/api/mesoscopic/run` | POST | Run complete simulation |
| `/api/mesoscopic/stability-test` | POST | Test stability |

## Test Coverage
- **Backend tests**: `/app/backend/tests/test_mesoscopic_api.py`
- **Test reports**: `/app/test_reports/iteration_2.json`
- **Results**: 23/23 tests passed (100%)

## Prioritized Backlog

### P0 - Complete
- [x] Mesoscopic substrate simulation with energy conservation

### P1 - Next
- [ ] Expand Apex Qualification System with multi-generational metrics
- [ ] Connect mesoscopic substrate to world generation pipeline

### P2 - Planned
- [ ] Civilization behavior modeling
- [ ] Hidden lineage and scan-detection systems

### P3 - Future
- [ ] Astrophysical realism (galaxy morphology, stellar lifecycles)
- [ ] Multiplayer world continuity and synchronization
- [ ] Unreal Engine runtime synchronization

## Known Issues & Technical Debt
1. `server.py` is large and prone to errors - continue modularization
2. `physics_engine.py` has overflow warnings - needs stability updates similar to mesoscopic module
