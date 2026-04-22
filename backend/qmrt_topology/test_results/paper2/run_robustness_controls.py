#!/usr/bin/env python3
"""
Paper 2: Robustness Controls
============================
1. Energy-matched control (periodic vs random injection)
2. Correlation length measurement
3. Activity vs Organization metric
"""

import requests
import json
import numpy as np
from scipy.ndimage import correlate
import os
import time
from datetime import datetime

API_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://death-world-gen.preview.emergentagent.com')
API = f"{API_URL}/api"

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/paper2"


def run_custom_driving(steps, pulse_times, pulse_positions, pulse_amplitude, size=50, alpha=0.5, sample_interval=100):
    """
    Run simulation with custom pulse injection times and positions.
    This allows energy-matched comparison between periodic and random.
    
    We'll do this by calling the sustained driving endpoint multiple times
    and averaging, OR by implementing locally.
    """
    # For energy-matched control, we need to inject at specific times
    # Since the API doesn't support arbitrary pulse times, we'll compute locally
    
    # Import simulation classes
    import sys
    sys.path.insert(0, '/app/backend')
    from qmrt_simulation_api import QMRTSimulator2D, StructureTracker
    
    np.random.seed(42)
    
    sim = QMRTSimulator2D(
        size=size,
        beta=alpha,
        lambda_relax=0.5,
        gamma_wave=0.01,
    )
    sim.add_pulse(amplitude=3.0)  # Initial pulse
    
    tracker = StructureTracker(dimension='2d', match_threshold=5.0)
    
    time_series = []
    pulse_idx = 0
    
    for step in range(steps):
        sim.step()
        
        # Check if we should inject a pulse
        if pulse_idx < len(pulse_times) and step >= pulse_times[pulse_idx]:
            pos = pulse_positions[pulse_idx]
            sim.add_pulse(center=pos, amplitude=pulse_amplitude, width=4.0)
            pulse_idx += 1
        
        # Sample
        if step % sample_interval == 0:
            t = step * sim.dt
            structures = sim.detect_all_structures()
            tracker.process_frame(structures, t)
            
            measurement = sim.measure(t)
            rho = sim.phi**2 + sim.phi_dot**2
            
            # Compute correlation length
            xi = compute_correlation_length(sim.phi)
            
            time_series.append({
                't': t,
                'S': measurement['S_total'],
                'I_TS': measurement['I_TS'],
                'rho_mean': float(np.mean(rho)),
                'rho_std': float(np.std(rho)),
                'births': tracker.births,
                'deaths': tracker.deaths,
                'xi': xi,
                'total_structures': len(structures['strain_nodes']) + len(structures['coherence_clusters'])
            })
    
    return time_series


def compute_correlation_length(phi):
    """
    Compute spatial correlation length from field phi.
    Uses radial average of 2-point correlation function.
    Returns xi where C(r) drops to 1/e.
    """
    size = phi.shape[0]
    
    # Compute 2D autocorrelation via FFT
    phi_centered = phi - np.mean(phi)
    fft = np.fft.fft2(phi_centered)
    power = np.abs(fft)**2
    autocorr = np.real(np.fft.ifft2(power))
    autocorr = np.fft.fftshift(autocorr)
    autocorr = autocorr / autocorr.max()  # Normalize
    
    # Radial average
    center = size // 2
    y, x = np.ogrid[:size, :size]
    r = np.sqrt((x - center)**2 + (y - center)**2).astype(int)
    
    max_r = min(center, 20)  # Look up to 20 pixels
    radial_profile = []
    for ri in range(max_r):
        mask = r == ri
        if np.any(mask):
            radial_profile.append(np.mean(autocorr[mask]))
        else:
            radial_profile.append(0)
    
    radial_profile = np.array(radial_profile)
    
    # Find where it drops to 1/e
    threshold = 1/np.e
    xi = max_r  # Default if never drops
    for i, val in enumerate(radial_profile):
        if val < threshold:
            xi = i
            break
    
    return float(xi)


