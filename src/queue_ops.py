from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


SEVERITY_WEIGHT = {
    "block": 3,
    "review_required": 2,
    "info": 1,
}

REVIEW_REASON_LABEL = {
    "duplicate_exact": "Exact duplicate",
    "duplicate_transition": "Ambiguous transition",
    "early_refill": "Early refill suppressed",
    "class_overlap_high_risk": "Same-class high risk",
    "polypharmacy_interaction": "Polypharmacy interaction",
}


def queue_reason(review_type: str) -> str:
    return REVIEW_REASON_LABEL.get(review_type, "Medication safety review")


def filter_queue_rows(rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    filtered = rows
    for key in ["severity", "review_type", "program", "status"]:
        value = filters.get(key, "all")
        if value and value != "all":
            filtered = [row for row in filtered if row.get(key) == value]

    llm_filter = filters.get("llm_mode", "all")
    if llm_filter == "claude_assisted":
        filtered = [row for row in filtered if row.get("should_invoke_llm") is True]
    elif llm_filter == "rules_only":
        filtered = [row for row in filtered if row.get("should_invoke_llm") is False]

    state_filter = filters.get("review_state", "all")
    if state_filter == "open":
        filtered = [row for row in filtered if row.get("status") == "open"]
    elif state_filter == "completed":
        filtered = [row for row in filtered if row.get("status") == "completed"]
    return filtered


def sort_queue_rows(rows: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    if sort_by == "severity":
        return sorted(rows, key=lambda x: SEVERITY_WEIGHT.get(x.get("severity", "info"), 0), reverse=True)
    if sort_by == "last_updated":
        return sorted(rows, key=lambda x: datetime.fromisoformat(x.get("updated_at", "1970-01-01T00:00:00+00:00")), reverse=True)
    if sort_by == "unresolved_first":
        return sorted(rows, key=lambda x: 0 if x.get("status") == "open" else 1)
    if sort_by == "overlap_days":
        return sorted(rows, key=lambda x: int(x.get("max_overlap_days", 0)), reverse=True)
    return rows


def build_queue_summary(rows: List[Dict[str, Any]], metrics_payload: Dict[str, Any]) -> Dict[str, Any]:
    open_reviews = sum(1 for row in rows if row.get("status") == "open")
    review_required_count = sum(1 for row in rows if row.get("severity") == "review_required")
    block_count = sum(1 for row in rows if row.get("severity") == "block")

    return {
        "open_reviews": open_reviews,
        "review_required": review_required_count,
        "block_count": block_count,
        "completed_today": sum(1 for row in rows if row.get("status") == "completed"),
        "false_positive_rate_90d": metrics_payload["metrics"].get("false_positive_rate"),
        "clinician_action_rate_90d": metrics_payload["metrics"].get("clinician_action_rate"),
    }
