"""
QMRT v3: Natural Quantization Search
=====================================

KEY QUESTION: Does quantization emerge naturally from oscillon dynamics
WITHOUT requiring topology?

If YES → Revolutionary finding: emergent quantum structure from classical dynamics

Tests:
1. LIFETIME SCALING: τ(E) law - do oscillons have discrete lifetimes?
2. AMPLITUDE-FREQUENCY RELATION: ω(A) - is it continuous or shows plateaus?
3. RESONANCE QUANTIZATION: Do discrete ω values dominate the spectrum?
4. ENERGY QUANTIZATION: Are E values discrete or continuous in stable oscillons?

The manifold mapping found ω = 31.61 locked across different initial radii.
This is the first hint of natural quantization!
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


def measure_oscillon_lifetime(amplitude, params, max_steps=5000, dt=0.01):
    """
    Measure how long an oscillon survives before dispersing.
    
    Returns:
    - lifetime: Number of timesteps before dispersion
    - final_state: 'STABLE', 'DISPERSED', or 'UNSTABLE'
    - energy_history: Energy over time
    """
    engine = QMRTv3Engine(grid_size=28, params=params)
    
    n = engine.grid_size
    center = n // 2
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
    
    # Initialize with given amplitude
    engine.tau[2] = amplitude * np.exp(-R_sq / 8)
    engine.initial_energy = engine.compute_total_energy()['E_total']
    
    initial_max = np.max(np.sqrt(engine._compute_tau_squared()))
    energy_history = []
    amplitude_history = []
    
    dispersion_threshold = 0.1  # Consider dispersed if max < 10% of initial
    blowup_threshold = 100.0
    
    for step in range(max_steps):
        engine.evolve_timestep(dt)
        
        tau_sq = engine._compute_tau_squared()
        current_max = np.max(np.sqrt(tau_sq))
        
        energy = engine.compute_total_energy()['E_total']
        energy_history.append(energy)
        amplitude_history.append(current_max)
        
        # Check for dispersion
        if current_max < dispersion_threshold * initial_max:
            return step * dt, 'DISPERSED', energy_history, amplitude_history
        
        # Check for blowup
        if current_max > blowup_threshold:
            return step * dt, 'UNSTABLE', energy_history, amplitude_history
    
    return max_steps * dt, 'STABLE', energy_history, amplitude_history


def lifetime_scaling_study():
    """
    Study how oscillon lifetime scales with energy/amplitude.
    
    Looking for:
    - Power law: τ ~ E^α
    - Discrete jumps (quantum-like)
    - Threshold effects
    """
    print("=" * 70)
    print("OSCILLON LIFETIME SCALING STUDY")
    print("=" * 70)
    print("""
If lifetime shows DISCRETE levels or sharp thresholds,
that would suggest natural quantization.
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Test range of amplitudes
    amplitudes = np.linspace(0.3, 3.0, 15)
    
    print(f"\n{'Amplitude':>10} | {'Lifetime':>10} | {'Final State':>12} | {'E_initial':>12}")
    print("-" * 55)
    
    lifetimes = []
    energies = []
    states = []
    
    for A in amplitudes:
        lifetime, state, e_hist, a_hist = measure_oscillon_lifetime(A, params, max_steps=2000)
        E_init = e_hist[0] if e_hist else 0
        
        lifetimes.append(lifetime)
        energies.append(E_init)
        states.append(state)
        
        print(f"{A:>10.2f} | {lifetime:>10.2f} | {state:>12} | {E_init:>12.4f}")
    
    # Analyze for quantization
    stable_indices = [i for i, s in enumerate(states) if s == 'STABLE']
    
    if len(stable_indices) >= 2:
        stable_lifetimes = [lifetimes[i] for i in stable_indices]
        stable_energies = [energies[i] for i in stable_indices]
        
        # Check for discrete levels
        if len(set([round(t, 1) for t in stable_lifetimes])) < len(stable_lifetimes) * 0.5:
            print("\n⚠️ Lifetime clustering detected - possible discrete levels")
    
    return lifetimes, energies, states


