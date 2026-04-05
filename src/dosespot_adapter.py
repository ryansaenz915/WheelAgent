from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from .dosespot_models import DoseSpotPrescriptionPayload, MedicationHistoryRequest, NormalizedMedication
from .models import PendingPrescriptionEvent
from .normalize import extract_ingredient_from_display, normalize_route, parse_strength


def to_history_request(event: PendingPrescriptionEvent, lookback_days: int = 180) -> MedicationHistoryRequest:
    return MedicationHistoryRequest(
        patient_id=event.patient.patient_id,
        start=event.event_time.date() - timedelta(days=lookback_days),
        end=event.event_time.date(),
        on_behalf_of_user_id=event.prescriber.dosespot_user_id,
    )


def to_normalized_medication(source: Dict[str, Any]) -> NormalizedMedication:
    display = source.get("drug_display") or source.get("DisplayName") or ""
    return NormalizedMedication(
        source_display_name=display,
        normalized_display_name=display.strip(),
        ingredient_name=(source.get("ingredient") or extract_ingredient_from_display(display)).lower(),
        strength=source.get("strength") or parse_strength(display),
        route=normalize_route(source.get("route", "")),
        rxcui_nullable=source.get("rxcui") or source.get("RxCUI"),
        drug_db_code_nullable=source.get("DrugDBCode"),
        drug_db_code_qualifier_nullable=source.get("DrugDBCodeQualifier"),
    )


def to_dosespot_prescription_payload(
    event: PendingPrescriptionEvent,
    resolved_pharmacy_id: str | None,
) -> DoseSpotPrescriptionPayload:
    rx = event.prescription
    return DoseSpotPrescriptionPayload(
        display_name=rx.drug_display,
        ndc=None,
        drug_db_code=None,
        drug_db_code_qualifier=None,
        refills=0,
        days_supply=rx.days_supply,
        dispense_unit_id=None,
        quantity=None,
        directions=rx.sig,
        pharmacy_id=resolved_pharmacy_id,
        effective_date=event.event_time.date().isoformat(),
        rx_reference_number=None,
        eligibility_id=None,
        non_dosespot_prescription_id=event.event_id,
        on_behalf_of_user_id=event.prescriber.dosespot_user_id,
        diagnosis_id=None,
        is_refill_replace=False,
        is_urgent=False,
        supervisor_id=None,
        status=event.status,
        comment=None,
        encounter=event.program,
    )
