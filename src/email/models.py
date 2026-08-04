from __future__ import annotations

import base64
from datetime import datetime

from pydantic import BaseModel, Field


class ClassificationSummary(BaseModel):
    category: str
    confidence: float
    method: str
    destination_entity_id: str | None = None
    destination_serial_id: int | None = None
    doctype_id: int | None = None
    doctype_label: str | None = None
    ocr_source: str | None = None
    reasoning: str | None = None


class ParsedAttachment(BaseModel):
    filename: str
    content: bytes
    content_type: str
    extension: str


class ParsedEmail(BaseModel):
    uid: str
    message_id: str | None = None
    subject: str
    sender: str
    sender_email: str | None = None
    received_at: datetime | None = None
    body_text: str | None = None
    attachments: list[ParsedAttachment] = Field(default_factory=list)


class IngestedAttachmentResult(BaseModel):
    filename: str
    attachment_id: int


class IngestedEmailResult(BaseModel):
    uid: str
    message_id: str | None = None
    subject: str
    res_id: int
    attachments: list[IngestedAttachmentResult] = Field(default_factory=list)
    classification: ClassificationSummary | None = None
    skipped: bool = False
    reason: str | None = None


class EmailPollResult(BaseModel):
    fetched: int
    ingested: int
    skipped: int
    failed: int
    results: list[IngestedEmailResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
