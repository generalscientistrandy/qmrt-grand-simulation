#!/usr/bin/env python3
"""
QMRT Medium-State Emergent Time Test v2
========================================

Enhanced test addressing the decision rule:

1. NOT A DIRECT ALGEBRAIC RESTATEMENT OF τ
   - Clock must not be trivially τ itself
   - Must show behavior beyond simple τ-tracking

2. NONTRIVIAL IMPROVEMENT
   - Medium clock must significantly outperform transport
   - >20% improvement threshold

3. INDEPENDENT CLOCK BEHAVIOR
   - Clocks in causally separated regions should evolve independently
   - Independence must survive disorder

4. COLLAPSE QUALITY ACROSS REGIMES
   - Test in coherent, transitional, and disordered regimes
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import json


class EnhancedMediumClockTest:
    """
    Enhanced clock testing with rigorous independence checks.
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
    ):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        
    def compute_c_eff(self):
        c_eff = self.c_0 * self.tau / self.tau_0
        return np.clip(c_eff, 0.3, self.c_0 * 1.5)
    
    def step(self):
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
    
    def add_pulse(self, center, amplitude=3.0, width=4.0, velocity=True):
        for i in range(self.size):
            for j in range(self.size):
                r = np.sqrt((i - center[0])**2 + (j - center[1])**2)
                if r < 4 * width:
                    if velocity:
                        self.phi_dot[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))
                    else:
                        self.phi[i, j] += amplitude * np.exp(-r**2 / (2 * width**2))


def test_non_algebraic_clocks():
    """
    Test 1: Verify clocks are NOT direct algebraic restatements of τ.
    
    A trivial clock would be: τ_clock = ∫ f(τ) dt where f(τ) ∝ τ
    
    We test if the clock decorrelates from instantaneous τ over time.
    """
    print("Test 1: Non-Algebraic Clock Independence")
    print("-" * 50)
    
    sim = EnhancedMediumClockTest(size=80)
    sim.add_pulse([40, 40], amplitude=4.0)
    
    # Track τ and various clocks at a point
    ri, rj = 40, 40
    
    tau_history = []
    clock_transport = 0.0
    clock_medium = 0.0
    clock_derivative = 0.0  # Based on dτ/dt, not τ
    
    transport_history = []
    medium_history = []
    derivative_history = []
    
    prev_tau = sim.tau[ri, rj]
    
    for t in range(400):
        sim.step()
        
        if t % 5 == 0:
            local_tau = sim.tau[ri, rj]
            local_c = sim.compute_c_eff()[ri, rj]
            dtau_dt = (local_tau - prev_tau) / (5 * sim.dt)
            prev_tau = local_tau
            
            tau_history.append(local_tau)
            
            # Accumulate clocks
            clock_transport += local_c * 5 * sim.dt
            clock_medium += (1.0 / local_tau) * 5 * sim.dt
            # Derivative clock: sensitive to rate of change, not absolute value
            clock_derivative += np.abs(dtau_dt) * 5 * sim.dt
            
            transport_history.append(clock_transport)
            medium_history.append(clock_medium)
            derivative_history.append(clock_derivative)
    
    tau_history = np.array(tau_history)
    transport_history = np.array(transport_history)
    medium_history = np.array(medium_history)
    derivative_history = np.array(derivative_history)
    
    # Compute correlation of clock rate with instantaneous τ
    # A truly independent clock should decorrelate
    tau_diff = tau_history[1:] - tau_history[:-1]
    medium_rate = np.diff(medium_history)
    derivative_rate = np.diff(derivative_history)
    
    # Correlation of medium clock rate with τ
    corr_medium_tau = np.corrcoef(tau_history[1:], medium_rate)[0, 1]
    
    # Correlation of derivative clock rate with τ
    corr_derivative_tau = np.corrcoef(tau_history[1:], derivative_rate)[0, 1]
    
    print(f"  Medium clock correlation with τ: {corr_medium_tau:.3f}")
    print(f"  Derivative clock correlation with τ: {corr_derivative_tau:.3f}")
    
    # Check if medium clock is algebraically trivial
    is_trivial = np.abs(corr_medium_tau) > 0.95
    print(f"  Medium clock is algebraic restatement: {is_trivial}")
    
    return {
        'corr_medium_tau': float(corr_medium_tau),
        'corr_derivative_tau': float(corr_derivative_tau),
        'is_trivial': bool(is_trivial),
        'tau_history': tau_history,
        'medium_history': medium_history,
    }


