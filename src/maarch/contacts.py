from __future__ import annotations

import re
from email.utils import parseaddr
from typing import Any

from pydantic import BaseModel, Field

from src.maarch.client import MaarchClient
from src.utils import get_logger


logger = get_logger(__name__)


class CreateContactRequest(BaseModel):
    email: str
    firstname: str | None = None
    lastname: str | None = None
    company: str | None = None
    external_id: dict[str, Any] | None = Field(default=None, alias="externalId")

    model_config = {"populate_by_name": True}


class ContactService:
    """Resolve email senders to Maarch contacts."""

    def __init__(self, client: MaarchClient):
        self.client = client

    def resolve_sender(
        self,
        *,
        sender: str | None,
        sender_email: str | None,
    ) -> int | None:
        email_address = (sender_email or "").strip().lower()
        if not email_address:
            _, parsed_email = parseaddr(sender or "")
            email_address = parsed_email.strip().lower()

        if not email_address:
            return None

        payload = self._build_contact_payload(sender=sender, email_address=email_address)
        response = self.client.post(
            "contacts",
            json=payload.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )
        return self._parse_contact_id(response)

    @staticmethod
    def _build_contact_payload(*, sender: str | None, email_address: str) -> CreateContactRequest:
        display_name, _ = parseaddr(sender or "")
        display_name = display_name.strip()

        firstname = None
        lastname = None
        company = None

        if display_name and display_name != email_address:
            if "@" in display_name:
                company = _company_from_email(email_address)
            else:
                parts = display_name.split()
                if len(parts) == 1:
                    lastname = parts[0]
                else:
                    firstname = parts[0]
                    lastname = " ".join(parts[1:])
        else:
            company = _company_from_email(email_address)

        if not lastname and not company:
            lastname = email_address.split("@")[0]

        return CreateContactRequest(
            email=email_address,
            firstname=firstname,
            lastname=lastname,
            company=company,
            externalId={"automationSource": "intelligent-mailroom"},
        )

    @staticmethod
    def _parse_contact_id(response: Any) -> int | None:
        if isinstance(response, dict):
            if "id" in response:
                return int(response["id"])
            if "contact" in response and isinstance(response["contact"], dict):
                return int(response["contact"]["id"])

        if isinstance(response, list) and response:
            first = response[0]
            if isinstance(first, dict) and "id" in first:
                return int(first["id"])

        logger.warning("Unexpected contact response: %r", response)
        return None


def _company_from_email(email_address: str) -> str:
    domain = email_address.split("@")[-1]
    domain = re.sub(r"^www\.", "", domain)
    base = domain.split(".")[0]
    return base.replace("-", " ").title()
