"""
τ Amplification Probe
=====================

QUESTION: Does stronger layer-0 accounting alone create layer differentiation?

If YES: One stronger accountant may suffice
If NO: Each layer needs its own auditor

TEST: Increase tau_response from 0.005 to 0.02 (4×) and re-audit.

MEASURE:
- Does τ correlation with topology increase?
- Does layer energy differentiation emerge?
- Or does it just dampen everything uniformly?
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from typing import Dict, List
import json


class TauAmplifiedSimulator:
    """Simulator with amplified τ response."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80,
                 tau_response: float = 0.005):  # Parameterized for comparison
        self.size = size
        self.injection_interval = injection_interval
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = tau_response  # VARIABLE
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
        self._create_masks()
        
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
    
    def _create_masks(self):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        
        self.interior_mask = r <= self.size * 0.25
        self.periphery_mask = r >= self.size * 0.35
    
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
    
    def compute_layer_differentiation(self) -> Dict:
        """
        Measure whether τ creates layer differentiation.
        
        KEY METRICS:
        - τ spread across topology levels
        - τ spread across spatial regions
        - Energy per topology level
        """
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        E_kinetic = 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        E_potential = 0.5 * (self.psi_r**2 + self.psi_i**2)
        E_total = E_kinetic + E_potential
        
        # Topology-based layers
        p10 = np.percentile(topology, 10)
        p50 = np.percentile(topology, 50)
        p90 = np.percentile(topology, 90)
        
        low_topo = topology < p10
        mid_topo = (topology >= p10) & (topology < p50)
        high_topo = topology >= p90
        
        return {
            # τ differentiation
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'tau_low_topo': float(np.mean(self.tau[low_topo])) if np.any(low_topo) else 1.0,
            'tau_mid_topo': float(np.mean(self.tau[mid_topo])) if np.any(mid_topo) else 1.0,
            'tau_high_topo': float(np.mean(self.tau[high_topo])) if np.any(high_topo) else 1.0,
            
            # τ spatial differentiation
            'tau_interior': float(np.mean(self.tau[self.interior_mask])),
            'tau_periphery': float(np.mean(self.tau[self.periphery_mask])),
            
            # Energy differentiation
            'E_low_topo': float(np.mean(E_total[low_topo])) if np.any(low_topo) else 0,
            'E_mid_topo': float(np.mean(E_total[mid_topo])) if np.any(mid_topo) else 0,
            'E_high_topo': float(np.mean(E_total[high_topo])) if np.any(high_topo) else 0,
            
            # Differentiation indices
            'tau_topo_spread': float(np.mean(self.tau[high_topo]) - np.mean(self.tau[low_topo])) if np.any(high_topo) and np.any(low_topo) else 0,
            'tau_spatial_spread': float(np.mean(self.tau[self.interior_mask]) - np.mean(self.tau[self.periphery_mask])),
        }


