from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional


@dataclass
class Patient:
    patient_id: str
    first_name: str
    last_name: str
    dob: date

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Patient":
        return Patient(
            patient_id=data["patient_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            dob=date.fromisoformat(data["dob"]),
        )


@dataclass
class Prescriber:
    npi: str
    display_name: str
    dosespot_user_id: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Prescriber":
        return Prescriber(
            npi=data["npi"],
            display_name=data["display_name"],
            dosespot_user_id=data["dosespot_user_id"],
        )


@dataclass
class Prescription:
    drug_display: str
    route: str
    sig: str
    days_supply: int
    rxcui: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Prescription":
        return Prescription(
            drug_display=data["drug_display"],
            route=data["route"],
            sig=data["sig"],
            days_supply=int(data["days_supply"]),
            rxcui=data.get("rxcui"),
        )


@dataclass
class Pharmacy:
    name: str
    ncpdp_id: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Pharmacy":
        return Pharmacy(name=data["name"], ncpdp_id=data["ncpdp_id"])


@dataclass
class PendingPrescriptionEvent:
    event_id: str
    event_time: datetime
    patient: Patient
    prescriber: Prescriber
    prescription: Prescription
    pharmacy: Pharmacy
    program: str
    status: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PendingPrescriptionEvent":
        return PendingPrescriptionEvent(
            event_id=data["event_id"],
            event_time=datetime.fromisoformat(data["event_time"]),
            patient=Patient.from_dict(data["patient"]),
            prescriber=Prescriber.from_dict(data["prescriber"]),
            prescription=Prescription.from_dict(data["prescription"]),
            pharmacy=Pharmacy.from_dict(data["pharmacy"]),
            program=data["program"],
            status=data["status"],
        )

    def to_serializable(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["event_time"] = self.event_time.isoformat()
        payload["patient"]["dob"] = self.patient.dob.isoformat()
        return payload


@dataclass
class MedicationHistoryEntry:
    drug_display: str
    ingredient: str
    strength: str
    route: str
    fill_date: date
    days_supply: int
    status: str
    pharmacy: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MedicationHistoryEntry":
        return MedicationHistoryEntry(
            drug_display=data["drug_display"],
            ingredient=data.get("ingredient", ""),
            strength=data.get("strength", ""),
            route=data.get("route", ""),
            fill_date=date.fromisoformat(data["fill_date"]),
            days_supply=int(data["days_supply"]),
            status=data.get("status", "unknown"),
            pharmacy=data.get("pharmacy", "Unknown"),
        )

    def to_serializable(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["fill_date"] = self.fill_date.isoformat()
        return payload


@dataclass
class DuplicateCandidate:
    drug_display: str
    ingredient: str
    strength: str
    route: str
    fill_date: date
    days_supply: int
    status: str
    pharmacy: str
    supply_end_date: date
    overlap_days: int
    same_ingredient: bool
    same_route: bool
    same_strength: bool
    different_pharmacy: bool
    classification: str
    llm_needed: bool
    rules_triggered: List[str] = field(default_factory=list)
    ignore_reasons: List[str] = field(default_factory=list)
    risk_amplifier: bool = False

    def to_trace(self) -> Dict[str, Any]:
        return {
            "drug_display": self.drug_display,
            "ingredient": self.ingredient,
            "strength": self.strength,
            "route": self.route,
            "fill_date": self.fill_date.isoformat(),
            "days_supply": self.days_supply,
            "status": self.status,
            "pharmacy": self.pharmacy,
            "supply_end_date": self.supply_end_date.isoformat(),
            "overlap_days": self.overlap_days,
            "same_ingredient": self.same_ingredient,
            "same_route": self.same_route,
            "same_strength": self.same_strength,
            "different_pharmacy": self.different_pharmacy,
            "classification": self.classification,
            "llm_needed": self.llm_needed,
            "risk_amplifier": self.risk_amplifier,
            "rules_triggered": self.rules_triggered,
            "ignore_reasons": self.ignore_reasons,
        }


@dataclass
class ClassifierOutput:
    classification: str
    rationale: List[str]
    confidence: str
    recommended_severity: str
    candidate_drug: str
    llm_invoked: bool

    def to_serializable(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DuplicateRxFinding:
    finding_id: str
    severity: str
    title: str
    summary: str
    drug_class: str
    duplicate_type: str
    computed: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    limitations: List[str]
    recommended_actions: List[Dict[str, str]]
    clinician_response: Dict[str, Any]

    def to_serializable(self) -> Dict[str, Any]:
        return asdict(self)
