# Dimensional Branching Study: Revised Understanding

**Date**: December 2025  
**Status**: METHODOLOGY REFINED

---

## Key Methodological Insight

The original threshold study was **measuring during build-up phase**, not after the system reached its sustained branch state.

### Evidence

From the diagnostic (`temporal_dimension_test.py` configuration):
```
Step    0: n=1
Step  300: n=5
Step  600: n=39
Step  900: n=23
Step 1500: n=58
Step 2100: n=134
Step 2700: n=211
```

The system takes **~2000-2500 steps** to build into the high-population regime where meaningful dimensional measurements can be made.

### The Oscillation Problem

The system exhibits **population oscillation**:
- Population builds up → peaks at hundreds of nodes
- Then collapses → drops to ~1 node
- Rebuilds → cycle repeats

If measurements happen during trough phases (n=1), they capture noise, not regime characteristics.

---

## Revised Experimental Design

### 1. Wait for Regime Formation
Instead of fixed equilibration steps, wait until:
- Population exceeds threshold (e.g., 150 nodes) consistently
- OR maximum wait time exceeded (indicating sparse regime)

### 2. Measure Peak States
During oscillation:
- Track population continuously
- Measure metrics only during peak phases (n > 50)
- Average over multiple peaks

### 3. Time-to-Branch as Key Metric
New observable: **When does the system first reach sustained high population?**
- Fast branching (strong driving): <500 steps
- Slow branching (weak driving): >2000 steps
- No branching: sparse regime

### 4. Regime Classification Based on Peaks

| Regime | Peak Dimension | Peak Correlation | Peak Fraction |
|--------|---------------|------------------|---------------|
| Peak 2D-like sustained | >1.5 | >0.5 | >50% |
| Peak 2D-like oscillatory | >1.5 | >0.5 | <50% |
| Peak filamentary sustained | <1.4 | >0.5 | >50% |
| Peak filamentary oscillatory | <1.4 | >0.5 | <50% |
| Sub-threshold | --- | --- | Few peaks |
| Collapsed sparse | --- | --- | No peaks |

---

## Preliminary Findings (Partial Data)

From oscillation-tracking study (before timeout):

| Interval | Peak Pop | Peak Dim | Peak Corr | Regime |
|----------|----------|----------|-----------|--------|
| 50 | 149 | 1.36 | 0.83 | Filamentary sustained |
| 100 | 648 | 1.66 | 0.67 | 2D-like sustained |

This suggests:
- **Stronger driving (interval 50)**: Lower dimension, smaller peaks
- **Weaker driving (interval 100)**: Higher dimension, larger peaks

This is **counter to the naive expectation** that stronger driving → higher dimension.

Possible interpretation: Very strong driving causes **rapid turnover** that prevents stable high-dimensional organization from forming. Moderate driving allows the system to **build and sustain** richer structure.

---

## What This Means for the Branching Hypothesis

The "dimensional branching" may involve:

1. **Development time**: System needs time to build organizational complexity
2. **Driving sweet spot**: Too little → sparse; too much → unstable turnover
3. **Peak vs trough**: Dimension is a peak-state property, not an average

The 1D → 2D transition may be:
- Not just a driving-rate threshold
- But a **developmental pathway** dependent on:
  - Driving rate
  - Development time
  - Population stability

---

## Recommended Next Steps

1. **Run longer simulations** (5000+ steps) to capture multiple oscillation cycles

2. **Track oscillation period** as a function of driving rate

3. **Measure dimension only during peaks** (population > threshold)

4. **Plot driving rate vs peak dimension** with proper statistics

5. **Test hysteresis**: Does dimension persist when driving is reduced?

---

## Files

- `/app/backend/branch_transition_threshold_study.py` - Original (measured too early)
- `/app/backend/branch_threshold_study_v2.py` - Population-threshold equilibration
- `/app/backend/oscillation_tracking_study.py` - Peak-aware measurements
- `/app/backend/qmrt_topology/papers/DIMENSIONAL_BRANCHING_STUDY.md` - Initial findings
- This file: Methodology revision notes

---

**Status**: METHODOLOGY REVISED  
**Next**: Run extended oscillation-aware study with longer runtime
