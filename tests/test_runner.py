import json
from pathlib import Path

from src.runner import run_duplicate_check


def test_runner_returns_expected_top_level_shape():
    data_dir = Path(__file__).resolve().parents[1] / "data"
    pending = json.loads((data_dir / "pending_rx.json").read_text(encoding="utf-8"))
    history = json.loads((data_dir / "med_history.json").read_text(encoding="utf-8"))
    result = run_duplicate_check(pending, history)

    assert "finding" in result
    assert "decision_trace" in result
    assert "audit_log" in result
    assert result["boundary"]
