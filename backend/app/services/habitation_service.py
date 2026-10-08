import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from geoalchemy2.elements import WKTElement
from shapely.geometry import Point
from sqlalchemy.orm import Session

from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DataOrigin
from backend.app.database import SessionLocal
from backend.app.engines.urgency_engine import UrgencyInput, normalize_urgency_scores
from backend.app.engines.vulnerability_engine import (
    VulnerabilityInputs,
    compute_vulnerability_index,
)
from backend.app.models.habitation import Habitation
from backend.app.services.hazard_service import ensure_district_in_db

logger = get_logger(__name__)


@dataclass(frozen=True)
class DemoHabitationSeed:
    id: str
    name: str
    lon: float
    lat: float
    population: int
    households: int
    hazard_score: float
    structural_hazard: float
    active_alert: bool
    vulnerability_inputs: VulnerabilityInputs


WAYANAD_DEMO_PLACES = [
    ("chooralmala", "Chooralmala"),
    ("mundakkai", "Mundakkai"),
    ("meppadi", "Meppadi"),
    ("puthumala", "Puthumala"),
    ("vythiri", "Vythiri"),
    ("padinjarathara", "Padinjarathara"),
    ("mananthavady", "Mananthavady"),
    ("panamaram", "Panamaram"),
    ("sulthan_bathery", "Sulthan Bathery"),
    ("kalpetta", "Kalpetta"),
]


def _district_place_names(district_id: str, count: int) -> List[tuple[str, str]]:
    if district_id.lower() == "wayanad":
        return WAYANAD_DEMO_PLACES[:count]
    return [(f"hab_{idx:02d}", f"Demo Habitation {idx:02d}") for idx in range(1, count + 1)]


def generate_demo_habitations(
    district_id: str,
    count: int = 10,
    seed: int = 26191,
    active_alert: bool = False,
) -> List[DemoHabitationSeed]:
    """Generate deterministic demo habitations inside the district bbox."""
    district = load_district_config(district_id)
    minx, miny, maxx, maxy = district.bbox
    rng = random.Random(f"{district_id}:{seed}")
    names = _district_place_names(district_id, count)
    event_lon = district.historical_events[0].lon if district.historical_events else (minx + maxx) / 2.0
    event_lat = district.historical_events[0].lat if district.historical_events else (miny + maxy) / 2.0

    habitations: List[DemoHabitationSeed] = []
    for idx, (slug, name) in enumerate(names, start=1):
        if idx <= 4:
            lon = event_lon + rng.uniform(-0.06, 0.06)
            lat = event_lat + rng.uniform(-0.05, 0.05)
        else:
            lon = rng.uniform(minx + 0.02, maxx - 0.02)
            lat = rng.uniform(miny + 0.02, maxy - 0.02)
        lon = min(max(lon, minx), maxx)
        lat = min(max(lat, miny), maxy)

        population = rng.randint(90, 850)
        households = max(1, round(population / rng.uniform(3.8, 5.2)))
        event_distance = abs(lon - event_lon) + abs(lat - event_lat)
        structural_hazard = min(0.95, max(0.20, 0.88 - event_distance * 3.2 + rng.uniform(-0.08, 0.08)))
        hazard_score = min(1.0, structural_hazard * (1.18 if active_alert else 1.0))
        vulnerability = VulnerabilityInputs(
            children_under_6=rng.uniform(0.06, 0.18),
            elderly_60_plus=rng.uniform(0.07, 0.22),
            disabled_persons=rng.uniform(0.01, 0.08),
            female_headed_hh=rng.uniform(0.09, 0.32),
            kutcha_houses=rng.uniform(0.18, 0.78),
            distance_to_health_m=rng.uniform(900.0, 9000.0),
        )
        habitations.append(
            DemoHabitationSeed(
                id=f"{district_id}_hab_{slug}",
                name=name,
                lon=round(lon, 6),
                lat=round(lat, 6),
                population=population,
                households=households,
                hazard_score=round(hazard_score, 4),
                structural_hazard=round(structural_hazard, 4),
                active_alert=active_alert,
                vulnerability_inputs=vulnerability,
            )
        )
    return habitations


