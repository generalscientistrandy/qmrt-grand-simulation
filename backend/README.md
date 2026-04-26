# QMRT Substrate Lab Simulator

A physics simulation environment for exploring **Quark Medium Relativity Theory (QMRT)** and deriving self-sustaining topological organization mechanisms.

## Overview

This simulator implements a Branch-Compositional Architecture testing multiple interacting mechanisms:
- **Geometry**: Spatial coupling field (interior/exterior)
- **Channel**: Energy binding and protection
- **Remnant**: Topological memory
- **τ (Tau)**: Thermal accounting and cross-polarity coupling
- **Damping**: Energy dissipation (and potential recycling)

The goal is to identify **recovery loop networks** that enable self-sustaining topological organization without external injection.

## Quick Start

### Prerequisites

- Python 3.9+
- NumPy, SciPy

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd qmrt-simulator

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Basic Simulation

```bash
cd backend
python full_mechanism_simulator.py
```

### Run Extended Tests (Local Machine)

For longer tests not possible in the cloud environment:

```bash
# Long-horizon remnant coupling test (requires ~30 min)
python local_extended_test.py --test remnant --steps 5000 --seeds 10

# Multi-seed sweep
python local_extended_test.py --test sweep --rates 0.05,0.10,0.15,0.20 --seeds 20

# Damping → τ coupling test
python local_extended_test.py --test damping --steps 3000
```

## Project Structure

```
backend/
├── full_mechanism_simulator.py    # Core simulator (baseline)
├── local_extended_test.py         # Extended tests for local machine
├── remnant_coupling_test.py       # Short-window remnant tests
├── multi_seed_verification.py     # Multi-seed verification
│
├── qmrt_topology/
│   └── papers/
│       ├── MANUSCRIPT_TOPOLOGICAL_DUAL_SECTOR.md  # Base theory
│       ├── BRANCH_INVENTORY.md                    # Mechanism catalog
│       ├── RECOVERY_LOOP_MAP.md                   # Architecture roadmap
│       ├── TIME_SERIES_ANALYSIS.md                # Latest test results
│       └── ...
```

## Key Concepts

### Recovery Loop Map

The simulator seeks to close energy recovery loops:

```
Current (broken):
  Topology → Energy → Damping → Lost

Target (closed):
  Topology → Energy → Damping → τ → Creation → Topology
                        ↑                         │
                        └─────────────────────────┘
```

### Branch Status

| Branch | Status | Notes |
|--------|--------|-------|
| τ → Creation | VALIDATED | Works at threshold=1.001 |
| Remnant → Creation | INCONCLUSIVE | Needs long-horizon testing |
| Damping → τ | NEXT | Energy recycling path |
| Channel → τ | PLANNED | Bound energy release |

## Running Extended Tests Locally

The cloud environment has a ~300 second timeout. For proper scientific testing, run locally:

### Long-Horizon Remnant Test

```bash
python local_extended_test.py --test remnant \
    --steps 10000 \
    --seeds 20 \
    --rates 0.05,0.075,0.10,0.125,0.15 \
    --memory_fracs 0.0,0.10,0.25,0.50
```

This tests whether remnant effects emerge over longer timescales.

### Stability-Weighted Remnant (Future)

```bash
python local_extended_test.py --test stability_remnant \
    --steps 5000 \
    --stability_decay 0.99
```

Tests "create where topology survived longest" rather than "create where topology existed".

## Documentation

See `qmrt_topology/papers/` for:
- Theoretical foundations
- Test results and analysis
- Recovery loop architecture
- Branch inventory

## Contributing

This is a physics research project. Contributions should:
1. Maintain scientific rigor
2. Document all tests and results
3. Follow the Branch-Compositional Architecture principles
4. Not conflate different mechanism branches

## License

Research use. See LICENSE file.
