from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


BEHAVIOR_CHANGE_ACTIONS = {
    "cancel",
    "edit",
    "defer",
    "adjust_start_date",
    "cancel_polypharmacy_issue",
    "choose_alternative",
    "escalate",
}

HIGH_SEVERITY = {"review_required", "block"}


def compute_resolution_duration_seconds(opened_at: str, resolved_at: str) -> int:
    opened = datetime.fromisoformat(opened_at)
    resolved = datetime.fromisoformat(resolved_at)
    return max(0, int((resolved - opened).total_seconds()))


def derive_outcome_fields(outcome: Dict[str, Any]) -> Dict[str, Any]:
    adjudication = outcome.get("clinician_adjudication")
    action = outcome.get("clinician_action_taken")
    severity = outcome.get("severity_at_open")
    if severity == "block":
        severity = "review_required"
        outcome["severity_at_open"] = severity

    outcome["is_false_positive"] = adjudication == "false_positive"
    outcome["is_behavior_change"] = action in BEHAVIOR_CHANGE_ACTIONS
    outcome["is_high_severity_confirmed_signal"] = (
        severity in HIGH_SEVERITY
        and adjudication in {"true_positive", "clinically_relevant_but_no_change"}
    )
    outcome["clinician_meaningful_duplicate"] = bool(outcome.get("clinician_meaningful_duplicate", False))
    outcome["override_used"] = bool(outcome.get("override_used", False))

    opened_at = outcome.get("opened_at")
    resolved_at = outcome.get("resolved_at")
    if opened_at and resolved_at:
        outcome["resolution_duration_seconds"] = compute_resolution_duration_seconds(opened_at, resolved_at)
    return outcome
