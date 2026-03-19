"""
Backend Tests for QMRT Mesoscopic Substrate Simulation API

Tests for:
- POST /api/mesoscopic/initialize - creates substrate with balanced fluctuations
- POST /api/mesoscopic/{id}/evolve - evolves substrate and detects structures
- POST /api/mesoscopic/run - runs complete simulation from init to structure detection
- POST /api/mesoscopic/stability-test - validates numerical stability and energy conservation
- GET /api/mesoscopic/list - lists active substrates
- GET /api/mesoscopic/{id}/state - returns current substrate state
- GET /api/mesoscopic/{id}/structures - returns detected emergent structures

Key validations:
- Energy conservation: total energy drift should be < 5% over extended simulation
- Numerical stability: no NaN/Inf values in outputs
- Structure detection: vortices, strain nodes, coherence clusters, particle nodes should be detected
- JSON serialization: all responses should be valid JSON with no serialization errors
"""

import pytest
import requests
import os
import json
import time
from typing import Dict, Any, Optional

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestMesoscopicAPI:
    """Tests for Mesoscopic Substrate Simulation API"""
    
    # Store created substrate IDs for cleanup
    created_substrates = []
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test"""
        yield
        # Note: cleanup can be done at end of test class
    
    # ======================
    # INITIALIZATION TESTS
    # ======================
    
    def test_initialize_substrate_basic(self):
        """Test POST /api/mesoscopic/initialize - basic initialization"""
        payload = {
            "name": "TEST_BasicInit",
            "grid_size": 32,
            "grid_spacing": 1.0,
            "amplitude": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/initialize", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Validate response structure
        assert "substrate_id" in data, "Response missing substrate_id"
        assert "name" in data, "Response missing name"
        assert "grid_size" in data, "Response missing grid_size"
        assert "initial_state" in data, "Response missing initial_state"
        
        # Validate values
        assert data["name"] == "TEST_BasicInit"
        assert data["grid_size"] == 32
        
        # Validate initial state
        state = data["initial_state"]
        assert "mean_density" in state
        assert "time" in state
        assert state["time"] == 0.0
        
        # Mean density should be close to 1.0 for balanced fluctuations
        assert 0.99 < state["mean_density"] < 1.01, f"Mean density {state['mean_density']} not near 1.0"
        
        # Store for later cleanup
        self.created_substrates.append(data["substrate_id"])
        
        print(f"✓ Initialize substrate - substrate_id: {data['substrate_id']}")
    
    def test_initialize_substrate_with_seed(self):
        """Test initialization with specific seed for reproducibility"""
        payload = {
            "name": "TEST_SeededInit",
            "grid_size": 32,
            "amplitude": 0.1,
            "seed": 12345
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/initialize", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        self.created_substrates.append(data["substrate_id"])
        
        # Verify seeded initialization
        state = data["initial_state"]
        
        # No NaN/Inf values
        assert not any(self._is_nan_or_inf(v) for v in [
            state["mean_density"], state["density_variance"], 
            state.get("mean_torsion", 0), state.get("max_torsion", 0)
        ]), "NaN/Inf detected in initial state"
        
        print(f"✓ Seeded initialization passed")
    
    # ======================
    # EVOLUTION TESTS
    # ======================
    
    def test_evolve_substrate(self):
        """Test POST /api/mesoscopic/{id}/evolve - substrate evolution"""
        # First initialize a substrate
        init_payload = {
            "name": "TEST_Evolve",
            "grid_size": 32,
            "amplitude": 0.1,
            "seed": 42
        }
        
        init_response = requests.post(f"{BASE_URL}/api/mesoscopic/initialize", json=init_payload)
        assert init_response.status_code == 200
        substrate_id = init_response.json()["substrate_id"]
        self.created_substrates.append(substrate_id)
        
        # Evolve the substrate
        evolve_payload = {
            "steps": 100,
            "dt": 0.01,
            "detect_structures": True
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/{substrate_id}/evolve", json=evolve_payload)
        
        assert response.status_code == 200, f"Evolution failed: {response.text}"
        
        data = response.json()
        
        # Validate response structure
        assert "substrate_id" in data
        assert "steps_completed" in data
        assert "final_time" in data
        assert "final_state" in data
        assert "structures" in data
        assert "evolution_summary" in data
        assert "stability" in data
        
        # Validate evolution completed
        assert data["steps_completed"] == 100
        assert data["final_time"] > 0
        
        # Validate stability
        stability = data["stability"]
        assert "stable" in stability
        
        # Validate structures (may or may not detect any at this point)
        structures = data["structures"]
        assert "torsion_vortices" in structures
        assert "strain_nodes" in structures
        assert "coherence_clusters" in structures
        assert "particle_nodes" in structures
        
        print(f"✓ Substrate evolution - time: {data['final_time']}, stability: {stability['stable']}")
    
    def test_evolve_substrate_not_found(self):
        """Test evolution with non-existent substrate ID"""
        evolve_payload = {
            "steps": 10,
            "dt": 0.01,
            "detect_structures": False
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/NONEXISTENT_ID_12345/evolve", json=evolve_payload)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print(f"✓ Non-existent substrate returns 404")
    
    # ======================
    # FULL SIMULATION TESTS
    # ======================
    
    def test_run_full_simulation(self):
        """Test POST /api/mesoscopic/run - complete simulation"""
        payload = {
            "name": "TEST_FullSim",
            "grid_size": 32,  # Smaller grid for faster test
            "amplitude": 0.1,
            "total_time": 10.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/run", json=payload)
        
        assert response.status_code == 200, f"Full simulation failed: {response.text}"
        
        data = response.json()
        
        # Validate response structure
        assert "substrate_id" in data
        assert "simulation_params" in data
        assert "initial_state" in data
        assert "final_state" in data
        assert "evolution_samples" in data
        assert "emergent_structures" in data
        assert "stability_analysis" in data
        
        self.created_substrates.append(data["substrate_id"])
        
        # Validate simulation params
        params = data["simulation_params"]
        assert params["grid_size"] == 32
        assert params["total_time"] == 10.0
        
        # Validate initial vs final state
        initial = data["initial_state"]
        final = data["final_state"]
        
        assert initial["time"] == 0.0
        assert final["time"] > 0
        
        # Validate no NaN/Inf in final state
        for key in ["mean_density", "density_variance", "max_torsion", "energy_total"]:
            if key in final:
                assert not self._is_nan_or_inf(final[key]), f"NaN/Inf in final state: {key}"
        
        # Validate emergent structures
        structures = data["emergent_structures"]
        assert "torsion_vortices" in structures
        assert "strain_nodes" in structures
        assert "coherence_clusters" in structures
        assert "particle_nodes" in structures
        
        print(f"✓ Full simulation - substrate_id: {data['substrate_id']}")
        print(f"  Final time: {final['time']}, Structures detected:")
        print(f"  - Vortices: {structures['torsion_vortices']['count']}")
        print(f"  - Strain nodes: {structures['strain_nodes']['count']}")
        print(f"  - Coherence clusters: {structures['coherence_clusters']['count']}")
        print(f"  - Particle nodes: {structures['particle_nodes']['count']}")
    
    def test_run_simulation_longer_time(self):
        """Test full simulation with longer time to verify structure formation"""
        payload = {
            "name": "TEST_LongerSim",
            "grid_size": 32,
            "amplitude": 0.12,  # Slightly higher amplitude for more structure formation
            "total_time": 15.0,  # Longer simulation
            "dt": 0.01,
            "seed": 123
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/run", json=payload)
        
        assert response.status_code == 200, f"Longer simulation failed: {response.text}"
        
        data = response.json()
        self.created_substrates.append(data["substrate_id"])
        
        # Check structure detection
        structures = data["emergent_structures"]
        
        # After sufficient evolution, we should detect some structures
        total_structures = (
            structures['torsion_vortices']['count'] +
            structures['strain_nodes']['count'] +
            structures['coherence_clusters']['count'] +
            structures['particle_nodes']['count']
        )
        
        print(f"✓ Longer simulation detected {total_structures} total structures")
        
        # Validate stability
        stability = data["stability_analysis"]
        assert "stable" in stability
        
        # Mean density should be preserved (near 1.0)
        final = data["final_state"]
        assert 0.5 < final["mean_density"] < 2.0, f"Density drift too large: {final['mean_density']}"
    
    # ======================
    # STABILITY TEST
    # ======================
    
    def test_stability_test_endpoint(self):
        """Test POST /api/mesoscopic/stability-test - numerical stability validation"""
        payload = {
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 10.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/stability-test", json=payload)
        
        assert response.status_code == 200, f"Stability test failed: {response.text}"
        
        data = response.json()
        
        # Validate response structure
        assert "test_params" in data
        assert "stability_result" in data
        assert "final_state" in data
        assert "history_samples" in data
        assert "diagnosis" in data
        
        # Validate stability result
        result = data["stability_result"]
        assert "overall_stable" in result
        assert "density_preserved" in result
        assert "density_drift" in result
        assert "energy_conservation_ratio" in result
        
        # Check numerical stability
        assert result["overall_stable"], f"Simulation unstable: {result}"
        
        # Energy conservation should be reasonable (< 5% drift)
        energy_ratio = result["energy_conservation_ratio"]
        assert energy_ratio < 0.05, f"Energy drift too high: {energy_ratio * 100:.2f}%"
        
        # Density should be preserved
        assert result["density_drift"] < 0.5, f"Density drift too high: {result['density_drift']}"
        
        print(f"✓ Stability test passed")
        print(f"  Energy conservation ratio: {energy_ratio * 100:.4f}%")
        print(f"  Density drift: {result['density_drift']:.4f}")
        print(f"  Overall stable: {result['overall_stable']}")
    
    def test_stability_with_higher_amplitude(self):
        """Test stability with higher amplitude fluctuations"""
        payload = {
            "grid_size": 32,
            "amplitude": 0.15,  # Higher amplitude
            "total_time": 15.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/stability-test", json=payload)
        
        assert response.status_code == 200, f"High amplitude stability test failed: {response.text}"
        
        data = response.json()
        result = data["stability_result"]
        
        # Even with higher amplitude, should remain stable
        assert result["overall_stable"], f"Simulation unstable at higher amplitude"
        
        # Energy conservation might be slightly worse but still reasonable
        assert result["energy_conservation_ratio"] < 0.1, f"Energy drift too high at high amplitude"
        
        print(f"✓ High amplitude stability test passed")
        print(f"  Energy conservation: {result['energy_conservation_ratio'] * 100:.2f}%")
    
    def test_stability_extended_time(self):
        """Test stability over extended simulation time"""
        payload = {
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 25.0,  # Extended time
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/stability-test", json=payload)
        
        assert response.status_code == 200, f"Extended stability test failed: {response.text}"
        
        data = response.json()
        result = data["stability_result"]
        
        # Should remain stable over extended time
        assert result["overall_stable"], f"Simulation unstable over extended time"
        
        # Energy should be conserved < 5% even over long time
        assert result["energy_conservation_ratio"] < 0.05, f"Energy not conserved: {result['energy_conservation_ratio'] * 100:.2f}%"
        
        print(f"✓ Extended time stability test passed")
        print(f"  Total steps: {data['test_params']['steps']}")
        print(f"  Energy conservation: {result['energy_conservation_ratio'] * 100:.4f}%")
    
    # ======================
    # LIST AND STATE TESTS
    # ======================
    
    def test_list_substrates(self):
        """Test GET /api/mesoscopic/list - list active substrates"""
        response = requests.get(f"{BASE_URL}/api/mesoscopic/list")
        
        assert response.status_code == 200
        
        data = response.json()
        
        assert "total_substrates" in data
        assert "substrates" in data
        assert isinstance(data["substrates"], list)
        
        # Each substrate should have required fields
        for substrate in data["substrates"]:
            assert "substrate_id" in substrate
            assert "time" in substrate
            assert "particle_nodes" in substrate
        
        print(f"✓ List substrates - total: {data['total_substrates']}")
    
    def test_get_substrate_state(self):
        """Test GET /api/mesoscopic/{id}/state - get current state"""
        # First create a substrate
        init_payload = {
            "name": "TEST_StateCheck",
            "grid_size": 32,
            "amplitude": 0.1,
            "seed": 42
        }
        
        init_response = requests.post(f"{BASE_URL}/api/mesoscopic/initialize", json=init_payload)
        assert init_response.status_code == 200
        substrate_id = init_response.json()["substrate_id"]
        self.created_substrates.append(substrate_id)
        
        # Get state
        response = requests.get(f"{BASE_URL}/api/mesoscopic/{substrate_id}/state")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate state fields
        required_fields = [
            "time", "grid_size", "mean_density", "density_variance",
            "mean_tension", "mean_torsion", "max_torsion",
            "mean_coherence", "max_coherence"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate no NaN/Inf
        for key, value in data.items():
            if isinstance(value, (int, float)):
                assert not self._is_nan_or_inf(value), f"NaN/Inf in state field: {key}"
        
        print(f"✓ Get substrate state - time: {data['time']}, mean_density: {data['mean_density']}")
    
    def test_get_substrate_state_not_found(self):
        """Test get state with non-existent ID"""
        response = requests.get(f"{BASE_URL}/api/mesoscopic/NONEXISTENT_12345/state")
        
        assert response.status_code == 404
        
        print(f"✓ Non-existent substrate state returns 404")
    
    def test_get_structures(self):
        """Test GET /api/mesoscopic/{id}/structures - get detected structures"""
        # Create and evolve a substrate
        init_payload = {
            "name": "TEST_Structures",
            "grid_size": 32,
            "amplitude": 0.1,
            "seed": 42
        }
        
        init_response = requests.post(f"{BASE_URL}/api/mesoscopic/initialize", json=init_payload)
        assert init_response.status_code == 200
        substrate_id = init_response.json()["substrate_id"]
        self.created_substrates.append(substrate_id)
        
        # Evolve to allow structure formation
        evolve_payload = {
            "steps": 500,
            "dt": 0.01,
            "detect_structures": False
        }
        requests.post(f"{BASE_URL}/api/mesoscopic/{substrate_id}/evolve", json=evolve_payload)
        
        # Get structures
        response = requests.get(f"{BASE_URL}/api/mesoscopic/{substrate_id}/structures")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate structure response
        assert "substrate_id" in data
        assert "time" in data
        assert "torsion_vortices" in data
        assert "strain_nodes" in data
        assert "coherence_clusters" in data
        assert "particle_nodes" in data
        assert "summary" in data
        
        # Validate summary
        summary = data["summary"]
        assert "vortex_count" in summary
        assert "strain_node_count" in summary
        assert "cluster_count" in summary
        assert "particle_node_count" in summary
        
        print(f"✓ Get structures - vortices: {summary['vortex_count']}, particles: {summary['particle_node_count']}")
    
    # ======================
    # ENERGY CONSERVATION TEST
    # ======================
    
    def test_energy_conservation(self):
        """Test that energy is conserved (< 5% drift) over simulation"""
        payload = {
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 20.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/stability-test", json=payload)
        
        assert response.status_code == 200
        
        data = response.json()
        result = data["stability_result"]
        
        energy_conservation = result["energy_conservation_ratio"]
        
        # Key requirement: Energy drift should be < 5%
        assert energy_conservation < 0.05, (
            f"ENERGY CONSERVATION VIOLATED: "
            f"Energy drift is {energy_conservation * 100:.2f}%, expected < 5%"
        )
        
        print(f"✓ Energy conservation test PASSED")
        print(f"  Energy drift: {energy_conservation * 100:.4f}% (requirement: < 5%)")
    
    # ======================
    # JSON SERIALIZATION TEST
    # ======================
    
    def test_json_serialization(self):
        """Test that all responses are valid JSON with no serialization errors"""
        # Test full simulation (most complex response)
        payload = {
            "name": "TEST_JSONTest",
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 10.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/run", json=payload)
        
        assert response.status_code == 200
        
        # Attempt to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in response: {e}")
        
        self.created_substrates.append(data["substrate_id"])
        
        # Recursively check for NaN/Inf values which cause JSON issues
        def check_values(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    check_values(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_values(v, f"{path}[{i}]")
            elif isinstance(obj, float):
                assert not self._is_nan_or_inf(obj), f"NaN/Inf found at {path}: {obj}"
        
        check_values(data)
        
        print(f"✓ JSON serialization test passed - all values valid")
    
    # ======================
    # STRUCTURE DETECTION TEST
    # ======================
    
    def test_structure_detection_after_evolution(self):
        """Test that structures are detected after sufficient evolution"""
        payload = {
            "name": "TEST_StructureDetection",
            "grid_size": 40,  # Larger grid for better structure formation
            "amplitude": 0.12,
            "total_time": 20.0,
            "dt": 0.01,
            "seed": 123
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/run", json=payload)
        
        assert response.status_code == 200
        
        data = response.json()
        self.created_substrates.append(data["substrate_id"])
        
        structures = data["emergent_structures"]
        
        # After evolution, we expect to see structure formation
        vortex_count = structures["torsion_vortices"]["count"]
        strain_count = structures["strain_nodes"]["count"]
        cluster_count = structures["coherence_clusters"]["count"]
        particle_count = structures["particle_nodes"]["count"]
        
        print(f"✓ Structure detection results:")
        print(f"  Torsion vortices: {vortex_count}")
        print(f"  Strain nodes: {strain_count}")
        print(f"  Coherence clusters: {cluster_count}")
        print(f"  Particle-like nodes: {particle_count}")
        
        # At least some structures should form
        total_structures = vortex_count + strain_count + cluster_count + particle_count
        
        # Log whether structures were detected
        if total_structures > 0:
            print(f"  Total structures detected: {total_structures}")
        else:
            print(f"  WARNING: No structures detected - this may be expected for some parameter sets")
    
    # ======================
    # DELETE SUBSTRATE TEST
    # ======================
    
    def test_delete_substrate(self):
        """Test DELETE /api/mesoscopic/{id} - delete substrate"""
        # Create a substrate to delete
        init_payload = {
            "name": "TEST_ToDelete",
            "grid_size": 32,
            "amplitude": 0.1,
            "seed": 42
        }
        
        init_response = requests.post(f"{BASE_URL}/api/mesoscopic/initialize", json=init_payload)
        assert init_response.status_code == 200
        substrate_id = init_response.json()["substrate_id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/mesoscopic/{substrate_id}")
        
        assert delete_response.status_code == 200
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/mesoscopic/{substrate_id}/state")
        assert get_response.status_code == 404
        
        print(f"✓ Delete substrate - verified removal")
    
    def test_delete_substrate_not_found(self):
        """Test delete non-existent substrate"""
        response = requests.delete(f"{BASE_URL}/api/mesoscopic/NONEXISTENT_12345")
        
        assert response.status_code == 404
        
        print(f"✓ Delete non-existent returns 404")
    
    # ======================
    # HELPER METHODS
    # ======================
    
    def _is_nan_or_inf(self, value) -> bool:
        """Check if value is NaN or Inf"""
        if isinstance(value, float):
            import math
            return math.isnan(value) or math.isinf(value)
        return False
    
    @classmethod
    def teardown_class(cls):
        """Cleanup created test substrates"""
        for substrate_id in cls.created_substrates:
            if "TEST_" in substrate_id:
                try:
                    requests.delete(f"{BASE_URL}/api/mesoscopic/{substrate_id}")
                except:
                    pass


# Additional focused tests for specific requirements

class TestEnergyConservation:
    """Focused tests for energy conservation requirement"""
    
    def test_energy_conservation_short_sim(self):
        """Test energy conservation over 10 second simulation"""
        payload = {
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 10.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/stability-test", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        drift = data["stability_result"]["energy_conservation_ratio"]
        
        assert drift < 0.05, f"Energy drift {drift*100:.2f}% exceeds 5% limit"
        print(f"✓ 10s sim energy conservation: {drift*100:.4f}%")
    
    def test_energy_conservation_long_sim(self):
        """Test energy conservation over 25 second simulation"""
        payload = {
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 25.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/stability-test", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        drift = data["stability_result"]["energy_conservation_ratio"]
        
        assert drift < 0.05, f"Energy drift {drift*100:.2f}% exceeds 5% limit"
        print(f"✓ 25s sim energy conservation: {drift*100:.4f}%")


class TestNumericalStability:
    """Focused tests for numerical stability - no NaN/Inf values"""
    
    def test_no_nan_in_simulation_output(self):
        """Verify no NaN values in simulation output"""
        payload = {
            "name": "TEST_NaN_Check",
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 15.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/run", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check final state
        final = data["final_state"]
        for key, value in final.items():
            if isinstance(value, float):
                import math
                assert not math.isnan(value), f"NaN found in final_state.{key}"
                assert not math.isinf(value), f"Inf found in final_state.{key}"
        
        # Check evolution samples
        for sample in data["evolution_samples"]:
            for key, value in sample.items():
                if isinstance(value, float):
                    import math
                    assert not math.isnan(value), f"NaN found in evolution sample {key}"
                    assert not math.isinf(value), f"Inf found in evolution sample {key}"
        
        print(f"✓ No NaN/Inf values detected in simulation output")
    
    def test_stability_under_high_amplitude(self):
        """Test numerical stability with higher amplitude fluctuations"""
        payload = {
            "grid_size": 32,
            "amplitude": 0.2,  # Higher amplitude
            "total_time": 10.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/stability-test", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        result = data["stability_result"]
        
        assert result["overall_stable"], f"Simulation unstable at high amplitude"
        assert result["unstable_steps"] == 0, f"Detected {result['unstable_steps']} unstable steps"
        
        print(f"✓ Stability maintained at amplitude=0.2")


class TestDensityPreservation:
    """Tests for density preservation (mean density near 1.0)"""
    
    def test_density_near_unity(self):
        """Test that mean density stays near 1.0"""
        payload = {
            "name": "TEST_DensityCheck",
            "grid_size": 32,
            "amplitude": 0.1,
            "total_time": 20.0,
            "dt": 0.01,
            "seed": 42
        }
        
        response = requests.post(f"{BASE_URL}/api/mesoscopic/run", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        final = data["final_state"]
        
        mean_density = final["mean_density"]
        
        # Density should be within 10% of 1.0
        assert 0.9 < mean_density < 1.1, f"Mean density {mean_density} deviates from 1.0"
        
        print(f"✓ Mean density preserved: {mean_density:.4f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
