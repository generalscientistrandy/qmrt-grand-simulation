"""
Dimensional Overflow / Pressure-Gradient Structure Test
========================================================

PURPOSE: Test whether pressure gradients in a saturating medium create
directed topology flow, clustering, sink-like behavior, and gravity-like
attraction BEFORE or DURING dimensional unlocking.

KEY INSIGHT (The Tub Analogy):
  - Empty tub: No coherent motion
  - Partially filled: Local motion but no system-wide flow
  - Near saturation: Motion couples, pressure gradients form
  - Overflow: Dimensional activation, new degree of freedom unlocks

THREE REGIMES:
  1. UNDERFILLED: Too little coupling; weak or no organized motion
  2. SATURATION/OVERFLOW: Pressure gradients, defect accumulation,
     dimensional unlocking, possible GRAVITY-LIKE ATTRACTION
  3. EQUILIBRIUM: Stable geometry, isotropy, but reduced accretion

CORE QUESTION:
  When a lower-dimensional medium approaches overflow, do pressure
  gradients create directed topology flow, clustering, or sink-like
  behavior?

KEY VARIABLE:
  saturation_ratio = active_topology_density / dimensional_capacity

HYPOTHESIS:
  Gravity-like attraction is a residual pressure-gradient effect from
  dimensional oversaturation, NOT a feature of calm equilibrium spacetime.

Author: QMRT Research
Date: December 2025
"""

import numpy as np
from scipy.ndimage import label, center_of_mass
from scipy.linalg import eigh
from typing import Dict, List, Any, Tuple
import time
import json
import os


