# Paper 2: Alpha Sweep Analysis

## Date: April 2026

## Key Results

### 1. Regime Classification: ALL TRANSIENT

All α values in [0.2, 0.8] produce **transient** regime at 6000 steps:

| α | Regime | Conf | Structures | CV | S_late | I_TS |
|---|--------|------|------------|-------|--------|------|
| 0.2 | transient | 63% | 10.2 | 0.450 | 0.00322 | 0.817 |
| 0.3 | transient | 77% | 11.8 | 0.510 | 0.00412 | 0.835 |
| 0.4 | transient | 77% | 12.8 | 0.502 | 0.00471 | 0.834 |
| 0.5 | transient | 63% | 13.4 | 0.486 | 0.00551 | 0.837 |
| 0.6 | transient | 63% | 12.9 | 0.459 | 0.00652 | 0.845 |
| 0.7 | transient | 77% | 15.9 | 0.556 | 0.00626 | 0.857 |
| 0.8 | transient | 99% | 16.4 | 0.558 | 0.00756 | 0.879 |

### 2. Strong Correlations with α

- **Structure count vs α**: r = 0.952 (strong positive)
- **S (late) vs α**: r = 0.982 (strong positive)
- **I_TS (late) vs α**: r = 0.941 (strong positive)
- **Total births vs α**: r = 0.944 (strong positive)

**Interpretation**: Higher coupling (α) produces:
- More structures
- More spatial organization (S)
- Stronger spacetime coupling (I_TS)
- More activity (births/deaths)

### 3. Detailed Analysis at α=0.5

Extended simulation (10000 steps) reveals:

**Dynamic Equilibrium**:
- Birth-death ratio: 0.994 (balanced)
- Late mean ≈ Overall mean (0.9% diff)
- System is in statistical steady state

**But S Continues Declining**:
- Early S: 0.036
- Middle S: 0.006
- Late S: 0.003

The system has reached **population equilibrium** but not **organizational equilibrium**.

### 4. Characterization of Behavior

The system exhibits **steady churn**:
- High instantaneous variability (structures range 0-45)
- Stable statistics over time
- Balanced birth-death rates
- Monotonically declining spatial organization

This is characteristic of a **driven-dissipative** system:
- Energy continuously pumped in (from initial pulse spreading)
- Structures continuously created and destroyed
- No convergence to static configuration
- But macroscopic statistics reach dynamic equilibrium

### 5. Implications for Paper 2

**What the system DOES over time at scale:**
1. Maintains dynamic equilibrium of structure population
2. Does NOT converge to steady state in the traditional sense
3. Experiences ongoing structural reorganization (high CV)
4. S (organization) continues declining → may reach floor eventually

**Paper 2 can claim:**
- α controls the level of activity and organization
- Higher α → more structures, more coupling, more organization
- System reaches population equilibrium but not organizational equilibrium
- Behavior is reproducible and deterministic

### 6. Files Generated

- `reproducibility_alpha05_6000steps.json` - Multi-seed analysis (confirms determinism)
- `alpha_sweep_6000steps.json` - Full α-sweep data
- `timeseries_alpha*.json` - Individual time series for each α

### 7. Next Steps for Paper 2

1. **Longer simulations** to see if S reaches a floor
2. **Investigate why S decreases** - energy dissipation vs structure formation
3. **Compare S decline rate across α** - is higher α more stable?
4. **Consider noise injection** to study robustness of equilibrium
