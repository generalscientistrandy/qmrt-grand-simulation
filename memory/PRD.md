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
- [x] QMRT Canonical Hamiltonian Engine (Yoshida 4th-order)
- [x] Quark-Level Dual-Basin Attractor Engine
- [x] **Frequency-Domain Substrate Engine** (December 2025)
- [x] **Comprehensive Physics Validation Suite** (December 2025 - NEW)
- [ ] Structure clustering & composite formation (hadrons)
- [ ] Civilization emergence systems
- [ ] Hidden lineage and scan-detection
- [ ] Unreal Engine integration layers

## Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Physics**: NumPy, SciPy for numerical simulation
- **Integrators**: Yoshida 4th-order symplectic, spectral Laplacian (FFT)

### Code Structure
```
/app/backend/
  server.py                 - Main FastAPI app
  models.py                 - Pydantic models
  physics_engine.py         - Core QMRT equations
  cosmological_simulator.py - Mode 1 simulation
  world_generator_v2.py     - Mode 2 world generation
  ecological_engine.py      - Predator/prey dynamics
  lineage_system.py         - Lineage tracking
  universe_simulator.py     - Enhanced universe sim
  universe_engine.py        - State management
  engine_api.py             - Universe engine API routes
  mesoscopic_substrate.py   - QMRT substrate simulation
  mesoscopic_api.py         - Substrate API routes
  qmrt_hamiltonian_engine.py - Canonical Hamiltonian engine
  qmrt_canonical_api.py     - Hamiltonian API routes
  qmrt_quark_engine.py      - Dual-basin attractor engine
  qmrt_quark_api.py         - Quark engine API routes
  qmrt_frequency_engine.py  - Frequency-domain engine
  qmrt_frequency_api.py     - Frequency API routes (includes comprehensive validation)
  qmrt_comprehensive_validation.py - Physics validation suite (NEW)
```

### Key Technical Decisions
1. **Energy Conservation**: Uses Yoshida 4th-order symplectic integration with velocity rescaling
2. **Zero-Balance Principle**: Energy renormalization maintains exact energy conservation (0.0% drift)
3. **Phase Convention**: φ ∈ (−π, +π) symmetric around zero for dual-basin attractors
4. **Emergent Classification**: Structure properties emerge from field modes - NOT hardcoded labels
5. **Modular API Design**: Separate router files for each major subsystem
6. **Numerical Stability**: Spectral methods for exact periodic BC, NaN/Inf guards

## What's Been Implemented

### December 2025 - Comprehensive Physics Validation Suite (LATEST)
- **Scaling Persistence Test**: Validates basin stability at larger grid sizes (32, 48, 64)
- **Long-time Entropy Drift Test**: S(t) = -Σ P_k log P_k, tests "half-entropy regime" hypothesis
- **Basin Identity Tracking**: Measures merge probability, tunneling probability, decay rates
- **Phase Diagram Mapping**: Maps (a_ω/K_ω) vs g coupling regimes (unstable/reflective/tunneling/equilibrium)
- **API Endpoints**:
  - `/api/qmrt_frequency/comprehensive/scaling_persistence` - ✅ TESTED
  - `/api/qmrt_frequency/comprehensive/entropy_drift` - ✅ TESTED
  - `/api/qmrt_frequency/comprehensive/basin_tracking` - ✅ TESTED
  - `/api/qmrt_frequency/comprehensive/phase_diagram` - ✅ Functional
  - `/api/qmrt_frequency/comprehensive/run_all` - Full suite runner

### December 2025 - Frequency-Domain Substrate Engine
- **Explicit frequency field (ω)**: Fifth fundamental field - medium state variable enabling spectral universes
- **Band potential**: V_band(ω) = a_ω(ω² − ω₀²)² creates double-well with basins at ±ω₀
- **Frequency-phase coupling**: g_ωφ·ω·|∇φ|² - matter structures prefer certain frequency bands
- **Frequency-density coupling**: g_ωρ·ω·(ρ−ρ₀)² - density-frequency interaction
- **Five fields**: (ρ, σ, τ, φ, ω) with five conjugate momenta
- **Spectral universe formation**: Frequency clustering observed from turbulent initial conditions
- **Energy conservation**: 0.0000% drift via Yoshida4 + velocity rescaling
- **Structure classification**: Both phase_basin AND frequency_band
- **API Endpoints**: 8 endpoints at `/api/qmrt_frequency/`
- **Test Results**: 33/33 tests passed (100%)

