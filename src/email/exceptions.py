class EmailError(Exception):
    """Base exception for email ingestion errors."""


class EmailConfigurationError(EmailError):
    """Raised when IMAP settings are missing or invalid."""


class EmailConnectionError(EmailError):
    """Raised when the IMAP server cannot be reached or authenticated."""
