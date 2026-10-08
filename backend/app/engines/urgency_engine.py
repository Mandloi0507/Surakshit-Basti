from dataclasses import dataclass
from math import log
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class UrgencyInput:
    id: str
    hazard_score: float
    structural_hazard: float
    vulnerability_index: float
    time_factor: float
    population: int
    active_alert: bool = False


@dataclass(frozen=True)
class UrgencyResult:
    id: str
    raw_urgency: float
    urgency_score: float
    bucket: str
    breakdown: Dict[str, float | bool | str]


def clamp_unit(value: float) -> float:
    """Clamp a numeric score to [0, 1]."""
    return min(1.0, max(0.0, float(value)))


def compute_raw_urgency(item: UrgencyInput) -> float:
    """Compute PRD urgency: H * (0.5 + V) * T * log(1 + P)."""
    population = max(0, int(item.population))
    return (
        clamp_unit(item.hazard_score)
        * (0.5 + clamp_unit(item.vulnerability_index))
        * max(0.0, float(item.time_factor))
        * log(1 + population)
    )


def classify_bucket(
    urgency_score: float,
    hazard_score: float,
    structural_hazard: float,
    active_alert: bool,
    immediate_min: float = 0.75,
    short_term_min: float = 0.45,
    red_zone_min: float = 0.70,
    active_alert_hazard_min: float = 0.85,
) -> str:
    """Apply PRD §16 bucket rules."""
    urgency = clamp_unit(urgency_score)
    hazard = clamp_unit(hazard_score)
    structural = clamp_unit(structural_hazard)
    if urgency >= immediate_min or (hazard >= active_alert_hazard_min and active_alert):
        return "Immediate"
    if short_term_min <= urgency < immediate_min:
        return "Short-term"
    if urgency < short_term_min and structural >= red_zone_min:
        return "Medium-term"
    return "NONE"


def normalize_urgency_scores(
    inputs: Iterable[UrgencyInput],
    immediate_min: float = 0.75,
    short_term_min: float = 0.45,
    red_zone_min: float = 0.70,
) -> List[UrgencyResult]:
    """Compute raw urgency, min-max normalise within a scenario, and assign buckets."""
    items = list(inputs)
    raw_by_id = {item.id: compute_raw_urgency(item) for item in items}
    raw_values = list(raw_by_id.values())
    min_raw = min(raw_values) if raw_values else 0.0
    max_raw = max(raw_values) if raw_values else 0.0
    span = max_raw - min_raw

    results: List[UrgencyResult] = []
    for item in items:
        raw = raw_by_id[item.id]
        normalized = 0.0 if span == 0.0 else (raw - min_raw) / span
        score = round(clamp_unit(normalized), 4)
        bucket = classify_bucket(
            score,
            item.hazard_score,
            item.structural_hazard,
            item.active_alert,
            immediate_min=immediate_min,
            short_term_min=short_term_min,
            red_zone_min=red_zone_min,
        )
        results.append(
            UrgencyResult(
                id=item.id,
                raw_urgency=round(raw, 4),
                urgency_score=score,
                bucket=bucket,
                breakdown={
                    "hazard_score": round(clamp_unit(item.hazard_score), 4),
                    "structural_hazard": round(clamp_unit(item.structural_hazard), 4),
                    "vulnerability_index": round(clamp_unit(item.vulnerability_index), 4),
                    "time_factor": round(max(0.0, float(item.time_factor)), 4),
                    "population": int(max(0, item.population)),
                    "raw_urgency": round(raw, 4),
                    "normalization_min": round(min_raw, 4),
                    "normalization_max": round(max_raw, 4),
                    "active_alert": item.active_alert,
                    "bucket": bucket,
                },
            )
        )
    return results
