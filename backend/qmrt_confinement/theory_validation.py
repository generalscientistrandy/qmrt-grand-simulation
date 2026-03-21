"""
QMRT Confinement Theory Validation - Systematic Tests

Before claiming a "different confinement class", we need:

1. METASTABILITY LIFETIME SCALING
   - Lifetime vs grid size, timestep, perturbation, domain depth
   - Determines: truly stable or just long-lived metastable?

2. BINDING ENERGY LAW
   - E(n) for n = 1, 2, 3, 4 excitations
   - Energy per excitation scaling
   - Structural result, not screenshot observation

3. SHAPE DEPENDENCE
   - What controls binding: separation? interface area? geometry?
   - Tests "droplet coalescence" interpretation

4. TOPOLOGY CHECK
   - Conserved quantity: winding number, defect charge, etc.
   - Without this: call it "barrier-protected metastability"
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import curve_fit
import time

import sys
sys.path.insert(0, '/app/backend')

from qmrt_frequency_engine import QMRTFrequencyEngine, QMRTFrequencyParameters


# =============================================================================
# TEST 1: METASTABILITY LIFETIME SCALING
# =============================================================================

@dataclass
class LifetimeResult:
    """Result from lifetime measurement"""
    parameter_name: str
    parameter_values: List[float]
    lifetimes: List[float]  # Time until excitation decays to 50% amplitude
    decay_rates: List[float]  # Exponential decay rate if applicable
    scaling_exponent: float = 0.0  # τ ~ param^α
    truly_stable: bool = False  # No decay observed
    
    def to_dict(self) -> Dict:
        return {
            'parameter': self.parameter_name,
            'values': [float(v) for v in self.parameter_values],
            'lifetimes': [float(t) for t in self.lifetimes],
            'decay_rates': [float(r) for r in self.decay_rates],
            'scaling_exponent': float(self.scaling_exponent),
            'truly_stable': self.truly_stable
        }


def measure_excitation_lifetime(
    grid_size: int = 24,
    dt: float = 0.02,
    max_time: float = 100.0,
    excitation_amplitude: float = 0.3,
    perturbation_amplitude: float = 0.0,
    a_omega: float = 1.0,
    seed: int = 42
) -> Tuple[float, float, List[Tuple[float, float]]]:
    """
    Measure lifetime of a single isolated excitation.
    
    Returns: (lifetime, decay_rate, time_series[(t, amplitude_ratio)])
    
    Lifetime = time until amplitude drops to 50% of initial
    If never drops: lifetime = max_time (truly stable)
    """
    params = QMRTFrequencyParameters(a_omega=a_omega)
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    # Stabilize substrate
    for _ in range(100):
        engine.evolve_timestep(dt)
    
    # Store reference
    omega_ref = engine.omega.copy()
    
    # Create excitation at center
    n = grid_size
    center = n // 2
    x = np.arange(n)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
    width = 2.5
    
    initial_amp = excitation_amplitude * p.omega_0
    excitation = initial_amp * np.exp(-R_sq / (2 * width**2))
    engine.omega = engine.omega + excitation
    
    # Add perturbation if specified
    if perturbation_amplitude > 0:
        np.random.seed(seed + 1000)
        noise = perturbation_amplitude * p.omega_0 * np.random.randn(n, n, n)
        engine.omega = engine.omega + noise
    
    # Evolve and track
    time_series = []
    steps = int(max_time / dt)
    sample_interval = max(1, steps // 200)
    
    lifetime = max_time  # Default: stable
    half_life_found = False
    
    amplitudes = []
    times = []
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            t = engine.time
            
            # Measure current amplitude
            excess = engine.omega - omega_ref
            search_mask = R_sq < (width * 4)**2
            current_amp = float(np.max(np.abs(excess[search_mask])))
            amp_ratio = current_amp / initial_amp
            
            time_series.append((t, amp_ratio))
            amplitudes.append(amp_ratio)
            times.append(t)
            
            # Check for half-life
            if not half_life_found and amp_ratio < 0.5:
                lifetime = t
                half_life_found = True
    
    # Fit decay rate
    decay_rate = 0.0
    if len(amplitudes) > 10:
        try:
            # Fit exponential: A(t) = A0 * exp(-γt)
            log_amp = np.log(np.array(amplitudes) + 1e-10)
            times_arr = np.array(times)
            
            # Linear fit to log
            coeffs = np.polyfit(times_arr, log_amp, 1)
            decay_rate = -coeffs[0]  # γ = -slope
        except:
            decay_rate = 0.0
    
    return lifetime, decay_rate, time_series


def test_lifetime_vs_grid_size(
    grid_sizes: List[int] = [16, 20, 24, 28],
    max_time: float = 50.0,
    seed: int = 42
) -> LifetimeResult:
    """Test if lifetime scales with grid size (finite-size effect)"""
    print("\n" + "="*60)
    print("TEST 1a: LIFETIME vs GRID SIZE")
    print("="*60)
    
    lifetimes = []
    decay_rates = []
    
    for gs in grid_sizes:
        print(f"  Grid {gs}³...", end=" ", flush=True)
        τ, γ, _ = measure_excitation_lifetime(
            grid_size=gs, max_time=max_time, seed=seed
        )
        lifetimes.append(τ)
        decay_rates.append(γ)
        print(f"τ = {τ:.2f}s, γ = {γ:.6f}/s")
    
    # Fit scaling: τ ~ N^α
    try:
        log_N = np.log(grid_sizes)
        log_τ = np.log(lifetimes)
        if min(lifetimes) < max_time * 0.99:  # Some decay observed
            α = np.polyfit(log_N, log_τ, 1)[0]
        else:
            α = float('inf')  # Truly stable
    except:
        α = 0.0
    
    truly_stable = all(τ >= max_time * 0.99 for τ in lifetimes)
    
    result = LifetimeResult(
        parameter_name="grid_size",
        parameter_values=grid_sizes,
        lifetimes=lifetimes,
        decay_rates=decay_rates,
        scaling_exponent=α if α != float('inf') else 0.0,
        truly_stable=truly_stable
    )
    
    print(f"\n  Scaling: τ ~ N^{α:.2f}" if α != float('inf') else "\n  No decay observed")
    print(f"  Truly stable: {'YES' if truly_stable else 'NO'}")
    
    return result


def test_lifetime_vs_timestep(
    timesteps: List[float] = [0.04, 0.02, 0.01, 0.005],
    max_time: float = 50.0,
    seed: int = 42
) -> LifetimeResult:
    """Test if lifetime changes with timestep (numerical artifact check)"""
    print("\n" + "="*60)
    print("TEST 1b: LIFETIME vs TIMESTEP")
    print("="*60)
    
    lifetimes = []
    decay_rates = []
    
    for dt in timesteps:
        print(f"  dt = {dt}...", end=" ", flush=True)
        τ, γ, _ = measure_excitation_lifetime(
            grid_size=20, dt=dt, max_time=max_time, seed=seed
        )
        lifetimes.append(τ)
        decay_rates.append(γ)
        print(f"τ = {τ:.2f}s, γ = {γ:.6f}/s")
    
    # Check convergence
    converged = abs(lifetimes[-1] - lifetimes[-2]) / (lifetimes[-1] + 1e-10) < 0.1
    truly_stable = all(τ >= max_time * 0.99 for τ in lifetimes)
    
    result = LifetimeResult(
        parameter_name="timestep",
        parameter_values=timesteps,
        lifetimes=lifetimes,
        decay_rates=decay_rates,
        scaling_exponent=0.0,
        truly_stable=truly_stable
    )
    
    print(f"\n  Converged with dt: {'YES' if converged else 'NO'}")
    print(f"  Truly stable: {'YES' if truly_stable else 'NO'}")
    
    return result


def test_lifetime_vs_perturbation(
    perturbations: List[float] = [0.0, 0.01, 0.05, 0.1, 0.2],
    max_time: float = 50.0,
    seed: int = 42
) -> LifetimeResult:
    """Test stability under perturbation (metastability test)"""
    print("\n" + "="*60)
    print("TEST 1c: LIFETIME vs PERTURBATION AMPLITUDE")
    print("="*60)
    
    lifetimes = []
    decay_rates = []
    
    for pert in perturbations:
        print(f"  Perturbation = {pert}ω₀...", end=" ", flush=True)
        τ, γ, _ = measure_excitation_lifetime(
            grid_size=20, perturbation_amplitude=pert, max_time=max_time, seed=seed
        )
        lifetimes.append(τ)
        decay_rates.append(γ)
        print(f"τ = {τ:.2f}s, γ = {γ:.6f}/s")
    
    # Perturbation sensitivity
    unperturbed_τ = lifetimes[0]
    sensitive = any(τ < unperturbed_τ * 0.5 for τ in lifetimes[1:])
    
    result = LifetimeResult(
        parameter_name="perturbation",
        parameter_values=perturbations,
        lifetimes=lifetimes,
        decay_rates=decay_rates,
        scaling_exponent=0.0,
        truly_stable=not sensitive
    )
    
    print(f"\n  Perturbation sensitive: {'YES' if sensitive else 'NO'}")
    
    return result


def test_lifetime_vs_domain_depth(
    a_omega_values: List[float] = [0.5, 1.0, 2.0, 4.0],
    max_time: float = 50.0,
    seed: int = 42
) -> LifetimeResult:
    """Test lifetime vs potential depth (barrier height)"""
    print("\n" + "="*60)
    print("TEST 1d: LIFETIME vs DOMAIN DEPTH (a_ω)")
    print("="*60)
    
    lifetimes = []
    decay_rates = []
    
    for a_omega in a_omega_values:
        print(f"  a_ω = {a_omega}...", end=" ", flush=True)
        τ, γ, _ = measure_excitation_lifetime(
            grid_size=20, a_omega=a_omega, max_time=max_time, seed=seed
        )
        lifetimes.append(τ)
        decay_rates.append(γ)
        print(f"τ = {τ:.2f}s, γ = {γ:.6f}/s")
    
    # Fit scaling: τ ~ a_ω^α
    try:
        log_a = np.log(a_omega_values)
        log_τ = np.log([max(τ, 0.1) for τ in lifetimes])
        α = np.polyfit(log_a, log_τ, 1)[0]
    except:
        α = 0.0
    
    result = LifetimeResult(
        parameter_name="a_omega",
        parameter_values=a_omega_values,
        lifetimes=lifetimes,
        decay_rates=decay_rates,
        scaling_exponent=α,
        truly_stable=all(τ >= max_time * 0.99 for τ in lifetimes)
    )
    
    print(f"\n  Scaling: τ ~ a_ω^{α:.2f}")
    
    return result


# =============================================================================
# TEST 2: BINDING ENERGY LAW
# =============================================================================

@dataclass
class BindingEnergyResult:
    """Result from binding energy measurement"""
    n_excitations: List[int]
    total_energies: List[float]
    energies_per_excitation: List[float]
    binding_energies: List[float]  # E(n) - n*E(1)
    binding_per_excitation: List[float]
    
    # Scaling analysis
    binding_law: str = ""  # e.g., "E_bind ~ n^α"
    scaling_exponent: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'n_excitations': self.n_excitations,
            'total_energies': [float(e) for e in self.total_energies],
            'energies_per_excitation': [float(e) for e in self.energies_per_excitation],
            'binding_energies': [float(e) for e in self.binding_energies],
            'binding_per_excitation': [float(e) for e in self.binding_per_excitation],
            'binding_law': self.binding_law,
            'scaling_exponent': float(self.scaling_exponent)
        }


def measure_n_excitation_energy(
    n: int,
    grid_size: int = 24,
    separation: float = 6.0,
    amplitude: float = 0.3,
    equilibration_time: float = 10.0,
    dt: float = 0.02,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Measure total energy and domain wall energy for n excitations
    arranged in optimal configuration.
    
    n=1: single at center
    n=2: pair along x-axis
    n=3: equilateral triangle
    n=4: tetrahedron (or square for 2D comparison)
    
    Returns: (E_total - E_baseline, E_wall)
    """
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    # Stabilize
    for _ in range(100):
        engine.evolve_timestep(dt)
    
    E_baseline = engine.compute_total_energy()
    wall_baseline = measure_wall_energy(engine, p)
    
    # Generate positions
    center = grid_size // 2
    positions = []
    
    if n == 1:
        positions = [(center, center, center)]
    elif n == 2:
        positions = [
            (center - separation/2, center, center),
            (center + separation/2, center, center)
        ]
    elif n == 3:
        # Equilateral triangle
        r = separation / np.sqrt(3)
        positions = [
            (center + r, center, center),
            (center - r/2, center + r * np.sqrt(3)/2, center),
            (center - r/2, center - r * np.sqrt(3)/2, center)
        ]
    elif n == 4:
        # Tetrahedron
        r = separation / np.sqrt(2)
        positions = [
            (center + r, center, center),
            (center - r/3, center + r * np.sqrt(8/9), center),
            (center - r/3, center - r * np.sqrt(2/9), center + r * np.sqrt(2/3)),
            (center - r/3, center - r * np.sqrt(2/9), center - r * np.sqrt(2/3))
        ]
    else:
        # General: arrange in sphere
        for i in range(n):
            phi = 2 * np.pi * i / n
            positions.append((
                center + separation/2 * np.cos(phi),
                center + separation/2 * np.sin(phi),
                center
            ))
    
    # Create excitations
    n_grid = grid_size
    x = np.arange(n_grid)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    width = 2.0
    amp = amplitude * p.omega_0
    
    for pos in positions:
        R_sq = (X - pos[0])**2 + (Y - pos[1])**2 + (Z - pos[2])**2
        profile = amp * np.exp(-R_sq / (2 * width**2))
        engine.omega += profile
    
    # Equilibrate
    eq_steps = int(equilibration_time / dt)
    for _ in range(eq_steps):
        engine.evolve_timestep(dt)
    
    E_total = engine.compute_total_energy()
    E_wall = measure_wall_energy(engine, p)
    
    return E_total - E_baseline, E_wall - wall_baseline


