"""
QMRT Simulation API
===================

Clean API for running 2D and 3D QMRT simulations with full metrics:
- Medium balance (E, P, D)
- Spatial structure (S)
- Ordering structure (O)
- Temporal layers (R, P)
- Spacetime coupling (I_TS)
- Causal geometry
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import pearsonr
import time

router = APIRouter(prefix="/qmrt-sim", tags=["QMRT Simulation"])


# ============================================================
# MODELS
# ============================================================

class SimulationConfig(BaseModel):
    """Configuration for QMRT simulation."""
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=60, ge=20, le=100, description="Grid size")
    alpha: float = Field(default=0.5, ge=0.1, le=0.9, description="Backreaction coupling β")
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0, description="Relaxation rate λ")
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1, description="Wave damping γ")
    steps: int = Field(default=300, ge=50, le=1000, description="Simulation steps")
    sample_interval: int = Field(default=10, ge=1, le=50, description="Measurement interval")


class TimePoint(BaseModel):
    """Single time point measurement."""
    t: float
    E_total: float
    E_kinetic: float
    E_gradient: float
    S_total: float
    O_total: float
    R_rate: float
    P_persistence: float
    I_TS: float
    isotropy_cv: float
    confinement: float


class SimulationResult(BaseModel):
    """Complete simulation result."""
    dimension: str
    config: Dict
    duration_seconds: float
    measurements: List[TimePoint]
    
    # Final metrics
    balance_achieved: bool
    balance_E_cv: float
    
    spatial_S_mean: float
    ordering_O_mean: float
    rate_R_mean: float
    persistence_P_mean: float
    coupling_I_TS_mean: float
    
    geometry_isotropic: bool
    geometry_confined: bool
    
    # Correlations
    rho_RS: float
    rho_PS: float
    rho_OS: float
    
    # Field snapshots (for visualization)
    field_snapshots: List[Dict]


# ============================================================
# SIMULATORS
# ============================================================

class QMRTSimulator2D:
    """2D QMRT dynamical medium simulator."""
    
    def __init__(self, size=60, c_0=2.0, tau_0=1.0, beta=0.5,
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
        self.tau_prev = self.tau.copy()
        
        self.source_center = (size // 2, size // 2)
        
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_laplacian(self, f):
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
    
    def compute_gradient_magnitude(self, f):
        gx = np.roll(f, -1, 0) - f
        gy = np.roll(f, -1, 1) - f
        return np.sqrt(gx**2 + gy**2)
    
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
    
    def add_pulse(self, center=None, amplitude=3.0, width=4.0):
        if center is None:
            center = self.source_center
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))
        self.source_center = center
    
    def measure(self, t):
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        
        # Energy
        grad_phi = self.compute_gradient_magnitude(self.phi)
        E_kinetic = 0.5 * np.sum(self.phi_dot**2)
        E_gradient = 0.5 * np.sum(c_eff**2 * grad_phi**2)
        E_total = E_kinetic + E_gradient
        
        # Spatial S
        c_mean = np.mean(c_eff)
        c_std = np.std(c_eff)
        S_metric = c_std / (c_mean + 1e-10)
        grad_c = self.compute_gradient_magnitude(c_eff)
        S_grad = np.mean(grad_c)
        S_total = np.sqrt(S_metric**2 + S_grad**2)
        
        # Ordering O
        O_capacity = c_std / (c_mean + 1e-10)
        O_total = O_capacity * S_grad * np.var(c_eff)
        
        # Temporal R, P
        tau_change = np.abs(self.tau - self.tau_prev)
        R_rate = np.mean(tau_change) / self.dt if self.dt > 0 else 0
        P_persistence = 1.0 / (1.0 + R_rate)
        
        # Coupling I_TS
        S_flat = c_eff.flatten()
        R_flat = tau_change.flatten()
        P_flat = gaussian_filter(rho, sigma=3.0).flatten()
        O_flat = (1.0 / (c_eff + 0.1)).flatten()
        
        rho_RS = pearsonr(R_flat, S_flat)[0] if np.std(R_flat) > 1e-10 else 0
        rho_PS = pearsonr(P_flat, S_flat)[0] if np.std(P_flat) > 1e-10 else 0
        rho_OS = pearsonr(O_flat, S_flat)[0] if np.std(O_flat) > 1e-10 else 0
        I_TS = np.sqrt(rho_RS**2 + rho_PS**2 + rho_OS**2) / np.sqrt(3)
        
        # Geometry (2D)
        cx, cy = self.source_center
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        energy_x = np.sum(rho[cx:, cy])
        energy_y = np.sum(rho[cx, cy:])
        isotropy_cv = np.std([energy_x, energy_y]) / (np.mean([energy_x, energy_y]) + 1e-10)
        
        cone_radius = c_mean * t
        inside = r <= cone_radius
        confinement = np.sum(rho[inside]) / (np.sum(rho) + 1e-10) * 100 if cone_radius > 0 else 100
        
        return {
            't': float(t),
            'E_total': float(E_total),
            'E_kinetic': float(E_kinetic),
            'E_gradient': float(E_gradient),
            'S_total': float(S_total),
            'O_total': float(O_total),
            'R_rate': float(R_rate),
            'P_persistence': float(P_persistence),
            'I_TS': float(I_TS),
            'isotropy_cv': float(isotropy_cv),
            'confinement': float(confinement),
            'rho_RS': float(rho_RS),
            'rho_PS': float(rho_PS),
            'rho_OS': float(rho_OS),
        }
    
    def get_field_snapshot(self):
        """Get field data for visualization."""
        rho = self.phi**2 + self.phi_dot**2
        c_eff = self.compute_c_eff()
        
        # Downsample for transfer
        step = max(1, self.size // 32)
        
        return {
            'rho': rho[::step, ::step].tolist(),
            'c_eff': c_eff[::step, ::step].tolist(),
            'tau': self.tau[::step, ::step].tolist(),
        }


class QMRTSimulator3D:
    """3D QMRT dynamical medium simulator."""
    
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
        self.tau_prev = self.tau.copy()
        
        self.source_center = (size // 2, size // 2, size // 2)
        
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
    
    def compute_gradient_magnitude(self, f):
        gx = np.roll(f, -1, 0) - f
        gy = np.roll(f, -1, 1) - f
        gz = np.roll(f, -1, 2) - f
        return np.sqrt(gx**2 + gy**2 + gz**2)
    
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
    
    def add_pulse(self, center=None, amplitude=4.0, width=3.0):
        if center is None:
            center = self.source_center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2 + (z - center[2])**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))
        self.source_center = center
    
    def measure(self, t):
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        
        # Energy
        grad_phi = self.compute_gradient_magnitude(self.phi)
        E_kinetic = 0.5 * np.sum(self.phi_dot**2)
        E_gradient = 0.5 * np.sum(c_eff**2 * grad_phi**2)
        E_total = E_kinetic + E_gradient
        
        # Spatial S
        c_mean = np.mean(c_eff)
        c_std = np.std(c_eff)
        S_metric = c_std / (c_mean + 1e-10)
        grad_c = self.compute_gradient_magnitude(c_eff)
        S_grad = np.mean(grad_c)
        S_total = np.sqrt(S_metric**2 + S_grad**2)
        
        # Ordering O
        O_capacity = c_std / (c_mean + 1e-10)
        O_total = O_capacity * S_grad * np.var(c_eff)
        
        # Temporal R, P
        tau_change = np.abs(self.tau - self.tau_prev)
        R_rate = np.mean(tau_change) / self.dt if self.dt > 0 else 0
        P_persistence = 1.0 / (1.0 + R_rate)
        
        # Coupling I_TS
        S_flat = c_eff.flatten()
        R_flat = tau_change.flatten()
        P_flat = gaussian_filter(rho, sigma=3.0).flatten()
        O_flat = (1.0 / (c_eff + 0.1)).flatten()
        
        rho_RS = pearsonr(R_flat, S_flat)[0] if np.std(R_flat) > 1e-10 else 0
        rho_PS = pearsonr(P_flat, S_flat)[0] if np.std(P_flat) > 1e-10 else 0
        rho_OS = pearsonr(O_flat, S_flat)[0] if np.std(O_flat) > 1e-10 else 0
        I_TS = np.sqrt(rho_RS**2 + rho_PS**2 + rho_OS**2) / np.sqrt(3)
        
        # 3D Geometry
        cx, cy, cz = self.source_center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
        
        energy_x = np.sum(rho[cx:, cy, cz])
        energy_y = np.sum(rho[cx, cy:, cz])
        energy_z = np.sum(rho[cx, cy, cz:])
        isotropy_cv = np.std([energy_x, energy_y, energy_z]) / (np.mean([energy_x, energy_y, energy_z]) + 1e-10)
        
        cone_radius = c_mean * t
        inside = r <= cone_radius
        confinement = np.sum(rho[inside]) / (np.sum(rho) + 1e-10) * 100 if cone_radius > 0 else 100
        
        return {
            't': float(t),
            'E_total': float(E_total),
            'E_kinetic': float(E_kinetic),
            'E_gradient': float(E_gradient),
            'S_total': float(S_total),
            'O_total': float(O_total),
            'R_rate': float(R_rate),
            'P_persistence': float(P_persistence),
            'I_TS': float(I_TS),
            'isotropy_cv': float(isotropy_cv),
            'confinement': float(confinement),
            'rho_RS': float(rho_RS),
            'rho_PS': float(rho_PS),
            'rho_OS': float(rho_OS),
        }
    
    def get_field_snapshot(self):
        """Get central slice for visualization."""
        mid = self.size // 2
        rho = self.phi**2 + self.phi_dot**2
        c_eff = self.compute_c_eff()
        
        # Central slice, downsampled
        step = max(1, self.size // 32)
        
        return {
            'rho_xy': rho[:, :, mid][::step, ::step].tolist(),
            'rho_xz': rho[:, mid, :][::step, ::step].tolist(),
            'rho_yz': rho[mid, :, :][::step, ::step].tolist(),
            'c_eff_xy': c_eff[:, :, mid][::step, ::step].tolist(),
        }


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post("/run", response_model=SimulationResult)
async def run_simulation(config: SimulationConfig):
    """Run a QMRT simulation with full metrics."""
    
    start_time = time.time()
    
    # Create simulator
    if config.dimension == "2d":
        sim = QMRTSimulator2D(
            size=config.size,
            beta=config.alpha,
            lambda_relax=config.lambda_relax,
            gamma_wave=config.gamma_wave,
        )
        sim.add_pulse()
    else:
        # 3D uses smaller grid for performance
        size_3d = min(config.size, 50)
        sim = QMRTSimulator3D(
            size=size_3d,
            beta=config.alpha,
            lambda_relax=config.lambda_relax,
            gamma_wave=config.gamma_wave,
        )
        sim.add_pulse()
    
    # Run simulation
    measurements = []
    field_snapshots = []
    
    for step in range(config.steps):
        sim.step()
        
        if step % config.sample_interval == 0:
            t = step * sim.dt
            m = sim.measure(t)
            measurements.append(TimePoint(**{k: v for k, v in m.items() 
                                            if k not in ['rho_RS', 'rho_PS', 'rho_OS']}))
            
            # Store field snapshot every 5 samples
            if len(measurements) % 5 == 0:
                snapshot = sim.get_field_snapshot()
                snapshot['t'] = t
                field_snapshots.append(snapshot)
    
    duration = time.time() - start_time
    
    # Analyze results
    n = len(measurements)
    late_start = int(0.6 * n)
    
    E_late = [m.E_total for m in measurements[late_start:]]
    E_cv = np.std(E_late) / (np.mean(E_late) + 1e-10)
    balance_achieved = E_cv < 0.05
    
    S_mean = np.mean([m.S_total for m in measurements[late_start:]])
    O_mean = np.mean([m.O_total for m in measurements[late_start:]])
    R_mean = np.mean([m.R_rate for m in measurements[late_start:]])
    P_mean = np.mean([m.P_persistence for m in measurements[late_start:]])
    I_TS_mean = np.mean([m.I_TS for m in measurements[late_start:]])
    
    iso_mean = np.mean([m.isotropy_cv for m in measurements[late_start:]])
    conf_mean = np.mean([m.confinement for m in measurements[late_start:]])
    
    # Get final correlations
    final_m = sim.measure(config.steps * sim.dt)
    
    return SimulationResult(
        dimension=config.dimension,
        config=config.model_dump(),
        duration_seconds=duration,
        measurements=measurements,
        
        balance_achieved=balance_achieved,
        balance_E_cv=float(E_cv),
        
        spatial_S_mean=float(S_mean),
        ordering_O_mean=float(O_mean),
        rate_R_mean=float(R_mean),
        persistence_P_mean=float(P_mean),
        coupling_I_TS_mean=float(I_TS_mean),
        
        geometry_isotropic=iso_mean < 0.2,
        geometry_confined=conf_mean > 80,
        
        rho_RS=final_m['rho_RS'],
        rho_PS=final_m['rho_PS'],
        rho_OS=final_m['rho_OS'],
        
        field_snapshots=field_snapshots,
    )


@router.get("/info")
async def get_simulation_info():
    """Get information about the QMRT simulation."""
    return {
        "theory": "Quark Medium Relativity Theory (QMRT)",
        "description": "Dynamical medium simulation for emergent spacetime",
        "components": {
            "S": "Spatial geometry structure (metric variation)",
            "O": "Ordering structure (causal path diversity)",
            "R": "Rate (temporal dynamics)",
            "P": "Persistence (configuration stability)",
            "I_TS": "Spacetime coupling integral",
        },
        "validated_results": {
            "scaling": "O ~ S² (universal exponent α = 2)",
            "balance": "Driven-dissipative equilibrium",
            "3d_isotropy": "Spherical light cones confirmed",
        },
        "parameters": {
            "alpha": "Backreaction coupling (β)",
            "lambda": "Relaxation rate (λ)",
            "gamma": "Wave damping (γ)",
        }
    }
