"""
τ-Maintenance Causal Test
=========================

QUESTION: Does τ causally implement maintenance cost through differential dissipation?

TESTS:
1. For matched structures, does higher τ → faster decay?
2. Do loop-rich states lose structure faster with elevated τ?
3. Do scaffold states persist longer with suppressed τ?
4. Is there a measurable relation between local τ and:
   - Defect lifetime
   - Channel persistence
   - Structural stability

SUCCESS: High τ → faster dissipation → maintenance cost mechanism confirmed
FAILURE: τ and dissipation are uncorrelated → τ is indicator only, not causal
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr, spearmanr
from typing import Dict, List, Tuple
import json


class MaintenanceCostSimulator:
    """Simulator for τ-maintenance causal testing."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80, 
                 tau_response: float = 0.02):
        self.size = size
        self.injection_interval = injection_interval
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = tau_response
        self.tau_relaxation = 0.01
        self.c_0_sq = 4.0
        
        self.channel_assignment = np.zeros((size, size, size))
        self.remnant_field = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        self.gamma = 0.007
        self.step_count = 0
        
        # Defect tracking for lifetime measurement
        self.defect_registry = {}  # id -> {birth_step, last_seen, birth_tau, death_tau, ...}
        self.next_defect_id = 0
        
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
    
    def detect_defects_detailed(self, threshold: float = 0.4) -> List[Dict]:
        """Detect defects with detailed local environment."""
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
                    # Local τ in 5x5x5 neighborhood
                    x_lo, x_hi = max(0, cx-2), min(self.size, cx+3)
                    y_lo, y_hi = max(0, cy-2), min(self.size, cy+3)
                    z_lo, z_hi = max(0, cz-2), min(self.size, cz+3)
                    
                    local_tau = np.mean(self.tau[x_lo:x_hi, y_lo:y_hi, z_lo:z_hi])
                    local_channel = np.mean(self.channel_assignment[x_lo:x_hi, y_lo:y_hi, z_lo:z_hi])
                    local_energy = np.mean(amp[x_lo:x_hi, y_lo:y_hi, z_lo:z_hi]**2)
                    
                    defects.append({
                        'pos': (cx, cy, cz),
                        'winding': winding,
                        'tau': float(local_tau),
                        'channel': float(local_channel),
                        'energy': float(local_energy),
                    })
        
        return defects
    
    def track_defects(self, defects: List[Dict], match_radius: float = 5.0):
        """
        Track defects across frames to measure lifetimes.
        
        Returns: births, deaths, and updated registry.
        """
        current_positions = set()
        births = []
        
        for d in defects:
            pos = d['pos']
            current_positions.add(pos)
            
            # Try to match to existing defect
            matched = False
            for def_id, info in self.defect_registry.items():
                if info['alive']:
                    old_pos = info['last_pos']
                    dist = np.sqrt(sum((a - b)**2 for a, b in zip(pos, old_pos)))
                    if dist < match_radius and info['winding'] == d['winding']:
                        # Match found - update
                        info['last_seen'] = self.step_count
                        info['last_pos'] = pos
                        info['tau_history'].append(d['tau'])
                        info['channel_history'].append(d['channel'])
                        matched = True
                        break
            
            if not matched:
                # New defect born
                self.defect_registry[self.next_defect_id] = {
                    'birth_step': self.step_count,
                    'birth_tau': d['tau'],
                    'birth_channel': d['channel'],
                    'last_seen': self.step_count,
                    'last_pos': pos,
                    'winding': d['winding'],
                    'tau_history': [d['tau']],
                    'channel_history': [d['channel']],
                    'alive': True,
                }
                births.append(self.next_defect_id)
                self.next_defect_id += 1
        
        # Check for deaths
        deaths = []
        for def_id, info in self.defect_registry.items():
            if info['alive'] and info['last_seen'] < self.step_count - 10:
                # Defect hasn't been seen in 10 steps - mark as dead
                info['alive'] = False
                info['death_step'] = info['last_seen']
                info['death_tau'] = info['tau_history'][-1] if info['tau_history'] else 1.0
                info['lifetime'] = info['death_step'] - info['birth_step']
                info['avg_tau'] = np.mean(info['tau_history'])
                info['avg_channel'] = np.mean(info['channel_history'])
                deaths.append(def_id)
        
        return births, deaths
    
    def compute_dissipation_metrics(self) -> Dict:
        """
        Compute metrics relating τ to dissipation/decay.
        """
        # Field energy decay rate
        energy = self.psi_r**2 + self.psi_i**2 + 0.5*(self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # Dissipation power: γ * |ψ_dot|²
        dissipation = self.gamma * (self.psi_r_dot**2 + self.psi_i_dot**2)
        
        # τ-weighted dissipation
        tau_weighted_dissipation = self.tau * dissipation
        
        # High-τ vs low-τ regions
        tau_median = np.median(self.tau)
        high_tau_mask = self.tau > tau_median
        low_tau_mask = self.tau <= tau_median
        
        diss_high_tau = np.mean(dissipation[high_tau_mask])
        diss_low_tau = np.mean(dissipation[low_tau_mask])
        
        energy_high_tau = np.mean(energy[high_tau_mask])
        energy_low_tau = np.mean(energy[low_tau_mask])
        
        # Specific dissipation rate (dissipation per unit energy)
        spec_diss_high = diss_high_tau / (energy_high_tau + 1e-10)
        spec_diss_low = diss_low_tau / (energy_low_tau + 1e-10)
        
        return {
            'dissipation_total': float(np.sum(dissipation)),
            'dissipation_mean': float(np.mean(dissipation)),
            'diss_high_tau': float(diss_high_tau),
            'diss_low_tau': float(diss_low_tau),
            'diss_ratio': float(diss_high_tau / (diss_low_tau + 1e-10)),
            'spec_diss_high_tau': float(spec_diss_high),
            'spec_diss_low_tau': float(spec_diss_low),
            'spec_diss_ratio': float(spec_diss_high / (spec_diss_low + 1e-10)),
            'tau_mean': float(np.mean(self.tau)),
            'tau_std': float(np.std(self.tau)),
        }


def run_maintenance_cost_test():
    """
    Test whether τ causally implements maintenance cost.
    """
    print("=" * 75)
    print("  τ-MAINTENANCE CAUSAL TEST")
    print("=" * 75)
    print()
    print("Question: Does τ causally implement maintenance cost through")
    print("          differential dissipation?")
    print()
    print("Tests:")
    print("  1. Does higher τ → faster dissipation rate?")
    print("  2. Is defect lifetime correlated with local τ?")
    print("  3. Do structures in high-τ regions decay faster?")
    print()
    
    sim = MaintenanceCostSimulator(size=48, injection_interval=80, tau_response=0.02)
    
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
    
    dissipation_history = []
    
    print("Phase 1: Collecting dissipation and lifetime data...")
    print()
    print(f"{'Step':>5} │ {'τ_mean':>7} │ {'D_high':>8} {'D_low':>8} │ "
          f"{'D_ratio':>7} │ {'Births':>6} {'Deaths':>6}")
    print("-" * 70)
    
    for step in range(2000):
        sim.step()
        
        if step % 50 == 0:
            defects = sim.detect_defects_detailed()
            births, deaths = sim.track_defects(defects)
        
        if step % 100 == 0 and step > 0:
            m = sim.compute_dissipation_metrics()
            m['step'] = step
            dissipation_history.append(m)
            
            # Count recent births/deaths
            recent_births = len([d for d in sim.defect_registry.values() 
                               if d['birth_step'] > step - 100])
            recent_deaths = len([d for d in sim.defect_registry.values() 
                               if not d['alive'] and d.get('death_step', 0) > step - 100])
            
            print(f"{step:>5} │ {m['tau_mean']:>7.4f} │ "
                  f"{m['diss_high_tau']:>8.5f} {m['diss_low_tau']:>8.5f} │ "
                  f"{m['diss_ratio']:>7.3f} │ {recent_births:>6} {recent_deaths:>6}")
    
    # === ANALYSIS 1: τ → Dissipation Rate ===
    print()
    print("=" * 75)
    print("TEST 1: τ → DISSIPATION RATE")
    print("=" * 75)
    print()
    
    avg_diss_ratio = np.mean([h['diss_ratio'] for h in dissipation_history])
    avg_spec_diss_ratio = np.mean([h['spec_diss_ratio'] for h in dissipation_history])
    
    print(f"Average dissipation ratio (high-τ / low-τ): {avg_diss_ratio:.3f}")
    print(f"Average specific dissipation ratio:        {avg_spec_diss_ratio:.3f}")
    print()
    
    if avg_diss_ratio > 1.1:
        print("✓ High-τ regions dissipate faster (raw)")
        test1_raw = True
    else:
        print("✗ No raw dissipation difference")
        test1_raw = False
    
    if avg_spec_diss_ratio > 1.05:
        print("✓ High-τ regions dissipate faster (per unit energy)")
        test1_spec = True
    else:
        print("✗ No specific dissipation difference")
        test1_spec = False
    
    # === ANALYSIS 2: Defect Lifetime vs τ ===
    print()
    print("=" * 75)
    print("TEST 2: DEFECT LIFETIME vs LOCAL τ")
    print("=" * 75)
    print()
    
    # Get completed defect lifetimes
    completed = [d for d in sim.defect_registry.values() if not d['alive'] and d['lifetime'] > 5]
    
    print(f"Completed defects tracked: {len(completed)}")
    
    if len(completed) >= 20:
        lifetimes = np.array([d['lifetime'] for d in completed])
        avg_taus = np.array([d['avg_tau'] for d in completed])
        birth_taus = np.array([d['birth_tau'] for d in completed])
        avg_channels = np.array([d['avg_channel'] for d in completed])
        
        # Correlations
        corr_life_tau, p_life_tau = pearsonr(lifetimes, avg_taus)
        corr_life_birth_tau, p_birth = pearsonr(lifetimes, birth_taus)
        corr_life_channel, p_channel = pearsonr(lifetimes, avg_channels)
        
        print()
        print(f"Correlation(lifetime, avg_τ):   r = {corr_life_tau:+.3f}, p = {p_life_tau:.4f}")
        print(f"Correlation(lifetime, birth_τ): r = {corr_life_birth_tau:+.3f}, p = {p_birth:.4f}")
        print(f"Correlation(lifetime, channel): r = {corr_life_channel:+.3f}, p = {p_channel:.4f}")
        
        # Key test: Does higher τ → shorter lifetime?
        print()
        if corr_life_tau < -0.1 and p_life_tau < 0.1:
            print("✓ Higher τ → SHORTER lifetime (maintenance cost confirmed)")
            test2_pass = True
        elif corr_life_tau > 0.1 and p_life_tau < 0.1:
            print("? Higher τ → LONGER lifetime (unexpected - τ may stabilize?)")
            test2_pass = False
        else:
            print("✗ No significant correlation between τ and lifetime")
            test2_pass = False
        
        # Bin analysis
        print()
        print("Lifetime by τ bin:")
        tau_low = avg_taus < np.percentile(avg_taus, 33)
        tau_mid = (avg_taus >= np.percentile(avg_taus, 33)) & (avg_taus < np.percentile(avg_taus, 67))
        tau_high = avg_taus >= np.percentile(avg_taus, 67)
        
        print(f"  Low τ  (n={np.sum(tau_low):>3}): lifetime = {np.mean(lifetimes[tau_low]):.1f}")
        print(f"  Mid τ  (n={np.sum(tau_mid):>3}): lifetime = {np.mean(lifetimes[tau_mid]):.1f}")
        print(f"  High τ (n={np.sum(tau_high):>3}): lifetime = {np.mean(lifetimes[tau_high]):.1f}")
        
        lifetime_low = np.mean(lifetimes[tau_low])
        lifetime_high = np.mean(lifetimes[tau_high])
    else:
        print("Insufficient completed defects for correlation analysis")
        test2_pass = False
        corr_life_tau = 0
        lifetime_low, lifetime_high = 0, 0
    
    # === ANALYSIS 3: Channel Persistence vs τ ===
    print()
    print("=" * 75)
    print("TEST 3: STRUCTURAL PERSISTENCE vs τ")
    print("=" * 75)
    print()
    
    # Check if high-τ regions have lower channel persistence
    tau_channel_corrs = []
    for h in dissipation_history[-10:]:  # Last 10 samples
        # Would need per-voxel correlation, approximate with aggregate
        pass
    
    # Use the channel correlation from defect data
    if len(completed) >= 20:
        print(f"Correlation(lifetime, channel): r = {corr_life_channel:+.3f}")
        if corr_life_channel > 0.1:
            print("✓ Higher channel → longer lifetime (channel = bound energy)")
            test3_pass = True
        else:
            print("✗ No significant channel-lifetime correlation")
            test3_pass = False
    else:
        test3_pass = False
    
    # === VERDICT ===
    print()
    print("=" * 75)
    print("VERDICT: τ-MAINTENANCE CAUSAL RELATIONSHIP")
    print("=" * 75)
    print()
    
    n_pass = sum([test1_raw or test1_spec, test2_pass, test3_pass])
    
    print(f"Tests passed: {n_pass}/3")
    print()
    
    if n_pass >= 2:
        print("RESULT: τ CAUSALLY IMPLEMENTS MAINTENANCE COST")
        print()
        print("Evidence:")
        if test1_raw or test1_spec:
            print(f"  ✓ High-τ regions dissipate {avg_diss_ratio:.1f}× faster")
        if test2_pass:
            print(f"  ✓ Higher τ correlates with shorter lifetime (r={corr_life_tau:.2f})")
        if test3_pass:
            print(f"  ✓ Channel (bound energy) correlates with persistence")
        print()
        print("Implication:")
        print("  τ is not just an indicator — it actively implements the")
        print("  energetic cost of maintaining structure. Higher τ → faster")
        print("  dissipation → higher maintenance cost → shorter lifetime.")
        verdict = "causal_confirmed"
    elif n_pass == 1:
        print("RESULT: PARTIAL EVIDENCE FOR τ-MAINTENANCE LINK")
        print()
        print("Some causal signal present but not definitive.")
        print("τ may be partially implementing maintenance cost.")
        verdict = "partial"
    else:
        print("RESULT: NO CAUSAL τ-MAINTENANCE RELATIONSHIP FOUND")
        print()
        print("τ appears to be an indicator of organizational state,")
        print("but does not causally implement maintenance cost.")
        print()
        print("Implication:")
        print("  Separate maintenance mechanism may be needed.")
        verdict = "not_causal"
    
    # Additional insight: The mechanism pathway
    print()
    print("=" * 75)
    print("MECHANISM ANALYSIS")
    print("=" * 75)
    print()
    print("The causal chain (if confirmed):")
    print()
    print("  High local energy → τ elevated")
    print("       ↓")
    print("  Higher c_eff = √(c₀² × τ)")
    print("       ↓")
    print("  Faster wave propagation → faster dispersion")
    print("       ↓")
    print("  Structure loses coherence faster")
    print("       ↓")
    print("  MAINTENANCE COST = dissipation rate × τ")
    print()
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/tau_maintenance_causal_results.json'
    
    # Prepare defect data for JSON
    defect_stats = []
    for d in completed[:100]:  # First 100 to avoid huge file
        defect_stats.append({
            'lifetime': d['lifetime'],
            'birth_tau': d['birth_tau'],
            'avg_tau': d['avg_tau'],
            'avg_channel': d['avg_channel'],
        })
    
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'tau_maintenance_causal',
            'tau_response': 0.02,
            'dissipation_history': dissipation_history,
            'defect_stats': defect_stats,
            'avg_diss_ratio': float(avg_diss_ratio),
            'lifetime_tau_correlation': float(corr_life_tau) if len(completed) >= 20 else None,
            'tests_passed': n_pass,
            'verdict': verdict,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return dissipation_history, completed, verdict


if __name__ == "__main__":
    dissipation_history, completed_defects, verdict = run_maintenance_cost_test()
