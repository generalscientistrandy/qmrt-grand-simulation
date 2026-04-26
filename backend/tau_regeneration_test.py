"""
τ-Mediated Pair Creation Test
==============================

QUESTION: Can local high-τ regions nucleate balanced vortex pairs without
          external injection?

This tests whether thermal/energetic polarity can feed topology.

MECHANISM:
- When local τ exceeds threshold, there's a probability of pair creation
- Always creates balanced +/- pair (not unbalanced)
- Local, not global (creation happens at the high-τ location)

SUCCESS: Structure persists or self-sustains without external injection
FAILURE: Structure still collapses (threshold too high, or mechanism insufficient)
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import Dict, List
import json


class TauRegenerationSimulator:
    """
    Simulator with τ-mediated spontaneous pair creation.
    
    Key addition: When local τ exceeds threshold, balanced vortex pairs
    can spontaneously nucleate.
    """
    
    def __init__(self, size: int = 48, 
                 tau_creation_threshold: float = 1.05,
                 creation_rate: float = 0.001):
        self.size = size
        
        # τ-mediated creation parameters
        self.tau_creation_threshold = tau_creation_threshold
        self.creation_rate = creation_rate
        
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
        
        # Track spontaneous creations
        self.spontaneous_creations = 0
        
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
        # Create vortex centered at (cx, cy) extending in z
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        
        # Localize in z as well
        z_weight = np.exp(-((z - cz)**2) / (2 * 3**2))
        
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        
        # Blend with z-weighting
        blend = 0.3 * z_weight
        combined = current * (1 - blend) + current * vortex / (np.abs(current) + 0.01) * blend
        
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_balanced_structure(self, n_pairs: int = 10):
        """Initial seeding only."""
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
    
    def attempt_spontaneous_creation(self):
        """
        τ-MEDIATED PAIR CREATION
        
        At locations where τ > threshold, there's a probability of
        creating a balanced +/- vortex pair.
        """
        # Find high-τ regions
        high_tau_mask = self.tau > self.tau_creation_threshold
        
        if not np.any(high_tau_mask):
            return 0
        
        # Get candidate locations
        candidates = np.where(high_tau_mask)
        n_candidates = len(candidates[0])
        
        if n_candidates == 0:
            return 0
        
        # Sample a subset of candidates (for efficiency)
        n_sample = min(100, n_candidates)
        indices = np.random.choice(n_candidates, n_sample, replace=False)
        
        creations = 0
        
        for idx in indices:
            cx = candidates[0][idx]
            cy = candidates[1][idx]
            cz = candidates[2][idx]
            
            local_tau = self.tau[cx, cy, cz]
            
            # Probability proportional to τ excess
            tau_excess = local_tau - self.tau_creation_threshold
            probability = tau_excess * self.creation_rate
            
            if np.random.random() < probability:
                # Create balanced pair nearby
                # + vortex at current location
                # - vortex offset by small distance
                offset_angle = np.random.uniform(0, 2 * np.pi)
                offset_dist = np.random.uniform(3, 6)
                
                cx2 = int(np.clip(cx + offset_dist * np.cos(offset_angle), 3, self.size - 3))
                cy2 = int(np.clip(cy + offset_dist * np.sin(offset_angle), 3, self.size - 3))
                
                self.inject_vortex_at(cx, cy, cz, +1)
                self.inject_vortex_at(cx2, cy2, cz, -1)
                
                creations += 1
                self.spontaneous_creations += 1
                
                # Only allow one creation per step (to prevent runaway)
                break
        
        return creations
    
    def step(self, dt: float = 0.04):
        """Evolution step with τ-mediated regeneration."""
        self.step_count += 1
        
        # τ-MEDIATED PAIR CREATION (the new mechanism)
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
        """Detect defects and count by sign."""
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
    
    def compute_state(self) -> Dict:
        """Compute detailed state."""
        defects = self.detect_defects()
        
        # τ statistics
        tau_max = float(np.max(self.tau))
        tau_above_threshold = float(np.mean(self.tau > self.tau_creation_threshold))
        
        return {
            'step': self.step_count,
            'n_total': defects['n_total'],
            'n_pos': defects['n_pos'],
            'n_neg': defects['n_neg'],
            'tau_max': tau_max,
            'tau_mean': float(np.mean(self.tau)),
            'tau_above_threshold': tau_above_threshold,
            'spontaneous_creations': self.spontaneous_creations,
            'channel_mean': float(np.mean(self.channel_assignment)),
        }


def run_tau_regeneration_test(threshold: float = 1.03, rate: float = 0.01):
    """
    Test τ-mediated pair creation.
    """
    print("=" * 80)
    print("  τ-MEDIATED PAIR CREATION TEST")
    print("=" * 80)
    print()
    print("Question: Can local high-τ regions nucleate balanced vortex pairs")
    print("          without external injection?")
    print()
    print(f"Parameters:")
    print(f"  τ creation threshold: {threshold}")
    print(f"  Creation rate:        {rate}")
    print()
    
    sim = TauRegenerationSimulator(
        size=48,
        tau_creation_threshold=threshold,
        creation_rate=rate
    )
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Seed with balanced structure
    seeded = sim.seed_balanced_structure(n_pairs=15)
    print(f"Seeded {seeded} vortices (15 +/- pairs)")
    print()
    
    history = []
    
    print(f"{'Step':>5} │ {'N':>4} │ {'+':>3} {'-':>3} │ {'τ_max':>6} │ "
          f"{'τ>thresh':>8} │ {'Creations':>9}")
    print("-" * 60)
    
    for step in range(2000):
        sim.step()
        
        if step % 50 == 0:
            state = sim.compute_state()
            history.append(state)
            
            if step % 100 == 0:
                print(f"{step:>5} │ {state['n_total']:>4} │ "
                      f"{state['n_pos']:>3} {state['n_neg']:>3} │ "
                      f"{state['tau_max']:>6.3f} │ "
                      f"{state['tau_above_threshold']:>8.4f} │ "
                      f"{state['spontaneous_creations']:>9}")
    
    # === ANALYSIS ===
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    final_n = history[-1]['n_total']
    total_creations = history[-1]['spontaneous_creations']
    
    print()
    print(f"Final defect count:     {final_n}")
    print(f"Total spontaneous creations: {total_creations}")
    
    # Check if structure persisted
    extinction_step = None
    for h in history:
        if h['n_total'] == 0:
            extinction_step = h['step']
            break
    
    if extinction_step:
        print(f"First extinction at step: {extinction_step}")
    else:
        print("No extinction (structure persisted throughout)")
    
    # Compare to no-regeneration case
    print()
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print()
    
    if final_n > 0 and total_creations > 10:
        print("RESULT: τ-MEDIATED REGENERATION SUSTAINS STRUCTURE")
        print()
        print(f"Without external injection, the system maintained {final_n} defects")
        print(f"through {total_creations} spontaneous pair creations.")
        print()
        print("This demonstrates that thermal → topological coupling can")
        print("provide internal regeneration in a zero-balanced model.")
        verdict = "sustains"
    elif final_n > 0:
        print("RESULT: PARTIAL SUCCESS")
        print()
        print(f"Structure present ({final_n} defects) but few spontaneous creations ({total_creations}).")
        print("Initial seeding may still be dominant.")
        verdict = "partial"
    elif total_creations > 0:
        print("RESULT: REGENERATION INSUFFICIENT")
        print()
        print(f"τ-mediated creation occurred ({total_creations} events)")
        print("but could not prevent extinction.")
        print("Rate or threshold may need adjustment.")
        verdict = "insufficient"
    else:
        print("RESULT: NO REGENERATION")
        print()
        print("No spontaneous creations occurred.")
        print("τ never exceeded threshold, or rate too low.")
        verdict = "none"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/tau_regeneration_test_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'tau_mediated_pair_creation',
            'threshold': threshold,
            'rate': rate,
            'history': history,
            'final_n': final_n,
            'total_creations': total_creations,
            'extinction_step': extinction_step,
            'verdict': verdict,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, verdict


if __name__ == "__main__":
    # Test with moderate threshold and rate
    history, verdict = run_tau_regeneration_test(threshold=1.03, rate=0.01)
