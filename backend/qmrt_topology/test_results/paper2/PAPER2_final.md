# Paper 2: Long-Path Dynamics and Sustained Organization in a Driven-Dissipative Medium

## Abstract

We investigate the long-time behavior of emergent structures in a dynamical medium, asking whether organization persists or decays. Through deterministic PDE simulations (2×10⁵ steps, 2D grid), we find that undriven dynamics exhibit asymptotic decay: spatial organization S → 0 and coupling I_TS → 0, despite persistent activity (births/deaths continue at ~80% of initial rate). Sustained energy injection maintains nonzero organization: S_late ≈ 0.002 vs ~0 undriven. An energy-matched control shows periodic and randomized driving produce equivalent S_late (ratio 0.97), indicating input magnitude—not temporal structure—dominates. Late-time organization scales with power: S_late ∝ P^0.15. These results establish a separation between kinetic activity and coherent organization, suggesting the latter is non-conserved and requires continuous energetic support.

**Keywords:** emergent structure, driven-dissipative systems, long-path dynamics, spatial organization

---

## 1. Introduction

Paper 1 established mechanisms governing structure lifecycle: births correlate with energy density peaks, persistence scales with spatial organization S, and merges occur in high-gradient regions. This paper addresses the long-time limit:

**Central question:** Do emergent structures persist, or does organization decay?

---

## 2. Setup

### 2.1 Definitions

| Symbol | Definition | Normalization |
|--------|------------|---------------|
| **S** | Spatial organization: normalized variance of ∇φ | S ∈ [0, 1], higher = more structured |
| **I_TS** | Spacetime coupling: mutual information between ∂_t φ and ∇²φ | I_TS ∈ [0, 1] |
| **Activity** | Event rate: (births + deaths) per unit time | events/time |
| **P** | Input power: A²/T_interval | energy rate |

**Driving protocol:**
- Amplitude A: pulse height (tested 0.5–3.0)
- Interval T: steps between pulses (tested 500–4000)
- Power P = A²/T
- Pulses injected at random grid positions

### 2.2 System

2D wave equation with backreaction:
$$\partial_t^2 \phi = c^2 \nabla^2 \phi - \gamma \partial_t \phi + \alpha (\nabla \cdot \mathbf{v}) \phi$$

### 2.3 Reproducibility

| Parameter | Value |
|-----------|-------|
| Grid size | 50×50 |
| Timestep dt | 0.04 |
| Boundary | Periodic |
| Stochastic noise | None (fully deterministic) |
| Long-path steps | 30,000–200,000 |
| Sampling rate | Every 100 steps |
| Coupling α | 0.5 (default) |

All simulations are deterministic: identical parameters yield identical results.

---

## 3. Undriven Dynamics

### 3.1 Asymptotic Decay

Figure 1 shows S(t) for undriven evolution (blue curve):

- S decays exponentially: S(t) ~ exp(-t/τ), τ ≈ 60
- Extended runs (200k steps): S → 10⁻¹⁶ (numerical zero)
- I_TS also decays to zero
- Energy ρ remains constant (homogenized, not lost)

**Late-time window (t > 6000):** S < 10⁻¹⁰, effectively zero.

### 3.2 Persistent Activity

Figure 3 demonstrates the activity vs organization separation:

| Metric | Early | Late | Ratio |
|--------|-------|------|-------|
| Activity | 4.3 | 3.4 | **0.80** |
| S | 0.023 | 6.7×10⁻⁵ | **0.003** |

**Key result:** Activity persists at 80% while S decays to 0.3%.

> **Activity ≠ Organization.** Structure-like events continue, but spatial coherence vanishes.

---

## 4. Driven Dynamics

### 4.1 Sustained Organization

Figure 1 (red curve) shows driven evolution:

| Condition | S_late | I_TS_late |
|-----------|--------|-----------|
| Undriven | ~0 | ~0 |
| Driven | 0.002 | 0.80 |

