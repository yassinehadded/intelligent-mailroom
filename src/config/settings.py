from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from .env
    """

    # Application
    app_name: str = "Intelligent Mailroom"
    app_env: str = "development"
    log_level: str = "INFO"

    # Maarch
    maarch_url: str
    maarch_username: str | None = None
    maarch_password: str | None = None
    maarch_timeout: int = 30
    maarch_default_model_id: int = 8
    maarch_default_status: str = "INIT"
    maarch_default_attachment_type: str = "incoming_mail_attachment"

    # Email
    email_host: str | None = None
    email_port: int = 993
    email_username: str | None = None
    email_password: str | None = None
    email_use_ssl: bool = True
    email_mailbox: str = "INBOX"
    email_fetch_limit: int = 20
    email_mark_as_read: bool = True
    email_default_destination: int | None = 13
    email_poll_interval_seconds: int = 60

    # OCR
    ocr_enabled: bool = True
    ocr_tesseract_enabled: bool = False
    ocr_tesseract_lang: str = "fra+eng"

    # AI / Classification
    ai_enabled: bool = True
    ai_provider: str = "rules"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None
    openai_timeout: int = 60
    classification_min_confidence: float = 0.5

    # Maarch resilience
    maarch_retry_count: int = 3
    maarch_retry_backoff_seconds: float = 1.0
    maarch_auto_create_contacts: bool = True

    # Audit
    audit_db_path: str = "data/audit.db"
    audit_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a singleton instance of application settings.
    The configuration is loaded only once.
    """

    return Settings()