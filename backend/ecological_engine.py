"""
Ecological Engine - Phase B: Predator Pressure & Death-World Dynamics
Implements ecological simulation emergent from QMRT substrate physics
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
import math


class PredatorTier:
    """Predator tier classification based on death-world severity"""
    TIER_0 = "herbivore"       # Base consumers
    TIER_1 = "apex_predator"    # Planetary apex (level 1-9)
    TIER_2 = "mega_predator"    # Death-world predator (level 10-12)
    TIER_3 = "titan_predator"   # Extreme death-world (level 13-14)
    TIER_4 = "world_eater"      # Apocalypse-level (level 15)


class Species:
    """Individual species with substrate-derived traits"""
    def __init__(self, name: str, tier: str, substrate_origin: Dict):
        self.name = name
        self.tier = tier
        self.population = 1000
        self.generation = 0
        
        # Substrate-derived traits
        self.aggression = substrate_origin.get('torsion_factor', 0.5)
        self.resilience = substrate_origin.get('density_factor', 0.5)
        self.intelligence = substrate_origin.get('coherence_factor', 0.5)
        self.adaptability = substrate_origin.get('temperature_variance', 0.5)
        
        # Evolutionary parameters
        self.mutation_rate = 0.01
        self.fitness = 1.0


class EcologicalEngine:
    """Ecological simulation engine with death-world pressure dynamics"""
    
    def __init__(self, world_params: Dict):
        self.world_params = world_params
        self.death_level = world_params['death_world_level']
        
        # Species registry
        self.species: List[Species] = []
        self.predator_pressure = self._calculate_predator_pressure()
        
        # Ecological parameters from substrate
        self.resource_capacity = world_params['world_parameters']['resource_density'] * 10000
        self.environmental_harshness = world_params['world_parameters']['survival_difficulty']
        self.mutation_intensity = self._calculate_mutation_intensity()
        
    def _calculate_predator_pressure(self) -> float:
        """Calculate predator pressure based on death-world level
        
        Pressure = f(death_level, torsion, temperature_extremes)
        Higher death-worlds have exponentially more dangerous predators
        """
        base_pressure = 0.1
        level_factor = math.exp((self.death_level - 10) * 0.15)
        
        # Substrate influence
        torsion = self.world_params['substrate_metrics'].get('mean_torsion', 0.05)
        temp_extremes = self.world_params['world_parameters'].get('temperature_extremes', 1.0)
        
        torsion_modifier = 1.0 + (torsion / 0.1) * 0.5
        temp_modifier = 1.0 + (temp_extremes / 5.0) * 0.3
        
        pressure = base_pressure * level_factor * torsion_modifier * temp_modifier
        return min(pressure, 10.0)
    
    def _calculate_mutation_intensity(self) -> float:
        """Mutation rate from coherence phase gradients
        
        Based on QMRT: MutationRate ∝ ||∇ΦΞ|| + T_eff
        """
        coherence_grad = self.world_params['substrate_metrics'].get('mean_coherence_gradient', 0.08)
        temp = self.world_params['substrate_metrics'].get('mean_temperature', 1.0)
        
        base_rate = 0.001
        mutation = base_rate * (1.0 + coherence_grad * 5.0 + temp * 0.2)
        
        return min(mutation, 0.1)
    
    def generate_predator_tier_distribution(self) -> Dict[str, int]:
        """Generate predator tier distribution based on death-world level"""
        distribution = {
            PredatorTier.TIER_0: 0,
            PredatorTier.TIER_1: 0,
            PredatorTier.TIER_2: 0,
            PredatorTier.TIER_3: 0,
            PredatorTier.TIER_4: 0,
        }
        
        if self.death_level <= 3:
            # Sanctuary worlds: mostly herbivores
            distribution[PredatorTier.TIER_0] = 80
            distribution[PredatorTier.TIER_1] = 20
            
        elif self.death_level <= 6:
            # Garden/Frontier: balanced ecosystem
            distribution[PredatorTier.TIER_0] = 60
            distribution[PredatorTier.TIER_1] = 35
            distribution[PredatorTier.TIER_2] = 5
            
        elif self.death_level <= 9:
            # Harsh worlds: significant predation
            distribution[PredatorTier.TIER_0] = 40
            distribution[PredatorTier.TIER_1] = 40
            distribution[PredatorTier.TIER_2] = 20
            
        elif self.death_level == 10:
            # Earth-class: apex predators dominant
            distribution[PredatorTier.TIER_0] = 30
            distribution[PredatorTier.TIER_1] = 50
            distribution[PredatorTier.TIER_2] = 20
            
        elif self.death_level <= 12:
            # Death worlds: mega predators
            distribution[PredatorTier.TIER_0] = 15
            distribution[PredatorTier.TIER_1] = 30
            distribution[PredatorTier.TIER_2] = 45
            distribution[PredatorTier.TIER_3] = 10
            
        elif self.death_level <= 14:
            # Extreme death worlds: titan predators
            distribution[PredatorTier.TIER_0] = 5
            distribution[PredatorTier.TIER_1] = 15
            distribution[PredatorTier.TIER_2] = 35
            distribution[PredatorTier.TIER_3] = 40
            distribution[PredatorTier.TIER_4] = 5
            
        else:  # Level 15
            # Apocalypse world: world-eaters
            distribution[PredatorTier.TIER_0] = 0
            distribution[PredatorTier.TIER_1] = 5
            distribution[PredatorTier.TIER_2] = 15
            distribution[PredatorTier.TIER_3] = 50
            distribution[PredatorTier.TIER_4] = 30
            
        return distribution
    
    def spawn_species(self, count: int = 10) -> List[Species]:
        """Spawn species with substrate-derived traits"""
        tier_dist = self.generate_predator_tier_distribution()
        spawned = []
        
        # Calculate substrate factors for trait derivation
        substrate = self.world_params['substrate_metrics']
        world_p = self.world_params['world_parameters']
        
        torsion_factor = min(substrate.get('mean_torsion', 0.05) / 0.1, 2.0)
        density_factor = min(abs(substrate.get('mean_density', 1.0)), 2.0)
        coherence_factor = min(substrate.get('mean_coherence_gradient', 0.08) / 0.15, 2.0)
        temp_variance = min(world_p.get('temperature_extremes', 1.0) / 3.0, 2.0)
        
        substrate_origin = {
            'torsion_factor': torsion_factor,
            'density_factor': density_factor,
            'coherence_factor': coherence_factor,
            'temperature_variance': temp_variance
        }
        
        # Spawn species according to tier distribution
        tier_counts = {tier: int(count * (pct / 100.0)) for tier, pct in tier_dist.items()}
        
        for tier, tier_count in tier_counts.items():
            for i in range(tier_count):
                species_name = f"{tier}_{self.death_level}_{i}"
                species = Species(species_name, tier, substrate_origin)
                spawned.append(species)
                
        self.species.extend(spawned)
        return spawned
    
    def evolve_ecosystem(self, generations: int = 100) -> Dict:
        """Evolve ecosystem through predator-prey dynamics
        
        Based on modified Lotka-Volterra with substrate influence:
        ∂Pop/∂t = r·Pop·(1 - Pop/K) - predation + MutationRate
        """
        evolution_log = {
            'initial_species': len(self.species),
            'extinctions': 0,
            'adaptations': 0,
            'final_diversity': 0
        }
        
        for gen in range(generations):
            # Calculate predation pressure
            total_predators = sum(1 for s in self.species if s.tier != PredatorTier.TIER_0)
            predation_factor = (total_predators / max(len(self.species), 1)) * self.predator_pressure
            
            for species in self.species:
                if species.population <= 0:
                    continue
                
                # Logistic growth with carrying capacity
                growth_rate = 0.1 * (1.0 - species.population / self.resource_capacity)
                
                # Predation mortality
                mortality = predation_factor * (1.0 if species.tier == PredatorTier.TIER_0 else 0.5)
                
                # Environmental pressure (death-world harshness)
                env_mortality = self.environmental_harshness * 0.01 * (1.0 - species.resilience)
                
                # Population change
                pop_change = species.population * (growth_rate - mortality - env_mortality)
                species.population = max(0, species.population + pop_change)
                
                # Mutation and adaptation
                if np.random.random() < self.mutation_intensity:
                    species.adaptability += np.random.normal(0, 0.05)
                    species.adaptability = max(0, min(1.0, species.adaptability))
                    evolution_log['adaptations'] += 1
                
                # Extinction check
                if species.population < 10:
                    species.population = 0
                    evolution_log['extinctions'] += 1
                    
                species.generation = gen
        
        # Count surviving species
        evolution_log['final_diversity'] = sum(1 for s in self.species if s.population > 0)
        evolution_log['predator_pressure'] = self.predator_pressure
        evolution_log['mutation_intensity'] = self.mutation_intensity
        
        return evolution_log
    
    def get_ecosystem_summary(self) -> Dict:
        """Get current ecosystem state"""
        alive_species = [s for s in self.species if s.population > 0]
        
        tier_counts = {}
        for tier in [PredatorTier.TIER_0, PredatorTier.TIER_1, PredatorTier.TIER_2, 
                    PredatorTier.TIER_3, PredatorTier.TIER_4]:
            tier_counts[tier] = sum(1 for s in alive_species if s.tier == tier)
        
        return {
            'total_species': len(alive_species),
            'total_population': sum(s.population for s in alive_species),
            'tier_distribution': tier_counts,
            'average_adaptability': np.mean([s.adaptability for s in alive_species]) if alive_species else 0,
            'predator_pressure': self.predator_pressure,
            'death_world_level': self.death_level,
            'mutation_intensity': self.mutation_intensity,
            'resource_utilization': sum(s.population for s in alive_species) / self.resource_capacity if self.resource_capacity > 0 else 0
        }
