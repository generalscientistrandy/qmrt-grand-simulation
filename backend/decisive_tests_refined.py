"""
Decisive Tests (Refined) for Stability Channel Co-Alignment
============================================================

Test 1A: SEEDED PERSISTENCE
    - Seed vortex-antivortex pairs explicitly
    - Measure lifetime, late-time density, residence in high-β
    - Question: Does β help SUSTAIN existing vortices?

Test 2B: PINNING / RESIDENCE
    - Seed single vortex at controlled locations
    - Measure drift, displacement, time in high-β
    - Question: Does β act as a pinning well?

Goal: Separate maintenance from creation, pinning from damping.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple
import json


class EnergyLandscapeSimulator2D:
    """
    Complex scalar with β(x) in the energy functional.
    
    Key change: ∂²ψ = ∇·(β(x)∇ψ) - γ∂ₜψ
    
    This makes vortex cores (high |∇ψ|) feel the β landscape directly.
    """
    
    def __init__(
        self,
        size: int = 80,
        c_0: float = 2.0,
        tau_0: float = 1.0,
        gamma: float = 0.01,
        lambda_relax: float = 0.5,
        beta_base: float = 0.5,
        D_medium: float = 0.1,
        dt: float = 0.04,
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.gamma = gamma
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.dt = dt
        
        self.psi_r = np.zeros((size, size))
        self.psi_i = np.zeros((size, size))
        self.psi_r_dot = np.zeros((size, size))
        self.psi_i_dot = np.zeros((size, size))
        
        self.tau = np.ones((size, size)) * tau_0
        self.beta_field = np.ones((size, size)) * beta_base
        self.lambda_field = np.ones((size, size)) * lambda_relax
    
    @property
    def amplitude(self) -> np.ndarray:
        return np.sqrt(self.psi_r**2 + self.psi_i**2)
    
    @property
    def phase(self) -> np.ndarray:
        return np.arctan2(self.psi_i, self.psi_r)
    
    @property
    def rho(self) -> np.ndarray:
        return self.psi_r**2 + self.psi_i**2 + self.psi_r_dot**2 + self.psi_i_dot**2
    
    def compute_c_eff(self) -> np.ndarray:
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho: np.ndarray) -> np.ndarray:
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta_field * rho_smooth / rho_max)
    
    def compute_beta_weighted_laplacian(self, f: np.ndarray) -> np.ndarray:
        """∇·(β∇f) = β∇²f + ∇β·∇f"""
        lap_f = (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                 np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
        
        df_dx = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) / 2
        df_dy = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / 2
        
        dbeta_dx = (np.roll(self.beta_field, -1, 0) - np.roll(self.beta_field, 1, 0)) / 2
        dbeta_dy = (np.roll(self.beta_field, -1, 1) - np.roll(self.beta_field, 1, 1)) / 2
        
        return self.beta_field * lap_f + dbeta_dx * df_dx + dbeta_dy * df_dy
    
    def step(self, use_beta_weighting: bool = True):
        """Advance simulation."""
        rho = self.rho
        
        # Medium evolution
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = (np.roll(self.tau, 1, 0) + np.roll(self.tau, -1, 0) +
                   np.roll(self.tau, 1, 1) + np.roll(self.tau, -1, 1) - 4*self.tau)
        dtau_dt = -self.lambda_field * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        c_eff_sq = c_eff**2
        
        if use_beta_weighting:
            weighted_lap_r = self.compute_beta_weighted_laplacian(self.psi_r)
            weighted_lap_i = self.compute_beta_weighted_laplacian(self.psi_i)
            acc_r = c_eff_sq * weighted_lap_r - self.gamma * self.psi_r_dot
            acc_i = c_eff_sq * weighted_lap_i - self.gamma * self.psi_i_dot
        else:
            lap_r = (np.roll(self.psi_r, 1, 0) + np.roll(self.psi_r, -1, 0) +
                     np.roll(self.psi_r, 1, 1) + np.roll(self.psi_r, -1, 1) - 4*self.psi_r)
            lap_i = (np.roll(self.psi_i, 1, 0) + np.roll(self.psi_i, -1, 0) +
                     np.roll(self.psi_i, 1, 1) + np.roll(self.psi_i, -1, 1) - 4*self.psi_i)
            acc_r = c_eff_sq * lap_r - self.gamma * self.psi_r_dot
            acc_i = c_eff_sq * lap_i - self.gamma * self.psi_i_dot
        
        self.psi_r_dot += acc_r * self.dt
        self.psi_i_dot += acc_i * self.dt
        self.psi_r += self.psi_r_dot * self.dt
        self.psi_i += self.psi_i_dot * self.dt
    
    def set_biased_region(self, center: Tuple[int, int], radius: float,
                          beta_inside: float, beta_outside: float):
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        inside = r <= radius
        self.beta_field[inside] = beta_inside
        self.beta_field[~inside] = beta_outside
    
    def set_beta_gradient(self, direction: str = 'x', beta_low: float = 0.2, beta_high: float = 0.8):
        if direction == 'x':
            for i in range(self.size):
                self.beta_field[i, :] = beta_low + (beta_high - beta_low) * i / self.size
        else:
            for j in range(self.size):
                self.beta_field[:, j] = beta_low + (beta_high - beta_low) * j / self.size
    
    def add_vortex(self, center: Tuple[int, int], charge: int = 1, 
                   amplitude: float = 1.0, core_radius: float = 3.0):
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        dx = x - center[0]
        dy = y - center[1]
        r = np.sqrt(dx**2 + dy**2 + 0.01)
        theta = np.arctan2(dy, dx)
        
        amp_profile = amplitude * np.tanh(r / core_radius)
        phase = charge * theta
        
        if np.max(np.abs(self.psi_r)) < 0.01:
            self.psi_r = amp_profile * np.cos(phase)
            self.psi_i = amp_profile * np.sin(phase)
        else:
            psi_existing = self.psi_r + 1j * self.psi_i
            psi_vortex = amp_profile * np.exp(1j * phase)
            combined = psi_existing * psi_vortex / (amplitude + 0.01)
            self.psi_r = np.real(combined)
            self.psi_i = np.imag(combined)
    
    def compute_winding_number(self, i: int, j: int, radius: int = 2) -> float:
        phase = self.phase
        loop_points = []
        for dj in range(-radius, radius+1):
            loop_points.append((i-radius, j+dj))
        for di in range(-radius+1, radius+1):
            loop_points.append((i+di, j+radius))
        for dj in range(radius-1, -radius-1, -1):
            loop_points.append((i+radius, j+dj))
        for di in range(radius-1, -radius, -1):
            loop_points.append((i+di, j-radius))
        
        total = 0
        for k in range(len(loop_points)):
            ni, nj = loop_points[k]
            ni_next, nj_next = loop_points[(k+1) % len(loop_points)]
            ni, nj = ni % self.size, nj % self.size
            ni_next, nj_next = ni_next % self.size, nj_next % self.size
            
            dp = phase[ni_next, nj_next] - phase[ni, nj]
            while dp > np.pi: dp -= 2*np.pi
            while dp < -np.pi: dp += 2*np.pi
            total += dp
        
        return total / (2*np.pi)
    
    def detect_vortices(self, amplitude_threshold: float = 0.3) -> List[Dict]:
        vortices = []
        amp = self.amplitude
        
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                local_amp = amp[i, j]
                region = amp[i-1:i+2, j-1:j+2]
                
                if local_amp <= np.min(region) and local_amp < amplitude_threshold:
                    winding = self.compute_winding_number(i, j, radius=2)
                    if abs(winding) > 0.5:
                        vortices.append({
                            'position': [i, j],
                            'charge': int(np.round(winding)),
                            'beta': float(self.beta_field[i, j])
                        })
        return vortices


# ============================================================
# TEST 1A: SEEDED PERSISTENCE
# ============================================================

def test_seeded_persistence():
    """
    Seed vortex-antivortex pairs explicitly.
    Measure: Do they survive longer with β-asymmetry?
    
    This separates MAINTENANCE from CREATION.
    """
    print("="*70)
    print("TEST 1A: SEEDED PERSISTENCE")
    print("="*70)
    print()
    print("Question: Does β help SUSTAIN existing vortices?")
    print("Method: Seed pairs explicitly, measure lifetime & late-time density")
    print()
    
    size = 100
    center = (size//2, size//2)
    radius = 25
    steps = 6000
    n_trials = 5
    
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    inside_mask = r <= radius
    
    configs = [
        ("uniform_low", 0.3, 0.3),      # Uniform low β
        ("uniform_high", 0.8, 0.8),     # Uniform high β
        ("biased_center", 0.8, 0.3),    # High-β center (well)
    ]
    
    all_results = {}
    
    for config_name, beta_inside, beta_outside in configs:
        print(f"--- Configuration: {config_name} ---")
        print(f"    β_inside={beta_inside}, β_outside={beta_outside}")
        
        lifetimes = []
        late_counts = []
        residence_times = []  # Steps spent in high-β
        
        for trial in range(n_trials):
            sim = EnergyLandscapeSimulator2D(size=size, gamma=0.006, D_medium=0.02)
            sim.set_biased_region(center, radius, beta_inside=beta_inside, beta_outside=beta_outside)
            
            # Initialize with uniform amplitude background
            sim.psi_r[:] = 1.2
            sim.psi_i[:] = 0.0
            
            # Seed vortex-antivortex pair INSIDE the high-β region
            v1_pos = (center[0] - 8, center[1])
            v2_pos = (center[0] + 8, center[1])
            sim.add_vortex(v1_pos, charge=+1, amplitude=1.2, core_radius=4.0)
            sim.add_vortex(v2_pos, charge=-1, amplitude=1.2, core_radius=4.0)
            
            # Track
            vortex_present = True
            lifetime = 0
            steps_in_high_beta = 0
            counts_over_time = []
            
            for step in range(steps):
                sim.step(use_beta_weighting=True)
                
                if step % 50 == 0:
                    vortices = sim.detect_vortices(amplitude_threshold=0.4)
                    n_vortices = len(vortices)
                    counts_over_time.append(n_vortices)
                    
                    if n_vortices > 0:
                        lifetime = step
                        # Count how many are in high-β
                        for v in vortices:
                            if sim.beta_field[v['position'][0], v['position'][1]] > 0.5:
                                steps_in_high_beta += 1
                    
                    if n_vortices == 0 and vortex_present:
                        vortex_present = False
            
            lifetimes.append(lifetime)
            late_counts.append(np.mean(counts_over_time[-10:]) if counts_over_time else 0)
            residence_times.append(steps_in_high_beta)
        
        avg_lifetime = np.mean(lifetimes)
        std_lifetime = np.std(lifetimes)
        avg_late = np.mean(late_counts)
        avg_residence = np.mean(residence_times)
        
        all_results[config_name] = {
            'avg_lifetime': avg_lifetime,
            'std_lifetime': std_lifetime,
            'avg_late_count': avg_late,
            'avg_residence': avg_residence,
            'lifetimes': lifetimes
        }
        
        print(f"    Avg lifetime: {avg_lifetime:.0f} ± {std_lifetime:.0f} steps")
        print(f"    Late vortex count: {avg_late:.2f}")
        print(f"    High-β residence: {avg_residence:.0f} sample-steps")
        print()
    
    # Summary comparison
    print("="*70)
    print("TEST 1A SUMMARY")
    print("="*70)
    print()
    print("| Configuration   | Avg Lifetime | Late Count | High-β Residence |")
    print("|-----------------|--------------|------------|------------------|")
    for name in ['uniform_low', 'uniform_high', 'biased_center']:
        r = all_results[name]
        print(f"| {name:15} | {r['avg_lifetime']:10.0f} | {r['avg_late_count']:10.2f} | {r['avg_residence']:16.0f} |")
    
    print()
    
    # Verdict
    uniform_low = all_results['uniform_low']['avg_lifetime']
    uniform_high = all_results['uniform_high']['avg_lifetime']
    biased = all_results['biased_center']['avg_lifetime']
    
    print("Interpretation:")
    if uniform_high > uniform_low * 1.3:
        print(f"  ✓ Higher β extends vortex lifetime ({uniform_high:.0f} vs {uniform_low:.0f})")
    else:
        print(f"  - β magnitude alone doesn't extend lifetime significantly")
    
    if biased > uniform_high * 1.1:
        print(f"  ✓ β-asymmetry (well) further extends lifetime ({biased:.0f} vs uniform_high {uniform_high:.0f})")
    elif biased > uniform_low * 1.3:
        print(f"  ~ β-well lifetime ({biased:.0f}) better than uniform_low ({uniform_low:.0f})")
    else:
        print(f"  - β-asymmetry doesn't provide additional stabilization")
    
    return all_results


# ============================================================
# TEST 2B: PINNING / RESIDENCE
# ============================================================

def test_pinning_residence():
    """
    Seed single vortex at different locations.
    Measure: Does it stay in high-β? Does it drift toward high-β?
    
    This tests whether β acts as a PINNING WELL.
    """
    print()
    print("="*70)
    print("TEST 2B: PINNING / RESIDENCE")
    print("="*70)
    print()
    print("Question: Does β act as a pinning well?")
    print("Method: Seed vortex at different locations, measure drift & residence")
    print()
    
    size = 80
    steps = 4000
    
    # β gradient: low at x=0, high at x=size
    # Test starting positions: low-β (x=15), center (x=40), high-β (x=65)
    start_positions = [
        ('low_beta', 15),
        ('center', 40),
        ('high_beta', 65),
    ]
    
    results = {}
    
    for use_beta_weighting in [False, True]:
        method = "β-weighted" if use_beta_weighting else "standard"
        results[method] = {}
        
        print(f"--- {method} Laplacian ---")
        
        for pos_name, start_x in start_positions:
            sim = EnergyLandscapeSimulator2D(size=size, gamma=0.005, D_medium=0.02)
            sim.set_beta_gradient(direction='x', beta_low=0.2, beta_high=0.8)
            
            # Background
            sim.psi_r[:] = 1.2
            sim.psi_i[:] = 0.0
            
            # Seed single vortex
            start_pos = (start_x, size//2)
            sim.add_vortex(start_pos, charge=+1, amplitude=1.2, core_radius=4.0)
            
            initial_beta = sim.beta_field[start_x, size//2]
            
            # Track trajectory
            x_positions = [start_x]
            beta_values = [initial_beta]
            time_in_high_beta = 0  # Steps where β > 0.5
            lifetime = 0
            
            for step in range(steps):
                sim.step(use_beta_weighting=use_beta_weighting)
                
                if step % 50 == 0:
                    vortices = sim.detect_vortices(amplitude_threshold=0.4)
                    if vortices:
                        v = vortices[0]
                        x = v['position'][0]
                        beta = v['beta']
                        x_positions.append(x)
                        beta_values.append(beta)
                        lifetime = step
                        if beta > 0.5:
                            time_in_high_beta += 1
            
            # Analyze
            final_x = x_positions[-1] if len(x_positions) > 1 else start_x
            drift = final_x - start_x
            final_beta = beta_values[-1] if len(beta_values) > 1 else initial_beta
            
            results[method][pos_name] = {
                'start_x': start_x,
                'final_x': final_x,
                'drift': drift,
                'initial_beta': initial_beta,
                'final_beta': final_beta,
                'lifetime': lifetime,
                'time_in_high_beta': time_in_high_beta,
                'trajectory_len': len(x_positions)
            }
            
            print(f"  {pos_name}: x={start_x}→{final_x} (Δ={drift:+.0f}), "
                  f"β={initial_beta:.2f}→{final_beta:.2f}, "
                  f"lifetime={lifetime}, high-β time={time_in_high_beta}")
        
        print()
    
    # Summary
    print("="*70)
    print("TEST 2B SUMMARY")
    print("="*70)
    print()
    print("| Method     | Start   | Drift | Final β | Lifetime | High-β Time |")
    print("|------------|---------|-------|---------|----------|-------------|")
    for method in ['standard', 'β-weighted']:
        for pos_name in ['low_beta', 'center', 'high_beta']:
            r = results[method][pos_name]
            print(f"| {method:10} | {pos_name:7} | {r['drift']:+5.0f} | {r['final_beta']:7.2f} | "
                  f"{r['lifetime']:8} | {r['time_in_high_beta']:11} |")
    
    print()
    
    # Interpretation
    print("Interpretation:")
    
    # Check if β-weighted keeps vortices in high-β longer
    std_high_beta_time = results['standard']['high_beta']['time_in_high_beta']
    bw_high_beta_time = results['β-weighted']['high_beta']['time_in_high_beta']
    
    if bw_high_beta_time > std_high_beta_time * 1.2:
        print(f"  ✓ β-weighting increases high-β residence ({bw_high_beta_time} vs {std_high_beta_time})")
    else:
        print(f"  - No significant residence time difference")
    
    # Check if vortex drifts toward high-β
    std_low_drift = results['standard']['low_beta']['drift']
    bw_low_drift = results['β-weighted']['low_beta']['drift']
    
    if bw_low_drift > std_low_drift + 5:
        print(f"  ✓ β-weighting causes drift toward high-β (Δx={bw_low_drift:+.0f} vs {std_low_drift:+.0f})")
    elif bw_low_drift < std_low_drift - 5:
        print(f"  ~ β-weighting REDUCES drift (possible pinning effect)")
    else:
        print(f"  - Similar drift patterns")
    
    # Check lifetime in different regions
    bw_lifetimes = [results['β-weighted'][p]['lifetime'] for p in ['low_beta', 'center', 'high_beta']]
    print(f"  β-weighted lifetimes: low={bw_lifetimes[0]}, center={bw_lifetimes[1]}, high={bw_lifetimes[2]}")
    
    if bw_lifetimes[2] > bw_lifetimes[0] * 1.2:
        print(f"  ✓ Vortices live longer in high-β regions")
    
    return results


# ============================================================
# TEST 3: PAIR DYNAMICS IN β-WELL
# ============================================================

def test_pair_dynamics_in_well():
    """
    Seed vortex-antivortex pair, one inside β-well, one outside.
    Measure: Do they annihilate? Where? Does the well-bound one survive longer?
    """
    print()
    print("="*70)
    print("TEST 3: PAIR DYNAMICS IN β-WELL")
    print("="*70)
    print()
    print("Question: Does β-well protect vortex from annihilation partner?")
    print()
    
    size = 100
    center = (size//2, size//2)
    radius = 20
    steps = 5000
    n_trials = 5
    
    results = {'standard': [], 'β-weighted': []}
    
    for use_beta_weighting in [False, True]:
        method = "β-weighted" if use_beta_weighting else "standard"
        print(f"--- {method} ---")
        
        for trial in range(n_trials):
            sim = EnergyLandscapeSimulator2D(size=size, gamma=0.006, D_medium=0.02)
            sim.set_biased_region(center, radius, beta_inside=0.8, beta_outside=0.25)
            
            sim.psi_r[:] = 1.2
            
            # Vortex inside well, antivortex outside
            v_inside = (center[0], center[1])
            v_outside = (center[0], center[1] + radius + 15)
            
            sim.add_vortex(v_inside, charge=+1, amplitude=1.2, core_radius=4.0)
            sim.add_vortex(v_outside, charge=-1, amplitude=1.2, core_radius=4.0)
            
            inside_lifetime = 0
            outside_lifetime = 0
            annihilation_step = None
            
            for step in range(steps):
                sim.step(use_beta_weighting=use_beta_weighting)
                
                if step % 50 == 0:
                    vortices = sim.detect_vortices(amplitude_threshold=0.4)
                    pos_vortices = [v for v in vortices if v['charge'] > 0]
                    neg_vortices = [v for v in vortices if v['charge'] < 0]
                    
                    if pos_vortices:
                        inside_lifetime = step
                    if neg_vortices:
                        outside_lifetime = step
                    
                    if len(vortices) == 0 and annihilation_step is None:
                        annihilation_step = step
            
            results[method].append({
                'inside_lifetime': inside_lifetime,
                'outside_lifetime': outside_lifetime,
                'annihilation_step': annihilation_step
            })
        
        avg_inside = np.mean([r['inside_lifetime'] for r in results[method]])
        avg_outside = np.mean([r['outside_lifetime'] for r in results[method]])
        print(f"  Avg inside lifetime: {avg_inside:.0f}")
        print(f"  Avg outside lifetime: {avg_outside:.0f}")
        print()
    
    print("="*70)
    print("TEST 3 SUMMARY")
    print("="*70)
    print()
    
    std_inside = np.mean([r['inside_lifetime'] for r in results['standard']])
    std_outside = np.mean([r['outside_lifetime'] for r in results['standard']])
    bw_inside = np.mean([r['inside_lifetime'] for r in results['β-weighted']])
    bw_outside = np.mean([r['outside_lifetime'] for r in results['β-weighted']])
    
    print(f"Standard:   inside={std_inside:.0f}, outside={std_outside:.0f}")
    print(f"β-weighted: inside={bw_inside:.0f}, outside={bw_outside:.0f}")
    print()
    
    if bw_inside > std_inside * 1.2:
        print(f"✓ β-weighting extends INSIDE vortex lifetime by {bw_inside/std_inside:.2f}x")
    if bw_inside > bw_outside * 1.2:
        print(f"✓ Inside-well vortex survives longer than outside ({bw_inside:.0f} vs {bw_outside:.0f})")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*70)
    print("DECISIVE TESTS (REFINED) FOR STABILITY CHANNEL CO-ALIGNMENT")
    print("="*70)
    print()
    print("Focus: MAINTENANCE (not creation) and PINNING (not damping)")
    print()
    
    persistence_results = test_seeded_persistence()
    pinning_results = test_pinning_residence()
    pair_results = test_pair_dynamics_in_well()
    
    print()
    print("="*70)
    print("FINAL VERDICT")
    print("="*70)
    print()
    
    # Check Test 1A
    ul = persistence_results['uniform_low']['avg_lifetime']
    uh = persistence_results['uniform_high']['avg_lifetime']
    bc = persistence_results['biased_center']['avg_lifetime']
    
    test1a_pass = (uh > ul * 1.2) or (bc > ul * 1.3)
    
    # Check Test 2B
    bw_high_res = pinning_results['β-weighted']['high_beta']['time_in_high_beta']
    std_high_res = pinning_results['standard']['high_beta']['time_in_high_beta']
    test2b_pass = bw_high_res > std_high_res * 1.1
    
    # Check Test 3
    std_in = np.mean([r['inside_lifetime'] for r in pair_results['standard']])
    bw_in = np.mean([r['inside_lifetime'] for r in pair_results['β-weighted']])
    test3_pass = bw_in > std_in * 1.2
    
    print(f"Test 1A (Seeded Persistence): {'✓ PASS' if test1a_pass else '✗ FAIL'}")
    print(f"Test 2B (Pinning/Residence):  {'✓ PASS' if test2b_pass else '✗ FAIL'}")
    print(f"Test 3 (Pair Protection):     {'✓ PASS' if test3_pass else '✗ FAIL'}")
    print()
    
    if test1a_pass and test2b_pass:
        print("CONCLUSION: β helps SUSTAIN and LOCALIZE existing vortices.")
        print("           Layers (2-4) CAN co-exist → potential for composite stability.")
    elif test1a_pass:
        print("CONCLUSION: β helps SUSTAIN vortices but pinning is weak.")
        print("           Partial co-alignment achieved.")
    elif test2b_pass:
        print("CONCLUSION: β provides spatial BIAS but not strong persistence.")
        print("           Partial co-alignment achieved.")
    else:
        print("CONCLUSION: Minimal coupling insufficient for strong co-alignment.")
        print("           Branch C does NOT achieve composite stability.")
