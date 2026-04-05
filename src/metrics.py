from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Dict, List

from .validation import validate_metrics_filters


def _in_window(iso_ts: str, cutoff: datetime) -> bool:
    if not iso_ts:
        return False
    return datetime.fromisoformat(iso_ts) >= cutoff


def _safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return num / den


def _window_days(window: str) -> int:
    return {"7d": 7, "30d": 30, "90d": 90, "all": 36500}.get(window, 90)


def _apply_filters(rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    ok, msg = validate_metrics_filters(filters)
    if not ok:
        raise ValueError(msg)

    out = rows
    for key in ["severity", "review_type", "program", "duplicate_type"]:
        val = filters.get(key, "all")
        if val and val != "all":
            mapped_key = "severity_at_open" if key == "severity" else key
            out = [r for r in out if r.get(mapped_key) == val]

    llm_filter = filters.get("llm_mode", "all")
    if llm_filter == "claude_assisted":
        out = [r for r in out if r.get("used_llm") is True]
    elif llm_filter == "rules_only":
        out = [r for r in out if r.get("used_llm") is False]

    return out


def _segment_counts(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    segment_counts: Dict[str, Dict[str, int]] = {
        "severity": {},
        "case_type": {},
        "program": {},
        "used_llm": {},
        "review_type": {},
        "clinician_action_taken": {},
        "duplicate_type": {},
        "adjudication": {},
    }
    for r in rows:
        values = {
            "severity": r.get("severity_at_open", "unknown"),
            "case_type": r.get("case_type", "unknown"),
            "program": r.get("program", "unknown"),
            "used_llm": str(r.get("used_llm", "unknown")),
            "review_type": r.get("review_type", "unknown"),
            "clinician_action_taken": r.get("clinician_action_taken", "unknown"),
            "duplicate_type": r.get("duplicate_type", "unknown"),
            "adjudication": r.get("clinician_adjudication", "unknown"),
        }
        for key, val in values.items():
            s_val = str(val)
            segment_counts[key][s_val] = segment_counts[key].get(s_val, 0) + 1
    return segment_counts


def _trend_by_week(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[str, int] = defaultdict(int)
    for row in rows:
        resolved = row.get("resolved_at")
        if not resolved:
            continue
        dt = datetime.fromisoformat(resolved)
        week_key = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        buckets[week_key] += 1
    return [{"week": k, "completed_reviews": buckets[k]} for k in sorted(buckets)]


def compute_metrics(
    review_outcomes: List[Dict[str, Any]],
    post_send_outcomes: List[Dict[str, Any]],
    window: str = "90d",
    now: datetime | None = None,
    filters: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    filters = filters or {}
    cutoff = now - timedelta(days=_window_days(window))

    in_window_reviews = [r for r in review_outcomes if _in_window(r.get("resolved_at", ""), cutoff)]
    reviews = _apply_filters(in_window_reviews, filters)
    reviewed = [r for r in reviews if r.get("clinician_adjudication")]

    fp_num = sum(1 for r in reviewed if r.get("is_false_positive"))
    fp_den = len(reviewed)

    hs_rows = [r for r in reviewed if r.get("severity_at_open") in {"review_required", "block"}]
    hs_num = sum(1 for r in hs_rows if r.get("is_high_severity_confirmed_signal"))

    reviewed_actionable = [r for r in reviewed if r.get("severity_at_open") in {"review_required", "block"}]
    action_num = sum(1 for r in reviewed_actionable if r.get("is_behavior_change"))

    durations = [
        int(r.get("resolution_duration_seconds", 0))
        for r in reviews
        if r.get("resolution_duration_seconds") is not None
    ]
    by_sev = {}
    for sev in ["info", "review_required", "block"]:
        vals = [int(r.get("resolution_duration_seconds", 0)) for r in reviews if r.get("severity_at_open") == sev]
        by_sev[sev] = median(vals) if vals else None

    post_rows = [p for p in post_send_outcomes if _in_window(p.get("followup_recorded_at", ""), cutoff)]
    post_den = sum(1 for p in post_rows if p.get("followup_recorded_at"))
    post_num = sum(1 for p in post_rows if p.get("duplicate_related_issue"))

    qa_sampled_info = [r for r in reviewed if r.get("severity_at_open") == "info" and r.get("qa_sampled_info_case")]
    false_positive_by_case_type: Dict[str, int] = {}
    for row in reviewed:
        if not row.get("is_false_positive"):
            continue
        case_type = row.get("review_type", "unknown")
        false_positive_by_case_type[case_type] = false_positive_by_case_type.get(case_type, 0) + 1

    behavior_change_by_severity: Dict[str, float | None] = {}
    for sev in ["info", "review_required", "block"]:
        sev_rows = [r for r in reviewed if r.get("severity_at_open") == sev]
        behavior_change_by_severity[sev] = _safe_rate(
            sum(1 for r in sev_rows if r.get("is_behavior_change")),
            len(sev_rows),
        )

    block_rows = [r for r in reviewed if r.get("severity_at_open") == "block"]

    metrics = {
        "false_positive_rate": _safe_rate(fp_num, fp_den),
        "high_severity_precision": _safe_rate(hs_num, len(hs_rows)),
        "clinician_action_rate": _safe_rate(action_num, len(reviewed_actionable)),
        "median_added_workflow_time_seconds": median(durations) if durations else None,
        "median_added_workflow_time_seconds_by_severity": by_sev,
        "post_send_duplicate_friction_rate": _safe_rate(post_num, post_den),
    }

    return {
        "window": window,
        "filters": filters,
        "counts": {
            "reviews_total": len(reviews),
            "reviews_adjudicated": len(reviewed),
            "high_severity_reviews": len(hs_rows),
            "post_send_followups": post_den,
            "completed_reviews_volume": len(reviews),
        },
        "metrics": metrics,
        "segments": _segment_counts(reviews),
        "trend": {
            "weekly_completed_reviews": _trend_by_week(reviews),
        },
        "qa": {
            "sampled_info_case_reviews": len(qa_sampled_info),
            "false_positives_by_case_type": false_positive_by_case_type,
            "behavior_change_rate_by_severity": behavior_change_by_severity,
            "block_confirmation_rate": _safe_rate(
                sum(1 for r in block_rows if r.get("is_high_severity_confirmed_signal")),
                len(block_rows),
            ),
        },
    }
