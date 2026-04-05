from datetime import datetime, timezone

from src.metrics import compute_metrics
from src.reporting import build_assignment_coverage_report
from src.review_cases import load_review_queue
from src.review_outcomes import load_post_send_outcomes, load_review_outcomes


def test_report_contains_required_sections():
    payload = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    report = build_assignment_coverage_report(payload, load_review_queue())
    required = {
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
    }
    assert required.issubset(set(report["sections"]))


def test_assignment_mapping_rows_complete():
    payload = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    report = build_assignment_coverage_report(payload, load_review_queue())
    required_rows = {
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
    }
    assert required_rows.issubset(set(report["assignment_mapping_rows"]))


def test_scenario_coverage_includes_all_seed_types():
    payload = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    report = build_assignment_coverage_report(payload, load_review_queue())
    expected = {"duplicate_exact", "duplicate_transition", "early_refill", "class_overlap_high_risk", "polypharmacy_interaction"}
    assert expected.issubset(set(report["scenario_types"]))


def test_metrics_section_has_all_five_cards():
    payload = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    report = build_assignment_coverage_report(payload, load_review_queue())
    expected = {
        "false_positive_rate",
        "high_severity_precision",
        "clinician_action_rate",
        "median_added_workflow_time_seconds",
        "post_send_duplicate_friction_rate",
    }
    assert expected.issubset(set(report["metric_cards"]))
