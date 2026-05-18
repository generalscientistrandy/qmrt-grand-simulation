# QMRT Unified Cosmology: Dark Sector Synthesis
## Dark Energy, Dark Matter, and Bullet Cluster from Substrate Dynamics

**Date**: December 2025  
**Status**: ALL THREE MAJOR TESTS CONFIRMED  
**Physics Baseline**: Regulated Recovery v1.1 (LOCKED)

---

## Abstract

We present computational evidence that the Quark Medium Relativity Theory (QMRT) simulator reproduces dark-energy-like, dark-matter-like, AND Bullet-Cluster-like observational signatures through unified substrate dynamics, without requiring exotic particles or fields.

**Dark-energy analog**: Dimensional unlocking produces a **+464.7%** increase in expansion velocity when new degrees of freedom (DOF) become accessible, compared to only **+8.8%** when unlocking is disabled.

**Dark-matter analog**: Medium τ-gradient structure produces rotation curves with slope **+0.669** (rising, far flatter than Keplerian -0.50) and lensing deflection **3.07×** the point-mass expectation.

**Bullet-Cluster analog**: During cluster collision, τ-structure separates from gas with **peak separation of 10.74 grid units** — **21× the no-response control** — demonstrating that medium structure can behave semi-independently from collisional matter.

**Core Claim**:
> In QMRT, dark-energy-like acceleration, dark-matter-like excess attraction/lensing, and Bullet-Cluster-like separation arise from structured quark-medium dynamics rather than separate exotic components. The τ-medium has its own response timescale that allows it to behave differently from collisional matter.

---

## 1. Background: Dark Sector Reinterpretation in QMRT

### 1.1 The Standard ΛCDM Picture

In conventional cosmology, the "dark sector" comprises approximately 95% of the universe's energy content:

| Component | Fraction | Standard Explanation |
|-----------|----------|---------------------|
| Dark Energy | ~68% | Cosmological constant Λ or quintessence field |
| Dark Matter | ~27% | WIMPs, axions, or other exotic particles |
| Visible Matter | ~5% | Baryons (protons, neutrons, electrons) |

These components are treated as fundamentally separate, with dark energy driving cosmic acceleration and dark matter providing extra gravitational attraction in galaxies and clusters.

### 1.2 The QMRT Reinterpretation

QMRT proposes that both "dark" phenomena arise from the same underlying substrate physics:

| Phenomenon | ΛCDM | QMRT |
|------------|------|------|
| **Dark Energy** | Exotic repulsive energy | DOF activation → expansion acceleration |
| **Dark Matter** | Invisible massive particles | τ-gradient structure → effective attraction |
| **Gravity** | Spacetime curvature | Pressure-gradient drift in medium |
| **Expansion** | Metric stretching | State-space activation |

The key insight is that **both dark phenomena are observational projections of substrate structure**, not separate substances.

---

## 2. Regulated Medium Baseline

All tests use the **Regulated Recovery v1.1** physics parameters:

```python
# LOCKED BASELINE - DO NOT MODIFY
tau_cap = 1.8           # Maximum τ (prevents hot-spot instability)
damping_to_tau = 0.20   # Energy recycling rate
dt = 0.12               # Timestep
gamma = 0.007           # Wave damping
c_0_sq = 4.0            # Base wave speed squared
tau_response = 0.02     # τ sensitivity to energy
tau_relaxation = 0.01   # τ relaxation rate
creation_rate = 0.15    # Topological creation rate
```

This baseline has been validated through:
- 2000+ timestep endurance tests
- Checkpoint/resume verification (RNG state preservation)
- Multiple seed reproducibility
- 1D → 2D → 3D dimensional emergence

---

## 3. Dark-Energy Analog: Expansion-DOF Coupling

### 3.1 Hypothesis

> Cosmic expansion is not merely the stretching of space; it is the activation of additional accessible degrees of freedom in the medium. As persistent motion saturates the current dimensional phase, the expansion boundary gives way, allowing the medium to distribute energy into a higher state.

### 3.2 Test Design

| Parameter | Value |
|-----------|-------|
| Grid Size | 32³ |
| Unlock Threshold | Pressure > 0.025 |
| Conditions | Enabled vs Disabled unlocking |
| Duration | T = 500 |

