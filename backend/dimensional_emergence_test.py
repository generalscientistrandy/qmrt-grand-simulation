"""
Dimensional Emergence Scale Test
================================

PURPOSE: Track the emergence of degrees of freedom from a branching medium,
measuring how the system progresses from 1D → 2D → 3D effective dimensionality.

CONCEPT:
  - Degrees of freedom, not literal spatial dimensions
  - 1D: Motion primarily forward/back (one dominant direction)
  - 2D: Motion in a plane (two dominant directions)
  - 3D: Isotropic motion (all directions equally available)

METRICS:
  - Directional participation ratio
  - Principal component analysis of defect/energy distribution
  - Anisotropy tensor eigenvalues
  - Graph dimension of defect network
  - Correlation lengths along each axis

CHECKPOINTING:
  - Save state every N steps or when dimensional transition detected
  - Can resume from checkpoint
  - Tracks time to reach each dimensional state

TIMELINE TRACKING:
  - T_1D_stable: when 1D state is reached
  - T_1D_to_2D: transition time from 1D to 2D
  - T_2D_stable: when 2D state is reached
  - T_2D_to_3D: transition time from 2D to 3D
  - T_3D_stable: when full 3D isotropy is reached

BASELINE: Regulated Recovery v1.1
"""

import numpy as np
from scipy.ndimage import label
from scipy.linalg import eigh
from collections import deque
from typing import Dict, List, Tuple, Optional
import time
import json
import os


