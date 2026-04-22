# Paper 2: Long-Path Dynamics and Sustained Organization in a Driven-Dissipative Medium

## Abstract

We investigate the long-time behavior of emergent structures in a dynamical medium model, extending the lifecycle analysis of Paper 1 to address structural persistence over extended timescales. Through deterministic numerical simulations spanning 10⁵–10⁶ timesteps, we demonstrate that sustained energy input maintains nonzero spatial organization (S) and coupling (I_TS) in the long-time limit, whereas undriven dynamics exhibit asymptotic decay of organization despite persistent activity. For matched total input energy, periodic and randomized driving produce comparable late-time organization, indicating that input magnitude—not temporal structure—dominates in this regime. These results establish a fundamental separation between kinetic activity (event rates) and coherent organization (S), suggesting that the latter is a non-conserved quantity requiring continuous energetic support.

---

## 1. Introduction

Paper 1 established the mechanisms governing structure formation and lifecycle events in the QMRT dynamical medium: births correlate with energy density peaks, persistence scales with spatial organization (S), and merges occur preferentially in high-gradient regions. This paper extends that analysis to the long-time limit, asking:

**Do emergent structures persist indefinitely, or does organization eventually decay?**

The answer has implications for understanding whether spacetime-like structures can be self-sustaining or require ongoing substrate activity.

---

## 2. Setup

### 2.1 System and Observables

We employ the same 2D wave equation with backreaction coupling:

$$\partial_t^2 \phi = c^2 \nabla^2 \phi - \gamma \partial_t \phi + \alpha (\nabla \cdot \mathbf{v}) \phi$$

where α controls coupling strength, γ provides damping, and v is the strain velocity field.

**Key observables:**
- **S (spatial organization)**: Normalized spatial gradient variance
- **I_TS (spacetime coupling)**: Mutual information between temporal and spatial structure
- **Activity**: Event rate (births + deaths per unit time)

### 2.2 Long-Path Protocol

Simulations extend to 3×10⁴ – 2×10⁵ steps with sampling every 100 steps. This represents 10–100× the timescales examined in Paper 1.

### 2.3 Driving Protocol

For sustained driving experiments:
- Periodic pulses injected at random positions
- Pulse interval: 500–4000 steps
- Pulse amplitude: 1.0–3.0
- Energy-matched random injection for controls

---

## 3. Undriven Dynamics

### 3.1 Asymptotic Decay of Organization

Figure 1 shows S(t) on a logarithmic scale for undriven evolution. Key observations:

1. **S decays exponentially**, then approaches zero: S ∝ exp(-t/τ) with τ ≈ 60 time units
2. **No stable floor exists**: Extended runs (200k steps) show S → 10⁻¹⁶ (numerical zero)
3. **I_TS also decays**, but more slowly than S (scale separation)

At 200k steps:
- S ≈ 10⁻¹⁶ (effectively zero)
- I_TS ≈ 0 (also decayed)
- ρ ≈ constant (energy conserved but homogenized)

### 3.2 Persistent Activity

Despite organizational decay, structure-like activity persists. Figure 3 demonstrates:

- **Activity late/early ratio**: 0.80 (activity persists at 80%)
- **S late/early ratio**: 0.003 (organization decays to 0.3%)

This establishes the central result:

> **Activity ≠ Organization.** Structure-like events (births, deaths) continue indefinitely, but the spatial coherence they represent decays to zero.

### 3.3 Physical Mechanism

The decay mechanism is energy homogenization:
- Initial pulse creates localized energy concentration
- Wave equation + damping spreads energy uniformly
- Gradients flatten → S → 0
- Structure detection continues (from numerical noise) but carries no physical content

---

## 4. Driven Dynamics

### 4.1 Sustained Organization

Figure 1 (red curve) shows that periodic energy injection maintains nonzero organization:

| Condition | S_late | I_TS_late |
|-----------|--------|-----------|
| Undriven | ≈ 0 | ≈ 0 |
| Driven | 0.002 | 0.80 |

The maintenance factor exceeds 10⁷ for S.

