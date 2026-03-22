# QMRT v3: Four Critical Validation Checks - Results

**Date**: December 2025

---

## Summary

| Check | Result | Status |
|-------|--------|--------|
| 1. Broader Convergence | All 4 parameter sets converge (1-3% change) | ✅ PASS |
| 2. Initial Condition Independence | CV = 32% (different final states) | ⚠️ PARTIAL |
| 3. Conserved Quantities | Only E conserved; Q, N vary | ⚠️ PARTIAL |
| 4. Analytical Approximation | Simple ansatz off by ~78% | ❌ NEEDS WORK |

**Overall**: 1.5/4 strong passes, needs refinement

---

## Detailed Results

### Check 1: Broader Convergence ✅

Convergence is **GENERIC**, not accidental:

| Parameters | 24³ → 32³ Change |
|------------|------------------|
| g_rt=5, m_tau=16 | 1.7% |
| g_rt=3, m_tau=16 | 2.3% |
| g_rt=8, m_tau=16 | 2.9% |
| g_rt=5, m_tau=12 | 0.3% |

All parameter sets show convergent behavior. This rules out fine-tuning.

### Check 2: Initial Condition Independence ⚠️

Different initial shapes lead to different final radii:

| Initial | R_final |
|---------|---------|
| narrow | 1.418 |
| standard | 2.318 |
| wide | 2.965 |
| asymmetric | 1.991 |
| ring | 2.207 |

**CV = 32%** - significant variation.

**Interpretation**: 
- The system has **multiple attractor states** or a **continuous family of attractors**
- Different initial energy/amplitude leads to different final size
- This is actually physically reasonable (different particle masses)

### Check 3: Conserved Quantities ⚠️

| Quantity | Variation | Status |
|----------|-----------|--------|
| Energy E | 0.00% | ✅ CONSERVED |
| Charge Q | 33% | ❌ varies |
| Number N | 53% | ❌ varies |

**Interpretation**:
- Energy conservation excellent (as expected from symplectic integrator)
- No obvious topological charge found
- The bound state behaves like an **oscillon** rather than a **topological soliton**

This doesn't disprove genuine emergence, but suggests the stability mechanism is **energetic** (local energy minimum) rather than **topological** (winding number protection).

### Check 4: Analytical Approximation ❌

Simple Gaussian variational ansatz:

| Quantity | Analytic | Numeric | Error |
|----------|----------|---------|-------|
| Radius | 0.50 | 2.32 | 78% |
| Frequency | 91 | 32 | 184% |

The simple ansatz **fails badly**.

**Reasons**:
1. The ρ-τ coupling creates a more complex potential landscape
2. The actual bound state isn't Gaussian
3. Need more sophisticated ansatz (e.g., double exponential, or numerical profile)

---

## Physics Assessment

### What the checks reveal:

**Strengths**:
1. ✅ Convergence is generic - not a numerical accident
2. ✅ Energy perfectly conserved - good numerics
3. ✅ Bound states exist across parameter space

**Weaknesses**:
1. ⚠️ No topological protection - could be long-lived oscillon
2. ⚠️ Initial conditions affect final state - not universal attractor
3. ❌ Simple analytics don't match - theory not yet predictive

### Classification

The QMRT v3 bound states appear to be:

> **Oscillons** (long-lived quasi-bound states) rather than **topological solitons** (topologically protected)

This is still physically meaningful:
- Oscillons exist in real field theories
- They can have very long lifetimes
- But they are **not** absolutely stable

### Implications

1. The stability we observed is **energetic** not **topological**
2. The structures might eventually decay on very long timescales
3. The theory needs a **symmetry/topological mechanism** for true stability

---

## Recommendations

### To strengthen the theory:

1. **Add discrete symmetry**: τ → -τ could create kink-like topological states

2. **Add gauge symmetry**: Local U(1) would give topologically protected vortices

3. **Improve analytical model**: Use numerical ground state profile, not Gaussian

4. **Test very long times**: See if oscillons eventually decay

5. **Look for breather resonances**: Periodic solutions have different stability character

---

## Verdict

> QMRT v3 produces **genuine emergent structure** (convergent, generic) but the structures are **oscillons**, not topological solitons.
>
> The theory demonstrates real physics but needs additional structure (symmetry protection) for absolute particle stability.

This is a common situation in field theory - oscillons are the "almost particles" that exist before topological considerations are added.
