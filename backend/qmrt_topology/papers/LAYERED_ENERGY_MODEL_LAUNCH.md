# Layered Energy Model Launch

**Date: December 2025**
**Status: LAUNCH NOTE — Architectural Redesign**

---

## 1. Why Flat Energy Is Insufficient

### What the Current Simulator Does Well

The validated simulator correctly captures:
- ✓ Topological dual-sector emergence (+/- winding balance)
- ✓ Statistical balance via symmetric creation
- ✓ Organizational symmetry (equal scaffold contribution)
- ✓ Geometry-driven branching (loop → cluster transition)
- ✓ τ self-regulation (prevents runaway coupling)
- ✓ Scale robustness (48³ → 64³)

### What the Current Simulator Misrepresents

All of the above operates on an **effectively uniform energy model**:

```
Current: E_layer1 ≈ E_layer2 ≈ E_layer3 ≈ ...
```

Every organizational layer (defects, loops, clusters, scaffold) draws from the same energy pool with the same rules. This may correctly show *that* structures form, but it cannot properly show:

| Question | Why Flat Energy Fails |
|----------|----------------------|
| Which layers are sustainable? | All layers have equal footing |
| How do transitions happen? | No energetic barrier/cost difference |
| Why does one branch dominate? | No layer-specific maintenance cost |
| Where does usable energy come from? | No distinction from bound energy |
| How is balance maintained across levels? | No layer-specific balance condition |

### The Core Problem

In a **zero-balanced layered universe**, equal energy across all layers is too crude.

The theory requires:
```
Different layers have different energetic roles, costs, and balancing requirements
```

Each layer needs:
1. Its own **energy budget**
2. Its own **maintenance cost**
3. Its own **coupling to other layers**
4. Its own **pathway for gaining or losing usable energy**

---

## 2. Evidence from Recent Results

The flat energy model helps explain several puzzling observations:

| Observation | Flat-Energy Interpretation |
|-------------|---------------------------|
| Richer structures self-limit | Energy redistribution without cost accounting |
| Clustering consolidates without increasing dimension | No energy barrier to consolidation |
| Driving sweet spots appear | Hidden layer costs create effective optima |
| τ self-regulation matters so much | τ is proxying for missing layer energy structure |
| Complexity rises while free energy seems to fall | No usable/bound energy distinction |
| Path B phase-coupling saturates | No energetic incentive for global coordination |

These all suggest: **energy is not being handled with enough structure yet**.

---

## 3. Proposed Layered Energy Variables

### Layer Hierarchy

```
Layer 0: Medium (ψ field, τ field)
Layer 1: Defects (vortex cores, topological charges)
Layer 2: Structures (loops, clusters)
Layer 3: Scaffold (organizational network)
Layer 4: Meta-organization (branch selection, regime)
```

### Per-Layer Energy Components

For each layer L:

