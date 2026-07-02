"""
Mesoscopic Substrate with Yoshida 4th-Order Integrator
======================================================

Apply the Yoshida integrator to the mesoscopic substrate
to see if it improves energy conservation.

Author: QMRT Research
Date: December 2025
"""

import numpy as np
import sys
sys.path.insert(0, '/app/backend/archive/experiments')

from mesoscopic_substrate import MesoscopicSubstrate


# Yoshida coefficients
YOSHIDA_W0 = -2**(1/3) / (2 - 2**(1/3))
YOSHIDA_W1 = 1 / (2 - 2**(1/3))
YOSHIDA_C = [YOSHIDA_W1/2, (YOSHIDA_W0+YOSHIDA_W1)/2, (YOSHIDA_W0+YOSHIDA_W1)/2, YOSHIDA_W1/2]
YOSHIDA_D = [YOSHIDA_W1, YOSHIDA_W0, YOSHIDA_W1]


class MesoscopicYoshida(MesoscopicSubstrate):
    """Mesoscopic substrate with Yoshida 4th-order integration."""
    
    def _compute_accelerations(self):
        """Compute all field accelerations."""
        # Spatial derivatives
        lap_rho = self.laplacian(self.rho_xi)
        lap_T = self.laplacian(self.T_xi)
        lap_tau = self.laplacian(self.tau_xi)
        lap_phi = self.laplacian(self.phi_xi)
        
        curl_tau = self.curl(self.tau_xi)
        curl_curl_tau = self.curl(curl_tau)
        
        # Conservative accelerations
        a_rho = self.c_xi**2 * lap_rho + self.alpha * lap_T
        a_T = self.c_xi**2 * lap_T + self.alpha * lap_rho
        a_tau = self.c_xi**2 * lap_tau + self.beta * curl_curl_tau
        a_phi = self.c_xi**2 * lap_phi + self.gamma * lap_phi
        
        # Weak nonlinear terms
        rho_deviation = self.rho_xi - 1.0
        tau_mag_sq = np.sum(self.tau_xi**2, axis=-1, keepdims=True)
        a_rho += self.nonlinear_rho * rho_deviation * (lap_rho * 0.1)
        a_tau += self.nonlinear_tau * (tau_mag_sq / (1.0 + tau_mag_sq)) * lap_tau
        
        return a_rho, a_T, a_tau, a_phi
    
    def _position_step(self, c, dt):
        """Position update."""
        self.rho_xi += c * dt * self.v_rho
        self.T_xi += c * dt * self.v_T
        self.tau_xi += c * dt * self.v_tau
        self.phi_xi += c * dt * self.v_phi
    
    def _velocity_step(self, d, dt):
        """Velocity update."""
        a_rho, a_T, a_tau, a_phi = self._compute_accelerations()
        self.v_rho += d * dt * a_rho
        self.v_T += d * dt * a_T
        self.v_tau += d * dt * a_tau
        self.v_phi += d * dt * a_phi
    
    def evolve_yoshida(self, dt):
        """Yoshida 4th-order step."""
        if self.initial_energy is None:
            self.initial_energy = self._compute_total_energy()
        
        # Yoshida composition
        self._position_step(YOSHIDA_C[0], dt)
        self._velocity_step(YOSHIDA_D[0], dt)
        self._position_step(YOSHIDA_C[1], dt)
        self._velocity_step(YOSHIDA_D[1], dt)
        self._position_step(YOSHIDA_C[2], dt)
        self._velocity_step(YOSHIDA_D[2], dt)
        self._position_step(YOSHIDA_C[3], dt)
        
        self._sanitize_fields()
        self.time += dt
        
        tau_norm = np.linalg.norm(self.tau_xi, axis=-1)
        current_energy = self._compute_total_energy()
        
        return {
            'time': self._safe_float(self.time),
            'total_energy': self._safe_float(current_energy),
            'energy_drift': self._safe_float((current_energy - self.initial_energy) / max(abs(self.initial_energy), 1e-10)),
            'mean_density': self._safe_float(np.mean(self.rho_xi)),
        }


def compare_mesoscopic_integrators():
    """Compare Verlet vs Yoshida for mesoscopic substrate."""
    
    print("=" * 70)
    print("  MESOSCOPIC SUBSTRATE: Verlet vs Yoshida Comparison")
    print("=" * 70)
    print()
    
    dt = 0.05
    n_steps = 300
    
    # Verlet (original evolve_timestep)
    print("  Running Verlet...")
    sub_verlet = MesoscopicSubstrate(grid_size=32)
    sub_verlet.initialize_balanced_fluctuations(amplitude=0.1, seed=42)
    
    verlet_initial = None
    for step in range(n_steps):
        metrics = sub_verlet.evolve_timestep(dt)
        if step == 0:
            verlet_initial = metrics['total_energy']
    verlet_final = metrics['total_energy']
    verlet_drift = (verlet_final - verlet_initial) / verlet_initial * 100
    
    # Yoshida
    print("  Running Yoshida...")
    sub_yoshida = MesoscopicYoshida(grid_size=32)
    sub_yoshida.initialize_balanced_fluctuations(amplitude=0.1, seed=42)
    
    yoshida_initial = None
    for step in range(n_steps):
        metrics = sub_yoshida.evolve_yoshida(dt)
        if step == 0:
            yoshida_initial = metrics['total_energy']
    yoshida_final = metrics['total_energy']
    yoshida_drift = (yoshida_final - yoshida_initial) / yoshida_initial * 100
    
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print()
    print(f"  Verlet (2nd order):")
    print(f"    Initial: {verlet_initial:.2f}")
    print(f"    Final:   {verlet_final:.2f}")
    print(f"    Drift:   {verlet_drift:+.2f}%")
    print()
    print(f"  Yoshida (4th order):")
    print(f"    Initial: {yoshida_initial:.2f}")
    print(f"    Final:   {yoshida_final:.2f}")
    print(f"    Drift:   {yoshida_drift:+.2f}%")
    print()
    
    if abs(yoshida_drift) < abs(verlet_drift):
        improvement = abs(verlet_drift) / abs(yoshida_drift) if yoshida_drift != 0 else float('inf')
        print(f"  Yoshida is {improvement:.1f}× better")
    else:
        print("  Yoshida did not improve conservation")
    
    print()
    
    # Analysis
    print("=" * 70)
    print("  ANALYSIS")
    print("=" * 70)
    print()
    
    if abs(yoshida_drift) > 100:
        print("  The mesoscopic substrate has DIFFERENT energy dynamics:")
        print("  - Multiple coupled fields (ρ, T, τ, Φ)")
        print("  - Non-conservative coupling terms")
        print("  - Energy naturally flows between field types")
        print()
        print("  The validated τ-energy sink applies to the WAVE simulator,")
        print("  not this multi-field mesoscopic model.")
        print()
        print("  Options:")
        print("  1. Derive the correct Hamiltonian for the 4-field system")
        print("  2. Keep the original rescaling for mesoscopic model only")
        print("  3. Use the wave simulator (validated) for physics tests")


if __name__ == "__main__":
    compare_mesoscopic_integrators()
