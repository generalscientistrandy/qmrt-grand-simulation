# Phase 9, Gate 2: Driven Non-Equilibrium Scaffold

**Date**: December 2025  
**Status**: MILESTONE ACHIEVED

---

## Core Finding

> **The filamentary proto-spacetime scaffold is not a conservative equilibrium structure but a driven non-equilibrium regime that rebuilds and persists under continuous injection.**

---

## Experimental Results

### Gate 1: Undriven Dynamics (Decay)

| Epoch | Population | Dimension | Triangles | Edges |
|-------|------------|-----------|-----------|-------|
| 1 | 245 | 1.19 | 18,259 | 3,173 |
| 2 | 142 | 1.18 | 8,682 | 1,821 |
| 3 | 79 | 1.11 | 4,004 | 1,059 |
| 4 | **30** | **1.01** | **751** | **322** |

**Finding**: Without driving, the scaffold decays toward a sparse, near-empty state.

### Gate 2: Driven Dynamics (Maintenance/Build-up)

| Epoch | Population | Dimension | Triangles | Edges |
|-------|------------|-----------|-----------|-------|
| 1 | 19 | 0.28 | 13 | 20 |
| 2 | 39 | 0.43 | 55 | 63 |
| 3 | 66 | 0.67 | 278 | 182 |
| 4 | **124** | **0.97** | **1,100** | **547** |

**Finding**: With continuous injection, the scaffold rebuilds and grows. Effective dimension approaches ~1D as population builds.

---

## Three Key Results

### 1. Undriven Decay

Without continuous injection:
- Population collapses (245 → 30)
- Triangles collapse (18,259 → 751)
- Edges collapse (3,173 → 322)
- The scaffold tends toward emptiness

### 2. Driven Maintenance/Build-up

With continuous injection (5 vortices every 50 steps):
- Population grows (19 → 124)
- Triangles grow (13 → 1,100)
- Edges grow (20 → 547)
- The scaffold rebuilds and exceeds undriven late-time state

### 3. Filamentary Regime as Emergent Driven State

As population builds under driving:
- Effective dimension rises: 0.28 → 0.97
- Approaches the ~1D filamentary regime from Phase 7
- **The ~1D structure is not an initial condition—it emerges as the driven state builds**

---

## Conceptual Bridge

This result connects three key program findings:

| Phase | Finding | Connection |
|-------|---------|------------|
| Papers 1–5 | Persistence requires energy input | Confirmed: undriven → decay |
| Phase 7 | Filamentary metric-like regime | Confirmed: ~1D emerges as driven state |
| Phase 9 | Driven non-equilibrium scaffold | **New**: the regime is maintained, not self-sustaining |

---

## Interpretation

The proto-spacetime filamentary scaffold is analogous to a **dissipative structure**:
- Requires continuous energy input (injection)
- Maintains organized structure far from equilibrium
- Without driving, relaxes toward disorder (empty state)
- The ~1D geometry is the natural organizational mode of the driven regime

---

## Open Question: Steady State

The driven scaffold at Epoch 4 is still growing:
- Population: +567% over 4 epochs
- Not yet saturated

**Next question**: What is the carrying capacity / steady state of the driven scaffold?

---

## Program Progression

| Level | Phase | Achievement |
|-------|-------|-------------|
| 1 | Papers 1–5 | Active selective environment |
| 2 | Phase 6 | Proto-spacetime organizational regime |
| 3 | Phase 7 | Metric-like filamentary geometry + organizational phases |
| 4 | Phase 8 | Robust ~1D boundary (stabilization mechanisms fail) |
| **5** | **Phase 9 Gate 2** | **Driven non-equilibrium scaffold** |

---

## Scripts

- `phase9_gate1_natural.py` — Undriven decay observation
- `phase9_gate2_driven.py` — Driven scaffold dynamics

---

## Conclusion

**The filamentary proto-spacetime scaffold is a driven non-equilibrium structure.** It requires continuous injection to persist; without driving, it decays. With driving, it rebuilds and approaches the ~1D filamentary regime established in Phase 7. The effective dimension (~1D) is not an equilibrium property but an emergent feature of the driven organizational state.

---

**Gate 2 Status: FROZEN**  
**Date: December 2025**
