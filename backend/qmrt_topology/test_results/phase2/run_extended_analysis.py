#!/usr/bin/env python3
"""
Phase 2B: Extended Cluster Analysis
====================================
Testing for hidden anisotropy via:
1. Absolute threshold (not percentile)
2. Multi-scale clustering (80-99%)
3. Directional coherence (field alignment)
4. Larger grid (100x100)
"""

import numpy as np
import json
import sys
import os
from datetime import datetime
from scipy import ndimage
from scipy.ndimage import label

sys.path.insert(0, '/app/backend')
from qmrt_simulation_api import QMRTSimulator2D

OUTPUT_DIR = "/app/backend/qmrt_topology/test_results/phase2"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_clusters_absolute(field, threshold, min_size=4):
    """Extract clusters using absolute threshold (not percentile)."""
    mask = field > threshold
    struct = ndimage.generate_binary_structure(2, 2)
    labeled, n_clusters = label(mask, structure=struct)
    
    clusters = []
    for cluster_id in range(1, n_clusters + 1):
        cluster_mask = labeled == cluster_id
        size = np.sum(cluster_mask)
        if size < min_size:
            continue
        
        y_coords, x_coords = np.where(cluster_mask)
        
        # Aspect ratio from covariance
        if len(x_coords) >= 3:
            x_c = x_coords - np.mean(x_coords)
            y_c = y_coords - np.mean(y_coords)
            cov = np.cov(np.stack([x_c, y_c]))
            if cov.size > 1:
                eigenvalues = np.sort(np.abs(np.linalg.eigvalsh(cov)))
                ar = np.sqrt(max(eigenvalues[1], 0.1) / max(eigenvalues[0], 0.1))
                ar = min(ar, 100)
            else:
                ar = 1.0
        else:
            ar = 1.0
        
        clusters.append({
            'size': size,
            'aspect_ratio': ar,
            'centroid': (float(np.mean(x_coords)), float(np.mean(y_coords)))
        })
    
    return clusters


def compute_directional_coherence(field):
    """
    Compute directional coherence of gradient field.
    Returns: mean angular variance (low = coherent/aligned)
    """
    grad_y, grad_x = np.gradient(field)
    
    # Compute local direction angles
    angles = np.arctan2(grad_y, grad_x)
    
    # Magnitude-weighted coherence
    mag = np.sqrt(grad_x**2 + grad_y**2)
    
    # Only consider significant gradients
    threshold = np.percentile(mag, 75)
    mask = mag > threshold
    
    if np.sum(mask) < 10:
        return 1.0, 0.0  # No coherence data
    
    # Compute mean direction (circular mean)
    cos_sum = np.sum(np.cos(2 * angles[mask]) * mag[mask])
    sin_sum = np.sum(np.sin(2 * angles[mask]) * mag[mask])
    
    # Resultant length (0 = random, 1 = perfectly aligned)
    r = np.sqrt(cos_sum**2 + sin_sum**2) / np.sum(mag[mask])
    
    # Angular variance (0 = aligned, 1 = random)
    angular_var = 1 - r
    
    return angular_var, r


def compute_spatial_correlation(field, max_lag=20):
    """
    Compute spatial autocorrelation and check for directional anisotropy.
    """
    size = field.shape[0]
    center = size // 2
    
    # Normalize field
    f = field - np.mean(field)
    f = f / (np.std(f) + 1e-10)
    
    # Autocorrelation via FFT
    fft = np.fft.fft2(f)
    power = np.abs(fft)**2
    autocorr = np.real(np.fft.ifft2(power))
    autocorr = np.fft.fftshift(autocorr)
    autocorr = autocorr / autocorr.max()
    
    # Extract horizontal and vertical profiles
    h_profile = autocorr[center, center:center+max_lag]
    v_profile = autocorr[center:center+max_lag, center]
    
    # Radial average
    y, x = np.ogrid[:size, :size]
    r = np.sqrt((x - center)**2 + (y - center)**2).astype(int)
    
    radial = []
    for ri in range(max_lag):
        mask = r == ri
        if np.any(mask):
            radial.append(np.mean(autocorr[mask]))
        else:
            radial.append(0)
    
    # Anisotropy: ratio of horizontal to vertical correlation length
    def find_corr_length(profile, threshold=1/np.e):
        for i, val in enumerate(profile):
            if val < threshold:
                return i
        return len(profile)
    
    xi_h = find_corr_length(h_profile)
    xi_v = find_corr_length(v_profile)
    xi_r = find_corr_length(radial)
    
    anisotropy = max(xi_h, xi_v) / (min(xi_h, xi_v) + 0.1)
    
    return {
        'xi_horizontal': xi_h,
        'xi_vertical': xi_v,
        'xi_radial': xi_r,
        'anisotropy_ratio': anisotropy
    }


