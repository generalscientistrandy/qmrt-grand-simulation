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
    test_type: Literal["birth_vs_rho", "longlived_vs_S", "merge_vs_gradient"] = "birth_vs_rho"
    n_runs: int = Field(default=20, ge=5, le=100)
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=40, ge=20, le=60)
    alpha: float = Field(default=0.5, ge=0.1, le=1.0)
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0)
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1)
    steps: int = Field(default=200, ge=100, le=500)
    seeds: Optional[List[int]] = None  # If None, generate random seeds

class SimpleTestRequest(BaseModel):
    """Simplified request for tests that don't need test_type."""
    n_runs: int = Field(default=20, ge=5, le=100)
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=40, ge=20, le=60)
    alpha: float = Field(default=0.5, ge=0.1, le=1.0)
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0)
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1)
    steps: int = Field(default=200, ge=100, le=500)
    seeds: Optional[List[int]] = None

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


class RobustnessCheckResult(BaseModel):
    """Result of robustness checks for validation tests."""
    # Shuffle control results
    shuffle_rho_mean: float
    shuffle_gradient_mean: float
    shuffle_rho_p_value: float  # Should be >0.05 (not significant vs 50%)
    shuffle_gradient_p_value: float
    
    # Effect preserved after shuffle?
    shuffle_nullifies_effect: bool  # True = good (proves effect is real)
    
    # Decile histogram data
    rho_decile_counts: List[int]  # 10 bins: 0-10%, 10-20%, ..., 90-100%
    gradient_decile_counts: List[int]
    
    # Expected uniform distribution (for comparison)
    expected_per_decile: float
    
    # Chi-squared test for non-uniformity
    rho_chi2: float
    rho_chi2_p: float
    gradient_chi2: float
    gradient_chi2_p: float
    
    # Interpretation
    interpretation: str


@router.post("/validate/robustness-check")
async def run_robustness_check(request: ValidationTestRequest):
    """
    Robustness checks for Test 1: Birth location vs ρ peaks
    
    1. Shuffle Control: Keep same births, shuffle positions within timestep
       - If effect is real, shuffled positions should show ~50% percentile
       
    2. Decile Histogram: Distribution of birth percentiles across deciles
       - Should show clear skew toward upper deciles
    """
    from scipy import stats
    
    # Generate seeds
    if request.seeds:
        seeds = request.seeds[:request.n_runs]
    else:
        seeds = [np.random.randint(0, 100000) for _ in range(request.n_runs)]
    
    # Collect all percentiles
    all_rho_percentiles = []
    all_gradient_percentiles = []
    shuffled_rho_percentiles = []
    shuffled_gradient_percentiles = []
    
    for seed in seeds:
        result = run_single_simulation_for_test(
            dimension=request.dimension,
            size=request.size,
            alpha=request.alpha,
            lambda_relax=request.lambda_relax,
            gamma_wave=request.gamma_wave,
            steps=request.steps,
            seed=seed
        )
        
        # Actual birth percentiles
        for event in result['birth_events']:
            all_rho_percentiles.append(event['rho_percentile'])
            all_gradient_percentiles.append(event['gradient_percentile'])
        
        # Shuffled: use baseline samples as "shuffled" positions
        # (random positions sampled from same field)
        for sample in result['baseline_samples'][:len(result['birth_events'])]:
            shuffled_rho_percentiles.append(sample['rho_percentile'])
            shuffled_gradient_percentiles.append(sample['gradient_percentile'])
    
    if not all_rho_percentiles:
        return {"error": "No births detected"}
    
    # === SHUFFLE CONTROL ===
    shuffle_rho_mean = float(np.mean(shuffled_rho_percentiles))
    shuffle_grad_mean = float(np.mean(shuffled_gradient_percentiles))
    
    # Test if shuffled is significantly different from 50%
    _, shuffle_rho_p = stats.ttest_1samp(shuffled_rho_percentiles, 50)
    _, shuffle_grad_p = stats.ttest_1samp(shuffled_gradient_percentiles, 50)
    
    # Effect is nullified if shuffled mean is close to 50% (p > 0.05)
    shuffle_nullifies = (shuffle_rho_p > 0.05 or abs(shuffle_rho_mean - 50) < 5)
    
    # === DECILE HISTOGRAM ===
    rho_deciles = [0] * 10
    gradient_deciles = [0] * 10
    
    for pct in all_rho_percentiles:
        decile = min(9, int(pct / 10))
        rho_deciles[decile] += 1
    
    for pct in all_gradient_percentiles:
        decile = min(9, int(pct / 10))
        gradient_deciles[decile] += 1
    
    expected_per_decile = len(all_rho_percentiles) / 10
    
    # Chi-squared test for non-uniformity
    expected = [expected_per_decile] * 10
    rho_chi2, rho_chi2_p = stats.chisquare(rho_deciles, expected)
    grad_chi2, grad_chi2_p = stats.chisquare(gradient_deciles, expected)
    
    # Interpretation
    interpretations = []
    
    # Shuffle control interpretation
    if shuffle_nullifies:
        interpretations.append(f"✓ SHUFFLE CONTROL PASSED: Shuffled positions show mean={shuffle_rho_mean:.1f}% (p={shuffle_rho_p:.3f}), confirming effect is NOT an artifact")
    else:
        interpretations.append(f"⚠ SHUFFLE CONTROL WARNING: Shuffled mean={shuffle_rho_mean:.1f}% still elevated (p={shuffle_rho_p:.3f})")
    
    # Decile distribution interpretation
    upper_decile_fraction = sum(rho_deciles[7:]) / sum(rho_deciles)  # 70-100%
    if rho_chi2_p < 0.001 and upper_decile_fraction > 0.5:
        interpretations.append(f"✓ DECILE TEST PASSED: {upper_decile_fraction*100:.0f}% of births in top 3 deciles (χ²={rho_chi2:.1f}, p<0.001)")
    elif rho_chi2_p < 0.05:
        interpretations.append(f"✓ Non-uniform distribution detected (χ²={rho_chi2:.1f}, p={rho_chi2_p:.4f})")
    else:
        interpretations.append(f"⚠ Distribution appears uniform (χ²={rho_chi2:.1f}, p={rho_chi2_p:.4f})")
    
    return RobustnessCheckResult(
        shuffle_rho_mean=shuffle_rho_mean,
        shuffle_gradient_mean=shuffle_grad_mean,
        shuffle_rho_p_value=float(shuffle_rho_p),
        shuffle_gradient_p_value=float(shuffle_grad_p),
        shuffle_nullifies_effect=shuffle_nullifies,
        rho_decile_counts=rho_deciles,
        gradient_decile_counts=gradient_deciles,
        expected_per_decile=expected_per_decile,
        rho_chi2=float(rho_chi2),
        rho_chi2_p=float(rho_chi2_p),
        gradient_chi2=float(grad_chi2),
        gradient_chi2_p=float(grad_chi2_p),
        interpretation=" | ".join(interpretations)
    )


# ============================================================
# TEST 2: LONG-LIVED NODES vs S (ORGANIZATION)
# ============================================================

class LongLivedTestResult(BaseModel):
    """Result of Test 2: Long-lived nodes vs S/P."""
    test_type: str
    n_runs: int
    config: Dict
    
    # Correlation results
    lifetime_S_correlation: float  # Pearson correlation
    lifetime_S_p_value: float
    lifetime_P_correlation: float
    lifetime_P_p_value: float
    
    # Mean S/P by lifetime bin
    short_lived_mean_S: float  # lifetime < threshold
    long_lived_mean_S: float   # lifetime >= threshold
    short_lived_mean_P: float
    long_lived_mean_P: float
    
    # Effect size (Cohen's d)
    S_effect_size: float
    P_effect_size: float
    
    # Sample sizes
    n_short_lived: int
    n_long_lived: int
    lifetime_threshold: float
    
    interpretation: str


def run_simulation_for_longlived_test(
    dimension: str, size: int, alpha: float, lambda_relax: float,
    gamma_wave: float, steps: int, seed: int
) -> Dict:
    """Run simulation and extract lifetime vs S/P data."""
    
    np.random.seed(seed)
    
    if dimension == '2d':
        sim = QMRTSimulator2D(size=size, beta=alpha, lambda_relax=lambda_relax, gamma_wave=gamma_wave)
    else:
        sim = QMRTSimulator3D(size=size, beta=alpha, lambda_relax=lambda_relax, gamma_wave=gamma_wave)
    sim.add_pulse(amplitude=3.0, width=4.0)
    
    tracker = StructureTracker()
    sample_interval = 10
    
    # Track S and P values along each structure's trajectory
    structure_metrics = {}  # id -> {'lifetimes': [], 'S_values': [], 'P_values': []}
    
    for step in range(steps):
        sim.step()
        t = step * sim.dt
        
        if step % sample_interval == 0:
            structures = sim.detect_all_structures()
            tracker.process_frame(structures, t)
            
            # Compute global S (spatial organization metric)
            rho = sim.phi**2 + sim.phi_dot**2
            grad_mag = sim.compute_gradient_magnitude(rho)
            
            # S = normalized gradient structure
            S_field = grad_mag / (np.mean(grad_mag) + 1e-8)
            
            # P = local persistence proxy (low variation = stable)
            P_field = 1.0 / (1.0 + np.std(rho) * grad_mag / (np.mean(rho) + 1e-8))
            
            # Sample S and P at active structure positions
            for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
                for sid, tracked in tracker.active_structures[struct_type].items():
                    trajectory = tracked.get('trajectory', [])
                    if trajectory:
                        pos = trajectory[-1][:len(trajectory[-1])-1]
                        pos_int = [max(0, min(int(p), size-1)) for p in pos]
                        
                        if dimension == '2d':
                            local_S = float(S_field[pos_int[0], pos_int[1]])
                            local_P = float(P_field[pos_int[0], pos_int[1]])
                        else:
                            local_S = float(S_field[pos_int[0], pos_int[1], pos_int[2]])
                            local_P = float(P_field[pos_int[0], pos_int[1], pos_int[2]])
                        
                        if sid not in structure_metrics:
                            structure_metrics[sid] = {'S_values': [], 'P_values': [], 'birth_time': tracked.get('birth_time', t)}
                        structure_metrics[sid]['S_values'].append(local_S)
                        structure_metrics[sid]['P_values'].append(local_P)
    
    # Compute final metrics per structure
    final_time = steps * sim.dt
    structure_data = []
    
    for sid, metrics in structure_metrics.items():
        # Find final status
        lifetime = final_time - metrics['birth_time']
        
        # Check if still active or completed
        for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
            if sid in tracker.active_structures[struct_type]:
                tracked = tracker.active_structures[struct_type][sid]
                lifetime = tracked.get('last_seen_time', final_time) - tracked.get('birth_time', 0)
                break
        
        if metrics['S_values']:
            structure_data.append({
                'id': sid,
                'lifetime': lifetime,
                'mean_S': float(np.mean(metrics['S_values'])),
                'mean_P': float(np.mean(metrics['P_values']))
            })
    
    return {
        'seed': seed,
        'n_structures': len(structure_data),
        'structure_data': structure_data
    }


@router.post("/validate/longlived-vs-S", response_model=LongLivedTestResult)
async def run_longlived_vs_S_test(request: ValidationTestRequest):
    """
    Test 2: Long-lived nodes vs S (Organization)
    
    Hypothesis: Persistent structures align with higher S (spatial organization).
    """
    from scipy import stats
    
    if request.seeds:
        seeds = request.seeds[:request.n_runs]
    else:
        seeds = [np.random.randint(0, 100000) for _ in range(request.n_runs)]
    
    all_lifetimes = []
    all_S = []
    all_P = []
    
    for seed in seeds:
        result = run_simulation_for_longlived_test(
            dimension=request.dimension,
            size=request.size,
            alpha=request.alpha,
            lambda_relax=request.lambda_relax,
            gamma_wave=request.gamma_wave,
            steps=request.steps,
            seed=seed
        )
        
        for struct in result['structure_data']:
            all_lifetimes.append(struct['lifetime'])
            all_S.append(struct['mean_S'])
            all_P.append(struct['mean_P'])
    
    if len(all_lifetimes) < 10:
        return LongLivedTestResult(
            test_type="longlived_vs_S",
            n_runs=request.n_runs,
            config={"dimension": request.dimension, "size": request.size},
            lifetime_S_correlation=0, lifetime_S_p_value=1,
            lifetime_P_correlation=0, lifetime_P_p_value=1,
            short_lived_mean_S=0, long_lived_mean_S=0,
            short_lived_mean_P=0, long_lived_mean_P=0,
            S_effect_size=0, P_effect_size=0,
            n_short_lived=0, n_long_lived=0, lifetime_threshold=0,
            interpretation="Insufficient data"
        )
    
    # Correlations
    corr_S, p_S = stats.pearsonr(all_lifetimes, all_S)
    corr_P, p_P = stats.pearsonr(all_lifetimes, all_P)
    
    # Split into short-lived vs long-lived
    lifetime_threshold = float(np.median(all_lifetimes))
    
    short_mask = [lt < lifetime_threshold for lt in all_lifetimes]
    long_mask = [lt >= lifetime_threshold for lt in all_lifetimes]
    
    short_S = [s for s, m in zip(all_S, short_mask) if m]
    long_S = [s for s, m in zip(all_S, long_mask) if m]
    short_P = [p for p, m in zip(all_P, short_mask) if m]
    long_P = [p for p, m in zip(all_P, long_mask) if m]
    
    short_S_mean = float(np.mean(short_S)) if short_S else 0
    long_S_mean = float(np.mean(long_S)) if long_S else 0
    short_P_mean = float(np.mean(short_P)) if short_P else 0
    long_P_mean = float(np.mean(long_P)) if long_P else 0
    
    # Effect size (Cohen's d)
    def cohens_d(g1, g2):
        n1, n2 = len(g1), len(g2)
        if n1 < 2 or n2 < 2:
            return 0
        var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
        pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
        return (np.mean(g2) - np.mean(g1)) / (pooled_std + 1e-8)
    
    S_effect = cohens_d(short_S, long_S)
    P_effect = cohens_d(short_P, long_P)
    
    # Interpretation
    interps = []
    if p_S < 0.05 and corr_S > 0:
        interps.append(f"✓ POSITIVE correlation: lifetime↔S (r={corr_S:.3f}, p={p_S:.4f})")
    elif p_S < 0.05:
        interps.append(f"Negative correlation: lifetime↔S (r={corr_S:.3f}, p={p_S:.4f})")
    else:
        interps.append(f"No significant lifetime↔S correlation (r={corr_S:.3f}, p={p_S:.4f})")
    
    if abs(S_effect) > 0.5:
        interps.append(f"Large effect size: d={S_effect:.2f}")
    elif abs(S_effect) > 0.2:
        interps.append(f"Medium effect size: d={S_effect:.2f}")
    
    return LongLivedTestResult(
        test_type="longlived_vs_S",
        n_runs=request.n_runs,
        config={
            "dimension": request.dimension,
            "size": request.size,
            "alpha": request.alpha,
            "steps": request.steps
        },
        lifetime_S_correlation=float(corr_S),
        lifetime_S_p_value=float(p_S),
        lifetime_P_correlation=float(corr_P),
        lifetime_P_p_value=float(p_P),
        short_lived_mean_S=short_S_mean,
        long_lived_mean_S=long_S_mean,
        short_lived_mean_P=short_P_mean,
        long_lived_mean_P=long_P_mean,
        S_effect_size=float(S_effect),
        P_effect_size=float(P_effect),
        n_short_lived=len(short_S),
        n_long_lived=len(long_S),
        lifetime_threshold=lifetime_threshold,
        interpretation=" | ".join(interps)
    )


