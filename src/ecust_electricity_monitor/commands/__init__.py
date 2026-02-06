"""CLI 命令模块

提供所有 CLI 命令的实现。每个命令独立一个模块，符合单一职责原则。
"""

from .alert import alert_command
from .base import console, version_callback
from .fetch import fetch_command
from .info import info_command
from .init import init_command
from .report import report_command
from .schedule import schedule_command

__all__ = [
    "alert_command",
    "console",
    "fetch_command",
    "info_command",
    "init_command",
    "report_command",
    "schedule_command",
    "version_callback",
]
