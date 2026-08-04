from __future__ import annotations

from datetime import date, datetime
from typing import Any

from src.ai.pipeline import DocumentAnalysisPipeline
from src.config import Settings, get_settings
from src.database import AuditRepository, get_audit_repository
from src.email.exceptions import EmailError
from src.email.imap_client import (
    ImapClient,
    choose_main_attachment,
    encode_file_base64,
    normalize_maarch_format,
)
from src.email.models import (
    ClassificationSummary,
    EmailPollResult,
    IngestedAttachmentResult,
    IngestedEmailResult,
    ParsedAttachment,
    ParsedEmail,
)
from src.maarch import CreateAttachmentRequest, CreateResourceRequest, MaarchService, get_maarch_service
from src.maarch.exceptions import MaarchAPIError
from src.maarch.models import ResourceListQuery, SenderRecipient
from src.utils import get_logger


logger = get_logger(__name__)


class EmailIngestionService:
    """
    Polls the mailbox and injects incoming emails into Maarch Courrier.

    Flow per email:
    1. OCR + AI classification (subject, destination, doctype)
    2. Resolve sender contact in Maarch
    3. Create courrier (model 8 - Courriels importés, status INIT)
    4. Upload remaining attachments
    5. Write audit event and mark email as seen in IMAP
    """

    def __init__(
        self,
        settings: Settings | None = None,
        imap_client: ImapClient | None = None,
        maarch_service: MaarchService | None = None,
        analysis_pipeline: DocumentAnalysisPipeline | None = None,
        audit_repository: AuditRepository | None = None,
    ):
        self.settings = settings or get_settings()
        self.imap_client = imap_client or ImapClient(self.settings)
        self.maarch_service = maarch_service or get_maarch_service()
        self.analysis_pipeline = analysis_pipeline or DocumentAnalysisPipeline(
            settings=self.settings,
            reference_service=self.maarch_service.reference,
        )
        self.audit_repository = audit_repository or get_audit_repository()

    def poll_and_ingest(self, *, limit: int | None = None) -> EmailPollResult:
        effective_limit = limit or self.settings.email_fetch_limit
        messages = self.imap_client.fetch_unseen(limit=effective_limit)

        result = EmailPollResult(
            fetched=len(messages),
            ingested=0,
            skipped=0,
            failed=0,
        )

        for message in messages:
            try:
                ingested = self._ingest_message(message)
                result.results.append(ingested)

                if ingested.skipped:
                    result.skipped += 1
                else:
                    result.ingested += 1
                    if self.settings.email_mark_as_read:
                        self.imap_client.mark_as_seen(message.uid)
            except (EmailError, MaarchAPIError, ValueError) as exc:
                result.failed += 1
                error_message = f"uid={message.uid}: {exc}"
                result.errors.append(error_message)
                logger.error("Email ingestion failed for %s", error_message)
                self._record_audit_event(
                    event_type="failed",
                    message=message,
                    error_message=str(exc),
                )

        return result

    def _ingest_message(self, message: ParsedEmail) -> IngestedEmailResult:
        if self._is_duplicate(message):
            self._record_audit_event(
                event_type="skipped",
                message=message,
                error_message="Duplicate message",
            )
            return IngestedEmailResult(
                uid=message.uid,
                message_id=message.message_id,
                subject=message.subject,
                res_id=0,
                skipped=True,
                reason="Duplicate message",
            )

        main_attachment = choose_main_attachment(message.attachments)
        remaining_attachments = [
            attachment
            for attachment in message.attachments
            if attachment is not main_attachment
        ]

        analysis = None
        if self.settings.ai_enabled:
            analysis = self.analysis_pipeline.analyze(
                subject=message.subject,
                sender=message.sender,
                body_text=message.body_text,
                file_content=main_attachment.content if main_attachment else None,
                file_extension=main_attachment.extension if main_attachment else None,
            )

        contact_id = self._resolve_sender_contact(message)
        resource_payload = self._build_resource_payload(
            message,
            main_attachment,
            analysis,
            contact_id=contact_id,
        )
        created = self.maarch_service.resources.create(resource_payload)

        uploaded_attachments: list[IngestedAttachmentResult] = []
        for attachment in remaining_attachments:
            attachment_result = self.maarch_service.attachments.create(
                CreateAttachmentRequest(
                    resIdMaster=created.res_id,
                    type=self.settings.maarch_default_attachment_type,
                    encodedFile=encode_file_base64(attachment.content),
                    format=normalize_maarch_format(attachment.extension),
                    title=attachment.filename,
                )
            )
            uploaded_attachments.append(
                IngestedAttachmentResult(
                    filename=attachment.filename,
                    attachment_id=attachment_result.id,
                )
            )

        classification_summary = _to_classification_summary(analysis)
        self._record_audit_event(
            event_type="ingested",
            message=message,
            res_id=created.res_id,
            classification=classification_summary,
            details={
                "attachments_uploaded": len(uploaded_attachments),
                "contact_id": contact_id,
            },
        )

        logger.info(
            "Ingested email uid=%s into Maarch res_id=%s with %s attachments",
            message.uid,
            created.res_id,
            len(uploaded_attachments),
        )

        return IngestedEmailResult(
            uid=message.uid,
            message_id=message.message_id,
            subject=resource_payload.subject or message.subject,
            res_id=created.res_id,
            attachments=uploaded_attachments,
            classification=classification_summary,
        )

    def _resolve_sender_contact(self, message: ParsedEmail) -> int | None:
        if not self.settings.maarch_auto_create_contacts:
            return None

        try:
            return self.maarch_service.contacts.resolve_sender(
                sender=message.sender,
                sender_email=message.sender_email,
            )
        except MaarchAPIError as exc:
            logger.warning("Unable to resolve sender contact for uid=%s: %s", message.uid, exc)
            return None

    def _build_resource_payload(
        self,
        message: ParsedEmail,
        main_attachment: ParsedAttachment | None,
        analysis=None,
        *,
        contact_id: int | None = None,
    ) -> CreateResourceRequest:
        classification = analysis.classification if analysis is not None else None

        subject = (
            classification.subject
            if classification and classification.subject
            else message.subject[:255]
        )

        payload_kwargs: dict[str, Any] = {
            "modelId": self.settings.maarch_default_model_id,
            "status": self.settings.maarch_default_status,
            "subject": subject,
            "chrono": True,
        }

        destination = self.settings.email_default_destination
        if classification and classification.destination_serial_id is not None:
            destination = classification.destination_serial_id
        if destination is not None:
            payload_kwargs["destination"] = destination

        if classification and classification.doctype_id is not None:
            payload_kwargs["doctype"] = classification.doctype_id

        priority = self.maarch_service.reference.get_default_priority_id()
        if priority:
            payload_kwargs["priority"] = priority

        if message.received_at is not None:
            payload_kwargs["documentDate"] = _as_date(message.received_at)
            payload_kwargs["arrivalDate"] = _as_date(message.received_at)

        if contact_id is not None:
            payload_kwargs["senders"] = [SenderRecipient(id=contact_id, type="contact")]

        if message.message_id:
            external_id = {"emailMessageId": message.message_id}
            if classification:
                external_id["automationCategory"] = classification.category
                external_id["automationMethod"] = classification.method
            payload_kwargs["externalId"] = external_id

        if main_attachment is not None:
            payload_kwargs["encodedFile"] = encode_file_base64(main_attachment.content)
            payload_kwargs["format"] = normalize_maarch_format(main_attachment.extension)

        return CreateResourceRequest(**payload_kwargs)

    def _is_duplicate(self, message: ParsedEmail) -> bool:
        if not message.message_id:
            return False

        if self.settings.audit_enabled and self.audit_repository.has_message_id(message.message_id):
            return True

        clause = f"external_id::text like '%{self._escape_sql_literal(message.message_id)}%'"
        try:
            response = self.maarch_service.resources.list(
                ResourceListQuery(
                    select="res_id",
                    clause=clause,
                    limit=1,
                )
            )
        except MaarchAPIError:
            return False

        resources = response.get("resources", []) if isinstance(response, dict) else []
        return bool(resources)

    def _record_audit_event(
        self,
        *,
        event_type: str,
        message: ParsedEmail,
        res_id: int | None = None,
        classification: ClassificationSummary | None = None,
        error_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if not self.settings.audit_enabled:
            return

        self.audit_repository.record_event(
            event_type=event_type,
            email_uid=message.uid,
            message_id=message.message_id,
            subject=message.subject,
            sender_email=message.sender_email,
            res_id=res_id,
            destination_serial_id=classification.destination_serial_id if classification else None,
            doctype_id=classification.doctype_id if classification else None,
            category=classification.category if classification else None,
            confidence=classification.confidence if classification else None,
            error_message=error_message,
            details=details,
        )

    @staticmethod
    def _escape_sql_literal(value: str) -> str:
        return value.replace("'", "''")


def _as_date(value: datetime) -> date:
    return value.date()


def _to_classification_summary(analysis) -> ClassificationSummary | None:
    if analysis is None:
        return None

    classification = analysis.classification
    return ClassificationSummary(
        category=classification.category,
        confidence=classification.confidence,
        method=classification.method,
        destination_entity_id=classification.destination_entity_id,
        destination_serial_id=classification.destination_serial_id,
        doctype_id=classification.doctype_id,
        doctype_label=classification.doctype_label,
        ocr_source=analysis.ocr_source,
        reasoning=classification.reasoning,
    )
