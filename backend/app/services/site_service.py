"""
Site service: generates demo candidate relocation sites, runs GIS screening,
computes multi-resource carrying capacity, and persists to PostGIS.
"""
import random
from math import floor
from typing import Dict, List, Optional

import yaml
from geoalchemy2.elements import WKTElement
from shapely.geometry import Point
from sqlalchemy.orm import Session

from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DataOrigin
from backend.app.core.settings import get_settings
from backend.app.database import SessionLocal
from backend.app.engines.capacity_engine import (
    CapacityNorms,
    CapacityResult,
    ScreeningResult,
    ScreeningThresholds,
    SiteResourceInputs,
    SiteScreeningInput,
    compute_capacity,
    screen_site,
    tier_from_capacity,
)
from backend.app.models.site import Site
from backend.app.services.hazard_service import ensure_district_in_db

logger = get_logger(__name__)


def load_capacity_norms(tier: str = "temporary_shelter") -> CapacityNorms:
    """Load capacity norms from config/capacity_norms.yaml for the specified tier."""
    settings = get_settings()
    config_file = settings.CONFIG_PATH / "capacity_norms.yaml"
    if not config_file.exists():
        logger.warning("capacity_norms.yaml not found at %s, using engine defaults", config_file)
        return CapacityNorms(
            land_sqm_per_person=12.0,
            water_litres_per_person_day=15.0,
            sanitation_persons_per_toilet=20.0,
            road_persons_per_m_width=120.0,
            service_person_capacity=300,
            usable_land_fraction=0.65,
        )
    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    tier_data = data.get(tier, data.get("temporary_shelter", {}))
    return CapacityNorms(
        land_sqm_per_person=float(tier_data.get("land_sqm_per_person", {}).get("value", 12.0)),
        water_litres_per_person_day=float(tier_data.get("water_litres_per_person_day", {}).get("value", 15.0)),
        sanitation_persons_per_toilet=float(tier_data.get("sanitation_persons_per_toilet", {}).get("value", 20.0)),
        road_persons_per_m_width=float(tier_data.get("road_persons_per_m_width", {}).get("value", 120.0)),
        service_person_capacity=int(tier_data.get("service_person_capacity", {}).get("value", 300)),
        usable_land_fraction=float(tier_data.get("usable_land_fraction", {}).get("value", 0.65)),
    )


# Wayanad demo sites: real-world-inspired safe locations (lower slopes, away from event zones)
WAYANAD_DEMO_SITES = [
    ("kalpetta_ground", "Kalpetta Town Ground", 76.0780, 11.6087),
    ("sulthan_bathery_ground", "Sulthan Bathery Parade Ground", 76.2640, 11.6630),
    ("mananthavady_site", "Mananthavady Relief Camp", 76.0060, 11.8040),
    ("panamaram_field", "Panamaram Open Field", 76.0770, 11.7350),
    ("meenangadi_ground", "Meenangadi Community Ground", 76.1640, 11.6230),
    ("poothadi_site", "Poothadi Transit Site", 76.0340, 11.7750),
    ("pulpally_ground", "Pulpally School Ground", 76.1790, 11.7930),
    ("ambalavayal_site", "Ambalavayal Heritage Site Area", 76.2180, 11.6330),
]


