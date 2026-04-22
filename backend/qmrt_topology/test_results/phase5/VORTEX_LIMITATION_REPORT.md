# Phase 5: Vortex Topology Tests - FUNDAMENTAL LIMITATION

## Date: April 2026

## Executive Summary

**FINDING: The scalar wave equation is inherently irrotational - no vortices can form.**

The "vortex" detection method computed vorticity (curl of velocity-like field), but:
- A scalar wave field φ with velocity v = ∇φ is **irrotational by definition**: ∇ × ∇φ = 0
- The model uses a single scalar field, not a vector field
- No topological defects can exist in a simply-connected scalar field

This is not a parameter issue - it's a **structural limitation** of the current model.

---

## 1. The Test Attempted

We tried to run three probes:
1. **Pinning test** - Do vortices preferentially form in high-β regions?
2. **Mobility test** - Are vortices free or pinned?
3. **Interaction test** - Do vortices attract/repel?

**Result: All tests return zero vortices** because the model cannot produce them.

---

## 2. Why No Vortices Exist

### The Mathematics

The wave equation:
$$\frac{\partial^2 \phi}{\partial t^2} = c_{eff}^2 \nabla^2 \phi - \gamma \frac{\partial \phi}{\partial t}$$

If we define a "velocity" field from φ:
$$\mathbf{v} = \nabla \phi$$

Then by vector calculus identity:
$$\nabla \times \mathbf{v} = \nabla \times (\nabla \phi) = 0$$

**Vorticity is identically zero** for any scalar field's gradient.

### What Would Be Needed for Vortices

Vortices require:
1. **Vector field** (e.g., fluid velocity, electromagnetic field)
2. **Complex scalar field** (phase can wind → topological defects)
3. **Multiple coupled fields** (creates effective rotation)

The current single real scalar field φ cannot support topological defects.

---

## 3. What This Means

### For the Theory Progression

| Paper | Finding | Status |
|-------|---------|--------|
| Paper 1 | Lifecycle statistics | ✓ |
| Paper 2 | Energy sustains organization | ✓ |
| Paper 3 | β asymmetry localizes (no interaction) | ✓ |
| Phase 5 | Topology provides interaction | **NOT TESTABLE** |

The current model has **no topology** to test.

### The Missing Ingredient

To test whether topology provides interaction, the model needs extension:

**Option A: Complex scalar field**
$$\psi = |\psi| e^{i\theta}$$
- Phase θ can have winding numbers
- Vortices = points where ψ = 0 with nonzero winding
- This is standard in superfluids, BEC, etc.

**Option B: Vector field**
$$\mathbf{A} = (A_x, A_y, A_z)$$
- Natural vorticity: ω = ∇ × A
- Topological defects from field configurations

**Option C: Coupled scalar fields**
$$(\phi_1, \phi_2) \rightarrow$$ effective rotation in field space
- Can create skyrmions, etc.

---

## 4. Recommendation

### Do NOT Proceed with Vortex Tests

The current scalar wave model cannot produce vortices. Continuing to "test" them is meaningless.

### Next Steps (Two Options)

**Option 1: Extend to complex scalar field (minimal change)**
- Replace φ ∈ ℝ with ψ ∈ ℂ
- Wave equation becomes: ψ_tt = c² ∇²ψ - γ ψ_t
- Vortices appear as phase singularities
- This is the minimal extension for topology

**Option 2: Accept the limitation and document**
- Paper 3 conclusion stands: β asymmetry localizes but doesn't produce interaction
- The constraint is: "real scalar field → no topological interaction"
- Future work requires model extension

---

## 5. Conclusion

**The vortex tests failed not due to parameter tuning, but due to fundamental mathematical structure.**

A single real scalar wave field is irrotational by construction. No amount of β asymmetry, damping adjustment, or initial conditions can create vortices.

To test whether topology provides the missing interaction:
1. Extend to complex scalar field (ψ = |ψ|e^{iθ})
2. Or acknowledge this as a model limitation

This is a **clean negative result** that sharpens the theory:
> "Real scalar wave + relaxation → organization wells without interaction or topology"

---

## 6. Files

- `run_vortex_tests.py` - Test script (shows zero vortices)
- `vortex_tests_results.json` - Empty results
