# QMRT Publication Package

## Topological Phase Quantization and Emergent Causal Geometry from Defect-Structured Media

**Status:** arXiv-ready | **Tests:** 17/17 passed | **Date:** April 2026

---

## Package Contents

### Main Paper
| File | Format | Description |
|------|--------|-------------|
| `QMRT_paper.tex` | LaTeX | Master source (arXiv submission format) |
| `QMRT_paper.pdf` | PDF | Compiled paper (11 pages, 9 figures) |

### Figures (9 total)
| # | File | Description |
|---|------|-------------|
| 1 | `fig1_quantization.png` | Phase vs winding number (discrete π steps) |
| 2 | `fig2_robustness.png` | SNR and detection curves |
| 3 | `fig3_structure_vs_random.png` | Ordered vs random (69× ratio) |
| 4 | `lc_qmrt_equivalence.png` | LC director field mapping |
| 5 | `fig_experimental_setup.png` | Proposed LC experiment |
| 6 | `test_p31_speed_mapping.png` | c_eff vs medium state |
| 7 | `test_p32_curvature.png` | Ray bending near defects |
| 8 | `test_p33_geodesic.png` | Wavefront and geodesics |
| 9 | `test_multi_defect_interference.png` | Emergent channels |

---

## Quick Start

### To Compile LaTeX
```bash
pdflatex QMRT_paper.tex
pdflatex QMRT_paper.tex  # Run twice for references
```

### To Submit to arXiv
1. Upload `QMRT_paper.tex` and all `.png` files
2. Select category: `cond-mat.soft` or `physics.class-ph`
3. Alternative: `gr-qc` (if emphasizing analog gravity)

---

## Key Results

### The Phase Law
$$\phi = -\pi W$$

Where W is the winding number (sum of enclosed chiralities).

### The Holonomy
$$H = (-1)^W$$

Even W → bosonic, Odd W → fermionic.

### Experimental Prediction
**90° polarization rotation per half-integer disclination** in nematic liquid crystals.

---

## Validation Summary

| Phase | Tests | Status |
|-------|-------|--------|
| A (Core) | 5/5 | ✓ |
| B (Robustness) | 5/5 | ✓ |
| C (Physical) | 3/3 | ✓ |
| 3 (Propagation) | 3/3 | ✓ |
| Multi-defect | 1/1 | ✓ |
| **Total** | **17/17** | **✓** |

---

## Recommended arXiv Categories

**Primary:** `cond-mat.soft` (Soft Condensed Matter)
- Best fit for LC analog and topological defects

**Secondary options:**
- `physics.class-ph` (Classical Physics)
- `gr-qc` (General Relativity and Quantum Cosmology) - if emphasizing analog gravity
- `cond-mat.other`

---

## Citation (Draft)

```bibtex
@article{wallace2026qmrt,
  title={Topological Phase Quantization and Emergent Causal Geometry from Defect-Structured Media},
  author={Wallace Jr., Randy},
  journal={arXiv preprint},
  year={2026}
}
```

---

## License

This research package is provided for scientific review and collaboration.
