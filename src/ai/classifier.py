from __future__ import annotations

import json
import re
from typing import Protocol

import requests

from src.ai.decision_engine import DecisionEngine
from src.ai.llm_service import OllamaLLMService
from src.ai.models import ClassificationResult, DecisionResult, LLMAnalysisResult, RuleAnalysisResult
from src.ai.rule_engine import EnhancedRuleClassifier, RULE_DEFINITIONS
from src.config import Settings, get_settings
from src.maarch.reference import ReferenceDataService
from src.utils import get_logger

logger = get_logger(__name__)


class DocumentClassifier(Protocol):
    def classify(
        self,
        *,
        subject: str,
        body_text: str,
        sender: str | None = None,
    ) -> ClassificationResult: ...


class RuleBasedClassifier:
    """Wrapper around EnhancedRuleClassifier maintaining backward compatibility."""

    def __init__(self, reference_service: ReferenceDataService | None = None):
        self.reference_service = reference_service
        self.rule_engine = EnhancedRuleClassifier(reference_service)

    def classify(
        self,
        *,
        subject: str,
        body_text: str,
        sender: str | None = None,
    ) -> ClassificationResult:
        rule_res = self.rule_engine.analyze(subject=subject, body_text=body_text, sender=sender)
        destination_serial_id = None
        if self.reference_service is not None:
            destination_serial_id = self.reference_service.get_entity_serial_id(rule_res.department)

        doctype_id, doctype_label = self._resolve_doctype(rule_res.department, rule_res.document_type)

        return ClassificationResult(
            category=rule_res.document_type or "general",
            confidence=rule_res.confidence,
            subject=_build_subject(subject, rule_res.document_type),
            destination_entity_id=rule_res.department,
            destination_serial_id=destination_serial_id,
            doctype_id=doctype_id,
            doctype_label=doctype_label,
            method="rules",
            reasoning=f"Matched department '{rule_res.department}' via enhanced rule engine",
            action="AUTO_ACCEPT" if rule_res.confidence >= 0.60 else "MANUAL_REVIEW",
            rule_result=rule_res,
        )

    def _resolve_doctype(self, department: str, document_type: str) -> tuple[int | None, str | None]:
        rule = next((r for r in RULE_DEFINITIONS if r.department == department), RULE_DEFINITIONS[-1])
        if self.reference_service is None:
            return rule.default_doctype_id, rule.doctype_label

        doctypes = self.reference_service.get_flat_doctypes()
        for dt in doctypes:
            if dt.get("type_id") == rule.default_doctype_id:
                return dt["type_id"], dt["label"]

        return rule.default_doctype_id, rule.doctype_label


class HybridClassifier:
    """
    Hybrid Classifier combining:
    1. Enhanced Rule Engine (FR, EN, AR + Regex + Deterministic Evidence)
    2. Local Qwen 2.5 7B via Ollama
    3. Decision Layer (5 Cases)
    """

    def __init__(
        self,
        settings: Settings | None = None,
        reference_service: ReferenceDataService | None = None,
        ollama_service: OllamaLLMService | None = None,
        rule_engine: EnhancedRuleClassifier | None = None,
        decision_engine: DecisionEngine | None = None,
    ):
        self.settings = settings or get_settings()
        self.reference_service = reference_service
        self.ollama_service = ollama_service or OllamaLLMService(self.settings)
        self.rule_engine = rule_engine or EnhancedRuleClassifier(reference_service)
        self.decision_engine = decision_engine or DecisionEngine()

    def classify(
        self,
        *,
        subject: str,
        body_text: str,
        sender: str | None = None,
    ) -> ClassificationResult:
        # Step 1: Rule Engine Analysis
        rule_res = self.rule_engine.analyze(subject=subject, body_text=body_text, sender=sender)

        # Step 2: Qwen 2.5 7B LLM Analysis (Ollama Local)
        llm_res = self.ollama_service.analyze(subject=subject, body_text=body_text, sender=sender)

        # Step 3: Decision Engine Layer
        decision = self.decision_engine.evaluate(rule_res, llm_res)

        # Step 4: Map to routing IDs
        destination_serial_id = None
        if self.reference_service is not None:
            destination_serial_id = self.reference_service.get_entity_serial_id(decision.department)

        rule_def = next((r for r in RULE_DEFINITIONS if r.department == decision.department), RULE_DEFINITIONS[-1])
        doctype_id = rule_def.default_doctype_id
        doctype_label = rule_def.doctype_label

        if self.reference_service is not None and doctype_id is not None:
            doctypes = self.reference_service.get_flat_doctypes()
            for dt in doctypes:
                if dt.get("type_id") == doctype_id:
                    doctype_label = dt.get("label", doctype_label)
                    break

        return ClassificationResult(
            category=decision.document_type,
            confidence=decision.confidence,
            subject=_build_subject(subject, decision.document_type),
            destination_entity_id=decision.department,
            destination_serial_id=destination_serial_id,
            doctype_id=doctype_id,
            doctype_label=doctype_label,
            method="hybrid_qwen_rules",
            reasoning=decision.reason,
            action=decision.action,
            rule_result=rule_res,
            llm_result=llm_res,
            decision=decision,
        )


