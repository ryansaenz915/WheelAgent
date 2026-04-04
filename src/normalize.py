from __future__ import annotations

import re
from typing import Optional

from .models import MedicationHistoryEntry, PendingPrescriptionEvent

_ROUTE_MAP = {
    "subcutaneous": "subcutaneous",
    "sc": "subcutaneous",
    "sq": "subcutaneous",
    "oral": "oral",
    "po": "oral",
}

_STOPWORDS = {
    "dose",
    "inject",
    "injection",
    "tablet",
    "capsule",
    "solution",
    "mg",
    "ml",
    "dose)",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def normalize_route(route: str) -> str:
    key = normalize_text(route)
    return _ROUTE_MAP.get(key, key)


def parse_strength(value: str) -> str:
    text = normalize_text(value)
    match = re.search(r"(\d+(?:\.\d+)?)\s*mg", text)
    if not match:
        return ""
    num = match.group(1)
    if num.endswith(".0"):
        num = num[:-2]
    return f"{num} mg"


def extract_ingredient_from_display(drug_display: str) -> str:
    text = normalize_text(re.sub(r"\(.*?\)", "", drug_display or ""))
    for token in re.split(r"[^a-z0-9]+", text):
        if token and token not in _STOPWORDS and not token[0].isdigit():
            return token
    return "unknown"


def pending_ingredient(event: PendingPrescriptionEvent) -> str:
    return extract_ingredient_from_display(event.prescription.drug_display)


def pending_strength(event: PendingPrescriptionEvent) -> str:
    return parse_strength(event.prescription.drug_display)


def normalize_history_entry(entry: MedicationHistoryEntry) -> MedicationHistoryEntry:
    ingredient = normalize_text(entry.ingredient)
    if not ingredient:
        ingredient = extract_ingredient_from_display(entry.drug_display)

    strength = parse_strength(entry.strength)
    if not strength:
        strength = parse_strength(entry.drug_display)

    route = normalize_route(entry.route)

    return MedicationHistoryEntry(
        drug_display=entry.drug_display,
        ingredient=ingredient,
        strength=strength,
        route=route,
        fill_date=entry.fill_date,
        days_supply=entry.days_supply,
        status=normalize_text(entry.status),
        pharmacy=entry.pharmacy,
    )


def normalize_pharmacy_name(pharmacy: Optional[str]) -> str:
    return normalize_text(pharmacy or "unknown")
