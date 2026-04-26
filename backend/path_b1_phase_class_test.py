"""
Path B.1: Persistent Phase-Class Test
======================================

QUESTION: Can stable phase classes emerge that are not reducible to winding sign?

MINIMAL MECHANISM:
Add a phase-coupling term that encourages nearby defects to develop
coherent phase relationships (either aligned or anti-aligned).

The simplest approach:
- In high-topology regions (where defects form), add a tendency for
  local phases to "lock" toward discrete values (0 or π relative to neighbors)
- This is the minimal intervention that could produce phase classes

FOUR DIAGNOSTICS:
1. Phase-offset distribution — does it develop peaks at 0 and π?
2. Class persistence — do peaks survive over time?
3. Winding independence — do classes cut across ± vorticity?
4. Organizational effect — do classes change scaffold behavior?

SUCCESS CRITERIA:
- Phase distribution develops bimodal structure (peaks at 0, π)
- Classes persist over 500+ steps
- Phase classes are NOT just a relabeling of winding sign
- Classes show some organizational difference

FAILURE CRITERIA:
- Phase distribution remains broad/random
- Any peaks decay rapidly
- Classes reduce to winding sign
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict
from typing import Dict, List, Tuple
import json


class PhaseCoupledSimulator:
    """
    Simulator with minimal phase-coupling mechanism.
    
    NEW MECHANISM:
    In high-topology regions, add a phase-locking tendency that encourages
    phases to cluster around discrete values relative to their neighbors.
    """
    
    def __init__(self, size: int = 48, injection_interval: int = 80,
                 phase_coupling_strength: float = 0.1):
        self.size = size
        self.injection_interval = injection_interval
        self.injection_count = 4
        self.phase_coupling_strength = phase_coupling_strength  # NEW PARAMETER
        
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
        
        # NEW: Phase class memory field
        # Tracks accumulated phase tendency (toward 0 or π relative to local average)
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
        
        # Standard dynamics
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
        
        # === NEW: PHASE-COUPLING MECHANISM ===
        # In high-topology regions, encourage phase to lock toward discrete classes
        # Compute local average phase (smoothed)
        phase_smooth = gaussian_filter(phase, sigma=2.0)
        
        # Phase difference from local average
        phase_diff = np.angle(np.exp(1j * (phase - phase_smooth)))
        
        # Quantize toward 0 or π: push phase_diff toward nearest of {0, π, -π}
        # This creates a tendency for phases to cluster into two classes
        target_diff = np.where(np.abs(phase_diff) < np.pi/2, 0, np.sign(phase_diff) * np.pi)
        phase_error = np.angle(np.exp(1j * (target_diff - phase_diff)))
        
        # Apply phase correction only in high-topology regions
        phase_correction = self.phase_coupling_strength * topology_norm * phase_error
        
        # Convert phase correction to psi adjustment
        # Rotate psi by phase_correction amount
        cos_corr = np.cos(phase_correction)
        sin_corr = np.sin(phase_correction)
        psi_r_new = self.psi_r * cos_corr - self.psi_i * sin_corr
        psi_i_new = self.psi_r * sin_corr + self.psi_i * cos_corr
        
        # Blend with original (gradual application)
        blend = 0.01 * topology_norm  # Only apply where topology is high
        self.psi_r = (1 - blend) * self.psi_r + blend * psi_r_new
        self.psi_i = (1 - blend) * self.psi_i + blend * psi_i_new
        
        # Update phase class field (memory of which class each region belongs to)
        class_indicator = np.sign(phase_diff)  # +1 or -1
        self.phase_class_field += 0.01 * topology_norm * class_indicator
        self.phase_class_field *= 0.995  # Slow decay
        self.phase_class_field = np.clip(self.phase_class_field, -1, 1)
        # === END NEW MECHANISM ===
        
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
        """
        Detect defects with:
        - position
        - winding sign (vorticity)
        - local phase
        - phase class (from phase_class_field)
        """
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
    """
    Analyze whether stable phase classes have emerged.
    
    DIAGNOSTICS:
    1. Phase-offset distribution — bimodal?
    2. Class persistence — stable values?
    3. Winding independence — classes cut across ±?
    4. Organizational correlation — any effect?
    """
    if len(defects) < 20:
        return {'valid': False, 'n': len(defects)}
    
    phases = np.array([d['phase'] for d in defects])
    windings = np.array([d['winding'] for d in defects])
    phase_classes = np.array([d['phase_class'] for d in defects])
    
    n = len(defects)
    n_pos = np.sum(windings == +1)
    n_neg = np.sum(windings == -1)
    
    # 1. Phase-offset distribution
    # Compute pairwise phase differences
    phase_diffs = []
    for i in range(min(n, 50)):
        for j in range(i+1, min(n, 50)):
            diff = np.angle(np.exp(1j * (phases[i] - phases[j])))
            phase_diffs.append(np.abs(diff))
    
    phase_diffs = np.array(phase_diffs)
    
    # Check for bimodality: fraction near 0 vs near π
    near_zero = np.sum(phase_diffs < np.pi/4) / len(phase_diffs)
    near_pi = np.sum(phase_diffs > 3*np.pi/4) / len(phase_diffs)
    bimodal_score = near_zero + near_pi  # Higher = more bimodal
    
    # 2. Phase class distribution
    # Are phase_class values clustered or spread?
    class_std = np.std(phase_classes)
    class_mean = np.mean(phase_classes)
    
    # Fraction strongly positive or strongly negative class
    strong_positive = np.sum(phase_classes > 0.3) / n
    strong_negative = np.sum(phase_classes < -0.3) / n
    class_separation = strong_positive + strong_negative
    
    # 3. Winding independence
    # Correlation between phase_class and winding
    # If classes just reproduce winding, correlation will be high
    if len(set(windings)) > 1 and len(set(phase_classes)) > 1:
        winding_class_corr, _ = pearsonr(windings, phase_classes)
    else:
        winding_class_corr = 0
    
    # Check: among + winding, are there both + and - phase classes?
    pos_winding_defects = [d for d in defects if d['winding'] == +1]
    neg_winding_defects = [d for d in defects if d['winding'] == -1]
    
    if len(pos_winding_defects) > 5:
        pos_classes = [d['phase_class'] for d in pos_winding_defects]
        pos_class_spread = np.std(pos_classes)
    else:
        pos_class_spread = 0
    
    if len(neg_winding_defects) > 5:
        neg_classes = [d['phase_class'] for d in neg_winding_defects]
        neg_class_spread = np.std(neg_classes)
    else:
        neg_class_spread = 0
    
    # Independence score: high spread within each winding = classes cut across winding
    winding_independence = (pos_class_spread + neg_class_spread) / 2
    
    return {
        'valid': True,
        'n': n,
        'n_pos_winding': n_pos,
        'n_neg_winding': n_neg,
        # Diagnostic 1: Phase distribution
        'phase_diff_near_zero': float(near_zero),
        'phase_diff_near_pi': float(near_pi),
        'bimodal_score': float(bimodal_score),
        # Diagnostic 2: Class separation
        'class_std': float(class_std),
        'strong_positive_class': float(strong_positive),
        'strong_negative_class': float(strong_negative),
        'class_separation': float(class_separation),
        # Diagnostic 3: Winding independence
        'winding_class_corr': float(winding_class_corr),
        'winding_independence': float(winding_independence),
    }


def run_phase_class_test():
    """
    Run Path B.1: Test whether stable phase classes emerge.
    """
    print("=" * 75)
    print("  PATH B.1: PERSISTENT PHASE-CLASS TEST")
    print("=" * 75)
    print()
    print("Question: Can stable phase classes emerge that are NOT reducible to")
    print("          winding sign?")
    print()
    print("Mechanism: Minimal phase-coupling in high-topology regions")
    print("Coupling strength: 0.1")
    print()
    
    sim = PhaseCoupledSimulator(size=48, injection_interval=80, 
                                phase_coupling_strength=0.1)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Initial seeding
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                chirality = 1 if (i + j) % 2 == 0 else -1
                sim.inject_vortex(center + i * 4, center + j * 4, chirality)
    
    print(f"{'Step':>5} │ {'N':>4} │ {'Bimodal':>7} {'ClassSep':>8} │ "
          f"{'W-C Corr':>8} {'W-Indep':>7}")
    print("-" * 65)
    
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
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("DIAGNOSTIC ANALYSIS")
    print("=" * 75)
    print()
    
    valid = [h for h in history if h['n'] > 30]
    
    if len(valid) >= 5:
        # Diagnostic 1: Phase distribution bimodality
        print("1. PHASE-OFFSET DISTRIBUTION")
        print("-" * 40)
        avg_bimodal = np.mean([h['bimodal_score'] for h in valid])
        avg_near_zero = np.mean([h['phase_diff_near_zero'] for h in valid])
        avg_near_pi = np.mean([h['phase_diff_near_pi'] for h in valid])
        
        print(f"   Fraction near 0: {avg_near_zero:.3f}")
        print(f"   Fraction near π: {avg_near_pi:.3f}")
        print(f"   Bimodal score:   {avg_bimodal:.3f}")
        
        if avg_bimodal > 0.5:
            print("   → BIMODAL STRUCTURE DETECTED")
            diag1_pass = True
        else:
            print("   → Distribution remains broad/random")
            diag1_pass = False
        
        print()
        
        # Diagnostic 2: Class persistence
        print("2. PHASE-CLASS SEPARATION")
        print("-" * 40)
        avg_class_sep = np.mean([h['class_separation'] for h in valid])
        avg_class_std = np.mean([h['class_std'] for h in valid])
        
        print(f"   Class separation: {avg_class_sep:.3f}")
        print(f"   Class std:        {avg_class_std:.3f}")
        
        # Check trend over time
        early = [h for h in valid if h['step'] < 600]
        late = [h for h in valid if h['step'] > 1000]
        
        if early and late:
            early_sep = np.mean([h['class_separation'] for h in early])
            late_sep = np.mean([h['class_separation'] for h in late])
            print(f"   Early separation: {early_sep:.3f}")
            print(f"   Late separation:  {late_sep:.3f}")
            
            if late_sep > early_sep:
                print("   → Classes STRENGTHENING over time")
                diag2_pass = True
            elif late_sep > 0.3:
                print("   → Classes PERSIST")
                diag2_pass = True
            else:
                print("   → Classes NOT strengthening")
                diag2_pass = False
        else:
            diag2_pass = avg_class_sep > 0.3
        
        print()
        
        # Diagnostic 3: Winding independence
        print("3. WINDING INDEPENDENCE")
        print("-" * 40)
        avg_wc_corr = np.mean([h['winding_class_corr'] for h in valid])
        avg_w_indep = np.mean([h['winding_independence'] for h in valid])
        
        print(f"   Winding-class correlation: {avg_wc_corr:+.3f}")
        print(f"   Within-winding spread:     {avg_w_indep:.3f}")
        
        if abs(avg_wc_corr) < 0.5 and avg_w_indep > 0.2:
            print("   → Phase classes CUT ACROSS winding sign")
            print("   → NEW DISTINCTION (not just relabeling)")
            diag3_pass = True
        elif abs(avg_wc_corr) > 0.7:
            print("   → Phase classes REDUCE to winding sign")
            diag3_pass = False
        else:
            print("   → Partial independence")
            diag3_pass = abs(avg_wc_corr) < 0.6
        
        print()
        print("=" * 75)
        print("B.1 VERDICT")
        print("=" * 75)
        print()
        
        n_pass = sum([diag1_pass, diag2_pass, diag3_pass])
        
        if n_pass >= 3:
            print("B.1: PASSED")
            print()
            print("Stable phase classes have emerged that are NOT reducible to")
            print("winding sign. Proceed to B.2 (Branch-Level Phase Coherence).")
            verdict = "passed"
        elif n_pass >= 2:
            print("B.1: PARTIAL")
            print()
            print(f"Passed {n_pass}/3 diagnostics. Phase classes show some structure")
            print("but may need stronger coupling or longer runs.")
            verdict = "partial"
        else:
            print("B.1: FAILED")
            print()
            print("Phase classes did not emerge or reduce to winding sign.")
            print("The topological branch remains the validated model.")
            verdict = "failed"
    else:
        verdict = "insufficient_data"
    
    # Save results (convert numpy types to native Python)
    def convert_numpy(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(v) for v in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    output_path = '/app/backend/qmrt_topology/papers/path_b1_phase_class_results.json'
    with open(output_path, 'w') as f:
        json.dump(convert_numpy({
            'test': 'B.1_persistent_phase_class',
            'mechanism': 'minimal_phase_coupling',
            'coupling_strength': 0.1,
            'history': history,
            'verdict': verdict,
        }), f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, verdict


if __name__ == "__main__":
    history, verdict = run_phase_class_test()
