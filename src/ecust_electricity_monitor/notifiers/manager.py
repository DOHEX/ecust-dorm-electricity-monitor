"""通知管理器

统一管理和调度所有通知器。
"""

from datetime import datetime, timedelta

from ..config import NotificationConfig
from ..logger import logger
from ..models import AlertContext
from .base import BaseNotifier
from .email import EmailNotifier
from .serverchan import ServerChanNotifier


class NotificationManager:
    """通知管理器

    负责：
    - 根据配置动态创建通知器
    - 管理告警去重逻辑
    - 协调多个通知器并发发送
    - 统一错误处理和日志记录

    采用工厂模式 + 策略模式的混合设计。
    """

    def __init__(self, config: NotificationConfig):
        """初始化通知管理器

        Args:
            config: 通知配置对象
        """
        self.config = config
        self._notifiers: list[BaseNotifier] = []
        self._last_alert_time: datetime | None = None
        self._last_alert_power: float | None = None

        # 根据配置初始化通知器
        self._init_notifiers()

    def _init_notifiers(self) -> None:
        """初始化通知器

        根据配置的推送方式，动态创建相应的通知器实例。
        """
        enabled_channels = self.config.enabled_channels

        if not enabled_channels:
            logger.warning("未配置任何推送方式")
            return

        # 初始化邮件通知器
        if "email" in enabled_channels:
            if self.config.is_email_configured:
                notifier = EmailNotifier(self.config)
                self._notifiers.append(notifier)
                logger.info(f"已启用通知器: {notifier.name}")
            else:
                logger.warning("邮件推送已启用但配置不完整，跳过")

        # 初始化 Server酱 通知器
        if "serverchan" in enabled_channels:
            if self.config.is_serverchan_configured:
                notifier = ServerChanNotifier(self.config.serverchan_sendkey)
                self._notifiers.append(notifier)
                logger.info(f"已启用通知器: {notifier.name}")
            else:
                logger.warning("Server酱推送已启用但配置不完整，跳过")

        if not self._notifiers:
            logger.warning("所有推送方式配置均不完整，通知功能不可用")

    def is_configured(self) -> bool:
        """检查是否至少配置了一个可用的通知器

        Returns:
            是否可用
        """
        return len(self._notifiers) > 0

    def should_send_alert(
        self, context: AlertContext, cooldown_hours: int = 24
    ) -> bool:
        """判断是否应该发送告警

        避免在短时间内重复发送相同告警。

        Args:
            context: 告警上下文
            cooldown_hours: 冷却时间（小时）

        Returns:
            是否应该发送告警
        """
        # 如果是紧急告警，总是发送
        if context.is_critical:
            logger.debug("检测到紧急告警，将立即发送")
            return True

        # 如果从未发送过告警，发送
        if self._last_alert_time is None:
            logger.debug("首次告警，将发送")
            return True

        # 检查冷却时间
        time_since_last = datetime.now() - self._last_alert_time
        if time_since_last < timedelta(hours=cooldown_hours):
            hours_since = time_since_last.total_seconds() / 3600
            logger.debug(
                f"在冷却时间内 ({hours_since:.1f}h < {cooldown_hours}h)，跳过告警"
            )
            return False

        # 如果电量显著变化（例如充值了），也发送
        if self._last_alert_power is not None:
            power_diff = abs(context.current_record.power - self._last_alert_power)
            if power_diff > 50:  # 电量变化超过 50 度
                logger.debug(f"电量显著变化 ({power_diff:.1f} 度)，将发送新告警")
                return True

        logger.debug("不满足告警发送条件")
        return False

    def send_power_alert(self, context: AlertContext) -> bool:
        """发送电量低电告警

        Args:
            context: 告警上下文

        Returns:
            发送是否成功（至少一种方式成功即为成功）
        """
        if not self.is_configured():
            logger.warning("未配置任何推送方式，跳过告警发送")
            return False

        success_count = 0
        fail_count = 0

        # 并发发送到所有已配置的通知器
        for notifier in self._notifiers:
            try:
                if notifier.send_power_alert(context):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"{notifier.name}推送失败: {e}")
                fail_count += 1

        # 至少一种方式成功即为成功
        if success_count > 0:
            # 记录发送时间和电量
            self._last_alert_time = datetime.now()
            self._last_alert_power = context.current_record.power
            logger.info(f"电量告警已发送 (成功: {success_count}, 失败: {fail_count})")
            return True
        else:
            logger.error("所有推送方式均失败")
            return False

    def send_system_alert(
        self, consecutive_failures: int, last_success_time: datetime | None
    ) -> bool:
        """发送系统健康告警

        Args:
            consecutive_failures: 连续失败次数
            last_success_time: 最后成功时间

        Returns:
            发送是否成功（至少一种方式成功即为成功）
        """
        if not self.is_configured():
            logger.warning("未配置任何推送方式，跳过系统告警发送")
            return False

        success_count = 0
        fail_count = 0

        # 并发发送到所有已配置的通知器
        for notifier in self._notifiers:
            try:
                if notifier.send_system_alert(consecutive_failures, last_success_time):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"{notifier.name}推送失败: {e}")
                fail_count += 1

        # 至少一种方式成功即为成功
        if success_count > 0:
            logger.info(f"系统告警已发送 (成功: {success_count}, 失败: {fail_count})")
            return True
        else:
            logger.error("所有推送方式均失败")
            return False

    def get_enabled_notifiers(self) -> list[str]:
        """获取已启用的通知器列表

        Returns:
            通知器名称列表
        """
        return [notifier.name for notifier in self._notifiers]
