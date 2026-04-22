# QMRT Papers: Overview

## Three-Paper Arc

This package contains three complementary papers investigating emergent structure in a dynamical medium model (QMRT).

```
┌─────────────────────────────────────────────────────────────────┐
│                         PAPER 1                                 │
│               "How Structures Form"                             │
│                                                                 │
│  • Births correlate with ρ peaks (85% enrichment)              │
│  • Persistence scales with S (r = 0.65)                        │
│  • Merges occur in high ∇ρ regions                             │
│  • Statistical lifecycle model validated                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Structures form, but...
                              │ do they persist?
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PAPER 2                                 │
│             "What Sustains Structure"                           │
│                                                                 │
│  • Undriven: S → 0, I_TS → 0 (organization decays)             │
│  • Activity persists at 80% (births/deaths continue)           │
│  • Driven: S maintained at ~0.002                               │
│  • Periodic ≈ Random: energy magnitude dominates               │
│  • S_late ∝ P^0.15                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Organization requires driving, but...
                              │ what is its spatial structure?
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PAPER 3                                 │
│          "Spatial Coherence and Constraints"                    │
│                                                                 │
│  • Driving creates 70× gradient magnitude                       │
│  • Driving creates 135× directional coherence                   │
│  • Cluster morphology UNCHANGED (AR ~ 2-3)                      │
│  • Localized driving FAILS (waves spread energy)               │
│  • Theoretical constraint: no matter-like localization         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Claims

### Paper 1
> Structure formation follows predictable statistical laws: births at energy peaks, persistence with organization, merges in gradient regions.

### Paper 2
> Structure maintenance requires sustained energy input. Activity ≠ Organization: event rates persist while spatial coherence decays without driving.

### Paper 3
> Driving creates gradient coherence (70× magnitude, 135× alignment) without morphological elongation. Linear wave dynamics cannot localize energy—matter-like structures require nonlinear or topological mechanisms.

---

## Connection

| Question | Paper 1 | Paper 2 | Paper 3 |
|----------|---------|---------|---------|
| What causes births? | ρ peaks | — | — |
| What determines persistence? | S level | — | — |
| What causes merges? | ∇ρ gradients | — | — |
| Does organization persist? | — | No (decays to 0) | — |
| What sustains organization? | — | Energy input | — |
| What is the spatial structure? | — | — | Aligned blobs, not filaments |
| Can organization be localized? | — | — | No (waves spread) |

---

## Key Results Summary

### Paper 1 Statistics
| Test | Result | Significance |
|------|--------|--------------|
| Birth vs ρ | 85% enrichment | p < 10⁻¹⁰ |
| Persistence vs S | r = 0.65 | Strong positive |
| Merge vs ∇ρ | Gradient-dominated | Verified |

### Paper 2 Dynamics
| Condition | S_late | I_TS_late |
|-----------|--------|-----------|
| Undriven | ~0 | ~0 |
| Driven | 0.002 | 0.80 |
| Periodic vs Random | 0.97 ratio | — |

### Paper 3 Spatial Structure
| Metric | Undriven | Driven | Ratio |
|--------|----------|--------|-------|
| Gradient magnitude | 1.2 | 84.0 | **70×** |
| Directional coherence | 0.001 | 0.186 | **135×** |
| Cluster aspect ratio | 2.2 | 2.3 | ~1× |
| Localization contrast | — | 1.4× | **Fails** |

---

## Implications

1. **Emergent structures are transient** without sustained input
2. **Activity does not imply organization** — these decouple
3. **Energy magnitude governs maintenance** (not temporal pattern)
4. **Organization is non-conserved** — requires throughput
5. **Driving creates coherence, not morphology** — gradients align, shapes don't elongate
6. **Localization is not supported** — wave propagation spreads energy

---

## Theoretical Constraint (Paper 3)

> **Linear wave propagation + relaxation dynamics cannot produce matter-like localized structures.**

For localization, future models require:
- Topological defects (vortex cores as "matter")
- Nonlinear self-interaction (solitons via φ⁴ terms)
- Modified dispersion (non-propagating modes)

---

## File Structure

```
/paper1/
  PAPER1_draft.md
  VALIDATION_REPORT.md
  figures/
  data/

/paper2/
  PAPER2_final.md
  figures/
  data/

/paper3/
  PAPER3_draft.md
  LOCALIZED_DRIVING_REPORT.md
  data/
    extended_cluster_analysis.json
    localized_driving_result.json

/phase2/
  EXTENDED_ANALYSIS_REPORT.md (directional coherence findings)
  CLUSTER_ANALYSIS_REPORT.md

/combined/
  OVERVIEW.md (this file)
```

---

## Next Steps: Topological Approach

With the current model's constraints established, the next theory branch investigates:

**"Matter as Topological Defects"**

Instead of "matter = localized energy", explore "matter = vortex cores":
- Vortices are already detected in the model
- They have chirality, stability scores
- They may provide natural localization via topology

This approach is motivated by the Paper 3 finding that simple localization fails.

---

## Graphical Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    UNDRIVEN                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Activity: ████████████████████████████  (~80%)      │   │
│  │ Organization S: ██░░░░░░░░░░░░░░░░░░░░  (→ 0)       │   │
│  └─────────────────────────────────────────────────────┘   │
│  Events continue, but structure vanishes                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     DRIVEN                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Activity: ████████████████████████████████████      │   │
│  │ Organization S: ████████████████████  (maintained)  │   │
│  └─────────────────────────────────────────────────────┘   │
│  Energy input sustains structure                            │
└─────────────────────────────────────────────────────────────┘

           PAPER 3: What is the spatial structure?

┌─────────────────────────────────────────────────────────────┐
│                  DRIVEN SPATIAL STRUCTURE                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Gradient magnitude: ████████████████████  (70×)     │   │
│  │ Directional coherence: █████████████████  (135×)    │   │
│  │ Morphology (AR): ██░░░░░░░░░░░░░░░░░░░░  (~1×)      │   │
│  │ Localization: ░░░░░░░░░░░░░░░░░░░░░░░░  (FAILS)    │   │
│  └─────────────────────────────────────────────────────┘   │
│  Aligned blobs, not filaments. Waves spread, can't localize │
└─────────────────────────────────────────────────────────────┘

              S_late ∝ P^0.15 | Coherence = 0.19
```

---

## Authors

QMRT Simulation Lab

## Date

April 2026
