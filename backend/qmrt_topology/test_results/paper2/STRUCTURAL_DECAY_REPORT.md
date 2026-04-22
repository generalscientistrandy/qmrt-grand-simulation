# Paper 2: Structural Decay Analysis Report

## Date: April 2026

## Executive Summary

**The system is NOT in equilibrium. It exhibits:**
- Event-balanced activity (births ≈ deaths)
- BUT continuous structural degradation (S declining)
- Energy homogenization (ρ flattening)

**Key Finding: S decays toward a non-zero floor (plateau model)**

---

## 1. S(t) Curve Fitting Results

All α values show **plateau decay** as best fit:

```
S(t) = S_floor + (S₀ - S_floor) × exp(-t/τ)
```

| α | S₀ | S_floor | τ (time constant) | Half-life | R² |
|---|-----|---------|-------------------|-----------|-----|
| 0.3 | 0.060 | 0.00096 | 62.3 | 43.2 | 0.847 |
| 0.5 | 0.092 | 0.00137 | 58.1 | 40.3 | 0.836 |
| 0.7 | 0.119 | 0.00171 | 56.3 | 39.0 | 0.827 |

### Interpretation
- **S does NOT decay to zero** — it approaches a floor
- **Higher α → higher S_floor**: More coupling preserves more organization
- **Higher α → faster decay (shorter τ)**: System reaches floor faster
- All models fit well (R² ~ 0.83), plateau slightly better than exponential/power-law

---

## 2. S per Structure (S/N)

| α | Early S/N | Late S/N | Change |
|---|-----------|----------|--------|
| 0.3 | 0.00202 | 0.000049 | **-97.5%** |
| 0.5 | 0.00271 | 0.000054 | **-98.0%** |
| 0.7 | 0.00336 | 0.000062 | **-98.2%** |

### Interpretation
This is **true structural degradation**, not just fragmentation:
- Organization per structure declines ~98%
- Structures exist but carry less spatial information
- Higher α shows slightly faster degradation

---

## 3. Energy Distribution Evolution

| α | Early CV | Late CV | Change |
|---|----------|---------|--------|
| 0.3 | 0.192 | 0.0019 | -99% |
| 0.5 | 0.187 | 0.0018 | -99% |
| 0.7 | 0.187 | 0.0017 | -99% |

### Interpretation
- Energy is **homogenizing** (CV → 0)
- System flattening explains S decline
- Initial energy concentration spreads out over time
- This is fundamental to wave equation with damping

---

## 4. I_TS Evolution (Spacetime Coupling)

| α | Early I_TS | Late I_TS | Change |
|---|------------|-----------|--------|
| 0.3 | 0.828 | 0.843 | +1.8% |
| 0.5 | 0.848 | 0.856 | +0.9% |
| 0.7 | 0.858 | 0.865 | +0.8% |

### Interpretation
- I_TS is **stable** or slightly increasing
- Spacetime coupling doesn't decay with S
- This is important: coupling persists even as organization degrades

---

## 5. Physical Mechanism

The structural decay is explained by:

1. **Energy homogenization**: The initial pulse spreads out due to wave equation + damping
2. **No sustained energy injection**: After initial pulse, no new energy enters
3. **Structures lose definition**: As ρ gradients flatten, structures become less distinct
4. **S_floor reached**: Some residual heterogeneity persists (numerical noise floor?)

### Why births ≈ deaths but S declines?
- New structures are born in **weaker gradients**
- Old structures die when **gradients dissipate below threshold**
- Structures are continuously recycled but each generation is **weaker**

---

## 6. Implications for Paper 2

### What the system DOES over time at scale:
1. **Maintains structure population** (births = deaths)
2. **Loses organizational information** (S → S_floor)
3. **Homogenizes energy** (CV → 0)
4. **Preserves spacetime coupling** (I_TS stable)

### Paper 2 can claim:
1. **Emergent structures are transient by nature** in a driven-dissipative system without sustained input
2. **Higher α slows structural degradation** (higher S_floor)
3. **Structure existence ≠ structure organization** — these decouple over time
4. **The system reaches a "degraded steady state"** — active but disorganized

---

## 7. Next Steps

1. **Run even longer (50k+ steps)** to confirm S_floor is stable
2. **Add sustained driving** (periodic pulses) to see if organization can be maintained
3. **Measure spatial correlation length** to confirm homogenization interpretation
4. **Paper 2 draft** can now argue:
   - "Event balance without structural equilibrium"
   - "Organization requires sustained input, not just energy balance"

---

## Files Generated

- `structural_decay_analysis.json` — Full analysis data
- `extended_timeseries_alpha0.3.json`
- `extended_timeseries_alpha0.5.json`
- `extended_timeseries_alpha0.7.json`
