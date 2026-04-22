"""
Branch B: Complex Scalar QMRT
=============================

Minimal extension of Branch A to support topology.

Replace: φ ∈ ℝ
With:    ψ = ψ_r + i*ψ_i = |ψ|e^{iθ} ∈ ℂ

Key features:
- Amplitude |ψ| and phase θ
- Phase can wind around points → topological defects
- Vortex cores where |ψ| = 0 with nonzero winding
- Same medium architecture (τ, β asymmetry, etc.)
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple, Optional

class ComplexScalarSimulator2D:
    """
    Complex scalar field coupled to a responsive medium.
    
    Equations:
        ψ_tt = c_eff² ∇²ψ - γ ψ_t + nonlinear terms
        τ_t = -λ(τ - τ_eq(ρ)) + D ∇²τ
    
    where ψ = ψ_r + i*ψ_i ∈ ℂ
    and ρ = |ψ|² + |ψ_t|²
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.01,
        lambda_relax: float = 0.5,
        beta: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
        nonlinear_coeff: float = 0.0  # For future nonlinear extensions
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.beta = beta
        self.D_medium = D_medium
        self.dt = dt
        self.nonlinear_coeff = nonlinear_coeff
        
        # Complex field ψ = ψ_r + i*ψ_i
        self.psi_r = np.zeros((size, size))  # Real part
        self.psi_i = np.zeros((size, size))  # Imaginary part
        self.psi_r_dot = np.zeros((size, size))  # Time derivative (real)
        self.psi_i_dot = np.zeros((size, size))  # Time derivative (imag)
        
        # Medium field
        self.tau = np.ones((size, size)) * tau_0
        
        # Spatially varying parameters (for β asymmetry)
        self.gamma_field = np.ones((size, size)) * gamma
        self.beta_field = np.ones((size, size)) * beta
        self.lambda_field = np.ones((size, size)) * lambda_relax
    
    # ============================================================
    # Field accessors
    # ============================================================
    
    @property
    def psi(self) -> np.ndarray:
        """Complex field ψ"""
        return self.psi_r + 1j * self.psi_i
    
    @property
    def psi_dot(self) -> np.ndarray:
        """Time derivative of ψ"""
        return self.psi_r_dot + 1j * self.psi_i_dot
    
    @property
    def amplitude(self) -> np.ndarray:
        """|ψ| - amplitude"""
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        """θ = arg(ψ) - phase"""
        return np.arctan2(self.psi_i, self.psi_r)
    
    @property
    def rho(self) -> np.ndarray:
        """Energy density ρ = |ψ|² + |ψ_t|²"""
        return (self.psi_r**2 + self.psi_i**2 + 
                self.psi_r_dot**2 + self.psi_i_dot**2)
    
    # ============================================================
    # Medium coupling
    # ============================================================
    
    def compute_c_eff(self) -> np.ndarray:
        """Effective wave speed c_eff = c_0 * τ / τ_0"""
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho: np.ndarray) -> np.ndarray:
        """Equilibrium tau depending on local energy density"""
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta_field * rho_smooth / rho_max)
    
    def compute_laplacian(self, f: np.ndarray) -> np.ndarray:
        """2D Laplacian with periodic boundary"""
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
    
    # ============================================================
    # Time evolution
    # ============================================================
    
    def step(self):
        """Advance one timestep"""
        rho = self.rho
        
        # Medium evolution
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_field * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Wave evolution (real and imaginary parts separately)
        c_eff = self.compute_c_eff()
        c_eff_sq = c_eff**2
        
        lap_psi_r = self.compute_laplacian(self.psi_r)
        lap_psi_i = self.compute_laplacian(self.psi_i)
        
        # Nonlinear term (optional): -λ_nl |ψ|² ψ
        nl_r = 0
        nl_i = 0
        if self.nonlinear_coeff != 0:
            amp_sq = self.psi_r**2 + self.psi_i**2
            nl_r = -self.nonlinear_coeff * amp_sq * self.psi_r
            nl_i = -self.nonlinear_coeff * amp_sq * self.psi_i
        
        # Acceleration
        acc_r = c_eff_sq * lap_psi_r - self.gamma_field * self.psi_r_dot + nl_r
        acc_i = c_eff_sq * lap_psi_i - self.gamma_field * self.psi_i_dot + nl_i
        
        # Update velocities and positions
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    # ============================================================
    # Initialization
    # ============================================================
    
    def add_gaussian_pulse(self, center: Tuple[int, int], amplitude: float = 1.0, 
                           width: float = 5.0, phase: float = 0.0):
        """Add a Gaussian pulse with given phase"""
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        envelope = amplitude * np.exp(-r**2 / (2*width**2))
        self.psi_r_dot += envelope * np.cos(phase)
        self.psi_i_dot += envelope * np.sin(phase)
    
    def add_vortex(self, center: Tuple[int, int], charge: int = 1, 
                   amplitude: float = 1.0, core_radius: float = 3.0):
        """
        Initialize a vortex with given topological charge.
        
        Creates: ψ = A * tanh(r/r_c) * e^{i n θ}
        where n is the charge (winding number)
        """
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        dx = x - center[0]
        dy = y - center[1]
        r = np.sqrt(dx**2 + dy**2 + 0.01)  # Avoid division by zero
        theta = np.arctan2(dy, dx)
        
        # Amplitude profile: zero at core, rises to amplitude
        amp_profile = amplitude * np.tanh(r / core_radius)
        
        # Phase winds n times around center
        phase = charge * theta
        
        # Multiply with existing field (or add if no background)
        if np.max(np.abs(self.psi_r)) < 0.01 and np.max(np.abs(self.psi_i)) < 0.01:
            # No background - just set
            self.psi_r = amp_profile * np.cos(phase)
            self.psi_i = amp_profile * np.sin(phase)
        else:
            # Multiply with existing (for proper phase combination)
            psi_existing = self.psi_r + 1j * self.psi_i
            psi_vortex = amp_profile * np.exp(1j * phase)
            combined = psi_existing * psi_vortex / (amplitude + 0.01)  # Normalize
            self.psi_r = np.real(combined)
            self.psi_i = np.imag(combined)
    
    def add_vortex_pair(self, center1: Tuple[int, int], center2: Tuple[int, int],
                        charge1: int = 1, charge2: int = -1,
                        amplitude: float = 1.0, core_radius: float = 3.0):
        """Add a vortex-antivortex pair"""
        self.add_vortex(center1, charge1, amplitude, core_radius)
        self.add_vortex(center2, charge2, amplitude, core_radius)
    
    def add_uniform_noise(self, amplitude: float = 0.1):
        """Add uniform noise to both components"""
        self.psi_r_dot += np.random.uniform(-amplitude, amplitude, (self.size, self.size))
        self.psi_i_dot += np.random.uniform(-amplitude, amplitude, (self.size, self.size))
    
    def set_biased_region(self, center: Tuple[int, int], radius: float,
                          beta_inside: float, beta_outside: float,
                          gamma_inside: Optional[float] = None,
                          gamma_outside: Optional[float] = None,
                          lambda_inside: Optional[float] = None,
                          lambda_outside: Optional[float] = None):
        """Set up a biased region with different parameters"""
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        inside = r <= radius
        
        self.beta_field[inside] = beta_inside
        self.beta_field[~inside] = beta_outside
        
        if gamma_inside is not None and gamma_outside is not None:
            self.gamma_field[inside] = gamma_inside
            self.gamma_field[~inside] = gamma_outside
        
        if lambda_inside is not None and lambda_outside is not None:
            self.lambda_field[inside] = lambda_inside
            self.lambda_field[~inside] = lambda_outside
    
    # ============================================================
    # Vortex detection
    # ============================================================
    
    def compute_winding_number(self, i: int, j: int, radius: int = 2) -> float:
        """
        Compute winding number around point (i,j).
        
        Winding number = (1/2π) ∮ dθ around a closed loop
        """
        # Sample phase around a square loop
        phase = self.phase
        
        # Points on loop (clockwise)
        loop_points = []
        # Top edge (left to right)
        for dj in range(-radius, radius+1):
            loop_points.append((i-radius, j+dj))
        # Right edge (top to bottom)
        for di in range(-radius+1, radius+1):
            loop_points.append((i+di, j+radius))
        # Bottom edge (right to left)
        for dj in range(radius-1, -radius-1, -1):
            loop_points.append((i+radius, j+dj))
        # Left edge (bottom to top)
        for di in range(radius-1, -radius, -1):
            loop_points.append((i+di, j-radius))
        
        # Compute phase increments
        total_phase_change = 0
        for k in range(len(loop_points)):
            ni, nj = loop_points[k]
            ni_next, nj_next = loop_points[(k+1) % len(loop_points)]
            
            # Periodic boundary
            ni = ni % self.size
            nj = nj % self.size
            ni_next = ni_next % self.size
            nj_next = nj_next % self.size
            
            # Phase difference (unwrap)
            dp = phase[ni_next, nj_next] - phase[ni, nj]
            # Unwrap to [-π, π]
            while dp > np.pi:
                dp -= 2*np.pi
            while dp < -np.pi:
                dp += 2*np.pi
            
            total_phase_change += dp
        
        winding = total_phase_change / (2*np.pi)
        return winding
    
    def detect_vortices(self, amplitude_threshold: float = 0.1,
                        winding_threshold: float = 0.5) -> List[Dict]:
        """
        Detect vortex cores (points where |ψ| ≈ 0 with nonzero winding).
        """
        vortices = []
        amp = self.amplitude
        
        # Find local minima of amplitude
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                local_amp = amp[i, j]
                
                # Check if local minimum
                region = amp[i-1:i+2, j-1:j+2]
                if local_amp <= np.min(region) and local_amp < amplitude_threshold:
                    # Compute winding number
                    winding = self.compute_winding_number(i, j, radius=2)
                    
                    if abs(winding) > winding_threshold:
                        charge = int(np.round(winding))
                        vortices.append({
                            'position': [i, j],
                            'charge': charge,
                            'amplitude': float(local_amp),
                            'winding': float(winding)
                        })
        
        return vortices
    
    # ============================================================
    # Measurement
    # ============================================================
    
    def measure(self) -> Dict:
        """Compute diagnostic quantities"""
        amp = self.amplitude
        rho = self.rho
        c_eff = self.compute_c_eff()
        
        # Energy
        grad_r_x = np.roll(self.psi_r, -1, 0) - self.psi_r
        grad_r_y = np.roll(self.psi_r, -1, 1) - self.psi_r
        grad_i_x = np.roll(self.psi_i, -1, 0) - self.psi_i
        grad_i_y = np.roll(self.psi_i, -1, 1) - self.psi_i
        grad_sq = grad_r_x**2 + grad_r_y**2 + grad_i_x**2 + grad_i_y**2
        
        E_kinetic = 0.5 * np.sum(self.psi_r_dot**2 + self.psi_i_dot**2)
        E_gradient = 0.5 * np.sum(c_eff**2 * grad_sq)
        E_total = E_kinetic + E_gradient
        
        # Organization
        S = np.std(c_eff) / (np.mean(c_eff) + 1e-10)
        
        # Vortex count
        vortices = self.detect_vortices()
        
        return {
            'E_total': float(E_total),
            'E_kinetic': float(E_kinetic),
            'E_gradient': float(E_gradient),
            'S': float(S),
            'amplitude_mean': float(np.mean(amp)),
            'amplitude_max': float(np.max(amp)),
            'rho_mean': float(np.mean(rho)),
            'n_vortices': len(vortices),
            'total_charge': sum(v['charge'] for v in vortices),
            'vortices': vortices
        }
    
    def measure_by_region(self, mask: np.ndarray) -> Dict:
        """Measure metrics inside vs outside a region"""
        amp = self.amplitude
        c_eff = self.compute_c_eff()
        
        inside = mask
        outside = ~mask
        
        # S inside/outside
        c_inside = c_eff[inside]
        c_outside = c_eff[outside]
        S_inside = np.std(c_inside) / (np.mean(c_inside) + 1e-10) if len(c_inside) > 0 else 0
        S_outside = np.std(c_outside) / (np.mean(c_outside) + 1e-10) if len(c_outside) > 0 else 0
        
        # Amplitude inside/outside
        amp_inside = np.mean(amp[inside]) if np.sum(inside) > 0 else 0
        amp_outside = np.mean(amp[outside]) if np.sum(outside) > 0 else 0
        
        # Vortex count inside/outside
        vortices = self.detect_vortices()
        v_inside = sum(1 for v in vortices if inside[v['position'][0], v['position'][1]])
        v_outside = len(vortices) - v_inside
        
        return {
            'S_inside': float(S_inside),
            'S_outside': float(S_outside),
            'S_contrast': float(S_inside / (S_outside + 1e-10)),
            'amp_inside': float(amp_inside),
            'amp_outside': float(amp_outside),
            'vortices_inside': v_inside,
            'vortices_outside': v_outside
        }


