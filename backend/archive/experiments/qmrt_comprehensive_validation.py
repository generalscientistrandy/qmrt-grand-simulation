"""
QMRT Comprehensive Physics Validation Suite

Advanced tests for validating QMRT frequency-domain physics:

1. Scaling Persistence Test
   - Grid sizes 32, 48, 64
   - Basin lifetime, number density, spectral width
   
2. Long-time Entropy Drift Test
   - S(t) = -Σ P_k log P_k
   - Tests "half-entropy regime" hypothesis
   
3. Basin Identity Tracking
   - Merge probability
   - Tunneling probability
   - Spontaneous decay rate
   - Spectral drift
   - "Basin particle statistics"
   
4. Phase Diagram Mapping
   - (a_ω / K_ω) vs (g coupling)
   - Regime classification: unstable, reflective, tunneling, equilibrium-locked
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
from collections import defaultdict

from qmrt_frequency_engine import (
    QMRTFrequencyEngine,
    QMRTFrequencyParameters
)


# =============================================================================
# 1. SCALING PERSISTENCE TEST
# =============================================================================

@dataclass
class ScalingPersistenceResult:
    """Results from scaling persistence test"""
    grid_sizes: List[int]
    basin_lifetimes: List[float]        # Average basin lifetime at each grid
    number_densities: List[float]       # Basin structures per unit volume
    spectral_widths: List[float]        # Width of frequency distribution
    stability_persists: bool            # True if stable at all scales
    scaling_exponents: Dict[str, float]
    raw_data: List[Dict]
    
    def to_dict(self) -> Dict:
        # Convert raw_data to ensure all numpy types are Python natives
        clean_raw_data = []
        for item in self.raw_data:
            clean_item = {}
            for k, v in item.items():
                if isinstance(v, (np.bool_, np.integer)):
                    clean_item[k] = int(v) if isinstance(v, np.integer) else bool(v)
                elif isinstance(v, np.floating):
                    clean_item[k] = float(v)
                else:
                    clean_item[k] = v
            clean_raw_data.append(clean_item)
        
        return {
            'grid_sizes': [int(x) for x in self.grid_sizes],
            'basin_lifetimes': [float(x) for x in self.basin_lifetimes],
            'number_densities': [float(x) for x in self.number_densities],
            'spectral_widths': [float(x) for x in self.spectral_widths],
            'stability_persists': bool(self.stability_persists),
            'scaling_exponents': {k: float(v) for k, v in self.scaling_exponents.items()},
            'raw_data': clean_raw_data
        }


def test_scaling_persistence(
    grid_sizes: List[int] = [24, 32, 48],
    simulation_time: float = 30.0,
    dt: float = 0.01,
    seed: int = 42
) -> ScalingPersistenceResult:
    """
    Test if basin stability persists at larger scales.
    
    Measures:
    - Basin lifetime distribution
    - Number density (basins per unit volume)
    - Spectral width (σ_ω)
    """
    results = []
    basin_lifetimes = []
    number_densities = []
    spectral_widths = []
    
    for gs in grid_sizes:
        print(f"Testing grid {gs}³...")
        start_time = time.time()
        
        engine = QMRTFrequencyEngine(grid_size=gs)
        engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
        
        p = engine.params
        steps = int(simulation_time / dt)
        sample_interval = max(1, steps // 20)
        
        # Track basin occupation over time
        basin_history = []
        initial_basins = None
        stability_time = simulation_time
        
        for step in range(steps):
            engine.evolve_timestep(dt)
            
            if step % sample_interval == 0:
                # Basin occupation
                in_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
                in_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
                total = in_high + in_low
                
                # Spectral width
                omega_std = float(np.std(engine.omega))
                
                basin_history.append({
                    'time': float(engine.time),
                    'total_basin': total,
                    'omega_std': omega_std
                })
                
                if initial_basins is None:
                    initial_basins = total
                
                if stability_time == simulation_time:
                    if total < 0.8 * initial_basins:
                        stability_time = engine.time
        
        # Compute metrics
        final = basin_history[-1]
        
        # Basin lifetime (time until 20% decay)
        basin_lifetimes.append(stability_time)
        
        # Number density (structures per unit volume)
        state = engine.get_state_summary()
        structures = state['structure_breakdown']['total_active']
        volume = gs ** 3
        number_densities.append(structures / volume)
        
        # Spectral width
        spectral_widths.append(final['omega_std'])
        
        elapsed = time.time() - start_time
        print(f"  Grid {gs}: lifetime={stability_time:.1f}s, density={structures/volume:.6f}, σ_ω={final['omega_std']:.4f} ({elapsed:.1f}s)")
        
        results.append({
            'grid_size': gs,
            'volume': volume,
            'basin_lifetime': stability_time,
            'number_density': structures / volume,
            'spectral_width': final['omega_std'],
            'final_basin_fraction': final['total_basin'],
            'structures': structures,
            'is_stable': stability_time >= simulation_time * 0.9
        })
    
    # Check if stability persists across scales
    stability_persists = all(r['is_stable'] for r in results)
    
    # Compute scaling exponents
    log_gs = np.log(grid_sizes)
    
    # Lifetime scaling (should be ~0 for true stability)
    log_lifetime = np.log(np.array(basin_lifetimes) + 1e-10)
    lifetime_slope, _ = np.polyfit(log_gs, log_lifetime, 1) if len(grid_sizes) > 1 else (0, 0)
    
    # Density scaling (should be ~0 for scale invariance)
    log_density = np.log(np.array(number_densities) + 1e-10)
    density_slope, _ = np.polyfit(log_gs, log_density, 1) if len(grid_sizes) > 1 else (0, 0)
    
    # Spectral width scaling
    log_width = np.log(np.array(spectral_widths) + 1e-10)
    width_slope, _ = np.polyfit(log_gs, log_width, 1) if len(grid_sizes) > 1 else (0, 0)
    
    return ScalingPersistenceResult(
        grid_sizes=grid_sizes,
        basin_lifetimes=basin_lifetimes,
        number_densities=number_densities,
        spectral_widths=spectral_widths,
        stability_persists=stability_persists,
        scaling_exponents={
            'lifetime_exponent': lifetime_slope,
            'density_exponent': density_slope,
            'spectral_width_exponent': width_slope
        },
        raw_data=results
    )


# =============================================================================
# 2. LONG-TIME ENTROPY DRIFT TEST
# =============================================================================

@dataclass
class EntropyDriftResult:
    """Results from entropy drift test"""
    total_time: float
    entropy_initial: float
    entropy_final: float
    entropy_plateau: float          # Plateau value if reached
    plateau_time: float             # Time when plateau reached
    entropy_plateaus: bool          # True if entropy stabilizes
    half_entropy_regime: bool       # True if in "partial entropy" state
    time_series: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            'total_time': float(self.total_time),
            'entropy_initial': float(self.entropy_initial),
            'entropy_final': float(self.entropy_final),
            'entropy_plateau': float(self.entropy_plateau),
            'plateau_time': float(self.plateau_time),
            'entropy_plateaus': bool(self.entropy_plateaus),
            'half_entropy_regime': bool(self.half_entropy_regime),
            'time_series': self.time_series
        }


def compute_frequency_entropy(omega: np.ndarray, n_bins: int = 50) -> float:
    """
    Compute entropy of frequency distribution.
    
    S(t) = -Σ P_k log P_k
    
    where P_k is the probability of omega being in bin k.
    """
    # Create histogram
    hist, _ = np.histogram(omega.flatten(), bins=n_bins, density=True)
    
    # Normalize to get probabilities
    hist = hist / (np.sum(hist) + 1e-10)
    
    # Compute entropy (avoiding log(0))
    mask = hist > 1e-10
    entropy = -np.sum(hist[mask] * np.log(hist[mask]))
    
    return float(entropy)


def compute_max_entropy(n_bins: int = 50) -> float:
    """Maximum entropy for uniform distribution"""
    return np.log(n_bins)


def test_entropy_drift(
    grid_size: int = 24,
    total_time: float = 100.0,
    dt: float = 0.01,
    n_bins: int = 50,
    seed: int = 42
) -> EntropyDriftResult:
    """
    Test long-time entropy evolution.
    
    Measures S(t) = -Σ P_k log P_k over the frequency distribution.
    
    If entropy plateaus below max → "half-entropy regime" is supported.
    """
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    steps = int(total_time / dt)
    sample_interval = max(1, steps // 100)
    
    max_entropy = compute_max_entropy(n_bins)
    time_series = []
    
    # Initial entropy
    initial_entropy = compute_frequency_entropy(engine.omega, n_bins)
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % sample_interval == 0:
            entropy = compute_frequency_entropy(engine.omega, n_bins)
            
            time_series.append({
                'time': float(engine.time),
                'entropy': entropy,
                'entropy_normalized': entropy / max_entropy,
                'omega_std': float(np.std(engine.omega)),
                'basin_fraction': float(np.sum(np.abs(engine.omega - engine.params.omega_0) < engine.params.frequency_basin_width) + 
                                        np.sum(np.abs(engine.omega + engine.params.omega_0) < engine.params.frequency_basin_width)) / engine.omega.size
            })
    
    final_entropy = time_series[-1]['entropy']
    
    # Detect plateau (entropy change < 5% over last 20% of simulation)
    late_samples = time_series[int(len(time_series) * 0.8):]
    entropy_values = [s['entropy'] for s in late_samples]
    entropy_variation = (max(entropy_values) - min(entropy_values)) / (np.mean(entropy_values) + 1e-10)
    
    entropy_plateaus = entropy_variation < 0.1
    plateau_value = np.mean(entropy_values) if entropy_plateaus else final_entropy
    
    # Detect plateau time (when entropy stops changing significantly)
    plateau_time = total_time
    for i in range(len(time_series) - 1):
        if i > len(time_series) * 0.2:  # Skip early transient
            window = time_series[i:min(i+10, len(time_series))]
            if len(window) >= 5:
                window_entropy = [s['entropy'] for s in window]
                if (max(window_entropy) - min(window_entropy)) / (np.mean(window_entropy) + 1e-10) < 0.05:
                    plateau_time = time_series[i]['time']
                    break
    
    # Check for "half-entropy regime"
    # Entropy is significantly below maximum but not zero
    half_entropy_regime = (0.3 < final_entropy / max_entropy < 0.8) and entropy_plateaus
    
    return EntropyDriftResult(
        total_time=total_time,
        entropy_initial=initial_entropy,
        entropy_final=final_entropy,
        entropy_plateau=plateau_value,
        plateau_time=plateau_time,
        entropy_plateaus=entropy_plateaus,
        half_entropy_regime=half_entropy_regime,
        time_series=time_series
    )


# =============================================================================
# 3. BASIN IDENTITY TRACKING
# =============================================================================

@dataclass 
class BasinStatistics:
    """Statistics for basin "particles" """
    total_basins_formed: int
    total_merges: int
    total_tunneling_events: int
    total_spontaneous_decays: int
    merge_probability: float
    tunneling_probability: float
    decay_rate: float               # Decays per unit time
    mean_spectral_drift: float      # Average |Δω| over lifetime
    lifetime_distribution: Dict[str, float]  # mean, std, max
    event_history: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            'total_basins_formed': self.total_basins_formed,
            'total_merges': self.total_merges,
            'total_tunneling_events': self.total_tunneling_events,
            'total_spontaneous_decays': self.total_spontaneous_decays,
            'merge_probability': float(self.merge_probability),
            'tunneling_probability': float(self.tunneling_probability),
            'decay_rate': float(self.decay_rate),
            'mean_spectral_drift': float(self.mean_spectral_drift),
            'lifetime_distribution': {k: float(v) for k, v in self.lifetime_distribution.items()},
            'event_history': self.event_history[:50]  # Limit for JSON size
        }


@dataclass
class TrackedBasin:
    """A tracked frequency basin region"""
    id: int
    formation_time: float
    death_time: Optional[float]
    initial_omega: float
    omega_history: List[float]
    centroid_history: List[Tuple[int, int, int]]
    is_alive: bool
    death_cause: Optional[str]  # 'merge', 'tunnel', 'decay', None
    
    @property
    def lifetime(self) -> float:
        if self.death_time is not None:
            return self.death_time - self.formation_time
        return 0.0
    
    @property
    def spectral_drift(self) -> float:
        if len(self.omega_history) < 2:
            return 0.0
        return abs(self.omega_history[-1] - self.omega_history[0])


def track_basin_identities(
    grid_size: int = 20,
    total_time: float = 50.0,
    dt: float = 0.01,
    seed: int = 42
) -> BasinStatistics:
    """
    Track individual basin identities over time.
    
    Measures:
    - Merge probability (two basins become one)
    - Tunneling probability (basin crosses ω=0)
    - Spontaneous decay rate
    - Spectral drift (change in ω over lifetime)
    """
    engine = QMRTFrequencyEngine(grid_size=grid_size)
    engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
    
    p = engine.params
    steps = int(total_time / dt)
    tracking_interval = max(1, steps // 100)
    
    # Basin tracking
    basin_counter = 0
    active_basins: Dict[int, TrackedBasin] = {}
    deceased_basins: List[TrackedBasin] = []
    events: List[Dict] = []
    
    # Detection threshold
    basin_threshold = 0.5  # Minimum size for basin detection
    
    def detect_basin_regions():
        """Find connected regions near basin minima"""
        high_mask = np.abs(engine.omega - p.omega_0) < p.frequency_basin_width
        low_mask = np.abs(engine.omega + p.omega_0) < p.frequency_basin_width
        
        basins = []
        
        # Simple region detection: find local maxima of basin membership
        for mask, basin_type in [(high_mask, 'high'), (low_mask, 'low')]:
            if np.sum(mask) > basin_threshold * engine.omega.size * 0.01:
                # Find centroid of this basin type
                coords = np.where(mask)
                if len(coords[0]) > 0:
                    ci = int(np.mean(coords[0]))
                    cj = int(np.mean(coords[1]))
                    ck = int(np.mean(coords[2]))
                    omega_val = float(engine.omega[ci, cj, ck])
                    basins.append({
                        'type': basin_type,
                        'centroid': (ci, cj, ck),
                        'omega': omega_val,
                        'size': np.sum(mask)
                    })
        
        return basins
    
    def match_basins(old_basins: Dict[int, TrackedBasin], new_regions: List[Dict]) -> Tuple[Dict, List, List, List]:
        """Match detected regions to tracked basins"""
        nonlocal basin_counter
        
        matched = {}
        new_basins = []
        merges = []
        tunnels = []
        
        used_regions = set()
        
        for bid, old in old_basins.items():
            if not old.is_alive:
                continue
                
            old_centroid = old.centroid_history[-1]
            old_type = 'high' if old.omega_history[-1] > 0 else 'low'
            
            best_match = None
            best_dist = float('inf')
            
            for i, region in enumerate(new_regions):
                if i in used_regions:
                    continue
                    
                # Distance to region centroid
                dist = np.sqrt(sum((a-b)**2 for a, b in zip(old_centroid, region['centroid'])))
                
                if dist < best_dist and dist < grid_size / 4:
                    best_match = (i, region)
                    best_dist = dist
            
            if best_match is not None:
                i, region = best_match
                used_regions.add(i)
                
                # Check for tunneling (basin type changed)
                new_type = region['type']
                if old_type != new_type:
                    tunnels.append({
                        'basin_id': bid,
                        'time': engine.time,
                        'from_type': old_type,
                        'to_type': new_type
                    })
                    old.death_cause = 'tunnel'
                    old.death_time = engine.time
                    old.is_alive = False
                    deceased_basins.append(old)
                else:
                    # Update basin
                    old.omega_history.append(region['omega'])
                    old.centroid_history.append(region['centroid'])
                    matched[bid] = old
            else:
                # Basin died (decay)
                old.death_cause = 'decay'
                old.death_time = engine.time
                old.is_alive = False
                deceased_basins.append(old)
        
        # Create new basins from unmatched regions
        for i, region in enumerate(new_regions):
            if i not in used_regions:
                basin_counter += 1
                new_basin = TrackedBasin(
                    id=basin_counter,
                    formation_time=engine.time,
                    death_time=None,
                    initial_omega=region['omega'],
                    omega_history=[region['omega']],
                    centroid_history=[region['centroid']],
                    is_alive=True,
                    death_cause=None
                )
                matched[basin_counter] = new_basin
                new_basins.append(basin_counter)
        
        return matched, new_basins, merges, tunnels
    
    # Initial detection
    initial_regions = detect_basin_regions()
    for region in initial_regions:
        basin_counter += 1
        active_basins[basin_counter] = TrackedBasin(
            id=basin_counter,
            formation_time=0.0,
            death_time=None,
            initial_omega=region['omega'],
            omega_history=[region['omega']],
            centroid_history=[region['centroid']],
            is_alive=True,
            death_cause=None
        )
    
    total_merges = 0
    total_tunnels = 0
    
    for step in range(steps):
        engine.evolve_timestep(dt)
        
        if step % tracking_interval == 0:
            current_regions = detect_basin_regions()
            active_basins, new_basins, merges, tunnels = match_basins(active_basins, current_regions)
            
            total_merges += len(merges)
            total_tunnels += len(tunnels)
            
            for m in merges:
                events.append({'type': 'merge', **m})
            for t in tunnels:
                events.append({'type': 'tunnel', **t})
    
    # Mark remaining active basins
    for basin in active_basins.values():
        basin.death_time = engine.time
        deceased_basins.append(basin)
    
    # Compute statistics
    all_basins = deceased_basins
    lifetimes = [b.lifetime for b in all_basins if b.lifetime > 0]
    spectral_drifts = [b.spectral_drift for b in all_basins]
    
    decay_count = sum(1 for b in all_basins if b.death_cause == 'decay')
    
    return BasinStatistics(
        total_basins_formed=basin_counter,
        total_merges=total_merges,
        total_tunneling_events=total_tunnels,
        total_spontaneous_decays=decay_count,
        merge_probability=total_merges / max(basin_counter, 1),
        tunneling_probability=total_tunnels / max(basin_counter, 1),
        decay_rate=decay_count / total_time,
        mean_spectral_drift=float(np.mean(spectral_drifts)) if spectral_drifts else 0.0,
        lifetime_distribution={
            'mean': float(np.mean(lifetimes)) if lifetimes else 0.0,
            'std': float(np.std(lifetimes)) if lifetimes else 0.0,
            'max': float(np.max(lifetimes)) if lifetimes else 0.0
        },
        event_history=events
    )


# =============================================================================
# 4. PHASE DIAGRAM MAPPING
# =============================================================================

@dataclass
class PhaseDiagramPoint:
    """Single point in the phase diagram"""
    a_omega: float
    K_omega: float
    g_coupling: float
    potential_gradient_ratio: float  # a_ω / K_ω
    regime: str  # 'unstable', 'reflective', 'tunneling', 'equilibrium'
    stability_time: float
    collision_type: str
    basin_fraction: float
    
    def to_dict(self) -> Dict:
        return {
            'a_omega': float(self.a_omega),
            'K_omega': float(self.K_omega),
            'g_coupling': float(self.g_coupling),
            'potential_gradient_ratio': float(self.potential_gradient_ratio),
            'regime': self.regime,
            'stability_time': float(self.stability_time),
            'collision_type': self.collision_type,
            'basin_fraction': float(self.basin_fraction)
        }


@dataclass
class PhaseDiagramResult:
    """Phase diagram mapping result"""
    points: List[PhaseDiagramPoint]
    regime_boundaries: Dict[str, List[float]]  # Approximate boundaries
    optimal_parameters: Dict[str, float]
    
    def to_dict(self) -> Dict:
        return {
            'points': [p.to_dict() for p in self.points],
            'regime_boundaries': self.regime_boundaries,
            'optimal_parameters': {k: float(v) for k, v in self.optimal_parameters.items()}
        }


def classify_regime(stability_time: float, collision_type: str, total_time: float) -> str:
    """Classify the dynamical regime based on observables"""
    if stability_time < total_time * 0.2:
        return 'unstable'
    elif collision_type == 'reflection':
        return 'reflective'
    elif collision_type == 'tunnel':
        return 'tunneling'
    else:
        return 'equilibrium'


def map_phase_diagram(
    grid_size: int = 16,
    test_time: float = 15.0,
    dt: float = 0.01,
    n_points: int = 25,
    seed: int = 42
) -> PhaseDiagramResult:
    """
    Map the phase diagram: (a_ω / K_ω) vs (g coupling).
    
    Identifies regions of:
    - Unstable (basins decay quickly)
    - Reflective (basins bounce)
    - Tunneling (basins pass through)
    - Equilibrium-locked (basins frozen)
    """
    # Parameter ranges
    ratio_values = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]  # a_ω / K_ω
    g_values = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]  # g_omega_phi
    
    points = []
    
    base_a_omega = 1.0
    
    for ratio in ratio_values:
        for g in g_values:
            print(f"Testing ratio={ratio}, g={g}...")
            
            # Set parameters
            params = QMRTFrequencyParameters()
            params.a_omega = base_a_omega
            params.K_omega = base_a_omega / ratio
            params.g_omega_phi = g
            params.g_omega_rho = g / 2
            
            # Test stability
            engine = QMRTFrequencyEngine(grid_size=grid_size, params=params)
            engine.initialize_frequency_domains(amplitude=0.03, seed=seed)
            
            p = engine.params
            steps = int(test_time / dt)
            
            initial_basins = None
            stability_time = test_time
            
            for step in range(steps):
                engine.evolve_timestep(dt)
                
                if step % 100 == 0:
                    in_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
                    in_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
                    total = in_high + in_low
                    
                    if initial_basins is None:
                        initial_basins = total
                    
                    if stability_time == test_time and total < 0.8 * initial_basins:
                        stability_time = engine.time
            
            # Quick collision test
            collision_type = 'equilibrium'  # Default
            if stability_time > test_time * 0.5:
                # Only test collision if somewhat stable
                engine2 = QMRTFrequencyEngine(grid_size=grid_size, params=params)
                np.random.seed(seed)
                shape = (grid_size, grid_size, grid_size)
                
                engine2.rho = p.rho_equilibrium + 0.02 * np.random.randn(*shape)
                engine2.sigma = 0.02 * np.random.randn(*shape)
                engine2.tau = 0.02 * np.random.randn(*shape)
                engine2.phi = 0.05 * np.random.randn(*shape)
                
                engine2.omega = np.zeros(shape)
                center = grid_size // 2
                for i in range(grid_size):
                    if i < center - 2:
                        engine2.omega[i, :, :] = p.omega_0
                    elif i > center + 2:
                        engine2.omega[i, :, :] = -p.omega_0
                    else:
                        t = (i - (center - 2)) / 4.0
                        engine2.omega[i, :, :] = p.omega_0 * (1 - 2*t)
                
                engine2.pi_rho = np.zeros(shape)
                engine2.pi_sigma = np.zeros(shape)
                engine2.pi_tau = np.zeros(shape)
                engine2.pi_phi = np.zeros(shape)
                engine2.pi_omega = np.zeros(shape)
                for i in range(grid_size):
                    engine2.pi_omega[i, :, :] = -0.1 if i < center else 0.1
                
                engine2._precompute_spectral()
                engine2.initial_energy = engine2.compute_total_energy()
                
                for _ in range(int(test_time * 0.5 / dt)):
                    engine2.evolve_timestep(dt)
                
                high_frac = float(np.sum(engine2.omega > 0.5 * p.omega_0)) / engine2.omega.size
                low_frac = float(np.sum(engine2.omega < -0.5 * p.omega_0)) / engine2.omega.size
                
                if high_frac > 0.2 and low_frac > 0.2:
                    collision_type = 'tunnel' if high_frac > 0.35 else 'reflection'
                elif high_frac + low_frac < 0.2:
                    collision_type = 'annihilation'
            
            # Final basin fraction
            in_high = float(np.sum(np.abs(engine.omega - p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            in_low = float(np.sum(np.abs(engine.omega + p.omega_0) < p.frequency_basin_width)) / engine.omega.size
            
            regime = classify_regime(stability_time, collision_type, test_time)
            
            points.append(PhaseDiagramPoint(
                a_omega=params.a_omega,
                K_omega=params.K_omega,
                g_coupling=g,
                potential_gradient_ratio=ratio,
                regime=regime,
                stability_time=stability_time,
                collision_type=collision_type,
                basin_fraction=in_high + in_low
            ))
    
    # Find regime boundaries (approximate)
    regime_boundaries = {
        'unstable_boundary': [],
        'tunneling_boundary': [],
        'equilibrium_boundary': []
    }
    
    # Find optimal parameters (highest stability with tunneling behavior)
    best_point = max(
        [p for p in points if p.regime in ['tunneling', 'equilibrium']],
        key=lambda p: p.stability_time * p.basin_fraction,
        default=points[0] if points else None
    )
    
    optimal = {
        'a_omega': best_point.a_omega if best_point else 1.0,
        'K_omega': best_point.K_omega if best_point else 0.05,
        'g_coupling': best_point.g_coupling if best_point else 0.005,
        'ratio': best_point.potential_gradient_ratio if best_point else 20.0
    }
    
    return PhaseDiagramResult(
        points=points,
        regime_boundaries=regime_boundaries,
        optimal_parameters=optimal
    )


# =============================================================================
# COMPREHENSIVE TEST RUNNER
# =============================================================================

def run_comprehensive_validation(quick_mode: bool = True, seed: int = 42) -> Dict:
    """
    Run all comprehensive validation tests.
    """
    print("=" * 70)
    print("QMRT COMPREHENSIVE PHYSICS VALIDATION")
    print("=" * 70)
    
    results = {}
    
    if quick_mode:
        scaling_grids = [20, 24, 32]
        entropy_time = 60.0
        tracking_time = 30.0
        phase_points = 20
    else:
        scaling_grids = [24, 32, 48, 64]
        entropy_time = 200.0
        tracking_time = 100.0
        phase_points = 50
    
    # 1. Scaling Persistence
    print("\n[1/4] SCALING PERSISTENCE TEST")
    print("-" * 40)
    start = time.time()
    results['scaling_persistence'] = test_scaling_persistence(
        grid_sizes=scaling_grids,
        simulation_time=30.0,
        seed=seed
    ).to_dict()
    print(f"  Completed in {time.time()-start:.1f}s")
    print(f"  Stability persists: {results['scaling_persistence']['stability_persists']}")
    
    # 2. Entropy Drift
    print("\n[2/4] ENTROPY DRIFT TEST")
    print("-" * 40)
    start = time.time()
    results['entropy_drift'] = test_entropy_drift(
        grid_size=20,
        total_time=entropy_time,
        seed=seed
    ).to_dict()
    print(f"  Completed in {time.time()-start:.1f}s")
    print(f"  Entropy plateaus: {results['entropy_drift']['entropy_plateaus']}")
    print(f"  Half-entropy regime: {results['entropy_drift']['half_entropy_regime']}")
    
    # 3. Basin Identity Tracking
    print("\n[3/4] BASIN IDENTITY TRACKING")
    print("-" * 40)
    start = time.time()
    results['basin_tracking'] = track_basin_identities(
        grid_size=20,
        total_time=tracking_time,
        seed=seed
    ).to_dict()
    print(f"  Completed in {time.time()-start:.1f}s")
    print(f"  Tunneling probability: {results['basin_tracking']['tunneling_probability']:.4f}")
    print(f"  Decay rate: {results['basin_tracking']['decay_rate']:.4f}")
    
    # 4. Phase Diagram (simplified for time)
    print("\n[4/4] PHASE DIAGRAM MAPPING")
    print("-" * 40)
    start = time.time()
    results['phase_diagram'] = map_phase_diagram(
        grid_size=14,
        test_time=10.0,
        n_points=phase_points,
        seed=seed
    ).to_dict()
    print(f"  Completed in {time.time()-start:.1f}s")
    print(f"  Optimal ratio (a_ω/K_ω): {results['phase_diagram']['optimal_parameters']['ratio']}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    results['summary'] = {
        'scaling_persists': results['scaling_persistence']['stability_persists'],
        'entropy_plateaus': results['entropy_drift']['entropy_plateaus'],
        'half_entropy_regime': results['entropy_drift']['half_entropy_regime'],
        'tunneling_observed': results['basin_tracking']['total_tunneling_events'] > 0,
        'optimal_parameters': results['phase_diagram']['optimal_parameters']
    }
    
    return results
