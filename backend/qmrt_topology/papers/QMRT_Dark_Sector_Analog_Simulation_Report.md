# Simulation Evidence for Dark-Sector-Like Behavior in a Regulated QMRT Medium

**Technical Report — OSF Preprint Draft**

**Authors**: QMRT Research Collaboration  
**Date**: December 2025  
**Version**: 1.0

---

## Abstract

We present computational evidence that a regulated Quark Medium Relativity Theory (QMRT) simulator reproduces dark-sector-like observational signatures through unified substrate dynamics, without requiring exotic particles or fields. Three major tests were conducted:

1. **Dark-energy analog**: Dimensional degree-of-freedom (DOF) unlocking produces a **+464.7%** increase in expansion velocity compared to +8.8% when unlocking is disabled, supporting the interpretation that cosmic acceleration arises from progressive activation of accessible degrees of freedom.

2. **Dark-matter analog**: Medium τ-gradient structure produces rotation curves with slope **+0.669** (rising, far exceeding the Keplerian -0.50) and gravitational lensing deflection **3.07×** the point-mass expectation, demonstrating that dark-matter-like signatures can emerge from medium structure without hidden particles.

3. **Bullet-Cluster analog**: During simulated cluster collision, τ-structure (dark matter proxy) separates from gas (collisional matter proxy) with peak separation **21× the no-response control**, reproducing the key observational signature often cited as definitive evidence for particle dark matter.

**Core Finding**: The QMRT simulator reproduces dark-sector-like behaviors through substrate mechanisms: accelerated expansion from dimensional degree-of-freedom activation, dark-matter-like excess rotation/lensing from τ-gradient medium structure, and Bullet-Cluster-like τ/gas separation during collision dynamics.

**Caution**: These results do not prove that real dark energy or dark matter are explained by QMRT. They establish that the QMRT simulation framework can generate analogous dark-sector signatures without adding exotic particles or a separate dark-energy field.

---

## 1. Introduction: The Dark Sector Problem

### 1.1 Observational Evidence

Modern cosmology faces a profound puzzle: approximately 95% of the universe's energy content appears to be "dark" — detectable only through gravitational effects but invisible to electromagnetic observation.

| Component | Fraction | Evidence |
|-----------|----------|----------|
| Dark Energy | ~68% | Accelerating cosmic expansion (Type Ia supernovae, BAO) |
| Dark Matter | ~27% | Galaxy rotation curves, gravitational lensing, cluster dynamics |
| Visible Matter | ~5% | Stars, gas, dust (electromagnetic detection) |

### 1.2 Standard ΛCDM Framework

The current concordance model (ΛCDM) treats these components as fundamentally distinct:

- **Dark energy (Λ)**: A cosmological constant or quintessence field providing negative pressure that accelerates expansion
- **Dark matter**: Weakly interacting massive particles (WIMPs), axions, or other exotic particles providing gravitational attraction without electromagnetic interaction

Despite decades of direct detection experiments, no dark matter particle has been observed. The cosmological constant suffers from the "fine-tuning" and "coincidence" problems.

### 1.3 Alternative Approach: Substrate Dynamics

QMRT proposes that both "dark" phenomena may be observational projections of structured dynamics in an underlying quark medium substrate, rather than separate exotic components. This report presents simulation evidence supporting this possibility.

---

## 2. QMRT Regulated Medium Baseline

### 2.1 Core Physics

The QMRT simulator models wave propagation through a medium characterized by a local parameter τ (tau), which modulates effective wave speed:

$$c_{eff}^2 = c_0^2 \cdot \tau$$

Where:
- $c_0$ = base wave speed
- $τ$ = local medium parameter (analogous to refractive index)

The τ field responds to local energy density, creating self-consistent dynamics.

### 2.2 Regulated Recovery v1.1 Parameters

All tests use a locked baseline configuration validated through extensive stability testing:

```
tau_cap         = 1.8      # Maximum τ (prevents runaway)
damping_to_tau  = 0.20     # Energy recycling rate
dt              = 0.12     # Timestep
gamma           = 0.007    # Wave damping coefficient
c_0_sq          = 4.0      # Base wave speed squared
tau_response    = 0.02     # τ sensitivity to energy
tau_relaxation  = 0.01     # τ relaxation rate
creation_rate   = 0.15     # Topological creation rate
```

### 2.3 Validation History

This baseline has been validated through:
- 2000+ timestep endurance tests (no instability)
- Checkpoint/resume verification (RNG state preservation)
- Multiple seed reproducibility
- Dimensional emergence (1D → 2D → 3D under pressure)
- Topological structure formation (clusters, filaments)