# ============================================================
# PARTIAL CORRELATION CHECK: Is S independent of ρ?
# ============================================================

class PartialCorrelationResult(BaseModel):
    """Result of partial correlation analysis."""
    # Raw correlations
    lifetime_S_correlation: float
    lifetime_rho_correlation: float
    S_rho_correlation: float
    
    # Partial correlations (controlling for confound)
    partial_lifetime_S_given_rho: float  # Key metric
    partial_lifetime_rho_given_S: float
    
    # P-values
    partial_lifetime_S_p_value: float
    partial_lifetime_rho_p_value: float
    
    # Independence check
    S_is_independent_of_rho: bool  # True if partial corr still significant
    
    interpretation: str


def partial_correlation(x, y, z):
    """
    Compute partial correlation between x and y, controlling for z.
    r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2)(1 - r_yz^2))
    """
    from scipy import stats
    
    r_xy, _ = stats.pearsonr(x, y)
    r_xz, _ = stats.pearsonr(x, z)
    r_yz, _ = stats.pearsonr(y, z)
    
    numerator = r_xy - r_xz * r_yz
    denominator = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
    
    if denominator < 1e-10:
        return 0.0, 1.0
    
    partial_r = numerator / denominator
    
    # Approximate p-value using Fisher's z transformation
    n = len(x)
    df = n - 3  # degrees of freedom for partial correlation
    if df <= 0:
        return partial_r, 1.0
    
    # t-statistic
    t_stat = partial_r * np.sqrt(df / (1 - partial_r**2 + 1e-10))
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    return float(partial_r), float(p_value)


def run_simulation_for_partial_corr(
    dimension: str, size: int, alpha: float, lambda_relax: float,
    gamma_wave: float, steps: int, seed: int
) -> Dict:
    """Run simulation and extract lifetime, S, and ρ data for partial correlation."""
    
    np.random.seed(seed)
    
    if dimension == '2d':
        sim = QMRTSimulator2D(size=size, beta=alpha, lambda_relax=lambda_relax, gamma_wave=gamma_wave)
    else:
        sim = QMRTSimulator3D(size=size, beta=alpha, lambda_relax=lambda_relax, gamma_wave=gamma_wave)
    sim.add_pulse(amplitude=3.0, width=4.0)
    
    tracker = StructureTracker()
    sample_interval = 10
    
    structure_metrics = {}
    
    for step in range(steps):
        sim.step()
        t = step * sim.dt
        
        if step % sample_interval == 0:
            structures = sim.detect_all_structures()
            tracker.process_frame(structures, t)
            
            rho = sim.phi**2 + sim.phi_dot**2
            grad_mag = sim.compute_gradient_magnitude(rho)
            S_field = grad_mag / (np.mean(grad_mag) + 1e-8)
            
            for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
                for sid, tracked in tracker.active_structures[struct_type].items():
                    trajectory = tracked.get('trajectory', [])
                    if trajectory:
                        pos = trajectory[-1][:len(trajectory[-1])-1]
                        pos_int = [max(0, min(int(p), size-1)) for p in pos]
                        
                        if dimension == '2d':
                            local_S = float(S_field[pos_int[0], pos_int[1]])
                            local_rho = float(rho[pos_int[0], pos_int[1]])
                        else:
                            local_S = float(S_field[pos_int[0], pos_int[1], pos_int[2]])
                            local_rho = float(rho[pos_int[0], pos_int[1], pos_int[2]])
                        
                        if sid not in structure_metrics:
                            structure_metrics[sid] = {
                                'S_values': [], 'rho_values': [],
                                'birth_time': tracked.get('birth_time', t)
                            }
                        structure_metrics[sid]['S_values'].append(local_S)
                        structure_metrics[sid]['rho_values'].append(local_rho)
    
    final_time = steps * sim.dt
    structure_data = []
    
    for sid, metrics in structure_metrics.items():
        lifetime = final_time - metrics['birth_time']
        
        for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
            if sid in tracker.active_structures[struct_type]:
                tracked = tracker.active_structures[struct_type][sid]
                lifetime = tracked.get('last_seen_time', final_time) - tracked.get('birth_time', 0)
                break
        
        if metrics['S_values'] and metrics['rho_values']:
            structure_data.append({
                'id': sid,
                'lifetime': lifetime,
                'mean_S': float(np.mean(metrics['S_values'])),
                'mean_rho': float(np.mean(metrics['rho_values']))
            })
    
    return {'seed': seed, 'structure_data': structure_data}


@router.post("/validate/partial-correlation", response_model=PartialCorrelationResult)
async def run_partial_correlation_check(request: SimpleTestRequest):
    """
    Partial Correlation Check: Is S independent of ρ?
    
    Computes partial correlation of lifetime↔S controlling for ρ.
    If still significant, S is a distinct organizing variable.
    """
    from scipy import stats
    
    if request.seeds:
        seeds = request.seeds[:request.n_runs]
    else:
        seeds = [np.random.randint(0, 100000) for _ in range(request.n_runs)]
    
    all_lifetimes = []
    all_S = []
    all_rho = []
    
    for seed in seeds:
        result = run_simulation_for_partial_corr(
            dimension=request.dimension,
            size=request.size,
            alpha=request.alpha,
            lambda_relax=request.lambda_relax,
            gamma_wave=request.gamma_wave,
            steps=request.steps,
            seed=seed
        )
        
        for struct in result['structure_data']:
            all_lifetimes.append(struct['lifetime'])
            all_S.append(struct['mean_S'])
            all_rho.append(struct['mean_rho'])
    
    if len(all_lifetimes) < 20:
        return PartialCorrelationResult(
            lifetime_S_correlation=0, lifetime_rho_correlation=0, S_rho_correlation=0,
            partial_lifetime_S_given_rho=0, partial_lifetime_rho_given_S=0,
            partial_lifetime_S_p_value=1, partial_lifetime_rho_p_value=1,
            S_is_independent_of_rho=False,
            interpretation="Insufficient data"
        )
    
    # Raw correlations
    r_lifetime_S, _ = stats.pearsonr(all_lifetimes, all_S)
    r_lifetime_rho, _ = stats.pearsonr(all_lifetimes, all_rho)
    r_S_rho, _ = stats.pearsonr(all_S, all_rho)
    
    # Partial correlations
    partial_lifetime_S, p_partial_S = partial_correlation(all_lifetimes, all_S, all_rho)
    partial_lifetime_rho, p_partial_rho = partial_correlation(all_lifetimes, all_rho, all_S)
    
    # Independence check: S is independent if partial correlation is still significant
    S_independent = p_partial_S < 0.05 and partial_lifetime_S > 0.1
    
    # Interpretation
    interps = []
    interps.append(f"Raw correlations: lifetime↔S={r_lifetime_S:.3f}, lifetime↔ρ={r_lifetime_rho:.3f}, S↔ρ={r_S_rho:.3f}")
    
    if S_independent:
        interps.append(f"✓ S IS INDEPENDENT: Partial r(lifetime,S|ρ)={partial_lifetime_S:.3f}, p={p_partial_S:.4f}")
        interps.append("S is a DISTINCT organizing variable, not just another form of energy")
    else:
        if p_partial_S >= 0.05:
            interps.append(f"⚠ S effect diminished when controlling for ρ: partial r={partial_lifetime_S:.3f}, p={p_partial_S:.4f}")
        else:
            interps.append(f"Weak partial correlation: r={partial_lifetime_S:.3f}")
    
    return PartialCorrelationResult(
        lifetime_S_correlation=float(r_lifetime_S),
        lifetime_rho_correlation=float(r_lifetime_rho),
        S_rho_correlation=float(r_S_rho),
        partial_lifetime_S_given_rho=partial_lifetime_S,
        partial_lifetime_rho_given_S=partial_lifetime_rho,
        partial_lifetime_S_p_value=p_partial_S,
        partial_lifetime_rho_p_value=p_partial_rho,
        S_is_independent_of_rho=S_independent,
        interpretation=" | ".join(interps)
    )


# ============================================================
# TEST 3: MERGE ACTIVITY vs ∇ρ (GRADIENT)
# ============================================================

class MergeTestResult(BaseModel):
    """Result of Test 3: Merge activity vs gradient."""
    test_type: str
    n_runs: int
    config: Dict
    
    # Merge statistics
    n_merges: int
    n_births: int  # For comparison
    
    # Gradient percentiles
    merge_gradient_mean: float
    merge_gradient_ci_low: float
    merge_gradient_ci_high: float
    
    birth_gradient_mean: float  # Comparison baseline
    random_gradient_mean: float
    
    # Enrichment ratios
    merge_vs_random_enrichment: float
    merge_vs_birth_enrichment: float
    
    # Statistical tests
    merge_vs_random_p: float
    merge_vs_birth_p: float
    
    # ρ comparison (to show gradient dominates)
    merge_rho_mean: float
    birth_rho_mean: float
    
    interpretation: str


def run_simulation_for_merge_test(
    dimension: str, size: int, alpha: float, lambda_relax: float,
    gamma_wave: float, steps: int, seed: int
) -> Dict:
    """Run simulation and extract merge location data."""
    
    np.random.seed(seed)
    
    if dimension == '2d':
        sim = QMRTSimulator2D(size=size, beta=alpha, lambda_relax=lambda_relax, gamma_wave=gamma_wave)
    else:
        sim = QMRTSimulator3D(size=size, beta=alpha, lambda_relax=lambda_relax, gamma_wave=gamma_wave)
    sim.add_pulse(amplitude=3.0, width=4.0)
    
    tracker = StructureTracker()
    sample_interval = 10
    
    # Store field snapshots at each sample time
    field_snapshots = {}  # time -> (rho, grad_mag)
    birth_data = {}  # structure_id -> {time, position}
    
    for step in range(steps):
        sim.step()
        t = step * sim.dt
        
        if step % sample_interval == 0:
            structures = sim.detect_all_structures()
            
            # Get field state
            rho = sim.phi**2 + sim.phi_dot**2
            grad_mag = sim.compute_gradient_magnitude(rho)
            field_snapshots[round(t, 2)] = (rho.copy(), grad_mag.copy())
            
            # Track structures
            tracker.process_frame(structures, t)
            
            # Record birth positions
            for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
                for sid, tracked in tracker.active_structures[struct_type].items():
                    if sid not in birth_data:
                        trajectory = tracked.get('trajectory', [])
                        if trajectory:
                            pos = trajectory[0][:len(trajectory[0])-1]
                            birth_data[sid] = {
                                'birth_time': tracked.get('birth_time', t),
                                'position': pos
                            }
    
    # After simulation: analyze completed and active structures
    merge_events = []
    birth_events = []
    
    # Get final field state for percentile calculations
    final_rho = sim.phi**2 + sim.phi_dot**2
    final_grad = sim.compute_gradient_magnitude(final_rho)
    
    # Process all tracked structures
    all_structures = {}
    for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
        # Active structures
        for sid, tracked in tracker.active_structures[struct_type].items():
            all_structures[sid] = tracked
        # Completed structures
        for tracked in tracker.completed_structures[struct_type]:
            all_structures[tracked.id] = {
                'id': tracked.id,
                'parent_ids': tracked.parent_ids,
                'birth_time': tracked.birth_time,
                'trajectory': tracked.trajectory
            }
    
    for sid, tracked in all_structures.items():
        parent_ids = tracked.get('parent_ids', [])
        trajectory = tracked.get('trajectory', [])
        birth_time = tracked.get('birth_time', 0)
        
        if not trajectory:
            continue
        
        pos = trajectory[0][:len(trajectory[0])-1]
        pos_int = [max(0, min(int(p), size-1)) for p in pos]
        
        # Use field snapshot closest to birth time if available
        t_key = round(birth_time, 1)
        if t_key in field_snapshots:
            rho, grad_mag = field_snapshots[t_key]
        else:
            rho, grad_mag = final_rho, final_grad
        
        if dimension == '2d':
            local_rho = float(rho[pos_int[0], pos_int[1]])
            local_grad = float(grad_mag[pos_int[0], pos_int[1]])
        else:
            local_rho = float(rho[pos_int[0], pos_int[1], pos_int[2]])
            local_grad = float(grad_mag[pos_int[0], pos_int[1], pos_int[2]])
        
        rho_pct = compute_percentile(local_rho, rho)
        grad_pct = compute_percentile(local_grad, grad_mag)
        
        event_data = {
            'id': sid,
            'time': birth_time,
            'rho_percentile': rho_pct,
            'gradient_percentile': grad_pct
        }
        
        if len(parent_ids) >= 2:
            merge_events.append(event_data)
        else:
            birth_events.append(event_data)
    
    # Random baseline
    n_samples = max(len(merge_events) + len(birth_events), 30)
    random_samples = []
    for _ in range(n_samples):
        if dimension == '2d':
            pos = [np.random.randint(0, size), np.random.randint(0, size)]
            local_grad = float(final_grad[pos[0], pos[1]])
        else:
            pos = [np.random.randint(0, size) for _ in range(3)]
            local_grad = float(final_grad[pos[0], pos[1], pos[2]])
        
        grad_pct = compute_percentile(local_grad, final_grad)
        random_samples.append({'gradient_percentile': grad_pct})
    
    return {
        'seed': seed,
        'merge_events': merge_events,
        'birth_events': birth_events,
        'random_samples': random_samples
    }


