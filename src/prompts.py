from __future__ import annotations

CLASSIFIER_SYSTEM_PROMPT = """You are a medication safety classification assistant used in an e-prescribing workflow.
Your job is to classify whether a medication history entry represents:
(A) a clinically meaningful duplicate of the pending prescription,
(B) a legitimate transition (dose titration or renewal),
(C) not relevant, or
(D) uncertain due to insufficient information.

Use only the data provided.
Do not infer facts not in evidence.
Return valid JSON only."""


CLASSIFIER_USER_PROMPT_TEMPLATE = """Pending Rx:
{PENDING_RX_JSON}

Candidate history entry:
{HISTORY_ENTRY_JSON}

Computed fields:
- pending_start_date: {PENDING_START_DATE}
- pending_days_supply: {PENDING_DAYS_SUPPLY}
- history_supply_end_date: {HISTORY_SUPPLY_END_DATE}
- overlap_days: {OVERLAP_DAYS}
- same_ingredient: {TRUE_FALSE_SAME_INGREDIENT}
- same_route: {TRUE_FALSE_SAME_ROUTE}
- same_strength: {TRUE_FALSE_SAME_STRENGTH}
- different_pharmacy: {TRUE_FALSE_DIFF_PHARMACY}

Clinical hints:
- For semaglutide/Ozempic, common escalation may include 0.25 mg weekly, then 0.5 mg weekly, then 1 mg weekly after at least 4 weeks at the prior dose.

Return JSON:
{{
  "classification": "true_duplicate | likely_transition | not_relevant | uncertain",
  "rationale": ["reason 1", "reason 2"],
  "confidence": "high | medium | low",
  "recommended_severity": "info | review_required | block"
}}"""


FINDING_SYSTEM_PROMPT = """You generate clinician-facing medication safety findings for pre-transmission review.
Your output must be concise, structured, evidence-based, and valid JSON only.
Do not hallucinate missing data.
Do not include PHI beyond what is provided."""


FINDING_USER_PROMPT_TEMPLATE = """Pending Rx event:
{PENDING_RX_JSON}

Relevant medication history entries:
{RELEVANT_HISTORY_JSON_ARRAY}

Computed overlap summary:
{OVERLAP_SUMMARY_JSON}

Classifier outputs:
{CLASSIFIER_OUTPUTS_JSON_ARRAY}

Return JSON:
{{
  "severity": "info | review_required | block",
  "title": "string",
  "summary": "string",
  "duplicate_type": "same_drug_same_strength | same_drug_diff_strength | same_class | other",
  "computed": {{
    "proposed_start_date": "YYYY-MM-DD",
    "proposed_end_date": "YYYY-MM-DD",
    "max_overlap_days": number
  }},
  "evidence": [
    {{
      "drug": "string",
      "fill_date": "YYYY-MM-DD",
      "days_supply": number,
      "supply_end_date": "YYYY-MM-DD",
      "status": "string",
      "pharmacy": "string"
    }}
  ],
  "limitations": ["string"],
  "recommended_actions": [
    {{
      "action": "confirm_with_patient | adjust_start_date | change_pharmacy | edit_or_cancel | proceed",
      "label": "string"
    }}
  ],
  "clinician_response": {{
    "required": true,
    "reason_codes": ["dose_titration", "renewal", "replacement_lost", "pharmacy_switch", "other"]
  }}
}}"""