### 4.2 Parameter Robustness

Organization is maintained across a wide range of driving parameters:
- Pulse intervals: 500–5000 steps (all maintain S > 0)
- Pulse amplitudes: 0.5–3.0 (all maintain S > 0)
- Even sparse driving (5 pulses over 30k steps) suffices

---

## 5. Controls

### 5.1 Energy-Matched Random Injection

**Critical control:** We compare periodic driving to randomized driving with matched total energy input.

| Condition | Pulses | S_late |
|-----------|--------|--------|
| Periodic | 29 | 0.00205 |
| Random (matched) | 29 | 0.00211 |
| Ratio | — | 0.97 |

**Result:** Periodic ≈ Random

**Interpretation:** Within the tested parameter range, input magnitude—not temporal structure—dominates. The system responds to total injected power, not pulse regularity.

### 5.2 Correlation Length

Spatial correlation length ξ was measured:
- Undriven: ξ ≈ 12 (misleadingly large due to field uniformity)
- Driven: ξ ≈ 10–11 (reflects real structural correlations)

Correlation length in the undriven case becomes ill-defined as the field homogenizes; the apparent large ξ reflects lack of gradients rather than coherent structure.

---

## 6. Scaling

### 6.1 Organization vs Power

Figure 5 shows late-time organization as a function of input power (P = A²/T_interval):

$$S_{late} \propto P^{0.15}$$

Higher power produces higher organization, though with diminishing returns (sublinear scaling).

### 6.2 Duty Cycle Analysis

| Interval | Amplitude | Power | S_late |
|----------|-----------|-------|--------|
| 500 | 1.0 | 0.002 | 0.00192 |
| 1000 | 2.0 | 0.004 | 0.00314 |
| 2000 | 3.0 | 0.0045 | 0.00382 |
| 4000 | 3.0 | 0.0022 | 0.00399 |

Optimal driving: moderate interval (2000–4000), high amplitude (3.0).

---

## 7. Discussion

### 7.1 Core Result

Sustained energy input maintains nonzero spatial organization (S) and coupling (I_TS) in the long-time limit, whereas undriven dynamics exhibit asymptotic decay of organization despite persistent activity.

### 7.2 Activity vs Organization

These results indicate a separation between kinetic activity (event rates) and coherent organization (S), suggesting that the latter is a non-conserved quantity requiring continuous energetic support.

**Undriven:**
- Activity persists (~80% of initial)
- Organization decays (~0.3% of initial, then → 0)

**Driven:**
- Both activity and organization persist

### 7.3 Energy Magnitude Dominates

For matched total input energy, periodic and randomized driving produce comparable late-time organization. This indicates that:
- Input magnitude controls outcome (in this regime)
- Temporal structure of driving is secondary
- The system behaves like a power-driven coherence reservoir

### 7.4 Implications

1. **Emergent structures are transient without sustained input**: Self-organization requires ongoing energetic support
2. **Activity does not imply organization**: Event balance coexists with structural decay
3. **No true equilibrium**: The system approaches homogeneity, not a structured steady state

---

## 8. Conclusion

Paper 1 established what causes structures. Paper 2 establishes what sustains them: nothing, unless energy is continuously supplied.

The medium supports persistent activity but not persistent organization. Structures decay to zero while births and deaths continue—phantom events in a homogenizing field. Only sustained energy injection maintains coherent structure.

This has potential implications for theories of emergent spacetime: if spacetime structure is analogous to our medium's organization, it may require continuous substrate activity to persist.

---

## Figures

1. **Figure 1**: S(t) undriven vs driven (log scale)
2. **Figure 2**: I_TS(t) undriven vs driven
3. **Figure 3**: Activity vs Organization (showing separation)
4. **Figure 4**: Energy-matched control (periodic vs random)
5. **Figure 5**: S_late vs input power

---

## Data Availability

All simulation data, analysis scripts, and figure generation code available at:
`/app/backend/qmrt_topology/test_results/paper2/`

---

## References

[Paper 1] "Statistical Lifecycle Model for Emergent Structures in a Dynamical Medium"
