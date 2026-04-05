from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple


REVIEW_TYPES = {
    "duplicate_exact",
    "duplicate_transition",
    "early_refill",
    "class_overlap_high_risk",
    "polypharmacy_interaction",
}

SEVERITIES = {"info", "review_required", "block"}
DUPLICATE_TYPES = {"same_drug_same_strength", "same_drug_diff_strength", "same_class", "other"}
ADJUDICATIONS = {"true_positive", "false_positive", "clinically_relevant_but_no_change", "uncertain"}


def _missing(data: Dict[str, Any], required: Iterable[str]) -> List[str]:
    return [key for key in required if key not in data]


def validate_case_fixture(case: Dict[str, Any]) -> Tuple[bool, str]:
    required_case = ["review_id", "review_type", "pending_rx", "med_history", "queue"]
    missing = _missing(case, required_case)
    if missing:
        return False, f"case fixture missing fields: {', '.join(missing)}"

    if case["review_type"] not in REVIEW_TYPES:
        return False, f"invalid review_type: {case['review_type']}"

    queue = case["queue"]
    missing_queue = _missing(queue, ["severity", "status", "program", "updated_at"])
    if missing_queue:
        return False, f"case queue metadata missing fields: {', '.join(missing_queue)}"

    if queue["severity"] not in SEVERITIES:
        return False, f"invalid queue severity: {queue['severity']}"

    return True, ""


def validate_review_outcome_payload(outcome: Dict[str, Any], require_interruptive_fields: bool = True) -> Tuple[bool, str]:
    required = [
        "review_id",
        "severity_at_open",
        "duplicate_type",
        "opened_at",
        "resolved_at",
    ]
    missing = _missing(outcome, required)
    if missing:
        return False, f"review outcome missing fields: {', '.join(missing)}"

    review_type = outcome.get("review_type") or outcome.get("case_type")
    if not review_type:
        return False, "review_type or case_type is required"
    if review_type not in REVIEW_TYPES:
        return False, f"invalid review_type: {review_type}"
    outcome["review_type"] = review_type

    severity = outcome.get("severity_at_open")
    if severity not in SEVERITIES:
        return False, f"invalid severity_at_open: {severity}"

    duplicate_type = outcome.get("duplicate_type")
    if duplicate_type not in DUPLICATE_TYPES:
        return False, f"invalid duplicate_type: {duplicate_type}"

    adjudication = outcome.get("clinician_adjudication")
    if adjudication and adjudication not in ADJUDICATIONS:
        return False, f"invalid clinician_adjudication: {adjudication}"

    interruptive = severity in {"review_required", "block"}
    if require_interruptive_fields and interruptive:
        if not outcome.get("clinician_adjudication"):
            return False, "clinician_adjudication is required"
        if not outcome.get("clinician_action_taken"):
            return False, "clinician_action_taken is required"

    if outcome.get("override_used") and not outcome.get("override_reason_code"):
        return False, "override_reason_code is required when override_used=true"

    return True, ""


def validate_post_send_followup_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    required = ["review_id", "finding_id", "sent_at", "followup_recorded_at", "duplicate_related_issue", "issue_type"]
    missing = _missing(payload, required)
    if missing:
        return False, f"post-send follow-up missing fields: {', '.join(missing)}"
    return True, ""


def validate_metrics_filters(filters: Dict[str, Any]) -> Tuple[bool, str]:
    if filters.get("severity") and filters["severity"] not in (SEVERITIES | {"all"}):
        return False, f"invalid severity filter: {filters['severity']}"
    if filters.get("review_type") and filters["review_type"] not in (REVIEW_TYPES | {"all"}):
        return False, f"invalid review_type filter: {filters['review_type']}"
    return True, ""


def validate_report_payload(report: Dict[str, Any]) -> Tuple[bool, str]:
    required = ["sections", "workflow_steps", "rules_vs_ai", "metric_cards", "assignment_feature_matrix"]
    missing = _missing(report, required)
    if missing:
        return False, f"report payload missing fields: {', '.join(missing)}"
    return True, ""
