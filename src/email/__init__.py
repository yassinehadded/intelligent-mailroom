from src.email.exceptions import EmailConfigurationError, EmailConnectionError, EmailError
from src.email.imap_client import ImapClient, parse_email_message
from src.email.models import EmailPollResult, IngestedEmailResult, ParsedEmail
from src.email.processor import EmailIngestionService


def get_email_ingestion_service() -> EmailIngestionService:
    return EmailIngestionService()


__all__ = [
    "EmailConfigurationError",
    "EmailConnectionError",
    "EmailError",
    "EmailIngestionService",
    "EmailPollResult",
    "ImapClient",
    "IngestedEmailResult",
    "ParsedEmail",
    "get_email_ingestion_service",
    "parse_email_message",
]
