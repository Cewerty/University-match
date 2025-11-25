import sys
from logging import Logger

from loguru import logger

from .config import config


def setup_logger() -> Logger:
    """Logger settings."""
    logger.remove()

    log_level = config.LOG_LEVEL

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        colorize=True,
        serialize=False,
    )

    if config.DEBUG is False:
        logger.add(
            sys.stdout,
            level=log_level,
            format="{message}",
            serialize=True,
            filter=lambda record: record["level"].no >= logger.level("WARNING").no,
        )

    return logger


logger: Logger = setup_logger()