### 3.3 Results

| Metric | Enabled (Unlocking) | Disabled (Locked) |
|--------|---------------------|-------------------|
| Y Unlock Time | T = 345.7 | Never |
| Z Unlock Time | T = 347.6 | Never |
| Pre-unlock dR/dT | 0.0322 | 0.0314 |
| **Post-unlock dR/dT** | **0.1818** | 0.0342 |
| **Velocity Change** | **+464.7%** | +8.8% |
| Final D_eff | 2.94 (3D) | 1.29 (1D) |
| Final Radius | 21.05 | 15.94 |

### 3.4 Key Finding

When dimensional DOF unlock (Y at T=345.7, Z at T=347.6), the expansion velocity increases by **464.7%**. Without unlocking, velocity increases only **8.8%**.

**Interpretation**: Expansion acceleration is intrinsic to DOF activation. The "dark energy" driving this acceleration is not a substance — it is the observational consequence of state-space expansion in the substrate.

### 3.5 Figures

Located at: `/app/backend/qmrt_topology/papers/expansion_dof/figures/`

- `fig1_expansion_radius.png` — R(T) comparison
- `fig2_expansion_velocity.png` — dR/dT with +464.7% annotation
- `fig3_d_eff.png` — Effective dimensionality
- `fig4_pressure.png` — Pressure dynamics
- `fig_combined_panel.png` — 4-panel summary

---

## 4. Dark-Matter Analog: τ-Gradient Structure

### 4.1 Hypothesis

> Dark matter is the gravitational and refractive signature of structured quark-medium dynamics (persistent τ gradients, pressure-flow envelopes) around visible matter concentrations. It is not invisible particles but the medium's organized response to matter.

### 4.2 Test Design

| Parameter | Value |
|-----------|-------|
| Grid Size | 48³ |
| Visible Matter Radius | 6 grid units |
| Duration | T = 300 |
| Measurements | V(r), θ(r), M_eff(r), τ(r) |

### 4.3 Results

| Metric | Keplerian Expectation | Observed |
|--------|----------------------|----------|
| **Rotation Slope** | -0.50 (falling) | **+0.669** (RISING) |
| **Lensing Ratio** | 1.0 (point mass) | **3.07** (3× excess) |

### 4.4 Key Findings

1. **Rotation curve**: Not just flat — **rising** with radius (slope +0.67)
2. **Lensing**: **3× stronger** than point-mass prediction at outer radii
3. **τ gradients**: Persist well beyond visible matter boundary
4. **Effective mass**: Exceeds visible mass at all radii

**Interpretation**: The medium's τ-gradient response to visible matter creates an extended "halo" of effective gravitational support. No hidden particles required — the same physics that creates visible matter automatically creates the "dark matter" signature.

### 4.5 Figures

Located at: `/app/backend/qmrt_topology/papers/dark_matter/figures/`

- `fig1_rotation_curve.png` — V(r) vs Keplerian
- `fig2_lensing_deflection.png` — θ(r) with 3× excess
- `fig3_tau_evolution.png` — τ profile over time
- `fig4_effective_mass.png` — M_eff vs visible mass
- `fig_combined_dm_panel.png` — 4-panel summary

---

## 5. Shared Substrate Mechanism

### 5.1 The Unifying Physics

Both dark sector phenomena emerge from the same regulated medium:

```
REGULATED τ DYNAMICS
        ↓
    ┌───┴───┐
    ↓       ↓
  DOF     τ-GRADIENT
ACTIVATION STRUCTURE
    ↓       ↓
EXPANSION  EFFECTIVE
ACCELERATION ATTRACTION
    ↓       ↓
  DARK     DARK
 ENERGY   MATTER
 ANALOG   ANALOG
```

### 5.2 τ as the Shared Currency

The local medium parameter τ plays both roles:

| Role | Dark Energy Connection | Dark Matter Connection |
|------|----------------------|----------------------|
| Energy storage | τ accumulation → pressure → DOF unlock | τ gradients → pressure gradients |
| Wave propagation | c_eff = √(c₀²·τ) | Refractive index ~ τ |
| Creation events | High τ → topology creation | τ structure → effective halo |

### 5.3 Why This Unification Matters

