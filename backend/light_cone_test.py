"""
Light-Cone Emergence Test
==========================

PURPOSE: Test whether regulated recovery produces emergent causal structure.

HYPOTHESIS:
  "Lorentz invariance emerges only in the dynamically regulated phase of
   the medium. Regulated recovery stabilizes the conditions for spacetime-like
   behavior."

TEST:
  Inject a localized disturbance and measure:
  - radius(T): expansion over time
  - c_eff: effective propagation speed
  - directional anisotropy: c_x vs c_y vs c_z
  - front thickness: sharpness of causal boundary
  - signal decay: how disturbance attenuates

COMPARISON:
  Mode A: Unregulated (damping_to_tau = 0)
  Mode B: Regulated Recovery v1.1 (damping_to_tau = 0.20, tau_cap = 1.8)

KEY QUESTION:
  Does regulated recovery produce a cleaner, more stable effective causal cone?

EXPECTED LORENTZ-LIKE BEHAVIOR:
  - radius ∝ T (linear expansion)
  - c_eff = Δradius / ΔT is constant
  - c_x ≈ c_y ≈ c_z (isotropic)
  - Clean front (not smeared)
"""

import numpy as np
from scipy.ndimage import label
from typing import Dict, List, Tuple
import time
import json


class LightConeSimulator:
    """
    Simulator for light-cone emergence testing.
    
    Key difference from recovery tests:
    - No initial seeded defects
    - Inject single localized disturbance
    - Track disturbance propagation radius
    """
    
    def __init__(self, size: int = 48, dt: float = 0.08,
                 damping_to_tau: float = 0.0,
                 tau_cap: float = 3.0):
        
        self.size = size
        self.dt = dt
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        
        self.T = 0.0
        self.step_count = 0
        
        # Initialize field at rest
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0  # Base wave speed squared
        self.gamma = 0.007
        
        self.channel = np.zeros((size, size, size))
        
        # No coupling gradient for cleaner test
        self.coupling = np.ones((size, size, size)) * 0.3
        
        # Disturbance tracking
        self.disturbance_center = None
        self.radius_history = []
        self.energy_history = []
        
    def inject_disturbance(self, cx: int = None, cy: int = None, cz: int = None,
                           amplitude: float = 0.5, width: float = 3.0):
        """
        Inject a localized Gaussian disturbance at the center.
        This creates an initial "event" that should propagate outward.
        """
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
        
        # Gaussian disturbance in velocity (impulse)
        disturbance = amplitude * np.exp(-r_sq / (2 * width**2))
        
        self.psi_r_dot += disturbance
        self.psi_i_dot += disturbance * 0.5  # Slight phase kick
        
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
        
        # Wave propagation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        return float(np.mean(energy))
    
    def compute_disturbance_radius(self, threshold: float = 0.01) -> Tuple[float, Dict]:
        """
        Compute the radius of the disturbance front.
        
        Returns the radius where the energy deviation from background
        exceeds the threshold.
        """
        if self.disturbance_center is None:
            return 0, {}
        
        cx, cy, cz = self.disturbance_center
        
        # Energy deviation from mean
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        deviation = np.abs(energy - np.mean(energy))
        
        # Distance from center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
        
        # Find radius where deviation exceeds threshold
        disturbed = deviation > threshold
        if np.any(disturbed):
            radius = float(np.max(r[disturbed]))
        else:
            radius = 0.0
        
        # Compute directional radii for anisotropy check
        # X direction
        x_slice = deviation[cx, cy, :]
        x_disturbed = x_slice > threshold
        r_x = float(np.max(np.abs(np.arange(self.size) - cz)[x_disturbed])) if np.any(x_disturbed) else 0
        
        # Y direction
        y_slice = deviation[cx, :, cz]
        y_disturbed = y_slice > threshold
        r_y = float(np.max(np.abs(np.arange(self.size) - cy)[y_disturbed])) if np.any(y_disturbed) else 0
        
        # Z direction  
        z_slice = deviation[:, cy, cz]
        z_disturbed = z_slice > threshold
        r_z = float(np.max(np.abs(np.arange(self.size) - cx)[z_disturbed])) if np.any(z_disturbed) else 0
        
        # Front energy (energy at the front)
        front_mask = (r > radius * 0.8) & (r < radius * 1.0) & disturbed
        front_energy = float(np.mean(deviation[front_mask])) if np.any(front_mask) else 0
        
        return radius, {
            'r_x': r_x,
            'r_y': r_y,
            'r_z': r_z,
            'front_energy': front_energy,
            'max_deviation': float(np.max(deviation))
        }
    
    def get_snapshot(self) -> Dict:
        radius, directional = self.compute_disturbance_radius()
        
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
            'energy_mean': float(np.mean(self.psi_r**2 + self.psi_i**2))
        }


