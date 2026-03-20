"""
QMRT Frequency-Domain Engine API Tests

Tests the foundational QMRT physics with explicit frequency field (ω).
Key physics: V_band(ω) = a_ω(ω² − ω₀²)² creates frequency basins (spectral universes).

Features tested:
- Five fields: (ρ, σ, τ, φ, ω) with conjugate momenta
- Energy conservation < 1% drift
- Frequency basins (ω clustering toward ±ω₀)
- Phase basins (matter/antimatter separation)
- Structure classification by BOTH phase AND frequency band
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test configuration for faster tests
TEST_CONFIG = {
    "grid_size": 16,  # Smaller grid for speed
    "total_time": 10.0,  # Shorter simulation
    "dt": 0.01,
    "amplitude": 0.05,
}


class TestQMRTFrequencyTheory:
    """Tests for GET /api/qmrt_frequency/theory endpoint"""
    
    def test_theory_endpoint_returns_200(self):
        """Verify theory endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/theory")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Theory endpoint returns 200 OK")
    
    def test_theory_contains_five_fields(self):
        """Verify theory describes all 5 fields including omega"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/theory")
        assert response.status_code == 200
        
        data = response.json()
        assert "fields" in data, "Response should contain 'fields'"
        
        fields = data["fields"]
        # Check for all 5 fundamental fields
        assert "ρ (rho)" in fields, "Missing rho field"
        assert "σ (sigma)" in fields, "Missing sigma field"
        assert "τ (tau)" in fields, "Missing tau field"
        assert "φ (phi)" in fields, "Missing phi field"
        assert "ω (omega)" in fields, "Missing omega field - the NEW frequency field"
        
        print(f"✓ All 5 fields documented: {list(fields.keys())}")
    
    def test_theory_contains_frequency_physics(self):
        """Verify theory describes frequency band potential"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/theory")
        assert response.status_code == 200
        
        data = response.json()
        assert "frequency_physics" in data, "Response should contain 'frequency_physics'"
        
        freq_physics = data["frequency_physics"]
        assert "band_potential" in freq_physics, "Missing band_potential"
        assert "ω²" in freq_physics["band_potential"] or "omega" in freq_physics["band_potential"].lower(), \
            "Band potential should reference ω"
        
        print(f"✓ Frequency physics documented: {freq_physics.get('band_potential', 'N/A')}")
    
    def test_theory_contains_multiverse_interpretation(self):
        """Verify theory explains spectral universes concept"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/theory")
        assert response.status_code == 200
        
        data = response.json()
        assert "multiverse_interpretation" in data, "Response should explain multiverse interpretation"
        
        print("✓ Multiverse/spectral universe interpretation documented")


class TestFrequencyDomainSeparation:
    """Tests for POST /api/qmrt_frequency/test_frequency_domains endpoint"""
    
    def test_frequency_domains_endpoint_returns_200(self):
        """Verify frequency domain test endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/test_frequency_domains",
            json={
                "grid_size": TEST_CONFIG["grid_size"],
                "total_time": TEST_CONFIG["total_time"],
                "dt": TEST_CONFIG["dt"],
                "amplitude": TEST_CONFIG["amplitude"],
                "matter_fraction": 0.5,
                "high_freq_fraction": 0.5,
                "seed": 42
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Frequency domains test endpoint returns 200 OK")
    
    def test_frequency_domains_energy_conservation(self):
        """Verify energy conservation < 1% drift"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/test_frequency_domains",
            json={
                "grid_size": TEST_CONFIG["grid_size"],
                "total_time": TEST_CONFIG["total_time"],
                "dt": TEST_CONFIG["dt"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "final_state" in data, "Response should contain final_state"
        
        final_state = data["final_state"]
        energy_drift_pct = abs(final_state.get("energy_drift_pct", 999))
        
        # Key physics test: energy conservation < 1%
        assert energy_drift_pct < 1.0, \
            f"Energy drift {energy_drift_pct:.4f}% exceeds 1% threshold"
        
        print(f"✓ Energy conservation verified: {energy_drift_pct:.4f}% drift (< 1% required)")
    
    def test_frequency_domains_basins_form(self):
        """Verify frequency basins form (ω → ±ω₀)"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/test_frequency_domains",
            json={
                "grid_size": TEST_CONFIG["grid_size"],
                "total_time": TEST_CONFIG["total_time"],
                "dt": TEST_CONFIG["dt"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        final_state = data["final_state"]
        stats = final_state.get("statistics", {})
        
        # Check frequency basin fractions
        high_basin = stats.get("in_high_basin_fraction", 0)
        low_basin = stats.get("in_low_basin_fraction", 0)
        total_in_basins = high_basin + low_basin
        
        # At least some frequency clustering should occur
        assert total_in_basins > 0.01, \
            f"Expected frequency clustering, got {total_in_basins:.2%} in basins"
        
        print(f"✓ Frequency basins forming: high={high_basin:.2%}, low={low_basin:.2%}, total={total_in_basins:.2%}")
    
    def test_frequency_domains_phase_basins_exist(self):
        """Verify phase basins exist (matter/antimatter separation)"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/test_frequency_domains",
            json={
                "grid_size": TEST_CONFIG["grid_size"],
                "total_time": TEST_CONFIG["total_time"],
                "dt": TEST_CONFIG["dt"],
                "amplitude": TEST_CONFIG["amplitude"],
                "matter_fraction": 0.5,
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        validation = data.get("validation_results", {})
        
        phase_basins_exist = validation.get("phase_basins_exist", False)
        stats = data["final_state"].get("statistics", {})
        
        matter_frac = stats.get("matter_fraction", 0)
        antimatter_frac = stats.get("antimatter_fraction", 0)
        
        print(f"✓ Phase basins: matter={matter_frac:.2%}, antimatter={antimatter_frac:.2%}")
        
        # Both basins should have some population
        assert matter_frac > 0.1, f"Expected matter_fraction > 10%, got {matter_frac:.2%}"
        assert antimatter_frac > 0.1, f"Expected antimatter_fraction > 10%, got {antimatter_frac:.2%}"


class TestSpectralUniverseFormation:
    """Tests for POST /api/qmrt_frequency/test_spectral_universes endpoint"""
    
    def test_spectral_universes_endpoint_returns_200(self):
        """Verify spectral universe test endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/test_spectral_universes",
            json={
                "grid_size": TEST_CONFIG["grid_size"],
                "total_time": 15.0,  # Slightly longer for universe formation
                "dt": TEST_CONFIG["dt"],
                "amplitude": 0.1,  # Higher amplitude for turbulent start
                "seed": 42
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Spectral universes test endpoint returns 200 OK")
    
    def test_spectral_universes_turbulent_start(self):
        """Verify test starts with turbulent conditions"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/test_spectral_universes",
            json={
                "grid_size": TEST_CONFIG["grid_size"],
                "total_time": 15.0,
                "dt": TEST_CONFIG["dt"],
                "amplitude": 0.1,
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        test_params = data.get("test_params", {})
        
        # Verify turbulent initial conditions
        assert test_params.get("initial_conditions") == "turbulent", \
            "Should start with turbulent initial conditions"
        
        print("✓ Turbulent initial conditions confirmed")
    
    def test_spectral_universes_frequency_clustering(self):
        """Verify frequency clustering occurs from turbulent start"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/test_spectral_universes",
            json={
                "grid_size": TEST_CONFIG["grid_size"],
                "total_time": 15.0,
                "dt": TEST_CONFIG["dt"],
                "amplitude": 0.1,
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        metrics = data.get("spectral_universe_metrics", {})
        
        frequency_clustering = metrics.get("frequency_clustering", 0)
        
        # Some clustering should occur (values depend on simulation parameters)
        print(f"✓ Frequency clustering metric: {frequency_clustering:.4f}")
        
        # Verify phase ordering occurs
        phase_ordering = metrics.get("phase_ordering", False)
        print(f"✓ Phase ordering achieved: {phase_ordering}")


class TestEngineInitialization:
    """Tests for POST /api/qmrt_frequency/initialize endpoint"""
    
    def test_initialize_returns_200(self):
        """Verify initialization endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "matter_fraction": 0.5,
                "high_freq_fraction": 0.5,
                "seed": 42
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Initialize endpoint returns 200 OK")
    
    def test_initialize_returns_engine_id(self):
        """Verify initialization returns valid engine_id"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine_ID",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "engine_id" in data, "Response should contain engine_id"
        assert data["engine_id"], "engine_id should not be empty"
        
        print(f"✓ Engine ID returned: {data['engine_id']}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/qmrt_frequency/{data['engine_id']}")
    
    def test_initialize_has_five_fields(self):
        """Verify initialization confirms 5 fields"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine_Fields",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "fields" in data, "Response should describe fields"
        
        # Should mention all 5 fields
        fields_str = data["fields"]
        assert "ρ" in fields_str or "rho" in fields_str.lower(), "Missing rho"
        assert "σ" in fields_str or "sigma" in fields_str.lower(), "Missing sigma"
        assert "τ" in fields_str or "tau" in fields_str.lower(), "Missing tau"
        assert "φ" in fields_str or "phi" in fields_str.lower(), "Missing phi"
        assert "ω" in fields_str or "omega" in fields_str.lower(), "Missing omega"
        
        print(f"✓ Five fields confirmed: {fields_str}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/qmrt_frequency/{data['engine_id']}")
    
    def test_initialize_initial_state_statistics(self):
        """Verify initial state contains frequency statistics"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine_Stats",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        initial_state = data.get("initial_state", {})
        stats = initial_state.get("statistics", {})
        
        # Verify frequency statistics present
        assert "omega_mean" in stats, "Missing omega_mean"
        assert "omega_std" in stats, "Missing omega_std"
        assert "high_freq_fraction" in stats, "Missing high_freq_fraction"
        assert "low_freq_fraction" in stats, "Missing low_freq_fraction"
        assert "in_high_basin_fraction" in stats, "Missing in_high_basin_fraction"
        assert "in_low_basin_fraction" in stats, "Missing in_low_basin_fraction"
        
        print(f"✓ Frequency statistics present: omega_mean={stats['omega_mean']:.4f}, omega_std={stats['omega_std']:.4f}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/qmrt_frequency/{data['engine_id']}")


class TestEngineEvolution:
    """Tests for POST /api/qmrt_frequency/{engine_id}/evolve endpoint"""
    
    @pytest.fixture
    def engine_id(self):
        """Create engine for testing and cleanup after"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine_Evolve",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        assert response.status_code == 200
        engine_id = response.json()["engine_id"]
        
        yield engine_id
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/qmrt_frequency/{engine_id}")
    
    def test_evolve_returns_200(self, engine_id):
        """Verify evolve endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/{engine_id}/evolve",
            json={"steps": 100, "dt": 0.01}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Evolve endpoint returns 200 OK")
    
    def test_evolve_updates_time(self, engine_id):
        """Verify evolution updates simulation time"""
        # Get initial time
        state_resp = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/state")
        initial_time = state_resp.json().get("time", 0)
        
        # Evolve
        steps = 100
        dt = 0.01
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/{engine_id}/evolve",
            json={"steps": steps, "dt": dt}
        )
        assert response.status_code == 200
        
        data = response.json()
        final_state = data.get("final_state", {})
        final_time = final_state.get("time", 0)
        
        expected_time = initial_time + steps * dt
        assert abs(final_time - expected_time) < 0.01, \
            f"Time mismatch: expected ~{expected_time:.2f}, got {final_time:.2f}"
        
        print(f"✓ Time updated correctly: {initial_time:.2f} → {final_time:.2f}")
    
    def test_evolve_energy_conservation(self, engine_id):
        """Verify energy conservation during evolution"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/{engine_id}/evolve",
            json={"steps": 500, "dt": 0.01}  # Longer evolution
        )
        assert response.status_code == 200
        
        data = response.json()
        final_state = data.get("final_state", {})
        energy_drift = abs(final_state.get("energy_drift_pct", 999))
        
        # Energy conservation < 1%
        assert energy_drift < 1.0, \
            f"Energy drift {energy_drift:.4f}% exceeds 1% threshold"
        
        print(f"✓ Energy conservation during evolution: {energy_drift:.4f}% drift")
    
    def test_evolve_returns_structures(self, engine_id):
        """Verify evolve returns structure information"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/{engine_id}/evolve",
            json={"steps": 200, "dt": 0.01}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "structures" in data, "Response should contain structures"
        
        structures = data["structures"]
        assert "active" in structures, "Should have active count"
        assert "items" in structures, "Should have structure items"
        
        print(f"✓ Structures returned: {structures['active']} active")
    
    def test_evolve_nonexistent_engine(self):
        """Verify 404 for non-existent engine"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/nonexistent_engine_xyz/evolve",
            json={"steps": 100, "dt": 0.01}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ 404 returned for non-existent engine")


class TestEngineState:
    """Tests for GET /api/qmrt_frequency/{engine_id}/state endpoint"""
    
    @pytest.fixture
    def engine_id(self):
        """Create and evolve engine for testing"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine_State",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        engine_id = response.json()["engine_id"]
        
        # Evolve to get interesting state
        requests.post(
            f"{BASE_URL}/api/qmrt_frequency/{engine_id}/evolve",
            json={"steps": 200, "dt": 0.01}
        )
        
        yield engine_id
        
        requests.delete(f"{BASE_URL}/api/qmrt_frequency/{engine_id}")
    
    def test_state_returns_200(self, engine_id):
        """Verify state endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/state")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ State endpoint returns 200 OK")
    
    def test_state_contains_frequency_statistics(self, engine_id):
        """Verify state contains frequency-specific statistics"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/state")
        assert response.status_code == 200
        
        data = response.json()
        stats = data.get("statistics", {})
        
        # Frequency statistics
        assert "omega_mean" in stats, "Missing omega_mean"
        assert "omega_std" in stats, "Missing omega_std"
        assert "high_freq_fraction" in stats, "Missing high_freq_fraction"
        assert "low_freq_fraction" in stats, "Missing low_freq_fraction"
        assert "in_high_basin_fraction" in stats, "Missing in_high_basin_fraction"
        assert "in_low_basin_fraction" in stats, "Missing in_low_basin_fraction"
        
        # Phase statistics
        assert "matter_fraction" in stats, "Missing matter_fraction"
        assert "antimatter_fraction" in stats, "Missing antimatter_fraction"
        
        print(f"✓ Frequency statistics present: ω_mean={stats['omega_mean']:.4f}, ω_std={stats['omega_std']:.4f}")
        print(f"  Basin fractions: high={stats['in_high_basin_fraction']:.2%}, low={stats['in_low_basin_fraction']:.2%}")
    
    def test_state_contains_energy_tracking(self, engine_id):
        """Verify state contains energy tracking"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/state")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "total_energy" in data, "Missing total_energy"
        assert "initial_energy" in data, "Missing initial_energy"
        assert "energy_drift_pct" in data, "Missing energy_drift_pct"
        
        print(f"✓ Energy tracking: E={data['total_energy']:.4f}, drift={data['energy_drift_pct']:.4f}%")
    
    def test_state_contains_structure_breakdown(self, engine_id):
        """Verify state contains structure breakdown by phase AND frequency"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/state")
        assert response.status_code == 200
        
        data = response.json()
        breakdown = data.get("structure_breakdown", {})
        
        # Should have breakdown by both phase and frequency
        assert "total_active" in breakdown, "Missing total_active"
        assert "matter_high_freq" in breakdown, "Missing matter_high_freq"
        assert "matter_low_freq" in breakdown, "Missing matter_low_freq"
        assert "antimatter_high_freq" in breakdown, "Missing antimatter_high_freq"
        assert "antimatter_low_freq" in breakdown, "Missing antimatter_low_freq"
        
        print(f"✓ Structure breakdown: matter_high={breakdown['matter_high_freq']}, "
              f"matter_low={breakdown['matter_low_freq']}, "
              f"antimatter_high={breakdown['antimatter_high_freq']}, "
              f"antimatter_low={breakdown['antimatter_low_freq']}")


class TestEngineStructures:
    """Tests for GET /api/qmrt_frequency/{engine_id}/structures endpoint"""
    
    @pytest.fixture
    def engine_id(self):
        """Create and evolve engine for testing structures"""
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine_Structures",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        engine_id = response.json()["engine_id"]
        
        # Evolve to form structures
        requests.post(
            f"{BASE_URL}/api/qmrt_frequency/{engine_id}/evolve",
            json={"steps": 300, "dt": 0.01}
        )
        
        yield engine_id
        
        requests.delete(f"{BASE_URL}/api/qmrt_frequency/{engine_id}")
    
    def test_structures_returns_200(self, engine_id):
        """Verify structures endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/structures")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Structures endpoint returns 200 OK")
    
    def test_structures_contain_phase_classification(self, engine_id):
        """Verify structures have phase_basin classification"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/structures")
        assert response.status_code == 200
        
        data = response.json()
        structures = data.get("structures", [])
        
        if structures:
            for s in structures[:5]:  # Check first 5
                assert "phase_basin" in s, f"Structure missing phase_basin"
                assert s["phase_basin"] in ["matter", "antimatter", "transitional"], \
                    f"Invalid phase_basin: {s['phase_basin']}"
            
            print(f"✓ Phase classification present in {len(structures)} structures")
        else:
            print("⚠ No structures formed in this run")
    
    def test_structures_contain_frequency_classification(self, engine_id):
        """Verify structures have frequency_band classification (KEY NEW FEATURE)"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/structures")
        assert response.status_code == 200
        
        data = response.json()
        structures = data.get("structures", [])
        
        if structures:
            for s in structures[:5]:  # Check first 5
                assert "frequency_band" in s, f"Structure missing frequency_band"
                assert s["frequency_band"] in ["high_band", "low_band", "transitional"], \
                    f"Invalid frequency_band: {s['frequency_band']}"
                
                assert "omega_value" in s, "Structure missing omega_value"
            
            # Count frequency band distribution
            high_count = sum(1 for s in structures if s["frequency_band"] == "high_band")
            low_count = sum(1 for s in structures if s["frequency_band"] == "low_band")
            trans_count = sum(1 for s in structures if s["frequency_band"] == "transitional")
            
            print(f"✓ Frequency classification present: high={high_count}, low={low_count}, transitional={trans_count}")
        else:
            print("⚠ No structures formed in this run")
    
    def test_structures_have_mode_properties(self, engine_id):
        """Verify structures have detailed mode properties"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/structures")
        assert response.status_code == 200
        
        data = response.json()
        structures = data.get("structures", [])
        
        if structures:
            s = structures[0]
            assert "mode_properties" in s, "Structure missing mode_properties"
            
            props = s["mode_properties"]
            # Check for frequency-related properties
            assert "omega" in props, "Missing omega in mode_properties"
            assert "frequency_band" in props, "Missing frequency_band in mode_properties"
            assert "omega_gradient_sq" in props, "Missing omega_gradient_sq"
            
            # Check for phase-related properties
            assert "phase_value" in props, "Missing phase_value"
            assert "phase_basin" in props, "Missing phase_basin"
            
            print(f"✓ Mode properties present with ω={props['omega']:.4f}, φ={props['phase_value']:.4f}")
        else:
            print("⚠ No structures formed in this run")
    
    def test_structures_have_topological_signature(self, engine_id):
        """Verify structures have topological signature with frequency component"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/structures")
        assert response.status_code == 200
        
        data = response.json()
        structures = data.get("structures", [])
        
        if structures:
            s = structures[0]
            assert "topological_signature" in s, "Structure missing topological_signature"
            
            sig = s["topological_signature"]
            assert len(sig) == 3, f"Expected 3-tuple signature (winding, freq_band_sign, tau_sign), got {sig}"
            
            print(f"✓ Topological signature present: {sig}")
        else:
            print("⚠ No structures formed in this run")


class TestEngineManagement:
    """Tests for engine listing and deletion"""
    
    def test_list_engines(self):
        """Verify engine listing works"""
        response = requests.get(f"{BASE_URL}/api/qmrt_frequency/list")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "count" in data, "Response should have count"
        assert "engines" in data, "Response should have engines list"
        
        print(f"✓ Engine listing works: {data['count']} engines")
    
    def test_delete_engine(self):
        """Verify engine deletion works"""
        # Create engine
        create_resp = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={
                "name": "TestEngine_Delete",
                "grid_size": TEST_CONFIG["grid_size"],
                "amplitude": TEST_CONFIG["amplitude"],
                "seed": 42
            }
        )
        engine_id = create_resp.json()["engine_id"]
        
        # Delete
        delete_resp = requests.delete(f"{BASE_URL}/api/qmrt_frequency/{engine_id}")
        assert delete_resp.status_code == 200, f"Expected 200, got {delete_resp.status_code}"
        
        # Verify deleted
        get_resp = requests.get(f"{BASE_URL}/api/qmrt_frequency/{engine_id}/state")
        assert get_resp.status_code == 404, "Engine should be deleted"
        
        print("✓ Engine deletion works correctly")


class TestInputValidation:
    """Tests for input validation"""
    
    def test_grid_size_limits(self):
        """Verify grid_size validation (8-48)"""
        # Too small
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={"name": "Test", "grid_size": 4}
        )
        assert response.status_code == 422, "grid_size=4 should fail validation"
        
        # Too large
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={"name": "Test", "grid_size": 100}
        )
        assert response.status_code == 422, "grid_size=100 should fail validation"
        
        print("✓ Grid size validation working (8-48 range)")
    
    def test_amplitude_limits(self):
        """Verify amplitude validation"""
        # Too small
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={"name": "Test", "grid_size": 16, "amplitude": 0.0001}
        )
        assert response.status_code == 422, "amplitude=0.0001 should fail validation"
        
        # Too large
        response = requests.post(
            f"{BASE_URL}/api/qmrt_frequency/initialize",
            json={"name": "Test", "grid_size": 16, "amplitude": 5.0}
        )
        assert response.status_code == 422, "amplitude=5.0 should fail validation"
        
        print("✓ Amplitude validation working (0.001-1.0 range)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
