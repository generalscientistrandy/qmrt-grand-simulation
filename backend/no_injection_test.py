"""
No-Injection Balanced Evolution Test
=====================================

FUNDAMENTAL QUESTION: Does the medium organize from its own balanced internal
dynamics, or only under externally imposed injection?

SETUP:
1. Seed once with balanced +/- structure
2. No ongoing injection after startup
3. Let it evolve freely

MEASURE:
- Does structure persist?
- Does it oscillate?
- Do the same regimes appear?
- Is there a natural timescale without forced resets?
- Does balance maintain itself?

OUTCOMES:
- Structure persists → Internal balance sustains organization
- Structure forms then decays → Balance can generate, but not sustain
- No meaningful organization → Model depends on external forcing
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from typing import Dict, List
import json


class NoInjectionSimulator:
    """
    Simulator with NO ongoing injection — tests internal balance dynamics.
    """
    
    def __init__(self, size: int = 48):
        self.size = size
        
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
    
    def inject_vortex(self, cx: int, cy: int, chirality: int = 1):
        """Used only for initial seeding."""
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * chirality * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def seed_balanced_structure(self, n_pairs: int = 10):
        """
        Seed with balanced +/- vortex pairs.
        This is the ONLY injection — no more after this.
        """
        center = self.size // 2
        seeded = 0
        
        for i in range(n_pairs):
            # Create a +/- pair at random positions
            angle1 = np.random.uniform(0, 2 * np.pi)
            radius1 = np.random.uniform(3, self.size * 0.20)
            cx1 = int(np.clip(center + radius1 * np.cos(angle1), 5, self.size - 5))
            cy1 = int(np.clip(center + radius1 * np.sin(angle1), 5, self.size - 5))
            
            angle2 = angle1 + np.random.uniform(0.5, 1.5)  # Nearby but not identical
            radius2 = np.random.uniform(3, self.size * 0.20)
            cx2 = int(np.clip(center + radius2 * np.cos(angle2), 5, self.size - 5))
            cy2 = int(np.clip(center + radius2 * np.sin(angle2), 5, self.size - 5))
            
            self.inject_vortex(cx1, cy1, +1)
            self.inject_vortex(cx2, cy2, -1)
            seeded += 2
        
        return seeded
    
    def step(self, dt: float = 0.04):
        """Evolution step — NO INJECTION."""
        self.step_count += 1
        
        # NO INJECTION HERE — this is the key difference
        
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
    
    def detect_defects_with_sign(self, threshold: float = 0.4) -> Dict:
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
        defects = self.detect_defects_with_sign()
        
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        total_energy = float(np.sum(energy))
        
        dissipation = self.gamma * (self.psi_r_dot**2 + self.psi_i_dot**2)
        total_dissipation = float(np.sum(dissipation))
        
        # Balance ratio
        n_pos = defects['n_pos']
        n_neg = defects['n_neg']
        if n_pos + n_neg > 0:
            balance = min(n_pos, n_neg) / (max(n_pos, n_neg) + 1e-10)
        else:
            balance = 1.0
        
        return {
            'step': self.step_count,
            'n_total': defects['n_total'],
            'n_pos': n_pos,
            'n_neg': n_neg,
            'balance': float(balance),
            'total_energy': total_energy,
            'total_dissipation': total_dissipation,
            'channel_mean': float(np.mean(self.channel_assignment)),
            'remnant_mean': float(np.mean(self.remnant_field)),
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
        }


def run_no_injection_test():
    """
    Test whether the medium organizes from internal balance dynamics.
    """
    print("=" * 80)
    print("  NO-INJECTION BALANCED EVOLUTION TEST")
    print("=" * 80)
    print()
    print("Question: Does the medium organize from its own balanced internal")
    print("          dynamics, or only under externally imposed injection?")
    print()
    print("Setup:")
    print("  - Seed once with 10 balanced +/- vortex pairs")
    print("  - NO ongoing injection")
    print("  - Evolve for 2000 steps")
    print()
    
    sim = NoInjectionSimulator(size=48)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Seed with balanced structure
    seeded = sim.seed_balanced_structure(n_pairs=10)
    print(f"Seeded {seeded} vortices (10 +/- pairs)")
    print()
    
    history = []
    
    print(f"{'Step':>5} │ {'N':>4} │ {'+':>3} {'-':>3} │ {'Balance':>7} │ "
          f"{'Energy':>10} │ {'Dissip':>8} │ {'Channel':>7}")
    print("-" * 75)
    
    for step in range(2000):
        sim.step()
        
        if step % 50 == 0:
            state = sim.compute_state()
            history.append(state)
            
            if step % 100 == 0:
                print(f"{step:>5} │ {state['n_total']:>4} │ "
                      f"{state['n_pos']:>3} {state['n_neg']:>3} │ "
                      f"{state['balance']:>7.3f} │ {state['total_energy']:>10.1f} │ "
                      f"{state['total_dissipation']:>8.3f} │ {state['channel_mean']:>7.4f}")
    
    # === ANALYSIS ===
    print()
    print("=" * 80)
    print("EVOLUTION ANALYSIS")
    print("=" * 80)
    
    # Check if structure persists
    initial_n = history[0]['n_total'] if history else 0
    final_n = history[-1]['n_total'] if history else 0
    
    print()
    print(f"Initial defect count: {initial_n}")
    print(f"Final defect count:   {final_n}")
    
    # Track when structure disappears (if it does)
    extinction_step = None
    for h in history:
        if h['n_total'] == 0 and extinction_step is None:
            extinction_step = h['step']
    
    if extinction_step:
        print(f"Structure extinction at step: {extinction_step}")
    else:
        print("Structure persists throughout (no extinction)")
    
    # Check balance maintenance
    print()
    print("Balance over time:")
    early_balance = np.mean([h['balance'] for h in history[:10]])
    late_balance = np.mean([h['balance'] for h in history[-10:]])
    print(f"  Early (steps 0-500):    {early_balance:.3f}")
    print(f"  Late (steps 1500-2000): {late_balance:.3f}")
    
    # Energy decay
    print()
    print("Energy decay:")
    early_energy = np.mean([h['total_energy'] for h in history[:10]])
    late_energy = np.mean([h['total_energy'] for h in history[-10:]])
    print(f"  Early: {early_energy:.1f}")
    print(f"  Late:  {late_energy:.1f}")
    print(f"  Decay: {(1 - late_energy/early_energy) * 100:.1f}%")
    
    # Channel/remnant persistence
    print()
    print("Organizational memory persistence:")
    late_channel = np.mean([h['channel_mean'] for h in history[-10:]])
    late_remnant = np.mean([h['remnant_mean'] for h in history[-10:]])
    print(f"  Channel (late): {late_channel:.4f}")
    print(f"  Remnant (late): {late_remnant:.4f}")
    
    # === VERDICT ===
    print()
    print("=" * 80)
    print("NO-INJECTION TEST VERDICT")
    print("=" * 80)
    print()
    
    if final_n > 0 and final_n > initial_n * 0.3:
        print("RESULT: STRUCTURE PERSISTS WITHOUT INJECTION")
        print()
        print("The medium maintains organizational structure from internal")
        print("balance dynamics alone. External injection is not required")
        print("for structure to exist — only for sustained replenishment.")
        verdict = "persists"
    elif final_n > 0:
        print("RESULT: STRUCTURE PARTIALLY PERSISTS")
        print()
        print(f"Structure reduced from {initial_n} to {final_n} defects.")
        print("Internal balance can maintain some organization, but")
        print("ongoing injection may be needed for full scaffold.")
        verdict = "partial"
    elif extinction_step and extinction_step > 500:
        print("RESULT: STRUCTURE FORMS THEN DECAYS")
        print()
        print(f"Structure persisted until step {extinction_step}, then collapsed.")
        print("Internal balance can generate structure temporarily,")
        print("but cannot sustain it indefinitely without energy input.")
        verdict = "decays"
    else:
        print("RESULT: NO MEANINGFUL ORGANIZATION")
        print()
        print("Structure collapsed quickly. The current model depends")
        print("strongly on external forcing for organization.")
        verdict = "collapses"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/no_injection_test_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'no_injection_balanced_evolution',
            'n_pairs_seeded': 10,
            'history': history,
            'initial_n': initial_n,
            'final_n': final_n,
            'extinction_step': extinction_step,
            'verdict': verdict,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, verdict


if __name__ == "__main__":
    history, verdict = run_no_injection_test()