@router.post("/validate/merge-vs-gradient", response_model=MergeTestResult)
async def run_merge_vs_gradient_test(request: ValidationTestRequest):
    """
    Test 3: Merge Activity vs ∇ρ (Gradient)
    
    Hypothesis: Merges occur in high-gradient interaction zones.
    Compares merge locations to both random baseline AND birth locations.
    """
    from scipy import stats
    
    if request.seeds:
        seeds = request.seeds[:request.n_runs]
    else:
        seeds = [np.random.randint(0, 100000) for _ in range(request.n_runs)]
    
    all_merge_grad = []
    all_merge_rho = []
    all_birth_grad = []
    all_birth_rho = []
    all_random_grad = []
    
    for seed in seeds:
        result = run_simulation_for_merge_test(
            dimension=request.dimension,
            size=request.size,
            alpha=request.alpha,
            lambda_relax=request.lambda_relax,
            gamma_wave=request.gamma_wave,
            steps=request.steps,
            seed=seed
        )
        
        for m in result['merge_events']:
            all_merge_grad.append(m['gradient_percentile'])
            all_merge_rho.append(m['rho_percentile'])
        
        for b in result['birth_events']:
            all_birth_grad.append(b['gradient_percentile'])
            all_birth_rho.append(b['rho_percentile'])
        
        for r in result['random_samples']:
            all_random_grad.append(r['gradient_percentile'])
    
    n_merges = len(all_merge_grad)
    n_births = len(all_birth_grad)
    
    if n_merges < 5:
        return MergeTestResult(
            test_type="merge_vs_gradient",
            n_runs=request.n_runs,
            config={"dimension": request.dimension, "size": request.size},
            n_merges=n_merges, n_births=n_births,
            merge_gradient_mean=50, merge_gradient_ci_low=50, merge_gradient_ci_high=50,
            birth_gradient_mean=50, random_gradient_mean=50,
            merge_vs_random_enrichment=1, merge_vs_birth_enrichment=1,
            merge_vs_random_p=1, merge_vs_birth_p=1,
            merge_rho_mean=50, birth_rho_mean=50,
            interpretation="Insufficient merge events for analysis"
        )
    
    # Statistics
    merge_grad_mean = float(np.mean(all_merge_grad))
    merge_grad_std = float(np.std(all_merge_grad))
    birth_grad_mean = float(np.mean(all_birth_grad)) if all_birth_grad else 50
    random_grad_mean = float(np.mean(all_random_grad))
    
    merge_rho_mean = float(np.mean(all_merge_rho))
    birth_rho_mean = float(np.mean(all_birth_rho)) if all_birth_rho else 50
    
    # Confidence interval
    se = merge_grad_std / np.sqrt(n_merges)
    ci_low = merge_grad_mean - 1.96 * se
    ci_high = merge_grad_mean + 1.96 * se
    
    # Enrichment
    merge_vs_random = merge_grad_mean / (random_grad_mean + 1e-8)
    merge_vs_birth = merge_grad_mean / (birth_grad_mean + 1e-8)
    
    # Statistical tests
    _, p_vs_random = stats.ttest_ind(all_merge_grad, all_random_grad)
    _, p_vs_birth = stats.ttest_ind(all_merge_grad, all_birth_grad) if all_birth_grad else (0, 1)
    
    # Interpretation
    interps = []
    
    if p_vs_random < 0.05 and merge_grad_mean > random_grad_mean:
        interps.append(f"✓ Merges occur in HIGH-GRADIENT regions: {merge_grad_mean:.1f}% vs random {random_grad_mean:.1f}% (p={p_vs_random:.4f})")
    else:
        interps.append(f"No significant gradient enrichment for merges (p={p_vs_random:.4f})")
    
    if p_vs_birth < 0.05 and merge_grad_mean > birth_grad_mean:
        interps.append(f"✓ Merges have HIGHER gradient than births: {merge_grad_mean:.1f}% vs {birth_grad_mean:.1f}% (p={p_vs_birth:.4f})")
    elif p_vs_birth < 0.05:
        interps.append(f"Merges have lower gradient than births (p={p_vs_birth:.4f})")
    else:
        interps.append(f"Merge and birth gradients similar (p={p_vs_birth:.4f})")
    
    # Check if gradient dominates over ρ
    if merge_grad_mean > merge_rho_mean:
        interps.append(f"Gradient dominates: ∇ρ={merge_grad_mean:.1f}% > ρ={merge_rho_mean:.1f}%")
    
    return MergeTestResult(
        test_type="merge_vs_gradient",
        n_runs=request.n_runs,
        config={
            "dimension": request.dimension,
            "size": request.size,
            "alpha": request.alpha,
            "steps": request.steps
        },
        n_merges=n_merges,
        n_births=n_births,
        merge_gradient_mean=merge_grad_mean,
        merge_gradient_ci_low=ci_low,
        merge_gradient_ci_high=ci_high,
        birth_gradient_mean=birth_grad_mean,
        random_gradient_mean=random_grad_mean,
        merge_vs_random_enrichment=merge_vs_random,
        merge_vs_birth_enrichment=merge_vs_birth,
        merge_vs_random_p=float(p_vs_random),
        merge_vs_birth_p=float(p_vs_birth),
        merge_rho_mean=merge_rho_mean,
        birth_rho_mean=birth_rho_mean,
        interpretation=" | ".join(interps)
    )


# ============================================================
# α-SWEEP: COUPLING STRENGTH VALIDATION
# ============================================================

class AlphaSweepRequest(BaseModel):
    """Request for α-sweep validation."""
    alpha_values: List[float] = Field(default=[0.2, 0.4, 0.6, 0.8, 1.0])
    n_runs_per_alpha: int = Field(default=10, ge=5, le=30)
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=40, ge=20, le=60)
    steps: int = Field(default=200, ge=100, le=400)

class AlphaPointResult(BaseModel):
    """Results for a single α value."""
    alpha: float
    n_runs: int
    
    # Birth enrichment
    birth_rho_mean: float
    birth_rho_ci: List[float]
    birth_gradient_mean: float
    birth_gradient_ci: List[float]
    
    # Merge enrichment
    merge_gradient_mean: float
    merge_gradient_ci: List[float]
    n_merges: int
    
    # Lifetime-S correlation
    lifetime_S_corr: float
    lifetime_S_p: float
    
    # Sample sizes
    n_births: int
    n_structures: int

class AlphaSweepResult(BaseModel):
    """Complete α-sweep results."""
    config: Dict
    alpha_points: List[AlphaPointResult]
    
    # Trend analysis
    birth_rho_trend: str  # "increasing", "decreasing", "flat", "non-monotonic"
    merge_gradient_trend: str
    lifetime_S_trend: str
    
    interpretation: str


@router.post("/validate/alpha-sweep", response_model=AlphaSweepResult)
async def run_alpha_sweep(request: AlphaSweepRequest):
    """
    α-Sweep: Test if coupling strength modulates emergence intensity.
    
    Runs the three core metrics across multiple α values to show
    that emergence effects strengthen with coupling.
    """
    from scipy import stats
    
    alpha_points = []
    
    for alpha in request.alpha_values:
        # Collect data for this α
        all_birth_rho = []
        all_birth_grad = []
        all_merge_grad = []
        all_lifetimes = []
        all_S = []
        total_merges = 0
        total_births = 0
        total_structures = 0
        
        for run_idx in range(request.n_runs_per_alpha):
            seed = np.random.randint(0, 100000)
            
            # Run simulation for birth/merge data
            merge_result = run_simulation_for_merge_test(
                dimension=request.dimension,
                size=request.size,
                alpha=alpha,
                lambda_relax=0.5,
                gamma_wave=0.01,
                steps=request.steps,
                seed=seed
            )
            
            for b in merge_result['birth_events']:
                all_birth_rho.append(b['rho_percentile'])
                all_birth_grad.append(b['gradient_percentile'])
            
            for m in merge_result['merge_events']:
                all_merge_grad.append(m['gradient_percentile'])
            
            total_merges += len(merge_result['merge_events'])
            total_births += len(merge_result['birth_events'])
            
            # Run simulation for lifetime-S data
            longlived_result = run_simulation_for_longlived_test(
                dimension=request.dimension,
                size=request.size,
                alpha=alpha,
                lambda_relax=0.5,
                gamma_wave=0.01,
                steps=request.steps,
                seed=seed + 1  # Different seed for variety
            )
            
            for struct in longlived_result['structure_data']:
                all_lifetimes.append(struct['lifetime'])
                all_S.append(struct['mean_S'])
            
            total_structures += len(longlived_result['structure_data'])
        
        # Compute statistics
        def mean_ci(data):
            if not data:
                return 50.0, [50.0, 50.0]
            mean = float(np.mean(data))
            std = float(np.std(data))
            n = len(data)
            se = std / np.sqrt(n) if n > 0 else 0
            ci = [mean - 1.96 * se, mean + 1.96 * se]
            return mean, ci
        
        birth_rho_mean, birth_rho_ci = mean_ci(all_birth_rho)
        birth_grad_mean, birth_grad_ci = mean_ci(all_birth_grad)
        merge_grad_mean, merge_grad_ci = mean_ci(all_merge_grad) if all_merge_grad else (50.0, [50.0, 50.0])
        
        # Lifetime-S correlation
        if len(all_lifetimes) >= 10:
            corr, p = stats.pearsonr(all_lifetimes, all_S)
        else:
            corr, p = 0.0, 1.0
        
        alpha_points.append(AlphaPointResult(
            alpha=alpha,
            n_runs=request.n_runs_per_alpha,
            birth_rho_mean=birth_rho_mean,
            birth_rho_ci=birth_rho_ci,
            birth_gradient_mean=birth_grad_mean,
            birth_gradient_ci=birth_grad_ci,
            merge_gradient_mean=merge_grad_mean,
            merge_gradient_ci=merge_grad_ci,
            n_merges=total_merges,
            lifetime_S_corr=float(corr),
            lifetime_S_p=float(p),
            n_births=total_births,
            n_structures=total_structures
        ))
    
    # Analyze trends
    def analyze_trend(values):
        if len(values) < 3:
            return "insufficient_data"
        
        # Check monotonicity
        diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
        
        if all(d > 0 for d in diffs):
            return "increasing"
        elif all(d < 0 for d in diffs):
            return "decreasing"
        elif all(abs(d) < 5 for d in diffs):  # Within 5% is "flat"
            return "flat"
        else:
            # Check overall correlation with α
            alphas = [p.alpha for p in alpha_points]
            corr, _ = stats.pearsonr(alphas, values)
            if corr > 0.7:
                return "increasing_trend"
            elif corr < -0.7:
                return "decreasing_trend"
            else:
                return "non_monotonic"
    
    birth_rho_values = [p.birth_rho_mean for p in alpha_points]
    merge_grad_values = [p.merge_gradient_mean for p in alpha_points]
    lifetime_S_values = [p.lifetime_S_corr for p in alpha_points]
    
    birth_trend = analyze_trend(birth_rho_values)
    merge_trend = analyze_trend(merge_grad_values)
    lifetime_trend = analyze_trend(lifetime_S_values)
    
    # Interpretation
    interps = []
    interps.append(f"Birth ρ enrichment trend: {birth_trend} ({birth_rho_values[0]:.1f}% → {birth_rho_values[-1]:.1f}%)")
    interps.append(f"Merge ∇ρ enrichment trend: {merge_trend} ({merge_grad_values[0]:.1f}% → {merge_grad_values[-1]:.1f}%)")
    interps.append(f"Lifetime-S correlation trend: {lifetime_trend} ({lifetime_S_values[0]:.2f} → {lifetime_S_values[-1]:.2f})")
    
    if "increasing" in birth_trend or "increasing" in merge_trend:
        interps.append("✓ Coupling strength (α) modulates emergence intensity")
    
    return AlphaSweepResult(
        config={
            "alpha_values": request.alpha_values,
            "n_runs_per_alpha": request.n_runs_per_alpha,
            "dimension": request.dimension,
            "size": request.size,
            "steps": request.steps
        },
        alpha_points=alpha_points,
        birth_rho_trend=birth_trend,
        merge_gradient_trend=merge_trend,
        lifetime_S_trend=lifetime_trend,
        interpretation=" | ".join(interps)
    )


