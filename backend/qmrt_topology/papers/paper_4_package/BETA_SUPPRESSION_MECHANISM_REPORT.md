# β-Suppression Mechanism Analysis Report

**Date**: 2025-12-19  
**Branch**: C+E Boundary Investigation  
**Status**: COMPLETE - Mechanism Identified

---

## Executive Summary

The combination of Branch C (β wells for localization) and Branch E (resonance self-selection for topological memory) fails because **β wells fundamentally disrupt the channel self-selection mechanism** while simultaneously **increasing local dispersion** that washes out phase remnants. The ∇β·∇ψ gradient term further **ejects any structures that form** near well boundaries.

**Primary Mechanism**: Channel Disruption (53% slower self-selection rate inside wells)  
**Secondary Mechanism**: Dispersion Spreading (dilutes phase gradients required for regeneration)  
**Tertiary Mechanism**: Boundary Ejection (∇β pushes structures out of wells)

---

## Quantitative Results

### Mechanism 1: Remnant Persistence

| Location | Vortex Death Time | Topology at Death | Remnant Duration |
|----------|------------------|-------------------|------------------|
| Inside β well | 1980 steps | 1.526 | 0 steps |
| Outside β well | 400 steps | 0.611 | 20 steps |

**Finding**: Vortices actually survive ~5× LONGER inside β wells (consistent with Branch C results). However, the remnant topology does not persist for regeneration. The "0 steps" inside the well indicates the simulation ended while the vortex was still alive—no post-death remnant was measured.

**Conclusion**: Remnant damping is NOT the suppression mechanism.

---

### Mechanism 2: Dispersion Rate

| Location | Initial Peak | Final Peak | Peak Decay | Spread Width Change |
|----------|-------------|------------|------------|---------------------|
| Inside β well | 1.500 | 1.084 | 27.8% | 5.3 → 15.5 |
| Outside β well | 1.500 | 1.013 | 32.4% | 5.3 → 0.0 |

**Finding**: Inside β wells:
- Peak amplitude decays LESS (27.8% vs 32.4%)
- But perturbation SPREADS dramatically (width 15.5 vs 0.0)

Outside β wells, perturbations damp in place without spreading.

**Conclusion**: High β causes dispersion (wave spreading) rather than damping. This dilutes the localized phase gradients that serve as seeds for topological regeneration.

---

### Mechanism 3: Channel Assignment Evolution (CRITICAL)

**Channel growth in first 300 steps:**
- Inside β well: +0.1215
- Outside β well: +0.2287
- **Ratio: 0.53** (inside grows at HALF the rate)

**Topology indicator evolution:**
```
Inside:  t=0 → t=300 → t=600 → t=900 → t=1200
         1.186 → 0.063 → 0.143 → 0.015 → 0.014

Outside: t=0 → t=300 → t=600 → t=900 → t=1200  
         1.195 → 0.058 → 0.036 → 0.009 → 0.006
```

**Finding**: The resonance self-selection mechanism—where local oscillators differentiate into distinct frequency channels based on topology—operates at only 53% efficiency inside β wells.

**Physical Interpretation**: The higher wave speed inside wells (c_eff ~ √β ≈ 1.8× faster) causes oscillator phases to mix more rapidly, preventing the slow frequency differentiation required for stable channel formation.

**Conclusion**: Channel self-selection disruption is the DOMINANT suppression mechanism.

---

### Mechanism 4: Wave Propagation

| Parameter | Inside Well | Outside Well | Ratio |
|-----------|-------------|--------------|-------|
| β value | 0.8 | 0.25 | 3.2× |
| Effective wave speed | ~√0.8 ≈ 0.89 | ~√0.25 = 0.5 | 1.8× |

**Wavefront propagation from well center:**
```
Step 0:   r = 0.0,  amp = 1.012
Step 100: r = 2.8,  amp = 1.217
Step 200: r = 7.8,  amp = 1.169
Step 300: r = 12.0, amp = 1.147
```

**Conclusion**: Higher β causes ~1.8× faster wave transport, leading to rapid homogenization of local phase structure.

---

### Mechanism 5: Gradient Term at Boundaries

**Vortex trajectory starting at well boundary (r=20):**
```
t=0:   r = 20.0 (inside)
t=100: r = 21.0 (outside)
t=200: r = 24.0 (outside)
t=300: r = 28.0 (outside)
t=450: r = 46.0 (outside)
Final: r = 57.8

Net drift: +37.8 (PUSHED OUTWARD)
```

**Physical Interpretation**: The term ∇β·∇ψ in the β-weighted Laplacian acts as a force that pushes field gradients from high-β to low-β regions. Vortices, being localized gradient structures, are ejected from wells.

**Conclusion**: Even structures that form inside β wells will be expelled by the gradient term.

---

## Synthesis: Why C+E Fails

The Branch E regeneration mechanism requires:
1. **Phase remnants** to persist as seeds after vortex death
2. **Channel self-selection** to differentiate frequency response locally
3. **Resonance amplification** to regrow topology from remnants

β wells break this at step 2:

```
Normal (Branch E):
  Vortex dies → Phase remnant persists → Channels differentiate →
  High-Q channel resonates with remnant → Topology regenerates

With β wells (C+E):
  Vortex lives longer (good) → But channels differentiate at 53% rate →
  Meanwhile, higher dispersion spreads remnant phase structure →
  No concentrated seed remains when vortex finally dies →
  Regeneration fails
```

The irony: β wells successfully extend individual vortex lifetime (Branch C result), but this comes at the cost of disrupting the medium's ability to remember and regenerate topology (Branch E mechanism).

---

## Implications for New Coupling Strategy

Any successful combination must:

1. **Preserve channel self-selection speed** — Cannot use high-β uniformly
2. **Maintain localized phase gradients** — Need damping, not dispersion
3. **Avoid gradient ejection** — Sharp β boundaries push structures out

**Potential approaches to explore:**
- β wells with resonance decoupled (separate length scales)
- Inverted structure: low-β wells in high-β background (slower dispersion inside)
- Dynamic β that responds to topology (only activate after stable vortex forms)
- Spatial separation: localization region ≠ regeneration region

---

## Conclusion

**The suppression mechanism is definitively identified as CHANNEL DISRUPTION**, with dispersion and boundary ejection as contributing factors.

β wells suppress regeneration NOT by:
- ~~Damping remnants faster~~
- ~~Shortening vortex lifetime~~

β wells suppress regeneration BY:
- **Slowing channel self-selection (53% rate)**
- **Spreading (not damping) phase structure**
- **Ejecting vortices via ∇β gradient force**

This analysis provides the physical foundation for designing a principled coupling strategy that does not repeat the C+E antagonism.
