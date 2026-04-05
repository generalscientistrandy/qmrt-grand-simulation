#!/usr/bin/env python3
"""
QMRT Medium-State-Based Emergent Time Test
============================================

KEY QUESTION:
Is emergent time better described by a clock that depends on the 
medium state τ, rather than directly on energy density ρ?

The dynamical medium provides τ as a candidate non-circular temporal variable:
- τ has memory (doesn't track ρ instantly)
- τ relaxes toward equilibrium
- τ is the actual carrier of geometry

CLOCKS TO TEST:
---------------

1. RAW CLOCK: t (simulation time)
   - The computational parameter
   - No physics meaning

2. TRANSPORT CLOCK: τ_transport = ∫ c(τ) dt
   - Based on local wave speed
   - Similar to previous c_eff-based clock

3. MEDIUM-STATE CLOCK: τ_medium = ∫ (1/τ) dt
   - Based on medium field directly
   - Lower τ → faster clock (stronger geometry)

4. MIXED CLOCK: τ_mixed = ∫ c(τ)/τ dt
   - Combines transport and medium state
   - May capture both effects

5. OSCILLATOR CLOCK: count of local phase cycles
   - Independent oscillators in different regions
   - Compare cycle counts under different clocks

KEY TEST:
---------
Do clocks synchronize better in coherent (geometric) regimes 
when built from τ rather than from ρ?

If τ-based clocks give less circular, more physically meaningful
synchronization, the temporal sector improves.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


class DynamicalMediumWithClocks:
    """
    Dynamical medium simulator with multiple clock types.
    """
    
    def __init__(
        self,
        size: int = 100,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        beta: float = 1.0,
        lambda_relax: float = 1.5,
        D_medium: float = 0.1,
        gamma_wave: float = 0.008,
        dt: float = 0.04,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        # Clocks (accumulated at reference point)
        self.ref_point = (size // 2, size // 2)
        
        self.clock_raw = 0.0
        self.clock_transport = 0.0
        self.clock_medium = 0.0
        self.clock_mixed = 0.0
        
        # History
        self.clock_history = {
            'raw': [],
            'transport': [],
            'medium': [],
            'mixed': [],
        }
        
    def compute_c_eff(self):
        """Wave speed from medium state."""
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
        """Advance one timestep."""
        rho = self.phi**2 + self.phi_dot**2
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        
        tau_eq = self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
        
        lap_tau = (np.roll(self.tau, 1, axis=0) + np.roll(self.tau, -1, axis=0) +
                   np.roll(self.tau, 1, axis=1) + np.roll(self.tau, -1, axis=1) - 
                   4 * self.tau)
        
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        
        lap_phi = (np.roll(self.phi, 1, axis=0) + np.roll(self.phi, -1, axis=0) +
                   np.roll(self.phi, 1, axis=1) + np.roll(self.phi, -1, axis=1) - 
                   4 * self.phi)
        
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
        
        # Update clocks at reference point
        ri, rj = self.ref_point
        local_c = c_eff[ri, rj]
        local_tau = self.tau[ri, rj]
        
        self.clock_raw += self.dt
        self.clock_transport += local_c * self.dt
        self.clock_medium += (1.0 / local_tau) * self.dt
        self.clock_mixed += (local_c / local_tau) * self.dt
        
    def record_clocks(self):
        """Record current clock values."""
        self.clock_history['raw'].append(self.clock_raw)
        self.clock_history['transport'].append(self.clock_transport)
        self.clock_history['medium'].append(self.clock_medium)
        self.clock_history['mixed'].append(self.clock_mixed)
    
    def add_pulse(self, center, amplitude=3.0, width=4.0, velocity=True):
        """Add a Gaussian pulse."""
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    if velocity:
                        self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
                    else:
                        self.phi[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))


def run_clock_comparison_test():
    """
    Test 1: Compare clock behavior in different regimes.
    """
    print("Test 1: Clock Comparison (coherent vs disordered)")
    print("-" * 50)
    
    results = {}
    
    # Run in two regimes: with and without strong energy concentration
    
    for regime, amplitude in [('weak', 0.5), ('strong', 5.0)]:
        sim = DynamicalMediumWithClocks(size=80)
        
        # Add energy at reference point
        sim.add_pulse([40, 40], amplitude=amplitude)
        
        for t in range(400):
            sim.step()
            if t % 10 == 0:
                sim.record_clocks()
        
        results[regime] = {
            'raw': np.array(sim.clock_history['raw']),
            'transport': np.array(sim.clock_history['transport']),
            'medium': np.array(sim.clock_history['medium']),
            'mixed': np.array(sim.clock_history['mixed']),
            'final_tau': sim.tau[40, 40],
        }
        
        print(f"  {regime}: τ_final={results[regime]['final_tau']:.3f}")
    
    return results


def run_multi_region_synchronization():
    """
    Test 2: Do clocks in different regions synchronize better 
    with τ-based clocks?
    """
    print("\nTest 2: Multi-Region Clock Synchronization")
    print("-" * 50)
    
    sim = DynamicalMediumWithClocks(size=100)
    
    # Create inhomogeneous medium with energy concentration
    sim.add_pulse([50, 50], amplitude=5.0, velocity=False)
    
    # Define measurement regions
    regions = {
        'center': (50, 50),    # High energy, low τ
        'edge': (50, 20),      # Low energy, high τ
        'corner': (20, 20),    # Very low energy
    }
    
    # Track clocks at each region
    clocks = {name: {'raw': [], 'transport': [], 'medium': [], 'mixed': []}
              for name in regions}
    
    for t in range(500):
        sim.step()
        
        if t % 10 == 0:
            c_eff = sim.compute_c_eff()
            
            for name, (ri, rj) in regions.items():
                local_c = c_eff[ri, rj]
                local_tau = sim.tau[ri, rj]
                
                # Accumulate clocks
                if len(clocks[name]['raw']) == 0:
                    clocks[name]['raw'].append(sim.dt)
                    clocks[name]['transport'].append(local_c * sim.dt)
                    clocks[name]['medium'].append((1.0 / local_tau) * sim.dt)
                    clocks[name]['mixed'].append((local_c / local_tau) * sim.dt)
                else:
                    clocks[name]['raw'].append(clocks[name]['raw'][-1] + sim.dt * 10)
                    clocks[name]['transport'].append(clocks[name]['transport'][-1] + local_c * sim.dt * 10)
                    clocks[name]['medium'].append(clocks[name]['medium'][-1] + (1.0 / local_tau) * sim.dt * 10)
                    clocks[name]['mixed'].append(clocks[name]['mixed'][-1] + (local_c / local_tau) * sim.dt * 10)
    
    # Compute clock disagreement
    def compute_disagreement(clock_type):
        """Compute variance of normalized clocks across regions."""
        values = []
        for name in regions:
            arr = np.array(clocks[name][clock_type])
            if arr[-1] > arr[0]:
                normalized = (arr - arr[0]) / (arr[-1] - arr[0])
                values.append(normalized)
        
        if len(values) >= 2:
            stacked = np.vstack(values)
            variance = np.var(stacked, axis=0)
            return np.mean(variance)
        return 0.0
    
    disagreements = {}
    for clock_type in ['raw', 'transport', 'medium', 'mixed']:
        disagreements[clock_type] = compute_disagreement(clock_type)
        print(f"  {clock_type:10}: disagreement = {disagreements[clock_type]:.6f}")
    
    return {
        'clocks': clocks,
        'regions': regions,
        'disagreements': disagreements,
        'final_tau': sim.tau.copy(),
    }


def run_oscillator_test():
    """
    Test 3: Local oscillator clocks in different τ regions.
    """
    print("\nTest 3: Local Oscillator Clocks")
    print("-" * 50)
    
    sim = DynamicalMediumWithClocks(size=100)
    
    # Create energy concentration
    sim.add_pulse([50, 50], amplitude=5.0, velocity=False)
    
    # Let medium settle
    for _ in range(100):
        sim.step()
    
    # Define oscillator locations
    oscillators = {
        'high_tau': (50, 20),   # Far from energy, high τ
        'low_tau': (50, 50),    # At energy center, low τ
    }
    
    # Oscillator state: phase accumulates based on local frequency
    # Frequency depends on medium state: ω = ω_0 × τ / τ_0
    omega_0 = 1.0
    phases = {name: 0.0 for name in oscillators}
    cycles = {name: [] for name in oscillators}
    
    for t in range(500):
        sim.step()
        
        for name, (ri, rj) in oscillators.items():
            local_tau = sim.tau[ri, rj]
            omega = omega_0 * local_tau / sim.tau_0
            phases[name] += omega * sim.dt
        
        if t % 10 == 0:
            for name in oscillators:
                cycles[name].append(phases[name] / (2 * np.pi))
    
    # Compare cycle counts
    final_cycles = {name: cycles[name][-1] for name in oscillators}
    
    print(f"  high_τ region: {final_cycles['high_tau']:.2f} cycles")
    print(f"  low_τ region: {final_cycles['low_tau']:.2f} cycles")
    print(f"  Ratio: {final_cycles['high_tau'] / (final_cycles['low_tau'] + 1e-10):.3f}")
    
    return {
        'cycles': cycles,
        'final_cycles': final_cycles,
        'oscillators': oscillators,
    }


def run_medium_time_test():
    """
    Main test: Medium-state-based emergent time.
    """
    print("=" * 70)
    print("MEDIUM-STATE-BASED EMERGENT TIME TEST")
    print("=" * 70)
    print()
    print("Key question: Is time better described by τ than by ρ?")
    print()
    
    results = {}
    
    # Test 1: Clock comparison
    results['clock_comparison'] = run_clock_comparison_test()
    
    # Test 2: Multi-region synchronization
    results['synchronization'] = run_multi_region_synchronization()
    
    # Test 3: Oscillator clocks
    results['oscillators'] = run_oscillator_test()
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Which clock has lowest disagreement?
    disagreements = results['synchronization']['disagreements']
    best_clock = min(disagreements.keys(), key=lambda k: disagreements[k])
    
    print(f"\nBest synchronizing clock: {best_clock}")
    print(f"  Disagreement: {disagreements[best_clock]:.6f}")
    
    # Is medium-based clock better than transport?
    medium_better = disagreements['medium'] < disagreements['transport']
    mixed_better = disagreements['mixed'] < disagreements['transport']
    
    print(f"\nMedium clock < Transport: {medium_better}")
    print(f"Mixed clock < Transport: {mixed_better}")
    
    # Oscillator ratio
    osc = results['oscillators']
    osc_ratio = osc['final_cycles']['high_tau'] / (osc['final_cycles']['low_tau'] + 1e-10)
    
    print(f"\nOscillator cycle ratio (high_τ / low_τ): {osc_ratio:.3f}")
    
    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    if medium_better or mixed_better:
        verdict = "τ-BASED CLOCKS IMPROVE SYNCHRONIZATION"
        print(f"\n>>> {verdict}")
        print(">>> The dynamical medium provides better temporal observables")
    else:
        verdict = "TRANSPORT CLOCK REMAINS BEST"
        print(f"\n>>> {verdict}")
        print(">>> τ-based clocks do not clearly improve over transport")
    
    results['verdict'] = verdict
    results['medium_better'] = medium_better
    results['mixed_better'] = mixed_better
    
    # Plotting
    fig = plt.figure(figsize=(16, 12))
    
    # Clock evolution comparison
    ax = fig.add_subplot(2, 3, 1)
    sync = results['synchronization']
    for name in ['center', 'edge', 'corner']:
        ax.plot(sync['clocks'][name]['transport'], label=f'{name} (transport)')
    ax.set_xlabel('Steps')
    ax.set_ylabel('Transport Clock')
    ax.set_title('Transport Clock by Region')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Medium clock by region
    ax = fig.add_subplot(2, 3, 2)
    for name in ['center', 'edge', 'corner']:
        ax.plot(sync['clocks'][name]['medium'], label=f'{name} (medium)')
    ax.set_xlabel('Steps')
    ax.set_ylabel('Medium Clock')
    ax.set_title('Medium Clock by Region')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # τ field
    ax = fig.add_subplot(2, 3, 3)
    im = ax.imshow(sync['final_tau'].T, origin='lower', cmap='viridis')
    ax.set_title('Final Medium State τ')
    plt.colorbar(im, ax=ax, label='τ')
    
    # Disagreement comparison
    ax = fig.add_subplot(2, 3, 4)
    clocks = list(disagreements.keys())
    values = [disagreements[c] for c in clocks]
    colors = ['green' if c == best_clock else 'gray' for c in clocks]
    ax.bar(clocks, values, color=colors)
    ax.set_ylabel('Clock Disagreement')
    ax.set_title('Clock Synchronization Quality\n(lower = better)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Oscillator cycles
    ax = fig.add_subplot(2, 3, 5)
    osc = results['oscillators']
    for name in ['high_tau', 'low_tau']:
        ax.plot(osc['cycles'][name], label=name)
    ax.set_xlabel('Steps')
    ax.set_ylabel('Cycles')
    ax.set_title(f'Oscillator Cycles\n(ratio={osc_ratio:.2f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Summary
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
MEDIUM-STATE EMERGENT TIME
==========================

Clocks tested:
  raw: simulation time
  transport: ∫ c(τ) dt
  medium: ∫ (1/τ) dt
  mixed: ∫ c(τ)/τ dt

Clock disagreements:
  raw: {disagreements['raw']:.6f}
  transport: {disagreements['transport']:.6f}
  medium: {disagreements['medium']:.6f}
  mixed: {disagreements['mixed']:.6f}

Best clock: {best_clock}

Medium < Transport: {medium_better}
Mixed < Transport: {mixed_better}

Oscillator ratio: {osc_ratio:.2f}

VERDICT: {verdict}
"""
    ax.text(0.1, 0.9, summary, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', 
                    facecolor='lightgreen' if medium_better or mixed_better else 'lightyellow',
                    alpha=0.5))
    
    plt.suptitle(f'MEDIUM-STATE EMERGENT TIME: {verdict}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/medium_time.png', dpi=150, bbox_inches='tight')
    print("\nSaved medium_time.png")
    
    # Save JSON
    summary_json = {
        'verdict': verdict,
        'best_clock': best_clock,
        'disagreements': {k: float(v) for k, v in disagreements.items()},
        'medium_better_than_transport': bool(medium_better),
        'mixed_better_than_transport': bool(mixed_better),
        'oscillator_ratio': float(osc_ratio),
    }
    
    with open('/app/backend/qmrt_topology/medium_time_results.json', 'w') as f:
        json.dump(summary_json, f, indent=2)
    print("Saved medium_time_results.json")
    
    return results


if __name__ == "__main__":
    results = run_medium_time_test()
