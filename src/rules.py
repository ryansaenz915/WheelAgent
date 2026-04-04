from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List

from .models import DuplicateCandidate, MedicationHistoryEntry, PendingPrescriptionEvent
from .normalize import (
    normalize_history_entry,
    normalize_pharmacy_name,
    normalize_route,
    pending_ingredient,
    pending_strength,
)
from .overlap import end_date, overlap_days, pending_window

DISPENSED_LIKE_STATUSES = {"dispensed", "filled", "fill", "active"}


@dataclass
class RulesResult:
    pending_start_date: str
    pending_end_date: str
    all_rows: List[DuplicateCandidate] = field(default_factory=list)
    true_duplicate_same_drug: List[DuplicateCandidate] = field(default_factory=list)
    transition_or_duplicate: List[DuplicateCandidate] = field(default_factory=list)
    low_info_rows: List[DuplicateCandidate] = field(default_factory=list)
    supporting_rows: List[DuplicateCandidate] = field(default_factory=list)
    max_overlap_days: int = 0
    multi_pharmacy_risk_amplifier: bool = False
    triggered_rules: List[str] = field(default_factory=list)

    def trace(self) -> Dict[str, object]:
        return {
            "pending_start_date": self.pending_start_date,
            "pending_end_date": self.pending_end_date,
            "candidate_rows_considered": [row.to_trace() for row in self.all_rows],
            "multi_pharmacy_risk_amplifier": self.multi_pharmacy_risk_amplifier,
            "max_overlap_days": self.max_overlap_days,
            "triggered_rules": self.triggered_rules,
        }


def apply_rules(
    event: PendingPrescriptionEvent,
    history_rows: List[MedicationHistoryEntry],
) -> RulesResult:
    pending_start, pending_end = pending_window(event.event_time.date(), event.prescription.days_supply)
    expected_ingredient = pending_ingredient(event)
    expected_strength = pending_strength(event)
    expected_route = normalize_route(event.prescription.route)
    pending_pharmacy = normalize_pharmacy_name(event.pharmacy.name)

    result = RulesResult(
        pending_start_date=pending_start.isoformat(),
        pending_end_date=pending_end.isoformat(),
    )

    same_ingredient_recent: List[DuplicateCandidate] = []

    for raw in history_rows:
        row = normalize_history_entry(raw)
        supply_end = end_date(row.fill_date, row.days_supply)
        overlap = overlap_days(pending_start, pending_end, row.fill_date, supply_end)
        same_ingredient = row.ingredient == expected_ingredient
        same_route = row.route == expected_route
        same_strength = bool(row.strength) and bool(expected_strength) and row.strength == expected_strength
        status_ok = row.status in DISPENSED_LIKE_STATUSES
        different_pharmacy = normalize_pharmacy_name(row.pharmacy) != pending_pharmacy

        candidate = DuplicateCandidate(
            drug_display=row.drug_display,
            ingredient=row.ingredient,
            strength=row.strength,
            route=row.route,
            fill_date=row.fill_date,
            days_supply=row.days_supply,
            status=row.status,
            pharmacy=row.pharmacy,
            supply_end_date=supply_end,
            overlap_days=overlap,
            same_ingredient=same_ingredient,
            same_route=same_route,
            same_strength=same_strength,
            different_pharmacy=different_pharmacy,
            classification="ignored",
            llm_needed=False,
            rules_triggered=[],
            ignore_reasons=[],
            risk_amplifier=False,
        )

        if same_ingredient and status_ok and row.fill_date >= pending_start - timedelta(days=60):
            same_ingredient_recent.append(candidate)

        if not same_ingredient:
            candidate.ignore_reasons.append("ingredient_mismatch")
            result.all_rows.append(candidate)
            continue
        if not same_route:
            candidate.ignore_reasons.append("route_mismatch")
            result.all_rows.append(candidate)
            continue
        if not status_ok:
            candidate.ignore_reasons.append("status_not_dispensed_like")
            result.all_rows.append(candidate)
            continue

        candidate.rules_triggered.append("A_relevance_filter_pass")
        if same_strength and overlap >= 4:
            candidate.classification = "true_duplicate_same_drug"
            candidate.rules_triggered.append("B_exact_duplicate_candidate")
            result.true_duplicate_same_drug.append(candidate)
        elif (not same_strength) and overlap > 0:
            candidate.classification = "transition_or_duplicate"
            candidate.rules_triggered.append("C_ambiguous_transition_candidate")
            candidate.llm_needed = True
            result.transition_or_duplicate.append(candidate)
        elif overlap == 0 and supply_end >= pending_start - timedelta(days=7):
            candidate.classification = "recent_non_overlap_info"
            candidate.rules_triggered.append("D_recent_non_overlap_info")
            result.low_info_rows.append(candidate)
        else:
            candidate.ignore_reasons.append("non_overlap_not_recent")

        result.all_rows.append(candidate)

    unique_pharmacies = {
        normalize_pharmacy_name(c.pharmacy)
        for c in same_ingredient_recent
        if normalize_pharmacy_name(c.pharmacy) != "unknown"
    }
    result.multi_pharmacy_risk_amplifier = len(unique_pharmacies) >= 2
    for c in same_ingredient_recent:
        c.risk_amplifier = result.multi_pharmacy_risk_amplifier
    result.supporting_rows = same_ingredient_recent
    result.max_overlap_days = max(
        [0] + [x.overlap_days for x in result.true_duplicate_same_drug + result.transition_or_duplicate]
    )
    result.triggered_rules = [
        "A_relevance_filter",
        "B_exact_duplicate_candidate",
        "C_ambiguous_transition_candidate",
        "D_recent_non_overlap_info",
        "E_multi_pharmacy_amplifier" if result.multi_pharmacy_risk_amplifier else "E_multi_pharmacy_not_triggered",
    ]
    return result
