# Why Filamentary? A Framework Note

**Date**: December 2025  
**Status**: EXPLORATORY

---

## The Question

Paper 6 established that the proto-spacetime scaffold is:
- Metric-like (graph distance encodes spatial distance)
- Robustly filamentary (~1D effective dimension)
- Phase-dependent in organization but not in spatial geometry
- Driven non-equilibrium (requires continuous injection)

The central open question is: **Why does the medium prefer ~1D filamentary organization?**

This note explores possible explanations and identifies testable hypotheses.

---

## Observed Facts

### What We Know

1. **Effective dimension is ~1.1** across all tested forcing regimes
2. **Forcing enriches local structure** (more triangles, higher degree) but does not change global dimension
3. **Attempted promotion mechanisms** produced sparser networks (false positives)
4. **Organizational control is hybrid** but spatial geometry is invariant
5. **The scaffold decays without driving** and rebuilds under continuous injection

### What This Suggests

The ~1D preference is:
- Not an artifact of baseline parameters (universal across forcing)
- Not due to insufficient forcing (triple extreme still ~1.2)
- Not easily overridden by stabilization mechanisms
- Apparently intrinsic to the current dynamical regime

---

## Candidate Explanations

### Hypothesis A: Locality Constraint

**Claim**: The ~1D structure arises because defect interactions are strictly local.

**Mechanism**: 
- Defects can only connect to nearby defects (adjacency radius ~10 units)
- This locality constraint naturally produces chain-like growth
- Cross-filament connections would require defects to "reach across" empty space
- The dynamics don't support long-range edge formation

**Prediction**: If adjacency radius is increased, effective dimension should rise.

**Test**: Run simulations with larger adjacency radius and measure dimension.

---

### Hypothesis B: Energetic Cost

**Claim**: Cross-filament connections are energetically unfavorable.

**Mechanism**:
- The protection mechanism (coupling × topology × channel) is optimized for chain continuation
- Maintaining a defect in a triangular configuration requires more "energy" than in a chain
- The system minimizes total cost by favoring linear extension

**Prediction**: If protection is made uniform (no coupling gradient), dimension should rise.

**Test**: Run simulations with flat coupling field and measure dimension.

---

### Hypothesis C: Topological Persistence

**Claim**: Winding/vorticity conservation favors linear propagation.

**Mechanism**:
- Topological defects have conserved winding number
- Linear filaments conserve topology along their length
- Branching or cross-linking would require topological splitting/merging
- The dynamics suppress topological transitions

**Prediction**: If topological constraints are relaxed (e.g., by allowing winding decay), dimension should rise.

**Test**: Add a winding dissipation term and measure dimension.

---

### Hypothesis D: DoF Decoupling

**Claim**: Spatial dimension and organizational DoFs are naturally decoupled.

**Mechanism**:
- The system has multiple organizational degrees of freedom (coupling, resonance, memory)
- Richer behavior is "carried" by non-spatial DoFs rather than by spatial extension
- There is no selective pressure to increase spatial dimension because organizational complexity can be achieved through internal DoFs

**Prediction**: This is more an interpretive frame than a testable mechanism. It suggests the question "why not 2D?" may be ill-posed—the system doesn't "need" higher spatial dimension.

**Implication**: Accept ~1D as the natural state and ask what structures build ON TOP of it.

---

### Hypothesis E: Layered Branching Deficit

**Claim**: Higher-dimensional organization requires recursive branching layers that the current dynamics don't support.

**Mechanism**:
- 1D → 2D transition requires "branching of filaments" (cross-linking)
- 2D → 3D transition requires "branching of sheets" (volume-filling)
- The current dynamics only support the first layer (filament formation)
- A new dynamical layer would be needed to enable the 1D → 2D transition

**Prediction**: If a specific cross-link stabilization layer is added (different from Phase 8 attempts), dimension might rise.

**Test**: Design a mechanism that explicitly tracks filament identity and rewards inter-filament connections.

---

## Assessment of Hypotheses

| Hypothesis | Plausibility | Testability | Priority |
|------------|--------------|-------------|----------|
| A (Locality) | Medium | High | Test first |
| B (Energetic cost) | Medium | Medium | Test second |
| C (Topological persistence) | High | Medium | Important |
| D (DoF decoupling) | High | Low (interpretive) | Framework |
| E (Layered branching) | High | Was tested (Phase 8), needs redesign | Later |

---

## Recommended Investigation Order

### 1. Test Hypothesis A (Locality)

Run baseline simulation with adjacency radius 15 and 20 (instead of 10).
- If dimension rises → locality is the constraint
- If dimension stays ~1.1 → locality is not the bottleneck

### 2. Test Hypothesis B (Energetic Cost)

Run simulation with flat coupling (κ = 0.5 everywhere).
- If dimension rises → coupling gradient favors filaments
- If dimension stays ~1.1 → coupling is not the cause

### 3. Consider Hypothesis D as Working Frame

If A and B fail, adopt Hypothesis D as the interpretive frame:
- ~1D is the natural spatial mode
- Organizational richness is carried by non-spatial DoFs
- The question becomes: what structures emerge ON the filamentary scaffold?

### 4. Revisit Hypothesis E Only If Needed

The Phase 8 attempts failed because they produced sparse artifacts. A redesigned mechanism would need to:
- Explicitly track which defects are on the same filament
- Reward edges between different filaments (not just high-topology regions)
- Ensure the mechanism increases triangles AND dimension together

---

## Deeper Question: Is ~1D Fundamental?

If all hypotheses fail to explain a route to higher dimension, we may conclude:

> **The ~1D filamentary geometry is a fundamental property of this dynamical regime, not a parameter artifact or insufficiently explored boundary.**

This would be a significant theoretical result: the proto-spacetime scaffold naturally produces metric-like relational structure, but that structure is intrinsically filamentary.

The question then becomes:
- Is this specific to QMRT or a general feature of topological medium dynamics?
- Does physical spacetime require a different class of dynamics?
- Can higher-dimensional structure be built hierarchically ON the ~1D scaffold?

---

## Connection to Paper 6

Paper 6 established the empirical arc. This note opens the interpretive/theoretical arc:

| Paper 6 (Empirical) | This Note (Theoretical) |
|---------------------|-------------------------|
| The scaffold IS ~1D | WHY is it ~1D? |
| Promotion fails | WHY does promotion fail? |
| Dynamics are driven | WHAT does driving maintain? |
| Organization is hybrid | HOW do DoFs relate to dimension? |

---

## Status

This is an **exploratory framework note**, not a completed investigation.

**Next steps**:
1. Test Hypothesis A (adjacency radius)
2. Test Hypothesis B (flat coupling)
3. Adopt Hypothesis D as working frame if tests fail
4. Consider whether ~1D is fundamental

---

**Note Status**: EXPLORATORY  
**Date**: December 2025