def energy_matched_control_experiment():
    """
    Compare:
    1. Undriven baseline
    2. Periodic driving
    3. Random driving (same total energy, random times/positions)
    """
    print("=" * 70)
    print("ENERGY-MATCHED CONTROL EXPERIMENT")
    print("=" * 70)
    
    steps = 30000
    sample_interval = 100
    size = 50
    alpha = 0.5
    
    # Periodic driving: every 1000 steps, 30 pulses total
    n_pulses = 29
    pulse_amplitude = 2.0
    
    # --- 1. Undriven ---
    print("\n1. UNDRIVEN BASELINE")
    print("-" * 40)
    
    undriven_times = []  # No pulses
    undriven_positions = []
    
    ts_undriven = run_custom_driving(
        steps, undriven_times, undriven_positions, 
        pulse_amplitude, size, alpha, sample_interval
    )
    
    S_late_undriven = np.mean([p['S'] for p in ts_undriven[-50:]])
    I_TS_late_undriven = np.mean([p['I_TS'] for p in ts_undriven[-50:]])
    xi_late_undriven = np.mean([p['xi'] for p in ts_undriven[-50:]])
    
    print(f"  S (late): {S_late_undriven:.2e}")
    print(f"  I_TS (late): {I_TS_late_undriven:.4f}")
    print(f"  ξ (late): {xi_late_undriven:.2f}")
    
    # --- 2. Periodic driving ---
    print("\n2. PERIODIC DRIVING")
    print("-" * 40)
    
    periodic_times = [1000 * (i+1) for i in range(n_pulses)]
    periodic_positions = [(size//2 + np.random.randint(-15, 15), 
                          size//2 + np.random.randint(-15, 15)) 
                         for _ in range(n_pulses)]
    
    np.random.seed(42)
    ts_periodic = run_custom_driving(
        steps, periodic_times, periodic_positions,
        pulse_amplitude, size, alpha, sample_interval
    )
    
    S_late_periodic = np.mean([p['S'] for p in ts_periodic[-50:]])
    I_TS_late_periodic = np.mean([p['I_TS'] for p in ts_periodic[-50:]])
    xi_late_periodic = np.mean([p['xi'] for p in ts_periodic[-50:]])
    
    print(f"  S (late): {S_late_periodic:.6f}")
    print(f"  I_TS (late): {I_TS_late_periodic:.4f}")
    print(f"  ξ (late): {xi_late_periodic:.2f}")
    
    # --- 3. Random driving (energy-matched) ---
    print("\n3. RANDOM DRIVING (energy-matched)")
    print("-" * 40)
    
    # Same number of pulses, same amplitude, but random times
    np.random.seed(123)
    random_times = sorted(np.random.randint(100, steps-100, n_pulses).tolist())
    random_positions = [(np.random.randint(10, size-10), 
                        np.random.randint(10, size-10)) 
                       for _ in range(n_pulses)]
    
    np.random.seed(42)  # Reset for simulation
    ts_random = run_custom_driving(
        steps, random_times, random_positions,
        pulse_amplitude, size, alpha, sample_interval
    )
    
    S_late_random = np.mean([p['S'] for p in ts_random[-50:]])
    I_TS_late_random = np.mean([p['I_TS'] for p in ts_random[-50:]])
    xi_late_random = np.mean([p['xi'] for p in ts_random[-50:]])
    
    print(f"  S (late): {S_late_random:.6f}")
    print(f"  I_TS (late): {I_TS_late_random:.4f}")
    print(f"  ξ (late): {xi_late_random:.2f}")
    
    # --- Summary ---
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print()
    print(f"{'Condition':<20} {'S_late':>12} {'I_TS':>10} {'ξ':>8}")
    print("-" * 50)
    print(f"{'Undriven':<20} {S_late_undriven:>12.2e} {I_TS_late_undriven:>10.4f} {xi_late_undriven:>8.2f}")
    print(f"{'Periodic':<20} {S_late_periodic:>12.6f} {I_TS_late_periodic:>10.4f} {xi_late_periodic:>8.2f}")
    print(f"{'Random (matched)':<20} {S_late_random:>12.6f} {I_TS_late_random:>10.4f} {xi_late_random:>8.2f}")
    print()
    
    # Ratios
    print("RATIOS:")
    print(f"  Periodic / Undriven S: {S_late_periodic / (S_late_undriven + 1e-20):.2e}")
    print(f"  Random / Undriven S:   {S_late_random / (S_late_undriven + 1e-20):.2e}")
    print(f"  Periodic / Random S:   {S_late_periodic / (S_late_random + 1e-10):.2f}")
    print()
    
    # Interpretation
    if S_late_periodic > S_late_random * 1.5:
        interp = "PERIODIC > RANDOM: Structure in driving matters, not just energy"
    elif S_late_random > S_late_periodic * 1.5:
        interp = "RANDOM > PERIODIC: Unexpected - random driving more effective"
    else:
        interp = "PERIODIC ≈ RANDOM: Energy magnitude matters more than structure"
    
    print(f"INTERPRETATION: {interp}")
    
    return {
        'undriven': {'S': S_late_undriven, 'I_TS': I_TS_late_undriven, 'xi': xi_late_undriven},
        'periodic': {'S': S_late_periodic, 'I_TS': I_TS_late_periodic, 'xi': xi_late_periodic},
        'random': {'S': S_late_random, 'I_TS': I_TS_late_random, 'xi': xi_late_random},
        'interpretation': interp,
        'ts_undriven': ts_undriven,
        'ts_periodic': ts_periodic,
        'ts_random': ts_random
    }


def activity_vs_organization_analysis(ts_undriven, ts_periodic):
    """
    Show that activity persists while organization decays (undriven)
    vs both persist (driven).
    """
    print("\n" + "=" * 70)
    print("ACTIVITY vs ORGANIZATION ANALYSIS")
    print("=" * 70)
    
    # Activity index: (births + deaths) / time
    def compute_activity(ts):
        if len(ts) < 2:
            return []
        activities = []
        for i in range(1, len(ts)):
            dt = ts[i]['t'] - ts[i-1]['t']
            if dt > 0:
                activity = (ts[i]['births'] - ts[i-1]['births'] + 
                           ts[i]['deaths'] - ts[i-1]['deaths']) / dt
                activities.append(activity)
        return activities
    
    activity_undriven = compute_activity(ts_undriven)
    activity_periodic = compute_activity(ts_periodic)
    
    S_undriven = [p['S'] for p in ts_undriven]
    S_periodic = [p['S'] for p in ts_periodic]
    
    n = len(ts_undriven)
    early = slice(0, n//5)
    late = slice(4*n//5, n)
    
    print("\nUNDRIVEN:")
    print("-" * 40)
    print(f"  Activity (early): {np.mean(activity_undriven[:len(activity_undriven)//5]):.2f}")
    print(f"  Activity (late):  {np.mean(activity_undriven[4*len(activity_undriven)//5:]):.2f}")
    print(f"  S (early):        {np.mean(S_undriven[early]):.6f}")
    print(f"  S (late):         {np.mean(S_undriven[late]):.2e}")
    
    print("\nPERIODIC DRIVING:")
    print("-" * 40)
    print(f"  Activity (early): {np.mean(activity_periodic[:len(activity_periodic)//5]):.2f}")
    print(f"  Activity (late):  {np.mean(activity_periodic[4*len(activity_periodic)//5:]):.2f}")
    print(f"  S (early):        {np.mean(S_periodic[early]):.6f}")
    print(f"  S (late):         {np.mean(S_periodic[late]):.6f}")
    
    print("\nKEY COMPARISON:")
    print("-" * 40)
    
    activity_ratio_undriven = (np.mean(activity_undriven[4*len(activity_undriven)//5:]) / 
                               (np.mean(activity_undriven[:len(activity_undriven)//5]) + 0.01))
    S_ratio_undriven = np.mean(S_undriven[late]) / (np.mean(S_undriven[early]) + 1e-10)
    
    print(f"  UNDRIVEN late/early ratios:")
    print(f"    Activity: {activity_ratio_undriven:.2f} (persists)")
    print(f"    S:        {S_ratio_undriven:.2e} (decays)")
    
    if activity_ratio_undriven > 0.5 and S_ratio_undriven < 0.01:
        print("\n  ✓ ACTIVITY ≠ ORGANIZATION confirmed")
        print("    Activity persists while organization decays")
    
    return {
        'activity_undriven': activity_undriven,
        'activity_periodic': activity_periodic,
        'S_undriven': S_undriven,
        'S_periodic': S_periodic
    }


def duty_cycle_analysis():
    """
    Create duty-cycle / power parameter space for driven regime.
    """
    print("\n" + "=" * 70)
    print("DUTY CYCLE ANALYSIS")
    print("=" * 70)
    
    # We'll use API for this since it's faster
    import requests
    
    results = []
    
    # Grid of (interval, amplitude)
    intervals = [500, 1000, 2000, 4000]
    amplitudes = [1.0, 2.0, 3.0]
    
    steps = 20000
    
    for interval in intervals:
        for amp in amplitudes:
            # Duty cycle: pulse_duration / interval (assume pulse_duration ~ 100 steps)
            duty = 100 / interval
            # Power: amplitude^2 / interval (energy rate)
            power = amp**2 / interval
            
            try:
                response = requests.post(
                    f"{API}/qmrt-sim/longpath/sustained-driving",
                    json={
                        "dimension": "2d",
                        "size": 50,
                        "alpha": 0.5,
                        "steps": steps,
                        "sample_interval": 100,
                        "pulse_interval": interval,
                        "pulse_amplitude": amp,
                        "seed": 42
                    },
                    timeout=60
                )
                data = response.json()
                S_late = data['driven_S_late']
                I_TS_late = data['driven_I_TS_late']
            except:
                S_late = None
                I_TS_late = None
            
            results.append({
                'interval': interval,
                'amplitude': amp,
                'duty': duty,
                'power': power,
                'S_late': S_late,
                'I_TS_late': I_TS_late
            })
            
            print(f"  interval={interval}, amp={amp}: S={S_late:.6f}" if S_late else f"  interval={interval}, amp={amp}: S=N/A")
    
    print("\nDUTY CYCLE TABLE:")
    print("-" * 60)
    print(f"{'Interval':>8} {'Amp':>6} {'Duty':>8} {'Power':>10} {'S_late':>12}")
    print("-" * 60)
    for r in results:
        if r['S_late']:
            print(f"{r['interval']:>8} {r['amplitude']:>6.1f} {r['duty']:>8.3f} {r['power']:>10.4f} {r['S_late']:>12.6f}")
    
    return results


def main():
    print("=" * 70)
    print("PAPER 2: ROBUSTNESS CONTROLS")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    # 1. Energy-matched control
    control_results = energy_matched_control_experiment()
    
    # 2. Activity vs Organization
    activity_results = activity_vs_organization_analysis(
        control_results['ts_undriven'],
        control_results['ts_periodic']
    )
    
    # 3. Duty cycle sweep
    duty_results = duty_cycle_analysis()
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'energy_matched_control': {
            'undriven': control_results['undriven'],
            'periodic': control_results['periodic'],
            'random': control_results['random'],
            'interpretation': control_results['interpretation']
        },
        'duty_cycle': duty_results
    }
    
    output_file = f"{OUTPUT_DIR}/robustness_controls.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
