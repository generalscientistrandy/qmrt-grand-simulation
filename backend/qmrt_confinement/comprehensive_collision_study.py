"""
QMRT v3: Comprehensive Collision Study
=======================================

Systematic investigation of two-particle collision outcomes:

1. COMPOSITE STRUCTURE FORMATION
   → Do particles bind into stable composites?
   → What binding energies emerge?

2. ANNIHILATION REGIMES  
   → Can particles annihilate (τ → φ conversion)?
   → What conditions trigger annihilation?

3. ENERGY → RADIATION CONVERSION
   → How much energy goes into φ field?
   → Is there a threshold for radiation production?

4. ORBITAL RESONANCE
   → Can particles form stable orbits?
   → Are there resonant configurations?

This tests:
- Proton-like emergence
- Hadron-like binding
- Multiverse frequency separation
"""

import numpy as np
from scipy.ndimage import maximum_filter, center_of_mass
import sys
sys.path.insert(0, '/app/backend')
from qmrt_v3_engine import QMRTv3Engine, QMRTv3Parameters


def setup_two_particle_system(engine, pos1, pos2, mom1=0, mom2=0, amplitude=1.0, radius=2.0):
    """Initialize two torsion particles with given positions and momenta."""
    n = engine.grid_size
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    R1_sq = (X - pos1[0])**2 + (Y - pos1[1])**2 + (Z - pos1[2])**2
    R2_sq = (X - pos2[0])**2 + (Y - pos2[1])**2 + (Z - pos2[2])**2
    
    tau1 = amplitude * np.exp(-R1_sq / (2 * radius**2))
    tau2 = amplitude * np.exp(-R2_sq / (2 * radius**2))
    
    engine.tau[2] = tau1 + tau2
    
    # Momenta in x-direction (toward each other if opposite signs)
    if mom1 != 0 or mom2 != 0:
        # Momentum ~ amplitude * velocity for wave packet
        engine.pi_tau[2] = mom1 * tau1 + mom2 * tau2
    
    engine.initial_energy = engine.compute_total_energy()['E_total']
    return tau1, tau2


def analyze_structure(engine, threshold_frac=0.05):
    """Analyze the current field structure."""
    tau_sq = engine._compute_tau_squared()
    
    if np.max(tau_sq) < 1e-10:
        return {'n_peaks': 0, 'peak_positions': [], 'total_tau_sq': 0}
    
    threshold = threshold_frac * np.max(tau_sq)
    local_max = (tau_sq == maximum_filter(tau_sq, size=3)) & (tau_sq > threshold)
    
    peak_positions = np.array(np.where(local_max)).T
    n_peaks = len(peak_positions)
    
    # Calculate center of mass
    n = engine.grid_size
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    total = np.sum(tau_sq)
    if total > 0:
        com = np.array([np.sum(X * tau_sq), np.sum(Y * tau_sq), np.sum(Z * tau_sq)]) / total
    else:
        com = np.array([n/2, n/2, n/2])
    
    return {
        'n_peaks': n_peaks,
        'peak_positions': peak_positions,
        'total_tau_sq': total,
        'tau_max': np.max(np.sqrt(tau_sq)),
        'center_of_mass': com,
    }


def measure_radiation_emission(engine):
    """Measure energy in the radiation (φ) field."""
    energies = engine.compute_total_energy()
    return {
        'E_phi': energies['E_phi'],
        'E_tau': energies['E_tau'],
        'E_rho': energies['E_rho'],
        'E_total': energies['E_total'],
        'phi_fraction': energies['E_phi'] / max(engine.initial_energy, 1e-10),
    }


# =============================================================================
# TEST 1: COLLISION ENERGY SCAN
# =============================================================================

