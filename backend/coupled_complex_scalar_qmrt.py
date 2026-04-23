"""
Branch C: Coupled Complex Scalar QMRT
=====================================

Minimal extension of Branch B to test β-topology coupling.

Hypothesis: Making vortex energy depend on β(x) will create pinning.

Change: Modify gradient energy term to include β(x)
    E_gradient = ∫ β(x) |∇ψ|² dx

This makes vortex cores (high |∇ψ|) energetically favorable where β is LOW.
Equivalently, vortices should AVOID high-β regions, or be ATTRACTED to low-β.

Wait - that's backwards for our test. Let's try:
    E_gradient = ∫ (1/β(x)) |∇ψ|² dx

Now vortex cores cost LESS energy where β is HIGH → pinning to high-β regions.

Alternative (simpler): Make damping depend on β
    γ(x) = γ_base / β(x)

Lower damping where β is high → vortices live longer there.

We'll test BOTH approaches.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional

class CoupledComplexScalarSimulator2D:
    """
    Branch C: Complex scalar with β-topology coupling.
    
    Two coupling modes:
    1. ENERGY coupling: gradient energy scales with β
    2. DAMPING coupling: damping scales inversely with β
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma_base: float = 0.01,
        lambda_relax: float = 0.5,
        beta_base: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
        # NEW: Coupling parameters
        coupling_mode: str = 'both',  # 'energy', 'damping', 'both', 'none'
        energy_coupling_strength: float = 1.0,  # How much β affects gradient energy
        damping_coupling_strength: float = 1.0,  # How much β affects damping
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma_base = gamma_base
        self.lambda_relax = lambda_relax
        self.beta_base = beta_base
        self.D_medium = D_medium
        self.dt = dt
        
        # Coupling parameters
        self.coupling_mode = coupling_mode
        self.energy_coupling_strength = energy_coupling_strength
        self.damping_coupling_strength = damping_coupling_strength
        
        # Complex field
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        # Medium field
        self.tau = np.ones((size, size)) * tau_0
        
        # Spatially varying β (this is what we couple to)
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
        return (self.psi_r**2 + self.psi_i**2 + 
                self.psi_r_dot**2 + self.psi_i_dot**2)
    
    def compute_c_eff(self) -> np.ndarray:
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho: np.ndarray) -> np.ndarray:
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta_field * rho_smooth / rho_max)
    
    def compute_laplacian(self, f: np.ndarray) -> np.ndarray:
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
    
    def compute_effective_damping(self) -> np.ndarray:
        """
        Compute spatially varying damping.
        
        With damping coupling: γ_eff = γ_base / (1 + α * (β - β_mean))
        Higher β → lower damping → vortices live longer
        """
        if self.coupling_mode in ['damping', 'both']:
            beta_mean = np.mean(self.beta_field)
            beta_normalized = (self.beta_field - beta_mean) / (beta_mean + 0.1)
            # Higher β → lower damping
            gamma_eff = self.gamma_base / (1 + self.damping_coupling_strength * beta_normalized)
            return np.clip(gamma_eff, 0.001, 0.1)
        else:
            return np.ones((self.size, self.size)) * self.gamma_base
    
    def compute_effective_gradient_coeff(self) -> np.ndarray:
        """
        Compute spatially varying gradient energy coefficient.
        
        With energy coupling: coeff = 1 / (1 + α * (β - β_mean))
        Higher β → lower gradient cost → vortex cores favored there
        """
        if self.coupling_mode in ['energy', 'both']:
            beta_mean = np.mean(self.beta_field)
            beta_normalized = (self.beta_field - beta_mean) / (beta_mean + 0.1)
            # Higher β → lower gradient penalty
            coeff = 1.0 / (1 + self.energy_coupling_strength * beta_normalized)
            return np.clip(coeff, 0.5, 2.0)
        else:
            return np.ones((self.size, self.size))
    
    def step(self):
        """Advance one timestep with β-coupled dynamics."""
        rho = self.rho
        
        # Medium evolution (unchanged from Branch B)
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_field * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave evolution with COUPLED terms
        c_eff = self.compute_c_eff()
        c_eff_sq = c_eff**2
        
        # Get spatially varying coefficients
        gamma_eff = self.compute_effective_damping()
        grad_coeff = self.compute_effective_gradient_coeff()
        
        # Laplacian with gradient coupling
        # Standard: c² ∇²ψ
        # Coupled: c² ∇·(coeff ∇ψ) ≈ c² * coeff * ∇²ψ + c² * ∇coeff · ∇ψ
        # Simplified: just scale by coeff
        lap_psi_r = self.compute_laplacian(self.psi_r)
        lap_psi_i = self.compute_laplacian(self.psi_i)
        
        # Acceleration with coupling
        acc_r = c_eff_sq * grad_coeff * lap_psi_r - gamma_eff * self.psi_r_dot
        acc_i = c_eff_sq * grad_coeff * lap_psi_i - gamma_eff * self.psi_i_dot
        
        # Update
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def set_biased_region(self, center: Tuple[int, int], radius: float,
                          beta_inside: float, beta_outside: float):
        """Set up β-biased region."""
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        inside = r <= radius
        
        self.beta_field[inside] = beta_inside
        self.beta_field[~inside] = beta_outside
    
    def add_vortex(self, center: Tuple[int, int], charge: int = 1, 
                   amplitude: float = 1.0, core_radius: float = 3.0):
        """Initialize a vortex."""
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
        """Compute winding number around point (i,j)."""
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
            
            ni = ni % self.size
            nj = nj % self.size
            ni_next = ni_next % self.size
            nj_next = nj_next % self.size
            
            dp = phase[ni_next, nj_next] - phase[ni, nj]
            while dp > np.pi:
                dp -= 2*np.pi
            while dp < -np.pi:
                dp += 2*np.pi
            
            total += dp
        
        return total / (2*np.pi)
    
    def detect_vortices(self, amplitude_threshold: float = 0.3,
                        winding_threshold: float = 0.5) -> List[Dict]:
        """Detect vortex cores."""
        vortices = []
        amp = self.amplitude
        
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                local_amp = amp[i, j]
                region = amp[i-1:i+2, j-1:j+2]
                
                if local_amp <= np.min(region) and local_amp < amplitude_threshold:
                    winding = self.compute_winding_number(i, j, radius=2)
                    
                    if abs(winding) > winding_threshold:
                        charge = int(np.round(winding))
                        # Also record local β
                        local_beta = self.beta_field[i, j]
                        vortices.append({
                            'position': [i, j],
                            'charge': charge,
                            'amplitude': float(local_amp),
                            'winding': float(winding),
                            'beta': float(local_beta)
                        })
        
        return vortices
    
    def measure(self) -> Dict:
        """Compute diagnostics."""
        vortices = self.detect_vortices()
        return {
            'n_vortices': len(vortices),
            'total_charge': sum(v['charge'] for v in vortices),
            'vortices': vortices
        }


