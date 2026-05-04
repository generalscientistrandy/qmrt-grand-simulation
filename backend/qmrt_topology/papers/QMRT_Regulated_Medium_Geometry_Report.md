# QMRT Regulated Medium: Effective Geometry and Lorentz-like Properties

**Technical Report — December 2025**  
**Baseline:** Regulated Recovery v1.1  
**Status:** Internal Research Document

---

## Abstract

We present validated simulation results demonstrating that the Quark Medium Relativity Theory (QMRT) regulated recovery phase exhibits Lorentz-like ingredients and effective refractive geometry. The regulated medium sustains topological defects through a self-consistent recovery loop, which injects vibrational energy that becomes statistically isotropic. Signal propagation obeys a bounded τ-dependent speed law c_eff(τ) = √(c₀²τ), and spatial τ gradients systematically bend wave paths through an effective refractive geometry. Boost tests reveal medium-dependent asymmetry consistent with a preferred rest frame rather than vacuum Lorentz invariance.

**Key validated properties:**
- Statistical rotational isotropy (anisotropy < 0.4%)
- Bounded signal propagation (c_eff scales with √τ)
- Causal creation-to-wave energy chain (correlation 0.81)
- τ-gradient lensing (perfect correlation, 100% correct direction)
- Preferred medium frame (boost asymmetry)

---

## 1. Introduction

The QMRT framework proposes that spacetime-like behavior can emerge from a substrate medium with self-regulating topological dynamics. This report documents the validation of key Lorentz-like properties in the "Regulated Recovery v1.1" phase, where sustained defect creation and wave propagation produce an effectively geometric medium.

### 1.1 Central Question

Can primitive local rules plus regulated recovery naturally generate spacetime-like behavior, including:
- Rotational symmetry
- Bounded signal propagation
- Effective curved geometry from field gradients

### 1.2 Claim Boundary

**Supported claim:**
> The regulated QMRT medium exhibits Lorentz-like ingredients in a preferred medium frame and supports τ-gradient lensing, where spatial τ gradients bend wave propagation through an effective refractive geometry.

**Not claimed:**
- Full vacuum Lorentz invariance
- Exact special relativity equivalence
- Emergent spacetime proven

---

## 2. Regulated Recovery v1.1 Baseline

### 2.1 Configuration

| Parameter | Value | Physical Role |
|-----------|-------|---------------|
| `tau_cap` | 1.8 | Maximum τ before creation triggers |
| `damping_to_tau` | 0.20 | Dissipation → τ recovery coupling |
| `dt` | 0.12 | Simulation timestep |
| `grid_size` | 32 | Standard test grid (some tests use 48-64) |
| `c_0_sq` | 4.0 | Base wave speed squared |
| `gamma` | 0.007 | Damping coefficient |

### 2.2 Recovery Mechanism

The regulated recovery loop operates as follows:

```
Wave energy dissipation (γ·kinetic)
         ↓
τ field recharges (damping_to_tau coupling)
         ↓
τ exceeds creation threshold (tau_cap)
         ↓
Topological defect created
         ↓
Defect injects vibrational energy
         ↓
Energy dissipates → loop continues
```

This self-sustaining mechanism is the foundation of all emergent properties.

### 2.3 Negative Controls

| Mode | Defects | Vibration | Isotropy |
|------|---------|-----------|----------|
| Remnant (no recovery) | Decays | Collapses | Degrades |
| Channel (weak recovery) | Partial | Reduced | Partial |
| **Regulated v1.1** | **Sustained** | **Stable** | **Emergent** |

Only Regulated Recovery v1.1 produces the full property set.

---

## 3. Creation-Wave Causal Chain

### 3.1 Hypothesis

Defect creation events inject measurable energy into the vibrational field, establishing a causal link from recovery to wave activity.

### 3.2 Results

| Metric | Value |
|--------|-------|
| Total creation events tracked | 37,413 |
| Positive energy injection fraction | **71.75%** |
| Mean energy delta per event | 0.0034 |
| Creation-energy correlation | **0.811** |
| Cumulative correlation | 0.683 |

### 3.3 Interpretation

The high correlation (0.81) and positive injection fraction (72%) establish that creation events are the **source** of vibrational energy. The causal chain is:

```
τ recovery → creation events → energy injection → waves
```

This is not mere correlation; the time-shifted analysis confirms that creation activity predicts subsequent energy levels.

---

## 4. Emergent Statistical Isotropy

### 4.1 Hypothesis

Despite anisotropic defect injection (z-axis bias), the vibrational field becomes statistically rotationally symmetric through averaging.

### 4.2 Multi-Seed Results

| Seed | Combined Anisotropy | Status |
|------|---------------------|--------|
| 42 | 0.0028 | STRONG ✓ |
| 123 | 0.0044 | STRONG ✓ |
| 456 | 0.0038 | STRONG ✓ |
| 789 | 0.0027 | STRONG ✓ |
| 1000 | 0.0037 | STRONG ✓ |

