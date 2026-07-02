# QMRT Energy Conservation: Model-Specific Summary

**Date**: December 2025

---

## Overview

QMRT uses two simulation models with **different energy characteristics**:

| Model | Location | Energy Conservation | Status |
|-------|----------|---------------------|--------|
| **Wave Simulator** | `full_mechanism_simulator.py`, physics tests | ✅ Natural (H = E_wave + α·Στ) | VALIDATED |
| **Mesoscopic Substrate** | `archive/experiments/mesoscopic_substrate.py` | Requires rescaling | Unchanged |

---

## Wave Simulator (Primary Physics Model)

**Used for**: All QMRT physics tests (dark matter, expansion, bullet cluster, etc.)

### Natural Hamiltonian
$$H = E_{\text{wave}} + \alpha \cdot \sum \tau$$

### Validation Results
- **Multiple seeds**: 0.0000% - 0.014% drift
- **Long-time (T=2000)**: 0.0047% drift with Yoshida 4th-order
- **Damping sweep**: 0.25% - 1.91% drift

### Integrators
| Method | Order | Typical Drift |
|--------|-------|---------------|
| Störmer-Verlet | 2nd | ~0.002% |
| **Yoshida** | **4th** | **~0.0006%** (3.5× better) |

---

## Mesoscopic Substrate (Experimental/Archived)

**Used for**: Structure detection experiments (archived)

### Why Rescaling is Required
- 4 coupled fields (ρ, T, τ, Φ) with non-conservative couplings
- Energy naturally flows between field types
- Different physics model than wave simulator

### Status
- Kept in `archive/experiments/` with original rescaling
- Not used for validated QMRT physics results
- Future work: Derive 4-field Hamiltonian if needed

---

## Key Insight

The **τ field as energy sink** mechanism applies specifically to wave-based dynamics where:
1. Wave damping (-γ·velocity) removes kinetic energy
2. Damped energy transfers to τ field
3. Total H = E_wave + α·Στ is conserved

This does NOT automatically apply to multi-field models with different coupling structures.

---

## Files

| File | Description |
|------|-------------|
| `yoshida_integrator.py` | 4th-order symplectic integrator |
| `hamiltonian_validation_test.py` | Multi-condition validation |
| `ENERGY_CONSERVATION_VALIDATION_REPORT.md` | Full validation report |
| `yoshida_integrator_comparison.png` | Verlet vs Yoshida comparison |
| `hamiltonian_validation.png` | Long-time conservation plots |

---

*All validated QMRT physics results (dark matter, expansion, bullet cluster) use the wave simulator with proven natural energy conservation.*
