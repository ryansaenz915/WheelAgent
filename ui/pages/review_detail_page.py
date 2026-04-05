from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict

import streamlit as st

from ui.components.finding_panel import render_finding_panel
from ui.components.review_form import render_review_form
from ui.formatting import title_case_label
from ui.state import run_check
from ui.theme import chip


def _render_patient_context(case: Dict[str, Any], result: Dict[str, Any] | None) -> None:
    p = case["pending_rx"]
    st.markdown("### Patient and Pending Rx")
    st.markdown(
        "<div class='card'>"
        + chip(f"Scenario Type: {title_case_label(case['review_type'])}", accent=True)
        + chip(f"Program: {case['queue']['program']}")
        + chip(f"Status: {title_case_label(case['queue']['status'])}")
        + f"<div><strong>{p['patient']['first_name']} {p['patient']['last_name']}</strong></div>"
        + f"<div class='muted'>DOB: {p['patient']['dob']} | Patient ID: {p['patient']['patient_id']}</div>"
        + f"<div class='muted'>Drug: {p['prescription']['drug_display']}</div>"
        + f"<div class='muted'>Days supply: {p['prescription']['days_supply']} | Route: {p['prescription']['route']}</div>"
        + f"<div class='muted'>Prescriber NPI: {p['prescriber']['npi']}</div>"
        + f"<div class='muted'>Pharmacy: {p['pharmacy']['name']} | NCPDP ID: {p['pharmacy'].get('ncpdp_id', 'unknown')}</div>"
        + "</div>",
        unsafe_allow_html=True,
    )


def _render_med_history(case: Dict[str, Any], result: Dict[str, Any] | None) -> None:
    st.markdown("### Medication History")
    evidence_drugs = {e.get("drug") for e in result.get("finding", {}).get("evidence", [])} if result else set()

    card_rows = []
    for row in case["med_history"]:
        fill_date = row.get("fill_date")
        supply_end_date = fill_date
        try:
            fill = date.fromisoformat(fill_date)
            days_supply = int(row.get("days_supply", 0))
            if days_supply > 0:
                supply_end_date = (fill + timedelta(days=days_supply - 1)).isoformat()
        except (TypeError, ValueError):
            supply_end_date = fill_date

        accent_border = "#24543D" if row.get("drug_display") in evidence_drugs else "#D9D9D9"
        card_rows.append(
            "<div style='background:#FFFFFF; color:#000000; border:1px solid "
            + accent_border
            + "; border-radius:12px; padding:10px 12px; margin-bottom:8px;'>"
            + f"<div style='font-weight:700; margin-bottom:6px;'>{row.get('drug_display', '')}</div>"
            + "<div style='display:flex; flex-wrap:wrap; gap:6px;'>"
            + f"<span style='border:1px solid #CFCFCF; border-radius:999px; padding:2px 8px;'>Ingredient: {row.get('ingredient', '')}</span>"
            + f"<span style='border:1px solid #CFCFCF; border-radius:999px; padding:2px 8px;'>Strength: {row.get('strength', '')}</span>"
            + f"<span style='border:1px solid #CFCFCF; border-radius:999px; padding:2px 8px;'>Fill Date: {row.get('fill_date', '')}</span>"
            + f"<span style='border:1px solid #CFCFCF; border-radius:999px; padding:2px 8px;'>Days Supply: {row.get('days_supply', '')}</span>"
            + f"<span style='border:1px solid #CFCFCF; border-radius:999px; padding:2px 8px;'>Supply End Date: {supply_end_date or ''}</span>"
            + f"<span style='border:1px solid #CFCFCF; border-radius:999px; padding:2px 8px;'>Pharmacy: {row.get('pharmacy', '')}</span>"
            + "</div></div>"
        )

    cards_html = (
        "<div style='background:#FFFFFF; border:1px solid #D9D9D9; border-radius:14px; padding:10px;'>"
        + "".join(card_rows)
        + "</div>"
    )
    st.markdown(cards_html, unsafe_allow_html=True)


def render_page(show_header: bool = True) -> None:
    case = st.session_state.selected_case

    if show_header:
        st.markdown("## Review Detail")
    if st.button("Run Safety Check Simulation", use_container_width=True):
        result = run_check(ack=False)
        if result:
            st.rerun()

    result = st.session_state.get("result")

    if result:
        render_finding_panel(case, result)
    else:
        st.info("Run pre-send safety check to generate clinician findings.")

    top_left, top_right = st.columns([1, 1], gap="large")
    with top_left:
        _render_patient_context(case, result)
    with top_right:
        _render_med_history(case, result)
    if result:
        render_review_form(case, result)
