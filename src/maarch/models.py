from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DiffusionListItem(BaseModel):
    id: int
    mode: Literal["dest", "cc", "avis", "visa", "sign"]
    type: Literal["user", "entity"]


class SenderRecipient(BaseModel):
    id: int
    type: Literal["contact", "user", "entity"]


class CreateResourceRequest(BaseModel):
    """Payload for POST /rest/resources (verified against Maarch 2301 docs)."""

    model_id: int = Field(alias="modelId")
    status: str
    subject: str | None = None
    doctype: int | None = None
    chrono: bool = False
    typist: int | None = None
    destination: int | None = None
    initiator: int | None = None
    confidentiality: bool = False
    document_date: datetime | date | None = Field(default=None, alias="documentDate")
    arrival_date: datetime | date | None = Field(default=None, alias="arrivalDate")
    departure_date: datetime | date | None = Field(default=None, alias="departureDate")
    process_limit_date: datetime | date | None = Field(default=None, alias="processLimitDate")
    priority: str | None = None
    barcode: str | None = None
    encoded_file: str | None = Field(default=None, alias="encodedFile")
    format: str | None = None
    external_id: dict[str, Any] | None = Field(default=None, alias="externalId")
    custom_fields: dict[str, Any] | None = Field(default=None, alias="customFields")
    senders: list[SenderRecipient] | None = None
    recipients: list[SenderRecipient] | None = None
    diffusion_list: list[DiffusionListItem] | None = Field(default=None, alias="diffusionList")
    folders: list[int] | None = None
    tags: list[int] | None = None

    model_config = {"populate_by_name": True}


class CreateResourceResponse(BaseModel):
    res_id: int = Field(alias="resId")

    model_config = {"populate_by_name": True}


class CreateAttachmentRequest(BaseModel):
    """Payload for POST /rest/attachments."""

    res_id_master: int = Field(alias="resIdMaster")
    type: str
    encoded_file: str = Field(alias="encodedFile")
    format: str
    title: str | None = None
    chrono: str | None = None
    status: str | None = None
    typist: int | None = None
    origin_id: int | None = Field(default=None, alias="originId")
    recipient_id: int | None = Field(default=None, alias="recipientId")
    recipient_type: Literal["user", "contact"] | None = Field(default=None, alias="recipientType")
    external_id: dict[str, Any] | None = Field(default=None, alias="externalId")

    model_config = {"populate_by_name": True}


class CreateAttachmentResponse(BaseModel):
    id: int


class ResourceListQuery(BaseModel):
    select: str
    clause: str
    with_file: bool = Field(default=False, alias="withFile")
    order_by: list[str] | None = Field(default=None, alias="orderBy")
    limit: int | None = None

    model_config = {"populate_by_name": True}


class UpdateStatusRequest(BaseModel):
    status: str
    res_id: list[int] = Field(alias="resId")
    history_message: str | None = Field(default=None, alias="historyMessage")

    model_config = {"populate_by_name": True}


class Entity(BaseModel):
    entity_id: str
    entity_label: str
    serial_id: int = Field(alias="serialId")
    parent_entity_id: str | None = Field(default=None, alias="parent_entity_id")

    model_config = {"populate_by_name": True}


class IndexingModel(BaseModel):
    id: int
    label: str
    category: str
    default: bool
    mandatory_file: bool = Field(alias="mandatoryFile")

    model_config = {"populate_by_name": True}
