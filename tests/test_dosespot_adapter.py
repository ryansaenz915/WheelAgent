import json
from pathlib import Path

from src.dosespot_adapter import to_dosespot_prescription_payload, to_history_request, to_normalized_medication
from src.models import PendingPrescriptionEvent


def _sample_event():
    data_dir = Path(__file__).resolve().parents[1] / "data"
    pending = json.loads((data_dir / "pending_rx.json").read_text(encoding="utf-8"))
    return PendingPrescriptionEvent.from_dict(pending)


def test_history_request_includes_on_behalf_of_user_id():
    event = _sample_event()
    req = to_history_request(event, lookback_days=180)
    assert req.on_behalf_of_user_id == event.prescriber.dosespot_user_id


def test_normalized_medication_supports_non_rxcui_fields():
    med = to_normalized_medication(
        {
            "drug_display": "Semaglutide 1mg/dose (Ozempic)",
            "ingredient": "semaglutide",
            "strength": "1 mg",
            "route": "subcutaneous",
            "DrugDBCode": "D123",
            "DrugDBCodeQualifier": "MEDISPAN",
        }
    )
    assert med.rxcui_nullable is None
    assert med.drug_db_code_nullable == "D123"
    assert med.drug_db_code_qualifier_nullable == "MEDISPAN"


def test_prescription_payload_contains_required_shape_fields():
    event = _sample_event()
    payload = to_dosespot_prescription_payload(event, resolved_pharmacy_id="ph_123456")
    assert payload.display_name
    assert payload.days_supply == 90
    assert payload.on_behalf_of_user_id == event.prescriber.dosespot_user_id
    assert payload.pharmacy_id == "ph_123456"