def generate_demo_sites(
    district_id: str,
    count: int = 8,
    seed: int = 26191,
) -> List[Dict[str, object]]:
    """Generate deterministic demo candidate relocation sites for a district."""
    district: DistrictConfig = load_district_config(district_id)
    minx, miny, maxx, maxy = district.bbox
    rng = random.Random(f"{district_id}_sites:{seed}")

    if district_id.lower() == "wayanad":
        place_names = WAYANAD_DEMO_SITES[:count]
    else:
        place_names = [
            (f"site_{idx:02d}", f"Demo Site {idx:02d}", 
             rng.uniform(minx + 0.03, maxx - 0.03),
             rng.uniform(miny + 0.03, maxy - 0.03))
            for idx in range(1, count + 1)
        ]

    sites: List[Dict[str, object]] = []
    for idx, (slug, name, lon, lat) in enumerate(place_names, start=1):
        lon = min(max(lon, minx), maxx)
        lat = min(max(lat, miny), maxy)

        # Deterministic pseudo-attributes for screening
        area_sqm = rng.uniform(3000.0, 25000.0)
        slope_deg = rng.uniform(1.0, 12.0)  # Candidate sites should have low slopes
        dist_road_m = rng.uniform(50.0, 800.0)
        dist_water_m = rng.uniform(100.0, 1200.0)
        hazard_score = rng.uniform(0.05, 0.35)  # Sites should be in safe zones

        # LULC: most sites on barren/scrub/grassland (eligible) or some on tree cover (marginal)
        lulc_options = ["barren", "scrub", "grassland", "grassland", "barren", "scrub", "herbaceous", "tree cover"]
        land_cover = lulc_options[idx % len(lulc_options)]

        # Resource inputs for capacity computation
        water_litres = rng.uniform(500.0, 5000.0)
        toilets = rng.randint(5, 40)
        road_width = rng.uniform(3.0, 8.0)
        service_cap = rng.randint(100, 600)

        # Run screening
        screening_input = SiteScreeningInput(
            slope_deg=slope_deg,
            hazard_score=hazard_score,
            land_cover=land_cover,
            dist_road_m=dist_road_m,
            dist_water_m=dist_water_m,
            protected_or_wetland=False,
        )
        screening: ScreeningResult = screen_site(screening_input)

        # Compute capacity (per tier)
        tier = "temporary_shelter" if screening.is_eligible else "permanent_site"
        norms = load_capacity_norms(tier)
        resource_inputs = SiteResourceInputs(
            area_sqm=area_sqm,
            water_litres_day=water_litres,
            toilets=toilets,
            road_width_m=road_width,
            service_capacity=service_cap,
        )
        capacity: CapacityResult = compute_capacity(resource_inputs, norms)

        # Auto-tier based on capacity
        tier = tier_from_capacity(capacity.final_capacity)

        site_id = f"{district_id}_site_{slug}"
        sites.append({
            "id": site_id,
            "district_id": district_id,
            "name": name,
            "geometry": Point(lon, lat),
            "tier": tier,
            "area_sqm": round(area_sqm, 1),
            "slope_deg": round(slope_deg, 2),
            "dist_road_m": round(dist_road_m, 1),
            "dist_water_m": round(dist_water_m, 1),
            "cap_land": capacity.cap_land,
            "cap_water": capacity.cap_water,
            "cap_sanitation": capacity.cap_sanitation,
            "cap_road": capacity.cap_road,
            "cap_services": capacity.cap_services,
            "final_capacity": capacity.final_capacity,
            "limiting_factor": capacity.limiting_factor,
            "allocated_population": 0,
            "remaining_capacity": capacity.final_capacity,
            "confidence_level": screening.confidence_level,
            "screening_reasons_json": screening.reasons + (
                [f"REJECTION: {r}" for r in screening.rejections] if screening.rejections else []
            ),
            "data_origin": DataOrigin.DEMO_SYNTHETIC.value,
        })

    return sites


def populate_demo_sites_in_db(
    district_id: str,
    count: int = 8,
    seed: int = 26191,
    db: Optional[Session] = None,
) -> int:
    """Replace demo sites for a district with deterministic screened and capacity-scored rows."""
    session = db or SessionLocal()
    should_close = db is None

    try:
        ensure_district_in_db(district_id, session)
        rows = generate_demo_sites(district_id, count=count, seed=seed)

        session.query(Site).filter(
            Site.district_id == district_id,
            Site.data_origin == DataOrigin.DEMO_SYNTHETIC.value,
        ).delete()
        session.flush()

        for row in rows:
            geometry = row.pop("geometry")
            session.add(Site(**row, geometry=WKTElement(geometry.wkt, srid=4326)))

        session.commit()
        logger.info("Populated %s demo sites for district=%s", len(rows), district_id)
        return len(rows)
    except Exception:
        session.rollback()
        logger.exception("Failed to populate demo sites for district=%s", district_id)
        raise
    finally:
        if should_close:
            session.close()
