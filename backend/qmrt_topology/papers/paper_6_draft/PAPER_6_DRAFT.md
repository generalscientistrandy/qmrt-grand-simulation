# Paper 6: The Proto-Spacetime Scaffold

## Geometric Structure and Driven Dynamics of the QMRT Medium

**Status**: DRAFT  
**Date**: December 2025

---

## Abstract

We investigate the geometric structure that emerges from the active selective environment established in Papers 1–5. Through systematic testing across four phases, we establish that the QMRT medium supports a **proto-spacetime organizational regime**: a driven, metric-like, filamentary non-equilibrium scaffold. This regime exhibits (1) relational geometry where graph distance encodes spatial distance, (2) robust ~1D filamentary organization that resists promotion to higher dimensions, (3) phase-dependent organizational control distributed across position, coupling, and resonance degrees of freedom, and (4) bounded topological carrying capacity under sustained driving. We conclude that the proto-spacetime scaffold is not a conservative equilibrium structure but a dissipative regime maintained by continuous energy input.

---

## 1. Introduction

Papers 1–5 established that the QMRT medium exhibits **active selective environment** properties: topological defects persist through protection mechanisms, populations self-regulate through carrying capacity and niche differentiation, and the medium exhibits memory, regeneration, and attractor-based spatial control.

This paper addresses the next-level question: **What kind of geometric regime emerges from such an active medium?**

We report results from Phases 6–9 of the program, which systematically characterize:
- Whether collective organization produces proto-spacetime structure (Phase 6)
- Whether that structure has metric-like geometric properties (Phase 7)
- Whether higher-dimensional geometry can be induced (Phase 8)
- Whether the structure is an equilibrium or driven regime (Phase 9)

The central finding is that the medium supports a **proto-spacetime scaffold**—a driven non-equilibrium structure with metric-like relational properties, robust filamentary (~1D) geometry, and bounded carrying capacity.

---

## 2. Proto-Spacetime Organization (Phase 6)

### 2.1 Collective Structure

Phase 6 tested whether defect populations form collective organizational regimes beyond individual persistence.

**Gate 1 (Clustering)**: Defect networks exhibit significant clustering (coefficient ~0.57), indicating local redundancy and non-random connectivity.

**Gate 2 (Persistence)**: Relational networks persist over extended timescales, with stable community structure and hub nodes.

**Gate 3 (Hierarchy)**: Multi-scale organization emerges, with hierarchical clustering at different coarse-graining levels.

**Gate 4 (Regime Transitions)**: Different forcing conditions (pressure, confinement, contrast) produce distinct organizational regimes.

### 2.2 Phase 6 Conclusion

The defect population forms a **proto-spacetime organizational regime**: a persistent, hierarchically organized relational network that responds to forcing through regime transitions rather than simple parameter scaling.

---

## 3. Metric-Like Filamentary Geometry (Phase 7)

### 3.1 Metric Properties

Phase 7 tested whether the organizational regime exhibits genuine geometric structure.

**Gate 1 Results**:

| Test | Result | Interpretation |
|------|--------|----------------|
| Graph-Euclidean correlation | r = 0.85 | Strong metric encoding |
| Monotonicity | 10/10 samples | Perfect ordering |
| Locality (long-range edges) | 0.0% | No shortcuts |
| Coarse-graining stability | r = 0.51 | Robust at multiple scales |
| Scaling exponent | d ≈ 1.1 | Filamentary (~1D) |

The network behaves like a **metric space**: graph distance faithfully encodes spatial distance.

### 3.2 Universal Filamentary Structure

**Gates 2–3** tested whether the ~1D dimension is universal or regime-dependent.

| Forcing Axis | Parameter Range | Dimension Range |
|--------------|-----------------|-----------------|
| Pressure | 10–75 vortices | 1.01–1.15 |
| Confinement | 10–35% radius | 1.05–1.10 |
| Coupling contrast | Δκ = 0.1–0.9 | 1.05–1.10 |
| Triple extreme | All combined | 1.10–1.21 |

The filamentary structure is **robust across all tested forcing regimes**. Even extreme combined forcing does not induce a transition to higher-dimensional geometry.

