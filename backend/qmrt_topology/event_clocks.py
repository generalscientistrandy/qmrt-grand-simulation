#!/usr/bin/env python3
"""
QMRT Event-Interval Clocks
===========================

Test discrete event-based clocks (threshold crossings) with the three questions:

1. Does the clock exist locally? (Do events occur at different rates in different regions?)
2. Does it improve collapse? (Does parameterizing by event count help?)
3. Does forcing agreement help or hurt? (Does coupling event detectors reduce information?)

EVENT CLOCK DEFINITION:
  Event occurs when φ(xᵢ, t) crosses threshold Φ_th upward
  N_events(xᵢ) = count of threshold crossings
  Δt_k = interval between event k and k+1
  τ_event = N_events (discrete event time)

This is fundamentally different from oscillators:
- Oscillators: continuous phase accumulation
- Events: discrete, triggered by actual wave dynamics
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import interp1d
import json


class EventClockSimulator:
    """
    Simulator with event-interval clocks.
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        beta: float = 1.0,
        lambda_relax: float = 1.5,
        D_medium: float = 0.1,
        gamma_wave: float = 0.008,
        dt: float = 0.04,
        # Event detector parameters
        phi_threshold: float = 0.2,
        # Event coupling (for test 3)
        kappa_event: float = 0.0,  # Coupling between event detectors
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        self.phi_threshold = phi_threshold
        self.kappa_event = kappa_event
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
        self.t_sim = 0.0
        self.probes = {}
        
        # Event state
        self.prev_phi = {}
        self.event_times = {}
        self.event_count = {}
        self.effective_threshold = {}  # Can be modified by coupling
        
        self.history = {'t_sim': []}
    
    def set_probes(self, probes: dict):
        self.probes = probes
        for name in probes:
            self.prev_phi[name] = 0.0
            self.event_times[name] = []
            self.event_count[name] = 0
            self.effective_threshold[name] = self.phi_threshold
            self.history[f'event_count_{name}'] = []
            self.history[f'phi_{name}'] = []
            self.history[f'tau_event_{name}'] = []
    
    def compute_c_eff(self):
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
        """Advance with event detection."""
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
        
        probe_names = list(self.probes.keys())
        
        # Event coupling: adjust thresholds based on other detectors
        if self.kappa_event > 0:
            mean_count = np.mean([self.event_count[name] for name in probe_names])
            for name in probe_names:
                # Lower threshold if behind, raise if ahead
                deviation = self.event_count[name] - mean_count
                self.effective_threshold[name] = self.phi_threshold + self.kappa_event * deviation * 0.1
                self.effective_threshold[name] = np.clip(self.effective_threshold[name], 0.05, 0.5)
        
        # Event detection at each probe
        for name, (ri, rj) in self.probes.items():
            local_phi = self.phi[ri, rj]
            prev = self.prev_phi[name]
            threshold = self.effective_threshold[name]
            
            # Detect upward threshold crossing
            if prev < threshold and local_phi >= threshold:
                self.event_times[name].append(self.t_sim)
                self.event_count[name] += 1
            
            self.prev_phi[name] = local_phi
        
        self.t_sim += self.dt
    
    def record_history(self):
        self.history['t_sim'].append(self.t_sim)
        
        for name, (ri, rj) in self.probes.items():
            self.history[f'event_count_{name}'].append(self.event_count[name])
            self.history[f'phi_{name}'].append(self.phi[ri, rj])
            # Event time = event count (discrete)
            self.history[f'tau_event_{name}'].append(self.event_count[name])
    
    def add_pulse(self, center, amplitude=3.0, width=4.0, velocity=True):
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    if velocity:
                        self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
                    else:
                        self.phi[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))


