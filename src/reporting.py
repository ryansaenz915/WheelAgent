from __future__ import annotations

from typing import Any, Dict, List

from .validation import validate_report_payload


def build_assignment_coverage_report(
    metrics_payload: Dict[str, Any],
    queue_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    scenario_types = sorted({q.get("review_type", "other") for q in queue_rows})
    assignment_rows = [
        "Problem summary",
        "Scope boundary",
        "90-day success metrics",
        "Agent architecture",
        "Duplicate detection logic",
        "Prompt design",
        "Escalation model",
        "Working prototype output",
        "Clinical review capture",
        "Metrics reporting",
    ]

    assignment_feature_matrix = [
        {
            "assignment_prompt_area": "Pre-transmission duplicate check",
            "implemented_feature": "Rules-first overlap engine with same-ingredient and same-class paths",
            "where_to_view": "Review Queue and Review Detail",
            "rules_ai_human": "Rules + Human",
            "scenarios": "duplicate_exact, class_overlap_high_risk",
        },
        {
            "assignment_prompt_area": "Ambiguous transition adjudication",
            "implemented_feature": "Claude-assisted classifier only for ambiguous transitions",
            "where_to_view": "Review Detail decision trace",
            "rules_ai_human": "Rules + AI + Human",
            "scenarios": "duplicate_transition",
        },
        {
            "assignment_prompt_area": "Clinical adjudication capture",
            "implemented_feature": "Structured review form with validation and send gating",
            "where_to_view": "Review Detail",
            "rules_ai_human": "Human + Rules",
            "scenarios": "all",
        },
        {
            "assignment_prompt_area": "Operational metrics",
            "implemented_feature": "90-day KPI cards, segmentation, QA rates, export",
            "where_to_view": "Metrics Dashboard",
            "rules_ai_human": "Rules",
            "scenarios": "all",
        },
    ]

    scenario_coverage_matrix = [
        {"scenario": "duplicate_exact", "exact_duplicate": True, "transition_no_overlap": False, "transition_overlap": False, "early_refill_suppression": False, "same_class_high_risk": False, "polypharmacy_safety_review": False},
        {"scenario": "duplicate_transition", "exact_duplicate": False, "transition_no_overlap": True, "transition_overlap": True, "early_refill_suppression": False, "same_class_high_risk": False, "polypharmacy_safety_review": False},
        {"scenario": "early_refill", "exact_duplicate": False, "transition_no_overlap": False, "transition_overlap": False, "early_refill_suppression": True, "same_class_high_risk": False, "polypharmacy_safety_review": False},
        {"scenario": "class_overlap_high_risk", "exact_duplicate": False, "transition_no_overlap": False, "transition_overlap": False, "early_refill_suppression": False, "same_class_high_risk": True, "polypharmacy_safety_review": False},
        {"scenario": "polypharmacy_interaction", "exact_duplicate": False, "transition_no_overlap": False, "transition_overlap": False, "early_refill_suppression": False, "same_class_high_risk": False, "polypharmacy_safety_review": True},
    ]

    report = {
        "sections": [
            "Executive summary",
            "Problem framing",
            "Scope boundary",
            "Agent workflow map",
            "Rules vs AI map",
            "90-day metrics dashboard",
            "Scenario coverage",
            "Prototype evidence",
            "How the assignment is addressed",
            "How to grade this prototype",
        ],
        "workflow_steps": [
            "pending transmission trigger",
            "retrieve DoseSpot medication history",
            "normalize medication identity",
            "compute supply windows and overlap",
            "apply deterministic rules",
            "route ambiguous cases to Claude if needed",
            "generate structured finding",
            "require clinician review if needed",
            "capture review outcome",
            "compute metrics",
        ],
        "rules_vs_ai": [
            {"task": "patient verification", "mode": "rules"},
            {"task": "medication identity normalization", "mode": "rules/adapter"},
            {"task": "overlap arithmetic", "mode": "rules"},
            {"task": "duplicate exact-match logic", "mode": "rules"},
            {"task": "dose transition ambiguity", "mode": "ai optional"},
            {"task": "final clinician decision", "mode": "human"},
            {"task": "metrics capture", "mode": "rules"},
        ],
        "assignment_mapping_rows": assignment_rows,
        "assignment_feature_matrix": assignment_feature_matrix,
        "scenario_coverage_matrix": scenario_coverage_matrix,
        "reviewer_guidance": {
            "first_click": "Review Queue",
            "flagship_case": "case_01",
            "best_transition_case": "case_03",
            "metrics_source": "data/mock_review_outcomes.json and data/mock_post_send_outcomes.json",
            "instrumentation_path": "src/review_outcomes.py",
        },
        "scenario_types": scenario_types,
        "metric_cards": [
            "false_positive_rate",
            "high_severity_precision",
            "clinician_action_rate",
            "median_added_workflow_time_seconds",
            "post_send_duplicate_friction_rate",
        ],
        "metrics": metrics_payload.get("metrics", {}),
    }

    ok, msg = validate_report_payload(report)
    if not ok:
        raise ValueError(msg)
    return report
