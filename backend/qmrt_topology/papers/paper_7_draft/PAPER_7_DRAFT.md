# Paper 7: Dimensional Branching Under Full QMRT Mechanism

**Date**: December 2025  
**Status**: DRAFT

---

## Abstract

Under the full QMRT mechanism—including dynamic τ field, variable effective wave speed, and active remnant memory—the medium exhibits a branching transition from lower-dimensional filamentary organization (~1.1D) to a richer regime (~1.7D) under sustained driving. This transition is a **regime property of population density and connectivity**, not a consequence of geometric expansion. Phase 10 testing ruled out simple scaffold spread as the driver; instead, dimensional organization emerges from internal structural reorganization bounded by τ-mediated self-regulation. We identify a "sweet-spot" driving rate that maximizes dimensional organization.

---

## 1. Introduction

### Background

Papers 1-6 established that the QMRT medium supports:
- Active selective environment (population ecology)
- Driven non-equilibrium scaffold (NESS)
- Metric-like filamentary geometry (~1.1D)
- Oscillatory build-up/collapse dynamics

### The Open Question

Does the medium access higher-dimensional organization? If so, what drives the transition?

### This Paper

We demonstrate that **dimensional branching is a robust QMRT feature** that survives validation under the full mechanism. Crucially, Phase 10 testing shows this is **not driven by geometric expansion** but by internal structural reorganization.

---

## 2. Implementation Fidelity and Validation

### 2.1 The Reduced Model

Previous work used a simplified simulator with:
- Constant wave speed (c² = 4.0)
- Channel assignment (active)
- Remnant field (initialized but not updated)

### 2.2 The Full Mechanism

The complete QMRT theory includes:
- **Dynamic τ field**: Medium response to energy density
- **Variable c_eff**: Wave speed c_eff = c₀√(τ/τ₀)
- **Active remnant field**: Topological memory updated each timestep

### 2.3 Validation Results

| Finding | Reduced Model | Full Mechanism | Status |
|---------|--------------|----------------|--------|
| Driven scaffold | ✓ | ✓ | **VALIDATED** |
| Dimensional branching | ✓ | ✓ | **VALIDATED** |
| Sweet-spot driving | ✓ | ✓ | **VALIDATED** |
| Post-cutoff growth | ✓ | ✗ | **RETRACTED** |

**Key insight**: Driven-state behavior is nearly identical in both models. Post-cutoff behavior differs dramatically due to τ self-regulation.

---

## 3. Dimensional Branching Under Full Mechanism

### 3.1 Method

- Grid: 48³
- Initial seeding: 25 vortices in center region
- Build phase: 1000-2500 steps with continuous driving
- Measurement: Late-time averages over 300-1000 steps

### 3.2 Results: Dimension vs Driving Rate

| Interval | Driving Rate | Population | Dimension | Tri/Node |
|----------|-------------|------------|-----------|----------|
| 50 | 0.060 | 520 | 1.46 | 1.94 |
| 100 | 0.030 | 905 | **1.72** | 2.42 |
| 200 | 0.015 | 788 | 1.69 | 2.57 |
| 500 | 0.006 | 409 | 1.57 | 4.28 |

### 3.3 Key Observations

1. **Dimensional transition exists**: Range 1.46 to 1.72 (span 0.26)

2. **Sweet-spot effect**: Interval ~100 achieves maximum dimension
   - Stronger driving (50): Lower dimension (1.46)
   - Optimal driving (100): Highest dimension (1.72)
   - Weaker driving (500): Lower dimension (1.57)

3. **Population correlates with dimension**: Higher populations enable richer connectivity

4. **Triangle enrichment at weak driving**: Interval 500 has highest tri/node (4.28) despite lower overall dimension

### 3.4 Interpretation: The Sweet-Spot Effect

The sweet-spot arises from competing factors:

**Too strong driving (interval 50)**:
- Rapid injection creates turbulent field
- Insufficient time for structure to stabilize
- High energy, low organization

**Optimal driving (interval ~100)**:
- Balance between injection and relaxation
- Population builds to high level (~900)
- Time for topological connections to form

**Too weak driving (interval 500)**:
- Insufficient injection to maintain large population
- Population limited to ~400
- Richer local structure (high tri/node) but lower global dimension

---

## 4. τ Self-Regulation

### 4.1 Mechanism

Dynamic τ creates self-limiting feedback:

```
High energy → τ increases → c_eff increases → faster dispersion
```

This prevents runaway accumulation that occurs in the reduced model.

### 4.2 Post-Cutoff Comparison

| Model | Post-Cutoff (2000 steps) |
|-------|-------------------------|
| Full mechanism | 106 defects (decay) |
| Reduced model | 1114 defects (sustained) |

