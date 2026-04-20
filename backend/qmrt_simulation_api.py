"""
QMRT Simulation API
===================

Clean API for running 2D and 3D QMRT simulations with full metrics:
- Medium balance (E, P, D)
- Spatial structure (S)
- Ordering structure (O)
- Temporal layers (R, P)
- Spacetime coupling (I_TS)
- Causal geometry
- Emergent structures (vortices, clusters, nodes)

Mesoscopic Structures (legacy integration):
- Torsion vortices
- Strain energy nodes
- Coherence clusters
- Particle-like nodes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Tuple
import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.stats import pearsonr
import time
import math

router = APIRouter(prefix="/qmrt-sim", tags=["QMRT Simulation"])


# ============================================================
# MESOSCOPIC STRUCTURE DATA CLASSES
# ============================================================

class TorsionVortexData(BaseModel):
    """Emergent vortex structure in torsion field"""
    position: List[int]
    strength: float
    radius: float
    chirality: int  # +1 or -1
    
class StrainNodeData(BaseModel):
    """Localized strain energy concentration"""
    position: List[int]
    energy_density: float
    gradient_magnitude: float
    stability: float
    
class CoherenceClusterData(BaseModel):
    """Phase coherence cluster"""
    center: List[float]
    size: float
    coherence_strength: float
    member_count: int
    phase_value: float

class ParticleNodeData(BaseModel):
    """Emergent particle-like structure"""
    id: str
    position: List[float]
    density_concentration: float
    strain_energy: float
    effective_mass: float
    stability_score: float
    structure_type: str  # 'stable', 'transient', 'proto-particle'
    has_vortex: bool
    has_cluster: bool


# ============================================================
# STRUCTURE TRACKING DATA CLASSES
# ============================================================

class StructureHistoryPoint(BaseModel):
    """Single history point for a tracked structure."""
    t: float
    position: List[float]
    stability: Optional[float] = None
    energy: Optional[float] = None
    mass: Optional[float] = None
    size: Optional[float] = None
    strength: Optional[float] = None


class TrackedStructure(BaseModel):
    """Persistent structure tracked across frames."""
    id: str
    structure_class: str  # 'strain_node', 'particle_node', 'cluster', 'vortex'
    birth_time: float
    last_seen_time: float
    age: float
    status: str  # 'active', 'disappeared', 'merged', 'split'
    match_confidence: str  # 'high', 'medium', 'low'
    trajectory: List[List[float]]  # [[x, y, t], ...] or [[x, y, z, t], ...]
    history: List[StructureHistoryPoint]
    parent_ids: List[str] = []
    child_ids: List[str] = []
    # Latest properties (for quick access)
    current_position: List[float]
    current_stability: Optional[float] = None
    current_energy: Optional[float] = None


class TimelineSnapshot(BaseModel):
    """Structures at a single timestep in the timeline."""
    t: float
    strain_nodes: List[Dict] = []
    particle_nodes: List[Dict] = []
    coherence_clusters: List[Dict] = []
    torsion_vortices: List[Dict] = []


class TrackedStructuresCollection(BaseModel):
    """All tracked structures organized by type."""
    strain_nodes: List[TrackedStructure] = []
    particle_nodes: List[TrackedStructure] = []
    coherence_clusters: List[TrackedStructure] = []
    torsion_vortices: List[TrackedStructure] = []
    
    # Summary stats
    total_births: int = 0
    total_deaths: int = 0
    total_merges: int = 0
    total_splits: int = 0
    avg_lifetime: float = 0.0


# ============================================================
# STRUCTURE TRACKER
# ============================================================

class StructureTracker:
    """
    Tracks structure persistence across simulation frames.
    Uses spatial proximity + type consistency for matching.
    """
    
    def __init__(self, dimension: str = '2d', match_threshold: float = 5.0):
        self.dimension = dimension
        self.match_threshold = match_threshold  # Max distance for same-structure match
        self.id_counter = {'strain': 0, 'particle': 0, 'cluster': 0, 'vortex': 0}
        
        # Active structures (currently being tracked)
        self.active_structures: Dict[str, Dict] = {
            'strain_nodes': {},
            'particle_nodes': {},
            'coherence_clusters': {},
            'torsion_vortices': {}
        }
        
        # Completed structures (disappeared or merged)
        self.completed_structures: Dict[str, List[TrackedStructure]] = {
            'strain_nodes': [],
            'particle_nodes': [],
            'coherence_clusters': [],
            'torsion_vortices': []
        }
        
        # Timeline of structure snapshots
        self.timeline: List[TimelineSnapshot] = []
        
        # Event counters
        self.births = 0
        self.deaths = 0
        self.merges = 0
        self.splits = 0
    
    def _generate_id(self, struct_type: str) -> str:
        """Generate unique structure ID."""
        prefix = {'strain': 'sn', 'particle': 'pn', 'cluster': 'cc', 'vortex': 'tv'}[struct_type]
        self.id_counter[struct_type] += 1
        return f"{prefix}_{self.id_counter[struct_type]}"
    
    def _get_position(self, struct: Dict, struct_class: str) -> List[float]:
        """Extract position from structure dict."""
        if struct_class == 'coherence_clusters':
            return struct.get('center', [0, 0])
        return [float(x) for x in struct.get('position', [0, 0])]
    
    def _compute_distance(self, pos1: List[float], pos2: List[float]) -> float:
        """Compute Euclidean distance between positions."""
        return math.sqrt(sum((a - b)**2 for a, b in zip(pos1, pos2)))
    
    def _compute_similarity(self, struct1: Dict, struct2: Dict, struct_class: str) -> float:
        """Compute similarity score (0-1) between two structures."""
        similarity = 1.0
        
        if struct_class == 'strain_nodes':
            # Compare energy and stability
            e1 = struct1.get('energy_density', 0)
            e2 = struct2.get('energy_density', 0)
            s1 = struct1.get('stability', 0)
            s2 = struct2.get('stability', 0)
            if e1 > 0 and e2 > 0:
                similarity *= min(e1, e2) / max(e1, e2)
            if s1 > 0 and s2 > 0:
                similarity *= min(s1, s2) / max(s1, s2)
                
        elif struct_class == 'particle_nodes':
            # Compare mass and stability
            m1 = struct1.get('effective_mass', 0)
            m2 = struct2.get('effective_mass', 0)
            s1 = struct1.get('stability_score', 0)
            s2 = struct2.get('stability_score', 0)
            if abs(m1) > 0.01 and abs(m2) > 0.01:
                similarity *= min(abs(m1), abs(m2)) / max(abs(m1), abs(m2))
            if s1 > 0 and s2 > 0:
                similarity *= min(s1, s2) / max(s1, s2)
                
        elif struct_class == 'coherence_clusters':
            # Compare size and coherence
            sz1 = struct1.get('size', 1)
            sz2 = struct2.get('size', 1)
            c1 = struct1.get('coherence_strength', 0)
            c2 = struct2.get('coherence_strength', 0)
            if sz1 > 0 and sz2 > 0:
                similarity *= min(sz1, sz2) / max(sz1, sz2)
            if c1 > 0 and c2 > 0:
                similarity *= min(c1, c2) / max(c1, c2)
                
        elif struct_class == 'torsion_vortices':
            # Compare strength and chirality
            str1 = struct1.get('strength', 0)
            str2 = struct2.get('strength', 0)
            chi1 = struct1.get('chirality', 1)
            chi2 = struct2.get('chirality', 1)
            if str1 > 0 and str2 > 0:
                similarity *= min(str1, str2) / max(str1, str2)
            # Chirality must match
            if chi1 != chi2:
                similarity *= 0.1  # Heavy penalty for chirality mismatch
        
        return similarity
    
    def _match_confidence(self, distance: float, similarity: float) -> str:
        """Determine match confidence level."""
        if distance < self.match_threshold * 0.3 and similarity > 0.8:
            return 'high'
        elif distance < self.match_threshold * 0.7 and similarity > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _create_tracked_structure(self, struct: Dict, struct_class: str, t: float, 
                                   struct_type: str) -> Dict:
        """Create new tracked structure entry."""
        pos = self._get_position(struct, struct_class)
        
        history_point = {
            't': t,
            'position': pos,
            'stability': struct.get('stability', struct.get('stability_score')),
            'energy': struct.get('energy_density', struct.get('strain_energy')),
            'mass': struct.get('effective_mass'),
            'size': struct.get('size'),
            'strength': struct.get('strength')
        }
        
        traj_point = pos + [t]
        
        return {
            'id': self._generate_id(struct_type),
            'structure_class': struct_class,
            'birth_time': t,
            'last_seen_time': t,
            'age': 0.0,
            'status': 'active',
            'match_confidence': 'high',
            'trajectory': [traj_point],
            'history': [history_point],
            'parent_ids': [],
            'child_ids': [],
            'current_position': pos,
            'current_stability': history_point['stability'],
            'current_energy': history_point['energy'],
            '_raw': struct  # Keep raw data for matching
        }
    
    def _update_tracked_structure(self, tracked: Dict, struct: Dict, struct_class: str, 
                                   t: float, confidence: str):
        """Update existing tracked structure with new observation."""
        pos = self._get_position(struct, struct_class)
        
        history_point = {
            't': t,
            'position': pos,
            'stability': struct.get('stability', struct.get('stability_score')),
            'energy': struct.get('energy_density', struct.get('strain_energy')),
            'mass': struct.get('effective_mass'),
            'size': struct.get('size'),
            'strength': struct.get('strength')
        }
        
        traj_point = pos + [t]
        
        tracked['last_seen_time'] = t
        tracked['age'] = t - tracked['birth_time']
        tracked['trajectory'].append(traj_point)
        tracked['history'].append(history_point)
        tracked['current_position'] = pos
        tracked['current_stability'] = history_point['stability']
        tracked['current_energy'] = history_point['energy']
        tracked['match_confidence'] = confidence
        tracked['_raw'] = struct
    
    def process_frame(self, structures: Dict, t: float):
        """Process a single frame of structure data with merge/split detection."""
        
        # Store timeline snapshot
        timeline_snap = TimelineSnapshot(
            t=t,
            strain_nodes=structures.get('strain_nodes', []),
            particle_nodes=structures.get('particle_nodes', []),
            coherence_clusters=structures.get('coherence_clusters', []),
            torsion_vortices=structures.get('torsion_vortices', [])
        )
        self.timeline.append(timeline_snap)
        
        # Process each structure class
        struct_type_map = {
            'strain_nodes': 'strain',
            'particle_nodes': 'particle',
            'coherence_clusters': 'cluster',
            'torsion_vortices': 'vortex'
        }
        
        for struct_class, struct_type in struct_type_map.items():
            current_structs = structures.get(struct_class, [])
            active = self.active_structures[struct_class]
            
            # Track which active structures were matched
            matched_active_ids = set()
            matched_current_indices = set()
            
            # Build full match matrix: for each current struct, find ALL nearby active structs
            # This helps detect merges (multiple active → one current)
            match_matrix = {}  # curr_idx -> [(active_id, confidence, score, distance)]
            reverse_match = {}  # active_id -> [(curr_idx, confidence, score, distance)]
            
            for curr_idx, curr_struct in enumerate(current_structs):
                curr_pos = self._get_position(curr_struct, struct_class)
                match_matrix[curr_idx] = []
                
                for active_id, active_struct in active.items():
                    active_pos = active_struct['current_position']
                    distance = self._compute_distance(curr_pos, active_pos)
                    
                    if distance <= self.match_threshold:
                        similarity = self._compute_similarity(curr_struct, active_struct['_raw'], struct_class)
                        score = similarity * (1 - distance / self.match_threshold)
                        confidence = self._match_confidence(distance, similarity)
                        
                        match_matrix[curr_idx].append((active_id, confidence, score, distance))
                        
                        if active_id not in reverse_match:
                            reverse_match[active_id] = []
                        reverse_match[active_id].append((curr_idx, confidence, score, distance))
            
            # Sort each list by score
            for curr_idx in match_matrix:
                match_matrix[curr_idx].sort(key=lambda x: x[2], reverse=True)
            for active_id in reverse_match:
                reverse_match[active_id].sort(key=lambda x: x[2], reverse=True)
            
            # ============================================
            # MERGE DETECTION (Conservative)
            # Multiple active structures → one current structure
            # Criteria: 
            #   - Current struct has 2+ high-confidence matches to different active structs
            #   - All parents are within close proximity to each other
            # ============================================
            merge_events = []  # [(curr_idx, [parent_ids], combined_position)]
            
            for curr_idx, matches in match_matrix.items():
                # Need at least 2 high-quality matches
                high_quality_matches = [m for m in matches if m[1] in ('high', 'medium') and m[2] > 0.3]
                
                if len(high_quality_matches) >= 2:
                    # Check if parent structures are close to each other (were converging)
                    parent_ids = [m[0] for m in high_quality_matches[:3]]  # Max 3 parents
                    parent_positions = [active[pid]['current_position'] for pid in parent_ids if pid in active]
                    
                    if len(parent_positions) >= 2:
                        # Calculate max pairwise distance between parents
                        max_parent_dist = 0
                        for i in range(len(parent_positions)):
                            for j in range(i + 1, len(parent_positions)):
                                d = self._compute_distance(parent_positions[i], parent_positions[j])
                                max_parent_dist = max(max_parent_dist, d)
                        
                        # Conservative: parents must be within 2x match threshold
                        if max_parent_dist < self.match_threshold * 2:
                            merge_events.append((curr_idx, parent_ids))
            
            # ============================================
            # SPLIT DETECTION (Conservative)  
            # One active structure → multiple current structures
            # Criteria:
            #   - Active struct has 2+ high-confidence matches to different current structs
            #   - Children are spreading apart from parent location
            # ============================================
            split_events = []  # [(active_id, [child_curr_indices])]
            
            for active_id, matches in reverse_match.items():
                # Need at least 2 high-quality matches
                high_quality_matches = [m for m in matches if m[1] in ('high', 'medium') and m[2] > 0.3]
                
                if len(high_quality_matches) >= 2:
                    child_indices = [m[0] for m in high_quality_matches[:3]]  # Max 3 children
                    
                    # Check that children aren't already matched to other active structures more strongly
                    # (i.e., this active struct is the best match for all children)
                    valid_children = []
                    for ci in child_indices:
                        if match_matrix[ci] and match_matrix[ci][0][0] == active_id:
                            # This active is the best match for this child
                            valid_children.append(ci)
                    
                    if len(valid_children) >= 2:
                        split_events.append((active_id, valid_children))
            
            # ============================================
            # APPLY EVENTS AND REGULAR MATCHING
            # ============================================
            
            # Process merges first (they consume multiple active structs)
            for curr_idx, parent_ids in merge_events:
                if curr_idx in matched_current_indices:
                    continue
                    
                # Check all parents are still available
                available_parents = [pid for pid in parent_ids if pid in active and pid not in matched_active_ids]
                if len(available_parents) < 2:
                    continue  # Not enough parents left, skip merge
                
                # Create merged structure
                curr_struct = current_structs[curr_idx]
                merged = self._create_tracked_structure(curr_struct, struct_class, t, struct_type)
                merged['parent_ids'] = available_parents
                merged['status'] = 'active'
                
                # Mark parents as merged
                for pid in available_parents:
                    parent = active.pop(pid)
                    parent['status'] = 'merged'
                    parent['child_ids'] = [merged['id']]
                    self.completed_structures[struct_class].append(
                        TrackedStructure(**{k: v for k, v in parent.items() if k != '_raw'})
                    )
                    matched_active_ids.add(pid)
                
                # Add merged structure
                active[merged['id']] = merged
                matched_current_indices.add(curr_idx)
                self.merges += 1
            
            # Process splits (they consume one active struct, create multiple)
            for active_id, child_indices in split_events:
                if active_id in matched_active_ids:
                    continue
                
                # Check children are available
                available_children = [ci for ci in child_indices if ci not in matched_current_indices]
                if len(available_children) < 2:
                    continue  # Not enough children, skip split
                
                # Mark parent as split
                parent = active.pop(active_id)
                parent['status'] = 'split'
                
                child_ids = []
                for ci in available_children:
                    curr_struct = current_structs[ci]
                    child = self._create_tracked_structure(curr_struct, struct_class, t, struct_type)
                    child['parent_ids'] = [active_id]
                    child_ids.append(child['id'])
                    active[child['id']] = child
                    matched_current_indices.add(ci)
                
                parent['child_ids'] = child_ids
                self.completed_structures[struct_class].append(
                    TrackedStructure(**{k: v for k, v in parent.items() if k != '_raw'})
                )
                matched_active_ids.add(active_id)
                self.splits += 1
            
            # Build regular matches list (excluding merge/split participants)
            matches = []
            for curr_idx, match_list in match_matrix.items():
                if curr_idx in matched_current_indices:
                    continue
                if match_list:
                    best = match_list[0]  # (active_id, confidence, score, distance)
                    if best[0] not in matched_active_ids:
                        matches.append((curr_idx, best[0], best[1], best[2]))
            
            # Sort matches by score (highest first) to resolve conflicts
            matches.sort(key=lambda x: x[3], reverse=True)
            
            # Apply matches (greedy, best-first)
            for curr_idx, active_id, confidence, _ in matches:
                if curr_idx in matched_current_indices or active_id in matched_active_ids:
                    continue
                
                self._update_tracked_structure(
                    active[active_id], 
                    current_structs[curr_idx], 
                    struct_class, 
                    t, 
                    confidence
                )
                matched_active_ids.add(active_id)
                matched_current_indices.add(curr_idx)
            
            # Handle disappeared structures (not matched, merged, or split)
            for active_id in list(active.keys()):
                if active_id not in matched_active_ids:
                    # Structure disappeared
                    disappeared = active.pop(active_id)
                    disappeared['status'] = 'disappeared'
                    self.completed_structures[struct_class].append(
                        TrackedStructure(**{k: v for k, v in disappeared.items() if k != '_raw'})
                    )
                    self.deaths += 1
            
            # Handle new births (current structs not matched to anything)
            for curr_idx, curr_struct in enumerate(current_structs):
                if curr_idx not in matched_current_indices:
                    # New structure born
                    new_tracked = self._create_tracked_structure(
                        curr_struct, struct_class, t, struct_type
                    )
                    active[new_tracked['id']] = new_tracked
                    self.births += 1
    
    def finalize(self, final_time: float) -> TrackedStructuresCollection:
        """Finalize tracking and return results."""
        result = TrackedStructuresCollection(
            total_births=self.births,
            total_deaths=self.deaths,
            total_merges=self.merges,
            total_splits=self.splits
        )
        
        # Collect all structures (active + completed)
        for struct_class in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
            all_structs = []
            
            # Add completed structures
            all_structs.extend(self.completed_structures[struct_class])
            
            # Add active structures (still alive at end)
            for tracked in self.active_structures[struct_class].values():
                tracked['age'] = final_time - tracked['birth_time']
                all_structs.append(
                    TrackedStructure(**{k: v for k, v in tracked.items() if k != '_raw'})
                )
            
            setattr(result, struct_class, all_structs)
        
        # Compute average lifetime
        all_lifetimes = []
        for struct_class in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
            for s in getattr(result, struct_class):
                all_lifetimes.append(s.age)
        
        if all_lifetimes:
            result.avg_lifetime = sum(all_lifetimes) / len(all_lifetimes)
        
        return result
    
    def get_timeline(self) -> List[TimelineSnapshot]:
        """Return the timeline of structure snapshots."""
        return self.timeline


# ============================================================
# MODELS
# ============================================================

class SimulationConfig(BaseModel):
    """Configuration for QMRT simulation."""
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=60, ge=20, le=100, description="Grid size")
    alpha: float = Field(default=0.5, ge=0.1, le=0.9, description="Backreaction coupling β")
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0, description="Relaxation rate λ")
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1, description="Wave damping γ")
    steps: int = Field(default=300, ge=50, le=1000, description="Simulation steps")
    sample_interval: int = Field(default=10, ge=1, le=50, description="Measurement interval")


class TimePoint(BaseModel):
    """Single time point measurement."""
    t: float
    E_total: float
    E_kinetic: float
    E_gradient: float
    S_total: float
    O_total: float
    R_rate: float
    P_persistence: float
    I_TS: float
    isotropy_cv: float
    confinement: float
    # Emergent structures counts
    vortex_count: int = 0
    cluster_count: int = 0
    strain_node_count: int = 0
    particle_node_count: int = 0
    mean_density: float = 1.0
    density_variance: float = 0.0


class StructuresSnapshot(BaseModel):
    """Mesoscopic structures at a point in time."""
    t: float
    torsion_vortices: List[TorsionVortexData] = []
    strain_nodes: List[StrainNodeData] = []
    coherence_clusters: List[CoherenceClusterData] = []
    particle_nodes: List[ParticleNodeData] = []


class SimulationResult(BaseModel):
    """Complete simulation result with unified metrics + structures."""
    dimension: str
    config: Dict
    duration_seconds: float
    
    # Time series measurements (new QMRT metrics)
    measurements: List[TimePoint]
    
    # Final metrics summary
    balance_achieved: bool
    balance_E_cv: float
    
    spatial_S_mean: float
    ordering_O_mean: float
    rate_R_mean: float
    persistence_P_mean: float
    coupling_I_TS_mean: float
    
    geometry_isotropic: bool
    geometry_confined: bool
    
    # Correlations
    rho_RS: float
    rho_PS: float
    rho_OS: float
    
    # === MESOSCOPIC STRUCTURES (legacy data) ===
    structures: StructuresSnapshot  # Final snapshot of all structures
    
    # Structure summary counts
    total_vortices: int = 0
    total_clusters: int = 0
    total_strain_nodes: int = 0
    total_particle_nodes: int = 0
    stable_nodes: int = 0
    proto_nodes: int = 0
    transient_nodes: int = 0
    
    # Field snapshots (for visualization)
    field_snapshots: List[Dict]
    
    # === STRUCTURE TIME TRACKING ===
    structures_timeline: List[TimelineSnapshot] = []  # Sampled history
    tracked_structures: Optional[TrackedStructuresCollection] = None  # Persistent object histories
    
    # Tracking summary
    tracking_births: int = 0
    tracking_deaths: int = 0
    tracking_merges: int = 0
    tracking_splits: int = 0
    tracking_avg_lifetime: float = 0.0


# ============================================================
# SIMULATORS
# ============================================================

class QMRTSimulator2D:
    """2D QMRT dynamical medium simulator."""
    
    def __init__(self, size=60, c_0=2.0, tau_0=1.0, beta=0.5,
                 lambda_relax=0.5, D_medium=0.1, gamma_wave=0.01, dt=0.04):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        self.tau_prev = self.tau.copy()
        
        self.source_center = (size // 2, size // 2)
        
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_laplacian(self, f):
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
    
    def compute_gradient_magnitude(self, f):
        gx = np.roll(f, -1, 0) - f
        gy = np.roll(f, -1, 1) - f
        return np.sqrt(gx**2 + gy**2)
    
    def step(self):
        self.tau_prev = self.tau.copy()
        rho = self.phi**2 + self.phi_dot**2
        
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center=None, amplitude=3.0, width=4.0):
        if center is None:
            center = self.source_center
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))
        self.source_center = center
    
    def measure(self, t):
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        
        # Energy
        grad_phi = self.compute_gradient_magnitude(self.phi)
        E_kinetic = 0.5 * np.sum(self.phi_dot**2)
        E_gradient = 0.5 * np.sum(c_eff**2 * grad_phi**2)
        E_total = E_kinetic + E_gradient
        
        # Spatial S
        c_mean = np.mean(c_eff)
        c_std = np.std(c_eff)
        S_metric = c_std / (c_mean + 1e-10)
        grad_c = self.compute_gradient_magnitude(c_eff)
        S_grad = np.mean(grad_c)
        S_total = np.sqrt(S_metric**2 + S_grad**2)
        
        # Ordering O
        O_capacity = c_std / (c_mean + 1e-10)
        O_total = O_capacity * S_grad * np.var(c_eff)
        
        # Temporal R, P
        tau_change = np.abs(self.tau - self.tau_prev)
        R_rate = np.mean(tau_change) / self.dt if self.dt > 0 else 0
        P_persistence = 1.0 / (1.0 + R_rate)
        
        # Coupling I_TS
        S_flat = c_eff.flatten()
        R_flat = tau_change.flatten()
        P_flat = gaussian_filter(rho, sigma=3.0).flatten()
        O_flat = (1.0 / (c_eff + 0.1)).flatten()
        
        rho_RS = pearsonr(R_flat, S_flat)[0] if np.std(R_flat) > 1e-10 else 0
        rho_PS = pearsonr(P_flat, S_flat)[0] if np.std(P_flat) > 1e-10 else 0
        rho_OS = pearsonr(O_flat, S_flat)[0] if np.std(O_flat) > 1e-10 else 0
        I_TS = np.sqrt(rho_RS**2 + rho_PS**2 + rho_OS**2) / np.sqrt(3)
        
        # Geometry (2D)
        cx, cy = self.source_center
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        energy_x = np.sum(rho[cx:, cy])
        energy_y = np.sum(rho[cx, cy:])
        isotropy_cv = np.std([energy_x, energy_y]) / (np.mean([energy_x, energy_y]) + 1e-10)
        
        cone_radius = c_mean * t
        inside = r <= cone_radius
        confinement = np.sum(rho[inside]) / (np.sum(rho) + 1e-10) * 100 if cone_radius > 0 else 100
        
        return {
            't': float(t),
            'E_total': float(E_total),
            'E_kinetic': float(E_kinetic),
            'E_gradient': float(E_gradient),
            'S_total': float(S_total),
            'O_total': float(O_total),
            'R_rate': float(R_rate),
            'P_persistence': float(P_persistence),
            'I_TS': float(I_TS),
            'isotropy_cv': float(isotropy_cv),
            'confinement': float(confinement),
            'rho_RS': float(rho_RS),
            'rho_PS': float(rho_PS),
            'rho_OS': float(rho_OS),
        }
    
    def get_field_snapshot(self):
        """Get field data for visualization."""
        rho = self.phi**2 + self.phi_dot**2
        c_eff = self.compute_c_eff()
        
        # Downsample for transfer
        step = max(1, self.size // 32)
        
        return {
            'rho': rho[::step, ::step].tolist(),
            'c_eff': c_eff[::step, ::step].tolist(),
            'tau': self.tau[::step, ::step].tolist(),
        }
    
    # ============================================================
    # MESOSCOPIC STRUCTURE DETECTION (2D)
    # ============================================================
    
    def detect_torsion_vortices(self, vortex_threshold: float = 0.03) -> List[Dict]:
        """
        Detect vortex structures using vorticity (curl of velocity-like field).
        In 2D, we use the scalar curl of the velocity field.
        """
        vortices = []
        
        # Compute vorticity: ∂v_y/∂x - ∂v_x/∂y
        # Use phi_dot gradient as velocity proxy
        vx = np.roll(self.phi_dot, -1, axis=0) - np.roll(self.phi_dot, 1, axis=0)
        vy = np.roll(self.phi_dot, -1, axis=1) - np.roll(self.phi_dot, 1, axis=1)
        
        # Curl in 2D is scalar: ω = ∂v_y/∂x - ∂v_x/∂y
        dvx_dy = np.roll(vx, -1, axis=1) - np.roll(vx, 1, axis=1)
        dvy_dx = np.roll(vy, -1, axis=0) - np.roll(vy, 1, axis=0)
        vorticity = dvy_dx - dvx_dy
        vorticity_mag = np.abs(vorticity)
        
        # Find local maxima above threshold
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                strength = vorticity_mag[i, j]
                
                if strength > vortex_threshold:
                    # Check if local maximum
                    local_region = vorticity_mag[i-1:i+2, j-1:j+2]
                    if strength >= np.max(local_region):
                        chirality = 1 if vorticity[i, j] > 0 else -1
                        
                        # Estimate radius (half-strength decay)
                        radius = self._estimate_vortex_radius_2d(vorticity_mag, i, j, strength)
                        
                        vortices.append({
                            'position': [i, j],
                            'strength': float(strength),
                            'radius': float(radius),
                            'chirality': int(chirality)
                        })
        
        return vortices
    
    def _estimate_vortex_radius_2d(self, vort_mag: np.ndarray, ci: int, cj: int, 
                                   center_strength: float) -> float:
        """Estimate vortex radius from vorticity decay."""
        for r in range(1, min(10, self.size // 4)):
            samples = []
            for di in [-r, 0, r]:
                for dj in [-r, 0, r]:
                    if di == dj == 0:
                        continue
                    ni, nj = ci + di, cj + dj
                    if 0 <= ni < self.size and 0 <= nj < self.size:
                        samples.append(vort_mag[ni, nj])
            
            if samples and np.mean(samples) < center_strength * 0.5:
                return float(r)
        return 1.0
    
    def detect_strain_energy_nodes(self, strain_threshold: float = 0.01) -> List[Dict]:
        """Detect localized strain energy concentrations."""
        strain_nodes = []
        
        # Compute strain energy density from density gradient
        rho = self.phi**2 + self.phi_dot**2
        grad_x = np.roll(rho, -1, axis=0) - rho
        grad_y = np.roll(rho, -1, axis=1) - rho
        strain_energy = grad_x**2 + grad_y**2
        
        # Find local maxima above threshold
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                energy = strain_energy[i, j]
                
                if energy > strain_threshold:
                    local_region = strain_energy[i-1:i+2, j-1:j+2]
                    if energy >= np.max(local_region):
                        grad_mag = np.sqrt(grad_x[i, j]**2 + grad_y[i, j]**2)
                        stability = self._compute_node_stability_2d(strain_energy, i, j)
                        
                        strain_nodes.append({
                            'position': [i, j],
                            'energy_density': float(energy),
                            'gradient_magnitude': float(grad_mag),
                            'stability': float(stability)
                        })
        
        return strain_nodes
    
    def _compute_node_stability_2d(self, energy_field: np.ndarray, ci: int, cj: int) -> float:
        """Compute stability of energy concentration."""
        center_energy = energy_field[ci, cj]
        
        window = 3
        i1, i2 = max(0, ci-window), min(self.size, ci+window+1)
        j1, j2 = max(0, cj-window), min(self.size, cj+window+1)
        
        local_region = energy_field[i1:i2, j1:j2]
        mean_local = np.mean(local_region)
        std_local = np.std(local_region)
        
        if std_local > 0:
            stability = (center_energy - mean_local) / std_local
            return float(min(1.0, max(0.0, stability / 3.0)))
        return 0.0
    
    def detect_coherence_clusters(self, coherence_threshold: float = 0.02) -> List[Dict]:
        """Detect phase coherence clustering."""
        clusters = []
        
        # Use smoothed energy density as coherence proxy
        rho = self.phi**2 + self.phi_dot**2
        coherence = gaussian_filter(rho, sigma=2.0)
        
        # Find regions of high coherence
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                if coherence[i, j] > coherence_threshold:
                    window = 3
                    local_region = coherence[i-window:i+window+1, j-window:j+window+1]
                    
                    if coherence[i, j] >= np.max(local_region):
                        cluster = self._characterize_cluster_2d(coherence, i, j, window, coherence_threshold)
                        if cluster:
                            clusters.append(cluster)
        
        return clusters
    
    def _characterize_cluster_2d(self, coherence: np.ndarray, ci: int, cj: int, 
                                  window: int, threshold: float) -> Optional[Dict]:
        """Characterize a coherence cluster."""
        i1, i2 = max(0, ci-window), min(self.size, ci+window+1)
        j1, j2 = max(0, cj-window), min(self.size, cj+window+1)
        
        local_region = coherence[i1:i2, j1:j2]
        threshold_mask = local_region > threshold * 0.5
        member_count = int(np.sum(threshold_mask))
        
        if member_count < 3:  # Minimum cluster size for 2D
            return None
        
        coords = np.array(np.where(threshold_mask))
        weights = local_region[threshold_mask]
        
        if len(weights) == 0:
            return None
        
        center_local = np.average(coords, axis=1, weights=weights)
        center_global = [float(center_local[0] + i1), float(center_local[1] + j1)]
        
        size = float(np.sqrt(np.mean((coords - center_local[:, None])**2)))
        coherence_strength = float(np.mean(local_region[threshold_mask]))
        phase_value = float(np.mean(self.phi[i1:i2, j1:j2][threshold_mask]))
        
        return {
            'center': center_global,
            'size': size,
            'coherence_strength': coherence_strength,
            'member_count': member_count,
            'phase_value': phase_value
        }
    
    def identify_particle_nodes(self, strain_nodes: List[Dict], vortices: List[Dict],
                                clusters: List[Dict]) -> List[Dict]:
        """Identify emergent particle-like structures from co-located features."""
        particle_nodes = []
        rho = self.phi**2 + self.phi_dot**2
        
        for idx, strain in enumerate(strain_nodes):
            pos = strain['position']
            i, j = pos[0], pos[1]
            
            # Find nearby vortex
            has_vortex = False
            for vortex in vortices:
                vpos = vortex['position']
                dist = math.sqrt((i - vpos[0])**2 + (j - vpos[1])**2)
                if dist < 3:
                    has_vortex = True
                    break
            
            # Find nearby cluster
            has_cluster = False
            for cluster in clusters:
                cpos = cluster['center']
                dist = math.sqrt((i - cpos[0])**2 + (j - cpos[1])**2)
                if dist < 3:
                    has_cluster = True
                    break
            
            if has_vortex or has_cluster:
                density_conc = float(rho[i, j] - np.mean(rho))
                effective_mass = density_conc * strain['energy_density']
                
                stability = strain['stability']
                if has_vortex:
                    stability += 0.2
                if has_cluster:
                    stability += 0.3
                stability = min(1.0, stability)
                
                if stability > 0.7:
                    structure_type = 'stable'
                elif stability > 0.4:
                    structure_type = 'proto-particle'
                else:
                    structure_type = 'transient'
                
                particle_nodes.append({
                    'id': f"node_2d_{idx}",
                    'position': [float(i), float(j)],
                    'density_concentration': density_conc,
                    'strain_energy': strain['energy_density'],
                    'effective_mass': effective_mass,
                    'stability_score': stability,
                    'structure_type': structure_type,
                    'has_vortex': has_vortex,
                    'has_cluster': has_cluster
                })
        
        return particle_nodes
    
    def detect_all_structures(self) -> Dict:
        """Detect all mesoscopic structures and return unified data."""
        vortices = self.detect_torsion_vortices()
        strain_nodes = self.detect_strain_energy_nodes()
        clusters = self.detect_coherence_clusters()
        particle_nodes = self.identify_particle_nodes(strain_nodes, vortices, clusters)
        
        return {
            'torsion_vortices': vortices,
            'strain_nodes': strain_nodes,
            'coherence_clusters': clusters,
            'particle_nodes': particle_nodes
        }


class QMRTSimulator3D:
    """3D QMRT dynamical medium simulator."""
    
    def __init__(self, size=40, c_0=2.0, tau_0=1.0, beta=0.5,
                 lambda_relax=0.5, D_medium=0.1, gamma_wave=0.01, dt=0.04):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.beta = beta
        self.lambda_relax = lambda_relax
        self.D_medium = D_medium
        self.gamma_wave = gamma_wave
        self.dt = dt
        
        self.phi = np.zeros((size, size, size))
        self.phi_dot = np.zeros((size, size, size))
        self.tau = np.ones((size, size, size)) * tau_0
        self.tau_prev = self.tau.copy()
        
        self.source_center = (size // 2, size // 2, size // 2)
        
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta * rho_smooth / rho_max)
    
    def compute_laplacian(self, f):
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) +
                np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6*f)
    
    def compute_gradient_magnitude(self, f):
        gx = np.roll(f, -1, 0) - f
        gy = np.roll(f, -1, 1) - f
        gz = np.roll(f, -1, 2) - f
        return np.sqrt(gx**2 + gy**2 + gz**2)
    
    def step(self):
        self.tau_prev = self.tau.copy()
        rho = self.phi**2 + self.phi_dot**2
        
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_relax * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_wave * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center=None, amplitude=4.0, width=3.0):
        if center is None:
            center = self.source_center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2 + (z - center[2])**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))
        self.source_center = center
    
    def measure(self, t):
        c_eff = self.compute_c_eff()
        rho = self.phi**2 + self.phi_dot**2
        
        # Energy
        grad_phi = self.compute_gradient_magnitude(self.phi)
        E_kinetic = 0.5 * np.sum(self.phi_dot**2)
        E_gradient = 0.5 * np.sum(c_eff**2 * grad_phi**2)
        E_total = E_kinetic + E_gradient
        
        # Spatial S
        c_mean = np.mean(c_eff)
        c_std = np.std(c_eff)
        S_metric = c_std / (c_mean + 1e-10)
        grad_c = self.compute_gradient_magnitude(c_eff)
        S_grad = np.mean(grad_c)
        S_total = np.sqrt(S_metric**2 + S_grad**2)
        
        # Ordering O
        O_capacity = c_std / (c_mean + 1e-10)
        O_total = O_capacity * S_grad * np.var(c_eff)
        
        # Temporal R, P
        tau_change = np.abs(self.tau - self.tau_prev)
        R_rate = np.mean(tau_change) / self.dt if self.dt > 0 else 0
        P_persistence = 1.0 / (1.0 + R_rate)
        
        # Coupling I_TS
        S_flat = c_eff.flatten()
        R_flat = tau_change.flatten()
        P_flat = gaussian_filter(rho, sigma=3.0).flatten()
        O_flat = (1.0 / (c_eff + 0.1)).flatten()
        
        rho_RS = pearsonr(R_flat, S_flat)[0] if np.std(R_flat) > 1e-10 else 0
        rho_PS = pearsonr(P_flat, S_flat)[0] if np.std(P_flat) > 1e-10 else 0
        rho_OS = pearsonr(O_flat, S_flat)[0] if np.std(O_flat) > 1e-10 else 0
        I_TS = np.sqrt(rho_RS**2 + rho_PS**2 + rho_OS**2) / np.sqrt(3)
        
        # 3D Geometry
        cx, cy, cz = self.source_center
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size),
                             np.arange(self.size), indexing='ij')
        r = np.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
        
        energy_x = np.sum(rho[cx:, cy, cz])
        energy_y = np.sum(rho[cx, cy:, cz])
        energy_z = np.sum(rho[cx, cy, cz:])
        isotropy_cv = np.std([energy_x, energy_y, energy_z]) / (np.mean([energy_x, energy_y, energy_z]) + 1e-10)
        
        cone_radius = c_mean * t
        inside = r <= cone_radius
        confinement = np.sum(rho[inside]) / (np.sum(rho) + 1e-10) * 100 if cone_radius > 0 else 100
        
        return {
            't': float(t),
            'E_total': float(E_total),
            'E_kinetic': float(E_kinetic),
            'E_gradient': float(E_gradient),
            'S_total': float(S_total),
            'O_total': float(O_total),
            'R_rate': float(R_rate),
            'P_persistence': float(P_persistence),
            'I_TS': float(I_TS),
            'isotropy_cv': float(isotropy_cv),
            'confinement': float(confinement),
            'rho_RS': float(rho_RS),
            'rho_PS': float(rho_PS),
            'rho_OS': float(rho_OS),
        }
    
    def get_field_snapshot(self):
        """Get central slice for visualization."""
        mid = self.size // 2
        rho = self.phi**2 + self.phi_dot**2
        c_eff = self.compute_c_eff()
        
        # Central slice, downsampled
        step = max(1, self.size // 32)
        
        return {
            'rho_xy': rho[:, :, mid][::step, ::step].tolist(),
            'rho_xz': rho[:, mid, :][::step, ::step].tolist(),
            'rho_yz': rho[mid, :, :][::step, ::step].tolist(),
            'c_eff_xy': c_eff[:, :, mid][::step, ::step].tolist(),
        }
    
    # ============================================================
    # MESOSCOPIC STRUCTURE DETECTION (3D)
    # ============================================================
    
    def _compute_curl_3d(self, vx: np.ndarray, vy: np.ndarray, vz: np.ndarray) -> np.ndarray:
        """Compute curl of a 3D vector field."""
        # curl_x = ∂vz/∂y - ∂vy/∂z
        dvz_dy = np.roll(vz, -1, axis=1) - np.roll(vz, 1, axis=1)
        dvy_dz = np.roll(vy, -1, axis=2) - np.roll(vy, 1, axis=2)
        curl_x = dvz_dy - dvy_dz
        
        # curl_y = ∂vx/∂z - ∂vz/∂x
        dvx_dz = np.roll(vx, -1, axis=2) - np.roll(vx, 1, axis=2)
        dvz_dx = np.roll(vz, -1, axis=0) - np.roll(vz, 1, axis=0)
        curl_y = dvx_dz - dvz_dx
        
        # curl_z = ∂vy/∂x - ∂vx/∂y
        dvy_dx = np.roll(vy, -1, axis=0) - np.roll(vy, 1, axis=0)
        dvx_dy = np.roll(vx, -1, axis=1) - np.roll(vx, 1, axis=1)
        curl_z = dvy_dx - dvx_dy
        
        return np.stack([curl_x, curl_y, curl_z], axis=-1)
    
    def detect_torsion_vortices(self, vortex_threshold: float = 0.03) -> List[Dict]:
        """Detect vortex structures in 3D using vorticity."""
        vortices = []
        
        # Compute velocity-like field from phi_dot gradients
        vx = np.roll(self.phi_dot, -1, axis=0) - np.roll(self.phi_dot, 1, axis=0)
        vy = np.roll(self.phi_dot, -1, axis=1) - np.roll(self.phi_dot, 1, axis=1)
        vz = np.roll(self.phi_dot, -1, axis=2) - np.roll(self.phi_dot, 1, axis=2)
        
        vorticity = self._compute_curl_3d(vx, vy, vz)
        vorticity_mag = np.linalg.norm(vorticity, axis=-1)
        
        # Find local maxima above threshold
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                for k in range(2, self.size - 2):
                    strength = vorticity_mag[i, j, k]
                    
                    if strength > vortex_threshold:
                        local_region = vorticity_mag[i-1:i+2, j-1:j+2, k-1:k+2]
                        if strength >= np.max(local_region):
                            # Chirality from dominant vorticity component
                            vort_vec = vorticity[i, j, k]
                            chirality = 1 if vort_vec[2] > 0 else -1
                            
                            radius = self._estimate_vortex_radius_3d(vorticity_mag, i, j, k, strength)
                            
                            vortices.append({
                                'position': [i, j, k],
                                'strength': float(strength),
                                'radius': float(radius),
                                'chirality': int(chirality)
                            })
        
        return vortices
    
    def _estimate_vortex_radius_3d(self, vort_mag: np.ndarray, ci: int, cj: int, ck: int,
                                    center_strength: float) -> float:
        """Estimate vortex radius from vorticity decay."""
        for r in range(1, min(10, self.size // 4)):
            samples = []
            for di in [-r, 0, r]:
                for dj in [-r, 0, r]:
                    for dk in [-r, 0, r]:
                        if di == dj == dk == 0:
                            continue
                        ni, nj, nk = ci + di, cj + dj, ck + dk
                        if 0 <= ni < self.size and 0 <= nj < self.size and 0 <= nk < self.size:
                            samples.append(vort_mag[ni, nj, nk])
            
            if samples and np.mean(samples) < center_strength * 0.5:
                return float(r)
        return 1.0
    
    def detect_strain_energy_nodes(self, strain_threshold: float = 0.01) -> List[Dict]:
        """Detect localized strain energy concentrations in 3D."""
        strain_nodes = []
        
        rho = self.phi**2 + self.phi_dot**2
        grad_x = np.roll(rho, -1, axis=0) - rho
        grad_y = np.roll(rho, -1, axis=1) - rho
        grad_z = np.roll(rho, -1, axis=2) - rho
        strain_energy = grad_x**2 + grad_y**2 + grad_z**2
        
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                for k in range(2, self.size - 2):
                    energy = strain_energy[i, j, k]
                    
                    if energy > strain_threshold:
                        local_region = strain_energy[i-1:i+2, j-1:j+2, k-1:k+2]
                        if energy >= np.max(local_region):
                            grad_mag = np.sqrt(grad_x[i, j, k]**2 + grad_y[i, j, k]**2 + grad_z[i, j, k]**2)
                            stability = self._compute_node_stability_3d(strain_energy, i, j, k)
                            
                            strain_nodes.append({
                                'position': [i, j, k],
                                'energy_density': float(energy),
                                'gradient_magnitude': float(grad_mag),
                                'stability': float(stability)
                            })
        
        return strain_nodes
    
    def _compute_node_stability_3d(self, energy_field: np.ndarray, ci: int, cj: int, ck: int) -> float:
        """Compute stability of energy concentration."""
        center_energy = energy_field[ci, cj, ck]
        
        window = 3
        i1, i2 = max(0, ci-window), min(self.size, ci+window+1)
        j1, j2 = max(0, cj-window), min(self.size, cj+window+1)
        k1, k2 = max(0, ck-window), min(self.size, ck+window+1)
        
        local_region = energy_field[i1:i2, j1:j2, k1:k2]
        mean_local = np.mean(local_region)
        std_local = np.std(local_region)
        
        if std_local > 0:
            stability = (center_energy - mean_local) / std_local
            return float(min(1.0, max(0.0, stability / 3.0)))
        return 0.0
    
    def detect_coherence_clusters(self, coherence_threshold: float = 0.02) -> List[Dict]:
        """Detect phase coherence clustering in 3D."""
        clusters = []
        
        rho = self.phi**2 + self.phi_dot**2
        coherence = gaussian_filter(rho, sigma=2.0)
        
        for i in range(3, self.size - 3):
            for j in range(3, self.size - 3):
                for k in range(3, self.size - 3):
                    if coherence[i, j, k] > coherence_threshold:
                        window = 3
                        local_region = coherence[i-window:i+window+1, j-window:j+window+1, k-window:k+window+1]
                        
                        if coherence[i, j, k] >= np.max(local_region):
                            cluster = self._characterize_cluster_3d(coherence, i, j, k, window, coherence_threshold)
                            if cluster:
                                clusters.append(cluster)
        
        return clusters
    
    def _characterize_cluster_3d(self, coherence: np.ndarray, ci: int, cj: int, ck: int,
                                  window: int, threshold: float) -> Optional[Dict]:
        """Characterize a coherence cluster in 3D."""
        i1, i2 = max(0, ci-window), min(self.size, ci+window+1)
        j1, j2 = max(0, cj-window), min(self.size, cj+window+1)
        k1, k2 = max(0, ck-window), min(self.size, ck+window+1)
        
        local_region = coherence[i1:i2, j1:j2, k1:k2]
        threshold_mask = local_region > threshold * 0.5
        member_count = int(np.sum(threshold_mask))
        
        if member_count < 5:  # Minimum cluster size for 3D
            return None
        
        coords = np.array(np.where(threshold_mask))
        weights = local_region[threshold_mask]
        
        if len(weights) == 0:
            return None
        
        center_local = np.average(coords, axis=1, weights=weights)
        center_global = [
            float(center_local[0] + i1), 
            float(center_local[1] + j1),
            float(center_local[2] + k1)
        ]
        
        size = float(np.sqrt(np.mean((coords - center_local[:, None])**2)))
        coherence_strength = float(np.mean(local_region[threshold_mask]))
        phase_value = float(np.mean(self.phi[i1:i2, j1:j2, k1:k2][threshold_mask]))
        
        return {
            'center': center_global,
            'size': size,
            'coherence_strength': coherence_strength,
            'member_count': member_count,
            'phase_value': phase_value
        }
    
    def identify_particle_nodes(self, strain_nodes: List[Dict], vortices: List[Dict],
                                clusters: List[Dict]) -> List[Dict]:
        """Identify emergent particle-like structures from co-located features in 3D."""
        particle_nodes = []
        rho = self.phi**2 + self.phi_dot**2
        
        for idx, strain in enumerate(strain_nodes):
            pos = strain['position']
            i, j, k = pos[0], pos[1], pos[2]
            
            # Find nearby vortex
            has_vortex = False
            for vortex in vortices:
                vpos = vortex['position']
                dist = math.sqrt((i - vpos[0])**2 + (j - vpos[1])**2 + (k - vpos[2])**2)
                if dist < 3:
                    has_vortex = True
                    break
            
            # Find nearby cluster
            has_cluster = False
            for cluster in clusters:
                cpos = cluster['center']
                dist = math.sqrt((i - cpos[0])**2 + (j - cpos[1])**2 + (k - cpos[2])**2)
                if dist < 3:
                    has_cluster = True
                    break
            
            if has_vortex or has_cluster:
                density_conc = float(rho[i, j, k] - np.mean(rho))
                effective_mass = density_conc * strain['energy_density']
                
                stability = strain['stability']
                if has_vortex:
                    stability += 0.2
                if has_cluster:
                    stability += 0.3
                stability = min(1.0, stability)
                
                if stability > 0.7:
                    structure_type = 'stable'
                elif stability > 0.4:
                    structure_type = 'proto-particle'
                else:
                    structure_type = 'transient'
                
                particle_nodes.append({
                    'id': f"node_3d_{idx}",
                    'position': [float(i), float(j), float(k)],
                    'density_concentration': density_conc,
                    'strain_energy': strain['energy_density'],
                    'effective_mass': effective_mass,
                    'stability_score': stability,
                    'structure_type': structure_type,
                    'has_vortex': has_vortex,
                    'has_cluster': has_cluster
                })
        
        return particle_nodes
    
    def detect_all_structures(self) -> Dict:
        """Detect all mesoscopic structures and return unified data."""
        vortices = self.detect_torsion_vortices()
        strain_nodes = self.detect_strain_energy_nodes()
        clusters = self.detect_coherence_clusters()
        particle_nodes = self.identify_particle_nodes(strain_nodes, vortices, clusters)
        
        return {
            'torsion_vortices': vortices,
            'strain_nodes': strain_nodes,
            'coherence_clusters': clusters,
            'particle_nodes': particle_nodes
        }


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post("/run", response_model=SimulationResult)
async def run_simulation(config: SimulationConfig):
    """Run a QMRT simulation with full metrics, mesoscopic structures, and time tracking."""
    
    start_time = time.time()
    
    # Create simulator
    if config.dimension == "2d":
        sim = QMRTSimulator2D(
            size=config.size,
            beta=config.alpha,
            lambda_relax=config.lambda_relax,
            gamma_wave=config.gamma_wave,
        )
        sim.add_pulse()
    else:
        # 3D uses smaller grid for performance
        size_3d = min(config.size, 50)
        sim = QMRTSimulator3D(
            size=size_3d,
            beta=config.alpha,
            lambda_relax=config.lambda_relax,
            gamma_wave=config.gamma_wave,
        )
        sim.add_pulse()
    
    # Initialize structure tracker
    tracker = StructureTracker(
        dimension=config.dimension,
        match_threshold=5.0  # Grid units for structure matching
    )
    
    # Run simulation
    measurements = []
    field_snapshots = []
    
    for step in range(config.steps):
        sim.step()
        
        if step % config.sample_interval == 0:
            t = step * sim.dt
            m = sim.measure(t)
            
            # Detect structures at this timestep
            structures = sim.detect_all_structures()
            
            # Feed structures to tracker for time tracking
            tracker.process_frame(structures, t)
            
            # Add structure counts to measurement
            m['vortex_count'] = len(structures['torsion_vortices'])
            m['cluster_count'] = len(structures['coherence_clusters'])
            m['strain_node_count'] = len(structures['strain_nodes'])
            m['particle_node_count'] = len(structures['particle_nodes'])
            
            # Add density stats
            rho = sim.phi**2 + sim.phi_dot**2
            m['mean_density'] = float(np.mean(rho))
            m['density_variance'] = float(np.var(rho))
            
            measurements.append(TimePoint(**{k: v for k, v in m.items() 
                                            if k not in ['rho_RS', 'rho_PS', 'rho_OS']}))
            
            # Store field snapshot every 5 samples
            if len(measurements) % 5 == 0:
                snapshot = sim.get_field_snapshot()
                snapshot['t'] = t
                field_snapshots.append(snapshot)
    
    duration = time.time() - start_time
    
    # Analyze results
    n = len(measurements)
    late_start = int(0.6 * n)
    
    E_late = [m.E_total for m in measurements[late_start:]]
    E_cv = np.std(E_late) / (np.mean(E_late) + 1e-10)
    balance_achieved = E_cv < 0.05
    
    S_mean = np.mean([m.S_total for m in measurements[late_start:]])
    O_mean = np.mean([m.O_total for m in measurements[late_start:]])
    R_mean = np.mean([m.R_rate for m in measurements[late_start:]])
    P_mean = np.mean([m.P_persistence for m in measurements[late_start:]])
    I_TS_mean = np.mean([m.I_TS for m in measurements[late_start:]])
    
    iso_mean = np.mean([m.isotropy_cv for m in measurements[late_start:]])
    conf_mean = np.mean([m.confinement for m in measurements[late_start:]])
    
    # Get final correlations
    final_m = sim.measure(config.steps * sim.dt)
    
    # === FINAL MESOSCOPIC STRUCTURES SNAPSHOT ===
    final_structures = sim.detect_all_structures()
    final_time = config.steps * sim.dt
    
    # Build structures snapshot
    structures_snapshot = StructuresSnapshot(
        t=float(final_time),
        torsion_vortices=[TorsionVortexData(**v) for v in final_structures['torsion_vortices']],
        strain_nodes=[StrainNodeData(**s) for s in final_structures['strain_nodes']],
        coherence_clusters=[CoherenceClusterData(**c) for c in final_structures['coherence_clusters']],
        particle_nodes=[ParticleNodeData(**p) for p in final_structures['particle_nodes']]
    )
    
    # Count particle node types
    stable_count = sum(1 for p in final_structures['particle_nodes'] if p['structure_type'] == 'stable')
    proto_count = sum(1 for p in final_structures['particle_nodes'] if p['structure_type'] == 'proto-particle')
    transient_count = sum(1 for p in final_structures['particle_nodes'] if p['structure_type'] == 'transient')
    
    # === FINALIZE STRUCTURE TRACKING ===
    tracked_structures = tracker.finalize(final_time)
    structures_timeline = tracker.get_timeline()
    
    return SimulationResult(
        dimension=config.dimension,
        config=config.model_dump(),
        duration_seconds=duration,
        measurements=measurements,
        
        balance_achieved=balance_achieved,
        balance_E_cv=float(E_cv),
        
        spatial_S_mean=float(S_mean),
        ordering_O_mean=float(O_mean),
        rate_R_mean=float(R_mean),
        persistence_P_mean=float(P_mean),
        coupling_I_TS_mean=float(I_TS_mean),
        
        geometry_isotropic=iso_mean < 0.2,
        geometry_confined=conf_mean > 80,
        
        rho_RS=final_m['rho_RS'],
        rho_PS=final_m['rho_PS'],
        rho_OS=final_m['rho_OS'],
        
        # Mesoscopic structures (final snapshot)
        structures=structures_snapshot,
        total_vortices=len(final_structures['torsion_vortices']),
        total_clusters=len(final_structures['coherence_clusters']),
        total_strain_nodes=len(final_structures['strain_nodes']),
        total_particle_nodes=len(final_structures['particle_nodes']),
        stable_nodes=stable_count,
        proto_nodes=proto_count,
        transient_nodes=transient_count,
        
        field_snapshots=field_snapshots,
        
        # Structure time tracking
        structures_timeline=structures_timeline,
        tracked_structures=tracked_structures,
        tracking_births=tracked_structures.total_births,
        tracking_deaths=tracked_structures.total_deaths,
        tracking_merges=tracked_structures.total_merges,
        tracking_splits=tracked_structures.total_splits,
        tracking_avg_lifetime=tracked_structures.avg_lifetime,
    )


@router.get("/info")
async def get_simulation_info():
    """Get information about the QMRT simulation."""
    return {
        "theory": "Quark Medium Relativity Theory (QMRT)",
        "description": "Dynamical medium simulation for emergent spacetime",
        "components": {
            "S": "Spatial geometry structure (metric variation)",
            "O": "Ordering structure (causal path diversity)",
            "R": "Rate (temporal dynamics)",
            "P": "Persistence (configuration stability)",
            "I_TS": "Spacetime coupling integral",
        },
        "validated_results": {
            "scaling": "O ~ S² (universal exponent α = 2)",
            "balance": "Driven-dissipative equilibrium",
            "3d_isotropy": "Spherical light cones confirmed",
        },
        "parameters": {
            "alpha": "Backreaction coupling (β)",
            "lambda": "Relaxation rate (λ)",
            "gamma": "Wave damping (γ)",
        }
    }


# ============================================================
# VALIDATION TESTING INFRASTRUCTURE
# ============================================================

class ValidationTestRequest(BaseModel):
    """Request for running validation tests."""
    test_type: Literal["birth_vs_rho", "longlived_vs_S", "merge_vs_gradient"]
    n_runs: int = Field(default=20, ge=5, le=100)
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=40, ge=20, le=60)
    alpha: float = Field(default=0.5, ge=0.1, le=1.0)
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0)
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1)
    steps: int = Field(default=200, ge=100, le=500)
    seeds: Optional[List[int]] = None  # If None, generate random seeds

class BirthLocationSample(BaseModel):
    """Sample data for a single birth event."""
    structure_id: str
    structure_type: str
    birth_time: float
    position: List[float]
    local_rho: float
    local_gradient: float
    rho_percentile: float  # What percentile of global rho distribution
    gradient_percentile: float

class ValidationTestResult(BaseModel):
    """Result of a validation test."""
    test_type: str
    n_runs: int
    config: Dict
    
    # Aggregated statistics
    mean_rho_percentile: float
    std_rho_percentile: float
    mean_gradient_percentile: float
    std_gradient_percentile: float
    
    # Enrichment ratios (vs 50th percentile baseline)
    rho_enrichment: float
    gradient_enrichment: float
    
    # Statistical significance
    rho_p_value: float
    gradient_p_value: float
    
    # Confidence intervals (95%)
    rho_ci_low: float
    rho_ci_high: float
    gradient_ci_low: float
    gradient_ci_high: float
    
    # Per-run data for detailed analysis
    per_run_stats: List[Dict]
    
    # Baseline comparison
    baseline_rho_mean: float
    baseline_gradient_mean: float
    
    # Interpretation
    interpretation: str


def compute_local_field_values(rho: np.ndarray, position: List[float]) -> Tuple[float, float]:
    """Compute local ρ and |∇ρ| at a position."""
    pos = [int(round(p)) for p in position]
    
    # Clamp to valid range
    shape = rho.shape
    pos = [max(0, min(p, s - 1)) for p, s in zip(pos, shape)]
    
    # Local ρ value
    if len(pos) == 2:
        local_rho = float(rho[pos[0], pos[1]])
    else:
        local_rho = float(rho[pos[0], pos[1], pos[2]])
    
    # Compute gradient magnitude using central differences
    grad_x = np.gradient(rho, axis=0)
    grad_y = np.gradient(rho, axis=1)
    
    if len(pos) == 2:
        gradient_mag = float(np.sqrt(grad_x[pos[0], pos[1]]**2 + grad_y[pos[0], pos[1]]**2))
    else:
        grad_z = np.gradient(rho, axis=2)
        gradient_mag = float(np.sqrt(
            grad_x[pos[0], pos[1], pos[2]]**2 + 
            grad_y[pos[0], pos[1], pos[2]]**2 + 
            grad_z[pos[0], pos[1], pos[2]]**2
        ))
    
    return local_rho, gradient_mag


def compute_percentile(value: float, distribution: np.ndarray) -> float:
    """Compute what percentile a value falls in within a distribution."""
    flat = distribution.flatten()
    return float(np.sum(flat <= value) / len(flat) * 100)


def run_single_simulation_for_test(
    dimension: str,
    size: int,
    alpha: float,
    lambda_relax: float,
    gamma_wave: float,
    steps: int,
    seed: int
) -> Dict:
    """Run a single simulation and extract birth location data."""
    
    # Set random seed for reproducibility
    np.random.seed(seed)
    
    # Create simulator based on dimension
    if dimension == '2d':
        sim = QMRTSimulator2D(
            size=size,
            beta=alpha,
            lambda_relax=lambda_relax,
            gamma_wave=gamma_wave
        )
        # Add initial pulse
        sim.add_pulse(amplitude=3.0, width=4.0)
    else:
        sim = QMRTSimulator3D(
            size=size,
            beta=alpha,
            lambda_relax=lambda_relax,
            gamma_wave=gamma_wave
        )
        sim.add_pulse(amplitude=3.0, width=4.0)
    
    # Structure tracker
    tracker = StructureTracker()
    
    # Storage for birth events
    birth_events = []
    
    # Run simulation
    sample_interval = 10
    
    for step in range(steps):
        sim.step()
        t = step * sim.dt
        
        # Detect structures at sample intervals
        if step % sample_interval == 0:
            structures = sim.detect_all_structures()
            
            # Get current field state for percentile calculations
            rho = sim.phi**2 + sim.phi_dot**2
            grad_rho_mag = sim.compute_gradient_magnitude(rho)
            
            # Track structures and capture birth events
            tracker.process_frame(structures, t)
            
            # Check for new births this frame
            for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
                for sid, tracked in tracker.active_structures[struct_type].items():
                    # tracked is a dict with TrackedStructure fields
                    # Check if this structure was just born (birth_time == current time)
                    birth_time = tracked.get('birth_time', 0)
                    if abs(birth_time - t) < 0.01:
                        trajectory = tracked.get('trajectory', [])
                        pos = trajectory[0][:len(trajectory[0])-1] if trajectory else [size//2] * (2 if dimension == '2d' else 3)
                        local_rho, local_grad = compute_local_field_values(rho, pos)
                        rho_pct = compute_percentile(local_rho, rho)
                        grad_pct = compute_percentile(local_grad, grad_rho_mag)
                        
                        birth_events.append({
                            'structure_id': sid,
                            'structure_type': struct_type,
                            'birth_time': t,
                            'position': [float(p) for p in pos],
                            'local_rho': local_rho,
                            'local_gradient': local_grad,
                            'rho_percentile': rho_pct,
                            'gradient_percentile': grad_pct
                        })
    
    # Final field state for baseline sampling
    rho = sim.phi**2 + sim.phi_dot**2
    grad_rho_mag = sim.compute_gradient_magnitude(rho)
    
    # Generate random baseline samples (same count as births, random positions)
    n_baseline = max(len(birth_events), 20)
    baseline_samples = []
    for _ in range(n_baseline):
        if dimension == '2d':
            pos = [float(np.random.randint(0, size)), float(np.random.randint(0, size))]
        else:
            pos = [float(np.random.randint(0, size)) for _ in range(3)]
        local_rho, local_grad = compute_local_field_values(rho, pos)
        rho_pct = compute_percentile(local_rho, rho)
        grad_pct = compute_percentile(local_grad, grad_rho_mag)
        baseline_samples.append({
            'rho_percentile': rho_pct,
            'gradient_percentile': grad_pct
        })
    
    return {
        'seed': seed,
        'n_births': len(birth_events),
        'birth_events': birth_events,
        'baseline_samples': baseline_samples,
        'mean_rho_percentile': float(np.mean([e['rho_percentile'] for e in birth_events])) if birth_events else 50.0,
        'mean_gradient_percentile': float(np.mean([e['gradient_percentile'] for e in birth_events])) if birth_events else 50.0,
        'baseline_rho_mean': float(np.mean([s['rho_percentile'] for s in baseline_samples])),
        'baseline_gradient_mean': float(np.mean([s['gradient_percentile'] for s in baseline_samples]))
    }


@router.post("/validate/birth-vs-rho", response_model=ValidationTestResult)
async def run_birth_vs_rho_test(request: ValidationTestRequest):
    """
    Test 1: Birth location vs ρ peaks
    
    Hypothesis: Structures are more likely to be born in high-ρ or high-∇ρ regions.
    
    Measures enrichment ratio and statistical significance against random baseline.
    """
    from scipy import stats
    
    # Generate seeds if not provided
    if request.seeds:
        seeds = request.seeds[:request.n_runs]
    else:
        seeds = [np.random.randint(0, 100000) for _ in range(request.n_runs)]
    
    # Run simulations
    per_run_stats = []
    all_rho_percentiles = []
    all_gradient_percentiles = []
    all_baseline_rho = []
    all_baseline_gradient = []
    
    for i, seed in enumerate(seeds):
        result = run_single_simulation_for_test(
            dimension=request.dimension,
            size=request.size,
            alpha=request.alpha,
            lambda_relax=request.lambda_relax,
            gamma_wave=request.gamma_wave,
            steps=request.steps,
            seed=seed
        )
        
        per_run_stats.append({
            'run': i + 1,
            'seed': seed,
            'n_births': result['n_births'],
            'mean_rho_percentile': result['mean_rho_percentile'],
            'mean_gradient_percentile': result['mean_gradient_percentile'],
            'baseline_rho_mean': result['baseline_rho_mean'],
            'baseline_gradient_mean': result['baseline_gradient_mean']
        })
        
        # Collect all birth percentiles
        for event in result['birth_events']:
            all_rho_percentiles.append(event['rho_percentile'])
            all_gradient_percentiles.append(event['gradient_percentile'])
        
        # Collect baseline
        for sample in result['baseline_samples']:
            all_baseline_rho.append(sample['rho_percentile'])
            all_baseline_gradient.append(sample['gradient_percentile'])
    
    # Compute aggregated statistics
    if all_rho_percentiles:
        mean_rho_pct = float(np.mean(all_rho_percentiles))
        std_rho_pct = float(np.std(all_rho_percentiles))
        mean_grad_pct = float(np.mean(all_gradient_percentiles))
        std_grad_pct = float(np.std(all_gradient_percentiles))
        
        # Enrichment vs 50th percentile (neutral expectation)
        rho_enrichment = mean_rho_pct / 50.0
        gradient_enrichment = mean_grad_pct / 50.0
        
        # Statistical test: are births significantly above random?
        # One-sample t-test against mean of 50 (random expectation)
        rho_t, rho_p = stats.ttest_1samp(all_rho_percentiles, 50)
        grad_t, grad_p = stats.ttest_1samp(all_gradient_percentiles, 50)
        
        # Also compare to actual baseline distribution
        baseline_rho_mean = float(np.mean(all_baseline_rho))
        baseline_grad_mean = float(np.mean(all_baseline_gradient))
        
        # 95% confidence intervals (bootstrap-like using std error)
        n = len(all_rho_percentiles)
        se_rho = std_rho_pct / np.sqrt(n)
        se_grad = std_grad_pct / np.sqrt(n)
        rho_ci_low = mean_rho_pct - 1.96 * se_rho
        rho_ci_high = mean_rho_pct + 1.96 * se_rho
        grad_ci_low = mean_grad_pct - 1.96 * se_grad
        grad_ci_high = mean_grad_pct + 1.96 * se_grad
        
        # Interpretation
        interpretations = []
        if rho_p < 0.05 and mean_rho_pct > 50:
            interpretations.append(f"Births SIGNIFICANTLY cluster in HIGH-ρ regions (mean={mean_rho_pct:.1f}%, p={rho_p:.4f})")
        elif rho_p < 0.05 and mean_rho_pct < 50:
            interpretations.append(f"Births SIGNIFICANTLY cluster in LOW-ρ regions (mean={mean_rho_pct:.1f}%, p={rho_p:.4f})")
        else:
            interpretations.append(f"No significant ρ preference (mean={mean_rho_pct:.1f}%, p={rho_p:.4f})")
        
        if grad_p < 0.05 and mean_grad_pct > 50:
            interpretations.append(f"Births SIGNIFICANTLY cluster in HIGH-GRADIENT regions (mean={mean_grad_pct:.1f}%, p={grad_p:.4f})")
        elif grad_p < 0.05 and mean_grad_pct < 50:
            interpretations.append(f"Births SIGNIFICANTLY cluster in LOW-GRADIENT regions (mean={mean_grad_pct:.1f}%, p={grad_p:.4f})")
        else:
            interpretations.append(f"No significant gradient preference (mean={mean_grad_pct:.1f}%, p={grad_p:.4f})")
        
        interpretation = " | ".join(interpretations)
    else:
        # No births detected
        mean_rho_pct = 50.0
        std_rho_pct = 0.0
        mean_grad_pct = 50.0
        std_grad_pct = 0.0
        rho_enrichment = 1.0
        gradient_enrichment = 1.0
        rho_p = 1.0
        grad_p = 1.0
        rho_ci_low = 50.0
        rho_ci_high = 50.0
        grad_ci_low = 50.0
        grad_ci_high = 50.0
        baseline_rho_mean = 50.0
        baseline_grad_mean = 50.0
        interpretation = "No births detected across runs"
    
    return ValidationTestResult(
        test_type="birth_vs_rho",
        n_runs=request.n_runs,
        config={
            "dimension": request.dimension,
            "size": request.size,
            "alpha": request.alpha,
            "lambda_relax": request.lambda_relax,
            "gamma_wave": request.gamma_wave,
            "steps": request.steps
        },
        mean_rho_percentile=mean_rho_pct,
        std_rho_percentile=std_rho_pct,
        mean_gradient_percentile=mean_grad_pct,
        std_gradient_percentile=std_grad_pct,
        rho_enrichment=rho_enrichment,
        gradient_enrichment=gradient_enrichment,
        rho_p_value=float(rho_p),
        gradient_p_value=float(grad_p),
        rho_ci_low=rho_ci_low,
        rho_ci_high=rho_ci_high,
        gradient_ci_low=grad_ci_low,
        gradient_ci_high=grad_ci_high,
        per_run_stats=per_run_stats,
        baseline_rho_mean=baseline_rho_mean,
        baseline_gradient_mean=baseline_grad_mean,
        interpretation=interpretation
    )