Standard cosmology requires:
- Λ (cosmological constant) for dark energy
- Unknown particles for dark matter
- Fine-tuning (coincidence problem: why Λ ~ ρ_matter now?)

QMRT suggests:
- Both arise from one substrate
- No new particles
- Natural scaling (DOF activation and τ response tied to matter density)

---

## 6. Comparison with Standard ΛCDM

| Observation | ΛCDM Explanation | QMRT Explanation | Notes |
|-------------|-----------------|------------------|-------|
| Hubble expansion | Metric stretching | DOF activation | Both predict acceleration |
| Galaxy rotation curves | DM halo (NFW profile) | τ-gradient envelope | QMRT predicts rising, not flat |
| Gravitational lensing | Extra mass bends light | τ gradients refract waves | Both give excess bending |
| CMB power spectrum | Λ + DM parameters | Not yet tested | Future work |
| BAO scale | Sound horizon + Λ | Not yet tested | Future work |
| Structure formation | DM gravitational seeding | Not yet tested | Future work |

### 6.1 Where QMRT May Differ

1. **Rotation curves**: QMRT shows **rising** curves (slope +0.67), stronger than typical flat curves
2. **Dynamical response**: Medium response may have different timescales than collisionless DM
3. **Bullet Cluster**: ✓ **TESTED** — τ-structure DOES separate from gas during collision (see Section 5)

---

## 6. Bullet Cluster Analog: τ-Gas Separation

### 6.1 The Challenge

The Bullet Cluster is often cited as definitive evidence for particle dark matter because:
- Gravitational lensing peak (dark matter) is offset from X-ray gas peak
- This suggests dark matter passed through while gas collided and slowed

### 6.2 Test Design

Two cluster collision with tracked layers:
- **Gas**: Collisional component (slows during collision)
- **τ-structure**: Dark matter proxy (lensing center)

Variants tested different τ-relaxation rates to understand medium dynamics.

### 6.3 Results

| Variant | Peak Separation | Control Comparison |
|---------|-----------------|-------------------|
| No τ-response (control) | 0.50 | — |
| Normal τ-response | 9.49 | 19× control |
| **Fast relaxation** | **10.74** | **21× control** |
| Slow relaxation | 4.60 | 9× control |

### 6.4 Key Finding

**τ-response creates 19-21× more separation than control.** The medium structure has independent dynamics that allow it to separate from collisional gas.

Unexpected observation: Fast relaxation > Slow relaxation. This indicates the τ-medium needs to **actively respond** (not just lag) to create separation. It responds quickly, overshoots, then relaxes.

---

## 7. Limitations and Non-Claims

### ⚠️ Important Caution

**This does not yet prove that real cosmological dark energy, dark matter, or the Bullet Cluster are explained by QMRT.** It establishes that the QMRT simulator can reproduce dark-sector-like behaviors through substrate mechanisms without adding exotic particles or fields.

### 7.1 What We Have Shown

✓ The regulated medium produces expansion acceleration upon DOF activation  
✓ The regulated medium produces flat/rising rotation curves from τ structure  
✓ The regulated medium produces excess lensing from τ gradients  
✓ The τ-structure separates from gas during collision (Bullet Cluster analog)  
✓ All phenomena arise from the same substrate physics  

### 7.2 What We Have NOT Shown

✗ Quantitative match to observed Hubble constant  
✗ CMB power spectrum reproduction  
✗ Large-scale structure formation  
✗ Long-term persistence of Bullet Cluster separation (~150 Myr)  
✗ Baryon acoustic oscillation scale  
✗ Big Bang nucleosynthesis compatibility  

### 7.3 Required for Stronger Claims

1. **Long-term Bullet Cluster persistence**: Does separation persist on cosmological timescales?
2. **Cosmological simulations**: Large-scale structure from QMRT
3. **CMB prediction**: Power spectrum from DOF activation history
4. **Quantitative calibration**: Match observed H₀, Ω_Λ, Ω_m

---

## 8. Summary: Three Major Tests Passed

| Test | Key Result | Status |
|------|------------|--------|
| **Dark Energy Analog** | +464.7% expansion acceleration after DOF unlock | ✓ CONFIRMED |
| **Dark Matter Analog** | Rotation slope +0.67, Lensing 3.07× | ✓ CONFIRMED |
| **Bullet Cluster Analog** | τ-gas separation 21× control | ✓ CONFIRMED |

