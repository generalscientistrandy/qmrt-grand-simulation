"""
Path B.1: Coupling Strength Sweep
=================================

MARGINAL result at coupling=0.1. Testing whether stronger coupling
produces robust phase-class emergence.

Sweep: [0.1, 0.2, 0.3]
All other parameters fixed.

SUCCESS CRITERIA (from user):
- Bimodal score > 0.55 (clearly above threshold)
- Class separation > 0.1 (minimum), trending toward 0.3
- Winding independence: correlation still low (<0.5)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from typing import Dict, List
import json


class PhaseCoupledSimulator:
    """Same simulator from B.1, parameterized for sweep."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80,
                 phase_coupling_strength: float = 0.1):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 4
        self.phase_coupling_strength = phase_coupling_strength
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.005
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
        
        # Phase-coupling mechanism
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
        
        class_indicator = np.sign(phase_diff)
        self.phase_class_field += 0.01 * topology_norm * class_indicator
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
                    })
        
        return defects


def analyze_phase_classes(defects: List[Dict]) -> Dict:
    if len(defects) < 20:
        return {'valid': False, 'n': len(defects)}
    
    phases = np.array([d['phase'] for d in defects])
    windings = np.array([d['winding'] for d in defects])
    phase_classes = np.array([d['phase_class'] for d in defects])
    
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
    }


def run_single_coupling_test(coupling_strength: float) -> Dict:
    """Run B.1 test with specific coupling strength."""
    
    print(f"\n{'='*60}")
    print(f"  COUPLING STRENGTH = {coupling_strength}")
    print(f"{'='*60}")
    
    sim = PhaseCoupledSimulator(size=48, injection_interval=80, 
                                phase_coupling_strength=coupling_strength)
    
    np.random.seed(42)  # Same seed for reproducibility
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                chirality = 1 if (i + j) % 2 == 0 else -1
                sim.inject_vortex(center + i * 4, center + j * 4, chirality)
    
    print(f"{'Step':>5} │ {'N':>4} │ {'Bimodal':>7} {'ClassSep':>8} │ "
          f"{'W-C Corr':>8} {'W-Indep':>7}")
    print("-" * 60)
    
    history = []
    
    for step in range(1500):
        sim.step()
        
        if step % 100 == 0 and step > 0:
            defects = sim.detect_defects_with_phase_class()
            m = analyze_phase_classes(defects)
            
            if m['valid']:
                print(f"{step:>5} │ {m['n']:>4} │ "
                      f"{m['bimodal_score']:>7.3f} {m['class_separation']:>8.3f} │ "
                      f"{m['winding_class_corr']:>+8.3f} {m['winding_independence']:>7.3f}")
                
                m['step'] = step
                history.append(m)
    
    # Compute averages from valid history (n > 30)
    valid = [h for h in history if h['n'] > 30]
    
    if len(valid) >= 5:
        avg_bimodal = np.mean([h['bimodal_score'] for h in valid])
        avg_class_sep = np.mean([h['class_separation'] for h in valid])
        avg_wc_corr = np.mean([h['winding_class_corr'] for h in valid])
        avg_w_indep = np.mean([h['winding_independence'] for h in valid])
        
        # Early vs late trend
        early = [h for h in valid if h['step'] < 600]
        late = [h for h in valid if h['step'] > 1000]
        
        early_sep = np.mean([h['class_separation'] for h in early]) if early else 0
        late_sep = np.mean([h['class_separation'] for h in late]) if late else 0
        
        return {
            'coupling_strength': coupling_strength,
            'valid_samples': len(valid),
            'avg_bimodal_score': float(avg_bimodal),
            'avg_class_separation': float(avg_class_sep),
            'early_class_sep': float(early_sep),
            'late_class_sep': float(late_sep),
            'avg_winding_class_corr': float(avg_wc_corr),
            'avg_winding_independence': float(avg_w_indep),
            'history': history,
        }
    else:
        return {
            'coupling_strength': coupling_strength,
            'valid_samples': len(valid),
            'error': 'Insufficient valid samples',
        }


def run_coupling_sweep():
    """Sweep coupling strengths: 0.1, 0.2, 0.3"""
    
    print("=" * 75)
    print("  PATH B.1: COUPLING STRENGTH SWEEP")
    print("=" * 75)
    print()
    print("Testing whether stronger phase-coupling produces robust phase classes.")
    print("Baseline (0.1) was MARGINAL. Testing 0.2 and 0.3.")
    print()
    print("SUCCESS CRITERIA:")
    print("  - Bimodal score > 0.55 (clearly above threshold)")
    print("  - Class separation > 0.10 (minimum)")
    print("  - Winding-class correlation still low (<0.5)")
    print()
    
    coupling_values = [0.1, 0.2, 0.3]
    results = []
    
    for coupling in coupling_values:
        result = run_single_coupling_test(coupling)
        results.append(result)
    
    # Summary table
    print()
    print("=" * 75)
    print("SWEEP SUMMARY")
    print("=" * 75)
    print()
    print(f"{'Coupling':>8} │ {'Bimodal':>8} │ {'ClassSep':>10} │ {'W-C Corr':>9} │ {'Verdict':>10}")
    print("-" * 65)
    
    for r in results:
        if 'error' not in r:
            bimodal = r['avg_bimodal_score']
            class_sep = r['avg_class_separation']
            wc_corr = r['avg_winding_class_corr']
            
            # Verdict logic
            bimodal_pass = bimodal > 0.55
            class_pass = class_sep > 0.10
            indep_pass = abs(wc_corr) < 0.5
            
            if bimodal_pass and class_pass and indep_pass:
                verdict = "PASS"
            elif bimodal_pass or class_pass:
                verdict = "MARGINAL"
            else:
                verdict = "FAIL"
            
            print(f"{r['coupling_strength']:>8.1f} │ {bimodal:>8.3f} │ {class_sep:>10.3f} │ "
                  f"{wc_corr:>+9.3f} │ {verdict:>10}")
        else:
            print(f"{r['coupling_strength']:>8.1f} │ {'---':>8} │ {'---':>10} │ "
                  f"{'---':>9} │ {'ERROR':>10}")
    
    print()
    
    # Detailed analysis
    print("=" * 75)
    print("DETAILED ANALYSIS")
    print("=" * 75)
    
    for r in results:
        if 'error' not in r:
            print(f"\nCoupling = {r['coupling_strength']}")
            print(f"  Bimodal score:    {r['avg_bimodal_score']:.3f}  "
                  f"{'✓ >0.55' if r['avg_bimodal_score'] > 0.55 else '✗ <0.55'}")
            print(f"  Class separation: {r['avg_class_separation']:.3f}  "
                  f"{'✓ >0.10' if r['avg_class_separation'] > 0.10 else '✗ <0.10'}")
            print(f"  Early→Late sep:   {r['early_class_sep']:.3f} → {r['late_class_sep']:.3f}  "
                  f"{'↑' if r['late_class_sep'] > r['early_class_sep'] else '↓'}")
            print(f"  W-C correlation:  {r['avg_winding_class_corr']:+.3f}  "
                  f"{'✓ low' if abs(r['avg_winding_class_corr']) < 0.5 else '✗ high'}")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/path_b1_coupling_sweep_results.json'
    
    # Strip history for cleaner output
    results_clean = []
    for r in results:
        r_clean = {k: v for k, v in r.items() if k != 'history'}
        results_clean.append(r_clean)
    
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'B.1_coupling_sweep',
            'coupling_values': coupling_values,
            'results': results_clean,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    results = run_coupling_sweep()
