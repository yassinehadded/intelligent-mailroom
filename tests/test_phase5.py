import sqlite3
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.config import Settings
from src.database.audit import AuditRepository
from src.email.models import ParsedEmail
from src.email.processor import EmailIngestionService
from src.maarch.client import MaarchClient
from src.maarch.contacts import ContactService
from src.maarch.exceptions import MaarchAPIError
from src.maarch.models import CreateResourceResponse


@pytest.fixture
def audit_repo(tmp_path):
    settings = Settings(
        maarch_url="http://localhost:8081",
        audit_db_path=str(tmp_path / "audit.db"),
        audit_enabled=True,
    )
    return AuditRepository(settings)


def test_audit_repository_records_and_deduplicates(audit_repo):
    audit_repo.record_event(
        event_type="ingested",
        message_id="<abc@mail.com>",
        subject="Test",
        res_id=100,
    )

    assert audit_repo.has_message_id("<abc@mail.com>") is True
    events = audit_repo.list_events(limit=10)
    assert len(events) == 1
    assert events[0]["res_id"] == 100


def test_march_client_retries_transient_http_error():
    settings = Settings(
        maarch_url="http://localhost:8081",
        maarch_username="user",
        maarch_password="pass",
        maarch_retry_count=2,
        maarch_retry_backoff_seconds=0,
    )
    client = MaarchClient(settings=settings)

    response_fail = MagicMock()
    response_fail.status_code = 503
    response_fail.content = b'{"errors":"Service unavailable"}'
    response_fail.headers = {"Content-Type": "application/json"}
    response_fail.url = "http://localhost:8081/rest/resources"
    response_fail.json.return_value = {"errors": "Service unavailable"}

    response_ok = MagicMock()
    response_ok.status_code = 200
    response_ok.content = b'{"resId": 42}'
    response_ok.headers = {"Content-Type": "application/json"}
    response_ok.json.return_value = {"resId": 42}

    client._session.request = MagicMock(side_effect=[response_fail, response_ok])

    result = client.post("resources", json={"modelId": 8, "status": "INIT"})
    assert result["resId"] == 42
    assert client._session.request.call_count == 2


def test_contact_service_builds_payload_from_sender_email():
    service = ContactService(MagicMock())
    payload = service._build_contact_payload(
        sender="Billing Team <billing@acme.com>",
        email_address="billing@acme.com",
    )

    assert payload.email == "billing@acme.com"
    assert payload.firstname == "Billing"
    assert payload.lastname == "Team"


def test_email_ingestion_uses_audit_log_for_duplicate_detection(tmp_path):
    settings = Settings(
        maarch_url="http://localhost:8081",
        maarch_username="user",
        maarch_password="pass",
        ai_enabled=False,
        audit_enabled=True,
        audit_db_path=str(tmp_path / "audit.db"),
    )

    audit_repo = AuditRepository(settings)
    audit_repo.record_event(
        event_type="ingested",
        message_id="<dup@test.com>",
        subject="Already ingested",
        res_id=55,
    )

    parsed = ParsedEmail(
        uid="1",
        message_id="<dup@test.com>",
        subject="Already ingested",
        sender="sender@test.com",
    )

    mock_imap = MagicMock()
    mock_imap.fetch_unseen.return_value = [parsed]

    mock_maarch = MagicMock()
    service = EmailIngestionService(
        settings=settings,
        imap_client=mock_imap,
        maarch_service=mock_maarch,
        audit_repository=audit_repo,
    )

    result = service.poll_and_ingest()

    assert result.skipped == 1
    mock_maarch.resources.create.assert_not_called()
    mock_imap.mark_as_seen.assert_not_called()


def test_validate_maarch_connection_warns_for_standard_user():
    from src.maarch.connection import validate_maarch_connection

    client = MagicMock()
    client.ping.return_value = {
        "applicationName": "COURRIER DEMO",
        "authMode": "standard",
        "maarchUrl": "http://localhost:8081/",
    }
    client.get_current_user_profile.return_value = {
        "user_id": "jdoe",
        "mode": "standard",
    }

    result = validate_maarch_connection(client)

    assert result["connected"] is True
    assert result["webservice_ready"] is False
    assert result["warnings"]