def test_nontrivial_improvement():
    """
    Test 2: Is the improvement nontrivial (>20%)?
    
    Compare synchronization variance across 5 widely separated regions.
    """
    print("\nTest 2: Nontrivial Improvement Threshold")
    print("-" * 50)
    
    sim = EnhancedMediumClockTest(size=120)
    
    # Create complex inhomogeneous medium
    sim.add_pulse([60, 60], amplitude=6.0, velocity=False)
    sim.add_pulse([30, 90], amplitude=3.0, velocity=False)
    
    # 5 measurement regions across the grid
    regions = {
        'center': (60, 60),      # High energy
        'north': (90, 60),
        'south': (30, 60),
        'east': (60, 90),
        'west': (60, 30),
    }
    
    # Accumulated clock values
    clocks = {
        name: {'raw': 0.0, 'transport': 0.0, 'medium': 0.0, 'hybrid': 0.0}
        for name in regions
    }
    
    # History for each
    history = {
        name: {'raw': [], 'transport': [], 'medium': [], 'hybrid': []}
        for name in regions
    }
    
    for t in range(600):
        sim.step()
        
        c_eff = sim.compute_c_eff()
        
        for name, (ri, rj) in regions.items():
            local_c = c_eff[ri, rj]
            local_tau = sim.tau[ri, rj]
            
            clocks[name]['raw'] += sim.dt
            clocks[name]['transport'] += local_c * sim.dt
            clocks[name]['medium'] += (1.0 / local_tau) * sim.dt
            # Hybrid: sqrt(c/τ) - geometric mean of transport and medium effects
            clocks[name]['hybrid'] += np.sqrt(local_c / local_tau) * sim.dt
        
        if t % 10 == 0:
            for name in regions:
                for clock_type in ['raw', 'transport', 'medium', 'hybrid']:
                    history[name][clock_type].append(clocks[name][clock_type])
    
    # Compute synchronization variance for each clock type
    def compute_sync_variance(clock_type):
        """Final clock spread normalized by mean."""
        final_values = [clocks[name][clock_type] for name in regions]
        mean_val = np.mean(final_values)
        variance = np.var(final_values)
        cv = np.sqrt(variance) / mean_val  # Coefficient of variation
        return cv
    
    sync_results = {}
    for clock_type in ['raw', 'transport', 'medium', 'hybrid']:
        sync_results[clock_type] = compute_sync_variance(clock_type)
        print(f"  {clock_type:10}: CV = {sync_results[clock_type]:.4f}")
    
    # Improvement calculation
    transport_cv = sync_results['transport']
    medium_cv = sync_results['medium']
    hybrid_cv = sync_results['hybrid']
    
    improvement_medium = (transport_cv - medium_cv) / transport_cv * 100
    improvement_hybrid = (transport_cv - hybrid_cv) / transport_cv * 100
    
    print(f"\n  Medium improvement over transport: {improvement_medium:.1f}%")
    print(f"  Hybrid improvement over transport: {improvement_hybrid:.1f}%")
    
    nontrivial_medium = improvement_medium > 20
    nontrivial_hybrid = improvement_hybrid > 20
    
    print(f"  Medium is nontrivial (>20%): {nontrivial_medium}")
    print(f"  Hybrid is nontrivial (>20%): {nontrivial_hybrid}")
    
    return {
        'sync_cv': sync_results,
        'improvement_medium': float(improvement_medium),
        'improvement_hybrid': float(improvement_hybrid),
        'nontrivial_medium': bool(nontrivial_medium),
        'nontrivial_hybrid': bool(nontrivial_hybrid),
        'history': history,
    }


