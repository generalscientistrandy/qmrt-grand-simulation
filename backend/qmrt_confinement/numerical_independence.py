"""
QMRT v3: Numerical Independence Verification
=============================================

CRITICAL QUESTION: Is ω ≈ 31.5 a genuine emergent eigenmode
or a numerical artifact from hidden scaling?

Tests:
1. SPATIAL SCALE: Does ω change if we scale dx?
2. TIMESTEP: Does ω change if we scale dt?
3. GRID RESOLUTION: Does ω change if we change N?
4. DOMAIN SIZE: Does ω change if we change L?

If ω is INVARIANT to all these → genuine physics
If ω SCALES with any → numerical artifact

The key insight:
- Physical frequency should scale as: ω_physical = ω_code * (1/t_unit)
- If t_unit is implicitly set by the discretization, ω will appear universal
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


def measure_breathing_frequency(engine, amplitude=1.0, evolution_steps=1500, dt=0.01, sample_skip=300):
    """
    Measure breathing frequency of an oscillon.
    
    Returns: (omega, tau_max_mean, valid)
    """
    n = engine.grid_size
    center = n // 2
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
    
    # Initialize
    engine.tau[2] = amplitude * np.exp(-R_sq / 8)
    engine.initial_energy = engine.compute_total_energy()['E_total']
    
    # Evolve and record
    amp_history = []
    for step in range(evolution_steps):
        engine.evolve_timestep(dt)
        if step > sample_skip and step % 5 == 0:
            amp_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
    
    tau_max = np.mean(amp_history[-20:]) if amp_history else 0
    
    # FFT for frequency
    from scipy.fft import fft, fftfreq
    arr = np.array(amp_history)
    
    if len(arr) < 20 or np.std(arr) < 1e-6:
        return 0, tau_max, False
    
    centered = arr - np.mean(arr)
    spectrum = np.abs(fft(centered))
    freqs = fftfreq(len(centered), d=5*dt)  # Sample every 5 steps
    
    pos_mask = freqs > 0.01
    if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
        omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
        return omega, tau_max, True
    
    return 0, tau_max, False


def test_timestep_independence():
    """
    Test 1: Does ω change with timestep dt?
    
    If ω is physical: ω should be INVARIANT to dt
    If ω is numerical: ω might scale as 1/dt or similar
    """
    print("=" * 70)
    print("TEST 1: TIMESTEP INDEPENDENCE")
    print("=" * 70)
    print("""
If ω is a genuine eigenmode: ω(dt) = constant
If ω is numerical artifact: ω(dt) ~ 1/dt or similar
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Different timesteps
    dt_values = [0.005, 0.01, 0.02, 0.04]
    
    print(f"\n{'dt':>10} | {'ω':>12} | {'τ_max':>12} | {'ω*dt':>12}")
    print("-" * 55)
    
    frequencies = []
    
    for dt in dt_values:
        engine = QMRTv3Engine(grid_size=28, params=params)
        
        # Adjust evolution steps to keep total time constant
        total_time = 15.0
        steps = int(total_time / dt)
        skip = int(3.0 / dt)  # Skip first 3 time units
        
        omega, tau_max, valid = measure_breathing_frequency(
            engine, amplitude=1.5, evolution_steps=steps, dt=dt, sample_skip=skip
        )
        
        if valid:
            frequencies.append((dt, omega))
        
        omega_dt = omega * dt if omega > 0 else 0
        print(f"{dt:>10.4f} | {omega:>12.2f} | {tau_max:>12.4f} | {omega_dt:>12.4f}")
    
    # Analyze scaling
    if len(frequencies) >= 3:
        omegas = [f[1] for f in frequencies]
        dts = [f[0] for f in frequencies]
        
        # Check if ω is constant
        omega_mean = np.mean(omegas)
        omega_std = np.std(omegas)
        cv = omega_std / omega_mean if omega_mean > 0 else float('inf')
        
        # Check if ω*dt is constant (would indicate ω ~ 1/dt)
        omega_dt = [o * d for o, d in frequencies]
        omega_dt_cv = np.std(omega_dt) / np.mean(omega_dt) if np.mean(omega_dt) > 0 else float('inf')
        
        print(f"\nω statistics: mean={omega_mean:.2f}, std={omega_std:.2f}, CV={cv:.1%}")
        print(f"ω*dt statistics: CV={omega_dt_cv:.1%}")
        
        if cv < 0.05:
            print("\n✅ ω is TIMESTEP-INDEPENDENT (genuine physics)")
        elif omega_dt_cv < 0.05:
            print("\n❌ ω ~ 1/dt (NUMERICAL ARTIFACT!)")
        else:
            print("\n⚠️ Unclear scaling - need more data")
    
    return frequencies


