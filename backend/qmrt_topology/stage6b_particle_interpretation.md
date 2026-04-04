# Stage 6B: Particle Interpretation

## Torsion Charge, Conservation, and Annihilation

---

## Abstract

We formalize the identification:
$$\rho_\tau \leftrightarrow \text{particle density}$$

and derive the conservation law:
$$\partial_\mu J^\mu_\tau = 0$$

This gives the particle interpretation "teeth": torsion conservation = particle number conservation.

---

## 1. The Identification

### 1.1 Torsion as Particle Number

**Definition (Particle Density).** In a spatial region Σ:

$$N_\Sigma = \int_\Sigma \rho_\tau \, d^2x = \sum_{v \in \Sigma} \tau_v$$

where:
- ρ_τ = Σ τ_v δ(x - x_v) is the torsion density
- τ_v is the torsion charge at defect v
- N_Σ is the total "particle number" in Σ

### 1.2 Physical Meaning

| Torsion Concept | Particle Concept |
|-----------------|------------------|
| τ_v = +1 | Particle |
| τ_v = -1 | Antiparticle |
| τ_v = 0 | Vacuum |
| Σ τ_v | Net particle number |
| ρ_τ(x) | Local particle density |

### 1.3 Why This Works

The identification is consistent because:
1. **Quantization**: τ ∈ ℤ for Z₂ statistics (fermions)
2. **Conservation**: dJ ≈ 0 (no isolated endpoints)
3. **Annihilation**: τ = +1 and τ = -1 cancel
4. **Statistics**: τ = 1 → fermionic holonomy

---

## 2. The Torsion Current

### 2.1 Definition (2D)

In 2D, the torsion current is a vector field:

$$J^\mu_\tau = \sum_i \tau_i \int \delta^{(2)}(x - x_i(t)) \, \dot{x}^\mu_i(t) \, dt$$

where:
- x_i(t) is the trajectory of defect i
- $\dot{x}^\mu_i$ = (1, v_i) is the velocity

### 2.2 Components

$$J^0_\tau = \rho_\tau = \sum_i \tau_i \, \delta^{(2)}(x - x_i(t)) \quad \text{(density)}$$

$$J^k_\tau = \sum_i \tau_i \, v^k_i \, \delta^{(2)}(x - x_i(t)) \quad \text{(flux)}$$

### 2.3 Definition (3+1D)

In 3+1D, the torsion current is a 4-vector:

$$J^\mu_\tau = \sum_i \tau_i \int_{\gamma_i} \delta^{(4)}(x - x_i(s)) \, \dot{x}^\mu_i(s) \, ds$$

where γ_i is the worldline of particle i.

---

## 3. Conservation Law

### 3.1 Derivation from Geometry

From the Cartan structure:
$$T^a = de^a + \omega^a{}_b \wedge e^b = 2\pi J^a_\tau$$

Taking the exterior derivative:
$$dT^a = d(de^a) + d(\omega^a{}_b \wedge e^b)$$

Using d² = 0 and the Bianchi identity:
$$dT^a + \omega^a{}_b \wedge T^b = R^a{}_b \wedge e^b$$

In flat spacetime (R = 0) with small connection:
$$dT^a \approx 0$$

Therefore:
$$d(2\pi J^a_\tau) = 0$$

$$\boxed{\partial_\mu J^{a\mu}_\tau = 0}$$

### 3.2 Physical Interpretation

This is the **continuity equation**:

$$\frac{\partial \rho_\tau}{\partial t} + \nabla \cdot \vec{J}_\tau = 0$$

**Meaning:**
- The rate of change of torsion density equals the divergence of torsion flux
- Torsion (particle number) is locally conserved
- Particles cannot appear or disappear in isolation

### 3.3 Integral Form

Integrating over a region Σ:

$$\frac{dN_\Sigma}{dt} = -\oint_{\partial\Sigma} \vec{J}_\tau \cdot d\vec{A}$$

**Meaning:**
- Change in particle number = flux through boundary
- Particles entering/leaving through the boundary account for all changes

---

## 4. Annihilation

### 4.1 Setup

Consider two defects:
- Particle at x_+ with τ = +1
- Antiparticle at x_- with τ = -1

Total torsion density:
$$\rho_\tau = \delta^{(2)}(x - x_+) - \delta^{(2)}(x - x_-)$$

### 4.2 Before Annihilation

Total torsion charge:
$$N = \int \rho_\tau \, d^2x = (+1) + (-1) = 0$$

The total is already zero, but there are two distinct defects.

### 4.3 Collision

As x_+ → x_-:
$$\rho_\tau \to \delta^{(2)}(x - x_0) - \delta^{(2)}(x - x_0) = 0$$

where x_0 is the collision point.

**Result:** The torsion density vanishes. Both defects disappear.

