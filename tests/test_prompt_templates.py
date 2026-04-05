from src.prompts import CLASSIFICATION_USER_PROMPT_TEMPLATE, FINDING_WORDING_USER_PROMPT_TEMPLATE


def test_classification_prompt_template_formats() -> None:
    out = CLASSIFICATION_USER_PROMPT_TEMPLATE.format(
        PENDING_RX_JSON="{}",
        HISTORY_ENTRY_JSON="{}",
        OVERLAP_DAYS=1,
        TRUE_FALSE_SAME_INGREDIENT="true",
        TRUE_FALSE_SAME_STRENGTH="false",
        TRUE_FALSE_SAME_ROUTE="true",
        TRUE_FALSE_DIFF_PHARMACY="false",
    )
    assert "classification" in out


def test_finding_prompt_template_formats() -> None:
    out = FINDING_WORDING_USER_PROMPT_TEMPLATE.format(
        PENDING_RX_JSON="{}",
        RELEVANT_HISTORY_JSON_ARRAY="[]",
        OVERLAP_SUMMARY_JSON="{}",
        CLASSIFIER_OUTPUTS_JSON_ARRAY="[]",
    )
    assert "recommended_actions" in out
