from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAIError

from services.openai_client import get_openai_client, get_openai_model
from .llm_schema import validate_classifier_output, validate_finding_llm_payload
from .models import ClassifierOutput, DuplicateCandidate, PendingPrescriptionEvent
from .prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    CLASSIFICATION_USER_PROMPT_TEMPLATE,
    FINDING_WORDING_SYSTEM_PROMPT,
    FINDING_WORDING_USER_PROMPT_TEMPLATE,
    PROMPT_VERSIONS,
)


class ClaudeAdapter:
    def __init__(self) -> None:
        import os

        self.model = get_openai_model()
        self.use_llm = os.getenv("USE_LLM", "false").lower() == "true"
        self.client = get_openai_client()
        self.has_api_key = self.client is not None

    def should_call_live(self) -> bool:
        return self.use_llm and self.has_api_key

    def execution_mode(self) -> str:
        if not self.use_llm:
            return "disabled"
        if self.should_call_live():
            return "live"
        return "deterministic_fallback"

    def mode_state(self) -> Dict[str, Any]:
        return {
            "llm_requested": self.use_llm,
            "mock_llm": not self.has_api_key,
            "has_api_key": self.has_api_key,
            "execution_mode": self.execution_mode(),
            "model": self.model,
            "prompt_versions": PROMPT_VERSIONS,
        }

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        content = text.strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.replace("json", "", 1).strip()
        return json.loads(content)

    def _call_claude_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if self.client is None:
            raise ValueError("OPENAI_API_KEY missing")
        response = self.client.responses.create(
            model=self.model,
            temperature=0,
            max_output_tokens=700,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = (getattr(response, "output_text", "") or "").strip()
        if not text:
            raise ValueError("LLM response output text was empty")
        return self._extract_json(text)

    def explain_route_for_candidate(self, candidate: DuplicateCandidate) -> Dict[str, Any]:
        if not candidate.llm_needed:
            return {
                "decision": "skip",
                "reason": "deterministic_rule_path",
                "prompt_version": PROMPT_VERSIONS["classification"],
            }
        if candidate.overlap_days <= 0:
            return {
                "decision": "skip",
                "reason": "zero_overlap",
                "prompt_version": PROMPT_VERSIONS["classification"],
            }
        if candidate.same_strength:
            return {
                "decision": "skip",
                "reason": "exact_duplicate_rules_first",
                "prompt_version": PROMPT_VERSIONS["classification"],
            }
        return {
            "decision": "invoke",
            "reason": "ambiguous_same_ingredient_diff_strength",
            "prompt_version": PROMPT_VERSIONS["classification"],
        }

    def _deterministic_classifier(self, candidate: DuplicateCandidate) -> ClassifierOutput:
        if (not candidate.same_ingredient) or (not candidate.same_route):
            return ClassifierOutput(
                classification="not_relevant",
                rationale=["same_ingredient or same_route is false."],
                confidence="high",
                recommended_severity="info",
                candidate_drug=candidate.drug_display,
                llm_invoked=False,
            )
        if candidate.overlap_days <= 0:
            return ClassifierOutput(
                classification="not_relevant",
                rationale=["overlap_days <= 0."],
                confidence="high",
                recommended_severity="info",
                candidate_drug=candidate.drug_display,
                llm_invoked=False,
            )
        if candidate.same_strength and candidate.overlap_days >= 4:
            return ClassifierOutput(
                classification="true_duplicate",
                rationale=["same_strength is true and overlap_days >= 4."],
                confidence="high",
                recommended_severity="review_required",
                candidate_drug=candidate.drug_display,
                llm_invoked=False,
            )
        if (not candidate.same_strength) and candidate.overlap_days <= 3:
            return ClassifierOutput(
                classification="likely_transition",
                rationale=["different strength with low overlap suggests titration."],
                confidence="medium",
                recommended_severity="info",
                candidate_drug=candidate.drug_display,
                llm_invoked=False,
            )
        return ClassifierOutput(
            classification="uncertain",
            rationale=["evidence is mixed or overlap is clinically meaningful with differing strength."],
            confidence="medium",
            recommended_severity="review_required",
            candidate_drug=candidate.drug_display,
            llm_invoked=False,
        )

    def classify_ambiguous_candidate(
        self,
        event: PendingPrescriptionEvent,
        candidate: DuplicateCandidate,
    ) -> ClassifierOutput:
        route = self.explain_route_for_candidate(candidate)
        if route["decision"] == "skip":
            return ClassifierOutput(
                classification="not_relevant",
                rationale=[f"LLM skipped: {route['reason']}"],
                confidence="high",
                recommended_severity="info",
                candidate_drug=candidate.drug_display,
                llm_invoked=False,
            )

        if not self.use_llm:
            out = self._deterministic_classifier(candidate)
            out.rationale.append("LLM mode disabled; deterministic classifier path used.")
            return out

        if not self.should_call_live():
            out = self._deterministic_classifier(candidate)
            out.rationale.append("LLM mode enabled but API key unavailable; deterministic fallback path used.")
            return out

        prompt = CLASSIFICATION_USER_PROMPT_TEMPLATE.format(
            PENDING_RX_JSON=json.dumps(event.to_serializable(), indent=2),
            HISTORY_ENTRY_JSON=json.dumps(
                {
                    "drug_display": candidate.drug_display,
                    "ingredient": candidate.ingredient,
                    "strength": candidate.strength,
                    "route": candidate.route,
                    "fill_date": candidate.fill_date.isoformat(),
                    "days_supply": candidate.days_supply,
                    "status": candidate.status,
                    "pharmacy": candidate.pharmacy,
                },
                indent=2,
            ),
            OVERLAP_DAYS=candidate.overlap_days,
            TRUE_FALSE_SAME_INGREDIENT=str(candidate.same_ingredient).lower(),
            TRUE_FALSE_SAME_ROUTE=str(candidate.same_route).lower(),
            TRUE_FALSE_SAME_STRENGTH=str(candidate.same_strength).lower(),
            TRUE_FALSE_DIFF_PHARMACY=str(candidate.different_pharmacy).lower(),
        )

        try:
            parsed = self._call_claude_json(CLASSIFICATION_SYSTEM_PROMPT, prompt)
            ok, _ = validate_classifier_output(parsed)
            if not ok:
                raise ValueError("Invalid classifier JSON schema")
            return ClassifierOutput(
                classification=str(parsed.get("classification", "uncertain")),
                rationale=list(parsed.get("rationale", ["No rationale returned."])),
                confidence=str(parsed.get("confidence", "low")),
                recommended_severity=str(parsed.get("recommended_severity", "review_required")),
                candidate_drug=candidate.drug_display,
                llm_invoked=True,
            )
        except (OpenAIError, ValueError, KeyError, json.JSONDecodeError):
            out = self._deterministic_classifier(candidate)
            out.rationale.append("Live LLM failed schema or request; deterministic fallback used.")
            return out

    def generate_finding_text(
        self,
        pending_json: Dict[str, Any],
        relevant_history: List[Dict[str, Any]],
        overlap_summary: Dict[str, Any],
        classifier_outputs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not self.should_call_live():
            return {}

        prompt = FINDING_WORDING_USER_PROMPT_TEMPLATE.format(
            PENDING_RX_JSON=json.dumps(pending_json, indent=2),
            RELEVANT_HISTORY_JSON_ARRAY=json.dumps(relevant_history, indent=2),
            OVERLAP_SUMMARY_JSON=json.dumps(overlap_summary, indent=2),
            CLASSIFIER_OUTPUTS_JSON_ARRAY=json.dumps(classifier_outputs, indent=2),
        )
        try:
            payload = self._call_claude_json(FINDING_WORDING_SYSTEM_PROMPT, prompt)
            ok, _ = validate_finding_llm_payload(payload)
            if not ok:
                return {}
            return payload
        except (OpenAIError, ValueError, KeyError, json.JSONDecodeError):
            return {}
