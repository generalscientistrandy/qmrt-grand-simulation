"""
Defect Organization Test
========================

PURPOSE: Determine whether regulated recovery v1.1 causes defects to
self-organize into a statistically isotropic structure over long time.

HYPOTHESIS:
  If regulated recovery organizes defects, we should see:
  - Defect anisotropy decreasing over time
  - More uniform spatial distribution
  - Lower density entropy (more ordered)

KEY QUESTION:
  Does regulated recovery merely sustain defects, or does it drive them
  toward a statistically isotropic organized phase?

METRICS:
  - N_defects: Total defect count
  - defect_anisotropy: Spatial anisotropy from position covariance
  - density_entropy: Spatial uniformity measure
  - pair_distance_cv: Coefficient of variation of inter-defect distances
  - tau_localization: τ_max / τ_mean
  - anisotropy_slope: Change in anisotropy over time
  - creations: Total creation events (indicates activity level)

MODES:
  - Unregulated: damping_to_tau=0.0, tau_cap=3.0
  - Regulated v1.1: damping_to_tau=0.20, tau_cap=1.8

CHECKPOINTS: T = 500, 1000, 2000
SEEDS: 3 (for statistical robustness)

NOTE: Uses the validated UltraLongHorizonSimulator which includes
the creation mechanism that sustains defects.
"""

import numpy as np
from scipy.ndimage import label
from scipy.spatial.distance import pdist
from typing import Dict, List, Tuple
import time
import json


# Locked v1.1 Configuration
REGULATED_RECOVERY_TAU_CAP = 1.8
OPTIMAL_DAMPING_TO_TAU = 0.20


