"""
World Generator - Mode 2: Gameplay Universe Generation
Derives playable worlds from cosmological seeds or direct initialization
"""
import numpy as np
from typing import Dict, Any, Optional
from physics_engine import QMRTSubstrate
import math


class WorldGenerator:
    """Mode 2: Generates playable world states from seeded outputs or direct generation"""
    
    def __init__(self):
        # Reference values for Earth-like world (death-world level 10)
        self.earth_ref = {
            'density_mean': 1.0,
            'density_std': 0.1,
            'tension_mean': 1.0,
            'tension_std': 0.1,
            'torsion_mean': 0.05,
            'torsion_max': 0.2,
            'coherence_gradient_mean': 0.08,
            'coherence_gradient_max': 0.3,
            'temperature_mean': 1.0,
            'temperature_max': 3.0,
            'curvature_mean': 0.1,
            'curvature_max': 0.5,
        }
    
    def generate_world(self, death_world_level: int, seed: Optional[int] = None, 
                      evolution_steps: int = 200,
                      cosmological_seed: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate a world at specified death-world level
        
        Args:
            death_world_level: Difficulty level 1-15 (Earth=10)
            seed: Random seed for reproducibility
            evolution_steps: Physics evolution iterations
            cosmological_seed: Optional seed from Mode 1 cosmological simulation
        
        Returns:
            Complete world parameters dictionary
        """
        if not 1 <= death_world_level <= 15:
            raise ValueError("Death-world level must be between 1 and 15")
        
        # Create physics engine
        physics = QMRTSubstrate(grid_size=32, scale=1.0)
        
        # Initialize substrate
        if cosmological_seed:
            # Mode 2A: Initialize from cosmological seed
            print(f"Mode 2A: Initializing from cosmological seed (density contrast: {cosmological_seed.get('density_contrast', 'N/A')})")
            self._initialize_from_cosmological_seed(physics, cosmological_seed, death_world_level)
        else:
            # Mode 2B: Direct initialization (original fast method)
            print(f"Mode 2B: Direct initialization (death level {death_world_level})")
            amplitude = self._scale_amplitude(death_world_level)
            physics.initialize_random_perturbations(amplitude=amplitude, seed=seed)
        
        # Evolve substrate
        scaled_steps = int(evolution_steps * (0.5 + death_world_level / 20.0))
        physics.evolve_substrate(dt=0.01, steps=scaled_steps)
        
        # Extract substrate metrics
        metrics = physics.get_substrate_metrics()
        
        # Translate to world parameters
        world_params = self._translate_to_world_parameters(metrics, death_world_level)
        
        # Add metadata
        world_params['death_world_level'] = death_world_level
        world_params['seed'] = seed
        world_params['substrate_metrics'] = metrics
        world_params['cosmological_origin'] = cosmological_seed is not None
        if cosmological_seed:
            world_params['cosmological_seed_position'] = cosmological_seed.get('position')
        
        # Calculate world classification
        world_params['classification'] = self._classify_world(world_params)
        
        return world_params
    
    def _initialize_from_cosmological_seed(self, physics: QMRTSubstrate, 
                                          cosmo_seed: Dict, death_level: int):
        """Initialize world substrate from cosmological structure seed
        
        Uses logarithmic and z-score scaling to compress cosmological magnitudes
        (10^17 scale) into stable planetary simulation ranges (10^0 scale)
        while preserving relative gradients and causal relationships.
        """
        # Extract cosmological substrate values (potentially huge)
        cosmo_rho = cosmo_seed.get('local_rho_mean', 1.0)
        cosmo_T = cosmo_seed.get('local_T_mean', 1.0)
        cosmo_tau = cosmo_seed.get('local_tau_mean', 0.05)
        cosmo_phi = cosmo_seed.get('local_phi_mean', 0.0)
        density_contrast = cosmo_seed.get('density_contrast', 1.0)
        
        # LOGARITHMIC SCALING: Compress absolute magnitudes while preserving ratios
        # For extremely large values, use log-space compression
        def safe_log_scale(value, reference=1.0, scale=0.1):
            """Logarithmic scaling that handles extreme values"""
            if abs(value) < 1e-10:
                return reference
            sign = np.sign(value)
            log_val = np.log10(abs(value) + 1)
            # Map log space to reasonable range: log(10^17) = 17 → scale to ~1
            compressed = reference + sign * scale * log_val
            return compressed
        
        # Apply logarithmic compression to cosmological values
        base_rho = safe_log_scale(cosmo_rho, reference=1.0, scale=0.05)
        base_T = safe_log_scale(cosmo_T, reference=1.0, scale=0.05)
        base_tau = safe_log_scale(cosmo_tau, reference=0.05, scale=0.01)
        base_phi = safe_log_scale(cosmo_phi, reference=0.0, scale=0.02)
        
        # DENSITY CONTRAST PRESERVATION: This drives death-world severity
        # Normalize contrast to [0.5, 2.0] range with death-level scaling
        contrast_normalized = 0.8 + (min(density_contrast, 10.0) - 1.0) * 0.1
        contrast_normalized = max(0.5, min(2.0, contrast_normalized))
        
        # Scale perturbations based on death-world level
        level_perturbation = self._scale_amplitude(death_level)
        
        # Z-SCORE NORMALIZATION: Preserve relative gradients
        # Generate perturbations with proper statistics
        rho_perturbations = np.random.randn(physics.grid_size, physics.grid_size, physics.grid_size)
        T_perturbations = np.random.randn(physics.grid_size, physics.grid_size, physics.grid_size)
        tau_perturbations = np.random.randn(physics.grid_size, physics.grid_size, physics.grid_size, 3)
        phi_perturbations = np.random.randn(physics.grid_size, physics.grid_size, physics.grid_size)
        
        # Normalize to unit variance
        rho_perturbations = (rho_perturbations - np.mean(rho_perturbations)) / (np.std(rho_perturbations) + 1e-10)
        T_perturbations = (T_perturbations - np.mean(T_perturbations)) / (np.std(T_perturbations) + 1e-10)
        phi_perturbations = (phi_perturbations - np.mean(phi_perturbations)) / (np.std(phi_perturbations) + 1e-10)
        
        # Apply scaled perturbations around compressed base values
        physics.rho_xi = base_rho * (1.0 + level_perturbation * rho_perturbations)
        physics.T_xi = base_T * (1.0 + level_perturbation * T_perturbations)
        physics.tau_xi = base_tau * (1.0 + level_perturbation * 0.5 * tau_perturbations)
        physics.phi_xi = base_phi + level_perturbation * phi_perturbations
        
        # CAUSAL RELATIONSHIP: Apply density contrast to preserve cosmological structure
        # High contrast regions become higher death-world potential
        physics.rho_xi *= contrast_normalized
        
        # Add structure-driven variations
        # Higher density contrast → more extreme local variations
        structure_factor = min(density_contrast, 5.0) / 5.0
        physics.rho_xi += structure_factor * level_perturbation * 0.2 * rho_perturbations
        
        print(f"  Scaled cosmological seed: rho={base_rho:.3f}, contrast={contrast_normalized:.3f}, structure_factor={structure_factor:.3f}")
        
    def _scale_amplitude(self, level: int) -> float:
        """Scale initial perturbation amplitude based on death-world level"""
        base = 0.02
        earth_amp = 0.10
        max_amp = 0.35
        
        if level <= 10:
            return base + (earth_amp - base) * (level - 1) / 9
        else:
            return earth_amp + (max_amp - earth_amp) * (level - 10) / 5
    
    def _translate_to_world_parameters(self, metrics: Dict[str, float], 
                                      level: int) -> Dict[str, Any]:
        """Translate substrate metrics to gameplay-relevant world parameters"""
        
        # Substrate density → Gravitational pressure & matter density
        gravity = self._map_to_range(metrics['mean_density'], 0.8, 1.3, 0.3, 3.0)
        gravity_variance = metrics['std_density'] * 5.0
        
        # Substrate tension → Energy potential & electromagnetic field strength
        energy_potential = self._map_to_range(metrics['mean_tension'], 0.8, 1.3, 0.5, 5.0)
        em_field_strength = metrics['std_tension'] * 10.0
        
        # Substrate torsion → Rotational forces, magnetic fields, atmospheric complexity
        magnetic_field = self._map_to_range(metrics['mean_torsion'], 0, 0.3, 0.1, 8.0)
        atmospheric_chaos = metrics['max_torsion'] * 15.0
        rotational_variance = metrics['mean_torsion'] * 20.0
        
        # Coherence phase → Quantum stability, biological viability, consciousness potential
        quantum_stability = 1.0 / (1.0 + metrics['max_coherence_gradient'] * 5.0)
        biological_viability = self._calculate_bio_viability(metrics)
        consciousness_potential = self._map_to_range(
            metrics['mean_coherence_gradient'], 0, 0.3, 0.1, 1.0
        )
        
        # Temperature → Environmental harshness
        temperature_mean = metrics['mean_temperature']
        temperature_extremes = metrics['max_temperature']
        
        # Curvature → Spatial anomalies and hazards
        spatial_distortion = metrics['max_curvature'] * 2.0
        hazard_density = self._map_to_range(metrics['mean_curvature'], 0, 1.0, 0.05, 0.8)
        
        # Resource density
        resource_density = self._calculate_resource_density(metrics, level)
        
        # Survival difficulty
        survival_difficulty = self._calculate_survival_difficulty(metrics, level)
        
        return {
            'gravity': round(gravity, 3),
            'gravity_variance': round(gravity_variance, 3),
            'energy_potential': round(energy_potential, 3),
            'em_field_strength': round(em_field_strength, 3),
            'magnetic_field': round(magnetic_field, 3),
            'atmospheric_chaos': round(atmospheric_chaos, 3),
            'rotational_variance': round(rotational_variance, 3),
            'quantum_stability': round(quantum_stability, 3),
            'biological_viability': round(biological_viability, 3),
            'consciousness_potential': round(consciousness_potential, 3),
            'temperature_mean': round(temperature_mean, 3),
            'temperature_extremes': round(temperature_extremes, 3),
            'spatial_distortion': round(spatial_distortion, 3),
            'hazard_density': round(hazard_density, 3),
            'resource_density': round(resource_density, 3),
            'survival_difficulty': round(survival_difficulty, 3),
        }
    
    def _map_to_range(self, value: float, in_min: float, in_max: float, 
                     out_min: float, out_max: float) -> float:
        """Map value from input range to output range"""
        clamped = max(in_min, min(in_max, value))
        normalized = (clamped - in_min) / (in_max - in_min) if in_max != in_min else 0.5
        return out_min + normalized * (out_max - out_min)
    
    def _calculate_bio_viability(self, metrics: Dict[str, float]) -> float:
        """Calculate biological viability from substrate properties"""
        pattern_index = metrics['mean_coherence_gradient'] + metrics['mean_torsion']
        temp = metrics['mean_temperature']
        
        pattern_score = math.exp(-((pattern_index - 0.125) / 0.1) ** 2)
        temp_score = math.exp(-((temp - 1.0) / 0.4) ** 2)
        
        return pattern_score * temp_score
    
    def _calculate_resource_density(self, metrics: Dict[str, float], level: int) -> float:
        """Calculate resource availability"""
        chaos = (metrics['max_torsion'] + metrics['max_coherence_gradient'] + 
                metrics['std_density'] + metrics['std_tension'])
        
        base_resources = 1.0 / (1.0 + chaos * 2.0)
        level_modifier = 1.0 - (level - 1) * 0.05
        
        return max(0.05, base_resources * level_modifier)
    
    def _calculate_survival_difficulty(self, metrics: Dict[str, float], level: int) -> float:
        """Calculate overall survival difficulty score (0-10)"""
        temp_factor = min(metrics['max_temperature'] / 5.0, 1.0)
        torsion_factor = min(metrics['max_torsion'] / 0.5, 1.0)
        curvature_factor = min(metrics['max_curvature'] / 2.0, 1.0)
        instability_factor = (metrics['std_density'] + metrics['std_tension']) / 0.4
        
        composite = (temp_factor * 0.3 + torsion_factor * 0.3 + 
                    curvature_factor * 0.2 + instability_factor * 0.2)
        
        difficulty = composite * 7.0 + (level / 15.0) * 3.0
        
        return min(10.0, difficulty)
    
    def _classify_world(self, params: Dict[str, Any]) -> str:
        """Classify world type based on parameters"""
        level = params['death_world_level']
        bio_viability = params['biological_viability']
        
        if level <= 3:
            return "Sanctuary World"
        elif level <= 6:
            if bio_viability > 0.5:
                return "Garden World"
            else:
                return "Frontier World"
        elif level <= 9:
            if bio_viability > 0.4:
                return "Contested World"
            else:
                return "Harsh World"
        elif level == 10:
            return "Earth-Class World"
        elif level <= 12:
            return "Death World"
        elif level <= 14:
            return "Extreme Death World"
        else:
            return "Apocalypse World"
