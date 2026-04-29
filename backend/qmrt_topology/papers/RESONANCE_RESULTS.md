# Resonance → τ Test Results

**Date: December 2025**
**Status: ✓ PROMISING — Needs Multi-Seed Validation**

---

## Executive Summary

Weak resonance coupling (res=0.01) **improves both N and distribution** when added to the v1.1 baseline. This is the first successful secondary branch.

| Config | N_defects | tau_loc | vs Baseline |
|--------|-----------|---------|-------------|
| v1.1 only | 104-109 | 1.35 | baseline |
| **v1.1 + res=0.01** | **119** | **1.22** | **N↑14%, loc↓10%** |
| v1.1 + res=0.03 | 112 | 1.08 | N↑8%, loc↓20% |
| v1.1 + res=0.05 | 88 | 1.04 | N↓15%, loc↓23% |

---

## Hypothesis Confirmed

> "Coherent oscillatory regions should recharge τ more constructively than raw damping alone, because they identify topology that is actively phase-coherent rather than merely energetic."

**Result**: Weak resonance (0.01) validates this hypothesis. The selective, coherence-based signal **complements** the coarse damping-based recycling.

---

## Mechanism

```python
# Phase coherence: low variance in local phase gradients = high coherence
coherence = 1.0 / (1.0 + local_phase_variance * 10)

# Resonance signal: coherent oscillation + topological structure
resonance_signal = coherence * topology_norm

# τ coupling
tau += resonance_to_tau * resonance_signal
```

---

## Why Resonance Works (Unlike Channel Release)

| Branch | Signal Type | Effect | Result |
|--------|-------------|--------|--------|
| Damping → τ | Active energy (any) | Coarse recycling | **+45%** |
| Channel → τ | Decay location | Wrong focus | **-15%** |
| **Resonance → τ** | **Coherent activity** | **Selective reinforcement** | **+14%** |

Resonance is **activity-correlated** (like damping) but **more selective** (only coherent regions). This focuses τ elevation on "healthy" organized activity rather than random oscillation or decay sites.

---

## Optimal Strength Range

| Strength | N_defects | tau_loc | Assessment |
|----------|-----------|---------|------------|
| 0.00 | 105 | 1.35 | Baseline |
| **0.01** | **119** | **1.22** | **OPTIMAL** |
| 0.03 | 112 | 1.08 | Good distribution, N starts declining |
| 0.05 | 88 | 1.04 | Over-distributed, N harmed |

**Optimal: res=0.01** — improves both N and distribution without over-distributing.

---

## Candidate Configuration (v1.2)

```python
REGULATED_RECOVERY_TAU_CAP = 1.8      # v1.1 baseline
OPTIMAL_DAMPING_TO_TAU = 0.20         # v1.1 baseline
OPTIMAL_RESONANCE_TO_TAU = 0.01       # NEW secondary branch
RECOVERY_MODE = "regulated_damping_resonance_v1_2"
```

**Pending**: Multi-seed validation required before promotion.

---

## Validation Requirements

Before locking v1.2:

1. **3-seed confirmation at res=0.01, T=1000**
   - Verify N improvement is consistent
   - Verify tau_loc improvement is consistent
   
2. **T=2000 endurance test**
   - Confirm long-horizon stability
   - Check late_N_slope remains near zero

3. **Acceptance criteria**
   - N_mean > v1.1 baseline
   - N_std ≤ v1.1 baseline
   - tau_loc ≤ v1.1 baseline
   - No collapse or extinction

---

## Theoretical Insight

The recovery loop now has two complementary activity-correlated branches:

```
PRIMARY: Damping → τ
  - Responds to ANY oscillation energy
  - Coarse but robust recycling

SECONDARY: Resonance → τ
  - Responds to COHERENT oscillation only
  - Selective reinforcement of organized activity
```

Together, they create a **two-stage τ recharge**:
1. Damping provides base-level energy recycling
2. Resonance adds selective boost to phase-coherent regions

---

## Recovery Branch Status (Updated)

| Branch | Signal Type | Result | Status |
|--------|-------------|--------|--------|
| Damping → τ | Active energy | **+45% → equilibrium** | **PRIMARY VALIDATED** |
| Remnant → Creation | Past location | -95% | Closed |
| Channel → τ | Decay site | -15% | Closed |
| **Resonance → τ** | **Coherent activity** | **+14%** | **PROMISING** |

---

*Resonance → τ Test — December 2025*
