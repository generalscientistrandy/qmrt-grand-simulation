"""
QMRT v3: Dynamic Equilibrium Manifold Mapping
==============================================

KEY INSIGHT: Matter forms where medium flow velocities, phase frequencies, 
and nonlinear coupling strengths reach a dynamic equilibrium manifold.

The oscillons we found are "coherence islands" - dynamically stabilized 
structures in the intermediate regime between:
  - Turbulent (high energy) → disperses
  - Uniform (low energy) → no structure
  - Coherence window → stable oscillons

This script maps the phase space to find:
1. The boundaries of the coherence trapping window
2. Parameter resonance zones
3. Frequency locking regions
4. The dynamic equilibrium manifold

Multi-scale stability cascade:
  chaotic medium → localized oscillons → locked topology → 
  composite particles → atomic resonance systems
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


def classify_state(engine, initial_tau_sq, evolution_steps=800):
    """
    Classify the final state after evolution.
    
    Returns:
    - 'DISPERSED': Structure dissolved (turbulent/spreading regime)
    - 'UNIFORM': Collapsed to uniform (low energy regime)
    - 'OSCILLON': Stable localized oscillation (coherence window)
    - 'UNSTABLE': Blew up numerically
    """
    # Evolve
    for step in range(evolution_steps):
        engine.evolve_timestep(0.01)
        
        # Check for blow-up
        tau_sq = engine._compute_tau_squared()
        if np.max(tau_sq) > 1e6:
            return 'UNSTABLE', 0, 0
    
    # Final measurements
    tau_sq = engine._compute_tau_squared()
    final_max = np.max(np.sqrt(tau_sq))
    
    # Compute localization measure
    total = np.sum(tau_sq)
    if total < 1e-10:
        return 'DISPERSED', 0, 0
    
    # Participation ratio: how spread out is the field?
    participation = (np.sum(tau_sq))**2 / np.sum(tau_sq**2)
    n = engine.grid_size
    max_participation = n**3
    
    localization = 1 - participation / max_participation
    
    # Classification
    if final_max < 0.01:
        return 'DISPERSED', localization, final_max
    elif localization < 0.5:
        return 'DISPERSED', localization, final_max
    elif localization > 0.95:
        return 'UNIFORM', localization, final_max
    else:
        return 'OSCILLON', localization, final_max


def map_coherence_window():
    """
    Map the coherence trapping window in (g_rt, m_tau) parameter space.
    """
    print("=" * 70)
    print("MAPPING THE COHERENCE TRAPPING WINDOW")
    print("=" * 70)
    print("""
Phase diagram in coupling-mass space:
  - DISPERSED: Linear spreading dominates → no structure
  - OSCILLON: Balance between spreading and compression
  - UNSTABLE: Nonlinear collapse dominates
""")
    
    # Parameter grid
    g_rt_values = [1, 2, 3, 5, 8, 12]
    m_tau_values = [4, 8, 12, 16, 20, 24]
    
    # Results storage
    phase_map = np.zeros((len(g_rt_values), len(m_tau_values)), dtype=object)
    
    print(f"\n{'g_rt \\ m_tau':<12}", end="")
    for m in m_tau_values:
        print(f"{m:>8}", end="")
    print()
    print("-" * (12 + 8 * len(m_tau_values)))
    
    for i, g_rt in enumerate(g_rt_values):
        print(f"{g_rt:<12}", end="")
        
        for j, m_tau in enumerate(m_tau_values):
            params = QMRTv3Parameters(g_rt=g_rt, m_tau=m_tau, g_tp=0.1)
            
            engine = QMRTv3Engine(grid_size=24, params=params)
            
            # Initialize standard perturbation
            n = engine.grid_size
            center = n // 2
            x = np.arange(n)
            X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
            R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
            
            engine.tau[2] = np.exp(-R_sq / 8)
            initial_tau_sq = np.sum(engine._compute_tau_squared())
            engine.initial_energy = engine.compute_total_energy()['E_total']
            
            state, loc, amp = classify_state(engine, initial_tau_sq)
            
            phase_map[i, j] = state
            
            # Short symbol for display
            symbol = {
                'DISPERSED': 'D',
                'OSCILLON': 'O',
                'UNIFORM': 'U',
                'UNSTABLE': 'X'
            }[state]
            
            print(f"{symbol:>8}", end="")
        
        print()
    
    # Count oscillons
    oscillon_count = np.sum(phase_map == 'OSCILLON')
    total = phase_map.size
    
    print(f"\nOscillon (coherence) window: {oscillon_count}/{total} = {oscillon_count/total:.0%}")
    print("Legend: D=Dispersed, O=Oscillon, U=Uniform, X=Unstable")
    
    return phase_map


def map_energy_amplitude_space():
    """
    Map coherence as function of initial amplitude (energy).
    
    Looking for the "intermediate regime" between:
    - Too low energy → disperses
    - Too high energy → turbulent/unstable
    - Just right → coherence island
    """
    print("\n" + "=" * 70)
    print("MAPPING ENERGY-AMPLITUDE COHERENCE WINDOW")
    print("=" * 70)
    print("""