def score_demo_habitations(
    district_id: str,
    count: int = 10,
    seed: int = 26191,
    active_alert: bool = False,
) -> List[Dict[str, object]]:
    """Generate demo habitations and compute vulnerability, urgency, and buckets."""
    district: DistrictConfig = load_district_config(district_id)
    seeds = generate_demo_habitations(district_id, count=count, seed=seed, active_alert=active_alert)
    vulnerability_by_id = {
        item.id: compute_vulnerability_index(item.vulnerability_inputs, weights=district.weights.vulnerability)
        for item in seeds
    }
    time_factor = district.time_factors.active_alert if active_alert else district.time_factors.baseline
    urgency_results = normalize_urgency_scores(
        [
            UrgencyInput(
                id=item.id,
                hazard_score=item.hazard_score,
                structural_hazard=item.structural_hazard,
                vulnerability_index=vulnerability_by_id[item.id].vulnerability_index,
                time_factor=time_factor,
                population=item.population,
                active_alert=active_alert,
            )
            for item in seeds
        ],
        immediate_min=district.thresholds.immediate_urgency_min,
        short_term_min=district.thresholds.short_term_urgency_min,
        red_zone_min=district.thresholds.red_zone_min,
    )
    urgency_by_id = {result.id: result for result in urgency_results}

    rows: List[Dict[str, object]] = []
    for item in seeds:
        vuln = vulnerability_by_id[item.id]
        urgency = urgency_by_id[item.id]
        rows.append(
            {
                "id": item.id,
                "district_id": district_id,
                "name": item.name,
                "geometry": Point(item.lon, item.lat),
                "population": item.population,
                "households": item.households,
                "vuln_children_u6": item.vulnerability_inputs.children_under_6,
                "vuln_elderly_60p": item.vulnerability_inputs.elderly_60_plus,
                "vuln_disabled": item.vulnerability_inputs.disabled_persons,
                "vuln_female_head": item.vulnerability_inputs.female_headed_hh,
                "vuln_kutcha": item.vulnerability_inputs.kutcha_houses,
                "vuln_dist_health_m": item.vulnerability_inputs.distance_to_health_m,
                "vulnerability_index": vuln.vulnerability_index,
                "hazard_score": item.hazard_score,
                "structural_hazard": item.structural_hazard,
                "time_factor": time_factor,
                "raw_urgency_score": urgency.raw_urgency,
                "urgency_score": urgency.urgency_score,
                "bucket": urgency.bucket,
                "vulnerability_breakdown_json": {
                    "normalized_components": vuln.normalized_components,
                    "weighted_components": vuln.weighted_components,
                    "weights": vuln.weights,
                    "data_origin": DataOrigin.DEMO_SYNTHETIC.value,
                },
                "urgency_breakdown_json": urgency.breakdown,
                "decision_reasons_json": {
                    "summary": (
                        f"{item.name} is in the {urgency.bucket} bucket from hazard "
                        f"{item.hazard_score:.2f}, vulnerability {vuln.vulnerability_index:.2f}, "
                        f"time factor {time_factor:.2f}, and population {item.population}."
                    )
                },
                "data_origin": DataOrigin.DEMO_SYNTHETIC.value,
            }
        )
    return rows


def populate_demo_habitations_in_db(
    district_id: str,
    count: int = 10,
    seed: int = 26191,
    active_alert: bool = False,
    db: Optional[Session] = None,
) -> int:
    """Replace demo habitations for a district with deterministic scored rows."""
    session = db or SessionLocal()
    should_close = db is None

    try:
        ensure_district_in_db(district_id, session)
        rows = score_demo_habitations(district_id, count=count, seed=seed, active_alert=active_alert)
        session.query(Habitation).filter(
            Habitation.district_id == district_id,
            Habitation.data_origin == DataOrigin.DEMO_SYNTHETIC.value,
        ).delete()
        session.flush()

        for row in rows:
            geometry = row.pop("geometry")
            session.add(Habitation(**row, geometry=WKTElement(geometry.wkt, srid=4326)))

        session.commit()
        logger.info("Populated %s scored demo habitations for district=%s", len(rows), district_id)
        return len(rows)
    except Exception:
        session.rollback()
        logger.exception("Failed to populate demo habitations for district=%s", district_id)
        raise
    finally:
        if should_close:
            session.close()
