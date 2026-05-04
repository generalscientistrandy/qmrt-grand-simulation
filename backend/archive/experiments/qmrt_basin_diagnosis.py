"""
QMRT Basin Decay Diagnostics

Systematic analysis of why frequency basins decay:

Hypotheses:
1. Gradient energy (K_omega |∇ω|²) smoothing out frequency differences
2. Phase-frequency coupling (g_omega_phi) pumping energy out
3. Density-frequency coupling (g_omega_rho) destabilizing
4. Numerical diffusion at high-k modes
5. Initial conditions not in equilibrium

Tests:
- Energy component tracking over time
- Isolated frequency dynamics (couplings = 0)
- Gradient-free test (K_omega = 0)
- Coupling strength sweep
"""
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from qmrt_frequency_engine import (
    QMRTFrequencyEngine,
    QMRTFrequencyParameters
)


@dataclass
class EnergyComponents:
    """Track individual energy components"""
    time: float
    KE_total: float
    KE_omega: float      # Frequency kinetic energy
    PE_band: float       # V_band(ω) = a_ω(ω² - ω₀²)²
    PE_gradient_omega: float  # K_ω|∇ω|²
    PE_coupling_omega_phi: float  # g_ωφ·ω·|∇φ|²
    PE_coupling_omega_rho: float  # g_ωρ·ω·(ρ-ρ₀)²
    basin_high: float
    basin_low: float
    omega_mean: float
    omega_std: float
    
    def to_dict(self) -> Dict:
        return {
            'time': float(self.time),
            'KE_total': float(self.KE_total),
            'KE_omega': float(self.KE_omega),
            'PE_band': float(self.PE_band),
            'PE_gradient_omega': float(self.PE_gradient_omega),
            'PE_coupling_omega_phi': float(self.PE_coupling_omega_phi),
            'PE_coupling_omega_rho': float(self.PE_coupling_omega_rho),
            'basin_high': float(self.basin_high),
            'basin_low': float(self.basin_low),
            'omega_mean': float(self.omega_mean),
            'omega_std': float(self.omega_std)
        }


def compute_energy_components(engine: QMRTFrequencyEngine) -> EnergyComponents:
    """Compute individual energy components for diagnosis"""
    p = engine.params
    
    # Kinetic energies
    KE_total = 0.5 * (
        np.sum(engine.pi_rho**2) / p.M_rho +
        np.sum(engine.pi_sigma**2) / p.M_sigma +
        np.sum(engine.pi_tau**2) / p.M_tau +
        np.sum(engine.pi_phi**2) / p.M_phi +
        np.sum(engine.pi_omega**2) / p.M_omega
    ) * engine.dx**3
    
    KE_omega = 0.5 * np.sum(engine.pi_omega**2) / p.M_omega * engine.dx**3
    
    # Band potential: V_band = a_ω(ω² - ω₀²)²
    omega_sq_minus = engine.omega**2 - p.omega_0**2
    PE_band = np.sum(p.a_omega * omega_sq_minus**2) * engine.dx**3
    
    # Gradient energy: K_ω|∇ω|²
    grad_omega_sq = engine._spectral_gradient_sq(engine.omega)
    PE_gradient_omega = 0.5 * np.sum(p.K_omega * grad_omega_sq) * engine.dx**3
    
    # Coupling: g_ωφ·ω·|∇φ|²
    grad_phi_sq = engine._spectral_gradient_sq(engine.phi)
    PE_coupling_omega_phi = np.sum(p.g_omega_phi * engine.omega * grad_phi_sq) * engine.dx**3
    
    # Coupling: g_ωρ·ω·(ρ-ρ₀)²
    delta_rho = engine.rho - p.rho_equilibrium
    PE_coupling_omega_rho = np.sum(p.g_omega_rho * engine.omega * delta_rho**2) * engine.dx**3
    
    # Basin occupation
    basin_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
    basin_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
    
    return EnergyComponents(
        time=engine.time,
        KE_total=KE_total,
        KE_omega=KE_omega,
        PE_band=PE_band,
        PE_gradient_omega=PE_gradient_omega,
        PE_coupling_omega_phi=PE_coupling_omega_phi,
        PE_coupling_omega_rho=PE_coupling_omega_rho,
        basin_high=basin_high,
        basin_low=basin_low,
        omega_mean=float(np.mean(engine.omega)),
        omega_std=float(np.std(engine.omega))
    )