---

## 3. Dark-Energy Analog: DOF Unlock Expansion

### 3.1 Hypothesis

> Cosmic expansion is not merely the stretching of space; it is the activation of additional accessible degrees of freedom in the medium. As the medium saturates its current dimensional state, new DOF become accessible, lowering resistance to expansion and producing observable acceleration.

### 3.2 Experimental Design

**Configuration**:
- Grid: 32³
- Initial state: 1D active (X only), Y and Z suppressed
- Unlock condition: Pressure exceeds threshold (0.025)
- Unlock dynamics: Gradual activation (rate 0.03 per step)

**Comparison**:
- **Enabled**: Dimensional unlocking active
- **Disabled**: Dimensions remain locked (control)

**Metrics**:
- Expansion radius R(T)
- Expansion velocity dR/dT
- Effective dimensionality D_eff
- Unlock timing

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

When dimensional DOF unlock, expansion velocity increases by **464.7%**. Without unlocking, velocity increases only **8.8%**. The acceleration is directly coupled to DOF activation.

### 3.5 Interpretation

The "dark energy" driving expansion acceleration is not an exotic field or cosmological constant — it is the observational consequence of state-space expansion as the medium accesses additional degrees of freedom. This provides a natural mechanism for cosmic acceleration without fine-tuning.

---

## 4. Dark-Matter Analog: τ-Gradient Structure

### 4.1 Hypothesis

> Dark matter is the gravitational and refractive signature of structured quark-medium dynamics (persistent τ gradients, pressure-flow envelopes) around visible matter concentrations. It is not invisible particles but the medium's organized response to matter.

### 4.2 Experimental Design

**Configuration**:
- Grid: 48³
- Central "visible matter": Exponential concentration (radius 6 units)
- All dimensions active (3D)
- Duration: T = 300

**Measurements**:
- Orbital velocity profile V(r) from pressure gradients
- Lensing deflection θ(r) from τ gradients
- Enclosed effective mass M_eff(r)
- τ profile evolution

### 4.3 Results

| Metric | Keplerian Expectation | Observed |
|--------|----------------------|----------|
| **Rotation Slope** | -0.50 (falling) | **+0.669** (RISING) |
| **Lensing Ratio** | 1.0 (point mass) | **3.07** (3× excess) |

The rotation curve is not merely flat — it **rises** with radius, even stronger than the classic flat curves observed in spiral galaxies.

### 4.4 Key Finding

The medium's τ-gradient response to visible matter creates an extended structure that:
1. Provides additional effective gravitational support (rotation curves)
2. Refracts wave paths (gravitational lensing)
3. Extends far beyond the visible matter boundary

No hidden particles are required — the same physics that creates visible matter automatically creates the "dark matter" signature.

### 4.5 Interpretation

An observer inside the 3D medium would interpret the τ-gradient structure as "extra mass" causing additional gravity and lensing. This matches the observational definition of dark matter without requiring exotic particles.

---

## 5. Bullet Cluster Analog: τ/Gas Separation

### 5.1 The Challenge

The Bullet Cluster (1E 0657-56) shows gravitational lensing peaks offset from X-ray gas peaks after cluster collision. This is often cited as definitive evidence for collisionless particle dark matter. Any alternative must explain how "dark matter" can separate from collisional gas.

### 5.2 Experimental Design

**Configuration**:
- Grid: 64³
- Two approaching clusters (initial separation 38 units)
- Collision velocity: 0.8

**Three Tracked Layers**:
1. Visible matter cores (galaxies) — collisionless
2. Gas field — collisional (slows and heats)
3. τ-structure — dark matter proxy (lensing center)

**Variants Tested**:
| Variant | τ_relaxation | τ_response | Purpose |
|---------|-------------|------------|---------|
| No response | 0.01 | 0.0 | Control |
| Normal | 0.01 | 0.02 | Main test |
| Fast relaxation | 0.05 | 0.02 | Quick response |
| Slow relaxation | 0.002 | 0.02 | Lagging response |

### 5.3 Results

| Variant | Peak Separation | Control Ratio |
|---------|-----------------|---------------|
| No τ-response (control) | 0.50 | — |
| Normal τ-response | 9.49 | **19×** |
| Fast relaxation | 10.74 | **21×** |
| Slow relaxation | 4.60 | 9× |

### 5.4 Key Finding

**τ-response creates 19-21× more separation than the no-response control.** The τ-medium structure can separate from gas and behave semi-independently during collision dynamics.

**Unexpected observation**: Fast relaxation produces MORE separation than slow relaxation. This indicates the τ-medium needs to **actively respond** (not just passively lag) to create separation — it responds quickly, overshoots, then relaxes.

