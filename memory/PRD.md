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

### Level 2: Global Exchange Topology ✅ COMPLETE  
- Berry phase π for defect exchange
- Spinor frames with 360° = -1
- Files: `frame_defect_test.py`, `parallel_transport_test.py`, `spinor_order_parameter_test.py`

### Level 3: Field-Theoretic Consistency ❌ OPEN
- Relativistic dispersion
- Lorentz covariance
- Causal propagation

## Session Progress (December 2025)

### A3: Explicit Parallel Transport ✅
- Holonomy `U_γ = P exp(∮ A·dl)` computed from connection
- SU(2) connection (factor=0.5): Linear scaling, π holonomy for w=1

### A2: Spinor Order Parameter ✅
- Spinor field Ψ ∈ C² with Berry connection
- w=1 vortex automatically gives -1 holonomy (fermion)
- No manual factor needed

### Key Finding
Two equivalent paths to fermion statistics:
1. **Path A**: Scalar medium + external spinor + manual factor (CONTAINS fermions)
2. **Path B**: Spinor medium + automatic Berry connection (EXPLAINS fermions if medium is spinor)

Ontological question open: Is QMRT medium fundamentally spinor-valued?

## Architecture
```
/app/backend/qmrt_topology/     # Active simulation scripts
/app/memory/                    # Scientific documentation
  - QMRT_CLAIM_VS_EVIDENCE.md   # Master claim table
  - QMRT_A3_A2_VALIDATION.md    # This session's results
```

## Next Tasks (Prioritized)
1. **P1**: Level 3 - Relativistic consistency
2. **P1**: 3D Fermi pressure - n^{5/3} scaling
3. **P2**: A1 Half-quantum vortices (if needed)
4. **P3**: Frontend visualization overhaul
