"""
Expansion-DOF Coupling Test - Publication Figures
==================================================

Generates paper-ready figures showing:
1. R(T) expansion radius with unlock markers
2. dR/dT expansion velocity with +464.7% annotation
3. D_eff effective dimensionality over time
4. Pressure dynamics before/after unlock

Author: QMRT Research
Date: December 2025
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Set publication style
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
})

# Colors
ENABLED_COLOR = '#2E86AB'  # Blue
DISABLED_COLOR = '#A23B72'  # Magenta
UNLOCK_Y_COLOR = '#F18F01'  # Orange
UNLOCK_Z_COLOR = '#C73E1D'  # Red
ANNOTATION_COLOR = '#1B4332'  # Dark green


def load_data():
    """Load the expansion comparison JSON data."""
    json_path = Path('/app/backend/qmrt_topology/papers/expansion_dof/expansion_comparison.json')
    with open(json_path, 'r') as f:
        return json.load(f)


def extract_timeseries(data, condition):
    """Extract timeseries arrays from condition data."""
    metrics = data[condition]['metrics_timeseries']
    
    T = np.array([m['T'] for m in metrics])
    radius = np.array([m['radius'] for m in metrics])
    dR_dT = np.array([m['dR_dT'] for m in metrics])
    pressure = np.array([m['pressure'] for m in metrics])
    D_eff = np.array([m['D_eff'] for m in metrics])
    ax = np.array([m['ax'] for m in metrics])
    ay = np.array([m['ay'] for m in metrics])
    az = np.array([m['az'] for m in metrics])
    
    return {
        'T': T,
        'radius': radius,
        'dR_dT': dR_dT,
        'pressure': pressure,
        'D_eff': D_eff,
        'ax': ax,
        'ay': ay,
        'az': az,
    }


def plot_expansion_radius(data, enabled, disabled, output_dir):
    """Figure 1: R(T) expansion radius over time."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot data
    ax.plot(enabled['T'], enabled['radius'], 
            color=ENABLED_COLOR, linewidth=2, label='Unlocking Enabled')
    ax.plot(disabled['T'], disabled['radius'], 
            color=DISABLED_COLOR, linewidth=2, linestyle='--', label='Unlocking Disabled')
    
    # Unlock markers
    y_unlock = data['enabled']['y_unlock_T']
    z_unlock = data['enabled']['z_unlock_T']
    
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=2, alpha=0.8)
        ax.annotate('Y Unlock', xy=(y_unlock, ax.get_ylim()[1]*0.95), 
                   fontsize=10, color=UNLOCK_Y_COLOR, ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=UNLOCK_Y_COLOR, alpha=0.9))
    
    if z_unlock:
        ax.axvline(x=z_unlock, color=UNLOCK_Z_COLOR, linestyle=':', linewidth=2, alpha=0.8)
        ax.annotate('Z Unlock', xy=(z_unlock + 15, ax.get_ylim()[1]*0.85), 
                   fontsize=10, color=UNLOCK_Z_COLOR, ha='left',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=UNLOCK_Z_COLOR, alpha=0.9))
    
    # Labels
    ax.set_xlabel('Simulation Time T')
    ax.set_ylabel('Expansion Radius R')
    ax.set_title('Expansion Radius Over Time: Unlocking Enabled vs Disabled')
    ax.legend(loc='upper left')
    
    # Annotate final values
    final_enabled = data['enabled']['final_radius']
    final_disabled = data['disabled']['final_radius']
    ax.annotate(f'Final: {final_enabled:.1f}', 
               xy=(enabled['T'][-1], enabled['radius'][-1]),
               xytext=(10, 10), textcoords='offset points',
               fontsize=9, color=ENABLED_COLOR)
    ax.annotate(f'Final: {final_disabled:.1f}', 
               xy=(disabled['T'][-1], disabled['radius'][-1]),
               xytext=(10, -15), textcoords='offset points',
               fontsize=9, color=DISABLED_COLOR)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig1_expansion_radius.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig1_expansion_radius.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig1_expansion_radius.png/pdf")


