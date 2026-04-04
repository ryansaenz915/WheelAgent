from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from src.runner import BOUNDARY_STATEMENT, run_duplicate_check


def _load_sample() -> tuple[dict, list[dict]]:
    data_dir = Path(__file__).parent / "data"
    pending = json.loads((data_dir / "pending_rx.json").read_text(encoding="utf-8"))
    history = json.loads((data_dir / "med_history.json").read_text(encoding="utf-8"))
    return pending, history


def _severity_color(severity: str) -> str:
    return {
        "info": "#0f766e",
        "review_required": "#b45309",
        "block": "#b91c1c",
    }.get(severity, "#334155")


def _render_action_pills(actions: list[dict]) -> None:
    for idx, action in enumerate(actions):
        st.button(action["label"], key=f"action_{idx}_{action['action']}")


def main() -> None:
    st.set_page_config(page_title="Duplicate Rx Detection Agent", layout="wide")
    st.title("Duplicate Prescription Detection Agent - Rules First Prototype")
    st.caption("Primary UI: Streamlit. Optional Claude assist only for ambiguous transition cases.")
    st.info(BOUNDARY_STATEMENT)

    default_pending, default_history = _load_sample()
    if "pending_text" not in st.session_state:
        st.session_state.pending_text = json.dumps(default_pending, indent=2)
    if "history_text" not in st.session_state:
        st.session_state.history_text = json.dumps(default_history, indent=2)

    st.header("Section A: Inputs")
    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state.pending_text = st.text_area(
            "Pending Prescription JSON",
            value=st.session_state.pending_text,
            height=340,
        )
    with col_b:
        st.session_state.history_text = st.text_area(
            "Medication History JSON",
            value=st.session_state.history_text,
            height=340,
        )

    options_col1, options_col2, options_col3 = st.columns(3)
    with options_col1:
        use_claude = st.toggle("Use Claude for ambiguous cases", value=False)
    with options_col2:
        show_trace = st.toggle("Show decision trace", value=True)
    with options_col3:
        if st.button("Load sample scenario"):
            st.session_state.pending_text = json.dumps(default_pending, indent=2)
            st.session_state.history_text = json.dumps(default_history, indent=2)
            st.rerun()

    run_now = st.button("Run duplicate check", type="primary")
    if run_now:
        try:
            pending = json.loads(st.session_state.pending_text)
            history = json.loads(st.session_state.history_text)
            os.environ["USE_LLM"] = "true" if use_claude else "false"
            os.environ["MOCK_LLM"] = "false" if use_claude else "true"
            result = run_duplicate_check(pending, history)
            st.session_state.result = result
        except Exception as exc:
            st.error(f"Run failed: {exc}")

    if "result" not in st.session_state:
        return

    result = st.session_state.result
    finding = result["finding"]
    trace = result["decision_trace"]

    if show_trace:
        st.header("Section B: Decision trace")
        st.write("Formula used: overlap_days = max(0, (min(end_dates) - max(start_dates)).days + 1)")
        st.dataframe(trace["candidate_rows_considered"], use_container_width=True)
        st.write("Triggered rules:", ", ".join(trace["triggered_rules"]))
        st.write("Multi-pharmacy risk amplifier:", trace["multi_pharmacy_risk_amplifier"])
        st.write("Claude invoked:", trace["claude_invoked"])
        if trace["classifier_outputs"]:
            st.subheader("Intermediate candidate classifications")
            st.json(trace["classifier_outputs"])

    st.header("Section C: Clinician finding")
    sev_color = _severity_color(finding["severity"])
    st.markdown(
        f"<div style='padding:8px 12px;border-radius:6px;background:{sev_color};color:white;font-weight:700;'>"
        f"Severity: {finding['severity']}</div>",
        unsafe_allow_html=True,
    )
    st.subheader(finding["title"])
    st.write(finding["summary"])
    st.write("Computed overlap:", finding["computed"])
    st.dataframe(finding["evidence"], use_container_width=True)
    st.write("Limitations:")
    for item in finding["limitations"]:
        st.write(f"- {item}")

    st.write("Recommended actions:")
    _render_action_pills(finding["recommended_actions"])

    reason = st.selectbox("Clinician reason code", finding["clinician_response"]["reason_codes"])
    st.caption(f"Selected reason code: {reason}")

    st.subheader("Final JSON")
    st.json(result)


if __name__ == "__main__":
    main()
