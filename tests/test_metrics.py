from datetime import datetime, timezone

from src.metrics import compute_metrics
from src.review_outcomes import load_post_send_outcomes, load_review_outcomes


def test_false_positive_rate_computed():
    m = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    assert m["metrics"]["false_positive_rate"] is not None


def test_high_severity_precision_computed():
    m = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    assert m["metrics"]["high_severity_precision"] is not None


def test_clinician_action_rate_computed():
    m = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    assert m["metrics"]["clinician_action_rate"] is not None


def test_median_workflow_time_computed():
    m = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    assert m["metrics"]["median_added_workflow_time_seconds"] is not None


def test_post_send_duplicate_friction_rate_computed():
    m = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    assert m["metrics"]["post_send_duplicate_friction_rate"] is not None
