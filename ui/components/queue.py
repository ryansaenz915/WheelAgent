from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from src.queue_ops import queue_reason
from src.review_outcomes import load_review_outcomes
from ui.state import cached_case, set_case


def _queue_table_rows(queue_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    completed_ids = {r.get("review_id") for r in load_review_outcomes()}
    rows = []
    for row in queue_rows:
        case = cached_case(row["review_id"])
        max_overlap = case.get("expected", {}).get("max_overlap_days", 0)
        raw_sev = row["severity"]
        severity = "review_required" if raw_sev == "block" else raw_sev
        status = "open" if severity == "info" else ("completed" if row["review_id"] in completed_ids else "open")
        rows.append(
            {
                "review_id": row["review_id"],
                "patient_name": row["patient_name"],
                "primary_issue": row["primary_drug_or_issue"],
                "review_type": row["review_type"],
                "severity": severity,
                "program": row["program"],
                "status": status,
                "updated_at": row["updated_at"],
                "reason": queue_reason(row["review_type"]),
                "max_overlap_days": max_overlap,
                "should_invoke_llm": bool(case.get("notes", {}).get("should_invoke_llm", False)),
            }
        )
    return rows


def render_review_queue(queue_rows: List[Dict[str, Any]]) -> None:
    table_rows = _queue_table_rows(queue_rows)
    st.markdown("## Review Queue")

    if not table_rows:
        st.info("No reviews available.")
        return

    options = {
        f"{row['review_id']} | {row['patient_name']} | {row['primary_issue']}": row
        for row in table_rows
    }
    default_idx = 0
    current_id = st.session_state.get("selected_review_id")
    labels = list(options.keys())
    for idx, label in enumerate(labels):
        if options[label]["review_id"] == current_id:
            default_idx = idx
            break

    selected_label = st.selectbox("Select review case", labels, index=default_idx)
    selected = options[selected_label]
    if selected["review_id"] != st.session_state.get("selected_review_id"):
        set_case(selected["review_id"])
