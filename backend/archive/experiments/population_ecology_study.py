"""
Population Ecology Study — Stage 1: Regional Statistics
========================================================

Question: Does the attractor create genuinely different "ecological niches"?

Measurements:
- Local density by region
- Nearest-neighbor spacing
- Fluctuation amplitude
- Birth/death/regeneration rates by region

This tells us whether the attractor just biases WHERE defects appear,
or creates qualitatively different population regimes.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.spatial.distance import pdist
from typing import Dict, List, Tuple
import time


class PopulationEcologySimulator:
    """
    3D simulator instrumented for population ecology measurements.
    """
    
    def __init__(
        self,
        size: int = 48,
        coupling_center: float = 0.7,
        coupling_edge: float = 0.2,
        gamma: float = 0.007,
    ):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        self.gamma = gamma
        
        # Fields
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        
        # Coupling field
        self.coupling = self._create_coupling()
        
        # Region masks
        self.interior_mask = self._create_region_mask('interior')
        self.periphery_mask = self._create_region_mask('periphery')
        
        # Tracking
        self.step_count = 0
        self.previous_defects = set()
    
    def _create_coupling(self) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        transition_w = 8
        
        coupling = np.zeros((self.size, self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    dist = r[i, j, k]
                    if dist <= interior_r:
                        coupling[i, j, k] = self.coupling_center
                    elif dist >= interior_r + transition_w:
                        coupling[i, j, k] = self.coupling_edge
                    else:
                        t = (dist - interior_r) / transition_w
                        blend = 0.5 * (1 - np.cos(np.pi * t))
                        coupling[i, j, k] = self.coupling_center + blend * (self.coupling_edge - self.coupling_center)
        return coupling
    
    def _create_region_mask(self, region: str) -> np.ndarray:
        x, y, z = np.meshgrid(
            np.arange(self.size), np.arange(self.size), np.arange(self.size),
            indexing='ij'
        )
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        transition_w = 8
        
        if region == 'interior':
            return r <= interior_r
        elif region == 'periphery':
            return r > interior_r + transition_w
        else:  # transition
            return (r > interior_r) & (r <= interior_r + transition_w)
    
    def get_region(self, x: int, y: int, z: int) -> str:
        center = self.size / 2
        r = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
        interior_r = self.size * 0.25
        if r <= interior_r:
            return 'interior'
        elif r <= interior_r + 8:
            return 'transition'
        return 'periphery'
    
    def step(self, dt: float = 0.04):
        self.step_count += 1
        
        def lap(f):
            return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                    np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                    np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f)
        
        c_eff = 2.0
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff**2 * lap_r - self.gamma * self.psi_r_dot
        acc_i = c_eff**2 * lap_i - self.gamma * self.psi_i_dot
        
        # Channel protection
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
    
    def detect_defects(self, threshold: float = 0.4) -> List[Tuple[int, int, int]]:
        """Detect defect positions."""
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        low_amp = amp < threshold
        labeled, n = label(low_amp)
        
        defects = []
        for i in range(1, n + 1):
            component = (labeled == i)
            if np.sum(component) < 5:
                continue
            coords = np.where(component)
            cx = int(np.mean(coords[0]))
            cy = int(np.mean(coords[1]))
            cz = int(np.mean(coords[2]))
            defects.append((cx, cy, cz))
        
        return defects
    
    def compute_regional_statistics(self, defects: List[Tuple[int, int, int]]) -> Dict:
        """Compute population statistics by region."""
        interior_defects = []
        periphery_defects = []
        
        for d in defects:
            region = self.get_region(d[0], d[1], d[2])
            if region == 'interior':
                interior_defects.append(d)
            elif region == 'periphery':
                periphery_defects.append(d)
        
        # Volume calculations
        interior_vol = np.sum(self.interior_mask)
        periphery_vol = np.sum(self.periphery_mask)
        
        # Densities
        interior_density = len(interior_defects) / interior_vol if interior_vol > 0 else 0
        periphery_density = len(periphery_defects) / periphery_vol if periphery_vol > 0 else 0
        
        # Nearest neighbor spacing (within each region)
        interior_nn = self._compute_nn_spacing(interior_defects) if len(interior_defects) >= 2 else None
        periphery_nn = self._compute_nn_spacing(periphery_defects) if len(periphery_defects) >= 2 else None
        
        return {
            'interior_count': len(interior_defects),
            'periphery_count': len(periphery_defects),
            'interior_density': interior_density,
            'periphery_density': periphery_density,
            'interior_nn_spacing': interior_nn,
            'periphery_nn_spacing': periphery_nn,
            'total_count': len(defects),
        }
    
    def _compute_nn_spacing(self, defects: List[Tuple[int, int, int]]) -> float:
        """Compute mean nearest-neighbor spacing."""
        if len(defects) < 2:
            return None
        
        positions = np.array(defects)
        nn_distances = []
        
        for i, pos in enumerate(positions):
            distances = np.sqrt(np.sum((positions - pos)**2, axis=1))
            distances[i] = np.inf  # Exclude self
            nn_distances.append(np.min(distances))
        
        return np.mean(nn_distances)
    
    def track_events(self, current_defects: List[Tuple[int, int, int]]) -> Dict:
        """Track birth/death events between frames."""
        current_set = set(current_defects)
        
        # Simple tracking: defects within 3 units are "same"
        def find_match(d, defect_set, radius=3):
            for other in defect_set:
                dist = np.sqrt(sum((a - b)**2 for a, b in zip(d, other)))
                if dist <= radius:
                    return other
            return None
        
        births = 0
        deaths = 0
        persisted = 0
        
        for d in current_defects:
            if find_match(d, self.previous_defects) is None:
                births += 1
            else:
                persisted += 1
        
        for d in self.previous_defects:
            if find_match(d, current_set) is None:
                deaths += 1
        
        self.previous_defects = current_set
        
        return {'births': births, 'deaths': deaths, 'persisted': persisted}
    
    def initialize_with_noise(self, noise_level: float = 0.03):
        """Initialize with noise to seed defect formation."""
        np.random.seed(42)
        self.psi_r += noise_level * np.random.randn(self.size, self.size, self.size)
        self.psi_i += noise_level * np.random.randn(self.size, self.size, self.size)


def run_regional_statistics_test(steps: int = 1500, sample_interval: int = 25):
    """
    Stage 1: Measure regional population statistics.
    """
    print("=" * 70)
    print("POPULATION ECOLOGY — STAGE 1: REGIONAL STATISTICS")
    print("=" * 70)
    print()
    print("Question: Does the attractor create different ecological niches?")
    print()
    
    sim = PopulationEcologySimulator(size=48, coupling_center=0.7, coupling_edge=0.2)
    sim.initialize_with_noise(noise_level=0.03)
    
    # Data collection
    time_points = []
    interior_counts = []
    periphery_counts = []
    interior_densities = []
    periphery_densities = []
    interior_nn_spacings = []
    periphery_nn_spacings = []
    
    interior_births = []
    interior_deaths = []
    periphery_births = []
    periphery_deaths = []
    
    print("Running simulation...")
    start_time = time.time()
    
    prev_interior = set()
    prev_periphery = set()
    
    for step in range(steps):
        sim.step()
        
        if step % sample_interval == 0:
            defects = sim.detect_defects()
            stats = sim.compute_regional_statistics(defects)
            
            time_points.append(step)
            interior_counts.append(stats['interior_count'])
            periphery_counts.append(stats['periphery_count'])
            interior_densities.append(stats['interior_density'])
            periphery_densities.append(stats['periphery_density'])
            
            if stats['interior_nn_spacing'] is not None:
                interior_nn_spacings.append(stats['interior_nn_spacing'])
            if stats['periphery_nn_spacing'] is not None:
                periphery_nn_spacings.append(stats['periphery_nn_spacing'])
            
            # Track regional events
            current_interior = set(d for d in defects if sim.get_region(*d) == 'interior')
            current_periphery = set(d for d in defects if sim.get_region(*d) == 'periphery')
            
            # Count births/deaths by region
            int_births = len(current_interior - prev_interior)
            int_deaths = len(prev_interior - current_interior)
            per_births = len(current_periphery - prev_periphery)
            per_deaths = len(prev_periphery - current_periphery)
            
            interior_births.append(int_births)
            interior_deaths.append(int_deaths)
            periphery_births.append(per_births)
            periphery_deaths.append(per_deaths)
            
            prev_interior = current_interior
            prev_periphery = current_periphery
            
            if step % 250 == 0:
                print(f"Step {step:4d}: interior={stats['interior_count']:3d}, "
                      f"periphery={stats['periphery_count']:3d}, "
                      f"total={stats['total_count']:3d}")
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f}s")
    
    # Analysis
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    # Late-time statistics (last quarter)
    n = len(time_points)
    late_start = 3 * n // 4
    
    late_int_count = np.mean(interior_counts[late_start:])
    late_per_count = np.mean(periphery_counts[late_start:])
    late_int_density = np.mean(interior_densities[late_start:])
    late_per_density = np.mean(periphery_densities[late_start:])
    
    print(f"\n1. POPULATION BY REGION (late-time averages)")
    print(f"   Interior: {late_int_count:.1f} defects, density={late_int_density:.6f}")
    print(f"   Periphery: {late_per_count:.1f} defects, density={late_per_density:.6f}")
    
    if late_per_density > 0:
        density_ratio = late_int_density / late_per_density
        print(f"   Density ratio (interior/periphery): {density_ratio:.2f}×")
    
    # Fluctuations
    int_std = np.std(interior_counts[late_start:])
    per_std = np.std(periphery_counts[late_start:])
    int_cv = int_std / (late_int_count + 0.01)
    per_cv = per_std / (late_per_count + 0.01)
    
    print(f"\n2. FLUCTUATION AMPLITUDE")
    print(f"   Interior: std={int_std:.2f}, CV={int_cv:.2f}")
    print(f"   Periphery: std={per_std:.2f}, CV={per_cv:.2f}")
    
    # Nearest-neighbor spacing
    if interior_nn_spacings and periphery_nn_spacings:
        avg_int_nn = np.mean(interior_nn_spacings)
        avg_per_nn = np.mean(periphery_nn_spacings)
        print(f"\n3. NEAREST-NEIGHBOR SPACING")
        print(f"   Interior: {avg_int_nn:.2f} grid units")
        print(f"   Periphery: {avg_per_nn:.2f} grid units")
        
        if avg_int_nn > 0:
            spacing_ratio = avg_per_nn / avg_int_nn
            print(f"   Ratio (periphery/interior): {spacing_ratio:.2f}×")
    
    # Birth/death rates
    avg_int_births = np.mean(interior_births[late_start:])
    avg_int_deaths = np.mean(interior_deaths[late_start:])
    avg_per_births = np.mean(periphery_births[late_start:])
    avg_per_deaths = np.mean(periphery_deaths[late_start:])
    
    print(f"\n4. EVENT RATES (per sample interval)")
    print(f"   Interior: births={avg_int_births:.2f}, deaths={avg_int_deaths:.2f}")
    print(f"   Periphery: births={avg_per_births:.2f}, deaths={avg_per_deaths:.2f}")
    
    # Turnover rates (births+deaths relative to population)
    int_turnover = (avg_int_births + avg_int_deaths) / (late_int_count + 0.01)
    per_turnover = (avg_per_births + avg_per_deaths) / (late_per_count + 0.01)
    
    print(f"\n5. TURNOVER RATE (events/population)")
    print(f"   Interior: {int_turnover:.3f}")
    print(f"   Periphery: {per_turnover:.3f}")
    
    # Interpretation
    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print()
    
    findings = []
    
    if density_ratio > 2:
        findings.append(f"✓ Interior density {density_ratio:.1f}× higher → attractor concentrates population")
    
    if int_cv < per_cv * 0.8:
        findings.append("✓ Interior has lower CV → more stable population")
    elif per_cv < int_cv * 0.8:
        findings.append("✓ Periphery has lower CV → more stable population")
    
    if interior_nn_spacings and periphery_nn_spacings:
        if avg_int_nn < avg_per_nn * 0.8:
            findings.append("✓ Interior has tighter spacing → higher local density")
    
    if int_turnover < per_turnover * 0.8:
        findings.append("✓ Interior has lower turnover → more stable individuals")
    elif per_turnover < int_turnover * 0.8:
        findings.append("✓ Periphery has lower turnover → more stable individuals")
    
    if findings:
        print("KEY FINDINGS:")
        for f in findings:
            print(f"  {f}")
    else:
        print("No strong regional differences detected.")
    
    return {
        'interior_counts': interior_counts,
        'periphery_counts': periphery_counts,
        'interior_densities': interior_densities,
        'periphery_densities': periphery_densities,
        'interior_nn_spacings': interior_nn_spacings,
        'periphery_nn_spacings': periphery_nn_spacings,
        'density_ratio': density_ratio if 'density_ratio' in dir() else None,
        'interior_cv': int_cv,
        'periphery_cv': per_cv,
        'interior_turnover': int_turnover,
        'periphery_turnover': per_turnover,
    }


if __name__ == "__main__":
    results = run_regional_statistics_test(steps=1500, sample_interval=25)
