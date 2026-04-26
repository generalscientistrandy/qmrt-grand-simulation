# Remnant → Creation Coupling Test Results

**Date: December 2025**
**Status: COMPLETED — HYPOTHESIS FALSIFIED**

---

## Test Parameters

- Grid: 48³
- τ threshold: 1.001
- Creation rates tested: 0.10, 0.15, 0.20, 0.25
- Remnant α (bias exponent): 1.0, 2.0
- ε (baseline): 0.01
- Steps: 1000 (200 warmup + 800 test)

---

## Raw Results

### Random Creation (Baseline)

| Rate | Avg Late N | Creates | Sustained |
|------|------------|---------|-----------|
| 0.10 | 0.00       | 15      | NO        |
| 0.15 | 13.00      | 181     | YES       |
| 0.20 | 14.50      | 295     | YES       |
| 0.25 | 11.12      | 209     | YES       |

**Minimal sustainable: rate = 0.15**

### Remnant-Guided (α = 1.0, linear)

| Rate | Avg Late N | Creates | Hi-Remnant% | Sustained |
|------|------------|---------|-------------|-----------|
| 0.10 | 0.00       | 6       | 100%        | NO        |
| 0.15 | 0.00       | 16      | 93.8%       | NO        |
| 0.20 | 5.25       | 88      | 92.0%       | YES       |
| 0.25 | 24.75      | 201     | 99.0%       | YES       |

**Minimal sustainable: rate = 0.20**

### Remnant-Guided (α = 2.0, quadratic)

| Rate | Avg Late N | Creates | Hi-Remnant% | Sustained |
|------|------------|---------|-------------|-----------|
| 0.10 | 0.00       | 11      | 100%        | NO        |
| 0.15 | 0.00       | 14      | 100%        | NO        |
| 0.20 | 6.12       | 70      | 100%        | YES       |
| 0.25 | 14.88      | 186     | 98.9%       | YES       |

**Minimal sustainable: rate = 0.20**

---

## Summary Table

| Configuration | Minimal Sustainable Rate |
|---------------|-------------------------|
| Random        | **0.15**                |
| Remnant α=1.0 | 0.20                    |
| Remnant α=2.0 | 0.20                    |

---

## Analysis

### HYPOTHESIS: FALSIFIED

The original hypothesis was:
> "Remnant-guided creation (placing defects at high-memory sites) will improve reoccupation efficiency and lower the minimal sustainable τ rate below the random baseline of 0.25."

**Result**: The opposite occurred. Random creation sustains at a LOWER rate (0.15) than remnant-guided creation (0.20).

---

### Why Does Remnant Guidance HURT Sustainability?

**Observation 1: Fewer creations at lower rates**
- At rate=0.15, random: 181 creations, remnant: 14-16 creations
- Remnant guidance dramatically suppresses creation rate

**Observation 2: Near-perfect remnant targeting**
- Hi-Remnant% is 93-100% across all remnant-guided runs
- The remnant bias is working as designed — creations DO land at high-memory sites

**Observation 3: Targeting works but kills diversity**

The problem appears to be **spatial concentration**:
- Random creation scatters defects across the entire interior region
- Remnant guidance clusters all creations at previous topological sites
- This creates **over-saturation** at memory sites and **no exploration** of fresh regions

### The Reoccupation Paradox

Efficient reoccupation (placing new defects where old ones died) sounds optimal, but:

1. **Memory sites are decayed sites** — topology died there for a reason (damping, annihilation)
2. **Fresh sites have untapped channel/geometry resources** — random placement accesses these
3. **Clustered creation → clustered annihilation** — all defects meet and cancel

**Metaphor**: It's like replanting seeds only where previous plants died, instead of finding new fertile ground.

---

## Physical Interpretation

### What Random Creation Provides

Random creation acts as **spatial exploration**:
- Probes new regions for viable organization
- Some sites fail, some succeed
- Successful sites build channel protection
- The surviving structure is naturally selected for stability

### What Remnant Guidance Provides

Remnant guidance acts as **spatial memory**:
- Reduces exploration
- Maximizes reoccupation at known sites
- But those sites may be unstable (that's why structure died there)
- Creates echo chamber of repeated failure

### The Balance

Optimal creation strategy may require:
- **Some** remnant guidance (not reinvent the wheel)
- **Some** random exploration (find new stable sites)
- A tunable mix: `weight[x] = ε_random + ε_memory * R[x]^α`

---

## Revised Hypothesis

> "Pure remnant guidance over-concentrates creation and suppresses spatial exploration. Optimal sustainability may require a MIXED strategy: partial remnant bias + partial random exploration."

### Suggested Follow-up Test

Test mixed strategies:
- 25% remnant / 75% random
- 50% remnant / 50% random  
- 75% remnant / 25% random

See if any mixture outperforms pure random (rate = 0.15 threshold).

---

## Implications for Recovery Loop Map

### Remnant → Creation: Not a simple improvement

The naive "memory guides regeneration" coupling does NOT automatically improve sustainability. This suggests:

1. **Memory must be selective** — not all memory is good memory
2. **Exploration vs exploitation tradeoff** — applies to the substrate
3. **Recovery loops need more than closing the circuit** — they need appropriate gain

### Updated Branch Status

| Branch Coupling | Expected Effect | Actual Effect |
|----------------|-----------------|---------------|
| τ → Creation | Enable regeneration | ✓ Works |
| Remnant → Creation (pure) | Lower threshold | ✗ RAISES threshold |
| Remnant → Creation (mixed) | TBD | Needs testing |

---

## Conclusion

**The remnant → creation coupling WORKS mechanistically** (creations do land at high-remnant sites) but **HARMS sustainability** by eliminating spatial exploration.

This is a fundamental insight: **not all closed loops are beneficial loops**. The sign and strength of coupling matters as much as its existence.

**Next investigation**: Test mixed remnant/random strategies to find optimal exploration-exploitation balance.

---

*Remnant Coupling Test Results — December 2025*
