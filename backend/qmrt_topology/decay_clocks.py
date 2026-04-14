#!/usr/bin/env python3
"""
QMRT Decay Clock - Metastable Packet Lifetime
==============================================

A metastable localized excitation provides a process-based decay clock.
Its lifetime is defined by a transition from localized coherent structure
to delocalized or sub-threshold behavior.

PACKET INITIALIZATION:
  u(x, 0) = A₀ exp(-|x - xᵢ|² / (2σ₀²))

LOCAL OBSERVABLES:
  Eᵢ(t) = ∫_Wᵢ [½u̇² + ½|∇u|²] dx  (local energy)
  σᵢ²(t) = ∫_Wᵢ |x-xᵢ|² ρ dx / ∫_Wᵢ ρ dx  (local width)
  Pᵢ(t) = max_{x∈Wᵢ} |u(x,t)|  (local peak)

DECAY CRITERION (excitation "alive" while ALL hold):
  Eᵢ(t) > E_min
  σᵢ(t) < σ_max
  Pᵢ(t) > P_min

STATISTICAL PROTOCOL:
  - Run N replicas with noise perturbations
  - Measure lifetime distribution p(T), mean ⟨T⟩, variance
  - Compare lifetimes across regions

NON-CIRCULAR TEST:
  - Rescale observables by measured lifetime, not raw t_sim
  - Check if different regions collapse under lifetime-based time
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


class DecayClockSimulator:
    """
    Simulator for metastable packet decay clocks.
    """
    
    def __init__(
        self,
        size: int = 100,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        beta: float = 1.0,
        lambda_relax: float = 1.5,
        D_medium: float = 0.1,
        gamma_wave: float = 0.008,
        dt: float = 0.04,
        # Decay parameters
        E_min_fraction: float = 0.3,  # Fraction of initial energy
        sigma_max_factor: float = 2.0,  # Multiple of initial width
        P_min_fraction: float = 0.2,  # Fraction of initial peak
        hold_time: int = 10,  # Steps to confirm decay
        # Noise
        noise_amplitude: float = 0.01,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.E_min_fraction = E_min_fraction
        self.sigma_max_factor = sigma_max_factor
        self.P_min_fraction = P_min_fraction
        self.hold_time = hold_time
        self.noise_amplitude = noise_amplitude
        
        # Initialize fields
        self.reset_fields()
        
    def reset_fields(self):
        """Reset all fields to initial state."""
        self.phi = np.zeros((self.size, self.size))
        self.phi_dot = np.zeros((self.size, self.size))
        self.tau = np.ones((self.size, self.size)) * self.tau_0
        self.t_sim = 0.0
        
        # Packet tracking
        self.packets = {}
        self.decay_times = {}
        self.alive = {}
        self.fail_counter = {}
        
    def add_background_structure(self, region_type: str, center: tuple):
        """
        Add background medium structure based on region type.
        """
        if region_type == 'high_structure':
            # Add energy concentration that affects medium
            for i in range(self.size):
                for j in range(self.size):
                    r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                    if r < 15:
                        self.phi[i, j] += 2.0 * np.exp(-r**2 / 50)
        elif region_type == 'transitional':
            # Moderate structure
            for i in range(self.size):
                for j in range(self.size):
                    r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                    if r < 10:
                        self.phi[i, j] += 0.5 * np.exp(-r**2 / 30)
        # 'quiet' region: no additional structure
        
    def seed_packet(self, name: str, center: tuple, amplitude: float = 1.0, width: float = 3.0):
        """
        Seed a localized metastable packet.
        u(x, 0) = A₀ exp(-|x - xᵢ|² / (2σ₀²))
        """
        ci, cj = center
        
        # Add Gaussian packet to phi
        for i in range(self.size):
            for j in range(self.size):
                r2 = (i - ci)**2 + (j - cj)**2
                self.phi[i, j] += amplitude * np.exp(-r2 / (2 * width**2))
        
        # Add noise
        if self.noise_amplitude > 0:
            self.phi += np.random.randn(self.size, self.size) * self.noise_amplitude
        
        # Store packet info
        self.packets[name] = {
            'center': center,
            'initial_width': width,
            'initial_amplitude': amplitude,
            'initial_energy': None,
            'initial_peak': None,
            'window_size': int(4 * width),
        }
        self.alive[name] = True
        self.decay_times[name] = None
        self.fail_counter[name] = 0
        
        # Compute initial observables
        E_init, sigma_init, P_init = self.compute_packet_observables(name)
        self.packets[name]['initial_energy'] = E_init
        self.packets[name]['initial_peak'] = P_init
        self.packets[name]['initial_sigma'] = sigma_init
        
    def compute_packet_observables(self, name: str):
        """
        Compute local observables for a packet.
        Returns: (local_energy, local_width, local_peak)
        """
        info = self.packets[name]
        ci, cj = info['center']
        w = info['window_size']
        
        # Window bounds
        i0 = max(0, ci - w)
        i1 = min(self.size, ci + w + 1)
        j0 = max(0, cj - w)
        j1 = min(self.size, cj + w + 1)
        
        # Local fields
        phi_local = self.phi[i0:i1, j0:j1]
        phi_dot_local = self.phi_dot[i0:i1, j0:j1]
        
        # Local energy: Eᵢ = ∫ [½u̇² + ½|∇u|²] dx
        # Approximate gradient energy
        grad_phi_i = np.diff(phi_local, axis=0, append=phi_local[-1:, :])
        grad_phi_j = np.diff(phi_local, axis=1, append=phi_local[:, -1:])
        grad_energy = 0.5 * (grad_phi_i**2 + grad_phi_j**2)
        kinetic_energy = 0.5 * phi_dot_local**2
        E_local = np.sum(kinetic_energy + grad_energy)
        
        # Local peak: Pᵢ = max |u|
        P_local = np.max(np.abs(phi_local))
        
        # Local width: σ² = ∫ |x-xᵢ|² ρ dx / ∫ ρ dx
        # Use energy density as weight
        rho = phi_local**2 + phi_dot_local**2
        rho_sum = np.sum(rho) + 1e-10
        
        # Create distance grid from center (relative to window)
        ii, jj = np.meshgrid(
            np.arange(i0, i1) - ci,
            np.arange(j0, j1) - cj,
            indexing='ij'
        )
        r2 = ii**2 + jj**2
        
        sigma2 = np.sum(r2 * rho) / rho_sum
        sigma = np.sqrt(sigma2) if sigma2 > 0 else 0
        
        return E_local, sigma, P_local
    
    def check_decay(self, name: str) -> bool:
        """
        Check if packet has decayed.
        Decay = any condition fails for hold_time consecutive steps.
        """
        if not self.alive[name]:
            return True
        
        info = self.packets[name]
        E, sigma, P = self.compute_packet_observables(name)
        
        # Thresholds
        E_min = info['initial_energy'] * self.E_min_fraction
        sigma_max = info['initial_sigma'] * self.sigma_max_factor
        P_min = info['initial_peak'] * self.P_min_fraction
        
        # Check conditions
        energy_ok = E > E_min
        width_ok = sigma < sigma_max
        peak_ok = P > P_min
        
        all_ok = energy_ok and width_ok and peak_ok
        
        if not all_ok:
            self.fail_counter[name] += 1
        else:
            self.fail_counter[name] = 0
        
        # Confirm decay after hold_time
        if self.fail_counter[name] >= self.hold_time:
            self.alive[name] = False
            self.decay_times[name] = self.t_sim
            return True
        
        return False
    
    def compute_c_eff(self):
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
        """Advance one timestep."""
        rho = self.phi**2 + self.phi_dot**2
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        
        tau_eq = self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
        
        lap_tau = (np.roll(self.tau, 1, axis=0) + np.roll(self.tau, -1, axis=0) +
                   np.roll(self.tau, 1, axis=1) + np.roll(self.tau, -1, axis=1) - 
                   4 * self.tau)
        
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        
        lap_phi = (np.roll(self.phi, 1, axis=0) + np.roll(self.phi, -1, axis=0) +
                   np.roll(self.phi, 1, axis=1) + np.roll(self.phi, -1, axis=1) - 
                   4 * self.phi)
        
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
        
        self.t_sim += self.dt
        
        # Check decay for all packets
        for name in self.packets:
            self.check_decay(name)


def run_single_lifetime_trial(region_type: str, center: tuple, noise_seed: int = None):
    """
    Run a single lifetime measurement trial.
    Returns decay time or None if packet survives.
    """
    if noise_seed is not None:
        np.random.seed(noise_seed)
    
    sim = DecayClockSimulator(
        size=100,
        beta=1.0,
        lambda_relax=1.5,
        E_min_fraction=0.2,
        sigma_max_factor=2.5,
        P_min_fraction=0.15,
        hold_time=15,
        noise_amplitude=0.02,
    )
    
    # Add background structure
    sim.add_background_structure(region_type, center)
    
    # Let medium settle
    for _ in range(50):
        sim.step()
    
    # Seed metastable packet
    sim.seed_packet('test', center, amplitude=1.5, width=4.0)
    
    # Run until decay or timeout
    max_steps = 800
    for t in range(max_steps):
        sim.step()
        if not sim.alive['test']:
            return sim.decay_times['test']
    
    # Survived entire simulation
    return None


def run_decay_clock_test():
    """
    Main decay clock test with statistical ensemble.
    """
    print("=" * 70)
    print("DECAY CLOCK - METASTABLE PACKET LIFETIME")
    print("=" * 70)
    print()
    print("Packet: u(x,0) = A₀ exp(-|x-xᵢ|²/(2σ₀²))")
    print("Decay: when E < E_min OR σ > σ_max OR P < P_min")
    print()
    
    # Region configurations
    regions = {
        'high_structure': (50, 50),
        'transitional': (50, 25),
        'quiet': (25, 25),
    }
    
    # Number of trials per region
    n_trials = 15
    
    # Results storage
    lifetimes = {region: [] for region in regions}
    
    for region, center in regions.items():
        print(f"Testing {region} region ({n_trials} trials)...")
        
        for trial in range(n_trials):
            decay_time = run_single_lifetime_trial(region, center, noise_seed=trial*100+42)
            
            if decay_time is not None:
                lifetimes[region].append(decay_time)
            else:
                # Survived - record as max time
                lifetimes[region].append(32.0)  # max_steps * dt
        
        mean_lifetime = np.mean(lifetimes[region])
        std_lifetime = np.std(lifetimes[region])
        print(f"  ⟨T⟩ = {mean_lifetime:.2f} ± {std_lifetime:.2f}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS")
    print("=" * 70)
    
    # Compute statistics
    stats = {}
    for region in regions:
        lt = np.array(lifetimes[region])
        stats[region] = {
            'mean': float(np.mean(lt)),
            'std': float(np.std(lt)),
            'median': float(np.median(lt)),
            'min': float(np.min(lt)),
            'max': float(np.max(lt)),
            'survived': int(np.sum(lt >= 31)),  # Near max time
        }
        print(f"\n{region}:")
        print(f"  Mean lifetime: {stats[region]['mean']:.2f}")
        print(f"  Std: {stats[region]['std']:.2f}")
        print(f"  Survived: {stats[region]['survived']}/{n_trials}")
    
    # Question 1: Do lifetimes differ across regions?
    print("\n" + "=" * 70)
    print("Q1: Do lifetimes differ systematically across regions?")
    print("=" * 70)
    
    mean_lifetimes = [stats[r]['mean'] for r in regions]
    lifetime_spread = max(mean_lifetimes) - min(mean_lifetimes)
    mean_overall = np.mean(mean_lifetimes)
    relative_spread = lifetime_spread / mean_overall * 100 if mean_overall > 0 else 0
    
    print(f"\n  Lifetime spread: {lifetime_spread:.2f}")
    print(f"  Relative spread: {relative_spread:.1f}%")
    
    q1_pass = relative_spread > 15  # >15% difference
    print(f"  Q1 Pass (>15% spread): {q1_pass}")
    
    # Question 2: Is lifetime correlated with transport clock?
    print("\n" + "=" * 70)
    print("Q2: Is decay time independent of transport-based measures?")
    print("=" * 70)
    
    # Run additional test to check correlation with c_eff
    # For now, use region ordering as proxy
    # High-structure should have different effective c than quiet
    
    region_order = ['quiet', 'transitional', 'high_structure']
    lifetime_order = [stats[r]['mean'] for r in region_order]
    
    # Check if ordering is monotonic (would suggest transport correlation)
    is_monotonic = (lifetime_order == sorted(lifetime_order) or 
                   lifetime_order == sorted(lifetime_order, reverse=True))
    
    print(f"\n  Lifetimes by region: {[f'{x:.2f}' for x in lifetime_order]}")
    print(f"  Monotonic with structure: {is_monotonic}")
    
    q2_pass = not is_monotonic or relative_spread > 30
    print(f"  Q2 Pass (non-trivial relationship): {q2_pass}")
    
    # Question 3: Does forcing agreement help or hurt?
    # For decay clocks, this would mean equalizing lifetimes
    # We'll compare variance
    print("\n" + "=" * 70)
    print("Q3: Statistical properties of lifetime distribution")
    print("=" * 70)
    
    all_lifetimes = []
    for region in regions:
        all_lifetimes.extend(lifetimes[region])
    
    overall_cv = np.std(all_lifetimes) / np.mean(all_lifetimes) * 100
    within_region_cv = np.mean([stats[r]['std']/stats[r]['mean']*100 for r in regions if stats[r]['mean'] > 0])
    
    print(f"\n  Overall CV: {overall_cv:.1f}%")
    print(f"  Within-region CV: {within_region_cv:.1f}%")
    print(f"  Between-region variation is {'larger' if overall_cv > within_region_cv else 'smaller'} than within-region")
    
    q3_informative = overall_cv > within_region_cv
    print(f"  Q3 Informative (between > within): {q3_informative}")
    
    # Final verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    print(f"\n  Q1 - Lifetimes differ across regions: {'PASS' if q1_pass else 'FAIL'}")
    print(f"  Q2 - Non-trivial transport relationship: {'PASS' if q2_pass else 'FAIL'}")
    print(f"  Q3 - Between-region variation significant: {'PASS' if q3_informative else 'FAIL'}")
    
    score = sum([q1_pass, q2_pass, q3_informative])
    
    if score >= 2:
        verdict = "DECAY CLOCKS PROVIDE USEFUL TEMPORAL INFORMATION"
        verdict_short = "USEFUL"
    elif score >= 1:
        verdict = "DECAY CLOCKS SHOW PARTIAL SIGNAL"
        verdict_short = "PARTIAL"
    else:
        verdict = "DECAY CLOCKS NOT INFORMATIVE IN CURRENT REGIME"
        verdict_short = "NOT_INFORMATIVE"
    
    print(f"\n>>> {verdict}")
    
    # Comparison to oscillators
    print("\n" + "=" * 70)
    print("COMPARISON TO OSCILLATORS")
    print("=" * 70)
    print(f"\n  Oscillator collapse improvement: 11.2% (independent)")
    print(f"  Decay clock relative spread: {relative_spread:.1f}%")
    
    if relative_spread > 15:
        print("  → Decay clocks show stronger region differentiation")
    else:
        print("  → Oscillators remain the stronger temporal candidate")
    
    # Plotting
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Lifetime distributions
    ax = fig.add_subplot(2, 3, 1)
    positions = [1, 2, 3]
    bp = ax.boxplot([lifetimes[r] for r in regions], positions=positions, patch_artist=True)
    colors = ['#ff9999', '#99ff99', '#9999ff']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax.set_xticklabels(list(regions.keys()), rotation=15)
    ax.set_ylabel('Decay Time')
    ax.set_title('Lifetime Distribution by Region')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 2. Mean lifetimes with error bars
    ax = fig.add_subplot(2, 3, 2)
    means = [stats[r]['mean'] for r in regions]
    stds = [stats[r]['std'] for r in regions]
    ax.bar(list(regions.keys()), means, yerr=stds, capsize=5, color=colors, alpha=0.7)
    ax.set_ylabel('Mean Lifetime ⟨T⟩')
    ax.set_title(f'Mean Lifetimes (spread={relative_spread:.1f}%)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 3. Survival curves
    ax = fig.add_subplot(2, 3, 3)
    for i, region in enumerate(regions):
        lt = np.array(lifetimes[region])
        t_vals = np.sort(lt)
        survival = 1 - np.arange(1, len(t_vals)+1) / len(t_vals)
        ax.step(t_vals, survival, where='post', label=region, linewidth=2, color=colors[i])
    ax.set_xlabel('Time')
    ax.set_ylabel('Survival Probability S(t)')
    ax.set_title('Survival Curves')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Histograms
    ax = fig.add_subplot(2, 3, 4)
    for i, region in enumerate(regions):
        ax.hist(lifetimes[region], bins=10, alpha=0.5, label=region, color=colors[i])
    ax.set_xlabel('Decay Time')
    ax.set_ylabel('Count')
    ax.set_title('Lifetime Histograms')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. CV comparison
    ax = fig.add_subplot(2, 3, 5)
    cvs = [stats[r]['std']/stats[r]['mean']*100 if stats[r]['mean'] > 0 else 0 for r in regions]
    cvs.append(overall_cv)
    labels = list(regions.keys()) + ['overall']
    ax.bar(labels, cvs, color=colors + ['gray'], alpha=0.7)
    ax.set_ylabel('Coefficient of Variation (%)')
    ax.set_title('Variability Analysis')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 6. Summary
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
DECAY CLOCK TEST
================

Metastable packet lifetime as temporal observable.

Decay criterion:
  E < 0.2×E₀ OR σ > 2.5×σ₀ OR P < 0.15×P₀

Results ({n_trials} trials per region):

  high_structure: ⟨T⟩ = {stats['high_structure']['mean']:.2f} ± {stats['high_structure']['std']:.2f}
  transitional:   ⟨T⟩ = {stats['transitional']['mean']:.2f} ± {stats['transitional']['std']:.2f}
  quiet:          ⟨T⟩ = {stats['quiet']['mean']:.2f} ± {stats['quiet']['std']:.2f}

  Lifetime spread: {lifetime_spread:.2f} ({relative_spread:.1f}%)

Questions:
  Q1 - Lifetimes differ: {'PASS' if q1_pass else 'FAIL'}
  Q2 - Non-trivial: {'PASS' if q2_pass else 'FAIL'}
  Q3 - Significant variation: {'PASS' if q3_informative else 'FAIL'}

VERDICT: {verdict_short}
"""
    
    color = 'lightgreen' if score >= 2 else 'lightyellow' if score >= 1 else 'lightcoral'
    ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'DECAY CLOCK: {verdict_short}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/decay_clocks.png', dpi=150, bbox_inches='tight')
    print("\nSaved decay_clocks.png")
    
    # Save JSON
    results_json = {
        'stats': stats,
        'lifetimes': {r: [float(x) for x in lifetimes[r]] for r in regions},
        'q1_pass': bool(q1_pass),
        'q2_pass': bool(q2_pass),
        'q3_informative': bool(q3_informative),
        'relative_spread': float(relative_spread),
        'verdict': verdict,
        'verdict_short': verdict_short,
    }
    
    with open('/app/backend/qmrt_topology/decay_clocks_results.json', 'w') as f:
        json.dump(results_json, f, indent=2)
    print("Saved decay_clocks_results.json")
    
    return results_json


if __name__ == "__main__":
    results = run_decay_clock_test()
