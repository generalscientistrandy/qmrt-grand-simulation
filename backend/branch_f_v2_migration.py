"""
Branch F v2: Migration Dynamics Test
=====================================

Question: Do vortices nucleate in high-coupling regions and then migrate to other zones?
Or do they simply stay where they're born?

This test tracks individual vortex trajectories to measure:
1. Birth zone
2. Death zone  
3. Net migration (zone change)
"""

import numpy as np
from branch_f_v2 import BranchFv2Simulator
from typing import Dict, List, Tuple


def test_migration_dynamics(steps: int = 8000) -> Dict:
    """Track individual vortex trajectories to measure migration."""
    
    sim = BranchFv2Simulator(
        size=100, gamma=0.007,
        coupling_center=0.8, coupling_edge=0.2,
        transition_width=20.0
    )
    
    # Seed
    center = sim.size // 2
    np.random.seed(42)
    sim.psi_r[:] = 1.2
    sim.psi_i[:] = 0.0
    
    for i, pos in enumerate([(center-5, center), (center+5, center), (center, center-8), (center, center+8)]):
        charge = 1 if i % 2 == 0 else -1
        x, y = np.meshgrid(np.arange(sim.size), np.arange(sim.size), indexing='ij')
        r = np.sqrt((x - pos[0])**2 + (y - pos[1])**2) + 0.1
        theta = np.arctan2(y - pos[1], x - pos[0])
        amp = 1.2 * np.tanh(r / 4.0)
        psi = sim.psi_r + 1j * sim.psi_i
        psi *= (amp / (np.abs(psi) + 0.01)) * np.exp(1j * charge * theta)
        sim.psi_r = np.real(psi)
        sim.psi_i = np.imag(psi)
    
    sim.psi_r += 0.05 * np.random.randn(100, 100)
    sim.psi_i += 0.05 * np.random.randn(100, 100)
    
    # Track vortices
    vortex_tracks = {}  # id -> {'birth_zone': str, 'birth_step': int, 'positions': [...], 'zones': [...]}
    next_id = 0
    prev_vortices = {}  # position -> id
    
    for step in range(steps):
        sim.step()
        
        if step % 25 == 0:
            vortices = sim.detect_vortices()
            current_positions = {v['position']: v for v in vortices}
            
            # Match vortices (simple nearest-neighbor)
            new_prev = {}
            matched_ids = set()
            
            for pos, v in current_positions.items():
                # Find nearest previous vortex
                best_id = None
                best_dist = 15
                
                for prev_pos, prev_id in prev_vortices.items():
                    if prev_id in matched_ids:
                        continue
                    dist = np.sqrt((pos[0] - prev_pos[0])**2 + (pos[1] - prev_pos[1])**2)
                    if dist < best_dist:
                        best_dist = dist
                        best_id = prev_id
                
                if best_id is not None:
                    # Continuation
                    matched_ids.add(best_id)
                    new_prev[pos] = best_id
                    vortex_tracks[best_id]['positions'].append(pos)
                    vortex_tracks[best_id]['zones'].append(v['zone'])
                else:
                    # New vortex
                    vid = next_id
                    next_id += 1
                    new_prev[pos] = vid
                    vortex_tracks[vid] = {
                        'birth_zone': v['zone'],
                        'birth_step': step,
                        'positions': [pos],
                        'zones': [v['zone']]
                    }
            
            # Mark deaths
            for prev_pos, prev_id in prev_vortices.items():
                if prev_id not in matched_ids:
                    vortex_tracks[prev_id]['death_step'] = step
                    vortex_tracks[prev_id]['death_zone'] = vortex_tracks[prev_id]['zones'][-1]
            
            prev_vortices = new_prev
    
    return vortex_tracks


