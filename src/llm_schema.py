from __future__ import annotations

from typing import Any, Dict, Tuple


CLASSIFICATIONS = {"true_duplicate", "likely_transition", "not_relevant", "uncertain"}
CONFIDENCE = {"high", "medium", "low"}
RECOMMENDED_SEVERITY = {"no_review_required", "review_required", "info", "block"}


def validate_classifier_output(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if payload.get("classification") not in CLASSIFICATIONS:
        return False, "invalid classification"
    rationale = payload.get("rationale")
    if not isinstance(rationale, list) or not rationale:
        return False, "rationale must be a non-empty list"
    if payload.get("confidence") not in CONFIDENCE:
        return False, "invalid confidence"
    if payload.get("recommended_severity") not in RECOMMENDED_SEVERITY:
        return False, "invalid recommended_severity"
    return True, ""


def validate_finding_llm_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not payload:
        return False, "empty payload"
    if not isinstance(payload.get("title"), str):
        return False, "missing title"
    if not isinstance(payload.get("summary"), str):
        return False, "missing summary"
    return True, ""
