"""
Energy Audit: Layer-Resolved Energy Accounting
===============================================

QUESTION: Is the current simulator energetically flat, or is τ already
encoding the first layer of non-uniform energy accounting?

MEASUREMENTS (per timestep):
1. Total field energy (kinetic + potential-like)
2. Energy partitioned by:
   - Loop-rich vs clustering-rich regimes
   - Signed sectors (+/-)
   - Attractor interior vs periphery
3. τ-linked contributions:
   - Dispersion energy (τ-dependent wave speed)
   - τ variance as energy structure proxy
4. Bound vs free energy proxies:
   - Energy in stable structures (low τ variance)
   - Energy in dynamic regions (high τ variance)

KEY HYPOTHESIS TO TEST:
τ self-regulation may already be primitive layer-0 accounting.
If true: τ fluctuations should correlate with energy transfers.
If false: τ and energy should be largely independent.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from typing import Dict, List, Tuple
import json


class EnergyAuditSimulator:
    """
    Standard simulator with comprehensive energy instrumentation.
    """
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        
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
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
        # Attractor masks
        self._create_attractor_masks()
        
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
    
    def _create_attractor_masks(self):
        """Create spatial masks for interior/periphery analysis."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        
        self.interior_mask = r <= self.size * 0.25
        self.periphery_mask = r >= self.size * 0.35
        self.transition_mask = ~self.interior_mask & ~self.periphery_mask
    
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
        
        # τ dynamics (energy-responsive)
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
    
    def compute_energy_audit(self) -> Dict:
        """
        Comprehensive energy audit at current state.
        
        Returns partitioned energy measurements.
        """
        # === FIELD ENERGIES ===
        
        # Kinetic energy: (1/2)(ψ_dot)²
        E_kinetic = 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Potential-like energy: (1/2)|ψ|²
        E_potential = 0.5 * (self.psi_r**2 + self.psi_i**2)
        
        # Gradient energy: (1/2)|∇ψ|²
        grad_r_x = np.roll(self.psi_r, -1, axis=0) - self.psi_r
        grad_r_y = np.roll(self.psi_r, -1, axis=1) - self.psi_r
        grad_r_z = np.roll(self.psi_r, -1, axis=2) - self.psi_r
        grad_i_x = np.roll(self.psi_i, -1, axis=0) - self.psi_i
        grad_i_y = np.roll(self.psi_i, -1, axis=1) - self.psi_i
        grad_i_z = np.roll(self.psi_i, -1, axis=2) - self.psi_i
        E_gradient = 0.5 * (grad_r_x**2 + grad_r_y**2 + grad_r_z**2 +
                           grad_i_x**2 + grad_i_y**2 + grad_i_z**2)
        
        # Total local energy density
        E_total_field = E_kinetic + E_potential + E_gradient
        
        # === τ-LINKED ENERGIES ===
        
        # Dispersion energy (τ modulates wave speed)
        # Higher τ = faster waves = more dispersive energy
        E_dispersion = self.tau * E_gradient
        
        # τ variance energy (energy in τ fluctuations)
        tau_deviation = self.tau - np.mean(self.tau)
        E_tau_variance = tau_deviation**2
        
        # === TOPOLOGY-LINKED ENERGIES ===
        
        # Energy in high-topology regions (defect cores)
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_phase_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_phase_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_phase_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_phase_x**2 + grad_phase_y**2 + grad_phase_z**2)
        
        high_topo_mask = topology > np.percentile(topology, 90)
        low_topo_mask = topology < np.percentile(topology, 50)
        
        # === VORTICITY-LINKED ENERGIES ===
        
        # Compute vorticity (2D slice for sign detection)
        vorticity = (np.roll(grad_phase_y, -1, axis=0) - grad_phase_y) - \
                    (np.roll(grad_phase_x, -1, axis=1) - grad_phase_x)
        
        pos_vort_mask = vorticity > 0.05
        neg_vort_mask = vorticity < -0.05
        
        # === AGGREGATE MEASUREMENTS ===
        
        n_total = self.size**3
        
        results = {
            # Global totals
            'E_total': float(np.sum(E_total_field)),
            'E_kinetic_total': float(np.sum(E_kinetic)),
            'E_potential_total': float(np.sum(E_potential)),
            'E_gradient_total': float(np.sum(E_gradient)),
            
            # Per-cell averages
            'E_kinetic_mean': float(np.mean(E_kinetic)),
            'E_potential_mean': float(np.mean(E_potential)),
            'E_gradient_mean': float(np.mean(E_gradient)),
            
            # τ-linked
            'E_dispersion_total': float(np.sum(E_dispersion)),
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'tau_variance_total': float(np.sum(E_tau_variance)),
            
            # Spatial partitioning: Interior vs Periphery
            'E_interior': float(np.sum(E_total_field[self.interior_mask])),
            'E_periphery': float(np.sum(E_total_field[self.periphery_mask])),
            'E_transition': float(np.sum(E_total_field[self.transition_mask])),
            'n_interior': int(np.sum(self.interior_mask)),
            'n_periphery': int(np.sum(self.periphery_mask)),
            
            # Interior vs periphery τ
            'tau_interior': float(np.mean(self.tau[self.interior_mask])),
            'tau_periphery': float(np.mean(self.tau[self.periphery_mask])),
            
            # Topology partitioning: High-topo (defects) vs Low-topo (bulk)
            'E_high_topo': float(np.sum(E_total_field[high_topo_mask])),
            'E_low_topo': float(np.sum(E_total_field[low_topo_mask])),
            'n_high_topo': int(np.sum(high_topo_mask)),
            'n_low_topo': int(np.sum(low_topo_mask)),
            
            # High-topo τ
            'tau_high_topo': float(np.mean(self.tau[high_topo_mask])) if np.any(high_topo_mask) else 0,
            'tau_low_topo': float(np.mean(self.tau[low_topo_mask])) if np.any(low_topo_mask) else 0,
            
            # Vorticity partitioning: Signed sectors
            'E_pos_vort': float(np.sum(E_total_field[pos_vort_mask])),
            'E_neg_vort': float(np.sum(E_total_field[neg_vort_mask])),
            'n_pos_vort': int(np.sum(pos_vort_mask)),
            'n_neg_vort': int(np.sum(neg_vort_mask)),
            
            # Channel/remnant (proxy for "bound" energy)
            'channel_total': float(np.sum(self.channel_assignment)),
            'remnant_total': float(np.sum(self.remnant_field)),
            
            # Bound vs free energy proxy
            # Bound: energy in high-channel regions (established structure)
            # Free: energy in low-channel regions (available for new structure)
            'E_bound_proxy': float(np.sum(E_total_field * self.channel_assignment)),
            'E_free_proxy': float(np.sum(E_total_field * (1 - self.channel_assignment))),
        }
        
        return results


