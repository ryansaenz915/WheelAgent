from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import ClassifierOutput
from .rules import RulesResult


@dataclass
class SeverityDecision:
    severity: str
    rationale: List[str]


def assign_severity(rules: RulesResult, classifier_outputs: List[ClassifierOutput]) -> SeverityDecision:
    exact_overlap_count = sum(1 for row in rules.true_duplicate_same_drug if row.overlap_days >= 4)
    transition_with_overlap = any(row.overlap_days > 0 for row in rules.transition_or_duplicate)

    severity = "info"
    rationale: List[str] = []

    if exact_overlap_count >= 2:
        severity = "block"
        rationale.append("multiple_overlapping_same_strength_fills")
    elif exact_overlap_count >= 1:
        severity = "review_required"
        rationale.append("same_drug_same_strength_overlap_ge_4")
    elif transition_with_overlap:
        if any(out.classification in {"true_duplicate", "uncertain"} for out in classifier_outputs):
            severity = "review_required"
            rationale.append("ambiguous_transition_requires_confirmation")
        elif rules.max_overlap_days >= 4:
            severity = "review_required"
            rationale.append("different_strength_overlap_ge_4")
        else:
            severity = "info"
            rationale.append("low_overlap_likely_titration")
    elif 0 < rules.max_overlap_days <= 3:
        severity = "info"
        rationale.append("low_overlap_le_3")

    if rules.multi_pharmacy_risk_amplifier and rules.max_overlap_days > 0 and severity == "info":
        severity = "review_required"
        rationale.append("multi_pharmacy_overlap_amplifier")

    return SeverityDecision(severity=severity, rationale=rationale)
