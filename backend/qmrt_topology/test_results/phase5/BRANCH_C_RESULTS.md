# Branch C: Coupled Complex Scalar QMRT - Results

## Date: April 2026

## Executive Summary

**Branch C reveals an INTRINSIC coupling between β and vortex lifetime.**

Even without explicit coupling terms, high-β regions increase vortex lifetime by **7.5×**. Adding explicit coupling improves this to **11.4×** (53% additional improvement).

---

## 1. Test Results

### Single Vortex Lifetime

| Mode | Region | β | Lifetime | Time (units) |
|------|--------|---|----------|--------------|
| none | center | 0.8 | 1500 steps | 60 |
| none | corner | 0.2 | 200 steps | 8 |
| both | center | 0.8 | 2300 steps | 92 |
| both | corner | 0.2 | 200 steps | 8 |

### Lifetime Ratios

| Coupling | High-β / Low-β |
|----------|----------------|
| None | **7.5×** |
| Both | **11.4×** |

---

## 2. Key Finding: Intrinsic β-Vortex Coupling

**Even without explicit coupling, β affects vortex lifetime.**

Why? The τ-equilibrium equation:
$$\tau_{eq} = \frac{\tau_0}{1 + \beta \cdot \rho}$$

Higher β means:
- Stronger τ response to energy density
- More c_eff variation
- Different wave dynamics around vortex core

This is an **indirect** coupling that was already present in Branches A and B!

---

## 3. Explicit Coupling Effects

Adding explicit β-topology coupling (damping + energy):
- High-β lifetime: 1500 → 2300 steps (**53% improvement**)
- Low-β lifetime: unchanged (200 steps)
- Ratio: 7.5× → 11.4×

The explicit coupling enhances the intrinsic effect but does not create it.

---

## 4. Implications

### For the Theory

| Finding | Implication |
|---------|-------------|
| β already affects vortex lifetime | Branches A and B were not fully separated |
| Explicit coupling enhances this | The coupling channel exists |
| Enhancement is significant (53%) | Worth further investigation |

### The Gap Is Smaller Than Thought

Branch B showed "β doesn't pin vortices" because:
1. Vortices died before pinning could be measured (lifetime ~8-60 time units)
2. The survival test was too long (4000 steps = 160 time units)

But β DOES affect vortex dynamics through τ_eq.

---

## 5. Updated Theoretical Picture

| Axis | Mechanism | Status |
|------|-----------|--------|
| Energy flow | Driving/dissipation | Established (Paper 2) |
| Organization (S) | β coupling via τ_eq | Established (Paper 3) |
| Vortex lifetime | **β coupling via τ_eq** | **NEW: Intrinsic** |
| Vortex interaction | Phase winding | Established (Branch B) |

The axes are **not fully independent**. β affects both organization AND vortex lifetime through the same τ_eq mechanism.

---

## 6. What This Means for "Matter-Like" Behavior

### Positive
- Vortices live 7-11× longer in high-β regions
- High-β can be thought of as "matter-favorable" regions
- Topology + localization have intrinsic connection

### Still Missing
- Vortices still decay (no topological conservation)
- Pinning test failed (vortices die before establishing equilibrium)
- Interaction remains independent of β

### Path Forward
To achieve true "matter-like" behavior:
1. ✓ Vortices interact (Branch B)
2. ✓ β enhances vortex lifetime (Branch C)
3. ✗ Need: Conservation law or continuous vortex creation
4. ✗ Need: Longer vortex persistence for pinning equilibrium

---

## 7. Conclusion

**Branch C reveals that β and vortex dynamics are intrinsically coupled through τ_eq.**

This closes the gap between Branches A (organization) and B (topology). The coupling exists—it just wasn't strong enough to appear in the pinning test due to vortex decay.

### Updated Boundary Statement

> "Localization (via β-asymmetry) and vortex dynamics are coupled through the τ-equilibrium mechanism. High-β regions increase vortex lifetime by 7-11×. However, in dissipative systems, vortices still decay before pinning equilibrium can be established."

---

## 8. Files

- `coupled_complex_scalar_qmrt.py` — Branch C simulator
- Test results above (not saved to file)
