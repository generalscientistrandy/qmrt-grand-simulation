#!/usr/bin/env python3
"""
QMRT Defect Dynamics Visualization
==================================
Generates visualizations of the defect dynamics simulation.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import json
from defect_dynamics import DefectDynamicsEngine, PhysicsParams, run_chaos_to_order_experiment

def plot_metrics(metrics: dict, save_path: str = None):
    """Plot simulation metrics over time."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Defect counts
    ax = axes[0, 0]
    ax.plot(metrics['defect_count'], 'b-', label='Total', linewidth=1)
    ax.plot(metrics['positive_count'], 'r--', label='Positive', linewidth=0.8, alpha=0.7)
    ax.plot(metrics['negative_count'], 'g--', label='Negative', linewidth=0.8, alpha=0.7)
    ax.set_xlabel('Time')
    ax.set_ylabel('Count')
    ax.set_title('Defect Population')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Creation/Annihilation events
    ax = axes[0, 1]
    window = 50
    if len(metrics['creation_events']) > window:
        creations = np.convolve(metrics['creation_events'], np.ones(window)/window, mode='valid')
        annihilations = np.convolve(metrics['annihilation_events'], np.ones(window)/window, mode='valid')
        ax.plot(creations, 'g-', label='Creations', linewidth=1)
        ax.plot(annihilations, 'r-', label='Annihilations', linewidth=1)
    ax.set_xlabel('Time')
    ax.set_ylabel('Rate (smoothed)')
    ax.set_title('Creation/Annihilation Events')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Total energy
    ax = axes[0, 2]
    ax.plot(metrics['total_energy'], 'orange', linewidth=1)
    ax.set_xlabel('Time')
    ax.set_ylabel('Energy')
    ax.set_title('Total Medium Energy')
    ax.grid(True, alpha=0.3)
    
    # Cluster count
    ax = axes[1, 0]
    ax.plot(metrics['cluster_count'], 'purple', linewidth=1)
    ax.set_xlabel('Time')
    ax.set_ylabel('Count')
    ax.set_title('Number of Clusters')
    ax.grid(True, alpha=0.3)
    
    # Mean cluster size
    ax = axes[1, 1]
    ax.plot(metrics['mean_cluster_size'], 'teal', linewidth=1)
    ax.set_xlabel('Time')
    ax.set_ylabel('Size')
    ax.set_title('Mean Cluster Size')
    ax.grid(True, alpha=0.3)
    
    # Spatial correlation
    ax = axes[1, 2]
    ax.plot(metrics['spatial_correlation'], 'brown', linewidth=1)
    ax.set_xlabel('Time')
    ax.set_ylabel('Correlation')
    ax.set_title('Spatial Correlation')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved metrics plot to {save_path}")
    
    plt.close()
    return fig


def plot_final_state(engine: DefectDynamicsEngine, save_path: str = None):
    """Plot the final state of the simulation."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Defect positions
    ax = axes[0]
    for defect in engine.defects:
        color = 'red' if defect.charge > 0 else 'blue'
        ax.scatter(defect.position[0], defect.position[1], 
                   c=color, s=50, alpha=0.7, marker='o')
        # Velocity arrow
        if np.linalg.norm(defect.velocity) > 0.1:
            ax.arrow(defect.position[0], defect.position[1],
                    defect.velocity[0]*2, defect.velocity[1]*2,
                    head_width=0.5, head_length=0.3, fc=color, ec=color, alpha=0.5)
    
    # Draw clusters
    for cluster in engine.clusters:
        color = 'green' if cluster.stable else 'yellow'
        circle = Circle(cluster.center, engine.params.cluster_radius, 
                       fill=False, color=color, linestyle='--', linewidth=2, alpha=0.5)
        ax.add_patch(circle)
    
    ax.set_xlim(0, engine.size[0])
    ax.set_ylim(0, engine.size[1])
    ax.set_aspect('equal')
    ax.set_title(f'Defect Positions (t={engine.time})\nRed=+1, Blue=-1')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    
    # Energy field
    ax = axes[1]
    im = ax.imshow(engine.medium.energy_field.T, origin='lower', 
                   cmap='hot', aspect='equal')
    plt.colorbar(im, ax=ax, label='Energy')
    ax.set_title('Energy Field')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    
    # Strain field
    ax = axes[2]
    im = ax.imshow(engine.medium.strain_field.T, origin='lower', 
                   cmap='RdBu', aspect='equal', vmin=-0.5, vmax=0.5)
    plt.colorbar(im, ax=ax, label='Strain')
    ax.set_title('Strain Field')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved final state to {save_path}")
    
    plt.close()
    return fig


def plot_phase_space(engine: DefectDynamicsEngine, save_path: str = None):
    """Plot defect distribution in position-velocity phase space."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    if len(engine.defects) == 0:
        print("No defects to plot")
        return None
    
    positions = np.array([d.position for d in engine.defects])
    velocities = np.array([d.velocity for d in engine.defects])
    charges = np.array([d.charge for d in engine.defects])
    
    # Position distribution
    ax = axes[0]
    colors = ['red' if c > 0 else 'blue' for c in charges]
    ax.scatter(positions[:, 0], positions[:, 1], c=colors, s=30, alpha=0.6)
    ax.set_xlim(0, engine.size[0])
    ax.set_ylim(0, engine.size[1])
    ax.set_aspect('equal')
    ax.set_title('Position Space')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.grid(True, alpha=0.3)
    
    # Velocity distribution
    ax = axes[1]
    ax.scatter(velocities[:, 0], velocities[:, 1], c=colors, s=30, alpha=0.6)
    max_v = max(np.max(np.abs(velocities)), 0.1)
    ax.set_xlim(-max_v*1.2, max_v*1.2)
    ax.set_ylim(-max_v*1.2, max_v*1.2)
    ax.set_aspect('equal')
    ax.set_title('Velocity Space')
    ax.set_xlabel('Vx')
    ax.set_ylabel('Vy')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved phase space to {save_path}")
    
    plt.close()
    return fig