def run_energy_audit():
    """
    Run comprehensive energy audit over 1500 steps.
    """
    print("=" * 75)
    print("  ENERGY AUDIT: Layer-Resolved Energy Accounting")
    print("=" * 75)
    print()
    print("Question: Is the simulator energetically flat, or is τ already")
    print("          encoding non-uniform energy accounting?")
    print()
    
    sim = EnergyAuditSimulator(size=48, injection_interval=80)
    
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
    
    history = []
    
    print(f"{'Step':>5} │ {'E_total':>10} │ {'τ_std':>7} │ "
          f"{'E_int/E_per':>11} │ {'τ_int/τ_per':>11} │ {'E_high/E_low':>12}")
    print("-" * 75)
    
    for step in range(1500):
        sim.step()
        
        if step % 100 == 0 and step > 0:
            audit = sim.compute_energy_audit()
            audit['step'] = step
            history.append(audit)
            
            # Ratios
            E_int_per = audit['E_interior'] / (audit['E_periphery'] + 1e-10)
            tau_int_per = audit['tau_interior'] / (audit['tau_periphery'] + 1e-10)
            E_high_low = audit['E_high_topo'] / (audit['E_low_topo'] + 1e-10)
            
            print(f"{step:>5} │ {audit['E_total']:>10.1f} │ {audit['tau_std']:>7.4f} │ "
                  f"{E_int_per:>11.3f} │ {tau_int_per:>11.4f} │ {E_high_low:>12.4f}")
    
    # === ANALYSIS ===
    print()
    print("=" * 75)
    print("ENERGY DISTRIBUTION ANALYSIS")
    print("=" * 75)
    
    # 1. Is energy spatially uniform?
    print()
    print("1. SPATIAL ENERGY DISTRIBUTION")
    print("-" * 50)
    
    E_int_ratios = [h['E_interior'] / (h['E_periphery'] + 1e-10) for h in history]
    n_int = history[0]['n_interior']
    n_per = history[0]['n_periphery']
    volume_ratio = n_int / n_per
    
    avg_E_int_ratio = np.mean(E_int_ratios)
    
    print(f"   Volume ratio (interior/periphery): {volume_ratio:.3f}")
    print(f"   Energy ratio (interior/periphery): {avg_E_int_ratio:.3f}")
    print(f"   Per-cell energy density ratio:     {avg_E_int_ratio / volume_ratio:.3f}")
    
    if abs(avg_E_int_ratio / volume_ratio - 1.0) < 0.1:
        print("   → Energy is SPATIALLY UNIFORM (per-cell)")
        spatial_uniform = True
    else:
        print(f"   → Energy is SPATIALLY STRUCTURED (interior {avg_E_int_ratio / volume_ratio:.2f}× denser)")
        spatial_uniform = False
    
    # 2. Is τ encoding energy structure?
    print()
    print("2. τ AS ENERGY PROXY")
    print("-" * 50)
    
    tau_int = [h['tau_interior'] for h in history]
    tau_per = [h['tau_periphery'] for h in history]
    tau_high = [h['tau_high_topo'] for h in history]
    tau_low = [h['tau_low_topo'] for h in history]
    
    E_totals = [h['E_total'] for h in history]
    tau_stds = [h['tau_std'] for h in history]
    
    # Correlation between τ variance and total energy
    if len(E_totals) > 3:
        corr_tau_E, _ = pearsonr(tau_stds, E_totals)
    else:
        corr_tau_E = 0
    
    print(f"   τ (interior mean):   {np.mean(tau_int):.4f}")
    print(f"   τ (periphery mean):  {np.mean(tau_per):.4f}")
    print(f"   τ (high-topo mean):  {np.mean(tau_high):.4f}")
    print(f"   τ (low-topo mean):   {np.mean(tau_low):.4f}")
    print(f"   Correlation(τ_std, E_total): {corr_tau_E:+.3f}")
    
    if np.mean(tau_high) > np.mean(tau_low) * 1.01:
        print("   → τ is ELEVATED in high-topology regions")
        tau_topo_linked = True
    else:
        print("   → τ is FLAT across topology levels")
        tau_topo_linked = False
    
    # 3. Bound vs free energy
    print()
    print("3. BOUND VS FREE ENERGY (CHANNEL PROXY)")
    print("-" * 50)
    
    E_bound = [h['E_bound_proxy'] for h in history]
    E_free = [h['E_free_proxy'] for h in history]
    
    avg_bound = np.mean(E_bound)
    avg_free = np.mean(E_free)
    bound_fraction = avg_bound / (avg_bound + avg_free + 1e-10)
    
    print(f"   E_bound (in channels):  {avg_bound:.1f}")
    print(f"   E_free (outside):       {avg_free:.1f}")
    print(f"   Bound fraction:         {bound_fraction:.3f}")
    
    # Trend over time
    early_bound = np.mean([h['E_bound_proxy'] for h in history[:3]])
    late_bound = np.mean([h['E_bound_proxy'] for h in history[-3:]])
    
    print(f"   Early bound fraction:   {early_bound / (history[0]['E_total'] + 1e-10):.3f}")
    print(f"   Late bound fraction:    {late_bound / (history[-1]['E_total'] + 1e-10):.3f}")
    
    if late_bound > early_bound * 1.1:
        print("   → Energy is ACCUMULATING in channels over time")
        channel_accumulating = True
    else:
        print("   → Energy distribution to channels is STABLE")
        channel_accumulating = False
    
    # 4. Signed sector energies
    print()
    print("4. SIGNED SECTOR ENERGY BALANCE")
    print("-" * 50)
    
    E_pos = [h['E_pos_vort'] for h in history]
    E_neg = [h['E_neg_vort'] for h in history]
    
    avg_E_pos = np.mean(E_pos)
    avg_E_neg = np.mean(E_neg)
    
    print(f"   E(+ vorticity):  {avg_E_pos:.1f}")
    print(f"   E(- vorticity):  {avg_E_neg:.1f}")
    print(f"   Balance ratio:   {avg_E_pos / (avg_E_neg + 1e-10):.3f}")
    
    if abs(avg_E_pos / (avg_E_neg + 1e-10) - 1.0) < 0.1:
        print("   → Signed sectors are ENERGETICALLY BALANCED")
        sector_balanced = True
    else:
        print("   → Signed sectors have ENERGY ASYMMETRY")
        sector_balanced = False
    
    # 5. Dispersion energy (τ-linked)
    print()
    print("5. τ-LINKED DISPERSION ENERGY")
    print("-" * 50)
    
    E_disp = [h['E_dispersion_total'] for h in history]
    E_grad = [h['E_gradient_total'] for h in history]
    
    disp_ratio = np.mean(E_disp) / (np.mean(E_grad) + 1e-10)
    
    print(f"   E_gradient (mean):   {np.mean(E_grad):.1f}")
    print(f"   E_dispersion (mean): {np.mean(E_disp):.1f}")
    print(f"   Dispersion/Gradient: {disp_ratio:.3f}")
    
    if disp_ratio > 1.05:
        print(f"   → τ is AMPLIFYING gradient energy by {(disp_ratio - 1) * 100:.1f}%")
    elif disp_ratio < 0.95:
        print(f"   → τ is SUPPRESSING gradient energy by {(1 - disp_ratio) * 100:.1f}%")
    else:
        print("   → τ has MINIMAL effect on gradient energy")
    
    # === VERDICT ===
    print()
    print("=" * 75)
    print("AUDIT VERDICT")
    print("=" * 75)
    print()
    
    is_flat = spatial_uniform and not tau_topo_linked and not channel_accumulating
    
    if is_flat:
        print("VERDICT: Simulator is ENERGETICALLY FLAT")
        print()
        print("Evidence:")
        print("  - Spatial energy is uniform (per-cell)")
        print("  - τ does not correlate with topology")
        print("  - Channel accumulation is not occurring")
        print()
        print("Implication: Full layered energy architecture is needed.")
        verdict = "flat"
    else:
        print("VERDICT: Simulator has EXISTING ENERGY STRUCTURE")
        print()
        print("Evidence of structure:")
        if not spatial_uniform:
            print(f"  ✓ Spatial non-uniformity (interior {avg_E_int_ratio / volume_ratio:.2f}× denser)")
        if tau_topo_linked:
            print(f"  ✓ τ is elevated in high-topology regions")
        if channel_accumulating:
            print(f"  ✓ Energy accumulates in channels over time")
        if sector_balanced:
            print(f"  ✓ Signed sectors are energetically balanced")
        print()
        print("Implication: τ may already be doing primitive layer-0 accounting.")
        print("Recommendation: Extend existing τ-based structure before full redesign.")
        verdict = "structured"
    
    # === τ SELF-REGULATION ANALYSIS ===
    print()
    print("=" * 75)
    print("τ SELF-REGULATION HYPOTHESIS")
    print("=" * 75)
    print()
    print("Question: Is τ already acting as a primitive energy bookkeeper?")
    print()
    
    # Check if τ responds to energy changes
    dE = np.diff(E_totals)
    dtau = np.diff(tau_stds)
    
    if len(dE) > 3:
        corr_dE_dtau, _ = pearsonr(dE, dtau)
    else:
        corr_dE_dtau = 0
    
    print(f"Correlation(ΔE, Δτ_std): {corr_dE_dtau:+.3f}")
    
    if abs(corr_dE_dtau) > 0.3:
        print("→ τ RESPONDS to energy changes (feedback loop exists)")
        tau_feedback = True
    else:
        print("→ τ does NOT respond to energy changes")
        tau_feedback = False
    
    # Check if τ limits energy growth
    print()
    print("τ response in high-energy regions:")
    print(f"  τ in high-topology (energy-rich): {np.mean(tau_high):.4f}")
    print(f"  τ in low-topology (energy-poor):  {np.mean(tau_low):.4f}")
    
    if np.mean(tau_high) > np.mean(tau_low) * 1.01:
        print("→ τ ELEVATES in energy-rich regions (self-limiting mechanism)")
        tau_self_limiting = True
    else:
        print("→ τ does not show self-limiting behavior")
        tau_self_limiting = False
    
    print()
    if tau_feedback or tau_self_limiting:
        print("CONCLUSION: τ IS acting as primitive layer-0 accounting")
        print("  - It responds to energy distribution")
        print("  - It elevates in high-energy regions (dissipation)")
        print("  - Extend this mechanism rather than replace it")
    else:
        print("CONCLUSION: τ is NOT doing significant energy accounting")
        print("  - A new layered energy model is needed")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/energy_audit_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'energy_audit',
            'history': history,
            'verdict': verdict,
            'analysis': {
                'spatial_uniform': spatial_uniform,
                'tau_topo_linked': tau_topo_linked,
                'channel_accumulating': channel_accumulating,
                'sector_balanced': sector_balanced,
                'tau_feedback': tau_feedback if 'tau_feedback' in dir() else False,
                'tau_self_limiting': tau_self_limiting if 'tau_self_limiting' in dir() else False,
            }
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, verdict


if __name__ == "__main__":
    history, verdict = run_energy_audit()
