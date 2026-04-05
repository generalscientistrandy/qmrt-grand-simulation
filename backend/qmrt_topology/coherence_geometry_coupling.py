#!/usr/bin/env python3
"""
QMRT Coherence-Geometry Coupling Analysis
==========================================

KEY INSIGHT: Spacetime = a coherence phase of the medium

Three Tests:
1. FIT SCALING LAW: t_coh ∝ σ₀ (linear) or t_coh ∝ σ₀²/D (diffusion)?
2. MAP COHERENCE FIELD: t_coh(x,y) spatial distribution
3. ENERGY-COHERENCE COUPLING: Does high energy reduce t_coh?

New Concept: Geometry Stability Field
  G(x,y) = t_coh(x,y) / t_obs
  - G >> 1: stable geometry
  - G ~ 1: transition  
  - G << 1: geometry breaks

Two Independent Mechanisms:
  1. curvature ~ ∇c_eff (from speed gradient)
  2. curvature ~ ∇t_coh (from coherence gradient)
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import curve_fit


def compute_geodesic(c_eff: np.ndarray, start: np.ndarray, 
                     direction: np.ndarray, n_steps: int = 500) -> np.ndarray:
    """Compute geodesic from metric."""
    size = c_eff.shape[0]
    
    phi = -np.log(np.clip(c_eff, 0.1, 10.0))
    grad_phi_x = np.gradient(phi, axis=0)
    grad_phi_y = np.gradient(phi, axis=1)
    
    x = np.arange(size)
    y = np.arange(size)
    
    grad_x_interp = RegularGridInterpolator((x, y), grad_phi_x, 
                                             bounds_error=False, fill_value=0)
    grad_y_interp = RegularGridInterpolator((x, y), grad_phi_y,
                                             bounds_error=False, fill_value=0)
    
    pos = start.copy().astype(float)
    vel = direction.copy().astype(float)
    vel = vel / np.linalg.norm(vel)
    
    trajectory = [pos.copy()]
    ds = 0.2
    
    for _ in range(n_steps):
        if not (0 <= pos[0] < size and 0 <= pos[1] < size):
            break
        
        grad_phi = np.array([grad_x_interp(pos)[0], grad_y_interp(pos)[0]])
        grad_dot_v = np.dot(grad_phi, vel)
        acc = grad_phi - grad_dot_v * vel
        
        vel = vel + acc * ds
        vel = vel / np.linalg.norm(vel)
        pos = pos + vel * ds
        
        trajectory.append(pos.copy())
    
    return np.array(trajectory)


def measure_coherence_time(size: int, start: np.ndarray, direction: np.ndarray,
                           c_eff: np.ndarray, initial_width: float,
                           n_steps: int = 600) -> dict:
    """
    Run simulation and measure coherence time.
    
    Returns t_coherence defined as when:
    - error > 2× baseline, OR
    - packet width > 2× initial
    """
    field = np.zeros((size, size))
    velocity = np.zeros((size, size))
    
    for i in range(size):
        for j in range(size):
            r = np.sqrt((i - start[0])**2 + (j - start[1])**2)
            if r < 4 * initial_width:
                velocity[i, j] = 4.0 * np.exp(-r**2 / (2 * initial_width**2))
    
    # Compute geodesic
    geodesic = compute_geodesic(c_eff, start, direction)
    geo_y_at_x = {}
    for pt in geodesic:
        x_int = int(pt[0])
        if x_int not in geo_y_at_x:
            geo_y_at_x[x_int] = pt[1]
    
    dt = 0.04
    damping = 0.008
    
    errors = []
    widths = []
    times = []
    
    for t in range(n_steps):
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        if t % 5 == 0 and t > 10:
            energy = field**2 + velocity**2
            total_energy = np.sum(energy)
            
            if total_energy < 1e-10:
                continue
            
            # Packet width
            cx = np.sum(np.arange(size)[:, None] * energy) / total_energy
            cy = np.sum(np.arange(size)[None, :] * energy) / total_energy
            dx = np.arange(size)[:, None] - cx
            dy = np.arange(size)[None, :] - cy
            r2 = dx**2 + dy**2
            sigma = np.sqrt(np.sum(r2 * energy) / total_energy)
            
            # Peak error
            amp = np.abs(field)
            peak_idx = np.unravel_index(np.argmax(amp), amp.shape)
            x_int = int(peak_idx[0])
            if x_int in geo_y_at_x:
                error = abs(peak_idx[1] - geo_y_at_x[x_int])
            else:
                error = 0
            
            times.append(t * dt)
            widths.append(sigma)
            errors.append(error)
    
    times = np.array(times)
    widths = np.array(widths)
    errors = np.array(errors)
    
    # Find t_coherence
    if len(errors) < 5 or len(widths) < 5:
        return {'t_coherence': 0, 't_dispersion': 0}
    
    baseline_error = np.mean(errors[:5])
    initial_width_measured = widths[0]
    
    # Error threshold
    t_coh_error = times[-1]
    for i, err in enumerate(errors):
        if err > max(baseline_error * 2, 1.0):
            t_coh_error = times[i]
            break
    
    # Width threshold
    t_coh_width = times[-1]
    for i, w in enumerate(widths):
        if w > initial_width_measured * 2:
            t_coh_width = times[i]
            break
    
    t_coherence = min(t_coh_error, t_coh_width)
    
    return {
        't_coherence': t_coherence,
        't_dispersion': t_coh_width,
        'times': times,
        'errors': errors,
        'widths': widths,
    }


def test_1_scaling_law():
    """
    Test 1: Fit t_coh vs σ₀
    
    Linear: t_coh = a × σ₀
    Quadratic: t_coh = b × σ₀²
    """
    print("=" * 70)
    print("TEST 1: SCALING LAW FIT")
    print("=" * 70)
    print("Testing: t_coh ∝ σ₀ (linear) vs t_coh ∝ σ₀² (diffusion)")
    print()
    
    np.random.seed(42)
    
    size = 100
    
    # Create c_eff field
    c_eff = np.ones((size, size)) * 2.0
    for i in range(size):
        for j in range(size):
            normalized_y = (j - size/2) / (size/4)
            c_eff[i, j] = 2.0 - 0.8 * (1 + np.tanh(normalized_y)) / 2
    c_eff = gaussian_filter(c_eff, sigma=1.5)
    c_eff = np.clip(c_eff, 0.5, 2.0)
    
    start = np.array([size * 0.15, size * 0.5])
    direction = np.array([1.0, 0.0])
    
    # Test range of σ₀
    sigmas = np.array([2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0])
    t_cohs = []
    
    for σ0 in sigmas:
        result = measure_coherence_time(size, start, direction, c_eff, σ0)
        t_cohs.append(result['t_coherence'])
        print(f"  σ₀ = {σ0:.1f} → t_coh = {result['t_coherence']:.2f}")
    
    t_cohs = np.array(t_cohs)
    
    # Fit linear: t_coh = a × σ₀
    def linear(x, a):
        return a * x
    
    # Fit quadratic: t_coh = b × σ₀²
    def quadratic(x, b):
        return b * x**2
    
    # Fit both
    try:
        popt_lin, _ = curve_fit(linear, sigmas, t_cohs)
        a = popt_lin[0]
        residuals_lin = t_cohs - linear(sigmas, a)
        ss_lin = np.sum(residuals_lin**2)
    except:
        a = 1.0
        ss_lin = float('inf')
    
    try:
        popt_quad, _ = curve_fit(quadratic, sigmas, t_cohs)
        b = popt_quad[0]
        residuals_quad = t_cohs - quadratic(sigmas, b)
        ss_quad = np.sum(residuals_quad**2)
    except:
        b = 0.1
        ss_quad = float('inf')
    
    print()
    print(f"Linear fit: t_coh = {a:.3f} × σ₀")
    print(f"  Sum of squares: {ss_lin:.3f}")
    print()
    print(f"Quadratic fit: t_coh = {b:.5f} × σ₀²")
    print(f"  Sum of squares: {ss_quad:.3f}")
    
    if ss_lin < ss_quad:
        best_fit = "LINEAR"
        scaling_law = f"t_coh ∝ σ₀"
    else:
        best_fit = "QUADRATIC (diffusion-like)"
        scaling_law = f"t_coh ∝ σ₀²/D"
    
    print()
    print(f">>> BEST FIT: {best_fit}")
    print(f">>> Scaling law: {scaling_law}")
    
    return {
        'sigmas': sigmas,
        't_cohs': t_cohs,
        'linear_coef': float(a),
        'quadratic_coef': float(b),
        'ss_linear': float(ss_lin),
        'ss_quadratic': float(ss_quad),
        'best_fit': best_fit,
        'scaling_law': scaling_law,
    }


def test_2_coherence_field():
    """
    Test 2: Map t_coh(x,y) spatially.
    
    Launch packets from different positions and measure t_coh.
    """
    print("\n" + "=" * 70)
    print("TEST 2: COHERENCE FIELD MAPPING")
    print("=" * 70)
    print("Creating spatial map of t_coh(x,y)")
    print()
    
    np.random.seed(42)
    
    size = 100
    
    # Create c_eff with spatial variation
    c_eff = np.ones((size, size)) * 2.0
    for i in range(size):
        for j in range(size):
            normalized_y = (j - size/2) / (size/4)
            c_eff[i, j] = 2.0 - 0.8 * (1 + np.tanh(normalized_y)) / 2
    c_eff = gaussian_filter(c_eff, sigma=1.5)
    c_eff = np.clip(c_eff, 0.5, 2.0)
    
    direction = np.array([1.0, 0.0])
    initial_width = 4.0
    
    # Sample grid of starting positions
    x_positions = np.linspace(15, 30, 4)
    y_positions = np.linspace(30, 70, 5)
    
    t_coh_map = np.zeros((len(x_positions), len(y_positions)))
    
    for i, x0 in enumerate(x_positions):
        for j, y0 in enumerate(y_positions):
            start = np.array([x0, y0])
            result = measure_coherence_time(size, start, direction, c_eff, 
                                           initial_width, n_steps=400)
            t_coh_map[i, j] = result['t_coherence']
            print(f"  ({x0:.0f}, {y0:.0f}): t_coh = {result['t_coherence']:.2f}")
    
    # Compute geometry stability field G = t_coh / t_obs
    t_obs = 10.0  # Observation timescale
    G_map = t_coh_map / t_obs
    
    print()
    print("Geometry Stability Field G = t_coh / t_obs:")
    print(f"  G >> 1: stable geometry")
    print(f"  G ~ 1: transition")
    print(f"  G << 1: geometry breaks")
    print()
    print(f"  Max G: {np.max(G_map):.2f}")
    print(f"  Min G: {np.min(G_map):.2f}")
    print(f"  Mean G: {np.mean(G_map):.2f}")
    
    return {
        'x_positions': x_positions,
        'y_positions': y_positions,
        't_coh_map': t_coh_map,
        'G_map': G_map,
        'c_eff': c_eff,
        't_obs': t_obs,
    }


def test_3_energy_coherence_coupling():
    """
    Test 3: Does higher energy reduce t_coh?
    
    If yes: energy → curvature → coherence loss
    This would link all three concepts.
    """
    print("\n" + "=" * 70)
    print("TEST 3: ENERGY-COHERENCE COUPLING")
    print("=" * 70)
    print("Question: Does higher energy reduce t_coh?")
    print()
    
    np.random.seed(42)
    
    size = 100
    
    # Create c_eff
    c_eff = np.ones((size, size)) * 2.0
    for i in range(size):
        for j in range(size):
            normalized_y = (j - size/2) / (size/4)
            c_eff[i, j] = 2.0 - 0.8 * (1 + np.tanh(normalized_y)) / 2
    c_eff = gaussian_filter(c_eff, sigma=1.5)
    c_eff = np.clip(c_eff, 0.5, 2.0)
    
    start = np.array([15.0, 50.0])
    direction = np.array([1.0, 0.0])
    initial_width = 4.0
    
    # Test with different initial amplitudes (energy levels)
    amplitudes = [2.0, 4.0, 6.0, 8.0, 10.0]
    results = []
    
    for amp in amplitudes:
        # Custom simulation with variable amplitude
        field = np.zeros((size, size))
        velocity = np.zeros((size, size))
        
        for i in range(size):
            for j in range(size):
                r = np.sqrt((i - start[0])**2 + (j - start[1])**2)
                if r < 4 * initial_width:
                    velocity[i, j] = amp * np.exp(-r**2 / (2 * initial_width**2))
        
        initial_energy = 0.5 * np.sum(velocity**2)
        
        # Run simulation
        geodesic = compute_geodesic(c_eff, start, direction)
        geo_y_at_x = {}
        for pt in geodesic:
            x_int = int(pt[0])
            if x_int not in geo_y_at_x:
                geo_y_at_x[x_int] = pt[1]
        
        dt = 0.04
        damping = 0.008
        
        errors = []
        times = []
        
        for t in range(500):
            lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
                   np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
            
            acc = c_eff**2 * lap - damping * velocity
            velocity += acc * dt
            field += velocity * dt
            
            if t % 5 == 0 and t > 10:
                amp_field = np.abs(field)
                if np.max(amp_field) > 0.01:
                    peak_idx = np.unravel_index(np.argmax(amp_field), amp_field.shape)
                    x_int = int(peak_idx[0])
                    if x_int in geo_y_at_x:
                        error = abs(peak_idx[1] - geo_y_at_x[x_int])
                        times.append(t * dt)
                        errors.append(error)
        
        # Find t_coherence
        t_coh = times[-1] if times else 0
        if len(errors) > 5:
            baseline = np.mean(errors[:5])
            for i, err in enumerate(errors):
                if err > max(baseline * 2, 1.0):
                    t_coh = times[i]
                    break
        
        results.append({
            'amplitude': amp,
            'initial_energy': initial_energy,
            't_coherence': t_coh,
        })
        
        print(f"  Amplitude = {amp:.1f}, Energy = {initial_energy:.1f} → t_coh = {t_coh:.2f}")
    
    # Check correlation
    energies = [r['initial_energy'] for r in results]
    t_cohs = [r['t_coherence'] for r in results]
    
    correlation = np.corrcoef(energies, t_cohs)[0, 1]
    
    print()
    print(f"Correlation(Energy, t_coh): {correlation:.3f}")
    
    if correlation < -0.5:
        verdict = "CONFIRMED: Higher energy → shorter coherence"
        print(f">>> {verdict}")
        print(">>> This links: Energy → Curvature → Coherence loss")
    elif correlation > 0.5:
        verdict = "UNEXPECTED: Higher energy → longer coherence"
        print(f">>> {verdict}")
    else:
        verdict = "NO CLEAR CORRELATION"
        print(f">>> {verdict}")
    
    return {
        'results': results,
        'correlation': float(correlation),
        'verdict': verdict,
    }


def run_all_tests():
    """Run all three coherence-geometry coupling tests."""
    print("=" * 70)
    print("COHERENCE-GEOMETRY COUPLING ANALYSIS")
    print("=" * 70)
    print("Fundamental insight: Spacetime = coherence phase of medium")
    print()
    
    # Test 1
    scaling_results = test_1_scaling_law()
    
    # Test 2
    field_results = test_2_coherence_field()
    
    # Test 3
    energy_results = test_3_energy_coherence_coupling()
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 15))
    
    # Test 1: Scaling law
    ax = fig.add_subplot(2, 3, 1)
    sigmas = scaling_results['sigmas']
    t_cohs = scaling_results['t_cohs']
    
    ax.plot(sigmas, t_cohs, 'bo-', markersize=10, linewidth=2, label='Data')
    
    # Plot fits
    sigma_fine = np.linspace(sigmas.min(), sigmas.max(), 100)
    ax.plot(sigma_fine, scaling_results['linear_coef'] * sigma_fine, 
           'r--', linewidth=2, label=f'Linear: {scaling_results["linear_coef"]:.2f}σ₀')
    ax.plot(sigma_fine, scaling_results['quadratic_coef'] * sigma_fine**2, 
           'g--', linewidth=2, label=f'Quadratic: {scaling_results["quadratic_coef"]:.4f}σ₀²')
    
    ax.set_xlabel('Initial Width σ₀')
    ax.set_ylabel('Coherence Time t_coh')
    ax.set_title(f'Scaling Law: {scaling_results["best_fit"]}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Test 1: Log-log plot
    ax = fig.add_subplot(2, 3, 2)
    ax.loglog(sigmas, t_cohs, 'bo-', markersize=10, linewidth=2)
    
    # Fit power law
    log_sigmas = np.log(sigmas)
    log_t_cohs = np.log(t_cohs)
    slope, intercept = np.polyfit(log_sigmas, log_t_cohs, 1)
    
    ax.loglog(sigma_fine, np.exp(intercept) * sigma_fine**slope, 'r--', 
             linewidth=2, label=f't_coh ∝ σ₀^{slope:.2f}')
    
    ax.set_xlabel('σ₀ (log scale)')
    ax.set_ylabel('t_coh (log scale)')
    ax.set_title(f'Power Law: t_coh ∝ σ₀^{slope:.2f}')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both')
    
    # Test 2: c_eff field
    ax = fig.add_subplot(2, 3, 3)
    c_eff = field_results['c_eff']
    im = ax.imshow(c_eff.T, origin='lower', cmap='viridis_r', 
                  extent=[0, 100, 0, 100])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('c_eff Field')
    plt.colorbar(im, ax=ax, label='c_eff')
    
    # Test 2: t_coh map
    ax = fig.add_subplot(2, 3, 4)
    X, Y = np.meshgrid(field_results['x_positions'], field_results['y_positions'])
    im = ax.pcolormesh(X, Y, field_results['t_coh_map'].T, cmap='plasma')
    ax.set_xlabel('X Start Position')
    ax.set_ylabel('Y Start Position')
    ax.set_title('Coherence Time t_coh(x,y)')
    plt.colorbar(im, ax=ax, label='t_coh')
    
    # Test 2: Geometry stability field G
    ax = fig.add_subplot(2, 3, 5)
    im = ax.pcolormesh(X, Y, field_results['G_map'].T, cmap='RdYlGn',
                       vmin=0, vmax=2)
    ax.set_xlabel('X Start Position')
    ax.set_ylabel('Y Start Position')
    ax.set_title(f'Geometry Stability G = t_coh/t_obs\n(Green=stable, Red=breaks)')
    plt.colorbar(im, ax=ax, label='G')
    
    # Test 3: Energy-coherence coupling
    ax = fig.add_subplot(2, 3, 6)
    energies = [r['initial_energy'] for r in energy_results['results']]
    t_cohs_energy = [r['t_coherence'] for r in energy_results['results']]
    
    ax.plot(energies, t_cohs_energy, 'bo-', markersize=10, linewidth=2)
    ax.set_xlabel('Initial Energy')
    ax.set_ylabel('Coherence Time t_coh')
    ax.set_title(f'Energy-Coherence Coupling\nCorr = {energy_results["correlation"]:.2f}')
    ax.grid(True, alpha=0.3)
    
    # Summary
    plt.suptitle('COHERENCE-GEOMETRY COUPLING ANALYSIS\n'
                'Spacetime = Coherence Phase of Medium', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/coherence_geometry_coupling.png', dpi=150,
               bbox_inches='tight')
    print("\nSaved coherence_geometry_coupling.png")
    
    # Save results
    import json
    summary = {
        'scaling_law': {
            'best_fit': scaling_results['best_fit'],
            'power_exponent': float(slope),
            'formula': f't_coh ∝ σ₀^{slope:.2f}',
        },
        'coherence_field': {
            'max_G': float(np.max(field_results['G_map'])),
            'min_G': float(np.min(field_results['G_map'])),
            't_obs': field_results['t_obs'],
        },
        'energy_coupling': {
            'correlation': energy_results['correlation'],
            'verdict': energy_results['verdict'],
        },
        'fundamental_insight': (
            "Spacetime = a coherence phase of the medium. "
            "Geometry exists conditionally, only where coherence length >> wavelength. "
            "Two curvature mechanisms: (1) ∇c_eff, (2) ∇t_coh."
        )
    }
    
    with open('/app/backend/qmrt_topology/coherence_geometry_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved coherence_geometry_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_all_tests()
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Scaling law: {result['scaling_law']['formula']}")
    print(f"Energy-coherence correlation: {result['energy_coupling']['correlation']:.2f}")
    print()
    print(result['fundamental_insight'])
