# FUTURE BRANCH: Hamiltonian Consistency

**Status:** DEFERRED — Separate research branch  
**Prerequisite:** The dissipative model is the system we *have*  
**This document:** Outlines the path toward a conservative analogue

---

## Motivation

The current dynamical medium is explicitly dissipative:
- Wave damping: $-\gamma \dot{\phi}$
- No exact energy conservation
- Balance arises from production ≈ dissipation

For fundamental physics, we may want a **conservative** formulation where:
- A Hamiltonian $H$ exists
- $\frac{dH}{dt} = 0$ exactly
- Phase space has symplectic structure

This document sketches three approaches.

---

## Branch 1: Conservative Analogue

### Approach
Remove dissipation and construct a purely Hamiltonian system.

### Extended Phase Space
Promote $\tau$ to a dynamical field with conjugate momentum $\pi_\tau$:

$$H[\phi, \pi_\phi, \tau, \pi_\tau] = \int \left[ \frac{\pi_\phi^2}{2} + \frac{c(\tau)^2}{2}|\nabla\phi|^2 + \frac{\pi_\tau^2}{2m_\tau} + V(\tau) + V_{int}(\tau, \rho) \right] dx$$

### Hamilton's Equations
$$\dot{\phi} = \frac{\delta H}{\delta \pi_\phi} = \pi_\phi$$

$$\dot{\pi}_\phi = -\frac{\delta H}{\delta \phi} = c(\tau)^2 \nabla^2 \phi - \frac{\partial V_{int}}{\partial \phi}$$

$$\dot{\tau} = \frac{\delta H}{\delta \pi_\tau} = \frac{\pi_\tau}{m_\tau}$$

$$\dot{\pi}_\tau = -\frac{\delta H}{\delta \tau} = -\frac{c_0^2 \tau}{\tau_0^2}|\nabla\phi|^2 - V'(\tau) - \frac{\partial V_{int}}{\partial \tau}$$

### Challenge
- The current relaxation term $-\lambda(\tau - \tau_{eq})$ is **not** derivable from a potential when $\tau_{eq}$ depends on $\rho = \phi^2 + \dot{\phi}^2$
- Need to either: (a) make $\tau_{eq}$ constant, or (b) introduce auxiliary fields

### Expected Outcome
A formally conservative system that may lack the key physics (lensing, attraction) unless carefully tuned.

---

## Branch 2: Closed-System Limit

### Approach
Take $\lambda \to \infty$ so that $\tau = \tau_{eq}(\rho)$ instantaneously (algebraic constraint).

### Resulting System
$$\frac{\partial^2 \phi}{\partial t^2} = c(\tau_{eq}(\rho))^2 \nabla^2 \phi$$

This is a **nonlinear wave equation** with state-dependent speed.

### Energy Functional
$$E = \int \left[ \frac{1}{2}\dot{\phi}^2 + \frac{1}{2}c(\tau_{eq})^2 |\nabla\phi|^2 \right] dx$$

### Conservation Check
$$\frac{dE}{dt} = \int \left[ \dot{\phi}\ddot{\phi} + c \frac{dc}{d\rho}\frac{d\rho}{dt}|\nabla\phi|^2 + c^2 \nabla\phi \cdot \nabla\dot{\phi} \right] dx$$

The middle term involves $\frac{d\rho}{dt} = 2\phi\dot{\phi} + 2\dot{\phi}\ddot{\phi}$, which couples back through $\ddot{\phi}$. This is generically **not zero**.

### Conclusion
Even the closed-system limit is not automatically conservative. Energy conservation requires specific functional forms of $c(\rho)$.

---

## Branch 3: Fundamental Completion

### Philosophy
The dissipation in the current model may be **emergent** from a more fundamental conservative theory, analogous to:
- Friction from microscopic reversible collisions
- Heat conduction from phonon dynamics
- Viscosity from molecular momentum transfer

### Hypothesis
There exists a "microscopic" theory with:
- Additional degrees of freedom (medium microstructure)
- Exact Hamiltonian dynamics
- Coarse-graining produces the effective dissipative equations

### Possible Structures

**Option A: Stochastic Medium**
- Add noise terms representing unresolved microscopic fluctuations
- The combination noise + deterministic = effective dissipation (fluctuation-dissipation theorem)

**Option B: Discrete Substructure**
- Replace continuum $\tau$ with a lattice of coupled oscillators
- Each oscillator has Hamiltonian dynamics
- Coarse-grained average $\langle \tau \rangle$ obeys relaxation dynamics

**Option C: Higher-Dimensional Embedding**
- Embed 2D medium in higher-dimensional space
- "Dissipation" is energy flow into unobserved dimensions
- Full system is conservative; projected system appears dissipative

### Research Program
1. Construct explicit microscopic models
2. Derive effective equations via coarse-graining
3. Verify the macroscopic predictions match current simulations
4. Identify observable signatures of underlying conservative dynamics

---

## Decision Framework

| Question | If Yes → | If No → |
|----------|----------|---------|
| Does the dissipative model match observations? | Keep it; Hamiltonian is optional | Fix dissipative model first |
| Is energy conservation physically required? | Pursue Branches 1-3 | Dissipative model is final |
| Are there quantum gravity connections? | Likely need Hamiltonian | Effective theory suffices |

---

## Current Status

**The dissipative model is the system we have.**

It:
- ✓ Produces lensing, attraction, causal cones
- ✓ Exhibits finite universal self-balance
- ✓ Has a well-defined balance manifold attractor
- ✗ Does not conserve energy exactly
- ✗ Has no global Lyapunov functional

The Hamiltonian branches are **future research**, not required for the current book chapter.

---

## References for Future Work

1. **Non-equilibrium thermodynamics:** Prigogine, Kondepudi — for NESS formalism
2. **Hamiltonian field theory:** Goldstein Ch. 13 — for canonical formulation
3. **Emergent dissipation:** Zwanzig projection — for coarse-graining methods
4. **Active matter:** Marchetti et al. (2013) — for driven-dissipative systems in physics

---

*Document created: December 2025*  
*Status: DEFERRED — Awaiting completion of dissipative model analysis*
