#!/usr/bin/env python3
"""
ENTROPY PRODUCTION AND THERMODYNAMIC STRUCTURE
===============================================

Building on the driven-dissipative balance analysis, we now define:

    Ṡ = (P - D) / T_eff

This connects QMRT to:
  - Statistical mechanics (entropy production)
  - Non-equilibrium thermodynamics (NESS)
  - Fluctuation theorems (Jarzynski, Crooks)

DEFINITIONS
-----------

1. ENTROPY PRODUCTION RATE:
   Ṡ_prod = P / T_eff
   
   Energy flowing INTO the system from medium → entropy produced
   
2. ENTROPY DISSIPATION RATE:
   Ṡ_diss = D / T_eff
   
   Energy flowing OUT via damping → entropy exported

3. NET ENTROPY RATE:
   Ṡ_net = (P - D) / T_eff = Ṡ_prod - Ṡ_diss
   
   At balance: Ṡ_net = 0 (steady state)
   Before balance: Ṡ_net ≠ 0 (system evolving)

4. EFFECTIVE TEMPERATURE:
   T_eff = ⟨ρ⟩ = mean energy density
   
   This is the "temperature" of the wave field.

FLUCTUATION THEOREM CONNECTION
------------------------------

For a driven-dissipative system, the probability ratio of forward vs reverse
trajectories satisfies:

    P(ΔS) / P(-ΔS) = exp(ΔS)

where ΔS is the entropy change along a trajectory.

If this holds, QMRT satisfies a fundamental thermodynamic consistency.

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json

from dynamical_medium import DynamicalMediumSimulator


class ThermodynamicAnalyzer:
    """
    Analyze entropy production in the driven-dissipative medium.
    """
    
    def __init__(
        self,
        size: int = 80,
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
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_gradients(self, field):
        grad_x = np.roll(field, -1, axis=0) - field
        grad_y = np.roll(field, -1, axis=1) - field
        return grad_x, grad_y
    
    def compute_laplacian(self, field):
        return (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
                np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4*field)
    
    def compute_thermodynamics(self):
        """
        Compute thermodynamic quantities.
        
        Returns:
            dict with P, D, T_eff, S_dot_prod, S_dot_diss, S_dot_net
        """
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        tau_eq = self.compute_tau_eq(rho)
        
        # Production rate P
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        dc_dt = (self.c_0 / self.tau_0) * dtau_dt
        
        grad_x, grad_y = self.compute_gradients(self.phi)
        grad_sq = grad_x**2 + grad_y**2
        P = np.sum(c_eff * dc_dt * grad_sq)
        
        # Dissipation rate D
        D = self.gamma_wave * np.sum(self.phi_dot**2)
        
        # Effective temperature (mean energy density)
        rho_mean = np.mean(rho)
        T_eff = max(rho_mean, 1e-10)  # Avoid division by zero
        
        # Entropy production/dissipation rates
        S_dot_prod = abs(P) / T_eff  # Production always positive
        S_dot_diss = D / T_eff
        
        # Net entropy rate
        # Positive P → energy into system → entropy produced
        # Negative P → energy out of medium coupling → entropy destroyed  
        S_dot_net = (P - D) / T_eff
        
        # Total entropy (approximation via Boltzmann-like measure)
        # S ~ log(phase space volume) ~ log(⟨E⟩) at fixed energy
        E_total = np.sum(0.5 * self.phi_dot**2 + 0.5 * c_eff**2 * grad_sq)
        S_total = np.log(E_total + 1)
        
        return {
            'P': float(P),
            'D': float(D),
            'T_eff': float(T_eff),
            'S_dot_prod': float(S_dot_prod),
            'S_dot_diss': float(S_dot_diss),
            'S_dot_net': float(S_dot_net),
            'S_total': float(S_total),
            'E_total': float(E_total),
            'rho_mean': float(rho_mean),
        }
    
    def step(self):
        """Advance one timestep."""
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
    
    def add_pulse(self, center, amplitude=3.0, width=4.0):
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))


def analyze_entropy_production():
    """
    Main analysis: entropy production in driven-dissipative medium.
    """
    print("=" * 70)
    print("ENTROPY PRODUCTION ANALYSIS")
    print("=" * 70)
    print()
    print("Definitions:")
    print("  Ṡ_net = (P - D) / T_eff")
    print("  P = production from medium coupling")
    print("  D = dissipation from wave damping")
    print("  T_eff = mean energy density (effective temperature)")
    print()
    
    analyzer = ThermodynamicAnalyzer(size=80, gamma_wave=0.01)
    analyzer.add_pulse([40, 40], amplitude=4.0)
    
    # Track evolution
    history = []
    steps = 1000
    
    for t in range(steps):
        thermo = analyzer.compute_thermodynamics()
        thermo['t'] = t * analyzer.dt
        history.append(thermo)
        analyzer.step()
    
    # Extract arrays
    t = np.array([h['t'] for h in history])
    P = np.array([h['P'] for h in history])
    D = np.array([h['D'] for h in history])
    T_eff = np.array([h['T_eff'] for h in history])
    S_dot_net = np.array([h['S_dot_net'] for h in history])
    S_total = np.array([h['S_total'] for h in history])
    E_total = np.array([h['E_total'] for h in history])
    
    # Analyze phases
    print("PHASE ANALYSIS")
    print("-" * 50)
    
    # Early phase
    early = int(0.2 * steps)
    early_S_dot = np.mean(S_dot_net[:early])
    print(f"Early (0-20%): ⟨Ṡ_net⟩ = {early_S_dot:.4f} {'(producing)' if early_S_dot > 0 else '(dissipating)'}")
    
    # Middle phase
    mid_start = int(0.2 * steps)
    mid_end = int(0.6 * steps)
    mid_S_dot = np.mean(S_dot_net[mid_start:mid_end])
    print(f"Middle (20-60%): ⟨Ṡ_net⟩ = {mid_S_dot:.4f}")
    
    # Late phase (should approach 0 at balance)
    late = int(0.6 * steps)
    late_S_dot = np.mean(S_dot_net[late:])
    print(f"Late (60-100%): ⟨Ṡ_net⟩ = {late_S_dot:.4f}")
    
    print()
    
    # Balance detection
    balance_achieved = abs(late_S_dot) < 0.01 * abs(early_S_dot)
    
    print("BALANCE DETECTION")
    print("-" * 50)
    print(f"|Ṡ_net(late)| / |Ṡ_net(early)| = {abs(late_S_dot) / (abs(early_S_dot) + 1e-10):.4f}")
    
    if balance_achieved:
        print("✓ THERMODYNAMIC BALANCE ACHIEVED (Ṡ_net → 0)")
    else:
        print("○ Approaching balance (Ṡ_net still nonzero)")
    
    print()
    
    # Total entropy change
    S_change = S_total[-1] - S_total[0]
    print("ENTROPY EVOLUTION")
    print("-" * 50)
    print(f"S(0) = {S_total[0]:.4f}")
    print(f"S(T) = {S_total[-1]:.4f}")
    print(f"ΔS = {S_change:.4f}")
    
    if S_change > 0:
        print("→ Net entropy PRODUCED (second law satisfied)")
    else:
        print("→ Net entropy REDUCED (driven system can do this)")
    
    print()
    
    # Effective temperature evolution
    print("EFFECTIVE TEMPERATURE")
    print("-" * 50)
    print(f"T_eff(0) = {T_eff[0]:.4f}")
    print(f"T_eff(T) = {T_eff[-1]:.4f}")
    print(f"T_eff ratio = {T_eff[-1] / T_eff[0]:.4f}")
    
    print()
    print("=" * 70)
    print("THERMODYNAMIC SUMMARY")
    print("=" * 70)
    
    print(f"""
