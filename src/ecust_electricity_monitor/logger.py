"""日志配置 - Logging Configuration using Loguru"""

import os
import sys
from pathlib import Path

from loguru import logger

from .constants import (
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_RETENTION,
    DEFAULT_LOG_ROTATION,
)


def setup_logging(log_level: str = "INFO", log_dir: Path = DEFAULT_LOG_DIR) -> None:
    """
    配置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_dir: 日志目录
    """
    # 移除默认的 handler
    logger.remove()

    # 检测是否在 CI 环境
    in_ci = os.getenv("CI") == "true"

    if in_ci:
        # CI 环境：简化格式，便于 GitHub Actions 解析
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level=log_level,
        )
    else:
        # 本地环境：详细格式
        # 控制台输出
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
                "<level>{message}</level>"
            ),
            level=log_level,
            colorize=True,
        )

        # 文件输出
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "app.log",
            rotation=DEFAULT_LOG_ROTATION,
            retention=DEFAULT_LOG_RETENTION,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} - {message}"
            ),
            level="DEBUG",  # 文件保存详细日志
            encoding="utf-8",
        )

    logger.info(f"日志系统初始化完成 | 级别: {log_level} | CI环境: {in_ci}")


# 导出 logger 实例，供其他模块使用
__all__ = ["logger", "setup_logging"]
