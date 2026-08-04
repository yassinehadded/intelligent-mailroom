from __future__ import annotations

import email
from datetime import datetime, timezone
from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.config import Settings
from src.email.imap_client import choose_main_attachment, parse_email_message
from src.email.models import ParsedAttachment, ParsedEmail
from src.email.processor import EmailIngestionService
from src.maarch.models import CreateResourceResponse


def _build_sample_email() -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = "Invoice from ACME"
    message["From"] = "billing@acme.com"
    message["To"] = "mailroom@example.com"
    message["Date"] = "Thu, 30 Jul 2026 10:00:00 +0000"
    message["Message-ID"] = "<invoice-123@acme.com>"
    message.set_content("Please find the attached invoice.")

    pdf_bytes = b"%PDF-1.4 sample"
    message.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="invoice.pdf")

    png_bytes = b"\x89PNG sample"
    message.add_attachment(png_bytes, maintype="image", subtype="png", filename="scan.png")

    return message


def test_parse_email_message_extracts_metadata_and_attachments():
    raw = _build_sample_email()
    parsed = parse_email_message(uid="42", message=raw)

    assert parsed.uid == "42"
    assert parsed.subject == "Invoice from ACME"
    assert parsed.sender_email == "billing@acme.com"
    assert parsed.message_id == "<invoice-123@acme.com>"
    assert parsed.body_text == "Please find the attached invoice."
    assert len(parsed.attachments) == 2
    assert parsed.attachments[0].filename == "invoice.pdf"


def test_choose_main_attachment_prefers_pdf():
    attachments = [
        ParsedAttachment(filename="scan.png", content=b"png", content_type="image/png", extension="png"),
        ParsedAttachment(filename="invoice.pdf", content=b"pdf", content_type="application/pdf", extension="pdf"),
    ]

    chosen = choose_main_attachment(attachments)
    assert chosen is not None
    assert chosen.filename == "invoice.pdf"


def test_email_ingestion_creates_resource_and_remaining_attachments():
    settings = Settings(
        maarch_url="http://localhost:8081",
        maarch_username="user",
        maarch_password="pass",
        email_default_destination=13,
        ai_enabled=False,
        audit_enabled=False,
    )

    parsed = ParsedEmail(
        uid="99",
        message_id="<duplicate-test@acme.com>",
        subject="Invoice from ACME",
        sender="billing@acme.com",
        sender_email="billing@acme.com",
        received_at=datetime(2026, 7, 30, 10, 0, tzinfo=timezone.utc),
        body_text="Body",
        attachments=[
            ParsedAttachment(filename="invoice.pdf", content=b"%PDF", content_type="application/pdf", extension="pdf"),
            ParsedAttachment(filename="scan.png", content=b"PNG", content_type="image/png", extension="png"),
        ],
    )

    mock_imap = MagicMock()
    mock_imap.fetch_unseen.return_value = [parsed]

    mock_maarch = MagicMock()
    mock_maarch.reference.get_default_priority_id.return_value = "poiuytre1357nbvc"
    mock_maarch.resources.list.return_value = {"resources": [], "count": 0}
    mock_maarch.resources.create.return_value = CreateResourceResponse(resId=501)
    mock_maarch.attachments.create.return_value = MagicMock(id=9001)

    service = EmailIngestionService(
        settings=settings,
        imap_client=mock_imap,
        maarch_service=mock_maarch,
    )

    result = service.poll_and_ingest()

    assert result.fetched == 1
    assert result.ingested == 1
    assert result.failed == 0
    assert result.results[0].res_id == 501
    assert len(result.results[0].attachments) == 1
    assert result.results[0].attachments[0].filename == "scan.png"

    create_payload = mock_maarch.resources.create.call_args.args[0]
    assert create_payload.model_dump(by_alias=True)["destination"] == 13
    assert create_payload.encoded_file is not None
    assert create_payload.format == "PDF"

    mock_imap.mark_as_seen.assert_called_once_with("99")


def test_email_ingestion_skips_duplicate_message_id():
    settings = Settings(
        maarch_url="http://localhost:8081",
        maarch_username="user",
        maarch_password="pass",
        ai_enabled=False,
        audit_enabled=False,
    )

    parsed = ParsedEmail(
        uid="100",
        message_id="<already-ingested@acme.com>",
        subject="Duplicate",
        sender="sender@acme.com",
        attachments=[],
    )

    mock_imap = MagicMock()
    mock_imap.fetch_unseen.return_value = [parsed]

    mock_maarch = MagicMock()
    mock_maarch.resources.list.return_value = {"resources": [{"res_id": 10}], "count": 1}

    service = EmailIngestionService(
        settings=settings,
        imap_client=mock_imap,
        maarch_service=mock_maarch,
    )

    result = service.poll_and_ingest()

    assert result.skipped == 1
    assert result.ingested == 0
    mock_maarch.resources.create.assert_not_called()
    mock_imap.mark_as_seen.assert_not_called()


def test_email_status_endpoint_without_credentials():
    app = create_app()
    client = TestClient(app)

    with patch("src.api.routes.email.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            maarch_url="http://localhost:8081",
            email_host=None,
            email_username=None,
            email_password=None,
        )
        response = client.get("/api/v1/email/status")

    assert response.status_code == 200
    assert response.json()["configured"] is False


def test_email_poll_requires_configuration():
    app = create_app()
    client = TestClient(app)

    with patch("src.api.routes.email.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            maarch_url="http://localhost:8081",
            maarch_username="user",
            maarch_password="pass",
            email_host=None,
        )
        response = client.post("/api/v1/email/poll")

    assert response.status_code == 503