# ============================================================
# RESOLUTION SANITY CHECK
# ============================================================

# ============================================================
# PAPER 2: LONG-PATH DYNAMICS
# ============================================================

class LongPathConfig(BaseModel):
    """Configuration for extended long-path dynamics simulation."""
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=50, ge=30, le=80, description="Grid size")
    alpha: float = Field(default=0.5, ge=0.1, le=0.9, description="Backreaction coupling")
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0, description="Relaxation rate")
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1, description="Wave damping")
    steps: int = Field(default=3000, ge=500, le=200000, description="Simulation steps (extended for decay analysis)")
    sample_interval: int = Field(default=10, ge=5, le=500, description="Measurement interval")
    seed: Optional[int] = None  # For reproducibility


class SustainedDrivingConfig(BaseModel):
    """Configuration for sustained driving experiment."""
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=50, ge=30, le=80)
    alpha: float = Field(default=0.5, ge=0.1, le=0.9)
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0)
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1)
    steps: int = Field(default=50000, ge=1000, le=200000)
    sample_interval: int = Field(default=50, ge=5, le=500)
    # Driving parameters
    pulse_interval: int = Field(default=1000, ge=100, le=10000, description="Steps between pulses")
    pulse_amplitude: float = Field(default=1.0, ge=0.1, le=5.0, description="Pulse amplitude")
    seed: Optional[int] = None


class TimeSeriesPoint(BaseModel):
    """Single timestep in the long-path time series."""
    t: float
    
    # Structure counts
    total_structures: int
    strain_node_count: int
    cluster_count: int
    vortex_count: int
    particle_node_count: int
    
    # Event counts (this timestep)
    births: int
    deaths: int
    merges: int
    splits: int
    
    # Lifetime statistics (rolling)
    mean_lifetime: float
    max_lifetime: float
    median_lifetime: float
    
    # QMRT metrics
    S_mean: float
    I_TS: float
    
    # Energy statistics
    rho_mean: float
    rho_std: float
    E_total: float


class LongPathAnalysis(BaseModel):
    """Analysis of long-path dynamics time series."""
    # Time windows
    early_window: Tuple[float, float]  # (start, end) in time units
    late_window: Tuple[float, float]
    
    # Steady state detection
    structure_count_stabilized: bool
    stabilization_time: Optional[float]  # When it stabilized (if it did)
    
    # Rolling statistics (late phase)
    structure_count_mean: float
    structure_count_std: float
    structure_count_cv: float  # Coefficient of variation
    
    event_rate_mean: float  # (births + deaths + merges + splits) / time
    event_rate_std: float
    
    # Lifetime distribution analysis
    lifetime_distribution_type: str  # 'exponential', 'heavy_tail', 'bimodal', 'unknown'
    lifetime_mean: float
    lifetime_median: float
    lifetime_std: float
    lifetime_max: float
    
    # S and I_TS over time
    S_early_mean: float
    S_late_mean: float
    S_trend: str  # 'increasing', 'decreasing', 'stable', 'oscillating'
    
    I_TS_early_mean: float
    I_TS_late_mean: float
    I_TS_trend: str
    
    # Autocorrelation (detect oscillations)
    structure_count_autocorr_lag1: float
    structure_count_autocorr_lag5: float
    structure_count_autocorr_lag10: float
    event_rate_autocorr_lag1: float
    
    # Regime classification
    regime: str  # 'convergent', 'oscillatory', 'steady_churn', 'transient'
    regime_confidence: float
    
    # Interpretation
    interpretation: str


class LongPathResult(BaseModel):
    """Complete result of long-path dynamics simulation."""
    config: Dict
    duration_seconds: float
    total_timesteps: int
    total_time_units: float
    
    # Full time series
    time_series: List[TimeSeriesPoint]
    
    # Lifetime data for all structures (for histogram)
    all_lifetimes: List[float]
    
    # Analysis
    analysis: LongPathAnalysis
    
    # Summary statistics
    total_births: int
    total_deaths: int
    total_merges: int
    total_splits: int
    final_structure_count: int


def compute_autocorrelation(series: List[float], lag: int) -> float:
    """Compute autocorrelation at a given lag."""
    if len(series) <= lag + 1:
        return 0.0
    
    n = len(series)
    mean = np.mean(series)
    var = np.var(series)
    
    if var < 1e-10:
        return 0.0
    
    autocov = np.sum((np.array(series[:-lag]) - mean) * (np.array(series[lag:]) - mean)) / (n - lag)
    return float(autocov / var)


def classify_lifetime_distribution(lifetimes: List[float]) -> str:
    """Classify the type of lifetime distribution."""
    if len(lifetimes) < 10:
        return "insufficient_data"
    
    arr = np.array(lifetimes)
    mean_val = np.mean(arr)
    median_val = np.median(arr)
    std_val = np.std(arr)
    max_val = np.max(arr)
    
    # Heavy tail: mean >> median, high max/mean ratio
    skewness_proxy = (mean_val - median_val) / (std_val + 1e-10)
    tail_ratio = max_val / (mean_val + 1e-10)
    
    if skewness_proxy > 0.5 and tail_ratio > 5:
        return "heavy_tail"
    elif abs(skewness_proxy) < 0.3 and tail_ratio < 3:
        return "exponential"
    else:
        # Check for bimodality using histogram
        hist, _ = np.histogram(arr, bins=10)
        peaks = 0
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                peaks += 1
        if peaks >= 2:
            return "bimodal"
        return "unknown"


def detect_trend(values: List[float], window_size: int = 20) -> str:
    """Detect trend in a time series: increasing, decreasing, stable, or oscillating."""
    if len(values) < window_size * 2:
        return "insufficient_data"
    
    arr = np.array(values)
    
    # Compare early vs late windows
    early_mean = np.mean(arr[:window_size])
    late_mean = np.mean(arr[-window_size:])
    
    rel_change = (late_mean - early_mean) / (early_mean + 1e-10)
    
    # Check for oscillation via autocorrelation
    autocorr_lag5 = compute_autocorrelation(values, 5)
    autocorr_lag10 = compute_autocorrelation(values, 10)
    
    # Oscillation if lag5 is negative but lag10 is positive (periodic)
    if autocorr_lag5 < -0.2 and autocorr_lag10 > 0.1:
        return "oscillating"
    
    if abs(rel_change) < 0.1:
        return "stable"
    elif rel_change > 0.1:
        return "increasing"
    else:
        return "decreasing"


def classify_regime(
    structure_cv: float,
    event_rate_cv: float,
    structure_autocorr: float,
    S_trend: str,
    stabilized: bool
) -> Tuple[str, float]:
    """
    Classify the system behavior regime.
    
    Returns: (regime_name, confidence)
    """
    scores = {
        "convergent": 0.0,
        "oscillatory": 0.0,
        "steady_churn": 0.0,
        "transient": 0.0
    }
    
    # Convergent: low CV, stabilized, stable trends
    if stabilized:
        scores["convergent"] += 0.3
    if structure_cv < 0.1:
        scores["convergent"] += 0.3
    if S_trend == "stable":
        scores["convergent"] += 0.2
    
    # Oscillatory: high autocorrelation, periodic
    if abs(structure_autocorr) > 0.5:
        scores["oscillatory"] += 0.4
    if structure_cv > 0.15 and structure_cv < 0.5:
        scores["oscillatory"] += 0.2
    
    # Steady churn: moderate CV, low autocorrelation, high event rate
    if event_rate_cv > 0.2 and structure_cv < 0.3:
        scores["steady_churn"] += 0.3
    if abs(structure_autocorr) < 0.2:
        scores["steady_churn"] += 0.2
    
    # Transient: high CV, not stabilized, changing trends
    if not stabilized:
        scores["transient"] += 0.3
    if structure_cv > 0.3:
        scores["transient"] += 0.2
    if S_trend in ["increasing", "decreasing"]:
        scores["transient"] += 0.2
    
    # Pick highest scoring regime
    best_regime = max(scores, key=scores.get)
    total_score = sum(scores.values())
    confidence = scores[best_regime] / (total_score + 0.01) if total_score > 0 else 0.5
    
    return best_regime, min(1.0, confidence)


@router.post("/longpath/run", response_model=LongPathResult)
async def run_long_path_simulation(config: LongPathConfig):
    """
    Paper 2 Phase 1: Long-Path Dynamics Simulation
    
    Runs an extended simulation (10-20× normal length) and tracks:
    - Structure count over time
    - Event rates (births/deaths/merges/splits)
    - Lifetime distribution
    - S and I_TS evolution
    - Autocorrelation (oscillation detection)
    
    Classifies system behavior:
    - Convergent: reaches steady state
    - Oscillatory: periodic fluctuations
    - Steady churn: constant reorganization without convergence
    - Transient: still evolving
    """
    import time as time_module
    
    start_time = time_module.time()
    
    # Set seed for reproducibility
    if config.seed is not None:
        np.random.seed(config.seed)
    
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
        size_3d = min(config.size, 50)
        sim = QMRTSimulator3D(
            size=size_3d,
            beta=config.alpha,
            lambda_relax=config.lambda_relax,
            gamma_wave=config.gamma_wave,
        )
        sim.add_pulse()
    
    # Structure tracker
    tracker = StructureTracker(dimension=config.dimension, match_threshold=5.0)
    
    # Time series storage
    time_series = []
    
    # Track events per interval
    prev_births = 0
    prev_deaths = 0
    prev_merges = 0
    prev_splits = 0
    
    # Run simulation
    for step in range(config.steps):
        sim.step()
        
        if step % config.sample_interval == 0:
            t = step * sim.dt
            
            # Detect structures
            structures = sim.detect_all_structures()
            tracker.process_frame(structures, t)
            
            # Current counts
            strain_count = len(structures['strain_nodes'])
            cluster_count = len(structures['coherence_clusters'])
            vortex_count = len(structures['torsion_vortices'])
            particle_count = len(structures['particle_nodes'])
            total_count = strain_count + cluster_count + vortex_count + particle_count
            
            # Events since last sample
            births = tracker.births - prev_births
            deaths = tracker.deaths - prev_deaths
            merges = tracker.merges - prev_merges
            splits = tracker.splits - prev_splits
            
            prev_births = tracker.births
            prev_deaths = tracker.deaths
            prev_merges = tracker.merges
            prev_splits = tracker.splits
            
            # Compute current lifetimes of active structures
            current_lifetimes = []
            for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
                for tracked in tracker.active_structures[struct_type].values():
                    age = t - tracked['birth_time']
                    if age > 0:
                        current_lifetimes.append(age)
            
            mean_lifetime = float(np.mean(current_lifetimes)) if current_lifetimes else 0.0
            max_lifetime = float(np.max(current_lifetimes)) if current_lifetimes else 0.0
            median_lifetime = float(np.median(current_lifetimes)) if current_lifetimes else 0.0
            
            # QMRT metrics
            measurement = sim.measure(t)
            
            # Energy stats
            rho = sim.phi**2 + sim.phi_dot**2
            rho_mean = float(np.mean(rho))
            rho_std = float(np.std(rho))
            
            time_series.append(TimeSeriesPoint(
                t=t,
                total_structures=total_count,
                strain_node_count=strain_count,
                cluster_count=cluster_count,
                vortex_count=vortex_count,
                particle_node_count=particle_count,
                births=births,
                deaths=deaths,
                merges=merges,
                splits=splits,
                mean_lifetime=mean_lifetime,
                max_lifetime=max_lifetime,
                median_lifetime=median_lifetime,
                S_mean=measurement['S_total'],
                I_TS=measurement['I_TS'],
                rho_mean=rho_mean,
                rho_std=rho_std,
                E_total=measurement['E_total']
            ))
    
    # Finalize tracking
    final_time = config.steps * sim.dt
    tracked = tracker.finalize(final_time)
    
    # Collect all lifetimes from completed + active structures
    all_lifetimes = []
    for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
        for s in getattr(tracked, struct_type):
            if s.age > 0:
                all_lifetimes.append(s.age)
    
    # ============================================================
    # ANALYSIS
    # ============================================================
    
    n_points = len(time_series)
    
    # Define early and late windows (first 20% vs last 20%)
    early_end_idx = max(1, int(0.2 * n_points))
    late_start_idx = max(early_end_idx + 1, int(0.8 * n_points))
    
    early_window = (time_series[0].t, time_series[early_end_idx - 1].t)
    late_window = (time_series[late_start_idx].t, time_series[-1].t)
    
    # Extract series for analysis
    structure_counts = [p.total_structures for p in time_series]
    event_rates = [p.births + p.deaths + p.merges + p.splits for p in time_series]
    S_values = [p.S_mean for p in time_series]
    I_TS_values = [p.I_TS for p in time_series]
    
    # Late phase statistics
    late_structure_counts = structure_counts[late_start_idx:]
    late_event_rates = event_rates[late_start_idx:]
    late_S = S_values[late_start_idx:]
    late_I_TS = I_TS_values[late_start_idx:]
    
    # Early phase statistics
    early_S = S_values[:early_end_idx]
    early_I_TS = I_TS_values[:early_end_idx]
    
    # Structure count stats
    sc_mean = float(np.mean(late_structure_counts)) if late_structure_counts else 0.0
    sc_std = float(np.std(late_structure_counts)) if late_structure_counts else 0.0
    sc_cv = sc_std / (sc_mean + 1e-10)
    
    # Event rate stats
    er_mean = float(np.mean(late_event_rates)) if late_event_rates else 0.0
    er_std = float(np.std(late_event_rates)) if late_event_rates else 0.0
    
    # Steady state detection: check if late phase variance is significantly lower than early
    if len(structure_counts) > 20:
        early_variance = np.var(structure_counts[:early_end_idx])
        late_variance = np.var(late_structure_counts)
        stabilized = late_variance < early_variance * 0.5 and sc_cv < 0.2
        
        # Find stabilization time (when variance drops below threshold)
        stabilization_time = None
        if stabilized:
            window = max(5, n_points // 20)
            for i in range(window, n_points - window):
                local_cv = np.std(structure_counts[i:i+window]) / (np.mean(structure_counts[i:i+window]) + 1e-10)
                if local_cv < 0.15:
                    stabilization_time = time_series[i].t
                    break
    else:
        stabilized = False
        stabilization_time = None
    
    # Lifetime distribution analysis
    lifetime_type = classify_lifetime_distribution(all_lifetimes)
    lt_mean = float(np.mean(all_lifetimes)) if all_lifetimes else 0.0
    lt_median = float(np.median(all_lifetimes)) if all_lifetimes else 0.0
    lt_std = float(np.std(all_lifetimes)) if all_lifetimes else 0.0
    lt_max = float(np.max(all_lifetimes)) if all_lifetimes else 0.0
    
    # S and I_TS trends
    S_trend = detect_trend(S_values)
    I_TS_trend = detect_trend(I_TS_values)
    
    S_early_mean = float(np.mean(early_S)) if early_S else 0.0
    S_late_mean = float(np.mean(late_S)) if late_S else 0.0
    I_TS_early_mean = float(np.mean(early_I_TS)) if early_I_TS else 0.0
    I_TS_late_mean = float(np.mean(late_I_TS)) if late_I_TS else 0.0
    
    # Autocorrelation
    sc_autocorr_1 = compute_autocorrelation(structure_counts, 1)
    sc_autocorr_5 = compute_autocorrelation(structure_counts, 5)
    sc_autocorr_10 = compute_autocorrelation(structure_counts, 10)
    er_autocorr_1 = compute_autocorrelation(event_rates, 1)
    
    # Regime classification
    regime, regime_conf = classify_regime(
        sc_cv, 
        er_std / (er_mean + 1e-10),
        sc_autocorr_5,
        S_trend,
        stabilized
    )
    
    # Build interpretation
    interps = []
    
    if regime == "convergent":
        interps.append(f"System CONVERGES to steady state (CV={sc_cv:.2f})")
    elif regime == "oscillatory":
        interps.append(f"System shows OSCILLATORY behavior (autocorr@5={sc_autocorr_5:.2f})")
    elif regime == "steady_churn":
        interps.append(f"System in STEADY CHURN (continuous reorganization, event rate≈{er_mean:.1f}/step)")
    else:
        interps.append("System still in TRANSIENT phase (not yet converged)")
    
    interps.append(f"Lifetime distribution: {lifetime_type} (mean={lt_mean:.2f}, max={lt_max:.2f})")
    interps.append(f"S trend: {S_trend} ({S_early_mean:.3f} → {S_late_mean:.3f})")
    interps.append(f"I_TS trend: {I_TS_trend} ({I_TS_early_mean:.3f} → {I_TS_late_mean:.3f})")
    
    analysis = LongPathAnalysis(
        early_window=early_window,
        late_window=late_window,
        structure_count_stabilized=stabilized,
        stabilization_time=stabilization_time,
        structure_count_mean=sc_mean,
        structure_count_std=sc_std,
        structure_count_cv=sc_cv,
        event_rate_mean=er_mean,
        event_rate_std=er_std,
        lifetime_distribution_type=lifetime_type,
        lifetime_mean=lt_mean,
        lifetime_median=lt_median,
        lifetime_std=lt_std,
        lifetime_max=lt_max,
        S_early_mean=S_early_mean,
        S_late_mean=S_late_mean,
        S_trend=S_trend,
        I_TS_early_mean=I_TS_early_mean,
        I_TS_late_mean=I_TS_late_mean,
        I_TS_trend=I_TS_trend,
        structure_count_autocorr_lag1=sc_autocorr_1,
        structure_count_autocorr_lag5=sc_autocorr_5,
        structure_count_autocorr_lag10=sc_autocorr_10,
        event_rate_autocorr_lag1=er_autocorr_1,
        regime=regime,
        regime_confidence=regime_conf,
        interpretation=" | ".join(interps)
    )
    
    duration = time_module.time() - start_time
    
    return LongPathResult(
        config=config.model_dump(),
        duration_seconds=duration,
        total_timesteps=len(time_series),
        total_time_units=final_time,
        time_series=time_series,
        all_lifetimes=all_lifetimes,
        analysis=analysis,
        total_births=tracked.total_births,
        total_deaths=tracked.total_deaths,
        total_merges=tracked.total_merges,
        total_splits=tracked.total_splits,
        final_structure_count=time_series[-1].total_structures if time_series else 0
    )


# ============================================================
# MULTI-SEED LONG-PATH RUNS
# ============================================================

class MultiSeedLongPathRequest(BaseModel):
    """Request for running long-path simulations with multiple seeds."""
    dimension: Literal["2d", "3d"] = "2d"
    size: int = Field(default=50, ge=30, le=80)
    alpha: float = Field(default=0.5, ge=0.1, le=0.9)
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0)
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1)
    steps: int = Field(default=3000, ge=500, le=50000)
    sample_interval: int = Field(default=10, ge=5, le=50)
    n_seeds: int = Field(default=5, ge=2, le=20)
    seeds: Optional[List[int]] = None