def measure_wall_energy(engine, params):
    """Measure gradient (domain wall) energy"""
    grad_omega_sq = (
        np.gradient(engine.omega, axis=0)**2 +
        np.gradient(engine.omega, axis=1)**2 +
        np.gradient(engine.omega, axis=2)**2
    )
    return float(np.sum(0.5 * params.K_omega * grad_omega_sq) * engine.dx**3)


def test_binding_energy_law(
    n_values: List[int] = [1, 2, 3, 4],
    grid_size: int = 28,
    separation: float = 7.0,
    seed: int = 42
) -> BindingEnergyResult:
    """
    Measure binding energy for 1, 2, 3, 4 excitations.
    
    Key question: Does triplet minimize energy more strongly than pair?
    """
    print("\n" + "="*60)
    print("TEST 2: BINDING ENERGY LAW")
    print("="*60)
    print(f"Grid: {grid_size}³, Separation: {separation}")
    print()
    
    total_energies = []
    wall_energies = []
    
    for n in n_values:
        print(f"  n = {n} excitations...", end=" ", flush=True)
        E_total, E_wall = measure_n_excitation_energy(
            n=n, grid_size=grid_size, separation=separation, seed=seed
        )
        total_energies.append(E_total)
        wall_energies.append(E_wall)
        print(f"ΔE = {E_total:.4f}, ΔE_wall = {E_wall:.4f}")
    
    # Compute derived quantities
    E_1 = total_energies[0]  # Single excitation energy
    
    energies_per_exc = [E / n for E, n in zip(total_energies, n_values)]
    binding_energies = [E - n * E_1 for E, n in zip(total_energies, n_values)]
    binding_per_exc = [B / n for B, n in zip(binding_energies, n_values)]
    
    # Summary table
    print("\n" + "-"*60)
    print(f"{'n':>3} | {'E_total':>12} | {'E/n':>12} | {'E_bind':>12} | {'E_bind/n':>12}")
    print("-"*60)
    for i, n in enumerate(n_values):
        print(f"{n:>3} | {total_energies[i]:>12.4f} | {energies_per_exc[i]:>12.4f} | "
              f"{binding_energies[i]:>12.4f} | {binding_per_exc[i]:>12.4f}")
    print("-"*60)
    
    # Fit binding law: E_bind ~ n^α or linear
    try:
        # For n >= 2, fit binding energy
        valid_n = [n for n in n_values if n >= 2]
        valid_bind = [binding_energies[i] for i, n in enumerate(n_values) if n >= 2]
        
        if len(valid_n) >= 2 and all(b != 0 for b in valid_bind):
            log_n = np.log(valid_n)
            log_bind = np.log(np.abs(valid_bind))
            α = np.polyfit(log_n, log_bind, 1)[0]
            binding_law = f"E_bind ~ n^{α:.2f}"
        else:
            α = 0.0
            binding_law = "insufficient data"
    except:
        α = 0.0
        binding_law = "fit failed"
    
    result = BindingEnergyResult(
        n_excitations=n_values,
        total_energies=total_energies,
        energies_per_excitation=energies_per_exc,
        binding_energies=binding_energies,
        binding_per_excitation=binding_per_exc,
        binding_law=binding_law,
        scaling_exponent=α
    )
    
    print(f"\nBinding law: {binding_law}")
    
    # Key comparison
    if len(n_values) >= 3:
        pair_bind_per = binding_per_exc[1] if n_values[1] == 2 else 0
        trip_bind_per = binding_per_exc[2] if n_values[2] == 3 else 0
        
        print(f"\nPair binding/excitation:   {pair_bind_per:.6f}")
        print(f"Triplet binding/excitation: {trip_bind_per:.6f}")
        
        if trip_bind_per < pair_bind_per:
            print("✅ Triplet has STRONGER binding per excitation")
        else:
            print("❌ Triplet does NOT have stronger binding")
    
    return result


