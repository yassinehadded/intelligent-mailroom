from __future__ import annotations

from functools import lru_cache
from typing import Any

from src.maarch.client import MaarchClient
from src.maarch.models import Entity, IndexingModel


class ReferenceDataService:
    """
    Cached read-only reference data from Maarch.

    Used by the automation layer for routing (entities, doctypes, statuses).
    """

    def __init__(self, client: MaarchClient):
        self.client = client

    def get_entities(self) -> list[Entity]:
        response = self.client.get("entities")
        raw_entities = response.get("entities", []) if isinstance(response, dict) else []
        return [Entity.model_validate(item) for item in raw_entities]

    def get_entity_by_code(self, entity_id: str) -> Entity | None:
        normalized = entity_id.upper()
        for entity in self.get_entities():
            if entity.entity_id.upper() == normalized:
                return entity
        return None

    def get_entity_serial_id(self, entity_id: str) -> int | None:
        entity = self.get_entity_by_code(entity_id)
        return entity.serial_id if entity else None

    def get_statuses(self) -> list[dict[str, Any]]:
        response = self.client.get("statuses")
        return response.get("statuses", []) if isinstance(response, dict) else []

    def get_doctypes(self) -> dict[str, Any]:
        return self.client.get("doctypes")

    def get_flat_doctypes(self) -> list[dict[str, Any]]:
        response = self.get_doctypes()
        structure = response.get("structure", []) if isinstance(response, dict) else []
        flat: list[dict[str, Any]] = []

        for item in structure:
            if not isinstance(item, dict):
                continue
            type_id = item.get("type_id")
            if type_id is None:
                continue
            flat.append(
                {
                    "type_id": int(type_id),
                    "label": item.get("description") or item.get("text") or str(type_id),
                }
            )

        return flat

    def find_doctype_by_keywords(self, keywords: tuple[str, ...]) -> dict[str, Any] | None:
        normalized_keywords = tuple(keyword.lower() for keyword in keywords if keyword)
        for doctype in self.get_flat_doctypes():
            label = doctype["label"].lower()
            if any(keyword in label for keyword in normalized_keywords):
                return doctype
        return None

    def get_indexing_models(self) -> list[IndexingModel]:
        response = self.client.get("indexingModels")
        raw_models = response.get("indexingModels", []) if isinstance(response, dict) else []
        return [IndexingModel.model_validate(item) for item in raw_models]

    def get_priorities(self) -> list[dict[str, Any]]:
        response = self.client.get("priorities")
        return response.get("priorities", []) if isinstance(response, dict) else []

    def get_attachment_types(self) -> dict[str, Any]:
        return self.client.get("attachmentsTypes")

    def get_actions(self) -> list[dict[str, Any]]:
        response = self.client.get("actions")
        return response.get("actions", []) if isinstance(response, dict) else []

    def get_baskets(self) -> list[dict[str, Any]]:
        response = self.client.get("baskets")
        return response.get("baskets", []) if isinstance(response, dict) else []

    def get_default_priority_id(self) -> str | None:
        priorities = self.get_priorities()
        if not priorities:
            return None
        return priorities[0]["id"]


@lru_cache
def get_reference_data_service(client: MaarchClient | None = None) -> ReferenceDataService:
    if client is None:
        from src.maarch.client import get_maarch_client

        client = get_maarch_client()
    return ReferenceDataService(client)