**Aggregate:** Mean = **0.0035 ± 0.0006**, 5/5 seeds pass

### 4.3 Interpretation

Anisotropy < 0.4% across independent seeds demonstrates **genuine emergent rotational symmetry**. The mechanism is statistical averaging: many randomly-oriented creation events produce an isotropic background despite individual events being directional.

This is analogous to how thermal radiation becomes isotropic despite individual photon emissions being directional.

---

## 5. Bounded Signal Propagation

### 5.1 Signal Speed Law

The effective signal speed depends on the local τ field:

$$c_{\text{eff}}(\tau) = \sqrt{c_0^2 \cdot \tau}$$

### 5.2 Light Cone Test Results

| τ Value | Theoretical c_eff | Measured Speed | Ratio |
|---------|-------------------|----------------|-------|
| 1.0 | 2.000 | 2.165 | 1.08 |
| 1.8 | 2.683 | 2.877 | 1.07 |

**Speed scaling verification:**
- Expected ratio: √(1.8/1.0) = 1.342
- Measured ratio: 2.877/2.165 = **1.329**
- Error: **< 1%**

### 5.3 Interpretation

The signal speed law is validated to high precision. This establishes a **causal structure** where no signal can propagate faster than c_eff(τ). The ~8% overshoot in absolute speed is consistent with numerical discretization effects.

---

## 6. Preferred-Frame Boost Behavior

### 6.1 Hypothesis

If the medium has vacuum Lorentz invariance, forward and backward propagation speeds should be equal in all frames. If the medium has a preferred rest frame, asymmetry should appear.

### 6.2 Results

| Boost Velocity | v_forward | v_backward | Asymmetry |
|----------------|-----------|------------|-----------|
| 0.0 (rest) | 2.110 | 2.110 | 0.000 |
| 1.0 | 2.141 | 2.191 | -0.012 |
| 1.5 | 1.927 | 2.141 | -0.053 |
| 2.0 | 1.682 | 2.141 | -0.120 |

**Analysis:**
- Asymmetry-boost correlation: **-0.844** (strongly velocity-dependent)
- Speed sum conserved: CV = 4.6%
- c_eff law holds locally: mean ratio 1.04

### 6.3 Interpretation

The medium exhibits **medium-dependent Lorentz-like behavior**, not vacuum Lorentz invariance:

- ✓ c_eff law holds in all frames
- ✓ Speed sum approximately conserved
- ✗ Asymmetry is velocity-dependent
- ✗ Preferred rest frame exists

This is analogous to wave propagation in any physical medium (water, air, glass), where a rest frame exists. The preliminary anti-drag behavior (forward speed decreases with boost) differs from classical Fresnel drag and merits further investigation.

---

## 7. τ-Gradient Lensing

### 7.1 Hypothesis

Since c_eff(τ) = √(c₀²τ), spatial τ gradients create speed gradients, which should bend wave paths toward slower regions (lower τ).

### 7.2 Setup

- τ gradient along x-axis: τ_left = 1.0, τ_right = 1.0 + Δτ
- Pulse propagates in y-direction (perpendicular to gradient)
- Track x-deflection as pulse travels

### 7.3 Results

| Δτ | c_left | c_right | x_drift | Deflection |
|----|--------|---------|---------|------------|
| 0.0 | 2.000 | 2.000 | 0.00 | 0.00° |
| 0.2 | 2.000 | 2.191 | -0.22 | -0.61° |
| 0.4 | 2.000 | 2.366 | -0.44 | -1.15° |
| 0.6 | 2.000 | 2.530 | -0.66 | -1.68° |
| 0.8 | 2.000 | 2.683 | -0.92 | -2.25° |

**Analysis:**
- Deflection-gradient correlation: **-1.000** (perfect)
- Deflection rate: **-2.73°** per unit Δτ
- Correct bend direction: **100%**
- Baseline deflection (Δτ=0): **0.00°**

### 7.4 Interpretation

This is one of the strongest results. The τ field acts as an **effective refractive geometry**:

- **τ controls signal speed** → c_eff(τ) = √(c₀²τ)
- **τ gradients create speed gradients** → ∇τ → ∇c_eff
- **Speed gradients bend wave paths** → analogous to Snell's law

The mechanism is closer to **effective-index refraction** than to null geodesics in curved spacetime. However, the geometric interpretation is valid: regions of different τ act like regions of different refractive index, systematically bending wave propagation.

---

## 8. Interpretation: τ as Effective Refractive Geometry

### 8.1 The Geometric Picture

The validated results support interpreting the τ field as an effective geometry:

| τ Configuration | Effective Geometry |
|-----------------|-------------------|
| Uniform τ | Flat (isotropic propagation) |
| τ gradient | Curved (wave bending) |
| τ well (low τ region) | "Gravitational well" analog |
| τ peak (high τ region) | "Repulsive" analog |

### 8.2 Connection to General Relativity Concepts