### 5.5 Interpretation

The τ-structure has its own response dynamics that allow it to:
- Respond differently from collisional gas
- Separate from gas centroids during collision
- Create Bullet-Cluster-like observation patterns

This demonstrates that medium dynamics can reproduce the key Bullet Cluster signature without requiring collisionless particles.

---

## 6. Unified Interpretation

### 6.1 Shared Substrate Mechanism

All three dark-sector phenomena emerge from the same regulated medium physics:

```
REGULATED τ DYNAMICS
        │
    ┌───┴───┐
    ▼       ▼
  DOF     τ-GRADIENT
ACTIVATION STRUCTURE
    │       │
    ▼       ▼
EXPANSION  EFFECTIVE    COLLISION
ACCEL.     ATTRACTION   SEPARATION
    │       │           │
    ▼       ▼           ▼
  DARK     DARK       BULLET
 ENERGY   MATTER      CLUSTER
 ANALOG   ANALOG      ANALOG
```

### 6.2 τ as Unifying Currency

The local medium parameter τ connects all phenomena:

| Role | Dark Energy | Dark Matter | Bullet Cluster |
|------|-------------|-------------|----------------|
| Energy storage | τ accumulation → pressure | τ gradients → attraction | τ structure → lensing |
| Response time | DOF unlock timing | Gradient persistence | Collision separation |
| Observational | Expansion rate | Rotation/lensing | Offset from gas |

### 6.3 Comparison with ΛCDM

| Observation | ΛCDM Requires | QMRT Provides |
|-------------|---------------|---------------|
| Expansion acceleration | Cosmological constant Λ | DOF activation |
| Flat rotation curves | Dark matter halo (NFW) | τ-gradient envelope |
| Gravitational lensing | Hidden mass | τ-based refraction |
| Bullet Cluster offset | Collisionless particles | τ-response dynamics |

ΛCDM requires two separate exotic components. QMRT provides all three signatures from one substrate physics.

---

## 7. Limitations and Non-Claims

### 7.1 Scope of Claims

**What we claim**:
> The QMRT simulator reproduces dark-sector-like behaviors through substrate mechanisms: accelerated expansion from dimensional degree-of-freedom activation, dark-matter-like excess rotation/lensing from τ-gradient medium structure, and Bullet-Cluster-like τ/gas separation during collision dynamics.

**What we do NOT claim**:
> These results do not prove that real dark energy or dark matter are explained by QMRT. They establish that the QMRT simulation framework can generate analogous dark-sector signatures without adding exotic particles or a separate dark-energy field.

### 7.2 What Has Been Demonstrated

✓ Regulated medium produces expansion acceleration upon DOF activation  
✓ Regulated medium produces flat/rising rotation curves from τ structure  
✓ Regulated medium produces excess lensing from τ gradients  
✓ τ-structure separates from gas during collision  
✓ All phenomena arise from the same substrate physics  

### 7.3 What Has NOT Been Demonstrated

✗ Quantitative match to observed Hubble constant H₀  
✗ CMB power spectrum reproduction  
✗ Large-scale structure formation  
✗ Long-term persistence of Bullet Cluster separation (~150 Myr)  
✗ Baryon acoustic oscillation scale  
✗ Big Bang nucleosynthesis compatibility  
✗ Actual physical existence of the quark medium substrate  

### 7.4 Required for Stronger Claims

1. **Quantitative calibration**: Match observed cosmological parameters
2. **Long-duration tests**: Verify Bullet Cluster separation persists
3. **Large-scale simulations**: Reproduce cosmic structure formation
4. **CMB prediction**: Power spectrum from DOF activation history
5. **Experimental signatures**: Predictions distinguishing QMRT from ΛCDM

---

## 8. Next Validation Targets

### 8.1 Immediate Priorities

| Test | Purpose | Priority |
|------|---------|----------|
| Long-term Bullet Cluster | Does τ/gas separation persist? | P0 |
| Asymmetric τ-lens | Wavefront focusing verification | P1 |
| Time dilation analog | Moving-structure deformation | P2 |

### 8.2 Medium-Term Goals

- Large-scale structure formation from QMRT
- CMB power spectrum prediction
- Quantitative H₀ calibration
- Testable observational predictions

### 8.3 Discriminating Predictions

QMRT may differ from ΛCDM in:
1. **Rotation curve shape**: QMRT shows rising (not flat) curves
2. **Dynamical response times**: τ-medium has characteristic timescales
3. **Structure formation**: Different growth rates and patterns
4. **Lensing correlations**: τ-based vs mass-based predictions

---

