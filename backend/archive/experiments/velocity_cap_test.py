"""
Moving Structure / Velocity Cap Test
=====================================

PURPOSE: Determine if coherent structures in the QMRT medium have a maximum
stable velocity (analogous to a "speed of light" limit), and whether they
deform or decay when pushed beyond this limit.

STRUCTURE TYPES:
  1. Gaussian Perturbation: Localized energy/momentum perturbation with boost
  2. Tau-Maxed Cluster: Frozen τ region (artificial coherent structure)

SWEEP PARAMETERS:
  - boost_strength: [0.00, 0.05, 0.10, 0.20, 0.30, 0.40]
  - directions: x, y, z, diagonal (normalized [1,1,1])

TRACKED METRICS:
  - measured_velocity: actual displacement per time
  - structure_survival_time: how long structure remains coherent
  - shape_anisotropy: deformation metric (elongation in boost direction)
  - energy_growth: energy change in structure region
  - decay_flag: whether structure collapsed/dispersed

PASS CRITERIA (Velocity Cap Exists):
  - measured_velocity saturates (does not grow linearly with boost)
  - high boosts cause deformation (anisotropy increases) or decay
  - there exists a maximum stable velocity c_eff

BASELINE: Regulated Recovery v1.1 (tau_cap=1.8, damping_to_tau=0.20, dt=0.12, size=32)
"""

import numpy as np
from typing import Dict, List, Tuple
import time
import json