| Variable | Symbol | Definition |
|----------|--------|------------|
| **Total energy** | E_L | Energy contained in layer L |
| **Bound energy** | B_L | Energy locked into maintaining existing structure |
| **Free energy** | F_L = E_L - B_L | Energy available for new organization |
| **Maintenance cost** | M_L | Continuous energy required to sustain layer |
| **Transfer rate** | T_{L→L'} | Rate of energy flow between layers |

### Key Ratios

| Ratio | Meaning |
|-------|---------|
| B_L / E_L | Fraction of energy locked in maintenance |
| F_L / E_total | Layer's share of free energy budget |
| M_L / F_L | How quickly free energy is consumed |
| T_{in} / T_{out} | Layer's net energy balance |

---

## 4. Zero-Balance Constraints

### Global Zero-Balance

In a zero-balanced universe, total energy sums to zero:

```
∑_L E_L = 0    (or constant)
```

But this does NOT mean:
```
E_1 = E_2 = E_3 = ...  ← WRONG (flat energy)
```

### Layer-Specific Balance Conditions

Each layer may have its own balance requirement:

| Layer | Balance Condition |
|-------|-------------------|
| Medium (L0) | E_0 + ∑_{L>0} E_L = constant |
| Defects (L1) | Creation rate = Annihilation rate (already have) |
| Structures (L2) | Formation cost = Dissolution release |
| Scaffold (L3) | Maintenance ≤ Available supply from L2 |
| Meta (L4) | Branch energy ≤ Scaffold surplus |

### The Critical Insight

**Local layers can be unequal while global balance holds.**

This allows:
- Energy gradients between layers (driving structure)
- Maintenance costs that vary by complexity
- Sustainable vs unsustainable organizational regimes
- True energetic competition between branches

---

## 5. Hypotheses to Test

### H1: Layer Maintenance Costs Scale with Complexity

```
M_scaffold > M_cluster > M_loop > M_defect > M_medium
```

Higher organizational layers require more energy to maintain.

**Test**: Add per-structure maintenance drain. Do some branches become energetically unsustainable?

### H2: Free Energy Limits Organization Depth

```
Max layer accessible = f(F_total, {M_L})
```

With finite free energy, not all layers can be populated.

**Test**: Reduce total energy input. Does the system truncate at lower organizational levels?

### H3: Layer Transfer Creates Energy Cascades

```
L0 → L1 → L2 → L3 (upward)
L3 → L2 → L1 → L0 (downward)
```

Energy flows upward during organization, downward during dissolution.

**Test**: Track energy transfer direction during loop→cluster transition.

### H4: Zero-Balance Enforces Layer Competition

If ∑ E_L = 0 and each layer has maintenance cost, layers must compete for limited free energy.

**Test**: With finite budget, do branches exclude each other?

### H5: τ Self-Regulation Is Layer-0 Energy Accounting

The τ field may already be implementing primitive layer-0 energy balance.

**Test**: Correlate τ fluctuations with layer energy transfers.

---

## 6. Implementation Strategy

### Phase 1: Energy Accounting (Diagnostic Only)

**Do not change dynamics yet.** First, instrument the existing simulator to measure:

- E_L for each layer at each timestep
- B_L vs F_L partition
- T_{L→L'} transfer rates
- M_L effective maintenance (from decay rates)

This creates an energy audit of the current (flat) model.

### Phase 2: Maintenance Costs

Add explicit maintenance drain to each layer:

```python
E_L -= M_L * dt  # Continuous cost
if E_L < threshold:
    dissolve_structure()  # Layer can't sustain itself
```

Test which branches become unsustainable.

### Phase 3: Layer Transfer Rules

Implement explicit energy flow:

```python
T_{L→L+1} = f(F_L, occupancy_{L+1})  # Upward transfer
T_{L→L-1} = g(dissolution_rate_L)     # Downward transfer
```

### Phase 4: Zero-Balance Enforcement

Ensure global constraint holds:

```python
assert abs(sum(E_L)) < epsilon  # or conserved constant
```

This forces layer competition under finite budget.

---

## 7. What This Replaces

| Previous Plan | New Understanding |
|---------------|-------------------|
| Path B: Phase-coherent mechanism | Mechanism failed; deeper issue identified |
| Add more branch types | Branches need energetic differentiation first |
| Test more organizational regimes | Regimes need energy-distinct layers first |

**The next serious advance is not another mechanism — it's moving from equal-energy layers to a layered zero-balance energy model.**

---

## 8. Relationship to Frozen Branch

| Branch | Status |
|--------|--------|
| Topological Dual-Sector | **FROZEN** — Organizationally valid |
| Path B (Phase-Coherent) | **FAILED** — Mechanism doesn't produce classes |
| Layered Energy Model | **LAUNCH** — Architectural redesign |

The frozen branch results remain valid as organizational observations. They were measured on a flat-energy substrate. Once layered energetics are implemented, we may find:

- Some results strengthen (energetically sustainable regimes)
- Some results weaken (energetically unfavorable regimes)
- New phenomena emerge (layer competition, energy cascades)

---

## 9. Summary Statement

> "The current simulator may correctly capture several organizational regimes while still underrepresenting the energetics that differentiate one layer from another. In a zero-balanced layered universe, energy cannot be treated as uniform across all levels; each layer likely requires its own balance condition and maintenance cost."

---

## 10. First Concrete Experiment

**Phase 1: Energy Audit of Current Simulator**

```
SETUP:
- Run standard simulator (1500 steps)
- At each sample, compute:
  - E_medium (field energy)
  - E_defect (core energy)
  - E_structure (loop/cluster energy)
  - E_scaffold (network energy)

MEASURE:
- How energy distributes across layers
- Whether distribution is static or dynamic
- Where energy accumulates vs dissipates
- Whether τ correlates with layer partitioning

OUTPUT:
- Energy layer time series
- Layer balance ratios
- Evidence for or against uniform distribution

DECISION:
- If distribution is truly flat → confirms problem
- If distribution is structured → reveals existing layer energetics to build on
```

---

*Layered Energy Model Launch Note — December 2025*
