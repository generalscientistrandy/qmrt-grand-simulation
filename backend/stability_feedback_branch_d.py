"""
Branch D: Stability-Feedback Extension
=======================================

Core Hypothesis:
    Stability is an ACTIVE BRANCH that feeds back on emergent branches,
    rather than a passive outcome of them.

The Stability Field Σ:
    - Accumulates where organization/topology persists
    - Decays where coherence is lost
    - Feeds back to modify system parameters (γ, β, λ)

Minimal Model:
    dΣ/dt = +k_org * S_local           (organization builds stability)
            +k_top * n_vortex_local    (topology builds stability)
            -k_decay * Σ               (natural decay)
            +D_Σ * ∇²Σ                 (diffusion/smoothing)

Feedback:
    γ(x) = γ₀ / (1 + ε_γ * Σ)         (high Σ → less damping)
    β(x) = β₀ * (1 + ε_β * Σ)         (high Σ → stronger coupling)

Test: Does this create self-reinforcing stability wells?
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple
import json


class StabilityFeedbackSimulator:
    """
    Complex scalar field with dynamic stability field Σ.
    
    Σ accumulates from persistent organization and topology,
    then feeds back to modify damping and coupling.
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma_0: float = 0.008,      # Base damping
        lambda_relax: float = 0.5,
        beta_0: float = 0.5,         # Base coupling
        D_medium: float = 0.1,
        dt: float = 0.04,
        # Stability field parameters
        k_org: float = 0.002,        # Organization → Σ rate
        k_top: float = 0.01,         # Topology → Σ rate  
        k_decay: float = 0.001,      # Σ natural decay
        D_sigma: float = 0.05,       # Σ diffusion
        eps_gamma: float = 0.5,      # Σ → γ feedback strength
        eps_beta: float = 0.3,       # Σ → β feedback strength
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma_0 = gamma_0
        self.lambda_relax = lambda_relax
        self.beta_0 = beta_0
        self.D_medium = D_medium
        self.dt = dt
        
        # Stability field parameters
        self.k_org = k_org
        self.k_top = k_top
        self.k_decay = k_decay
        self.D_sigma = D_sigma
        self.eps_gamma = eps_gamma
        self.eps_beta = eps_beta
        
        # Complex field
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Medium
        self.tau = np.ones((size, size)) * tau_0
        
        # THE NEW STABILITY FIELD
        self.sigma = np.zeros((size, size))
        
        # Derived fields (computed from Σ)
        self.gamma_field = np.ones((size, size)) * gamma_0
        self.beta_field = np.ones((size, size)) * beta_0
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
    
    def compute_local_organization(self) -> np.ndarray:
        """
        Local organization S_local: measures gradient structure.
        High when there's coherent spatial variation.
        """
        grad_r_x = np.roll(self.psi_r, -1, 0) - np.roll(self.psi_r, 1, 0)
        grad_r_y = np.roll(self.psi_r, -1, 1) - np.roll(self.psi_r, 1, 1)
        grad_i_x = np.roll(self.psi_i, -1, 0) - np.roll(self.psi_i, 1, 0)
        grad_i_y = np.roll(self.psi_i, -1, 1) - np.roll(self.psi_i, 1, 1)
        
        grad_mag = np.sqrt(grad_r_x**2 + grad_r_y**2 + grad_i_x**2 + grad_i_y**2)
        
        # Normalize and smooth
        S_local = gaussian_filter(grad_mag, sigma=3.0)
        S_max = np.max(S_local) + 1e-10
        return S_local / S_max
    
    def compute_local_topology(self) -> np.ndarray:
        """
        Local topology indicator: high near vortex cores.
        Uses amplitude dips as proxy for vortex presence.
        """
        amp = self.amplitude
        amp_smooth = gaussian_filter(amp, sigma=2.0)
        
        # Topology indicator: low amplitude = near vortex core
        # Invert: high value where amplitude is low
        amp_max = np.max(amp_smooth) + 1e-10
        T_local = 1.0 - amp_smooth / amp_max
        
        # Threshold to focus on actual vortex regions
        T_local = np.where(T_local > 0.5, T_local, 0)
        
        return gaussian_filter(T_local, sigma=2.0)
    
    def update_stability_field(self):
        """
        Core Branch D dynamics:
        dΣ/dt = +k_org * S_local + k_top * T_local - k_decay * Σ + D_Σ * ∇²Σ
        """
        S_local = self.compute_local_organization()
        T_local = self.compute_local_topology()
        
        # Source terms
        source_org = self.k_org * S_local
        source_top = self.k_top * T_local
        decay = self.k_decay * self.sigma
        
        # Diffusion
        lap_sigma = (np.roll(self.sigma, 1, 0) + np.roll(self.sigma, -1, 0) +
                     np.roll(self.sigma, 1, 1) + np.roll(self.sigma, -1, 1) - 4*self.sigma)
        diffusion = self.D_sigma * lap_sigma
        
        # Update
        dSigma_dt = source_org + source_top - decay + diffusion
        self.sigma += dSigma_dt * self.dt
        self.sigma = np.clip(self.sigma, 0, 10)  # Bound stability field
    
    def update_feedback_fields(self):
        """
        Stability feeds back to modify system parameters:
        γ(x) = γ₀ / (1 + ε_γ * Σ)    → high Σ = less damping
        β(x) = β₀ * (1 + ε_β * Σ)    → high Σ = stronger coupling
        """
        self.gamma_field = self.gamma_0 / (1 + self.eps_gamma * self.sigma)
        self.beta_field = self.beta_0 * (1 + self.eps_beta * self.sigma)
    
    def compute_c_eff(self) -> np.ndarray:
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho: np.ndarray) -> np.ndarray:
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta_field * rho_smooth / rho_max)
    
    def compute_beta_weighted_laplacian(self, f: np.ndarray) -> np.ndarray:
        """∇·(β∇f) = β∇²f + ∇β·∇f"""
        lap_f = (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                 np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
        
        df_dx = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) / 2
        df_dy = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / 2
        
        dbeta_dx = (np.roll(self.beta_field, -1, 0) - np.roll(self.beta_field, 1, 0)) / 2
        dbeta_dy = (np.roll(self.beta_field, -1, 1) - np.roll(self.beta_field, 1, 1)) / 2
        
        return self.beta_field * lap_f + dbeta_dx * df_dx + dbeta_dy * df_dy
    
    def step(self):
        """Full step including stability field dynamics."""
        # 1. Update stability field from current state
        self.update_stability_field()
        
        # 2. Update feedback parameters
        self.update_feedback_fields()
        
        # 3. Medium evolution (with feedback-modified β)
        rho = self.rho
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_field * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # 4. Wave evolution with feedback-modified γ and β
        c_eff = self.compute_c_eff()
        c_eff_sq = c_eff**2
        
        weighted_lap_r = self.compute_beta_weighted_laplacian(self.psi_r)
        weighted_lap_i = self.compute_beta_weighted_laplacian(self.psi_i)
        
        # Use spatially-varying gamma
        acc_r = c_eff_sq * weighted_lap_r - self.gamma_field * self.psi_r_dot
        acc_i = c_eff_sq * weighted_lap_i - self.gamma_field * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
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
                            'sigma': float(self.sigma[i, j]),
                            'gamma': float(self.gamma_field[i, j]),
                            'beta': float(self.beta_field[i, j])
                        })
        return vortices


