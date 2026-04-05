from src.review_cases import load_case_by_id
from src.transmission_service import TransmissionService


def test_case_05_same_class_anticoagulant():
    case = load_case_by_id("case_05")
    result = TransmissionService().process_case(case)
    assert result["finding"]["computed"]["max_overlap_days"] == 15
    assert result["decision_trace"].get("same_class") is True
    assert result["finding"]["severity"] == "review_required"
