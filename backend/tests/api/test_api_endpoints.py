import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoints():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}

    r_db = client.get("/health/db")
    assert r_db.status_code == 200
    assert r_db.json().get("database") == "connected"


def test_cells_api():
    r = client.get("/api/v1/cells?district_id=wayanad&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert len(data.get("features", [])) > 0


def test_habitations_api():
    r = client.get("/api/v1/habitations?district_id=wayanad")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"

    r_table = client.get("/api/v1/habitations/priority-table?district_id=wayanad")
    assert r_table.status_code == 200
    assert isinstance(r_table.json(), list)


def test_sites_api():
    r = client.get("/api/v1/sites?district_id=wayanad")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert len(data.get("features", [])) > 0


def test_scenario_run_and_compare():
    # Run a simulation
    r_run = client.post("/api/v1/scenarios/run", json={
        "district_id": "wayanad",
        "name": "Integration Test Scenario",
        "rainfall_multiplier": 1.2,
        "solver_method": "greedy"
    })
    assert r_run.status_code == 200
    scen_id = r_run.json().get("scenario_id")
    assert scen_id is not None

    # Query assignments
    r_asgn = client.get(f"/api/v1/assignments?scenario_id={scen_id}")
    assert r_asgn.status_code == 200

    # CSV Export
    r_csv = client.get(f"/api/v1/assignments/export/csv?scenario_id={scen_id}")
    assert r_csv.status_code == 200
    assert "text/csv" in r_csv.headers.get("content-type", "")
