from src.review_cases import load_case_by_id
from src.transmission_service import TransmissionService


def test_case_04_early_refill():
    case = load_case_by_id("case_04")
    result = TransmissionService().process_case(case)
    assert result["finding"]["computed"]["max_overlap_days"] == 3
    assert result["finding"]["severity"] == "info"
    assert "early_refill_suppression" in result["decision_trace"].get("route_reason", [])
