"""
QMRT Validation Suite

Modular validation framework for QMRT frequency-domain physics.

Scientific order (strict dependency):
1. eigenmode_test.py     - Prove basin = true attractor
2. interaction_test.py   - Basin interaction/scattering law
3. scaling_test.py       - Resolution independence (only after 1,2)
4. entropy_test.py       - Thermodynamics (only after 1,2,3)

validation_orchestrator.py - Coordinates tests with dependency checking
"""

from .eigenmode_test import (
    EigenmodeResult,
    ComprehensiveStabilityResult,
    BasinStabilityClass,
    run_eigenmode_stability_test,
    run_comprehensive_stability_test,
    run_multi_perturbation_test,
    classify_basin_stability
)

from .interaction_test import (
    CollisionOutcome,
    CollisionEvent,
    InteractionResult,
    run_interaction_classification,
    run_single_collision_test
)

__all__ = [
    # Eigenmode
    'EigenmodeResult',
    'ComprehensiveStabilityResult',
    'BasinStabilityClass',
    'run_eigenmode_stability_test',
    'run_comprehensive_stability_test',
    'run_multi_perturbation_test',
    'classify_basin_stability',
    # Interaction
    'CollisionOutcome',
    'CollisionEvent',
    'InteractionResult',
    'run_interaction_classification',
    'run_single_collision_test'
]
