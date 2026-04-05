#!/usr/bin/env python3
"""
QMRT Geodesic Test — THE CRITICAL MILESTONE
============================================

Test whether waves follow MINIMUM OPTICAL PATH LENGTH:

    L = ∫ ds / c_eff(x,y)

Not the shortest geometric (Euclidean) distance.

Test procedure:
1. Create a CURVED channel (not straight line)
2. Launch wave from point A
3. Compare:
   - Actual wave path (where wave energy travels)
   - Shortest geometric path (straight line)
   - Minimum optical path (Fermat's principle)

If waves follow minimum optical path → 
"The medium defines an effective metric governing signal propagation."
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from wave_field_dynamics import WaveFieldSystem, WaveParams


def compute_optical_path_length(path: np.ndarray, c_eff_field: np.ndarray) -> float:
    """
    Compute optical path length: L = ∫ ds / c_eff
    
    path: array of (x, y) points
    c_eff_field: 2D array of local wave speeds
    """
    L = 0.0
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i+1]
        
        # Geometric segment length
        ds = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        # Average c_eff along segment
        xi = int((x1+x2)/2) % c_eff_field.shape[0]
        yi = int((y1+y2)/2) % c_eff_field.shape[1]
        c_local = c_eff_field[xi, yi]
        
        # Optical path length contribution
        L += ds / c_local
    
    return L


def find_minimum_optical_path(start: np.ndarray, end: np.ndarray, 
                               c_eff_field: np.ndarray, n_points: int = 50) -> np.ndarray:
    """
    Find approximate minimum optical path using gradient descent on path shape.
    
    This is a simplified variational approach.
    """
    # Initialize with straight line
    path = np.zeros((n_points, 2))
    for i in range(n_points):
        t = i / (n_points - 1)
        path[i] = (1-t) * start + t * end
    
    # Gradient descent to minimize optical path length
    learning_rate = 0.5
    
    for iteration in range(200):
        # Compute current optical path length
        L_current = compute_optical_path_length(path, c_eff_field)
        
        # Perturb each interior point and compute gradient
        grad = np.zeros_like(path)
        eps = 0.5
        
        for i in range(1, n_points - 1):  # Don't move endpoints
            for dim in [0, 1]:
                # Positive perturbation
                path_plus = path.copy()
                path_plus[i, dim] += eps
                L_plus = compute_optical_path_length(path_plus, c_eff_field)
                
                # Negative perturbation
                path_minus = path.copy()
                path_minus[i, dim] -= eps
                L_minus = compute_optical_path_length(path_minus, c_eff_field)
                
                # Gradient
                grad[i, dim] = (L_plus - L_minus) / (2 * eps)
        
        # Update path
        path[1:-1] -= learning_rate * grad[1:-1]
        
        # Keep path in bounds
        path = np.clip(path, 0, min(c_eff_field.shape) - 1)
    
    return path


def track_wave_peak(system: WaveFieldSystem, n_steps: int = 100) -> list:
    """Track the position of maximum wave amplitude over time."""
    peaks = []
    
    for t in range(n_steps):
        system.step(dt=0.1)
        
        if t % 5 == 0:
            # Find peak of wave amplitude
            amp = np.abs(system.field)
            peak_idx = np.unravel_index(np.argmax(amp), amp.shape)
            peaks.append(np.array([peak_idx[0], peak_idx[1]]))
    
    return peaks


def test_geodesic_curved_channel():
    """
    THE GEODESIC TEST
    
    Create a curved channel, launch wave, verify it follows optical geodesic.
    """
    print("=" * 60)
    print("GEODESIC TEST — THE CRITICAL MILESTONE")
    print("=" * 60)
    
    np.random.seed(42)
    
    params = WaveParams(
        wave_speed=2.0,
        wave_damping=0.01,
        creation_threshold=100,
        creation_rate=0,
    )
    
    size = 80
    system = WaveFieldSystem(size=(size, size), params=params)
    
    # Create CURVED channel: an arc from (10, 40) to (70, 40)
    # The channel curves upward through (40, 60)
    print("\nCreating curved channel...")
    
    for i in range(size):
        for j in range(size):
            # Parabolic curve: peaks at x=40
            # y = 40 + 20 * (1 - ((x-40)/30)^2)  for x in [10, 70]
            if 10 <= i <= 70:
                curve_y = 40 + 25 * (1 - ((i - 40) / 30)**2)
                dist_to_curve = abs(j - curve_y)
                
                if dist_to_curve < 8:
                    # Higher energy in channel = lower c_eff = higher refractive index
                    system.energy_field[i, j] = 4.0 * np.exp(-dist_to_curve**2 / 18)
    
    # Smooth the channel
    system.energy_field = gaussian_filter(system.energy_field, sigma=1.5)
    
    # Compute c_eff field
    c_eff = params.wave_speed / (1 + 0.4 * system.energy_field / (1 + system.energy_field))
    
    print(f"Channel created. c_eff range: [{c_eff.min():.2f}, {c_eff.max():.2f}]")
    
    # Define start and end points
    start = np.array([10.0, 40.0])  # Left side
    end = np.array([70.0, 40.0])    # Right side
    
    # Path 1: Straight line (shortest geometric distance)
    n_path_points = 50
    straight_path = np.array([
        (1-t) * start + t * end 
        for t in np.linspace(0, 1, n_path_points)
    ])
    L_straight = compute_optical_path_length(straight_path, c_eff)
    print(f"\nStraight path optical length: {L_straight:.2f}")
    
    # Path 2: Following the curve (minimum optical path approximation)
    curved_path = []
    for i in range(n_path_points):
        t = i / (n_path_points - 1)
        x = 10 + 60 * t
        y = 40 + 25 * (1 - ((x - 40) / 30)**2)
        curved_path.append([x, y])
    curved_path = np.array(curved_path)
    L_curved = compute_optical_path_length(curved_path, c_eff)
    print(f"Curved path (channel) optical length: {L_curved:.2f}")
    
    # Path 3: Optimized minimum optical path
    print("\nFinding minimum optical path...")
    optimal_path = find_minimum_optical_path(start, end, c_eff, n_points=50)
    L_optimal = compute_optical_path_length(optimal_path, c_eff)
    print(f"Optimized path optical length: {L_optimal:.2f}")
    
    # Launch wave and track where it goes
    print("\nLaunching wave from start point...")
    system.inject_wave_pulse(start, amplitude=5.0, radius=4.0)
    
    # Track wave propagation
    wave_positions = []
    
    for t in range(200):
        system.step(dt=0.1)
        
        if t % 10 == 0:
            # Find centroid of wave energy (weighted by amplitude)
            amp = np.abs(system.field)
            total_amp = np.sum(amp)
            
            if total_amp > 0.01:
                x_centroid = np.sum(np.arange(size)[:, None] * amp) / total_amp
                y_centroid = np.sum(np.arange(size)[None, :] * amp) / total_amp
                wave_positions.append([x_centroid, y_centroid])
    
    wave_path = np.array(wave_positions)
    
    # Compute how close wave path is to each reference path
    def path_similarity(wave_path, ref_path):
        """Compute average distance from wave path to reference path."""
        if len(wave_path) == 0:
            return float('inf')
        
        distances = []
        for wp in wave_path:
            # Find closest point on reference
            dists = np.sqrt(np.sum((ref_path - wp)**2, axis=1))
            distances.append(np.min(dists))
        return np.mean(distances)
    
    dist_to_straight = path_similarity(wave_path, straight_path)
    dist_to_curved = path_similarity(wave_path, curved_path)
    dist_to_optimal = path_similarity(wave_path, optimal_path)
    
    print(f"\nWave path similarity:")
    print(f"  Distance to straight line: {dist_to_straight:.2f}")
    print(f"  Distance to curved channel: {dist_to_curved:.2f}")
    print(f"  Distance to optimal path: {dist_to_optimal:.2f}")
    
    # Determine which path the wave follows
    print("\n" + "=" * 60)
    print("GEODESIC TEST RESULT")
    print("=" * 60)
    
    # The key comparison: does wave prefer optical geodesic over straight line?
    if L_curved < L_straight * 0.95:  # Curved path has lower optical length
        print(f"Curved path IS shorter in optical length ({L_curved:.1f} < {L_straight:.1f})")
        
        if dist_to_curved < dist_to_straight * 0.8:
            result = "GEODESIC VERIFIED"
            print(f"✓ {result}")
            print("  Wave follows minimum optical path, NOT shortest distance!")
        else:
            result = "PARTIAL GEODESIC"
            print(f"~ {result}")
            print("  Wave shows some preference but not strong")
    else:
        if dist_to_straight < dist_to_curved:
            result = "FOLLOWS STRAIGHT LINE"
            print(f"~ {result}")
        else:
            result = "FOLLOWS CHANNEL"
            print(f"✓ {result}")
    
    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # c_eff map with paths
    ax = axes[0, 0]
    im = ax.imshow(c_eff.T, origin='lower', cmap='viridis_r', extent=[0, size, 0, size])
    ax.plot(straight_path[:, 0], straight_path[:, 1], 'w--', linewidth=2, label=f'Straight (L={L_straight:.1f})')
    ax.plot(curved_path[:, 0], curved_path[:, 1], 'r-', linewidth=2, label=f'Channel (L={L_curved:.1f})')
    ax.plot(optimal_path[:, 0], optimal_path[:, 1], 'g:', linewidth=2, label=f'Optimal (L={L_optimal:.1f})')
    ax.scatter(*start, c='yellow', s=200, marker='*', zorder=5, label='Start')
    ax.scatter(*end, c='orange', s=200, marker='*', zorder=5, label='End')
    ax.set_title('c_eff Field with Paths\n(Lower = higher index = waveguide)', fontsize=11)
    ax.legend(loc='lower right', fontsize=8)
    plt.colorbar(im, ax=ax, label='c_eff')
    
    # Wave path tracking
    ax = axes[0, 1]
    im = ax.imshow(system.energy_field.T, origin='lower', cmap='hot', extent=[0, size, 0, size])
    if len(wave_path) > 0:
        ax.plot(wave_path[:, 0], wave_path[:, 1], 'c-', linewidth=3, marker='o', markersize=4, label='Wave path')
    ax.plot(curved_path[:, 0], curved_path[:, 1], 'w--', linewidth=1, alpha=0.5, label='Channel')
    ax.scatter(*start, c='yellow', s=200, marker='*', zorder=5)
    ax.set_title('Wave Propagation Path', fontsize=11)
    ax.legend(fontsize=8)
    
    # Final wave field
    ax = axes[1, 0]
    im = ax.imshow(system.field.T, origin='lower', cmap='RdBu', vmin=-2, vmax=2, extent=[0, size, 0, size])
    ax.plot(curved_path[:, 0], curved_path[:, 1], 'k--', linewidth=1, alpha=0.5)
    ax.scatter(*start, c='yellow', s=100, marker='*')
    ax.set_title(f'Final Wave Field (t={system.time})', fontsize=11)
    plt.colorbar(im, ax=ax)
    
    # Path comparison
    ax = axes[1, 1]
    paths = ['Straight', 'Channel\n(curved)', 'Optimal']
    optical_lengths = [L_straight, L_curved, L_optimal]
    wave_distances = [dist_to_straight, dist_to_curved, dist_to_optimal]
    
    x = np.arange(len(paths))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, optical_lengths, width, label='Optical Length', color='blue', alpha=0.7)
    ax2 = ax.twinx()
    bars2 = ax2.bar(x + width/2, wave_distances, width, label='Wave Distance', color='red', alpha=0.7)
    
    ax.set_ylabel('Optical Path Length', color='blue')
    ax2.set_ylabel('Wave Path Distance', color='red')
    ax.set_xticks(x)
    ax.set_xticklabels(paths)
    ax.set_title(f'Path Comparison\nResult: {result}', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    
    plt.suptitle('GEODESIC TEST: Does Wave Follow Minimum Optical Path?', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/test_geodesic.png', dpi=150)
    print("\nSaved test_geodesic.png")
    
    return {
        'result': result,
        'L_straight': L_straight,
        'L_curved': L_curved,
        'L_optimal': L_optimal,
        'dist_to_straight': dist_to_straight,
        'dist_to_curved': dist_to_curved,
    }


if __name__ == "__main__":
    result = test_geodesic_curved_channel()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Result: {result['result']}")
    print(f"\nOptical path lengths:")
    print(f"  Straight line: {result['L_straight']:.2f}")
    print(f"  Curved channel: {result['L_curved']:.2f}")
    print(f"  (Ratio: {result['L_curved']/result['L_straight']:.3f})")
    
    if result['result'] == "GEODESIC VERIFIED":
        print("\n" + "=" * 60)
        print("✓ THE MEDIUM DEFINES AN EFFECTIVE METRIC")
        print("  GOVERNING SIGNAL PROPAGATION")
        print("=" * 60)
    
    # Save results
    import json
    with open('/app/backend/qmrt_topology/geodesic_results.json', 'w') as f:
        json.dump(result, f, indent=2)