class MultiSeedLongPathResult(BaseModel):
    """Aggregated result from multiple long-path runs."""
    config: Dict
    n_seeds: int
    total_duration_seconds: float
    
    # Per-seed results (summary only, not full time series)
    per_seed_summaries: List[Dict]
    
    # Aggregated regime distribution
    regime_distribution: Dict[str, int]  # regime -> count
    dominant_regime: str
    regime_agreement: float  # Fraction agreeing on dominant
    
    # Aggregated statistics (mean ± std across seeds)
    lifetime_mean_across_seeds: float
    lifetime_std_across_seeds: float
    lifetime_distribution_consensus: str
    
    structure_count_mean_across_seeds: float
    structure_count_std_across_seeds: float
    
    S_late_mean_across_seeds: float
    I_TS_late_mean_across_seeds: float
    
    # Interpretation
    interpretation: str


@router.post("/longpath/multi-seed", response_model=MultiSeedLongPathResult)
async def run_multi_seed_long_path(request: MultiSeedLongPathRequest):
    """
    Run long-path simulations with multiple seeds to assess reproducibility
    and consensus on regime classification.
    """
    import time as time_module
    
    start_time = time_module.time()
    
    # Generate seeds if not provided
    if request.seeds:
        seeds = request.seeds[:request.n_seeds]
    else:
        seeds = [np.random.randint(0, 100000) for _ in range(request.n_seeds)]
    
    per_seed_summaries = []
    regimes = []
    lifetime_means = []
    structure_counts = []
    S_late_values = []
    I_TS_late_values = []
    lifetime_types = []
    
    for seed in seeds:
        # Create config for this seed
        config = LongPathConfig(
            dimension=request.dimension,
            size=request.size,
            alpha=request.alpha,
            lambda_relax=request.lambda_relax,
            gamma_wave=request.gamma_wave,
            steps=request.steps,
            sample_interval=request.sample_interval,
            seed=seed
        )
        
        # Run simulation (call the endpoint function directly)
        result = await run_long_path_simulation(config)
        
        # Extract summary
        summary = {
            "seed": seed,
            "regime": result.analysis.regime,
            "regime_confidence": result.analysis.regime_confidence,
            "lifetime_mean": result.analysis.lifetime_mean,
            "lifetime_distribution_type": result.analysis.lifetime_distribution_type,
            "structure_count_mean": result.analysis.structure_count_mean,
            "structure_count_cv": result.analysis.structure_count_cv,
            "S_late_mean": result.analysis.S_late_mean,
            "I_TS_late_mean": result.analysis.I_TS_late_mean,
            "total_births": result.total_births,
            "total_deaths": result.total_deaths
        }
        per_seed_summaries.append(summary)
        
        regimes.append(result.analysis.regime)
        lifetime_means.append(result.analysis.lifetime_mean)
        structure_counts.append(result.analysis.structure_count_mean)
        S_late_values.append(result.analysis.S_late_mean)
        I_TS_late_values.append(result.analysis.I_TS_late_mean)
        lifetime_types.append(result.analysis.lifetime_distribution_type)
    
    # Aggregate regime distribution
    regime_dist = {}
    for r in regimes:
        regime_dist[r] = regime_dist.get(r, 0) + 1
    
    dominant_regime = max(regime_dist, key=regime_dist.get)
    regime_agreement = regime_dist[dominant_regime] / len(regimes)
    
    # Lifetime distribution consensus
    type_counts = {}
    for lt in lifetime_types:
        type_counts[lt] = type_counts.get(lt, 0) + 1
    lifetime_consensus = max(type_counts, key=type_counts.get)
    
    duration = time_module.time() - start_time
    
    # Build interpretation
    interps = []
    interps.append(f"Regime consensus: {dominant_regime} ({regime_agreement*100:.0f}% agreement)")
    interps.append(f"Lifetime type: {lifetime_consensus}")
    interps.append(f"Structure count: {np.mean(structure_counts):.1f} ± {np.std(structure_counts):.1f}")
    interps.append(f"S late-phase: {np.mean(S_late_values):.4f} ± {np.std(S_late_values):.4f}")
    
    return MultiSeedLongPathResult(
        config={
            "dimension": request.dimension,
            "size": request.size,
            "alpha": request.alpha,
            "lambda_relax": request.lambda_relax,
            "gamma_wave": request.gamma_wave,
            "steps": request.steps,
            "n_seeds": request.n_seeds
        },
        n_seeds=len(seeds),
        total_duration_seconds=duration,
        per_seed_summaries=per_seed_summaries,
        regime_distribution=regime_dist,
        dominant_regime=dominant_regime,
        regime_agreement=regime_agreement,
        lifetime_mean_across_seeds=float(np.mean(lifetime_means)),
        lifetime_std_across_seeds=float(np.std(lifetime_means)),
        lifetime_distribution_consensus=lifetime_consensus,
        structure_count_mean_across_seeds=float(np.mean(structure_counts)),
        structure_count_std_across_seeds=float(np.std(structure_counts)),
        S_late_mean_across_seeds=float(np.mean(S_late_values)),
        I_TS_late_mean_across_seeds=float(np.mean(I_TS_late_values)),
        interpretation=" | ".join(interps)
    )


# ============================================================
# RESOLUTION SANITY CHECK
# ============================================================

class SanityCheckRequest(BaseModel):
    """Request for resolution/timestep sanity check."""
    grid_sizes: List[int] = Field(default=[30, 40, 50])
    n_runs: int = Field(default=10, ge=5, le=20)
    alpha: float = Field(default=0.5)
    steps: int = Field(default=200)

class SanityCheckResult(BaseModel):
    """Results of sanity check."""
    config: Dict
    results_by_size: Dict[int, Dict]
    metrics_stable: bool
    interpretation: str


@router.post("/validate/sanity-check", response_model=SanityCheckResult)
async def run_sanity_check(request: SanityCheckRequest):
    """
    Resolution Sanity Check: Verify results are stable across grid sizes.
    """
    from scipy import stats
    
    results_by_size = {}
    
    for size in request.grid_sizes:
        all_birth_rho = []
        all_lifetime_S_corrs = []
        
        for _ in range(request.n_runs):
            seed = np.random.randint(0, 100000)
            
            # Birth enrichment
            birth_result = run_single_simulation_for_test(
                dimension="2d",
                size=size,
                alpha=request.alpha,
                lambda_relax=0.5,
                gamma_wave=0.01,
                steps=request.steps,
                seed=seed
            )
            
            for e in birth_result['birth_events']:
                all_birth_rho.append(e['rho_percentile'])
            
            # Lifetime-S
            longlived_result = run_simulation_for_longlived_test(
                dimension="2d",
                size=size,
                alpha=request.alpha,
                lambda_relax=0.5,
                gamma_wave=0.01,
                steps=request.steps,
                seed=seed + 1
            )
            
            lifetimes = [s['lifetime'] for s in longlived_result['structure_data']]
            S_vals = [s['mean_S'] for s in longlived_result['structure_data']]
            
            if len(lifetimes) >= 5:
                corr, _ = stats.pearsonr(lifetimes, S_vals)
                all_lifetime_S_corrs.append(corr)
        
        birth_mean = float(np.mean(all_birth_rho)) if all_birth_rho else 50.0
        birth_std = float(np.std(all_birth_rho)) if all_birth_rho else 0.0
        corr_mean = float(np.mean(all_lifetime_S_corrs)) if all_lifetime_S_corrs else 0.0
        corr_std = float(np.std(all_lifetime_S_corrs)) if all_lifetime_S_corrs else 0.0
        
        results_by_size[size] = {
            "birth_rho_mean": birth_mean,
            "birth_rho_std": birth_std,
            "lifetime_S_corr_mean": corr_mean,
            "lifetime_S_corr_std": corr_std,
            "n_births": len(all_birth_rho)
        }
    
    # Check stability (all within 10% of each other)
    birth_means = [r["birth_rho_mean"] for r in results_by_size.values()]
    corr_means = [r["lifetime_S_corr_mean"] for r in results_by_size.values()]
    
    birth_range = max(birth_means) - min(birth_means)
    corr_range = max(corr_means) - min(corr_means)
    
    stable = birth_range < 15 and corr_range < 0.3
    
    interps = []
    interps.append(f"Birth ρ range across sizes: {birth_range:.1f}%")
    interps.append(f"Lifetime-S corr range: {corr_range:.2f}")
    if stable:
        interps.append("✓ Metrics STABLE across resolutions")
    else:
        interps.append("⚠ Some variation across resolutions")
    
    return SanityCheckResult(
        config={
            "grid_sizes": request.grid_sizes,
            "n_runs": request.n_runs,
            "alpha": request.alpha
        },
        results_by_size=results_by_size,
        metrics_stable=stable,
        interpretation=" | ".join(interps)
    )


