"""
Detailed τ Energy Accounting Test
=================================

Track EXACTLY where energy goes:
1. Wave kinetic → damping → where?
2. Does τ actually receive the damped energy?
3. Is there a Hamiltonian formulation?

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os


class DetailedEnergyTracker:
    """Meticulously track every energy transfer."""
    
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
        
        # Detailed energy tracking
        self.history = {
            'T': [],
            'wave_kinetic': [],
            'wave_potential': [],
            'wave_gradient': [],
            'tau_deviation': [],
            'tau_mean': [],
            'cumulative_damping_loss': [],
            'cumulative_tau_injection': [],
        }
        
        self.cumulative_damping_loss = 0.0
        self.cumulative_tau_injection = 0.0
        
        self._record()
    
    def _compute_gradient_energy(self):
        """Compute gradient energy separately."""
        grad_energy = 0.0
        for axis in range(3):
            grad_r = np.roll(self.psi_r, -1, axis=axis) - self.psi_r
            grad_i = np.roll(self.psi_i, -1, axis=axis) - self.psi_i
            grad_energy += 0.25 * np.sum(grad_r**2 + grad_i**2)
        return float(grad_energy)
    
    def _record(self):
        kinetic = 0.5 * np.sum(self.psi_r_dot**2 + self.psi_i_dot**2)
        potential = 0.5 * np.sum(self.psi_r**2 + self.psi_i**2)
        gradient = self._compute_gradient_energy()
        tau_dev = np.sum((self.tau - 1.0)**2)
        
        self.history['T'].append(self.global_T)
        self.history['wave_kinetic'].append(float(kinetic))
        self.history['wave_potential'].append(float(potential))
        self.history['wave_gradient'].append(float(gradient))
        self.history['tau_deviation'].append(float(tau_dev))
        self.history['tau_mean'].append(float(np.mean(self.tau)))
        self.history['cumulative_damping_loss'].append(self.cumulative_damping_loss)
        self.history['cumulative_tau_injection'].append(self.cumulative_tau_injection)
    
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
        
        # Track damping → τ transfer
        if self.damping_to_tau > 0 and self.gamma > 0:
            damped_kinetic = self.gamma * kinetic
            tau_injection = self.damping_to_tau * damped_kinetic
            self.tau += tau_injection
            
            # Track cumulative amounts
            self.cumulative_damping_loss += np.sum(damped_kinetic) * self.dt
            self.cumulative_tau_injection += np.sum(tau_injection)
        
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


def run_detailed_test():
    """Deep dive into energy accounting."""
    
    print("=" * 70)
    print("  DETAILED τ ENERGY ACCOUNTING TEST")
    print("=" * 70)
    print()
    
    sim = DetailedEnergyTracker(size=32, dt=0.12, seed=42, gamma=0.007)
    
    target_T = 300
    sample_interval = 5.0
    last_sample = 0
    
    print("  Running simulation with detailed tracking...")
    
    while sim.global_T < target_T:
        sim.step()
        
        if sim.global_T - last_sample >= sample_interval:
            last_sample = sim.global_T
            sim._record()
    
    h = sim.history
    
    # Compute totals
    wave_total = [k + p + g for k, p, g in zip(h['wave_kinetic'], h['wave_potential'], h['wave_gradient'])]
    
    print()
    print("=" * 70)
    print("  ENERGY BREAKDOWN")
    print("=" * 70)
    print()
    print(f"  Initial State:")
    print(f"    Wave Kinetic:   {h['wave_kinetic'][0]:.2f}")
    print(f"    Wave Potential: {h['wave_potential'][0]:.2f}")
    print(f"    Wave Gradient:  {h['wave_gradient'][0]:.2f}")
    print(f"    τ Deviation:    {h['tau_deviation'][0]:.6f}")
    print(f"    τ Mean:         {h['tau_mean'][0]:.6f}")
    print()
    print(f"  Final State:")
    print(f"    Wave Kinetic:   {h['wave_kinetic'][-1]:.2f}")
    print(f"    Wave Potential: {h['wave_potential'][-1]:.2f}")
    print(f"    Wave Gradient:  {h['wave_gradient'][-1]:.2f}")
    print(f"    τ Deviation:    {h['tau_deviation'][-1]:.6f}")
    print(f"    τ Mean:         {h['tau_mean'][-1]:.6f}")
    print()
    
    wave_loss = wave_total[0] - wave_total[-1]
    tau_gain = h['tau_deviation'][-1] - h['tau_deviation'][0]
    
    print(f"  Energy Transfer Analysis:")
    print(f"    Wave Energy Lost:      {wave_loss:.2f}")
    print(f"    τ Deviation Gained:    {tau_gain:.6f}")
    print(f"    Cumulative Damping:    {h['cumulative_damping_loss'][-1]:.2f}")
    print(f"    Cumulative τ Inject:   {h['cumulative_tau_injection'][-1]:.6f}")
    print()
    
    # Check if damping energy = τ injection
    ratio = h['cumulative_tau_injection'][-1] / (h['cumulative_damping_loss'][-1] + 1e-10)
    print(f"  τ Injection / Damping Loss Ratio: {ratio:.4f}")
    print()
    
    # Key insight check
    print("=" * 70)
    print("  KEY INSIGHT")
    print("=" * 70)
    print()
    
    if tau_gain > wave_loss * 0.5:
        print("  ✓ τ absorbs significant portion of wave energy loss")
        print("    → Natural conservation mechanism EXISTS")
    elif tau_gain > 0:
        print("  ~ τ absorbs SOME energy, but not enough")
        print("    → Partial natural conservation")
        print("    → May need different energy definition for τ")
    else:
        print("  ✗ τ does NOT absorb wave energy")
        print("    → Need different approach")
    
    # Plot
    output_dir = '/app/backend/qmrt_topology/papers/artifact_audit'
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    T = h['T']
    
    # Panel A: Wave energy components
    ax = axes[0, 0]
    ax.plot(T, h['wave_kinetic'], label='Kinetic', color='blue')
    ax.plot(T, h['wave_potential'], label='Potential', color='green')
    ax.plot(T, h['wave_gradient'], label='Gradient', color='orange')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Energy')
    ax.set_title('(A) Wave Energy Components')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Panel B: Total wave energy
    ax = axes[0, 1]
    ax.plot(T, wave_total, color='purple', linewidth=2)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Energy')
    ax.set_title('(B) Total Wave Energy')
    ax.grid(True, alpha=0.3)
    
    # Panel C: τ mean
    ax = axes[0, 2]
    ax.plot(T, h['tau_mean'], color='red')
    ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Mean τ')
    ax.set_title('(C) τ Field Mean')
    ax.grid(True, alpha=0.3)
    
    # Panel D: τ deviation (proxy for τ energy)
    ax = axes[1, 0]
    ax.plot(T, h['tau_deviation'], color='red')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Σ(τ-1)²')
    ax.set_title('(D) τ Deviation Energy')
    ax.grid(True, alpha=0.3)
    
    # Panel E: Cumulative transfers
    ax = axes[1, 1]
    ax.plot(T, h['cumulative_damping_loss'], label='Damping Loss', color='blue')
    ax.plot(T, [x * 1000 for x in h['cumulative_tau_injection']], label='τ Injection (×1000)', color='red')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Cumulative Energy')
    ax.set_title('(E) Cumulative Energy Transfers')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Panel F: Conservation check
    ax = axes[1, 2]
    # Theoretical conserved quantity: wave + 10*tau_deviation
    conserved = [w + 10 * td for w, td in zip(wave_total, h['tau_deviation'])]
    ax.plot(T, [w / wave_total[0] for w in wave_total], label='Wave (norm)', color='purple', linestyle='--')
    ax.plot(T, [c / conserved[0] for c in conserved], label='Wave + τ (norm)', color='black', linewidth=2)
    ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Normalized Energy')
    ax.set_title('(F) Conservation Check')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.suptitle('Detailed τ Energy Accounting', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/tau_energy_detailed.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print()
    print(f"  Plot saved to: {output_dir}/tau_energy_detailed.png")
    
    return h


if __name__ == "__main__":
    run_detailed_test()
