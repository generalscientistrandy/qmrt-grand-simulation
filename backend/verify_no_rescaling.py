"""
Verify mesoscopic_substrate.py works after removing artificial rescaling.
"""
import sys
sys.path.insert(0, '/app/backend/archive/experiments')

from mesoscopic_substrate import MesoscopicSubstrate

def test_no_artificial_rescaling():
    """Test that substrate works without velocity rescaling band-aids."""
    
    print("=" * 60)
    print("  VERIFICATION: Mesoscopic Substrate Without Rescaling")
    print("=" * 60)
    print()
    
    # Create substrate
    substrate = MesoscopicSubstrate(grid_size=32)
    substrate.initialize_balanced_fluctuations(amplitude=0.1, seed=42)
    
    # Run for a while
    dt = 0.05
    n_steps = 500
    
    print(f"  Running {n_steps} steps with dt={dt}...")
    
    initial_energy = None
    for step in range(n_steps):
        metrics = substrate.evolve_timestep(dt)
        
        if step == 0:
            initial_energy = metrics['total_energy']
        
        if step % 100 == 0:
            drift = metrics['energy_drift'] * 100
            print(f"    Step {step}: E={metrics['total_energy']:.2f}, drift={drift:+.2f}%")
    
    final_energy = metrics['total_energy']
    total_drift = (final_energy - initial_energy) / initial_energy * 100
    
    print()
    print("=" * 60)
    print("  RESULT")
    print("=" * 60)
    print()
    print(f"  Initial Energy: {initial_energy:.2f}")
    print(f"  Final Energy:   {final_energy:.2f}")
    print(f"  Total Drift:    {total_drift:+.2f}%")
    print()
    
    if abs(total_drift) < 5:
        print("  ✓ PASS: System stable without artificial rescaling")
    elif abs(total_drift) < 20:
        print("  ~ ACCEPTABLE: Some drift but no blowup")
    else:
        print("  ! WARNING: Large drift detected")
    
    print()
    return total_drift


if __name__ == "__main__":
    test_no_artificial_rescaling()
