from src.review_cases import load_case_by_id
from src.transmission_service import TransmissionService


def test_case_06_polypharmacy_qt_risk():
    case = load_case_by_id("case_06")
    result = TransmissionService().process_case(case)
    assert result["review_type"] == "polypharmacy_interaction"
    assert result["finding"]["severity"] == "review_required"
    interaction = result["finding"].get("interaction", {})
    assert interaction.get("risk_group") == "QT_PROLONGATION_RISK"
    drugs = set(interaction.get("implicated_drugs", []))
    assert {"Azithromycin", "Citalopram", "Ondansetron"}.issubset(drugs)
