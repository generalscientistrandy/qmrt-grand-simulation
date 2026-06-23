"""
Energy Conservation Sensitivity Test
=====================================

PURPOSE: Test whether our simulation mechanisms survive without artificial
energy stabilization. Check if the physics is real or an artifact of
energy band-aids.

TESTS:
1. Run with normal damping (gamma=0.007) - current config
2. Run with zero damping (gamma=0.0) - pure Hamiltonian
3. Run with high damping (gamma=0.05) - strong dissipation
4. Track energy conservation in each case
5. Check if DOF unlock mechanism survives

QUESTION: Does the mechanism depend on energy manipulation?

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from typing import Dict, List, Any
import time
import json
import os


class EnergyAuditSimulator:
    """
    Simulator with explicit energy tracking and configurable damping.
    Tests whether mechanisms survive without artificial energy correction.
    """
    
    def __init__(self, 
                 size: int = 32, 
                 dt: float = 0.12, 
                 seed: int = 42,
                 gamma: float = 0.007,  # Damping coefficient
                 tau_response: float = 0.02,
                 unlock_enabled: bool = True):
        
        self.size = size
        self.dt = dt
        self.seed = seed
        self.gamma = gamma
        self.tau_response = tau_response
        self.unlock_enabled = unlock_enabled
        
        np.random.seed(seed)
        
        # Physics parameters
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.unlock_threshold = 0.025
        self.unlock_rate = 0.03
        
        # Dimensional activation
        self.ax, self.ay, self.az = 1.0, 0.0, 0.0
        self.y_unlock_T = None
        self.z_unlock_T = None
        
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
        
        # Track initial energy
        self.initial_energy = self._compute_total_energy()
        self.energy_history = [self.initial_energy]
    
    def _compute_total_energy(self) -> float:
        """Compute total system energy (kinetic + potential + tau)."""
        # Kinetic energy
        kinetic = 0.5 * np.sum(self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Potential energy (wave amplitude)
        potential = 0.5 * np.sum(self.psi_r**2 + self.psi_i**2)
        
        # Tau excess energy
        tau_energy = np.sum((self.tau - 1.0)**2)
        
        # Gradient energy (wave tension)
        grad_r_x = np.roll(self.psi_r, -1, axis=0) - self.psi_r
        grad_r_y = np.roll(self.psi_r, -1, axis=1) - self.psi_r
        grad_r_z = np.roll(self.psi_r, -1, axis=2) - self.psi_r
        grad_i_x = np.roll(self.psi_i, -1, axis=0) - self.psi_i
        grad_i_y = np.roll(self.psi_i, -1, axis=1) - self.psi_i
        grad_i_z = np.roll(self.psi_i, -1, axis=2) - self.psi_i
        
        gradient_energy = 0.5 * np.sum(
            grad_r_x**2 + grad_r_y**2 + grad_r_z**2 +
            grad_i_x**2 + grad_i_y**2 + grad_i_z**2
        )
        
        return float(kinetic + potential + tau_energy + gradient_energy)
    
    def _laplacian(self, f):
        lap = (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def compute_pressure(self) -> float:
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        tau_excess = np.maximum(self.tau - 1.0, 0)
        return float(np.mean(kinetic) + np.mean(tau_excess) * 5)
    
    def check_unlock(self, pressure: float):
        if not self.unlock_enabled:
            return
        
        if self.ay < 1.0 and pressure > self.unlock_threshold:
            self.ay = min(1.0, self.ay + self.unlock_rate)
            if self.y_unlock_T is None and self.ay > 0.01:
                self.y_unlock_T = self.global_T
        
        if self.ay > 0.5 and self.az < 1.0 and pressure > self.unlock_threshold * 1.2:
            self.az = min(1.0, self.az + self.unlock_rate)
            if self.z_unlock_T is None and self.az > 0.01:
                self.z_unlock_T = self.global_T
    
    def compute_d_eff(self) -> float:
        return self.ax + self.ay * 0.5 + self.az * 0.5
    
    def step(self):
        """Advance one timestep - NO artificial energy correction."""
        self.global_T += self.dt
        
        # τ dynamics (this is the tau-response mechanism)
        if self.tau_response > 0:
            kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
            energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
            tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
            self.tau += self.tau_relaxation * (tau_target - self.tau)
            
            # Damped energy goes to tau (energy recycling)
            if self.damping_to_tau > 0 and self.gamma > 0:
                damped_energy = self.gamma * kinetic
                self.tau += self.damping_to_tau * damped_energy
            
            self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Wave equation with damping
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._laplacian(self.psi_r)
        lap_i = self._laplacian(self.psi_i)
        
        # Acceleration (with optional damping)
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        # Update velocities and positions
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt


def run_energy_sensitivity_test():
    """
    Test mechanism survival under different energy regimes.
    """
    
    print("=" * 70)
    print("  ENERGY CONSERVATION SENSITIVITY TEST")
    print("=" * 70)
    print()
    print("  Question: Does DOF unlock mechanism survive without energy band-aids?")
    print()
    
    configurations = [
        {'name': 'Normal damping', 'gamma': 0.007, 'desc': 'Current config'},
        {'name': 'Zero damping', 'gamma': 0.0, 'desc': 'Pure Hamiltonian'},
        {'name': 'Low damping', 'gamma': 0.002, 'desc': 'Minimal dissipation'},
        {'name': 'High damping', 'gamma': 0.02, 'desc': 'Strong dissipation'},
        {'name': 'Very high damping', 'gamma': 0.05, 'desc': 'Overdamped'},
    ]
    
    results = []
    
    for config in configurations:
        print(f"  Testing: {config['name']} (gamma={config['gamma']})...")
        
        sim = EnergyAuditSimulator(
            size=32, dt=0.12, seed=42,
            gamma=config['gamma'],
            tau_response=0.02,
            unlock_enabled=True
        )
        
        t_start = time.time()
        max_wall = 30
        target_T = 400
        
        energy_samples = []
        
        while sim.global_T < target_T:
            if time.time() - t_start >= max_wall - 2:
                break
            
            sim.step()
            
            pressure = sim.compute_pressure()
            sim.check_unlock(pressure)
            
            # Sample energy periodically
            if int(sim.global_T) % 50 == 0 and len(energy_samples) < int(sim.global_T / 50) + 1:
                current_energy = sim._compute_total_energy()
                energy_samples.append(current_energy)
        
        # Final metrics
        final_energy = sim._compute_total_energy()
        energy_change = (final_energy - sim.initial_energy) / sim.initial_energy * 100
        
        result = {
            'config': config['name'],
            'gamma': config['gamma'],
            'y_unlock_T': sim.y_unlock_T,
            'z_unlock_T': sim.z_unlock_T,
            'final_d_eff': sim.compute_d_eff(),
            'ay': sim.ay,
            'az': sim.az,
            'initial_energy': sim.initial_energy,
            'final_energy': final_energy,
            'energy_change_pct': energy_change,
            'energy_samples': energy_samples,
            'final_T': sim.global_T,
        }
        results.append(result)
        
        unlock_str = f"T={sim.y_unlock_T:.1f}" if sim.y_unlock_T else "Never"
        print(f"    Y unlock: {unlock_str}, Energy Δ: {energy_change:+.1f}%, D_eff: {sim.compute_d_eff():.2f}")
    
    # Analysis
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print()
    print(f"  {'Config':>20} | {'Gamma':>8} | {'Y Unlock':>10} | {'Energy Δ':>12} | {'D_eff':>8}")
    print("  " + "-"*70)
    
    for r in results:
        unlock_str = f"{r['y_unlock_T']:.1f}" if r['y_unlock_T'] else "Never"
        print(f"  {r['config']:>20} | {r['gamma']:>8.4f} | {unlock_str:>10} | "
              f"{r['energy_change_pct']:>+12.1f}% | {r['final_d_eff']:>8.2f}")
    
    # Key questions
    print()
    print("=" * 70)
    print("  KEY FINDINGS")
    print("=" * 70)
    print()
    
    # Does mechanism survive zero damping?
    zero_damp = next((r for r in results if r['gamma'] == 0.0), None)
    normal_damp = next((r for r in results if r['gamma'] == 0.007), None)
    
    if zero_damp:
        survives_zero = zero_damp['y_unlock_T'] is not None
        print(f"  1. Mechanism survives ZERO damping: {'YES' if survives_zero else 'NO'}")
        if survives_zero:
            print(f"     → Y unlock at T={zero_damp['y_unlock_T']:.1f}")
        print(f"     → Energy change: {zero_damp['energy_change_pct']:+.1f}%")
        
        if abs(zero_damp['energy_change_pct']) > 50:
            print(f"     ⚠️ WARNING: Large energy drift without damping!")
    
    # Does energy explode or collapse?
    print()
    energy_stable = all(abs(r['energy_change_pct']) < 200 for r in results)
    print(f"  2. Energy stability across configs: {'YES' if energy_stable else 'NO'}")
    
    # Does mechanism depend on damping level?
    unlock_counts = sum(1 for r in results if r['y_unlock_T'] is not None)
    print(f"  3. Configs showing unlock: {unlock_counts}/{len(results)}")
    
    # Conservation analysis
    print()
    print("  ENERGY CONSERVATION ANALYSIS:")
    for r in results:
        conservation = "CONSERVED" if abs(r['energy_change_pct']) < 10 else \
                      "MODERATE DRIFT" if abs(r['energy_change_pct']) < 50 else \
                      "LARGE DRIFT"
        print(f"    {r['config']:>20}: {r['energy_change_pct']:>+8.1f}% ({conservation})")
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    if zero_damp and zero_damp['y_unlock_T'] is not None and unlock_counts >= 4:
        verdict = "MECHANISM IS ROBUST: Survives without energy band-aid"
        mechanism_real = True
    elif unlock_counts >= 3:
        verdict = "MECHANISM LIKELY REAL: Works in most configurations"
        mechanism_real = True
    else:
        verdict = "MECHANISM MAY BE ARTIFACT: Depends on specific energy handling"
        mechanism_real = False
    
    print()
    print(f"  {verdict}")
    print()
    
    if mechanism_real:
        print("  The DOF unlock mechanism appears to be GENUINE PHYSICS,")
        print("  not an artifact of energy manipulation.")
    else:
        print("  ⚠️ The mechanism may depend on energy handling.")
        print("  Further investigation needed.")
    
    # Save results
    output_dir = '/app/backend/qmrt_topology/papers/artifact_audit'
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert for JSON
    analysis = {
        'test': 'Energy Conservation Sensitivity',
        'question': 'Does mechanism survive without energy band-aid?',
        'results': [{
            'config': r['config'],
            'gamma': r['gamma'],
            'y_unlock_T': r['y_unlock_T'],
            'final_d_eff': r['final_d_eff'],
            'energy_change_pct': r['energy_change_pct'],
        } for r in results],
        'verdict': verdict,
        'mechanism_robust': mechanism_real,
    }
    
    with open(f'{output_dir}/energy_sensitivity_test.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"  Results saved to: {output_dir}/energy_sensitivity_test.json")
    
    return results, analysis


def brainstorm_natural_fixes():
    """
    Brainstorm ideas for natural energy conservation without band-aids.
    """
    
    print()
    print("=" * 70)
    print("  BRAINSTORM: NATURAL ENERGY CONSERVATION")
    print("=" * 70)
    print()
    print("  Problem: Current energy handling is either artificial (rescaling)")
    print("           or dissipative (damping). Neither is ideal physics.")
    print()
    print("  POTENTIAL NATURAL FIXES:")
    print()
    
    ideas = [
        {
            'name': '1. Symplectic Integration',
            'desc': 'Use Yoshida 4th-order or higher symplectic integrator',
            'mechanism': 'Symplectic methods preserve phase space volume → energy bounded',
            'pros': 'Mathematically guaranteed energy bounds',
            'cons': 'More expensive, doesn\'t eliminate drift just bounds it',
        },
        {
            'name': '2. τ as Energy Sink/Source',
            'desc': 'Let τ field naturally absorb/release energy',
            'mechanism': 'τ > 1 stores energy, τ < 1 releases it. Total (wave + τ) conserved.',
            'pros': 'Already partially implemented! Energy goes to τ via damping_to_tau',
            'cons': 'Need to verify total conservation, not just wave energy',
        },
        {
            'name': '3. Creation Events as Energy Redistribution',
            'desc': 'When τ > threshold, create new excitations instead of capping',
            'mechanism': 'High τ → topological creation → energy redistributed spatially',
            'pros': 'Physically motivated, prevents accumulation',
            'cons': 'May change dynamics significantly',
        },
        {
            'name': '4. Boundary Flux Accounting',
            'desc': 'Track energy leaving/entering through boundaries',
            'mechanism': 'E_total = E_interior + E_radiated. Conserve the sum.',
            'pros': 'Honest accounting of open system',
            'cons': 'Requires radiation boundary conditions',
        },
        {
            'name': '5. Hamiltonian Formulation with τ',
            'desc': 'Derive equations from proper Hamiltonian including τ',
            'mechanism': 'H = ∫[½ρ̇² + ½c²(τ)|∇ρ|² + V(τ)]dx. dH/dt = 0 by construction.',
            'pros': 'Fundamental fix, guarantees conservation',
            'cons': 'Requires rederiving all equations',
        },
        {
            'name': '6. Constraint-Preserving Discretization',
            'desc': 'Use discrete exterior calculus or mimetic methods',
            'mechanism': 'Preserve differential geometric structure at discrete level',
            'pros': 'Conservation laws built into discretization',
            'cons': 'Complex implementation',
        },
    ]
    
    for idea in ideas:
        print(f"  {idea['name']}")
        print(f"    Description: {idea['desc']}")
        print(f"    Mechanism:   {idea['mechanism']}")
        print(f"    Pros:        {idea['pros']}")
        print(f"    Cons:        {idea['cons']}")
        print()
    
    print("=" * 70)
    print("  RECOMMENDED APPROACH")
    print("=" * 70)
    print()
    print("  Start with: Option 2 (τ as Energy Sink/Source)")
    print()
    print("  Reason: We ALREADY have damping_to_tau = 0.20, meaning 20% of")
    print("  damped kinetic energy goes into τ. This is a natural energy")
    print("  conservation mechanism if we track TOTAL energy (wave + τ).")
    print()
    print("  Test: Verify that (wave_energy + τ_energy) is conserved")
    print("  even when wave_energy alone is not.")
    print()
    
    return ideas


if __name__ == "__main__":
    results, analysis = run_energy_sensitivity_test()
    print()
    brainstorm_natural_fixes()
