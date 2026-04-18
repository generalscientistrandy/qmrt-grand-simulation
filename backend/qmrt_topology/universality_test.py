#!/usr/bin/env python3
"""
CRITICAL EXPONENT UNIVERSALITY TEST
====================================

Test whether the power-law exponent α ≈ 2.54 in O_structure = O_max · S^α
is universal across:

1. DIMENSIONALITY: 1D, 2D, 3D
2. COUPLING REGIME: near transition, far from transition  
3. SYSTEM SIZE: grid resolution, timestep
4. INITIAL CONDITIONS: pulse, plane wave, random

If the exponent is UNIVERSAL:
  → Same α across all conditions
  → Strong evidence for critical phenomenon
  → Connects to universality classes in stat mech

If the exponent VARIES:
  → System-dependent, not universal
  → Still valid, but different physics interpretation

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
from scipy.ndimage import gaussian_filter
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# MULTI-DIMENSIONAL SIMULATORS
# ============================================================

class Simulator1D:
    """1D dynamical medium."""
    
    def __init__(self, size=200, c_0=2.0, tau_0=1.0, beta=0.5, 
                 lambda_relax=0.5, D_medium=0.1, gamma_wave=0.01, dt=0.04):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.phi = np.zeros(size)
        self.phi_dot = np.zeros(size)
        self.tau = np.ones(size) * tau_0
        
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_laplacian(self, f):
        return np.roll(f, 1) + np.roll(f, -1) - 2*f
    
    def step(self):
        rho = self.phi**2 + self.phi_dot**2
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        self.tau += (-self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau) * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center, amplitude=3.0, width=4.0):
        x = np.arange(self.size)
        self.phi_dot += amplitude * np.exp(-(x - center)**2 / (2*width**2))


class Simulator2D:
    """2D dynamical medium (standard)."""
    
    def __init__(self, size=80, c_0=2.0, tau_0=1.0, beta=0.5,
                 lambda_relax=0.5, D_medium=0.1, gamma_wave=0.01, dt=0.04):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_laplacian(self, f):
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) + 
                np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
    
    def step(self):
        rho = self.phi**2 + self.phi_dot**2
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        self.tau += (-self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau) * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center, amplitude=3.0, width=4.0):
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size))
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))


class Simulator3D:
    """3D dynamical medium."""
    
    def __init__(self, size=40, c_0=2.0, tau_0=1.0, beta=0.5,
                 lambda_relax=0.5, D_medium=0.1, gamma_wave=0.01, dt=0.04):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.phi = np.zeros((size, size, size))
        self.phi_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size)) * tau_0
        
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_laplacian(self, f):
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) + 
                np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6*f)
    
    def step(self):
        rho = self.phi**2 + self.phi_dot**2
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        self.tau += (-self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau) * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center, amplitude=3.0, width=4.0):
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                              np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2 + (z - center[2])**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))


# ============================================================
# MEASUREMENT FUNCTIONS
# ============================================================

def measure_S_O(sim, dim):
    """Measure S (geometry) and O_structure for any dimension."""
    c_eff = sim.compute_c_eff()
    
    # S_structure: coefficient of variation + gradient magnitude
    c_mean = np.mean(c_eff)
    c_std = np.std(c_eff)
    S_metric = c_std / (c_mean + 1e-10)
    
    if dim == 1:
        grad = np.roll(c_eff, -1) - c_eff
        S_grad = np.mean(np.abs(grad))
    elif dim == 2:
        gx = np.roll(c_eff, -1, 0) - c_eff
        gy = np.roll(c_eff, -1, 1) - c_eff
        S_grad = np.mean(np.sqrt(gx**2 + gy**2))
    else:  # 3D
        gx = np.roll(c_eff, -1, 0) - c_eff
        gy = np.roll(c_eff, -1, 1) - c_eff
        gz = np.roll(c_eff, -1, 2) - c_eff
        S_grad = np.mean(np.sqrt(gx**2 + gy**2 + gz**2))
    
    S = np.sqrt(S_metric**2 + S_grad**2)
    
    # O_structure: path diversity measure
    O_diversity = np.std(c_eff.flatten())
    O_capacity = O_diversity / (c_mean + 1e-10)
    O = O_capacity * S_grad
    
    return float(S), float(O)


def fit_power_law(S_vals, O_vals):
    """Fit O = A * S^alpha and return exponent."""
    S = np.array(S_vals)
    O = np.array(O_vals)
    
    # Filter valid points
    valid = (S > 0) & (O > 0) & np.isfinite(S) & np.isfinite(O)
    S = S[valid]
    O = O[valid]
    
    if len(S) < 3:
        return None, None, 0
    
    try:
        def power_law(x, A, alpha):
            return A * np.power(x + 0.001, alpha)
        
        popt, _ = curve_fit(power_law, S, O, p0=[1.0, 2.0], maxfev=5000)
        O_pred = power_law(S, *popt)
        ss_res = np.sum((O - O_pred)**2)
        ss_tot = np.sum((O - np.mean(O))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        
        return popt[0], popt[1], r2  # A, alpha, R²
    except:
        return None, None, 0


# ============================================================
# TEST 1: DIMENSIONALITY
# ============================================================

def test_dimensionality():
    """Test exponent across 1D, 2D, 3D."""
    print("\n" + "="*70)
    print("TEST 1: DIMENSIONALITY")
    print("="*70)
    
    results = {}
    
    for dim in [1, 2, 3]:
        print(f"\nRunning {dim}D...")
        
        alpha_values = np.linspace(0.1, 0.9, 10)
        S_data = []
        O_data = []
        
        for alpha in alpha_values:
            if dim == 1:
                sim = Simulator1D(size=200, beta=alpha)
                sim.add_pulse(100, amplitude=3.0)
            elif dim == 2:
                sim = Simulator2D(size=60, beta=alpha)
                sim.add_pulse([30, 30], amplitude=3.0)
            else:
                sim = Simulator3D(size=30, beta=alpha)
                sim.add_pulse([15, 15, 15], amplitude=3.0)
            
            for _ in range(150):
                sim.step()
            
            S, O = measure_S_O(sim, dim)
            S_data.append(S)
            O_data.append(O)
        
        A, alpha_exp, r2 = fit_power_law(S_data, O_data)
        
        results[f'{dim}D'] = {
            'exponent': alpha_exp,
            'coefficient': A,
            'R2': r2,
            'S_range': [min(S_data), max(S_data)],
            'O_range': [min(O_data), max(O_data)],
        }
        
        if alpha_exp:
            print(f"  {dim}D: α = {alpha_exp:.3f}, R² = {r2:.4f}")
        else:
            print(f"  {dim}D: Fit failed")
    
    return results


# ============================================================
# TEST 2: COUPLING REGIME
# ============================================================

def test_coupling_regime():
    """Test exponent near vs far from transition."""
    print("\n" + "="*70)
    print("TEST 2: COUPLING REGIME")
    print("="*70)
    
    # Near transition: α around 0.3-0.5 (crossover region)
    # Far from transition: α around 0.7-0.9 (deep spacetime regime)
    
    regimes = {
        'near_transition': np.linspace(0.2, 0.5, 8),
        'far_transition': np.linspace(0.6, 0.9, 8),
        'full_range': np.linspace(0.1, 0.9, 12),
    }
    
    results = {}
    
    for regime_name, alpha_values in regimes.items():
        print(f"\nRegime: {regime_name}")
        
        S_data = []
        O_data = []
        
        for alpha in alpha_values:
            sim = Simulator2D(size=60, beta=alpha)
            sim.add_pulse([30, 30], amplitude=3.0)
            
            for _ in range(150):
                sim.step()
            
            S, O = measure_S_O(sim, 2)
            S_data.append(S)
            O_data.append(O)
        
        A, alpha_exp, r2 = fit_power_law(S_data, O_data)
        
        results[regime_name] = {
            'alpha_range': [float(alpha_values.min()), float(alpha_values.max())],
            'exponent': alpha_exp,
            'coefficient': A,
            'R2': r2,
        }
        
        if alpha_exp:
            print(f"  α ∈ [{alpha_values.min():.1f}, {alpha_values.max():.1f}]: exponent = {alpha_exp:.3f}, R² = {r2:.4f}")
    
    return results


# ============================================================
# TEST 3: SYSTEM SIZE / RESOLUTION
# ============================================================

def test_system_size():
    """Test exponent across different grid sizes and timesteps."""
    print("\n" + "="*70)
    print("TEST 3: SYSTEM SIZE / RESOLUTION")
    print("="*70)
    
    results = {}
    
    # Grid size test
    print("\nGrid size variation:")
    sizes = [40, 60, 80, 100]
    
    for size in sizes:
        alpha_values = np.linspace(0.2, 0.8, 8)
        S_data = []
        O_data = []
        
        for alpha in alpha_values:
            sim = Simulator2D(size=size, beta=alpha)
            center = size // 2
            sim.add_pulse([center, center], amplitude=3.0)
            
            for _ in range(150):
                sim.step()
            
            S, O = measure_S_O(sim, 2)
            S_data.append(S)
            O_data.append(O)
        
        A, alpha_exp, r2 = fit_power_law(S_data, O_data)
        
        results[f'size_{size}'] = {
            'grid_size': size,
            'exponent': alpha_exp,
            'R2': r2,
        }
        
        if alpha_exp:
            print(f"  Size {size}×{size}: α = {alpha_exp:.3f}, R² = {r2:.4f}")
    
    # Timestep test
    print("\nTimestep variation:")
    timesteps = [0.02, 0.04, 0.06, 0.08]
    
    for dt in timesteps:
        alpha_values = np.linspace(0.2, 0.8, 8)
        S_data = []
        O_data = []
        
        for alpha in alpha_values:
            sim = Simulator2D(size=60, beta=alpha, dt=dt)
            sim.add_pulse([30, 30], amplitude=3.0)
            
            n_steps = int(6.0 / dt)  # Same total time
            for _ in range(n_steps):
                sim.step()
            
            S, O = measure_S_O(sim, 2)
            S_data.append(S)
            O_data.append(O)
        
        A, alpha_exp, r2 = fit_power_law(S_data, O_data)
        
        results[f'dt_{dt}'] = {
            'timestep': dt,
            'exponent': alpha_exp,
            'R2': r2,
        }
        
        if alpha_exp:
            print(f"  dt = {dt}: α = {alpha_exp:.3f}, R² = {r2:.4f}")
    
    return results


# ============================================================
# TEST 4: INITIAL CONDITIONS
# ============================================================

def test_initial_conditions():
    """Test exponent with different initial conditions."""
    print("\n" + "="*70)
    print("TEST 4: INITIAL CONDITIONS")
    print("="*70)
    
    results = {}
    
    def run_with_init(init_type, init_func):
        alpha_values = np.linspace(0.2, 0.8, 8)
        S_data = []
        O_data = []
        
        for alpha in alpha_values:
            sim = Simulator2D(size=60, beta=alpha)
            init_func(sim)
            
            for _ in range(150):
                sim.step()
            
            S, O = measure_S_O(sim, 2)
            S_data.append(S)
            O_data.append(O)
        
        A, alpha_exp, r2 = fit_power_law(S_data, O_data)
        return alpha_exp, r2
    
    # 1. Gaussian pulse (standard)
    def pulse_init(sim):
        sim.add_pulse([30, 30], amplitude=3.0, width=4.0)
    
    exp, r2 = run_with_init('pulse', pulse_init)
    results['gaussian_pulse'] = {'exponent': exp, 'R2': r2}
    print(f"\nGaussian pulse: α = {exp:.3f}, R² = {r2:.4f}" if exp else "Gaussian pulse: fit failed")
    
    # 2. Plane wave
    def plane_wave_init(sim):
        x = np.arange(sim.size)
        wave = 2.0 * np.sin(2*np.pi*x/sim.size * 3)
        sim.phi_dot += wave[None, :]
    
    exp, r2 = run_with_init('plane_wave', plane_wave_init)
    results['plane_wave'] = {'exponent': exp, 'R2': r2}
    print(f"Plane wave: α = {exp:.3f}, R² = {r2:.4f}" if exp else "Plane wave: fit failed")
    
    # 3. Random noise
    def random_init(sim):
        np.random.seed(42)
        sim.phi_dot += 2.0 * np.random.randn(sim.size, sim.size)
    
    exp, r2 = run_with_init('random', random_init)
    results['random_noise'] = {'exponent': exp, 'R2': r2}
    print(f"Random noise: α = {exp:.3f}, R² = {r2:.4f}" if exp else "Random noise: fit failed")
    
    # 4. Two pulses
    def two_pulse_init(sim):
        sim.add_pulse([20, 30], amplitude=3.0, width=4.0)
        sim.add_pulse([40, 30], amplitude=3.0, width=4.0)
    
    exp, r2 = run_with_init('two_pulse', two_pulse_init)
    results['two_pulses'] = {'exponent': exp, 'R2': r2}
    print(f"Two pulses: α = {exp:.3f}, R² = {r2:.4f}" if exp else "Two pulses: fit failed")
    
    # 5. Ring
    def ring_init(sim):
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size))
        r = np.sqrt((x - 30)**2 + (y - 30)**2)
        ring = 3.0 * np.exp(-((r - 15)**2) / 8)
        sim.phi_dot += ring
    
    exp, r2 = run_with_init('ring', ring_init)
    results['ring'] = {'exponent': exp, 'R2': r2}
    print(f"Ring: α = {exp:.3f}, R² = {r2:.4f}" if exp else "Ring: fit failed")
    
    return results


# ============================================================
# MAIN
# ============================================================

def run_universality_tests():
    """Run all universality tests."""
    print("="*70)
    print("CRITICAL EXPONENT UNIVERSALITY TEST SUITE")
    print("="*70)
    print("\nTesting whether α ≈ 2.54 in O = A·S^α is universal")
    
    all_results = {}
    
    all_results['dimensionality'] = test_dimensionality()
    all_results['coupling_regime'] = test_coupling_regime()
    all_results['system_size'] = test_system_size()
    all_results['initial_conditions'] = test_initial_conditions()
    
    # Collect all exponents
    print("\n" + "="*70)
    print("SUMMARY: ALL EXPONENTS")
    print("="*70)
    
    exponents = []
    
    for test_name, test_results in all_results.items():
        print(f"\n{test_name.upper()}:")
        for config, data in test_results.items():
            if isinstance(data, dict) and 'exponent' in data and data['exponent'] is not None:
                exp = data['exponent']
                r2 = data.get('R2', 0)
                exponents.append((config, exp, r2))
                print(f"  {config}: α = {exp:.3f} (R² = {r2:.3f})")
    
    # Statistics
    valid_exponents = [e[1] for e in exponents if e[1] is not None and e[2] > 0.8]
    
    print("\n" + "="*70)
    print("UNIVERSALITY ANALYSIS")
    print("="*70)
    
    if len(valid_exponents) >= 3:
        mean_exp = np.mean(valid_exponents)
        std_exp = np.std(valid_exponents)
        cv = std_exp / mean_exp
        
        print(f"\nExponents with R² > 0.8: {len(valid_exponents)}")
        print(f"Mean exponent: {mean_exp:.3f}")
        print(f"Std deviation: {std_exp:.3f}")
        print(f"Coefficient of variation: {cv:.3f}")
        
        if cv < 0.1:
            verdict = "UNIVERSAL"
            interpretation = "Exponent is STABLE across conditions → Critical phenomenon"
        elif cv < 0.3:
            verdict = "WEAKLY UNIVERSAL"
            interpretation = "Exponent varies moderately → Quasi-universal"
        else:
            verdict = "NOT UNIVERSAL"
            interpretation = "Exponent varies significantly → System-dependent"
        
        print(f"\nVERDICT: {verdict}")
        print(f"Interpretation: {interpretation}")
        
        all_results['summary'] = {
            'mean_exponent': mean_exp,
            'std_exponent': std_exp,
            'cv': cv,
            'n_valid': len(valid_exponents),
            'verdict': verdict,
        }
    else:
        print("\nInsufficient valid fits for universality analysis")
        all_results['summary'] = {'verdict': 'INSUFFICIENT DATA'}
    
    # Save
    # Convert numpy types for JSON
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_types(v) for v in obj]
        elif isinstance(obj, (np.floating, np.integer)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    with open('/app/backend/qmrt_topology/universality_test.json', 'w') as f:
        json.dump(convert_types(all_results), f, indent=2)
    print("\nSaved: universality_test.json")
    
    return all_results


def generate_universality_figures(results):
    """Generate universality figures."""
    
    fig = plt.figure(figsize=(16, 12))
    
    # Collect all exponents for bar chart
    all_exps = []
    all_labels = []
    all_r2 = []
    
    for test_name, test_results in results.items():
        if test_name == 'summary':
            continue
        for config, data in test_results.items():
            if isinstance(data, dict) and 'exponent' in data and data['exponent'] is not None:
                all_exps.append(data['exponent'])
                all_labels.append(f"{test_name[:3]}:{config[:8]}")
                all_r2.append(data.get('R2', 0))
    
    # Panel 1: All exponents bar chart
    ax1 = fig.add_subplot(2, 2, 1)
    colors = ['green' if r > 0.9 else 'orange' if r > 0.7 else 'red' for r in all_r2]
    bars = ax1.barh(range(len(all_exps)), all_exps, color=colors, alpha=0.7)
    ax1.set_yticks(range(len(all_exps)))
    ax1.set_yticklabels(all_labels, fontsize=8)
    ax1.set_xlabel('Exponent α', fontsize=12)
    ax1.set_title('Critical Exponent Across All Tests', fontsize=12, fontweight='bold')
    
    # Add mean line
    valid_exps = [e for e, r in zip(all_exps, all_r2) if r > 0.8]
    if valid_exps:
        mean_exp = np.mean(valid_exps)
        ax1.axvline(x=mean_exp, color='blue', linestyle='--', linewidth=2, label=f'Mean = {mean_exp:.2f}')
        ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Dimensionality comparison
    ax2 = fig.add_subplot(2, 2, 2)
    dims = ['1D', '2D', '3D']
    dim_exps = []
    dim_r2 = []
    for d in dims:
        data = results.get('dimensionality', {}).get(d, {})
        dim_exps.append(data.get('exponent', 0) or 0)
        dim_r2.append(data.get('R2', 0) or 0)
    
    ax2.bar(dims, dim_exps, color=['blue', 'green', 'red'], alpha=0.7)
    ax2.set_ylabel('Exponent α', fontsize=12)
    ax2.set_title('Exponent vs Dimensionality', fontsize=12, fontweight='bold')
    for i, (e, r) in enumerate(zip(dim_exps, dim_r2)):
        ax2.text(i, e + 0.1, f'R²={r:.2f}', ha='center', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Coupling regime comparison
    ax3 = fig.add_subplot(2, 2, 3)
    regimes = ['near_transition', 'far_transition', 'full_range']
    regime_labels = ['Near\nTransition', 'Far\nTransition', 'Full\nRange']
    regime_exps = []
    regime_r2 = []
    for r in regimes:
        data = results.get('coupling_regime', {}).get(r, {})
        regime_exps.append(data.get('exponent', 0) or 0)
        regime_r2.append(data.get('R2', 0) or 0)
    
    ax3.bar(regime_labels, regime_exps, color=['orange', 'purple', 'green'], alpha=0.7)
    ax3.set_ylabel('Exponent α', fontsize=12)
    ax3.set_title('Exponent vs Coupling Regime', fontsize=12, fontweight='bold')
    for i, (e, r) in enumerate(zip(regime_exps, regime_r2)):
        ax3.text(i, e + 0.1, f'R²={r:.2f}', ha='center', fontsize=10)
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Summary
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    
    summary = results.get('summary', {})
    mean = summary.get('mean_exponent', 'N/A')
    std = summary.get('std_exponent', 'N/A')
    cv = summary.get('cv', 'N/A')
    verdict = summary.get('verdict', 'N/A')
    
    text = f"""
