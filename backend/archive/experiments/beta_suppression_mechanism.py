"""
β-Suppression Mechanism Study
==============================

Question: WHY do β wells suppress topological regeneration?

Candidate mechanisms:
1. Remnant persistence — phase structure washes out faster in high-β
2. Dispersion rate — perturbations spread/flatten faster
3. Channel assignment — self-selection grows slower or saturates lower
4. Effective propagation — wave transport altered to prevent regrowth

Goal: Identify which mechanism(s) explain the C+E antagonism.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict, Tuple
from branch_ce_combined_test import CombinedCESimulator


def measure_remnant_persistence():
    """
    After vortex death, measure how long topology indicator remnants persist
    in high-β vs low-β regions.
    """
    print("="*70)
    print("MECHANISM 1: REMNANT PERSISTENCE")
    print("="*70)
    print()
    print("Question: Do phase remnants persist longer outside β wells?")
    print()
    
    size = 100
    
    # Create two identical vortices: one in high-β, one in low-β
    for region_type in ['inside_well', 'outside_well']:
        print(f"--- {region_type.upper()} ---")
        
        sim = CombinedCESimulator(size=size, gamma=0.007, beta_inside=0.8, beta_outside=0.25)
        
        # Single well at center
        sim.create_beta_wells([(50, 50)], [20])
        sim.channel_assignment[:] = 0
        
        # Place vortex based on region
        if region_type == 'inside_well':
            vortex_pos = (50, 50)  # Inside β well
        else:
            vortex_pos = (20, 50)  # Outside β well
        
        sim.psi_r[:] = 1.2
        sim.add_vortex(vortex_pos, charge=+1, amplitude=1.2, core_radius=4.0)
        sim.seed_oscillators(amp=0.1)
        
        # Track topology indicator at vortex location over time
        topology_at_pos = []
        vortex_alive = []
        
        for step in range(2000):
            sim.step(mode='combined')
            
            if step % 20 == 0:
                topo = sim.compute_topology_indicator()
                topology_at_pos.append(topo[vortex_pos[0], vortex_pos[1]])
                
                # Check if vortex still alive
                vortices = sim.detect_all_vortices(amp_threshold=0.4)
                alive = any(abs(v['position'][0] - vortex_pos[0]) < 10 and 
                           abs(v['position'][1] - vortex_pos[1]) < 10 for v in vortices)
                vortex_alive.append(alive)
        
        # Find when vortex dies
        death_step = None
        for i, alive in enumerate(vortex_alive):
            if not alive and (i == 0 or vortex_alive[i-1]):
                death_step = i * 20
                break
        
        if death_step is None:
            death_step = len(vortex_alive) * 20
            print(f"  Vortex survived entire simulation")
        else:
            print(f"  Vortex died at step {death_step}")
        
        # Measure remnant persistence after death
        if death_step < len(topology_at_pos) * 20:
            death_idx = death_step // 20
            
            # How long until topology drops below threshold?
            remnant_threshold = 0.05
            remnant_duration = 0
            
            for i in range(death_idx, len(topology_at_pos)):
                if topology_at_pos[i] > remnant_threshold:
                    remnant_duration = (i - death_idx) * 20
                else:
                    break
            
            print(f"  Topology at death: {topology_at_pos[death_idx]:.4f}")
            print(f"  Remnant duration (>0.05): {remnant_duration} steps")
            
            # Show decay curve
            if death_idx + 10 < len(topology_at_pos):
                decay = topology_at_pos[death_idx:death_idx+10]
                print(f"  Topology decay: {[f'{t:.3f}' for t in decay]}")
        print()


def measure_dispersion_rate():
    """
    Measure how quickly a localized perturbation spreads in high-β vs low-β regions.
    """
    print("="*70)
    print("MECHANISM 2: DISPERSION RATE")
    print("="*70)
    print()
    print("Question: Do perturbations spread faster inside β wells?")
    print()
    
    size = 100
    
    for region_type in ['inside_well', 'outside_well']:
        print(f"--- {region_type.upper()} ---")
        
        sim = CombinedCESimulator(size=size, gamma=0.007, beta_inside=0.8, beta_outside=0.25)
        sim.create_beta_wells([(50, 50)], [20])
        
        # Uniform background
        sim.psi_r[:] = 1.0
        sim.psi_i[:] = 0.0
        
        # Add localized perturbation
        if region_type == 'inside_well':
            perturb_pos = (50, 50)
        else:
            perturb_pos = (20, 50)
        
        # Gaussian bump perturbation
        x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
        r = np.sqrt((x - perturb_pos[0])**2 + (y - perturb_pos[1])**2)
        perturbation = 0.5 * np.exp(-r**2 / (2 * 3**2))
        sim.psi_r += perturbation
        
        sim.seed_oscillators(amp=0.1)
        
        # Track spread of perturbation
        initial_amplitude = sim.amplitude[perturb_pos[0], perturb_pos[1]]
        
        spread_widths = []
        peak_amplitudes = []
        
        for step in range(1000):
            sim.step(mode='combined')
            
            if step % 50 == 0:
                amp = sim.amplitude
                
                # Measure peak amplitude at perturbation center
                peak = amp[perturb_pos[0], perturb_pos[1]]
                peak_amplitudes.append(peak)
                
                # Measure spread width (radius where amp > 1.1)
                threshold = 1.1
                spread_mask = amp > threshold
                spread_area = np.sum(spread_mask)
                spread_radius = np.sqrt(spread_area / np.pi) if spread_area > 0 else 0
                spread_widths.append(spread_radius)
        
        print(f"  Initial peak: {initial_amplitude:.3f}")
        print(f"  Final peak: {peak_amplitudes[-1]:.3f}")
        print(f"  Peak decay: {(initial_amplitude - peak_amplitudes[-1]) / initial_amplitude * 100:.1f}%")
        print(f"  Spread width: {spread_widths[0]:.1f} → {spread_widths[-1]:.1f}")
        print()


def measure_channel_evolution():
    """
    Measure how channel assignment evolves differently inside vs outside β wells.
    """
    print("="*70)
    print("MECHANISM 3: CHANNEL ASSIGNMENT EVOLUTION")
    print("="*70)
    print()
    print("Question: Does self-selection grow slower inside β wells?")
    print()
    
    size = 100
    
    sim = CombinedCESimulator(size=size, gamma=0.007, beta_inside=0.8, beta_outside=0.25)
    sim.create_beta_wells([(50, 50)], [20])
    sim.channel_assignment[:] = 0
    
    # Seed vortices in both regions
    sim.psi_r[:] = 1.2
    sim.add_vortex((50, 50), charge=+1, amplitude=1.2, core_radius=4.0)  # Inside
    sim.add_vortex((20, 50), charge=-1, amplitude=1.2, core_radius=4.0)  # Outside
    sim.seed_oscillators(amp=0.1)
    
    # Track channel assignment at both locations
    channel_inside = []
    channel_outside = []
    topo_inside = []
    topo_outside = []
    
    inside_pos = (50, 50)
    outside_pos = (20, 50)
    
    for step in range(1500):
        sim.step(mode='combined')
        
        if step % 30 == 0:
            channel_inside.append(sim.channel_assignment[inside_pos[0], inside_pos[1]])
            channel_outside.append(sim.channel_assignment[outside_pos[0], outside_pos[1]])
            
            topo = sim.compute_topology_indicator()
            topo_inside.append(topo[inside_pos[0], inside_pos[1]])
            topo_outside.append(topo[outside_pos[0], outside_pos[1]])
    
    print("Channel assignment over time:")
    print(f"  Inside (t=0, 300, 600, 900, 1200): {[f'{channel_inside[i]:.3f}' for i in [0, 10, 20, 30, 40] if i < len(channel_inside)]}")
    print(f"  Outside (t=0, 300, 600, 900, 1200): {[f'{channel_outside[i]:.3f}' for i in [0, 10, 20, 30, 40] if i < len(channel_outside)]}")
    print()
    
    print("Topology indicator over time:")
    print(f"  Inside (t=0, 300, 600, 900, 1200): {[f'{topo_inside[i]:.3f}' for i in [0, 10, 20, 30, 40] if i < len(topo_inside)]}")
    print(f"  Outside (t=0, 300, 600, 900, 1200): {[f'{topo_outside[i]:.3f}' for i in [0, 10, 20, 30, 40] if i < len(topo_outside)]}")
    print()
    
    # Compare growth rates
    if len(channel_inside) > 10 and len(channel_outside) > 10:
        growth_inside = channel_inside[10] - channel_inside[0]
        growth_outside = channel_outside[10] - channel_outside[0]
        print(f"Channel growth (first 300 steps):")
        print(f"  Inside well: {growth_inside:+.4f}")
        print(f"  Outside well: {growth_outside:+.4f}")
        
        if abs(growth_outside) > 0:
            ratio = growth_inside / growth_outside
            print(f"  Ratio (inside/outside): {ratio:.2f}")


def measure_wave_propagation():
    """
    Compare effective wave speed and propagation inside vs outside β wells.
    """
    print()
    print("="*70)
    print("MECHANISM 4: WAVE PROPAGATION")
    print("="*70)
    print()
    print("Question: Does β change wave transport enough to prevent regrowth?")
    print()
    
    size = 100
    
    sim = CombinedCESimulator(size=size, gamma=0.007, beta_inside=0.8, beta_outside=0.25)
    sim.create_beta_wells([(50, 50)], [20])
    
    # The β-weighted Laplacian is: ∇·(β∇ψ) = β∇²ψ + ∇β·∇ψ
    # Inside well: β = 0.8, so wave propagation is faster
    # Outside well: β = 0.25, so wave propagation is slower
    # At boundary: ∇β ≠ 0, so there's a gradient force
    
    print("Theoretical analysis:")
    print(f"  β inside well: {sim.beta_inside}")
    print(f"  β outside well: {sim.beta_outside}")
    print(f"  Ratio: {sim.beta_inside / sim.beta_outside:.2f}×")
    print()
    print("  Inside wells, the effective wave equation has:")
    print("    - Faster wave speed (c_eff ~ √β)")
    print("    - Faster dispersion of localized structures")
    print("    - ∇β·∇ψ term at boundaries pushes waves outward")
    print()
    
    # Measure actual wave speed by tracking a pulse
    sim.psi_r[:] = 1.0
    
    # Create a small pulse
    pulse_pos = (50, 50)
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    r = np.sqrt((x - pulse_pos[0])**2 + (y - pulse_pos[1])**2)
    sim.psi_r_dot = 0.3 * np.exp(-r**2 / (2 * 2**2))
    
    sim.seed_oscillators(amp=0.1)
    
    # Track wavefront
    print("Wavefront propagation from center of well:")
    
    for step in range(400):
        sim.step(mode='combined')
        
        if step % 100 == 0:
            amp = sim.amplitude
            # Find maximum amplitude location
            max_idx = np.unravel_index(np.argmax(amp), amp.shape)
            max_r = np.sqrt((max_idx[0] - pulse_pos[0])**2 + (max_idx[1] - pulse_pos[1])**2)
            print(f"  Step {step}: max at r={max_r:.1f}, amp={amp[max_idx]:.3f}")


def analyze_gradient_term():
    """
    Analyze the ∇β·∇ψ term at well boundaries.
    """
    print()
    print("="*70)
    print("MECHANISM 5: GRADIENT TERM AT BOUNDARIES")
    print("="*70)
    print()
    print("Question: Does ∇β·∇ψ push vortices out of wells?")
    print()
    
    size = 100
    
    sim = CombinedCESimulator(size=size, gamma=0.007, beta_inside=0.8, beta_outside=0.25)
    sim.create_beta_wells([(50, 50)], [20])
    
    # Place vortex at well boundary
    boundary_pos = (50, 30)  # At edge of well (radius 20 from center at 50,50)
    
    sim.psi_r[:] = 1.2
    sim.add_vortex(boundary_pos, charge=+1, amplitude=1.2, core_radius=4.0)
    sim.seed_oscillators(amp=0.1)
    
    # Track vortex position
    positions = [boundary_pos]
    
    for step in range(800):
        sim.step(mode='combined')
        
        if step % 50 == 0:
            vortices = sim.detect_all_vortices(amp_threshold=0.4)
            if vortices:
                # Find closest to last position
                last = positions[-1]
                closest = min(vortices, key=lambda v: 
                             (v['position'][0]-last[0])**2 + (v['position'][1]-last[1])**2)
                positions.append(closest['position'])
    
    print("Vortex trajectory at well boundary:")
    for i, pos in enumerate(positions[:10]):
        r_from_center = np.sqrt((pos[0]-50)**2 + (pos[1]-50)**2)
        in_well = "inside" if r_from_center <= 20 else "outside"
        print(f"  t={i*50}: ({pos[0]}, {pos[1]}), r={r_from_center:.1f}, {in_well}")
    
    # Check if vortex moved outward
    if len(positions) > 1:
        initial_r = np.sqrt((positions[0][0]-50)**2 + (positions[0][1]-50)**2)
        final_r = np.sqrt((positions[-1][0]-50)**2 + (positions[-1][1]-50)**2)
        print()
        print(f"  Initial r from center: {initial_r:.1f}")
        print(f"  Final r from center: {final_r:.1f}")
        print(f"  Net drift: {final_r - initial_r:+.1f} (positive = pushed OUT)")


def main():
    print("="*70)
    print("β-SUPPRESSION MECHANISM STUDY")
    print("="*70)
    print()
    print("Goal: Identify WHY β wells suppress topological regeneration")
    print()
    
    measure_remnant_persistence()
    measure_dispersion_rate()
    measure_channel_evolution()
    measure_wave_propagation()
    analyze_gradient_term()
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("Compare results across mechanisms to identify the primary cause:")
    print("1. Remnant persistence: Do remnants decay faster inside wells?")
    print("2. Dispersion rate: Do perturbations spread faster inside wells?")
    print("3. Channel evolution: Does self-selection grow slower inside wells?")
    print("4. Wave propagation: Is effective wave speed significantly different?")
    print("5. Gradient term: Does ∇β·∇ψ push structures out of wells?")


if __name__ == "__main__":
    main()