def test_1_absolute_threshold():
    """Test 1: Absolute threshold comparison."""
    print("\n" + "=" * 70)
    print("TEST 1: ABSOLUTE THRESHOLD")
    print("=" * 70)
    
    steps = 15000
    sample_step = 14000  # Late time
    
    results = {'undriven': {}, 'driven': {}}
    
    for condition in ['undriven', 'driven']:
        print(f"\n{condition.upper()}:")
        
        np.random.seed(42)
        sim = QMRTSimulator2D(size=50, beta=0.5)
        sim.add_pulse(amplitude=3.0)
        
        for step in range(steps):
            sim.step()
            if condition == 'driven' and step > 0 and step % 1000 == 0:
                cx, cy = np.random.randint(15, 35), np.random.randint(15, 35)
                sim.add_pulse(center=(cx, cy), amplitude=2.0, width=4.0)
        
        # Get gradient field
        rho = sim.phi**2 + sim.phi_dot**2
        grad_x = np.gradient(rho, axis=1)
        grad_y = np.gradient(rho, axis=0)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        print(f"  Gradient stats: mean={np.mean(grad_mag):.4f}, max={np.max(grad_mag):.4f}, p90={np.percentile(grad_mag, 90):.4f}")
        
        # Test multiple absolute thresholds
        thresholds = [0.1, 0.5, 1.0, 2.0, 5.0]
        
        results[condition] = {}
        for thresh in thresholds:
            clusters = extract_clusters_absolute(grad_mag, thresh)
            n = len(clusters)
            if n > 0:
                sizes = [c['size'] for c in clusters]
                ars = [c['aspect_ratio'] for c in clusters]
                mean_size = np.mean(sizes)
                mean_ar = np.mean(ars)
                elongated_frac = np.mean(np.array(ars) > 3)
            else:
                mean_size, mean_ar, elongated_frac = 0, 0, 0
            
            results[condition][thresh] = {
                'n_clusters': n,
                'mean_size': mean_size,
                'mean_ar': mean_ar,
                'elongated_frac': elongated_frac
            }
            print(f"  thresh={thresh}: n={n}, size={mean_size:.1f}, AR={mean_ar:.2f}, elong={elongated_frac*100:.1f}%")
    
    # Compare
    print("\n" + "-" * 60)
    print("COMPARISON (Driven / Undriven ratio):")
    print("-" * 60)
    for thresh in thresholds:
        u = results['undriven'][thresh]
        d = results['driven'][thresh]
        if u['n_clusters'] > 0:
            ratio_n = d['n_clusters'] / u['n_clusters']
            ratio_sz = d['mean_size'] / (u['mean_size'] + 0.1)
        else:
            ratio_n = "inf" if d['n_clusters'] > 0 else 1
            ratio_sz = "N/A"
        print(f"  thresh={thresh}: n_ratio={ratio_n}, size_ratio={ratio_sz}")
    
    return results


def test_2_multiscale_threshold():
    """Test 2: Multi-scale percentile thresholds."""
    print("\n" + "=" * 70)
    print("TEST 2: MULTI-SCALE PERCENTILE THRESHOLDS")
    print("=" * 70)
    
    steps = 15000
    percentiles = [80, 85, 90, 95, 99]
    
    results = {'undriven': {}, 'driven': {}}
    
    for condition in ['undriven', 'driven']:
        print(f"\n{condition.upper()}:")
        
        np.random.seed(42)
        sim = QMRTSimulator2D(size=50, beta=0.5)
        sim.add_pulse(amplitude=3.0)
        
        for step in range(steps):
            sim.step()
            if condition == 'driven' and step > 0 and step % 1000 == 0:
                cx, cy = np.random.randint(15, 35), np.random.randint(15, 35)
                sim.add_pulse(center=(cx, cy), amplitude=2.0, width=4.0)
        
        rho = sim.phi**2 + sim.phi_dot**2
        grad_x = np.gradient(rho, axis=1)
        grad_y = np.gradient(rho, axis=0)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        results[condition] = {}
        for pct in percentiles:
            thresh = np.percentile(grad_mag, pct)
            clusters = extract_clusters_absolute(grad_mag, thresh)
            n = len(clusters)
            if n > 0:
                ars = [c['aspect_ratio'] for c in clusters]
                sizes = [c['size'] for c in clusters]
                mean_ar = np.mean(ars)
                max_ar = np.max(ars)
                elongated = np.mean(np.array(ars) > 3)
                highly_elong = np.mean(np.array(ars) > 5)
            else:
                mean_ar, max_ar, elongated, highly_elong = 0, 0, 0, 0
            
            results[condition][pct] = {
                'n_clusters': n,
                'mean_ar': mean_ar,
                'max_ar': max_ar,
                'elongated_frac': elongated,
                'highly_elongated_frac': highly_elong
            }
            print(f"  p{pct}: n={n}, AR={mean_ar:.2f}, max_AR={max_ar:.2f}, elong={elongated*100:.1f}%, h_elong={highly_elong*100:.1f}%")
    
    return results


