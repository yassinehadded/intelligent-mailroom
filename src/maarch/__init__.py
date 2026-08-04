from functools import lru_cache

from src.maarch.attachments import AttachmentService
from src.maarch.client import MaarchClient, get_maarch_client
from src.maarch.contacts import ContactService
from src.maarch.exceptions import MaarchAPIError, MaarchConfigurationError, MaarchError
from src.maarch.models import (
    CreateAttachmentRequest,
    CreateAttachmentResponse,
    CreateResourceRequest,
    CreateResourceResponse,
    Entity,
    IndexingModel,
    ResourceListQuery,
    UpdateStatusRequest,
)
from src.maarch.reference import ReferenceDataService, get_reference_data_service
from src.maarch.resources import ResourceService


class MaarchService:
    """Facade grouping Maarch domain services for the automation layer."""

    def __init__(self, client: MaarchClient | None = None):
        self.client = client or get_maarch_client()
        self.resources = ResourceService(self.client)
        self.attachments = AttachmentService(self.client)
        self.reference = ReferenceDataService(self.client)
        self.contacts = ContactService(self.client)

    def ping(self) -> dict:
        return self.client.ping()

    def validate_connection(self) -> dict:
        from src.maarch.connection import validate_maarch_connection

        return validate_maarch_connection(self.client)


def get_maarch_service() -> MaarchService:
    return MaarchService()


__all__ = [
    "AttachmentService",
    "ContactService",
    "CreateAttachmentRequest",
    "CreateAttachmentResponse",
    "CreateResourceRequest",
    "CreateResourceResponse",
    "Entity",
    "IndexingModel",
    "MaarchAPIError",
    "MaarchClient",
    "MaarchConfigurationError",
    "MaarchError",
    "MaarchService",
    "ReferenceDataService",
    "ResourceListQuery",
    "ResourceService",
    "UpdateStatusRequest",
    "get_maarch_client",
    "get_maarch_service",
    "get_reference_data_service",
]
