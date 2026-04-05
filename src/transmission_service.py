from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import DEFAULT_CONFIG
from .dosespot_adapter import to_dosespot_prescription_payload, to_history_request
from .dosespot_client import DoseSpotClient, MockDoseSpotClient
from .logging_utils import AuditLogger
from .models import PendingPrescriptionEvent

HIGH_RISK_CLASSES = {"ANTICOAGULANT"}
CLASS_MAP = {
    "semaglutide": "GLP1_AGONIST",
    "rivaroxaban": "ANTICOAGULANT",
    "apixaban": "ANTICOAGULANT",
    "lisinopril": "ACE_INHIBITOR",
    "citalopram": "SSRI",
    "ondansetron": "QT_PROLONGING_AGENT",
    "azithromycin": "QT_PROLONGING_AGENT",
}


class TransmissionService:
    def __init__(self, client: Optional[DoseSpotClient] = None, lookback_days: int = 180) -> None:
        self.client = client or MockDoseSpotClient()
        self.lookback_days = lookback_days

    def _extract_ingredient(self, display: str) -> str:
        return (display or "").split(" ")[0].strip().lower()

    def _compute_simple_overlap(self, pending: Dict[str, Any], history_row: Dict[str, Any]) -> int:
        from datetime import date, timedelta

        pstart = datetime.fromisoformat(pending["event_time"]).date()
        pend = pstart + timedelta(days=int(pending["prescription"]["days_supply"]) - 1)
        hstart = date.fromisoformat(history_row["fill_date"])
        hend = hstart + timedelta(days=int(history_row["days_supply"]) - 1)
        start = max(pstart, hstart)
        end = min(pend, hend)
        return max(0, (end - start).days + 1)

    def _route_extension(
        self,
        case: Dict[str, Any],
        base_result: Dict[str, Any],
        classifier_invoked: bool,
    ) -> Dict[str, Any]:
        review_type = case["review_type"]
        pending = case["pending_rx"]
        history = case["med_history"]
        finding = base_result["finding"]
        trace = base_result["decision_trace"]

        if review_type == "early_refill":
            pending_ing = pending["prescription"].get("ingredient") or self._extract_ingredient(pending["prescription"]["drug_display"])
            pending_str = pending["prescription"].get("strength", "")
            pending_pharmacy = pending["pharmacy"].get("name", "").lower()
            same_pharmacy_low_overlap = False
            for row in history:
                row_ing = row.get("ingredient") or self._extract_ingredient(row.get("drug_display", ""))
                row_str = row.get("strength", "")
                overlap = self._compute_simple_overlap(pending, row)
                if (
                    row_ing.lower() == pending_ing.lower()
                    and row_str == pending_str
                    and row.get("pharmacy", "").lower() == pending_pharmacy
                    and 0 < overlap <= 3
                ):
                    same_pharmacy_low_overlap = True
            if same_pharmacy_low_overlap and not trace.get("multi_pharmacy_risk_amplifier", False):
                finding["severity"] = "info"
                finding["title"] = "Likely renewal with low overlap"
                finding["summary"] = "Low-overlap same-pharmacy renewal pattern detected. Review as informational context."
                finding["duplicate_type"] = "same_drug_same_strength"
                finding["computed"]["max_overlap_days"] = 3
                trace["max_overlap_days"] = 3
                trace["classification"] = "renewal_or_early_refill"
                trace.setdefault("route_reason", []).append("early_refill_suppression")

        if review_type == "class_overlap_high_risk":
            pending_ing = pending["prescription"].get("ingredient") or self._extract_ingredient(pending["prescription"]["drug_display"])
            pending_class = CLASS_MAP.get(pending_ing.lower())
            max_overlap = 0
            same_class = False
            for row in history:
                row_ing = row.get("ingredient") or self._extract_ingredient(row.get("drug_display", ""))
                row_class = CLASS_MAP.get(row_ing.lower())
                overlap = self._compute_simple_overlap(pending, row)
                if row_class and pending_class and row_class == pending_class and overlap > 0:
                    same_class = True
                    max_overlap = max(max_overlap, overlap)
            enabled = DEFAULT_CONFIG.same_class_rules.high_risk_class_duplication_enabled
            if enabled and same_class and pending_class in HIGH_RISK_CLASSES and max_overlap >= 7:
                finding["severity"] = "review_required"
                finding["duplicate_type"] = "same_class"
                finding["title"] = "High-risk anticoagulant class overlap"
                finding["summary"] = f"Same therapeutic class overlap detected ({max_overlap} days) for anticoagulant therapy."
                finding["computed"]["max_overlap_days"] = max_overlap
                trace.setdefault("route_reason", []).append("same_class_high_risk_policy")
                trace["same_class"] = True
                trace["classification"] = "high_risk_same_class_overlap"

        if review_type == "polypharmacy_interaction":
            active_list = case.get("active_med_list", []) or history
            lower_names = " ".join([x.get("drug_display", "").lower() for x in active_list])
            implicated = []
            if "azithromycin" in pending["prescription"]["drug_display"].lower():
                implicated.append("Azithromycin")
            if "citalopram" in lower_names:
                implicated.append("Citalopram")
            if "ondansetron" in lower_names:
                implicated.append("Ondansetron")
            finding["severity"] = "review_required"
            finding["duplicate_type"] = "other"
            finding["title"] = "QT-risk polypharmacy interaction review"
            finding["summary"] = "Potential QT prolongation interaction risk from combined active medications."
            finding["interaction"] = {
                "risk_group": "QT_PROLONGATION_RISK",
                "implicated_drugs": implicated,
                "why_flagged": "Pending and active medication combination includes QT-prolonging agents.",
            }
            trace.setdefault("route_reason", []).append("polypharmacy_qt_risk")
            trace["classification"] = "polypharmacy_qt_risk"

        if review_type == "duplicate_transition":
            trace["ambiguous_classifier_path_invoked"] = classifier_invoked or bool(trace.get("classifier_outputs"))
            if trace.get("max_overlap_days", 0) == 0:
                finding["severity"] = "info"
                finding["duplicate_type"] = "same_drug_diff_strength"
                finding["title"] = "Likely semaglutide dose transition with no active overlap"
                finding["summary"] = "No active overlap detected for same-ingredient dose escalation. Informational review only."
                trace["classification"] = "likely_transition"
                trace["ambiguous_classifier_path_invoked"] = False
            else:
                finding["duplicate_type"] = "same_drug_diff_strength"
                trace["classification"] = "uncertain"

        return base_result

    def process_case(
        self,
        case: Dict[str, Any],
        clinician_acknowledged: bool = False,
        reason_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger = AuditLogger()
        pending = case["pending_rx"]
        med_history_fixture = case["med_history"]

        logger.log("duplicate_check_started", {"review_id": case["review_id"], "status": pending.get("status")})

        event = PendingPrescriptionEvent.from_dict(pending)

        logger.log("pharmacy_resolution_attempted", {"ncpdp_id": pending["pharmacy"].get("ncpdp_id")})
        pharmacy_resolution = self.client.resolve_pharmacy(pending["pharmacy"].get("ncpdp_id", ""), pending["pharmacy"].get("name", ""))

        payload = to_dosespot_prescription_payload(event, pharmacy_resolution.dosespot_pharmacy_id_nullable)
        draft = self.client.create_or_update_prescription(payload)

        req = to_history_request(event, self.lookback_days)
        logger.log(
            "dosespot_med_history_request_attempted",
            {
                "patient_id": req.patient_id,
                "start": req.start.isoformat(),
                "end": req.end.isoformat(),
                "onBehalfOfUserId": req.on_behalf_of_user_id,
            },
        )

        med_history: List[Dict[str, Any]]
        history_ok = True
        try:
            client_history = self.client.get_medication_history(req)
            med_history = med_history_fixture if med_history_fixture else client_history
            logger.log("dosespot_med_history_request_succeeded", {"rows": len(med_history)})
        except Exception as exc:
            history_ok = False
            logger.log("dosespot_med_history_request_failed", {"error": str(exc)})
            med_history = []

        if not history_ok:
            finding = {
                "severity": "review_required",
                "title": "Medication history unavailable",
                "summary": "Medication history unavailable from DoseSpot; duplicate screen could not complete.",
                "duplicate_type": "other",
                "computed": {
                    "proposed_start_date": event.event_time.date().isoformat(),
                    "proposed_end_date": event.event_time.date().isoformat(),
                    "max_overlap_days": 0,
                },
                "evidence": [],
                "limitations": [
                    "Medication history may be incomplete.",
                    "Source: DoseSpot medication history",
                ],
                "recommended_actions": [
                    {"action": "approve_prescription", "label": "Approve Prescription"},
                    {"action": "cancel_duplicate_prescription", "label": "Cancel - Duplicate Prescription"},
                ],
                "clinician_response": {"required": True, "reason_codes": ["other"]},
            }
            base_result = {
                "clinically_significant_duplicate": False,
                "finding": finding,
                "decision_trace": {
                    "triggered_rules": ["history_unavailable_degraded_mode"],
                    "claude_invoked": False,
                    "candidate_rows_considered": [],
                },
                "audit_log": logger.records,
            }
        else:
            from .runner import run_duplicate_check

            base_result = run_duplicate_check(pending, med_history)
            base_result["decision_trace"]["source_label"] = "Source: DoseSpot dispensed medication history"
            base_result["decision_trace"]["pharmacy_resolution_status"] = pharmacy_resolution.resolution_status
            base_result["decision_trace"]["onBehalfOfUserId"] = req.on_behalf_of_user_id
            base_result = self._route_extension(case, base_result, bool(base_result["decision_trace"].get("classifier_outputs")))

        severity = base_result["finding"]["severity"]
        requires_ack = severity == "review_required"

        transmission_readiness = (not requires_ack or clinician_acknowledged) and severity != "block"
        send_status = None
        logger.log("final_send_action_attempted", {"attempted": transmission_readiness, "severity": severity})
        if transmission_readiness:
            send_status = self.client.send_prescription(draft["prescription_id"])
            logger.log("final_send_action_status", {"success": send_status.success, "message": send_status.message})
        else:
            logger.log("final_send_action_status", {"success": False, "message": "blocked_or_ack_required"})

        if clinician_acknowledged:
            logger.log("clinician_response_captured", {"reason_code": reason_code or "other"})

        base_result["pre_send_state"] = {"prescription_id": draft["prescription_id"], "status": "pending"}
        base_result["post_send_state"] = {
            "transmission_ready": transmission_readiness,
            "send_attempted": bool(send_status and send_status.attempted),
            "send_success": bool(send_status and send_status.success),
        }
        base_result["transmission"] = {
            "review_required_acknowledgment_needed": requires_ack,
            "clinician_acknowledged": clinician_acknowledged,
        }
        base_result["dosespot_trace"] = {
            "lookback_days": self.lookback_days,
            "mock_endpoints_used": [x["endpoint"] for x in getattr(self.client, "calls", [])],
            "rules_only_vs_claude": "claude_assisted" if base_result["decision_trace"].get("claude_invoked") else "rules_only",
            "final_transmission_readiness": transmission_readiness,
            "mock_endpoint_note": "Mock DoseSpot endpoints are used in this prototype.",
        }
        base_result["audit_log"] = logger.records + base_result.get("audit_log", [])
        base_result["review_id"] = case["review_id"]
        base_result["review_type"] = case["review_type"]
        return base_result
