# Phase 3: Localized Driving Experiment Report

## Date: April 2026

## Executive Summary

**CRITICAL FINDING: The current QMRT model does NOT support matter-like localization.**

Organization spreads throughout the medium via wave propagation, preventing the formation of persistent localized structures.

---

## 1. Experiment Design

### Question
Can the medium support persistent, localized pockets of organization?

In other words: Can we create "matter" (driven region) embedded in "space" (undriven background)?

### Method
- Apply periodic driving ONLY to a small circular region (radius ~10, area ~5% of grid)
- Leave the rest of the grid undriven (the "background/space")
- Measure spatial contrast in organization metric S between inside and outside

### Key Metrics
- **S contrast**: S_inside / S_outside (higher = better localization)
- **Leakage**: Fraction of high-gradient regions outside the driven area
- **Boundary sharpness**: Gradient magnitude at the boundary

---

## 2. Results

### Initial State vs Late Time

| Time | S inside | S outside | S Contrast | Leakage |
|------|----------|-----------|------------|---------|
| t=0  | 0.0018   | 0.00005   | **36.7×**  | 0.35    |
| t=60 | 0.0311   | 0.0335    | 0.93×      | 0.59    |
| t=120| 0.0164   | 0.0142    | 1.16×      | 0.71    |
| t=300| 0.0101   | 0.0081    | 1.25×      | 0.71    |
| Late | ~0.01    | ~0.007    | **~1.4×**  | ~0.45   |

**Key observation**: Initial contrast of 36× decays to ~1.4× within ~60 time units.

### Parameter Sweeps

#### Varying Medium Diffusion (D_medium)
| D_medium | S Contrast | Localized? |
|----------|------------|------------|
| 0.100    | 1.35×      | NO         |
| 0.050    | 1.36×      | NO         |
| 0.010    | 1.37×      | NO         |
| 0.001    | 1.37×      | NO         |
| **0.000**| 1.37×      | **NO**     |

**Result**: Even with zero diffusion (D_medium=0), localization fails.

#### Varying Other Parameters
| Parameter | Range Tested | Effect on S Contrast |
|-----------|--------------|---------------------|
| Pulse amplitude | 0.5 - 4.0 | Minimal (~1.3-1.4×) |
| Pulse interval | 100 - 500 | Minimal |
| Driven radius | 5 - 15 | Minimal |
| Wave damping (γ) | 0.005 - 0.1 | Slight increase (1.3→1.5×) |
| Relaxation (λ) | 0.1 - 0.8 | Minimal |

**No parameter combination achieved localization** (defined as S contrast > 2× with leakage < 50%).

---

## 3. Physics Interpretation

### Why Spreading Occurs

The medium field φ satisfies a **wave equation**:
```
∂²φ/∂t² = c_eff² ∇²φ - γ ∂φ/∂t
```

**Waves naturally propagate outward**. Energy injected at the center spreads via wave propagation on a timescale:
```
t_spread ~ R / c_eff ~ 10 / 2 ~ 5 time units
```

This matches the observed rapid decay of S contrast.

The tau field (medium structure) follows the energy density ρ = φ² + φ̇², which spreads via waves. Even with D_medium = 0, the tau field homogenizes because ρ homogenizes.

### Fundamental Insight

> **The spreading is intrinsic to wave-based systems, not a parameter issue.**

For localization to occur, the model would need:
1. **Wave trapping** (solitons, topological defects)
2. **Nonlinear self-focusing** (energy attracts itself)
3. **Boundary-breaking mechanisms** (strong damping barriers)
4. **Modified dispersion** (waves that don't propagate)

---

## 4. Implications for QMRT

### What This Means

| Hypothesis | Status |
|------------|--------|
| "Matter = localized sustained organization" | ❌ NOT SUPPORTED (in current model) |
| "Space = undriven background" | ✓ Background decays (Paper 2) |
| "Matter/space boundary is sharp" | ❌ Boundary rapidly diffuses |

### The Current Model Describes...
- ✓ Global organization maintenance (via global driving)
- ✓ Asymptotic decay without driving
- ✓ Non-local gradient alignment (Phase 2B coherence)
- ❌ Localized "particle-like" structures
- ❌ Matter/space differentiation

### What Would Be Needed for Matter Emergence

To support persistent localized structures, the model needs **nonlinear confinement**:

1. **Solitonic solutions**: φ⁴ or sine-Gordon potentials
2. **Self-trapping**: Energy concentration that deepens the local potential
3. **Topological defects**: Vortices, domain walls that trap energy
4. **Modified wave equation**: Non-propagating modes

This would require **new physics** not present in the current linear wave + relaxation model.

---

## 5. Conclusion

### Summary

**The localized driving experiment yields a NEGATIVE result:**
- Organization spreads throughout the medium
- Wave propagation prevents localization
- No parameter regime supports matter-like structures

### Scientific Value

This is an **important constraining result**:
- It rules out simple localization in the current model
- It identifies wave propagation as the key spreading mechanism
- It points toward necessary model extensions (nonlinear terms)

### Path Forward

To achieve matter-like behavior, consider:
1. Adding **nonlinear self-interaction** (φ³ or φ⁴ terms)
2. Introducing **topological constraints** (vortex cores as matter)
3. Exploring **breaking wave propagation** (massive modes, confinement)

---

## 6. Files

- `run_localized_driving.py` - Experiment script
- `localized_driving_result.json` - Full results
- `localized_driving_timeseries.json` - Time series data

---

## 7. Summary for Paper 3

**Proposed claim:**

> "The current QMRT model does not support persistent localized organization. Energy injected into a localized region spreads throughout the medium via wave propagation, preventing the formation of matter-like structures. Localization requires nonlinear confinement mechanisms not present in the linear wave + relaxation model. This negative result constrains theories that attempt to derive matter from medium dynamics."

This is a scientifically rigorous negative result that advances understanding of the model's limitations.
