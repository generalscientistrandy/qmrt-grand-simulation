# Phase 10: Geometric Expansion Test Results

**Date**: December 2025  
**Status**: INITIAL FINDINGS

---

## Central Question

Does increasing scaffold extent or relational spread activate higher effective dimension even at fixed local rules?

---

## Key Findings

### 1. Apparent Correlation is an Oscillation Artifact

When comparing all states (peaks and troughs):
| Metric | Correlation with Dimension |
|--------|---------------------------|
| Graph diameter | 0.975 |
| Occupied radius | 0.871 |
| Population | 0.855 |

**However**, these correlations disappear when analyzing only peak states (pop > 200):
| Metric | Correlation with Dimension |
|--------|---------------------------|
| Graph diameter | -0.313 |
| Occupied radius | 0.126 |
| Population | 0.072 |

**Interpretation**: The strong correlations are **artifacts of comparing peaks to troughs**, not genuine expansion-dimension coupling.

### 2. Dimension is Stable Within Peak States

Within peak states:
- Min dimension: 1.45
- Max dimension: 1.65
- Range: 0.20 (small)

This suggests dimension is a property of the **organizational regime**, not of geometric extent within that regime.

### 3. Geometric Extent is Bounded

The occupied radius in peak states is similar (~31 grid units) across different driving rates. The geometric extent appears to be **bounded by the attractor landscape**, not by driving rate.

---

## What This Means for Spacetime Expansion

### What Has NOT Been Found
- Expansion of geometric extent activating higher dimension
- Relational spread increasing degree of freedom
- Scale-factor-like expansion in graph distances

### What HAS Been Found
- Dimension is a **regime property**, stable within peak states
- Different driving rates access **the same geometric extent**
- The attractor landscape (coupling gradient) constrains expansion

### Implication

The dimensional branching (~1.1 → ~1.7) is **not driven by geometric expansion**. It appears to be driven by:
- Population density (more nodes = more potential connections)
- Driving rate (determines connectivity dynamics)
- NOT by the scaffold "spreading out" into new territory

---

## Conceptual Update

The original hypothesis was:
> "Expansion may be what unlocks higher-dimensional organization."

The evidence suggests instead:
> "Dimensional organization is determined by population dynamics and connectivity within a bounded geometric domain, not by expansion of that domain."

This doesn't rule out expansion in QMRT, but it means:
- Expansion (if it exists) may operate at a different scale
- Or through a different mechanism not captured by these observables

---

## Open Questions

1. Does the attractor landscape itself expand over longer timescales?
2. Is there a "relational expansion" that isn't captured by geometric radius?
3. Could dimension increase if the grid size were larger?

---

## Files

- `/app/backend/phase10_expansion_test.py` — Test implementation
- `/app/backend/qmrt_topology/papers/phase10_expansion_results.json` — Raw data

---

**Status**: INITIAL FINDINGS — Further investigation needed  
**Date**: December 2025
