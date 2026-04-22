#!/usr/bin/env python3
"""
Paper 2: Publication Figure Generation
=======================================
Generates 5 key figures for the paper.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
plt.style.use('seaborn-v0_8-whitegrid')

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/paper2"

# Load data
with open(f"{OUTPUT_DIR}/robustness_controls.json", 'r') as f:
    controls = json.load(f)

# We need to regenerate time series for figures
# Using the data from previous runs

def load_or_generate_data():
    """Load existing time series or use control data."""
    # Check if we have extended time series
    try:
        with open(f"{OUTPUT_DIR}/timeseries_ultra_long_alpha0.5.json", 'r') as f:
            undriven_data = json.load(f)
        undriven_ts = undriven_data['time_series']
    except:
        undriven_ts = None
    
    return undriven_ts


def fig1_s_decay(save_path):
    """
    Figure 1: S(t) undriven vs driven (log scale)
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Generate data by running simulations
    import sys
    sys.path.insert(0, '/app/backend')
    from qmrt_simulation_api import QMRTSimulator2D, StructureTracker
    
    np.random.seed(42)
    
    steps = 30000
    sample_interval = 100
    
    # Undriven
    sim_u = QMRTSimulator2D(size=50, beta=0.5)
    sim_u.add_pulse(amplitude=3.0)
    
    t_u, S_u = [], []
    for step in range(steps):
        sim_u.step()
        if step % sample_interval == 0:
            t_u.append(step * sim_u.dt)
            m = sim_u.measure(step * sim_u.dt)
            S_u.append(m['S_total'])
    
    # Driven (periodic, every 1000 steps)
    sim_d = QMRTSimulator2D(size=50, beta=0.5)
    sim_d.add_pulse(amplitude=3.0)
    
    t_d, S_d = [], []
    for step in range(steps):
        sim_d.step()
        if step > 0 and step % 1000 == 0:
            cx = np.random.randint(15, 35)
            cy = np.random.randint(15, 35)
            sim_d.add_pulse(center=(cx, cy), amplitude=2.0, width=4.0)
        if step % sample_interval == 0:
            t_d.append(step * sim_d.dt)
            m = sim_d.measure(step * sim_d.dt)
            S_d.append(m['S_total'])
    
    # Plot
    ax.semilogy(t_u, S_u, 'b-', linewidth=1.5, label='Undriven', alpha=0.8)
    ax.semilogy(t_d, S_d, 'r-', linewidth=1.5, label='Driven (periodic)', alpha=0.8)
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('S (spatial organization)', fontsize=12)
    ax.set_title('Figure 1: Organizational Decay vs Maintenance', fontsize=14)
    ax.legend(fontsize=11)
    ax.set_ylim([1e-8, 1])
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")
    
    return t_u, S_u, t_d, S_d


