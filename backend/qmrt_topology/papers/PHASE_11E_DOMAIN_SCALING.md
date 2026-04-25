# Phase 11e: Domain Scaling Test — Results

**Date: December 2025**
**Status: COMPLETE (Unexpected Result)**

---

## Key Finding: Transition Does NOT Scale with Volume

| Domain | Volume | Predicted Transition | Observed Transition |
|--------|--------|---------------------|---------------------|
| 48³ | 110,592 | ~400 | ~400 |
| 64³ | 262,144 | ~950 (2.37× scaling) | **~250** |

**The transition occurred EARLIER on the larger grid, not later!**

---

## What This Means

### The Prediction Failed

If the transition were purely geometric packing:
- Larger volume → more room → later transition
- Expected: 400 × (64³/48³) ≈ 950 defects

Instead:
- Transition at ~250 defects (earlier than 48³!)
- Loops dominant only at very low population (64-244 defects)
- Clustering dominates almost immediately

### Possible Interpretations

#### 1. NOT Pure Packing — Something Else Matters

The transition is NOT simply "when nodes get too close". Other factors:
- **Boundary effects**: Larger domain may have different edge behavior
- **Coupling gradient**: Interior region scales differently
- **τ dynamics**: Medium responds differently at different scales

#### 2. Packing Threshold is ABSOLUTE, not Volume-Relative

The transition may occur at a fixed **density** threshold, not a fixed population.

On 64³: 
- Transition at ~250 defects
- Avg distance ~28-29 at transition
- Density ~0.003-0.004

On 48³:
- Transition at ~400 defects  
- Avg distance ~22-23 at transition
- Density ~0.006-0.007

**Wait — the densities are LOWER on 64³!** This suggests the larger domain allows defects to spread out more, reaching lower density at similar populations. But the transition still happened earlier.

#### 3. Interior Region Size May Be Key

The coupling gradient creates an interior region:
- 48³: interior_r = 12 (diameter 24)
- 64³: interior_r = 16 (diameter 32)

Interior volume ratio: (16/12)³ = 2.37× (same as full volume)

But the **attractor dynamics** may not scale simply.

---

## Revised Interpretation

The transition is NOT driven by simple packing density. Instead:

**The transition may be driven by the INTERIOR attractor dynamics** — how defects organize within the high-coupling region, which has complex boundary effects.

This suggests:
1. **Geometry is still the leading branch** — but it's attractor geometry, not raw packing
2. **The coupling gradient creates a "container"** — and the container's dynamics matter
3. **Scaling is NOT simple** — domain size changes the attractor landscape

---

## Data Summary (64³ Run)

| Population Band | Loop | Balanced | Clust | Avg L-C |
|-----------------|------|----------|-------|---------|
| 0-200 | 1 | 0 | 0 | +1.497 |
| 200-500 | 1 | 2 | 1 | -0.005 |
| 500-800 | 0 | 0 | 2 | -0.361 |
| 800-1200 | 0 | 1 | 2 | -0.245 |
| 1200-2000 | 0 | 0 | 10 | -0.353 |

**Loop dominance only at very low population (< 250)**
**Clustering dominates from ~250 onwards**

---

## Theoretical Implications

### Geometry is Still Primary, But...

The "geometry as leading branch" hypothesis needs refinement:

> It's not raw packing that drives the transition. It's the **relational geometry within the attractor region** — how the coupling gradient shapes structure formation.

The attractor landscape (high-coupling interior vs. low-coupling periphery) creates a "container" for structure. The container's geometry — not just the defect packing — determines when loops give way to clustering.

### Domain Size Changes the Attractor Dynamics

Larger domains may:
- Have different boundary-interior interaction
- Support different wave-speed distributions
- Allow different modes of structure formation

This is more complex than simple packing.

---

## Next Steps to Resolve

1. **Same-density comparison**: Run 48³ and 64³ at matched density, not matched population
2. **Interior-only analysis**: Measure L-C only for defects inside the interior region
3. **Coupling gradient analysis**: How does the transition correlate with position within the attractor?

---

## Summary Statement

**The domain scaling test shows that the Loop→Clustering transition does NOT scale simply with volume. On a 64³ grid, the transition occurred at ~250 defects (EARLIER than the 48³ transition at ~400). This refutes simple packing-density scaling and suggests the transition is governed by attractor geometry — the interaction between the coupling gradient and structure formation dynamics — rather than raw defect crowding.**

---

*Phase 11e Complete — December 2025*
