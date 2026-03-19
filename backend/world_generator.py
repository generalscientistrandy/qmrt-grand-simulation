"""
World Generator - Translates QMRT substrate physics to world parameters
"""
import numpy as np
from typing import Dict, Any, Optional
from physics_engine import QMRTSubstrate
import math


class WorldGenerator:
    """Generates world parameters from QMRT substrate simulation"""
    
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
                      evolution_steps: int = 200) -> Dict[str, Any]:
        """Generate a world at specified death-world level (1-15)
        
        Death-world level scaling:
        1: Minimal perturbations, stable, low energy
        10: Earth-like, balanced (reference)
        15: Extreme gradients, chaotic, high energy
        """
        if not 1 <= death_world_level <= 15:
            raise ValueError("Death-world level must be between 1 and 15")
        
        # Create physics engine
        physics = QMRTSubstrate(grid_size=32, scale=1.0)
        
        # Scale perturbation amplitude based on death-world level
        # Level 1: 0.02, Level 10: 0.10 (Earth), Level 15: 0.30
        amplitude = self._scale_amplitude(death_world_level)
        
        # Initialize and evolve substrate
        physics.initialize_random_perturbations(amplitude=amplitude, seed=seed)
        
        # Evolution steps also scale with difficulty
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
        
        # Calculate world classification
        world_params['classification'] = self._classify_world(world_params)
        
        return world_params
    
    def _scale_amplitude(self, level: int) -> float:
        """Scale initial perturbation amplitude based on death-world level"""
        # Exponential scaling for dramatic difference at high levels
        base = 0.02
        earth_amp = 0.10  # Level 10 reference
        max_amp = 0.35     # Level 15
        
        if level <= 10:
            # Linear interpolation from base to earth
            return base + (earth_amp - base) * (level - 1) / 9
        else:
            # Steeper scaling from earth to max
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
        
        # Resource density (inverse relationship with chaos)
        resource_density = self._calculate_resource_density(metrics, level)
        
        # Survival difficulty (composite metric)
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
        """Calculate biological viability from substrate properties
        
        Based on QMRT biology equations:
        PatternIndex = ||Xi_grad(ΦΞ)|| + ||τΞ||
        Stable patterns emerge in moderate zones
        """
        pattern_index = metrics['mean_coherence_gradient'] + metrics['mean_torsion']
        temp = metrics['mean_temperature']
        
        # Optimal zone: pattern_index ~ 0.1-0.15, temp ~ 0.8-1.2
        pattern_score = math.exp(-((pattern_index - 0.125) / 0.1) ** 2)
        temp_score = math.exp(-((temp - 1.0) / 0.4) ** 2)
        
        return pattern_score * temp_score
    
    def _calculate_resource_density(self, metrics: Dict[str, float], level: int) -> float:
        """Calculate resource availability (inverse of chaos)"""
        chaos = (metrics['max_torsion'] + metrics['max_coherence_gradient'] + 
                metrics['std_density'] + metrics['std_tension'])
        
        # Resources scarce in chaotic environments
        base_resources = 1.0 / (1.0 + chaos * 2.0)
        
        # Scale with level (harder worlds have fewer resources)
        level_modifier = 1.0 - (level - 1) * 0.05
        
        return max(0.05, base_resources * level_modifier)
    
    def _calculate_survival_difficulty(self, metrics: Dict[str, float], level: int) -> float:
        """Calculate overall survival difficulty score (0-10)"""
        # Weighted composite of various hazards
        temp_factor = min(metrics['max_temperature'] / 5.0, 1.0)
        torsion_factor = min(metrics['max_torsion'] / 0.5, 1.0)
        curvature_factor = min(metrics['max_curvature'] / 2.0, 1.0)
        instability_factor = (metrics['std_density'] + metrics['std_tension']) / 0.4
        
        composite = (temp_factor * 0.3 + torsion_factor * 0.3 + 
                    curvature_factor * 0.2 + instability_factor * 0.2)
        
        # Scale to 0-10 range with level bias
        difficulty = composite * 7.0 + (level / 15.0) * 3.0
        
        return min(10.0, difficulty)
    
    def _classify_world(self, params: Dict[str, Any]) -> str:
        """Classify world type based on parameters"""
        level = params['death_world_level']
        bio_viability = params['biological_viability']
        survival = params['survival_difficulty']
        
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
