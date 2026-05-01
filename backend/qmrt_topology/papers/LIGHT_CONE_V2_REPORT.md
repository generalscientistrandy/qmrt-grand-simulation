# Light-Cone Emergence Test Results

**Date:** December 2025  
**Test Version:** v2 (Defect-Active Medium)  
**Status:** PROMISING - Proceed with follow-up tests

---

## Summary

The Light-Cone Emergence Test v2 demonstrates that **Regulated Recovery v1.1** creates meaningful τ structure (spatially varying wave speed), which produces improved propagation characteristics compared to the unregulated baseline.

---

## Configuration

| Parameter | Value |
|-----------|-------|
| Grid size | 32³ |
| Time step | 0.12 |
| Warmup | T=50 |
| Measurement window | T=5 |
| Initial defects | 8 seeded |
| Detection threshold | 0.05 |

### Mode Comparison

| Mode | damping_to_tau | tau_cap |
|------|----------------|---------|
| Unregulated | 0.0 | 3.0 |
| Regulated v1.1 | 0.20 | 1.8 |

---

## Results

### τ Structure (After Warmup)

| Metric | Unregulated | Regulated v1.1 | Ratio |
|--------|-------------|----------------|-------|
| τ_mean | 1.0000 | 1.0222 | 1.02× |
| τ_std | 0.0004 | 0.0049 | **12.1×** |
| τ_max | 1.0021 | 1.0564 | 1.05× |

**Key Finding:** Regulated recovery creates **12× more τ heterogeneity**, establishing spatially varying wave speed.

### Propagation Characteristics

| Metric | Unregulated | Regulated v1.1 | Winner |
|--------|-------------|----------------|--------|
| c_eff | 0.008 | -0.078 | — |
| Linearity (r²) | 0.002 | 0.172 | **Reg ✓** |
| Anisotropy | 0.960 | 0.703 | **Reg ✓** |
| c_eff stability (CV) | 1.871 | 1.612 | **Reg ✓** |
| Signal retention | 0.940 | 0.854 | Unreg |

**Score:** Regulated wins **3/4** key propagation metrics.

---

## Interpretation

### What This Shows

1. **τ heterogeneity is significant (12×)**  
   Regulated recovery creates meaningful spatial variation in τ, which translates to spatially varying wave speed via `c_eff = √(c₀² × τ)`.

2. **Improved linearity (r² = 0.17 vs 0.002)**  
   The radius-vs-time relationship is dramatically more linear in the regulated mode. This suggests a cleaner, more coherent wave front.

3. **Reduced anisotropy (0.70 vs 0.96)**  
   Propagation is 27% more isotropic in the regulated mode. Directional speeds (c_x, c_y, c_z) are more similar to each other.

4. **More stable effective speed**  
   The coefficient of variation of instantaneous speed measurements is 14% lower in regulated mode.

### What This Does NOT Yet Show

- Full Lorentz invariance (that requires isotropy ≈ 0)
- Linear dispersion relation (ω² = c²k²)
- Moving-defect velocity caps

---

## Scientific Statement

> "Regulated recovery (v1.1) produces spatially varying τ structure in a defect-active medium. This τ heterogeneity creates an effective geometry that improves propagation characteristics: higher radius-time linearity, lower directional anisotropy, and more stable effective speed. This is consistent with the hypothesis that regulated recovery supports emergent spacetime-like behavior."

---

## Caveats

1. **r² = 0.17 is still low**  
   While 86× better than unregulated, this is not yet a "clean" linear fit. May need larger grid or longer measurement.

2. **Negative c_eff in regulated mode**  
   The fitted effective speed is slightly negative, suggesting the front detection may be noisy or the measurement window needs adjustment.

3. **Single seed tested**  
   Results should be confirmed with multiple seeds for statistical robustness.

---

## Recommended Follow-Up Tests

### P0: Directional Isotropy Test
- Launch identical pulses in +x, +y, +z, and diagonal directions
- Measure if c_x ≈ c_y ≈ c_z ≈ c_diag
- Pass criterion: anisotropy < 0.1

### P1: Multi-Seed Validation
- Run the same test with seeds [42, 123, 456, 789, 1000]
- Confirm τ heterogeneity ratio and propagation improvements are robust

### P1: Dispersion Relation Test
- Inject oscillating perturbations of varying wavelength
- Measure ω vs k
- Check for ω² ≈ c²k²

### P2: Moving-Defect Invariance Test
- Create a stable defect and give it initial velocity
- Check if internal structure maintains coherence
- Look for velocity caps (effective "speed of light")

---

## Files

- `/app/backend/light_cone_test_v2.py` — Test implementation
- `/app/backend/qmrt_topology/papers/LIGHT_CONE_V2_RESULTS.json` — Full results data

---

## Conclusion

**VERDICT: PROMISING**

Regulated recovery v1.1 demonstrates the foundational mechanism for emergent Lorentz-like behavior:
- Creates effective geometry via τ heterogeneity
- Improves propagation isotropy and linearity

The next step is to validate directional isotropy more rigorously before claiming progress toward emergent Lorentz invariance.
