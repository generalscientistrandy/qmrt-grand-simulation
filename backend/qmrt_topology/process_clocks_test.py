#!/usr/bin/env python3
"""
QMRT Process-Based Clocks Test
===============================

CORE RULE:
Clocks must be driven by local processes and only couple INDIRECTLY 
to the medium through interaction terms.

They must NOT be defined as:
- c_eff
- τ  
- any direct field integral

CLOCKS IMPLEMENTED:
1. Local Oscillator Clock: dθ/dt = ω₀ + ε|φ(xₚ)|
2. Event Interval Clock: count threshold crossings

KEY FIX:
Replace global ρ_max normalization with local Gaussian smoothing.

EQUATIONS:
----------
Medium:
  ∂τ/∂t = -λ(τ - τ_eq) + D∇²τ

Local equilibrium (FIXED - no global normalization):
  ρ_local = Gaussian_smooth(ρ, σ_local)
  τ_eq = τ₀ / (1 + β·ρ / (ρ_local + ε))

Wave:
  ∂²φ/∂t² = c(τ)²∇²φ - γ∂φ/∂t

Oscillator:
  dθ/dt = ω₀ + ε|φ(xₚ)|
  N_cycles = floor(θ / 2π)

Event detector:
  event when φ(xₚ, t) crosses threshold Φ_th upward
  Δt_k = t_k - t_{k-1}
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


class ProcessClockSimulator:
    """
    Simulator with process-based clocks and local normalization.
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
        # Local normalization parameters
        sigma_local: float = 8.0,  # Gaussian smoothing scale
        epsilon_local: float = 0.01,  # Regularization
        # Oscillator parameters
        omega_0: float = 1.0,  # Base frequency
        epsilon_coupling: float = 0.1,  # Coupling to |φ|
        # Event detector parameters
        phi_threshold: float = 0.5,  # Threshold for event detection
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        # Local normalization
        self.sigma_local = sigma_local
        self.epsilon_local = epsilon_local
        
        # Oscillator parameters
        self.omega_0 = omega_0
        self.epsilon_coupling = epsilon_coupling
        
        # Event detector
        self.phi_threshold = phi_threshold
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        # Time
        self.t = 0.0
        
        # Probe locations (to be set)
        self.probes = {}
        
        # Oscillator state: θ at each probe
        self.oscillator_phase = {}
        
        # Event detector state
        self.prev_phi = {}  # Previous φ value at each probe
        self.event_times = {}  # List of event times
        self.event_count = {}
        
        # History for analysis
        self.history = {
            'time': [],
            'oscillator_phase': {},
            'oscillator_cycles': {},
            'event_count': {},
            'phi_at_probes': {},
            'tau_at_probes': {},
        }
    
    def set_probes(self, probes: dict):
        """
        Set probe locations.
        probes = {'high_structure': (50, 50), 'edge': (50, 20), 'quiet': (20, 20)}
        """
        self.probes = probes
        for name in probes:
            self.oscillator_phase[name] = 0.0
            self.prev_phi[name] = 0.0
            self.event_times[name] = []
            self.event_count[name] = 0
            self.history['oscillator_phase'][name] = []
            self.history['oscillator_cycles'][name] = []
            self.history['event_count'][name] = []
            self.history['phi_at_probes'][name] = []
            self.history['tau_at_probes'][name] = []
    
    def compute_c_eff(self):
        """Wave speed from medium state: c = c₀ · τ / τ₀"""
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq_local(self, rho):
        """
        LOCAL equilibrium medium state (NO global normalization).
        
        τ_eq = τ₀ / (1 + β·ρ / (ρ_local + ε))
        
        where ρ_local = Gaussian_smooth(ρ, σ_local)
        """
        # Local smoothing instead of global max
        rho_local = gaussian_filter(rho, sigma=self.sigma_local)
        
        # Local normalization
        tau_eq = self.tau_0 / (1 + self.beta * rho / (rho_local + self.epsilon_local))
        
        return tau_eq
    
    def step(self):
        """Advance one timestep."""
        # Current energy density
        rho = self.phi**2 + self.phi_dot**2
        
        # 1. Update medium field with LOCAL normalization
        tau_eq = self.compute_tau_eq_local(rho)
        
        # Laplacian of τ
        lap_tau = (np.roll(self.tau, 1, axis=0) + np.roll(self.tau, -1, axis=0) +
                   np.roll(self.tau, 1, axis=1) + np.roll(self.tau, -1, axis=1) - 
                   4 * self.tau)
        
        # Medium relaxation
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # 2. Update wave field
        c_eff = self.compute_c_eff()
        
        lap_phi = (np.roll(self.phi, 1, axis=0) + np.roll(self.phi, -1, axis=0) +
                   np.roll(self.phi, 1, axis=1) + np.roll(self.phi, -1, axis=1) - 
                   4 * self.phi)
        
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
        
        # 3. Update oscillator clocks at each probe
        for name, (ri, rj) in self.probes.items():
            local_phi = self.phi[ri, rj]
            
            # Oscillator dynamics: dθ/dt = ω₀ + ε|φ|
            dtheta_dt = self.omega_0 + self.epsilon_coupling * np.abs(local_phi)
            self.oscillator_phase[name] += dtheta_dt * self.dt
        
        # 4. Update event detectors
        for name, (ri, rj) in self.probes.items():
            local_phi = self.phi[ri, rj]
            prev = self.prev_phi[name]
            
            # Detect upward threshold crossing
            if prev < self.phi_threshold and local_phi >= self.phi_threshold:
                self.event_times[name].append(self.t)
                self.event_count[name] += 1
            
            self.prev_phi[name] = local_phi
        
        # Update time
        self.t += self.dt
    
    def record_history(self):
        """Record current state for analysis."""
        self.history['time'].append(self.t)
        
        for name, (ri, rj) in self.probes.items():
            self.history['oscillator_phase'][name].append(self.oscillator_phase[name])
            self.history['oscillator_cycles'][name].append(
                int(self.oscillator_phase[name] / (2 * np.pi))
            )
            self.history['event_count'][name].append(self.event_count[name])
            self.history['phi_at_probes'][name].append(self.phi[ri, rj])
            self.history['tau_at_probes'][name].append(self.tau[ri, rj])
    
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


