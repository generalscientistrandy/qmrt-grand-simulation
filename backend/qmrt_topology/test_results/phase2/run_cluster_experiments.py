#!/usr/bin/env python3
"""
Phase 2: Cluster Analysis Experiments
=====================================
A. Undriven vs Driven comparison
B. Power scaling
C. Time evolution (long-path)
"""

import numpy as np
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, '/app/backend')
from cluster_metrics import ClusterExtractor, ClusterTracker, ClusterMetrics, run_cluster_analysis
from qmrt_simulation_api import QMRTSimulator2D

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/phase2"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_undriven_analysis(steps=20000, sample_interval=50):
    """Run undriven simulation and collect cluster metrics."""
    print("\n" + "=" * 60)
    print("UNDRIVEN CLUSTER ANALYSIS")
    print("=" * 60)
    
    np.random.seed(42)
    sim = QMRTSimulator2D(size=50, beta=0.5)
    sim.add_pulse(amplitude=3.0)
    
    metrics = run_cluster_analysis(sim, steps, sample_interval)
    
    print(f"\nResults:")
    print(f"  Total clusters tracked: {metrics.n_clusters_total}")
    print(f"  Lifetime: mean={metrics.lifetime_mean:.2f}, median={metrics.lifetime_median:.2f}, p90={metrics.lifetime_p90:.2f}")
    print(f"  Size: mean={metrics.size_mean:.1f}, max={metrics.size_max:.1f}")
    print(f"  Aspect ratio: mean={metrics.aspect_ratio_mean:.2f}")
    print(f"  Elongated (AR>3): {metrics.elongated_fraction*100:.1f}%")
    print(f"  Highly elongated (AR>5): {metrics.highly_elongated_fraction*100:.1f}%")
    
    return metrics


def run_driven_analysis(steps=20000, sample_interval=50, pulse_interval=1000, pulse_amplitude=2.0):
    """Run driven simulation and collect cluster metrics."""
    print("\n" + "=" * 60)
    print(f"DRIVEN CLUSTER ANALYSIS (interval={pulse_interval}, amp={pulse_amplitude})")
    print("=" * 60)
    
    np.random.seed(42)
    sim = QMRTSimulator2D(size=50, beta=0.5)
    sim.add_pulse(amplitude=3.0)
    
    extractor = ClusterExtractor(threshold_percentile=90, min_size=4, connectivity=2)
    tracker = ClusterTracker(max_distance=5.0)
    
    frame_cluster_counts = []
    
    for step in range(steps):
        sim.step()
        
        # Add periodic driving
        if step > 0 and step % pulse_interval == 0:
            cx = np.random.randint(15, 35)
            cy = np.random.randint(15, 35)
            sim.add_pulse(center=(cx, cy), amplitude=pulse_amplitude, width=4.0)
        
        if step % sample_interval == 0:
            t = step * sim.dt
            
            rho = sim.phi**2 + sim.phi_dot**2
            grad_x = np.gradient(rho, axis=1)
            grad_y = np.gradient(rho, axis=0)
            field = np.sqrt(grad_x**2 + grad_y**2)
            
            clusters = extractor.extract(field)
            frame_cluster_counts.append(len(clusters))
            tracker.process_frame(clusters, t)
    
    final_time = steps * sim.dt
    tracker.finalize(final_time)
    
    metrics = ClusterMetrics(
        lifetimes=tracker.get_lifetime_distribution(),
        sizes=tracker.get_size_distribution(),
        aspect_ratios=tracker.get_aspect_ratio_distribution(),
        frame_cluster_counts=frame_cluster_counts
    )
    
    print(f"\nResults:")
    print(f"  Total clusters tracked: {metrics.n_clusters_total}")
    print(f"  Lifetime: mean={metrics.lifetime_mean:.2f}, median={metrics.lifetime_median:.2f}, p90={metrics.lifetime_p90:.2f}")
    print(f"  Size: mean={metrics.size_mean:.1f}, max={metrics.size_max:.1f}")
    print(f"  Aspect ratio: mean={metrics.aspect_ratio_mean:.2f}")
    print(f"  Elongated (AR>3): {metrics.elongated_fraction*100:.1f}%")
    print(f"  Highly elongated (AR>5): {metrics.highly_elongated_fraction*100:.1f}%")
    
    return metrics


def experiment_A_comparison():
    """A. Undriven vs Driven comparison."""
    print("\n" + "=" * 70)
    print("EXPERIMENT A: UNDRIVEN vs DRIVEN COMPARISON")
    print("=" * 70)
    
    undriven = run_undriven_analysis(steps=20000)
    driven = run_driven_analysis(steps=20000, pulse_interval=1000, pulse_amplitude=2.0)
    
    print("\n" + "-" * 60)
    print("COMPARISON SUMMARY")
    print("-" * 60)
    print(f"{'Metric':<25} {'Undriven':>12} {'Driven':>12} {'Ratio':>12}")
    print("-" * 60)
    
    comparisons = [
        ('Clusters total', undriven.n_clusters_total, driven.n_clusters_total),
        ('Lifetime mean', undriven.lifetime_mean, driven.lifetime_mean),
        ('Lifetime p90', undriven.lifetime_p90, driven.lifetime_p90),
        ('Size mean', undriven.size_mean, driven.size_mean),
        ('Size max', undriven.size_max, driven.size_max),
        ('Aspect ratio mean', undriven.aspect_ratio_mean, driven.aspect_ratio_mean),
        ('Elongated %', undriven.elongated_fraction*100, driven.elongated_fraction*100),
    ]
    
    for name, u, d in comparisons:
        ratio = d / (u + 1e-10)
        print(f"{name:<25} {u:>12.2f} {d:>12.2f} {ratio:>12.2f}")
    
    return {'undriven': undriven.to_dict(), 'driven': driven.to_dict()}