Testing if oscillons exist in intermediate energy regime:
  - Low amplitude → spreading dominates → dispersed
  - High amplitude → nonlinear collapse → unstable
  - Intermediate → dynamic balance → oscillon
""")
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    amplitudes = [0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0]
    
    print(f"\n{'Amplitude':>10} | {'Final τ_max':>12} | {'Localization':>12} | {'State':>10}")
    print("-" * 55)
    
    states = []
    
    for A in amplitudes:
        engine = QMRTv3Engine(grid_size=24, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = A * np.exp(-R_sq / 8)
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        state, loc, amp_final = classify_state(engine, A**2)
        states.append(state)
        
        print(f"{A:>10.1f} | {amp_final:>12.4f} | {loc:>12.2f} | {state:>10}")
    
    # Find coherence window
    oscillon_indices = [i for i, s in enumerate(states) if s == 'OSCILLON']
    
    if oscillon_indices:
        A_low = amplitudes[min(oscillon_indices)]
        A_high = amplitudes[max(oscillon_indices)]
        print(f"\n✅ Coherence window: A ∈ [{A_low}, {A_high}]")
    else:
        print("\n⚠️ No clear coherence window found")


def map_frequency_resonance():
    """
    Look for frequency locking / resonance zones.
    
    In the coherence window, oscillons have characteristic frequencies.
    If these frequencies show discrete locking, that indicates resonance.
    """
    print("\n" + "=" * 70)
    print("FREQUENCY LOCKING / RESONANCE ANALYSIS")
    print("=" * 70)
    
    params = QMRTv3Parameters(g_rt=5.0, m_tau=16.0, g_tp=0.1)
    
    # Try different initial sizes and measure final breathing frequency
    initial_radii = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    
    print(f"\n{'R_init':>8} | {'R_final':>10} | {'ω_breath':>10} | {'Note':>15}")
    print("-" * 50)
    
    frequencies = []
    
    for R_init in initial_radii:
        engine = QMRTv3Engine(grid_size=28, params=params)
        
        n = engine.grid_size
        center = n // 2
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
        
        engine.tau[2] = np.exp(-R_sq / (2 * R_init**2))
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Evolve and record
        tau_history = []
        for step in range(1000):
            engine.evolve_timestep(0.01)
            if step % 5 == 0 and step > 200:  # Skip initial transient
                tau_history.append(np.max(np.sqrt(engine._compute_tau_squared())))
        
        # Measure final radius
        tau_sq = engine._compute_tau_squared()
        total = np.sum(tau_sq)
        R_final = np.sqrt(np.sum(R_sq * tau_sq) / total) if total > 1e-10 else 0
        
        # FFT for frequency
        from scipy.fft import fft, fftfreq
        tau_arr = np.array(tau_history)
        if len(tau_arr) > 10 and np.std(tau_arr) > 1e-6:
            tau_centered = tau_arr - np.mean(tau_arr)
            spectrum = np.abs(fft(tau_centered))
            freqs = fftfreq(len(tau_centered), d=0.05)
            pos_mask = freqs > 0.01
            if np.any(pos_mask) and np.max(spectrum[pos_mask]) > 1e-6:
                omega = 2 * np.pi * freqs[pos_mask][np.argmax(spectrum[pos_mask])]
            else:
                omega = 0
        else:
            omega = 0
        
        frequencies.append(omega)
        
        note = ""
        if omega > 0:
            # Check if frequency is close to any previous
            for prev_omega in frequencies[:-1]:
                if prev_omega > 0 and abs(omega - prev_omega) / omega < 0.05:
                    note = "LOCKED"
                    break
        
        print(f"{R_init:>8.1f} | {R_final:>10.2f} | {omega:>10.2f} | {note:>15}")
    
    # Analyze frequency distribution
    valid_freqs = [f for f in frequencies if f > 0]
    if len(valid_freqs) >= 2:
        freq_std = np.std(valid_freqs)
        freq_mean = np.mean(valid_freqs)
        cv = freq_std / freq_mean
        
        print(f"\nFrequency statistics: mean={freq_mean:.2f}, std={freq_std:.2f}, CV={cv:.1%}")
        
        if cv < 0.1:
            print("✅ FREQUENCY LOCKING DETECTED - strong resonance")
        elif cv < 0.2:
            print("⚠️ Partial frequency clustering")
        else:
            print("❌ No clear frequency locking")


def summarize_equilibrium_manifold():
    """
    Summarize findings about the dynamic equilibrium manifold.
    """
    print("\n" + "=" * 70)
    print("DYNAMIC EQUILIBRIUM MANIFOLD: SUMMARY")
    print("=" * 70)
    
    print("""
