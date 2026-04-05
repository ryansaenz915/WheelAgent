# LLM Mode I/O Spec for Duplicate Prescription Agent

## Purpose
This document defines expected LLM-related input/output contracts for evaluating and comparing model behavior across providers.

## Runtime Mode Contract
The app supports three execution modes for ambiguous classifier logic:
- `disabled`: `USE_LLM=false`
- `mock`: `USE_LLM=true` but no live API key or `MOCK_LLM=true`
- `live`: `USE_LLM=true`, `MOCK_LLM=false`, valid API key present

Decision trace includes:
- `decision_trace.llm_mode.llm_requested`
- `decision_trace.llm_mode.mock_llm`
- `decision_trace.llm_mode.has_api_key`
- `decision_trace.llm_mode.execution_mode`
- `decision_trace.llm_mode.model`
- `decision_trace.llm_mode.prompt_versions`

## Prompt A: Duplicate vs Legitimate Dose Transition Classifier

### Invocation Boundary
Prompt A is only used for ambiguous same-ingredient, different-strength candidates with overlap greater than 0.
It is skipped when any deterministic skip condition is true.

### Input Template
System:
```
You are a medication safety assistant used in an e-prescribing workflow.
Your task is to classify whether a medication history entry is:
1) true_duplicate
2) likely_transition
3) not_relevant
4) uncertain

Use only the facts provided. Do not infer facts not in evidence.
Return valid JSON only.
```

User fields:
- `pending_rx` JSON
- `history_entry` JSON
- `overlap_days`
- `same_ingredient`
- `same_strength`
- `same_route`
- `different_pharmacy`

### Expected Output JSON
```json
{
  "classification": "true_duplicate | likely_transition | not_relevant | uncertain",
  "confidence": "high | medium | low",
  "rationale": ["reason 1", "reason 2"],
  "recommended_severity": "info | review_required | block"
}
```

### Validation Rules
- `classification` must be one of the allowed enum values.
- `confidence` must be one of `high|medium|low`.
- `rationale` must be a non-empty list.
- `recommended_severity` must be one of `info|review_required|block`.
- Invalid output falls back to deterministic classifier.

## Prompt B: Structured Finding Generator

### Invocation Boundary
Prompt B is only used in `live` mode after classifier outputs are available.
If unavailable or invalid, deterministic finding text remains in place.

### Input Template
System:
```
You generate clinician-facing medication safety findings for pre-transmission review.
Return valid JSON only.
Do not hallucinate missing fields.
Keep the title and summary understandable in under 10 seconds.
```

User fields:
- `pending_rx` JSON
- `relevant_history_entries` JSON array
- `computed_summary` JSON
- `classifier_outputs` JSON array

### Expected Output JSON
```json
{
  "severity": "info | review_required | block",
  "title": "string",
  "summary": "string",
  "duplicate_type": "same_drug_same_strength | same_drug_diff_strength | same_class | other",
  "computed": {
    "proposed_start_date": "YYYY-MM-DD",
    "proposed_end_date": "YYYY-MM-DD",
    "max_overlap_days": 0
  },
  "evidence": [
    {
      "drug": "string",
      "fill_date": "YYYY-MM-DD",
      "days_supply": 0,
      "supply_end_date": "YYYY-MM-DD",
      "status": "string",
      "pharmacy": "string"
    }
  ],
  "limitations": ["string"],
  "recommended_actions": [
    {
      "action": "confirm_with_patient | adjust_start_date | change_pharmacy | edit_or_cancel | proceed",
      "label": "string"
    }
  ],
  "clinician_response": {
    "required": true,
    "reason_codes": ["dose_titration", "renewal", "replacement_lost", "pharmacy_switch", "other"]
  }
}
```

### Validation Rules
- Must include `title` and `summary` strings.
- Invalid output is ignored and deterministic finding text is used.

## Escalation Model (Implemented)

### Severity `info`
Use when:
- no active overlap
- low overlap only
- likely benign transition

### Severity `review_required`
Use when:
- same ingredient overlap is meaningful
- same-strength overlap exists
- multi-pharmacy pattern increases concern

### Severity `block`
Reserved for sparse high-confidence conditions in v1:
- multiple active overlapping same-strength duplicates
- classifier-recommended block with substantial overlap

## Deterministic Fallback Behavior
When `live` path is unavailable or invalid:
- Classifier falls back to deterministic contract-based rules.
- Finding generation falls back to deterministic finding generator.
- Decision trace still records mode and execution path.

## Comparison Checklist for External LLM Evaluation
For each model, compare:
1. JSON validity rate for Prompt A.
2. JSON validity rate for Prompt B.
3. Classification agreement with deterministic baseline.
4. Escalation alignment (`info`, `review_required`, `block`).
5. Hallucination rate (fields not in provided evidence).
6. Latency and error rate across ambiguous cases.
