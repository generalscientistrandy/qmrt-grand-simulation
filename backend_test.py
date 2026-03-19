#!/usr/bin/env python3
"""
Backend API Testing for QMRT Simulation Universe
Tests all endpoints using the public production URL
"""
import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Use production public URL for testing
BACKEND_URL = "https://death-world-gen.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class QMRTAPITester:
    def __init__(self):
        self.base_url = API_BASE
        self.tests_run = 0
        self.tests_passed = 0
        self.created_world_id = None
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {details}")
        else:
            print(f"❌ {name}: FAILED {details}")
        
    def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_fields = ["message", "version", "substrate"]
                has_fields = all(field in data for field in expected_fields)
                success = has_fields and data.get("substrate") == "Quark Medium Relativity Theory"
                
            self.log_test("Root API endpoint", success, 
                         f"Status: {response.status_code}, Data: {response.json() if success else 'Invalid'}")
            return success
            
        except Exception as e:
            self.log_test("Root API endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_substrate_info_endpoint(self):
        """Test GET /api/substrate/info endpoint"""
        try:
            response = requests.get(f"{self.base_url}/substrate/info", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_fields = ["theory", "substrate_properties", "death_world_scaling", "world_generation"]
                has_fields = all(field in data for field in expected_fields)
                success = (has_fields and 
                          data.get("theory") == "Quark Medium Relativity Theory (QMRT)" and
                          len(data.get("substrate_properties", [])) == 4)
                
            self.log_test("Substrate info endpoint", success,
                         f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Substrate info endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_create_world(self):
        """Test POST /api/worlds endpoint"""
        test_world = {
            "name": f"Test World {datetime.now().strftime('%H%M%S')}",
            "death_world_level": 8,
            "seed": 12345,
            "evolution_steps": 100
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/worlds",
                json=test_world,
                timeout=30  # World generation can take time
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["id", "name", "death_world_level", "classification", 
                                 "world_parameters", "substrate_metrics", "apex_qualified"]
                has_fields = all(field in data for field in required_fields)
                
                # Validate data structure
                valid_data = (
                    has_fields and
                    data["name"] == test_world["name"] and
                    data["death_world_level"] == test_world["death_world_level"] and
                    isinstance(data["world_parameters"], dict) and
                    isinstance(data["substrate_metrics"], dict) and
                    len(data["world_parameters"]) >= 10 and
                    len(data["substrate_metrics"]) >= 10
                )
                
                if valid_data:
                    self.created_world_id = data["id"]
                    
                success = valid_data
                
            self.log_test("Create world", success,
                         f"Status: {response.status_code}, ID: {self.created_world_id if success else 'N/A'}")
            return success
            
        except Exception as e:
            self.log_test("Create world", False, f"Error: {str(e)}")
            return False
    
    def test_list_worlds(self):
        """Test GET /api/worlds endpoint"""
        try:
            response = requests.get(f"{self.base_url}/worlds", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_structure = (
                    "worlds" in data and
                    "total" in data and
                    isinstance(data["worlds"], list) and
                    isinstance(data["total"], int)
                )
                
                # If we created a world, it should be in the list
                if has_structure and self.created_world_id:
                    world_ids = [w["id"] for w in data["worlds"]]
                    has_created_world = self.created_world_id in world_ids
                    success = has_structure and has_created_world
                else:
                    success = has_structure
                
            self.log_test("List worlds", success,
                         f"Status: {response.status_code}, Count: {data.get('total', 'Unknown') if success else 'N/A'}")
            return success
            
        except Exception as e:
            self.log_test("List worlds", False, f"Error: {str(e)}")
            return False
    
    def test_get_world(self):
        """Test GET /api/worlds/{id} endpoint"""
        if not self.created_world_id:
            self.log_test("Get specific world", False, "No world ID available (create world test failed)")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/worlds/{self.created_world_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["id", "name", "death_world_level", "classification", 
                                 "world_parameters", "substrate_metrics"]
                has_fields = all(field in data for field in required_fields)
                correct_id = data.get("id") == self.created_world_id
                success = has_fields and correct_id
                
            self.log_test("Get specific world", success,
                         f"Status: {response.status_code}, ID matches: {data.get('id') == self.created_world_id if success else 'N/A'}")
            return success
            
        except Exception as e:
            self.log_test("Get specific world", False, f"Error: {str(e)}")
            return False
    
    def test_delete_world(self):
        """Test DELETE /api/worlds/{id} endpoint"""
        if not self.created_world_id:
            self.log_test("Delete world", False, "No world ID available (create world test failed)")
            return False
            
        try:
            response = requests.delete(f"{self.base_url}/worlds/{self.created_world_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (
                    "message" in data and
                    "id" in data and
                    data["id"] == self.created_world_id
                )
                
            self.log_test("Delete world", success,
                         f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Delete world", False, f"Error: {str(e)}")
            return False
    
    def test_validation_errors(self):
        """Test API validation and error handling"""
        test_cases = [
            {
                "name": "Invalid death world level (too low)",
                "data": {"name": "Test", "death_world_level": 0},
                "expected_status": 422
            },
            {
                "name": "Invalid death world level (too high)", 
                "data": {"name": "Test", "death_world_level": 16},
                "expected_status": 422
            },
            {
                "name": "Missing required name field",
                "data": {"death_world_level": 5},
                "expected_status": 422
            }
        ]
        
        passed = 0
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/worlds",
                    json=test_case["data"],
                    timeout=10
                )
                success = response.status_code == test_case["expected_status"]
                if success:
                    passed += 1
                    
                self.log_test(test_case["name"], success,
                             f"Expected: {test_case['expected_status']}, Got: {response.status_code}")
                             
            except Exception as e:
                self.log_test(test_case["name"], False, f"Error: {str(e)}")
        
        overall_success = passed == len(test_cases)
        self.tests_run += len(test_cases)
        self.tests_passed += passed
        return overall_success
    
    def run_all_tests(self):
        """Run all API tests in logical order"""
        print(f"\n🚀 Starting QMRT API Tests - {datetime.now()}")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_root_endpoint,
            self.test_substrate_info_endpoint,
            self.test_create_world,
            self.test_list_worlds,
            self.test_get_world,
            self.test_delete_world,
            self.test_validation_errors
        ]
        
        for test in tests:
            test()
            
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend API tests PASSED!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests FAILED!")
            return 1

def main():
    """Main test execution"""
    tester = QMRTAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())