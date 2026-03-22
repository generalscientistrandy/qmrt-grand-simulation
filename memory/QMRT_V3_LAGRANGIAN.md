# QMRT v3: Tri-Branch Lagrangian Skeleton

**Date**: December 2025  
**Status**: Candidate theory ready for implementation  
**Purpose**: Physics-principled field theory with geometric branch structure

---

## Field Content

| Field | Type | Physical Mode | Role |
|-------|------|---------------|------|
| **ρ(x,t)** | Scalar | Compression / Density | Mass accumulation, background stability |
| **τᵢ(x,t)** | Vector (3-component) | Torsion / Rotational strain | Localized energy, confinement |
| **φ(x,t)** | Scalar | Radiation / Phase | Causal propagation, decay pathways |

---

## Total Lagrangian

$$\mathcal{L} = \mathcal{L}_\rho + \mathcal{L}_\tau + \mathcal{L}_\phi + \mathcal{L}_{\text{int}}$$

---

## 1. Compression Branch (ρ)

$$\mathcal{L}_\rho = \frac{1}{2}(\partial_t \rho)^2 - \frac{c_\rho^2}{2}(\nabla\rho)^2 - \frac{1}{2}m_\rho^2 \rho^2 - \lambda_\rho \rho^4$$

**Physical meaning**:
- Finite mass term → density mode is not long-range massless
- Quartic self-interaction → enables localized density wells
- Provides gravitational-like ordering background

**Parameters**:
- `c_ρ` = compression wave speed
- `m_ρ` = compression mass (gap)
- `λ_ρ` = self-interaction strength (must be > 0)

---

## 2. Torsion Branch (τ)

$$\mathcal{L}_\tau = \frac{1}{2}(\partial_t \tau_i)^2 - \frac{c_\tau^2}{2}(\nabla\tau_i)^2 - \frac{1}{2}m_\tau^2 \tau_i\tau_i - \lambda_\tau (\tau_i\tau_i)^2$$

**Physical meaning**:
- Vector field supports vortex-like localized energy
- Confinement candidate
- Nonlinear self-locking resonance possible

**Parameters**:
- `c_τ` = torsion wave speed
- `m_τ` = torsion mass (gap)
- `λ_τ` = self-interaction strength (must be > 0)

**Note**: Sum over repeated index i (Einstein convention)

---

## 3. Radiation Branch (φ)

$$\mathcal{L}_\phi = \frac{1}{2}(\partial_t \phi)^2 - \frac{c_\phi^2}{2}(\nabla\phi)^2$$

**Physical meaning**:
- **No mass term** (or extremely small) → defines causal propagation
- Emergent relativistic cone
- Energy transport channel

**Parameters**:
- `c_φ` = radiation speed (emergent "speed of light")

**Critical**: This is the ONLY massless branch → defines causality

---

## 4. Coupling Hierarchy

### Compression ↔ Torsion (NONLINEAR)

$$\mathcal{L}_{\rho\tau} = -g_{rt} \rho (\tau_i \tau_i)$$

**Physical meaning**:
- Density gradients generate torsion wells
- Torsion modifies particle size scale
- **Confinement-shell generator**

### Torsion ↔ Radiation (THRESHOLD / DERIVATIVE)

$$\mathcal{L}_{\tau\phi} = -g_{tp} (\tau_i \tau_i)(\partial_\mu \phi \partial^\mu \phi)$$

**Physical meaning**:
- Low torsion amplitude → no radiation emission
- High torsion energy → radiative decay channel opens
- Creates **stable low-energy particles** and **unstable high-energy excitations**

### Compression ↔ Radiation (WEAK LINEAR)

$$\mathcal{L}_{\rho\phi} = -g_{rp} \rho \phi$$

**Physical meaning**:
- Long-range weak interaction
- Redshift / energy damping
- Large-scale coherence modulation
- **Emergent gravity sector candidate**

---

## Constraints and Symmetries

### 1. Rotational Symmetry
System depends only on invariants:
- $\tau_i \tau_i$ (not individual components)
- $\nabla\rho \cdot \nabla\rho$
- $\nabla\phi \cdot \nabla\phi$

### 2. Energy Boundedness
**Required for stability**:
$$\lambda_\rho > 0, \quad \lambda_\tau > 0$$

Otherwise simulation will blow up.

### 3. Speed Hierarchy (Causal Layering)
$$c_\phi \geq c_\tau \geq c_\rho$$

**Meaning**:
- Fastest propagation → radiation (defines light cone)
- Medium response → torsion (particle dynamics)
- Slow background ordering → density (structure formation)

---

## Equations of Motion

Derived from Euler-Lagrange: $\partial_\mu \frac{\partial \mathcal{L}}{\partial(\partial_\mu \psi)} = \frac{\partial \mathcal{L}}{\partial \psi}$

### Compression (ρ):
$$\partial_t^2 \rho = c_\rho^2 \nabla^2 \rho - m_\rho^2 \rho - 4\lambda_\rho \rho^3 - g_{rt}(\tau_i\tau_i) - g_{rp}\phi$$

### Torsion (τᵢ):
$$\partial_t^2 \tau_i = c_\tau^2 \nabla^2 \tau_i - m_\tau^2 \tau_i - 4\lambda_\tau (\tau_j\tau_j)\tau_i - 2g_{rt}\rho\tau_i - 2g_{tp}\tau_i(\partial_\mu\phi\partial^\mu\phi)$$

### Radiation (φ):
$$\partial_t^2 \phi = c_\phi^2 \nabla^2 \phi - g_{rp}\rho + 2g_{tp}(\tau_i\tau_i)\nabla^2\phi - 2g_{tp}\partial_t[(\tau_i\tau_i)\partial_t\phi]$$

---

## Physical Interpretation

### What is a Particle?

> **A particle = coherent locked resonance between compression (ρ) and torsion (τ), below the radiation (φ) coupling threshold**

### Stability Mechanism

1. **Torsion self-locks** via $\lambda_\tau(\tau_i\tau_i)^2$
2. **Density forms stabilizing shell** via $g_{rt}\rho(\tau_i\tau_i)$
3. **Radiation coupling suppressed** when $\tau_i\tau_i$ is below threshold

### Decay Mechanism

When torsion amplitude crosses the threshold set by $g_{tp}$:
- Radiation channel opens
- Energy escapes via φ field
- Particle decays

---

## Connection to QMRT v2

| QMRT v2 Field | QMRT v3 Mapping | Notes |
|---------------|-----------------|-------|
| ω (frequency/ordering) | ρ (compression) | Both control structure/mass |
| φ (phase) | τ (torsion) | Both enable localization |
| — | φ (radiation) | NEW: massless propagation |

**Key upgrade**: v3 has proper massless radiation channel that v2 lacked.

---

## Parameter Ranges (TO BE DETERMINED)

Awaiting dimensionless scaling analysis to determine:
- Natural units
- Stable parameter windows
- Resonance locking conditions
- Threshold coupling values

---

## Implementation Notes

### Numerical Scheme
- Symplectic integrator (Yoshida 4th order) for energy conservation
- Spectral Laplacian for spatial derivatives
- Vector field τᵢ requires 3 additional field components

### Grid Requirements
- Minimum: 16³ for testing
- Production: 32³ - 64³ for convergence
- Must resolve torsion vortex cores

### Initial Conditions for Testing
1. Uniform background ρ = ρ₀
2. Localized torsion perturbation (Gaussian vortex)
3. Zero radiation field
4. Observe: does torsion remain localized? Does it radiate?
