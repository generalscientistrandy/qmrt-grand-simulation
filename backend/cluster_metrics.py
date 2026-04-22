#!/usr/bin/env python3
"""
Phase 2: Cluster Metrics Infrastructure
========================================
Four primitives for objective spatial structure analysis:
1. Cluster identity (connected components)
2. Cluster persistence (lifetime tracking)
3. Size distribution
4. Anisotropy (aspect ratio from covariance)

No "filament" labels yet - metrics only.
"""

import numpy as np
from scipy import ndimage
from scipy.ndimage import label, find_objects
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json


@dataclass
class ClusterInfo:
    """Single cluster properties at one frame."""
    id: int
    size: int  # pixels
    centroid: Tuple[float, float]
    mass: float  # sum of field values
    aspect_ratio: float  # λ_max / λ_min from covariance
    bbox: Tuple[int, int, int, int]  # (min_x, min_y, max_x, max_y)
    eigenvalues: Tuple[float, float]  # (λ_min, λ_max)


@dataclass
class ClusterTrack:
    """Tracked cluster over time."""
    track_id: int
    birth_time: float
    death_time: Optional[float] = None
    frames: List[float] = field(default_factory=list)
    sizes: List[int] = field(default_factory=list)
    centroids: List[Tuple[float, float]] = field(default_factory=list)
    aspect_ratios: List[float] = field(default_factory=list)
    
    @property
    def lifetime(self) -> float:
        if self.death_time is not None:
            return self.death_time - self.birth_time
        return self.frames[-1] - self.birth_time if self.frames else 0
    
    @property
    def mean_size(self) -> float:
        return np.mean(self.sizes) if self.sizes else 0
    
    @property
    def mean_aspect_ratio(self) -> float:
        return np.mean(self.aspect_ratios) if self.aspect_ratios else 1.0


class ClusterExtractor:
    """
    Extracts clusters from a scalar field using thresholding + connected components.
    """
    
    def __init__(self, threshold_percentile: float = 90, min_size: int = 4, 
                 connectivity: int = 2):
        """
        Args:
            threshold_percentile: Use top X% of field as cluster mask
            min_size: Minimum cluster size in pixels
            connectivity: 1 for 4-connectivity, 2 for 8-connectivity
        """
        self.threshold_percentile = threshold_percentile
        self.min_size = min_size
        self.connectivity = connectivity
        
        # Structure for connected components
        if connectivity == 1:
            self.struct = ndimage.generate_binary_structure(2, 1)
        else:
            self.struct = ndimage.generate_binary_structure(2, 2)
    
    def extract(self, field: np.ndarray) -> List[ClusterInfo]:
        """
        Extract clusters from a 2D field.
        
        Args:
            field: 2D numpy array (e.g., ρ, |∇ρ|, or strain)
        
        Returns:
            List of ClusterInfo objects
        """
        # Create binary mask using percentile threshold
        threshold = np.percentile(field, self.threshold_percentile)
        mask = field > threshold
        
        # Label connected components
        labeled, n_clusters = label(mask, structure=self.struct)
        
        clusters = []
        for cluster_id in range(1, n_clusters + 1):
            # Extract cluster pixels
            cluster_mask = labeled == cluster_id
            size = np.sum(cluster_mask)
            
            if size < self.min_size:
                continue
            
            # Get pixel coordinates
            y_coords, x_coords = np.where(cluster_mask)
            
            # Compute centroid
            centroid = (float(np.mean(x_coords)), float(np.mean(y_coords)))
            
            # Compute mass (sum of field values in cluster)
            mass = float(np.sum(field[cluster_mask]))
            
            # Compute bounding box
            bbox = (int(x_coords.min()), int(y_coords.min()),
                   int(x_coords.max()), int(y_coords.max()))
            
            # Compute anisotropy via covariance eigenvalues
            aspect_ratio, eigenvalues = self._compute_anisotropy(x_coords, y_coords)
            
            clusters.append(ClusterInfo(
                id=cluster_id,
                size=size,
                centroid=centroid,
                mass=mass,
                aspect_ratio=aspect_ratio,
                bbox=bbox,
                eigenvalues=eigenvalues
            ))
        
        return clusters
    
    def _compute_anisotropy(self, x_coords: np.ndarray, y_coords: np.ndarray) -> Tuple[float, Tuple[float, float]]:
        """
        Compute aspect ratio from covariance matrix eigenvalues.
        
        Returns:
            (aspect_ratio, (λ_min, λ_max))
        """
        if len(x_coords) < 3:
            return 1.0, (1.0, 1.0)
        
        # Center coordinates
        x_c = x_coords - np.mean(x_coords)
        y_c = y_coords - np.mean(y_coords)
        
        # Covariance matrix
        cov = np.cov(np.stack([x_c, y_c]))
        
        # Handle edge cases
        if cov.size == 1:
            return 1.0, (1.0, 1.0)
        
        # Eigenvalues
        try:
            eigenvalues = np.linalg.eigvalsh(cov)
            eigenvalues = np.sort(np.abs(eigenvalues))  # [λ_min, λ_max]
            
            λ_min = max(eigenvalues[0], 0.1)  # Floor to prevent division issues
            λ_max = max(eigenvalues[1], 0.1)
            
            aspect_ratio = float(np.sqrt(λ_max / λ_min))  # Use sqrt for proper length ratio
            aspect_ratio = min(aspect_ratio, 100)  # Cap at reasonable value
        except:
            aspect_ratio = 1.0
            eigenvalues = [1.0, 1.0]
        
        return aspect_ratio, (float(eigenvalues[0]), float(eigenvalues[1]))