def test_causal_independence():
    """
    Test 3: Do clocks remain independent when causally separated?
    
    Place energy sources in two distant regions. Track if clocks
    in each region evolve independently until signals could causally connect.
    """
    print("\nTest 3: Causal Clock Independence")
    print("-" * 50)
    
    sim = EnhancedMediumClockTest(size=150)
    
    # Two causally separated energy concentrations
    sim.add_pulse([40, 40], amplitude=5.0)
    sim.add_pulse([110, 110], amplitude=5.0)
    
    # Clock points (near each source, far from each other)
    clock_A = (45, 45)
    clock_B = (105, 105)
    
    distance = np.sqrt((clock_A[0] - clock_B[0])**2 + (clock_A[1] - clock_B[1])**2)
    causal_time = distance / sim.c_0  # Time for signal to travel
    
    clocks_A = {'transport': 0.0, 'medium': 0.0}
    clocks_B = {'transport': 0.0, 'medium': 0.0}
    
    history_A = {'transport': [], 'medium': []}
    history_B = {'transport': [], 'medium': []}
    
    for t in range(400):
        sim.step()
        
        c_eff = sim.compute_c_eff()
        
        # Clock A
        local_c_A = c_eff[clock_A[0], clock_A[1]]
        local_tau_A = sim.tau[clock_A[0], clock_A[1]]
        clocks_A['transport'] += local_c_A * sim.dt
        clocks_A['medium'] += (1.0 / local_tau_A) * sim.dt
        
        # Clock B
        local_c_B = c_eff[clock_B[0], clock_B[1]]
        local_tau_B = sim.tau[clock_B[0], clock_B[1]]
        clocks_B['transport'] += local_c_B * sim.dt
        clocks_B['medium'] += (1.0 / local_tau_B) * sim.dt
        
        if t % 5 == 0:
            for ct in ['transport', 'medium']:
                history_A[ct].append(clocks_A[ct])
                history_B[ct].append(clocks_B[ct])
    
    # Check correlation before and after causal time
    causal_step = int(causal_time / sim.dt / 5)  # Convert to history index
    
    history_A_arr = {k: np.array(v) for k, v in history_A.items()}
    history_B_arr = {k: np.array(v) for k, v in history_B.items()}
    
    # Rate of change (derivative)
    def compute_rates(h):
        return np.diff(h)
    
    # Pre-causal correlation
    pre_end = min(causal_step, len(history_A_arr['transport']) - 1)
    if pre_end > 5:
        rates_A_pre = compute_rates(history_A_arr['medium'][:pre_end])
        rates_B_pre = compute_rates(history_B_arr['medium'][:pre_end])
        corr_pre = np.corrcoef(rates_A_pre, rates_B_pre)[0, 1]
    else:
        corr_pre = 0.0
    
    # Post-causal correlation
    if causal_step < len(history_A_arr['transport']) - 5:
        rates_A_post = compute_rates(history_A_arr['medium'][causal_step:])
        rates_B_post = compute_rates(history_B_arr['medium'][causal_step:])
        corr_post = np.corrcoef(rates_A_post, rates_B_post)[0, 1]
    else:
        corr_post = 0.0
    
    print(f"  Distance: {distance:.0f} grid units")
    print(f"  Causal time: {causal_time:.1f}")
    print(f"  Pre-causal correlation: {corr_pre:.3f}")
    print(f"  Post-causal correlation: {corr_post:.3f}")
    
    # Independence = low pre-causal correlation
    independent = np.abs(corr_pre) < 0.5
    print(f"  Clocks are independent before causal contact: {independent}")
    
    return {
        'distance': float(distance),
        'causal_time': float(causal_time),
        'corr_pre': float(corr_pre) if not np.isnan(corr_pre) else 0.0,
        'corr_post': float(corr_post) if not np.isnan(corr_post) else 0.0,
        'independent': bool(independent),
        'history_A': history_A_arr,
        'history_B': history_B_arr,
    }


