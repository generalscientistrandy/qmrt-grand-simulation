"""
Enhanced Cosmological Simulator with Stellar & Planetary Formation
Extends structure formation through to planetary system emergence
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
import math
from cosmological_simulator import CosmologicalSimulator, CosmologicalEpoch, CosmologicalSnapshot


class StellarSystem:
    """Stellar system formed from structure seed"""
    def __init__(self, seed_id: int, position: Tuple[int, int, int], 
                 substrate_properties: Dict):
        self.seed_id = seed_id
        self.position = position
        self.substrate = substrate_properties
        
        # Stellar properties
        self.star_mass = self._calculate_star_mass()
        self.star_type = self._classify_star()
        self.luminosity = self._calculate_luminosity()
        
        # Planetary system
        self.num_planets = self._determine_planet_count()
        self.planets = []
        self._generate_planets()
        
    def _calculate_star_mass(self) -> float:
        """Calculate stellar mass from substrate density
        
        M_star ∝ ρΞ^(3/2) (Jeans mass)
        """
        density = self.substrate.get('density', 1.0)
        mass = density ** 1.5
        return max(0.1, min(100.0, mass))  # Solar masses
    
    def _classify_star(self) -> str:
        """Classify star by spectral type based on mass"""
        if self.star_mass > 16:
            return "O-type (Blue Giant)"
        elif self.star_mass > 2.1:
            return "B-type (Blue-White)"
        elif self.star_mass > 1.4:
            return "A-type (White)"
        elif self.star_mass > 1.04:
            return "F-type (Yellow-White)"
        elif self.star_mass > 0.8:
            return "G-type (Yellow) - Sun-like"
        elif self.star_mass > 0.45:
            return "K-type (Orange)"
        else:
            return "M-type (Red Dwarf)"
    
    def _calculate_luminosity(self) -> float:
        """L ∝ M^3.5 (mass-luminosity relation)"""
        return self.star_mass ** 3.5
    
    def _determine_planet_count(self) -> int:
        """Number of planets from substrate tension and torsion"""
        tension = self.substrate.get('tension', 1.0)
        torsion = self.substrate.get('torsion', 0.05)
        
        # Handle NaN/Inf
        if not np.isfinite(tension):
            tension = 1.0
        if not np.isfinite(torsion):
            torsion = 0.05
        
        # More tension = more angular momentum = more planets
        base_count = int(3 + abs(tension) * 5 + abs(torsion) * 20)
        return max(1, min(base_count, 15))  # Cap at 1-15 planets
    
    def _generate_planets(self):
        """Generate planetary system"""
        for i in range(self.num_planets):
            # Orbital radius increases with planet number
            orbit_au = 0.4 * (1.5 ** i)  # AU
            
            # Planet mass from substrate properties + orbital position
            coherence = self.substrate.get('coherence', 0.0)
            base_mass = 0.01 + abs(coherence) * 10
            
            # Rocky vs gas giant (inner vs outer)
            if orbit_au < 3.0:
                # Rocky planet
                mass = base_mass * (0.1 + np.random.random() * 0.5)  # Earth masses
                planet_type = "Rocky"
            else:
                # Gas giant
                mass = base_mass * (10 + np.random.random() * 300)  # Earth masses
                planet_type = "Gas Giant"
            
            # Habitability check
            habitable = self._check_habitability(orbit_au, mass, planet_type)
            
            planet = {
                'id': i,
                'orbit_au': round(orbit_au, 2),
                'mass_earth': round(mass, 3),
                'type': planet_type,
                'habitable': habitable,
                'substrate_influence': {
                    'density_factor': self.substrate.get('density', 1.0),
                    'torsion_factor': self.substrate.get('torsion', 0.05)
                }
            }
            
            self.planets.append(planet)
    
    def _check_habitability(self, orbit_au: float, mass: float, planet_type: str) -> bool:
        """Check if planet is in habitable zone"""
        if planet_type != "Rocky":
            return False
        
        # Habitable zone based on stellar luminosity
        inner_hz = 0.95 * math.sqrt(self.luminosity)
        outer_hz = 1.37 * math.sqrt(self.luminosity)
        
        in_hz = inner_hz <= orbit_au <= outer_hz
        mass_ok = 0.3 <= mass <= 5.0  # Earth-like mass range
        
        return in_hz and mass_ok


class UniverseSimulator(CosmologicalSimulator):
    """Enhanced cosmological simulator with stellar and planetary formation"""
    
    def __init__(self, grid_size: int = 64, hubble_parameter: float = 0.07):
        super().__init__(grid_size, hubble_parameter)
        self.stellar_systems: List[StellarSystem] = []
        self.habitable_worlds: List[Dict] = []
        
        # Simulation tracking
        self.epoch_snapshots: Dict[str, CosmologicalSnapshot] = {}
        self.simulation_log = []
        
    def run_full_universe_simulation(self, seed: Optional[int] = None) -> Dict:
        """Run complete universe simulation from Big Bang to planetary systems"""
        print("\n╔════════════════════════════════════════════════════════╗")
        print("║   QMRT UNIVERSE SIMULATION - Full Evolution Mode      ║")
        print("╚════════════════════════════════════════════════════════╝\n")
        
        # Phase 1-5: Standard cosmological evolution
        print("📍 PHASE 1-5: Cosmological Evolution")
        cosmo_result = self.run_full_simulation(seed=seed)
        
        # Phase 6: Stellar formation
        print("\n📍 PHASE 6: Stellar Formation")
        self._evolve_stellar_formation()
        
        # Phase 7: Planetary formation
        print("\n📍 PHASE 7: Planetary System Formation")
        self._evolve_planetary_formation()
        
        # Summary
        summary = self._generate_universe_summary(cosmo_result)
        
        print("\n╔════════════════════════════════════════════════════════╗")
        print(f"║  Universe Simulation Complete                          ║")
        print(f"║  Stellar Systems: {len(self.stellar_systems):<35} ║")
        print(f"║  Habitable Worlds: {len(self.habitable_worlds):<34} ║")
        print("╚════════════════════════════════════════════════════════╝\n")
        
        return summary
    
    def _evolve_stellar_formation(self):
        """Form stellar systems from structure seeds"""
        print("  Collapsing structure seeds into protostars...")
        
        if not self.structure_seeds:
            print("  ⚠ No structure seeds found - skipping stellar formation")
            return
        
        for i, seed in enumerate(self.structure_seeds):
            # Extract substrate properties at seed location
            pos = seed['position']
            substrate_props = {
                'density': seed['density'],
                'tension': seed['tension'],
                'torsion': seed['torsion'],
                'coherence': seed['coherence'],
                'density_contrast': seed['density_contrast']
            }
            
            # Form stellar system
            stellar_system = StellarSystem(
                seed_id=i,
                position=pos,
                substrate_properties=substrate_props
            )
            
            self.stellar_systems.append(stellar_system)
        
        print(f"  ✓ Formed {len(self.stellar_systems)} stellar systems")
        
        # Log spectral distribution
        spectral_types = {}
        for system in self.stellar_systems:
            stype = system.star_type.split()[0]
            spectral_types[stype] = spectral_types.get(stype, 0) + 1
        
        print(f"  Spectral distribution: {spectral_types}")
    
    def _evolve_planetary_formation(self):
        """Identify habitable worlds from planetary systems"""
        print("  Accreting planetary disks...")
        
        total_planets = 0
        for system in self.stellar_systems:
            total_planets += len(system.planets)
            
            # Identify habitable planets
            for planet in system.planets:
                if planet['habitable']:
                    habitable_world = {
                        'stellar_system_id': system.seed_id,
                        'star_type': system.star_type,
                        'star_mass': system.star_mass,
                        'planet_id': planet['id'],
                        'orbit_au': planet['orbit_au'],
                        'mass_earth': planet['mass_earth'],
                        'substrate_origin': system.substrate,
                        'position': system.position
                    }
                    self.habitable_worlds.append(habitable_world)
        
        print(f"  ✓ Generated {total_planets} planets across {len(self.stellar_systems)} systems")
        print(f"  ✓ Identified {len(self.habitable_worlds)} potentially habitable worlds")
        
        if self.habitable_worlds:
            print(f"\n  Sample habitable world:")
            hw = self.habitable_worlds[0]
            print(f"    Star: {hw['star_type']}, {hw['star_mass']:.2f} M☉")
            print(f"    Planet: {hw['mass_earth']:.2f} M⊕ at {hw['orbit_au']:.2f} AU")
    
    def _generate_universe_summary(self, cosmo_result: Dict) -> Dict:
        """Generate complete universe summary"""
        return {
            # Cosmological data
            'cosmological_time': cosmo_result['cosmic_time'],
            'scale_factor': cosmo_result['scale_factor'],
            'structure_seeds': len(self.structure_seeds),
            
            # Stellar data
            'stellar_systems': len(self.stellar_systems),
            'stellar_distribution': self._get_stellar_distribution(),
            
            # Planetary data
            'total_planets': sum(len(s.planets) for s in self.stellar_systems),
            'habitable_worlds': len(self.habitable_worlds),
            'habitable_worlds_data': self.habitable_worlds,
            
            # System details
            'stellar_systems_data': [
                {
                    'id': s.seed_id,
                    'position': s.position,
                    'star_type': s.star_type,
                    'star_mass': round(s.star_mass, 2),
                    'luminosity': round(s.luminosity, 2),
                    'num_planets': s.num_planets,
                    'planets': s.planets,
                    'substrate': s.substrate
                }
                for s in self.stellar_systems
            ],
            
            # Metadata
            'simulation_seed': cosmo_result.get('seed'),
            'epochs_completed': len(self.snapshots)
        }
    
    def _get_stellar_distribution(self) -> Dict[str, int]:
        """Get distribution of stellar types"""
        distribution = {}
        for system in self.stellar_systems:
            stype = system.star_type.split('(')[0].strip()
            distribution[stype] = distribution.get(stype, 0) + 1
        return distribution
    
    def get_habitable_world_seeds(self) -> List[Dict]:
        """Get list of habitable worlds that can seed gameplay worlds (Mode 2)"""
        seeds = []
        for i, hw in enumerate(self.habitable_worlds):
            # Calculate death-world potential based on substrate properties
            substrate = hw['substrate_origin']
            
            # High density contrast = higher death-world potential
            density_contrast = substrate.get('density_contrast', 1.0)
            torsion = substrate.get('torsion', 0.05)
            
            # Death level estimation (1-15)
            death_level = 5  # Base
            death_level += min(int(density_contrast * 3), 5)  # +0 to +5 from density
            death_level += min(int(torsion * 30), 5)  # +0 to +5 from torsion
            death_level = max(1, min(15, death_level))
            
            seed = {
                'habitable_world_id': i,
                'stellar_system_id': hw['stellar_system_id'],
                'star_type': hw['star_type'],
                'planet_mass_earth': hw['mass_earth'],
                'orbit_au': hw['orbit_au'],
                'estimated_death_level': death_level,
                'substrate_seed': substrate,
                'cosmological_position': hw['position']
            }
            seeds.append(seed)
        
        return seeds
    
    def export_visualization_data(self) -> Dict:
        """Export data for visualization"""
        return {
            'grid_size': self.grid_size,
            'cosmic_time': self.cosmic_time,
            'scale_factor': self.scale_factor,
            'current_epoch': self.current_epoch,
            
            # Structure data
            'structure_seeds_positions': [s['position'] for s in self.structure_seeds],
            'structure_seeds_density': [s['density_contrast'] for s in self.structure_seeds],
            
            # Stellar systems
            'stellar_positions': [s.position for s in self.stellar_systems],
            'stellar_types': [s.star_type for s in self.stellar_systems],
            'stellar_masses': [s.star_mass for s in self.stellar_systems],
            
            # Habitable worlds
            'habitable_positions': [hw['position'] for hw in self.habitable_worlds],
            'habitable_count': len(self.habitable_worlds),
            
            # Substrate fields (downsampled for performance)
            'density_field_sample': self._downsample_field(self.substrate.rho_xi, 16),
            'torsion_field_sample': self._downsample_field(
                np.linalg.norm(self.substrate.tau_xi, axis=-1), 16
            )
        }
    
    def _downsample_field(self, field: np.ndarray, target_size: int) -> List:
        """Downsample 3D field for visualization"""
        step = max(1, field.shape[0] // target_size)
        downsampled = field[::step, ::step, ::step]
        return downsampled.tolist()