### 4.4 Energy Release

The connection field energy before annihilation:
$$E \sim \int |\omega|^2 \, d^2x \sim \int \frac{1}{|x - x_+|^2} + \frac{1}{|x - x_-|^2} - \frac{2}{|x - x_+||x - x_-|} \, d^2x$$

After annihilation:
$$E' = 0$$

**The field energy is released.** This is the analog of mass-energy release in particle-antiparticle annihilation.

---

## 5. Creation

### 5.1 Pair Creation

The reverse process: from vacuum, create:
- Particle (τ = +1) at x_+
- Antiparticle (τ = -1) at x_-

**Energy required:** Must supply the field energy to create the defect configuration.

### 5.2 Conservation Check

Before: N = 0
After: N = (+1) + (-1) = 0

**Total torsion charge is conserved.** ✓

### 5.3 Modified Conservation Law

At interaction vertices:
$$\partial_\mu J^{\mu}_\tau = \sigma$$

where σ is a source/sink (nonzero only at vertices).

**Constraint:** Total σ over an interaction = 0 (pairs created/destroyed).

---

## 6. Cosmological Scaling

### 6.1 Expanding Universe

In an expanding 2D universe with scale factor a(t):
- Physical distances: r_phys = a(t) · r_comoving
- Physical area: A_phys = a²(t) · A_comoving

### 6.2 Comoving Defects

If defects are comoving (fixed in comoving coordinates):
$$\rho_\tau^{(\text{phys})} = \frac{N}{A_{\text{phys}}} = \frac{N}{a^2 \cdot A_{\text{comov}}}$$

Therefore:
$$\boxed{\rho_\tau \sim \frac{1}{a^2} \quad \text{(2D)}}$$

### 6.3 3D Scaling

In 3D:
$$\boxed{\rho_\tau \sim \frac{1}{a^3} \quad \text{(3D)}}$$

### 6.4 Comparison

| Component | Scaling | Behavior |
|-----------|---------|----------|
| Radiation | 1/a⁴ | Dilution + redshift |
| **QMRT Torsion** | **1/a³** | **Matter-like** |
| Matter | 1/a³ | Dilution only |
| Dark Energy | 1/a⁰ | Constant |

**Result:** Torsion density scales like matter density!

### 6.5 Implications

If torsion defects behave like matter:
- They contribute to structure formation
- They cluster gravitationally
- They dilute with expansion (not constant like dark energy)

**This is a testable prediction** (in principle).

---

## 7. Summary

### 7.1 Key Results

| Result | Equation |
|--------|----------|
| Particle density | ρ_τ = Σ τ_v δ(x - x_v) |
| Torsion current | J^μ_τ = Σ τ_i ∫ δ(x - x_i) ẋ^μ ds |
| **Conservation** | **∂_μ J^μ_τ = 0** |
| Annihilation | τ = +1 and τ = -1 → 0 |
| Cosmological scaling | ρ_τ ~ 1/a³ (matter-like) |

### 7.2 Physical Picture

| QMRT Concept | Standard Particle Physics |
|--------------|--------------------------|
| Torsion defect | Particle |
| τ = +1 | Particle |
| τ = -1 | Antiparticle |
| τ = 0 | Vacuum |
| ∂_μJ^μ = 0 | Particle number conservation |
| τ_+ + τ_- → 0 | Pair annihilation |
| ρ ~ 1/a³ | Matter-like behavior |

### 7.3 What This Achieves

**Before:**
> "ρ_τ ↔ particle density" (handwaving)

**After:**
> "Torsion current satisfies ∂_μJ^μ = 0, giving particle number conservation. Pair annihilation is torsion cancellation. Cosmological scaling is 1/a³ (matter-like)."

**This is where QMRT starts making testable claims.**

---

## Appendix: Verification

### A.1 Conservation Check (2D)

For a static defect at origin:
$$J^0 = \tau \, \delta^{(2)}(x)$$
$$J^i = 0$$

Conservation:
$$\partial_0 J^0 + \partial_i J^i = 0 + 0 = 0 \quad \checkmark$$

### A.2 Conservation Check (Moving Defect)

For a defect moving with velocity v:
$$J^0 = \tau \, \delta(x - vt) \, \delta(y)$$
$$J^1 = \tau \, v \, \delta(x - vt) \, \delta(y)$$

Conservation:
$$\partial_0 J^0 = \tau \, (-v) \, \delta'(x - vt) \, \delta(y)$$
$$\partial_1 J^1 = \tau \, v \, \delta'(x - vt) \, \delta(y)$$

$$\partial_0 J^0 + \partial_1 J^1 = 0 \quad \checkmark$$

---

*Document created: December 2025*
*Status: Stage 6B — Particle Interpretation*