def experiment_B_power_scaling():
    """B. Power scaling of cluster metrics."""
    print("\n" + "=" * 70)
    print("EXPERIMENT B: POWER SCALING")
    print("=" * 70)
    
    # Power = A^2 / T_interval
    configs = [
        (2000, 1.0),  # P = 0.0005
        (1000, 1.0),  # P = 0.001
        (2000, 2.0),  # P = 0.002
        (1000, 2.0),  # P = 0.004
        (500, 2.0),   # P = 0.008
        (1000, 3.0),  # P = 0.009
    ]
    
    results = []
    
    for interval, amp in configs:
        power = amp**2 / interval
        print(f"\nRunning: interval={interval}, amp={amp}, P={power:.4f}")
        
        metrics = run_driven_analysis(
            steps=15000, 
            sample_interval=50,
            pulse_interval=interval,
            pulse_amplitude=amp
        )
        
        results.append({
            'interval': interval,
            'amplitude': amp,
            'power': power,
            'lifetime_mean': metrics.lifetime_mean,
            'lifetime_p90': metrics.lifetime_p90,
            'size_mean': metrics.size_mean,
            'size_max': metrics.size_max,
            'aspect_ratio_mean': metrics.aspect_ratio_mean,
            'elongated_fraction': metrics.elongated_fraction,
            'n_clusters': metrics.n_clusters_total
        })
    
    print("\n" + "-" * 80)
    print("POWER SCALING SUMMARY")
    print("-" * 80)
    print(f"{'Power':>8} {'Lifetime':>10} {'Size':>10} {'AR':>8} {'Elong%':>8} {'N_clust':>8}")
    print("-" * 80)
    
    for r in sorted(results, key=lambda x: x['power']):
        print(f"{r['power']:>8.4f} {r['lifetime_mean']:>10.2f} {r['size_mean']:>10.1f} {r['aspect_ratio_mean']:>8.2f} {r['elongated_fraction']*100:>8.1f} {r['n_clusters']:>8}")
    
    return results


def experiment_C_time_evolution():
    """C. Time evolution of max cluster size and lifetimes."""
    print("\n" + "=" * 70)
    print("EXPERIMENT C: TIME EVOLUTION (LONG-PATH)")
    print("=" * 70)
    
    steps = 30000
    sample_interval = 50
    
    np.random.seed(42)
    sim = QMRTSimulator2D(size=50, beta=0.5)
    sim.add_pulse(amplitude=3.0)
    
    extractor = ClusterExtractor(threshold_percentile=90, min_size=4, connectivity=2)
    
    time_series = []
    
    for step in range(steps):
        sim.step()
        
        # Add driving
        if step > 0 and step % 1000 == 0:
            cx = np.random.randint(15, 35)
            cy = np.random.randint(15, 35)
            sim.add_pulse(center=(cx, cy), amplitude=2.0, width=4.0)
        
        if step % sample_interval == 0:
            t = step * sim.dt
            
            rho = sim.phi**2 + sim.phi_dot**2
            grad_x = np.gradient(rho, axis=1)
            grad_y = np.gradient(rho, axis=0)
            field = np.sqrt(grad_x**2 + grad_y**2)
            
            clusters = extractor.extract(field)
            
            if clusters:
                max_size = max(c.size for c in clusters)
                max_ar = max(c.aspect_ratio for c in clusters)
                mean_ar = np.mean([c.aspect_ratio for c in clusters])
            else:
                max_size = 0
                max_ar = 1
                mean_ar = 1
            
            time_series.append({
                't': t,
                'n_clusters': len(clusters),
                'max_size': max_size,
                'max_aspect_ratio': max_ar,
                'mean_aspect_ratio': mean_ar
            })
    
    # Analyze windows
    n = len(time_series)
    early = time_series[:n//3]
    mid = time_series[n//3:2*n//3]
    late = time_series[2*n//3:]
    
    print("\nTIME EVOLUTION SUMMARY:")
    print("-" * 60)
    print(f"{'Phase':<10} {'N_clust':>10} {'Max_size':>10} {'Mean_AR':>10}")
    print("-" * 60)
    
    for name, window in [('Early', early), ('Middle', mid), ('Late', late)]:
        n_clust = np.mean([w['n_clusters'] for w in window])
        max_sz = np.mean([w['max_size'] for w in window])
        mean_ar = np.mean([w['mean_aspect_ratio'] for w in window])
        print(f"{name:<10} {n_clust:>10.1f} {max_sz:>10.1f} {mean_ar:>10.2f}")
    
    return time_series


def main():
    print("=" * 70)
    print("PHASE 2: CLUSTER ANALYSIS EXPERIMENTS")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Run experiments
    results_A = experiment_A_comparison()
    results_B = experiment_B_power_scaling()
    results_C = experiment_C_time_evolution()
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'experiment_A_comparison': results_A,
        'experiment_B_power_scaling': results_B,
        'experiment_C_time_evolution': results_C
    }
    
    output_file = f"{OUTPUT_DIR}/cluster_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 2 SUMMARY")
    print("=" * 70)
    
    print("\nA. Undriven vs Driven:")
    print(f"   Driven has {results_A['driven']['lifetime']['mean']/results_A['undriven']['lifetime']['mean']:.1f}x longer lifetimes")
    print(f"   Driven has {results_A['driven']['size']['mean']/results_A['undriven']['size']['mean']:.1f}x larger clusters")
    print(f"   Driven elongated fraction: {results_A['driven']['aspect_ratio']['elongated_fraction']*100:.1f}%")
    
    print("\nB. Power scaling:")
    print("   (See table above)")
    
    print("\nC. Time evolution:")
    print("   Clusters stabilize under driving")


if __name__ == "__main__":
    main()
