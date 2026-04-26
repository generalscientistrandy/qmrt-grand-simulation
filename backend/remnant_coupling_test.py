"""
Remnant → Creation Location Coupling Test
==========================================

QUESTION: Can remnant-guided creation lower the minimal sustainable threshold?

MECHANISM:
- When τ exceeds threshold, creation probability still controlled by τ
- But creation LOCATION is biased by remnant density R(x)
- creation_weight[x] = epsilon + remnant[x] ** alpha

VERSIONS:
- A: Random τ creation (baseline)
- B: Linear remnant bias (R^1) 
- C: Strong remnant bias (R^2)

SUCCESS: Remnant coupling sustains at rate < 0.25 (lower than random)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import Dict, List, Tuple
import json


class RemnantGuidedSimulator:
    """
    Simulator with τ-mediated creation guided by remnant memory.
    """
    
    def __init__(self, size: int = 48,
                 tau_creation_threshold: float = 1.001,
                 creation_rate: float = 0.25,
                 remnant_alpha: float = 1.0,  # Remnant bias exponent
                 remnant_epsilon: float = 0.01,  # Prevents total lock-in
                 use_remnant_guidance: bool = True):
        
        self.size = size
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        self.remnant_alpha = remnant_alpha
        self.remnant_epsilon = remnant_epsilon
        self.use_remnant_guidance = use_remnant_guidance
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
        # Tracking
        self.spontaneous_creations = 0
        self.creations_at_remnant = 0  # Creations at high-remnant sites
        self.creation_remnant_values = []  # Remnant value at each creation site
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        mask_interior = r <= interior_r
        mask_exterior = r >= interior_r + 10.0
        mask_transition = ~mask_interior & ~mask_exterior
        
        coupling[mask_interior] = 0.7
        coupling[mask_exterior] = 0.2
        t = (r[mask_transition] - interior_r) / 10.0
        coupling[mask_transition] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        
        return coupling
    
    def inject_vortex_at(self, cx: int, cy: int, cz: int, chirality: int = 1):
        """Inject a single vortex at specific 3D location."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        z_weight = np.exp(-((z - cz)**2) / (2 * 3**2))
        
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_balanced_structure(self, n_pairs: int = 15):
        """Initial seeding to build up remnant field."""
        center = self.size // 2
        seeded = 0
        
        for i in range(n_pairs):
            angle1 = np.random.uniform(0, 2 * np.pi)
            radius1 = np.random.uniform(3, self.size * 0.20)
            cx1 = int(np.clip(center + radius1 * np.cos(angle1), 5, self.size - 5))
            cy1 = int(np.clip(center + radius1 * np.sin(angle1), 5, self.size - 5))
            cz1 = center
            
            angle2 = angle1 + np.random.uniform(0.5, 1.5)
            radius2 = np.random.uniform(3, self.size * 0.20)
            cx2 = int(np.clip(center + radius2 * np.cos(angle2), 5, self.size - 5))
            cy2 = int(np.clip(center + radius2 * np.sin(angle2), 5, self.size - 5))
            cz2 = center
            
            self.inject_vortex_at(cx1, cy1, cz1, +1)
            self.inject_vortex_at(cx2, cy2, cz2, -1)
            seeded += 2
        
        return seeded
    
    def select_creation_location(self) -> Tuple[int, int, int]:
        """
        Select creation location based on remnant field (if enabled).
        
        Returns (cx, cy, cz) for the creation site.
        """
        if not self.use_remnant_guidance:
            # Random location in interior
            center = self.size // 2
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(3, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            cz = center
            return cx, cy, cz
        
        # Remnant-guided selection
        # Compute creation weights: epsilon + remnant^alpha
        weights = self.remnant_epsilon + np.power(self.remnant_field + 1e-10, self.remnant_alpha)
        
        # Only consider interior region
        center = self.size // 2
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_mask = r < self.size * 0.30
        
        weights = weights * interior_mask
        
        # Normalize
        weights_sum = np.sum(weights)
        if weights_sum < 1e-10:
            # Fallback to random
            return self.select_creation_location_random()
        
        weights_flat = weights.flatten() / weights_sum
        
        # Sample location
        idx = np.random.choice(len(weights_flat), p=weights_flat)
        cx = idx // (self.size * self.size)
        cy = (idx % (self.size * self.size)) // self.size
        cz = idx % self.size
        
        return int(cx), int(cy), int(cz)
    
    def select_creation_location_random(self) -> Tuple[int, int, int]:
        """Fallback random selection."""
        center = self.size // 2
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(3, self.size * 0.20)
        cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
        cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
        cz = center
        return cx, cy, cz
    
    def attempt_spontaneous_creation(self):
        """τ-mediated pair creation with remnant-guided location."""
        high_tau_mask = self.tau > self.tau_creation_threshold
        
        if not np.any(high_tau_mask):
            return 0
        
        # Get candidate τ locations for probability
        candidates = np.where(high_tau_mask)
        n_candidates = len(candidates[0])
        
        if n_candidates == 0:
            return 0
        
        # Sample a subset
        n_sample = min(50, n_candidates)
        indices = np.random.choice(n_candidates, n_sample, replace=False)
        
        creations = 0
        
        for idx in indices:
            cx = candidates[0][idx]
            cy = candidates[1][idx]
            cz = candidates[2][idx]
            
            local_tau = self.tau[cx, cy, cz]
            tau_excess = local_tau - self.tau_creation_threshold
            probability = tau_excess * self.creation_rate
            
            if np.random.random() < probability:
                # SELECT LOCATION using remnant guidance
                loc_cx, loc_cy, loc_cz = self.select_creation_location()
                
                # Record remnant value at creation site
                remnant_at_site = self.remnant_field[loc_cx, loc_cy, loc_cz]
                self.creation_remnant_values.append(remnant_at_site)
                
                if remnant_at_site > 0.3:
                    self.creations_at_remnant += 1
                
                # Create balanced pair
                offset_angle = np.random.uniform(0, 2 * np.pi)
                offset_dist = np.random.uniform(3, 6)
                
                cx2 = int(np.clip(loc_cx + offset_dist * np.cos(offset_angle), 3, self.size - 3))
                cy2 = int(np.clip(loc_cy + offset_dist * np.sin(offset_angle), 3, self.size - 3))
                
                self.inject_vortex_at(loc_cx, loc_cy, loc_cz, +1)
                self.inject_vortex_at(cx2, cy2, loc_cz, -1)
                
                creations += 1
                self.spontaneous_creations += 1
                
                break  # One per step
        
        return creations
    
    def step(self, dt: float = 0.04):
        """Evolution step with remnant-guided τ creation."""
        self.step_count += 1
        
        self.attempt_spontaneous_creation()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        tau_target = 1.0 + self.tau_response * (energy - np.mean(energy))
        self.tau += self.tau_relaxation * (tau_target - self.tau)
        self.tau = np.clip(self.tau, 0.5, 2.0)
        
        c_eff_sq = self.c_0_sq * self.tau
        
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        self.remnant_field += 0.02 * topology_norm
        self.remnant_field *= 0.999
        self.remnant_field = np.clip(self.remnant_field, 0, 1)
        
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects(self, threshold: float = 0.4) -> Dict:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        
        n_pos = 0
        n_neg = 0
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                local_vort = vorticity[cx, cy, coords[2][0]]
                
                if local_vort > 0.05:
                    n_pos += 1
                elif local_vort < -0.05:
                    n_neg += 1
        
        return {'n_pos': n_pos, 'n_neg': n_neg, 'n_total': n_pos + n_neg}


def run_remnant_coupling_test(rate: float, alpha: float, use_guidance: bool, steps: int = 1000):
    """Run a single test configuration."""
    sim = RemnantGuidedSimulator(
        size=48,
        tau_creation_threshold=1.001,
        creation_rate=rate,
        remnant_alpha=alpha,
        remnant_epsilon=0.01,
        use_remnant_guidance=use_guidance
    )
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    sim.seed_balanced_structure(n_pairs=15)
    
    # Run warmup to build remnant
    for _ in range(200):
        sim.step()
    
    # Track late activity
    late_activity = []
    for step in range(steps):
        sim.step()
        if step >= steps - 400 and step % 50 == 0:
            defects = sim.detect_defects()
            late_activity.append(defects['n_total'])
    
    avg_late_n = np.mean(late_activity)
    
    # Compute reoccupation rate
    if sim.creation_remnant_values:
        avg_remnant_at_creation = np.mean(sim.creation_remnant_values)
        high_remnant_frac = sim.creations_at_remnant / max(1, sim.spontaneous_creations)
    else:
        avg_remnant_at_creation = 0
        high_remnant_frac = 0
    
    return {
        'avg_late_n': avg_late_n,
        'creations': sim.spontaneous_creations,
        'avg_remnant_at_creation': avg_remnant_at_creation,
        'high_remnant_frac': high_remnant_frac,
        'sustained': avg_late_n > 0.3,
    }


def run_comparison_sweep():
    """Compare random vs remnant-guided creation."""
    print("=" * 80)
    print("  REMNANT → CREATION COUPLING TEST")
    print("=" * 80)
    print()
    print("Question: Can remnant-guided creation lower the minimal sustainable threshold?")
    print()
    print("Baseline (random): minimal sustainable rate = 0.25")
    print()
    
    # Test configurations
    rates = [0.10, 0.15, 0.20, 0.25]
    alphas = [1.0, 2.0]
    
    results = []
    
    print("Testing RANDOM (no remnant guidance):")
    print("-" * 60)
    print(f"{'Rate':>6} │ {'Avg N':>6} │ {'Creates':>8} │ {'Sustained':>9}")
    print("-" * 60)
    
    for rate in rates:
        r = run_remnant_coupling_test(rate, alpha=1.0, use_guidance=False)
        results.append({'type': 'random', 'rate': rate, **r})
        ok = "YES" if r['sustained'] else "no"
        print(f"{rate:>6.2f} │ {r['avg_late_n']:>6.2f} │ {r['creations']:>8} │ {ok:>9}")
    
    print()
    print("Testing REMNANT-GUIDED (alpha=1.0, linear):")
    print("-" * 60)
    print(f"{'Rate':>6} │ {'Avg N':>6} │ {'Creates':>8} │ {'Hi-Remn%':>8} │ {'Sustained':>9}")
    print("-" * 60)
    
    for rate in rates:
        r = run_remnant_coupling_test(rate, alpha=1.0, use_guidance=True)
        results.append({'type': 'remnant_1.0', 'rate': rate, **r})
        ok = "YES" if r['sustained'] else "no"
        print(f"{rate:>6.2f} │ {r['avg_late_n']:>6.2f} │ {r['creations']:>8} │ "
              f"{r['high_remnant_frac']*100:>7.1f}% │ {ok:>9}")
    
    print()
    print("Testing REMNANT-GUIDED (alpha=2.0, quadratic):")
    print("-" * 60)
    print(f"{'Rate':>6} │ {'Avg N':>6} │ {'Creates':>8} │ {'Hi-Remn%':>8} │ {'Sustained':>9}")
    print("-" * 60)
    
    for rate in rates:
        r = run_remnant_coupling_test(rate, alpha=2.0, use_guidance=True)
        results.append({'type': 'remnant_2.0', 'rate': rate, **r})
        ok = "YES" if r['sustained'] else "no"
        print(f"{rate:>6.2f} │ {r['avg_late_n']:>6.2f} │ {r['creations']:>8} │ "
              f"{r['high_remnant_frac']*100:>7.1f}% │ {ok:>9}")
    
    # Analysis
    print()
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    
    # Find minimal sustainable for each type
    for typ in ['random', 'remnant_1.0', 'remnant_2.0']:
        type_results = [r for r in results if r['type'] == typ]
        sustained = [r for r in type_results if r['sustained']]
        if sustained:
            min_rate = min(r['rate'] for r in sustained)
            print(f"{typ:>15}: minimal sustainable rate = {min_rate}")
        else:
            print(f"{typ:>15}: no sustainable configuration found")
    
    # Save results (convert numpy/bool types for JSON)
    output_path = '/app/backend/qmrt_topology/papers/remnant_coupling_results.json'
    clean_results = []
    for r in results:
        clean_r = {}
        for k, v in r.items():
            if isinstance(v, (np.bool_, bool)):
                clean_r[k] = bool(v)
            elif isinstance(v, (np.integer, np.floating)):
                clean_r[k] = float(v)
            else:
                clean_r[k] = v
        clean_results.append(clean_r)
    
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'remnant_creation_coupling',
            'results': clean_results,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    results = run_comparison_sweep()
