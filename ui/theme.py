from __future__ import annotations

import streamlit as st

from src.config import ThemeTokens


def apply_theme(tokens: ThemeTokens) -> None:
    st.markdown(
        f"""
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {{
  background: #FCFDFB !important;
  color: {tokens.text} !important;
}}
[data-testid="stSidebar"] {{ display: none !important; }}
h1, h2, h3, h4, h5, h6 {{ color: {tokens.heading} !important; }}
p, div, span, label, li, td, th, small {{
  color: #000000 !important;
}}
.card {{
  background: #FFFFFF;
  border: 1px solid {tokens.border};
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
}}
.muted {{ color: {tokens.muted} !important; }}
.chip {{
  display: inline-block;
  border-radius: 999px;
  padding: 3px 10px;
  border: 1px solid {tokens.border};
  margin-right: 6px;
  margin-bottom: 6px;
  font-size: 0.8rem;
  font-weight: 600;
}}
.chip-accent {{ border-color: {tokens.accent}; background: {tokens.accent_soft}; }}
.stButton > button {{
  background: #FFFFFF !important;
  color: #000000 !important;
  border: 1px solid #CFCFCF !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}}
.stButton > button:hover {{
  background: #F6F6F6 !important;
  color: #000000 !important;
  border: 1px solid #BDBDBD !important;
}}
.stButton > button[kind="primary"] {{
  background: #E5E5E5 !important;
  color: #000000 !important;
  border: 1px solid #C7C7C7 !important;
}}
[data-testid="stAlert"], [data-testid="stAlert"] * {{
  color: #000000 !important;
}}
[data-testid="stMetric"], [data-testid="stMetric"] * {{
  color: #000000 !important;
}}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{
  color: #000000 !important;
}}
[data-testid="stTable"], [data-testid="stTable"] * {{
  color: #000000 !important;
  background: #FFFFFF !important;
}}
[data-testid="stTable"] table {{
  width: 100% !important;
  border-collapse: collapse !important;
  table-layout: auto !important;
}}
[data-testid="stTable"] th, [data-testid="stTable"] td {{
  border: 1px solid #D0D0D0 !important;
  padding: 6px 8px !important;
  white-space: normal !important;
  word-break: break-word !important;
}}
[data-testid="stDataFrame"], [data-testid="stDataFrame"] * {{
  background: #FFFFFF !important;
  color: #000000 !important;
}}
[data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {{
  border-color: #D0D0D0 !important;
}}
[data-testid="stSelectbox"] label {{
  color: #000000 !important;
}}
[data-testid="stTextArea"] label {{
  color: #000000 !important;
}}
[data-testid="stTextArea"] textarea {{
  background: #FFFFFF !important;
  color: #000000 !important;
  border: 1px solid #CFCFCF !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"] {{
  border: 1px solid #CFCFCF !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  background: #FFFFFF !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"] > div {{
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  background: transparent !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"] textarea {{
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}}
[data-baseweb="select"] > div {{
  background: #FFFFFF !important;
  color: #000000 !important;
  border: 1px solid #CFCFCF !important;
}}
[data-baseweb="popover"] {{
  background: #FFFFFF !important;
}}
[data-baseweb="menu"], [data-baseweb="menu"] * {{
  background: #FFFFFF !important;
  color: #000000 !important;
}}
[role="listbox"], [role="listbox"] * {{
  background: #FFFFFF !important;
  color: #000000 !important;
}}
div[role="option"], li[role="option"] {{
  background: #FFFFFF !important;
  color: #000000 !important;
}}
div[role="option"][aria-selected="true"], li[role="option"][aria-selected="true"] {{
  background: #E5E5E5 !important;
  color: #000000 !important;
}}
div[role="option"]:hover, li[role="option"]:hover {{
  background: #F2F2F2 !important;
  color: #000000 !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def chip(text: str, accent: bool = False) -> str:
    cls = "chip chip-accent" if accent else "chip"
    return f'<span class="{cls}">{text}</span>'


def format_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{round(value * 100, 1)}%"
