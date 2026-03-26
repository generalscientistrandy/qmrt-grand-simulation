# QMRT (Quark Medium Relativity Theory) - Product Requirements

## Original Problem Statement
Conduct a deep, iterative scientific investigation to derive a candidate fundamental theory of physics (QMRT) where:
- Stable, particle-like structures emerge from classical nonlinear topological medium dynamics
- Quantum mechanics (fermion statistics, Pauli exclusion, quantization) emerges from topology
- Mathematical rigor with honest claim vs evidence tracking

## Core Requirements
1. **Simulation Engine**: Mathematical modeling scripts for topological phenomena
2. **Core Physics Validation**: Prove quantum mechanics arises from emergent topology
3. **Theoretical Rigor**: Maintain exact mathematical honesty, document claims vs evidence

## Validation Levels

### Level 1: Energetic Selection ✅ COMPLETE
- Antisymmetric states have lower energy
- Pauli exclusion from energy penalty
- Files: `pauli_exclusion_test.py`

### Level 2: Global Exchange Topology ✅ COMPLETE (with SU(2) input)
- Berry phase π for defect exchange
- Spinor frames with 360° = -1
- Files: `frame_defect_test.py`, `parallel_transport_test.py`, `spinor_order_parameter_test.py`

### Level 3: Field-Theoretic Consistency ❌ OPEN
- Relativistic dispersion
- Lorentz covariance
- Causal propagation

## Complete Validation Results (December 2025)

### A3: Explicit Parallel Transport ✅
- Holonomy `U_γ = P exp(∮ A·dl)` computed from connection
- SO(3) (α=1): slope 1.99 → boson
- SU(2) (α=0.5): slope 0.99 → **fermion**

### A2: Spinor Order Parameter ✅
- Spinor field Ψ ∈ C² with Berry connection
- w=1 vortex → holonomy = -0.997 → fermion
- No manual factor needed IF medium is spinor-valued

### B1: Configuration Space Topology ✅
- π₁(two-defect config space) = ℤ₂
- Topology PERMITS ±1 but does NOT FORCE the sign
- Sign determined by internal structure (SU(2) vs SO(3))

### B2: Torsion → Spin Connection ✅
- Phase = α × 2πw (verified)
- α = 1/2 gives fermion, α = 1 gives boson
- The 1/2 is NOT derived from medium — it's a model input

### B3: Clifford Algebra ❌
- Pauli matrices satisfy {σ_i, σ_j} = 2δ_{ij}
- Medium frame vectors orthonormal but insufficient
- Medium ALONE does not generate Clifford algebra
- Spinor structure must be ADDED

### Branch Web Test 🔥 NEW DIRECTION
- Self-crossings with 2π phase give -1 holonomy
- Crossing operators are NON-COMMUTATIVE
- Non-Abelian structure detected!

## The Fundamental Gap

**What QMRT has proven:**
- Defects from medium ✅
- ℤ₂ topology permitting ±1 ✅
- Geometric holonomy selecting statistics ✅
- Consistent fermion phenomenology with α=1/2 ✅

**What remains open:**
- Why SU(2) instead of SO(3)?
- Why α = 1/2 instead of α = 1?

## The Open Direction: Branch Web Hypothesis

> SU(2)-type structure may emerge from ordered transport through a self-interacting branch web whose crossings and self-crossings generate double-cover behavior.

Model: W = (V, E, C) where V=nodes, E=segments, C=crossing rules
Transport: U(γ) = ∏ U_e X_c (product of segment and crossing operators)

## Architecture
```
/app/backend/qmrt_topology/     # Active simulation scripts
/app/memory/                    # Scientific documentation
  - QMRT_COMPLETE_STATUS.md     # Comprehensive summary
  - QMRT_CLAIM_VS_EVIDENCE.md   # Master claim table
```

## Next Tasks (Prioritized)
1. **P0**: Refine branch web model — tune crossing operators for π holonomy
2. **P1**: Physical mechanism — what creates self-crossings in medium?
3. **P2**: Level 3 - Relativistic consistency
4. **P3**: 3D Fermi pressure simulation
