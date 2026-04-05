from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from src.metrics import compute_metrics
from src.review_outcomes import load_post_send_outcomes, load_review_outcomes
from ui.formatting import title_case_label
from ui.theme import format_rate


def _select_with_labels(label: str, values: list[str], index: int = 0) -> str:
    display_to_value = {title_case_label(v): v for v in values}
    display_options = list(display_to_value.keys())
    selected_display = st.selectbox(label, display_options, index=index)
    return display_to_value[selected_display]


def _available_values(outcomes: list[dict], key: str, default_values: list[str]) -> list[str]:
    seen = sorted({str(row.get(key)) for row in outcomes if row.get(key)})
    if not seen:
        return default_values
    ordered = [value for value in default_values if value in seen]
    extras = [value for value in seen if value not in ordered]
    return ordered + extras


def render_metrics_dashboard() -> None:
    st.markdown("## Metrics Dashboard")
    outcomes = load_review_outcomes()
    post_send = load_post_send_outcomes()

    severity_values = _available_values(outcomes, "severity_at_open", ["info", "review_required"])
    review_type_values = _available_values(
        outcomes,
        "review_type",
        ["duplicate_exact", "duplicate_transition", "early_refill", "class_overlap_high_risk", "polypharmacy_interaction"],
    )
    program_values = _available_values(outcomes, "program", [])
    duplicate_type_values = _available_values(
        outcomes,
        "duplicate_type",
        ["same_drug_same_strength", "same_drug_diff_strength", "same_class", "other"],
    )

    c1, c2, c3 = st.columns(3)
    window = c1.selectbox("Window", ["7d", "30d", "90d", "all"], index=2)
    with c2:
        severity = _select_with_labels("Severity", ["all"] + severity_values, index=0)
    with c3:
        review_type = _select_with_labels(
            "Review Type",
            ["all"] + review_type_values,
            index=0,
        )

    c4, c5, c6 = st.columns(3)
    program = c4.selectbox("Program", ["all"] + program_values, index=0)
    with c5:
        duplicate_type = _select_with_labels(
            "Duplicate Type",
            ["all"] + duplicate_type_values,
            index=0,
        )
    llm_display_to_value = {
        "All": "all",
        "Hard Coded Functionality": "rules_only",
        "LLM Assisted": "claude_assisted",
    }
    llm_mode = llm_display_to_value[c6.selectbox("Path", list(llm_display_to_value.keys()), index=0)]

    filters = {
        "severity": severity,
        "review_type": review_type,
        "program": program,
        "duplicate_type": duplicate_type,
        "llm_mode": llm_mode,
    }

    metrics = compute_metrics(
        outcomes,
        post_send,
        window=window,
        now=datetime.now(timezone.utc),
        filters=filters,
    )

    cards = st.columns(5)
    cards[0].metric("False positive rate", format_rate(metrics["metrics"]["false_positive_rate"]))
    cards[1].metric("High-severity precision", format_rate(metrics["metrics"]["high_severity_precision"]))
    cards[2].metric("Clinician action rate", format_rate(metrics["metrics"]["clinician_action_rate"]))
    cards[3].metric("Median added workflow time (sec)", metrics["metrics"]["median_added_workflow_time_seconds"])
    cards[4].metric("Post-send duplicate friction", format_rate(metrics["metrics"]["post_send_duplicate_friction_rate"]))
