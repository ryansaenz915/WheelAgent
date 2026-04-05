from __future__ import annotations


def title_case_label(value: str) -> str:
    text = str(value or "")
    if not text:
        return ""
    return text.replace("_", " ").strip().title()
