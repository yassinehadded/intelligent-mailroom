import time

from src.config import get_settings
from src.email import EmailConfigurationError, EmailIngestionService
from src.utils import get_logger


logger = get_logger(__name__)


def run_polling_loop() -> None:
    settings = get_settings()
    service = EmailIngestionService()
    interval = max(settings.email_poll_interval_seconds, 10)

    logger.info("Starting email polling worker (interval=%ss)", interval)

    while True:
        try:
            result = service.poll_and_ingest()
            logger.info(
                "Email poll complete: fetched=%s ingested=%s skipped=%s failed=%s",
                result.fetched,
                result.ingested,
                result.skipped,
                result.failed,
            )
        except EmailConfigurationError as exc:
            logger.error("Email worker stopped: %s", exc)
            break
        except Exception as exc:
            logger.exception("Email poll failed: %s", exc)

        time.sleep(interval)


if __name__ == "__main__":
    run_polling_loop()
