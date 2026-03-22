# QMRT v3: Dimensionless Scaling & Parameter Guide

**Date**: December 2025  
**Purpose**: Concrete parameter ranges for simulation, not blind tuning

---

## 1. Natural Units

Use **compression branch as reference scale**:

| Quantity | Definition | Value |
|----------|------------|-------|
| Mass unit | m_ρ | 1 |
| Speed unit | c_ρ | 1 |
| Self-interaction unit | λ_ρ | 1 |
| **Length unit** | 1/m_ρ | 1 |
| **Time unit** | 1/(m_ρ·c_ρ) | 1 |
| **Amplitude unit** | 1/√λ_ρ | 1 |

---

## 2. Dimensionless Parameters That Matter

After scaling, the system is controlled by:

### Mass/Speed Ratios
- `m_τ/m_ρ` — torsion localization vs density
- `c_τ/c_ρ` — torsion response speed
- `c_φ/c_ρ` — radiation speed (defines light cone)
- `λ_τ/λ_ρ` — torsion self-interaction strength

### Effective Couplings
- `Γ_rt` — compression-torsion (shell formation)
- `Γ_tp` — torsion-radiation (decay threshold)
- `Γ_rp` — compression-radiation (gravity-like)

---

## 3. Stable Starting Window

### Baseline Values (First Simulation)

| Parameter | Range | Best First Value |
|-----------|-------|------------------|
| m_τ/m_ρ | [1.5, 3] | **2** |
| c_τ/c_ρ | [0.5, 1] | **0.7** |
| c_φ/c_ρ | [1.5, 3] | **2** |
| λ_τ/λ_ρ | [0.5, 2] | **1** |

### Physical Interpretation
- `m_τ/m_ρ ≈ 2`: torsion is more localized than density
- `c_τ < c_ρ < c_φ`: torsion stores, radiation escapes
- `λ_τ ≈ λ_ρ`: bounded torsion sector

---

## 4. Coupling Strength Recommendations

### Γ_rt: Compression-Torsion (Shell Formation)

**This is the main confinement-builder.**

| Range | Behavior |
|-------|----------|
| 0 - 0.1 | Weak deformation only |
| 0.2 - 0.5 | **Shell formation window** ✓ |
| 0.5 - 1.0 | Strong confinement / possible overbinding |
| > 1 | Likely numerical or physical collapse |

**Best first target: Γ_rt = 0.5**

---

### Γ_tp: Torsion-Radiation (Decay Threshold)

**Controls whether low-energy torsion survives.**

| Range | Behavior |
|-------|----------|
| < 0.01 | Almost no decay channel |
| 0.05 - 0.2 | **Threshold-like decay behavior** ✓ |
| 0.2 - 0.5 | Strong radiation leakage |
| > 0.5 | Most localized states decay too easily |

**Best first target: Γ_tp = 0.1**

---

### Γ_rp: Compression-Radiation (Gravity-like)

**Should stay small — background sector, not particle dynamics.**

| Range | Behavior |
|-------|----------|
| 0 - 0.02 | Almost negligible |
| 0.02 - 0.1 | **Weak long-range influence** ✓ |
| > 0.1 | Probably too intrusive |

**Best first target: Γ_rp = 0.02**

---

## 5. Mass Ratio for Resonance Locking

**Critical structural parameter.**

Want torsion localized enough to trap energy, but not so heavy it decouples from density.

| m_τ/m_ρ | Effect |
|---------|--------|
| << 1 | Torsion spreads too easily |
| >> 1 | Torsion becomes too stiff and detached |
| **≈ 2** | Density provides background well, torsion stays localized |

**Best first guess: m_τ/m_ρ ≈ 2**

**Scan values**: {1.25, 1.5, 2, 2.5, 3, 4}

---

## 6. Initial Condition Scaling

### Torsion Perturbation (Gaussian Packet)

$$\tau(r, 0) = A_\tau \exp\left(-\frac{r^2}{2R_\tau^2}\right)$$

| Parameter | Range | Best First |
|-----------|-------|------------|
| A_τ (amplitude) | 0.5 - 1.5 | **1** |
| R_τ (radius) | 1 - 3 | **2** |

Initial velocity: zero or small inward kick

### Density
- Start with **vacuum baseline ρ = 0**
- Or weak induced shell from torsion only
- **Do NOT preload huge density clump** — let g_rt generate it dynamically

### Radiation
$$\phi(x, 0) = 0, \quad \partial_t\phi(x, 0) = 0$$

So any φ emission is real decay, not injected by hand.

---

## 7. Practical Scan Order

**Do NOT sweep everything at once.**

### Step 1: Fix Baseline
```
m_ρ = 1, c_ρ = 1, λ_ρ = 1
m_τ = 2, c_τ = 0.7, c_φ = 2, λ_τ = 1
Γ_tp = 0.1, Γ_rp = 0.02
```

### Step 2: Scan Shell Coupling Only
```
Γ_rt ∈ [0.2, 1.2]
```

