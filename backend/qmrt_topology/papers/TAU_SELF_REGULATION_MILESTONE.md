# τ Self-Regulation Milestone

**Date**: December 2025  
**Status**: FROZEN

---

## Core Statement

> **Dynamic τ introduces a self-limiting feedback: increasing excitation raises τ, which increases effective propagation speed and enhances dispersion, preventing runaway post-cutoff growth.**

---

## Mechanism

### The τ Feedback Loop

```
High local energy density
        ↓
    τ increases
        ↓
   c_eff = c₀ τ/τ₀ increases
        ↓
  Faster wave propagation
        ↓
  Enhanced energy dispersion
        ↓
  Prevents local accumulation
```

### Mathematical Form

```
τ_target = 1.0 + α (E_local - ⟨E⟩)
∂τ/∂t = β (τ_target - τ)

c_eff² = c₀² τ/τ₀
```

Where:
- α = τ response rate to energy (~0.005)
- β = τ relaxation rate (~0.01)
- E_local = ψ² + ½ψ̇² (local energy density)

---

## Experimental Evidence

### Test: Post-Cutoff Behavior Comparison

| Model | Post-Cutoff (2000 steps) | Behavior |
|-------|-------------------------|----------|
| Full mechanism (dynamic τ) | Population → 106 | Self-limiting decay |
| Reduced model (constant c) | Population → 1114 | Sustained growth |

### Interpretation

In the reduced model (constant wave speed):
- Accumulated field momentum continues driving dynamics
- No feedback mechanism to disperse excess energy
- Population grows and sustains post-cutoff

In the full mechanism (dynamic τ):
- High-energy regions have faster wave propagation
- Energy disperses rather than accumulating
- System returns toward equilibrium after driving stops

---

## Why This Matters

### 1. Distinguishes Reduced-Model Artifacts

The "endogenous regeneration" observed in the reduced model was NOT a QMRT feature—it was an artifact of missing self-regulation. The full mechanism correctly produces decay post-cutoff.

### 2. Establishes a Physical Limit

τ self-regulation creates a **carrying capacity** for energy density. The medium cannot sustain arbitrarily high excitation because dispersion increases with excitation.

### 3. Stabilizes Driven Scaffolds

During sustained driving, τ self-regulation moderates the response to injection. This may contribute to the observed sweet-spot effect where moderate driving outperforms both weak and strong driving.

---

## Connection to Driven-State Behavior

Importantly, τ self-regulation does **not** significantly affect driven-state behavior:

| Interval | Full Dim | Reduced Dim | Difference |
|----------|----------|-------------|------------|
| 50 | 1.46 | 1.49 | -0.03 |
| 100 | 1.72 | 1.72 | 0.00 |
| 200 | 1.69 | 1.74 | -0.05 |
| 500 | 1.57 | 1.60 | -0.03 |

During continuous driving, the external injection dominates and both models produce similar organizational structure. The τ feedback primarily affects **post-driving** dynamics.

---

## Implications for Theory

### The Medium is Self-Regulating

QMRT is not a passive substrate that can be driven to arbitrary states. The τ dynamics impose intrinsic limits on energy accumulation and structural persistence.

### Organizational Structure is Driven, Not Self-Sustaining

Without external driving:
- The scaffold decays (full mechanism)
- Memory effects (channel, remnant) preserve information but not population
- True "self-organization" requires sustained input

### The Reduced Model Has Limited Validity

For driven-state properties, the reduced model is adequate. For post-driving dynamics, the full mechanism is required.

---

## Files

- `/app/backend/full_mechanism_simulator.py` — Implementation with dynamic τ
- `/app/backend/qmrt_topology/papers/IMPLEMENTATION_FIDELITY_AUDIT.md` — Audit details

---

**Status**: FROZEN  
**Date**: December 2025
