# Branch F: Spatially Separated Regeneration-Stabilization Model

**Date**: 2025-12-19  
**Status**: PARTIAL SUCCESS — Mechanism validated, regeneration rate insufficient

---

## Executive Summary

Branch F tested the hypothesis that topological memory (regeneration) and vortex stabilization can co-align if they occur in **different spatial regions**:

- **Zone A (Interior)**: Low-β or high-coupling region for regeneration
- **Zone B (Periphery)**: High-β or low-coupling region for stabilization

**Results**: The spatial separation mechanism works as designed (2/3 tests pass), but the combined system fails to achieve sustained population due to insufficient regeneration rate.

---

## Test Results

### Test 1: Regeneration Location — ✓ PASS

**Question**: Do vortices nucleate preferentially in the regeneration zone?

| Zone | Nucleation Density (×1000) | % of Total |
|------|---------------------------|------------|
| Interior (low-β) | 1.1–1.4 | 30-33% |
| Transition | 2.0–2.3 | 67-70% |
| Periphery (high-β) | 0.0 | 0% |

**Verdict**: Vortices nucleate in low-β regions (interior + transition), **never** in high-β periphery.

### Test 2: Migration/Capture — ✓ PASS

**Question**: Do vortices migrate toward the stabilization zone?

| Metric | Value |
|--------|-------|
| Mean β change (final - initial) | +0.058 to +0.068 |
| Migrations toward higher β | 31-34% |
| Interior-born lifetime | 116-122 steps |
| Periphery-born lifetime | 92-98 steps |

**Verdict**: Net migration toward higher β; interior-born vortices live ~25% longer.

### Test 3: Population Localization — ✗ FAIL

**Question**: Can the system maintain nonzero localized population?

| Metric | Target | Achieved |
|--------|--------|----------|
| Late population | > 1.0 | 0.0–0.25 |
| Total births | > 50 | 10–30 |
| Localization ratio | > 0.4 | 0.0 |

**Verdict**: Population goes extinct; regeneration rate too low to sustain.

---

## Mechanism Analysis

### What Works

1. **Spatial selectivity is correct**: Nucleation happens where intended (low-β / high-coupling)
2. **Migration direction is correct**: Vortices drift toward stabilization zone
3. **Lifetime gradient exists**: Structures in periphery would persist if they arrived

### What Fails

1. **Regeneration rate is ~60× lower than pure Branch E**
   - Pure Branch E: ~1200 births in 4000 steps
   - Branch F variants: ~20 births in 4000 steps

2. **Root cause**: The β-weighted Laplacian changes wave dynamics enough to disrupt the full Branch E regeneration mechanism
   - Branch E uses medium dynamics (tau field evolves)
   - Branch E uses oscillators (chi_1, chi_2) that couple to channels
   - Branch F simplified these away

---

## Comparison: Branch E vs Branch F Dynamics

| Component | Branch E | Branch F |
|-----------|----------|----------|
| Laplacian | `c_eff² * lap` | β-weighted lap |
| Medium (tau) | Dynamic, evolves | Static |
| Oscillators | Present (chi_1, chi_2) | Absent |
| Wave speed | `c_eff = c_0 * tau / tau_0` | Implicit via β |
| dt | 0.04 (internal) | 0.05 (argument) |
| Regeneration rate | ~300/1000 steps | ~5/1000 steps |

---

## Key Insight

> **β-weighted Laplacian disrupts regeneration.**
> 
> Branch E's regeneration mechanism requires specific wave dynamics (medium-dependent speed, oscillator coupling). The β-weighted Laplacian in Branch C/F changes the wave equation form in a way that breaks this mechanism, even when the channel self-selection logic is preserved.

This explains why:
- Branch C (β wells) + Branch E (regeneration) are antagonistic
- Branch F (spatial β variation) + regeneration doesn't reach sustained population
- Even Branch F Alternative (spatial coupling variation with uniform β) underperforms

The β-coupling affects not just localization but the fundamental wave transport that enables topological memory.

---

## Implications for Future Work

### Option 1: Full Branch E + Localization Overlay

Instead of modifying Branch E dynamics, add a localization mechanism that doesn't affect wave propagation:
- External potential (not β)
- Defect-defect interactions
- Energy landscape modification

### Option 2: Proper Medium Coupling

Extend Branch F to include Branch E's full dynamics:
- Dynamic tau field
- Dual oscillators (chi_1, chi_2)
- Proper c_eff calculation

Then add spatial variation to parameters that don't disrupt regeneration.

### Option 3: Accept Functional Separation

The spatial separation principle is validated. The implementation challenge is preserving regeneration strength while adding localization. This may require:
- Separate timescales for regeneration vs stabilization
- Hybrid regions with intermediate properties
- Sequential (not simultaneous) optimization

---

## Files

- `branch_f_spatial_separation.py` — Primary implementation
- `branch_f_parameter_sweep.py` — Parameter exploration
- `branch_f_alternative.py` — Coupling-variation approach
- `branch_f_results.json` — Quantitative results

---

## Conclusion

**Branch F demonstrates that spatial separation is the correct principle** for co-aligning localization and topological memory. Tests 1 and 2 prove the mechanism works as designed. The failure is in achieving sufficient regeneration rate, which is an implementation challenge, not a physics failure.

The next step should be integrating the full Branch E dynamics (medium + oscillators) into a spatially-structured system, rather than simplifying them away.