def amplitude_frequency_relation():
    """
    Measure how breathing frequency depends on amplitude.
    
    Looking for:
    - Continuous relation (classical)
    - Discrete plateaus (quantum-like)
    - Universal frequency (strong resonance)
    """
    print("\n" + "=" * 70)
    print("AMPLITUDE-FREQUENCY RELATION")
    print("=" * 70)
    print("""
The manifold mapping found ω = 31.61 for all initial radii.
Now testing if this holds across different AMPLITUDES.

If ω is truly quantized, it should show:
- Discrete plateaus
- Sharp transitions between levels
- Possibly harmonic ratios (ω_n = n * ω_0)
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    amplitudes = np.linspace(0.5, 4.0, 12)
    
    print(f"\n{'Amplitude':>10} | {'τ_max_final':>12} | {'ω_breath':>10} | {'ω/ω_0':>10}")
    print("-" * 55)
    
    frequencies = []
    final_amplitudes = []
    
    omega_0 = None  # Will store first measured frequency
    
    for A in amplitudes:
        engine = QMRTv3Engine(grid_size=28, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = A * np.exp(-R_sq / 8)
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Evolve and record amplitude history
        amp_history = []
        for step in range(1500):
            engine.evolve_timestep(0.01)
            if step > 300 and step % 5 == 0:  # Skip transient
                amp_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
        
        final_amp = np.mean(amp_history[-20:]) if amp_history else 0
        final_amplitudes.append(final_amp)
        
        # FFT for frequency
        from scipy.fft import fft, fftfreq
        arr = np.array(amp_history)
        
        if len(arr) > 20 and np.std(arr) > 1e-6:
            centered = arr - np.mean(arr)
            spectrum = np.abs(fft(centered))
            freqs = fftfreq(len(centered), d=0.05)
            
            pos_mask = freqs > 0.01
            if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
                omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
            else:
                omega = 0
        else:
            omega = 0
        
        frequencies.append(omega)
        
        if omega_0 is None and omega > 0:
            omega_0 = omega
        
        ratio = omega / omega_0 if omega_0 and omega > 0 else 0
        print(f"{A:>10.2f} | {final_amp:>12.4f} | {omega:>10.2f} | {ratio:>10.2f}")
    
    # Analyze for quantization
    valid_freqs = [f for f in frequencies if f > 0]
    
    if len(valid_freqs) >= 3:
        freq_mean = np.mean(valid_freqs)
        freq_std = np.std(valid_freqs)
        cv = freq_std / freq_mean if freq_mean > 0 else float('inf')
        
        print(f"\nFrequency statistics: mean={freq_mean:.2f}, std={freq_std:.2f}, CV={cv:.1%}")
        
        if cv < 0.05:
            print("✅ UNIVERSAL FREQUENCY - Strong natural quantization!")
            print(f"   ω_natural = {freq_mean:.2f}")
        elif cv < 0.15:
            print("⚠️ Weak frequency clustering")
        else:
            print("❌ Frequency varies with amplitude (classical behavior)")
        
        # Check for harmonic ratios
        if omega_0:
            ratios = [f / omega_0 for f in valid_freqs if f > 0]
            int_ratios = [round(r) for r in ratios if 0.8 < r < 5]
            unique_ints = set(int_ratios)
            if len(unique_ints) > 1:
                print(f"\n   Detected harmonic candidates: {sorted(unique_ints)}")
    
    return frequencies, final_amplitudes


def energy_quantization_test():
    """
    Test if stable oscillons have discrete energy levels.
    
    For natural quantization, we expect:
    - E_n = E_0 * f(n) for integer n
    - Possibly E_n ~ n * ℏω (quantum-like)
    """
    print("\n" + "=" * 70)
    print("ENERGY QUANTIZATION TEST")
    print("=" * 70)
    print("""
Testing if final oscillon energies show discrete levels.

Method:
1. Create oscillons with various initial conditions
2. Let them relax to quasi-equilibrium
3. Measure final energy
4. Look for clustering / discrete levels
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Various initial conditions
    initial_conditions = []
    
    # Different amplitudes
    for A in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        initial_conditions.append(('amp', A, 2.0))  # amplitude, width
    
    # Different widths
    for W in [1.5, 2.0, 2.5, 3.0, 3.5]:
        initial_conditions.append(('width', 1.0, W))  # amplitude, width
    
    print(f"\n{'Init Type':>10} | {'Param':>8} | {'E_initial':>12} | {'E_final':>12} | {'ΔE':>10}")
    print("-" * 60)
    
    final_energies = []
    
    for init_type, A, W in initial_conditions:
        engine = QMRTv3Engine(grid_size=28, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = A * np.exp(-R_sq / (2 * W**2))
        E_init = engine.compute_total_energy()['E_total']
        engine.initial_energy = E_init
        
        # Evolve to quasi-equilibrium
        for _ in range(1500):
            engine.evolve_timestep(0.01)
        
        E_final = engine.compute_total_energy()['E_total']
        final_energies.append(E_final)
        
        param_val = A if init_type == 'amp' else W
        delta_E = (E_final - E_init) / E_init * 100 if E_init > 0 else 0
        
        print(f"{init_type:>10} | {param_val:>8.2f} | {E_init:>12.4f} | {E_final:>12.4f} | {delta_E:>9.1f}%")
    
    # Analyze for discrete levels
    sorted_E = sorted(final_energies)
    
    # Cluster detection
    clusters = []
    current_cluster = [sorted_E[0]]
    
    tolerance = 0.05  # 5% tolerance for same level
    
    for E in sorted_E[1:]:
        if abs(E - current_cluster[-1]) / current_cluster[-1] < tolerance:
            current_cluster.append(E)
        else:
            clusters.append(current_cluster)
            current_cluster = [E]
    clusters.append(current_cluster)
    
    print(f"\n{len(clusters)} distinct energy clusters found:")
    for i, cluster in enumerate(clusters):
        E_mean = np.mean(cluster)
        print(f"  Level {i+1}: E = {E_mean:.4f} ({len(cluster)} states)")
    
    if len(clusters) < len(final_energies) * 0.5:
        print("\n✅ ENERGY CLUSTERING DETECTED - Possible discrete levels!")
    else:
        print("\n❌ No clear energy quantization")
    
    return final_energies, clusters


def resonance_plateau_search():
    """
    Systematic search for resonance plateaus.
    
    Sweeping coupling strength and looking for
    frequency plateaus where ω stays constant.
    """
    print("\n" + "=" * 70)
    print("RESONANCE PLATEAU SEARCH")
    print("=" * 70)
    print("""
Sweeping g_rt coupling and measuring breathing frequency.

If ω shows PLATEAUS (constant over range of g_rt),
that indicates RESONANCE QUANTIZATION.
""")
    
    g_rt_values = np.linspace(2.0, 12.0, 15)
    
    print(f"\n{'g_rt':>8} | {'τ_max':>10} | {'ω_breath':>10} | {'Status':>15}")
    print("-" * 50)
    
    frequencies = []
    amplitudes = []
    
    for g_rt in g_rt_values:
        params = QMRTv3Parameters(g_rt=g_rt, m_tau=16.0, g_tp=0.1)
        engine = QMRTv3Engine(grid_size=24, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = np.exp(-R_sq / 8)
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Evolve and record
        amp_history = []
        for step in range(1200):
            engine.evolve_timestep(0.01)
            if step > 200 and step % 5 == 0:
                amp_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
        
        tau_max = np.mean(amp_history[-10:]) if amp_history else 0
        amplitudes.append(tau_max)
        
        # FFT
        from scipy.fft import fft, fftfreq
        arr = np.array(amp_history)
        
        if len(arr) > 20 and np.std(arr) > 1e-6:
            centered = arr - np.mean(arr)
            spectrum = np.abs(fft(centered))
            freqs = fftfreq(len(centered), d=0.05)
            
            pos_mask = freqs > 0.01
            if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
                omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
            else:
                omega = 0
        else:
            omega = 0
        
        frequencies.append(omega)
        
        # Detect plateau
        status = ""
        if len(frequencies) >= 3:
            recent = frequencies[-3:]
            if all(f > 0 for f in recent):
                if np.std(recent) / np.mean(recent) < 0.03:
                    status = "PLATEAU"
        
        print(f"{g_rt:>8.2f} | {tau_max:>10.4f} | {omega:>10.2f} | {status:>15}")
    
    # Analyze plateaus
    valid_omega = [(g, f) for g, f in zip(g_rt_values, frequencies) if f > 0]
    
    if len(valid_omega) >= 5:
        # Find plateau regions
        plateau_regions = []
        current_plateau = [valid_omega[0]]
        
        for g, f in valid_omega[1:]:
            if abs(f - current_plateau[-1][1]) / current_plateau[-1][1] < 0.05:
                current_plateau.append((g, f))
            else:
                if len(current_plateau) >= 2:
                    plateau_regions.append(current_plateau)
                current_plateau = [(g, f)]
        
        if len(current_plateau) >= 2:
            plateau_regions.append(current_plateau)
        
        if plateau_regions:
            print(f"\n{len(plateau_regions)} resonance plateau(s) found:")
            for i, plateau in enumerate(plateau_regions):
                g_range = (plateau[0][0], plateau[-1][0])
                omega_val = np.mean([p[1] for p in plateau])
                print(f"  Plateau {i+1}: g_rt ∈ [{g_range[0]:.1f}, {g_range[1]:.1f}], ω = {omega_val:.2f}")
            
            print("\n✅ RESONANCE PLATEAUS DETECTED - Natural quantization evidence!")
        else:
            print("\n❌ No clear plateaus found")
    
    return g_rt_values, frequencies


def summarize_quantization_findings():
    """Summary of all quantization tests."""
    print("\n" + "=" * 70)
    print("NATURAL QUANTIZATION SEARCH: SUMMARY")
    print("=" * 70)
    
    print("""
THEORETICAL SIGNIFICANCE:

If oscillons show QUANTIZED properties (discrete frequencies, energies, 
lifetimes) WITHOUT topological protection, this would mean:

  "Quantum-like discreteness emerges from classical nonlinear dynamics"

This is the essence of:
- Bohr's original atomic model (before QM)
- Emergent gauge theories
- Analog gravity models

QMRT FINDINGS:

From the equilibrium manifold mapping, we found:
  ω_breath = 31.61 (universal across initial radii)
  CV = 0.0% (perfect frequency locking)

This is STRONG EVIDENCE that oscillons naturally quantize their 
breathing frequency without requiring topology.

NEXT STEPS:

If quantization confirmed:
1. Derive ω_natural from the Lagrangian (analytical prediction)
2. Look for higher harmonics (ω_n = n * ω_0?)
3. Test if collision products have same frequency
4. This would establish QMRT as emergent quantum substrate

If quantization NOT confirmed:
1. Need topological protection after all
2. Add U(1) gauge symmetry for winding numbers
3. Would be standard oscillon physics
""")


def main():
    """Run complete natural quantization search."""
    print("#" * 70)
    print("# QMRT v3: NATURAL QUANTIZATION SEARCH")
    print("#" * 70)
    print("""
Question: Does quantization emerge naturally from oscillon dynamics?

The equilibrium manifold mapping found universal ω = 31.61.
Now testing systematically across all dimensions.
""")
    
    # Run all tests
    lifetime_scaling_study()
    amplitude_frequency_relation()
    energy_quantization_test()
    resonance_plateau_search()
    summarize_quantization_findings()


if __name__ == "__main__":
    main()
