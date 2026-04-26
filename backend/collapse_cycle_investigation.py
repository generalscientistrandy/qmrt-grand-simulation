"""
Collapse Cycle Investigation
=============================

QUESTION: What causes the scaffold→sparse→scaffold cycles?

Hypotheses:
1. DEPLETION: Driving can't keep up with dissipation → collapse → rebuild
2. OSCILLATION: Inherent attractor between organization and exhaustion
3. GEOMETRY: Overcrowding triggers geometric instability → reset
4. CHANNEL SATURATION: Channel reaches ceiling → protection fails
5. PHASE-LOCKED: Cycles are locked to driving injection rhythm

MEASUREMENTS:
- What happens BEFORE each collapse?
- What triggers the rebuild?
- Is the timing regular (oscillatory) or irregular (event-driven)?
- Do branch activities predict the transition?
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from typing import Dict, List, Tuple
import json


class CollapseCycleSimulator:
    """
    Simulator with detailed tracking for collapse cycle analysis.
    """
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        
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
        
        # Track injections
        self.last_injection_step = 0
        self.total_injections = 0
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        self.radial_distance = r
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
    
    def inject_balanced_vortices(self):
        center = self.size // 2
        for chirality in [+1, +1, -1, -1]:
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy, chirality)
        self.last_injection_step = self.step_count
        self.total_injections += 1
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        if self.step_count % self.injection_interval == 0:
            self.inject_balanced_vortices()
        
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
        
        self._current_topology = topology_norm
        self._current_energy = energy
    
    def detect_defects(self, threshold: float = 0.4) -> int:
        """Count defects."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        count = 0
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                local_vort = vorticity[cx, cy, coords[2][0]]
                if abs(local_vort) > 0.05:
                    count += 1
        
        return count
    
    def compute_state(self) -> Dict:
        """Compute detailed state for collapse analysis."""
        n_defects = self.detect_defects()
        
        # Energy metrics
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        total_energy = float(np.sum(energy))
        kinetic_energy = float(np.sum(0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)))
        
        # Dissipation
        dissipation = self.gamma * (self.psi_r_dot**2 + self.psi_i_dot**2)
        total_dissipation = float(np.sum(dissipation))
        
        # Channel/remnant
        channel_mean = float(np.mean(self.channel_assignment))
        channel_max = float(np.max(self.channel_assignment))
        remnant_mean = float(np.mean(self.remnant_field))
        
        # τ
        tau_mean = float(np.mean(self.tau))
        tau_std = float(np.std(self.tau))
        
        # Time since last injection
        steps_since_injection = self.step_count - self.last_injection_step
        
        # Regime
        if n_defects < 50:
            regime = 'sparse'
        elif n_defects < 150:
            regime = 'building'
        elif n_defects < 250:
            regime = 'scaffold'
        else:
            regime = 'dense'
        
        return {
            'step': self.step_count,
            'n_defects': n_defects,
            'regime': regime,
            'total_energy': total_energy,
            'kinetic_energy': kinetic_energy,
            'total_dissipation': total_dissipation,
            'channel_mean': channel_mean,
            'channel_max': channel_max,
            'remnant_mean': remnant_mean,
            'tau_mean': tau_mean,
            'tau_std': tau_std,
            'steps_since_injection': steps_since_injection,
            'total_injections': self.total_injections,
        }