### 3.3 Organizational Phases

**Gates 4–5** characterized which degrees of freedom control network organization.

**DoF Hierarchy** (baseline):
- Position (geometric): 0.42 score
- Coupling (κ-landscape): 0.34 score  
- Resonance (channel state): 0.33 score
- Topology/memory: negligible

**Phase-Dependent Control**:

| Forcing Regime | Dominant Control |
|----------------|------------------|
| Baseline | HYBRID (position ≈ coupling ≈ resonance) |
| Confinement extreme | RESONANCE-dominated |
| Triple extreme | GEOMETRIC-dominated |

Organization is **hybrid and phase-dependent**: different forcing regimes produce different DoF hierarchies while maintaining the same ~1D spatial structure.

### 3.4 Key Conceptual Distinction

Phase 7 established an important distinction:

- **Spatial dimension**: How structure extends in position space (~1D, filamentary)
- **Effective degrees of freedom**: Independent channels for organization (multiple: position, coupling, resonance, topology, memory)

The richer behavior of the medium is carried by **non-spatial degrees of freedom**, not by higher spatial dimensionality.

---

## 4. Robust ~1D Boundary (Phase 8)

### 4.1 Attempted Dimensional Promotion

Phase 8 tested whether mechanisms designed to promote cross-filament connectivity could raise effective dimension.

**Gate 1 (Cross-link stabilization)**:
- Dimension: 1.18 → 1.33 (+13%)
- Triangles: 17,089 → 8,176 (-52%)
- Edges: 3,053 → 1,970 (-35%)

**Gate 2 (Loop/motif stabilization)**:
- Dimension: 1.18 → 1.51 (+28%)
- Triangles: 17,089 → 4,698 (-72%)
- Edges: 3,053 → 1,444 (-53%)

### 4.2 False Positive Identification

Both mechanisms produced **false positives**: dimension appeared to increase, but triangles and edges decreased. The apparent dimension increase was an artifact of sparser, more diffuse networks—not true 2D enrichment.

**Diagnostic finding**: The dimension estimator (neighborhood scaling) can be fooled by sparse networks that extend farther per hop without being genuinely higher-dimensional.

### 4.3 Phase 8 Conclusion

Within the current mechanism family, **attempts to promote higher-dimensional organization do not produce true enrichment**. The ~1D filamentary structure is robust—a boundary property of this regime.

---

## 5. Driven Scaffold Dynamics (Phase 9)

### 5.1 Undriven Decay

Phase 9 tested the dynamical nature of the scaffold.

**Gate 1 (Undriven)**:

| Epoch | Population | Dimension | Triangles |
|-------|------------|-----------|-----------|
| 1 | 245 | 1.19 | 18,259 |
| 4 | 30 | 1.01 | 751 |

Without continuous injection, the scaffold **decays toward emptiness**: population drops 88%, triangles drop 96%.

### 5.2 Driven Maintenance

**Gate 2 (Driven)**:

| Epoch | Population | Dimension | Triangles |
|-------|------------|-----------|-----------|
| 1 | 19 | 0.28 | 13 |
| 4 | 124 | 0.97 | 1,100 |

With continuous injection (5 vortices / 50 steps), the scaffold **rebuilds and grows**. Effective dimension rises toward ~1D as population builds.

### 5.3 Steady State

**Gate 3 (Extended)**:

| Epoch | Population | Dimension | Triangles |
|-------|------------|-----------|-----------|
| 6 | 125 | 0.98 | 1,208 |
| 8 | 190 | 1.12 | 3,888 |

The driven scaffold approaches a **bounded steady state**:
- Carrying capacity: ~180–200 defects
- Steady-state dimension: ~1.1–1.2
- Growth slows as population saturates

### 5.4 Phase 9 Conclusion

The proto-spacetime scaffold is a **driven non-equilibrium steady state (NESS)**:
- Requires continuous energy input
- Decays without driving
- Approaches bounded population under sustained driving
- The ~1D filamentary structure emerges as the natural organizational mode

---

## 6. Interpretation

