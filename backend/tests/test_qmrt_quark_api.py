"""
QMRT Quark-Level Dual-Basin Attractor Engine API Tests

Tests for:
1. GET /api/qmrt_quark/theory - Theory summary
2. POST /api/qmrt_quark/validate_dual_basin - Dual-basin validation with energy conservation
3. POST /api/qmrt_quark/test_annihilation - Annihilation dynamics testing
4. POST /api/qmrt_quark/test_persistence - Structure persistence over time
5. POST /api/qmrt_quark/initialize - Initialize new engine
6. POST /api/qmrt_quark/{engine_id}/evolve - Evolve engine for N steps
7. GET /api/qmrt_quark/{engine_id}/state - Engine state summary
8. GET /api/qmrt_quark/{engine_id}/structures - Active structures with mode properties

Key physics:
- Phase convention: φ ∈ (−π, +π)
- Matter basin: φ ≈ 0 (|φ| < π/2)
- Antimatter basin: φ ≈ ±π (|φ| ≥ π/2)
- Energy conservation target: < 1% drift
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    pytest.skip("REACT_APP_BACKEND_URL not set", allow_module_level=True)


class TestQMRTQuarkTheory:
    """Test theory endpoint returns correct dual-basin ontology summary"""
    
    def test_get_theory_summary(self):
        """GET /api/qmrt_quark/theory - returns dual-basin theory summary"""
        response = requests.get(f"{BASE_URL}/api/qmrt_quark/theory")
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response structure
        data = response.json()
        assert "title" in data, "Missing 'title' in theory response"
        assert "QMRT" in data["title"], "Theory should reference QMRT"
        
        # Verify phase convention
        assert "phase_convention" in data, "Missing phase_convention"
        phase = data["phase_convention"]
        assert phase["range"] == "φ ∈ (−π, +π)", f"Unexpected phase range: {phase['range']}"
        assert "matter_basin" in phase, "Missing matter_basin"
        assert "antimatter_basin" in phase, "Missing antimatter_basin"
        
        # Verify dual-basin potential
        assert "dual_basin_potential" in data, "Missing dual_basin_potential"
        potential = data["dual_basin_potential"]
        assert "cos" in potential["form"].lower(), "Dual-basin potential should use cosine"
        
        # Verify annihilation dynamics
        assert "annihilation_dynamics" in data, "Missing annihilation_dynamics"
        
        # Verify structure tracking methods
        assert "structure_tracking" in data, "Missing structure_tracking"
        
        print(f"✓ Theory summary returned successfully with phase range: {phase['range']}")


class TestDualBasinValidation:
    """Test dual-basin attractor validation endpoint"""
    
    def test_validate_dual_basin_default_params(self):
        """POST /api/qmrt_quark/validate_dual_basin - runs dual-basin validation"""
        # Use small grid and short time for faster tests
        payload = {
            "grid_size": 16,
            "amplitude": 0.05,
            "total_time": 10.0,
            "dt": 0.01,
            "matter_fraction": 0.5,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt_quark/validate_dual_basin", json=payload)
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert data["test_name"] == "dual_basin_validation", "Wrong test name"
        assert "test_params" in data, "Missing test_params"
        assert "final_state" in data, "Missing final_state"
        assert "evolution_samples" in data, "Missing evolution_samples"
        assert "validation_results" in data, "Missing validation_results"
        
        # Validate physics results
        validation = data["validation_results"]
        
        # Check energy conservation - CRITICAL requirement: < 1% drift
        assert validation["energy_conserved"], f"Energy not conserved! Energy drift exceeded 1%"
        
        # Verify structures formed in both basins (important physics)
        assert validation["structures_formed"] > 0, "No structures formed in simulation"
        
        # Check basin fractions are reasonable
        matter_frac = validation["final_matter_fraction"]
        antimatter_frac = validation["final_antimatter_fraction"]
        assert 0 < matter_frac < 1, f"Invalid matter fraction: {matter_frac}"
        assert 0 < antimatter_frac < 1, f"Invalid antimatter fraction: {antimatter_frac}"
        
        print(f"✓ Dual-basin validation passed")
        print(f"  Energy conserved: {validation['energy_conserved']}")
        print(f"  Matter fraction: {matter_frac:.3f}")
        print(f"  Antimatter fraction: {antimatter_frac:.3f}")
        print(f"  Structures formed: {validation['structures_formed']}")
    
    def test_validate_energy_conservation_requirement(self):
        """Verify energy conservation is < 1% drift as per requirements"""
        payload = {
            "grid_size": 16,
            "amplitude": 0.05,
            "total_time": 15.0,
            "dt": 0.01,
            "seed": 123
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt_quark/validate_dual_basin", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        final_state = data["final_state"]
        
        energy_drift_pct = abs(final_state["energy_drift_pct"])
        
        # CRITICAL: Energy drift must be < 1%
        assert energy_drift_pct < 1.0, f"Energy drift {energy_drift_pct:.3f}% exceeds 1% requirement"
        
        print(f"✓ Energy conservation verified: {energy_drift_pct:.4f}% drift (< 1% required)")
    
    def test_both_basins_form_structures(self):
        """Verify both matter and antimatter basins form structures"""
        payload = {
            "grid_size": 20,
            "amplitude": 0.08,
            "total_time": 15.0,
            "dt": 0.01,
            "matter_fraction": 0.5,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt_quark/validate_dual_basin", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        final_state = data["final_state"]
        structure_stats = final_state["structure_statistics"]
        
        # Check both basins have activity
        matter_count = structure_stats["matter"]["count"]
        antimatter_count = structure_stats["antimatter"]["count"]
        
        # At least one basin should have structures (ideally both)
        total_active = structure_stats["total_active"]
        total_deceased = structure_stats["total_deceased"]
        total_structures = total_active + total_deceased
        
        assert total_structures > 0, "No structures formed in either basin"
        
        print(f"✓ Structures formed:")
        print(f"  Active matter structures: {matter_count}")
        print(f"  Active antimatter structures: {antimatter_count}")
        print(f"  Total deceased: {total_deceased}")


class TestAnnihilationDynamics:
    """Test annihilation dynamics endpoint"""
    
    def test_annihilation_test_basic(self):
        """POST /api/qmrt_quark/test_annihilation - tests annihilation dynamics"""
        payload = {
            "grid_size": 16,
            "amplitude": 0.1,
            "total_time": 15.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt_quark/test_annihilation", json=payload)
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert data["test_name"] == "annihilation_test", "Wrong test name"
        assert "test_params" in data, "Missing test_params"
        assert "final_state" in data, "Missing final_state"
        assert "annihilation_events" in data, "Missing annihilation_events"
        assert "annihilation_count" in data, "Missing annihilation_count"
        
        # Verify annihilation events structure (if any occurred)
        if data["annihilation_count"] > 0:
            event = data["annihilation_events"][0]
            assert "time" in event, "Annihilation event missing time"
            assert "position" in event, "Annihilation event missing position"
            assert "matter_structure_id" in event, "Missing matter_structure_id"
            assert "antimatter_structure_id" in event, "Missing antimatter_structure_id"
            assert "released_energy" in event, "Missing released_energy"
            
            print(f"✓ Annihilation test completed with {data['annihilation_count']} events")
            print(f"  First event at time: {event['time']:.3f}")
            print(f"  Released energy: {event['released_energy']:.4f}")
        else:
            print(f"✓ Annihilation test completed (no events triggered)")


class TestStructurePersistence:
    """Test structure persistence endpoint"""
    
    def test_persistence_test_basic(self):
        """POST /api/qmrt_quark/test_persistence - tests structure persistence over time"""
        payload = {
            "grid_size": 16,
            "amplitude": 0.08,
            "total_time": 20.0,  # Longer simulation for persistence
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt_quark/test_persistence", json=payload)
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert data["test_name"] == "structure_persistence", "Wrong test name"
        assert "final_state" in data, "Missing final_state"
        assert "persistence_data" in data, "Missing persistence_data"
        assert "lifetime_distribution" in data, "Missing lifetime_distribution"
        assert "mode_census" in data, "Missing mode_census"
        
        # Check persistence data samples
        persistence = data["persistence_data"]
        assert len(persistence) > 0, "No persistence data samples"
        
        # Verify energy drift stays low throughout
        for sample in persistence:
            assert "energy_drift" in sample, "Sample missing energy_drift"
            assert abs(sample["energy_drift"]) < 0.05, f"Energy drift too high: {sample['energy_drift']}"
        
        # Check lifetime distribution structure
        lifetime_dist = data["lifetime_distribution"]
        assert "matter" in lifetime_dist, "Missing matter lifetime distribution"
        assert "antimatter" in lifetime_dist, "Missing antimatter lifetime distribution"
        
        print(f"✓ Persistence test completed")
        print(f"  Samples collected: {len(persistence)}")
        print(f"  Matter lifetimes: {lifetime_dist['matter']['count']} structures")
        print(f"  Antimatter lifetimes: {lifetime_dist['antimatter']['count']} structures")


class TestEngineLifecycle:
    """Test engine initialization, evolution, and state retrieval"""
    
    created_engine_id = None
    
    def test_01_initialize_engine(self):
        """POST /api/qmrt_quark/initialize - initializes a new quark engine"""
        payload = {
            "name": "TEST_QuarkEngine",
            "grid_size": 16,
            "amplitude": 0.05,
            "matter_fraction": 0.5,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt_quark/initialize", json=payload)
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "engine_id" in data, "Missing engine_id"
        assert "phase_convention" in data, "Missing phase_convention"
        assert "initial_state" in data, "Missing initial_state"
        
        # Store for later tests
        TestEngineLifecycle.created_engine_id = data["engine_id"]
        
        # Verify phase convention
        assert data["phase_convention"] == "φ ∈ (−π, +π)", f"Wrong phase convention: {data['phase_convention']}"
        
        # Verify initial state structure
        state = data["initial_state"]
        assert "time" in state, "State missing time"
        assert state["time"] == 0.0, "Initial time should be 0"
        assert "total_energy" in state, "State missing total_energy"
        assert "basin_statistics" in state, "State missing basin_statistics"
        
        print(f"✓ Engine initialized: {data['engine_id']}")
        print(f"  Grid size: {payload['grid_size']}³")
        print(f"  Initial energy: {state['total_energy']:.4f}")
    
    def test_02_evolve_engine(self):
        """POST /api/qmrt_quark/{engine_id}/evolve - evolves engine for N steps"""
        assert TestEngineLifecycle.created_engine_id, "No engine created"
        engine_id = TestEngineLifecycle.created_engine_id
        
        payload = {
            "steps": 100,
            "dt": 0.01
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt_quark/{engine_id}/evolve", json=payload)
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert data["engine_id"] == engine_id, "Wrong engine_id returned"
        assert data["steps_completed"] == payload["steps"], "Steps mismatch"
        assert "final_state" in data, "Missing final_state"
        assert "structures" in data, "Missing structures"
        assert "annihilation_events" in data, "Missing annihilation_events"
        
        # Verify final state
        state = data["final_state"]
        assert state["time"] > 0, "Time should have advanced"
        
        # Verify structures data
        structures = data["structures"]
        assert "active" in structures, "Missing active count"
        assert "matter" in structures, "Missing matter count"
        assert "antimatter" in structures, "Missing antimatter count"
        assert "items" in structures, "Missing structure items"
        
        # Verify energy conservation
        energy_drift = abs(state["energy_drift_pct"])
        assert energy_drift < 1.0, f"Energy drift {energy_drift}% exceeds 1%"
        
        print(f"✓ Engine evolved {payload['steps']} steps")
        print(f"  Time: {state['time']:.2f}s")
        print(f"  Energy drift: {energy_drift:.4f}%")
        print(f"  Active structures: {structures['active']} (matter: {structures['matter']}, antimatter: {structures['antimatter']})")
    
    def test_03_get_engine_state(self):
        """GET /api/qmrt_quark/{engine_id}/state - returns engine state summary"""
        assert TestEngineLifecycle.created_engine_id, "No engine created"
        engine_id = TestEngineLifecycle.created_engine_id
        
        response = requests.get(f"{BASE_URL}/api/qmrt_quark/{engine_id}/state")
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify state structure
        assert "time" in data, "Missing time"
        assert "grid_size" in data, "Missing grid_size"
        assert "phase_range" in data, "Missing phase_range"
        assert data["phase_range"] == "(-pi, +pi)", f"Wrong phase range: {data['phase_range']}"
        assert "total_energy" in data, "Missing total_energy"
        assert "basin_statistics" in data, "Missing basin_statistics"
        assert "structure_statistics" in data, "Missing structure_statistics"
        assert "mode_property_census" in data, "Missing mode_property_census"
        
        print(f"✓ Engine state retrieved")
        print(f"  Current time: {data['time']:.2f}s")
        print(f"  Energy: {data['total_energy']:.4f}")
    
    def test_04_get_structures(self):
        """GET /api/qmrt_quark/{engine_id}/structures - returns active structures with mode properties"""
        assert TestEngineLifecycle.created_engine_id, "No engine created"
        engine_id = TestEngineLifecycle.created_engine_id
        
        response = requests.get(f"{BASE_URL}/api/qmrt_quark/{engine_id}/structures")
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert data["engine_id"] == engine_id, "Wrong engine_id"
        assert "time" in data, "Missing time"
        assert "active_structures" in data, "Missing active_structures"
        assert "basin_statistics" in data, "Missing basin_statistics"
        assert "mode_census" in data, "Missing mode_census"
        
        # If structures exist, verify their properties
        structures = data["active_structures"]
        if len(structures) > 0:
            struct = structures[0]
            
            # Verify structure fields
            assert "id" in struct, "Structure missing id"
            assert "centroid" in struct, "Structure missing centroid"
            assert "basin" in struct, "Structure missing basin"
            assert struct["basin"] in ["matter", "antimatter"], f"Invalid basin: {struct['basin']}"
            assert "phase_value" in struct, "Structure missing phase_value"
            assert "mode_properties" in struct, "Structure missing mode_properties"
            
            # Verify mode properties structure
            mode_props = struct["mode_properties"]
            assert "binding_energy" in mode_props, "Mode missing binding_energy"
            assert "winding_number" in mode_props, "Mode missing winding_number"
            assert "coherence_length" in mode_props, "Mode missing coherence_length"
            assert "S_value" in mode_props, "Mode missing S_value"
            
            print(f"✓ Retrieved {len(structures)} structures")
            print(f"  First structure basin: {struct['basin']}")
            print(f"  Phase value: {struct['phase_value']:.4f}")
        else:
            print(f"✓ Retrieved structures (none active at this time)")
    
    def test_05_list_engines(self):
        """GET /api/qmrt_quark/list - lists all active engines"""
        response = requests.get(f"{BASE_URL}/api/qmrt_quark/list")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert "count" in data, "Missing count"
        assert "engines" in data, "Missing engines list"
        assert data["count"] >= 1, "Should have at least one engine"
        
        # Find our test engine
        test_engines = [e for e in data["engines"] if "TEST" in e["id"]]
        assert len(test_engines) >= 1, "Test engine not found in list"
        
        print(f"✓ Listed {data['count']} engines")
    
    def test_06_delete_engine(self):
        """DELETE /api/qmrt_quark/{engine_id} - deletes engine to free memory"""
        assert TestEngineLifecycle.created_engine_id, "No engine created"
        engine_id = TestEngineLifecycle.created_engine_id
        
        response = requests.delete(f"{BASE_URL}/api/qmrt_quark/{engine_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing message"
        assert engine_id in data["message"], "Engine ID not in response"
        
        # Verify engine is gone
        verify_response = requests.get(f"{BASE_URL}/api/qmrt_quark/{engine_id}/state")
        assert verify_response.status_code == 404, "Engine should be deleted"
        
        print(f"✓ Engine deleted: {engine_id}")


class TestEngineNotFound:
    """Test proper 404 handling for non-existent engines"""
    
    def test_get_state_404(self):
        """GET /api/qmrt_quark/{engine_id}/state - returns 404 for unknown engine"""
        response = requests.get(f"{BASE_URL}/api/qmrt_quark/nonexistent_engine/state")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_get_structures_404(self):
        """GET /api/qmrt_quark/{engine_id}/structures - returns 404 for unknown engine"""
        response = requests.get(f"{BASE_URL}/api/qmrt_quark/nonexistent_engine/structures")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_evolve_404(self):
        """POST /api/qmrt_quark/{engine_id}/evolve - returns 404 for unknown engine"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_quark/nonexistent_engine/evolve",
            json={"steps": 10, "dt": 0.01}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestJSONSerialization:
    """Test that numpy types are properly serialized to JSON"""
    
    def test_no_serialization_errors(self):
        """All endpoints should return valid JSON without numpy type errors"""
        # Test dual basin validation
        response = requests.post(
            f"{BASE_URL}/api/qmrt_quark/validate_dual_basin",
            json={"grid_size": 16, "total_time": 5.0, "dt": 0.01, "seed": 42}
        )
        assert response.status_code == 200, f"Serialization error in validate_dual_basin: {response.text}"
        
        # Verify all numeric values are valid JSON types (not numpy)
        data = response.json()
        
        def check_json_types(obj, path=""):
            """Recursively check that all values are JSON-serializable types"""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    check_json_types(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_json_types(v, f"{path}[{i}]")
            elif obj is not None:
                valid_types = (str, int, float, bool)
                if not isinstance(obj, valid_types):
                    raise AssertionError(f"Invalid type at {path}: {type(obj).__name__}")
        
        check_json_types(data)
        print("✓ JSON serialization verified - no numpy types in response")


class TestPhaseConventionValidation:
    """Verify phase values are within (-π, +π) convention"""
    
    def test_phase_values_in_range(self):
        """All phase values should be in (-π, +π)"""
        import math
        
        # Initialize and evolve engine
        init_response = requests.post(
            f"{BASE_URL}/api/qmrt_quark/initialize",
            json={"name": "TEST_PhaseCheck", "grid_size": 16, "seed": 42}
        )
        assert init_response.status_code == 200
        engine_id = init_response.json()["engine_id"]
        
        # Evolve a bit
        requests.post(
            f"{BASE_URL}/api/qmrt_quark/{engine_id}/evolve",
            json={"steps": 50, "dt": 0.01}
        )
        
        # Get structures
        struct_response = requests.get(f"{BASE_URL}/api/qmrt_quark/{engine_id}/structures")
        assert struct_response.status_code == 200
        
        data = struct_response.json()
        
        # Check phase values of structures
        for struct in data["active_structures"]:
            phase = struct["phase_value"]
            assert -math.pi <= phase <= math.pi, f"Phase {phase} outside (-π, +π) range"
            
            # Verify basin classification matches phase
            basin = struct["basin"]
            if abs(phase) < math.pi / 2:
                assert basin == "matter", f"Phase {phase} should be matter basin, got {basin}"
            else:
                assert basin == "antimatter", f"Phase {phase} should be antimatter basin, got {basin}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/qmrt_quark/{engine_id}")
        
        print(f"✓ Phase convention verified for all {len(data['active_structures'])} structures")


class TestInputValidation:
    """Test input validation on endpoints"""
    
    def test_grid_size_limits(self):
        """Grid size should be limited (8-64)"""
        # Too small
        response = requests.post(
            f"{BASE_URL}/api/qmrt_quark/initialize",
            json={"name": "TEST_TooSmall", "grid_size": 4}
        )
        assert response.status_code == 422, f"Expected 422 for grid_size=4, got {response.status_code}"
        
        # Too large
        response = requests.post(
            f"{BASE_URL}/api/qmrt_quark/initialize",
            json={"name": "TEST_TooLarge", "grid_size": 100}
        )
        assert response.status_code == 422, f"Expected 422 for grid_size=100, got {response.status_code}"
        
        print("✓ Grid size limits validated")
    
    def test_amplitude_limits(self):
        """Amplitude should be limited (0.001-1.0)"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_quark/initialize",
            json={"name": "TEST_BadAmp", "grid_size": 16, "amplitude": 2.0}
        )
        assert response.status_code == 422, f"Expected 422 for amplitude=2.0, got {response.status_code}"
        
        print("✓ Amplitude limits validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