class ClusterTracker:
    """
    Tracks clusters across frames using centroid proximity.
    """
    
    def __init__(self, max_distance: float = 5.0):
        """
        Args:
            max_distance: Maximum centroid distance to match clusters between frames
        """
        self.max_distance = max_distance
        self.tracks: Dict[int, ClusterTrack] = {}
        self.next_track_id = 0
        self.active_tracks: Dict[int, int] = {}  # frame_cluster_id -> track_id
        self.last_centroids: Dict[int, Tuple[float, float]] = {}  # track_id -> centroid
    
    def process_frame(self, clusters: List[ClusterInfo], t: float):
        """
        Process clusters from a single frame.
        """
        # Match clusters to existing tracks
        matched_tracks = set()
        new_centroids = {}
        
        for cluster in clusters:
            best_track = None
            best_dist = self.max_distance
            
            # Find closest existing track
            for track_id, centroid in self.last_centroids.items():
                if track_id in matched_tracks:
                    continue
                dist = np.sqrt((cluster.centroid[0] - centroid[0])**2 + 
                              (cluster.centroid[1] - centroid[1])**2)
                if dist < best_dist:
                    best_dist = dist
                    best_track = track_id
            
            if best_track is not None:
                # Update existing track
                track = self.tracks[best_track]
                track.frames.append(t)
                track.sizes.append(cluster.size)
                track.centroids.append(cluster.centroid)
                track.aspect_ratios.append(cluster.aspect_ratio)
                matched_tracks.add(best_track)
                new_centroids[best_track] = cluster.centroid
            else:
                # Create new track
                track_id = self.next_track_id
                self.next_track_id += 1
                
                self.tracks[track_id] = ClusterTrack(
                    track_id=track_id,
                    birth_time=t,
                    frames=[t],
                    sizes=[cluster.size],
                    centroids=[cluster.centroid],
                    aspect_ratios=[cluster.aspect_ratio]
                )
                new_centroids[track_id] = cluster.centroid
        
        # Mark unmatched tracks as dead
        for track_id in list(self.last_centroids.keys()):
            if track_id not in matched_tracks:
                self.tracks[track_id].death_time = t
        
        self.last_centroids = new_centroids
    
    def finalize(self, final_time: float):
        """Mark all remaining active tracks as dead."""
        for track_id in self.last_centroids:
            if self.tracks[track_id].death_time is None:
                self.tracks[track_id].death_time = final_time
    
    def get_lifetime_distribution(self) -> List[float]:
        """Return list of all track lifetimes."""
        return [track.lifetime for track in self.tracks.values() if track.lifetime > 0]
    
    def get_size_distribution(self) -> List[float]:
        """Return list of mean sizes across all tracks."""
        return [track.mean_size for track in self.tracks.values()]
    
    def get_aspect_ratio_distribution(self) -> List[float]:
        """Return list of mean aspect ratios across all tracks."""
        return [track.mean_aspect_ratio for track in self.tracks.values()]


