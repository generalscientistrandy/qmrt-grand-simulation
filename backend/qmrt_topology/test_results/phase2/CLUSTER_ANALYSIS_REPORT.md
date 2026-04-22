# Phase 2: Cluster Analysis Report

## Date: April 2026

## Executive Summary

Phase 2 establishes objective cluster metrics using connected-component analysis on the gradient field (|∇ρ|, top 10% threshold). Key finding: **Cluster morphology is insensitive to driving**, unlike organization metrics (S, I_TS) from Paper 2.

---

## 1. Metrics Defined

### 1.1 Cluster Identity
- Binary mask: |∇ρ| > 90th percentile
- Connected components (8-neighborhood)
- Minimum size: 4 pixels

### 1.2 Properties Per Cluster
| Metric | Definition |
|--------|------------|
| Size | Pixel count |
| Aspect Ratio (AR) | √(λ_max / λ_min) from covariance eigenvalues |
| Elongated | AR > 3 |
| Highly Elongated | AR > 5 |

### 1.3 Tracking
- Centroid-based matching (max distance = 5 pixels)
- Lifetime = death_time - birth_time

---

## 2. Experiment A: Undriven vs Driven

| Metric | Undriven | Driven | Ratio |
|--------|----------|--------|-------|
| Clusters total | 1011 | 1046 | 1.03 |
| Lifetime mean | 4.00 | 3.59 | **0.90** |
| Lifetime p90 | 8.00 | 6.00 | 0.75 |
| Size mean | 44.9 | 45.5 | 1.01 |
| Size max | 250 | 250 | 1.00 |
| AR mean | 2.15 | 2.25 | 1.05 |
| Elongated % | 15.1% | 14.3% | 0.95 |
| Highly elongated % | 0.8% | 2.0% | 2.5 |

### Key Finding
**Cluster morphology is nearly identical** between undriven and driven:
- Same sizes (~45 pixels)
- Same aspect ratios (~2.2)
- Same elongation fraction (~15%)

The difference in S and I_TS (Paper 2) does not manifest in cluster-level metrics.

---

## 3. Experiment B: Power Scaling

| Power P | Lifetime | Size | AR | Elongated % |
|---------|----------|------|-----|------------|
| 0.0005 | 3.73 | 46.2 | 2.23 | 14.6% |
| 0.0010 | 3.69 | 45.1 | 2.24 | 14.2% |
| 0.0020 | 3.78 | 45.7 | 2.28 | 15.3% |
| 0.0040 | 3.60 | 44.6 | 2.23 | 14.5% |
| 0.0080 | 3.67 | 38.9 | 2.23 | 13.2% |
| 0.0090 | 3.62 | 47.7 | 2.29 | 15.6% |

### Key Finding
**No clear power dependence** in cluster metrics:
- Lifetime: ~3.6-3.8 (flat)
- Size: ~39-48 (noisy, no trend)
- AR: ~2.23-2.29 (flat)
- Elongated: ~13-16% (flat)

---

## 4. Experiment C: Time Evolution

| Phase | N_clusters | Max Size | Mean AR |
|-------|------------|----------|---------|
| Early | 4.8 | 132.6 | 2.14 |
| Middle | 4.6 | 135.9 | 2.30 |
| Late | 4.9 | 132.0 | 2.26 |

### Key Finding
**Clusters are stable over time** under driving:
- Count: ~4.6-4.9 (stable)
- Max size: ~130 (stable)
- AR: ~2.1-2.3 (stable)

---

## 5. Interpretation

### What This Means
1. **Cluster morphology is a local property** - governed by gradient field structure, not global organization (S)
2. **Driving affects S, not cluster shape** - the organization metric captures field-wide coherence, not individual cluster properties
3. **Low anisotropy** (~15% elongated) - clusters are mostly blob-like, not filament-like
4. **No significant filament-like structures** in current parameter regime

### Scale Separation
| Level | Metric | Affected by Driving? |
|-------|--------|---------------------|
| Field-wide | S, I_TS | **Yes** (Paper 2) |
| Cluster-level | Size, AR, Lifetime | **No** (Phase 2) |

This suggests S measures **field coherence**, not cluster morphology.

---

## 6. Implications for "Filament" Claims

### Current Evidence
- Only 15% of clusters have AR > 3
- Only 1-2% have AR > 5
- No trend with power or driving

### Conclusion
**Cannot justify "filament-like" language** based on current data:
- Clusters are predominantly blob-like (AR ~ 2)
- Elongation is rare and doesn't scale with driving

### If We Want Filaments
Would need:
- Different field (e.g., strain tensor components)
- Different threshold strategy
- Larger grid size
- Different parameter regime

---

## 7. Files

- `cluster_analysis_results.json` - Full experimental data
- `cluster_metrics.py` - Metrics infrastructure

---

## 8. Phase 2 Status

**Completed:**
- [x] Cluster extraction (connected components)
- [x] Lifetime tracking
- [x] Size distribution
- [x] Anisotropy measurement
- [x] Undriven vs driven comparison
- [x] Power scaling

**Finding:**
Cluster morphology is insensitive to driving. The organization (S) measured in Paper 2 reflects field-wide coherence, not individual cluster properties.

**Next (if desired):**
- Test different fields (strain, vorticity)
- Test larger grids
- Test different parameter regimes (high α)
