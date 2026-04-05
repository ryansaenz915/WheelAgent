from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .finding import build_finding
from .llm import ClaudeAdapter
from .logging_utils import AuditLogger
from .models import ClassifierOutput, MedicationHistoryEntry, PendingPrescriptionEvent
from .review_cases import load_case_by_id
from .rules import apply_rules
from .severity import assign_severity
from .transmission_service import TransmissionService

BOUNDARY_STATEMENT = (
    "This workflow provides medication-safety reconciliation support only. "
    "The clinician remains the final decision-maker."
)

METRICS_PLACEHOLDERS = {
    "actionable_alert_rate": None,
    "false_positive_rate": None,
    "precision_high_severity": None,
    "median_added_time_to_transmit": None,
    "downstream_duplicate_too_soon_proxy": None,
}


def run_duplicate_check(pending_rx: Dict[str, Any], med_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    event = PendingPrescriptionEvent.from_dict(pending_rx)
    history_rows = [MedicationHistoryEntry.from_dict(item) for item in med_history]

    if event.status != "pending_transmission":
        raise ValueError("Duplicate check trigger requires status=pending_transmission")

    logger = AuditLogger()
    logger.log("duplicate_check_started", {"event_id": event.event_id, "status": event.status})

    rules_result = apply_rules(event, history_rows)
    logger.log(
        "normalized_candidate_set",
        {
            "rows_considered": len(rules_result.all_rows),
            "same_strength_candidates": len(rules_result.true_duplicate_same_drug),
            "ambiguous_candidates": len(rules_result.transition_or_duplicate),
            "multi_pharmacy_risk_amplifier": rules_result.multi_pharmacy_risk_amplifier,
        },
    )
    logger.log(
        "overlap_calculations",
        {
            "pending_start_date": rules_result.pending_start_date,
            "pending_end_date": rules_result.pending_end_date,
            "max_overlap_days": rules_result.max_overlap_days,
        },
    )
    logger.log("rule_triggers", {"triggered_rules": rules_result.triggered_rules})

    llm_adapter = ClaudeAdapter()
    llm_mode = llm_adapter.mode_state()
    classifier_outputs: List[ClassifierOutput] = []
    classifier_route_log: List[Dict[str, Any]] = []

    for candidate in rules_result.transition_or_duplicate:
        route = llm_adapter.explain_route_for_candidate(candidate)
        classifier_route_log.append(
            {
                "drug_display": candidate.drug_display,
                "overlap_days": candidate.overlap_days,
                "same_strength": candidate.same_strength,
                "route_decision": route["decision"],
                "route_reason": route["reason"],
                "llm_execution_mode": llm_mode["execution_mode"],
            }
        )
        classifier_outputs.append(llm_adapter.classify_ambiguous_candidate(event, candidate))

    logger.log(
        "llm_invoked_or_skipped",
        {
            "llm_invoked": any(output.llm_invoked for output in classifier_outputs),
            "transition_candidates": len(rules_result.transition_or_duplicate),
            "route_log": classifier_route_log,
            "llm_mode": llm_mode,
        },
    )

    severity = assign_severity(rules_result, classifier_outputs)
    finding = build_finding(event, rules_result, severity.severity, classifier_outputs, llm_adapter)
    logger.log(
        "final_finding_emitted",
        {
            "finding_id": finding.finding_id,
            "severity": finding.severity,
            "duplicate_type": finding.duplicate_type,
            "max_overlap_days": finding.computed.get("max_overlap_days", 0),
        },
    )

    clinically_significant_duplicate = (
        finding.severity in {"review_required", "block"}
        and int(finding.computed.get("max_overlap_days", 0)) >= 4
    )

    return {
        "clinically_significant_duplicate": clinically_significant_duplicate,
        "finding": finding.to_serializable(),
        "decision_trace": {
            **rules_result.trace(),
            "classifier_outputs": [x.to_serializable() for x in classifier_outputs],
            "classifier_route_log": classifier_route_log,
            "severity_rationale": severity.rationale,
            "claude_invoked": any(x.llm_invoked for x in classifier_outputs),
            "llm_policy": "ambiguous_same_ingredient_diff_strength_only",
            "llm_mode": llm_mode,
        },
        "boundary": BOUNDARY_STATEMENT,
        "metrics_placeholders": METRICS_PLACEHOLDERS,
        "audit_log": logger.records,
    }


def run_sample(data_dir: Path) -> Dict[str, Any]:
    pending = json.loads((data_dir / "pending_rx.json").read_text(encoding="utf-8"))
    history = json.loads((data_dir / "med_history.json").read_text(encoding="utf-8"))
    return run_duplicate_check(pending, history)


def run_review_case(
    review_id: str,
    clinician_acknowledged: bool = False,
    reason_code: str | None = None,
) -> Dict[str, Any]:
    case = load_case_by_id(review_id)
    service = TransmissionService()
    return service.process_case(case, clinician_acknowledged=clinician_acknowledged, reason_code=reason_code)


def main() -> None:
    result = run_sample(Path("data"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