### December 2025 - Quark-Level Dual-Basin Attractor Engine
- **Dual-basin phase potential**: U_φ(φ) = -a_φ cos(φ) creates symmetric minima at φ=0 (matter) and φ=±π (antimatter)
- **Phase convention**: φ ∈ (−π, +π) symmetric around zero
- **Antimatter as phase-inverted attractor**: NOT a separate species, same field solution family
- **Combined structure tracking**: Centroid-based + topological fingerprinting
- **Emergent mode properties**: binding_energy, winding_number, vorticity, coherence_length, radial_profile
- **Annihilation dynamics**: Coherence collapse, phase decoherence cascade, energy redistribution
- **Energy conservation**: 0.0000% drift via Yoshida4 + velocity rescaling
- **API Endpoints**:
  - `/api/qmrt_quark/theory` - Dual-basin ontology summary
  - `/api/qmrt_quark/validate_dual_basin` - Basin symmetry validation test
  - `/api/qmrt_quark/test_annihilation` - Annihilation dynamics test
  - `/api/qmrt_quark/test_persistence` - Long-term structure persistence test
  - `/api/qmrt_quark/initialize` - Create engine for step-by-step evolution
  - `/api/qmrt_quark/{engine_id}/evolve` - Evolve engine N steps
  - `/api/qmrt_quark/{engine_id}/state` - Get state summary
  - `/api/qmrt_quark/{engine_id}/structures` - Get active structures with mode properties
- **Test Results**: 19/19 tests passed (100%), energy drift 0.0000%

### December 2025 - QMRT Canonical Hamiltonian Engine
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
- **Energy conservation**: 0.0% drift via Yoshida4 + velocity rescaling

### December 2025 - Mesoscopic Substrate Simulation
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
| `/api/qmrt/run` | POST | Run canonical Hamiltonian simulation |
| `/api/qmrt/stability-test` | POST | Test integrator stability |
| `/api/qmrt_quark/theory` | GET | Dual-basin ontology summary |
| `/api/qmrt_quark/validate_dual_basin` | POST | Basin validation test |
| `/api/qmrt_quark/test_annihilation` | POST | Annihilation dynamics test |
| `/api/qmrt_quark/test_persistence` | POST | Structure persistence test |
| `/api/qmrt_quark/initialize` | POST | Initialize quark engine |
| `/api/qmrt_quark/{id}/evolve` | POST | Evolve quark engine |
| `/api/qmrt_frequency/theory` | GET | Frequency-domain theory summary |
| `/api/qmrt_frequency/test_frequency_domains` | POST | Test frequency basin separation |
| `/api/qmrt_frequency/test_spectral_universes` | POST | Test spectral universe formation |
| `/api/qmrt_frequency/initialize` | POST | Initialize frequency engine |
| `/api/qmrt_frequency/{id}/evolve` | POST | Evolve frequency engine |

## Test Coverage
- **Backend tests**: 
  - `/app/backend/tests/test_mesoscopic_api.py` (23 tests)
  - `/app/backend/tests/test_qmrt_quark_api.py` (19 tests)
  - `/app/backend/tests/test_qmrt_frequency_api.py` (33 tests)
- **Test reports**: 
  - `/app/test_reports/iteration_2.json` (mesoscopic)
  - `/app/test_reports/iteration_3.json` (quark engine)
  - `/app/test_reports/iteration_4.json` (frequency engine)
- **Results**: 75/75 tests passed (100%)

## Prioritized Backlog

### P0 - Complete
- [x] Mesoscopic substrate simulation with energy conservation
- [x] QMRT Canonical Hamiltonian Engine with Yoshida4 integrator
- [x] Quark-Level Dual-Basin Attractor Engine (validates ontology)
- [x] **Frequency-Domain Substrate Engine** (spectral universes)

### P1 - Next (Scale Ladder)
- [ ] **Quark-like Node Persistence**: Validate stable structures in frequency basins survive long-term
- [ ] **Hadron Confinement Regime**: Model transition from quark structures to confined composites
- [ ] **Tune Frequency Parameters**: Optimize ω₀, a_ω, coupling strengths for cleaner basin separation
- [ ] **Update Frontend Visualizer**: Display frequency domain statistics

### P2 - Planned
- [ ] Expand Apex Qualification System with multi-generational metrics
- [ ] Connect substrate simulations to world generation pipeline
- [ ] Civilization behavior modeling

### P3 - Future
- [ ] Cosmological scaling: Emergent scale factor a(t) from quark-level dynamics
- [ ] Astrophysical realism (galaxy morphology, stellar lifecycles)
- [ ] Multiplayer world continuity and synchronization
- [ ] Unreal Engine runtime synchronization

## Known Issues & Technical Debt
1. **Basin Asymmetry**: In dual-basin tests, matter basin dominates (~70%) over antimatter (~30%) - may need potential tuning or is emergent physics
2. **No Annihilation Events**: Current parameters don't trigger annihilation - structures don't overlap enough
3. `server.py` is large - continue modularization
4. Obsolete files (`mesoscopic_substrate.py`, `physics_engine.py`) should be deprecated
