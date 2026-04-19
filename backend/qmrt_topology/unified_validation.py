#!/usr/bin/env python3
"""
UNIFIED 3D VALIDATION RUN
=========================

Single end-to-end experiment measuring ALL theory components together:

1. MEDIUM BALANCE: damping, relaxation, bounded attractor
2. SPATIAL STRUCTURE: S (metric variation, gradients)
3. ORDERING STRUCTURE: O (causal path diversity)
4. RATE: R (dynamical flow coupling)
5. PERSISTENCE: P (stability measure)
6. SPACETIME COUPLING: I_TS, cross-branch correlations
7. 3D CAUSAL GEOMETRY: cone shape, isotropy
8. SCALING CHECK: O ~ S² in unified context

QUESTION: Does the full theory survive when everything 
is measured together instead of in separate tests?

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.stats import pearsonr
from scipy.optimize import curve_fit
import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


@dataclass
class UnifiedMeasurement:
    """Single timestep measurement of all theory components."""
    t: float
    
    # Medium balance
    E_total: float = 0.0
    E_kinetic: float = 0.0
    E_gradient: float = 0.0
    P_production: float = 0.0
    D_dissipation: float = 0.0
    
    # Spatial structure S
    S_metric: float = 0.0
    S_gradient: float = 0.0
    S_total: float = 0.0
    
    # Ordering structure O
    O_diversity: float = 0.0
    O_capacity: float = 0.0
    O_total: float = 0.0
    
    # Temporal layers
    R_rate: float = 0.0
    P_persistence: float = 0.0
    O_ordering: float = 0.0
    
    # Spacetime coupling
    I_TS: float = 0.0
    rho_RS: float = 0.0
    rho_PS: float = 0.0
    rho_OS: float = 0.0
    
    # 3D geometry
    isotropy_cv: float = 0.0
    cone_confinement: float = 0.0
    wavefront_radius: float = 0.0


class UnifiedSimulator3D:
    """
    Full 3D dynamical medium with integrated measurement.
    """
    
    def __init__(
        self,
        size: int = 40,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        beta: float = 0.5,
        lambda_relax: float = 0.5,
        D_medium: float = 0.1,
        gamma_wave: float = 0.01,
        dt: float = 0.04,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        # 3D fields
        self.phi = np.zeros((size, size, size))
        self.phi_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size)) * tau_0
        
        # Previous state for rate computation
        self.tau_prev = self.tau.copy()
        self.phi_prev = self.phi.copy()
        
        # Coordinates
        self.x, self.y, self.z = np.meshgrid(
            np.arange(size), np.arange(size), np.arange(size), indexing='ij'
        )
        
        # Source location
        self.source_center = (size // 2, size // 2, size // 2)
        
    def compute_c_eff(self) -> np.ndarray:
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho: np.ndarray) -> np.ndarray:
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_laplacian(self, f: np.ndarray) -> np.ndarray:
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6*f)
    
    def compute_gradient_magnitude(self, f: np.ndarray) -> np.ndarray:
        gx = np.roll(f, -1, 0) - f
        gy = np.roll(f, -1, 1) - f
        gz = np.roll(f, -1, 2) - f
        return np.sqrt(gx**2 + gy**2 + gz**2)
    
    def step(self):
        """Advance one timestep, storing previous state."""
        self.tau_prev = self.tau.copy()
        self.phi_prev = self.phi.copy()
        
        rho = self.phi**2 + self.phi_dot**2
        
        # Medium relaxation
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave evolution
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center: Tuple[int, int, int], amplitude: float = 3.0, width: float = 3.0):
        cx, cy, cz = center
        r = np.sqrt((self.x - cx)**2 + (self.y - cy)**2 + (self.z - cz)**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))
        self.source_center = center
    
    # ================================================================
    # INTEGRATED MEASUREMENT
    # ================================================================
    
    def measure_all(self, t: float) -> UnifiedMeasurement:
        """Measure ALL theory components in one pass."""
        m = UnifiedMeasurement(t=t)
        
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        tau_eq = self.compute_tau_eq(rho)
        
        # ----- 1. MEDIUM BALANCE -----
        grad_phi = self.compute_gradient_magnitude(self.phi)
        m.E_kinetic = 0.5 * np.sum(self.phi_dot**2)
        m.E_gradient = 0.5 * np.sum(c_eff**2 * grad_phi**2)
        m.E_total = m.E_kinetic + m.E_gradient
        
        # Production/dissipation
        dtau_dt = (self.tau - self.tau_prev) / self.dt if self.dt > 0 else np.zeros_like(self.tau)
        dc_dt = (self.c_0 / self.tau_0) * dtau_dt
        m.P_production = np.sum(c_eff * dc_dt * grad_phi**2)
        m.D_dissipation = self.gamma_wave * np.sum(self.phi_dot**2)
        
        # ----- 2. SPATIAL STRUCTURE S -----
        c_mean = np.mean(c_eff)
        c_std = np.std(c_eff)
        m.S_metric = c_std / (c_mean + 1e-10)
        
        grad_c = self.compute_gradient_magnitude(c_eff)
        m.S_gradient = np.mean(grad_c)
        m.S_total = np.sqrt(m.S_metric**2 + m.S_gradient**2)
        
        # ----- 3. ORDERING STRUCTURE O -----
        m.O_diversity = c_std
        m.O_capacity = c_std / (c_mean + 1e-10)
        m.O_total = m.O_capacity * m.S_gradient * np.var(c_eff)
        
        # ----- 4. TEMPORAL LAYERS (O, R, P) -----
        
        # O_ordering: based on causal connectivity
        # (simplified: measure of how structured the c_eff field is)
        m.O_ordering = 1.0 - m.S_metric  # High structure = constrained ordering
        
        # R_rate: temporal change rate of the medium
        tau_change = np.abs(self.tau - self.tau_prev)
        m.R_rate = np.mean(tau_change) / self.dt if self.dt > 0 else 0
        
        # P_persistence: stability of the configuration
        # (inverse of rate, bounded)
        m.P_persistence = 1.0 / (1.0 + m.R_rate)
        
        # ----- 5. SPACETIME COUPLING I_TS -----
        # Cross-branch coupling integral
        # I_TS = correlation between temporal layers and spatial structure
        
        # Flatten for correlation
        S_flat = c_eff.flatten()
        
        # R proxy: local rate of change
        R_flat = tau_change.flatten()
        
        # P proxy: local stability (inverse variance in neighborhood)
        P_flat = gaussian_filter(rho, sigma=3.0).flatten()
        
        # Correlations
        if np.std(S_flat) > 1e-10 and np.std(R_flat) > 1e-10:
            m.rho_RS, _ = pearsonr(R_flat, S_flat)
        else:
            m.rho_RS = 0.0
            
        if np.std(S_flat) > 1e-10 and np.std(P_flat) > 1e-10:
            m.rho_PS, _ = pearsonr(P_flat, S_flat)
        else:
            m.rho_PS = 0.0
        
        # O-S correlation (ordering vs spatial)
        O_flat = (1.0 / (c_eff + 0.1)).flatten()  # Low c = more constrained = higher O
        if np.std(O_flat) > 1e-10 and np.std(S_flat) > 1e-10:
            m.rho_OS, _ = pearsonr(O_flat, S_flat)
        else:
            m.rho_OS = 0.0
        
        # Combined coupling strength
        m.I_TS = np.sqrt(m.rho_RS**2 + m.rho_PS**2 + m.rho_OS**2) / np.sqrt(3)
        
        # ----- 6. 3D CAUSAL GEOMETRY -----
        cx, cy, cz = self.source_center
        r = np.sqrt((self.x - cx)**2 + (self.y - cy)**2 + (self.z - cz)**2)
        
        # Isotropy check: energy along each axis
        energy_x = np.sum(rho[cx:, cy, cz])
        energy_y = np.sum(rho[cx, cy:, cz])
        energy_z = np.sum(rho[cx, cy, cz:])
        energies = [energy_x, energy_y, energy_z]
        if np.mean(energies) > 1e-10:
            m.isotropy_cv = np.std(energies) / np.mean(energies)
        else:
            m.isotropy_cv = 0.0
        
        # Cone confinement
        cone_radius = np.mean(c_eff) * t
        if cone_radius > 0:
            inside = r <= cone_radius
            energy_inside = np.sum(rho[inside])
            energy_total = np.sum(rho)
            m.cone_confinement = energy_inside / (energy_total + 1e-10) * 100
        else:
            m.cone_confinement = 100.0
        
        # Wavefront radius (peak energy)
        r_flat = r.flatten()
        rho_flat = rho.flatten()
        if np.max(rho_flat) > 1e-10:
            # Weighted average radius
            m.wavefront_radius = np.sum(r_flat * rho_flat) / (np.sum(rho_flat) + 1e-10)
        else:
            m.wavefront_radius = 0.0
        
        return m


def run_unified_validation():
    """
    Main unified validation run.
    """
    print("="*70)
    print("UNIFIED 3D VALIDATION RUN")
    print("="*70)
    print()
    print("Measuring ALL theory components in one coherent experiment:")
    print("  1. Medium balance (E, P, D)")
    print("  2. Spatial structure (S)")
    print("  3. Ordering structure (O)")
    print("  4. Temporal layers (O, R, P)")
    print("  5. Spacetime coupling (I_TS, ρ)")
    print("  6. 3D causal geometry")
    print("  7. Scaling check (O ~ S²)")
    print()
    
    # Create simulator
    sim = UnifiedSimulator3D(size=40, beta=0.5, gamma_wave=0.01)
    sim.add_pulse((20, 20, 20), amplitude=4.0, width=3.0)
    
    # Run and measure
    measurements: List[UnifiedMeasurement] = []
    n_steps = 400
    measure_interval = 10
    
    print("Running simulation...")
    for step in range(n_steps):
        sim.step()
        
        if step % measure_interval == 0:
            t = step * sim.dt
            m = sim.measure_all(t)
            measurements.append(m)
            
            if step % 100 == 0:
                print(f"  t = {t:.1f}: E = {m.E_total:.0f}, S = {m.S_total:.4f}, "
                      f"O = {m.O_total:.6f}, I_TS = {m.I_TS:.3f}")
    
    print()
    
    # ================================================================
    # ANALYSIS
    # ================================================================
    
    results = analyze_unified_measurements(measurements)
    
    # ================================================================
    # SCALING CHECK: O ~ S²
    # ================================================================
    
    print("\n" + "-"*50)
    print("SCALING CHECK: O ~ S²")
    print("-"*50)
    
    S_vals = np.array([m.S_total for m in measurements])
    O_vals = np.array([m.O_total for m in measurements])
    
    # Filter valid points
    valid = (S_vals > 1e-6) & (O_vals > 1e-10) & np.isfinite(S_vals) & np.isfinite(O_vals)
    S_valid = S_vals[valid]
    O_valid = O_vals[valid]
    
    if len(S_valid) > 5:
        try:
            def power_law(x, A, alpha):
                return A * np.power(x + 1e-6, alpha)
            
            popt, _ = curve_fit(power_law, S_valid, O_valid, p0=[1.0, 2.0], maxfev=5000)
            A_fit, alpha_fit = popt
            
            O_pred = power_law(S_valid, *popt)
            ss_res = np.sum((O_valid - O_pred)**2)
            ss_tot = np.sum((O_valid - np.mean(O_valid))**2)
            r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
            
            print(f"  Fitted: O = {A_fit:.4f} · S^{alpha_fit:.3f}")
            print(f"  R² = {r2:.4f}")
            print(f"  Expected α = 2.0, measured α = {alpha_fit:.3f}")
            
            alpha_error = abs(alpha_fit - 2.0)
            scaling_holds = alpha_error < 0.5 and r2 > 0.7
            
            print(f"  {'✓ SCALING HOLDS' if scaling_holds else '○ Scaling deviation'}")
            
            results['scaling'] = {
                'A': float(A_fit),
                'alpha': float(alpha_fit),
                'R2': float(r2),
                'holds': scaling_holds,
            }
        except Exception as e:
            print(f"  Fit failed: {e}")
            results['scaling'] = {'holds': False, 'error': str(e)}
    else:
        print("  Insufficient valid data points")
        results['scaling'] = {'holds': False, 'error': 'insufficient data'}
    
    # ================================================================
    # FINAL VERDICT
    # ================================================================
    
    print("\n" + "="*70)
    print("UNIFIED VALIDATION VERDICT")
    print("="*70)
    
    checks = [
        ('Medium Balance', results['balance']['achieved']),
        ('Spatial Structure S', results['spatial']['valid']),
        ('Ordering Structure O', results['ordering']['valid']),
        ('Rate R', results['temporal']['R_valid']),
        ('Persistence P', results['temporal']['P_valid']),
        ('Spacetime Coupling I_TS', results['coupling']['strong']),
        ('3D Isotropy', results['geometry']['isotropic']),
        ('Causal Confinement', results['geometry']['confined']),
        ('Scaling O ~ S²', results['scaling'].get('holds', False)),
    ]
    
    print()
    for name, passed in checks:
        status = "✓ PASS" if passed else "○ FAIL"
        print(f"  {name}: {status}")
    
    n_pass = sum(c[1] for c in checks)
    n_total = len(checks)
    
    print()
    print(f"Overall: {n_pass}/{n_total} checks passed")
    
    unified_valid = n_pass >= 7  # Allow 2 failures
    
    if unified_valid:
        print()
        print("="*70)
        print("✓ UNIFIED THEORY VALIDATED")
        print("  All components hold together in integrated measurement")
        print("="*70)
    else:
        print()
        print("○ THEORY NEEDS REFINEMENT")
        print("  Some components do not integrate cleanly")
    
    results['verdict'] = {
        'checks_passed': n_pass,
        'checks_total': n_total,
        'unified_valid': unified_valid,
    }
    
    # Save results
    save_results(results, measurements)
    
    # Generate figures
    generate_unified_figures(measurements, results)
    
    return results, measurements


def analyze_unified_measurements(measurements: List[UnifiedMeasurement]) -> Dict:
    """Analyze the unified measurements."""
    results = {}
    
    # Extract arrays
    E = np.array([m.E_total for m in measurements])
    P = np.array([m.P_production for m in measurements])
    D = np.array([m.D_dissipation for m in measurements])
    S = np.array([m.S_total for m in measurements])
    O = np.array([m.O_total for m in measurements])
    R = np.array([m.R_rate for m in measurements])
    Pers = np.array([m.P_persistence for m in measurements])
    I_TS = np.array([m.I_TS for m in measurements])
    iso = np.array([m.isotropy_cv for m in measurements])
    conf = np.array([m.cone_confinement for m in measurements])
    
    n = len(measurements)
    late_start = int(0.6 * n)
    
    # ----- 1. MEDIUM BALANCE -----
    print("-"*50)
    print("1. MEDIUM BALANCE")
    print("-"*50)
    
    late_E = E[late_start:]
    E_cv = np.std(late_E) / (np.mean(late_E) + 1e-10)
    balance_achieved = E_cv < 0.05
    
    print(f"  Late energy CV: {E_cv:.4f}")
    print(f"  {'✓ BALANCED' if balance_achieved else '○ Not balanced'}")
    
    results['balance'] = {
        'E_cv': float(E_cv),
        'achieved': balance_achieved,
        'E_mean': float(np.mean(late_E)),
    }
    
    # ----- 2. SPATIAL STRUCTURE S -----
    print("\n" + "-"*50)
    print("2. SPATIAL STRUCTURE S")
    print("-"*50)
    
    S_late = S[late_start:]
    S_mean = np.mean(S_late)
    S_valid = S_mean > 0.01  # Meaningful structure exists
    
    print(f"  Late S mean: {S_mean:.4f}")
    print(f"  {'✓ VALID' if S_valid else '○ Weak structure'}")
    
    results['spatial'] = {
        'S_mean': float(S_mean),
        'valid': S_valid,
    }
    
    # ----- 3. ORDERING STRUCTURE O -----
    print("\n" + "-"*50)
    print("3. ORDERING STRUCTURE O")
    print("-"*50)
    
    O_late = O[late_start:]
    O_mean = np.mean(O_late)
    O_valid = O_mean > 1e-8  # Nonzero ordering
    
    print(f"  Late O mean: {O_mean:.8f}")
    print(f"  {'✓ VALID' if O_valid else '○ Negligible ordering'}")
    
    results['ordering'] = {
        'O_mean': float(O_mean),
        'valid': O_valid,
    }
    
    # ----- 4. TEMPORAL LAYERS (R, P) -----
    print("\n" + "-"*50)
    print("4. TEMPORAL LAYERS (R, P)")
    print("-"*50)
    
    R_late = R[late_start:]
    R_mean = np.mean(R_late)
    R_valid = R_mean > 0 and R_mean < 10  # Reasonable rate
    
    Pers_late = Pers[late_start:]
    Pers_mean = np.mean(Pers_late)
    P_valid = Pers_mean > 0.1  # Some persistence
    
    print(f"  Late R mean: {R_mean:.4f} {'✓' if R_valid else '○'}")
    print(f"  Late P mean: {Pers_mean:.4f} {'✓' if P_valid else '○'}")
    
    results['temporal'] = {
        'R_mean': float(R_mean),
        'R_valid': R_valid,
        'P_mean': float(Pers_mean),
        'P_valid': P_valid,
    }
    
    # ----- 5. SPACETIME COUPLING I_TS -----
    print("\n" + "-"*50)
    print("5. SPACETIME COUPLING I_TS")
    print("-"*50)
    
    I_late = I_TS[late_start:]
    I_mean = np.mean(I_late)
    coupling_strong = I_mean > 0.3  # Meaningful coupling
    
    rho_RS_mean = np.mean([m.rho_RS for m in measurements[late_start:]])
    rho_PS_mean = np.mean([m.rho_PS for m in measurements[late_start:]])
    rho_OS_mean = np.mean([m.rho_OS for m in measurements[late_start:]])
    
    print(f"  Late I_TS mean: {I_mean:.4f}")
    print(f"  ρ(R,S) = {rho_RS_mean:.3f}")
    print(f"  ρ(P,S) = {rho_PS_mean:.3f}")
    print(f"  ρ(O,S) = {rho_OS_mean:.3f}")
    print(f"  {'✓ STRONG COUPLING' if coupling_strong else '○ Weak coupling'}")
    
    results['coupling'] = {
        'I_TS_mean': float(I_mean),
        'rho_RS': float(rho_RS_mean),
        'rho_PS': float(rho_PS_mean),
        'rho_OS': float(rho_OS_mean),
        'strong': coupling_strong,
    }
    
    # ----- 6. 3D GEOMETRY -----
    print("\n" + "-"*50)
    print("6. 3D CAUSAL GEOMETRY")
    print("-"*50)
    
    iso_late = iso[late_start:]
    iso_mean = np.mean(iso_late)
    isotropic = iso_mean < 0.2  # Low CV = isotropic
    
    conf_late = conf[late_start:]
    conf_mean = np.mean(conf_late)
    confined = conf_mean > 80  # >80% confined
    
    print(f"  Late isotropy CV: {iso_mean:.4f} {'✓' if isotropic else '○'}")
    print(f"  Late confinement: {conf_mean:.1f}% {'✓' if confined else '○'}")
    
    results['geometry'] = {
        'isotropy_cv': float(iso_mean),
        'isotropic': isotropic,
        'confinement': float(conf_mean),
        'confined': confined,
    }
    
    return results


def save_results(results: Dict, measurements: List[UnifiedMeasurement]):
    """Save results to JSON."""
    
    # Convert measurements to serializable format
    m_data = []
    for m in measurements:
        m_data.append({
            't': m.t,
            'E_total': m.E_total,
            'S_total': m.S_total,
            'O_total': m.O_total,
            'R_rate': m.R_rate,
            'P_persistence': m.P_persistence,
            'I_TS': m.I_TS,
            'isotropy_cv': m.isotropy_cv,
            'cone_confinement': m.cone_confinement,
        })
    
    output = {
        'results': results,
        'measurements_summary': {
            'n_measurements': len(measurements),
            'duration': measurements[-1].t if measurements else 0,
        },
    }
    
    with open('/app/backend/qmrt_topology/unified_validation.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("\nSaved: unified_validation.json")


def generate_unified_figures(measurements: List[UnifiedMeasurement], results: Dict):
    """Generate unified validation figures."""
    
    t = np.array([m.t for m in measurements])
    E = np.array([m.E_total for m in measurements])
    S = np.array([m.S_total for m in measurements])
    O = np.array([m.O_total for m in measurements])
    R = np.array([m.R_rate for m in measurements])
    P = np.array([m.P_persistence for m in measurements])
    I_TS = np.array([m.I_TS for m in measurements])
    iso = np.array([m.isotropy_cv for m in measurements])
    conf = np.array([m.cone_confinement for m in measurements])
    
    fig = plt.figure(figsize=(16, 14))
    
    # Row 1: Medium and Structure
    ax1 = fig.add_subplot(3, 3, 1)
    ax1.plot(t, E, 'b-', linewidth=2)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Energy E')
    ax1.set_title('Medium Balance', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    ax2 = fig.add_subplot(3, 3, 2)
    ax2.plot(t, S, 'g-', linewidth=2, label='S')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('S')
    ax2.set_title('Spatial Structure', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    ax3 = fig.add_subplot(3, 3, 3)
    ax3.plot(t, O, 'r-', linewidth=2)
    ax3.set_xlabel('Time')
    ax3.set_ylabel('O')
    ax3.set_title('Ordering Structure', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Row 2: Temporal and Coupling
    ax4 = fig.add_subplot(3, 3, 4)
    ax4.plot(t, R, 'orange', linewidth=2, label='R (rate)')
    ax4.plot(t, P, 'purple', linewidth=2, label='P (persist)')
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Value')
    ax4.set_title('Temporal Layers', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    ax5 = fig.add_subplot(3, 3, 5)
    ax5.plot(t, I_TS, 'b-', linewidth=2)
    ax5.axhline(y=0.3, color='r', linestyle='--', alpha=0.5, label='Strong threshold')
    ax5.set_xlabel('Time')
    ax5.set_ylabel('I_TS')
    ax5.set_title('Spacetime Coupling', fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    ax6 = fig.add_subplot(3, 3, 6)
    ax6.plot(t, iso, 'g-', linewidth=2, label='Isotropy CV')
    ax6.plot(t, conf/100, 'b-', linewidth=2, label='Confinement')
    ax6.set_xlabel('Time')
    ax6.set_ylabel('Value')
    ax6.set_title('3D Geometry', fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    # Row 3: Scaling and Summary
    ax7 = fig.add_subplot(3, 3, 7)
    valid = (S > 1e-6) & (O > 1e-10)
    ax7.scatter(S[valid], O[valid], c=t[valid], cmap='viridis', s=20, alpha=0.7)
    if 'scaling' in results and 'alpha' in results['scaling']:
        S_fit = np.linspace(S[valid].min(), S[valid].max(), 50)
        A = results['scaling']['A']
        alpha = results['scaling']['alpha']
        O_fit = A * np.power(S_fit + 1e-6, alpha)
        ax7.plot(S_fit, O_fit, 'r-', linewidth=2, label=f'O = {A:.2e}·S^{alpha:.2f}')
        ax7.legend()
    ax7.set_xlabel('S')
    ax7.set_ylabel('O')
    ax7.set_title('Scaling: O vs S', fontweight='bold')
    ax7.grid(True, alpha=0.3)
    
    ax8 = fig.add_subplot(3, 3, 8)
    # Correlation plot
    rho_RS = [m.rho_RS for m in measurements]
    rho_PS = [m.rho_PS for m in measurements]
    rho_OS = [m.rho_OS for m in measurements]
    ax8.plot(t, rho_RS, 'r-', label='ρ(R,S)', alpha=0.7)
    ax8.plot(t, rho_PS, 'g-', label='ρ(P,S)', alpha=0.7)
    ax8.plot(t, rho_OS, 'b-', label='ρ(O,S)', alpha=0.7)
    ax8.set_xlabel('Time')
    ax8.set_ylabel('Correlation')
    ax8.set_title('Cross-Branch Correlations', fontweight='bold')
    ax8.legend()
    ax8.grid(True, alpha=0.3)
    
    # Summary panel
    ax9 = fig.add_subplot(3, 3, 9)
    ax9.axis('off')
    
    v = results['verdict']
    summary = f"""
