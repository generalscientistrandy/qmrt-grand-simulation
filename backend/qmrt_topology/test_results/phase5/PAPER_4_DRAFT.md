# Paper 4: Causal Attractor Control of Topological Defect Populations in a Topological-Memory Medium

**Substrate Lab — QMRT Theory Program**  
**Date**: December 2025  
**Status**: DRAFT v1

---

## Abstract

Prior work in this program established that topological defects can form, interact, and—through resonance self-selection—maintain fluctuating populations via remnant amplification. However, spatial control over where defects regenerate and persist remained elusive: direct combination of localization mechanisms (β-coupling) with topological memory proved antagonistic. Here we demonstrate that spatially varying channel coupling creates a causal attractor landscape for topological defects, biasing their regeneration, transport, and survival toward high-coupling regions. Branch F v2 preserves the full self-selection dynamics while introducing spatial variation only in the channel coupling pathway. The resulting system exhibits: (1) nonzero long-time population saturating at ~1500 defects, (2) nucleation biased toward high-coupling regions (64% interior births with strong gradient), (3) directed drift toward high-coupling regions (mean radial displacement -2.59), and (4) longest lifetime in high-coupling regions (146 vs 56 steps). Critically, inverting the coupling gradient reverses both transport direction and population localization—interior-born defects switch from -2.59 inward drift to +5.24 outward drift, and population concentration shifts from 56% interior to 44% periphery. This inversion test provides causal proof that the coupling gradient, not initial conditions or transient dynamics, determines defect transport and localization. The result represents the first successful co-alignment of topological memory with spatial control in the current program.

---

## 1. Introduction

### 1.1 Program Context

This paper is the fourth in a series investigating the emergence of organized structures from continuous scalar field dynamics, with the long-term goal of understanding whether spacetime-like properties can arise from simpler substrates.

**Paper 1** established that coherent structures form according to measurable statistical lifecycle rules—nucleation, growth, persistence, and decay follow quantifiable distributions rather than random fluctuations.

**Paper 2** demonstrated that sustained organization requires continuous energy input; without driving, structures decay toward equilibrium and organization dissipates.

**Paper 3** introduced β-asymmetry (spatially varying coupling coefficients) and showed that organization can be localized to preferred regions. However, the resulting structures did not exhibit matter-like interactions—they remained field excitations without conserved identity or persistent bound states.

### 1.2 Topological Branch Context

Following Paper 3, the program shifted focus to topological defects—phase singularities in complex scalar fields that carry conserved winding number and interact through well-defined rules.

**Branch B** (Complex Scalar) established that topological defects exist, can be detected via phase winding, and undergo pairwise annihilation when vortex-antivortex pairs meet.

**Branch C** (Coupled Complex Scalar) showed that β-asymmetry extends individual vortex lifetime by approximately 1.67×, but does not trap or pin defects—they still annihilate when encountering opposite-charge partners.

**Branch E** (Resonance Self-Selection) introduced frequency contrast and channel self-selection, discovering that the medium develops *topological memory*: phase remnants persist after vortex annihilation, and resonance amplification can regenerate topology from these remnants. This mechanism maintains a fluctuating but nonzero defect population (mean ~5-6) over long times—a breakthrough termed "remnant amplification."

**Branch C+E Combination** attempted to directly combine β-localization with topological memory. The result was antagonistic: β wells suppress channel self-selection (operating at only 53% rate inside wells), increase local dispersion, and eject structures via ∇β gradient forces. The combination produced fewer defects than resonance alone.

### 1.3 Question of This Paper

The failure of direct C+E combination raised a fundamental question:

> *Can spatially varying parameters create stable spatial control over topological defect populations without disrupting the regeneration mechanism?*

This paper answers affirmatively by identifying the correct parameter to vary: **channel coupling** rather than wave dynamics (β). Branch F v2 preserves the full Branch E self-selection mechanism while introducing spatial variation only in the channel coupling pathway—the parameter controlling core-filling suppression strength.

---

## 2. Model and Methods

### 2.1 Branch F v2 Model

The Branch F v2 simulator implements the complete Branch E dynamics:

**Complex scalar field** ψ = ψ_r + iψ_i evolving under:
```
∂²ψ/∂t² = c_eff² ∇²ψ - γ ∂ψ/∂t + [nonlinear + coupling terms]
```

**Dynamic medium** with relaxation time τ(x,t) responding to local energy density:
```
∂τ/∂t = -λ(τ - τ_eq) + D∇²τ
```
where τ_eq depends on smoothed amplitude.

**Effective wave speed** c_eff = c₀ τ/τ₀, creating medium-dependent propagation.

**Channel self-selection** where local oscillators differentiate in frequency based on topology indicator, building up channel_assignment over time.

**Core-filling suppression** that prevents vortex cores from filling in:
```
suppression = channel_coupling × protection × max(acc_radial, 0)
```

The critical modification in Branch F v2: **channel_coupling varies spatially** while all other dynamics remain uniform.

