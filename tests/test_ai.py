from unittest.mock import MagicMock

from src.ai.classifier import RuleBasedClassifier
from src.ai.pipeline import DocumentAnalysisPipeline
from src.config import Settings
from src.ocr.extractor import DocumentTextExtractor


def test_rule_classifier_routes_invoice_to_finance():
    reference = MagicMock()
    reference.get_entity_serial_id.return_value = 17
    reference.get_flat_doctypes.return_value = [
        {"type_id": 407, "label": "Facture ou avoir"},
        {"type_id": 1203, "label": "Courriel importé"},
    ]

    classifier = RuleBasedClassifier(reference)
    result = classifier.classify(
        subject="Facture fournisseur janvier",
        body_text="Veuillez trouver ci-joint la facture n° 2026-001.",
        sender="billing@vendor.com",
    )

    assert result.category == "invoice"
    assert result.destination_entity_id == "FIN"
    assert result.destination_serial_id == 17
    assert result.doctype_id == 407
    assert result.method == "rules"


def test_rule_classifier_routes_hr_request_to_drh():
    reference = MagicMock()
    reference.get_entity_serial_id.return_value = 11
    reference.get_flat_doctypes.return_value = [
        {"type_id": 703, "label": "Candidature"},
    ]

    classifier = RuleBasedClassifier(reference)
    result = classifier.classify(
        subject="Candidature spontanée",
        body_text="Je souhaite postuler au service RH.",
    )

    assert result.category == "hr"
    assert result.destination_entity_id == "DRH"


def test_rule_classifier_routes_voirie_to_pte():
    reference = MagicMock()
    reference.get_entity_serial_id.return_value = 10
    reference.get_flat_doctypes.return_value = [
        {"type_id": 1202, "label": "Demande intervention voirie"},
    ]

    classifier = RuleBasedClassifier(reference)
    result = classifier.classify(
        subject="Nid de poule rue principale",
        body_text="Demande d'intervention voirie urgente.",
    )

    assert result.category == "technical"
    assert result.destination_entity_id == "PTE"
    assert result.doctype_id == 1202


def test_document_analysis_pipeline_classifies_body_text():
    settings = Settings(
        maarch_url="http://localhost:8081",
        ai_enabled=True,
        ai_provider="rules",
        ocr_enabled=True,
    )

    reference = MagicMock()
    reference.get_entity_serial_id.return_value = 17
    reference.get_flat_doctypes.return_value = [
        {"type_id": 407, "label": "Facture ou avoir"},
    ]

    pipeline = DocumentAnalysisPipeline(
        settings=settings,
        text_extractor=DocumentTextExtractor(settings),
        reference_service=reference,
    )

    result = pipeline.analyze(
        subject="Document entrant",
        body_text="Facture fournisseur pour prestation janvier 2026.",
    )

    assert result.ocr_source == "fallback"
    assert result.classification.category == "invoice"
    assert result.classification.destination_entity_id == "FIN"