CRITICAL EXPONENT UNIVERSALITY
==============================

Mean Exponent: {mean:.3f}
Std Deviation: {std:.3f}
Coeff. of Var: {cv:.3f}

VERDICT: {verdict}

Tests Performed:
  • Dimensionality (1D, 2D, 3D)
  • Coupling regime (near/far transition)
  • System size (40-100 grid)
  • Timestep (0.02-0.08)
  • Initial conditions (5 types)

Color code:
  Green: R² > 0.9 (excellent fit)
  Orange: R² > 0.7 (good fit)
  Red: R² < 0.7 (poor fit)

If CV < 0.1: UNIVERSAL exponent
If CV < 0.3: WEAKLY UNIVERSAL
If CV > 0.3: NOT UNIVERSAL
"""
    
    bg_color = 'lightgreen' if verdict == 'UNIVERSAL' else 'lightyellow' if verdict == 'WEAKLY UNIVERSAL' else 'lightcoral'
    ax4.text(0.05, 0.95, text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.5))
    
    plt.suptitle('CRITICAL EXPONENT UNIVERSALITY TEST', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/universality_test.png', dpi=150, bbox_inches='tight')
    print("Saved: universality_test.png")


if __name__ == "__main__":
    results = run_universality_tests()
    generate_universality_figures(results)
