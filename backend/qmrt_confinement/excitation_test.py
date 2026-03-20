"""
QMRT Quark Confinement Analogies - Step 1: Localized Excitation Confinement

FOUNDATIONAL TEST: Can the QMRT medium support particle-like solitons?

Goal: Test if localized wave packets remain self-bound in the substrate.

Initial condition:
    ψ(x,t=0) = A·exp(-(x-x₀)²/σ²)·exp(iω₀t)
    
Evolution (effective):
    ∂ₜψ = D∇²ψ - ∂V(ψ)/∂ψ - γ∇S
    
Observations:
    1. Does amplitude disperse?
    2. Does it lock into domain boundary?
    3. Does energy stabilize?
    
If YES to stability → PROTO-QUARK ANALOGUE confirmed.

Physical context:
    - Half-entropy plateau (λ_L ≈ 0.75) suggests medium can support long-lived quasi-particles
    - Full entropy maximization normally destroys localization
    - This environment is where vortices, skyrmions, solitons, flux tubes naturally form
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.ndimage import center_of_mass, label
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters


@dataclass
class ExcitationState:
    """State of a localized excitation at a point in time"""
    time: float
    
    # Position tracking
    center_of_mass: Tuple[float, float, float]
    position_drift: float  # Distance from initial position
    
    # Shape metrics
    amplitude_peak: float
    amplitude_mean: float
    width_sigma: float      # Effective width (RMS)
    aspect_ratio: float     # Measure of shape preservation
    
    # Energy metrics
    excitation_energy: float
    kinetic_energy: float
    potential_energy: float
    
    # Stability metrics
    dispersion_ratio: float  # width(t) / width(0)
    amplitude_ratio: float   # A(t) / A(0)
    energy_ratio: float      # E(t) / E(0)
    
    # Confinement indicators
    within_domain: bool      # Is excitation still within its frequency domain?
    domain_locked: bool      # Has it locked to a domain boundary?
    
    def to_dict(self) -> Dict:
        return {
            'time': float(self.time),
            'position': {
                'center_of_mass': [float(x) for x in self.center_of_mass],
                'drift': float(self.position_drift)
            },
            'shape': {
                'amplitude_peak': float(self.amplitude_peak),
                'amplitude_mean': float(self.amplitude_mean),
                'width_sigma': float(self.width_sigma),
                'aspect_ratio': float(self.aspect_ratio)
            },
            'energy': {
                'excitation': float(self.excitation_energy),
                'kinetic': float(self.kinetic_energy),
                'potential': float(self.potential_energy)
            },
            'stability': {
                'dispersion_ratio': float(self.dispersion_ratio),
                'amplitude_ratio': float(self.amplitude_ratio),
                'energy_ratio': float(self.energy_ratio)
            },
            'confinement': {
                'within_domain': self.within_domain,
                'domain_locked': self.domain_locked
            }
        }


@dataclass
class LocalizedExcitationResult:
    """Result from localized excitation confinement test"""
    
    # Time series
    states: List[ExcitationState] = field(default_factory=list)
    
    # Initial conditions
    initial_amplitude: float = 0.0
    initial_width: float = 0.0
    initial_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    excitation_type: str = ""  # 'gaussian', 'sech', etc.
    
    # Final stability assessment
    remained_localized: bool = False
    amplitude_preserved: bool = False  # A(t)/A(0) > 0.5
    width_stable: bool = False         # width(t)/width(0) < 2.0
    energy_conserved: bool = False     # |E(t)-E(0)|/E(0) < 0.1
    
    # Confinement assessment
    confined_to_domain: bool = False
    domain_boundary_locked: bool = False
    
    # Soliton quality metrics
    soliton_score: float = 0.0         # 0-1, overall soliton quality
    lifetime_estimate: float = 0.0      # Estimated lifetime
    
    # Metadata
    grid_size: int = 0
    total_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'time_series': [s.to_dict() for s in self.states],
            'initial_conditions': {
                'amplitude': float(self.initial_amplitude),
                'width': float(self.initial_width),
                'position': [float(x) for x in self.initial_position],
                'type': self.excitation_type
            },
            'stability_assessment': {
                'remained_localized': self.remained_localized,
                'amplitude_preserved': self.amplitude_preserved,
                'width_stable': self.width_stable,
                'energy_conserved': self.energy_conserved
            },
            'confinement_assessment': {
                'confined_to_domain': self.confined_to_domain,
                'domain_boundary_locked': self.domain_boundary_locked
            },
            'soliton_metrics': {
                'soliton_score': float(self.soliton_score),
                'lifetime_estimate': float(self.lifetime_estimate)
            },
            'metadata': {
                'grid_size': int(self.grid_size),
                'total_time': float(self.total_time)
            },
            'verdict': self._get_verdict()
        }
    
    def _get_verdict(self) -> str:
        if self.soliton_score > 0.7:
            return f"PROTO-QUARK CONFIRMED: Localized excitation remains self-bound (score={self.soliton_score:.2f}). Medium supports particle-like solitons."
        elif self.soliton_score > 0.4:
            return f"QUASI-STABLE: Partial localization maintained (score={self.soliton_score:.2f}). Excitation disperses slowly."
        elif self.domain_boundary_locked:
            return f"BOUNDARY-LOCKED: Excitation locked to domain wall. Different confinement mechanism."
        else:
            return f"DISPERSIVE: Excitation disperses in the medium (score={self.soliton_score:.2f}). No soliton support."


def create_localized_excitation(
    engine: QMRTFrequencyEngine,
    position: Tuple[float, float, float],
    amplitude: float,
    width: float,
    excitation_type: str = 'gaussian',
    momentum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> np.ndarray:
    """
    Create a localized excitation (wave packet) in the omega field.
    
    ψ(x) = A·exp(-(x-x₀)²/(2σ²)) for Gaussian
    
    Returns: mask of excitation region for tracking
    """
    n = engine.grid_size
    p = engine.params
    
    x0, y0, z0 = position
    
    # Create coordinate grids
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Distance from center
    R_sq = (X - x0)**2 + (Y - y0)**2 + (Z - z0)**2
    
    if excitation_type == 'gaussian':
        # Gaussian wave packet
        profile = amplitude * np.exp(-R_sq / (2 * width**2))
    elif excitation_type == 'sech':
        # Sech profile (more soliton-like)
        R = np.sqrt(R_sq + 0.01)
        profile = amplitude / np.cosh(R / width)
    elif excitation_type == 'tophat':
        # Top-hat for testing
        profile = np.where(R_sq < width**2, amplitude, 0.0)
    else:
        profile = amplitude * np.exp(-R_sq / (2 * width**2))
    
    # Add to omega field (on top of existing substrate)
    engine.omega = engine.omega + profile
    
    # Add momentum if specified
    kx, ky, kz = momentum
    if abs(kx) + abs(ky) + abs(kz) > 0.01:
        phase = kx * (X - x0) + ky * (Y - y0) + kz * (Z - z0)
        engine.pi_omega = engine.pi_omega + profile * np.sin(phase) * 0.1
    
    # Create mask for tracking
    mask = profile > 0.1 * amplitude
    
    # Recalculate initial energy
    engine.initial_energy = engine.compute_total_energy()
    
    return mask


def measure_excitation_state(
    engine: QMRTFrequencyEngine,
    initial_position: Tuple[float, float, float],
    initial_amplitude: float,
    initial_width: float,
    initial_energy: float
) -> ExcitationState:
    """
    Measure the current state of a localized excitation.
    """
    omega = engine.omega
    p = engine.params
    n = engine.grid_size
    
    # Find the excitation (excess omega above background)
    # Background is approximately ±ω_0 in basins
    background = np.where(omega > 0, p.omega_0, -p.omega_0)
    excess = omega - background
    
    # Threshold for excitation
    threshold = 0.1 * initial_amplitude
    excitation_mask = np.abs(excess) > threshold
    
    if np.sum(excitation_mask) < 10:
        # Excitation dispersed
        return ExcitationState(
            time=engine.time,
            center_of_mass=initial_position,
            position_drift=float('inf'),
            amplitude_peak=0.0,
            amplitude_mean=0.0,
            width_sigma=float('inf'),
            aspect_ratio=0.0,
            excitation_energy=0.0,
            kinetic_energy=0.0,
            potential_energy=0.0,
            dispersion_ratio=float('inf'),
            amplitude_ratio=0.0,
            energy_ratio=0.0,
            within_domain=False,
            domain_locked=False
        )
    
    # Center of mass
    excitation_field = np.abs(excess) * excitation_mask
    total_weight = np.sum(excitation_field)
    
    x = np.arange(n)
    y = np.arange(n)
    z = np.arange(n)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    if total_weight > 0:
        com_x = np.sum(X * excitation_field) / total_weight
        com_y = np.sum(Y * excitation_field) / total_weight
        com_z = np.sum(Z * excitation_field) / total_weight
        com = (float(com_x), float(com_y), float(com_z))
    else:
        com = initial_position
    
    # Position drift
    drift = np.sqrt((com[0] - initial_position[0])**2 + 
                    (com[1] - initial_position[1])**2 + 
                    (com[2] - initial_position[2])**2)
    
    # Amplitude metrics
    amplitude_peak = float(np.max(np.abs(excess)))
    amplitude_mean = float(np.mean(np.abs(excess[excitation_mask])))
    
    # Width (RMS)
    R_sq = (X - com[0])**2 + (Y - com[1])**2 + (Z - com[2])**2
    width_sq = np.sum(R_sq * excitation_field) / (total_weight + 0.001)
    width_sigma = float(np.sqrt(width_sq))
    
    # Aspect ratio (measure of spherical symmetry)
    # Compute moments in each direction
    mx = np.sum((X - com[0])**2 * excitation_field) / (total_weight + 0.001)
    my = np.sum((Y - com[1])**2 * excitation_field) / (total_weight + 0.001)
    mz = np.sum((Z - com[2])**2 * excitation_field) / (total_weight + 0.001)
    
    max_moment = max(mx, my, mz)
    min_moment = min(mx, my, mz) + 0.001
    aspect_ratio = float(min_moment / max_moment)  # 1.0 = spherical
    
    # Energy metrics
    total_energy = engine.compute_total_energy()
    
    # Excitation energy (energy in excess field region)
    # Simplified: proportional to |excess|² in excitation region
    excitation_energy = float(np.sum(excess**2 * excitation_mask))
    
    # Kinetic energy in excitation region
    kinetic_energy = float(0.5 * np.sum(engine.pi_omega**2 * excitation_mask))
    
    # Potential energy in excitation region
    potential_energy = float(np.sum(p.a_omega * (omega**2 - p.omega_0**2)**2 * excitation_mask))
    
    # Stability ratios
    dispersion_ratio = width_sigma / initial_width if initial_width > 0 else float('inf')
    amplitude_ratio = amplitude_peak / initial_amplitude if initial_amplitude > 0 else 0.0
    energy_ratio = total_energy / initial_energy if initial_energy > 0 else 0.0
    
    # Confinement checks
    # Within domain: is excitation still in a frequency basin?
    mean_omega_at_excitation = np.mean(omega[excitation_mask])
    within_domain = abs(mean_omega_at_excitation) > 0.3 * p.omega_0
    
    # Domain locked: is excitation at a domain boundary?
    # Gradient is high at boundaries
    grad_omega = np.sqrt(
        np.gradient(omega, axis=0)**2 + 
        np.gradient(omega, axis=1)**2 + 
        np.gradient(omega, axis=2)**2
    )
    mean_grad_at_excitation = np.mean(grad_omega[excitation_mask])
    domain_locked = mean_grad_at_excitation > 0.5 * np.mean(grad_omega)
    
    return ExcitationState(
        time=engine.time,
        center_of_mass=com,
        position_drift=drift,
        amplitude_peak=amplitude_peak,
        amplitude_mean=amplitude_mean,
        width_sigma=width_sigma,
        aspect_ratio=aspect_ratio,
        excitation_energy=excitation_energy,
        kinetic_energy=kinetic_energy,
        potential_energy=potential_energy,
        dispersion_ratio=dispersion_ratio,
        amplitude_ratio=amplitude_ratio,
        energy_ratio=energy_ratio,
        within_domain=within_domain,
        domain_locked=domain_locked
    )


def run_localized_excitation_test(
    grid_size: int = 20,
    total_time: float = 50.0,
    dt: float = 0.02,
    excitation_amplitude: float = 0.5,  # Relative to ω_0
    excitation_width: float = 3.0,       # Grid units
    excitation_type: str = 'gaussian',
    seed: int = 42
) -> LocalizedExcitationResult:
    """
    Run localized excitation confinement test.
    
    Tests if the QMRT medium supports particle-like solitons.
    
    Steps:
    1. Initialize substrate with frequency domains
    2. Create localized excitation on top
    3. Evolve and track:
       - Does amplitude disperse?
       - Does width grow?
       - Does energy remain localized?
       - Does it lock to domain boundary?
    """
    print("="*60)
    print("LOCALIZED EXCITATION CONFINEMENT TEST")
    print("="*60)
    print(f"Grid: {grid_size}³, Time: {total_time}s")
    print(f"Excitation: {excitation_type}, A={excitation_amplitude}ω₀, σ={excitation_width}")
    print("-"*60)
    
    # Initialize substrate
    print("\n[1/4] Initializing substrate...")
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    p = engine.params
    
    # Let substrate stabilize
    for _ in range(200):
        engine.evolve_timestep(dt)
    
    # Find a location in a high-frequency domain for excitation
    high_domain_mask = engine.omega > 0.5 * p.omega_0
    if np.sum(high_domain_mask) > 0:
        # Find center of largest high-frequency region
        labeled, num_features = label(high_domain_mask)
        if num_features > 0:
            sizes = [(labeled == i).sum() for i in range(1, num_features + 1)]
            largest_label = sizes.index(max(sizes)) + 1
            com = center_of_mass(high_domain_mask, labeled, largest_label)
            position = (float(com[0]), float(com[1]), float(com[2]))
        else:
            position = (grid_size // 2, grid_size // 2, grid_size // 2)
    else:
        position = (grid_size // 2, grid_size // 2, grid_size // 2)
    
    print(f"    Substrate stabilized. Placing excitation at {position}")
    
    # Record pre-excitation state
    energy_before = engine.compute_total_energy()
    
    # Create localized excitation
    print("[2/4] Creating localized excitation...")
    actual_amplitude = excitation_amplitude * p.omega_0
    mask = create_localized_excitation(
        engine, position, actual_amplitude, excitation_width, excitation_type
    )
    
    initial_position = position
    initial_amplitude = actual_amplitude
    initial_width = excitation_width
    initial_energy = engine.compute_total_energy()
    excitation_energy = initial_energy - energy_before
    
    print(f"    Created {excitation_type} excitation:")
    print(f"    Amplitude: {actual_amplitude:.4f}")
    print(f"    Width: {excitation_width:.1f}")
    print(f"    Energy added: {excitation_energy:.4f}")
    
    # Evolve and track
    print("[3/4] Evolving system...")
    result = LocalizedExcitationResult(
        initial_amplitude=initial_amplitude,
        initial_width=initial_width,
        initial_position=initial_position,
        excitation_type=excitation_type,
        grid_size=grid_size,
        total_time=total_time
    )
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            state = measure_excitation_state(
                engine, initial_position, initial_amplitude, 
                initial_width, initial_energy
            )
            result.states.append(state)
            
            if step % (sample_interval * 10) == 0:
                print(f"    t={state.time:.1f}s: A/A₀={state.amplitude_ratio:.3f}, "
                      f"σ/σ₀={state.dispersion_ratio:.3f}, drift={state.position_drift:.2f}")
    
    # Analysis
    print("\n[4/4] Analyzing results...")
    
    if len(result.states) < 2:
        print("    Insufficient data for analysis")
        return result
    
    # Get final state metrics
    final_states = result.states[-5:]  # Last few states
    
    final_amplitude_ratio = np.mean([s.amplitude_ratio for s in final_states])
    final_dispersion_ratio = np.mean([s.dispersion_ratio for s in final_states])
    final_energy_ratio = np.mean([s.energy_ratio for s in final_states])
    final_within_domain = sum([s.within_domain for s in final_states]) > len(final_states) / 2
    final_domain_locked = sum([s.domain_locked for s in final_states]) > len(final_states) / 2
    
    # Stability assessment
    result.amplitude_preserved = final_amplitude_ratio > 0.5
    result.width_stable = final_dispersion_ratio < 2.0
    result.energy_conserved = abs(1.0 - final_energy_ratio) < 0.1
    
    result.remained_localized = result.amplitude_preserved and result.width_stable
    result.confined_to_domain = final_within_domain
    result.domain_boundary_locked = final_domain_locked
    
    # Soliton score (0-1)
    score = 0.0
    if result.amplitude_preserved:
        score += 0.3 * final_amplitude_ratio
    if result.width_stable:
        score += 0.3 * (1.0 / final_dispersion_ratio)
    if result.energy_conserved:
        score += 0.2
    if result.confined_to_domain:
        score += 0.2
    
    result.soliton_score = min(1.0, score)
    
    # Lifetime estimate (time until amplitude drops to 1/e)
    amplitude_ratios = [s.amplitude_ratio for s in result.states]
    times = [s.time for s in result.states]
    
    # Find when amplitude drops below 1/e
    threshold = 1.0 / np.e
    lifetime_idx = len(amplitude_ratios)
    for i, ar in enumerate(amplitude_ratios):
        if ar < threshold:
            lifetime_idx = i
            break
    
    if lifetime_idx < len(times):
        result.lifetime_estimate = times[lifetime_idx]
    else:
        result.lifetime_estimate = times[-1]  # Survived entire simulation
    
    # Summary
    print(f"\n{'='*60}")
    print("LOCALIZED EXCITATION RESULTS")
    print(f"{'='*60}")
    print(f"\n  Stability:")
    print(f"    Amplitude preserved: {'✅' if result.amplitude_preserved else '❌'} ({final_amplitude_ratio:.3f})")
    print(f"    Width stable:        {'✅' if result.width_stable else '❌'} ({final_dispersion_ratio:.3f}x)")
    print(f"    Energy conserved:    {'✅' if result.energy_conserved else '❌'}")
    print(f"\n  Confinement:")
    print(f"    Within domain:       {'✅' if result.confined_to_domain else '❌'}")
    print(f"    Boundary locked:     {'✅' if result.domain_boundary_locked else '❌'}")
    print(f"\n  Soliton metrics:")
    print(f"    Score: {result.soliton_score:.3f}")
    print(f"    Lifetime: {result.lifetime_estimate:.1f}s")
    print(f"\n  VERDICT: {result._get_verdict()}")
    print(f"{'='*60}\n")
    
    return result


def test_multiple_excitation_types(
    grid_size: int = 16,
    total_time: float = 30.0,
    dt: float = 0.02,
    seed: int = 42
) -> Dict:
    """
    Test multiple excitation types to find which forms stable solitons.
    """
    print("="*60)
    print("MULTI-TYPE EXCITATION TEST")
    print("="*60)
    
    excitation_types = ['gaussian', 'sech']
    amplitudes = [0.3, 0.5, 0.8]
    
    results = []
    
    for etype in excitation_types:
        for amp in amplitudes:
            print(f"\nTesting: {etype}, amplitude={amp}ω₀")
            
            result = run_localized_excitation_test(
                grid_size=grid_size,
                total_time=total_time,
                dt=dt,
                excitation_amplitude=amp,
                excitation_width=3.0,
                excitation_type=etype,
                seed=seed
            )
            
            results.append({
                'type': etype,
                'amplitude': amp,
                'soliton_score': result.soliton_score,
                'lifetime': result.lifetime_estimate,
                'amplitude_preserved': result.amplitude_preserved,
                'width_stable': result.width_stable,
                'confined': result.confined_to_domain
            })
    
    # Find best
    best = max(results, key=lambda x: x['soliton_score'])
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for r in results:
        status = "✅" if r['soliton_score'] > 0.5 else "❌"
        print(f"  {status} {r['type']}, A={r['amplitude']}: score={r['soliton_score']:.3f}, τ={r['lifetime']:.1f}s")
    
    print(f"\n  Best: {best['type']} at A={best['amplitude']}ω₀ (score={best['soliton_score']:.3f})")
    
    return {
        'results': results,
        'best_configuration': best,
        'proto_quark_found': best['soliton_score'] > 0.5
    }


if __name__ == "__main__":
    result = run_localized_excitation_test(
        grid_size=16,
        total_time=30.0,
        dt=0.02,
        excitation_amplitude=0.5,
        excitation_width=3.0,
        excitation_type='gaussian',
        seed=42
    )
    
    print("\nFinal soliton score:", result.soliton_score)
