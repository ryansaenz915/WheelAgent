from datetime import datetime, timezone

from src.metrics import compute_metrics
from src.reporting import build_assignment_coverage_report
from src.review_cases import load_review_queue
from src.review_outcomes import load_post_send_outcomes, load_review_outcomes


def test_assignment_report_contains_feature_and_scenario_matrices():
    payload = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    report = build_assignment_coverage_report(payload, load_review_queue())
    assert isinstance(report["assignment_feature_matrix"], list)
    assert isinstance(report["scenario_coverage_matrix"], list)
    assert report["reviewer_guidance"]["first_click"] == "Review Queue"
