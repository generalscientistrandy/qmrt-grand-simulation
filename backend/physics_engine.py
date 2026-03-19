"""
QMRT Physics Engine - Authoritative Substrate Layer
Implements Quark Medium Relativity Theory equations
"""
import numpy as np
from typing import Dict, List, Tuple
import math


class QMRTSubstrate:
    """Core QMRT substrate physics engine implementing the four fundamental properties"""
    
    def __init__(self, grid_size: int = 64, scale: float = 1.0):
        self.grid_size = grid_size
        self.scale = scale
        
        # Fundamental substrate properties (the four pillars)
        self.rho_xi = np.zeros((grid_size, grid_size, grid_size))  # Density
        self.T_xi = np.zeros((grid_size, grid_size, grid_size))    # Tension
        self.tau_xi = np.zeros((grid_size, grid_size, grid_size, 3))  # Torsion (vector field)
        self.phi_xi = np.zeros((grid_size, grid_size, grid_size))  # Coherence phase
        
        # Physical constants
        self.c_xi = 1.0  # Substrate wave speed
        self.k_B = 1.0   # Boltzmann-like constant
        
        # Coupling coefficients
        self.alpha_rho = 0.1
        self.alpha_T = 0.1
        self.alpha_tau = 0.15
        self.gamma_phi = 0.2
        
        # Wave equation coefficients
        self.A_phi = 1.0
        self.B_phi = 0.3
        self.C_phi = 0.2
        self.A_rho = 1.0
        self.B_rho = 0.4
        self.A_T = 1.0
        self.B_T = 0.3
        self.A_tau = 1.0
        
    def initialize_random_perturbations(self, amplitude: float = 0.1, seed: int = None):
        """Initialize substrate with random quantum perturbations"""
        if seed is not None:
            np.random.seed(seed)
            
        self.rho_xi = 1.0 + amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size)
        self.T_xi = 1.0 + amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size)
        self.tau_xi = amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size, 3)
        self.phi_xi = amplitude * np.random.randn(self.grid_size, self.grid_size, self.grid_size)
        
    def xi_laplacian(self, field: np.ndarray) -> np.ndarray:
        """Compute Xi-Laplacian operator (substrate-modified Laplacian)"""
        # Simple finite difference approximation
        laplacian = np.zeros_like(field)
        
        if field.ndim == 3:
            # Scalar field
            laplacian[1:-1, 1:-1, 1:-1] = (
                field[2:, 1:-1, 1:-1] + field[:-2, 1:-1, 1:-1] +
                field[1:-1, 2:, 1:-1] + field[1:-1, :-2, 1:-1] +
                field[1:-1, 1:-1, 2:] + field[1:-1, 1:-1, :-2] -
                6 * field[1:-1, 1:-1, 1:-1]
            )
        elif field.ndim == 4:
            # Vector field
            for i in range(field.shape[3]):
                laplacian[:, :, :, i] = self.xi_laplacian(field[:, :, :, i])
                
        return laplacian
    
    def xi_gradient(self, field: np.ndarray) -> np.ndarray:
        """Compute Xi-gradient operator"""
        grad = np.zeros((*field.shape, 3))
        grad[1:-1, 1:-1, 1:-1, 0] = (field[2:, 1:-1, 1:-1] - field[:-2, 1:-1, 1:-1]) / 2
        grad[1:-1, 1:-1, 1:-1, 1] = (field[1:-1, 2:, 1:-1] - field[1:-1, :-2, 1:-1]) / 2
        grad[1:-1, 1:-1, 1:-1, 2] = (field[1:-1, 1:-1, 2:] - field[1:-1, 1:-1, :-2]) / 2
        return grad
    
    def evolve_substrate(self, dt: float = 0.01, steps: int = 100):
        """Evolve substrate fields using coupled wave equations"""
        # Velocity fields for wave evolution
        v_phi = np.zeros_like(self.phi_xi)
        v_rho = np.zeros_like(self.rho_xi)
        v_T = np.zeros_like(self.T_xi)
        v_tau = np.zeros_like(self.tau_xi)
        
        for _ in range(steps):
            # Compute Laplacians
            lap_phi = self.xi_laplacian(self.phi_xi)
            lap_rho = self.xi_laplacian(self.rho_xi)
            lap_T = self.xi_laplacian(self.T_xi)
            lap_tau = self.xi_laplacian(self.tau_xi)
            
            # Coupled wave equations (from QMRT Part 2)
            # ∂²(ΦΞ)/∂t² = A_phi Xi_Lap(ΦΞ) + B_phi Xi_Lap(ρΞ) + C_phi Xi_Lap(TΞ)
            a_phi = self.A_phi * lap_phi + self.B_phi * lap_rho + self.C_phi * lap_T
            
            # ∂²(ρΞ)/∂t² = A_rho Xi_Lap(ρΞ) + B_rho Xi_Lap(TΞ)
            a_rho = self.A_rho * lap_rho + self.B_rho * lap_T
            
            # ∂²(TΞ)/∂t² = A_T Xi_Lap(TΞ) + B_T Xi_Lap(ρΞ)
            a_T = self.A_T * lap_T + self.B_T * lap_rho
            
            # ∂²(τΞ)/∂t² = A_tau Xi_Lap(τΞ) + curl_terms
            a_tau = self.A_tau * lap_tau
            
            # Leapfrog integration
            v_phi += a_phi * dt
            v_rho += a_rho * dt
            v_T += a_T * dt
            v_tau += a_tau * dt
            
            self.phi_xi += v_phi * dt
            self.rho_xi += v_rho * dt
            self.T_xi += v_T * dt
            self.tau_xi += v_tau * dt
            
            # Add damping to prevent instabilities
            v_phi *= 0.995
            v_rho *= 0.995
            v_T *= 0.995
            v_tau *= 0.995
    
    def compute_effective_temperature(self) -> np.ndarray:
        """Compute effective temperature from substrate gradients
        T_eff = (1/k_B)(||∇ΦΞ||² + ||τΞ||² + ||ρΞ'||²)
        """
        grad_phi = self.xi_gradient(self.phi_xi)
        grad_rho = self.xi_gradient(self.rho_xi)
        
        grad_phi_mag_sq = np.sum(grad_phi**2, axis=-1)
        tau_mag_sq = np.sum(self.tau_xi**2, axis=-1)
        grad_rho_mag_sq = np.sum(grad_rho**2, axis=-1)
        
        T_eff = (1.0 / self.k_B) * (grad_phi_mag_sq + tau_mag_sq + grad_rho_mag_sq)
        return T_eff
    
    def compute_curvature(self) -> np.ndarray:
        """Compute substrate curvature
        R ∝ α_ρ ∇²(ρΞ) + α_T ∇²(TΞ) + α_τ |τΞ|²
        """
        lap_rho = self.xi_laplacian(self.rho_xi)
        lap_T = self.xi_laplacian(self.T_xi)
        tau_mag_sq = np.sum(self.tau_xi**2, axis=-1)
        
        curvature = self.alpha_rho * lap_rho + self.alpha_T * lap_T + self.alpha_tau * tau_mag_sq
        return curvature
    
    def get_substrate_metrics(self) -> Dict[str, float]:
        """Extract key substrate metrics for world generation"""
        T_eff = self.compute_effective_temperature()
        curvature = self.compute_curvature()
        
        grad_phi = self.xi_gradient(self.phi_xi)
        grad_phi_mag = np.sqrt(np.sum(grad_phi**2, axis=-1))
        tau_mag = np.sqrt(np.sum(self.tau_xi**2, axis=-1))
        
        metrics = {
            'mean_density': float(np.mean(self.rho_xi)),
            'std_density': float(np.std(self.rho_xi)),
            'mean_tension': float(np.mean(self.T_xi)),
            'std_tension': float(np.std(self.T_xi)),
            'mean_torsion': float(np.mean(tau_mag)),
            'max_torsion': float(np.max(tau_mag)),
            'mean_coherence_gradient': float(np.mean(grad_phi_mag)),
            'max_coherence_gradient': float(np.max(grad_phi_mag)),
            'mean_temperature': float(np.mean(T_eff)),
            'max_temperature': float(np.max(T_eff)),
            'mean_curvature': float(np.mean(np.abs(curvature))),
            'max_curvature': float(np.max(np.abs(curvature))),
        }
        
        return metrics
