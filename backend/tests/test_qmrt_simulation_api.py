"""
QMRT Simulation API Tests
=========================
Tests for the QMRT Simulation Lab API endpoints:
- POST /api/qmrt-sim/run - Run 2D/3D simulations with mesoscopic structure detection
- GET /api/qmrt-sim/info - Get simulation theory info

Key features tested:
- 2D simulation returns structures object with torsion_vortices, strain_nodes, coherence_clusters, particle_nodes
- 3D simulation returns structures object with all mesoscopic arrays
- TimePoint measurements include vortex_count, cluster_count, strain_node_count, particle_node_count
- Response structure validation (metrics + structures)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestQMRTSimulationInfo:
    """Test /api/qmrt-sim/info endpoint"""
    
    def test_get_simulation_info(self):
        """Test GET /api/qmrt-sim/info returns theory information"""
        response = requests.get(f"{BASE_URL}/api/qmrt-sim/info")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify theory info structure
        assert "theory" in data, "Response should contain 'theory' field"
        assert data["theory"] == "Quark Medium Relativity Theory (QMRT)"
        
        assert "components" in data, "Response should contain 'components' field"
        components = data["components"]
        assert "S" in components, "Components should include S (Spatial)"
        assert "O" in components, "Components should include O (Ordering)"
        assert "R" in components, "Components should include R (Rate)"
        assert "P" in components, "Components should include P (Persistence)"
        assert "I_TS" in components, "Components should include I_TS (Coupling)"
        
        print(f"✓ GET /api/qmrt-sim/info - 200 OK (theory: {data['theory']})")


class TestQMRTSimulation2D:
    """Test 2D QMRT simulation with mesoscopic structure detection"""
    
    def test_run_2d_simulation_basic(self):
        """Test POST /api/qmrt-sim/run with 2D dimension returns valid response"""
        payload = {
            "dimension": "2d",
            "size": 40,
            "alpha": 0.5,
            "lambda_relax": 0.5,
            "gamma_wave": 0.01,
            "steps": 100,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify basic response structure
        assert data["dimension"] == "2d", "Dimension should be '2d'"
        assert "measurements" in data, "Response should contain 'measurements'"
        assert "structures" in data, "Response should contain 'structures'"
        assert "config" in data, "Response should contain 'config'"
        assert "duration_seconds" in data, "Response should contain 'duration_seconds'"
        
        print(f"✓ POST /api/qmrt-sim/run (2D) - 200 OK (duration: {data['duration_seconds']:.2f}s)")
    
    def test_2d_simulation_structures_object(self):
        """Test 2D simulation returns structures object with all mesoscopic arrays"""
        payload = {
            "dimension": "2d",
            "size": 50,
            "alpha": 0.6,
            "steps": 150,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        structures = data["structures"]
        
        # Verify structures object contains all required arrays
        assert "torsion_vortices" in structures, "structures should contain 'torsion_vortices'"
        assert "strain_nodes" in structures, "structures should contain 'strain_nodes'"
        assert "coherence_clusters" in structures, "structures should contain 'coherence_clusters'"
        assert "particle_nodes" in structures, "structures should contain 'particle_nodes'"
        assert "t" in structures, "structures should contain 't' (timestamp)"
        
        # Verify arrays are lists
        assert isinstance(structures["torsion_vortices"], list), "torsion_vortices should be a list"
        assert isinstance(structures["strain_nodes"], list), "strain_nodes should be a list"
        assert isinstance(structures["coherence_clusters"], list), "coherence_clusters should be a list"
        assert isinstance(structures["particle_nodes"], list), "particle_nodes should be a list"
        
        print(f"✓ 2D structures object validated:")
        print(f"  - torsion_vortices: {len(structures['torsion_vortices'])} items")
        print(f"  - strain_nodes: {len(structures['strain_nodes'])} items")
        print(f"  - coherence_clusters: {len(structures['coherence_clusters'])} items")
        print(f"  - particle_nodes: {len(structures['particle_nodes'])} items")
    
    def test_2d_simulation_structure_counts_in_summary(self):
        """Test 2D simulation returns structure counts in summary fields"""
        payload = {
            "dimension": "2d",
            "size": 50,
            "alpha": 0.5,
            "steps": 150,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify summary count fields exist
        assert "total_vortices" in data, "Response should contain 'total_vortices'"
        assert "total_clusters" in data, "Response should contain 'total_clusters'"
        assert "total_strain_nodes" in data, "Response should contain 'total_strain_nodes'"
        assert "total_particle_nodes" in data, "Response should contain 'total_particle_nodes'"
        
        # Verify counts are integers
        assert isinstance(data["total_vortices"], int), "total_vortices should be int"
        assert isinstance(data["total_clusters"], int), "total_clusters should be int"
        assert isinstance(data["total_strain_nodes"], int), "total_strain_nodes should be int"
        assert isinstance(data["total_particle_nodes"], int), "total_particle_nodes should be int"
        
        # Verify particle node type breakdown
        assert "stable_nodes" in data, "Response should contain 'stable_nodes'"
        assert "proto_nodes" in data, "Response should contain 'proto_nodes'"
        assert "transient_nodes" in data, "Response should contain 'transient_nodes'"
        
        print(f"✓ 2D structure counts validated:")
        print(f"  - total_vortices: {data['total_vortices']}")
        print(f"  - total_strain_nodes: {data['total_strain_nodes']}")
        print(f"  - total_clusters: {data['total_clusters']}")
        print(f"  - total_particle_nodes: {data['total_particle_nodes']}")
        print(f"  - stable/proto/transient: {data['stable_nodes']}/{data['proto_nodes']}/{data['transient_nodes']}")
    
    def test_2d_timepoint_measurements_include_structure_counts(self):
        """Test 2D TimePoint measurements include vortex_count, cluster_count, etc."""
        payload = {
            "dimension": "2d",
            "size": 40,
            "alpha": 0.5,
            "steps": 100,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        measurements = data["measurements"]
        
        assert len(measurements) > 0, "Should have at least one measurement"
        
        # Check first measurement has structure counts
        first_measurement = measurements[0]
        
        assert "vortex_count" in first_measurement, "TimePoint should contain 'vortex_count'"
        assert "cluster_count" in first_measurement, "TimePoint should contain 'cluster_count'"
        assert "strain_node_count" in first_measurement, "TimePoint should contain 'strain_node_count'"
        assert "particle_node_count" in first_measurement, "TimePoint should contain 'particle_node_count'"
        
        # Verify they are integers
        assert isinstance(first_measurement["vortex_count"], int), "vortex_count should be int"
        assert isinstance(first_measurement["cluster_count"], int), "cluster_count should be int"
        assert isinstance(first_measurement["strain_node_count"], int), "strain_node_count should be int"
        assert isinstance(first_measurement["particle_node_count"], int), "particle_node_count should be int"
        
        # Check last measurement too
        last_measurement = measurements[-1]
        assert "vortex_count" in last_measurement
        assert "cluster_count" in last_measurement
        
        print(f"✓ 2D TimePoint measurements validated ({len(measurements)} points)")
        print(f"  - First point (t={first_measurement['t']:.2f}): vortex={first_measurement['vortex_count']}, cluster={first_measurement['cluster_count']}")
        print(f"  - Last point (t={last_measurement['t']:.2f}): vortex={last_measurement['vortex_count']}, cluster={last_measurement['cluster_count']}")
    
    def test_2d_simulation_metrics_structure(self):
        """Test 2D simulation returns proper metrics (S, O, R, P, I_TS)"""
        payload = {
            "dimension": "2d",
            "size": 40,
            "alpha": 0.5,
            "steps": 100,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify QMRT metrics
        assert "spatial_S_mean" in data, "Response should contain 'spatial_S_mean'"
        assert "ordering_O_mean" in data, "Response should contain 'ordering_O_mean'"
        assert "rate_R_mean" in data, "Response should contain 'rate_R_mean'"
        assert "persistence_P_mean" in data, "Response should contain 'persistence_P_mean'"
        assert "coupling_I_TS_mean" in data, "Response should contain 'coupling_I_TS_mean'"
        
        # Verify balance metrics
        assert "balance_achieved" in data, "Response should contain 'balance_achieved'"
        assert "balance_E_cv" in data, "Response should contain 'balance_E_cv'"
        
        # Verify geometry metrics
        assert "geometry_isotropic" in data, "Response should contain 'geometry_isotropic'"
        assert "geometry_confined" in data, "Response should contain 'geometry_confined'"
        
        # Verify correlations
        assert "rho_RS" in data, "Response should contain 'rho_RS'"
        assert "rho_PS" in data, "Response should contain 'rho_PS'"
        assert "rho_OS" in data, "Response should contain 'rho_OS'"
        
        print(f"✓ 2D metrics validated:")
        print(f"  - S={data['spatial_S_mean']:.4f}, O={data['ordering_O_mean']:.6f}")
        print(f"  - R={data['rate_R_mean']:.4f}, P={data['persistence_P_mean']:.4f}")
        print(f"  - I_TS={data['coupling_I_TS_mean']:.4f}")
        print(f"  - Balance: {data['balance_achieved']} (E_cv={data['balance_E_cv']:.4f})")


class TestQMRTSimulation3D:
    """Test 3D QMRT simulation with mesoscopic structure detection"""
    
    def test_run_3d_simulation_basic(self):
        """Test POST /api/qmrt-sim/run with 3D dimension returns valid response"""
        payload = {
            "dimension": "3d",
            "size": 30,  # Smaller for 3D performance
            "alpha": 0.5,
            "lambda_relax": 0.5,
            "gamma_wave": 0.01,
            "steps": 80,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=180)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify basic response structure
        assert data["dimension"] == "3d", "Dimension should be '3d'"
        assert "measurements" in data, "Response should contain 'measurements'"
        assert "structures" in data, "Response should contain 'structures'"
        
        print(f"✓ POST /api/qmrt-sim/run (3D) - 200 OK (duration: {data['duration_seconds']:.2f}s)")
    
    def test_3d_simulation_structures_object(self):
        """Test 3D simulation returns structures object with all mesoscopic arrays"""
        payload = {
            "dimension": "3d",
            "size": 30,
            "alpha": 0.6,
            "steps": 100,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=180)
        assert response.status_code == 200
        
        data = response.json()
        structures = data["structures"]
        
        # Verify structures object contains all required arrays
        assert "torsion_vortices" in structures, "structures should contain 'torsion_vortices'"
        assert "strain_nodes" in structures, "structures should contain 'strain_nodes'"
        assert "coherence_clusters" in structures, "structures should contain 'coherence_clusters'"
        assert "particle_nodes" in structures, "structures should contain 'particle_nodes'"
        assert "t" in structures, "structures should contain 't' (timestamp)"
        
        # Verify arrays are lists
        assert isinstance(structures["torsion_vortices"], list), "torsion_vortices should be a list"
        assert isinstance(structures["strain_nodes"], list), "strain_nodes should be a list"
        assert isinstance(structures["coherence_clusters"], list), "coherence_clusters should be a list"
        assert isinstance(structures["particle_nodes"], list), "particle_nodes should be a list"
        
        print(f"✓ 3D structures object validated:")
        print(f"  - torsion_vortices: {len(structures['torsion_vortices'])} items")
        print(f"  - strain_nodes: {len(structures['strain_nodes'])} items")
        print(f"  - coherence_clusters: {len(structures['coherence_clusters'])} items")
        print(f"  - particle_nodes: {len(structures['particle_nodes'])} items")
    
    def test_3d_timepoint_measurements_include_structure_counts(self):
        """Test 3D TimePoint measurements include vortex_count, cluster_count, etc."""
        payload = {
            "dimension": "3d",
            "size": 30,
            "alpha": 0.5,
            "steps": 80,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=180)
        assert response.status_code == 200
        
        data = response.json()
        measurements = data["measurements"]
        
        assert len(measurements) > 0, "Should have at least one measurement"
        
        # Check first measurement has structure counts
        first_measurement = measurements[0]
        
        assert "vortex_count" in first_measurement, "TimePoint should contain 'vortex_count'"
        assert "cluster_count" in first_measurement, "TimePoint should contain 'cluster_count'"
        assert "strain_node_count" in first_measurement, "TimePoint should contain 'strain_node_count'"
        assert "particle_node_count" in first_measurement, "TimePoint should contain 'particle_node_count'"
        
        print(f"✓ 3D TimePoint measurements validated ({len(measurements)} points)")
        print(f"  - First point (t={first_measurement['t']:.2f}): vortex={first_measurement['vortex_count']}, cluster={first_measurement['cluster_count']}")
    
    def test_3d_simulation_structure_counts_in_summary(self):
        """Test 3D simulation returns structure counts in summary fields"""
        payload = {
            "dimension": "3d",
            "size": 30,
            "alpha": 0.5,
            "steps": 100,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=180)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify summary count fields exist
        assert "total_vortices" in data, "Response should contain 'total_vortices'"
        assert "total_clusters" in data, "Response should contain 'total_clusters'"
        assert "total_strain_nodes" in data, "Response should contain 'total_strain_nodes'"
        assert "total_particle_nodes" in data, "Response should contain 'total_particle_nodes'"
        
        print(f"✓ 3D structure counts validated:")
        print(f"  - total_vortices: {data['total_vortices']}")
        print(f"  - total_strain_nodes: {data['total_strain_nodes']}")
        print(f"  - total_clusters: {data['total_clusters']}")
        print(f"  - total_particle_nodes: {data['total_particle_nodes']}")


class TestQMRTSimulationStructureDetails:
    """Test detailed structure data validation"""
    
    def test_vortex_structure_fields(self):
        """Test torsion vortex structure has correct fields"""
        payload = {
            "dimension": "2d",
            "size": 60,
            "alpha": 0.7,  # Higher alpha for more structures
            "steps": 200,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        vortices = data["structures"]["torsion_vortices"]
        
        if len(vortices) > 0:
            vortex = vortices[0]
            assert "position" in vortex, "Vortex should have 'position'"
            assert "strength" in vortex, "Vortex should have 'strength'"
            assert "radius" in vortex, "Vortex should have 'radius'"
            assert "chirality" in vortex, "Vortex should have 'chirality'"
            
            assert isinstance(vortex["position"], list), "position should be a list"
            assert isinstance(vortex["strength"], (int, float)), "strength should be numeric"
            assert isinstance(vortex["radius"], (int, float)), "radius should be numeric"
            assert vortex["chirality"] in [-1, 1], "chirality should be -1 or +1"
            
            print(f"✓ Vortex structure validated: pos={vortex['position']}, ω={vortex['strength']:.4f}, r={vortex['radius']:.2f}, χ={vortex['chirality']}")
        else:
            print("⚠ No vortices detected in this run (may be expected based on parameters)")
    
    def test_strain_node_structure_fields(self):
        """Test strain node structure has correct fields"""
        payload = {
            "dimension": "2d",
            "size": 60,
            "alpha": 0.6,
            "steps": 200,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        strain_nodes = data["structures"]["strain_nodes"]
        
        if len(strain_nodes) > 0:
            node = strain_nodes[0]
            assert "position" in node, "Strain node should have 'position'"
            assert "energy_density" in node, "Strain node should have 'energy_density'"
            assert "gradient_magnitude" in node, "Strain node should have 'gradient_magnitude'"
            assert "stability" in node, "Strain node should have 'stability'"
            
            assert isinstance(node["position"], list), "position should be a list"
            assert isinstance(node["energy_density"], (int, float)), "energy_density should be numeric"
            assert isinstance(node["stability"], (int, float)), "stability should be numeric"
            
            print(f"✓ Strain node validated: pos={node['position']}, E={node['energy_density']:.4f}, σ={node['stability']:.2f}")
        else:
            print("⚠ No strain nodes detected in this run")
    
    def test_coherence_cluster_structure_fields(self):
        """Test coherence cluster structure has correct fields"""
        payload = {
            "dimension": "2d",
            "size": 60,
            "alpha": 0.6,
            "steps": 200,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        clusters = data["structures"]["coherence_clusters"]
        
        if len(clusters) > 0:
            cluster = clusters[0]
            assert "center" in cluster, "Cluster should have 'center'"
            assert "size" in cluster, "Cluster should have 'size'"
            assert "coherence_strength" in cluster, "Cluster should have 'coherence_strength'"
            assert "member_count" in cluster, "Cluster should have 'member_count'"
            assert "phase_value" in cluster, "Cluster should have 'phase_value'"
            
            assert isinstance(cluster["center"], list), "center should be a list"
            assert isinstance(cluster["member_count"], int), "member_count should be int"
            
            print(f"✓ Cluster validated: center={cluster['center']}, n={cluster['member_count']}, Φ={cluster['coherence_strength']:.4f}")
        else:
            print("⚠ No clusters detected in this run")
    
    def test_particle_node_structure_fields(self):
        """Test particle node structure has correct fields"""
        payload = {
            "dimension": "2d",
            "size": 60,
            "alpha": 0.7,
            "steps": 250,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        particles = data["structures"]["particle_nodes"]
        
        if len(particles) > 0:
            particle = particles[0]
            assert "id" in particle, "Particle should have 'id'"
            assert "position" in particle, "Particle should have 'position'"
            assert "density_concentration" in particle, "Particle should have 'density_concentration'"
            assert "strain_energy" in particle, "Particle should have 'strain_energy'"
            assert "effective_mass" in particle, "Particle should have 'effective_mass'"
            assert "stability_score" in particle, "Particle should have 'stability_score'"
            assert "structure_type" in particle, "Particle should have 'structure_type'"
            assert "has_vortex" in particle, "Particle should have 'has_vortex'"
            assert "has_cluster" in particle, "Particle should have 'has_cluster'"
            
            assert particle["structure_type"] in ["stable", "proto-particle", "transient"], \
                f"structure_type should be valid, got {particle['structure_type']}"
            
            print(f"✓ Particle node validated: id={particle['id']}, type={particle['structure_type']}, m={particle['effective_mass']:.4f}")
        else:
            print("⚠ No particle nodes detected in this run (requires co-located vortex/cluster with strain)")


class TestQMRTSimulationInputValidation:
    """Test input validation for simulation parameters"""
    
    def test_invalid_dimension(self):
        """Test invalid dimension parameter"""
        payload = {
            "dimension": "4d",  # Invalid
            "size": 40,
            "steps": 100
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=30)
        assert response.status_code == 422, f"Expected 422 for invalid dimension, got {response.status_code}"
        print("✓ Invalid dimension rejected with 422")
    
    def test_size_limits(self):
        """Test grid size limits"""
        # Too small
        payload = {"dimension": "2d", "size": 10, "steps": 50}
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=30)
        assert response.status_code == 422, f"Expected 422 for size=10, got {response.status_code}"
        
        # Too large
        payload = {"dimension": "2d", "size": 200, "steps": 50}
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=30)
        assert response.status_code == 422, f"Expected 422 for size=200, got {response.status_code}"
        
        print("✓ Size limits validated (20-100)")
    
    def test_alpha_limits(self):
        """Test alpha (backreaction) limits"""
        # Too small
        payload = {"dimension": "2d", "size": 40, "alpha": 0.05, "steps": 50}
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=30)
        assert response.status_code == 422, f"Expected 422 for alpha=0.05, got {response.status_code}"
        
        # Too large
        payload = {"dimension": "2d", "size": 40, "alpha": 0.95, "steps": 50}
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=30)
        assert response.status_code == 422, f"Expected 422 for alpha=0.95, got {response.status_code}"
        
        print("✓ Alpha limits validated (0.1-0.9)")


class TestQMRTSimulationFieldSnapshots:
    """Test field snapshot data in response"""
    
    def test_2d_field_snapshots(self):
        """Test 2D simulation returns field snapshots"""
        payload = {
            "dimension": "2d",
            "size": 40,
            "steps": 100,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=120)
        assert response.status_code == 200
        
        data = response.json()
        
        assert "field_snapshots" in data, "Response should contain 'field_snapshots'"
        snapshots = data["field_snapshots"]
        
        if len(snapshots) > 0:
            snapshot = snapshots[0]
            assert "t" in snapshot, "Snapshot should have 't'"
            assert "rho" in snapshot, "2D snapshot should have 'rho'"
            assert "c_eff" in snapshot, "2D snapshot should have 'c_eff'"
            assert "tau" in snapshot, "2D snapshot should have 'tau'"
            
            print(f"✓ 2D field snapshots validated ({len(snapshots)} snapshots)")
        else:
            print("⚠ No field snapshots in response")
    
    def test_3d_field_snapshots(self):
        """Test 3D simulation returns field snapshots with slices"""
        payload = {
            "dimension": "3d",
            "size": 30,
            "steps": 80,
            "sample_interval": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/qmrt-sim/run", json=payload, timeout=180)
        assert response.status_code == 200
        
        data = response.json()
        
        assert "field_snapshots" in data, "Response should contain 'field_snapshots'"
        snapshots = data["field_snapshots"]
        
        if len(snapshots) > 0:
            snapshot = snapshots[0]
            assert "t" in snapshot, "Snapshot should have 't'"
            assert "rho_xy" in snapshot, "3D snapshot should have 'rho_xy'"
            assert "rho_xz" in snapshot, "3D snapshot should have 'rho_xz'"
            assert "rho_yz" in snapshot, "3D snapshot should have 'rho_yz'"
            assert "c_eff_xy" in snapshot, "3D snapshot should have 'c_eff_xy'"
            
            print(f"✓ 3D field snapshots validated ({len(snapshots)} snapshots with XY/XZ/YZ slices)")
        else:
            print("⚠ No field snapshots in response")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