def run_process_clocks_test():
    """
    Main test: Process-based clocks with local normalization.
    """
    print("=" * 70)
    print("PROCESS-BASED CLOCKS TEST")
    print("=" * 70)
    print()
    print("Key changes from field-based clocks:")
    print("  1. Local normalization (no global ρ_max)")
    print("  2. Oscillator clock: dθ/dt = ω₀ + ε|φ|")
    print("  3. Event clock: threshold crossings")
    print()
    
    # Create simulator with local normalization
    sim = ProcessClockSimulator(
        size=100,
        beta=1.0,
        lambda_relax=1.5,
        sigma_local=8.0,  # Local smoothing scale
        omega_0=1.0,
        epsilon_coupling=0.1,
        phi_threshold=0.1,  # Lower threshold for more events
    )
    
    # Set up probes in three distinct regions
    probes = {
        'high_structure': (50, 50),  # Where we'll put energy
        'edge': (50, 25),            # Transition region
        'quiet': (25, 25),           # Far from energy source
    }
    sim.set_probes(probes)
    
    # Add energy concentration at high_structure region
    sim.add_pulse([50, 50], amplitude=5.0, velocity=False)
    
    # Let medium settle slightly
    print("Phase 1: Medium settling (50 steps)")
    for t in range(50):
        sim.step()
        if t % 10 == 0:
            sim.record_history()
    
    # Add propagating pulse to create events
    print("Phase 2: Adding propagating pulse")
    sim.add_pulse([50, 50], amplitude=3.0, velocity=True)
    
    # Run simulation
    print("Phase 3: Main simulation (600 steps)")
    for t in range(600):
        sim.step()
        if t % 5 == 0:
            sim.record_history()
    
    # Analysis
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    results = {}
    
    # 1. Oscillator clock analysis
    print("\n1. OSCILLATOR CLOCKS")
    print("-" * 50)
    
    osc_results = {}
    for name in probes:
        final_phase = sim.oscillator_phase[name]
        final_cycles = int(final_phase / (2 * np.pi))
        osc_results[name] = {
            'final_phase': float(final_phase),
            'final_cycles': int(final_cycles),
        }
        print(f"  {name:15}: θ = {final_phase:.2f} rad, cycles = {final_cycles}")
    
    # Check if cycles differ
    cycles = [osc_results[name]['final_cycles'] for name in probes]
    cycle_spread = int(max(cycles) - min(cycles))
    osc_divergent = cycle_spread >= 1
    print(f"\n  Cycle spread: {cycle_spread}")
    print(f"  Oscillators divergent: {osc_divergent}")
    
    results['oscillator'] = osc_results
    results['oscillator_divergent'] = bool(osc_divergent)
    
    # 2. Event clock analysis
    print("\n2. EVENT CLOCKS")
    print("-" * 50)
    
    event_results = {}
    for name in probes:
        count = sim.event_count[name]
        times = sim.event_times[name]
        
        # Compute intervals
        if len(times) >= 2:
            intervals = np.diff(times)
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
        else:
            intervals = []
            mean_interval = np.nan
            std_interval = np.nan
        
        event_results[name] = {
            'count': int(count),
            'mean_interval': float(mean_interval) if not np.isnan(mean_interval) else None,
            'std_interval': float(std_interval) if not np.isnan(std_interval) else None,
        }
        print(f"  {name:15}: events = {count}, mean_Δt = {mean_interval:.3f}" if not np.isnan(mean_interval) else f"  {name:15}: events = {count}")
    
    # Check if event counts differ
    counts = [event_results[name]['count'] for name in probes]
    count_spread = int(max(counts) - min(counts)) if max(counts) > 0 else 0
    events_divergent = count_spread >= 2
    print(f"\n  Event count spread: {count_spread}")
    print(f"  Events divergent: {events_divergent}")
    
    results['events'] = event_results
    results['events_divergent'] = bool(events_divergent)
    
    # 3. Pre-causal correlation test (key fix validation)
    print("\n3. LOCAL NORMALIZATION TEST")
    print("-" * 50)
    
    # Compare τ histories at different probes
    tau_histories = {}
    for name in probes:
        tau_histories[name] = np.array(sim.history['tau_at_probes'][name])
    
    # Compute correlation between probes
    if len(tau_histories['high_structure']) > 10:
        corr_hs_edge = np.corrcoef(
            tau_histories['high_structure'][10:],
            tau_histories['edge'][10:]
        )[0, 1]
        corr_hs_quiet = np.corrcoef(
            tau_histories['high_structure'][10:],
            tau_histories['quiet'][10:]
        )[0, 1]
    else:
        corr_hs_edge = 0.0
        corr_hs_quiet = 0.0
    
    print(f"  τ correlation (high_structure ↔ edge): {corr_hs_edge:.3f}")
    print(f"  τ correlation (high_structure ↔ quiet): {corr_hs_quiet:.3f}")
    
    # Compare to previous global normalization (was 1.0)
    local_norm_improvement = (1.0 - abs(corr_hs_quiet)) * 100
    print(f"\n  Decorrelation from global norm: {local_norm_improvement:.1f}%")
    
    local_norm_success = abs(corr_hs_quiet) < 0.9
    print(f"  Local normalization working: {local_norm_success}")
    
    results['tau_correlation_hs_edge'] = float(corr_hs_edge)
    results['tau_correlation_hs_quiet'] = float(corr_hs_quiet)
    results['local_norm_success'] = bool(local_norm_success)
    
    # 4. Phase/cycle histories
    print("\n4. OSCILLATOR PHASE DIVERGENCE")
    print("-" * 50)
    
    phase_histories = {}
    for name in probes:
        phase_histories[name] = np.array(sim.history['oscillator_phase'][name])
    
    # Compute phase difference over time
    phase_diff_hs_quiet = phase_histories['high_structure'] - phase_histories['quiet']
    
    if len(phase_diff_hs_quiet) > 1:
        initial_diff = phase_diff_hs_quiet[1] if len(phase_diff_hs_quiet) > 1 else 0
        final_diff = phase_diff_hs_quiet[-1]
        diff_growth = final_diff - initial_diff
    else:
        diff_growth = 0
    
    print(f"  Phase difference growth (high_structure - quiet): {diff_growth:.2f} rad")
    print(f"  Cycles difference: {diff_growth / (2 * np.pi):.2f}")
    
    results['phase_diff_growth'] = float(diff_growth)
    
    # 5. Final verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    # Pass criteria
    osc_pass = osc_divergent or (diff_growth > 1.0)
    event_pass = events_divergent
    local_pass = local_norm_success
    
    total_pass = sum([osc_pass, event_pass, local_pass])
    
    print(f"\n  Oscillator clock divergent: {'PASS' if osc_pass else 'FAIL'}")
    print(f"  Event clock divergent: {'PASS' if event_pass else 'FAIL'}")
    print(f"  Local normalization working: {'PASS' if local_pass else 'FAIL'}")
    print(f"\n  Score: {total_pass}/3")
    
    if total_pass >= 2:
        verdict = "PROCESS CLOCKS SHOW INDEPENDENT BEHAVIOR"
        verdict_short = "SUCCESS"
    elif total_pass >= 1:
        verdict = "PARTIAL: Some clock independence observed"
        verdict_short = "PARTIAL"
    else:
        verdict = "CLOCKS STILL COUPLED - need stronger differentiation"
        verdict_short = "FAIL"
    
    print(f"\n>>> {verdict}")
    
    results['verdict'] = verdict
    results['verdict_short'] = verdict_short
    results['score'] = int(total_pass)
    
    # Plotting
    fig = plt.figure(figsize=(16, 14))
    
    # 1. Oscillator phase evolution
    ax = fig.add_subplot(3, 3, 1)
    times = np.array(sim.history['time'])
    for name in probes:
        phases = np.array(sim.history['oscillator_phase'][name])
        ax.plot(times, phases, label=name, linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Oscillator Phase θ')
    ax.set_title('Oscillator Clock Evolution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Oscillator cycles
    ax = fig.add_subplot(3, 3, 2)
    for name in probes:
        cycles = np.array(sim.history['oscillator_cycles'][name])
        ax.plot(times, cycles, label=name, linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Cycle Count N')
    ax.set_title(f'Oscillator Cycles (spread={cycle_spread})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Event counts
    ax = fig.add_subplot(3, 3, 3)
    for name in probes:
        ecounts = np.array(sim.history['event_count'][name])
        ax.plot(times, ecounts, label=name, linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Event Count')
    ax.set_title(f'Event Clock (spread={count_spread})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. φ at probes
    ax = fig.add_subplot(3, 3, 4)
    for name in probes:
        phi_vals = np.array(sim.history['phi_at_probes'][name])
        ax.plot(times, phi_vals, label=name, linewidth=1.5, alpha=0.7)
    ax.axhline(y=sim.phi_threshold, color='k', linestyle='--', label='threshold')
    ax.set_xlabel('Time')
    ax.set_ylabel('φ')
    ax.set_title('Wave Field at Probes')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. τ at probes
    ax = fig.add_subplot(3, 3, 5)
    for name in probes:
        tau_vals = np.array(sim.history['tau_at_probes'][name])
        ax.plot(times, tau_vals, label=name, linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('τ')
    ax.set_title(f'Medium State (corr={corr_hs_quiet:.2f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Phase difference
    ax = fig.add_subplot(3, 3, 6)
    ax.plot(times, phase_diff_hs_quiet, 'b-', linewidth=2)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Time')
    ax.set_ylabel('Δθ (high_structure - quiet)')
    ax.set_title(f'Oscillator Phase Difference\n(growth={diff_growth:.2f} rad)')
    ax.grid(True, alpha=0.3)
    
    # 7. Final τ field
    ax = fig.add_subplot(3, 3, 7)
    im = ax.imshow(sim.tau.T, origin='lower', cmap='viridis')
    for name, (ri, rj) in probes.items():
        ax.scatter(ri, rj, c='red', s=100, marker='x', linewidths=2)
        ax.annotate(name, (ri, rj), color='white', fontsize=8)
    ax.set_title('Final Medium State τ')
    plt.colorbar(im, ax=ax, label='τ')
    
    # 8. Event interval histograms
    ax = fig.add_subplot(3, 3, 8)
    for name in probes:
        times_list = sim.event_times[name]
        if len(times_list) >= 2:
            intervals = np.diff(times_list)
            ax.hist(intervals, bins=15, alpha=0.5, label=name)
    ax.set_xlabel('Event Interval Δt')
    ax.set_ylabel('Count')
    ax.set_title('Event Interval Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 9. Summary
    ax = fig.add_subplot(3, 3, 9)
    ax.axis('off')
    
    summary = f"""
PROCESS-BASED CLOCKS TEST
=========================

Oscillator Clock:
  dθ/dt = ω₀ + ε|φ|
  
  Cycles (high_structure): {osc_results['high_structure']['final_cycles']}
  Cycles (edge): {osc_results['edge']['final_cycles']}
  Cycles (quiet): {osc_results['quiet']['final_cycles']}
  Phase diff growth: {diff_growth:.2f} rad

Event Clock:
  Events (high_structure): {event_results['high_structure']['count']}
  Events (edge): {event_results['edge']['count']}
  Events (quiet): {event_results['quiet']['count']}

Local Normalization:
  τ correlation (hs↔quiet): {corr_hs_quiet:.3f}
  (was 1.0 with global ρ_max)

RESULTS:
  Oscillator divergent: {'PASS' if osc_pass else 'FAIL'}
  Event divergent: {'PASS' if event_pass else 'FAIL'}
  Local norm working: {'PASS' if local_pass else 'FAIL'}
  Score: {total_pass}/3

VERDICT: {verdict_short}
"""
    
    color = 'lightgreen' if total_pass >= 2 else ('lightyellow' if total_pass >= 1 else 'lightcoral')
    ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'PROCESS-BASED CLOCKS: {verdict_short}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/process_clocks.png', dpi=150, bbox_inches='tight')
    print("\nSaved process_clocks.png")
    
    # Save JSON
    with open('/app/backend/qmrt_topology/process_clocks_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved process_clocks_results.json")
    
    return results


if __name__ == "__main__":
    results = run_process_clocks_test()
