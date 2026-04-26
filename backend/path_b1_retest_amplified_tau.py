"""
Path B.1 Retest: Phase-Class Test with Amplified τ
===================================================

CONTEXT: Path B.1 originally failed with tau_response=0.005.
Now retesting with tau_response=0.02 (amplified energy accounting).

QUESTION: Does proper energy accounting enable phase-class emergence?

HYPOTHESIS: With τ differentiating organizational regimes, phase-coupling
may now have energetic support to produce stable phase classes.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from typing import Dict, List
import json


class PhaseCoupledSimulatorV2:
    """
    Phase-coupled simulator with AMPLIFIED τ (energy accounting baseline).
    
    Key difference from original B.1:
    - tau_response = 0.02 (was 0.005)
    - τ now differentiates organizational regimes
    """
    
    def __init__(self, size: int = 48, injection_interval: int = 80,
                 phase_coupling_strength: float = 0.1):
        self.size = size
        self.injection_interval = injection_interval
        self.phase_coupling_strength = phase_coupling_strength
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02  # AMPLIFIED (was 0.005)
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        self.phase_class_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        mask_interior = r <= interior_r
        mask_exterior = r >= interior_r + 10.0
        mask_transition = ~mask_interior & ~mask_exterior
        
        coupling[mask_interior] = 0.7
        coupling[mask_exterior] = 0.2
        t = (r[mask_transition] - interior_r) / 10.0
        coupling[mask_transition] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
        return coupling
    
    def inject_vortex(self, cx: int, cy: int, chirality: int = 1):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_balanced_vortices(self):
        center = self.size // 2
        for chirality in [+1, +1, -1, -1]:
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy, chirality)
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        if self.step_count % self.injection_interval == 0:
            self.inject_balanced_vortices()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # τ dynamics with AMPLIFIED response
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        c_eff_sq = self.c_0_sq * self.tau
        
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        # Phase-coupling mechanism (same as original B.1)
        phase_smooth = gaussian_filter(phase, sigma=2.0)
        phase_diff = np.angle(np.exp(1j * (phase - phase_smooth)))
        target_diff = np.where(np.abs(phase_diff) < np.pi/2, 0, np.sign(phase_diff) * np.pi)
        phase_error = np.angle(np.exp(1j * (target_diff - phase_diff)))
        
        phase_correction = self.phase_coupling_strength * topology_norm * phase_error
        
        cos_corr = np.cos(phase_correction)
        sin_corr = np.sin(phase_correction)
        psi_r_new = self.psi_r * cos_corr - self.psi_i * sin_corr
        psi_i_new = self.psi_r * sin_corr + self.psi_i * cos_corr
        
        blend = 0.01 * topology_norm
        self.psi_r = (1 - blend) * self.psi_r + blend * psi_r_new
        self.psi_i = (1 - blend) * self.psi_i + blend * psi_i_new
        
        # Phase class field with τ-weighted accumulation
        # NEW: Weight by inverse τ (low-τ regions accumulate class memory faster)
        tau_weight = 1.0 / (self.tau + 0.1)  # Inverse τ weighting
        class_indicator = np.sign(phase_diff)
        self.phase_class_field += 0.01 * topology_norm * tau_weight * class_indicator
        self.phase_class_field *= 0.995
        self.phase_class_field = np.clip(self.phase_class_field, -1, 1)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        self.remnant_field += 0.02 * topology_norm
        self.remnant_field *= 0.999
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects_with_phase_class(self, threshold: float = 0.4) -> List[Dict]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        defects = []
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                cz = int(np.mean(coords[2]))
                
                local_vort = vorticity[cx, cy, cz]
                local_phase = phase[cx, cy, cz]
                local_phase_class = self.phase_class_field[cx, cy, cz]
                local_tau = self.tau[cx, cy, cz]
                
                winding_sign = 0
                if local_vort > 0.05:
                    winding_sign = +1
                elif local_vort < -0.05:
                    winding_sign = -1
                
                if winding_sign != 0:
                    defects.append({
                        'pos': (cx, cy, cz),
                        'winding': winding_sign,
                        'phase': float(local_phase),
                        'phase_class': float(local_phase_class),
                        'tau': float(local_tau),
                    })
        
        return defects


def analyze_phase_classes(defects: List[Dict]) -> Dict:
    if len(defects) < 20:
        return {'valid': False, 'n': len(defects)}
    
    phases = np.array([d['phase'] for d in defects])
    windings = np.array([d['winding'] for d in defects])
    phase_classes = np.array([d['phase_class'] for d in defects])
    taus = np.array([d['tau'] for d in defects])
    
    n = len(defects)
    n_pos = np.sum(windings == +1)
    n_neg = np.sum(windings == -1)
    
    # Phase-offset distribution
    phase_diffs = []
    for i in range(min(n, 50)):
        for j in range(i+1, min(n, 50)):
            diff = np.angle(np.exp(1j * (phases[i] - phases[j])))
            phase_diffs.append(np.abs(diff))
    
    phase_diffs = np.array(phase_diffs)
    near_zero = np.sum(phase_diffs < np.pi/4) / len(phase_diffs)
    near_pi = np.sum(phase_diffs > 3*np.pi/4) / len(phase_diffs)
    bimodal_score = near_zero + near_pi
    
    # Class separation
    class_std = np.std(phase_classes)
    strong_positive = np.sum(phase_classes > 0.3) / n
    strong_negative = np.sum(phase_classes < -0.3) / n
    class_separation = strong_positive + strong_negative
    
    # Winding independence
    if len(set(windings)) > 1 and len(set(phase_classes)) > 1:
        winding_class_corr, _ = pearsonr(windings, phase_classes)
    else:
        winding_class_corr = 0
    
    pos_winding_defects = [d for d in defects if d['winding'] == +1]
    neg_winding_defects = [d for d in defects if d['winding'] == -1]
    
    pos_class_spread = np.std([d['phase_class'] for d in pos_winding_defects]) if len(pos_winding_defects) > 5 else 0
    neg_class_spread = np.std([d['phase_class'] for d in neg_winding_defects]) if len(neg_winding_defects) > 5 else 0
    winding_independence = (pos_class_spread + neg_class_spread) / 2
    
    # NEW: τ-class correlation (does low τ correlate with stronger class?)
    if len(set(taus)) > 1 and len(set(phase_classes)) > 1:
        tau_class_corr, _ = pearsonr(taus, np.abs(phase_classes))
    else:
        tau_class_corr = 0
    
    return {
        'valid': True,
        'n': n,
        'n_pos_winding': int(n_pos),
        'n_neg_winding': int(n_neg),
        'phase_diff_near_zero': float(near_zero),
        'phase_diff_near_pi': float(near_pi),
        'bimodal_score': float(bimodal_score),
        'class_std': float(class_std),
        'strong_positive_class': float(strong_positive),
        'strong_negative_class': float(strong_negative),
        'class_separation': float(class_separation),
        'winding_class_corr': float(winding_class_corr),
        'winding_independence': float(winding_independence),
        'tau_class_corr': float(tau_class_corr),
        'tau_mean': float(np.mean(taus)),
    }


def run_b1_retest():
    """
    Retest B.1 with amplified τ energy accounting.
    """
    print("=" * 75)
    print("  PATH B.1 RETEST: Phase-Class with Amplified τ")
    print("=" * 75)
    print()
    print("Context: Original B.1 FAILED with tau_response=0.005")
    print("Now testing with tau_response=0.02 (amplified energy accounting)")
    print()
    print("Question: Does proper energy accounting enable phase-class emergence?")
    print()
    
    # Test both coupling strengths
    results = {}
    
    for coupling in [0.1, 0.2]:
        print(f"\n{'='*60}")
        print(f"  Phase coupling strength = {coupling}")
        print(f"{'='*60}")
        
        sim = PhaseCoupledSimulatorV2(size=48, injection_interval=80, 
                                      phase_coupling_strength=coupling)
        
        np.random.seed(42)
        sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
        
        center = 24
        for i in range(-3, 4):
            for j in range(-3, 4):
                if abs(i) + abs(j) <= 3:
                    chirality = 1 if (i + j) % 2 == 0 else -1
                    sim.inject_vortex(center + i * 4, center + j * 4, chirality)
        
        print(f"{'Step':>5} │ {'N':>4} │ {'Bimodal':>7} {'ClassSep':>8} │ "
              f"{'W-C Corr':>8} │ {'τ-Class':>7} {'τ_mean':>7}")
        print("-" * 70)
        
        history = []
        
        for step in range(1500):
            sim.step()
            
            if step % 100 == 0 and step > 0:
                defects = sim.detect_defects_with_phase_class()
                m = analyze_phase_classes(defects)
                
                if m['valid']:
                    print(f"{step:>5} │ {m['n']:>4} │ "
                          f"{m['bimodal_score']:>7.3f} {m['class_separation']:>8.3f} │ "
                          f"{m['winding_class_corr']:>+8.3f} │ "
                          f"{m['tau_class_corr']:>+7.3f} {m['tau_mean']:>7.4f}")
                    
                    m['step'] = step
                    history.append(m)
        
        results[coupling] = history
    
    # === COMPARISON WITH ORIGINAL ===
    print()
    print("=" * 75)
    print("COMPARISON: ORIGINAL B.1 vs RETEST WITH AMPLIFIED τ")
    print("=" * 75)
    print()
    
    # Original results (from previous run)
    original = {
        0.1: {'bimodal': 0.501, 'class_sep': 0.038, 'wc_corr': -0.019},
        0.2: {'bimodal': 0.500, 'class_sep': 0.039, 'wc_corr': -0.008},
    }
    
    print(f"{'Coupling':>8} │ {'Metric':>12} │ {'Original':>10} │ {'Retest':>10} │ {'Change':>10}")
    print("-" * 65)
    
    for coupling in [0.1, 0.2]:
        if results[coupling]:
            valid = [h for h in results[coupling] if h['n'] > 30]
            if valid:
                new_bimodal = np.mean([h['bimodal_score'] for h in valid])
                new_class_sep = np.mean([h['class_separation'] for h in valid])
                new_wc_corr = np.mean([h['winding_class_corr'] for h in valid])
                
                orig = original[coupling]
                
                print(f"{coupling:>8.1f} │ {'Bimodal':>12} │ {orig['bimodal']:>10.3f} │ {new_bimodal:>10.3f} │ {new_bimodal - orig['bimodal']:>+10.3f}")
                print(f"{'':>8} │ {'Class Sep':>12} │ {orig['class_sep']:>10.3f} │ {new_class_sep:>10.3f} │ {new_class_sep - orig['class_sep']:>+10.3f}")
                print(f"{'':>8} │ {'W-C Corr':>12} │ {orig['wc_corr']:>10.3f} │ {new_wc_corr:>10.3f} │ {new_wc_corr - orig['wc_corr']:>+10.3f}")
                print("-" * 65)
    
    # === VERDICT ===
    print()
    print("=" * 75)
    print("RETEST VERDICT")
    print("=" * 75)
    print()
    
    # Check if any coupling now passes
    best_result = None
    for coupling, history in results.items():
        if history:
            valid = [h for h in history if h['n'] > 30]
            if valid:
                bimodal = np.mean([h['bimodal_score'] for h in valid])
                class_sep = np.mean([h['class_separation'] for h in valid])
                
                if best_result is None or class_sep > best_result['class_sep']:
                    best_result = {
                        'coupling': coupling,
                        'bimodal': bimodal,
                        'class_sep': class_sep,
                    }
    
    if best_result:
        if best_result['bimodal'] > 0.55 and best_result['class_sep'] > 0.10:
            print("B.1 RETEST: PASSED")
            print()
            print(f"With amplified τ, phase classes now emerge:")
            print(f"  Bimodal score:    {best_result['bimodal']:.3f} (>0.55)")
            print(f"  Class separation: {best_result['class_sep']:.3f} (>0.10)")
            verdict = "passed"
        elif best_result['class_sep'] > original[0.1]['class_sep'] * 1.5:
            print("B.1 RETEST: IMPROVED BUT STILL MARGINAL")
            print()
            print(f"Amplified τ improved phase-class metrics but not to passing threshold:")
            print(f"  Bimodal score:    {best_result['bimodal']:.3f}")
            print(f"  Class separation: {best_result['class_sep']:.3f}")
            verdict = "improved"
        else:
            print("B.1 RETEST: NO SIGNIFICANT CHANGE")
            print()
            print("Amplified τ energy accounting does not enable phase-class emergence.")
            print("The phase-coupling mechanism fails independently of energy accounting.")
            verdict = "unchanged"
    else:
        verdict = "error"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/path_b1_retest_results.json'
    
    results_clean = {}
    for k, v in results.items():
        results_clean[str(k)] = v
    
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'B.1_retest_with_amplified_tau',
            'tau_response': 0.02,
            'results': results_clean,
            'verdict': verdict,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return results, verdict


if __name__ == "__main__":
    results, verdict = run_b1_retest()
