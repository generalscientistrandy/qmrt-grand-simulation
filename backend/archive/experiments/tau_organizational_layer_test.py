"""
τ Organizational Layer Test
============================

QUESTION: Can amplified τ distinguish organizational layers, not just topology?

LAYERS TO DISTINGUISH:
- Loop-dominated regime (low density, sparse defects)
- Transition regime (building toward clustering)
- Clustering-dominated regime (high density, packed defects)
- Scaffold regime (stable network organization)

KEY MEASUREMENTS:
- Mean τ by organizational regime
- τ variance by regime
- τ in loop-rich vs cluster-rich neighborhoods
- Does τ change before/during/after loop→clustering transition?

SUCCESS: τ shows systematic differences across organizational regimes
FAILURE: τ only tracks local topology, blind to organizational role
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from typing import Dict, List, Tuple
import json


class OrganizationalLayerSimulator:
    """Simulator with amplified τ for organizational layer analysis."""
    
    def __init__(self, size: int = 48, injection_interval: int = 80):
        self.size = size
        self.injection_interval = injection_interval
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        
        self.tau = np.ones((size, size, size))
        self.tau_response = 0.02  # AMPLIFIED
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
    
    def detect_defects(self, threshold: float = 0.4) -> List[Dict]:
        """Detect defects with position, winding, and local τ."""
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
                local_tau = self.tau[cx, cy, cz]
                
                winding = 0
                if local_vort > 0.05:
                    winding = +1
                elif local_vort < -0.05:
                    winding = -1
                
                if winding != 0:
                    defects.append({
                        'pos': (cx, cy, cz),
                        'winding': winding,
                        'tau': float(local_tau),
                    })
        
        return defects
    
    def compute_organizational_metrics(self) -> Dict:
        """
        Compute metrics to identify organizational regime.
        
        REGIMES:
        - Loop-dominated: low N, sparse, low channel
        - Transition: medium N, building
        - Clustering: high N, dense, high channel
        - Scaffold: stable N, high remnant
        """
        defects = self.detect_defects()
        n_defects = len(defects)
        
        # Defect τ statistics
        if n_defects > 0:
            defect_taus = [d['tau'] for d in defects]
            tau_at_defects = np.mean(defect_taus)
            tau_std_at_defects = np.std(defect_taus)
        else:
            tau_at_defects = 1.0
            tau_std_at_defects = 0.0
        
        # Bulk τ (away from defects)
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        bulk_mask = amp > 0.6  # Away from defect cores
        tau_bulk = np.mean(self.tau[bulk_mask]) if np.any(bulk_mask) else 1.0
        
        # Channel and remnant (organizational proxies)
        channel_mean = np.mean(self.channel_assignment)
        channel_high_frac = np.mean(self.channel_assignment > 0.5)
        remnant_mean = np.mean(self.remnant_field)
        
        # Clustering proxy: average nearest-neighbor distance
        if n_defects >= 2:
            positions = np.array([d['pos'] for d in defects])
            nn_distances = []
            for i, p in enumerate(positions):
                dists = np.sqrt(np.sum((positions - p)**2, axis=1))
                dists[i] = np.inf
                nn_distances.append(np.min(dists))
            avg_nn_dist = np.mean(nn_distances)
        else:
            avg_nn_dist = self.size  # Max possible
        
        # Regime classification
        if n_defects < 50:
            regime = 'sparse'
        elif n_defects < 150:
            if avg_nn_dist > 5:
                regime = 'loop_dominated'
            else:
                regime = 'transition'
        elif n_defects < 300:
            regime = 'clustering'
        else:
            if remnant_mean > 0.3:
                regime = 'scaffold'
            else:
                regime = 'clustering'
        
        return {
            'n_defects': n_defects,
            'tau_at_defects': float(tau_at_defects),
            'tau_std_at_defects': float(tau_std_at_defects),
            'tau_bulk': float(tau_bulk),
            'tau_defect_bulk_diff': float(tau_at_defects - tau_bulk),
            'tau_global_mean': float(np.mean(self.tau)),
            'tau_global_std': float(np.std(self.tau)),
            'channel_mean': float(channel_mean),
            'channel_high_frac': float(channel_high_frac),
            'remnant_mean': float(remnant_mean),
            'avg_nn_dist': float(avg_nn_dist),
            'regime': regime,
        }


def run_organizational_layer_test():
    """
    Test whether amplified τ distinguishes organizational layers.
    """
    print("=" * 75)
    print("  τ ORGANIZATIONAL LAYER TEST")
    print("=" * 75)
    print()
    print("Question: Can amplified τ distinguish organizational layers,")
    print("          not just topology intensity?")
    print()
    print("Regimes to distinguish:")
    print("  - Sparse/Loop-dominated (low N, sparse defects)")
    print("  - Transition (medium N, building toward clustering)")
    print("  - Clustering (high N, packed defects)")
    print("  - Scaffold (stable N, high organizational memory)")
    print()
    
    sim = OrganizationalLayerSimulator(size=48, injection_interval=80)
    
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
    
    print(f"{'Step':>5} │ {'N':>4} │ {'Regime':>12} │ "
          f"{'τ_defect':>8} {'τ_bulk':>8} │ {'Δτ':>7} │ {'Channel':>7}")
    print("-" * 75)
    
    for step in range(2000):
        sim.step()
        
        if step % 100 == 0 and step > 0:
            m = sim.compute_organizational_metrics()
            m['step'] = step
            history.append(m)
            
            print(f"{step:>5} │ {m['n_defects']:>4} │ {m['regime']:>12} │ "
                  f"{m['tau_at_defects']:>8.4f} {m['tau_bulk']:>8.4f} │ "
                  f"{m['tau_defect_bulk_diff']:>+7.4f} │ {m['channel_mean']:>7.4f}")
    
    # === REGIME ANALYSIS ===
    print()
    print("=" * 75)
    print("REGIME-RESOLVED τ ANALYSIS")
    print("=" * 75)
    
    # Group by regime
    regimes = {}
    for h in history:
        r = h['regime']
        if r not in regimes:
            regimes[r] = []
        regimes[r].append(h)
    
    print()
    print(f"{'Regime':>15} │ {'N_samples':>9} │ {'τ_defect':>9} │ {'τ_bulk':>9} │ "
          f"{'Δτ (d-b)':>9} │ {'Channel':>8}")
    print("-" * 75)
    
    regime_stats = {}
    for regime, samples in sorted(regimes.items()):
        n = len(samples)
        tau_d = np.mean([s['tau_at_defects'] for s in samples])
        tau_b = np.mean([s['tau_bulk'] for s in samples])
        delta = tau_d - tau_b
        chan = np.mean([s['channel_mean'] for s in samples])
        
        print(f"{regime:>15} │ {n:>9} │ {tau_d:>9.4f} │ {tau_b:>9.4f} │ "
              f"{delta:>+9.4f} │ {chan:>8.4f}")
        
        regime_stats[regime] = {
            'n_samples': n,
            'tau_defect': float(tau_d),
            'tau_bulk': float(tau_b),
            'tau_diff': float(delta),
            'channel': float(chan),
        }
    
    # === KEY QUESTION: Does τ differentiate regimes? ===
    print()
    print("=" * 75)
    print("ORGANIZATIONAL DIFFERENTIATION TEST")
    print("=" * 75)
    print()
    
    # Check if τ differs systematically across regimes
    regime_order = ['sparse', 'loop_dominated', 'transition', 'clustering', 'scaffold']
    present_regimes = [r for r in regime_order if r in regime_stats]
    
    if len(present_regimes) >= 2:
        tau_diffs = [regime_stats[r]['tau_diff'] for r in present_regimes]
        tau_defects = [regime_stats[r]['tau_defect'] for r in present_regimes]
        
        print("τ at defects by regime:")
        for r in present_regimes:
            print(f"  {r:>15}: τ_defect = {regime_stats[r]['tau_defect']:.4f}")
        
        print()
        print("τ defect-bulk difference by regime:")
        for r in present_regimes:
            print(f"  {r:>15}: Δτ = {regime_stats[r]['tau_diff']:+.4f}")
        
        # Variance across regimes
        tau_diff_variance = np.var(tau_diffs)
        tau_defect_variance = np.var(tau_defects)
        
        print()
        print(f"τ_defect variance across regimes: {tau_defect_variance:.6f}")
        print(f"Δτ variance across regimes: {tau_diff_variance:.6f}")
    
    # === TEMPORAL ANALYSIS: Does τ lead or lag transitions? ===
    print()
    print("=" * 75)
    print("τ TRANSITION DYNAMICS")
    print("=" * 75)
    print()
    
    # Find regime transitions
    transitions = []
    for i in range(1, len(history)):
        if history[i]['regime'] != history[i-1]['regime']:
            transitions.append({
                'step': history[i]['step'],
                'from': history[i-1]['regime'],
                'to': history[i]['regime'],
                'tau_before': history[i-1]['tau_at_defects'],
                'tau_after': history[i]['tau_at_defects'],
                'delta_tau': history[i]['tau_at_defects'] - history[i-1]['tau_at_defects'],
            })
    
    print(f"Found {len(transitions)} regime transitions:")
    for t in transitions:
        print(f"  Step {t['step']}: {t['from']} → {t['to']}, "
              f"Δτ = {t['delta_tau']:+.4f}")
    
    # === VERDICT ===
    print()
    print("=" * 75)
    print("VERDICT")
    print("=" * 75)
    print()
    
    # Does τ show systematic regime differentiation?
    if len(present_regimes) >= 2:
        # Check if τ differs meaningfully between regimes
        min_tau = min(tau_defects)
        max_tau = max(tau_defects)
        tau_range = max_tau - min_tau
        
        if tau_range > 0.02:  # At least 2% difference between regimes
            print("RESULT: τ DIFFERENTIATES ORGANIZATIONAL REGIMES")
            print()
            print(f"τ at defects ranges from {min_tau:.4f} to {max_tau:.4f}")
            print(f"across organizational regimes (range = {tau_range:.4f})")
            print()
            print("Implication: τ can serve as a primitive multi-layer accountant.")
            print("Higher organizational complexity → different τ response.")
            verdict = "differentiates_regimes"
        else:
            print("RESULT: τ DOES NOT DIFFERENTIATE ORGANIZATIONAL REGIMES")
            print()
            print(f"τ at defects varies only by {tau_range:.4f} across regimes")
            print("This is essentially flat — no organizational layer distinction.")
            print()
            print("Implication: τ only tracks local topology.")
            print("Separate auditors are needed for organizational layers.")
            verdict = "topology_only"
    else:
        print("RESULT: INSUFFICIENT REGIME DATA")
        print()
        print(f"Only {len(present_regimes)} regimes observed.")
        print("Need more diverse organizational states to test differentiation.")
        verdict = "insufficient_data"
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/tau_organizational_layer_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'test': 'tau_organizational_layer',
            'tau_response': 0.02,
            'history': history,
            'regime_stats': regime_stats,
            'transitions': transitions,
            'verdict': verdict,
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_path}")
    
    return history, regime_stats, verdict


if __name__ == "__main__":
    history, regime_stats, verdict = run_organizational_layer_test()
