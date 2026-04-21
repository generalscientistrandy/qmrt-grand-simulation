# QMRT Emergence Validation - Paper 1 Package

## Overview

This package contains the complete results and materials for **Paper 1: Statistical Lifecycle of Emergent Structures in a Dynamical Medium**.

## Key Finding

Structure emergence is statistically coupled to medium state through a coherent lifecycle:
- **Birth**: Enriched in high ρ (1.72×) and high |∇ρ| (1.55×) regions
- **Persistence**: Correlates with S (r=0.83), independently of ρ
- **Interaction**: Merges biased toward high |∇ρ| (1.69×)

Effects are robust to shuffle controls, stable across resolutions, and scale with coupling strength α.

## Contents

### Paper
- `PAPER1_draft.md` - Full paper draft (2-3 pages)
- `VALIDATION_REPORT.md` - Detailed results report

### Figures
- `figures/fig1_birth_histogram.png/svg` - Birth percentile histogram
- `figures/fig2_lifetime_vs_S.png/svg` - Lifetime vs S scatter
- `figures/fig3_merge_distributions.png/svg` - Merge vs gradient
- `figures/fig4_alpha_sweep.png/svg` - Coupling strength panel

### Raw Data (JSON)
- `test1_birth_vs_rho.json` - Test 1 results
- `test1_robustness_check.json` - Shuffle control & deciles
- `test2_longlived_vs_S.json` - Test 2 results
- `test3_merge_vs_gradient.json` - Test 3 results
- `partial_correlation_check.json` - S independence verification
- `alpha_sweep.json` - Coupling strength sweep
- `resolution_sanity_check.json` - Grid size validation

### Code
- `generate_figures.py` - Figure generation script

## Reproducing Results

### Run validation tests

```bash
# Test 1: Birth vs ρ
curl -X POST "http://localhost:8001/api/qmrt-sim/validate/birth-vs-rho" \
  -H "Content-Type: application/json" \
  -d '{"n_runs":20,"dimension":"2d","size":40,"steps":200}'

# Test 2: Lifetime vs S
curl -X POST "http://localhost:8001/api/qmrt-sim/validate/longlived-vs-S" \
  -H "Content-Type: application/json" \
  -d '{"n_runs":20,"dimension":"2d","size":40,"steps":250}'

# Test 3: Merge vs gradient
curl -X POST "http://localhost:8001/api/qmrt-sim/validate/merge-vs-gradient" \
  -H "Content-Type: application/json" \
  -d '{"n_runs":20,"dimension":"2d","size":40,"steps":300}'

# Robustness check
curl -X POST "http://localhost:8001/api/qmrt-sim/validate/robustness-check" \
  -H "Content-Type: application/json" \
  -d '{"n_runs":20,"dimension":"2d","size":40,"steps":200}'

# Partial correlation
curl -X POST "http://localhost:8001/api/qmrt-sim/validate/partial-correlation" \
  -H "Content-Type: application/json" \
  -d '{"n_runs":20,"dimension":"2d","size":40,"steps":250}'

# α-sweep
curl -X POST "http://localhost:8001/api/qmrt-sim/validate/alpha-sweep" \
  -H "Content-Type: application/json" \
  -d '{"alpha_values":[0.2,0.4,0.6,0.8,1.0],"n_runs_per_alpha":10}'

# Resolution check
curl -X POST "http://localhost:8001/api/qmrt-sim/validate/sanity-check" \
  -H "Content-Type: application/json" \
  -d '{"grid_sizes":[30,40,50],"n_runs":10}'
```

### Generate figures

```bash
cd /app/backend
python qmrt_topology/test_results/generate_figures.py
```

## Summary Statistics

| Test | N | Effect | p-value |
|------|---|--------|---------|
| Birth vs ρ | 1040 | 1.72× enrichment | <10⁻⁶ |
| Birth vs ∇ρ | 1040 | 1.55× enrichment | <10⁻⁶ |
| Lifetime vs S | 1280 | r=0.834, d=0.81 | <10⁻⁶ |
| Merge vs ∇ρ | 320 | 1.69× vs random | <10⁻⁶ |
| α-sweep | 5 points | Monotonic increase | — |
| Resolution | 3 sizes | Stable | — |
| 3D check | 10 runs | Same direction | — |

## Citation

> "We find strong statistical coupling between structure lifecycle events and local field variables: births are enriched in high ρ and high |∇ρ| regions; persistence correlates with S independently of ρ; and merges are biased toward high |∇ρ|. These effects are robust to shuffle controls, stable across resolutions, and increase with coupling strength α."

## License

Research materials for academic use.

---

*Generated: December 2025*
