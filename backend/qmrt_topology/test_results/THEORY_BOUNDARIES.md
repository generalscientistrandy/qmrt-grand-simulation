# QMRT Theory Boundaries: Complete Summary

## April 2026

---

## Executive Summary

Two model branches have been fully characterized:

| Branch | Field | Localization | Interaction | Topology |
|--------|-------|--------------|-------------|----------|
| **A** (Real scalar) | φ ∈ ℝ | ✓ (14-32×) | ✗ | ✗ |
| **B** (Complex scalar) | ψ ∈ ℂ | ✗ | ✓ | ✓ |

**Key finding**: Localization and interaction are **separable mechanisms** in the current framework.

---

## Branch A: Real Scalar QMRT

### Model
$$\frac{\partial^2 \phi}{\partial t^2} = c_{eff}^2 \nabla^2 \phi - \gamma \frac{\partial \phi}{\partial t}$$

### Capabilities
- ✓ Structure formation follows statistical laws (Paper 1)
- ✓ Organization requires sustained energy (Paper 2)
- ✓ β-asymmetry localizes organization: S contrast up to **32×** (Paper 3)
- ✓ Energy-organization decoupling

### Limitations
- ✗ Multiple organization wells do NOT interact
- ✗ No topological defects (∇×∇φ = 0 identically)
- ✗ Cannot test topology-mediated interaction

### Conclusion
> Real scalar fields support **parameter-induced organization wells** but not interacting structures.

---

## Branch B: Complex Scalar QMRT

### Model
$$\frac{\partial^2 \psi}{\partial t^2} = c_{eff}^2 \nabla^2 \psi - \gamma \frac{\partial \psi}{\partial t}$$

where ψ = |ψ|e^{iθ} ∈ ℂ

### Capabilities
- ✓ Vortices exist (phase winding, amplitude zeros)
- ✓ Vortex-antivortex annihilation (~12 time units)
- ✓ Single vortex lifetime (~64 time units)
- ✓ Topological charge detected via winding number

### Limitations
- ✗ β-asymmetry does NOT pin vortices (density ratio unchanged)
- ✗ Vortices decay in dissipative system
- ✗ No spatial preference for high-β regions

### Conclusion
> Complex scalar fields support **topological interaction** but not β-controlled localization.

---

## The Structural Result

### What This Shows

| Mechanism | Branch A (Real) | Branch B (Complex) |
|-----------|-----------------|-------------------|
| Organization (S) responds to β | ✓ | ✓ |
| Vortices exist | ✗ | ✓ |
| Vortices respond to β | N/A | ✗ |
| Wells interact | ✗ | N/A |
| Vortices interact | N/A | ✓ |

### The Gap

**β-asymmetry and topology operate independently.**

- β controls organization (S) via τ_eq coupling
- Vortices are controlled by phase gradients and energy minimization
- These are **different mechanisms** that don't automatically couple

### Implication

> Neither Branch A nor Branch B alone yields matter-like behavior. Matter-like behavior—if it exists in this framework—requires a mechanism that **couples topological defects to spatially localized organization**.

---

## What Would Be Needed (Future Branch C)

To unify localization and interaction:

1. **Explicit vortex-β coupling**
   - Make vortex core energy depend on local β
   - E_vortex(x) = f(β(x))

2. **Nonlinear self-interaction**
   - Add |ψ|⁴ terms that create energy wells
   - Vortices trapped at energy minima

3. **Topological conservation**
   - Reduce dissipation so vortices persist
   - Or add mechanism that creates vortices continuously

---

## Papers Summary

| Paper | Question | Answer |
|-------|----------|--------|
| **1** | How do structures form? | Births at ρ peaks, persistence ∝ S, merges at ∇ρ |
| **2** | What sustains organization? | Energy input (S→0 without driving) |
| **3** | Can organization localize? | YES via β-asymmetry (14-32×), NO interaction |

| Branch | Question | Answer |
|--------|----------|--------|
| **A** | Does real scalar support topology? | NO (irrotational by construction) |
| **B** | Does complex scalar support β-pinning? | NO (vortices ignore β) |

---

## Theoretical Boundary Statement

> **The QMRT framework exhibits two separable phenomena:**
> 1. **Organization localization** (controlled by β-asymmetry, no interaction)
> 2. **Topological interaction** (vortex dynamics, not controlled by β)
>
> **These do not automatically couple.** Matter-like behavior—persistent, localized, interacting structures—requires additional physics that links topology to the medium's spatial properties.

---

## File Structure

```
/test_results/
├── BRANCH_A_COMPLETE.md     ← Real scalar summary
├── BRANCH_B_RESULTS.md      ← Complex scalar summary  
├── paper2/PAPER2_final.md   ← Long-path dynamics
├── paper3/PAPER3_final.md   ← Localization via β
├── phase4/                  ← Threshold analysis
├── phase5/                  ← Vortex tests
├── combined/OVERVIEW.md     ← Three-paper summary
└── THEORY_BOUNDARIES.md     ← This document
```

---

## Date

April 2026

## Status

**CLOSED** - Both branches fully characterized. Ready for Branch C if desired.
