from src.review_outcomes import compute_resolution_duration_seconds, derive_fields, validate_review_outcome


def _base_outcome():
    return {
        "review_id": "case_x",
        "case_type": "duplicate_exact",
        "finding_id": "f_x",
        "opened_at": "2026-03-20T10:00:00+00:00",
        "resolved_at": "2026-03-20T10:05:00+00:00",
        "resolution_duration_seconds": 0,
        "clinician_id": "clin",
        "severity_at_open": "review_required",
        "agent_classification": "true_duplicate",
        "duplicate_type": "same_drug_same_strength",
        "max_overlap_days": 11,
        "used_llm": False,
        "rules_triggered": [],
        "multi_pharmacy_flag": False,
        "clinician_adjudication": "true_positive",
        "clinician_meaningful_duplicate": True,
        "clinician_action_taken": "edit",
        "changed_prescribing_behavior": True,
        "interruptive_alert_appropriate": True,
        "override_used": False,
        "override_reason_code": None,
        "patient_confirmation_completed": True,
        "pharmacy_confirmation_completed": False,
        "free_text_notes": "",
        "transmission_attempted": False,
        "transmission_completed": False,
        "post_send_followup_flag": False,
        "post_send_followup_type": "none",
    }


def test_review_required_case_requires_fields():
    o = _base_outcome()
    o["clinician_adjudication"] = None
    ok, msg = validate_review_outcome(o)
    assert ok is False
    assert "clinician_adjudication" in msg


def test_override_reason_required_when_override_used():
    o = _base_outcome()
    o["override_used"] = True
    o["override_reason_code"] = None
    ok, msg = validate_review_outcome(o)
    assert ok is False
    assert "override_reason_code" in msg


def test_resolution_duration_computed_correctly():
    assert compute_resolution_duration_seconds("2026-03-20T10:00:00+00:00", "2026-03-20T10:01:30+00:00") == 90


def test_is_false_positive_derivation():
    o = _base_outcome()
    o["clinician_adjudication"] = "false_positive"
    o = derive_fields(o)
    assert o["is_false_positive"] is True


def test_is_behavior_change_derivation():
    o = _base_outcome()
    o["clinician_action_taken"] = "proceed"
    o = derive_fields(o)
    assert o["is_behavior_change"] is False
    o["clinician_action_taken"] = "cancel"
    o = derive_fields(o)
    assert o["is_behavior_change"] is True
