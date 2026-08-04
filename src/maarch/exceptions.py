class MaarchError(Exception):
    """Base exception for Maarch integration errors."""


class MaarchAPIError(MaarchError):
    """Raised when the Maarch REST API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, payload: dict | list | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class MaarchConfigurationError(MaarchError):
    """Raised when Maarch credentials or URL are missing or invalid."""
