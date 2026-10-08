from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "Surakshit Basti"
    assert data["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_database_health_endpoint():
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "connected"
    assert "3.6" in data["postgis_version"]


def test_api_v1_status_endpoint():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["active_district"]["id"] == "wayanad"
    assert "data_sources" in data
    assert "nasa_gpm_imerg" in data["data_sources"]
    assert "copernicus_dem" in data["data_sources"]
    assert "esa_worldcover" in data["data_sources"]
    assert "openstreetmap" in data["data_sources"]
