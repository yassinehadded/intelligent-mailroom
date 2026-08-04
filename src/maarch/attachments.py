from __future__ import annotations

from typing import Any

from src.maarch.client import MaarchClient
from src.maarch.models import CreateAttachmentRequest, CreateAttachmentResponse


class AttachmentService:
    """Operations on Maarch pièces jointes (POST /rest/attachments, etc.)."""

    def __init__(self, client: MaarchClient):
        self.client = client

    def create(self, payload: CreateAttachmentRequest) -> CreateAttachmentResponse:
        body = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        response = self.client.post("attachments", json=body)
        return self._parse_create_response(response)

    def list_for_resource(self, res_id: int, *, limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return self.client.get(f"resources/{res_id}/attachments", params=params)

    def get_content_base64(self, attachment_id: int) -> dict[str, Any]:
        return self.client.get(f"attachments/{attachment_id}/content", params={"mode": "base64"})

    @staticmethod
    def _parse_create_response(response: Any) -> CreateAttachmentResponse:
        if isinstance(response, dict) and "id" in response:
            return CreateAttachmentResponse.model_validate(response)

        if isinstance(response, list) and response:
            first = response[0]
            if isinstance(first, dict) and "id" in first:
                return CreateAttachmentResponse.model_validate(first)

        raise ValueError(f"Unexpected create attachment response: {response!r}")
