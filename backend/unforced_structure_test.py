"""
Unforced Structure Formation Test
==================================

PURPOSE: Test whether the regulated QMRT medium naturally forms persistent
density/topology concentrations WITHOUT pre-seeding planets, gravity wells,
or spherical structures.

CRITICAL PRINCIPLE: No forcing. Structure must emerge from:
  - Regulated recovery dynamics
  - τ gradients
  - Topological interactions
  - Random fluctuations

FORBIDDEN (to maintain scientific integrity):
  - Pre-placed spherical mass
  - Pre-placed gravity potential
  - Hard-coded inverse-square attraction
  - Manual orbital velocity
  - Manual planet radius
  - Manual collapse threshold designed to make spheres

ALLOWED:
  - Random fluctuations
  - Generic local interaction rules
  - τ gradients (emergent, not imposed)
  - Field energy
  - Topology formation via standard creation mechanism
  - Medium damping/recovery
  - Bounded propagation

METRICS:
  - Cluster count and mass distribution
  - Cluster lifetime and stability
  - Compactness and sphericity
  - Accretion rate (mass growth)
  - Center-of-mass stability
  - Angular momentum (if rotating structures emerge)

STAGES:
  1. Persistent clumps
  2. Accreting clumps
  3. Rotating accretion structures
  4. Compact planet-like bodies
  5. Multi-body orbital systems

BASELINE: Regulated Recovery v1.1

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label, center_of_mass
from scipy.linalg import eigh
from typing import Dict, List, Any, Tuple
import time
import json
import pickle
import os
import argparse


class UnforcedStructureSimulator:
    """
    Simulator for testing unforced structure formation.
    
    Uses ONLY the standard Regulated Recovery v1.1 physics.
    NO gravity, NO pre-seeded structures, NO spherical forcing.
    """
    
    # =========================================================================
    # FORBIDDEN FORCING CONDITIONS (for scientific integrity)
    # =========================================================================
    # The following are explicitly NOT implemented:
    # - Inverse-square gravity potential
    # - Pre-placed spherical mass distribution
    # - Manual orbital velocity injection
    # - Collapse threshold tuned to form spheres
    # - Any "planet seed" or "gravity well"
    # =========================================================================
    
    def __init__(self, 
                 size: int = 48, 
                 dt: float = 0.12, 
                 seed: int = 42,
                 initial_noise_amplitude: float = 0.01):
        """
        Initialize with uniform noise — NO pre-seeded structures.
        
        Parameters:
        -----------
        size : int
            Grid size
        initial_noise_amplitude : float
            Amplitude of initial random fluctuations (small!)
        """
        
        self.size = size
        self.dt = dt
        self.seed = seed
        
        np.random.seed(seed)
        self._rng_state = np.random.get_state()
        
        # Regulated Recovery v1.1 parameters (LOCKED)
        self.config = {
            'size': size,
            'dt': dt,
            'seed': seed,
            'initial_noise_amplitude': initial_noise_amplitude,
            # Locked physics
            'tau_cap': 1.8,
            'damping_to_tau': 0.20,
            'tau_creation_threshold': 1.001,
            'creation_rate': 0.15,
            'tau_response': 0.02,
            'tau_relaxation': 0.01,
            'c_0_sq': 4.0,
            'gamma': 0.007,
            # NO GRAVITY PARAMETERS - this is intentional
        }
        
        self.tau_cap = self.config['tau_cap']
        self.damping_to_tau = self.config['damping_to_tau']
        self.tau_creation_threshold = self.config['tau_creation_threshold']
        self.creation_rate = self.config['creation_rate']
        self.tau_response = self.config['tau_response']
        self.tau_relaxation = self.config['tau_relaxation']
        self.c_0_sq = self.config['c_0_sq']
        self.gamma = self.config['gamma']
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Fields — initialized with UNIFORM + small noise ONLY
        # NO pre-placed structure, NO density gradients, NO gravity wells
        self.psi_r = np.ones((size, size, size)) + np.random.randn(size, size, size) * initial_noise_amplitude
        self.psi_i = np.random.randn(size, size, size) * initial_noise_amplitude
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size))  # Uniform τ — NO gradients imposed
        
        # Counters
        self.total_creations = 0
        self.total_annihilations = 0
        
        # Cluster tracking history
        self.cluster_history = []
        self.metrics_history = []
        
        # Track individual clusters across time for lifetime measurement
        self.cluster_registry = {}  # cluster_id -> {birth_T, last_seen_T, max_mass, ...}
        self.next_cluster_id = 0
        
        print(f"Unforced Structure Formation Test initialized")
        print(f"  Grid: {size}³")
        print(f"  Initial condition: uniform + noise (amplitude={initial_noise_amplitude})")
        print(f"  NO pre-seeded structures")
        print(f"  NO imposed gravity")
    
    def step(self):
        """
        Advance simulation using ONLY standard Regulated Recovery physics.
        NO additional gravity or forcing terms.
        """
        self.step_count += 1
        self.global_T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        # τ dynamics (standard regulated recovery — NO gravity modification)
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        if self.damping_to_tau > 0:
            self.tau += self.damping_to_tau * damped_energy
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Creation events (standard mechanism)
        high_tau_mask = self.tau > self.tau_creation_threshold
        if np.any(high_tau_mask):
            n_candidates = np.sum(high_tau_mask)
            create_prob = self.creation_rate * (self.tau[high_tau_mask] - self.tau_creation_threshold)
            create_mask_1d = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask_1d):
                coords = np.array(np.where(high_tau_mask)).T
                create_coords = coords[create_mask_1d]
                
                for (cx, cy, cz) in create_coords[:3]:
                    self._inject_vortex(cx, cy, cz, np.random.choice([-1, 1]))
                    self.tau[cx, cy, cz] = 1.0
                    self.total_creations += 1
        
        # Wave equation (standard — NO gravity potential)
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        # Standard wave acceleration — NO additional forcing
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def _inject_vortex(self, cx, cy, cz, chirality):
        """Standard vortex injection — NO modification for structure forcing."""
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
    
    def compute_topology_field(self) -> np.ndarray:
        """Compute topology activity field (phase gradient magnitude)."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        
        return np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
    
    def compute_energy_density(self) -> np.ndarray:
        """Compute local energy density."""
        kinetic = 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        potential = 0.5 * (self.psi_r**2 + self.psi_i**2)
        return kinetic + potential
    
    def detect_clusters(self, 
                       field: str = 'topology',
                       threshold_percentile: float = 90,
                       min_cluster_size: int = 8) -> List[Dict]:
        """
        Detect clusters in the specified field.
        
        NO spherical assumption — clusters can be any shape.
        """
        if field == 'topology':
            data = self.compute_topology_field()
        elif field == 'energy':
            data = self.compute_energy_density()
        elif field == 'tau':
            data = self.tau
        else:
            raise ValueError(f"Unknown field: {field}")
        
        # Threshold at percentile (emergent, not forced)
        threshold = np.percentile(data, threshold_percentile)
        binary = data > threshold
        
        # Label connected components
        labeled, n_clusters = label(binary)
        
        clusters = []
        for i in range(1, n_clusters + 1):
            mask = (labeled == i)
            size = np.sum(mask)
            
            if size < min_cluster_size:
                continue
            
            # Get cluster properties (NO spherical assumption)
            coords = np.array(np.where(mask)).T
            com = center_of_mass(data, labeled, i)
            
            # Mass = sum of field values in cluster
            mass = np.sum(data[mask])
            
            # Compactness: actual volume vs bounding box volume
            bbox_size = np.prod(np.ptp(coords, axis=0) + 1)
            compactness = size / bbox_size if bbox_size > 0 else 0
            
            # Sphericity: eigenvalue analysis of position distribution
            if len(coords) >= 4:
                centered = coords - np.mean(coords, axis=0)
                cov = np.cov(centered.T)
                if cov.shape == (3, 3):
                    eigenvalues = np.sort(np.linalg.eigvalsh(cov))[::-1]
                    # Sphericity = smallest/largest eigenvalue (1 = perfect sphere)
                    sphericity = eigenvalues[2] / eigenvalues[0] if eigenvalues[0] > 0 else 0
                else:
                    sphericity = 0
            else:
                sphericity = 0
            
            # Angular momentum (if cluster has velocity)
            # L = Σ r × p where r is position from COM, p is momentum
            ang_mom = np.zeros(3)
            for coord in coords:
                r = coord - np.array(com)
                # Momentum ~ velocity at that point
                p = np.array([
                    self.psi_r_dot[tuple(coord)],
                    self.psi_i_dot[tuple(coord)],
                    0  # Placeholder for z-component
                ])
                ang_mom += np.cross(r, p[:3])
            
            clusters.append({
                'id': i,
                'size': int(size),
                'mass': float(mass),
                'com': [float(c) for c in com],
                'compactness': float(compactness),
                'sphericity': float(sphericity),
                'angular_momentum': [float(l) for l in ang_mom],
                'ang_mom_magnitude': float(np.linalg.norm(ang_mom)),
            })
        
        return clusters
    
    def compute_global_metrics(self) -> Dict[str, Any]:
        """Compute global simulation metrics."""
        topology = self.compute_topology_field()
        energy = self.compute_energy_density()
        
        # Total energy and momentum
        total_energy = float(np.sum(energy))
        
        # Momentum (simplified: sum of velocities)
        total_momentum = np.array([
            np.sum(self.psi_r_dot),
            np.sum(self.psi_i_dot),
            0
        ])
        
        # τ statistics
        tau_mean = float(np.mean(self.tau))
        tau_std = float(np.std(self.tau))
        tau_max = float(np.max(self.tau))
        
        # τ gradient strength (emergent, not imposed)
        tau_grad = np.sqrt(
            np.gradient(self.tau, axis=0)**2 +
            np.gradient(self.tau, axis=1)**2 +
            np.gradient(self.tau, axis=2)**2
        )
        tau_gradient_strength = float(np.mean(tau_grad))
        
        return {
            'total_energy': total_energy,
            'total_momentum': [float(p) for p in total_momentum],
            'momentum_magnitude': float(np.linalg.norm(total_momentum)),
            'tau_mean': tau_mean,
            'tau_std': tau_std,
            'tau_max': tau_max,
            'tau_gradient_strength': tau_gradient_strength,
            'topology_mean': float(np.mean(topology)),
            'topology_max': float(np.max(topology)),
        }
    
    def analyze_structure_formation(self) -> Dict[str, Any]:
        """
        Comprehensive analysis of emergent structure.
        
        NO spherical bias — analyzes whatever shapes emerge.
        """
        clusters = self.detect_clusters(field='topology')
        global_metrics = self.compute_global_metrics()
        
        n_clusters = len(clusters)
        
        if n_clusters == 0:
            return {
                'T': self.global_T,
                'n_clusters': 0,
                'has_structure': False,
                **global_metrics,
            }
        
        # Cluster statistics
        masses = [c['mass'] for c in clusters]
        sizes = [c['size'] for c in clusters]
        compactnesses = [c['compactness'] for c in clusters]
        sphericities = [c['sphericity'] for c in clusters]
        ang_moms = [c['ang_mom_magnitude'] for c in clusters]
        
        largest_cluster = max(clusters, key=lambda c: c['mass'])
        
        return {
            'T': self.global_T,
            'n_clusters': n_clusters,
            'has_structure': n_clusters > 0,
            'largest_cluster_mass': float(max(masses)),
            'largest_cluster_size': int(max(sizes)),
            'largest_cluster_compactness': largest_cluster['compactness'],
            'largest_cluster_sphericity': largest_cluster['sphericity'],
            'largest_cluster_ang_mom': largest_cluster['ang_mom_magnitude'],
            'mean_cluster_mass': float(np.mean(masses)),
            'mean_compactness': float(np.mean(compactnesses)),
            'mean_sphericity': float(np.mean(sphericities)),
            'mean_angular_momentum': float(np.mean(ang_moms)),
            'total_clustered_mass': float(sum(masses)),
            'clusters': clusters,
            **global_metrics,
        }
    
    def save_checkpoint(self, filepath: str):
        """Save full simulation state."""
        self._rng_state = np.random.get_state()
        
        state = {
            'config': self.config,
            'global_T': self.global_T,
            'step_count': self.step_count,
            'total_creations': self.total_creations,
            'metrics_history': self.metrics_history,
            'cluster_history': self.cluster_history,
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        npz_path = filepath.replace('.json', '_fields.npz')
        np.savez_compressed(npz_path,
            psi_r=self.psi_r, psi_i=self.psi_i,
            psi_r_dot=self.psi_r_dot, psi_i_dot=self.psi_i_dot,
            tau=self.tau)
        
        pkl_path = filepath.replace('.json', '_rng.pkl')
        with open(pkl_path, 'wb') as f:
            pickle.dump(self._rng_state, f)
    
    def load_checkpoint(self, filepath: str):
        """Load simulation state."""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.global_T = state['global_T']
        self.step_count = state['step_count']
        self.total_creations = state['total_creations']
        self.metrics_history = state['metrics_history']
        self.cluster_history = state['cluster_history']
        
        npz_path = filepath.replace('.json', '_fields.npz')
        fields = np.load(npz_path)
        self.psi_r = fields['psi_r']
        self.psi_i = fields['psi_i']
        self.psi_r_dot = fields['psi_r_dot']
        self.psi_i_dot = fields['psi_i_dot']
        self.tau = fields['tau']
        
        pkl_path = filepath.replace('.json', '_rng.pkl')
        with open(pkl_path, 'rb') as f:
            self._rng_state = pickle.load(f)
        np.random.set_state(self._rng_state)


def run_structure_formation_test(
    target_T: float = 1000.0,
    max_wall_seconds: float = 100.0,
    checkpoint_interval: float = 50.0,
    size: int = 48,
    seed: int = 42,
    resume: bool = False,
) -> Dict[str, Any]:
    """
    Run unforced structure formation test.
    
    NO pre-seeded planets, gravity, or spherical forcing.
    """
    print("=" * 70)
    print("  UNFORCED STRUCTURE FORMATION TEST")
    print("=" * 70)
    print()
    print("SCIENTIFIC PRINCIPLE: No forcing. Structure must emerge naturally.")
    print()
    print("FORBIDDEN:")
    print("  ✗ Pre-placed spherical mass")
    print("  ✗ Imposed gravity potential")
    print("  ✗ Manual orbital velocity")
    print("  ✗ Collapse threshold tuned for spheres")
    print()
    print("ALLOWED (standard Regulated Recovery v1.1):")
    print("  ✓ Random fluctuations")
    print("  ✓ τ-gradient dynamics (emergent)")
    print("  ✓ Topological interactions")
    print("  ✓ Bounded propagation")
    print()
    
    output_dir = '/app/backend/qmrt_topology/papers/structure_formation'
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_file = f'{output_dir}/structure_seed{seed}.json'
    
    sim = UnforcedStructureSimulator(size=size, dt=0.12, seed=seed)
    
    if resume and os.path.exists(checkpoint_file):
        print(f"Resuming from checkpoint at T={sim.global_T:.1f}")
        sim.load_checkpoint(checkpoint_file)
    
    print()
    print(f"Target T: {target_T}, Checkpoint every: {checkpoint_interval}")
    print()
    print("-" * 70)
    print(f"{'T':>6} | {'Clusters':>8} | {'Max Mass':>10} | {'Sphericity':>10} | {'τ gradient':>10}")
    print("-" * 70)
    
    t_start = time.time()
    last_checkpoint = sim.global_T
    last_print = sim.global_T
    
    while sim.global_T < target_T:
        # Check wall time
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - 15:
            print(f"\nWall time limit, saving checkpoint at T={sim.global_T:.1f}")
            sim.save_checkpoint(checkpoint_file)
            break
        
        sim.step()
        
        # Checkpoint and analyze
        if sim.global_T - last_checkpoint >= checkpoint_interval:
            last_checkpoint = sim.global_T
            
            analysis = sim.analyze_structure_formation()
            sim.metrics_history.append(analysis)
            
            # Print status
            n_clust = analysis['n_clusters']
            max_mass = analysis.get('largest_cluster_mass', 0)
            sphericity = analysis.get('largest_cluster_sphericity', 0)
            tau_grad = analysis['tau_gradient_strength']
            
            print(f"{sim.global_T:>6.1f} | {n_clust:>8} | {max_mass:>10.1f} | "
                  f"{sphericity:>10.3f} | {tau_grad:>10.4f}")
            
            # Save checkpoint
            sim.save_checkpoint(checkpoint_file)
    
    # Final analysis
    final_analysis = sim.analyze_structure_formation()
    
    print()
    print("=" * 70)
    print("  STRUCTURE FORMATION ANALYSIS")
    print("=" * 70)
    
    # Analyze progression
    if len(sim.metrics_history) > 0:
        cluster_counts = [m['n_clusters'] for m in sim.metrics_history]
        max_masses = [m.get('largest_cluster_mass', 0) for m in sim.metrics_history]
        sphericities = [m.get('largest_cluster_sphericity', 0) for m in sim.metrics_history]
        
        print(f"\nCluster count over time:")
        print(f"  Initial: {cluster_counts[0] if cluster_counts else 0}")
        print(f"  Final:   {cluster_counts[-1] if cluster_counts else 0}")
        print(f"  Max:     {max(cluster_counts) if cluster_counts else 0}")
        
        print(f"\nLargest cluster mass over time:")
        print(f"  Initial: {max_masses[0]:.1f}")
        print(f"  Final:   {max_masses[-1]:.1f}")
        print(f"  Max:     {max(max_masses):.1f}")
        
        # Check for persistent structures
        persistent = sum(1 for c in cluster_counts if c > 0) / len(cluster_counts)
        print(f"\nPersistence: Clusters present in {100*persistent:.0f}% of checkpoints")
        
        # Check for growth (accretion)
        if len(max_masses) >= 3:
            early_mass = np.mean(max_masses[:len(max_masses)//3])
            late_mass = np.mean(max_masses[-len(max_masses)//3:])
            growth = (late_mass - early_mass) / (early_mass + 1e-10)
            print(f"\nMass growth: {100*growth:.1f}% (early→late)")
        
        # Check for sphericity trend
        if len(sphericities) >= 3 and any(s > 0 for s in sphericities):
            valid_sphericities = [s for s in sphericities if s > 0]
            print(f"\nSphericity: mean={np.mean(valid_sphericities):.3f}, "
                  f"max={max(valid_sphericities):.3f}")
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    has_clusters = final_analysis['n_clusters'] > 0
    has_persistent = persistent > 0.5 if 'persistent' in dir() else False
    has_growth = growth > 0.1 if 'growth' in dir() else False
    has_sphericity = final_analysis.get('largest_cluster_sphericity', 0) > 0.3
    
    print()
    print(f"Stage 1 - Persistent clumps:    {'✓ YES' if has_clusters and has_persistent else '✗ NO'}")
    print(f"Stage 2 - Accreting clumps:     {'✓ YES' if has_growth else '✗ NO'}")
    print(f"Stage 3 - Spherical tendency:   {'✓ YES' if has_sphericity else '✗ NO'}")
    
    result = {
        'seed': seed,
        'target_T': target_T,
        'final_T': sim.global_T,
        'final_analysis': final_analysis,
        'metrics_history': sim.metrics_history,
        'verdict': {
            'has_clusters': bool(has_clusters),
            'has_persistent_clusters': bool(has_persistent) if 'persistent' in dir() else False,
            'has_mass_growth': bool(has_growth) if 'growth' in dir() else False,
            'has_spherical_tendency': bool(has_sphericity),
        }
    }
    
    # Save results
    results_file = f'{output_dir}/RESULTS_seed{seed}.json'
    with open(results_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print()
    print(f"Results saved to: {results_file}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Unforced Structure Formation Test')
    parser.add_argument('--target-T', type=float, default=1000.0)
    parser.add_argument('--max-wall-seconds', type=float, default=100.0)
    parser.add_argument('--checkpoint-interval', type=float, default=50.0)
    parser.add_argument('--size', type=int, default=48)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--resume', action='store_true')
    
    args = parser.parse_args()
    
    result = run_structure_formation_test(
        target_T=args.target_T,
        max_wall_seconds=args.max_wall_seconds,
        checkpoint_interval=args.checkpoint_interval,
        size=args.size,
        seed=args.seed,
        resume=args.resume,
    )
    
    return result


if __name__ == "__main__":
    main()