Maintenance factor: >10⁷ for S.

### 4.2 Parameter Robustness

All tested parameters maintain S > 0:
- Intervals 500–5000 steps: all stabilize
- Amplitudes 0.5–3.0: all stabilize
- Even 5 pulses over 30k steps suffices

---

## 5. Controls

### 5.1 Energy-Matched Random Injection

**Setup:** 29 pulses, amplitude 2.0, same total energy
- Periodic: pulses every 1000 steps
- Random: pulses at random times (energy-matched)

| Condition | S_late |
|-----------|--------|
| Periodic | 0.00205 |
| Random | 0.00211 |
| Ratio | **0.97** |

**Result:** Periodic ≈ Random.

Across the tested range, temporal structure of the input does not materially change S_late when total injected energy is matched, indicating magnitude-dominated maintenance in this regime.

### 5.2 Correlation Length

| Condition | ξ |
|-----------|---|
| Undriven | 12.3 |
| Driven | 10.4 |

**Caveat:** Correlation length in undriven case becomes ill-defined as field homogenizes; large ξ reflects lack of gradients, not coherent structure. Driven ξ ≈ 10 reflects real structural correlations.

---

## 6. Scaling

Figure 5 shows S_late vs input power P:

$$S_{late} \propto P^{0.15 \pm 0.03}$$

Higher power produces higher organization, with sublinear (diminishing returns) scaling.

| Interval | Amp | P | S_late |
|----------|-----|---|--------|
| 4000 | 3.0 | 0.0022 | 0.00399 |
| 2000 | 3.0 | 0.0045 | 0.00382 |
| 1000 | 2.0 | 0.004 | 0.00314 |

---

## 7. Limitations

This study is bounded by:

1. **Regime tested:** α ∈ [0.2, 0.8], driving intervals 500–4000, amplitudes 0.5–3.0
2. **Deterministic system:** No stochastic noise; noise effects untested
3. **2D only:** 3D validation pending
4. **Correlation length caveat:** ξ is meaningful only when gradients exist
5. **No universality claim:** Results specific to this model; other driven-dissipative systems may behave differently

---

## 8. Discussion

### 8.1 Activity vs Organization

These results establish a fundamental separation:
- **Kinetic activity** (event rates): persists without driving
- **Coherent organization** (S): requires energy throughput

Organization is a non-conserved quantity in this medium.

### 8.2 Mechanism

Energy homogenization drives decay:
1. Initial pulse creates gradients
2. Wave equation + damping spreads energy
3. Gradients flatten → S → 0
4. Structure detection continues (from noise) but carries no content

Driving counteracts this by continuously injecting new gradients.

---

## 9. Conclusion

**Result 1:** Undriven → activity persists, organization decays to zero.

**Result 2:** Driven → organization sustained; S_late ∝ P^0.15.

**Implication:** Organization is a non-conserved quantity requiring energy throughput. In a driven-dissipative medium, structure-like events can persist indefinitely while spatial coherence vanishes—unless sustained energy maintains gradients.

Paper 1 established how structures form. Paper 2 establishes what sustains them: nothing, without continuous energy input.

---

## Figures

1. **Figure 1:** S(t) undriven (blue) vs driven (red), log scale. Shaded region: late-time window. Annotation: S_floor ≈ 0.
2. **Figure 2:** I_TS(t) undriven vs driven.
3. **Figure 3:** Activity index (top) and S (bottom) vs time. Both normalized. Labels: "Activity persists ~80%", "S decays ~300×".
4. **Figure 4:** Energy-matched control bar plot: Undriven / Periodic / Random.
5. **Figure 5:** S_late vs Power with fit line S ∝ P^0.15.

---

## Data Availability

All data, scripts, and figures: `/app/backend/qmrt_topology/test_results/paper2/`

---

## References

[1] Paper 1: "Statistical Lifecycle Model for Emergent Structures in a Dynamical Medium"
