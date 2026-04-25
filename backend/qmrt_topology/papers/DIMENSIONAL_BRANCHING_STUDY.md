# Dimensional Branching: Branch Transition Threshold Study

**Date**: December 2025  
**Status**: COMPLETE - Key Findings Documented

---

## Executive Summary

The Branch-Transition Threshold Study confirms the **Dimensional Branching Hypothesis**: the medium's effective dimension is not a fixed spatial constant but an **activated degree-of-freedom count** that rises with sustained driving.

### Key Finding

**The ~1D → ~2D transition is a gradual crossover, not a sharp phase transition.**

| Driving Interval | Driving Rate | Eff. Dimension | Regime Classification |
|------------------|--------------|----------------|----------------------|
| 1000 | 0.003 | 0.90 | Stable Filamentary |
| 700 | 0.004 | 1.18 | Oscillatory Filamentary |
| 500 | 0.006 | 1.38 | Transitional |
| **350** | **0.009** | **1.51** | **Filamentary Boundary** |
| **340** | **0.009** | **1.62** | **Transition Zone** |
| 300 | 0.010 | 1.67 | Stable 2D-like |
| 200 | 0.015 | 1.85 | Stable 2D-like |
| 100 | 0.030 | 1.89 | Stable 2D-like |

### Transition Zone Characteristics

The transition occurs around **injection interval ~345** (driving rate ~0.0087 vortices/step):

1. **Below transition (interval > 400)**: 
   - Dimension: ~1.0-1.5
   - Population: 50-150 nodes
   - Correlation: 0.7-0.85
   - Regime: Filamentary scaffold

2. **Transition zone (interval ~350-340)**:
   - Dimension: ~1.5-1.6
   - Population: 150-175 nodes
   - Correlation: 0.70-0.75
   - Regime: Intermediate

3. **Above transition (interval < 330)**:
   - Dimension: ~1.65-1.9
   - Population: 175-500+ nodes
   - Correlation: 0.72-0.80
   - Regime: 2D-like mesh

---

## Scientific Interpretation

### What This Means

1. **Dimension is not geometric** — It's a measure of **activated connectivity degrees of freedom**.

2. **The transition is continuous** — There is no sharp "phase boundary" between 1D and 2D. Instead, the system smoothly recruits additional topological connections as driving increases.

3. **Population correlates with dimension** — Higher sustained populations enable more cross-connections, raising effective dimension.

4. **Correlation remains strong** — Both regimes show graph-Euclidean correlation > 0.7, confirming metric-like geometry is preserved across the transition.

5. **Triangle enrichment** — The 2D-like regime shows 5-10 triangles per node, indicating genuine loop formation rather than sparse-network artifacts.

### The Branching Mechanism

The data suggests the following mechanism:

```
WEAK DRIVING (interval > 400):
- Low injection rate → population ~50-150
- Defects form linear chains
- Few cross-connections → ~1D dimension

TRANSITION ZONE (interval ~340-350):
- Moderate injection → population ~150-175
- Chains begin to cross-link
- Loop formation starts → ~1.5D dimension

STRONG DRIVING (interval < 330):
- High injection rate → population 175-500+
- Dense network with many triangles
- Mesh-like topology → ~1.8D dimension
```

---

## Regime Classification Criteria

### Stable Filamentary (d < 1.4, corr > 0.6)
- Low effective dimension (~1.0-1.3)
- Chain-like topology
- Strong metric correlation

### Transitional (1.4 < d < 1.6, corr > 0.5)
- Intermediate dimension
- Mixed chain/mesh features
- Moderate correlation

### Stable 2D-like (d > 1.5, tri/n > 0.5, corr > 0.5)
- High effective dimension (~1.6-2.0)
- Triangle-rich mesh topology
- Maintained metric correlation (NOT sparse-network artifact)

### Runaway Overflow
- Population exceeds measurement cap (600 nodes)
- Occurs with very strong driving (interval < 60)

### Sparse-Network Artifact (d > 1.3, corr < 0.4)
- High dimension but weak correlation
- Indicates disconnected structure, not genuine 2D organization

---

## Experimental Parameters

| Parameter | Value |
|-----------|-------|
| Grid size | 48³ |
| Population cap | 600 |
| Window steps | 150 |
| Number of windows | 4 |
| Equilibration steps | 300 |
| Measurement interval | 30 steps |
| Timeout per interval | 35s |
| Injection count | 3 vortices/injection |

---

## Key Metrics Explained

### Effective Dimension
Computed from graph radius scaling: N(r) ~ r^d where N(r) is the number of nodes within graph distance r. Dimension d is the power-law exponent.

### Graph-Euclidean Correlation
Pearson correlation between graph distance and Euclidean distance for all node pairs. High correlation (>0.7) indicates metric-like geometry where graph topology reflects spatial structure.

### Triangle-per-Node (Tri/N)
Number of triangles divided by number of nodes. Higher values indicate loop-rich mesh topology characteristic of 2D organization.

---

## Implications for QMRT

1. **The ~1D state (Paper 6) is not a failure** — It's the naturally preferred organizational mode under moderate driving.

2. **Higher dimensions are accessible** — With stronger driving, the medium can organize into ~2D mesh structures.

3. **No need for special promotion mechanisms** — The Phase 8 forced promotion attempts were unnecessary; simple increased driving naturally activates higher-dimensional organization.

4. **Dimension as a dynamical variable** — Effective dimension should be treated as a state variable, not a fixed spatial parameter.

---

## Connection to Previous Work

| Phase/Paper | Finding | Updated Interpretation |
|-------------|---------|----------------------|
| Phase 7 | ~1.1 dimension is robust | ✓ Confirmed for moderate driving |
| Phase 8 | 2D promotion fails | ✗ Superseded: 2D emerges naturally with stronger driving |
| Phase 9 | NESS scaffold | ✓ Confirmed: driving sustains organization |
| Paper 6 | Filamentary scaffold | ✓ Confirmed as one branch; 2D branch now also identified |

---

## Next Steps

1. **Investigate 2D branch rules** — What causal/organizational mechanisms stabilize the 2D mesh regime?

2. **Test persistence** — Does the 2D branch persist when driving is reduced, or does it collapse back to 1D?

3. **Explore 2D → 3D transition** — Can even stronger driving (or different parameters) push the system toward 3D organization?

4. **Update theoretical framework** — Revise the "Why Filamentary?" note to incorporate the dimensional branching finding.

---

**Status**: COMPLETE  
**Date**: December 2025  
**Output File**: `/app/backend/qmrt_topology/papers/branch_transition_study_results.json`
