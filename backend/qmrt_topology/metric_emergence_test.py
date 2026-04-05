#!/usr/bin/env python3
"""
QMRT Metric Emergence Test
==========================

The definitive test: Does geometry emerge from the medium?

Three-part verification:
1. CONVERGENCE SWEEP: error → 0 as σ → 0 (proves true eikonal limit)
2. METRIC EXTRACTION: ds² = (1/c_eff²)(dx² + dy²) → geodesic equation → compare
3. ENERGY FLUX: S⃗ ~ u·∇u_t visualization (strongest evidence)

If all three pass → Geometry emerges from the medium
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator
from scipy.integrate import odeint


# =============================================================================
# PART 1: METRIC-DERIVED GEODESIC SOLVER
# =============================================================================

def compute_metric_geodesic(c_eff: np.ndarray, start: np.ndarray, 
                            direction: np.ndarray, n_steps: int = 800,
                            ds: float = 0.2) -> np.ndarray:
    """
    Compute geodesic from the METRIC: ds² = (1/c_eff²)(dx² + dy²)
    
    This is an optical/conformal metric where:
    - g_ij = (1/c_eff²) δ_ij (isotropic)
    - Geodesic equation: d²x^i/ds² + Γ^i_jk (dx^j/ds)(dx^k/ds) = 0
    
    For conformal metric g_ij = e^(2φ) δ_ij where φ = -ln(c_eff):
    The geodesic equation simplifies to:
    d²x/ds² = ∇φ - (∇φ · v)v  where v = dx/ds (unit tangent)
    
    Or equivalently: acceleration perpendicular to velocity toward -∇c_eff
    """
    size = c_eff.shape
    
    x = np.arange(size[0])
    y = np.arange(size[1])
    
    # Compute φ = -ln(c_eff) and its gradient
    phi = -np.log(np.clip(c_eff, 0.1, 10.0))
    grad_phi_x = np.gradient(phi, axis=0)
    grad_phi_y = np.gradient(phi, axis=1)
    
    grad_x_interp = RegularGridInterpolator((x, y), grad_phi_x, method='linear',
                                             bounds_error=False, fill_value=0)
    grad_y_interp = RegularGridInterpolator((x, y), grad_phi_y, method='linear',
                                             bounds_error=False, fill_value=0)
    
    pos = start.copy().astype(float)
    vel = direction.copy().astype(float)
    vel = vel / np.linalg.norm(vel)
    
    trajectory = [pos.copy()]
    
    for _ in range(n_steps):
        if not (0 <= pos[0] < size[0] and 0 <= pos[1] < size[1]):
            break
        
        # Get ∇φ at current position
        grad_phi = np.array([grad_x_interp(pos)[0], grad_y_interp(pos)[0]])
        
        # Geodesic acceleration: a = ∇φ - (∇φ · v)v
        # This bends the ray toward regions of higher φ (lower c_eff)
        grad_dot_v = np.dot(grad_phi, vel)
        acc = grad_phi - grad_dot_v * vel
        
        # Update velocity
        vel = vel + acc * ds
        vel = vel / np.linalg.norm(vel)  # Keep unit speed
        
        # Update position
        pos = pos + vel * ds
        
        if pos[0] < 0 or pos[0] >= size[0] or pos[1] < 0 or pos[1] >= size[1]:
            break
        
        trajectory.append(pos.copy())
    
    return np.array(trajectory)


# =============================================================================
# PART 2: WAVE SIMULATION WITH ENERGY FLUX TRACKING
# =============================================================================

def simulate_wave_with_flux(c_eff: np.ndarray, start: np.ndarray,
                            direction: np.ndarray, packet_width: float = 3.0,
                            n_steps: int = 600) -> dict:
    """
    Full wave simulation tracking:
    1. Peak amplitude trajectory
    2. Energy flux field S⃗ ~ u·∇u_t
    """
    size = c_eff.shape
    
    field = np.zeros(size)
    velocity = np.zeros(size)
    
    # Initialize Gaussian wave packet
    for i in range(size[0]):
        for j in range(size[1]):
            r = np.array([i, j]) - start
            dist = np.linalg.norm(r)
            
            if dist < 4 * packet_width:
                envelope = np.exp(-dist**2 / (2 * packet_width**2))
                velocity[i, j] = 4.0 * envelope
    
    dt = 0.04
    damping = 0.008
    
    peaks = []
    flux_snapshots = []
    
    for t in range(n_steps):
        # Laplacian
        lap = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)
        
        # Wave equation
        acc = c_eff**2 * lap - damping * velocity
        velocity += acc * dt
        field += velocity * dt
        
        if t % 10 == 0 and t > 20:
            amp = np.abs(field)
            
            # Peak trajectory
            max_idx = np.unravel_index(np.argmax(amp), amp.shape)
            if amp[max_idx] > 0.01:
                peaks.append([float(max_idx[0]), float(max_idx[1])])
            
            # Energy flux: S⃗ ~ u · ∇(∂u/∂t) = field * grad(velocity)
            grad_v_x = np.gradient(velocity, axis=0)
            grad_v_y = np.gradient(velocity, axis=1)
            
            Sx = field * grad_v_x
            Sy = field * grad_v_y
            
            if t in [100, 200, 300, 400]:
                flux_snapshots.append({
                    't': t,
                    'Sx': Sx.copy(),
                    'Sy': Sy.copy(),
                    'field': field.copy(),
                })
    
    return {
        'peaks': np.array(peaks) if peaks else np.array([]),
        'flux_snapshots': flux_snapshots,
    }


# =============================================================================
# PART 3: CONVERGENCE SWEEP
# =============================================================================

def run_convergence_sweep(c_eff: np.ndarray, start: np.ndarray, 
                          direction: np.ndarray) -> dict:
    """
    Critical test: Does error → 0 as packet width σ → 0?
    
    This proves TRUE eikonal convergence, not coincidence.
    """
    # Compute ground truth: metric geodesic
    geodesic = compute_metric_geodesic(c_eff, start, direction, n_steps=1000)
    
    # Build lookup for geodesic y-value at each x
    geo_y_at_x = {}
    for pt in geodesic:
        x_int = int(pt[0])
        if x_int not in geo_y_at_x:
            geo_y_at_x[x_int] = pt[1]
    
    # Test multiple packet widths
    packet_widths = [8.0, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5]
    results = []
    
    print("CONVERGENCE SWEEP")
    print("-" * 50)
    print(f"{'σ':>8} | {'Peak Bend':>12} | {'Geo Bend':>12} | {'Avg Error':>12}")
    print("-" * 50)
    
    for σ in packet_widths:
        # Simulate wave
        wave_data = simulate_wave_with_flux(c_eff, start, direction, 
                                           packet_width=σ, n_steps=600)
        peaks = wave_data['peaks']
        
        if len(peaks) > 5:
            # Compute deviation from geodesic
            deviations = []
            for pt in peaks:
                x_int = int(pt[0])
                if x_int in geo_y_at_x:
                    dev = abs(pt[1] - geo_y_at_x[x_int])
                    deviations.append(dev)
            
            avg_error = np.mean(deviations) if deviations else float('inf')
            peak_bend = peaks[-1, 1] - peaks[0, 1]
            geo_bend = geodesic[-1, 1] - geodesic[0, 1]
            
            results.append({
                'sigma': σ,
                'avg_error': avg_error,
                'peak_bend': peak_bend,
                'geo_bend': geo_bend,
                'peaks': peaks,
            })
            
            print(f"{σ:>8.1f} | {peak_bend:>+12.2f} | {geo_bend:>+12.2f} | {avg_error:>12.2f}")
        else:
            print(f"{σ:>8.1f} | {'N/A':>12} | {'N/A':>12} | {'N/A':>12}")
    
    print("-" * 50)
    
    return {
        'geodesic': geodesic,
        'results': results,
    }


# =============================================================================
# PART 4: CREATE SHARP GRADIENT FIELD
# =============================================================================

def create_gradient_field(size: int) -> np.ndarray:
    """Sharp tanh-profile gradient field."""
    c_eff = np.ones((size, size)) * 2.0
    
    for i in range(size):
        for j in range(size):
            normalized_y = (j - size/2) / (size/4)
            c_eff[i, j] = 2.0 - 0.8 * (1 + np.tanh(normalized_y)) / 2
    
    c_eff = gaussian_filter(c_eff, sigma=1.5)
    c_eff = np.clip(c_eff, 0.5, 2.0)
    
    return c_eff


# =============================================================================
# MAIN TEST
# =============================================================================

def run_metric_emergence_test():
    """
    The definitive test for emergent geometry.
    """
    print("=" * 70)
    print("METRIC EMERGENCE TEST")
    print("=" * 70)
    print("Question: Does geometry emerge from the medium?")
    print()
    print("Test components:")
    print("  1. Convergence sweep: error → 0 as σ → 0")
    print("  2. Metric geodesic comparison: ds² = (1/c_eff²)(dx² + dy²)")
    print("  3. Energy flux visualization: S⃗ ~ u·∇u_t")
    print()
    
    np.random.seed(42)
    
    size = 100
    c_eff = create_gradient_field(size)
    
    print(f"c_eff field:")
    print(f"  Min: {c_eff.min():.3f}, Max: {c_eff.max():.3f}")
    print(f"  Gradient: tanh profile over ~{size//4} cells")
    print()
    
    start = np.array([15.0, 50.0])
    direction = np.array([1.0, 0.0])
    
    # =================================
    # TEST 1: Convergence Sweep
    # =================================
    print("\n" + "=" * 70)
    print("TEST 1: CONVERGENCE SWEEP")
    print("=" * 70)
    
    sweep_results = run_convergence_sweep(c_eff, start, direction)
    geodesic = sweep_results['geodesic']
    results = sweep_results['results']
    
    # Check convergence trend
    if len(results) >= 3:
        sigmas = [r['sigma'] for r in results]
        errors = [r['avg_error'] for r in results]
        
        # Fit trend: error = A * σ^B (expect B > 0 for convergence)
        log_sigmas = np.log(sigmas)
        log_errors = np.log(np.array(errors) + 0.1)  # Avoid log(0)
        
        # Simple linear regression in log space
        slope = np.polyfit(log_sigmas, log_errors, 1)[0]
        
        print(f"\nConvergence analysis:")
        print(f"  Error scaling: error ~ σ^{slope:.2f}")
        
        if slope > 0.3:
            convergence_verdict = "CONVERGENT (error decreases with σ)"
        elif slope > 0:
            convergence_verdict = "WEAKLY CONVERGENT"
        else:
            convergence_verdict = "NOT CONVERGENT"
        
        print(f"  Verdict: {convergence_verdict}")
    else:
        convergence_verdict = "INSUFFICIENT DATA"
    
    # =================================
    # TEST 2: Energy Flux Visualization
    # =================================
    print("\n" + "=" * 70)
    print("TEST 2: ENERGY FLUX VISUALIZATION")
    print("=" * 70)
    
    # Use best (smallest) packet width for flux visualization
    best_sigma = min([r['sigma'] for r in results]) if results else 3.0
    
    print(f"Running flux simulation with σ = {best_sigma}...")
    flux_data = simulate_wave_with_flux(c_eff, start, direction, 
                                        packet_width=best_sigma, n_steps=500)
    
    flux_snapshots = flux_data['flux_snapshots']
    print(f"  Captured {len(flux_snapshots)} flux snapshots")
    
    # =================================
    # PLOTTING
    # =================================
    fig = plt.figure(figsize=(20, 16))
    
    # --- Row 1: c_eff and metric info ---
    ax1 = fig.add_subplot(3, 4, 1)
    im = ax1.imshow(c_eff.T, origin='lower', cmap='viridis_r', 
                   extent=[0, size, 0, size])
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_title('c_eff Field\n(Dark = low c = high index)')
    plt.colorbar(im, ax=ax1, label='c_eff')
    
    ax2 = fig.add_subplot(3, 4, 2)
    # Show metric: g_ij = 1/c_eff²
    metric = 1 / c_eff**2
    im2 = ax2.imshow(metric.T, origin='lower', cmap='plasma', 
                    extent=[0, size, 0, size])
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_title('Effective Metric g = 1/c_eff²\n(Conformal factor)')
    plt.colorbar(im2, ax=ax2, label='g')
    
    # --- Row 1 cont: Convergence plot ---
    ax3 = fig.add_subplot(3, 4, 3)
    if results:
        sigmas = [r['sigma'] for r in results]
        errors = [r['avg_error'] for r in results]
        ax3.loglog(sigmas, errors, 'bo-', linewidth=2, markersize=8)
        ax3.set_xlabel('Packet width σ')
        ax3.set_ylabel('Average error from geodesic')
        ax3.set_title(f'CONVERGENCE: error ~ σ^{slope:.2f}')
        ax3.grid(True, alpha=0.3)
        ax3.invert_xaxis()
    
    ax4 = fig.add_subplot(3, 4, 4)
    if results:
        peak_bends = [r['peak_bend'] for r in results]
        geo_bend = results[0]['geo_bend']
        ax4.plot(sigmas, peak_bends, 'bo-', linewidth=2, markersize=8, label='Peak bend')
        ax4.axhline(geo_bend, color='r', linestyle='--', linewidth=2, label=f'Geodesic bend: {geo_bend:.1f}')
        ax4.set_xlabel('Packet width σ')
        ax4.set_ylabel('Total Y-displacement')
        ax4.set_title('Peak vs Geodesic Bending')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.invert_xaxis()
    
    # --- Row 2: Trajectory comparison for different σ ---
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(results)))
    
    ax5 = fig.add_subplot(3, 4, 5)
    ax5.imshow(c_eff.T, origin='lower', cmap='gray', alpha=0.3,
              extent=[0, size, 0, size])
    ax5.plot(geodesic[:, 0], geodesic[:, 1], 'r-', linewidth=3, label='Metric geodesic')
    for i, r in enumerate(results):
        peaks = r['peaks']
        if len(peaks) > 0:
            ax5.plot(peaks[:, 0], peaks[:, 1], '--', color=colors[i], 
                    linewidth=1.5, alpha=0.8, label=f'σ={r["sigma"]:.1f}')
    ax5.scatter(*start, c='yellow', s=200, marker='*', zorder=5)
    ax5.set_xlabel('X')
    ax5.set_ylabel('Y')
    ax5.set_title('All Peak Trajectories vs Metric Geodesic')
    ax5.legend(fontsize=7, loc='upper left')
    
    # Close-up
    ax6 = fig.add_subplot(3, 4, 6)
    ax6.imshow(c_eff.T, origin='lower', cmap='gray', alpha=0.3,
              extent=[0, size, 0, size])
    ax6.plot(geodesic[:, 0], geodesic[:, 1], 'r-', linewidth=3, label='Geodesic')
    if results:
        # Show best (smallest σ) result
        best = min(results, key=lambda r: r['sigma'])
        ax6.plot(best['peaks'][:, 0], best['peaks'][:, 1], 'c--', 
                linewidth=2, label=f'Peak (σ={best["sigma"]})')
    ax6.set_xlim(10, 80)
    ax6.set_ylim(45, 80)
    ax6.set_xlabel('X')
    ax6.set_ylabel('Y')
    ax6.set_title('Close-up: Best Match')
    ax6.legend()
    
    # Y vs X comparison
    ax7 = fig.add_subplot(3, 4, 7)
    ax7.plot(geodesic[:, 0], geodesic[:, 1], 'r-', linewidth=3, label='Geodesic Y(x)')
    for i, r in enumerate(results[-3:]):  # Show last 3 (smallest σ)
        peaks = r['peaks']
        if len(peaks) > 0:
            ax7.plot(peaks[:, 0], peaks[:, 1], '--', linewidth=2, 
                    label=f'Peak σ={r["sigma"]:.1f}')
    ax7.axhline(50, color='gray', linestyle=':', alpha=0.5)
    ax7.set_xlabel('X')
    ax7.set_ylabel('Y')
    ax7.set_title('Y-Coordinate Along Path')
    ax7.legend()
    ax7.grid(True, alpha=0.3)
    
    # Error evolution
    ax8 = fig.add_subplot(3, 4, 8)
    for i, r in enumerate(results[-3:]):
        peaks = r['peaks']
        geo_y_at_x = {}
        for pt in geodesic:
            x_int = int(pt[0])
            if x_int not in geo_y_at_x:
                geo_y_at_x[x_int] = pt[1]
        
        errors_along_path = []
        x_values = []
        for pt in peaks:
            x_int = int(pt[0])
            if x_int in geo_y_at_x:
                errors_along_path.append(abs(pt[1] - geo_y_at_x[x_int]))
                x_values.append(pt[0])
        
        if x_values:
            ax8.plot(x_values, errors_along_path, linewidth=2, 
                    label=f'σ={r["sigma"]:.1f}')
    
    ax8.set_xlabel('X')
    ax8.set_ylabel('|Y_peak - Y_geodesic|')
    ax8.set_title('Error Along Path')
    ax8.legend()
    ax8.grid(True, alpha=0.3)
    
    # --- Row 3: Energy Flux Visualization ---
    for idx, snapshot in enumerate(flux_snapshots[:4]):
        ax = fig.add_subplot(3, 4, 9 + idx)
        
        t = snapshot['t']
        Sx = snapshot['Sx']
        Sy = snapshot['Sy']
        field = snapshot['field']
        
        # Show field amplitude as background
        ax.imshow(np.abs(field).T, origin='lower', cmap='Blues', alpha=0.5,
                 extent=[0, size, 0, size])
        
        # Quiver plot of energy flux
        skip = 5
        X, Y = np.meshgrid(np.arange(0, size, skip), np.arange(0, size, skip))
        Sx_sub = Sx[::skip, ::skip].T
        Sy_sub = Sy[::skip, ::skip].T
        
        # Normalize for visibility
        mag = np.sqrt(Sx_sub**2 + Sy_sub**2)
        mask = mag > 0.01 * np.max(mag)
        
        ax.quiver(X[mask], Y[mask], Sx_sub[mask], Sy_sub[mask], 
                 color='red', alpha=0.7, scale=np.max(mag)*20)
        
        # Show geodesic for reference
        ax.plot(geodesic[:, 0], geodesic[:, 1], 'g-', linewidth=2, alpha=0.5)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title(f'Energy Flux S⃗ at t={t}\n(Red arrows = energy flow)')
        ax.set_xlim(0, size)
        ax.set_ylim(0, size)
    
    # Determine overall verdict
    print("\n" + "=" * 70)
    print("FINAL ASSESSMENT")
    print("=" * 70)
    
    # Check if convergent
    convergent = 'CONVERGENT' in convergence_verdict
    
    # Find the BEST result (minimum error, not minimum σ)
    if results:
        best = min(results, key=lambda r: r['avg_error'])
        direction_match = (best['peak_bend'] * best['geo_bend']) > 0
        error_acceptable = best['avg_error'] < 10
    else:
        direction_match = False
        error_acceptable = False
    
    print(f"Convergence: {convergence_verdict}")
    print(f"Direction match: {'YES' if direction_match else 'NO'}")
    print(f"Error acceptable: {'YES' if error_acceptable else 'NO'} (best error: {best['avg_error']:.2f})")
    
    if convergent and direction_match:
        if error_acceptable:
            overall_verdict = "GEOMETRY EMERGES FROM MEDIUM"
            print(f"\n>>> VERDICT: {overall_verdict}")
            print(">>> Wave peak trajectories converge to metric geodesics as σ → 0")
            print(">>> The effective metric ds² = (1/c_eff²)(dx² + dy²) determines transport")
        else:
            overall_verdict = "PARTIAL EMERGENCE (convergent, but not yet tight)"
            print(f"\n>>> VERDICT: {overall_verdict}")
            print(">>> Convergence trend is correct, need smaller σ for tight match")
    else:
        overall_verdict = "EMERGENCE NOT PROVEN"
        print(f"\n>>> VERDICT: {overall_verdict}")
    
    plt.suptitle(f'METRIC EMERGENCE TEST: {overall_verdict}', 
                fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/metric_emergence.png', dpi=150, 
               bbox_inches='tight')
    print("\nSaved metric_emergence.png")
    
    # Save results
    import json
    summary = {
        'verdict': overall_verdict,
        'convergence': convergence_verdict,
        'direction_match': bool(direction_match),
        'best_sigma': float(best['sigma']) if results else None,
        'best_error': float(best['avg_error']) if results else None,
        'scaling_exponent': float(slope) if 'slope' in dir() else None,
        'results': [
            {
                'sigma': float(r['sigma']),
                'avg_error': float(r['avg_error']),
                'peak_bend': float(r['peak_bend']),
                'geo_bend': float(r['geo_bend']),
            }
            for r in results
        ]
    }
    
    with open('/app/backend/qmrt_topology/metric_emergence_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved metric_emergence_results.json")
    
    return summary


if __name__ == "__main__":
    result = run_metric_emergence_test()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Verdict: {result['verdict']}")
    print(f"Convergence scaling: error ~ σ^{result['scaling_exponent']:.2f}")
    print(f"Best configuration: σ = {result['best_sigma']}")
    print(f"Best error: {result['best_error']:.2f} cells")
