# QMRT v2: Normal Mode Spectrum Analysis

**Date**: December 2025  
**Analysis Type**: Linearized normal mode spectrum  
**Methodology**: Measure first, then interpret (as requested)

---

## Executive Summary

The complete normal-mode spectrum analysis of the QMRT v2 two-field system reveals:

| Branch | Gap ω(0) | Asymptotic Speed | Classification | Physical Role |
|--------|----------|------------------|----------------|---------------|
| 1 (φ-dominated) | 0.458 | 1.0 | **Massive Klein-Gordon** | Massive propagating mode |
| 2 (ω-dominated) | 2.828 | 0.224 | **Optical/Higgs-like** | Confinement/structure |

**Key Finding**: Both branches are **gapped** (massive). There is no true gapless acoustic mode in the current parameterization.

---

## 1. Methodology

### Linearization Around Background
Background state: ω = ω₀ = 1, φ = 0, π_ω = π_φ = 0

For small perturbations δω, δφ ~ e^{i(kx - ωt)}, the equations become:

```
ω² [δω]   =  [K_ω k²/M_ω + 8aω₀²/M_ω      0                    ] [δω]
   [δφ]      [0                            K_φ k²/M_φ + m²_eff/M_φ] [δφ]
```

where m²_eff = m²_φ + 2g·ω₀² (effective φ mass including coupling)

**Note**: The cross-coupling vanishes at the background (∂²V_int/∂ω∂φ = 0 when φ=0).

---

## 2. Branch Structure (Default Parameters)

Parameters: M_ω=1, K_ω=0.05, a=1, ω₀=1, M_φ=1, K_φ=1, m²_φ=0.01, g=0.1

### Branch 1 (Lower Frequency)
- **Gap**: ω(0) = 0.458
- **Dispersion**: ω² = c²k² + m² with c ≈ 1.0, m ≈ 0.458
- **Group velocity**: v_g → 0 as k → 0, v_g → c as k → ∞
- **Classification**: GAPPED, propagating at high k
- **Character**: Massive Klein-Gordon (relativistic massive scalar)

### Branch 2 (Higher Frequency)
- **Gap**: ω(0) = 2.828 = √8 (from double-well curvature)
- **Dispersion**: Weakly dispersive, nearly flat
- **Group velocity**: v_g ≈ 0.22 (slow)
- **Classification**: GAPPED, weakly propagating (optical phonon)
- **Character**: Optical/Higgs-like (localized oscillations)

---

## 3. Critical Physics Discovery

### The Coupling Generates Mass (Higgs Mechanism Analog)

The interaction term V_int = g·ω²·φ² generates an effective mass for φ:

```
m²_eff = m²_φ + 2g·⟨ω⟩² = 0.01 + 2(0.1)(1)² = 0.21
```

**This is mathematically identical to the Higgs mechanism!**

- The ω field has a nonzero VEV: ⟨ω⟩ = ω₀ = 1 (condensate)
- The φ field couples to this condensate
- The coupling "gives mass" to φ

### Stability Analysis

| g value | m²_eff | gap_φ | Stable? |
|---------|--------|-------|---------|
| 0.000 | 0.010 | 0.100 | YES |
| 0.050 | 0.110 | 0.332 | YES |
| 0.100 | 0.210 | 0.458 | YES |
| 0.200 | 0.410 | 0.640 | YES |
| 0.500 | 1.010 | 1.005 | YES |

The system is stable for all tested g ≥ 0.

---

## 4. Conditions for Gapless (Photon-like) Mode

To achieve gap_φ = 0, need m²_eff = m²_φ + 2g·ω₀² = 0

### Option A: Decoupled Fields (g = 0, m²_φ = 0)
- φ becomes a free massless scalar
- Dispersion: ω = c·k (pure acoustic)
- **Drawback**: No interaction with ω structure

### Option B: Fine-tuned Negative Mass (m²_φ = -2g·ω₀²)
- Can achieve exact gaplessness
- Requires negative bare mass
- Potentially unstable in some regimes

### Option C: Gauge Symmetry (Vector Field)
- Replace scalar φ with vector A_μ
- Gauge invariance protects masslessness
- More complex but physically motivated

---

## 5. Assessment of Two-Branch Picture

### Is it Complete?
✅ YES - For a two-scalar-field system, exactly 2 branches exist.

### Is it Approximate?
⚠️ YES - The linearized analysis only captures small-amplitude physics. Near domain walls or high-amplitude excitations, nonlinear effects may introduce additional physics.

### Is it Missing Major Physics?
| Missing Feature | Present in Current Model? |
|-----------------|---------------------------|
| Gapless (photon) mode | NO - both branches gapped |
| Localized solitons | YES - ω field supports domain walls |
| Propagation | YES - Branch 1 propagates at c ≈ 1 |
| Relativity (Klein-Gordon) | YES - Branch 1 follows ω² = c²k² + m² |
| Gauge invariance | NO - would need vector field |
| Goldstone mode | NO - discrete symmetry only |

---

## 6. Physical Interpretation

The QMRT v2 system models:

1. **ω field**: A Higgs-like condensate with VEV ω₀
   - Creates domain walls (confinement)
   - Provides "mass" to the φ field via coupling
   - Optical phonon dispersion

2. **φ field**: A massive propagating scalar
   - Acquires mass from ω condensate
   - Follows Klein-Gordon dispersion
   - Can carry information at speeds up to c_φ

**This is analogous to**:
- Standard Model: Higgs + massive scalar (but not the actual Higgs mechanism which gives mass to fermions)
- Condensed matter: Superfluid order parameter + phonon (but massive phonon)

---

## 7. Recommendations

### For Emergent Light (True Photon Analog)
Need gapless mode → Options:
1. Introduce gauge symmetry (vector field φ → A_μ)
2. Use continuous symmetry breaking for Goldstone mode
3. Accept that current model has only massive propagation

### For Current Model
The two-branch structure is **correct and complete** for:
- Massive particle propagation
- Confinement via domain walls
- Higgs-like mass generation

The model does NOT naturally produce a photon but can produce:
- Massive bosons (like W, Z in electroweak theory)
- Massive scalar excitations (like Higgs itself)

---

## 8. Files Created

- `/app/backend/qmrt_confinement/normal_mode_analysis.py` - Full eigenvalue computation
- `/app/backend/qmrt_confinement/deep_branch_analysis.py` - Dispersion classification
- `/app/backend/qmrt_confinement/gapless_mode_investigation.py` - Parameter sweeps
- `/app/backend/qmrt_confinement/dispersion_spectrum.png` - Visualization
