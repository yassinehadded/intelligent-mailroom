from functools import lru_cache

from src.maarch import MaarchConfigurationError, MaarchService, get_maarch_service


@lru_cache
def _cached_maarch_service() -> MaarchService:
    return get_maarch_service()


def get_maarch_service_optional() -> MaarchService | None:
    """
    Returns a Maarch service when credentials are configured, otherwise None.
    """
    try:
        return _cached_maarch_service()
    except MaarchConfigurationError:
        return None
