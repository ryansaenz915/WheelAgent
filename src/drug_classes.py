from __future__ import annotations

from typing import Optional


CLASS_MAP = {
    "semaglutide": "GLP1_AGONIST",
    "rivaroxaban": "ANTICOAGULANT",
    "apixaban": "ANTICOAGULANT",
    "lisinopril": "ACE_INHIBITOR",
    "citalopram": "SSRI",
    "ondansetron": "QT_PROLONGING_AGENT",
    "azithromycin": "QT_PROLONGING_AGENT",
}

CLASS_LABELS = {
    "GLP1_AGONIST": "GLP-1 Agonist",
    "ANTICOAGULANT": "Anticoagulant",
    "ACE_INHIBITOR": "ACE Inhibitor",
    "SSRI": "SSRI",
    "QT_PROLONGING_AGENT": "QT-Prolonging Agent",
}


def _extract_ingredient_from_display(display: str) -> str:
    return (display or "").split(" ")[0].strip().lower()


def classify_drug_class(drug_display: str, ingredient: Optional[str] = None) -> str:
    ing = (ingredient or "").strip().lower() or _extract_ingredient_from_display(drug_display)
    return CLASS_MAP.get(ing, "UNKNOWN")


def drug_class_label(drug_class: str) -> str:
    if not drug_class:
        return "Unknown"
    return CLASS_LABELS.get(drug_class, drug_class.replace("_", " ").title())

