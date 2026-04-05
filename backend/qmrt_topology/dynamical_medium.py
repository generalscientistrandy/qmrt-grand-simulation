#!/usr/bin/env python3
"""
QMRT Dynamical Medium Field Implementation
============================================

UPGRADE: Replace algebraic backreaction with a dynamical medium field.

CURRENT PROBLEM:
  c_eff = c_0 * f(ρ)  ← instantaneous, algebraic
  
  Energy instantly changes geometry → runaway feedback

NEW ARCHITECTURE:
  Wave field φ propagates on medium field τ
  Medium field τ has its own dynamics with relaxation
  c_eff = c(τ) is derived from medium state

EQUATIONS:
----------

Wave field:
  ∂²φ/∂t² = c(τ)² ∇²φ - γ_φ ∂φ/∂t

Medium field (relaxation dynamics):
  ∂τ/∂t = -λ(τ - τ_eq(ρ)) + D∇²τ

where:
  τ_eq(ρ) = τ_0 / (1 + β·ρ)  ← equilibrium medium state
  c(τ) = c_0 · τ / τ_0        ← wave speed from medium
  λ = relaxation rate
  D = medium diffusion

PHYSICAL MEANING:
  - τ stores geometry/structure
  - τ relaxes toward τ_eq(ρ), doesn't jump instantly
  - Introduces memory/inertia into the medium
  - Changing geometry has a time cost

MODIFIED EFFECTIVE ENERGY:
  E_eff = ∫ [½(∂φ/∂t)² + ½c(τ)²|∇φ|² + U(τ)] dx

where U(τ) = ½κ(τ - τ_0)² is the "cost" of distorting the medium.

GOAL:
  Show that lensing, attraction, and causal structure survive
  while energy growth is tamed.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


class DynamicalMediumSimulator:
    """
    Simulator with dynamical medium field.
    """
    
    def __init__(
        self,
        size: int = 100,
        c_0: float = 2.0,
        tau_0: float = 1.0,      # Reference medium state
        beta: float = 0.5,       # Coupling strength (energy → τ_eq)
        lambda_relax: float = 0.5,  # Relaxation rate
        D_medium: float = 0.1,   # Medium diffusion
        gamma_wave: float = 0.008,  # Wave damping
        kappa: float = 0.1,      # Medium distortion cost
        dt: float = 0.04,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.kappa = kappa
        self.dt = dt
        
        # Fields
        self.phi = np.zeros((size, size))      # Wave field
        self.phi_dot = np.zeros((size, size))  # Wave velocity
        self.tau = np.ones((size, size)) * tau_0  # Medium field
        
    def compute_c_eff(self):
        """Wave speed from medium state: c = c_0 · τ / τ_0"""
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        """Equilibrium medium state: τ_eq = τ_0 / (1 + β·ρ/ρ_max)"""
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        tau_eq = self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
        return tau_eq
    
    def compute_energy(self):
        """
        Modified effective energy:
        E_eff = ∫ [½v² + ½c(τ)²|∇φ|² + ½κ(τ - τ_0)²] dx
        """
        c_eff = self.compute_c_eff()
        
        # Kinetic energy
        kinetic = 0.5 * np.sum(self.phi_dot**2)
        
        # Gradient energy
        grad_x = np.roll(self.phi, 1, axis=0) - self.phi
        grad_y = np.roll(self.phi, 1, axis=1) - self.phi
        gradient = 0.5 * np.sum(c_eff**2 * (grad_x**2 + grad_y**2))
        
        # Medium distortion cost
        medium_cost = 0.5 * self.kappa * np.sum((self.tau - self.tau_0)**2)
        
        return kinetic + gradient + medium_cost
    
    def step(self):
        """
        Advance one timestep using coupled dynamics.
        """
        # Current energy density
        rho = self.phi**2 + self.phi_dot**2
        
        # 1. Update medium field (relaxation dynamics)
        # ∂τ/∂t = -λ(τ - τ_eq) + D∇²τ
        tau_eq = self.compute_tau_eq(rho)
        
        # Laplacian of τ
        lap_tau = (np.roll(self.tau, 1, axis=0) + np.roll(self.tau, -1, axis=0) +
                   np.roll(self.tau, 1, axis=1) + np.roll(self.tau, -1, axis=1) - 
                   4 * self.tau)
        
        # Medium relaxation
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)  # Bound medium state
        
        # 2. Update wave field
        # ∂²φ/∂t² = c(τ)² ∇²φ - γ ∂φ/∂t
        c_eff = self.compute_c_eff()
        
        lap_phi = (np.roll(self.phi, 1, axis=0) + np.roll(self.phi, -1, axis=0) +
                   np.roll(self.phi, 1, axis=1) + np.roll(self.phi, -1, axis=1) - 
                   4 * self.phi)
        
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center, amplitude=3.0, width=4.0, velocity=True):
        """Add a Gaussian pulse."""
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    if velocity:
                        self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
                    else:
                        self.phi[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))


def test_energy_behavior():
    """Test if energy growth is tamed."""
    print("Test 1: Energy Behavior")
    print("-" * 40)
    
    sim = DynamicalMediumSimulator(size=80, beta=0.5, lambda_relax=0.5)
    sim.add_pulse([40, 40], amplitude=3.0)
    
    initial_energy = sim.compute_energy()
    energies = [initial_energy]
    
    for t in range(400):
        sim.step()
        if t % 10 == 0:
            energies.append(sim.compute_energy())
    
    final_energy = energies[-1]
    ratio = final_energy / initial_energy
    
    print(f"  Initial energy: {initial_energy:.2f}")
    print(f"  Final energy: {final_energy:.2f}")
    print(f"  Ratio: {ratio:.2f}")
    
    return {
        'initial': initial_energy,
        'final': final_energy,
        'ratio': ratio,
        'history': np.array(energies),
    }


def test_lensing():
    """Test if lensing survives."""
    print("\nTest 2: Lensing Analog")
    print("-" * 40)
    
    sim = DynamicalMediumSimulator(size=150, beta=0.8, lambda_relax=0.3)
    
    # Lens (stationary energy concentration)
    lens_pos = np.array([75, 90])
    sim.add_pulse(lens_pos, amplitude=8.0, width=6.0, velocity=False)
    
    # Let medium settle around lens
    for _ in range(50):
        sim.step()
    
    # Probe
    probe_start = np.array([90, 22])  # Above center, moving right
    sim.add_pulse(probe_start, amplitude=0.5, width=3.0, velocity=True)
    
    # Track probe
    probe_positions = [probe_start.copy()]
    
    for t in range(600):
        sim.step()
        
        if t % 5 == 0:
            energy = sim.phi**2 + sim.phi_dot**2
            probe_energy = energy.copy()
            
            # Mask lens
            li, lj = int(lens_pos[0]), int(lens_pos[1])
            for di in range(-24, 25):
                for dj in range(-24, 25):
                    ni, nj = li + di, lj + dj
                    if 0 <= ni < 150 and 0 <= nj < 150:
                        probe_energy[ni, nj] = 0
            
            if np.max(probe_energy) > 0.01:
                probe_idx = np.unravel_index(np.argmax(probe_energy), probe_energy.shape)
                probe_positions.append(np.array(probe_idx, dtype=float))
    
    probe_positions = np.array(probe_positions)
    
    if len(probe_positions) > 10:
        deflection = probe_positions[-1][0] - probe_start[0]
        toward = deflection < 0  # Probe above lens should bend down
    else:
        deflection = 0
        toward = False
    
    status = "TOWARD" if toward else "away"
    print(f"  Probe deflection: {deflection:+.1f} pixels ({status})")
    
    return {
        'deflection': deflection,
        'toward_lens': toward,
        'positions': probe_positions,
        'tau_final': sim.tau.copy(),
    }


def test_attraction():
    """Test if attraction survives."""
    print("\nTest 3: Pulse Attraction")
    print("-" * 40)
    
    sim = DynamicalMediumSimulator(size=100, beta=0.8, lambda_relax=0.3)
    
    center = 50
    sep_pixels = 15
    
    sim.add_pulse([center, center - sep_pixels], amplitude=3.0)
    sim.add_pulse([center, center + sep_pixels], amplitude=3.0)
    
    initial_sep = 2 * sep_pixels
    
    for t in range(500):
        sim.step()
    
    # Find peaks
    energy = sim.phi**2 + sim.phi_dot**2
    energy_for_peaks = energy.copy()
    
    peak_A = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
    for di in range(-12, 13):
        for dj in range(-12, 13):
            ni, nj = peak_A[0] + di, peak_A[1] + dj
            if 0 <= ni < 100 and 0 <= nj < 100:
                energy_for_peaks[ni, nj] = 0
    
    peak_B = np.unravel_index(np.argmax(energy_for_peaks), energy.shape)
    
    final_sep = np.sqrt((peak_A[0] - peak_B[0])**2 + (peak_A[1] - peak_B[1])**2)
    delta_sep = final_sep - initial_sep
    attracted = delta_sep < -5
    
    status = "ATTRACT" if attracted else "spread"
    print(f"  Initial sep: {initial_sep:.0f}")
    print(f"  Final sep: {final_sep:.0f}")
    print(f"  Δsep: {delta_sep:+.1f} ({status})")
    
    return {
        'initial_sep': initial_sep,
        'final_sep': final_sep,
        'delta_sep': delta_sep,
        'attracted': attracted,
        'tau_final': sim.tau.copy(),
    }


def test_causal_cone():
    """Test causal cone confinement."""
    print("\nTest 4: Causal Cone")
    print("-" * 40)
    
    sim = DynamicalMediumSimulator(size=100, beta=0.5, lambda_relax=0.5)
    
    # Point source at center
    center = 50
    sim.phi_dot[center, center] = 10.0
    
    for t in range(200):
        sim.step()
    
    # Compute confinement
    energy = sim.phi**2 + sim.phi_dot**2
    total_time = 200 * sim.dt
    cone_radius = sim.c_0 * total_time
    
    y_coords, x_coords = np.meshgrid(range(100), range(100))
    r = np.sqrt((x_coords - center)**2 + (y_coords - center)**2)
    
    energy_in_cone = np.sum(energy[r <= cone_radius])
    energy_total = np.sum(energy)
    
    confinement = energy_in_cone / (energy_total + 1e-10) * 100
    
    print(f"  Confinement: {confinement:.1f}%")
    
    return {
        'confinement': confinement,
        'cone_radius': cone_radius,
    }


def run_dynamical_medium_test():
    """
    Main test: Dynamical medium field.
    """
    print("=" * 70)
    print("DYNAMICAL MEDIUM FIELD TEST")
    print("=" * 70)
    print()
    print("Architecture:")
    print("  Wave: ∂²φ/∂t² = c(τ)² ∇²φ - γ ∂φ/∂t")
    print("  Medium: ∂τ/∂t = -λ(τ - τ_eq(ρ)) + D∇²τ")
    print("  c(τ) = c_0 · τ / τ_0")
    print()
    
    results = {}
    
    # Run tests
    results['energy'] = test_energy_behavior()
    results['lensing'] = test_lensing()
    results['attraction'] = test_attraction()
    results['causal'] = test_causal_cone()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    e_ratio = results['energy']['ratio']
    lensing_ok = results['lensing']['toward_lens']
    attract_ok = results['attraction']['attracted']
    cone_ok = results['causal']['confinement'] > 80
    
    print(f"\n  Energy ratio: {e_ratio:.2f}")
    print(f"  Lensing: {'✓' if lensing_ok else '✗'}")
    print(f"  Attraction: {'✓' if attract_ok else '✗'}")
    print(f"  Causal cone: {'✓' if cone_ok else '✗'} ({results['causal']['confinement']:.0f}%)")
    
    # Verdict
    physics_preserved = sum([lensing_ok, attract_ok, cone_ok]) >= 2
    energy_improved = e_ratio < 50  # Much better than ~120 for original
    
    if physics_preserved and energy_improved:
        verdict = "SUCCESS: Physics preserved, energy tamed"
    elif physics_preserved:
        verdict = "PARTIAL: Physics preserved, energy still high"
    else:
        verdict = "NEEDS TUNING: Physics broken"
    
    print(f"\n  VERDICT: {verdict}")
    
    results['verdict'] = verdict
    results['physics_preserved'] = physics_preserved
    results['energy_improved'] = energy_improved
    
    # Plotting
    fig = plt.figure(figsize=(16, 12))
    
    # Energy evolution
    ax = fig.add_subplot(2, 3, 1)
    history = results['energy']['history']
    times = np.arange(len(history)) * 0.04 * 10
    ax.plot(times, history / history[0], 'b-', linewidth=2)
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Time')
    ax.set_ylabel('E / E₀')
    ax.set_title(f'Energy Evolution (ratio={e_ratio:.1f})')
    ax.grid(True, alpha=0.3)
    
    # Lensing trajectory
    ax = fig.add_subplot(2, 3, 2)
    pos = results['lensing']['positions']
    if len(pos) > 0:
        ax.plot(pos[:, 1], pos[:, 0], 'b-', linewidth=2)
        ax.scatter([90], [75], c='red', s=200, marker='*', label='Lens')
    ax.set_xlabel('Y')
    ax.set_ylabel('X')
    ax.set_title(f"Lensing: Δx={results['lensing']['deflection']:+.1f}")
    ax.legend()
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    # Medium field (τ) from lensing
    ax = fig.add_subplot(2, 3, 3)
    tau = results['lensing']['tau_final']
    im = ax.imshow(tau.T, origin='lower', cmap='viridis')
    ax.set_title('Medium Field τ (after lensing)')
    plt.colorbar(im, ax=ax, label='τ')
    
    # Attraction final τ
    ax = fig.add_subplot(2, 3, 4)
    tau = results['attraction']['tau_final']
    im = ax.imshow(tau.T, origin='lower', cmap='viridis')
    ax.set_title('Medium Field τ (after attraction)')
    plt.colorbar(im, ax=ax, label='τ')
    
    # Summary bars
    ax = fig.add_subplot(2, 3, 5)
    metrics = ['Energy\n(lower=better)', 'Lensing', 'Attraction', 'Cone']
    values = [min(e_ratio/100, 1.5), 1 if lensing_ok else 0, 1 if attract_ok else 0, 
              results['causal']['confinement']/100]
    colors = ['green' if v > 0.5 else 'red' for v in [1-e_ratio/200, lensing_ok, attract_ok, cone_ok]]
    ax.bar(metrics, values, color=colors)
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    ax.set_ylabel('Score (1=pass)')
    ax.set_title('Test Results')
    
    # Summary text
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
DYNAMICAL MEDIUM FIELD
======================

Architecture:
  Wave: ∂²φ/∂t² = c(τ)² ∇²φ
  Medium: ∂τ/∂t = -λ(τ - τ_eq) + D∇²τ

Results:
  Energy ratio: {e_ratio:.1f}
  Lensing: {'TOWARD' if lensing_ok else 'away'}
  Attraction: {'YES' if attract_ok else 'no'}
  Cone: {results['causal']['confinement']:.0f}%

VERDICT: {verdict}

Key insight:
  τ introduces memory/inertia
  Geometry changes have a time cost
  Runaway feedback is damped
"""
    ax.text(0.1, 0.9, summary, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', 
                    facecolor='lightgreen' if physics_preserved else 'lightyellow',
                    alpha=0.5))
    
    plt.suptitle(f'DYNAMICAL MEDIUM: {verdict}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/dynamical_medium.png', dpi=150, bbox_inches='tight')
    print("\nSaved dynamical_medium.png")
    
    # Save JSON
    summary_json = {
        'verdict': verdict,
        'energy_ratio': float(e_ratio),
        'lensing_toward': bool(lensing_ok),
        'lensing_deflection': float(results['lensing']['deflection']),
        'attraction': bool(attract_ok),
        'delta_sep': float(results['attraction']['delta_sep']),
        'cone_confinement': float(results['causal']['confinement']),
        'physics_preserved': bool(physics_preserved),
        'energy_improved': bool(energy_improved),
    }
    
    with open('/app/backend/qmrt_topology/dynamical_medium_results.json', 'w') as f:
        json.dump(summary_json, f, indent=2)
    print("Saved dynamical_medium_results.json")
    
    return results


if __name__ == "__main__":
    results = run_dynamical_medium_test()