def plot_expansion_velocity(data, enabled, disabled, output_dir):
    """Figure 2: dR/dT expansion velocity with acceleration annotation."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot data - use positive values only for cleaner visualization
    # Smooth the data a bit for visual clarity
    window = 3
    enabled_smooth = np.convolve(enabled['dR_dT'], np.ones(window)/window, mode='same')
    disabled_smooth = np.convolve(disabled['dR_dT'], np.ones(window)/window, mode='same')
    
    ax.plot(enabled['T'], enabled['dR_dT'], 
            color=ENABLED_COLOR, linewidth=1.5, alpha=0.4, label='_nolegend_')
    ax.plot(enabled['T'], enabled_smooth, 
            color=ENABLED_COLOR, linewidth=2.5, label='Unlocking Enabled')
    
    ax.plot(disabled['T'], disabled['dR_dT'], 
            color=DISABLED_COLOR, linewidth=1.5, alpha=0.4, label='_nolegend_')
    ax.plot(disabled['T'], disabled_smooth, 
            color=DISABLED_COLOR, linewidth=2.5, linestyle='--', label='Unlocking Disabled')
    
    # Unlock markers
    y_unlock = data['enabled']['y_unlock_T']
    z_unlock = data['enabled']['z_unlock_T']
    
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=2, alpha=0.8)
    if z_unlock:
        ax.axvline(x=z_unlock, color=UNLOCK_Z_COLOR, linestyle=':', linewidth=2, alpha=0.8)
    
    # Shade pre-unlock and post-unlock regions
    if y_unlock:
        ax.axvspan(0, y_unlock, alpha=0.1, color='gray', label='Pre-Unlock')
        ax.axvspan(y_unlock, enabled['T'][-1], alpha=0.1, color=ENABLED_COLOR, label='Post-Unlock')
    
    # Velocity change annotation
    pre_vel_enabled = data['enabled']['pre_velocity']
    post_vel_enabled = data['enabled']['post_velocity']
    vel_change = data['enabled']['velocity_change_pct']
    
    # Add annotation box
    annotation_text = f'+{vel_change:.1f}% Acceleration'
    if y_unlock:
        mid_post = (y_unlock + enabled['T'][-1]) / 2
        ax.annotate(annotation_text,
                   xy=(mid_post, post_vel_enabled),
                   xytext=(mid_post, post_vel_enabled + 0.15),
                   fontsize=12, fontweight='bold', color=ANNOTATION_COLOR,
                   ha='center',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#90EE90', edgecolor=ANNOTATION_COLOR, alpha=0.9),
                   arrowprops=dict(arrowstyle='->', color=ANNOTATION_COLOR, lw=1.5))
    
    # Add pre/post velocity labels
    if y_unlock:
        mid_pre = y_unlock / 2
        ax.annotate(f'Pre: {pre_vel_enabled:.3f}',
                   xy=(mid_pre, pre_vel_enabled),
                   xytext=(mid_pre, pre_vel_enabled + 0.08),
                   fontsize=10, color=ENABLED_COLOR, ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=ENABLED_COLOR, alpha=0.8))
        ax.annotate(f'Post: {post_vel_enabled:.3f}',
                   xy=(mid_post, post_vel_enabled - 0.05),
                   fontsize=10, color=ENABLED_COLOR, ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=ENABLED_COLOR, alpha=0.8))
    
    # Labels
    ax.set_xlabel('Simulation Time T')
    ax.set_ylabel('Expansion Velocity dR/dT')
    ax.set_title('Expansion Velocity: Sharp Acceleration After Dimensional Unlocking')
    ax.legend(loc='upper left')
    
    # Set y limits to show the spike clearly
    ax.set_ylim(-0.2, 0.7)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig2_expansion_velocity.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig2_expansion_velocity.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig2_expansion_velocity.png/pdf")


def plot_d_eff(data, enabled, disabled, output_dir):
    """Figure 3: D_eff effective dimensionality over time."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot data
    ax.plot(enabled['T'], enabled['D_eff'], 
            color=ENABLED_COLOR, linewidth=2.5, label='Unlocking Enabled')
    ax.plot(disabled['T'], disabled['D_eff'], 
            color=DISABLED_COLOR, linewidth=2.5, linestyle='--', label='Unlocking Disabled')
    
    # Unlock markers
    y_unlock = data['enabled']['y_unlock_T']
    z_unlock = data['enabled']['z_unlock_T']
    
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=2, alpha=0.8)
        ax.annotate('Y Unlock', xy=(y_unlock, 2.0), 
                   fontsize=10, color=UNLOCK_Y_COLOR, ha='right', rotation=90,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=UNLOCK_Y_COLOR, alpha=0.9))
    
    if z_unlock:
        ax.axvline(x=z_unlock, color=UNLOCK_Z_COLOR, linestyle=':', linewidth=2, alpha=0.8)
    
    # Horizontal reference lines for dimensions
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=2.0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=3.0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # Dimension labels
    ax.text(enabled['T'][-1] + 5, 1.0, '1D', fontsize=9, va='center', color='gray')
    ax.text(enabled['T'][-1] + 5, 2.0, '2D', fontsize=9, va='center', color='gray')
    ax.text(enabled['T'][-1] + 5, 3.0, '3D', fontsize=9, va='center', color='gray')
    
    # Annotate final D_eff
    final_enabled_deff = data['enabled']['post_d_eff']
    final_disabled_deff = data['disabled']['post_d_eff']
    
    ax.annotate(f'D_eff = {final_enabled_deff:.2f}\n(Full 3D)',
               xy=(enabled['T'][-1], enabled['D_eff'][-1]),
               xytext=(-60, 15), textcoords='offset points',
               fontsize=10, color=ENABLED_COLOR, ha='center',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=ENABLED_COLOR, alpha=0.9))
    
    ax.annotate(f'D_eff = {final_disabled_deff:.2f}\n(Trapped in 1D)',
               xy=(disabled['T'][-1], disabled['D_eff'][-1]),
               xytext=(-70, -30), textcoords='offset points',
               fontsize=10, color=DISABLED_COLOR, ha='center',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=DISABLED_COLOR, alpha=0.9))
    
    # Labels
    ax.set_xlabel('Simulation Time T')
    ax.set_ylabel('Effective Dimensionality D_eff')
    ax.set_title('Effective Dimensionality: Enabled Mode Expands to 3D, Disabled Remains Trapped')
    ax.legend(loc='center left')
    ax.set_ylim(0.8, 3.3)
    ax.set_xlim(0, enabled['T'][-1] + 20)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig3_d_eff.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig3_d_eff.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig3_d_eff.png/pdf")