def diagnose_basin_decay(
    grid_size: int = 16,
    total_time: float = 5.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Diagnose basin decay by tracking energy components.
    
    Identifies which energy term is responsible for decay.
    """
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    energy_history = []
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            components = compute_energy_components(engine)
            energy_history.append(components.to_dict())
    
    # Analyze which components changed most
    initial = energy_history[0]
    final = energy_history[-1]
    
    changes = {
        'KE_omega_change': final['KE_omega'] - initial['KE_omega'],
        'PE_band_change': final['PE_band'] - initial['PE_band'],
        'PE_gradient_omega_change': final['PE_gradient_omega'] - initial['PE_gradient_omega'],
        'PE_coupling_omega_phi_change': final['PE_coupling_omega_phi'] - initial['PE_coupling_omega_phi'],
        'PE_coupling_omega_rho_change': final['PE_coupling_omega_rho'] - initial['PE_coupling_omega_rho'],
        'basin_total_change': (final['basin_high'] + final['basin_low']) - (initial['basin_high'] + initial['basin_low']),
        'omega_std_change': final['omega_std'] - initial['omega_std']
    }
    
    # Find the dominant factor
    abs_changes = {k: abs(v) for k, v in changes.items() if 'basin' not in k and 'omega_std' not in k}
    dominant_factor = max(abs_changes, key=abs_changes.get)
    
    return {
        'test': 'energy_component_tracking',
        'initial_state': initial,
        'final_state': final,
        'changes': changes,
        'dominant_factor': dominant_factor,
        'energy_history': energy_history,
        'diagnosis': f"Largest energy change: {dominant_factor} ({changes[dominant_factor]:.4f})"
    }


def test_isolated_frequency_dynamics(
    grid_size: int = 16,
    total_time: float = 10.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Test with couplings = 0: isolate frequency dynamics.
    
    If basins are stable with no couplings → couplings are the problem.
    If still unstable → potential or gradient is the problem.
    """
    params = QMRTFrequencyParameters()
    params.g_omega_phi = 0.0  # Disable phase coupling
    params.g_omega_rho = 0.0  # Disable density coupling
    
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    p = engine.params
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    history = []
    initial_basins = None
    stability_time = total_time
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            basin_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            basin_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            
            history.append({
                'time': float(engine.time),
                'basin_high': basin_high,
                'basin_low': basin_low,
                'total': basin_high + basin_low,
                'omega_std': float(np.std(engine.omega))
            })
            
            if initial_basins is None:
                initial_basins = basin_high + basin_low
            
            if stability_time == total_time:
                if (basin_high + basin_low) < 0.8 * initial_basins:
                    stability_time = engine.time
    
    final = history[-1]
    is_stable = (final['basin_high'] + final['basin_low']) > 0.7 * initial_basins
    
    return {
        'test': 'isolated_frequency_dynamics',
        'couplings_disabled': ['g_omega_phi', 'g_omega_rho'],
        'initial_basin_total': initial_basins,
        'final_basin_total': final['basin_high'] + final['basin_low'],
        'stability_time': stability_time,
        'is_stable': bool(is_stable),
        'history': history,
        'diagnosis': 'Couplings are NOT the problem' if not is_stable else 'Couplings WERE the problem - disabling stabilized basins'
    }


def test_gradient_free_dynamics(
    grid_size: int = 16,
    total_time: float = 10.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Test with K_omega = 0: no gradient penalty on frequency.
    
    If basins are stable → gradient term was smoothing out basins.
    If still unstable → gradient is not the problem.
    """
    params = QMRTFrequencyParameters()
    params.K_omega = 0.0  # Disable frequency gradient energy
    
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    p = engine.params
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    history = []
    initial_basins = None
    stability_time = total_time
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            basin_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            basin_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            
            history.append({
                'time': float(engine.time),
                'basin_high': basin_high,
                'basin_low': basin_low,
                'total': basin_high + basin_low,
                'omega_std': float(np.std(engine.omega))
            })
            
            if initial_basins is None:
                initial_basins = basin_high + basin_low
            
            if stability_time == total_time:
                if (basin_high + basin_low) < 0.8 * initial_basins:
                    stability_time = engine.time
    
    final = history[-1]
    is_stable = (final['basin_high'] + final['basin_low']) > 0.7 * initial_basins
    
    return {
        'test': 'gradient_free_dynamics',
        'K_omega': 0.0,
        'initial_basin_total': initial_basins,
        'final_basin_total': final['basin_high'] + final['basin_low'],
        'stability_time': stability_time,
        'is_stable': bool(is_stable),
        'history': history,
        'diagnosis': 'Gradient term was NOT the problem' if not is_stable else 'Gradient term WAS the problem - disabling stabilized basins'
    }


def test_stronger_potential(
    grid_size: int = 16,
    total_time: float = 10.0,
    dt: float = 0.01,
    a_omega_multiplier: float = 10.0,
    seed: int = 42
) -> Dict:
    """
    Test with much stronger band potential.
    
    If basins stabilize → potential was too weak relative to other forces.
    """
    params = QMRTFrequencyParameters()
    params.a_omega *= a_omega_multiplier  # Increase potential strength
    
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    p = engine.params
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    history = []
    initial_basins = None
    stability_time = total_time
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            basin_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            basin_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            
            history.append({
                'time': float(engine.time),
                'basin_high': basin_high,
                'basin_low': basin_low,
                'total': basin_high + basin_low,
                'omega_std': float(np.std(engine.omega))
            })
            
            if initial_basins is None:
                initial_basins = basin_high + basin_low
            
            if stability_time == total_time:
                if (basin_high + basin_low) < 0.8 * initial_basins:
                    stability_time = engine.time
    
    final = history[-1]
    is_stable = (final['basin_high'] + final['basin_low']) > 0.7 * initial_basins
    
    return {
        'test': 'stronger_potential',
        'a_omega': float(params.a_omega),
        'multiplier': a_omega_multiplier,
        'initial_basin_total': initial_basins,
        'final_basin_total': final['basin_high'] + final['basin_low'],
        'stability_time': stability_time,
        'is_stable': bool(is_stable),
        'history': history,
        'diagnosis': f'Stronger potential (x{a_omega_multiplier}) {"STABILIZED" if is_stable else "did NOT stabilize"} basins'
    }


def test_combined_fixes(
    grid_size: int = 16,
    total_time: float = 15.0,
    dt: float = 0.01,
    seed: int = 42
) -> Dict:
    """
    Test with combined parameter adjustments:
    - Stronger potential (a_omega x10)
    - Weaker couplings (g_omega_phi, g_omega_rho x0.1)
    - Weaker gradient (K_omega x0.1)
    """
    params = QMRTFrequencyParameters()
    params.a_omega *= 10.0       # Much stronger potential
    params.K_omega *= 0.1        # Weaker gradient smoothing
    params.g_omega_phi *= 0.1    # Weaker phase coupling
    params.g_omega_rho *= 0.1    # Weaker density coupling
    
    engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    p = engine.params
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 50)
    
    history = []
    initial_basins = None
    stability_time = total_time
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            basin_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            basin_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            
            history.append({
                'time': float(engine.time),
                'basin_high': basin_high,
                'basin_low': basin_low,
                'total': basin_high + basin_low,
                'omega_std': float(np.std(engine.omega)),
                'energy_drift': float((engine.compute_total_energy() - engine.initial_energy) / abs(engine.initial_energy))
            })
            
            if initial_basins is None:
                initial_basins = basin_high + basin_low
            
            if stability_time == total_time:
                if (basin_high + basin_low) < 0.8 * initial_basins:
                    stability_time = engine.time
    
    final = history[-1]
    is_stable = (final['basin_high'] + final['basin_low']) > 0.7 * initial_basins
    
    return {
        'test': 'combined_parameter_fixes',
        'adjustments': {
            'a_omega': 'x10 (stronger)',
            'K_omega': 'x0.1 (weaker)',
            'g_omega_phi': 'x0.1 (weaker)',
            'g_omega_rho': 'x0.1 (weaker)'
        },
        'initial_basin_total': initial_basins,
        'final_basin_total': final['basin_high'] + final['basin_low'],
        'stability_time': stability_time,
        'is_stable': bool(is_stable),
        'history': history,
        'diagnosis': f'Combined fixes {"STABILIZED" if is_stable else "did NOT stabilize"} basins (stability: {stability_time:.1f}s)'
    }


def run_full_basin_diagnosis(seed: int = 42) -> Dict:
    """
    Run complete basin decay diagnosis.
    
    Tests:
    1. Energy component tracking
    2. Isolated frequency (no couplings)
    3. Gradient-free test
    4. Stronger potential
    5. Combined fixes
    """
    print("=" * 60)
    print("QMRT BASIN DECAY DIAGNOSIS")
    print("=" * 60)
    
    results = {}
    
    # 1. Energy tracking
    print("\n[1/5] Tracking energy components...")
    results['energy_tracking'] = diagnose_basin_decay(seed=seed)
    print(f"  Dominant factor: {results['energy_tracking']['dominant_factor']}")
    
    # 2. Isolated frequency
    print("\n[2/5] Testing isolated frequency dynamics (no couplings)...")
    results['isolated_frequency'] = test_isolated_frequency_dynamics(seed=seed)
    print(f"  Stability time: {results['isolated_frequency']['stability_time']:.2f}s")
    print(f"  Diagnosis: {results['isolated_frequency']['diagnosis']}")
    
    # 3. Gradient-free
    print("\n[3/5] Testing gradient-free dynamics (K_omega=0)...")
    results['gradient_free'] = test_gradient_free_dynamics(seed=seed)
    print(f"  Stability time: {results['gradient_free']['stability_time']:.2f}s")
    print(f"  Diagnosis: {results['gradient_free']['diagnosis']}")
    
    # 4. Stronger potential
    print("\n[4/5] Testing stronger potential (a_omega x10)...")
    results['stronger_potential'] = test_stronger_potential(a_omega_multiplier=10.0, seed=seed)
    print(f"  Stability time: {results['stronger_potential']['stability_time']:.2f}s")
    print(f"  Diagnosis: {results['stronger_potential']['diagnosis']}")
    
    # 5. Combined fixes
    print("\n[5/5] Testing combined parameter fixes...")
    results['combined_fixes'] = test_combined_fixes(seed=seed)
    print(f"  Stability time: {results['combined_fixes']['stability_time']:.2f}s")
    print(f"  Diagnosis: {results['combined_fixes']['diagnosis']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    diagnoses = []
    
    if results['isolated_frequency']['is_stable']:
        diagnoses.append("COUPLINGS cause decay - disabling stabilizes basins")
    else:
        diagnoses.append("Couplings are NOT the main problem")
    
    if results['gradient_free']['is_stable']:
        diagnoses.append("GRADIENT TERM causes decay - disabling stabilizes basins")
    else:
        diagnoses.append("Gradient term is NOT the main problem")
    
    if results['stronger_potential']['is_stable']:
        diagnoses.append("POTENTIAL too weak - stronger potential stabilizes")
    else:
        diagnoses.append("Potential strength alone doesn't fix it")
    
    if results['combined_fixes']['is_stable']:
        diagnoses.append("COMBINED FIXES work - need parameter rebalancing")
    else:
        diagnoses.append("Combined fixes don't fully solve it - may need deeper changes")
    
    results['summary'] = {
        'diagnoses': diagnoses,
        'dominant_energy_change': results['energy_tracking']['dominant_factor'],
        'best_stability_time': max(
            results['isolated_frequency']['stability_time'],
            results['gradient_free']['stability_time'],
            results['stronger_potential']['stability_time'],
            results['combined_fixes']['stability_time']
        ),
        'recommendation': 'See individual diagnoses for specific parameter adjustments'
    }
    
    for d in diagnoses:
        print(f"  • {d}")
    
    return results
