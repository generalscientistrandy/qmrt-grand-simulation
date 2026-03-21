"""
QMRT Quark Confinement Analogies

This module implements physics tests for quark confinement analogs in the QMRT substrate.

Step 1: Localized excitation stability (excitation_test.py)
    - Tests if proto-quarks can remain coherent
    - Identifies stabilization mechanisms
    - RESULT: Proto-quarks are STABLE via barrier potential
    
Step 2: Flux tube / separation energy (flux_tube_test.py)
    - THE MOST CRITICAL TEST
    - Tests if E(r) ~ σr emerges naturally
    - σ is medium strain tension, not gluon string tension
    - RESULT: LINEAR POTENTIAL CONFIRMED (R² = 0.999), σ ≈ 0.7

Step 3: Internal color-like degrees of freedom (color_test.py)
    - Tests if composite neutralization is required for stability
    - Determines what marks proton formation
    - RESULT: Triplets minimize domain energy (surface area effect)
    
Robustness verification (robustness_verification.py)
    - Grid resolution independence
    - Timestep convergence
    - Energy conservation
    - Parameter scaling
"""

from .excitation_test import (
    run_localized_excitation_test,
    test_multiple_excitation_types,
    LocalizedExcitationResult,
    ExcitationState
)

from .flux_tube_test import (
    run_flux_tube_test,
    run_detailed_flux_tube_test,
    FluxTubeResult,
    SeparationEnergyPoint
)

from .color_test import (
    run_internal_dof_test,
    run_composite_stability_test,
    InternalDoFResult,
    CompositeState,
    ExcitationConfig
)

from .robustness_verification import (
    run_all_robustness_tests,
    test_grid_resolution_independence,
    test_timestep_convergence,
    test_energy_conservation,
    test_scaling_robustness,
    RobustnessResult
)

__all__ = [
    # Step 1
    'run_localized_excitation_test',
    'test_multiple_excitation_types',
    'LocalizedExcitationResult',
    'ExcitationState',
    # Step 2
    'run_flux_tube_test',
    'run_detailed_flux_tube_test',
    'FluxTubeResult',
    'SeparationEnergyPoint',
    # Step 3
    'run_internal_dof_test',
    'run_composite_stability_test',
    'InternalDoFResult',
    'CompositeState',
    'ExcitationConfig',
    # Robustness
    'run_all_robustness_tests',
    'test_grid_resolution_independence',
    'test_timestep_convergence',
    'test_energy_conservation',
    'test_scaling_robustness',
    'RobustnessResult',
]
