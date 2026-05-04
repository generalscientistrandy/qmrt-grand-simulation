"""
Decisive Tests for Stability Channel Co-Alignment
==================================================

Test 1: Steady-state vortex population under continuous driving
Test 2: Vortex drift via β-gradient energy landscape

Goal: Prove whether layers (2-4) can coexist in time, not just transiently.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple
import json

class EnergyLandscapeSimulator2D:
    """
    Complex scalar with β(x) in the energy functional.
    
    Key change: ∂²ψ = ∇·(β(x)∇ψ) - γ∂ₜψ
    
    This makes vortex cores (high |∇ψ|) feel the β landscape directly.
    Vortices should drift toward high-β (effective potential well).
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.01,
        lambda_relax: float = 0.5,
        beta_base: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.dt = dt
        
        # Complex field
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Medium
        self.tau = np.ones((size, size)) * tau_0
        
        # β field - THIS IS THE KEY
        self.beta_field = np.ones((size, size)) * beta_base
        self.lambda_field = np.ones((size, size)) * lambda_relax
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    @property
    def rho(self) -> np.ndarray:
        return self.psi_r**2 + self.psi_i**2 + self.psi_r_dot**2 + self.psi_i_dot**2
    
    def compute_c_eff(self) -> np.ndarray:
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho: np.ndarray) -> np.ndarray:
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta_field * rho_smooth / rho_max)
    
    def compute_beta_weighted_laplacian(self, f: np.ndarray) -> np.ndarray:
        """
        Compute ∇·(β(x)∇f) - the key modification.
        
        This is NOT just β * ∇²f. It's:
        ∇·(β∇f) = β∇²f + ∇β·∇f
        
        The second term creates a drift force toward high-β.
        """
        # Standard Laplacian
        lap_f = (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                 np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
        
        # Gradient of f
        df_dx = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) / 2
        df_dy = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / 2
        
        # Gradient of β
        dbeta_dx = (np.roll(self.beta_field, -1, 0) - np.roll(self.beta_field, 1, 0)) / 2
        dbeta_dy = (np.roll(self.beta_field, -1, 1) - np.roll(self.beta_field, 1, 1)) / 2
        
        # ∇·(β∇f) = β∇²f + ∇β·∇f
        return self.beta_field * lap_f + dbeta_dx * df_dx + dbeta_dy * df_dy
    
    def step(self):
        """Advance with β-weighted gradient energy."""
        rho = self.rho
        
        # Medium evolution
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_field * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave evolution with β-weighted Laplacian
        c_eff = self.compute_c_eff()
        c_eff_sq = c_eff**2
        
        # KEY: Use ∇·(β∇ψ) instead of just ∇²ψ
        weighted_lap_r = self.compute_beta_weighted_laplacian(self.psi_r)
        weighted_lap_i = self.compute_beta_weighted_laplacian(self.psi_i)
        
        acc_r = c_eff_sq * weighted_lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * weighted_lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def add_continuous_driving(self, amplitude: float = 0.01):
        """Add low-amplitude uniform noise (continuous driving)."""
        self.psi_r_dot += np.random.uniform(-amplitude, amplitude, (self.size, self.size))
        self.psi_i_dot += np.random.uniform(-amplitude, amplitude, (self.size, self.size))
    
    def set_biased_region(self, center: Tuple[int, int], radius: float,
                          beta_inside: float, beta_outside: float):
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        inside = r <= radius
        self.beta_field[inside] = beta_inside
        self.beta_field[~inside] = beta_outside
    
    def set_beta_gradient(self, direction: str = 'x', beta_low: float = 0.2, beta_high: float = 0.8):
        """Create linear β gradient for drift test."""
        if direction == 'x':
            for i in range(self.size):
                self.beta_field[i, :] = beta_low + (beta_high - beta_low) * i / self.size
        else:
            for j in range(self.size):
                self.beta_field[:, j] = beta_low + (beta_high - beta_low) * j / self.size
    
    def add_vortex(self, center: Tuple[int, int], charge: int = 1, 
                   amplitude: float = 1.0, core_radius: float = 3.0):
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        dx = x - center[0]
        dy = y - center[1]
        r = np.sqrt(dx**2 + dy**2 + 0.01)
        theta = np.arctan2(dy, dx)
        
        amp_profile = amplitude * np.tanh(r / core_radius)
        phase = charge * theta
        
        if np.max(np.abs(self.psi_r)) < 0.01:
            self.psi_r = amp_profile * np.cos(phase)
            self.psi_i = amp_profile * np.sin(phase)
        else:
            psi_existing = self.psi_r + 1j * self.psi_i
            psi_vortex = amp_profile * np.exp(1j * phase)
            combined = psi_existing * psi_vortex / (amplitude + 0.01)
            self.psi_r = np.real(combined)
            self.psi_i = np.imag(combined)
    
    def compute_winding_number(self, i: int, j: int, radius: int = 2) -> float:
        phase = self.phase
        loop_points = []
        for dj in range(-radius, radius+1):
            loop_points.append((i-radius, j+dj))
        for di in range(-radius+1, radius+1):
            loop_points.append((i+di, j+radius))
        for dj in range(radius-1, -radius-1, -1):
            loop_points.append((i+radius, j+dj))
        for di in range(radius-1, -radius, -1):
            loop_points.append((i+di, j-radius))
        
        total = 0
        for k in range(len(loop_points)):
            ni, nj = loop_points[k]
            ni_next, nj_next = loop_points[(k+1) % len(loop_points)]
            ni, nj = ni % self.size, nj % self.size
            ni_next, nj_next = ni_next % self.size, nj_next % self.size
            
            dp = phase[ni_next, nj_next] - phase[ni, nj]
            while dp > np.pi: dp -= 2*np.pi
            while dp < -np.pi: dp += 2*np.pi
            total += dp
        
        return total / (2*np.pi)
    
    def detect_vortices(self, amplitude_threshold: float = 0.3) -> List[Dict]:
        vortices = []
        amp = self.amplitude
        
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                local_amp = amp[i, j]
                region = amp[i-1:i+2, j-1:j+2]
                
                if local_amp <= np.min(region) and local_amp < amplitude_threshold:
                    winding = self.compute_winding_number(i, j, radius=2)
                    if abs(winding) > 0.5:
                        vortices.append({
                            'position': [i, j],
                            'charge': int(np.round(winding)),
                            'beta': float(self.beta_field[i, j])
                        })
        return vortices