class DimensionalOverflowSimulator:
    """
    Simulator for testing pressure-gradient structure formation
    during dimensional saturation and overflow.
    
    Tracks the three regimes:
    1. Underfilled
    2. Saturation/Overflow (where gravity-like effects may emerge)
    3. Equilibrium
    """
    
    def __init__(self, 
                 size: int = 32, 
                 dt: float = 0.12, 
                 seed: int = 42,
                 unlock_threshold: float = 1.5,
                 unlock_rate: float = 0.01):
        """
        Initialize with dimensional activation dynamics.
        """
        
        self.size = size
        self.dt = dt
        self.seed = seed
        
        np.random.seed(seed)
        
        # Regulated Recovery v1.1 (LOCKED)
        self.tau_cap = 1.8
        self.damping_to_tau = 0.20
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Dimensional activation
        self.ax = 1.0  # X active
        self.ay = 0.0  # Y starts suppressed
        self.az = 0.0  # Z starts suppressed
        
        self.unlock_threshold = unlock_threshold
        self.unlock_rate = unlock_rate
        
        # Time tracking
        self.global_T = 0.0
        self.step_count = 0
        
        # Unlock events
        self.y_unlock_T = None
        self.z_unlock_T = None
        
        # Fields - start with concentrated structure along X axis
        shape = (size, size, size)
        self.psi_r = np.ones(shape)
        self.psi_i = np.zeros(shape)
        
        # Seed initial perturbations along X axis
        center = size // 2
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    d = np.sqrt((y - center)**2 + (z - center)**2)
                    if d < 3:
                        self.psi_r[x, y, z] += np.random.randn() * 0.1
                        self.psi_i[x, y, z] += np.random.randn() * 0.1
        
        self.psi_r_dot = np.zeros(shape)
        self.psi_i_dot = np.zeros(shape)
        self.tau = np.ones(shape)
        
        # Tracking
        self.total_creations = 0
        self.metrics_history = []
        self.cluster_tracking = []  # Track cluster positions over time
        
        # Regime tracking
        self.current_regime = "underfilled"
        
        print(f"Dimensional Overflow Test initialized")
        print(f"  Grid: {size}³, starting in 1D phase")
    
    def _weighted_laplacian(self, f):
        """Laplacian weighted by dimensional activation."""
        lap = self.ax * (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) - 2 * f)
        lap += self.ay * (np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 2 * f)
        lap += self.az * (np.roll(f, 1, axis=2) + np.roll(f, -1, axis=2) - 2 * f)
        return lap
    
    def compute_saturation_metrics(self) -> Dict[str, float]:
        """
        Compute the KEY VARIABLE: saturation_ratio
        
        saturation_ratio = active_topology_density / dimensional_capacity
        """
        # Topology field
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        
        # Weight gradients by dimensional activation
        effective_grad = np.sqrt(
            self.ax * grad_x**2 + 
            self.ay * grad_y**2 + 
            self.az * grad_z**2
        )
        
        # Active topology density
        topology_density = np.mean(effective_grad)
        topology_max = np.max(effective_grad)
        
        # Dimensional capacity = effective number of active dimensions
        dimensional_capacity = self.ax + self.ay + self.az
        
        # SATURATION RATIO - the key variable
        # Higher = more saturated, approaching overflow
        saturation_ratio = topology_density / (dimensional_capacity * 0.1 + 0.01)
        
        # Fill fraction (how "full" the active dimensions are)
        fill_fraction = topology_density / (topology_max + 0.01)
        
        return {
            'topology_density': float(topology_density),
            'topology_max': float(topology_max),
            'dimensional_capacity': float(dimensional_capacity),
            'saturation_ratio': float(saturation_ratio),
            'fill_fraction': float(fill_fraction),
        }
    
    def compute_pressure_gradient_field(self) -> Tuple[np.ndarray, Dict]:
        """
        Compute pressure gradient field.
        
        This is where gravity-like effects should emerge during saturation.
        """
        # Pressure components
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        potential = self.psi_r**2 + self.psi_i**2
        tau_pressure = (self.tau - 1.0) * 10
        
        # Total local pressure
        local_pressure = kinetic + potential + tau_pressure
        
        # Pressure gradient (3D gradient magnitude)
        grad_p_x = np.gradient(local_pressure, axis=0)
        grad_p_y = np.gradient(local_pressure, axis=1)
        grad_p_z = np.gradient(local_pressure, axis=2)
        
        # Weight by dimensional activation
        grad_p_mag = np.sqrt(
            self.ax * grad_p_x**2 +
            self.ay * grad_p_y**2 +
            self.az * grad_p_z**2
        )
        
        # Metrics
        metrics = {
            'mean_pressure': float(np.mean(local_pressure)),
            'max_pressure': float(np.max(local_pressure)),
            'mean_gradient': float(np.mean(grad_p_mag)),
            'max_gradient': float(np.max(grad_p_mag)),
            'gradient_concentration': float(np.std(grad_p_mag) / (np.mean(grad_p_mag) + 0.01)),
        }
        
        return local_pressure, metrics
    
    def detect_sink_nodes(self, pressure_field: np.ndarray, threshold_percentile: float = 95) -> List[Dict]:
        """
        Detect potential sink nodes (localized oversaturation points).
        
        These are where "black-hole-like" behavior might emerge.
        """
        threshold = np.percentile(pressure_field, threshold_percentile)
        high_pressure_mask = pressure_field > threshold
        
        labeled, n_nodes = label(high_pressure_mask)
        
        sink_nodes = []
        for i in range(1, n_nodes + 1):
            mask = (labeled == i)
            size = np.sum(mask)
            
            if size < 4:
                continue
            
            com = center_of_mass(pressure_field, labeled, i)
            peak_pressure = np.max(pressure_field[mask])
            mean_pressure = np.mean(pressure_field[mask])
            
            # Compute local gradient convergence (are gradients pointing inward?)
            coords = np.array(np.where(mask)).T
            
            sink_nodes.append({
                'id': i,
                'size': int(size),
                'com': [float(c) for c in com],
                'peak_pressure': float(peak_pressure),
                'mean_pressure': float(mean_pressure),
            })
        
        return sink_nodes
    
    def detect_topology_clusters(self) -> List[Dict]:
        """Detect topology clusters for flow tracking."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        threshold = np.percentile(topology, 90)
        high_top_mask = topology > threshold
        
        labeled, n_clusters = label(high_top_mask)
        
        clusters = []
        for i in range(1, n_clusters + 1):
            mask = (labeled == i)
            size = np.sum(mask)
            if size < 8:
                continue
            
            com = center_of_mass(topology, labeled, i)
            mass = np.sum(topology[mask])
            
            clusters.append({
                'id': i,
                'size': int(size),
                'mass': float(mass),
                'com': [float(c) for c in com],
            })
        
        return clusters
    
    def compute_topology_flow(self, prev_clusters: List[Dict], curr_clusters: List[Dict]) -> Dict:
        """
        Compute topology flow between timesteps.
        
        This measures whether topology is flowing toward pressure nodes.
        """
        if not prev_clusters or not curr_clusters:
            return {'net_drift': 0, 'drift_direction': [0, 0, 0]}
        
        # Match clusters by proximity
        total_drift = np.zeros(3)
        n_matched = 0
        
        for prev in prev_clusters:
            prev_com = np.array(prev['com'])
            
            # Find closest current cluster
            min_dist = float('inf')
            best_match = None
            for curr in curr_clusters:
                curr_com = np.array(curr['com'])
                dist = np.linalg.norm(curr_com - prev_com)
                if dist < min_dist and dist < 10:  # Max matching distance
                    min_dist = dist
                    best_match = curr
            
            if best_match:
                drift = np.array(best_match['com']) - prev_com
                total_drift += drift
                n_matched += 1
        
        if n_matched > 0:
            avg_drift = total_drift / n_matched
            return {
                'net_drift': float(np.linalg.norm(avg_drift)),
                'drift_direction': [float(d) for d in avg_drift],
                'n_matched': n_matched,
            }
        
        return {'net_drift': 0, 'drift_direction': [0, 0, 0], 'n_matched': 0}
    
    def determine_regime(self, saturation: Dict, pressure: Dict) -> str:
        """
        Determine current regime based on saturation and pressure.
        """
        sat_ratio = saturation['saturation_ratio']
        grad_mag = pressure['mean_gradient']
        
        if sat_ratio < 0.3:
            return "underfilled"
        elif sat_ratio > 0.7 or grad_mag > 0.5:
            return "saturation/overflow"
        else:
            return "equilibrium"
    
    def step(self):
        """Advance simulation with dimensional dynamics."""
        self.step_count += 1
        self.global_T += self.dt
        
        # τ dynamics
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
            create_mask = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask):
                coords = np.array(np.where(high_tau_mask)).T[create_mask]
                for coord in coords[:3]:
                    self._inject_perturbation(*coord)
                    self.tau[tuple(coord)] = 1.0
                    self.total_creations += 1
        
        # Wave equation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r = self._weighted_laplacian(self.psi_r)
        lap_i = self._weighted_laplacian(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def check_unlock(self, total_pressure: float):
        """Check and apply dimensional unlocking."""
        if self.ay < 1.0 and total_pressure > self.unlock_threshold:
            self.ay = min(1.0, self.ay + self.unlock_rate)
            if self.y_unlock_T is None and self.ay > 0:
                self.y_unlock_T = self.global_T
                print(f"  *** Y UNLOCKING at T={self.global_T:.1f}")
        
        if self.ay > 0.5 and self.az < 1.0 and total_pressure > self.unlock_threshold * 1.5:
            self.az = min(1.0, self.az + self.unlock_rate)
            if self.z_unlock_T is None and self.az > 0:
                self.z_unlock_T = self.global_T
                print(f"  *** Z UNLOCKING at T={self.global_T:.1f}")
    
    def _inject_perturbation(self, cx, cy, cz):
        """Inject perturbation."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), 
            np.arange(self.size), indexing='ij'
        )
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        perturbation = np.exp(-r_sq / 8)
        phase = np.random.uniform(0, 2 * np.pi)
        
        self.psi_r += 0.1 * perturbation * np.cos(phase)
        self.psi_i += 0.1 * perturbation * np.sin(phase)
    
    def get_full_metrics(self, prev_clusters=None) -> Dict[str, Any]:
        """Get comprehensive metrics for analysis."""
        saturation = self.compute_saturation_metrics()
        pressure_field, pressure_metrics = self.compute_pressure_gradient_field()
        sink_nodes = self.detect_sink_nodes(pressure_field)
        clusters = self.detect_topology_clusters()
        
        flow = self.compute_topology_flow(prev_clusters, clusters) if prev_clusters else {}
        
        # Determine regime
        regime = self.determine_regime(saturation, pressure_metrics)
        
        return {
            'T': self.global_T,
            'ax': self.ax,
            'ay': self.ay,
            'az': self.az,
            'regime': regime,
            'saturation_ratio': saturation['saturation_ratio'],
            'fill_fraction': saturation['fill_fraction'],
            'dimensional_capacity': saturation['dimensional_capacity'],
            'mean_pressure': pressure_metrics['mean_pressure'],
            'max_pressure': pressure_metrics['max_pressure'],
            'mean_gradient': pressure_metrics['mean_gradient'],
            'max_gradient': pressure_metrics['max_gradient'],
            'n_sink_nodes': len(sink_nodes),
            'n_clusters': len(clusters),
            'total_cluster_mass': sum(c['mass'] for c in clusters),
            'net_drift': flow.get('net_drift', 0),
            'clusters': clusters,
            'sink_nodes': sink_nodes,
        }


