# Branch B: Complex Scalar QMRT - Initial Results

## Date: April 2026

## Executive Summary

**Branch B (complex scalar) enables topology, but β-asymmetry does NOT pin vortices.**

| Test | Result |
|------|--------|
| Vortex formation | ✓ Vortices can be initialized |
| Vortex lifetime | ~1600 steps (64 time units) |
| Vortex-antivortex annihilation | ✓ Occurs rapidly (~12 time units) |
| Pinning in β-biased regions | ✗ No significant effect |
| Vortex-vortex interaction | ✓ Opposite charges annihilate |

---

## 1. What Works

### Vortices Exist
Complex scalar field ψ = |ψ|e^{iθ} supports:
- Phase winding (θ winds around vortex core)
- Amplitude zeros (|ψ| = 0 at vortex center)
- Proper winding number detection

### Vortex-Antivortex Annihilation
| Initial Separation | Time to Annihilate |
|-------------------|-------------------|
| 20 grid units | ~12 time units |

Opposite-charge vortices **attract and annihilate** - classic topological behavior.

### Single Vortex Lifetime
| Damping (γ) | Lifetime |
|-------------|----------|
| 0.001-0.01 | ~1600 steps (64 time units) |

Single vortices decay eventually (dissipative system doesn't conserve charge).

---

## 2. What Doesn't Work

### β-Asymmetry Does NOT Pin Vortices

| Condition | Inside Density | Outside Density | Ratio |
|-----------|----------------|-----------------|-------|
| Uniform β | 1.60 | 5.43 | 1.21 |
| Biased β | 1.77 | 6.13 | 1.18 |

**No improvement**: Vortices don't preferentially survive in high-β regions.

### Why?

Vortex dynamics are governed by:
1. Phase gradients (not β)
2. Energy minimization (vortex cores cost energy)
3. Damping (γ) - which was lower inside, helping slightly

The β coupling affects τ (medium speed), but vortex stability depends on:
- Core energy
- Phase gradients
- Interactions with other vortices

β-asymmetry from Branch A (organization localization) operates on a **different mechanism** than vortex dynamics.

---

## 3. Key Insight

### Two Separate Phenomena

| Mechanism | Affected by β? | Provides interaction? |
|-----------|----------------|----------------------|
| Organization (S) localization | ✓ Yes | ✗ No |
| Vortex dynamics | ✗ No | ✓ Yes |

**β-asymmetry and topology operate independently.**

- β localizes organization (Paper 3 / Branch A)
- Vortices provide interaction (Branch B)
- But β does NOT control vortices

---

## 4. What Would Be Needed for Vortex Pinning

For vortices to pin to specific regions, need:

1. **Energy landscape modification** - Not just β, but actual potential well for vortex cores
2. **Inhomogeneous damping** (tried - small effect)
3. **Topological trapping** - Boundary conditions that confine vortices
4. **Nonlinear self-interaction** - Makes vortex cores energetically favorable

Current model lacks these.

---

## 5. Conclusions

### Branch B Enables Topology
✓ Complex scalar field supports vortices
✓ Vortices interact (attract/annihilate)
✓ True topological defects exist

### But Topology is Independent of β-Asymmetry
✗ β-asymmetry does not pin vortices
✗ Organization localization (Branch A) and vortex dynamics (Branch B) are separate

### For Matter-Like Behavior
Would need to combine:
1. Localization mechanism (β-asymmetry works for S)
2. Topological pinning (need additional physics)
3. Vortex persistence (need lower dissipation or conservation)

---

## 6. Theoretical Summary

| Branch | Model | Key Finding | Limitation |
|--------|-------|-------------|------------|
| A | Real scalar | β localizes S (14×) | No topology |
| B | Complex scalar | Vortices exist & interact | β doesn't pin them |

**The missing ingredient for matter-like behavior is a mechanism that connects localization to topology.**

Current options:
1. Nonlinear potential that traps vortices at high-β
2. Explicit vortex-medium coupling
3. Different field structure (vector, gauge)

---

## 7. Files

- `complex_scalar_qmrt.py` - Branch B simulator
- Test results in memory (not saved - vortices don't persist)
