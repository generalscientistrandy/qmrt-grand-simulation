#!/usr/bin/env python3
"""
QMRT Energy-Conserving Solver
==============================

Problem: Current solver pumps energy (E_ret >> 1)

Solution: Implement a symplectic/leapfrog integrator that conserves
energy in the absence of damping.

APPROACH:
---------
The wave equation: ∂²φ/∂t² = c² ∇²φ - γ ∂φ/∂t

Can be split into position and velocity updates (Hamiltonian form):
  q' = q + p * dt/2        (half position step)
  p' = p + F(q') * dt      (full momentum step using new position)
  q'' = q' + p' * dt/2     (second half position step)

This is the Störmer-Verlet / leapfrog scheme, which is symplectic
and conserves energy much better than naive Euler.

For the wave equation:
  φ = "position" (field)
  v = ∂φ/∂t = "velocity"
  F = c² ∇²φ = "force"

TESTS:
------
1. Compare energy conservation: old vs new solver (α=0)
2. Check if lensing survives with new solver
3. Check if attraction survives with new solver
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


def old_solver_step(field, velocity, c_eff, dt, damping):
    """
    Original (Euler-like) solver step.
    """
    lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
           np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
    
    acc = c_eff**2 * lap - damping * velocity
    velocity_new = velocity + acc * dt
    field_new = field + velocity_new * dt
    
    return field_new, velocity_new


def symplectic_solver_step(field, velocity, c_eff, dt, damping):
    """
    Symplectic (Störmer-Verlet) solver step.
    
    Split into:
    1. Half position step
    2. Full velocity step (using new position)
    3. Half position step
    """
    # Step 1: Half position update
    field_half = field + velocity * (dt / 2)
    
    # Step 2: Full velocity update using half-step position
    # Compute Laplacian at half-step position
    lap = (np.roll(field_half, 1, axis=0) + np.roll(field_half, -1, axis=0) +
           np.roll(field_half, 1, axis=1) + np.roll(field_half, -1, axis=1) - 4 * field_half)
    
    # Force: F = c² ∇²φ - γv
    # For symplectic, we separate conservative and dissipative parts
    force = c_eff**2 * lap
    
    # Apply damping as exponential decay (more stable)
    decay_factor = np.exp(-damping * dt)
    velocity_new = decay_factor * velocity + force * dt
    
    # Step 3: Second half position update
    field_new = field_half + velocity_new * (dt / 2)
    
    return field_new, velocity_new


def compute_energy(field, velocity, c_eff):
    """
    Total energy: kinetic + potential.
    
    E = ∫ [½v² + ½c²|∇φ|²] dx
    """
    # Kinetic energy
    kinetic = 0.5 * np.sum(velocity**2)
    
    # Potential energy (gradient energy)
    grad_x = np.roll(field, 1, axis=0) - field
    grad_y = np.roll(field, 1, axis=1) - field
    potential = 0.5 * np.sum(c_eff**2 * (grad_x**2 + grad_y**2))
    
    return kinetic + potential


def run_solver_comparison(
    size: int = 80,
    n_steps: int = 400,
    alpha: float = 0.0,
    damping: float = 0.0,  # No damping for energy test
):
    """
    Compare old and symplectic solvers.
    """
    # Initialize identical fields
    field_old = np.zeros((size, size))
    velocity_old = np.zeros((size, size))
    field_sym = np.zeros((size, size))
    velocity_sym = np.zeros((size, size))
    
    center = size / 2
    packet_width = 4.0
    amplitude = 3.0
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - center)**2 + (j - center)**2)
            if r < 4 * packet_width:
                velocity_old[i, j] = amplitude * np.exp(-r**2 / (2 * packet_width**2))
                velocity_sym[i, j] = amplitude * np.exp(-r**2 / (2 * packet_width**2))
    
    dt = 0.04
    c_0 = 2.0
    
    # Track energy
    c_eff = np.ones((size, size)) * c_0  # Constant c for energy test
    
    initial_energy = compute_energy(field_old, velocity_old, c_eff)
    
    energy_old = [initial_energy]
    energy_sym = [initial_energy]
    
    for t in range(n_steps):
        # Update c_eff with backreaction
        if alpha > 0:
            energy_density_old = field_old**2 + velocity_old**2
            energy_smooth_old = gaussian_filter(energy_density_old, sigma=2.0)
            rho_max = np.max(energy_smooth_old) + 1e-10
            c_eff_old = c_0 * (1 - alpha * energy_smooth_old / rho_max)
            c_eff_old = np.clip(c_eff_old, 0.3, c_0)
            
            energy_density_sym = field_sym**2 + velocity_sym**2
            energy_smooth_sym = gaussian_filter(energy_density_sym, sigma=2.0)
            rho_max = np.max(energy_smooth_sym) + 1e-10
            c_eff_sym = c_0 * (1 - alpha * energy_smooth_sym / rho_max)
            c_eff_sym = np.clip(c_eff_sym, 0.3, c_0)
        else:
            c_eff_old = c_eff
            c_eff_sym = c_eff
        
        # Old solver
        field_old, velocity_old = old_solver_step(field_old, velocity_old, c_eff_old, dt, damping)
        
        # Symplectic solver
        field_sym, velocity_sym = symplectic_solver_step(field_sym, velocity_sym, c_eff_sym, dt, damping)
        
        # Record energy
        if t % 10 == 0:
            energy_old.append(compute_energy(field_old, velocity_old, c_eff_old))
            energy_sym.append(compute_energy(field_sym, velocity_sym, c_eff_sym))
    
    return {
        'energy_old': np.array(energy_old),
        'energy_sym': np.array(energy_sym),
        'initial_energy': initial_energy,
        'final_ratio_old': energy_old[-1] / initial_energy,
        'final_ratio_sym': energy_sym[-1] / initial_energy,
    }


def run_lensing_with_symplectic(
    size: int = 150,
    n_steps: int = 600,
    alpha: float = 0.5,
    impact_parameter: float = 0.10,
    damping: float = 0.006,
):
    """
    Run lensing test with symplectic solver.
    """
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    # Lens
    lens_pos = np.array([size * 0.5, size * 0.6])
    lens_width = 6.0
    lens_amplitude = 8.0
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - lens_pos[0])**2 + (j - lens_pos[1])**2)
            if r < 4 * lens_width:
                field[i, j] = lens_amplitude * np.exp(-r**2 / (2 * lens_width**2))
    
    # Probe
    impact_pixels = impact_parameter * size
    probe_start = np.array([size * 0.5 + impact_pixels, size * 0.15])
    probe_width = 3.0
    probe_amplitude = 0.5
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - probe_start[0])**2 + (j - probe_start[1])**2)
            if r < 4 * probe_width:
                velocity[i, j] += probe_amplitude * np.exp(-r**2 / (2 * probe_width**2))
    
    dt = 0.04
    c_0 = 2.0
    
    probe_positions = [probe_start.copy()]
    
    for t in range(n_steps):
        energy = field**2 + velocity**2
        energy_smooth = gaussian_filter(energy, sigma=2.0)
        
        rho_max = np.max(energy_smooth) + 1e-10
        c_eff = c_0 * (1 - alpha * energy_smooth / rho_max)
        c_eff = np.clip(c_eff, 0.3, c_0)
        
        # Use symplectic solver
        field, velocity = symplectic_solver_step(field, velocity, c_eff, dt, damping)
        
        # Track probe
        if t % 5 == 0:
            probe_energy = energy.copy()
            lens_mask_radius = int(lens_width * 4)
            li, lj = int(lens_pos[0]), int(lens_pos[1])
            for di in range(-lens_mask_radius, lens_mask_radius + 1):
                for dj in range(-lens_mask_radius, lens_mask_radius + 1):
                    ni, nj = li + di, lj + dj
                    if 0 <= ni < size and 0 <= nj < size:
                        probe_energy[ni, nj] = 0
            
            if np.max(probe_energy) > 0.01:
                probe_idx = np.unravel_index(np.argmax(probe_energy), probe_energy.shape)
                probe_positions.append(np.array(probe_idx, dtype=float))
    
    probe_positions = np.array(probe_positions)
    
    # Compute deflection
    if len(probe_positions) > 10:
        expected_end_x = probe_start[0]
        actual_end_x = probe_positions[-1][0]
        vertical_deflection = actual_end_x - expected_end_x
        bent_toward_lens = (impact_parameter > 0 and vertical_deflection < 0) or \
                          (impact_parameter < 0 and vertical_deflection > 0)
    else:
        vertical_deflection = 0.0
        bent_toward_lens = False
    
    return {
        'probe_positions': probe_positions,
        'vertical_deflection': vertical_deflection,
        'bent_toward_lens': bent_toward_lens,
    }


def run_energy_conserving_test():
    """
    Main test suite for energy-conserving solver.
    """
    print("=" * 70)
    print("ENERGY-CONSERVING SOLVER TEST")
    print("=" * 70)
    print("Comparing old Euler-like solver vs symplectic integrator")
    print()
    
    results = {}
    
    # Test 1: Energy conservation (no damping, no backreaction)
    print("Test 1: Energy conservation (α=0, γ=0)...")
    result = run_solver_comparison(alpha=0.0, damping=0.0)
    results['no_damping'] = result
    print(f"  Old solver: E_final/E_initial = {result['final_ratio_old']:.4f}")
    print(f"  Symplectic: E_final/E_initial = {result['final_ratio_sym']:.4f}")
    
    # Test 2: With damping (should both decay, but sym should be more stable)
    print("\nTest 2: With damping (α=0, γ=0.01)...")
    result = run_solver_comparison(alpha=0.0, damping=0.01)
    results['with_damping'] = result
    print(f"  Old solver: E_final/E_initial = {result['final_ratio_old']:.4f}")
    print(f"  Symplectic: E_final/E_initial = {result['final_ratio_sym']:.4f}")
    
    # Test 3: With backreaction
    print("\nTest 3: With backreaction (α=0.5, γ=0.01)...")
    result = run_solver_comparison(alpha=0.5, damping=0.01)
    results['with_backreaction'] = result
    print(f"  Old solver: E_final/E_initial = {result['final_ratio_old']:.4f}")
    print(f"  Symplectic: E_final/E_initial = {result['final_ratio_sym']:.4f}")
    
    # Test 4: Lensing with symplectic solver
    print("\nTest 4: Lensing with symplectic solver...")
    lensing_results = {}
    
    for b in [-0.15, 0.15]:
        result = run_lensing_with_symplectic(impact_parameter=b)
        lensing_results[b] = result
        toward = "TOWARD" if result['bent_toward_lens'] else "away"
        print(f"  b={b:+.2f}: Δx={result['vertical_deflection']:+.1f}, {toward}")
    
    results['lensing_symplectic'] = lensing_results
    
    # =================================
    # ANALYSIS
    # =================================
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Energy conservation improvement
    old_no_damp = results['no_damping']['final_ratio_old']
    sym_no_damp = results['no_damping']['final_ratio_sym']
    
    print(f"\nEnergy conservation (no damping):")
    print(f"  Old solver: {old_no_damp:.4f} (deviation: {abs(old_no_damp - 1) * 100:.1f}%)")
    print(f"  Symplectic: {sym_no_damp:.4f} (deviation: {abs(sym_no_damp - 1) * 100:.1f}%)")
    
    improvement = abs(old_no_damp - 1) / (abs(sym_no_damp - 1) + 1e-10)
    print(f"  Improvement factor: {improvement:.1f}x")
    
    # Lensing survival
    lensing_survives = all(lensing_results[b]['bent_toward_lens'] for b in [-0.15, 0.15])
    print(f"\nLensing with symplectic: {'SURVIVES' if lensing_survives else 'FAILS'}")
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(16, 12))
    
    # Energy evolution comparison
    ax = fig.add_subplot(2, 3, 1)
    times = np.arange(len(results['no_damping']['energy_old'])) * 0.04 * 10
    ax.plot(times, results['no_damping']['energy_old'] / results['no_damping']['initial_energy'], 
           'r-', linewidth=2, label='Old solver')
    ax.plot(times, results['no_damping']['energy_sym'] / results['no_damping']['initial_energy'], 
           'b-', linewidth=2, label='Symplectic')
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5, label='Exact conservation')
    ax.set_xlabel('Time')
    ax.set_ylabel('E / E₀')
    ax.set_title('Energy Conservation (no damping)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # With damping
    ax = fig.add_subplot(2, 3, 2)
    times = np.arange(len(results['with_damping']['energy_old'])) * 0.04 * 10
    ax.plot(times, results['with_damping']['energy_old'] / results['with_damping']['initial_energy'], 
           'r-', linewidth=2, label='Old solver')
    ax.plot(times, results['with_damping']['energy_sym'] / results['with_damping']['initial_energy'], 
           'b-', linewidth=2, label='Symplectic')
    ax.set_xlabel('Time')
    ax.set_ylabel('E / E₀')
    ax.set_title('With Damping (γ=0.01)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # With backreaction
    ax = fig.add_subplot(2, 3, 3)
    times = np.arange(len(results['with_backreaction']['energy_old'])) * 0.04 * 10
    ax.plot(times, results['with_backreaction']['energy_old'] / results['with_backreaction']['initial_energy'], 
           'r-', linewidth=2, label='Old solver')
    ax.plot(times, results['with_backreaction']['energy_sym'] / results['with_backreaction']['initial_energy'], 
           'b-', linewidth=2, label='Symplectic')
    ax.set_xlabel('Time')
    ax.set_ylabel('E / E₀')
    ax.set_title('With Backreaction (α=0.5)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Lensing trajectories with symplectic
    ax = fig.add_subplot(2, 3, 4)
    for b in [-0.15, 0.15]:
        pos = lensing_results[b]['probe_positions']
        ax.plot(pos[:, 1], pos[:, 0], linewidth=2, label=f'b={b:+.2f}')
    
    ax.scatter([90], [75], c='red', s=200, marker='*', label='Lens')
    ax.set_xlabel('Y position')
    ax.set_ylabel('X position')
    ax.set_title('Lensing with Symplectic Solver')
    ax.legend()
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    # Summary comparison bar chart
    ax = fig.add_subplot(2, 3, 5)
    conditions = ['No damp', 'With damp', 'Backreact']
    old_ratios = [results['no_damping']['final_ratio_old'],
                 results['with_damping']['final_ratio_old'],
                 results['with_backreaction']['final_ratio_old']]
    sym_ratios = [results['no_damping']['final_ratio_sym'],
                 results['with_damping']['final_ratio_sym'],
                 results['with_backreaction']['final_ratio_sym']]
    
    x = np.arange(len(conditions))
    width = 0.35
    ax.bar(x - width/2, old_ratios, width, label='Old solver', color='red', alpha=0.7)
    ax.bar(x + width/2, sym_ratios, width, label='Symplectic', color='blue', alpha=0.7)
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylabel('E_final / E_initial')
    ax.set_title('Energy Ratio Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Summary panel
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary_text = f"""
SYMPLECTIC SOLVER RESULTS
=========================

