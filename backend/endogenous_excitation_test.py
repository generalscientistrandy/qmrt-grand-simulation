"""
Endogenous Excitation / Self-Driving Test
==========================================

CENTRAL QUESTION:
Can the medium sustain or regenerate its scaffold through endogenous feedback 
after external driving is reduced or removed?

This tests whether the scaffold is:
- Purely externally maintained (passive under forcing)
- Or can become autocatalytic / self-reinforcing / self-maintaining

TEST STAGES:

Stage 1: Build the scaffold
- Run with normal external driving until strong peak-state scaffold exists

Stage 2: Modify driving
- Test A: Hard cutoff (injection → 0)
- Test B: Slow taper (injection gradually decreases)  
- Test C: Feedback mode (driving replaced by function of internal state)

Stage 3: Measure sustainability
- Population trajectory
- Effective dimension
- Triangles / edges / correlation
- Decay rate or oscillation persistence
- Time-to-collapse (if applicable)

OUTCOMES:
1. Immediate decay → no self-driving, purely external maintenance
2. Delayed decay → internal memory, partial self-driving but not sustainable
3. Oscillatory self-maintenance → endogenous regeneration (significant)
4. Stable under internal feedback → strongest case, internal organizational control

TERMINOLOGY:
- "Endogenous excitation" not "self-driving" (avoids strong ontological claims)
- "Autocatalytic maintenance" for feedback-driven persistence
- "Decay half-life" for coasting time after cutoff
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Callable
import json


class EndogenousExcitationSimulator:
    """
    Simulator with configurable driving modes for testing self-maintenance.
    
    Driving modes:
    - 'external': Fixed injection interval (standard)
    - 'cutoff': No injection after specified step
    - 'taper': Injection probability decreases over time
    - 'feedback': Injection triggered by internal state (population deficit, etc.)
    """
    
    def __init__(self, size: int = 48):
        self.size = size
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        self.coupling = self._create_coupling()
        self.step_count = 0
        
        # Driving configuration
        self.driving_mode = 'external'
        self.injection_interval = 50
        self.injection_count = 3
        self.cutoff_step = None
        self.taper_start = None
        self.taper_rate = 0.001  # Probability decrease per step
        self.feedback_threshold = 100  # Target population for feedback mode
        
        # Tracking
        self.injections_this_run = 0
        self.last_population = 0
        
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = 0.7
                    elif dist >= interior_r + 10.0:
                        coupling[i, j, k] = 0.2
                    else:
                        t = (dist - interior_r) / 10.0
                        coupling[i, j, k] = 0.7 + 0.5 * (1 - np.cos(np.pi * t)) * (0.2 - 0.7)
        return coupling
    
    def inject_vortex(self, cx: int, cy: int):
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        r = np.sqrt((x - cx)**2 + (y - cy)**2) + 0.1
        theta = np.arctan2(y - cy, x - cx)
        vortex = np.tanh(r / 3) * np.exp(1j * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)
    
    def inject_random_vortices(self, n: int = None):
        if n is None:
            n = self.injection_count
        center = self.size // 2
        for _ in range(n):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.size * 0.20)
            cx = int(np.clip(center + radius * np.cos(angle), 5, self.size - 5))
            cy = int(np.clip(center + radius * np.sin(angle), 5, self.size - 5))
            self.inject_vortex(cx, cy)
        self.injections_this_run += n
    
    def should_inject(self) -> bool:
        """Determine whether to inject based on driving mode."""
        
        if self.driving_mode == 'external':
            return self.step_count % self.injection_interval == 0
        
        elif self.driving_mode == 'cutoff':
            if self.cutoff_step is not None and self.step_count >= self.cutoff_step:
                return False
            return self.step_count % self.injection_interval == 0
        
        elif self.driving_mode == 'taper':
            if self.taper_start is None:
                return self.step_count % self.injection_interval == 0
            
            steps_since_taper = self.step_count - self.taper_start
            if steps_since_taper < 0:
                return self.step_count % self.injection_interval == 0
            
            # Probability decreases linearly
            prob = max(0, 1.0 - self.taper_rate * steps_since_taper)
            if self.step_count % self.injection_interval == 0:
                return np.random.random() < prob
            return False
        
        elif self.driving_mode == 'feedback':
            # Inject only if population is below threshold
            if self.last_population < self.feedback_threshold:
                # Inject with probability proportional to deficit
                deficit_ratio = 1 - (self.last_population / self.feedback_threshold)
                prob = min(1.0, deficit_ratio * 0.5)  # Scale down
                return np.random.random() < prob
            return False
        
        return False
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        # Conditional injection based on driving mode
        if self.should_inject():
            self.inject_random_vortices()
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        gamma = 0.007
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = 4.0 * lap_r - gamma * self.psi_r_dot
        acc_i = 4.0 * lap_i - gamma * self.psi_i_dot
        
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
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple]:
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        labeled, n = label(amp < threshold)
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) >= 5:
                coords = np.where(component)
                defects.append((int(np.mean(coords[0])), int(np.mean(coords[1])), int(np.mean(coords[2]))))
        self.last_population = len(defects)
        return defects
    
    def get_channel_strength(self) -> float:
        """Get mean channel assignment (internal organizational state)."""
        return float(np.mean(self.channel_assignment))


def quick_measure(defects, size) -> Dict:
    """Quick measurement for tracking."""
    n = len(defects)
    if n < 10:
        return {'valid': False, 'n': n}
    
    # Sample for efficiency
    max_n = min(n, 100)
    if n > max_n:
        indices = np.random.choice(n, max_n, replace=False)
        sample = [defects[i] for i in indices]
    else:
        sample = defects
        max_n = n
    
    # Build adjacency
    def euclidean_periodic(p1, p2, size):
        d = np.abs(np.array(p1) - np.array(p2))
        d = np.minimum(d, size - d)
        return np.sqrt(np.sum(d**2))
    
    adj = defaultdict(set)
    for i in range(max_n):
        for j in range(i + 1, max_n):
            d = euclidean_periodic(sample[i], sample[j], size)
            if d < 10.0:
                adj[i].add(j)
                adj[j].add(i)
    
    edges = sum(len(adj[i]) for i in range(max_n)) // 2
    
    # Triangles
    triangles = 0
    for node in range(max_n):
        neighbors = list(adj[node])
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adj[neighbors[i]]:
                    triangles += 1
    triangles //= 3
    
    tri_per_node = triangles / max_n if max_n > 0 else 0
    
    return {
        'valid': True,
        'n': n,
        'edges': edges,
        'triangles': triangles,
        'tri_per_node': tri_per_node,
    }


def run_test_a_hard_cutoff():
    """
    Test A: Hard Cutoff
    
    Build scaffold with external driving, then cut off completely.
    Measure: How quickly does the scaffold decay?
    """
    print("=" * 70)
    print("TEST A: HARD CUTOFF")
    print("=" * 70)
    print()
    print("Phase 1: Build scaffold with external driving")
    print("Phase 2: Cut off driving completely")
    print("Phase 3: Track decay")
    print()
    
    sim = EndogenousExcitationSimulator(size=48)
    sim.driving_mode = 'external'
    sim.injection_interval = 50
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    # Dense initial seeding
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    # Phase 1: Build scaffold (2000 steps)
    BUILD_STEPS = 2000
    print(f"Building scaffold for {BUILD_STEPS} steps...")
    
    build_history = []
    for step in range(BUILD_STEPS):
        sim.step()
        if step % 200 == 0:
            defects = sim.detect_defects()
            m = quick_measure(defects, sim.size)
            build_history.append({'step': step, **m})
            print(f"  Step {step}: n={len(defects)}")
    
    # Record state at cutoff
    defects = sim.detect_defects()
    cutoff_state = quick_measure(defects, sim.size)
    print(f"\nState at cutoff: n={cutoff_state['n']}, tri/n={cutoff_state.get('tri_per_node', 0):.2f}")
    
    # Phase 2 & 3: Cut off and track decay
    sim.driving_mode = 'cutoff'
    sim.cutoff_step = sim.step_count  # Cut off now
    
    DECAY_STEPS = 2000
    print(f"\nTracking decay for {DECAY_STEPS} steps after cutoff...")
    
    decay_history = []
    for step in range(DECAY_STEPS):
        sim.step()
        if step % 100 == 0:
            defects = sim.detect_defects()
            m = quick_measure(defects, sim.size)
            decay_history.append({'step_after_cutoff': step, **m})
            print(f"  +{step}: n={len(defects)}")
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    
    # Find decay characteristics
    populations = [d['n'] for d in decay_history if d.get('valid', False) or 'n' in d]
    
    if populations:
        initial_pop = cutoff_state.get('n', populations[0])
        final_pop = populations[-1]
        
        # Find half-life (when population first drops below 50% of initial)
        half_pop = initial_pop / 2
        half_life_step = None
        for d in decay_history:
            if d.get('n', 0) < half_pop:
                half_life_step = d['step_after_cutoff']
                break
        
        # Find collapse point (population < 10)
        collapse_step = None
        for d in decay_history:
            if d.get('n', 0) < 10:
                collapse_step = d['step_after_cutoff']
                break
        
        print(f"Initial population at cutoff: {initial_pop}")
        print(f"Final population: {final_pop}")
        print(f"Half-life (50% decay): {half_life_step if half_life_step else '>'+str(DECAY_STEPS)} steps")
        print(f"Collapse (<10): {collapse_step if collapse_step else '>'+str(DECAY_STEPS)} steps")
        
        # Classify outcome
        print()
        if collapse_step and collapse_step < 200:
            print("OUTCOME: IMMEDIATE DECAY")
            print("  → No self-driving capacity")
            print("  → Scaffold is purely externally maintained")
        elif collapse_step and collapse_step < 1000:
            print("OUTCOME: DELAYED DECAY")
            print("  → Some internal memory/coasting")
            print("  → Partial self-driving but not sustainable")
        elif collapse_step:
            print("OUTCOME: SLOW DECAY")
            print("  → Significant internal memory")
            print("  → Medium retains organization for extended period")
        else:
            print("OUTCOME: PERSISTENT (no collapse in test window)")
            print("  → Strong candidate for endogenous regeneration")
            print("  → Further investigation needed")
    
    return {
        'test': 'hard_cutoff',
        'build_steps': BUILD_STEPS,
        'decay_steps': DECAY_STEPS,
        'cutoff_state': cutoff_state,
        'decay_history': decay_history,
    }


def run_test_b_taper():
    """
    Test B: Gradual Taper
    
    Build scaffold, then gradually reduce injection probability.
    Does gradual reduction preserve organization longer?
    """
    print()
    print("=" * 70)
    print("TEST B: GRADUAL TAPER")
    print("=" * 70)
    print()
    
    sim = EndogenousExcitationSimulator(size=48)
    sim.driving_mode = 'external'
    sim.injection_interval = 50
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    # Build phase
    BUILD_STEPS = 2000
    print(f"Building scaffold for {BUILD_STEPS} steps...")
    for step in range(BUILD_STEPS):
        sim.step()
        if step % 500 == 0:
            defects = sim.detect_defects()
            print(f"  Step {step}: n={len(defects)}")
    
    defects = sim.detect_defects()
    cutoff_state = quick_measure(defects, sim.size)
    print(f"\nState at taper start: n={cutoff_state['n']}")
    
    # Taper phase
    sim.driving_mode = 'taper'
    sim.taper_start = sim.step_count
    sim.taper_rate = 0.0005  # Slow taper: ~2000 steps to reach 0
    
    TAPER_STEPS = 2500
    print(f"\nTapering over {TAPER_STEPS} steps (rate={sim.taper_rate})...")
    
    taper_history = []
    injections_at_start = sim.injections_this_run
    
    for step in range(TAPER_STEPS):
        sim.step()
        if step % 200 == 0:
            defects = sim.detect_defects()
            m = quick_measure(defects, sim.size)
            inj_since_taper = sim.injections_this_run - injections_at_start
            taper_history.append({
                'step_after_taper': step, 
                'injections': inj_since_taper,
                **m
            })
            print(f"  +{step}: n={len(defects)}, injections_so_far={inj_since_taper}")
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    
    populations = [d['n'] for d in taper_history if 'n' in d]
    initial = cutoff_state.get('n', populations[0] if populations else 0)
    final = populations[-1] if populations else 0
    
    print(f"Initial population: {initial}")
    print(f"Final population: {final}")
    print(f"Total injections during taper: {sim.injections_this_run - injections_at_start}")
    
    # Compare to hard cutoff
    print()
    if final > 10:
        print("OUTCOME: SCAFFOLD PERSISTS UNDER TAPER")
        print("  → Gradual reduction allows adaptation")
    else:
        print("OUTCOME: SCAFFOLD COLLAPSES DESPITE TAPER")
        print("  → Gradual reduction does not prevent decay")
    
    return {
        'test': 'taper',
        'taper_rate': sim.taper_rate,
        'cutoff_state': cutoff_state,
        'taper_history': taper_history,
    }


def run_test_c_feedback():
    """
    Test C: Internal Feedback Driving
    
    Replace external injection with population-deficit-driven injection.
    Can the medium regulate its own driving based on internal state?
    """
    print()
    print("=" * 70)
    print("TEST C: INTERNAL FEEDBACK DRIVING")
    print("=" * 70)
    print()
    print("External driving replaced by population-deficit feedback:")
    print("  Injection triggered when population < threshold")
    print("  Injection probability ∝ deficit ratio")
    print()
    
    sim = EndogenousExcitationSimulator(size=48)
    sim.driving_mode = 'external'
    sim.injection_interval = 50
    
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(48, 48, 48)
    sim.psi_i += 0.04 * np.random.randn(48, 48, 48)
    
    center = 24
    for i in range(-4, 5):
        for j in range(-4, 5):
            if abs(i) + abs(j) <= 4:
                sim.inject_vortex(center + i * 3, center + j * 3)
    
    # Build phase with external driving
    BUILD_STEPS = 2000
    print(f"Building scaffold for {BUILD_STEPS} steps (external driving)...")
    for step in range(BUILD_STEPS):
        sim.step()
        if step % 500 == 0:
            defects = sim.detect_defects()
            print(f"  Step {step}: n={len(defects)}")
    
    defects = sim.detect_defects()
    cutoff_state = quick_measure(defects, sim.size)
    print(f"\nState before feedback mode: n={cutoff_state['n']}")
    
    # Switch to feedback mode
    sim.driving_mode = 'feedback'
    sim.feedback_threshold = 150  # Target population
    
    FEEDBACK_STEPS = 2000
    print(f"\nRunning {FEEDBACK_STEPS} steps in feedback mode (target={sim.feedback_threshold})...")
    
    feedback_history = []
    injections_at_start = sim.injections_this_run
    
    for step in range(FEEDBACK_STEPS):
        sim.step()
        if step % 200 == 0:
            defects = sim.detect_defects()
            m = quick_measure(defects, sim.size)
            inj_since_feedback = sim.injections_this_run - injections_at_start
            feedback_history.append({
                'step_in_feedback': step,
                'injections': inj_since_feedback,
                **m
            })
            print(f"  +{step}: n={len(defects)}, feedback_injections={inj_since_feedback}")
    
    # Analysis
    print()
    print("-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    
    populations = [d['n'] for d in feedback_history if 'n' in d]
    
    if populations:
        mean_pop = np.mean(populations)
        pop_std = np.std(populations)
        final_pop = populations[-1]
        total_feedback_injections = sim.injections_this_run - injections_at_start
        
        print(f"Mean population under feedback: {mean_pop:.1f} ± {pop_std:.1f}")
        print(f"Target population: {sim.feedback_threshold}")
        print(f"Total feedback-triggered injections: {total_feedback_injections}")
        
        # Compare to external driving rate
        external_rate = (BUILD_STEPS / sim.injection_interval) * 3  # Expected external injections
        feedback_rate = total_feedback_injections
        
        print(f"External driving equivalent: ~{external_rate:.0f} injections per {BUILD_STEPS} steps")
        print(f"Feedback driving used: {feedback_rate} injections")
        print(f"Efficiency: {feedback_rate/external_rate*100:.1f}% of external rate")
        
        print()
        if mean_pop >= sim.feedback_threshold * 0.7:
            print("OUTCOME: SELF-REGULATED MAINTENANCE")
            print("  → Internal feedback successfully maintains scaffold")
            print("  → Medium can replace some external driving with internal control")
            if feedback_rate < external_rate * 0.5:
                print("  → AND does so more efficiently than constant external driving!")
        elif mean_pop >= 50:
            print("OUTCOME: PARTIAL SELF-REGULATION")
            print("  → Feedback maintains reduced population")
            print("  → Some internal organizational control exists")
        else:
            print("OUTCOME: FEEDBACK INSUFFICIENT")
            print("  → Internal feedback cannot maintain scaffold")
            print("  → System requires stronger external driving")
    
    return {
        'test': 'feedback',
        'feedback_threshold': sim.feedback_threshold,
        'cutoff_state': cutoff_state,
        'feedback_history': feedback_history,
    }


def run_endogenous_excitation_study():
    """
    Run complete endogenous excitation study.
    """
    print()
    print("=" * 75)
    print("  ENDOGENOUS EXCITATION / SELF-DRIVING TEST SUITE")
    print("=" * 75)
    print()
    print("Central question:")
    print("  Can the medium sustain or regenerate its scaffold through")
    print("  endogenous feedback after external driving is reduced or removed?")
    print()
    
    results = {}
    
    # Test A: Hard Cutoff
    results['test_a'] = run_test_a_hard_cutoff()
    
    # Test B: Gradual Taper  
    results['test_b'] = run_test_b_taper()
    
    # Test C: Internal Feedback
    results['test_c'] = run_test_c_feedback()
    
    # Summary
    print()
    print("=" * 75)
    print("SUMMARY: ENDOGENOUS EXCITATION CAPACITY")
    print("=" * 75)
    print()
    print("Test A (Hard Cutoff):   Does scaffold coast or collapse immediately?")
    print("Test B (Gradual Taper): Does slow reduction preserve organization?")
    print("Test C (Feedback):      Can internal state replace external driving?")
    print()
    
    # Save results
    output_path = '/app/backend/qmrt_topology/papers/endogenous_excitation_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    results = run_endogenous_excitation_study()
