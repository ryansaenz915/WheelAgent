from datetime import datetime, timezone

from src.metrics import compute_metrics
from src.review_outcomes import load_post_send_outcomes, load_review_outcomes


def test_metrics_segmentation_filters_by_review_type():
    metrics = compute_metrics(
        load_review_outcomes(),
        load_post_send_outcomes(),
        window="90d",
        now=datetime.now(timezone.utc),
        filters={"review_type": "duplicate_exact"},
    )
    assert metrics["counts"]["reviews_total"] > 0
    assert set(metrics["segments"]["review_type"].keys()) == {"duplicate_exact"}


def test_metrics_segmentation_filters_by_llm_mode():
    metrics = compute_metrics(
        load_review_outcomes(),
        load_post_send_outcomes(),
        window="90d",
        now=datetime.now(timezone.utc),
        filters={"llm_mode": "claude_assisted"},
    )
    if metrics["counts"]["reviews_total"] > 0:
        assert set(metrics["segments"]["used_llm"].keys()) == {"True"}


def test_metrics_has_qa_fields():
    metrics = compute_metrics(load_review_outcomes(), load_post_send_outcomes(), window="90d", now=datetime.now(timezone.utc))
    assert "sampled_info_case_reviews" in metrics["qa"]
    assert "block_confirmation_rate" in metrics["qa"]
