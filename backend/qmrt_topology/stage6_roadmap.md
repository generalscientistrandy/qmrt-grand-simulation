# QMRT Stage 6 Roadmap

## High-Impact Next Steps

---

## Current Status

### The Closed Causal Stack (Complete)

```
1. DISCRETE SOURCE
   ρ_τ = Σ τ_v δ(x - x_v)
         │
         ↓
2. CONNECTION CONSTRUCTION
   ω_μ = Σ τ_v G_μ(x - x_v)
   dω = 2πρ_τ · vol₂
         │
         ↓
3. HOLONOMY
   ∮ω = 2πτW
         │
         ↓
4. SPINORIAL TRANSPORT
   ψ → e^{iπτW}ψ
         │
         ↓
5. COUPLING LOCK
   α = -τ/2 (derived)
         │
         ↓
6. ACTION
   S = ∫ψ̄(iγ^μ∂_μ - (τ/2)γ^μω_μ)ψ d²x
```

### Position

| Aspect | Status |
|--------|--------|
| Internal consistency | ✅ |
| Parameter elimination | ✅ |
| Connection derived | ✅ |
| Form degrees explicit | ✅ |
| **Experimental validation** | ❌ |
| **3D extension** | ❌ |
| **Physical predictions** | ❌ |

---

## Priority 1: 3D Extension (Most Important)

### 1.1 Why This Matters

Currently:
- Everything is loop-based (1D objects in 2D space)
- Holonomy is abelian (U(1))
- No spacetime interpretation

For real physics:
- Need worldlines (1D in 4D) or flux tubes (2D in 4D)
- Spacetime torsion T^λ_μν ≠ 0
- Particles as torsion defects

### 1.2 The Lift

**2D (Current):**
- Loops γ encircle point defects
- ∮ω measures torsion enclosed
- Statistics from π₁(M - defects)

**3D Target:**
- Loops γ encircle line defects (worldlines)
- ∮ω measures torsion flux through loop
- Statistics from π₁(M - worldlines) or braid group

### 1.3 Key Equations to Derive

**3D torsion tensor:**
$$T^{\lambda}_{\mu\nu} = \Gamma^{\lambda}_{\mu\nu} - \Gamma^{\lambda}_{\nu\mu}$$

**3D connection (spin connection):**
$$\omega^{ab}_{\mu} = \mathring{\omega}^{ab}_{\mu} + K^{ab}_{\mu}$$

**Holonomy around line defect:**
$$\text{Hol}(\gamma) = \mathcal{P} \exp\left(\oint_\gamma \omega^{ab}_\mu \Sigma_{ab} dx^\mu\right)$$

where Σ_{ab} are Lorentz generators.

### 1.4 Expected Result

If the 2D → 3D lift works:
- Torsion lines = particle worldlines
- Holonomy around worldline = particle statistics
- τ = 1 worldline = fermion worldline

**This connects QMRT to real spacetime physics.**

---

## Priority 2: Particle Interpretation

### 2.1 The Proposal

**Identification:**
$$\rho_T = \text{(number of torsion defects)} / \text{(area)}$$

More precisely:
$$\rho_T(x) = \sum_i q_i \, \delta^{(2)}(x - x_i)$$

where q_i = τ_i is the torsion "charge" of particle i.

### 2.2 Questions to Answer

| Question | Physical Meaning |
|----------|------------------|
| Is torsion conserved? | Particle number conservation |
| Can torsion annihilate? | Particle-antiparticle annihilation |
| Is ∫ρ_T quantized? | Charge quantization |
| How does ρ_T evolve? | Particle dynamics |

### 2.3 Conservation Law

**Claim:** Torsion is conserved in the absence of sources/sinks.

From dω = 2πρ_τ vol₂ and d² = 0:
$$d(d\omega) = 0 = 2\pi d(\rho_\tau \, \text{vol}_2)$$

In 2D, d(ρ vol₂) = (dρ) ∧ vol₂ = 0 implies:
- Either ρ is constant, or
- The change in ρ is compensated by flux at boundaries