### 4.3 Implication

The medium is **driven, not self-sustaining**. Without external input, the scaffold decays. The reduced-model "endogenous regeneration" was an artifact of missing self-regulation.

---

## 5. The Branching Transition

### 5.1 What the Data Show

Under sustained driving at optimal rate:
- Dimension reaches ~1.7
- Population stabilizes at ~900
- Graph-Euclidean correlation maintained (~0.65)
- Triangle enrichment present (~2.4 per node)

This is **not** a sharp phase transition but a **gradual crossover** modulated by driving rate.

### 5.2 Physical Interpretation

Effective dimension in QMRT is:
- **Not a fixed spatial property**
- A measure of **activated connectivity degrees of freedom**
- Modulated by driving rate and population level

The ~1.7D regime represents a state where the defect network has developed cross-connections beyond simple chains, but has not reached a fully 2D mesh.

---

## 6. Phase 10: Geometric Expansion Test

### 6.1 The Question

A natural hypothesis was: does geometric expansion of the scaffold activate higher dimension? If spacetime is emergent, expansion might unlock additional degrees of freedom.

### 6.2 Method

Tracked geometric expansion metrics over time:
- Occupied radius (90th percentile distance from center)
- Graph diameter (maximum graph distance)
- Relational volume (total edges)

### 6.3 Initial Appearance

Strong correlations emerged:
| Metric | Correlation with Dimension |
|--------|---------------------------|
| Graph diameter | 0.975 |
| Occupied radius | 0.871 |

### 6.4 After Controlling for Oscillation

When analyzing only peak states (population > 200), correlations **disappeared**:
| Metric | Correlation with Dimension |
|--------|---------------------------|
| Graph diameter | -0.313 |
| Occupied radius | 0.126 |

### 6.5 Interpretation

The apparent expansion-dimension coupling was an **artifact of comparing peaks to troughs**. Within stable peak states:
- Dimension range is narrow (1.45-1.65)
- Geometric extent is similar across driving rates (~31 grid units)
- The attractor landscape bounds expansion

### 6.6 Conclusion

**Dimensional branching is not driven by geometric expansion.** It is a regime property of internal structural organization—population density, connectivity, and loop richness—not scaffold spread.

---

## 7. Discussion

### 7.1 What Is Now Established

1. **The medium supports dimensional branching** from ~1.1D to ~1.7D under sustained driving

2. **A sweet-spot driving rate exists** around interval ~100 (rate 0.03 vortices/step)

3. **τ self-regulation prevents post-cutoff persistence** — the scaffold requires continuous driving

4. **Dimensional branching is NOT driven by geometric expansion** — Phase 10 ruled this out

5. **Dimension is a regime property** of internal structural organization, not scaffold extent

### 7.2 What Was Retracted

1. **Post-cutoff "endogenous regeneration"** — reduced-model artifact

2. **Self-sustaining scaffold after driving stops** — does not occur in full mechanism

3. **Expansion-dimension coupling** — artifact of oscillation phase comparison

### 7.3 Open Questions

1. Can the attractor landscape itself evolve on longer timescales or larger grids?
2. What determines the sweet-spot location mechanistically?
3. How does τ response strength affect the dimensional ceiling?

---

## 8. Conclusion

Under the full QMRT mechanism, effective dimensionality is a **driven, state-dependent regime property** of the medium. The system exhibits a branching transition from filamentary (~1.1D) to richer (~1.7D) organization under sustained driving, with a sweet-spot at intermediate driving rates. τ-mediated self-regulation stabilizes driven behavior while preventing runaway post-cutoff persistence.

Phase 10 testing ruled out simple geometric expansion as the driver. Dimension emerges from **internal structural reorganization**—population density, connectivity, and loop richness—not from the scaffold spreading into new territory.

**Core thesis**:
> Dimensional organization in the QMRT medium emerges as a driven regime property of population density and connectivity, bounded by τ self-regulation and not directly explained by simple geometric expansion of the scaffold.

---

## Files

| File | Purpose |
|------|---------|
| `full_mechanism_simulator.py` | Complete QMRT implementation |
| `dimensional_branching_full_mechanism.py` | Dimensional study |
| `phase10_expansion_test.py` | Geometric expansion test |
| `IMPLEMENTATION_FIDELITY_AUDIT.md` | Code-theory comparison |
| `TAU_SELF_REGULATION_MILESTONE.md` | τ mechanism note |
| `PHASE_10_EXPANSION_RESULTS.md` | Expansion test findings |

---

**Status**: FROZEN  
**Date**: December 2025
