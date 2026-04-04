# Experimental Consistency Note

## Why This Effect Hasn't Been Observed Yet

---

## 1. What Are the Defects? (Attack 1)

### 1.1 Clarification

> **"Effective torsion defects correspond to localized topological dislocations in the phase field, analogous to screw dislocations in condensed matter systems."**

### 1.2 Three Interpretations

| Interpretation | Physical Realization | τ Value |
|----------------|---------------------|---------|
| **Material defects** | Screw dislocations in crystals | τ = ±1 (Burgers vector) |
| **Effective emergent** | Phase vortices in order parameter | τ = winding number |
| **Spacetime torsion** | Einstein-Cartan torsion sources | τ = spin density integral |

### 1.3 For This Paper

We focus on the **condensed matter interpretation**:
- Defects = screw dislocations or phase vortices
- τ = topological charge (integer)
- Experimentally accessible in crystals, superfluids, superconductors

---

## 2. Why Hasn't This Been Seen? (Attack 2 — THE BIG ONE)

### 2.1 The Problem

Standard Aharonov-Bohm experiments:
- Measure phase shifts to ~0.01 rad precision
- Would easily detect a π ≈ 3.14 rad shift

**Why no observation?**

### 2.2 Answer: Four Reasons

#### Reason 1: Defects Are Avoided

Standard AB experiments are designed with:
- **Defect-free samples** (high-purity crystals)
- **Controlled geometries** (no dislocations in beam path)
- **Magnetic flux only** (torsion not considered)

> **"QMRT predicts effects only when torsion defects are deliberately enclosed by the electron path. Standard AB setups exclude such defects by design."**

#### Reason 2: Statistical Cancellation

In polycrystalline or disordered samples:
- Defects have **random orientations** (τ = +1 and -1 equally)
- Phase shifts **cancel on average**: ⟨Δφ⟩ = 0

> **"Random defect distributions produce zero net phase shift. QMRT effects require ordered defect arrays with controlled τ orientation."**

#### Reason 3: Attributed to Scattering

When defects ARE present:
- They cause **electron scattering** (amplitude loss)
- Phase effects are **masked by decoherence**
- Experiments discard "noisy" data

> **"Defect-induced phase shifts may have been present but attributed to scattering artifacts rather than coherent torsion effects."**

#### Reason 4: Wrong Topology

QMRT requires:
- Electron path **encircles** defect (W = 1)
- Not just passes near it

Standard setups:
- Paths may pass **through** defect regions (not around)
- No topological encirclement

> **"The QMRT phase shift requires topological encirclement (W ≠ 0). Paths that intersect defect regions without encircling them show no effect."**

### 2.3 Summary Statement (Include in Paper)

> **"The predicted π phase shift has not been observed because: (1) standard AB experiments use defect-free samples; (2) random defect orientations cause statistical cancellation; (3) defect-induced decoherence masks phase effects; and (4) topological encirclement (W ≠ 0) is required but not achieved in typical geometries. A dedicated experiment with ordered defect arrays and controlled encirclement would provide a definitive test."**

---

## 3. Sign and Convention (Attack 3)

### 3.1 Definition of τ

$$\tau = \pm 1$$

where:
- **τ = +1**: Right-handed screw dislocation (or positive winding vortex)
- **τ = -1**: Left-handed screw dislocation (or negative winding vortex)

### 3.2 Properties

| Property | Value |
|----------|-------|
| **Dimension** | Dimensionless |
| **Range** | τ ∈ ℤ (integer for Z₂ statistics) |
| **Minimal nontrivial** | τ = ±1 |
| **Orientation** | Sign determined by handedness/chirality |

### 3.3 Relation to Burgers Vector

For screw dislocations:
$$\tau = \frac{b \cdot \hat{z}}{|b|}$$

where b is the Burgers vector and ẑ is the dislocation line direction.

### 3.4 The Phase Shift Formula (Complete)

$$\boxed{\Delta\phi = -\pi \tau W = -\pi (\pm 1) W}$$

- τ = ±1 (defect chirality)
- W ∈ ℤ (winding number of electron path)
- Δφ ∈ πℤ (quantized in units of π)

---

## 4. Proposed Experimental Test

### 4.1 Setup

1. **Sample**: Crystal with **ordered** screw dislocation array
2. **Geometry**: Electron path encircles **single** dislocation
3. **Control**: Compare with defect-free reference path
4. **Measurement**: Interference fringe shift

### 4.2 Expected Signal

| Configuration | τ | W | Δφ | Fringe Shift |
|---------------|---|---|-----|--------------|
| No defect | 0 | any | 0 | None |
| One RH defect | +1 | 1 | -π | 1/2 period |
| One LH defect | -1 | 1 | +π | 1/2 period |
| RH + LH pair | 0 | 1 | 0 | None (cancel) |

### 4.3 Falsifiability

| Outcome | Interpretation |
|---------|----------------|
| Δφ = -π per RH defect | QMRT confirmed |
| Δφ = 0 with single defect | QMRT falsified |
| Δφ ≠ 0 but ≠ π | Modified QMRT (fractional τ?) |

---

## 5. Statement for Paper (Copy This)

### Section: Experimental Considerations

> **"We address the question of why this effect has not been observed in existing Aharonov-Bohm experiments. Standard AB setups employ defect-free samples and controlled magnetic flux, explicitly avoiding topological defects. When defects are present (as in polycrystalline samples), their random orientations lead to statistical cancellation of the phase shift. Furthermore, defect-induced scattering causes decoherence that can mask coherent phase effects. Finally, the QMRT prediction requires topological encirclement (winding number W ≠ 0), which is not achieved in typical experimental geometries where electron paths may pass through defect regions without encircling them.**
>
> **A definitive test of QMRT would require: (1) a sample with an ordered array of screw dislocations of known chirality; (2) an electron interferometer geometry where one path encircles a single defect while the other does not; and (3) measurement of the resulting fringe shift. The predicted signal is a π phase shift (half-period fringe displacement) per enclosed defect with τ = ±1. Absence of this shift would falsify the framework."**

---

## 6. Summary

| Attack | Resolution |
|--------|------------|
| "Where do defects come from?" | Screw dislocations / phase vortices (τ = ±1) |
| "Why not already seen?" | Avoided, cancelled, masked, or wrong topology |
| "Sign and convention?" | τ = ±1 (chirality), dimensionless, integer |

---

*Document created: December 2025*
*Status: Experimental Consistency Note — Pre-Submission*
