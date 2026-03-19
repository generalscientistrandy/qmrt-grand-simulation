"""
Pytest configuration for mesoscopic API tests
"""
import pytest
import os

# Set base URL from environment
@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Ensure BASE_URL is set"""
    base_url = os.environ.get('REACT_APP_BACKEND_URL', '')
    if not base_url:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    print(f"\nUsing API base URL: {base_url}")