### 2.2 Spatial Coupling Profiles

Two coupling landscapes were tested:

**Original gradient** (high center):
- Interior (r < 30): coupling = 0.8
- Periphery (r > 50): coupling = 0.2
- Transition: cosine interpolation

**Inverted gradient** (high edge):
- Interior: coupling = 0.2
- Periphery: coupling = 0.8
- Transition: cosine interpolation

The smooth cosine transition (width = 20 grid units) prevents sharp gradients that could cause artifacts.

### 2.3 Zone Definitions

For analysis, the domain is partitioned into:
- **Interior**: r ≤ 30 (high coupling in original, low in inverted)
- **Transition**: 30 < r ≤ 50
- **Periphery**: r > 50 (low coupling in original, high in inverted)

### 2.4 Observables

All metrics are defined consistently across tests:

| Observable | Definition |
|------------|------------|
| Population | Count of detected vortices (phase singularities with |winding| > 0.5) |
| Birth count | New vortices appearing between frames |
| Birth zone | Zone where vortex first appears |
| Radial displacement | r_final - r_initial for tracked vortices |
| Lifetime | Steps from birth to death |
| Late-time population | Mean population in final 30% of simulation |
| Localization fraction | Population in interior / total population |

### 2.5 Causal Test Design

The decisive test for causal control is **gradient inversion**:

If the coupling gradient causally determines defect behavior, then:
1. Inverting high-coupling from center to edge should shift population localization
2. Drift direction should reverse (inward → outward)
3. Survival advantage should follow the high-coupling region

If these predictions hold, correlation becomes causation.

---

## 3. Results

### 3.1 Branch F v2 Establishes Localized Topological Regeneration

With the original coupling gradient (high center), Branch F v2 achieves:

| Metric | Uniform Coupling | Strong Spatial (0.8/0.2) | Change |
|--------|------------------|--------------------------|--------|
| Total births (4000 steps) | 10,472 | 21,035 | +101% |
| Late population | 65.7 | 136.6 | +108% |
| Interior birth % | 44.4% | 63.9% | +44% |
| Periphery birth % | 7.5% | 2.8% | -63% |

**Key finding**: Spatially varying channel coupling roughly doubles regeneration rate while concentrating 64% of births in the high-coupling interior zone. Periphery births are suppressed to only 2.8%.

### 3.2 Long-Time Behavior: Stable Population with Persistent Localization

Extended simulations (20,000 steps) reveal equilibrium behavior:

| Phase | Steps | Population | Interior % |
|-------|-------|------------|------------|
| Early | 0-4k | ~250 | 64-73% |
| Mid | 4k-8k | ~500-700 | 50-60% |
| Late | 8k-12k | ~1000-1300 | 40-45% |
| Equilibrium | 16k-20k | ~1500 | ~37% |

The population saturates around 1500 defects. Localization persists—the 37% interior fraction exceeds the ~25% expected from area alone, indicating real spatial bias.

**Robustness**: Coefficient of variation across different random seeds is 0.09 (very stable). Moderate damping variations (γ = 0.004-0.010) produce CV = 0.09.

### 3.3 Migration Dynamics Reveal Directed Transport

Tracking individual vortex trajectories reveals directed transport:

**Birth → Death transition matrix (original gradient):**

|  | Death: Interior | Death: Transition | Death: Periphery |
|--|-----------------|-------------------|------------------|
| Birth: Interior | 75% | 24% | 1% |
| Birth: Transition | 35% | 63% | 2% |
| Birth: Periphery | 6% | 27% | 67% |

**Migration summary:**
- Stayed in birth zone: 68%
- Migrated outward: 12%
- Migrated inward: 20%
- Mean radial displacement: **-2.59** (inward)

Vortices preferentially drift toward the high-coupling center, not away from it.

### 3.4 Inverted Gradient Provides Causal Proof

The decisive test: inverting the coupling gradient.

| Metric | Original (high center) | Inverted (high edge) |
|--------|------------------------|----------------------|
| Interior population % | **56.0%** | 2.8% |
| Periphery population % | 1.0% | **43.9%** |
| Interior-born drift | -2.59 (inward) | **+5.24 (outward)** |
| Periphery-born drift | N/A | -2.88 (inward) |
| Late population | 654.6 | 343.6 |

**Critical observations:**

1. **Population localization completely flipped**: From 56% interior to 44% periphery
2. **Drift direction reversed for interior-born vortices**: From -2.59 to +5.24
3. **Population lower in inverted case**: High-coupling at periphery is less efficient (smaller area)

The unifying principle: **Vortices always drift toward regions of higher channel coupling**, regardless of whether that region is at the center or periphery.

### 3.5 Survival Is Maximized in the High-Coupling Zone

Lifetime analysis across configurations:

