# QMRT Papers: Overview

## Two-Paper Arc

This package contains two complementary papers investigating emergent structure in a dynamical medium model (QMRT).

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
```

---

## Core Claims

### Paper 1
> Structure formation follows predictable statistical laws: births at energy peaks, persistence with organization, merges in gradient regions.

### Paper 2
> Structure maintenance requires sustained energy input. Activity ≠ Organization: event rates persist while spatial coherence decays without driving.

---

## Connection

| Question | Paper 1 | Paper 2 |
|----------|---------|---------|
| What causes births? | ρ peaks | — |
| What determines persistence? | S level | — |
| What causes merges? | ∇ρ gradients | — |
| Does organization persist? | — | No (decays to 0) |
| What sustains organization? | — | Energy input |
| Does activity = organization? | — | No (separation) |

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

---

## Implications

1. **Emergent structures are transient** without sustained input
2. **Activity does not imply organization** — these decouple
3. **Energy magnitude governs maintenance** (not temporal pattern)
4. **Organization is non-conserved** — requires throughput

---

## File Structure

```
/paper1/
  PAPER1_draft.md
  VALIDATION_REPORT.md
  figures/
    fig1_birth_histogram.png
    fig2_lifetime_S.png
    ...
  data/
    *.json

/paper2/
  PAPER2_final.md
  figures/
    fig1_S_decay.png
    fig2_ITS_decay.png
    fig3_activity_vs_S.png
    fig4_energy_matched.png
    fig5_power_vs_S.png
  data/
    robustness_controls.json
    structural_decay_analysis.json
    ...

/combined/
  OVERVIEW.md (this file)
```

---

## Next Steps (Phase 2)

With temporal dynamics established, the next phase addresses spatial patterns:

1. **Cluster metrics** (no labels yet):
   - Cluster persistence time
   - Cluster size distribution
   - Spatial correlation anisotropy

2. **Driven vs undriven comparison**:
   - Do clusters only persist under driving?
   - Does cluster size scale with power?

3. **Filament-like behavior** (if metrics support):
   - Based on anisotropy + connectivity
   - Not visual interpretation

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

                    S_late ∝ P^0.15
```

---

## Authors

QMRT Simulation Lab

## Date

April 2026