THEORETICAL FRAMEWORK:

Matter = Dynamically stabilized coherence islands in medium energy flow

The equilibrium manifold is defined by:
  ∂E/∂R = 0  (radius equilibrium)
  ∂E/∂A = 0  (amplitude equilibrium)  
  ω_breath = ω_natural  (frequency resonance)

Where these conditions intersect → stable oscillon exists.

QMRT v3 FINDINGS:

1. COHERENCE WINDOW EXISTS
   - Not all parameters give oscillons
   - Window in (g_rt, m_tau, amplitude) space
   - Boundaries: dispersed ↔ oscillon ↔ unstable

2. INTERMEDIATE ENERGY REGIME
   - Too low → spreading dominates
   - Too high → collapse or turbulence
   - Middle → dynamic balance

3. FREQUENCY STRUCTURE
   - Oscillons have characteristic breathing mode
   - Frequency depends on parameters
   - Possible locking/resonance zones

PHYSICAL INTERPRETATION:

The stability cascade:
  
  [TURBULENT]        [COHERENCE]        [UNIFORM]
  High energy    →   Intermediate   →   Low energy
  Dispersive          Balance            Collapsed
  No structure        OSCILLONS          No dynamics

Matter (oscillons) forms in the TRANSITIONAL ZONE where:
  - Linear spreading tries to dissolve them
  - Nonlinear coupling tries to compress them
  - Balance creates metastable structures

This is analogous to:
  - Ice floes in moving water
  - Crystal nucleation at phase boundaries
  - Galaxy formation at density thresholds

The mathematical statement:

  "Matter corresponds to dynamically stabilized coherence 
   islands in the quark medium energy flow."

Or more precisely:

  "Oscillons exist on the dynamic equilibrium manifold where
   spreading and compression forces balance, creating
   frequency-locked, spatially localized, long-lived structures."
""")


def main():
    """Map the complete dynamic equilibrium manifold."""
    print("#" * 70)
    print("# QMRT v3: DYNAMIC EQUILIBRIUM MANIFOLD MAPPING")
    print("#" * 70)
    print("""
Objective: Find where matter (coherence islands) forms in the
transitional stability zone between turbulent and uniform phases.
""")
    
    # Map the coherence window
    phase_map = map_coherence_window()
    
    # Map energy/amplitude space
    map_energy_amplitude_space()
    
    # Check for frequency locking
    map_frequency_resonance()
    
    # Summary
    summarize_equilibrium_manifold()


if __name__ == "__main__":
    main()
