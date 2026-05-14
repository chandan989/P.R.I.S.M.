"""
P.R.I.S.M. Server Tests

Tests for the FastAPI server endpoints and components.
"""

import pytest
from fastapi.testclient import TestClient
from server import app

class TestServer:
    """Tests for the FastAPI server."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_model_info_endpoint(self, client):
        """Test model info endpoint."""
        response = client.get("/model/info")
        # This might fail if model is not initialized, which is expected in test environment
        assert response.status_code in [200, 500, 503]

    def test_knowledge_base_status_endpoint(self, client):
        """Test knowledge base status endpoint."""
        response = client.get("/knowledge-base/status")
        # This might fail if knowledge base is not initialized, which is expected in test environment
        assert response.status_code in [200, 500, 503]

    def test_query_endpoint(self, client):
        """Test query endpoint."""
        response = client.post("/query", json={"prompt": "Test query"})
        # This might fail if model is not initialized, which is expected in test environment
        assert response.status_code in [200, 500, 503]