def run_light_cone_test(damping_to_tau: float, tau_cap: float, 
                        T_max: float = 20.0, measure_every: int = 10) -> List[Dict]:
    """
    Run light-cone emergence test.
    
    Args:
        damping_to_tau: 0.0 for unregulated, 0.20 for v1.1
        tau_cap: 3.0 for unregulated, 1.8 for v1.1
        T_max: Maximum simulation time
        measure_every: Steps between measurements
    """
    sim = LightConeSimulator(
        size=48, dt=0.08,
        damping_to_tau=damping_to_tau,
        tau_cap=tau_cap
    )
    
    # Inject disturbance at center
    sim.inject_disturbance(amplitude=0.5, width=3.0)
    
    history = []
    
    while sim.T < T_max:
        sim.step()
        
        if sim.step_count % measure_every == 0:
            snapshot = sim.get_snapshot()
            history.append(snapshot)
    
    return history


def analyze_light_cone(history: List[Dict]) -> Dict:
    """Analyze light-cone properties from history."""
    
    if len(history) < 2:
        return {'error': 'insufficient data'}
    
    T_vals = [h['T'] for h in history]
    r_vals = [h['radius'] for h in history]
    
    # Compute effective speed c_eff = dr/dT
    # Use linear regression on the growth phase
    T_arr = np.array(T_vals[2:])  # Skip initial transient
    r_arr = np.array(r_vals[2:])
    
    if len(T_arr) > 2 and np.std(T_arr) > 0:
        # Linear fit: r = c_eff * T + r0
        coeffs = np.polyfit(T_arr, r_arr, 1)
        c_eff = coeffs[0]
        r0 = coeffs[1]
        
        # Compute fit quality
        r_pred = c_eff * T_arr + r0
        residuals = r_arr - r_pred
        r_squared = 1 - np.var(residuals) / np.var(r_arr) if np.var(r_arr) > 0 else 0
    else:
        c_eff = 0
        r0 = 0
        r_squared = 0
    
    # Compute anisotropy: variation in directional speeds
    r_x_vals = [h['r_x'] for h in history[2:]]
    r_y_vals = [h['r_y'] for h in history[2:]]
    r_z_vals = [h['r_z'] for h in history[2:]]
    
    # Directional speeds
    if len(T_arr) > 2:
        c_x = np.polyfit(T_arr, np.array(r_x_vals), 1)[0]
        c_y = np.polyfit(T_arr, np.array(r_y_vals), 1)[0]
        c_z = np.polyfit(T_arr, np.array(r_z_vals), 1)[0]
        
        c_mean = (c_x + c_y + c_z) / 3
        anisotropy = np.std([c_x, c_y, c_z]) / c_mean if c_mean > 0 else 0
    else:
        c_x, c_y, c_z = 0, 0, 0
        anisotropy = 0
    
    # Front energy decay
    front_energies = [h['front_energy'] for h in history]
    if len(front_energies) > 2:
        energy_decay_rate = (front_energies[-1] - front_energies[2]) / (T_vals[-1] - T_vals[2]) if T_vals[-1] != T_vals[2] else 0
    else:
        energy_decay_rate = 0
    
    return {
        'c_eff': c_eff,
        'c_x': c_x,
        'c_y': c_y,
        'c_z': c_z,
        'anisotropy': anisotropy,
        'r_squared': r_squared,
        'energy_decay_rate': energy_decay_rate,
        'final_radius': r_vals[-1] if r_vals else 0,
        'final_T': T_vals[-1] if T_vals else 0
    }


