import numpy as np
import pytest
from backend.app.engines.assignment_engine import (
    HabitationDemand,
    SiteSupply,
    greedy_assign,
    ilp_assign,
    validate_assignment_invariants,
)


def test_greedy_assignment_capacity_and_tie_breaking():
    habs = [
        HabitationDemand(id="h_urgent", population=100, urgency_score=0.95, vulnerability_index=0.8, bucket="Immediate"),
        HabitationDemand(id="h_low", population=100, urgency_score=0.30, vulnerability_index=0.2, bucket="Short-term"),
        HabitationDemand(id="h_safe", population=50, urgency_score=0.10, vulnerability_index=0.1, bucket="NONE"),
    ]
    # Site 1 has only 120 capacity (enough for h_urgent, not enough for both)
    sites = [
        SiteSupply(id="site_1", tier="temporary_shelter", final_capacity=120, remaining_capacity=120),
    ]
    # Distances: h_urgent is 5km away, h_low is 2km away
    dist_matrix = np.array([
        [5.0],
        [2.0],
        [1.0],
    ])

    sol = greedy_assign(habs, sites, dist_matrix)

    assert sol.total_assigned == 1
    assert sol.total_unassigned == 2

    # h_urgent assigned first due to higher urgency score despite being further away
    asgn_urgent = next(a for a in sol.assignments if a.habitation_id == "h_urgent")
    assert asgn_urgent.site_id == "site_1"
    assert asgn_urgent.assigned_population == 100

    # h_low unassigned due to insufficient capacity left (120 - 100 = 20 < 100)
    asgn_low = next(a for a in sol.assignments if a.habitation_id == "h_low")
    assert asgn_low.site_id is None
    assert asgn_low.unassigned_reason is not None

    # Invariants must hold
    violations = validate_assignment_invariants(sol, sites)
    assert len(violations) == 0


def test_ilp_assignment_invariants():
    habs = [
        HabitationDemand(id="h1", population=150, urgency_score=0.85, vulnerability_index=0.7, bucket="Immediate"),
        HabitationDemand(id="h2", population=200, urgency_score=0.75, vulnerability_index=0.6, bucket="Short-term"),
    ]
    sites = [
        SiteSupply(id="s1", tier="permanent_site", final_capacity=300, remaining_capacity=300),
        SiteSupply(id="s2", tier="permanent_site", final_capacity=300, remaining_capacity=300),
    ]
    dist_matrix = np.array([
        [10.0, 20.0],
        [15.0, 8.0],
    ])

    sol = ilp_assign(habs, sites, dist_matrix)
    assert sol.total_assigned == 2
    assert sol.total_unassigned == 0

    violations = validate_assignment_invariants(sol, sites)
    assert len(violations) == 0