class ValidatedOrganizationSimulator:
    """
    Simulator for defect organization analysis.
    Based on the validated UltraLongHorizonSimulator with creation mechanism.
    """
    
    def __init__(self, size: int = 32, dt: float = 0.12,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.15,
                 damping_to_tau: float = OPTIMAL_DAMPING_TO_TAU,
                 tau_cap: float = REGULATED_RECOVERY_TAU_CAP,
                 seed: int = None):
        
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.damping_to_tau = damping_to_tau
        self.tau_cap = tau_cap
        
        self.T = 0.0
        self.step_count = 0
        
        # Initialize as in validated simulator
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        self.channel = np.zeros((size, size, size))
        
        # Coupling gradient (standard configuration)
        x, y, z = np.meshgrid(np.arange(size), np.arange(size), 
                             np.arange(size), indexing='ij')
        center = size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.coupling = np.where(r <= size * 0.25, 0.7, 0.2)
        
        self.creations = 0
        self.total_damped = 0.0
        self.total_recycled = 0.0
        self.explosion = False
        
        # Seed initial structure
        self.seed_structure(n_pairs=8)
    
    def inject_vortex(self, cx, cy, cz, chirality=1):
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / 18)
        
        vortex = np.tanh(r / 2.5) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_structure(self, n_pairs=8):
        center = self.size // 2
        for _ in range(n_pairs):
            a1 = np.random.uniform(0, 2*np.pi)
            r1 = np.random.uniform(2, self.size * 0.17)
            cx1 = center + r1 * np.cos(a1)
            cy1 = center + r1 * np.sin(a1)
            cz1 = center + np.random.uniform(-3, 3)
            
            a2 = a1 + np.pi + np.random.uniform(-0.5, 0.5)
            r2 = np.random.uniform(2, self.size * 0.17)
            cx2 = center + r2 * np.cos(a2)
            cy2 = center + r2 * np.sin(a2)
            cz2 = center + np.random.uniform(-3, 3)
            
            self.inject_vortex(cx1, cy1, cz1, chirality=1)
            self.inject_vortex(cx2, cy2, cz2, chirality=-1)
    
    def step(self):
        self.step_count += 1
        self.T += self.dt
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        kinetic = self.psi_r_dot**2 + self.psi_i_dot**2
        damped_energy = self.gamma * kinetic
        self.total_damped += float(np.sum(damped_energy))
        
        # Energy and tau dynamics
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * kinetic
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        
        # Damping → τ coupling (v1.1)
        if self.damping_to_tau > 0:
            recycled = self.damping_to_tau * damped_energy
            self.tau += recycled
            self.total_recycled += float(np.sum(recycled))
        
        self.tau = np.clip(self.tau, 0.5, self.tau_cap)
        
        # Creation from high τ regions
        high_tau_mask = self.tau > self.tau_creation_threshold
        if np.any(high_tau_mask):
            n_candidates = np.sum(high_tau_mask)
            create_prob = self.creation_rate * (self.tau[high_tau_mask] - self.tau_creation_threshold)
            create_mask_1d = np.random.random(n_candidates) < create_prob
            
            if np.any(create_mask_1d):
                # Find coordinates
                coords = np.array(np.where(high_tau_mask)).T
                create_coords = coords[create_mask_1d]
                
                for (cx, cy, cz) in create_coords[:5]:  # Limit creations per step
                    chirality = np.random.choice([-1, 1])
                    self.inject_vortex(cx, cy, cz, chirality)
                    self.creations += 1
                    self.tau[cx, cy, cz] = 1.0  # Reset τ after creation
        
        # Wave propagation
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
        
        # Check for explosion
        if np.max(np.abs(self.psi_r)) > 100 or np.max(np.abs(self.psi_i)) > 100:
            self.explosion = True
        
        return float(np.mean(energy))
    
    def detect_defects(self) -> Tuple[int, np.ndarray]:
        """Detect defects and return count and positions."""
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        dx = np.diff(phase, axis=0, append=phase[:1, :, :])
        dy = np.diff(phase, axis=1, append=phase[:, :1, :])
        dz = np.diff(phase, axis=2, append=phase[:, :, :1])
        
        dx = np.where(dx > np.pi, dx - 2*np.pi, dx)
        dx = np.where(dx < -np.pi, dx + 2*np.pi, dx)
        dy = np.where(dy > np.pi, dy - 2*np.pi, dy)
        dy = np.where(dy < -np.pi, dy + 2*np.pi, dy)
        dz = np.where(dz > np.pi, dz - 2*np.pi, dz)
        dz = np.where(dz < -np.pi, dz + 2*np.pi, dz)
        
        curl_mag = np.sqrt(
            (np.roll(dz, -1, 1) - dz)**2 +
            (np.roll(dx, -1, 2) - dx)**2 +
            (np.roll(dy, -1, 0) - dy)**2
        )
        
        threshold = 1.5
        defect_mask = curl_mag > threshold
        labeled, n_defects = label(defect_mask)
        
        positions = []
        for i in range(1, n_defects + 1):
            coords = np.array(np.where(labeled == i))
            centroid = coords.mean(axis=1)
            positions.append(centroid)
        
        positions = np.array(positions) if positions else np.empty((0, 3))
        
        return n_defects, positions
    
    def compute_organization_metrics(self) -> Dict:
        """Compute all organization metrics."""
        
        n_defects, positions = self.detect_defects()
        
        metrics = {
            'T': self.T,
            'N_defects': n_defects,
            'creations': self.creations,
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
            'tau_max': float(np.max(self.tau)),
            'tau_localization': float(np.max(self.tau) / np.mean(self.tau)),
            'explosion': self.explosion
        }
        
        if n_defects >= 3:
            # Defect anisotropy from position covariance
            centered = positions - positions.mean(axis=0)
            cov = np.cov(centered.T)
            eigs = np.linalg.eigvalsh(cov)
            eigs = np.sort(eigs)[::-1]
            
            metrics['defect_anisotropy'] = float((eigs[0] - eigs[-1]) / (np.mean(eigs) + 1e-9))
            metrics['eigenvalues'] = [float(e) for e in eigs]
            
            # Pair distance statistics
            distances = pdist(positions)
            if len(distances) > 0:
                metrics['pair_distance_mean'] = float(np.mean(distances))
                metrics['pair_distance_std'] = float(np.std(distances))
                metrics['pair_distance_cv'] = float(np.std(distances) / np.mean(distances)) if np.mean(distances) > 0 else 0
            else:
                metrics['pair_distance_mean'] = 0
                metrics['pair_distance_std'] = 0
                metrics['pair_distance_cv'] = 0
            
            # Density entropy
            center = self.size / 2
            octant_counts = np.zeros(8)
            for pos in positions:
                octant_idx = int(pos[0] > center) + 2*int(pos[1] > center) + 4*int(pos[2] > center)
                octant_counts[octant_idx] += 1
            
            probs = octant_counts / n_defects
            probs = probs[probs > 0]
            entropy = -np.sum(probs * np.log(probs + 1e-10))
            max_entropy = np.log(8)
            metrics['density_entropy'] = float(entropy)
            metrics['density_entropy_normalized'] = float(entropy / max_entropy)
            
        else:
            metrics['defect_anisotropy'] = float('nan')
            metrics['eigenvalues'] = [0, 0, 0]
            metrics['pair_distance_mean'] = 0
            metrics['pair_distance_std'] = 0
            metrics['pair_distance_cv'] = 0
            metrics['density_entropy'] = 0
            metrics['density_entropy_normalized'] = 0
        
        return metrics