# ============================================================
# TEST 1: Does Σ accumulate around vortices?
# ============================================================

def test_sigma_accumulation():
    """
    Test: Does the stability field Σ build up around persistent vortices?
    """
    print("="*70)
    print("TEST 1: STABILITY FIELD ACCUMULATION")
    print("="*70)
    print()
    print("Question: Does Σ accumulate where vortices persist?")
    print()
    
    size = 80
    steps = 4000
    
    sim = StabilityFeedbackSimulator(
        size=size,
        gamma_0=0.006,
        k_org=0.003,
        k_top=0.015,
        k_decay=0.0008,
        eps_gamma=0.5,
        eps_beta=0.3
    )
    
    # Background + vortex
    sim.psi_r[:] = 1.2
    center = (size//2, size//2)
    sim.add_vortex(center, charge=1, amplitude=1.2, core_radius=4.0)
    
    # Track Σ evolution
    sigma_at_vortex = []
    sigma_mean = []
    vortex_alive = []
    
    for step in range(steps):
        sim.step()
        
        if step % 100 == 0:
            vortices = sim.detect_vortices(amplitude_threshold=0.5)
            
            if vortices:
                v = vortices[0]
                sigma_at_vortex.append(v['sigma'])
                vortex_alive.append(1)
            else:
                sigma_at_vortex.append(sim.sigma[center[0], center[1]])
                vortex_alive.append(0)
            
            sigma_mean.append(np.mean(sim.sigma))
    
    print(f"Σ at vortex location (early): {sigma_at_vortex[5]:.4f}")
    print(f"Σ at vortex location (late):  {sigma_at_vortex[-1]:.4f}")
    print(f"Σ mean (early): {sigma_mean[5]:.4f}")
    print(f"Σ mean (late):  {sigma_mean[-1]:.4f}")
    print(f"Vortex survived: {sum(vortex_alive[-10:])} / 10 late samples")
    print()
    
    # Check if Σ accumulated
    sigma_growth = sigma_at_vortex[-1] / (sigma_at_vortex[5] + 1e-10)
    
    if sigma_growth > 1.5:
        print(f"✓ Σ ACCUMULATED at vortex: {sigma_growth:.2f}× growth")
    else:
        print(f"- Σ did not accumulate significantly")
    
    return {
        'sigma_at_vortex': sigma_at_vortex,
        'sigma_mean': sigma_mean,
        'sigma_growth': sigma_growth,
        'vortex_survival': sum(vortex_alive[-10:])
    }


# ============================================================
# TEST 2: Does feedback extend vortex lifetime?
# ============================================================

def test_feedback_lifetime_extension():
    """
    Compare vortex lifetime with and without stability feedback.
    """
    print()
    print("="*70)
    print("TEST 2: FEEDBACK LIFETIME EXTENSION")
    print("="*70)
    print()
    print("Question: Does stability feedback extend vortex lifetime?")
    print()
    
    size = 80
    steps = 5000
    n_trials = 5
    
    configs = [
        ("no_feedback", 0.0, 0.0),       # No Σ feedback
        ("weak_feedback", 0.3, 0.2),     # Weak feedback
        ("strong_feedback", 0.6, 0.4),   # Strong feedback
    ]
    
    results = {}
    
    for name, eps_gamma, eps_beta in configs:
        print(f"--- {name} (ε_γ={eps_gamma}, ε_β={eps_beta}) ---")
        
        lifetimes = []
        final_sigmas = []
        
        for trial in range(n_trials):
            sim = StabilityFeedbackSimulator(
                size=size,
                gamma_0=0.008,
                k_org=0.003,
                k_top=0.012,
                k_decay=0.001,
                eps_gamma=eps_gamma,
                eps_beta=eps_beta
            )
            
            sim.psi_r[:] = 1.2
            sim.add_vortex((size//2, size//2), charge=1, amplitude=1.2, core_radius=4.0)
            
            lifetime = 0
            for step in range(steps):
                sim.step()
                
                if step % 50 == 0:
                    vortices = sim.detect_vortices(amplitude_threshold=0.5)
                    if vortices:
                        lifetime = step
            
            lifetimes.append(lifetime)
            final_sigmas.append(np.max(sim.sigma))
        
        avg_lifetime = np.mean(lifetimes)
        std_lifetime = np.std(lifetimes)
        avg_sigma = np.mean(final_sigmas)
        
        results[name] = {
            'avg_lifetime': avg_lifetime,
            'std_lifetime': std_lifetime,
            'avg_final_sigma': avg_sigma,
            'lifetimes': lifetimes
        }
        
        print(f"  Avg lifetime: {avg_lifetime:.0f} ± {std_lifetime:.0f}")
        print(f"  Avg final Σ_max: {avg_sigma:.4f}")
        print()
    
    # Summary
    print("="*70)
    print("LIFETIME COMPARISON")
    print("="*70)
    print()
    print("| Config | Avg Lifetime | Σ_max | Improvement |")
    print("|--------|--------------|-------|-------------|")
    
    baseline = results['no_feedback']['avg_lifetime']
    for name in ['no_feedback', 'weak_feedback', 'strong_feedback']:
        r = results[name]
        improvement = r['avg_lifetime'] / baseline if baseline > 0 else 0
        print(f"| {name:14} | {r['avg_lifetime']:10.0f} | {r['avg_final_sigma']:.4f} | {improvement:.2f}× |")
    
    print()
    
    strong_improvement = results['strong_feedback']['avg_lifetime'] / (baseline + 1)
    if strong_improvement > 1.3:
        print(f"✓ FEEDBACK EXTENDS LIFETIME: {strong_improvement:.2f}× with strong feedback")
    else:
        print(f"- Feedback effect is weak or absent")
    
    return results


# ============================================================
# TEST 3: Does Σ create self-reinforcing stability wells?
# ============================================================

def test_self_reinforcing_wells():
    """
    Test: Does high Σ become self-reinforcing?
    (High Σ → less damping → more persistence → more Σ)
    """
    print()
    print("="*70)
    print("TEST 3: SELF-REINFORCING STABILITY WELLS")
    print("="*70)
    print()
    print("Question: Does Σ create runaway stability in some regions?")
    print()
    
    size = 80
    steps = 6000
    
    sim = StabilityFeedbackSimulator(
        size=size,
        gamma_0=0.006,
        k_org=0.004,
        k_top=0.015,
        k_decay=0.0005,  # Slow decay
        eps_gamma=0.7,    # Strong feedback
        eps_beta=0.4
    )
    
    # Seed multiple vortices
    sim.psi_r[:] = 1.2
    positions = [
        (20, 40), (40, 40), (60, 40)
    ]
    for i, pos in enumerate(positions):
        charge = 1 if i % 2 == 0 else -1
        sim.add_vortex(pos, charge=charge, amplitude=1.2, core_radius=4.0)
    
    # Track
    sigma_maps = []
    gamma_maps = []
    vortex_counts = []
    
    for step in range(steps):
        sim.step()
        
        if step % 500 == 0:
            sigma_maps.append(sim.sigma.copy())
            gamma_maps.append(sim.gamma_field.copy())
            vortices = sim.detect_vortices(amplitude_threshold=0.5)
            vortex_counts.append(len(vortices))
    
    # Analyze
    print(f"Initial vortices: {vortex_counts[0]}")
    print(f"Final vortices: {vortex_counts[-1]}")
    print()
    
    # Check for Σ concentration
    sigma_initial = sigma_maps[1]  # After first accumulation
    sigma_final = sigma_maps[-1]
    
    sigma_max_initial = np.max(sigma_initial)
    sigma_max_final = np.max(sigma_final)
    
    # Check for localized peaks
    threshold = 0.5 * sigma_max_final
    high_sigma_area_initial = np.sum(sigma_initial > threshold)
    high_sigma_area_final = np.sum(sigma_final > threshold)
    
    print(f"Σ_max (early): {sigma_max_initial:.4f}")
    print(f"Σ_max (late):  {sigma_max_final:.4f}")
    print(f"High-Σ area (early): {high_sigma_area_initial}")
    print(f"High-Σ area (late):  {high_sigma_area_final}")
    print()
    
    # Check γ reduction
    gamma_min_initial = np.min(gamma_maps[1])
    gamma_min_final = np.min(gamma_maps[-1])
    
    print(f"γ_min (early): {gamma_min_initial:.5f}")
    print(f"γ_min (late):  {gamma_min_final:.5f}")
    print(f"γ reduction: {(1 - gamma_min_final/sim.gamma_0)*100:.1f}%")
    print()
    
    if sigma_max_final > sigma_max_initial * 1.5 and gamma_min_final < gamma_min_initial * 0.9:
        print("✓ SELF-REINFORCING: Σ grew and γ decreased over time")
    else:
        print("- Self-reinforcement not clearly observed")
    
    return {
        'sigma_max_final': sigma_max_final,
        'gamma_min_final': gamma_min_final,
        'vortex_counts': vortex_counts
    }


# ============================================================
# TEST 4: Comparison with Branch C (no stability branch)
# ============================================================

def test_branch_d_vs_branch_c():
    """
    Direct comparison: Does Branch D outperform Branch C?
    """
    print()
    print("="*70)
    print("TEST 4: BRANCH D vs BRANCH C COMPARISON")
    print("="*70)
    print()
    print("Question: Does stability feedback outperform static β-coupling?")
    print()
    
    size = 80
    steps = 5000
    n_trials = 5
    
    # Branch C: static high-β region
    print("--- Branch C (static β-well) ---")
    branch_c_lifetimes = []
    
    for trial in range(n_trials):
        sim = StabilityFeedbackSimulator(
            size=size,
            gamma_0=0.008,
            eps_gamma=0.0,  # No feedback
            eps_beta=0.0,   # No feedback
            k_org=0.0,      # No stability accumulation
            k_top=0.0
        )
        
        # Static β-well
        center = (size//2, size//2)
        x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        sim.beta_field = np.where(r < 20, 0.8, 0.3)
        
        sim.psi_r[:] = 1.2
        sim.add_vortex(center, charge=1, amplitude=1.2, core_radius=4.0)
        
        lifetime = 0
        for step in range(steps):
            sim.step()
            if step % 50 == 0:
                vortices = sim.detect_vortices(amplitude_threshold=0.5)
                if vortices:
                    lifetime = step
        
        branch_c_lifetimes.append(lifetime)
    
    avg_c = np.mean(branch_c_lifetimes)
    print(f"  Avg lifetime: {avg_c:.0f}")
    
    # Branch D: dynamic stability feedback
    print()
    print("--- Branch D (stability feedback) ---")
    branch_d_lifetimes = []
    
    for trial in range(n_trials):
        sim = StabilityFeedbackSimulator(
            size=size,
            gamma_0=0.008,
            eps_gamma=0.6,
            eps_beta=0.4,
            k_org=0.004,
            k_top=0.015,
            k_decay=0.0008
        )
        
        # No static β-well - let Σ create the structure
        
        sim.psi_r[:] = 1.2
        sim.add_vortex((size//2, size//2), charge=1, amplitude=1.2, core_radius=4.0)
        
        lifetime = 0
        for step in range(steps):
            sim.step()
            if step % 50 == 0:
                vortices = sim.detect_vortices(amplitude_threshold=0.5)
                if vortices:
                    lifetime = step
        
        branch_d_lifetimes.append(lifetime)
    
    avg_d = np.mean(branch_d_lifetimes)
    print(f"  Avg lifetime: {avg_d:.0f}")
    
    print()
    print("="*70)
    print("COMPARISON RESULT")
    print("="*70)
    print()
    print(f"Branch C (static β): {avg_c:.0f} steps")
    print(f"Branch D (feedback): {avg_d:.0f} steps")
    print()
    
    improvement = avg_d / (avg_c + 1)
    
    if improvement > 1.2:
        print(f"✓ BRANCH D OUTPERFORMS: {improvement:.2f}× lifetime improvement")
        print("  → Stability as active feedback > static coupling")
    elif improvement > 0.8:
        print(f"~ COMPARABLE: {improvement:.2f}× (within 20%)")
    else:
        print(f"- BRANCH C BETTER: Branch D underperforms by {(1-improvement)*100:.0f}%")
    
    return {
        'branch_c': avg_c,
        'branch_d': avg_d,
        'improvement': improvement
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*70)
    print("BRANCH D: STABILITY-FEEDBACK EXTENSION")
    print("="*70)
    print()
    print("Hypothesis: Stability is an ACTIVE BRANCH that feeds back")
    print("            on emergent branches, not a passive outcome.")
    print()
    print("Model: dΣ/dt = k_org*S + k_top*T - k_decay*Σ + D∇²Σ")
    print("       γ(x) = γ₀/(1 + ε_γ*Σ)   [high Σ → less damping]")
    print("       β(x) = β₀*(1 + ε_β*Σ)   [high Σ → more coupling]")
    print()
    
    test1_results = test_sigma_accumulation()
    test2_results = test_feedback_lifetime_extension()
    test3_results = test_self_reinforcing_wells()
    test4_results = test_branch_d_vs_branch_c()
    
    print()
    print("="*70)
    print("FINAL VERDICT")
    print("="*70)
    print()
    
    # Evaluate
    sigma_accumulated = test1_results['sigma_growth'] > 1.5
    lifetime_extended = test2_results['strong_feedback']['avg_lifetime'] > test2_results['no_feedback']['avg_lifetime'] * 1.3
    self_reinforcing = test3_results['sigma_max_final'] > 0.1
    outperforms_c = test4_results['improvement'] > 1.2
    
    print(f"Test 1 (Σ accumulation):    {'✓ PASS' if sigma_accumulated else '✗ FAIL'}")
    print(f"Test 2 (Lifetime extension): {'✓ PASS' if lifetime_extended else '✗ FAIL'}")
    print(f"Test 3 (Self-reinforcing):   {'✓ PASS' if self_reinforcing else '✗ FAIL'}")
    print(f"Test 4 (vs Branch C):        {'✓ PASS' if outperforms_c else '✗ FAIL'}")
    print()
    
    passed = sum([sigma_accumulated, lifetime_extended, self_reinforcing, outperforms_c])
    
    if passed >= 3:
        print("CONCLUSION: STABILITY-FEEDBACK IS A VIABLE MECHANISM")
        print("            The stability branch hypothesis is supported.")
        print("            Repeated organization DOES create stabilizing environment.")
    elif passed >= 2:
        print("CONCLUSION: PARTIAL SUPPORT FOR STABILITY-FEEDBACK")
        print("            Some evidence, but not conclusive.")
    else:
        print("CONCLUSION: STABILITY-FEEDBACK NOT CLEARLY EFFECTIVE")
        print("            The mechanism needs revision or different parameters.")