def scan_collision_energies():
    """Scan collision outcomes as function of collision energy."""
    print("=" * 70)
    print("TEST 1: COLLISION ENERGY SCAN")
    print("=" * 70)
    print("Question: How does collision energy affect outcomes?")
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Momentum values (collision energy ~ p²)
    momenta = [0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8]
    
    print(f"\n{'p':>6} | {'KE_init':>10} | {'Peaks_f':>8} | {'φ_frac':>10} | {'τ_max':>8} | {'Outcome':>15}")
    print("-" * 75)
    
    results = []
    
    for p in momenta:
        engine = QMRTv3Engine(grid_size=28, params=params)
        
        # Two particles approaching
        center = engine.grid_size // 2
        pos1 = (center - 5, center, center)
        pos2 = (center + 5, center, center)
        
        setup_two_particle_system(engine, pos1, pos2, mom1=p, mom2=-p)
        
        # Estimate kinetic energy
        KE_init = 0.5 * np.sum(engine.pi_tau**2) * engine.dx**3
        
        # Evolve
        for _ in range(3000):  # 30 time units
            engine.evolve_timestep(0.01)
        
        # Analyze outcome
        structure = analyze_structure(engine)
        radiation = measure_radiation_emission(engine)
        
        # Classify outcome
        if structure['n_peaks'] == 0:
            outcome = "ANNIHILATED"
        elif structure['n_peaks'] == 1:
            outcome = "MERGED"
        elif structure['n_peaks'] == 2:
            outcome = "SCATTERED"
        elif structure['n_peaks'] <= 5:
            outcome = "EXCITED"
        else:
            outcome = "FRAGMENTED"
        
        results.append({
            'p': p, 'KE': KE_init, 'n_peaks': structure['n_peaks'],
            'phi_frac': radiation['phi_fraction'], 'tau_max': structure['tau_max'],
            'outcome': outcome
        })
        
        print(f"{p:6.2f} | {KE_init:10.2f} | {structure['n_peaks']:8d} | "
              f"{radiation['phi_fraction']:10.4%} | {structure['tau_max']:8.4f} | {outcome:>15}")
    
    # Find thresholds
    merge_threshold = max([r['p'] for r in results if r['outcome'] == 'MERGED'], default=0)
    fragment_threshold = min([r['p'] for r in results if r['outcome'] == 'FRAGMENTED'], default=999)
    
    print(f"\n>>> FUSION threshold: p < {merge_threshold:.2f}")
    print(f">>> FRAGMENTATION threshold: p > {fragment_threshold:.2f}")
    
    return results


# =============================================================================
# TEST 2: ANNIHILATION SEARCH
# =============================================================================

def search_annihilation():
    """Search for annihilation regimes (τ → φ conversion)."""
    print("\n" + "=" * 70)
    print("TEST 2: ANNIHILATION REGIME SEARCH")
    print("=" * 70)
    print("Question: Can torsion energy convert to radiation?")
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Try high-energy collisions with different radiation couplings
    g_tp_values = [0.1, 0.3, 0.5, 1.0]
    
    print(f"\n{'g_tp':>6} | {'p':>6} | {'τ_init':>10} | {'τ_final':>10} | {'φ_frac':>10} | {'Annihil?':>10}")
    print("-" * 70)
    
    for g_tp in g_tp_values:
        params_test = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=g_tp)
        
        engine = QMRTv3Engine(grid_size=28, params=params_test)
        center = engine.grid_size // 2
        
        # High-energy head-on collision
        p = 0.5
        setup_two_particle_system(engine, 
                                  (center - 5, center, center),
                                  (center + 5, center, center),
                                  mom1=p, mom2=-p)
        
        tau_init = np.sum(engine._compute_tau_squared()) * engine.dx**3
        
        # Evolve
        for _ in range(4000):
            engine.evolve_timestep(0.01)
        
        tau_final = np.sum(engine._compute_tau_squared()) * engine.dx**3
        radiation = measure_radiation_emission(engine)
        
        tau_loss = 1 - tau_final / tau_init
        annihilated = "YES" if tau_loss > 0.5 else ("partial" if tau_loss > 0.2 else "no")
        
        print(f"{g_tp:6.2f} | {p:6.2f} | {tau_init:10.2f} | {tau_final:10.2f} | "
              f"{radiation['phi_fraction']:10.4%} | {annihilated:>10}")
    
    print("\nAnnihilation = significant τ loss + radiation emission")


# =============================================================================
# TEST 3: ORBITAL RESONANCE SEARCH
# =============================================================================

