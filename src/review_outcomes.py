from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .derived_fields import (
    compute_resolution_duration_seconds as _compute_resolution_duration_seconds,
    derive_outcome_fields,
)
from .storage import DATA_DIR, read_json_list, write_json_list
from .validation import validate_post_send_followup_payload, validate_review_outcome_payload


REVIEW_OUTCOMES_PATH = DATA_DIR / "mock_review_outcomes.json"
POST_SEND_OUTCOMES_PATH = DATA_DIR / "mock_post_send_outcomes.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_review_outcomes() -> List[Dict[str, Any]]:
    rows = read_json_list(REVIEW_OUTCOMES_PATH)
    return [derive_outcome_fields(dict(row)) for row in rows]


def save_review_outcome(outcome: Dict[str, Any]) -> None:
    row = dict(outcome)
    ok, msg = validate_review_outcome(row)
    if not ok:
        raise ValueError(msg)

    rows = load_review_outcomes()
    rows = [r for r in rows if r.get("review_id") != row.get("review_id")]
    rows.append(row)
    write_json_list(REVIEW_OUTCOMES_PATH, rows)


def load_post_send_outcomes() -> List[Dict[str, Any]]:
    return read_json_list(POST_SEND_OUTCOMES_PATH)


def save_post_send_outcome(outcome: Dict[str, Any]) -> None:
    row = dict(outcome)
    ok, msg = validate_post_send_followup_payload(row)
    if not ok:
        raise ValueError(msg)

    rows = load_post_send_outcomes()
    rows = [r for r in rows if r.get("review_id") != row.get("review_id")]
    rows.append(row)
    write_json_list(POST_SEND_OUTCOMES_PATH, rows)


def clear_review_and_followup_for_review_ids(review_ids: List[str]) -> None:
    ids = set(review_ids)
    review_rows = [r for r in load_review_outcomes() if r.get("review_id") not in ids]
    post_rows = [r for r in load_post_send_outcomes() if r.get("review_id") not in ids]
    write_json_list(REVIEW_OUTCOMES_PATH, review_rows)
    write_json_list(POST_SEND_OUTCOMES_PATH, post_rows)


def derive_fields(outcome: Dict[str, Any]) -> Dict[str, Any]:
    return derive_outcome_fields(outcome)


def validate_review_outcome(outcome: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = validate_review_outcome_payload(outcome)
    if not ok:
        return False, msg
    derive_outcome_fields(outcome)
    return True, ""


def compute_resolution_duration_seconds(opened_at: str, resolved_at: str) -> int:
    return _compute_resolution_duration_seconds(opened_at, resolved_at)