| Configuration | Interior | Transition | Periphery | Longest |
|---------------|----------|------------|-----------|---------|
| Original (high center) | **146** | 124 | 56 | Interior |
| Inverted (high edge) | 77 | 79 | **92** | Periphery |
| Lower damping | **139** | 113 | 62 | Interior |
| Higher damping | **144** | 135 | 66 | Interior |

In all configurations, the **high-coupling region has the longest lifetime**. There is no separate "survival ridge"—the same coupling landscape controls nucleation, transport, and survival.

---

## 4. Mechanistic Interpretation

### 4.1 From Remnant Amplification to Spatial Attractor

Branch E established that topological memory operates through resonance self-selection: local oscillators differentiate in frequency near topology, channel assignment builds up, and this protects vortex cores from filling. When vortices annihilate, phase remnants persist and can be amplified back into new vortices.

Branch F v2 spatially biases this mechanism. Higher channel coupling means:
- Stronger core-filling suppression
- More effective protection for existing vortices
- Higher probability that remnants successfully regenerate

The coupling gradient creates differential regeneration success across space.

### 4.2 Unified Attractor Picture

The central principle emerging from these results:

> **High channel coupling functions as a topological attractor landscape: it biases defect birth, directs drift, and prolongs survival.**

This is a unified mechanism, not three separate effects:
1. **Nucleation bias**: More births where coupling is high (regeneration succeeds more often)
2. **Directed drift**: Vortices move toward high-coupling regions (gradient in protection strength)
3. **Survival advantage**: Longer lifetime where coupling is high (sustained core protection)

### 4.3 What This Is Not

Important boundaries for this result:

- **Not matter-like particles**: Defects are not conserved; they continuously regenerate and annihilate
- **Not bound states**: No stable vortex-vortex bound configurations demonstrated
- **Not universal spacetime emergence**: This is a specific mechanism in a specific model
- **Not derived from first principles**: Channel coupling is a model ingredient, not a fundamental law

The claim is narrower but solid: spatial coupling gradients provide causal control over topological populations.

---

## 5. Relation to Earlier Branches

### 5.1 Why Earlier Branches Were Insufficient

| Branch | Achievement | Limitation |
|--------|-------------|------------|
| B | Topology exists, defects interact | No population maintenance |
| C | β extends lifetime | No trapping, eventual annihilation |
| E | Remnant amplification maintains population | No spatial control |
| C+E | N/A | Antagonistic—β disrupts self-selection |

### 5.2 What Branch F v2 Adds

Branch F v2 achieves the first co-alignment of:
- Topological memory (from Branch E)
- Spatial control (attempted but failed in C+E)
- Long-time population maintenance
- Survival bias toward preferred regions

The key insight: vary channel coupling, not wave dynamics (β). This preserves self-selection while adding spatial structure.

---

## 6. Limitations

This work has clear boundaries:

1. **Two-dimensional only**: All simulations are 2D; 3D behavior may differ
2. **Defects are not conserved**: Population is maintained statistically, not through conservation laws
3. **No matter-like bound states**: Vortices do not form stable pairs or higher-order structures
4. **Model-specific mechanism**: Channel coupling is a construct; connection to physical systems is interpretive
5. **Equilibrium is statistical**: Population fluctuates; localization is a bias, not a trap

---

## 7. Conclusion

This paper demonstrates three principal results:

1. **Spatially varying channel coupling produces robust, nonuniform topological populations.** With strong coupling gradients, birth rates double and localization reaches 64% in the favored region.

2. **The coupling gradient acts as a causal attractor for defect nucleation, transport, and survival.** All three effects point toward high-coupling regions, and all three reverse when the gradient is inverted.

3. **This provides the first successful co-alignment of topological memory with spatial control in the current program.** Prior attempts (Branch C+E) failed due to antagonism between mechanisms; Branch F v2 succeeds by targeting the correct parameter.

The result suggests that organized media may regulate topology not only through *whether* defects exist, but through *where* they are allowed to persist.

---

## Figures (Planned)

**Figure 1**: Branch F v2 population results — births, late population, regional fractions for uniform vs spatial coupling

**Figure 2**: Long-time dynamics — population and localization vs time (20k steps)

**Figure 3**: Migration dynamics — radial displacement distribution and transition matrix

**Figure 4**: Inverted gradient causal test — side-by-side comparison of original vs inverted

**Figure 5**: Lifetime by zone — bar chart across configurations showing high-coupling zone always longest

**Figure 6** (optional): Conceptual diagram of attractor landscape

---

## References

[Internal program documents]
- BRANCH_B_REPORT.md
- BRANCH_C_DECISIVE_REPORT.md  
- BRANCH_E_MECHANISM_DISCOVERY.md
- BRANCH_CE_BOUNDARY_REPORT.md
- BETA_SUPPRESSION_MECHANISM_REPORT.md
- BRANCH_F_V2_SUCCESS_REPORT.md
- BRANCH_F_V2_VERIFICATION_REPORT.md
- INVERTED_GRADIENT_CAUSAL_REPORT.md