def search_orbital_resonance():
    """Search for stable orbital configurations."""
    print("\n" + "=" * 70)
    print("TEST 3: ORBITAL RESONANCE SEARCH")
    print("=" * 70)
    print("Question: Can particles form stable orbits?")
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    # Give particles tangential momentum for orbital motion
    orbital_momenta = [0.02, 0.05, 0.08, 0.1, 0.15]
    
    print(f"\n{'p_tang':>8} | {'Sep_0':>8} | {'Sep_10':>8} | {'Sep_20':>8} | {'Sep_30':>8} | {'Type':>12}")
    print("-" * 70)
    
    for p_tang in orbital_momenta:
        engine = QMRTv3Engine(grid_size=32, params=params)
        n = engine.grid_size
        center = n // 2
        
        # Two particles with tangential momentum (perpendicular to line joining them)
        pos1 = (center - 4, center, center)
        pos2 = (center + 4, center, center)
        
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        R1_sq = (X - pos1[0])**2 + (Y - pos1[1])**2 + (Z - pos1[2])**2
        R2_sq = (X - pos2[0])**2 + (Y - pos2[1])**2 + (Z - pos2[2])**2
        
        tau1 = np.exp(-R1_sq / 8)
        tau2 = np.exp(-R2_sq / 8)
        
        engine.tau[2] = tau1 + tau2
        
        # Tangential momentum in Y direction (perpendicular to X separation)
        engine.pi_tau[2] = p_tang * tau1 - p_tang * tau2  # Opposite tangential
        
        engine.initial_energy = engine.compute_total_energy()['E_total']
        
        # Track separation over time
        separations = []
        
        def measure_separation():
            tau_sq = engine._compute_tau_squared()
            total = np.sum(tau_sq)
            if total < 1e-10:
                return 0
            # Find two largest peaks and measure their separation
            threshold = 0.1 * np.max(tau_sq)
            local_max = (tau_sq == maximum_filter(tau_sq, size=3)) & (tau_sq > threshold)
            peaks = np.array(np.where(local_max)).T
            if len(peaks) >= 2:
                # Distance between two highest peaks
                peak_vals = [tau_sq[tuple(p)] for p in peaks]
                sorted_idx = np.argsort(peak_vals)[-2:]
                p1, p2 = peaks[sorted_idx[0]], peaks[sorted_idx[1]]
                return np.sqrt(np.sum((p1 - p2)**2))
            elif len(peaks) == 1:
                return 0  # Merged
            return -1  # Unknown
        
        sep_history = []
        for t in [0, 10, 20, 30]:
            if t > 0:
                for _ in range(1000):
                    engine.evolve_timestep(0.01)
            sep = measure_separation()
            sep_history.append(sep)
        
        # Classify orbital type
        if sep_history[-1] == 0:
            orbit_type = "MERGED"
        elif sep_history[-1] < 0:
            orbit_type = "DISPERSED"
        elif abs(sep_history[-1] - sep_history[0]) < 2:
            orbit_type = "STABLE ORBIT"
        elif sep_history[-1] > sep_history[0] * 1.5:
            orbit_type = "ESCAPING"
        else:
            orbit_type = "OSCILLATING"
        
        print(f"{p_tang:8.2f} | {sep_history[0]:8.1f} | {sep_history[1]:8.1f} | "
              f"{sep_history[2]:8.1f} | {sep_history[3]:8.1f} | {orbit_type:>12}")
    
    print("\nStable orbit = separation remains roughly constant")


# =============================================================================
# TEST 4: COMPOSITE STRUCTURE FORMATION
# =============================================================================

def test_composite_formation():
    """Test if merged states form stable composites."""
    print("\n" + "=" * 70)
    print("TEST 4: COMPOSITE STRUCTURE ANALYSIS")
    print("=" * 70)
    print("Question: Do merged states form stable proton-like composites?")
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    engine = QMRTv3Engine(grid_size=28, params=params)
    center = engine.grid_size // 2
    
    # Create merged state via slow collision
    setup_two_particle_system(engine,
                              (center - 4, center, center),
                              (center + 4, center, center),
                              mom1=0.03, mom2=-0.03)
    
    E_init = engine.initial_energy
    
    print(f"\nInitial: 2 particles approaching slowly")
    print(f"Initial energy: {E_init:.2f}")
    
    # Track merger
    print(f"\n{'t':>6} | {'Peaks':>6} | {'τ_max':>8} | {'R_eff':>8} | {'E_τ':>10} | {'E_φ':>10}")
    print("-" * 60)
    
    for t in [0, 10, 20, 30, 40, 50]:
        if t > 0:
            for _ in range(1000):
                engine.evolve_timestep(0.01)
        
        structure = analyze_structure(engine)
        radiation = measure_radiation_emission(engine)
        R_eff = engine.measure_torsion_radius()
        
        print(f"{t:6.0f} | {structure['n_peaks']:6d} | {structure['tau_max']:8.4f} | "
              f"{R_eff:8.2f} | {radiation['E_tau']:10.2f} | {radiation['E_phi']:10.4f}")
    
    # Analyze final state
    final_structure = analyze_structure(engine)
    final_radiation = measure_radiation_emission(engine)
    
    if final_structure['n_peaks'] == 1:
        print(f"\n✅ COMPOSITE FORMED!")
        print(f"   Final radius: {engine.measure_torsion_radius():.2f}")
        print(f"   Final τ_max: {final_structure['tau_max']:.4f}")
        print(f"   Energy retained in τ: {final_radiation['E_tau']/E_init:.1%}")
        print(f"   Energy radiated (φ): {final_radiation['phi_fraction']:.4%}")
        
        # Compare to single particle
        engine_single = QMRTv3Engine(grid_size=28, params=params)
        engine_single.initialize_vacuum()
        engine_single.initialize_torsion_perturbation(amplitude=1.0, radius=2.0)
        E_single = engine_single.compute_total_energy()['E_total']
        
        binding_E = E_init - final_radiation['E_total']
        print(f"\n   Binding energy: {binding_E:.2f}")
        print(f"   (Negative = energy released in fusion)")
    else:
        print(f"\n❌ Did not form single composite (peaks = {final_structure['n_peaks']})")


