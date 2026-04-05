from src.review_cases import load_case_by_id
from src.transmission_service import TransmissionService


def test_case_02_transition_no_overlap():
    case = load_case_by_id("case_02")
    result = TransmissionService().process_case(case)
    assert result["finding"]["computed"]["max_overlap_days"] == 0
    assert result["finding"]["severity"] == "info"
    assert result["decision_trace"]["classification"] == "likely_transition"