### 6.1 The Proto-Spacetime Scaffold

The QMRT medium supports a geometric regime with the following properties:

| Property | Finding |
|----------|---------|
| **Relational geometry** | Graph distance encodes spatial distance (r = 0.85) |
| **Filamentary structure** | Effective dimension ~1.1 (robust) |
| **Phase-dependent control** | Hybrid DoF hierarchy with regime transitions |
| **Driven maintenance** | Requires continuous injection to persist |
| **Bounded capacity** | ~180–200 defects under current driving |

### 6.2 Not an Inert Substrate

The scaffold is **not** a passive geometric background:
- It actively selects which defects persist
- It exhibits memory and regeneration
- It responds to forcing through organizational phase transitions
- It requires driving to maintain structure

### 6.3 Dimensions as Degrees of Freedom

The ~1D spatial geometry coexists with rich organizational behavior because:
- Spatial dimension measures how structure extends in position space
- Organizational complexity is carried by non-spatial degrees of freedom
- Multiple DoFs (position, coupling, resonance, memory) contribute to organization

This suggests that **what are often described as extra dimensions may, in some frameworks, be more naturally interpreted as additional degrees of freedom of the underlying medium**.

### 6.4 Dissipative Structure Analogy

The scaffold behaves like a **dissipative structure**:
- Maintained far from equilibrium by energy input
- Exhibits organized structure that would decay without driving
- The organization is the driven state, not a conservative equilibrium

---

## 7. Limits and Caveats

### 7.1 Model-Specific

These results are established within the QMRT simulation framework. Generalization to other systems requires separate investigation.

### 7.2 Filamentary, Not Space-Filling

The geometry is metric-like but remains ~1D filamentary in 3D embedding space. We have not demonstrated:
- True 2D or 3D space-filling geometry
- Transition mechanisms to higher dimensions
- Whether higher-dimensional regimes exist in other parameter regions

### 7.3 No Matter-Like Bound States

The scaffold provides a relational geometric structure, but we have not demonstrated:
- Matter-like localized excitations
- Propagating degrees of freedom
- Particle-like phenomenology

### 7.4 Approximate Quantitative Estimates

Carrying capacity (~180–200 defects) and other quantitative estimates are provisional. Longer runs or different driving rates may refine these values.

### 7.5 Not Full Spacetime

We describe a **proto-spacetime** scaffold—a geometric precursor with metric-like properties—not a complete spacetime with all expected physical structure.

---

## 8. Conclusion

We have established that the QMRT medium supports a **proto-spacetime scaffold**: a driven, metric-like, filamentary non-equilibrium structure.

### Three Central Results

1. **The proto-spacetime regime exists**: Defect populations form persistent, hierarchically organized relational networks with metric-like geometric properties.

2. **It is robustly filamentary**: Effective dimension remains ~1.1 across all tested forcing regimes. Attempted promotion mechanisms produce artifacts, not true enrichment.

3. **It is a driven non-equilibrium scaffold**: The structure requires continuous energy input to persist. Without driving, it decays; with driving, it approaches a bounded steady state.

### Synthesis Statement

> The proto-spacetime regime of the QMRT medium is a driven, metric-like, filamentary non-equilibrium scaffold: it exhibits relational geometry, robust ~1D organization, phase-dependent control structure, and bounded topological carrying capacity under sustained driving.

This establishes the geometric character of the active selective environment: not a static equilibrium geometry, but a maintained dissipative structure with metric-like relational properties and rich organizational degrees of freedom.

---

## References

- Paper 1: Topological Protection and Localization
- Paper 2: Memory and Regeneration
- Paper 3: Multi-Scale Organization
- Paper 4: Attractor-Based Spatial Control
- Paper 5: Active Selective Environment
- Phase 6 Milestone: Proto-Spacetime Organizational Regime
- Phase 7 Conclusion: Metric-Like Filamentary Geometry
- Phase 8 Conclusion: Robust ~1D Boundary
- Phase 9 Conclusion: Driven Non-Equilibrium Scaffold

---

**Paper 6 Status**: DRAFT  
**Date**: December 2025
