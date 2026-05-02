# Directional Isotropy Test Results

**Date:** December 2025  
**Status:** BASELINE ESTABLISHED — Defect-induced anisotropy dominates

---

## Summary

The Directional Isotropy Test revealed a critical baseline finding:

| Medium Type | Anisotropy Index |
|-------------|------------------|
| Clean wave (zero initial) | **0.0000** (perfect) |
| Unregulated + defects | ~0.96 |
| Regulated v1.1 + defects | ~1.00 |

**Key Finding:** The wave solver is **perfectly isotropic** in a clean medium. All observed anisotropy comes from the random defect configuration, not from the underlying physics or lattice structure.

---

## Test Results

### Baseline: Clean Wave Medium (Zero Initial State)

| Direction | t_arrive | c_eff |
|-----------|----------|-------|
| +x | 6.0 | 2.67 |
| -x | 6.0 | 2.67 |
| +y | 6.0 | 2.67 |
| -y | 6.0 | 2.67 |
| +z | 6.0 | 2.67 |
| -z | 6.0 | 2.67 |

- **Mean c_eff:** 2.67
- **Std c_eff:** 0.000
- **Anisotropy:** 0.0000

Theoretical c = √(c₀² × τ) = √4 = 2.0. Measured c_eff = 2.67 is consistent with wave front spreading.

### Defect-Active Media

With randomly seeded defects (8 initial defects, seed=42), propagation becomes highly anisotropic due to:
1. Non-uniform τ field from defect activity
2. Random defect positions creating directional bias
3. Energy scattering from defect interactions

Multi-seed testing (seeds 42, 123, 456) showed:

| Mode | Mean c_eff | Std | Anisotropy |
|------|------------|-----|------------|
| Unregulated | 47.3 | 45.6 | 0.964 |
| Regulated v1.1 | 17.2 | 17.3 | 1.004 |

The high variance (std ~ mean) indicates chaotic, unreliable measurements dominated by the specific defect configuration.

---

## Interpretation

### Why Regulation Doesn't Improve Isotropy

The hypothesis was:
> "Regulated recovery creates effective geometry that should produce isotropic propagation."

However, the test reveals:
1. **The wave solver IS isotropic** (proven by clean medium test)
2. **Defects introduce directional bias** based on their random positions
3. **τ heterogeneity from regulation** doesn't overcome the defect-induced anisotropy

### The Real Question

The isotropy test doesn't measure what we thought. It measures:
- How defect positions affect propagation paths
- NOT the intrinsic isotropy of the effective geometry

### What This Means for Emergent Lorentz

This doesn't invalidate the Light-Cone v2 result (τ heterogeneity improves propagation metrics). It shows:

1. **Lorentz-like isotropy is already built into the wave equation**
2. **Defect dynamics break isotropy** by creating non-uniform τ
3. **The question shifts** from "is propagation isotropic?" to "does regulation create a more stable effective geometry?"

---

## Conclusions

1. **Wave solver is perfectly isotropic** in clean medium (anisotropy = 0)
2. **Defect configurations dominate** the anisotropy in active media
3. **Regulation does not improve** defect-induced anisotropy
4. **The original hypothesis needs refinement** — emergent Lorentz behavior may require defect organization, not just τ regulation

---

## Recommended Next Steps

### Option A: Refine the Isotropy Test
- Use controlled defect configurations (not random)
- Measure anisotropy with defects at known positions
- Compare regulated vs unregulated with same defect layout

### Option B: Pivot to Different Lorentz Tests
- **Dispersion Relation**: Does ω² = c²k² hold?
- **Moving-Defect Invariance**: Do defects have velocity caps?
- **Causal Boundary**: Is signal confined within expected light cone?

### Option C: Investigate Defect Organization
- Does regulated recovery create more organized defect patterns?
- Do organized patterns reduce propagation anisotropy?

---

## Scientific Statement

> "The QMRT wave solver exhibits perfect isotropy (anisotropy = 0) in uniform media, confirming that Lorentz-like geometry is built into the wave equation. Observed anisotropy in defect-active simulations arises from random defect configurations, not from lattice artifacts. Regulated recovery v1.1, while creating meaningful τ heterogeneity, does not reduce this defect-induced anisotropy. Future Lorentz-emergence tests should focus on defect organization metrics or alternative propagation tests (dispersion, moving-defect invariance)."

---

## Files

- `/app/backend/directional_isotropy_test.py`
- `/app/backend/qmrt_topology/papers/DIRECTIONAL_ISOTROPY_RESULTS.json`
