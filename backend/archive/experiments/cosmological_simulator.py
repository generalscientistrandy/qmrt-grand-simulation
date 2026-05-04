"""
QMRT Cosmological Simulator - Mode 1: Full Experimental Simulation
Evolves universe from primordial state through structure formation
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
import math
from physics_engine import QMRTSubstrate


class CosmologicalEpoch:
    """Represents a specific epoch in cosmological evolution"""
    PRIMORDIAL = "primordial"  # t ≈ 0, quantum fluctuations
    INFLATION = "inflation"     # Rapid expansion phase
    RADIATION = "radiation"     # Radiation-dominated era
    MATTER = "matter"          # Matter-dominated era
    STRUCTURE = "structure"    # Large-scale structure formation
    STELLAR = "stellar"        # Star and galaxy formation
    PLANETARY = "planetary"    # Planetary system formation
    CONTEMPORARY = "contemporary"  # Present-day epoch


class CosmologicalSnapshot:
    """Snapshot of substrate state at a specific epoch"""
    def __init__(self, epoch: str, time: float, substrate_state: Dict, metrics: Dict):
        self.epoch = epoch
        self.time = time
        self.substrate_state = substrate_state
        self.metrics = metrics
        self.structure_seeds = []


class CosmologicalSimulator:
    """Mode 1: Full cosmological simulation from primordial to planetary scales"""
    
    def __init__(self, grid_size: int = 64, hubble_parameter: float = 0.07):
        self.grid_size = grid_size
        self.H0 = hubble_parameter  # Hubble parameter (expansion rate)
        
        # Substrate physics engine
        self.substrate = QMRTSubstrate(grid_size=grid_size, scale=1.0)
        
        # Cosmological parameters
        self.scale_factor = 1e-6  # Start very small (early universe)
        self.cosmic_time = 0.0
        
        # Evolution tracking
        self.current_epoch = CosmologicalEpoch.PRIMORDIAL
        self.snapshots: List[CosmologicalSnapshot] = []
        self.structure_seeds: List[Dict] = []
        
    def initialize_primordial_fluctuations(self, amplitude: float = 1e-5, seed: Optional[int] = None):
        """Initialize quantum fluctuations in primordial substrate
        
        Based on QMRT: Early universe coherence phase fluctuations
        ΦΞ ~ quantum vacuum fluctuations
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Quantum vacuum state - very small perturbations
        self.substrate.rho_xi = np.ones((self.grid_size, self.grid_size, self.grid_size))
        self.substrate.T_xi = np.ones((self.grid_size, self.grid_size, self.grid_size))
        
        # Coherence phase quantum fluctuations (primary source)
        freq_space = np.fft.fftn(np.random.randn(self.grid_size, self.grid_size, self.grid_size))
        
        # Power spectrum: P(k) ~ k^n with n ≈ 1 (scale-invariant)
        kx = np.fft.fftfreq(self.grid_size)
        ky = np.fft.fftfreq(self.grid_size)
        kz = np.fft.fftfreq(self.grid_size)
        kx, ky, kz = np.meshgrid(kx, ky, kz, indexing='ij')
        k = np.sqrt(kx**2 + ky**2 + kz**2)
        k[0, 0, 0] = 1  # Avoid division by zero
        
        power_spectrum = k  # Scale-invariant (n=1)
        freq_space *= power_spectrum * amplitude
        
        self.substrate.phi_xi = np.real(np.fft.ifftn(freq_space))
        
        # Torsion fluctuations (subdominant)
        self.substrate.tau_xi = amplitude * 0.1 * np.random.randn(self.grid_size, self.grid_size, self.grid_size, 3)
        
        self.current_epoch = CosmologicalEpoch.PRIMORDIAL
        self.cosmic_time = 0.0
        print(f"✓ Initialized primordial quantum fluctuations (amplitude={amplitude})")
        
    def evolve_inflation(self, e_folds: float = 60.0, steps: int = 100):
        """Inflate the universe - exponential expansion phase
        
        Scale factor: a(t) ~ exp(H*t)
        Substrate stretching amplifies fluctuations
        """
        dt = e_folds / steps / self.H0
        
        for i in range(steps):
            # Exponential expansion (with overflow protection)
            expansion_factor = min(self.H0 * dt, 1.0)  # Limit to prevent overflow
            self.scale_factor *= (1.0 + expansion_factor)
            
            # Evolve substrate with expansion
            self.substrate.evolve_substrate(dt=dt * 0.1, steps=5)
            
            # Stretch wavelengths (comoving coordinates)
            stretch_factor = 1.0 + expansion_factor * 0.01
            self.substrate.phi_xi *= stretch_factor
            
            self.cosmic_time += dt
            
        self.current_epoch = CosmologicalEpoch.INFLATION
        print(f"✓ Inflation complete: {e_folds} e-folds, scale factor = {self.scale_factor:.2e}")
        
    def evolve_radiation_era(self, duration: float = 1000.0, steps: int = 200):
        """Radiation-dominated era
        
        Substrate tension dominates (TΞ ~ radiation pressure)
        """
        dt = duration / steps
        
        for i in range(steps):
            # Radiation-dominated expansion: a(t) ~ t^(1/2)
            self.scale_factor = math.sqrt(self.cosmic_time + dt)
            
            # Evolve substrate (tension-dominated)
            self.substrate.evolve_substrate(dt=dt * 0.05, steps=3)
            
            # Cooling: T_eff ~ 1/a
            cooling_factor = 0.999
            self.substrate.T_xi *= cooling_factor
            
            self.cosmic_time += dt
            
        self.current_epoch = CosmologicalEpoch.RADIATION
        print(f"✓ Radiation era evolved: t = {self.cosmic_time:.1f}, scale = {self.scale_factor:.2e}")
        
    def evolve_matter_era(self, duration: float = 5000.0, steps: int = 300):
        """Matter-dominated era - density perturbations grow
        
        Substrate density ρΞ becomes dominant
        Gravitational instability from density fluctuations
        """
        dt = duration / steps
        
        for i in range(steps):
            # Matter-dominated expansion: a(t) ~ t^(2/3)
            self.scale_factor = (self.cosmic_time + dt) ** (2.0/3.0)
            
            # Density perturbations grow (limited growth)
            lap_rho = self.substrate.xi_laplacian(self.substrate.rho_xi)
            growth_rate = 0.0001  # Reduced from 0.001
            self.substrate.rho_xi += growth_rate * lap_rho * dt
            
            # Renormalize to prevent explosion
            if i % 50 == 0:
                self.substrate.rho_xi /= np.mean(self.substrate.rho_xi)
            
            # Evolve substrate
            if i % 10 == 0:
                self.substrate.evolve_substrate(dt=dt * 0.01, steps=1)
            
            self.cosmic_time += dt
            
        self.current_epoch = CosmologicalEpoch.MATTER
        print(f"✓ Matter era evolved: t = {self.cosmic_time:.1f}, density contrast = {np.std(self.substrate.rho_xi):.3f}")
        
    def evolve_structure_formation(self, duration: float = 3000.0, steps: int = 500):
        """Large-scale structure formation from density perturbations
        
        Gravitational collapse in overdense regions
        Formation of cosmic web structure
        """
        dt = duration / steps
        
        for i in range(steps):
            # Continued expansion (slower)
            self.scale_factor *= 1.0 + self.H0 * dt * 0.0001
            
            # Nonlinear structure growth
            lap_rho = self.substrate.xi_laplacian(self.substrate.rho_xi)
            grad_rho = self.substrate.xi_gradient(self.substrate.rho_xi)
            
            # Gravitational collapse (limited to prevent explosion)
            growth = 0.0001 * lap_rho * dt
            self.substrate.rho_xi += growth
            
            # Renormalize periodically
            if i % 100 == 0:
                rho_mean = np.mean(self.substrate.rho_xi)
                self.substrate.rho_xi = 1.0 + (self.substrate.rho_xi - rho_mean) * 0.5
            
            # Torsion develops from rotational collapse
            if i % 10 == 0:
                self.substrate.tau_xi[:, :, :, 0] += 0.00001 * grad_rho[:, :, :, 1] * dt
                self.substrate.tau_xi[:, :, :, 1] -= 0.00001 * grad_rho[:, :, :, 0] * dt
            
            # Evolve full substrate
            if i % 20 == 0:
                self.substrate.evolve_substrate(dt=dt * 0.1, steps=2)
            
            self.cosmic_time += dt
            
        # Identify structure seeds (local density maxima)
        self._identify_structure_seeds()
        
        self.current_epoch = CosmologicalEpoch.STRUCTURE
        print(f"✓ Structure formation: t = {self.cosmic_time:.1f}, {len(self.structure_seeds)} seeds identified")
        
    def _identify_structure_seeds(self, threshold: float = 1.1):
        """Identify regions that can collapse into stellar/planetary systems"""
        self.structure_seeds = []
        
        # Find local maxima in density field above threshold
        rho_mean = np.mean(self.substrate.rho_xi)
        
        for i in range(3, self.grid_size - 3, 2):  # Sample every other point for speed
            for j in range(3, self.grid_size - 3, 2):
                for k in range(3, self.grid_size - 3, 2):
                    rho = self.substrate.rho_xi[i, j, k]
                    
                    if rho > threshold * rho_mean:
                        # Check if local maximum
                        neighbors = [
                            self.substrate.rho_xi[i+di, j+dj, k+dk]
                            for di in [-1, 0, 1]
                            for dj in [-1, 0, 1]
                            for dk in [-1, 0, 1]
                            if not (di == 0 and dj == 0 and dk == 0)
                        ]
                        
                        if rho >= max(neighbors):  # >= instead of > to allow plateaus
                            # Extract local substrate properties
                            local_window = 2
                            i1, i2 = max(0, i-local_window), min(self.grid_size, i+local_window+1)
                            j1, j2 = max(0, j-local_window), min(self.grid_size, j+local_window+1)
                            k1, k2 = max(0, k-local_window), min(self.grid_size, k+local_window+1)
                            
                            seed = {
                                'position': (int(i), int(j), int(k)),
                                'density': float(rho),
                                'tension': float(self.substrate.T_xi[i, j, k]),
                                'torsion': float(np.linalg.norm(self.substrate.tau_xi[i, j, k])),
                                'coherence': float(self.substrate.phi_xi[i, j, k]),
                                'density_contrast': float(rho / rho_mean),
                                'local_rho_mean': float(np.mean(self.substrate.rho_xi[i1:i2, j1:j2, k1:k2])),
                                'local_T_mean': float(np.mean(self.substrate.T_xi[i1:i2, j1:j2, k1:k2])),
                                'local_tau_mean': float(np.mean(np.linalg.norm(self.substrate.tau_xi[i1:i2, j1:j2, k1:k2], axis=-1))),
                                'local_phi_mean': float(np.mean(self.substrate.phi_xi[i1:i2, j1:j2, k1:k2])),
                            }
                            
                            self.structure_seeds.append(seed)
        
        print(f"  Found {len(self.structure_seeds)} potential structure seeds (threshold={threshold}x mean density)")
        
    def create_snapshot(self) -> CosmologicalSnapshot:
        """Create snapshot of current cosmological state"""
        metrics = self.substrate.get_substrate_metrics()
        metrics['scale_factor'] = self.scale_factor
        metrics['cosmic_time'] = self.cosmic_time
        metrics['hubble_parameter'] = self.H0
        
        snapshot = CosmologicalSnapshot(
            epoch=self.current_epoch,
            time=self.cosmic_time,
            substrate_state={
                'rho_xi': self.substrate.rho_xi.copy(),
                'T_xi': self.substrate.T_xi.copy(),
                'tau_xi': self.substrate.tau_xi.copy(),
                'phi_xi': self.substrate.phi_xi.copy(),
            },
            metrics=metrics
        )
        
        snapshot.structure_seeds = self.structure_seeds.copy()
        self.snapshots.append(snapshot)
        
        return snapshot
    
    def run_full_simulation(self, seed: Optional[int] = None) -> Dict:
        """Run complete cosmological simulation from primordial to structure formation"""
        print("\n=== QMRT MODE 1: FULL COSMOLOGICAL SIMULATION ===")
        
        # 1. Primordial quantum fluctuations
        self.initialize_primordial_fluctuations(amplitude=1e-5, seed=seed)
        self.create_snapshot()
        
        # 2. Inflationary epoch
        self.evolve_inflation(e_folds=60.0, steps=100)
        self.create_snapshot()
        
        # 3. Radiation-dominated era
        self.evolve_radiation_era(duration=1000.0, steps=200)
        self.create_snapshot()
        
        # 4. Matter-dominated era
        self.evolve_matter_era(duration=5000.0, steps=300)
        self.create_snapshot()
        
        # 5. Structure formation
        self.evolve_structure_formation(duration=3000.0, steps=500)
        final_snapshot = self.create_snapshot()
        
        print(f"\n✓ Cosmological simulation complete!")
        print(f"  Final epoch: {self.current_epoch}")
        print(f"  Cosmic time: {self.cosmic_time:.1f}")
        print(f"  Scale factor: {self.scale_factor:.2e}")
        print(f"  Structure seeds: {len(self.structure_seeds)}")
        print(f"  Snapshots: {len(self.snapshots)}")
        
        return {
            'final_epoch': self.current_epoch,
            'cosmic_time': self.cosmic_time,
            'scale_factor': self.scale_factor,
            'num_structure_seeds': len(self.structure_seeds),
            'structure_seeds': self.structure_seeds,
            'snapshots': len(self.snapshots),
            'final_metrics': final_snapshot.metrics,
            'seed': seed
        }