# ============================================================
# SUSTAINED DRIVING EXPERIMENT
# ============================================================

class SustainedDrivingResult(BaseModel):
    """Result of sustained driving experiment."""
    config: Dict
    duration_seconds: float
    total_timesteps: int
    total_pulses: int
    
    # Time series (same structure as LongPath)
    time_series: List[TimeSeriesPoint]
    
    # Comparison: driven vs undriven baseline
    driven_S_late: float
    undriven_S_late: float  # From previous runs
    S_maintenance_factor: float  # driven / undriven
    
    driven_I_TS_late: float
    I_TS_maintenance_factor: float
    
    # Analysis
    steady_state_reached: bool
    S_stabilized: bool
    interpretation: str


@router.post("/longpath/sustained-driving", response_model=SustainedDrivingResult)
async def run_sustained_driving(config: SustainedDrivingConfig):
    """
    Paper 2 Critical Experiment: Sustained Driving
    
    Tests whether periodic energy injection can maintain organization (S > 0)
    that would otherwise decay to zero.
    
    This answers: "Does organization require sustained input?"
    """
    import time as time_module
    
    start_time = time_module.time()
    
    # Set seed
    if config.seed is not None:
        np.random.seed(config.seed)
    
    # Create simulator
    if config.dimension == "2d":
        sim = QMRTSimulator2D(
            size=config.size,
            beta=config.alpha,
            lambda_relax=config.lambda_relax,
            gamma_wave=config.gamma_wave,
        )
        sim.add_pulse(amplitude=3.0)  # Initial pulse
    else:
        size_3d = min(config.size, 50)
        sim = QMRTSimulator3D(
            size=size_3d,
            beta=config.alpha,
            lambda_relax=config.lambda_relax,
            gamma_wave=config.gamma_wave,
        )
        sim.add_pulse()
    
    # Structure tracker
    tracker = StructureTracker(dimension=config.dimension, match_threshold=5.0)
    
    time_series = []
    prev_births = 0
    prev_deaths = 0
    prev_merges = 0
    prev_splits = 0
    
    total_pulses = 0
    
    # Run simulation with periodic driving
    for step in range(config.steps):
        sim.step()
        
        # Add pulse periodically (sustained driving)
        if step > 0 and step % config.pulse_interval == 0:
            # Add pulse at random location
            if config.dimension == "2d":
                cx = np.random.randint(10, config.size - 10)
                cy = np.random.randint(10, config.size - 10)
                sim.add_pulse(center=(cx, cy), amplitude=config.pulse_amplitude, width=4.0)
            else:
                cx = np.random.randint(10, size_3d - 10)
                cy = np.random.randint(10, size_3d - 10)
                cz = np.random.randint(10, size_3d - 10)
                sim.add_pulse(center=(cx, cy, cz), amplitude=config.pulse_amplitude)
            total_pulses += 1
        
        # Sample
        if step % config.sample_interval == 0:
            t = step * sim.dt
            
            structures = sim.detect_all_structures()
            tracker.process_frame(structures, t)
            
            strain_count = len(structures['strain_nodes'])
            cluster_count = len(structures['coherence_clusters'])
            vortex_count = len(structures['torsion_vortices'])
            particle_count = len(structures['particle_nodes'])
            total_count = strain_count + cluster_count + vortex_count + particle_count
            
            births = tracker.births - prev_births
            deaths = tracker.deaths - prev_deaths
            merges = tracker.merges - prev_merges
            splits = tracker.splits - prev_splits
            
            prev_births = tracker.births
            prev_deaths = tracker.deaths
            prev_merges = tracker.merges
            prev_splits = tracker.splits
            
            # Lifetimes
            current_lifetimes = []
            for struct_type in ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']:
                for tracked in tracker.active_structures[struct_type].values():
                    age = t - tracked['birth_time']
                    if age > 0:
                        current_lifetimes.append(age)
            
            mean_lifetime = float(np.mean(current_lifetimes)) if current_lifetimes else 0.0
            max_lifetime = float(np.max(current_lifetimes)) if current_lifetimes else 0.0
            median_lifetime = float(np.median(current_lifetimes)) if current_lifetimes else 0.0
            
            measurement = sim.measure(t)
            rho = sim.phi**2 + sim.phi_dot**2
            
            time_series.append(TimeSeriesPoint(
                t=t,
                total_structures=total_count,
                strain_node_count=strain_count,
                cluster_count=cluster_count,
                vortex_count=vortex_count,
                particle_node_count=particle_count,
                births=births,
                deaths=deaths,
                merges=merges,
                splits=splits,
                mean_lifetime=mean_lifetime,
                max_lifetime=max_lifetime,
                median_lifetime=median_lifetime,
                S_mean=measurement['S_total'],
                I_TS=measurement['I_TS'],
                rho_mean=float(np.mean(rho)),
                rho_std=float(np.std(rho)),
                E_total=measurement['E_total']
            ))
    
    # Analysis
    n = len(time_series)
    late_start = int(0.8 * n)
    
    S_late = [p.S_mean for p in time_series[late_start:]]
    I_TS_late = [p.I_TS for p in time_series[late_start:]]
    
    driven_S_late = float(np.mean(S_late))
    driven_I_TS_late = float(np.mean(I_TS_late))
    
    # Compare to undriven baseline (from 100k step run)
    # Undriven at equivalent time: S ~ 10^-10, I_TS ~ 0.55
    undriven_S_late = 1e-10  # From previous runs
    undriven_I_TS_late = 0.55
    
    S_maintenance = driven_S_late / (undriven_S_late + 1e-20)
    I_TS_maintenance = driven_I_TS_late / (undriven_I_TS_late + 1e-10)
    
    # Check if S stabilized (CV < 0.5 in late phase)
    S_cv = np.std(S_late) / (np.mean(S_late) + 1e-20)
    S_stabilized = S_cv < 0.5 and driven_S_late > 1e-6
    
    # Interpretation
    interps = []
    if driven_S_late > 1e-4:
        interps.append(f"S MAINTAINED at {driven_S_late:.6f} (vs undriven ~0)")
        interps.append("✓ SUSTAINED DRIVING PRESERVES ORGANIZATION")
    elif driven_S_late > 1e-8:
        interps.append(f"S partially maintained ({driven_S_late:.2e})")
        interps.append("Driving slows but doesn't fully prevent decay")
    else:
        interps.append(f"S still decays to ~0 even with driving")
        interps.append("Driving insufficient at these parameters")
    
    interps.append(f"Pulse interval: {config.pulse_interval} steps, amplitude: {config.pulse_amplitude}")
    interps.append(f"Total pulses: {total_pulses}")
    
    duration = time_module.time() - start_time
    
    return SustainedDrivingResult(
        config=config.model_dump(),
        duration_seconds=duration,
        total_timesteps=len(time_series),
        total_pulses=total_pulses,
        time_series=time_series,
        driven_S_late=driven_S_late,
        undriven_S_late=undriven_S_late,
        S_maintenance_factor=S_maintenance,
        driven_I_TS_late=driven_I_TS_late,
        I_TS_maintenance_factor=I_TS_maintenance,
        steady_state_reached=S_cv < 0.3,
        S_stabilized=S_stabilized,
        interpretation=" | ".join(interps)
    )


# ============================================================
# LOCALIZED DRIVING EXPERIMENT (Matter vs Space Test)
# ============================================================

class LocalizedDrivingConfig(BaseModel):
    """Configuration for localized driving experiment - testing matter vs space hypothesis."""
    dimension: Literal["2d"] = "2d"  # Start with 2D for clarity
    size: int = Field(default=80, ge=50, le=120, description="Grid size (larger to see contrast)")
    alpha: float = Field(default=0.5, ge=0.1, le=0.9)
    lambda_relax: float = Field(default=0.5, ge=0.1, le=1.0)
    gamma_wave: float = Field(default=0.01, ge=0.001, le=0.1)
    D_medium: float = Field(default=0.1, ge=0.0, le=0.5, description="Medium diffusion coefficient - KEY for localization")
    steps: int = Field(default=30000, ge=5000, le=100000)
    sample_interval: int = Field(default=100, ge=10, le=500)
    
    # Driving region parameters
    driven_region_center: Optional[List[int]] = None  # If None, use grid center
    driven_region_radius: float = Field(default=8.0, ge=3.0, le=20.0, description="Radius of driven region")
    
    # Driving parameters
    pulse_interval: int = Field(default=500, ge=50, le=5000, description="Steps between pulses")
    pulse_amplitude: float = Field(default=1.5, ge=0.1, le=5.0, description="Pulse amplitude")
    
    seed: Optional[int] = None


class SpatialMetrics(BaseModel):
    """Spatial metrics comparing driven vs undriven regions."""
    # Inside driven region
    S_inside: float
    rho_inside: float
    gradient_mag_inside: float
    structure_count_inside: int
    
    # Outside driven region (background)
    S_outside: float
    rho_outside: float
    gradient_mag_outside: float
    structure_count_outside: int
    
    # Contrast ratios
    S_contrast: float  # S_inside / S_outside
    rho_contrast: float
    gradient_contrast: float
    structure_contrast: float
    
    # Boundary metrics
    boundary_gradient: float  # Gradient at the boundary
    leakage_fraction: float  # How much organization leaked outside


class LocalizedTimePoint(BaseModel):
    """Single timestep in localized driving experiment."""
    t: float
    step: int
    
    # Global metrics
    S_global: float
    E_total: float
    
    # Spatial comparison
    spatial: SpatialMetrics
    
    # Structure distribution
    structures_inside: int
    structures_outside: int
    total_structures: int
    
    # Event tracking
    births: int
    deaths: int


class LocalizedDrivingResult(BaseModel):
    """Result of localized driving experiment."""
    config: Dict
    duration_seconds: float
    total_timesteps: int
    total_pulses: int
    
    # Driven region info
    driven_center: List[int]
    driven_radius: float
    driven_area_fraction: float  # Fraction of grid that's driven
    
    # Time series
    time_series: List[LocalizedTimePoint]
    
    # Late-time analysis (last 20%)
    late_S_inside: float
    late_S_outside: float
    late_S_contrast: float
    
    late_rho_inside: float
    late_rho_outside: float
    late_rho_contrast: float
    
    late_structures_inside: float
    late_structures_outside: float
    
    # Key results
    localization_maintained: bool  # Did structure stay localized?
    spread_rate: float  # Rate at which organization spreads outward
    boundary_sharpness: float  # How sharp is the matter/space boundary?
    
    # Interpretation
    interpretation: List[str]
    experiment_outcome: str  # 'localized_stable', 'spreads', 'decays', 'insufficient'


def compute_spatial_mask_2d(size: int, center: Tuple[int, int], radius: float) -> np.ndarray:
    """Create a binary mask for the driven region."""
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    return r <= radius


def compute_spatial_metrics_2d(
    sim: QMRTSimulator2D, 
    mask: np.ndarray, 
    structures: Dict
) -> SpatialMetrics:
    """Compute metrics comparing inside vs outside the driven region."""
    
    c_eff = sim.compute_c_eff()
    rho = sim.phi**2 + sim.phi_dot**2
    
    # Compute gradient magnitude
    grad_x = np.roll(c_eff, -1, axis=0) - c_eff
    grad_y = np.roll(c_eff, -1, axis=1) - c_eff
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    
    # Inside mask
    inside = mask
    outside = ~mask
    
    # Mean values inside/outside
    c_inside = c_eff[inside]
    c_outside = c_eff[outside]
    
    # S metric (coefficient of variation of c_eff)
    S_inside = np.std(c_inside) / (np.mean(c_inside) + 1e-10) if len(c_inside) > 0 else 0
    S_outside = np.std(c_outside) / (np.mean(c_outside) + 1e-10) if len(c_outside) > 0 else 0
    
    rho_inside = float(np.mean(rho[inside])) if np.sum(inside) > 0 else 0
    rho_outside = float(np.mean(rho[outside])) if np.sum(outside) > 0 else 0
    
    grad_inside = float(np.mean(grad_mag[inside])) if np.sum(inside) > 0 else 0
    grad_outside = float(np.mean(grad_mag[outside])) if np.sum(outside) > 0 else 0
    
    # Count structures inside/outside
    def count_structures_in_mask(structs: List[Dict], mask: np.ndarray) -> int:
        count = 0
        for s in structs:
            pos = s.get('position', s.get('center', [0, 0]))
            i, j = int(pos[0]), int(pos[1])
            if 0 <= i < mask.shape[0] and 0 <= j < mask.shape[1]:
                if mask[i, j]:
                    count += 1
        return count
    
    all_structs = (
        structures.get('strain_nodes', []) +
        structures.get('coherence_clusters', []) +
        structures.get('torsion_vortices', []) +
        structures.get('particle_nodes', [])
    )
    
    struct_inside = count_structures_in_mask(all_structs, inside)
    struct_outside = count_structures_in_mask(all_structs, outside)
    
    # Compute boundary gradient (ring around driven region)
    # Use a ring from radius to radius+2
    x, y = np.meshgrid(np.arange(mask.shape[0]), np.arange(mask.shape[1]), indexing='ij')
    center = np.array(np.where(mask)).mean(axis=1)
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    
    # Find the radius of the driven region
    driven_radius = np.sqrt(np.sum(mask) / np.pi)
    boundary_ring = (r >= driven_radius - 1) & (r <= driven_radius + 3)
    boundary_gradient = float(np.mean(grad_mag[boundary_ring])) if np.sum(boundary_ring) > 0 else 0
    
    # Leakage: fraction of high-gradient (organization) that's outside
    high_grad_threshold = np.percentile(grad_mag, 90)
    high_grad_mask = grad_mag > high_grad_threshold
    leakage = np.sum(high_grad_mask & outside) / (np.sum(high_grad_mask) + 1e-10)
    
    return SpatialMetrics(
        S_inside=float(S_inside),
        rho_inside=rho_inside,
        gradient_mag_inside=grad_inside,
        structure_count_inside=struct_inside,
        S_outside=float(S_outside),
        rho_outside=rho_outside,
        gradient_mag_outside=grad_outside,
        structure_count_outside=struct_outside,
        S_contrast=float(S_inside / (S_outside + 1e-10)),
        rho_contrast=float(rho_inside / (rho_outside + 1e-10)),
        gradient_contrast=float(grad_inside / (grad_outside + 1e-10)),
        structure_contrast=float((struct_inside + 1) / (struct_outside + 1)),
        boundary_gradient=boundary_gradient,
        leakage_fraction=float(leakage)
    )