## 9. Conclusion

This technical report presents simulation evidence that a regulated QMRT medium can reproduce the three major dark-sector observational signatures:

1. **Accelerating expansion** (+464.7% velocity increase upon DOF unlock)
2. **Dark-matter-like gravity/lensing** (rotation slope +0.67, lensing 3.07×)
3. **Bullet-Cluster-like separation** (21× control during collision)

All three arise from the same τ-field dynamics without exotic particles or cosmological constants. While this does not prove QMRT explains real cosmological dark phenomena, it establishes the framework's capability to generate analogous signatures through unified substrate physics.

The results motivate continued investigation into whether the quark medium hypothesis can provide a viable alternative to the standard ΛCDM paradigm.

---

## 10. Figures and Data

### 10.1 Dark Energy Analog

| Figure | Description | Location |
|--------|-------------|----------|
| fig1 | Expansion radius R(T) | `expansion_dof/figures/fig1_expansion_radius.png` |
| fig2 | Expansion velocity dR/dT | `expansion_dof/figures/fig2_expansion_velocity.png` |
| fig3 | Effective dimensionality | `expansion_dof/figures/fig3_d_eff.png` |
| fig4 | Pressure dynamics | `expansion_dof/figures/fig4_pressure.png` |
| Panel | Combined 4-panel | `expansion_dof/figures/fig_combined_panel.png` |

**Data**: `expansion_dof/expansion_comparison.json`

### 10.2 Dark Matter Analog

| Figure | Description | Location |
|--------|-------------|----------|
| fig1 | Rotation curve V(r) | `dark_matter/figures/fig1_rotation_curve.png` |
| fig2 | Lensing deflection θ(r) | `dark_matter/figures/fig2_lensing_deflection.png` |
| fig3 | τ profile evolution | `dark_matter/figures/fig3_tau_evolution.png` |
| fig4 | Effective mass M_eff | `dark_matter/figures/fig4_effective_mass.png` |
| Panel | Combined 4-panel | `dark_matter/figures/fig_combined_dm_panel.png` |

**Data**: `dark_matter/dark_matter_results.json`

### 10.3 Bullet Cluster Analog

| Figure | Description | Location |
|--------|-------------|----------|
| fig1 | Separation over time | `bullet_cluster/figures/fig1_separation_over_time.png` |
| fig2 | Centroid trajectories | `bullet_cluster/figures/fig2_centroid_trajectories.png` |
| fig3 | Peak separation comparison | `bullet_cluster/figures/fig3_peak_comparison.png` |
| fig4 | τ evolution | `bullet_cluster/figures/fig4_tau_evolution.png` |
| Panel | Combined 4-panel | `bullet_cluster/figures/fig_combined_bullet.png` |

**Data**: `bullet_cluster/bullet_cluster_results.json`

### 10.4 All Files Location

Base path: `/app/backend/qmrt_topology/papers/`

---

## Appendix A: Test Scripts

```bash
# Dark Energy Analog
python /app/backend/expansion_dof_test.py
python /app/backend/expansion_dof_plots.py

# Dark Matter Analog
python /app/backend/dark_matter_analog_test.py
python /app/backend/dark_matter_plots.py

# Bullet Cluster Analog
python /app/backend/bullet_cluster_analog_test.py
python /app/backend/bullet_cluster_plots.py
```

---

## Appendix B: Terminology Guide

| Term | Definition |
|------|------------|
| τ (tau) | Local medium parameter modulating wave speed |
| DOF | Degrees of freedom (accessible dimensional states) |
| D_eff | Effective dimensionality (weighted average of active dimensions) |
| dR/dT | Expansion velocity (rate of change of expansion radius) |
| τ-gradient | Spatial variation in τ field |
| Regulated recovery | Self-consistent τ dynamics with creation/relaxation |

---

## Appendix C: Key Equations

**Wave equation with τ-dependent speed**:
$$\frac{\partial^2 \psi}{\partial t^2} = c_0^2 \tau \nabla^2 \psi - \gamma \frac{\partial \psi}{\partial t}$$

**τ dynamics**:
$$\frac{\partial \tau}{\partial t} = r_{relax}(\tau_{target} - \tau) + r_{damp} E_{kinetic}$$

**Effective velocity from pressure gradient**:
$$V_{eff}(r) \sim \sqrt{r \cdot |\nabla P|}$$

**Lensing deflection from τ gradient**:
$$\theta(r) \sim \int_r^\infty |\nabla \tau| \, dr$$

---

**Document Version**: 1.0  
**Status**: OSF Preprint Draft  
**Last Updated**: December 2025

---

*End of Technical Report*
