from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

import requests
from requests import Response, Session
from requests.exceptions import ChunkedEncodingError, ConnectionError, RequestException, Timeout

from src.config import Settings, get_settings
from src.maarch.exceptions import MaarchAPIError, MaarchConfigurationError
from src.utils import get_logger


logger = get_logger(__name__)

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class MaarchClient:
    """
    HTTP client for Maarch Courrier REST API.

    Authentication uses HTTP Basic Auth on every request (Maarch 2301 pattern).
    Transient failures are retried with exponential backoff.
    """

    def __init__(self, settings: Settings | None = None, session: Session | None = None):
        self.settings = settings or get_settings()
        self._session = session or requests.Session()
        self._configure_session()

    def _configure_session(self) -> None:
        if not self.settings.maarch_url:
            raise MaarchConfigurationError("MAARCH_URL is not configured")

        if not self.settings.maarch_username or not self.settings.maarch_password:
            raise MaarchConfigurationError("MAARCH_USERNAME and MAARCH_PASSWORD are required")

        self._session.auth = (
            self.settings.maarch_username,
            self.settings.maarch_password,
        )
        self._session.headers.update({"Accept": "application/json"})

    @property
    def base_url(self) -> str:
        base = self.settings.maarch_url.rstrip("/")
        return f"{base}/rest"

    def _build_url(self, path: str) -> str:
        from urllib.parse import urljoin

        normalized = path if path.startswith("/") else f"/{path}"
        return urljoin(f"{self.base_url}/", normalized.lstrip("/"))

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        timeout: int | None = None,
    ) -> Any:
        url = self._build_url(path)
        timeout = timeout or self.settings.maarch_timeout
        max_attempts = max(self.settings.maarch_retry_count, 1)
        backoff = self.settings.maarch_retry_backoff_seconds

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            logger.debug("Maarch %s %s (attempt %s/%s)", method.upper(), url, attempt, max_attempts)

            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=timeout,
                )
            except RequestException as exc:
                last_error = MaarchAPIError(f"Maarch request failed: {exc}")
                if attempt >= max_attempts or not self._is_retryable_exception(exc):
                    raise last_error from exc
                self._sleep_before_retry(attempt, backoff)
                continue

            if response.status_code < 400:
                return self._parse_success_response(response)

            if attempt >= max_attempts or response.status_code not in RETRYABLE_STATUS_CODES:
                return self._parse_error_response(response)

            logger.warning(
                "Retrying Maarch %s %s after HTTP %s",
                method.upper(),
                path,
                response.status_code,
            )
            self._sleep_before_retry(attempt, backoff)

        if last_error:
            raise last_error
        raise MaarchAPIError("Maarch request failed after retries")

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json: dict[str, Any] | list[Any] | None = None) -> Any:
        return self.request("POST", path, json=json)

    def put(self, path: str, *, json: dict[str, Any] | list[Any] | None = None) -> Any:
        return self.request("PUT", path, json=json)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def _parse_success_response(self, response: Response) -> Any:
        if not response.content:
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()

        return response.content

    def _parse_error_response(self, response: Response) -> Any:
        payload = self._safe_json(response)
        message = self._extract_error_message(payload, response)
        logger.error(
            "Maarch API error %s on %s: %s",
            response.status_code,
            response.url,
            message,
        )
        raise MaarchAPIError(message, status_code=response.status_code, payload=payload)

    @staticmethod
    def _sleep_before_retry(attempt: int, backoff: float) -> None:
        time.sleep(backoff * (2 ** (attempt - 1)))

    @staticmethod
    def _is_retryable_exception(exc: RequestException) -> bool:
        return isinstance(
            exc,
            (
                ConnectionError,
                Timeout,
                ChunkedEncodingError,
            ),
        )

    @staticmethod
    def _safe_json(response: Response) -> dict | list | None:
        try:
            return response.json()
        except ValueError:
            return None

    @staticmethod
    def _extract_error_message(payload: dict | list | None, response: Response) -> str:
        if isinstance(payload, dict):
            errors = payload.get("errors")
            if errors:
                return str(errors)

        return f"Maarch API returned HTTP {response.status_code}"

    def ping(self) -> dict[str, Any]:
        """Verify connectivity using a public endpoint."""
        return self.get("authenticationInformations")

    def get_current_user_profile(self) -> dict[str, Any]:
        return self.get("currentUser/profile")


@lru_cache
def get_maarch_client() -> MaarchClient:
    return MaarchClient()