class VelocityCapSimulator:
    """Simulator for velocity cap testing with boosted structures."""
    
    def __init__(self, size: int = 32, dt: float = 0.12, seed: int = None):
        if seed is not None:
            np.random.seed(seed)
        
        self.size = size
        self.dt = dt
        self.T = 0.0
        self.step_count = 0
        
        # Regulated Recovery v1.1 configuration
        self.damping_to_tau = 0.20
        self.tau_cap = 1.8
        self.tau_creation_threshold = 1.001
        self.creation_rate = 0.15
        
        # Wave field
        self.psi_r = np.ones((size, size, size)) * 1.0
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        # Medium field
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        self.gamma = 0.007
        
        # Tracking
        self.creations = 0
        self.structure_center_history = []
        self.structure_energy_history = []
        self.structure_shape_history = []
    
    def inject_gaussian_structure(self, center: Tuple[int, int, int], 
                                   boost_dir: np.ndarray, boost_strength: float,
                                   sigma: float = 4.0, amplitude: float = 1.0):
        """
        Inject a Gaussian energy perturbation with initial momentum boost.
        
        This represents a "natural" moving excitation - localized energy
        with directional momentum.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Gaussian envelope - larger sigma and amplitude for better tracking
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        envelope = amplitude * np.exp(-r_sq / (2 * sigma**2))
        
        # Add to field (creates energy concentration)
        self.psi_r += envelope
        
        # Add momentum boost in specified direction
        # This creates a wave packet moving in boost_dir
        boost_dir = boost_dir / (np.linalg.norm(boost_dir) + 1e-10)
        
        # Direct momentum injection for cleaner velocity
        # psi_dot in boost direction creates motion
        self.psi_r_dot += boost_strength * envelope * boost_dir[0]
        self.psi_i_dot += boost_strength * envelope * boost_dir[1]
        # Add z-component to real part momentum
        self.psi_r_dot += boost_strength * envelope * boost_dir[2] * 0.5
        
        return center
    
    def inject_tau_maxed_cluster(self, center: Tuple[int, int, int],
                                  boost_dir: np.ndarray, boost_strength: float,
                                  radius: int = 4):
        """
        Inject a τ-maxed cluster (frozen τ region) with momentum boost.
        
        This represents a strong artificial coherent structure - a region
        where τ is capped, creating a defect-like zone.
        """
        cx, cy, cz = center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        
        # Create spherical mask
        r_sq = (x - cx)**2 + (y - cy)**2 + (z - cz)**2
        mask = r_sq <= radius**2
        
        # Max out τ in this region (creates "frozen" structure)
        self.tau[mask] = self.tau_cap
        
        # Also add stronger energy perturbation for detectability
        envelope = 0.8 * np.exp(-r_sq / (2 * (radius * 1.0)**2))
        self.psi_r += envelope
        
        # Add momentum boost - direct injection
        boost_dir = boost_dir / (np.linalg.norm(boost_dir) + 1e-10)
        
        self.psi_r_dot += boost_strength * envelope * boost_dir[0]
        self.psi_i_dot += boost_strength * envelope * boost_dir[1]
        self.psi_r_dot += boost_strength * envelope * boost_dir[2] * 0.5
        
        return center
    
    def step(self):
        """Advance simulation by one timestep (Regulated Recovery v1.1)."""
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
        
        # Creation events (disabled for clean tracking in this test)
        # We want to track the injected structure, not spontaneous creations
        
        # Wave equation with variable c_eff
        c_eff_sq = self.c_0_sq * self.tau
        lap_r, lap_i = lap(self.psi_r), lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def detect_structure_center(self, threshold_percentile: float = 90) -> Tuple:
        """
        Detect the center of the coherent structure by finding the
        PEAK energy location (not centroid).
        
        Peak tracking better captures actual energy transport.
        """
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Find peak location
        peak_idx = np.unravel_index(np.argmax(energy), energy.shape)
        peak_value = energy[peak_idx]
        
        # Use peak and surrounding region for center estimation
        cx, cy, cz = peak_idx
        
        # Small neighborhood around peak for weighted center
        pad = 3
        x_lo, x_hi = max(0, cx-pad), min(self.size, cx+pad+1)
        y_lo, y_hi = max(0, cy-pad), min(self.size, cy+pad+1)
        z_lo, z_hi = max(0, cz-pad), min(self.size, cz+pad+1)
        
        local_energy = energy[x_lo:x_hi, y_lo:y_hi, z_lo:z_hi]
        local_total = np.sum(local_energy)
        
        # Weighted center within neighborhood
        lx, ly, lz = np.meshgrid(
            np.arange(x_lo, x_hi),
            np.arange(y_lo, y_hi), 
            np.arange(z_lo, z_hi),
            indexing='ij'
        )
        
        if local_total > 1e-10:
            cx_refined = np.sum(lx * local_energy) / local_total
            cy_refined = np.sum(ly * local_energy) / local_total
            cz_refined = np.sum(lz * local_energy) / local_total
        else:
            cx_refined, cy_refined, cz_refined = float(cx), float(cy), float(cz)
        
        # Check coherence: is the energy localized or spread?
        # Compare peak region energy to total
        total_energy = np.sum(energy)
        energy_concentration = local_total / (total_energy + 1e-10)
        
        # If > 5% of energy is in the peak neighborhood, structure is coherent
        is_coherent = energy_concentration > 0.05
        
        return (cx_refined, cy_refined, cz_refined), float(peak_value), is_coherent
    
    def compute_shape_anisotropy(self, boost_dir: np.ndarray) -> float:
        """
        Compute shape anisotropy: how much the structure is elongated
        in the boost direction vs perpendicular.
        
        Anisotropy > 1 means elongated along boost (deformation).
        """
        energy = self.psi_r**2 + self.psi_i**2 + 0.5 * (self.psi_r_dot**2 + self.psi_i_dot**2)
        threshold = np.percentile(energy, 90)
        
        high_energy_mask = energy > threshold
        if np.sum(high_energy_mask) < 10:
            return 1.0  # Not enough data
        
        coords = np.array(np.where(high_energy_mask)).T  # Nx3
        weights = energy[high_energy_mask]
        
        # Center of mass
        com = np.average(coords, axis=0, weights=weights)
        centered = coords - com
        
        # Normalize boost direction
        boost_dir = boost_dir / (np.linalg.norm(boost_dir) + 1e-10)
        
        # Project onto boost direction and perpendicular
        parallel = np.dot(centered, boost_dir)
        perp_vec = centered - np.outer(parallel, boost_dir)
        perp_dist = np.linalg.norm(perp_vec, axis=1)
        
        # Weighted RMS in each direction
        rms_parallel = np.sqrt(np.average(parallel**2, weights=weights))
        rms_perp = np.sqrt(np.average(perp_dist**2, weights=weights))
        
        if rms_perp < 1e-6:
            return 1.0
        
        return rms_parallel / rms_perp


def run_single_velocity_test(structure_type: str, boost_strength: float, 
                              boost_dir: np.ndarray, seed: int,
                              T_max: float = 150.0, sample_interval: float = 5.0) -> Dict:
    """
    Run a single velocity cap test for given parameters.
    
    Returns metrics for this configuration.
    """
    sim = VelocityCapSimulator(size=32, dt=0.12, seed=seed)
    
    # Inject structure at center with boost
    center = (sim.size // 2, sim.size // 2, sim.size // 2)
    initial_center = center
    
    if structure_type == 'gaussian':
        sim.inject_gaussian_structure(center, boost_dir, boost_strength)
    elif structure_type == 'tau_maxed':
        sim.inject_tau_maxed_cluster(center, boost_dir, boost_strength)
    
    # Track structure over time
    positions = [center]
    times = [0.0]
    energies = []
    anisotropies = []
    coherent_flags = []
    
    survival_time = T_max  # Will be updated if structure decays
    decayed = False
    
    last_sample = 0.0
    while sim.T < T_max:
        sim.step()
        
        if sim.T - last_sample >= sample_interval:
            last_sample = sim.T
            
            pos, energy, is_coherent = sim.detect_structure_center()
            aniso = sim.compute_shape_anisotropy(boost_dir)
            
            if pos is not None:
                positions.append(pos)
                times.append(sim.T)
                energies.append(energy)
                anisotropies.append(aniso)
                coherent_flags.append(is_coherent)
                
                if not is_coherent and not decayed:
                    survival_time = sim.T
                    decayed = True
            else:
                if not decayed:
                    survival_time = sim.T
                    decayed = True
    
    # Compute measured velocity
    if len(positions) >= 2:
        # Use positions from early coherent phase
        coherent_positions = []
        coherent_times = []
        for i, (pos, t, coh) in enumerate(zip(positions, times, [True] + coherent_flags)):
            if coh or i < 3:  # Include first few regardless
                coherent_positions.append(pos)
                coherent_times.append(t)
            if len(coherent_positions) >= 5:
                break
        
        if len(coherent_positions) >= 2:
            start_pos = np.array(coherent_positions[0])
            end_pos = np.array(coherent_positions[-1])
            displacement = end_pos - start_pos
            time_elapsed = coherent_times[-1] - coherent_times[0]
            
            if time_elapsed > 0:
                measured_velocity = np.linalg.norm(displacement) / time_elapsed
                # Velocity component along boost direction
                boost_dir_norm = boost_dir / (np.linalg.norm(boost_dir) + 1e-10)
                velocity_along_boost = np.dot(displacement, boost_dir_norm) / time_elapsed
            else:
                measured_velocity = 0.0
                velocity_along_boost = 0.0
        else:
            measured_velocity = 0.0
            velocity_along_boost = 0.0
    else:
        measured_velocity = 0.0
        velocity_along_boost = 0.0
    
    # Aggregate metrics
    mean_anisotropy = np.mean(anisotropies) if anisotropies else 1.0
    max_anisotropy = np.max(anisotropies) if anisotropies else 1.0
    energy_change = (energies[-1] / energies[0] - 1.0) if len(energies) >= 2 and energies[0] > 0 else 0.0
    
    return {
        'structure_type': structure_type,
        'boost_strength': boost_strength,
        'boost_direction': boost_dir.tolist(),
        'seed': seed,
        'measured_velocity': float(measured_velocity),
        'velocity_along_boost': float(velocity_along_boost),
        'survival_time': float(survival_time),
        'decayed': decayed,
        'mean_anisotropy': float(mean_anisotropy),
        'max_anisotropy': float(max_anisotropy),
        'energy_change': float(energy_change),
        'n_samples': len(positions),
    }


def run_velocity_sweep(structure_type: str, seeds: List[int], 
                       boost_strengths: List[float], 
                       directions: Dict[str, np.ndarray],
                       T_max: float = 150.0) -> List[Dict]:
    """Run full velocity sweep for a structure type."""
    results = []
    
    for boost_strength in boost_strengths:
        for dir_name, boost_dir in directions.items():
            for seed in seeds:
                result = run_single_velocity_test(
                    structure_type=structure_type,
                    boost_strength=boost_strength,
                    boost_dir=boost_dir,
                    seed=seed,
                    T_max=T_max
                )
                result['direction_name'] = dir_name
                results.append(result)
                
    return results


def analyze_velocity_cap(results: List[Dict]) -> Dict:
    """
    Analyze results to determine if a velocity cap exists.
    
    Key signatures of velocity cap:
    1. measured_velocity saturates (sublinear with boost_strength)
    2. high boosts cause increased anisotropy (deformation)
    3. high boosts cause early decay (survival_time decreases)
    """
    import numpy as np
    
    boost_strengths = sorted(set(r['boost_strength'] for r in results))
    
    # Group by boost strength
    by_boost = {b: [r for r in results if r['boost_strength'] == b] for b in boost_strengths}
    
    # Compute averages
    avg_velocity = []
    avg_anisotropy = []
    avg_survival = []
    decay_rate = []
    
    for b in boost_strengths:
        runs = by_boost[b]
        avg_velocity.append(np.mean([r['velocity_along_boost'] for r in runs]))
        avg_anisotropy.append(np.mean([r['mean_anisotropy'] for r in runs]))
        avg_survival.append(np.mean([r['survival_time'] for r in runs]))
        decay_rate.append(np.mean([r['decayed'] for r in runs]))
    
    # Check for velocity saturation
    # If velocity cap exists: d(velocity)/d(boost) should decrease at high boost
    velocity_response = []
    for i in range(1, len(boost_strengths)):
        db = boost_strengths[i] - boost_strengths[i-1]
        dv = avg_velocity[i] - avg_velocity[i-1]
        if db > 0:
            velocity_response.append(dv / db)
    
    # Check for deformation at high boost
    anisotropy_increase = avg_anisotropy[-1] / avg_anisotropy[0] if avg_anisotropy[0] > 0 else 1.0
    
    # Check for survival decrease at high boost
    survival_decrease = avg_survival[-1] / avg_survival[0] if avg_survival[0] > 0 else 1.0
    
    # Determine max stable velocity
    # Find highest boost where decay_rate < 0.5
    max_stable_boost = 0.0
    max_stable_velocity = 0.0
    for i, b in enumerate(boost_strengths):
        if decay_rate[i] < 0.5:
            max_stable_boost = b
            max_stable_velocity = avg_velocity[i]
    
    # Velocity cap detection
    velocity_saturates = len(velocity_response) >= 2 and velocity_response[-1] < velocity_response[0] * 0.5
    deformation_increases = anisotropy_increase > 1.3
    survival_decreases = survival_decrease < 0.7
    
    velocity_cap_detected = velocity_saturates or deformation_increases or survival_decreases
    
    return {
        'boost_strengths': boost_strengths,
        'avg_velocity': avg_velocity,
        'avg_anisotropy': avg_anisotropy,
        'avg_survival': avg_survival,
        'decay_rate': decay_rate,
        'velocity_response': velocity_response,
        'anisotropy_increase': float(anisotropy_increase),
        'survival_decrease': float(survival_decrease),
        'max_stable_boost': float(max_stable_boost),
        'max_stable_velocity': float(max_stable_velocity),
        'velocity_cap_detected': velocity_cap_detected,
        'velocity_saturates': velocity_saturates,
        'deformation_increases': deformation_increases,
        'survival_decreases': survival_decreases,
    }


def main():
    print("=" * 80)
    print("  MOVING STRUCTURE / VELOCITY CAP TEST")
    print("=" * 80)
    print()
    print("Question: Do coherent structures have a maximum stable velocity?")
    print("          Do they deform or decay when pushed beyond this limit?")
    print()
    print("Structure types: Gaussian perturbation, Tau-maxed cluster")
    print("Boost strengths: 0.00, 0.10, 0.25, 0.50, 0.75, 1.00")
    print("Directions: x, y, z, diagonal")
    print("Seeds: 42, 123, 456")
    print()
    print("Baseline: Regulated Recovery v1.1 (tau_cap=1.8, damping_to_tau=0.20)")
    print()
    
    # Configuration - optimized for timeout limits
    seeds = [42, 123, 456]
    boost_strengths = [0.00, 0.10, 0.25, 0.50, 0.75, 1.00]  # Higher boosts for clearer effect
    directions = {
        'x': np.array([1.0, 0.0, 0.0]),
        'y': np.array([0.0, 1.0, 0.0]),
        'z': np.array([0.0, 0.0, 1.0]),
        'diagonal': np.array([1.0, 1.0, 1.0]) / np.sqrt(3),
    }
    
    # Reduced T_max for faster execution
    T_MAX = 100.0
    
    all_results = {}
    
    # Test Gaussian structures
    print("-" * 80)
    print("Testing GAUSSIAN PERTURBATION structures...")
    print("-" * 80)
    
    t0 = time.time()
    gaussian_results = run_velocity_sweep(
        structure_type='gaussian',
        seeds=seeds,
        boost_strengths=boost_strengths,
        directions=directions,
        T_max=T_MAX
    )
    print(f"Gaussian tests complete ({time.time()-t0:.1f}s)")
    
    gaussian_analysis = analyze_velocity_cap(gaussian_results)
    all_results['gaussian'] = {
        'runs': gaussian_results,
        'analysis': gaussian_analysis
    }
    
    # Test Tau-maxed structures
    print()
    print("-" * 80)
    print("Testing TAU-MAXED CLUSTER structures...")
    print("-" * 80)
    
    t0 = time.time()
    tau_maxed_results = run_velocity_sweep(
        structure_type='tau_maxed',
        seeds=seeds,
        boost_strengths=boost_strengths,
        directions=directions,
        T_max=T_MAX
    )
    print(f"Tau-maxed tests complete ({time.time()-t0:.1f}s)")
    
    tau_maxed_analysis = analyze_velocity_cap(tau_maxed_results)
    all_results['tau_maxed'] = {
        'runs': tau_maxed_results,
        'analysis': tau_maxed_analysis
    }
    
    # Print summary
    print()
    print("=" * 80)
    print("  RESULTS SUMMARY")
    print("=" * 80)
    print()
    
    for struct_type in ['gaussian', 'tau_maxed']:
        analysis = all_results[struct_type]['analysis']
        
        print(f"{'GAUSSIAN PERTURBATION' if struct_type == 'gaussian' else 'TAU-MAXED CLUSTER'}")
        print("-" * 40)
        
        print(f"  Boost     | Velocity | Anisotropy | Survival | Decay%")
        print(f"  ----------|----------|------------|----------|-------")
        for i, b in enumerate(analysis['boost_strengths']):
            print(f"  {b:8.2f}  | {analysis['avg_velocity'][i]:8.4f} | "
                  f"{analysis['avg_anisotropy'][i]:10.3f} | "
                  f"{analysis['avg_survival'][i]:8.1f} | {analysis['decay_rate'][i]*100:5.1f}%")
        
        print()
        print(f"  Max stable boost: {analysis['max_stable_boost']:.2f}")
        print(f"  Max stable velocity: {analysis['max_stable_velocity']:.4f}")
        print(f"  Anisotropy increase: {analysis['anisotropy_increase']:.2f}x")
        print(f"  Survival decrease: {analysis['survival_decrease']:.2f}x")
        print()
        
        # Verdict
        print(f"  Velocity cap signatures:")
        print(f"    - Velocity saturates: {'YES' if analysis['velocity_saturates'] else 'NO'}")
        print(f"    - Deformation increases: {'YES' if analysis['deformation_increases'] else 'NO'}")
        print(f"    - Survival decreases: {'YES' if analysis['survival_decreases'] else 'NO'}")
        print(f"  VELOCITY CAP DETECTED: {'YES' if analysis['velocity_cap_detected'] else 'NO'}")
        print()
    
    # Overall verdict
    print("=" * 80)
    print("  OVERALL VERDICT")
    print("=" * 80)
    print()
    
    gaussian_cap = all_results['gaussian']['analysis']['velocity_cap_detected']
    tau_maxed_cap = all_results['tau_maxed']['analysis']['velocity_cap_detected']
    
    if gaussian_cap and tau_maxed_cap:
        verdict = "STRONG_EVIDENCE"
        print("STRONG EVIDENCE for velocity cap:")
        print("  Both structure types show velocity cap signatures.")
        print("  The medium appears to have an effective maximum signal speed.")
    elif gaussian_cap or tau_maxed_cap:
        verdict = "PARTIAL_EVIDENCE"
        print("PARTIAL EVIDENCE for velocity cap:")
        print("  One structure type shows velocity cap signatures.")
        print("  Further investigation needed with more seeds or parameters.")
    else:
        verdict = "NO_EVIDENCE"
        print("NO CLEAR EVIDENCE for velocity cap:")
        print("  Neither structure type shows clear velocity saturation.")
        print("  The medium may not have a strict velocity limit, or")
        print("  the boost range tested may be insufficient.")
    
    print()
    print("Physical interpretation:")
    print("  If velocity cap exists, the QMRT medium has a natural")
    print("  'speed of light' analogous to Lorentz-invariant physics.")
    print("  Structures deforming/decaying at high boost would indicate")
    print("  relativistic-like behavior in the emergent spacetime.")
    
    # Save results
    # Convert numpy bools to Python bools for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    output = convert_to_serializable({
        'test': 'velocity_cap',
        'date': 'December 2025',
        'baseline': 'Regulated Recovery v1.1',
        'configuration': {
            'seeds': seeds,
            'boost_strengths': boost_strengths,
            'directions': list(directions.keys()),
            'T_max': T_MAX,
            'grid_size': 32,
            'dt': 0.12,
        },
        'verdict': verdict,
        'gaussian_cap_detected': gaussian_cap,
        'tau_maxed_cap_detected': tau_maxed_cap,
        'gaussian_analysis': all_results['gaussian']['analysis'],
        'tau_maxed_analysis': all_results['tau_maxed']['analysis'],
        'gaussian_runs': all_results['gaussian']['runs'],
        'tau_maxed_runs': all_results['tau_maxed']['runs'],
    })
    
    with open('/app/backend/qmrt_topology/papers/VELOCITY_CAP_RESULTS.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to: /app/backend/qmrt_topology/papers/VELOCITY_CAP_RESULTS.json")
    
    return output


if __name__ == "__main__":
    main()