def run_tau_amplification_probe():
    """
    Compare baseline τ response vs amplified τ response.
    """
    print("=" * 75)
    print("  τ AMPLIFICATION PROBE")
    print("=" * 75)
    print()
    print("Question: Does stronger layer-0 accounting create layer differentiation?")
    print()
    print("If YES → One stronger accountant may suffice")
    print("If NO  → Each layer needs its own auditor")
    print()
    
    tau_response_values = [0.005, 0.02]  # Baseline vs 4× amplified
    results = {}
    
    for tau_resp in tau_response_values:
        print(f"\n{'='*60}")
        print(f"  τ_response = {tau_resp}")
        print(f"{'='*60}")
        
        sim = TauAmplifiedSimulator(size=48, injection_interval=80, 
                                    tau_response=tau_resp)
        
        np.random.seed(42)
        sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
        sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
        
        center = 24
        for i in range(-3, 4):
            for j in range(-3, 4):
                if abs(i) + abs(j) <= 3:
                    chirality = 1 if (i + j) % 2 == 0 else -1
                    sim.inject_vortex(center + i * 4, center + j * 4, chirality)
        
        history = []
        
        print(f"{'Step':>5} │ {'τ_std':>7} │ {'τ_low':>7} {'τ_high':>7} │ "
              f"{'Δτ_topo':>8} │ {'Δτ_space':>9}")
        print("-" * 60)
        
        for step in range(1500):
            sim.step()
            
            if step % 100 == 0 and step > 0:
                m = sim.compute_layer_differentiation()
                m['step'] = step
                history.append(m)
                
                print(f"{step:>5} │ {m['tau_std']:>7.4f} │ "
                      f"{m['tau_low_topo']:>7.4f} {m['tau_high_topo']:>7.4f} │ "
                      f"{m['tau_topo_spread']:>+8.4f} │ {m['tau_spatial_spread']:>+9.4f}")
        
        results[tau_resp] = history
    
    # === COMPARISON ===
    print()
    print("=" * 75)
    print("COMPARISON: BASELINE vs AMPLIFIED")
    print("=" * 75)
    
    baseline = results[0.005]
    amplified = results[0.02]
    
    # Average metrics
    def avg_metric(history, key):
        return np.mean([h[key] for h in history[-5:]])  # Last 5 measurements
    
    print()
    print(f"{'Metric':30} │ {'Baseline':>10} │ {'Amplified':>10} │ {'Change':>10}")
    print("-" * 70)
    
    metrics = [
        ('τ std (variance)', 'tau_std'),
        ('τ (low topology)', 'tau_low_topo'),
        ('τ (high topology)', 'tau_high_topo'),
        ('Δτ topology spread', 'tau_topo_spread'),
        ('Δτ spatial spread', 'tau_spatial_spread'),
    ]
    
    for name, key in metrics:
        base_val = avg_metric(baseline, key)
        amp_val = avg_metric(amplified, key)
        change = amp_val - base_val
        print(f"{name:30} │ {base_val:>10.4f} │ {amp_val:>10.4f} │ {change:>+10.4f}")
    
    # === VERDICT ===
    print()
    print("=" * 75)
    print("PROBE VERDICT")
    print("=" * 75)
    print()
    
    base_topo_spread = avg_metric(baseline, 'tau_topo_spread')
    amp_topo_spread = avg_metric(amplified, 'tau_topo_spread')
    
    base_tau_std = avg_metric(baseline, 'tau_std')
    amp_tau_std = avg_metric(amplified, 'tau_std')
    
    # Did amplification increase differentiation?
    spread_increase = amp_topo_spread / (base_topo_spread + 1e-10)
    std_increase = amp_tau_std / (base_tau_std + 1e-10)
    
    print(f"τ variance increase: {std_increase:.2f}×")
    print(f"τ topology spread increase: {spread_increase:.2f}×")
    print()
    
    # Key question: Does amplification create REAL differentiation?
    # We need to see if high-topology regions have meaningfully different τ
    
    if amp_topo_spread > 0.01:  # At least 1% τ difference between low and high topology
        print("RESULT: AMPLIFICATION CREATES LAYER DIFFERENTIATION")
        print()
        print("Stronger τ response produces measurable τ separation between")
        print("high and low topology regions. One stronger accountant may be")
        print("sufficient as a starting point.")
        verdict = "differentiation_achieved"
    else:
        print("RESULT: AMPLIFICATION DOES NOT CREATE LAYER DIFFERENTIATION")
        print()
        print("Even with 4× stronger τ response, topology-based τ separation")
        print("remains negligible. This strongly supports the hypothesis that:")
        print()
        print("  → Each layer needs its own auditor")
        print("  → A single global accountant cannot distinguish layers")
        print("  → Layer-specific balance rules are required")
        verdict = "multi_auditor_needed"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/tau_amplification_probe_results.json'
    
    # Convert to serializable format
    results_clean = {}
    for k, v in results.items():
        results_clean[str(k)] = v
    
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'tau_amplification_probe',
            'tau_response_values': tau_response_values,
            'results': results_clean,
            'verdict': verdict,
            'spread_increase': float(spread_increase),
            'std_increase': float(std_increase),
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return results, verdict


if __name__ == "__main__":
    results, verdict = run_tau_amplification_probe()
