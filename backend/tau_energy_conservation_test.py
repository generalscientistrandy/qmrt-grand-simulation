"""
Test: τ as Natural Energy Sink/Source
======================================

Hypothesis: Total energy (wave + τ) is conserved even when wave energy
alone drifts. The τ field acts as a natural energy reservoir.

This would be a NATURAL fix — no artificial rescaling needed.

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, List
import json
import os


class TotalEnergyTracker:
    """Track wave energy AND τ energy separately to test conservation."""
    
    def __init__(self, size=32, dt=0.12, seed=42, gamma=0.007):
        self.size = size
        self.dt = dt
        self.gamma = gamma
        
        np.random.seed(seed)
        
        # Physics
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.global_T = 0.0
        
        # Fields
        shape = (size, size, size)
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Initial perturbation
        center = size // 2
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
                    if r < 4:
                        amp = 0.8 * np.exp(-r**2 / 6)
                        self.psi_r[x, y, z] += amp * np.random.randn()
                        self.psi_i[x, y, z] += amp * np.random.randn()
                    if r < 3:
                        vel_amp = 0.3 * np.exp(-r**2 / 4)
                        self.psi_r_dot[x, y, z] += vel_amp * np.random.randn()
                        self.psi_i_dot[x, y, z] += vel_amp * np.random.randn()
        
        # Energy tracking
        self.wave_kinetic_history = []
        self.wave_potential_history = []
        self.tau_energy_history = []
        self.total_energy_history = []
        self.T_history = []
        
        self._record_energy()
    
    def _compute_energies(self):
        """Compute wave and τ energies separately."""
        # Wave kinetic
        wave_kinetic = 0.5 * np.sum(self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Wave potential (amplitude + gradient)
        wave_potential = 0.5 * np.sum(self.psi_r**2 + self.psi_i**2)
        
        # Gradient energy
        for axis in range(3):
            grad_r = np.roll(self.psi_r, -1, axis=axis) - self.psi_r
            grad_i = np.roll(self.psi_i, -1, axis=axis) - self.psi_i
            wave_potential += 0.25 * np.sum(grad_r**2 + grad_i**2)
        
        # τ energy: energy stored in τ deviation from equilibrium
        # τ = 1 is equilibrium, τ > 1 stores energy, τ < 1 is depleted
        tau_energy = np.sum((self.tau - 1.0)**2) * 10  # Scale factor for visibility
        
        total = wave_kinetic + wave_potential + tau_energy
        
        return float(wave_kinetic), float(wave_potential), float(tau_energy), float(total)
    
    def _record_energy(self):
        wk, wp, te, total = self._compute_energies()
        self.wave_kinetic_history.append(wk)
        self.wave_potential_history.append(wp)
        self.tau_energy_history.append(te)
        self.total_energy_history.append(total)
        self.T_history.append(self.global_T)
    
    def _laplacian(self, f):
        lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def step(self):
        self.global_T += self.dt
        
        # τ dynamics
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # Key: damped energy goes INTO τ (energy transfer, not loss)
        if self.damping_to_tau > 0 and self.gamma > 0:
            damped_energy = self.gamma * kinetic
            self.tau += self.damping_to_tau * damped_energy
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._laplacian(self.psi_r)
        lap_i = self._laplacian(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt


def run_total_energy_test():
    """Test if total (wave + τ) energy is conserved."""
    
    print("=" * 70)
    print("  TEST: τ AS NATURAL ENERGY SINK/SOURCE")
    print("=" * 70)
    print()
    print("  Hypothesis: Total (wave + τ) energy is conserved")
    print("              even when wave energy alone drifts.")
    print()
    
    # Run simulation
    sim = TotalEnergyTracker(size=32, dt=0.12, seed=42, gamma=0.007)
    
    target_T = 300
    sample_interval = 5.0
    last_sample = 0
    
    print("  Running simulation...")
    
    while sim.global_T < target_T:
        sim.step()
        
        if sim.global_T - last_sample >= sample_interval:
            last_sample = sim.global_T
            sim._record_energy()
    
    # Analysis
    print()
    print("=" * 70)
    print("  ENERGY PARTITION ANALYSIS")
    print("=" * 70)
    print()
    
    initial_wave = sim.wave_kinetic_history[0] + sim.wave_potential_history[0]
    final_wave = sim.wave_kinetic_history[-1] + sim.wave_potential_history[-1]
    wave_change = (final_wave - initial_wave) / initial_wave * 100
    
    initial_tau = sim.tau_energy_history[0]
    final_tau = sim.tau_energy_history[-1]
    tau_change = (final_tau - initial_tau) / (initial_tau + 1e-10) * 100
    
    initial_total = sim.total_energy_history[0]
    final_total = sim.total_energy_history[-1]
    total_change = (final_total - initial_total) / initial_total * 100
    
    print(f"  Wave Energy:")
    print(f"    Initial: {initial_wave:.2f}")
    print(f"    Final:   {final_wave:.2f}")
    print(f"    Change:  {wave_change:+.2f}%")
    print()
    print(f"  τ Energy:")
    print(f"    Initial: {initial_tau:.2f}")
    print(f"    Final:   {final_tau:.2f}")
    print(f"    Change:  {tau_change:+.2f}%")
    print()
    print(f"  TOTAL Energy (wave + τ):")
    print(f"    Initial: {initial_total:.2f}")
    print(f"    Final:   {final_total:.2f}")
    print(f"    Change:  {total_change:+.2f}%")
    print()
    
    # Verdict
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    print()
    
    if abs(total_change) < abs(wave_change) * 0.5:
        print("  ✓ HYPOTHESIS SUPPORTED:")
        print(f"    Total energy change ({total_change:+.2f}%) is SMALLER than")
        print(f"    wave energy change ({wave_change:+.2f}%).")
        print()
        print("    → τ field IS acting as energy sink/source!")
        print("    → This is a NATURAL conservation mechanism.")
        verdict = "SUPPORTED"
    elif abs(total_change) < 20:
        print("  ~ PARTIALLY SUPPORTED:")
        print(f"    Total energy drift ({total_change:+.2f}%) is moderate.")
        print(f"    τ is absorbing some energy but not perfectly.")
        verdict = "PARTIAL"
    else:
        print("  ✗ HYPOTHESIS NOT SUPPORTED:")
        print(f"    Total energy drifts significantly ({total_change:+.2f}%).")
        print("    Need different approach for conservation.")
        verdict = "NOT_SUPPORTED"
    
    # Plot
    output_dir = '/app/backend/qmrt_topology/papers/artifact_audit'
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    T = sim.T_history
    
    # Panel A: Wave energies
    ax = axes[0, 0]
    ax.plot(T, sim.wave_kinetic_history, label='Kinetic', color='blue')
    ax.plot(T, sim.wave_potential_history, label='Potential', color='green')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Energy')
    ax.set_title('(A) Wave Energy Components')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Panel B: τ energy
    ax = axes[0, 1]
    ax.plot(T, sim.tau_energy_history, label='τ Energy', color='red')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Energy')
    ax.set_title('(B) τ Field Energy')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Panel C: Total energy comparison
    ax = axes[1, 0]
    wave_total = [k + p for k, p in zip(sim.wave_kinetic_history, sim.wave_potential_history)]
    ax.plot(T, wave_total, label='Wave Only', color='purple', linestyle='--')
    ax.plot(T, sim.total_energy_history, label='Wave + τ', color='black', linewidth=2)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Energy')
    ax.set_title('(C) Total Energy Conservation')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Panel D: Normalized comparison
    ax = axes[1, 1]
    wave_norm = [w / wave_total[0] for w in wave_total]
    total_norm = [t / sim.total_energy_history[0] for t in sim.total_energy_history]
    ax.plot(T, wave_norm, label='Wave Only (norm)', color='purple', linestyle='--')
    ax.plot(T, total_norm, label='Wave + τ (norm)', color='black', linewidth=2)
    ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Normalized Energy')
    ax.set_title('(D) Normalized Energy Drift')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.5, 1.5)
    
    plt.suptitle('τ as Natural Energy Sink/Source', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/tau_energy_conservation.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print()
    print(f"  Plot saved to: {output_dir}/tau_energy_conservation.png")
    
    # Save data
    analysis = {
        'hypothesis': 'τ field acts as natural energy sink/source',
        'wave_energy_change_pct': wave_change,
        'tau_energy_change_pct': tau_change,
        'total_energy_change_pct': total_change,
        'verdict': verdict,
        'natural_conservation': abs(total_change) < abs(wave_change) * 0.5,
    }
    
    with open(f'{output_dir}/tau_energy_conservation.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    return analysis


if __name__ == "__main__":
    run_total_energy_test()