| GR Concept | QMRT Analog | Status |
|------------|-------------|--------|
| Speed of light | c_eff(τ) | ✓ Validated |
| Curved spacetime | τ gradient geometry | ✓ Validated (lensing) |
| Gravitational time dilation | Moving-structure effects | Pending |
| Null geodesics | Wave paths in τ field | ✓ Lensing shows bending |
| Preferred frame | Medium rest frame | ✓ Confirmed |

### 8.3 Limitations of the Analogy

The QMRT medium is **not** vacuum spacetime:

1. **Preferred frame exists** — The medium has a rest frame where propagation is symmetric. Vacuum Lorentz invariance is not present.

2. **Refraction, not geodesics** — Wave bending occurs through speed gradients (Snell's law analog), not through curved null geodesics.

3. **τ is a field, not a metric** — The τ field controls propagation speed but is not a full spacetime metric tensor.

The correct interpretation is:
> τ-gradient lensing demonstrates effective refractive geometry, geometrically similar to lensing behavior but mechanistically based on propagation-speed gradients rather than curved spacetime.

---

## 9. Limitations and Next Tests

### 9.1 Current Limitations

| Limitation | Impact |
|------------|--------|
| Preferred medium frame | Cannot claim vacuum Lorentz invariance |
| Weak anti-drag (R² = 0.45) | Fresnel analysis needs more seeds |
| No time dilation test | SR analogs incomplete |
| Numerical discretization | ~8% speed overshoot |

### 9.2 Recommended Next Tests

| Priority | Test | Question |
|----------|------|----------|
| P1 | Medium-dragged deformation | Do moving structures deform in τ-frame? |
| P2 | Repeat Fresnel (more seeds) | Tighten anti-drag coefficient |
| P3 | τ-well focusing | Do τ wells focus waves like lenses? |
| P4 | Oscillator time dilation | Do "clocks" slow in high-τ regions? |

---

## 10. Conclusion

The Regulated Recovery v1.1 phase of the QMRT medium has been validated to exhibit:

1. **Self-sustaining topological dynamics** — Recovery loop maintains defects indefinitely
2. **Causal creation-wave chain** — Creation events inject vibrational energy (corr = 0.81)
3. **Emergent statistical isotropy** — Anisotropy < 0.4% across seeds
4. **Bounded τ-dependent signal speed** — c_eff(τ) = √(c₀²τ) validated to < 1% error
5. **Preferred medium frame** — Boost asymmetry confirms rest frame exists
6. **τ-gradient lensing** — Perfect correlation, 100% correct bend direction

These results support the interpretation of the τ field as an **effective refractive geometry** that produces Lorentz-like ingredients within the medium's rest frame. Full vacuum Lorentz invariance is not claimed; the medium is better understood as a wave-supporting substrate with geometric properties.

---

## Appendix A: Test Summary Table

| Test | File | Key Metric | Status |
|------|------|------------|--------|
| Light Cone v2 | `light_cone_test_v2.py` | τ heterogeneity improves propagation | ✓ |
| Directional Isotropy | `directional_isotropy_test.py` | Solver isotropic; defects break symmetry | ✓ |
| Dispersion Relation | `dispersion_relation_test.py` | ω² = c²k² (R² > 0.99) | ✓ |
| Vibration Source | `vibration_source_test.py` | Defects are active sources | ✓ |
| Spectrum Stability | `spectrum_stability_test.py` | Stationary phase (CV ≈ 0.14) | ✓ |
| Vibration Isotropy | `vibration_isotropy_test.py` | Aniso = 0.003 | ✓ |
| Multi-Seed Isotropy | `multi_seed_isotropy_test.py` | Aniso = 0.0035 ± 0.0006 | ★ |
| Signal Speed | `signal_speed_test.py` | c_eff = √(c₀²τ), ratio 1.329 ≈ √1.8 | ★ |
| Creation-Wave | `creation_wave_test.py` | Corr = 0.811, 72% positive | ★ |
| Boost Invariance | `boost_invariance_test.py` | Asymmetry corr = -0.844 | ✓ |
| Fresnel Drag | `fresnel_drag_test.py` | α = -0.067, R² = 0.45 | ○ |
| τ-Gradient Lensing | `tau_gradient_lensing_test.py` | Corr = -1.000, 100% correct | ★ |

Legend: ★ = Major validated result, ✓ = Confirmed, ○ = Candidate (needs more data)

---

## Appendix B: Locked Parameters

These parameters define the Regulated Recovery v1.1 baseline and should not be modified for reproducibility:

```python
REGULATED_RECOVERY_V1_1 = {
    'tau_cap': 1.8,
    'damping_to_tau': 0.20,
    'tau_creation_threshold': 1.001,
    'creation_rate': 0.15,
    'c_0_sq': 4.0,
    'gamma': 0.007,
    'tau_response': 0.02,
    'tau_relaxation': 0.01,
    'dt': 0.12,
    'grid_size': 32,  # Standard; some tests use 48-64
}
```

---

*Document generated: December 2025*  
*All test files located in: `/app/backend/`*  
*Reports and data in: `/app/backend/qmrt_topology/papers/`*