def run_overflow_test(
    target_T: float = 1000.0,
    max_wall_seconds: float = 100.0,
    size: int = 32,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run dimensional overflow / pressure-gradient structure test."""
    
    print("=" * 70)
    print("  DIMENSIONAL OVERFLOW / PRESSURE-GRADIENT STRUCTURE TEST")
    print("=" * 70)
    print()
    print("HYPOTHESIS: Gravity-like attraction emerges from pressure gradients")
    print("            during dimensional saturation, NOT in equilibrium.")
    print()
    print("THREE REGIMES:")
    print("  1. Underfilled: Weak coupling, no organized motion")
    print("  2. Saturation/Overflow: Pressure gradients → attraction → unlocking")
    print("  3. Equilibrium: Stable geometry but reduced accretion")
    print()
    print("KEY VARIABLE: saturation_ratio = topology_density / dimensional_capacity")
    print()
    
    sim = DimensionalOverflowSimulator(
        size=size, dt=0.12, seed=seed,
        unlock_threshold=1.5, unlock_rate=0.015
    )
    
    print()
    print("-" * 95)
    print(f"{'T':>6} | {'Regime':>15} | {'Sat.Ratio':>9} | {'Gradient':>8} | {'Sinks':>5} | {'Clusters':>8} | {'Drift':>6} | Dims")
    print("-" * 95)
    
    t_start = time.time()
    measure_interval = 20.0
    last_measure = 0.0
    prev_clusters = None
    
    # Track regime transitions
    regime_transitions = []
    last_regime = "underfilled"
    
    # Track gravity-like behavior signatures
    gravity_signatures = []
    
    while sim.global_T < target_T:
        elapsed = time.time() - t_start
        if elapsed >= max_wall_seconds - 10:
            print(f"\nWall time limit at T={sim.global_T:.1f}")
            break
        
        sim.step()
        
        if sim.global_T - last_measure >= measure_interval:
            last_measure = sim.global_T
            
            metrics = sim.get_full_metrics(prev_clusters)
            sim.metrics_history.append(metrics)
            
            # Check for regime transition
            if metrics['regime'] != last_regime:
                regime_transitions.append({
                    'T': sim.global_T,
                    'from': last_regime,
                    'to': metrics['regime'],
                })
                print(f"  *** REGIME TRANSITION: {last_regime} → {metrics['regime']}")
                last_regime = metrics['regime']
            
            # Check for gravity-like signatures
            if metrics['n_sink_nodes'] > 0 and metrics['net_drift'] > 0.5:
                gravity_signatures.append({
                    'T': sim.global_T,
                    'sink_nodes': metrics['n_sink_nodes'],
                    'drift': metrics['net_drift'],
                    'regime': metrics['regime'],
                })
            
            # Check dimensional unlock
            total_pressure = metrics['mean_pressure'] + metrics['max_gradient']
            sim.check_unlock(total_pressure)
            
            # Print status
            dims = f"{sim.ax:.0f}{sim.ay:.0f}{sim.az:.0f}"
            print(f"{sim.global_T:>6.1f} | {metrics['regime']:>15} | {metrics['saturation_ratio']:>9.3f} | "
                  f"{metrics['mean_gradient']:>8.3f} | {metrics['n_sink_nodes']:>5} | {metrics['n_clusters']:>8} | "
                  f"{metrics['net_drift']:>6.2f} | {dims}")
            
            prev_clusters = metrics['clusters']
    
    # Analysis
    print()
    print("=" * 70)
    print("  ANALYSIS")
    print("=" * 70)
    
    print(f"\nRegime transitions:")
    for t in regime_transitions:
        print(f"  T={t['T']:.1f}: {t['from']} → {t['to']}")
    
    print(f"\nDimensional unlocks:")
    print(f"  Y unlock: T={sim.y_unlock_T:.1f}" if sim.y_unlock_T else "  Y: not unlocked")
    print(f"  Z unlock: T={sim.z_unlock_T:.1f}" if sim.z_unlock_T else "  Z: not unlocked")
    
    print(f"\nGravity-like signatures detected: {len(gravity_signatures)}")
    if gravity_signatures:
        print(f"  First at T={gravity_signatures[0]['T']:.1f}")
        print(f"  Regime distribution: {set(g['regime'] for g in gravity_signatures)}")
    
    # Check if gravity-like behavior correlates with saturation regime
    saturation_regime_metrics = [m for m in sim.metrics_history if m['regime'] == 'saturation/overflow']
    if saturation_regime_metrics:
        avg_drift_saturation = np.mean([m['net_drift'] for m in saturation_regime_metrics])
        avg_sinks_saturation = np.mean([m['n_sink_nodes'] for m in saturation_regime_metrics])
        print(f"\nSaturation regime behavior:")
        print(f"  Avg drift: {avg_drift_saturation:.3f}")
        print(f"  Avg sink nodes: {avg_sinks_saturation:.1f}")
    
    # Verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    
    has_saturation_regime = any(m['regime'] == 'saturation/overflow' for m in sim.metrics_history)
    has_sink_nodes = any(m['n_sink_nodes'] > 0 for m in sim.metrics_history)
    has_drift = any(m['net_drift'] > 0.5 for m in sim.metrics_history)
    has_unlocking = sim.y_unlock_T is not None
    
    print()
    print(f"  Saturation regime observed:     {'✓ YES' if has_saturation_regime else '✗ NO'}")
    print(f"  Sink nodes (oversaturation):    {'✓ YES' if has_sink_nodes else '✗ NO'}")
    print(f"  Topology drift detected:        {'✓ YES' if has_drift else '✗ NO'}")
    print(f"  Dimensional unlocking:          {'✓ YES' if has_unlocking else '✗ NO'}")
    
    if has_saturation_regime and has_sink_nodes and has_drift:
        verdict = "GRAVITY-LIKE BEHAVIOR IN SATURATION REGIME"
    elif has_saturation_regime and (has_sink_nodes or has_drift):
        verdict = "PARTIAL EVIDENCE FOR PRESSURE-GRADIENT ATTRACTION"
    else:
        verdict = "NO CLEAR GRAVITY-LIKE SIGNATURE"
    
    print(f"\n  {verdict}")
    
    result = {
        'seed': seed,
        'final_T': sim.global_T,
        'regime_transitions': regime_transitions,
        'y_unlock_T': sim.y_unlock_T,
        'z_unlock_T': sim.z_unlock_T,
        'gravity_signatures': gravity_signatures,
        'verdict': verdict,
        'metrics_history': sim.metrics_history,
    }
    
    # Save
    output_dir = '/app/backend/qmrt_topology/papers/dimensional_overflow'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/overflow_seed{seed}.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_dir}/overflow_seed{seed}.json")
    
    return result


def main():
    result = run_overflow_test(
        target_T=800.0,
        max_wall_seconds=100.0,
        size=32,
        seed=42,
    )
    return result


if __name__ == "__main__":
    main()
