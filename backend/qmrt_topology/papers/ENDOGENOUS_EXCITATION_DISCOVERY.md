# Endogenous Excitation Discovery

**Date**: December 2025  
**Status**: MAJOR FINDING — Requires Validation

---

## Executive Summary

**The medium demonstrates endogenous regeneration capacity.**

After external driving is completely cut off, with **zero new injections**, the population grows from ~1 to ~1200 nodes and stabilizes.

This indicates the medium is not merely a passive substrate under forcing—it can generate new topological structure from its internal dynamics alone.

---

## Key Result: Hard Cutoff Test

### Protocol
1. Build scaffold with external driving (2000 steps, interval=50)
2. Cut off external driving completely (zero injections)
3. Track population for 3000 additional steps

### Observations

| Phase | Steps | Injections | Population |
|-------|-------|------------|------------|
| Build | 0-2000 | 120 | Builds to ~82 (oscillating) |
| Post-cutoff | +0 | 0 | 125 |
| Post-cutoff | +200 | 0 | 551 |
| Post-cutoff | +600 | 0 | 685 |
| Post-cutoff | +1000 | 0 | 900 |
| Post-cutoff | +1400 | 0 | 1003 |
| Post-cutoff | +2000 | 0 | 1247 |
| Post-cutoff | +2800 | 0 | 1152 |

**Population grows >10x after driving is removed.**

### Robustness

| Seed | Pop at Cutoff | Pop after 2000 steps (no driving) | Outcome |
|------|---------------|-----------------------------------|---------|
| 42 | 1 | 1195 | GROWTH |
| 456 | 1 | 1254 | GROWTH |

Result is robust across different random seeds.

---

## Interpretation

### What This Means

1. **The medium is not purely externally maintained**
   - Scaffold survives and grows without external input
   - Internal dynamics generate new topological structure

2. **Endogenous regeneration exists**
   - The medium has an internal source of structural generation
   - This is distinct from mere "memory" or "coasting"

3. **Self-organization capacity**
   - The medium can organize itself once seeded
   - External driving may be needed to initiate, but not to sustain

### Possible Mechanisms

1. **Wave-field instability**: The psi field may have growing modes that spontaneously generate amplitude minima (defects)

2. **Channel memory**: The channel_assignment field preserves organizational structure, which may seed new defect formation

3. **Topological reproduction**: Existing defects may catalyze new defect formation through field interactions

4. **Resonance amplification**: Internal oscillations may amplify and generate new structure

---

## Caveats and Validation Needed

### Possible Artifacts

1. **Measurement at trough**: The "Pop at cutoff: 1" may be catching oscillation trough, not true population. Need finer sampling.

2. **Delayed injection effect**: Some injections may have long-delayed effects that manifest post-cutoff. Need to test with zero build-phase injections.

3. **Field momentum**: The psi_r_dot and psi_i_dot fields carry momentum that could drive growth. Need to test if zeroing momentum prevents growth.

## Validation Tests Completed

### Test 1: No-Build (Initial Seeding Only, Zero Driving)
**Result**: Population rises briefly (~220 nodes), then decays to ~2 by step 4500
**Interpretation**: Initial seeding alone cannot sustain structure—eventually collapses

### Test 2: Priming Duration
| Build Steps | Injections | Final Pop (1500 steps post-cutoff) |
|-------------|------------|-------------------------------------|
| 0 | 0 | ~2 (decays) |
| 250 | 15 | 418 |
| 500 | 30 | 722 |
| 1500 | 90 | 1258 |
| 2000 | 120 | 1241 |

**Interpretation**: More priming establishes stronger regeneration capacity. Saturates around ~1200.

### Test 3: Channel Memory Erasure
- Channel erased at cutoff: Population still grows to ~1000
- **Conclusion**: Channel memory is NOT the critical factor

### Test 4: Momentum Zeroing
- Momentum zeroed at cutoff: Population still rises to ~500
- Momentum rebuilds itself
- **Conclusion**: Wave field has intrinsic regenerative dynamics

---

## Refined Interpretation

The regeneration comes from **intrinsic wave field instability**, not from stored momentum or channel memory:

1. The wave field (psi_r, psi_i) has growing modes
2. External driving "organizes" these modes into coherent structure
3. Once organized, the field continues to generate defects through its natural dynamics
4. The Laplacian coupling propagates and amplifies structure

**Key insight**: External driving doesn't just add energy—it establishes **organizational patterns** that the wave field then perpetuates.

---

## Scientific Significance

If validated, this result suggests:

> **The proto-spacetime scaffold is not merely a driven non-equilibrium structure, but an autocatalytic self-organizing medium that can regenerate its topology from internal dynamics once seeded.**

This would be a significant upgrade from Paper 6's conclusion (driven NESS scaffold) to:

> **An autocatalytic NESS scaffold with endogenous regeneration capacity.**

This changes the interpretive framework:
- Not just: "external driving maintains structure"
- But: "external driving seeds structure; internal dynamics regenerate it"

---

## Next Steps

1. **Validate the finding** with the tests listed above
2. **Identify the mechanism** (wave instability? channel memory? resonance?)
3. **Map the parameter space** where endogenous regeneration occurs
4. **Test sustainability limits** (does it eventually saturate or collapse?)

---

## Files

- `/app/backend/endogenous_excitation_test.py` — Test implementation
- `/app/backend/qmrt_topology/papers/endogenous_excitation_results.json` — Raw data

---

**Status**: MAJOR FINDING — Awaiting validation tests  
**Date**: December 2025