def test_3_directional_coherence():
    """Test 3: Directional coherence of gradient field."""
    print("\n" + "=" * 70)
    print("TEST 3: DIRECTIONAL COHERENCE")
    print("=" * 70)
    
    steps = 15000
    results = {}
    
    for condition in ['undriven', 'driven']:
        print(f"\n{condition.upper()}:")
        
        np.random.seed(42)
        sim = QMRTSimulator2D(size=50, beta=0.5)
        sim.add_pulse(amplitude=3.0)
        
        coherence_history = []
        
        for step in range(steps):
            sim.step()
            if condition == 'driven' and step > 0 and step % 1000 == 0:
                cx, cy = np.random.randint(15, 35), np.random.randint(15, 35)
                sim.add_pulse(center=(cx, cy), amplitude=2.0, width=4.0)
            
            if step % 500 == 0:
                rho = sim.phi**2 + sim.phi_dot**2
                angular_var, resultant = compute_directional_coherence(rho)
                coherence_history.append({
                    't': step * sim.dt,
                    'angular_variance': angular_var,
                    'resultant_length': resultant
                })
        
        # Analyze
        early = coherence_history[:len(coherence_history)//3]
        late = coherence_history[2*len(coherence_history)//3:]
        
        early_coh = np.mean([c['resultant_length'] for c in early])
        late_coh = np.mean([c['resultant_length'] for c in late])
        
        results[condition] = {
            'early_coherence': early_coh,
            'late_coherence': late_coh,
            'coherence_change': late_coh - early_coh
        }
        
        print(f"  Early coherence: {early_coh:.4f}")
        print(f"  Late coherence:  {late_coh:.4f}")
        print(f"  Change: {late_coh - early_coh:+.4f}")
    
    print("\n" + "-" * 60)
    print("COMPARISON:")
    print(f"  Driven late coherence: {results['driven']['late_coherence']:.4f}")
    print(f"  Undriven late coherence: {results['undriven']['late_coherence']:.4f}")
    print(f"  Ratio: {results['driven']['late_coherence'] / (results['undriven']['late_coherence'] + 1e-10):.2f}")
    
    return results


def test_4_spatial_anisotropy():
    """Test 4: Spatial correlation anisotropy."""
    print("\n" + "=" * 70)
    print("TEST 4: SPATIAL CORRELATION ANISOTROPY")
    print("=" * 70)
    
    steps = 15000
    results = {}
    
    for condition in ['undriven', 'driven']:
        print(f"\n{condition.upper()}:")
        
        np.random.seed(42)
        sim = QMRTSimulator2D(size=50, beta=0.5)
        sim.add_pulse(amplitude=3.0)
        
        for step in range(steps):
            sim.step()
            if condition == 'driven' and step > 0 and step % 1000 == 0:
                cx, cy = np.random.randint(15, 35), np.random.randint(15, 35)
                sim.add_pulse(center=(cx, cy), amplitude=2.0, width=4.0)
        
        rho = sim.phi**2 + sim.phi_dot**2
        
        corr = compute_spatial_correlation(rho)
        results[condition] = corr
        
        print(f"  ξ_horizontal: {corr['xi_horizontal']}")
        print(f"  ξ_vertical:   {corr['xi_vertical']}")
        print(f"  ξ_radial:     {corr['xi_radial']}")
        print(f"  Anisotropy:   {corr['anisotropy_ratio']:.2f}")
    
    return results


def test_5_larger_grid():
    """Test 5: Larger grid (100x100)."""
    print("\n" + "=" * 70)
    print("TEST 5: LARGER GRID (100x100)")
    print("=" * 70)
    
    steps = 10000  # Fewer steps for larger grid
    
    results = {}
    
    for condition in ['undriven', 'driven']:
        print(f"\n{condition.upper()}:")
        
        np.random.seed(42)
        sim = QMRTSimulator2D(size=100, beta=0.5)
        sim.add_pulse(amplitude=3.0, width=8.0)
        
        for step in range(steps):
            sim.step()
            if condition == 'driven' and step > 0 and step % 1000 == 0:
                cx, cy = np.random.randint(30, 70), np.random.randint(30, 70)
                sim.add_pulse(center=(cx, cy), amplitude=2.0, width=6.0)
        
        rho = sim.phi**2 + sim.phi_dot**2
        grad_x = np.gradient(rho, axis=1)
        grad_y = np.gradient(rho, axis=0)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Cluster analysis
        thresh = np.percentile(grad_mag, 90)
        clusters = extract_clusters_absolute(grad_mag, thresh)
        
        if len(clusters) > 0:
            ars = [c['aspect_ratio'] for c in clusters]
            sizes = [c['size'] for c in clusters]
            
            results[condition] = {
                'n_clusters': len(clusters),
                'mean_size': np.mean(sizes),
                'max_size': np.max(sizes),
                'mean_ar': np.mean(ars),
                'max_ar': np.max(ars),
                'elongated_frac': np.mean(np.array(ars) > 3),
                'highly_elongated_frac': np.mean(np.array(ars) > 5)
            }
        else:
            results[condition] = {
                'n_clusters': 0,
                'mean_size': 0,
                'max_size': 0,
                'mean_ar': 0,
                'max_ar': 0,
                'elongated_frac': 0,
                'highly_elongated_frac': 0
            }
        
        print(f"  Clusters: {results[condition]['n_clusters']}")
        print(f"  Size: mean={results[condition]['mean_size']:.1f}, max={results[condition]['max_size']:.1f}")
        print(f"  AR: mean={results[condition]['mean_ar']:.2f}, max={results[condition]['max_ar']:.2f}")
        print(f"  Elongated: {results[condition]['elongated_frac']*100:.1f}%")
        
        # Spatial correlation
        corr = compute_spatial_correlation(rho, max_lag=40)
        print(f"  Spatial anisotropy: {corr['anisotropy_ratio']:.2f}")
        results[condition]['spatial_anisotropy'] = corr['anisotropy_ratio']
    
    return results


def main():
    print("=" * 70)
    print("PHASE 2B: EXTENDED CLUSTER ANALYSIS")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print("\nLooking for hidden anisotropy via:")
    print("  1. Absolute threshold")
    print("  2. Multi-scale thresholds")
    print("  3. Directional coherence")
    print("  4. Spatial correlation anisotropy")
    print("  5. Larger grid")
    
    results = {}
    
    results['test1_absolute'] = test_1_absolute_threshold()
    results['test2_multiscale'] = test_2_multiscale_threshold()
    results['test3_coherence'] = test_3_directional_coherence()
    results['test4_spatial'] = test_4_spatial_anisotropy()
    results['test5_larger_grid'] = test_5_larger_grid()
    
    # Save
    output_file = f"{OUTPUT_DIR}/extended_cluster_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n\nResults saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: EVIDENCE FOR ANISOTROPY")
    print("=" * 70)
    
    # Check each test
    evidence = []
    
    # Test 1: Absolute threshold
    t1 = results['test1_absolute']
    if t1['driven'].get(1.0, {}).get('n_clusters', 0) > t1['undriven'].get(1.0, {}).get('n_clusters', 0) * 1.5:
        evidence.append("Absolute threshold: MORE clusters with driving")
    
    # Test 2: Multiscale
    t2 = results['test2_multiscale']
    if t2['driven'].get(99, {}).get('max_ar', 0) > 5:
        evidence.append("Multiscale: High AR at extreme percentiles")
    
    # Test 3: Coherence
    t3 = results['test3_coherence']
    if t3['driven']['late_coherence'] > t3['undriven']['late_coherence'] * 1.5:
        evidence.append("Coherence: Driving increases directional alignment")
    
    # Test 4: Spatial
    t4 = results['test4_spatial']
    if t4['driven']['anisotropy_ratio'] > 1.5:
        evidence.append("Spatial: Anisotropic correlation structure")
    
    # Test 5: Larger grid
    t5 = results['test5_larger_grid']
    if t5['driven']['elongated_frac'] > 0.2:
        evidence.append("Larger grid: >20% elongated clusters")
    
    if evidence:
        print("POSITIVE EVIDENCE:")
        for e in evidence:
            print(f"  ✓ {e}")
    else:
        print("NO STRONG EVIDENCE FOR ANISOTROPY")
        print("Cluster morphology appears truly isotropic in this regime.")


if __name__ == "__main__":
    main()
