# Phase 4C: Multi-Spot Interaction Analysis

## Date: April 2026

## Executive Summary

**Multiple biased regions show NO interaction. They are independent organization wells.**

| Test | Result |
|------|--------|
| Identical spots at varying separation | S1 = S2 regardless of distance |
| Asymmetric spots (β1 > β2) | Each S determined by local β |
| Energy localized in one spot | Energy equilibrates; S stays local |
| Correlation between spots | High, but from global field, not interaction |

---

## 1. Experiments

### 1.1 Identical Spots at Varying Separation

**Setup**: Two spots with identical β=0.8, at separations 20-60 grid units.

| Separation | S (spot 1) | S (spot 2) | S_between | Correlation |
|------------|------------|------------|-----------|-------------|
| 20 | 0.0264 | 0.0264 | 0.0109 | 0.87 |
| 30 | 0.0265 | 0.0264 | 0.0080 | 0.85 |
| 40 | 0.0264 | 0.0264 | 0.0065 | 0.80 |
| 60 | 0.0264 | 0.0264 | 0.0050 | 0.88 |

**Result**: S1 = S2 at ALL separations. Organization does not depend on neighbor distance.

### 1.2 Energy Initially in One Spot Only

**Setup**: Energy injected only into spot1. Spot2 starts empty.

| Time | S1 | S2 | E1 | E2 |
|------|-----|-----|-----|-----|
| 0 | 0.0007 | 0.0000 | 0.078 | 0.000 |
| 200 | 0.0259 | 0.0257 | 0.0068 | 0.0067 |
| Late | 0.0264 | 0.0264 | 0.0068 | 0.0068 |

**Result**: 
- Energy equilibrates (E1 ≈ E2) via wave propagation
- Organization becomes identical (S1 = S2) because both have identical β

### 1.3 Asymmetric Spots

**Setup**: Spot1 has β=0.9, Spot2 has varying β (0.3-0.7).

| β2 | β ratio | S1 | S2 | S ratio |
|----|---------|-----|-----|---------|
| 0.3 | 3.00 | 0.037 | ~0 | ∞ |
| 0.4 | 2.25 | 0.037 | 0.006 | 5.9 |
| 0.5 | 1.80 | 0.037 | 0.012 | 3.0 |
| 0.6 | 1.50 | 0.037 | 0.019 | 2.0 |
| 0.7 | 1.29 | 0.037 | 0.025 | 1.5 |

**Result**: 
- S1 is constant (~0.037) regardless of β2
- S2 depends only on β2, not on β1
- **No redistribution** between spots

---

## 2. Interpretation

### What the High Correlation Means

The 0.85 correlation between spots is **NOT** evidence of interaction.

It arises because both spots:
- Share the same global energy field
- Respond to the same wave fluctuations
- Have identical τ dynamics (same β threshold)

### Why There's No Interaction

The organization metric S measures local gradients in c_eff:
$$S = \sigma(c_{eff}) / \mu(c_{eff})$$

c_eff depends on τ, which evolves according to:
$$\dot{\tau} = -\lambda(\tau - \tau_{eq}(\rho)) + D\nabla^2\tau$$

The key term is τ_eq(ρ), which depends on LOCAL β:
$$\tau_{eq} = \tau_0 / (1 + \beta_{local} \cdot \rho)$$

Since β is a fixed spatial field, each region's τ_eq (and thus S) is determined by its own β, regardless of neighbors.

---

## 3. What This Means

### These are Organization Wells, Not Particles

| Property | Particles | Organization Wells |
|----------|-----------|-------------------|
| Interaction | Yes | **No** |
| Momentum exchange | Yes | **No** |
| Conservation laws | Yes | **No** |
| Motion | Possible | **Fixed** |
| Determined by | Internal state | **Local parameters** |

### Correct Terminology

- ✗ "Matter-like structures"
- ✗ "Particles"  
- ✗ "Interacting regions"
- ✓ **"Parameter-induced organization wells"**
- ✓ **"Localized organization zones"**

---

## 4. Conclusions for Paper 3

**Add to the paper:**

> "Testing multiple biased regions reveals no interaction between them. Each region's organization is determined entirely by its local coupling strength β, independent of neighboring regions. Energy equilibrates globally via wave propagation, but organization remains locally determined. This establishes that the localized structures are parameter-induced organization wells, not interacting particles. The model produces persistent localized organization, but lacks the interaction and conservation properties needed for particle-like behavior."

---

## 5. What Would Be Needed for Interaction

To achieve interacting structures, the model would need:

1. **Nonlinear coupling between τ and ρ** (feedback loops)
2. **Long-range correlations in τ** beyond simple diffusion
3. **Topological defects** that carry conserved quantities
4. **Modified dynamics** where organization affects β itself

This points toward the next extension: vortices/topological defects.

---

## 6. Files

- `multispot_interaction.json` — Separation scan data
- `redistribution_analysis.json` — Asymmetric spots data
