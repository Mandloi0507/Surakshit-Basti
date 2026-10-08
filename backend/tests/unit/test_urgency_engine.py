from math import log

from backend.app.engines.urgency_engine import (
    UrgencyInput,
    classify_bucket,
    compute_raw_urgency,
    normalize_urgency_scores,
)


def test_raw_urgency_formula_hand_computed():
    item = UrgencyInput(
        id="hab_1",
        hazard_score=0.8,
        structural_hazard=0.8,
        vulnerability_index=0.4,
        time_factor=1.25,
        population=99,
    )

    expected = 0.8 * (0.5 + 0.4) * 1.25 * log(100)
    assert abs(compute_raw_urgency(item) - expected) < 1e-9


def test_urgency_normalization_and_bucket_rules():
    results = normalize_urgency_scores(
        [
            UrgencyInput("low", 0.20, 0.20, 0.20, 1.0, 100),
            UrgencyInput("mid", 0.65, 0.65, 0.40, 1.0, 300),
            UrgencyInput("high", 0.90, 0.80, 0.70, 1.5, 800, active_alert=True),
        ]
    )
    by_id = {result.id: result for result in results}

    assert by_id["low"].urgency_score == 0.0
    assert by_id["high"].urgency_score == 1.0
    assert by_id["high"].bucket == "Immediate"
    assert 0.0 < by_id["mid"].urgency_score < 1.0


def test_bucket_medium_term_structural_red():
    assert classify_bucket(
        urgency_score=0.30,
        hazard_score=0.30,
        structural_hazard=0.80,
        active_alert=False,
    ) == "Medium-term"


def test_bucket_short_term_threshold():
    assert classify_bucket(
        urgency_score=0.50,
        hazard_score=0.50,
        structural_hazard=0.50,
        active_alert=False,
    ) == "Short-term"


def test_active_alert_high_hazard_forces_immediate():
    assert classify_bucket(
        urgency_score=0.20,
        hazard_score=0.88,
        structural_hazard=0.60,
        active_alert=True,
    ) == "Immediate"