# =============================================================================
# TEST 5: THREE-BODY PROBLEM
# =============================================================================

def test_three_body():
    """Test three-particle interactions."""
    print("\n" + "=" * 70)
    print("TEST 5: THREE-BODY PROBLEM")
    print("=" * 70)
    print("Question: Can three particles form stable bound states?")
    
    params = QMRTv3Parameters(g_rt=3.0, m_tau=4.0, g_tp=0.1)
    
    engine = QMRTv3Engine(grid_size=32, params=params)
    n = engine.grid_size
    center = n // 2
    
    # Three particles in equilateral triangle
    R = 5  # Triangle radius
    angles = [0, 2*np.pi/3, 4*np.pi/3]
    
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    total_tau = np.zeros((n, n, n))
    for angle in angles:
        px = center + R * np.cos(angle)
        py = center + R * np.sin(angle)
        pz = center
        R_sq = (X - px)**2 + (Y - py)**2 + (Z - pz)**2
        total_tau += np.exp(-R_sq / 8)
    
    engine.tau[2] = total_tau
    engine.initial_energy = engine.compute_total_energy()['E_total']
    
    print(f"\nInitial: 3 particles in equilateral triangle (R={R})")
    print(f"Initial energy: {engine.initial_energy:.2f}")
    
    print(f"\n{'t':>6} | {'Peaks':>6} | {'τ_max':>8} | {'Spread':>10}")
    print("-" * 40)
    
    def measure_spread():
        tau_sq = engine._compute_tau_squared()
        total = np.sum(tau_sq)
        if total < 1e-10:
            return 0
        # RMS distance from center
        X_c = np.sum(X * tau_sq) / total
        Y_c = np.sum(Y * tau_sq) / total
        Z_c = np.sum(Z * tau_sq) / total
        R_sq_from_center = (X - X_c)**2 + (Y - Y_c)**2 + (Z - Z_c)**2
        return np.sqrt(np.sum(R_sq_from_center * tau_sq) / total)
    
    for t in [0, 10, 20, 30, 40]:
        if t > 0:
            for _ in range(1000):
                engine.evolve_timestep(0.01)
        
        structure = analyze_structure(engine)
        spread = measure_spread()
        
        print(f"{t:6.0f} | {structure['n_peaks']:6d} | {structure['tau_max']:8.4f} | {spread:10.2f}")
    
    final_structure = analyze_structure(engine)
    
    if final_structure['n_peaks'] == 1:
        print(f"\n✅ THREE-BODY BOUND STATE FORMED!")
    elif final_structure['n_peaks'] == 3:
        print(f"\n⚠️ Three particles remain separate (stable configuration?)")
    else:
        print(f"\n❓ Complex outcome: {final_structure['n_peaks']} peaks")


def main():
    """Run comprehensive collision study."""
    print("#" * 70)
    print("# QMRT v3: COMPREHENSIVE COLLISION STUDY")
    print("#" * 70)
    print("""
Testing:
- Proton-like emergence
- Hadron-like binding  
- Multiverse frequency separation

Key questions:
1. Does collision energy determine fusion vs fragmentation?
2. Can particles annihilate (τ → φ)?
3. Can particles form stable orbits?
4. Do composites have proton-like properties?
5. Can three particles bind?
""")
    
    # Run all tests
    collision_results = scan_collision_energies()
    search_annihilation()
    search_orbital_resonance()
    test_composite_formation()
    test_three_body()
    
    # Summary
    print("\n" + "=" * 70)
    print("COLLISION STUDY SUMMARY")
    print("=" * 70)
    print("""
Key findings will appear above for each test.

PHYSICS INTERPRETATION:
- FUSION at low energy → nuclear binding analog
- FRAGMENTATION at high energy → particle production analog  
- τ→φ conversion → matter-antimatter annihilation analog
- Stable orbits → atomic/molecular analog
- Three-body bound states → nuclear/hadronic analog
""")


if __name__ == "__main__":
    main()
