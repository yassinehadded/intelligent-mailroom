from __future__ import annotations

import base64
import email
import imaplib
from datetime import datetime
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime, parseaddr

from src.config import Settings, get_settings
from src.email.exceptions import EmailConfigurationError, EmailConnectionError
from src.email.models import ParsedAttachment, ParsedEmail
from src.utils import get_logger


logger = get_logger(__name__)

SUPPORTED_MAIN_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tif", "tiff", "doc", "docx"}
PREFERRED_MAIN_EXTENSIONS = ("pdf", "doc", "docx", "tif", "tiff", "jpg", "jpeg", "png")


class ImapClient:
    """Minimal IMAP client for fetching unread messages."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._connection: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None

    def _validate_configuration(self) -> None:
        if not self.settings.email_host:
            raise EmailConfigurationError("EMAIL_HOST is not configured")
        if not self.settings.email_username or not self.settings.email_password:
            raise EmailConfigurationError("EMAIL_USERNAME and EMAIL_PASSWORD are required")

    def connect(self) -> None:
        self._validate_configuration()

        try:
            if self.settings.email_use_ssl:
                self._connection = imaplib.IMAP4_SSL(
                    self.settings.email_host,
                    self.settings.email_port,
                )
            else:
                self._connection = imaplib.IMAP4(
                    self.settings.email_host,
                    self.settings.email_port,
                )

            self._connection.login(
                self.settings.email_username,
                self.settings.email_password,
            )
            logger.info("Connected to IMAP server %s", self.settings.email_host)
        except imaplib.IMAP4.error as exc:
            raise EmailConnectionError(f"IMAP authentication failed: {exc}") from exc
        except OSError as exc:
            raise EmailConnectionError(f"IMAP connection failed: {exc}") from exc

    def disconnect(self) -> None:
        if self._connection is None:
            return

        try:
            self._connection.close()
        except imaplib.IMAP4.error:
            pass

        try:
            self._connection.logout()
        except imaplib.IMAP4.error:
            pass

        self._connection = None

    def ping(self) -> dict[str, str | int]:
        self.connect()
        try:
            status, data = self._require_connection().select(self.settings.email_mailbox, readonly=True)
            if status != "OK":
                raise EmailConnectionError(f"Unable to select mailbox {self.settings.email_mailbox}")

            message_count = int(data[0]) if data and data[0] else 0
            return {
                "mailbox": self.settings.email_mailbox,
                "message_count": message_count,
                "host": self.settings.email_host,
            }
        finally:
            self.disconnect()

    def fetch_unseen(self, *, limit: int | None = None) -> list[ParsedEmail]:
        self.connect()
        try:
            self._require_connection().select(self.settings.email_mailbox)
            status, data = self._require_connection().search(None, "UNSEEN")
            if status != "OK":
                raise EmailConnectionError("IMAP search for UNSEEN messages failed")

            uids = data[0].split() if data and data[0] else []
            if limit is not None:
                uids = uids[:limit]

            parsed_messages: list[ParsedEmail] = []
            for uid in uids:
                uid_text = uid.decode() if isinstance(uid, bytes) else str(uid)
                parsed = self._fetch_message(uid_text)
                if parsed is not None:
                    parsed_messages.append(parsed)

            return parsed_messages
        finally:
            self.disconnect()

    def mark_as_seen(self, uid: str) -> None:
        self.connect()
        try:
            self._require_connection().select(self.settings.email_mailbox)
            self._require_connection().store(uid, "+FLAGS", "\\Seen")
        finally:
            self.disconnect()

    def _fetch_message(self, uid: str) -> ParsedEmail | None:
        status, data = self._require_connection().fetch(uid, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            logger.warning("Failed to fetch message uid=%s", uid)
            return None

        raw_email = data[0][1]
        message = email.message_from_bytes(raw_email)
        return parse_email_message(uid=uid, message=message)

    def _require_connection(self) -> imaplib.IMAP4 | imaplib.IMAP4_SSL:
        if self._connection is None:
            raise EmailConnectionError("IMAP connection is not established")
        return self._connection


def parse_email_message(*, uid: str, message: Message) -> ParsedEmail:
    subject = _decode_header_value(message.get("Subject")) or "(no subject)"
    sender_raw = _decode_header_value(message.get("From")) or "unknown"
    sender_name, sender_email = parseaddr(sender_raw)
    sender = sender_name or sender_email or sender_raw

    received_at = None
    date_header = message.get("Date")
    if date_header:
        try:
            received_at = parsedate_to_datetime(date_header)
        except (TypeError, ValueError, IndexError):
            received_at = None

    body_text, attachments = _extract_content(message)

    return ParsedEmail(
        uid=uid,
        message_id=_decode_header_value(message.get("Message-ID")),
        subject=subject.strip(),
        sender=sender.strip(),
        sender_email=sender_email or None,
        received_at=received_at,
        body_text=body_text,
        attachments=attachments,
    )


def _extract_content(message: Message) -> tuple[str | None, list[ParsedAttachment]]:
    body_text: str | None = None
    attachments: list[ParsedAttachment] = []

    if message.is_multipart():
        for part in message.walk():
            disposition = part.get_content_disposition()
            filename = part.get_filename()

            if disposition == "attachment" or filename:
                attachment = _parse_attachment_part(part, filename)
                if attachment is not None:
                    attachments.append(attachment)
                continue

            if disposition == "inline" and filename:
                attachment = _parse_attachment_part(part, filename)
                if attachment is not None:
                    attachments.append(attachment)
                continue

            if disposition is not None:
                continue

            if part.get_content_type() == "text/plain" and body_text is None:
                body_text = _decode_payload(part)
    else:
        if message.get_content_type() == "text/plain":
            body_text = _decode_payload(message)

    return body_text, attachments


def _parse_attachment_part(part: Message, filename: str | None) -> ParsedAttachment | None:
    decoded_filename = _decode_header_value(filename) if filename else None
    if not decoded_filename:
        decoded_filename = "attachment.bin"

    payload = part.get_payload(decode=True)
    if not payload:
        return None

    extension = decoded_filename.rsplit(".", 1)[-1].lower() if "." in decoded_filename else "bin"
    return ParsedAttachment(
        filename=decoded_filename,
        content=payload,
        content_type=part.get_content_type(),
        extension=extension,
    )


def _decode_header_value(value: str | None) -> str | None:
    if not value:
        return None

    parts = decode_header(value)
    decoded_chunks: list[str] = []

    for chunk, encoding in parts:
        if isinstance(chunk, bytes):
            decoded_chunks.append(chunk.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded_chunks.append(chunk)

    return "".join(decoded_chunks)


def _decode_payload(part: Message) -> str | None:
    payload = part.get_payload(decode=True)
    if payload is None:
        return None

    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace").strip()


def choose_main_attachment(attachments: list[ParsedAttachment]) -> ParsedAttachment | None:
    if not attachments:
        return None

    for preferred in PREFERRED_MAIN_EXTENSIONS:
        for attachment in attachments:
            if attachment.extension.lower() == preferred:
                return attachment

    return attachments[0]


def encode_file_base64(content: bytes) -> str:
    return base64.b64encode(content).decode("ascii")


def normalize_maarch_format(extension: str) -> str:
    normalized = extension.lower().lstrip(".")
    mapping = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "tif": "TIFF",
        "tiff": "TIFF",
        "docx": "DOCX",
        "doc": "DOC",
        "pdf": "PDF",
        "png": "PNG",
    }
    return mapping.get(normalized, normalized.upper())
