# QMRT Branch Inventory (Current Revision)

**Date: December 2025**
**Status: PROVISIONAL — Expected to expand as hidden branches are discovered**

---

## Inventory Principles

1. **This inventory is incomplete** — New branches are often discovered when previously bundled mechanisms are separated by role, timescale, or interaction pattern

2. **Future additions should be classified as**:
   - **New branch** — A truly distinct role not already represented
   - **Sub-branch** — A more specific mechanism inside a current branch
   - **Branch interaction pattern** — A stable coupling between known branches

3. **Likely undiscovered branches include**:
   - Transition branches (regime switching control)
   - Persistence branches (structure maintenance beyond damping)
   - Coordination branches (mesoscopic organization)
   - Selection branches (which structures survive to scaffold)
   - Transfer branches (energy flow between layers)

---

## Overview

This inventory tracks each mechanism's role in the coupled QMRT architecture. Per the Branch-Compositional Emergence Principle, understanding a branch requires knowing:

1. **Purpose** — What does it do?
2. **Timescale** — When does it matter?
3. **Partners** — What does it couple with?
4. **Failure Mode** — What happens in isolation?
5. **Status** — Frozen, Active, Closed, or Proposed

---

## Branch Inventory

---

### 1. TOPOLOGICAL CREATION (Vortex Injection)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Generate topological defects (+/- winding) in the medium |
| **Role Type** | Creator |
| **What it does** | Injects balanced pairs of positive and negative vortices into the field |
| **Timescale** | Discrete injection events (every N steps when driving is active) |
| **Partners** | Attractor geometry (determines where injection is effective), τ field (determines local energy cost) |
| **Failure Mode** | Without injection, system relaxes to trivial state; with only injection, no organization |
| **Status** | **FROZEN** |

**Key insight**: Creation alone produces chaos. Organization requires other branches.

---

### 2. TOPOLOGICAL BALANCE (Symmetric Creation)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Maintain 50/50 balance between +/- winding sectors |
| **Role Type** | Regulator (emergent) |
| **What it does** | Symmetric injection ensures equal numbers of +/- defects are created |
| **Timescale** | Per-injection (each event creates balanced pairs) |
| **Partners** | Topological creation (provides the balance), attractor geometry (shapes how balance organizes spatially) |
| **Failure Mode** | Asymmetric injection → population imbalance → different dynamics |
| **Status** | **FROZEN** |

**Key insight**: Balance is not a single mechanism — it's symmetric creation + organizational symmetry acting together.

---

### 3. ATTRACTOR COUPLING (Spatial Geometry)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Shape spatial organization through coupling gradient |
| **Role Type** | Sorter / Organizer |
| **What it does** | Creates interior (high coupling, protective) vs exterior (low coupling, dissipative) landscape |
| **Timescale** | Static geometry, always active |
| **Partners** | All structure-forming mechanisms (determines where structures can persist) |
| **Failure Mode** | Flat coupling → no spatial organization, structures form randomly |
| **Status** | **FROZEN** |

**Key insight**: Geometry doesn't create structure — it determines where structure can survive.

---

### 4. τ ENERGY ACCOUNTING (Dynamic Medium)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Implement regime-sensitive energy regulation |
| **Role Type** | Regulator / Accountant |
| **What it does** | τ responds to local energy: high energy → high τ → faster dissipation (maintenance cost) |
| **Timescale** | Continuous (relaxation timescale ~0.01), strengthens over developmental time |
| **Partners** | All energy-containing structures, channel assignment (bound energy), topology |
| **Failure Mode** | Weak τ response → flat energy landscape, no regime differentiation |
| **Status** | **ACTIVE** (tau_response = 0.02) |

**Key parameters**:
- `tau_response = 0.02` (amplified from 0.005)
- `tau_relaxation = 0.01`

**Key insight**: τ differentiates organizational regimes (loop vs clustering vs scaffold). Birth environment τ predicts defect lifetime (20% effect).

---

### 5. CHANNEL ASSIGNMENT (Topological Protection)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Mark and protect topologically active regions |
| **Role Type** | Stabilizer / Memory |
| **What it does** | Accumulates in high-topology regions, provides protection from amplitude collapse |
| **Timescale** | Accumulative (builds up over ~100 steps), decays slowly |
| **Partners** | Topology detection, τ accounting (channel = bound energy), attractor coupling |
| **Failure Mode** | No channel → structures unprotected, rapid decay |
| **Status** | **ACTIVE** |

**Key insight**: Channel represents "bound energy" — energy committed to maintaining existing structure rather than available for new organization.

---

### 6. REMNANT FIELD (Topological Memory)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Carry memory of past topological activity |
| **Role Type** | Memory / Scaffold |
| **What it does** | Accumulates where topology has been active, decays very slowly |
| **Timescale** | Long-term accumulative (decay ~0.999 per step) |
| **Partners** | Topology detection, channel assignment, scaffold organization |
| **Failure Mode** | No remnant → no memory of past organization, each cycle starts fresh |
| **Status** | **ACTIVE** |

**Key insight**: Remnant enables scaffold persistence — organizational patterns can outlast individual defects.

