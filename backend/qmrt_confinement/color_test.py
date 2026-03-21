"""
QMRT Quark Confinement Analogies - Step 3: Internal Degree of Freedom Test
(Color Analog)

KEY QUESTIONS:
1. Do proton-like states require phase triplet locking?
2. Does neutral composite minimize domain energy?

If YES to both →
    Candidate mechanism for:
    - Baryon formation
    - Composite stability threshold
    - Regime transition ladder

Physical context:
    In QCD: quarks carry color charge (red, green, blue)
    In QMRT: excitations carry PHASE (φ) and FREQUENCY (ω) degrees of freedom
    
    Color neutrality analog:
    - QCD: R + G + B = white (neutral)
    - QMRT: Multiple excitations with phase/frequency balance → stable composite

Tests:
1. ISOLATED EXCITATION: Does it decohere over time?
2. PAIR COMPOSITE: Two excitations - more stable than isolated?
3. TRIPLET COMPOSITE: Three excitations - most stable configuration?
4. PHASE TRIPLET LOCKING: Do stable composites require specific phase relations?
5. DOMAIN ENERGY MINIMIZATION: Does neutral composite minimize total domain energy?
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import minimize
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters


@dataclass
class ExcitationConfig:
    """Configuration for a single excitation"""
    position: Tuple[float, float, float]
    amplitude: float
    width: float
    phase_offset: float = 0.0  # Phase angle (0, 2π/3, 4π/3 for triplet)


@dataclass 
class CompositeState:
    """State of a composite at a point in time"""
    time: float
    
    # Individual excitation metrics
    excitation_amplitudes: List[float]
    excitation_widths: List[float]
    excitations_preserved: List[bool]
    
    # Composite metrics
    total_energy: float
    binding_energy: float  # E_composite - sum(E_isolated)
    center_of_mass: Tuple[float, float, float]
    composite_width: float  # Overall extent
    
    # Phase coherence
    phase_coherence: float  # 0-1, measures phase correlation
    phase_variance: float
    
    # Domain metrics  
    domain_wall_energy: float
    domain_occupation: float  # Fraction in frequency basin
    
    def to_dict(self) -> Dict:
        return {
            'time': float(self.time),
            'excitation_amplitudes': [float(a) for a in self.excitation_amplitudes],
            'excitation_widths': [float(w) for w in self.excitation_widths],
            'excitations_preserved': self.excitations_preserved,
            'total_energy': float(self.total_energy),
            'binding_energy': float(self.binding_energy),
            'center_of_mass': [float(x) for x in self.center_of_mass],
            'composite_width': float(self.composite_width),
            'phase_coherence': float(self.phase_coherence),
            'phase_variance': float(self.phase_variance),
            'domain_wall_energy': float(self.domain_wall_energy),
            'domain_occupation': float(self.domain_occupation)
        }


@dataclass
class InternalDoFResult:
    """Result from internal degree of freedom test"""
    
    # Configuration
    num_excitations: int
    configuration_name: str  # 'isolated', 'pair', 'triplet', 'custom'
    
    # Time series
    states: List[CompositeState] = field(default_factory=list)
    
    # Stability metrics
    survived_time: float = 0.0
    final_preservation_rate: float = 0.0
    decoherence_rate: float = 0.0  # Rate at which phase coherence decays
    
    # Energy metrics
    initial_energy: float = 0.0
    final_energy: float = 0.0
    binding_energy_avg: float = 0.0
    binding_energy_stable: bool = False
    
    # Phase locking
    phase_locked: bool = False
    phase_lock_strength: float = 0.0
    optimal_phase_relation: List[float] = field(default_factory=list)
    
    # Composite stability
    composite_stable: bool = False
    stability_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'configuration': {
                'num_excitations': int(self.num_excitations),
                'name': self.configuration_name
            },
            'time_series': [s.to_dict() for s in self.states],
            'stability': {
                'survived_time': float(self.survived_time),
                'final_preservation_rate': float(self.final_preservation_rate),
                'decoherence_rate': float(self.decoherence_rate)
            },
            'energy': {
                'initial': float(self.initial_energy),
                'final': float(self.final_energy),
                'binding_avg': float(self.binding_energy_avg),
                'binding_stable': self.binding_energy_stable
            },
            'phase_locking': {
                'locked': self.phase_locked,
                'strength': float(self.phase_lock_strength),
                'optimal_phases': [float(p) for p in self.optimal_phase_relation]
            },
            'composite': {
                'stable': self.composite_stable,
                'score': float(self.stability_score)
            },
            'verdict': self._get_verdict()
        }
    
    def _get_verdict(self) -> str:
        if self.composite_stable and self.phase_locked:
            return f"STABLE COMPOSITE: {self.configuration_name} configuration is stable with phase locking (score={self.stability_score:.2f}). Candidate for baryon analog."
        elif self.composite_stable:
            return f"QUASI-STABLE: {self.configuration_name} is stable but no clear phase locking (score={self.stability_score:.2f})."
        elif self.num_excitations == 1:
            return f"ISOLATED DECOHERENCE: Single excitation {'stable' if self.final_preservation_rate > 0.5 else 'decohered'}."
        else:
            return f"UNSTABLE: {self.configuration_name} composite not stable (score={self.stability_score:.2f})."


def create_excitation_at(
    engine: QMRTFrequencyEngine,
    config: ExcitationConfig
) -> None:
    """Add an excitation to the engine at specified configuration"""
    n = engine.grid_size
    p = engine.params
    
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    px, py, pz = config.position
    R_sq = (X - px)**2 + (Y - py)**2 + (Z - pz)**2
    
    # Gaussian profile in omega
    profile = config.amplitude * np.exp(-R_sq / (2 * config.width**2))
    engine.omega = engine.omega + profile
    
    # Apply phase offset to phi field (for phase-locking test)
    if abs(config.phase_offset) > 0.01:
        phase_profile = config.phase_offset * np.exp(-R_sq / (2 * config.width**2))
        engine.phi = engine.phi + phase_profile


def measure_excitation(
    engine: QMRTFrequencyEngine,
    config: ExcitationConfig,
    threshold_fraction: float = 0.1
) -> Tuple[float, float, bool]:
    """
    Measure amplitude, width, and preservation of an excitation.
    
    Returns: (amplitude, width, preserved)
    """
    n = engine.grid_size
    p = engine.params
    px, py, pz = config.position
    
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Expected excitation region
    R_sq = (X - px)**2 + (Y - py)**2 + (Z - pz)**2
    search_radius = config.width * 3
    search_mask = R_sq < search_radius**2
    
    # Find omega excess above background
    background = np.where(engine.omega > 0, p.omega_0, -p.omega_0)
    excess = engine.omega - background
    
    threshold = threshold_fraction * config.amplitude
    excitation_mask = (np.abs(excess) > threshold) & search_mask
    
    if np.sum(excitation_mask) < 5:
        return 0.0, float('inf'), False
    
    # Amplitude
    amplitude = float(np.max(np.abs(excess[search_mask])))
    
    # Width (RMS)
    excitation_field = np.abs(excess) * excitation_mask
    total_weight = np.sum(excitation_field)
    
    if total_weight > 0:
        com_x = np.sum(X * excitation_field) / total_weight
        com_y = np.sum(Y * excitation_field) / total_weight
        com_z = np.sum(Z * excitation_field) / total_weight
        
        R_sq_from_com = (X - com_x)**2 + (Y - com_y)**2 + (Z - com_z)**2
        width = float(np.sqrt(np.sum(R_sq_from_com * excitation_field) / total_weight))
    else:
        width = float('inf')
    
    # Preserved if amplitude > 50% of initial
    preserved = amplitude > 0.5 * config.amplitude
    
    return amplitude, width, preserved


def measure_phase_coherence(
    engine: QMRTFrequencyEngine,
    configs: List[ExcitationConfig]
) -> Tuple[float, float]:
    """
    Measure phase coherence between excitations.
    
    Returns: (coherence 0-1, phase_variance)
    """
    n = engine.grid_size
    phases = []
    
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    for config in configs:
        px, py, pz = config.position
        R_sq = (X - px)**2 + (Y - py)**2 + (Z - pz)**2
        mask = R_sq < (config.width * 2)**2
        
        if np.sum(mask) > 0:
            local_phase = np.mean(engine.phi[mask])
            phases.append(local_phase)
    
    if len(phases) < 2:
        return 1.0, 0.0
    
    phases = np.array(phases)
    
    # Phase variance (wrapped)
    phase_mean = np.angle(np.mean(np.exp(1j * phases)))
    phase_diffs = np.angle(np.exp(1j * (phases - phase_mean)))
    phase_variance = float(np.var(phase_diffs))
    
    # Coherence: 1 if all phases aligned, 0 if random
    coherence = float(np.abs(np.mean(np.exp(1j * phases))))
    
    return coherence, phase_variance


def measure_domain_energy(
    engine: QMRTFrequencyEngine,
    configs: List[ExcitationConfig]
) -> Tuple[float, float]:
    """
    Measure domain wall energy and basin occupation.
    
    Returns: (wall_energy, basin_occupation)
    """
    p = engine.params
    
    # Gradient energy (domain walls)
    grad_omega_sq = (
        np.gradient(engine.omega, axis=0)**2 +
        np.gradient(engine.omega, axis=1)**2 +
        np.gradient(engine.omega, axis=2)**2
    )
    wall_energy = float(np.sum(0.5 * p.K_omega * grad_omega_sq) * engine.dx**3)
    
    # Basin occupation
    in_high_basin = np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)
    in_low_basin = np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)
    total = engine.omega.size
    basin_occupation = float((in_high_basin + in_low_basin) / total)
    
    return wall_energy, basin_occupation


def measure_composite_state(
    engine: QMRTFrequencyEngine,
    configs: List[ExcitationConfig],
    isolated_energy_sum: float
) -> CompositeState:
    """Measure full composite state"""
    n = engine.grid_size
    p = engine.params
    
    # Measure individual excitations
    amplitudes = []
    widths = []
    preserved = []
    
    for config in configs:
        a, w, p_flag = measure_excitation(engine, config)
        amplitudes.append(a)
        widths.append(w)
        preserved.append(p_flag)
    
    # Total energy
    total_energy = engine.compute_total_energy()
    binding_energy = total_energy - isolated_energy_sum
    
    # Center of mass of composite
    if len(configs) > 0:
        com = np.mean([c.position for c in configs], axis=0)
    else:
        com = (n/2, n/2, n/2)
    
    # Composite width (max extent)
    if len(configs) > 1:
        positions = np.array([c.position for c in configs])
        max_dist = 0.0
        for i in range(len(positions)):
            for j in range(i+1, len(positions)):
                d = np.linalg.norm(positions[i] - positions[j])
                max_dist = max(max_dist, d)
        composite_width = max_dist + 2 * np.mean(widths)
    else:
        composite_width = widths[0] if widths else 0.0
    
    # Phase coherence
    coherence, phase_var = measure_phase_coherence(engine, configs)
    
    # Domain metrics
    wall_energy, basin_occ = measure_domain_energy(engine, configs)
    
    return CompositeState(
        time=engine.time,
        excitation_amplitudes=amplitudes,
        excitation_widths=widths,
        excitations_preserved=preserved,
        total_energy=total_energy,
        binding_energy=binding_energy,
        center_of_mass=tuple(com),
        composite_width=composite_width,
        phase_coherence=coherence,
        phase_variance=phase_var,
        domain_wall_energy=wall_energy,
        domain_occupation=basin_occ
    )


def run_composite_stability_test(
    configs: List[ExcitationConfig],
    configuration_name: str,
    grid_size: int = 24,
    total_time: float = 30.0,
    dt: float = 0.02,
    seed: int = 42
) -> InternalDoFResult:
    """
    Run stability test for a composite configuration.
    """
    print(f"\n{'='*60}")
    print(f"COMPOSITE STABILITY TEST: {configuration_name}")
    print(f"{'='*60}")
    print(f"Excitations: {len(configs)}, Grid: {grid_size}³, Time: {total_time}s")
    
    # Initialize
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    # Stabilize substrate
    for _ in range(100):
        engine.evolve_timestep(dt)
    
    # Measure isolated energy (approximate)
    isolated_energy_per_excitation = 0.0
    if len(configs) > 0:
        # Quick estimate from one excitation
        test_engine = QMRTFrequencyEngine(grid_size=grid_size)
        test_engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
        for _ in range(50):
            test_engine.evolve_timestep(dt)
        E_before = test_engine.compute_total_energy()
        create_excitation_at(test_engine, configs[0])
        for _ in range(50):
            test_engine.evolve_timestep(dt)
        E_after = test_engine.compute_total_energy()
        isolated_energy_per_excitation = E_after - E_before
    
    isolated_energy_sum = len(configs) * isolated_energy_per_excitation
    
    # Create all excitations
    for config in configs:
        create_excitation_at(engine, config)
    
    initial_energy = engine.compute_total_energy()
    
    # Evolve and track
    result = InternalDoFResult(
        num_excitations=len(configs),
        configuration_name=configuration_name,
        initial_energy=initial_energy
    )
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    print(f"\nEvolving composite...")
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            state = measure_composite_state(engine, configs, isolated_energy_sum)
            result.states.append(state)
            
            if step % (sample_interval * 5) == 0:
                pres_rate = sum(state.excitations_preserved) / len(configs) if configs else 0
                print(f"  t={state.time:.1f}s: preserved={pres_rate:.0%}, "
                      f"binding={state.binding_energy:.2f}, coherence={state.phase_coherence:.2f}")
    
    # Analyze results
    if len(result.states) > 5:
        final_states = result.states[-5:]
        
        # Survival time
        for s in result.states:
            if all(s.excitations_preserved):
                result.survived_time = s.time
        
        # Final preservation rate
        final_preserved = [sum(s.excitations_preserved) / len(configs) for s in final_states]
        result.final_preservation_rate = np.mean(final_preserved)
        
        # Binding energy
        binding_energies = [s.binding_energy for s in result.states]
        result.binding_energy_avg = np.mean(binding_energies[-10:])
        binding_stable = np.std(binding_energies[-10:]) < 0.1 * abs(result.binding_energy_avg + 1)
        result.binding_energy_stable = binding_stable
        
        # Phase coherence
        coherences = [s.phase_coherence for s in result.states]
        if len(coherences) > 5:
            initial_coh = np.mean(coherences[:5])
            final_coh = np.mean(coherences[-5:])
            if initial_coh > 0.1:
                result.decoherence_rate = (initial_coh - final_coh) / total_time
        
        # Phase locking (coherence > 0.7 at end)
        result.phase_lock_strength = np.mean([s.phase_coherence for s in final_states])
        result.phase_locked = result.phase_lock_strength > 0.7
        
        # Composite stability
        result.composite_stable = (
            result.final_preservation_rate > 0.8 and
            result.binding_energy_stable
        )
        
        # Stability score
        score = 0.0
        score += 0.3 * result.final_preservation_rate
        score += 0.2 * result.phase_lock_strength
        score += 0.2 * (1.0 if result.binding_energy_stable else 0.0)
        score += 0.3 * (1.0 if result.binding_energy_avg < 0 else 0.0)  # Negative binding = attractive
        result.stability_score = score
    
    result.final_energy = engine.compute_total_energy()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"RESULT: {configuration_name}")
    print(f"{'='*60}")
    print(f"  Preservation rate: {result.final_preservation_rate:.0%}")
    print(f"  Binding energy: {result.binding_energy_avg:.2f}")
    print(f"  Phase coherence: {result.phase_lock_strength:.2f}")
    print(f"  Phase locked: {'✅' if result.phase_locked else '❌'}")
    print(f"  Composite stable: {'✅' if result.composite_stable else '❌'}")
    print(f"  Stability score: {result.stability_score:.2f}")
    print(f"\n  VERDICT: {result._get_verdict()}")
    print(f"{'='*60}\n")
    
    return result


def run_internal_dof_test(
    grid_size: int = 24,
    excitation_amplitude: float = 0.3,
    excitation_width: float = 2.0,
    separation: float = 8.0,
    total_time: float = 25.0,
    dt: float = 0.02,
    seed: int = 42
) -> Dict:
    """
    Run the complete internal degree of freedom test.
    
    Tests:
    1. Single isolated excitation
    2. Pair composite (2 excitations)
    3. Triplet composite (3 excitations in triangle)
    4. Triplet with phase offsets (color analog)
    """
    print("\n" + "="*70)
    print("STEP 3: INTERNAL DEGREE OF FREEDOM TEST")
    print("="*70)
    print("Testing: Do proton-like states require phase triplet locking?")
    print("         Does neutral composite minimize domain energy?")
    print("="*70)
    
    center = grid_size // 2
    amplitude = excitation_amplitude
    width = excitation_width
    
    results = {}
    
    # Test 1: Single isolated excitation
    single_config = [
        ExcitationConfig(
            position=(center, center, center),
            amplitude=amplitude,
            width=width
        )
    ]
    results['isolated'] = run_composite_stability_test(
        single_config, "ISOLATED",
        grid_size=grid_size, total_time=total_time, dt=dt, seed=seed
    )
    
    # Test 2: Pair composite
    pair_configs = [
        ExcitationConfig(
            position=(center - separation/2, center, center),
            amplitude=amplitude,
            width=width
        ),
        ExcitationConfig(
            position=(center + separation/2, center, center),
            amplitude=amplitude,
            width=width
        )
    ]
    results['pair'] = run_composite_stability_test(
        pair_configs, "PAIR",
        grid_size=grid_size, total_time=total_time, dt=dt, seed=seed
    )
    
    # Test 3: Triplet (equilateral triangle)
    r = separation / np.sqrt(3)  # Radius for equilateral triangle
    triplet_configs = [
        ExcitationConfig(
            position=(center + r, center, center),
            amplitude=amplitude,
            width=width,
            phase_offset=0.0
        ),
        ExcitationConfig(
            position=(center - r/2, center + r * np.sqrt(3)/2, center),
            amplitude=amplitude,
            width=width,
            phase_offset=0.0
        ),
        ExcitationConfig(
            position=(center - r/2, center - r * np.sqrt(3)/2, center),
            amplitude=amplitude,
            width=width,
            phase_offset=0.0
        )
    ]
    results['triplet'] = run_composite_stability_test(
        triplet_configs, "TRIPLET",
        grid_size=grid_size, total_time=total_time, dt=dt, seed=seed
    )
    
    # Test 4: Triplet with 120° phase offsets (color analog: R+G+B=white)
    triplet_phase_configs = [
        ExcitationConfig(
            position=(center + r, center, center),
            amplitude=amplitude,
            width=width,
            phase_offset=0.0  # "Red"
        ),
        ExcitationConfig(
            position=(center - r/2, center + r * np.sqrt(3)/2, center),
            amplitude=amplitude,
            width=width,
            phase_offset=2*np.pi/3  # "Green"
        ),
        ExcitationConfig(
            position=(center - r/2, center - r * np.sqrt(3)/2, center),
            amplitude=amplitude,
            width=width,
            phase_offset=4*np.pi/3  # "Blue"
        )
    ]
    results['triplet_phase_locked'] = run_composite_stability_test(
        triplet_phase_configs, "TRIPLET_PHASE_LOCKED",
        grid_size=grid_size, total_time=total_time, dt=dt, seed=seed
    )
    
    # Summary analysis
    print("\n" + "="*70)
    print("INTERNAL DEGREE OF FREEDOM TEST SUMMARY")
    print("="*70)
    
    print("\nCOMPARATIVE STABILITY:")
    for name, res in results.items():
        status = "✅" if res.composite_stable else "❌"
        phase_status = "🔒" if res.phase_locked else "🔓"
        print(f"  {name:25s}: score={res.stability_score:.2f} {status} phase={phase_status}")
    
    # Key findings
    isolated_decoheres = not results['isolated'].composite_stable
    composite_stabilizes = (
        results['pair'].stability_score > results['isolated'].stability_score or
        results['triplet'].stability_score > results['isolated'].stability_score
    )
    phase_locking_helps = (
        results['triplet_phase_locked'].stability_score > 
        results['triplet'].stability_score
    )
    
    # Domain energy comparison
    domain_energies = {
        name: np.mean([s.domain_wall_energy for s in res.states[-5:]]) 
        for name, res in results.items() if res.states
    }
    min_domain_energy_config = min(domain_energies, key=domain_energies.get)
    
    print(f"\nKEY FINDINGS:")
    print(f"  Isolated excitation decoheres:     {'✅ YES' if isolated_decoheres else '❌ NO'}")
    print(f"  Composite more stable than isolated: {'✅ YES' if composite_stabilizes else '❌ NO'}")
    print(f"  Phase locking improves stability:  {'✅ YES' if phase_locking_helps else '❌ NO'}")
    print(f"  Minimum domain energy config:      {min_domain_energy_config}")
    
    print(f"\nDOMAIN WALL ENERGIES:")
    for name, E in domain_energies.items():
        print(f"  {name:25s}: E_wall = {E:.4f}")
    
    # Final verdict
    confinement_mechanism = (
        isolated_decoheres and
        composite_stabilizes
    )
    
    print(f"\n{'='*70}")
    print("VERDICT")
    print(f"{'='*70}")
    
    if confinement_mechanism and phase_locking_helps:
        print("""
