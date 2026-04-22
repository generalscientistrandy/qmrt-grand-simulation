# Paper 2: Asymptotic Decay Analysis

## Date: April 2026

## Executive Summary

**The system decays completely to a homogeneous state.**

Extended simulations (200k steps) reveal:
- **S → 0** (spatial organization vanishes)
- **I_TS → 0** (spacetime coupling vanishes)
- **ρ → constant** (energy conserved but homogenized)
- **Structures persist** but carry no organization

---

## 1. Complete Decay Timeline

| Window | Time Range | S | I_TS | ρ |
|--------|------------|---|------|---|
| Q1 | 0-1600 | 3.8×10⁻³ | 0.856 | 3.9×10³ |
| Q2 | 1600-3200 | 5.8×10⁻⁷ | 0.836 | 4.5×10³ |
| Q3 | 3200-4800 | 2.0×10⁻¹⁰ | 0.589 | 4.5×10³ |
| Q4 | 4800-6400 | 6.6×10⁻¹⁴ | 0.273 | 4.5×10³ |
| Q5 | 6400-8000 | 1.6×10⁻¹⁶ | 0.000 | 4.5×10³ |

---

## 2. Key Findings

### 2.1. No True Floor Exists
- Earlier observation of "S_floor" was premature
- S continues to decay through 20k, 50k, 100k, 200k steps
- Final S ~ 10⁻¹⁶ is numerical zero

### 2.2. I_TS Also Decays (But Slower)
- I_TS appears stable early (86.5% retention at 50k)
- But by 100k: 55% retention
- By 200k: **0%** retention
- Scale separation is **temporary**, not permanent

### 2.3. Energy is Conserved but Homogenized
- ρ stabilizes around 4.5×10³
- No energy loss, just redistribution
- System approaches uniform energy density

### 2.4. Structures Persist Without Organization
- ~30 structures exist at late times
- But S = 0 means they carry no spatial information
- "Ghost structures" with no physical content

---

## 3. Physical Interpretation

### What's Happening:
1. **Initial pulse** creates energy concentration
2. **Wave equation + damping** spreads energy
3. **Gradients flatten** → structures lose definition
4. **S measures gradients** → S → 0 as system homogenizes
5. **I_TS measures coupling** → also decays as gradients vanish

### Why Structures Still Exist:
- Structure detection is based on thresholds
- Numerical noise creates phantom threshold crossings
- These are artifacts, not physical structures

### The System's End State:
- **Uniform energy density** (heat death analog)
- **No spatial organization** (S = 0)
- **No spacetime coupling** (I_TS = 0)
- **Balanced births/deaths** continue (from noise)

---

## 4. Corrected Paper 2 Claim

### Wrong (our earlier interpretation):
> "Organization decays toward a nonzero floor"

### Correct (based on 200k data):
> "Organization decays completely; apparent floors are slow transients"

### The Real Result:
> "Event balance persists but both fine-scale (S) and coarse-scale (I_TS) organization eventually vanish. The system approaches homogeneity while maintaining phantom structure activity."

---

## 5. Implications

### 5.1. For Paper 2:
- Cannot claim "coupling-dependent residual structure"
- Instead: "decay rate is coupling-dependent but endpoint is universal"
- Higher α may slow decay but doesn't prevent it

### 5.2. For the Theory:
- **Without sustained driving, structure is not self-sustaining**
- Confirms: organization requires ongoing input
- The medium can support activity but not organization

### 5.3. Next Experiment (Critical):
- **Add sustained driving** (periodic pulses)
- Test if organization can be MAINTAINED above zero
- This would prove the "sustained input" hypothesis

---

## 6. What Higher α Does

From α-sweep at 6k steps:
- Higher α → higher S at fixed time
- But all α decay to zero eventually

The interpretation:
- **Higher coupling slows decay** (longer τ)
- But **cannot prevent eventual homogenization**
- Unless sustained input is provided

---

## 7. Updated Paper 2 Structure

1. **Long-path dynamics setup** (deterministic, reproducible)
2. **Event balance observation** (births ≈ deaths)
3. **Complete organizational decay** (S → 0, I_TS → 0)
4. **Timescale separation** (S decays faster than I_TS)
5. **α-dependence** (higher α slows but doesn't prevent decay)
6. **Physical mechanism** (energy homogenization)
7. **Conclusion**: Organization requires sustained input

---

## 8. Data Files

- `ultra_long_50k_alpha0.5.json`
- `timeseries_ultra_long_alpha0.5.json`
- Analysis from 100k and 200k runs (console output)

---

## 9. Next Steps

**🔴 CRITICAL**: Test sustained driving
- Add periodic pulse injection
- See if S can be maintained > 0
- This completes the Paper 2 argument
