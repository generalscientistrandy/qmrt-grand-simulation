"""
Regime Transition Branch Audit
==============================

PURPOSE: Map branch activity through the loop→clustering transition.

Not just "does the transition happen," but:
- Which branch turns on first?
- Which branch changes sign or role?
- Which branch saturates?
- Does τ lead or follow the transition?
- Do channel/remnant stabilize after geometry sorts?

This is the first true branch interaction study.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from typing import Dict, List, Tuple
import json


class BranchAuditSimulator:
    """
    Full simulator with comprehensive branch activity tracking.
    """
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02  # Amplified baseline
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
        # Branch activity tracking
        self.branch_history = []
        
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
        
        self.interior_mask = mask_interior
        self.exterior_mask = mask_exterior
        
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
        
        # Store current topology for branch audit
        self._current_topology = topology_norm
        self._current_energy = energy
    
    def detect_defects(self, threshold: float = 0.4) -> List[Dict]:
        """Detect defects with full context."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        vorticity = (np.roll(grad_y, -1, axis=0) - grad_y) - (np.roll(grad_x, -1, axis=1) - grad_x)
        
        labeled, n = label(amp < threshold)
        defects = []
        
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                cx = int(np.mean(coords[0]))
                cy = int(np.mean(coords[1]))
                cz = int(np.mean(coords[2]))
                
                local_vort = vorticity[cx, cy, cz]
                winding = 0
                if local_vort > 0.05:
                    winding = +1
                elif local_vort < -0.05:
                    winding = -1
                
                if winding != 0:
                    defects.append({
                        'pos': (cx, cy, cz),
                        'winding': winding,
                        'radial': float(self.radial_distance[cx, cy, cz]),
                    })
        
        return defects
    
    def compute_branch_activity(self) -> Dict:
        """
        Compute activity level for each branch.
        
        Returns metrics that indicate how "active" each branch is.
        """
        defects = self.detect_defects()
        n_defects = len(defects)
        
        # === CREATION BRANCH ===
        # Activity: number of defects created (proxy: current population)
        creation_activity = n_defects
        
        # === BALANCE BRANCH ===
        # Activity: how balanced are +/- populations
        n_pos = sum(1 for d in defects if d['winding'] == +1)
        n_neg = sum(1 for d in defects if d['winding'] == -1)
        if n_defects > 0:
            balance_ratio = min(n_pos, n_neg) / (max(n_pos, n_neg) + 1e-10)
        else:
            balance_ratio = 1.0
        
        # === GEOMETRY BRANCH ===
        # Activity: how concentrated are defects in interior vs exterior
        if n_defects > 0:
            interior_frac = sum(1 for d in defects if d['radial'] < self.size * 0.25) / n_defects
        else:
            interior_frac = 0.5
        geometry_activity = abs(interior_frac - 0.5) * 2  # 0 = uniform, 1 = all interior or exterior
        
        # === τ ACCOUNTING BRANCH ===
        # Activity: τ variance (how differentiated is τ)
        tau_activity = float(np.std(self.tau))
        tau_mean = float(np.mean(self.tau))
        
        # τ in high-topology vs low-topology
        if hasattr(self, '_current_topology'):
            topo = self._current_topology
            high_topo = topo > np.percentile(topo, 90)
            low_topo = topo < np.percentile(topo, 10)
            tau_high_topo = float(np.mean(self.tau[high_topo])) if np.any(high_topo) else 1.0
            tau_low_topo = float(np.mean(self.tau[low_topo])) if np.any(low_topo) else 1.0
            tau_differentiation = tau_high_topo - tau_low_topo
        else:
            tau_differentiation = 0
        
        # === CHANNEL BRANCH ===
        # Activity: channel accumulation level
        channel_activity = float(np.mean(self.channel_assignment))
        channel_high_frac = float(np.mean(self.channel_assignment > 0.5))
        
        # === REMNANT BRANCH ===
        # Activity: remnant accumulation level
        remnant_activity = float(np.mean(self.remnant_field))
        remnant_max = float(np.max(self.remnant_field))
        
        # === DAMPING BRANCH ===
        # Activity: dissipation rate
        dissipation = self.gamma * (self.psi_r_dot**2 + self.psi_i_dot**2)
        damping_activity = float(np.mean(dissipation))
        
        # === WAVE BRANCH ===
        # Activity: kinetic energy level
        wave_activity = float(np.mean(self.psi_r_dot**2 + self.psi_i_dot**2))
        
        # === REGIME CLASSIFICATION ===
        # Based on defect count and clustering
        if n_defects < 50:
            regime = 'sparse'
        elif n_defects < 150:
            # Check clustering via nearest-neighbor distance
            if n_defects >= 2:
                positions = np.array([d['pos'] for d in defects])
                nn_dists = []
                for i, p in enumerate(positions):
                    dists = np.sqrt(np.sum((positions - p)**2, axis=1))
                    dists[i] = np.inf
                    nn_dists.append(np.min(dists))
                avg_nn = np.mean(nn_dists)
            else:
                avg_nn = self.size
            
            if avg_nn > 5:
                regime = 'loop_dominated'
            else:
                regime = 'transition'
        else:
            if remnant_activity > 0.3:
                regime = 'scaffold'
            else:
                regime = 'clustering'
        
        return {
            'step': self.step_count,
            'regime': regime,
            'n_defects': n_defects,
            
            # Branch activities
            'creation': creation_activity,
            'balance': float(balance_ratio),
            'geometry': float(geometry_activity),
            'tau_activity': tau_activity,
            'tau_mean': tau_mean,
            'tau_differentiation': tau_differentiation,
            'channel': channel_activity,
            'channel_high_frac': channel_high_frac,
            'remnant': remnant_activity,
            'remnant_max': remnant_max,
            'damping': damping_activity,
            'wave': wave_activity,
            
            # Additional context
            'interior_frac': float(interior_frac) if n_defects > 0 else 0.5,
            'n_pos': n_pos,
            'n_neg': n_neg,
        }


