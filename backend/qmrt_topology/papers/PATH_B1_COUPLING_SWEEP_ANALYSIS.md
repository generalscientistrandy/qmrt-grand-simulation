# Path B.1 Coupling Sweep Results — DECISIVE ANALYSIS

**Date: December 2025**
**Status: B.1 FAILED — Path B Falsified**

---

## 1. Experiment

Increased `phase_coupling_strength` from baseline 0.1 to 0.2 and 0.3, keeping all other parameters fixed.

**Motivation**: Baseline coupling (0.1) produced a MARGINAL result. Hypothesis was that stronger coupling might amplify the phase-class effect.

---

## 2. Results

| Coupling | Bimodal Score | Class Separation | W-C Correlation | Verdict |
|----------|---------------|------------------|-----------------|---------|
| 0.1 | 0.501 | 0.038 | -0.019 | FAIL |
| 0.2 | 0.500 | 0.039 | -0.008 | FAIL |
| 0.3 | 0.502 | 0.034 | +0.011 | FAIL |

**Required thresholds:**
- Bimodal score > 0.55 (clearly above random)
- Class separation > 0.10 (minimum viable)
- W-C correlation < 0.5 (independence from winding)

---

## 3. Key Finding: No Dose-Response

**Critical observation**: Increasing coupling strength did NOT improve the metrics.

| Coupling | Change from 0.1 |
|----------|-----------------|
| 0.2 | Bimodal: -0.001, ClassSep: +0.001 |
| 0.3 | Bimodal: +0.001, ClassSep: -0.004 |

The system is **saturated** — the phase-coupling mechanism is already applying its maximum effect at 0.1. Increasing the strength parameter does not produce stronger phase classes.

---

## 4. Interpretation

The minimal phase-coupling mechanism:
```python
target_diff = where(|phase_diff| < π/2, 0, ±π)
phase_correction = coupling_strength × topology_norm × phase_error
```

This mechanism **nudges** phases toward 0 or π relative to local average, but:

1. **The nudge is not accumulating** — Class separation stays flat (~0.035-0.04) regardless of coupling
2. **No bimodal structure emerges** — Bimodal score hovers at 0.50 (random level)
3. **The effect is purely local** — No global phase-class organization develops

---

## 5. Why This Mechanism Fails

The phase-coupling term operates on **local phase differences** relative to a Gaussian-smoothed average. This creates:

- A **restoring force** toward local conformity
- But NO **global coordination** between distant defects

For true phase classes to emerge, defects would need to:
1. "Know" about each other across the domain
2. Develop persistent, domain-wide phase relationships

The current mechanism lacks this non-local coordination. It's a local smoothing operation, not a symmetry-breaking mechanism.

---

## 6. Verdict

### B.1: FAILED

The phase-coupling mechanism does not produce robust phase-class emergence:

| Diagnostic | Required | Observed | Status |
|------------|----------|----------|--------|
| Phase distribution peaks | >0.55 | ~0.50 | **FAIL** |
| Class persistence | >0.10 | ~0.035 | **FAIL** |
| Winding independence | <0.50 | ~0.00 | ✓ PASS |

**Winding independence is real** — the mechanism does create something orthogonal to winding sign. But that "something" is too weak to constitute genuine phase classes.

---

## 7. Implications for Path B

Per the launch note:

> *"If any of 1-3 fail, Path B is falsified."*

Gates 1 and 2 have failed decisively. The minimal phase-coupling mechanism does not enable phase-coherent branch-pair structure.

**Recommended action**: 
- **Declare Path B.1 failed**
- **Do not proceed to B.2**
- **Return to the frozen Topological Dual-Sector branch** as the validated model

---

## 8. Scientific Statement

> "The minimal phase-coupling mechanism (local phase quantization toward 0/π) does not produce robust emergent phase classes in the QMRT medium. While the mechanism creates structure orthogonal to winding sign (correlation ~0), it fails to generate either bimodal phase distributions or persistent class separation. The effect is already saturated at coupling strength 0.1 and does not strengthen with increased coupling. Path B is therefore falsified under this mechanism."

---

## 9. What Would Be Needed for a Different Path B

A viable phase-coherence mechanism would require:

1. **Non-local coordination** — Defects must influence each other across the domain
2. **Symmetry-breaking dynamics** — A true bifurcation that splits the population
3. **Memory/hysteresis** — Phase assignments must persist robustly

The current local-smoothing approach does not provide any of these.

---

*Path B.1 Coupling Sweep Analysis — December 2025*