def test_regime_scaling():
    """
    Test 4: Does clock behavior scale correctly across regimes?
    
    Compare weak, medium, strong energy regimes.
    """
    print("\nTest 4: Regime Scaling")
    print("-" * 50)
    
    results = {}
    
    for regime, amplitude in [('weak', 1.0), ('medium', 4.0), ('strong', 10.0)]:
        sim = EnhancedMediumClockTest(size=80)
        sim.add_pulse([40, 40], amplitude=amplitude)
        
        # Track clocks at two points
        point_1 = (40, 40)  # Center
        point_2 = (60, 40)  # Edge
        
        clock_1 = {'transport': 0.0, 'medium': 0.0}
        clock_2 = {'transport': 0.0, 'medium': 0.0}
        
        for t in range(400):
            sim.step()
            
            c_eff = sim.compute_c_eff()
            
            clock_1['transport'] += c_eff[point_1] * sim.dt
            clock_1['medium'] += (1.0 / sim.tau[point_1]) * sim.dt
            clock_2['transport'] += c_eff[point_2] * sim.dt
            clock_2['medium'] += (1.0 / sim.tau[point_2]) * sim.dt
        
        # Clock ratio between points
        ratio_transport = clock_1['transport'] / (clock_2['transport'] + 1e-10)
        ratio_medium = clock_1['medium'] / (clock_2['medium'] + 1e-10)
        
        results[regime] = {
            'amplitude': amplitude,
            'ratio_transport': float(ratio_transport),
            'ratio_medium': float(ratio_medium),
            'final_tau_center': float(sim.tau[point_1]),
            'final_tau_edge': float(sim.tau[point_2]),
        }
        
        print(f"  {regime:8}: transport ratio={ratio_transport:.3f}, medium ratio={ratio_medium:.3f}")
    
    # Check if medium clock shows stronger regime dependence
    weak_diff = np.abs(results['weak']['ratio_medium'] - 1)
    strong_diff = np.abs(results['strong']['ratio_medium'] - 1)
    
    shows_scaling = strong_diff > weak_diff * 1.5
    print(f"\n  Medium clock shows regime scaling: {shows_scaling}")
    
    return {
        'regimes': results,
        'shows_scaling': bool(shows_scaling),
    }


