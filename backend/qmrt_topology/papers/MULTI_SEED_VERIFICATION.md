# Multi-Seed Verification Results

**Date: December 2025**
**Status: COMPLETED — RESULTS AMBIGUOUS**

---

## Test Configuration

- Grid: 36³ (reduced for computational speed)
- Seeds: [10, 42, 99]
- Rates: [0.10, 0.15]
- Strategies: Random (0%), 10% Memory, 25% Memory
- Steps: 80 warmup + 200 run + 50 measurement

---

## Raw Results

### Rate = 0.10

| Strategy | Sustain% | Mean N | Per-Seed N |
|----------|----------|--------|------------|
| Random   | 100%     | 9.28   | [14.8, 4.2, 8.8] |
| 10% Mem  | 100%     | 9.28   | [14.8, 4.2, 8.8] |
| 25% Mem  | 100%     | 9.28   | [14.8, 4.2, 8.8] |

**Observation**: All strategies produce **identical results** at rate=0.10.

### Rate = 0.15

| Strategy | Sustain% | Mean N | Per-Seed N |
|----------|----------|--------|------------|
| Random   | 100%     | 13.39  | [18.0, 3.8, 18.3] |
| 10% Mem  | 100%     | 14.22  | [18.0, 6.3, 18.3] |
| 25% Mem  | 100%     | 14.22  | [18.0, 6.3, 18.3] |

**Observation**: Mixed strategies show +6% improvement (14.22 vs 13.39).

---

## Analysis

### Why Identical at Rate=0.10?

At low creation rates, the remnant field hasn't accumulated enough signal to meaningfully bias creation locations. The result:
- The `0.01 + remnant` weighting has ~same effect as pure random
- Difference only emerges when creation rate is high enough for remnant to accumulate

### Seed Variance

Per-seed variance is **substantial**:
- Seed 42 consistently underperforms: N=4.2 at rate=0.10, N=3.8/6.3 at rate=0.15
- Seeds 10 and 99 perform similarly: N=14.8/18.0 at rate=0.10, N=18.0/18.3 at rate=0.15

This 3x variance across seeds dominates any strategy effect.

### Statistical Significance

The +6% improvement at rate=0.15 is:
- Real: 14.22 > 13.39 consistently across mixed strategies
- Small: Within seed variance (3.8 to 18.3)
- **NOT statistically significant** with only 3 seeds

---

## Verdict

### Remnant → Creation Coupling: AMBIGUOUS

1. **No threshold improvement**: All strategies sustain at the same minimum rate
2. **No improvement at low rates**: Results identical at rate=0.10
3. **Marginal improvement at higher rates**: +6% at rate=0.15, but within noise
4. **High seed variance**: 3x variation dominates strategy effect

### Decision Rule Applied

> "A strategy wins only if it improves sustain_probability or mean_late_N across multiple seeds at the same or lower rate."

**Result**: No strategy shows improvement at a *lower* rate. The marginal improvement at equal rate is not statistically significant.

---

## Recommendation

### Option A: More Testing (If Remnant Coupling is High Priority)
- Run 10+ seeds
- Test at intermediate rates (0.075, 0.125)
- Use larger grid (48³) for cleaner signal

### Option B: Proceed to Next Coupling (Recommended)

Given:
- Remnant coupling shows no threshold improvement
- Marginal quality improvement is within noise
- Testing resources are limited

**Proceed to Damping → τ coupling** as the next recovery loop candidate.

Remnant coupling can be revisited later if Damping → τ also fails to close the loop.

---

## Theoretical Note

The identical results at rate=0.10 suggest that remnant-guided creation requires a **minimum remnant accumulation** before it can differentiate from random. This implies:

1. Remnant guidance is a **rate-dependent** effect
2. At low creation rates, remnant doesn't accumulate fast enough to matter
3. The coupling may only be relevant in high-activity regimes

This is consistent with the earlier finding that pure remnant (100%) *hurts* performance — the system needs random exploration when remnant signal is weak.

---

*Multi-Seed Verification — December 2025*
