import logging
import os
from logging.handlers import RotatingFileHandler

from src.config import get_settings


def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a configured application logger.
    """

    settings = get_settings()

    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level)

    # Create logs directory if missing
    os.makedirs("logs", exist_ok=True)

    # Console handler
    console_handler = logging.StreamHandler()

    # File handler
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger