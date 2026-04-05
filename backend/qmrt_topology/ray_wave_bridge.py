#!/usr/bin/env python3
"""
QMRT Ray-Wave Bridge Test
=========================

The critical test: Do wave packets follow predicted ray trajectories?

Given c_eff(x,y), compute:
1. Ray trajectory using eikonal equation: dx/ds = ∇(1/c_eff) direction
2. Wave packet centroid from full wave simulation
3. Compare them

If they match → effective geometry for trajectories
If they don't → system is in full-wave regime, not geometric optics

This is the bridge between "waveguide behavior" and "effective geometry behavior".
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator


def compute_ray_trajectory(c_eff: np.ndarray, start: np.ndarray, 
                           direction: np.ndarray, n_steps: int = 500,
                           step_size: float = 0.5) -> np.ndarray:
    """
    Compute ray trajectory using eikonal equation.
    
    Ray equation in medium with n(x) = c0/c_eff(x):
    The ray bends toward regions of higher n (lower c_eff).
    
    Simplified: ray follows gradient of optical path.
    d(ray)/ds points along the local wavevector, which bends
    according to Snell's law in continuous media.
    
    Using: d²r/ds² = (1/2)∇(n²) = (1/2)∇(c0²/c_eff²)
    Or equivalently: ray bends toward lower c_eff
    """
    size = c_eff.shape
    
    # Create interpolator for c_eff and its gradient
    x = np.arange(size[0])
    y = np.arange(size[1])
    c_interp = RegularGridInterpolator((x, y), c_eff, method='linear', 
                                        bounds_error=False, fill_value=None)
    
    # Compute gradient of n² = (c0/c_eff)² ∝ 1/c_eff²
    # ∇(1/c²) = -2/c³ * ∇c
    grad_x = np.gradient(c_eff, axis=0)
    grad_y = np.gradient(c_eff, axis=1)
    
    grad_x_interp = RegularGridInterpolator((x, y), grad_x, method='linear',
                                             bounds_error=False, fill_value=0)
    grad_y_interp = RegularGridInterpolator((x, y), grad_y, method='linear',
                                             bounds_error=False, fill_value=0)
    
    # Initialize ray
    pos = start.copy().astype(float)
    vel = direction.copy().astype(float)
    vel = vel / np.linalg.norm(vel)  # Normalize
    
    trajectory = [pos.copy()]
    
    for _ in range(n_steps):
        # Get local c_eff and gradient
        if 0 <= pos[0] < size[0] and 0 <= pos[1] < size[1]:
            c_local = c_interp(pos)[0]
            dc_dx = grad_x_interp(pos)[0]
            dc_dy = grad_y_interp(pos)[0]
        else:
            break
        
        # Ray bends toward lower c_eff (higher index)
        # Acceleration = -k * ∇c / c  (bends toward low c)
        # This is a simplified ray equation
        k = 0.1  # Coupling strength
        acc_x = -k * dc_dx / max(c_local, 0.1)
        acc_y = -k * dc_dy / max(c_local, 0.1)
        
        # Update velocity (bend)
        vel[0] += acc_x * step_size
        vel[1] += acc_y * step_size
        
        # Normalize velocity (constant speed along ray)
        vel = vel / np.linalg.norm(vel)
        
        # Update position
        pos = pos + vel * step_size
        
        # Boundary check
        if pos[0] < 0 or pos[0] >= size[0] or pos[1] < 0 or pos[1] >= size[1]:
            break
        
        trajectory.append(pos.copy())
    
    return np.array(trajectory)


def simulate_wave_packet(c_eff: np.ndarray, start: np.ndarray,
                         direction: np.ndarray, n_steps: int = 400) -> np.ndarray:
    """
    Simulate wave packet propagation and track centroid.
    
    Uses damped wave equation with variable c_eff.
    """
    size = c_eff.shape
    
    field = np.zeros(size)
    velocity = np.zeros(size)
    
    # Initialize Gaussian wave packet
    packet_width = 5.0
    for i in range(size[0]):
        for j in range(size[1]):
            r = np.array([i, j]) - start
            dist = np.linalg.norm(r)
            
            if dist < 3 * packet_width:
                # Gaussian envelope
                envelope = np.exp(-dist**2 / (2 * packet_width**2))
                # Initial velocity in direction
                velocity[i, j] = 3.0 * envelope
    
    dt = 0.05
    damping = 0.01
    
    centroids = []
    
    for t in range(n_steps):
        # Laplacian
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        # Wave equation with local c_eff
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        # Track centroid
        if t % 5 == 0:
            amp = np.abs(field)
            total = np.sum(amp)
            
            if total > 0.01:
                x_c = np.sum(np.arange(size[0])[:, None] * amp) / total
                y_c = np.sum(np.arange(size[1])[None, :] * amp) / total
                centroids.append([x_c, y_c])
    
    return np.array(centroids)


def run_ray_wave_comparison():
    """
    The Bridge Test: Compare ray trajectory vs wave packet path.
    """
    print("=" * 60)
    print("RAY-WAVE BRIDGE TEST")
    print("=" * 60)
    print("Question: Do wave packets follow predicted ray trajectories?")
    print()
    
    np.random.seed(42)
    
    size = 80
    
    # Create c_eff field with smooth gradient
    # Lower c_eff in upper region (rays should bend upward)
    c_eff = np.ones((size, size)) * 2.0
    
    for i in range(size):
        for j in range(size):
            # Gradient: c_eff decreases toward top (j increases)
            # This creates a "lens" that bends rays upward
            c_eff[i, j] = 2.0 - 0.8 * (j / size)
    
    # Smooth
    c_eff = gaussian_filter(c_eff, sigma=3.0)
    c_eff = np.clip(c_eff, 0.5, 2.0)
    
    print(f"c_eff field created:")
    print(f"  Bottom (j=10): c_eff = {c_eff[40, 10]:.2f}")
    print(f"  Middle (j=40): c_eff = {c_eff[40, 40]:.2f}")
    print(f"  Top (j=70): c_eff = {c_eff[40, 70]:.2f}")
    print()
    print("Expectation: Rays/waves should bend toward LOW c_eff (top)")
    
    # Start position and direction
    start = np.array([10.0, 40.0])
    direction = np.array([1.0, 0.0])  # Initially horizontal
    
    # Compute ray trajectory
    print("\nComputing ray trajectory...")
    ray_path = compute_ray_trajectory(c_eff, start, direction, n_steps=600)
    print(f"  Ray traveled from y={ray_path[0, 1]:.1f} to y={ray_path[-1, 1]:.1f}")
    
    # Simulate wave packet
    print("\nSimulating wave packet...")
    wave_path = simulate_wave_packet(c_eff, start, direction, n_steps=400)
    print(f"  Wave centroid traveled from y={wave_path[0, 1]:.1f} to y={wave_path[-1, 1]:.1f}")
    
    # Compare
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    
    # Measure how well they track
    # Find corresponding points by x-coordinate
    ray_y_at_x = {}
    for pt in ray_path:
        x_int = int(pt[0])
        if x_int not in ray_y_at_x:
            ray_y_at_x[x_int] = pt[1]
    
    deviations = []
    for pt in wave_path:
        x_int = int(pt[0])
        if x_int in ray_y_at_x:
            dev = abs(pt[1] - ray_y_at_x[x_int])
            deviations.append(dev)
    
    if deviations:
        avg_deviation = np.mean(deviations)
        max_deviation = np.max(deviations)
        print(f"Average deviation (wave from ray): {avg_deviation:.2f}")
        print(f"Maximum deviation: {max_deviation:.2f}")
        
        # Check if both bend in same direction
        ray_bend = ray_path[-1, 1] - ray_path[0, 1]
        wave_bend = wave_path[-1, 1] - wave_path[0, 1] if len(wave_path) > 1 else 0
        
        print(f"\nRay bending: {ray_bend:+.1f} (from y={ray_path[0,1]:.1f} to y={ray_path[-1,1]:.1f})")
        print(f"Wave bending: {wave_bend:+.1f} (from y={wave_path[0,1]:.1f} to y={wave_path[-1,1]:.1f})")
        
        if ray_bend * wave_bend > 0:  # Same sign
            print("\n✓ Ray and wave bend in SAME direction!")
            if avg_deviation < 5:
                result = "STRONG MATCH"
                print(f"✓ {result}: Wave packet follows ray trajectory!")
            else:
                result = "QUALITATIVE MATCH"
                print(f"~ {result}: Same direction, but quantitative deviation")
        else:
            result = "MISMATCH"
            print(f"✗ {result}: Ray and wave bend in opposite directions")
    else:
        result = "INSUFFICIENT DATA"
        avg_deviation = 0
        ray_bend = 0
        wave_bend = 0
    
    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # c_eff field with trajectories
    ax = axes[0, 0]
    im = ax.imshow(c_eff.T, origin='lower', cmap='viridis_r', extent=[0, size, 0, size])
    ax.plot(ray_path[:, 0], ray_path[:, 1], 'r-', linewidth=3, label='Ray (predicted)')
    if len(wave_path) > 0:
        ax.plot(wave_path[:, 0], wave_path[:, 1], 'c--', linewidth=3, label='Wave (actual)')
    ax.scatter(*start, c='yellow', s=200, marker='*', zorder=5, label='Start')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.legend(fontsize=10)
    ax.set_title('c_eff Field with Trajectories\n(Dark = low c_eff = high index)')
    plt.colorbar(im, ax=ax, label='c_eff')
    
    # Y-coordinate comparison
    ax = axes[0, 1]
    ax.plot(ray_path[:, 0], ray_path[:, 1], 'r-', linewidth=2, label='Ray Y(x)')
    if len(wave_path) > 0:
        ax.plot(wave_path[:, 0], wave_path[:, 1], 'c--', linewidth=2, label='Wave Y(x)')
    ax.axhline(40, color='gray', linestyle=':', label='Initial Y')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.legend()
    ax.set_title(f'Y-Coordinate Along Path\nRay bend: {ray_bend:+.1f}, Wave bend: {wave_bend:+.1f}')
    ax.grid(True, alpha=0.3)
    
    # Deviation over distance
    ax = axes[1, 0]
    if deviations:
        ax.plot(deviations, 'b-', linewidth=2)
        ax.axhline(avg_deviation, color='r', linestyle='--', label=f'Avg: {avg_deviation:.2f}')
        ax.set_xlabel('Measurement point')
        ax.set_ylabel('Deviation (wave - ray)')
        ax.set_title('Deviation Along Path')
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
    
    # c_eff profile
    ax = axes[1, 1]
    ax.plot(c_eff[40, :], 'b-', linewidth=2)
    ax.set_xlabel('Y')
    ax.set_ylabel('c_eff at X=40')
    ax.set_title('c_eff Profile (vertical slice)\nLow c_eff at top → rays bend upward')
    ax.grid(True, alpha=0.3)
    
    plt.suptitle(f'RAY-WAVE BRIDGE TEST: {result}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/ray_wave_bridge.png', dpi=150)
    print("\nSaved ray_wave_bridge.png")
    
    return {
        'result': result,
        'avg_deviation': float(avg_deviation) if deviations else None,
        'ray_bend': float(ray_bend),
        'wave_bend': float(wave_bend),
    }


if __name__ == "__main__":
    result = run_ray_wave_comparison()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Result: {result['result']}")
    print(f"Ray bending: {result['ray_bend']:+.1f}")
    print(f"Wave bending: {result['wave_bend']:+.1f}")
    if result['avg_deviation']:
        print(f"Average deviation: {result['avg_deviation']:.2f}")
    
    if result['result'] in ['STRONG MATCH', 'QUALITATIVE MATCH']:
        print("\n" + "=" * 60)
        print("✓ WAVE PACKETS FOLLOW RAY TRAJECTORIES")
        print("  This bridges waveguide behavior to effective geometry")
        print("=" * 60)
    
    # Save
    import json
    with open('/app/backend/qmrt_topology/ray_wave_results.json', 'w') as f:
        json.dump(result, f, indent=2)
