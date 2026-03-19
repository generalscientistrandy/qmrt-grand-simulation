"""
Lineage System - Cross-Session Evolutionary Identity
Tracks ancestor chains, origin classification, and multi-generation survival
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid


class LineageNode:
    """Single node in ancestry chain"""
    def __init__(self, entity_id: str, entity_name: str, generation: int, 
                 birth_world_id: str, birth_death_level: int, parent_id: Optional[str] = None):
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.generation = generation
        self.birth_world_id = birth_world_id
        self.birth_death_level = birth_death_level
        self.parent_id = parent_id
        self.born_at = datetime.now(timezone.utc)
        
        # Survival metrics
        self.worlds_survived = [birth_world_id]
        self.total_predator_encounters = 0
        self.successful_hunts = 0
        self.times_hunted = 0
        self.max_death_level_survived = birth_death_level
        
        # Apex tracking
        self.apex_qualified = birth_death_level >= 10
        self.apex_verified = False
        self.predator_dominance_score = 0.0


class LineageTracker:
    """Manages lineage chains and evolutionary identity"""
    
    def __init__(self):
        self.lineages: Dict[str, LineageNode] = {}
        
    def create_lineage(self, entity_name: str, birth_world_id: str, 
                      birth_death_level: int, parent_id: Optional[str] = None) -> LineageNode:
        """Create new lineage entry
        
        Args:
            entity_name: Name of the entity (player, species, civilization)
            birth_world_id: World where entity originated
            birth_death_level: Death-world level at birth
            parent_id: Optional parent lineage ID for multi-generation tracking
        
        Returns:
            LineageNode with unique ID and generation tracking
        """
        # Determine generation
        generation = 1
        if parent_id and parent_id in self.lineages:
            generation = self.lineages[parent_id].generation + 1
            
        # Create node
        entity_id = str(uuid.uuid4())
        node = LineageNode(
            entity_id=entity_id,
            entity_name=entity_name,
            generation=generation,
            birth_world_id=birth_world_id,
            birth_death_level=birth_death_level,
            parent_id=parent_id
        )
        
        self.lineages[entity_id] = node
        return node
    
    def get_ancestry_chain(self, entity_id: str, max_depth: int = 10) -> List[LineageNode]:
        """Get full ancestry chain from entity to root ancestor"""
        if entity_id not in self.lineages:
            return []
        
        chain = []
        current = self.lineages[entity_id]
        depth = 0
        
        while current and depth < max_depth:
            chain.append(current)
            if current.parent_id and current.parent_id in self.lineages:
                current = self.lineages[current.parent_id]
            else:
                current = None
            depth += 1
            
        return chain
    
    def get_origin_classification(self, entity_id: str) -> Dict[str, any]:
        """Get origin world classification for lineage
        
        Traces back to root ancestor to determine true origin
        """
        chain = self.get_ancestry_chain(entity_id)
        if not chain:
            return {"origin_found": False}
        
        # Root ancestor (furthest back)
        root = chain[-1]
        
        return {
            "origin_found": True,
            "origin_entity_id": root.entity_id,
            "origin_entity_name": root.entity_name,
            "origin_world_id": root.birth_world_id,
            "origin_death_level": root.birth_death_level,
            "generations_from_origin": len(chain) - 1,
            "lineage_depth": len(chain)
        }
    
    def record_world_survival(self, entity_id: str, world_id: str, death_level: int):
        """Record that entity survived in a world"""
        if entity_id not in self.lineages:
            return
        
        node = self.lineages[entity_id]
        if world_id not in node.worlds_survived:
            node.worlds_survived.append(world_id)
        
        # Update max survived level
        if death_level > node.max_death_level_survived:
            node.max_death_level_survived = death_level
    
    def record_predator_encounter(self, entity_id: str, was_hunter: bool, success: bool):
        """Record predator-prey encounter
        
        Args:
            entity_id: Entity involved
            was_hunter: True if entity was the predator, False if prey
            success: True if hunt/escape was successful
        """
        if entity_id not in self.lineages:
            return
        
        node = self.lineages[entity_id]
        node.total_predator_encounters += 1
        
        if was_hunter:
            if success:
                node.successful_hunts += 1
        else:
            node.times_hunted += 1
            
        # Update predator dominance score
        self._calculate_predator_dominance(node)
    
    def _calculate_predator_dominance(self, node: LineageNode):
        """Calculate predator dominance score
        
        Score = (successful_hunts / total_encounters) × (max_level / 10) × survival_bonus
        """
        if node.total_predator_encounters == 0:
            node.predator_dominance_score = 0.0
            return
        
        hunt_ratio = node.successful_hunts / node.total_predator_encounters
        level_factor = min(node.max_death_level_survived / 10.0, 2.0)
        survival_bonus = 1.0 + (len(node.worlds_survived) * 0.1)
        
        node.predator_dominance_score = hunt_ratio * level_factor * survival_bonus
    
    def check_apex_qualification(self, entity_id: str, 
                                min_generations: int = 3,
                                min_dominance: float = 0.5) -> Dict[str, any]:
        """Check if entity qualifies for apex status
        
        Criteria:
        1. Origin from death-world level 10+
        2. Multi-generation survival (3+ generations from harsh origins)
        3. Predator dominance threshold (>0.5 score)
        4. Survived multiple worlds
        """
        if entity_id not in self.lineages:
            return {"qualified": False, "reason": "Entity not found"}
        
        node = self.lineages[entity_id]
        origin = self.get_origin_classification(entity_id)
        
        # Check criteria
        checks = {
            "origin_level": origin.get("origin_death_level", 0) >= 10,
            "multi_generation": node.generation >= min_generations,
            "predator_dominance": node.predator_dominance_score >= min_dominance,
            "world_survival": len(node.worlds_survived) >= 3
        }
        
        qualified = all(checks.values())
        
        # Calculate rarity (higher origin level = rarer)
        origin_level = origin.get("origin_death_level", 0)
        rarity_score = 0.0
        if origin_level >= 10:
            rarity_score = (origin_level - 10) / 5.0  # 0.0 at L10, 1.0 at L15
        
        return {
            "qualified": qualified,
            "checks": checks,
            "origin_death_level": origin.get("origin_death_level"),
            "generation": node.generation,
            "predator_dominance_score": node.predator_dominance_score,
            "worlds_survived_count": len(node.worlds_survived),
            "rarity_score": rarity_score,
            "apex_tier": self._determine_apex_tier(origin_level, rarity_score) if qualified else None
        }
    
    def _determine_apex_tier(self, origin_level: int, rarity_score: float) -> str:
        """Determine apex tier based on origin and rarity"""
        if origin_level >= 15:
            return "Apocalypse Survivor"
        elif origin_level >= 13:
            return "Extreme Apex"
        elif origin_level >= 10:
            if rarity_score > 0.6:
                return "Elite Apex"
            else:
                return "Standard Apex"
        return "Unqualified"
    
    def get_lineage_summary(self, entity_id: str) -> Dict:
        """Get complete lineage summary for entity"""
        if entity_id not in self.lineages:
            return {"found": False}
        
        node = self.lineages[entity_id]
        origin = self.get_origin_classification(entity_id)
        apex = self.check_apex_qualification(entity_id)
        chain = self.get_ancestry_chain(entity_id)
        
        return {
            "found": True,
            "entity_id": node.entity_id,
            "entity_name": node.entity_name,
            "generation": node.generation,
            "birth_world_id": node.birth_world_id,
            "birth_death_level": node.birth_death_level,
            "born_at": node.born_at.isoformat(),
            
            # Origin tracking
            "origin": origin,
            
            # Survival metrics
            "max_death_level_survived": node.max_death_level_survived,
            "worlds_survived_count": len(node.worlds_survived),
            "worlds_survived": node.worlds_survived,
            
            # Combat metrics
            "total_predator_encounters": node.total_predator_encounters,
            "successful_hunts": node.successful_hunts,
            "times_hunted": node.times_hunted,
            "predator_dominance_score": round(node.predator_dominance_score, 3),
            
            # Apex status
            "apex_qualified": apex["qualified"],
            "apex_checks": apex.get("checks"),
            "apex_tier": apex.get("apex_tier"),
            "rarity_score": round(apex.get("rarity_score", 0), 3),
            
            # Ancestry
            "ancestry_chain": [
                {
                    "id": ancestor.entity_id,
                    "name": ancestor.entity_name,
                    "generation": ancestor.generation,
                    "birth_level": ancestor.birth_death_level
                }
                for ancestor in chain
            ]
        }
    
    def to_dict(self, entity_id: str) -> Optional[Dict]:
        """Convert lineage node to dictionary for storage"""
        if entity_id not in self.lineages:
            return None
        
        node = self.lineages[entity_id]
        return {
            "entity_id": node.entity_id,
            "entity_name": node.entity_name,
            "generation": node.generation,
            "birth_world_id": node.birth_world_id,
            "birth_death_level": node.birth_death_level,
            "parent_id": node.parent_id,
            "born_at": node.born_at.isoformat(),
            "worlds_survived": node.worlds_survived,
            "total_predator_encounters": node.total_predator_encounters,
            "successful_hunts": node.successful_hunts,
            "times_hunted": node.times_hunted,
            "max_death_level_survived": node.max_death_level_survived,
            "apex_qualified": node.apex_qualified,
            "apex_verified": node.apex_verified,
            "predator_dominance_score": node.predator_dominance_score
        }
    
    def from_dict(self, data: Dict):
        """Load lineage node from dictionary"""
        node = LineageNode(
            entity_id=data["entity_id"],
            entity_name=data["entity_name"],
            generation=data["generation"],
            birth_world_id=data["birth_world_id"],
            birth_death_level=data["birth_death_level"],
            parent_id=data.get("parent_id")
        )
        
        node.born_at = datetime.fromisoformat(data["born_at"])
        node.worlds_survived = data.get("worlds_survived", [])
        node.total_predator_encounters = data.get("total_predator_encounters", 0)
        node.successful_hunts = data.get("successful_hunts", 0)
        node.times_hunted = data.get("times_hunted", 0)
        node.max_death_level_survived = data.get("max_death_level_survived", node.birth_death_level)
        node.apex_qualified = data.get("apex_qualified", False)
        node.apex_verified = data.get("apex_verified", False)
        node.predator_dominance_score = data.get("predator_dominance_score", 0.0)
        
        self.lineages[node.entity_id] = node
        return node
