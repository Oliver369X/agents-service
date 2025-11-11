from __future__ import annotations

from loguru import logger

from .config import get_settings

_LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"


def _install_sink(level: str) -> None:
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=level,
        format=_LOG_FORMAT,
    )


def setup_logging() -> None:
    settings = get_settings()
    logger.remove()

    desired_level = settings.log_level.upper()

    try:
        _install_sink(desired_level)
    except ValueError:
        fallback_level = "INFO"
        _install_sink(fallback_level)
        logger.warning(
            "Nivel de log '%s' no reconocido, usando nivel por defecto '%s'.",
            desired_level,
            fallback_level,
        )