**This is the analog of charge conservation in electromagnetism.**

### 2.4 Torsion Annihilation

If two defects with τ = +1 and τ = -1 approach:
$$\rho_\tau = \delta(x - x_+) - \delta(x - x_-)$$

As x_+ → x_-:
$$\rho_\tau \to 0$$

**This is torsion annihilation = particle-antiparticle annihilation.**

---

## Priority 3: Cosmological Scaling

### 3.1 The Setup

Consider a 2D expanding universe with scale factor a(t).

Physical distances: r_phys = a(t) × r_comoving

### 3.2 Torsion Density Scaling

If torsion defects are comoving:
$$\rho_\tau^{\text{(phys)}} = \frac{N}{\text{physical area}} = \frac{N}{a^2 \cdot \text{comoving area}}$$

Therefore:
$$\boxed{\rho_\tau \sim \frac{1}{a^2} \quad \text{(2D)}}$$

In 3D:
$$\boxed{\rho_\tau \sim \frac{1}{a^3} \quad \text{(3D)}}$$

### 3.3 Physical Interpretation

This matches:
- **Matter density scaling**: ρ_matter ~ 1/a³
- **Particle dilution under expansion**

**Key test:** Does the torsion sector behave like:
- Radiation (1/a⁴)?
- Matter (1/a³)?
- Cosmological constant (1/a⁰)?
- New sector?

### 3.4 Equation to Derive

From the action with cosmological expansion:
$$S = \int \bar{\psi}(iγ^\mu D_\mu)\psi \sqrt{g} \, d^2x$$

where g = a²(t) is the metric determinant.

The dynamics of ρ_τ under expansion determines the cosmological behavior.

---

## Priority 4: Braid Group Extension (Anyons)

### 4.1 Current Situation

For integer τ:
- Statistics group: Z₂ = {±1}
- Fermions (τ = 1) and bosons (τ = 0)

For fractional τ:
- Holonomy: e^{iπτW} ∉ {±1}
- "Anyonic" phases

### 4.2 The Upgrade

Replace:
- Loop group π₁ → Braid group B_n
- Z₂ statistics → Anyonic statistics

In 2D:
$$B_n = \langle \sigma_1, ..., \sigma_{n-1} \mid \sigma_i\sigma_{i+1}\sigma_i = \sigma_{i+1}\sigma_i\sigma_{i+1}, [\sigma_i, \sigma_j] = 1 \text{ for } |i-j| > 1 \rangle$$

### 4.3 QMRT Representation

The braid group representation:
$$\sigma_i \to e^{i\theta}$$

where θ = πτ for QMRT defects.

**This unifies:**
- τ = 0: bosons (θ = 0)
- τ = 1: fermions (θ = π)
- τ = 1/m: anyons (θ = π/m)

### 4.4 Physical Relevance

Anyons appear in:
- Fractional quantum Hall effect
- Topological quantum computing
- 2D condensed matter systems

**QMRT provides a geometric origin for anyonic phases.**

---

## Implementation Plan

### Phase 1: Precision (Immediate)

- [x] Form degree clarification (differential_forms_notation.md)
- [x] Connection construction verified (stage5d)
- [ ] Clean theorem statement in single document

### Phase 2: 3D Extension (Next)

1. Define 3D torsion tensor from defect lines
2. Compute holonomy in 3D spin connection
3. Show fermionic statistics for τ = 1 worldlines
4. Connect to Einstein-Cartan theory

### Phase 3: Physics (Following)

1. Particle interpretation with conservation laws
2. Cosmological scaling under expansion
3. Braid group for anyonic extensions
4. Physical predictions for testing

---

## Success Criteria

| Milestone | Criterion |
|-----------|-----------|
| 3D Extension | Holonomy around worldline → Z₂ |
| Particle Interpretation | Conservation law derived |
| Cosmological | Scaling law ρ ~ 1/a³ derived |
| Anyons | Braid group representation constructed |

---

*Document created: December 2025*
*Status: Roadmap for Stage 6*
