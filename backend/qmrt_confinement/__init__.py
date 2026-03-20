"""
QMRT Quark Confinement Analogies

This module implements physics tests for quark confinement analogs in the QMRT substrate.

Step 1: Localized excitation stability (excitation_test.py)
    - Tests if proto-quarks can remain coherent
    - Identifies stabilization mechanisms
    
Step 2: Flux tube / separation energy (flux_tube_test.py)
    - THE MOST CRITICAL TEST
    - Tests if E(r) ~ σr emerges naturally
    - σ is medium strain tension, not gluon string tension

Step 3: Internal color-like degrees of freedom (color_test.py - TODO)
    - Tests if composite neutralization is required for stability
    - Determines what marks proton formation
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
]