✅ NEW CONFINEMENT MECHANISM CLASS DISCOVERED:
   - Excitations DECOHERE when isolated
   - Excitations STABILIZE in composite phase resonance
   - Phase triplet locking ENHANCES stability
   
   This is a candidate mechanism for:
   - Baryon formation
   - Composite stability threshold
   - Regime transition ladder
""")
    elif confinement_mechanism:
        print("""
⚠️  PARTIAL CONFINEMENT MECHANISM:
   - Excitations decohere when isolated
   - Composites provide some stabilization
   - Phase locking NOT a dominant factor
   
   Need further investigation of stability conditions.
""")
    elif composite_stabilizes:
        print("""
⚠️  COMPOSITE ENHANCEMENT (NO DECOHERENCE):
   - Isolated excitations remain stable
   - Composites show binding effects
   - Mechanism differs from QCD-like confinement
""")
    else:
        print("""
❌ NO CLEAR CONFINEMENT MECHANISM:
   - Neither decoherence nor composite stabilization observed
   - Proton formation regime assumptions may need revision
""")
    
    print(f"{'='*70}\n")
    
    return {
        'results': {k: v.to_dict() for k, v in results.items()},
        'findings': {
            'isolated_decoheres': isolated_decoheres,
            'composite_stabilizes': composite_stabilizes,
            'phase_locking_helps': phase_locking_helps,
            'min_domain_energy_config': min_domain_energy_config,
            'confinement_mechanism_found': confinement_mechanism
        }
    }


if __name__ == "__main__":
    results = run_internal_dof_test(
        grid_size=24,
        excitation_amplitude=0.3,
        excitation_width=2.0,
        separation=8.0,
        total_time=20.0,
        dt=0.02,
        seed=42
    )
    
    print("\nTest complete.")