---

### 7. WAVE DYNAMICS (Field Propagation)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Propagate field disturbances through the medium |
| **Role Type** | Carrier / Transmitter |
| **What it does** | Laplacian-based wave equation with τ-modulated speed: c_eff = √(c₀² × τ) |
| **Timescale** | Fast (wave speed ~2), continuous |
| **Partners** | τ field (modulates speed), damping (energy loss), all structure |
| **Failure Mode** | Without waves, no communication between regions |
| **Status** | **ACTIVE** |

**Key insight**: Wave speed links τ to dissipation — high τ → fast waves → faster energy loss.

---

### 8. DAMPING (Energy Dissipation)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Remove energy from the system |
| **Role Type** | Limiter / Drain |
| **What it does** | Velocity-proportional damping: -γ × ψ_dot |
| **Timescale** | Continuous, affects all motion |
| **Partners** | τ field (high τ regions dissipate faster), wave dynamics |
| **Failure Mode** | No damping → energy accumulates indefinitely, instability |
| **Status** | **ACTIVE** |

**Key parameter**: `gamma = 0.007`

**Key insight**: Damping alone is uniform. τ makes it regime-sensitive.

---

### 9. DRIVING (Energy Input)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Supply energy to sustain organization |
| **Role Type** | Creator / Sustainer |
| **What it does** | Periodic vortex injection adds energy and topological charge |
| **Timescale** | Periodic (every `injection_interval` steps) |
| **Partners** | Topological creation, balance, all organizational mechanisms |
| **Failure Mode** | No driving → system decays to ground state |
| **Status** | **ACTIVE** |

**Key parameter**: `injection_interval = 50-80` (regime-dependent)

**Key insight**: Driving is not just energy — it's also topological charge. Sweet spot exists for organizational complexity.

---

### 10. PHASE COUPLING (Local Phase Conformity) — CLOSED

| Aspect | Description |
|--------|-------------|
| **Purpose** | (Proposed) Generate phase-coherent classes beyond winding sign |
| **Role Type** | Sorter (proposed) |
| **What it does** | Nudges local phases toward 0 or π relative to smoothed average |
| **Timescale** | Continuous, local |
| **Partners** | Topology, τ accounting |
| **Failure Mode** | Produces only local conformity, no global phase classes |
| **Status** | **CLOSED** — Insufficient as standalone mechanism |

**Key insight**: Local coupling cannot produce global coordination. Failed independently of energy accounting.

---

## Interaction Matrix

| Branch | Creates | Stabilizes | Limits | Times | Supports |
|--------|---------|------------|--------|-------|----------|
| **Topological Creation** | ✓ | | | | |
| **Balance** | | ✓ | | | |
| **Attractor Geometry** | | | | | ✓ |
| **τ Accounting** | | | ✓ | | ✓ |
| **Channel** | | ✓ | | | |
| **Remnant** | | ✓ | | | |
| **Wave Dynamics** | | | | | ✓ |
| **Damping** | | | ✓ | | |
| **Driving** | ✓ | | | ✓ | |

---

## Coupling Diagram

```
                    DRIVING (energy + topology input)
                              │
                              ▼
              ┌───────────────────────────────┐
              │    TOPOLOGICAL CREATION       │
              │    (vortex pairs +/-)         │
              └───────────────┬───────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ BALANCE  │       │ GEOMETRY │       │ τ FIELD  │
    │ (50/50)  │       │ (attractor)│     │ (energy) │
    └────┬─────┘       └────┬─────┘       └────┬─────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                            ▼
              ┌───────────────────────────────┐
              │    ORGANIZATIONAL REGIMES     │
              │  (loop → clustering → scaffold)│
              └───────────────┬───────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ CHANNEL  │       │ REMNANT  │       │ DAMPING  │
    │ (protect)│       │ (memory) │       │ (drain)  │
    └──────────┘       └──────────┘       └──────────┘
```

---

## Emergent Phenomena by Branch Combination

| Phenomenon | Required Branches |
|------------|-------------------|
| Defect persistence | Creation + Channel + Geometry |
| Population balance | Creation (symmetric) + Geometry |
| Regime differentiation | τ + Driving (density) |
| Scaffold formation | Remnant + Channel + Geometry |
| Maintenance cost | τ + Damping + Wave dynamics |
| Birth-environment effect | τ (at birth time) + subsequent dynamics |

---

## Open Questions

1. **Higher-layer auditors**: Does τ alone suffice for complex organization, or are layer-specific auditors needed?

2. **Scaffold dynamics**: What determines scaffold stability vs collapse? Is remnant sufficient?

3. **Phase coherence**: Could phase coupling matter in combination with other branches, even though it fails alone?

4. **Scale effects**: Do branch interactions change at larger scales (96³)?

---

## Update Log

| Date | Change |
|------|--------|
| Dec 2025 | Initial inventory created |
| Dec 2025 | τ accounting updated to amplified baseline (0.02) |
| Dec 2025 | Phase coupling marked CLOSED |

---

*QMRT Branch Inventory — Living Document*