# ============================================================
# TEST 1: Steady-state vortex population under continuous driving
# ============================================================

def test_steady_state_vortex_population():
    """
    Add continuous low-amplitude driving.
    Measure: Does vortex density plateau higher in high-β regions?
    """
    print("="*70)
    print("TEST 1: STEADY-STATE VORTEX POPULATION")
    print("="*70)
    print()
    print("Question: Can continuous driving maintain vortex population?")
    print("          Does n_vortices plateau higher in high-β?")
    print()
    
    size = 100
    center = (size//2, size//2)
    radius = 25
    steps = 8000
    driving_interval = 50
    driving_amplitude = 0.05
    
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    inside_mask = r <= radius
    
    results = {}
    
    for use_beta_energy in [False, True]:
        label = "β-weighted" if use_beta_energy else "standard"
        print(f"--- {label} Laplacian ---")
        
        sim = EnergyLandscapeSimulator2D(size=size, gamma=0.008, D_medium=0.02)
        sim.set_biased_region(center, radius, beta_inside=0.8, beta_outside=0.2)
        
        # Background
        sim.psi_r[:] = 1.5
        
        # Track vortex counts over time
        counts_inside = []
        counts_outside = []
        counts_total = []
        
        for step in range(steps):
            # Continuous driving
            if step % driving_interval == 0:
                sim.add_continuous_driving(amplitude=driving_amplitude)
            
            if use_beta_energy:
                sim.step()
            else:
                # Standard step without β-weighting
                rho = sim.rho
                tau_eq = sim.compute_tau_eq(rho)
                lap_tau = (np.roll(sim.tau, 1, 0) + np.roll(sim.tau, -1, 0) +
                           np.roll(sim.tau, 1, 1) + np.roll(sim.tau, -1, 1) - 4*sim.tau)
                dtau_dt = -sim.lambda_field * (sim.tau - tau_eq) + sim.D_medium * lap_tau
                sim.tau += dtau_dt * sim.dt
                sim.tau = np.clip(sim.tau, 0.1, 2.0)
                
                c_eff = sim.compute_c_eff()
                lap_r = (np.roll(sim.psi_r, 1, 0) + np.roll(sim.psi_r, -1, 0) +
                         np.roll(sim.psi_r, 1, 1) + np.roll(sim.psi_r, -1, 1) - 4*sim.psi_r)
                lap_i = (np.roll(sim.psi_i, 1, 0) + np.roll(sim.psi_i, -1, 0) +
                         np.roll(sim.psi_i, 1, 1) + np.roll(sim.psi_i, -1, 1) - 4*sim.psi_i)
                
                acc_r = c_eff**2 * lap_r - sim.gamma * sim.psi_r_dot
                acc_i = c_eff**2 * lap_i - sim.gamma * sim.psi_i_dot
                
                sim.psi_r_dot += acc_r * sim.dt
                sim.psi_i_dot += acc_i * sim.dt
                sim.psi_r += sim.psi_r_dot * sim.dt
                sim.psi_i += sim.psi_i_dot * sim.dt
            
            if step % 100 == 0:
                vortices = sim.detect_vortices(amplitude_threshold=0.5)
                n_in = sum(1 for v in vortices if inside_mask[v['position'][0], v['position'][1]])
                n_out = len(vortices) - n_in
                counts_inside.append(n_in)
                counts_outside.append(n_out)
                counts_total.append(len(vortices))
        
        # Late-time statistics
        late_inside = np.mean(counts_inside[-20:])
        late_outside = np.mean(counts_outside[-20:])
        late_total = np.mean(counts_total[-20:])
        
        area_in = np.sum(inside_mask)
        area_out = size*size - area_in
        density_ratio = (late_inside / area_in) / (late_outside / area_out + 1e-10)
        
        results[label] = {
            'late_inside': late_inside,
            'late_outside': late_outside,
            'late_total': late_total,
            'density_ratio': density_ratio,
            'time_series_total': counts_total
        }
        
        print(f"  Late vortices inside: {late_inside:.2f}")
        print(f"  Late vortices outside: {late_outside:.2f}")
        print(f"  Density ratio: {density_ratio:.2f}")
        print()
    
    print("="*70)
    print("STEADY-STATE RESULTS")
    print("="*70)
    print()
    print("| Laplacian | Inside | Outside | Density Ratio |")
    print("|-----------|--------|---------|---------------|")
    for label in ['standard', 'β-weighted']:
        r = results[label]
        print(f"| {label:12} | {r['late_inside']:.2f} | {r['late_outside']:.2f} | {r['density_ratio']:.2f} |")
    
    improvement = results['β-weighted']['density_ratio'] / (results['standard']['density_ratio'] + 0.01)
    print()
    if improvement > 1.3:
        print(f"✓ β-WEIGHTING IMPROVES DENSITY RATIO: {improvement:.2f}x improvement")
    else:
        print(f"  No significant improvement from β-weighting")
    
    return results


# ============================================================
# TEST 2: Vortex drift via β-gradient
# ============================================================

def test_vortex_drift():
    """
    Create linear β gradient.
    Initialize vortex in low-β region.
    Track: Does it drift toward high-β?
    """
    print()
    print("="*70)
    print("TEST 2: VORTEX DRIFT VIA β-GRADIENT")
    print("="*70)
    print()
    print("Question: Do vortices drift toward high-β regions?")
    print()
    
    size = 80
    steps = 3000
    
    results = {}
    
    for use_beta_energy in [False, True]:
        label = "β-weighted" if use_beta_energy else "standard"
        print(f"--- {label} Laplacian ---")
        
        sim = EnergyLandscapeSimulator2D(size=size, gamma=0.005, D_medium=0.02)
        
        # Linear β gradient: low at x=0, high at x=size
        sim.set_beta_gradient(direction='x', beta_low=0.2, beta_high=0.8)
        
        # Background + vortex in LOW-β region (left side)
        sim.psi_r[:] = 1.5
        initial_pos = (15, size//2)  # Low-β region
        sim.add_vortex(initial_pos, charge=1, amplitude=1.5, core_radius=4.0)
        
        initial_beta = sim.beta_field[initial_pos[0], initial_pos[1]]
        print(f"  Initial position: {initial_pos}, β = {initial_beta:.2f}")
        
        # Track trajectory
        positions = [initial_pos]
        betas = [initial_beta]
        
        for step in range(steps):
            if use_beta_energy:
                sim.step()
            else:
                # Standard step
                rho = sim.rho
                tau_eq = sim.compute_tau_eq(rho)
                lap_tau = (np.roll(sim.tau, 1, 0) + np.roll(sim.tau, -1, 0) +
                           np.roll(sim.tau, 1, 1) + np.roll(sim.tau, -1, 1) - 4*sim.tau)
                dtau_dt = -sim.lambda_field * (sim.tau - tau_eq) + sim.D_medium * lap_tau
                sim.tau += dtau_dt * sim.dt
                sim.tau = np.clip(sim.tau, 0.1, 2.0)
                
                c_eff = sim.compute_c_eff()
                lap_r = (np.roll(sim.psi_r, 1, 0) + np.roll(sim.psi_r, -1, 0) +
                         np.roll(sim.psi_r, 1, 1) + np.roll(sim.psi_r, -1, 1) - 4*sim.psi_r)
                lap_i = (np.roll(sim.psi_i, 1, 0) + np.roll(sim.psi_i, -1, 0) +
                         np.roll(sim.psi_i, 1, 1) + np.roll(sim.psi_i, -1, 1) - 4*sim.psi_i)
                
                acc_r = c_eff**2 * lap_r - sim.gamma * sim.psi_r_dot
                acc_i = c_eff**2 * lap_i - sim.gamma * sim.psi_i_dot
                
                sim.psi_r_dot += acc_r * sim.dt
                sim.psi_i_dot += acc_i * sim.dt
                sim.psi_r += sim.psi_r_dot * sim.dt
                sim.psi_i += sim.psi_i_dot * sim.dt
            
            if step % 100 == 0:
                vortices = sim.detect_vortices(amplitude_threshold=0.5)
                if vortices:
                    v = vortices[0]
                    pos = tuple(v['position'])
                    positions.append(pos)
                    betas.append(v['beta'])
        
        if len(positions) > 1:
            # Analyze drift
            x_positions = [p[0] for p in positions]
            initial_x = x_positions[0]
            final_x = x_positions[-1] if x_positions else initial_x
            drift = final_x - initial_x
            
            initial_beta = betas[0]
            final_beta = betas[-1] if betas else initial_beta
            beta_change = final_beta - initial_beta
            
            results[label] = {
                'initial_x': initial_x,
                'final_x': final_x,
                'drift': drift,
                'initial_beta': initial_beta,
                'final_beta': final_beta,
                'beta_change': beta_change,
                'n_tracked': len(positions)
            }
            
            print(f"  Final position x: {final_x:.1f}")
            print(f"  Drift (Δx): {drift:+.1f}")
            print(f"  β change: {initial_beta:.2f} → {final_beta:.2f}")
        else:
            print(f"  Vortex lost immediately")
            results[label] = {'drift': 0, 'error': 'lost'}
    
    print()
    print("="*70)
    print("DRIFT RESULTS")
    print("="*70)
    print()
    print("| Laplacian | Δx (drift) | β change |")
    print("|-----------|------------|----------|")
    for label in ['standard', 'β-weighted']:
        r = results.get(label, {})
        drift = r.get('drift', 0)
        beta_change = r.get('beta_change', 0)
        print(f"| {label:12} | {drift:+.1f} | {beta_change:+.2f} |")
    
    print()
    std_drift = results.get('standard', {}).get('drift', 0)
    beta_drift = results.get('β-weighted', {}).get('drift', 0)
    
    if beta_drift > std_drift + 5 and beta_drift > 5:
        print(f"✓ DRIFT TOWARD HIGH-β: β-weighted shows drift = {beta_drift:+.1f}")
    elif beta_drift < std_drift - 5:
        print(f"  Unexpected: β-weighted shows LESS drift")
    else:
        print(f"  No significant drift difference")
    
    return results


# ============================================================
# TEST 3: Annihilation location preference
# ============================================================

def test_annihilation_location():
    """
    Create vortex-antivortex pairs.
    Track: Do they annihilate inside or outside high-β regions?
    """
    print()
    print("="*70)
    print("TEST 3: ANNIHILATION LOCATION")
    print("="*70)
    print()
    print("Question: Does annihilation happen preferentially inside or outside high-β?")
    print()
    
    size = 100
    center = (size//2, size//2)
    radius = 25
    n_trials = 10
    
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    inside_mask = r <= radius
    
    results = {'inside': 0, 'outside': 0, 'unknown': 0}
    
    for trial in range(n_trials):
        np.random.seed(200 + trial)
        
        sim = EnergyLandscapeSimulator2D(size=size, gamma=0.008, D_medium=0.02)
        sim.set_biased_region(center, radius, beta_inside=0.8, beta_outside=0.2)
        sim.psi_r[:] = 1.5
        
        # Create vortex-antivortex pair straddling boundary
        # One inside, one outside
        v1_pos = (center[0], center[1] - 10)  # Inside
        v2_pos = (center[0], center[1] + radius + 10)  # Outside
        
        sim.add_vortex(v1_pos, charge=1, amplitude=1.5, core_radius=4.0)
        sim.add_vortex(v2_pos, charge=-1, amplitude=1.5, core_radius=4.0)
        
        # Track until annihilation
        last_positions = None
        annihilation_location = 'unknown'
        
        for step in range(3000):
            sim.step()
            
            if step % 50 == 0:
                vortices = sim.detect_vortices(amplitude_threshold=0.5)
                
                if len(vortices) >= 2:
                    # Find +1 and -1
                    pos_v = [v for v in vortices if v['charge'] > 0]
                    neg_v = [v for v in vortices if v['charge'] < 0]
                    if pos_v and neg_v:
                        last_positions = (pos_v[0]['position'], neg_v[0]['position'])
                elif len(vortices) < 2 and last_positions:
                    # Annihilation happened - where?
                    p1, p2 = last_positions
                    midpoint = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
                    if inside_mask[midpoint[0], midpoint[1]]:
                        annihilation_location = 'inside'
                    else:
                        annihilation_location = 'outside'
                    break
        
        results[annihilation_location] += 1
    
    print(f"Annihilation locations (n={n_trials}):")
    print(f"  Inside high-β: {results['inside']}")
    print(f"  Outside high-β: {results['outside']}")
    print(f"  Unknown: {results['unknown']}")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*70)
    print("DECISIVE TESTS FOR STABILITY CHANNEL CO-ALIGNMENT")
    print("="*70)
    print()
    
    steady_results = test_steady_state_vortex_population()
    drift_results = test_vortex_drift()
    # annihilation_results = test_annihilation_location()  # Optional
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("Test 1 (Steady-state): ", end="")
    if steady_results['β-weighted']['density_ratio'] > steady_results['standard']['density_ratio'] * 1.3:
        print("✓ β-weighting improves vortex density ratio")
    else:
        print("Inconclusive")
    
    print("Test 2 (Drift): ", end="")
    std_drift = drift_results.get('standard', {}).get('drift', 0)
    beta_drift = drift_results.get('β-weighted', {}).get('drift', 0)
    if beta_drift > std_drift + 5:
        print(f"✓ Vortices drift toward high-β (Δx = {beta_drift:+.1f})")
    else:
        print("No clear drift toward high-β")
    
    print()
    print("If both tests pass → Layers (2-4) can co-exist")
    print("This is evidence for potential composite stability (Layer 5)")
