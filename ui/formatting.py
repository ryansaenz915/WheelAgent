from __future__ import annotations


def title_case_label(value: str) -> str:
    text = str(value or "")
    if not text:
        return ""
    severity_display_map = {
        "info": "No Review Required",
    }
    if text in severity_display_map:
        return severity_display_map[text]
    return text.replace("_", " ").strip().title()
