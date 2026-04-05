from __future__ import annotations

from pathlib import Path
from typing import List

import streamlit as st

from src.config import DEFAULT_CONFIG


def render_header() -> None:
    left, mid, right = st.columns([1, 3, 2])
    with left:
        logo = Path(__file__).resolve().parents[1] / "assets" / DEFAULT_CONFIG.theme.logo_file
        if logo.exists():
            st.image(str(logo), width=120)
    with mid:
        st.markdown("### Duplicate Prescription Agent")

    with right:
        mode = st.session_state.llm_mode_value
        c1, c2 = st.columns(2)
        if c1.button("LLM Assisted", type="primary" if mode == "LLM Assisted" else "secondary", use_container_width=True):
            st.session_state.llm_mode_value = "LLM Assisted"
            st.session_state.use_claude = True
            st.rerun()
        if c2.button(
            "Hard Coded Functionality",
            type="primary" if mode == "Hard Coded Functionality" else "secondary",
            use_container_width=True,
        ):
            st.session_state.llm_mode_value = "Hard Coded Functionality"
            st.session_state.use_claude = False
            st.rerun()


def render_nav(pages: List[str]) -> str:
    cols = st.columns(len(pages))
    for idx, page in enumerate(pages):
        is_selected = st.session_state.active_page == page
        if cols[idx].button(page, key=f"nav_{idx}", type="primary" if is_selected else "secondary", use_container_width=True):
            st.session_state.active_page = page
            st.rerun()
    return st.session_state.active_page
