from __future__ import annotations

import streamlit as st

from src.review_outcomes import load_post_send_outcomes, load_review_outcomes


def render_page() -> None:
    st.markdown("## Audit and Persistence")
    result = st.session_state.get("result")
    if result:
        st.markdown("### Current finding JSON")
        st.json(result.get("finding", {}))
        st.markdown("### Runtime audit log")
        st.json(result.get("audit_log", []))
        st.markdown("### DoseSpot trace")
        st.json(result.get("dosespot_trace", {}))
    else:
        st.caption("Run a case on Review Detail to populate runtime audit output.")

    st.markdown("### Persisted review outcomes")
    st.json(load_review_outcomes())

    st.markdown("### Persisted post-send outcomes")
    st.json(load_post_send_outcomes())