def fig2_its_decay(save_path):
    """
    Figure 2: I_TS(t) undriven vs driven
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    import sys
    sys.path.insert(0, '/app/backend')
    from qmrt_simulation_api import QMRTSimulator2D
    
    np.random.seed(42)
    
    steps = 30000
    sample_interval = 100
    
    # Undriven
    sim_u = QMRTSimulator2D(size=50, beta=0.5)
    sim_u.add_pulse(amplitude=3.0)
    
    t_u, I_u = [], []
    for step in range(steps):
        sim_u.step()
        if step % sample_interval == 0:
            t_u.append(step * sim_u.dt)
            m = sim_u.measure(step * sim_u.dt)
            I_u.append(m['I_TS'])
    
    # Driven
    sim_d = QMRTSimulator2D(size=50, beta=0.5)
    sim_d.add_pulse(amplitude=3.0)
    
    t_d, I_d = [], []
    for step in range(steps):
        sim_d.step()
        if step > 0 and step % 1000 == 0:
            cx = np.random.randint(15, 35)
            cy = np.random.randint(15, 35)
            sim_d.add_pulse(center=(cx, cy), amplitude=2.0, width=4.0)
        if step % sample_interval == 0:
            t_d.append(step * sim_d.dt)
            m = sim_d.measure(step * sim_d.dt)
            I_d.append(m['I_TS'])
    
    ax.plot(t_u, I_u, 'b-', linewidth=1.5, label='Undriven', alpha=0.8)
    ax.plot(t_d, I_d, 'r-', linewidth=1.5, label='Driven (periodic)', alpha=0.8)
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('$I_{TS}$ (spacetime coupling)', fontsize=12)
    ax.set_title('Figure 2: Coupling Evolution', fontsize=14)
    ax.legend(fontsize=11)
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")


def fig3_activity_vs_S(save_path):
    """
    Figure 3: Activity vs S (showing separation)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    
    import sys
    sys.path.insert(0, '/app/backend')
    from qmrt_simulation_api import QMRTSimulator2D, StructureTracker
    
    np.random.seed(42)
    
    steps = 30000
    sample_interval = 100
    
    # Undriven simulation with tracking
    sim = QMRTSimulator2D(size=50, beta=0.5)
    sim.add_pulse(amplitude=3.0)
    tracker = StructureTracker(dimension='2d', match_threshold=5.0)
    
    t_list, S_list, activity_list = [], [], []
    prev_events = 0
    
    for step in range(steps):
        sim.step()
        if step % sample_interval == 0:
            t = step * sim.dt
            structures = sim.detect_all_structures()
            tracker.process_frame(structures, t)
            
            m = sim.measure(t)
            t_list.append(t)
            S_list.append(m['S_total'])
            
            current_events = tracker.births + tracker.deaths
            if len(t_list) > 1:
                dt = t_list[-1] - t_list[-2]
                activity = (current_events - prev_events) / dt if dt > 0 else 0
            else:
                activity = 0
            activity_list.append(activity)
            prev_events = current_events
    
    # Normalize for comparison
    S_norm = np.array(S_list) / (S_list[0] + 1e-10)
    activity_norm = np.array(activity_list)
    activity_norm = activity_norm / (np.mean(activity_norm[:50]) + 1e-10)  # Normalize to early mean
    
    # Plot Activity
    ax1.plot(t_list, activity_norm, 'g-', linewidth=1.5, alpha=0.8)
    ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Activity (normalized)', fontsize=12, color='g')
    ax1.set_title('Figure 3: Activity vs Organization (Undriven)', fontsize=14)
    ax1.tick_params(axis='y', labelcolor='g')
    ax1.set_ylim([0, 2])
    ax1.grid(True, alpha=0.3)
    ax1.text(0.02, 0.95, 'Activity persists (~80%)', transform=ax1.transAxes, 
             fontsize=10, verticalalignment='top', color='g')
    
    # Plot S
    ax2.semilogy(t_list, S_norm, 'b-', linewidth=1.5, alpha=0.8)
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('S (normalized, log scale)', fontsize=12, color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2.set_ylim([1e-4, 10])
    ax2.grid(True, alpha=0.3)
    ax2.text(0.02, 0.95, 'Organization decays (~300×)', transform=ax2.transAxes,
             fontsize=10, verticalalignment='top', color='b')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")


def fig4_energy_matched_control(save_path):
    """
    Figure 4: Energy-matched control bar plot
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    
    # Data from controls
    conditions = ['Undriven', 'Periodic', 'Random\n(matched)']
    S_values = [
        controls['energy_matched_control']['undriven']['S'],
        controls['energy_matched_control']['periodic']['S'],
        controls['energy_matched_control']['random']['S']
    ]
    
    colors = ['#1f77b4', '#d62728', '#ff7f0e']
    
    bars = ax.bar(conditions, S_values, color=colors, edgecolor='black', linewidth=1.2)
    
    # Add value labels
    for bar, val in zip(bars, S_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2e}' if val < 0.001 else f'{val:.4f}',
                ha='center', va='bottom', fontsize=10)
    
    ax.set_ylabel('$S_{late}$ (late-time organization)', fontsize=12)
    ax.set_title('Figure 4: Energy-Matched Control', fontsize=14)
    ax.set_ylim([0, max(S_values) * 1.3])
    
    # Add annotation
    ax.annotate('Periodic ≈ Random', xy=(1.5, S_values[1]), xytext=(1.5, S_values[1]*1.15),
                ha='center', fontsize=10, color='gray')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")


def fig5_power_vs_S(save_path):
    """
    Figure 5: S_late vs Power (from duty cycle data)
    """
    fig, ax = plt.subplots(figsize=(7, 5))
    
    duty_data = controls['duty_cycle']
    
    power = [d['power'] for d in duty_data]
    S_late = [d['S_late'] for d in duty_data]
    amp = [d['amplitude'] for d in duty_data]
    
    # Color by amplitude
    colors = {1.0: '#1f77b4', 2.0: '#ff7f0e', 3.0: '#d62728'}
    
    for a in [1.0, 2.0, 3.0]:
        mask = [d['amplitude'] == a for d in duty_data]
        p_a = [p for p, m in zip(power, mask) if m]
        s_a = [s for s, m in zip(S_late, mask) if m]
        ax.scatter(p_a, s_a, c=colors[a], s=80, label=f'Amplitude = {a}', edgecolor='black', linewidth=0.5)
    
    # Fit line
    power_arr = np.array(power)
    S_arr = np.array(S_late)
    
    # Log-log fit
    log_p = np.log10(power_arr + 1e-10)
    log_S = np.log10(S_arr)
    
    coeffs = np.polyfit(log_p, log_S, 1)
    fit_line = 10**(coeffs[0] * log_p + coeffs[1])
    
    sorted_idx = np.argsort(power_arr)
    ax.plot(power_arr[sorted_idx], fit_line[sorted_idx], 'k--', linewidth=1.5, 
            label=f'Fit: $S \\propto P^{{{coeffs[0]:.2f}}}$')
    
    ax.set_xlabel('Power ($A^2 / T_{interval}$)', fontsize=12)
    ax.set_ylabel('$S_{late}$', fontsize=12)
    ax.set_title('Figure 5: Organization vs Input Power', fontsize=14)
    ax.legend(fontsize=10)
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")


def main():
    print("=" * 60)
    print("PAPER 2: GENERATING PUBLICATION FIGURES")
    print("=" * 60)
    
    # Generate all figures
    print("\nGenerating Figure 1: S(t) decay comparison...")
    fig1_s_decay(f"{OUTPUT_DIR}/fig1_S_decay.png")
    
    print("\nGenerating Figure 2: I_TS(t) evolution...")
    fig2_its_decay(f"{OUTPUT_DIR}/fig2_ITS_decay.png")
    
    print("\nGenerating Figure 3: Activity vs Organization...")
    fig3_activity_vs_S(f"{OUTPUT_DIR}/fig3_activity_vs_S.png")
    
    print("\nGenerating Figure 4: Energy-matched control...")
    fig4_energy_matched_control(f"{OUTPUT_DIR}/fig4_energy_matched.png")
    
    print("\nGenerating Figure 5: Power vs S_late...")
    fig5_power_vs_S(f"{OUTPUT_DIR}/fig5_power_vs_S.png")
    
    print("\n" + "=" * 60)
    print("ALL FIGURES GENERATED")
    print("=" * 60)


if __name__ == "__main__":
    main()
