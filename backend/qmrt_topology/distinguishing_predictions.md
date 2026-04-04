# Distinguishing Predictions

## What Makes QMRT Falsifiable

---

## Abstract

This document presents explicit, falsifiable predictions that distinguish QMRT from standard physics. We identify three classes of predictions: (1) modified interference patterns under torsion background, (2) defect interaction potentials, and (3) cosmological corrections.

---

## 1. The Challenge

### 1.1 Generic Predictions (Not Enough)

Our current predictions:
- ρ ~ 1/a³ (matter-like scaling)
- ∂_μJ^μ = 0 (conservation)
- τ_+ + τ_- → 0 (annihilation)

**Problem:** These look like standard matter. Reviewers will ask: "How do I distinguish QMRT torsion particles from regular fermions?"

### 1.2 What We Need

ONE prediction that:
- Differs from standard physics
- Is in principle testable
- Has a clear signature

---

## 2. Prediction 1: Modified Aharonov-Bohm Phase

### 2.1 Standard Aharonov-Bohm Effect

A charged particle encircling a magnetic flux Φ acquires phase:

$$\phi_{AB} = \frac{e}{\hbar} \Phi = \frac{e}{\hbar} \oint A \cdot dl$$

This is independent of the particle's path (only depends on enclosed flux).

### 2.2 QMRT Prediction: Torsion-Modified Phase

In a torsioned medium, a spinor acquires an **additional** phase from the torsion connection:

$$\phi_{\text{QMRT}} = \phi_{AB} + \alpha \oint \omega$$

For a loop encircling a torsion defect with τ = 1:

$$\phi_{\text{QMRT}} = \phi_{AB} - \frac{1}{2} \cdot 2\pi W = \phi_{AB} - \pi W$$

### 2.3 Observable Difference

| Quantity | Standard AB | QMRT |
|----------|-------------|------|
| Phase | eΦ/ℏ | eΦ/ℏ - πW |
| For W = 1 | eΦ/ℏ | eΦ/ℏ - π |
| **Interference shift** | 0 | **-π** |

**Prediction:** In a medium with torsion defects, interference patterns show an additional π phase shift per encircled defect.

### 2.4 Falsifiability

- **Test:** Electron interferometry in a torsioned crystal lattice
- **Null result:** No extra phase → QMRT falsified
- **Positive result:** Extra π phase → QMRT supported

---

## 3. Prediction 2: Defect Interaction Potential

### 3.1 Standard Particle Interaction

Two particles at distance r interact via:

$$V_{\text{standard}}(r) = \frac{q_1 q_2}{4\pi\epsilon_0 r} \quad \text{(Coulomb)}$$

or for neutral particles, van der Waals / gravitational.

### 3.2 QMRT Prediction: Torsion-Mediated Interaction

Two torsion defects (τ₁, τ₂) interact via the connection field:

$$V_{\text{QMRT}}(r) = -\tau_1 \tau_2 \cdot v^2 \cdot \log(r/\xi)$$

where:
- v is the vacuum value of the order parameter
- ξ is the defect core size

**This is a logarithmic potential** — characteristic of 2D vortex interactions.

### 3.3 Observable Difference

| Property | Standard (Coulomb) | QMRT (Torsion) |
|----------|-------------------|----------------|
| Potential | ~1/r | ~log(r) |
| Force | ~1/r² | ~1/r |
| Long-range | Falls off | **Grows** (confined) |
| Opposite charges | Attract | Attract |
| Same charges | Repel | Repel |

**Key difference:** Logarithmic confinement vs power-law falloff.

### 3.4 Falsifiability

- **Test:** Measure interaction between topological defects in condensed matter systems
- **Signature:** log(r) potential instead of 1/r
- **Null result:** Standard 1/r → QMRT falsified in that regime

---

## 4. Prediction 3: Cosmological Correction

### 4.1 Standard Matter Scaling

In standard cosmology, matter density scales as:

$$\rho_{\text{standard}} = \frac{\rho_0}{a^3}$$

with no corrections (pressureless dust).

### 4.2 QMRT Prediction: Torsion Correction

If matter consists of torsion defects, there's a **small correction** from the torsion field energy:

$$\rho_{\text{QMRT}} = \frac{\rho_0}{a^3} + \epsilon(\tau)$$

where the correction term comes from:
- Defect core energy: E_core ~ v² per defect
- Connection field energy: E_field ~ v² log(R/ξ)

### 4.3 Explicit Correction

The torsion field energy density:

$$\epsilon_\omega = \frac{1}{2} \langle |d\omega|^2 \rangle \sim n_{\text{defect}} \cdot v^2 \cdot \log(a/\xi)$$

As the universe expands (a increases), this gives:

$$\rho_{\text{QMRT}} = \frac{\rho_0}{a^3} \left(1 + \frac{v^2}{\rho_0 a^3} \log(a/\xi) \right)$$

**Key:** The correction grows logarithmically with scale factor.

### 4.4 Observable Difference

| Quantity | Standard | QMRT |
|----------|----------|------|
| ρ(a) | ρ₀/a³ | ρ₀/a³ × (1 + ε log a) |
| w (equation of state) | 0 | 0 + O(ε) |
| Late-time behavior | Pure dust | **Slight deviation** |

**Prediction:** Small logarithmic correction to matter scaling at late times.

### 4.5 Falsifiability

- **Test:** Precision cosmology (CMB, BAO, SN)
- **Signature:** log(a) correction to matter density
- **Null result:** Pure 1/a³ → constrains QMRT parameters

---

## 5. Prediction 4: Fermion Mass from Torsion

