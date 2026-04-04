# Final Estimates and Theory Connections

## Making QMRT Experimentally Real

---

## 1. Magnitude Estimates (CRITICAL)

### 1.1 The Question

> "How many defects exist in a real setup? What's the expected phase shift magnitude?"

### 1.2 Condensed Matter Context: Screw Dislocations

**Setup:** Electron interferometry in a crystal with screw dislocations.

**Dislocation density in metals:**
- Annealed metals: n ~ 10⁶ - 10⁸ cm⁻²
- Heavily worked metals: n ~ 10¹⁰ - 10¹² cm⁻²

**Typical electron path length:** L ~ 1 μm = 10⁻⁴ cm

**Number of enclosed defects:**
$$N = n \times A_{\text{loop}} \sim n \times L^2$$

For n = 10⁸ cm⁻² and L = 1 μm:
$$N \sim 10^8 \times 10^{-8} = 1 \text{ defect}$$

### 1.3 Expected Phase Shift

**QMRT prediction:**
$$\Delta\phi = -\pi \tau W$$

For τ = 1 (unit torsion) and W = 1 (single encircling):
$$\boxed{\Delta\phi = -\pi \approx -3.14 \text{ rad}}$$

**This is HUGE** — a half-period shift in interference fringes.

### 1.4 Comparison to Standard AB Effect

| Effect | Phase Shift | Typical Magnitude |
|--------|-------------|-------------------|
| Standard AB | eΦ/ℏ | ~π for Φ = Φ₀/2 |
| **QMRT Torsion** | **-πτW** | **~π per defect** |

**Key point:** The QMRT effect is comparable to the standard AB effect — not astronomically small, not already ruled out.

### 1.5 Why Hasn't This Been Seen?

**Possible reasons:**
1. **Not looked for:** Standard AB experiments avoid defects
2. **Attributed to scattering:** Defects cause scattering; phase effects may be masked
3. **Averaging:** Multiple defects with random orientations may cancel

**QMRT-specific test:** Use **ordered** defect arrays with known τ orientation.

---

## 2. Connection to Known Physics

### 2.1 Einstein-Cartan Theory

**Einstein-Cartan (EC)** is the minimal extension of GR that includes torsion:

| GR | Einstein-Cartan |
|----|-----------------|
| Metric g_μν | Metric + Torsion T^λ_μν |
| 10 DOF | 10 + 24 DOF |
| Torsion = 0 | Torsion ≠ 0 (sourced by spin) |

**QMRT connection:**
- EC: T^λ_μν ~ spin density
- QMRT: T^λ_μν ~ torsion defect density

**Explicit mapping:**
$$T^{\lambda}_{\mu\nu} \leftrightarrow 2\pi J^{\lambda}_{\tau,\mu\nu}$$

where J is the QMRT torsion current.

### 2.2 Topological Defects in Condensed Matter

**Screw dislocations** in crystals carry torsion:

| Crystal Defect | QMRT Object |
|----------------|-------------|
| Screw dislocation | Torsion worldline (τ = ±1) |
| Burgers vector b | Torsion charge τ |
| Dislocation line | Worldline γ |

**The Burgers vector integral:**
$$\oint_\gamma du = b$$

is the condensed matter analog of:
$$\oint_\gamma \omega = 2\pi\tau$$

### 2.3 Gauge Holonomy / Berry Phase

**Standard Berry phase:**
$$\gamma_B = i\oint \langle n | \nabla_R | n \rangle \cdot dR$$

**QMRT holonomy:**
$$\phi = \alpha \oint \omega = -\frac{\tau}{2} \cdot 2\pi W = -\pi\tau W$$

**Key similarity:** Both are geometric phases from parallel transport around a loop.

**Key difference:** Berry phase is in parameter space; QMRT holonomy is in real space with torsion sources.

---

## 3. Tightened Observable Formula

### 3.1 The QMRT Phase Shift

$$\boxed{\Delta\phi_{\text{QMRT}} = -\pi \tau W}$$

where:
- τ = torsion charge of enclosed defect(s) (integer for Z₂)
- W = winding number of the electron path

### 3.2 Total Phase in AB-like Experiment

$$\phi_{\text{total}} = \phi_{AB} + \Delta\phi_{\text{QMRT}} = \frac{e\Phi}{\hbar} - \pi\tau W$$

### 3.3 Explicit Dependence

| Parameter | Effect on Δφ |
|-----------|--------------|
| τ | Linear: Δφ ∝ τ |
| W | Linear: Δφ ∝ W |
| Path area | Only via enclosed defects |
| Defect position | Inside vs outside loop matters |

### 3.4 Interference Pattern

For a two-path interferometer:
$$I = I_0 \left( 1 + \cos(\phi_{\text{total}}) \right)$$

With QMRT correction:
$$I = I_0 \left( 1 + \cos\left(\frac{e\Phi}{\hbar} - \pi\tau W\right) \right)$$

**Observable:** Fringe shift by τW/2 periods compared to defect-free case.

### 3.5 Experimental Protocol

1. **Setup:** Electron interferometer with controllable magnetic flux
2. **Baseline:** Measure fringe pattern without defects (or with defects outside paths)
3. **Test:** Introduce defect(s) inside one path
4. **Measure:** Fringe shift Δφ
5. **Prediction:** Δφ = -πτW per enclosed defect with τ = 1

---

## 4. Summary Table

### 4.1 Magnitude Estimate

| Quantity | Estimate |
|----------|----------|
| Defect density (metals) | 10⁶ - 10¹² cm⁻² |
| Loop area (typical) | 10⁻⁸ cm² (1 μm²) |
| Enclosed defects | ~1 (for moderate density) |
| **Phase shift per defect** | **~π rad** |
| Fringe shift | **1/2 period** |

### 4.2 Theory Connections

| QMRT | Known Physics |
|------|---------------|
| Torsion T^a | EC torsion tensor |
| Defect worldlines | Screw dislocations |
| Holonomy ∮ω | Berry phase / AB effect |
| Quantization ∮ω = 2πn | Flux quantization |

### 4.3 Observable Formula

$$\boxed{\Delta\phi = -\pi\tau W}$$

- τ = torsion charge (integer)
- W = winding number
- Magnitude: ~π per defect (large, measurable)

---

## 5. Falsifiability Statement (Final)

> **"QMRT predicts a phase shift of Δφ = -πτW for spinors encircling torsion defects. For screw dislocations in crystals (τ = ±1), this corresponds to a π ≈ 3.14 rad shift per defect — observable as a half-period fringe shift in electron interferometry. Absence of this shift in controlled experiments with ordered defect arrays would falsify QMRT."**

---

## 6. What This Achieves

| Issue | Resolution |
|-------|------------|
| Magnitude estimate | ~π per defect (large, measurable) |
| Theory connection | EC, condensed matter, Berry phase |
| Observable formula | Δφ = -πτW (explicit) |
| Falsifiability | Clear null-result scenario |

---

*Document created: December 2025*
*Status: Final Estimates — Paper Ready*