def main():
    print("=" * 80)
    print("  LIGHT-CONE EMERGENCE TEST")
    print("=" * 80)
    print()
    print("Hypothesis: Regulated recovery produces emergent causal structure")
    print()
    
    # Mode A: Unregulated
    print("Mode A: Unregulated (damping=0, cap=3.0)...")
    t0 = time.time()
    history_unreg = run_light_cone_test(
        damping_to_tau=0.0, tau_cap=3.0, T_max=15.0
    )
    analysis_unreg = analyze_light_cone(history_unreg)
    print(f"  c_eff = {analysis_unreg['c_eff']:.3f}")
    print(f"  anisotropy = {analysis_unreg['anisotropy']:.3f}")
    print(f"  r² = {analysis_unreg['r_squared']:.3f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    
    # Mode B: Regulated Recovery v1.1
    print("Mode B: Regulated v1.1 (damping=0.20, cap=1.8)...")
    t0 = time.time()
    history_reg = run_light_cone_test(
        damping_to_tau=0.20, tau_cap=1.8, T_max=15.0
    )
    analysis_reg = analyze_light_cone(history_reg)
    print(f"  c_eff = {analysis_reg['c_eff']:.3f}")
    print(f"  anisotropy = {analysis_reg['anisotropy']:.3f}")
    print(f"  r² = {analysis_reg['r_squared']:.3f}")
    print(f"  time: {time.time()-t0:.1f}s")
    print()
    
    # Comparison
    print("=" * 80)
    print("  COMPARISON")
    print("=" * 80)
    print()
    
    print(f"{'Metric':>20} | {'Unregulated':>12} | {'Regulated v1.1':>14} | {'Better':>10}")
    print("-" * 65)
    
    # Effective speed
    print(f"{'c_eff':>20} | {analysis_unreg['c_eff']:>12.3f} | {analysis_reg['c_eff']:>14.3f} | {'—':>10}")
    
    # Anisotropy (lower is better = more Lorentz-like)
    better_aniso = "Reg" if analysis_reg['anisotropy'] < analysis_unreg['anisotropy'] else "Unreg"
    print(f"{'Anisotropy':>20} | {analysis_unreg['anisotropy']:>12.3f} | {analysis_reg['anisotropy']:>14.3f} | {better_aniso:>10}")
    
    # Linearity (higher r² is better = cleaner cone)
    better_linear = "Reg" if analysis_reg['r_squared'] > analysis_unreg['r_squared'] else "Unreg"
    print(f"{'Linearity (r²)':>20} | {analysis_unreg['r_squared']:>12.3f} | {analysis_reg['r_squared']:>14.3f} | {better_linear:>10}")
    
    # Directional speeds
    print(f"{'c_x':>20} | {analysis_unreg['c_x']:>12.3f} | {analysis_reg['c_x']:>14.3f} | {'—':>10}")
    print(f"{'c_y':>20} | {analysis_unreg['c_y']:>12.3f} | {analysis_reg['c_y']:>14.3f} | {'—':>10}")
    print(f"{'c_z':>20} | {analysis_unreg['c_z']:>12.3f} | {analysis_reg['c_z']:>14.3f} | {'—':>10}")
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    if analysis_reg['anisotropy'] < analysis_unreg['anisotropy'] and analysis_reg['r_squared'] > analysis_unreg['r_squared']:
        print("✓ REGULATED RECOVERY PRODUCES CLEANER CAUSAL STRUCTURE")
        print("  Lower anisotropy + higher linearity = more Lorentz-like")
    elif analysis_reg['anisotropy'] < analysis_unreg['anisotropy']:
        print("? REGULATED RECOVERY REDUCES ANISOTROPY")
        print("  More isotropic propagation, but linearity inconclusive")
    elif analysis_reg['r_squared'] > analysis_unreg['r_squared']:
        print("? REGULATED RECOVERY IMPROVES LINEARITY")
        print("  Cleaner cone expansion, but anisotropy inconclusive")
    else:
        print("? NO CLEAR IMPROVEMENT FROM REGULATION")
        print("  May need longer simulation or different test")
    
    # Save results
    output = {
        'test': 'light_cone_emergence',
        'date': 'December 2025',
        'hypothesis': 'Regulated recovery produces emergent causal structure',
        'unregulated': {
            'config': {'damping_to_tau': 0.0, 'tau_cap': 3.0},
            'analysis': analysis_unreg,
            'history': history_unreg
        },
        'regulated_v1_1': {
            'config': {'damping_to_tau': 0.20, 'tau_cap': 1.8},
            'analysis': analysis_reg,
            'history': history_reg
        }
    }
    
    with open('/app/backend/qmrt_topology/papers/light_cone_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/light_cone_results.json")


if __name__ == "__main__":
    main()
