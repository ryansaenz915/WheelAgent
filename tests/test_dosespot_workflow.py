from src.dosespot_client import MockDoseSpotClient
from src.review_cases import load_case_by_id
from src.transmission_service import TransmissionService


def test_history_retrieval_occurs_before_transmit():
    client = MockDoseSpotClient()
    service = TransmissionService(client=client)
    case = load_case_by_id("case_01")
    service.process_case(case, clinician_acknowledged=True, reason_code="renewal")
    endpoints = [x["endpoint"] for x in client.calls]
    hist_idx = endpoints.index("GET api/patients/{patientId}/medications/history")
    send_idx = endpoints.index("POST api/prescriptions/send")
    assert hist_idx < send_idx


def test_failed_history_retrieval_does_not_silent_pass():
    client = MockDoseSpotClient(fail_history=True)
    service = TransmissionService(client=client)
    case = load_case_by_id("case_01")
    result = service.process_case(case, clinician_acknowledged=False)
    assert "Medication history unavailable" in result["finding"]["title"]
    assert result["post_send_state"]["send_attempted"] is False


def test_review_required_requires_ack_before_send():
    client = MockDoseSpotClient()
    service = TransmissionService(client=client)
    case = load_case_by_id("case_01")
    result = service.process_case(case, clinician_acknowledged=False)
    assert result["finding"]["severity"] == "review_required"
    assert result["post_send_state"]["transmission_ready"] is False