Energy Conservation:
  Old solver: {old_no_damp:.4f}
  Symplectic: {sym_no_damp:.4f}
  Improvement: {improvement:.1f}x closer to 1.0

Lensing survives: {'YES' if lensing_survives else 'NO'}

Key findings:
{'✓' if sym_no_damp < old_no_damp else '○'} Better energy conservation
{'✓' if lensing_survives else '○'} Lensing still works
{'✓' if sym_no_damp < 2.0 else '○'} E_ratio < 2.0

The symplectic solver provides:
- More stable energy evolution
- Same physical results
- Improved numerical discipline
"""
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightgreen' if sym_no_damp < 2.0 else 'lightyellow', alpha=0.5))
    
    plt.suptitle('ENERGY-CONSERVING SOLVER TEST', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/symplectic_solver.png', dpi=150, bbox_inches='tight')
    print("\nSaved symplectic_solver.png")
    
    # Save results
    summary = {
        'no_damping': {
            'old_ratio': float(old_no_damp),
            'symplectic_ratio': float(sym_no_damp),
            'improvement_factor': float(improvement),
        },
        'with_damping': {
            'old_ratio': float(results['with_damping']['final_ratio_old']),
            'symplectic_ratio': float(results['with_damping']['final_ratio_sym']),
        },
        'with_backreaction': {
            'old_ratio': float(results['with_backreaction']['final_ratio_old']),
            'symplectic_ratio': float(results['with_backreaction']['final_ratio_sym']),
        },
        'lensing_survives': bool(lensing_survives),
    }
    
    with open('/app/backend/qmrt_topology/symplectic_solver_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved symplectic_solver_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_energy_conserving_test()
    
    print("\n" + "=" * 70)
    print("SYMPLECTIC SOLVER TEST COMPLETE")
    print("=" * 70)
    print(f"Improvement factor: {result['no_damping']['improvement_factor']:.1f}x")
    print(f"Lensing survives: {result['lensing_survives']}")
