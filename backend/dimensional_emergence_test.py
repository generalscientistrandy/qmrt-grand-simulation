"""
Dimensional Emergence Long-Horizon Test
=========================================

PURPOSE: Track degrees-of-freedom emergence from the QMRT medium,
measuring transition points from 1D → 2D → 3D effective dimensionality.

CHECKPOINTING: Full state preservation including RNG for exact resume.

METRICS (per user spec):
  - D_eff = (λ1 + λ2 + λ3)² / (λ1² + λ2² + λ3²)
  - r2 = λ2 / λ1
  - r3 = λ3 / λ1
  - anisotropy index
  - tau_mean, tau_std, tau_localization

PHASE LABELS:
  - pre_spatial / branching
  - 1D_candidate → 1D_stable
  - 2D_candidate → 2D_stable
  - 3D_candidate → 3D_stable

TRANSITION LOGIC: Requires persistence over N consecutive checkpoints.

TIME TRACKING:
  - global_T: total simulation time since origin
  - phase_T: time since current dimensional phase stabilized

BASELINE: Regulated Recovery v1.1

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label
from scipy.linalg import eigh
from typing import Dict, List, Optional, Any
import time
import json
import pickle
import os
import argparse


class DimensionalEmergenceSimulator:
    """
    Simulator for tracking dimensional emergence over time.
    
    Full state checkpoint includes RNG state for exact resume.
    """
    
    def __init__(self, size: int = 48, dt: float = 0.10, seed: int = None, 
                 initial_condition: str = 'line_seed'):
        """
        Initialize simulator with Regulated Recovery v1.1 baseline.
        
        Parameters:
        -----------
        initial_condition : str
            - 'random': Small random perturbations (isotropic from start)
            - 'line_seed': Vortices seeded along a line (start from 1D-like)
            - 'plane_seed': Vortices seeded in a plane (start from 2D-like)
            - 'point_seed': Single vortex at center (minimal structure)
        """
        
        # Configuration (immutable)
        self.config = {
            'size': size,
            'dt': dt,
            'initial_seed': seed,
            'initial_condition': initial_condition,
            'damping_to_tau': 0.20,
            'tau_cap': 1.8,
            'tau_creation_threshold': 1.001,
            'creation_rate': 0.15,
            'tau_response': 0.02,
            'tau_relaxation': 0.01,
            'c_0_sq': 4.0,
            'gamma': 0.007,
        }
        
        self.size = size
        self.dt = dt
        
        # Set RNG with seed
        if seed is not None:
            np.random.seed(seed)
        self._rng_state = np.random.get_state()
        
        # Time tracking
        self.global_T = 0.0  # Total simulation time
        self.phase_T = 0.0   # Time since current phase stabilized
        self.step_count = 0
        
        # Regulated Recovery v1.1 parameters
        self.damping_to_tau = self.config['damping_to_tau']
        self.tau_cap = self.config['tau_cap']
        self.tau_creation_threshold = self.config['tau_creation_threshold']
        self.creation_rate = self.config['creation_rate']
        self.tau_response = self.config['tau_response']
        self.tau_relaxation = self.config['tau_relaxation']
        self.c_0_sq = self.config['c_0_sq']
        self.gamma = self.config['gamma']
        
        # Wave field - initialize based on initial condition
        self.psi_r = np.ones((size, size, size)) * 1.0
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Apply initial condition
        self._apply_initial_condition(initial_condition)
        
        # Medium field
        self.tau = np.ones((size, size, size))
    
    def _apply_initial_condition(self, condition: str):
        """
        Apply initial condition to seed dimensional structure.
        
        This determines where the simulation starts in dimensionality space.
        """
        center = self.size // 2
        
        if condition == 'random':
            # Small random perturbations - isotropic from start
            self.psi_r += np.random.randn(self.size, self.size, self.size) * 0.01
            self.psi_i += np.random.randn(self.size, self.size, self.size) * 0.01
            
        elif condition == 'line_seed':
            # Seed vortices along a line (z-axis) - start from 1D-like
            # This creates activity concentrated along one direction
            n_vortices = 8
            for i in range(n_vortices):
                z = int(center - n_vortices//2 * 3 + i * 3)
                z = max(3, min(self.size - 3, z))
                chirality = 1 if i % 2 == 0 else -1
                self._inject_vortex(center, center, z, chirality)
            # Small noise to break perfect symmetry
            self.psi_r += np.random.randn(self.size, self.size, self.size) * 0.001
            self.psi_i += np.random.randn(self.size, self.size, self.size) * 0.001
            
        elif condition == 'plane_seed':
            # Seed vortices in a plane (x-y plane at z=center) - start from 2D-like
            n_per_side = 4
            spacing = 5
            for i in range(n_per_side):
                for j in range(n_per_side):
                    cx = center - (n_per_side//2) * spacing + i * spacing
                    cy = center - (n_per_side//2) * spacing + j * spacing
                    cx = max(3, min(self.size - 3, cx))
                    cy = max(3, min(self.size - 3, cy))
                    chirality = 1 if (i + j) % 2 == 0 else -1
                    self._inject_vortex(cx, cy, center, chirality)
            # Small noise
            self.psi_r += np.random.randn(self.size, self.size, self.size) * 0.001
            self.psi_i += np.random.randn(self.size, self.size, self.size) * 0.001
            
        elif condition == 'point_seed':
            # Single vortex at center - minimal starting structure
            self._inject_vortex(center, center, center, 1)
            self.psi_r += np.random.randn(self.size, self.size, self.size) * 0.001
            self.psi_i += np.random.randn(self.size, self.size, self.size) * 0.001
            
        else:
            raise ValueError(f"Unknown initial condition: {condition}")
        
        # Channel and remnant fields
        self.channel_field = np.zeros((self.size, self.size, self.size))
        self.remnant_field = np.zeros((self.size, self.size, self.size))
        
        # Event counters
        self.total_creations = 0
        self.total_annihilations = 0
        
        # Dimensional tracking
        self.current_phase = 'pre_spatial'
        self.phase_history = []  # List of phase transitions
        self.dimension_history = []  # Per-checkpoint metrics
        self.transition_log = []  # Detailed transition events
        
        # Stability tracking for transitions
        self.phase_stability_count = 0
        self.stability_threshold = 5  # Checkpoints required for stable phase
        
        # Transition times
        self.transition_times = {
            'T_1D_candidate': None,
            'T_1D_stable': None,
            'T_2D_candidate': None,
            'T_2D_stable': None,
            'T_3D_candidate': None,
            'T_3D_stable': None,
        }
    
    def _inject_vortex(self, cx: int, cy: int, cz: int, chirality: int = 1):
        """Inject a vortex at specified location."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / 18)
        
        vortex = np.tanh(r / 2.5) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        blend = 0.15 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def step(self):
        """Advance simulation by one timestep with creation events."""
        self.step_count += 1
        self.global_T += self.dt
        self.phase_T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # τ dynamics with regulated recovery
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        if self.damping_to_tau > 0:
            self.tau += self.damping_to_tau * damped_energy
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Creation events
        high_tau_mask = self.tau > self.tau_creation_threshold
        if np.any(high_tau_mask):
            n_candidates = np.sum(high_tau_mask)
            create_prob = self.creation_rate * (self.tau[high_tau_mask] - self.tau_creation_threshold)
            create_mask_1d = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask_1d):
                coords = np.array(np.where(high_tau_mask)).T
                create_coords = coords[create_mask_1d]
                
                for (cx, cy, cz) in create_coords[:3]:
                    chirality = np.random.choice([-1, 1])
                    self._inject_vortex(cx, cy, cz, chirality)
                    self.tau[cx, cy, cz] = 1.0
                    self.total_creations += 1
        
        # Wave equation with variable c_eff
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        # Update channel and remnant fields
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology_norm = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology_norm = topology_norm / (np.max(topology_norm) + 1e-10)
        
        self.channel_field += 0.01 * (topology_norm - self.channel_field)
        self.channel_field = np.clip(self.channel_field, 0, 1)
        
        self.remnant_field += 0.02 * topology_norm
        self.remnant_field *= 0.999
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
    
    def detect_defects(self, threshold: float = 0.5) -> int:
        """Detect and count topological defects."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        count = 0
        for i in range(1, n + 1):
            if np.sum(labeled == i) >= 3:
                count += 1
        return count
    
    def compute_dimensional_metrics(self) -> Dict[str, Any]:
        """
        Compute dimensionality metrics from active topology distribution.
        
        Uses eigenvalue analysis of position covariance for high-activity cells.
        """
        # Get topology activity field
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Threshold for "active" cells (top 10% of topology activity)
        threshold = np.percentile(topology, 90)
        active_mask = topology > threshold
        n_active = np.sum(active_mask)
        
        if n_active < 10:
            # Not enough activity for meaningful dimensionality
            return {
                'valid': False,
                'D_eff': 0.0,
                'r2': 0.0,
                'r3': 0.0,
                'anisotropy': 1.0,
                'n_active': int(n_active),
                'n_defects': self.detect_defects(),
                'tau_mean': float(np.mean(self.tau)),
                'tau_std': float(np.std(self.tau)),
                'tau_localization': float(np.max(self.tau) / np.mean(self.tau)),
            }
        
        # Get positions of active cells
        active_coords = np.array(np.where(active_mask)).T  # Shape: (n_active, 3)
        
        # Compute weighted positions (weight by topology strength)
        weights = topology[active_mask]
        weights = weights / np.sum(weights)
        
        # Compute centroid
        centroid = np.average(active_coords, axis=0, weights=weights)
        
        # Compute weighted covariance matrix
        centered = active_coords - centroid
        cov = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                cov[i, j] = np.sum(weights * centered[:, i] * centered[:, j])
        
        # Eigenvalue decomposition
        eigenvalues, _ = eigh(cov)
        eigenvalues = np.sort(eigenvalues)[::-1]  # Descending order: λ1 ≥ λ2 ≥ λ3
        eigenvalues = np.maximum(eigenvalues, 1e-10)  # Avoid division by zero
        
        lambda1, lambda2, lambda3 = eigenvalues
        
        # D_eff = (λ1 + λ2 + λ3)² / (λ1² + λ2² + λ3²)
        # Ranges from 1 (line) to 3 (isotropic volume)
        sum_lambda = lambda1 + lambda2 + lambda3
        sum_lambda_sq = lambda1**2 + lambda2**2 + lambda3**2
        D_eff = sum_lambda**2 / sum_lambda_sq if sum_lambda_sq > 0 else 1.0
        
        # Eigenvalue ratios
        r2 = lambda2 / lambda1 if lambda1 > 0 else 0.0
        r3 = lambda3 / lambda1 if lambda1 > 0 else 0.0
        
        # Anisotropy = 1 - (smallest / largest)
        anisotropy = 1 - (lambda3 / lambda1) if lambda1 > 0 else 1.0
        
        return {
            'valid': True,
            'D_eff': float(D_eff),
            'r2': float(r2),
            'r3': float(r3),
            'eigenvalues': [float(lambda1), float(lambda2), float(lambda3)],
            'anisotropy': float(anisotropy),
            'n_active': int(n_active),
            'n_defects': self.detect_defects(),
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'tau_localization': float(np.max(self.tau) / np.mean(self.tau)),
        }
    
    def classify_phase(self, D_eff: float, r2: float, r3: float) -> str:
        """
        Classify current phase based on dimensionality metrics.
        
        Returns: 'pre_spatial', '1D_candidate', '2D_candidate', '3D_candidate'
        """
        if D_eff < 0.8:
            return 'pre_spatial'
        elif D_eff < 1.3:
            # 1D-like: D_eff ≈ 1
            return '1D_candidate'
        elif D_eff < 2.3 and r2 >= 0.15:
            # 2D-like: D_eff ≈ 2, r2 significant
            return '2D_candidate'
        elif D_eff >= 2.3 and r2 >= 0.35 and r3 >= 0.15:
            # 3D-like: D_eff ≈ 3, both r2 and r3 significant
            return '3D_candidate'
        else:
            # Transitional state
            return self.current_phase.replace('_stable', '_candidate').replace('_candidate', '_candidate')
    
    def update_phase_tracking(self, metrics: Dict[str, Any]):
        """
        Update phase tracking with persistence-based transition logic.
        
        Transitions require stability over several consecutive checkpoints.
        """
        if not metrics['valid']:
            return
        
        D_eff = metrics['D_eff']
        r2 = metrics['r2']
        r3 = metrics['r3']
        
        candidate_phase = self.classify_phase(D_eff, r2, r3)
        
        # Check if same candidate as current
        current_base = self.current_phase.replace('_stable', '_candidate')
        
        if candidate_phase == current_base or candidate_phase == self.current_phase:
            # Same phase, increment stability
            self.phase_stability_count += 1
            
            # Check for promotion to stable
            if self.phase_stability_count >= self.stability_threshold:
                stable_phase = candidate_phase.replace('_candidate', '_stable')
                
                if stable_phase != self.current_phase:
                    # Phase transition to stable!
                    old_phase = self.current_phase
                    self.current_phase = stable_phase
                    self.phase_T = 0.0  # Reset phase clock
                    
                    # Record transition
                    transition_event = {
                        'from_phase': old_phase,
                        'to_phase': stable_phase,
                        'global_T': self.global_T,
                        'D_eff': D_eff,
                        'r2': r2,
                        'r3': r3,
                        'stability_count': self.phase_stability_count,
                    }
                    self.transition_log.append(transition_event)
                    self.phase_history.append((self.global_T, stable_phase))
                    
                    # Record transition times
                    if '1D' in stable_phase and self.transition_times['T_1D_stable'] is None:
                        self.transition_times['T_1D_stable'] = self.global_T
                    if '2D' in stable_phase and self.transition_times['T_2D_stable'] is None:
                        self.transition_times['T_2D_stable'] = self.global_T
                    if '3D' in stable_phase and self.transition_times['T_3D_stable'] is None:
                        self.transition_times['T_3D_stable'] = self.global_T
        else:
            # Different candidate phase
            if candidate_phase != 'pre_spatial':
                # Moving to new candidate
                self.current_phase = candidate_phase
                self.phase_stability_count = 1
                
                # Record candidate times
                if '1D' in candidate_phase and self.transition_times['T_1D_candidate'] is None:
                    self.transition_times['T_1D_candidate'] = self.global_T
                if '2D' in candidate_phase and self.transition_times['T_2D_candidate'] is None:
                    self.transition_times['T_2D_candidate'] = self.global_T
                if '3D' in candidate_phase and self.transition_times['T_3D_candidate'] is None:
                    self.transition_times['T_3D_candidate'] = self.global_T
            else:
                # Back to pre-spatial
                self.current_phase = 'pre_spatial'
                self.phase_stability_count = 0
    
    def record_checkpoint_metrics(self, metrics: Dict[str, Any]):
        """Record metrics for this checkpoint."""
        record = {
            'global_T': self.global_T,
            'phase_T': self.phase_T,
            'step_count': self.step_count,
            'current_phase': self.current_phase,
            'D_eff': metrics.get('D_eff', 0.0),
            'r2': metrics.get('r2', 0.0),
            'r3': metrics.get('r3', 0.0),
            'anisotropy': metrics.get('anisotropy', 1.0),
            'n_active': metrics.get('n_active', 0),
            'n_defects': metrics.get('n_defects', 0),
            'tau_mean': metrics.get('tau_mean', 1.0),
            'tau_std': metrics.get('tau_std', 0.0),
            'tau_localization': metrics.get('tau_localization', 1.0),
            'total_creations': self.total_creations,
            'total_annihilations': self.total_annihilations,
        }
        self.dimension_history.append(record)
    
    def compute_total_energy(self) -> float:
        """Compute total system energy for validation."""
        kinetic = 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        potential = 0.5 * (self.psi_r**2 + self.psi_i**2)
        return float(np.sum(kinetic + potential))
    
    def save_checkpoint(self, filepath: str):
        """
        Save complete simulation state for exact resume.
        
        Includes RNG state for reproducibility.
        """
        # Store current RNG state
        self._rng_state = np.random.get_state()
        
        state = {
            # Configuration
            'config': self.config,
            
            # Time tracking
            'global_T': self.global_T,
            'phase_T': self.phase_T,
            'step_count': self.step_count,
            
            # Phase tracking
            'current_phase': self.current_phase,
            'phase_stability_count': self.phase_stability_count,
            'transition_times': self.transition_times,
            'phase_history': self.phase_history,
            'dimension_history': self.dimension_history,
            'transition_log': self.transition_log,
            
            # Counters
            'total_creations': self.total_creations,
            'total_annihilations': self.total_annihilations,
            
            # RNG state (critical for exact resume)
            'rng_state': self._rng_state,
        }
        
        # Save metadata as JSON
        json_path = filepath
        with open(json_path, 'w') as f:
            # Convert RNG state for JSON (it has numpy arrays)
            state_json = state.copy()
            state_json['rng_state'] = 'saved_in_pickle'
            json.dump(state_json, f, indent=2)
        
        # Save arrays as numpy compressed
        npz_path = filepath.replace('.json', '_fields.npz')
        np.savez_compressed(
            npz_path,
            psi_r=self.psi_r,
            psi_i=self.psi_i,
            psi_r_dot=self.psi_r_dot,
            psi_i_dot=self.psi_i_dot,
            tau=self.tau,
            channel_field=self.channel_field,
            remnant_field=self.remnant_field,
        )
        
        # Save RNG state separately (pickle handles numpy state tuple)
        pkl_path = filepath.replace('.json', '_rng.pkl')
        with open(pkl_path, 'wb') as f:
            pickle.dump(self._rng_state, f)
        
        print(f"  [Checkpoint saved: T={self.global_T:.1f}, phase={self.current_phase}]")
    
    def load_checkpoint(self, filepath: str):
        """
        Load simulation state from checkpoint.
        
        Restores RNG state for exact continuation.
        """
        # Load metadata
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore scalars
        self.global_T = state['global_T']
        self.phase_T = state['phase_T']
        self.step_count = state['step_count']
        self.current_phase = state['current_phase']
        self.phase_stability_count = state['phase_stability_count']
        self.transition_times = state['transition_times']
        self.phase_history = state['phase_history']
        self.dimension_history = state['dimension_history']
        self.transition_log = state['transition_log']
        self.total_creations = state['total_creations']
        self.total_annihilations = state['total_annihilations']
        
        # Load arrays
        npz_path = filepath.replace('.json', '_fields.npz')
        fields = np.load(npz_path)
        self.psi_r = fields['psi_r']
        self.psi_i = fields['psi_i']
        self.psi_r_dot = fields['psi_r_dot']
        self.psi_i_dot = fields['psi_i_dot']
        self.tau = fields['tau']
        self.channel_field = fields['channel_field']
        self.remnant_field = fields['remnant_field']
        
        # Load RNG state (critical!)
        pkl_path = filepath.replace('.json', '_rng.pkl')
        with open(pkl_path, 'rb') as f:
            self._rng_state = pickle.load(f)
        np.random.set_state(self._rng_state)
        
        print(f"  [Checkpoint loaded: T={self.global_T:.1f}, phase={self.current_phase}]")


def run_resume_validation(seed: int = 42) -> Dict[str, Any]:
    """
    Validate checkpoint resume correctness.
    
    Run A: Continuous to T=500
    Run B: T=250, save, reload, continue to T=500
    
    Compare metrics - should match within numerical precision.
    """
    print("=" * 70)
    print("  RESUME VALIDATION TEST")
    print("=" * 70)
    print()
    print("Run A: Continuous T=0 → T=500")
    print("Run B: T=0 → T=250 → save → reload → T=500")
    print("Pass: Metrics should match within numerical precision")
    print()
    
    checkpoint_dir = '/app/backend/qmrt_topology/papers/dimensional_emergence'
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Run A: Continuous
    print("--- Run A (continuous) ---")
    sim_a = DimensionalEmergenceSimulator(size=32, dt=0.10, seed=seed, initial_condition='line_seed')
    target_T = 500.0
    measure_interval = 50.0
    last_measure = 0.0
    
    while sim_a.global_T < target_T:
        sim_a.step()
        if sim_a.global_T - last_measure >= measure_interval:
            last_measure = sim_a.global_T
            metrics = sim_a.compute_dimensional_metrics()
            sim_a.update_phase_tracking(metrics)
            sim_a.record_checkpoint_metrics(metrics)
    
    metrics_a = sim_a.compute_dimensional_metrics()
    energy_a = sim_a.compute_total_energy()
    print(f"  Final T={sim_a.global_T:.1f}, D_eff={metrics_a['D_eff']:.4f}, "
          f"tau_mean={metrics_a['tau_mean']:.4f}, energy={energy_a:.2f}")
    
    # Run B: Split with checkpoint
    print("--- Run B (split with checkpoint) ---")
    sim_b = DimensionalEmergenceSimulator(size=32, dt=0.10, seed=seed, initial_condition='line_seed')
    checkpoint_file = f'{checkpoint_dir}/validation_checkpoint.json'
    
    # Phase 1: Run to T=250
    mid_T = 250.0
    last_measure = 0.0
    while sim_b.global_T < mid_T:
        sim_b.step()
        if sim_b.global_T - last_measure >= measure_interval:
            last_measure = sim_b.global_T
            metrics = sim_b.compute_dimensional_metrics()
            sim_b.update_phase_tracking(metrics)
            sim_b.record_checkpoint_metrics(metrics)
    
    print(f"  Mid-point T={sim_b.global_T:.1f}")
    sim_b.save_checkpoint(checkpoint_file)
    
    # Phase 2: Create new simulator and load checkpoint
    sim_b_resumed = DimensionalEmergenceSimulator(size=32, dt=0.10, seed=999, initial_condition='random')  # Different params
    sim_b_resumed.load_checkpoint(checkpoint_file)
    
    # Continue to T=500
    while sim_b_resumed.global_T < target_T:
        sim_b_resumed.step()
        if sim_b_resumed.global_T - last_measure >= measure_interval:
            last_measure = sim_b_resumed.global_T
            metrics = sim_b_resumed.compute_dimensional_metrics()
            sim_b_resumed.update_phase_tracking(metrics)
            sim_b_resumed.record_checkpoint_metrics(metrics)
    
    metrics_b = sim_b_resumed.compute_dimensional_metrics()
    energy_b = sim_b_resumed.compute_total_energy()
    print(f"  Final T={sim_b_resumed.global_T:.1f}, D_eff={metrics_b['D_eff']:.4f}, "
          f"tau_mean={metrics_b['tau_mean']:.4f}, energy={energy_b:.2f}")
    
    # Compare
    print()
    print("=" * 70)
    print("  COMPARISON")
    print("=" * 70)
    
    diffs = {
        'D_eff': abs(metrics_a['D_eff'] - metrics_b['D_eff']),
        'r2': abs(metrics_a['r2'] - metrics_b['r2']),
        'r3': abs(metrics_a['r3'] - metrics_b['r3']),
        'n_defects': abs(metrics_a['n_defects'] - metrics_b['n_defects']),
        'tau_mean': abs(metrics_a['tau_mean'] - metrics_b['tau_mean']),
        'tau_std': abs(metrics_a['tau_std'] - metrics_b['tau_std']),
        'energy': abs(energy_a - energy_b),
    }
    
    print()
    print(f"{'Metric':<15} {'Run A':>12} {'Run B':>12} {'Diff':>12} {'Status':>10}")
    print("-" * 65)
    
    all_pass = True
    tolerance = 1e-6
    for key, diff in diffs.items():
        val_a = metrics_a.get(key, energy_a if key == 'energy' else 0)
        val_b = metrics_b.get(key, energy_b if key == 'energy' else 0)
        if key == 'energy':
            val_a, val_b = energy_a, energy_b
        
        rel_diff = diff / (abs(val_a) + 1e-10)
        status = "PASS" if rel_diff < tolerance else "FAIL"
        if status == "FAIL":
            all_pass = False
        
        print(f"{key:<15} {val_a:>12.6f} {val_b:>12.6f} {diff:>12.2e} {status:>10}")
    
    print()
    if all_pass:
        print("VALIDATION PASSED: Resume produces identical results")
    else:
        print("VALIDATION FAILED: Resume diverges from continuous run")
    
    # Cleanup validation checkpoint
    for ext in ['.json', '_fields.npz', '_rng.pkl']:
        path = checkpoint_file.replace('.json', ext)
        if os.path.exists(path):
            os.remove(path)
    
    return {
        'passed': all_pass,
        'metrics_a': metrics_a,
        'metrics_b': metrics_b,
        'energy_a': energy_a,
        'energy_b': energy_b,
        'diffs': diffs,
    }


def run_dimensional_emergence(
    target_T: float = 10000.0,
    max_wall_seconds: float = 285.0,
    save_margin: float = 15.0,
    checkpoint_every_T: float = 50.0,
    seed: int = 42,
    resume: bool = False,
    initial_condition: str = 'line_seed',
) -> Dict[str, Any]:
    """
    Run dimensional emergence test with checkpointing.
    
    Parameters:
    -----------
    target_T : float
        Target simulation time (will checkpoint and exit early if wall time exceeded)
    max_wall_seconds : float
        Maximum wall-clock time before forced save (default: 285s for 300s limit)
    save_margin : float
        Seconds before max_wall_seconds to trigger save (default: 15s)
    checkpoint_every_T : float
        Checkpoint interval in simulation time units
    seed : int
        Random seed for reproducibility
    resume : bool
        If True, attempt to load existing checkpoint
    initial_condition : str
        Initial condition type: 'random', 'line_seed', 'plane_seed', 'point_seed'
    
    Returns:
    --------
    Dict with results, status, and paths
    """
    print("=" * 70)
    print("  DIMENSIONAL EMERGENCE LONG-HORIZON TEST")
    print("=" * 70)
    print()
    print(f"Target T: {target_T:.0f}")
    print(f"Wall time limit: {max_wall_seconds}s (save at {max_wall_seconds - save_margin}s)")
    print(f"Checkpoint interval: every {checkpoint_every_T} simulation time units")
    print(f"Seed: {seed}")
    print(f"Initial condition: {initial_condition}")
    print()
    
    checkpoint_dir = '/app/backend/qmrt_topology/papers/dimensional_emergence'
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_file = f'{checkpoint_dir}/emergence_seed{seed}.json'
    
    # Initialize or resume
    sim = DimensionalEmergenceSimulator(size=48, dt=0.10, seed=seed, initial_condition=initial_condition)
    
    if resume and os.path.exists(checkpoint_file):
        print("Resuming from checkpoint...")
        sim.load_checkpoint(checkpoint_file)
        print(f"  Resumed at T={sim.global_T:.1f}, step={sim.step_count}")
    else:
        print("Starting fresh simulation...")
    
    print()
    print("-" * 70)
    
    t_start = time.time()
    last_checkpoint_T = sim.global_T
    last_print_T = sim.global_T
    print_interval = checkpoint_every_T
    
    completed = False
    forced_save = False
    
    while sim.global_T < target_T:
        # Check wall time
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - save_margin:
            print(f"\nWall time limit approaching ({elapsed:.1f}s), saving checkpoint...")
            sim.save_checkpoint(checkpoint_file)
            forced_save = True
            break
        
        # Step simulation
        sim.step()
        
        # Periodic checkpoint
        if sim.global_T - last_checkpoint_T >= checkpoint_every_T:
            last_checkpoint_T = sim.global_T
            
            # Compute and record metrics
            metrics = sim.compute_dimensional_metrics()
            sim.update_phase_tracking(metrics)
            sim.record_checkpoint_metrics(metrics)
            
            # Save checkpoint
            sim.save_checkpoint(checkpoint_file)
        
        # Periodic print
        if sim.global_T - last_print_T >= print_interval:
            last_print_T = sim.global_T
            metrics = sim.compute_dimensional_metrics()
            print(f"T={sim.global_T:>7.1f} | D_eff={metrics['D_eff']:.3f} | "
                  f"r2={metrics['r2']:.3f} | r3={metrics['r3']:.3f} | "
                  f"phase={sim.current_phase:<15} | defects={metrics['n_defects']}")
        
        # Check for 3D stable
        if sim.transition_times['T_3D_stable'] is not None:
            print(f"\n3D STABLE STATE REACHED at T={sim.transition_times['T_3D_stable']:.1f}!")
            completed = True
            break
    
    # Final save if completed naturally
    if not forced_save:
        sim.save_checkpoint(checkpoint_file)
        if sim.global_T >= target_T:
            completed = True
            print(f"\nTarget T={target_T:.0f} reached!")
    
    # Compute final metrics
    final_metrics = sim.compute_dimensional_metrics()
    
    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print()
    print(f"Final simulation time: T = {sim.global_T:.1f}")
    print(f"Total steps: {sim.step_count}")
    print(f"Current phase: {sim.current_phase}")
    print(f"Final D_eff: {final_metrics['D_eff']:.3f}")
    print(f"Final r2/r3: {final_metrics['r2']:.3f} / {final_metrics['r3']:.3f}")
    print(f"Total creations: {sim.total_creations}")
    print()
    
    print("Transition times:")
    for key, value in sim.transition_times.items():
        if value is not None:
            print(f"  {key}: T = {value:.1f}")
        else:
            print(f"  {key}: not reached")
    print()
    
    if completed:
        if sim.transition_times['T_3D_stable']:
            print("RESULT: 3D emergence COMPLETE")
        else:
            print(f"RESULT: Target T={target_T:.0f} reached, current phase: {sim.current_phase}")
    else:
        print(f"RESULT: Checkpointed at T={sim.global_T:.1f} - run again with --resume to continue")
    
    # Save results summary
    result = {
        'seed': seed,
        'target_T': target_T,
        'final_T': sim.global_T,
        'final_step': sim.step_count,
        'current_phase': sim.current_phase,
        'completed': completed,
        'forced_save': forced_save,
        'final_metrics': final_metrics,
        'transition_times': sim.transition_times,
        'phase_history': sim.phase_history,
        'transition_log': sim.transition_log,
        'total_creations': sim.total_creations,
        'n_checkpoints': len(sim.dimension_history),
    }
    
    results_file = f'{checkpoint_dir}/RESULTS_seed{seed}.json'
    with open(results_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to: {results_file}")
    
    return result


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Dimensional Emergence Test')
    parser.add_argument('--mode', choices=['validate', 'run'], default='run',
                       help='Mode: validate (test resume correctness) or run (long-horizon test)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from existing checkpoint')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--target-T', type=float, default=10000.0,
                       help='Target simulation time')
    parser.add_argument('--max-wall-seconds', type=float, default=100.0,
                       help='Max wall-clock seconds (default: 100 for safety)')
    parser.add_argument('--save-margin', type=float, default=15.0,
                       help='Seconds before wall limit to save')
    parser.add_argument('--checkpoint-every-T', type=float, default=50.0,
                       help='Checkpoint interval in simulation time')
    parser.add_argument('--initial-condition', choices=['random', 'line_seed', 'plane_seed', 'point_seed'],
                       default='line_seed',
                       help='Initial condition type')
    
    args = parser.parse_args()
    
    if args.mode == 'validate':
        result = run_resume_validation(seed=args.seed)
        return result
    else:
        result = run_dimensional_emergence(
            target_T=args.target_T,
            max_wall_seconds=args.max_wall_seconds,
            save_margin=args.save_margin,
            checkpoint_every_T=args.checkpoint_every_T,
            seed=args.seed,
            resume=args.resume,
            initial_condition=args.initial_condition,
        )
        return result


if __name__ == "__main__":
    main()
