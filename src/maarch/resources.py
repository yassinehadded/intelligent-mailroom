from __future__ import annotations

from typing import Any

from src.maarch.client import MaarchClient
from src.maarch.models import (
    CreateResourceRequest,
    CreateResourceResponse,
    ResourceListQuery,
    UpdateStatusRequest,
)


class ResourceService:
    """Operations on Maarch courriers (POST /rest/resources, etc.)."""

    def __init__(self, client: MaarchClient):
        self.client = client

    def create(self, payload: CreateResourceRequest) -> CreateResourceResponse:
        body = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        response = self.client.post("resources", json=body)
        return self._parse_create_response(response)

    def get(self, res_id: int) -> dict[str, Any]:
        return self.client.get(f"resources/{res_id}")

    def list(self, query: ResourceListQuery) -> dict[str, Any]:
        body = query.model_dump(by_alias=True, exclude_none=True, mode="json")
        return self.client.post("res/list", json=body)

    def update_status(self, payload: UpdateStatusRequest) -> dict[str, Any]:
        body = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        return self.client.put("res/resource/status", json=body)

    def get_diffusion_list(self, res_id: int) -> dict[str, Any]:
        return self.client.get(f"resources/{res_id}/listInstance")

    def get_visa_circuit(self, res_id: int) -> dict[str, Any]:
        return self.client.get(f"resources/{res_id}/visaCircuit")

    @staticmethod
    def _parse_create_response(response: Any) -> CreateResourceResponse:
        if isinstance(response, dict) and "resId" in response:
            return CreateResourceResponse.model_validate(response)

        if isinstance(response, list) and response:
            first = response[0]
            if isinstance(first, dict) and "resId" in first:
                return CreateResourceResponse.model_validate(first)

        if isinstance(response, dict) and "res_id" in response:
            return CreateResourceResponse(resId=response["res_id"])

        raise ValueError(f"Unexpected create resource response: {response!r}")
