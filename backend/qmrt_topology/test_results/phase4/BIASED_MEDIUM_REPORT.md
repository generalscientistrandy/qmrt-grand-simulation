# Phase 4: Biased Medium Experiment Report

## Date: April 2026

## Executive Summary

**BREAKTHROUGH: Organization localizes in biased regions, even though energy does not.**

By embedding parameter asymmetry INTO the medium (rather than injecting energy externally), 
we achieve **S contrast of 14×** — ten times better than localized driving (1.4×).

---

## 1. The Key Insight

### What Failed (Localized Driving)
- Injected energy into small region
- Measured energy contrast: spreads to ~1.0×
- Measured S contrast: also decays to ~1.4×
- **Conclusion**: "Localization fails"

### What Works (Biased Medium)
- Embed parameter asymmetry into medium
- Energy still spreads uniformly: rho contrast ~1.0×
- But organization concentrates: **S contrast ~14×**
- **Conclusion**: "Organization localizes, energy does not"

### The Decoupling

| Quantity | Behavior | Why |
|----------|----------|-----|
| Energy (ρ) | Spreads uniformly | Waves propagate, energy conserved |
| Organization (S) | Concentrates in biased region | Depends on local parameters |

**Energy and organization can decouple.**

---

## 2. Experimental Setup

### Biased Medium Parameters

| Parameter | Inside (biased) | Outside (background) | Contrast |
|-----------|-----------------|---------------------|----------|
| γ (damping) | 0.001 | 0.1 | 100× |
| β (coupling) | 0.8 | 0.2 | 4× |
| λ (relaxation) | 0.2 | 0.8 | 4× |

- Biased region: ~7% of grid (radius=15)
- Initial condition: Uniform noise (no localized pulse)
- No external driving after initialization

### What the Parameters Do

| Parameter | Effect of Lower Value |
|-----------|-----------------------|
| γ (damping) | Oscillations persist longer |
| λ (relaxation) | τ deviations persist longer |
| β (coupling) | Stronger response to energy density |

**Combined effect**: The biased region is "stickier" for organization.

---

## 3. Results

### Time Evolution

| Time | S inside | S outside | S Contrast | ρ Contrast |
|------|----------|-----------|------------|------------|
| t=0 | 0.0002 | 0.0004 | 0.4× | 1.0× |
| t=200 | 0.0344 | 0.0026 | 13.2× | 1.0× |
| t=400 | 0.0346 | 0.0025 | 13.9× | 1.0× |
| t=1400 | 0.0344 | 0.0025 | **13.9×** | 1.0× |

**Key observations:**
1. S contrast rises rapidly from 0.4× to 13× in first 200 time units
2. S contrast then STABILIZES at ~14×
3. Energy (ρ) remains uniform throughout
4. Structure persists indefinitely (tested to t=1400)

### Comparison

| Experiment | S Contrast | ρ Contrast | Mechanism |
|------------|------------|------------|-----------|
| Localized Driving | 1.4× | ~1× | External energy injection |
| **Biased Medium** | **14×** | 1× | Parameter asymmetry |

**10× improvement in organization localization.**

---

## 4. Physics Interpretation

### Why This Works

1. **Energy spreads** (wave equation → propagation)
2. **But organization depends on local physics** (γ, β, λ)
3. Where parameters favor structure, structure concentrates
4. The "same" energy is organized differently in different regions

### Matter vs Space (Revised)

| Region | Energy | Organization | Interpretation |
|--------|--------|--------------|----------------|
| Biased | Uniform | HIGH (S=0.034) | "Matter-like" |
| Background | Uniform | LOW (S=0.002) | "Space-like" |

**Matter = region where organization concentrates, not where energy concentrates.**

### Analogy

Think of the same amount of flour:
- Scattered uniformly on a table → low structure (space)
- Shaped into a pile → high structure (matter)

The flour (energy) is the same; the organization differs.

---

## 5. Implications

### For the "Matter from Imbalance" Hypothesis

**SUPPORTED**: 
- Structure emerges from parameter imbalance
- No external driving needed after initialization
- Organization stays localized indefinitely

### Constraint Update

| Statement | Paper 3 (old) | Phase 4 (new) |
|-----------|---------------|---------------|
| Energy localizes | NO | NO |
| Organization localizes | NO (with driving) | **YES** (with imbalance) |
| Mechanism | Injection | Embedded asymmetry |

### What This Means Physically

The medium can support "matter-like" regions if:
1. Parameters vary spatially (broken symmetry)
2. Some regions favor structure (lower damping, stronger coupling)
3. Energy flows everywhere but organizes preferentially

This is closer to real physics:
- The universe is not uniform
- Parameters (coupling constants, masses) vary
- Structure concentrates where conditions favor it

---

## 6. Next Questions

1. **Multiple biased spots**: Do they interact? Attract? Repel?
2. **Spot dynamics**: If we make the bias region move, does structure follow?
3. **Topological connection**: Do vortices preferentially form in biased regions?
4. **Stability analysis**: What's the minimum contrast needed for localization?

---

## 7. Summary Statement

> **Organization can localize even when energy cannot. Embedded parameter asymmetry 
> achieves 14× organization contrast (vs 1.4× with external driving). This supports 
> the interpretation: "matter = regions where organization concentrates due to 
> favorable local physics, not where energy is injected."**

---

## 8. Files

- `/phase4/biased_medium_extreme.json` — Experimental data
- `/phase4/BIASED_MEDIUM_REPORT.md` — This report
