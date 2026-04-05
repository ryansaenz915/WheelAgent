from src.llm import ClaudeAdapter
from src.models import MedicationHistoryEntry, PendingPrescriptionEvent
from src.review_cases import load_case_by_id
from src.rules import apply_rules


def _ambiguous_candidate():
    case = load_case_by_id("case_03")
    event = PendingPrescriptionEvent.from_dict(case["pending_rx"])
    rows = [MedicationHistoryEntry.from_dict(r) for r in case["med_history"]]
    rules = apply_rules(event, rows)
    return event, rules.transition_or_duplicate[0]


def test_llm_route_invokes_for_ambiguous_transition():
    adapter = ClaudeAdapter()
    _, candidate = _ambiguous_candidate()
    route = adapter.explain_route_for_candidate(candidate)
    assert route["decision"] == "invoke"


def test_llm_route_skips_non_ambiguous_candidate():
    adapter = ClaudeAdapter()
    _, candidate = _ambiguous_candidate()
    candidate.llm_needed = False
    route = adapter.explain_route_for_candidate(candidate)
    assert route["decision"] == "skip"


def test_llm_invalid_schema_falls_back(monkeypatch):
    adapter = ClaudeAdapter()
    adapter.use_llm = True
    adapter.has_api_key = True
    adapter.client = object()
    event, candidate = _ambiguous_candidate()

    def _bad_call(system_prompt: str, user_prompt: str):
        return {"classification": "bad"}

    monkeypatch.setattr(adapter, "_call_claude_json", _bad_call)
    output = adapter.classify_ambiguous_candidate(event=event, candidate=candidate)
    assert output.classification == "uncertain"
    assert output.llm_invoked is False
