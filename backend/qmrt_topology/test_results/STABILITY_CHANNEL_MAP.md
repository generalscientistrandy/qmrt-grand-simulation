# Stability Channel Map: Comparative Analysis of QMRT Branches

**Date:** December 2025  
**Purpose:** Visual comparison of stability mechanisms across theoretical branches

---

## Overview

The QMRT research program has naturally organized into three distinct theoretical branches, each testing different combinations of stability mechanisms. This map provides a systematic comparison.

---

## The Five Stability Channels

| Channel | Definition | Physical Requirement |
|---------|------------|---------------------|
| **1. Coherence** | Phase relationships maintained over time | Complex-valued field with U(1) symmetry |
| **2. Localization** | Energy/structure spatially concentrated | Spatial asymmetry in parameters (β, coupling) |
| **3. Topology** | Defects with conserved winding number | Complex field + nonlinear dynamics allowing vortices |
| **4. Interaction** | Defects influence each other | Topological attraction/repulsion, annihilation |
| **5. Lifetime Stabilization** | Structures persist against decay | Mechanism that extends natural lifetime |

**Composite Stability** (matter-like behavior) requires **co-alignment** of channels 1-5.

---

## Branch Comparison Matrix

```
                    ┌─────────────┬─────────────┬─────────────┬─────────────┐
                    │  BRANCH A   │  BRANCH B   │  BRANCH C   │  BRANCH E   │
                    │ Real Scalar │   Complex   │   Coupled   │  Resonance  │
                    │             │   Scalar    │   Complex   │  Contrast   │
┌───────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 1. Coherence      │     ✗       │     ✓       │     ✓       │     ✓       │
│                   │ (no phase)  │  (U(1))     │  (U(1))     │  (U(1))     │
├───────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 2. Localization   │     ✓       │     ✗       │   partial   │   partial   │
│                   │ (β-wells)   │ (uniform)   │  (β-wells)  │ (freq wells)│
├───────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 3. Topology       │     ✗       │     ✓       │     ✓       │     ✓       │
│                   │ (no defects)│ (vortices)  │ (vortices)  │ (vortices)  │
├───────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 4. Interaction    │     ✗       │     ✓       │     ✓       │     ✓       │
│                   │ (no contact)│(annihilate) │(annihilate) │ (suppressed)│
├───────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 5. Lifetime       │   partial   │   limited   │     ✓       │     ✓✓      │
│    Stabilization  │(local S↑)   │(decay only) │  (1.5-2×)   │ (2× single) │
├───────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 6. Annihilation   │     N/A     │     ✗       │     ✗       │     ✓✓✓     │
│    Suppression    │             │ (rapid)     │ (rapid)     │ (32-48×)    │
├───────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ COMPOSITE         │     ✗       │     ✗       │   partial   │  **strong** │
│ (Matter-like)     │             │             │             │             │
└───────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

### Branch E Key Discovery

**Adaptive resonance differentiation suppresses topological annihilation.**

| Mode | Single Vortex | Pair Lifetime |
|------|---------------|---------------|
| Baseline | 1850 | 80 |
| Partitioned | 3850 (2×) | 80 (1×) |
| Self-selecting | 3900 (2×) | 2600 (32×) |
| Combined | 3950 (2×) | 3840 (48×) |

The breakthrough: Self-selection allows vortices to dynamically differentiate their frequency signature, dramatically suppressing pair annihilation.

---

## Detailed Branch Profiles

### Branch A: Real Scalar Field

**File:** `qmrt_simulation_api.py`

**Theory:** Real-valued wave equation with β-dependent coupling:
$$\partial_t^2 \phi = c^2 \nabla^2 \phi - \gamma \partial_t \phi$$

**What it achieves:**
- ✓ Organization (S) localizes in high-β regions
- ✓ Energy remains uniform (no violation of conservation)
- ✓ Clear spatial asymmetry in dynamical structure

**What it lacks:**
- ✗ No phase → no coherence channel
- ✗ No topological defects possible
- ✗ Localized spots do NOT interact (Paper 3 result)

**Key Publication:** Paper 3 — "Localization via Coupling Asymmetry"

**Verdict:** Proves localization mechanism works, but cannot support topology or interaction.

---

### Branch B: Complex Scalar Field

**File:** `complex_scalar_qmrt.py`

**Theory:** Complex-valued wave equation with uniform parameters:
$$\partial_t^2 \psi = c^2 \nabla^2 \psi - \gamma \partial_t \psi$$

**What it achieves:**
- ✓ Phase winding → coherence channel active
- ✓ Vortices form with quantized winding
- ✓ Vortex-antivortex pairs interact and annihilate

**What it lacks:**
- ✗ No spatial asymmetry → vortices don't localize
- ✗ Vortices decay everywhere at same rate
- ✗ No mechanism to sustain vortex population

**Key Finding:** Topology exists but is spatially unbiased.

**Verdict:** Proves topology and interaction work, but no localization or stabilization.

---

### Branch C: Coupled Complex Scalar

**File:** `coupled_complex_scalar_qmrt.py`

**Theory:** Complex-valued wave equation with β-weighted gradient:
$$\partial_t^2 \psi = \nabla \cdot (\beta(x) \nabla \psi) - \gamma \partial_t \psi$$

**What it achieves:**
- ✓ Phase winding → coherence channel active
- ✓ Vortices form with quantized winding
- ✓ Vortex-antivortex pairs interact and annihilate
- ✓ Vortex lifetime extended 1.5-2× in high-β regions
- ~ Partial spatial bias in vortex survival

**What it lacks:**
- ✗ No true pinning — vortices still drift and decay
- ✗ Does not prevent close-pair annihilation
- ✗ Not a trapping mechanism, only stabilizing

**Key Finding:** β acts as stabilizer, not trap.

**Verdict:** Achieves partial co-alignment. Strongest candidate but still incomplete.

---

## Graphical Representation

### Channel Activation by Branch

```
Channel          Branch A    Branch B    Branch C
─────────────────────────────────────────────────
Coherence        ░░░░░░░░    ████████    ████████
Localization     ████████    ░░░░░░░░    ████░░░░
Topology         ░░░░░░░░    ████████    ████████
Interaction      ░░░░░░░░    ████████    ████████
Stabilization    ████░░░░    ██░░░░░░    ██████░░
─────────────────────────────────────────────────
Composite Score     2/5         3/5        4.5/5
```

Legend: █ = achieved, ░ = not achieved, ░░ = partial

---

### Co-Alignment Diagram

```
                 COHERENCE
                     │
                     │
        Branch B ────┼──── Branch C
           │         │         │
           │         │         │
           ▼         │         ▼
      TOPOLOGY ──────┼──── LOCALIZATION
           │         │         │
           │         │         │
           └─────────┼─────────┘
                     │
                     ▼
               INTERACTION
                     │
                     │
                     ▼
              STABILIZATION
                     │
                     │
                     ▼
        ┌────────────────────────┐
        │   COMPOSITE STABILITY  │
        │    (Matter-like)       │
        │                        │
        │  Branch A: ✗ blocked   │
        │  Branch B: ✗ blocked   │
        │  Branch C: ~ partial   │
        └────────────────────────┘
