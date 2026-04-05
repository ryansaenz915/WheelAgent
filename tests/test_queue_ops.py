from datetime import datetime, timezone

from src.metrics import compute_metrics
from src.queue_ops import build_queue_summary, filter_queue_rows, queue_reason, sort_queue_rows
from src.review_cases import load_review_queue
from src.review_outcomes import load_post_send_outcomes, load_review_outcomes


def test_queue_reason_labels_cover_seed_types():
    assert queue_reason("duplicate_exact") == "Exact duplicate"
    assert queue_reason("duplicate_transition") == "Ambiguous transition"
    assert queue_reason("class_overlap_high_risk") == "Same-class high risk"


def test_queue_filtering_by_severity_and_type():
    rows = load_review_queue()
    filtered = filter_queue_rows(rows, {"severity": "block", "review_type": "class_overlap_high_risk"})
    assert len(filtered) == 1
    assert filtered[0]["review_id"] == "case_05"


def test_queue_sorting_by_updated_at_desc():
    rows = load_review_queue()
    sorted_rows = sort_queue_rows(rows, "last_updated")
    latest = max(rows, key=lambda x: datetime.fromisoformat(x["updated_at"]))
    assert sorted_rows[0]["review_id"] == latest["review_id"]


def test_queue_summary_includes_metric_rates():
    rows = load_review_queue()
    metrics = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), now=datetime.now(timezone.utc))
    summary = build_queue_summary(rows, metrics)
    assert "false_positive_rate_90d" in summary
    assert "clinician_action_rate_90d" in summary