def run_organization_test(damping_to_tau: float, tau_cap: float,
                          checkpoints: List[float], seed: int = 42) -> List[Dict]:
    """
    Run organization test to specified checkpoints using validated simulator.
    """
    sim = ValidatedOrganizationSimulator(
        size=32, dt=0.12,
        damping_to_tau=damping_to_tau,
        tau_cap=tau_cap,
        seed=seed
    )
    
    results = []
    
    for T_target in checkpoints:
        # Run to checkpoint
        while sim.T < T_target:
            sim.step()
            
            # Progress indicator every 100 time units
            if sim.step_count % 1000 == 0:
                print(f"    T={sim.T:.0f}...", end="", flush=True)
        
        # Measure organization
        metrics = sim.compute_organization_metrics()
        results.append(metrics)
        print(f" N={metrics['N_defects']}", end="")
    
    print()
    return results


def compute_anisotropy_slope(results: List[Dict]) -> float:
    """Compute slope of anisotropy vs time."""
    valid_results = [r for r in results if not np.isnan(r.get('defect_anisotropy', float('nan')))]
    
    if len(valid_results) < 2:
        return float('nan')
    
    T_vals = np.array([r['T'] for r in valid_results])
    aniso_vals = np.array([r['defect_anisotropy'] for r in valid_results])
    
    # Linear fit
    coeffs = np.polyfit(T_vals, aniso_vals, 1)
    return coeffs[0]  # Slope


