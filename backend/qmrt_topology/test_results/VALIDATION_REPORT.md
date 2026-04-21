# QMRT Emergence Validation: Complete Results Report

**Date:** December 2025  
**Status:** Paper-Ready Core Results

---

## Executive Summary

We present statistical evidence for a coherent lifecycle model of structure emergence in the QMRT dynamical medium framework. Three independent tests, supported by robustness checks and parameter sweeps, demonstrate that structure creation, persistence, and interaction are governed by distinct field variables.

**Main Finding:** Structure emergence is statistically coupled to medium state, not random.

---

## Test Results

### Test 1: Birth Location vs ρ (Energy Density)

**Hypothesis:** Structures are more likely to be born in high-ρ or high-∇ρ regions.

| Metric | Mean Percentile | 95% CI | p-value | Enrichment |
|--------|----------------|--------|---------|------------|
| ρ (Energy) | 85.8% | [85.0%, 86.5%] | <10⁻⁶ | 1.72× |
| ∇ρ (Gradient) | 77.5% | [75.7%, 79.2%] | <10⁻⁶ | 1.55× |

**Robustness Check:**
- Shuffle control: 49.7% (effect nullified → proves real spatial coupling)
- Decile histogram: 92% of births in top 3 deciles (χ²=2598, p<0.001)

---

### Test 2: Persistence vs S (Spatial Organization)

**Hypothesis:** Persistent structures align with higher S (organization).

| Metric | Correlation | p-value | Effect Size |
|--------|-------------|---------|-------------|
| Lifetime ↔ S | r = 0.834 | <10⁻⁶ | d = 0.81 (large) |

- Long-lived mean S: **4.66** vs Short-lived: **1.49** (3.1× higher)

**Partial Correlation Check:**
- r(Lifetime, S | ρ) = **0.919** (STRONGER than raw correlation)
- S ↔ ρ correlation = -0.125 (nearly independent)
- **Conclusion:** S is a DISTINCT organizing variable, not another form of energy

---

### Test 3: Merge Activity vs ∇ρ (Gradient)

**Hypothesis:** Merges occur in high-gradient interaction zones.

| Comparison | Merge | Control | Enrichment | p-value |
|------------|-------|---------|------------|---------|
| Merge vs Random | 83.3% | 49.3% | 1.69× | <10⁻⁶ |
| Merge vs Birth | 83.3% | 77.6% | 1.07× | <10⁻⁵ |

**Key Finding:** Gradient DOMINATES over energy density for merges (∇ρ=83.3% > ρ=74.5%)

---

## Validation Checks

### α-Sweep (Coupling Strength)

| α | Birth ρ% | Merge ∇ρ% | r(L,S) |
|---|----------|-----------|--------|
| 0.2 | 79.0% | 98.1% | 0.824 |
| 0.4 | 83.2% | 98.8% | 0.834 |
| 0.6 | 85.4% | 97.5% | 0.846 |
| 0.8 | 90.4% | 100.0% | 0.867 |
| 1.0 | 92.2% | 82.2% | 0.862 |

**Trend:** Birth ρ enrichment INCREASES with α (79% → 92%)  
**Conclusion:** Coupling strength modulates emergence intensity

### Resolution Sanity Check

| Grid Size | Birth ρ% | r(Lifetime,S) |
|-----------|----------|---------------|
| 30 | 92.1 ± 9.9% | 0.84 |
| 40 | 85.8 ± 12.0% | 0.87 |
| 50 | 89.8 ± 8.1% | 0.86 |

**Conclusion:** ✓ Metrics STABLE across resolutions (not numerical artifacts)

---

## Validated Emergence Chain

```
High ρ + ∇ρ  →  BIRTH       (energy + instability)
High S       →  PERSISTENCE (spatial organization)  
High ∇ρ      →  INTERACTION (gradient-driven merges)
```

### Functional Decomposition of Field Variables

| Variable | Role | Evidence |
|----------|------|----------|
| **ρ** | Energy availability | Birth enriched at 85.8% percentile |
| **∇ρ** | Instability / interaction driver | Merges at 83.3%, gradient dominates |
| **S** | Structural organization | r=0.83 with lifetime, independent of ρ |

---

## Statistical Summary

| Test | Sample Size | Effect Size | p-value | Robustness |
|------|-------------|-------------|---------|------------|
| Birth vs ρ | N=1040 births | 1.72× | <10⁻⁶ | Shuffle ✓ |
| Persistence vs S | N=1280 structures | d=0.81 | <10⁻⁶ | Partial ✓ |
| Merge vs ∇ρ | N=320 merges | 1.69× | <10⁻⁶ | vs Birth ✓ |
| α-sweep | 5 values | Monotonic | — | Resolution ✓ |

---

## Conclusions

1. **Structure birth is NOT random** — it is strongly biased toward high-energy and high-gradient regions.

2. **Structure persistence is NOT arbitrary** — it correlates with spatial organization (S), independently of energy density.

3. **Structure interaction is gradient-driven** — merges occur in high-gradient zones, with gradient dominating over energy density.

4. **Effects scale with coupling** — stronger α leads to stronger energy-dependent birth, confirming the framework's predictions.

5. **Results are robust** — shuffle controls, partial correlations, and resolution checks all support the physical interpretation.

---

## Recommended Citation Format

> "We find strong statistical coupling between structure lifecycle events and local field variables: birth is enriched in high ρ and high |∇ρ| regions; persistence correlates with S independently of ρ; and interaction (merges) is biased toward high |∇ρ|. These relationships are robust to shuffle controls and consistent across parameter variations. These results support a lifecycle model of emergence in the dynamical medium framework."

---

## Files

- `test1_birth_vs_rho.json` - Birth location analysis
- `test1_robustness_check.json` - Shuffle and decile validation
- `test2_longlived_vs_S.json` - Persistence correlation
- `partial_correlation_check.json` - S independence verification
- `test3_merge_vs_gradient.json` - Merge interaction analysis
- `alpha_sweep.json` - Coupling strength sweep
- `resolution_sanity_check.json` - Grid resolution validation
