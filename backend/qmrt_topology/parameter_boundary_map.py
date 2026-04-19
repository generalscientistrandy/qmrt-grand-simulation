#!/usr/bin/env python3
"""
PARAMETER BOUNDARY MAPPING
==========================

Map the phase space of the QMRT dynamical medium to find:
1. Where spacetime "turns on" (coupling emerges)
2. Where it strengthens (strong coupling regime)
3. Where it weakens or breaks (boundary conditions)

Parameters to sweep:
- α (backreaction): 0.05 → 0.95
- Dimension: 2D and 3D comparison

Measurements at each point:
- Balance achieved (E_cv)
- Spatial structure S
- Ordering structure O  
- Spacetime coupling I_TS
- Temporal layers R, P
- Correlations ρ(O,S), ρ(P,S), ρ(R,S)
- Isotropy CV
- Confinement %

Output: Phase diagram showing regime boundaries

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.stats import pearsonr
from scipy.signal import find_peaks
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


@dataclass
class BoundaryPoint:
    """Single point in parameter space."""
    alpha: float
    dimension: str
    
    # Balance
    E_cv: float
    balanced: bool
    
    # Structure
    S_mean: float
    O_mean: float
    
    # Temporal
    R_mean: float
    P_mean: float
    
    # Coupling
    I_TS: float
    rho_OS: float
    rho_PS: float
    rho_RS: float
    
    # Geometry
    isotropy_cv: float
    confinement: float
    
    # Derived
    coupling_strength: float  # Combined measure
    regime: str  # 'weak', 'transition', 'strong', 'breakdown'


class BoundaryMapper2D:
    """2D simulation for boundary mapping."""
    
    def __init__(self, size=60, beta=0.5, lambda_relax=0.5, 
                 D_medium=0.1, gamma_wave=0.01, dt=0.04):
        self.size = size
        self.c_0 = 2.0
        self.tau_0 = 1.0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.reset()
        
    def reset(self):
        self.phi = np.zeros((self.size, self.size))
        self.phi_dot = np.zeros((self.size, self.size))
        self.tau = np.ones((self.size, self.size)) * self.tau_0
        self.tau_prev = self.tau.copy()
        
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
        self.tau_prev = self.tau.copy()
        rho = self.phi**2 + self.phi_dot**2
        
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, amplitude=3.0):
        center = self.size // 2
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center)**2 + (y - center)**2)
        self.phi_dot += amplitude * np.exp(-r**2 / 32)
    
    def measure_steady_state(self, n_steps=300, sample_start=0.6):
        """Run to steady state and measure."""
        self.add_pulse()
        
        measurements = []
        start_idx = int(n_steps * sample_start)
        
        for step in range(n_steps):
            self.step()
            
            if step >= start_idx and step % 5 == 0:
                measurements.append(self._measure())
        
        return self._aggregate_measurements(measurements)
    
    def _measure(self):
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        
        # Energy
        gx = np.roll(self.phi, -1, 0) - self.phi
        gy = np.roll(self.phi, -1, 1) - self.phi
        grad_phi = np.sqrt(gx**2 + gy**2)
        E_kin = 0.5 * np.sum(self.phi_dot**2)
        E_grad = 0.5 * np.sum(c_eff**2 * grad_phi**2)
        E_total = E_kin + E_grad
        
        # S
        c_mean = np.mean(c_eff)
        c_std = np.std(c_eff)
        gc = np.sqrt((np.roll(c_eff, -1, 0) - c_eff)**2 + (np.roll(c_eff, -1, 1) - c_eff)**2)
        S = np.sqrt((c_std / (c_mean + 1e-10))**2 + np.mean(gc)**2)
        
        # O
        O = (c_std / (c_mean + 1e-10)) * np.mean(gc) * np.var(c_eff)
        
        # R, P
        tau_change = np.abs(self.tau - self.tau_prev)
        R = np.mean(tau_change) / self.dt
        P = 1.0 / (1.0 + R)
        
        # Correlations
        S_flat = c_eff.flatten()
        R_flat = tau_change.flatten()
        P_flat = gaussian_filter(rho, sigma=3.0).flatten()
        O_flat = (1.0 / (c_eff + 0.1)).flatten()
        
        rho_RS = pearsonr(R_flat, S_flat)[0] if np.std(R_flat) > 1e-10 else 0
        rho_PS = pearsonr(P_flat, S_flat)[0] if np.std(P_flat) > 1e-10 else 0
        rho_OS = pearsonr(O_flat, S_flat)[0] if np.std(O_flat) > 1e-10 else 0
        
        I_TS = np.sqrt(rho_RS**2 + rho_PS**2 + rho_OS**2) / np.sqrt(3)
        
        # Geometry
        center = self.size // 2
        energy_x = np.sum(rho[center:, center])
        energy_y = np.sum(rho[center, center:])
        isotropy = np.std([energy_x, energy_y]) / (np.mean([energy_x, energy_y]) + 1e-10)
        
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center)**2 + (y - center)**2)
        cone_r = c_mean * self.dt * 300 * 0.6  # Approximate
        inside = r <= cone_r
        conf = np.sum(rho[inside]) / (np.sum(rho) + 1e-10) * 100 if cone_r > 0 else 100
        
        return {
            'E': E_total, 'S': S, 'O': O, 'R': R, 'P': P,
            'I_TS': I_TS, 'rho_OS': rho_OS, 'rho_PS': rho_PS, 'rho_RS': rho_RS,
            'isotropy': isotropy, 'confinement': conf
        }
    
    def _aggregate_measurements(self, measurements):
        """Aggregate steady-state measurements."""
        E_vals = [m['E'] for m in measurements]
        E_cv = np.std(E_vals) / (np.mean(E_vals) + 1e-10)
        
        return {
            'E_cv': E_cv,
            'balanced': E_cv < 0.05,
            'S_mean': np.mean([m['S'] for m in measurements]),
            'O_mean': np.mean([m['O'] for m in measurements]),
            'R_mean': np.mean([m['R'] for m in measurements]),
            'P_mean': np.mean([m['P'] for m in measurements]),
            'I_TS': np.mean([m['I_TS'] for m in measurements]),
            'rho_OS': np.mean([m['rho_OS'] for m in measurements]),
            'rho_PS': np.mean([m['rho_PS'] for m in measurements]),
            'rho_RS': np.mean([m['rho_RS'] for m in measurements]),
            'isotropy_cv': np.mean([m['isotropy'] for m in measurements]),
            'confinement': np.mean([m['confinement'] for m in measurements]),
        }


class BoundaryMapper3D:
    """3D simulation for boundary mapping (smaller grid for speed)."""
    
    def __init__(self, size=32, beta=0.5, lambda_relax=0.5,
                 D_medium=0.1, gamma_wave=0.01, dt=0.04):
        self.size = size
        self.c_0 = 2.0
        self.tau_0 = 1.0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.reset()
        
    def reset(self):
        self.phi = np.zeros((self.size, self.size, self.size))
        self.phi_dot = np.zeros((self.size, self.size, self.size))
        self.tau = np.ones((self.size, self.size, self.size)) * self.tau_0
        self.tau_prev = self.tau.copy()
        
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
        self.tau_prev = self.tau.copy()
        rho = self.phi**2 + self.phi_dot**2
        
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, amplitude=4.0):
        center = self.size // 2
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.phi_dot += amplitude * np.exp(-r**2 / 18)
    
    def measure_steady_state(self, n_steps=200, sample_start=0.6):
        """Run to steady state and measure."""
        self.add_pulse()
        
        measurements = []
        start_idx = int(n_steps * sample_start)
        
        for step in range(n_steps):
            self.step()
            
            if step >= start_idx and step % 5 == 0:
                measurements.append(self._measure())
        
        return self._aggregate_measurements(measurements)
    
    def _measure(self):
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        
        # Energy
        gx = np.roll(self.phi, -1, 0) - self.phi
        gy = np.roll(self.phi, -1, 1) - self.phi
        gz = np.roll(self.phi, -1, 2) - self.phi
        grad_phi = np.sqrt(gx**2 + gy**2 + gz**2)
        E_kin = 0.5 * np.sum(self.phi_dot**2)
        E_grad = 0.5 * np.sum(c_eff**2 * grad_phi**2)
        E_total = E_kin + E_grad
        
        # S
        c_mean = np.mean(c_eff)
        c_std = np.std(c_eff)
        gcx = np.roll(c_eff, -1, 0) - c_eff
        gcy = np.roll(c_eff, -1, 1) - c_eff
        gcz = np.roll(c_eff, -1, 2) - c_eff
        gc = np.sqrt(gcx**2 + gcy**2 + gcz**2)
        S = np.sqrt((c_std / (c_mean + 1e-10))**2 + np.mean(gc)**2)
        
        # O
        O = (c_std / (c_mean + 1e-10)) * np.mean(gc) * np.var(c_eff)
        
        # R, P
        tau_change = np.abs(self.tau - self.tau_prev)
        R = np.mean(tau_change) / self.dt
        P = 1.0 / (1.0 + R)
        
        # Correlations
        S_flat = c_eff.flatten()
        R_flat = tau_change.flatten()
        P_flat = gaussian_filter(rho, sigma=2.0).flatten()
        O_flat = (1.0 / (c_eff + 0.1)).flatten()
        
        rho_RS = pearsonr(R_flat, S_flat)[0] if np.std(R_flat) > 1e-10 else 0
        rho_PS = pearsonr(P_flat, S_flat)[0] if np.std(P_flat) > 1e-10 else 0
        rho_OS = pearsonr(O_flat, S_flat)[0] if np.std(O_flat) > 1e-10 else 0
        
        I_TS = np.sqrt(rho_RS**2 + rho_PS**2 + rho_OS**2) / np.sqrt(3)
        
        # Geometry
        center = self.size // 2
        energy_x = np.sum(rho[center:, center, center])
        energy_y = np.sum(rho[center, center:, center])
        energy_z = np.sum(rho[center, center, center:])
        isotropy = np.std([energy_x, energy_y, energy_z]) / (np.mean([energy_x, energy_y, energy_z]) + 1e-10)
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        cone_r = c_mean * self.dt * 200 * 0.6
        inside = r <= cone_r
        conf = np.sum(rho[inside]) / (np.sum(rho) + 1e-10) * 100 if cone_r > 0 else 100
        
        return {
            'E': E_total, 'S': S, 'O': O, 'R': R, 'P': P,
            'I_TS': I_TS, 'rho_OS': rho_OS, 'rho_PS': rho_PS, 'rho_RS': rho_RS,
            'isotropy': isotropy, 'confinement': conf
        }
    
    def _aggregate_measurements(self, measurements):
        E_vals = [m['E'] for m in measurements]
        E_cv = np.std(E_vals) / (np.mean(E_vals) + 1e-10)
        
        return {
            'E_cv': E_cv,
            'balanced': E_cv < 0.05,
            'S_mean': np.mean([m['S'] for m in measurements]),
            'O_mean': np.mean([m['O'] for m in measurements]),
            'R_mean': np.mean([m['R'] for m in measurements]),
            'P_mean': np.mean([m['P'] for m in measurements]),
            'I_TS': np.mean([m['I_TS'] for m in measurements]),
            'rho_OS': np.mean([m['rho_OS'] for m in measurements]),
            'rho_PS': np.mean([m['rho_PS'] for m in measurements]),
            'rho_RS': np.mean([m['rho_RS'] for m in measurements]),
            'isotropy_cv': np.mean([m['isotropy'] for m in measurements]),
            'confinement': np.mean([m['confinement'] for m in measurements]),
        }


def classify_regime(point: Dict) -> str:
    """Classify the regime based on measurements."""
    I_TS = point['I_TS']
    balanced = point['balanced']
    rho_OS = abs(point['rho_OS'])
    
    if not balanced:
        return 'unstable'
    elif I_TS < 0.3:
        return 'weak'
    elif I_TS < 0.6:
        return 'transition'
    elif I_TS >= 0.6 and rho_OS > 0.8:
        return 'strong'
    else:
        return 'partial'


def run_boundary_mapping():
    """Main boundary mapping experiment."""
    print("="*70)
    print("PARAMETER BOUNDARY MAPPING")
    print("="*70)
    print()
    print("Mapping α from 0.05 to 0.95 in 2D and 3D")
    print("Looking for: weak → transition → strong → breakdown")
    print()
    
    # Parameter sweep
    alpha_values = np.linspace(0.05, 0.95, 19)
    
    results_2d = []
    results_3d = []
    
    # 2D sweep
    print("Running 2D sweep...")
    print("-" * 50)
    
    for i, alpha in enumerate(alpha_values):
        sim = BoundaryMapper2D(size=60, beta=alpha)
        m = sim.measure_steady_state(n_steps=300)
        
        regime = classify_regime(m)
        
        point = BoundaryPoint(
            alpha=alpha,
            dimension='2d',
            E_cv=m['E_cv'],
            balanced=m['balanced'],
            S_mean=m['S_mean'],
            O_mean=m['O_mean'],
            R_mean=m['R_mean'],
            P_mean=m['P_mean'],
            I_TS=m['I_TS'],
            rho_OS=m['rho_OS'],
            rho_PS=m['rho_PS'],
            rho_RS=m['rho_RS'],
            isotropy_cv=m['isotropy_cv'],
            confinement=m['confinement'],
            coupling_strength=m['I_TS'] * abs(m['rho_OS']),
            regime=regime,
        )
        results_2d.append(point)
        
        print(f"  α={alpha:.2f}: I_TS={m['I_TS']:.3f}, ρ(O,S)={m['rho_OS']:.3f}, regime={regime}")
    
    print()
    
    # 3D sweep
    print("Running 3D sweep...")
    print("-" * 50)
    
    for i, alpha in enumerate(alpha_values):
        sim = BoundaryMapper3D(size=32, beta=alpha)
        m = sim.measure_steady_state(n_steps=200)
        
        regime = classify_regime(m)
        
        point = BoundaryPoint(
            alpha=alpha,
            dimension='3d',
            E_cv=m['E_cv'],
            balanced=m['balanced'],
            S_mean=m['S_mean'],
            O_mean=m['O_mean'],
            R_mean=m['R_mean'],
            P_mean=m['P_mean'],
            I_TS=m['I_TS'],
            rho_OS=m['rho_OS'],
            rho_PS=m['rho_PS'],
            rho_RS=m['rho_RS'],
            isotropy_cv=m['isotropy_cv'],
            confinement=m['confinement'],
            coupling_strength=m['I_TS'] * abs(m['rho_OS']),
            regime=regime,
        )
        results_3d.append(point)
        
        print(f"  α={alpha:.2f}: I_TS={m['I_TS']:.3f}, ρ(O,S)={m['rho_OS']:.3f}, regime={regime}")
    
    print()
    
    # Analyze boundaries
    print("="*70)
    print("BOUNDARY ANALYSIS")
    print("="*70)
    
    # Find transition points
    def find_transitions(results):
        regimes = [p.regime for p in results]
        alphas = [p.alpha for p in results]
        
        transitions = []
        for i in range(1, len(regimes)):
            if regimes[i] != regimes[i-1]:
                transitions.append({
                    'alpha': (alphas[i-1] + alphas[i]) / 2,
                    'from': regimes[i-1],
                    'to': regimes[i],
                })
        return transitions
    
    transitions_2d = find_transitions(results_2d)
    transitions_3d = find_transitions(results_3d)
    
    print("\n2D Transitions:")
    for t in transitions_2d:
        print(f"  α ≈ {t['alpha']:.2f}: {t['from']} → {t['to']}")
    
    print("\n3D Transitions:")
    for t in transitions_3d:
        print(f"  α ≈ {t['alpha']:.2f}: {t['from']} → {t['to']}")
    
    # Summary statistics
    print("\n" + "="*70)
    print("REGIME SUMMARY")
    print("="*70)
    
    for dim, results in [('2D', results_2d), ('3D', results_3d)]:
        print(f"\n{dim}:")
        regimes = {}
        for p in results:
            if p.regime not in regimes:
                regimes[p.regime] = []
            regimes[p.regime].append(p.alpha)
        
        for regime in ['weak', 'transition', 'partial', 'strong', 'unstable']:
            if regime in regimes:
                alphas = regimes[regime]
                print(f"  {regime}: α ∈ [{min(alphas):.2f}, {max(alphas):.2f}]")
    
    return results_2d, results_3d, transitions_2d, transitions_3d


def generate_boundary_figures(results_2d, results_3d, transitions_2d, transitions_3d):
    """Generate phase diagram figures."""
    
    alpha_2d = [p.alpha for p in results_2d]
    alpha_3d = [p.alpha for p in results_3d]
    
    fig = plt.figure(figsize=(16, 14))
    
    # Panel 1: I_TS vs α
    ax1 = fig.add_subplot(3, 3, 1)
    ax1.plot(alpha_2d, [p.I_TS for p in results_2d], 'b-o', label='2D', markersize=4)
    ax1.plot(alpha_3d, [p.I_TS for p in results_3d], 'r-s', label='3D', markersize=4)
    ax1.axhline(y=0.3, color='gray', linestyle='--', alpha=0.5, label='Weak threshold')
    ax1.axhline(y=0.6, color='gray', linestyle=':', alpha=0.5, label='Strong threshold')
    ax1.set_xlabel('α (Backreaction)')
    ax1.set_ylabel('I_TS (Coupling)')
    ax1.set_title('Spacetime Coupling vs α', fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: ρ(O,S) vs α
    ax2 = fig.add_subplot(3, 3, 2)
    ax2.plot(alpha_2d, [p.rho_OS for p in results_2d], 'b-o', label='2D', markersize=4)
    ax2.plot(alpha_3d, [p.rho_OS for p in results_3d], 'r-s', label='3D', markersize=4)
    ax2.axhline(y=-0.8, color='gray', linestyle='--', alpha=0.5)
    ax2.set_xlabel('α')
    ax2.set_ylabel('ρ(O, S)')
    ax2.set_title('O-S Correlation vs α', fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: S vs α
    ax3 = fig.add_subplot(3, 3, 3)
    ax3.plot(alpha_2d, [p.S_mean for p in results_2d], 'b-o', label='2D', markersize=4)
    ax3.plot(alpha_3d, [p.S_mean for p in results_3d], 'r-s', label='3D', markersize=4)
    ax3.set_xlabel('α')
    ax3.set_ylabel('S (Spatial)')
    ax3.set_title('Spatial Structure vs α', fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: E_cv vs α
    ax4 = fig.add_subplot(3, 3, 4)
    ax4.plot(alpha_2d, [p.E_cv for p in results_2d], 'b-o', label='2D', markersize=4)
    ax4.plot(alpha_3d, [p.E_cv for p in results_3d], 'r-s', label='3D', markersize=4)
    ax4.axhline(y=0.05, color='gray', linestyle='--', alpha=0.5, label='Balance threshold')
    ax4.set_xlabel('α')
    ax4.set_ylabel('E_cv')
    ax4.set_title('Energy Stability vs α', fontweight='bold')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # Panel 5: Coupling strength heatmap
    ax5 = fig.add_subplot(3, 3, 5)
    coupling_2d = [p.coupling_strength for p in results_2d]
    coupling_3d = [p.coupling_strength for p in results_3d]
    ax5.plot(alpha_2d, coupling_2d, 'b-o', label='2D', markersize=4)
    ax5.plot(alpha_3d, coupling_3d, 'r-s', label='3D', markersize=4)
    ax5.set_xlabel('α')
    ax5.set_ylabel('Coupling Strength (I_TS × |ρ_OS|)')
    ax5.set_title('Combined Coupling Strength', fontweight='bold')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3)
    
    # Panel 6: Regime classification
    ax6 = fig.add_subplot(3, 3, 6)
    regime_colors = {'weak': 'blue', 'transition': 'yellow', 'partial': 'orange', 
                     'strong': 'green', 'unstable': 'red'}
    
    for i, p in enumerate(results_2d):
        ax6.scatter(p.alpha, 0.7, c=regime_colors.get(p.regime, 'gray'), s=100, marker='s')
    for i, p in enumerate(results_3d):
        ax6.scatter(p.alpha, 0.3, c=regime_colors.get(p.regime, 'gray'), s=100, marker='o')
    
    ax6.set_xlabel('α')
    ax6.set_yticks([0.3, 0.7])
    ax6.set_yticklabels(['3D', '2D'])
    ax6.set_title('Regime Classification', fontweight='bold')
    ax6.set_xlim(0, 1)
    ax6.grid(True, alpha=0.3)
    
    # Add legend for regimes
    for regime, color in regime_colors.items():
        ax6.scatter([], [], c=color, s=50, label=regime)
    ax6.legend(loc='upper left', fontsize=8)
    
    # Panel 7: ρ(R,S) and ρ(P,S)
    ax7 = fig.add_subplot(3, 3, 7)
    ax7.plot(alpha_2d, [p.rho_RS for p in results_2d], 'b-o', label='ρ(R,S) 2D', markersize=4)
    ax7.plot(alpha_2d, [p.rho_PS for p in results_2d], 'b--s', label='ρ(P,S) 2D', markersize=4)
    ax7.plot(alpha_3d, [p.rho_RS for p in results_3d], 'r-o', label='ρ(R,S) 3D', markersize=4)
    ax7.plot(alpha_3d, [p.rho_PS for p in results_3d], 'r--s', label='ρ(P,S) 3D', markersize=4)
    ax7.set_xlabel('α')
    ax7.set_ylabel('Correlation')
    ax7.set_title('R,P Correlations with S', fontweight='bold')
    ax7.legend(fontsize=7)
    ax7.grid(True, alpha=0.3)
    
    # Panel 8: Confinement
    ax8 = fig.add_subplot(3, 3, 8)
    ax8.plot(alpha_2d, [p.confinement for p in results_2d], 'b-o', label='2D', markersize=4)
    ax8.plot(alpha_3d, [p.confinement for p in results_3d], 'r-s', label='3D', markersize=4)
    ax8.axhline(y=80, color='gray', linestyle='--', alpha=0.5)
    ax8.set_xlabel('α')
    ax8.set_ylabel('Confinement %')
    ax8.set_title('Causal Confinement vs α', fontweight='bold')
    ax8.legend(fontsize=8)
    ax8.grid(True, alpha=0.3)
    
    # Panel 9: Summary
    ax9 = fig.add_subplot(3, 3, 9)
    ax9.axis('off')
    
    # Build summary text
    summary_lines = ["PARAMETER BOUNDARY MAP", "=" * 30, ""]
    
    summary_lines.append("2D Regimes:")
    for p in results_2d:
        if p.alpha in [0.05, 0.25, 0.5, 0.75, 0.95]:
            summary_lines.append(f"  α={p.alpha:.2f}: {p.regime}")
    
    summary_lines.append("")
    summary_lines.append("3D Regimes:")
    for p in results_3d:
        if p.alpha in [0.05, 0.25, 0.5, 0.75, 0.95]:
            summary_lines.append(f"  α={p.alpha:.2f}: {p.regime}")
    
    summary_lines.append("")
    summary_lines.append("2D Transitions:")
    for t in transitions_2d:
        summary_lines.append(f"  α≈{t['alpha']:.2f}: {t['from']}→{t['to']}")
    
    summary_lines.append("")
    summary_lines.append("3D Transitions:")
    for t in transitions_3d:
        summary_lines.append(f"  α≈{t['alpha']:.2f}: {t['from']}→{t['to']}")
    
    summary_text = "\n".join(summary_lines)
    
    ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    plt.suptitle('QMRT PARAMETER BOUNDARY MAP: Where Spacetime Emerges', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/parameter_boundary_map.png', dpi=150, bbox_inches='tight')
    print("\nSaved: parameter_boundary_map.png")
    
    # Save data
    output = {
        '2d': [{'alpha': p.alpha, 'regime': p.regime, 'I_TS': p.I_TS, 
                'rho_OS': p.rho_OS, 'S': p.S_mean, 'coupling': p.coupling_strength}
               for p in results_2d],
        '3d': [{'alpha': p.alpha, 'regime': p.regime, 'I_TS': p.I_TS,
                'rho_OS': p.rho_OS, 'S': p.S_mean, 'coupling': p.coupling_strength}
               for p in results_3d],
        'transitions_2d': transitions_2d,
        'transitions_3d': transitions_3d,
    }
    
    with open('/app/backend/qmrt_topology/parameter_boundary_map.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("Saved: parameter_boundary_map.json")


if __name__ == "__main__":
    results_2d, results_3d, t_2d, t_3d = run_boundary_mapping()
    generate_boundary_figures(results_2d, results_3d, t_2d, t_3d)
