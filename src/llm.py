from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List

from .models import ClassifierOutput, DuplicateCandidate, PendingPrescriptionEvent
from .prompts import (
    CLASSIFIER_SYSTEM_PROMPT,
    CLASSIFIER_USER_PROMPT_TEMPLATE,
    FINDING_SYSTEM_PROMPT,
    FINDING_USER_PROMPT_TEMPLATE,
)


class ClaudeAdapter:
    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        self.use_llm = os.getenv("USE_LLM", "false").lower() == "true"
        self.mock_llm = os.getenv("MOCK_LLM", "true").lower() == "true"

    def should_call_live(self) -> bool:
        return self.use_llm and (not self.mock_llm) and bool(self.api_key)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        content = text.strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.replace("json", "", 1).strip()
        return json.loads(content)

    def _call_claude_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "max_tokens": 700,
            "temperature": 0,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        req = urllib.request.Request(
            url="https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
        parts = body.get("content", [])
        text = ""
        for part in parts:
            if part.get("type") == "text":
                text += part.get("text", "")
        return self._extract_json(text)

    def classify_ambiguous_candidate(
        self,
        event: PendingPrescriptionEvent,
        candidate: DuplicateCandidate,
    ) -> ClassifierOutput:
        if not candidate.llm_needed:
            return ClassifierOutput(
                classification="not_relevant",
                rationale=["Candidate is not ambiguous; LLM not required."],
                confidence="high",
                recommended_severity="info",
                candidate_drug=candidate.drug_display,
                llm_invoked=False,
            )

        if not self.should_call_live():
            return self._mock_classify(candidate)

        prompt = CLASSIFIER_USER_PROMPT_TEMPLATE.format(
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
            PENDING_START_DATE=event.event_time.date().isoformat(),
            PENDING_DAYS_SUPPLY=event.prescription.days_supply,
            HISTORY_SUPPLY_END_DATE=candidate.supply_end_date.isoformat(),
            OVERLAP_DAYS=candidate.overlap_days,
            TRUE_FALSE_SAME_INGREDIENT=str(candidate.same_ingredient).lower(),
            TRUE_FALSE_SAME_ROUTE=str(candidate.same_route).lower(),
            TRUE_FALSE_SAME_STRENGTH=str(candidate.same_strength).lower(),
            TRUE_FALSE_DIFF_PHARMACY=str(candidate.different_pharmacy).lower(),
        )

        try:
            parsed = self._call_claude_json(CLASSIFIER_SYSTEM_PROMPT, prompt)
            return ClassifierOutput(
                classification=str(parsed.get("classification", "uncertain")),
                rationale=list(parsed.get("rationale", ["No rationale returned."])),
                confidence=str(parsed.get("confidence", "low")),
                recommended_severity=str(parsed.get("recommended_severity", "review_required")),
                candidate_drug=candidate.drug_display,
                llm_invoked=True,
            )
        except (urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError):
            fallback = self._mock_classify(candidate)
            fallback.rationale.append("Claude unavailable; deterministic mock mode used.")
            return fallback

    def _mock_classify(self, candidate: DuplicateCandidate) -> ClassifierOutput:
        if candidate.overlap_days <= 3:
            return ClassifierOutput(
                classification="likely_transition",
                rationale=[
                    "Different strengths with low overlap can represent titration.",
                    "No same-strength overlap evidence in this candidate.",
                ],
                confidence="medium",
                recommended_severity="info",
                candidate_drug=candidate.drug_display,
                llm_invoked=False,
            )
        return ClassifierOutput(
            classification="uncertain",
            rationale=[
                "Different strengths overlap for more than a short bridge period.",
                "May represent transition or duplicate supply.",
            ],
            confidence="medium",
            recommended_severity="review_required",
            candidate_drug=candidate.drug_display,
            llm_invoked=False,
        )

    def generate_finding_text(
        self,
        pending_json: Dict[str, Any],
        relevant_history: List[Dict[str, Any]],
        overlap_summary: Dict[str, Any],
        classifier_outputs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not self.should_call_live():
            return {}

        prompt = FINDING_USER_PROMPT_TEMPLATE.format(
            PENDING_RX_JSON=json.dumps(pending_json, indent=2),
            RELEVANT_HISTORY_JSON_ARRAY=json.dumps(relevant_history, indent=2),
            OVERLAP_SUMMARY_JSON=json.dumps(overlap_summary, indent=2),
            CLASSIFIER_OUTPUTS_JSON_ARRAY=json.dumps(classifier_outputs, indent=2),
        )
        try:
            return self._call_claude_json(FINDING_SYSTEM_PROMPT, prompt)
        except (urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError):
            return {}
