"""
Clean pytest tests for ML service
"""
import pytest
from fastapi.testclient import TestClient
import json

# Import the app directly
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from app.main import app
except ImportError:
    # Fallback for different import paths
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "main", 
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "main.py")
    )
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)
    app = main.app

@pytest.fixture
def client():
    return TestClient(app)

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_recommendations(client):
    response = client.get("/recommendations/user/1?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert len(data["recommendations"]) == 3

def test_interactions(client):
    payload = {"user_id": 1, "item_id": 2, "interaction_type": "view"}
    response = client.post("/interactions", json=payload)
    assert response.status_code == 200