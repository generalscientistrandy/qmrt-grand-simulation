# QMRT Physics Classification - OFFICIAL REFERENCE
## Last Updated: December 2025

---

## CRITICAL: TERMINOLOGY GUIDELINES

### DO NOT USE:
- "emergent relativity"
- "Lorentz invariance"
- "relativistic dispersion"  
- "speed of light" (in QMRT context)
- "rest mass" (relativistic sense)
- "spacetime geometry"

### USE INSTEAD:
- "phonon-like dispersion"
- "medium-limited propagation"
- "condensed matter analog"
- "maximum soliton velocity"
- "effective inertia"
- "substrate dynamics"

---

## VALIDATED PHYSICS SUMMARY

### 1. SUBSTRATE TYPE
**Classification**: Nonlinear optical phonon medium

The QMRT substrate is a **phase-separated medium** with:
- Double-well potential: `V_band(ω) = a_ω(ω² - ω₀²)²`
- Frequency basins at `ω = ±ω₀`
- Domain walls between basins (carry energy)

### 2. DISPERSION RELATION

**LINEAR REGIME** (small perturbations):
```
ω(k) ≈ ω_optical = √(4·a_ω·ω₀²/M_ω) ≈ constant

Group velocity: v_group = dω/dk ≈ 0
```
- This is **OPTICAL PHONON** dispersion
- Linear waves **DO NOT PROPAGATE** (zero group velocity)
- Perturbations oscillate in place

**NONLINEAR REGIME** (solitonic excitations):
```
v(p) = v_max · (1 - exp(-p/p₀))  for p > p_threshold

Parameters:
  v_max ≈ 3.5 (maximum soliton velocity)
  p_threshold ≈ 6-8 (nonlinear regime entry)
  p₀ ≈ 20 (characteristic momentum scale)
```
- Coherent propagation requires **threshold momentum**
- Velocity **saturates** at v_max (NOT relativistic form)

### 3. CONFINEMENT

**Linear Potential**:
```
E(r) = σ·r + E₀

String tension: σ ≈ 0.7-0.8 (energy/length)
R² = 0.999 (excellent fit)
```
- Domain walls carry energy proportional to area
- Isolated excitations have **infinite energy** → confined

### 4. EXCITATION TYPES

| Type | Description | Propagation |
|------|-------------|-------------|
| Linear waves | Small perturbations | v_group ≈ 0 (don't propagate) |
| Solitons | Large-amplitude localized | v → v_max (with threshold) |
| Domain walls | Phase boundaries | Stationary or slow drift |
| Composites | Bound soliton clusters | Reduced wall energy |

### 5. TOPOLOGICAL PROTECTION

- Winding number **conserved** (CV < 1%)
- Excitations are **long-lived metastable**
- Lifetime is grid-independent, perturbation-resistant

---

## PHYSICAL ANALOGIES

### QMRT IS LIKE:
- **Ferromagnet**: Phase-separated domains (up/down magnetization)
- **Type-II superconductor**: Flux tubes between vortices
- **Nonlinear optical crystal**: Polaritons, optical solitons
- **Bose-Einstein condensate**: Bright solitons in attractive BEC

### QMRT IS NOT LIKE:
- **Empty spacetime**: No particles exist without medium
- **Relativistic field theory**: No Lorentz invariance
- **Free particle gas**: Threshold and saturation prevent this
- **Acoustic phonon system**: Group velocity is NOT linear in k

---

## KEY EQUATIONS

### Hamiltonian (frequency sector):
```
H_ω = ½π_ω²/M_ω + V_band(ω) + ½K_ω|∇ω|²

where V_band(ω) = a_ω(ω² - ω₀²)²
```

### Domain wall energy:
```
E_wall(r) = σ·r

σ = ∫ dA [a_ω(ω² - ω₀²)² + ½K_ω|∇ω|²]  (wall profile integral)
```

### Soliton velocity (empirical):
```
v(p) = v_max · (1 - exp(-p/p₀))    for p > p_threshold
v(p) → dispersive/backward         for p < p_threshold
```

### Optical frequency:
```
ω_optical = √(4·a_ω·ω₀²/M_ω)
```

---

## PARAMETER REFERENCE

| Parameter | Symbol | Default | Role |
|-----------|--------|---------|------|
| Basin center | ω₀ | 1.0 | Equilibrium frequency |
| Potential depth | a_ω | 1.0 | Domain wall strength |
| Gradient coefficient | K_ω | 0.05 | Wall thickness |
| Field mass | M_ω | 1.0 | Inertia |
| String tension | σ | ~0.7-0.8 | Confinement strength |
| Max soliton velocity | v_max | ~3.5 | Speed limit |
| Threshold momentum | p_threshold | ~6-8 | Nonlinear onset |

---

## IMPLICATIONS FOR HIGHER LEVELS

### For Cosmology:
- Universe evolution is **substrate dynamics**, not spacetime expansion
- "Inflation" would be domain coarsening / phase ordering
- Structure formation is topological defect nucleation

### For Particle Physics:
- "Particles" are **solitonic excitations**, not point objects
- Confinement is **domain wall tension**, not gauge flux tubes
- "Mass" is effective inertia from nonlinear dynamics

### For Relativity:
- Speed limit exists but is **medium property**, not spacetime geometry
- No Lorentz invariance at fundamental level
- Approximate Lorentz symmetry might emerge at low-energy effective theory

---

## VERSION HISTORY

- **December 2025**: Vacuum limit test completed
  - Discovered optical phonon dispersion
  - Identified threshold momentum
  - Confirmed phonon-like (not relativistic) propagation
  - Formalized corrected terminology

- **Earlier December 2025**: Confinement validation
  - Linear potential confirmed (R² = 0.999)
  - Topological protection validated
  - Composite binding measured

---

*This document supersedes any earlier descriptions using "emergent relativity" terminology.*