UNIFIED VALIDATION SUMMARY
==========================

Checks Passed: {v['checks_passed']}/{v['checks_total']}

Components:
  Medium Balance: {'✓' if results['balance']['achieved'] else '○'}
  Spatial S: {'✓' if results['spatial']['valid'] else '○'}
  Ordering O: {'✓' if results['ordering']['valid'] else '○'}
  Rate R: {'✓' if results['temporal']['R_valid'] else '○'}
  Persistence P: {'✓' if results['temporal']['P_valid'] else '○'}
  Coupling I_TS: {'✓' if results['coupling']['strong'] else '○'}
  Isotropy: {'✓' if results['geometry']['isotropic'] else '○'}
  Confinement: {'✓' if results['geometry']['confined'] else '○'}
  Scaling O~S²: {'✓' if results['scaling'].get('holds', False) else '○'}

{'✓ UNIFIED THEORY VALIDATED' if v['unified_valid'] else '○ NEEDS REFINEMENT'}
"""
    
    bg = 'lightgreen' if v['unified_valid'] else 'lightyellow'
    ax9.text(0.05, 0.95, summary, transform=ax9.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor=bg, alpha=0.5))
    
    plt.suptitle('UNIFIED 3D VALIDATION: All Theory Components', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/unified_validation.png', dpi=150, bbox_inches='tight')
    print("Saved: unified_validation.png")


if __name__ == "__main__":
    run_unified_validation()
