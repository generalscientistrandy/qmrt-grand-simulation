"""
Bullet Cluster Analog Test - Publication Figures
=================================================

Generates paper-ready figures showing τ-gas separation during collision.

Author: QMRT Research
Date: December 2025
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Publication style
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
COLORS = {
    'no_response': '#888888',
    'normal': '#2E86AB',
    'fast_relaxation': '#F18F01',
    'slow_relaxation': '#A23B72',
}


def load_data():
    """Load the bullet cluster results JSON."""
    json_path = Path('/app/backend/qmrt_topology/papers/bullet_cluster/bullet_cluster_results.json')
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_separation_over_time(data, output_dir):
    """Figure 1: τ-gas separation over time for all variants."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for name, variant_data in data['variants'].items():
        metrics = variant_data['metrics']
        if not metrics:
            continue
        
        T = [m['T'] for m in metrics]
        sep = [m['separation_x'] for m in metrics]
        
        color = COLORS.get(name, 'gray')
        label = name.replace('_', ' ').title()
        ax.plot(T, sep, color=color, linewidth=2.5, label=label, marker='o', markersize=4)
    
    # Reference line at zero
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    # Shade separation region
    ax.axhspan(-15, -3, alpha=0.1, color='red', label='Significant separation')
    ax.axhspan(3, 15, alpha=0.1, color='red')
    
    ax.set_xlabel('Simulation Time T')
    ax.set_ylabel('τ-structure - Gas Centroid Separation (grid units)')
    ax.set_title('Bullet Cluster Analog: τ-Gas Separation During Collision')
    ax.legend(loc='upper right')
    ax.set_ylim(-15, 15)
    
    # Annotate peak separations
    ax.annotate('Peak: -10.7\n(Fast relax)', xy=(20, -10.7), fontsize=9,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
    ax.annotate('Peak: -9.5\n(Normal)', xy=(40, -9.5), fontsize=9,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig1_separation_over_time.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig1_separation_over_time.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig1_separation_over_time.png/pdf")


def plot_centroid_trajectories(data, output_dir):
    """Figure 2: Gas and τ centroid x-positions over time."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    for idx, (name, variant_data) in enumerate(data['variants'].items()):
        ax = axes[idx // 2, idx % 2]
        
        metrics = variant_data['metrics']
        if not metrics:
            continue
        
        T = [m['T'] for m in metrics]
        gas_x = [m['gas_centroid'][0] for m in metrics]
        tau_x = [m['tau_centroid'][0] for m in metrics]
        
        ax.plot(T, gas_x, color='red', linewidth=2, label='Gas centroid', linestyle='--')
        ax.plot(T, tau_x, color='blue', linewidth=2, label='τ-structure centroid')
        
        # Fill between to show separation
        ax.fill_between(T, gas_x, tau_x, alpha=0.2, color='purple')
        
        title = name.replace('_', ' ').title()
        ax.set_title(f'({chr(65+idx)}) {title}')
        ax.set_xlabel('Time T')
        ax.set_ylabel('X position')
        ax.legend(loc='upper right', fontsize=9)
        ax.axhline(y=32, color='gray', linestyle=':', alpha=0.5)  # Grid center
    
    fig.suptitle('Centroid Trajectories: Gas (red) vs τ-Structure (blue)', fontsize=14, y=1.02)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig2_centroid_trajectories.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig2_centroid_trajectories.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig2_centroid_trajectories.png/pdf")


def plot_peak_separation_comparison(data, output_dir):
    """Figure 3: Bar chart comparing peak separations."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    variants = list(data['variants'].keys())
    peak_seps = [data['analysis'][v]['peak_separation'] for v in variants]
    final_seps = [abs(data['analysis'][v]['final_separation']) for v in variants]
    
    x = np.arange(len(variants))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, peak_seps, width, label='Peak Separation', 
                   color=[COLORS.get(v, 'gray') for v in variants], edgecolor='black')
    bars2 = ax.bar(x + width/2, final_seps, width, label='Final Separation',
                   color=[COLORS.get(v, 'gray') for v in variants], alpha=0.5, edgecolor='black')
    
    ax.set_ylabel('Separation (grid units)')
    ax.set_title('Peak vs Final τ-Gas Separation by Variant')
    ax.set_xticks(x)
    ax.set_xticklabels([v.replace('_', '\n') for v in variants])
    ax.legend()
    
    # Add value labels
    for bar, val in zip(bars1, peak_seps):
        ax.annotate(f'{val:.1f}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                   xytext=(0, 3), textcoords='offset points', ha='center', fontsize=10)
    
    # Reference line for significant separation
    ax.axhline(y=5, color='green', linestyle='--', alpha=0.7, label='Significant threshold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig3_peak_comparison.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig3_peak_comparison.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig3_peak_comparison.png/pdf")


def plot_tau_max_evolution(data, output_dir):
    """Figure 4: τ_max evolution during collision."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for name, variant_data in data['variants'].items():
        metrics = variant_data['metrics']
        if not metrics:
            continue
        
        T = [m['T'] for m in metrics]
        tau_max = [m['tau_max'] for m in metrics]
        
        color = COLORS.get(name, 'gray')
        label = name.replace('_', ' ').title()
        ax.plot(T, tau_max, color=color, linewidth=2, label=label)
    
    ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, label='τ = 1 (baseline)')
    
    ax.set_xlabel('Simulation Time T')
    ax.set_ylabel('Maximum τ value')
    ax.set_title('τ Field Evolution During Collision')
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig4_tau_evolution.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig4_tau_evolution.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig4_tau_evolution.png/pdf")


def plot_combined_panel(data, output_dir):
    """Combined figure for paper."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Panel A: Separation over time
    ax = axes[0, 0]
    for name in ['no_response', 'normal']:
        metrics = data['variants'][name]['metrics']
        T = [m['T'] for m in metrics]
        sep = [m['separation_x'] for m in metrics]
        color = COLORS.get(name, 'gray')
        label = 'Control (no τ)' if name == 'no_response' else 'Normal τ-response'
        ax.plot(T, sep, color=color, linewidth=2.5, label=label)
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Separation')
    ax.set_title('(A) τ-Gas Separation: Normal vs Control')
    ax.legend(fontsize=9)
    ax.annotate('19× more separation\nwith τ-response', xy=(50, -8), fontsize=10,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='#90EE90', alpha=0.9))
    
    # Panel B: All variants separation
    ax = axes[0, 1]
    for name, variant_data in data['variants'].items():
        metrics = variant_data['metrics']
        T = [m['T'] for m in metrics]
        sep = [m['separation_x'] for m in metrics]
        color = COLORS.get(name, 'gray')
        label = name.replace('_', ' ').title()
        ax.plot(T, sep, color=color, linewidth=2, label=label)
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax.set_xlabel('Time T')
    ax.set_ylabel('Separation')
    ax.set_title('(B) All Variants')
    ax.legend(fontsize=8, loc='upper right')
    
    # Panel C: Peak separation bar chart
    ax = axes[1, 0]
    variants = list(data['variants'].keys())
    peak_seps = [data['analysis'][v]['peak_separation'] for v in variants]
    colors = [COLORS.get(v, 'gray') for v in variants]
    bars = ax.bar(range(len(variants)), peak_seps, color=colors, edgecolor='black')
    ax.set_xticks(range(len(variants)))
    ax.set_xticklabels([v.replace('_', '\n') for v in variants], fontsize=9)
    ax.set_ylabel('Peak Separation')
    ax.set_title('(C) Peak Separation by Variant')
    ax.axhline(y=5, color='green', linestyle='--', alpha=0.7)
    for bar, val in zip(bars, peak_seps):
        ax.annotate(f'{val:.1f}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                   xytext=(0, 3), textcoords='offset points', ha='center', fontsize=10)
    
    # Panel D: τ evolution
    ax = axes[1, 1]
    for name in ['normal', 'slow_relaxation']:
        metrics = data['variants'][name]['metrics']
        T = [m['T'] for m in metrics]
        tau_max = [m['tau_max'] for m in metrics]
        color = COLORS.get(name, 'gray')
        label = name.replace('_', ' ').title()
        ax.plot(T, tau_max, color=color, linewidth=2, label=label)
    ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
    ax.set_xlabel('Time T')
    ax.set_ylabel('τ_max')
    ax.set_title('(D) τ Field Evolution')
    ax.legend(fontsize=9)
    
    fig.suptitle('QMRT Bullet Cluster Analog: τ-Structure Separates from Gas', 
                fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_combined_bullet.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig_combined_bullet.pdf', bbox_inches='tight')
    plt.close()
    print("Created: fig_combined_bullet.png/pdf")


def main():
    """Generate all figures."""
    print("=" * 60)
    print("  BULLET CLUSTER ANALOG - PUBLICATION FIGURES")
    print("=" * 60)
    
    data = load_data()
    print(f"\nVerdict: {data['verdict']}")
    
    output_dir = Path('/app/backend/qmrt_topology/papers/bullet_cluster/figures')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating figures to: {output_dir}\n")
    
    plot_separation_over_time(data, output_dir)
    plot_centroid_trajectories(data, output_dir)
    plot_peak_separation_comparison(data, output_dir)
    plot_tau_max_evolution(data, output_dir)
    plot_combined_panel(data, output_dir)
    
    print()
    print("=" * 60)
    print("  ALL FIGURES GENERATED")
    print("=" * 60)
    
    print("""
SUGGESTED FIGURE CAPTION:

Figure: The QMRT Bullet Cluster analog test demonstrates that τ-structure 
(dark matter proxy) separates from gas (collisional matter) during cluster 
collision. (A) Normal τ-response shows 19× more separation than the control.
(B) All variants show transient separation, with peak values reaching 10+ 
grid units. (C) τ-responsive variants (normal, fast, slow relaxation) all 
exceed the no-response control. (D) τ field evolution shows different 
persistence patterns for different relaxation rates.
""")


if __name__ == "__main__":
    main()