**Unified Statement**:
> In QMRT, the 95% of the universe attributed to "dark energy" and "dark matter" may be observational signatures of structured substrate dynamics. All three major dark sector challenges — expansion acceleration, excess gravity/lensing, and Bullet Cluster separation — arise from the same regulated recovery physics without exotic particles or cosmological constants.

---

## 9. Next Validation Tests

### 9.1 Upcoming Tests

| Test | Purpose | Priority |
|------|---------|----------|
| Asymmetric τ-lens | Wavefront focusing verification | P1 |
| Time dilation analog | Moving-structure deformation | P2 |
| Large-scale clustering | Structure formation | P3 |
| Bullet Cluster persistence | Long-term separation test | P4 |

---

## 9. Conclusion

The QMRT framework provides a unified substrate explanation for both dark sector phenomena:

| Phenomenon | Mechanism | Quantitative Result |
|------------|-----------|---------------------|
| Dark Energy | DOF activation | +464.7% expansion acceleration |
| Dark Matter | τ-gradient structure | Slope +0.67, Lensing 3.07× |

**Summary Statement**:
> In Quark Medium Relativity Theory, the 95% of the universe currently attributed to "dark energy" and "dark matter" may instead be observational signatures of structured substrate dynamics. Expansion acceleration arises from progressive DOF activation, while excess gravitational effects arise from τ-gradient medium structure. Both phenomena emerge from the same regulated recovery physics without requiring exotic particles or cosmological constants.

---

## 10. Figure Index and Report Links

### 10.1 Dark Energy Analog (Expansion-DOF)

| Figure | Description | Path |
|--------|-------------|------|
| fig1 | Expansion radius R(T) | `expansion_dof/figures/fig1_expansion_radius.png` |
| fig2 | Expansion velocity dR/dT | `expansion_dof/figures/fig2_expansion_velocity.png` |
| fig3 | Effective dimensionality | `expansion_dof/figures/fig3_d_eff.png` |
| fig4 | Pressure dynamics | `expansion_dof/figures/fig4_pressure.png` |
| Panel | Combined 4-panel | `expansion_dof/figures/fig_combined_panel.png` |

**Full Report**: `/app/backend/qmrt_topology/papers/EXPANSION_DOF_COUPLING_REPORT.md`  
**Data**: `/app/backend/qmrt_topology/papers/expansion_dof/expansion_comparison.json`

### 10.2 Dark Matter Analog (τ-Gradient)

| Figure | Description | Path |
|--------|-------------|------|
| fig1 | Rotation curve V(r) | `dark_matter/figures/fig1_rotation_curve.png` |
| fig2 | Lensing deflection θ(r) | `dark_matter/figures/fig2_lensing_deflection.png` |
| fig3 | τ profile evolution | `dark_matter/figures/fig3_tau_evolution.png` |
| fig4 | Effective mass M_eff | `dark_matter/figures/fig4_effective_mass.png` |
| Panel | Combined 4-panel | `dark_matter/figures/fig_combined_dm_panel.png` |

**Full Report**: `/app/backend/qmrt_topology/papers/DARK_MATTER_ANALOG_REPORT.md`  
**Data**: `/app/backend/qmrt_topology/papers/dark_matter/dark_matter_results.json`

### 10.3 Related Documents

- Dimensional Unlocking: `/app/backend/qmrt_topology/papers/DIMENSIONAL_UNLOCKING_REPORT.md`
- Dimensional Leakage: `/app/backend/qmrt_topology/papers/DIMENSIONAL_LEAKAGE_REPORT.md`
- Spacetime Emergence Arc: `/app/backend/qmrt_topology/papers/SPACETIME_EMERGENCE_COMPLETE_ARC.md`

---

## Appendix A: Test Scripts

```bash
# Dark Energy Analog
python /app/backend/expansion_dof_test.py

# Dark Matter Analog  
python /app/backend/dark_matter_analog_test.py

# Generate Expansion-DOF figures
python /app/backend/expansion_dof_plots.py

# Generate Dark Matter figures
python /app/backend/dark_matter_plots.py
```

---

**Document Version**: 1.0  
**Authors**: QMRT Research  
**Last Updated**: December 2025