class DimensionalEmergenceSimulator:
    """Simulator for tracking dimensional emergence over time."""
    
    def __init__(self, size: int = 48, dt: float = 0.10, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.T = 0.0
        self.step_count = 0
        self.seed = seed
        
        # Regulated Recovery v1.1 configuration
        self.damping_to_tau = 0.20
        self.tau_cap = 1.8
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        
        # Wave field - start with small random perturbations
        self.psi_r = np.ones((size, size, size)) * 1.0 + np.random.randn(size, size, size) * 0.01
        self.psi_i = np.random.randn(size, size, size) * 0.01
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Medium field
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Tracking
        self.total_creations = 0
        self.dimension_history = []
        self.transition_times = {
            'T_1D_first': None,
            'T_2D_first': None, 
            'T_3D_first': None,
            'T_1D_stable': None,
            'T_2D_stable': None,
            'T_3D_stable': None,
        }
        self.current_dimension = 0
        self.dimension_stable_count = 0
        self.stability_threshold = 20  # Steps to consider stable
    
    def _inject_vortex(self, cx, cy, cz, chirality=1):
        """Inject a vortex at specified location."""
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
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
        self.T += self.dt
        
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
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def detect_defects(self, threshold: float = 0.5) -> List[Tuple]:
        """Detect defect locations based on amplitude dips."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 3:
                coords = np.where(component)
                defects.append((
                    float(np.mean(coords[0])),
                    float(np.mean(coords[1])),
                    float(np.mean(coords[2]))
                ))
        return defects
    
    def compute_dimensional_metrics(self) -> Dict:
        """
        Compute metrics that indicate effective dimensionality.
        
        Returns dimension estimate and supporting metrics.
        """
        # Method 1: Energy distribution anisotropy tensor
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        center = self.size / 2
        
        # Center coordinates
        dx = x - center
        dy = y - center
        dz = z - center
        
        # Energy-weighted inertia tensor
        total_energy = np.sum(energy)
        if total_energy < 1e-10:
            return {'dimension': 0, 'valid': False}
        
        # Inertia tensor components
        Ixx = np.sum(energy * (dy**2 + dz**2)) / total_energy
        Iyy = np.sum(energy * (dx**2 + dz**2)) / total_energy
        Izz = np.sum(energy * (dx**2 + dy**2)) / total_energy
        Ixy = -np.sum(energy * dx * dy) / total_energy
        Ixz = -np.sum(energy * dx * dz) / total_energy
        Iyz = -np.sum(energy * dy * dz) / total_energy
        
        inertia_tensor = np.array([
            [Ixx, Ixy, Ixz],
            [Ixy, Iyy, Iyz],
            [Ixz, Iyz, Izz]
        ])
        
        # Eigenvalues give principal moments
        eigenvalues, _ = eigh(inertia_tensor)
        eigenvalues = np.sort(eigenvalues)[::-1]  # Descending
        
        # Participation ratio: how many dimensions are "active"
        # PR = (sum λ)² / sum(λ²)
        if np.sum(eigenvalues**2) > 0:
            participation_ratio = np.sum(eigenvalues)**2 / np.sum(eigenvalues**2)
        else:
            participation_ratio = 1.0
        
        # Eigenvalue ratios
        if eigenvalues[0] > 1e-10:
            ratio_12 = eigenvalues[1] / eigenvalues[0]
            ratio_13 = eigenvalues[2] / eigenvalues[0]
        else:
            ratio_12, ratio_13 = 0, 0
        
        # Method 2: Defect network dimension
        defects = self.detect_defects()
        n_defects = len(defects)
        
        graph_dimension = 0.0
        if n_defects >= 10:
            # Build adjacency and measure graph dimension
            graph_dimension = self._compute_graph_dimension(defects)
        
        # Method 3: Momentum direction distribution
        momentum_x = np.sum(np.abs(self.psi_r_dot * np.sign(np.roll(self.psi_r, 1, 0) - self.psi_r)))
        momentum_y = np.sum(np.abs(self.psi_r_dot * np.sign(np.roll(self.psi_r, 1, 1) - self.psi_r)))
        momentum_z = np.sum(np.abs(self.psi_r_dot * np.sign(np.roll(self.psi_r, 1, 2) - self.psi_r)))
        
        total_momentum = momentum_x + momentum_y + momentum_z + 1e-10
        mom_fractions = np.array([momentum_x, momentum_y, momentum_z]) / total_momentum
        mom_entropy = -np.sum(mom_fractions * np.log(mom_fractions + 1e-10)) / np.log(3)  # Normalized 0-1
        
        # Effective dimension estimation
        # 1D: PR ≈ 1, one eigenvalue dominates
        # 2D: PR ≈ 2, two eigenvalues similar
        # 3D: PR ≈ 3, all eigenvalues similar
        
        if participation_ratio < 1.5:
            effective_dimension = 1
        elif participation_ratio < 2.5:
            effective_dimension = 2
        else:
            effective_dimension = 3
        
        # Refine with eigenvalue ratios
        if ratio_12 < 0.3:  # Second much smaller than first
            effective_dimension = min(effective_dimension, 1)
        elif ratio_13 < 0.3 and ratio_12 > 0.5:  # Third much smaller, first two similar
            effective_dimension = min(effective_dimension, 2)
        
        return {
            'valid': True,
            'effective_dimension': effective_dimension,
            'participation_ratio': float(participation_ratio),
            'eigenvalues': eigenvalues.tolist(),
            'ratio_12': float(ratio_12),
            'ratio_13': float(ratio_13),
            'n_defects': n_defects,
            'graph_dimension': float(graph_dimension),
            'momentum_entropy': float(mom_entropy),
            'momentum_fractions': mom_fractions.tolist(),
        }
    
    def _compute_graph_dimension(self, defects: List[Tuple], r_link: float = 8.0) -> float:
        """Compute graph dimension from defect network."""
        n = len(defects)
        if n < 10:
            return 0.0
        
        # Sample if too many
        max_n = min(n, 100)
        if n > max_n:
            indices = np.random.choice(n, max_n, replace=False)
            sample = [defects[i] for i in indices]
        else:
            sample = defects
            max_n = n
        
        # Build adjacency
        adj = {i: set() for i in range(max_n)}
        for i in range(max_n):
            for j in range(i + 1, max_n):
                d = self._periodic_distance(sample[i], sample[j])
                if d < r_link:
                    adj[i].add(j)
                    adj[j].add(i)
        
        # BFS to get graph distances
        max_sources = min(max_n, 20)
        graph_dist = np.full((max_sources, max_n), np.inf)
        
        for idx in range(max_sources):
            graph_dist[idx, idx] = 0
            queue = deque([idx])
            visited = {idx}
            while queue:
                node = queue.popleft()
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        graph_dist[idx, neighbor] = graph_dist[idx, node] + 1
                        queue.append(neighbor)
        
        # Dimension from N(r) scaling
        radii = [1, 2, 3, 4]
        counts = []
        for r in radii:
            count = np.mean([np.sum((graph_dist[idx, :] <= r) & (graph_dist[idx, :] > 0)) 
                           for idx in range(max_sources)])
            counts.append(count)
        
        if min(counts) > 0 and len(counts) >= 2:
            log_r = np.log(radii)
            log_n = np.log(np.array(counts) + 1)
            dimension = np.polyfit(log_r, log_n, 1)[0]
            return max(0, min(3, dimension))
        
        return 0.0
    
    def _periodic_distance(self, p1, p2) -> float:
        """Euclidean distance with periodic boundaries."""
        d = np.abs(np.array(p1) - np.array(p2))
        d = np.minimum(d, self.size - d)
        return np.sqrt(np.sum(d**2))
    
    def update_dimension_tracking(self, metrics: Dict):
        """Track dimensional state and transitions."""
        if not metrics['valid']:
            return
        
        dim = metrics['effective_dimension']
        self.dimension_history.append({
            'T': self.T,
            'step': self.step_count,
            'dimension': dim,
            'participation_ratio': metrics['participation_ratio'],
            'n_defects': metrics['n_defects'],
        })
        
        # Track first occurrences
        if dim >= 1 and self.transition_times['T_1D_first'] is None:
            self.transition_times['T_1D_first'] = self.T
        if dim >= 2 and self.transition_times['T_2D_first'] is None:
            self.transition_times['T_2D_first'] = self.T
        if dim >= 3 and self.transition_times['T_3D_first'] is None:
            self.transition_times['T_3D_first'] = self.T
        
        # Track stability
        if dim == self.current_dimension:
            self.dimension_stable_count += 1
        else:
            self.current_dimension = dim
            self.dimension_stable_count = 1
        
        # Mark stable states
        if self.dimension_stable_count >= self.stability_threshold:
            if dim >= 1 and self.transition_times['T_1D_stable'] is None:
                self.transition_times['T_1D_stable'] = self.T
            if dim >= 2 and self.transition_times['T_2D_stable'] is None:
                self.transition_times['T_2D_stable'] = self.T
            if dim >= 3 and self.transition_times['T_3D_stable'] is None:
                self.transition_times['T_3D_stable'] = self.T
    
    def save_checkpoint(self, filepath: str):
        """Save simulation state to file."""
        state = {
            'T': self.T,
            'step_count': self.step_count,
            'seed': self.seed,
            'total_creations': self.total_creations,
            'dimension_history': self.dimension_history,
            'transition_times': self.transition_times,
            'current_dimension': self.current_dimension,
            'dimension_stable_count': self.dimension_stable_count,
            # Field states (compressed)
            'psi_r_mean': float(np.mean(self.psi_r)),
            'psi_r_std': float(np.std(self.psi_r)),
            'tau_mean': float(np.mean(self.tau)),
            'tau_max': float(np.max(self.tau)),
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Save full field state as numpy
        np.savez_compressed(
            filepath.replace('.json', '_fields.npz'),
            psi_r=self.psi_r,
            psi_i=self.psi_i,
            psi_r_dot=self.psi_r_dot,
            psi_i_dot=self.psi_i_dot,
            tau=self.tau
        )
    
    def load_checkpoint(self, filepath: str):
        """Load simulation state from file."""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.T = state['T']
        self.step_count = state['step_count']
        self.total_creations = state['total_creations']
        self.dimension_history = state['dimension_history']
        self.transition_times = state['transition_times']
        self.current_dimension = state['current_dimension']
        self.dimension_stable_count = state['dimension_stable_count']
        
        # Load fields
        fields = np.load(filepath.replace('.json', '_fields.npz'))
        self.psi_r = fields['psi_r']
        self.psi_i = fields['psi_i']
        self.psi_r_dot = fields['psi_r_dot']
        self.psi_i_dot = fields['psi_i_dot']
        self.tau = fields['tau']


def run_dimensional_emergence(max_wall_time: float = 110.0, 
                               checkpoint_interval: float = 30.0,
                               seed: int = 42) -> Dict:
    """
    Run dimensional emergence test with checkpointing.
    
    Stops 10 seconds before max_wall_time to save state.
    """
    
    checkpoint_dir = '/app/backend/qmrt_topology/papers/dimensional_emergence'
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Check for existing checkpoint
    checkpoint_file = f'{checkpoint_dir}/checkpoint_seed{seed}.json'
    
    sim = DimensionalEmergenceSimulator(size=48, dt=0.10, seed=seed)
    
    if os.path.exists(checkpoint_file):
        print(f"Loading checkpoint from {checkpoint_file}...")
        sim.load_checkpoint(checkpoint_file)
        print(f"  Resumed at T={sim.T:.1f}, step={sim.step_count}")
    
    print(f"\nStarting dimensional emergence tracking (seed={seed})...")
    print(f"Max wall time: {max_wall_time}s, checkpoint every {checkpoint_interval}s")
    print()
    
    t_start = time.time()
    last_checkpoint = t_start
    last_measure = sim.T
    measure_interval = 5.0  # Measure dimension every 5 time units
    
    while True:
        # Check wall time
        elapsed = time.time() - t_start
        if elapsed > max_wall_time - 10:
            print(f"\nApproaching wall time limit, saving checkpoint...")
            sim.save_checkpoint(checkpoint_file)
            break
        
        # Step simulation
        sim.step()
        
        # Periodic measurement
        if sim.T - last_measure >= measure_interval:
            last_measure = sim.T
            metrics = sim.compute_dimensional_metrics()
            sim.update_dimension_tracking(metrics)
            
            print(f"T={sim.T:.1f}: dim={metrics['effective_dimension']}, "
                  f"PR={metrics['participation_ratio']:.2f}, "
                  f"defects={metrics['n_defects']}, "
                  f"creations={sim.total_creations}")
        
        # Periodic checkpoint
        if time.time() - last_checkpoint > checkpoint_interval:
            sim.save_checkpoint(checkpoint_file)
            last_checkpoint = time.time()
            print(f"  [Checkpoint saved at T={sim.T:.1f}]")
        
        # Check if 3D stable reached
        if sim.transition_times['T_3D_stable'] is not None:
            print(f"\n3D STABLE STATE REACHED at T={sim.transition_times['T_3D_stable']:.1f}!")
            break
    
    # Final measurements
    final_metrics = sim.compute_dimensional_metrics()
    
    result = {
        'seed': seed,
        'final_T': sim.T,
        'final_step': sim.step_count,
        'total_creations': sim.total_creations,
        'final_dimension': final_metrics['effective_dimension'],
        'final_participation_ratio': final_metrics['participation_ratio'],
        'transition_times': sim.transition_times,
        'dimension_history': sim.dimension_history,
        'complete': sim.transition_times['T_3D_stable'] is not None,
    }
    
    return result


def main():
    print("=" * 80)
    print("  DIMENSIONAL EMERGENCE SCALE TEST")
    print("=" * 80)
    print()
    print("Tracking degrees of freedom emergence:")
    print("  1D: Motion primarily in one direction")
    print("  2D: Motion in a plane (two directions)")
    print("  3D: Isotropic motion (all directions)")
    print()
    print("Metrics: Participation ratio, eigenvalue ratios, graph dimension")
    print()
    
    # Run with checkpointing
    result = run_dimensional_emergence(
        max_wall_time=100.0,
        checkpoint_interval=25.0,
        seed=42
    )
    
    print()
    print("=" * 80)
    print("  RESULTS")
    print("=" * 80)
    print()
    
    print(f"Final simulation time: T = {result['final_T']:.1f}")
    print(f"Final dimension: {result['final_dimension']}")
    print(f"Final participation ratio: {result['final_participation_ratio']:.2f}")
    print(f"Total creations: {result['total_creations']}")
    print()
    
    print("Transition times:")
    for key, value in result['transition_times'].items():
        if value is not None:
            print(f"  {key}: T = {value:.1f}")
        else:
            print(f"  {key}: not reached")
    print()
    
    if result['complete']:
        print("★ 3D EMERGENCE COMPLETE")
    else:
        print("⋯ 3D emergence not yet complete - run again to continue")
    
    # Save results
    output_file = '/app/backend/qmrt_topology/papers/DIMENSIONAL_EMERGENCE_RESULTS.json'
    
    # Convert for JSON
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    with open(output_file, 'w') as f:
        json.dump(convert(result), f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return result


if __name__ == "__main__":
    main()
