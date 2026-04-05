from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class MedicationHistoryRequest:
    patient_id: str
    start: date
    end: date
    on_behalf_of_user_id: str


@dataclass
class NormalizedMedication:
    # Keep this migration-safe because DoseSpot is moving to API v2 and Medi-Span identifiers.
    source_display_name: str
    normalized_display_name: str
    ingredient_name: str
    strength: str
    route: str
    rxcui_nullable: Optional[str]
    drug_db_code_nullable: Optional[str]
    drug_db_code_qualifier_nullable: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PharmacyResolution:
    pharmacy_name: str
    ncpdp_id: str
    dosespot_pharmacy_id_nullable: Optional[str]
    resolution_status: str


@dataclass
class DoseSpotPrescriptionPayload:
    display_name: str
    ndc: Optional[str]
    drug_db_code: Optional[str]
    drug_db_code_qualifier: Optional[str]
    refills: int
    days_supply: int
    dispense_unit_id: Optional[str]
    quantity: Optional[float]
    directions: str
    pharmacy_id: Optional[str]
    effective_date: str
    rx_reference_number: Optional[str]
    eligibility_id: Optional[str]
    non_dosespot_prescription_id: Optional[str]
    on_behalf_of_user_id: str
    diagnosis_id: Optional[str]
    is_refill_replace: bool
    is_urgent: bool
    supervisor_id: Optional[str]
    status: str
    comment: Optional[str]
    encounter: Optional[str]


@dataclass
class TransmissionStatus:
    attempted: bool
    success: bool
    channel: str
    message: str
    prescription_id: Optional[str] = None