### 5.1 Standard Fermion Mass

In the Standard Model, fermion mass comes from Yukawa coupling to Higgs:

$$m = y \cdot v_H$$

where y is Yukawa coupling, v_H is Higgs VEV.

### 5.2 QMRT Prediction: Torsion-Generated Mass

In QMRT, the effective action includes:

$$S = \int \bar{\psi}(i\gamma^\mu D_\mu)\psi \, d^4x$$

with D_μ = ∂_μ - i(τ/2)ω_μ.

Expanding around a torsion background:

$$S \supset \int \bar{\psi} \left( -\frac{\tau}{2} \langle\omega\rangle \right) \psi \, d^4x$$

This generates an **effective mass term**:

$$m_{\text{eff}} \sim \frac{\tau}{2} \cdot v$$

where v is the torsion VEV.

### 5.3 Observable Consequence

**If fermion masses originate from torsion:**
- Mass ratio depends on torsion coupling
- Flavor structure from torsion configuration
- Mass hierarchy from defect separation

### 5.4 Falsifiability

This is speculative but offers a **direction** for connecting to particle physics.

---

## 6. Summary: Distinguishing Predictions

### 6.1 Table of Predictions

| Prediction | Standard | QMRT | Test |
|------------|----------|------|------|
| **AB phase** | eΦ/ℏ | eΦ/ℏ - πW | Interferometry |
| **Interaction** | 1/r | log(r) | Defect dynamics |
| **Cosmology** | 1/a³ | 1/a³ × (1 + ε log a) | Precision cosmology |
| **Mass** | Yukawa | Torsion VEV | Flavor physics |

### 6.2 The Sharpest Prediction

**Modified Aharonov-Bohm phase** is the clearest:

| Aspect | Value |
|--------|-------|
| Effect | Extra π phase per torsion defect |
| Observable | Interference fringe shift |
| Test | Electron interferometer in torsioned medium |
| Falsifiable | Yes — no shift means QMRT wrong |

### 6.3 For the Paper

Include in Section 8 (Predictions):

> **"QMRT predicts a modified Aharonov-Bohm effect: spinors encircling a torsion defect acquire an additional phase of -πW, where W is the winding number. For W = 1, this corresponds to a π phase shift in addition to the standard electromagnetic contribution. This is in principle detectable via electron interferometry in materials with torsion defects (e.g., screw dislocations in crystals)."**

---

## 7. Why Torsion? (Addressing Reviewer Attack)

### 7.1 The Question

"Why should nature use torsion at all?"

### 7.2 Answer 1: Minimal Extension of GR

Einstein-Cartan theory is the **minimal extension** of General Relativity that includes spin:

- GR: metric g_μν (10 DOF)
- EC: metric + torsion T^λ_μν (24 additional DOF)

Torsion couples naturally to spin via:

$$T^{\lambda}_{\mu\nu} \sim \bar{\psi}\gamma^{[\lambda}\gamma_\mu\gamma_{\nu]}\psi$$

**QMRT claim:** This coupling, when combined with topological constraints, produces quantized holonomy.

### 7.3 Answer 2: Defect Physics

In condensed matter:
- Dislocations in crystals carry torsion
- Screw dislocations have measurable torsion

QMRT connects to this: **torsion defects in the medium = particle worldlines**.

### 7.4 Answer 3: Mathematical Necessity

Given:
1. A medium with defects
2. Single-valued order parameter
3. Spinorial transport

Torsion **emerges** as the natural description:
- Defects → curvature/torsion in connection
- Single-valuedness → quantization
- Spinors → half-angle coupling

---

## 8. Explicit Lagrangian (Addressing Reviewer Attack)

### 8.1 The Full Action

$$S = S_{\text{torsion}} + S_{\text{spinor}} + S_{\text{coupling}}$$

### 8.2 Torsion Sector

$$S_{\text{torsion}} = \int \left( \frac{1}{2}|T|^2 + \frac{\lambda}{4}(|\omega|^2 - v^2)^2 \right) \star 1$$

**Degrees of freedom:** ω_μ (connection 1-form)

### 8.3 Spinor Sector

$$S_{\text{spinor}} = \int \bar{\psi}(i\gamma^\mu\partial_\mu - m)\psi \, \star 1$$

**Degrees of freedom:** ψ (Dirac spinor)

### 8.4 Coupling

$$S_{\text{coupling}} = -\int \bar{\psi} \left( \frac{\tau}{2}\gamma^\mu\omega_\mu \right) \psi \, \star 1$$

**Coupling constant:** α = -τ/2 (derived, not free parameter)

### 8.5 Equations of Motion

**Torsion field:**
$$d\star d\omega + \lambda\omega(|\omega|^2 - v^2) = \frac{\tau}{2}\bar{\psi}\gamma\psi$$

**Spinor:**
$$(i\gamma^\mu\partial_\mu - m - \frac{\tau}{2}\gamma^\mu\omega_\mu)\psi = 0$$

---

## 9. Conclusion

### 9.1 The Three Predictions

1. **Phase shift:** π extra phase per torsion defect
2. **Interaction:** Logarithmic (not Coulomb) potential
3. **Cosmology:** Small log(a) correction to matter scaling

### 9.2 The Falsifiability Statement

> **"QMRT is falsifiable: the predicted π phase shift in Aharonov-Bohm experiments around torsion defects, if absent, would rule out the framework. Similarly, precision measurements of matter scaling that show no logarithmic correction would constrain the torsion contribution."**

---

*Document created: December 2025*
*Status: Distinguishing Predictions — Paper Section*
