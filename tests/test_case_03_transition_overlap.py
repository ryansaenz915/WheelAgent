from src.review_cases import load_case_by_id
from src.transmission_service import TransmissionService


def test_case_03_transition_overlap():
    case = load_case_by_id("case_03")
    result = TransmissionService().process_case(case)
    assert result["finding"]["computed"]["max_overlap_days"] == 11
    assert result["finding"]["severity"] == "review_required"
    assert result["decision_trace"]["ambiguous_classifier_path_invoked"] is True
