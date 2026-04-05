from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from src.review_outcomes import save_review_outcome, utc_now_iso
from ui.formatting import title_case_label
from ui.state import cached_metrics, cached_queue, set_case
from ui.theme import chip


def _behavior_change(action: str) -> bool:
    return action in {
        "cancel",
        "cancel_duplicate_prescription",
        "edit",
        "defer",
        "adjust_start_date",
        "choose_alternative",
        "escalate",
    }


def _default_adjudication(action: str) -> str:
    if action in {"approve_prescription", "proceed_next_case"}:
        return "false_positive"
    if action in {"proceed", "confirm_patient"}:
        return "clinically_relevant_but_no_change"
    return "true_positive"


def _save_action_outcome(case: Dict[str, Any], result: Dict[str, Any], action: str, notes: str) -> None:
    finding = result["finding"]
    severity = "review_required" if finding["severity"] == "block" else finding["severity"]
    outcome = {
        "review_id": case["review_id"],
        "case_type": case["review_type"],
        "review_type": case["review_type"],
        "program": case["queue"]["program"],
        "finding_id": finding["finding_id"],
        "opened_at": st.session_state.get("review_opened_at") or utc_now_iso(),
        "resolved_at": utc_now_iso(),
        "resolution_duration_seconds": 0,
        "clinician_id": "mock_clinician_001",
        "severity_at_open": severity,
        "agent_classification": result.get("decision_trace", {}).get("classification") or finding.get("duplicate_type", "other"),
        "duplicate_type": finding.get("duplicate_type", "other"),
        "max_overlap_days": int(finding.get("computed", {}).get("max_overlap_days", 0)),
        "used_llm": bool(result.get("decision_trace", {}).get("claude_invoked", False)),
        "rules_triggered": result.get("decision_trace", {}).get("triggered_rules", []),
        "multi_pharmacy_flag": bool(result.get("decision_trace", {}).get("multi_pharmacy_risk_amplifier", False)),
        "clinician_adjudication": _default_adjudication(action),
        "clinician_meaningful_duplicate": action != "proceed_next_case",
        "clinician_action_taken": action,
        "changed_prescribing_behavior": _behavior_change(action),
        "interruptive_alert_appropriate": severity in {"review_required", "block"},
        "override_used": False,
        "override_reason_code": None,
        "patient_confirmation_completed": False,
        "pharmacy_confirmation_completed": False,
        "free_text_notes": notes or "Captured from recommended action button.",
        "transmission_attempted": False,
        "transmission_completed": False,
        "post_send_followup_flag": False,
        "post_send_followup_type": "none",
        "qa_sampled_info_case": False,
    }
    save_review_outcome(outcome)
    completed = set(st.session_state.get("completed_case_ids", []))
    completed.add(case["review_id"])
    st.session_state.completed_case_ids = sorted(completed)


def _next_review_required_case(current_review_id: str) -> str | None:
    queue = cached_queue()
    completed_ids = set(st.session_state.get("completed_case_ids", []))
    required_ids = [r["review_id"] for r in queue if r.get("severity") in {"review_required", "block"}]
    pending_required_ids = [rid for rid in required_ids if rid not in completed_ids]
    if not required_ids:
        return queue[0]["review_id"] if queue else None
    if not pending_required_ids:
        st.session_state.completed_case_ids = []
        return "case_01" if any(r["review_id"] == "case_01" for r in queue) else required_ids[0]

    ordered_ids = [r["review_id"] for r in queue]
    if current_review_id in ordered_ids:
        idx = ordered_ids.index(current_review_id)
        tail = ordered_ids[idx + 1 :]
        for review_id in tail:
            if review_id in pending_required_ids:
                return review_id

    return pending_required_ids[0]


def _advance_to_next_case(current_review_id: str) -> None:
    next_case = _next_review_required_case(current_review_id)
    if next_case:
        set_case(next_case)
    cached_metrics.clear()


def _render_info_action(case: Dict[str, Any], result: Dict[str, Any]) -> None:
    if st.button("Proceed to Next Case", key=f"info_next_{case['review_id']}", use_container_width=True):
        _save_action_outcome(case, result, "proceed_next_case", notes="")
        _advance_to_next_case(case["review_id"])
        st.rerun()


def render_finding_panel(case: Dict[str, Any], result: Dict[str, Any]) -> None:
    finding = result["finding"]
    computed = finding.get("computed", {})
    severity = "review_required" if finding.get("severity") == "block" else finding.get("severity")

    st.markdown("### Clinical Review")
    st.markdown(
        "<div class='card'>"
        + chip(f"Severity: {title_case_label(severity)}", accent=True)
        + chip("Review Type: Duplicate Detected")
        + chip(f"Duplicate Type: {title_case_label(finding.get('duplicate_type'))}")
        + f"<div><strong>{finding.get('title')}</strong></div>"
        + f"<div class='muted' style='margin-top:6px'>{finding.get('summary')}</div>"
        + f"<div style='margin-top:8px'>Proposed Start: <strong>{computed.get('proposed_start_date')}</strong></div>"
        + f"<div>Proposed End: <strong>{computed.get('proposed_end_date')}</strong></div>"
        + f"<div>Max Overlap: <strong>{computed.get('max_overlap_days')}</strong> days</div>"
        + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("#### Recommended Actions")
    if severity == "info":
        _render_info_action(case, result)
    else:
        notes_key = f"action_notes_{case['review_id']}"
        action_cols = st.columns(2)
        actions = list(finding.get("recommended_actions", []))
        actions = sorted(actions, key=lambda x: 0 if x.get("action") == "approve_prescription" else 1)
        if severity == "block":
            actions = [a for a in actions if a.get("action") not in {"approve_prescription"}]
        for idx, action in enumerate(actions):
            label = action.get("label", "Action")
            action_key = action.get("action", "other")
            if action_cols[idx % 2].button(label, key=f"rec_action_{case['review_id']}_{idx}", use_container_width=True):
                notes = st.session_state.get(notes_key, "")
                _save_action_outcome(case, result, action_key, notes=notes)
                if action_key in {"approve_prescription", "cancel_duplicate_prescription", "adjust_start_date"}:
                    _advance_to_next_case(case["review_id"])
                    st.rerun()
                st.success(f"Action recorded: {title_case_label(action_key)}")
        st.text_area("Action Notes (optional)", key=notes_key, height=80)

    return