class OpenAiClassifier:
    """LLM-based classifier using an OpenAI-compatible chat API."""

    def __init__(
        self,
        settings: Settings | None = None,
        reference_service: ReferenceDataService | None = None,
    ):
        self.settings = settings or get_settings()
        self.reference_service = reference_service
        self.fallback = RuleBasedClassifier(reference_service)

    def classify(
        self,
        *,
        subject: str,
        body_text: str,
        sender: str | None = None,
    ) -> ClassificationResult:
        if not self.settings.openai_api_key:
            return self.fallback.classify(subject=subject, body_text=body_text, sender=sender)

        entities = []
        if self.reference_service is not None:
            entities = [
                {"entity_id": entity.entity_id, "label": entity.entity_label}
                for entity in self.reference_service.get_entities()
            ]

        prompt = {
            "subject": subject,
            "sender": sender,
            "body_excerpt": body_text[:4000],
            "entities": entities[:30],
            "categories": [rule.category for rule in RULE_DEFINITIONS],
        }

        try:
            response = self._call_llm(prompt)
            parsed = json.loads(response)
            entity_id = parsed.get("destination_entity_id") or "COU"
            destination_serial_id = None
            if self.reference_service is not None:
                destination_serial_id = self.reference_service.get_entity_serial_id(entity_id)

            rule = next((item for item in RULE_DEFINITIONS if item.department == entity_id), RULE_DEFINITIONS[-1])
            doctype_id, doctype_label = self.fallback._resolve_doctype(rule.department, rule.category)

            return ClassificationResult(
                category=parsed.get("category", "general"),
                confidence=float(parsed.get("confidence", 0.75)),
                subject=parsed.get("subject") or subject,
                destination_entity_id=entity_id,
                destination_serial_id=destination_serial_id,
                doctype_id=doctype_id,
                doctype_label=doctype_label,
                method="openai",
                reasoning=parsed.get("reasoning"),
            )
        except Exception as exc:
            logger.warning("OpenAI LLM classification failed, using rules fallback: %s", exc)
            return self.fallback.classify(subject=subject, body_text=body_text, sender=sender)

    def _call_llm(self, prompt: dict) -> str:
        base_url = (self.settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You classify incoming mail for a French public administration GEC platform. "
                        "Return strict JSON with keys: category, confidence, subject, destination_entity_id, "
                        "doctype_id, doctype_label, reasoning."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.settings.openai_timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return _extract_json(content)


def build_classifier(
    settings: Settings | None = None,
    reference_service: ReferenceDataService | None = None,
) -> DocumentClassifier:
    settings = settings or get_settings()
    if settings.ai_provider == "hybrid" or settings.ai_provider == "ollama":
        return HybridClassifier(settings, reference_service)
    elif settings.ai_provider == "openai":
        return OpenAiClassifier(settings, reference_service)
    return RuleBasedClassifier(reference_service)


def _build_subject(original_subject: str, category: str) -> str:
    cleaned = original_subject.strip()
    if cleaned and cleaned != "(no subject)":
        return cleaned[:255]
    return f"Courrier entrant - {category}"[:255]


def _extract_json(content: str) -> str:
    content = content.strip()
    if content.startswith("{"):
        return content

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        return match.group(0)

    raise ValueError("LLM response did not contain JSON")