```

---

## Gap Analysis

### What's Missing for Full Composite Stability?

| Gap | Description | Potential Solution |
|-----|-------------|-------------------|
| **Pinning** | Vortices don't settle into stable positions | Explicit potential V(|ψ|, x) with position-dependent minima |
| **Annihilation Prevention** | Close pairs always annihilate | Repulsive core potential or gauge-field mediated repulsion |
| **Population Maintenance** | No steady-state vortex density | External driving that nucleates faster than decay |

### Required Physics for Matter-like Behavior

To achieve true composite stability, the model would need:

1. **Confinement mechanism** — not just slower decay, but actual potential minimum
2. **Charge separation** — way to keep opposite charges apart
3. **Dynamic equilibrium** — balance between creation and annihilation

This likely requires going beyond minimal wave-equation modifications.

---

## Summary Table

| Aspect | Branch A | Branch B | Branch C |
|--------|----------|----------|----------|
| **Field Type** | Real φ | Complex ψ | Complex ψ |
| **β-Coupling** | Yes (medium) | No | Yes (gradient) |
| **Supports Vortices** | No | Yes | Yes |
| **Vortex Lifetime** | N/A | ~500 steps | ~850 steps |
| **Spatial Bias** | Strong | None | Partial |
| **Interaction** | None | Annihilation | Annihilation |
| **Best Use** | Localization proof | Topology proof | Co-alignment test |
| **Paper** | Paper 3 | (documented) | Paper 4 (pending) |

---

## Conclusions

1. **Branch A** proved that spatial asymmetry (β-coupling) can localize organization without violating energy conservation. This is documented in Paper 3.

2. **Branch B** proved that complex scalar fields support topological defects (vortices) with genuine interaction (annihilation). However, without spatial asymmetry, there's no localization.

3. **Branch C** represents the closest approach to composite stability achieved so far:
   - Combines coherence, localization, topology, and interaction
   - β-coupling extends vortex lifetime by 1.5-2×
   - However, β acts as a **stabilizer, not a trap**
   - Full matter-like behavior remains out of reach with minimal coupling

4. **The path forward** (if pursued) would require stronger coupling mechanisms that provide true confinement — a qualitatively different physics addition, not just parameter tuning.

---

## File References

| Branch | Simulation Code | Key Results |
|--------|-----------------|-------------|
| A | `qmrt_simulation_api.py` | `paper3/PAPER3_final.md` |
| B | `complex_scalar_qmrt.py` | `phase5/VORTEX_LIMITATION_REPORT.md` |
| C | `coupled_complex_scalar_qmrt.py` | `phase5/BRANCH_C_DECISIVE_REPORT.md` |
