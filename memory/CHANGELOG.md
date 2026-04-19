# QMRT Simulation Lab - Changelog

## December 2025

### 3D Slice Projection (Latest)
- **Added**: Slice-based structure filtering for 3D views
- **Added**: Coordinate projection: XY (filter z), XZ (filter y), YZ (filter x)
- **Added**: Distance-based opacity fading: `opacity = max(0, 1 - |d| / δ)`
- **Added**: Cluster radius scaling for slice intersection visualization
- **Added**: Slice Thickness slider (1-10 units, default 3)
- **Added**: Debug "Show all z" toggle (yellow, secondary)
- **Added**: Hover tooltip shows slice type, distance, and projection warnings
- **Tested**: 3D simulation with 503 births, 487 deaths, all four slice views working

### Timeline Animation Mode
- **Added**: Play/pause button with time display
- **Added**: Timeline scrubber for manual navigation
- **Added**: Speed control slider (20ms-500ms per frame, shown as Nx)
- **Added**: Event navigation buttons (jump to first birth, next event, final frame)
- **Added**: Event count badges showing births/deaths at current frame
- **Added**: Animation filters (Births, Deaths, Active, Selected)
- **Added**: Birth effect - green glow/pulse on newly born structures
- **Added**: Death effect - fade out with grayscale
- **Added**: Structures animate with timeline (use structures_timeline not just final snapshot)
- **Added**: Hover tooltips show structure state (birth/active/death)
- **Tested**: Screenshots verified all animation controls working

### Structure Time Tracking
- **Added**: `StructureTracker` class with frame-to-frame ID matching
- **Added**: Per-structure tracking: id, birth_time, last_seen_time, age, status, match_confidence
- **Added**: Trajectory recording (position history over time)
- **Added**: Stability/energy history recording per structure
- **Added**: API response: structures_timeline, tracked_structures, tracking_* summary stats
- **Added**: Frontend: Structure Time Tracking stats card
- **Added**: Frontend: Trajectories toggle and trajectory overlay lines
- **Added**: Frontend: Enhanced inspector with tracking section (ID, Status, Birth, Age, Confidence)
- **Added**: Frontend: Stability history mini-chart in inspector
- **Matching Algorithm**: Spatial proximity + type consistency + similarity scoring
- **Confidence Levels**: high (close + similar), medium, low

### Structure Position Overlays
- **Added**: `FieldHeatmapWithOverlays` component with interactive SVG overlays
- **Added**: Toggle controls for strain nodes, clusters, particle nodes, vortices
- **Added**: Hover tooltips showing type-specific details (E, σ, Φ, n, ω, χ)
- **Added**: Click inspector panel with full structure properties
- **Added**: Close button on inspector panel (data-testid='inspector-close-btn')
- **Visual**: Orange diamonds (strain), green circles (clusters), colored circles (particles), cyan spirals (vortices)
- **Tested**: 7/7 frontend features verified

### Mesoscopic Structures Integration
- **Added**: Ported legacy mesoscopic structure detection into `qmrt_simulation_api.py`
  - `detect_torsion_vortices()` — 2D/3D vorticity-based vortex detection
  - `detect_strain_energy_nodes()` — 2D/3D strain energy localization
  - `detect_coherence_clusters()` — 2D/3D phase coherence clustering
  - `identify_particle_nodes()` — Co-located structure identification
- **Added**: New API response structure with clean `structures` top-level key
- **Added**: Structure counts in TimePoint measurements (`vortex_count`, `cluster_count`, etc.)
- **Added**: New "Structures" tab in frontend UI
- **Added**: Structure Count Evolution chart
- **Added**: Detailed structure lists with item badges
- **Updated**: Overview tab now shows structure count summary row
- **Tested**: 19/19 backend pytest tests passed, all frontend UI verified

### Parameter Boundary Map
- **Added**: `parameter_boundary_map.py` — 19-point α sweep in 2D and 3D
- **Added**: `BOUNDARY_MAP_RESULTS.md` — Results interpretation
- **Discovery**: System is in STRONG coupling regime across entire α range (0.05-0.95)

### Frontend Redesign
- **Added**: `QMRTSimulationLab.jsx` — New pure physics simulation interface
- **Removed**: Game elements (ecology, predators, death-worlds)
- **Added**: Real-time metrics display (S, O, R, P, I_TS)
- **Added**: Field heatmaps (2D) and central slices (3D)
- **Added**: Playback controls for time evolution

### Unified Validation
- **Added**: `unified_validation.py` — 3D integrated validation run
- **Result**: 7/9 checks passed when all components measured together

### 3D Simulation
- **Added**: `simulation_3d.py` — Full 3+1D simulation
- **Result**: 4/4 tests passed (spherical light cones, causal confinement, lensing, energy balance)

### Universal Critical Exponent
- **Added**: `universality_test.py` — 19-test comprehensive suite
- **Discovery**: Universal exponent α = 2.00 ± 0.04 (dimension-independent)
