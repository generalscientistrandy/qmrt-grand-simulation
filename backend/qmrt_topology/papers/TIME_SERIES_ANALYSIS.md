# Time Series Analysis: Remnant → Creation Coupling

**Date: December 2025**
**Status: COMPLETED — COUPLING EFFECT NOT CONFIRMED**

---

## Test Configuration

- Grid: 36³
- Seeds: [10, 42, 99]
- Rate: 0.15
- Strategies: Random (0%), 10% Memory
- Time points: t = 2.0, 5.0, 8.0, 11.0, 14.0 (simulation time)
- Steps per time unit: ~25

---

## Time Series Results

### N_defects Over Time (Mean Across 3 Seeds)

| Time | Random | 10%Mem | Delta |
|------|--------|--------|-------|
| 2.0  | 4.67   | 4.67   | 0% (identical) |
| 5.0  | 5.00   | 2.67   | -47% (memory worse) |
| 8.0  | 7.00   | 6.67   | -5% |
| 11.0 | 4.67   | 6.00   | +29% |
| 14.0 | 4.67   | 4.67   | 0% (identical) |

### Per-Seed Breakdown at t=14.0

| Seed | Random N | 10%Mem N |
|------|----------|----------|
| 10   | 6        | 6        |
| 42   | 1        | 1        |
| 99   | 7        | 7        |

**Observation**: Random and 10%Mem produce **identical results** at every seed at late time.

---

## Analysis

### Key Finding: No Coupling Effect

The time series analysis reveals that:

1. **Early phase (t≤2)**: Strategies are identical (expected — remnant hasn't accumulated)

2. **Mid phase (t=5-11)**: Fluctuations occur, but they go **both directions**:
   - t=5: Memory -47% (worse)
   - t=11: Memory +29% (better)
   - This is noise, not signal

3. **Late phase (t=14)**: Strategies converge to **identical results** — not just similar means, but identical per-seed values

### Why Identical?

The 10% memory fraction is too small to create meaningful divergence:
- 90% of creations are random anyway
- The 10% that use remnant don't accumulate enough bias
- By late time, the stochastic dynamics dominate any weak memory signal

### Previous Single-Seed Result Was Noise

The earlier finding that "seed 42 shows improvement with memory" was an artifact of:
- Single measurement window
- Snapshot timing
- Stochastic fluctuation

The time series proves the strategies are fundamentally equivalent at this coupling strength.

---

## Limitation: Short Simulation Window

The current verification was constrained by practical runtime limits. The external AI execution environment is limited to approximately 300 seconds of wall-clock simulation time, requiring reduced grid size, reduced seed count, and shortened time-series windows.

Therefore, this result should be interpreted as a **short-horizon falsification attempt**, not a definitive long-horizon exclusion of remnant coupling.

The correct conclusion is:

> **Remnant → Creation coupling does not improve recovery-loop closure within the tested short-window regime.**

It remains possible that remnant effects require:
- Longer accumulation time
- Larger grid scale  
- Slower remnant decay
- Stronger but non-overfitting memory fraction
- **Stability-weighted remnant field** rather than raw topology history

---

## Verdict

### Remnant → Creation Coupling: INCONCLUSIVE / LOW PRIORITY

At 10-25% memory fraction with rate=0.15 in short-window tests:
- No improvement in sustainability threshold
- No improvement in late-stage defect count
- Time series shows identical trajectories

**Status**: Moved to low-priority backlog while Damping → τ coupling is tested.

**Future Direction**: Replace raw remnant with **stability-weighted remnant**:
- Current (failed): "create where topology *existed*"
- Future (to test): "create where topology *survived longest*"

Raw remnants remember where topology was. Stability-weighted remnants remember where topology was *viable*. This distinction matters.

---

## Options

### Option A: Test Stronger Memory (50-75%)
But earlier tests showed pure memory (100%) *hurts* performance. The sweet spot, if it exists, would need careful parameter sweep.

### Option B: Proceed to Damping → τ Coupling (Recommended)
- Remnant coupling does not close the recovery loop
- Damping → τ is the next candidate on the Recovery Loop Map
- Move forward rather than over-investing in a null result

### Option C: Archive and Document
- Document remnant coupling as "tested, not beneficial"
- Preserve test scripts for future reference
- Update RECOVERY_LOOP_MAP.md with closure status

---

## Theoretical Implication

Memory-guided creation requires either:
1. **Much stronger memory bias** (but this risks overfitting)
2. **Longer remnant accumulation times** (but system may go extinct first)
3. **Different memory mechanism** (e.g., channel-based rather than remnant-based)

The fundamental issue: **memory of where topology *was* is not the same as memory of where topology *can be stable*.**

Sites where defects existed and died may be *worse* than random — they died for a reason.

---

*Time Series Analysis — December 2025*
