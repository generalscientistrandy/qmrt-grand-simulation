#!/usr/bin/env python3
"""
QMRT Causal Graph O-Layer
=========================

The ordering layer is measured not as a scalar clock but as the structure 
of the causal graph induced by simulation events. Dynamic ordering is 
detected when spatial changes alter the reachability and precedence 
structure of events, rather than merely preserving a fixed causal order.

CORE IDEA:
  Build directed graph G = (V, E) where:
    - Nodes V are events (threshold crossings, peaks, packet births/decays)
    - Edges E mean "event A can causally precede/influence event B"

EDGE CONDITION (A → B):
  1. Temporal order: t_A < t_B
  2. Causal reachability: d(A,B) ≤ c_eff_avg × (t_B - t_A)
  3. Signal compatibility: same/compatible event types

METRICS:
  O_cons = #valid_causal_edges / #candidate_ordered_pairs
  O_acyc = 1 - #cycles / (#edges + ε)
  O_diff = normalized variation of graph structure across regimes

DYNAMIC O:
  Δ_O(r1, r2) = ||A^(1) - A^(2)||_1 / N²
  where A is adjacency matrix

If geometry changes enough to affect ordering, Δ_O should rise.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from scipy.signal import find_peaks
import json

from dynamical_medium import DynamicalMediumSimulator


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Event:
    """A discrete event in the simulation."""
    event_id: int
    event_type: str  # 'threshold', 'peak', 'birth', 'decay'
    x: float         # Spatial x coordinate
    y: float         # Spatial y coordinate
    t: float         # Simulation time
    amplitude: float = 0.0
    local_c_eff: float = 1.0
    
    def distance_to(self, other: 'Event') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class CausalGraph:
    """Directed graph of causal relations between events."""
    events: List[Event] = field(default_factory=list)
    adjacency: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Graph metrics
    edge_density: float = 0.0
    reachability_fraction: float = 0.0
    longest_chain: int = 0
    acyclicity_score: float = 1.0
    n_connected_components: int = 1
    
    def as_dict(self) -> Dict:
        return {
            'n_events': len(self.events),
            'edge_density': self.edge_density,
            'reachability_fraction': self.reachability_fraction,
            'longest_chain': self.longest_chain,
            'acyclicity_score': self.acyclicity_score,
            'n_connected_components': self.n_connected_components,
        }


@dataclass  
class DynamicOrderingMetrics:
    """Metrics for dynamic O measurement."""
    O_cons: float = 0.0      # Causal consistency
    O_acyc: float = 1.0      # Acyclicity
    O_diff: float = 0.0      # Differentiation across regimes
    O_dyn: float = 0.0       # Combined dynamic ordering score
    
    # Graph comparison
    delta_O: float = 0.0     # Graph distance from baseline
    
    def as_dict(self) -> Dict:
        return {
            'O_cons': self.O_cons,
            'O_acyc': self.O_acyc,
            'O_diff': self.O_diff,
            'O_dyn': self.O_dyn,
            'delta_O': self.delta_O,
        }


# ============================================================
# EVENT EXTRACTION
# ============================================================

def extract_threshold_events(
    phi_history: List[np.ndarray],
    threshold: float,
    probe_points: List[Tuple[int, int]],
    dt: float,
    c_eff_field: np.ndarray,
    min_separation: int = 5
) -> List[Event]:
    """
    Extract threshold crossing events from simulation history.
    """
    events = []
    event_id = 0
    
    for px, py in probe_points:
        trace = [phi[py, px] for phi in phi_history]
        trace = np.array(trace)
        
        # Find upward crossings
        for t in range(1, len(trace)):
            if trace[t-1] < threshold <= trace[t]:
                # Check minimum separation from previous event at this probe
                recent = [e for e in events if e.x == px and e.y == py and t - e.t < min_separation]
                if not recent:
                    events.append(Event(
                        event_id=event_id,
                        event_type='threshold',
                        x=px, y=py,
                        t=t * dt,
                        amplitude=trace[t],
                        local_c_eff=c_eff_field[py, px]
                    ))
                    event_id += 1
    
    return events


def extract_peak_events(
    phi_history: List[np.ndarray],
    probe_points: List[Tuple[int, int]],
    dt: float,
    c_eff_field: np.ndarray,
    height_threshold: float = 0.3,
    distance: int = 10
) -> List[Event]:
    """
    Extract local peak events from simulation history.
    """
    events = []
    event_id = 1000  # Offset to distinguish from threshold events
    
    for px, py in probe_points:
        trace = [phi[py, px] for phi in phi_history]
        trace = np.array(trace)
        
        peaks, properties = find_peaks(trace, height=height_threshold, distance=distance)
        
        for peak_t in peaks:
            events.append(Event(
                event_id=event_id,
                event_type='peak',
                x=px, y=py,
                t=peak_t * dt,
                amplitude=trace[peak_t],
                local_c_eff=c_eff_field[py, px]
            ))
            event_id += 1
    
    return events


def extract_all_events(
    sim: DynamicalMediumSimulator,
    t_run: int = 150,
    n_probes: int = 16
) -> Tuple[List[Event], np.ndarray]:
    """
    Run simulation and extract all events.
    """
    size = sim.size
    
    # Define probe grid
    probe_spacing = size // (int(np.sqrt(n_probes)) + 1)
    probe_points = []
    for i in range(1, int(np.sqrt(n_probes)) + 1):
        for j in range(1, int(np.sqrt(n_probes)) + 1):
            px = i * probe_spacing
            py = j * probe_spacing
            if 0 < px < size and 0 < py < size:
                probe_points.append((px, py))
    
    # Inject initial excitation
    x, y = np.meshgrid(np.arange(size), np.arange(size))
    cx, cy = size // 4, size // 2
    pulse = 4.0 * np.exp(-((x - cx)**2 + (y - cy)**2) / 32)
    sim.phi += pulse
    
    # Run and record history
    phi_history = [sim.phi.copy()]
    for _ in range(t_run):
        sim.step()
        phi_history.append(sim.phi.copy())
    
    c_eff = sim.compute_c_eff()
    
    # Extract events
    threshold_events = extract_threshold_events(
        phi_history, threshold=0.2, probe_points=probe_points,
        dt=sim.dt, c_eff_field=c_eff
    )
    
    peak_events = extract_peak_events(
        phi_history, probe_points=probe_points,
        dt=sim.dt, c_eff_field=c_eff
    )
    
    all_events = threshold_events + peak_events
    
    # Sort by time
    all_events.sort(key=lambda e: e.t)
    
    # Reassign IDs
    for i, e in enumerate(all_events):
        e.event_id = i
    
    return all_events, c_eff


# ============================================================
# CAUSAL GRAPH CONSTRUCTION
# ============================================================

def build_causal_graph(
    events: List[Event],
    c_eff_field: np.ndarray,
    c_eff_mean: float,
    dt: float,
    causal_margin: float = 1.2  # Allow some slack in reachability
) -> CausalGraph:
    """
    Build causal graph from events.
    
    Edge A → B exists if:
      1. t_A < t_B (temporal order)
      2. d(A,B) ≤ c_eff_avg × (t_B - t_A) × causal_margin (reachability)
    """
    n = len(events)
    if n == 0:
        return CausalGraph()
    
    adjacency = np.zeros((n, n), dtype=int)
    
    n_candidate_pairs = 0
    n_valid_edges = 0
    
    for i, event_a in enumerate(events):
        for j, event_b in enumerate(events):
            if event_a.t < event_b.t:  # Temporal order
                n_candidate_pairs += 1
                
                delta_t = event_b.t - event_a.t
                distance = event_a.distance_to(event_b)
                
                # Causal reachability: can a signal from A reach B?
                max_reach = c_eff_mean * delta_t * causal_margin
                
                if distance <= max_reach:
                    adjacency[i, j] = 1
                    n_valid_edges += 1
    
    # Create graph object
    graph = CausalGraph(
        events=events,
        adjacency=adjacency
    )
    
    # Compute metrics
    compute_graph_metrics(graph, n_candidate_pairs, n_valid_edges)
    
    return graph


def compute_graph_metrics(
    graph: CausalGraph,
    n_candidate_pairs: int,
    n_valid_edges: int
):
    """
    Compute graph-based metrics.
    """
    n = len(graph.events)
    adj = graph.adjacency
    
    if n == 0:
        return
    
    # Edge density
    max_edges = n * (n - 1) // 2  # For DAG
    graph.edge_density = n_valid_edges / (max_edges + 1e-10)
    
    # Reachability fraction (using transitive closure)
    # Compute reachability matrix via matrix power
    reachability = adj.copy().astype(float)
    for _ in range(min(n, 10)):  # Limit iterations
        reachability = np.minimum(reachability + reachability @ adj, 1)
    
    n_reachable = np.sum(reachability > 0)
    graph.reachability_fraction = n_reachable / (n_candidate_pairs + 1e-10)
    
    # Longest causal chain (approximation via topological depth)
    # Use BFS-like approach
    in_degree = np.sum(adj, axis=0)
    depth = np.zeros(n)
    
    for iteration in range(n):
        updated = False
        for j in range(n):
            for i in range(n):
                if adj[i, j] and depth[i] + 1 > depth[j]:
                    depth[j] = depth[i] + 1
                    updated = True
        if not updated:
            break
    
    graph.longest_chain = int(np.max(depth)) + 1 if n > 0 else 0
    
    # Acyclicity score (DAGs should have no cycles)
    # Check if graph is DAG by looking for cycles
    # Simple check: if reachability matrix diagonal has nonzeros, there are cycles
    cycles = np.sum(np.diag(reachability) > 0)
    graph.acyclicity_score = 1.0 - cycles / (n + 1e-10)
    
    # Connected components (weak connectivity)
    # Use union-find approximation
    symmetric_adj = adj + adj.T
    visited = np.zeros(n, dtype=bool)
    n_components = 0
    
    for start in range(n):
        if not visited[start]:
            n_components += 1
            # BFS
            queue = [start]
            while queue:
                node = queue.pop(0)
                if visited[node]:
                    continue
                visited[node] = True
                neighbors = np.where(symmetric_adj[node] > 0)[0]
                for neighbor in neighbors:
                    if not visited[neighbor]:
                        queue.append(neighbor)
    
    graph.n_connected_components = n_components


# ============================================================
# DYNAMIC O METRICS
# ============================================================

def compute_graph_distance(graph1: CausalGraph, graph2: CausalGraph) -> float:
    """
    Compute distance between two causal graphs.
    
    Δ_O = ||A^(1) - A^(2)||_1 / N²
    """
    n1 = len(graph1.events)
    n2 = len(graph2.events)
    
    if n1 == 0 or n2 == 0:
        return 1.0  # Maximum distance if one is empty
    
    # Pad to same size
    n = max(n1, n2)
    
    adj1 = np.zeros((n, n))
    adj2 = np.zeros((n, n))
    
    adj1[:n1, :n1] = graph1.adjacency
    adj2[:n2, :n2] = graph2.adjacency
    
    # L1 distance normalized
    distance = np.sum(np.abs(adj1 - adj2)) / (n * n + 1e-10)
    
    return float(distance)


def compute_ordering_metrics(
    graph: CausalGraph,
    baseline_graph: CausalGraph = None
) -> DynamicOrderingMetrics:
    """
    Compute dynamic ordering metrics.
    """
    n = len(graph.events)
    adj = graph.adjacency
    
    # O_cons: Causal consistency
    # What fraction of temporally-ordered pairs are causally connected?
    O_cons = graph.reachability_fraction
    
    # O_acyc: Acyclicity
    O_acyc = graph.acyclicity_score
    
    # O_diff: Differentiation (requires baseline comparison)
    if baseline_graph is not None:
        delta_O = compute_graph_distance(graph, baseline_graph)
    else:
        delta_O = 0.0
    
    # O_diff from graph structure variation
    # Use edge density variation as proxy
    O_diff = graph.edge_density * (1 - graph.edge_density)  # Max at 0.5
    
    # Combined dynamic ordering score
    # O_dyn = μ_graph × (1 - σ_graph)
    metrics = [O_cons, O_acyc]
    mu = np.mean(metrics)
    sigma = np.std(metrics)
    O_dyn = mu * (1 - sigma)
    
    return DynamicOrderingMetrics(
        O_cons=O_cons,
        O_acyc=O_acyc,
        O_diff=O_diff,
        O_dyn=O_dyn,
        delta_O=delta_O
    )


# ============================================================
# REGIME COMPARISON
# ============================================================

def run_regime_comparison(
    regimes: Dict[str, Dict[str, float]],
    size: int = 80,
    t_run: int = 120
) -> Dict:
    """
    Run the same event generation in multiple regimes and compare graphs.
    
    regimes = {
        'weak': {'alpha': 0.2, 'lambda': 0.5},
        'medium': {'alpha': 0.5, 'lambda': 1.0},
        'strong': {'alpha': 0.8, 'lambda': 2.0},
    }
    """
    results = {}
    graphs = {}
    
    # Build graph for each regime
    for regime_name, params in regimes.items():
        sim = DynamicalMediumSimulator(
            size=size,
            beta=params['alpha'],
            lambda_relax=params['lambda'],
            D_medium=0.1,
            gamma_wave=0.01,
        )
        
        # Equilibrate
        for _ in range(50):
            sim.step()
        
        events, c_eff = extract_all_events(sim, t_run=t_run)
        c_eff_mean = np.mean(c_eff)
        
        graph = build_causal_graph(events, c_eff, c_eff_mean, sim.dt)
        graphs[regime_name] = graph
        
        results[regime_name] = {
            'params': params,
            'n_events': len(events),
            'graph_metrics': graph.as_dict(),
        }
    
    # Compute pairwise graph distances
    regime_names = list(regimes.keys())
    distances = {}
    
    for i, r1 in enumerate(regime_names):
        for r2 in regime_names[i+1:]:
            dist = compute_graph_distance(graphs[r1], graphs[r2])
            distances[f'{r1}_vs_{r2}'] = dist
    
    # Compute ordering metrics with weak regime as baseline
    baseline_name = regime_names[0]
    baseline_graph = graphs[baseline_name]
    
    for regime_name, graph in graphs.items():
        metrics = compute_ordering_metrics(graph, baseline_graph)
        results[regime_name]['ordering_metrics'] = metrics.as_dict()
    
    # Summary
    results['graph_distances'] = distances
    results['summary'] = {
        'n_regimes': len(regimes),
        'max_distance': max(distances.values()) if distances else 0,
        'mean_distance': np.mean(list(distances.values())) if distances else 0,
    }
    
    return results, graphs


# ============================================================
# MAIN TEST
# ============================================================

def test_causal_graph_O():
    """
    Test causal graph O measurement across regimes.
    """
    print("=" * 70)
    print("CAUSAL GRAPH O-LAYER TEST")
    print("=" * 70)
    print()
    print("Measuring O as causal graph structure, not scalar clock.")
    print()
    
    # Define regimes
    regimes = {
        'weak': {'alpha': 0.2, 'lambda': 0.5},
        'medium': {'alpha': 0.5, 'lambda': 1.0},
        'strong': {'alpha': 0.8, 'lambda': 2.0},
    }
    
    print("Regimes:")
    for name, params in regimes.items():
        print(f"  {name}: α={params['alpha']}, λ={params['lambda']}")
    print()
    
    print("Running simulations and building causal graphs...")
    results, graphs = run_regime_comparison(regimes, size=80, t_run=120)
    
    print()
    print("-" * 70)
    print("GRAPH METRICS BY REGIME")
    print("-" * 70)
    
    for regime_name in regimes:
        r = results[regime_name]
        g = r['graph_metrics']
        o = r['ordering_metrics']
        print(f"\n{regime_name.upper()} (α={r['params']['alpha']}, λ={r['params']['lambda']}):")
        print(f"  Events: {r['n_events']}")
        print(f"  Edge density:      {g['edge_density']:.3f}")
        print(f"  Reachability:      {g['reachability_fraction']:.3f}")
        print(f"  Longest chain:     {g['longest_chain']}")
        print(f"  Acyclicity:        {g['acyclicity_score']:.3f}")
        print(f"  Components:        {g['n_connected_components']}")
        print(f"  → O_cons: {o['O_cons']:.3f}")
        print(f"  → O_acyc: {o['O_acyc']:.3f}")
        print(f"  → O_dyn:  {o['O_dyn']:.3f}")
        print(f"  → Δ_O:    {o['delta_O']:.3f}")
    
    print()
    print("-" * 70)
    print("GRAPH DISTANCES (REGIME COMPARISONS)")
    print("-" * 70)
    
    for pair, dist in results['graph_distances'].items():
        print(f"  {pair}: Δ_O = {dist:.3f}")
    
    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    
    max_dist = results['summary']['max_distance']
    mean_dist = results['summary']['mean_distance']
    
    # Extract O_dyn values
    O_dyn_values = [results[r]['ordering_metrics']['O_dyn'] for r in regimes]
    O_dyn_range = max(O_dyn_values) - min(O_dyn_values)
    
    print(f"\nGraph distance summary:")
    print(f"  Max Δ_O:  {max_dist:.3f}")
    print(f"  Mean Δ_O: {mean_dist:.3f}")
    print(f"  O_dyn range: {O_dyn_range:.3f}")
    
    if max_dist > 0.1:
        print(f"""
