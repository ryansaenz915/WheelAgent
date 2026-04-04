from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .finding import build_finding
from .llm import ClaudeAdapter
from .logging_utils import AuditLogger
from .models import ClassifierOutput, MedicationHistoryEntry, PendingPrescriptionEvent
from .rules import apply_rules
from .severity import assign_severity

BOUNDARY_STATEMENT = (
    "This is a medication reconciliation assist only. "
    "Clinician judgment remains the final decision-maker."
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
    classifier_outputs: List[ClassifierOutput] = []
    for candidate in rules_result.transition_or_duplicate:
        classifier_outputs.append(llm_adapter.classify_ambiguous_candidate(event, candidate))
    logger.log(
        "llm_invoked_or_skipped",
        {
            "llm_invoked": any(output.llm_invoked for output in classifier_outputs),
            "transition_candidates": len(rules_result.transition_or_duplicate),
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
            "severity_rationale": severity.rationale,
            "claude_invoked": any(x.llm_invoked for x in classifier_outputs),
        },
        "boundary": BOUNDARY_STATEMENT,
        "metrics_placeholders": METRICS_PLACEHOLDERS,
        "audit_log": logger.records,
    }


def run_sample(data_dir: Path) -> Dict[str, Any]:
    pending = json.loads((data_dir / "pending_rx.json").read_text(encoding="utf-8"))
    history = json.loads((data_dir / "med_history.json").read_text(encoding="utf-8"))
    return run_duplicate_check(pending, history)


def main() -> None:
    result = run_sample(Path("data"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
