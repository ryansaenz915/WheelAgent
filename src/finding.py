from __future__ import annotations

import uuid
from typing import Dict, List

from .drug_classes import classify_drug_class
from .llm import ClaudeAdapter
from .models import ClassifierOutput, DuplicateCandidate, DuplicateRxFinding, PendingPrescriptionEvent
from .normalize import extract_ingredient_from_display
from .rules import RulesResult


def _build_evidence(rules: RulesResult) -> List[Dict[str, object]]:
    selected: List[DuplicateCandidate] = []
    for row in sorted(rules.true_duplicate_same_drug, key=lambda x: x.overlap_days, reverse=True):
        selected.append(row)
    for row in sorted(rules.transition_or_duplicate, key=lambda x: x.overlap_days, reverse=True):
        if row.drug_display not in {x.drug_display for x in selected}:
            selected.append(row)
    for row in sorted(rules.supporting_rows, key=lambda x: x.fill_date, reverse=True):
        if row.drug_display not in {x.drug_display for x in selected}:
            selected.append(row)

    return [
        {
            "drug": x.drug_display,
            "drug_class": classify_drug_class(x.drug_display, x.ingredient),
            "fill_date": x.fill_date.isoformat(),
            "days_supply": x.days_supply,
            "supply_end_date": x.supply_end_date.isoformat(),
            "status": x.status,
            "pharmacy": x.pharmacy,
        }
        for x in selected
    ]


def _duplicate_type(rules: RulesResult) -> str:
    if rules.true_duplicate_same_drug:
        return "same_drug_same_strength"
    if rules.transition_or_duplicate:
        return "same_drug_diff_strength"
    return "other"


def _deterministic_title(event: PendingPrescriptionEvent, rules: RulesResult) -> str:
    ingredient = extract_ingredient_from_display(event.prescription.drug_display)
    if rules.true_duplicate_same_drug:
        top = sorted(rules.true_duplicate_same_drug, key=lambda x: x.overlap_days, reverse=True)[0]
        return f"Possible duplicate {ingredient} {top.strength} fill with active overlap"
    if rules.transition_or_duplicate:
        return f"Possible overlapping {ingredient} dose transition requires review"
    return "No clinically significant duplicate overlap detected"


def _deterministic_summary(rules: RulesResult) -> str:
    if rules.true_duplicate_same_drug:
        top = sorted(rules.true_duplicate_same_drug, key=lambda x: x.overlap_days, reverse=True)[0]
        summary = (
            f"Medication history shows {top.drug_display} dispensed on {top.fill_date.isoformat()} "
            f"with a {top.days_supply}-day supply. If this Rx starts on {rules.pending_start_date}, "
            f"there is an estimated {top.overlap_days}-day overlap through {top.supply_end_date.isoformat()}."
        )
    elif rules.transition_or_duplicate:
        top = sorted(rules.transition_or_duplicate, key=lambda x: x.overlap_days, reverse=True)[0]
        summary = (
            f"Medication history shows same ingredient and route but different strength overlap of "
            f"{top.overlap_days} days for {top.drug_display}."
        )
    else:
        summary = "No meaningful active overlap was detected from available medication history."

    if rules.multi_pharmacy_risk_amplifier:
        summary += " Patient also filled semaglutide at multiple pharmacies recently."
    return summary


def build_finding(
    event: PendingPrescriptionEvent,
    rules: RulesResult,
    severity: str,
    classifier_outputs: List[ClassifierOutput],
    llm_adapter: ClaudeAdapter,
) -> DuplicateRxFinding:
    evidence = _build_evidence(rules)
    computed = {
        "proposed_start_date": rules.pending_start_date,
        "proposed_end_date": rules.pending_end_date,
        "max_overlap_days": rules.max_overlap_days,
    }
    duplicate_type = _duplicate_type(rules)

    llm_finding = llm_adapter.generate_finding_text(
        pending_json=event.to_serializable(),
        relevant_history=evidence,
        overlap_summary={
            "pending_start_date": rules.pending_start_date,
            "pending_end_date": rules.pending_end_date,
            "max_overlap_days": rules.max_overlap_days,
            "multi_pharmacy_risk_amplifier": rules.multi_pharmacy_risk_amplifier,
            "severity": severity,
        },
        classifier_outputs=[c.to_serializable() for c in classifier_outputs],
    )

    recommended_actions = [
        {
            "action": "approve_prescription",
            "label": "Approve Prescription",
        },
        {
            "action": "adjust_start_date",
            "label": "Start after 2026-03-30 if continuing existing supply",
        },
        {
            "action": "cancel_duplicate_prescription",
            "label": "Cancel - Duplicate Prescription",
        },
    ]

    payload = {
        "severity": severity,
        "title": _deterministic_title(event, rules),
        "summary": _deterministic_summary(rules),
        "drug_class": classify_drug_class(event.prescription.drug_display),
        "duplicate_type": duplicate_type,
        "computed": computed,
        "evidence": evidence,
        "limitations": [
            "Medication history may be incomplete and may not reflect what the patient is actually taking.",
            "Overlap is estimated from fill date plus days supply.",
        ],
        "recommended_actions": recommended_actions,
        "clinician_response": {
            "required": True,
            "reason_codes": ["dose_titration", "renewal", "replacement_lost", "pharmacy_switch", "other"],
        },
    }
    if llm_finding:
        payload["title"] = str(llm_finding.get("title", payload["title"]))
        payload["summary"] = str(llm_finding.get("summary", payload["summary"]))
        payload["drug_class"] = str(llm_finding.get("drug_class", payload["drug_class"]))

    return DuplicateRxFinding(
        finding_id=str(uuid.uuid4()),
        severity=str(payload["severity"]),
        title=str(payload["title"]),
        summary=str(payload["summary"]),
        drug_class=str(payload.get("drug_class", "UNKNOWN")),
        duplicate_type=str(payload["duplicate_type"]),
        computed=dict(payload["computed"]),
        evidence=list(payload["evidence"]),
        limitations=list(payload["limitations"]),
        recommended_actions=list(payload["recommended_actions"]),
        clinician_response=dict(payload["clinician_response"]),
    )
