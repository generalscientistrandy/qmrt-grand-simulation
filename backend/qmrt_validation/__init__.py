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

from .scaling_test import (
    ScalingMetrics,
    ScalingConvergenceResult,
    run_scaling_convergence_test,
    run_scaling_at_resolution
)

from .entropy_test import (
    EntropyTrajectory,
    EntropyProductionResult,
    run_entropy_production_test,
    compute_frequency_entropy
)

from .phase_diagram import (
    PhaseDiagramResult,
    HysteresisPoint,
    InteractionRegimePoint,
    run_phase_diagram_refinement,
    run_hysteresis_scan,
    run_long_time_plateau_test,
    run_interaction_regime_map
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
    'run_single_collision_test',
    # Scaling
    'ScalingMetrics',
    'ScalingConvergenceResult',
    'run_scaling_convergence_test',
    'run_scaling_at_resolution',
    # Entropy
    'EntropyTrajectory',
    'EntropyProductionResult',
    'run_entropy_production_test',
    'compute_frequency_entropy',
    # Phase Diagram
    'PhaseDiagramResult',
    'HysteresisPoint',
    'InteractionRegimePoint',
    'run_phase_diagram_refinement',
    'run_hysteresis_scan',
    'run_long_time_plateau_test',
    'run_interaction_regime_map'
]