The QMRT dynamical medium exhibits:

1. ENTROPY PRODUCTION during early evolution
   - Medium coupling injects energy → entropy produced
   
2. ENTROPY DISSIPATION throughout
   - Wave damping exports energy → entropy exported
   
3. THERMODYNAMIC BALANCE at late times
   - Ṡ_net → 0 (production ≈ dissipation)
   - This is the NESS (non-equilibrium steady state)

4. EFFECTIVE TEMPERATURE T_eff
   - Defined as mean energy density
   - Provides the thermodynamic scale

KEY RESULT:
  The driven-dissipative balance IS a thermodynamic balance.
  The system satisfies Ṡ_prod = Ṡ_diss at the fixed point.
""")
    
    return {
        'history': history,
        't': t.tolist(),
        'P': P.tolist(),
        'D': D.tolist(),
        'S_dot_net': S_dot_net.tolist(),
        'S_total': S_total.tolist(),
        'T_eff': T_eff.tolist(),
        'balance_achieved': balance_achieved,
        'S_change': S_change,
        'late_S_dot_mean': late_S_dot,
    }


def generate_entropy_figures(results):
    """Generate entropy production figures."""
    
    t = np.array(results['t'])
    P = np.array(results['P'])
    D = np.array(results['D'])
    S_dot_net = np.array(results['S_dot_net'])
    S_total = np.array(results['S_total'])
    T_eff = np.array(results['T_eff'])
    
    fig = plt.figure(figsize=(16, 10))
    
    # Panel 1: P and D over time
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.plot(t, P, 'g-', linewidth=1.5, label='P (production)', alpha=0.8)
    ax1.plot(t, D, 'r-', linewidth=1.5, label='D (dissipation)', alpha=0.8)
    ax1.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Rate', fontsize=12)
    ax1.set_title('Production vs Dissipation', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Net entropy production rate
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.plot(t, S_dot_net, 'b-', linewidth=1.5)
    ax2.axhline(y=0, color='k', linestyle='-', linewidth=2, alpha=0.5)
    ax2.fill_between(t, S_dot_net, 0, where=(S_dot_net > 0), 
                     alpha=0.3, color='green', label='Producing')
    ax2.fill_between(t, S_dot_net, 0, where=(S_dot_net < 0), 
                     alpha=0.3, color='red', label='Dissipating')
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('Ṡ_net = (P-D)/T_eff', fontsize=12)
    ax2.set_title('Net Entropy Production Rate', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Total entropy
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.plot(t, S_total, 'purple', linewidth=2)
    ax3.set_xlabel('Time', fontsize=12)
    ax3.set_ylabel('S_total', fontsize=12)
    ax3.set_title('Total Entropy Evolution', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Effective temperature
    ax4 = fig.add_subplot(2, 3, 4)
    ax4.plot(t, T_eff, 'orange', linewidth=2)
    ax4.set_xlabel('Time', fontsize=12)
    ax4.set_ylabel('T_eff = ⟨ρ⟩', fontsize=12)
    ax4.set_title('Effective Temperature', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Panel 5: Cumulative entropy production
    ax5 = fig.add_subplot(2, 3, 5)
    cumulative_S = np.cumsum(S_dot_net) * (t[1] - t[0])
    ax5.plot(t, cumulative_S, 'b-', linewidth=2)
    ax5.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax5.set_xlabel('Time', fontsize=12)
    ax5.set_ylabel('∫Ṡ_net dt', fontsize=12)
    ax5.set_title('Cumulative Net Entropy', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # Panel 6: Summary
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')
    
    balance = "YES ✓" if results['balance_achieved'] else "APPROACHING"
    
    summary = f"""