def run_branch_audit():
    """
    Run the regime transition branch audit.
    """
    print("=" * 80)
    print("  REGIME TRANSITION BRANCH AUDIT")
    print("=" * 80)
    print()
    print("Purpose: Map branch activity through the loop→clustering transition.")
    print()
    print("Questions to answer:")
    print("  - Which branch turns on first?")
    print("  - Which branch changes during transition?")
    print("  - Does τ lead or follow the transition?")
    print("  - Do channel/remnant stabilize after geometry sorts?")
    print()
    
    sim = BranchAuditSimulator(size=48, injection_interval=80)
    
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
    
    history = []
    
    print(f"{'Step':>5} │ {'Regime':>12} │ {'N':>4} │ "
          f"{'τ_diff':>7} │ {'Chan':>6} │ {'Remn':>6} │ {'Geom':>5}")
    print("-" * 70)
    
    for step in range(2500):
        sim.step()
        
        if step % 50 == 0 and step > 0:
            activity = sim.compute_branch_activity()
            history.append(activity)
            
            if step % 100 == 0:
                print(f"{step:>5} │ {activity['regime']:>12} │ {activity['n_defects']:>4} │ "
                      f"{activity['tau_differentiation']:>+7.4f} │ "
                      f"{activity['channel']:>6.4f} │ {activity['remnant']:>6.4f} │ "
                      f"{activity['geometry']:>5.3f}")
    
    # === REGIME TRANSITION ANALYSIS ===
    print()
    print("=" * 80)
    print("REGIME TRANSITION ANALYSIS")
    print("=" * 80)
    
    # Find transition points
    transitions = []
    for i in range(1, len(history)):
        if history[i]['regime'] != history[i-1]['regime']:
            transitions.append({
                'step': history[i]['step'],
                'from': history[i-1]['regime'],
                'to': history[i]['regime'],
                'idx': i,
            })
    
    print()
    print(f"Found {len(transitions)} regime transitions:")
    for t in transitions:
        print(f"  Step {t['step']}: {t['from']} → {t['to']}")
    
    # === BRANCH ACTIVITY BY REGIME ===
    print()
    print("=" * 80)
    print("BRANCH ACTIVITY BY REGIME")
    print("=" * 80)
    
    regimes = {}
    for h in history:
        r = h['regime']
        if r not in regimes:
            regimes[r] = []
        regimes[r].append(h)
    
    print()
    print(f"{'Regime':>15} │ {'N':>5} │ {'τ_diff':>8} │ {'Channel':>8} │ "
          f"{'Remnant':>8} │ {'Geom':>6} │ {'Balance':>7}")
    print("-" * 80)
    
    for regime in ['sparse', 'loop_dominated', 'transition', 'clustering', 'scaffold']:
        if regime in regimes:
            samples = regimes[regime]
            n = np.mean([s['n_defects'] for s in samples])
            tau_diff = np.mean([s['tau_differentiation'] for s in samples])
            channel = np.mean([s['channel'] for s in samples])
            remnant = np.mean([s['remnant'] for s in samples])
            geom = np.mean([s['geometry'] for s in samples])
            balance = np.mean([s['balance'] for s in samples])
            
            print(f"{regime:>15} │ {n:>5.0f} │ {tau_diff:>+8.4f} │ {channel:>8.4f} │ "
                  f"{remnant:>8.4f} │ {geom:>6.3f} │ {balance:>7.3f}")
    
    # === BRANCH ORDERING ANALYSIS ===
    print()
    print("=" * 80)
    print("BRANCH ORDERING: Which turns on first?")
    print("=" * 80)
    
    # Find when each branch first exceeds threshold
    branch_onset = {}
    
    thresholds = {
        'tau_differentiation': 0.01,
        'channel': 0.05,
        'remnant': 0.1,
        'geometry': 0.2,
    }
    
    for branch, thresh in thresholds.items():
        for h in history:
            if h[branch] > thresh:
                branch_onset[branch] = h['step']
                break
    
    print()
    print("Branch onset order (when first exceeds threshold):")
    for branch, step in sorted(branch_onset.items(), key=lambda x: x[1]):
        print(f"  Step {step:>4}: {branch}")
    
    # === τ LEAD/LAG ANALYSIS ===
    print()
    print("=" * 80)
    print("τ LEAD/LAG ANALYSIS")
    print("=" * 80)
    
    # Does τ change BEFORE or AFTER regime transition?
    for t in transitions:
        idx = t['idx']
        if idx >= 3 and idx < len(history) - 3:
            # τ differentiation before and after transition
            tau_before = np.mean([history[idx-3+j]['tau_differentiation'] for j in range(3)])
            tau_after = np.mean([history[idx+j]['tau_differentiation'] for j in range(3)])
            
            # N defects before and after
            n_before = np.mean([history[idx-3+j]['n_defects'] for j in range(3)])
            n_after = np.mean([history[idx+j]['n_defects'] for j in range(3)])
            
            print()
            print(f"Transition: {t['from']} → {t['to']} (step {t['step']})")
            print(f"  τ_diff: {tau_before:+.4f} → {tau_after:+.4f} (Δ = {tau_after - tau_before:+.4f})")
            print(f"  N:      {n_before:.0f} → {n_after:.0f}")
            
            # Check if τ changed first
            tau_change = tau_after - tau_before
            if abs(tau_change) > 0.005:
                # Check 2 steps before transition
                tau_pre = history[idx-2]['tau_differentiation'] if idx >= 2 else tau_before
                if abs(tau_pre - tau_before) > 0.003:
                    print(f"  → τ LEADS (changed before transition)")
                else:
                    print(f"  → τ FOLLOWS (changed after transition)")
            else:
                print(f"  → τ UNCHANGED through transition")
    
    # === CHANNEL/REMNANT STABILIZATION ===
    print()
    print("=" * 80)
    print("CHANNEL/REMNANT STABILIZATION")
    print("=" * 80)
    
    # Does channel/remnant stabilize in later regimes?
    if 'clustering' in regimes and 'loop_dominated' in regimes:
        loop_chan_var = np.std([s['channel'] for s in regimes['loop_dominated']])
        clust_chan_var = np.std([s['channel'] for s in regimes['clustering']])
        
        loop_remn_var = np.std([s['remnant'] for s in regimes['loop_dominated']])
        clust_remn_var = np.std([s['remnant'] for s in regimes['clustering']])
        
        print()
        print("Variance comparison (loop vs clustering):")
        print(f"  Channel: {loop_chan_var:.5f} → {clust_chan_var:.5f} "
              f"({'stabilizes' if clust_chan_var < loop_chan_var else 'destabilizes'})")
        print(f"  Remnant: {loop_remn_var:.5f} → {clust_remn_var:.5f} "
              f"({'stabilizes' if clust_remn_var < loop_remn_var else 'destabilizes'})")
    
    # === SUMMARY ===
    print()
    print("=" * 80)
    print("BRANCH AUDIT SUMMARY")
    print("=" * 80)
    print()
    
    print("Branch activation order:")
    for i, (branch, step) in enumerate(sorted(branch_onset.items(), key=lambda x: x[1])):
        print(f"  {i+1}. {branch} (step {step})")
    
    print()
    print("Key findings:")
    
    # Determine key insights
    if 'tau_differentiation' in branch_onset and 'channel' in branch_onset:
        if branch_onset['tau_differentiation'] < branch_onset['channel']:
            print("  - τ differentiation activates BEFORE channel accumulation")
        else:
            print("  - Channel accumulation activates BEFORE τ differentiation")
    
    if 'geometry' in branch_onset and 'channel' in branch_onset:
        if branch_onset['geometry'] < branch_onset['channel']:
            print("  - Geometry sorting activates BEFORE channel stabilization")
        else:
            print("  - Channel stabilization activates BEFORE geometry sorting")
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/branch_audit_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'regime_transition_branch_audit',
            'history': history,
            'transitions': transitions,
            'branch_onset': branch_onset,
            'regimes_observed': list(regimes.keys()),
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, transitions, branch_onset


if __name__ == "__main__":
    history, transitions, branch_onset = run_branch_audit()
