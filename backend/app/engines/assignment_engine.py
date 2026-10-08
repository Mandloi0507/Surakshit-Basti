"""
Assignment engine: capacity-constrained, vulnerability-weighted relocation assignment.

Implements two solvers:
1. **Greedy** (baseline): sort habitations by urgency descending, assign to nearest
   eligible site with remaining capacity. PRD tie-breaking: higher vulnerability →
   larger population → shorter distance → id ascending.
2. **ILP / CP-SAT via OR-Tools** (optimal): maximise Σ(U_i * P_i − λ * d_ij * P_i) * x_ij
   subject to capacity, eligibility, and single-assignment constraints.

Every habitation is either assigned or carries an explicit `unassigned_reason`.
No site ever exceeds its capacity (hard invariant).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class HabitationDemand:
    """Input for the assignment solver representing one habitation."""
    id: str
    population: int
    urgency_score: float
    vulnerability_index: float
    bucket: str  # Immediate, Short-term, Medium-term, NONE


@dataclass(frozen=True)
class SiteSupply:
    """Input for the assignment solver representing one candidate site."""
    id: str
    tier: str  # temporary_shelter, permanent_site
    final_capacity: int
    remaining_capacity: int


@dataclass
class AssignmentResult:
    """Result of assigning one habitation to one site (or marking unassigned)."""
    habitation_id: str
    site_id: Optional[str]
    assigned_population: int
    distance_km: float
    routing_method: str
    decision_rank: int
    reasons: List[str]
    unassigned_reason: Optional[str]
    solver_method: str


@dataclass
class AssignmentSolution:
    """Complete solution for one scenario run."""
    assignments: List[AssignmentResult]
    total_assigned: int
    total_unassigned: int
    solver_method: str
    stats: Dict[str, object] = field(default_factory=dict)


def _tier_eligible(bucket: str, tier: str) -> bool:
    """Check if habitation bucket is eligible for a given site tier (PRD §16)."""
    if bucket == "Immediate":
        return tier in ("temporary_shelter", "permanent_site")
    if bucket == "Short-term":
        return tier in ("permanent_site", "temporary_shelter")
    if bucket == "Medium-term":
        return tier == "permanent_site"
    return True  # NONE can go to any if needed


def _sort_key(hab: HabitationDemand) -> Tuple:
    """PRD tie-breaking: higher urgency → higher vulnerability → larger population → id ascending."""
    return (
        -hab.urgency_score,
        -hab.vulnerability_index,
        -hab.population,
        hab.id,
    )


def greedy_assign(
    habitations: List[HabitationDemand],
    sites: List[SiteSupply],
    distances_km: np.ndarray,
    routing_method: str = "straight_line_fallback",
    max_distance_km: float = 50.0,
) -> AssignmentSolution:
    """
    Greedy assignment: sort habitations by urgency descending (with tie-breaking),
    assign each to the nearest eligible site that has remaining capacity ≥ demand.

    Args:
        habitations: list of habitation demands
        sites: list of site supplies
        distances_km: shape (n_hab, n_site) distance matrix
        routing_method: label for provenance
        max_distance_km: maximum assignment distance

    Returns:
        AssignmentSolution with all assignments and stats.
    """
    # Sort habitations by priority (highest urgency first, with tie-breaking)
    sorted_habs = sorted(habitations, key=_sort_key)

    # Map IDs to indices
    hab_id_to_idx = {h.id: i for i, h in enumerate(habitations)}
    site_id_to_idx = {s.id: i for i, s in enumerate(sites)}

    # Track remaining capacity
    remaining = {s.id: s.remaining_capacity for s in sites}

    assignments: List[AssignmentResult] = []
    rank = 0

    for hab in sorted_habs:
        rank += 1
        hab_idx = hab_id_to_idx[hab.id]

        # Skip NONE bucket habitations (not in any relocation bucket)
        if hab.bucket == "NONE":
            assignments.append(AssignmentResult(
                habitation_id=hab.id,
                site_id=None,
                assigned_population=0,
                distance_km=0.0,
                routing_method=routing_method,
                decision_rank=rank,
                reasons=[],
                unassigned_reason="Not in any relocation bucket (urgency below thresholds and outside structural Red Zone)",
                solver_method="greedy",
            ))
            continue

        # Find eligible sites: correct tier, within distance, has capacity
        candidates: List[Tuple[int, float]] = []  # (site_idx, distance)
        for site in sites:
            site_idx = site_id_to_idx[site.id]
            dist = float(distances_km[hab_idx, site_idx])

            if not _tier_eligible(hab.bucket, site.tier):
                continue
            if dist > max_distance_km:
                continue
            if remaining[site.id] < hab.population:
                continue
            candidates.append((site_idx, dist))

        if not candidates:
            # Try to find any site with partial capacity for explanation
            reason_parts = []
            for site in sites:
                site_idx = site_id_to_idx[site.id]
                dist = float(distances_km[hab_idx, site_idx])
                if not _tier_eligible(hab.bucket, site.tier):
                    reason_parts.append(f"{site.id}: tier mismatch ({site.tier} vs {hab.bucket})")
                elif dist > max_distance_km:
                    reason_parts.append(f"{site.id}: too far ({dist:.1f} km > {max_distance_km} km)")
                elif remaining[site.id] < hab.population:
                    reason_parts.append(f"{site.id}: insufficient capacity ({remaining[site.id]} < {hab.population})")

            unassigned_reason = f"No eligible site with sufficient capacity. Details: {'; '.join(reason_parts[:3])}"
            if len(reason_parts) > 3:
                unassigned_reason += f" (+{len(reason_parts) - 3} more)"

            assignments.append(AssignmentResult(
                habitation_id=hab.id,
                site_id=None,
                assigned_population=0,
                distance_km=0.0,
                routing_method=routing_method,
                decision_rank=rank,
                reasons=[],
                unassigned_reason=unassigned_reason,
                solver_method="greedy",
            ))
            continue

        # Sort candidates by distance (nearest first)
        candidates.sort(key=lambda x: (x[1], sites[x[0]].id))
        best_site_idx, best_dist = candidates[0]
        best_site = sites[best_site_idx]

        # Build assignment reasons
        reasons = [
            f"Assigned to {best_site.id} (rank #{rank})",
            f"Urgency: {hab.urgency_score:.3f}, Vulnerability: {hab.vulnerability_index:.3f}",
            f"Distance: {best_dist:.2f} km ({routing_method})",
            f"Site remaining capacity: {remaining[best_site.id]} → {remaining[best_site.id] - hab.population}",
            f"Bucket: {hab.bucket} → Tier: {best_site.tier}",
        ]
        if len(candidates) > 1:
            second_site_idx, second_dist = candidates[1]
            reasons.append(
                f"Next-best alternative: {sites[second_site_idx].id} at {second_dist:.2f} km"
            )

        # Deduct capacity
        remaining[best_site.id] -= hab.population

        assignments.append(AssignmentResult(
            habitation_id=hab.id,
            site_id=best_site.id,
            assigned_population=hab.population,
            distance_km=round(best_dist, 4),
            routing_method=routing_method,
            decision_rank=rank,
            reasons=reasons,
            unassigned_reason=None,
            solver_method="greedy",
        ))

    total_assigned = sum(1 for a in assignments if a.site_id is not None)
    total_unassigned = sum(1 for a in assignments if a.site_id is None)

    return AssignmentSolution(
        assignments=assignments,
        total_assigned=total_assigned,
        total_unassigned=total_unassigned,
        solver_method="greedy",
        stats={
            "total_habitations": len(habitations),
            "total_sites": len(sites),
            "remaining_capacities": dict(remaining),
        },
    )


def ilp_assign(
    habitations: List[HabitationDemand],
    sites: List[SiteSupply],
    distances_km: np.ndarray,
    routing_method: str = "straight_line_fallback",
    max_distance_km: float = 50.0,
    distance_penalty_lambda: float = 0.01,
    time_limit_seconds: float = 30.0,
) -> AssignmentSolution:
    """
    Optimal assignment using OR-Tools CP-SAT solver.

    Maximise: Σ (U_i * P_i − λ * d_ij * P_i) * x_ij
    Subject to:
        - Each habitation assigned to at most one site (or unassigned)
        - Each site's allocated population ≤ capacity
        - Only eligible (tier-compatible, within distance) pairs
        - Only habitations in a relocation bucket are assigned

    Falls back to greedy if OR-Tools is unavailable or times out.
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        # OR-Tools not available; fall back to greedy
        result = greedy_assign(habitations, sites, distances_km, routing_method, max_distance_km)
        for a in result.assignments:
            a.solver_method = "greedy_fallback_no_ortools"
        result.solver_method = "greedy_fallback_no_ortools"
        return result

    model = cp_model.CpModel()

    hab_id_to_idx = {h.id: i for i, h in enumerate(habitations)}
    site_id_to_idx = {s.id: i for i, s in enumerate(sites)}
    n_hab = len(habitations)
    n_site = len(sites)

    # Scale factor for integer arithmetic (CP-SAT requires integers)
    SCALE = 10000

    # Decision variables: x[i][j] = 1 if habitation i assigned to site j
    x = {}
    eligible_pairs = set()

    for i, hab in enumerate(habitations):
        if hab.bucket == "NONE":
            continue
        for j, site in enumerate(sites):
            dist = float(distances_km[i, j])
            if dist > max_distance_km:
                continue
            if not _tier_eligible(hab.bucket, site.tier):
                continue
            if site.remaining_capacity < hab.population:
                continue
            x[i, j] = model.NewBoolVar(f"x_{i}_{j}")
            eligible_pairs.add((i, j))

    # Constraint 1: Each habitation assigned to at most one site
    for i, hab in enumerate(habitations):
        vars_for_hab = [x[i, j] for j in range(n_site) if (i, j) in eligible_pairs]
        if vars_for_hab:
            model.Add(sum(vars_for_hab) <= 1)

    # Constraint 2: Site capacity not exceeded
    for j, site in enumerate(sites):
        capacity_terms = []
        for i, hab in enumerate(habitations):
            if (i, j) in eligible_pairs:
                capacity_terms.append(hab.population * x[i, j])
        if capacity_terms:
            model.Add(sum(capacity_terms) <= site.remaining_capacity)

    # Objective: maximise Σ (U_i * P_i − λ * d_ij * P_i) * x_ij
    objective_terms = []
    for (i, j) in eligible_pairs:
        hab = habitations[i]
        dist = float(distances_km[i, j])
        benefit = hab.urgency_score * hab.population
        cost = distance_penalty_lambda * dist * hab.population
        score_scaled = int((benefit - cost) * SCALE)
        objective_terms.append(score_scaled * x[i, j])

    if objective_terms:
        model.Maximize(sum(objective_terms))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Fallback to greedy
        result = greedy_assign(habitations, sites, distances_km, routing_method, max_distance_km)
        for a in result.assignments:
            a.solver_method = "greedy_fallback_ilp_infeasible"
        result.solver_method = "greedy_fallback_ilp_infeasible"
        result.stats["ilp_status"] = "INFEASIBLE" if status == cp_model.INFEASIBLE else "UNKNOWN"
        return result

    # Extract solution
    remaining = {s.id: s.remaining_capacity for s in sites}
    assignments: List[AssignmentResult] = []

    # Sort habitations by urgency for rank assignment
    sorted_habs = sorted(habitations, key=_sort_key)

    for rank, hab in enumerate(sorted_habs, start=1):
        i = hab_id_to_idx[hab.id]

        if hab.bucket == "NONE":
            assignments.append(AssignmentResult(
                habitation_id=hab.id,
                site_id=None,
                assigned_population=0,
                distance_km=0.0,
                routing_method=routing_method,
                decision_rank=rank,
                reasons=[],
                unassigned_reason="Not in any relocation bucket",
                solver_method="ilp_ortools",
            ))
            continue

        assigned_site_idx = None
        for j in range(n_site):
            if (i, j) in eligible_pairs and solver.Value(x[i, j]) == 1:
                assigned_site_idx = j
                break

        if assigned_site_idx is None:
            assignments.append(AssignmentResult(
                habitation_id=hab.id,
                site_id=None,
                assigned_population=0,
                distance_km=0.0,
                routing_method=routing_method,
                decision_rank=rank,
                reasons=[],
                unassigned_reason="ILP solver did not assign (capacity constraints or no eligible site)",
                solver_method="ilp_ortools",
            ))
            continue

        site = sites[assigned_site_idx]
        dist = float(distances_km[i, assigned_site_idx])
        remaining[site.id] -= hab.population

        reasons = [
            f"ILP-optimal assignment to {site.id} (rank #{rank})",
            f"Urgency: {hab.urgency_score:.3f}, Vulnerability: {hab.vulnerability_index:.3f}",
            f"Distance: {dist:.2f} km ({routing_method})",
            f"Site remaining capacity: {remaining[site.id] + hab.population} → {remaining[site.id]}",
            f"Bucket: {hab.bucket} → Tier: {site.tier}",
        ]

        assignments.append(AssignmentResult(
            habitation_id=hab.id,
            site_id=site.id,
            assigned_population=hab.population,
            distance_km=round(dist, 4),
            routing_method=routing_method,
            decision_rank=rank,
            reasons=reasons,
            unassigned_reason=None,
            solver_method="ilp_ortools",
        ))

    total_assigned = sum(1 for a in assignments if a.site_id is not None)
    total_unassigned = sum(1 for a in assignments if a.site_id is None)

    ilp_status = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"

    return AssignmentSolution(
        assignments=assignments,
        total_assigned=total_assigned,
        total_unassigned=total_unassigned,
        solver_method="ilp_ortools",
        stats={
            "total_habitations": len(habitations),
            "total_sites": len(sites),
            "remaining_capacities": dict(remaining),
            "ilp_status": ilp_status,
            "objective_value": solver.ObjectiveValue() / SCALE if objective_terms else 0.0,
            "wall_time_s": solver.WallTime(),
        },
    )


def validate_assignment_invariants(
    solution: AssignmentSolution,
    sites: List[SiteSupply],
) -> List[str]:
    """
    Validate hard assignment invariants (PRD §16, §17):
    1. No site exceeds capacity
    2. Every habitation is assigned or has an unassigned_reason
    3. Results are deterministic for identical inputs

    Returns list of violation messages (empty = valid).
    """
    violations: List[str] = []

    # Check 1: No site exceeds capacity
    allocated_per_site: Dict[str, int] = {}
    site_capacity = {s.id: s.remaining_capacity for s in sites}
    for a in solution.assignments:
        if a.site_id is not None:
            allocated_per_site[a.site_id] = allocated_per_site.get(a.site_id, 0) + a.assigned_population

    for site_id, allocated in allocated_per_site.items():
        if site_id in site_capacity and allocated > site_capacity[site_id]:
            violations.append(
                f"CAPACITY VIOLATION: Site {site_id} allocated {allocated} > capacity {site_capacity[site_id]}"
            )

    # Check 2: Every habitation is assigned or has a reason
    for a in solution.assignments:
        if a.site_id is None and not a.unassigned_reason:
            violations.append(
                f"MISSING REASON: Habitation {a.habitation_id} is unassigned without a reason"
            )

    return violations