def test_grid_resolution_independence():
    """
    Test 2: Does ω change with grid resolution N?
    
    If ω is physical: ω should CONVERGE as N increases
    If ω is numerical: ω might scale with N
    """
    print("\n" + "=" * 70)
    print("TEST 2: GRID RESOLUTION INDEPENDENCE")
    print("=" * 70)
    print("""
If ω is a genuine eigenmode: ω(N) → constant as N → ∞
If ω is numerical artifact: ω(N) ~ N or 1/N
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Different grid sizes
    N_values = [16, 20, 24, 28, 32]
    
    print(f"\n{'N':>8} | {'ω':>12} | {'τ_max':>12} | {'ω/N':>12}")
    print("-" * 55)
    
    frequencies = []
    
    for N in N_values:
        engine = QMRTv3Engine(grid_size=N, params=params)
        
        omega, tau_max, valid = measure_breathing_frequency(
            engine, amplitude=1.5, evolution_steps=1500, dt=0.01, sample_skip=300
        )
        
        if valid:
            frequencies.append((N, omega))
        
        omega_N = omega / N if omega > 0 else 0
        print(f"{N:>8} | {omega:>12.2f} | {tau_max:>12.4f} | {omega_N:>12.4f}")
    
    # Analyze scaling
    if len(frequencies) >= 3:
        omegas = [f[1] for f in frequencies]
        Ns = [f[0] for f in frequencies]
        
        # Check if ω is constant
        omega_mean = np.mean(omegas)
        omega_std = np.std(omegas)
        cv = omega_std / omega_mean if omega_mean > 0 else float('inf')
        
        # Check convergence (should ω approach a limit?)
        if len(omegas) >= 3:
            # Richardson extrapolation for convergence
            delta_omega = [omegas[i+1] - omegas[i] for i in range(len(omegas)-1)]
            convergence_rate = np.mean([abs(d) for d in delta_omega])
        
        print(f"\nω statistics: mean={omega_mean:.2f}, std={omega_std:.2f}, CV={cv:.1%}")
        
        if cv < 0.05:
            print("\n✅ ω is RESOLUTION-INDEPENDENT (genuine physics)")
        else:
            # Check if converging
            if len(omegas) >= 3 and abs(omegas[-1] - omegas[-2]) < abs(omegas[-2] - omegas[-3]):
                print("\n⚠️ ω is CONVERGING (may be physical, needs higher N)")
            else:
                print("\n❌ ω varies with N (possible numerical artifact)")
    
    return frequencies


def test_spatial_scale_independence():
    """
    Test 3: Does ω change if we rescale the spatial domain?
    
    This tests whether the equation has implicit length scale.
    
    If ω is physical: ω should scale as 1/L (like a cavity mode)
    If ω is numerical artifact: ω might be constant or scale differently
    """
    print("\n" + "=" * 70)
    print("TEST 3: SPATIAL SCALE INDEPENDENCE")
    print("=" * 70)
    print("""
For a physical breathing mode in a box of size L:
  ω ~ 1/L (larger box → lower frequency)
  
Or if ω is intrinsic to the structure (not the box):
  ω = constant (independent of L)

Testing by changing the initial Gaussian width while keeping grid fixed.
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Different Gaussian widths (proxy for spatial scale)
    width_values = [1.5, 2.0, 2.5, 3.0, 3.5]
    
    print(f"\n{'Width':>8} | {'ω':>12} | {'τ_max':>12} | {'ω*Width':>12}")
    print("-" * 55)
    
    frequencies = []
    
    for width in width_values:
        engine = QMRTv3Engine(grid_size=28, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        # Initialize with given width
        engine.tau[2] = np.exp(-R_sq / (2 * width**2))
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Evolve
        amp_history = []
        for step in range(1500):
            engine.evolve_timestep(0.01)
            if step > 300 and step % 5 == 0:
                amp_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
        
        tau_max = np.mean(amp_history[-20:]) if amp_history else 0
        
        # FFT
        from scipy.fft import fft, fftfreq
        arr = np.array(amp_history)
        
        omega = 0
        if len(arr) > 20 and np.std(arr) > 1e-6:
            centered = arr - np.mean(arr)
            spectrum = np.abs(fft(centered))
            freqs = fftfreq(len(centered), d=0.05)
            pos_mask = freqs > 0.01
            if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
                omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
        
        if omega > 0:
            frequencies.append((width, omega))
        
        omega_width = omega * width if omega > 0 else 0
        print(f"{width:>8.2f} | {omega:>12.2f} | {tau_max:>12.4f} | {omega_width:>12.2f}")
    
    # Analyze scaling
    if len(frequencies) >= 3:
        omegas = [f[1] for f in frequencies]
        widths = [f[0] for f in frequencies]
        
        # Check if ω is constant
        omega_mean = np.mean(omegas)
        omega_std = np.std(omegas)
        cv = omega_std / omega_mean if omega_mean > 0 else float('inf')
        
        # Check if ω*width is constant (would indicate ω ~ 1/width)
        omega_width = [o * w for o, w in frequencies]
        omega_width_cv = np.std(omega_width) / np.mean(omega_width) if np.mean(omega_width) > 0 else float('inf')
        
        print(f"\nω statistics: mean={omega_mean:.2f}, std={omega_std:.2f}, CV={cv:.1%}")
        print(f"ω*Width statistics: CV={omega_width_cv:.1%}")
        
        if cv < 0.05:
            print("\n✅ ω is WIDTH-INDEPENDENT (intrinsic to medium, not structure size)")
            print("   This suggests ω is a MEDIUM PROPERTY, like a plasma frequency!")
        elif omega_width_cv < 0.05:
            print("\n⚠️ ω ~ 1/Width (cavity-like mode, depends on structure size)")
        else:
            print("\n⚠️ Complex scaling - neither pure constant nor 1/Width")
    
    return frequencies


def test_domain_size_independence():
    """
    Test 4: Does ω change with total domain size L?
    
    If the oscillon doesn't "feel" the boundary, ω should be constant.
    """
    print("\n" + "=" * 70)
    print("TEST 4: DOMAIN SIZE INDEPENDENCE")
    print("=" * 70)
    print("""
Testing if ω changes when we increase the simulation domain
while keeping the oscillon size fixed.

If ω is intrinsic to oscillon: ω = constant
If ω depends on boundaries: ω will change with domain size
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Different domain sizes (keeping initialization width fixed)
    domain_sizes = [20, 24, 28, 32, 36]
    
    print(f"\n{'Domain N':>10} | {'ω':>12} | {'τ_max':>12}")
    print("-" * 45)
    
    frequencies = []
    
    for N in domain_sizes:
        engine = QMRTv3Engine(grid_size=N, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        # Fixed initialization width (in grid units)
        init_width = 2.0
        engine.tau[2] = np.exp(-R_sq / (2 * init_width**2))
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Evolve
        amp_history = []
        for step in range(1500):
            engine.evolve_timestep(0.01)
            if step > 300 and step % 5 == 0:
                amp_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
        
        tau_max = np.mean(amp_history[-20:]) if amp_history else 0
        
        # FFT
        from scipy.fft import fft, fftfreq
        arr = np.array(amp_history)
        
        omega = 0
        if len(arr) > 20 and np.std(arr) > 1e-6:
            centered = arr - np.mean(arr)
            spectrum = np.abs(fft(centered))
            freqs = fftfreq(len(centered), d=0.05)
            pos_mask = freqs > 0.01
            if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
                omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
        
        if omega > 0:
            frequencies.append((N, omega))
        
        print(f"{N:>10} | {omega:>12.2f} | {tau_max:>12.4f}")
    
    # Analyze
    if len(frequencies) >= 3:
        omegas = [f[1] for f in frequencies]
        omega_mean = np.mean(omegas)
        omega_std = np.std(omegas)
        cv = omega_std / omega_mean if omega_mean > 0 else float('inf')
        
        print(f"\nω statistics: mean={omega_mean:.2f}, std={omega_std:.2f}, CV={cv:.1%}")
        
        if cv < 0.05:
            print("\n✅ ω is DOMAIN-INDEPENDENT (oscillon doesn't feel boundaries)")
        else:
            print("\n⚠️ ω varies with domain size (boundary effects present)")
    
    return frequencies


def check_equation_scaling():
    """
    Analyze the QMRT v3 equations for implicit scaling.
    """
    print("\n" + "=" * 70)
    print("EQUATION SCALING ANALYSIS")
    print("=" * 70)
    
    print("""
QMRT v3 Lagrangian for τ field:

  L_τ = ½|∂τ/∂t|² - ½|∇τ|² - ½m_τ²|τ|² - (g_rt/4)|τ|⁴·ρ

The equation of motion is:
  ∂²τ/∂t² = ∇²τ - m_τ²τ - g_rt|τ|²τ·ρ

DIMENSIONAL ANALYSIS:

Let: τ → τ, x → L·x', t → T·t'

Then: ∂²τ/∂t'² · (1/T²) = ∇²τ · (1/L²) - m_τ²τ - g_rt|τ|²τ·ρ

For the equation to be scale-invariant, we need:
  1/T² = 1/L² = m_τ² → T = 1/m_τ, L = 1/m_τ

So there IS an intrinsic scale set by m_τ!

The natural frequency should be:
  ω_natural ~ m_τ (in code units)

With m_τ = 16: ω ~ 16

But we measure ω ≈ 31.5. Why the factor of ~2?

Possibilities:
1. Nonlinear correction factor (likely)
2. Mode mixing with other branches
3. Numerical factor from oscillating boundary

The KEY POINT: ω should scale with m_τ, not with dt, dx, or N.
""")


def summarize_numerical_independence():
    """Summary of all numerical independence tests."""
    print("\n" + "=" * 70)
    print("NUMERICAL INDEPENDENCE: FINAL VERDICT")
    print("=" * 70)
    
    print("""
VERDICTS:

| Test | Expected for Physics | Expected for Artifact |
|------|---------------------|----------------------|
| Timestep dt | ω = const | ω ~ 1/dt |
| Resolution N | ω → limit | ω ~ N or 1/N |
| Width | ω = const or ~1/W | varies erratically |
| Domain size | ω = const | ω varies |

If ω passes ALL tests → GENUINE EMERGENT EIGENMODE
If ω fails ANY test → NUMERICAL ARTIFACT (investigate!)

THEORETICAL PREDICTION:

From dimensional analysis: ω_natural ~ m_τ = 16

Measured: ω ≈ 31.5 ≈ 2 * m_τ

This factor of ~2 could come from:
- Nonlinear potential energy contribution
- Coupling between τ and ρ fields
- Breathing mode being a standing wave (factor of 2 for round trip)

The critical question answered by these tests:
"Is 31.5 a property of the PHYSICS or the NUMERICS?"
""")


def main():
    """Run complete numerical independence verification."""
    print("#" * 70)
    print("# QMRT v3: NUMERICAL INDEPENDENCE VERIFICATION")
    print("#" * 70)
    print("""
CRITICAL SCIENTIFIC TEST:

Is ω ≈ 31.5 a genuine emergent eigenmode
or a numerical artifact from hidden scaling?
""")
    
    # Run all tests
    dt_results = test_timestep_independence()
    N_results = test_grid_resolution_independence()
    width_results = test_spatial_scale_independence()
    domain_results = test_domain_size_independence()
    
    check_equation_scaling()
    summarize_numerical_independence()
    
    # Final summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    
    print(f"\n{'Test':>20} | {'Result':>40}")
    print("-" * 65)
    
    if dt_results:
        cv_dt = np.std([f[1] for f in dt_results]) / np.mean([f[1] for f in dt_results])
        status_dt = "✅ PASS (CV={:.1%})".format(cv_dt) if cv_dt < 0.1 else "❌ FAIL"
        print(f"{'Timestep':>20} | {status_dt:>40}")
    
    if N_results:
        cv_N = np.std([f[1] for f in N_results]) / np.mean([f[1] for f in N_results])
        status_N = "✅ PASS (CV={:.1%})".format(cv_N) if cv_N < 0.1 else "❌ FAIL"
        print(f"{'Resolution':>20} | {status_N:>40}")
    
    if width_results:
        cv_W = np.std([f[1] for f in width_results]) / np.mean([f[1] for f in width_results])
        status_W = "✅ PASS (CV={:.1%})".format(cv_W) if cv_W < 0.1 else "❌ FAIL"
        print(f"{'Spatial Width':>20} | {status_W:>40}")
    
    if domain_results:
        cv_D = np.std([f[1] for f in domain_results]) / np.mean([f[1] for f in domain_results])
        status_D = "✅ PASS (CV={:.1%})".format(cv_D) if cv_D < 0.1 else "❌ FAIL"
        print(f"{'Domain Size':>20} | {status_D:>40}")


if __name__ == "__main__":
    main()
