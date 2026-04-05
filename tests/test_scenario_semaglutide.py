import json
from pathlib import Path

from src.runner import run_duplicate_check


def test_full_sample_scenario_expected_output():
    data_dir = Path(__file__).resolve().parents[1] / "data"
    pending = json.loads((data_dir / "pending_rx.json").read_text(encoding="utf-8"))
    history = json.loads((data_dir / "med_history.json").read_text(encoding="utf-8"))
    result = run_duplicate_check(pending, history)
    finding = result["finding"]

    assert finding["severity"] == "review_required"
    assert finding["duplicate_type"] == "same_drug_same_strength"
    assert finding["computed"]["max_overlap_days"] == 11
    assert any(
        e["drug"] == "Semaglutide 1mg/dose (Ozempic)"
        and e["fill_date"] == "2026-03-01"
        and e["pharmacy"] == "Costco Pharmacy, Round Rock TX"
        for e in finding["evidence"]
    )
    assert any(a["action"] == "approve_prescription" for a in finding["recommended_actions"])
