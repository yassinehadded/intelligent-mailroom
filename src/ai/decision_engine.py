from __future__ import annotations

from src.ai.models import DecisionResult, LLMAnalysisResult, RuleAnalysisResult
from src.utils import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """
    Decision layer comparing Rule-Based engine results and Qwen 2.5 7B LLM results
    to make final routing decisions based on 5 configurable rules.
    """

    LOW_CONFIDENCE_THRESHOLD = 0.60
    HIGH_LLM_CONFIDENCE_THRESHOLD = 0.90

    def evaluate(
        self,
        rule_result: RuleAnalysisResult,
        llm_result: LLMAnalysisResult,
    ) -> DecisionResult:
        rule_dept = rule_result.department.upper()
        llm_dept = llm_result.department.upper() if llm_result.department else "COU"

        depts_agree = (rule_dept == llm_dept)
        doctypes_agree = (
            rule_result.document_type.lower() == llm_result.document_type.lower()
            if (rule_result.document_type and llm_result.document_type)
            else depts_agree
        )

        priority = llm_result.priority if llm_result.priority else "normal"
        confidential = llm_result.confidential

        # --- CASE 4: Strong deterministic rule evidence vs LLM disagreement ---
        if rule_result.has_deterministic_evidence and not depts_agree:
            evidence_str = ", ".join(rule_result.evidence_details) or "deterministic patterns"
            return DecisionResult(
                department=rule_dept,
                document_type=rule_result.document_type or "general_mail",
                priority=priority,
                confidential=confidential,
                confidence=rule_result.confidence,
                action="MANUAL_REVIEW",
                reason=(
                    f"Case 4 (Deterministic Rule Override): Rule engine found strong deterministic evidence "
                    f"({evidence_str}) pointing to {rule_dept}, but LLM proposed {llm_dept}. "
                    f"Flagged for manual review."
                ),
                case_applied="CASE_4_DETERMINISTIC_RULE_OVERRIDE",
            )

        # --- CASE 5: Both confidences are low (< 0.60) ---
        if rule_result.confidence < self.LOW_CONFIDENCE_THRESHOLD and llm_result.confidence < self.LOW_CONFIDENCE_THRESHOLD:
            pref_dept = llm_dept if llm_result.confidence >= rule_result.confidence else rule_dept
            return DecisionResult(
                department=pref_dept,
                document_type=llm_result.document_type or rule_result.document_type or "general_mail",
                priority=priority,
                confidential=confidential,
                confidence=max(rule_result.confidence, llm_result.confidence),
                action="MANUAL_REVIEW",
                reason=(
                    f"Case 5 (Low Confidence): Both rule confidence ({rule_result.confidence:.2f}) "
                    f"and LLM confidence ({llm_result.confidence:.2f}) are below threshold ({self.LOW_CONFIDENCE_THRESHOLD:.2f}). "
                    f"Sent to Manual Review queue."
                ),
                case_applied="CASE_5_LOW_CONFIDENCE",
            )

        # --- CASE 1: Both classifiers agree on department and document type ---
        if depts_agree and doctypes_agree:
            boosted_conf = min(1.0, max(rule_result.confidence, llm_result.confidence) + 0.10)
            return DecisionResult(
                department=rule_dept,
                document_type=rule_result.document_type or llm_result.document_type or "general_mail",
                priority=priority,
                confidential=confidential,
                confidence=boosted_conf,
                action="AUTO_ACCEPT",
                reason=(
                    f"Case 1 (Agreement): Both Rule Engine and LLM agree on department '{rule_dept}' "
                    f"and document type '{rule_result.document_type}'. Confidence boosted to {boosted_conf:.2f}."
                ),
                case_applied="CASE_1_AGREEMENT",
            )

        # --- CASE 3: High LLM confidence (>= 0.90) and weak rule evidence ---
        if (
            llm_result.confidence >= self.HIGH_LLM_CONFIDENCE_THRESHOLD
            and not rule_result.has_deterministic_evidence
            and rule_result.confidence < 0.70
        ):
            return DecisionResult(
                department=llm_dept,
                document_type=llm_result.document_type or "general_mail",
                priority=priority,
                confidential=confidential,
                confidence=llm_result.confidence,
                action="AUTO_ACCEPT",
                reason=(
                    f"Case 3 (High LLM Confidence): Qwen LLM has high confidence ({llm_result.confidence:.2f}) "
                    f"for department '{llm_dept}' while rule engine evidence was weak ({rule_result.confidence:.2f}). "
                    f"Preferred LLM output."
                ),
                case_applied="CASE_3_HIGH_CONF_LLM",
            )

        # --- CASE 2: Departments differ (General comparison) ---
        kw_str = ", ".join(rule_result.matched_keywords) if rule_result.matched_keywords else "none"
        if llm_result.confidence > rule_result.confidence:
            chosen_dept = llm_dept
            chosen_conf = llm_result.confidence
            chosen_doctype = llm_result.document_type or rule_result.document_type or "general_mail"
        else:
            chosen_dept = rule_dept
            chosen_conf = rule_result.confidence
            chosen_doctype = rule_result.document_type or "general_mail"

        action = "AUTO_ACCEPT" if chosen_conf >= 0.75 else "MANUAL_REVIEW"
        return DecisionResult(
            department=chosen_dept,
            document_type=chosen_doctype,
            priority=priority,
            confidential=confidential,
            confidence=chosen_conf,
            action=action,
            reason=(
                f"Case 2 (Department Mismatch): Rule engine suggested '{rule_dept}' (conf: {rule_result.confidence:.2f}, "
                f"keywords: [{kw_str}]), whereas LLM suggested '{llm_dept}' (conf: {llm_result.confidence:.2f}, "
                f"reason: '{llm_result.reason}'). Selected '{chosen_dept}' based on higher confidence score."
            ),
            case_applied="CASE_2_DEPT_MISMATCH",
        )