def analyze_migration(tracks: Dict):
    """Analyze migration patterns."""
    print("="*70)
    print("MIGRATION DYNAMICS ANALYSIS")
    print("="*70)
    print()
    
    # Only analyze completed tracks (with death)
    completed = {k: v for k, v in tracks.items() if 'death_zone' in v}
    
    print(f"Total vortex tracks: {len(tracks)}")
    print(f"Completed (born and died): {len(completed)}")
    print()
    
    # Transition matrix: birth_zone -> death_zone
    zones = ['interior', 'transition', 'periphery']
    transitions = {bz: {dz: 0 for dz in zones} for bz in zones}
    
    for vid, track in completed.items():
        bz = track['birth_zone']
        dz = track['death_zone']
        transitions[bz][dz] += 1
    
    print("Birth → Death transition matrix:")
    print("           | Death Zone")
    print("Birth Zone | Interior | Transit | Periph | Total")
    print("-" * 55)
    
    for bz in zones:
        total = sum(transitions[bz].values())
        row = f"{bz:10s} |"
        for dz in zones:
            row += f"  {transitions[bz][dz]:5d}  |"
        row += f"  {total:5d}"
        print(row)
    
    print()
    
    # Migration analysis
    stayed_same = sum(transitions[z][z] for z in zones)
    migrated_outward = (transitions['interior']['transition'] + 
                        transitions['interior']['periphery'] +
                        transitions['transition']['periphery'])
    migrated_inward = (transitions['periphery']['transition'] +
                       transitions['periphery']['interior'] +
                       transitions['transition']['interior'])
    
    total_completed = len(completed)
    
    print("Migration summary:")
    print(f"  Stayed in birth zone: {stayed_same} ({100*stayed_same/total_completed:.1f}%)")
    print(f"  Migrated outward (toward low-coupling): {migrated_outward} ({100*migrated_outward/total_completed:.1f}%)")
    print(f"  Migrated inward (toward high-coupling): {migrated_inward} ({100*migrated_inward/total_completed:.1f}%)")
    print()
    
    # Lifetime by birth zone
    lifetimes_by_zone = {z: [] for z in zones}
    for vid, track in completed.items():
        lifetime = track['death_step'] - track['birth_step']
        lifetimes_by_zone[track['birth_zone']].append(lifetime)
    
    print("Lifetime by birth zone:")
    for z in zones:
        if lifetimes_by_zone[z]:
            mean = np.mean(lifetimes_by_zone[z])
            median = np.median(lifetimes_by_zone[z])
            print(f"  {z:10s}: mean={mean:.0f}, median={median:.0f}, n={len(lifetimes_by_zone[z])}")
        else:
            print(f"  {z:10s}: no data")
    
    print()
    
    # Net migration per vortex
    radial_changes = []
    for vid, track in completed.items():
        if len(track['positions']) >= 2:
            start_pos = track['positions'][0]
            end_pos = track['positions'][-1]
            
            center = 50
            r_start = np.sqrt((start_pos[0] - center)**2 + (start_pos[1] - center)**2)
            r_end = np.sqrt((end_pos[0] - center)**2 + (end_pos[1] - center)**2)
            
            radial_changes.append(r_end - r_start)
    
    if radial_changes:
        mean_radial = np.mean(radial_changes)
        print(f"Mean radial displacement: {mean_radial:+.2f} (positive = outward)")
        
        outward = sum(1 for dr in radial_changes if dr > 2)
        inward = sum(1 for dr in radial_changes if dr < -2)
        stationary = len(radial_changes) - outward - inward
        
        print(f"  Moved outward (>2): {outward} ({100*outward/len(radial_changes):.1f}%)")
        print(f"  Stayed (~0): {stationary} ({100*stationary/len(radial_changes):.1f}%)")
        print(f"  Moved inward (<-2): {inward} ({100*inward/len(radial_changes):.1f}%)")
    
    return {
        'transitions': transitions,
        'stayed_same': stayed_same,
        'migrated_outward': migrated_outward,
        'migrated_inward': migrated_inward,
        'lifetimes_by_zone': {z: np.mean(v) if v else 0 for z, v in lifetimes_by_zone.items()}
    }


def main():
    print("="*70)
    print("BRANCH F v2: MIGRATION DYNAMICS TEST")
    print("="*70)
    print()
    print("Question: Do vortices migrate between zones?")
    print()
    
    tracks = test_migration_dynamics(steps=8000)
    analysis = analyze_migration(tracks)
    
    print()
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()
    
    total = analysis['stayed_same'] + analysis['migrated_outward'] + analysis['migrated_inward']
    
    if analysis['migrated_outward'] > analysis['stayed_same'] * 0.3:
        print("✓ Significant migration exists (outward bias)")
        print("  Vortices born in high-coupling interior DO migrate outward")
    elif analysis['migrated_inward'] > analysis['stayed_same'] * 0.3:
        print("✓ Significant migration exists (inward bias)")
    else:
        print("~ Vortices mostly stay in their birth zone")
        print("  The system is a single favored region, not regeneration→stabilization")


if __name__ == "__main__":
    main()
