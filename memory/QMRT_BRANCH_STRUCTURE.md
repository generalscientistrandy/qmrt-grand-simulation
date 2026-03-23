# QMRT: Branch Activation Structure

**Date**: December 2025  
**Status**: Awaiting user decision on fundamental structure

---

## The Key Question

> Do all branches exist simultaneously at every point,
> or do different energy regimes activate different subsets?

This determines whether QMRT is:

| Option | Structure | Character |
|--------|-----------|-----------|
| **A** | Fixed multi-field | All branches always active |
| **B** | Phase-transition hierarchical | Branches activate at thresholds |

---

## Option A: Fixed Multi-Field Theory

**Picture:**
```
At every point (x,t), the medium state is:

  Φ(x,t) = (ρ, τ, φ, θ, ...)
           ↑   ↑   ↑   ↑
           |   |   |   └── Phase coherence
           |   |   └────── Radiation/energy transport
           |   └────────── Torsion/rotation
           └────────────── Compression/density

All components always exist, just with different amplitudes.
```

**Lagrangian structure:**
```
L = L_ρ(ρ, ∂ρ) + L_τ(τ, ∂τ) + L_φ(φ, ∂φ) + L_θ(θ, ∂θ)
    + L_coupling(ρ, τ, φ, θ)
```

**Properties:**
- Mathematically simpler (fixed DOF count)
- All couplings always present
- Quantum effects from interference of all branches
- Like: Standard Model (all fields always exist)

**Emergence in this view:**
- Quantum behavior = small-amplitude excitations of phase branch
- Classical limit = phase branch negligible
- Black holes = all branches strongly excited

---

## Option B: Phase-Transition Hierarchical Theory

**Picture:**
```
Different energy regimes activate different branches:

LOW ENERGY (everyday matter):
  Active: ρ (compression)
  Dormant: τ, φ, θ mostly frozen

MEDIUM ENERGY (nuclear/particle):  
  Active: ρ, τ (torsion awakens)
  Dormant: φ, θ still suppressed

HIGH ENERGY (black holes, early universe):
  Active: ρ, τ, φ, θ (all branches active)
  Full medium dynamics

QUANTUM REGIME:
  Active: θ (phase coherence dominates)
  Others become background
```

**Lagrangian structure:**
```
L = L_ρ  +  Θ(E > E₁) × L_τ  +  Θ(E > E₂) × L_φ  + ...

where Θ is activation function (smooth or sharp threshold)
```

**Properties:**
- Richer phase structure
- Natural scale hierarchy
- Different physics at different energies
- Like: Symmetry breaking in particle physics

**Emergence in this view:**
- Quantum behavior = crossing into phase-coherent regime
- Classical limit = below activation threshold
- Black holes = maximally activated state

---

## Connection to Emergence Ladder

| Rung | Energy Scale | Active Branches (Option B) |
|------|--------------|---------------------------|
| 1. Deep medium | Lowest | ρ only |
| 2. Relativistic wave | Low | ρ + τ |
| 3. Fluctuation coherent | Medium | ρ + τ + φ |
| 4. Quantum statistical | Medium-high | ρ + τ + φ + θ |
| 5. Geometric | High | All, coarse-grained |
| 6. Spacetime | Emergent | Effective metric only |

**Option B naturally maps onto the ladder!**

---

## Physical Intuition

### Option A intuition:
"The medium is like a crystal with multiple vibration modes.
 All modes exist, we just excite different ones."

### Option B intuition:
"The medium is like water with phase transitions.
 Ice, liquid, gas have different active degrees of freedom."

---

## Mathematical Consequences

### Option A: Fixed fields
```python
# State at every point
state = {
    'rho': float,      # Always exists
    'tau': vector,     # Always exists  
    'phi': float,      # Always exists
    'theta': complex,  # Always exists
}

# Evolution: coupled PDEs for all fields
d_rho/dt = f(rho, tau, phi, theta)
d_tau/dt = g(rho, tau, phi, theta)
...
```

### Option B: Activated fields
```python
# State depends on local energy density
def get_active_fields(E_local):
    if E_local < E1:
        return ['rho']
    elif E_local < E2:
        return ['rho', 'tau']
    elif E_local < E3:
        return ['rho', 'tau', 'phi']
    else:
        return ['rho', 'tau', 'phi', 'theta']

# Evolution: only active fields evolve
for field in get_active_fields(E):
    d_field/dt = f(active_fields)
```

---

## Which Fits Your Vision?

**Arguments for Option A (Fixed):**
- Simpler mathematically
- No arbitrary thresholds
- All physics always present (just at different scales)

**Arguments for Option B (Hierarchical):**
- Natural explanation for scale-dependent physics
- Matches emergence ladder
- Explains why quantum effects appear at small scales
- Explains why GR appears at large scales
- More predictive (thresholds are measurable)

---

## The Deep Question

Your answer reveals whether you see the universe as:

**A**: A multi-component medium where all structure is always present
      (like a crystal with many phonon modes)

**B**: A phase-transitioning medium where structure emerges at thresholds
      (like water with ice/liquid/gas phases)

Both are legitimate physics. Which matches your intuition about reality?
