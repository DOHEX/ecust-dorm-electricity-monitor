"""通知器模块

提供多种推送方式的统一接口。

使用示例:
    from notifiers import NotificationManager

    manager = NotificationManager(config.notification)
    manager.send_power_alert(alert_context)

支持的通知器:
    - EmailNotifier: 邮件推送
    - ServerChanNotifier: Server酱微信推送
"""

from .base import BaseNotifier
from .email import EmailNotifier
from .manager import NotificationManager
from .serverchan import ServerChanNotifier

__all__ = [
    "BaseNotifier",
    "EmailNotifier",
    "ServerChanNotifier",
    "NotificationManager",
]
