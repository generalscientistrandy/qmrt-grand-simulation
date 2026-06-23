"""
Proper Hamiltonian Energy Test for QMRT
=======================================

The previous test showed τ injection >> τ deviation energy change.
This means we need a CORRECT energy formula for τ.

Physical interpretation:
- τ represents medium tension/stiffness
- Injecting energy into τ increases tension
- The energy stored should scale with τ itself, not (τ-1)²

New hypothesis: E_τ = Σ log(τ) or E_τ = Σ τ²

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os


class HamiltonianEnergyTracker:
    """Test different energy formulations for proper conservation."""
    
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
        
        # Energy tracking with multiple τ formulas
        self.history = {
            'T': [],
            'wave_kinetic': [],
            'wave_potential': [],
            'tau_sum': [],           # Σ τ (simplest)
            'tau_deviation_sq': [],  # Σ (τ-1)²
            'tau_log': [],           # Σ log(τ)
            'tau_squared': [],       # Σ τ²
            'total_wave': [],
        }
        
        self._record()
    
    def _compute_energies(self):
        """Compute wave and multiple τ energy formulations."""
        # Wave kinetic
        wave_kinetic = 0.5 * np.sum(self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Wave potential (amplitude + gradient)
        wave_potential = 0.5 * np.sum(self.psi_r**2 + self.psi_i**2)
        for axis in range(3):
            grad_r = np.roll(self.psi_r, -1, axis=axis) - self.psi_r
            grad_i = np.roll(self.psi_i, -1, axis=axis) - self.psi_i
            wave_potential += 0.25 * np.sum(grad_r**2 + grad_i**2)
        
        # Multiple τ energy formulations
        tau_sum = np.sum(self.tau)
        tau_deviation_sq = np.sum((self.tau - 1.0)**2)
        tau_log = np.sum(np.log(self.tau))
        tau_squared = np.sum(self.tau**2)
        
        return {
            'wave_kinetic': float(wave_kinetic),
            'wave_potential': float(wave_potential),
            'tau_sum': float(tau_sum),
            'tau_deviation_sq': float(tau_deviation_sq),
            'tau_log': float(tau_log),
            'tau_squared': float(tau_squared),
            'total_wave': float(wave_kinetic + wave_potential),
        }
    
    def _record(self):
        e = self._compute_energies()
        for key in self.history:
            if key == 'T':
                self.history['T'].append(self.global_T)
            else:
                self.history[key].append(e[key])
    
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
        
        # Damping → τ transfer
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


def run_hamiltonian_test():
    """Find the correct Hamiltonian formulation."""
    
    print("=" * 70)
    print("  HAMILTONIAN ENERGY FORMULATION TEST")
    print("=" * 70)
    print()
    print("  Testing multiple τ energy formulas to find conserved quantity:")
    print("    1. E_τ = Σ τ")
    print("    2. E_τ = Σ (τ-1)²")
    print("    3. E_τ = Σ log(τ)")
    print("    4. E_τ = Σ τ²")
    print()
    
    sim = HamiltonianEnergyTracker(size=32, dt=0.12, seed=42, gamma=0.007)
    
    target_T = 300
    sample_interval = 5.0
    last_sample = 0
    
    print("  Running simulation...")
    
    while sim.global_T < target_T:
        sim.step()
        
        if sim.global_T - last_sample >= sample_interval:
            last_sample = sim.global_T
            sim._record()
    
    h = sim.history
    
    # Compute conservation quality for each formulation
    # We want: d(wave + α*τ_energy)/dt ≈ 0
    
    print()
    print("=" * 70)
    print("  CONSERVATION ANALYSIS")
    print("=" * 70)
    print()
    
    wave_initial = h['total_wave'][0]
    wave_final = h['total_wave'][-1]
    wave_change = wave_final - wave_initial
    
    print(f"  Wave Energy Change: {wave_change:.2f}")
    print()
    
    # For each τ formulation, find optimal scaling and check conservation
    formulations = [
        ('Σ τ', 'tau_sum'),
        ('Σ (τ-1)²', 'tau_deviation_sq'),
        ('Σ log(τ)', 'tau_log'),
        ('Σ τ²', 'tau_squared'),
    ]
    
    results = []
    
    for name, key in formulations:
        tau_initial = h[key][0]
        tau_final = h[key][-1]
        tau_change = tau_final - tau_initial
        
        # Find optimal scaling coefficient α
        # We want wave_change + α * tau_change ≈ 0
        if abs(tau_change) > 1e-10:
            optimal_alpha = -wave_change / tau_change
        else:
            optimal_alpha = float('inf')
        
        # Compute total energy with optimal scaling
        total_initial = wave_initial + optimal_alpha * tau_initial if optimal_alpha != float('inf') else float('inf')
        total_final = wave_final + optimal_alpha * tau_final if optimal_alpha != float('inf') else float('inf')
        
        if optimal_alpha != float('inf'):
            total_change_pct = abs(total_final - total_initial) / abs(total_initial) * 100
        else:
            total_change_pct = float('inf')
        
        results.append({
            'name': name,
            'key': key,
            'tau_change': tau_change,
            'optimal_alpha': optimal_alpha,
            'total_change_pct': total_change_pct,
        })
        
        print(f"  {name}:")
        print(f"    τ Change: {tau_change:.4f}")
        print(f"    Optimal α: {optimal_alpha:.4f}" if optimal_alpha != float('inf') else f"    Optimal α: ∞")
        print(f"    Conservation drift: {total_change_pct:.4f}%" if total_change_pct != float('inf') else "    Conservation drift: ∞")
        print()
    
    # Find best formulation
    valid_results = [r for r in results if r['total_change_pct'] != float('inf') and r['total_change_pct'] < 100]
    if valid_results:
        best = min(valid_results, key=lambda x: x['total_change_pct'])
        print("=" * 70)
        print(f"  BEST FORMULATION: {best['name']}")
        print(f"  Optimal Hamiltonian: H = E_wave + {best['optimal_alpha']:.4f} × {best['name']}")
        print(f"  Conservation quality: {best['total_change_pct']:.4f}% drift")
        print("=" * 70)
    
    # Plot
    output_dir = '/app/backend/qmrt_topology/papers/artifact_audit'
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    T = h['T']
    
    # Panel A: Wave energy
    ax = axes[0, 0]
    ax.plot(T, h['total_wave'], color='purple', linewidth=2)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Energy')
    ax.set_title('(A) Total Wave Energy')
    ax.grid(True, alpha=0.3)
    
    # Panel B: Σ τ
    ax = axes[0, 1]
    ax.plot(T, h['tau_sum'], color='red')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Σ τ')
    ax.set_title('(B) τ Sum')
    ax.grid(True, alpha=0.3)
    
    # Panel C: Σ log(τ)
    ax = axes[0, 2]
    ax.plot(T, h['tau_log'], color='blue')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Σ log(τ)')
    ax.set_title('(C) τ Log Sum')
    ax.grid(True, alpha=0.3)
    
    # Panel D-F: Combined energies with optimal scaling
    for i, (name, key) in enumerate([('Σ τ', 'tau_sum'), ('Σ log(τ)', 'tau_log'), ('Σ τ²', 'tau_squared')]):
        ax = axes[1, i]
        
        result = next((r for r in results if r['key'] == key), None)
        if result and result['optimal_alpha'] != float('inf'):
            alpha = result['optimal_alpha']
            combined = [w + alpha * t for w, t in zip(h['total_wave'], h[key])]
            combined_norm = [c / combined[0] for c in combined]
            wave_norm = [w / h['total_wave'][0] for w in h['total_wave']]
            
            ax.plot(T, wave_norm, label='Wave only', color='purple', linestyle='--', alpha=0.7)
            ax.plot(T, combined_norm, label=f'Wave + {alpha:.2f}×{name}', color='black', linewidth=2)
            ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)
            ax.set_xlabel('Time T')
            ax.set_ylabel('Normalized Energy')
            ax.set_title(f'(D) Conservation with {name}')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0.9, 1.1)
    
    plt.suptitle('Hamiltonian Energy Formulation Test', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/hamiltonian_energy_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print()
    print(f"  Plot saved to: {output_dir}/hamiltonian_energy_test.png")
    
    # Save results
    analysis = {
        'wave_change': wave_change,
        'formulations': results,
        'best_formulation': best['name'] if valid_results else None,
        'best_alpha': best['optimal_alpha'] if valid_results else None,
        'best_drift_pct': best['total_change_pct'] if valid_results else None,
    }
    
    with open(f'{output_dir}/hamiltonian_energy_test.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    return analysis


if __name__ == "__main__":
    run_hamiltonian_test()