**Look for:**
- Localized lifetime
- Shell thickness
- Peak torsion amplitude
- Radiated φ-energy fraction

### Step 3: After Finding Good Shell Window
```
Scan: m_τ/m_ρ ∈ {1.25, 1.5, 2, 2.5, 3, 4}
```

### Step 4: Identify Stability/Decay Threshold
```
Scan: Γ_tp
```

---

## 8. Stable Particle Criteria (Objective)

A "particle" should satisfy:

| Criterion | Threshold |
|-----------|-----------|
| Radius bounded | R(t)/R(0) < 2 |
| Retained core energy | E_core(t)/E_tot(0) > 0.7 |
| Radiation fraction | E_φ/E_tot < 0.2 |
| Bounded breathing | Oscillatory but not runaway |
| No UV blow-up | No grid-locked collapse |

This gives a **phase map** instead of intuition only.

---

## 9. First Benchmark Configuration

**Run this exact configuration first:**

```python
# Natural units (compression branch)
m_rho = 1.0
c_rho = 1.0
lambda_rho = 1.0

# Torsion branch
m_tau = 2.0          # m_τ/m_ρ = 2
c_tau = 0.7          # c_τ/c_ρ = 0.7
lambda_tau = 1.0     # λ_τ/λ_ρ = 1

# Radiation branch
c_phi = 2.0          # c_φ/c_ρ = 2 (fastest)
# No mass term for φ

# Couplings
Gamma_rt = 0.5       # Shell formation
Gamma_tp = 0.1       # Decay threshold
Gamma_rp = 0.02      # Weak long-range

# Initial torsion perturbation
A_tau = 1.0
R_tau = 2.0

# Grid
grid_size = 32       # Start with 32³
dt = 0.01            # Timestep
t_max = 50.0         # Run time
```

---

## 10. Expected Outcomes by Regime

### Γ_rt Too Small (< 0.2)
- Torsion disperses
- No shell formation
- No particle

### Γ_rt in Shell Window (0.3 - 0.8)
- Torsion self-localizes
- Density shell forms around torsion core
- Stable breathing oscillation
- **This is the particle regime** ✓

### Γ_rt Too Large (> 1.0)
- Runaway collapse
- Grid-scale instability
- Numerical blow-up

### Γ_tp Too Small (< 0.05)
- All torsion states survive
- No stability hierarchy
- Everything looks "stable" (not physical)

### Γ_tp in Threshold Window (0.05 - 0.2)
- Low-energy torsion survives
- High-energy torsion decays to radiation
- **Physical stability/decay separation** ✓

### Γ_tp Too Large (> 0.3)
- Most states decay
- No stable particles
- Over-radiative

## 11. Discovered Stable Configuration (December 2025)

After systematic scanning, the following configuration produces **stable localized particles**:

```python
# Optimal configuration for long-term stability
m_rho = 1.0
c_rho = 1.0
lambda_rho = 1.0

m_tau = 4.0          # Higher than baseline (stiffer torsion)
c_tau = 0.7
lambda_tau = 1.0

c_phi = 2.0

Gamma_rt = 3.0       # Higher than baseline (stronger shell)
Gamma_tp = 0.1
Gamma_rp = 0.02

# Initial conditions
A_tau = 1.0
R_tau = 2.0
```

**Results at t=50**:
- R/R₀ = 1.24 (well localized, < 2)
- τ_max oscillates around 0.5-0.75 (breathing mode)
- Energy conservation: < 0.01%
- Radiation fraction: < 0.01%

**Key insight**: Need **stronger shell coupling (Γ_rt ≈ 3)** and **higher torsion mass (m_τ ≈ 4)** than the initial conservative estimates.

---

## 12. Measurement Protocol

For each simulation, record:

1. **Radius evolution**: R(t) = √(∫ r² |τ|² d³x / ∫ |τ|² d³x)
2. **Core energy**: E_core = energy within R < 2·R(0)
3. **Radiation energy**: E_φ = ∫ [(∂_t φ)² + c_φ²(∇φ)²] d³x
4. **Torsion amplitude**: max(|τ|)
5. **Shell thickness**: FWHM of ρ profile
6. **Lifetime**: time until R(t) > 2·R(0) or E_core < 0.5·E_tot(0)

---

## 12. Phase Map Template

After scanning, fill in:

| Γ_rt | Γ_tp | Lifetime | Radius Stable? | E_core > 0.7? | Classification |
|------|------|----------|----------------|---------------|----------------|
| 0.2 | 0.1 | ? | ? | ? | ? |
| 0.3 | 0.1 | ? | ? | ? | ? |
| 0.5 | 0.1 | ? | ? | ? | ? |
| 0.8 | 0.1 | ? | ? | ? | ? |
| 1.0 | 0.1 | ? | ? | ? | ? |

Classifications:
- **DISPERSED**: No localization
- **UNSTABLE**: Decays rapidly
- **STABLE**: Meets all criteria ✓
- **COLLAPSED**: Numerical blow-up
