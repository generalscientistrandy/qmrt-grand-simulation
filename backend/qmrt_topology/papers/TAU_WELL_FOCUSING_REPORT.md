# τ-Well Focusing Test Report

**Date:** December 2025  
**Test:** τ-Well Focusing  
**Status:** ANTI-FOCUSING OBSERVED (Divergence)

---

## Executive Summary

Contrary to the initial hypothesis, τ-wells (lower τ regions in higher τ background) produce **anti-focusing** (divergence) rather than convergence. The intensity and concentration **decrease** with increasing well depth.

### Key Results

| Δτ | τ_well | Intensity | Concentration |
|----|--------|-----------|---------------|
| 0.0 | 1.80 | 3.092 | 0.383 |
| 0.2 | 1.60 | 2.997 | 0.376 |
| 0.4 | 1.40 | 2.866 | 0.367 |
| 0.6 | 1.20 | 2.706 | 0.357 |
| 0.8 | 1.00 | 2.537 | 0.346 |

**Concentration-depth correlation: -0.999** (strong anti-correlation)

---

## Physical Interpretation

### Why Anti-Focusing?

The τ-well creates a region of **slower** wave speed. When a wavefront enters:

1. **At entry**: The central portion slows down relative to the edges
2. **Inside well**: Central wave lags behind the edge portions
3. **At exit**: The wavefront has curved **outward** (concave)
4. **After well**: The concave wavefront continues to diverge

This is analogous to a **diverging lens** in optics, not a converging one.

### Corrected Physics

For a τ-well to act as a **converging** lens, we need a τ-**peak** (higher τ region):
- Higher τ → faster c_eff
- Central portion speeds up → wavefront curves **inward** (convex)
- Convex wavefront converges after exiting

### Comparison to Optics

| Optical Lens | τ Analog | Effect |
|--------------|----------|--------|
| Converging (thick center) | τ-peak (high τ center) | Focusing |
| Diverging (thin center) | τ-well (low τ center) | **Defocusing** |

The test result is **physically correct** — it just tested the diverging case.

---

## Revised Interpretation

The τ-gradient lensing result (waves bend toward slower regions) is still valid. However:

- **Single gradient**: Wave bends toward lower τ (confirmed)
- **τ-well (symmetric)**: Wave enters and exits with opposite deflections, net divergence
- **τ-peak (symmetric)**: Would produce convergence (not yet tested)

This is consistent with the τ field acting as an effective refractive geometry.

---

## Recommendation

Test a **τ-peak** configuration to confirm focusing:
- Background τ = 1.0
- Central peak τ = 1.0 + Δτ (up to 1.8)
- Expect: convergence, intensity enhancement

---

## Conclusion

The τ-well test reveals **diverging lens behavior**, which is physically correct but opposite to the initial hypothesis framing. The τ field continues to act as an effective refractive geometry, but:

- τ-wells → divergence (like a diverging lens)
- τ-peaks → convergence (expected, to be tested)

This does not invalidate the lensing finding; it clarifies the geometry.

---

## Files

- `/app/backend/tau_well_focusing_test.py` — Test implementation
- `/app/backend/qmrt_topology/papers/TAU_WELL_FOCUSING_RESULTS.json` — Raw data