# =============================================================================
# TEST 3: SHAPE DEPENDENCE
# =============================================================================

@dataclass
class ShapeDependenceResult:
    """Result from shape dependence test"""
    configurations: List[str]
    separations: List[float]
    interface_areas: List[float]  # Estimated interface area
    binding_energies: List[float]
    
    # What controls binding?
    correlation_separation: float = 0.0
    correlation_area: float = 0.0
    dominant_factor: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'configurations': self.configurations,
            'separations': [float(s) for s in self.separations],
            'interface_areas': [float(a) for a in self.interface_areas],
            'binding_energies': [float(e) for e in self.binding_energies],
            'correlations': {
                'separation': float(self.correlation_separation),
                'area': float(self.correlation_area)
            },
            'dominant_factor': self.dominant_factor
        }


def test_shape_dependence(
    grid_size: int = 28,
    seed: int = 42
) -> ShapeDependenceResult:
    """
    Test what controls binding: separation, interface area, or geometry?
    
    Configurations for 3 excitations:
    - Equilateral triangle (compact)
    - Isoceles triangle (stretched)
    - Line (maximum separation)
    - L-shape
    """
    print("\n" + "="*60)
    print("TEST 3: SHAPE DEPENDENCE")
    print("="*60)
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    for _ in range(100):
        engine.evolve_timestep(0.02)
    
    E_baseline = engine.compute_total_energy()
    center = grid_size // 2
    width = 2.0
    amp = 0.3 * p.omega_0
    sep = 8.0
    
    configurations = []
    separations = []  # Average pair distance
    interface_areas = []  # Estimated
    binding_energies = []
    
    # Define configurations
    config_defs = {
        'equilateral': [
            (center + sep/np.sqrt(3), center, center),
            (center - sep/(2*np.sqrt(3)), center + sep/2, center),
            (center - sep/(2*np.sqrt(3)), center - sep/2, center)
        ],
        'isoceles_stretch': [
            (center, center + sep, center),
            (center - sep/2, center - sep/2, center),
            (center + sep/2, center - sep/2, center)
        ],
        'line': [
            (center - sep, center, center),
            (center, center, center),
            (center + sep, center, center)
        ],
        'L_shape': [
            (center, center, center),
            (center + sep, center, center),
            (center, center + sep, center)
        ],
        'tight_cluster': [
            (center, center, center),
            (center + sep/2, center, center),
            (center + sep/4, center + sep/2 * np.sqrt(3)/2, center)
        ]
    }
    
    # First measure E(1)
    E_1, _ = measure_n_excitation_energy(1, grid_size, sep, seed=seed)
    
    for name, positions in config_defs.items():
        print(f"  {name}...", end=" ", flush=True)
        
        # Fresh engine
        eng = QMRTFrequencyEngine(grid_size=grid_size)
        eng.initialize_frequency_domains(amplitude=0.02, seed=seed)
        for _ in range(100):
            eng.evolve_timestep(0.02)
        
        E_base = eng.compute_total_energy()
        
        # Create excitations
        n = grid_size
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        
        for pos in positions:
            R_sq = (X - pos[0])**2 + (Y - pos[1])**2 + (Z - pos[2])**2
            profile = amp * np.exp(-R_sq / (2 * width**2))
            eng.omega += profile
        
        # Equilibrate
        for _ in range(500):
            eng.evolve_timestep(0.02)
        
        E_total = eng.compute_total_energy() - E_base
        E_bind = E_total - 3 * E_1
        
        # Calculate average separation
        pos_arr = np.array(positions)
        dists = []
        for i in range(3):
            for j in range(i+1, 3):
                dists.append(np.linalg.norm(pos_arr[i] - pos_arr[j]))
        avg_sep = np.mean(dists)
        
        # Estimate interface area (simplified: perimeter * width)
        perimeter = sum(dists)
        interface_area = perimeter * width * 2  # Tube-like interface
        
        configurations.append(name)
        separations.append(avg_sep)
        interface_areas.append(interface_area)
        binding_energies.append(E_bind)
        
        print(f"avg_sep={avg_sep:.2f}, area~{interface_area:.1f}, E_bind={E_bind:.4f}")
    
    # Correlation analysis
    if len(binding_energies) >= 3:
        corr_sep = np.corrcoef(separations, binding_energies)[0, 1]
        corr_area = np.corrcoef(interface_areas, binding_energies)[0, 1]
    else:
        corr_sep = corr_area = 0.0
    
    # Determine dominant factor
    if abs(corr_area) > abs(corr_sep) + 0.1:
        dominant = "interface_area"
    elif abs(corr_sep) > abs(corr_area) + 0.1:
        dominant = "separation"
    else:
        dominant = "mixed/geometry"
    
    result = ShapeDependenceResult(
        configurations=configurations,
        separations=separations,
        interface_areas=interface_areas,
        binding_energies=binding_energies,
        correlation_separation=corr_sep,
        correlation_area=corr_area,
        dominant_factor=dominant
    )
    
    print(f"\nCorrelation (binding vs separation): {corr_sep:.4f}")
    print(f"Correlation (binding vs interface area): {corr_area:.4f}")
    print(f"Dominant factor: {dominant.upper()}")
    
    if dominant == "interface_area":
        print("✅ DROPLET COALESCENCE interpretation supported")
    
    return result