✅ CAUSAL GRAPH STRUCTURE VARIES WITH REGIME

The ordering layer is no longer constant!
  - Graph distance Δ_O = {max_dist:.3f} shows structural change
  - Geometry is affecting the causal graph topology
  
This means:
  - O is geometry-sensitive, not just universal background
  - Stronger spatial structure → different event reachability
  - Dynamic ordering detected
""")
    elif max_dist > 0.02:
        print(f"""
⚠️  PARTIAL ORDERING VARIATION

Some graph structure change detected (Δ_O = {max_dist:.3f})
  - Ordering is mostly stable but not completely rigid
  - May need stronger regime contrast to see full effect
""")
    else:
        print(f"""
✓ ORDERING REMAINS STABLE

Causal graph structure is consistent across regimes.
  - Δ_O = {max_dist:.3f} (very small)
  - This confirms causality is universal in this parameter range
  
Note: This is expected physics for moderate geometry changes.
To see dynamic O, may need more extreme regime contrast.
""")
    
    # Save results
    output = {
        'regimes': {k: {**v, 'ordering_metrics': results[k]['ordering_metrics']} 
                    for k, v in results.items() if k not in ['graph_distances', 'summary']},
        'graph_distances': results['graph_distances'],
        'summary': results['summary'],
        'O_dyn_values': {r: results[r]['ordering_metrics']['O_dyn'] for r in regimes},
    }
    
    with open('/app/backend/qmrt_topology/causal_graph_O_test.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print("\nSaved: causal_graph_O_test.json")
    
    return results, graphs


if __name__ == "__main__":
    test_causal_graph_O()