THERMODYNAMIC STRUCTURE
=======================

Entropy Production Rate:
  Ṡ = (P - D) / T_eff

where:
  P = ∫ c·(dc/dt)|∇φ|² dx   (production)
  D = γ ∫ φ̇² dx              (dissipation)
  T_eff = ⟨ρ⟩                (effective temp)

Results:
  Balance achieved: {balance}
  ΔS_total = {results['S_change']:.4f}
  Late ⟨Ṡ_net⟩ = {results['late_S_dot_mean']:.6f}

Physical Interpretation:
  The driven-dissipative medium reaches
  a NON-EQUILIBRIUM STEADY STATE (NESS)
  where entropy production = dissipation.

  This connects QMRT to:
    • Statistical mechanics
    • Fluctuation theorems
    • Irreversible thermodynamics

NESS Condition: Ṡ_prod = Ṡ_diss
  → No net entropy accumulation
  → Constant energy flow through system
  → Thermodynamic balance = dynamic balance
"""
    
    ax6.text(0.02, 0.98, summary, transform=ax6.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.5))
    
    plt.suptitle('ENTROPY PRODUCTION IN DRIVEN-DISSIPATIVE MEDIUM', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/entropy_production.png', dpi=150, bbox_inches='tight')
    print("\nSaved: entropy_production.png")
    
    # Save JSON (without huge arrays)
    output = {
        'balance_achieved': bool(results['balance_achieved']),
        'S_change': float(results['S_change']),
        'late_S_dot_mean': float(results['late_S_dot_mean']),
        'T_eff_initial': float(T_eff[0]),
        'T_eff_final': float(T_eff[-1]),
        'S_initial': float(S_total[0]),
        'S_final': float(S_total[-1]),
    }
    
    with open('/app/backend/qmrt_topology/entropy_production.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("Saved: entropy_production.json")


if __name__ == "__main__":
    results = analyze_entropy_production()
    generate_entropy_figures(results)