# =============================================================================
# TEST 4: TOPOLOGY CHECK
# =============================================================================

@dataclass
class TopologyResult:
    """Result from topology check"""
    has_conserved_quantity: bool = False
    quantity_name: str = ""
    initial_value: float = 0.0
    final_value: float = 0.0
    conservation_error: float = 0.0
    
    # Defect analysis
    winding_number: Optional[float] = None
    defect_charge: Optional[float] = None
    
    interpretation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'has_conserved_quantity': self.has_conserved_quantity,
            'quantity_name': self.quantity_name,
            'initial_value': float(self.initial_value),
            'final_value': float(self.final_value),
            'conservation_error': float(self.conservation_error),
            'winding_number': float(self.winding_number) if self.winding_number else None,
            'defect_charge': float(self.defect_charge) if self.defect_charge else None,
            'interpretation': self.interpretation
        }


def compute_winding_number(omega: np.ndarray, omega_0: float) -> float:
    """
    Compute topological winding number for omega field.
    
    For a field with two minima ±ω₀, count domain wall crossings.
    Winding = (1/2π) ∮ ∇θ · dl where θ = arctan(ω/ω₀)
    
    Simplified: count zero crossings along closed path
    """
    n = omega.shape[0]
    center = n // 2
    radius = n // 3
    
    # Sample along circle in xy plane
    n_samples = 100
    angles = np.linspace(0, 2*np.pi, n_samples, endpoint=False)
    
    omega_samples = []
    for θ in angles:
        x = int(center + radius * np.cos(θ))
        y = int(center + radius * np.sin(θ))
        x = np.clip(x, 0, n-1)
        y = np.clip(y, 0, n-1)
        omega_samples.append(omega[x, y, center])
    
    # Count sign changes (zero crossings)
    signs = np.sign(omega_samples)
    crossings = np.sum(np.abs(np.diff(signs)) > 0)
    
    # Winding number = crossings / 2 (each domain wall crossed twice)
    winding = crossings / 2
    
    return winding


