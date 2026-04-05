from __future__ import annotations

import streamlit as st

from ui.components.queue import render_review_queue
from ui.pages import review_detail_page
from ui.state import cached_queue


def render_page() -> None:
    render_review_queue(cached_queue())
    review_detail_page.render_page(show_header=False)
