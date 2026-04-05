from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def render_decision_trace(result: Dict[str, Any]) -> None:
    trace = result.get("decision_trace", {})

    st.markdown("### Decision Trace")
    st.markdown("#### Normalization and candidate summary")
    st.write(f"- Pending window: {trace.get('pending_start_date')} to {trace.get('pending_end_date')}")
    st.write(f"- Max overlap days: {trace.get('max_overlap_days')}")
    st.write(f"- Triggered rules: {', '.join(trace.get('triggered_rules', []))}")
    st.write(f"- Multi-pharmacy amplifier: {trace.get('multi_pharmacy_risk_amplifier')}")

    st.markdown("#### Candidate routing")
    route_log = trace.get("classifier_route_log", [])
    if route_log:
        for row in route_log:
            st.write(
                f"- {row.get('drug_display')}: {row.get('route_decision')} ({row.get('route_reason')}) | overlap={row.get('overlap_days')}"
            )
    else:
        st.caption("No ambiguous candidate routing was needed.")

    st.markdown("#### LLM and transmission status")
    st.write(f"- Claude invoked: {trace.get('claude_invoked')}")
    st.write(f"- Classification path invoked: {trace.get('ambiguous_classifier_path_invoked')}")
    st.write(f"- Final classification: {trace.get('classification')}")

    post_send = result.get("post_send_state", {})
    st.write(f"- Transmission ready: {post_send.get('transmission_ready')}")
    st.write(f"- Transmission attempted: {post_send.get('send_attempted')}")
    st.write(f"- Transmission success: {post_send.get('send_success')}")

    with st.expander("Raw decision trace JSON", expanded=False):
        st.json(trace)