def run_collapse_investigation():
    """
    Investigate what causes collapse cycles.
    """
    print("=" * 80)
    print("  COLLAPSE CYCLE INVESTIGATION")
    print("=" * 80)
    print()
    print("Question: What causes the scaffold→sparse→scaffold cycles?")
    print()
    print("Hypotheses:")
    print("  1. DEPLETION: Driving can't keep up with dissipation")
    print("  2. OSCILLATION: Inherent attractor dynamics")
    print("  3. GEOMETRY: Overcrowding triggers instability")
    print("  4. CHANNEL SATURATION: Protection ceiling reached")
    print("  5. PHASE-LOCKED: Tied to injection rhythm")
    print()
    
    sim = CollapseCycleSimulator(size=48, injection_interval=80)
    
    np.random.seed(42)
    sim.psi_r += 0.03 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.03 * np.random.randn(48, 48, 48)
    
    # Initial seeding
    center = 24
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) + abs(j) <= 3:
                chirality = 1 if (i + j) % 2 == 0 else -1
                sim.inject_vortex(center + i * 4, center + j * 4, chirality)
    
    # High-resolution tracking
    history = []
    
    print(f"{'Step':>5} │ {'N':>4} │ {'Regime':>8} │ {'Energy':>10} │ "
          f"{'Dissip':>8} │ {'Channel':>7} │ {'SinceInj':>8}")
    print("-" * 75)
    
    for step in range(3000):
        sim.step()
        
        # Track every 20 steps for high resolution
        if step % 20 == 0 and step > 0:
            state = sim.compute_state()
            history.append(state)
            
            if step % 200 == 0:
                print(f"{step:>5} │ {state['n_defects']:>4} │ {state['regime']:>8} │ "
                      f"{state['total_energy']:>10.1f} │ {state['total_dissipation']:>8.3f} │ "
                      f"{state['channel_mean']:>7.4f} │ {state['steps_since_injection']:>8}")
    
    # === COLLAPSE DETECTION ===
    print()
    print("=" * 80)
    print("COLLAPSE EVENT ANALYSIS")
    print("=" * 80)
    
    # Find collapse events (N drops by >50% in 100 steps)
    collapses = []
    for i in range(5, len(history)):
        n_now = history[i]['n_defects']
        n_before = history[i-5]['n_defects']  # 100 steps earlier
        
        if n_before > 100 and n_now < n_before * 0.3:
            collapses.append({
                'step': history[i]['step'],
                'n_before': n_before,
                'n_after': n_now,
                'idx': i,
            })
    
    print()
    print(f"Found {len(collapses)} collapse events (>70% drop in 100 steps):")
    
    for c in collapses:
        print(f"  Step {c['step']}: {c['n_before']} → {c['n_after']} defects")
    
    # === ANALYZE WHAT PRECEDES COLLAPSES ===
    print()
    print("=" * 80)
    print("PRE-COLLAPSE CONDITIONS")
    print("=" * 80)
    
    if collapses:
        print()
        print("Metrics 100 steps BEFORE each collapse:")
        print()
        print(f"{'Collapse':>8} │ {'N':>4} │ {'Energy':>10} │ {'Dissip':>8} │ "
              f"{'Channel':>7} │ {'τ_std':>6} │ {'SinceInj':>8}")
        print("-" * 75)
        
        pre_collapse_data = []
        for c in collapses:
            idx = c['idx']
            if idx >= 5:
                pre = history[idx - 5]  # 100 steps before
                print(f"{c['step']:>8} │ {pre['n_defects']:>4} │ "
                      f"{pre['total_energy']:>10.1f} │ {pre['total_dissipation']:>8.3f} │ "
                      f"{pre['channel_mean']:>7.4f} │ {pre['tau_std']:>6.4f} │ "
                      f"{pre['steps_since_injection']:>8}")
                pre_collapse_data.append(pre)
        
        # Average pre-collapse conditions
        if pre_collapse_data:
            print()
            print("Average pre-collapse conditions:")
            print(f"  N defects:    {np.mean([p['n_defects'] for p in pre_collapse_data]):.1f}")
            print(f"  Energy:       {np.mean([p['total_energy'] for p in pre_collapse_data]):.1f}")
            print(f"  Dissipation:  {np.mean([p['total_dissipation'] for p in pre_collapse_data]):.3f}")
            print(f"  Channel:      {np.mean([p['channel_mean'] for p in pre_collapse_data]):.4f}")
    
    # === REBUILD DETECTION ===
    print()
    print("=" * 80)
    print("REBUILD EVENT ANALYSIS")
    print("=" * 80)
    
    # Find rebuild events (N increases by >100 in 100 steps)
    rebuilds = []
    for i in range(5, len(history)):
        n_now = history[i]['n_defects']
        n_before = history[i-5]['n_defects']
        
        if n_before < 50 and n_now > 150:
            rebuilds.append({
                'step': history[i]['step'],
                'n_before': n_before,
                'n_after': n_now,
                'idx': i,
            })
    
    print()
    print(f"Found {len(rebuilds)} rebuild events (sparse → scaffold in 100 steps):")
    
    for r in rebuilds:
        print(f"  Step {r['step']}: {r['n_before']} → {r['n_after']} defects")
    
    # === TIMING ANALYSIS ===
    print()
    print("=" * 80)
    print("TIMING ANALYSIS")
    print("=" * 80)
    
    # Check if collapses are regular
    if len(collapses) >= 2:
        intervals = []
        for i in range(1, len(collapses)):
            interval = collapses[i]['step'] - collapses[i-1]['step']
            intervals.append(interval)
        
        print()
        print("Collapse intervals:")
        for i, interval in enumerate(intervals):
            print(f"  Collapse {i+1} → {i+2}: {interval} steps")
        
        print()
        print(f"Mean interval: {np.mean(intervals):.1f} steps")
        print(f"Std interval:  {np.std(intervals):.1f} steps")
        print(f"CV (std/mean): {np.std(intervals) / np.mean(intervals):.2f}")
        
        # Is it regular (CV < 0.3)?
        cv = np.std(intervals) / np.mean(intervals)
        if cv < 0.3:
            print()
            print("→ Collapses are REGULAR (oscillatory behavior)")
            timing_pattern = 'oscillatory'
        else:
            print()
            print("→ Collapses are IRREGULAR (event-driven)")
            timing_pattern = 'irregular'
    else:
        timing_pattern = 'insufficient_data'
    
    # === INJECTION CORRELATION ===
    print()
    print("=" * 80)
    print("INJECTION CORRELATION")
    print("=" * 80)
    
    # Check if collapses correlate with injection phase
    if collapses:
        collapse_phases = []
        for c in collapses:
            step = c['step']
            phase_in_cycle = step % sim.injection_interval
            collapse_phases.append(phase_in_cycle)
        
        print()
        print("Collapse timing within injection cycle (interval = 80):")
        for i, phase in enumerate(collapse_phases):
            print(f"  Collapse {i+1}: step {collapses[i]['step']} → phase {phase}/80")
        
        print()
        print(f"Mean phase: {np.mean(collapse_phases):.1f}")
        print(f"Std phase:  {np.std(collapse_phases):.1f}")
        
        # Are collapses phase-locked?
        if np.std(collapse_phases) < 20:
            print("→ Collapses are PHASE-LOCKED to injection")
            phase_locked = True
        else:
            print("→ Collapses are NOT phase-locked")
            phase_locked = False
    else:
        phase_locked = False
    
    # === ENERGY BALANCE ANALYSIS ===
    print()
    print("=" * 80)
    print("ENERGY BALANCE HYPOTHESIS")
    print("=" * 80)
    
    # Track energy input vs dissipation
    if len(history) > 10:
        # Compare energy at different times
        early_energy = np.mean([h['total_energy'] for h in history[:10]])
        late_energy = np.mean([h['total_energy'] for h in history[-10:]])
        
        early_dissip = np.mean([h['total_dissipation'] for h in history[:10]])
        late_dissip = np.mean([h['total_dissipation'] for h in history[-10:]])
        
        print()
        print(f"Energy:      Early = {early_energy:.1f}, Late = {late_energy:.1f}")
        print(f"Dissipation: Early = {early_dissip:.3f}, Late = {late_dissip:.3f}")
        
        if late_dissip > early_dissip * 1.5:
            print()
            print("→ Dissipation INCREASES over time")
            print("→ Collapses may be DEPLETION events (dissipation > input)")
        else:
            print()
            print("→ Dissipation is STABLE")
            print("→ Collapses are likely NOT depletion-driven")
    
    # === VERDICT ===
    print()
    print("=" * 80)
    print("COLLAPSE CYCLE VERDICT")
    print("=" * 80)
    print()
    
    print("Evidence summary:")
    print(f"  - Timing pattern: {timing_pattern}")
    print(f"  - Phase-locked to injection: {phase_locked}")
    print(f"  - Number of collapses: {len(collapses)}")
    print(f"  - Number of rebuilds: {len(rebuilds)}")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/collapse_cycle_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'collapse_cycle_investigation',
            'history': history,
            'collapses': collapses,
            'rebuilds': rebuilds,
            'timing_pattern': timing_pattern,
            'phase_locked': phase_locked,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, collapses, rebuilds


if __name__ == "__main__":
    history, collapses, rebuilds = run_collapse_investigation()