def main():
    print("=" * 80)
    print("  DEFECT ORGANIZATION TEST")
    print("=" * 80)
    print()
    print("Question: Does regulated recovery organize defects into isotropic structure?")
    print()
    print("Checkpoints: T = 500, 1000, 2000")
    print("Seeds: 42, 123, 456")
    print()
    
    checkpoints = [500, 1000, 2000]
    seeds = [42, 123, 456]
    
    conditions = {
        'unregulated': {'damping_to_tau': 0.0, 'tau_cap': 3.0},
        'regulated_v1_1': {'damping_to_tau': 0.20, 'tau_cap': 1.8}
    }
    
    all_results = {}
    
    for cond_name, config in conditions.items():
        print(f"Running: {cond_name}")
        print(f"  Config: damping_to_tau={config['damping_to_tau']}, tau_cap={config['tau_cap']}")
        
        cond_results = []
        
        for seed in seeds:
            print(f"  Seed {seed}:", end="")
            t0 = time.time()
            
            results = run_organization_test(
                damping_to_tau=config['damping_to_tau'],
                tau_cap=config['tau_cap'],
                checkpoints=checkpoints,
                seed=seed
            )
            
            print(f" ({time.time()-t0:.1f}s)")
            cond_results.append({'seed': seed, 'checkpoints': results})
        
        all_results[cond_name] = cond_results
        print()
    
    # Analysis
    print("=" * 80)
    print("  ANALYSIS: DEFECT SURVIVAL")
    print("=" * 80)
    print()
    
    print(f"{'Condition':>15} | {'Seed':>6} | {'N(500)':>8} | {'N(1000)':>8} | {'N(2000)':>8}")
    print("-" * 60)
    
    for cond_name, cond_results in all_results.items():
        for seed_result in cond_results:
            seed = seed_result['seed']
            checkpoints_data = seed_result['checkpoints']
            N_500 = checkpoints_data[0]['N_defects']
            N_1000 = checkpoints_data[1]['N_defects']
            N_2000 = checkpoints_data[2]['N_defects']
            print(f"{cond_name:>15} | {seed:>6} | {N_500:>8} | {N_1000:>8} | {N_2000:>8}")
    
    print()
    
    # Compute aggregate statistics
    print("=" * 80)
    print("  ANALYSIS: DEFECT ANISOTROPY")
    print("=" * 80)
    print()
    
    print(f"{'Condition':>15} | {'Seed':>6} | {'Aniso(500)':>10} | {'Aniso(1000)':>10} | {'Aniso(2000)':>10} | {'Slope':>10}")
    print("-" * 80)
    
    aggregate_stats = {}
    
    for cond_name, cond_results in all_results.items():
        aniso_slopes = []
        final_anisos = []
        
        for seed_result in cond_results:
            seed = seed_result['seed']
            checkpoints_data = seed_result['checkpoints']
            
            aniso_500 = checkpoints_data[0].get('defect_anisotropy', float('nan'))
            aniso_1000 = checkpoints_data[1].get('defect_anisotropy', float('nan'))
            aniso_2000 = checkpoints_data[2].get('defect_anisotropy', float('nan'))
            
            slope = compute_anisotropy_slope(checkpoints_data)
            
            aniso_500_str = f"{aniso_500:.3f}" if not np.isnan(aniso_500) else "N/A"
            aniso_1000_str = f"{aniso_1000:.3f}" if not np.isnan(aniso_1000) else "N/A"
            aniso_2000_str = f"{aniso_2000:.3f}" if not np.isnan(aniso_2000) else "N/A"
            slope_str = f"{slope:.6f}" if not np.isnan(slope) else "N/A"
            
            print(f"{cond_name:>15} | {seed:>6} | {aniso_500_str:>10} | {aniso_1000_str:>10} | {aniso_2000_str:>10} | {slope_str:>10}")
            
            if not np.isnan(slope):
                aniso_slopes.append(slope)
            if not np.isnan(aniso_2000):
                final_anisos.append(aniso_2000)
        
        aggregate_stats[cond_name] = {
            'mean_slope': np.mean(aniso_slopes) if aniso_slopes else float('nan'),
            'mean_final_aniso': np.mean(final_anisos) if final_anisos else float('nan')
        }
    
    print()
    
    # Aggregate comparison
    print("=" * 80)
    print("  AGGREGATE COMPARISON")
    print("=" * 80)
    print()
    
    print(f"{'Condition':>15} | {'Mean Final Aniso':>18} | {'Mean Slope':>15}")
    print("-" * 55)
    
    for cond_name, stats in aggregate_stats.items():
        aniso_str = f"{stats['mean_final_aniso']:.3f}" if not np.isnan(stats['mean_final_aniso']) else "N/A"
        slope_str = f"{stats['mean_slope']:.6f}" if not np.isnan(stats['mean_slope']) else "N/A"
        print(f"{cond_name:>15} | {aniso_str:>18} | {slope_str:>15}")
    
    print()
    
    # Verdict
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print()
    
    unreg_stats = aggregate_stats.get('unregulated', {})
    reg_stats = aggregate_stats.get('regulated_v1_1', {})
    
    unreg_aniso = unreg_stats.get('mean_final_aniso', float('nan'))
    reg_aniso = reg_stats.get('mean_final_aniso', float('nan'))
    unreg_slope = unreg_stats.get('mean_slope', float('nan'))
    reg_slope = reg_stats.get('mean_slope', float('nan'))
    
    # Compare defect survival
    unreg_N_final = np.mean([r['checkpoints'][-1]['N_defects'] for r in all_results.get('unregulated', [])])
    reg_N_final = np.mean([r['checkpoints'][-1]['N_defects'] for r in all_results.get('regulated_v1_1', [])])
    
    print(f"Defect survival at T=2000:")
    print(f"  Unregulated: N = {unreg_N_final:.1f}")
    print(f"  Regulated v1.1: N = {reg_N_final:.1f}")
    
    if reg_N_final > unreg_N_final * 1.5:
        print(f"  → Regulated sustains {reg_N_final/unreg_N_final:.1f}× more defects")
    
    print()
    
    # Compare anisotropy
    if not np.isnan(reg_aniso) and not np.isnan(unreg_aniso):
        print(f"Defect anisotropy at T=2000:")
        print(f"  Unregulated: {unreg_aniso:.3f}")
        print(f"  Regulated v1.1: {reg_aniso:.3f}")
        
        if reg_aniso < unreg_aniso:
            improvement = (1 - reg_aniso / unreg_aniso) * 100
            print(f"  → Regulated {improvement:.1f}% lower anisotropy")
        else:
            print(f"  → No improvement in anisotropy")
    
    print()
    
    # Anisotropy slope
    if not np.isnan(reg_slope):
        print(f"Anisotropy slope (change per T):")
        print(f"  Unregulated: {unreg_slope:.6f}")
        print(f"  Regulated v1.1: {reg_slope:.6f}")
        
        if reg_slope < 0:
            print(f"  → Regulated anisotropy DECREASING over time (organizing)")
            verdict = "ORGANIZING"
        elif reg_slope < unreg_slope:
            print(f"  → Regulated anisotropy increasing slower than unregulated")
            verdict = "STABILIZING"
        else:
            print(f"  → Regulated not improving anisotropy")
            verdict = "NO_ORGANIZATION"
    else:
        verdict = "INSUFFICIENT_DATA"
    
    print()
    print(f"VERDICT: {verdict}")
    
    # Save results
    output = {
        'test': 'defect_organization',
        'date': 'December 2025',
        'question': 'Does regulated recovery organize defects into isotropic structure?',
        'config': {
            'size': 32, 'dt': 0.12,
            'checkpoints': checkpoints,
            'seeds': seeds
        },
        'verdict': verdict,
        'summary': {
            'unreg_N_final': float(unreg_N_final),
            'reg_N_final': float(reg_N_final),
            'unreg_final_aniso': float(unreg_aniso) if not np.isnan(unreg_aniso) else None,
            'reg_final_aniso': float(reg_aniso) if not np.isnan(reg_aniso) else None,
            'unreg_slope': float(unreg_slope) if not np.isnan(unreg_slope) else None,
            'reg_slope': float(reg_slope) if not np.isnan(reg_slope) else None
        }
    }
    
    # Simplify results for JSON
    output['per_condition'] = {}
    for cond_name, cond_results in all_results.items():
        output['per_condition'][cond_name] = []
        for seed_result in cond_results:
            simplified = {
                'seed': seed_result['seed'],
                'checkpoints': []
            }
            for cp in seed_result['checkpoints']:
                simplified['checkpoints'].append({
                    'T': cp['T'],
                    'N_defects': cp['N_defects'],
                    'defect_anisotropy': float(cp.get('defect_anisotropy', 0)) if not np.isnan(cp.get('defect_anisotropy', float('nan'))) else None,
                    'tau_localization': cp.get('tau_localization', 0),
                    'density_entropy_normalized': cp.get('density_entropy_normalized', 0)
                })
            output['per_condition'][cond_name].append(simplified)
    
    with open('/app/backend/qmrt_topology/papers/DEFECT_ORGANIZATION_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/DEFECT_ORGANIZATION_RESULTS.json")


if __name__ == "__main__":
    main()
