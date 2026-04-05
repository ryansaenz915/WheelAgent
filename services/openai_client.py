from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from openai import OpenAI


def _read_streamlit_secret(name: str) -> Optional[str]:
    try:
        import streamlit as st
    except Exception:
        return None
    try:
        value = st.secrets.get(name)
    except Exception:
        return None
    if value is None:
        return None
    out = str(value).strip()
    return out or None


def get_openai_api_key() -> Optional[str]:
    api_key = _read_streamlit_secret("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "").strip() or None
    if not api_key:
        return None
    if api_key in {"sk-...", "your_openai_api_key"}:
        return None
    return api_key


def get_openai_model_name() -> str:
    return _read_streamlit_secret("OPENAI_MODEL") or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")


def get_openai_model() -> str:
    return get_openai_model_name()


@lru_cache(maxsize=4)
def _cached_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def get_openai_client() -> Optional[OpenAI]:
    api_key = get_openai_api_key()
    if not api_key:
        return None
    return _cached_client(api_key)


def is_openai_configured() -> bool:
    return bool(get_openai_api_key())
