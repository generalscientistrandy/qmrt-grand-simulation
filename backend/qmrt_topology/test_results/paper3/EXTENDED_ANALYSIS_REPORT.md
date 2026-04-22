# Phase 2B: Extended Cluster Analysis Report

## Date: April 2026

## Executive Summary

**Hidden anisotropy found via directional coherence analysis.**

The percentile-based clustering in Phase 2A was normalizing away the key difference:
- **Driven system has 70× stronger gradients** (masked by percentile threshold)
- **Driven system has 135× higher directional coherence**

---

## 1. Key Findings

### 1.1 Directional Coherence (Test 3) — THE SMOKING GUN

| Condition | Late Coherence | Early Coherence | Change |
|-----------|----------------|-----------------|--------|
| Undriven | 0.0014 | 0.0012 | +0.0002 |
| Driven | **0.1858** | 0.1195 | +0.066 |
| **Ratio** | **135×** | — | — |

**Interpretation**: Driving creates **directional alignment** in the gradient field.
- Undriven: nearly random direction (coherence ≈ 0)
- Driven: significant alignment (coherence ≈ 0.19)

This is evidence for organized, directional structure.

### 1.2 Absolute Threshold (Test 1) — GRADIENT MAGNITUDE

| Condition | Mean |∇ρ| | Max |∇ρ| | p90 |
|-----------|---------|--------|-----|
| Undriven | 1.2 | 2.3 | 1.9 |
| Driven | **84.0** | 193.2 | 140.3 |
| **Ratio** | **70×** | 84× | 72× |

**Interpretation**: Driving creates 70× stronger gradients.
- Percentile threshold (top 10%) masks this by always selecting relative peaks
- Absolute threshold reveals the true magnitude difference

### 1.3 Multi-Scale Thresholds (Test 2)

At extreme percentiles (p99):

| Condition | n_clusters | Mean AR | Max AR |
|-----------|------------|---------|--------|
| Undriven | 1 | 4.08 | 4.08 |
| Driven | 2 | 1.94 | 2.71 |

**Interesting finding**: Rare high-intensity structures are MORE elongated in undriven.

This suggests:
- Undriven: few surviving structures are stretched by decay process
- Driven: continuous injection creates more isotropic structures

### 1.4 Larger Grid (Test 5) — 100×100

| Condition | n_clusters | Mean Size | Mean AR | Elongated % |
|-----------|------------|-----------|---------|-------------|
| Undriven | 8 | 125 | 3.72 | **50%** |
| Driven | 7 | 143 | 2.81 | 29% |

**Finding**: Larger grid shows MORE elongation in undriven.

This is counterintuitive but meaningful:
- At large scales, decaying structures stretch and fragment
- Driving maintains compact, isotropic structures

### 1.5 Spatial Correlation (Test 4)

| Condition | ξ_h | ξ_v | ξ_r | Anisotropy |
|-----------|-----|-----|-----|------------|
| Undriven | 10 | 10 | 10 | 0.99 |
| Driven | 14 | 13 | 13 | 1.07 |

**Finding**: Isotropic correlation at both conditions.
- No preferred direction in correlation function
- Directional coherence is local, not field-wide

---

## 2. Revised Interpretation

### What We Learned

| Test | Original (Phase 2A) | Revised (Phase 2B) |
|------|---------------------|-------------------|
| Cluster shape | Same (AR ≈ 2.2) | Same (correctly measured) |
| Gradient strength | Not measured | **70× higher driven** |
| Directional alignment | Not measured | **135× higher driven** |
| Large-scale structure | Not tested | Undriven more elongated |

### The Correct Picture

1. **Driving creates strong, aligned gradients** (coherence = 0.19)
2. **Cluster shape is similar** (AR ≈ 2-3) but...
3. **Gradient magnitude differs enormously** (70×)
4. **Percentile normalization hid this**

### "Filament-like" Evidence?

**Partial evidence:**
- High directional coherence suggests aligned structures
- But cluster AR remains moderate (2-3)
- No field-wide anisotropy in correlation

**Conclusion:**
> The system exhibits **local directional alignment** under driving, but not filament-like morphology. Structures are aligned blobs, not elongated filaments.

---

## 3. Corrected Conclusion

### Phase 2A Said:
> "Cluster morphology is insensitive to driving"

### Phase 2B Says:
> "Cluster shape is similar, but driving creates 70× stronger gradients with 135× higher directional coherence. The alignment is local, not filament-like."

### Key Insight:
**S (Paper 2) measures gradient strength + coherence, not cluster shape.**

This explains why S is affected by driving while cluster AR is not:
- S ∝ gradient variance × alignment
- Cluster AR ∝ local shape only

---

## 4. What "Filaments" Would Require

To claim filament-like behavior, we would need:
1. ❌ High cluster AR (>5) — not observed
2. ✓ Directional coherence — **observed (0.19)**
3. ❌ Field-wide anisotropy — not observed
4. ✓ Strong gradients — **observed (70×)**

**Score: 2/4** — partial evidence for organized structure, not filaments.

---

## 5. Files

- `extended_cluster_analysis.json` — Full test results
- `run_extended_analysis.py` — Analysis script

---

## 6. Summary for Paper 3 (if written)

Paper 3 could claim:
> "Driving creates locally aligned gradient structures with 70× higher magnitude and 135× higher directional coherence, but cluster morphology remains isotropic (AR ≈ 2-3). The organization metric S reflects this gradient coherence, not cluster elongation."

This is a nuanced, defensible result.