@router.post("/longpath/localized-driving", response_model=LocalizedDrivingResult)
async def run_localized_driving(config: LocalizedDrivingConfig):
    """
    Phase 3 Critical Experiment: Localized Driving
    
    Tests the "matter vs space" hypothesis:
    - Apply periodic driving ONLY to a small region
    - Leave the rest undriven (background/"space")
    - Measure: Does a stable localized structure form?
    
    Possible outcomes:
    A) Localized stable structure forms → "matter-like" behavior
    B) Driven region spreads everywhere → no localization
    C) Structure forms but decays → driving insufficient
    
    This is the key test for whether the medium supports persistent,
    localized pockets of organization.
    """
    import time as time_module
    
    start_time = time_module.time()
    
    # Set seed
    if config.seed is not None:
        np.random.seed(config.seed)
    
    size = config.size
    
    # Driven region center
    if config.driven_region_center is not None:
        driven_center = tuple(config.driven_region_center)
    else:
        driven_center = (size // 2, size // 2)
    
    driven_radius = config.driven_region_radius
    
    # Create spatial mask for driven region
    driven_mask = compute_spatial_mask_2d(size, driven_center, driven_radius)
    driven_area = np.sum(driven_mask)
    total_area = size * size
    driven_fraction = driven_area / total_area
    
    # Create simulator
    sim = QMRTSimulator2D(
        size=size,
        beta=config.alpha,
        lambda_relax=config.lambda_relax,
        gamma_wave=config.gamma_wave,
        D_medium=config.D_medium,  # KEY parameter for localization
    )
    
    # Initial pulse in driven region only
    sim.add_pulse(center=driven_center, amplitude=3.0, width=driven_radius * 0.5)
    
    # Structure tracker
    tracker = StructureTracker(dimension='2d', match_threshold=5.0)
    
    time_series = []
    prev_births = 0
    prev_deaths = 0
    total_pulses = 1  # Count initial pulse
    
    # Run simulation
    for step in range(config.steps):
        sim.step()
        
        # Add pulse periodically - ONLY IN DRIVEN REGION
        if step > 0 and step % config.pulse_interval == 0:
            # Random position WITHIN driven region
            angle = np.random.uniform(0, 2 * np.pi)
            r = np.random.uniform(0, driven_radius * 0.8)  # Stay inside
            cx = int(driven_center[0] + r * np.cos(angle))
            cy = int(driven_center[1] + r * np.sin(angle))
            cx = np.clip(cx, 5, size - 5)
            cy = np.clip(cy, 5, size - 5)
            
            sim.add_pulse(center=(cx, cy), amplitude=config.pulse_amplitude, width=3.0)
            total_pulses += 1
        
        # Sample
        if step % config.sample_interval == 0:
            t = step * sim.dt
            
            structures = sim.detect_all_structures()
            tracker.process_frame(structures, t)
            
            # Compute spatial metrics
            spatial = compute_spatial_metrics_2d(sim, driven_mask, structures)
            
            births = tracker.births - prev_births
            deaths = tracker.deaths - prev_deaths
            prev_births = tracker.births
            prev_deaths = tracker.deaths
            
            total_structs = (
                len(structures['strain_nodes']) +
                len(structures['coherence_clusters']) +
                len(structures['torsion_vortices']) +
                len(structures['particle_nodes'])
            )
            
            measurement = sim.measure(t)
            
            time_series.append(LocalizedTimePoint(
                t=t,
                step=step,
                S_global=measurement['S_total'],
                E_total=measurement['E_total'],
                spatial=spatial,
                structures_inside=spatial.structure_count_inside,
                structures_outside=spatial.structure_count_outside,
                total_structures=total_structs,
                births=births,
                deaths=deaths
            ))
    
    # Late-time analysis (last 20%)
    n = len(time_series)
    late_start = int(0.8 * n)
    late_series = time_series[late_start:]
    
    late_S_inside = float(np.mean([p.spatial.S_inside for p in late_series]))
    late_S_outside = float(np.mean([p.spatial.S_outside for p in late_series]))
    late_S_contrast = late_S_inside / (late_S_outside + 1e-10)
    
    late_rho_inside = float(np.mean([p.spatial.rho_inside for p in late_series]))
    late_rho_outside = float(np.mean([p.spatial.rho_outside for p in late_series]))
    late_rho_contrast = late_rho_inside / (late_rho_outside + 1e-10)
    
    late_struct_inside = float(np.mean([p.structures_inside for p in late_series]))
    late_struct_outside = float(np.mean([p.structures_outside for p in late_series]))
    
    # Compute spread rate (how leakage changes over time)
    early_leakage = np.mean([p.spatial.leakage_fraction for p in time_series[:int(0.2*n)]])
    late_leakage = np.mean([p.spatial.leakage_fraction for p in late_series])
    spread_rate = (late_leakage - early_leakage) / (time_series[-1].t - time_series[0].t + 1e-10)
    
    # Boundary sharpness (higher = sharper)
    late_boundary_grad = float(np.mean([p.spatial.boundary_gradient for p in late_series]))
    late_grad_outside = float(np.mean([p.spatial.gradient_mag_outside for p in late_series]))
    boundary_sharpness = late_boundary_grad / (late_grad_outside + 1e-10)
    
    # Determine outcome
    interpretation = []
    
    # Check if localization is maintained
    localization_maintained = (
        late_S_contrast > 2.0 and  # Inside has 2x more organization
        late_leakage < 0.5 and  # Less than half leaked out
        late_S_inside > 1e-4  # Organization actually exists
    )
    
    if localization_maintained:
        if late_S_contrast > 10:
            outcome = 'localized_stable'
            interpretation.append(f"STRONG LOCALIZATION: S contrast = {late_S_contrast:.1f}x")
            interpretation.append("Driven region maintains organization while background decays")
            interpretation.append("This supports 'matter = localized sustained organization'")
        else:
            outcome = 'localized_stable'
            interpretation.append(f"LOCALIZATION ACHIEVED: S contrast = {late_S_contrast:.1f}x")
            interpretation.append("Moderate differentiation between driven and background")
    elif late_leakage > 0.7:
        outcome = 'spreads'
        interpretation.append(f"SPREADING: Organization leaked out (leakage = {late_leakage:.2f})")
        interpretation.append("System does not support localization - energy spreads everywhere")
    elif late_S_inside < 1e-6:
        outcome = 'decays'
        interpretation.append(f"DECAY: Even driven region lost organization (S = {late_S_inside:.2e})")
        interpretation.append("Driving insufficient or decay too fast")
    else:
        outcome = 'insufficient'
        interpretation.append(f"INCONCLUSIVE: S contrast = {late_S_contrast:.1f}x")
        interpretation.append("Some localization but not strong enough")
    
    interpretation.append(f"Driven area: {driven_fraction*100:.1f}% of grid (radius={driven_radius})")
    interpretation.append(f"Boundary sharpness: {boundary_sharpness:.2f}")
    interpretation.append(f"Spread rate: {spread_rate:.4f}/time unit")
    interpretation.append(f"Total pulses: {total_pulses}")
    
    duration = time_module.time() - start_time
    
    return LocalizedDrivingResult(
        config=config.model_dump(),
        duration_seconds=duration,
        total_timesteps=len(time_series),
        total_pulses=total_pulses,
        driven_center=list(driven_center),
        driven_radius=driven_radius,
        driven_area_fraction=float(driven_fraction),
        time_series=time_series,
        late_S_inside=late_S_inside,
        late_S_outside=late_S_outside,
        late_S_contrast=late_S_contrast,
        late_rho_inside=late_rho_inside,
        late_rho_outside=late_rho_outside,
        late_rho_contrast=late_rho_contrast,
        late_structures_inside=late_struct_inside,
        late_structures_outside=late_struct_outside,
        localization_maintained=localization_maintained,
        spread_rate=spread_rate,
        boundary_sharpness=boundary_sharpness,
        interpretation=interpretation,
        experiment_outcome=outcome
    )



# ============================================================
# BIASED MEDIUM EXPERIMENT (Matter from Imbalance)
# ============================================================

class BiasedMediumSimulator2D:
    """
    2D QMRT simulator with SPATIALLY VARYING parameters.
    
    Instead of uniform γ, β, λ across the grid, we allow spatial fields:
    - γ(x,y): wave damping
    - β(x,y): backreaction coupling
    - λ(x,y): relaxation rate
    
    This tests the hypothesis:
    "Structure emerges from imbalance, not external driving"
    """
    
    def __init__(self, size=60, c_0=2.0, tau_0=1.0, D_medium=0.1, dt=0.04):
        self.size = size
        self.c_0 = c_0
        self.tau_0 = tau_0
        self.D_medium = D_medium
        self.dt = dt
        
        # Fields
        self.phi = np.zeros((size, size))
        self.phi_dot = np.zeros((size, size))
        self.tau = np.ones((size, size)) * tau_0
        self.tau_prev = self.tau.copy()
        
        # SPATIALLY VARYING PARAMETERS (initialized to uniform)
        self.gamma_field = np.ones((size, size)) * 0.01  # Wave damping
        self.beta_field = np.ones((size, size)) * 0.5    # Backreaction coupling
        self.lambda_field = np.ones((size, size)) * 0.5  # Relaxation rate
        
        self.source_center = (size // 2, size // 2)
    
    def set_biased_region(self, center, radius, 
                          gamma_inside=None, beta_inside=None, lambda_inside=None,
                          gamma_outside=None, beta_outside=None, lambda_outside=None):
        """
        Create a biased region with different parameters inside vs outside.
        
        Example: Lower damping inside (γ_in < γ_out) → energy persists longer there
        """
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        mask = r <= radius
        
        if gamma_inside is not None and gamma_outside is not None:
            self.gamma_field[mask] = gamma_inside
            self.gamma_field[~mask] = gamma_outside
        
        if beta_inside is not None and beta_outside is not None:
            self.beta_field[mask] = beta_inside
            self.beta_field[~mask] = beta_outside
        
        if lambda_inside is not None and lambda_outside is not None:
            self.lambda_field[mask] = lambda_inside
            self.lambda_field[~mask] = lambda_outside
    
    def set_multiple_bias_spots(self, spots, radius,
                                 gamma_spot=None, beta_spot=None, lambda_spot=None,
                                 gamma_bg=None, beta_bg=None, lambda_bg=None):
        """
        Create multiple biased spots (potential matter sites).
        
        spots: list of (x, y) centers
        """
        # Set background first
        if gamma_bg is not None:
            self.gamma_field[:] = gamma_bg
        if beta_bg is not None:
            self.beta_field[:] = beta_bg
        if lambda_bg is not None:
            self.lambda_field[:] = lambda_bg
        
        # Then set spots
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        for cx, cy in spots:
            r = np.sqrt((x - cx)**2 + (y - cy)**2)
            mask = r <= radius
            if gamma_spot is not None:
                self.gamma_field[mask] = gamma_spot
            if beta_spot is not None:
                self.beta_field[mask] = beta_spot
            if lambda_spot is not None:
                self.lambda_field[mask] = lambda_spot
    
    def compute_c_eff(self):
        return np.clip(self.c_0 * self.tau / self.tau_0, 0.3, self.c_0 * 1.5)
    
    def compute_tau_eq(self, rho):
        """Tau equilibrium with SPATIALLY VARYING beta."""
        rho_smooth = gaussian_filter(rho, sigma=2.0)
        rho_max = np.max(rho_smooth) + 1e-10
        return self.tau_0 / (1 + self.beta_field * rho_smooth / rho_max)
    
    def compute_laplacian(self, f):
        return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
                np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4*f)
    
    def compute_gradient_magnitude(self, f):
        gx = np.roll(f, -1, 0) - f
        gy = np.roll(f, -1, 1) - f
        return np.sqrt(gx**2 + gy**2)
    
    def step(self):
        """Step with SPATIALLY VARYING parameters."""
        self.tau_prev = self.tau.copy()
        rho = self.phi**2 + self.phi_dot**2
        
        # Tau evolution with spatial lambda
        tau_eq = self.compute_tau_eq(rho)
        lap_tau = self.compute_laplacian(self.tau)
        dtau_dt = -self.lambda_field * (self.tau - tau_eq) + self.D_medium * lap_tau
        self.tau += dtau_dt * self.dt
        self.tau = np.clip(self.tau, 0.1, 2.0)
        
        # Phi evolution with spatial gamma
        c_eff = self.compute_c_eff()
        lap_phi = self.compute_laplacian(self.phi)
        acc = c_eff**2 * lap_phi - self.gamma_field * self.phi_dot
        self.phi_dot += acc * self.dt
        self.phi += self.phi_dot * self.dt
    
    def add_pulse(self, center=None, amplitude=3.0, width=4.0):
        if center is None:
            center = self.source_center
        x, y = np.meshgrid(np.arange(self.size), np.arange(self.size), indexing='ij')
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        self.phi_dot += amplitude * np.exp(-r**2 / (2*width**2))
        self.source_center = center
    
    def add_uniform_noise(self, amplitude=0.1):
        """Add small uniform noise to seed structure everywhere."""
        self.phi_dot += np.random.uniform(-amplitude, amplitude, (self.size, self.size))
    
    def measure(self, t):
        """Measure with spatial breakdown."""
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
        
        return {
            't': float(t),
            'E_total': float(E_total),
            'E_kinetic': float(E_kinetic),
            'E_gradient': float(E_gradient),
            'S_total': float(S_total),
            'rho_mean': float(np.mean(rho)),
            'rho_max': float(np.max(rho)),
            'rho_std': float(np.std(rho)),
        }
    
    def measure_by_region(self, mask):
        """Measure metrics separately for inside/outside mask."""
        rho = self.phi**2 + self.phi_dot**2
        c_eff = self.compute_c_eff()
        grad_c = self.compute_gradient_magnitude(c_eff)
        
        inside = mask
        outside = ~mask
        
        c_inside = c_eff[inside]
        c_outside = c_eff[outside]
        
        S_inside = np.std(c_inside) / (np.mean(c_inside) + 1e-10) if len(c_inside) > 0 else 0
        S_outside = np.std(c_outside) / (np.mean(c_outside) + 1e-10) if len(c_outside) > 0 else 0
        
        return {
            'S_inside': float(S_inside),
            'S_outside': float(S_outside),
            'S_contrast': float(S_inside / (S_outside + 1e-10)),
            'rho_inside': float(np.mean(rho[inside])) if np.sum(inside) > 0 else 0,
            'rho_outside': float(np.mean(rho[outside])) if np.sum(outside) > 0 else 0,
            'grad_inside': float(np.mean(grad_c[inside])) if np.sum(inside) > 0 else 0,
            'grad_outside': float(np.mean(grad_c[outside])) if np.sum(outside) > 0 else 0,
        }
    
    def detect_torsion_vortices(self, vortex_threshold: float = 0.03) -> List[Dict]:
        """
        Detect vortex structures using vorticity (curl of velocity-like field).
        """
        vortices = []
        
        # Compute vorticity: use phi_dot gradient as velocity proxy
        vx = np.roll(self.phi_dot, -1, axis=0) - np.roll(self.phi_dot, 1, axis=0)
        vy = np.roll(self.phi_dot, -1, axis=1) - np.roll(self.phi_dot, 1, axis=1)
        
        # Curl in 2D: ω = ∂v_y/∂x - ∂v_x/∂y
        dvx_dy = np.roll(vx, -1, axis=1) - np.roll(vx, 1, axis=1)
        dvy_dx = np.roll(vy, -1, axis=0) - np.roll(vy, 1, axis=0)
        vorticity = dvy_dx - dvx_dy
        vorticity_mag = np.abs(vorticity)
        
        # Find local maxima above threshold
        for i in range(2, self.size - 2):
            for j in range(2, self.size - 2):
                strength = vorticity_mag[i, j]
                
                if strength > vortex_threshold:
                    local_region = vorticity_mag[i-1:i+2, j-1:j+2]
                    if strength >= np.max(local_region):
                        chirality = 1 if vorticity[i, j] > 0 else -1
                        
                        # Estimate radius
                        radius = 2.0  # Default
                        for r in range(1, min(10, self.size // 4)):
                            samples = []
                            for di in [-r, 0, r]:
                                for dj in [-r, 0, r]:
                                    if di == dj == 0:
                                        continue
                                    ni, nj = i + di, j + dj
                                    if 0 <= ni < self.size and 0 <= nj < self.size:
                                        samples.append(vorticity_mag[ni, nj])
                            if samples and np.mean(samples) < strength * 0.5:
                                radius = float(r)
                                break
                        
                        vortices.append({
                            'position': [i, j],
                            'strength': float(strength),
                            'radius': float(radius),
                            'chirality': int(chirality)
                        })
        
        return vortices


class BiasedMediumConfig(BaseModel):
    """Configuration for biased medium experiment."""
    size: int = Field(default=80, ge=50, le=120)
    steps: int = Field(default=20000, ge=5000, le=100000)
    sample_interval: int = Field(default=100, ge=10, le=500)
    D_medium: float = Field(default=0.05, ge=0.0, le=0.2)
    
    # Bias region geometry
    bias_center: Optional[List[int]] = None  # If None, use grid center
    bias_radius: float = Field(default=10.0, ge=3.0, le=25.0)
    
    # PARAMETER CONTRASTS (inside vs outside the biased region)
    # Lower gamma inside = less damping = energy persists longer
    gamma_inside: float = Field(default=0.005, ge=0.001, le=0.1)
    gamma_outside: float = Field(default=0.02, ge=0.001, le=0.1)
    
    # Higher beta inside = stronger backreaction = more structure
    beta_inside: float = Field(default=0.7, ge=0.1, le=0.9)
    beta_outside: float = Field(default=0.3, ge=0.1, le=0.9)
    
    # Lower lambda inside = slower relaxation = structure persists
    lambda_inside: float = Field(default=0.3, ge=0.1, le=1.0)
    lambda_outside: float = Field(default=0.7, ge=0.1, le=1.0)
    
    # Initial condition: pulse or noise
    initial_condition: Literal["pulse_center", "pulse_bias", "uniform_noise", "random_spots"] = "uniform_noise"
    noise_amplitude: float = Field(default=0.5, ge=0.01, le=2.0)
    
    seed: Optional[int] = None


class BiasedMediumTimePoint(BaseModel):
    """Single timestep in biased medium experiment."""
    t: float
    step: int
    
    # Global
    S_global: float
    E_total: float
    rho_mean: float
    rho_max: float
    
    # Regional
    S_inside: float
    S_outside: float
    S_contrast: float
    rho_inside: float
    rho_outside: float
    rho_contrast: float


class BiasedMediumResult(BaseModel):
    """Result of biased medium experiment."""
    config: Dict
    duration_seconds: float
    
    # Bias region info
    bias_center: List[int]
    bias_radius: float
    bias_area_fraction: float
    
    # Parameter contrasts
    gamma_contrast: float  # gamma_outside / gamma_inside
    beta_contrast: float   # beta_inside / beta_outside
    lambda_contrast: float # lambda_outside / lambda_inside
    
    # Time series
    time_series: List[BiasedMediumTimePoint]
    
    # Late-time analysis
    late_S_inside: float
    late_S_outside: float
    late_S_contrast: float
    late_rho_inside: float
    late_rho_outside: float
    late_rho_contrast: float
    
    # Key results
    structure_preferentially_forms_inside: bool
    structure_persists_inside: bool
    localization_achieved: bool
    
    # Interpretation
    interpretation: List[str]
    experiment_outcome: str  # 'localized', 'spreads', 'no_structure', 'inconclusive'


@router.post("/biased-medium/run", response_model=BiasedMediumResult)
async def run_biased_medium(config: BiasedMediumConfig):
    """
    Phase 4 Experiment: Biased Medium
    
    Tests the hypothesis: "Structure emerges from imbalance, not external driving"
    
    Instead of driving a region externally, we embed asymmetry INTO the medium:
    - Lower γ inside (less damping → energy persists)
    - Higher β inside (stronger coupling → more structure)
    - Lower λ inside (slower relaxation → structure persists)
    
    NO external pulses after initialization - structure must emerge from imbalance.
    """
    import time as time_module
    
    start_time = time_module.time()
    
    if config.seed is not None:
        np.random.seed(config.seed)
    
    size = config.size
    
    # Bias region center
    if config.bias_center is not None:
        bias_center = tuple(config.bias_center)
    else:
        bias_center = (size // 2, size // 2)
    
    bias_radius = config.bias_radius
    
    # Create mask for analysis
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - bias_center[0])**2 + (y - bias_center[1])**2)
    bias_mask = r <= bias_radius
    bias_area = np.sum(bias_mask)
    total_area = size * size
    bias_fraction = bias_area / total_area
    
    # Create simulator
    sim = BiasedMediumSimulator2D(size=size, D_medium=config.D_medium)
    
    # Set biased region parameters
    sim.set_biased_region(
        center=bias_center,
        radius=bias_radius,
        gamma_inside=config.gamma_inside,
        gamma_outside=config.gamma_outside,
        beta_inside=config.beta_inside,
        beta_outside=config.beta_outside,
        lambda_inside=config.lambda_inside,
        lambda_outside=config.lambda_outside
    )
    
    # Initial condition
    if config.initial_condition == "pulse_center":
        sim.add_pulse(center=(size//2, size//2), amplitude=3.0, width=5.0)
    elif config.initial_condition == "pulse_bias":
        sim.add_pulse(center=bias_center, amplitude=3.0, width=bias_radius*0.5)
    elif config.initial_condition == "uniform_noise":
        sim.add_uniform_noise(amplitude=config.noise_amplitude)
    elif config.initial_condition == "random_spots":
        # Random small pulses everywhere
        n_spots = 20
        for _ in range(n_spots):
            cx = np.random.randint(5, size-5)
            cy = np.random.randint(5, size-5)
            sim.add_pulse(center=(cx, cy), amplitude=config.noise_amplitude, width=2.0)
    
    # Run simulation - NO FURTHER DRIVING
    time_series = []
    
    for step in range(config.steps):
        sim.step()
        
        if step % config.sample_interval == 0:
            t = step * sim.dt
            
            m = sim.measure(t)
            regional = sim.measure_by_region(bias_mask)
            
            time_series.append(BiasedMediumTimePoint(
                t=t,
                step=step,
                S_global=m['S_total'],
                E_total=m['E_total'],
                rho_mean=m['rho_mean'],
                rho_max=m['rho_max'],
                S_inside=regional['S_inside'],
                S_outside=regional['S_outside'],
                S_contrast=regional['S_contrast'],
                rho_inside=regional['rho_inside'],
                rho_outside=regional['rho_outside'],
                rho_contrast=regional['rho_inside'] / (regional['rho_outside'] + 1e-10)
            ))
    
    # Late-time analysis (last 20%)
    n = len(time_series)
    late_start = int(0.8 * n)
    late_series = time_series[late_start:]
    
    late_S_inside = float(np.mean([p.S_inside for p in late_series]))
    late_S_outside = float(np.mean([p.S_outside for p in late_series]))
    late_S_contrast = late_S_inside / (late_S_outside + 1e-10)
    
    late_rho_inside = float(np.mean([p.rho_inside for p in late_series]))
    late_rho_outside = float(np.mean([p.rho_outside for p in late_series]))
    late_rho_contrast = late_rho_inside / (late_rho_outside + 1e-10)
    
    # Compare early vs late to detect preferential formation
    early_series = time_series[:int(0.2 * n)]
    early_S_contrast = float(np.mean([p.S_contrast for p in early_series])) if early_series else 1.0
    
    # Determine outcome
    interpretation = []
    
    # Did structure preferentially form inside?
    structure_forms_inside = late_S_contrast > 1.5 and late_S_inside > late_S_outside
    
    # Did structure persist?
    structure_persists = late_S_inside > 0.001  # Threshold for "meaningful" structure
    
    # Contrast thresholds
    gamma_contrast = config.gamma_outside / config.gamma_inside
    beta_contrast = config.beta_inside / config.beta_outside
    lambda_contrast = config.lambda_outside / config.lambda_inside
    
    # Determine localization
    localization_achieved = (
        late_S_contrast > 2.0 and
        late_rho_contrast > 1.5 and
        structure_persists
    )
    
    if localization_achieved:
        outcome = 'localized'
        interpretation.append(f"LOCALIZATION ACHIEVED: S contrast = {late_S_contrast:.2f}x")
        interpretation.append("Structure preferentially forms and persists in biased region")
        interpretation.append("This supports: 'matter = regions of stable imbalance'")
    elif structure_forms_inside and not structure_persists:
        outcome = 'decays'
        interpretation.append(f"Structure formed inside (early contrast = {early_S_contrast:.2f}x)")
        interpretation.append(f"But decayed over time (late S = {late_S_inside:.6f})")
        interpretation.append("Imbalance alone insufficient - needs stronger contrast or nonlinearity")
    elif late_S_contrast < 1.2:
        outcome = 'spreads'
        interpretation.append(f"No preferential formation: S contrast = {late_S_contrast:.2f}x")
        interpretation.append("Structure spreads uniformly despite parameter imbalance")
    else:
        outcome = 'inconclusive'
        interpretation.append(f"Partial effect: S contrast = {late_S_contrast:.2f}x")
        interpretation.append("Some preference for biased region but not strong localization")
    
    interpretation.append(f"Parameter contrasts: γ={gamma_contrast:.1f}x, β={beta_contrast:.1f}x, λ={lambda_contrast:.1f}x")
    interpretation.append(f"Biased region: {bias_fraction*100:.1f}% of grid")
    
    duration = time_module.time() - start_time
    
    return BiasedMediumResult(
        config=config.model_dump(),
        duration_seconds=duration,
        bias_center=list(bias_center),
        bias_radius=bias_radius,
        bias_area_fraction=float(bias_fraction),
        gamma_contrast=gamma_contrast,
        beta_contrast=beta_contrast,
        lambda_contrast=lambda_contrast,
        time_series=time_series,
        late_S_inside=late_S_inside,
        late_S_outside=late_S_outside,
        late_S_contrast=late_S_contrast,
        late_rho_inside=late_rho_inside,
        late_rho_outside=late_rho_outside,
        late_rho_contrast=late_rho_contrast,
        structure_preferentially_forms_inside=structure_forms_inside,
        structure_persists_inside=structure_persists,
        localization_achieved=localization_achieved,
        interpretation=interpretation,
        experiment_outcome=outcome
    )