def plot_pressure(data, enabled, disabled, output_dir):
    """Figure 4: Pressure dynamics over time."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot data
    ax.plot(enabled['T'], enabled['pressure'], 
            color=ENABLED_COLOR, linewidth=2.5, label='Unlocking Enabled')
    ax.plot(disabled['T'], disabled['pressure'], 
            color=DISABLED_COLOR, linewidth=2.5, linestyle='--', label='Unlocking Disabled')
    
    # Unlock markers
    y_unlock = data['enabled']['y_unlock_T']
    z_unlock = data['enabled']['z_unlock_T']
    
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=2, alpha=0.8)
        ax.annotate('Y Unlock\n(Threshold)', xy=(y_unlock, 0.025), 
                   fontsize=9, color=UNLOCK_Y_COLOR, ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=UNLOCK_Y_COLOR, alpha=0.9))
    
    if z_unlock:
        ax.axvline(x=z_unlock, color=UNLOCK_Z_COLOR, linestyle=':', linewidth=2, alpha=0.8)
    
    # Unlock threshold line
    ax.axhline(y=0.025, color='green', linestyle='--', alpha=0.6, linewidth=1.5, label='Unlock Threshold')
    
    # Shade regions
    if y_unlock:
        ax.axvspan(0, y_unlock, alpha=0.1, color='gray')
        ax.axvspan(y_unlock, enabled['T'][-1], alpha=0.1, color=ENABLED_COLOR)
    
    # Annotate pressure behavior
    if y_unlock:
        # Pre-unlock: building
        mid_pre = y_unlock / 2
        ax.annotate('Pressure\nBuilding',
                   xy=(mid_pre, 0.015),
                   fontsize=9, ha='center', color='gray',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Post-unlock enabled: redistributed across 3D
        mid_post = (y_unlock + enabled['T'][-1]) / 2
        ax.annotate('Redistributed\nacross 3D',
                   xy=(mid_post, 0.10),
                   fontsize=9, ha='center', color=ENABLED_COLOR,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=ENABLED_COLOR, alpha=0.9))
        
        # Disabled: accumulates in 1D
        ax.annotate('Accumulates\nin 1D',
                   xy=(mid_post, 0.022),
                   fontsize=9, ha='center', color=DISABLED_COLOR,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=DISABLED_COLOR, alpha=0.9))
    
    # Labels
    ax.set_xlabel('Simulation Time T')
    ax.set_ylabel('Pressure (Kinetic + τ Excess)')
    ax.set_title('Pressure Dynamics: Buildup Triggers Unlock, Then Redistributes')
    ax.legend(loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig4_pressure.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig4_pressure.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig4_pressure.png/pdf")


def plot_combined_panel(data, enabled, disabled, output_dir):
    """Combined 2x2 panel figure for paper."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    y_unlock = data['enabled']['y_unlock_T']
    z_unlock = data['enabled']['z_unlock_T']
    
    # Panel A: Expansion Radius
    ax = axes[0, 0]
    ax.plot(enabled['T'], enabled['radius'], color=ENABLED_COLOR, linewidth=2, label='Enabled')
    ax.plot(disabled['T'], disabled['radius'], color=DISABLED_COLOR, linewidth=2, linestyle='--', label='Disabled')
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=1.5, alpha=0.8)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Radius R')
    ax.set_title('(A) Expansion Radius')
    ax.legend(loc='upper left', fontsize=9)
    
    # Panel B: Expansion Velocity
    ax = axes[0, 1]
    ax.plot(enabled['T'], enabled['dR_dT'], color=ENABLED_COLOR, linewidth=2, label='Enabled')
    ax.plot(disabled['T'], disabled['dR_dT'], color=DISABLED_COLOR, linewidth=2, linestyle='--', label='Disabled')
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=1.5, alpha=0.8)
        ax.axvspan(y_unlock, enabled['T'][-1], alpha=0.15, color=ENABLED_COLOR)
    ax.annotate('+464.7%', xy=(420, 0.15), fontsize=11, fontweight='bold', color=ANNOTATION_COLOR,
               bbox=dict(boxstyle='round,pad=0.4', facecolor='#90EE90', edgecolor=ANNOTATION_COLOR, alpha=0.9))
    ax.set_xlabel('Time T')
    ax.set_ylabel('Velocity dR/dT')
    ax.set_title('(B) Expansion Velocity')
    ax.legend(loc='upper left', fontsize=9)
    ax.set_ylim(-0.2, 0.65)
    
    # Panel C: D_eff
    ax = axes[1, 0]
    ax.plot(enabled['T'], enabled['D_eff'], color=ENABLED_COLOR, linewidth=2, label='Enabled')
    ax.plot(disabled['T'], disabled['D_eff'], color=DISABLED_COLOR, linewidth=2, linestyle='--', label='Disabled')
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=1.5, alpha=0.8)
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.4, linewidth=1)
    ax.axhline(y=3.0, color='gray', linestyle='--', alpha=0.4, linewidth=1)
    ax.text(enabled['T'][-1]+5, 1.0, '1D', fontsize=8, va='center', color='gray')
    ax.text(enabled['T'][-1]+5, 3.0, '3D', fontsize=8, va='center', color='gray')
    ax.set_xlabel('Time T')
    ax.set_ylabel('D_eff')
    ax.set_title('(C) Effective Dimensionality')
    ax.legend(loc='center left', fontsize=9)
    ax.set_ylim(0.8, 3.3)
    
    # Panel D: Pressure
    ax = axes[1, 1]
    ax.plot(enabled['T'], enabled['pressure'], color=ENABLED_COLOR, linewidth=2, label='Enabled')
    ax.plot(disabled['T'], disabled['pressure'], color=DISABLED_COLOR, linewidth=2, linestyle='--', label='Disabled')
    if y_unlock:
        ax.axvline(x=y_unlock, color=UNLOCK_Y_COLOR, linestyle=':', linewidth=1.5, alpha=0.8)
    ax.axhline(y=0.025, color='green', linestyle='--', alpha=0.5, linewidth=1, label='Threshold')
    ax.set_xlabel('Time T')
    ax.set_ylabel('Pressure')
    ax.set_title('(D) Pressure Dynamics')
    ax.legend(loc='upper left', fontsize=9)
    
    fig.suptitle('Expansion-DOF Coupling: Dark Energy Analog in QMRT', fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_combined_panel.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig_combined_panel.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig_combined_panel.png/pdf")


def main():
    """Generate all figures."""
    print("=" * 60)
    print("  EXPANSION-DOF COUPLING - PUBLICATION FIGURES")
    print("=" * 60)
    
    # Load data
    data = load_data()
    print(f"\nLoaded data: {data['test_name']}")
    print(f"Verdict: {data['verdict']}")
    
    # Extract timeseries
    enabled = extract_timeseries(data, 'enabled')
    disabled = extract_timeseries(data, 'disabled')
    
    # Output directory
    output_dir = Path('/app/backend/qmrt_topology/papers/expansion_dof/figures')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating figures to: {output_dir}")
    print()
    
    # Generate individual figures
    plot_expansion_radius(data, enabled, disabled, output_dir)
    plot_expansion_velocity(data, enabled, disabled, output_dir)
    plot_d_eff(data, enabled, disabled, output_dir)
    plot_pressure(data, enabled, disabled, output_dir)
    
    # Generate combined panel
    plot_combined_panel(data, enabled, disabled, output_dir)
    
    print()
    print("=" * 60)
    print("  ALL FIGURES GENERATED")
    print("=" * 60)
    print()
    print("Files created:")
    for f in sorted(output_dir.glob('*')):
        print(f"  - {f.name}")
    
    # Print suggested caption
    print()
    print("=" * 60)
    print("  SUGGESTED FIGURE CAPTION (for fig2)")
    print("=" * 60)
    print("""
Figure 2: Dimensional unlocking produces a sharp acceleration in 
expansion rate. When additional degrees of freedom become accessible 
(vertical dashed lines mark Y and Z unlock events), the expansion 
velocity increases by 464.7% (blue), while the unlocking-disabled 
control (magenta dashed) shows only an 8.8% increase. This supports 
the QMRT interpretation that cosmic acceleration arises from 
progressive activation of accessible degrees of freedom, not from 
an exotic dark energy field.
""")


if __name__ == "__main__":
    main()
