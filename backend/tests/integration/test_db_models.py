from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from backend.app.database import SessionLocal, engine
from backend.app.models import (
    District,
    Cell,
    Habitation,
    Site,
    Scenario,
    Assignment,
    CapacityNorm,
    AuditLog,
)


@pytest.fixture
def db_session():
    """Provides a transactional database session that rolls back automatically."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.mark.db
def test_district_and_cells_spatial_roundtrip(db_session: Session):
    # 1. Insert District
    district = District(
        id="test_dist_01",
        name="Test District",
        state="Kerala",
        bbox_json=[75.8, 11.5, 76.4, 12.0],
        projected_crs="EPSG:32643",
        grid_resolution_m=100,
    )
    db_session.add(district)
    db_session.flush()

    # 2. Insert Cell with Polygon geometry
    cell_wkt = "POLYGON((76.0 11.5, 76.01 11.5, 76.01 11.51, 76.0 11.51, 76.0 11.5))"
    cell = Cell(
        id="test_cell_01",
        district_id="test_dist_01",
        geometry=WKTElement(cell_wkt, srid=4326),
        slope_deg=28.5,
        hand_m=4.2,
        landslide_score=0.75,
        flood_score=0.45,
        structural_hazard=0.80,
        combined_hazard=0.86,
        hazard_class="Red",
        factor_contributions_json={"slope": 0.5, "drainage": 0.3},
        data_origin="CACHED",
    )
    db_session.add(cell)
    db_session.flush()

    # 3. Query back and verify spatial & numeric attributes
    queried_cell = db_session.query(Cell).filter(Cell.id == "test_cell_01").one()
    assert queried_cell.combined_hazard == 0.86
    assert queried_cell.hazard_class == "Red"
    assert queried_cell.slope_deg == 28.5
    assert queried_cell.district.name == "Test District"


@pytest.mark.db
def test_habitation_site_assignment_roundtrip(db_session: Session):
    # 1. Setup District
    district = District(
        id="test_dist_02",
        name="Test District 2",
        state="Kerala",
        bbox_json=[75.8, 11.5, 76.4, 12.0],
    )
    db_session.add(district)
    db_session.flush()

    # 2. Insert Site
    site_wkt = "POLYGON((76.10 11.60, 76.11 11.60, 76.11 11.61, 76.10 11.61, 76.10 11.60))"
    site = Site(
        id="test_site_01",
        district_id="test_dist_02",
        name="Safe Hill Community Center",
        geometry=WKTElement(site_wkt, srid=4326),
        tier="temporary_shelter",
        area_sqm=5000.0,
        slope_deg=4.5,
        cap_land=400,
        cap_water=350,
        cap_sanitation=500,
        cap_road=600,
        cap_services=450,
        final_capacity=350,
        limiting_factor="water",
        allocated_population=0,
        remaining_capacity=350,
        confidence_level="high",
        screening_reasons_json=["Slope < 15 deg", "Outside Red Zone"],
        data_origin="DEMO_SYNTHETIC",
    )
    db_session.add(site)

    # 3. Insert Habitation
    hab_wkt = "POINT(76.05 11.55)"
    hab = Habitation(
        id="test_hab_01",
        district_id="test_dist_02",
        name="Riverbank Settlement A",
        geometry=WKTElement(hab_wkt, srid=4326),
        population=120,
        households=28,
        vuln_children_u6=0.15,
        vuln_elderly_60p=0.12,
        vuln_disabled=0.04,
        vuln_female_head=0.20,
        vuln_kutcha=0.65,
        vuln_dist_health_m=4500.0,
        vulnerability_index=0.62,
        hazard_score=0.82,
        structural_hazard=0.79,
        time_factor=1.5,
        raw_urgency_score=4.22,
        urgency_score=0.88,
        bucket="Immediate",
        vulnerability_breakdown_json={"weighted_components": {"kutcha_houses": 0.1}},
        urgency_breakdown_json={"raw_urgency": 4.22},
        assigned_site_id="test_site_01",
        data_origin="DEMO_SYNTHETIC",
    )
    db_session.add(hab)
    db_session.flush()

    # 4. Insert Scenario & Assignment
    scenario = Scenario(
        id="test_scen_01",
        district_id="test_dist_02",
        name="Monsoon Heavy Rainfall Spike",
        rainfall_multiplier=2.0,
    )
    db_session.add(scenario)
    db_session.flush()

    assignment = Assignment(
        id="test_asgn_01",
        scenario_id="test_scen_01",
        habitation_id="test_hab_01",
        site_id="test_site_01",
        assigned_population=120,
        distance_km=4.8,
        routing_method="road_network",
        decision_rank=1,
        reasons_json=["Assigned to nearest eligible site with available capacity."],
        solver_method="greedy",
    )
    db_session.add(assignment)
    db_session.flush()

    # 5. Query and Assert Invariants
    queried_asgn = db_session.query(Assignment).filter(Assignment.id == "test_asgn_01").one()
    assert queried_asgn.assigned_population == 120
    assert queried_asgn.habitation.name == "Riverbank Settlement A"
    assert queried_asgn.site.limiting_factor == "water"
    assert queried_asgn.site.final_capacity == 350


@pytest.mark.db
def test_capacity_norms_and_audit_log(db_session: Session):
    # Insert norm
    norm = CapacityNorm(
        id="test_norm_water_01",
        norm_type="temporary",
        tier="temporary_shelter",
        resource_name="water",
        norm_value=15.0,
        unit="litres/person/day",
        source_citation="Sphere Handbook 2018",
        is_placeholder=False,
    )
    db_session.add(norm)

    # Insert audit entry
    audit = AuditLog(
        id="test_audit_01",
        user_name="Officer Sharma",
        action="threshold_slider_adjusted",
        resource_type="scenario",
        resource_id="test_scen_01",
        before_state_json={"red_threshold": 0.70},
        after_state_json={"red_threshold": 0.65},
    )
    db_session.add(audit)
    db_session.flush()

    queried_norm = db_session.query(CapacityNorm).filter(CapacityNorm.id == "test_norm_water_01").one()
    assert queried_norm.norm_value == 15.0

    queried_audit = db_session.query(AuditLog).filter(AuditLog.id == "test_audit_01").one()
    assert queried_audit.user_name == "Officer Sharma"
    assert queried_audit.after_state_json["red_threshold"] == 0.65
