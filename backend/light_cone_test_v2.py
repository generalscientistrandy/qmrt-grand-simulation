"""
Light-Cone Emergence Test v2 - With Defect-Active Medium
=========================================================

PURPOSE: Test whether regulated recovery produces emergent causal structure
in a medium that has active topological dynamics.

KEY INSIGHT: The difference between regulated and unregulated modes only
manifests when there are defects creating local energy variations that
feed back into τ.

TEST PROTOCOL:
1. Initialize medium with seeded defects (like recovery tests)
2. Let medium evolve to establish τ structure
3. Inject localized disturbance
4. Measure propagation characteristics

COMPARISON:
  Mode A: Unregulated (damping_to_tau = 0)
  Mode B: Regulated Recovery v1.1 (damping_to_tau = 0.20, tau_cap = 1.8)

KEY METRICS:
  - c_eff: effective propagation speed
  - c_eff_cv: stability of effective speed (lower = more uniform)
  - anisotropy: directional speed variation
  - r²: linearity of radius vs time
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List, Tuple
import time
import json


class DefectActiveLightConeSimulator:
    """
    Simulator for light-cone testing in defect-active medium.
    """
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 damping_to_tau: float = 0.0, tau_cap: float = 3.0,
                 seed: int = None):
        
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        
        self.T = 0.0
        self.step_count = 0
        
        # Initialize field with small fluctuations
        self.psi_r = np.random.randn(size, size, size) * 0.1 + 1.0
        self.psi_i = np.random.randn(size, size, size) * 0.05
        self.psi_r_dot = np.random.randn(size, size, size) * 0.02
        self.psi_i_dot = np.random.randn(size, size, size) * 0.02
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Standard coupling gradient
        x = np.linspace(0, 1, size)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        center_dist = np.sqrt((X-0.5)**2 + (Y-0.5)**2 + (Z-0.5)**2)
        self.coupling = 0.5 - 0.3 * center_dist
        
        # Seed initial defects
        self._seed_defects(n_defects=8)
        
        self.disturbance_center = None
        
    def _seed_defects(self, n_defects=8):
        margin = self.size // 4
        for _ in range(n_defects):
            cx = np.random.randint(margin, self.size - margin)
            cy = np.random.randint(margin, self.size - margin)
            cz = np.random.randint(margin, self.size - margin)
            
            x, y, z = np.meshgrid(
                np.arange(self.size), np.arange(self.size), np.arange(self.size),
                indexing='ij'
            )
            r = np.sqrt((x-cx)**2 + (y-cy)**2 + (z-cz)**2) + 0.1
            
            chirality = np.random.choice([-1, 1])
            theta = np.arctan2(y - cy, x - cx)
            
            amp = 1.5 * np.exp(-r**2 / 8)
            self.psi_r += amp * np.cos(chirality * theta)
            self.psi_i += amp * np.sin(chirality * theta)
    
    def inject_disturbance(self, cx: int = None, cy: int = None, cz: int = None,
                           amplitude: float = 0.5, width: float = 3.0):
        if cx is None:
            cx = self.size // 2
        if cy is None:
            cy = self.size // 2
        if cz is None:
            cz = self.size // 2
        
        self.disturbance_center = (cx, cy, cz)
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        disturbance = amplitude * np.exp(-r_sq / (2 * width**2))
        
        self.psi_r_dot += disturbance
        self.psi_i_dot += disturbance * 0.5
        
    def step(self):
        self.step_count += 1
        self.T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # Damping → τ coupling (if enabled)
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Wave propagation with τ-dependent speed
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        return float(np.mean(energy))
    
    def compute_disturbance_radius(self, threshold: float = 0.05) -> Tuple[float, Dict]:
        if self.disturbance_center is None:
            return 0, {}
        
        cx, cy, cz = self.disturbance_center
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        deviation = np.abs(energy - np.mean(energy))
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
        
        disturbed = deviation > threshold
        if np.any(disturbed):
            radius = float(np.max(r[disturbed]))
        else:
            radius = 0.0
        
        # Directional radii
        x_slice = deviation[cx, cy, :]
        x_disturbed = x_slice > threshold
        r_x = float(np.max(np.abs(np.arange(self.size) - cz)[x_disturbed])) if np.any(x_disturbed) else 0
        
        y_slice = deviation[cx, :, cz]
        y_disturbed = y_slice > threshold
        r_y = float(np.max(np.abs(np.arange(self.size) - cy)[y_disturbed])) if np.any(y_disturbed) else 0
        
        z_slice = deviation[:, cy, cz]
        z_disturbed = z_slice > threshold
        r_z = float(np.max(np.abs(np.arange(self.size) - cx)[z_disturbed])) if np.any(z_disturbed) else 0
        
        front_mask = (r > radius * 0.8) & (r < radius * 1.0) & disturbed
        front_energy = float(np.mean(deviation[front_mask])) if np.any(front_mask) else 0
        
        return radius, {
            'r_x': r_x, 'r_y': r_y, 'r_z': r_z,
            'front_energy': front_energy,
            'max_deviation': float(np.max(deviation))
        }
    
    def get_snapshot(self, threshold: float = 0.05) -> Dict:
        radius, directional = self.compute_disturbance_radius(threshold=threshold)
        
        # Compute local effective speed map
        c_eff = np.sqrt(self.c_0_sq * self.tau)
        
        return {
            'T': self.T,
            'radius': radius,
            'r_x': directional.get('r_x', 0),
            'r_y': directional.get('r_y', 0),
            'r_z': directional.get('r_z', 0),
            'front_energy': directional.get('front_energy', 0),
            'max_deviation': directional.get('max_deviation', 0),
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'tau_max': float(np.max(self.tau)),
            'c_eff_mean': float(np.mean(c_eff)),
            'c_eff_std': float(np.std(c_eff)),
            'energy_mean': float(np.mean(self.psi_r**2 + self.psi_i**2))
        }


def run_test_with_warmup(damping_to_tau: float, tau_cap: float,
                         warmup_T: float = 50.0, measure_T: float = 5.0,
                         seed: int = 42) -> Tuple[List[Dict], Dict]:
    """
    Run light-cone test with warmup phase to establish τ structure.
    
    1. Initialize with defects
    2. Run warmup to establish τ gradients
    3. Inject disturbance
    4. Measure propagation
    """
    
    sim = DefectActiveLightConeSimulator(
        size=32, dt=0.12,
        damping_to_tau=damping_to_tau,
        tau_cap=tau_cap,
        seed=seed
    )
    
    # Warmup phase - let τ structure develop
    warmup_data = {'tau_evolution': []}
    while sim.T < warmup_T:
        sim.step()
        if sim.step_count % 50 == 0:
            warmup_data['tau_evolution'].append({
                'T': sim.T,
                'tau_mean': float(np.mean(sim.tau)),
                'tau_std': float(np.std(sim.tau)),
                'tau_max': float(np.max(sim.tau))
            })
    
    warmup_data['final_tau_mean'] = float(np.mean(sim.tau))
    warmup_data['final_tau_std'] = float(np.std(sim.tau))
    warmup_data['final_tau_max'] = float(np.max(sim.tau))
    warmup_data['final_c_eff_mean'] = float(np.mean(np.sqrt(sim.c_0_sq * sim.tau)))
    warmup_data['final_c_eff_std'] = float(np.std(np.sqrt(sim.c_0_sq * sim.tau)))
    
    # Record τ structure before injection
    tau_before = sim.tau.copy()
    
    # Inject disturbance
    sim.inject_disturbance(amplitude=0.5, width=3.0)
    
    # Measure propagation
    history = []
    T_start = sim.T
    
    while sim.T < T_start + measure_T:
        sim.step()
        if sim.step_count % 2 == 0:
            snapshot = sim.get_snapshot(threshold=0.05)
            history.append(snapshot)
    
    return history, warmup_data


def analyze_results(history: List[Dict]) -> Dict:
    """Analyze propagation characteristics."""
    
    if len(history) < 3:
        return {'error': 'insufficient data'}
    
    T_vals = np.array([h['T'] for h in history])
    r_vals = np.array([h['radius'] for h in history])
    
    # Skip first few measurements (initial transient)
    T_arr = T_vals[2:]
    r_arr = r_vals[2:]
    
    # Linear fit for c_eff
    if len(T_arr) > 2 and np.std(r_arr) > 0:
        coeffs = np.polyfit(T_arr - T_arr[0], r_arr, 1)
        c_eff = coeffs[0]
        r0 = coeffs[1]
        
        r_pred = c_eff * (T_arr - T_arr[0]) + r0
        residuals = r_arr - r_pred
        r_squared = 1 - np.var(residuals) / np.var(r_arr) if np.var(r_arr) > 0 else 0
    else:
        c_eff, r0, r_squared = 0, 0, 0
    
    # Directional speeds
    r_x_vals = np.array([h['r_x'] for h in history[2:]])
    r_y_vals = np.array([h['r_y'] for h in history[2:]])
    r_z_vals = np.array([h['r_z'] for h in history[2:]])
    
    if len(T_arr) > 2:
        c_x = np.polyfit(T_arr - T_arr[0], r_x_vals, 1)[0]
        c_y = np.polyfit(T_arr - T_arr[0], r_y_vals, 1)[0]
        c_z = np.polyfit(T_arr - T_arr[0], r_z_vals, 1)[0]
        
        c_mean = (c_x + c_y + c_z) / 3
        anisotropy = np.std([c_x, c_y, c_z]) / c_mean if c_mean > 0 else 0
    else:
        c_x, c_y, c_z = 0, 0, 0
        anisotropy = 0
    
    # c_eff stability (from instantaneous measurements)
    if len(r_vals) > 3:
        dr = np.diff(r_vals[2:])
        dT = np.diff(T_vals[2:])
        instant_speeds = np.abs(dr / dT)
        c_eff_cv = np.std(instant_speeds) / np.mean(instant_speeds) if np.mean(instant_speeds) > 0 else 1.0
    else:
        c_eff_cv = 1.0
    
    # Signal retention
    front_energies = [h['front_energy'] for h in history]
    if len(front_energies) > 2 and front_energies[2] > 0:
        signal_retention = front_energies[-1] / front_energies[2]
    else:
        signal_retention = 0
    
    # τ and c_eff statistics from snapshots
    tau_std_mean = np.mean([h['tau_std'] for h in history])
    c_eff_std_mean = np.mean([h['c_eff_std'] for h in history])
    
    return {
        'c_eff': c_eff,
        'c_x': c_x, 'c_y': c_y, 'c_z': c_z,
        'anisotropy': anisotropy,
        'r_squared': r_squared,
        'c_eff_cv': c_eff_cv,
        'signal_retention': signal_retention,
        'tau_heterogeneity': tau_std_mean,
        'c_eff_heterogeneity': c_eff_std_mean,
        'final_radius': r_vals[-1] if len(r_vals) > 0 else 0,
        'n_measurements': len(history)
    }


def main():
    print("=" * 80)
    print("  LIGHT-CONE EMERGENCE TEST v2 - DEFECT-ACTIVE MEDIUM")
    print("=" * 80)
    print()
    print("Hypothesis: Regulated recovery produces spatially varying τ,")
    print("            which creates an effective geometry for propagation.")
    print()
    print("Protocol:")
    print("  1. Initialize with 8 seeded defects")
    print("  2. Warmup for T=50 to establish τ structure")
    print("  3. Inject localized disturbance")
    print("  4. Measure propagation for T=5")
    print()
    
    results = {}
    
    # Mode A: Unregulated
    print("Mode A: Unregulated (damping=0, cap=3.0)...")
    t0 = time.time()
    history_unreg, warmup_unreg = run_test_with_warmup(
        damping_to_tau=0.0, tau_cap=3.0,
        warmup_T=50.0, measure_T=5.0, seed=42
    )
    analysis_unreg = analyze_results(history_unreg)
    
    print(f"  After warmup:")
    print(f"    τ_mean = {warmup_unreg['final_tau_mean']:.4f}")
    print(f"    τ_std  = {warmup_unreg['final_tau_std']:.4f}")
    print(f"    τ_max  = {warmup_unreg['final_tau_max']:.4f}")
    print(f"  Propagation:")
    print(f"    c_eff = {analysis_unreg['c_eff']:.3f}")
    print(f"    r² = {analysis_unreg['r_squared']:.3f}")
    print(f"    anisotropy = {analysis_unreg['anisotropy']:.3f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    
    results['unregulated'] = {
        'warmup': warmup_unreg,
        'analysis': analysis_unreg,
        'history': history_unreg
    }
    
    # Mode B: Regulated Recovery v1.1
    print("Mode B: Regulated v1.1 (damping=0.20, cap=1.8)...")
    t0 = time.time()
    history_reg, warmup_reg = run_test_with_warmup(
        damping_to_tau=0.20, tau_cap=1.8,
        warmup_T=50.0, measure_T=5.0, seed=42
    )
    analysis_reg = analyze_results(history_reg)
    
    print(f"  After warmup:")
    print(f"    τ_mean = {warmup_reg['final_tau_mean']:.4f}")
    print(f"    τ_std  = {warmup_reg['final_tau_std']:.4f}")
    print(f"    τ_max  = {warmup_reg['final_tau_max']:.4f}")
    print(f"  Propagation:")
    print(f"    c_eff = {analysis_reg['c_eff']:.3f}")
    print(f"    r² = {analysis_reg['r_squared']:.3f}")
    print(f"    anisotropy = {analysis_reg['anisotropy']:.3f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    
    results['regulated_v1_1'] = {
        'warmup': warmup_reg,
        'analysis': analysis_reg,
        'history': history_reg
    }
    
    # Comparison
    print("=" * 80)
    print("  COMPARISON: τ STRUCTURE")
    print("=" * 80)
    print()
    
    tau_ratio = warmup_reg['final_tau_std'] / warmup_unreg['final_tau_std'] if warmup_unreg['final_tau_std'] > 0 else float('inf')
    print(f"τ heterogeneity ratio (Reg/Unreg): {tau_ratio:.1f}×")
    print()
    
    print(f"{'Metric':>25} | {'Unregulated':>12} | {'Regulated v1.1':>14} | {'Delta':>10}")
    print("-" * 70)
    print(f"{'τ_std (after warmup)':>25} | {warmup_unreg['final_tau_std']:>12.4f} | {warmup_reg['final_tau_std']:>14.4f} | {tau_ratio:>9.1f}×")
    print(f"{'c_eff_std':>25} | {warmup_unreg['final_c_eff_std']:>12.4f} | {warmup_reg['final_c_eff_std']:>14.4f} | —")
    print()
    
    print("=" * 80)
    print("  COMPARISON: PROPAGATION CHARACTERISTICS")
    print("=" * 80)
    print()
    
    print(f"{'Metric':>25} | {'Unregulated':>12} | {'Regulated v1.1':>14} | {'Better':>10}")
    print("-" * 70)
    
    # Effective speed
    print(f"{'c_eff':>25} | {analysis_unreg['c_eff']:>12.3f} | {analysis_reg['c_eff']:>14.3f} | {'—':>10}")
    
    # Linearity
    better_linear = "Reg ✓" if analysis_reg['r_squared'] > analysis_unreg['r_squared'] else "Unreg"
    print(f"{'Linearity (r²)':>25} | {analysis_unreg['r_squared']:>12.3f} | {analysis_reg['r_squared']:>14.3f} | {better_linear:>10}")
    
    # Anisotropy
    better_aniso = "Reg ✓" if analysis_reg['anisotropy'] < analysis_unreg['anisotropy'] else "Unreg"
    print(f"{'Anisotropy':>25} | {analysis_unreg['anisotropy']:>12.3f} | {analysis_reg['anisotropy']:>14.3f} | {better_aniso:>10}")
    
    # c_eff stability
    better_stab = "Reg ✓" if analysis_reg['c_eff_cv'] < analysis_unreg['c_eff_cv'] else "Unreg"
    print(f"{'c_eff stability (CV)':>25} | {analysis_unreg['c_eff_cv']:>12.3f} | {analysis_reg['c_eff_cv']:>14.3f} | {better_stab:>10}")
    
    # Signal retention
    better_signal = "Reg ✓" if analysis_reg['signal_retention'] > analysis_unreg['signal_retention'] else "Unreg"
    print(f"{'Signal retention':>25} | {analysis_unreg['signal_retention']:>12.3f} | {analysis_reg['signal_retention']:>14.3f} | {better_signal:>10}")
    
    # Directional speeds
    print(f"{'c_x':>25} | {analysis_unreg['c_x']:>12.3f} | {analysis_reg['c_x']:>14.3f} | {'—':>10}")
    print(f"{'c_y':>25} | {analysis_unreg['c_y']:>12.3f} | {analysis_reg['c_y']:>14.3f} | {'—':>10}")
    print(f"{'c_z':>25} | {analysis_unreg['c_z']:>12.3f} | {analysis_reg['c_z']:>14.3f} | {'—':>10}")
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    # Key finding: Does regulation create meaningful τ heterogeneity?
    tau_heterogeneity_significant = tau_ratio > 2.0
    
    # Score propagation metrics
    reg_wins = 0
    if analysis_reg['r_squared'] > analysis_unreg['r_squared']:
        reg_wins += 1
    if analysis_reg['anisotropy'] < analysis_unreg['anisotropy']:
        reg_wins += 1
    if analysis_reg['c_eff_cv'] < analysis_unreg['c_eff_cv']:
        reg_wins += 1
    if analysis_reg['signal_retention'] > analysis_unreg['signal_retention']:
        reg_wins += 1
    
    print(f"τ heterogeneity ratio: {tau_ratio:.1f}× {'(SIGNIFICANT)' if tau_heterogeneity_significant else '(minimal)'}")
    print(f"Propagation metrics: Regulated wins {reg_wins}/4")
    print()
    
    if tau_heterogeneity_significant:
        print("KEY FINDING: Regulated recovery creates SIGNIFICANT τ heterogeneity")
        print("  → Spatially varying wave speed = effective geometry")
        
        if reg_wins >= 2:
            verdict = "PROMISING"
            print()
            print("✓ REGULATED RECOVERY SHOWS PROMISE FOR EMERGENT LORENTZ")
            print("  - Creates meaningful τ structure")
            print("  - Shows improved propagation characteristics")
            print("  - Recommend: Proceed with isotropy and dispersion tests")
        else:
            verdict = "PARTIAL"
            print()
            print("? τ STRUCTURE EXISTS BUT PROPAGATION IMPROVEMENT UNCLEAR")
            print("  - Regulated recovery creates τ gradients")
            print("  - Propagation metrics mixed")
            print("  - May need larger grid or longer measurement window")
    else:
        if reg_wins >= 3:
            verdict = "PASS_NO_TAU"
            print("? PROPAGATION IMPROVED BUT τ STRUCTURE MINIMAL")
        else:
            verdict = "INCONCLUSIVE"
            print("✗ NO CLEAR EFFECT FROM REGULATION")
            print("  - τ heterogeneity minimal")
            print("  - Propagation metrics not improved")
    
    # Save results
    output = {
        'test': 'light_cone_emergence_v2',
        'date': 'December 2025',
        'hypothesis': 'Regulated recovery creates effective geometry via τ heterogeneity',
        'config': {
            'size': 32, 'dt': 0.12,
            'warmup_T': 50.0, 'measure_T': 5.0,
            'seed': 42
        },
        'verdict': verdict,
        'tau_heterogeneity_ratio': tau_ratio,
        'propagation_score': f'{reg_wins}/4',
        'unregulated': results['unregulated'],
        'regulated_v1_1': results['regulated_v1_1']
    }
    
    with open('/app/backend/qmrt_topology/papers/LIGHT_CONE_V2_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2, default=lambda x: float(x) if isinstance(x, np.floating) else x)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/LIGHT_CONE_V2_RESULTS.json")


if __name__ == "__main__":
    main()
