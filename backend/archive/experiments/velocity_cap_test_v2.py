"""
Moving Structure / Velocity Cap Test v2
=======================================

REVISED APPROACH: Track energy flux and propagation speed rather than
structure position. Wave packets in the QMRT medium disperse, so we
measure the GROUP VELOCITY of energy transport instead.

METHODOLOGY:
1. Inject a localized perturbation at center with initial momentum
2. Track the energy flux (current density) in each direction
3. Measure the effective propagation speed of the energy front
4. Compare to the theoretical maximum c_eff = sqrt(c_0^2 * tau)

KEY PHYSICS QUESTION:
- Does energy propagation speed saturate at c_eff?
- Does boosting beyond c_eff cause deformation/decay?

BASELINE: Regulated Recovery v1.1 (tau_cap=1.8, damping_to_tau=0.20, dt=0.12, size=32)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class EnergyPropagationSimulator:
    """Simulator focused on energy flux and propagation speed."""
    
    def __init__(self, size: int = 32, dt: float = 0.12, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.T = 0.0
        self.step_count = 0
        
        # Regulated Recovery v1.1 configuration
        self.damping_to_tau = 0.20
        self.tau_cap = 1.8
        
        # Wave field - initialized flat
        self.psi_r = np.ones((size, size, size)) * 1.0
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Medium field
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Theoretical max speed
        self.c_eff_max = np.sqrt(self.c_0_sq * self.tau_cap)  # ~2.68
        
    def inject_wave_packet(self, center: Tuple[int, int, int], 
                           k_dir: np.ndarray, k_magnitude: float,
                           sigma: float = 4.0, amplitude: float = 0.5):
        """
        Inject a plane-wave packet: A * exp(-r^2/2σ^2) * exp(i k·r)
        
        This creates a wave packet with well-defined group velocity ~c_eff * k_hat
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Gaussian envelope
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        envelope = amplitude * np.exp(-r_sq / (2 * sigma**2))
        
        # Wave vector
        k_dir = k_dir / (np.linalg.norm(k_dir) + 1e-10)
        k = k_magnitude * k_dir
        
        # Phase: k · (r - center)
        phase = k[0] * (x - cx) + k[1] * (y - cy) + k[2] * (z - cz)
        
        # Complex wave packet
        self.psi_r += envelope * np.cos(phase)
        self.psi_i += envelope * np.sin(phase)
        
        # Initial momentum from group velocity
        # For wave equation, group velocity ~ c_eff * k_hat
        # psi_dot ~ i * omega * psi, where omega = c_eff * |k|
        c_eff = np.sqrt(self.c_0_sq)  # At tau=1
        omega = c_eff * k_magnitude
        
        # Time derivative: d/dt(A*exp(i(k·r - ωt))) = -iω * psi
        # So psi_r_dot = omega * psi_i, psi_i_dot = -omega * psi_r
        self.psi_r_dot += omega * envelope * np.sin(phase)
        self.psi_i_dot += -omega * envelope * np.cos(phase)
        
    def step(self):
        """Advance simulation by one timestep."""
        self.step_count += 1
        self.T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # τ dynamics
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        if self.damping_to_tau > 0:
            self.tau += self.damping_to_tau * damped_energy
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def compute_energy_flux(self) -> Dict:
        """
        Compute energy current density J = ψ* ∂ψ/∂t (complex) or equivalently
        J_i = ψ_r * ∂ψ_r/∂x_i + ψ_i * ∂ψ_i/∂x_i for gradient-based flux
        
        Returns mean flux in each direction.
        """
        # Gradient in each direction
        grad_r_x = np.roll(self.psi_r, -1, axis=0) - self.psi_r
        grad_r_y = np.roll(self.psi_r, -1, axis=1) - self.psi_r
        grad_r_z = np.roll(self.psi_r, -1, axis=2) - self.psi_r
        
        grad_i_x = np.roll(self.psi_i, -1, axis=0) - self.psi_i
        grad_i_y = np.roll(self.psi_i, -1, axis=1) - self.psi_i
        grad_i_z = np.roll(self.psi_i, -1, axis=2) - self.psi_i
        
        # Energy flux: J_i = -Im(ψ* ∂ψ/∂x_i) ~ ψ_r * ∂ψ_i/∂x_i - ψ_i * ∂ψ_r/∂x_i
        J_x = self.psi_r * grad_i_x - self.psi_i * grad_r_x
        J_y = self.psi_r * grad_i_y - self.psi_i * grad_r_y
        J_z = self.psi_r * grad_i_z - self.psi_i * grad_r_z
        
        return {
            'J_x': float(np.mean(J_x)),
            'J_y': float(np.mean(J_y)),
            'J_z': float(np.mean(J_z)),
            'J_magnitude': float(np.sqrt(np.mean(J_x)**2 + np.mean(J_y)**2 + np.mean(J_z)**2)),
            'total_energy': float(np.mean(self.psi_r**2 + self.psi_i**2 + 
                                          0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2))),
        }
    
    def compute_radial_energy_profile(self, center: Tuple[int, int, int]) -> Dict:
        """
        Compute energy as a function of distance from injection point.
        This shows how far the energy front has propagated.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Distance from center (with periodic boundary handling)
        dx = np.minimum(np.abs(x - cx), self.size - np.abs(x - cx))
        dy = np.minimum(np.abs(y - cy), self.size - np.abs(y - cy))
        dz = np.minimum(np.abs(z - cz), self.size - np.abs(z - cz))
        r = np.sqrt(dx**2 + dy**2 + dz**2)
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Bin by radius
        r_bins = np.linspace(0, self.size/2, 16)
        r_centers = 0.5 * (r_bins[:-1] + r_bins[1:])
        energy_profile = []
        
        for i in range(len(r_bins) - 1):
            mask = (r >= r_bins[i]) & (r < r_bins[i+1])
            if np.any(mask):
                energy_profile.append(float(np.mean(energy[mask])))
            else:
                energy_profile.append(0.0)
        
        # Find the "front" - where energy drops to background level
        background = energy_profile[-1] if energy_profile else 0
        front_idx = len(energy_profile) - 1
        for i, e in enumerate(energy_profile):
            if e < background * 1.5 + 1e-6:
                front_idx = i
                break
        
        front_radius = float(r_centers[front_idx]) if front_idx < len(r_centers) else float(r_centers[-1])
        
        return {
            'r_centers': [float(r) for r in r_centers],
            'energy_profile': energy_profile,
            'front_radius': front_radius,
        }
    
    def compute_directional_energy(self, center: Tuple[int, int, int], 
                                    k_dir: np.ndarray) -> Dict:
        """
        Compute how much energy has propagated in the k-direction vs opposite.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        k_dir = k_dir / (np.linalg.norm(k_dir) + 1e-10)
        
        # Signed distance along k_dir from center
        signed_dist = k_dir[0] * (x - cx) + k_dir[1] * (y - cy) + k_dir[2] * (z - cz)
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Energy in forward vs backward hemisphere
        forward_mask = signed_dist > 1
        backward_mask = signed_dist < -1
        
        E_forward = float(np.mean(energy[forward_mask])) if np.any(forward_mask) else 0.0
        E_backward = float(np.mean(energy[backward_mask])) if np.any(backward_mask) else 0.0
        
        # Asymmetry: positive means energy went forward
        asymmetry = (E_forward - E_backward) / (E_forward + E_backward + 1e-10)
        
        # Mean position of energy in k-direction
        total_energy = np.sum(energy)
        if total_energy > 1e-10:
            mean_k_position = float(np.sum(signed_dist * energy) / total_energy)
        else:
            mean_k_position = 0.0
        
        return {
            'E_forward': E_forward,
            'E_backward': E_backward,
            'asymmetry': asymmetry,
            'mean_k_position': mean_k_position,
        }