# ============================================================
# Quick test
# ============================================================

if __name__ == "__main__":
    print("Testing Complex Scalar Simulator...")
    
    sim = ComplexScalarSimulator2D(size=80)
    
    # Add a vortex-antivortex pair
    sim.add_vortex_pair(
        center1=(30, 40), center2=(50, 40),
        charge1=1, charge2=-1,
        amplitude=1.0, core_radius=3.0
    )
    
    print(f"Initial state:")
    m = sim.measure()
    print(f"  Vortices detected: {m['n_vortices']}")
    print(f"  Total charge: {m['total_charge']}")
    for v in m['vortices']:
        print(f"    Position {v['position']}, charge={v['charge']}, winding={v['winding']:.2f}")
    
    # Evolve
    print("\nEvolving...")
    for step in range(1000):
        sim.step()
        if step % 200 == 0:
            m = sim.measure()
            print(f"  Step {step}: {m['n_vortices']} vortices, E={m['E_total']:.2f}")
    
    print("\nFinal state:")
    m = sim.measure()
    print(f"  Vortices detected: {m['n_vortices']}")
    print(f"  Total charge: {m['total_charge']}")
    for v in m['vortices']:
        print(f"    Position {v['position']}, charge={v['charge']}, winding={v['winding']:.2f}")
