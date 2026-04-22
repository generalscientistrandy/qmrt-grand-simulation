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
                              │ can it be localized?
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PAPER 3                                 │
│      "Localization via Coupling Asymmetry"                      │
│                                                                 │
│  • External driving FAILS to localize (S contrast 1.4×)        │
│  • β asymmetry SUCCEEDS (S contrast 14-32×)                    │
│  • Energy uniform, organization localized (DECOUPLING)          │
│  • Threshold: β contrast ≥ 1.33×, linear scaling               │
│  • Multiple regions: NO INTERACTION                             │
│  • Result: ORGANIZATION WELLS, not particles                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Claims

### Paper 1
> Structure formation follows predictable statistical laws: births at energy peaks, persistence with organization, merges in gradient regions.

### Paper 2
> Structure maintenance requires sustained energy input. Activity ≠ Organization: event rates persist while spatial coherence decays without driving.

### Paper 3
> Spatial asymmetry in coupling strength β localizes organization (S contrast up to 32×) while energy remains uniform. Multiple biased regions show no interaction—they are parameter-induced organization wells, not particles. Matter-like behavior requires physics beyond the current model.

---

## Connection

| Question | Paper 1 | Paper 2 | Paper 3 |
|----------|---------|---------|---------|
| What causes births? | ρ peaks | — | — |
| What determines persistence? | S level | — | — |
| What causes merges? | ∇ρ gradients | — | — |
| Does organization persist? | — | No (decays to 0) | — |
| What sustains organization? | — | Energy input | — |
| Can organization be localized? | — | — | YES (via β asymmetry) |
| Do localized regions interact? | — | — | NO (independent wells) |

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

### Paper 3 Localization
| Method | S Contrast | ρ Contrast | Interaction? |
|--------|------------|------------|--------------|
| External driving | 1.4× | ~1× | N/A |
| β asymmetry (single) | 14-32× | ~1× | N/A |
| β asymmetry (multiple) | 14× each | ~1× | **None** |

| Parameter | Threshold | Scaling |
|-----------|-----------|---------|
| β contrast | ≥ 1.33× | Linear: S ≈ 2 + 4×(β-1) |

---

## Implications

1. **Emergent structures are transient** without sustained input
2. **Activity does not imply organization** — these decouple
3. **Energy magnitude governs maintenance** (not temporal pattern)
4. **Organization is non-conserved** — requires throughput
5. **Energy and organization decouple** — same energy, different structure based on local β
6. **Localization via β asymmetry works** — up to 32× S contrast
7. **No interaction between localized regions** — organization wells, not particles

---

## Theoretical Constraint (Paper 3)

> **β asymmetry localizes organization, but produces independent wells, not interacting particles.**

The current model CAN:
- Localize organization (via β asymmetry)
- Decouple energy from organization
- Create persistent regional differentiation

The current model CANNOT:
- Produce interaction between localized regions
- Create conservation-like behavior
- Support particle dynamics

For matter-like structures, future models require:
- Topological defects (vortex cores as "matter")
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
