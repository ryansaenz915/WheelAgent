import json
from pathlib import Path

from src.models import MedicationHistoryEntry, PendingPrescriptionEvent
from src.rules import apply_rules


def _scenario():
    data_dir = Path(__file__).resolve().parents[1] / "data"
    pending = json.loads((data_dir / "pending_rx.json").read_text(encoding="utf-8"))
    history = json.loads((data_dir / "med_history.json").read_text(encoding="utf-8"))
    return PendingPrescriptionEvent.from_dict(pending), [MedicationHistoryEntry.from_dict(x) for x in history]


def test_unrelated_metformin_is_ignored():
    event, rows = _scenario()
    result = apply_rules(event, rows)
    metformin = [r for r in result.all_rows if "metformin" in r.drug_display.lower()]
    assert metformin
    assert all("ingredient_mismatch" in r.ignore_reasons for r in metformin)


def test_same_ingredient_same_strength_overlap_ge_4_is_duplicate():
    event, rows = _scenario()
    result = apply_rules(event, rows)
    assert any(r.classification == "true_duplicate_same_drug" and r.overlap_days >= 4 for r in result.all_rows)


def test_different_strength_overlap_gt_0_is_ambiguous():
    event, rows = _scenario()
    rows.append(
        MedicationHistoryEntry.from_dict(
            {
                "drug_display": "Semaglutide 0.5mg/dose (Ozempic)",
                "ingredient": "semaglutide",
                "strength": "0.5 mg",
                "route": "subcutaneous",
                "fill_date": "2026-03-18",
                "days_supply": 21,
                "status": "dispensed",
                "pharmacy": "CVS #8821, Austin TX",
            }
        )
    )
    result = apply_rules(event, rows)
    assert any(r.classification == "transition_or_duplicate" and r.overlap_days > 0 for r in result.all_rows)


def test_multi_pharmacy_risk_amplifier_set():
    event, rows = _scenario()
    result = apply_rules(event, rows)
    assert result.multi_pharmacy_risk_amplifier is True