def compute_defect_charge(omega: np.ndarray, omega_0: float) -> float:
    """
    Compute topological defect charge.
    
    Q = ∫ (1/4π) ε_ijk ∂_i n · (∂_j n × ∂_k n) dV
    
    where n = ω/|ω| (unit field direction)
    
    Simplified: count distinct domain regions
    """
    # Binarize field
    binary = (omega > 0).astype(int)
    
    # Count distinct regions using connected components
    from scipy.ndimage import label
    labeled_pos, n_pos = label(omega > omega_0 * 0.5)
    labeled_neg, n_neg = label(omega < -omega_0 * 0.5)
    
    # Topological charge = difference in domain count
    charge = n_pos - n_neg
    
    return float(charge)


def test_topology(
    grid_size: int = 24,
    total_time: float = 30.0,
    dt: float = 0.02,
    seed: int = 42
) -> TopologyResult:
    """
    Test for topological protection by checking conserved quantities.
    
    Candidates:
    1. Winding number (domain wall count)
    2. Defect charge (domain asymmetry)
    3. Total "color" (if field has internal symmetry)
    """
    print("\n" + "="*60)
    print("TEST 4: TOPOLOGY CHECK")
    print("="*60)
    
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.02, seed=seed)
    p = engine.params
    
    # Stabilize
    for _ in range(100):
        engine.evolve_timestep(dt)
    
    # Add excitation
    center = grid_size // 2
    x = np.arange(grid_size)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R_sq = (X - center)**2 + (Y - center)**2 + (Z - center)**2
    amplitude = 0.3 * p.omega_0
    width = 2.5
    engine.omega += amplitude * np.exp(-R_sq / (2 * width**2))
    
    # Measure initial topology
    W_initial = compute_winding_number(engine.omega, p.omega_0)
    Q_initial = compute_defect_charge(engine.omega, p.omega_0)
    
    print(f"Initial winding number: {W_initial:.2f}")
    print(f"Initial defect charge: {Q_initial:.2f}")
    
    # Evolve
    steps = int(total_time / dt)
    winding_history = [W_initial]
    charge_history = [Q_initial]
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % (steps // 10) == 0:
            W = compute_winding_number(engine.omega, p.omega_0)
            Q = compute_defect_charge(engine.omega, p.omega_0)
            winding_history.append(W)
            charge_history.append(Q)
    
    W_final = winding_history[-1]
    Q_final = charge_history[-1]
    
    print(f"\nFinal winding number: {W_final:.2f}")
    print(f"Final defect charge: {Q_final:.2f}")
    
    # Check conservation
    W_error = abs(W_final - W_initial) / (abs(W_initial) + 1)
    Q_error = abs(Q_final - Q_initial) / (abs(Q_initial) + 1)
    
    W_conserved = W_error < 0.1
    Q_conserved = Q_error < 0.1
    
    print(f"\nWinding conservation error: {W_error:.2%}")
    print(f"Charge conservation error: {Q_error:.2%}")
    
    # Determine interpretation
    if W_conserved or Q_conserved:
        conserved = True
        if W_conserved:
            quantity = "winding_number"
            val_init, val_final = W_initial, W_final
            err = W_error
        else:
            quantity = "defect_charge"
            val_init, val_final = Q_initial, Q_final
            err = Q_error
        interpretation = f"TOPOLOGICALLY PROTECTED: {quantity} is conserved"
    else:
        conserved = False
        quantity = "none"
        val_init, val_final = 0, 0
        err = max(W_error, Q_error)
        interpretation = "BARRIER-PROTECTED METASTABILITY (no topological conservation)"
    
    result = TopologyResult(
        has_conserved_quantity=conserved,
        quantity_name=quantity,
        initial_value=val_init,
        final_value=val_final,
        conservation_error=err,
        winding_number=W_final,
        defect_charge=Q_final,
        interpretation=interpretation
    )
    
    print(f"\n{interpretation}")
    
    return result


# =============================================================================
# MAIN: Run All Validation Tests
# =============================================================================

def run_theory_validation(seed: int = 42) -> Dict:
    """
    Run all four systematic validation tests.
    """
    print("\n" + "="*70)
    print("QMRT CONFINEMENT THEORY VALIDATION SUITE")
    print("="*70)
    print("Four systematic tests before claiming 'different confinement class'")
    print("="*70)
    
    results = {}
    
    # Test 1: Metastability
    print("\n" + "#"*70)
    print("# TEST 1: METASTABILITY LIFETIME SCALING")
    print("#"*70)
    
    results['lifetime_grid'] = test_lifetime_vs_grid_size(
        grid_sizes=[16, 20, 24], max_time=40.0, seed=seed
    )
    
    results['lifetime_dt'] = test_lifetime_vs_timestep(
        timesteps=[0.04, 0.02, 0.01], max_time=40.0, seed=seed
    )
    
    results['lifetime_perturbation'] = test_lifetime_vs_perturbation(
        perturbations=[0.0, 0.05, 0.1], max_time=40.0, seed=seed
    )
    
    results['lifetime_depth'] = test_lifetime_vs_domain_depth(
        a_omega_values=[0.5, 1.0, 2.0], max_time=40.0, seed=seed
    )
    
    # Test 2: Binding energy
    print("\n" + "#"*70)
    print("# TEST 2: BINDING ENERGY LAW")
    print("#"*70)
    
    results['binding'] = test_binding_energy_law(
        n_values=[1, 2, 3, 4], grid_size=24, separation=7.0, seed=seed
    )
    
    # Test 3: Shape dependence
    print("\n" + "#"*70)
    print("# TEST 3: SHAPE DEPENDENCE")
    print("#"*70)
    
    results['shape'] = test_shape_dependence(grid_size=24, seed=seed)
    
    # Test 4: Topology
    print("\n" + "#"*70)
    print("# TEST 4: TOPOLOGY CHECK")
    print("#"*70)
    
    results['topology'] = test_topology(grid_size=24, total_time=25.0, seed=seed)
    
    # Final summary
    print("\n" + "="*70)
    print("THEORY VALIDATION SUMMARY")
    print("="*70)
    
    # Interpret results
    truly_stable = all([
        results['lifetime_grid'].truly_stable,
        results['lifetime_dt'].truly_stable,
        results['lifetime_perturbation'].truly_stable
    ])
    
    triplet_stronger = False
    if hasattr(results['binding'], 'binding_per_excitation'):
        bpe = results['binding'].binding_per_excitation
        if len(bpe) >= 3:
            triplet_stronger = bpe[2] < bpe[1]  # More negative = stronger
    
    droplet_supported = results['shape'].dominant_factor == "interface_area"
    topologically_protected = results['topology'].has_conserved_quantity
    
    print(f"""
1. METASTABILITY:
   Truly stable (no decay): {'YES' if truly_stable else 'NO - METASTABLE'}
   
2. BINDING ENERGY:
   Triplet stronger than pair: {'YES' if triplet_stronger else 'NO'}
   Binding law: {results['binding'].binding_law}
   
3. SHAPE DEPENDENCE:
   Dominant factor: {results['shape'].dominant_factor}
   Droplet coalescence supported: {'YES' if droplet_supported else 'NO'}
   
4. TOPOLOGY:
   Conserved quantity found: {'YES' if topologically_protected else 'NO'}
   Interpretation: {results['topology'].interpretation}

CORRECT TERMINOLOGY:
""")
    
    if topologically_protected:
        print("   Use: TOPOLOGICALLY PROTECTED")
    else:
        print("   Use: BARRIER-PROTECTED METASTABILITY")
    
    if truly_stable:
        print("   Use: STABLE EXCITATIONS")
    else:
        print("   Use: LONG-LIVED METASTABLE EXCITATIONS")
    
    if droplet_supported:
        print("   Use: SURFACE-ENERGY-DRIVEN BINDING (droplet coalescence)")
    else:
        print("   Use: GEOMETRY-DEPENDENT BINDING")
    
    print("="*70 + "\n")
    
    return {
        'results': {k: v.to_dict() for k, v in results.items()},
        'summary': {
            'truly_stable': truly_stable,
            'triplet_stronger': triplet_stronger,
            'droplet_coalescence_supported': droplet_supported,
            'topologically_protected': topologically_protected
        }
    }


if __name__ == "__main__":
    results = run_theory_validation(seed=42)