# ============================================================
# Branch C Tests
# ============================================================

def run_pinning_test():
    """Test: Does β-topology coupling create vortex pinning?"""
    print("="*70)
    print("BRANCH C TEST 1: VORTEX PINNING")
    print("="*70)
    print()
    
    size = 100
    center = (size//2, size//2)
    radius = 25
    steps = 4000
    
    # Create mask
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    inside_mask = r <= radius
    
    results = {}
    
    for mode in ['none', 'damping', 'energy', 'both']:
        print(f"\n--- Coupling mode: {mode} ---")
        
        sim = CoupledComplexScalarSimulator2D(
            size=size,
            gamma_base=0.008,
            D_medium=0.02,
            coupling_mode=mode,
            energy_coupling_strength=2.0,
            damping_coupling_strength=2.0
        )
        
        # Set β bias
        sim.set_biased_region(center, radius, beta_inside=0.8, beta_outside=0.2)
        
        # Background + vortices (3 inside, 3 outside)
        sim.psi_r[:] = 1.5
        sim.psi_i[:] = 0.0
        
        np.random.seed(42)
        # Inside
        for _ in range(3):
            while True:
                cx = np.random.randint(center[0]-radius+5, center[0]+radius-5)
                cy = np.random.randint(center[1]-radius+5, center[1]+radius-5)
                if inside_mask[cx, cy]:
                    break
            sim.add_vortex((cx, cy), charge=1, amplitude=1.5, core_radius=4.0)
        
        # Outside
        for _ in range(3):
            while True:
                cx = np.random.randint(10, size-10)
                cy = np.random.randint(10, size-10)
                if not inside_mask[cx, cy]:
                    break
            sim.add_vortex((cx, cy), charge=1, amplitude=1.5, core_radius=4.0)
        
        # Track
        inside_counts = []
        outside_counts = []
        
        for step in range(steps):
            sim.step()
            if step % 100 == 0:
                vortices = sim.detect_vortices(amplitude_threshold=0.5)
                n_in = sum(1 for v in vortices if inside_mask[v['position'][0], v['position'][1]])
                n_out = len(vortices) - n_in
                inside_counts.append(n_in)
                outside_counts.append(n_out)
        
        # Stats
        area_in = np.sum(inside_mask)
        area_out = size*size - area_in
        
        mean_in = np.mean(inside_counts[-10:]) if inside_counts else 0
        mean_out = np.mean(outside_counts[-10:]) if outside_counts else 0
        
        density_ratio = (mean_in / area_in) / (mean_out / area_out + 1e-10)
        
        results[mode] = {
            'mean_inside': mean_in,
            'mean_outside': mean_out,
            'density_ratio': density_ratio
        }
        
        print(f"  Late vortices inside: {mean_in:.2f}")
        print(f"  Late vortices outside: {mean_out:.2f}")
        print(f"  Density ratio: {density_ratio:.2f}")
    
    print()
    print("="*70)
    print("PINNING TEST RESULTS")
    print("="*70)
    print()
    print("| Mode | Inside | Outside | Density Ratio |")
    print("|------|--------|---------|---------------|")
    for mode in ['none', 'damping', 'energy', 'both']:
        r = results[mode]
        print(f"| {mode:8} | {r['mean_inside']:.2f} | {r['mean_outside']:.2f} | {r['density_ratio']:.2f} |")
    
    # Check for pinning
    baseline = results['none']['density_ratio']
    best_mode = max(['damping', 'energy', 'both'], key=lambda m: results[m]['density_ratio'])
    best_ratio = results[best_mode]['density_ratio']
    
    print()
    if best_ratio > baseline * 1.5 and best_ratio > 1.5:
        print(f"✓ PINNING WORKS: {best_mode} coupling achieves {best_ratio:.2f}x density ratio")
    else:
        print(f"✗ NO STRONG PINNING: Best ratio = {best_ratio:.2f}x (baseline = {baseline:.2f}x)")
    
    return results


def run_lifetime_test():
    """Test: Does coupling increase vortex lifetime in high-β regions?"""
    print()
    print("="*70)
    print("BRANCH C TEST 2: VORTEX LIFETIME")
    print("="*70)
    print()
    
    size = 80
    
    results = {}
    
    for mode in ['none', 'both']:
        print(f"--- Coupling mode: {mode} ---")
        
        for region in ['high_beta', 'low_beta']:
            sim = CoupledComplexScalarSimulator2D(
                size=size,
                gamma_base=0.008,
                coupling_mode=mode,
                energy_coupling_strength=2.0,
                damping_coupling_strength=2.0
            )
            
            # Set β bias
            center = (size//2, size//2)
            sim.set_biased_region(center, 20, beta_inside=0.8, beta_outside=0.2)
            
            # Background
            sim.psi_r[:] = 1.5
            
            # Single vortex in high or low β region
            if region == 'high_beta':
                vortex_pos = center
            else:
                vortex_pos = (15, 15)  # Corner, low β
            
            sim.add_vortex(vortex_pos, charge=1, amplitude=1.5, core_radius=4.0)
            
            # Track lifetime
            lifetime = 0
            for step in range(8000):
                sim.step()
                if step % 100 == 0:
                    vortices = sim.detect_vortices(amplitude_threshold=0.5)
                    if not vortices:
                        lifetime = step
                        break
            else:
                lifetime = 8000
            
            key = f"{mode}_{region}"
            results[key] = lifetime
            print(f"  {region}: lifetime = {lifetime} steps")
    
    print()
    print("| Mode | High-β Region | Low-β Region | Ratio |")
    print("|------|---------------|--------------|-------|")
    for mode in ['none', 'both']:
        hi = results[f'{mode}_high_beta']
        lo = results[f'{mode}_low_beta']
        ratio = hi / (lo + 1) if lo > 0 else float('inf')
        print(f"| {mode:8} | {hi} | {lo} | {ratio:.2f}x |")
    
    return results


if __name__ == "__main__":
    print("="*70)
    print("BRANCH C: COUPLED COMPLEX SCALAR QMRT")
    print("Testing β-topology coupling")
    print("="*70)
    print()
    
    pinning_results = run_pinning_test()
    lifetime_results = run_lifetime_test()
    
    print()
    print("="*70)
    print("BRANCH C SUMMARY")
    print("="*70)
    print()
    print("Hypothesis: β-topology coupling creates vortex pinning")
    print()
    
    # Evaluate
    baseline_pinning = pinning_results['none']['density_ratio']
    coupled_pinning = pinning_results['both']['density_ratio']
    
    baseline_lifetime_ratio = lifetime_results['none_high_beta'] / (lifetime_results['none_low_beta'] + 1)
    coupled_lifetime_ratio = lifetime_results['both_high_beta'] / (lifetime_results['both_low_beta'] + 1)
    
    if coupled_pinning > baseline_pinning * 1.5:
        print("✓ PINNING: Coupling increases vortex density in high-β regions")
    else:
        print("✗ PINNING: Coupling does not significantly affect vortex density")
    
    if coupled_lifetime_ratio > baseline_lifetime_ratio * 1.5:
        print("✓ LIFETIME: Coupling increases vortex lifetime in high-β regions")
    else:
        print("✗ LIFETIME: Coupling does not significantly affect lifetime")
