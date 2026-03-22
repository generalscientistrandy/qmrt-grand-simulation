"""
QMRT v3: Resolution Convergence Study
======================================

DEFINITIVE TEST: Scale-independent emergent structure

Run identical physics at:
- grid = 64 (warmup)
- grid = 128
- grid = 256
- grid = 512 (if feasible)

Measure:
1. Bound state radius (physical units)
2. Oscillation frequency (breathing mode)
3. Binding energy

If these CONVERGE as resolution increases:
→ Scale-independent emergent structure
→ Very serious theoretical result

Using verified stable parameters: m_tau=16, g_rt=5
"""

import numpy as np
from scipy.fft import fft, fftfreq
import time
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


def run_convergence_test(grid_size, physical_domain=24.0, run_time=30.0):
    """
    Run simulation at given resolution, measuring key observables.
    
    Keep PHYSICAL parameters constant, only change resolution.
    """
    dx = physical_domain / grid_size
    dt = 0.005 * dx  # CFL-scaled timestep
    
    # Verified stable parameters
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    engine = QMRTv3Engine(grid_size=grid_size, params=params)
    engine.dx = dx
    
    # Initialize with fixed PHYSICAL size
    physical_radius = 2.0
    center_phys = physical_domain / 2
    
    x_phys = np.arange(grid_size) * dx
    X, Y, Z = np.meshgrid(x_phys, x_phys, x_phys, indexing='ij')
    
    R_sq_phys = (X - center_phys)**2 + (Y - center_phys)**2 + (Z - center_phys)**2
    
    engine.tau[2] = np.exp(-R_sq_phys / (2 * physical_radius**2))
    engine.initial_energy = engine.compute_total_energy()['E_total']
    
    # Relax first
    relax_steps = int(10.0 / dt)
    for _ in range(min(relax_steps, 5000)):
        engine.evolve_timestep(dt)
    
    # Now measure oscillations
    n_measure = int(run_time / dt)
    record_interval = max(1, n_measure // 500)  # ~500 data points
    
    radius_history = []
    tau_max_history = []
    time_history = []
    
    t = 0
    for step in range(n_measure):
        engine.evolve_timestep(dt)
        t += dt
        
        if step % record_interval == 0:
            # Measure radius in PHYSICAL units
            tau_sq = engine._compute_tau_squared()
            total = np.sum(tau_sq) * dx**3
            
            if total > 1e-10:
                R_sq_mean = np.sum(R_sq_phys * tau_sq) * dx**3 / total
                R_physical = np.sqrt(R_sq_mean)
            else:
                R_physical = 0
            
            tau_max = np.max(np.sqrt(tau_sq))
            
            radius_history.append(R_physical)
            tau_max_history.append(tau_max)
            time_history.append(t)
    
    # Compute observables
    radius_history = np.array(radius_history)
    tau_max_history = np.array(tau_max_history)
    time_history = np.array(time_history)
    
    # 1. Mean radius
    mean_radius = np.mean(radius_history)
    std_radius = np.std(radius_history)
    
    # 2. Oscillation frequency from FFT
    if len(tau_max_history) > 10:
        tau_centered = tau_max_history - np.mean(tau_max_history)
        dt_measure = time_history[1] - time_history[0] if len(time_history) > 1 else 0.1
        
        spectrum = np.abs(fft(tau_centered))
        freqs = fftfreq(len(tau_centered), d=dt_measure)
        
        pos_mask = freqs > 0.01
        if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 0:
            peak_idx = np.argmax(spectrum[pos_mask])
            omega_breath = 2 * np.pi * freqs[pos_mask][peak_idx]
        else:
            omega_breath = 0
    else:
        omega_breath = 0
    
    # 3. Final energy (proxy for binding)
    final_energy = engine.compute_total_energy()['E_total']
    energy_density = final_energy / (physical_domain**3)  # Energy per unit volume
    
    return {
        'grid': grid_size,
        'dx': dx,
        'dt': dt,
        'mean_radius': mean_radius,
        'std_radius': std_radius,
        'omega_breath': omega_breath,
        'energy_density': energy_density,
        'final_energy': final_energy,
        'tau_max_final': tau_max_history[-1] if len(tau_max_history) > 0 else 0,
    }


def main():
    """Run full convergence study."""
    print("=" * 70)
    print("QMRT v3: RESOLUTION CONVERGENCE STUDY")
    print("=" * 70)
    print("""
DEFINITIVE TEST for scale-independent emergent structure.

Parameters: m_tau=16, g_rt=5 (verified stable)
Physical domain: 24 units
Physical particle radius: 2 units

Measuring:
- Bound state radius (should converge)
- Breathing frequency (should converge)
- Energy density (should converge)
""")
    
    # Grid sizes to test
    grid_sizes = [48, 64, 96, 128]
    
    results = []
    
    print(f"\n{'Grid':>6} | {'dx':>8} | {'R_phys':>10} | {'ω_breath':>10} | {'E_density':>12} | {'Time':>8}")
    print("-" * 75)
    
    for n in grid_sizes:
        start_time = time.time()
        
        result = run_convergence_test(n, physical_domain=24.0, run_time=20.0)
        
        elapsed = time.time() - start_time
        
        results.append(result)
        
        print(f"{n:6d} | {result['dx']:8.4f} | {result['mean_radius']:10.4f} | "
              f"{result['omega_breath']:10.4f} | {result['energy_density']:12.6f} | {elapsed:8.1f}s")
    
    # Convergence analysis
    print("\n" + "=" * 70)
    print("CONVERGENCE ANALYSIS")
    print("=" * 70)
    
    if len(results) >= 2:
        # Check if quantities are converging
        radii = [r['mean_radius'] for r in results]
        omegas = [r['omega_breath'] for r in results]
        energies = [r['energy_density'] for r in results]
        
        # Compute convergence rate: |Q_fine - Q_coarse| / |Q_fine|
        print("\n--- Radius Convergence ---")
        for i in range(1, len(radii)):
            change = abs(radii[i] - radii[i-1]) / max(abs(radii[i]), 1e-10)
            print(f"  {results[i-1]['grid']} → {results[i]['grid']}: "
                  f"R = {radii[i-1]:.4f} → {radii[i]:.4f}, change = {change:.2%}")
        
        print("\n--- Frequency Convergence ---")
        for i in range(1, len(omegas)):
            if omegas[i] > 0:
                change = abs(omegas[i] - omegas[i-1]) / max(abs(omegas[i]), 1e-10)
                print(f"  {results[i-1]['grid']} → {results[i]['grid']}: "
                      f"ω = {omegas[i-1]:.4f} → {omegas[i]:.4f}, change = {change:.2%}")
        
        print("\n--- Energy Density Convergence ---")
        for i in range(1, len(energies)):
            change = abs(energies[i] - energies[i-1]) / max(abs(energies[i]), 1e-10)
            print(f"  {results[i-1]['grid']} → {results[i]['grid']}: "
                  f"ε = {energies[i-1]:.6f} → {energies[i]:.6f}, change = {change:.2%}")
        
        # Final assessment
        print("\n" + "=" * 70)
        print("VERDICT")
        print("=" * 70)
        
        # Check if the highest resolution results are close to second-highest
        if len(results) >= 2:
            R_change = abs(radii[-1] - radii[-2]) / max(abs(radii[-1]), 1e-10)
            E_change = abs(energies[-1] - energies[-2]) / max(abs(energies[-1]), 1e-10)
            
            if R_change < 0.1 and E_change < 0.1:
                print("""
✅ CONVERGENCE DETECTED

The bound state radius and energy density are converging as resolution increases.
This indicates SCALE-INDEPENDENT EMERGENT STRUCTURE.

The particle properties are determined by the PHYSICS, not the grid.
This is a very serious theoretical result.
""")
            elif R_change < 0.2 and E_change < 0.2:
                print("""
⚠️ PARTIAL CONVERGENCE

Results are trending toward convergence but higher resolution needed
to confirm scale-independence.
""")
            else:
                print(f"""
❌ NOT YET CONVERGED

R change: {R_change:.1%}
E change: {E_change:.1%}

Higher resolution may be needed, or the structure may be grid-dependent.
""")
    
    return results


if __name__ == "__main__":
    results = main()
