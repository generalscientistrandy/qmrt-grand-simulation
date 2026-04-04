# QMRT: Final Equations Summary

## Core Equations for Publication

---

## 1. Fundamental Definitions

### Discrete Torsion
$$\tau_v := \frac{1}{2\pi}\left(\sum_i \theta_i - 2\pi\right)$$

### Torsion Density
$$\rho_\tau(x) = \sum_v \tau_v \, \delta^{(2)}(x - x_v)$$

### Connection from Sources
$$\omega_\mu(x) = \sum_v \tau_v \, G_\mu(x - x_v)$$

where G_μ is the 2D vortex Green's function.

---

## 2. Key Relations

### Source Equation
$$d\omega = 2\pi \rho_\tau \cdot \text{vol}_2$$

### Holonomy Quantization
$$\oint_\gamma \omega = 2\pi n, \quad n \in \mathbb{Z}$$

### Transport Coupling (Derived)
$$\alpha = -\frac{\tau}{2}$$

### Spinor Phase
$$\psi \to e^{i\alpha \oint \omega} \psi = e^{-i\pi\tau W} \psi$$

### Holonomy
$$H = e^{-i\pi\tau W} = (-1)^{\tau W}$$

---

## 3. Effective Action

$$S[\psi, \bar{\psi}, \omega] = S_{\text{torsion}} + S_{\text{spinor}}$$

### Torsion Sector
$$S_{\text{torsion}} = \int \left( \frac{1}{2}|d\omega|^2 + \frac{\lambda}{4}(|\omega|^2 - v^2)^2 \right) d^2x$$

### Spinor Sector
$$S_{\text{spinor}} = \int \bar{\psi}\left(i\gamma^\mu\partial_\mu - \frac{\tau}{2}\gamma^\mu\omega_\mu - m\right)\psi \, d^2x$$

---

## 4. 3+1D Extension

### Torsion Current
$$J^a_\tau = \sum_i \tau_i \int_{\gamma_i} \delta^{(4)}(x - x_i(s)) \, \dot{x}^a_i \, ds$$

### Cartan Structure
$$T^a = de^a + \omega^a{}_b \wedge e^b = 2\pi J^a_\tau$$

### Conservation
$$\partial_\mu J^{a\mu}_\tau = 0$$

### Spinor Holonomy
$$\text{Hol}(\gamma) = \mathcal{P} \exp\left(\frac{i}{4} \oint_\gamma \omega^{ab} \gamma_{ab}\right)$$

---

## 5. Predictions

### Modified Aharonov-Bohm Phase
$$\boxed{\Delta\phi_{\text{QMRT}} = -\pi\tau W}$$

### Total Phase
$$\phi_{\text{total}} = \frac{e\Phi}{\hbar} - \pi\tau W$$

### Interaction Potential
$$V(r) = -\tau_1\tau_2 v^2 \log(r/\xi)$$

### Cosmological Scaling
$$\rho = \frac{\rho_0}{a^3}\left(1 + \epsilon\log\frac{a}{\xi}\right)$$

---

## 6. Derivation Chain (Summary)

```
Single-valuedness: Φ = ρe^{iχ}
         ↓
Quantization: ∮ω = 2πn
         ↓
Z₂ constraint: α ∈ (1/2)ℤ
         ↓
Coupling: α = -τ/2
         ↓
Statistics: H = (-1)^W
```

---

## 7. Magnitude Estimate

| Quantity | Value |
|----------|-------|
| Defect density | 10⁶ - 10¹² cm⁻² |
| Enclosed defects (typical) | ~1 |
| **Phase shift per defect** | **~π rad** |
| **Fringe shift** | **1/2 period** |

---

## 8. Theory Connections

| QMRT | Standard Physics |
|------|------------------|
| T^a | Einstein-Cartan torsion |
| Defect worldlines | Screw dislocations |
| ∮ω = 2πn | Flux quantization |
| Δφ = -πτW | Berry/AB phase analog |

---

## 9. The Main Result

### Theorem (QMRT Torsion-Holonomy)

**If:**
1. Torsion configurations preserve single-valued transport
2. Transport obeys spinorial double-cover

**Then:**
1. ∮ω = 2πn (quantized)
2. α = -τ/2 (uniquely fixed)
3. H = (-1)^{τW} (Z₂ for τ ∈ ℤ)

### Corollary (Observable)

$$\Delta\phi = -\pi\tau W$$

For τ = 1, W = 1: **Δφ = -π** (half-period fringe shift)

---

## 10. Falsifiability

> **"Absence of the predicted π phase shift per torsion defect in controlled electron interferometry would falsify QMRT."**

---

*Status: Final Equations — Ready for arXiv*
