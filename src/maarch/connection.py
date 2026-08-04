from __future__ import annotations

from typing import Any

from src.maarch.client import MaarchClient
from src.maarch.exceptions import MaarchConfigurationError


RECOMMENDED_WEBSERVICE_MODES = {"rest", "root_invisible", "root_visible"}


def validate_maarch_connection(client: MaarchClient | None = None) -> dict[str, Any]:
    client = client or MaarchClient()
    ping = client.ping()

    warnings: list[str] = []
    profile: dict[str, Any] | None = None
    webservice_ready = True

    try:
        profile = client.get_current_user_profile()
        mode = profile.get("mode")
        if mode not in RECOMMENDED_WEBSERVICE_MODES:
            webservice_ready = False
            warnings.append(
                f"User mode '{mode}' is not a dedicated WebService account. "
                "Create a Maarch user with mode 'rest' for production."
            )
        if mode == "standard":
            warnings.append("Using a standard user for automation is discouraged.")
    except Exception as exc:
        warnings.append(f"Unable to read current user profile: {exc}")

    return {
        "connected": True,
        "application_name": ping.get("applicationName"),
        "auth_mode": ping.get("authMode"),
        "maarch_url": ping.get("maarchUrl"),
        "webservice_ready": webservice_ready,
        "current_user": profile.get("user_id") if profile else None,
        "current_user_mode": profile.get("mode") if profile else None,
        "warnings": warnings,
    }


def ensure_maarch_configured(settings) -> None:
    if not settings.maarch_url:
        raise MaarchConfigurationError("MAARCH_URL is not configured")
    if not settings.maarch_username or not settings.maarch_password:
        raise MaarchConfigurationError("MAARCH_USERNAME and MAARCH_PASSWORD are required")
