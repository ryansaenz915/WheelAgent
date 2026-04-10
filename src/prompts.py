from __future__ import annotations

PROMPT_VERSIONS = {
    "classification": "prompt_a_duplicate_transition_classifier.v1",
    "finding_wording": "prompt_b_structured_finding_generator.v1",
    "combined_classification_finding": "prompt_ab_combined_classifier_finding.v1",
}

CLASSIFICATION_SYSTEM_PROMPT = """You are a medication safety assistant used in an e-prescribing workflow.
Your task is to classify whether a medication history entry is:
1) true_duplicate
2) likely_transition
3) not_relevant
4) uncertain

Use only the facts provided. Do not infer facts not in evidence.
Return valid JSON only."""


CLASSIFICATION_USER_PROMPT_TEMPLATE = """Pending prescription:
{PENDING_RX_JSON}

Medication history entry:
{HISTORY_ENTRY_JSON}

Computed facts:
- overlap_days: {OVERLAP_DAYS}
- same_ingredient: {TRUE_FALSE_SAME_INGREDIENT}
- same_strength: {TRUE_FALSE_SAME_STRENGTH}
- same_route: {TRUE_FALSE_SAME_ROUTE}
- different_pharmacy: {TRUE_FALSE_DIFF_PHARMACY}
- pending_drug_class: {PENDING_DRUG_CLASS}
- history_drug_class: {HISTORY_DRUG_CLASS}

Guidance:
- If same_ingredient is false or same_route is false -> not_relevant
- If overlap_days <= 0 -> not_relevant
- If same_strength is true and overlap_days >= 4 -> true_duplicate
- If strength differs and the pattern suggests dose escalation or titration -> likely_transition
- If evidence is mixed or incomplete -> uncertain

Return this JSON:
{{
 "classification": "true_duplicate | likely_transition | not_relevant | uncertain",
 "confidence": "high | medium | low",
 "rationale": ["reason 1", "reason 2"],
 "recommended_severity": "review_required | no_review_required",
 "drug_class": "string"
}}"""


FINDING_WORDING_SYSTEM_PROMPT = """You generate clinician-facing medication safety findings for pre-transmission review.
Return valid JSON only.
Do not hallucinate missing fields.
Keep the title and summary understandable in under 10 seconds."""


FINDING_WORDING_USER_PROMPT_TEMPLATE = """Pending prescription:
{PENDING_RX_JSON}

Relevant medication history entries:
{RELEVANT_HISTORY_JSON_ARRAY}

Computed summary:
{OVERLAP_SUMMARY_JSON}

Classifier outputs:
{CLASSIFIER_OUTPUTS_JSON_ARRAY}

Return this JSON:
{{
 "severity": "review_required | no_review_required",
 "title": "string",
 "summary": "string",
 "drug_class": "string",
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
     "action": "approve_prescription | adjust_start_date | cancel_duplicate_prescription | proceed_next_case",
     "label": "string"
   }}
 ],
 "clinician_response": {{
   "required": true,
   "reason_codes": ["dose_titration", "renewal", "replacement_lost", "pharmacy_switch", "other"]
 }}
}}"""


COMBINED_CLASSIFICATION_FINDING_SYSTEM_PROMPT = """You are a medication safety assistant used in a pre-transmission e-prescribing workflow.
You must return both:
1) a strict classifier output for the ambiguous candidate
2) a clinician-facing structured finding

Use only provided evidence.
Do not infer unknown facts.
Return valid JSON only."""


COMBINED_CLASSIFICATION_FINDING_USER_PROMPT_TEMPLATE = """Pending prescription:
{PENDING_RX_JSON}

Candidate medication history entry:
{HISTORY_ENTRY_JSON}

Computed facts:
- overlap_days: {OVERLAP_DAYS}
- same_ingredient: {TRUE_FALSE_SAME_INGREDIENT}
- same_strength: {TRUE_FALSE_SAME_STRENGTH}
- same_route: {TRUE_FALSE_SAME_ROUTE}
- different_pharmacy: {TRUE_FALSE_DIFF_PHARMACY}

Computed summary:
{OVERLAP_SUMMARY_JSON}

Guidance:
- If same_ingredient is false or same_route is false -> not_relevant
- If overlap_days <= 0 -> not_relevant
- If same_strength is true and overlap_days >= 4 -> true_duplicate
- If strength differs and pattern suggests titration -> likely_transition
- If evidence is mixed or incomplete -> uncertain

Return this JSON:
{{
  "classifier": {{
    "classification": "true_duplicate | likely_transition | not_relevant | uncertain",
    "confidence": "high | medium | low",
    "rationale": ["reason 1", "reason 2"],
    "recommended_severity": "review_required | no_review_required",
    "drug_class": "string"
  }},
  "finding": {{
    "severity": "review_required | no_review_required",
    "title": "string",
    "summary": "string",
    "drug_class": "string",
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
        "pharmacy": "string",
        "drug_class": "string"
      }}
    ],
    "limitations": ["string"],
    "recommended_actions": [
      {{
        "action": "approve_prescription | adjust_start_date | cancel_duplicate_prescription | proceed_next_case",
        "label": "string"
      }}
    ],
    "clinician_response": {{
      "required": true,
      "reason_codes": ["dose_titration", "renewal", "replacement_lost", "pharmacy_switch", "other"]
    }}
  }}
}}"""
