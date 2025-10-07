from .config import settings
from loguru import logger
import sys


# 统一日志初始化
def _init_logger() -> None:
    log_config = getattr(settings, "log", {})
    level = log_config.get("level", "INFO")
    file = log_config.get("file", None)
    rotation = log_config.get("rotation", "10 MB")
    retention = log_config.get("retention", "7 days")
    fmt = log_config.get("format", None)
    logger.remove()
    if file:
        logger.add(
            file, level=level, rotation=rotation, retention=retention, format=fmt
        )
    logger.add(sys.stderr, level=level, format=fmt)


_init_logger()