class ClusterMetrics:
    """
    Aggregated cluster metrics for analysis.
    """
    
    def __init__(self, lifetimes: List[float], sizes: List[float], 
                 aspect_ratios: List[float], frame_cluster_counts: List[int]):
        self.lifetimes = np.array(lifetimes)
        self.sizes = np.array(sizes)
        self.aspect_ratios = np.array(aspect_ratios)
        self.frame_cluster_counts = np.array(frame_cluster_counts)
    
    @property
    def n_clusters_total(self) -> int:
        return len(self.lifetimes)
    
    @property
    def lifetime_mean(self) -> float:
        return float(np.mean(self.lifetimes)) if len(self.lifetimes) > 0 else 0
    
    @property
    def lifetime_median(self) -> float:
        return float(np.median(self.lifetimes)) if len(self.lifetimes) > 0 else 0
    
    @property
    def lifetime_p90(self) -> float:
        return float(np.percentile(self.lifetimes, 90)) if len(self.lifetimes) > 0 else 0
    
    @property
    def size_mean(self) -> float:
        return float(np.mean(self.sizes)) if len(self.sizes) > 0 else 0
    
    @property
    def size_max(self) -> float:
        return float(np.max(self.sizes)) if len(self.sizes) > 0 else 0
    
    @property
    def aspect_ratio_mean(self) -> float:
        return float(np.mean(self.aspect_ratios)) if len(self.aspect_ratios) > 0 else 1
    
    @property
    def elongated_fraction(self) -> float:
        """Fraction of clusters with aspect ratio > 3."""
        if len(self.aspect_ratios) == 0:
            return 0
        return float(np.mean(self.aspect_ratios > 3))
    
    @property
    def highly_elongated_fraction(self) -> float:
        """Fraction of clusters with aspect ratio > 5."""
        if len(self.aspect_ratios) == 0:
            return 0
        return float(np.mean(self.aspect_ratios > 5))
    
    def survival_curve(self, time_points: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute survival curve P(lifetime > τ).
        
        Returns:
            (τ values, P(lifetime > τ))
        """
        if len(self.lifetimes) == 0:
            return np.array([0]), np.array([0])
        
        if time_points is None:
            time_points = np.linspace(0, np.max(self.lifetimes), 50)
        
        survival = []
        for τ in time_points:
            survival.append(np.mean(self.lifetimes > τ))
        
        return time_points, np.array(survival)
    
    def to_dict(self) -> dict:
        """Export metrics as dictionary."""
        τ, p_surv = self.survival_curve()
        
        return {
            'n_clusters_total': self.n_clusters_total,
            'lifetime': {
                'mean': self.lifetime_mean,
                'median': self.lifetime_median,
                'p90': self.lifetime_p90,
                'all': self.lifetimes.tolist()
            },
            'size': {
                'mean': self.size_mean,
                'max': self.size_max,
                'all': self.sizes.tolist()
            },
            'aspect_ratio': {
                'mean': self.aspect_ratio_mean,
                'elongated_fraction': self.elongated_fraction,
                'highly_elongated_fraction': self.highly_elongated_fraction,
                'all': self.aspect_ratios.tolist()
            },
            'frame_cluster_counts': self.frame_cluster_counts.tolist(),
            'survival_curve': {
                'tau': τ.tolist(),
                'probability': p_surv.tolist()
            }
        }


def run_cluster_analysis(sim, steps: int, sample_interval: int = 50,
                        threshold_percentile: float = 90,
                        field_type: str = 'gradient') -> ClusterMetrics:
    """
    Run simulation and collect cluster metrics.
    
    Args:
        sim: QMRTSimulator2D instance (already initialized)
        steps: Number of simulation steps
        sample_interval: Sample every N steps
        threshold_percentile: Top X% of field for clustering
        field_type: 'gradient' for |∇ρ|, 'rho' for ρ
    
    Returns:
        ClusterMetrics object
    """
    extractor = ClusterExtractor(
        threshold_percentile=threshold_percentile,
        min_size=4,
        connectivity=2
    )
    tracker = ClusterTracker(max_distance=5.0)
    
    frame_cluster_counts = []
    
    for step in range(steps):
        sim.step()
        
        if step % sample_interval == 0:
            t = step * sim.dt
            
            # Choose field for clustering
            rho = sim.phi**2 + sim.phi_dot**2
            if field_type == 'gradient':
                grad_x = np.gradient(rho, axis=1)
                grad_y = np.gradient(rho, axis=0)
                field = np.sqrt(grad_x**2 + grad_y**2)
            else:
                field = rho
            
            # Extract clusters
            clusters = extractor.extract(field)
            frame_cluster_counts.append(len(clusters))
            
            # Track clusters
            tracker.process_frame(clusters, t)
    
    # Finalize tracking
    final_time = steps * sim.dt
    tracker.finalize(final_time)
    
    # Collect metrics
    return ClusterMetrics(
        lifetimes=tracker.get_lifetime_distribution(),
        sizes=tracker.get_size_distribution(),
        aspect_ratios=tracker.get_aspect_ratio_distribution(),
        frame_cluster_counts=frame_cluster_counts
    )


# Export for use in API
__all__ = ['ClusterExtractor', 'ClusterTracker', 'ClusterMetrics', 
           'ClusterInfo', 'ClusterTrack', 'run_cluster_analysis']
