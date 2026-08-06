from __future__ import annotations

import time

from src.ai.classifier import DocumentClassifier, build_classifier
from src.ai.models import ClassificationResult, DocumentAnalysisResult
from src.config import Settings, get_settings
from src.maarch.reference import ReferenceDataService
from src.ocr import DocumentTextExtractor, OcrResult


class DocumentAnalysisPipeline:
    """Runs OCR then hybrid classification (Rules + Qwen 2.5 7B + Decision Layer) to produce routing metadata."""

    PREVIEW_LENGTH = 500

    def __init__(
        self,
        settings: Settings | None = None,
        text_extractor: DocumentTextExtractor | None = None,
        classifier: DocumentClassifier | None = None,
        reference_service: ReferenceDataService | None = None,
    ):
        self.settings = settings or get_settings()
        self.text_extractor = text_extractor or DocumentTextExtractor(self.settings)
        self.reference_service = reference_service
        self.classifier = classifier or build_classifier(self.settings, reference_service)

    def analyze(
        self,
        *,
        subject: str,
        sender: str | None = None,
        body_text: str | None = None,
        file_content: bytes | None = None,
        file_extension: str | None = None,
    ) -> DocumentAnalysisResult:
        start_time = time.perf_counter()

        ocr_result = self.text_extractor.extract(
            content=file_content,
            extension=file_extension,
            fallback_text=self._compose_fallback_text(subject, body_text, sender),
        )

        classification = self.classifier.classify(
            subject=subject,
            body_text=ocr_result.text,
            sender=sender,
        )

        if classification.confidence < self.settings.classification_min_confidence:
            classification = self._apply_safe_defaults(classification, subject)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return DocumentAnalysisResult(
            ocr_source=ocr_result.source,
            extracted_text_preview=ocr_result.text[: self.PREVIEW_LENGTH],
            ocr_text=ocr_result.text,
            classification=classification,
            rule_result=classification.rule_result,
            llm_result=classification.llm_result,
            decision_result=classification.decision,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def _compose_fallback_text(
        self,
        subject: str,
        body_text: str | None,
        sender: str | None,
    ) -> str:
        parts = [subject]
        if sender:
            parts.append(f"From: {sender}")
        if body_text:
            parts.append(body_text)
        return "\n".join(parts)

    def _apply_safe_defaults(
        self,
        classification: ClassificationResult,
        subject: str,
    ) -> ClassificationResult:
        fallback_destination = self.settings.email_default_destination
        if fallback_destination is None and self.reference_service is not None:
            fallback_destination = self.reference_service.get_entity_serial_id("COU")

        return classification.model_copy(
            update={
                "destination_entity_id": classification.destination_entity_id or "COU",
                "destination_serial_id": classification.destination_serial_id or fallback_destination,
                "subject": classification.subject or subject[:255],
            }
        )


def get_document_analysis_pipeline(
    reference_service: ReferenceDataService | None = None,
) -> DocumentAnalysisPipeline:
    return DocumentAnalysisPipeline(reference_service=reference_service)
