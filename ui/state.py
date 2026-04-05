from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import streamlit as st

from services.openai_client import is_openai_configured
from src.config import DEFAULT_CONFIG
from src.metrics import compute_metrics
from src.review_cases import load_case_by_id, load_review_queue
from src.review_outcomes import load_post_send_outcomes, load_review_outcomes
from src.transmission_service import TransmissionService


@st.cache_data(show_spinner=False)
def cached_queue() -> List[Dict[str, Any]]:
    return load_review_queue()


@st.cache_data(show_spinner=False)
def cached_case(review_id: str) -> Dict[str, Any]:
    return load_case_by_id(review_id)


@st.cache_data(show_spinner=False)
def cached_metrics(window: str, filters_json: str) -> Dict[str, Any]:
    outcomes = load_review_outcomes()
    post_send = load_post_send_outcomes()
    filters = json.loads(filters_json) if filters_json else {}
    return compute_metrics(outcomes, post_send, window=window, now=datetime.now(timezone.utc), filters=filters)


def seed_state() -> None:
    queue = cached_queue()
    if "queue_items" not in st.session_state:
        st.session_state.queue_items = queue
    if "selected_review_id" not in st.session_state:
        st.session_state.selected_review_id = DEFAULT_CONFIG.default_case_id
    if "active_page" not in st.session_state:
        st.session_state.active_page = DEFAULT_CONFIG.default_page
    if "llm_mode_value" not in st.session_state:
        st.session_state.llm_mode_value = DEFAULT_CONFIG.default_llm_mode
    if st.session_state.llm_mode_value == "Rules only":
        st.session_state.llm_mode_value = "Hard Coded Functionality"
    if st.session_state.llm_mode_value == "LLM on":
        st.session_state.llm_mode_value = "LLM Assisted"
    if "use_claude" not in st.session_state:
        st.session_state.use_claude = DEFAULT_CONFIG.llm_mode_labels[DEFAULT_CONFIG.default_llm_mode]
    if "review_opened_at" not in st.session_state:
        st.session_state.review_opened_at = None
    if "review_saved" not in st.session_state:
        st.session_state.review_saved = False
    if "completed_case_ids" not in st.session_state:
        st.session_state.completed_case_ids = []

    set_case(st.session_state.selected_review_id, initialize_only=True)


def set_case(review_id: str, initialize_only: bool = False) -> None:
    if initialize_only and "selected_case" in st.session_state:
        return
    case = cached_case(review_id)
    st.session_state.selected_review_id = review_id
    st.session_state.selected_case = case
    st.session_state.pending_text = json.dumps(case["pending_rx"], indent=2)
    st.session_state.history_text = json.dumps(case["med_history"], indent=2)
    st.session_state.active_text = json.dumps(case.get("active_med_list", []), indent=2)
    st.session_state.result = None
    st.session_state.review_opened_at = None
    st.session_state.review_saved = False


def set_page(page_name: str) -> None:
    st.session_state.active_page = page_name


def build_case_from_inputs() -> Dict[str, Any]:
    case = dict(st.session_state.selected_case)
    case["pending_rx"] = json.loads(st.session_state.pending_text)
    case["med_history"] = json.loads(st.session_state.history_text)
    case["active_med_list"] = json.loads(st.session_state.active_text)
    return case


def run_check(ack: bool = False, reason_code: str | None = None) -> Dict[str, Any]:
    if st.session_state.use_claude and not is_openai_configured():
        st.error("OpenAI API key is not configured. Add OPENAI_API_KEY to Streamlit secrets.")
        return {}
    os.environ["USE_LLM"] = "true" if st.session_state.use_claude else "false"
    service = TransmissionService()
    result = service.process_case(build_case_from_inputs(), clinician_acknowledged=ack, reason_code=reason_code)
    st.session_state.result = result
    if not st.session_state.review_opened_at:
        st.session_state.review_opened_at = datetime.now(timezone.utc).isoformat()
    return result