def compute_event_metrics(history, probe_names):
    """Compute event clock metrics."""
    
    results = {}
    
    # Final event counts
    final_counts = {name: history[f'event_count_{name}'][-1] for name in probe_names}
    results['final_counts'] = {name: int(final_counts[name]) for name in probe_names}
    
    # Event count spread (Question 1: do events occur at different rates?)
    counts = list(final_counts.values())
    count_spread = max(counts) - min(counts) if counts else 0
    results['count_spread'] = int(count_spread)
    results['events_exist_locally'] = bool(count_spread >= 2)
    
    # Compute collapse quality (Question 2)
    t_sim = np.array(history['t_sim'])
    tau_event = {name: np.array(history[f'tau_event_{name}']) for name in probe_names}
    phi = {name: np.array(history[f'phi_{name}']) for name in probe_names}
    
    # Observable: smoothed |φ|
    phi_abs = {name: np.abs(phi[name]) for name in probe_names}
    
    # Variance under t_sim
    obs_stack = np.vstack([phi_abs[name] for name in probe_names])
    variance_t_sim = np.mean(np.var(obs_stack, axis=0))
    
    # Variance under tau_event (discrete, so need careful handling)
    # Only valid where event counts differ
    event_mins = [np.min(tau_event[name]) for name in probe_names]
    event_maxs = [np.max(tau_event[name]) for name in probe_names]
    event_common_min = max(event_mins)
    event_common_max = min(event_maxs)
    
    if event_common_max > event_common_min + 1:
        # Interpolate onto common event count grid
        event_common = np.arange(event_common_min, event_common_max + 1)
        
        interpolated = []
        for name in probe_names:
            # Sort by event count
            sort_idx = np.argsort(tau_event[name])
            event_sorted = tau_event[name][sort_idx]
            obs_sorted = phi_abs[name][sort_idx]
            
            try:
                f = interp1d(event_sorted, obs_sorted, kind='linear',
                            bounds_error=False, fill_value='extrapolate')
                interpolated.append(f(event_common))
            except:
                pass
        
        if len(interpolated) >= 2:
            variance_tau_event = np.mean(np.var(np.vstack(interpolated), axis=0))
        else:
            variance_tau_event = variance_t_sim
    else:
        variance_tau_event = variance_t_sim
    
    improvement = (variance_t_sim - variance_tau_event) / variance_t_sim * 100 if variance_t_sim > 0 else 0
    
    results['variance_t_sim'] = float(variance_t_sim)
    results['variance_tau_event'] = float(variance_tau_event)
    results['improvement_pct'] = float(improvement)
    results['improves_collapse'] = bool(improvement > 10)
    
    return results


