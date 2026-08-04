
def test_email_ingestion_applies_classification_metadata():
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    from src.ai.models import ClassificationResult, DocumentAnalysisResult
    from src.config import Settings
    from src.email.models import ParsedAttachment, ParsedEmail
    from src.email.processor import EmailIngestionService
    from src.maarch.models import CreateResourceResponse

    settings = Settings(
        maarch_url="http://localhost:8081",
        maarch_username="user",
        maarch_password="pass",
        ai_enabled=True,
        audit_enabled=False,
        maarch_auto_create_contacts=False,
    )

    parsed = ParsedEmail(
        uid="77",
        message_id="<classified@acme.com>",
        subject="Fwd: invoice",
        sender="billing@acme.com",
        received_at=datetime(2026, 7, 30, 10, 0, tzinfo=timezone.utc),
        body_text="Facture mensuelle",
        attachments=[
            ParsedAttachment(filename="invoice.pdf", content=b"%PDF", content_type="application/pdf", extension="pdf"),
        ],
    )

    mock_imap = MagicMock()
    mock_imap.fetch_unseen.return_value = [parsed]

    mock_maarch = MagicMock()
    mock_maarch.reference.get_default_priority_id.return_value = "priority-1"
    mock_maarch.resources.list.return_value = {"resources": [], "count": 0}
    mock_maarch.resources.create.return_value = CreateResourceResponse(resId=777)
    mock_maarch.attachments.create.return_value = MagicMock(id=1)

    mock_pipeline = MagicMock()
    mock_pipeline.analyze.return_value = DocumentAnalysisResult(
        ocr_source="pdf",
        extracted_text_preview="Facture",
        classification=ClassificationResult(
            category="invoice",
            confidence=0.9,
            subject="Facture ACME",
            destination_entity_id="FIN",
            destination_serial_id=17,
            doctype_id=407,
            doctype_label="Facture ou avoir",
            method="rules",
        ),
    )

    service = EmailIngestionService(
        settings=settings,
        imap_client=mock_imap,
        maarch_service=mock_maarch,
        analysis_pipeline=mock_pipeline,
    )

    result = service.poll_and_ingest()

    assert result.ingested == 1
    assert result.results[0].classification is not None
    assert result.results[0].classification.category == "invoice"
    assert result.results[0].classification.destination_serial_id == 17

    create_payload = mock_maarch.resources.create.call_args.args[0]
    dumped = create_payload.model_dump(by_alias=True)
    assert dumped["subject"] == "Facture ACME"
    assert dumped["destination"] == 17
    assert dumped["doctype"] == 407
    assert dumped["externalId"]["automationCategory"] == "invoice"