def run_comprehensive_medium_time_test():
    """
    Main comprehensive test.
    """
    print("=" * 70)
    print("COMPREHENSIVE MEDIUM-STATE EMERGENT TIME TEST v2")
    print("=" * 70)
    print()
    
    results = {}
    
    # Run all tests
    results['algebraic'] = test_non_algebraic_clocks()
    results['improvement'] = test_nontrivial_improvement()
    results['independence'] = test_causal_independence()
    results['scaling'] = test_regime_scaling()
    
    # Final verdict using decision rules
    print("\n" + "=" * 70)
    print("FINAL ANALYSIS")
    print("=" * 70)
    
    # Check each criterion
    not_algebraic = not results['algebraic']['is_trivial']
    nontrivial = results['improvement']['nontrivial_medium'] or results['improvement']['nontrivial_hybrid']
    independent = results['independence']['independent']
    scales = results['scaling']['shows_scaling']
    
    print(f"\n  1. Clock is NOT algebraic restatement of τ: {not_algebraic}")
    print(f"  2. Improvement is nontrivial (>20%): {nontrivial}")
    print(f"  3. Clocks are causally independent: {independent}")
    print(f"  4. Clock shows regime scaling: {scales}")
    
    score = sum([not_algebraic, nontrivial, independent, scales])
    
    print(f"\n  Score: {score}/4")
    
    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    if score >= 3:
        verdict = "STRONG: τ-based clocks provide a better candidate temporal variable"
        verdict_short = "STRONG_IMPROVEMENT"
    elif score >= 2:
        verdict = "PRELIMINARY: Dynamical medium improves clock structure, but temporal emergence remains partial"
        verdict_short = "PRELIMINARY_IMPROVEMENT"
    else:
        verdict = "WEAK: Medium architecture fixed spatial/causal structure; time remains open"
        verdict_short = "WEAK_NO_CLEAR_IMPROVEMENT"
    
    print(f"\n>>> {verdict}")
    
    results['verdict'] = verdict
    results['verdict_short'] = verdict_short
    results['score'] = score
    results['criteria'] = {
        'not_algebraic': bool(not_algebraic),
        'nontrivial': bool(nontrivial),
        'independent': bool(independent),
        'scales': bool(scales),
    }
    
    # Plotting
    fig = plt.figure(figsize=(16, 12))
    
    # Test 1: Algebraic independence
    ax = fig.add_subplot(2, 3, 1)
    alg = results['algebraic']
    ax.plot(alg['tau_history'], label='τ', linewidth=2)
    ax.plot(alg['medium_history'] / np.max(alg['medium_history']) * np.max(alg['tau_history']), 
            '--', label='Medium clock (scaled)', linewidth=2)
    ax.set_xlabel('Step')
    ax.set_ylabel('Value')
    ax.set_title(f"τ vs Medium Clock\n(corr={alg['corr_medium_tau']:.2f})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Test 2: Synchronization improvement
    ax = fig.add_subplot(2, 3, 2)
    imp = results['improvement']
    cv_vals = [imp['sync_cv'][k] for k in ['raw', 'transport', 'medium', 'hybrid']]
    colors = ['gray', 'blue', 'green' if imp['nontrivial_medium'] else 'red', 
              'green' if imp['nontrivial_hybrid'] else 'orange']
    ax.bar(['raw', 'transport', 'medium', 'hybrid'], cv_vals, color=colors)
    ax.set_ylabel('Coefficient of Variation')
    ax.set_title(f"Sync Quality (lower=better)\nMedium improvement: {imp['improvement_medium']:.1f}%")
    ax.grid(True, alpha=0.3, axis='y')
    
    # Test 3: Causal independence
    ax = fig.add_subplot(2, 3, 3)
    ind = results['independence']
    ax.bar(['Pre-causal', 'Post-causal'], [np.abs(ind['corr_pre']), np.abs(ind['corr_post'])],
           color=['green' if np.abs(ind['corr_pre']) < 0.5 else 'red', 'blue'])
    ax.axhline(y=0.5, color='k', linestyle='--', alpha=0.5, label='Independence threshold')
    ax.set_ylabel('|Correlation|')
    ax.set_title(f"Causal Independence\n(pre={ind['corr_pre']:.2f})")
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Test 4: Regime scaling
    ax = fig.add_subplot(2, 3, 4)
    sc = results['scaling']['regimes']
    regimes = ['weak', 'medium', 'strong']
    transport_ratios = [sc[r]['ratio_transport'] for r in regimes]
    medium_ratios = [sc[r]['ratio_medium'] for r in regimes]
    x = np.arange(len(regimes))
    width = 0.35
    ax.bar(x - width/2, transport_ratios, width, label='Transport', color='blue')
    ax.bar(x + width/2, medium_ratios, width, label='Medium', color='green')
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(regimes)
    ax.set_ylabel('Center/Edge Clock Ratio')
    ax.set_title(f"Regime Scaling\n(shows scaling: {results['scaling']['shows_scaling']})")
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Summary scorecard
    ax = fig.add_subplot(2, 3, 5)
    criteria = ['Not Algebraic', 'Nontrivial\nImprovement', 'Causally\nIndependent', 'Shows\nScaling']
    scores = [not_algebraic, nontrivial, independent, scales]
    colors = ['green' if s else 'red' for s in scores]
    ax.bar(criteria, [1 if s else 0 for s in scores], color=colors)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel('Pass/Fail')
    ax.set_title(f'Decision Criteria Score: {score}/4')
    
    # Final verdict text
    ax = fig.add_subplot(2, 3, 6)
    ax.axis('off')
    
    summary = f"""
MEDIUM-STATE EMERGENT TIME v2
=============================

Decision Criteria:
  1. Not algebraic restatement: {'PASS' if not_algebraic else 'FAIL'}
  2. Nontrivial improvement:    {'PASS' if nontrivial else 'FAIL'}
  3. Causally independent:      {'PASS' if independent else 'FAIL'}
  4. Shows regime scaling:      {'PASS' if scales else 'FAIL'}

Score: {score}/4

Improvement over transport:
  Medium: {imp['improvement_medium']:.1f}%
  Hybrid: {imp['improvement_hybrid']:.1f}%

VERDICT:
{verdict}
"""
    
    color = 'lightgreen' if score >= 3 else ('lightyellow' if score >= 2 else 'lightcoral')
    ax.text(0.1, 0.9, summary, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.5))
    
    plt.suptitle(f'MEDIUM-STATE EMERGENT TIME: {verdict_short}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/medium_time_v2.png', dpi=150, bbox_inches='tight')
    print("\nSaved medium_time_v2.png")
    
    # Save JSON (excluding numpy arrays)
    summary_json = {
        'verdict': verdict,
        'verdict_short': verdict_short,
        'score': score,
        'criteria': results['criteria'],
        'algebraic_correlation': float(results['algebraic']['corr_medium_tau']),
        'improvement_medium_pct': float(results['improvement']['improvement_medium']),
        'improvement_hybrid_pct': float(results['improvement']['improvement_hybrid']),
        'pre_causal_correlation': float(results['independence']['corr_pre']),
        'shows_scaling': bool(results['scaling']['shows_scaling']),
    }
    
    with open('/app/backend/qmrt_topology/medium_time_v2_results.json', 'w') as f:
        json.dump(summary_json, f, indent=2)
    print("Saved medium_time_v2_results.json")
    
    return results


if __name__ == "__main__":
    results = run_comprehensive_medium_time_test()
