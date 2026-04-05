from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Protocol

from .dosespot_models import DoseSpotPrescriptionPayload, MedicationHistoryRequest, PharmacyResolution, TransmissionStatus


class DoseSpotClient(Protocol):
    def get_medication_history(self, request: MedicationHistoryRequest) -> List[Dict[str, Any]]: ...

    def search_medications(self, name: str) -> List[Dict[str, Any]]: ...

    def basic_search_medications(self, name: str) -> List[Dict[str, Any]]: ...

    def select_medication(self, rxcui: str | None, name: str, strength: str | None) -> Dict[str, Any]: ...

    def resolve_pharmacy(self, ncpdp_id: str, pharmacy_name: str) -> PharmacyResolution: ...

    def create_or_update_prescription(self, payload: DoseSpotPrescriptionPayload) -> Dict[str, Any]: ...

    def send_prescription(self, prescription_id: str) -> TransmissionStatus: ...

    def send_epcs_prescription(self, prescription_id: str) -> TransmissionStatus: ...


class MockDoseSpotClient:
    def __init__(self, fail_history: bool = False) -> None:
        self.fail_history = fail_history
        self.calls: List[Dict[str, Any]] = []
        self._next_id = 1000

    def _log(self, endpoint: str, payload: Dict[str, Any]) -> None:
        self.calls.append({"endpoint": endpoint, "payload": payload})

    def get_medication_history(self, request: MedicationHistoryRequest) -> List[Dict[str, Any]]:
        self._log(
            "GET api/patients/{patientId}/medications/history",
            {
                "patient_id": request.patient_id,
                "start": request.start.isoformat(),
                "end": request.end.isoformat(),
                "onBehalfOfUserId": request.on_behalf_of_user_id,
            },
        )
        if self.fail_history:
            raise RuntimeError("Medication history unavailable from DoseSpot")
        return []

    def search_medications(self, name: str) -> List[Dict[str, Any]]:
        self._log("GET api/medications/search", {"name": name})
        return [{"DisplayName": name, "RxCUI": None}]

    def basic_search_medications(self, name: str) -> List[Dict[str, Any]]:
        self._log("GET api/medications/basicSearch", {"name": name})
        return [{"DisplayName": name}]

    def select_medication(self, rxcui: str | None, name: str, strength: str | None) -> Dict[str, Any]:
        self._log("GET api/medications/select", {"RxCUI": rxcui, "Name": name, "Strength": strength})
        return {"DisplayName": name, "RxCUI": rxcui}

    def resolve_pharmacy(self, ncpdp_id: str, pharmacy_name: str) -> PharmacyResolution:
        self._log("GET api/pharmacies/search", {"ncpdpID": ncpdp_id, "name": pharmacy_name})
        mock_id = f"ph_{ncpdp_id}" if ncpdp_id else None
        return PharmacyResolution(
            pharmacy_name=pharmacy_name,
            ncpdp_id=ncpdp_id,
            dosespot_pharmacy_id_nullable=mock_id,
            resolution_status="resolved" if mock_id else "unresolved",
        )

    def create_or_update_prescription(self, payload: DoseSpotPrescriptionPayload) -> Dict[str, Any]:
        self._log("POST api/prescriptions", asdict(payload))
        self._next_id += 1
        return {"prescription_id": f"rx_{self._next_id}", "status": "pending"}

    def send_prescription(self, prescription_id: str) -> TransmissionStatus:
        self._log("POST api/prescriptions/send", {"prescription_id": prescription_id})
        return TransmissionStatus(attempted=True, success=True, channel="send", message="sent", prescription_id=prescription_id)

    def send_epcs_prescription(self, prescription_id: str) -> TransmissionStatus:
        self._log("POST api/prescriptions/sendEpcs", {"prescription_id": prescription_id})
        return TransmissionStatus(
            attempted=True,
            success=True,
            channel="sendEpcs",
            message="sent epcs",
            prescription_id=prescription_id,
        )


class LiveDoseSpotClient(MockDoseSpotClient):
    # Placeholder for live integration. Keep all UI/business logic isolated from raw API shapes.
    pass