def run_propagation_test(k_magnitude: float, k_dir: np.ndarray, seed: int,
                          T_max: float = 50.0, sample_interval: float = 2.0) -> Dict:
    """
    Run a single energy propagation test.
    
    Track how the wave packet's energy propagates and whether it respects
    the theoretical maximum speed.
    """
    sim = EnergyPropagationSimulator(size=32, dt=0.12, seed=seed)
    
    center = (sim.size // 2, sim.size // 2, sim.size // 2)
    sim.inject_wave_packet(center, k_dir, k_magnitude, sigma=4.0, amplitude=0.5)
    
    # Theoretical group velocity
    c_eff = np.sqrt(sim.c_0_sq)  # ~2.0 at tau=1
    theoretical_velocity = c_eff  # Group velocity for waves
    
    # Track propagation
    times = [0.0]
    front_radii = [0.0]
    asymmetries = [0.0]
    mean_positions = [0.0]
    flux_magnitudes = [0.0]
    
    last_sample = 0.0
    while sim.T < T_max:
        sim.step()
        
        if sim.T - last_sample >= sample_interval:
            last_sample = sim.T
            
            radial = sim.compute_radial_energy_profile(center)
            directional = sim.compute_directional_energy(center, k_dir)
            flux = sim.compute_energy_flux()
            
            times.append(sim.T)
            front_radii.append(radial['front_radius'])
            asymmetries.append(directional['asymmetry'])
            mean_positions.append(directional['mean_k_position'])
            flux_magnitudes.append(flux['J_magnitude'])
    
    # Compute measured propagation speed
    if len(times) >= 2 and times[-1] > times[0]:
        # Front velocity
        front_velocity = (front_radii[-1] - front_radii[0]) / (times[-1] - times[0])
        
        # Mean position velocity (for directional propagation)
        position_velocity = (mean_positions[-1] - mean_positions[0]) / (times[-1] - times[0])
    else:
        front_velocity = 0.0
        position_velocity = 0.0
    
    # Compare to theoretical maximum
    velocity_ratio = front_velocity / (theoretical_velocity + 1e-10)
    
    return {
        'k_magnitude': float(k_magnitude),
        'k_direction': k_dir.tolist(),
        'seed': seed,
        'theoretical_velocity': float(theoretical_velocity),
        'measured_front_velocity': float(front_velocity),
        'measured_position_velocity': float(position_velocity),
        'velocity_ratio': float(velocity_ratio),
        'final_asymmetry': float(asymmetries[-1]),
        'final_front_radius': float(front_radii[-1]),
        'c_eff_max': float(sim.c_eff_max),
        'times': times,
        'front_radii': front_radii,
        'asymmetries': asymmetries,
        'mean_positions': mean_positions,
    }


def main():
    print("=" * 80)
    print("  ENERGY PROPAGATION / VELOCITY CAP TEST v2")
    print("=" * 80)
    print()
    print("Question: Does energy propagation respect a maximum speed (c_eff)?")
    print()
    print("Method: Inject wave packets with different k-magnitudes and track")
    print("        the propagation of the energy front and directional asymmetry.")
    print()
    print("Baseline: Regulated Recovery v1.1")
    print(f"Theoretical c_eff (tau=1): {np.sqrt(4.0):.3f}")
    print(f"Maximum c_eff (tau=1.8):   {np.sqrt(4.0 * 1.8):.3f}")
    print()
    
    # Configuration
    seeds = [42, 123, 456]
    k_magnitudes = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5]  # Different wavelengths
    directions = {
        'x': np.array([1.0, 0.0, 0.0]),
        'y': np.array([0.0, 1.0, 0.0]),
        'z': np.array([0.0, 0.0, 1.0]),
        'diagonal': np.array([1.0, 1.0, 1.0]) / np.sqrt(3),
    }
    
    all_results = []
    
    print("-" * 80)
    print("Running propagation tests...")
    print("-" * 80)
    
    t0_total = time.time()
    
    for k_mag in k_magnitudes:
        for dir_name, k_dir in directions.items():
            for seed in seeds:
                result = run_propagation_test(
                    k_magnitude=k_mag,
                    k_dir=k_dir,
                    seed=seed,
                    T_max=40.0,
                    sample_interval=2.0
                )
                result['direction_name'] = dir_name
                all_results.append(result)
        
        print(f"  k={k_mag:.2f} complete")
    
    print(f"\nTotal time: {time.time() - t0_total:.1f}s")
    print()
    
    # Analysis
    print("=" * 80)
    print("  RESULTS BY k-MAGNITUDE")
    print("=" * 80)
    print()
    
    # Group by k_magnitude
    by_k = {}
    for r in all_results:
        k = r['k_magnitude']
        if k not in by_k:
            by_k[k] = []
        by_k[k].append(r)
    
    print(f"{'k_mag':>6} | {'v_front':>8} | {'v_position':>10} | {'v_ratio':>8} | {'asymmetry':>10}")
    print("-" * 60)
    
    k_values = []
    v_front_values = []
    v_pos_values = []
    
    for k in sorted(by_k.keys()):
        runs = by_k[k]
        v_front = np.mean([r['measured_front_velocity'] for r in runs])
        v_pos = np.mean([r['measured_position_velocity'] for r in runs])
        v_ratio = np.mean([r['velocity_ratio'] for r in runs])
        asym = np.mean([r['final_asymmetry'] for r in runs])
        
        k_values.append(k)
        v_front_values.append(v_front)
        v_pos_values.append(v_pos)
        
        print(f"{k:>6.2f} | {v_front:>8.3f} | {v_pos:>10.3f} | {v_ratio:>8.3f} | {asym:>10.4f}")
    
    print()
    
    # Check for velocity saturation
    c_eff_theory = np.sqrt(4.0)  # ~2.0
    
    print("=" * 80)
    print("  VELOCITY CAP ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"Theoretical c_eff (tau=1): {c_eff_theory:.3f}")
    print(f"Maximum c_eff (tau=1.8):   {np.sqrt(4.0 * 1.8):.3f}")
    print()
    
    # Check if velocity saturates
    max_measured = max(v_front_values) if v_front_values else 0
    min_measured = min(v_front_values) if v_front_values else 0
    
    # Velocity ratio to c_eff
    velocity_ratios = [v / c_eff_theory for v in v_front_values]
    
    print(f"Measured front velocities: {min_measured:.3f} to {max_measured:.3f}")
    print(f"Velocity ratios to c_eff: {min(velocity_ratios):.3f} to {max(velocity_ratios):.3f}")
    print()
    
    # Check for saturation: does higher k NOT increase velocity?
    if len(v_front_values) >= 2:
        # Fit linear trend
        k_arr = np.array(k_values)
        v_arr = np.array(v_front_values)
        
        if np.std(k_arr) > 0:
            corr = np.corrcoef(k_arr, v_arr)[0, 1]
            
            # If correlation is low or velocity is capped near c_eff
            velocity_cap_detected = max(velocity_ratios) < 1.2 or corr < 0.5
        else:
            velocity_cap_detected = False
            corr = 0.0
    else:
        velocity_cap_detected = False
        corr = 0.0
    
    print(f"k-velocity correlation: {corr:.3f}")
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    if max(velocity_ratios) < 0.8:
        verdict = "STRONG_SUBLUMINAL"
        print("STRONG EVIDENCE: All propagation speeds well below c_eff")
        print("  Energy propagation is strongly subluminal in the medium.")
    elif max(velocity_ratios) < 1.1:
        verdict = "VELOCITY_CAP_CONFIRMED"
        print("VELOCITY CAP CONFIRMED: Propagation speeds bounded by c_eff")
        print("  The medium has an effective 'speed of light' limit.")
    elif corr < 0.3:
        verdict = "SATURATION_DETECTED"
        print("SATURATION DETECTED: Velocity does not increase with k")
        print("  Energy propagation saturates, suggesting a velocity cap.")
    else:
        verdict = "NO_CLEAR_CAP"
        print("NO CLEAR VELOCITY CAP: Propagation speeds vary with k")
        print("  Further investigation needed at higher k values.")
    
    print()
    print("Physical interpretation:")
    print("  In the QMRT medium, wave packets disperse but their energy")
    print("  propagation speed is governed by the local c_eff = sqrt(c_0^2 * tau).")
    print("  If velocity is capped, this establishes an analog to the")
    print("  'speed of light' limit in relativistic physics.")
    
    # Convert numpy types for JSON serialization
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    # Save results
    output = convert({
        'test': 'velocity_cap_v2',
        'date': 'December 2025',
        'baseline': 'Regulated Recovery v1.1',
        'method': 'wave_packet_propagation',
        'configuration': {
            'seeds': seeds,
            'k_magnitudes': k_magnitudes,
            'directions': list(directions.keys()),
            'T_max': 40.0,
            'grid_size': 32,
            'dt': 0.12,
        },
        'theoretical': {
            'c_eff_tau1': float(c_eff_theory),
            'c_eff_max': float(np.sqrt(4.0 * 1.8)),
        },
        'verdict': verdict,
        'summary': {
            'k_values': k_values,
            'v_front_values': v_front_values,
            'v_pos_values': v_pos_values,
            'velocity_ratios': velocity_ratios,
            'k_velocity_correlation': float(corr),
            'max_velocity_ratio': float(max(velocity_ratios)) if velocity_ratios else 0.0,
        },
        'runs': all_results,
    })
    
    with open('/app/backend/qmrt_topology/papers/VELOCITY_CAP_V2_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/VELOCITY_CAP_V2_RESULTS.json")
    
    return output


if __name__ == "__main__":
    main()