def create_evolution_snapshots(grid_size=50, n_initial_pairs=50, n_steps=5000, 
                                snapshot_times=[0, 100, 500, 1000, 2500, 5000],
                                save_path=None):
    """Create snapshots of evolution at different times."""
    np.random.seed(42)
    
    params = PhysicsParams(
        creation_threshold=1.0,
        pair_separation=2.0,
        creation_rate=0.005,
        interaction_strength=1.0,
        force_exponent=2.0,
        damping=0.15,
        max_speed=1.5,
        annihilation_radius=1.5,
        annihilation_energy=1.5,
        cluster_radius=6.0,
        stability_threshold=0.15,
        energy_decay=0.02,
        strain_diffusion=0.03,
        boundary_mode="periodic"
    )
    
    engine = DefectDynamicsEngine(size=(grid_size, grid_size), params=params)
    engine.create_random_pairs(n_initial_pairs)
    engine.medium.energy_field = np.random.uniform(0, 0.5, engine.size)
    engine.medium.strain_field = np.random.uniform(-0.3, 0.3, engine.size)
    
    n_snapshots = len(snapshot_times)
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    snapshot_idx = 0
    
    for step in range(n_steps + 1):
        if step in snapshot_times and snapshot_idx < n_snapshots:
            ax = axes[snapshot_idx]
            
            # Plot defects
            for defect in engine.defects:
                color = 'red' if defect.charge > 0 else 'blue'
                ax.scatter(defect.position[0], defect.position[1], 
                          c=color, s=30, alpha=0.7, marker='o')
            
            # Plot clusters
            for cluster in engine.clusters:
                color = 'green' if cluster.stable else 'yellow'
                circle = Circle(cluster.center, params.cluster_radius, 
                               fill=False, color=color, linestyle='--', 
                               linewidth=1.5, alpha=0.5)
                ax.add_patch(circle)
            
            ax.set_xlim(0, grid_size)
            ax.set_ylim(0, grid_size)
            ax.set_aspect('equal')
            ax.set_title(f't = {step}\nDefects: {len(engine.defects)}, Clusters: {len(engine.clusters)}')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            
            snapshot_idx += 1
            print(f"Snapshot at t={step}: {len(engine.defects)} defects, {len(engine.clusters)} clusters")
        
        if step < n_steps:
            engine.step(dt=0.1)
    
    plt.suptitle('QMRT Defect Dynamics: Evolution from Chaos', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved evolution snapshots to {save_path}")
    
    plt.close()
    return engine


if __name__ == "__main__":
    print("Running QMRT Defect Dynamics Experiment with Visualization")
    print("=" * 60)
    
    # Run the experiment (reduced for faster initial test)
    result = run_chaos_to_order_experiment(
        grid_size=40,
        n_initial_pairs=30,
        n_steps=2000,
        seed=42
    )
    
    engine = result['engine']
    summary = result['summary']
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    
    plot_metrics(
        summary['metrics'],
        save_path='/app/backend/qmrt_topology/dynamics_metrics.png'
    )
    
    plot_final_state(
        engine,
        save_path='/app/backend/qmrt_topology/dynamics_final_state.png'
    )
    
    plot_phase_space(
        engine,
        save_path='/app/backend/qmrt_topology/dynamics_phase_space.png'
    )
    
    # Create evolution snapshots (separate run)
    print("\nCreating evolution snapshots...")
    create_evolution_snapshots(
        grid_size=40,
        n_initial_pairs=30,
        n_steps=2000,
        snapshot_times=[0, 100, 400, 800, 1400, 2000],
        save_path='/app/backend/qmrt_topology/dynamics_evolution.png'
    )
    
    print("\nAll visualizations complete!")
