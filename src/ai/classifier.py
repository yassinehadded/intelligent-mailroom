from __future__ import annotations

import json
import re
from typing import Protocol

import requests

from src.ai.models import ClassificationResult
from src.ai.routing import ROUTING_RULES, RoutingRule
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
    """Keyword-based classifier used as default and fallback."""

    def __init__(self, reference_service: ReferenceDataService | None = None):
        self.reference_service = reference_service

    def classify(
        self,
        *,
        subject: str,
        body_text: str,
        sender: str | None = None,
    ) -> ClassificationResult:
        combined = " ".join(part for part in [subject, body_text, sender or ""] if part).lower()
        best_rule = self._match_rule(combined)
        doctype_id, doctype_label = self._resolve_doctype(best_rule, combined)

        destination_serial_id = None
        if self.reference_service is not None:
            destination_serial_id = self.reference_service.get_entity_serial_id(best_rule.entity_id)

        confidence = 0.9 if best_rule.category != "general" else 0.55
        return ClassificationResult(
            category=best_rule.category,
            confidence=confidence,
            subject=_build_subject(subject, best_rule.category),
            destination_entity_id=best_rule.entity_id,
            destination_serial_id=destination_serial_id,
            doctype_id=doctype_id,
            doctype_label=doctype_label,
            method="rules",
            reasoning=f"Matched routing rule '{best_rule.category}' via keywords",
        )

    def _match_rule(self, combined_text: str) -> RoutingRule:
        best_rule = ROUTING_RULES[-1]
        best_score = 0

        for rule in ROUTING_RULES:
            if rule.category == "general":
                continue

            score = sum(1 for keyword in rule.keywords if keyword in combined_text)
            if score > best_score:
                best_score = score
                best_rule = rule

        return best_rule

    def _resolve_doctype(
        self,
        rule: RoutingRule,
        combined_text: str,
    ) -> tuple[int | None, str | None]:
        if self.reference_service is None:
            return rule.default_doctype_id, None

        doctypes = self.reference_service.get_flat_doctypes()
        for doctype in doctypes:
            label = doctype["label"].lower()
            if any(keyword in label for keyword in rule.doctype_keywords):
                return doctype["type_id"], doctype["label"]

        for doctype in doctypes:
            label = doctype["label"].lower()
            if any(keyword in combined_text for keyword in rule.doctype_keywords if keyword in label):
                return doctype["type_id"], doctype["label"]

        if rule.default_doctype_id is not None:
            for doctype in doctypes:
                if doctype["type_id"] == rule.default_doctype_id:
                    return doctype["type_id"], doctype["label"]

        return rule.default_doctype_id, None


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
            "categories": [rule.category for rule in ROUTING_RULES],
        }

        try:
            response = self._call_llm(prompt)
            parsed = json.loads(response)
            entity_id = parsed.get("destination_entity_id") or "COU"
            destination_serial_id = None
            if self.reference_service is not None:
                destination_serial_id = self.reference_service.get_entity_serial_id(entity_id)

            doctype_id = parsed.get("doctype_id")
            doctype_label = parsed.get("doctype_label")
            if doctype_id is None:
                rule = next(
                    (item for item in ROUTING_RULES if item.entity_id == entity_id),
                    ROUTING_RULES[-1],
                )
                doctype_id, doctype_label = self.fallback._resolve_doctype(
                    rule,
                    body_text.lower(),
                )

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
            logger.warning("LLM classification failed, using rules fallback: %s", exc)
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
    if settings.ai_provider == "openai":
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
