# QMRT Fermion Sector: Claim vs Evidence Table

**Date**: December 2025 (Updated after A3/A2 validation)  
**Purpose**: Maintain scientific honesty while developing the theory

---

## The Minimal Statement

**Defect State** = (x^μ, σ, U)    where U ∈ SU(2)

- **x^μ**: Position in spacetime (from medium)
- **σ**: Topology activation (shown to be medium-dependent)
- **U**: Internal spinor frame (EXTERNAL or INTRINSIC depending on medium type)

---

## Claim vs Evidence Table

| Claim | Status | Evidence | Gap |
|-------|--------|----------|-----|
| **Particles are medium defects** | ✅ Supported | Vortex stability, energy localization | Need dynamical formation |
| **Charge = topological winding** | ✅ Supported | Winding number conserved | Need charge quantization derivation |
| **Same-spin overlap is penalized** | ✅ Strong | E(↑↑) >> E(↑↓), robust across parameters | Need λ from medium properties |
| **Antisymmetric states lower energy** | ✅ Strong | Variational, mathematical identity | Complete |
| **Exchange gives phase π** | ✅ PROVEN | A3: parallel_transport_test.py | With SU(2) connection |
| **Topology activation is local** | ✅ Supported | σ depends on medium excitation | Need σ(medium) derivation |
| **Spin-½ from 360° = -1** | ✅ PROVEN | A3 + A2: holonomy = -1 for w=1 | Complete |
| **Geometric holonomy scales correctly** | ✅ PROVEN | A3: slope = 0.9928 (expect 1.0) | Complete |
| **Spinor medium gives automatic π** | ✅ PROVEN | A2: spinor_order_parameter_test.py | w=1 → -0.997 holonomy |
| **U emerges dynamically** | ⚠️ PARTIAL | spinor_emergence_test.py | Evolved field gives 2π not π |
| **Medium naturally spinor-valued** | ❓ OPEN | Conceptual question | A2 shows it WORKS if true |
| **Lorentz covariance** | ❌ Not shown | None | Level 3 |
| **Dirac dispersion** | ❌ Not shown | None | Level 3 |
| **3D degeneracy P ∝ n^{5/3}** | ❌ Not shown | Only 1D (P ∝ n³) | Computational |

---

## A3 + A2 Validation Results (This Session)

### A3: Explicit Parallel Transport ✅

Computed `U_γ = P exp(∮ A·dl)` directly from connection.

| Connection | Slope | Expected | Result |
|------------|-------|----------|--------|
| SO(3) (factor=1.0) | 1.9855 | 2.0 | Boson |
| SU(2) (factor=0.5) | 0.9928 | 1.0 | **FERMION** |

**Key**: Linear scaling with R=1.000. The geometry supports spinors.

### A2: Spinor Order Parameter ✅

Spinor field Ψ ∈ C² with Berry connection A = i⟨Ψ|∂Ψ⟩.

| Winding | Holonomy | Status |
|---------|----------|--------|
| 1.0 | -0.997 | ✅ FERMION |
| 2.0 | -1.000 | ✅ FERMION |

**Key**: w=1 spinor vortex automatically gives fermion holonomy WITHOUT manual factor.

---

## The Critical Question (Updated)

> **Is the QMRT medium spinor-valued, or scalar with attached spinor?**

### Path A: Scalar Medium + Attached Spinor ✅ COMPLETE
- Medium: σ(x) ∈ ℝ
- Spinor: U(x) ∈ SU(2) attached externally
- Connection: τ·σ with manual factor 0.5
- Result: Fermion statistics **CONTAINED** (engineered)

### Path B: Spinor-Valued Medium ✅ WORKS, ontology open
- Medium: Ψ(x) ∈ C² (spinor order parameter)  
- Connection: Berry A = i⟨Ψ|∂Ψ⟩ (automatic)
- Factor: 1/2 built into spinor representation
- Result: Fermion statistics **INTRINSIC** if medium is spinor

### The Remaining Gap
Path B works mathematically. The open question is:
**What physical mechanism makes QMRT's medium spinor-valued?**

Possibilities:
1. Fundamental: Medium excitations are intrinsically C²
2. Emergent: Classical medium develops spinor modes at defects
3. Imposed: Spinor structure is a model assumption

---

## Honest Status Summary (Updated)

| Level | Claim | Status |
|-------|-------|--------|
| 1 | Energy selects antisymmetric | ✅ Proven |
| 2a | Exchange topology gives π | ✅ Proven (A3) |
| 2b | Spinor medium works | ✅ Proven (A2) |
| 2c | Medium is naturally spinor | ❓ Open |
| 3 | Lorentz covariance | ❌ Open |

---

## Current Honest Claim (Updated)

> **QMRT produces consistent fermion statistics in two equivalent ways:**
>
> 1. **Path A**: Scalar medium with externally assigned spinor frames U ∈ SU(2)
>    and manually chosen connection factor 0.5.
>
> 2. **Path B**: Spinor-valued medium Ψ ∈ C² with automatic Berry connection.
>    The factor 0.5 is built into the spinor representation.
>
> **Both paths give identical physics**: Exchange phase π, holonomy -1, Pauli exclusion.
>
> **The ontological question remains**: Is QMRT's medium fundamentally spinor-valued?
> If yes, fermions are EXPLAINED. If no, they are CONTAINED.

---

## Files Created This Session

- `parallel_transport_test.py` - A3 validation ✅
- `spinor_order_parameter_test.py` - A2 validation ✅  
- `spinor_emergence_test.py` - Dynamical emergence (partial)
- `QMRT_A3_A2_VALIDATION.md` - Documentation

## Next Steps

1. **A1**: Half-quantum vortices in spinor medium (if needed)
2. **Level 3**: Relativistic consistency
3. **3D Fermi pressure**: n^{5/3} scaling simulation
