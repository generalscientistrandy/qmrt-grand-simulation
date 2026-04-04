# QMRT Publication Package — Complete File Index

## How to Access Files

All files are located in `/app/backend/qmrt_topology/`. You can download them via the Emergent platform's file browser or use `git` to push to GitHub.

---

## 📄 MAIN PAPER

| File | Description | Size |
|------|-------------|------|
| `PAPER_DRAFT.md` | **Complete arXiv-ready paper** | 9.7 KB |
| `SCIENTIFIC_POSITION.md` | Honest scientific framing guide | 7.0 KB |

---

## 📊 PHASE PAPERS (Development Stages)

### Phase A: Core Physics (Topological Quantization)
| File | Description |
|------|-------------|
| `phase_a_tests.py` | Simulation code (5 tests) |
| `phase_a_results.json` | Numerical results |
| `test1_single_defect_fringe.png` | Single defect test figure |
| `test2_w_scaling.png` | W scaling test figure |
| `test3_chirality_reversal.png` | Chirality flip figure |
| `test4_no_encirclement.png` | Control test figure |
| `test5_random_vs_ordered.png` | Structure vs random figure |

### Phase B: Robustness Tests
| File | Description |
|------|-------------|
| `phase_b_tests.py` | Simulation code (5 tests) |
| `phase_b_results.json` | Numerical results |
| `test_b1_decoherence.png` | Noise robustness |
| `test_b2_em_separation.png` | EM vs QMRT |
| `test_b3_pair_cancellation.png` | Exact cancellation |
| `test_b4_deformation_invariance.png` | Topology proof |
| `test_b5_disorder.png` | Random cancellation |

### Phase C: Physical Reality Bridge
| File | Description |
|------|-------------|
| `phase_c_tests.py` | Simulation code (3 tests) |
| `phase_c_results.json` | Numerical results |
| `test_c1_worldline.png` | Spacetime formalism |
| `test_c2_cosmology.png` | Large-scale scaling |
| `test_c3_condensed_matter.png` | LC analog mapping |

### Phase 3: Propagation & Effective Metric
| File | Description |
|------|-------------|
| `phase_3_propagation.py` | Simulation code (3 tests) |
| `phase_3_results.json` | Numerical results |
| `test_p31_speed_mapping.png` | c_eff vs medium state |
| `test_p32_curvature.png` | Ray bending |
| `test_p33_geodesic.png` | Emergent geodesics |

### Multi-Defect Interference (Final Test)
| File | Description |
|------|-------------|
| `multi_defect_test.py` | Simulation code |
| `multi_defect_results.json` | Results |
| `test_multi_defect_interference.png` | Emergent channels |

---

## 🖼️ PUBLICATION FIGURES (Key 9)

| # | File | Description | For Paper Section |
|---|------|-------------|-------------------|
| 1 | `fig1_quantization.png` | φ vs W (discrete π steps) | Section 3 |
| 2 | `fig2_robustness.png` | SNR & detection curves | Section 3.2 |
| 3 | `fig3_structure_vs_random.png` | 69× signal ratio | Section 3 |
| 4 | `lc_qmrt_equivalence.png` | LC director field mapping | Section 4 |
| 5 | `fig_experimental_setup.png` | Proposed LC experiment | Section 4.2 |
| 6 | `test_p31_speed_mapping.png` | c_eff vs ρ and |τ| | Section 5 |
| 7 | `test_p32_curvature.png` | Ray bending | Section 5.3 |
| 8 | `test_p33_geodesic.png` | Wavefront & geodesics | Section 5.3 |
| 9 | `test_multi_defect_interference.png` | Emergent channels | Section 6 |

---

## 📚 THEORETICAL DERIVATIONS

| File | Content |
|------|---------|
| `stage4_paper_section.md` | Full theory derivation |
| `stage5_torsion_geometry_derivation.md` | Torsion geometry |
| `stage5b_coupling_derivation.md` | Coupling constant α = -τ/2 |
| `stage5c_continuous_limit.md` | Discrete → continuous |
| `stage5d_connection_formalization.md` | Connection 1-form |
| `stage6_3d_torsion_formalism.md` | 3D extension |
| `stage6b_particle_interpretation.md` | Particle worldlines |
| `stage7_torsion_quantization.md` | Discreteness proof |
| `qmrt_torsion_holonomy_theorem.md` | Main theorem |
| `quantization_proof.md` | Phase quantization |

---

## 🧪 EXPERIMENTAL PROPOSAL

| File | Description |
|------|-------------|
| `experimental_protocol.json` | Full LC experiment protocol |
| `experimental_consistency_note.md` | Why not already seen |
| `distinguishing_predictions.md` | Falsifiable predictions |

---

## 📈 ALL RESULT FILES

Total: 75+ JSON result files containing numerical validation data

Key results:
- `phase_a_results.json` — Core physics (5 tests)
- `phase_b_results.json` — Robustness (5 tests)
- `phase_c_results.json` — Physical bridge (3 tests)
- `phase_3_results.json` — Propagation (3 tests)
- `multi_defect_results.json` — Interference test

---

## 🖨️ HOW TO PRINT/DOWNLOAD

### Option 1: GitHub (Recommended)
1. Use "Save to GitHub" in the chat input
2. Clone the repository
3. Navigate to `backend/qmrt_topology/`

### Option 2: Direct Download
1. Use the Emergent file browser
2. Navigate to `/app/backend/qmrt_topology/`
3. Download individual files

### Option 3: Create ZIP
```bash
cd /app/backend
zip -r qmrt_publication.zip qmrt_topology/
```

---

## 📋 QUICK CHECKLIST FOR arXiv SUBMISSION

### Required Files
- [ ] `PAPER_DRAFT.md` → Convert to LaTeX
- [ ] 9 key figures (listed above)
- [ ] `experimental_protocol.json` → Appendix

### Optional Supporting Material
- [ ] Simulation code (Python files)
- [ ] Full result JSONs
- [ ] Theoretical derivations

---

## Test Summary: 17/17 PASSED

| Phase | Tests | Status |
|-------|-------|--------|
| A (Core) | 5/5 | ✅ |
| B (Robustness) | 5/5 | ✅ |
| C (Physical) | 3/3 | ✅ |
| 3 (Propagation) | 3/3 | ✅ |
| Multi-defect | 1/1 | ✅ |
| **Total** | **17/17** | **✅** |
