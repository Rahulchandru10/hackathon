import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_failure():
    # Attempting to query cases without token should return 401 Unauthorized
    response = client.get("/api/case/all")
    assert response.status_code == 401
