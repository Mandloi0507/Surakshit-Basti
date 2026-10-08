from backend.app.services.habitation_service import score_demo_habitations


def test_demo_habitation_generation_is_deterministic():
    first = score_demo_habitations("wayanad", count=5, seed=123)
    second = score_demo_habitations("wayanad", count=5, seed=123)

    assert first == second
    assert len(first) == 5


def test_demo_habitation_scores_and_breakdowns_present():
    rows = score_demo_habitations("wayanad", count=5, seed=123, active_alert=True)

    assert all(row["data_origin"] == "DEMO_SYNTHETIC" for row in rows)
    assert all(0.0 <= row["vulnerability_index"] <= 1.0 for row in rows)
    assert all(0.0 <= row["urgency_score"] <= 1.0 for row in rows)
    assert all(row["bucket"] in {"Immediate", "Short-term", "Medium-term", "NONE"} for row in rows)
    assert "weighted_components" in rows[0]["vulnerability_breakdown_json"]
    assert "raw_urgency" in rows[0]["urgency_breakdown_json"]
