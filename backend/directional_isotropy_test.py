"""
Directional Isotropy Test
==========================

PURPOSE: Test whether regulated recovery produces isotropic propagation
by launching identical pulses in multiple directions.

HYPOTHESIS:
  If regulated recovery creates Lorentz-like effective geometry,
  propagation speed should be direction-independent (isotropic).

DIRECTIONS TESTED:
  - Cardinal: +x, -x, +y, -y, +z, -z
  - Diagonal: xy, xz, yz, xyz

KEY METRIC:
  anisotropy_index = std(c_eff_by_direction) / mean(c_eff_by_direction)
  
PASS CRITERIA:
  - Regulated anisotropy < Unregulated anisotropy
  - Strong result: anisotropy_index < 0.10-0.15

MODES:
  A: Unregulated (damping_to_tau = 0, tau_cap = 3.0)
  B: Regulated v1.1 (damping_to_tau = 0.20, tau_cap = 1.8)
  C: Quiet medium control (no defects, no recovery)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class DirectionalIsotropySimulator:
    """
    Simulator for directional isotropy testing.
    Injects pulse at offset from center, measures arrival at opposite side.
    """
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 damping_to_tau: float = 0.0, tau_cap: float = 3.0,
                 seed: int = None, with_defects: bool = True):
        
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        self.with_defects = with_defects
        
        self.T = 0.0
        self.step_count = 0
        
        # Initialize field
        self.psi_r = np.random.randn(size, size, size) * 0.1 + 1.0
        self.psi_i = np.random.randn(size, size, size) * 0.05
        self.psi_r_dot = np.random.randn(size, size, size) * 0.02
        self.psi_i_dot = np.random.randn(size, size, size) * 0.02
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Coupling gradient
        x = np.linspace(0, 1, size)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        center_dist = np.sqrt((X-0.5)**2 + (Y-0.5)**2 + (Z-0.5)**2)
        self.coupling = 0.5 - 0.3 * center_dist
        
        # Seed defects if enabled
        if with_defects:
            self._seed_defects(n_defects=8)
        
        self.pulse_center = None
        self.pulse_direction = None
        
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
    
    def inject_directional_pulse(self, direction: str, amplitude: float = 0.5, width: float = 3.0):
        """
        Inject pulse offset from center in specified direction.
        
        Directions: '+x', '-x', '+y', '-y', '+z', '-z', 'xy', 'xz', 'yz', 'xyz'
        """
        center = self.size // 2
        offset = self.size // 4  # Start pulse 1/4 grid away from center
        
        # Compute pulse position based on direction
        direction_map = {
            '+x': (center - offset, center, center),
            '-x': (center + offset, center, center),
            '+y': (center, center - offset, center),
            '-y': (center, center + offset, center),
            '+z': (center, center, center - offset),
            '-z': (center, center, center + offset),
            'xy': (center - offset//2, center - offset//2, center),
            'xz': (center - offset//2, center, center - offset//2),
            'yz': (center, center - offset//2, center - offset//2),
            'xyz': (center - offset//3, center - offset//3, center - offset//3),
        }
        
        if direction not in direction_map:
            raise ValueError(f"Unknown direction: {direction}")
        
        cx, cy, cz = direction_map[direction]
        self.pulse_center = (cx, cy, cz)
        self.pulse_direction = direction
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        pulse = amplitude * np.exp(-r_sq / (2 * width**2))
        
        self.psi_r_dot += pulse
        self.psi_i_dot += pulse * 0.5
        
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
        
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        return float(np.mean(energy))
    
    def compute_front_radius(self, threshold: float = 0.05) -> float:
        """Compute radius of energy front from pulse center."""
        if self.pulse_center is None:
            return 0.0
        
        cx, cy, cz = self.pulse_center
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        deviation = np.abs(energy - np.mean(energy))
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
        
        disturbed = deviation > threshold
        if np.any(disturbed):
            return float(np.max(r[disturbed]))
        return 0.0


def run_single_direction(direction: str, damping_to_tau: float, tau_cap: float,
                         warmup_T: float = 50.0, measure_T: float = 4.0,
                         seed: int = 42, with_defects: bool = True) -> Dict:
    """
    Run isotropy test for a single direction.
    """
    sim = DirectionalIsotropySimulator(
        size=32, dt=0.12,
        damping_to_tau=damping_to_tau,
        tau_cap=tau_cap,
        seed=seed,
        with_defects=with_defects
    )
    
    # Warmup to establish τ structure
    while sim.T < warmup_T:
        sim.step()
    
    tau_before = {
        'mean': float(np.mean(sim.tau)),
        'std': float(np.std(sim.tau)),
        'max': float(np.max(sim.tau))
    }
    
    # Inject directional pulse
    sim.inject_directional_pulse(direction, amplitude=0.5, width=3.0)
    
    # Track front propagation
    T_start = sim.T
    history = []
    
    while sim.T < T_start + measure_T:
        sim.step()
        if sim.step_count % 2 == 0:
            radius = sim.compute_front_radius(threshold=0.05)
            history.append({'T': sim.T - T_start, 'radius': radius})
    
    # Compute effective speed from radius growth
    if len(history) > 3:
        T_arr = np.array([h['T'] for h in history[2:]])
        r_arr = np.array([h['radius'] for h in history[2:]])
        
        if np.std(r_arr) > 0:
            coeffs = np.polyfit(T_arr, r_arr, 1)
            c_eff = coeffs[0]
            
            r_pred = c_eff * T_arr + coeffs[1]
            residuals = r_arr - r_pred
            r_squared = 1 - np.var(residuals) / np.var(r_arr) if np.var(r_arr) > 0 else 0
        else:
            c_eff = 0
            r_squared = 0
    else:
        c_eff = 0
        r_squared = 0
    
    return {
        'direction': direction,
        'c_eff': c_eff,
        'r_squared': r_squared,
        'final_radius': history[-1]['radius'] if history else 0,
        'tau_before': tau_before,
        'n_measurements': len(history)
    }


def run_isotropy_test(damping_to_tau: float, tau_cap: float, 
                      mode_name: str, seed: int = 42,
                      with_defects: bool = True) -> Dict:
    """
    Run full isotropy test across all directions.
    """
    directions = ['+x', '-x', '+y', '-y', '+z', '-z', 'xy', 'xz', 'yz', 'xyz']
    
    results = {}
    c_effs = []
    
    for direction in directions:
        r = run_single_direction(
            direction, damping_to_tau, tau_cap,
            warmup_T=50.0, measure_T=4.0, seed=seed,
            with_defects=with_defects
        )
        results[direction] = r
        if r['c_eff'] > 0:  # Only count positive speeds
            c_effs.append(r['c_eff'])
    
    # Compute anisotropy index
    if len(c_effs) >= 2 and np.mean(c_effs) > 0:
        anisotropy_index = np.std(c_effs) / np.mean(c_effs)
    else:
        anisotropy_index = 1.0  # Maximum anisotropy if no valid speeds
    
    # Cardinal vs diagonal comparison
    cardinal_speeds = [results[d]['c_eff'] for d in ['+x', '-x', '+y', '-y', '+z', '-z'] if results[d]['c_eff'] > 0]
    diagonal_speeds = [results[d]['c_eff'] for d in ['xy', 'xz', 'yz', 'xyz'] if results[d]['c_eff'] > 0]
    
    cardinal_mean = np.mean(cardinal_speeds) if cardinal_speeds else 0
    diagonal_mean = np.mean(diagonal_speeds) if diagonal_speeds else 0
    
    return {
        'mode': mode_name,
        'config': {'damping_to_tau': damping_to_tau, 'tau_cap': tau_cap, 'with_defects': with_defects},
        'directions': results,
        'c_eff_mean': np.mean(c_effs) if c_effs else 0,
        'c_eff_std': np.std(c_effs) if c_effs else 0,
        'anisotropy_index': anisotropy_index,
        'cardinal_mean': cardinal_mean,
        'diagonal_mean': diagonal_mean,
        'cardinal_diagonal_ratio': cardinal_mean / diagonal_mean if diagonal_mean > 0 else float('inf'),
        'n_valid_directions': len(c_effs)
    }


def main():
    print("=" * 80)
    print("  DIRECTIONAL ISOTROPY TEST")
    print("=" * 80)
    print()
    print("Hypothesis: Regulated recovery produces isotropic propagation")
    print()
    print("Directions: +x, -x, +y, -y, +z, -z, xy, xz, yz, xyz")
    print("Key metric: anisotropy_index = std(c_eff) / mean(c_eff)")
    print()
    
    all_results = {}
    
    # Mode A: Unregulated (with defects)
    print("Mode A: Unregulated (damping=0, cap=3.0, with defects)...")
    t0 = time.time()
    results_unreg = run_isotropy_test(
        damping_to_tau=0.0, tau_cap=3.0,
        mode_name='unregulated', seed=42, with_defects=True
    )
    print(f"  anisotropy_index = {results_unreg['anisotropy_index']:.4f}")
    print(f"  c_eff_mean = {results_unreg['c_eff_mean']:.3f}")
    print(f"  cardinal/diagonal = {results_unreg['cardinal_diagonal_ratio']:.3f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    all_results['unregulated'] = results_unreg
    
    # Mode B: Regulated v1.1 (with defects)
    print("Mode B: Regulated v1.1 (damping=0.20, cap=1.8, with defects)...")
    t0 = time.time()
    results_reg = run_isotropy_test(
        damping_to_tau=0.20, tau_cap=1.8,
        mode_name='regulated_v1_1', seed=42, with_defects=True
    )
    print(f"  anisotropy_index = {results_reg['anisotropy_index']:.4f}")
    print(f"  c_eff_mean = {results_reg['c_eff_mean']:.3f}")
    print(f"  cardinal/diagonal = {results_reg['cardinal_diagonal_ratio']:.3f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    all_results['regulated_v1_1'] = results_reg
    
    # Mode C: Quiet medium control (no defects, no recovery)
    print("Mode C: Quiet medium (no defects, no recovery)...")
    t0 = time.time()
    results_quiet = run_isotropy_test(
        damping_to_tau=0.0, tau_cap=3.0,
        mode_name='quiet_medium', seed=42, with_defects=False
    )
    print(f"  anisotropy_index = {results_quiet['anisotropy_index']:.4f}")
    print(f"  c_eff_mean = {results_quiet['c_eff_mean']:.3f}")
    print(f"  cardinal/diagonal = {results_quiet['cardinal_diagonal_ratio']:.3f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    all_results['quiet_medium'] = results_quiet
    
    # Comparison
    print("=" * 80)
    print("  COMPARISON: ANISOTROPY INDEX")
    print("=" * 80)
    print()
    
    print(f"{'Mode':>20} | {'Aniso Index':>12} | {'c_eff Mean':>10} | {'Card/Diag':>10}")
    print("-" * 60)
    
    for mode_name, r in [('Unregulated', results_unreg), 
                         ('Regulated v1.1', results_reg),
                         ('Quiet Medium', results_quiet)]:
        print(f"{mode_name:>20} | {r['anisotropy_index']:>12.4f} | {r['c_eff_mean']:>10.3f} | {r['cardinal_diagonal_ratio']:>10.3f}")
    
    print()
    
    # Directional breakdown
    print("=" * 80)
    print("  DIRECTIONAL SPEEDS (c_eff)")
    print("=" * 80)
    print()
    
    directions = ['+x', '-x', '+y', '-y', '+z', '-z', 'xy', 'xz', 'yz', 'xyz']
    print(f"{'Direction':>10} | {'Unregulated':>12} | {'Regulated':>12} | {'Quiet':>12}")
    print("-" * 55)
    
    for d in directions:
        u_ceff = results_unreg['directions'][d]['c_eff']
        r_ceff = results_reg['directions'][d]['c_eff']
        q_ceff = results_quiet['directions'][d]['c_eff']
        print(f"{d:>10} | {u_ceff:>12.3f} | {r_ceff:>12.3f} | {q_ceff:>12.3f}")
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    # Compare anisotropy
    reg_better = results_reg['anisotropy_index'] < results_unreg['anisotropy_index']
    quiet_baseline = results_quiet['anisotropy_index']
    
    print(f"Anisotropy improvement (Reg vs Unreg): ", end="")
    if reg_better:
        improvement = (1 - results_reg['anisotropy_index'] / results_unreg['anisotropy_index']) * 100
        print(f"YES ({improvement:.1f}% reduction)")
    else:
        print("NO")
    
    print(f"Quiet medium baseline anisotropy: {quiet_baseline:.4f}")
    print()
    
    # Strong result check
    if results_reg['anisotropy_index'] < 0.15:
        print("✓ STRONG RESULT: Regulated anisotropy < 0.15")
        verdict = "STRONG_ISOTROPY"
    elif results_reg['anisotropy_index'] < 0.30 and reg_better:
        print("? MODERATE RESULT: Anisotropy improved but not below 0.15")
        verdict = "MODERATE_ISOTROPY"
    elif reg_better:
        print("? WEAK RESULT: Anisotropy improved but still high")
        verdict = "WEAK_ISOTROPY"
    else:
        print("✗ NO IMPROVEMENT: Regulated not more isotropic than unregulated")
        verdict = "NO_IMPROVEMENT"
    
    print()
    
    # Scientific interpretation
    if reg_better and results_reg['anisotropy_index'] < results_quiet['anisotropy_index']:
        print("KEY FINDING: Regulated recovery produces MORE isotropic propagation")
        print("             than both unregulated and quiet medium.")
        print("             This supports the emergent-geometry hypothesis.")
    elif reg_better:
        print("KEY FINDING: Regulated recovery reduces anisotropy vs unregulated,")
        print("             but quiet medium is still more isotropic.")
        print("             Effect may be from defect dynamics, not geometry.")
    
    # Save results (simplified to avoid circular reference)
    output = {
        'test': 'directional_isotropy',
        'date': 'December 2025',
        'hypothesis': 'Regulated recovery produces isotropic propagation',
        'config': {
            'size': 32, 'dt': 0.12,
            'warmup_T': 50.0, 'measure_T': 4.0,
            'seed': 42, 'directions': directions
        },
        'verdict': verdict,
        'summary': {
            'unregulated_anisotropy': float(results_unreg['anisotropy_index']),
            'regulated_anisotropy': float(results_reg['anisotropy_index']),
            'quiet_anisotropy': float(results_quiet['anisotropy_index']),
            'improvement': reg_better,
            'unreg_c_eff_mean': float(results_unreg['c_eff_mean']),
            'reg_c_eff_mean': float(results_reg['c_eff_mean']),
            'quiet_c_eff_mean': float(results_quiet['c_eff_mean'])
        },
        'directional_speeds': {
            'unregulated': {d: float(results_unreg['directions'][d]['c_eff']) for d in directions},
            'regulated': {d: float(results_reg['directions'][d]['c_eff']) for d in directions},
            'quiet': {d: float(results_quiet['directions'][d]['c_eff']) for d in directions}
        }
    }
    
    with open('/app/backend/qmrt_topology/papers/DIRECTIONAL_ISOTROPY_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/DIRECTIONAL_ISOTROPY_RESULTS.json")


if __name__ == "__main__":
    main()
