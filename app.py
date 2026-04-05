from __future__ import annotations

import streamlit as st

from src.config import DEFAULT_CONFIG
from ui.app_shell import render_header, render_nav
from ui.pages import metrics_page, review_queue_page
from ui.state import seed_state
from ui.theme import apply_theme

PAGES = [
    "Review Queue",
    "Metrics Dashboard",
]


def main() -> None:
    st.set_page_config(page_title="Duplicate Prescription Agent", layout="wide")
    try:
        seed_state()
        apply_theme(DEFAULT_CONFIG.theme)
        render_header()
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        page = render_nav(PAGES)
        st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)

        if page == "Review Queue":
            review_queue_page.render_page()
        elif page == "Metrics Dashboard":
            metrics_page.render_page()
    except Exception:
        st.error("An application error occurred. Please retry the action.")
        st.stop()


if __name__ == "__main__":
    main()
