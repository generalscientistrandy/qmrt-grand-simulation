# QMRT Fermion Sector: Claim vs Evidence Table

**Date**: December 2025  
**Purpose**: Maintain scientific honesty while developing the theory

---

## The Minimal Statement

**Defect State** = (x^μ, σ, U)    where U ∈ SU(2)

- **x^μ**: Position in spacetime (from medium)
- **σ**: Topology activation (shown to be medium-dependent)
- **U**: Internal spinor frame (currently EXTERNAL)

---

## Claim vs Evidence Table

| Claim | Status | Evidence | Gap |
|-------|--------|----------|-----|
| **Particles are medium defects** | ✅ Supported | Vortex stability, energy localization | Need dynamical formation |
| **Charge = topological winding** | ✅ Supported | Winding number conserved | Need charge quantization derivation |
| **Same-spin overlap is penalized** | ✅ Strong | E(↑↑) >> E(↑↓), robust across parameters | Need λ from medium properties |
| **Antisymmetric states lower energy** | ✅ Strong | Variational, mathematical identity | Complete |
| **Exchange gives phase π** | ✅ Strong | Berry phase = 1.00π with spinor frames | **IF U is included** |
| **Topology activation is local** | ✅ Supported | σ depends on medium excitation | Need σ(medium) derivation |
| **Spin-½ from 360° = -1** | ✅ Strong | Spinor rotation verified | **IF U is included** |
| **U emerges from medium** | ❌ Not shown | None | **THE KEY GAP** |
| **Lorentz covariance** | ❌ Not shown | None | Level 3 |
| **Dirac dispersion** | ❌ Not shown | None | Level 3 |
| **3D degeneracy P ∝ n^{5/3}** | ❌ Not shown | Only 1D (P ∝ n³) | Computational |

---

## The Critical Question

> **Can U ∈ SU(2) arise from a deeper branch of the medium?**

### What U Needs To Be

1. An internal degree of freedom at each defect
2. Taking values in SU(2) (or equivalent)
3. Having the property: 2π rotation = -1
4. Parallel-transporting during defect motion

### Possible Medium Origins of U

| Mechanism | Medium Branch | SU(2) Structure? | Evidence |
|-----------|---------------|------------------|----------|
| **Torsion field τ** | Torsion | If τ ∈ so(3) → SU(2) via double cover | Need to check |
| **Phase gradient ∇θ** | Coherence | Direction field, but SO(3) not SU(2) | Unlikely |
| **Vortex core structure** | Topological | Core could have orientation | Need simulation |
| **Medium flow vorticity** | Density | ω = ∇×v defines axis | SO(3), not SU(2) |
| **Bi-vector field** | New branch? | Spinors as even Clifford subalgebra | Theoretical |

### The SO(3) vs SU(2) Problem

Most medium quantities give SO(3) (vectors, rotations):
- 2π rotation = +1 (identity)

Fermions require SU(2):
- 2π rotation = -1

**This is not automatic from classical medium physics.**

Possible resolutions:
1. **Topological origin**: The configuration space of defects has SU(2) structure
2. **Double cover**: Medium naturally lives on covering space
3. **Emergent**: SU(2) emerges at quantum activation threshold

---

## Honest Status Summary

### What QMRT Has Shown

| Level | Claim | Status |
|-------|-------|--------|
| 1 | Energy selects antisymmetric | ✅ Proven |
| 2 | Exchange topology gives π | ✅ Proven (with U) |
| 2b | U emerges from medium | ❌ Open |
| 3 | Lorentz covariance | ❌ Open |

### The Fork

```
Path A: "Medium theory that CONTAINS fermions"
  - Add U ∈ SU(2) as a postulate
  - Show statistics work
  - Consistent but not explanatory
  - Status: DONE ✅

Path B: "Medium theory that EXPLAINS fermions"
  - Derive U from medium dynamics
  - Show SU(2) structure emerges
  - Would be a major theoretical result
  - Status: OPEN ❓
```

---

## Research Directions for Path B

### Direction 1: Torsion Branch as Spinor

The torsion field τ could be promoted to spinor-valued:
```
τ: ℝ³ → SU(2)  instead of  τ: ℝ³ → SO(3)

If the medium naturally lives on the SU(2) covering space,
then defects would automatically have spinor frames.
```

**Test**: Can QMRT equations be written with τ ∈ SU(2)?

### Direction 2: Configuration Space Topology

The space of two-defect configurations has nontrivial topology:
```
(ℝ³ × ℝ³ - diagonal) / exchange ≅ ℝ³ × (ℝ³ - {0}) / Z₂

π₁ of this space is Z₂, which can carry ±1 representations.
```

**Test**: Does this give U automatically, or is U additional structure?

### Direction 3: Quantum Activation Creates U

At low excitation (σ ≈ 0): No internal structure
At high excitation (σ ≈ 1): U emerges as coherent mode

```
The spinor frame U could be the "phase" of a coherent internal excitation
that only exists when σ > threshold.
```

**Test**: Simulate medium with internal modes, see if SU(2) emerges.

### Direction 4: Geometric Algebra Approach

Spinors are even elements of Clifford algebra:
```
Spin(3) = even subalgebra of Cl(3) ≅ quaternions ≅ SU(2)

If the medium has a natural Clifford algebra structure
(via tangent space), spinors emerge automatically.
```

**Test**: Formulate QMRT in geometric algebra, see if spinors are natural.

---

## What Would Confirm Path B

To claim "QMRT explains fermions", need to show:

1. **U emerges dynamically**
   - Simulation of medium equations
   - U appears as stable internal mode
   - Not put in by hand

2. **U has SU(2) structure**
   - 2π rotation = -1 from dynamics
   - Not from assuming spinor form

3. **Exchange phase follows**
   - Berry phase π from emergent U
   - Without assuming exchange statistics

**This would be a major result in theoretical physics.**

---

## Current Honest Claim

> QMRT, with externally assigned spinor frames U ∈ SU(2), produces
> consistent fermion statistics including:
> - Pauli exclusion from energy penalty
> - Exchange phase π from Berry phase
> - Fermi-Dirac filling
>
> Whether U emerges from the medium itself remains open.

This is scientifically honest and still valuable:
- Shows the framework is CONSISTENT with fermions
- Identifies exactly what needs to be derived
- Points to specific research directions

---

## Next Steps

1. **Formalize the claim** (this document)
2. **Investigate τ ∈ SU(2)** (torsion as spinor)
3. **Check configuration space topology** (does it give U?)
4. **Test medium simulations** (do internal modes emerge?)

The goal is to move from "contains" to "explains".