def run_event_clock_test():
    """
    Test event-interval clocks with the three questions.
    """
    print("=" * 70)
    print("EVENT-INTERVAL CLOCKS TEST")
    print("=" * 70)
    print()
    print("Three questions:")
    print("  1. Does the clock exist locally? (Different event rates?)")
    print("  2. Does it improve collapse?")
    print("  3. Does forcing agreement help or hurt?")
    print()
    
    probes = {
        'high_activity': (40, 40),
        'edge': (40, 20),
        'quiet': (20, 20),
    }
    probe_names = list(probes.keys())
    
    # Test configurations
    configs = [
        {'name': 'Independent (κ=0)', 'kappa_event': 0.0},
        {'name': 'Weak coupling (κ=0.2)', 'kappa_event': 0.2},
        {'name': 'Medium coupling (κ=0.5)', 'kappa_event': 0.5},
        {'name': 'Strong coupling (κ=1.0)', 'kappa_event': 1.0},
    ]
    
    all_results = []
    
    for config in configs:
        print(f"\nRunning: {config['name']}")
        print("-" * 50)
        
        sim = EventClockSimulator(
            size=80,
            beta=1.0,
            lambda_relax=1.5,
            phi_threshold=0.05,  # Lower threshold for more events
            kappa_event=config['kappa_event'],
        )
        sim.set_probes(probes)
        
        # Add stationary energy
        sim.add_pulse([40, 40], amplitude=4.0, velocity=False)
        
        # Settle
        for _ in range(30):
            sim.step()
        
        # Add multiple propagating pulses for more events
        for t_pulse in range(8):  # More pulses
            if t_pulse > 0:
                for _ in range(80):
                    sim.step()
                    if _ % 4 == 0:
                        sim.record_history()
            sim.add_pulse([40, 40], amplitude=3.0, velocity=True)  # Stronger pulses
        
        # Final run
        for t in range(200):
            sim.step()
            if t % 5 == 0:
                sim.record_history()
        
        metrics = compute_event_metrics(sim.history, probe_names)
        metrics['config'] = config['name']
        metrics['kappa_event'] = config['kappa_event']
        all_results.append(metrics)
        
        print(f"  Event counts: {metrics['final_counts']}")
        print(f"  Count spread: {metrics['count_spread']}")
        print(f"  Q1 - Events exist locally: {metrics['events_exist_locally']}")
        print(f"  Q2 - Collapse improvement: {metrics['improvement_pct']:.1f}%")
        print(f"  Q2 - Improves collapse: {metrics['improves_collapse']}")
    
    # Question 3 analysis
    print("\n" + "=" * 70)
    print("QUESTION 3: Does forcing agreement help or hurt?")
    print("=" * 70)
    
    independent_result = all_results[0]
    coupled_results = all_results[1:]
    
    print(f"\n  Independent collapse: {independent_result['improvement_pct']:.1f}%")
    for r in coupled_results:
        delta = r['improvement_pct'] - independent_result['improvement_pct']
        direction = "HELPS" if delta > 2 else "HURTS" if delta < -2 else "NEUTRAL"
        print(f"  {r['config']}: {r['improvement_pct']:.1f}% ({delta:+.1f}% → {direction})")
    
    # Overall verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    q1_pass = independent_result['events_exist_locally']
    q2_pass = independent_result['improves_collapse']
    
    # Q3: Does any coupling help?
    best_coupled = max([r['improvement_pct'] for r in coupled_results])
    q3_coupling_helps = best_coupled > independent_result['improvement_pct'] + 2
    q3_coupling_hurts = all([r['improvement_pct'] < independent_result['improvement_pct'] - 2 for r in coupled_results])
    
    print(f"\n  Q1 - Clock exists locally: {'PASS' if q1_pass else 'FAIL'}")
    print(f"  Q2 - Improves collapse: {'PASS' if q2_pass else 'FAIL'}")
    print(f"  Q3 - Coupling helps: {'YES' if q3_coupling_helps else 'NO'}")
    print(f"  Q3 - Coupling hurts: {'YES' if q3_coupling_hurts else 'NO'}")
    
    if q1_pass and q2_pass:
        if q3_coupling_hurts:
            verdict = "EVENT CLOCKS WORK, COUPLING HURTS (like oscillators)"
            verdict_short = "WORKS_COUPLING_HURTS"
        elif q3_coupling_helps:
            verdict = "EVENT CLOCKS WORK, COUPLING HELPS"
            verdict_short = "WORKS_COUPLING_HELPS"
        else:
            verdict = "EVENT CLOCKS WORK, COUPLING NEUTRAL"
            verdict_short = "WORKS_COUPLING_NEUTRAL"
    elif q1_pass:
        verdict = "EVENT CLOCKS EXIST BUT DON'T IMPROVE COLLAPSE"
        verdict_short = "EXISTS_NO_COLLAPSE"
    else:
        verdict = "EVENT CLOCKS NOT DIFFERENTIATED"
        verdict_short = "NOT_DIFFERENTIATED"
    
    print(f"\n>>> {verdict}")
    
    # Plotting
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Event counts by config
    ax = fig.add_subplot(2, 3, 1)
    x = np.arange(len(probe_names))
    width = 0.2
    for i, r in enumerate(all_results):
        counts = [r['final_counts'][name] for name in probe_names]
        ax.bar(x + i*width, counts, width, label=r['config'])
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(probe_names)
    ax.set_ylabel('Event Count')
    ax.set_title('Event Counts by Region')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 2. Collapse improvement
    ax = fig.add_subplot(2, 3, 2)
    names = [r['config'] for r in all_results]
    improvements = [r['improvement_pct'] for r in all_results]
    colors = ['green' if imp > 10 else 'orange' if imp > 0 else 'red' for imp in improvements]
    ax.barh(names, improvements, color=colors)
    ax.axvline(x=10, color='k', linestyle='--', alpha=0.5, label='10% threshold')
    ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    ax.set_xlabel('Collapse Improvement (%)')
    ax.set_title('Q2: Collapse Quality')
    ax.legend()
    
    # 3. Count spread vs coupling
    ax = fig.add_subplot(2, 3, 3)
    kappas = [r['kappa_event'] for r in all_results]
    spreads = [r['count_spread'] for r in all_results]
    ax.plot(kappas, spreads, 'o-', linewidth=2, markersize=10)
    ax.set_xlabel('Event Coupling κ')
    ax.set_ylabel('Event Count Spread')
    ax.set_title('Q3: Does Coupling Reduce Spread?')
    ax.grid(True, alpha=0.3)
    
    # 4. Improvement vs coupling
    ax = fig.add_subplot(2, 3, 4)
    ax.plot(kappas, improvements, 'o-', linewidth=2, markersize=10, color='green')
    ax.axhline(y=improvements[0], color='blue', linestyle='--', alpha=0.5, label=f'Independent ({improvements[0]:.1f}%)')
    ax.axhline(y=10, color='k', linestyle='--', alpha=0.3, label='10% threshold')
    ax.set_xlabel('Event Coupling κ')
    ax.set_ylabel('Collapse Improvement (%)')
    ax.set_title('Q3: Does Coupling Help Collapse?')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Event count evolution (independent)
    ax = fig.add_subplot(2, 3, 5)
    # Re-run independent for history
    sim_viz = EventClockSimulator(size=80, beta=1.0, phi_threshold=0.15, kappa_event=0.0)
    sim_viz.set_probes(probes)
    sim_viz.add_pulse([40, 40], amplitude=4.0, velocity=False)
    for _ in range(30):
        sim_viz.step()
    for t_pulse in [0, 100, 200]:
        if t_pulse > 0:
            for _ in range(100):
                sim_viz.step()
                if _ % 5 == 0:
                    sim_viz.record_history()
        sim_viz.add_pulse([40, 40], amplitude=2.5, velocity=True)
    for t in range(100):
        sim_viz.step()
        if t % 5 == 0:
            sim_viz.record_history()
    
    t_sim = np.array(sim_viz.history['t_sim'])
    for name in probe_names:
        counts = np.array(sim_viz.history[f'event_count_{name}'])
        ax.plot(t_sim, counts, label=name, linewidth=2)
    ax.set_xlabel('t_sim')
    ax.set_ylabel('Event Count')
    ax.set_title('Event Clock Evolution (Independent)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Summary
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
EVENT-INTERVAL CLOCKS TEST
==========================

Event definition:
  Trigger when φ crosses threshold upward

Q1: Clock exists locally?
  Count spread: {independent_result['count_spread']}
  Answer: {'YES' if q1_pass else 'NO'}

Q2: Improves collapse?
  Independent: {independent_result['improvement_pct']:.1f}%
  Answer: {'YES' if q2_pass else 'NO'}

Q3: Coupling helps or hurts?
  Independent: {independent_result['improvement_pct']:.1f}%
  Best coupled: {best_coupled:.1f}%
  Answer: {'HELPS' if q3_coupling_helps else 'HURTS' if q3_coupling_hurts else 'NEUTRAL'}

VERDICT: {verdict_short}

Comparison to oscillators:
  Oscillator (indep): 11.2%
  Event (indep): {independent_result['improvement_pct']:.1f}%
"""
    
    color = 'lightgreen' if q1_pass and q2_pass else 'lightyellow' if q1_pass else 'lightcoral'
    ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'EVENT-INTERVAL CLOCKS: {verdict_short}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/event_clocks.png', dpi=150, bbox_inches='tight')
    print("\nSaved event_clocks.png")
    
    # Save JSON
    results_json = {
        'configs': all_results,
        'q1_events_exist': bool(q1_pass),
        'q2_improves_collapse': bool(q2_pass),
        'q3_coupling_helps': bool(q3_coupling_helps),
        'q3_coupling_hurts': bool(q3_coupling_hurts),
        'verdict': verdict,
        'verdict_short': verdict_short,
    }
    
    with open('/app/backend/qmrt_topology/event_clocks_results.json', 'w') as f:
        json.dump(results_json, f, indent=2)
    print("Saved event_clocks_results.json")
    
    return results_json


if __name__ == "__main__":
    results = run_event_clock_test()
